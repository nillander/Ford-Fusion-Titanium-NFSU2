"""Generates new window glass (one clean single-sided sheet per window, retail UG2 style).
Only the shape of the MW glass is used: outer faces -> per-window smooth surface fit (polynomial over the
window's own plane) -> outline dilated by D so it runs under the body frame -> fresh Delaunay mesh."""
import pickle, sys, numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import Delaunay, cKDTree
from scipy import ndimage
from matplotlib.path import Path
import contourpy

D = float(sys.argv[1]) if len(sys.argv) > 1 else 0.015     # m under the frame
STEP = 0.06        # interior point spacing (m)
EDGE = 0.03        # max outline segment (m)
RES = 0.002        # raster resolution (m)
DEG = 6
TUCK = 0.35       # inward drop per metre beyond the original edge


def load(pkl, mw='MUSTANGGT'):
    P = pickle.load(open(pkl, 'rb'))
    pos, tri, nrm, uv, col = [], [], [], [], []; o = 0
    for part in ['%s_KIT00_FRONT_WINDOW_A' % mw, '%s_KIT00_REAR_WINDOW_A' % mw]:
        for g in P[part]['groups']:
            pos.append(g['pos']); nrm.append(g['nrm']); uv.append(g['uv']); col.append(g['col']); tri.append(g['tri'] + o); o += len(g['pos'])
    pos, nrm, uv, col, tri = map(np.concatenate, (pos, nrm, uv, col, tri))
    c = pos[tri].mean(1)
    fn = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])
    ax = np.zeros_like(c); ax[:, 0] = np.clip(c[:, 0], -0.9, 0.5); ax[:, 2] = 0.75
    tri = tri[((c - ax) * fn).sum(1) > 0]          # outer layer only
    return P, pos, nrm, uv, col, tri


def panes(pos, tri):
    k = np.round(pos / 2e-3).astype(np.int64)
    _, inv = np.unique(k, axis=0, return_inverse=True); inv = inv.ravel()
    t = inv[tri]; n = inv.max() + 1
    r = np.r_[t[:, 0], t[:, 1], t[:, 2]]; cc = np.r_[t[:, 1], t[:, 2], t[:, 0]]
    _, lab = connected_components(coo_matrix((np.ones(len(r)), (r, cc)), shape=(n, n)), directed=False)
    fl = lab[t[:, 0]]
    return [tri[fl == L] for L in np.unique(fl)]


def monomials(u, v, deg):
    return np.stack([u ** i * v ** j for i in range(deg + 1) for j in range(deg + 1 - i)], -1)


def dmono(u, v, deg):
    du = np.stack([i * u ** max(i - 1, 0) * v ** j if i else 0 * u for i in range(deg + 1) for j in range(deg + 1 - i)], -1)
    dv = np.stack([j * u ** i * v ** max(j - 1, 0) if j else 0 * u for i in range(deg + 1) for j in range(deg + 1 - i)], -1)
    return du, dv


def rdp(pts, eps):
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]; ab = b - a; L = np.linalg.norm(ab) + 1e-12
    d = np.abs(ab[0] * (pts[:, 1] - a[1]) - ab[1] * (pts[:, 0] - a[0])) / L
    i = np.argmax(d)
    if d[i] > eps:
        return np.r_[rdp(pts[:i + 1], eps)[:-1], rdp(pts[i:], eps)]
    return np.r_[[a], [b]]


def build_pane(pos, nrm, uv, col, tri):
    vid = np.unique(tri); p = pos[vid]
    mu = p.mean(0)
    _, _, Vt = np.linalg.svd(p - mu); E = Vt                     # rows: e1, e2, normal
    nmean = nrm[vid].mean(0)
    if E[2] @ nmean < 0: E[2] = -E[2]
    if np.linalg.det(E) < 0: E[1] = -E[1]
    L = (p - mu) @ E.T
    s = np.abs(L[:, :2]).max()
    A = monomials(L[:, 0] / s, L[:, 1] / s, DEG)
    coef, *_ = np.linalg.lstsq(A, L[:, 2], rcond=None)
    resid = np.abs(A @ coef - L[:, 2]).max()
    # raster of the pane footprint in its plane
    T = (pos[tri] - mu) @ E.T
    lo = T[..., :2].reshape(-1, 2).min(0) - D - 0.02; hi = T[..., :2].reshape(-1, 2).max(0) + D + 0.02
    nx, ny = (np.ceil((hi - lo) / RES).astype(int) + 1)
    mask = np.zeros((ny, nx), bool)
    for t in T[..., :2]:
        x = (t[:, 0] - lo[0]) / RES; y = (t[:, 1] - lo[1]) / RES
        x0, x1 = int(np.floor(x.min())), int(np.ceil(x.max())); y0, y1 = int(np.floor(y.min())), int(np.ceil(y.max()))
        X, Y = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        ar = (x[1] - x[0]) * (y[2] - y[0]) - (x[2] - x[0]) * (y[1] - y[0])
        if abs(ar) < 1e-12: continue
        w0 = ((x[1] - X) * (y[2] - Y) - (x[2] - X) * (y[1] - Y)) / ar
        w1 = ((x[2] - X) * (y[0] - Y) - (x[0] - X) * (y[2] - Y)) / ar
        ins = (w0 >= -0.02) & (w1 >= -0.02) & (1 - w0 - w1 >= -0.02)
        mask[Y[ins], X[ins]] = True
    mask = ndimage.binary_closing(mask, iterations=2)
    mask = ndimage.binary_fill_holes(mask)
    outside = ndimage.distance_transform_edt(~mask) * RES      # distance beyond the original glass edge
    r = int(round(D / RES))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    mask = ndimage.binary_dilation(mask, structure=(xx ** 2 + yy ** 2) <= r * r)
    gen = contourpy.contour_generator(z=mask.astype(float))
    lines = gen.lines(0.5)
    ring = max(lines, key=len)
    ring = ring * RES + lo
    h = len(ring) // 2
    ring = np.r_[rdp(ring[:h + 1], 0.0015)[:-1], rdp(np.r_[ring[h:], ring[:1]], 0.0015)[:-1]]
    # resample long segments
    out = []
    for i in range(len(ring)):
        a, b = ring[i], ring[(i + 1) % len(ring)]
        k = max(1, int(np.ceil(np.linalg.norm(b - a) / EDGE)))
        out += [a + (b - a) * j / k for j in range(k)]
    ring = np.array(out)
    path = Path(ring)
    gx, gy = np.meshgrid(np.arange(lo[0], hi[0], STEP), np.arange(lo[1], hi[1], STEP))
    g = np.c_[gx.ravel(), gy.ravel()]
    g = g[path.contains_points(g)]
    if len(g):
        dist, _ = cKDTree(ring).query(g); g = g[dist > STEP * 0.45]
    pts = np.r_[ring, g]
    dt = Delaunay(pts)
    F = dt.simplices
    cen = pts[F].mean(1)
    F = F[path.contains_points(cen)]
    # lift to the fitted surface
    u, v = pts[:, 0] / s, pts[:, 1] / s
    w = monomials(u, v, DEG) @ coef
    du, dv = dmono(u, v, DEG)
    gu, gv = (du @ coef) / s, (dv @ coef) / s
    Lp = np.c_[pts, w]; Ln = np.c_[-gu, -gv, np.ones_like(gu)]; Ln /= np.linalg.norm(Ln, axis=1, keepdims=True)
    ix = np.clip(((pts[:, 0] - lo[0]) / RES).round().astype(int), 0, mask.shape[1] - 1)
    iy = np.clip(((pts[:, 1] - lo[1]) / RES).round().astype(int), 0, mask.shape[0] - 1)
    Lp = Lp - Ln * (TUCK * outside[iy, ix])[:, None]           # border bends into the car, under the frame
    P3 = Lp @ E + mu; N3 = Ln @ E
    # winding: face normal along the surface normal
    fnn = np.cross(P3[F[:, 1]] - P3[F[:, 0]], P3[F[:, 2]] - P3[F[:, 0]])
    flip = (fnn * N3[F].mean(1)).sum(1) < 0
    F[flip] = F[flip][:, ::-1]
    kd = cKDTree(pos[vid]); _, nn = kd.query(P3)
    return dict(pos=P3, nrm=N3, uv=uv[vid][nn], col=col[vid][nn], tri=F), resid, len(F)


if __name__ == '__main__':
    P, pos, nrm, uv, col, tri = load('glass_src.pkl')
    res = []
    for pt in panes(pos, tri):
        m, resid, n = build_pane(pos, nrm, uv, col, pt)
        c = m['pos'].mean(0)
        print('pane at', c.round(2), 'fit residual %.1f mm' % (resid * 1000), 'tris', n)
        res.append(m)
    pickle.dump(res, open('newglass_%d.pkl' % round(D * 1000), 'wb'))
    print('total tris', sum(len(m['tri']) for m in res))
