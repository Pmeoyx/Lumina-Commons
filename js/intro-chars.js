/* ============ 首页入场动画 · 八个区的代表角色 ============ */
/* 严格按用户给的参考图重绘：扁平 Q 版、无描边、大头圆眼、低双马尾/侧发。
   viewBox 统一 0 0 200 320，分组供动画驱动：
     .b 身体整体（呼吸/蹦跳）  .h 头+头发+帽子（摆动/低头，原点脖颈 100,156）
     .a-l/.a-r 左右臂（原点肩 76/124,162）  .gaze 双眼（眨眼，原点 100,118）
     .prop/.prop2 道具（原点见 intro.css）
   关键高度：帽顶 ~26 · 眼 116 · 下巴 ~152 · 肩 158 · 脚底 ~292            */

export const CHARS = [
  /* ① 志愿服务区 —— 橙红棒球帽(白爱心) + 黑色低双马尾 + 黄耳环 + 红马甲(白X带/白十字) + 右臂红袖章 + 米色长裤 + 急救箱 */
  { key: 'vol', zone: '志愿服务区', svg: `
<g class="b">
  <rect x="92" y="144" width="16" height="20" fill="#ffe3cb"/>
  <path d="M70 156 L130 156 L136 252 L64 252 Z" fill="#ffffff"/>
  <path d="M74 158 L92 158 L100 176 L108 158 L126 158 L131 248 L69 248 Z" fill="#ef4a28"/>
  <path d="M76 160 L86 156 L126 214 L116 220 Z" fill="#ffffff"/>
  <path d="M124 160 L114 156 L74 214 L84 220 Z" fill="#ffffff"/>
  <path d="M78 194 L82 194 L82 190 L86 190 L86 194 L90 194 L90 198 L86 198 L86 202 L82 202 L82 198 L78 198 Z" fill="#ffffff"/>
  <path d="M68 248 L98 248 L98 292 L64 292 Z" fill="#f0e3cd"/>
  <path d="M102 248 L132 248 L136 292 L102 292 Z" fill="#f0e3cd"/>
  <ellipse cx="79" cy="291" rx="16" ry="8" fill="#e23c28"/>
  <ellipse cx="121" cy="291" rx="16" ry="8" fill="#e23c28"/>
  <g class="a-l">
    <path d="M72 158 L58 160 L54 194 L68 198 Z" fill="#ffffff"/>
    <path d="M56 192 L70 196 L67 224 L57 222 Z" fill="#ffe3cb"/>
    <circle cx="62" cy="226" r="7" fill="#ffe3cb"/>
  </g>
  <g class="a-r">
    <path d="M128 158 L142 160 L146 194 L132 198 Z" fill="#ffffff"/>
    <path d="M131 166 L143 168 L144 184 L132 182 Z" fill="#e23c28"/>
    <path d="M131.5 171 L143.5 173 M132 177 L144 179" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>
    <path d="M132 192 L146 190 L149 218 L135 220 Z" fill="#ffe3cb"/>
    <circle cx="142" cy="222" r="7" fill="#ffe3cb"/>
  </g>
  <g class="prop">
    <path d="M52 228 Q62 216 72 228" fill="none" stroke="#c9c2b8" stroke-width="3.4" stroke-linecap="round"/>
    <rect x="40" y="228" width="44" height="38" rx="5" fill="#ffffff"/>
    <path d="M58 240 L66 240 L66 236 L70 236 L70 240 L74 240 L74 244 L70 244 L70 248 L66 248 L66 244 L58 244 Z" fill="#e23c28" transform="translate(0 4)"/>
  </g>
  <g class="h">
    <circle cx="100" cy="102" r="54" fill="#322a35"/>
    <rect x="46" y="116" width="20" height="100" rx="10" fill="#322a35"/>
    <rect x="134" y="116" width="20" height="100" rx="10" fill="#322a35"/>
    <ellipse cx="53" cy="112" rx="6" ry="9" fill="#ffe3cb"/>
    <ellipse cx="147" cy="112" rx="6" ry="9" fill="#ffe3cb"/>
    <ellipse cx="100" cy="110" rx="45" ry="42" fill="#ffe3cb"/>
    <circle cx="53" cy="124" r="4" fill="#ffd34d"/>
    <circle cx="147" cy="124" r="4" fill="#ffd34d"/>
    <path d="M58 94 C66 80 134 80 142 94 C128 86 72 86 58 94 Z" fill="#322a35"/>
    <path d="M100 30 C64 30 48 60 48 92 L152 92 C152 60 136 30 100 30 Z" fill="#f2502d"/>
    <path d="M48 84 C80 93 120 93 152 84 L152 92 C120 100 80 100 48 92 Z" fill="#d94322"/>
    <path d="M100 70 C92 60 84 54 84 47 C84 41 89 37 94 37 C97 37 100 40 100 40 C100 40 103 37 106 37 C111 37 116 41 116 47 C116 54 108 60 100 70 Z" fill="#ffffff"/>
    <g class="gaze">
      <circle cx="82" cy="116" r="9" fill="#2b2430"/>
      <circle cx="118" cy="116" r="9" fill="#2b2430"/>
      <circle cx="79" cy="112" r="3" fill="#ffffff"/>
      <circle cx="115" cy="112" r="3" fill="#ffffff"/>
    </g>
    <ellipse cx="66" cy="128" rx="6.5" ry="4" fill="#ffb0a8" opacity=".8"/>
    <ellipse cx="134" cy="128" rx="6.5" ry="4" fill="#ffb0a8" opacity=".8"/>
    <path d="M94 134 Q100 139 106 134" fill="none" stroke="#c9756a" stroke-width="2.4" stroke-linecap="round"/>
  </g>
</g>` },

  /* ② 动物守护区 —— 棕色猫耳 + 棕色波波头侧发 + 白衬衫棕背带裙 + 抱橘猫 + 右侧猫尾 */
  { key: 'pet', zone: '动物守护区', svg: `
<g class="b">
  <rect x="92" y="144" width="16" height="20" fill="#ffead9"/>
  <path d="M72 156 L128 156 L134 224 L66 224 Z" fill="#ffffff"/>
  <rect x="80" y="152" width="8" height="28" rx="3" fill="#a87a4e"/>
  <rect x="112" y="152" width="8" height="28" rx="3" fill="#a87a4e"/>
  <path d="M70 178 L130 178 L138 250 L62 250 Z" fill="#a87a4e"/>
  <path d="M70 250 L130 250 L132 268 L68 268 Z" fill="#fff3e2"/>
  <rect x="78" y="266" width="16" height="22" fill="#ffead9"/>
  <rect x="106" y="266" width="16" height="22" fill="#ffead9"/>
  <ellipse cx="82" cy="291" rx="17" ry="8" fill="#6b4a2f"/>
  <ellipse cx="118" cy="291" rx="17" ry="8" fill="#6b4a2f"/>
  <g class="a-l">
    <path d="M72 158 L60 162 L62 186 L74 186 Z" fill="#ffffff"/>
    <rect x="64" y="180" width="26" height="12" rx="6" fill="#ffead9" transform="rotate(32 64 180)"/>
    <circle cx="89" cy="197" r="7" fill="#ffead9"/>
  </g>
  <g class="a-r">
    <path d="M128 158 L140 162 L138 186 L126 186 Z" fill="#ffffff"/>
    <rect x="110" y="180" width="26" height="12" rx="6" fill="#ffead9" transform="rotate(-32 136 180)"/>
    <circle cx="111" cy="197" r="7" fill="#ffead9"/>
  </g>
  <rect x="76" y="180" width="48" height="38" rx="17" fill="#f2a65a"/>
  <circle cx="100" cy="180" r="17" fill="#f2a65a"/>
  <path d="M87 168 L84 155 L96 163 Z" fill="#f2a65a"/>
  <path d="M113 168 L116 155 L104 163 Z" fill="#f2a65a"/>
  <circle cx="94" cy="180" r="2.6" fill="#4a3220"/>
  <circle cx="106" cy="180" r="2.6" fill="#4a3220"/>
  <path d="M96 187 Q100 190 104 187" fill="none" stroke="#c9784a" stroke-width="1.8" stroke-linecap="round"/>
  <g class="prop">
    <path d="M134 234 C152 232 163 220 161 206 C170 218 165 242 138 246 Z" fill="#8a6242"/>
  </g>
  <g class="h">
    <circle cx="100" cy="100" r="55" fill="#8a6242"/>
    <path d="M66 58 L58 16 L94 44 Z" fill="#8a6242"/>
    <path d="M134 58 L142 16 L106 44 Z" fill="#8a6242"/>
    <path d="M71 51 L66 29 L86 43 Z" fill="#dba583"/>
    <path d="M129 51 L134 29 L114 43 Z" fill="#dba583"/>
    <path d="M54 96 C42 130 44 160 56 176 C66 164 68 130 66 100 Z" fill="#8a6242"/>
    <path d="M146 96 C158 130 156 160 144 176 C134 164 132 130 134 100 Z" fill="#8a6242"/>
    <ellipse cx="100" cy="110" rx="43" ry="40" fill="#ffead9"/>
    <path d="M60 92 C66 74 134 74 140 92 C126 80 74 80 60 92 Z" fill="#8a6242"/>
    <g class="gaze">
      <circle cx="82" cy="116" r="9" fill="#2b2430"/>
      <circle cx="118" cy="116" r="9" fill="#2b2430"/>
      <circle cx="79" cy="112" r="3" fill="#ffffff"/>
      <circle cx="115" cy="112" r="3" fill="#ffffff"/>
    </g>
    <ellipse cx="67" cy="128" rx="6.5" ry="4" fill="#ffb0a8" opacity=".8"/>
    <ellipse cx="133" cy="128" rx="6.5" ry="4" fill="#ffb0a8" opacity=".8"/>
    <path d="M95 134 Q100 138 105 134" fill="none" stroke="#c9756a" stroke-width="2.4" stroke-linecap="round"/>
  </g>
</g>` },

  /* ③ 卫生打扫区 —— 绿棒球帽(白云) + 黑色低双马尾 + 黄耳环 + 绿围裙(口袋) + 扫把 */
  { key: 'clean', zone: '卫生打扫区', svg: `
<g class="b">
  <rect x="92" y="144" width="16" height="20" fill="#ffe3cb"/>
  <path d="M70 156 L130 156 L136 252 L64 252 Z" fill="#ffffff"/>
  <rect x="82" y="152" width="7" height="26" rx="2.5" fill="#63b52e"/>
  <rect x="111" y="152" width="7" height="26" rx="2.5" fill="#63b52e"/>
  <path d="M74 172 L126 172 L134 248 L66 248 Z" fill="#63b52e"/>
  <rect x="86" y="208" width="28" height="24" rx="4" fill="#54a124"/>
  <rect x="76" y="248" width="18" height="34" fill="#ffe3cb"/>
  <rect x="106" y="248" width="18" height="34" fill="#ffe3cb"/>
  <rect x="70" y="276" width="28" height="20" rx="9" fill="#63b52e"/>
  <rect x="102" y="276" width="28" height="20" rx="9" fill="#63b52e"/>
  <g class="a-l">
    <path d="M72 158 L58 160 L54 192 L68 196 Z" fill="#ffffff"/>
    <path d="M56 190 L70 194 L68 222 L58 220 Z" fill="#ffe3cb"/>
    <circle cx="63" cy="224" r="7" fill="#ffe3cb"/>
  </g>
  <g class="a-r">
    <path d="M128 158 L142 158 L148 188 L134 192 Z" fill="#ffffff"/>
    <path d="M134 186 L148 184 L150 206 L136 208 Z" fill="#ffe3cb"/>
    <circle cx="143" cy="208" r="7.5" fill="#ffe3cb"/>
  </g>
  <g class="prop">
    <path d="M140 148 L146 146 L162 244 L156 246 Z" fill="#c9975a"/>
    <path d="M148 240 L186 250 L178 274 L140 264 Z" fill="#e8c36a"/>
    <path d="M152 246 L180 254 M149 254 L177 262 M146 262 L172 269" stroke="#c9a04e" stroke-width="1.8" stroke-linecap="round"/>
  </g>
  <g class="h">
    <circle cx="100" cy="102" r="54" fill="#322a35"/>
    <rect x="46" y="116" width="20" height="96" rx="10" fill="#322a35"/>
    <rect x="134" y="116" width="20" height="96" rx="10" fill="#322a35"/>
    <ellipse cx="53" cy="112" rx="6" ry="9" fill="#ffe3cb"/>
    <ellipse cx="147" cy="112" rx="6" ry="9" fill="#ffe3cb"/>
    <ellipse cx="100" cy="110" rx="45" ry="42" fill="#ffe3cb"/>
    <circle cx="53" cy="124" r="4" fill="#ffd34d"/>
    <circle cx="147" cy="124" r="4" fill="#ffd34d"/>
    <path d="M58 94 C66 80 134 80 142 94 C128 86 72 86 58 94 Z" fill="#322a35"/>
    <path d="M100 30 C64 30 48 60 48 92 L152 92 C152 60 136 30 100 30 Z" fill="#63b52e"/>
    <path d="M48 84 C80 93 120 93 152 84 L152 92 C120 100 80 100 48 92 Z" fill="#54a124"/>
    <path d="M87 62 C82 54 90 47 96 50 C99 43 112 43 114 51 C121 51 124 59 118 63 L88 63 Z" fill="#ffffff"/>
    <g class="gaze">
      <circle cx="82" cy="116" r="9" fill="#2b2430"/>
      <circle cx="118" cy="116" r="9" fill="#2b2430"/>
      <circle cx="79" cy="112" r="3" fill="#ffffff"/>
      <circle cx="115" cy="112" r="3" fill="#ffffff"/>
    </g>
    <ellipse cx="66" cy="128" rx="6.5" ry="4" fill="#ffb0a8" opacity=".8"/>
    <ellipse cx="134" cy="128" rx="6.5" ry="4" fill="#ffb0a8" opacity=".8"/>
    <path d="M92 132 C94 141 106 141 108 132 Z" fill="#e2604f"/>
  </g>
</g>` },

  /* ④ 体育运动区 —— 藏蓝粗双马尾 + 青色发带(白星) + 白卫衣(青心) + 青短裤 + 白球鞋 + 篮球 */
  { key: 'sport', zone: '体育运动区', svg: `
<g class="b">
  <rect x="92" y="144" width="16" height="20" fill="#ffe3cb"/>
  <path d="M70 156 L130 156 L136 218 L64 218 Z" fill="#f5f8ff"/>
  <path d="M100 190 C94 182 88 178 88 171 C88 166 92 163 95.5 163 C98 163 100 166 100 166 C100 166 102 163 104.5 163 C108 163 112 166 112 171 C112 178 106 182 100 190 Z" fill="#35c4d8"/>
  <path d="M68 214 L98 214 L97 244 L66 244 Z" fill="#35c4d8"/>
  <path d="M102 214 L132 214 L134 244 L103 244 Z" fill="#35c4d8"/>
  <rect x="74" y="242" width="16" height="34" fill="#ffe3cb"/>
  <rect x="110" y="242" width="16" height="34" fill="#ffe3cb"/>
  <rect x="66" y="272" width="30" height="22" rx="9" fill="#ffffff"/>
  <rect x="104" y="272" width="30" height="22" rx="9" fill="#ffffff"/>
  <rect x="66" y="285" width="30" height="5" fill="#35c4d8"/>
  <rect x="104" y="285" width="30" height="5" fill="#35c4d8"/>
  <g class="a-l">
    <path d="M70 158 L58 162 L58 190 L72 192 Z" fill="#f5f8ff"/>
    <rect x="64" y="186" width="24" height="11" rx="5.5" fill="#ffe3cb" transform="rotate(20 64 186)"/>
    <circle cx="89" cy="200" r="7" fill="#ffe3cb"/>
  </g>
  <g class="a-r">
    <path d="M130 158 L144 160 L150 186 L136 190 Z" fill="#f5f8ff"/>
    <rect x="134" y="184" width="22" height="11" rx="5.5" fill="#ffe3cb" transform="rotate(-24 156 184)"/>
    <circle cx="144" cy="198" r="7.5" fill="#ffe3cb"/>
  </g>
  <g class="prop">
    <circle cx="158" cy="196" r="20" fill="#e8762c"/>
    <path d="M158 176 L158 216 M138 196 L178 196" stroke="#b85a1c" stroke-width="2"/>
    <path d="M146 180 C152 190 152 202 146 212" fill="none" stroke="#b85a1c" stroke-width="2"/>
    <path d="M170 180 C164 190 164 202 170 212" fill="none" stroke="#b85a1c" stroke-width="2"/>
  </g>
  <g class="h">
    <circle cx="100" cy="100" r="53" fill="#2b3a6b"/>
    <path d="M56 100 C34 118 30 156 44 186 C60 176 68 140 66 108 Z" fill="#2b3a6b"/>
    <path d="M144 100 C166 118 170 156 156 186 C140 176 132 140 134 108 Z" fill="#2b3a6b"/>
    <ellipse cx="100" cy="110" rx="44" ry="41" fill="#ffe3cb"/>
    <path d="M60 92 C66 76 134 76 140 92 C124 82 76 82 60 92 Z" fill="#2b3a6b"/>
    <path d="M54 84 C70 76 130 76 146 84 L146 95 C130 87 70 87 54 95 Z" fill="#35c4d8"/>
    <path d="M100 76 L102.4 82 L109 82 L104 86.5 L106 93 L100 89 L94 93 L96 86.5 L91 82 L97.6 82 Z" fill="#ffffff"/>
    <g class="gaze">
      <circle cx="82" cy="116" r="9" fill="#232a45"/>
      <circle cx="118" cy="116" r="9" fill="#232a45"/>
      <circle cx="79" cy="112" r="3" fill="#ffffff"/>
      <circle cx="115" cy="112" r="3" fill="#ffffff"/>
    </g>
    <ellipse cx="66" cy="128" rx="6.5" ry="4" fill="#ffb0a8" opacity=".8"/>
    <ellipse cx="134" cy="128" rx="6.5" ry="4" fill="#ffb0a8" opacity=".8"/>
    <path d="M93 132 C95 140 105 140 107 132 Z" fill="#e2604f"/>
  </g>
</g>` },

  /* ⑤ 游戏娱乐区 —— 粉猫耳(浅内耳) + 深灰耳机 + 粉色侧发 + 粉卫衣(黄闪电) + 深蓝短裤 + 粉掌机 */
  { key: 'game', zone: '游戏娱乐区', svg: `
<g class="b">
  <rect x="92" y="144" width="16" height="20" fill="#ffe3cb"/>
  <path d="M70 156 L130 156 L136 218 L64 218 Z" fill="#ff6fb0"/>
  <path d="M102 172 L94 184 L100 184 L97 194 L106 182 L100 182 Z" fill="#ffd93d"/>
  <path d="M70 214 L130 214 L133 244 L103 244 L100 232 L97 244 L67 244 Z" fill="#2c2c44"/>
  <rect x="76" y="242" width="16" height="34" fill="#ffe3cb"/>
  <rect x="108" y="242" width="16" height="34" fill="#ffe3cb"/>
  <rect x="68" y="272" width="28" height="22" rx="9" fill="#ff9ccb"/>
  <rect x="104" y="272" width="28" height="22" rx="9" fill="#ff9ccb"/>
  <g class="a-l">
    <path d="M70 158 L56 164 L52 192 L66 196 Z" fill="#ff6fb0"/>
    <path d="M57 172 L67 176 M55 180 L65 184" stroke="#ffffff" stroke-width="2.4" stroke-linecap="round"/>
    <rect x="52" y="188" width="22" height="11" rx="5.5" fill="#ffe3cb" transform="rotate(28 52 188)"/>
    <circle cx="73" cy="206" r="7.5" fill="#ffe3cb"/>
  </g>
  <g class="a-r">
    <path d="M130 158 L144 164 L148 194 L134 198 Z" fill="#ff6fb0"/>
    <rect x="126" y="190" width="22" height="11" rx="5.5" fill="#ffe3cb" transform="rotate(-20 148 190)"/>
    <circle cx="127" cy="207" r="7.5" fill="#ffe3cb"/>
  </g>
  <g class="prop">
    <rect x="42" y="188" width="56" height="38" rx="12" fill="#ff8ec4"/>
    <circle cx="56" cy="206" r="4.5" fill="#4a4a66"/>
    <circle cx="84" cy="200" r="3.6" fill="#ffd93d"/>
    <circle cx="90" cy="210" r="3.6" fill="#7ce6a0"/>
    <circle cx="78" cy="212" r="3.6" fill="#6bb8ff"/>
  </g>
  <g class="h">
    <circle cx="100" cy="100" r="55" fill="#ff8ec4"/>
    <path d="M62 60 L50 14 L92 44 Z" fill="#ff6fb0"/>
    <path d="M138 60 L150 14 L108 44 Z" fill="#ff6fb0"/>
    <path d="M67 53 L59 27 L84 44 Z" fill="#ffc2dd"/>
    <path d="M133 53 L141 27 L116 44 Z" fill="#ffc2dd"/>
    <path d="M52 100 C44 136 48 172 58 196 C68 184 70 140 66 104 Z" fill="#ff8ec4"/>
    <path d="M148 100 C156 136 152 172 142 196 C132 184 130 140 134 104 Z" fill="#ff8ec4"/>
    <ellipse cx="100" cy="112" rx="43" ry="40" fill="#ffe3cb"/>
    <path d="M62 94 C68 78 132 78 138 94 C124 84 76 84 62 94 Z" fill="#ff8ec4"/>
    <path d="M48 80 C48 50 152 50 152 80" fill="none" stroke="#3a3a4a" stroke-width="8" stroke-linecap="round"/>
    <ellipse cx="44" cy="94" rx="13" ry="18" fill="#3a3a4a"/>
    <ellipse cx="156" cy="94" rx="13" ry="18" fill="#3a3a4a"/>
    <ellipse cx="44" cy="94" rx="6" ry="10" fill="#ff6fb0"/>
    <ellipse cx="156" cy="94" rx="6" ry="10" fill="#ff6fb0"/>
    <g class="gaze">
      <circle cx="82" cy="116" r="9" fill="#c63d8a"/>
      <circle cx="118" cy="116" r="9" fill="#c63d8a"/>
      <circle cx="79" cy="112" r="3" fill="#ffffff"/>
      <circle cx="115" cy="112" r="3" fill="#ffffff"/>
    </g>
    <ellipse cx="67" cy="128" rx="6.5" ry="4" fill="#ffb0a8" opacity=".85"/>
    <ellipse cx="133" cy="128" rx="6.5" ry="4" fill="#ffb0a8" opacity=".85"/>
    <path d="M93 132 C95 140 105 140 107 132 Z" fill="#e2608f"/>
  </g>
</g>` },

  /* ⑥ 学习备赛区 —— 米色学士帽(金流苏) + 棕色侧发 + 金圆眼镜 + 白长袍(金V领/书本纹/金边) */
  { key: 'study', zone: '学习备赛区', svg: `
<g class="b">
  <rect x="92" y="144" width="16" height="20" fill="#ffead9"/>
  <path d="M70 156 L130 156 L142 262 L58 262 Z" fill="#f7f2e2"/>
  <path d="M82 156 L100 178 L92 185 L74 160 Z" fill="#e8c76a"/>
  <path d="M118 156 L100 178 L108 185 L126 160 Z" fill="#e8c76a"/>
  <rect x="82" y="190" width="36" height="28" rx="3" fill="#7a4a28"/>
  <rect x="86" y="194" width="13" height="20" fill="#ffffff"/>
  <rect x="101" y="194" width="13" height="20" fill="#ffffff"/>
  <rect x="62" y="240" width="76" height="9" fill="#e8c76a"/>
  <rect x="80" y="262" width="14" height="18" fill="#ffead9"/>
  <rect x="106" y="262" width="14" height="18" fill="#ffead9"/>
  <ellipse cx="82" cy="286" rx="17" ry="9" fill="#5a3a26"/>
  <ellipse cx="118" cy="286" rx="17" ry="9" fill="#5a3a26"/>
  <g class="a-l">
    <path d="M70 158 L58 162 L62 198 L76 200 Z" fill="#f7f2e2"/>
    <circle cx="70" cy="205" r="7.5" fill="#ffead9"/>
  </g>
  <g class="a-r">
    <path d="M130 158 L142 162 L138 198 L124 200 Z" fill="#f7f2e2"/>
    <circle cx="130" cy="205" r="7.5" fill="#ffead9"/>
  </g>
  <g class="h">
    <circle cx="100" cy="100" r="53" fill="#6b4a34"/>
    <path d="M54 98 C46 132 48 162 58 180 C68 168 68 132 66 102 Z" fill="#6b4a34"/>
    <path d="M146 98 C154 132 152 162 142 180 C132 168 132 132 134 102 Z" fill="#6b4a34"/>
    <ellipse cx="100" cy="110" rx="44" ry="41" fill="#ffead9"/>
    <path d="M62 92 C68 78 132 78 138 92 C124 84 76 84 62 92 Z" fill="#6b4a34"/>
    <path d="M70 80 C82 73 118 73 130 80 L130 88 C118 81 82 81 70 88 Z" fill="#eadfbd"/>
    <path d="M100 22 L172 50 L100 78 L28 50 Z" fill="#f2e8c8"/>
    <path d="M100 22 L100 78 M28 50 L172 50" stroke="#dcc99a" stroke-width="1.6"/>
    <path d="M170 50 C177 70 173 92 165 106" fill="none" stroke="#e8b93a" stroke-width="3" stroke-linecap="round"/>
    <rect x="159" y="104" width="11" height="17" rx="3" fill="#e8b93a"/>
    <circle cx="83" cy="116" r="13.5" fill="#ffffff" fill-opacity=".12" stroke="#e8b93a" stroke-width="2.6"/>
    <circle cx="117" cy="116" r="13.5" fill="#ffffff" fill-opacity=".12" stroke="#e8b93a" stroke-width="2.6"/>
    <path d="M96.5 114 L103.5 114" stroke="#e8b93a" stroke-width="2.6"/>
    <path d="M69.5 112 L58 108 M130.5 112 L142 108" stroke="#e8b93a" stroke-width="2.2" stroke-linecap="round"/>
    <g class="gaze">
      <circle cx="83" cy="117" r="7" fill="#5a3a22"/>
      <circle cx="117" cy="117" r="7" fill="#5a3a22"/>
      <circle cx="80.5" cy="113.5" r="2.4" fill="#ffffff"/>
      <circle cx="114.5" cy="113.5" r="2.4" fill="#ffffff"/>
    </g>
    <ellipse cx="66" cy="130" rx="5.5" ry="3.6" fill="#ffb0a8" opacity=".7"/>
    <ellipse cx="134" cy="130" rx="5.5" ry="3.6" fill="#ffb0a8" opacity=".7"/>
    <path d="M95 136 Q100 140 105 136" fill="none" stroke="#c9756a" stroke-width="2.2" stroke-linecap="round"/>
  </g>
</g>` },

  /* ⑦ 餐饮美食区 —— 白厨师帽(面包标) + 金色双团卷发 + 橙围裙 + 深蓝裙 + 法棍 + 木勺 */
  { key: 'food', zone: '餐饮美食区', svg: `
<g class="b">
  <rect x="92" y="144" width="16" height="20" fill="#ffe3cb"/>
  <path d="M72 156 L128 156 L134 212 L66 212 Z" fill="#ffffff"/>
  <rect x="82" y="150" width="7" height="28" rx="2.5" fill="#f08a3a"/>
  <rect x="111" y="150" width="7" height="28" rx="2.5" fill="#f08a3a"/>
  <path d="M74 176 L126 176 L132 244 L68 244 Z" fill="#f08a3a"/>
  <path d="M68 244 L132 244 L136 262 L64 262 Z" fill="#3a3a44"/>
  <rect x="64" y="257" width="72" height="4" fill="#f08a3a"/>
  <rect x="78" y="262" width="16" height="24" fill="#ffe3cb"/>
  <rect x="106" y="262" width="16" height="24" fill="#ffe3cb"/>
  <ellipse cx="82" cy="290" rx="17" ry="9" fill="#7a5230"/>
  <ellipse cx="118" cy="290" rx="17" ry="9" fill="#7a5230"/>
  <g class="a-l">
    <path d="M72 158 L60 160 L56 194 L70 198 Z" fill="#ffffff"/>
    <path d="M58 192 L72 196 L68 220 L58 216 Z" fill="#ffe3cb"/>
    <circle cx="63" cy="221" r="7" fill="#ffe3cb"/>
  </g>
  <g class="a-r">
    <path d="M128 158 L142 156 L150 188 L136 192 Z" fill="#ffffff"/>
    <path d="M136 186 L150 182 L154 204 L140 208 Z" fill="#ffe3cb"/>
    <circle cx="148" cy="207" r="7.5" fill="#ffe3cb"/>
  </g>
  <g class="prop">
    <ellipse cx="158" cy="166" rx="12" ry="34" transform="rotate(16 158 166)" fill="#e0b062"/>
    <path d="M149 142 L159 147 M146 158 L156 163 M146 174 L156 179" stroke="#c9903e" stroke-width="2.2" stroke-linecap="round"/>
  </g>
  <g class="prop2">
    <rect x="57" y="198" width="4.5" height="30" rx="2.2" fill="#c9975a" transform="rotate(7 59 198)"/>
    <ellipse cx="56" cy="234" rx="7" ry="9" fill="#c9975a"/>
  </g>
  <g class="h">
    <circle cx="100" cy="100" r="53" fill="#f0cd7a"/>
    <circle cx="48" cy="122" r="22" fill="#f0cd7a"/>
    <circle cx="152" cy="122" r="22" fill="#f0cd7a"/>
    <ellipse cx="100" cy="110" rx="41" ry="39" fill="#ffe3cb"/>
    <path d="M64 94 C70 80 130 80 136 94 C122 86 78 86 64 94 Z" fill="#f0cd7a"/>
    <path d="M62 70 C52 42 72 24 100 24 C128 24 148 42 138 70 Z" fill="#fdfdff"/>
    <rect x="60" y="64" width="80" height="14" rx="7" fill="#f2f2f7"/>
    <ellipse cx="100" cy="46" rx="11" ry="8" fill="#e8a94a"/>
    <path d="M94 43 L98 47 M102 42 L106 46" stroke="#c9832e" stroke-width="1.6" stroke-linecap="round"/>
    <g class="gaze">
      <circle cx="82" cy="116" r="9" fill="#6b4a22"/>
      <circle cx="118" cy="116" r="9" fill="#6b4a22"/>
      <circle cx="79" cy="112" r="3" fill="#ffffff"/>
      <circle cx="115" cy="112" r="3" fill="#ffffff"/>
    </g>
    <ellipse cx="68" cy="128" rx="6.5" ry="4" fill="#ffb0a8" opacity=".8"/>
    <ellipse cx="132" cy="128" rx="6.5" ry="4" fill="#ffb0a8" opacity=".8"/>
    <path d="M93 132 C95 141 105 141 107 132 Z" fill="#e2604f"/>
  </g>
</g>` },

  /* ⑧ 工坊区 —— 紫黑刺猬头 + 紫发带 + 斜眉紫瞳小胡子 + 颈挂耳机 + 深灰背带裤(金扣) + 扳手 */
  { key: 'maker', zone: '工坊区', svg: `
<g class="b">
  <rect x="92" y="144" width="16" height="20" fill="#ffe3cb"/>
  <path d="M70 156 L130 156 L134 192 L66 192 Z" fill="#7a4ec4"/>
  <path d="M60 158 C60 145 140 145 140 158" fill="none" stroke="#5a34a0" stroke-width="9" stroke-linecap="round"/>
  <ellipse cx="58" cy="163" rx="10" ry="13" fill="#7a4ec4"/>
  <ellipse cx="142" cy="163" rx="10" ry="13" fill="#7a4ec4"/>
  <ellipse cx="58" cy="163" rx="5" ry="7" fill="#5a34a0"/>
  <ellipse cx="142" cy="163" rx="5" ry="7" fill="#5a34a0"/>
  <rect x="80" y="150" width="8" height="26" rx="2.5" fill="#3a3a44"/>
  <rect x="112" y="150" width="8" height="26" rx="2.5" fill="#3a3a44"/>
  <rect x="82" y="170" width="36" height="28" rx="3" fill="#3a3a44"/>
  <path d="M68 192 L132 192 L136 260 L64 260 Z" fill="#3a3a44"/>
  <rect x="68" y="208" width="14" height="18" rx="3" fill="#2e2e38"/>
  <rect x="118" y="208" width="14" height="18" rx="3" fill="#2e2e38"/>
  <rect x="95" y="202" width="10" height="16" rx="2" fill="#d9b23a"/>
  <rect x="64" y="260" width="32" height="32" rx="10" fill="#7a4ec4"/>
  <rect x="104" y="260" width="32" height="32" rx="10" fill="#7a4ec4"/>
  <rect x="64" y="284" width="32" height="6" fill="#5a34a0"/>
  <rect x="104" y="284" width="32" height="6" fill="#5a34a0"/>
  <g class="a-l">
    <path d="M70 158 L58 160 L54 194 L68 198 Z" fill="#7a4ec4"/>
    <rect x="53" y="192" width="17" height="13" rx="3.5" fill="#2a2233"/>
    <circle cx="61" cy="209" r="7" fill="#2a2233"/>
  </g>
  <g class="a-r">
    <path d="M130 158 L144 156 L152 190 L138 196 Z" fill="#7a4ec4"/>
    <rect x="136" y="192" width="17" height="13" rx="3.5" fill="#2a2233"/>
    <circle cx="146" cy="209" r="7.5" fill="#2a2233"/>
  </g>
  <g class="prop">
    <rect x="150" y="188" width="7" height="46" rx="3" fill="#d4d4e0" transform="rotate(-7 153 188)"/>
    <path d="M147 173 L163 169 L167 181 L159 183 L161 191 L153 193 L151 185 L143 187 Z" fill="#d4d4e0"/>
  </g>
  <g class="h">
    <circle cx="100" cy="102" r="52" fill="#2a2233"/>
    <path d="M50 96 L36 68 L56 74 L50 44 L72 60 L77 30 L92 54 L105 26 L115 54 L135 34 L134 64 L156 50 L147 78 L163 82 L150 98 Z" fill="#2a2233"/>
    <ellipse cx="100" cy="112" rx="42" ry="40" fill="#ffe3cb"/>
    <path d="M56 86 C72 76 128 76 144 86 L144 99 C128 89 72 89 56 99 Z" fill="#7a4ec4"/>
    <path d="M62 88 C78 81 122 81 138 88 L138 93 C122 86 78 86 62 93 Z" fill="#9a72d8" opacity=".85"/>
    <path d="M72 105 L92 100 M128 105 L108 100" stroke="#2a2233" stroke-width="3.6" stroke-linecap="round"/>
    <g class="gaze">
      <circle cx="83" cy="117" r="8.5" fill="#6a3ec0"/>
      <circle cx="117" cy="117" r="8.5" fill="#6a3ec0"/>
      <circle cx="80" cy="113" r="2.8" fill="#ffffff"/>
      <circle cx="114" cy="113" r="2.8" fill="#ffffff"/>
    </g>
    <path d="M87 135 C91 130 109 130 113 135 C109 141 91 141 87 135 Z" fill="#7a4ec4"/>
  </g>
</g>` },
];
