# -*- coding: utf-8 -*-
"""
生成「学习备考区」室内剖面场景（diorama）样板。
参考用户提供的目标样式视频：两墙开放剖面 + 满墙书架 + 木桌椅 + CRT 电脑 + 绿植。

产物（独立，不触碰现有沙盘模型）：
  assets/lumina/room_study.glb
  output/room_study.png   （等距俯视预览）

用法：
  blender --background --factory-startup --python tools/build_room.py
"""
import bpy, bmesh, math, os, random, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_GLB = os.path.join(ROOT, "assets", "lumina", "room_study.glb")
OUT_PNG = os.path.join(ROOT, "output", "room_study.png")
SEED = 20261007
random.seed(SEED)

# ============================================================
# 0. 基本设置
# ============================================================
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'

# 房间尺度（沙盘单位；1 单位 ≈ 1 米）
RW = 10.0          # 地面 X 向宽度
RD = 10.0          # 地面 Z 向深度
WT = 0.26          # 墙厚
WH = 6.0           # 墙高
FT = 0.34          # 地面厚（做出模型底座的厚度感）

# ============================================================
# 1. 材质
# ============================================================
def mk_mat(name, rgb, rough=0.75, emis=None, emis_str=0.0, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = metal
    if emis:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (emis[0], emis[1], emis[2], 1.0)
        elif "Emission" in bsdf.inputs:
            bsdf.inputs["Emission"].default_value = (emis[0], emis[1], emis[2], 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emis_str
    return m

M = {}
M["wall"]   = mk_mat("mat_R01_wall",   (0.855, 0.825, 0.775), 0.92)
M["floor"]  = mk_mat("mat_R01_floor",  (0.620, 0.445, 0.275), 0.70)
M["rug"]    = mk_mat("mat_R01_rug",    (0.880, 0.845, 0.775), 0.97)
M["blind"]  = mk_mat("mat_R01_blind",  (0.925, 0.930, 0.935), 0.60)
M["glass"]  = mk_mat("mat_R01_glass",  (0.760, 0.840, 0.900), 0.22)
M["trim"]   = mk_mat("mat_R01_trim",   (0.520, 0.345, 0.185), 0.68)
M["wood_d"] = mk_mat("mat_R01_wood_dark", (0.330, 0.205, 0.115), 0.62)
M["wood_m"] = mk_mat("mat_R01_wood",      (0.645, 0.435, 0.215), 0.58)
M["wood_l"] = mk_mat("mat_R01_wood_light",(0.735, 0.560, 0.335), 0.62)
M["chair"]  = mk_mat("mat_R01_chair",  (0.870, 0.420, 0.155), 0.78)
M["leaf"]   = mk_mat("mat_R01_leaf",   (0.180, 0.470, 0.190), 0.74)
M["pot"]    = mk_mat("mat_R01_pot",    (0.400, 0.245, 0.590), 0.64)
M["metal"]  = mk_mat("mat_R01_metal",  (0.520, 0.525, 0.550), 0.42, metal=0.65)
M["screen"] = mk_mat("mat_R01_screen", (0.095, 0.105, 0.120), 0.32)
M["paper"]  = mk_mat("mat_R01_paper",  (0.915, 0.905, 0.865), 0.90)
# 书本 8 色
BOOK_RGB = [
    (0.72, 0.22, 0.20), (0.20, 0.35, 0.62), (0.24, 0.52, 0.32),
    (0.78, 0.62, 0.22), (0.46, 0.28, 0.55), (0.80, 0.45, 0.18),
    (0.22, 0.50, 0.55), (0.62, 0.20, 0.38),
]
for i, c in enumerate(BOOK_RGB):
    M["book%d" % i] = mk_mat("mat_R01_book%d" % i, c, 0.85)

# ============================================================
# 2. 几何原语（纯 verts/faces，供合并器使用）
# ============================================================
def prim_box(sx, sy, sz, r=0.0, seg=2):
    """中心在原点的盒；r>0 时用 bmesh 倒角做圆角。"""
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
    rr = min(r, hx - 0.01, hy - 0.01, hz - 0.01)
    if rr <= 0.015:
        v = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
             (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        return v, f
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for vv in bm.verts:
        vv.co.x *= sx; vv.co.y *= sy; vv.co.z *= sz
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=rr, segments=seg,
                    profile=0.5, affect='EDGES', clamp_overlap=True)
    bm.verts.ensure_lookup_table()
    verts = [tuple(vv.co) for vv in bm.verts]
    bm.faces.ensure_lookup_table()
    faces = [tuple(l.vert.index for l in fc.loops) for fc in bm.faces]
    bm.free()
    return verts, faces

def prim_cyl(r, h, seg=16):
    v, f = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        v.append((r * math.cos(a), r * math.sin(a), -h / 2))
    for i in range(seg):
        a = 2 * math.pi * i / seg
        v.append((r * math.cos(a), r * math.sin(a), h / 2))
    for i in range(seg):
        j = (i + 1) % seg
        f.append((i, j, seg + j, seg + i))
    f.append(tuple(range(seg - 1, -1, -1)))
    f.append(tuple(range(seg, 2 * seg)))
    return v, f

def prim_sphere(r, seg=12, rings=6):
    v, f = [], []
    v.append((0, 0, r))
    for j in range(1, rings):
        phi = math.pi * j / rings
        z = r * math.cos(phi); rr = r * math.sin(phi)
        for i in range(seg):
            a = 2 * math.pi * i / seg
            v.append((rr * math.cos(a), rr * math.sin(a), z))
    v.append((0, 0, -r))
    bottom = len(v) - 1
    for i in range(seg):
        f.append((0, 1 + (i + 1) % seg, 1 + i))
    for j in range(rings - 2):
        a0 = 1 + j * seg; a1 = 1 + (j + 1) * seg
        for i in range(seg):
            f.append((a0 + i, a0 + (i + 1) % seg, a1 + (i + 1) % seg, a1 + i))
    a0 = 1 + (rings - 2) * seg
    for i in range(seg):
        f.append((bottom, a0 + i, a0 + (i + 1) % seg))
    return v, f

# ============================================================
# 3. 合并器：把成百上千个小件拼成一个多材质 mesh，省 draw call
# ============================================================
class Accum:
    def __init__(self, name):
        self.name = name
        self.v, self.f, self.fm = [], [], []

    def add(self, verts, faces, mat, cx=0.0, cy=0.0, z0=0.0, rotz=0.0):
        """把局部几何按 (rotz, +cx,+cy, z0) 摆到世界，并登记材质。"""
        ca, sa = math.cos(rotz), math.sin(rotz)
        off = len(self.v)
        for (x, y, z) in verts:
            xr = x * ca - y * sa
            yr = x * sa + y * ca
            self.v.append((xr + cx, yr + cy, z + z0))
        for fc in faces:
            self.f.append(tuple(i + off for i in fc))
            self.fm.append(mat)

    def box(self, sx, sy, sz, cx, cy, z0, mat, rotz=0.0, r=0.0):
        v, f = prim_box(sx, sy, sz, r=r)
        self.add(v, f, mat, cx, cy, z0, rotz)

    def cyl(self, r_, h, cx, cy, z0, mat, seg=16):
        v, f = prim_cyl(r_, h, seg)
        self.add(v, f, mat, cx, cy, z0)

    def sphere(self, r_, cx, cy, z0, mat, seg=12, rings=6):
        v, f = prim_sphere(r_, seg, rings)
        self.add(v, f, mat, cx, cy, z0)

    def build(self):
        """按「短键名 → M 字典里的真实材质」建多材质槽 mesh。"""
        mats = []
        for k in self.fm:
            if k not in mats:
                mats.append(k)
        me = bpy.data.meshes.new(self.name)
        me.from_pydata(self.v, [], self.f)
        me.validate(verbose=False)
        me.update()
        idx = {}
        for i, k in enumerate(mats):
            mat = M.get(k)
            if mat is None:
                raise KeyError("未定义的材质键: " + k)
            me.materials.append(mat)
            idx[k] = i
        for i, p in enumerate(me.polygons):
            p.material_index = idx[self.fm[i]]
            p.use_smooth = False
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.collection.objects.link(ob)
        return ob

# ============================================================
# 4. 构建房间
# ============================================================
def build_shell():
    """地板 + 两面墙 + 百叶窗"""
    a = Accum("R01_shell")
    # 木地板（略大一点点，形成台面外沿）
    a.box(RW + 0.6, RD + 0.6, FT, 0, 0, -FT, "floor")
    # 地毯：铺在中央的一大块
    a.box(RW - 3.4, RD - 3.2, 0.05, 0.05, 0.55, 0, "rug")
    # 踢脚线（沿两面墙底部）
    a.box(RW + 0.6, 0.10, 0.30, 0, -RD / 2 + 0.05, 0, "trim")
    a.box(0.10, RD + 0.6, 0.30, RW / 2 - 0.05, 0, 0, "trim")

    # 后墙：沿 X，位于 z = -RD/2
    a.box(RW + 0.6, WT, WH, 0, -RD / 2 - WT / 2 + 0.13, 0, "wall")
    # 右墙：沿 Z，位于 x = +RW/2
    a.box(WT, RD + 0.6, WH, RW / 2 + WT / 2 - 0.13, 0, 0, "wall")

    # 右墙上的两扇百叶窗（朝 -X 面的浅浮雕框 + 白色叶片）
    for wz, ww, wh in ((-2.1, 2.3, 1.7), (1.4, 2.3, 1.7)):
        x_in = RW / 2 - 0.02            # 墙面内侧
        zc = wz
        y0 = 3.55                        # 窗底高度
        # 外框
        a.box(0.16, ww + 0.26, wh + 0.26, x_in - 0.05, zc, y0 - 0.13, "wall")
        # 玻璃底（深色）
        a.box(0.06, ww, wh, x_in - 0.11, zc, y0, "glass")
        # 百叶叶片（水平条纹）
        n_lame = 9
        for k in range(n_lame):
            yy = y0 + wh * (k + 0.5) / n_lame
            a.box(0.11, ww, wh / n_lame * 0.52, x_in - 0.10, zc, yy - wh / n_lame * 0.26, "blind")
    return a.build()

def build_bookshelf(a, cx, cz, rotz=0.0):
    """一座书架：侧板 + 背板 + 层板 + 满架彩色书"""
    W, D, H = 2.40, 0.70, 4.05
    t = 0.13
    # 侧板
    a.box(t, D, H, cx - W / 2 + t / 2, cz, 0, "wood_d", rotz)
    a.box(t, D, H, cx + W / 2 - t / 2, cz, 0, "wood_d", rotz)
    # 背板
    a.box(W, 0.08, H, cx, cz - D / 2 + 0.04, 0, "wood_d", rotz)
    # 顶板 / 底板
    a.box(W, D, t, cx, cz, 0, "wood_d", rotz)
    a.box(W, D, t, cx, cz, H - t, "wood_d", rotz)
    # 层板 + 书
    n_shelf = 6
    inner_w = W - 2 * t
    for s in range(n_shelf):
        zb = 0.30 + s * ((H - 0.45) / n_shelf)
        a.box(inner_w, D - 0.06, 0.075, cx, cz, zb - 0.075, "wood_d", rotz)
        # 书：随机宽度/高度/颜色，竖排，偶尔倾斜
        x = -inner_w / 2 + 0.05
        while x < inner_w / 2 - 0.06:
            bw = random.uniform(0.055, 0.105)
            bh = random.uniform(0.34, 0.50)
            if x + bw > inner_w / 2 - 0.05:
                break
            col = "book%d" % random.randrange(len(BOOK_RGB))
            bx = cx + x + bw / 2
            # 少量书做成倾斜（靠倒）
            if random.random() < 0.10:
                # 斜放：用一个略转的盒近似
                a.box(bw, D - 0.14, bh, bx, cz + 0.02, zb, col, rotz + random.uniform(-0.13, 0.13))
            else:
                a.box(bw, D - 0.14, bh, bx, cz + 0.02, zb, col, rotz)
            x += bw + random.uniform(0.004, 0.016)

def build_desk(a, cx, cz, rotz=0.0):
    """靠墙书桌 + CRT 电脑 + 书"""
    W, D, H = 1.38, 3.30, 0.90   # W 沿 X（进深方向），D 沿 Z（长度）
    top_t = 0.09
    # 桌面
    a.box(W, D, top_t, cx, cz, H - top_t, "wood_m", rotz)
    # 四腿
    for dx in (-1, 1):
        for dz in (-1, 1):
            a.box(0.10, 0.10, H - top_t,
                  cx + dx * (W / 2 - 0.10), cz + dz * (D / 2 - 0.12),
                  0, "wood_m", rotz)
    # 侧挡板（更实心，像视频里的木桌）
    a.box(W - 0.06, 0.07, H - top_t - 0.06, cx, cz - D / 2 + 0.10, 0, "wood_m", rotz)

    # ---- CRT 电脑（机身 + 屏幕 + 底座 + 键盘）----
    mon_x, mon_z = cx - 0.06, cz - 0.55
    base_y = H
    a.box(0.82, 0.72, 0.10, mon_x, mon_z, base_y, "paper")          # 底座
    a.box(0.78, 0.68, 0.62, mon_x, mon_z - 0.05, base_y + 0.10, "paper", r=0.05)  # 机身
    a.box(0.05, 0.56, 0.44, mon_x - 0.40, mon_z - 0.05, base_y + 0.20, "screen")  # 屏幕（朝 -X）
    a.box(0.22, 0.44, 0.05, mon_x - 0.16, mon_z + 0.46, base_y + 0.005, "screen")  # 键盘
    # 主机/杂物盒
    a.box(0.30, 0.34, 0.30, cx + 0.30, cz + 0.62, base_y, "metal", r=0.03)

    # 桌上书堆
    bs = [("book2", 0.46, 0.34), ("book5", 0.42, 0.31), ("book1", 0.44, 0.33)]
    zz = base_y
    for k, (bcol, bl, bw) in enumerate(bs):
        a.box(bl, bw, 0.055, cx - 0.02, cz + 1.20, zz, bcol, rotz + 0.06 * (k % 2))
        zz += 0.062

def build_chair(a, cx, cz, rotz=0.0):
    """木椅 + 橙色坐垫"""
    seat = 0.58
    H = 0.52
    leg = 0.10
    for dx in (-1, 1):
        for dz in (-1, 1):
            a.box(leg, leg, H, cx + dx * (seat / 2 - leg / 2), cz + dz * (seat / 2 - leg / 2), 0, "wood_d", rotz)
    a.box(seat, seat, 0.10, cx, cz, H, "wood_d", rotz, r=0.03)
    a.box(seat - 0.04, seat - 0.04, 0.10, cx, cz, H + 0.10, "chair", rotz, r=0.04)
    # 靠背
    a.box(seat, 0.10, 0.80, cx, cz - seat / 2 + 0.06, H + 0.20, "wood_d", rotz, r=0.03)
    a.box(seat - 0.06, 0.12, 0.54, cx, cz - seat / 2 + 0.11, H + 0.34, "chair", rotz, r=0.05)

def build_table(a, cx, cz):
    """中央大木桌 + 桌上书堆"""
    W, D, H = 3.60, 2.50, 0.90
    top_t = 0.12
    a.box(W, D, top_t, cx, cz, H - top_t, "wood_m", r=0.05)
    for dx in (-1, 1):
        for dz in (-1, 1):
            a.box(0.17, 0.17, H - top_t,
                  cx + dx * (W / 2 - 0.28), cz + dz * (D / 2 - 0.28), 0, "wood_m")
    # 桌下横撑
    a.box(W - 0.5, 0.09, 0.09, cx, cz, H - 0.32, "wood_m")
    # 桌上书堆（像视频里那一摞）
    zz = H
    for k, (bcol, bl, bw) in enumerate([("book1", 0.62, 0.46), ("book4", 0.58, 0.43),
                                        ("book7", 0.55, 0.41), ("book3", 0.50, 0.38)]):
        a.box(bl, bw, 0.06, cx - 0.55 + 0.04 * (k % 2), cz + 0.10, zz, bcol, 0.10 * (k % 3 - 1))
        zz += 0.066

def build_plant(a, cx, cz):
    """绿植：紫盆 + 三团叶球"""
    a.cyl(0.30, 0.42, cx, cz, 0, "pot", 14)
    a.cyl(0.24, 0.10, cx, cz, 0.40, "leaf", 14)
    a.sphere(0.46, cx, cz, 0.72, "leaf", 12, 6)
    a.sphere(0.30, cx + 0.26, cz - 0.16, 0.86, "leaf", 10, 5)
    a.sphere(0.26, cx - 0.22, cz + 0.18, 0.80, "leaf", 10, 5)

def build_room():
    build_shell()

    furn = Accum("R01_furniture")
    # 两座书架靠后墙
    build_bookshelf(furn, -3.30, -RD / 2 + 0.55)
    build_bookshelf(furn, -0.75, -RD / 2 + 0.55)
    # 中央大木桌
    build_table(furn, -1.05, 0.55)
    # 两把椅子（一前一侧，像视频）
    build_chair(furn, -1.00, 2.05, rotz=math.pi)
    build_chair(furn, 1.35, 0.30, rotz=-math.pi / 2)
    # 靠右墙书桌
    build_desk(furn, RW / 2 - 0.95, 0.95)
    furn.build()

    props = Accum("R01_props")
    # 书架旁的小绿植
    build_plant(props, 1.35, -RD / 2 + 0.85)
    # 桌上小摆件
    props.build()

    # 近端矮柜（视频右侧靠墙矮柜）
    cab = Accum("R01_cabinet")
    # 靠窗那面墙的矮柜（沿 Z 摆放），远离书架视线
    cab.box(0.74, 2.30, 1.12, RW / 2 - 0.62, -2.70, 0, "wood_d", r=0.05)
    cab.box(0.64, 2.12, 0.07, RW / 2 - 0.62, -2.70, 1.12, "wood_m", r=0.03)
    cab.build()

# ============================================================
# 5. 灯光 / 相机 / 渲染
# ============================================================
def setup_scene_light():
    world = bpy.data.worlds.new("W")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.52, 0.56, 0.64, 1.0)
    bg.inputs[1].default_value = 0.36

    sun_d = bpy.data.lights.new("sun", 'SUN')
    sun_d.energy = 5.4
    sun_d.color = (1.0, 0.955, 0.895)
    sun_d.angle = math.radians(7)
    sun_o = bpy.data.objects.new("sun", sun_d)
    sun_o.rotation_euler = (math.radians(50), 0, math.radians(-124))
    bpy.context.collection.objects.link(sun_o)

    fill_d = bpy.data.lights.new("fill", 'AREA')
    fill_d.energy = 260
    fill_d.size = 18
    fill_d.color = (1.0, 0.965, 0.915)
    fill_o = bpy.data.objects.new("fill", fill_d)
    fill_o.location = (-11, 9, 9)
    from mathutils import Vector as _V
    fill_o.rotation_euler = (_V((0, 0, 1.8)) - fill_o.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.collection.objects.link(fill_o)

def render_view(name, loc, target, ortho=None, lens=58, res=(1200, 900)):
    """渲染一个视角到 output/<name>.png（用完即删相机）"""
    from mathutils import Vector
    cd = bpy.data.cameras.new("cam_" + name)
    if ortho:
        cd.type = 'ORTHO'
        cd.ortho_scale = ortho
    else:
        cd.lens = lens
    co = bpy.data.objects.new("cam_" + name, cd)
    bpy.context.collection.objects.link(co)
    co.location = Vector(loc)
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = co
    scene.render.resolution_x, scene.render.resolution_y = res
    path = os.path.join(ROOT, "output", name + ".png")
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("[render]", path)
    bpy.data.objects.remove(co, do_unlink=True)

def render_preview():
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        scene.render.engine = 'BLENDER_EEVEE'
    scene.render.film_transparent = False
    if hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 64
    for lk in ("AgX - Punchy", "Punchy", "AgX - Medium High Contrast"):
        try:
            scene.view_settings.look = lk
            print("[render] look =", lk)
            break
        except Exception:
            continue
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    # 正片：等距俯视（对齐参考视频机位）
    render_view("room_study", (-15.2, 16.2, 12.6), (-0.4, -0.2, 2.1), lens=56, res=(1440, 960))
    # 诊断三视图（正交，用来核对几何）
    render_view("dbg_top",   (0, 0.01, 30), (0, 0, 0),   ortho=13, res=(1000, 1000))
    render_view("dbg_front", (0, 26, 3.2),  (0, 0, 3.2), ortho=13)
    render_view("dbg_side",  (-26, 0, 3.2), (0, 0, 3.2), ortho=13)

# ============================================================
# 6. 主流程
# ============================================================
build_room()
setup_scene_light()

objs = [o for o in bpy.data.objects if o.type == 'MESH']
tris = sum(len(o.data.polygons) for o in objs)
print("[room] objects =", len(objs), " faces =", tris)
for o in objs:
    print("   -", o.name, len(o.data.polygons), "faces,", len(o.data.materials), "mats")

os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=OUT_GLB,
    export_format='GLB',
    use_selection=False,
    export_apply=True,
    export_yup=True,
)
print("[export]", OUT_GLB, "%.2f MB" % (os.path.getsize(OUT_GLB) / 1048576.0))

render_preview()
print("[done]")
