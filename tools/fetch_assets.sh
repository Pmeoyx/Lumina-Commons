#!/usr/bin/env bash
# fetch_assets.sh — 从 GitHub CC0 仓库 (ToxSam/cc0-models-Polygonal-Mind)
# 经 jsDelivr 镜像批量下载 GLB 模型。
#
# 为什么不用 raw.githubusercontent.com：国内直连会 Failed to fetch。
# jsDelivr 镜像同路径可用（实测 HTTP 200，约 60KB/s）。
# 为什么不用 xargs 并发：Windows(git bash) 下并发/间接调用会让 curl 报 (23) write error。
# 本脚本用最朴素的 while 循环串行下载，稳定。
#
# 用法：  bash tools/fetch_assets.sh
# 追加模型：往 MANIFEST 里加 "集合/模型名" 一行即可。

set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/assets/glb"
MIRROR="https://cdn.jsdelivr.net/gh/ToxSam/cc0-models-Polygonal-Mind@main/projects"
mkdir -p "$OUT"

MANIFEST="
chromatic-chaos/Building_Corner_01
chromatic-chaos/Building_Rect_01
chromatic-chaos/Building_Vapor_Ramp_01
chromatic-chaos/CellPhone_Retro
chromatic-chaos/Pot_Vapor_01
chromatic-chaos/Pot_Retro_03
chromatic-chaos/Floor_Vapor_01
chromatic-chaos/Frame_Neon_Vapor_01
chromatic-chaos/Column_Vapor_01
tomb-chaser-2/ElectricPost01_Art
tomb-chaser-2/Grass01_Art
tomb-chaser-2/TempleRoof01_Art
tomb-chaser-2/Column01_Art
tomb-chaser-2/Rock01_Art
"

echo "目标目录: $OUT"
echo "------------------------------------------------------------"
FAILED=0
while IFS= read -r item; do
  [ -z "$item" ] && continue
  coll="${item%%/*}"
  name="${item##*/}"
  dst="$OUT/${coll}__${name}.glb"
  if [ -s "$dst" ] && [ "$(head -c 4 "$dst")" = "glTF" ]; then
    echo "SKIP ${name}"
    continue
  fi
  if curl -fsSL --retry 3 --retry-delay 2 --max-time 180 -o "$dst" "$MIRROR/$coll/$name.glb"; then
    if [ "$(head -c 4 "$dst" 2>/dev/null)" = "glTF" ]; then
      echo "OK   ${name}  ($(du -k "$dst" | cut -f1)KB)"
    else
      echo "BAD  ${name} (非 glTF, 已删)"
      rm -f "$dst"
      FAILED=$((FAILED + 1))
    fi
  else
    echo "FAIL ${name}"
    rm -f "$dst"
    FAILED=$((FAILED + 1))
  fi
  sleep 4   # 沙箱连续外连/写盘会限流，留间隔可稳定下载
done <<< "$MANIFEST"

echo "------------------------------------------------------------"
echo "失败: $FAILED    目录 glb 文件数: $(ls -1 "$OUT"/*.glb 2>/dev/null | wc -l)"
