"""Figure 6: torsion geometry with dimensions and boundary conditions, the
torque-rotation response, damage at six selected increments and three views of
the final damage field.

Geometry, scalar damage and torque are read from saved numerical arrays. All
damage panels share the turbo colour map, limits and display threshold of
Figure 5 (d >= 0.95 on a 0.95-1.00 scale) and use undeformed coordinates. Display coordinates are a proper rotation of the model axes
(no mirroring), so the notch inclination and twist sense are preserved.
"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from scipy.io import loadmat
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.patches import Rectangle, Polygon, FancyArrowPatch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT = Path(__file__).resolve().parents[1]
STEPS = (21,41,61,69,80,100,120,140)  # increments stored in the state cache
SHOW = (41,61,69,80,100,140)  # increments drawn in panels (f-k)
LETTERS = 'efghij'
PEAK = 69
THETA_END, N_INC = .003, 140
DMIN = .95  # same colour map, limits and threshold as Figure 5
CMAP = plt.get_cmap('turbo')
NORM = Normalize(DMIN,1)
ELEV, AZIM = 24, -122  # camera on the rotated-end, +z, notched-face side
FIXED, LOADED, DIM, EDGE = '#2f5d7c', '#c65b38', '#222222', '#3b4650'


# ---------------------------------------------------------------- geometry
def boundary(t):
    faces = np.concatenate([t[:, ids] for ids in ([0,1,2],[0,1,3],[0,2,3],[1,2,3])])
    owners = np.tile(np.arange(len(t)),4)
    unique,index,count = np.unique(np.sort(faces,axis=1),axis=0,return_index=True,return_counts=True)
    mask = count==1
    return unique[mask],owners[index[mask]]


def local(p):
    """Model (x,y,z) -> local (X,Y,Z) in mm: X from the rotated end (x = min),
    Y from the unnotched face, Z across the width."""
    return p-p.min(axis=0)


def plot_xyz(q):
    """Local (X,Y,Z) -> 3D plot axes. (X,-Z,Y) is a proper rotation, so the
    image is not mirrored. Y (notched face up) becomes the vertical axis."""
    q = np.atleast_2d(q)
    return np.column_stack([q[:,0],100-q[:,2],q[:,1]])


def notch_from_mesh(q,faces):
    """Notch slot measured from the boundary faces that are not on the box."""
    lo,hi = q.min(axis=0),q.max(axis=0)
    on = np.zeros(len(faces),bool)
    for a in range(3):
        for v in (lo[a],hi[a]): on |= np.all(np.isclose(q[faces,a],v),axis=1)
    n = q[np.unique(faces[~on])]
    z0,z1 = n[:,2].min(),n[:,2].max()
    def x_at(z):
        s = n[np.isclose(n[:,2],z),0];return float(s.min()),float(s.max())
    return {'bottom_Y':float(n[:,1].min()),'top_Y':float(hi[1]),'x_z0':x_at(z0),'x_z1':x_at(z1),'z':(float(z0),float(z1))}


def box_edges(L=400,H=100,W=100):
    c = np.array([[x,y,z] for x in (0,L) for y in (0,H) for z in (0,W)],float)
    return [(c[i],c[j]) for i in range(8) for j in range(i+1,8) if np.sum(c[i]!=c[j])==1]


def split_box_edges(elev,azim,L=400,H=100,W=100):
    """Visible and hidden box edges for an orthographic camera. An edge is
    visible when either face meeting there faces the viewer."""
    el,az = np.radians(elev),np.radians(azim)
    e = np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
    eye = np.array([e[0],e[2],-e[1]])  # plot (X,100-Z,Y) -> local (X,Y,Z)
    size = np.array([L,H,W],float);seen,hidden = [],[]
    for u,v in box_edges(L,H,W):
        normals = [np.sign(u[a]-size[a]/2)*np.eye(3)[a] for a in range(3) if u[a]==v[a]]
        (seen if any(n@eye>1e-6 for n in normals) else hidden).append((u,v))
    return seen,hidden


def notch_edges(nt):
    (a0,b0),(a1,b1) = nt['x_z0'],nt['x_z1'];z0,z1 = nt['z'];yb,yt = nt['bottom_Y'],nt['top_Y']
    e = []
    for y in (yb,yt):
        e += [((a0,y,z0),(a1,y,z1)),((b0,y,z0),(b1,y,z1))]
    for x,z in ((a0,z0),(b0,z0),(a1,z1),(b1,z1)):
        e.append(((x,yb,z),(x,yt,z)))
    e += [((a0,yb,z0),(b0,yb,z0)),((a1,yb,z1),(b1,yb,z1))]
    return [(np.array(u,float),np.array(v,float)) for u,v in e]


# ---------------------------------------------------------------- 3D helpers
def camera(ax,elev=24,azim=-60,zoom=1.0,pad=(14,14,14)):
    ax.set(xlim=(-pad[0],400+pad[0]),ylim=(-pad[1],100+pad[1]),zlim=(-pad[2],100+pad[2]))
    ax.set_box_aspect((400+2*pad[0],100+2*pad[1],100+2*pad[2]),zoom=zoom)
    ax.view_init(elev=elev,azim=azim)
    ax.set_proj_type('ortho');ax.set_axis_off()
    ax.set_facecolor((1,1,1,0))  # neighbouring 3D panels must not paint over each other


def add_faces(ax,v,faces,**kw):
    # 3D axes clip to a square region; the long beam must not be cut at its ends.
    art = Poly3DCollection(v[faces],**kw);art.set_rasterized(True);art.set_clip_on(False)
    ax.add_collection3d(art);return art


def lines3d(ax,edges,**kw):
    for u,v in edges:
        P = plot_xyz(np.array([u,v]));ax.plot(P[:,0],P[:,1],P[:,2],clip_on=False,**kw)


def dim3d(ax,a,b,text,offset,tick=4.5):
    """Dimension line between local points a and b, shifted by a local offset,
    with extension lines and end ticks."""
    a,b,o = (np.asarray(v,float) for v in (a,b,offset))
    u = o/np.linalg.norm(o)
    lines3d(ax,[(a+u*2,a+o+u*3),(b+u*2,b+o+u*3)],color='#777777',lw=.45)
    lines3d(ax,[(a+o,b+o)],color=DIM,lw=.7)
    s = (b-a)/np.linalg.norm(b-a)
    for e in (a+o,b+o):
        lines3d(ax,[(e-(u+s)*tick*.7,e+(u+s)*tick*.7)],color=DIM,lw=.8)
    m = plot_xyz((a+b)/2+o*1.6)[0]
    ax.text(m[0],m[1],m[2],text,fontsize=7.5,ha='center',va='center',color=DIM,zorder=10,
            bbox=dict(fc='white',ec='none',pad=.4,alpha=.85))


def rotation_arrow3d(ax,X,radius,a0=-.9,a1=1.15,color=LOADED):
    """Positive rotation about +x, drawn around the beam axis in the plane X."""
    a = np.linspace(a0,a1,60)
    q = np.column_stack([np.full_like(a,X),50+radius*np.cos(a),50+radius*np.sin(a)])
    P = plot_xyz(q);ax.plot(P[:,0],P[:,1],P[:,2],color=color,lw=1.6,zorder=9)
    d = P[-1]-P[-5]
    ax.quiver(P[-1,0],P[-1,1],P[-1,2],d[0],d[1],d[2],length=12,normalize=True,color=color,
              arrow_length_ratio=1.0,lw=1.6,zorder=9)


def label(ax,text,x=0.,y=1.,**kw):
    put = ax.text2D if hasattr(ax,'text2D') else ax.text
    put(x,y,text,transform=ax.transAxes,fontsize=8.5,weight='bold',va='top',ha='left',**kw)


# ---------------------------------------------------------------- panels
def geometry3d(ax,q,faces,nt):
    camera(ax,elev=ELEV,azim=AZIM,zoom=1.0,pad=(60,22,30))
    v = plot_xyz(q)
    # One collection, so end faces are depth-sorted with the rest of the mesh.
    colour = np.tile(matplotlib.colors.to_rgba('#e3eaef'),(len(faces),1))
    for end,c in ((0.,LOADED),(400.,FIXED)):
        colour[np.all(np.isclose(q[faces,0],end),axis=1)] = matplotlib.colors.to_rgba(c)
    add_faces(ax,v,faces,facecolors=colour,edgecolors='#9aa9b3',linewidths=.04)
    seen,_ = split_box_edges(ELEV,AZIM)
    lines3d(ax,seen,color=EDGE,lw=.6)
    lines3d(ax,notch_edges(nt),color=EDGE,lw=.55)
    # clamp hatching on the visible edges of the (hidden) fixed end face
    for a,b in (((400,0,100),(400,100,100)),((400,100,0),(400,100,100))):
        a,b = np.array(a,float),np.array(b,float);lines3d(ax,[(a,b)],color=FIXED,lw=1.8)
        for s in np.linspace(.06,1,9):
            p = a+s*(b-a);lines3d(ax,[(p,p+np.array([12.,0,0])-(b-a)/np.linalg.norm(b-a)*7)],color=FIXED,lw=.6)
    dim3d(ax,(0,0,100),(400,0,100),'400',(0,-18,0))
    dim3d(ax,(400,0,100),(400,100,100),'100',(30,0,0))
    dim3d(ax,(400,100,0),(400,100,100),'100',(30,0,0))
    A = plot_xyz(np.array([[-34,50,50],[434,50,50]]))
    ax.plot(A[:,0],A[:,1],A[:,2],color='#555555',lw=.6,ls=(0,(6,2,1,2)),zorder=8)
    rotation_arrow3d(ax,-24,66)
    t = plot_xyz((-24,134,50))[0]
    ax.text(t[0],t[1],t[2],r'$\theta$',color=LOADED,fontsize=11,ha='center',zorder=10)
    ax.text2D(.01,.80,'Rotated end\n$u_x=0$, rigid twist\n$\\theta$ about beam axis',transform=ax.transAxes,color=LOADED,fontsize=7.2,weight='bold',va='top')
    ax.text2D(.99,.30,'Fixed end\n$u_x=u_y=u_z=0$',transform=ax.transAxes,color=FIXED,fontsize=7.2,weight='bold',va='top',ha='right')


def dim2d(ax,a,b,text,off,fs=7,rot=None):
    a,b,o = np.asarray(a,float),np.asarray(b,float),np.asarray(off,float)
    u = o/np.linalg.norm(o)
    for p in (a,b): ax.plot(*zip(p+u*1.5,p+o+u*3),color='#777777',lw=.45)
    ax.add_patch(FancyArrowPatch(a+o,b+o,arrowstyle='<|-|>',mutation_scale=5,lw=.6,color=DIM,shrinkA=0,shrinkB=0))
    m = (a+b)/2+o
    if rot is None: rot = 90 if abs(b[0]-a[0])<1e-9 else 0
    ax.text(*m,text,fontsize=fs,ha='center',va='center',rotation=rot,color=DIM,bbox=dict(fc='white',ec='none',pad=.3))


def wall(ax,x,y0,y1,n=8):
    ax.plot([x,x],[y0,y1],color=FIXED,lw=1.8,solid_capstyle='butt')
    for y in np.linspace(y0+6,y1,n):
        ax.plot([x,x+7],[y,y-7],color=FIXED,lw=.6)


def axes_key(ax,o,h,v,L=22):
    o = np.asarray(o,float)
    for d,s in (((L,0),h),((0,L),v)):
        ax.add_patch(FancyArrowPatch(o,o+d,arrowstyle='-|>',mutation_scale=5,lw=.6,color='#333333'))
        ax.text(*(o+np.array(d)*1.35),'$%s$'%s,fontsize=6.5,ha='center',va='center')


def view_setup(ax,xl,yl):
    ax.set_xlim(*xl);ax.set_ylim(*yl);ax.set_aspect('equal');ax.set_axis_off()


def plan_view(ax,nt):
    """View from +y onto the notched face: right = x, up = -z."""
    (a0,b0),(a1,b1) = nt['x_z0'],nt['x_z1']
    ax.add_patch(Rectangle((0,0),400,100,fc='#eef2f5',ec=EDGE,lw=.8))
    ax.add_patch(Polygon([(a0,100),(b0,100),(b1,0),(a1,0)],fc='#9aa4ab',ec=EDGE,lw=.6))
    wall(ax,400,0,100);ax.plot([0,0],[0,100],color=LOADED,lw=1.8)
    dim2d(ax,(0,100),(400,100),'400',(0,14))
    dim2d(ax,(0,0),(0,100),'100',(-14,0))
    ax.plot([(a0+b1)/2]*2,[50,-14],color='#777777',lw=.45,ls=(0,(6,2,1,2)))
    dim2d(ax,(0,50),((a0+b1)/2,50),'%.0f'%((a0+b1)/2),(0,-63))
    p = np.array([b0,100.]);ax.plot([p[0],p[0]+48],[100,100],color='#777777',lw=.45,ls='--')
    ang = np.linspace(-np.pi/4,0,24);ax.plot(p[0]+34*np.cos(ang),p[1]+34*np.sin(ang),color=DIM,lw=.6)
    ax.text(p[0]+40,p[1]-17,'45$^\\circ$',fontsize=7)
    ax.annotate('notch, 5 wide',((a0+a1)/2+40,50),xytext=(70,30),fontsize=6.5,ha='center',
                arrowprops=dict(arrowstyle='-',lw=.5,color='#444444'))
    axes_key(ax,(-46,-30),'x','-z',L=18)
    view_setup(ax,(-60,430),(-36,124))


def elevation_view(ax,nt):
    """View from +z: right = x, up = y. Near-face notch solid, far-face dashed."""
    (a0,b0),(a1,b1) = nt['x_z0'],nt['x_z1'];yb = nt['bottom_Y']
    ax.add_patch(Polygon([(0,0),(400,0),(400,100),(b1,100),(b1,yb),(a1,yb),(a1,100),(0,100)],fc='#eef2f5',ec=EDGE,lw=.8))
    for x in (a0,b0): ax.plot([x,x],[yb,100],color=EDGE,lw=.5,ls=(0,(3,2)))
    ax.plot([a0,a1],[yb,yb],color=EDGE,lw=.5,ls=(0,(3,2)))
    wall(ax,400,0,100);ax.plot([0,0],[0,100],color=LOADED,lw=1.8)
    ax.plot([-12,412],[50,50],color='#555555',lw=.5,ls=(0,(6,2,1,2)))
    dim2d(ax,(b1,100),(b1,yb),'50',(18,0))
    dim2d(ax,(0,0),(400,0),'400',(0,-13))
    dim2d(ax,(0,0),(0,100),'100',(-14,0))
    ax.text(290,54,'beam axis',fontsize=6.3,color='#555555')
    axes_key(ax,(-46,-30),'x','y',L=18)
    view_setup(ax,(-60,430),(-36,118))


def end_view(ax):
    """Rotated end seen from -x: right = z, up = y. Positive theta about +x
    appears clockwise from this side."""
    ax.add_patch(Rectangle((0,0),100,100,fc='#f6e1d8',ec=LOADED,lw=1.2))
    ax.plot(50,50,marker='o',ms=6,mfc='white',mec='#333333',mew=.8)
    ax.plot(50,50,marker='x',ms=3.6,mec='#333333',mew=.8)
    a = np.linspace(np.pi*.92,np.pi*.12,60);r = 32
    ax.plot(50+r*np.cos(a),50+r*np.sin(a),color=LOADED,lw=1.4)
    ax.add_patch(FancyArrowPatch((50+r*np.cos(a[-5]),50+r*np.sin(a[-5])),(50+r*np.cos(a[-1]),50+r*np.sin(a[-1])),
                                 arrowstyle='-|>',mutation_scale=9,color=LOADED,lw=1.4))
    ax.text(20,74,r'$\theta$',ha='center',fontsize=10,color=LOADED)
    for (y,z) in ((96,50),(4,50),(50,96),(50,4)):
        uy,uz = -(z-50),(y-50);n = np.hypot(uy,uz)
        ax.add_patch(FancyArrowPatch((z,y),(z+13*uz/n,y+13*uy/n),arrowstyle='-|>',mutation_scale=6,color='#7a3a26',lw=.8))
    ax.text(57,40,'$(y_c,z_c)$',fontsize=6.3)
    ax.text(50,-10,'$u_y=-\\theta\\,(z-z_c)$\n$u_z=\\theta\\,(y-y_c)$\n$\\theta: 0\\rightarrow0.003$ rad',ha='center',va='top',fontsize=6.6)
    axes_key(ax,(-24,-30),'z','y',L=15)
    view_setup(ax,(-30,122),(-58,122))


def torque_panel(ax,curve):
    th = curve['theta_rad']*1e3;T = curve['Torque_Nmm']/1e6
    ax.plot(th,T,color='#2b5d8a',lw=1.3,zorder=2)
    for s,letter in zip(SHOW,LETTERS):
        i = s-1;peak = s==PEAK
        ax.plot(th[i],T[i],'o',ms=5.5 if peak else 4,mfc=LOADED if peak else 'white',mec=LOADED if peak else '#2b5d8a',mew=1,zorder=3)
        ax.annotate(letter,(th[i],T[i]),xytext=(0,5),textcoords='offset points',ha='center',fontsize=6.5)
    i = int(np.argmax(T))
    ax.annotate('peak, inc. %d'%(i+1),(th[i],T[i]),xytext=(16,-16),textcoords='offset points',fontsize=6.8,color=LOADED,
                arrowprops=dict(arrowstyle='-',color=LOADED,lw=.5))
    ax.set_xlabel(r'End rotation $\theta$ [mrad]',fontsize=7.5,labelpad=1)
    ax.set_ylabel('Torque $T$ [kN m]',fontsize=7.5,labelpad=1)
    ax.set_xlim(0,3.05);ax.set_ylim(0,T.max()*1.22)
    ax.tick_params(labelsize=7,length=2.5,pad=1.5);ax.grid(alpha=.25,lw=.4)
    for s in ('top','right'): ax.spines[s].set_visible(False)
    return int(i+1)


def shaded(colours,v,faces,elev,azim,ambient=.72):
    """Mild Lambert shading with the light at the camera, so the damaged
    volume reads as a solid. Hue is kept and brightness changes by <= 28%."""
    el,az = np.radians(elev),np.radians(azim)
    light = np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)+.5])
    n = np.cross(v[faces[:,1]]-v[faces[:,0]],v[faces[:,2]]-v[faces[:,0]])
    cos = np.abs(n@light)/(np.linalg.norm(n,axis=1)*np.linalg.norm(light)+1e-30)
    out = colours.copy();out[:,:3] *= (ambient+(1-ambient)*cos)[:,None]
    return out


def damage_panel(ax,q,t,damage,text,nt,elev=ELEV,azim=AZIM,zoom=1.12):
    camera(ax,elev,azim,zoom,pad=(4,6,6))
    selected = np.flatnonzero(damage>=DMIN)
    if len(selected):
        surface,owners = boundary(t[selected]);values = damage[selected[owners]]
        assert len(values)==len(surface) and np.all((values>=DMIN)&(values<=1))
        v = plot_xyz(q)
        add_faces(ax,v,surface,facecolors=shaded(CMAP(NORM(values)),v,surface,elev,azim),edgecolors='none',linewidths=0)
    else:
        ax.text2D(.5,.36,'No element with $d\\geqslant%.2f$\n(max. $d$ = %.2f)'%(DMIN,damage.max()),
                  transform=ax.transAxes,ha='center',va='center',fontsize=6.8,color='#555555',zorder=10,
                  bbox=dict(fc='white',ec='none',pad=1.2,alpha=.9))
    seen,hidden = split_box_edges(elev,azim)
    lines3d(ax,hidden,color='#a8a8a8',lw=.4,ls=(0,(2,2)),zorder=5)
    lines3d(ax,seen,color='#7f7f7f',lw=.5,zorder=5)
    lines3d(ax,notch_edges(nt),color='#8c8c8c',lw=.35,zorder=5)
    ax.text2D(.03,.98,text,transform=ax.transAxes,fontsize=7.2,va='top',linespacing=1.15)


# ---------------------------------------------------------------- data
def load_states(folder,cache):
    if folder:
        records = [loadmat(folder/('state_%04d.mat'%s),squeeze_me=True) for s in STEPS]
        p = np.asarray(records[0]['p']);t = np.asarray(records[0]['T'],dtype=int)-1
        damage = np.stack([r['De'].ravel() for r in records])
        theta = np.array([float(r['current_theta']) for r in records])
        for r,step in zip(records,STEPS):
            assert int(r['inc'])==step and np.array_equal(r['p'],p)
            assert np.array_equal(np.asarray(r['T'],dtype=int)-1,t)
        np.savez_compressed(cache,points=p,tets=t,damage=damage,steps=np.array(STEPS),theta=theta)
    data = np.load(cache)
    assert tuple(data['steps'])==STEPS
    assert np.all((data['damage']>=0)&(data['damage']<=1))
    assert np.allclose(data['theta'],np.array(STEPS)*THETA_END/N_INC,rtol=0,atol=1e-14)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--states',type=Path,help='folder with state_NNNN.mat files from the replay')
    parser.add_argument('--cache',type=Path,default=ROOT/'figure_sources/torsion/evolution_states.npz')
    parser.add_argument('--torque',type=Path,default=ROOT/'figure_sources/torsion/torque_rotation_reference.csv')
    parser.add_argument('--output',type=Path,default=ROOT/'figures')
    args = parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    data = load_states(args.states,args.cache);q = local(data['points']);t = data['tets']
    faces,_ = boundary(t);nt = notch_from_mesh(q,faces)
    assert np.allclose(q.max(axis=0),(400,100,100)),q.max(axis=0)
    curve = np.genfromtxt(args.torque,delimiter=',',names=True);assert len(curve)==N_INC
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'savefig.facecolor':'white','mathtext.fontset':'dejavusans'})

    fig = plt.figure(figsize=(6.6,9.2),facecolor='white')
    H = [1.95,1.2,1.12,1.12,.95,.3];tot = sum(H)
    def row(k):
        h = H[k]/tot;return 1-sum(H[:k+1])/tot,h
    b,h = row(0)
    ax = fig.add_axes([0,b,.63,h],projection='3d',computed_zorder=False);geometry3d(ax,q,faces,nt)
    label(ax,'(a) Model, mesh and boundary conditions',.01,.99)
    ax.text2D(.5,.03,'TET4 mesh: %s nodes, %s elements (dimensions in mm)'%(f'{len(q):,}',f'{len(t):,}'),
              transform=ax.transAxes,ha='center',fontsize=6.8,color='#444444')
    ax = fig.add_axes([.73,b+.20*h,.26,h*.68]);peak = torque_panel(ax,curve)
    label(ax,'(b) Torque-rotation',-.32,1.16)
    b,h = row(1)
    for k,(x0,w,draw,text) in enumerate(((0,.49,lambda a: plan_view(a,nt),'(c) Top view'),
                                         (.51,.49,lambda a: elevation_view(a,nt),'(d) Side view'))):
        ax = fig.add_axes([x0,b,w,h*.9]);draw(ax);ax.set_anchor('N')
        ax.text(.02 if k<2 else 0,1.0,text,transform=ax.transAxes,fontsize=8.5,weight='bold',va='bottom')
    for i,step in enumerate(SHOW):
        b,h = row(2+i//3);k = STEPS.index(step)
        ax = fig.add_axes([(i%3)/3,b,1/3,h],projection='3d',computed_zorder=False)
        text = '(%s) inc. %d%s, $\\theta$ = %.2f mrad'%(LETTERS[i],step,' (peak)' if step==PEAK else '',data['theta'][k]*1e3)
        damage_panel(ax,q,t,data['damage'][k],text,nt,zoom=1.36)
    b,h = row(4);last = data['damage'][STEPS.index(140)]
    views = (('(k) inc. 140, top view',90,-90,1.32),('(l) inc. 140, side view',0,-90,1.32),('(m) inc. 140, opposite side',ELEV,AZIM+180,1.3))
    for i,(text,el,az,zm) in enumerate(views):
        ax = fig.add_axes([i/3,b,1/3,h],projection='3d',computed_zorder=False)
        damage_panel(ax,q,t,last,text,nt,el,az,zm)
    b,h = row(5)
    cax = fig.add_axes([.27,b+h*.30,.46,h*.26])
    ticks = np.linspace(DMIN,1,6)
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=NORM,cmap=CMAP),cax=cax,orientation='horizontal',ticks=ticks)
    cb.ax.set_xticklabels(['%.2f'%v for v in ticks])
    cb.ax.tick_params(labelsize=7,length=2,pad=1)
    cax.set_title('Damage $d$, faces of elements with $d\\geqslant%.2f$'%DMIN,fontsize=7.5,pad=2)
    for ext in ('png','pdf'):
        fig.savefig(args.output/('figure6_torsion_multiview.'+ext),dpi=400)
    plt.close(fig)

    panels = [{'panel':LETTERS[i],'step':s,'theta_rad':float(data['theta'][STEPS.index(s)]),
               'maximum_damage':float(data['damage'][STEPS.index(s)].max()),
               'elements_shown':int((data['damage'][STEPS.index(s)]>=DMIN).sum())}
              for i,s in enumerate(SHOW)]
    report = {'specimen_mm':[400,100,100],
              'notch':{'depth_mm':nt['top_Y']-nt['bottom_Y'],'width_mm':nt['x_z0'][1]-nt['x_z0'][0],
                       'inclination_deg':float(np.degrees(np.arctan2(nt['z'][1]-nt['z'][0],nt['x_z1'][0]-nt['x_z0'][0]))),
                       'centre_from_rotated_end_mm':(nt['x_z0'][0]+nt['x_z1'][1])/2},
              'boundary_conditions':{'fixed_end':'x = max: u_x = u_y = u_z = 0',
                                     'rotated_end':'x = min: u_x = 0, u_y = -theta (z - z_c), u_z = theta (y - y_c)',
                                     'theta_end_rad':THETA_END,'increments':N_INC},
              'peak_torque_increment':peak,'colormap':'turbo','color_limits':[DMIN,1],'display_threshold':DMIN,
              'geometry':'undeformed','display_axes':'plot = (X, 100 - Z, Y), a proper rotation of local (X, Y, Z)',
              'state_cache_sha256':hashlib.sha256(args.cache.read_bytes()).hexdigest(),
              'torque_csv_sha256':hashlib.sha256(args.torque.read_bytes()).hexdigest(),'panels':panels}
    (args.output/'figure6_torsion_multiview_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Saved Figure 6: geometry, boundary conditions, torque and damage views.')


if __name__=='__main__':
    main()
