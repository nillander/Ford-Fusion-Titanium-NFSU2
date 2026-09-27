import sys, numpy as np, ug2, zdiag as diag
from hashes import bh
geo, out = sys.argv[1], sys.argv[2]
names = sys.argv[3].split(',') if len(sys.argv) > 3 else ['FOCUS_KIT00_BODY_A']
views = [tuple(map(float, v.split(':'))) for v in (sys.argv[4].split(',') if len(sys.argv) > 4 else ['35:15', '145:15', '-90:3', '90:3', '0:30', '180:25'])]
d, cl, h, S = ug2.parse(geo)
COL = {0x3C84D757: (230, 200, 40), bh('WINDOW'): (90, 120, 200)}
M = []
for s in S:
    if s['name'] not in names: continue
    raw = np.frombuffer(s['vb'], np.uint8).reshape(-1, 36)
    pos = raw[:, :12].copy().view('<f4').reshape(-1, 3); nrm = raw[:, 12:24].copy().view('<f4').reshape(-1, 3)
    for g in s['groups']:
        tri = s['ib'][g['off']:g['off'] + g['len']].reshape(-1, 3).astype(int)
        M.append(dict(pos=pos, nrm=nrm, tri=tri, color=COL.get(s['tex'][g['tex']], (170, 170, 170))))
import os; L=tuple(map(float,os.environ.get("LIGHT","0.4:0.3:0.85").split(":")))
ims=[diag.draw(M,a,e,light=L) for a,e in views]
from PIL import Image
W,H=ims[0].size
S=Image.new("RGB",(W*2,H*((len(ims)+1)//2)))
for i,im in enumerate(ims): S.paste(im,((i%2)*W,(i//2)*H))
S.save(out)
