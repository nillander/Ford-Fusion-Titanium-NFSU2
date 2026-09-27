"""Read one MW release car into mw_parts.pkl and texdump/.

Usage: python extract_mw.py [2018|2012]
The zip must already be extracted at mw/CARS/<MW slot>/.
"""
import os
import sys

import mwgeo
import numpy as np
import pickle
import ports
import tpk2
from hashes import bh
from PIL import Image
import dxt

PORT = ports.get(sys.argv[1] if len(sys.argv) > 1 else '2018')
SLOT = PORT['mw']
S = mwgeo.parse('mw/CARS/%s/GEOMETRY.BIN' % SLOT)
info, tex = tpk2.parse('mw/CARS/%s/TEXTURES.BIN' % SLOT)
names = {t['hash']: t['name'] for t in tex}
cand = 'CARSKIN WINDSHIELD WINDOW_FRONT WINDOW_REAR WINDOW_LEFT_FRONT WINDOW_RIGHT_FRONT WINDOW_LEFT_REAR WINDOW_RIGHT_REAR DULLPLASTIC INTERIOR LICENSEPLATE RUBBER HEADLIGHTGLASS HEADLIGHT BRAKELIGHT DRIVER BRAKEDISC CALIPER CHROME MAGSILVER'.split()
for c in cand:
    names.setdefault(bh(c), c)
out = {}
for s in S:
    parts = []
    for g, vb, stride, idx, k in mwgeo.meshes(s):
        pos, nrm, col, uv = mwgeo.vert_arrays(vb, stride)
        tri = idx.reshape(-1, 3)
        used = np.unique(tri)
        remap = np.full(len(pos), -1, np.int64)
        remap[used] = np.arange(len(used))
        parts.append(dict(
            tex=names.get(s['tex'][g['ids'][0]], '%08X' % s['tex'][g['ids'][0]]),
            mat=names.get(s['light'][g['ids'][5]], '%08X' % s['light'][g['ids'][5]]) if s.get('light') else None,
            pos=pos[used].astype(np.float64), nrm=nrm[used].astype(np.float64), col=col[used],
            uv=uv[used].astype(np.float64), tri=remap[tri], stride=stride))
    out[s['name']] = dict(groups=parts, mat=s['mat'], markers=s.get('markers_raw', b''), bmin=s['bmin'], bmax=s['bmax'])
pickle.dump(out, open('mw_parts.pkl', 'wb'))
print(PORT['id'], SLOT, '->', PORT['ug2'], 'solids', len(out))
for n in [SLOT + '_KIT00_BODY_A', SLOT + '_BASE_A', SLOT + '_KIT00_FRONT_WINDOW_A']:
    for g in out[n]['groups']:
        print(n, g['tex'], g['mat'], len(g['pos']), len(g['tri']), g['stride'])
os.makedirs('texdump', exist_ok=True)
for t in tex:
    Image.fromarray(dxt.decode(t['data'], t['w'], t['h'], t['fmt'])).save('texdump/mw_%s.png' % t['name'])
