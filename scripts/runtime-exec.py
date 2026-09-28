#!/usr/bin/env python3
"""Enter the prepared private runtime after pressure-vessel establishes mounts."""
import hashlib
import json
import os
from pathlib import Path
import sys


def helper_environment(root, environment):
    """Validate local compiled support before using it; no proprietary patching."""
    env = dict(environment)
    config = root/'config/popup-present.json'
    if not config.is_file():
        return env
    manifest = json.loads(config.read_text())
    if not manifest.get('enabled'):
        return env
    library = (root/manifest['library']).resolve(strict=True)
    if not library.is_relative_to(root) or library.name != 'libaag-popup-present.so':
        raise ValueError('Popup helper must remain inside the installation runtime')
    if hashlib.sha256(library.read_bytes()).hexdigest() != manifest['sha256']:
        raise ValueError('Popup helper hash changed; rebuild and validate before launch')
    if manifest.get('dialog_background') != 'white':
        raise ValueError('Unvalidated dialog background setting')
    # LD_LIBRARY_PATH accepts spaces; LD_PRELOAD splits on both spaces and colons.
    # A basename avoids temporary symlinks when the installation path has spaces.
    env['LD_LIBRARY_PATH'] = str(library.parent) + ':' + env.get('LD_LIBRARY_PATH', '')
    env['LD_PRELOAD'] = library.name
    env['AAG_POPUP_PRESENT'] = '1'
    env['AAG_POPUP_PREFIX'] = str(root/'compatdata/pfx')
    env['AAG_DIALOG_BACKGROUND'] = 'white'
    return env


def main():
    root = Path(sys.argv[1]).resolve(strict=True)
    command = sys.argv[2:]
    if not command or Path(command[0]).resolve() != (root/'runtime/GE-Proton10-25/proton').resolve():
        raise ValueError('Unexpected private runtime command')
    isolation = root/'candidate-isolation.json'
    if isolation.is_file():
        protected = json.loads(isolation.read_text())['protected_readonly']
        report = {p: bool(os.statvfs(p).f_flag & os.ST_RDONLY) for p in protected}
        (root/'logs/isolation-enforced.json').write_text(json.dumps(report, indent=2)+'\n')
        if not all(report.values()):
            raise ValueError('Candidate protected source/production/backup path is writable')
    environment = helper_environment(root, os.environ)
    os.execve(command[0], command, environment)


if __name__ == '__main__':
    try:
        main()
    except (OSError,ValueError,KeyError) as error:
        print('REFUSED: '+str(error), file=sys.stderr)
        sys.exit(77)
