"""Restore only the title-screen copyright entry in an UG2 language file.

Usage: python restore_startup_copyright.py input.bin output.bin
Keeps every other string, offset and chunk byte unchanged.
"""
import struct
import sys
from pathlib import Path

def restore(source, output):
    data = bytearray(Path(source).read_bytes())
    assert struct.unpack_from('<I', data)[0] == 0x39000, 'unexpected language chunk'
    _, count, table, strings = struct.unpack_from('<4I', data, 8)
    for i in range(count):
        key, offset = struct.unpack_from('<II', data, 8 + table + i * 8)
        if key == 0x181419E5:
            start = 8 + strings + offset
            end = data.index(0, start)
            text = '\u00a9 2004 Electronic Arts Inc. Todos os direitos reservados.'.encode('cp1252')
            assert len(text) <= end - start, 'replacement does not fit existing allocation'
            data[start:end] = text.ljust(end - start, b'\0')
            Path(output).write_bytes(data)
            print('Restored title-screen copyright, key 181419E5; all other bytes preserved.')
            return
    raise ValueError('title-screen copyright entry missing')

if __name__ == '__main__':
    restore(*sys.argv[1:])
