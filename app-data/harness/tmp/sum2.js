const fs = require('fs');
const p = 'C:\\work\\260907 掌财智能体\\CodeX-st-wsp\\zhangcai-web-3003\\app-data\\harness\\tasks\\task-ea541557-3843-45ed-832e-36367a4e2628.txt';
const t = fs.readFileSync(p, 'utf8');

function sliceArrAt(startIdx) {
  const open = t.indexOf('[', startIdx);
  let depth = 0, inStr = false, esc = false;
  for (let i = open; i < t.length; i++) {
    const c = t[i];
    if (inStr) { if (esc) { esc = false; continue; } if (c === '\\') { esc = true; continue; } if (c === '"') inStr = false; continue; }
    if (c === '"') { inStr = true; continue; }
    if (c === '[') depth++; else if (c === ']') { depth--; if (depth === 0) return t.slice(open, i + 1); }
  }
  return null;
}
function sec(name) {
  const i = t.indexOf(name + '：[');
  if (i < 0) return null;
  try { return JSON.parse(sliceArrAt(i)); } catch (e) { return 'ERR ' + e.message; }
}
const out = [];
const log = (...a) => out.push(a.map(x => typeof x === 'string' ? x : JSON.stringify(x)).join(' '));

const TARGET = '300959';
const ind = sec('TDX行业板块聚合'), thm = sec('TDX主题板块聚合'), lu = sec('涨停/连板候选');
const gain = sec('涨幅领先候选'), amt = sec('成交额领先候选'), lose = sec('跌幅/负反馈候选'), dt = sec('跌停阈值候选');

log('### TARGET PRESENCE SCAN');
function scan(label, arr) {
  if (!Array.isArray(arr)) { log(label, 'N/A'); return; }
  const hit = arr.filter(x => x.code === TARGET);
  log(label, 'len=' + arr.length, 'targetHit=' + JSON.stringify(hit));
  // leaders deep scan
  const inLeader = [];
  for (const g of arr) if (Array.isArray(g.leaders)) for (const l of g.leaders) if (l.code === TARGET) inLeader.push(g.name + '/' + g.code + ' rank=' + (g.leaders.indexOf(l) + 1));
  if (inLeader.length) log('  leaderHit:', JSON.stringify(inLeader));
}
scan('涨幅', gain); scan('成交额', amt); scan('跌幅', lose); scan('跌停阈值', dt);
scan('行业', ind); scan('主题', thm); scan('涨停连板', lu);

log('');
log('### TDX 行业板块聚合 (sorted avgPct desc, fields: name|count|avgPct|amount|up|down|limitCount|top3)');
const indSorted = (Array.isArray(ind) ? ind.slice() : []).sort((a, b) => b.avgPct - a.avgPct);
log('total=' + indSorted.length);
for (const g of indSorted) {
  log([g.code, g.name, g.count, g.avgPct, g.amount, g.up + '/' + g.down + '/' + g.flat, 'lim=' + g.limitCount,
    (g.leaders || []).slice(0, 3).map(l => l.name + ' ' + l.pct + '%').join(' ; ')].join(' | '));
}

log('');
log('### TDX 主题板块聚合 (sorted avgPct desc, top 15, fields: code|name|count/declared|avgPct|amount|up/down|lim|top3)');
const thmSorted = (Array.isArray(thm) ? thm.slice() : []).sort((a, b) => b.avgPct - a.avgPct);
log('total=' + thmSorted.length);
for (const g of thmSorted.slice(0, 15)) {
  log([g.code, g.name, g.count + '/' + (g.declaredCount || '-'), g.avgPct, g.amount, g.up + '/' + g.down + '/' + g.flat, 'lim=' + g.limitCount, 'upd=' + (g.updatedDate || '-'),
    (g.leaders || []).slice(0, 3).map(l => l.name + ' ' + l.pct + '%').join(' ; ')].join(' | '));
}
log('--- 主题 full name list ---');
log(thmSorted.map(g => g.name + '(' + g.avgPct + '%)').join(', '));
log('--- 行业 full name list ---');
log(indSorted.map(g => g.name + '(' + g.avgPct + '%)').join(', '));

log('');
log('### 涨停/连板候选 full (code|name|pct|limitPct|streak|amount)');
const luSorted = (Array.isArray(lu) ? lu.slice() : []).sort((a, b) => (b.streak || 0) - (a.streak || 0) || b.amount - a.amount);
log('total=' + luSorted.length);
for (const x of luSorted) log([x.code, x.name, x.pct, x.limitPct, x.streak, x.amount].join(' | '));

log('');
log('### 涨幅领先候选 full');
for (const x of (gain || [])) log([x.code, x.name, x.pct, x.amount, x.close, x.market].join(' | '));
log('### 成交额领先候选 full');
for (const x of (amt || [])) log([x.code, x.name, x.pct, x.amount, x.close].join(' | '));
log('### 跌幅/负反馈候选 full');
for (const x of (lose || [])) log([x.code, x.name, x.pct, x.amount, x.close].join(' | '));
log('### 跌停阈值候选 full');
for (const x of (dt || [])) log([x.code, x.name, x.pct, x.limitPct, x.amount].join(' | '));

log('');
log('### PLAIN TEXT BETWEEN SECTIONS (non-JSON narrative)');
const idxLU = t.indexOf('涨停/连板候选：[', 0);
const idxMain = t.indexOf('主线名称聚类候选：[', 0);
const tailEnd = idxMain + sliceArrAt(idxMain).length;
log(t.slice(tailEnd, 72200));

fs.writeFileSync('C:\\work\\260907 掌财智能体\\CodeX-st-wsp\\zhangcai-web-3003\\app-data\\harness\\tmp\\sum2.txt', out.join('\n'), 'utf8');
console.log('OK');
