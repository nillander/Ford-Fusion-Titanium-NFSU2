import numpy as np
from PIL import Image
def look(az,el):
    az=np.radians(az);el=np.radians(el)
    # camera direction: from camera toward origin
    f=-np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
    up=np.array([0,0,1.])
    r=np.cross(f,up);r/=np.linalg.norm(r);u=np.cross(r,f)
    return np.stack([r,u,-f])  # rows: screen x, screen y, depth(toward camera)
def render(meshes,az=35,el=15,W=1200,H=700,scale=230,center=(0,0,0.55),light=(0.4,0.3,0.85),bg=(235,238,242),cull=False,ortho=True,flip_normals=True):
    R=look(az,el)
    zb=np.full((H,W),-1e9);img=np.zeros((H,W,3));img[:]=bg
    L=np.array(light);L/=np.linalg.norm(L)
    for m in meshes:
        P=(m['pos']-np.array(center))@R.T
        sx=W/2+P[:,0]*scale; sy=H/2-P[:,1]*scale; sz=P[:,2]
        tri=m['tri']; tex=m.get('tex'); col=np.array(m.get('color',(180,180,180)),float)
        uv=m.get('uv')
        # face normals for shading
        a=m['pos'][tri[:,0]];b=m['pos'][tri[:,1]];c=m['pos'][tri[:,2]]
        fn=np.cross(b-a,c-a); fn/= (np.linalg.norm(fn,axis=1,keepdims=True)+1e-12)
        vn=m.get('nrm')
        for t in range(len(tri)):
            i0,i1,i2=tri[t]
            x0,x1,x2=sx[i0],sx[i1],sx[i2];y0,y1,y2=sy[i0],sy[i1],sy[i2]
            area=(x1-x0)*(y2-y0)-(x2-x0)*(y1-y0)
            if abs(area)<1e-9: continue
            if cull and area>0: continue
            xmin=max(int(np.floor(min(x0,x1,x2))),0);xmax=min(int(np.ceil(max(x0,x1,x2))),W-1)
            ymin=max(int(np.floor(min(y0,y1,y2))),0);ymax=min(int(np.ceil(max(y0,y1,y2))),H-1)
            if xmin>xmax or ymin>ymax: continue
            X,Y=np.meshgrid(np.arange(xmin,xmax+1)+0.5,np.arange(ymin,ymax+1)+0.5)
            w0=((x1-X)*(y2-Y)-(x2-X)*(y1-Y))/area
            w1=((x2-X)*(y0-Y)-(x0-X)*(y2-Y))/area
            w2=1-w0-w1
            inside=(w0>=-1e-6)&(w1>=-1e-6)&(w2>=-1e-6)
            if not inside.any(): continue
            z=w0*sz[i0]+w1*sz[i1]+w2*sz[i2]
            sub=zb[ymin:ymax+1,xmin:xmax+1]
            upd=inside&(z>sub)
            if not upd.any(): continue
            if vn is not None:
                n=w0[upd,None]*vn[i0]+w1[upd,None]*vn[i1]+w2[upd,None]*vn[i2]
                n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
            else: n=np.repeat(fn[t][None],upd.sum(),0)
            vd=R[2]
            ndv=n@vd
            if flip_normals:
                n=np.where((ndv<0)[:,None],-n,n)
            sh=0.35+0.65*np.clip(n@L,0,1)
            if tex is not None and uv is not None:
                u=w0[upd]*uv[i0,0]+w1[upd]*uv[i1,0]+w2[upd]*uv[i2,0]
                v=w0[upd]*uv[i0,1]+w1[upd]*uv[i1,1]+w2[upd]*uv[i2,1]
                th,tw=tex.shape[:2]
                tx=(np.mod(u,1)*tw).astype(int).clip(0,tw-1); ty=(np.mod(v,1)*th).astype(int).clip(0,th-1)
                c=tex[ty,tx,:3].astype(float)
                if tex.shape[2]==4 and m.get('alphatest'):
                    keep=tex[ty,tx,3]>127
                    if not keep.all():
                        yy,xx=np.nonzero(upd); upd2=np.zeros_like(upd); upd2[yy[keep],xx[keep]]=True
                        c=c[keep];sh=sh[keep];z=z; upd=upd2
                        if not upd.any(): continue
            else: c=col[None]
            sub[upd]=z[upd]
            img[ymin:ymax+1,xmin:xmax+1][upd]=c*sh[:,None] if np.ndim(sh) else c*sh
    return Image.fromarray(img.clip(0,255).astype(np.uint8))
