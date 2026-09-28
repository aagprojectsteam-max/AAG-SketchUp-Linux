#!/usr/bin/env python3
"""Build the original popup presentation helper inside a closed SketchUp root.

Requires a C compiler and X11/XCB/XRender development headers. Does not install
host packages or download anything. Compiled output stays in the local runtime.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(root):
    root = root.expanduser().resolve(strict=True)
    if not (root/'app/SketchUp.exe').is_file() or not (root/'compatdata').is_dir():
        raise ValueError('Expected a prepared SketchUp root')
    if any((p/'Windows').is_dir() and (p/'Users').is_dir() for p in (root, *root.parents)):
        raise ValueError('Real Windows source volumes are read-only')
    marker = ('STEAM_COMPAT_DATA_PATH='+str(root/'compatdata')).encode()
    for env in Path('/proc').glob('[0-9]*/environ'):
        try:
            active = marker in env.read_bytes().split(b'\0')
        except OSError:
            continue
        if active:
            raise ValueError('Close this SketchUp prefix before replacing its helper')
    source = Path(__file__).with_name('popup-present.c')
    output = root/'runtime/popup-present'
    config = root/'config/popup-present.json'
    for path in (output, config):
        if not path.resolve().is_relative_to(root) or path.is_symlink():
            raise ValueError('Output must remain inside the installation root')
    compiler = shutil.which('cc')
    if not compiler:
        raise ValueError('A C compiler is required; see WINDOW-PAINTING.md')
    flags = ['-shared','-fPIC','-O2','-Wall','-Wextra','-Werror','-Wl,-z,relro,-z,now']
    output.mkdir(parents=True, exist_ok=True)
    config.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.build-', dir=output) as temp:
        library = Path(temp)/'libaag-popup-present.so'
        subprocess.run([compiler,*flags,str(source),'-o',str(library),'-ldl','-lX11','-lxcb','-pthread'],check=True)
        header = library.read_bytes()[:64]
        if header[:6] != b'\x7fELF\x02\x01' or struct.unpack_from('<H',header,18)[0] != 62:
            raise ValueError('Expected a little-endian x86-64 ELF helper')
        symbols = subprocess.check_output(['objdump','-T',str(library)],text=True)
        versions = set(re.findall(r'GLIBC_(\d+(?:\.\d+)+)',symbols))
        newest = max(versions, key=lambda x:tuple(map(int,x.split('.'))))
        if tuple(map(int,newest.split('.'))) > (2,36):
            raise ValueError('Helper needs a newer glibc than the validated sniper runtime')
        manifest = {'schema':1,'enabled':True,'library':'runtime/popup-present/libaag-popup-present.so',
                    'sha256':digest(library),'source_sha256':digest(source),'architecture':'x86-64',
                    'minimum_glibc':newest,'compiler':subprocess.check_output([compiler,'--version'],text=True).splitlines()[0],
                    'flags':flags,'validated_runtime':'GE-Proton10-25 + SteamLinuxRuntime_sniper',
                    'scope':'Wine raster tool popups; prefix-scoped; no OpenGL interposition',
                    'fallback_ms':250,'dialog_background':'white','utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        library.chmod(0o755)
        os.replace(library,output/library.name)
        shutil.copyfile(source,output/'popup-present.c')
        temporary = config.with_suffix('.json.new')
        temporary.write_text(json.dumps(manifest,indent=2)+'\n')
        os.replace(temporary,config)
    return manifest


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    try:
        print(json.dumps(build(args.root),indent=2))
    except (OSError,ValueError,subprocess.CalledProcessError) as error:
        parser.exit(2,'REFUSED: '+str(error)+'\n')
