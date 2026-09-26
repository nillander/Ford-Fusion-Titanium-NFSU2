import struct, numpy as np
from ug2 import chunks, al
EFF=['WorldShader','WorldReflectShader','WorldBoneShader','WorldNormalMap','CarShader','GlossyWindow','billboardshader']
def parse(path):
    d=open(path,'rb').read()
    cl=chunks(d,0,len(d),0,[])
    solids=[];cur=None
    for depth,cid,p,sz in cl:
        s=p+8;e=s+sz
        if cid==0x80134010: cur={'vbs':[],'names':[]};solids.append(cur);continue
        if cur is None: continue
        if cid==0x134011:
            q=al(s,16);h=d[q:e]
            cur['hash']=struct.unpack_from('<I',h,16)[0]
            cur['bmin']=struct.unpack_from('<3f',h,32);cur['bmax']=struct.unpack_from('<3f',h,48)
            cur['mat']=np.frombuffer(h[64:128],'<f4').reshape(4,4)
            cur['name']=h[160:].split(b'\0')[0].decode('latin1')
        elif cid==0x134012: cur['tex']=[struct.unpack_from('<I',d,s+i)[0] for i in range(0,sz,8)]
        elif cid==0x134013: cur['light']=[struct.unpack_from('<I',d,s+i)[0] for i in range(0,sz,8)]
        elif cid==0x13401A: q=al(s,16);cur['markers_raw']=d[q:e]
        elif cid==0x134900: q=al(s,16);cur['desc']=struct.unpack_from('<11I',d,q)
        elif cid==0x134B01: q=al(s,0x80);cur['vbs'].append(d[q:e])
        elif cid==0x134B02:
            q=al(s,16);g=[]
            n=(e-q)//104
            for i in range(n):
                o=q+i*104
                bmin=struct.unpack_from('<3f',d,o);bmax=struct.unpack_from('<3f',d,o+12)
                ids=d[o+24:o+30]
                eff,effp,fl,nv,nt=struct.unpack_from('<5I',d,o+0x30)
                rest=struct.unpack_from('<9I',d,o+0x44)
                g.append(dict(bmin=bmin,bmax=bmax,ids=tuple(ids),eff=eff,flags=fl,nv=nv,nt=nt,rest=rest))
            cur['groups']=g
        elif cid==0x134B03: q=al(s,16);cur['ib']=np.frombuffer(d[q:e][:(e-q)//2*2],'<u2')
        elif cid==0x134C02 and sz>0: cur['names'].append(d[s:e].split(b'\0')[0].decode('latin1'))
    return solids
def meshes(s):
    """yield per group: (group, verts structured array, local tri indices into that array)"""
    gs=s.get('groups',[])
    if not gs: return []
    stream=[];si=0;last=None
    for j,g in enumerate(gs):
        if j>0 and g['eff']!=last: si+=1
        stream.append(si);last=g['eff']
    counts=[0]*(si+1)
    for g,k in zip(gs,stream): counts[k]+=g['nv']
    if len(s['vbs'])==1 and si==0: counts=[None]
    out=[];ioff=0;voff=[0]*(si+1)
    arrs=[]
    for k,vb in enumerate(s['vbs']):
        c=counts[k] if counts[k] else None
        arrs.append(vb)
    for g,k in zip(gs,stream):
        vb=s['vbs'][k]
        tot=sum(gg['nv'] for gg,kk in zip(gs,stream) if kk==k)
        stride=len(vb)//tot
        ni=g['nt']*3
        idx=s['ib'][ioff:ioff+ni].astype(np.int64);ioff+=ni
        out.append((g,vb,stride,idx,k))
    return out
def vert_arrays(vb,stride):
    raw=np.frombuffer(vb,np.uint8).reshape(-1,stride)
    pos=raw[:,0:12].copy().view('<f4').reshape(-1,3)
    nrm=raw[:,12:24].copy().view('<f4').reshape(-1,3)
    col=raw[:,24:28].copy().view('<u4').reshape(-1)
    uv=raw[:,28:36].copy().view('<f4').reshape(-1,2)
    return pos,nrm,col,uv
if __name__=='__main__':
    import sys
    S=parse(sys.argv[1])
    tot=0
    for s in S:
        gs=s.get('groups',[])
        nv=sum(g['nv'] for g in gs); nt=sum(g['nt'] for g in gs)
        strides=[len(v) for v in s['vbs']]
        print(f"{s['name']:42s} nv{nv:6d} nt{nt:6d} grp{len(gs):2d} vbs{len(s['vbs'])} effs{sorted(set(g['eff'] for g in gs))} ib{len(s.get('ib',[]))} mk{len(s.get('markers_raw',b''))//80}")
