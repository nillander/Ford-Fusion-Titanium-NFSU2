"""Half-edge-collapse QEM decimation that keeps UV/normal seams, material borders and open borders.

Input mesh uses "attribute vertices" (the game's split vertices).  Positions are welded to find
the real surface topology.  A collapse u->v is only accepted if every attribute vertex of u can be
mapped onto an attribute vertex of v through a triangle that contains the edge, so textures never
smear across seams.
"""
import heapq
import numpy as np


def _plane_quadrics(P, F):
    a, b, c = P[F[:, 0]], P[F[:, 1]], P[F[:, 2]]
    n = np.cross(b - a, c - a)
    area = np.linalg.norm(n, axis=1)
    ok = area > 1e-14
    n[ok] /= area[ok, None]
    d = -(n * a).sum(1)
    p = np.concatenate([n, d[:, None]], 1)
    Q = p[:, :, None] * p[:, None, :] * (area[:, None, None] * 0.5)
    Q[~ok] = 0
    return Q, n, area


def decimate(pos, tri, target_faces, feature_weight=50.0, max_normal_dev=0.25, lock_features=False, weld_eps=1e-5, verbose=False):
    pos = np.asarray(pos, np.float64)
    tri = np.asarray(tri, np.int64)
    key = np.round(pos / weld_eps).astype(np.int64)
    _, geo_of = np.unique(key, axis=0, return_inverse=True)
    geo_of = geo_of.reshape(-1)
    ng = geo_of.max() + 1
    gpos = np.zeros((ng, 3))
    gpos[geo_of] = pos
    FA = tri.copy()
    FG = geo_of[FA]
    good = (FG[:, 0] != FG[:, 1]) & (FG[:, 1] != FG[:, 2]) & (FG[:, 0] != FG[:, 2])
    FA = FA[good]; FG = FG[good]
    M = len(FA)
    alive = np.ones(M, bool)
    Qf, fn, farea = _plane_quadrics(gpos, FG)
    Q = np.zeros((ng, 4, 4))
    for k in range(3):
        np.add.at(Q, FG[:, k], Qf)
    vfaces = [set() for _ in range(ng)]
    for f in range(M):
        for k in range(3):
            vfaces[FG[f, k]].add(f)
    # edges -> faces
    edge_faces = {}
    for f in range(M):
        for k in range(3):
            a, b = FG[f, k], FG[f, (k + 1) % 3]
            e = (a, b) if a < b else (b, a)
            edge_faces.setdefault(e, []).append(f)
    feat = [set() for _ in range(ng)]
    bnd = [set() for _ in range(ng)]

    def attr_at(f, g):
        r = FG[f]
        return FA[f][0] if r[0] == g else (FA[f][1] if r[1] == g else FA[f][2])

    for (a, b), fl in edge_faces.items():
        is_feat = False
        if len(fl) == 1:
            bnd[a].add(b); bnd[b].add(a); is_feat = True
        elif len(fl) > 2:
            is_feat = True
        else:
            f1, f2 = fl
            if attr_at(f1, a) != attr_at(f2, a) or attr_at(f1, b) != attr_at(f2, b):
                is_feat = True
        if is_feat:
            feat[a].add(b); feat[b].add(a)
            # constraint plane: contains the edge, perpendicular to adjacent faces
            e = gpos[b] - gpos[a]
            L = np.linalg.norm(e)
            if L < 1e-12:
                continue
            for f in fl:
                n = np.cross(e, fn[f])
                nn = np.linalg.norm(n)
                if nn < 1e-12:
                    continue
                n /= nn
                d = -n @ gpos[a]
                p = np.r_[n, d]
                q = np.outer(p, p) * (L * L * feature_weight)
                Q[a] += q; Q[b] += q
    version = np.zeros(ng, np.int64)
    heap = []

    def cost(u, v):
        p = np.r_[gpos[v], 1.0]
        return float(p @ Q[u] @ p)

    def locked(u):
        k = len(feat[u])
        if k == 0:
            return False
        if lock_features:
            return True
        return k != 2

    def push_vertex(u):
        if locked(u):
            return
        nb = set()
        for f in vfaces[u]:
            nb.update(FG[f].tolist())
        nb.discard(u)
        for v in nb:
            if feat[u] and v not in feat[u]:
                continue
            heapq.heappush(heap, (cost(u, v), u, v, version[u]))

    for u in range(ng):
        push_vertex(u)
    faces_left = M
    it = 0
    while faces_left > target_faces and heap:
        c, u, v, ver = heapq.heappop(heap)
        if ver != version[u] or not vfaces[u] or not vfaces[v]:
            continue
        if locked(u):
            continue
        if feat[u] and v not in feat[u]:
            continue
        if bnd[u] and v not in bnd[u]:
            continue
        shared = [f for f in vfaces[u] if f in vfaces[v]]
        if not shared:
            continue
        # link condition
        nu = set(); nv = set()
        for f in vfaces[u]:
            nu.update(FG[f].tolist())
        for f in vfaces[v]:
            nv.update(FG[f].tolist())
        opp = set()
        for f in shared:
            for g in FG[f]:
                if g != u and g != v:
                    opp.add(g)
        if (nu & nv) - {u, v} != opp:
            continue
        # attribute mapping
        amap = {}
        for f in shared:
            amap[attr_at(f, u)] = attr_at(f, v)
        ok = True
        moving = [f for f in vfaces[u] if f not in vfaces[v]]
        for f in moving:
            if attr_at(f, u) not in amap:
                ok = False; break
        if not ok:
            continue
        # normal flip / sliver check
        for f in moving:
            r = FG[f].copy()
            old = np.cross(gpos[r[1]] - gpos[r[0]], gpos[r[2]] - gpos[r[0]])
            r[r == u] = v
            new = np.cross(gpos[r[1]] - gpos[r[0]], gpos[r[2]] - gpos[r[0]])
            no = np.linalg.norm(old); nn = np.linalg.norm(new)
            if nn < 1e-12 or no < 1e-14 or (old @ new) / (no * nn) < max_normal_dev:
                ok = False; break
        if not ok:
            continue
        # perform collapse
        for f in shared:
            alive[f] = False
            for g in FG[f]:
                vfaces[g].discard(f)
            faces_left -= 1
        for f in moving:
            for k in range(3):
                if FG[f, k] == u:
                    FA[f, k] = amap[FA[f, k]]
                    FG[f, k] = v
            vfaces[v].add(f)
        vfaces[u] = set()
        Q[v] += Q[u]
        for w in list(feat[u]):
            feat[w].discard(u)
            if w != v:
                feat[w].add(v); feat[v].add(w)
        feat[u] = set()
        for w in list(bnd[u]):
            bnd[w].discard(u)
            if w != v:
                bnd[w].add(v); bnd[v].add(w)
        bnd[u] = set()
        feat[v].discard(v); bnd[v].discard(v)
        version[u] += 1
        version[v] += 1
        touched = set()
        for f in vfaces[v]:
            touched.update(FG[f].tolist())
        for w in touched:
            version[w] += 1
            push_vertex(w)
        it += 1
        if verbose and it % 5000 == 0:
            print('  collapses', it, 'faces', faces_left, 'cost', c)
    F = FA[alive]
    used = np.unique(F)
    remap = np.full(len(pos), -1, np.int64)
    remap[used] = np.arange(len(used))
    return used, remap[F]


def recompute_normals(pos, nrm_orig, F, cos_limit=0.5, weld_eps=1e-5):
    """Smooth normals from the decimated faces, grouped by welded position; faces whose normal
    deviates too much from the vertex's original normal are ignored (keeps the original hard edges)."""
    pos = np.asarray(pos, np.float64)
    key = np.round(pos / weld_eps).astype(np.int64)
    _, geo = np.unique(key, axis=0, return_inverse=True)
    geo = geo.reshape(-1)
    a, b, c = pos[F[:, 0]], pos[F[:, 1]], pos[F[:, 2]]
    fnw = np.cross(b - a, c - a)  # area weighted
    fn = fnw / (np.linalg.norm(fnw, axis=1, keepdims=True) + 1e-20)
    no = nrm_orig / (np.linalg.norm(nrm_orig, axis=1, keepdims=True) + 1e-20)
    # faces per geo vertex
    ng = geo.max() + 1
    lists = [[] for _ in range(ng)]
    for f in range(len(F)):
        for k in range(3):
            lists[geo[F[f, k]]].append(f)
    out = no.copy()
    for v in range(len(pos)):
        fl = lists[geo[v]]
        if not fl:
            continue
        fl = np.array(fl)
        w = fn[fl] @ no[v]
        sel = fl[w > cos_limit]
        if len(sel) == 0:
            continue
        s = fnw[sel].sum(0)
        n = np.linalg.norm(s)
        if n > 1e-20:
            out[v] = s / n
    return out
