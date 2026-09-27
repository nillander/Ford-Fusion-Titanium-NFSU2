"""Moves only one slot's wheels to the Fusion arches (X, Y). Everything else in the record stays.
usage: python globalb_wheels.py GlobalB.lzc GlobalB.lzc.new [2018|2012]"""
import struct, sys, ug2, ports
REC = 2192
FX, RX, WY = 1.431, -1.311, 0.78
D = bytearray(open(sys.argv[1], 'rb').read())
assert D[:4] != b'JDLZ', 'GlobalB is compressed'
for a, b, p, s in ug2.chunks(bytes(D), 0, len(D), 0, []):
    if b == 0x34600: base, size = p + 8, s
recs = {bytes(D[o:o + 32]).split(b'\0')[0].decode(): o for o in range(base + 8, base + size, REC)}
F = recs[ports.get(sys.argv[3] if len(sys.argv) > 3 else '2018')['ug2']]
for i, (x, y) in enumerate([(FX, WY), (FX, -WY), (RX, -WY), (RX, WY)]):   # FL, FR, RR, RL (+y = left)
    old = struct.unpack_from('<3f', D, F + 288 + 48 * i)
    struct.pack_into('<2f', D, F + 288 + 48 * i, x, y)
    print(i, [round(v, 3) for v in old], '->', [round(v, 3) for v in struct.unpack_from('<3f', D, F + 288 + 48 * i)])
open(sys.argv[2], 'wb').write(D)
