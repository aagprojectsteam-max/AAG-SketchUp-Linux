#!/usr/bin/env python3
"""Copy one reviewed extension into a closed candidate or verified production.

Only a loader and its same-name directory are eligible. No installers are run,
no registry or license state is copied, and existing files are never overwritten.
Keep the receipt private. Review every source bundle before using this tool.
"""
import argparse
import datetime
import json
from pathlib import Path
import re
import shutil
import sys
import os
sys.dont_write_bytecode = True
from pe_metadata import sha256


def inside(path, root):
    return path == root or path.is_relative_to(root)


def windows_volume(path):
    return any((p/'Windows').is_dir() and (p/'Users').is_dir() for p in (path,*path.parents))


def plan(source, destination, name, exclude=()):
    source=source.resolve(strict=True); destination=destination.resolve()
    if not re.fullmatch(r'[A-Za-z0-9_! -]+',name): raise ValueError('Invalid extension identifier')
    if inside(destination,source) or inside(source,destination): raise ValueError('Source and destination overlap')
    if windows_volume(destination): raise ValueError('Refusing a real Windows destination')
    entries=[source/(name+'.rb')]
    if (source/name).exists() or (source/name).is_symlink(): entries.append(source/name)
    if not entries[0].is_file(): raise ValueError('Missing extension loader')
    files=[]
    for entry in entries:
        if entry.is_symlink(): raise ValueError('Source root entry is a symlink')
        if (destination/entry.name).exists() or (destination/entry.name).is_symlink(): raise ValueError('Destination entry already exists: '+entry.name)
        for p in ([entry] if entry.is_file() else sorted(entry.rglob('*'))):
            if p.is_symlink(): raise ValueError('Source contains a symlink; review it separately')
            if not p.is_file(): continue
            rel=p.relative_to(source).as_posix()
            if rel in exclude: continue
            if p.suffix.lower() in ('.lic','.key','.token','.db','.sqlite','.dmp'):
                raise ValueError('Possible private/license state requires separate review: '+rel)
            files.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha256(p)})
    return files


def write_receipt(receipt, report):
    temporary = receipt.with_suffix(receipt.suffix+'.new')
    with temporary.open('w') as stream:
        json.dump(report, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(receipt)


def copy_files(source, destination, files, receipt, report):
    report.update(state='COPYING', copied=[], current_file=None)
    write_receipt(receipt, report)
    try:
        for item in files:
            src = source/item['path']; out = destination/item['path']
            report['current_file'] = item['path']
            write_receipt(receipt, report)
            if src.is_symlink() or sha256(src) != item['sha256']:
                raise ValueError('Source changed since preflight')
            out.parent.mkdir(parents=True, exist_ok=True)
            if not out.resolve().is_relative_to(destination):
                raise ValueError('Destination escaped through a symlink')
            # O_EXCL rejects both existing files and dangling links.
            with src.open('rb') as sf, out.open('xb') as df:
                shutil.copyfileobj(sf, df)
                df.flush(); os.fsync(df.fileno())
            if sha256(out) != item['sha256']:
                raise ValueError('Copied file failed verification')
            report['copied'].append(item['path'])
            report['current_file'] = None
            write_receipt(receipt, report)
        report['state'] = 'COPIED_AND_VERIFIED'
        write_receipt(receipt, report)
    except Exception as error:
        report.update(state='PARTIAL_COPY_REQUIRES_REVIEW', error=str(error))
        write_receipt(receipt, report)
        raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--destination',type=Path,required=True)
    p.add_argument('--plugin',required=True)
    p.add_argument('--current-root',type=Path,required=True)
    p.add_argument('--exclude',action='append',default=[],help='reviewed relative file to omit')
    p.add_argument('--production-evidence',type=Path,help='reviewed local PASS record with matching source hashes and rollback path')
    p.add_argument('--receipt',type=Path)
    p.add_argument('--dry-run',action='store_true')
    a=p.parse_args();dest=a.destination.resolve();current=a.current_root.resolve(strict=True)
    try:
        files=plan(a.source,dest,a.plugin,a.exclude)
        production=inside(dest,current)
        if production:
            if not a.production_evidence: raise ValueError('Production copy requires explicit validated evidence')
            e=json.loads(a.production_evidence.read_text())
            gates=['LOAD','FUNCTION','GUI','SAVE_REOPEN','RESTART','NO_CRASH','ARCHITECTURE','ROLLBACK']
            if e.get('plugin')!=a.plugin or any(e.get('gates',{}).get(g)!='PASS' for g in gates): raise ValueError('Required plugin gates have not passed')
            if e.get('files')!=files: raise ValueError('Evidence hashes do not match the proposed copy')
            rollback=Path(e['rollback_path']).resolve(strict=True)
            if inside(rollback,current) or not (rollback/'manifest.json').is_file(): raise ValueError('Invalid independent rollback backup')
        report={'schema':1,'plugin':a.plugin,'source':str(a.source.resolve()),'destination':str(dest),'production':production,'files':files,'excluded':a.exclude,'operation':'DRY_RUN' if a.dry_run else 'COPY','utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        if a.dry_run:
            print(json.dumps(report,indent=2));return 0
        if not a.receipt: raise ValueError('A private --receipt is required for a copy')
        receipt=a.receipt.resolve()
        if receipt.exists() or inside(receipt,a.source.resolve()) or windows_volume(receipt): raise ValueError('Unsafe or existing receipt destination')
        # Caller must close the destination SketchUp first; enforce using prefix marker.
        for env in Path('/proc').glob('[0-9]*/environ'):
            try:values=env.read_bytes().split(b'\0')
            except OSError:continue
            for value in values:
                if value.startswith(b'STEAM_COMPAT_DATA_PATH='):
                    prefix=Path(value.split(b'=',1)[1].decode(errors='replace')).resolve()
                    if inside(dest,prefix): raise ValueError('Destination prefix has running processes')
        receipt.parent.mkdir(parents=True,exist_ok=True)
        copy_files(a.source.resolve(),dest,files,receipt,report)
        print(json.dumps({'state':report['state'],'files':len(files),'receipt':str(receipt)}));return 0
    except (OSError,ValueError,KeyError) as error:
        print('REFUSED: '+str(error),file=sys.stderr);return 2


if __name__=='__main__':sys.exit(main())
