# -*- coding: utf-8 -*-
"""
「微光社区」10 区室内剖面房间沙盘生成器（方案 A：房间盒替换方块楼）

每区一间「两墙开放剖面」的房间，围成一圈（R=60），开口一律朝向中央广场，
从广场方向就能看进每间房的内部。

配色：较上一版样板整体压暗、提饱和（用户反馈「太淡太亮」）。
昼夜：每个对象生成两份，xxx（夜）/ xxx_day（昼），前端按可见性切换。

产物：
  assets/lumina/lumina_rooms.glb
  output/rooms_day.png  output/rooms_night.png  output/rooms_close.png

用法：
  blender --background --factory-startup --python tools/build_rooms.py
"""
import bpy, bmesh, math, os, random, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_GLB = os.path.join(ROOT, "assets", "lumina", "lumina_rooms.glb")
OUT_DIR = os.path.join(ROOT, "output")
SEED = 20261007

# ============================================================
# 0. 基本设置
# ============================================================
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'

# 房间本体尺寸（本地坐标，中心在原点）
RW = 10.0          # X 向宽
RD = 10.0          # Y 向深
WT = 0.28          # 墙厚
WH = 6.0           # 墙高（每区会微调，制造高低错落）
FT = 0.54          # 地板/底座厚度（微缩模型底座感）

R_RING = 60.0      # 环半径（与 build_city.py 的 R_ZONE 一致）
DAY_SUFFIX = "_day"

# ============================================================
# 1. 分区定义（与 js/zones.js 严格一致）
# ============================================================
ZONES = [
    # id, key, 名称,          主题色(rgb),          角度,   墙高,  缩放
    (1,  'study',    '学习备赛区', (1.00, 0.82, 0.40),   0.0, 4.80, 1.34),
    (2,  'arcade',   '游戏娱乐区', (1.00, 0.36, 0.66),  35.5, 4.20, 1.28),
    (3,  'market',   '餐饮美食区', (1.00, 0.62, 0.36),  71.6, 3.90, 1.30),
    (4,  'sport',    '体育运动区', (0.36, 0.88, 0.90), 108.4, 5.40, 1.42),
    (5,  'workshop', '工坊创客区', (0.70, 0.53, 1.00), 144.5, 4.40, 1.32),
    (6,  'music',    '音乐艺术区', (1.00, 0.42, 0.42), 180.0, 4.60, 1.30),
    (7,  'garden',   '花园冥想区', (0.49, 0.99, 0.61), 215.5, 3.60, 1.38),
    (8,  'animal',   '动物守护区', (0.78, 0.60, 0.42), 251.6, 4.00, 1.26),
    (9,  'volunteer','志愿服务区', (1.00, 0.36, 0.36), 288.4, 4.70, 1.30),
    (10, 'clean',    '卫生打扫区', (0.30, 0.82, 0.88), 324.5, 4.30, 1.28),
]

# ============================================================
# 2. 材质（深色调 · 昼夜两套）
# ============================================================
def mk_mat(name, rgb, rough=0.78, emis=None, emis_str=0.0, metal=0.0):
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

# —— 白天：压暗提饱和的暖色调（相对上一版样板明显加深）——
DAY_BASE = {
    "wall":   ((0.455, 0.408, 0.340), 0.94),
    "floor":  ((0.270, 0.152, 0.066), 0.72),
    "trim":   ((0.205, 0.115, 0.048), 0.70),
    "blind":  ((0.520, 0.535, 0.560), 0.62),
    "glass":  ((0.180, 0.300, 0.410), 0.18),
    "wood_d": ((0.105, 0.058, 0.026), 0.64),
    "wood_m": ((0.285, 0.160, 0.062), 0.60),
    "wood_l": ((0.400, 0.245, 0.108), 0.64),
    "metal":  ((0.310, 0.320, 0.340), 0.40),
    "screen": ((0.038, 0.042, 0.050), 0.30),
    "paper":  ((0.585, 0.560, 0.512), 0.92),
    "leaf":   ((0.078, 0.240, 0.092), 0.78),
    "pot":    ((0.215, 0.108, 0.310), 0.66),
    "soil":   ((0.120, 0.078, 0.046), 0.95),
    "stone":  ((0.330, 0.318, 0.292), 0.92),
    "water":  ((0.095, 0.225, 0.340), 0.12),
    "white":  ((0.610, 0.605, 0.590), 0.80),
    "gray":   ((0.235, 0.240, 0.250), 0.75),
    "dark":   ((0.072, 0.075, 0.082), 0.62),
    "red":    ((0.545, 0.090, 0.090), 0.75),
    "green":  ((0.095, 0.320, 0.140), 0.78),
    "blue":   ((0.095, 0.210, 0.470), 0.75),
    "yellow": ((0.640, 0.490, 0.080), 0.78),
    "orange": ((0.630, 0.300, 0.062), 0.76),
    "cyan":   ((0.085, 0.390, 0.470), 0.72),
    "purple": ((0.310, 0.160, 0.440), 0.76),
    "pink":   ((0.620, 0.200, 0.340), 0.78),
}
# 书本 8 色（加深版）
BOOK_RGB = [
    (0.400, 0.088, 0.080), (0.082, 0.165, 0.350), (0.085, 0.270, 0.140),
    (0.430, 0.320, 0.070), (0.215, 0.115, 0.295), (0.430, 0.205, 0.058),
    (0.078, 0.245, 0.285), (0.320, 0.078, 0.175),
]

M = {}   # 全局材质表：短键 -> 真实材质

def make_mats(zid, theme, night):
    """按昼夜生成一整套材质到全局 M。night=True 时整体更暗且主题色/窗发光。"""
    M.clear()
    suf = "" if night else DAY_SUFFIX
    k = 0.74 if night else 1.0          # 夜间整体压暗系数
    for key, (rgb, rough) in DAY_BASE.items():
        c = tuple(min(1.0, v * k) for v in rgb)
        M[key] = mk_mat("mat_R%02d_%s%s" % (zid, key, suf), c, rough)
    # 主题色：白天实色，夜晚发光
    if night:
        M["theme"]  = mk_mat("mat_R%02d_theme" % zid,
                             tuple(v * 0.55 for v in theme), 0.62,
                             emis=theme, emis_str=2.4)
        M["theme2"] = mk_mat("mat_R%02d_theme2" % zid,
                             tuple(v * 0.35 for v in theme), 0.70,
                             emis=tuple(v * 0.8 for v in theme), emis_str=1.1)
        # 夜晚窗内暖光
        M["glass"] = mk_mat("mat_R%02d_glass" % zid, (0.520, 0.430, 0.250), 0.20,
                            emis=(1.0, 0.860, 0.620), emis_str=2.6)
        M["screen"] = mk_mat("mat_R%02d_screen" % zid, (0.120, 0.190, 0.240), 0.25,
                             emis=(0.450, 0.780, 0.900), emis_str=1.7)
        M["lamp"] = mk_mat("mat_R%02d_lamp" % zid, (0.700, 0.660, 0.560), 0.55,
                           emis=(1.0, 0.930, 0.780), emis_str=3.2)
    else:
        M["theme"]  = mk_mat("mat_R%02d_theme%s" % (zid, suf), theme, 0.70)
        M["theme2"] = mk_mat("mat_R%02d_theme2%s" % (zid, suf),
                             tuple(min(1.0, v * 0.72 + 0.06) for v in theme), 0.74)
        M["lamp"] = mk_mat("mat_R%02d_lamp%s" % (zid, suf), (0.850, 0.820, 0.740), 0.60)
    # 地毯 = 主题色调和后的深色（每区可覆盖）
    M["rug"] = mk_mat("mat_R%02d_rug%s" % (zid, suf),
                      tuple(min(1.0, v * 0.30 + 0.045) for v in theme), 0.95)
    for i, c in enumerate(BOOK_RGB):
        cc = tuple(min(1.0, v * (0.68 if night else 1.0)) for v in c)
        M["book%d" % i] = mk_mat("mat_R%02d_book%d%s" % (zid, i, suf), cc, 0.86)

# ============================================================
# 3. 几何原语
# ============================================================
def prim_box(sx, sy, sz, r=0.0, seg=2):
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
# 4. 合并器（按材质拼成单个多材质 mesh，大幅降 draw call）
# ============================================================
class Accum:
    def __init__(self, name):
        self.name = name
        self.v, self.f, self.fm = [], [], []

    def add(self, verts, faces, mat, cx=0.0, cy=0.0, z0=0.0, rotz=0.0):
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
        """z0 = 底面高度（内部换算为中心高度再摆位）"""
        v, f = prim_box(sx, sy, sz, r=r)
        self.add(v, f, mat, cx, cy, z0 + sz / 2.0, rotz)

    def cyl(self, r_, h, cx, cy, z0, mat, seg=16):
        """z0 = 底面高度"""
        v, f = prim_cyl(r_, h, seg)
        self.add(v, f, mat, cx, cy, z0 + h / 2.0)

    def sphere(self, r_, cx, cy, z0, mat, seg=12, rings=6):
        v, f = prim_sphere(r_, seg, rings)
        self.add(v, f, mat, cx, cy, z0)

    def build(self):
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
# 5. 通用家具零件库
# ============================================================
def f_shelf(a, cx, cy, rotz, w=2.4, d=0.70, h=4.05, n=6, mat="wood_d"):
    """货架/书架：侧板+背板+层板"""
    t = 0.13
    a.box(t, d, h, cx - w / 2 + t / 2, cy, 0, mat, rotz)
    a.box(t, d, h, cx + w / 2 - t / 2, cy, 0, mat, rotz)
    a.box(w, 0.08, h, cx, cy - d / 2 + 0.04, 0, mat, rotz)
    a.box(w, d, t, cx, cy, 0, mat, rotz)
    a.box(w, d, t, cx, cy, h - t, mat, rotz)
    iw = w - 2 * t
    for s in range(n):
        zb = 0.30 + s * ((h - 0.45) / n)
        a.box(iw, d - 0.06, 0.075, cx, cy, zb - 0.075, mat, rotz)

def f_books(a, cx, cy, rotz, w=2.14, d=0.56, h=4.05, n=6):
    """往货架里塞彩色书"""
    t = 0.13
    for s in range(n):
        zb = 0.30 + s * ((h - 0.45) / n) + 0.04
        x = -w / 2 + 0.05
        while x < w / 2 - 0.06:
            bw = random.uniform(0.055, 0.105)
            bh = random.uniform(0.32, 0.46)
            if x + bw > w / 2 - 0.05:
                break
            col = "book%d" % random.randrange(len(BOOK_RGB))
            tilt = random.uniform(-0.13, 0.13) if random.random() < 0.10 else rotz
            a.box(bw, d, bh, cx + x + bw / 2, cy, zb, col, tilt)
            x += bw + random.uniform(0.004, 0.016)

def f_table(a, cx, cy, w=3.6, d=2.5, h=0.90, rotz=0.0, mat="wood_m", leg="wood_m"):
    top_t = 0.12
    a.box(w, d, top_t, cx, cy, h - top_t, mat, rotz, r=0.05)
    for dx in (-1, 1):
        for dz in (-1, 1):
            a.box(0.17, 0.17, h - top_t, cx + dx * (w / 2 - 0.28),
                  cy + dz * (d / 2 - 0.28), 0, leg, rotz)
    a.box(w - 0.5, 0.09, 0.09, cx, cy, h - 0.32, mat, rotz)

def f_chair(a, cx, cy, rotz=0.0, seat_mat="theme", frame="wood_d", s=1.0):
    seat = 0.58 * s; H = 0.52 * s; leg = 0.10 * s
    for dx in (-1, 1):
        for dz in (-1, 1):
            a.box(leg, leg, H, cx + dx * (seat / 2 - leg / 2),
                  cy + dz * (seat / 2 - leg / 2), 0, frame, rotz)
    a.box(seat, seat, 0.10 * s, cx, cy, H, frame, rotz, r=0.03)
    a.box(seat - 0.04, seat - 0.04, 0.10 * s, cx, cy, H + 0.10 * s, seat_mat, rotz, r=0.04)
    a.box(seat, 0.10 * s, 0.80 * s, cx, cy - seat / 2 + 0.06, H + 0.20 * s, frame, rotz, r=0.03)
    a.box(seat - 0.06, 0.12 * s, 0.54 * s, cx, cy - seat / 2 + 0.11, H + 0.34 * s, seat_mat, rotz, r=0.05)

def f_stool(a, cx, cy, r=0.30, h=0.62, mat="theme", frame="wood_d"):
    a.cyl(r, 0.08, cx, cy, h, mat, 14)
    for i in range(3):
        ang = 2 * math.pi * i / 3 + 0.4
        a.box(0.08, 0.08, h, cx + 0.22 * r / 0.3 * 0.9 * math.cos(ang),
              cy + 0.22 * r / 0.3 * 0.9 * math.sin(ang), 0, frame)

def f_plant(a, cx, cy, s=1.0, pot="pot", leaf="leaf"):
    a.cyl(0.30 * s, 0.42 * s, cx, cy, 0, pot, 14)
    a.cyl(0.24 * s, 0.10 * s, cx, cy, 0.40 * s, leaf, 14)
    a.sphere(0.46 * s, cx, cy, 0.72 * s, leaf, 12, 6)
    a.sphere(0.30 * s, cx + 0.26 * s, cy - 0.16 * s, 0.86 * s, leaf, 10, 5)
    a.sphere(0.26 * s, cx - 0.22 * s, cy + 0.18 * s, 0.80 * s, leaf, 10, 5)

def f_crate(a, cx, cy, z0, s=0.62, mat="wood_l", rotz=0.0):
    a.box(s, s * 0.82, s * 0.68, cx, cy, z0, mat, rotz, r=0.03)
    a.box(s * 1.02, s * 0.10, s * 0.08, cx, cy, z0 + s * 0.30, "wood_d", rotz)

def f_sign(a, cx, cy, z0, w=1.7, h=1.1, rotz=0.0, post="metal", face="theme"):
    a.cyl(0.07, h, cx, cy, z0, post, 10)
    a.box(w, 0.10, h * 0.55, cx, cy, z0 + h * 0.50, face, rotz, r=0.04)

# ============================================================
# 6. 房间外壳（每区共用，材质可变）
# ============================================================
def build_shell(a, wh):
    """地板 + 两面墙 + 两扇百叶窗；开口朝 (-X, +Y) 对角"""
    a.box(RW + 0.6, RD + 0.6, 0.16, 0, 0, -0.16, "floor")
    a.box(RW + 1.0, RD + 1.0, FT - 0.16, 0, 0, -FT, "trim")
    a.box(RW - 4.2, RD - 4.0, 0.05, 0.05, 0.45, 0, "rug")
    # 地板边框（四边压深，收住台面轮廓）
    a.box(RW + 0.7, 0.22, 0.20, 0, RD / 2 + 0.05, -0.16, "trim")
    a.box(0.22, RD + 0.7, 0.20, -RW / 2 - 0.05, 0, -0.16, "trim")
    # 踢脚线
    a.box(RW + 0.6, 0.10, 0.30, 0, -RD / 2 + 0.05, 0, "trim")
    a.box(0.10, RD + 0.6, 0.30, RW / 2 - 0.05, 0, 0, "trim")
    # 后墙（沿 X，y=-RD/2）与右墙（沿 Y，x=+RW/2）
    a.box(RW + 0.6, WT, wh, 0, -RD / 2 - WT / 2 + 0.14, 0, "wall")
    a.box(WT, RD + 0.6, wh, RW / 2 + WT / 2 - 0.14, 0, 0, "wall")
    # 右墙上两扇百叶窗
    y0 = wh * 0.58
    for wz, ww, whh in ((-2.1, 2.3, 1.7), (1.4, 2.3, 1.7)):
        x_in = RW / 2 - 0.02
        a.box(0.16, ww + 0.26, whh + 0.26, x_in - 0.05, wz, y0 - 0.13, "wall")
        a.box(0.06, ww, whh, x_in - 0.11, wz, y0, "glass")
        n = 9
        for k in range(n):
            yy = y0 + whh * (k + 0.5) / n
            a.box(0.11, ww, whh / n * 0.52, x_in - 0.10, wz, yy - whh / n * 0.26, "blind")
    # 墙顶内侧细檐（贴墙，不外挑）
    a.box(RW + 0.6, 0.22, 0.18, 0, -RD / 2 + 0.11, wh - 0.18, "trim")
    a.box(0.22, RD + 0.6, 0.18, RW / 2 - 0.11, 0, wh - 0.18, "trim")

# ============================================================
# 7. 十区专属陈设
# ============================================================
def z01_study(a):
    """学习备考区：双书墙 + 大桌 + 书桌/CRT + 绿植 + 矮柜"""
    f_shelf(a, -3.30, -RD / 2 + 0.62, 0.0, h=4.6)
    f_shelf(a, -0.75, -RD / 2 + 0.62, 0.0, h=4.6)
    f_books(a, -3.30, -RD / 2 + 0.62, 0.0, h=4.6)
    f_books(a, -0.75, -RD / 2 + 0.62, 0.0, h=4.6)
    f_table(a, -1.05, 0.55)
    f_chair(a, -1.00, 2.05, rotz=math.pi)
    f_chair(a, 1.35, 0.30, rotz=-math.pi / 2)
    # 靠右墙书桌 + CRT
    cx, cy = RW / 2 - 0.95, 0.95
    W, D, H = 1.38, 3.30, 0.90
    a.box(W, D, 0.09, cx, cy, H - 0.09, "wood_m")
    for dx in (-1, 1):
        for dz in (-1, 1):
            a.box(0.10, 0.10, H - 0.09, cx + dx * (W / 2 - 0.10),
                  cy + dz * (D / 2 - 0.12), 0, "wood_m")
    a.box(0.82, 0.72, 0.10, cx - 0.06, cy - 0.55, H, "paper")
    a.box(0.78, 0.68, 0.62, cx - 0.06, cy - 0.60, H + 0.10, "paper", r=0.05)
    a.box(0.05, 0.56, 0.44, cx - 0.46, cy - 0.60, H + 0.20, "screen")
    a.box(0.22, 0.44, 0.05, cx - 0.22, cy + 0.01, H + 0.005, "screen")
    zz = H
    for k, (bc, bl, bw) in enumerate([("book2", .46, .34), ("book5", .42, .31), ("book1", .44, .33)]):
        a.box(bl, bw, 0.055, cx - 0.02, cy + 1.20, zz, bc, 0.06 * (k % 2))
        zz += 0.062
    # 矮柜 + 奖杯
    a.box(0.74, 2.30, 1.12, RW / 2 - 0.62, -2.70, 0, "wood_d", r=0.05)
    a.box(0.64, 2.12, 0.07, RW / 2 - 0.62, -2.70, 1.12, "wood_m", r=0.03)
    a.cyl(0.14, 0.34, RW / 2 - 0.62, -2.70, 1.19, "yellow", 12)
    a.sphere(0.17, RW / 2 - 0.62, -2.70, 1.62, "yellow", 10, 5)

def z02_arcade(a):
    """游戏娱乐区：街机柜×2 + 沙发 + 电视墙 + 茶几 + 巨型骰子"""
    for i, (cx, cy, rot) in enumerate(((-3.2, -RD / 2 + 1.0, 0.0), (-1.0, -RD / 2 + 1.0, 0.0))):
        a.box(1.05, 0.85, 1.95, cx, cy, 0, "dark", rot, r=0.06)
        a.box(0.92, 0.12, 1.05, cx, cy + 0.42, 0.75, "screen", rot)     # 斜屏
        a.box(0.20, 0.62, 0.10, cx, cy + 0.30, 1.05, "theme", rot)      # 控制台
        a.box(0.86, 0.80, 0.16, cx, cy, 1.95, "theme2", rot, r=0.05)    # 顶招
    # 电视墙
    a.box(1.90, 0.12, 1.10, -2.1, RD / 2 - 0.10, 2.10, "dark")
    a.box(1.72, 0.06, 0.92, -2.1, RD / 2 - 0.16, 2.19, "screen")
    a.box(2.30, 0.30, 0.20, -2.1, RD / 2 - 0.20, 1.85, "gray")
    # 沙发 + 茶几
    a.box(2.60, 0.95, 0.42, 0.10, 0.30, 0, "theme", r=0.08)
    a.box(2.60, 0.28, 0.72, 0.10, 0.72, 0.42, "theme", r=0.08)
    a.box(0.30, 0.95, 0.60, -1.20, 0.30, 0.42, "theme2", r=0.08)
    a.box(0.30, 0.95, 0.60, 1.40, 0.30, 0.42, "theme2", r=0.08)
    a.box(1.40, 0.80, 0.10, 0.10, -0.95, 0.42, "wood_m", r=0.04)
    for dx in (-1, 1):
        for dz in (-1, 1):
            a.box(0.10, 0.10, 0.42, 0.10 + dx * 0.62, -0.95 + dz * 0.32, 0, "wood_m")
    # 巨型骰子（地标）
    a.box(1.05, 1.05, 1.05, 2.55, -1.85, 0, "white", 0.4, r=0.10)
    a.sphere(0.09, 2.30, -1.60, 1.06, "dark", 8, 4)
    a.sphere(0.09, 2.80, -2.10, 1.06, "dark", 8, 4)
    a.sphere(0.09, 2.55, -1.85, 1.06, "dark", 8, 4)
    # 手柄
    a.box(0.52, 0.22, 0.12, 0.10, -0.95, 0.55, "theme2", r=0.05)

def z03_market(a):
    """餐饮美食区：吧台 + 圆桌×2 + 凳子 + 咖啡机 + 橱柜 + 吊灯"""
    # 吧台（沿后墙）
    a.box(4.60, 0.80, 1.08, -1.60, -RD / 2 + 1.05, 0, "wood_m", r=0.05)
    a.box(4.80, 0.95, 0.12, -1.60, -RD / 2 + 1.05, 1.08, "wood_l", r=0.04)
    a.box(4.60, 0.10, 0.90, -1.60, -RD / 2 + 1.55, 1.20, "theme", r=0.03)
    # 咖啡机 + 杯子
    a.box(0.70, 0.55, 0.72, -3.20, -RD / 2 + 1.05, 1.20, "dark", r=0.05)
    a.box(0.30, 0.24, 0.10, -3.20, -RD / 2 + 0.72, 1.50, "screen")
    for i in range(4):
        a.cyl(0.09, 0.14, -1.30 + i * 0.42, -RD / 2 + 1.05, 1.20, "white", 10)
    # 圆桌 ×2 + 凳
    for (cx, cy) in ((-2.30, 1.60), (0.90, 2.30)):
        a.cyl(0.85, 0.10, cx, cy, 0.78, "wood_l", 18)
        a.cyl(0.11, 0.78, cx, cy, 0.39, "wood_d", 10)
        a.cyl(0.42, 0.06, cx, cy, 0, "wood_d", 14)
        for k in range(3):
            ang = 2 * math.pi * k / 3 + 0.6
            f_stool(a, cx + 1.28 * math.cos(ang), cy + 1.28 * math.sin(ang), 0.28, 0.60)
    # 橱柜 + 顶棚吊灯
    a.box(0.80, 3.20, 1.80, RW / 2 - 0.75, -1.60, 0, "wood_d", r=0.05)
    a.box(0.70, 3.00, 0.08, RW / 2 - 0.75, -1.60, 1.80, "theme2", r=0.03)
    for i in range(3):
        a.cyl(0.03, 1.10, -2.20 + i * 2.2, 0.60, 4.30, "dark", 8)
        a.sphere(0.22, -2.20 + i * 2.2, 0.60, 3.20, "lamp", 10, 5)

def z04_sport(a):
    """体育运动区：球场线 + 篮球架 + 计分牌 + 器材架 + 哑铃"""
    # 场地白线（中圈 + 边线）
    a.cyl(1.90, 0.03, 0, 0.4, 0.005, "white", 30)
    a.box(7.60, 0.09, 0.03, 0, -3.30, 0.005, "white")
    a.box(7.60, 0.09, 0.03, 0, 4.10, 0.005, "white")
    a.box(0.09, 7.60, 0.03, -3.30, 0.4, 0.005, "white")
    a.box(0.09, 7.60, 0.03, 3.30, 0.4, 0.005, "white")
    # 篮球架（靠后墙）
    a.box(0.20, 0.20, 3.30, 0.60, -RD / 2 + 0.85, 0, "gray")
    a.box(1.80, 0.10, 1.20, 0.60, -RD / 2 + 1.42, 3.05, "white", r=0.03)
    a.box(1.10, 0.06, 0.72, 0.60, -RD / 2 + 1.66, 2.35, "theme", r=0.02)
    a.cyl(0.05, 0.72, 0.60, -RD / 2 + 1.78, 2.05, "orange", 10)
    a.cyl(0.30, 0.02, 0.60, -RD / 2 + 1.78, 2.28, "white", 14)
    # 计分牌
    a.box(2.20, 0.16, 1.30, -3.10, -RD / 2 + 0.30, 3.20, "dark", r=0.04)
    a.box(1.90, 0.06, 1.00, -3.10, -RD / 2 + 0.42, 3.30, "screen")
    # 器材架 + 球 + 哑铃
    f_shelf(a, RW / 2 - 0.85, 1.90, math.pi / 2, w=3.0, d=0.60, h=2.60, n=3, mat="metal")
    for i, c in enumerate(("orange", "theme", "white")):
        a.sphere(0.32, RW / 2 - 1.05 - i * 0.75, 1.90, 0.78, c, 12, 6)
    for i in range(3):
        a.box(0.62, 0.14, 0.14, -3.30, 3.20 - i * 0.45, 0.14, "dark", r=0.05)
        a.sphere(0.17, -3.30 - 0.34, 3.20 - i * 0.45, 0.14, "gray", 10, 5)
        a.sphere(0.17, -3.30 + 0.34, 3.20 - i * 0.45, 0.14, "gray", 10, 5)
    # 长凳
    a.box(2.60, 0.42, 0.10, -2.60, -2.60, 0.44, "wood_l", r=0.03)
    for dx in (-1, 1):
        a.box(0.12, 0.38, 0.44, -2.60 + dx * 1.15, -2.60, 0, "metal")

def z05_workshop(a):
    """工坊创客区：工作台 + 3D 打印机 + 工具墙 + 材料架 + 颜料桶"""
    # 工作台 ×2
    for (cx, cy, rot) in ((-2.60, 0.60, 0.0), (-2.60, -2.40, 0.0)):
        a.box(3.40, 1.40, 0.14, cx, cy, 0.86, "wood_m", rot, r=0.04)
        for dx in (-1, 1):
            for dz in (-1, 1):
                a.box(0.14, 0.14, 0.86, cx + dx * 1.55, cy + dz * 0.58, 0, "metal", rot)
        a.box(3.40, 0.10, 0.60, cx, cy - 0.65, 1.00, "wood_d", rot)
    # 3D 打印机（龙门架 + 热床 + 打印件）
    px, py = 0.40, 1.10
    a.box(1.30, 1.10, 0.16, px, py, 1.00, "dark", r=0.04)
    a.box(1.10, 0.90, 0.10, px, py, 1.16, "theme", r=0.03)
    for dx in (-1, 1):
        a.box(0.12, 0.12, 1.20, px + dx * 0.60, py, 1.16, "metal")
    a.box(1.00, 0.12, 0.10, px, py, 2.30, "metal")
    a.box(0.22, 0.22, 0.30, px, py + 0.05, 2.40, "theme2", r=0.04)   # 挤出头
    a.box(0.46, 0.46, 0.34, px, py, 1.26, "yellow", r=0.05)          # 半成品
    # 工具墙（挂板 + 工具）
    a.box(3.00, 0.10, 1.90, -1.30, -RD / 2 + 0.30, 1.60, "wood_d", r=0.03)
    for i in range(7):
        a.box(0.10, 0.10, 0.52, -2.60 + i * 0.44, -RD / 2 + 0.52, 1.90, "metal", 0.0)
        a.box(0.16, 0.06, 0.14, -2.60 + i * 0.44, -RD / 2 + 0.52, 2.40, "gray")
    # 材料架 + 颜料桶
    f_shelf(a, RW / 2 - 0.80, -1.90, math.pi / 2, w=3.20, d=0.62, h=3.20, n=4, mat="wood_d")
    for i in range(5):
        a.cyl(0.22, 0.46, RW / 2 - 1.00, -3.20 + i * 0.62, 0, ["red", "blue", "yellow", "green", "purple"][i], 12)
        a.cyl(0.24, 0.06, RW / 2 - 1.00, -3.20 + i * 0.62, 0.46, "gray", 12)
    # 台灯
    a.cyl(0.06, 0.70, -1.30, 0.60, 1.00, "metal", 10)
    a.sphere(0.20, -1.30, 0.60, 1.72, "lamp", 10, 5)

def z06_music(a):
    """音乐艺术区：小舞台 + 吉他架 + 音箱 + 画架 + 钢琴"""
    # 小舞台
    a.box(6.20, 2.60, 0.42, -1.00, -RD / 2 + 1.70, 0, "wood_d", r=0.04)
    a.box(6.30, 2.70, 0.08, -1.00, -RD / 2 + 1.70, 0.42, "theme", r=0.03)
    # 吉他架 ×2（A 架 + 吉他轮廓）
    for (cx, cy) in ((-2.60, -RD / 2 + 2.10), (-1.40, -RD / 2 + 2.30)):
        a.box(0.08, 0.50, 1.30, cx - 0.30, cy, 0.42, "wood_l", 0.18)
        a.box(0.08, 0.50, 1.30, cx + 0.30, cy, 0.42, "wood_l", -0.18)
        a.box(0.66, 0.16, 1.10, cx, cy, 0.50, "wood_m", 0.10, r=0.06)
        a.cyl(0.26, 0.06, cx, cy + 0.06, 1.02, "wood_d", 14)
        a.box(0.10, 0.62, 0.34, cx, cy - 0.02, 1.28, "wood_l", r=0.04)
    # 音箱 ×2
    for (cx, cy) in ((1.90, -RD / 2 + 2.20), (3.10, -RD / 2 + 2.20)):
        a.box(0.90, 0.70, 1.60, cx, cy, 0.42, "dark", r=0.05)
        a.cyl(0.26, 0.06, cx, cy + 0.36, 1.10, "gray", 14)
        a.cyl(0.15, 0.06, cx, cy + 0.36, 1.72, "gray", 12)
    # 立式麦克风
    a.cyl(0.04, 1.30, -0.60, -RD / 2 + 2.10, 0.42, "metal", 10)
    a.sphere(0.12, -0.60, -RD / 2 + 2.10, 1.78, "gray", 10, 5)
    # 画架 + 画板
    a.box(0.09, 0.09, 2.00, 2.60, 1.40, 0, "wood_l", 0.20)
    a.box(0.09, 0.09, 2.00, 3.10, 1.40, 0, "wood_l", -0.20)
    a.box(0.09, 0.09, 2.00, 2.85, 1.90, 0, "wood_l")
    a.box(1.30, 0.08, 1.05, 2.85, 1.40, 1.10, "paper", r=0.03)
    a.box(1.18, 0.04, 0.92, 2.85, 1.44, 1.14, "theme", r=0.02)
    # 键盘琴
    a.box(2.20, 0.80, 0.16, -2.60, 2.60, 0.74, "dark", r=0.04)
    a.box(2.00, 0.34, 0.06, -2.60, 2.90, 0.90, "white")
    for i in range(14):
        a.box(0.09, 0.26, 0.05, -3.50 + i * 0.14, 2.90, 0.96, "dark")
    f_stool(a, -2.60, 3.60, 0.30, 0.56, "theme")

def z07_garden(a):
    """花园冥想区：静心亭 + 花坛 + 水池 + 长椅 + 大量绿植"""
    # 木平台（替代地毯）
    a.box(RW - 4.0, RD - 3.6, 0.12, 0, 0.30, 0.02, "wood_l", r=0.03)
    # 静心亭：4 柱 + 顶棚
    for dx in (-1, 1):
        for dy in (-1, 1):
            a.cyl(0.14, 3.20, -1.60 + dx * 1.90, 0.40 + dy * 1.70, 0.14, "wood_d", 12)
    for dx in (-1, 1):
        a.box(4.20, 0.14, 0.16, -1.60, 0.40 + dx * 1.70, 3.34, "wood_d")
    for dy in (-1, 1):
        a.box(0.14, 3.90, 0.16, -1.60 + dy * 1.90, 0.40, 3.34, "wood_d")
    a.box(4.60, 4.30, 0.16, -1.60, 0.40, 3.50, "theme", r=0.04)
    a.box(4.90, 4.60, 0.14, -1.60, 0.40, 3.66, "theme2", r=0.05)
    # 水池
    a.cyl(1.30, 0.26, 2.60, -2.30, 0.13, "stone", 20)
    a.cyl(1.12, 0.06, 2.60, -2.30, 0.30, "water", 20)
    a.sphere(0.24, 2.30, -2.10, 0.42, "stone", 10, 5)
    # 花坛 ×3
    for (cx, cy, w, d) in ((-3.60, 3.40, 2.40, 1.10), (1.60, 3.60, 2.60, 1.10), (3.40, -1.20, 1.10, 2.60)):
        a.box(w, d, 0.50, cx, cy, 0, "wood_d", r=0.04)
        a.box(w - 0.16, d - 0.16, 0.10, cx, cy, 0.50, "soil")
        n = max(3, int(w * d / 0.9))
        for i in range(n):
            px = cx + random.uniform(-w / 2 + 0.35, w / 2 - 0.35)
            py = cy + random.uniform(-d / 2 + 0.35, d / 2 - 0.35)
            f_plant(a, px, py, random.uniform(0.42, 0.62),
                    leaf=["green", "leaf", "green"][i % 3])
    # 长椅 + 石灯
    a.box(2.40, 0.46, 0.10, 2.10, 1.60, 0.46, "wood_l", r=0.03)
    a.box(2.40, 0.12, 0.52, 2.10, 1.86, 0.46, "wood_l", 0.10)
    for dx in (-1, 1):
        a.box(0.14, 0.42, 0.46, 2.10 + dx * 1.05, 1.60, 0.14, "stone")
    a.cyl(0.30, 0.50, -0.20, -3.60, 0.14, "stone", 12)
    a.box(0.52, 0.52, 0.34, -0.20, -3.60, 0.64, "lamp", r=0.05)
    a.box(0.66, 0.66, 0.12, -0.20, -3.60, 0.98, "stone", r=0.04)

def z08_animal(a):
    """动物守护区：狗窝 + 猫爬架 + 食盆 + 软垫 + 围栏 + 玩具球"""
    # 狗窝（坡屋顶小屋）
    a.box(2.00, 1.80, 1.10, -3.00, -2.40, 0, "wood_l", r=0.05)
    a.box(2.30, 2.10, 0.14, -3.00, -2.40, 1.10, "theme", r=0.05)
    a.box(1.24, 0.10, 0.90, -3.00, -2.40, 1.24, "wood_l", r=0.03)
    a.box(0.10, 0.90, 0.62, -3.00, -1.52, 0, "dark")          # 门洞
    a.sphere(0.34, -3.00, -1.62, 0.34, "wood_m", 10, 5)        # 趴着的狗（简化）
    a.sphere(0.22, -3.00, -1.30, 0.56, "wood_m", 10, 5)
    # 猫爬架（立柱 + 平台 + 跳台）
    a.cyl(0.14, 2.60, 1.60, 1.60, 0, "gray", 12)
    a.box(1.00, 1.00, 0.14, 1.60, 1.60, 1.10, "gray", r=0.04)
    a.box(0.90, 0.90, 0.10, 1.60, 1.60, 1.24, "theme", r=0.03)
    a.box(0.90, 0.90, 0.14, 1.60, 1.60, 2.30, "gray", r=0.04)
    a.box(0.80, 0.80, 0.10, 1.60, 1.60, 2.44, "theme", r=0.03)
    a.box(1.40, 1.40, 0.16, 1.60, 1.60, 0, "wood_l", r=0.05)
    a.sphere(0.26, 1.60, 1.60, 2.80, "orange", 10, 5)          # 猫
    a.sphere(0.18, 1.60, 1.42, 3.02, "orange", 10, 5)
    # 食盆 ×2 + 软垫 + 球
    for (cx, cy, c) in ((-0.60, -3.20, "theme"), (0.40, -3.20, "theme2")):
        a.cyl(0.30, 0.14, cx, cy, 0, c, 14)
        a.cyl(0.24, 0.06, cx, cy, 0.12, "gray", 14)
    a.box(1.40, 1.00, 0.16, 3.10, -2.60, 0, "theme2", 0.2, r=0.06)
    a.sphere(0.20, -1.20, 1.80, 0.20, "red", 10, 5)
    a.sphere(0.16, 0.20, 3.30, 0.16, "yellow", 10, 5)
    # 矮围栏（分区感）
    for i in range(9):
        fx = -4.40 + i * 1.10
        a.box(0.12, 0.12, 0.72, fx, 4.30, 0, "wood_l")
    a.box(9.00, 0.08, 0.10, -0.10, 4.30, 0.44, "wood_l")
    a.box(9.00, 0.08, 0.10, -0.10, 4.30, 0.20, "wood_l")

def z09_volunteer(a):
    """志愿服务区：接待台 + 物资货架 + 红十字牌 + 地图板 + 折叠椅"""
    # 接待台
    a.box(3.60, 1.00, 1.05, -2.20, 1.20, 0, "white", r=0.05)
    a.box(3.90, 1.20, 0.12, -2.20, 1.20, 1.05, "theme", r=0.04)
    a.box(3.40, 0.10, 0.60, -2.20, 1.72, 1.17, "white")
    # 电脑
    a.box(0.90, 0.10, 0.55, -3.00, 1.20, 1.17, "screen", 0.0)
    a.box(0.90, 0.06, 0.52, -3.00, 1.14, 1.24, "screen", 0.35)
    # 红十字牌（墙面）
    a.box(1.60, 0.10, 1.60, -1.20, -RD / 2 + 0.28, 2.90, "white", r=0.03)
    a.box(1.10, 0.06, 0.32, -1.20, -RD / 2 + 0.42, 3.20, "red")
    a.box(0.32, 0.06, 1.10, -1.20, -RD / 2 + 0.42, 3.20, "red")
    # 地图板
    a.box(2.60, 0.12, 1.80, 2.10, -RD / 2 + 0.28, 1.90, "wood_d", r=0.03)
    a.box(2.36, 0.06, 1.56, 2.10, -RD / 2 + 0.42, 1.96, "paper")
    for i in range(5):
        a.box(0.90, 0.03, 0.06, 1.60 + (i % 2) * 0.95, -RD / 2 + 0.48, 2.10 + i * 0.30, "theme")
    # 物资货架 + 箱子
    f_shelf(a, RW / 2 - 0.85, -1.40, math.pi / 2, w=3.40, d=0.66, h=3.40, n=4, mat="wood_l")
    for i in range(6):
        zz = 0.30 + (i // 2) * 0.78
        f_crate(a, RW / 2 - 0.95, -2.60 + (i % 2) * 0.85, zz, 0.58,
                ["theme", "theme2", "white"][i % 3])
    # 急救箱 + 折叠椅 ×2
    a.box(0.62, 0.42, 0.34, 0.60, 3.40, 0, "white", r=0.05)
    a.box(0.34, 0.06, 0.10, 0.60, 3.40, 0.35, "red")
    a.box(0.10, 0.06, 0.24, 0.60, 3.40, 0.35, "red")
    f_chair(a, -0.40, -0.60, 0.4, "theme", "gray", 0.95)
    f_chair(a, 1.10, -0.20, -0.5, "theme", "gray", 0.95)

def z10_clean(a):
    """卫生打扫区：四色垃圾桶 + 清洁车 + 拖把 + 货架 + 水槽"""
    # 四色垃圾桶
    cols = ["green", "blue", "red", "gray"]
    for i, c in enumerate(cols):
        cx = -3.60 + i * 1.02
        a.cyl(0.34, 1.00, cx, -RD / 2 + 1.10, 0, c, 16)
        a.cyl(0.38, 0.10, cx, -RD / 2 + 1.10, 1.00, c, 16)
        a.cyl(0.24, 0.06, cx, -RD / 2 + 1.10, 1.10, "dark", 14)
    # 清洁车（小车 + 桶 + 拖把）
    a.box(1.30, 0.80, 0.14, 0.40, 1.60, 0.20, "metal", r=0.04)
    for dx in (-1, 1):
        for dy in (-1, 1):
            a.cyl(0.13, 0.08, 0.40 + dx * 0.52, 1.60 + dy * 0.32, 0.13, "dark", 12)
    a.cyl(0.30, 0.80, 0.40, 1.60, 0.34, "theme", 14)
    a.cyl(0.05, 1.50, 1.05, 1.60, 0.34, "wood_l", 10)
    a.box(0.44, 0.16, 0.12, 1.05, 1.60, 0.06, "gray", 0.0, r=0.04)
    a.box(1.30, 0.10, 0.60, 0.40, 2.28, 0.34, "metal")
    # 拖把 + 扫帚（靠墙）
    for i, (cx, c) in enumerate(((-4.20, "wood_l"), (-3.90, "yellow"))):
        a.cyl(0.05, 1.70, cx, -RD / 2 + 0.60, 0, c, 10)
        a.box(0.40, 0.14, 0.30, cx, -RD / 2 + 0.60, 0, "gray", r=0.05)
    # 水槽
    a.box(1.80, 0.90, 0.86, 3.00, -RD / 2 + 0.90, 0, "white", r=0.04)
    a.box(1.60, 0.70, 0.10, 3.00, -RD / 2 + 0.90, 0.86, "gray", r=0.03)
    a.box(1.44, 0.54, 0.24, 3.00, -RD / 2 + 0.90, 0.60, "metal")
    a.cyl(0.04, 0.34, 3.00, -RD / 2 + 0.45, 0.96, "metal", 10)
    a.box(0.10, 0.28, 0.05, 3.00, -RD / 2 + 0.45, 1.26, "metal")
    # 货架 + 卷纸/瓶
    f_shelf(a, RW / 2 - 0.80, -1.20, math.pi / 2, w=3.20, d=0.60, h=3.00, n=3, mat="metal")
    for i in range(6):
        zz = 0.30 + (i // 3) * 0.90
        a.cyl(0.16, 0.36, RW / 2 - 0.90, -2.40 + (i % 3) * 0.80, zz,
              ["cyan", "white", "theme2"][i % 3], 12)

ZFURN = {1: z01_study, 2: z02_arcade, 3: z03_market, 4: z04_sport, 5: z05_workshop,
         6: z06_music, 7: z07_garden, 8: z08_animal, 9: z09_volunteer, 10: z10_clean}

# ============================================================
# 8. 组装一间房并摆到环上
# ============================================================
def build_zone(zid, key, name, theme, angle, wh, scale, night):
    random.seed(SEED + zid)                 # 每区稳定但不同
    make_mats(zid, theme, night)
    suf = "" if night else DAY_SUFFIX

    # 花园区地面改草绿 / 体育区改球场木色
    if zid == 7:
        M["floor"] = mk_mat("mat_R%02d_floor%s" % (zid, suf),
                            (0.150, 0.330, 0.135) if not night else (0.070, 0.150, 0.065), 0.95)
        M["rug"] = mk_mat("mat_R%02d_rug%s" % (zid, suf),
                          (0.300, 0.230, 0.140) if not night else (0.135, 0.105, 0.065), 0.95)
    if zid == 4:
        M["floor"] = mk_mat("mat_R%02d_floor%s" % (zid, suf),
                            (0.545, 0.360, 0.165) if not night else (0.215, 0.145, 0.070), 0.68)

    # --- 外壳 ---
    sh = Accum("Z%02d_room_shell%s" % (zid, suf))
    build_shell(sh, wh)
    o_sh = sh.build()

    # --- 陈设 ---
    fu = Accum("Z%02d_room_furn%s" % (zid, suf))
    ZFURN[zid](fu)
    o_fu = fu.build()

    # --- 点缀：绿植 + 门牌 ---
    pr = Accum("Z%02d_room_prop%s" % (zid, suf))
    if zid not in (7,):
        f_plant(pr, -4.10, -RD / 2 + 1.00, 0.85)
    if zid not in (8, 10):
        f_plant(pr, 3.90, -RD / 2 + 1.05, 0.70)
    # 门口立牌（朝广场一侧）
    f_sign(pr, -3.60, 3.30, 0.0, 1.8, 1.5, 0.0)
    o_pr = pr.build()

    # --- 摆到环上：开口朝圆心 ---
    th = math.radians(angle)
    yaw = 3 * math.pi / 4 - th
    px, py = R_RING * math.sin(th), R_RING * math.cos(th)
    for o in (o_sh, o_fu, o_pr):
        o.location = (px, py, 0.0)
        o.rotation_euler = (0.0, 0.0, yaw)
        o.scale = (scale, scale, scale)
    return [o_sh, o_fu, o_pr]

# ============================================================
# 9. 灯光 / 相机 / 渲染
# ============================================================
def setup_light(night):
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT':
            bpy.data.objects.remove(o, do_unlink=True)
    world = bpy.data.worlds.new("W")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if night:
        bg.inputs[0].default_value = (0.050, 0.060, 0.095, 1.0)
        bg.inputs[1].default_value = 1.0
    else:
        bg.inputs[0].default_value = (0.255, 0.290, 0.350, 1.0)
        bg.inputs[1].default_value = 1.0

    if night:
        moon = bpy.data.lights.new("moon", 'SUN')
        moon.energy = 1.25
        moon.color = (0.62, 0.72, 1.0)
        moon.angle = math.radians(6)
        mo = bpy.data.objects.new("moon", moon)
        mo.rotation_euler = (math.radians(52), 0, math.radians(-120))
        bpy.context.collection.objects.link(mo)
        amb = bpy.data.lights.new("amb", 'AREA')
        amb.energy = 110
        amb.size = 60
        amb.color = (0.55, 0.66, 0.95)
        ao = bpy.data.objects.new("amb", amb)
        ao.location = (0, 0, 70)
        ao.rotation_euler = (0, 0, 0)
        bpy.context.collection.objects.link(ao)
        # 每间房一盏主题色室内灯（只在预览渲染里用，不导出）
        for (zid, _k, _n, theme, angle, _w, sc) in ZONES:
            th = math.radians(angle)
            po = bpy.data.objects.new(
                "roomlight_%d" % zid,
                bpy.data.lights.new("roomlight_%d" % zid, 'POINT'))
            po.data.energy = 7200
            po.data.color = theme
            po.data.shadow_soft_size = 3.5
            po.location = (R_RING * math.sin(th), R_RING * math.cos(th), 6.5 * sc)
            bpy.context.collection.objects.link(po)
    else:
        sun = bpy.data.lights.new("sun", 'SUN')
        sun.energy = 2.40            # 材质已压深，光照给足以出质感
        sun.color = (1.0, 0.955, 0.885)
        sun.angle = math.radians(5)
        so = bpy.data.objects.new("sun", sun)
        so.rotation_euler = (math.radians(37), 0, math.radians(-25))
        bpy.context.collection.objects.link(so)
        fill = bpy.data.lights.new("fill", 'AREA')
        fill.energy = 110
        fill.size = 40
        fill.color = (0.88, 0.90, 0.98)
        fo = bpy.data.objects.new("fill", fill)
        fo.location = (-18, -8, 42)
        from mathutils import Vector
        fo.rotation_euler = (Vector((0, 0, 0)) - fo.location).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.collection.objects.link(fo)
        # 每间房一盏暖白补光：让墙内表面与家具受光，不再背光发黑
        for (zid, _k, _n, theme, angle, wh, sc) in ZONES:
            th = math.radians(angle)
            po = bpy.data.objects.new(
                "daylight_%d" % zid,
                bpy.data.lights.new("daylight_%d" % zid, 'POINT'))
            po.data.energy = 1500
            po.data.color = (1.0, 0.965, 0.900)
            po.data.shadow_soft_size = 3.0
            po.location = (R_RING * math.sin(th), R_RING * math.cos(th), 5.6 * sc)
            bpy.context.collection.objects.link(po)

def render_view(name, loc, target, lens=52, res=(1440, 960), ortho=None):
    from mathutils import Vector
    cd = bpy.data.cameras.new("cam_" + name)
    if ortho:
        cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else:
        cd.lens = lens
    co = bpy.data.objects.new("cam_" + name, cd)
    bpy.context.collection.objects.link(co)
    co.location = Vector(loc)
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = co
    scene.render.resolution_x, scene.render.resolution_y = res
    path = os.path.join(OUT_DIR, name + ".png")
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("[render]", path)
    bpy.data.objects.remove(co, do_unlink=True)

def setup_render():
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        scene.render.engine = 'BLENDER_EEVEE'
    scene.render.film_transparent = False
    if hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 48
    try:
        scene.view_settings.view_transform = 'AgX'
        scene.view_settings.look = 'AgX - Punchy'
        scene.view_settings.exposure = -0.05
        print("[render] look = AgX - Punchy, exposure = -0.05")
    except Exception:
        pass
    os.makedirs(OUT_DIR, exist_ok=True)

def show_only(night, zones=None):
    """按当前时段 + 可选分区白名单切换可见性（渲染用）"""
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        is_day = o.name.endswith(DAY_SUFFIX)
        base = o.name[:-len(DAY_SUFFIX)] if is_day else o.name
        zid = int(base[1:3]) if (base.startswith("Z") and base[1:3].isdigit()) else -1
        day_ok = (is_day if not night else not is_day)
        zone_ok = (zones is None or zid in zones)
        vis = day_ok and zone_ok
        o.hide_render = not vis
        o.hide_viewport = not vis

# ============================================================
# 10. 主流程
# ============================================================
print("[build] generating 10 zone rooms ...")
objs = []
for (zid, key, name, theme, angle, wh, scale) in ZONES:
    objs += build_zone(zid, key, name, theme, angle, wh, scale, night=True)
for (zid, key, name, theme, angle, wh, scale) in ZONES:
    objs += build_zone(zid, key, name, theme, angle, wh, scale, night=False)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
faces = sum(len(o.data.polygons) for o in meshes)
print("[build] objects =", len(meshes), " faces =", faces)

os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=OUT_GLB,
    export_format='GLB',
    use_selection=False,
    export_apply=True,
    export_yup=True,
)
print("[export]", OUT_GLB, "%.2f MB" % (os.path.getsize(OUT_GLB) / 1048576.0))

# ---- 渲染 ----
setup_render()
setup_light(False); show_only(False)
render_view("rooms_day", (0, 62, 196), (0, 0, 4), lens=32, res=(1440, 960))
setup_light(True);  show_only(True)
render_view("rooms_night", (0, 62, 196), (0, 0, 4), lens=32, res=(1440, 960))
# Z01 近景（θ=0 → 位于 (0,60)，开口朝 -Y）
setup_light(False); show_only(False)
render_view("rooms_pair", (0, 12, 12), (0, 58, 3.4), lens=50, res=(1440, 960))

# ---- 正交诊断：Z01 立面 + 俯视（核对墙高/檐位是否吻合）----
setup_light(False); show_only(False, zones={1})
render_view("dbg_front", (0, 14, 3.6), (0, 60, 3.6), ortho=23, res=(1000, 800))
render_view("dbg_top",   (0, 60.6, 34), (0, 60, 0),  ortho=20, res=(1000, 800))
setup_light(False); show_only(False, zones={1})
render_view("rooms_close", (13, 30, 16), (0.4, 60, 3.2), lens=52, res=(1440, 960))
print("[done]")
