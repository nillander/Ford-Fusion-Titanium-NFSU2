import struct
from ug2 import chunks
def jdlz(inp):
    assert inp[:4]==b'JDLZ',inp[:8]
    dlen,clen=struct.unpack_from('<II',inp,8)
    out=bytearray(dlen);ip=16;op=0;f1=1;f2=1
    n=len(inp)
    while ip<n and op<dlen:
        if f1==1: f1=inp[ip]|0x100;ip+=1
        if f2==1: f2=inp[ip]|0x100;ip+=1
        if f1&1:
            if f2&1:
                ln=(inp[ip+1]|((inp[ip]&0xF0)<<4))+3; t=(inp[ip]&0x0F)+1
            else:
                t=(inp[ip+1]|((inp[ip]&0xE0)<<3))+17; ln=(inp[ip]&0x1F)+3
            ip+=2
            for i in range(ln): out[op+i]=out[op+i-t]
            op+=ln; f2>>=1
        else:
            out[op]=inp[ip];op+=1;ip+=1
        f1>>=1
    return bytes(out)
def decomp(blob):
    m=blob[:4]
    if m==b'JDLZ': return jdlz(blob)
    if m==b'RAWW':
        return blob[16:16+struct.unpack_from('<I',blob,8)[0]]
    raise Exception('unknown '+repr(blob[:16]))
def parse(path):
    d=open(path,'rb').read()
    cl=chunks(d,0,len(d),0,[])
    info=None;tex=[]
    for depth,cid,p,sz in cl:
        s=p+8
        if cid==0x33310001: info=d[s:s+sz]
        if cid==0x33310003:
            for i in range(0,sz,24):
                h,off,lc,l,fl,_=struct.unpack_from('<6I',d,s+i)
                blob=d[off:off+lc]
                raw=decomp(blob) if blob[:4] in (b'JDLZ',b'RAWW') else None
                if raw is None:
                    print('blob',hex(h),off,lc,l,blob[:16]); continue
                assert len(raw)==l,(len(raw),l)
                ti=raw[-156:-32]; dd=raw[-32:]
                t=dict(hash=h,flags=fl,name=ti[12:36].split(b'\0')[0].decode('latin1'),info=ti,dds=dd,
                  w=struct.unpack_from('<H',ti,68)[0],h=struct.unpack_from('<H',ti,70)[0],size=struct.unpack_from('<I',ti,56)[0],
                  fmt=dd[20:24],mips=ti[78],clsh=struct.unpack_from('<I',ti,40)[0],alpha=ti[82:88])
                t['data']=raw[:t['size']]
                t['rawlen']=l; t['tail']=raw[t['size']:-156]
                tex.append(t)
    return info,tex
if __name__=='__main__':
    import sys
    info,tex=parse(sys.argv[1])
    print(info[4:32],info[32:96].split(b'\0')[0])
    for t in tex: print(f"{t['name']:24s} {t['hash']:08X} {t['w']}x{t['h']} {t['fmt']} mips{t['mips']} sz{t['size']} tail{len(t['tail'])} fl{t['flags']:x} cls{t['clsh']:08X} a{t['alpha'].hex()}")
