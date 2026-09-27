"""Renders the compiled UG2 GEOMETRY.BIN/TEXTURES.BIN (read back from disk) with wheels at the GlobalB positions."""
import sys, numpy as np, ug2, tpk2, dxt, render
from PIL import Image
from hashes import bh
geo, texf, out = sys.argv[1], sys.argv[2], sys.argv[3]
body = sys.argv[4] if len(sys.argv) > 4 else 'FOCUS_KIT00_BODY_A'
WHEELS = [(1.431, 0.78, 0.098), (1.431, -0.78, 0.098), (-1.311, 0.78, 0.098), (-1.311, -0.78, 0.098)]
d, cl, h, S = ug2.parse(geo)
info, tex = tpk2.parse(texf)
T = {t['hash']: dxt.decode(t['data'], t['w'], t['h'], t['fmt']) for t in tex}
COL = {0x3C84D757: (35, 70, 150), bh('WINDOW'): (25, 30, 38)}
def meshes(s, xf=None):
    raw = np.frombuffer(s['vb'], np.uint8).reshape(-1, 36)
    pos = raw[:, :12].copy().view('<f4').reshape(-1, 3).astype(float)
    nrm = raw[:, 12:24].copy().view('<f4').reshape(-1, 3).astype(float)
    uv = raw[:, 28:36].copy().view('<f4').reshape(-1, 2).astype(float)
    if xf: pos, nrm = xf(pos, nrm)
    out = []
    for g in s['groups']:
        tri = s['ib'][g['off']:g['off'] + g['len']].reshape(-1, 3).astype(int)
        th = s['tex'][g['tex']]
        m = dict(pos=pos, nrm=nrm, uv=uv, tri=tri)
        if th in T: m['tex'] = T[th]
        else: m['color'] = COL.get(th, (255, 0, 255))
        out.append(m)
    return out
parts = {s['name']: s for s in S}
M = meshes(parts[body]) + meshes(parts['FOCUS_BASE_A']) + (meshes(parts['FOCUS_KIT00_TRUNK_A']) if 'FOCUS_KIT00_TRUNK_A' in parts else [])
wh = parts['FOCUS_KIT00_FRONT_WHEEL_A']
for x, y, z in WHEELS:
    def xf(p, n, x=x, y=y, z=z):
        p = p.copy(); n = n.copy()
        sgn = 1 if y > 0 else -1
        p[:, 1] = sgn * (0.11 - p[:, 1]); n[:, 1] = -sgn * n[:, 1]
        return p + [x, y, z], n
    M += meshes(wh, xf)
views = [(90, 3, 'side'), (35, 15, 'persp'), (0, 4, 'front'), (180, 4, 'rear'), (215, 18, 'persp2'), (-60, 35, 'top')]
ims = [render.render(M, a, e, W=1000, H=520, scale=205, center=(0, 0, 0.45)) for a, e, _ in views]
W, H = ims[0].size
sheet = Image.new('RGB', (W * 2, H * 3))
for i, im in enumerate(ims): sheet.paste(im, ((i % 2) * W, (i // 2) * H))
sheet.save(out)
