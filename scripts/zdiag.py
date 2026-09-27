"""Z-buffer diagnostic renderer. Front faces: vertex-normal shading (as the game, no flipping).
Back faces (culled in game): magenta. Faces whose vertex normal disagrees with the face: green."""
import numpy as np
from PIL import Image
from diag import look
def draw(meshes, az=35, el=15, W=900, H=500, scale=180, center=(0, 0, 0.55), light=(0.4, 0.3, 0.85)):
    R = look(az, el); L = np.array(light, float); L /= np.linalg.norm(L)
    zb = np.full((H, W), -1e9); img = np.zeros((H, W, 3)); img[:] = (235, 238, 242)
    for m in meshes:
        pos = np.asarray(m['pos'], float); P = (pos - center) @ R.T
        sx = W/2 + P[:, 0]*scale; sy = H/2 - P[:, 1]*scale; sz = P[:, 2]
        t = np.asarray(m['tri'])
        wp = pos[t]; fn = np.cross(wp[:, 1]-wp[:, 0], wp[:, 2]-wp[:, 0]); fn /= np.linalg.norm(fn, axis=1, keepdims=True)+1e-12
        vn = np.asarray(m['nrm'], float); base = np.array(m.get('color', (190, 190, 190)), float)
        for i in range(len(t)):
            a, b, c = t[i]
            x0, x1, x2 = sx[a], sx[b], sx[c]; y0, y1, y2 = sy[a], sy[b], sy[c]
            area = (x1-x0)*(y2-y0) - (x2-x0)*(y1-y0)
            if abs(area) < 1e-9: continue
            xmin = max(int(min(x0, x1, x2)), 0); xmax = min(int(max(x0, x1, x2))+1, W-1)
            ymin = max(int(min(y0, y1, y2)), 0); ymax = min(int(max(y0, y1, y2))+1, H-1)
            if xmin > xmax or ymin > ymax: continue
            X, Y = np.meshgrid(np.arange(xmin, xmax+1)+0.5, np.arange(ymin, ymax+1)+0.5)
            w0 = ((x1-X)*(y2-Y)-(x2-X)*(y1-Y))/area; w1 = ((x2-X)*(y0-Y)-(x0-X)*(y2-Y))/area; w2 = 1-w0-w1
            ins = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not ins.any(): continue
            z = w0*sz[a]+w1*sz[b]+w2*sz[c]
            sub = zb[ymin:ymax+1, xmin:xmax+1]; upd = ins & (z > sub)
            if not upd.any(): continue
            sub[upd] = z[upd]
            if area > 0: col = np.array([255., 0, 255])
            else:
                n = w0[upd, None]*vn[a]+w1[upd, None]*vn[b]+w2[upd, None]*vn[c]
                n /= np.linalg.norm(n, axis=1, keepdims=True)+1e-12
                sh = 0.3+0.7*np.clip(n @ L, 0, 1)
                col = base[None]*sh[:, None]
                bad = (n @ fn[i]) < 0.2
                if bad.any(): col[bad] = (0, 170, 0)
            img[ymin:ymax+1, xmin:xmax+1][upd] = col
    return Image.fromarray(img.clip(0, 255).astype(np.uint8))
def sheet(meshes, views, out, W=900, H=500, scale=180, center=(0, 0, 0.55)):
    ims = [draw(meshes, a, e, W, H, scale, center) for a, e in views]
    S = Image.new('RGB', (W*2, H*((len(ims)+1)//2)), (255, 255, 255))
    for i, im in enumerate(ims): S.paste(im, ((i % 2)*W, (i//2)*H))
    S.save(out)
