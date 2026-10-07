"""Export geometry to Wavefront OBJ (positions, normals, UVs, one group per part/material) to try other tools
such as NFS-CarToolkit. Usage:
  export_obj.py ug2 GEOMETRY.BIN out.obj          # compiled UG2 file, A parts
  export_obj.py mw mw_parts.pkl PREFIX out.obj    # MW source parts whose name starts with PREFIX"""
import sys, pickle, numpy as np


def write(groups, path):
    with open(path, 'w') as f:
        o = 1
        for name, pos, nrm, uv, tri in groups:
            f.write('g %s\n' % name)
            for p in pos: f.write('v %.6f %.6f %.6f\n' % tuple(p))
            for t in uv: f.write('vt %.6f %.6f\n' % (t[0], 1 - t[1]))
            for n in nrm: f.write('vn %.6f %.6f %.6f\n' % tuple(n))
            for a, b, c in tri + o:
                f.write('f %d/%d/%d %d/%d/%d %d/%d/%d\n' % (a, a, a, b, b, b, c, c, c))
            o += len(pos)
    print(path, sum(len(g[4]) for g in groups), 'triangles')


if sys.argv[1] == 'ug2':
    import ug2
    out = []
    for s in ug2.parse(sys.argv[2])[3]:
        if not s['name'].endswith('_A') or 'DECAL' in s['name'] or 'KITW' in s['name']:
            continue
        raw = np.frombuffer(s['vb'], np.uint8).reshape(-1, 36)
        pos = raw[:, :12].copy().view('<f4').reshape(-1, 3); nrm = raw[:, 12:24].copy().view('<f4').reshape(-1, 3)
        uv = raw[:, 28:36].copy().view('<f4').reshape(-1, 2)
        for k, g in enumerate(s['groups']):
            tri = s['ib'][g['off']:g['off'] + g['len']].reshape(-1, 3).astype(int)
            used = np.unique(tri); remap = np.full(len(pos), -1); remap[used] = np.arange(len(used))
            out.append(('%s_%d_%08X' % (s['name'], k, s['tex'][g['tex']]), pos[used], nrm[used], uv[used], remap[tri]))
    write(out, sys.argv[3])
else:
    P = pickle.load(open(sys.argv[2], 'rb'))
    out = []
    for name in sorted(P):
        if not name.startswith(sys.argv[3]):
            continue
        for k, g in enumerate(P[name]['groups']):
            out.append(('%s_%d_%s' % (name, k, g['mat']), g['pos'], g['nrm'], g['uv'], np.asarray(g['tri'])))
    write(out, sys.argv[4])
