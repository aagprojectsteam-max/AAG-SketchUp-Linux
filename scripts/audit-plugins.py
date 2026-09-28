#!/usr/bin/env python3
"""Inventory explicit extension roots without loading code or copying settings.

Outputs are private by default: paths and filenames may disclose user information.
Use --output only in a local evidence directory; manually sanitize public summaries.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
from pe_metadata import inspect_pe, sha256

PRIVATE = re.compile(r'(?i)(license|licence|credential|cookie|token|password|login|account|\.lic$|webcache)')


def audit(root):
    files=[]
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            files.append({'path':str(path.relative_to(root)), 'kind':'SYMLINK_NOT_FOLLOWED'})
            continue
        if not path.is_file(): continue
        rel=str(path.relative_to(root)); info={'path':rel,'bytes':path.stat().st_size}
        # No contents, hashes or values collected for potential account state.
        if PRIVATE.search(rel) and path.suffix.lower() not in ('.rb','.rbe','.so','.dll','.exe','.html','.js','.css','.png','.svg','.gif','.bundle','.susig','.lang'):
            info['kind']='PRIVATE_OR_LICENSE_METADATA_ONLY'
        else:
            with path.open('rb') as f: magic=f.read(4)
            if magic[:2]==b'MZ':
                info.update(inspect_pe(path)); info['kind']='PE'
            else:
                kind = 'ELF' if magic==b'\x7fELF' else ('MACH_O' if magic in [b'\xca\xfe\xba\xbe', b'\xce\xfa\xed\xfe', b'\xcf\xfa\xed\xfe'] else 'FILE')
                info.update(sha256=sha256(path), kind=kind)
                if kind == 'MACH_O':
                    import struct
                    with path.open('rb') as f: header=f.read(4096)
                    cpu_names={7:'x86',0x1000007:'x86-64',12:'ARM',0x100000c:'ARM64'}
                    if magic == b'\xca\xfe\xba\xbe':
                        count=struct.unpack_from('>I',header,4)[0]
                        info['architectures']=[cpu_names.get(struct.unpack_from('>I',header,8+20*n)[0],'UNKNOWN') for n in range(min(count,(len(header)-8)//20))]
                    else: info['architectures']=[cpu_names.get(struct.unpack_from('<I',header,4)[0],'UNKNOWN')]
                    info['platform']='macOS; inactive in Windows SketchUp'
            if path.suffix.lower() in ('.rb','.plugin'):
                text=path.read_text(errors='replace')
                info['declared_versions']=sorted(set(re.findall(r'(?im)(?:[.\[]?version[\]\s:]*(?:=|=>)?\s*[\x27\"]?)(\d+\.\d+[a-zA-Z0-9. -]*)',text)))[:15]
                info['api_flags']=[name for name,pattern in {'native_ffi':r'Fiddle|Win32API|FFI|DL::','html_dialog':r'HtmlDialog|WebDialog','external_process':r'\bspawn\b|\bexec\b|IO.popen|system\(','registry':r'Win32::Registry','update':r'updat'}.items() if re.search(pattern,text,re.I)]
        files.append(info)
    natives=[{k:v for k,v in f.items() if k!='exports'} for f in files if f['kind']=='PE']
    return {'root':str(root), 'file_count':len(files), 'bytes':sum(f.get('bytes',0) for f in files), 'architectures':dict(Counter(f.get('architecture') for f in natives)), 'native_files':natives, 'files':files}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',action='append',type=Path,required=True)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    roots=[s.resolve(strict=True) for s in a.source]
    if a.output:
        out=a.output.resolve()
        if out.exists(): p.error('Output exists; choose a new evidence file')
        if any(out.is_relative_to(r) for r in roots): p.error('Output must be outside source roots')
        if any((ancestor/'Windows').is_dir() and (ancestor/'Users').is_dir() for ancestor in (out,*out.parents)):
            p.error('Refusing output on a real Windows installation')
    report={'schema':1,'source_operation':'READ_ONLY','extensions_executed':False,'roots':[audit(s) for s in roots]}
    data=json.dumps(report,indent=2)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(data+'\n')
        print(json.dumps({'output':str(a.output),'roots':[{'source':r['root'],'files':r['file_count'],'bytes':r['bytes'],'architectures':r['architectures']} for r in report['roots']]},indent=2))
    else: print(data)


if __name__=='__main__': main()
