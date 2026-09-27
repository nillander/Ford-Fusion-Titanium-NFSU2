import numpy as np
def components(pos, tri, tol=1e-4):
    # weld by position then union-find over triangles
    k = np.round(pos/tol).astype(np.int64)
    _, inv = np.unique(k, axis=0, return_inverse=True); inv = inv.reshape(-1)
    t = inv[tri]
    par = np.arange(inv.max()+1)
    def f(x):
        r = x
        while par[r] != r: r = par[r]
        while par[x] != r: par[x], x = r, par[x]
        return r
    for a, b, c in t:
        ra, rb, rc = f(a), f(b), f(c)
        par[rb] = ra; par[f(rc)] = ra
    root = np.array([f(x) for x in range(len(par))])
    lab = root[t[:, 0]]
    _, lab = np.unique(lab, return_inverse=True)
    return lab
