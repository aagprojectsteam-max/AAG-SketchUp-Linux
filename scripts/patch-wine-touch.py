#!/usr/bin/env python3
"""Add a nonfatal unsupported-touch export to one exact GE-Proton Wine build.

Only the open-source Wine user32.dll is changed. No executable code is added.
GetPointerFrameTouchInfo aliases the existing same-signature unsupported
GetPointerTouchInfoHistory function (FALSE / ERROR_CALL_NOT_IMPLEMENTED).
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

STOCK = '996d515d8cb4828cd0a61fc82414e15ebf352e49d1d3655ca9dd0e4cbc29d7a1'
NAME = 'GetPointerFrameTouchInfo'
TARGET = 'GetPointerTouchInfoHistory'

class PE:
    def __init__(self, data):
        self.data = data
        self.pe = self.u32(60)
        self.opt = self.pe + 24
        assert data[:2] == b'MZ' and data[self.pe:self.pe+4] == b'PE\0\0'
        assert self.u16(self.pe+4) == 0x8664 and self.u16(self.opt) == 0x20b
        self.table = self.opt + self.u16(self.pe+20)
        self.sections = [struct.unpack_from('<IIII', data, self.table+40*i+8)
                         for i in range(self.u16(self.pe+6))]
        self.exp = self.offset(self.u32(self.opt+112))
    def u16(self, offset): return struct.unpack_from('<H', self.data, offset)[0]
    def u32(self, offset): return struct.unpack_from('<I', self.data, offset)[0]
    def offset(self, rva):
        for size, va, rawsize, raw in self.sections:
            if va <= rva < va+max(size, rawsize): return raw+rva-va
        raise ValueError('RVA outside sections')
    def entries(self):
        names = self.offset(self.u32(self.exp+32))
        ords = self.offset(self.u32(self.exp+36))
        eat = self.offset(self.u32(self.exp+28))
        result = {}
        for i in range(self.u32(self.exp+24)):
            rva = self.u32(names+4*i)
            pos = self.offset(rva)
            name = self.data[pos:self.data.index(b'\0', pos)].decode('ascii')
            ordinal = self.u16(ords+2*i)
            result[name] = (rva, ordinal, self.u32(eat+4*ordinal))
        return result

def patch(data):
    if hashlib.sha256(data).hexdigest() != STOCK:
        raise ValueError('Unsupported DLL hash; refusing to modify this file')
    pe = PE(data)
    old = pe.entries()
    assert NAME not in old and TARGET in old
    entries = dict(old)
    count = len(old)+1
    align = lambda n, a: (n+a-1)//a*a
    va = align(pe.u32(pe.opt+56), pe.u32(pe.opt+32))
    raw = align(len(data), pe.u32(pe.opt+36))
    entries[NAME] = (va+6*count, old[TARGET][1], old[TARGET][2])
    ordered = sorted(entries)
    payload = b''.join(struct.pack('<I', entries[n][0]) for n in ordered)
    payload += b''.join(struct.pack('<H', entries[n][1]) for n in ordered)
    payload += NAME.encode()+b'\0'
    rawsize = align(len(payload), pe.u32(pe.opt+36))
    out = bytearray(data)
    section = pe.table+40*len(pe.sections)
    assert section+40 <= min(s[3] for s in pe.sections if s[3])
    assert not any(out[section:section+40])
    struct.pack_into('<8sIIIIIIHHI', out, section, b'.aagfix\0', len(payload), va,
                     rawsize, raw, 0, 0, 0, 0, 0x40000040)
    struct.pack_into('<H', out, pe.pe+6, len(pe.sections)+1)
    struct.pack_into('<I', out, pe.opt+56, align(va+len(payload), pe.u32(pe.opt+32)))
    struct.pack_into('<I', out, pe.opt+8, pe.u32(pe.opt+8)+rawsize)
    struct.pack_into('<I', out, pe.opt+64, 0)  # PE checksum is optional for user DLLs
    struct.pack_into('<I', out, pe.exp+24, count)
    struct.pack_into('<II', out, pe.exp+32, va, va+4*count)
    out.extend(b'\0'*(raw-len(out)))
    out.extend(payload)
    out.extend(b'\0'*(rawsize-len(payload)))
    new = PE(out).entries()
    assert all(new[name] == value for name, value in old.items())
    assert new[NAME][1:] == old[TARGET][1:]
    # All executable sections remain byte-for-byte unchanged.
    for i, (_, _, size, offset) in enumerate(pe.sections):
        if pe.u32(pe.table+40*i+36) & 0x20000000:
            assert out[offset:offset+size] == data[offset:offset+size]
    return bytes(out)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dll', type=Path)
    args = parser.parse_args()
    path = args.dll.resolve()
    if path.name.lower() != 'user32.dll':
        parser.error('Only user32.dll is eligible')
    data = path.read_bytes()
    backup = path.with_name('user32.dll.aag-original')
    if backup.exists():
        original = backup.read_bytes()
        result = patch(original)
        if data == result:
            print(json.dumps({'status': 'already patched', 'sha256': hashlib.sha256(data).hexdigest()}))
            return
        if data != original:
            raise ValueError('Existing backup does not match current file; refusing overwrite')
    result = patch(data)
    if not backup.exists():
        with backup.open('xb') as stream: stream.write(data)
    temporary = path.with_name(path.name+'.aag-new')
    with temporary.open('xb') as stream: stream.write(result)
    temporary.chmod(path.stat().st_mode & 0o777)
    temporary.replace(path)
    print(json.dumps({'status': 'patched', 'original_sha256': STOCK,
                      'sha256': hashlib.sha256(result).hexdigest(), 'backup': str(backup),
                      'new_export': NAME, 'alias': TARGET, 'executable_code_changed': False}))

if __name__ == '__main__': main()
