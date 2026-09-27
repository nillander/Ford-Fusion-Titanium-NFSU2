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
open('hdr.bin','wb').write(hdr)
# --- extract the two files of FOCUS.7z (one LZMA folder: GEOMETRY.BIN then TEXTURES.BIN) into escort/
p = 2; assert hdr[p] == 6; p += 1
packpos, p = num(hdr, p); n, p = num(hdr, p); p += 1; psize, p = num(hdr, p)
i = hdr.index(bytes([0x5d, 0, 0, 0x30, 0])); props2 = hdr[i:i + 5]; p = i + 5; assert hdr[p] == 0xc; p += 1
usize2, p = num(hdr, p)
data = lzma_dec(d[32 + packpos:32 + packpos + psize], props2, usize2)
j = hdr.index(bytes([8, 0xd, 2, 9])) + 4; s1, j = num(hdr, j)
os.makedirs('escort', exist_ok=True)
open('escort/GEOMETRY.BIN', 'wb').write(data[:s1]); open('escort/TEXTURES.BIN', 'wb').write(data[s1:])
print('escort/GEOMETRY.BIN', s1, 'escort/TEXTURES.BIN', len(data) - s1)
