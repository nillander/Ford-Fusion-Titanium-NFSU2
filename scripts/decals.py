"""Decal placement solids (UG2 retail mechanism): each decal slot is a small mesh with UV 0..1 and one of the
global textures DUMMY_DECAL1..8 (0x910E6654..0x910E665B), material DECAL (0x02A05578).
Doors / quarters / windows come from the MW Fusion decal parts, re-projected onto the v5 glass and paint;
hood decals reuse the Corolla layout mapped onto the Fusion hood."""
import numpy as np
from hashes import bh

DECAL_MAT = 0x02A05578
SLOTS = [0x910E6654 + i for i in range(8)]
COL = 0xFF000000            # vertex colour used by every retail decal


def _closest_on_tris(p, A, B, C):
    """closest point on every triangle (A,B,C: (m,3)) to point p; returns points (m,3)"""
    ab = B - A; ac = C - A; ap = p - A
    d1 = (ab * ap).sum(1); d2 = (ac * ap).sum(1)
    bp = p - B; d3 = (ab * bp).sum(1); d4 = (ac * bp).sum(1)
    cp = p - C; d5 = (ab * cp).sum(1); d6 = (ac * cp).sum(1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    den = va + vb + vc; den = np.where(np.abs(den) < 1e-20, 1e-20, den)
    v = vb / den; w = vc / den
    res = A + ab * v[:, None] + ac * w[:, None]
    # regions
    m = (d1 <= 0) & (d2 <= 0); res[m] = A[m]
    m = (d3 >= 0) & (d4 <= d3); res[m] = B[m]
    m = (d6 >= 0) & (d5 <= d6); res[m] = C[m]
    vcr = (vc <= 0) & (d1 >= 0) & (d3 <= 0)
    t = d1 / np.where(d1 - d3 == 0, 1e-20, d1 - d3); res[vcr] = (A + ab * t[:, None])[vcr]
    vbr = (vb <= 0) & (d2 >= 0) & (d6 <= 0)
    t = d2 / np.where(d2 - d6 == 0, 1e-20, d2 - d6); res[vbr] = (A + ac * t[:, None])[vbr]
    var = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
    t = (d4 - d3) / np.where((d4 - d3) + (d5 - d6) == 0, 1e-20, (d4 - d3) + (d5 - d6)); res[var] = (B + (C - B) * t[:, None])[var]
    return res


def project(p, target, off=0.003, facing=None):
    """closest point on the target surface among faces looking the same way as `facing`, lifted `off` metres
    along that face normal. target = (pos, tri)"""
    tpos, ttri = target
    A, B, C = tpos[ttri[:, 0]], tpos[ttri[:, 1]], tpos[ttri[:, 2]]
    fn = np.cross(B - A, C - A); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
    sel = np.ones(len(A), bool) if facing is None else (fn @ facing) > 0.5
    A, B, C, fn = A[sel], B[sel], C[sel], fn[sel]
    out = np.empty_like(p); nout = np.empty_like(p)
    for i, q in enumerate(p):
        cpt = _closest_on_tris(q, A, B, C)
        k = np.argmin(((cpt - q) ** 2).sum(1))
        out[i] = cpt[k] + off * fn[k]; nout[i] = fn[k]
    return out, nout


def subdivide(pos, uv, tri, levels=2):
    pos = np.asarray(pos, float); uv = np.asarray(uv, float); tri = np.asarray(tri, np.int64)
    for _ in range(levels):
        P, U = list(pos), list(uv); cache = {}; T = []
        def mid(a, b):
            k = (min(a, b), max(a, b))
            if k not in cache:
                cache[k] = len(P); P.append((pos[a] + pos[b]) / 2); U.append((uv[a] + uv[b]) / 2)
            return cache[k]
        for a, b, c in tri:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            T += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
        pos, uv, tri = np.array(P), np.array(U), np.array(T)
    return pos, uv, tri


def mesh_from_groups(groups, target, off=0.003, levels=0):
    """groups: list of (slot_texture_hash, pos, uv, tri, facing). Returns solid-ready meshes list"""
    meshes = []
    for th, pos, uv, tri, facing in groups:
        if levels:
            pos, uv, tri = subdivide(pos, uv, tri, levels)
        p, n = project(np.asarray(pos, float), target, off=off, facing=facing)
        tri = np.asarray(tri, np.int64).copy()
        fn = np.cross(p[tri[:, 1]] - p[tri[:, 0]], p[tri[:, 2]] - p[tri[:, 0]])
        bad = (fn * n[tri].mean(1)).sum(1) < 0            # face must look outwards (the game culls back faces)
        tri[bad] = tri[bad][:, ::-1]
        meshes.append(dict(pos=p, nrm=n, uv=np.asarray(uv, float), col=np.full(len(p), COL, np.uint32),
                           tri=tri, tex=th, mat=DECAL_MAT))
    return meshes


def from_mw(P, part, keep_slots=True):
    gs = []
    for g in P[part]['groups']:
        name = g['tex']
        try:
            th = int(name, 16)
        except ValueError:
            th = bh(name)
        if th in SLOTS:
            nf = g['nrm'][g['tri']].mean(1).mean(0) if False else None
            p = g['pos']; t = g['tri']
            fn = np.cross(p[t[:, 1]] - p[t[:, 0]], p[t[:, 2]] - p[t[:, 0]]).sum(0)
            cen = p.mean(0); out = cen - np.array([np.clip(cen[0], -1.0, 1.0), 0, 0.7])
            fn = fn / (np.linalg.norm(fn) + 1e-12)
            if fn @ out < 0: fn = -fn                      # decal faces away from the car
            gs.append((th, p, g['uv'], t, fn))
    return gs


def _drop(xy, hpos, htri):
    """z of the hood top at each (x, y) (highest triangle hit by a vertical ray) and its face normal"""
    a, b, c = hpos[htri[:, 0]], hpos[htri[:, 1]], hpos[htri[:, 2]]
    fn = np.cross(b - a, c - a); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
    z = np.full(len(xy), np.nan); n = np.zeros((len(xy), 3))
    den = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
    ok = np.abs(den) > 1e-12
    for i, (x, y) in enumerate(xy):
        w0 = ((b[:, 1] - c[:, 1]) * (x - c[:, 0]) + (c[:, 0] - b[:, 0]) * (y - c[:, 1])) / np.where(ok, den, 1)
        w1 = ((c[:, 1] - a[:, 1]) * (x - c[:, 0]) + (a[:, 0] - c[:, 0]) * (y - c[:, 1])) / np.where(ok, den, 1)
        w2 = 1 - w0 - w1
        hit = ok & (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6) & (fn[:, 2] > 0.3)
        if hit.any():
            zz = (w0 * a[:, 2] + w1 * b[:, 2] + w2 * c[:, 2])[hit]
            k = np.argmax(zz); z[i] = zz[k]; n[i] = fn[hit][k]
    return z, n


def hood_from_corolla(npz, key, hood_pos, hood_tri, off=0.0, sub=10):
    """one flat rectangle per slot: the slot's footprint on the Corolla hood (normalised to the hood) placed
    on the Fusion hood top, subdivided and dropped onto the surface"""
    D = np.load(npz)
    cp = D[key + '_pos'].astype(float); ch = D['hood_pos'].astype(float)
    ib = D[key + '_ib']; gt = D[key + '_gtex']; tex = D[key + '_tex']
    lo_c, hi_c = ch.min(0), ch.max(0)
    top = hood_pos[hood_pos[:, 2] > np.percentile(hood_pos[:, 2], 30)]
    lo_f = np.array([top[:, 0].min() + 0.08, top[:, 1].min() + 0.08]); hi_f = np.array([top[:, 0].max() - 0.06, top[:, 1].max() - 0.08])
    gs = []
    for ti in np.unique(gt):
        v = cp[np.unique(ib[gt == ti])][:, :2]
        a = np.clip((v.min(0) - lo_c[:2]) / (hi_c[:2] - lo_c[:2]), 0, 1); b = np.clip((v.max(0) - lo_c[:2]) / (hi_c[:2] - lo_c[:2]), 0, 1)
        x0, y0 = lo_f + a * (hi_f - lo_f); x1, y1 = lo_f + b * (hi_f - lo_f)
        us, vs = np.meshgrid(np.linspace(0, 1, sub + 1), np.linspace(0, 1, sub + 1))
        # UV: u along the car's width (y), v from the front of the car backwards, as the retail slots
        xy = np.c_[(x1 - (x1 - x0) * vs).ravel(), (y0 + (y1 - y0) * us).ravel()]
        z, n = _drop(xy, hood_pos, hood_tri)
        if np.isnan(z).any():
            continue
        p = np.c_[xy, z] + off * n
        uv = np.c_[us.ravel(), vs.ravel()]
        t = []
        for r in range(sub):
            for c_ in range(sub):
                i0 = r * (sub + 1) + c_; i1 = i0 + 1; i2 = i0 + sub + 1; i3 = i2 + 1
                t += [(i0, i1, i3), (i0, i3, i2)]
        gs.append((int(tex[ti]), p, uv, np.array(t), np.array([0, 0, 1.0])))
    return gs
