"""Vinyl UVs in the layout of the FOCUS vinyl template (CARS/FOCUS/VINYLS.BIN, texture FOCUS_DEBUG):
left side at the top (upside down), top view in the middle, right side at the bottom, front view bottom-left,
rear view bottom-right. Longitudinal scale/offset from the template's wheel discs (u 0.251 / 0.803) and the
Fusion axles (x -1.311 / +1.431); the convention (which way is front/up) was measured on the retail COROLLA."""
import numpy as np
A_U = (0.803 - 0.251) / (1.431 + 1.311)     # u per metre along x
B_U = 0.803 - A_U * 1.431
S_V = A_U * 1.163                           # vertical scale (Corolla ratio v/u = 1.163)
WZ = 0.098                                  # wheel centre height in model space


def uv_region(pos, region):
    x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
    if region == 'left':
        return np.c_[A_U * x + B_U, 11 / 512 + S_V * (z - WZ)]
    if region == 'right':
        return np.c_[A_U * x + B_U, 372 / 512 - S_V * (z - WZ)]
    if region == 'top':
        return np.c_[A_U * x + B_U, 192 / 512 - S_V * y]
    if region == 'front':
        return np.c_[0.395 + 0.19 * y, 0.96 - 0.24 * (z + 0.04)]
    return np.c_[0.77 - 0.19 * y, 0.96 - 0.24 * (z + 0.04)]          # rear


def apply(m):
    """returns a copy of mesh m (pos,nrm,uv,col,tri) with vinyl UVs; vertices are split between regions"""
    p = m['pos']; t = m['tri']
    fn = np.cross(p[t[:, 1]] - p[t[:, 0]], p[t[:, 2]] - p[t[:, 0]])
    fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
    c = p[t].mean(1)
    ax = np.abs(fn)
    reg = np.where((ax[:, 2] >= ax[:, 1]) & (ax[:, 2] >= ax[:, 0]) & (fn[:, 2] > 0), 'top',
          np.where((ax[:, 0] > ax[:, 1]) & (ax[:, 0] > ax[:, 2]), np.where(fn[:, 0] > 0, 'front', 'rear'),
                   np.where(c[:, 1] > 0, 'left', 'right')))
    keys = {}; newv = []; T = np.empty_like(t)
    for f in range(len(t)):
        for k in range(3):
            key = (int(t[f, k]), reg[f])
            if key not in keys:
                keys[key] = len(newv); newv.append(key)
            T[f, k] = keys[key]
    src = np.array([v for v, _ in newv]); rg = np.array([r for _, r in newv])
    uv = np.zeros((len(src), 2))
    for r in ('left', 'right', 'top', 'front', 'rear'):
        s = rg == r
        if s.any(): uv[s] = uv_region(p[src[s]], r)
    return dict(pos=p[src], nrm=m['nrm'][src], uv=np.clip(uv, 0.0, 1.0), col=m['col'][src], tri=T)
