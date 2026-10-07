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


def backing(ring, radial=None, depth=0.003, grow=1.0):
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
