# -*- coding: utf-8 -*-
"""
build_rooms_v2.py —— 「微光社区」街区化改造（社区连接感 / 温馨感）

v1 病灶：10 个房间是「漂浮在空地上的展品」——独立、死板、没有社区感。
    相邻房间中心距 37 单位，房间本体仅 13.8 宽，中间空 23 单位。

v2 六层改造：
  L1 连续街廓   每户加一块放大地块(Yard)，相邻地块角对角相切，围成一整片街区
  L2 生活痕迹   前院铺装 / 后院草坪 / 矮院墙+院门 / 树 / 花箱 / 长椅
  L3 街角共享   每相邻两户之间的街角布置共用路灯/大树/长椅/垃圾桶/公告栏
  L4 物理连接   环形步道 + 10 条辐射小径 + 门前支路 + 环形串灯 + 归家灯串
  L5 不成盒子   外挑屋檐 + 托架 + 角部烟囱 + 老虎窗 + 店面门楣/横梁/招牌
  L6 社区之心   抬升的中心集会广场 + 环形坐凳 + 篝火 + 放射铺装

以「库」方式加载 v1（截断到主流程之前），不修改 v1 源文件。
产物覆盖 assets/lumina/lumina_rooms.glb（先把 v1 备份为 lumina_rooms_v1.glb）

用法： blender --background --factory-startup --python tools/build_rooms_v2.py
"""
import math, os, random, shutil, types
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_GLB = os.path.join(ROOT, "assets", "lumina", "lumina_rooms.glb")
OUT_BLEND = os.path.join(ROOT, "assets", "lumina", "lumina_rooms_v2.blend")
OUT_DIR = os.path.join(ROOT, "output")

# ---------------- 以库方式加载 v1 ----------------
SRC = open(os.path.join(HERE, 'build_rooms.py'), encoding='utf-8').read()
try:
    CUT = SRC.index('# 10. 主流程')
except ValueError:
    CUT = len(SRC)
V1_script = os.path.join(HERE, 'build_rooms.py')
V1 = types.ModuleType('rooms_v1')
V1.__dict__['__file__'] = V1_script
exec(compile(SRC[:CUT], V1_script, 'exec'), V1.__dict__)
V1.ROOT = ROOT                 # 覆盖 v1 的路径基准，保证渲染图落在工程 output/
V1.OUT_DIR = OUT_DIR

scene = bpy.context.scene
RW, RD, FT = V1.RW, V1.RD, V1.FT
R_RING = V1.R_RING
# 8 区：去花园(7) + 工坊(5)与音乐(6)融合为 makermusic(5)；角度均匀 45°
# 保留原 zid 值，避免破坏 V1.ZFURN 按原 id 的索引
ZONES = [
    (1,  'study',     '学习备赛区', (1.00, 0.82, 0.40),   0.0,  4.80, 1.34),
    (2,  'arcade',    '游戏娱乐区', (1.00, 0.36, 0.66),  45.0,  4.20, 1.28),
    (3,  'market',    '餐饮美食区', (1.00, 0.62, 0.36),  90.0,  3.90, 1.30),
    (4,  'sport',     '体育运动区', (0.36, 0.88, 0.90), 135.0,  5.40, 1.42),
    (5,  'makermusic','工坊音乐区', (0.80, 0.55, 1.00), 180.0,  4.50, 1.33),
    (8,  'animal',    '动物守护区', (0.78, 0.60, 0.42), 225.0,  4.00, 1.26),
    (9,  'volunteer', '志愿服务区', (1.00, 0.36, 0.36), 270.0,  4.70, 1.30),
    (10, 'clean',     '卫生打扫区', (0.30, 0.82, 0.88), 315.0,  4.30, 1.28),
]
OPEN_ZONES = (3, 4, 5, 8, 10)   # 无墙开放区

# ---------------- 场地尺度常量 ----------------
YARD_DIAG_W = 36.6        # 地块世界对角长（相邻中心距 ≈37.1，留 0.5 缝）
ROOM_OUT = 5.30           # 房间占地半宽（本地）
WALL_OUT = 5.14           # 墙外皮（本地）
EAVE = 0.85               # 屋檐挑出
R_ALLEY = 57.0            # 街角共享节点半径
R_TIP = R_RING - YARD_DIAG_W / 2.0     # 地块前院尖角半径 ≈41.7
RING_IN, RING_OUT = 33.0, 40.0         # 环形步道内外半径
R_GARDEN = RING_IN                      # 社区花园（草坪）外沿
R_CORE = 14.5                           # 中心集会广场半径


def yard_local(scale):
    """本地地块边长：使缩放后世界对角恒为 YARD_DIAG_W"""
    return (YARD_DIAG_W / math.sqrt(2.0)) / scale


def pol(r, deg):
    """ZONES 极坐标约定：theta 自 +Y 轴起算"""
    t = math.radians(deg)
    return (r * math.sin(t), r * math.cos(t))


def seg(a, p0, p1, th, mat):
    """两点之间的方截面连杆（串灯/柴薪/树枝）"""
    p0v, p1v = Vector(p0), Vector(p1)
    d = p1v - p0v
    L = d.length
    if L < 1e-4:
        return
    q = Vector((0, 0, 1)).rotation_difference(d / L)
    v0, f0 = V1.prim_box(th, th, L)
    verts = [tuple(q @ Vector((x, y, z))) for (x, y, z) in v0]
    a.add(verts, f0, mat, p0v.x + d.x / 2, p0v.y + d.y / 2, p0v.z + d.z / 2)


# ============================================================
# 补充材质
# ============================================================
def extra_mats(zid, night, theme):
    M = V1.M
    suf = "" if night else V1.DAY_SUFFIX
    k = 0.72 if night else 1.0

    def add(key, rgb, rough, emis=None, es=0.0):
        c = tuple(min(1.0, v * k) for v in rgb)
        if emis:
            M[key] = V1.mk_mat("mat_R%02d_%s%s" % (zid, key, suf), c, rough,
                               emis=emis, emis_str=es)
        else:
            M[key] = V1.mk_mat("mat_R%02d_%s%s" % (zid, key, suf), c, rough)

    add("yard",    (0.395, 0.375, 0.338), 0.96)
    add("pave",    (0.520, 0.478, 0.408), 0.92)
    add("path",    (0.560, 0.512, 0.428), 0.94)
    add("grass",   (0.175, 0.345, 0.148), 0.97)
    add("brick",   (0.355, 0.190, 0.152), 0.90)
    add("bark",    (0.195, 0.132, 0.090), 0.92)
    add("roof",    (0.245, 0.152, 0.132), 0.86)
    add("post",    (0.150, 0.104, 0.062), 0.74)
    add("planter", (0.290, 0.178, 0.122), 0.90)
    add("petal",   (0.600, 0.270, 0.320), 0.86)
    if night:
        add("bulb",  (0.68, 0.54, 0.32), 0.45, emis=(1.00, 0.80, 0.50), es=2.3)
        add("bulb2", (0.60, 0.58, 0.46), 0.45, emis=(0.86, 0.92, 1.00), es=1.9)
        add("sign",  tuple(v * 0.55 for v in theme), 0.55, emis=theme, es=2.4)
        add("chain", (0.230, 0.185, 0.140), 0.72)
        add("lamp",  (0.70, 0.66, 0.56), 0.55, emis=(1.0, 0.90, 0.72), es=2.6)
    else:
        add("bulb",  (0.82, 0.79, 0.70), 0.52)
        add("bulb2", (0.72, 0.80, 0.86), 0.52)
        add("sign",  theme, 0.62)
        add("chain", (0.235, 0.240, 0.250), 0.70)
        add("lamp",  (0.85, 0.82, 0.74), 0.60)


# ============================================================
# 街区零件库
# ============================================================
def tree(a, cx, cy, s=1.0, leaf="leaf"):
    h = 3.2 * s
    a.cyl(0.24 * s, h * 0.55, cx, cy, 0, "bark", 8)
    a.cyl(0.15 * s, 0.90 * s, cx + 0.22 * s, cy - 0.10 * s, h * 0.42, "bark", 6)
    a.sphere(1.15 * s, cx, cy, h * 0.66, leaf, 8, 5)
    a.sphere(0.86 * s, cx + 0.58 * s, cy - 0.42 * s, h * 0.86, leaf, 8, 5)
    a.sphere(0.72 * s, cx - 0.62 * s, cy + 0.48 * s, h * 0.92, leaf, 7, 5)


def planter(a, cx, cy, w=1.8, d=0.72, rotz=0.0):
    a.box(w, d, 0.52, cx, cy, 0, "planter", rotz)
    a.box(w - 0.18, d - 0.18, 0.10, cx, cy, 0.52, "soil", rotz)
    n = max(2, int(w / 0.55))
    ca, sa = math.cos(rotz), math.sin(rotz)
    for k in range(n):
        lx = (k - (n - 1) / 2.0) * (w / n)
        px, py = cx + lx * ca, cy + lx * sa
        a.sphere(0.23, px, py, 0.78, "petal", 7, 5)


def bench(a, cx, cy, rotz=0.0, w=2.1, z0=0.0):
    a.box(w, 0.56, 0.10, cx, cy, 0.44 + z0, "wood_l", rotz)
    a.box(w, 0.13, 0.52, cx, cy - 0.24, 0.54 + z0, "wood_l", rotz)
    for dx in (-1, 1):
        a.box(0.11, 0.48, 0.44 + z0, cx + dx * (w / 2 - 0.16), cy, 0, "metal", rotz)


def lamp_post(a, cx, cy, h=4.6, rotz=0.0):
    a.cyl(0.16, h, cx, cy, 0, "post", 8)
    a.cyl(0.34, 0.14, cx, cy, 0, "post", 8)
    a.box(0.90, 0.18, 0.12, cx, cy, h - 0.22, "post", rotz)
    a.box(0.62, 0.62, 0.52, cx, cy, h, "lamp", rotz, r=0.06)
    a.sphere(0.20, cx, cy, h + 0.10, "bulb", 7, 5)


def notice_board(a, cx, cy, rotz=0.0):
    for dx in (-0.72, 0.72):
        a.box(0.13, 0.13, 1.35, cx + dx, cy, 0, "post", rotz)
    a.box(1.95, 0.14, 1.15, cx, cy, 1.25, "wood_m", rotz)
    a.box(1.72, 0.06, 0.92, cx, cy - 0.10, 1.36, "paper", rotz)
    a.box(2.25, 0.42, 0.12, cx, cy, 2.42, "roof", rotz)


def bin_set(a, cx, cy, rotz=0.0):
    for i, c in enumerate(("green", "blue", "yellow")):
        dx = (i - 1) * 0.72
        a.cyl(0.30, 0.86, cx + dx, cy, 0, c, 10)
        a.cyl(0.34, 0.10, cx + dx, cy, 0.86, "gray", 10)


def _lw(cx, cy, rotz, ox, oy):
    """本地偏移 (ox, oy) -> 世界坐标"""
    ca, sa = math.cos(rotz), math.sin(rotz)
    return (cx + ox * ca - oy * sa, cy + ox * sa + oy * ca)


def pergola(a, cx, cy, rotz=0.0, w=3.6, d=3.2, h=3.1):
    """花架连廊：四柱 + 顶部格栅 + 藤蔓"""
    for dx in (-1, 1):
        for dy in (-1, 1):
            px, py = _lw(cx, cy, rotz, dx * w / 2, dy * d / 2)
            a.box(0.22, 0.22, h, px, py, 0, "post")
    for k in range(5):
        oy = (k / 4.0 - 0.5) * d
        px, py = _lw(cx, cy, rotz, 0.0, oy)
        a.box(w + 0.6, 0.14, 0.14, px, py, h, "roof", rotz)
    for k in range(4):
        ox = (k / 3.0 - 0.5) * w
        px, py = _lw(cx, cy, rotz, ox, 0.0)
        a.box(0.14, d + 0.6, 0.14, px, py, h + 0.16, "roof", rotz)
    for (ox, oy) in ((-w / 2, -d / 2), (w / 2, d / 2), (0.0, 0.0)):
        px, py = _lw(cx, cy, rotz, ox, oy)
        a.sphere(0.62, px, py, h + 0.34, "leaf", 7, 5)


def flower_bed(a, cx, cy, r=1.5, rotz=0.0):
    """花坛：石圈 + 土 + 花簇"""
    for i in range(10):
        ang = math.pi * 2 * i / 10.0
        a.box(0.26, 0.26, 0.42, cx + r * math.cos(ang), cy + r * math.sin(ang),
              0, "stone", ang)
    a.cyl(r - 0.16, 0.34, cx, cy, 0, "soil", 12)
    for i in range(5):
        ang = math.pi * 2 * i / 5.0 + 0.6
        a.sphere(0.30, cx + (r * 0.42) * math.cos(ang),
                 cy + (r * 0.42) * math.sin(ang), 0.62, "petal", 7, 5)
    a.sphere(0.24, cx, cy, 0.66, "green", 7, 5)


def garland(a, p1, p2, sag=1.7, n=9, bulb="bulb"):
    pts = []
    for k in range(n + 1):
        t = k / float(n)
        x = p1[0] + (p2[0] - p1[0]) * t
        y = p1[1] + (p2[1] - p1[1]) * t
        z = p1[2] + (p2[2] - p1[2]) * t - sag * 4.0 * t * (1 - t)
        pts.append((x, y, z))
    for k in range(n):
        seg(a, pts[k], pts[k + 1], 0.075, "chain")
    for k in range(n):
        x = (pts[k][0] + pts[k + 1][0]) * 0.5
        y = (pts[k][1] + pts[k + 1][1]) * 0.5
        z = (pts[k][2] + pts[k + 1][2]) * 0.5
        a.sphere(0.21, x, y, z - 0.30, bulb, 6, 4)


# ============================================================
# L1 / L2 / L5 —— 每户「外部」层（房间本地坐标）
# ============================================================
def build_ext(a, wh, zid, scale):
    L = yard_local(scale)
    h = L / 2.0
    random.seed(V1.SEED + 900 + zid)

    xi = yi = ROOM_OUT          # 房间占地边
    ho = h - 0.62               # 铺装/草坪外沿

    # ---- L1 地块底座（相邻相切的基础，让沙盘连成一整片街区）----
    a.box(L, L, 0.54, 0, 0, -0.54, "yard")
    ed = 0.52
    for s in (-1, 1):
        a.box(L, ed, 0.09, 0, s * (h - ed / 2), -0.02, "trim")
        a.box(ed, L, 0.09, s * (h - ed / 2), 0, -0.02, "trim")

    # ---- L2 前院铺装（第二象限 L 形，不重叠）----
    a.box(ho - xi, ho + yi, 0.07, -(ho + xi) / 2, (ho - yi) / 2, 0.0, "pave")
    a.box(ho + xi, ho - yi, 0.07, (ho - xi) / 2, (ho + yi) / 2, 0.0, "pave")
    # ---- L2 后院 / 侧院草坪 ----
    a.box(2 * ho, ho - yi, 0.06, 0, -(ho + yi) / 2, 0.0, "grass")
    a.box(ho - xi, ho + yi, 0.06, (ho + xi) / 2, (ho - yi) / 2, 0.0, "grass")

    # ---- L2 矮院墙：两端各止于 5.2，角部留出斜向院门 ----
    WH0, T0, GEP = 0.92, 0.22, 5.20
    wx, wy = -(h - 0.78), (h - 0.78)
    a.box(T0, GEP + ho, WH0, wx, (GEP - ho) / 2, 0, "brick")
    a.box(T0 + 0.10, GEP + ho, 0.11, wx, (GEP - ho) / 2, WH0, "stone")
    a.box(ho + GEP, T0, WH0, (ho - GEP) / 2, wy, 0, "brick")
    a.box(ho + GEP, T0 + 0.10, 0.11, (ho - GEP) / 2, wy, WH0, "stone")
    # 院门柱（两墙端头）+ 门楣拱
    for (px, py) in ((wx, GEP), (GEP, wy)):
        a.box(0.30, 0.30, WH0 + 0.62, px, py, 0, "post")
    seg(a, (wx, GEP, WH0 + 0.62), (GEP, wy, WH0 + 0.62), 0.16, "post")
    a.sphere(0.16, (wx + GEP) / 2, (GEP + wy) / 2, WH0 + 0.78, "bulb", 6, 4)

    # ---- L5 L 形外挑屋檐（沿两面墙外皮）----
    zt = wh
    sx1 = WALL_OUT + EAVE + WALL_OUT          # 后墙檐长
    a.box(sx1, EAVE, 0.26, (WALL_OUT - (WALL_OUT + EAVE)) / 2,
          -(WALL_OUT + EAVE / 2), zt, "roof")
    a.box(EAVE, sx1, 0.26, (WALL_OUT + EAVE / 2),
          (WALL_OUT + EAVE - WALL_OUT) / 2, zt, "roof")
    nb = 7
    for k in range(nb):
        t = -WALL_OUT - 0.9 + (2 * WALL_OUT + 1.8) * k / float(nb - 1)
        a.box(0.16, 0.62, 0.42, t, -WALL_OUT - 0.26, zt - 0.44, "trim")
        a.box(0.62, 0.16, 0.42, WALL_OUT + 0.26, t, zt - 0.44, "trim")

    # ---- L5 外角烟囱（背朝广场那一角）----
    a.box(1.20, 1.20, wh + 2.0, WALL_OUT - 0.42, -(WALL_OUT - 0.42), 0, "brick")
    a.box(1.52, 1.52, 0.22, WALL_OUT - 0.42, -(WALL_OUT - 0.42), wh + 2.0, "stone")
    a.box(0.55, 0.55, 0.40, WALL_OUT - 0.42, -(WALL_OUT - 0.42), wh + 2.22, "gray")

    # ---- L5 后墙外侧老虎窗 ×2（夜里透暖光）----
    for ox in (-2.5, 1.9):
        oz = wh * 0.60
        a.box(1.55, 0.95, 1.35, ox, -WALL_OUT - 0.45, oz, "roof")
        a.box(1.12, 0.09, 0.96, ox, -WALL_OUT - 0.90, oz + 0.22, "glass")
        a.box(1.90, 1.30, 0.16, ox, -WALL_OUT - 0.52, oz + 1.35, "roof")

    # ---- L5 店面：角柱 + 高位檐梁（梁两端嵌进墙体，不加中间立柱，避免遮挡室内）----
    zc = wh * 0.86
    BL = yi + 5.42                                   # 梁长（角柱 → 对面外墙）
    a.box(0.22, 0.22, zc + 0.18, -xi - 0.12, yi + 0.12, 0, "post")
    a.box(0.20, BL, 0.18, -xi - 0.12, (yi - 5.30) / 2, zc, "roof")
    a.box(BL, 0.20, 0.18, (-xi + 5.30) / 2, yi + 0.12, zc, "roof")
    a.box(1.05, BL, 0.14, -xi - 0.55, (yi - 5.30) / 2, zc + 0.20, "roof")
    a.box(BL, 1.05, 0.14, (-xi + 5.30) / 2, yi + 0.55, zc + 0.20, "roof")
    # 转角店招：挂在檐梁下、45° 面向广场
    a.box(0.14, 0.14, 0.92, -xi + 0.10, yi - 0.10, zc - 0.92, "post")
    a.box(2.10, 0.16, 0.72, -xi + 0.52, yi - 0.52, zc - 1.52, "sign", math.pi / 4)

    # ---- L2 院子里的生活物件（1.5 倍放大后按院角/院沿比例布置，仍在院内、不进房间）----
    if zid != 8:
        tree(a, -(h * 0.84), (h * 0.84), 0.55)                    # 院角小树
    planter(a, -(h * 0.82), h * 0.20, 1.20)                       # 沿 -x 院沿
    planter(a, h * 0.20, (h * 0.82), 1.20, rotz=math.pi / 2)      # 沿 +y 院沿
    bench(a, -(h * 0.82), -h * 0.26, math.pi / 2)                 # 沿 -x 院沿
    # 檐梁下的一排迎宾灯（沿两条檐梁全长布置）
    for k in range(9):
        t = (k + 0.5) / 9.0
        a.sphere(0.13, -xi - 0.12, yi - BL * t, zc - 0.24, "bulb", 6, 4)
        a.sphere(0.13, -xi - 0.12 + BL * t, yi + 0.12, zc - 0.24, "bulb", 6, 4)


# ============================================================
# L3 / L4 / L6 —— 社区连接层（世界坐标，单对象）
# ============================================================
def build_link(night):
    suf = "" if night else V1.DAY_SUFFIX
    random.seed(V1.SEED + 4242)
    V1.make_mats(0, (1.0, 0.86, 0.62), night)
    extra_mats(0, night, (1.0, 0.86, 0.62))
    a = V1.Accum("Z00_link" + suf)
    nz = len(ZONES)
    N = 72
    RM = (RING_IN + RING_OUT) / 2.0
    WD = RING_OUT - RING_IN

    # ---- L4-0 社区花园（草地底盘，一片连通的绿）----
    a.cyl(RING_OUT + 1.6, 0.12, 0, 0, -0.08, "grass", 76)
    a.cyl(RING_OUT + 0.5, 0.10, 0, 0, -0.10, "soil", 76)

    # ---- L4 环形步道（环抱整片街区）+ 内外路缘 ----
    for i in range(N):
        deg = 360.0 * i / N
        x, y = pol(RM, deg)
        a.box(2 * math.pi * RM / N + 0.12, WD, 0.18, x, y, -0.12, "path",
              math.radians(-deg))
    for rr in (RING_IN + 0.32, RING_OUT - 0.32):
        for i in range(N):
            deg = 360.0 * i / N
            x, y = pol(rr, deg)
            a.box(2 * math.pi * rr / N + 0.12, 0.36, 0.08, x, y, 0.02, "trim",
                  math.radians(-deg))

    # ---- L4 十条辐射小径：中心广场 ↔ 每户门前 ----
    for (_z, _k, _n, _t, ang, _w, _s) in ZONES:
        x, y = pol((R_CORE + RING_OUT) / 2.0, ang)
        a.box(RING_OUT - R_CORE + 1.0, 3.6, 0.18, x, y, -0.06, "path",
              math.radians(90.0 - ang))
    # ---- L4 门前支路：环道 → 地块前院尖角 ----
    for (_z, _k, _n, _t, ang, _w, _s) in ZONES:
        x, y = pol((RING_OUT + R_TIP) / 2.0, ang)
        a.box(R_TIP - RING_OUT + 1.4, 3.2, 0.16, x, y, -0.04, "path",
              math.radians(90.0 - ang))

    # ---- L6 社区之心：抬升广场 + 放射纹 + 环形坐凳 + 篝火 + 四周花架 ----
    a.cyl(R_CORE + 0.42, 0.42, 0, 0, -0.30, "trim", 44)
    a.cyl(R_CORE, 0.44, 0, 0, -0.30, "pave", 44)
    a.cyl(6.4, 0.50, 0, 0, -0.30, "path", 32)
    for (_z, _k, _n, _t, ang, _w, _s) in ZONES:
        x, y = pol((6.4 + R_CORE) / 2.0, ang)
        a.box(R_CORE - 6.4, 0.42, 0.05, x, y, 0.20, "trim",
              math.radians(90.0 - ang))
    for i in range(12):
        deg = 30.0 * i + 15.0
        x, y = pol(11.4, deg)
        bench(a, x, y, math.radians(-deg), 2.1, 0.14)
    for i in range(10):
        x, y = pol(1.7, 36.0 * i)
        a.cyl(0.33, 0.56, x, y, 0, "gray", 8)
    for i in range(5):
        ang = math.pi * 2 * i / 5.0
        seg(a, (0.92 * math.sin(ang), 0.92 * math.cos(ang), 0.34),
            (-0.92 * math.sin(ang), -0.92 * math.cos(ang), 1.22), 0.17, "bark")
    a.cyl(0.88, 0.68, 0, 0, 0, "dark", 12)
    a.sphere(0.72, 0, 0, 1.14, "lamp", 10, 6)

    # ---- L4 花园内容：花坛 / 树 / 花架，填满「广场与街区之间」的空地 ----
    for i in range(nz):
        a1 = ZONES[i][4]
        a2 = ZONES[(i + 1) % nz][4]
        mid = (a1 + ((a2 - a1) % 360.0) / 2.0) % 360.0
        for (rr, kind) in ((19.5, 'bed'), (27.0, 'tree')):
            x, y = pol(rr, mid)
            if kind == 'bed':
                flower_bed(a, x, y, 1.55)
            else:
                tree(a, x, y, 1.25)
        if i % 2 == 0:
            x, y = pol(23.5, mid)
            pergola(a, x, y, math.radians(90.0 - mid), 3.8, 3.4, 3.1)
        # 花园里的两盏小地灯
        for dd in (-9.0, 9.0):
            x, y = pol(24.5, mid + dd / 24.5 * 57.2958)
            a.cyl(0.14, 1.35, x, y, 0, "post", 6)
            a.sphere(0.20, x, y, 1.44, "bulb", 6, 4)

    # ---- L3 街角共享节点（每相邻两户之间）----
    for i in range(nz):
        a1 = ZONES[i][4]
        a2 = ZONES[(i + 1) % nz][4]
        mid = (a1 + ((a2 - a1) % 360.0) / 2.0) % 360.0
        x, y = pol(R_ALLEY, mid)
        si, co = math.sin(math.radians(mid)), math.cos(math.radians(mid))
        rz = math.radians(-mid)            # 切向
        rr = math.radians(90.0 - mid)      # 径向
        a.cyl(5.4, 0.16, x, y, -0.14, "pave", 20)
        a.cyl(2.1, 0.14, x, y, -0.10, "grass", 16)
        tree(a, x, y, 1.55)
        lamp_post(a, x + 2.4 * si, y + 2.4 * co, 4.8, rz)
        bench(a, x - 2.3 * si, y - 2.3 * co, rr)
        if i % 2 == 0:
            notice_board(a, x + 3.6 * co, y - 3.6 * si, rz)
        else:
            bin_set(a, x + 3.4 * co, y - 3.4 * si, rz)

    # ---- L4 串灯环 + 归家灯串（每户门灯 → 中心篝火）----
    tips = []
    for (_z, _k, _n, _t, ang, _w, _s) in ZONES:
        x, y = pol(R_TIP, ang)
        tips.append((x, y, 5.2))
    for i in range(nz):
        x, y, _h = tips[i]
        a.cyl(0.22, 5.2, x, y, 0, "post", 8)
        a.cyl(0.40, 0.16, x, y, 0, "post", 8)
        a.box(0.74, 0.74, 0.66, x, y, 5.2, "lamp", 0.0, r=0.08)
        a.sphere(0.26, x, y, 5.66, "bulb", 7, 5)
        garland(a, tips[i], tips[(i + 1) % nz], sag=2.1, n=9, bulb="bulb")
        garland(a, (x * 0.94, y * 0.94, 5.0), (0.0, 0.0, 5.6),
                sag=2.8, n=10, bulb="bulb2")

    o = a.build()
    o.location = (0.0, 0.0, 0.0)
    return [o]


# ============================================================
# 单区装配
# ============================================================
def _m(name, rgb, rough=0.7, emis=None, es=0.0, metal=0.0):
    """在 V1.M 里注册一个自定义材质，返回键名，供 a.box(..., name) 直接引用"""
    V1.M[name] = V1.mk_mat("mat_lumina_%s" % name, rgb, rough, emis, es, metal)
    return name


# ---- 任意欧拉角图元（Accum.add 仅支持 rotz；这里预旋转顶点以支持斜面/人字顶/倾斜黑板） ----
def _rotv(vs, rx, ry, rz):
    if rx:
        c, s = math.cos(rx), math.sin(rx)
        vs = [(x, y * c - z * s, y * s + z * c) for (x, y, z) in vs]
    if ry:
        c, s = math.cos(ry), math.sin(ry)
        vs = [(x * c + z * s, y, -x * s + z * c) for (x, y, z) in vs]
    if rz:
        c, s = math.cos(rz), math.sin(rz)
        vs = [(x * c - y * s, x * s + y * c, z) for (x, y, z) in vs]
    return vs


def rbox(a, sx, sy, sz, cx, cy, cz, mat, rx=0.0, ry=0.0, rz=0.0, r=0.0):
    """任意欧拉角箱体；cz = 箱体中心高度，旋转绕箱体中心"""
    v, f = V1.prim_box(sx, sy, sz, r=r)
    a.add(_rotv(v, rx, ry, rz), f, mat, cx, cy, cz)


def rcyl(a, rr, h, cx, cy, cz, mat, seg=16, rx=0.0, ry=0.0, rz=0.0):
    """任意欧拉角圆柱；cz = 圆柱中心高度"""
    v, f = V1.prim_cyl(rr, h, seg)
    a.add(_rotv(v, rx, ry, rz), f, mat, cx, cy, cz)


def rsphere(a, rr, cx, cy, cz, mat, seg=12, rings=6,
            sc=(1.0, 1.0, 1.0), rx=0.0, ry=0.0, rz=0.0):
    """任意欧拉角椭球；cz = 球心高度；sc = 三轴缩放"""
    v, f = V1.prim_sphere(rr, seg, rings)
    if sc != (1.0, 1.0, 1.0):
        v = [(x * sc[0], y * sc[1], z * sc[2]) for (x, y, z) in v]
    a.add(_rotv(v, rx, ry, rz), f, mat, cx, cy, cz)


def build_open_ground(a, wh, size=1.0):
    """开放地面：仅地板 + 贴地细收边，无竖向墙、无边框。
    地板顶面精确落在 z=0（物件不再悬空）；size 可整体放大地面（美食区 1.5 倍）"""
    W, D = (RW + 0.6) * size, (RD + 0.6) * size
    a.box(W, D, 0.18, 0, 0, -0.18, "floor")            # z0=底面 → 顶面正好 z=0
    a.box(W + 0.1, 0.22, 0.22, 0, D / 2 + 0.05, -0.17, "trim")
    a.box(0.22, D + 0.1, 0.22, -W / 2 - 0.05, 0, -0.17, "trim")
    a.box(W + 0.1, 0.22, 0.22, 0, -D / 2 - 0.05, -0.17, "trim")
    a.box(0.22, D + 0.1, 0.22, W / 2 + 0.05, 0, -0.17, "trim")


def flared_wall(a, rb, rt, h, mat, cx=0.0, cy=0.0, z0=0.0, seg=44, thick=0.45,
                gap_deg=0.0, gap_center_deg=135.0):
    """露天圆筒围墙：上大下小（rt>rb）的空心截锥，无顶盖、无底盖，贴地而立。
    顶点直接进 Accum（与家具同 mesh，随区域一起变换/缩放）。
    gap_deg>0 时在该角留门洞：gap_center_deg 为中心角(度，自 +X 轴，135°=本地(-X,+Y)正面/朝广场)，
    gap_deg 为门洞总张角；并加两立柱+门楣做成门框，读起来是「门」而非缺角。"""
    n = seg
    # 门洞角度区间（弧度）
    half = math.radians(gap_deg) / 2.0
    gc = math.radians(gap_center_deg) if gap_deg > 0 else None

    def seg_in_gap(i):
        if gc is None:
            return False
        ang = 2.0 * math.pi * (i + 0.5) / n      # 扇段中心角
        d = (ang - gc) % (2.0 * math.pi)
        if d > math.pi:
            d -= 2.0 * math.pi
        return -half <= d <= half

    verts, faces = [], []
    for i in range(n):
        ang = 2.0 * math.pi * i / n
        co, si = math.cos(ang), math.sin(ang)
        verts.append((cx + rb * co, cy + rb * si, z0))                 # 4i   外底
        verts.append((cx + rt * co, cy + rt * si, z0 + h))             # 4i+1 外顶
        verts.append((cx + (rb - thick) * co, cy + (rb - thick) * si, z0))         # 4i+2 内底
        verts.append((cx + (rt - thick) * co, cy + (rt - thick) * si, z0 + h))     # 4i+3 内顶
    # 仅连接「两端都在实墙」的相邻扇段；门洞两侧的扇段不连面，自然断开成门框边
    for i in range(n):
        j = (i + 1) % n
        if seg_in_gap(i) or seg_in_gap(j):
            continue
        faces.append((4 * i,     4 * j,     4 * j + 1, 4 * i + 1))     # 外壁（朝外）
        faces.append((4 * i + 2, 4 * i + 3, 4 * j + 3, 4 * j + 2))     # 内壁（朝内）
        faces.append((4 * i + 1, 4 * j + 1, 4 * j + 3, 4 * i + 3))     # 顶圈（朝上）
        faces.append((4 * i,     4 * j,     4 * j + 2, 4 * i + 2))     # 底圈（朝下）
    a.add(verts, faces, mat, 0.0, 0.0, 0.0)

    # ---- 门框：两立柱 + 门楣（仅在留门洞时）----
    if gap_deg > 0:
        Rm = (rb + rt) / 2.0                       # 门框所在中径（筒壁中部）
        for ed in (gc - half, gc + half):
            ex, ey = math.cos(ed), math.sin(ed)
            a.box(0.26, 0.26, h, cx + Rm * ex, cy + Rm * ey, z0 + h / 2, mat, rotz=ed)
        chord = 2.0 * Rm * math.sin(half)
        a.box(chord, 0.26, 0.34, cx + Rm * math.cos(gc), cy + Rm * math.sin(gc),
              z0 + h, mat, rotz=gc + math.pi / 2)


def build_ext_open(a, wh, zid, scale):
    """开放区外部层：只留地块底座 + 前院铺装 + 草坪，不加院墙/屋檐/烟囱/店面"""
    L = yard_local(scale)
    h = L / 2.0
    xi = yi = ROOM_OUT
    ho = h - 0.62
    a.box(L, L, 0.54, 0, 0, -0.54, "yard")
    ed = 0.52
    for s in (-1, 1):
        a.box(L, ed, 0.09, 0, s * (h - ed / 2), -0.02, "trim")
        a.box(ed, L, 0.09, s * (h - ed / 2), 0, -0.02, "trim")
    a.box(ho - xi, ho + yi, 0.07, -(ho + xi) / 2, (ho - yi) / 2, 0.0, "pave")
    a.box(ho + xi, ho - yi, 0.07, (ho - xi) / 2, (ho + yi) / 2, 0.0, "pave")
    a.box(2 * ho, ho - yi, 0.06, 0, -(ho + yi) / 2, 0.0, "grass")
    a.box(ho - xi, ho + yi, 0.06, (ho + xi) / 2, (ho - yi) / 2, 0.0, "grass")


def gingerbread(a, cx, cy, z0, s=1.0):
    """姜饼人：头+身+四肢+纽扣，棕色"""
    _m("ginger", (0.55, 0.32, 0.16), 0.85)
    _m("white", (0.95, 0.92, 0.85), 0.6)
    a.sphere(0.46 * s, cx, cy, z0 + 0.52 * s, "ginger", 10, 6)
    a.box(0.66 * s, 0.86 * s, 0.30 * s, cx, cy, z0 + 1.15 * s, "ginger")
    for dx in (-0.46, 0.46):
        a.box(0.20 * s, 0.74 * s, 0.20 * s, cx + dx * s, cy, z0 + 1.35 * s, "ginger")
    for dx in (-0.30, 0.30):
        a.box(0.24 * s, 0.66 * s, 0.20 * s, cx + dx * s, cy, z0 + 0.42 * s, "ginger")
    for k in (0, 1):
        a.sphere(0.10 * s, cx, cy, z0 + 1.00 * s + k * 0.34 * s, "white", 6, 4)


def hockey(a, cx, cy, z0, s=1.0, rotz=0.0):
    """曲棍球杆：竖杆 + 底部横刀"""
    _m("stick", (0.85, 0.62, 0.30), 0.6)
    a.box(0.14 * s, 3.0 * s, 0.14 * s, cx, cy, z0 + 1.5 * s, "stick", rotz)
    a.box(0.14 * s, 0.95 * s, 0.14 * s, cx, cy - 1.45 * s, z0 + 0.10 * s, "stick", rotz)


def cross_red(a, cx, cy, z0, s=0.5):
    """红十字（吧台 / 志愿标识）"""
    _m("redcross", (0.85, 0.18, 0.18), 0.5)
    a.box(s * 0.95, 0.24, 0.10, cx, cy, z0, "redcross")
    a.box(0.24, s * 0.95, 0.10, cx, cy, z0, "redcross")


def cross_red_wall(a, cx, cy, zc, s=1.0):
    """竖直红十字（xz 平面，薄 y 方向贴墙，zc=十字中心高度）。
    鲜艳高饱和红 + 低粗糙度，显眼醒目。"""
    _m("redcross", (0.92, 0.03, 0.05), 0.30)
    bw = 0.30 * s                                        # 十字臂宽
    a.box(s, 0.12, bw, cx, cy, zc - bw / 2, "redcross")  # 横臂（x 向）
    a.box(bw, 0.12, s, cx, cy, zc - s / 2, "redcross")   # 竖臂（z 向）


def z01_study_big(a):
    """学习备赛区（放大版）：双书墙更宽更高、大桌加宽、书桌/矮柜/书本整体放大"""
    # 双书墙（贴后墙，加宽加高，但压在墙高 4.8 以内）
    V1.f_shelf(a, -3.50, -RD / 2 + 0.70, 0.0, w=3.2, d=0.85, h=4.7, n=7)
    V1.f_books(a, -3.50, -RD / 2 + 0.70, 0.0, w=2.9, d=0.66, h=4.7, n=7)
    V1.f_shelf(a, -0.20, -RD / 2 + 0.70, 0.0, w=3.2, d=0.85, h=4.7, n=7)
    V1.f_books(a, -0.20, -RD / 2 + 0.70, 0.0, w=2.9, d=0.66, h=4.7, n=7)
    # 大桌（加宽加长）
    V1.f_table(a, -1.10, 0.70, w=4.4, d=3.1, h=0.96)
    V1.f_chair(a, -1.05, 2.35, rotz=math.pi)
    V1.f_chair(a, 1.55, 0.40, rotz=-math.pi / 2)
    # 靠右墙书桌 + CRT（放大）
    cx, cy = RW / 2 - 1.05, 1.05
    W, D, H = 1.9, 4.0, 1.0
    a.box(W, D, 0.10, cx, cy, H - 0.10, "wood_m")
    for dx in (-1, 1):
        for dz in (-1, 1):
            a.box(0.12, 0.12, H - 0.10, cx + dx * (W / 2 - 0.12),
                  cy + dz * (D / 2 - 0.14), 0, "wood_m")
    a.box(1.10, 1.00, 0.12, cx - 0.10, cy - 0.70, H, "paper")
    a.box(1.05, 0.95, 0.85, cx - 0.10, cy - 0.78, H + 0.12, "paper", r=0.05)
    a.box(0.07, 0.75, 0.60, cx - 0.62, cy - 0.78, H + 0.22, "screen")
    a.box(0.30, 0.60, 0.06, cx - 0.30, cy + 0.02, H + 0.01, "screen")
    zz = H
    for k, (bc, bl, bw) in enumerate([("book2", .62, .46), ("book5", .56, .42), ("book1", .60, .44)]):
        a.box(bl, bw, 0.075, cx - 0.03, cy + 1.55, zz, bc, 0.06 * (k % 2))
        zz += 0.085
    # 矮柜 + 奖杯（放大）
    a.box(1.0, 3.1, 1.35, RW / 2 - 0.85, -2.90, 0, "wood_d", r=0.05)
    a.box(0.88, 2.9, 0.09, RW / 2 - 0.85, -2.90, 1.35, "wood_m", r=0.03)
    a.cyl(0.18, 0.45, RW / 2 - 0.85, -2.90, 1.42, "yellow", 12)
    a.sphere(0.22, RW / 2 - 0.85, -2.90, 1.87, "yellow", 10, 5)


def z03_market_open(a):
    """餐饮美食区 · 严格参照面包房参考图：
    深木小屋(正面全开) + 圆顶大面包屋顶(3道切口) + BAKERY木牌 + 开放柜台(小兔+法棍)
    + 左侧灰管烟囱 + 门前A字菜单黑板 + 石板路 + 草坡石头 + 右侧蓝邮箱"""
    # ---- 材质 ----
    bread = _m("bread", (0.80, 0.50, 0.22), 0.72)
    crumb = _m("crumb", (0.93, 0.80, 0.55), 0.6)
    wdark = _m("wood_dark", (0.40, 0.25, 0.15), 0.85)
    wframe = _m("wood_frame", (0.52, 0.33, 0.19), 0.8)
    ctr = _m("counter_w", (0.60, 0.41, 0.23), 0.75)
    bunny = _m("bunny", (0.94, 0.92, 0.88), 0.55)
    pink = _m("cheek", (0.95, 0.66, 0.66), 0.5)
    pipe = _m("pipe", (0.46, 0.48, 0.50), 0.45, metal=0.2)
    chalk = _m("chalk", (0.16, 0.24, 0.19), 0.7)
    gold = _m("goldroll", (0.82, 0.55, 0.25), 0.7)
    cream = _m("cream", (0.93, 0.88, 0.72), 0.5)
    stone = _m("stone", (0.62, 0.60, 0.57), 0.9)
    mound = _m("mound", (0.30, 0.55, 0.26), 0.95)
    rock = _m("rock", (0.50, 0.52, 0.50), 0.9)
    mail = _m("mailbox", (0.32, 0.52, 0.62), 0.5)
    mailp = _m("mailpost", (0.42, 0.28, 0.16), 0.8)

    WX, DY, WH = 6.4, 5.2, 3.4
    cx0, cy0 = 0.0, -0.8                 # 屋体中心（背朝 -Y，开口朝 +Y 中心）
    fy = cy0 + DY / 2                    # 正面 y
    # ---- 墙：后墙 + 左右墙，正面全开 ----
    a.box(WX, 0.30, WH, cx0, cy0 - DY / 2, 0.0, wdark)
    a.box(0.30, DY, WH, cx0 - WX / 2, cy0, 0.0, wdark)
    a.box(0.30, DY, WH, cx0 + WX / 2, cy0, 0.0, wdark)
    # ---- 正面开口框：两角柱 + 门楣 + BAKERY 木牌（切字块示意）+ 羊角包图标 ----
    for px in (cx0 - WX / 2 + 0.18, cx0 + WX / 2 - 0.18):
        a.box(0.26, 0.26, WH, px, fy, 0.0, wframe)
    a.box(WX, 0.45, 0.40, cx0, fy, WH - 0.40, wframe)            # 门楣
    a.box(WX - 0.6, 1.30, 0.18, cx0, fy + 0.04, WH - 0.30, wframe)   # 牌底（gable 上）
    for lx in (-2.0, -1.2, -0.4, 0.4, 1.2, 2.0):
        a.box(0.34, 0.10, 0.60, cx0 + lx, fy + 0.04, WH + 0.12, cream)   # BAKERY 字块
    a.box(0.95, 0.55, 0.32, cx0 - 2.8, fy + 0.04, WH + 0.05, gold, rotz=0.2)  # 牌上羊角包
    # ---- 圆顶大面包屋顶 + 3 道切口 ----
    rsphere(a, 1.0, cx0, cy0, WH + 0.25, bread, seg=16, rings=8, sc=(3.3, 2.9, 1.95))
    for jx in (-1.3, 0.0, 1.3):
        a.box(0.22, 1.7, 0.14, cx0 + jx, cy0, WH + 2.05, crumb)   # 沿 Y 的切口，贴穹顶
    # ---- 开放柜台（朝 +Y 外探）+ 法棍 + 面包卷 ----
    a.box(WX - 0.6, 1.4, 1.0, cx0, fy + 0.55, 0.0, ctr)           # 柜台体
    a.box(WX - 0.6, 1.5, 0.12, cx0, fy + 0.55, 1.0, wframe, r=0.04)   # 台面
    a.box(2.4, 0.34, 0.34, cx0 - 0.2, fy + 0.55, 1.12, gold)      # 法棍
    for bx in (-1.4, 0.6):
        a.sphere(0.26, cx0 + bx, fy + 0.55, 1.18, gold, 8, 5)     # 面包卷
    # ---- 柜台后小兔（身体+头+双耳+腮红+鼻） ----
    bx, by = cx0 + 1.2, cy0 + 0.2
    a.box(0.7, 0.7, 1.4, bx, by, 0.0, bunny)                     # 身
    a.sphere(0.45, bx, by, 1.55, bunny, 10, 6)                   # 头
    for ex in (-0.16, 0.16):
        rbox(a, 0.14, 0.14, 0.7, bx + ex, by + 0.05, 2.05, bunny, rx=-0.18)  # 耳
    for ex in (-0.18, 0.18):
        a.sphere(0.10, bx + ex, by + 0.22, 1.45, pink, 6, 4)     # 腮红
    a.sphere(0.10, bx + 0.18, by + 0.30, 1.50, pink, 6, 4)       # 鼻
    # ---- 左侧灰管烟囱（竖管 + 顶横管 + 弯头） ----
    a.cyl(0.20, 3.4, cx0 - WX / 2 - 0.35, cy0 - 1.6, 0.0, pipe, 12)
    a.box(0.9, 0.22, 0.22, cx0 - WX / 2 + 0.10, cy0 - 1.6, 3.40, pipe)
    a.sphere(0.22, cx0 - WX / 2 - 0.35, cy0 - 1.6, 3.60, pipe, 10, 5)
    # ---- 门前 A 字菜单黑板（任意角倾斜，朝 +Y 迎客） ----
    ry = fy + 2.4
    rbox(a, 2.6, 0.12, 1.5, cx0 - 0.9, ry, 1.0, chalk, rx=0.30)
    rbox(a, 2.6, 0.12, 1.5, cx0 + 0.9, ry, 1.0, chalk, rx=-0.30)
    for k in range(3):
        a.box(0.10, 0.5, 0.06, cx0 - 0.9, ry + 0.06, 0.9 + k * 0.28, cream, rotz=0.0)
    # ---- 草坡石头 + 石板路 + 右侧蓝邮箱 ----
    a.box(2.2, 3.4, 0.06, cx0, fy + 2.0, 0.0, stone)            # 石板路
    a.sphere(0.6, cx0 - WX / 2 - 0.6, fy + 1.2, 0.5, rock, 8, 5)
    a.sphere(0.5, cx0 + WX / 2 + 0.7, fy + 1.6, 0.4, rock, 8, 5)
    a.sphere(0.55, cx0 + WX / 2 + 0.4, fy + 0.4, 0.45, mound, 8, 5)  # 草丛
    a.box(0.20, 0.20, 1.1, cx0 + WX / 2 + 1.4, fy + 1.0, 0.0, mailp)   # 邮箱柱
    a.box(0.6, 0.8, 0.55, cx0 + WX / 2 + 1.4, fy + 1.0, 0.95, mail)    # 邮箱


def z04_sport_open(a):
    """体育运动区（开放）：整片篮球场，地面白线彩绘 + 篮架"""
    _m("court_basket", (0.80, 0.45, 0.20), 0.85)
    _m("line_white", (0.92, 0.92, 0.90), 0.6)
    zf = 0.005                                             # 贴地彩绘（z0=底面，露出地面之上）
    a.box(10.6, 10.4, 0.04, 0, 0, zf, "court_basket")      # 整片篮球场
    a.box(0.18, 10.4, 0.05, 0, 0, zf + 0.02, "line_white")  # 中线
    for px in (-5.0, 5.0):
        a.box(0.18, 10.4, 0.05, px, 0, zf + 0.02, "line_white")
    for py in (-5.0, 5.0):
        a.box(10.6, 0.18, 0.05, 0, py, zf + 0.02, "line_white")
    a.box(0.20, 0.20, 3.2, -4.4, 0, 0.0, "post")         # 篮球架立柱（落地）
    a.box(1.8, 0.12, 1.1, -4.0, 0, 2.40, "line_white")   # 篮板
    a.cyl(0.32, 0.12, -3.7, 0, 2.35, "line_white", 14)   # 篮圈


_ART_CACHE = {}

def add_art_painting(night):
    """带纹理的画：独立竖直 plane（xz 平面），贴用户图片，挂在画架上。
    缓存 img/mat/mesh；day/night 各建一个对象（仅名字后缀不同）。"""
    if "art" not in _ART_CACHE:
        img = bpy.data.images.load(
            os.path.join(ROOT, "assets", "lumina", "art_painting.png"))
        mat = bpy.data.materials.new("mat_art_painting")
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        # 竖直 plane：宽 2.0(x) 高 1.6(z)，中心 (0, 3.12, 1.35)，法线朝 -Y（朝中心观众）
        W, H, cy, cz = 2.0, 1.6, 3.12, 1.35
        me = bpy.data.meshes.new("mesh_art_painting")
        me.from_pydata(
            [(-W / 2, cy, cz - H / 2), (W / 2, cy, cz - H / 2),
             (W / 2, cy, cz + H / 2), (-W / 2, cy, cz + H / 2)],
            [], [(0, 1, 2, 3)])
        me.materials.append(mat)
        uv = me.uv_layers.new(name="UVMap")
        for li, (u, v) in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
            uv.data[li].uv = (u, v)
        _ART_CACHE["art"] = me
    me = _ART_CACHE["art"]
    suf = "" if night else V1.DAY_SUFFIX
    ob = bpy.data.objects.new("Z05_art_painting%s" % suf, me)
    bpy.context.collection.objects.link(ob)
    return ob


def z05_makermusic(a):
    """工坊+音乐融合区：圆形大舞台 + 麦克风 + 钢琴 + 画架油画 + 大轮胎 + 木桌"""
    _m("stage", (0.80, 0.62, 0.40), 0.7)
    _m("piano", (0.12, 0.12, 0.14), 0.5)
    _m("canvas", (0.86, 0.80, 0.62), 0.85)
    _m("tire", (0.10, 0.10, 0.12), 0.95)
    _m("artwall", (0.80, 0.70, 0.88), 0.82)
    # ---- 露天圆筒：圆形底盘 + 上大下小的空心截锥围墙（无顶、无底盖）----
    a.cyl(6.4, 0.24, 0, 0, -0.24, "floor", 48)           # 圆形底盘（顶面 z=0，随 furn 缩放）
    a.cyl(6.60, 0.12, 0, 0, -0.12, "trim", 48)            # 底盘外圈收边
    flared_wall(a, 6.2, 6.9, 4.5, "artwall", gap_deg=60.0, gap_center_deg=135.0)  # 圆筒围墙：上大下小、露天无顶、本地(-X,+Y)正面开门洞
    a.cyl(3.3, 0.55, 0, 0, 0.0, "stage", 40)             # 圆形舞台（落地，顶面 0.55）
    a.cyl(3.6, 0.18, 0, 0, 0.0, "trim", 40)              # 舞台外圈收边（落地）
    a.box(0.10, 0.10, 1.5, -1.2, 0.6, 0.55, "post")      # 麦克风（立在舞台上）
    a.sphere(0.22, -1.2, 0.6, 2.12, "gray", 10, 6)       # 麦头（球心）
    a.box(2.2, 1.5, 0.9, 1.3, -0.4, 0.55, "piano")       # 钢琴（坐在舞台上）
    a.box(2.0, 0.22, 0.12, 1.3, 0.45, 1.45, "white", r=0.03)   # 键盘
    a.box(2.1, 1.4, 0.10, 1.3, -0.9, 1.45, "piano")      # 琴盖
    for px in (-1.8, 0.0, 1.8):                           # 画架：三根竖杆
        a.box(0.12, 0.12, 2.4, px, 3.2, 0.0, "wood_d")
    a.box(2.1, 0.12, 0.12, 0, 3.2, 2.30, "wood_d")        # 顶部横梁（画布靠背）
    a.box(2.1, 0.12, 0.12, 0, 3.2, 0.55, "wood_d")        # 底部横梁
    V1.f_table(a, 3.9, 2.5, w=2.4, d=1.3, h=0.9)          # 木头桌子（落地，内收避免顶到筒壁）


def z08_animal_open(a):
    """动物守护区（开放式）：猫爬架 + 猫房(平顶屋脊) + 狗窝(下凹软垫) + 饭盆"""
    _m("catpost", (0.72, 0.52, 0.34), 0.7)
    _m("cathouse", (0.85, 0.62, 0.42), 0.8)
    _m("cushion", (0.80, 0.55, 0.55), 0.95)
    _m("bowl", (0.75, 0.78, 0.82), 0.5)
    _m("food", (0.55, 0.34, 0.18), 0.85)
    a.cyl(0.22, 3.0, -3.2, -2.4, 0.0, "catpost", 12)      # 猫爬架立柱（落地）
    a.box(1.4, 1.4, 0.18, -3.2, -2.4, 0.90, "catpost", r=0.06)   # 中层平台
    a.box(1.1, 1.1, 0.16, -3.2, -2.4, 1.90, "catpost", r=0.05)   # 顶层平台
    a.sphere(0.30, -3.2, -2.4, 3.00, "food", 8, 5)        # 顶端逗猫球
    a.box(2.2, 2.2, 1.5, 3.0, -2.2, 0.0, "cathouse", r=0.06)     # 猫房（落地）
    a.box(2.5, 2.5, 0.20, 3.0, -2.2, 1.50, "roof")        # 屋面板
    a.box(2.5, 0.18, 0.34, 3.0, -2.2, 1.70, "roof")       # 屋脊
    a.box(0.9, 0.2, 1.0, 3.0, -1.05, 0.10, "dark")        # 猫洞（朝院一侧）
    a.box(2.6, 2.0, 0.9, -3.0, 3.0, 0.0, "cathouse", r=0.06)     # 狗窝（落地）
    a.box(2.8, 2.8, 0.20, -3.0, 3.0, 0.90, "roof")        # 屋面板
    a.box(2.8, 0.18, 0.34, -3.0, 3.0, 1.10, "roof")       # 屋脊
    a.box(0.9, 0.2, 0.9, -3.0, 4.05, 0.10, "dark")        # 狗窝口
    a.cyl(0.85, 0.22, -3.0, 4.40, 0.0, "cushion", 16)      # 下凹软垫（窝口前，落地）
    a.cyl(0.5, 0.28, 3.2, 3.2, 0.0, "bowl", 14)            # 饭盆（落地）
    a.cyl(0.36, 0.20, 3.2, 3.2, 0.20, "food", 12)          # 盆中食物


def z09_volunteer(a):
    """志愿服务区（双墙壳）：仅留正中间一个鲜艳红十字 + 吧台"""
    _m("bar", (0.78, 0.55, 0.34), 0.7)
    wy = -RD / 2 + 0.25
    cross_red_wall(a, 0.0, wy, 2.05, s=1.7)                # 仅留正中间一个鲜艳红十字
    a.box(4.2, 1.2, 1.1, 0, 2.6, 0.0, "bar")               # 吧台（落地）
    a.box(4.4, 1.4, 0.12, 0, 2.6, 1.10, "wood_d", r=0.04)  # 台面


def z10_clean_open(a):
    """卫生打扫区（开放）：四角骨架 + 四色分类桶 + 扫把 + 簸箕"""
    _m("frame", (0.62, 0.46, 0.30), 0.7)
    _m("bin_blue", (0.20, 0.45, 0.75), 0.6)
    _m("bin_green", (0.25, 0.65, 0.35), 0.6)
    _m("bin_red", (0.78, 0.28, 0.28), 0.6)
    _m("bin_gray", (0.55, 0.57, 0.60), 0.6)
    _m("bristle", (0.80, 0.70, 0.40), 0.9)
    fh = 3.6                                               # 四角骨架净高
    for (px, py) in ((-4.2, -4.2), (4.2, -4.2), (-4.2, 4.2), (4.2, 4.2)):
        a.box(0.18, 0.18, fh + 0.5, px, py, -0.5, "frame")  # 立柱埋入地面 0.5（z0=底面），顶端 fh
    a.box(8.6, 0.18, 0.18, 0, -4.2, fh, "frame")           # 顶圈横梁，坐立柱顶
    a.box(8.6, 0.18, 0.18, 0, 4.2, fh, "frame")
    a.box(0.18, 8.6, 0.18, -4.2, 0, fh, "frame")
    a.box(0.18, 8.6, 0.18, 4.2, 0, fh, "frame")
    # 落地底圈：把四根立柱在地面处连成一圈，视觉上锚死
    a.box(8.6, 0.20, 0.20, 0, -4.2, 0.0, "frame")
    a.box(8.6, 0.20, 0.20, 0, 4.2, 0.0, "frame")
    a.box(0.20, 8.6, 0.20, -4.2, 0, 0.0, "frame")
    a.box(0.20, 8.6, 0.20, 4.2, 0, 0.0, "frame")
    for (k, c) in ((-3.0, "bin_blue"), (-1.0, "bin_green"), (1.0, "bin_red"), (3.0, "bin_gray")):
        a.box(1.1, 1.1, 1.5, k, -3.2, 0.0, c, r=0.06)      # 四色分类桶（落地）
        a.box(1.2, 1.2, 0.12, k, -3.2, 1.5, c, r=0.06)     # 桶盖
    a.box(0.12, 0.12, 2.6, 4.4, 3.0, 0.0, "wood_d")       # 扫把（落地）
    a.box(0.7, 0.5, 0.5, 4.4, 1.7, 0.0, "bristle", r=0.05)
    a.box(0.5, 0.7, 0.4, 3.2, 3.6, 0.0, "bristle", r=0.05)  # 簸箕


def build_zone_v2(zid, key, name, theme, angle, wh, scale, night):
    scale = scale * 1.5                 # 所有区域内容整体放大 1.5 倍（地块底座经 yard_local 补偿，世界尺寸不变）
    V1.make_mats(zid, theme, night)
    extra_mats(zid, night, theme)
    suf = "" if night else V1.DAY_SUFFIX
    M = V1.M

    if zid == 4:
        M["floor"] = V1.mk_mat("mat_R%02d_floor%s" % (zid, suf),
                               (0.66, 0.66, 0.68) if not night
                               else (0.30, 0.30, 0.32), 0.85)
    if zid == 3:
        M["floor"] = V1.mk_mat("mat_R%02d_floor%s" % (zid, suf),
                               (0.30, 0.55, 0.26) if not night
                               else (0.13, 0.24, 0.12), 0.95)

    objs = []
    random.seed(V1.SEED + zid)
    sh = V1.Accum("Z%02d_room_shell%s" % (zid, suf))
    if zid in OPEN_ZONES:
        if zid == 5:
            pass   # 艺术区：圆形底盘+圆筒围墙都在 furn 内，随区统一缩放；shell 留空避免双层地面
        else:
            build_open_ground(sh, wh)      # 开放区：无墙地面（已随 scale 统一放大 1.5）
    else:
        V1.build_shell(sh, wh)             # 学习/娱乐/志愿：默认双墙壳
    objs.append(sh.build())

    random.seed(V1.SEED + zid)
    fu = V1.Accum("Z%02d_room_furn%s" % (zid, suf))
    if zid == 1:
        z01_study_big(fu)                  # 学习区：桌/柜/书整体放大
    elif zid == 3:
        z03_market_open(fu)                # 美食区：开放式面包房
    elif zid == 4:
        pass                               # 运动区：改用 import_sport_court 导入围栏篮球场
    elif zid == 5:
        z05_makermusic(fu)                 # 工坊+音乐：圆形大舞台
    elif zid == 8:
        z08_animal_open(fu)                # 动物区：猫爬架/猫房/狗窝/饭盆
    elif zid == 9:
        z09_volunteer(fu)                  # 志愿区：红马甲 + 吧台红十字
    elif zid == 10:
        z10_clean_open(fu)                 # 打扫区：骨架 + 分类桶 + 扫把簸箕
    else:
        V1.ZFURN[zid](fu)
    objs.append(fu.build())
    if zid == 5:
        objs.append(add_art_painting(night))   # 纹理画：独立竖直 plane，贴用户图片

    random.seed(V1.SEED + zid)
    pr = V1.Accum("Z%02d_room_prop%s" % (zid, suf))
    if zid in (1, 2, 9):                   # 仅围合区放盆栽，开放区不放
        V1.f_plant(pr, -4.10, -RD / 2 + 1.00, 0.85)
        V1.f_plant(pr, 3.90, -RD / 2 + 1.05, 0.70)
    objs.append(pr.build())

    random.seed(V1.SEED + zid)
    ex = V1.Accum("Z%02d_room_ext%s" % (zid, suf))
    if zid in OPEN_ZONES:
        build_ext_open(ex, wh, zid, scale)
    else:
        build_ext(ex, wh, zid, scale)
    objs.append(ex.build())

    th = math.radians(angle)
    yaw = 3 * math.pi / 4 - th
    px, py = R_RING * math.sin(th), R_RING * math.cos(th)
    for o in objs:
        o.location = (px, py, 0.0)
        o.rotation_euler = (0.0, 0.0, yaw)
        o.scale = (scale, scale, scale)   # 整区（地板+墙+家具+檐）同倍放大，不脱节
    return objs


# ============================================================
# 灯光：沿用在 v1 基础上追加共享节点的光源
# ============================================================
def setup_light(night):
    V1.setup_light(night)
    if not night:
        return
    nz = len(ZONES)
    for i in range(nz):
        a1 = ZONES[i][4]
        a2 = ZONES[(i + 1) % nz][4]
        mid = (a1 + ((a2 - a1) % 360.0) / 2.0) % 360.0
        x, y = pol(R_ALLEY, mid)
        for (lx, ly, lz, e) in ((x, y, 5.4, 2600), (x * 0.7, y * 0.7, 4.6, 900)):
            po = bpy.data.objects.new("alley_%d" % i,
                                      bpy.data.lights.new("alley_%d" % i, 'POINT'))
            po.data.energy = e
            po.data.color = (1.0, 0.86, 0.62)
            po.data.shadow_soft_size = 3.0
            po.location = (lx, ly, lz)
            bpy.context.collection.objects.link(po)
    fl = bpy.data.objects.new("fire_light",
                              bpy.data.lights.new("fire_light", 'POINT'))
    fl.data.energy = 9000
    fl.data.color = (1.0, 0.72, 0.42)
    fl.data.shadow_soft_size = 2.0
    fl.location = (0, 0, 2.0)
    bpy.context.collection.objects.link(fl)
    # 社区花园的散步地灯
    for i in range(10):
        x, y = pol(24.5, 36.0 * i + 18.0)
        gl = bpy.data.objects.new("garden_%d" % i,
                                  bpy.data.lights.new("garden_%d" % i, 'POINT'))
        gl.data.energy = 1500
        gl.data.color = (1.0, 0.84, 0.60)
        gl.data.shadow_soft_size = 3.0
        gl.location = (x, y, 1.7)
        bpy.context.collection.objects.link(gl)


def import_sport_court():
    """导入外部「围栏篮球场」模型（Basketball Court collection）：
    清掉幽灵圆柱 + 地面大平面，曲线转 mesh，join 成单 mesh，缩放到体育区开放地面，
    生成 day/night 两份（名字符合 show_only 的 Z<zid> 格式）。返回对象列表。"""
    blend_path = r"D:/潘宇欣/网页下载/blender_3d_kMaiycHHNhRX/围栏篮球场.blend"
    if not os.path.exists(blend_path):
        print("[v2] 警告：找不到围栏篮球场模型，跳过导入：", blend_path)
        return []
    with bpy.data.libraries.load(blend_path, link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c == "Basketball Court"]
    src_col = bpy.data.collections.get("Basketball Court")
    if src_col is None:
        print("[v2] 警告：源文件无 Basketball Court 集合")
        return []
    bpy.context.scene.collection.children.link(src_col)

    deps = bpy.context.evaluated_depsgraph_get()
    # 1) 删除 Light/Camera/Empty、幽灵圆柱（z_min<-3）、地面大平面（薄且大且贴地）
    remove = []
    for o in list(src_col.all_objects):
        if o.type in ('LIGHT', 'CAMERA', 'EMPTY'):
            remove.append(o)
            continue
        if o.type == 'MESH' and o.data:
            oe = o.evaluated_get(deps)
            mw = oe.matrix_world
            mi = [1e9] * 3
            ma = [-1e9] * 3
            for v in oe.data.vertices:
                w = mw @ v.co
                for i in range(3):
                    mi[i] = min(mi[i], w[i])
                    ma[i] = max(ma[i], w[i])
            sz = [ma[i] - mi[i] for i in range(3)]
            if mi[2] < -3.0:                                   # 幽灵圆柱（埋地过深）
                remove.append(o)
                continue
            if sz[2] < 0.2 and max(sz[0], sz[1]) > 15.0 and ma[2] < 1.0:  # 地面大平面
                remove.append(o)
                continue
    for o in remove:
        bpy.data.objects.remove(o, do_unlink=True)

    # 2) 曲线转 mesh（围栏网 NurbsPath）
    curve_objs = [o for o in src_col.all_objects if o.type == 'CURVE']
    for o in curve_objs:
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        bpy.ops.object.convert(target='MESH')
        o.select_set(False)

    # 3) join 所有可见 mesh 成单 mesh
    mesh_objs = [o for o in src_col.all_objects if o.type == 'MESH' and not o.hide_get()]
    if not mesh_objs:
        print("[v2] 警告：篮球场无可 join 的 mesh")
        return []
    bpy.context.view_layer.objects.active = mesh_objs[0]
    bpy.ops.object.select_all(action='DESELECT')
    for o in mesh_objs:
        o.select_set(True)
    bpy.ops.object.join()
    joined = bpy.context.active_object
    joined.name = "Z04_court_src"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # 4) 测量 + 缩放 + 居中 + 地面抬到 z=0
    mi = [1e9] * 3
    ma = [-1e9] * 3
    for v in joined.data.vertices:
        for i in range(3):
            mi[i] = min(mi[i], v.co[i])
            ma[i] = max(ma[i], v.co[i])
    cx = [(mi[i] + ma[i]) / 2.0 for i in range(3)]
    target = 21.5                       # 篮球场长边铺到 ~21.5（开放地面 22.6 内留边）
    s = target / max(ma[0] - mi[0], ma[1] - mi[1])
    for v in joined.data.vertices:
        # 只居中 x/y + 等比缩放，z 不抬升（模型地面基准即 z=0，围栏柱埋地属正常）
        v.co = ((v.co[0] - cx[0]) * s, (v.co[1] - cx[1]) * s, v.co[2] * s)

    # 5) 体育区定位（angle=135），生成 day/night 两份
    th = math.radians(135.0)
    yaw = 3 * math.pi / 4 - th
    px, py = R_RING * math.sin(th), R_RING * math.cos(th)
    out = []
    for night, suf in [(True, ""), (False, V1.DAY_SUFFIX)]:
        ob = bpy.data.objects.new("Z04_court%s" % suf, joined.data)
        ob.location = (px, py, 0.0)
        ob.rotation_euler = (0.0, 0.0, yaw)
        ob.scale = (1.0, 1.0, 1.0)
        bpy.context.collection.objects.link(ob)
        out.append(ob)
    bpy.data.objects.remove(joined, do_unlink=True)
    print("[v2] 导入围栏篮球场：顶点 %d，缩放 %.3f" % (len(out[0].data.vertices), s))
    return out


# ============================================================
# 主流程
# ============================================================
print("[v2] 街区化改造开始 ...")
objs = []
for (zid, key, name, theme, angle, wh, scale) in ZONES:
    objs += build_zone_v2(zid, key, name, theme, angle, wh, scale, night=True)
for (zid, key, name, theme, angle, wh, scale) in ZONES:
    objs += build_zone_v2(zid, key, name, theme, angle, wh, scale, night=False)
objs += import_sport_court()
objs += build_link(night=True)
objs += build_link(night=False)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
faces = sum(len(o.data.polygons) for o in meshes)
print("[v2] objects =", len(meshes), " faces =", faces)

bak = os.path.join(ROOT, "assets", "lumina", "lumina_rooms_v1.glb")
if os.path.exists(OUT_GLB) and not os.path.exists(bak):
    shutil.copyfile(OUT_GLB, bak)
    print("[v2] 已备份 v1 ->", bak)

os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=OUT_GLB,
    export_format='GLB',
    use_selection=False,
    export_apply=True,
    export_yup=True,
)
print("[v2] export", OUT_GLB, "%.2f MB" % (os.path.getsize(OUT_GLB) / 1048576.0))

# ---------------- 保存可编辑 .blend 源文件 ----------------
# 场景已建好：10×2 昼夜两套对象 + 2 个 link 对象 + 材质 + 灯光都在 bpy.data 里
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print("[v2] saved", OUT_BLEND, "%.2f MB" % (os.path.getsize(OUT_BLEND) / 1048576.0))

# ---------------- 渲染 ----------------
V1.setup_render()
V1.setup_light(False); setup_light(False); V1.show_only(False)
V1.render_view("rooms_day", (0, 132, 188), (0, 0, 6), lens=32, res=(1440, 960))
V1.setup_light(True);  setup_light(True);  V1.show_only(True)
V1.render_view("rooms_night", (0, 132, 188), (0, 0, 6), lens=32, res=(1440, 960))

# 俯视全貌（看清是否被连成一整片街区）
V1.setup_light(False); V1.show_only(False)
V1.render_view("rooms_top", (0, 0.1, 230), (0, 0, 0), ortho=175, res=(1200, 1200))

# 归家视角：从街区望向中心广场（夜）
V1.setup_light(True); V1.show_only(True)
V1.render_view("rooms_street", (17, 47, 7.5), (0, 0, 4.2), lens=40, res=(1440, 960))
V1.render_view("rooms_night_close", (14, 44, 6.0), (2, 62, 4.0), lens=42,
               res=(1440, 960))

# 单户近景（昼）
V1.setup_light(False); V1.show_only(False)
V1.render_view("rooms_close", (16, 34, 15), (0.4, 60, 3.4), lens=52, res=(1440, 960))
print("[v2] done")
