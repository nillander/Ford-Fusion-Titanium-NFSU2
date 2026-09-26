import numpy as np
def _565(c):
    c=np.clip(np.round(c),0,255).astype(np.int32)
    return ((c[...,0]>>3)<<11)|((c[...,1]>>2)<<5)|(c[...,2]>>3)
def _from565(v):
    r=((v>>11)&31)*255/31; g=((v>>5)&63)*255/63; b=(v&31)*255/31
    return np.stack([r,g,b],-1).astype(np.float32)
def _color_blocks(rgb):
    mean=rgb.mean(1,keepdims=True); d=rgb-mean
    cov=np.einsum('bki,bkj->bij',d,d)
    axis=np.ones((len(rgb),3),np.float32)
    for _ in range(6):
        axis=np.einsum('bij,bj->bi',cov,axis); axis/=np.linalg.norm(axis,axis=1,keepdims=True)+1e-9
    proj=np.einsum('bki,bi->bk',d,axis)
    c0=mean[:,0]+axis*proj.max(1,keepdims=True); c1=mean[:,0]+axis*proj.min(1,keepdims=True)
    e0=_565(c0); e1=_565(c1)
    swap=e0<e1; e0,e1=np.where(swap,e1,e0),np.where(swap,e0,e1)
    p0=_from565(e0); p1=_from565(e1)
    pal=np.stack([p0,p1,(2*p0+p1)/3,(p0+2*p1)/3],1)
    dist=((rgb[:,:,None,:]-pal[:,None,:,:])**2).sum(-1); idx=dist.argmin(-1).astype(np.uint32)
    idx[e0==e1]=0
    code=np.zeros(len(rgb),np.uint32)
    for k in range(16): code|=idx[:,k]<<(2*k)
    out=np.zeros((len(rgb),8),np.uint8)
    out[:,0:2]=e0.astype('<u2').view(np.uint8).reshape(-1,2)
    out[:,2:4]=e1.astype('<u2').view(np.uint8).reshape(-1,2)
    out[:,4:8]=code.astype('<u4').view(np.uint8).reshape(-1,4)
    return out
def _blocks(rgba):
    H,W,_=rgba.shape
    return rgba.astype(np.float32).reshape(H//4,4,W//4,4,4).transpose(0,2,1,3,4).reshape(-1,16,4)
def encode_dxt1(rgba):
    b=_blocks(rgba); return _color_blocks(b[...,:3]).tobytes()
def encode_dxt3(rgba):
    b=_blocks(rgba); col=_color_blocks(b[...,:3])
    a4=np.clip(np.round(b[...,3]/17),0,15).astype(np.uint64)
    bits=np.zeros(len(b),np.uint64)
    for k in range(16): bits|=a4[:,k]<<np.uint64(4*k)
    return np.concatenate([bits.astype('<u8').view(np.uint8).reshape(-1,8),col],1).tobytes()
