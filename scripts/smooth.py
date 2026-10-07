import numpy as np
def smooth_normals(pos, tri, nrm_ref, crease_deg=40, weld=1e-4):
    """area-weighted face normals averaged over welded positions, but only among faces within `crease_deg`
    of the vertex's own reference normal (keeps hard edges where the source split them)"""
    fn = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])
    fa = np.linalg.norm(fn, axis=1); fu = fn / (fa[:, None] + 1e-20)
    k = np.round(pos / weld).astype(np.int64); _, gid = np.unique(k, axis=0, return_inverse=True); gid = gid.ravel()
    # per attribute vertex: faces of its welded position
    from collections import defaultdict
    vf = defaultdict(list)
    for f, t in enumerate(tri):
        for v in t: vf[gid[v]].append(f)
    ref = nrm_ref / (np.linalg.norm(nrm_ref, axis=1, keepdims=True) + 1e-12)
    # reference = average of the faces that use this attribute vertex (robust even if nrm_ref is bad)
    own = np.zeros_like(pos)
    for kk in range(3): np.add.at(own, tri[:, kk], fn)
    own /= np.linalg.norm(own, axis=1, keepdims=True) + 1e-20
    c = np.cos(np.radians(crease_deg)); out = np.empty_like(pos)
    for v in range(len(pos)):
        fs = np.array(vf[gid[v]]); w = fu[fs] @ own[v]
        sel = fs[w > c]
        n = fn[sel].sum(0) if len(sel) else own[v]
        out[v] = n / (np.linalg.norm(n) + 1e-20)
    return out


def relax_normals(pos, tri, nrm, iters=2, max_deg=30, weld=1e-4, alpha=0.5):
    """keeps the source (MW) normals but (1) averages coincident vertices whose normals differ < max_deg
    (seams from UV/mirror splits, not hard edges) and (2) blends each normal with its 1-ring neighbours that
    are within max_deg (damps lighting waves from a faceted mesh). Geometry is not moved."""
    n = nrm / (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12)
    k = np.round(pos / weld).astype(np.int64); _, gid = np.unique(k, axis=0, return_inverse=True); gid = gid.ravel()
    c = np.cos(np.radians(max_deg))
    # neighbour pairs: triangle edges + coincident vertices
    e = np.r_[tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]
    order = np.argsort(gid); gs = gid[order]
    starts = np.r_[0, np.nonzero(np.diff(gs))[0] + 1]; ends = np.r_[starts[1:], len(gs)]
    co = [(order[a], order[b]) for s0, s1 in zip(starts, ends) if s1 - s0 > 1 for a in range(s0, s1) for b in range(a + 1, s1)]
    pairs = np.r_[e, np.array(co, np.int64).reshape(-1, 2)] if co else e
    for _ in range(iters):
        ok = (n[pairs[:, 0]] * n[pairs[:, 1]]).sum(1) > c
        p = pairs[ok]
        acc = n.copy(); cnt = np.ones(len(n))
        np.add.at(acc, p[:, 0], n[p[:, 1]]); np.add.at(acc, p[:, 1], n[p[:, 0]])
        np.add.at(cnt, p[:, 0], 1); np.add.at(cnt, p[:, 1], 1)
        avg = acc / cnt[:, None]; avg /= np.linalg.norm(avg, axis=1, keepdims=True) + 1e-12
        n = (1 - alpha) * n + alpha * avg; n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    return n


def fair_region(m, inside, iters=12, lam=0.5, crease_deg=25, weld=1e-4, pin_border=True):
    """Moves vertices (welded by position) inside the region `inside(pos)->bool` along their normal towards the
    average of their 1-ring (only neighbours whose normal is within crease_deg), so bumps/dents flatten while
    creases, open borders and the region border stay. Returns a new mesh with recomputed smooth normals there."""
    pos = m['pos'].copy(); tri = m['tri']
    k = np.round(pos / weld).astype(np.int64); _, gid = np.unique(k, axis=0, return_inverse=True); gid = gid.ravel()
    ng = gid.max() + 1
    gp = np.zeros((ng, 3)); gp[gid] = pos
    gt = gid[tri]
    fn = np.cross(gp[gt[:, 1]] - gp[gt[:, 0]], gp[gt[:, 2]] - gp[gt[:, 0]])
    gn = np.zeros((ng, 3))
    for kk in range(3): np.add.at(gn, gt[:, kk], fn)
    gn /= np.linalg.norm(gn, axis=1, keepdims=True) + 1e-20
    e = np.r_[gt[:, [0, 1]], gt[:, [1, 2]], gt[:, [2, 0]]]
    es = np.sort(e, 1); u, cnt = np.unique(es, axis=0, return_counts=True)
    border = np.zeros(ng, bool); border[u[cnt == 1].ravel()] = True
    free = inside(gp) & ~border
    if pin_border:   # vertices touching a face that leaves the region stay fixed
        out_face = ~inside(gp[gt].mean(1))
        free[np.unique(gt[out_face])] = False
    c = np.cos(np.radians(crease_deg))
    pairs = np.unique(np.r_[u, u[:, ::-1]], axis=0)
    for _ in range(iters):
        ok = (gn[pairs[:, 0]] * gn[pairs[:, 1]]).sum(1) > c
        p = pairs[ok]
        acc = np.zeros_like(gp); n = np.zeros(ng)
        np.add.at(acc, p[:, 0], gp[p[:, 1]]); np.add.at(n, p[:, 0], 1)
        has = n > 0
        d = np.zeros_like(gp); d[has] = acc[has] / n[has, None] - gp[has]
        d = (d * gn).sum(1, keepdims=True) * gn          # only along the normal
        gp[free] += lam * d[free]
    newpos = gp[gid]
    # normals of moved vertices: area-weighted face normals among faces within crease of the old normal
    moved = free[gid]
    fn2 = np.cross(newpos[tri[:, 1]] - newpos[tri[:, 0]], newpos[tri[:, 2]] - newpos[tri[:, 0]])
    acc = np.zeros_like(newpos)
    for kk in range(3): np.add.at(acc, gid[tri[:, kk]], fn2)   # per welded vertex (smooth)
    sm = acc[gid]; sm /= np.linalg.norm(sm, axis=1, keepdims=True) + 1e-20
    nrm = m['nrm'].copy()
    ref = nrm / (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-20)
    use = moved & ((sm * ref).sum(1) > np.cos(np.radians(crease_deg)))
    nrm[use] = sm[use]
    out = dict(m); out['pos'] = newpos; out['nrm'] = nrm
    return out, int(free.sum())


def transfer_normals(g, src, radius=0.03, k=8, cos_limit=0.5, chunk=256):
    """v12: give a decimated/LOD B paint mesh the authored normals of the LOD A surface. Each vertex takes the
    distance-weighted mean of the k nearest LOD A vertex normals within `radius` that agree with its own face
    normal (cos > cos_limit, so hard edges and the other side of thin panels are ignored). Geometry is not
    moved. Returns (mesh, vertices changed)."""
    p, t = g['pos'].astype(np.float64), g['tri']
    fn = np.cross(p[t[:, 1]] - p[t[:, 0]], p[t[:, 2]] - p[t[:, 0]])
    own = np.zeros_like(p)
    for kk in range(3):
        np.add.at(own, t[:, kk], fn)
    own /= np.linalg.norm(own, axis=1, keepdims=True) + 1e-20
    sp = src['pos'].astype(np.float64)
    sn = src['nrm'].astype(np.float64)
    sn /= np.linalg.norm(sn, axis=1, keepdims=True) + 1e-20
    # bucket the source by a coarse grid so each chunk only compares against nearby points
    cell = radius
    keys = np.floor(sp / cell).astype(np.int64)
    order = np.lexsort(keys.T[::-1])
    keys, sp, sn = keys[order], sp[order], sn[order]
    uniq, start = np.unique(keys, axis=0, return_index=True)
    end = np.r_[start[1:], len(keys)]
    lookup = {tuple(u): (s, e) for u, s, e in zip(uniq, start, end)}
    out = g['nrm'].astype(np.float64).copy()
    changed = 0
    qk = np.floor(p / cell).astype(np.int64)
    offs = np.array([(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)])
    for v in range(len(p)):
        idx = []
        for o in offs:
            r = lookup.get(tuple(qk[v] + o))
            if r:
                idx.append(np.arange(*r))
        if not idx:
            continue
        idx = np.concatenate(idx)
        d = np.linalg.norm(sp[idx] - p[v], axis=1)
        ok = (d < radius) & (sn[idx] @ own[v] > cos_limit)
        if not ok.any():
            continue
        idx, d = idx[ok], d[ok]
        sel = np.argsort(d)[:k]
        w = 1.0 / (d[sel] + 1e-4)
        n = (sn[idx[sel]] * w[:, None]).sum(0)
        out[v] = n / (np.linalg.norm(n) + 1e-20)
        changed += 1
    return dict(g, nrm=out.astype(g['nrm'].dtype)), changed


def orient_to_normals(g):
    """v12.1: turn faces whose winding disagrees with their own vertex normals (dot < 0). Such faces are
    culled from outside or, with both faces drawn, are lit from the inside; the export then replaced their
    vertex normals with the inward face normal, which showed as dark crackle. Returns (mesh, faces turned)."""
    p, t = g['pos'], g['tri']
    fn = np.cross(p[t[:, 1]] - p[t[:, 0]], p[t[:, 2]] - p[t[:, 0]])
    vn = g['nrm'][t].sum(1)
    bad = (fn * vn).sum(1) < 0
    if not bad.any():
        return g, 0
    t = t.copy()
    t[bad] = t[bad][:, ::-1]
    return dict(g, tri=t), int(bad.sum())
