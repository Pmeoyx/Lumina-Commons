// ============ 8 个分区 · 全站唯一数据源 ============
// sandbox 信标 / 技能广场分区筛选 / AI 讲解 都从这里取，改一处全局生效。
// theme 为分区主题色（与模型 mat_Zxx 大致对应，后续按渲染微调）。
// 8 区：去花园冥想区(旧 7)；工坊(旧 5)与音乐(旧 6)融合为「工坊音乐区」(id 5)。
// 角度按环均匀 45° 重排，与 tools/build_rooms_v2.py 的 ZONES 完全对应。

export const ZONES = [
  { id:1, key:'study',     name:'学习备赛区', theme:'#ffd166', angle:0.0,
    hero:'知识塔', beacon:'备考互助',
    skills:['课业答疑','考研带背','编程辅导','四六级'],
    desc:'安静的自习与备考空间。知识塔通宵亮灯，适合组队带背、互相讲题。' },
  { id:2, key:'arcade',    name:'游戏娱乐区', theme:'#ff5ca8', angle:45.0,
    hero:'像素方舟', beacon:'开黑约局',
    skills:['联机开黑','桌游组织','电竞陪练','剧情攻略'],
    desc:'放松与社交的游乐场。巨型骰子与手柄是地标，周末常有人组队开黑。' },
  { id:3, key:'market',    name:'餐饮美食区', theme:'#ff9f5c', angle:90.0,
    hero:'面包小屋', beacon:'拼饭探店',
    skills:['厨艺教学','拼单点餐','探店推荐','烘焙'],
    desc:'香味最浓的一区。圆顶面包房与敞开柜台之间，是拼饭、探店的据点，柜台后还守着一只小白兔。' },
  { id:4, key:'sport',     name:'体育运动区', theme:'#5ce1e6', angle:135.0,
    hero:'跃动球场', beacon:'约球运动',
    skills:['篮球约局','夜跑搭子','健身指导','羽毛球'],
    desc:'整片敞开篮球场，不设墙。篮球架下随时能凑一场，运动搭子最好找。' },
  { id:5, key:'makermusic',name:'工坊音乐区', theme:'#b388ff', angle:180.0,
    hero:'造物声台', beacon:'手作排练',
    skills:['3D 打印','电子焊接','木工','旧物改造','吉他教学','合唱','绘画','编曲'],
    desc:'动手党与乐手共享的圆形大舞台。3D 打印机、颜料桶与钢琴、麦克风同处一室，画架对着光，常有人喊"谁来帮我看一眼这个模型"。' },
  { id:8, key:'animal',    name:'动物守护区', theme:'#c79a6b', angle:225.0,
    hero:'毛茸之家', beacon:'萌宠互助',
    skills:['宠物寄养','遛狗搭子','义诊','领养'],
    desc:'猫爬架与狗窝的地盘。出差时的寄养、周末的遛狗搭子，都在这里解决。' },
  { id:9, key:'volunteer', name:'志愿服务区', theme:'#ff5c5c', angle:270.0,
    hero:'暖心站', beacon:'志愿接力',
    skills:['急救培训','敬老陪伴','支教','物资搬运'],
    desc:'红十字与红马甲指向奉献。急救箱常备，志愿接力的第一站就在这儿。' },
  { id:10,key:'clean',     name:'卫生打扫区', theme:'#4dd0e1', angle:315.0,
    hero:'净界屋', beacon:'清洁轮值',
    skills:['公共清扫','收纳整理','旧物回收','消杀'],
    desc:'让社区保持体面的后勤区。四角骨架下摆着四色垃圾桶，旁边是扫把与水槽，清洁轮值的约定地。' },
];

export const ZONE_BY_ID = Object.fromEntries(ZONES.map(z => [z.id, z]));

// 分区坐标：与 build_rooms_v2.py / build_base_ground.py 完全一致的落位公式。
// 房间与地基均经 export_yup 导出，glTF 实际坐标为 z = -R·cosθ（y-up 翻转），
// 故此处用负号，使名牌/信标/相机精确落在每栋房间上方（R=60 地块，R=52 信标）。
export function zoneXY(zone, R = 52) {
  const th = Math.PI * zone.angle / 180;
  return [R * Math.sin(th), 0, -R * Math.cos(th)];
}

// ============ 技能 → 分区 归类规则 ============
// 一条技能可能命中多个区（如「3D 建模」既在学习也在工坊；「瑜伽」归运动）。
// 关键词做大小写无关的子串匹配；短技能(≥2字)也允许被关键词包含，避免漏判。
export const SKILL_RULES = [
  { zones:[1],    kw:['课业','答疑','考研','带背','编程','辅导','四六级','英语','数学','学习','备赛','复习','笔记','python','matlab','代码','写作','软件','论文'] },
  { zones:[2],    kw:['游戏','开黑','桌游','电竞','攻略','联机','steam','手柄','剧本杀','switch','主机'] },
  { zones:[3],    kw:['厨艺','饭','餐','探店','烘焙','咖啡','美食','做饭','做菜','甜点','奶茶','料理','面包'] },
  { zones:[4],    kw:['篮球','排球','运动','约球','夜跑','健身','羽毛球','跑步','足球','瑜伽','游泳','球','骑行','跳绳','登山','网球'] },
  { zones:[1,5],  kw:['3d','建模','模型','打印','blender','c4d','maya','sketchup'] },
  { zones:[5],    kw:['电子','焊接','木工','旧物','改造','手作','diy','创客','机械','电路','arduino','吉他','音乐','合唱','绘画','编曲','钢琴','唱歌','舞蹈','美术','书法','摄影','设计'] },
  { zones:[8],    kw:['宠物','寄养','遛狗','猫','狗','义诊','领养','萌宠','动物','铲屎'] },
  { zones:[9],    kw:['急救','敬老','支教','志愿','物资','搬运','公益','陪伴','义工'] },
  { zones:[10],   kw:['清扫','收纳','整理','回收','消杀','清洁','打扫','保洁','家务'] },
];

// 输入：技能字符串数组（如 ['3D 建模','排球']）
// 返回：命中的分区 id 数组（可多个，已去重，按规则出现顺序）
export function classifySkills(skillsRaw) {
  const list = (skillsRaw || []).map(s => String(s).toLowerCase()).filter(Boolean);
  const hit = [];
  const seen = new Set();
  for (const r of SKILL_RULES) {
    const match = list.some(s =>
      r.kw.some(k => {
        const kk = k.toLowerCase();
        return s.includes(kk) || (s.length >= 2 && kk.includes(s));
      })
    );
    if (match) r.zones.forEach(z => { if (!seen.has(z)) { seen.add(z); hit.push(z); } });
  }
  return hit;
}

// ============ 搭子需求 → 关键词 提取 ============
// 用于「信封上提取需求关键词（用户可改）」。优先命中分区技能词与常见搭子格式词，
// 命中不足 2 个时再按标点切出的 2~4 字短语兜底，最后去重截断。
const FORMAT_TERMS = ['周末','工作日','线上','线下','免费','收费','一对一','组队','求带','教学','陪练',
  '约局','拼单','拼饭','一起','招','带','收','新手','零基础','进阶','晚上','白天','下午','上午','晚上7点','图书馆'];
export function extractKeywords(content, zoneId) {
  const s = String(content || '');
  const zone = ZONE_BY_ID[zoneId];
  const dict = [
    ...(zone ? zone.skills : []),
    ...ZONES.flatMap(z => z.skills),
    ...FORMAT_TERMS,
  ];
  const hits = [];
  const low = s.toLowerCase();
  for (const w of dict) {
    if (w && low.includes(String(w).toLowerCase()) && !hits.includes(w)) hits.push(w);
  }
  // 兜底：命中太少时，按常见分隔符切出 2~4 字短语补位
  if (hits.length < 2) {
    const tokens = s.split(/[\s,，。、；;！!？?：:（）()【】\[\]"'“”‘’…·\-—]+/).filter(Boolean);
    for (const t of tokens) {
      if (t.length >= 2 && t.length <= 4 && !hits.includes(t)) hits.push(t);
    }
  }
  const out = []; const seen = new Set();
  for (const h of hits) {
    if (seen.has(h)) continue;
    seen.add(h); out.push(h);
    if (out.length >= 6) break;
  }
  return out;
}
