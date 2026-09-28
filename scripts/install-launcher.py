#!/usr/bin/env python3
"""Install desktop integration for an existing validated SketchUp root."""
import argparse, datetime, json, pathlib, shutil, subprocess
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--root', type=pathlib.Path, required=True)
p.add_argument('--desktop-shortcut', action='store_true')
a = p.parse_args()
root = a.root.expanduser().resolve()
launcher = root/'bin/launch-sketchup.py'
icon_dir = root/'config/icons'
icon_dir.mkdir(parents=True, exist_ok=True)
icon = icon_dir/'sketchup.png'
for command in ['wrestool', 'icotool']:
    if not shutil.which(command):
        raise SystemExit('Install the icoutils package for native SketchUp icon extraction.')
subprocess.run(['wrestool', '-x', '-t', '14', '-n', 'IDR_MAINFRAME', '-o',
                str(icon_dir/'sketchup.ico'), str(root/'app/SketchUp.exe')], check=True)
subprocess.run(['icotool', '-x', '--index=9', '-o', str(icon), str(icon_dir/'sketchup.ico')], check=True)
subprocess.run([str(launcher), '--check'], check=True)
assert icon.is_file(), 'SketchUp icon missing'
text = '\n'.join(['[Desktop Entry]', 'Type=Application', 'Version=1.0',
    'Name=SketchUp 2026', 'Exec="' + str(launcher) + '" %f',
    'Icon=' + str(icon), 'Terminal=false', 'Categories=Graphics;3DGraphics;',
    'StartupNotify=false', 'StartupWMClass=steam_app_0', ''])
backup = root/'backups'/('desktop-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
backup.mkdir(parents=True)
staged = backup/'new.desktop'
staged.write_text(text)
subprocess.run(['desktop-file-validate', str(staged)], check=True)
targets = [pathlib.Path.home()/'.local/share/applications/aag-sketchup-2026.desktop']
if a.desktop_shortcut:
    desktop = pathlib.Path(subprocess.check_output(['xdg-user-dir', 'DESKTOP'], text=True).strip())
    targets.append(desktop/'SketchUp 2026.desktop')
changes = []
for index, target in enumerate(targets):
    target.parent.mkdir(parents=True, exist_ok=True)
    old = backup/(str(index) + '.desktop')
    if target.exists():
        shutil.copy2(target, old)
    target.write_text(text)
    target.chmod(0o755)
    changes.append({'target': str(target), 'previous': str(old) if old.exists() else None})
    if index:
        subprocess.run(['gio', 'set', str(target), 'metadata::trusted', 'true'], check=False)
(backup/'manifest.json').write_text(json.dumps(changes, indent=2))
subprocess.run(['update-desktop-database', str(targets[0].parent)], check=True)
print('Installed SketchUp 2026 launcher. Backup: ' + str(backup))
