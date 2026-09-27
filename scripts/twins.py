import numpy as np
def twins(pos, tri, tol=2e-3):
    """Faces that have a coincident face with opposite orientation (double-sided shells).
    Returns (is_twin mask, outward_keep mask) ; tol in metres (grid rounding)."""
    p = pos[tri]; c = p.mean(1)
    fn = np.cross(p[:, 1]-p[:, 0], p[:, 2]-p[:, 0]); fn /= np.linalg.norm(fn, axis=1, keepdims=True)+1e-12
    # key: rounded centroid (faces may be re-triangulated between sides, so use a spatial hash on centroid + |normal| axis)
    q = np.round(c/tol).astype(np.int64)
    from collections import defaultdict
    H = defaultdict(list)
    for i, k in enumerate(map(tuple, q)): H[k].append(i)
    tw = np.zeros(len(tri), bool)
    offs = [(a, b, d) for a in (-1, 0, 1) for b in (-1, 0, 1) for d in (-1, 0, 1)]
    for i in range(len(tri)):
        k = q[i]
        for o in offs:
            for j in H.get((k[0]+o[0], k[1]+o[1], k[2]+o[2]), ()):
                if j != i and fn[i] @ fn[j] < -0.9:
                    tw[i] = True; break
            if tw[i]: break
    return tw, fn, c
