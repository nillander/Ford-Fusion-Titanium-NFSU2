"""Builds a Fusion for NFSU2 from an approved MW2005 release.

Usage: python build.py <out-dir> [2018|2012]
  2018  MUSTANGGT -> MUSTANGGT (Fusion Titanium 2018 AWD; mesmo nome de slot dos dois jogos)
  2012  COBALTSS  -> FOCUS     (Fusion Titanium 2012 FWD; same part split, clip, glass and decals as 2018)

The destination names follow the nfsu360 layout proved on the Focus slot:
  <SLOT>_KIT00_BODY_A, <SLOT>_KITW01..04_BODY_A, <SLOT>_BASE_A, <SLOT>_KIT00_FRONT_WHEEL_A
Every solid stays under 65,535 indices. Opaque textures are DXT1; only lamp lenses use DXT3.
"""
import pickle, json, struct, sys, os
import numpy as np
from PIL import Image
import decimate, ug2write, tpkwrite, tpk2, dxt, dxtenc, ports
from hashes import bh

PORT = ports.get(sys.argv[2] if len(sys.argv) > 2 else '2018')
MW, UG2 = PORT['mw'], PORT['ug2']
OUT = sys.argv[1] if len(sys.argv) > 1 else 'out'
os.makedirs(OUT, exist_ok=True)
P = pickle.load(open('mw_parts.pkl', 'rb'))
LOG = {'port': PORT['id'], 'mw': MW, 'ug2': UG2}

# ---------------------------------------------------------------- materials
M = {k: bh(k) for k in ['CARSKIN', 'WINDSHIELD', 'DULLPLASTIC', 'INTERIOR', 'LICENSEPLATE', 'HEADLIGHTGLASS',
                        'HEADLIGHTREFLECTOR', 'BRAKELIGHT', 'BRAKELIGHTGLASS', 'DRIVER', 'RUBBER', 'USER_RIMS']}
T_PAINT = 0x3C84D757   # global paint texture used by every UG2 body (retail and mods)
T_WINDOW = bh('WINDOW')
def sheet(suffix):
    """PNG stem for a MW texture. The TPK truncates the name (HEADLIG vs HEADLIGH)."""
    prefix = MW + '_'
    hits = []
    for filename in os.listdir('texdump'):
        if not (filename.startswith('mw_') and filename.endswith('.png')):
            continue
        stem = filename[3:-4]
        if stem.startswith(prefix) and stem[len(prefix):].startswith(suffix):
            hits.append(stem)
    if len(hits) != 1:
        raise SystemExit('texture %s for %s: %s' % (suffix, MW, hits))
    return hits[0]


TEX = {  # destination name -> (mw sheet suffix, size, format[, processing])
    UG2 + '_MISC': ('MISC', 512, 'DXT1'),
    UG2 + '_LOGO': ('LOGO', 512, 'DXT1'),
    UG2 + '_INTERIOR': ('INTERIOR', 512, 'DXT1'),
    UG2 + '_BADGING': ('BADGING', 512, 'DXT1'),
    UG2 + '_KIT00_HEADLIGHT': ('KIT00_HEADLIG', 256, 'DXT1'),
    UG2 + '_KIT00_BRAKELIGHT': ('KIT00_BRAKELI', 256, 'DXT1'),
    UG2 + '_RIM': ('RIM', 256, 'DXT1'),
    UG2 + '_TIRE': ('TIRE', 256, 'DXT1'),
    UG2 + '_DRIVER': ('DRIVER', 256, 'DXT1'),
}
# Lamp sheets. The 2018 keeps each lamp on its own sheet; the 2012 draws the tail-light housings on the
# headlight sheet and both lenses on the tail-light sheet. A lens is a DXT3 copy of the sheet its UVs point at,
# one copy per (sheet, role): the tail-light copy gets the bright red of v6, the headlight copy stays clear.
LAMP_SHEETS = ('KIT00_HEADLIG', 'KIT00_BRAKELI')
LENS_NAMES = {('KIT00_HEADLIG', 'head'): '_HEADLIGHT_GLASS', ('KIT00_BRAKELI', 'brake'): '_BRAKELIGHT_GLASS',
              ('KIT00_BRAKELI', 'head'): '_HEADLIGHT_LENS', ('KIT00_HEADLIG', 'brake'): '_BRAKELIGHT_LENS'}


def lamp_sheet(mwtex):
    body = mwtex[len(MW) + 1:] if mwtex.startswith(MW + '_') else mwtex
    return next((k for k in LAMP_SHEETS if body.startswith(k)), None)


def opaque_tex(mwtex):
    return UG2 + {'KIT00_HEADLIG': '_KIT00_HEADLIGHT', 'KIT00_BRAKELI': '_KIT00_BRAKELIGHT'}[lamp_sheet(mwtex)]


def lens_tex(mwtex, role):
    key = lamp_sheet(mwtex)
    name = UG2 + LENS_NAMES[(key, role)]
    TEX.setdefault(name, (key, 256, 'DXT3', 'boost' if role == 'brake' else None))
    return name


KEEP_SUFFIXES = ('SHADOWFE', 'SHADOWIG', 'NEON')
# v11: UG2's CarRenderInfo binds only car textures whose names it builds itself (SPEED2.EXE strings: %s_MISC,
# %s_SIDELIGHT, %s_DOOR_HANDLE, %s_CENTRE_BRAKELIGHT, <lamp TEXTURE_NAME>_GLASS_OFF, ...). Any other name in
# TEXTURES.BIN is never bound and the groups using it are not drawn: this is why KIT00_HEADLIGHT, the lens
# copies and the 2018 SOLID_LAMPS test were invisible while MISC showed. 'tex_alias' renames those sheets.
TEX_ALIAS = {UG2 + '_' + k: UG2 + '_' + v for k, v in PORT.get('tex_alias', {}).items()}
ALIAS_H = {bh(k): bh(v) for k, v in TEX_ALIAS.items()}
LOG['tex_alias'] = TEX_ALIAS


def alias(name):
    return TEX_ALIAS.get(name, name)


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
    return [weld(g) | {'tex': g['tex'], 'mat': g['mat']} for g in P[MW + '_' + part]['groups']]


def tex_for(mwtex, mwmat):
    if lamp_sheet(mwtex):
        if mwmat == 'HEADLIGHTGLASS':
            return bh(lens_tex(mwtex, 'head')), M['HEADLIGHTGLASS']
        return bh(opaque_tex(mwtex)), M['HEADLIGHTREFLECTOR']
    body = mwtex[len(MW) + 1:] if mwtex.startswith(MW + '_') else mwtex
    mat = M.get(mwmat, M['DULLPLASTIC'])
    return bh(UG2 + '_' + body), mat


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


def drop_inward_twins(g, name, keep_inward=False):
    """MW shells carry a copy of each face in the same place, turned the other way (the underside of the hood,
    the inner layer of the glass, the back of the lamp housings). The plain game culls it; with the mods that
    draw both faces the dark copy fights the visible one (MW v2.6/v2.8). Keep one face: the one looking out of
    the car, or into the cabin for the interior (keep_inward)."""
    tw, fn, c = twins.twins(g['pos'], g['tri'])
    o = outwardness(g)
    drop = tw & ((o > 0) if keep_inward else (o < 0))
    LOG.setdefault('inward_twins_removed', {})[name] = int(drop.sum())
    out = compact(g, ~drop)
    for k in ('tex', 'mat'):
        if k in g: out[k] = g[k]
    return out


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
paint = drop_inward_twins(weld(P[MW + '_KIT00_BODY_B']['groups'][0]), 'paint_B')
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
wA = weld(P[MW + '_KIT00_BODY_A']['groups'][0])
_tA = trunk_region(wA)
# The 2012 rear end is heavier at every LOD; its port takes the lid from the LOD in ports.py ('trunk_lod').
# The lid is its own mesh component (a gap separates it from the body), so the LOD change leaves no step.
TRUNK_LOD = os.environ.get('BUILD_TRUNK_LOD', PORT.get('trunk_lod', 'A'))
assert TRUNK_LOD in ('A', 'B', 'C', 'D'), TRUNK_LOD
LOG['trunk_lod'] = TRUNK_LOD
_wT = wA if TRUNK_LOD == 'A' else weld(P[MW + '_KIT00_BODY_' + TRUNK_LOD]['groups'][0])
trunk_paint = drop_inward_twins(compact(_wT, trunk_region(_wT)), 'trunk_' + TRUNK_LOD)
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
REAR_X, NOSE_X, NOSE_Y = PORT.get('rear_x', -1.9), 2.0, 0.45
BOXES = {'rear': dict(xmax=REAR_X), 'nose': dict(xmin=NOSE_X, ymin=-NOSE_Y, ymax=NOSE_Y, zmin=0.52, zmax=0.75),
         'roof_front': dict(xmin=0.15, xmax=0.6, ymin=-0.5, ymax=0.5, zmin=1.05)}
bB = body_paint; A_parts = {}
REAR_LOD = PORT.get('rear_lod', 'A')         # 2012: the rear bumper from LOD B (same cut, lighter)
for nm, box in BOXES.items():
    insB, bB = clip.split_box(bB, box)
    ins, _ = clip.split_box(restA, box)
    A_parts[nm] = insB if (nm == 'rear' and REAR_LOD == 'B') else ins
rearA = A_parts['rear']
noseA = merge([A_parts['nose'], A_parts['roof_front']])      # these go into BASE
BODY_B_TARGET = PORT.get('body_b_target', 14900)
bB = dec(bB, BODY_B_TARGET, 'paint_B_flat')
# 'rear_in': where the LOD A rear bumper goes. 'trunk' frees the body for the 2012 headlights; the only
# side effect is the audio screen, which already swings TRUNK_A around the slot's own pivot.
REAR_IN = PORT.get('rear_in', 'body')
if REAR_IN == 'trunk':
    body_paint = bB
    trunk_paint = merge([trunk_paint, rearA])
else:
    body_paint = merge([bB, rearA])
hood = outward_only(weld(P[MW + '_KIT00_HOOD_B']['groups'][0]), 'hood_B', clamp=(1.2, 1.9), zc=0.35)
A_parts['body_B'] = bB
LOG['paint_lods'] = {k + '_A': int(len(v['tri'])) for k, v in A_parts.items()}

# ---------------------------------------------------------------- lamps. Lenses double-sided, drawn last.
# A lens is told apart by its part (*_GLASS_*), not by the MW material: since MW v2.7 the 2018 tail-light lens
# uses a diffuse shader there. Inside a glass part, a group with the MW BRAKELIGHT material is an opaque
# reflector (the 2012 pair above the exhausts; MW lesson 17) and stays opaque.
# Tail-light lens: retail MOLDINGS material (BRAKELIGHTGLASS is only the glow shown when braking).
LOD = PORT.get('lamps', dict(head='C', head_glass='C', brake='B', brake_glass='B'))
# 'lens': 'double' draws both faces (v4); 'outward' turns the faces that point into the car around and keeps one
# layer, which looks the same from outside at half the triangles.
LENS = PORT.get('lens', 'double')


def face_out(g):
    o = outwardness(g)
    inward = o < 0
    if not inward.any():
        return g
    keep = compact(g, ~inward)
    flip = compact(g, inward)
    flip = dict(flip, nrm=-flip['nrm'], tri=flip['tri'][:, ::-1])
    LOG.setdefault('lens_faces_turned', 0); LOG['lens_faces_turned'] += int(inward.sum())
    return merge([keep, flip])

head_opaque, head_glass, brake_opaque, brake_glass = [], [], [], []
fog_meshes = []
tail_outlines, fog_outlines = [], []
lamp_sides = [sd for sd in ('RIGHT', 'LEFT') if '%s_KIT00_%s_HEADLIGHT_%s' % (MW, sd, LOD['head']) in P]
if PORT.get('opaque_reflectors'):
    import solid_lamps
for side in lamp_sides:
    for part, role, lod in (('HEADLIGHT', 'head', LOD['head']), ('HEADLIGHT_GLASS', 'head', LOD['head_glass']),
                            ('BRAKELIGHT', 'brake', LOD['brake']), ('BRAKELIGHT_GLASS', 'brake', LOD['brake_glass'])):
        name = 'KIT00_%s_%s_%s' % (side, part, lod)
        if MW + '_' + name not in P:
            continue
        for g in groups_of(name):
            if PORT.get('fog_lod') and role == 'head':
                c = g['pos'][g['tri']].mean(1)
                fog = (c[:, 0] > 1.9) & (c[:, 2] < .3) & (np.abs(c[:, 1]) > .5)
                g = compact(g, ~fog) | {'tex': g['tex'], 'mat': g['mat']}
            if (PORT.get('opaque_reflectors') and role == 'brake'
                    and part.endswith('GLASS') and g['mat'] == 'BRAKELIGHT'
                    and g['pos'][:, 0].max() < -1.7 and g['pos'][:, 2].max() < .5):
                # v11: the plate has a front and a back layer about 1 cm apart (not exact twins) and its source
                # normals average both, so face_out kept two layers with skewed normals: dark red in the game.
                # Keep the outward layer only, with one flat normal per reflector (2018 v10.9 lesson).
                reflector = solid_lamps.single_face(compact(g, outwardness(g) > 0))
                LOG.setdefault('inner_faces_removed', {})[name + '_opaque_reflector'] = int((outwardness(g) <= 0).sum())
                reflector = solid_lamps.colour(reflector, solid_lamps.RED_UV)
                brake_opaque.append(mesh(reflector, bh(UG2 + '_MISC'), M['DULLPLASTIC']))
                LOG.setdefault('opaque_reflectors', {})[name] = dict(
                    tris=len(reflector['tri']), texture=UG2 + '_MISC', material='DULLPLASTIC',
                    uv=solid_lamps.RED_UV.tolist(), color=[255, 78, 86, 255])
            elif part.endswith('GLASS') and g['mat'] != 'BRAKELIGHT':
                lg = double_sided(g) if LENS == 'double' else face_out(g)
                m = mesh(lg, bh(lens_tex(g['tex'], role)), M['HEADLIGHTGLASS'] if role == 'head' else bh('MOLDINGS'))
                (head_glass if role == 'head' else brake_glass).append(m)
            else:
                g = drop_inward_twins(g, name + '_' + g['mat'])
                m = mesh(g, bh(opaque_tex(g['tex'])), M['HEADLIGHTREFLECTOR'] if role == 'head' else M['DULLPLASTIC'])
                (head_opaque if role == 'head' else brake_opaque).append(m)
if PORT.get('solid_tail'):
    import solid_lamps
    # Both SOLID_LAMPS and KIT00_BRAKELIGHT tests were invisible in-game.
    # Reuse the MISC entry and material group drawn by visible base details.
    solid_tex = UG2 + '_MISC'
    # Keep the centre stop lamp and cabin details; remove the four rear housings.
    retained = []
    for m in brake_opaque:
        c = m['pos'][m['tri']].mean(1)
        if (c[:, 0] > -1.7).any():
            keep = compact(m, c[:, 0] > -1.7)
            retained.append(mesh(keep, m['tex'], m['mat']))
    brake_opaque, brake_glass = retained, []
    LOG['solid_tail'] = {}
    trim_sources = []
    for source in groups_of('BASE_A'):
        if source['tex'] == MW + '_MISC':
            selected = solid_lamps.trunk_trim_mask(source)
            if selected.any():
                trim_sources.append(compact(source, selected))
    for side in lamp_sides:
        for g in groups_of('KIT00_%s_BRAKELIGHT_GLASS_A' % side):
            for name, red, white in solid_lamps.tail_patches(g):
                tail_outlines.append(red)
                red = face_out(drop_inward_twins(red, 'solid_tail_' + name))
                for layer in (red, white):
                    if layer is white:
                        layer = solid_lamps.rear_finish(layer, lens=True)
                    brake_opaque.append(mesh(layer, bh(solid_tex), M['DULLPLASTIC']))
                sign = 1 if name.startswith('left') else -1
                detail = (solid_lamps.outer_trim(red, white, sign) if name.endswith('body')
                          else solid_lamps.lower_inner_white(red, white, trim_sources))
                if len(detail['tri']):
                    detail = face_out(detail)
                    detail = solid_lamps.rear_finish(detail, lens=not name.endswith('body'))
                    brake_opaque.append(mesh(detail, bh(solid_tex), M['DULLPLASTIC']))
                LOG.setdefault('tail_white_details', {})[name] = dict(tris=len(detail['tri']),
                    role='outer_trim' if name.endswith('body') else 'lower_inner_white')
                LOG['solid_tail'][name] = dict(red=len(red['tri']), white=len(white['tri']), backing_m=.003)
            c = g['pos'][g['tri']].mean(1)
            low = c[:, 2] < .5
            if low.any():
                reflector = face_out(drop_inward_twins(compact(g, low), 'solid_reflector'))
                brake_opaque.append(mesh(solid_lamps.colour(reflector, [.25, .5]), bh(solid_tex), M['DULLPLASTIC']))
if PORT.get('fog_lod'):
    import solid_lamps
    for side in lamp_sides:
        for part in ('HEADLIGHT', 'HEADLIGHT_GLASS'):
            for g in groups_of('KIT00_%s_%s_%s' % (side, part, PORT['fog_lod'])):
                c = g['pos'][g['tri']].mean(1)
                sel = (c[:, 0] > 1.9) & (c[:, 2] < .3) & (np.abs(c[:, 1]) > .5)
                if not sel.any():
                    continue
                g = compact(g, sel) | {'tex': g['tex'], 'mat': g['mat']}
                # v11.2: 'fog_glass' draws the fog lamp like the main headlight (housing with the lamp sheet and
                # HEADLIGHTREFLECTOR, real lens with HEADLIGHTGLASS) instead of a flat white sheet over it. The
                # sheet outline is still computed: it removes base-car pieces inside the lamp.
                if part.endswith('GLASS'):
                    for sign in (1, -1):
                        fg = compact(g, g['pos'][g['tri']].mean(1)[:, 1] * sign > 0)
                        lens = solid_lamps.backing(fg, radial=[1., sign, 0.])
                        fog_outlines.append(lens)
                        if not PORT.get('fog_glass'):
                            fog_meshes.append(mesh(lens, bh(solid_tex), M['DULLPLASTIC']))
                    if PORT.get('fog_glass'):
                        fog_meshes.append(mesh(face_out(g), bh(lens_tex(g['tex'], 'head')), M['HEADLIGHTGLASS']))
                elif PORT.get('fog_glass'):
                    g = drop_inward_twins(g, 'fog_' + side + '_housing')
                    fog_meshes.append(mesh(g, bh(opaque_tex(g['tex'])), M['HEADLIGHTREFLECTOR']))
                else:
                    fog_meshes.append(mesh(face_out(g), bh(opaque_tex(g['tex'])), M['DULLPLASTIC']))
    LOG['fog'] = dict(lod=PORT['fog_lod'], destination='BASE_A', tris=ntris(fog_meshes))
if PORT.get('solid_tail'):
    for m in brake_opaque + fog_meshes:
        if m['tex'] == bh(solid_tex):
            u = m['uv'][:, 0]
            # Preserve explicit atlas cells: the lens-white cell also has u > .75.
            # Only the source placeholder UVs need remapping into the MISC atlas.
            atlas_uv = ((m['uv'][:, 1] >= 14 / 16) & (m['uv'][:, 1] < 15 / 16)) & (
                np.isclose(u, solid_lamps.GRAY_UV[0])
                | np.isclose(u, solid_lamps.WHITE_UV[0])
                | np.isclose(u, solid_lamps.RED_UV[0]))
            mapped = np.where((u > .75)[:, None], solid_lamps.GRAY_UV,
                              np.where((u < .5)[:, None], solid_lamps.RED_UV, solid_lamps.WHITE_UV))
            m['uv'] = np.where(atlas_uv[:, None], m['uv'], mapped)
    LOG['lamp_atlas'] = dict(texture=solid_tex, red_uv=solid_lamps.RED_UV.tolist(),
                            white_uv=solid_lamps.WHITE_UV.tolist())
LOG['lamps'] = dict(lod=LOD, sides=lamp_sides, head=ntris(head_opaque) + ntris(head_glass), brake=ntris(brake_opaque) + ntris(brake_glass))

def split_y(ms, lim=None):
    lim = (.585 if PORT.get('solid_tail') else .6) if lim is None else lim
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
if PORT.get('solid_tail'):
    # Painted inner lips from the donor must not poke through the new white sheets.
    for name, paint_mesh in (('body', body_paint), ('trunk', trunk_paint)):
        remove = solid_lamps.volume_mask(paint_mesh['pos'][paint_mesh['tri']].mean(1), tail_outlines)
        LOG.setdefault('tail_paint_under_lens_removed', {})[name] = int(remove.sum())
        clean = compact(paint_mesh, ~remove)
        if name == 'body':
            body_paint = clean
        else:
            trunk_paint = clean
trunk_target = os.environ.get('BUILD_TRUNK_PAINT_TARGET', PORT.get('trunk_paint_target'))
if trunk_target:
    target = int(trunk_target)
    assert target > 0, target
    trunk_paint = dec(trunk_paint, target, 'trunk_paint')
    LOG['trunk_paint_target'] = target
VP = lambda m: mesh(vinyluv.apply(m, UG2), T_PAINT, M['CARSKIN'])       # paint with vinyl UVs
body_list = [VP(body_paint)] + head_opaque + head_glass
NOSE_IN = PORT.get('nose_in', 'base')          # LOD A nose and roof front: BASE (v9) or BODY
if NOSE_IN == 'body':
    body_list = [VP(body_paint), VP(noseA)] + head_opaque + head_glass

trunk_list = [VP(trunk_paint)] + brake_opaque_in + brake_glass_in
if PORT.get('outer_brake_in', 'base') == 'trunk':      # outer tail lights next to the rear bumper
    trunk_list = [VP(trunk_paint)] + brake_opaque_in + brake_opaque + brake_glass_in + brake_glass
    brake_opaque, brake_glass = [], []

if PORT.get('solid_tail'):
    # Preserve the real 2018 trim from MW. The 2012 removal does not apply to this source.
    for g in groups_of('BASE_A'):
        if g['tex'] != MW + '_MISC':
            continue
        selected = solid_lamps.trunk_trim_mask(g)
        if selected.any():
            trim = face_out(drop_inward_twins(compact(g, selected), 'original_2018_trunk_trim'))
            trim = solid_lamps.rear_finish(trim)
            trunk_list.append(mesh(trim, bh(solid_tex), M['DULLPLASTIC']))
            LOG['trunk_trim'] = dict(source='MW BASE_A/MISC', tris=len(trim['tri']), color='white', destination='TRUNK_A')
    assert 'trunk_trim' in LOG, 'original 2018 trunk trim missing'

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
    if g['tex'] == MW + '_MISC':      # v7: Ford oval on the nose removed (the nose paint is now smooth LOD A)
        emb = (c[:, 0] > 2.24) & (np.abs(c[:, 1]) < 0.075) & (c[:, 2] > 0.58) & (c[:, 2] < 0.64)
        LOG['emblem_removed'] = int(emb.sum()); k &= ~emb
    if k.any(): _baseC.append(compact(g, k) | {'tex': g['tex'], 'mat': g['mat']})
for g in groups_of('BASE_B'):             # v7: exhaust tips and diffuser from LOD B (C was too coarse)
    c = g['pos'][g['tri']].mean(1); k = _rear_low(c)
    if k.any() and g['tex'] in (MW + '_MISC', MW + '_LOGO'):
        _baseC.append(compact(g, k) | {'tex': g['tex'], 'mat': g['mat']}); LOG.setdefault('rear_low_from_B', {})[g['tex']] = int(k.sum())
for g in _baseC:
    if PORT.get('solid_tail'):
        c = g['pos'][g['tri']].mean(1)
        removed = solid_lamps.volume_mask(c, tail_outlines) | solid_lamps.volume_mask(c, fog_outlines, front=True)
        if g['tex'] == MW + '_MISC':
            removed |= solid_lamps.trunk_trim_mask(g)
        LOG.setdefault('lamp_base_internals_removed', {})[g['tex']] = LOG.get('lamp_base_internals_removed', {}).get(g['tex'], 0) + int(removed.sum())
        g = compact(g, ~removed) | {'tex': g['tex'], 'mat': g['mat']}
    g = drop_inward_twins(g, 'base_' + g['tex'][len(MW) + 1:] + '_' + str(g['mat']))
    if g['tex'] in (MW + '_LOGO', MW + '_MISC'):
        fr = near_glass(g['pos'][g['tri']].mean(1))
        if fr.any():
            LOG.setdefault('frit_removed', {})[g['tex']] = int(fr.sum())
            g = compact(g, ~fr) | {'tex': g['tex'], 'mat': g['mat']}
    if len(g['tri']) > 2000:
        g = dec(g, int(len(g['tri']) * PORT.get('base_dec', 0.9)), 'base_' + g['tex'][len(MW) + 1:]) | {'tex': g['tex'], 'mat': g['mat']}
    if g['tex'] in (MW + '_LOGO', MW + '_MISC'):
        # v6: MW draws both faces; the black valances of the bumpers were modelled facing inwards and vanish
        # in UG2 (back-face culling) -> lower front/rear areas made double-sided
        c = g['pos'][g['tri']].mean(1)
        low = (np.abs(c[:, 0]) > 1.85) & (c[:, 2] < 0.5)
        if PORT.get('valance', 'all') == 'inward':      # only the faces that look into the car get a back face
            low &= outwardness(g, clamp=(-1.0, 1.0), zc=0.7) < 0
        if low.any():
            ds = double_sided(compact(g, low))
            LOG.setdefault('double_sided_valance', {})[g['tex']] = int(low.sum())
            gg = merge([compact(g, ~low), ds])
            g = gg | {'tex': g['tex'], 'mat': g['mat']}
    if g['tex'] == MW + '_SKIN1':          # 2012: painted bumper pieces live in the MW base; same paint as the body
        base.append(VP(g)); LOG.setdefault('base_paint', 0); LOG['base_paint'] += int(len(g['tri'])); continue
    t, m = tex_for(g['tex'], g['mat'])
    base.append(mesh(g, t, m))
for g in groups_of('KIT00_DRIVER_A'):
    base.append(mesh(dec(g, 700, 'driver'), bh(UG2 + '_DRIVER'), M['DRIVER']))
base += brake_opaque + fog_meshes
base.append(VP(hood))
if NOSE_IN == 'base':
    base.append(VP(noseA))
# glass (v5): new sheets generated by scripts/newglass.py (needs scipy + contourpy): one clean single-sided
# surface per window fitted to the MW glass shape, outline widened 30 mm and bent inwards under the frame
_G = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'vidros_v5.npz')) \
    if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'vidros_v5.npz')) else np.load('vidros_v5.npz')
glass = merge([{k: _G[f'{i}_{k}'] for k in ('pos', 'nrm', 'uv', 'col', 'tri')} for i in range(int(_G['n']))])
LOG['glass'] = dict(source='docs/vidros_v5.npz', windows=int(_G['n']), tris=int(len(glass['tri'])), under_frame_m=0.03)
# The floor and pedals (z < 0.30) cannot be seen through the windows; leaving them out keeps the interior
# budget for the seats and dashboard (the MW base and lamps grew since v9 and squeezed the interior).
FLOOR_Z = 0.30
inter = []
for g in groups_of('KIT00_INTERIOR_A'):
    k = g['pos'][g['tri']].mean(1)[:, 2] >= FLOOR_Z
    LOG.setdefault('interior_floor_removed', 0); LOG['interior_floor_removed'] += int((~k).sum())
    if k.any(): inter.append(drop_inward_twins(compact(g, k) | {'tex': g['tex'], 'mat': g['mat']}, 'interior_' + g['mat'], keep_inward=True))
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
    if g['tex'] == MW + '_RIM':
        wheel.append(mesh(g, bh(UG2 + '_RIM'), M['USER_RIMS']))
    else:
        wheel.append(mesh(g, bh(UG2 + '_TIRE'), M['RUBBER']))

# ---------------------------------------------------------------- markers (MW positions, UG2 left = +y)
mw_markers = P[MW + '_BASE_A']['markers']
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
    # v10.3: one group per (texture, material), as in the v9 that drew everything in the game. The 2012 body and
    # trunk had the left and right lamps (and the nose) as separate groups with the same key, and the game drew
    # only part of them.
    keyed = {}
    for m in meshes:
        m = dict(m, tex=ALIAS_H.get(m['tex'], m['tex']))
        if len(m['tri']):
            keyed.setdefault((m['tex'], m['mat']), []).append(m)
    meshes = [v[0] if len(v) == 1 else mesh(merge(v), k[0], k[1]) for k, v in keyed.items()]
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
    solids.append(solid(f'{UG2}_{slot}_BODY_A', body_list, exhaust_markers))
solids.append(solid(UG2 + '_KIT00_TRUNK_A', trunk_list))

solids.append(solid(UG2 + '_BASE_A', base, base_markers))
solids.append(solid(UG2 + '_KIT00_FRONT_WHEEL_A', wheel))
if PORT.get('wheel_donor'):
    import ug2, hashlib
    donor = PORT['wheel_donor']
    donor_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'CARS', donor, 'GEOMETRY.BIN')
    s = next(s for s in ug2.parse(donor_path)[3] if s['hash'] == bh(donor + '_KIT00_FRONT_WHEEL_A'))
    v = np.frombuffer(s['vb'], np.uint8).reshape(-1, 36)
    tex_map = {bh(donor + '_' + k): bh(UG2 + '_' + k) for k in ('RIM', 'TIRE')}
    assert set(s['tex']) <= set(tex_map), s['tex']
    copied = dict(name=UG2 + '_KIT00_FRONT_WHEEL_A',
                  pos=v[:, :12].copy().view('<f4').reshape(-1, 3),
                  nrm=v[:, 12:24].copy().view('<f4').reshape(-1, 3),
                  col=v[:, 24:28].copy().view('<u4').reshape(-1),
                  uv=v[:, 28:36].copy().view('<f4').reshape(-1, 2),
                  tex=[tex_map[t] for t in s['tex']], light=s['light'],
                  groups=[dict(tex_i=g['tex'], sh_i=g['sh'],
                               tri=s['ib'][g['off']:g['off'] + g['len']].reshape(-1, 3)) for g in s['groups']], markers=[])
    solids[-1] = copied
    LOG['wheel_donor'] = dict(slot=donor, sha256=hashlib.sha256(open(donor_path, 'rb').read()).hexdigest())
    LOG['solids'][copied['name']] = dict(tris=sum(len(g['tri']) for g in copied['groups']),
                                       indices=sum(g['tri'].size for g in copied['groups']),
                                       verts=len(copied['pos']), groups=len(copied['groups']))
# 'lod_alias' (MUSTANGGT): the retail slots list B/C LODs for body, trunk and wheel. The FOCUS slot (set up by the
# Escort installer) draws _A only; the Mustang slot drew none of these three. Same mesh under the other LOD names.
for letter in PORT.get('lod_alias', ()):
    for src in [s_ for s_ in solids if s_['name'] in (UG2 + '_KIT00_BODY_A', UG2 + '_KIT00_TRUNK_A', UG2 + '_KIT00_FRONT_WHEEL_A')]:
        solids.append(dict(src, name=src['name'][:-1] + letter))

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
dec_parts['DECAL_FRONT_WINDOW_WIDE_MEDIUM_A'] = decals.mesh_from_groups(decals.from_mw(P, MW + '_DECAL_FRONT_WINDOW_WIDE_MEDIUM_A'), GT, off=0.004, levels=2)
dec_parts['DECAL_REAR_WINDOW_WIDE_MEDIUM_A'] = decals.mesh_from_groups(decals.from_mw(P, MW + '_DECAL_REAR_WINDOW_WIDE_MEDIUM_A'), GT, off=0.004, levels=2)
for mwside in ('LEFT', 'RIGHT'):
    for what in ('DOOR', 'QUARTER'):
        part = f'{MW}_KIT00_DECAL_{mwside}_{what}_RECT_MEDIUM_A'
        dec_parts[f'DECAL_{side_of(part)}_{what}_RECT_MEDIUM_A'] = decals.mesh_from_groups(decals.from_mw(P, part), PT, off=0.005, levels=2)
for key, nm in (('medium', 'DECAL_HOOD_RECT_MEDIUM_A'), ('small', 'DECAL_HOOD_RECT_SMALL_A')):
    dec_parts[nm] = decals.mesh_from_groups(decals.hood_from_corolla(_hood_npz, key, hood['pos'], hood['tri']), (hood['pos'], hood['tri']), off=0.008)
for nm, ms in list(dec_parts.items()):
    solids.append(solid(UG2 + '_' + nm, ms))
    if 'DOOR' in nm or 'QUARTER' in nm:          # the wide-body kits use their own decal parts (same body here)
        for w in range(1, 5):
            solids.append(solid(f'{UG2}_WIDE{w}_' + nm, ms))
LOG['decals'] = {nm: ntris(ms) for nm, ms in dec_parts.items()}
LOG['trunk_lid'] = int(len(trunk_paint['tri'])); LOG['hood'] = int(len(hood['tri']))
if os.environ.get('BUILD_DRY'):          # budget probe: print the pieces and stop before writing
    print(json.dumps({k: LOG.get(k) for k in ('budget', 'paint_lods', 'trunk_lid', 'hood', 'lamps', 'decimation', 'base_paint')}, indent=1))
    raise SystemExit(0)
for s in solids:
    assert sum(len(g['tri']) for g in s['groups']) <= CAP, (s['name'], LOG.get('decimation'), LOG.get('budget'))
for s in solids:
    print(s['name'], sum(len(g['tri']) for g in s['groups']), len(s['pos']))

size = ug2write.write(solids, f'{OUT}/GEOMETRY.BIN')
LOG['geometry_bytes'] = size

# ---------------------------------------------------------------- textures
info_e, tex_e = tpk2.parse(ports.TEMPLATE)


def _fmt(texture):
    return texture['fmt'].decode() if isinstance(texture['fmt'], bytes) else texture['fmt']


tmpl_dxt1 = next(t for t in tex_e if _fmt(t) == 'DXT1')
tmpl_dxt3 = next(t for t in tex_e if _fmt(t) == 'DXT3')
out_tex = []
place = 0
# v11.1: textures the game binds stay resident. With the 2012 lamps bound (v11), viewing the 2018 closed the
# game, as when its own trunk got heavier (v10.14): the car memory is tight. Leave out sheets no solid uses and
# let 'tex_size' shrink sheets (lens copies, badging) so the resident total stays below the working v10.x.
USED = {t for s in solids for t in s['tex']}
SIZES = PORT.get('tex_size', {})
for name, spec in TEX.items():
    suffix, sz, fmt = spec[:3]
    if bh(alias(name)) not in USED:
        LOG.setdefault('textures_unused_dropped', []).append(name)
        continue
    sz = SIZES.get(name[len(UG2) + 1:], sz)
    if suffix == '@solid_lamps':
        full = solid_lamps.atlas(sz)
    else:
        src = sheet(suffix)
        img = Image.open(f'texdump/mw_{src}.png').convert('RGBA')
        full = np.array(img)
    # 'tex_cells' (2012): MW lights the black inside of the headlight with its reflective lamp shader; UG2 draws it
    # black, so the lamps read as holes. Fill that 1/8 cell of the sheet with a darker copy of the chrome cell.
    for dst, srcc, k in PORT.get('tex_cells', {}).get(name[len(UG2) + 1:], ()):
        cw, ch = full.shape[1] // 8, full.shape[0] // 8
        cell = full[srcc[1] * ch:(srcc[1] + 1) * ch, srcc[0] * cw:(srcc[0] + 1) * cw].astype(float)
        cell[..., :3] *= k
        full[dst[1] * ch:(dst[1] + 1) * ch, dst[0] * cw:(dst[0] + 1) * cw] = cell.astype(np.uint8)
        LOG.setdefault('tex_cells', []).append([name, dst, srcc, k])
    rgba = np.array(Image.fromarray(full).resize((sz, sz), Image.LANCZOS))
    if (PORT.get('solid_tail') or PORT.get('opaque_reflectors')) and name == UG2 + '_MISC':
        rgba = solid_lamps.paint_misc(rgba, reflectors_only=not PORT.get('solid_tail'))
    if len(spec) > 3 and spec[3] == 'boost':   # v6: MW lens is dark red (lit by emission in MW); UG2 needs it bright
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
    info = tpkwrite.build_info(tm['info'], alias(name), bh(alias(name)), sz, sz, len(data), place)
    place += len(data)
    out_tex.append(dict(hash=bh(alias(name)), info=info, dds=tm['dds'], data=data, name=alias(name), fmt=fmt, size=sz))
kept = set()
for t in tex_e:
    suffix = next((item for item in KEEP_SUFFIXES if t['name'].endswith(item)), None)
    if suffix is None or suffix in kept:
        continue
    kept.add(suffix)
    name = UG2 + '_' + suffix
    info = tpkwrite.build_info(t['info'], name, bh(name), t['w'], t['h'], t['size'], place)
    place += t['size']
    out_tex.append(dict(hash=bh(name), info=info, dds=t['dds'], data=t['data'], tail=t['tail'], name=name, fmt=_fmt(t), size=t['w']))
LOG['textures'] = {t['name']: [t['fmt'], t['size']] for t in out_tex}
LOG['textures_bytes'] = tpkwrite.write_raw(out_tex, f'{OUT}/TEXTURES.BIN', slot=UG2)  # v3: RAWW (mwtc layout) instead of JDLZ
json.dump(LOG, open(f'{OUT}/build_log.json', 'w'), indent=1)
print(json.dumps(LOG, indent=1))
