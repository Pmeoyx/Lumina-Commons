# -*- coding: utf-8 -*-
"""
Lumina Commons —— 沙盘"高低错落"改造脚本（Blender headless）

输入: assets/lumina/lumina_commons_src.glb   (原始，只读)
输出: assets/lumina/lumina_commons_v2.glb    (改造后)
      output/lumina_v2_night.png / lumina_v2_day.png  (预览)

改造思路:
  1) 保持既有路网/地块/浮标/围栏/英雄建筑 完全不动
  2) 在 10 个区之间的空档走廊 + 外环，程序化"长"出建筑群（高度按分区性格分布）
  3) 每簇配阶梯基座 + 建筑顶部发光檐口 + 中段光带
  4) 撒低面树做绿化穿插
  5) 新增件严格镜像  xxx / xxx_day  命名 + 昼夜双材质
运行:
  blender.exe --background --factory-startup --python tools/build_city.py
"""

import bpy, math, os, random, sys, bmesh

# ------------------------------------------------------------------ 路径
PROJ   = r"C:\Users\pmeoyx\WorkBuddy\2026-10-04-12-15-33"
SRC    = os.path.join(PROJ, "assets", "lumina", "lumina_commons_src.glb")
OUT    = os.path.join(PROJ, "assets", "lumina", "lumina_commons_v2.glb")
OUTDIR = os.path.join(PROJ, "output")
os.makedirs(OUTDIR, exist_ok=True)

SEED = 20261007

# ------------------------------------------------------------------ 布局常量
ZONE_ANGLE = {1:0.0, 2:35.5, 3:71.6, 4:108.4, 5:144.5,
              6:180.0, 7:215.5, 8:251.6, 9:288.4, 10:324.5}
ZONE_NAME  = {1:'study', 2:'arcade', 3:'market', 4:'sport', 5:'workshop',
              6:'music', 7:'garden', 8:'pet', 9:'volunteer', 10:'clean'}
# 每个区的"性格高度段"，用于给周边卫星楼定高 —— 这是"错落"的核心
HEIGHT = {1:(10, 20), 2:(7, 17), 3:(3, 8), 4:(3, 6), 5:(8, 18),
          6:(5, 12), 7:(3, 8), 8:(3, 7), 9:(3, 7), 10:(4, 12)}
# 3 个地标空档（取"较小分区号"标识），立高塔做天际线峰值
LANDMARK_GAPS = {2: (24, 30), 5: (22, 28), 9: (20, 26)}
R_ZONE   = 60.0
TILE_H   = 12.0          # 地块半边长 (24x24)
FENCE_R  = 90.0
PLAZA_R  = 16.0

DAY_SUFFIX = '_day'

# ------------------------------------------------------------------ 基础几何
def prim_box(sx, sy, h, r=0.0, seg=3):
    """圆角盒。r>0 时对 12 条棱做 bevel，边缘圆滑、无锋利直角。"""
    rr = min(r, sx/2.0 - 0.05, sy/2.0 - 0.05, max(0.0, h/2.0 - 0.05))
    if rr <= 0.02:
        hx, hy = sx/2.0, sy/2.0
        v = [(-hx,-hy,0),(hx,-hy,0),(hx,hy,0),(-hx,hy,0),
             (-hx,-hy,h),(hx,-hy,h),(hx,hy,h),(-hx,hy,h)]
        f = [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
        return v, f
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx/2.0
        v.co.y *= sy/2.0
        v.co.z *= h/2.0
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=rr, segments=seg,
                    profile=0.5, affect='EDGES', clamp_overlap=True)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    verts = [(v.co.x, v.co.y, v.co.z) for v in bm.verts]
    faces = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    return verts, faces

def prim_cyl(r, h, seg=8):
    v=[]; f=[]
    for i in range(seg):
        a = 2*math.pi*i/seg
        v.append((r*math.cos(a), r*math.sin(a), 0.0))
    for i in range(seg):
        a = 2*math.pi*i/seg
        v.append((r*math.cos(a), r*math.sin(a), h))
    for i in range(seg):
        j = (i+1) % seg
        f.append((i, j, j+seg, i+seg))
    f.append(tuple(range(seg-1, -1, -1)))
    f.append(tuple(range(seg, seg*2)))
    return v, f

def prim_cone(r, h, seg=8):
    v=[]; f=[]; apex=seg
    for i in range(seg):
        a = 2*math.pi*i/seg
        v.append((r*math.cos(a), r*math.sin(a), 0.0))
    v.append((0.0, 0.0, h))
    for i in range(seg):
        j = (i+1) % seg
        f.append((i, j, apex))
    f.append(tuple(range(seg-1, -1, -1)))
    return v, f

def prim_sphere(rz, seg=12, rings=6, rxy=None):
    """低面球（用于圆润树冠）。rxy 为空时取 rz 等轴。"""
    if rxy is None:
        rxy = rz
    v=[]; f=[]
    v.append((0.0, 0.0, rz))                       # 上极点
    for ri in range(1, rings):
        phi = math.pi * ri / rings
        z = rz * math.cos(phi)
        rr = rxy * math.sin(phi)
        for si in range(seg):
            a = 2*math.pi*si/seg
            v.append((rr*math.cos(a), rr*math.sin(a), z))
    v.append((0.0, 0.0, -rz))                      # 下极点
    bottom = len(v) - 1
    # 顶部扇面
    for si in range(seg):
        f.append((0, 1+si, 1+(si+1) % seg))
    # 中间环带
    for ri in range(rings-2):
        a0 = 1 + ri*seg
        b0 = 1 + (ri+1)*seg
        for si in range(seg):
            sj = (si+1) % seg
            f.append((a0+si, b0+si, b0+sj, a0+sj))
    # 底部扇面
    a0 = 1 + (rings-2)*seg
    for si in range(seg):
        f.append((a0+si, bottom, a0+(si+1) % seg))
    return v, f

def prim_torus(R, r, seg=24, rseg=6):
    """平躺圆环（-hole 沿 Z），用于地面主题色地环 / 篮筐 / 杯把。"""
    v=[]; f=[]
    for i in range(seg):
        a = 2*math.pi*i/seg
        ca, sa = math.cos(a), math.sin(a)
        for j in range(rseg):
            b = 2*math.pi*j/rseg
            rr = R + r*math.cos(b)
            v.append((rr*ca, rr*sa, r*math.sin(b)))
    for i in range(seg):
        for j in range(rseg):
            a0 = i*seg + j
            a1 = ((i+1) % seg)*seg + j
            b0 = i*seg + ((j+1) % rseg)
            b1 = ((i+1) % seg)*seg + ((j+1) % rseg)
            f.append((a0, a1, b1, b0))
    return v, f

def add_multi(name, parts):
    """parts: [(verts, faces, z_bottom, cx, cy, yaw_deg, material), ...] -> 合成一个多材质对象"""
    V=[]; F=[]; MI=[]; mats=[]
    for (v, fp, zb, cx, cy, yaw, mat) in parts:
        if mat not in mats:
            mats.append(mat)
        idx = mats.index(mat)
        base = len(V)
        ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        for (x, y, z) in v:
            V.append((x*ca - y*sa + cx, x*sa + y*ca + cy, z + zb))
        for face in fp:
            F.append(tuple(base + i for i in face))
            MI.append(idx)
    me = bpy.data.meshes.new(name)
    me.from_pydata(V, [], F)
    me.update()
    for m in mats:
        me.materials.append(m)
    for i, p in enumerate(me.polygons):
        if i < len(MI):
            p.material_index = MI[i]
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob

# ------------------------------------------------------------------ 导入
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
print("[import] objects =", len(bpy.data.objects))

# 记录导入时的原始对象名，倒角只作用于这些件（不碰后面新生成的道具/地环）
ORIGINAL_NAMES = set(o.name for o in bpy.data.objects)

def getobj(n):
    return bpy.data.objects.get(n)

# ------------------------------------------------------------------ 绿化材质
def ensure_mat(name, base, emit, strength, rough=0.7, metal=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    def setv(key, val):
        if bsdf and key in bsdf.inputs:
            try:
                bsdf.inputs[key].default_value = val
            except Exception:
                pass
    setv("Base Color", (base[0], base[1], base[2], 1.0))
    setv("Emission Color", (emit[0], emit[1], emit[2], 1.0))
    setv("Emission Strength", strength)
    setv("Roughness", rough)
    setv("Metallic", metal)
    return m

ensure_mat("mat_G_leaf_night", (0.06,0.17,0.14), (0.06,0.55,0.42), 0.55)
ensure_mat("mat_G_leaf_day",   (0.26,0.62,0.32), (0.35,0.80,0.42), 0.06)
ensure_mat("mat_G_trunk_night",(0.10,0.08,0.07), (0.10,0.08,0.07), 0.0)
ensure_mat("mat_G_trunk_day",  (0.34,0.24,0.16), (0.34,0.24,0.16), 0.0)
# 道具用的中性件 + 四色垃圾桶
ensure_mat("mat_neutral_night",(0.14,0.14,0.16), (0.14,0.14,0.16), 0.0, rough=0.8)
ensure_mat("mat_neutral_day",  (0.82,0.82,0.84), (0.82,0.82,0.84), 0.0, rough=0.8)
ensure_mat("mat_bin_blue", (0.20,0.45,0.95), (0.30,0.55,1.0), 0.25, rough=0.6)
ensure_mat("mat_bin_green",(0.25,0.75,0.40), (0.35,0.85,0.50), 0.25, rough=0.6)
ensure_mat("mat_bin_red",  (0.90,0.30,0.30), (0.95,0.40,0.40), 0.30, rough=0.6)
ensure_mat("mat_bin_gray", (0.55,0.58,0.62), (0.60,0.63,0.67), 0.10, rough=0.7)

# ------------------------------------------------------------------ 英雄建筑 AABB（供避让）
def hero_aabbs():
    out = {}
    for z in range(1, 11):
        x0=y0=1e9; x1=y1=-1e9; found=False
        for o in bpy.data.objects:
            n = o.name
            if n.endswith(DAY_SUFFIX):
                continue
            if n.startswith("Z%02d_" % z) and o.type == 'MESH':
                found = True
                for c in o.bound_box:
                    wx = o.matrix_world @ __import__('mathutils').Vector(c)
                    x0=min(x0,wx.x); x1=max(x1,wx.x)
                    y0=min(y0,wx.y); y1=max(y1,wx.y)
        if found:
            out[z] = (x0, y0, x1, y1)
    return out
HERO = hero_aabbs()

def zone_xy(z):
    th = math.radians(ZONE_ANGLE[z])
    return (R_ZONE*math.sin(th), R_ZONE*math.cos(th))

TILE_RECTS = []
for z in range(1, 11):
    cx, cy = zone_xy(z)
    TILE_RECTS.append((cx-TILE_H, cy-TILE_H, cx+TILE_H, cy+TILE_H))

def in_rect(r, x, y, pad=0.0):
    return (r[0]-pad) <= x <= (r[2]+pad) and (r[1]-pad) <= y <= (r[3]+pad)

def blocked(x, y, extra=None):
    rr = x*x + y*y
    if rr > (FENCE_R-3.0)**2:
        return True
    if rr < PLAZA_R**2:
        return True
    for r in TILE_RECTS:
        if in_rect(r, x, y, 1.6):
            return True
    if extra:
        for r in extra:
            if in_rect(r, x, y, 0.8):
                return True
    return False

# ------------------------------------------------------------------ 布局生成
def build_layout():
    rng = random.Random(SEED)
    placed = []   # (x, y, footprint_radius)
    items = []    # dict

    def fits(x, y, foot):
        for (px, py, pr) in placed:
            if math.hypot(x-px, y-py) < (pr + foot) * 0.72:
                return False
        return True

    def push(kind, x, y, foot, extra):
        placed.append((x, y, foot))
        d = {'kind': kind, 'x': x, 'y': y}
        d.update(extra)
        items.append(d)

    # ---------------- (1) 地标塔：3 个空档，各 2 座 ----------------
    for gz, (hmin, hmax) in LANDMARK_GAPS.items():
        a0 = ZONE_ANGLE[gz] + 18.0          # 空档中心角
        for k in range(2):
            h = rng.uniform(hmin, hmax)
            sx = rng.uniform(5.0, 7.5); sy = rng.uniform(5.0, 7.5)
            foot = max(sx, sy)/2.0 + 1.0
            for _ in range(400):
                ang = a0 + rng.uniform(-4.6, 4.6)
                rad = rng.uniform(60.0, 76.0)
                x = rad*math.sin(math.radians(ang)); y = rad*math.cos(math.radians(ang))
                if blocked(x, y) or not fits(x, y, foot):
                    continue
                push('bldg', x, y, foot, {'sx':sx, 'sy':sy, 'h':h,
                     'yaw':rng.uniform(-16, 16), 'za':gz, 'zb':(gz % 10) + 1,
                     'landmark':True, 'band':True})
                break

    # ---------------- (2) 空档街道群：填充圆环 ----------------
    for gz in range(1, 11):
        za, zb = gz, (gz % 10) + 1
        n = rng.randint(3, 5)
        for i in range(n):
            src = za if rng.random() < 0.5 else zb
            h = rng.uniform(*HEIGHT[src])
            sx = rng.uniform(3.2, 7.0); sy = rng.uniform(3.2, 7.0)
            foot = max(sx, sy)/2.0 + 0.8
            for _ in range(300):
                ang = ZONE_ANGLE[gz] + 18.0 + rng.uniform(-6.5, 6.5)
                rad = rng.uniform(55.0, 79.0)
                x = rad*math.sin(math.radians(ang)); y = rad*math.cos(math.radians(ang))
                if blocked(x, y) or not fits(x, y, foot):
                    continue
                push('bldg', x, y, foot, {'sx':sx, 'sy':sy, 'h':h,
                     'yaw':rng.uniform(-22, 22), 'za':za, 'zb':zb,
                     'landmark':False, 'band':(h > 11.0)})
                break

    # ---------------- (3) 区内伴楼：地块还有空的分区 ----------------
    for z, rect in HERO.items():
        hx0, hy0, hx1, hy1 = rect
        cx, cy = zone_xy(z)
        free = (TILE_H*2 - (hx1-hx0)) * (TILE_H*2 - (hy1-hy0))
        if free < 150.0:
            continue
        n = 2 if free < 330.0 else 3
        for i in range(n):
            h = rng.uniform(max(3.0, HEIGHT[z][0]-4), HEIGHT[z][1]*0.85)
            sx = rng.uniform(3.0, 5.2); sy = rng.uniform(3.0, 5.2)
            foot = max(sx, sy)/2.0 + 0.7
            for _ in range(400):
                x = rng.uniform(cx-TILE_H+2.0, cx+TILE_H-2.0)
                y = rng.uniform(cy-TILE_H+2.0, cy+TILE_H-2.0)
                if in_rect((hx0, hy0, hx1, hy1), x, y, 1.8):
                    continue
                if in_rect((cx-15.0, cy-15.0, cx+15.0, cy+15.0), x, y, 0.0) and False:
                    continue
                if not fits(x, y, foot):
                    continue
                push('bldg', x, y, foot, {'sx':sx, 'sy':sy, 'h':h,
                     'yaw':rng.uniform(-20, 20), 'za':z, 'zb':z,
                     'landmark':False, 'band':(h > 11.0)})
                break

    # ---------------- (4) 外环天际线：低矮建筑做景深 ----------------
    for i in range(16):
        h = rng.uniform(4.0, 12.0)
        sx = rng.uniform(3.5, 6.5); sy = rng.uniform(3.5, 6.5)
        foot = max(sx, sy)/2.0 + 0.8
        for _ in range(400):
            ang = rng.uniform(0, 360)
            rad = rng.uniform(79.0, 86.5)
            x = rad*math.sin(math.radians(ang)); y = rad*math.cos(math.radians(ang))
            if blocked(x, y) or not fits(x, y, foot):
                continue
            push('bldg', x, y, foot, {'sx':sx, 'sy':sy, 'h':h,
                 'yaw':rng.uniform(-30, 30),
                 'za':rng.randint(1, 10), 'zb':rng.randint(1, 10),
                 'landmark':False, 'band':False})
            break

    # ---------------- (5) 树：空隙绿化 ----------------
    trees = 0
    for _ in range(1400):
        if trees >= 46:
            break
        ang = rng.uniform(0, 360); rad = rng.uniform(52.0, 87.0)
        x = rad*math.sin(math.radians(ang)); y = rad*math.cos(math.radians(ang))
        if blocked(x, y):
            continue
        ok = True
        for (px, py, pr) in placed:
            if math.hypot(x-px, y-py) < pr + 1.5:
                ok = False; break
        if not ok:
            continue
        placed.append((x, y, 1.1))
        items.append({'kind':'tree', 'x':x, 'y':y,
                      'scale':rng.uniform(0.75, 1.35),
                      'kind2':('pine' if rng.random() < 0.55 else 'round'),
                      'yaw':rng.uniform(0, 360)})
        trees += 1

    # ---------------- (6) 阶梯基座：给"簇"一个落地的台 ----------------
    for gz in range(1, 11):
        ang = ZONE_ANGLE[gz] + 18.0
        rad = rng.uniform(60.0, 68.0)
        x = rad*math.sin(math.radians(ang)); y = rad*math.cos(math.radians(ang))
        near = [p for p in placed if math.hypot(p[0]-x, p[1]-y) < 16.0]
        if len(near) < 2:
            continue
        # 用附近的建筑重心做台中心
        mx = sum(p[0] for p in near)/len(near)
        my = sum(p[1] for p in near)/len(near)
        items.append({'kind':'pad', 'x':mx, 'y':my,
                      'sx':rng.uniform(16.0, 22.0), 'sy':rng.uniform(14.0, 20.0),
                      'yaw':rng.uniform(-12, 12), 'gz':gz})

    return items

LAYOUT = build_layout()
print("[layout] items =", len(LAYOUT),
      " bldg =", sum(1 for i in LAYOUT if i['kind']=='bldg'),
      " tree =", sum(1 for i in LAYOUT if i['kind']=='tree'),
      " pad  =", sum(1 for i in LAYOUT if i['kind']=='pad'))

# ------------------------------------------------------------------ 实例化
def make_building(name, it, mat_body_a, mat_body_b, mat_glow_a, mat_glow_b):
    x, y = it['x'], it['y']
    sx, sy, h, yaw = it['sx'], it['sy'], it['h'], it['yaw']
    # 主体（用相邻两区之一的颜色，做出邻里的色彩过渡）
    body = mat_body_a if (hash((name, 'b')) % 2 == 0) else mat_body_b
    glow = mat_glow_a if body is mat_body_a else mat_glow_b
    # 圆角半径：随体量走，既不糊成一团、也不留尖角
    r_body = min(0.62, min(sx, sy) * 0.17, h * 0.11)
    parts = []
    parts.append((*prim_box(sx, sy, h, r=r_body), 0.0, x, y, yaw, body))
    # 中段光带
    if it.get('band'):
        bw = prim_box(sx*1.035, sy*1.035, 0.28, r=0.10, seg=2)
        parts.append((*bw, h*0.58, x, y, yaw, glow))
    # 顶部发光檐口
    parts.append((*prim_box(sx*1.07, sy*1.07, 0.42, r=0.14, seg=2), h, x, y, yaw, glow))
    # 地标塔尖
    if it.get('landmark'):
        parts.append((*prim_box(sx*0.42, sy*0.42, h*0.16, r=0.12, seg=2),
                      h+0.42, x, y, yaw, glow))
        parts.append((*prim_cyl(0.16, h*0.22, 6), h+0.42+h*0.16, x, y, yaw, glow))
    add_multi(name, parts)

def make_tree(name, it, mat_trunk, mat_leaf):
    x, y = it['x'], it['y']
    s = it['scale']; yaw = it['yaw']
    parts = [(*prim_cyl(0.25*s, 1.20*s, 8), 0.0, x, y, yaw, mat_trunk)]
    if it['kind2'] == 'pine':
        # 针叶：多层锥体，锥尖是植物自然形态
        parts.append((*prim_cone(1.45*s, 2.55*s, 10), 1.05*s, x, y, yaw, mat_leaf))
        parts.append((*prim_cone(1.02*s, 1.95*s, 10), 2.40*s, x, y, yaw, mat_leaf))
    else:
        # 阔叶：圆润球冠，替代原来的硬边柱+锥
        parts.append((*prim_sphere(1.30*s, seg=12, rings=6), 2.55*s, x, y, yaw, mat_leaf))
        parts.append((*prim_sphere(1.02*s, seg=10, rings=5),
                      3.10*s, x+0.55*s, y-0.35*s, yaw, mat_leaf))
    add_multi(name, parts)

def make_pad(name, it, mat_u, mat_glow):
    x, y, yaw = it['x'], it['y'], it['yaw']
    a, b = it['sx'], it['sy']
    parts = [
        (*prim_box(a,      b,      0.44, r=0.38, seg=3), 0.0, x, y, yaw, mat_u),
        (*prim_box(a*0.88, b*0.88, 0.28, r=0.30, seg=3), 0.44, x, y, yaw, mat_u),
    ]
    # 台面发光描边
    parts.append((*prim_box(a*0.74, b*0.74, 0.07, r=0.10, seg=2), 0.72, x, y, yaw, mat_glow))
    add_multi(name, parts)

def instantiate(is_day):
    k = 'day' if is_day else 'night'
    suf = DAY_SUFFIX if is_day else ''
    def zbody(z): return bpy.data.materials["mat_Z%02d_%s" % (z, k)]
    def zglow(z): return bpy.data.materials["mat_Z%02d_%s_glow" % (z, k)]
    um = bpy.data.materials["mat_U_%s" % k]
    ug = bpy.data.materials["mat_U_%s_glow" % k]
    leaf = bpy.data.materials["mat_G_leaf_%s" % k]
    trunk = bpy.data.materials["mat_G_trunk_%s" % k]
    n = 0
    for i, it in enumerate(LAYOUT):
        if it['kind'] == 'bldg':
            nm = "C_%s_%02d%s" % (ZONE_NAME[it['za']], i, suf)
            za, zb = it['za'], it['zb']
            make_building(nm, it, zbody(za), zbody(zb), zglow(za), zglow(zb))
            n += 1
        elif it['kind'] == 'tree':
            nm = "G_tree_%02d%s" % (i, suf)
            make_tree(nm, it, trunk, leaf)
            n += 1
        elif it['kind'] == 'pad':
            nm = "C_pad_%02d%s" % (i, suf)
            make_pad(nm, it, um, ug)
            n += 1
    return n

# ----------------------------------------------------------------- 场所特征强化
def zmat(z, is_day, glow=False):
    k = 'day' if is_day else 'night'
    return bpy.data.materials["mat_Z%02d_%s%s" % (z, k, "_glow" if glow else "")]

def neut(is_day):
    return bpy.data.materials["mat_neutral_%s" % ("day" if is_day else "night")]

# ---- 各分区标志道具（写实低面，分区主题色上色）----
def p_bookstack(px,py,yaw,M):
    parts=[]; z=0.0
    for (sx,sy,h) in [(3.2,2.4,0.7),(2.8,2.0,0.6),(2.3,1.6,0.5)]:
        parts.append((*prim_box(sx,sy,h,r=0.06,seg=2), z, px,py,yaw,M['body'])); z+=h
    return parts

def p_trophy(px,py,yaw,M):
    return [(*prim_cyl(0.9,0.3,8),0.0,px,py,yaw,M['neut']),
            (*prim_cyl(0.18,2.2,8),0.3,px,py,yaw,M['neut']),
            (*prim_cone(1.1,1.6,12),2.5,px,py,yaw,M['body'])]

def p_dice(px,py,yaw,M):
    return [(*prim_box(4.0,4.0,4.0,r=0.5,seg=3),0.0,px,py,yaw,M['body'])]

def p_gamepad(px,py,yaw,M):
    return [(*prim_box(4.0,2.2,0.8,r=0.3,seg=2),0.4,px,py,yaw,M['body']),
            (*prim_cyl(0.35,0.7,10),0.8,px-1.0,py,yaw,M['neut']),
            (*prim_cyl(0.35,0.7,10),0.8,px+1.0,py,yaw,M['neut']),
            (*prim_box(1.4,1.0,0.06,r=0.05,seg=2),0.85,px,py,yaw,M['glow'])]

def p_coffee(px,py,yaw,M):
    return [(*prim_cyl(1.2,3.0,14),0.0,px,py,yaw,M['neut']),
            (*prim_torus(1.5,0.22,12,6),1.5,px+1.4,py,yaw,M['neut']),
            (*prim_cone(0.5,1.2,8),3.0,px,py,yaw,M['glow'])]

def p_table(px,py,yaw,M):
    parts=[(*prim_box(3.0,3.0,0.3,r=0.1,seg=2),1.4,px,py,yaw,M['neut'])]
    for dx,dy in [(-1.2,-1.2),(1.2,-1.2),(-1.2,1.2),(1.2,1.2)]:
        parts.append((*prim_cyl(0.18,1.4,8),0.0,px+dx,py+dy,yaw,M['neut']))
    return parts

def p_hoop(px,py,yaw,M):
    return [(*prim_cyl(0.25,4.0,8),0.0,px,py,yaw,M['neut']),
            (*prim_box(3.0,2.0,0.2,r=0.05,seg=2),4.0,px,py,yaw,M['neut']),
            (*prim_torus(0.7,0.12,12,6),3.0,px,py,yaw,M['glow'])]

def p_scoreboard(px,py,yaw,M):
    return [(*prim_cyl(0.2,3.0,8),0.0,px,py,yaw,M['neut']),
            (*prim_box(3.2,2.0,0.3,r=0.08,seg=2),3.0,px,py,yaw,M['glow'])]

def p_paint(px,py,yaw,M):
    parts=[]
    for i,c in enumerate(['mat_bin_blue','mat_bin_green','mat_bin_red']):
        parts.append((*prim_cyl(0.7,1.6,12),0.0,px-2.0+i*2.0,py,yaw,bpy.data.materials[c]))
    return parts

def p_printer(px,py,yaw,M):
    return [(*prim_box(2.6,2.6,2.4,r=0.12,seg=2),0.0,px,py,yaw,M['body']),
            (*prim_cyl(0.2,0.6,8),2.4,px,py,yaw,M['neut'])]

def p_guitar(px,py,yaw,M):
    return [(*prim_box(1.6,3.4,0.5,r=0.2,seg=2),0.6,px,py-1.6,yaw,M['body']),
            (*prim_box(0.5,3.2,0.4,r=0.1,seg=2),2.2,px,py+1.4,yaw,M['neut'])]

def p_easel(px,py,yaw,M):
    return [(*prim_box(0.3,0.3,4.0,r=0.05,seg=2),0.0,px-0.6,py,yaw,M['neut']),
            (*prim_box(0.3,0.3,4.0,r=0.05,seg=2),0.0,px+0.6,py,yaw,M['neut']),
            (*prim_box(2.2,1.6,0.15,r=0.05,seg=2),2.6,px,py,yaw,M['glow'])]

def p_planter(px,py,yaw,M):
    return [(*prim_box(2.4,1.4,1.2,r=0.15,seg=2),0.0,px,py,yaw,M['neut']),
            (*prim_sphere(0.9,seg=10,rings=5),1.4,px-0.6,py,yaw,M['leaf']),
            (*prim_sphere(0.7,seg=10,rings=5),1.3,px+0.6,py,yaw,M['leaf'])]

def p_doghouse(px,py,yaw,M):
    return [(*prim_box(2.4,2.4,1.8,r=0.1,seg=2),0.0,px,py,yaw,M['body']),
            (*prim_cone(1.9,1.0,4),1.8,px,py,yaw,M['neut'])]

def p_catree(px,py,yaw,M):
    return [(*prim_cyl(0.4,3.0,8),0.0,px,py,yaw,M['neut']),
            (*prim_sphere(1.0,seg=10,rings=5),3.0,px,py,yaw,M['body'])]

def p_firstaid(px,py,yaw,M):
    return [(*prim_box(2.0,1.6,1.4,r=0.1,seg=2),0.0,px,py,yaw,M['neut']),
            (*prim_box(0.4,1.0,0.06,r=0.03,seg=2),0.72,px,py,yaw,M['acc_red']),
            (*prim_box(1.0,0.4,0.06,r=0.03,seg=2),0.72,px,py,yaw,M['acc_red'])]

def p_mapboard(px,py,yaw,M):
    return [(*prim_cyl(0.2,2.6,8),0.0,px,py,yaw,M['neut']),
            (*prim_box(2.4,1.8,0.12,r=0.05,seg=2),2.6,px,py,yaw,M['glow'])]

def p_bins(px,py,yaw,M):
    parts=[]
    for i,c in enumerate(['mat_bin_blue','mat_bin_green','mat_bin_red','mat_bin_gray']):
        a=math.radians(45+i*90)
        parts.append((*prim_cyl(0.7,1.8,12),0.0,px+1.6*math.cos(a),py+1.6*math.sin(a),yaw,bpy.data.materials[c]))
    return parts

def p_sweeper(px,py,yaw,M):
    return [(*prim_cyl(1.4,0.5,16),0.0,px,py,yaw,M['body']),
            (*prim_sphere(0.7,seg=10,rings=5),0.5,px,py,yaw,M['neut'])]

ZPROP = {1:[p_bookstack,p_trophy,p_bookstack], 2:[p_dice,p_gamepad,p_dice],
         3:[p_coffee,p_table,p_coffee], 4:[p_hoop,p_scoreboard,p_hoop],
         5:[p_paint,p_printer,p_paint], 6:[p_guitar,p_easel,p_guitar],
         7:[p_planter,p_planter,p_planter], 8:[p_doghouse,p_catree,p_doghouse],
         9:[p_firstaid,p_mapboard,p_firstaid], 10:[p_bins,p_sweeper,p_bins]}

def prop_slots(z, cx, cy, ha):
    # 英雄建筑几乎铺满地块 -> 道具改放到"朝广场一侧的入口铺地"
    # 按英雄 AABB 内边界自适应外推，避开英雄与广场
    if ha:
        corners = [(ha[0],ha[1]),(ha[2],ha[1]),(ha[0],ha[3]),(ha[2],ha[3])]
        innerR = min(math.hypot(x, y) for (x, y) in corners)
    else:
        innerR = R_ZONE - 14.0
    Rp = max(innerR - 5.0, PLAZA_R + 4.0)
    th = math.atan2(cx, cy)            # 与 zone_xy 一致：x=R sinθ, y=R cosθ
    rx, ry = math.sin(th), math.cos(th)
    tx, ty = -ry, rx                  # 切线方向（沿地块横向铺开）
    bx, by = Rp*rx, Rp*ry
    slots = []
    for off in (-11, 0, 11):
        px, py = bx + tx*off, by + ty*off
        if math.hypot(px, py) < PLAZA_R + 2:
            continue
        slots.append((px, py))
    return slots

def build_props():
    rng = random.Random(SEED + 7)
    total = 0
    for z in range(1, 11):
        cx, cy = zone_xy(z)
        ha = HERO.get(z)
        slots = prop_slots(z, cx, cy, ha)
        builders = ZPROP[z]
        for idx, (px, py) in enumerate(slots):
            if idx >= len(builders):
                break
            yaw = rng.uniform(-25, 25)
            for is_day in (False, True):
                suf = DAY_SUFFIX if is_day else ''
                M = {'body': zmat(z, is_day),
                     'glow': zmat(z, is_day, glow=True),
                     'neut': neut(is_day),
                     'leaf': bpy.data.materials["mat_G_leaf_%s" % ("day" if is_day else "night")],
                     'acc_red': bpy.data.materials["mat_bin_red"]}
                nm = "Z%02d_prop_%02d%s" % (z, idx, suf)
                add_multi(nm, builders[idx](px, py, yaw, M))
                total += 1
    return total

def build_halos():
    total = 0
    for z in range(1, 11):
        cx, cy = zone_xy(z)
        for is_day in (False, True):
            suf = DAY_SUFFIX if is_day else ''
            # 白天=实色亮环；夜晚=主题色发光环
            mat = zmat(z, is_day, glow=(not is_day))
            nm = "Z%02d_halo%s" % (z, suf)
            add_multi(nm, [(*prim_torus(11.0, 0.7, 40, 8), 0.25, cx, cy, 0.0, mat)])
            total += 1
    return total

print("[build] night objects:", instantiate(False))
print("[build] day   objects:", instantiate(True))
print("[build] total objects:", len(bpy.data.objects))
print("[props]  objects:", build_props())
print("[halo]   objects:", build_halos())

# ------------------------------------------------------------------ 原模型圆角化
# 用户要求"建模也不要锋利边缘"：给英雄建筑 + 地块 加保守 bevel（导出时烘焙）
def bevel_original(width=0.12, segments=2, angle_deg=35.0):
    n = 0
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        nm = o.name
        if nm not in ORIGINAL_NAMES:
            continue
        base = nm[:-len(DAY_SUFFIX)] if nm.endswith(DAY_SUFFIX) else nm
        is_hero = (len(base) > 3 and base[0] == 'Z' and base[1:3].isdigit() and base[3] == '_')
        is_tile = base.startswith('U_tile')
        if not (is_hero or is_tile):
            continue
        if any(m.type == 'BEVEL' for m in o.modifiers):
            continue
        m = o.modifiers.new("smooth_bevel", 'BEVEL')
        m.width = width
        m.segments = segments
        m.limit_method = 'ANGLE'
        m.angle_limit = math.radians(angle_deg)
        m.use_clamp_overlap = True
        try:
            m.harden_normals = False
        except Exception:
            pass
        n += 1
    return n

print("[smooth] bevel applied to", bevel_original(), "original meshes")

# ------------------------------------------------------------------ 导出 GLB
bpy.ops.export_scene.gltf(
    filepath=OUT,
    export_format='GLB',
    use_selection=False,
    export_apply=True,
    export_yup=True,
    export_cameras=False,
    export_lights=False,
)
print("[export]", OUT, "%.2f MB" % (os.path.getsize(OUT)/1048576.0))

# ------------------------------------------------------------------ 渲染预览
scene = bpy.context.scene
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except Exception:
    try:
        scene.render.engine = 'BLENDER_EEVEE'
    except Exception:
        scene.render.engine = 'CYCLES'
print("[render] engine =", scene.render.engine)

scene.render.resolution_x = 1440
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
try:
    scene.eevee.taa_render_samples = 32
except Exception:
    pass
try:
    scene.view_settings.view_transform = 'Standard'
except Exception:
    pass

# 相机（近等距俯视，对齐参考截图观感）
cam_d = bpy.data.cameras.new("PreviewCam")
cam_d.lens = 80.0
cam = bpy.data.objects.new("PreviewCam", cam_d)
scene.collection.objects.link(cam)
TGT = (0.0, 0.0, 9.0)
AZ, EL, DIST = math.radians(18.0), math.radians(46.0), 350.0
cx = DIST*math.cos(EL)*math.sin(AZ)
cy = -DIST*math.cos(EL)*math.cos(AZ)
cz = DIST*math.sin(EL)
cam.location = (TGT[0]+cx, TGT[1]+cy, TGT[2]+cz)
v = __import__('mathutils').Vector(TGT) - cam.location
cam.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# 灯光
sun_d = bpy.data.lights.new("Sun", type='SUN')
sun = bpy.data.objects.new("Sun", sun_d)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(52), 0.0, math.radians(35))

world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")

def set_mode(is_day):
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        d = o.name.endswith(DAY_SUFFIX)
        o.hide_render = (d != is_day)
    if bg:
        if is_day:
            bg.inputs[0].default_value = (0.78, 0.85, 0.96, 1.0)
            bg.inputs[1].default_value = 1.05
            sun_d.energy = 3.4
            sun_d.color = (1.0, 0.98, 0.94)
        else:
            bg.inputs[0].default_value = (0.035, 0.040, 0.085, 1.0)
            bg.inputs[1].default_value = 0.85
            sun_d.energy = 0.55
            sun_d.color = (0.62, 0.70, 1.0)

def render_to(path, is_day):
    set_mode(is_day)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("[render]", path)

try:
    render_to(os.path.join(OUTDIR, "lumina_v2_night.png"), False)
    render_to(os.path.join(OUTDIR, "lumina_v2_day.png"), True)
except Exception as e:
    print("[render] EEVEE failed -> CYCLES:", e)
    scene.render.engine = 'CYCLES'
    try:
        scene.cycles.samples = 24
        scene.cycles.use_denoising = True
    except Exception:
        pass
    render_to(os.path.join(OUTDIR, "lumina_v2_night.png"), False)
    render_to(os.path.join(OUTDIR, "lumina_v2_day.png"), True)

print("[done]")
