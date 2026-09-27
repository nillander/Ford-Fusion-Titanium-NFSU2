"""render chosen solids; glass (WINDOW tex) in blue, paint yellow, other grey; optional only-glass"""
import sys, os, numpy as np, ug2, zdiag
from hashes import bh
from PIL import Image
geo, out, names, views = sys.argv[1], sys.argv[2], sys.argv[3].split(','), [tuple(map(float, v.split(':'))) for v in sys.argv[4].split(',')]
only = sys.argv[5].split(',') if len(sys.argv) > 5 else None
COL = {0x3C84D757: (230, 200, 40), bh('WINDOW'): (90, 120, 200)}
d, cl, h, S = ug2.parse(geo); M = []
for s in S:
    if s['name'] not in names: continue
    raw = np.frombuffer(s['vb'], np.uint8).reshape(-1, 36)
    pos = raw[:, :12].copy().view('<f4').reshape(-1, 3); nrm = raw[:, 12:24].copy().view('<f4').reshape(-1, 3)
    for g in s['groups']:
        th = s['tex'][g['tex']]
        if only and '%08X' % th not in only: continue
        M.append(dict(pos=pos, nrm=nrm, tri=s['ib'][g['off']:g['off']+g['len']].reshape(-1, 3).astype(int), color=COL.get(th, (150, 150, 150))))
ims = [zdiag.draw(M, a, e, W=900, H=500, scale=200, center=(-0.3, 0, 0.9)) for a, e in views]
W, H = ims[0].size; Sh = Image.new('RGB', (W*2, H*((len(ims)+1)//2)), 'white')
for i, im in enumerate(ims): Sh.paste(im, ((i % 2)*W, (i//2)*H))
Sh.save(out)
