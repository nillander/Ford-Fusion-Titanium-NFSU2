"""v12: paint-only reflection preview. Stripes of a studio environment are mapped through the vertex
normals (reflection of the view ray), as the UG2 car shader does with its environment map: crackled or wavy
normals show as broken stripes. Usage: preview_paint.py GEOMETRY.BIN out.png"""
import sys, numpy as np, ug2, render
from PIL import Image
from hashes import bh
geo, out = sys.argv[1:3]
S = ug2.parse(geo)[3]
slot = next(n for n in ('FOCUS', 'MUSTANGGT') if any(s['hash'] == bh(n + '_KIT00_BODY_A') for s in S))
env = np.zeros((256, 8, 3), np.uint8)
yy = np.linspace(0, 1, 256)
val = 70 + 150 * (0.5 + 0.5 * np.sin(yy * np.pi * 14)) ** 3
env[:] = val[:, None, None].astype(np.uint8)
views = [(90, 5, 230, (0, 0, .55)), (35, 12, 230, (0, 0, .55)), (145, 12, 230, (0, 0, .55))]
# optional close-ups: az,el,scale,cx,cy,cz
if len(sys.argv) > 3:
    views = [(float(a), float(b), float(c), (float(x), float(y), float(z))) for a, b, c, x, y, z in (v.split(',') for v in sys.argv[3:])]
ims = []
for az, el, sc, ce in views:
    R = render.look(az, el); vd = R[2]
    meshes = []
    for name in ('_KIT00_BODY_A', '_KIT00_TRUNK_A', '_BASE_A'):
        s = next(s for s in S if s['hash'] == bh(slot + name))
        raw = np.frombuffer(s['vb'], np.uint8).reshape(-1, 36)
        pos = raw[:, :12].copy().view('<f4').reshape(-1, 3).astype(float)
        nrm = raw[:, 12:24].copy().view('<f4').reshape(-1, 3).astype(float)
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
        d = -vd
        r = d - 2 * (nrm @ d)[:, None] * nrm
        uv = np.c_[np.full(len(pos), .5), 0.5 - 0.5 * r[:, 2]]
        for g in s['groups']:
            if s['tex'][g['tex']] != 0x3C84D757:
                continue
            tri = s['ib'][g['off']:g['off'] + g['len']].reshape(-1, 3).astype(int)
            meshes.append(dict(pos=pos, nrm=nrm, uv=uv, tri=tri, tex=env))
    ims.append(render.render(meshes, az, el, W=1100, H=520, scale=sc, center=ce, cull=True, flip_normals=False))
W, H = ims[0].size
sheet = Image.new('RGB', (W, H * len(ims)))
for i, im in enumerate(ims):
    sheet.paste(im, (0, i * H))
sheet.save(out)
