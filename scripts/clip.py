"""Clip a mesh with planes (keeps faces split exactly on the plane, attributes interpolated)."""
import numpy as np


def clip_plane(m, n, d, keep_positive=True):
    """keep the part where pos.n - d >= 0 (or <= 0). m: dict pos,nrm,uv,col,tri"""
    s = m['pos'] @ np.asarray(n, float) - d
    if not keep_positive: s = -s
    P, N, U, C = [m['pos']], [m['nrm']], [m['uv']], [m['col']]
    nv = len(m['pos']); cache = {}; T = []
    def cut(a, b):
        k = (min(a, b), max(a, b))
        if k not in cache:
            t = s[a] / (s[a] - s[b])
            P.append((m['pos'][a] + t * (m['pos'][b] - m['pos'][a]))[None]); N.append((m['nrm'][a] + t * (m['nrm'][b] - m['nrm'][a]))[None])
            U.append((m['uv'][a] + t * (m['uv'][b] - m['uv'][a]))[None]); C.append(m['col'][a:a + 1])
            cache[k] = nv + len(cache)
        return cache[k]
    for tri in m['tri']:
        ins = s[tri] >= 0
        if ins.all(): T.append(tuple(tri)); continue
        if not ins.any(): continue
        poly = []
        for i in range(3):
            a, b = tri[i], tri[(i + 1) % 3]
            if s[a] >= 0: poly.append(a)
            if (s[a] >= 0) != (s[b] >= 0): poly.append(cut(a, b))
        for i in range(1, len(poly) - 1): T.append((poly[0], poly[i], poly[i + 1]))
    out = dict(pos=np.concatenate(P), nrm=np.concatenate(N), uv=np.concatenate(U), col=np.concatenate(C),
               tri=np.array(T, np.int64).reshape(-1, 3))
    used = np.unique(out['tri']); remap = np.full(len(out['pos']), -1); remap[used] = np.arange(len(used))
    return dict(pos=out['pos'][used], nrm=out['nrm'][used], uv=out['uv'][used], col=out['col'][used], tri=remap[out['tri']])


def empty_like(m):
    return dict(pos=m['pos'][:0], nrm=m['nrm'][:0], uv=m['uv'][:0], col=m['col'][:0], tri=np.zeros((0, 3), np.int64))


def _sub(m, sel):
    t = m['tri'][sel]; used = np.unique(t); remap = np.full(len(m['pos']), -1); remap[used] = np.arange(len(used))
    return dict(pos=m['pos'][used], nrm=m['nrm'][used], uv=m['uv'][used], col=m['col'][used], tri=remap[t])


def _cat(parts, like):
    parts = [x for x in parts if len(x['tri'])]
    if not parts: return empty_like(like)
    o = {k: np.concatenate([x[k] for x in parts]) for k in ('pos', 'nrm', 'uv', 'col')}
    off = np.cumsum([0] + [len(x['pos']) for x in parts[:-1]])
    o['tri'] = np.concatenate([x['tri'] + f for x, f in zip(parts, off)])
    return o


def split_box(m, box):
    """box: dict with optional xmin,xmax,ymin,ymax,zmin,zmax. Returns (inside, outside) exactly cut.
    Only triangles touching the box are cut."""
    p = m['pos'][m['tri']]; lo = p.min(1); hi = p.max(1)
    touch = np.ones(len(m['tri']), bool)
    for ax, i in (('x', 0), ('y', 1), ('z', 2)):
        if ax + 'min' in box: touch &= hi[:, i] > box[ax + 'min']
        if ax + 'max' in box: touch &= lo[:, i] < box[ax + 'max']
    far = _sub(m, ~touch)
    ins, outs = _split_box(_sub(m, touch), box)
    return ins, _cat([far, outs], m)


def _split_box(m, box):
    planes = []
    for ax, i in (('x', 0), ('y', 1), ('z', 2)):
        n = np.zeros(3); n[i] = 1
        if ax + 'min' in box: planes.append((n, box[ax + 'min'], True))
        if ax + 'max' in box: planes.append((n, box[ax + 'max'], False))
    outs = []; rest = m
    for n, d, pos in planes:
        outs.append(clip_plane(rest, n, d, keep_positive=not pos))
        rest = clip_plane(rest, n, d, keep_positive=pos)
    outs = [o for o in outs if len(o['tri'])]
    if outs:
        o = {k: np.concatenate([x[k] for x in outs]) for k in ('pos', 'nrm', 'uv', 'col')}
        off = np.cumsum([0] + [len(x['pos']) for x in outs[:-1]])
        o['tri'] = np.concatenate([x['tri'] + f for x, f in zip(outs, off)])
    else:
        o = empty_like(m)
    return rest, o
