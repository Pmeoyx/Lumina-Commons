#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GLB 只读几何核对（不依赖 Blender）。
列出指定名字前缀的节点在世界坐标系下的中心 (x,y,z)，用于验证
"地块(U_tile) / 房间(Zxx_room) / 信标(Z00)" 三者是否对齐到同一 R 环。

用法: python tools/gdump.py <glb> [prefix1 prefix2 ...]
"""
import struct, json, sys, math, os

def load_glb(path):
    with open(path, 'rb') as f:
        data = f.read()
    magic, ver, length = struct.unpack('<III', data[:12])
    if magic != 0x46546C67:
        raise SystemExit("不是 GLB: " + path)
    off = 12
    js = None
    binc = b''
    while off < length:
        clen, ctype = struct.unpack('<II', data[off:off+8]); off += 8
        if ctype == 0x4E4F534A:
            js = json.loads(data[off:off+clen].decode('utf-8'))
        elif ctype == 0x004E4942:
            binc = data[off:off+clen]
        off += clen
    return js, binc

def ident():
    return [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]

def mul(a, b):
    # 列主序 4x4
    r = [0.0]*16
    for c in range(4):
        for i in range(4):
            s = 0.0
            for k in range(4):
                s += a[k*4+i] * b[c*4+k]
            r[c*4+i] = s
    return r

def translate(x,y,z):
    m = ident(); m[12]=x; m[13]=y; m[14]=z; return m

def scale(x,y,z):
    m = ident(); m[0]=x; m[5]=y; m[10]=z; return m

def quat(q):  # [x,y,z,w]
    x,y,z,w = q
    m = ident()
    m[0]=1-2*(y*y+z*z); m[1]=2*(x*y+z*w);   m[2]=2*(x*z-y*w)
    m[4]=2*(x*y-z*w);   m[5]=1-2*(x*x+z*z); m[6]=2*(y*z+x*w)
    m[8]=2*(x*z+y*w);   m[9]=2*(y*z-x*w);   m[10]=1-2*(x*x+y*y)
    return m

def apply(M, p):
    x,y,z = p
    w = M[3]*x + M[7]*y + M[11]*z + M[15]
    return ((M[0]*x+M[4]*y+M[8]*z+M[12]) / w,
            (M[1]*x+M[5]*y+M[9]*z+M[13]) / w,
            (M[2]*x+M[6]*y+M[10]*z+M[14]) / w)

def node_matrix(js, idx, parent):
    n = js['nodes'][idx]
    T = ident()
    if 'translation' in n:
        tx,ty,tz = n['translation']
        T = mul(T, translate(tx,ty,tz))
    if 'rotation' in n:
        T = mul(T, quat(n['rotation']))
    if 'scale' in n:
        sx,sy,sz = n['scale']
        T = mul(T, scale(sx,sy,sz))
    if parent:
        T = mul(parent, T)
    return T

def local_aabb(js, mesh_idx):
    mesh = js['meshes'][mesh_idx]
    mn=[1e9,1e9,1e9]; mx=[-1e9,-1e9,-1e9]
    for prim in mesh['primitives']:
        acc = js['accessors'][prim['attributes']['POSITION']]
        if 'min' in acc and 'max' in acc:
            mn = [min(mn[i], acc['min'][i]) for i in range(3)]
            mx = [max(mx[i], acc['max'][i]) for i in range(3)]
    return mn, mx

def collect(js, binc, prefixes):
    roots = js['scenes'][0]['nodes']
    out = []
    def walk(idx, parent):
        n = js['nodes'][idx]
        nm = n.get('name','')
        M = node_matrix(js, idx, parent)
        if any(nm.startswith(p) for p in prefixes):
            if 'mesh' in n:
                mn, mx = local_aabb(js, n['mesh'])
                c = [(mn[i]+mx[i])/2 for i in range(3)]
                wc = apply(M, c)
                out.append((nm, round(wc[0],2), round(wc[1],2), round(wc[2],2)))
        for ch in n.get('children', []):
            walk(ch, M)
    for r in roots:
        walk(r, None)
    return out

def main():
    if len(sys.argv) < 2:
        print("用法: python tools/gdump.py <glb> [prefix ...]")
        sys.exit(1)
    path = sys.argv[1]
    prefixes = sys.argv[2:] or ['U_tile', 'Z', 'C_']
    if not os.path.exists(path):
        raise SystemExit("文件不存在: " + path)
    js, binc = load_glb(path)
    rows = collect(js, binc, prefixes)
    rows.sort(key=lambda r: r[0])
    print("=== %s ===" % os.path.basename(path))
    print("节点数(匹配):", len(rows))
    for nm, x, y, z in rows:
        r = math.hypot(x, z)
        print("  %-26s  center=(%8.2f, %8.2f, %8.2f)   R=%.2f" % (nm, x, y, z, r))

if __name__ == '__main__':
    main()
