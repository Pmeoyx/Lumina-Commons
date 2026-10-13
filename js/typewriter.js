// ==================== 沉浸式 3D 复古打字机 ====================
// 点击输入框 → 下方升起一台复古打字机（暖琥珀 + 深棕，电影感）。
//   · 按键盘哪个键，打字机上对应的键帽就下沉
//   · 敲字时字模臂（打字杆）甩起撞击纸面，撞击点叠加柔和高光闪烁
//   · 拼音输入：字母进缓冲，下方候选栏给出对应中文，数字键 1-9 / 空格选词
//   · 真实机械键音（WebAudio 合成：键击、打字、空格、退格、回车铃+回车滑动）
//   · 无拼音时按 Enter → 纸张平滑向上移动一行（换行）
//
// 用法：
//   import { attachTypewriter } from './js/typewriter.js';
//   attachTypewriter(document.getElementById('f-name'), { label:'姓名', singleLine:true });
//
// 组件自带样式（注入一次），不依赖任何外部 CSS。
//
// AI 候选：本地词库有限，若已配置大模型（见 js/ai.js 的 AI_CONFIG），
// 会异步请求更日常的候选词补到候选栏最前面，并用蓝色标注区分。

import { aiPinyin } from './ai.js';

const LH = 30;              // 纸张行高(px)
const PAPER_H = 240;        // 纸张窗口高度(px)
const PAPER_PAD = 20;       // 纸张底部留白(px)
const BAR_COUNT = 17;       // 字模臂数量

// ---------------- 迷你拼音词表 ----------------
// 单音节 → 常用汉字（首位为默认首选）
const SYL = {
  a:'啊阿', ai:'爱艾哎', an:'安按案', ang:'昂', ao:'奥澳',
  ba:'把吧八爸巴', bai:'白百拜', ban:'半班板版', bang:'帮邦', bao:'包报宝抱保', bei:'被北备背杯', ben:'本奔', beng:'蹦', bi:'比笔必毕', bian:'边变便遍', biao:'表标', bie:'别', bin:'宾', bing:'并病冰兵', bo:'波博播伯', bu:'不步部补布',
  ca:'擦', cai:'才菜财彩', can:'参餐残', cang:'藏仓', cao:'草操', ce:'册侧测策', ceng:'层曾', cha:'茶查差插', chai:'拆柴', chan:'产', chang:'长常场唱厂', chao:'超朝吵', che:'车彻', chen:'陈沉晨尘', cheng:'成城程诚', chi:'吃池迟持', chong:'冲充虫', chou:'抽愁', chu:'出初除厨础', chuan:'穿传船川', chuang:'创窗床', chui:'吹垂', chun:'春纯', ci:'次词此刺', cong:'从聪葱', cu:'粗促', cun:'存村寸', cuo:'错措',
  da:'大打达答搭', dai:'带代待袋', dan:'单但担蛋淡', dang:'当党挡', dao:'到道倒岛刀', de:'的地得德', deng:'等灯登', di:'低地第弟底敌', dian:'点电店典', diao:'掉调', die:'跌叠', ding:'定顶订丁', dong:'动东冬懂洞', dou:'都斗豆抖', du:'读度独肚毒', duan:'短段断', dui:'对队堆', dun:'顿盾', duo:'多朵躲夺',
  e:'额俄饿', en:'恩', er:'而二耳儿',
  fa:'发法', fan:'反饭翻凡', fang:'方房放防', fei:'飞非费肥', fen:'分份粉奋', feng:'风封丰疯', fo:'佛', fou:'否', fu:'服夫复父富府扶幅',
  ga:'咖嘎', gai:'该改盖', gan:'干感敢甘', gang:'刚钢港', gao:'高告搞', ge:'个各歌哥格割', gei:'给', gen:'根跟', geng:'更耕', gong:'工公共功弓', gou:'够狗沟构', gu:'古故股骨鼓谷', gua:'挂瓜刮', guai:'怪拐', guan:'关观管馆冠', guang:'光广逛', gui:'贵归规鬼', gun:'滚棍', guo:'国过果锅',
  ha:'哈', hai:'还海孩害', han:'喊汉寒含', hang:'行航', hao:'好号浩豪', he:'和喝河合何', hei:'黑嘿', hen:'很狠恨', heng:'横恒', hong:'红洪轰', hou:'后候厚猴', hua:'花话化画华', huai:'坏怀', huan:'还换欢环缓', huang:'黄皇荒慌', hui:'会回灰汇慧', hun:'混婚昏', huo:'活火或货获', hu:'户湖胡虎护',
  ji:'几机记及级计济急集技即', jia:'家加价假架佳', jian:'见件间建简剑健', jiang:'讲将江降奖', jiao:'叫教脚觉交角较', jie:'接结解界姐街介', jin:'今进金近紧尽', jing:'经京精惊景静镜', jiong:'窘', jiu:'九就酒久旧救', ju:'句居局具举聚', juan:'卷捐', jue:'绝决觉', jun:'军均君',
  ka:'卡咖', kai:'开凯', kan:'看刊砍', kang:'康扛', kao:'靠考烤', ke:'可科客课刻克', ken:'肯啃', keng:'坑', kong:'空孔控', kou:'口扣', ku:'哭苦库裤', kua:'跨夸', kuai:'快块筷', kuan:'宽款', kuang:'狂矿框', kui:'亏愧', kun:'困昆', kuo:'扩阔',
  la:'拉啦辣', lai:'来赖', lan:'蓝兰懒烂栏', lang:'浪郎狼', lao:'老劳牢', le:'了乐勒', lei:'累类雷泪', leng:'冷愣', li:'里力立离李理利历丽粒', lia:'俩', lian:'连脸练恋联', liang:'两亮凉量良', liao:'聊料疗', lie:'列裂烈', lin:'林临邻', ling:'另令灵领零', liu:'流六留刘', long:'龙隆笼', lou:'楼漏', lu:'路录露陆卢', luan:'乱', lun:'论轮', luo:'落罗络',
  ma:'吗马妈麻码', mai:'买卖麦', man:'满慢蛮', mang:'忙盲', mao:'毛猫冒帽', me:'么', mei:'没每美妹眉', men:'门们闷', meng:'梦猛蒙', mi:'米密迷秘', mian:'面免棉眠', miao:'秒妙描', mie:'灭', min:'民敏', ming:'明名命鸣', mo:'摸磨末莫默', mou:'某谋', mu:'木目母幕牧',
  na:'那拿哪纳', nai:'奶耐', nan:'南男难', nao:'脑闹', ne:'呢', nei:'内', nen:'嫩', neng:'能', ni:'你尼泥妮', nian:'年念', niang:'娘', niao:'鸟尿', nie:'捏', nin:'您', ning:'宁凝', niu:'牛扭', nong:'农弄浓', nu:'努怒', nuan:'暖', nuo:'挪',
  o:'哦噢', ou:'欧偶',
  pa:'怕爬趴', pai:'拍排牌派', pan:'盘判盼', pang:'旁胖', pao:'跑泡炮', pei:'陪配赔', pen:'盆喷', peng:'朋碰棚', pi:'皮批疲匹', pian:'片偏篇骗', piao:'票飘漂', pin:'品拼贫', ping:'平评苹瓶', po:'破坡婆迫', pu:'普铺扑朴',
  qi:'起其气七期奇齐器汽', qia:'恰', qian:'前钱千签浅', qiang:'强墙抢', qiao:'桥巧敲', qie:'切且', qin:'亲琴勤', qing:'请清青轻情晴', qiong:'穷', qiu:'球求秋', qu:'去取区曲趣', quan:'全权圈劝', que:'却缺确', qun:'群',
  ran:'然染燃', rang:'让', rao:'绕扰', re:'热', ren:'人认任忍仁', reng:'扔', ri:'日', rong:'容荣融', rou:'肉柔', ru:'如入乳', ruan:'软', rui:'锐瑞', run:'润', ruo:'若弱',
  sa:'撒洒', sai:'赛塞', san:'三散', sang:'桑嗓', sao:'扫骚', se:'色涩', sen:'森', sha:'杀沙啥傻', shai:'晒', shan:'山善闪衫', shang:'上商伤赏', shao:'少烧绍', she:'社设舍蛇', shei:'谁', shen:'身深神审甚', sheng:'生声升胜省', shi:'是时事实十市师识试食石世史', shou:'手收受首瘦', shu:'书数树束输属熟舒', shua:'刷耍', shuai:'帅摔', shuang:'双爽', shui:'水睡谁税', shun:'顺', shuo:'说硕',
  si:'四思司死私丝', song:'送松宋颂', sou:'搜', su:'素速苏诉', suan:'酸算', sui:'岁随碎虽', sun:'孙损', suo:'所索锁缩',
  ta:'他她它塔踏', tai:'太台态抬', tan:'谈弹探摊坦', tang:'糖堂躺汤', tao:'逃套掏桃讨', te:'特', teng:'疼腾', ti:'题体提踢替', tian:'天田甜添', tiao:'条跳挑', tie:'铁贴', ting:'听停厅挺', tong:'同通痛统童', tou:'头投透', tu:'图土突兔徒', tuan:'团', tui:'推退腿', tun:'吞', tuo:'脱托拖',
  wa:'挖娃袜', wai:'外歪', wan:'完晚万弯玩', wang:'王忘往网望', wei:'为位未围伟味微威', wen:'文问闻稳温', weng:'翁', wo:'我握卧', wu:'无五物务午舞屋武雾误',
  xi:'西系洗喜细习息席吸', xia:'下夏吓虾', xian:'先现线县显限险鲜', xiang:'想向相像香乡响', xiao:'小笑校消效肖', xie:'写些谢血鞋协', xin:'新心信辛', xing:'行性姓星形兴型', xiong:'兄胸熊', xiu:'修休秀', xu:'需许须续虚', xuan:'选宣悬', xue:'学雪血', xun:'寻讯迅训',
  ya:'呀压牙亚鸦', yan:'眼言演验严研烟盐沿颜', yang:'样阳养洋扬羊', yao:'要药摇咬腰', ye:'也业夜叶野页', yi:'一以已意义议衣医易亿艺', yin:'因音银引印阴', ying:'应英影营硬迎赢', yo:'哟', yong:'用永勇拥', you:'有又右由友优游油邮', yu:'与于语雨鱼育遇预余玉', yuan:'元原员园圆远院愿', yue:'月越约阅', yun:'云运允',
  za:'咋杂', zai:'在再载灾', zan:'咱暂赞', zang:'脏', zao:'早造遭澡', ze:'则责', zei:'贼', zen:'怎', zeng:'增曾', zha:'炸扎眨', zhai:'摘宅窄', zhan:'站占战展粘', zhang:'张章长掌涨', zhao:'找照招着', zhe:'这着者折', zhen:'真针阵震珍镇', zheng:'正整争政证睁', zhi:'之只知直制指志质纸支治值职致', zhong:'中种重众钟终', zhou:'周州粥轴', zhu:'主住注助祝竹猪逐', zhua:'抓', zhuan:'转专赚', zhuang:'装状庄撞', zhui:'追', zhun:'准', zhuo:'桌捉',
  zi:'子自字资紫姿', zong:'总宗综', zou:'走奏', zu:'组足族租阻', zuan:'钻', zui:'最嘴醉', zun:'尊', zuo:'做作坐左座昨',
};

// 音节候选字补充表：原表每个音节只有 3~4 个字，经常选不到正确的字。
// 这里按常用度补厚（追加在末尾，不改变原来的首选字，所以默认候选不变）。
// 重复字会在下面被过滤掉。
const SYL_EXTRA = {
  ai:'哀矮碍唉蔼', an:'暗岸俺鞍', ao:'傲熬袄',
  ba:'罢芭疤拔把', bai:'摆败柏', ban:'搬伴扮斑拌颁', bang:'棒榜磅', bao:'薄爆饱堡鲍',
  bei:'悲贝碑辈惫', bi:'闭壁避鼻彼碧蔽弊', bian:'编辩辨鞭', biao:'镖彪', bing:'饼柄丙秉',
  bo:'拨剥玻脖驳', bu:'捕簿卜怖哺',
  cai:'裁猜踩材', can:'惨灿', cao:'槽曹燥糙', ceng:'蹭',
  cha:'叉岔刹', chan:'缠禅铲蝉', chang:'尝偿肠畅', chao:'炒潮嘲巢', che:'撤澈', chen:'趁衬辰',
  cheng:'呈承惩橙撑秤', chi:'翅尺斥耻驰', chong:'崇宠', chou:'丑筹酬稠', chu:'楚储触畜雏',
  chuan:'串喘', chuang:'闯疮', chui:'锤炊', chun:'唇蠢醇', ci:'慈磁雌瓷辞',
  cong:'丛匆', cu:'醋簇', cuo:'搓挫',
  da:'搭瘩', dai:'呆贷怠', dan:'胆旦弹', dang:'档荡', dao:'盗稻悼导', deng:'凳瞪蹬',
  di:'滴抵帝缔迪', dian:'垫殿甸', diao:'雕叼吊', die:'蝶谍', ding:'钉鼎锭', dong:'冻栋董',
  dou:'逗兜陡', du:'赌堵镀杜', duan:'锻缎', dun:'吨蹲炖', duo:'舵堕',
  e:'娥鹅蛾恶', er:'尔饵贰',
  fa:'罚伐阀筏', fan:'繁返贩帆', fang:'纺仿妨', fei:'废菲匪沸', fen:'氛坟芬焚',
  feng:'峰锋蜂缝', fu:'副符幅辐拂抚俯斧腐赴',
  gan:'杆肝赶竿赣', gang:'纲缸杠', gao:'糕稿膏羔', ge:'隔革阁葛鸽', gong:'攻贡恭躬',
  gou:'钩购勾苟', gu:'顾雇孤姑辜', guan:'惯灌罐', gui:'柜桂跪轨硅', guo:'裹郭',
  han:'函韩旱焊悍', hao:'耗嚎壕', he:'赫盒荷鹤', hong:'宏烘虹鸿弘',
  hou:'吼喉', hu:'互呼忽蝴糊壶葫沪', hua:'划桦', huan:'患幻唤焕', huang:'煌凰幌',
  hui:'惠辉毁晦', hun:'魂浑', huo:'祸惑霍',
  ji:'吉积鸡基激绩籍寂挤祭辑疾嫉', jia:'甲夹嘉稼嫁', jian:'肩艰监兼减检荐箭溅',
  jiang:'浆酱僵疆', jiao:'焦骄浇娇胶缴', jie:'阶截揭洁戒届借杰', jin:'劲禁锦仅谨晋',
  jing:'警竟净竞境敬睛', jiu:'究纠揪玖', ju:'巨拒剧俱惧矩距锯', jue:'掘诀爵', jun:'俊竣骏菌',
  kai:'慨楷', kan:'坎勘', kang:'抗炕', ke:'壳渴颗柯苛', ken:'垦恳', kong:'恐',
  ku:'酷枯窟', kuan:'款', kuang:'旷况', kui:'窥溃葵', kun:'捆', kuo:'括廓',
  la:'蜡喇腊', lan:'篮览缆滥', lang:'廊朗', lao:'捞姥唠',
  lei:'垒擂', li:'粒丽犁璃鲤', lian:'链廉镰帘', liang:'谅辆梁粮', liao:'辽撩',
  lin:'淋霖鳞', ling:'龄铃陵', liu:'榴柳瘤', long:'聋垄', lou:'搂篓', lu:'炉卤麓',
  lv:'旅律率绿滤驴', lun:'仑伦沦', luo:'锣骆萝螺',
  ma:'嘛蚂玛', mai:'迈脉', man:'漫蔓馒瞒', mao:'茂茅贸', mei:'玫煤霉',
  meng:'盟朦', mi:'蜜谜眯觅', mian:'绵冕缅', miao:'瞄庙苗', ming:'铭冥',
  mo:'膜墨沫寞漠', mu:'拇募墓穆慕',
  na:'娜呐捺', nan:'楠腩', nao:'挠恼', ni:'拟逆腻匿', nian:'粘碾',
  ning:'拧柠', niu:'纽钮', nu:'奴', nuo:'诺糯',
  ou:'殴藕呕', pa:'帕琶', pai:'徘', pan:'磐叛', pang:'螃庞', pao:'袍刨', pei:'沛培',
  peng:'鹏蓬彭', pi:'劈疲脾譬', pian:'篇骗', piao:'瓢', pin:'贫频聘', ping:'屏坪萍',
  po:'颇泼魄', pu:'葡蒲瀑谱',
  qi:'旗启弃契棋歧祈', qia:'掐', qian:'嵌谦遣钳', qiang:'腔蔷', qiao:'悄瞧樵',
  qie:'茄怯窃', qin:'禽寝芹', qing:'卿倾顷', qiu:'丘囚裘', qu:'娶驱趋渠',
  quan:'拳犬券', que:'雀鹊', qun:'裙',
  ran:'冉', rang:'壤嚷', re:'惹', ren:'刃韧饪', ri:'',
  rong:'绒蓉熔', rou:'揉', ru:'辱儒褥', ruan:'阮', rui:'蕊', ruo:'箬',
  san:'伞叁', sang:'丧', sao:'嫂搔', se:'瑟', sha:'砂纱刹鲨', shai:'筛',
  shan:'杉姗珊扇擅', shang:'晌', shao:'勺芍哨', she:'涉摄赦', shen:'申绅呻婶',
  sheng:'绳甥', shi:'侍逝誓柿嗜', shou:'兽寿授', shu:'薯薯署曙鼠黍', shuai:'衰',
  shuang:'霜', shui:'',
  si:'撕嘶肆寺伺饲', song:'诵讼', su:'塑粟诉', suan:'蒜',
  sui:'髓隧穗', sun:'笋', suo:'琐梭唆',
  ta:'塌榻獭', tai:'苔胎汰', tan:'坛毯瘫炭潭', tang:'唐塘搪膛', tao:'陶淘滔萄',
  te:'', teng:'藤', ti:'堤蹄剃啼', tian:'填佃佃', tiao:'笤', tie:'帖',
  ting:'亭艇廷', tong:'桶筒瞳彤', tou:'偷', tu:'涂屠吐凸', tui:'褪',
  tuo:'驼驼椭拓',
  wa:'洼蛙娃', wai:'', wan:'丸腕豌', wang:'汪枉妄', wei:'违唯维萎帷巍薇',
  wen:'吻纹蚊紊', wo:'窝蜗沃', wu:'吾捂梧钨侮',
  xi:'溪熄膝牺昔熙稀希析溪', xia:'瞎峡霞侠', xian:'闲贤咸嫌掀弦衔',
  xiang:'翔厢镶橡', xiao:'萧宵霄潇嚣', xie:'斜谐携卸屑蟹泄',
  xin:'欣薪锌馨', xing:'醒腥杏幸', xiong:'匈汹', xiu:'羞锈绣嗅',
  xu:'叙旭蓄绪墟', xuan:'喧炫靴', xue:'穴靴', xun:'巡循旬熏薰',
  ya:'押崖涯雅讶', yan:'岩炎焰宴燕雁淹腌艳', yang:'杨央漾秧', yao:'遥谣窑耀瑶',
  ye:'冶椰曳', yi:'依仪遗亦益盈忆翼怡毅抑疫',
  yin:'殷饮隐姻阴', ying:'鹰婴缨莹荧盈', yong:'涌踊咏', you:'悠幽忧尤犹柚',
  yu:'宇羽欲浴裕迂愉渔愚逾', yuan:'援缘猿源渊', yue:'悦岳跃钥',
  yun:'匀孕韵蕴', za:'砸咋', zai:'栽宰崽', zan:'攒贊', zang:'葬赃',
  zao:'遭噪燥皂', ze:'泽择', zeng:'赠憎', zha:'渣札闸诈', zhai:'债摘斋',
  zhan:'沾崭盏詹', zhang:'帐账胀杖樟', zhao:'沼召兆沼昭', zhe:'浙蔗辄',
  zhen:'诊枕疹贞桢斟', zheng:'症挣筝蒸怔', zhi:'枝植执旨掷滞稚帜炙蛛植',
  zhong:'忠衷肿衷', zhou:'舟昼皱骤', zhu:'筑烛筑逐驻柱煮蛛', zhuan:'砖撰', zhuang:'妆桩',
  zhui:'坠缀', zhuo:'卓琢酌', zi:'滋仔籽姊姿', zong:'棕踪鬃', zou:'邹',
  zu:'诅', zui:'罪', zuo:'凿琢',
};
for (const k in SYL_EXTRA) {
  const cur = SYL[k] || '';
  SYL[k] = cur + SYL_EXTRA[k].split('').filter(c => c && cur.indexOf(c) < 0).join('');
}

// 常用词（整词优先命中）
const WORDS = {
  // —— 社区 / 搭子场景 ——
  lanqiu:'篮球', zuqiu:'足球', paiqiu:'网球', maqiu:'马球', yuqiu:'羽球', jita:'吉他', gangqin:'钢琴',
  yinyue:'音乐', xuexi:'学习', yingyu:'英语', shuxue:'数学', biancheng:'编程', daima:'代码', kaoyan:'考研',
  tushuguan:'图书馆', xiawu:'下午', shangwu:'上午', wanshang:'晚上', zaoshang:'早上', zhoumo:'周末',
  gongzuori:'工作日', mingtian:'明天', jintian:'今天', zuotian:'昨天', yiqi:'一起', dazi:'搭子',
  pengyou:'朋友', tongxue:'同学', jiaolian:'教练', jiaoxue:'教学', yueju:'约局', kaihei:'开黑', youxi:'游戏',
  dianjing:'电竞', zhuoyou:'桌游', meishi:'美食', tandian:'探店', naicha:'奶茶', kafei:'咖啡', hongbei:'烘焙',
  zuofan:'做饭', zuocai:'做菜', chongwu:'宠物', jumao:'橘猫', liugou:'遛狗', jiyang:'寄养', zhiyuan:'志愿',
  jijiu:'急救', zhijiao:'支教', jinglao:'敬老', dasao:'打扫', shouna:'收纳', huishou:'回收', qingjie:'清洁',
  hanjie:'焊接', mugong:'木工', shouzuo:'手作', huihua:'绘画', huahua:'画画', sheying:'摄影', sheji:'设计',
  jianmo:'建模', paobu:'跑步', yepao:'夜跑', jianshen:'健身', yumaoqiu:'羽毛球', youyong:'游泳', yujia:'瑜伽',
  qixing:'骑行', pashan:'爬山', huoguo:'火锅', dianying:'电影', juben:'剧本', changge:'唱歌', wudao:'舞蹈',
  shufa:'书法', yuedu:'阅读', dushu:'读书', beikao:'备考', fuxi:'复习', biji:'笔记', dayi:'答疑', fudao:'辅导',
  siliuji:'四六级', shijian:'时间', didian:'地点', renshu:'人数', yaoqiu:'要求', mianfei:'免费', shoufei:'收费',
  xianshang:'线上', xianxia:'线下', zudui:'组队', qiudai:'求带', peilian:'陪练', xinshou:'新手',
  lingjichu:'零基础', jinjie:'进阶', nansheng:'男生', nvsheng:'女生', qingwen:'请问', xiangxue:'想学',
  huanying:'欢迎', lianxi:'联系', fangshi:'方式', weixin:'微信', shoujihao:'手机号', zhaopin:'招聘',
  jianzhi:'兼职', shixi:'实习', tigao:'提高', bangmang:'帮忙', xiexie:'谢谢', zaijian:'再见', youkong:'有空',
  keyi:'可以', buneng:'不能', huanyingnin:'欢迎您',
  // —— 高频虚词 / 常用词 ——
  zhidao:'知道', juede:'觉得', shenme:'什么', zenme:'怎么', weishenme:'为什么', yinwei:'因为', suoyi:'所以',
  danshi:'但是', ruguo:'如果', xianzai:'现在', yijing:'已经', dajia:'大家', women:'我们', nimen:'你们',
  tamen:'他们', ziji:'自己', shihou:'时候', difang:'地方', dongxi:'东西', shiqing:'事情', wenti:'问题',
  haode:'好的', meiguanxi:'没关系', duibuqi:'对不起', buhaoyisi:'不好意思', zaoshang:'早上',
  // —— 超高频口语 / 社交（原来缺很多，导致"很难打对"） ——
  nihao:'你好', ninhao:'您好', zaijianba:'再见吧', xiexieni:'谢谢你', bukeqi:'不客气',
  haojiu:'好久', haojiubujian:'好久不见', zaoshanghao:'早上好', wanshanghao:'晚上好',
  chifan:'吃饭', chifanle:'吃饭了', shuijiao:'睡觉', qichuang:'起床', shangke:'上课',
  xiake:'下课', fangxue:'放学', huijia:'回家', chumen:'出门', shangban:'上班', xiaban:'下班',
  jiaban:'加班', kaoshi:'考试', chengji:'成绩', zuoye:'作业', ketang:'课堂', jiaoshi:'教室',
  sushe:'宿舍', shitang:'食堂', caochang:'操场', tushu:'图书', jiaoxuelou:'教学楼',
  tongxue:'同学', shixiong:'师兄', shijie:'师姐', xuezhang:'学长', xuejie:'学姐',
  laoshi:'老师', daoshi:'导师', banji:'班级', zhuanye:'专业', xueyuan:'学院',
  qingjiao:'请教', qingwen:'请问', mafan:'麻烦', xinku:'辛苦', gongxi:'恭喜', zhufu:'祝福',
  shengri:'生日', kuaile:'快乐', xinnian:'新年', kaixin:'开心', nanguo:'难过', shengqi:'生气',
  jinzhang:'紧张', fangxin:'放心', zhuyi:'注意', xiaoxin:'小心', anquan:'安全', jiankang:'健康',
  yisheng:'医生', yiyuan:'医院', ganmao:'感冒', fashao:'发烧', chiyao:'吃药', xiuxi:'休息',
  yundong:'运动', duanlian:'锻炼', renshen:'热身', shenzhan:'伸展', huxi:'呼吸', quanli:'全力',
  bisai:'比赛', jiaolian:'教练', duiyuan:'队员', xunlian:'训练',   shijian:'时间', riqi:'日期', xingqi:'星期', libai:'礼拜', yuefen:'月份', jijie:'季节',
  chuntian:'春天', xiatian:'夏天', qiutian:'秋天', dongtian:'冬天',
  gongyu:'公寓', dianti:'电梯', loudao:'楼道', tingche:'停车', dache:'打车', ditie:'地铁',
  bus:'公交', gaotie:'高铁', jichang:'机场', chezhan:'车站', ditu:'地图', daohang:'导航',
  waichu:'外出', lvxing:'旅行', paizhao:'拍照', heying:'合影', zhaopian:'照片', shipin:'视频',
  luyin:'录音', zhibo:'直播', huatong:'话筒', yinxiang:'音箱', dengguang:'灯光', wutai:'舞台',
  biaoyan:'表演', yanchu:'演出', caipai:'彩排', jiemu:'节目', zhuchiren:'主持人',
  xiangmu:'项目', renwu:'任务', jihua:'计划', mubiao:'目标', jinbu:'进步',
  nuli:'努力', jianchi:'坚持', tiaozhan:'挑战', tuandui:'团队',
  hezuo:'合作', fenxiang:'分享', goutong:'沟通', taolun:'讨论', huiyi:'会议', zongjie:'总结',
  guanli:'管理', zuzhi:'组织', anpai:'安排', canyu:'参与', baoming:'报名', canjia:'参加',
  fengxian:'风险', jingyan:'经验', nengli:'能力', shuiping:'水平', shili:'实力', jingzheng:'竞争',
  peixun:'培训', kecheng:'课程', jiaocai:'教材', shuji:'书籍', ziliao:'资料', lunwen:'论文',
  shiyan:'实验', shuju:'数据', fenxi:'分析', jielun:'结论', fangfa:'方法', silu:'思路',
  wenti:'问题', daan:'答案', cuowu:'错误', zhengque:'正确', jieguo:'结果', yuanyin:'原因',
  zhuangtai:'状态', jindu:'进度', xiaoguo:'效果', biaoxian:'表现', chengjiu:'成就',
  // —— 搭子帖场景超高频短句（用户反馈"选项太少、常用词偏差大"后补厚） ——
  youmeiyou:'有没有', youren:'有人', youmeiyouren:'有没有人', shuiyoukong:'谁有空',
  youkongma:'有空吗', xiangzhao:'想找', xiangyao:'想要', xiangqu:'想去', xiangwan:'想玩',
  yiqiwan:'一起玩', yiqiqu:'一起去', yiqixue:'一起学', yiqilian:'一起练', yiqiquan:'一起逛',
  qiuzudui:'求组队', qiudaizi:'求带子', qiudaishang:'求带上', qiuren:'求人', qiuyou:'求友',
  zhaoxiaohuo:'找小伙', zhaoren:'找人', zhaodazi:'找搭子', zhaopengyou:'找朋友',
  zhaotongban:'找同伴', zhaodian:'找店', zhaoweixin:'找微信',
  youmeiyourenxiang:'有没有人想', youmeiyourenkeyi:'有没有人可以',
  youmeiyourenyao:'有没有人要', youmeiyourenhui:'有没有人会',
  youmeiyourena:'有没有人啊', zhoumoyoukong:'周末有空',
  yiyanjiading:'一言家丁', yiqiyueju:'一起约局', yiqikaihei:'一起开黑', yiqihongbei:'一起烘焙',
  yiqizuofan:'一起做饭', yiqichifan:'一起吃饭', yiqitanguang:'一起逛逛', yiqipaizhao:'一起拍照',
  yundongyueju:'运动约局', yundongzu:'运动族', yundongchang:'运动场', yundongyuan:'运动员',
  yundongxie:'运动鞋', yundongku:'运动裤', yundongfu:'运动服',
  pengyouyue:'朋友约', pengyouquan:'朋友圈', pengyoujubu:'朋友聚会',
  jiyangchongwu:'寄养宠物', chongwuyiyuan:'宠物医院', chongwudian:'宠物店', chongwuzhu:'宠物主',
  chongwumeishi:'宠物美食', chongwumeirong:'宠物美容', chongwuyongchi:'宠物泳池',
  yingyujiao:'英语角', yingyukouyu:'英语口语', yingyutingli:'英语听力', yingyuyuedu:'英语阅读',
  yingyuxiezuo:'英语写作', yingyufanyi:'英语翻译', yingyudanci:'英语单词',
  kaoyanyingyu:'考研英语', kaoyanzhengzhi:'考研政治', kaoyanshuxue:'考研数学',
  kaoyanzhuanye:'考研专业', kaoyanchongci:'考研冲刺', kaoyanfuxi:'考研复习',
  bianchengjiaocheng:'编程教程', bianchengyuyan:'编程语言', bianchengpeixun:'编程培训',
  bianchengbisai:'编程比赛', bianchengxiangmu:'编程项目', daimashencha:'代码审查',
  daimaguihua:'代码规范', daimazhushi:'代码注释', daimatijiao:'代码提交',
  bisaisai:'比赛赛', bisaisaicheng:'比赛赛程', bisaisairi:'比赛日', bisaisaizhu:'比赛主',
  bisaiduixing:'比赛队形', bisaimingdan:'比赛名单',
  xinshourumen:'新手入门', xinshoujiaocheng:'新手教程', xinshouzhiyin:'新手指引',
  lingjichurumen:'零基础入门', lingjichujiaocheng:'零基础教程', lingjichixue:'零基础学',
  jiaochengdingji:'教程定级', jiaochengxiangjie:'教程详解',
  paiqiubisai:'排球比赛', paiqiushudui:'排球双队', paiqiudanming:'排球单名',
  paiqiujingji:'排球竞技', paiqiujiao:'排球教', paiqiujiaoxue:'排球教学',
  paiqiuzhuangbei:'排球装备', paiqiuchangdi:'排球场地', paiqiujianshen:'排球健身',
  yumaoqiubisai:'羽毛球比赛', yumaoqiushuang:'羽毛球双', yumaoqiudan:'羽毛球单',
  yumaoqiujiao:'羽毛球教', yumaoqiuxunlian:'羽毛球训练', yumaoqiuchang:'羽毛球厂',
  yumaoqiuchangdi:'羽毛球场地', yumaoqiuzhuangbei:'羽毛球装备',
  lanqiubisai:'篮球比赛', lanqiuban:'篮球半', lanqiuchang:'篮球场', lanqiuxie:'篮球鞋',
  lanqiuku:'篮球裤', lanqiuyundong:'篮球运动', lanqiujiaoxue:'篮球教学',
  lanqiuxunlian:'篮球训练', lanqiucuo:'篮球错', lanqiuzu:'篮球组',
  jitajiaoxue:'吉他教学', jitaxunlian:'吉他训练', jitaxue:'吉他学', jitajianzi:'吉他谱子',
  jitajiao:'吉他教', jitajiarizi:'吉他日子', gitaer:"吉他儿",
  gangqinjiaoxue:'钢琴教学', gangqinyanZou:'钢琴演奏', gangqinboxue:'钢琴谱学',
  huaban:'滑板', huabanshen:'滑板神', huabanjiaoxue:'滑板教学', huabancuo:'滑板错',
  youyongjiaoxue:'游泳教学', youyongxunlian:'游泳训练', youyongchi:'游泳池',
  youyongyongchi:'游泳泳池', youyongzhuangbei:'游泳装备',
  paochang:'操场', paochuyouxi:'跑步游戏', paobuxunlian:'跑步训练', paobuzhuangbei:'跑步装备',
  jianshenfang:'健身房', jianshenjiao:'健身教', jianshenxunlian:'健身训练',
  jianshenfangshi:'健身方式', jianshenjihua:'健身计划', jianshenyundong:'健身运动',
  yujiajiaoxue:'瑜伽教学', yujiaxunlian:'瑜伽训练', yujiashi:'瑜伽室', yujiayongju:'瑜伽用具',
  bianchengruanjian:'编程软件', ruanjinkaifa:'软件开发', ruanjianjiaocheng:'软件教程',
  ruanjianpeixun:'软件培训', ruanjiansheji:'软件设计', ruanjianxingneng:'软件性能',
  // —— 日常超高频补充（用户反馈"偏差大"后补） ——
  jintianyoukong:'今天有空', mingtianyoukong:'明天有空', zuotianyoukong:'昨天有空',
  zhoumoyoukong:'周末有空', xiawuyoukong:'下午有空', wanshangyoukong:'晚上有空',
  zaoshangyoukong:'早上有空', zhongwuyoukong:'中午有空',
  wokeyi:'我可以', woxiang:'我想', wojiao:'我叫', woxihuan:'我喜欢',
  wotaishan:'我擅长', wohui:'我会', woneng:'我能', woanpai:'我安排',
  wodepengyou:'我的朋友', womendou:'我们都', womenlia:'我们俩', womenyiqi:'我们一起',
  keyima:'可以吗', xingma:'行吗', keyiyoukong:'可以有空',
  yikuai:'一块', yikuaiqu:'一块去', yikuaiwan:'一块玩', yikuailian:'一块练',
  youxingqu:'有兴趣', ganxingqu:'感兴趣', youyisi:'有意思', youyiyong:'有一用',
  xingbuxing:'行不行', keyibuneng:'可以不能', xingma:'行吗',
  youmeiyouyiqi:'有没有一起', youmeiyourenqu:'有没有人去', youmeiyourenyaoqu:'有没有人要去',
  // —— 教学/求助场景补充 ——
  qiuweijiao:'求外教', qiudu:'求读', qiujiang:'求讲', qiutong:'求同', qiuzu:'求组',
  qiubisai:'求比赛', qiudianzi:'求电子', qiufuzhu:'求辅助', qiutigong:'求提供',
  jiajiao:'家教', jiajiaolaoshi:'家教老师', jiajiaofudao:'家教辅导',
  // —— 时间地点高频补充 ——
  zhoumoshagnwu:'周末上午', zhoumoxiawu:'周末下午', zhoumowanshang:'周末晚上',
  gongzuorishangwu:'工作日上午', gongzuorixiawu:'工作日下午', gongzuoriwanshang:'工作日晚上',
  shangwuyoukong:'上午有空', xiawuyoukong:'下午有空', wanshangyoukong:'晚上有空',
  jintianxiawu:'今天下午', mingtianxiawu:'明天下午', zuotianxiawu:'昨天下午',
  zhoumosh:'周末上', zhoumozhongwu:'周末中午', zhoumowancan:'周末晚餐',
  zhoumozaocan:'周末早餐', zhoumowancan:'周末晚餐',
  // —— 约局/活动高频补充 ——
  yueju:'约局', yueqiu:'约球', yuepao:'约跑', yueying:'约影', yuefan:'约饭',
  yuepa:'约拍', yuechang:'约唱', yuekao:'约考', yuejiao:'约教', yuelian:'约练',
  bisaiyueju:'比赛约局', yundongyueju:'运动约局', youxiyueju:'游戏约局',
  // —— 零基础/入门补充 ——
  lingjichu:'零基础', rumen:'入门', xueshu:'学手', xuesheng:'学生', xuexiao:'学校',
  xuexizhe:'学习者', xuexijihua:'学习计划', xuexifangfa:'学习方法',
  xuexijindu:'学习进度', xuexixiaoguo:'学习效果', xuexichengduo:'学习成果',
  // —— 城市/社区高频 ——
  chengshi:'城市', shequ:'社区', shequhuodong:'社区活动', shequfuwu:'社区服务',
  shequjiaoliu:'社区交流', shequcanyu:'社区参与', shequzuzhi:'社区组织',
  shequguanli:'社区管理', shequgonggao:'社区公告', shequxinxi:'社区信息',
  shequtongzhi:'社区通知', shequdongtai:'社区动态', shequchengyuan:'社区成员',
  shequpengyou:'社区朋友', shequhuodong:'社区活动', shequxuexi:'社区学习',
  // —— 搭子帖常用尾句 ——
  yiqilai:'一起来', yiqiqu:'一起去', yiqiwan:'一起玩', yiqixue:'一起学',
  kuailai:'快来', kuailaiba:'快来吧', kuailaicuba:'快来吧',
  yiqicanyu:'一起参与', yiqibaoming:'一起报名', yiqijiaru:'一起加入',
  yiqizuodui:'一起组队', yiqizuuzhi:'一起组织', yiqicexiao:'一起撤销',
  yiqicongshi:'一起从事', yiqitaolun:'一起讨论', yiqifenxiang:'一起分享',
};
for (const k of Object.keys(WORDS)) {
  if (!/^[a-z]+$/.test(k)) { const v = WORDS[k]; delete WORDS[k]; const kk = k.replace(/[^a-z]/g, ''); if (kk) WORDS[kk] = v; }
}

// 音节切分（最多 maxSeg 种切法）
function segment(buf, maxSeg) {
  const res = [];
  const rec = (i, cur) => {
    if (res.length >= maxSeg) return;
    if (i === buf.length) { res.push(cur.slice()); return; }
    for (let len = Math.min(6, buf.length - i); len >= 1; len--) {
      const s = buf.substr(i, len);
      if (SYL[s]) { cur.push(s); rec(i + len, cur); cur.pop(); if (res.length >= maxSeg) return; }
    }
  };
  rec(0, []);
  return res;
}

// 贪心分词：先把最长的「词」切出来，其次最长的「音节」，都不行就单字母原样。
// 这是解决"很难出现正确的"的关键 —— 老实现只取每个音节的首字组合，
// 例如 xiangxuejita 只会给出「想学几X」，永远到不了「想学吉他」。
function tokensOf(buf) {
  const toks = []; let i = 0;
  while (i < buf.length) {
    const rest = buf.length - i;
    let tok = null;
    for (let len = Math.min(8, rest); len >= 2; len--) {       // 最长词优先
      const s = buf.substr(i, len);
      if (WORDS[s]) { tok = { kind: 'w', alts: String(WORDS[s]).split('|'), len }; break; }
    }
    if (!tok) {
      for (let len = Math.min(6, rest); len >= 1; len--) {     // 再退到音节
        const s = buf.substr(i, len);
        if (SYL[s]) { tok = { kind: 's', alts: SYL[s].split(''), len }; break; }
      }
    }
    if (!tok) { tok = { kind: 'x', alts: [buf[i]], len: 1 }; }  // 认不出 → 原样保留
    toks.push(tok); i += tok.len;
  }
  return toks;
}

// 内部候选总量：3 页 × 9
export const CAND_PER_PAGE = 9;
export const CAND_PAGES = 3;
const CAND_CAP = CAND_PER_PAGE * CAND_PAGES;

// 拼音缓冲 → 候选中文
export function pinyinCandidates(bufRaw) {
  const buf = String(bufRaw || '').toLowerCase().replace(/[^a-z]/g, '');
  const out = [];
  const push = s => { if (s && out.indexOf(s) < 0) out.push(s); };
  if (!buf) return out;

  // ① 整串就是一个词
  if (WORDS[buf]) String(WORDS[buf]).split('|').forEach(push);

  // ② 主路径：把缓冲切成「单元序列」，再把末尾单元的候选字全组合。
  //    同时喂多种切分方案 —— 词+音节混合（保词）排在前面，纯音节切分跟在后面。
  //    这样 nihao / xiangxuejita 这种既能拿到整词，也能拿到"逐字改"的挑选空间。
  const lists = [tokensOf(buf)];
  const sigs = new Set([lists[0].map(t => t.len).join(',')]);
  for (const seg of segment(buf, 8)) {
    const sig = seg.join(',');
    if (sigs.has(sig)) continue;
    sigs.add(sig);
    lists.push(seg.map(s => ({ kind: 's', alts: (SYL[s] || '').split('') })));
  }

  for (const units of lists) {
    if (!units.length || units.some(u => !u.alts.length)) continue;
    const base = units.map(u => u.alts[0]);
    push(base.join(''));
    const n = units.length;
    // 单音节时把所有候选字都放出来（原来只取前 10 个，常常选不到要的字）
    const lastAlts = units[n - 1].alts.slice(0, n === 1 ? CAND_CAP : 10);
    for (const b of lastAlts) {
      const arr = base.slice(); arr[n - 1] = b;
      push(arr.join(''));
      if (out.length >= CAND_CAP) break;
    }
    if (out.length >= CAND_CAP) break;
    if (n >= 2) {
      const prevAlts = units[n - 2].alts.slice(0, 6);
      for (const a of prevAlts) {
        for (const b of lastAlts) {
          const arr = base.slice(); arr[n - 2] = a; arr[n - 1] = b;
          push(arr.join(''));
          if (out.length >= CAND_CAP) break;
        }
        if (out.length >= CAND_CAP) break;
      }
    }
    if (out.length >= CAND_CAP) break;
  }

  // ③ 整词前缀 + 剩余（例：xiangxue + ta 这种前段成词的情况）
  for (let len = Math.min(buf.length - 1, 12); len >= 2; len--) {
    const head = buf.slice(0, len);
    if (!WORDS[head]) continue;
    const rc = pinyinCandidates(buf.slice(len));
    for (let i = 0; i < Math.min(3, rc.length); i++) push(String(WORDS[head]).split('|')[0] + rc[i]);
  }

  if (!out.length) push(buf);           // 兜底：原样输出
  return out.slice(0, CAND_CAP);
}

// ---------------- 音效（WebAudio 合成，无外部资源） ----------------
let AC = null;
function ac() {
  if (!AC) {
    try { AC = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { AC = null; }
  }
  if (AC && AC.state === 'suspended') AC.resume();
  return AC;
}
function noiseSource(a, dur) {
  const n = Math.max(1, (a.sampleRate * dur) | 0);
  const b = a.createBuffer(1, n, a.sampleRate);
  const d = b.getChannelData(0);
  for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / n);
  const s = a.createBufferSource(); s.buffer = b; return s;
}
function click(a, t, freq, gain, dur, q) {
  const s = noiseSource(a, dur);
  const f = a.createBiquadFilter(); f.type = 'bandpass'; f.frequency.value = freq; f.Q.value = q || 1.1;
  const g = a.createGain();
  g.gain.setValueAtTime(gain, t); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  s.connect(f); f.connect(g); g.connect(a.destination);
  s.start(t); s.stop(t + dur + 0.02);
}
function tone(a, t, freq, gain, dur, type) {
  const o = a.createOscillator(); o.type = type || 'sine'; o.frequency.value = freq;
  const g = a.createGain();
  g.gain.setValueAtTime(0.0001, t);
  g.gain.linearRampToValueAtTime(gain, t + 0.005);
  g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  o.connect(g); g.connect(a.destination);
  o.start(t); o.stop(t + dur + 0.03);
}
function sweep(a, t, f0, f1, gain, dur) {
  const s = noiseSource(a, dur);
  const f = a.createBiquadFilter(); f.type = 'bandpass'; f.Q.value = 2.4;
  f.frequency.setValueAtTime(f0, t); f.frequency.exponentialRampToValueAtTime(f1, t + dur);
  const g = a.createGain();
  g.gain.setValueAtTime(gain, t); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  s.connect(f); f.connect(g); g.connect(a.destination);
  s.start(t); s.stop(t + dur + 0.02);
}
const SFX = {
  press(a, t) { click(a, t, 2500, 0.05, 0.03, 1.4); tone(a, t, 170, 0.03, 0.035, 'square'); },
  strike(a, t) { click(a, t, 1150, 0.11, 0.055, 1.0); click(a, t + 0.004, 3900, 0.05, 0.02, 1.6); tone(a, t, 95, 0.05, 0.06, 'triangle'); },
  space(a, t) { click(a, t, 820, 0.12, 0.075, 0.9); tone(a, t, 68, 0.05, 0.06, 'sine'); },
  back(a, t) { click(a, t, 1750, 0.06, 0.026, 1.5); },
  ding(a, t) { tone(a, t, 1180, 0.10, 0.55, 'sine'); tone(a, t + 0.005, 2360, 0.028, 0.34, 'sine'); },
  slide(a, t) { sweep(a, t, 2200, 380, 0.055, 0.34); },
};

// ---------------- 组件样式（注入一次） ----------------
const CSS = `
.twx{position:fixed;inset:0;z-index:900;display:none;font-family:'Segoe UI','PingFang SC','Microsoft YaHei',system-ui,sans-serif;color:#f4e3c4}
.twx.open{display:block}
.twx-bg{position:absolute;inset:0;background:radial-gradient(125% 85% at 50% 116%,#5a3415 0%,#321d0c 38%,#170e06 68%,#080503 100%)}
.twx-lamp{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(46% 40% at 16% 6%,rgba(255,196,118,.30),transparent 70%),
             radial-gradient(40% 34% at 86% 12%,rgba(255,150,70,.18),transparent 72%),
             radial-gradient(70% 46% at 50% 100%,rgba(255,170,90,.14),transparent 78%)}
.twx-vig{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(78% 62% at 50% 46%,transparent 26%,rgba(0,0,0,.62) 82%,rgba(0,0,0,.86) 100%)}
.twx-dust{position:absolute;inset:0;overflow:hidden;pointer-events:none;opacity:.5}
.twx-dust i{position:absolute;width:3px;height:3px;border-radius:50%;background:rgba(255,214,150,.7);
  box-shadow:0 0 8px rgba(255,196,120,.8);animation:twxFloat linear infinite}
@keyframes twxFloat{0%{transform:translateY(12vh) scale(.6);opacity:0}
  12%{opacity:.9}88%{opacity:.7}100%{transform:translateY(-70vh) scale(1.1);opacity:0}}

.twx-shell{position:absolute;left:0;right:0;bottom:0;height:min(80vh,780px);display:flex;flex-direction:column}
.twx-head{display:flex;align-items:center;gap:14px;padding:14px 26px 6px;flex-shrink:0}
.twx-head .ed{font-size:13px;letter-spacing:1px;color:#f0cf9a}
.twx-head .ed b{color:#ffd9a0;font-weight:700}
.twx-head .hi{font-size:11px;color:#a9885e;line-height:1.7;flex:1}
.twx-head .hi kbd{background:rgba(255,214,150,.14);border:1px solid rgba(255,214,150,.3);
  border-radius:5px;padding:1px 6px;color:#ffd9a0;font-family:inherit;font-size:11px}
.twx-close{background:rgba(255,214,150,.10);border:1px solid rgba(255,214,150,.34);color:#ffd9a0;
  border-radius:9px;padding:6px 13px;font-size:12px;cursor:pointer;transition:.15s;font-family:inherit}
.twx-close:hover{background:rgba(255,214,150,.24)}

.twx-stage{flex:1;position:relative;display:flex;align-items:flex-end;justify-content:center;
  perspective:1400px;perspective-origin:50% 22%;padding-bottom:6px}
.twx-machine{position:relative;width:min(1020px,94vw);transform-style:preserve-3d;
  transform:rotateX(17deg) translateZ(0);animation:twxRise .5s cubic-bezier(.2,.9,.3,1)}
@keyframes twxRise{from{opacity:0;transform:rotateX(26deg) translateY(64px)}to{opacity:1;transform:rotateX(17deg) translateY(0)}}

/* —— 字模臂扇形（打字杆） —— */
.twx-bars{position:absolute;left:50%;bottom:322px;width:min(560px,58vw);height:170px;
  transform:translateX(-50%);pointer-events:none;transform-style:preserve-3d;z-index:1}
.twx-baritem{position:absolute;left:50%;bottom:0;width:7px;height:142px;margin-left:-3.5px;
  transform-origin:50% 100%;border-radius:4px 4px 2px 2px;
  background:linear-gradient(180deg,#e6d3ad 0%,#b39a6c 42%,#6d5837 100%);
  box-shadow:inset 0 0 0 1px rgba(28,18,8,.55),0 0 8px rgba(0,0,0,.5);
  transform:translateY(16px) rotate(var(--a,0deg)) scaleY(.9);opacity:.72}
.twx-baritem::after{content:'';position:absolute;left:1px;right:1px;top:5px;height:16px;border-radius:3px;
  background:linear-gradient(180deg,#fff4d8,#c9b183);opacity:.85}
.twx-baritem.strike{animation:twxStrike .19s cubic-bezier(.2,.7,.3,1) 1}
@keyframes twxStrike{
  0%{transform:translateY(12px) rotate(var(--a,0deg)) scaleY(.9);opacity:.8}
  34%{transform:translateY(-14px) rotate(var(--a,0deg)) scaleY(1.08);opacity:1}
  100%{transform:translateY(16px) rotate(var(--a,0deg)) scaleY(.9);opacity:.72}}

/* —— 纸张（从滚筒里吐出，逐行上移） —— */
.twx-paperwrap{position:relative;margin:0 auto;width:min(560px,62vw);z-index:3}
.twx-paper{position:relative;height:240px;overflow:hidden;border-radius:3px 3px 0 0;
  background:linear-gradient(180deg,#fdf7e7 0%,#f3ead3 62%,#e6d9bd 100%);
  box-shadow:0 -6px 26px rgba(0,0,0,.5),inset 0 0 60px rgba(150,116,70,.16)}
.twx-paper::before{content:'';position:absolute;inset:0;pointer-events:none;opacity:.9;
  background-image:repeating-linear-gradient(180deg,transparent 0 28px,rgba(158,131,94,.26) 28px 30px);
  background-position:0 10px}
.twx-paper::after{content:'';position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(90deg,rgba(120,92,52,.16),transparent 8%,transparent 92%,rgba(120,92,52,.16))}
.twx-inner{position:absolute;left:0;right:0;top:0;padding:0 34px;
  transition:transform .3s cubic-bezier(.3,.85,.3,1);
  font-family:'KaiTi','STKaiti','Kaiti SC','FangSong',serif;font-size:20px;line-height:30px;
  color:#2f2617;white-space:pre-wrap;word-break:break-all;text-shadow:0 0 1px rgba(40,28,10,.5)}
.twx-caret{display:inline-block;width:.55em;color:#b4341f;animation:twxBlink .8s steps(1) infinite}
@keyframes twxBlink{50%{opacity:0}}
.twx-flash{position:absolute;left:50%;bottom:-14px;width:150px;height:86px;margin-left:-75px;
  border-radius:50%;pointer-events:none;opacity:0;filter:blur(2px);
  background:radial-gradient(circle,rgba(255,240,200,.98) 0%,rgba(255,196,112,.46) 42%,transparent 74%)}
.twx-flash.on{animation:twxFlash .27s ease-out 1}
@keyframes twxFlash{0%{opacity:0;transform:scale(.55)}22%{opacity:1;transform:scale(1.06)}100%{opacity:0;transform:scale(1.42)}}

/* —— 滚筒 + 字车 —— */
.twx-roller{position:relative;height:46px;margin:0 auto;width:min(600px,66vw);border-radius:0 0 12px 12px;
  background:linear-gradient(180deg,#8d7250 0%,#4a3823 34%,#2b1f12 78%,#171009 100%);
  box-shadow:0 16px 34px rgba(0,0,0,.6),inset 0 2px 0 rgba(255,222,170,.28)}
.twx-roller .k{position:absolute;top:6px;width:34px;height:34px;border-radius:50%;
  background:radial-gradient(circle at 34% 30%,#e6d2a8,#8b7350 58%,#4a3823);
  box-shadow:0 3px 8px rgba(0,0,0,.6),inset 0 0 0 1px rgba(30,20,8,.6)}
.twx-roller .k.l{left:-15px}.twx-roller .k.r{right:-15px}
.twx-carriage{position:absolute;bottom:50px;left:0;width:100%;height:5px;border-radius:3px;
  background:linear-gradient(90deg,transparent,rgba(255,216,150,.42),transparent);pointer-events:none}
.twx-carriage i{position:absolute;top:-5px;left:0;width:14px;height:15px;border-radius:2px;
  background:linear-gradient(180deg,#ffe6b4,#a98a56);box-shadow:0 0 10px rgba(255,200,120,.75);
  transition:transform .1s linear}

/* —— 键盘（阶梯键位，按键下沉） —— */
.twx-keybed{position:relative;margin:-6px auto 0;width:min(940px,88vw);padding:16px 20px 18px;
  border-radius:8px 8px 18px 18px;
  background:linear-gradient(180deg,#33220f 0%,#241708 46%,#160e05 100%);
  box-shadow:0 -3px 0 rgba(255,216,150,.16),0 26px 54px rgba(0,0,0,.7),inset 0 1px 0 rgba(255,210,150,.22)}
.twx-row{display:flex;justify-content:center;gap:8px;margin-bottom:8px}
.twx-row:last-child{margin-bottom:0}
.twx-key{position:relative;width:52px;height:40px;flex:0 0 auto;transform-style:preserve-3d}
.twx-key.wide{width:104px}
.twx-key.wider{width:210px}
.twx-key .cap{position:absolute;left:0;right:0;top:0;height:40px;border-radius:8px;
  display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;letter-spacing:.4px;
  color:#2b1c0c;background:linear-gradient(180deg,#f7e9c9 0%,#e0cba0 52%,#c3a878 100%);
  box-shadow:0 5px 0 #6d5330,0 7px 10px rgba(0,0,0,.55),inset 0 1px 0 rgba(255,255,255,.7),
    inset 0 -2px 0 rgba(120,92,52,.5);
  transition:transform .05s ease-out,box-shadow .05s ease-out}
.twx-key.down .cap{transform:translateY(5px);
  box-shadow:0 0 0 #6d5330,0 1px 3px rgba(0,0,0,.6),inset 0 1px 0 rgba(255,255,255,.35),
    inset 0 -1px 0 rgba(120,92,52,.6);
  background:linear-gradient(180deg,#e8d5ac 0%,#d3bd8f 52%,#b89f70 100%)}
.twx-key .cap.hot{box-shadow:0 5px 0 #6d5330,0 0 20px rgba(255,190,110,.9),0 7px 10px rgba(0,0,0,.55),
  inset 0 1px 0 rgba(255,255,255,.7)}

/* —— 候选栏 —— */
.twx-cand{display:flex;align-items:center;gap:12px;padding:12px 26px 18px;flex-shrink:0;min-height:64px}
.twx-pinyin{min-width:132px;font-size:16px;letter-spacing:2px;color:#ffd9a0;
  font-family:'Courier New',monospace;border-bottom:1px dashed rgba(255,214,150,.5);padding-bottom:3px;
  text-transform:lowercase}
.twx-pinyin em{color:#a9885e;font-style:normal;font-size:14px}
.twx-cands{display:flex;flex-wrap:wrap;gap:8px;flex:1}
.twx-c{display:inline-flex;align-items:center;gap:7px;background:rgba(255,214,150,.09);
  border:1px solid rgba(255,214,150,.3);color:#ffe9c4;border-radius:9px;padding:6px 12px;
  font-size:15px;cursor:pointer;transition:.12s;font-family:'KaiTi','Kaiti SC',serif}
.twx-c:hover{background:rgba(255,214,150,.26)}
.twx-c i{font-style:normal;font-size:10px;color:#a9885e;font-family:inherit}
/* AI 生成的候选词：蓝色区分 */
.twx-c.ai{background:rgba(140,220,255,.12);border-color:rgba(140,220,255,.45);color:#d8f3ff}
.twx-c.ai:hover{background:rgba(140,220,255,.3)}
.twx-c.ai i{color:#7fd0ff}
.twx-pinyin em.twx-ai{color:#7fd0ff}
.twx-none{font-size:12px;color:#8a6f4c}
`;

// ---------------- 组件主体 ----------------
const KEY_ROWS = [
  [['Digit1','1'],['Digit2','2'],['Digit3','3'],['Digit4','4'],['Digit5','5'],['Digit6','6'],['Digit7','7'],['Digit8','8'],['Digit9','9'],['Digit0','0'],['Minus','·'],['Equal','—'],['Backspace','⌫','wide']],
  [['KeyQ','Q'],['KeyW','W'],['KeyE','E'],['KeyR','R'],['KeyT','T'],['KeyY','Y'],['KeyU','U'],['KeyI','I'],['KeyO','O'],['KeyP','P'],['BracketLeft','（'],['BracketRight','）']],
  [['KeyA','A'],['KeyS','S'],['KeyD','D'],['KeyF','F'],['KeyG','G'],['KeyH','H'],['KeyJ','J'],['KeyK','K'],['KeyL','L'],['Semicolon','；'],['Quote','“']],
  [['KeyZ','Z'],['KeyX','X'],['KeyC','C'],['KeyV','V'],['KeyB','B'],['KeyN','N'],['KeyM','M'],['Comma','，'],['Period','。'],['Slash','？']],
  [['ControlLeft','Ctrl'],['AltLeft','Alt'],['Space','SPACE','wider'],['Enter','↵ 回车','wide']],
];
// 数字键 → 输出字符（中文标点，符合中文打字机语感）
const CODE_CHAR = {
  Minus:'·', Equal:'—', BracketLeft:'（', BracketRight:'）', Semicolon:'；', Quote:'“',
  Comma:'，', Period:'。', Slash:'？',
};
// 小键盘数字映射到主键盘数字（键帽下沉动画也落在同一颗键上）
const NUMPAD_MAP = {
  Numpad0:'Digit0', Numpad1:'Digit1', Numpad2:'Digit2', Numpad3:'Digit3', Numpad4:'Digit4',
  Numpad5:'Digit5', Numpad6:'Digit6', Numpad7:'Digit7', Numpad8:'Digit8', Numpad9:'Digit9',
};

const S = {
  inited: false, open: false, el: null, opts: null,
  text: '', buf: '', cands: [], candPage: 0, keyMap: {}, enterCommit: false,
  aiSet: new Set(),   // 当前候选里哪些来自 AI（用于蓝色标注）
  aiToken: 0,         // 请求序号：缓冲变了就作废旧响应
  aiTimer: null,
  aiLoading: false,
};

function el(id) { return document.getElementById(id); }

function ensureDOM() {
  if (S.inited) return;
  const style = document.createElement('style');
  style.id = 'twx-style';
  style.textContent = CSS;
  document.head.appendChild(style);

  const root = document.createElement('div');
  root.className = 'twx';
  root.id = 'twx';
  root.innerHTML = `
    <div class="twx-bg"></div>
    <div class="twx-lamp"></div>
    <div class="twx-vig"></div>
    <div class="twx-dust" id="twx-dust"></div>
    <div class="twx-shell">
      <div class="twx-head">
        <div class="ed">正在编辑 · <b id="twx-label">内容</b></div>
        <div class="hi">拼音输入 → 下方选词　·　<kbd>1</kbd>~<kbd>9</kbd> 或 <kbd>空格</kbd> 上屏　·　<kbd>回车</kbd> 换行/确认　·　<kbd>Esc</kbd> 收起</div>
        <button class="twx-close" id="twx-close">收起 ⌄</button>
      </div>
      <div class="twx-stage">
        <div class="twx-machine" id="twx-machine">
          <div class="twx-bars" id="twx-bars"></div>
          <div class="twx-paperwrap">
            <div class="twx-paper" id="twx-paper">
              <div class="twx-inner" id="twx-inner"><span id="twx-text"></span><span class="twx-caret" id="twx-caret">▌</span></div>
              <div class="twx-flash" id="twx-flash"></div>
            </div>
          </div>
          <div class="twx-roller">
            <i class="k l"></i><i class="k r"></i>
            <div class="twx-carriage"><i id="twx-head-mark"></i></div>
          </div>
          <div class="twx-keybed" id="twx-keybed"></div>
        </div>
      </div>
      <div class="twx-cand">
        <div class="twx-pinyin" id="twx-pinyin"><em>拼音</em></div>
        <div class="twx-cands" id="twx-cands"><span class="twx-none">直接敲键盘即可开始 · 字母组成拼音 → 数字键或点击选词 · Tab 换候选页</span></div>
      </div>
    </div>`;
  document.body.appendChild(root);

  // 字模臂
  const bars = el('twx-bars');
  for (let i = 0; i < BAR_COUNT; i++) {
    const b = document.createElement('div');
    b.className = 'twx-baritem';
    const a = -64 + (128 / (BAR_COUNT - 1)) * i;
    b.style.setProperty('--a', a.toFixed(2) + 'deg');
    bars.appendChild(b);
  }
  // 键位
  const bed = el('twx-keybed');
  KEY_ROWS.forEach(row => {
    const r = document.createElement('div');
    r.className = 'twx-row';
    row.forEach(([code, label, wide]) => {
      const k = document.createElement('div');
      k.className = 'twx-key' + (wide ? ' ' + wide : '');
      k.dataset.code = code;
      k.innerHTML = `<div class="cap">${label}</div>`;
      k.addEventListener('pointerdown', ev => { ev.preventDefault(); hitKey(code); });
      r.appendChild(k);
      S.keyMap[code] = k;
    });
    bed.appendChild(r);
  });
  // 浮尘
  const dust = el('twx-dust');
  let seed = 7;
  const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };
  for (let i = 0; i < 22; i++) {
    const d = document.createElement('i');
    d.style.left = (rnd() * 100).toFixed(1) + '%';
    d.style.bottom = (-rnd() * 30).toFixed(1) + '%';
    d.style.animationDuration = (9 + rnd() * 12).toFixed(1) + 's';
    d.style.animationDelay = (-rnd() * 14).toFixed(1) + 's';
    d.style.opacity = (0.25 + rnd() * 0.6).toFixed(2);
    dust.appendChild(d);
  }

  el('twx-close').onclick = () => close(true);
  root.querySelector('.twx-bg').addEventListener('click', () => close(true));
  root.querySelector('.twx-vig').addEventListener('click', () => close(true));

  S.inited = true;
}

// —— 纸张排版：当前行始终停在第 N 行（打印点），上一行平滑上移 ——
function layout(animate) {
  const inner = el('twx-inner');
  if (!inner) return;
  if (!animate) inner.style.transition = 'none';
  const lines = Math.max(1, Math.round(inner.scrollHeight / LH));
  const ty = (PAPER_H - PAPER_PAD) - lines * LH;
  inner.style.transform = `translateY(${ty}px)`;
  if (!animate) { void inner.offsetHeight; inner.style.transition = ''; }
  // 字车跟着打印点（光标）走
  const mark = el('twx-head-mark'), caret = el('twx-caret'), paper = el('twx-paper');
  if (mark && caret && paper) {
    const c = caret.getBoundingClientRect(), p = paper.getBoundingClientRect();
    if (p.width > 0) {
      const w = Math.max(0, Math.min(p.width - 14, c.left - p.left));
      mark.style.transform = `translateX(${w}px)`;
    }
  }
}
function setPaperText(v) {
  S.text = v == null ? '' : String(v);
  el('twx-text').textContent = S.text;
  layout(false);
}

// —— 候选栏（分页：每页 9 个，共 3 页；Tab 翻页，数字键选本页第 N 个） ——
function renderCands() {
  const py = el('twx-pinyin'), box = el('twx-cands');
  if (!py || !box) return;
  box.innerHTML = '';
  if (!S.buf) {
    py.innerHTML = '<em>拼音</em>';
    box.innerHTML = '<span class="twx-none">直接敲键盘即可开始 · 字母组成拼音 → 数字键或点击选词 · Tab 换候选页</span>';
    return;
  }
  const pages = Math.max(1, Math.ceil(S.cands.length / CAND_PER_PAGE));
  if (S.candPage >= pages) S.candPage = pages - 1;
  if (S.candPage < 0) S.candPage = 0;
  py.innerHTML = S.buf + (pages > 1
    ? ` <em>第 ${S.candPage + 1}/${pages} 页 · Tab 换页</em>` : '')
    + (S.aiLoading ? ' <em class="twx-ai">AI 补全中…</em>'
      : (S.aiSet.size ? ' <em class="twx-ai">AI</em>' : ''));

  if (!S.cands.length) {
    box.innerHTML = '<span class="twx-none">无匹配候选，回车原样上屏</span>';
    return;
  }
  const from = S.candPage * CAND_PER_PAGE;
  S.cands.slice(from, from + CAND_PER_PAGE).forEach((c, i) => {
    const b = document.createElement('span');
    b.className = 'twx-c' + (S.aiSet.has(c) ? ' ai' : '');
    b.innerHTML = `<i>${i + 1}</i>${c}`;
    b.addEventListener('pointerdown', ev => { ev.preventDefault(); commitCand(i); });
    box.appendChild(b);
  });
  if (pages > 1) {
    const more = document.createElement('span');
    more.className = 'twx-none';
    more.textContent = `共 ${S.cands.length} 个候选 · Tab 换页`;
    box.appendChild(more);
  }
}
function refreshCands() {
  S.cands = pinyinCandidates(S.buf);
  S.candPage = 0;
  S.aiSet = new Set();
  S.aiLoading = false;
  renderCands();
  scheduleAI();
}
// 异步向大模型要「更日常」的候选词，补到候选栏最前面（防抖 + 过期作废）
function scheduleAI() {
  clearTimeout(S.aiTimer);
  const buf = S.buf;
  S.aiLoading = false;
  if (!S.open || !buf || buf.length < 2) return;
  const token = ++S.aiToken;
  S.aiTimer = setTimeout(async () => {
    if (token !== S.aiToken) return;
    S.aiLoading = true;
    renderCands();
    let list = null;
    try { list = await aiPinyin(buf); } catch (e) { list = null; }
    if (token !== S.aiToken) return;               // 缓冲已变，丢弃这次结果
    S.aiLoading = false;
    if (list && list.length) {
      const localSet = new Set(S.cands);
      const fresh = list.filter(w => !localSet.has(w) && w !== buf);
      if (fresh.length) {
        S.aiSet = new Set(fresh);
        S.cands = fresh.concat(S.cands);           // AI 词放最前
        S.candPage = 0;
      }
    }
    renderCands();
  }, 380);
}
// 翻候选页（Tab / Shift+Tab）
function pageCands(dir) {
  if (!S.buf || S.cands.length <= CAND_PER_PAGE) return false;
  const pages = Math.ceil(S.cands.length / CAND_PER_PAGE);
  S.candPage = (S.candPage + dir + pages) % pages;
  renderCands();
  play('press');
  return true;
}

// —— 动作 ——
function strikeAnim(ch) {
  const bars = el('twx-bars');
  if (bars && bars.children.length) {
    const idx = ((ch ? ch.charCodeAt(0) : 0) * 7 + (S.text.length * 3)) % bars.children.length;
    const b = bars.children[idx];
    b.classList.remove('strike'); void b.offsetWidth; b.classList.add('strike');
  }
  const f = el('twx-flash');
  if (f) { f.classList.remove('on'); void f.offsetWidth; f.classList.add('on'); }
}
function play(kind) {
  const a = ac(); if (!a) return;
  try { SFX[kind](a, a.currentTime + 0.001); } catch (e) { /* 忽略音频异常 */ }
}
function sinkKey(code) {
  const k = S.keyMap[code];
  if (!k) return;
  k.classList.add('down');
  setTimeout(() => k.classList.remove('down'), 78);
}
function appendText(s, animate) {
  S.text += s;
  el('twx-text').textContent = S.text;
  layout(!!animate);
  sync();
}
function backspace() {
  if (S.buf) { S.buf = S.buf.slice(0, -1); refreshCands(); play('press'); return; }
  if (S.text) { S.text = S.text.slice(0, -1); el('twx-text').textContent = S.text; layout(false); sync(); }
  play('back');
}
function commitCand(i) {
  if (!S.buf) return;
  const gi = S.candPage * CAND_PER_PAGE + i;      // 本页第 i 个 → 全局第 gi 个
  const c = S.cands[gi] || S.buf;
  S.buf = '';
  refreshCands();
  appendText(c);
  play('strike');
  strikeAnim(c[c.length - 1]);
}
function commitBuffer() {
  if (!S.buf) return false;
  commitCand(0);
  return true;
}
// 换行：纸张平滑向上移动一行（回车铃 + 字车滑动音）
function newLine() {
  appendText('\n', true);
  play('slide');
  setTimeout(() => play('ding'), 120);
}

// —— 同步回原输入框 ——
function sync() {
  const o = S.opts;
  if (!o || !S.el) return;
  const v = o.multiline ? S.text : S.text.replace(/\n+/g, ' ');
  if (S.el.value !== v) {
    S.el.value = v;
    S.el.dispatchEvent(new Event('input', { bubbles: true }));
  }
}
function syncFinal() {
  const o = S.opts;
  if (!o || !S.el) return;
  const v = o.multiline ? S.text : S.text.replace(/\n+/g, ' ').trim();
  S.el.value = v;
  S.el.dispatchEvent(new Event('input', { bubbles: true }));
  S.el.dispatchEvent(new Event('change', { bubbles: true }));
}

// —— 键盘事件 ——
// 数字键：有拼音候选时先用于选词上屏；否则（或没有对应候选）直接打出数字
function digitKey(d) {
  if (S.buf && d !== '0') {
    const i = parseInt(d, 10) - 1;
    if (S.cands[i]) { commitCand(i); return; }
    commitBuffer();          // 没有第 i 个候选 → 先把拼音原样上屏
  }
  doChar(d);
}
function hitKey(code) {
  const c = NUMPAD_MAP[code] || code;
  sinkKey(c);
  if (/^Digit[0-9]$/.test(c)) { digitKey(c.slice(5)); return; }
  if (c === 'Backspace') { backspace(); return; }
  if (c === 'Enter') { doEnter(); return; }
  if (c === 'Space') { doSpace(); return; }
  if (c === 'ControlLeft' || c === 'AltLeft') { play('press'); return; }
  const ch = CODE_CHAR[c];
  if (ch) doChar(ch);
}
function doEnter() {
  if (S.buf) { commitBuffer(); return; }
  if (S.opts && S.opts.multiline) { newLine(); return; }
  // 单行输入：回车 = 确认并收起（仍播放回车铃 + 纸张上移）
  S.enterCommit = true;
  newLine();
  setTimeout(() => close(true), 320);
}
function doSpace() {
  if (S.buf) { commitBuffer(); return; }
  appendText(' ');
  play('space');
}
function doChar(ch) {
  if (/^[a-zA-Z]$/.test(ch)) {
    S.buf += ch.toLowerCase();
    refreshCands();
    play('press');
    strikeAnim(ch);
    return;
  }
  if (S.buf) commitBuffer();               // 非字母键：先把拼音上屏
  appendText(ch);
  play('strike');
  strikeAnim(ch);
}

function onKeyDown(e) {
  if (!S.open) return;
  if (e.ctrlKey || e.metaKey || e.altKey) return;   // 放行浏览器快捷键
  const code = NUMPAD_MAP[e.code] || e.code || '';
  if (code === 'Escape') { e.preventDefault(); close(true); return; }
  if (code === 'Tab') { e.preventDefault(); pageCands(e.shiftKey ? -1 : 1); return; }
  if (!S.keyMap[code]) return;

  e.preventDefault();
  if (e.repeat && (code === 'Enter' || code === 'Space')) return;
  sinkKey(code);

  // 数字键：有拼音缓冲时优先选词，否则直接打出数字（以前这里会静默丢掉数字）
  if (/^Digit[0-9]$/.test(code)) { digitKey(code.slice(5)); return; }
  if (/^[a-zA-Z]$/.test(e.key || '')) { doChar(e.key); return; }
  if (code === 'Backspace') { backspace(); return; }
  if (code === 'Enter') { doEnter(); return; }
  if (code === 'Space') { doSpace(); return; }
  if (code === 'ControlLeft' || code === 'AltLeft') { play('press'); return; }
  const ch = CODE_CHAR[code];
  if (ch) doChar(ch);
}

// —— 打开 / 关闭 ——
function open(elem, opts) {
  ensureDOM();
  S.el = elem;
  S.opts = Object.assign({ label: '内容', multiline: false, onEnter: null }, opts || {});
  S.buf = ''; S.cands = []; S.candPage = 0; S.enterCommit = false;
  el('twx-label').textContent = S.opts.label;
  const m = el('twx-machine');
  m.style.animation = 'none'; void m.offsetWidth; m.style.animation = '';
  const root = el('twx');
  root.classList.add('open');
  root.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
  if (elem.blur) elem.blur();
  elem.classList.add('twx-active');
  S.open = true;
  setPaperText(elem.value || '');   // 在可见状态下排版，字车位置才准
  refreshCands();
  ac();  // 借用户手势解锁音频
}
function close(commitVal) {
  if (!S.open) return;
  S.open = false;
  // 关闭时取消未完成的 AI 候选请求，避免关闭后仍发请求 / 回写
  clearTimeout(S.aiTimer); S.aiToken++; S.aiLoading = false; S.aiSet = new Set();
  const wasEnter = S.enterCommit; S.enterCommit = false;
  if (commitVal !== false) { commitBuffer(); syncFinal(); }
  el('twx').classList.remove('open');
  el('twx').setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
  if (S.el) S.el.classList.remove('twx-active');
  const o = S.opts, e = S.el;
  S.el = null; S.opts = null;
  if (wasEnter && o && typeof o.onEnter === 'function') {
    try { o.onEnter(e); } catch (err) { /* noop */ }
  }
}

document.addEventListener('keydown', onKeyDown, true);

/**
 * 让某个输入框 / 文本域在获得焦点时升起打字机。
 * @param {HTMLInputElement|HTMLTextAreaElement} elem
 * @param {{label?:string, multiline?:boolean, onEnter?:(el)=>void}} [opts]
 */
export function attachTypewriter(elem, opts) {
  if (!elem || elem.__twx) return;
  elem.__twx = true;
  elem.setAttribute('autocomplete', 'off');
  elem.addEventListener('focus', () => {
    if (S.open && S.el === elem) return;
    open(elem, opts);
  });
  elem.addEventListener('click', () => {
    if (S.open && S.el === elem) return;
    open(elem, opts);
  });
}

export default { attachTypewriter, pinyinCandidates };
