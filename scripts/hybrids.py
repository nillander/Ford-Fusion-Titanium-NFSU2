import ug2, ug2write, tpk2, tpkwrite, numpy as np, os
from hashes import bh
def solids_of(path):
    d,cl,h,S=ug2.parse(path); out={}
    for s in S:
        raw=np.frombuffer(s['vb'],np.uint8).reshape(-1,36)
        mk=[];m=s.get('markers_raw',b'')
        for i in range(0,len(m),80): mk.append((int.from_bytes(m[i:i+4],'little'),np.frombuffer(m[i+16:i+80],'<f4').reshape(4,4)))
        out[s['name']]=dict(name=s['name'],tex=s['tex'],light=s['light'],pos=raw[:,0:12].copy().view('<f4').reshape(-1,3),
            nrm=raw[:,12:24].copy().view('<f4').reshape(-1,3),col=raw[:,24:28].copy().view('<u4').ravel(),uv=raw[:,28:36].copy().view('<f4').reshape(-1,2),
            groups=[dict(tex_i=g['tex'],sh_i=g['sh'],tri=s['ib'][g['off']:g['off']+g['len']].reshape(-1,3)) for g in s['groups']],markers=mk)
    return out
E=solids_of('escort/GEOMETRY.BIN'); F=solids_of('out3/GEOMETRY.BIN')
os.makedirs('hib',exist_ok=True)
tests={'H1_base':['FOCUS_BASE_A'],'H2_body':['FOCUS_KIT00_BODY_A'],'H3_roda':['FOCUS_KIT00_FRONT_WHEEL_A']}
for name,swap in tests.items():
    sol=[F[n] if n in swap else E[n] for n in E]
    os.makedirs(f'hib/{name}',exist_ok=True); ug2write.write(sol,f'hib/{name}/GEOMETRY.BIN')
# union TPK: Escort + Fusion textures
ie,te=tpk2.parse('escort/TEXTURES.BIN'); iF,tF=tpk2.parse('out3/TEXTURES.BIN')
U={t['hash']:dict(hash=t['hash'],info=t['info'],dds=t['dds'],data=t['data'],tail=t['tail']) for t in te}
for t in tF: U.setdefault(t['hash'],dict(hash=t['hash'],info=t['info'],dds=t['dds'],data=t['data'],tail=t['tail']))
tpkwrite.write_raw(list(U.values()),'hib/TEXTURES_uniao.BIN')
print(len(U))
