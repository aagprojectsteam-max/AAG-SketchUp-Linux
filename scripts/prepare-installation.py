#!/usr/bin/env python3
"""Prepare an isolated installation using only files supplied by the user.

This script does not download SketchUp, accept its terms, or activate a license.
"""
import argparse, hashlib, json, os, pathlib, re, runpy, shutil, subprocess

P = pathlib.Path
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--root', type=P, required=True, help='new, empty destination')
p.add_argument('--app-source', type=P, required=True, help='complete user-owned SketchUp application directory')
p.add_argument('--content-source', type=P, required=True, help='SketchUp ProgramData content directory')
p.add_argument('--msvcp-x64', type=P, required=True, help='legitimate x64 MSVCP140.dll')
p.add_argument('--ucrt-x64', type=P, required=True, help='legitimate native x64 ucrtbase.dll')
p.add_argument('--proton-source', type=P, required=True, help='extracted GE-Proton10-25 directory')
p.add_argument('--container-source', type=P, required=True, help='complete SteamLinuxRuntime_sniper directory')
p.add_argument('--dpi', type=int, default=192)
a = p.parse_args()
if not 96 <= a.dpi <= 288:
    p.error('--dpi must be between 96 and 288')
root = a.root.expanduser().resolve()
if root.exists():
    p.error('Destination already exists; refusing to merge or overwrite an installation')
launcher = P(__file__).with_name('launch-sketchup.py')
api = runpy.run_path(str(launcher))
api['check_x64'](a.app_source/'SketchUp.exe')
api['check_x64'](a.msvcp_x64)
api['check_x64'](a.ucrt_x64)
assert (a.content_source/'Styles/StyleTemplate.skp').is_file(), 'Missing StyleTemplate.skp in supplied content'
assert (a.proton_source/'proton').is_file(), 'Missing Proton entry point'
assert (a.container_source/'_v2-entry-point').is_file(), 'Missing container entry point'
(root/'runtime/client').mkdir(parents=True)
(root/'config').mkdir()
(root/'compatdata').mkdir()
(root/'bin').mkdir()
(root/'logs/setup').mkdir(parents=True)
for source, dest in [(a.app_source, root/'app'), (a.proton_source, root/'runtime/GE-Proton10-25'),
                     (a.container_source, root/'runtime/SteamLinuxRuntime_sniper')]:
    subprocess.run(['cp', '-a', '--reflink=auto', str(source.resolve()), str(dest)], check=True)
shutil.copy2(a.msvcp_x64, root/'app/msvcp140.dll')
# Hash-guarded fix to this private open-source Wine runtime only.
subprocess.run(['python3', str(P(__file__).with_name('patch-wine-touch.py')),
                str(root/'runtime/GE-Proton10-25/files/lib/wine/x86_64-windows/user32.dll')], check=True)
(root/'config/fontconfig.conf').write_text('<?xml version="1.0"?>\n<!DOCTYPE fontconfig SYSTEM "fonts.dtd">\n<fontconfig>\n  <include ignore_missing="yes">/etc/fonts/fonts.conf</include>\n  <selectfont><rejectfont>\n    <glob>/usr/share/fonts/noto-emoji/NotoColorEmoji.ttf</glob>\n    <glob>/run/host/fonts/truetype/noto/NotoColorEmoji.ttf</glob>\n    <glob>/run/host/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf</glob>\n  </rejectfont></selectfont>\n</fontconfig>\n')
for name in ['launch-sketchup.py', 'install-launcher.py', 'collect-diagnostics.py']:
    source = P(__file__).with_name(name)
    if source.exists():
        shutil.copy2(source, root/'bin'/name)
        (root/'bin'/name).chmod(0o755)
env = os.environ.copy()
env.update(api['environment'](root, root/'logs/setup'))
for key in ['WAYLAND_DISPLAY', 'WINEPREFIX', 'SU_CEF_DBG_PORT', 'QT_PLUGIN_PATH']:
    env.pop(key, None)
cmd = [str(root/'runtime/SteamLinuxRuntime_sniper/_v2-entry-point'), '--verb=run', '--',
       str(root/'runtime/GE-Proton10-25/proton'), 'run', 'C:\\windows\\system32\\cmd.exe', '/c', 'exit', '0']
with (root/'logs/setup/prefix-init.log').open('w') as output:
    subprocess.run(cmd, env=env, stdout=output, stderr=subprocess.STDOUT, check=True, timeout=180)
prefix = root/'compatdata/pfx'
assert (prefix/'user.reg').is_file(), 'Prefix creation did not complete'
content = prefix/'drive_c/ProgramData/SketchUp/SketchUp 2026/SketchUp'
content.mkdir(parents=True, exist_ok=True)
shutil.copytree(a.content_source, content, dirs_exist_ok=True)
shutil.copy2(a.msvcp_x64, prefix/'drive_c/windows/system32/msvcp140.dll')
shutil.copy2(a.ucrt_x64, prefix/'drive_c/windows/system32/ucrtbase.dll')
reg = prefix/'user.reg'
text = reg.read_text()

def set_value(section, name, value):
    global text
    marker = '[' + section.replace(chr(92), chr(92)*2) + ']'
    start = text.find(marker)
    if start < 0:
        text += '\n' + marker + '\n"' + name + '"=' + value + '\n'
        return
    end = text.find('\n[', start + 1)
    if end < 0:
        end = len(text)
    block = re.sub(r'^"' + re.escape(name) + r'"=.*\n?', '', text[start:end], flags=re.M)
    block += '\n"' + name + '"=' + value + '\n'
    text = text[:start] + block + text[end:]

set_value('Control Panel'+chr(92)+'Desktop', 'LogPixels', 'dword:' + format(a.dpi, '08x'))
set_value('Software'+chr(92)+'Wine'+chr(92)+'AppDefaults'+chr(92)+'SketchUp.exe', 'Version', '"win10"')
set_value('Software'+chr(92)+'Wine'+chr(92)+'DllOverrides', 'ucrtbase', '"native,builtin"')
# CEF and Qt must agree on DPI before creating their first window.
text += '\n[Software\\\\Microsoft\\\\Windows NT\\\\CurrentVersion\\\\AppCompatFlags\\\\Layers]\n@="HIGHDPIAWARE"\n'
reg.write_text(text)
prefs = prefix/'drive_c/users/steamuser/AppData/Local/SketchUp/SketchUp 2026/SketchUp/PrivatePreferences.json'
prefs.parent.mkdir(parents=True, exist_ok=True)
prefs.write_text(json.dumps({'This Computer Only': {'Preferences': {
    'UseNewRenderer': False, 'TryNewRenderer': False, 'CountOfNewRenderersOnProbation': 0,
    'AAMethod': 8, 'UseFastFeedback': False, 'ValidateGraphicsCardPrefs': True}}}, indent=4))
critical = [root/'app/SketchUp.exe', root/'app/msvcp140.dll',
            prefix/'drive_c/windows/system32/ucrtbase.dll', content/'Styles/StyleTemplate.skp']
(root/'logs/setup/inputs.json').write_text(json.dumps({
    'dpi': a.dpi, 'proton': api['PROTON'], 'terms_accepted_by_script': False,
    'files': {str(f.relative_to(root)): {'sha256': hashlib.sha256(f.read_bytes()).hexdigest(),
                                      'bytes': f.stat().st_size} for f in critical}
}, indent=2))
subprocess.run([str(root/'bin/launch-sketchup.py'), '--check'], check=True)
print('Prepared. Launch SketchUp and personally review its terms and license prompts. No desktop shortcut was changed.')
