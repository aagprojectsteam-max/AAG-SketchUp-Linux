#!/usr/bin/env python3
"""Collect a small local support report, excluding model data and raw crash dumps."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import runpy
import subprocess


def capture(argv):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=15)
        return {'exit': r.returncode, 'output': (r.stdout + r.stderr).strip()}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'error': type(error).__name__}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    a = parser.parse_args()
    root = a.root.expanduser().resolve()
    prefix = root/'compatdata/pfx'
    api = runpy.run_path(str(Path(__file__).with_name('launch-sketchup.py')))
    files = ['app/SketchUp.exe', 'app/msvcp140.dll',
             'runtime/GE-Proton10-25/files/lib/wine/x86_64-windows/user32.dll',
             'compatdata/pfx/drive_c/windows/system32/user32.dll',
             'compatdata/pfx/drive_c/windows/system32/msvcp140.dll',
             'compatdata/pfx/drive_c/windows/system32/ucrtbase.dll',
             'compatdata/pfx/drive_c/ProgramData/SketchUp/SketchUp 2026/SketchUp/Styles/StyleTemplate.skp']
    report = {'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'kernel': platform.release(), 'session': os.environ.get('XDG_SESSION_TYPE', 'unknown'),
              'proton': api['PROTON'], 'files': {},
              'launcher_check': capture([str(root/'bin/launch-sketchup.py'), '--check']),
              'service': capture(['systemctl', '--user', 'show', api['UNIT'],
                                 '-p', 'ActiveState', '-p', 'SubState', '-p', 'Result',
                                 '-p', 'MemoryCurrent', '-p', 'CPUUsageNSec']),
              'prefix_process_count': len(api['processes'](root/'compatdata'))}
    for relative in files:
        file = root/relative
        value = {'exists': file.is_file()}
        if file.is_file():
            value.update(bytes=file.stat().st_size, sha256=hashlib.sha256(file.read_bytes()).hexdigest())
            if file.suffix.lower() in ('.exe', '.dll'):
                try:
                    api['check_x64'](file)
                    value['architecture'] = 'x86-64'
                except (OSError, ValueError):
                    value['architecture'] = 'INVALID_OR_NOT_X64'
        report['files'][relative] = value
    reg = prefix/'user.reg'
    if reg.exists():
        text = reg.read_text(errors='replace')
        section = re.search(r'^\[Control Panel\\\\Desktop\][^\n]*\n(.*?)(?=^\[|\Z)', text, re.M | re.S)
        value = re.search(r'^"LogPixels"=dword:([0-9a-f]+)', section.group(1), re.M) if section else None
        report['wine_dpi'] = int(value.group(1), 16) if value else 'default'
    prefs = prefix/'drive_c/users/steamuser/AppData/Local/SketchUp/SketchUp 2026/SketchUp/PrivatePreferences.json'
    if prefs.exists():
        try:
            values = json.loads(prefs.read_text()).get('This Computer Only', {}).get('Preferences', {})
            report['renderer_preferences'] = {k: values[k] for k in
                ['UseNewRenderer', 'TryNewRenderer', 'AAMethod', 'UseFastFeedback', 'ValidateGraphicsCardPrefs'] if k in values}
        except (ValueError, OSError):
            report['renderer_preferences'] = 'UNREADABLE'
    for name, file in [('proton_version', root/'runtime'/api['PROTON']/'version'),
                       ('container_version', root/'runtime'/api['CONTAINER']/'VERSIONS.txt')]:
        if file.exists():
            report[name] = file.read_text(errors='replace')[:8192]
    # Only known roots are included above. Scrub them before emitting the report.
    text = json.dumps(report, indent=2).replace(str(root), '$SKETCHUP_ROOT').replace(str(Path.home()), '$HOME')
    destination = root/'logs'/('diagnostics-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '.json')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text + '\n')
    print(destination)
    print('Raw logs, models, account data and crash dumps were not copied. Review before sharing.')


if __name__ == '__main__':
    main()
