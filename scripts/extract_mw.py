import mwgeo, tpk2, pickle, numpy as np
from hashes import bh
S=mwgeo.parse('mw/CARS/MUSTANGGT/GEOMETRY.BIN')
info,tex=tpk2.parse('mw/CARS/MUSTANGGT/TEXTURES.BIN')
names={t['hash']:t['name'] for t in tex}
cand='CARSKIN WINDSHIELD WINDOW_FRONT WINDOW_REAR WINDOW_LEFT_FRONT WINDOW_RIGHT_FRONT WINDOW_LEFT_REAR WINDOW_RIGHT_REAR DULLPLASTIC INTERIOR LICENSEPLATE RUBBER HEADLIGHTGLASS HEADLIGHT BRAKELIGHT DRIVER BRAKEDISC CALIPER CHROME MAGSILVER'.split()
for c in cand: names.setdefault(bh(c),c)
out={}
for s in S:
    parts=[]
    for g,vb,stride,idx,k in mwgeo.meshes(s):
        pos,nrm,col,uv=mwgeo.vert_arrays(vb,stride)
        tri=idx.reshape(-1,3)
        used=np.unique(tri)
        remap=np.full(len(pos),-1,np.int64); remap[used]=np.arange(len(used))
        parts.append(dict(tex=names.get(s['tex'][g['ids'][0]],'%08X'%s['tex'][g['ids'][0]]),
            mat=names.get(s['light'][g['ids'][5]],'%08X'%s['light'][g['ids'][5]]) if s.get('light') else None,
            pos=pos[used].astype(np.float64),nrm=nrm[used].astype(np.float64),col=col[used],uv=uv[used].astype(np.float64),tri=remap[tri],stride=stride))
    out[s['name']]=dict(groups=parts,mat=s['mat'],markers=s.get('markers_raw',b''),bmin=s['bmin'],bmax=s['bmax'])
pickle.dump(out,open('mw_parts.pkl','wb'))
for n in ['MUSTANGGT_KIT00_BODY_A','MUSTANGGT_BASE_A','MUSTANGGT_KIT00_FRONT_WINDOW_A']:
    for g in out[n]['groups']: print(n,g['tex'],g['mat'],len(g['pos']),len(g['tri']),g['stride'])
