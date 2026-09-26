import struct,lzma,sys,os
def num(b,p):
    f=b[p];p+=1;mask=0x80;val=0
    for i in range(8):
        if f&mask==0:
            hi=f&(mask-1); val|=hi<<(8*i); return val,p
        val|=b[p]<<(8*i);p+=1;mask>>=1
    return val,p
def lzma_dec(data,props,size):
    lc_lp_pb=props[0];dict_size=struct.unpack('<I',props[1:5])[0]
    pb=lc_lp_pb//45;r=lc_lp_pb%45;lp=r//9;lc=r%9
    f=[{'id':lzma.FILTER_LZMA1,'dict_size':dict_size,'lc':lc,'lp':lp,'pb':pb}]
    dec=lzma.LZMADecompressor(lzma.FORMAT_RAW,filters=f)
    return dec.decompress(data,max_length=size)
d=open(sys.argv[1],'rb').read()
nho,nhs,crc=struct.unpack_from('<QQI',d,12)
h=d[32+nho:32+nho+nhs]
p=1
assert h[p]==6;p+=1
packpos,p=num(h,p);n,p=num(h,p);assert h[p]==9;p+=1;psize,p=num(h,p);p+=1
# unpackinfo
assert h[p]==7;p+=1;assert h[p]==0xb;p+=1;nf,p=num(h,p);p+=1;nc,p=num(h,p);flag=h[p];p+=1
cid=h[p:p+(flag&15)];p+=flag&15;ps,p=num(h,p);props=h[p:p+ps];p+=ps
assert h[p]==0xc;p+=1;usize,p=num(h,p)
hdr=lzma_dec(d[32+packpos:32+packpos+psize],props,usize)
print(hdr.hex())
open('/tmp/hdr.bin','wb').write(hdr)
