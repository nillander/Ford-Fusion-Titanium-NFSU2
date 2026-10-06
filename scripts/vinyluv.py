"""Vinyl UVs in the layout of the slot's vinyl template (CARS/<SLOT>/VINYLS.BIN, texture <SLOT>_DEBUG):
left side at the top (upside down), top view in the middle, right side at the bottom, front view bottom-left,
rear view bottom-right. Longitudinal scale/offset from the template's wheel discs and the Fusion axles
(x -1.311 / +1.431); the convention (which way is front/up) was measured on the retail COROLLA.

FOCUS was measured for v8 (docs/diagnostico-v8/FOCUS_DEBUG-molde.png). MUSTANGGT uses the same convention;
its discs, centre line and front/rear columns were measured on MUSTANGGT_DEBUG of the installed game
(the P8 texture decoded with its palette): discs at u 125.5/411.5 px, v 47.8 (left) and 364 (right),
top centre line at v 206 px, FRONT column at u 235 px, REAR column at u 415 px."""
import numpy as np

REAR_X, FRONT_X = -1.311, 1.431
WZ = 0.098                                  # wheel centre height in model space
TEMPLATES = {
    'FOCUS': dict(u_rear=0.251, u_front=0.803, v_left=11 / 512, v_right=372 / 512, v_top=192 / 512,
                  u_frontview=0.395, u_rearview=0.77),
    'MUSTANGGT': dict(u_rear=125.5 / 512, u_front=411.5 / 512, v_left=47.8 / 512, v_right=364 / 512, v_top=206 / 512,
                      u_frontview=235 / 512, u_rearview=415 / 512),
}


def uv_region(pos, region, t):
    a_u = (t['u_front'] - t['u_rear']) / (FRONT_X - REAR_X)     # u per metre along x
    b_u = t['u_front'] - a_u * FRONT_X
    s_v = a_u * 1.163                                            # vertical scale (Corolla ratio v/u = 1.163)
    x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
    if region == 'left':
        return np.c_[a_u * x + b_u, t['v_left'] + s_v * (z - WZ)]
    if region == 'right':
        return np.c_[a_u * x + b_u, t['v_right'] - s_v * (z - WZ)]
    if region == 'top':
        return np.c_[a_u * x + b_u, t['v_top'] - s_v * y]
    if region == 'front':
        return np.c_[t['u_frontview'] + 0.19 * y, 0.96 - 0.24 * (z + 0.04)]
    return np.c_[t['u_rearview'] - 0.19 * y, 0.96 - 0.24 * (z + 0.04)]          # rear


def apply(m, slot='FOCUS'):
    """returns a copy of mesh m (pos,nrm,uv,col,tri) with vinyl UVs; vertices are split between regions"""
    t_ = TEMPLATES[slot]
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
        if s.any(): uv[s] = uv_region(p[src[s]], r, t_)
    return dict(pos=p[src], nrm=m['nrm'][src], uv=np.clip(uv, 0.0, 1.0), col=m['col'][src], tri=T)
