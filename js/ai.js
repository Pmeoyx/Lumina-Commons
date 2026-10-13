// ============ AI 能力层 ============
// 比赛要求「AI 深度融入」，这里是两个真实可跑的智能点：
//   1) aiMatchSkills  —— 技能广场的个性化推荐引擎（启发式打分，离线可用）
//   2) aiExplainZone  —— 沙盘点击分区后的自然语言讲解（模板生成 + 个性化）
// 两者都预留了 callLLM() 接缝：后期把 AI_CONFIG.endpoint 填上真实大模型地址，
// 即可把「关键词匹配」升级为「语义/向量匹配」，无需改业务代码。

import { ZONES, ZONE_BY_ID, SKILL_RULES } from './zones.js';
import { getMe, getLetters, getPosts, getUsers } from './store.js';

export const AI_CONFIG = {
  endpoint: null,   // OpenAI 兼容的 chat/completions 地址，如 'https://api.deepseek.com/chat/completions'
  apiKey: null,
  model: null,      // 如 'deepseek-chat' / 'qwen-plus' / 'gpt-4o-mini'
};

// 配置持久化到 localStorage：页面里填一次，三个页面通用，刷新不丢
const K_AI = 'lumina.ai';
try {
  const raw = localStorage.getItem(K_AI);
  if (raw) Object.assign(AI_CONFIG, JSON.parse(raw));
} catch (e) { /* 隐私模式等场景忽略 */ }

export function setAI(cfg) {
  Object.assign(AI_CONFIG, cfg);
  try {
    localStorage.setItem(K_AI, JSON.stringify({
      endpoint: AI_CONFIG.endpoint || null,
      apiKey: AI_CONFIG.apiKey || null,
      model: AI_CONFIG.model || null,
    }));
  } catch (e) {}
}
export function getAI() {
  return { endpoint: AI_CONFIG.endpoint, apiKey: AI_CONFIG.apiKey, model: AI_CONFIG.model };
}
// 是否已接入真实大模型（页面据此显示「AI 已接入 / 未配置」）
export function aiConfigured() { return !!AI_CONFIG.endpoint; }

// 记录最近一次调用失败的原因，供页面展示（模型名写错 / 密钥无效 / CORS 等）
let lastAIError = '';
export function getLastAIError() { return lastAIError; }

// 调用真实大模型（OpenAI 兼容协议）。未配置或失败时返回 null，交给本地逻辑兜底。
async function callLLM(system, user, opts) {
  if (!AI_CONFIG.endpoint) return null;
  opts = opts || {};
  lastAIError = '';
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), opts.timeout || 25000);
  try {
    const r = await fetch(AI_CONFIG.endpoint, {
      method:'POST',
      signal: ctrl.signal,
      headers:{'Content-Type':'application/json', ...(AI_CONFIG.apiKey?{'Authorization':'Bearer '+AI_CONFIG.apiKey}:{})},
      body: JSON.stringify({
        model: AI_CONFIG.model || 'gpt-4o-mini',
        messages:[{role:'system',content:system},{role:'user',content:user}],
        temperature: opts.temperature != null ? opts.temperature : 0.6,
      }),
    });
    clearTimeout(timer);
    if (!r.ok) {
      let detail = '';
      try {
        detail = await r.text();
        const j = JSON.parse(detail);
        detail = j.error?.message || j.message || j.msg || detail;
      } catch (e) { /* 非 JSON，保留原文 */ }
      lastAIError = 'HTTP ' + r.status + (detail ? '：' + String(detail).slice(0, 160) : '');
      console.warn('[ai] LLM 返回错误', lastAIError);
      return null;
    }
    const j = await r.json();
    // 兼容 OpenAI / 通义 / 文心 等几种常见返回结构
    const text = j.choices?.[0]?.message?.content || j.output?.text || j.result || '';
    if (!String(text).trim()) { lastAIError = '模型返回内容为空'; return null; }
    return String(text).trim();
  } catch (e) {
    clearTimeout(timer);
    const msg = (e && e.name === 'AbortError') ? '请求超时' : ((e && e.message) || String(e));
    lastAIError = msg + (/Failed to fetch|NetworkError|Load failed/i.test(msg)
      ? '（可能被浏览器跨域 CORS 拦截，或网络不可达）' : '');
    console.warn('[ai] LLM 调用失败:', lastAIError);
    return null;
  }
}

// 连通性自检：设置面板的「测试连接」用
export async function testAI() {
  if (!AI_CONFIG.endpoint) return { ok:false, msg:'还没填接口地址' };
  const t = await callLLM('你是测试助手，只回复两个字。', '回复：已连通', { timeout:15000, temperature:0 });
  if (t) return { ok:true, msg:'连接成功，模型回复：' + t.slice(0, 20) };
  return { ok:false, msg:'连接失败：' + (lastAIError || '未知错误') };
}

// ---------- 打字机输入法：用大模型生成更日常的候选词 ----------
// 本地词库有限（「选项少且不日常」），接入大模型后按拼音串给出常用中文词/短语。
// 返回字符串数组；未配置大模型或失败时返回 null，交由本地词库兜底。
export async function aiPinyin(bufRaw) {
  if (!AI_CONFIG.endpoint) return null;
  const b = String(bufRaw || '').toLowerCase().replace(/[^a-z]/g, '');
  if (b.length < 2) return null;
  const t = await callLLM(
    '你是中文拼音输入法的候选词引擎。用户给出一个拼音字母串（可能没写完），'
    + '请给出最可能是他想输入的中文词或短语。要求：'
    + '1) 贴近中国人日常口语与常用词，优先高频词；'
    + '2) 每个候选要和整串拼音长度大致对应（可以是 2~6 个字）；'
    + '3) 只返回一个 JSON 数组，元素为字符串，最多 8 个；'
    + '4) 不要输出解释、代码块或任何多余文字。',
    `拼音串：${b}`,
    { temperature: 0.4, timeout: 12000 }
  );
  if (!t) return null;
  try {
    const m = t.match(/\[[\s\S]*\]/);      // 容错：从返回里抠出数组
    if (!m) return null;
    const arr = JSON.parse(m[0]);
    return arr.filter(x => typeof x === 'string' && x.trim())
      .map(s => s.trim())
      .slice(0, 8);
  } catch (e) { return null; }
}

// ---------- 1) 技能匹配引擎 ----------
// 输入：所有帖子；输出：按与「我」的相关度排序的推荐 + 中文理由。
export async function aiMatchSkills(posts) {
  const me = getMe();
  const mySkills = (me.skills || []).map(s => s.toLowerCase());
  const myTime   = me.freeTime || [];

  const out = [];
  for (const p of posts) {
    const tags = (p.tags || []).map(t => t.toLowerCase());
    const pTime = p.time || [];

    let score = 0; const reasons = [];

    // (a) 我能教他：他「想要」的标签里有我会的东西 → 高价值互补
    if (p.type === 'want') {
      const hit = tags.filter(t => mySkills.some(m => m.includes(t) || t.includes(m)));
      if (hit.length) {
        score += 50 * hit.length;
        reasons.push('对方想学「' + hit.join('、') + '」，你的技能正好能教');
      }
    }
    // (b) 我想学：他「提供」的标签里有我感兴趣的（我技能为空时按全部弱相关）
    if (p.type === 'offer') {
      const hit = mySkills.length
        ? tags.filter(t => mySkills.some(m => m.includes(t) || t.includes(m)))
        : tags;
      if (hit.length) {
        score += 30 * (mySkills.length ? hit.length : 1);
        reasons.push('对方提供「' + (hit.length?hit.join('、'):p.title) + '」，契合你想提升的方向');
      } else if (!mySkills.length) {
        score += 8; reasons.push('暂未填写你的技能，按内容弱相关推荐');
      }
    }
    // (b2) 组队帖：标签与我的技能/兴趣有交集就推荐（组队是「平级同行」，不是供需互补）
    if (p.type === 'team') {
      const hit = mySkills.length
        ? tags.filter(t => mySkills.some(m => m.includes(t) || t.includes(m)))
        : tags;
      if (hit.length) {
        score += 28 * (mySkills.length ? hit.length : 1);
        reasons.push('组队帖「' + (hit.length ? hit.join('、') : p.title) + '」，和你的技能对得上');
      } else if (!mySkills.length) {
        score += 6; reasons.push('组队帖，按内容弱相关推荐');
      }
    }
    // (c) 空闲时间重叠
    const tHit = pTime.filter(t => myTime.includes(t));
    if (tHit.length) { score += 12 * tHit.length; reasons.push('空闲时间重叠：' + tHit.join('、')); }
    // (d) 同区加成
    if (p.zone && reasons.length) { /* 区已在卡片体现，不重复计分 */ }

    if (score <= 0) continue;
    out.push({ post:p, score, reasons });
  }
  out.sort((a, b) => b.score - a.score);
  return out.slice(0, 8);
}

// ---------- 2) 分区讲解 ----------
export async function aiExplainZone(zoneId) {
  const z = ZONE_BY_ID[zoneId];
  if (!z) return '未知分区';

  const llm = await callLLM(
    '你是微光社区的AI向导，用亲切、口语化、不超过120字的中文介绍社区分区，并可结合用户技能给一句个性化建议。',
    `分区：${z.name}（地标${z.hero}）。典型技能：${z.skills.join('、')}。用户技能：${(getMe().skills||[]).join('、')||'暂无'}。`
  );
  if (llm) return llm;

  // 本地模板兜底
  const me = getMe();
  let tip = '';
  if (me.skills && me.skills.length) {
    const overlap = z.skills.filter(s => me.skills.some(m => m.includes(s) || s.includes(m)));
    tip = overlap.length ? ` 你会的「${overlap.join('、')}」在这区能直接派上用场。` : ' 你目前的技能在这儿暂时用不上，但来这儿能认识互补的人。';
  } else {
    tip = ' 先去个人中心填一下你的技能，我能给你更准的匹配。';
  }
  return `${z.name}——${z.desc} 常驻技能：${z.skills.join('、')}。${tip}`;
}

// ---------- 3) AI 寻友（站内检索 + 站外通用问答） ----------
// 站内：搭子帖 + 技能帖 + 社区成员，按关键词+分区匹配
// 站外：当问题与社区搭子无关（如「怎么学吉他」「附近哪有球场」），调 LLM 做通用问答；
//       LLM 未配置时，本地给出社区知识型兜底回答 + 引导回社区。
export async function aiFindFriends(query) {
  const q = String(query || '').trim();
  if (!q) {
    return { ok:false, keywords:[], zones:[], matches:[],
      summary:'请先描述你想找的搭子，例如「有没有人最近想打排球」。' };
  }

  // ① 抽取关键词
  const vocab = [];
  const seen = new Set();
  const pushVocab = w => { if (w && !seen.has(w)) { seen.add(w); vocab.push(w); } };
  SKILL_RULES.forEach(r => r.kw.forEach(pushVocab));
  ZONES.forEach(z => z.skills.forEach(pushVocab));
  vocab.sort((a, b) => b.length - a.length);

  const low = q.toLowerCase();
  const kws = vocab.filter(w => low.includes(String(w).toLowerCase())).slice(0, 6);

  if (kws.length < 1) {
    const tokens = q.split(/[\s,，。、；;！!？?：:（）()【】\[\]"'“”‘’…·\-—]+/).filter(Boolean);
    for (const t of tokens) { if (t.length >= 2 && t.length <= 4) { kws.push(t); if (kws.length >= 4) break; } }
  }

  // ② 推断分区
  const zoneSet = new Set();
  for (const r of SKILL_RULES) {
    if (r.kw.some(k => kws.some(w => low.includes(k.toLowerCase())))) {
      r.zones.forEach(z => zoneSet.add(z));
    }
  }
  const zones = [...zoneSet];

  // ③ 站内检索：搭子信封
  const letters = getLetters();
  const matchedLetters = [];
  for (const l of letters) {
    const lk = (l.keywords || []).join(' ').toLowerCase();
    const lc = String(l.content || '').toLowerCase();
    const hitKw = kws.filter(w => lk.includes(w.toLowerCase()) || lc.includes(w.toLowerCase()));
    const inZone = zones.includes(l.zone);
    if (hitKw.length || inZone) matchedLetters.push({ letter:l, byKeyword:hitKw.length > 0 });
  }
  matchedLetters.sort((a, b) => (Number(b.byKeyword) - Number(a.byKeyword)) || ((b.letter.created || 0) - (a.letter.created || 0)));

  // ③b 站内检索：技能广场帖子
  const posts = getPosts();
  const matchedPosts = [];
  for (const p of posts) {
    const pt = String(p.title || '').toLowerCase();
    const pd = String(p.desc || '').toLowerCase();
    const hitKw = kws.filter(w => pt.includes(w.toLowerCase()) || pd.includes(w.toLowerCase()));
    const inZone = zones.includes(p.zone);
    if (hitKw.length || inZone) matchedPosts.push({ post:p, byKeyword:hitKw.length > 0 });
  }
  matchedPosts.sort((a, b) => (Number(b.byKeyword) - Number(a.byKeyword)) || ((b.post.created || 0) - (a.post.created || 0)));

  // ③c 站内检索：社区成员
  const users = getUsers().filter(u => !u.isMe);
  const matchedUsers = [];
  for (const u of users) {
    const us = (u.skills || []).join(' ').toLowerCase();
    const un = String(u.name || '').toLowerCase();
    const ub = String(u.bio || '').toLowerCase();
    const hitKw = kws.filter(w => us.includes(w.toLowerCase()) || un.includes(w.toLowerCase()) || ub.includes(w.toLowerCase()));
    const inZone = (u.zones || []).some(z => zones.includes(z));
    if (hitKw.length || inZone) matchedUsers.push({ user:u, byKeyword:hitKw.length > 0 });
  }
  matchedUsers.sort((a, b) => (Number(b.byKeyword) - Number(a.byKeyword)));
  const topUsers = matchedUsers.slice(0, 4).map(m => m.user);

  const matches = matchedLetters.map(m => m.letter);
  const hasInSiteMatches = matches.length || matchedPosts.length || matchedUsers.length;

  // ④ 组织检索上下文（RAG）：把站内命中的内容交给大模型，让它据此生成回答
  const ctxLines = [];
  if (matchedLetters.length) {
    ctxLines.push('【站内搭子帖】');
    matchedLetters.slice(0, 6).forEach(m => {
      const z = ZONE_BY_ID[m.letter.zone];
      ctxLines.push(`- ${z ? z.name : ''}：${String(m.letter.content || '').slice(0, 60)}`);
    });
  }
  if (matchedPosts.length) {
    ctxLines.push('【技能广场帖子】');
    matchedPosts.slice(0, 6).forEach(m =>
      ctxLines.push(`- [${m.post.type === 'offer' ? '能教' : (m.post.type === 'team' ? '组队' : '想学')}] ${m.post.title}${m.post.desc ? '：' + String(m.post.desc).slice(0, 50) : ''}`));
  }
  if (matchedUsers.length) {
    ctxLines.push('【相关成员】');
    matchedUsers.slice(0, 6).forEach(m =>
      ctxLines.push(`- ${m.user.name}（${(m.user.skills || []).join('、')}）`));
  }
  const ctx = ctxLines.length ? ctxLines.join('\n') : '（站内暂无直接相关的内容）';
  const meSkills = (getMe().skills || []).join('、') || '未知';
  const znames = zones.map(z => ZONE_BY_ID[z]?.name).filter(Boolean);

  // ⑤ 交给大模型生成回答（这才是真正的 AI 环节）；未配置或失败时本地兜底
  const llm = await callLLM(
    '你是微光社区的 AI 寻友助手。你会收到：用户的问题、用户技能，以及系统从社区里检索到的候选内容（搭子帖 / 技能帖 / 成员）。'
    + '请用亲切、口语化的中文回答，不超过 160 字。规则：'
    + '1) 若站内有相关内容，先说明找到了什么、涉及哪个分区，并引导用户点下方卡片或去信封墙；'
    + '2) 若站内没有相关内容，就正常回答用户的通用问题（可以是社区之外的知识），并在合适时建议去社区发帖找搭子；'
    + '3) 严禁编造站内检索结果里不存在的内容。',
    `用户的问题：${q}\n用户技能：${meSkills}\n\n【站内检索结果】\n${ctx}`
  );

  let summary, aiGenerated = false;
  if (llm) {
    summary = llm; aiGenerated = true;
  } else {
    // ---- 本地兜底（未配置大模型时）----
    let inSiteSummary = '';
    if (hasInSiteMatches) {
      const parts = [];
      if (matches.length) parts.push(`${matches.length} 封搭子帖`);
      if (matchedPosts.length) parts.push(`${matchedPosts.length} 条技能帖`);
      if (matchedUsers.length) parts.push(`${matchedUsers.length} 位相关伙伴`);
      inSiteSummary = `站内帮你找到了 ${parts.join('、')}${znames.length ? `（${znames.join('、')}）` : ''} 📨 点下方卡片看详情，或进信封墙翻全部。`;
    }
    const isQuestion = /[?？]$|^(怎么|如何|为什么|什么是|哪|怎么才能|怎样才能)/.test(q);
    let externalAnswer = '';
    if (!hasInSiteMatches && isQuestion) externalAnswer = localAnswer(q, kws, znames);
    summary = [inSiteSummary, externalAnswer].filter(Boolean).join('\n\n')
      || (kws.length
        ? `我在社区里翻了一圈，暂时没有和「${kws.join('、')}」直接相关的内容。换个说法，或去信箱里发一封搭子帖，很快就有人回应～`
        : `没太听清你想找什么。可以说具体点，比如「周末想约羽毛球」或「怎么学吉他入门」。`);
  }

  return { ok:true, query:q, keywords:kws, zones, matches,
    matchedPosts: matchedPosts.map(m => m.post), matchedUsers: topUsers,
    summary, external: aiGenerated, ai: aiGenerated, configured: aiConfigured(),
    aiError: aiGenerated ? '' : lastAIError };
}

// 本地知识兜底（无 LLM 时回答常见站外问题）
function localAnswer(q, kws, znames) {
  if (/怎么.*(学|入门|开始).*?(吉他|钢琴|画画|编程|游泳|健身|瑜伽|羽毛球|篮球)/.test(q) || /^(怎么|如何).*(学|入门|开始)/.test(q)) {
    const skill = (q.match(/(吉他|钢琴|画画|编程|游泳|健身|瑜伽|羽毛球|篮球|滑板)/) || [])[0];
    if (skill) return `学${skill}入门的话，建议先从基础姿势/指法/节奏感开始，每天练20-30分钟比一周猛练一次效果好得多。\n\n💡 社区里可能有会${skill}的伙伴愿意带你，去技能广场发一条「想学${skill}，求带入门」的帖子，或者点上面的信封看看有没有现成的${skill}搭子帖。`;
  }
  if (/(附近|哪里|哪有|哪儿|什么地方).*(球场|健身房|游泳池|图书馆|咖啡|奶茶|店)/.test(q)) {
    const place = (q.match(/(球场|健身房|游泳池|图书馆|咖啡|奶茶|店|食堂|操场)/) || [])[0];
    if (place) return `学校周边的${place}信息，建议查一下学校官网的校园地图，或者问同宿舍的学长学姐最准。\n\n💡 社区里也许有伙伴也常去同一个${place}，去信封墙发一条「有没有人常去XX${place}，求带路」说不定就找到同好了。`;
  }
  if (/(怎么|如何).*(约|找|组).*(人|搭子|朋友|队)/.test(q)) {
    return `找搭子最有效的方式：① 在社区信封墙发一封搭子帖，写清楚你想做什么、什么时间、什么水平；② 去技能广场看有没有人发了「能教/想学」的帖子；③ 点沙盘上的建筑，看同区有没有你认识的伙伴。\n\n社区里大多数伙伴都是这样找到搭子的，试试看！`;
  }
  return `这个问题我不太确定答案，建议你搜一下或者问问身边的朋友。\n\n💡 如果和社区搭子/学技能/约局有关，可以在信封墙发个帖，社区里说不定有人能帮你。`;
}
