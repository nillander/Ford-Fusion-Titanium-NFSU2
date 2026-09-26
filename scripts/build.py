"""Builds the Ford Fusion Titanium 2018 for NFSU2 (FOCUS slot) from the approved MW2005 port (V1prime-z10).

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


# ---------------------------------------------------------------- shared pieces
win = merge([weld(g) for g in P['MUSTANGGT_KIT00_FRONT_WINDOW_A']['groups']])
win = dec(win, 2300, 'windows')
windows = mesh(win, T_WINDOW, M['WINDSHIELD'])
hood = weld(P['MUSTANGGT_KIT00_HOOD_C']['groups'][0])


def body_meshes(kit):
    paint = merge([weld(P[f'MUSTANGGT_{kit}_BODY_C']['groups'][0]), hood])
    return [mesh(paint, T_PAINT, M['CARSKIN']), windows]


# BASE: LOD C of the base (grille, chassis, trims, plates, emblems) + interior + driver + lamps (LOD B)
base = []
for g in groups_of('BASE_C'):
    t, m = tex_for(g['tex'], g['mat'])
    base.append(mesh(g, t, m))
inter = groups_of('KIT00_INTERIOR_A')
big = [g for g in inter if len(g['tri']) > 1000]
small = [g for g in inter if len(g['tri']) <= 1000]
tot = sum(len(g['tri']) for g in big)
INTERIOR_BUDGET = 7600
for g in big:
    tgt = int(INTERIOR_BUDGET * len(g['tri']) / tot)
    d = dec(g, tgt, 'interior_' + g['mat'])
    t, m = tex_for(g['tex'], g['mat'])
    base.append(mesh(d, t, m))
for g in small:
    t, m = tex_for(g['tex'], g['mat'])
    base.append(mesh(g, t, m))
for g in groups_of('KIT00_DRIVER_A'):
    base.append(mesh(g, bh('FOCUS_DRIVER'), M['DRIVER']))
lamps_opaque, lamps_glass = [], []
for part in ['KIT00_RIGHT_HEADLIGHT_B', 'KIT00_RIGHT_BRAKELIGHT_B', 'KIT00_RIGHT_HEADLIGHT_GLASS_B', 'KIT00_RIGHT_BRAKELIGHT_GLASS_B']:
    for g in groups_of(part):
        t, m = tex_for(g['tex'], g['mat'])
        (lamps_glass if m in (M['HEADLIGHTGLASS'], M['BRAKELIGHTGLASS']) else lamps_opaque).append(mesh(g, t, m))
# opaque first, translucent (DXT3 lenses) last
base_glass = [b for b in base if b['mat'] == M['HEADLIGHTGLASS']]
base = [b for b in base if b['mat'] != M['HEADLIGHTGLASS']] + lamps_opaque + base_glass + lamps_glass

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


bodies = {'KIT00': 'KIT00', 'KITW01': 'KIT01', 'KITW02': 'KIT02', 'KITW03': 'KIT00', 'KITW04': 'KIT01'}
solids = []
for slot, kit in bodies.items():
    solids.append(solid(f'FOCUS_{slot}_BODY_A', body_meshes(kit), exhaust_markers))
solids.append(solid('FOCUS_BASE_A', base, base_markers))
solids.append(solid('FOCUS_KIT00_FRONT_WHEEL_A', wheel))
for s in solids:
    assert sum(len(g['tri']) for g in s['groups']) * 3 <= 65535, s['name']
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
LOG['textures_bytes'] = tpkwrite.write(out_tex, f'{OUT}/TEXTURES.BIN')
json.dump(LOG, open(f'{OUT}/build_log.json', 'w'), indent=1)
print(json.dumps(LOG, indent=1))
