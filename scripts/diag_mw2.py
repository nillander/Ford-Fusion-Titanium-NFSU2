import sys, pickle, numpy as np, zdiag
from PIL import Image
P = pickle.load(open('mw_parts.pkl', 'rb'))
out = sys.argv[1]; names = sys.argv[2].split(','); cen = tuple(map(float, sys.argv[3].split(':'))); sc = float(sys.argv[4])
views = [tuple(map(float, v.split(':'))) for v in sys.argv[5].split(',')]
cols = [(230, 200, 40), (90, 120, 200), (120, 120, 120), (80, 180, 90)]
M = []
for k, n in enumerate(names):
    for g in P['MUSTANGGT_' + n]['groups']:
        M.append(dict(pos=g['pos'], nrm=g['nrm'], tri=g['tri'], color=cols[k % 4]))
ims = [zdiag.draw(M, a, e, W=900, H=500, scale=sc, center=cen, light=(-0.8, 0.2, 0.6)) for a, e in views]
W, H = ims[0].size; S = Image.new('RGB', (W*2, H*((len(ims)+1)//2)))
for i, im in enumerate(ims): S.paste(im, ((i % 2)*W, (i//2)*H))
S.save(out)
