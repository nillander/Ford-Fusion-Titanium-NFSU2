"""Fast diagnostic renderer (painter's algorithm, PIL). Front faces shaded by *vertex normals*
(game-like, no flipping); faces seen from behind drawn magenta (in-game: culled -> hole)."""
import numpy as np
from PIL import Image, ImageDraw
def look(az, el):
    az = np.radians(az); el = np.radians(el)
    f = -np.array([np.cos(el)*np.cos(az), np.cos(el)*np.sin(az), np.sin(el)])
    r = np.cross(f, [0, 0, 1.]); r /= np.linalg.norm(r); u = np.cross(r, f)
    return np.stack([r, u, -f])
def draw(meshes, az=35, el=15, W=1000, H=560, scale=200, center=(0, 0, 0.55), light=(0.4, 0.3, 0.85)):
    R = look(az, el); L = np.array(light, float); L /= np.linalg.norm(L)
    polys = []
    for m in meshes:
        P = (np.asarray(m['pos'], float) - center) @ R.T
        t = np.asarray(m['tri']); p = P[t]
        sx = W/2 + p[..., 0]*scale; sy = H/2 - p[..., 1]*scale; z = p[..., 2].mean(1)
        area = (sx[:, 1]-sx[:, 0])*(sy[:, 2]-sy[:, 0]) - (sx[:, 2]-sx[:, 0])*(sy[:, 1]-sy[:, 0])
        wp = np.asarray(m['pos'], float)[t]
        fn = np.cross(wp[:, 1]-wp[:, 0], wp[:, 2]-wp[:, 0]); fn /= np.linalg.norm(fn, axis=1, keepdims=True)+1e-12
        vn = np.asarray(m['nrm'], float)[t].mean(1); vn /= np.linalg.norm(vn, axis=1, keepdims=True)+1e-12
        sh = 0.3 + 0.7*np.clip(vn @ L, 0, 1)
        base = np.array(m.get('color', (190, 190, 190)), float)
        for i in range(len(t)):
            if area[i] > 0:   # screen-space CW -> facing away (y is flipped)
                c = (255, 0, 255) if m.get('show_back', True) else None
            else:
                c = tuple(int(x) for x in base*sh[i])
                if (vn[i] @ fn[i]) < 0.2: c = (0, 160, 0)   # vertex normal disagrees with face
            if c is None: continue
            polys.append((z[i], [(sx[i, k], sy[i, k]) for k in range(3)], c))
    polys.sort(key=lambda q: q[0])
    im = Image.new('RGB', (W, H), (235, 238, 242)); d = ImageDraw.Draw(im)
    for _, pts, c in polys: d.polygon(pts, fill=c)
    return im
def sheet(meshes, views, out, W=900, H=500, scale=180, center=(0, 0, 0.55)):
    ims = [draw(meshes, a, e, W, H, scale, center) for a, e in views]
    cols = 2; rows = (len(ims)+1)//2
    S = Image.new('RGB', (W*cols, H*rows), (255, 255, 255))
    for i, im in enumerate(ims): S.paste(im, ((i % cols)*W, (i//cols)*H))
    S.save(out)
