// Read-only equivalent of scripts/public_market_sync.py for environments without Python.
// Saves byte-exact raw snapshots + a metadata wrapper per source, then a combined snapshot.
import { createHash } from 'node:crypto';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';

const ROOT = resolve(process.argv[2] ?? 'C:/work/260907 掌财智能体/CodeX-st-wsp/zhangcai-demo');
const DATE = process.argv[3] ?? '2026-09-10';
const COMPACT = DATE.replace(/-/g, '');
const PUB = join(ROOT, 'data', 'public');
const dayDir = join(PUB, COMPACT);
mkdirSync(dayDir, { recursive: true });

const lhbQuery = new URLSearchParams({
  sortColumns: 'SECURITY_CODE,TRADE_DATE', sortTypes: '1,-1', pageSize: '5000', pageNumber: '1',
  reportName: 'RPT_DAILYBILLBOARD_DETAILSNEW',
  columns: 'SECURITY_CODE,SECURITY_NAME_ABBR,TRADE_DATE,BILLBOARD_NET_AMT,BILLBOARD_BUY_AMT,BILLBOARD_SELL_AMT,EXPLAIN',
  source: 'WEB', client: 'WEB', filter: `(TRADE_DATE<='${DATE}')(TRADE_DATE>='${DATE}')`,
});
const ztQuery = new URLSearchParams({
  ut: '7eea3edcaed734bea9cbfc24409ed989', dpt: 'wz.ztzt', Pageindex: '0', pagesize: '10000',
  sort: 'fbt:asc', date: COMPACT,
});
const jobs = {
  lianban: `https://lianban.net/opendata/${DATE}.json`,
  eastmoneyLimitUp: `https://push2ex.eastmoney.com/getTopicZTPool?${ztQuery}`,
  eastmoneyLhb: `https://datacenter-web.eastmoney.com/api/data/v1/get?${lhbQuery}`,
};

const now = new Date();
const stamp = now.toTimeString().slice(0, 8).replace(/:/g, '');
const sources = {};

for (const [name, url] of Object.entries(jobs)) {
  const fetchedAt = new Date().toISOString();
  try {
    const resp = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0 (ZhangcaiAgent/1.0)', Accept: 'application/json,text/plain,*/*' }, signal: AbortSignal.timeout(30000) });
    const buf = Buffer.from(await resp.arrayBuffer());
    const sha256 = createHash('sha256').update(buf).digest('hex');
    const rawPath = join(dayDir, `${name}-${stamp}.raw.json`);
    writeFileSync(rawPath, buf);
    let parsed = null; let parseError = null;
    try { parsed = JSON.parse(buf.toString('utf8').replace(/^\uFEFF/, '')); } catch (e) { parseError = String(e); }
    sources[name] = {
      source_name: name, source_url: url, trade_date: DATE, fetched_at: fetchedAt,
      http_status: resp.status, content_type: resp.headers.get('content-type'),
      sha256, bytes: buf.length, status: resp.ok ? 'available' : 'missing',
      raw_path: `data/public/${COMPACT}/${name}-${stamp}.raw.json`,
      parse_error: parseError, data: parsed,
    };
    console.log(`${name} => HTTP ${resp.status} bytes=${buf.length} sha256=${sha256.slice(0, 12)} parse=${parseError ? 'FAIL' : 'ok'}`);
  } catch (err) {
    sources[name] = { source_name: name, source_url: url, trade_date: DATE, fetched_at: fetchedAt, status: 'missing', error: `${err?.name}: ${err?.message}` };
    console.log(`${name} => ERROR ${err?.name}: ${err?.message}`);
  }
}

const combined = { schema: 'ZHANGCAI_PUBLIC_MARKET_V1', date: DATE, fetchedAt: now.toISOString(), collector: 'public_market_sync_node.mjs (python unavailable)', sources };
const combinedPath = join(dayDir, `market-${stamp}.json`);
writeFileSync(combinedPath, JSON.stringify(combined, null, 2), 'utf8');
console.log(`COMBINED=${combinedPath}`);
