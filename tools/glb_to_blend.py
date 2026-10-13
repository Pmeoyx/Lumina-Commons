# -*- coding: utf-8 -*-
"""
把已导出的 GLB 转成 Blender 原生 .blend 工程文件。
用途：GLB 不能用「文件→打开」直接打开（那不是 Blend 文档），
      转成 .blend 后即可双击 / 文件→打开 直接编辑。

运行（headless）：
  blender.exe --background --factory-startup --python tools/glb_to_blend.py
"""
import os
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SRC = os.path.join(ROOT, "assets", "lumina", "lumina_commons_v2.glb")
OUT = os.path.join(ROOT, "assets", "lumina", "lumina_commons_v2.blend")

print("[glb2blend] src  =", SRC)
print("[glb2blend] out  =", OUT)

assert os.path.isfile(SRC), "找不到源 GLB: %s" % SRC

# 清空场景（不要默认立方体/灯光/相机）
bpy.ops.wm.read_factory_settings(use_empty=True)

# 导入 glTF（会自动做 +Y-up -> +Z-up 的坐标转换）
bpy.ops.import_scene.gltf(filepath=SRC)

n = len([o for o in bpy.data.objects])
n_mesh = len([o for o in bpy.data.objects if o.type == 'MESH'])
print("[glb2blend] imported objects = %d  (mesh = %d)" % (n, n_mesh))

# 选中全部方便用户一眼看到
for o in bpy.data.objects:
    o.select_set(True)

# 保存为原生 .blend
bpy.ops.wm.save_as_mainfile(filepath=OUT)

size = os.path.getsize(OUT) / (1024.0 * 1024.0)
print("[glb2blend] saved  %.2f MB" % size)
print("[done]")
