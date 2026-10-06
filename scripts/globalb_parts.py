"""Gives one car slot the part-to-geometry layout of another slot (GlobalB.lzc, chunk 0x80034602).

Usage: python globalb_parts.py <src GlobalB> <dst GlobalB> [FROM=FOCUS] [TO=MUSTANGGT]

The car part database lists, for every car, the same 270 parts (BASE, KIT00_BODY, KITW01-04_BODY, KIT00_TRUNK,
KIT00_FRONT_WHEEL, bumpers, hoods, decals...). Each part record (14 bytes in 0x34604: name hash, part id,
sub id, flag, car index, attribute offset, attribute offset, model table) points with its last u16 to a 36-byte
model table in 0x3460A: [templated u8, 0, u16 string] + 8 string offsets, one per LOD (A, B, C, D, then four more).
A templated name is <CAR> + string + entry + _<LOD>, so a table can be shared by every car.

v10 finding: the MUSTANGGT records pointed at tables written by the custom Mustang mod, whose LOD A entry is the
empty string (MUSTANGGT_KIT00_A instead of MUSTANGGT_KIT00_BODY_A); BODY, TRUNK and FRONT_WHEEL were never drawn.
The fix points each MUSTANGGT record at the table its FOCUS twin uses: the layout set up by the Escort installer,
in which the approved v9 drew BODY_A, BASE_A, TRUNK_A, FRONT_WHEEL_A and the decals. Only the model table index
changes; part names, attributes and the tables themselves stay as they are (the tables are shared between cars).
"""
import struct, sys
from hashes import bh

src, dst = sys.argv[1], sys.argv[2]
FROM = sys.argv[3] if len(sys.argv) > 3 else 'FOCUS'
TO = sys.argv[4] if len(sys.argv) > 4 else 'MUSTANGGT'
D = bytearray(open(src, 'rb').read())
assert D[:4] != b'JDLZ', 'GlobalB is compressed; decompress first'
p = 0
while True:
    cid, size = struct.unpack_from('<II', D, p)
    if cid == 0x80034602:
        break
    p += 8 + size
subs = {}
q = p + 8
while q < p + 8 + size:
    cid, ss = struct.unpack_from('<II', D, q)
    subs[cid] = (q + 8, ss)
    q += 8 + ss
ob, sb = subs[0x3460B]
packs = list(struct.unpack_from('<%dI' % (sb // 4), D, ob))      # car / part pack names, hash order
o4, s4 = subs[0x34604]
recs = [o4 + i for i in range(0, s4 - 13, 14)]
cf, ct = packs.index(bh(FROM)), packs.index(bh(TO))
rf = [r for r in recs if D[r + 7] == cf]
rt = [r for r in recs if D[r + 7] == ct]
assert len(rf) == len(rt), (len(rf), len(rt))
for a, b in zip(rf, rt):          # same parts in the same order (part id and sub id checked)
    assert D[a + 4:a + 6] == D[b + 4:b + 6], (a, b)
changed = 0
for a, b in zip(rf, rt):
    xf = struct.unpack_from('<H', D, a + 12)[0]
    if struct.unpack_from('<H', D, b + 12)[0] != xf:
        struct.pack_into('<H', D, b + 12, xf)
        changed += 1
open(dst, 'wb').write(D)
print('%s <- %s: %d of %d part records now use the %s model tables' % (TO, FROM, changed, len(rt), FROM))
