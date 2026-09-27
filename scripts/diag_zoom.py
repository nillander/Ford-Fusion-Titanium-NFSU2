import sys, numpy as np, ug2, zdiag
from hashes import bh
from PIL import Image
geo, out = sys.argv[1], sys.argv[2]
names = sys.argv[3].split(','); cen = tuple(map(float, sys.argv[4].split(':'))); sc = float(sys.argv[5])
views = [tuple(map(float, v.split(':'))) for v in sys.argv[6].split(',')]
light = tuple(map(float, sys.argv[7].split(':'))) if len(sys.argv) > 7 else (0.4, 0.3, 0.85)
COL = {**{0x910E6654+i: c for i, c in enumerate([(255,0,0),(0,200,0),(0,120,255),(255,140,0),(160,0,255),(0,220,220),(255,0,160),(120,80,0)])}, 0x3C84D757: (230, 200, 40), bh('WINDOW'): (90, 120, 200), bh('FOCUS_LOGO'): (60, 60, 60), bh('FOCUS_MISC'): (130, 130, 130),
       bh('FOCUS_BRAKELIGHT_GLASS'): (220, 30, 30), bh('FOCUS_KIT00_BRAKELIGHT'): (200, 200, 220), bh('FOCUS_INTERIOR'): (100, 70, 40), bh('FOCUS_BADGING'): (255, 255, 255), bh('FOCUS_DRIVER'): (255, 150, 150), bh('FOCUS_KIT00_HEADLIGHT'): (150, 220, 255), bh('FOCUS_HEADLIGHT_GLASS'): (200, 255, 255)}
d, cl, h, S = ug2.parse(geo); M = []
for s in S:
    if s['name'] not in names and not ('DECAL' in s['name'] and 'WIDE' not in s['name'] and 'DECALS' in names): continue
    raw = np.frombuffer(s['vb'], np.uint8).reshape(-1, 36)
    pos = raw[:, :12].copy().view('<f4').reshape(-1, 3); nrm = raw[:, 12:24].copy().view('<f4').reshape(-1, 3)
    for g in s['groups']:
        M.append(dict(pos=pos, nrm=nrm, tri=s['ib'][g['off']:g['off']+g['len']].reshape(-1, 3).astype(int), color=COL.get(s['tex'][g['tex']], (170, 170, 170))))
ims = [zdiag.draw(M, a, e, W=900, H=500, scale=sc, center=cen, light=light) for a, e in views]
W, H = ims[0].size; Sh = Image.new('RGB', (W*2, H*((len(ims)+1)//2)), 'white')
for i, im in enumerate(ims): Sh.paste(im, ((i % 2)*W, (i//2)*H))
Sh.save(out)
