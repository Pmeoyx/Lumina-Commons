# 微光社区 Lumina Commons · Web 架构说明

> 2026 无锡职业技术大学 · AI WEB 应用开发挑战赛
> 本文档随「整体架构骨架」一起生成，记录**现有结构 / 已可用部分 / 待细化部分**。

---

## 1. 目录结构

```
.
├── index.html          入口页：品牌 + 三大模块 + AI 亮点说明
├── sandbox.html        3D 实时沙盘（核心展示页，加载 lumina_commons_v2.glb）
├── skills.html         技能广场：发帖 + 浏览 + AI 个性化推荐
├── profile.html        个人中心：微光名片（姓名/年龄/联系方式/技能/空闲时间）
├── editor.html         场景编辑器（拖拽搭场景，原有工具页，保留）
├── preview.html        资产预览（CC0 物件库，原有工具页，保留）
├── css/
│   └── site.css        全站共享暗色玻璃拟态主题 + 顶部导航样式
├── js/
│   ├── nav.js          顶部导航注入（各页 <body data-nav="x"> 后挂载）
│   ├── zones.js        ★ 10 分区唯一数据源（名称/主题色/角度/地标/技能/描述）
│   ├── store.js         本地数据层（localStorage：档案 + 帖子）
│   └── ai.js            ★ AI 能力层（技能匹配引擎 + 分区讲解 + LLM 接缝）
├── assets/
│   ├── lumina/lumina_commons_v2.glb   真正社区模型（800 对象，昼夜双份）
│   └── glb/…           CC0 占位模型（preview/editor 用）
├── three_lib/         本地 three.js r160（离线可用，importmap 指向它）
└── tools/build_city.py Blender 无头建模脚本（生成上述 glb）
```

---

## 2. 各页面状态

| 页面 | 状态 | 说明 |
|---|---|---|
| index.html | ✅ 完成 | 纯静态引导页，链接各模块 |
| sandbox.html | 🟡 主体可用 | 已加载真模型、10 区信标、昼夜切换、天气、AI 向导。**待细化**：信标与模型内 beacon 网格的精确对齐、点击模型拾取分区（现用信标标签点击）、性能进一步优化 |
| skills.html | 🟡 主体可用 | 发帖/筛选/删除 + AI 推荐已跑通（本地启发式）。**待细化**：接真实 LLM 升级语义匹配、帖子持久化到后端 |
| profile.html | 🟡 主体可用 | 五字段 + 本地存储已可用。**待细化**：用户给的布局模板未到，当前为通用表单，待按模板重排 |
| editor.html / preview.html | ✅ 原样保留 | 上一阶段的工具页，功能正常，纳入导航 |

---

## 3. 已实现的「AI 深度融入」

两个智能点都在 `js/ai.js`，**离线即可运行**（本地算法），并预留真实大模型接缝：

1. **技能匹配引擎 `aiMatchSkills(posts)`**
   对每个帖子结合「我」的档案打分：供需互补（你能教对方想学的，高权重）+ 技能相关 + 空闲时间重叠，输出排序结果 + 中文理由。
2. **沙盘 AI 向导 `aiExplainZone(zoneId)`**
   点任意分区，结合用户技能生成一句个性化建议，而非机械念简介。

**升级为真实大模型**：在 `js/ai.js` 填 `AI_CONFIG.endpoint`（+ `apiKey`/`model`），
`callLLM()` 会自动接管，业务代码零改动。比赛提交前接你们自己的模型即可。

---

## 4. 如何运行（必须用本地服务器，不能直接双击）

ES Module + GLB 加载受 CORS 限制，需 http 协议。两种方式任选：

- **双击** `启动服务器.bat`（Windows，需 python 在 PATH），浏览器开 `http://localhost:8000/index.html`
- 或命令行：`python -m http.server 8000`（项目根目录执行），再开上面的地址

> 已内置本地 `three_lib`，**无需联网**。

---

## 5. 待你 / 待后期细化的清单

- [ ] **个人中心布局模板**：你说先画模板给我，模板到后我按你的版式重排 profile.html
- [ ] sandbox 信标与模型内 beacon 网格精确对齐（目前 R=52 推算，需对照渲染微调）
- [ ] 真实大模型接入（`AI_CONFIG`）
- [ ] 帖子/档案后端化（现有全在 localStorage，演示够用，提交需评估）
- [ ] 3–5 分钟演示视频脚本 + ≤5 页技术文档（比赛交付物，最后阶段产出）
- [ ] 模型「高低错落 + 圆角 + 场所特征」仍需你在 Blender 验收（见 tools/build_city.py）
