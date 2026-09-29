#!/usr/bin/env python3
"""Launch a user-supplied SketchUp installation with a private Proton runtime."""
import argparse
import datetime
import fcntl
import json
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys

UNIT = 'aag-sketchup-2026.service'
PROTON = 'GE-Proton10-25'
CONTAINER = 'SteamLinuxRuntime_sniper'


def run(args):
    return subprocess.run(args, text=True, capture_output=True)


def notify(text):
    print(text, file=sys.stderr)
    if shutil.which('notify-send'):
        run(['notify-send', 'SketchUp 2026', text])


def processes(prefix):
    marker = ('STEAM_COMPAT_DATA_PATH=' + str(prefix)).encode()
    result = set()
    for entry in Path('/proc').glob('[0-9]*/environ'):
        try:
            if marker in entry.read_bytes().split(b'\0'):
                result.add(int(entry.parent.name))
        except (OSError, ValueError):
            pass
    return result


def focus(pids):
    desktop = next((line.split()[0] for line in run(['wmctrl', '-d']).stdout.splitlines()
                    if line.split()[1] == '*'), None)
    found = []
    for line in run(['wmctrl', '-lp']).stdout.splitlines():
        row = line.split(None, 4)
        if len(row) < 5 or not row[2].isdigit() or int(row[2]) not in pids:
            continue
        win = row[0]
        if desktop is not None:
            run(['wmctrl', '-ir', win, '-t', desktop])
        run(['wmctrl', '-ir', win, '-b', 'remove,hidden'])
        run(['wmctrl', '-ia', win])
        found.append(win)
    return found


def check_x64(path):
    with path.open('rb') as stream:
        header = stream.read(64)
        if len(header) < 64 or header[:2] != b'MZ':
            raise ValueError('Invalid Windows executable: ' + str(path))
        stream.seek(struct.unpack_from('<I', header, 60)[0])
        pe = stream.read(6)
        if len(pe) != 6 or pe[:4] != b'PE\0\0' or struct.unpack_from('<H', pe, 4)[0] != 0x8664:
            raise ValueError('Expected an x86-64 PE file: ' + str(path))


def environment(root, log, debug=False):
    proton = root/'runtime'/PROTON
    container = root/'runtime'/CONTAINER
    env = {key: os.environ[key] for key in
           ['DISPLAY', 'XAUTHORITY', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS', 'LANG']
           if key in os.environ}
    env.update({
        'STEAM_COMPAT_DATA_PATH': str(root/'compatdata'),
        'STEAM_COMPAT_CLIENT_INSTALL_PATH': str(root/'runtime/client'),
        'STEAM_COMPAT_INSTALL_PATH': str(root/'app'),
        'STEAM_COMPAT_LIBRARY_PATHS': str(root),
        'STEAM_COMPAT_TOOL_PATHS': str(proton) + ':' + str(container),
        'STEAM_COMPAT_MOUNTS': str(root),
        'UMU_ID': 'umu-sketchup', 'STEAM_COMPAT_PROTON': '1',
        'STEAM_COMPAT_APP_ID': '0', 'SteamAppId': '0', 'SteamGameId': '0',
        'PROTON_ENABLE_WAYLAND': '0', 'SU_CEF_DISABLE_GPU': '1',
        'PROTON_USE_WINED3D': '0', 'DISABLE_VK_LAYER_VALVE_steam_overlay_1': '1',
        'FONTCONFIG_FILE': str(root/'config/fontconfig.conf'),
        'PROTON_LOG': '1', 'PROTON_LOG_DIR': str(log),
        'WINEDEBUG': '-all,err+all,+seh,+loaddll' if debug else '-all,err+all',
    })
    network_source = Path(__file__).with_name('network-environment.py')
    if network_source.is_file():
        import runpy
        previous = sys.dont_write_bytecode
        try:
            sys.dont_write_bytecode = True
            env.update(runpy.run_path(str(network_source))['prepare'](root))
        finally:
            sys.dont_write_bytecode = previous
    isolation = root/'candidate-isolation.json'
    if isolation.is_file():
        protected = json.loads(isolation.read_text())['protected_readonly']
        if any(':' in path for path in protected):
            raise ValueError('Colon in a protected path is unsupported')
        env['PRESSURE_VESSEL_FILESYSTEMS_RO'] = ':'.join(protected)
    if debug:
        env['AAG_POPUP_TRACE'] = str(log/'popup-events.log')
    return env


def receipt_environment(env):
    source = Path(__file__).with_name('network-environment.py')
    if source.is_file():
        import runpy
        return runpy.run_path(str(source))['redact_environment'](env)
    return {key: '[configured; value omitted]' if 'proxy' in key.lower() else value
            for key, value in env.items()}


def check_popup_support(root):
    support = root/'bin/runtime-exec.py'
    if not support.is_file():
        raise ValueError('Missing private runtime entry helper: ' + str(support))
    source = Path(__file__).with_name('runtime-exec.py')
    spec = importlib.util.spec_from_file_location('aag_runtime_entry', source)
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    module.helper_environment(root, {})
    return 'CONFIGURED' if (root/'config/popup-present.json').is_file() else 'BASE_WITHOUT_PAINTING_HELPER'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1],
                        help='installation root; defaults to the parent of the installed bin directory')
    parser.add_argument('--debug', action='store_true', help='capture detailed Wine diagnostics for this launch')
    parser.add_argument('--check', action='store_true', help='validate required files without launching')
    parser.add_argument('model', nargs='?', type=Path)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    unit = UNIT
    if (root/'candidate-isolation.json').is_file():
        unit = 'aag-sketchup-candidate-' + hashlib.sha256(str(root).encode()).hexdigest()[:12] + '.service'
    prefix = root/'compatdata'
    app = root/'app/SketchUp.exe'
    proton = root/'runtime'/PROTON/'proton'
    container = root/'runtime'/CONTAINER/'_v2-entry-point'
    style = prefix/'pfx/drive_c/ProgramData/SketchUp/SketchUp 2026/SketchUp/Styles/StyleTemplate.skp'
    dlls = [root/'app/msvcp140.dll', prefix/'pfx/drive_c/windows/system32/msvcp140.dll',
            prefix/'pfx/drive_c/windows/system32/ucrtbase.dll']
    for tool in ['systemd-run', 'systemctl', 'wmctrl']:
        if not shutil.which(tool):
            raise ValueError('Required command is missing: ' + tool)
    for file in [app, proton, container, style, root/'config/fontconfig.conf', *dlls]:
        if not file.is_file():
            raise ValueError('Required SketchUp/runtime file is missing: ' + str(file))
    for file in [app, *dlls]:
        check_x64(file)
    for wine_dll in [root/'runtime'/PROTON/'files/lib/wine/x86_64-windows/user32.dll',
                     prefix/'pfx/drive_c/windows/system32/user32.dll']:
        if hashlib.sha256(wine_dll.read_bytes()).hexdigest() != '4e1251c8074cef40260caf36a9c84db42be33400af88a15c39fa5f638c42df65':
            raise ValueError('The validated Wine touch compatibility fix is missing: ' + str(wine_dll))
    popup_support = check_popup_support(root)
    if args.check:
        print(json.dumps({'root': str(root), 'architecture': 'x86-64', 'required_files': 'PASS', 'popup_support': popup_support}))
        return 0
    model = args.model.expanduser().resolve() if args.model else None
    if model is not None and not model.is_file():
        raise ValueError('The selected model does not exist: ' + str(model))
    runtime_dir = Path(os.environ.get('XDG_RUNTIME_DIR', '/run/user/' + str(os.getuid())))
    with (runtime_dir/(unit.removesuffix('.service')+'.lock')).open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        pids = processes(prefix)
        active = run(['systemctl', '--user', 'is-active', unit]).stdout.strip()
        if pids or active in ('active', 'activating', 'deactivating'):
            if not focus(pids):
                notify('SketchUp is still starting or closing. Try again in a moment.')
            elif model is not None:
                notify('SketchUp is already open. Use File > Open for another model.')
            return 0
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        log = root/'logs'/stamp
        log.mkdir(parents=True)
        env = environment(root, log, args.debug)
        cmd = [str(container), '--verb=run', '--', '/usr/bin/python3',
               str(root/'bin/runtime-exec.py'), str(root), str(proton), 'run',
               'Z:' + str(app).replace('/', chr(92))]
        if model is not None:
            cmd.append('Z:' + str(model).replace('/', chr(92)))
        manifest = {'unit': unit, 'log': str(log), 'root': str(root),
                    'start': datetime.datetime.now().isoformat(), 'command': cmd,
                    'environment': receipt_environment(env), 'max_seconds': 'infinity', 'debug': args.debug,
                    'proton_version': PROTON}
        (log/'manifest.json').write_text(json.dumps(manifest, indent=2))
        (root/'logs/current.json').write_text(json.dumps(manifest, indent=2))
        argv = ['systemd-run', '--user', '--collect', '--unit=' + unit,
                '--property=RuntimeMaxSec=infinity', '--property=TimeoutStopSec=8',
                '--property=KillMode=control-group', '--property=ExitType=cgroup',
                '--property=Restart=no', '--property=WorkingDirectory=' + str(root/'app'),
                '--property=StandardOutput=append:' + str(log/'console.log'),
                '--property=StandardError=append:' + str(log/'console.log')]
        argv += ['--setenv=' + key + '=' + value for key, value in env.items()]
        argv += ['/usr/bin/env', '-u', 'WAYLAND_DISPLAY', '-u', 'WINEPREFIX',
                 '-u', 'LD_PRELOAD', '-u', 'LD_LIBRARY_PATH',
                 '-u', 'SU_CEF_DBG_PORT', '-u', 'QT_PLUGIN_PATH',
                 '-u', 'QT_SCALE_FACTOR', '-u', 'QT_SCREEN_SCALE_FACTORS', *cmd]
        result = run(argv)
        if result.returncode:
            raise RuntimeError('SketchUp could not start: ' + result.stderr.strip())
        print('SketchUp logs: ' + str(log))
        return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError) as error:
        notify(str(error))
        sys.exit(1)
