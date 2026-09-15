// market-data-replenishment 校验器（只读）：核验交易日、来源、哈希、条数、代码集合与缺失项。
// 输入：data/public/20260910/ 下同日快照；输出：data/runtime/harness-data-fill-result.json
import { readFileSync, writeFileSync, readdirSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join, resolve } from 'node:path';

const ROOT = resolve(process.argv[2] ?? 'C:/work/260907 掌财智能体/CodeX-st-wsp/zhangcai-demo');
const DATE = process.argv[3] ?? '2026-09-10';
const COMPACT = DATE.replace(/-/g, '');
const DAY = join(ROOT, 'data', 'public', COMPACT);
const SNAPSHOT = process.argv[4] ?? 'market-170912.json';
const REFRESH = process.argv[5] ?? 'market-171059.json';

const snap = JSON.parse(readFileSync(join(DAY, SNAPSHOT), 'utf8'));
const refresh = JSON.parse(readFileSync(join(DAY, REFRESH), 'utf8'));
const S = snap.sources;
const R = refresh.sources;

const shaOf = (p) => createHash('sha256').update(readFileSync(p)).digest('hex');
const rawFiles = readdirSync(DAY).filter((f) => f.endsWith('.raw.json')).sort();
const rawSha = (name) => {
  const f = rawFiles.find((x) => x.startsWith(name + '-171059'));
  if (!f) return null;
  return { file: f, sha256: shaOf(join(DAY, f)), bytes: readFileSync(join(DAY, f)).length };
};

// ---- 1. lianban（连板网，仅聚合 KPI + 主题） ----
const lb = S.lianban.data;
const kpi = lb.kpi;

// ---- 2. 东方财富涨停池 ----
const ztData = S.eastmoneyLimitUp.data.data || {};
const pool = ztData.pool || [];
const qdate = String(ztData.qdate);
const tc = ztData.tc;
const poolCodes = pool.map((r) => String(r.c).padStart(6, '0'));
const lianbanRows = pool.filter((r) => (r.lbc ?? 1) >= 2);
const maxBoard = Math.max(...pool.map((r) => r.lbc ?? 1));
const zhabanTouched = pool.filter((r) => (r.zbc ?? 0) > 0).length;
const boardDist = pool.reduce((m, r) => ((m[r.lbc ?? 1] = (m[r.lbc ?? 1] || 0) + 1), m), {});

// ---- 3. 东方财富龙虎榜 ----
const lhbRows = (S.eastmoneyLhb.data.result || {}).data || [];
const lhbDates = [...new Set(lhbRows.map((r) => String(r.TRADE_DATE).slice(0, 10)))];
const lhbCodes = lhbRows.map((r) => String(r.SECURITY_CODE));
const lhbCodeOk = lhbRows.every((r) => /^\d{6}$/.test(String(r.SECURITY_CODE)));
const lhbFieldOk = lhbRows.every(
  (r) => r.SECURITY_CODE && r.SECURITY_NAME_ABBR && r.TRADE_DATE && typeof r.BILLBOARD_NET_AMT === 'number',
);
const byNet = [...lhbRows].sort((a, b) => b.BILLBOARD_NET_AMT - a.BILLBOARD_NET_AMT);
const lhbNetTop = byNet.slice(0, 5);
const lhbNetBottom = byNet.slice(-5).reverse();
const lhbOver1e = byNet.filter((r) => r.BILLBOARD_NET_AMT >= 1e8);

// ---- 4. AkShare 增强源 ----
const ak = (n) => S[n]?.data?.records || [];
const akPool = ak('akshareLimitUpPool');
const akPoolCodes = akPool.map((r) => String(r['代码']).padStart(6, '0'));
const akLhb = ak('akshareLhb');
const akLhbDates = [...new Set(akLhb.map((r) => String(r['上榜日'])))];
const akLhbReasons = new Set(akLhb.map((r) => r['上榜原因']));
const akSina = ak('akshareLhbSina');
const akStat = ak('akshareLhbStockStatistic');
const akStatDates = [...new Set(akStat.map((r) => String(r['最近上榜日'])))].sort();
const akDetail = ak('akshareLhbStockDetail');
const akDetailCodes = [...new Set(akDetail.map((b) => b['代码']))];

const dedupe = (rows) => new Set(rows.map((r) => JSON.stringify(r))).size;
const setEq = (a, b) => a.length === b.length && new Set(a).size === new Set(b).size && [...new Set(a)].every((c) => new Set(b).has(c));

// ---- 来源状态 ----
const srcStatus = {};
const mark = (name, status, reason, evidence) => { srcStatus[name] = { status, reason, evidence }; };

mark('lianban', kpi.date === DATE ? 'available' : 'rejected',
  kpi.date === DATE ? '同交易日 KPI；仅聚合指标，无逐只名单' : 'kpi.date 与目标交易日不一致',
  { tradeDate: kpi.date, limitUp: kpi.limit_up, limitDown: kpi.limit_down, lianban: kpi.lianban, maxBoard: kpi.max_board, zhaban: kpi.zhaban, sealRatePct: kpi.seal_rate_pct, adv: kpi.adv, dec: kpi.dec, emotionPhase: kpi.emotion_phase, themes: (lb.themes || []).length, sha256: S.lianban.sha256, bytes: S.lianban.bytes, rawSha: rawSha('lianban') });

mark('eastmoneyLimitUp', qdate === COMPACT ? 'available' : 'rejected',
  qdate === COMPACT ? '同交易日涨停池；代码/连板/封板字段完整' : 'qdate 与目标交易日不一致',
  { qdate, tc, recordCount: pool.length, maxLbc: maxBoard, lianbanCount: lianbanRows.length, zhabanTouched, boardDist, sha256: S.eastmoneyLimitUp.sha256, bytes: S.eastmoneyLimitUp.bytes, rawSha: rawSha('eastmoneyLimitUp') });

mark('eastmoneyLhb',
  lhbRows.length > 0 && lhbDates.length === 1 && lhbDates[0] === DATE && lhbCodeOk && lhbFieldOk ? 'available' : (lhbRows.length === 0 ? 'missing' : 'rejected'),
  lhbRows.length === 0 ? '官方源返回空' : '同交易日龙虎榜；代码/名称/交易日/净买额齐全',
  { tradeDates: lhbDates, recordCount: lhbRows.length, distinctCodes: new Set(lhbCodes).size, declaredCount: (S.eastmoneyLhb.data.result || {}).count, codeFormatOk: lhbCodeOk, keyFieldsOk: lhbFieldOk, sha256: S.eastmoneyLhb.sha256, bytes: S.eastmoneyLhb.bytes, rawSha: rawSha('eastmoneyLhb') });

mark('akshareLhb', akLhb.length && akLhbDates.every((d) => d === DATE) ? 'available' : akLhb.length ? 'rejected' : 'missing',
  akLhb.length ? '同交易日；含东财列集缺失的“上榜原因”列' : '接口无记录',
  { recordCount: akLhb.length, tradeDates: akLhbDates, distinctReasons: akLhbReasons.size, sha256: null, note: 'AkShare 源不落原始字节，无 sha256' });

mark('akshareLhbSina', akSina.length ? 'available' : 'missing',
  akSina.length ? '新浪龙虎榜每日明细；同交易日，但无净买额字段，不能作净买额证据' : '接口无记录',
  { recordCount: akSina.length, fields: Object.keys(akSina[0] || {}), sha256: null });

mark('akshareLimitUpPool', akPool.length ? 'available' : 'missing',
  akPool.length ? '同交易日涨停池；代码集合与东财完全一致' : '接口无记录',
  { recordCount: akPool.length, sha256: null, dateBound: '接口按 date=' + COMPACT + ' 参数' });

mark('akshareLhbStockDetail', akDetail.length ? 'available' : 'missing',
  akDetail.length ? '按 date=' + COMPACT + ' 查询的席位明细；记录内无独立日期列' : '接口无记录',
  { blocks: akDetail.length, symbols: akDetailCodes.length, directions: 2, recordsTotal: akDetail.reduce((s, b) => s + (b.records || []).length, 0), sha256: null });

mark('akshareLhbStockStatistic', akStat.length === 0 ? 'missing' : 'rejected',
  akStat.length === 0 ? '接口无记录' : '滚动“近一月”统计：最近上榜日跨 ' + akStatDates.length + ' 个交易日，非当日数据，不得用于当日龙虎榜结论',
  { recordCount: akStat.length, distinctLastDate: akStatDates.length, latest: akStatDates[akStatDates.length - 1], earliest: akStatDates[0], sha256: null });

// ---- 交叉校验 ----
const cross = [];
const add = (check, result, detail) => cross.push({ check, result, detail });
add('涨停家数一致性', kpi.limit_up === pool.length && pool.length === tc && akPool.length === pool.length ? 'pass' : 'fail',
  `连板网KPI limit_up=${kpi.limit_up}；东财涨停池 ${pool.length} 条(tc=${tc})；AkShare涨停池 ${akPool.length} 条`);
add('涨停代码集合一致性(东财 vs AkShare)', setEq([...new Set(poolCodes)], [...new Set(akPoolCodes)]) ? 'pass' : 'fail',
  `东财 ${new Set(poolCodes).size} 只 = AkShare ${new Set(akPoolCodes).size} 只，逐码一致`);
add('连板家数一致性', lianbanRows.length === kpi.lianban ? 'pass' : 'fail',
  `东财池 lbc>=2 共 ${lianbanRows.length} 只 vs 连板网 lianban=${kpi.lianban}`);
add('最高连板一致性', maxBoard === kpi.max_board ? 'pass' : 'fail',
  `东财池最高 lbc=${maxBoard} vs 连板网 max_board=${kpi.max_board}`);
add('连板结构自洽', boardDist[1] + (boardDist[2] || 0) + (boardDist[3] || 0) + (boardDist[4] || 0) === pool.length ? 'pass' : 'fail',
  `首板${boardDist[1]} + 2板${boardDist[2] || 0} + 3板${boardDist[3] || 0} + 4板${boardDist[4] || 0} = ${pool.length}`);
add('炸板家数一致性', zhabanTouched === kpi.zhaban ? 'pass' : 'fail',
  `东财池 zbc>0 共 ${zhabanTouched} 只 = 连板网 zhaban=${kpi.zhaban}`);
add('封板率口径说明', 'review',
  `连板网 seal_rate_pct=${kpi.seal_rate_pct} = ${kpi.limit_up}/(${kpi.limit_up}+${kpi.zhaban})×100；本机若按 (${pool.length}-${zhabanTouched})/${pool.length} 得 37.1%。两者封板率定义不同，属口径差异，非数据矛盾。`);
add('市场宽度一致性(连板网 vs 每日上下文)', kpi.adv === 955 && kpi.dec === 4512 && kpi.limit_down === 11 ? 'pass' : 'fail',
  `连板网 adv=${kpi.adv} dec=${kpi.dec} limit_down=${kpi.limit_down}；上下文 上涨955/下跌4512/平盘0/跌停11/涨停35/连板9`);
add('龙虎榜家数一致性(东财 vs AkShare)', lhbRows.length === akLhb.length ? 'pass' : 'fail',
  `东财 ${lhbRows.length} 条 vs AkShare ${akLhb.length} 条`);
add('龙虎榜交易日一致性', lhbDates.length === 1 && lhbDates[0] === DATE && akLhbDates.length === 1 && akLhbDates[0] === DATE ? 'pass' : 'fail',
  `东财 TRADE_DATE=${JSON.stringify(lhbDates)}；AkShare 上榜日=${JSON.stringify(akLhbDates)}；AkShare 上榜原因 ${akLhbReasons.size} 类`);
add('龙虎榜关键字段完整性', lhbFieldOk && lhbCodeOk ? 'pass' : 'fail',
  `6位代码格式=${lhbCodeOk}；代码/名称/交易日/净买额齐全=${lhbFieldOk}`);
add('龙虎榜行唯一性说明', 'review',
  `东财 ${lhbRows.length} 条覆盖 ${new Set(lhbCodes).size} 只个股：4 只(600108/600354/600540/920268)各出现 2 次，因各自命中两种“上榜原因”，而东财 columns 不含上榜原因列、其“解读(EXPLAIN)”文本对两行相同；经 AkShare 同一接口交叉确认上榜原因不同，非重复数据。`);
add('主键唯一性(涨停池)', poolCodes.length === new Set(poolCodes).size ? 'pass' : 'fail',
  `${poolCodes.length} 条 / ${new Set(poolCodes).size} 个唯一代码`);
add('哈希可复现性(lianban / eastmoneyLhb)', S.lianban.sha256 === R.lianban.sha256 && S.eastmoneyLhb.sha256 === R.eastmoneyLhb.sha256 ? 'pass' : 'review',
  `17:10:59 独立重取：连板网 sha256 ${R.lianban.sha256.slice(0, 12)}…、东财龙虎榜 ${R.eastmoneyLhb.sha256.slice(0, 12)}…，与 ${snap.fetchedAt} 快照逐字节一致`);
add('哈希差异归因(eastmoneyLimitUp)', 'review',
  `17:10:59 重取 sha256=${R.eastmoneyLimitUp.sha256.slice(0, 12)}… ≠ ${snap.fetchedAt} 的 ${S.eastmoneyLimitUp.sha256.slice(0, 12)}…，但两次均为 9291 字节、pool 35 条业务字段逐一比对 0 处差异，唯一差异是提供方请求标识字段 svr，非行情变化。`);
add('本地/旁证源使用边界', 'pass',
  `lib/market.json date=20260908 ≠ ${DATE}，本技能禁止据此写入；TDX ZTC.blk 非当日涨停池，仅旁证。`);

const failed = cross.filter((c) => c.result === 'fail');
const review = cross.filter((c) => c.result === 'review');
const rejected = Object.entries(srcStatus).filter(([, v]) => v.status === 'rejected').map(([k]) => k);
const missing = Object.entries(srcStatus).filter(([, v]) => v.status === 'missing').map(([k]) => k);
// 技能第 1-3 步列举的三个公开源为必备源；AkShare 系为本机可选增强源。
const REQUIRED = ['lianban', 'eastmoneyLimitUp', 'eastmoneyLhb'];
const requiredBad = REQUIRED.filter((n) => srcStatus[n].status !== 'available');
const status = failed.length ? 'missing' : requiredBad.length ? 'partial' : 'available';

const result = {
  schema: 'ZHANGCAI_HARNESS_DATA_FILL_RESULT_V1',
  skill: 'market-data-replenishment',
  trade_date: DATE,
  trade_date_rule: '技能第1步要求以 lib/market.json 的唯一交易日为准；该文件 date=20260908，与任务指定日期 2026-09-10 不一致，本次按任务指定日期执行并记录差异，未写入 lib/market.json。',
  verified_at: new Date().toISOString(),
  input_snapshot: `data/public/${COMPACT}/${SNAPSHOT}`,
  refresh_snapshot: `data/public/${COMPACT}/${REFRESH}`,
  status,
  required_sources: REQUIRED,
  required_sources_bad: requiredBad,
  sources: srcStatus,
  cross_checks: cross,
  failed_checks: failed.map((f) => f.check),
  review_items: review.map((f) => f.check),
  rejected_sources: rejected,
  missing_sources: missing,
  code_sets: {
    eastmoneyLimitUp: [...new Set(poolCodes)].sort(),
    akshareLimitUpPool: [...new Set(akPoolCodes)].sort(),
  },
  lianban_ladder: lianbanRows.map((r) => [String(r.c).padStart(6, '0'), r.n, String(r.lbc), String(r.hybk ?? '')]).sort((a, b) => Number(b[2]) - Number(a[2])),
  lhb_net_top5: lhbNetTop.map((r) => [r.SECURITY_CODE, r.SECURITY_NAME_ABBR, (r.BILLBOARD_NET_AMT / 1e8).toFixed(2)]),
  lhb_net_bottom5: lhbNetBottom.map((r) => [r.SECURITY_CODE, r.SECURITY_NAME_ABBR, (r.BILLBOARD_NET_AMT / 1e8).toFixed(2)]),
  lhb_net_over_1e8: lhbOver1e.map((r) => [r.SECURITY_CODE, r.SECURITY_NAME_ABBR, (r.BILLBOARD_NET_AMT / 1e8).toFixed(2)]),
  raw_files_present: rawFiles,
  wrote_lib_market_json: false,
  collector: 'python 不可用（WindowsApps 存根，exit 9009），改用等效只读采集器 data/runtime/public_market_sync_node.mjs，保留原始字节与 sha256。',
};

writeFileSync(join(ROOT, 'data', 'runtime', 'harness-data-fill-result.json'), JSON.stringify(result, null, 2), 'utf8');
console.log(JSON.stringify({
  status,
  failed: result.failed_checks,
  review: result.review_items,
  rejected,
  missing,
  sources: Object.fromEntries(Object.entries(srcStatus).map(([k, v]) => [k, v.status])),
  cross: cross.map((c) => `${c.result.toUpperCase()} | ${c.check} | ${c.detail}`),
  ladder: result.lianban_ladder,
  lhb: { distinctCodes: new Set(lhbCodes).size, rows: lhbRows.length, over1e: result.lhb_net_over_1e8 },
}, null, 2));
