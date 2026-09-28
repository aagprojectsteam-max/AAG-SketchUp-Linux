"""Read PE architecture, fixed file version, imports and exports without execution."""
import hashlib
import struct
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inspect_pe(path):
    data = Path(path).read_bytes()
    result = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    if data[:2] != b'MZ':
        return dict(result, architecture='NON_PE')
    def u16(p): return struct.unpack_from('<H', data, p)[0]
    def u32(p): return struct.unpack_from('<I', data, p)[0]
    try:
        pe = u32(60)
        if data[pe:pe+4] != b'PE\0\0': raise ValueError('Invalid PE signature')
        machine = u16(pe+4)
        result['architecture'] = {0x8664:'x86-64', 0x14c:'x86', 0xaa64:'ARM64'}.get(machine, hex(machine))
        opt = pe+24
        dirs = opt+(112 if u16(opt)==0x20b else 96)
        sections = []
        for n in range(u16(pe+6)):
            s = opt+u16(pe+20)+40*n
            sections.append((data[s:s+8].rstrip(b'\0'), u32(s+12), u32(s+8), u32(s+20), u32(s+16)))
        def offset(rva):
            if rva < u32(opt+60): return rva
            for name,va,vs,raw,rs in sections:
                if va <= rva < va+min(max(vs,rs),rs): return raw+rva-va
            raise ValueError('RVA outside file-backed sections')
        def string(rva):
            p=offset(rva); end=data.find(b'\0',p,p+4096)
            if end < 0: raise ValueError('Unterminated PE string')
            return data[p:end].decode('ascii',errors='replace')
        imports=[]; delay=[]; exports=[]
        if u32(dirs+8):
            p=offset(u32(dirs+8))
            for n in range(4096):
                rec=struct.unpack_from('<5I',data,p+20*n)
                if not any(rec): break
                imports.append(string(rec[3]))
        if u32(dirs+13*8):
            p=offset(u32(dirs+13*8))
            for n in range(4096):
                rec=struct.unpack_from('<8I',data,p+32*n)
                if not any(rec): break
                if rec[0]&1: delay.append(string(rec[1]))
        if u32(dirs):
            p=offset(u32(dirs)); count=u32(p+24); names=offset(u32(p+32)) if count else 0
            for n in range(min(count,65536)): exports.append(string(u32(names+4*n)))
        result.update(imports=sorted(set(imports)), delay_imports=sorted(set(delay)), exports=exports)
        # VS_FIXEDFILEINFO belongs to the PE resource section; ignore accidental code signatures.
        for name,va,vs,raw,rs in sections:
            if name != b'.rsrc': continue
            region=data[raw:raw+rs]; start=0
            # Some applications keep 26.0.0.0 in VS_FIXEDFILEINFO while the
            # bounded StringFileInfo block carries the actual 26.1.252 build.
            for key in ('FileVersion', 'ProductVersion'):
                encoded = (key+'\0').encode('utf-16le')
                pos = 0
                values = set()
                while True:
                    at = region.find(encoded, pos)
                    if at < 0: break
                    pos = at+len(encoded)
                    if at < 6: continue
                    size, chars, kind = struct.unpack_from('<HHH', region, at-6)
                    begin = (raw+at+len(encoded)+3)//4*4-raw
                    end = begin+chars*2
                    if kind != 1 or not chars or end > at-6+size or end > len(region): continue
                    value = region[begin:end].decode('utf-16le', errors='strict').rstrip('\0').strip()
                    if value: values.add(value)
                if values: result.setdefault('version_strings', {})[key] = sorted(values)
            while True:
                p=region.find(b'\xbd\x04\xef\xfe',start)
                if p < 0: break
                start=p+4
                if p+52 > len(region): continue
                fields=struct.unpack_from('<13I',region,p)
                if fields[1] != 0x10000: continue
                result['file_version']='.'.join(map(str,[fields[2]>>16,fields[2]&65535,fields[3]>>16,fields[3]&65535]))
                result['product_version']='.'.join(map(str,[fields[4]>>16,fields[4]&65535,fields[5]>>16,fields[5]&65535]))
                break
        return result
    except (struct.error,ValueError,IndexError,UnicodeError) as error:
        return dict(result, error=str(error), architecture='INVALID_PE')
