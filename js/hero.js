/* ============ 首页 · 社区漫游视频（全屏铺满 / 经典脚本，兼容 file:// 直开） ============ */
/* 为什么不用 ES Module：直接双击 index.html 时浏览器会拦截 module 与 fetch，
   页面会白屏。这段是「经典脚本」，file:// 和 http:// 下都能跑。
   素材：assets/intro/community-tour.mp4（1080p H.264，30s 循环，自带分区标注与角色登场）。
   声音：默认尝试带声音自动播放；浏览器拦截时自动改为静音起播，
   首次点击页面即恢复声音——尽量满足「一开始不静音」的预期。 */

(function () {
  var ENTER_URL  = './sandbox.html';   // 点「进入首页」去的地方（要改目的地改这一行）
  var BUTTON_AT  = 3;                  // 视频到 3s：浮现「进入首页」按钮
  var LEAVE_MS   = 620;                // 过场淡出时长（与 css 的 leaving 动画对齐）

  function mountIntro() {
    var root  = document.getElementById('intro');
    if (!root) return null;
    var vmain = document.getElementById('ivmain');
    var vblur = document.getElementById('ivblur');
    var title = document.getElementById('ititle');
    var btn   = document.getElementById('ienter');
    var sound = document.getElementById('isound');
    var hint  = document.getElementById('ihint');

    var FILE_MODE = location.protocol === 'file:';   // 直开模式：只能看视频，进不了沙盘
    var timers = [];
    var leaving = false;
    var revealed = false;                            // 按钮是否已放出（只放一次）
    function later(fn, ms) { timers.push(setTimeout(fn, ms)); }

    /* ---------- 1. 播放（先试带声音，被拦再静音兜底；铺底层始终静音） ---------- */
    var started = false;
    function playBlur() {
      if (!vblur) return;
      var p = vblur.play();
      if (p && p.catch) p.catch(function () {});   // 铺底被拦也无妨，首次交互再补
    }
    function start() {
      if (started) return;
      started = true;
      playBlur();
      var p = vmain.play();
      if (p && p.catch) {
        p.catch(function () {                        // 带声音被拦 → 静音起播 + 提示
          vmain.muted = true;
          syncSoundBtn();
          var p2 = vmain.play();
          if (p2 && p2.catch) {
            p2.catch(function () { showPlayTip('点击画面播放视频'); });
          } else {
            showPlayTip('已静音播放 · 点击画面开启声音');
          }
        });
      }
    }
    function showPlayTip(text) {
      hint.textContent = text;
      hint.classList.add('show');
      root.style.cursor = 'pointer';
      later(hideTip, 5200);
    }
    function hideTip() { hint.classList.remove('show'); root.style.cursor = ''; }
    if (vmain.readyState >= 3) start();
    else vmain.addEventListener('loadeddata', start, { once: true });
    later(function () { if (!vmain.currentTime) start(); }, 2600);   // 兜底再推一次

    /* 首次交互：若当前因浏览器策略被静音，恢复声音 */
    function unmuteOnce() {
      playBlur();                                    // 铺底层若被拦，一并补播
      if (vmain.muted) {
        vmain.muted = false;
        vmain.volume = 1;
        syncSoundBtn();
        var p = vmain.play(); if (p && p.catch) p.catch(function () {});
      }
      hideTip();
    }
    root.addEventListener('pointerdown', unmuteOnce, { once: true });

    /* ---------- 2. 冰块按钮：约 3s 浮现（视频循环后不重复） ---------- */
    function reveal() {
      if (revealed) return;
      revealed = true;
      btn.classList.add('show');
      title.classList.remove('show');
      title.classList.add('hide');
    }
    function onTime() {
      var t = vmain.currentTime || 0;
      if (t >= BUTTON_AT) reveal();
      /* 两层视频保持同步：漂移超过 0.35s 就对齐（模糊层慢一点/快一点都看不出，但要兜住） */
      if (vblur && !vblur.paused) {
        var dt = vblur.currentTime - t;
        if (dt > 0.35 || dt < -0.35) {
          try { vblur.currentTime = t; } catch (e) {}
        }
      }
    }
    vmain.addEventListener('timeupdate', onTime);
    vmain.addEventListener('seeking', onTime);
    vmain.addEventListener('error', function () {    // 视频读不出来也不能把人堵在门口
      reveal();
      hint.textContent = FILE_MODE ? '视频未能加载（可重开本页试试）' : '视频加载失败，可直接进入';
      hint.classList.add('show');
    });

    title.classList.add('show');
    later(function () { hint.classList.add('show'); }, 700);
    later(hideTip, 5200);

    /* ---------- 2.5 看门狗：视频万一不推进，也绝不让页面「打不开」 ---------- */
    /* 用 setInterval 而不是 requestAnimationFrame：后台标签里 rAF 会被完全停掉，
       定时器至少还能以 1s 的频率跑，兜底不会失效。 */
    var born = Date.now(), lastT = -1, lastMove = Date.now();
    function tick() {
      var t = vmain.currentTime || 0;
      if (t >= BUTTON_AT) reveal();
      if (t > lastT + 0.15) { lastT = t; lastMove = Date.now(); }
      if ((Date.now() - lastMove) > 3200 && t < 0.6 && !revealed) showPlayTip('点击画面播放视频');
      if ((Date.now() - born) > 16000 && t < 1 && !revealed) {       // 兜底：别把人堵在门口
        reveal();
        hint.textContent = '视频未能播放，可直接进入';
        hint.classList.add('show');
      }
    }
    var wd = setInterval(tick, 350);
    timers.push(wd);

    /* ---------- 3. 跳转 ---------- */
    function go(url) {
      if (leaving) return;
      leaving = true;
      for (var i = 0; i < timers.length; i++) clearTimeout(timers[i]);
      root.classList.add('leaving');
      try { vmain.pause(); } catch (e) {}
      setTimeout(function () { location.href = url; }, LEAVE_MS);
    }
    /* 直开（file://）时：直接尝试在新标签打开本机已启动的服务器（固定 8000 端口）；
       同时把正确地址提示出来，避免「进不去」还不知道怎么办。 */
    function goViaServer() {
      var url = 'http://127.0.0.1:8000/sandbox.html';
      hint.textContent = '正在为你打开本地服务器上的沙盘：' + url;
      hint.classList.add('show');
      var w = window.open(url, '_blank');
      if (!w) {
        hint.textContent = '浏览器拦了弹窗。请先双击「启动服务器.bat」，再访问 ' + url;
      }
    }
    btn.addEventListener('click', function () { FILE_MODE ? goViaServer() : go(ENTER_URL); });

    window.addEventListener('keydown', function (e) {
      if (e.code === 'Space' || e.code === 'Escape' || e.code === 'Enter') {
        e.preventDefault();
        if (FILE_MODE) { goViaServer(); return; }
        if (e.code === 'Enter' && btn.classList.contains('show')) go(ENTER_URL);
        else go(ENTER_URL);
      }
    });

    /* ---------- 4. 声音开关 ---------- */
    function syncSoundBtn() {
      if (sound) {
        sound.textContent = vmain.muted ? '🔇' : '🔊';
        sound.classList.toggle('off', vmain.muted);
      }
    }
    if (sound) {
      sound.addEventListener('click', function (e) {
        e.stopPropagation();                         // 别触发页面的 unmuteOnce
        vmain.muted = !vmain.muted;
        vmain.volume = 1;
        if (!vmain.muted) {
          var p = vmain.play(); if (p && p.catch) p.catch(function () {});
        }
        syncSoundBtn();
      });
    }
    syncSoundBtn();                                  // 初始即为「有声」状态

    /* ---------- 5. 顶栏问候 ---------- */
    var PERIODS = [[5, '凌晨', '凌晨好'], [9, '早晨', '早上好'], [12, '上午', '上午好'],
                   [14, '中午', '中午好'], [18, '下午', '下午好'], [23, '晚间', '晚上好'], [24, '深夜', '夜深了']];
    var now = new Date(), hh = now.getHours(), pi = 0;
    while (pi < PERIODS.length - 1 && hh >= PERIODS[pi][0]) pi++;
    var helloEl = document.getElementById('ihello');
    if (helloEl) helloEl.textContent = PERIODS[pi][2] + '，欢迎来到微光社区';

    window.__intro = { video: vmain, showButton: reveal, go: go, fileMode: FILE_MODE };

    /* file:// 直开时，常驻一条提示，明确告诉用户正确入口（避免「进不去」却不知原因） */
    if (FILE_MODE) {
      var warn = document.createElement('div');
      warn.style.cssText = 'position:absolute;left:50%;top:82px;transform:translateX(-50%);z-index:8;'
        + 'background:rgba(120,46,22,.9);color:#ffe6c8;font-size:12.5px;letter-spacing:.5px;'
        + 'padding:9px 16px;border-radius:12px;box-shadow:0 8px 22px rgba(0,0,0,.35);'
        + 'text-align:center;max-width:88%;line-height:1.7';
      warn.innerHTML = '⚠ 你正在用 file:// 直接打开，沙盘（WebGL + .glb 模型）无法在此加载。<br>'
        + '请双击项目里的 <b>启动服务器.bat</b>，浏览器会自动打开 '
        + '<b>http://127.0.0.1:8000/index.html</b>，再点「进入首页」即可。';
      root.appendChild(warn);
    }
    return window.__intro;
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mountIntro);
  else mountIntro();
})();
