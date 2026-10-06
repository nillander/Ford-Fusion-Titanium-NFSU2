"""Rear repair views read from compiled files, without flipping normals toward the camera."""
import sys
from pathlib import Path
import numpy as np
import ug2, tpk2, dxt, render
from hashes import bh

geo, texture, prefix = sys.argv[1:]
textures = {t['hash']: dxt.decode(t['data'], t['w'], t['h'], t['fmt'])
            for t in tpk2.parse(texture)[1]}
meshes = []
parts = {bh('MUSTANGGT_' + name) for name in ('KIT00_BODY_A', 'BASE_A', 'KIT00_TRUNK_A')}
for solid in ug2.parse(geo)[3]:
    if solid['hash'] not in parts:
        continue
    raw = np.frombuffer(solid['vb'], np.uint8).reshape(-1, 36)
    pos = raw[:, :12].copy().view('<f4').reshape(-1, 3)
    nrm = raw[:, 12:24].copy().view('<f4').reshape(-1, 3)
    uv = raw[:, 28:36].copy().view('<f4').reshape(-1, 2)
    for group in solid['groups']:
        tri = solid['ib'][group['off']:group['off'] + group['len']].reshape(-1, 3)
        c = pos[tri].mean(1)
        tri = tri[(c[:, 0] < -1.6) & (c[:, 2] < .86)]
        if not len(tri):
            continue
        tex = textures.get(solid['tex'][group['tex']])
        meshes.append(dict(pos=pos, nrm=nrm, uv=uv, tri=tri, tex=tex, color=(35, 70, 150)))
Path(prefix).parent.mkdir(parents=True, exist_ok=True)
for suffix, az, el in (('rear', 180, 4), ('angle', 205, 12)):
    render.render(meshes, az, el, W=1100, H=580, scale=540, center=(-2.1, 0, .5),
                  light=(-.7, .2, .7), cull=True, flip_normals=False).save(prefix + '-' + suffix + '.png')
