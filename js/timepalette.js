// ==================== 时段配色（5 档） ====================
// 与 3D 沙盘同一套时段划分：凌晨 / 早晨 / 正午 / 傍晚 / 夜间。
// 这里只提供「页面级 CSS 变量」，供聊天页等普通页面跟随真实时间换色。
// 用法：
//   import { applyPeriod, autoPeriod, PERIOD_ORDER } from './js/timepalette.js';
//   applyPeriod(autoPeriod());          // 按当前真实时间配色
//   applyPeriod('dusk');                // 或指定时段

export const PERIOD_ORDER = ['wee', 'morning', 'noon', 'dusk', 'night'];

export const PERIODS = {
  wee: {
    name: '凌晨', icon: '🌙',
    bg: 'radial-gradient(120% 120% at 70% 8%,#16143a 0%,#07060f 62%)',
    nav: 'rgba(8,7,18,.86)',
    card: 'linear-gradient(180deg,rgba(26,24,56,.94),rgba(11,10,24,.96))',
    head: 'linear-gradient(90deg,rgba(146,152,255,.20),rgba(92,225,230,.05))',
    me: 'linear-gradient(100deg,#474da6,#6a6ade)',
    ta: 'rgba(255,255,255,.075)',
    text: '#e9e9f2', muted: '#8f8fa6', line: 'rgba(255,255,255,.11)',
    accent: '#9298ff', accent2: '#5ce1e6',
  },
  morning: {
    name: '早晨', icon: '🌤',
    bg: 'radial-gradient(120% 120% at 70% 8%,#2e3d5e 0%,#0d1220 62%)',
    nav: 'rgba(20,23,33,.85)',
    card: 'linear-gradient(180deg,rgba(31,40,63,.94),rgba(13,17,28,.96))',
    head: 'linear-gradient(90deg,rgba(255,197,122,.22),rgba(120,170,235,.12))',
    me: 'linear-gradient(100deg,#b57a2c,#d8a84c)',
    ta: 'rgba(255,255,255,.075)',
    text: '#eef2f8', muted: '#93a0b5', line: 'rgba(255,255,255,.12)',
    accent: '#ffd08a', accent2: '#8fc4ff',
  },
  noon: {
    name: '正午', icon: '☀️',
    bg: 'radial-gradient(120% 120% at 70% 8%,#5c5230 0%,#191509 62%)',
    nav: 'rgba(40,38,26,.88)',
    card: 'linear-gradient(180deg,rgba(60,54,33,.94),rgba(23,20,11,.96))',
    head: 'linear-gradient(90deg,rgba(255,214,120,.26),rgba(255,255,255,.07))',
    me: 'linear-gradient(100deg,#b3811f,#d9b445)',
    ta: 'rgba(255,255,255,.085)',
    text: '#f6f2e4', muted: '#a79f83', line: 'rgba(255,255,255,.14)',
    accent: '#ffd977', accent2: '#ffe9a8',
  },
  dusk: {
    name: '傍晚', icon: '🌇',
    bg: 'radial-gradient(120% 120% at 70% 8%,#652f22 0%,#150b11 62%)',
    nav: 'rgba(26,15,14,.86)',
    card: 'linear-gradient(180deg,rgba(53,28,26,.94),rgba(20,11,14,.96))',
    head: 'linear-gradient(90deg,rgba(255,138,69,.24),rgba(180,90,140,.14))',
    me: 'linear-gradient(100deg,#b64d18,#e08340)',
    ta: 'rgba(255,255,255,.085)',
    text: '#f8ece4', muted: '#a88b80', line: 'rgba(255,255,255,.13)',
    accent: '#ff9a5c', accent2: '#ffb98a',
  },
  night: {
    name: '夜间', icon: '🌜',
    bg: 'radial-gradient(120% 120% at 70% 8%,#1a1530 0%,#0b0a13 62%)',
    nav: 'rgba(11,10,19,.82)',
    card: 'linear-gradient(180deg,rgba(24,21,42,.94),rgba(12,11,20,.96))',
    head: 'linear-gradient(90deg,rgba(255,122,92,.18),rgba(92,225,230,.08))',
    me: 'linear-gradient(100deg,#b04430,#e06b4b)',
    ta: 'rgba(255,255,255,.07)',
    text: '#e9e9f2', muted: '#8a8a9c', line: 'rgba(255,255,255,.10)',
    accent: '#ff7a5c', accent2: '#5ce1e6',
  },
};

// 与 sandbox.html 的 autoVisual() 完全一致的分档
export function autoPeriod(d) {
  const h = (d || new Date()).getHours();
  if (h >= 2 && h < 6) return 'wee';
  if (h >= 6 && h < 9) return 'morning';
  if (h >= 9 && h < 16) return 'noon';
  if (h >= 16 && h < 19) return 'dusk';
  return 'night';
}

// 把某个时段写成 CSS 变量挂到 <html> 上（页面样式用 var(--cp-*) 取用）
export function applyPeriod(key) {
  const P = PERIODS[key] || PERIODS.night;
  const r = document.documentElement.style;
  const map = {
    '--cp-bg': P.bg, '--cp-nav': P.nav, '--cp-card': P.card, '--cp-head': P.head,
    '--cp-me': P.me, '--cp-ta': P.ta, '--cp-text': P.text, '--cp-muted': P.muted,
    '--cp-line': P.line, '--cp-accent': P.accent, '--cp-accent2': P.accent2,
  };
  for (const k in map) r.setProperty(k, map[k]);
  document.documentElement.dataset.period = key;
  return P;
}

export default { PERIODS, PERIOD_ORDER, autoPeriod, applyPeriod };
