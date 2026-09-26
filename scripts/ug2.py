import struct, numpy as np
def chunks(d,start,end,depth=0,out=None):
    p=start
    while p+8<=end:
        cid,sz=struct.unpack_from('<II',d,p)
        out.append((depth,cid,p,sz))
        if cid&0x80000000: chunks(d,p+8,p+8+sz,depth+1,out)
        p+=8+sz
    return out
def al(p,a): return (p+a-1)&~(a-1)
def parse(path):
    d=open(path,'rb').read()
    cl=chunks(d,0,len(d),0,[])
    solids=[];cur=None;header=None
    for depth,cid,p,sz in cl:
        s=p+8;e=s+sz
        if cid==0x134002: header=d[s:e]
        elif cid==0x80134010: cur={'chunk':(p,sz),'sub':[]};solids.append(cur)
        if cur is None: continue
        if p>=cur['chunk'][0] and e<=cur['chunk'][0]+8+cur['chunk'][1] and cid!=0x80134010: cur['sub'].append((cid,p,sz))
        if cid==0x134011:
            q=al(s,16);cur['hdr_off']=q-s
            h=d[q:q+0xa0]
            cur['version']=h[12];cur['flags']=struct.unpack_from('<H',h,14)[0]
            cur['hash'],cur['npolys'],cur['nverts']=struct.unpack_from('<IHH',h,16)
            cur['counts']=tuple(h[24:28])
            cur['bmin']=struct.unpack_from('<3f',h,32);cur['bmax']=struct.unpack_from('<3f',h,48)
            cur['mat']=np.frombuffer(h[64:128],dtype='<f4').reshape(4,4)
            cur['tail']=h[128:160]
            cur['name']=d[q+164:e].split(b'\0')[0].decode()
            cur['hdr_raw']=d[q:e]
        elif cid==0x134012: cur['tex']=[struct.unpack_from('<I',d,s+i)[0] for i in range(0,sz,8)]
        elif cid==0x134013: cur['light']=[struct.unpack_from('<I',d,s+i)[0] for i in range(0,sz,8)]
        elif cid==0x13401A:
            q=al(s,16);cur['markers_raw']=d[q:e]
        elif cid==0x134900:
            q=al(s,16);cur['desc']=struct.unpack_from('<16I',d,q);cur['desc_raw']=d[q:e]
        elif cid==0x134B01:
            q=al(s,0x80);cur['vb']=d[q:e]
        elif cid==0x134B02:
            q=al(s,16);g=[]
            for i in range(q,e,60):
                if i+60>e:break
                bmin=struct.unpack_from('<3f',d,i);ln=struct.unpack_from('<I',d,i+12)[0]
                bmax=struct.unpack_from('<3f',d,i+16)
                ti,si,d1,d2,d3,d4,off,fl=struct.unpack_from('<8I',d,i+28)
                g.append(dict(bmin=bmin,len=ln,bmax=bmax,tex=ti,sh=si,d=(d1,d2,d3,d4),off=off,flags=fl,raw=d[i:i+60]))
            cur['groups']=g
        elif cid==0x134B03:
            q=al(s,16);cur['ib']=np.frombuffer(d[q:e][:(e-q)//2*2],dtype='<u2')
    return d,cl,header,solids
if __name__=='__main__':
    import sys
    d,cl,header,solids=parse(sys.argv[1])
    print('header',header.hex())
    from collections import Counter
    print(Counter(hex(c[1]) for c in cl))
    for s in solids:
        nv=s['desc'][13] if 'desc' in s else 0
        stride=len(s.get('vb',b''))/max(nv,1)
        print(f"{s['name']:32s} v{s['version']:x} fl{s['flags']:04x} {s['hash']:08X} P{s['npolys']} V{s['nverts']} c{s['counts']} tex{len(s.get('tex',[]))} lm{len(s.get('light',[]))} mk{len(s.get('markers_raw',b''))} grp{len(s.get('groups',[]))} stride{stride:.1f} ib{len(s.get('ib',[]))} b{tuple(round(x,2) for x in s['bmin'])}..{tuple(round(x,2) for x in s['bmax'])}")
