"""Opaque two-colour tail lamps, using the source red lens as the outline.

The white backing fills the opening in each red ring; no reflector, chrome
housing or internal fins are used. Four independent patches retain the seam
between the lid and the quarter panel. Only numpy is required.
"""
import numpy as np
import clip

RED_UV = np.array([13.5 / 16, 14.5 / 16])
WHITE_UV = np.array([14.5 / 16, 14.5 / 16])
GRAY_UV = np.array([12.5 / 16, 14.5 / 16])


def trunk_trim_mask(g):
    """Original 2018 cross-car trim island in BASE/MISC, independent of LOD numbering."""
    import comps
    labels = comps.components(g['pos'], g['tri'])
    selected = np.zeros(len(g['tri']), bool)
    for label in np.unique(labels):
        k = labels == label
        p = g['pos'][np.unique(g['tri'][k])]
        lo, hi = p.min(0), p.max(0)
        if (hi[0] < -1.7 and lo[2] > .67 and hi[2] < .75
                and lo[1] < -.45 and hi[1] > .45 and max(abs(lo[1]), abs(hi[1])) < .63):
            selected |= k
    return selected


def paint_misc(rgba, reflectors_only=False):
    """Three unused cells in the existing MISC sheet (original UVs end at v=.75)."""
    out = rgba.copy()
    h, w = out.shape[:2]
    cells = ((13, [255, 78, 86]), (14, [238, 240, 242])) if reflectors_only else (
        (12, [255, 255, 255]), (13, [255, 78, 86]), (14, [238, 240, 242]))
    for x, rgb in cells:
        out[14 * h // 16:15 * h // 16, x * w // 16:(x + 1) * w // 16] = rgb + [255]
    if reflectors_only:
        return out
    # A single vertical metallic highlight shared by the entire trim, distinct from
    # the plain lens-white cell. This stays in the existing opaque MISC texture.
    top, bottom = 14 * h // 16, 15 * h // 16
    height = np.linspace(1., 0., bottom - top)
    levels = [0., .23, .55, .78, 1.]
    shades = np.array([[64, 68, 74], [98, 102, 110], [178, 184, 190],
                       [248, 250, 252], [194, 202, 210]])
    gradient = np.stack([np.interp(height, levels, shades[:, k]) for k in range(3)], axis=1)
    out[top:bottom, 12 * w // 16:13 * w // 16, :3] = gradient[:, None].round().astype(np.uint8)
    return out


def gray_stripe(g, zmin=.685, zmax=.725, xmax=-1.78, ymax=.86, offset=.003):
    """Copy a rear surface as a white trim band (legacy GRAY_UV cell is now white)."""
    import clip
    band, _ = clip.split_box(g, dict(xmax=xmax, ymin=-ymax, ymax=ymax, zmin=zmin, zmax=zmax))
    if not len(band['tri']):
        return band
    band = dict(band)
    n = band['nrm'].astype(float)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    band['pos'] = band['pos'] + n * offset
    band['uv'] = np.tile(GRAY_UV, (len(band['pos']), 1))
    band['col'] = np.full(len(band['pos']), 0xFFFFFFFF, np.uint32)
    return band


def outer_trim(red, white, sign, seam=.585):
    """Front-facing continuation; stop before the lens wraps onto the body side."""
    bands = []
    for g in (red, white):
        band, _ = clip.split_box(g, dict(xmax=-1.97, ymin=-.775, ymax=.775,
                                        zmin=.702, zmax=.728))
        band = dict(band, pos=band['pos'] + np.array([-.003, 0., 0.]))
        bands.append(band)
    band = clip._cat(bands, white)
    return clip.clip_plane(band, [0, sign, 0], seam)


def lower_inner_white(red, white, trim):
    """Restore the lower insert's previous outline without extending its ends."""
    patch, _ = clip.split_box(white, dict(zmin=.663, zmax=.688))
    if not len(patch['tri']):
        return patch
    n = white['nrm'][0].copy()
    n /= np.linalg.norm(n)
    d = (patch['pos'] @ n).max() + .002
    p = patch['pos'].copy()
    p[:, 0] = (d - p[:, 1] * n[1] - p[:, 2] * n[2]) / n[0]
    patch = colour(patch, WHITE_UV)
    patch['pos'] = p
    patch['nrm'] = np.tile(n, (len(p), 1))
    return patch


def subset(g, selected):
    return clip._sub(g, selected)


def single_face(g, lift=True):
    """One flat normal per connected island: the area-weighted face normal. With lift, a normal pointing
    down is levelled (z = 0) so the patch is lit like the vertical bumper around it."""
    import comps
    p, t = g['pos'], g['tri']
    fn = np.cross(p[t[:, 1]] - p[t[:, 0]], p[t[:, 2]] - p[t[:, 0]])
    labels = comps.components(p, t)
    nrm = np.zeros_like(p, dtype=float)
    for label in np.unique(labels):
        k = labels == label
        n = fn[k].sum(0)
        if lift and n[2] < 0:
            n[2] = 0.
        n /= max(np.linalg.norm(n), 1e-12)
        nrm[np.unique(t[k])] = n
    return dict(g, nrm=nrm.astype(g['nrm'].dtype))


def colour(g, uv):
    g = dict(g)
    g['uv'] = np.tile(uv, (len(g['pos']), 1))
    g['col'] = np.full(len(g['pos']), 0xFFFFFFFF, np.uint32)
    return g


def rear_finish(g, lens=False):
    """Keep surface normals; map the trim highlight by height and the lens to plain white."""
    g = colour(g, WHITE_UV if lens else GRAY_UV)
    if not lens:
        # Avoid sampling adjacent cells while using the same height mapping for all pieces.
        height = np.clip((g['pos'][:, 2] - .685) / (.729 - .685), 0., 1.)
        g['uv'][:, 1] = (14 + (1 + 30 * (1 - height)) / 32) / 16
    return g


def hull_indices(q):
    """Monotone convex hull of projected lens points, in boundary order."""
    order = sorted(range(len(q)), key=lambda i: tuple(q[i]))
    def cross(a, b, c):
        u, v = q[b] - q[a], q[c] - q[a]
        return u[0] * v[1] - u[1] * v[0]
    def half(ids):
        out = []
        for i in ids:
            while len(out) >= 2 and cross(out[-2], out[-1], i) <= 1e-12:
                out.pop()
            out.append(i)
        return out
    return np.array(half(order)[:-1] + half(order[::-1])[:-1])


def backing(ring, radial=None, depth=0.003, grow=1.0, grow_down=1.0):
    p = ring['pos']
    centre = p.mean(0)
    _, _, axes = np.linalg.svd(p - centre, full_matrices=False)
    ids = hull_indices((p - centre) @ axes[:2].T)
    boundary = p[ids]
    # Place a white sheet behind the ring, following its curved boundary.
    outward = axes[2].copy()
    radial = np.array([-1., np.sign(centre[1]), 0.]) if radial is None else np.asarray(radial)
    if outward @ radial < 0:
        outward *= -1
    boundary = boundary.mean(0) + (boundary - boundary.mean(0)) * grow
    if grow_down != 1.0:       # stretch only the lower half (covers gaps under a lamp centre)
        below = boundary[:, 2] < boundary[:, 2].mean()
        boundary[below, 2] = boundary[:, 2].mean() + (boundary[below, 2] - boundary[:, 2].mean()) * grow_down
    pos = np.vstack([boundary.mean(0), boundary]) - outward * depth
    n = len(boundary)
    tri = np.array([(0, i + 1, (i + 1) % n + 1) for i in range(n)])
    face = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])
    if face.sum(0) @ outward < 0:
        tri = tri[:, ::-1]
    return dict(pos=pos, nrm=np.tile(outward, (n + 1, 1)),
                uv=np.tile([.75, .5], (n + 1, 1)),
                col=np.full(n + 1, 0xFFFFFFFF, np.uint32), tri=tri)


def tail_patches(g, seam=.585):
    """Return (name, red ring, white sheet), one per side and attachment."""
    c = g['pos'][g['tri']].mean(1)
    upper = subset(g, (c[:, 0] < -1.7) & (c[:, 2] > .5))
    patches = []
    for sign, side in ((1, 'left'), (-1, 'right')):
        half = clip.clip_plane(upper, [0, sign, 0], 0)
        for inner, attachment in ((True, 'trunk'), (False, 'body')):
            ring = clip.clip_plane(half, [0, sign, 0], seam, keep_positive=not inner)
            assert len(ring['tri']), (side, attachment)
            patches.append((side + '_' + attachment, colour(ring, [.25, .5]), backing(ring)))
    return patches


def atlas(size):
    rgba = np.full((size, size, 4), 255, np.uint8)
    rgba[:, :size // 2, :3] = [238, 8, 12]
    rgba[:, size // 2:, :3] = [226, 230, 234]
    return rgba


def volume_mask(points, lenses, front=False):
    """Remove base-car chrome lying inside a lamp outline, near its surface."""
    selected = np.zeros(len(points), bool)
    for lens in lenses:
        p = lens['pos']; centre = p.mean(0)
        _, _, axes = np.linalg.svd(p - centre, full_matrices=False)
        normal = axes[2].copy()
        radial = np.array([1. if front else -1., np.sign(centre[1]), 0.])
        if normal @ radial < 0:
            normal *= -1
        q = (p - centre) @ axes[:2].T
        hull = q[hull_indices(q)]
        projected = (points - centre) @ axes[:2].T
        inside = np.ones(len(points), bool)
        for a, b in zip(hull, np.roll(hull, -1, axis=0)):
            edge = b - a; v = projected - a
            inside &= edge[0] * v[:, 1] - edge[1] * v[:, 0] >= -.002 * np.linalg.norm(edge)
        depth = (points - centre) @ normal
        selected |= inside & (depth > -.18) & (depth < .04)
    return selected


def small_holes(g, max_len=24, weld=1e-4):
    """Closed boundary loops of at most max_len vertices (holes inside a lens). Returns a list of
    (fan mesh, faces touching the loop). The fan goes from the loop centre; orient it afterwards."""
    from collections import defaultdict
    p, t = g['pos'], g['tri']
    key = np.round(p / weld).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    tw = inv[t]
    edges = defaultdict(list)
    for f, a in enumerate(tw):
        for i in range(3):
            edges[tuple(sorted((a[i], a[(i + 1) % 3])))].append(f)
    border = {e: fs[0] for e, fs in edges.items() if len(fs) == 1}
    adj = defaultdict(list)
    for u, v in border:
        adj[u].append(v); adj[v].append(u)
    rep = {}
    for v in range(len(p)):
        rep.setdefault(inv[v], v)
    seen, out = set(), []
    for s in list(adj):
        if s in seen or len(adj[s]) != 2:
            continue
        loop, prev, cur = [s], None, s
        ok = True
        while True:
            seen.add(cur)
            nxt = [x for x in adj[cur] if x != prev]
            if len(adj[cur]) != 2 or not nxt:
                ok = False; break
            prev, cur = cur, nxt[0]
            if cur == s:
                break
            loop.append(cur)
            if len(loop) > max_len:
                ok = False; break
        if not ok or len(loop) < 3:
            continue
        ring = np.array([p[rep[v]] for v in loop])
        pos = np.vstack([ring.mean(0), ring])
        n = len(ring)
        tri = np.array([(0, i + 1, (i + 1) % n + 1) for i in range(n)])
        faces = sorted({border[tuple(sorted((loop[i], loop[(i + 1) % n])))] for i in range(n)})
        fan = dict(pos=pos, nrm=np.zeros_like(pos), uv=np.zeros((n + 1, 2)),
                   col=np.full(n + 1, 0xFFFFFFFF, np.uint32), tri=tri)
        out.append((fan, faces))
    return out


def thin_parts(g, sel, cell=.002, radius=3):
    """Faces of `sel` lying in thin protrusions of their y-z footprint (seen from behind the car): the parts
    removed by a morphological opening of that footprint with a disc of `radius` cells."""
    P = g['pos'][g['tri']][:, :, 1:]
    lo = P.reshape(-1, 2).min(0) - .02
    shape = tuple(((P.reshape(-1, 2).max(0) + .02 - lo) / cell).astype(int) + 1)
    cov = np.zeros(shape, bool)
    gy, gz = np.meshgrid(np.arange(shape[0]), np.arange(shape[1]), indexing='ij')
    pts = np.stack([gy, gz], -1) * cell + lo
    for f in np.nonzero(sel)[0]:
        a, b, c = P[f]
        mn = ((np.minimum(np.minimum(a, b), c) - lo) / cell).astype(int)
        mx = ((np.maximum(np.maximum(a, b), c) - lo) / cell).astype(int) + 1
        q = pts[mn[0]:mx[0] + 1, mn[1]:mx[1] + 1]
        d1 = np.cross(b - a, q - a); d2 = np.cross(c - b, q - b); d3 = np.cross(a - c, q - c)
        cov[mn[0]:mx[0] + 1, mn[1]:mx[1] + 1] |= ((d1 >= 0) & (d2 >= 0) & (d3 >= 0)) | ((d1 <= 0) & (d2 <= 0) & (d3 <= 0))

    def morph(m, op):
        out = m.copy()
        H, W = m.shape
        pad = np.pad(m, radius, constant_values=(op is np.logical_or) is False and False)
        for dy in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                if dy * dy + dz * dz <= radius * radius:
                    out = op(out, pad[radius + dy:radius + dy + H, radius + dz:radius + dz + W])
        return out
    opened = morph(morph(cov, np.logical_and), np.logical_or)
    thin = cov & ~opened
    ix = ((g['pos'][g['tri']].mean(1)[:, 1:] - lo) / cell).astype(int)
    return [f for f in np.nonzero(sel)[0] if thin[ix[f, 0], ix[f, 1]]]


def fill_gaps(g, white, cell=.002, behind=.0015, white_reach=.005):
    """Cracks of a lamp lens seen from behind the car (y-z): pixels inside the lens outline that no face
    covers. Each row run of such pixels becomes a quad just behind the nearest lens point, white or red
    after the nearest face. Returns (white mesh, red mesh)."""
    P = g['pos'][g['tri']]
    Q = P[:, :, 1:]
    lo = Q.reshape(-1, 2).min(0) - 2 * cell
    shape = tuple(((Q.reshape(-1, 2).max(0) + 2 * cell - lo) / cell).astype(int) + 1)
    cov = np.zeros(shape, bool)
    gy, gz = np.meshgrid(np.arange(shape[0]), np.arange(shape[1]), indexing='ij')
    pts = np.stack([gy, gz], -1) * cell + lo + cell / 2
    for f in range(len(Q)):
        a, b, c = Q[f]
        mn = np.maximum(((np.minimum(np.minimum(a, b), c) - lo) / cell).astype(int) - 1, 0)
        mx = ((np.maximum(np.maximum(a, b), c) - lo) / cell).astype(int) + 2
        q = pts[mn[0]:mx[0], mn[1]:mx[1]]
        d1 = np.cross(b - a, q - a); d2 = np.cross(c - b, q - b); d3 = np.cross(a - c, q - c)
        e = 1e-9
        cov[mn[0]:mx[0], mn[1]:mx[1]] |= ((d1 >= -e) & (d2 >= -e) & (d3 >= -e)) | ((d1 <= e) & (d2 <= e) & (d3 <= e))
    # exterior = uncovered pixels connected to the border
    ext = np.zeros(shape, bool)
    stack = [(i, j) for i in range(shape[0]) for j in (0, shape[1] - 1)] + [(i, j) for i in (0, shape[0] - 1) for j in range(shape[1])]
    while stack:
        i, j = stack.pop()
        if i < 0 or j < 0 or i >= shape[0] or j >= shape[1] or ext[i, j] or cov[i, j]:
            continue
        ext[i, j] = True
        stack += [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]
    hole = ~cov & ~ext
    fc = P.mean(1)
    wv = g['pos'][np.unique(g['tri'][np.asarray(white, bool)])] if np.any(white) else np.zeros((0, 3))
    out = {True: [], False: []}
    for j in range(shape[1]):
        i = 0
        while i < shape[0]:
            if not hole[i, j]:
                i += 1; continue
            k = i
            while k + 1 < shape[0] and hole[k + 1, j]:
                k += 1
            y0, y1 = lo[0] + i * cell - cell * .5, lo[0] + (k + 1) * cell + cell * .5
            z0, z1 = lo[1] + j * cell - cell * .5, lo[1] + (j + 1) * cell + cell * .5
            mid = np.array([(y0 + y1) / 2, (z0 + z1) / 2])
            f = np.argmin(((fc[:, 1:] - mid) ** 2).sum(1))
            x = fc[f, 0] + behind
            near_white = len(wv) and (((wv[:, 1:] - mid) ** 2).sum(1).min() < white_reach ** 2)
            out[bool(white[f] or near_white)].append(np.array([[x, y0, z0], [x, y1, z0], [x, y1, z1], [x, y0, z1]]))
            i = k + 1
    meshes = []
    for key in (True, False):
        quads = out[key]
        if not quads:
            meshes.append(None); continue
        pos = np.concatenate(quads)
        n = len(quads)
        tri = np.array([t for q in range(n) for t in ((4 * q, 4 * q + 1, 4 * q + 2), (4 * q, 4 * q + 2, 4 * q + 3))])
        meshes.append(dict(pos=pos, nrm=np.tile([-1., 0., 0.], (len(pos), 1)), uv=np.zeros((len(pos), 2)),
                           col=np.full(len(pos), 0xFFFFFFFF, np.uint32), tri=tri))
    return meshes[0], meshes[1]


def flatten_quadratic(g):
    """Per lamp (sign of y): move vertices along x onto the least-squares quadratic x = f(y, z) of that
    lamp's vertices and use the surface normals. Removes local dips while keeping the overall curvature."""
    g = dict(g, pos=g['pos'].copy(), nrm=g['nrm'].copy())
    p = g['pos']
    for sgn in (1, -1):
        k = p[:, 1] * sgn > 0
        if k.sum() < 6:
            continue
        y, z = p[k, 1], p[k, 2]
        A = np.c_[np.ones_like(y), y, z, y * y, z * z, y * z]
        x = p[k, 0]
        use = np.ones(len(x), bool)
        for _ in range(4):           # fit the outer envelope: dips (deeper, larger x) are left out
            c, *_ = np.linalg.lstsq(A[use], x[use], rcond=None)
            use = x <= A @ c + .001
        p[k, 0] = np.minimum(x, A @ c)  # only pull dips out to the surface, never push faces in
        dy = c[1] + 2 * c[3] * y + c[5] * z
        dz = c[2] + 2 * c[4] * z + c[5] * y
        n = np.c_[-np.ones_like(y), dy, dz]          # gradient of f - x points toward -x (rear) when flipped
        n /= np.linalg.norm(n, axis=1, keepdims=True)
        g['nrm'][k] = n
    return g
