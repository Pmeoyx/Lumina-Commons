import json,struct,re,math,sys

def load(fn):
    d=open(fn,'rb').read()
    off=12; js=None
    while off<len(d):
        ln,ty=struct.unpack_from('<II',d,off); off+=8
        if ty==0x4E4F534A: js=json.loads(d[off:off+ln].decode('utf-8'))
        off+=ln
    return js

def mat_identity(): return [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]

def trs_to_mat(t,r,s):
    # column-major 4x4 as list of 16 (glTF order)
    x,y,z,w = r if len(r)==4 else (0,0,0,1)
    xx,yy,zz=x*x,y*y,z*z
    xy,xz,yz=x*y,x*z,y*z
    wx,wy,wz=w*x,w*y,w*z
    m=[
        1-2*(yy+zz), 2*(xy+wz),   2*(xz-wy),   0,
        2*(xy-wz),   1-2*(xx+zz), 2*(yz+wx),   0,
        2*(xz+wy),   2*(yz-wx),   1-2*(xx+yy), 0,
        0,0,0,1]
    for i in range(3):
        m[i*4+0]*=s[0]; m[i*4+1]*=s[1]; m[i*4+2]*=s[2]
        m[i*4+3] = t[i] if i<3 else 0
    return m

def xform(m,v):
    x,y,z=v
    return (m[0]*x+m[4]*y+m[8]*z+m[12],
            m[1]*x+m[5]*y+m[9]*z+m[13],
            m[2]*x+m[6]*y+m[10]*z+m[14])

js=load('assets/lumina/lumina_commons_src.glb')
nodes=js['nodes']; meshes=js['meshes']; acc=js['accessors']

# assume root has identity transform
def node_world_aabb(ni):
    n=nodes[ni]
    if 'matrix' in n:
        mm=n['matrix']
    elif 'translation' in n or 'rotation' in n or 'scale' in n:
        mm=trs_to_mat(n.get('translation',[0,0,0]), n.get('rotation',[0,0,0,1]), n.get('scale',[1,1,1]))
    else:
        mm=mat_identity()
    mn=[1e9]*3; mx=[-1e9]*3; nprim=0
    if 'mesh' in n:
        for p in meshes[n['mesh']].get('primitives',[]):
            ai=p.get('attributes',{}).get('POSITION')
            if ai is None: continue
            a=acc[ai]
            if 'min' not in a: continue
            nprim+=1
            # 8 corners
            for cx in (a['min'][0],a['max'][0]):
              for cy in (a['min'][1],a['max'][1]):
                for cz in (a['min'][2],a['max'][2]):
                    w=xform(mm,(cx,cy,cz))
                    for i in range(3):
                        mn[i]=min(mn[i],w[i]); mx[i]=max(mx[i],w[i])
    return mn,mx,nprim

heroes=[i for i,n in enumerate(nodes) if re.match(r'^Z\d\d_',n.get('name',''))]
print('%-26s %10s %10s %10s %8s %8s %8s  %s' % ('节点','maxX-minX','maxY(高)','maxZ-minZ','cx','cy','cz','prims'))
print('-'*104)
rows=[]
for i in sorted(heroes, key=lambda k: nodes[k]['name']):
    mn,mx,np_=node_world_aabb(i)
    if mn[0]>1e8:
        print('%-26s  (no geom)' % nodes[i]['name']); continue
    dx=mx[0]-mn[0]; dy=mx[1]-mn[1]; dz=mx[2]-mn[2]
    cx=(mx[0]+mn[0])/2; cy=(mx[1]+mn[1])/2; cz=(mx[2]+mn[2])/2
    rows.append((nodes[i]['name'],dx,dy,dz,cx,cy,cz,np_))
    print('%-26s %10.2f %10.2f %10.2f %8.1f %8.2f %8.1f  %d' % (nodes[i]['name'],dx,dy,dz,cx,cy,cz,np_))

print()
tiles=[i for i,n in enumerate(nodes) if re.match(r'^U_tile_Z\d\d$',n.get('name',''))]
print('=== 地块 U_tile_Zxx ===')
for i in sorted(tiles,key=lambda k:nodes[k]['name']):
    mn,mx,np_=node_world_aabb(i)
    if mn[0]>1e8: continue
    print('%-18s size=(%.1f, %.2f, %.1f)  center=(%.1f, %.2f, %.1f)' % (
        nodes[i]['name'], mx[0]-mn[0], mx[1]-mn[1], mx[2]-mn[2],
        (mx[0]+mn[0])/2,(mx[1]+mn[1])/2,(mx[2]+mn[2])/2))

print()
print('=== 全部 hero 高度排序 ===')
for r in sorted(rows,key=lambda r:-r[2]):
    print('  %-26s 高 %.2f' % (r[0], r[2]))
