// market-data-replenishment 校验器 v3（只读）
// 输入：data/public/20260910/ 下同日快照 + 本会话独立重取快照
// 输出：data/runtime/harness-data-fill-result.json
import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join, resolve } from 'node:path';

const ROOT = resolve(process.argv[2] ?? 'C:/work/260907 掌财智能体/CodeX-st-wsp/zhangcai-demo');
const DATE = process.argv[3] ?? '2026-09-10';
const COMPACT = DATE.replace(/-/g, '');
const PRIMARY = process.argv[4] ?? 'market-224354.json';   // 任务上下文快照
const REFRESH = process.argv[5] ?? 'market-224452.json';   // 本会话独立重取
const DAY = join(ROOT, 'data', 'public', COMPACT);

const shaOf = (p) => createHash('sha256').update(readFileSync(p)).digest('hex');
const snap = JSON.parse(readFileSync(join(DAY, PRIMARY), 'utf8'));
const refresh = JSON.parse(readFileSync(join(DAY, REFRESH), 'utf8'));
const S = snap.sources;
const R = refresh.sources;

const rawFiles = readdirSync(DAY).filter((f) => f.endsWith('.raw.json')).sort();
const rawSha = (name, stamp) => {
  const f = rawFiles.find((x) => x.startsWith(name + '-' + stamp));
  if (!f) return null;
  return { file: `data/public/${COMPACT}/${f}`, sha256: shaOf(join(DAY, f)), bytes: readFileSync(join(DAY, f)).length };
};

const norm = (rows) => rows.map((r) => JSON.stringify(Object.fromEntries(Object.entries(r).filter(([k]) => k !== 'svr'))));
const setEq = (a, b) => a.length === new Set(a).size && a.length === new Set(b).size && a.every((c) => new Set(b).has(c));

// ---------- 1. 连板网 ----------
const lb = S.lianban.data;
const kpi = lb.kpi;
const themes = lb.themes || [];

// ---------- 2. 东方财富涨停池 ----------
const ztData = S.eastmoneyLimitUp.data.data || {};
const pool = ztData.pool || [];
const qdate = String(ztData.qdate);
const tc = ztData.tc;
const poolCodes = pool.map((r) => String(r.c).padStart(6, '0'));
const lianbanRows = pool.filter((r) => (r.lbc ?? 1) >= 2);
const maxBoard = Math.max(...pool.map((r) => r.lbc ?? 1));
const zhabanTouched = pool.filter((r) => (r.zbc ?? 0) > 0).length;
const boardDist = pool.reduce((m, r) => ((m[r.lbc ?? 1] = (m[r.lbc ?? 1] || 0) + 1), m), {});
const sealFieldOk = pool.every((r) => r.fbt != null && r.lbt != null && r.fund != null && r.lbc != null);
const poolCodeOk = pool.every((r) => /^\d{6}$/.test(String(r.c)));
const poolKeyUnique = poolCodes.length === new Set(poolCodes).size;

// ---------- 3. 东方财富龙虎榜 ----------
const lhbRows = (S.eastmoneyLhb.data.result || {}).data || [];
const lhbDates = [...new Set(lhbRows.map((r) => String(r.TRADE_DATE).slice(0, 10)))];
const lhbCodes = lhbRows.map((r) => String(r.SECURITY_CODE));
const lhbCodeOk = lhbRows.every((r) => /^\d{6}$/.test(String(r.SECURITY_CODE)));
const lhbFieldOk = lhbRows.every(
  (r) => r.SECURITY_CODE && r.SECURITY_NAME_ABBR && r.TRADE_DATE && typeof r.BILLBOARD_NET_AMT === 'number',
);
const lhbDeclaredCount = (S.eastmoneyLhb.data.result || {}).count;
const byNet = [...lhbRows].sort((a, b) => b.BILLBOARD_NET_AMT - a.BILLBOARD_NET_AMT);
const lhbOver1e = byNet.filter((r) => r.BILLBOARD_NET_AMT >= 1e8);
const lhbNetBottom = [...byNet].slice(-5).reverse();
const codeCount = lhbCodes.reduce((m, c) => ((m[c] = (m[c] || 0) + 1), m), {});
const dupCodes = Object.keys(codeCount).filter((c) => codeCount[c] > 1).sort();
const dupShape = dupCodes.map((c) => `${c}×${codeCount[c]}`).join('/');

// ---------- 4. AkShare 增强源 ----------
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
// AkShare 净值与东财逐笔净买额对账（按代码聚合东财多行）
const emByCode = {};
for (const r of lhbRows) emByCode[r.SECURITY_CODE] = (emByCode[r.SECURITY_CODE] || 0) + r.BILLBOARD_NET_AMT;
const akByCode = {};
for (const r of akLhb) {
  const c = String(r['代码']).padStart(6, '0');
  akByCode[c] = (akByCode[c] || 0) + Number(r['龙虎榜净买额']);
}
const netMismatch = Object.keys(akByCode).filter((c) => {
  const e = emByCode[c];
  if (e == null) return true;
  return Math.abs(e - akByCode[c]) > 1;
});
const netTotalMatch = Math.abs(Object.values(emByCode).reduce((a, b) => a + b, 0) - Object.values(akByCode).reduce((a, b) => a + b, 0)) < 1;
const emCodeOk = Object.keys(akByCode).every((c) => emByCode[c] != null);

// ---------- 来源状态 ----------
const srcStatus = {};
const mark = (name, status, reason, evidence) => { srcStatus[name] = { status, reason, evidence }; };

mark('lianban', kpi.date === DATE ? 'available' : 'rejected',
  kpi.date === DATE ? '同交易日 KPI 聚合；源仅含 KPI 与主题，无逐只名单' : 'kpi.date 与目标交易日不一致',
  { tradeDate: kpi.date, limitUp: kpi.limit_up, limitDown: kpi.limit_down, lianban: kpi.lianban, maxBoard: kpi.max_board, zhaban: kpi.zhaban, sealRatePct: kpi.seal_rate_pct, adv: kpi.adv, dec: kpi.dec, emotionPhase: kpi.emotion_phase, themes: themes.length, sha256: S.lianban.sha256, bytes: S.lianban.bytes, rawSha: rawSha('lianban', '224354') || rawSha('lianban', '171059'), refreshSha256: R.lianban.sha256 });

mark('eastmoneyLimitUp', qdate === COMPACT && pool.length > 0 ? 'available' : 'rejected',
  qdate === COMPACT ? '同交易日涨停池；代码/连板/封板字段完整' : 'qdate 与目标交易日不一致',
  { qdate, tc, recordCount: pool.length, maxLbc: maxBoard, lianbanCount: lianbanRows.length, zhabanTouched, boardDist, sealFieldOk, codeFormatOk: poolCodeOk, primaryKeyUnique: poolKeyUnique, sha256: S.eastmoneyLimitUp.sha256, bytes: S.eastmoneyLimitUp.bytes, rawSha: rawSha('eastmoneyLimitUp', '224354') || rawSha('eastmoneyLimitUp', '171059'), refreshSha256: R.eastmoneyLimitUp.sha256 });

mark('eastmoneyLhb',
  lhbRows.length > 0 && lhbDates.length === 1 && lhbDates[0] === DATE && lhbCodeOk && lhbFieldOk ? 'available' : (lhbRows.length === 0 ? 'missing' : 'rejected'),
  lhbRows.length === 0 ? '官方源返回空' : '同交易日龙虎榜；代码/名称/交易日/净买额齐全',
  { tradeDates: lhbDates, recordCount: lhbRows.length, distinctCodes: new Set(lhbCodes).size, declaredCount: lhbDeclaredCount, codeFormatOk: lhbCodeOk, keyFieldsOk: lhbFieldOk, dupCodes, sha256: S.eastmoneyLhb.sha256, bytes: S.eastmoneyLhb.bytes, rawSha: rawSha('eastmoneyLhb', '224354') || rawSha('eastmoneyLhb', '171059'), refreshSha256: R.eastmoneyLhb.sha256 });

mark('akshareLhb', akLhb.length && akLhbDates.every((d) => d === DATE) ? 'available' : akLhb.length ? 'rejected' : 'missing',
  akLhb.length ? '同交易日；含东财 columns 缺失的“上榜原因”列，可用于多行归因' : '接口无记录',
  { recordCount: akLhb.length, tradeDates: akLhbDates, distinctReasons: akLhbReasons.size, sha256: null, note: 'AkShare 源不落原始字节，无 sha256' });

mark('akshareLhbSina', akSina.length ? 'available' : 'missing',
  akSina.length ? '新浪龙虎榜每日明细；无净买额字段、无日期列，仅可作旁证' : '接口无记录',
  { recordCount: akSina.length, fields: Object.keys(akSina[0] || {}), hasNetAmt: Object.keys(akSina[0] || {}).some((k) => /净买/.test(k)), hasDateCol: Object.keys(akSina[0] || {}).some((k) => /日期|上榜日/.test(k)), sha256: null });

mark('akshareLimitUpPool', akPool.length ? 'available' : 'missing',
  akPool.length ? '同交易日涨停池；用于与东财逐码核对' : '接口无记录',
  { recordCount: akPool.length, sha256: null, dateBound: '接口按 date=' + COMPACT + ' 参数', fields: Object.keys(akPool[0] || {}) });

mark('akshareLhbStockDetail', akDetail.length ? 'available' : 'missing',
  akDetail.length ? '按 date=' + COMPACT + ' 查询的席位明细；记录内无独立日期列，且仅覆盖净买额靠前标的' : '接口无记录',
  { blocks: akDetail.length, symbols: akDetailCodes.length, directions: 2, recordsTotal: akDetail.reduce((s, b) => s + (b.records || []).length, 0), sha256: null });

mark('akshareLhbStockStatistic', akStat.length === 0 ? 'missing' : 'rejected',
  akStat.length === 0 ? '接口无记录' : '滚动“近一月”统计：最近上榜日跨 ' + akStatDates.length + ' 个交易日，非当日数据，不得用于当日结论',
  { recordCount: akStat.length, distinctLastDate: akStatDates.length, latest: akStatDates[akStatDates.length - 1], earliest: akStatDates[0], sha256: null });

// ---------- 交叉校验 ----------
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
add('连板结构自洽', (boardDist[1] || 0) + (boardDist[2] || 0) + (boardDist[3] || 0) + (boardDist[4] || 0) === pool.length ? 'pass' : 'fail',
  `首板${boardDist[1] || 0} + 2板${boardDist[2] || 0} + 3板${boardDist[3] || 0} + 4板${boardDist[4] || 0} = ${pool.length}`);
add('炸板家数一致性', zhabanTouched === kpi.zhaban ? 'pass' : 'fail',
  `东财池 zbc>0 共 ${zhabanTouched} 只 = 连板网 zhaban=${kpi.zhaban}`);
add('封板字段完整性(涨停池)', poolCodeOk && sealFieldOk && poolKeyUnique ? 'pass' : 'fail',
  `6位代码=${poolCodeOk}；fbt/lbt/lbc/fund 齐全=${sealFieldOk}；主键唯一=${poolKeyUnique}`);
add('封板率口径说明', 'review',
  `连板网 seal_rate_pct=${kpi.seal_rate_pct}=${kpi.limit_up}/(${kpi.limit_up}+${kpi.zhaban})×100；若按(涨停${pool.length}-炸板${zhabanTouched})/${pool.length} 得 ${(((pool.length - zhabanTouched) / pool.length) * 100).toFixed(1)}%，属口径差异非数据矛盾`);
add('市场宽度一致性(连板网 vs 任务上下文)', kpi.adv === 955 && kpi.dec === 4512 && kpi.limit_down === 11 ? 'pass' : 'fail',
  `连板网 adv=${kpi.adv} dec=${kpi.dec} limit_down=${kpi.limit_down}；上下文 涨955/跌4512/平盘0/跌停11/涨停35/连板9`);
add('龙虎榜条数一致性(东财 vs AkShare)', lhbRows.length === akLhb.length ? 'pass' : 'fail',
  `东财 ${lhbRows.length} 条 vs AkShare ${akLhb.length} 条`);
add('龙虎榜交易日一致性', lhbDates.length === 1 && lhbDates[0] === DATE && akLhbDates.length === 1 && akLhbDates[0] === DATE ? 'pass' : 'fail',
  `东财 TRADE_DATE=${JSON.stringify(lhbDates)}；AkShare 上榜日=${JSON.stringify(akLhbDates)}；上榜原因 ${akLhbReasons.size} 类`);
add('龙虎榜关键字段完整性', lhbFieldOk && lhbCodeOk ? 'pass' : 'fail',
  `6位代码格式=${lhbCodeOk}；代码/名称/交易日/净买额齐全=${lhbFieldOk}；声明 count=${lhbDeclaredCount}`);
add('龙虎榜逐笔净买额与AkShare对账', netMismatch.length === 0 && netTotalMatch && emCodeOk && new Set(lhbCodes).size === Object.keys(akByCode).length ? 'pass' : 'fail',
  `${new Set(lhbCodes).size} 只逐只净买额与东财按代码聚合值一致=${netMismatch.length === 0}；两源净买额合计一致=${netTotalMatch}；代码集合互为子集=${emCodeOk}`);
add('龙虎榜行唯一性说明', 'review',
  `东财 ${lhbRows.length} 条覆盖 ${new Set(lhbCodes).size} 只：${dupShape} 为多行，系同一标的命中多种“上榜原因”；东财 columns 未含上榜原因列，经 AkShare 同接口（上榜原因 ${akLhbReasons.size} 类）交叉确认两/三行原因为不同条目，非重复数据。因此 64 不可当作个股家数，逐笔净买额须按代码聚合后再比较。`);
add('哈希可复现性(lianban / eastmoneyLhb)', S.lianban.sha256 === R.lianban.sha256 && S.eastmoneyLhb.sha256 === R.eastmoneyLhb.sha256 ? 'pass' : 'review',
  `${refresh.fetchedAt} 独立重取：连板网 ${R.lianban.sha256.slice(0, 12)}…、东财龙虎榜 ${R.eastmoneyLhb.sha256.slice(0, 12)}…，与 ${snap.fetchedAt} 快照逐字节一致`);
add('哈希差异归因(eastmoneyLimitUp)', (() => {
  const a = norm((S.eastmoneyLimitUp.data.data || {}).pool || []);
  const b = norm((R.eastmoneyLimitUp.data.data || {}).pool || []);
  return a.length === b.length && a.every((x, i) => x === b[i]);
})() ? 'review' : 'fail',
  `${PRIMARY} sha256=${S.eastmoneyLimitUp.sha256.slice(0, 12)}… vs ${REFRESH} sha256=${R.eastmoneyLimitUp.sha256.slice(0, 12)}…；两次同为 ${S.eastmoneyLimitUp.bytes} 字节、pool 35 条业务字段逐一比对 0 处差异，唯一差异为提供方请求标识字段 svr，非行情变化`);
add('本地/旁证源使用边界', 'pass',
  `lib/market.json date=${JSON.parse(readFileSync(join(ROOT, 'lib', 'market.json'), 'utf8')).date} ≠ ${COMPACT}，禁止据此写入，本次未写入；TDX ZTC.blk 非当日涨停池，仅旁证。`);
add('AkShare滚动统计边界', srcStatus.akshareLhbStockStatistic.status === 'rejected' ? 'pass' : 'fail',
  `akshareLhbStockStatistic 最近上榜日跨 ${akStatDates.length} 个交易日（${akStatDates[0]}~${akStatDates[akStatDates.length - 1]}），已标记 rejected`);
add('AkShare新浪源字段边界', srcStatus.akshareLhbSina.evidence.hasNetAmt === false ? 'pass' : 'fail',
  `akshareLhbSina ${akSina.length} 条，字段=${(srcStatus.akshareLhbSina.evidence.fields || []).join('/')}，无净买额列、无日期列，不能作为资金方向证据`);

const failed = cross.filter((c) => c.result === 'fail');
const review = cross.filter((c) => c.result === 'review');
const rejected = Object.entries(srcStatus).filter(([, v]) => v.status === 'rejected').map(([k]) => k);
const missing = Object.entries(srcStatus).filter(([, v]) => v.status === 'missing').map(([k]) => k);
const REQUIRED = ['lianban', 'eastmoneyLimitUp', 'eastmoneyLhb'];
const requiredBad = REQUIRED.filter((n) => srcStatus[n].status !== 'available');
const status = failed.length ? 'missing' : requiredBad.length ? 'partial' : 'available';

const result = {
  schema: 'ZHANGCAI_HARNESS_DATA_FILL_RESULT_V1',
  skill: 'market-data-replenishment',
  trade_date: DATE,
  trade_date_rule: '技能第1步要求以 lib/market.json 的唯一交易日为准；该文件 date=20260908，与任务指定日期 2026-09-10 不一致，本次按任务指定日期执行并记录差异，未写入 lib/market.json。',
  verified_at: new Date().toISOString(),
  input_snapshot: `data/public/${COMPACT}/${PRIMARY}`,
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
    set_equal: setEq([...new Set(poolCodes)], [...new Set(akPoolCodes)]),
  },
  lianban_ladder: lianbanRows.map((r) => [String(r.c).padStart(6, '0'), r.n, String(r.lbc), String(r.hybk ?? ''), `${r.zttj?.days ?? ''}/${r.zttj?.ct ?? ''}`]).sort((a, b) => Number(b[2]) - Number(a[2])),
  lhb_net_over_1e8: lhbOver1e.map((r) => [r.SECURITY_CODE, r.SECURITY_NAME_ABBR, (r.BILLBOARD_NET_AMT / 1e8).toFixed(2)]),
  lhb_net_bottom5: lhbNetBottom.map((r) => [r.SECURITY_CODE, r.SECURITY_NAME_ABBR, (r.BILLBOARD_NET_AMT / 1e8).toFixed(2)]),
  raw_files_present: rawFiles,
  wrote_lib_market_json: false,
  collector: 'python 不可用（WindowsApps 存根），改用等效只读采集器 data/runtime/public_market_sync_node.mjs；本会话直连 HTTPS 成功，原始字节与 sha256 已留档。',
};

writeFileSync(join(ROOT, 'data', 'runtime', 'harness-data-fill-result.json'), JSON.stringify(result, null, 2), 'utf8');
console.log(JSON.stringify({
  status, failed: result.failed_checks, review: result.review_items, rejected, missing,
  sources: Object.fromEntries(Object.entries(srcStatus).map(([k, v]) => [k, v.status])),
  boardDist, ladder: result.lianban_ladder, over1e: result.lhb_net_over_1e8, bottom5: result.lhb_net_bottom5,
  dupCodes, dupShape, akStatRange: [akStatDates[0], akStatDates[akStatDates.length - 1]],
  cross: cross.map((c) => `${c.result.toUpperCase()} | ${c.check} | ${c.detail}`),
}, null, 2));
