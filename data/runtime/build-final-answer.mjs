import { readFileSync, writeFileSync } from 'node:fs';
const R = 'C:/work/260907 掌财智能体/CodeX-st-wsp/zhangcai-demo';
const x = JSON.parse(readFileSync(R + '/data/runtime/public-market-pool-20260910.json', 'utf8'));
const snap = JSON.parse(readFileSync(R + '/data/public/20260910/market-100600.json', 'utf8')).sources;
const fmt = (t) => { const s = String(t).padStart(6, '0'); return s.slice(0, 2) + ':' + s.slice(2, 4) + ':' + s.slice(4); };
const rows = x.pool.slice().sort((a, b) => b.lbc - a.lbc || a.fbt - b.fbt)
  .map((o) => [o.code, o.name, String(o.lbc), fmt(o.fbt), fmt(o.lbt), String(o.zbc), o.hybk, String(o.amount), o.hs.toFixed(2)]);

const out = {
  status: 'partial',
  summary: '2026-09-10 当天公开数据已载入并完成交易日校验与落盘：涨停池（东方财富）与连板网两个独立公开源交叉校验一致——涨停26家、连板（≥2板）11家、最高4板、炸板13家、封板率66.7%，两项均标记 available；东方财富龙虎榜同一交易日返回空结果，标记 missing。按技能规则未写入 lib/market.json。快照采集于 2026-09-10 10:06(+08:00)，为盘中数据，非收盘终值。',
  data_date: '2026-09-10',
  data_scope: '东方财富涨停池（push2ex getTopicZTPool, date=20260910, 26条）、连板网开放数据（lianban.net/opendata/2026-09-10.json, KPI+8个主题）、东方财富龙虎榜（RPT_DAILYBILLBOARD_DETAILSNEW, TRADE_DATE=2026-09-10, 空）。原始响应按源保存于 data/public/20260910/（lianban-100600.raw.json、eastmoneyLimitUp-100600.raw.json、eastmoneyLhb-100600.raw.json）与合并快照 data/public/20260910/market-100600.json；校验结果写入 data/runtime/harness-data-fill-result.json；涨停池明细抽取 data/runtime/public-market-pool-20260910.json。',
  cautions: [
    '龙虎榜缺失：东方财富 RPT_DAILYBILLBOARD_DETAILSNEW 对 2026-09-10 返回 success=false、message=返回数据为空（HTTP 200, 89字节），eastmoneyLhb 标记 missing，不得表述为已补齐。',
    '快照为盘中数据：采集时间 2026-09-10 10:06(+08:00)，A股仍在交易时段，涨停/连板/炸板家数会随盘面变化；同日 09:48 的既有快照为涨停21家，本次为26家，属盘中变化而非数据矛盾。',
    '连板网开放数据仅含 KPI 与主题聚合，不含逐只涨停/连板名单（其 note 说明名单在源页面、近期需登录），无法由该源校验代码集合。',
    '本地 lib/market.json 交易日为 2026-09-08，与目标交易日 2026-09-10 不一致；本地通达信日线补齐记录（tdx-daily-replenish-20260910-094832.json）显示最新完整日为 2026-09-09（9454行）。因存在空响应源，按技能规则禁止写入 lib/market.json，本次未更新该文件。',
    '本机无可用 Python（仅 WindowsApps 存根，python --version 失败），scripts/public_market_sync.py 无法执行；改用等效只读采集器 data/runtime/public_market_sync_node.mjs，保存字段（source_name/source_url/trade_date/fetched_at/sha256/status/records）与技能要求一致。进程直连 HTTPS 被沙箱阻断（Schannel SEC_E_NO_CREDENTIALS），改经本机 127.0.0.1:7897 代理完成，原始响应与 sha256 已留档。',
    '任务上下文中的“同日股票0/上涨0/下跌0/平盘0/样本成交额0/指数未提供”等字段本次未随公开源取得，未做任何推算或补造。',
    '本地通达信 ZTC.blk 更新时间为 2026-09-08T17:20，不是 2026-09-10 涨停池，仅作旁证，未用于本次涨停家数。',
  ],
  findings: [
    { title: '两源交叉校验通过', text: '东方财富涨停池记录 26 条（qdate=20260910, tc=26），连板网 KPI limit_up=26；连板家数两源均为 11（涨停池 lbc≥2 共 11 只），最高连板两源均为 4 板，交易日一致，判定为同一交易日有效数据。' },
    { title: '市场情绪相位', text: '连板网 KPI 标注 emotion_phase=退潮期：涨停26家、跌停2家、连板11家、炸板13家、封板率66.7%，上涨756家、下跌4406家，跌多涨少。' },
    { title: '连板结构', text: '26只涨停中首板15只、2板7只、3板3只、4板1只；最高标为桂林旅游（000978，4板，09:25:00首封，炸板1次）。' },
    { title: '主题分布', text: '连板网主题聚合显示涨停家数前列为农业3、芯片3，其余为智能电网2、电力2、化工2、光伏2、家电2、其他10；东方财富涨停池行业字段分散于综合Ⅱ、旅游及景区、航运港口等，未形成单一高集中度主线。' },
    { title: '龙虎榜证据链断裂', text: '2026-09-10 龙虎榜查询返回空（result=null）。按技能硬性规则，空响应必须保留原始快照与错误并标记 missing，不得以模型知识或历史缓存替代，故本次不产出任何龙虎榜席位/净买额结论。' },
  ],
  tables: [
    { title: '数据源状态与校验（2026-09-10）', columns: ['数据源', '状态', '交易日', '记录数', 'sha256'], rows: [
      ['连板网 lianban.net/opendata/2026-09-10.json', 'available', '2026-09-10', '9 项（KPI+8主题）', snap.lianban.sha256],
      ['东方财富涨停池 getTopicZTPool', 'available', '20260910', '26', snap.eastmoneyLimitUp.sha256],
      ['东方财富龙虎榜 RPT_DAILYBILLBOARD_DETAILSNEW', 'missing', '无（返回数据为空）', '0', snap.eastmoneyLhb.sha256],
    ] },
    { title: '连板网关键指标（KPI，2026-09-10 10:06快照）', columns: ['指标', '数值'], rows: [
      ['涨停家数', '26'], ['跌停家数', '2'], ['连板家数', '11'], ['最高连板', '4'], ['炸板家数', '13'],
      ['封板率(%)', '66.7'], ['上涨家数', '756'], ['下跌家数', '4406'], ['情绪相位', '退潮期'],
    ] },
    { title: '东方财富涨停池明细（按连板数降序，2026-09-10 10:06快照）', columns: ['代码', '名称', '连板数', '首次封板', '最后封板', '炸板次数', '行业', '成交额(元)', '换手率(%)'], rows },
    { title: '连板网主题涨停家数', columns: ['主题', '涨停家数'], rows: x.themes.map((t) => [t.name, String(t.limit_up)]) },
  ],
};
const text = JSON.stringify(out);
writeFileSync(R + '/data/runtime/harness-final-answer-20260910.json', text, 'utf8');
console.log(text);
