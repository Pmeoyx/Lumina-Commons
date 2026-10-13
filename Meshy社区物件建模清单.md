# 邻里同好社区 · Meshy 3D 物件建模清单

> 用途：为 PC 端「3D 实时社区沙盘」生成真实 3D 模型（替代画布里的假渐变块）。
> 视觉基调：glass-vision-os-aurora —— 深色玻璃拟态 + 极光 + 霓虹发光浮标。
> 统一风格：**stylized low-poly（风格化低面）**，非写实，面数轻、Web 端可实时加载。

---

## 一、统一生成规范（每条提示词都套用）

**通用前缀（贴到 Meshy prompt 最前面）：**
```
stylized low-poly 3D model, flat-shaded clean geometry, soft neon accent rim light,
dark glassmorphism community sandbox aesthetic, isometric game asset,
white background for generation, NO text, NO logo
```
- 导出格式：`glb`（Three.js 直接加载，含 PBR 材质）
- 目标面数：道具 ≤ 3k 面，建筑 ≤ 8k 面
- 贴图：尽量用顶点色 / 单色材质，少依赖外部贴图，保证轻量
- 比例：以「1 单位 = 1 米」为基准，建筑高约 20–60 单位

---

## 二、建模清单总表

| 编号 | 物件 | 场景角色 | 优先级 | 预估面数 |
|---|---|---|---|---|
| A1 | 高层住宅楼 | 主楼（对应 B1–B6 概念） | 高 | 8k |
| A2 | 中层公寓 | 次楼，靠换色出变化 | 高 | 6k |
| A3 | 低层会所/商铺 | 社区公共空间 | 中 | 4k |
| P1 | 行道树（风格化） | 环境点缀 | 中 | 1.5k |
| P2 | 路灯（可发光） | 夜景发光源 | 中 | 1k |
| P3 | 长椅 | 公共区域 | 低 | 0.8k |
| P4 | 快递柜/信箱 | 生活感 | 低 | 1k |
| P5 | 自行车 | 呼应「拼车」技能 | 低 | 1.2k |
| P6 | 花箱盆栽 | 呼应「多肉交换」 | 低 | 0.6k |
| S1 | 电钻 | 技能浮标·借电钻 | 高 | 1k |
| S2 | 纸杯蛋糕 | 技能浮标·烘焙·3F | 高 | 0.8k |
| S3 | 智能手机 | 技能浮标·教手机 | 高 | 0.5k |
| S4 | 小汽车 | 技能浮标·拼车 | 高 | 2k |
| S5 | 多肉盆栽 | 技能浮标·多肉交换 | 高 | 0.6k |
| S6 | 咖啡杯 | 技能浮标·咖啡局 | 高 | 0.6k |
| E1 | 发光网格地面广场 | 场景底座 | 高 | 2k |
| C1 | 业主简模（可选） | 演示用角色 | 低 | 1.5k |

> 天气（雨/雪）建议用 Three.js 粒子/shader 实现，**不单独建模**；E1 地面用自发光网格呼应 aurora。

---

## 三、分类提示词（Meshy 直接粘贴）

### A 建筑类
- **A1 高层住宅楼**
  `tall residential tower, stacked balcony slabs, glowing window grid, cyan-violet neon edges, [`前缀`]`
- **A2 中层公寓**
  `mid-rise apartment block, rounded corners, soft emissive strips, [`前缀`]`
- **A3 低层会所**
  `low-rise glass clubhouse, arched entrance, aurora-tinted roof, [`前缀`]`

### P 环境道具
- **P1 行道树**：`low-poly stylized tree, geometric canopy, neon-lit trunk, [`前缀`]`
- **P2 路灯**：`modern street lamp, emissive lantern top, slim pole, [`前缀`]`
- **P3 长椅**：`minimal bench, floating panel legs, [`前缀`]`
- **P4 快递柜**：`parcel locker bank, glowing slot lights, [`前缀`]`
- **P5 自行车**：`stylized bicycle, clean lines, [`前缀`]`
- **P6 花箱盆栽**：`planter box with succulent, [`前缀`]`

### S 技能浮标本体（6 个，对应画布 f1–f6）
- **S1 电钻**：`cordless power drill, toy-like low-poly, [`前缀`]`
- **S2 纸杯蛋糕**：`cupcake with cherry, cute low-poly, [`前缀`]`
- **S3 智能手机**：`smartphone, floating, screen glow, [`前缀`]`
- **S4 小汽车**：`compact car, rounded low-poly, [`前缀`]`
- **S5 多肉盆栽**：`succulent in pot, [`前缀`]`
- **S6 咖啡杯**：`coffee cup with steam, [`前缀`]`

### E 场景底座
- **E1 发光网格地面**：`circular plaza base, glowing grid lines, dark glass, [`前缀`]`

---

## 四、与现有产物的对接

1. **画布（ardot）**：白天/夜晚/雨雪三态继续当「视觉规范 + 镜头参考」，不塞真模型。
2. **生产管线**：Meshy 导出 `glb` → Three.js `GLTFLoader` 加载 → A1–A3 摆楼、P 类布景、S 类挂到发光浮标环上、E1 当地面。
3. **时空切换**：白天/午/晚 = 改光照 + 极光强度；晴/雨/雪 = 切粒子系统，楼体/道具复用不重建模。
4. **下一步**：清单确认后，我用 3D 模型技能先生成 S1–S6 + A1 + E1 这套「门面样板」验证风格，再批量补齐。
