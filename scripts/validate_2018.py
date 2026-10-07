"""Read back a v10.5 port; check budgets, wheel identity and called part names.

Usage: python validate_2018.py GEOMETRY TEXTURES GlobalB FOCUS_GEOMETRY
"""
import sys
import numpy as np
import ug2, tpk2, dxt, globalb_carparts, solid_lamps
from hashes import bh


def validate(geo, tex, bank, focus):
    solids = ug2.parse(geo)[3]
    textures = tpk2.parse(tex)[1]
    hashes = {s['hash'] for s in solids}
    assert len(hashes) == len(solids), 'duplicate solid hashes'
    available = {t['hash'] for t in textures}
    global_tex = {0x3C84D757, bh('WINDOW')} | {bh('DUMMY_DECAL%d' % n) for n in range(1, 9)}
    for s in solids:
        assert sum(g['len'] for g in s['groups']) <= 64500, s['name']
        assert len(s['vb']) // 36 <= 65535, s['name']
        assert set(s['tex']) <= available | global_tex, s['name']
        for g in s['groups']:
            assert s['ib'][g['off']:g['off'] + g['len']].max() < len(s['vb']) // 36
    wheel = next(s for s in solids if s['hash'] == bh('MUSTANGGT_KIT00_FRONT_WHEEL_A'))
    donor = next(s for s in ug2.parse(focus)[3] if s['hash'] == bh('FOCUS_KIT00_FRONT_WHEEL_A'))
    assert wheel['vb'] == donor['vb'], 'wheel vertex buffers differ'
    assert np.array_equal(wheel['ib'], donor['ib']), 'wheel index buffers differ'
    assert wheel['light'] == donor['light'], 'wheel materials differ'
    lamp = next(t for t in textures if t['hash'] == bh('MUSTANGGT_MISC'))
    assert bh('MUSTANGGT_SOLID_LAMPS') not in available, 'bespoke atlas still present'
    assert lamp['fmt'] in ('DXT1', b'DXT1')
    rgba = dxt.decode(lamp['data'], lamp['w'], lamp['h'], lamp['fmt'])
    assert (rgba[..., 3] == 255).all(), 'lamp atlas is transparent'
    red, white, gray = [rgba[int(uv[1] * lamp['h']), int(uv[0] * lamp['w'])]
                        for uv in (solid_lamps.RED_UV, solid_lamps.WHITE_UV, solid_lamps.GRAY_UV)]
    assert red[0] > 220 and 35 < red[1] < red[0] and red[2] < red[0], red
    assert min(white[:3]) > 200, white
    trim_cell = rgba[14 * lamp['h'] // 16:15 * lamp['h'] // 16,
                     12 * lamp['w'] // 16:13 * lamp['w'] // 16, :3]
    span = int(trim_cell.max()) - int(trim_cell.min())
    assert ((span < 10 and min(gray[:3]) > 245)
            or (span > 80 and trim_cell.max() > 225 and trim_cell.min() > 40)), 'invalid trim finish'
    data, subs = globalb_carparts.load(bank)
    rows = globalb_carparts.car_parts(data, subs, 'MUSTANGGT')
    for pid, name in ((5, 'KIT00_BODY'), (10, 'KIT00_TRUNK'), (28, 'KIT00_FRONT_WHEEL')):
        row = next(r for r in rows if r[1] == pid and r[2] == 0)
        full = 'MUSTANGGT_' + name + '_A'
        assert full in row[4] and bh(full) in hashes, (full, row)
    print('OK: budgets, indices, texture references, opaque lamps, exact 2012 wheel, BODY/TRUNK/WHEEL calls')


if __name__ == '__main__':
    validate(*sys.argv[1:])
