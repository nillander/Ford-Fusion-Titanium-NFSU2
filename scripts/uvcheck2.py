import sys, os, numpy as np, ug2, render
from PIL import Image, ImageOps
f, prefix, texpng, out = sys.argv[1:5]
tex = np.array(ImageOps.equalize(Image.open(texpng).convert('L')).convert('RGB'))
d, cl, h, S = ug2.parse(f)
M = []
for s in S:
    if not (s['name'].startswith(prefix) and (s['name'].endswith('_A') or s['name'] in [prefix + x for x in ('KIT00_FRONT_BUMPER_',)])): continue
    if 'DECAL' in s['name'] or 'WIDE' in s['name'] or 'KITW' in s['name'] or 'STYLE' in s['name'] or ('KIT' in s['name'] and 'KIT00' not in s['name']): continue
    nv = s['desc'][13]
    if nv == 0 or 'vb' not in s: continue
    raw = np.frombuffer(s['vb'], np.uint8)[:nv*36].reshape(nv, 36)
    pos = raw[:, :12].copy().view('<f4').reshape(-1, 3).astype(float); nrm = raw[:, 12:24].copy().view('<f4').reshape(-1, 3).astype(float); uv = raw[:, 28:36].copy().view('<f4').reshape(-1, 2).astype(float)
    for g in s['groups']:
        if s['tex'][g['tex']] != 0x3C84D757: continue
        ib = s['ib'][g['off']:g['off']+g['len']].astype(int)
        if len(ib) % 3: continue
        M.append(dict(pos=pos, nrm=nrm, uv=uv, tri=ib.reshape(-1, 3), tex=tex))
        print(s['name'], len(ib)//3, uv[ib].min(0).round(2), uv[ib].max(0).round(2))
views = [(90, 5), (-90, 5), (0, 89), (0, 10), (180, 10)]
ims = [render.render(M, a, e, W=700, H=400, scale=150, center=(0, 0, 0.6)) for a, e in views]
W, H = ims[0].size; S2 = Image.new('RGB', (W*2, H*3), 'white')
for i, im in enumerate(ims): S2.paste(im, ((i % 2)*W, (i//2)*H))
S2.save(out)
