import numpy as np
def _565(v):
    v=v.astype(np.uint32)
    r=((v>>11)&31)*255/31; g=((v>>5)&63)*255/63; b=(v&31)*255/31
    return np.stack([r,g,b],-1)
def decode(data,w,h,fmt):
    fmt=fmt if isinstance(fmt,str) else fmt.decode('latin1')
    bw,bh_=max(w//4,1),max(h//4,1)
    if fmt=='DXT1': bs=8
    elif fmt in('DXT3','DXT5'): bs=16
    else: raise ValueError(fmt)
    b=np.frombuffer(data[:bw*bh_*bs],np.uint8).reshape(-1,bs)
    cb=b[:,-8:]
    c0=cb[:,0].astype(np.uint16)|(cb[:,1].astype(np.uint16)<<8); c1=cb[:,2].astype(np.uint16)|(cb[:,3].astype(np.uint16)<<8)
    p0=_565(c0);p1=_565(c1)
    four=(c0>c1)|(fmt!='DXT1')
    p2=np.where(four[:,None],(2*p0+p1)/3,(p0+p1)/2); p3=np.where(four[:,None],(p0+2*p1)/3,0)
    pal=np.stack([p0,p1,p2,p3],1)
    alpha_pal=np.ones((len(b),4))*255
    if fmt=='DXT1': alpha_pal[:,3]=np.where(four,255,0)
    code=cb[:,4].astype(np.uint32)|(cb[:,5].astype(np.uint32)<<8)|(cb[:,6].astype(np.uint32)<<16)|(cb[:,7].astype(np.uint32)<<24)
    idx=np.stack([(code>>(2*k))&3 for k in range(16)],1)
    rgb=np.take_along_axis(pal,idx[:,:,None].repeat(3,2),1)
    a=np.take_along_axis(alpha_pal,idx,1)
    if fmt=='DXT3':
        ab=b[:,:8]; a=np.stack([((ab[:,k//2]>>(4*(k%2)))&15)*17 for k in range(16)],1).astype(float)
    if fmt=='DXT5':
        a0=b[:,0].astype(float);a1=b[:,1].astype(float)
        bits=np.zeros(len(b),np.uint64)
        for k in range(6): bits|=b[:,2+k].astype(np.uint64)<<np.uint64(8*k)
        ai=np.stack([(bits>>np.uint64(3*k))&np.uint64(7) for k in range(16)],1).astype(int)
        apal=np.zeros((len(b),8))
        apal[:,0]=a0;apal[:,1]=a1
        big=a0>a1
        for k in range(2,8): apal[:,k]=np.where(big,((8-k)*a0+(k-1)*a1)/7, ((6-k)*a0+(k-1)*a1)/5 if k<6 else 0)
        apal[:,7]=np.where(big,apal[:,7],255)
        a=np.take_along_axis(apal,ai,1)
    img=np.concatenate([rgb,a[:,:,None]],2).reshape(bh_,bw,4,4,4).transpose(0,2,1,3,4).reshape(bh_*4,bw*4,4)
    return np.clip(img,0,255).astype(np.uint8)[:h,:w]
