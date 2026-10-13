// ============ 本地数据层（localStorage） ============
// 个人中心档案 + 技能广场帖子 + 社区用户（建筑成员）。无后端也能跑，演示数据全落本地。

import { ZONES, classifySkills, extractKeywords } from './zones.js';

const K_PROFILE = 'lumina.profile';
const K_POSTS   = 'lumina.posts';
const K_USERS   = 'lumina.users';
const K_USERS_V = 'lumina.users.v';   // 种子成员版本号：升级后老缓存自动重建
const K_LETTERS = 'lumina.letters';
const K_FOLLOWS = 'lumina.follows';   // 我关注的成员工牌 id 列表

// 每区种子成员数 / 种子数据版本（改动 genUsers 时 +1，老浏览器缓存会自动重建）
// 11 人/区 →（叠加技能跨区后各区 11~14 人）→ 工牌墙每区正好 3 页（每页 3~5 张）
const PER_ZONE = 11;
// 每区工牌上限：14 张 = 3 页（每页 ≤5），再给「本人」留 1 个位置不溢出第 4 页。
// 跨区归属照旧（一个人可挂在多栋楼），但某栋楼满员后就不再接收新的跨区成员，
// 否则「工坊音乐区」这类技能池大、又被高频命中的区会一路堆到 4~5 页。
const ZONE_CAP = 14;
const USERS_VERSION = 6;

export const FREE_SLOTS = ['工作日上午','工作日下午','工作日晚间','工作日凌晨','周末上午','周末下午','周末晚间','周末凌晨'];

function read(key, fallback) {
  try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; }
  catch { return fallback; }
}
function write(key, val) {
  localStorage.setItem(key, JSON.stringify(val));
}

// ---------- 个人档案 ----------
export const AVATAR_CHOICES = [
  '🙂','😄','😎','🤓','🧑‍🎓','🧑‍🔬','🧑‍🎨','🧑‍🍳','🧑‍🚀','🐱','🐶','🦊','🐼','🦉','🐧',
  '🌻','🍀','⭐','🌈','🎧','📷','🏸','☕','🍰','🎯','🪄','🧩','🍃','🔥','💫','🦋','🌸',
];

export function getProfile() {
  return read(K_PROFILE, { name:'', age:'', contact:'', skills:[], freeTime:[], face:'', joinedAt:0 });
}
export function saveProfile(p) { write(K_PROFILE, p); }

// ---------- 关注（本机记录我关注了谁） ----------
export function getFollows() { return read(K_FOLLOWS, []); }
export function isFollowing(id) { return getFollows().includes(id); }
export function toggleFollow(id) {
  const arr = getFollows();
  const i = arr.indexOf(id);
  if (i >= 0) arr.splice(i, 1); else arr.push(id);
  write(K_FOLLOWS, arr);
  return i < 0;   // true = 关注成功
}

// ---------- 头像渲染（emoji 或 上传照片的 dataURL 通用） ----------
// face 为 'data:image/...' 时输出 <img>，否则原样输出 emoji 文本。
// 放在 store 里是为了让 skills / profile / sandbox 三个页面用同一套判断逻辑。
export function faceHTML(face, fallback = '🙂') {
  const f = face || fallback;
  if (typeof f === 'string' && f.startsWith('data:image')) {
    return `<img class="face-img" src="${f}" alt="">`;
  }
  return f;
}

// ---------- 技能帖 ----------
export function getPosts() { return read(K_POSTS, []); }
export function addPost(post) {
  const posts = getPosts();
  post.id = 'p' + Date.now().toString(36) + Math.floor(Math.random()*1e3).toString(36);
  post.created = Date.now();
  posts.unshift(post);
  write(K_POSTS, posts);
  return post;
}
export function removePost(id) {
  write(K_POSTS, getPosts().filter(p => p.id !== id));
}

// ---------- 技能搭子信封（寻觅帖） ----------
// 信封 = 一封「搭子寻觅帖」：需求全文 + 关键词(可改) + 时间 + 联系方式 + 分区。
// 3D 沙盘中央广场把这些信封按分区叠成「沓」供翻看。
export function getLetters() {
  let arr = read(K_LETTERS, null);
  if (!arr) { arr = seedLetters(); write(K_LETTERS, arr); }
  return arr;
}
export function addLetter(letter) {
  const arr = getLetters();
  letter.id = 'l' + Date.now().toString(36) + Math.floor(Math.random() * 1e3).toString(36);
  letter.created = Date.now();
  letter.mine = true;   // 从沙盘发布搭子帖的入口只有本人，标记后个人中心可统计「我的搭子帖」
  arr.unshift(letter);
  write(K_LETTERS, arr);
  return letter;
}
export function lettersInZone(zid) {
  return getLetters().filter(l => l.zone === zid);
}

// 种子信封：首次访问即有可翻看的信封，覆盖若干分区
function seedLetters() {
  const samples = [
    { zone:4, type:'offer', time:'周末下午', contact:'wx·林小满', content:'周六下午篮球半场约局，4缺1，会传球的来，水平不限，快乐为主。' },
    { zone:5, type:'want',  time:'周末下午', contact:'wx·星河',   content:'想学吉他，零基础求带入门，周末下午有空，可请奶茶。' },
    { zone:1, type:'offer', time:'工作日晚间', contact:'wx·陈知行', content:'考研英语带背，工作日晚上7点图书馆三楼，组队打卡。' },
    { zone:3, type:'want',  time:'周末',     contact:'wx·拾光',   content:'想找人一起拼单点奶茶、探店，城南一带，周末。' },
    { zone:9, type:'offer', time:'工作日晚间', contact:'wx·周见山', content:'急救培训志愿者，每周三晚，有证优先，免费教学。' },
    { zone:8, type:'want',  time:'工作日',   contact:'wx·阿橘',   content:'出差一周，求靠谱的宠物寄养，家里有只橘猫。' },
  ];
  return samples.map((s, i) => ({
    id: 'seed' + i,
    zone: s.zone, type: s.type, content: s.content, time: s.time, contact: s.contact,
    keywords: extractKeywords(s.content, s.zone),
    created: Date.now() - i * 86400000,
  }));
}

// 当前用户本人（用于匹配时排除自己、对比技能）
export function getMe() {
  const p = getProfile();
  return {
    skills: p.skills || [],
    freeTime: p.freeTime || [],
    name: p.name || '我',
  };
}

// ---------- 社区用户（建筑成员） ----------
// 每位用户带 zones 字段 = 由技能归类出的分区 id 列表（可多区）。
// 点开某栋建筑 → 展示 usersInZone(该区) 的成员工牌。
const SURNAMES = ['林','陈','王','李','赵','周','吴','郑','孙','黄','刘','徐','何','高'];
const GIVEN = ['小满','知行','一禾','星河','清越','砚书','南风','见山','听澜','拾光','阿吉','可乐','团子','橙子','阿橘','小鹿','三七','木木',
               '阿柚','念念','清和','子墨','亦辰','知微','南栀','望舒','冬青','小桥','迟野','白露','余声','向晚','照野','穗穗'];

// 每人一个头像表情（合影时不会全是同一个 emoji）
const FACES = ['🙂','😄','😎','🤓','🧑🎓','🧑🔬','🧑🎨','🧑🍳','🧑🚀','🐱','🐶','🦊','🐼','🦉','🐧',
               '🌻','🍀','⭐','🌈','🎧','📷','🏸','☕','🍰','🎯','🪄','🧩','🍃'];

// 简介模板：让同区 10 张工牌的文字不重样
const BIO_TPL = [
  (z, p, ft) => `${z.name}常驻成员，擅长${p}。`,
  (z, p, ft) => `主要混迹${z.name}，${p}都能搭把手，${ft ? ft[0] + '最闲。' : '时间比较随缘。'}`,
  (z, p, ft) => `在${z.name}出没，${p}是老本行，${ft ? '一般' + ft[0] + '在。' : '随时可约。'}`,
  (z, p, ft) => `${z.name}的熟面孔，${p}都还行，${ft ? '常选' + ft[0] + '。' : '看心情出没。'}`,
  (z, p, ft) => `来了就是搭子。${p}相关都可以找我，${ft ? '空档在' + ft[0] + '。' : '随时留言。'}`,
];

function genUsers() {
  const arr = [];
  let seed = 20261007;
  const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };
  const pick = pool => pool[Math.floor(rnd() * pool.length)];
  const usedNames = new Set();
  const zoneCount = {};                                 // 每区已挂靠人数，用于跨区满员判断
  ZONES.forEach(z => { zoneCount[z.id] = 0; });
  ZONES.forEach(z => {
    const n = PER_ZONE;
    for (let i = 0; i < n; i++) {
      // 名字去重：最多重试 60 次，仍冲突则加序号后缀（保证同区 10 张卡不重名）
      let name = pick(SURNAMES) + pick(GIVEN);
      for (let t = 0; t < 60 && usedNames.has(name); t++) name = pick(SURNAMES) + pick(GIVEN);
      if (usedNames.has(name)) name = name + (i + 1);
      usedNames.add(name);

      const pool = [...z.skills];
      const k = 1 + Math.floor(rnd() * 2);
      const picks = [];
      for (let j = 0; j < k && pool.length; j++) picks.push(pool.splice(Math.floor(rnd() * pool.length), 1)[0]);
      // 技能跨区归类：一个擅长吉他+篮球的人，会同时出现在音乐楼和体育馆里。
      // 但每栋楼封顶 ZONE_CAP 张：满员后不再接收新的跨区成员（本区归属永远保留）。
      const hit = classifySkills(picks);
      const zones = hit.filter(id => id === z.id || zoneCount[id] < ZONE_CAP);
      if (!zones.includes(z.id)) zones.push(z.id);      // 保底归属本区
      zones.forEach(id => { zoneCount[id] = (zoneCount[id] || 0) + 1; });
      const free = FREE_SLOTS.filter(() => rnd() < 0.4);
      const pStr = picks.join('、');
      const tpl = BIO_TPL[Math.floor(rnd() * BIO_TPL.length)];
      arr.push({
        id: 'u' + z.id + '_' + i,
        name, age: 18 + Math.floor(rnd() * 8),
        contact: 'wx · ' + name,
        face: pick(FACES),
        skills: picks, freeTime: free, zones,
        bio: tpl(z, pStr, free),
      });
    }
  });
  return arr;
}

export function getUsers() {
  const ver = read(K_USERS_V, 0);
  let arr = read(K_USERS, null);
  if (!arr || ver !== USERS_VERSION) {
    // 保留「本人」条目，再重建种子成员，避免升级后把自己弄丢
    const me = Array.isArray(arr) ? arr.find(u => u && u.isMe) : null;
    arr = genUsers();
    if (me) arr.push(me);
    write(K_USERS, arr);
    write(K_USERS_V, USERS_VERSION);
  }
  return arr;
}

// 个人中心保存时把「本人」按技能归入对应建筑
export function upsertMe() {
  const p = getProfile();
  if (!p.name && !(p.skills && p.skills.length)) return; // 信息太少不入库
  const users = getUsers();
  const zones = classifySkills(p.skills);
  const me = {
    id: 'me', name: p.name || '我', age: p.age || '', contact: p.contact || '',
    skills: p.skills || [], freeTime: p.freeTime || [], face: p.face || '',
    zones: zones.length ? zones : [], bio: '这是你本人，由你的技能自动归类到以上建筑。', isMe: true,
  };
  const idx = users.findIndex(u => u.id === 'me');
  if (idx >= 0) users[idx] = me; else users.push(me);
  write(K_USERS, users);
}

export function usersInZone(zid) {
  const list = getUsers().filter(u => (u.zones || []).includes(zid));
  list.sort((a, b) => (b.isMe ? 1 : 0) - (a.isMe ? 1 : 0)); // 本人置顶
  return list;
}
