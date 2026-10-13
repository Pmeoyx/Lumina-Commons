/* ============ 首页入场动画 · 编排（视频版） ============ */
/* 八个分区的角色在沙盘里依次登场 → 全员到齐（视频 11s）→ 角色脚底浮出冰块按钮「进入首页」。
   右下角常驻「快进」，一键跳过动画直接进 3D 沙盘。
   素材：assets/intro/hero-intro.mp4（已去水印、气泡里的字改为「喵」）。 */

const ENTER_URL  = './sandbox.html';   // 点「进入首页」去的地方（要改目的地改这一行）
const SKIP_URL   = './sandbox.html';   // 「快进」去的地方 = 沙盘模型页面
const BUTTON_AT  = 11;                 // 视频到 11s：人物脚底开始出现按钮
const LEAVE_MS   = 620;                // 过场淡出时长（与 css 的 leaving 动画对齐）
const TITLE_HIDE = 6.5;                // 品牌字退场时刻

export function mountIntro() {
  const root  = document.getElementById('intro');
  if (!root) return null;
  const vmain = document.getElementById('ivmain');
  const vbg   = document.getElementById('ivbg');
  const title = document.getElementById('ititle');
  const btn   = document.getElementById('ienter');
  const skip  = document.getElementById('iskip');
  const sound = document.getElementById('isound');
  const hint  = document.getElementById('ihint');

  const timers = [];
  const later = (fn, ms) => timers.push(setTimeout(fn, ms));
  let leaving = false;

  /* ---------- 1. 播放 ---------- */
  const kickBg = () => { if (vbg) vbg.play().catch(() => {}); };
  const syncBg = () => {                        // 背景层偏差大了才校正，避免来回 seek
    if (!vbg || vbg.readyState < 2) return;
    if (Math.abs((vbg.currentTime || 0) - (vmain.currentTime || 0)) > 0.35) {
      vbg.currentTime = vmain.currentTime;
    }
  };
  const start = () => {
    const p = vmain.play();
    kickBg();
    if (p && p.catch) {
      p.catch(() => {                           // 自动播放被拦：点一下再播
        hint.textContent = '点击播放动画';
        hint.classList.add('show');
        const kick = () => {
          hint.classList.remove('show');
          vmain.play().catch(() => {});
          kickBg();
          root.removeEventListener('pointerdown', kick);
        };
        root.addEventListener('pointerdown', kick);
      });
    }
  };
  if (vmain.readyState >= 3) start();
  else vmain.addEventListener('loadeddata', start, { once: true });
  later(() => { if (!vmain.currentTime) start(); }, 2600);   // 兜底再推一次

  /* ---------- 2. 冰块按钮贴在「人物脚底」 ---------- */
  /* 视频 4:3、用 object-fit:contain 完整显示（不裁角色），
     所以按钮位置要按视频真正显示出来的矩形算，不能直接按视口底部定。 */
  const VW = 960, VH = 720;
  function place() {
    const iw = window.innerWidth, ih = window.innerHeight;
    const s = Math.min(iw / VW, ih / VH);
    const dh = VH * s;
    const below = (ih - dh) / 2;                // 视频下边缘到视口底的距离
    const h = btn.offsetHeight || 64;
    btn.style.bottom = 'auto';
    btn.style.top = `${Math.round(ih - below - dh * 0.075 - h)}px`;
  }
  place();
  window.addEventListener('resize', place);

  /* ---------- 3. 时间轴：11s 出按钮 ---------- */
  const reveal = () => {
    btn.classList.add('show');
    title.classList.add('hide');
    place();
  };
  const onTime = () => {
    const t = vmain.currentTime || 0;
    if (t >= BUTTON_AT) { reveal(); syncBg(); }
    if (t >= TITLE_HIDE) title.classList.remove('show');
  };
  vmain.addEventListener('timeupdate', onTime);
  vmain.addEventListener('seeking', onTime);
  vmain.addEventListener('ended', reveal);
  vmain.addEventListener('error', () => {        // 视频读不出来也不能把人堵在门口
    reveal();
    hint.textContent = '动画加载失败，可直接进入';
    hint.classList.add('show');
  });

  title.classList.add('show');
  later(() => hint.classList.add('show'), 700);
  later(() => hint.classList.remove('show'), 5200);

  /* ---------- 4. 跳转 ---------- */
  function go(url) {
    if (leaving) return;
    leaving = true;
    timers.forEach(clearTimeout);
    root.classList.add('leaving');
    try { vmain.pause(); if (vbg) vbg.pause(); } catch (e) {}
    setTimeout(() => { location.href = url; }, LEAVE_MS);
  }
  btn.addEventListener('click', () => go(ENTER_URL));
  skip.addEventListener('click', () => go(SKIP_URL));

  const onKey = e => {
    if (e.code === 'Space' || e.code === 'Escape' || e.code === 'Enter') {
      e.preventDefault();
      if (e.code === 'Enter' && btn.classList.contains('show')) go(ENTER_URL);
      else go(SKIP_URL);
    }
  };
  window.addEventListener('keydown', onKey);

  /* ---------- 5. 声音开关（默认静音浏览器才允许自动播放） ---------- */
  if (sound) {
    sound.addEventListener('click', () => {
      const wasMuted = vmain.muted;
      vmain.muted = !wasMuted;
      vmain.volume = 1;
      if (wasMuted) { vmain.play().catch(() => {}); kickBg(); }
      sound.textContent = wasMuted ? '🔊' : '🔇';
      sound.classList.toggle('on', wasMuted);
    });
  }

  window.__intro = { video: vmain, showButton: reveal, go };

  /* 调试用：index.html?t=11.6 → 直接跳到该时刻，方便核对按钮出现的位置 */
  const t0 = parseFloat(new URLSearchParams(location.search).get('t'));
  if (!isNaN(t0)) {
    const seek = () => { try { vmain.currentTime = t0; } catch (e) {} onTime(); };
    if (vmain.readyState >= 2) seek();
    else vmain.addEventListener('loadeddata', seek, { once: true });
  }
  return window.__intro;
}
