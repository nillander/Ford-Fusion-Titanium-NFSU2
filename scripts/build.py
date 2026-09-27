"""v4. Builds the Ford Fusion Titanium 2018 for NFSU2 (FOCUS slot) from the approved MW2005 port (V1prime-z10).

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
trunk_paint = compact(paint, is_trunk)
body_paint = compact(paint, ~is_trunk)
hood = outward_only(weld(P['MUSTANGGT_KIT00_HOOD_B']['groups'][0]), 'hood_B', clamp=(1.2, 1.9), zc=0.35)

# ---------------------------------------------------------------- lamps (LOD C). Lenses double-sided;
# brake lens uses the BRAKELIGHT material (BRAKELIGHTGLASS is only the glow shown when braking)
head_parts, brake_parts = [], []
for part in ['KIT00_RIGHT_HEADLIGHT_C', 'KIT00_RIGHT_HEADLIGHT_GLASS_C']:
    for g in groups_of(part):
        t, m = tex_for(g['tex'], g['mat'])
        if m == M['HEADLIGHTGLASS']:
            g = double_sided(g)
        head_parts.append(mesh(g, t, m))
for part in ['KIT00_RIGHT_BRAKELIGHT_C', 'KIT00_RIGHT_BRAKELIGHT_GLASS_C']:
    for g in groups_of(part):
        if g['mat'] == 'HEADLIGHTGLASS':
            brake_parts.append(mesh(double_sided(g), bh('FOCUS_BRAKELIGHT_GLASS'), M['BRAKELIGHT']))
        else:
            brake_parts.append(mesh(g, bh('FOCUS_KIT00_BRAKELIGHT'), M['DULLPLASTIC']))
# draw order inside a solid: opaque first, lenses (DXT3) last
head_opaque = [m for m in head_parts if m['mat'] != M['HEADLIGHTGLASS']]
head_glass = [m for m in head_parts if m['mat'] == M['HEADLIGHTGLASS']]
brake_opaque = [m for m in brake_parts if m['tex'] != bh('FOCUS_BRAKELIGHT_GLASS')]
brake_glass = [m for m in brake_parts if m['tex'] == bh('FOCUS_BRAKELIGHT_GLASS')]

body_list = [mesh(body_paint, T_PAINT, M['CARSKIN'])] + head_opaque + head_glass
trunk_list = [mesh(trunk_paint, T_PAINT, M['CARSKIN'])]

# ---------------------------------------------------------------- BASE
base = []
for g in groups_of('BASE_C'):
    if len(g['tri']) > 2000:
        g = dec(g, int(len(g['tri']) * 0.85), 'base_' + g['tex'][10:]) | {'tex': g['tex'], 'mat': g['mat']}
    t, m = tex_for(g['tex'], g['mat'])
    base.append(mesh(g, t, m))
base.append(mesh(hood, T_PAINT, M['CARSKIN']))
for g in groups_of('KIT00_DRIVER_A'):
    base.append(mesh(dec(g, 1000, 'driver'), bh('FOCUS_DRIVER'), M['DRIVER']))
base += brake_opaque
# glass: both MW pieces (FRONT_WINDOW + REAR_WINDOW), outer faces only, then mild decimation
glass = merge([weld(g) for part in ('KIT00_FRONT_WINDOW_A', 'KIT00_REAR_WINDOW_A') for g in P['MUSTANGGT_' + part]['groups']])
glass = outward_only(glass, 'glass')
GLASS_BUDGET = 3500
glass = dec(glass, GLASS_BUDGET, 'glass')
inter = groups_of('KIT00_INTERIOR_A')
fixed = ntris(base) + len(glass['tri']) + ntris(brake_glass) + ntris([m for m in base if m['mat'] == M['HEADLIGHTGLASS']]) * 0
INTERIOR_BUDGET = 21000 - fixed
big = [g for g in inter if len(g['tri']) > 1000]
small = [g for g in inter if len(g['tri']) <= 1000]
avail = INTERIOR_BUDGET - sum(len(g['tri']) for g in small)
tot = sum(len(g['tri']) for g in big)
for g in big:
    d = dec(g, int(avail * len(g['tri']) / tot), 'interior_' + g['mat'])
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
