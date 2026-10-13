# -*- coding: utf-8 -*-
"""
微光社区 · 地基重建脚本（Blender headless）

只重建"地盘"层，严格对齐 lumina_rooms.glb 的 8 区房间：
  - 8 区地块 U_tile / U_tile_top（落在每栋房间的正下方，R=60 新 8 区环）
  - 中心广场 U_plaza + 中心信标 Z00（来自源，对称保留）
  - 每区信标基座 U_beacon_Zxx（给 Web 悬浮信标一个落地柱）
  - 放射状路网 U_path（连接中心与各区）
  - 绿化：起伏草坪 U_lawn + 草丛 G_grass_* + 灌木 G_bush_* + 小花 G_flower_* + 树 G_tree_*

落位公式与 build_rooms_v2.py 完全一致：
  Blender 坐标 (R*sinθ, R*cosθ, 0)  →  导出 y-up 后 glTF (R*sinθ, 0, -R*cosθ)
  即与房间 shell 的世界坐标逐区重合。

运行:
  "D:/Program Files/Blender Foundation/Blender 5.0/blender.exe" --background --factory-startup --python tools/build_base_ground.py
"""

import bpy, math, os, random, bmesh

PROJ   = r"C:\Users\pmeoyx\WorkBuddy\2026-10-04-12-15-33"
SRC    = os.path.join(PROJ, "assets", "lumina", "lumina_commons_src.glb")
OUT    = os.path.join(PROJ, "assets", "lumina", "lumina_commons_v2.glb")
OUTDIR = os.path.join(PROJ, "output")
os.makedirs(OUTDIR, exist_ok=True)

SEED = 20261009

R_ZONE   = 60.0     # 地块环半径（= 房间环）
TILE     = 24.0     # 地块边长
TILE_H   = 0.5      # 地块厚度
PLAZA_R  = 16.0
FENCE_R  = 92.0

# 新 8 区：与 js/zones.js 角度一致；id 集合 {1,2,3,4,5,8,9,10}
ZONES = [
    (1,   0.0), (2,  45.0), (3,  90.0), (4, 135.0),
    (5, 180.0), (8, 225.0), (9, 270.0), (10, 315.0),
]
THEME = {1:'#ffd166', 2:'#ff5ca8', 3:'#ff9f5c', 4:'#5ce1e6',
         5:'#b388ff', 8:'#c79a6b', 9:'#ff5c5c', 10:'#4dd0e1'}

# ------------------------------------------------------------------ 基础几何
def prim_box(sx, sy, h, r=0.0, seg=3):
    rr = min(r, sx/2.0-0.05, sy/2.0-0.05, max(0.0, h/2.0-0.05))
    if rr <= 0.02:
        hx, hy = sx/2.0, sy/2.0
        v = [(-hx,-hy,0),(hx,-hy,0),(hx,hy,0),(-hx,hy,0),
             (-hx,-hy,h),(hx,-hy,h),(hx,hy,h),(-hx,hy,h)]
        f = [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
        return v, f
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx/2.0; v.co.y *= sy/2.0; v.co.z *= h/2.0
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=rr, segments=seg,
                    profile=0.5, affect='EDGES', clamp_overlap=True)
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    verts = [(v.co.x, v.co.y, v.co.z) for v in bm.verts]
    faces = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    return verts, faces

def prim_cyl(r, h, seg=10):
    v=[]; f=[]
    for i in range(seg):
        a=2*math.pi*i/seg
        v.append((r*math.cos(a), r*math.sin(a), 0.0))
    for i in range(seg):
        a=2*math.pi*i/seg
        v.append((r*math.cos(a), r*math.sin(a), h))
    for i in range(seg):
        j=(i+1)%seg
        f.append((i, j, j+seg, i+seg))
    f.append(tuple(range(seg-1,-1,-1)))
    f.append(tuple(range(seg, seg*2)))
    return v, f

def prim_cone(r, h, seg=10):
    v=[]; f=[]; apex=seg
    for i in range(seg):
        a=2*math.pi*i/seg
        v.append((r*math.cos(a), r*math.sin(a), 0.0))
    v.append((0.0,0.0,h))
    for i in range(seg):
        j=(i+1)%seg
        f.append((i, j, apex))
    f.append(tuple(range(seg-1,-1,-1)))
    return v, f

def prim_sphere(rz, seg=12, rings=6, rxy=None):
    if rxy is None: rxy=rz
    v=[]; f=[]
    v.append((0.0,0.0,rz))
    for ri in range(1,rings):
        phi=math.pi*ri/rings; z=rz*math.cos(phi); rr=rxy*math.sin(phi)
        for si in range(seg):
            a=2*math.pi*si/seg
            v.append((rr*math.cos(a), rr*math.sin(a), z))
    v.append((0.0,0.0,-rz))
    bottom=len(v)-1
    for si in range(seg):
        f.append((0,1+si,1+(si+1)%seg))
    for ri in range(rings-2):
        a0=1+ri*seg; b0=1+(ri+1)*seg
        for si in range(seg):
            sj=(si+1)%seg
            f.append((a0+si,b0+si,b0+sj,a0+sj))
    a0=1+(rings-2)*seg
    for si in range(seg):
        f.append((a0+si,bottom,a0+(si+1)%seg))
    return v, f

def add_multi(name, parts):
    """parts: [(verts, faces, z_bottom, cx, cy, yaw_deg, material), ...]"""
    V=[]; F=[]; MI=[]; mats=[]
    for (v, fp, zb, cx, cy, yaw, mat) in parts:
        if mat not in mats: mats.append(mat)
        idx=mats.index(mat)
        base=len(V)
        ca, sa=math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        for (x,y,z) in v:
            V.append((x*ca-y*sa+cx, x*sa+y*ca+cy, z+zb))
        for face in fp:
            F.append(tuple(base+i for i in face)); MI.append(idx)
    me=bpy.data.meshes.new(name); me.from_pydata(V,[],F); me.update()
    for m in mats: me.materials.append(m)
    for i,p in enumerate(me.polygons):
        if i<len(MI): p.material_index=MI[i]
    ob=bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob

# ------------------------------------------------------------------ 材质
def ensure_mat(name, base, emit, strength, rough=0.85, metal=0.0):
    m=bpy.data.materials.get(name)
    if m: return m
    m=bpy.data.materials.new(name); m.use_nodes=True
    bsdf=m.node_tree.nodes.get("Principled BSDF")
    def setv(k,val):
        if bsdf and k in bsdf.inputs:
            try: bsdf.inputs[k].default_value=val
            except Exception: pass
    setv("Base Color", (base[0],base[1],base[2],1.0))
    setv("Emission Color", (emit[0],emit[1],emit[2],1.0))
    setv("Emission Strength", strength)
    setv("Roughness", rough); setv("Metallic", metal)
    return m

def theme_rgb(hexs):
    h=hexs.lstrip('#')
    return (int(h[0:2],16)/255.0, int(h[2:4],16)/255.0, int(h[4:6],16)/255.0)

# 注：材质在下方「导入源 + 清理」之后创建，避免 read_factory_settings 把
#     预创建的材质全部清空，导致 add_multi 时 StructRNA 已销毁的报错。

# ------------------------------------------------------------------ 导入源（仅取材质 + 中心信标）
bpy.ops.wm.read_factory_settings(use_empty=True)
try:
    bpy.ops.preferences.addon_enable(module='io_scene_gltf2')
except Exception:
    pass
bpy.ops.import_scene.gltf(filepath=SRC)
print("[import] 源对象数 =", len(bpy.data.objects))

# 删除源里"旧 10 区错位"且会被 Web 显示的元素；保留 Z00_* 中心信标组
# 做法：删掉所有旧网格（mesh），仅保留含 "Z00" 的中心信标组与空物体/骨架。
removed=0
for o in list(bpy.data.objects):
    nm=o.name
    if o.type != 'MESH': continue        # 保留空物体 / 骨架等层级结构
    if 'Z00' in nm: continue             # 保留中心信标组（含 U_beacon_Z00 等）
    bpy.data.objects.remove(o, do_unlink=True); removed+=1
print("[clean] 删除旧错位网格 =", removed, "· 剩余对象 =", len(bpy.data.objects))

# ------------------------------------------------------------------ 材质（在 read_factory_settings + 导入 + 清理之后创建）
# 中性色，昼夜间都协调；LBG_ 前缀避免与源同名材质撞车
mat_ground = ensure_mat("LBG_ground", (0.17,0.18,0.24), (0.10,0.11,0.16), 0.20)
mat_plaza  = ensure_mat("LBG_plaza",  (0.22,0.24,0.32), (0.14,0.16,0.24), 0.25)
mat_path   = ensure_mat("LBG_path",   (0.20,0.21,0.27), (0.12,0.13,0.18), 0.18)
mat_beacon = ensure_mat("LBG_beacon", (0.55,0.58,0.66), (0.30,0.62,0.66), 0.45)
mat_beacon_glow = ensure_mat("LBG_beacon_glow", (0.20,0.45,0.48), (0.25,0.95,1.0), 0.9)
mat_leaf = ensure_mat("LBG_leaf", (0.18,0.45,0.28), (0.15,0.40,0.25), 0.20)
mat_trunk= ensure_mat("LBG_trunk",(0.28,0.20,0.14), (0.10,0.08,0.07), 0.0)

# 每区地块顶面：主题色（轻度发光，区分分区）
ZTOP={}
for zid, hx in THEME.items():
    tr,tg,tb=theme_rgb(hx)
    ZTOP[zid]=ensure_mat("LBG_top_%02d"%zid,
                         (tr*0.55,tg*0.55,tb*0.55), (tr*0.35,tg*0.35,tb*0.35), 0.30)

# ------------------------------------------------------------------ 落位（与房间同公式）
def zone_xy_blender(angle):
    th=math.radians(angle)
    return (R_ZONE*math.sin(th), R_ZONE*math.cos(th), 0.0)

TILE_RECTS=[]
for zid, ang in ZONES:
    px,py,_=zone_xy_blender(ang)
    TILE_RECTS.append((px-TILE/2, py-TILE/2, px+TILE/2, py+TILE/2))
    # 地块底座
    add_multi("U_tile_Z%02d"%zid, [
        (*prim_box(TILE, TILE, TILE_H, r=0.4, seg=3), 0.0, px, py, 0.0, mat_ground)])
    # 地块顶面（主题色）
    add_multi("U_tile_top_Z%02d"%zid, [
        (*prim_box(TILE-1.2, TILE-1.2, 0.28, r=0.3, seg=3), TILE_H, px, py, 0.0, ZTOP[zid])])
    # 信标基座（给 Web R=60 处悬浮信标一个落地柱）
    add_multi("U_beacon_Z%02d"%zid, [
        (*prim_cyl(1.3, 6.0, 12), TILE_H, px, py, 0.0, mat_beacon),
        (*prim_cyl(1.55, 0.5, 12), TILE_H+6.0, px, py, 0.0, mat_beacon_glow)])
print("[tiles] 已生成 8 区地块 + 信标基座")

# 中心广场
add_multi("U_plaza", [
    (*prim_cyl(PLAZA_R, 0.4, 48), 0.0, 0.0, 0.0, 0.0, mat_plaza),
    (*prim_cyl(PLAZA_R-2.0, 0.12, 48), 0.4, 0.0, 0.0, 0.0, mat_beacon_glow)])
print("[plaza] 中心广场完成")

# 放射状路网：中心 → 每区（沿径向）
for zid, ang in ZONES:
    th=math.radians(ang)
    r0, r1 = PLAZA_R+1.0, R_ZONE-TILE/2-1.0
    rm=(r0+r1)/2.0; length=r1-r0
    px=rm*math.sin(th); py=rm*math.cos(th)
    yaw=math.degrees(math.atan2(math.cos(th), math.sin(th)))  # 长边指向径向
    add_multi("U_path_Z%02d"%zid, [
        (*prim_box(length, 3.0, 0.22, r=0.3, seg=2), 0.22, px, py, yaw, mat_path)])
print("[path] 放射路网完成")

# 绿化：草坪 + 草丛 + 灌木 + 小花 + 树 -------------------------------------
# 原来地基只有地块与路网，地面本身是"空"的（Web 里透出背景色 + 一条网格线），
# 远景看着像水泥荒漠。这里补一块起伏草坪，再用大量低面数的"绒毛"堆出
# 草木旺盛、毛茸茸的感觉。
mat_lawn  = ensure_mat("LBG_lawn",  (0.19,0.40,0.19), (0.05,0.11,0.05), 0.06, rough=0.96)
mat_lawn2 = ensure_mat("LBG_lawn2", (0.24,0.48,0.23), (0.06,0.13,0.06), 0.06, rough=0.96)
mat_grass1= ensure_mat("LBG_grass1",(0.33,0.60,0.25), (0.06,0.13,0.05), 0.08, rough=0.95)
mat_grass2= ensure_mat("LBG_grass2",(0.43,0.71,0.29), (0.08,0.16,0.06), 0.10, rough=0.95)
mat_grass3= ensure_mat("LBG_grass3",(0.25,0.50,0.21), (0.05,0.11,0.05), 0.08, rough=0.95)
mat_bush  = ensure_mat("LBG_bush",  (0.21,0.45,0.23), (0.05,0.12,0.05), 0.07, rough=0.93)
mat_leaf2 = ensure_mat("LBG_leaf2", (0.25,0.53,0.25), (0.06,0.13,0.05), 0.08, rough=0.93)
mat_leaf3 = ensure_mat("LBG_leaf3", (0.35,0.65,0.29), (0.08,0.16,0.06), 0.10, rough=0.93)
mat_flower= ensure_mat("LBG_flower",(0.96,0.93,0.74), (0.34,0.31,0.17), 0.40, rough=0.55)


def prim_disc(r, rings=6, seg=48, noise=0.0, seed=0, flat_r=0.0):
    """圆盘（同心环）。noise 给顶点加轻微起伏避免死平；
    flat_r 半径以内保持水平，免得草坪拱起来穿过中心广场和路面。"""
    rr_ = random.Random(seed)
    v = [(0.0, 0.0, 0.0)]
    for ri in range(1, rings + 1):
        R = r * ri / rings
        k = 1.0 if flat_r <= 0 else max(0.0, min(1.0, (R - flat_r) / 14.0))
        for si in range(seg):
            a = 2 * math.pi * si / seg
            z = 0.0
            if noise and k > 0.0:
                z = (math.sin(a * 3.0 + ri * 1.7) * 0.55
                     + math.sin(a * 7.0 + ri * 2.3) * 0.30
                     + (rr_.random() - 0.5) * 0.8) * noise * k
            v.append((R * math.cos(a), R * math.sin(a), z))
    f = []
    for si in range(seg):
        f.append((0, 1 + si, 1 + (si + 1) % seg))
    for ri in range(rings - 1):
        a0 = 1 + ri * seg; b0 = 1 + (ri + 1) * seg
        for si in range(seg):
            sj = (si + 1) % seg
            f.append((a0 + si, b0 + si, b0 + sj, a0 + sj))
    return v, f


# 草坪：两层叠出轻微色带，外圈比内圈稍亮
add_multi("U_lawn", [
    (*prim_disc(FENCE_R + 9.0, 8, 64, 0.55, 11, PLAZA_R + 4.0), -0.25, 0.0, 0.0, 0.0, mat_lawn),
    (*prim_disc(FENCE_R + 3.0, 6, 48, 0.40, 22, PLAZA_R + 4.0), -0.16, 0.0, 0.0, 0.0, mat_lawn2)])
print("[lawn] 草坪完成 · 半径", FENCE_R + 9.0)

# 绿化散布：避开地块 / 广场 / 围栏 / 放射路网
def blocked(x, y, pad=0.0):
    rr = x * x + y * y
    if rr > (FENCE_R - 3.0) ** 2: return True
    if rr < (PLAZA_R + 3.0) ** 2: return True
    for r in TILE_RECTS:
        if (r[0] - pad) <= x <= (r[2] + pad) and (r[1] - pad) <= y <= (r[3] + pad): return True
    return False


def on_road(x, y, pad=0.0):
    rad = math.hypot(x, y)
    if rad < PLAZA_R + 0.5 or rad > R_ZONE - TILE / 2.0 + 0.5: return False
    a = math.degrees(math.atan2(x, y)) % 360.0        # 与 zone_xy_blender 同向
    for _zid, zang in ZONES:
        d = abs((a - zang + 180.0) % 360.0 - 180.0)
        half = math.degrees(math.atan2(1.5 + pad, max(1.0, rad)))
        if d <= half: return True
    return False

rng = random.Random(SEED + 7)
def scatter(count, r0, r1, pad):
    out = []
    for _ in range(count * 16):
        if len(out) >= count: break
        ang = rng.uniform(0, 360); rad = rng.uniform(r0, r1)
        x = rad * math.sin(math.radians(ang)); y = rad * math.cos(math.radians(ang))
        if blocked(x, y, pad=pad): continue
        if on_road(x, y, pad=0.9): continue
        out.append((x, y))
    return out

GR = [mat_grass1, mat_grass2, mat_grass3]

# —— 草丛：数量最多，成片铺满草坪 ——
spots = scatter(1250, 16.0, FENCE_R - 2.0, 1.2)
bucket = []; gi = 0; blades = 0
for (x, y) in spots:
    s = rng.uniform(0.75, 1.35)
    for _ in range(rng.randint(3, 5)):
        ox = rng.uniform(-0.36, 0.36) * s; oy = rng.uniform(-0.36, 0.36) * s
        h = rng.uniform(0.50, 1.05) * s; r = rng.uniform(0.06, 0.12) * s
        bucket.append((*prim_cone(r, h, 5), -0.55, x + ox, y + oy,
                       rng.uniform(0, 360), GR[rng.randrange(3)]))
        blades += 1
    if rng.random() < 0.55:                            # 一小团软底绒
        rr = rng.uniform(0.22, 0.40) * s
        bucket.append((*prim_sphere(rr * 0.7, 6, 4), -0.45,
                       x + rng.uniform(-0.2, 0.2), y + rng.uniform(-0.2, 0.2), 0.0, GR[rng.randrange(3)]))
    if len(bucket) >= 70:
        add_multi("G_grass_%02d" % gi, bucket); gi += 1; bucket = []
if bucket: add_multi("G_grass_%02d" % gi, bucket); gi += 1
print("[grass] 草丛对象 =", gi, "· 草叶 =", blades)

# —— 灌木丛：圆润一坨，3~5 瓣 ——
spots = scatter(120, 17.0, FENCE_R - 4.0, 2.4)
bucket = []; bi = 0
for (x, y) in spots:
    s = rng.uniform(0.9, 1.9)
    bucket.append((*prim_sphere(0.95 * s, 9, 6), -0.35, x, y, 0.0, mat_bush))
    for _ in range(rng.randint(2, 4)):
        rr = rng.uniform(0.45, 0.80) * s
        bucket.append((*prim_sphere(rr, 8, 5), -0.30 + rng.uniform(0.10, 0.50) * s,
                       x + rng.uniform(-0.7, 0.7) * s, y + rng.uniform(-0.7, 0.7) * s, 0.0,
                       mat_bush if rng.random() < 0.6 else mat_leaf2))
    if rng.random() < 0.45:
        bucket.append((*prim_sphere(0.50 * s, 7, 4), -0.20,
                       x + rng.uniform(-0.3, 0.3) * s, y + rng.uniform(-0.3, 0.3) * s, 0.0, mat_leaf3))
    if len(bucket) >= 36:
        add_multi("G_bush_%02d" % bi, bucket); bi += 1; bucket = []
if bucket: add_multi("G_bush_%02d" % bi, bucket); bi += 1
print("[bush] 灌木对象 =", bi)

# —— 小花点：稀疏亮色点缀，给"鲜艳"一点细节 ——
spots = scatter(230, 16.5, FENCE_R - 3.0, 1.6)
parts = []; fi = 0
for (x, y) in spots:
    for _ in range(rng.randint(2, 4)):
        parts.append((*prim_sphere(0.10, 5, 3), rng.uniform(0.35, 0.80),
                      x + rng.uniform(-0.4, 0.4), y + rng.uniform(-0.4, 0.4), 0.0, mat_flower))
    if len(parts) >= 60:
        add_multi("G_flower_%02d" % fi, parts); fi += 1; parts = []
if parts: add_multi("G_flower_%02d" % fi, parts); fi += 1
print("[flower] 花点对象 =", fi)

# —— 树：4~7 个球错落叠成蓬松树冠（原来只有 2 个球，太瘦） ——
spots = scatter(78, 19.0, FENCE_R - 4.0, 3.0)
ti = 0
for (x, y) in spots:
    s = rng.uniform(0.85, 1.5)
    parts = [(*prim_cyl(0.26 * s, 1.4 * s, 7), 0.0, x, y, 0.0, mat_trunk)]
    for _ in range(rng.randint(4, 7)):
        rr = rng.uniform(0.80, 1.35) * s
        m = [mat_leaf, mat_leaf2, mat_leaf3][rng.randrange(3)]
        parts.append((*prim_sphere(rr, 9, 6), rng.uniform(1.9, 3.4) * s,
                      x + rng.uniform(-0.85, 0.85) * s, y + rng.uniform(-0.85, 0.85) * s, 0.0, m))
    parts.append((*prim_sphere(0.72 * s, 8, 5), 3.6 * s,
                  x + rng.uniform(-0.2, 0.2), y + rng.uniform(-0.2, 0.2), 0.0, mat_leaf3))
    add_multi("G_tree_%02d" % ti, parts); ti += 1
print("[trees] 树 =", ti)

# ------------------------------------------------------------------ 导出
bpy.ops.export_scene.gltf(
    filepath=OUT, export_format='GLB', use_selection=False,
    export_apply=True, export_yup=True,
    export_cameras=False, export_lights=False,
)
print("[export]", OUT, "%.2f MB" % (os.path.getsize(OUT)/1048576.0))
print("[done]")
