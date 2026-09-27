import sys, pickle, numpy as np, zdiag
P = pickle.load(open('mw_parts.pkl', 'rb'))
out = sys.argv[1]; names = sys.argv[2].split(',')
views = [tuple(map(float, v.split(':'))) for v in (sys.argv[3].split(',') if len(sys.argv) > 3 else ['35:15', '145:15', '-90:3', '90:3', '0:30', '180:25'])]
light = tuple(map(float, sys.argv[4].split(':'))) if len(sys.argv) > 4 else (0.4, 0.3, 0.85)
cols = [(230, 200, 40), (90, 120, 200), (200, 90, 60), (80, 180, 90), (160, 160, 160)]
M = []
for k, n in enumerate(names):
    for g in P['MUSTANGGT_' + n]['groups']:
        M.append(dict(pos=g['pos'], nrm=g['nrm'], tri=g['tri'], color=cols[k % len(cols)]))
ims = [zdiag.draw(M, a, e, light=light) for a, e in views]
from PIL import Image
W, H = ims[0].size
S = Image.new('RGB', (W*2, H*((len(ims)+1)//2)))
for i, im in enumerate(ims): S.paste(im, ((i % 2)*W, (i//2)*H))
S.save(out)
