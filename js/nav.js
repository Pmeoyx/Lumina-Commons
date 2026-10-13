// ============ 顶部导航注入 ============
// 每个页面在 <body data-nav="sandbox"> 后引入本模块，自动挂载导航并高亮当前页。

const PAGES = [
  { href:'index.html',   key:'home',    label:'首页' },
  { href:'sandbox.html', key:'sandbox', label:'3D 沙盘' },
  { href:'skills.html',  key:'skills',  label:'技能广场' },
  { href:'profile.html', key:'profile', label:'个人中心' },
];

export function mountNav(activeKey) {
  const nav = document.createElement('nav');
  nav.id = 'topnav';
  let html = '<span class="brand"><span class="brand-light">微光</span><b>社区</b> · <i>Lumina Commons</i></span>';
  for (const p of PAGES) {
    const cls = p.key === activeKey ? ' class="active"' : '';
    html += `<a href="${p.href}"${cls}>${p.label}</a>`;
  }
  html += '<span class="spacer"></span>';
  nav.innerHTML = html;
  document.body.prepend(nav);
}
