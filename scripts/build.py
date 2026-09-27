"""v6. Builds the Ford Fusion Titanium 2018 for NFSU2 (FOCUS slot) from the approved MW2005 port (V1prime-z10).

Layout follows the Escort RS mod that already works in this game (nfsu360 compiler layout):
  FOCUS_KIT00_BODY_A, FOCUS_KITW01..04_BODY_A, FOCUS_BASE_A, FOCUS_KIT00_FRONT_WHEEL_A
Every solid stays under 65,535 indices (UG2 limit).  Opaque textures are DXT1; only lamp lenses
use a DXT3 texture (MW lesson: DXT3 = no depth write).
"""
import pickle, json, struct, sys, os
import numpy as np
from PIL import Image
import decimate, ug2write, tpkwrite, tpk2, dxt, dxtenc
from hashes import bh

OUT = sys.argv[1] if len(sys.argv) > 1 else 'out'
os.makedirs(OUT, exist_ok=True)
P = pickle.load(open('mw_parts.pkl', 'rb'))
LOG = {}

# ---------------------------------------------------------------- materials
M = {k: bh(k) for k in ['CARSKIN', 'WINDSHIELD', 'DULLPLASTIC', 'INTERIOR', 'LICENSEPLATE', 'HEADLIGHTGLASS',
                        'HEADLIGHTREFLECTOR', 'BRAKELIGHT', 'BRAKELIGHTGLASS', 'DRIVER', 'RUBBER', 'USER_RIMS']}
T_PAINT = 0x3C84D757   # global paint texture used by every UG2 body (retail and mods)
T_WINDOW = bh('WINDOW')
TEX = {  # new car textures (name -> source, size, format)
    'FOCUS_MISC': ('MUSTANGGT_MISC', 512, 'DXT1'),
    'FOCUS_LOGO': ('MUSTANGGT_LOGO', 512, 'DXT1'),
    'FOCUS_INTERIOR': ('MUSTANGGT_INTERIOR', 512, 'DXT1'),
    'FOCUS_BADGING': ('MUSTANGGT_BADGING', 512, 'DXT1'),
    'FOCUS_KIT00_HEADLIGHT': ('MUSTANGGT_KIT00_HEADLIG', 256, 'DXT1'),
    'FOCUS_HEADLIGHT_GLASS': ('MUSTANGGT_KIT00_HEADLIG', 256, 'DXT3'),
    'FOCUS_KIT00_BRAKELIGHT': ('MUSTANGGT_KIT00_BRAKELI', 256, 'DXT1'),
    'FOCUS_BRAKELIGHT_GLASS': ('MUSTANGGT_KIT00_BRAKELI', 256, 'DXT3'),
    'FOCUS_RIM': ('MUSTANGGT_RIM', 256, 'DXT1'),
    'FOCUS_TIRE': ('MUSTANGGT_TIRE', 256, 'DXT1'),
    'FOCUS_DRIVER': ('MUSTANGGT_DRIVER', 256, 'DXT1'),
}
KEEP_ESCORT = [0x6F62BC7B, bh('FOCUS_SHADOWFE'), bh('FOCUS_SHADOWIG'), bh('FOCUS_NEON')]


def weld(g):
    k = np.c_[np.round(g['pos'] / 1e-5), np.round(g['nrm'] * 1e3), np.round(g['uv'] * 1e5)].astype(np.int64)
    _, first, inv = np.unique(k, axis=0, return_index=True, return_inverse=True)
    return dict(pos=g['pos'][first], nrm=g['nrm'][first], uv=g['uv'][first], col=g['col'][first],
                tri=inv.reshape(-1)[g['tri']])


def merge(gs):
    out = dict(pos=[], nrm=[], uv=[], col=[], tri=[]); o = 0
    for g in gs:
        for k in ('pos', 'nrm', 'uv', 'col'):
            out[k].append(g[k])
        out['tri'].append(g['tri'] + o); o += len(g['pos'])
    return {k: np.concatenate(v) for k, v in out.items()}


def mesh(g, tex, mat):
    return dict(pos=g['pos'], nrm=g['nrm'], uv=g['uv'], col=g['col'], tri=g['tri'], tex=tex, mat=mat)


def dec(g, target, name):
    before = len(g['tri'])
    if before <= target:
        return g
    used, F = decimate.decimate(g['pos'], g['tri'], target)
    pos = g['pos'][used]
    nrm = decimate.recompute_normals(pos, g['nrm'][used], F)
    LOG.setdefault('decimation', {})[name] = [int(before), int(len(F))]
    return dict(pos=pos, nrm=nrm, uv=g['uv'][used], col=g['col'][used], tri=F)


def groups_of(part):
    return [weld(g) | {'tex': g['tex'], 'mat': g['mat']} for g in P['MUSTANGGT_' + part]['groups']]


def tex_for(mwtex, mwmat):
    if mwtex == 'MUSTANGGT_KIT00_HEADLIG':
        return (bh('FOCUS_HEADLIGHT_GLASS'), M['HEADLIGHTGLASS']) if mwmat == 'HEADLIGHTGLASS' else (bh('FOCUS_KIT00_HEADLIGHT'), M['HEADLIGHTREFLECTOR'])
    if mwtex == 'MUSTANGGT_KIT00_BRAKELI':
        return (bh('FOCUS_BRAKELIGHT_GLASS'), M['BRAKELIGHTGLASS']) if mwmat == 'HEADLIGHTGLASS' else (bh('FOCUS_KIT00_BRAKELIGHT'), M['BRAKELIGHT'])
    name = 'FOCUS_' + mwtex[len('MUSTANGGT_'):]
    mat = M.get(mwmat, M['DULLPLASTIC'])
    return bh(name), mat


# ---------------------------------------------------------------- v4 helpers
import twins, comps
CAP = 21500   # tris per solid (64.5k indices, under the 16-bit 65,535; Senna mod loads with 20,486)


def compact(g, keep):
    t = g['tri'][keep]
    used = np.unique(t)
    remap = np.full(len(g['pos']), -1, np.int64); remap[used] = np.arange(len(used))
    return dict(pos=g['pos'][used], nrm=g['nrm'][used], uv=g['uv'][used], col=g['col'][used], tri=remap[t])


def outwardness(g, clamp=(-1.0, 1.0), zc=0.7):
    p = g['pos']; t = g['tri']; c = p[t].mean(1)
    fn = np.cross(p[t[:, 1]] - p[t[:, 0]], p[t[:, 2]] - p[t[:, 0]])
    ax = np.zeros_like(c); ax[:, 0] = np.clip(c[:, 0], *clamp); ax[:, 2] = zc
    return ((c - ax) * fn).sum(1)


def drop_inward_twins(g, name):
    tw, fn, c = twins.twins(g['pos'], g['tri'])
    o = outwardness(g)
    keep = ~(tw & (o < 0))
    LOG.setdefault('inward_twins_removed', {})[name] = int((~keep).sum())
    return compact(g, keep)


def outward_only(g, name, clamp=(-0.9, 0.5), zc=0.75):
    keep = outwardness(g, clamp, zc) > 0
    LOG.setdefault('inner_faces_removed', {})[name] = int((~keep).sum())
    return compact(g, keep)


def double_sided(g):
    n = len(g['pos'])
    return dict(pos=np.r_[g['pos'], g['pos']], nrm=np.r_[g['nrm'], -g['nrm']], uv=np.r_[g['uv'], g['uv']],
                col=np.r_[g['col'], g['col']], tri=np.r_[g['tri'], g['tri'][:, ::-1] + n])


def ntris(ms):
    return sum(len(m['tri']) for m in ms)


# ---------------------------------------------------------------- paint: LOD B (smooth), single-sided
paint = drop_inward_twins(weld(P['MUSTANGGT_KIT00_BODY_B']['groups'][0]), 'paint_B')
lab = comps.components(paint['pos'], paint['tri'])
is_trunk = np.zeros(len(paint['tri']), bool)
for i in range(lab.max() + 1):
    s = lab == i
    p = paint['pos'][np.unique(paint['tri'][s])]
    mn, mx = p.min(0), p.max(0)
    if mx[0] < -1.7 and max(abs(mn[1]), abs(mx[1])) < 0.63 and mn[2] > 0.33:
        is_trunk |= s
body_paint = compact(paint, ~is_trunk)


def trunk_region(g):
    lab = comps.components(g['pos'], g['tri'])
    sel = np.zeros(len(g['tri']), bool)
    for i in range(lab.max() + 1):
        s_ = lab == i
        p_ = g['pos'][np.unique(g['tri'][s_])]
        mn, mx = p_.min(0), p_.max(0)
        if mx[0] < -1.7 and max(abs(mn[1]), abs(mx[1])) < 0.63 and mn[2] > 0.33:
            sel |= s_
    return sel


# v6: the trunk lid comes from LOD A (the TRUNK_A solid has room for it; LOD B showed waves in the game)
wA = weld(P['MUSTANGGT_KIT00_BODY_A']['groups'][0])
_tA = trunk_region(wA)
trunk_paint = drop_inward_twins(compact(wA, _tA), 'trunk_A')
# v8: ALL paint from LOD A, no decimation, split over the retail part slots that are drawn with every kit
# (doors and roof are separate parts in the retail cars; the KITW bodies do not cover the doors).
# Cuts are exact (same mesh on both sides), so the pieces meet without steps.
import clip, vinyluv
restA = drop_inward_twins(compact(wA, ~_tA), 'paint_A')
import smooth
FAIR = {  # v8: local fairing of dents/waves seen in the game (vertices move only along their normal)
}
for nm_, f_ in FAIR.items():
    restA, n_ = smooth.fair_region(restA, f_)
    LOG.setdefault('faired_vertices', {})[nm_] = n_

# nose: fill the recess of the removed Ford oval. Fit x = f(y, z) (quadratic) on the nose around it and push
# the vertices of the recess out to that surface (only outwards, only inside the oval area + margin)
def fill_recess(m, y0=0.24, z0=0.52, z1=0.70, xmin=2.12):
    p = m['pos']
    ring = (p[:, 0] > xmin) & (np.abs(p[:, 1]) > y0) & (np.abs(p[:, 1]) < y0 + 0.2) & (p[:, 2] > z0) & (p[:, 2] < z1)
    ins = (p[:, 0] > xmin) & (np.abs(p[:, 1]) <= y0) & (p[:, 2] > z0 + 0.01) & (p[:, 2] < z1 - 0.01)
    if ring.sum() < 20 or not ins.any(): return m, 0
    Y, Z = p[ring, 1], p[ring, 2]
    A = np.c_[np.ones_like(Y), Y ** 2, Z, Z ** 2, Z * Y ** 2]
    c, *_ = np.linalg.lstsq(A, p[ring, 0], rcond=None)
    Yi, Zi = p[ins, 1], p[ins, 2]
    xf = np.c_[np.ones_like(Yi), Yi ** 2, Zi, Zi ** 2, Zi * Yi ** 2] @ c
    newp = p.copy(); sel = np.nonzero(ins)[0]
    push = xf > p[ins, 0]
    newp[sel[push], 0] = xf[push]
    near = np.abs(newp[sel, 0] - xf) < 0.012            # on the surface now (pushed or already there)
    push = push | near
    n = m['nrm'].copy()
    dx = np.c_[np.zeros_like(Yi), 2 * c[1] * Yi + 2 * c[4] * Zi * Yi, c[2] + 2 * c[3] * Zi + c[4] * Yi ** 2]
    nn = np.c_[np.ones_like(Yi), -dx[:, 1], -dx[:, 2]]; nn /= np.linalg.norm(nn, axis=1, keepdims=True)
    n[sel[push]] = nn[push]
    out = dict(m); out['pos'] = newp; out['nrm'] = n
    return out, int(push.sum())


restA, n_ = fill_recess(restA)
LOG['nose_recess_filled_vertices'] = n_
# v9: the FOCUS slot only draws BODY / BASE / TRUNK / WHEEL (+ decals): ROOF_A and DOOR_*_A are ignored
# (v8 showed no roof, doors or hood). Paint = LOD B + LOD A where the game showed deformations
# (rear bumper, nose, front edge of the roof); exact cuts so the LODs meet without steps.
REAR_X, NOSE_X, NOSE_Y = -1.9, 2.0, 0.45
BOXES = {'rear': dict(xmax=REAR_X), 'nose': dict(xmin=NOSE_X, ymin=-NOSE_Y, ymax=NOSE_Y, zmin=0.52, zmax=0.75),
         'roof_front': dict(xmin=0.15, xmax=0.6, ymin=-0.5, ymax=0.5, zmin=1.05)}
bB = body_paint; A_parts = {}
for nm, box in BOXES.items():
    _, bB = clip.split_box(bB, box)
    ins, _ = clip.split_box(restA, box)
    A_parts[nm] = ins
rearA = A_parts['rear']
noseA = merge([A_parts['nose'], A_parts['roof_front']])      # these go into BASE
BODY_B_TARGET = 14900
bB = dec(bB, BODY_B_TARGET, 'paint_B_flat')
body_paint = merge([bB, rearA])
hood = outward_only(weld(P['MUSTANGGT_KIT00_HOOD_B']['groups'][0]), 'hood_B', clamp=(1.2, 1.9), zc=0.35)
A_parts['body_B'] = bB
LOG['paint_lods'] = {k + '_A': int(len(v['tri'])) for k, v in A_parts.items()}

# ---------------------------------------------------------------- lamps (LOD C). Lenses double-sided;
# brake lens uses the BRAKELIGHT material (BRAKELIGHTGLASS is only the glow shown when braking)
head_parts, brake_parts = [], []
for part in ['KIT00_RIGHT_HEADLIGHT_C', 'KIT00_RIGHT_HEADLIGHT_GLASS_C']:
    for g in groups_of(part):
        t, m = tex_for(g['tex'], g['mat'])
        if m == M['HEADLIGHTGLASS']:
            g = double_sided(g)
        head_parts.append(mesh(g, t, m))
for part in ['KIT00_RIGHT_BRAKELIGHT_B', 'KIT00_RIGHT_BRAKELIGHT_GLASS_B']:
    for g in groups_of(part):
        if g['mat'] == 'HEADLIGHTGLASS':
            brake_parts.append(mesh(double_sided(g), bh('FOCUS_BRAKELIGHT_GLASS'), bh('MOLDINGS')))   # v7: retail lens material
        else:
            brake_parts.append(mesh(g, bh('FOCUS_KIT00_BRAKELIGHT'), M['DULLPLASTIC']))
# draw order inside a solid: opaque first, lenses (DXT3) last
head_opaque = [m for m in head_parts if m['mat'] != M['HEADLIGHTGLASS']]
head_glass = [m for m in head_parts if m['mat'] == M['HEADLIGHTGLASS']]
brake_opaque = [m for m in brake_parts if m['tex'] != bh('FOCUS_BRAKELIGHT_GLASS')]
brake_glass = [m for m in brake_parts if m['tex'] == bh('FOCUS_BRAKELIGHT_GLASS')]

def split_y(ms, lim=0.6):
    inner, outer = [], []
    for m in ms:
        c = m['pos'][m['tri']].mean(1)
        k = np.abs(c[:, 1]) < lim
        for sel, dst in ((k, inner), (~k, outer)):
            if sel.any():
                g = compact(m, sel); dst.append(mesh(g, m['tex'], m['mat']))
    return inner, outer


brake_opaque_in, brake_opaque = split_y(brake_opaque)
brake_glass_in, brake_glass = split_y(brake_glass)
VP = lambda m: mesh(vinyluv.apply(m), T_PAINT, M['CARSKIN'])       # paint with vinyl UVs
body_list = [VP(body_paint)] + head_opaque + head_glass

trunk_list = [VP(trunk_paint)] + brake_opaque_in + brake_glass_in

# ---------------------------------------------------------------- BASE
_G = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'vidros_v5.npz')) \
    if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'vidros_v5.npz')) else np.load('vidros_v5.npz')
_panes = [{k: _G[f'{i}_{k}'] for k in ('pos', 'nrm', 'uv', 'col', 'tri')} for i in range(int(_G['n']))]
_big = [p_ for p_ in _panes if abs(p_['pos'][:, 1].mean()) < 0.3]          # windscreen and rear screen
GP = np.concatenate([p_['pos'] for p_ in _big]); GN = np.concatenate([p_['nrm'] for p_ in _big])


def near_glass(c, tol=0.015, lat=0.08):
    out = np.zeros(len(c), bool)
    for i in range(0, len(c), 256):
        q = c[i:i + 256]
        d2 = ((q[:, None] - GP[None]) ** 2).sum(-1); j = d2.argmin(1)
        v = q - GP[j]; dn = np.abs((v * GN[j]).sum(1))
        out[i:i + 256] = (dn < tol) & (np.sqrt(d2[np.arange(len(q)), j]) < lat)
    return out


base = []
_rear_low = lambda c: (c[:, 0] < -1.85) & (c[:, 2] < 0.5)
_baseC = []
for g in groups_of('BASE_C'):
    c = g['pos'][g['tri']].mean(1)
    k = ~_rear_low(c)
    if g['tex'] == 'MUSTANGGT_MISC':      # v7: Ford oval on the nose removed (the nose paint is now smooth LOD A)
        emb = (c[:, 0] > 2.24) & (np.abs(c[:, 1]) < 0.075) & (c[:, 2] > 0.58) & (c[:, 2] < 0.64)
        LOG['emblem_removed'] = int(emb.sum()); k &= ~emb
    if k.any(): _baseC.append(compact(g, k) | {'tex': g['tex'], 'mat': g['mat']})
for g in groups_of('BASE_B'):             # v7: exhaust tips and diffuser from LOD B (C was too coarse)
    c = g['pos'][g['tri']].mean(1); k = _rear_low(c)
    if k.any() and g['tex'] in ('MUSTANGGT_MISC', 'MUSTANGGT_LOGO'):
        _baseC.append(compact(g, k) | {'tex': g['tex'], 'mat': g['mat']}); LOG.setdefault('rear_low_from_B', {})[g['tex']] = int(k.sum())
for g in _baseC:
    if g['tex'] in ('MUSTANGGT_LOGO', 'MUSTANGGT_MISC'):
        fr = near_glass(g['pos'][g['tri']].mean(1))
        if fr.any():
            LOG.setdefault('frit_removed', {})[g['tex']] = int(fr.sum())
            g = compact(g, ~fr) | {'tex': g['tex'], 'mat': g['mat']}
    if len(g['tri']) > 2000:
        g = dec(g, int(len(g['tri']) * 0.9), 'base_' + g['tex'][10:]) | {'tex': g['tex'], 'mat': g['mat']}
    if g['tex'] in ('MUSTANGGT_LOGO', 'MUSTANGGT_MISC'):
        # v6: MW draws both faces; the black valances of the bumpers were modelled facing inwards and vanish
        # in UG2 (back-face culling) -> lower front/rear areas made double-sided
        c = g['pos'][g['tri']].mean(1)
        low = (np.abs(c[:, 0]) > 1.85) & (c[:, 2] < 0.5)
        if low.any():
            ds = double_sided(compact(g, low))
            LOG.setdefault('double_sided_valance', {})[g['tex']] = int(low.sum())
            gg = merge([compact(g, ~low), ds])
            g = gg | {'tex': g['tex'], 'mat': g['mat']}
    t, m = tex_for(g['tex'], g['mat'])
    base.append(mesh(g, t, m))
for g in groups_of('KIT00_DRIVER_A'):
    base.append(mesh(dec(g, 700, 'driver'), bh('FOCUS_DRIVER'), M['DRIVER']))
base += brake_opaque
base.append(VP(hood))
base.append(VP(noseA))
# glass (v5): new sheets generated by scripts/newglass.py (needs scipy + contourpy): one clean single-sided
# surface per window fitted to the MW glass shape, outline widened 30 mm and bent inwards under the frame
_G = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'vidros_v5.npz')) \
    if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'vidros_v5.npz')) else np.load('vidros_v5.npz')
glass = merge([{k: _G[f'{i}_{k}'] for k in ('pos', 'nrm', 'uv', 'col', 'tri')} for i in range(int(_G['n']))])
LOG['glass'] = dict(source='docs/vidros_v5.npz', windows=int(_G['n']), tris=int(len(glass['tri'])), under_frame_m=0.03)
inter = groups_of('KIT00_INTERIOR_A')
fixed = ntris(base) + len(glass['tri']) + ntris(brake_glass)
INTERIOR_BUDGET = 21300 - fixed
big = [g for g in inter if len(g['tri']) > 1000]
small = [g for g in inter if len(g['tri']) <= 1000]
avail = INTERIOR_BUDGET - sum(len(g['tri']) for g in small)
tot = sum(len(g['tri']) for g in big)
def dec_cluster(g, target, name):
    """vertex clustering on a grid (any target reachable); UV/colour of the first vertex of each cell"""
    lo = g['pos'].min(0); best = None
    for cell in np.geomspace(0.005, 0.2, 40):
        k = np.floor((g['pos'] - lo) / cell).astype(np.int64)
        _, first, inv = np.unique(k, axis=0, return_index=True, return_inverse=True); inv = inv.ravel()
        t = inv[g['tri']]
        t = t[(t[:, 0] != t[:, 1]) & (t[:, 1] != t[:, 2]) & (t[:, 0] != t[:, 2])]
        t = np.unique(np.sort(t, 1), axis=0, return_index=True)[1]
        tt = inv[g['tri']]; tt = tt[(tt[:, 0] != tt[:, 1]) & (tt[:, 1] != tt[:, 2]) & (tt[:, 0] != tt[:, 2])]
        _, ui = np.unique(np.sort(tt, 1), axis=0, return_index=True); tt = tt[np.sort(ui)]
        best = (cell, first, inv, tt)
        if len(tt) <= target: break
    cell, first, inv, F = best
    cnt = np.bincount(inv); pos = np.zeros((len(first), 3)); np.add.at(pos, inv, g['pos']); pos /= cnt[:, None]
    used = np.unique(F); remap = np.full(len(pos), -1); remap[used] = np.arange(len(used)); F = remap[F]
    pos = pos[used]; fi = first[used]
    fn = np.cross(pos[F[:, 1]] - pos[F[:, 0]], pos[F[:, 2]] - pos[F[:, 0]]); acc = np.zeros_like(pos)
    for kk in range(3): np.add.at(acc, F[:, kk], fn)
    nrm = acc / (np.linalg.norm(acc, axis=1, keepdims=True) + 1e-12)
    LOG.setdefault('decimation', {})[name] = [int(len(g['tri'])), int(len(F)), 'cluster %.3f m' % cell]
    return dict(pos=pos, nrm=nrm, uv=g['uv'][fi], col=g['col'][fi], tri=F)


def dec_free(g, target, name):
    k = np.round(g['pos'] / 1e-4).astype(np.int64)
    _, first, inv = np.unique(k, axis=0, return_index=True, return_inverse=True); inv = inv.ravel()
    gp = g['pos'][first]; gt = inv[g['tri']]
    gt = gt[(gt[:, 0] != gt[:, 1]) & (gt[:, 1] != gt[:, 2]) & (gt[:, 0] != gt[:, 2])]
    used, F = decimate.decimate(gp, gt, target)
    pos = gp[used]
    # UV and colour from the nearest original vertex
    j = np.empty(len(pos), np.int64)
    for i in range(0, len(pos), 512):
        j[i:i + 512] = ((pos[i:i + 512, None] - g['pos'][None]) ** 2).sum(-1).argmin(1)
    fn = np.cross(pos[F[:, 1]] - pos[F[:, 0]], pos[F[:, 2]] - pos[F[:, 0]]); acc = np.zeros_like(pos)
    for kk in range(3): np.add.at(acc, F[:, kk], fn)
    nrm = acc / (np.linalg.norm(acc, axis=1, keepdims=True) + 1e-12)
    LOG.setdefault('decimation', {})[name] = [int(len(g['tri'])), int(len(F))]
    return dict(pos=pos, nrm=nrm, uv=g['uv'][j], col=g['col'][j], tri=F)


for g in big:
    tgt = int(avail * len(g['tri']) / tot)
    d = dec_free(g, tgt, 'interior_' + g['mat'])
    if len(d['tri']) > tgt:                                 # QEM stops on open borders: finish with a fine grid
        d = dec_cluster(d, tgt, 'interior_grid_' + g['mat'])
    t, m = tex_for(g['tex'], g['mat'])
    base.append(mesh(d, t, m))
for g in small:
    t, m = tex_for(g['tex'], g['mat'])
    base.append(mesh(g, t, m))
base_glass = [b for b in base if b['mat'] == M['HEADLIGHTGLASS']]
base = [b for b in base if b['mat'] != M['HEADLIGHTGLASS']] + [mesh(glass, T_WINDOW, M['WINDSHIELD'])] + base_glass + brake_glass
LOG['base_parts'] = [(hex(m['tex']), hex(m['mat']), len(m['tri'])) for m in base]
print(LOG['base_parts'])
LOG['budget'] = dict(body=ntris(body_list), trunk=ntris(trunk_list), base=ntris(base))
print(LOG['budget'])

# wheel: LOD B of the 20-spoke 18" wheel
wheel = []
for g in groups_of('KIT00_FRONT_TIRE_B'):
    if g['tex'] == 'MUSTANGGT_RIM':
        wheel.append(mesh(g, bh('FOCUS_RIM'), M['USER_RIMS']))
    else:
        wheel.append(mesh(g, bh('FOCUS_TIRE'), M['RUBBER']))

# ---------------------------------------------------------------- markers (MW positions, UG2 left = +y)
mw_markers = P['MUSTANGGT_BASE_A']['markers']
names = {bh(n): n for n in ['LEFT_REVERSE', 'RIGHT_REVERSE', 'LEFT_BRAKELIGHT', 'RIGHT_BRAKELIGHT', 'LEFT_EXHAUST',
                              'RIGHT_EXHAUST', 'CENTRE_BRAKELIGHT', 'LEFT_HEADLIGHT', 'RIGHT_HEADLIGHT', 'SPOILER', 'ROOF_SCOOP']}
swap = {'LEFT': 'RIGHT', 'RIGHT': 'LEFT'}
base_markers, exhaust_markers = [], []
for i in range(0, len(mw_markers), 80):
    h = int.from_bytes(mw_markers[i:i + 4], 'little')
    m = np.frombuffer(mw_markers[i + 16:i + 80], '<f4').reshape(4, 4).copy()
    n = names[h]
    side = n.split('_')[0]
    if side in swap:
        n = swap[side] + n[len(side):]
    if n.endswith('REVERSE'):
        continue
    entry = (bh(n), m)
    (exhaust_markers if 'EXHAUST' in n else base_markers).append(entry)
    LOG.setdefault('markers', {})[n] = [round(float(x), 3) for x in m[3, :3]]


# ---------------------------------------------------------------- assemble solids
def solid(name, meshes, markers=()):
    texs, lights = [], []
    pos, nrm, uv, col, groups = [], [], [], [], []
    o = 0
    for m in meshes:
        if len(m['tri']) == 0:
            continue
        if m['tex'] not in texs: texs.append(m['tex'])
        if m['mat'] not in lights: lights.append(m['mat'])
        pos.append(m['pos']); nrm.append(m['nrm']); uv.append(m['uv']); col.append(m['col'])
        groups.append(dict(tex_i=texs.index(m['tex']), sh_i=lights.index(m['mat']), tri=np.asarray(m['tri']) + o))
        o += len(m['pos'])
    for g in groups:  # drop degenerate triangles
        t = g['tri']
        g['tri'] = t[(t[:, 0] != t[:, 1]) & (t[:, 1] != t[:, 2]) & (t[:, 0] != t[:, 2])]
    nrm_all = np.concatenate(nrm)
    ln = np.linalg.norm(nrm_all, axis=1)
    bad = ln < 0.5
    if bad.any():  # zero normals from the source: use the average face normal
        pos_all = np.concatenate(pos); acc = np.zeros_like(pos_all)
        for g in groups:
            t = g['tri']; fnm = np.cross(pos_all[t[:, 1]] - pos_all[t[:, 0]], pos_all[t[:, 2]] - pos_all[t[:, 0]])
            for k in range(3): np.add.at(acc, t[:, k], fnm)
        acc[np.linalg.norm(acc, axis=1) < 1e-12] = [0, 0, 1]
        nrm_all[bad] = acc[bad]
        LOG.setdefault('fixed_normals', {})[name] = int(bad.sum())
    nrm_all = nrm_all / np.linalg.norm(nrm_all, axis=1, keepdims=True)
    # v6: a normal that disagrees with the faces using that vertex (> ~70 deg) makes a dark blotch in UG2;
    # replace it with the area-weighted average of those faces (hard edges stay: vertices are already split)
    pos_all = np.concatenate(pos); acc = np.zeros_like(pos_all)
    for g in groups:
        t = g['tri']; fnm = np.cross(pos_all[t[:, 1]] - pos_all[t[:, 0]], pos_all[t[:, 2]] - pos_all[t[:, 0]])
        for k in range(3): np.add.at(acc, t[:, k], fnm)
    ln2 = np.linalg.norm(acc, axis=1)
    ok = ln2 > 1e-12
    avg = np.zeros_like(acc); avg[ok] = acc[ok] / ln2[ok, None]
    flip = ok & ((nrm_all * avg).sum(1) < 0.35)
    if flip.any():
        nrm_all[flip] = avg[flip]
        LOG.setdefault('normals_fixed', {})[name] = int(flip.sum())
    nrm = [nrm_all]
    s = dict(name=name, tex=texs, light=lights, pos=np.concatenate(pos).astype(np.float32),
             nrm=np.concatenate(nrm).astype(np.float32), uv=np.concatenate(uv).astype(np.float32),
             col=np.concatenate(col).astype(np.uint32), groups=groups, markers=list(markers))
    ntri = sum(len(g['tri']) for g in groups)
    LOG.setdefault('solids', {})[name] = dict(tris=int(ntri), indices=int(ntri * 3), verts=int(o), groups=len(groups))
    return s


solids = []
for slot in ['KIT00', 'KITW01', 'KITW02', 'KITW03', 'KITW04']:   # the MW kits share the same paint mesh at LOD B
    solids.append(solid(f'FOCUS_{slot}_BODY_A', body_list, exhaust_markers))
solids.append(solid('FOCUS_KIT00_TRUNK_A', trunk_list))

solids.append(solid('FOCUS_BASE_A', base, base_markers))
solids.append(solid('FOCUS_KIT00_FRONT_WHEEL_A', wheel))

# ---------------------------------------------------------------- v6: decal placement solids
import decals
paint_all = merge([body_paint, trunk_paint, hood, noseA])
PT = (paint_all['pos'], paint_all['tri'])
glass_all = merge(_panes)
GT = (glass_all['pos'], glass_all['tri'])
_hood_npz = next(p_ for p_ in (os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'decal_capo_corolla.npz'), 'decal_capo_corolla.npz') if os.path.exists(p_))


def side_of(part):
    ys = np.concatenate([g['pos'][:, 1] for g in P[part]['groups']])
    return 'LEFT' if ys.mean() > 0 else 'RIGHT'          # UG2: +y is the left side


dec_parts = {}
dec_parts['DECAL_FRONT_WINDOW_WIDE_MEDIUM_A'] = decals.mesh_from_groups(decals.from_mw(P, 'MUSTANGGT_DECAL_FRONT_WINDOW_WIDE_MEDIUM_A'), GT, off=0.004, levels=2)
dec_parts['DECAL_REAR_WINDOW_WIDE_MEDIUM_A'] = decals.mesh_from_groups(decals.from_mw(P, 'MUSTANGGT_DECAL_REAR_WINDOW_WIDE_MEDIUM_A'), GT, off=0.004, levels=2)
for mwside in ('LEFT', 'RIGHT'):
    for what in ('DOOR', 'QUARTER'):
        part = f'MUSTANGGT_KIT00_DECAL_{mwside}_{what}_RECT_MEDIUM_A'
        dec_parts[f'DECAL_{side_of(part)}_{what}_RECT_MEDIUM_A'] = decals.mesh_from_groups(decals.from_mw(P, part), PT, off=0.005, levels=2)
for key, nm in (('medium', 'DECAL_HOOD_RECT_MEDIUM_A'), ('small', 'DECAL_HOOD_RECT_SMALL_A')):
    dec_parts[nm] = decals.mesh_from_groups(decals.hood_from_corolla(_hood_npz, key, hood['pos'], hood['tri']), (hood['pos'], hood['tri']), off=0.008)
for nm, ms in list(dec_parts.items()):
    solids.append(solid('FOCUS_' + nm, ms))
    if 'DOOR' in nm or 'QUARTER' in nm:          # the wide-body kits use their own decal parts (same body here)
        for w in range(1, 5):
            solids.append(solid(f'FOCUS_WIDE{w}_' + nm, ms))
LOG['decals'] = {nm: ntris(ms) for nm, ms in dec_parts.items()}
for s in solids:
    assert sum(len(g['tri']) for g in s['groups']) <= CAP, (s['name'], LOG.get('decimation'), LOG.get('budget'))
for s in solids:
    print(s['name'], sum(len(g['tri']) for g in s['groups']), len(s['pos']))

size = ug2write.write(solids, f'{OUT}/GEOMETRY.BIN')
LOG['geometry_bytes'] = size

# ---------------------------------------------------------------- textures
info_e, tex_e = tpk2.parse('escort/TEXTURES.BIN')
tmpl_dxt1 = next(t for t in tex_e if t['name'] == 'FOCUS_MISC')
tmpl_dxt3 = next(t for t in tex_e if t['name'] == 'FOCUS_BADGING')
out_tex = []
place = 0
for name, (src, sz, fmt) in TEX.items():
    img = Image.open(f'texdump/mw_{src}.png').convert('RGBA').resize((sz, sz), Image.LANCZOS)
    rgba = np.array(img)
    if name == 'FOCUS_BRAKELIGHT_GLASS':      # v6: MW lens is dark red (lit by emission in MW); UG2 needs it bright
        f = rgba[..., :3].astype(float)
        red = f[..., 0] > f[..., 1:].max(-1) + 20
        f[red, 0] = np.clip(f[red, 0] * 2.2 + 40, 0, 235); f[red, 1:] = np.clip(f[red, 1:] * 1.5, 0, 40)
        rgba[..., :3] = f.astype(np.uint8)
        rgba[..., 3] = np.maximum(rgba[..., 3], 215)
    if fmt == 'DXT1':
        rgba[..., 3] = 255
        data = dxtenc.encode_dxt1(rgba); tm = tmpl_dxt1
    else:
        data = dxtenc.encode_dxt3(rgba); tm = tmpl_dxt3
    info = tpkwrite.build_info(tm['info'], name, bh(name), sz, sz, len(data), place)
    place += len(data)
    out_tex.append(dict(hash=bh(name), info=info, dds=tm['dds'], data=data, name=name, fmt=fmt, size=sz))
for t in tex_e:
    if t['hash'] in KEEP_ESCORT:
        info = bytearray(t['info'])
        struct.pack_into('<I', info, 48, place); struct.pack_into('<I', info, 52, place + t['size'])
        place += t['size']
        out_tex.append(dict(hash=t['hash'], info=bytes(info), dds=t['dds'], data=t['data'], tail=t['tail'], name=t['name'], fmt=t['fmt'].decode(), size=t['w']))
LOG['textures'] = {t['name']: [t['fmt'], t['size']] for t in out_tex}
LOG['textures_bytes'] = tpkwrite.write_raw(out_tex, f'{OUT}/TEXTURES.BIN')  # v3: RAWW (mwtc layout) instead of JDLZ
json.dump(LOG, open(f'{OUT}/build_log.json', 'w'), indent=1)
print(json.dumps(LOG, indent=1))
