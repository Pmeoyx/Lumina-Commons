# -*- coding: utf-8 -*-
"""首页入场动画视频后期：
   1) 把宠物角色气泡里的「猫」改成「喵」（逐帧定位气泡 + 量取原字墨迹尺寸，等比重绘）
   2) 交给 ffmpeg 用 delogo 按时间窗擦掉左上/右下交替出现的「豆包AI生成」水印
   3) 输出网页用 H.264（faststart，保留原音轨）
"""
import subprocess, sys, numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont
from imageio_ffmpeg import get_ffmpeg_exe

FF = get_ffmpeg_exe()
SRC = r'D:\首页动画小人入场设计.mp4'
DST = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\pmeoyx\WorkBuddy\2026-10-04-12-15-33\assets\intro\hero-intro.mp4'
W, H, FPS = 960, 720, 24

FONT = ImageFont.truetype(r'C:\Windows\Fonts\Noto Sans SC Bold (TrueType).otf', 100)
WIN = (455, 315, 620, 435)          # 气泡搜索窗 x0,y0,x1,y1（贴着气泡活动范围，避免混入角色深色块）
PATCH_FROM, PATCH_TO = 12.55, 17.45  # 气泡存在区间（前后各留一点余量）
NEW_GLYPH = '喵'
GLYPH_SCALE = 0.5      # 新字相对原字墨迹高度的比例（0.5＝字号减半）

# 水印时间窗（含淡入淡出余量）
TL_SEGS = [(4.5, 7.95), (12.75, 15.95), (20.5, 23.95), (28.45, 30.1)]
BR_SEGS = [(0.0, 4.15), (8.25, 11.95), (16.25, 19.95), (24.25, 28.05)]
TL_BOX = (24, 17, 168, 48)          # x,y,w,h
BR_BOX = (786, 652, 160, 46)


def enab(segs):
    return '+'.join(f"between(t,{a},{b})" for a, b in segs)


def fit_glyph(draw, ch, target_h, fill):
    """渲染 ch 并让墨迹高度正好等于 target_h"""
    size = max(8, int(target_h * 1.15))
    for _ in range(24):
        f = FONT.font_variant(size=size)
        box = draw.textbbox((0, 0), ch, font=f)
        ih = box[3] - box[1]
        if ih <= 0:
            size += 2
            continue
        if abs(ih - target_h) <= 1:
            break
        size = max(8, int(round(size * target_h / ih)))
    f = FONT.font_variant(size=size)
    return f, draw.textbbox((0, 0), ch, font=f)


def patch_bubble(rgb, log=None):
    """以「白底 + 外圈黑描边」为特征定位对话气泡（白底用 fill_holes 补上字迹的洞），
       擦掉旧字后等尺寸重绘「喵」。不依赖字迹与背景分离，压在深色头发上也能找到。"""
    x0, y0, x1, y1 = WIN
    win = rgb[y0:y1, x0:x1]
    s = win.astype(np.int16)
    lum = s.sum(2)
    hh, ww = lum.shape

    blob = None
    for thr in (222, 210, 200):
        white = (s[..., 0] > thr) & (s[..., 1] > thr) & (s[..., 2] > thr - 8)
        if white.sum() < 250:
            continue
        filled = ndimage.binary_fill_holes(white)
        lab, n = ndimage.label(filled)
        if not n:
            continue
        for i, a in enumerate(ndimage.sum(filled, lab, range(1, n + 1)), 1):
            if a < 380 or a > 16000:
                continue
            m = lab == i
            ys, xs = np.where(m)
            bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max(), ys.max()
            bw, bh = bx1 - bx0 + 1, by1 - by0 + 1
            if bw < 26 or bh < 26 or bw > 130 or bh > 130 or not (0.6 < bw / bh < 1.75):
                continue
            if bx0 <= 2 or by0 <= 2 or bx1 >= ww - 3 or by1 >= hh - 3:
                continue
            ring = ndimage.binary_dilation(m, np.ones((3, 3), bool), iterations=3) & ~m
            if ring.sum() == 0 or float((lum[ring] < 430).mean()) < 0.5:
                continue
            cxd, cyd = (bx0 + bx1) / 2.0 - 60, (by0 + by1) / 2.0 - 58      # 越靠气泡常驻位置越好
            score = a - 400 * (cxd * cxd + cyd * cyd) ** 0.5
            if blob is None or score > blob[0]:
                blob = (score, m, (bx0, by0, bx1, by1), thr)
        if blob is not None:
            break
    if blob is None:
        return False

    _, mask, (bx0, by0, bx1, by1), thr = blob
    inner = ndimage.binary_dilation(mask, np.ones((3, 3), bool))           # 含进抗锯齿边
    wm = mask & (s[..., 0] > 220) & (s[..., 1] > 220) & (s[..., 2] > 212)
    white_rgb = tuple(int(v) for v in np.median(win[wm], axis=0)) if wm.sum() > 40 else (250, 250, 249)
    if max(white_rgb) < 198:                                              # 气泡已淡到看不清，别硬贴
        if log is not None:
            log['faint'] = white_rgb
        return False

    ink = (lum < 520) & inner & np.pad(np.ones((by1 - by0 + 1, bx1 - bx0 + 1), bool),
                                       ((by0, lum.shape[0] - by1 - 1), (bx0, lum.shape[1] - bx1 - 1)))
    if int(ink.sum()) >= 30:
        ys, xs = np.where(ink)
        gh = int(ys.max() - ys.min() + 1)
        gcx, gcy = float((xs.min() + xs.max()) / 2.0), float((ys.min() + ys.max()) / 2.0)
    else:
        gh = max(12, int((by1 - by0 + 1) * 0.56))
        gcx, gcy = (bx0 + bx1) / 2.0, (by0 + by1) / 2.0
    if log is not None:
        log['ink'] = (int(gcx), int(gcy), int(gh))
        log['blob'] = (int(bx0), int(by0), int(bx1 - bx0 + 1), int(by1 - by0 + 1), thr)

    body = win.copy()
    body[inner] = white_rgb                                               # 只重铺气泡内部，不动描边
    timg = Image.fromarray(body)
    d = ImageDraw.Draw(timg)
    fnt, bbox = fit_glyph(d, NEW_GLYPH, max(8, gh * GLYPH_SCALE), None)
    iw, ih = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text((gcx - iw / 2.0 - bbox[0], gcy - ih / 2.0 - bbox[1]),
           NEW_GLYPH, font=fnt, fill=(26, 26, 32))
    rgb[y0:y1, x0:x1] = np.asarray(timg)
    return True


def main():
    vf = []
    for (x, y, w, h), segs in ((TL_BOX, TL_SEGS), (BR_BOX, BR_SEGS)):
        vf.append(f"delogo=x={x}:y={y}:w={w}:h={h}:enable='{enab(segs)}'")
    vf.append('format=yuv420p')

    rd = subprocess.Popen([FF, '-hide_banner', '-loglevel', 'error', '-i', SRC,
                           '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-'],
                          stdout=subprocess.PIPE)
    wr = subprocess.Popen([FF, '-hide_banner', '-loglevel', 'error', '-y',
                           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-',
                           '-i', SRC,
                           '-map', '0:v', '-map', '1:a?',
                           '-vf', ','.join(vf),
                           '-c:v', 'libx264', '-preset', 'slow', '-crf', '22',
                           '-profile:v', 'high', '-level', '4.0',
                           '-c:a', 'aac', '-b:a', '128k',
                           '-movflags', '+faststart', DST],
                          stdin=subprocess.PIPE)
    fs = W * H * 3
    idx = n_patched = 0
    missed = []
    while True:
        buf = rd.stdout.read(fs)
        if len(buf) < fs:
            break
        t = idx / FPS
        if PATCH_FROM <= t <= PATCH_TO:
            a = np.frombuffer(bytearray(buf), np.uint8).reshape(H, W, 3)
            if patch_bubble(a):
                n_patched += 1
                buf = a.tobytes()
            else:
                missed.append(round(t, 3))
        wr.stdin.write(buf)
        idx += 1
    rd.stdout.close()
    wr.stdin.close()
    wr.wait()
    rd.wait()
    print(f'frames={idx} patched={n_patched} missed={len(missed)}')
    if missed:
        print('  missed frames:', missed[:40])


if __name__ == '__main__':
    main()
