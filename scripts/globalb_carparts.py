"""Reads the car part database of GlobalB.lzc (chunk 0x80034602) and prints, for one car, which geometry name each
part asks for at each LOD. Read-only. Decoded in v10.4 (06/10/2026).

Usage: python globalb_carparts.py GlobalB.lzc MUSTANGGT [FOCUS]   (a second car prints side by side)

Layout (UG2, as saved by Nikki):
  0x34603  header: ..., n attributes (4636), n packs (75), n model tables, n parts (12167)
  0x34606  string table; strings are addressed by offset / 4
  0x3460B  75 pack hashes in hash order (every car, plus ROOF, AUDIO, WHEELS, SPOILER, MIRRORS_*...);
           a part's car is the index in this list
  0x34605  attributes, 8 bytes (key hash, value);  0x3460C  u16 attribute index lists
  0x3460A  model tables, 36 bytes: u8 templated, u8 0, u16 string, 8 x u32 (LOD A, B, C, D, then four more).
           templated name = <CAR> + string + entry + _<LOD>; an entry of -1 means no model at that LOD.
           templated == 0: the 8 u32 are full name hashes (brakes).  Tables are shared between cars (Nikki dedups).
  0x34604  parts, 14 bytes: u32 hash of '<CAR>_<PART>' (e.g. MUSTANGGT_KIT00_BODY), u8 part id, u8 sub id, u8 flag,
           u8 car (index in 0x3460B), u16 attributes, u16 attributes, u16 model table index (x 36 bytes)
Part ids seen: 0 BASE, 1 FRONT_BUMPER, 2 REAR_BUMPER, 5 KIT00_BODY, 6 KITW00-04_BODY, 9 HOOD, 10 TRUNK, 11 SKIRT,
12 SPOILER, 13 ENGINE, 14 HEADLIGHT, 15 BRAKELIGHT, 16 EXHAUST, 17-22 DOORS/PANELS/SILLS, 25 HOOD_UNDER,
26 TRUNK_UNDER, 27 FRONT_BRAKE, 28 FRONT_WHEEL, 37-47 DECALS, 60 TRUNK_AUDIO, 68 (5 per car, unknown).
"""
import struct, sys
from hashes import bh


def load(path):
    D = open(path, 'rb').read()
    p = 0
    while True:
        cid, size = struct.unpack_from('<II', D, p)
        if cid == 0x80034602:
            break
        p += 8 + size
    subs, q = {}, p + 8
    while q < p + 8 + size:
        cid, ss = struct.unpack_from('<II', D, q)
        subs[cid] = (q + 8, ss)
        q += 8 + ss
    return D, subs


def part_names():
    out = ['BASE', 'KIT00_BODY', 'KIT00_TRUNK', 'KIT00_FRONT_WHEEL', 'KIT00_HOOD', 'KIT00_SPOILER', 'KIT00_ENGINE',
           'KIT00_HEADLIGHT', 'KIT00_BRAKELIGHT', 'KIT00_EXHAUST', 'KIT00_HOOD_UNDER', 'KIT00_TRUNK_UNDER',
           'KIT00_FRONT_BRAKE']
    for k in range(0, 32):
        for p in ('FRONT_BUMPER', 'REAR_BUMPER', 'SKIRT', 'TRUNK_AUDIO'):
            out.append('KIT%02d_%s' % (k, p))
        for p in ('HOOD', 'HOOD_CF', 'HEADLIGHT', 'BRAKELIGHT', 'ENGINE'):
            out.append('STYLE%02d_%s' % (k, p))
    for w in range(0, 5):
        for p in ('BODY', 'DOOR_LEFT', 'DOOR_RIGHT', 'DOOR_PANEL_LEFT', 'DOOR_PANEL_RIGHT', 'DOOR_SILL_LEFT', 'DOOR_SILL_RIGHT'):
            out.append(('KIT00_' if w == 0 else 'KITW%02d_' % w) + p)
        out.append('KITW%02d_BODY' % w)
    for d in ('FRONT_WINDOW_WIDE_MEDIUM', 'REAR_WINDOW_WIDE_MEDIUM', 'HOOD_RECT_MEDIUM', 'HOOD_RECT_SMALL',
              'LEFT_DOOR_RECT_MEDIUM', 'RIGHT_DOOR_RECT_MEDIUM', 'LEFT_QUARTER_RECT_MEDIUM', 'RIGHT_QUARTER_RECT_MEDIUM'):
        out.append('DECAL_' + d)
        out += ['WIDE%d_DECAL_%s' % (w, d) for w in range(1, 5)]
    return out


def car_parts(D, subs, car):
    o6, s6 = subs[0x34606]
    st = D[o6:o6 + s6]
    s_at = lambda off: st[off:st.find(b'\0', off)].decode('latin1')
    ob, sb = subs[0x3460B]
    packs = list(struct.unpack_from('<%dI' % (sb // 4), D, ob))
    oa, sa = subs[0x3460A]
    o4, s4 = subs[0x34604]
    ci = packs.index(bh(car))
    names = {bh(car + '_' + n): n for n in part_names()}
    rows = []
    for i in range(0, s4 - 13, 14):
        h, pid, sub, flag, c, a1, a2, x = struct.unpack_from('<IBBBBHHH', D, o4 + i)
        if c != ci:
            continue
        if x == 0xFFFF:
            desc = 'no model'
        else:
            t = D[oa + x * 36:oa + x * 36 + 36]
            templ, _, s = struct.unpack_from('<BBH', t)
            vals = struct.unpack_from('<8I', t, 4)
            if templ == 1:
                desc = [(car + s_at(s * 4) + s_at(v * 4) + '_' + 'ABCDEFGH'[k]) for k, v in enumerate(vals) if v != 0xFFFFFFFF]
            else:
                desc = ['%08X' % v for v in vals if v != 0xFFFFFFFF]
        rows.append((names.get(h, '%08X' % h), pid, sub, x, desc))
    return rows


if __name__ == '__main__':
    D, subs = load(sys.argv[1])
    cars = sys.argv[2:] or ['MUSTANGGT']
    tables = [car_parts(D, subs, c) for c in cars]
    for k, row in enumerate(tables[0]):
        line = '%-34s pid%-3d sub%-3d x%-5d %s' % (row[0], row[1], row[2], row[3], row[4])
        for t in tables[1:]:
            line += '   ||  x%-5d %s' % (t[k][3], t[k][4])
        print(line)
