const fs = require('fs');
const p = 'C:\\work\\260907 掌财智能体\\CodeX-st-wsp\\zhangcai-web-3003\\app-data\\harness\\tasks\\task-ea541557-3843-45ed-832e-36367a4e2628.txt';
const t = fs.readFileSync(p, 'utf8');

function sliceArr(startIdx) {
  const open = t.indexOf('[', startIdx);
  let depth = 0, inStr = false, esc = false;
  for (let i = open; i < t.length; i++) {
    const c = t[i];
    if (inStr) {
      if (esc) { esc = false; continue; }
      if (c === '\\') { esc = true; continue; }
      if (c === '"') inStr = false;
      continue;
    }
    if (c === '"') { inStr = true; continue; }
    if (c === '[') depth++;
    else if (c === ']') { depth--; if (depth === 0) return t.slice(open, i + 1); }
  }
  return null;
}

const secs = {};
for (const name of ['涨幅领先候选', '成交额领先候选', '跌幅/负反馈候选', '跌停阈值候选', 'TDX行业板块聚合', 'TDX主题板块聚合', '涨停/连板候选', '主线名称聚类候选']) {
  const i = t.indexOf(name + '：[');
  if (i < 0) { secs[name] = null; continue; }
  const s = sliceArr(i);
  try { secs[name] = JSON.parse(s); } catch (e) { secs[name] = 'PARSE_ERR:' + e.message + ' len=' + (s ? s.length : 0); }
}

// target + history
const hi = t.indexOf('{"targetStock"');
const hs = t.lastIndexOf('"history":');
function braceBlock(start) {
  let depth = 0, inStr = false, esc = false;
  for (let i = start; i < t.length; i++) {
    const c = t[i];
    if (inStr) { if (esc) { esc = false; continue; } if (c === '\\') { esc = true; continue; } if (c === '"') inStr = false; continue; }
    if (c === '"') { inStr = true; continue; }
    if (c === '{') depth++; else if (c === '}') { depth--; if (depth === 0) return t.slice(start, i + 1); }
  }
  return null;
}
const target = JSON.parse(braceBlock(hi));
const hOpen = t.indexOf('[', hs);
let depth = 0, inStr = false, esc = false, hEnd = -1;
for (let i = hOpen; i < t.length; i++) {
  const c = t[i];
  if (inStr) { if (esc) { esc = false; continue; } if (c === '\\') { esc = true; continue; } if (c === '"') inStr = false; continue; }
  if (c === '"') { inStr = true; continue; }
  if (c === '[') depth++; else if (c === ']') { depth--; if (depth === 0) { hEnd = i; break; } }
}
const history = JSON.parse(t.slice(hOpen, hEnd + 1));
const metaIdx = t.indexOf('"historyMeta":', hEnd) >= 0 ? t.indexOf('{', t.indexOf('"historyMeta":', hEnd)) : -1;
const historyMeta = metaIdx >= 0 ? JSON.parse(braceBlock(metaIdx)) : null;

const out = [];
const log = (...a) => out.push(a.map(x => typeof x === 'string' ? x : JSON.stringify(x)).join(' '));

log('=== TARGET ===');
log(JSON.stringify(target, null, 1));
log('=== HISTORY META ===');
log(JSON.stringify(historyMeta, null, 1));
log('=== SECTIONS (counts) ===');
for (const k in secs) log(k, Array.isArray(secs[k]) ? secs[k].length : String(secs[k]).slice(0, 120));

const C = history.map(b => b.close), H = history.map(b => b.high), L = history.map(b => b.low), O = history.map(b => b.open), V = history.map(b => b.volume), A = history.map(b => b.amount), D = history.map(b => b.date);
const n = C.length;
const sma = (arr, k, i) => { if (i - k + 1 < 0) return null; let s = 0; for (let j = i - k + 1; j <= i; j++) s += arr[j]; return s / k; };
const last = n - 1;
const r = (x, d = 3) => x === null || x === undefined || !isFinite(x) ? null : Number(x.toFixed(d));

function ret(days) { const i = last - days; return i < 0 ? null : r((C[last] / C[i] - 1) * 100, 2); }

// volatility
function vol(k) {
  const rs = [];
  for (let i = last - k + 1; i <= last; i++) { if (i < 1) continue; rs.push(C[i] / C[i - 1] - 1); }
  const m = rs.reduce((a, b) => a + b, 0) / rs.length;
  const v = Math.sqrt(rs.reduce((a, b) => a + (b - m) ** 2, 0) / (rs.length - 1));
  return { daily: r(v * 100, 2), annual: r(v * Math.sqrt(244) * 100, 2), n: rs.length };
}

// RSI14
function rsi(k) {
  let g = 0, l = 0;
  for (let i = last - k + 1; i <= last; i++) { const d = C[i] - C[i - 1]; if (d > 0) g += d; else l -= d; }
  const ag = g / k, al = l / k;
  if (al === 0) return 100;
  return r(100 - 100 / (1 + ag / al), 2);
}

// MACD
function ema(arr, k) { const a = 2 / (k + 1); let e = arr[0]; const o = [e]; for (let i = 1; i < arr.length; i++) { e = arr[i] * a + e * (1 - a); o.push(e); } return o; }
const e12 = ema(C, 12), e26 = ema(C, 26);
const dif = C.map((_, i) => e12[i] - e26[i]);
const dea = ema(dif, 9);
const macd = dif.map((d, i) => (d - dea[i]) * 2);

// ATR14
let trs = [];
for (let i = last - 13; i <= last; i++) trs.push(Math.max(H[i] - L[i], Math.abs(H[i] - C[i - 1]), Math.abs(L[i] - C[i - 1])));
const atr14 = trs.reduce((a, b) => a + b, 0) / 14;

// 52w / ranges
function hiLo(k) { const s = Math.max(0, last - k + 1); let hh = -Infinity, ll = Infinity, hiD = '', loD = ''; for (let i = s; i <= last; i++) { if (H[i] > hh) { hh = H[i]; hiD = D[i]; } if (L[i] < ll) { ll = L[i]; loD = D[i]; } } return { high: hh, highDate: hiD, low: ll, lowDate: loD, n: last - s + 1 }; }
const r250 = hiLo(250), r120 = hiLo(120), r60 = hiLo(60), r20 = hiLo(20), rAll = hiLo(n);

// limit up/down detection (limitPct 20 for 创业板)
const lim = (target.limitPct || 20) / 100;
function limitStats(k) {
  const s = Math.max(1, last - k + 1); let lu = 0, ld = 0; const days = [];
  for (let i = s; i <= last; i++) { const ch = C[i] / C[i - 1] - 1; if (ch >= lim - 0.005) { lu++; days.push([D[i], '涨停', r(ch * 100, 2)]); } if (ch <= -(lim - 0.005)) { ld++; days.push([D[i], '跌停', r(ch * 100, 2)]); } }
  return { window: k, limitUp: lu, limitDown: ld, days };
}

// streaks
let upStreak = 0, downStreak = 0;
for (let i = last; i > 0; i--) { const ch = C[i] - C[i - 1]; if (ch > 0) { if (downStreak) break; upStreak++; } else if (ch < 0) { if (upStreak) break; downStreak++; } else break; }

log('=== PRICE / INDICATORS (as of last bar) ===');
log(JSON.stringify({
  lastDate: D[last], lastClose: C[last], prevClose: C[last - 1],
  lastBar: history[last],
  pctVsPrev: r((C[last] / C[last - 1] - 1) * 100, 2),
  ma: { ma5: r(sma(C, 5, last)), ma10: r(sma(C, 10, last)), ma20: r(sma(C, 20, last)), ma60: r(sma(C, 60, last)), ma120: r(sma(C, 120, last)), ma250: r(sma(C, 250, last)), ma500: r(sma(C, 500, last)) },
  volMa: { v5: r(sma(V, 5, last), 0), v10: r(sma(V, 10, last), 0), v20: r(sma(V, 20, last), 0), v60: r(sma(V, 60, last), 0), last: V[last], ratio5: r(V[last] / sma(V, 5, last), 2), ratio20: r(V[last] / sma(V, 20, last), 2) },
  amount: { last: A[last], ma5: r(sma(A, 5, last), 0), ma20: r(sma(A, 20, last), 0), ma60: r(sma(A, 60, last), 0), maxAll: Math.max(...A), maxAllDate: D[A.indexOf(Math.max(...A))] },
  returns: { d1: ret(1), d5: ret(5), d10: ret(10), d20: ret(20), d60: ret(60), d120: ret(120), d250: ret(250), sinceStart: r((C[last] / C[0] - 1) * 100, 2) },
  vol: { v20: vol(20), v60: vol(60) },
  rsi14: rsi(14), rsi6: rsi(6),
  macd: { dif: r(dif[last], 3), dea: r(dea[last], 3), macd: r(macd[last], 3), difPrev: r(dif[last - 1], 3), deaPrev: r(dea[last - 1], 3) },
  atr14: r(atr14, 3), atr14Pct: r(atr14 / C[last] * 100, 2),
  ranges: { r20, r60, r120, r250, rAll, fromAllHigh: r((C[last] / rAll.high - 1) * 100, 2), from250High: r((C[last] / r250.high - 1) * 100, 2), from250Low: r((C[last] / r250.low - 1) * 100, 2), pos250: r((C[last] - r250.low) / (r250.high - r250.low) * 100, 1) },
  streaks: { up: upStreak, down: downStreak },
  limit20d: limitStats(20), limit60d: limitStats(60), limit250d: limitStats(250),
  maxDrawdown250: (() => { let peak = -Infinity, mdd = 0, pd = '', td = ''; const s = Math.max(0, last - 249); for (let i = s; i <= last; i++) { if (C[i] > peak) { peak = C[i]; pd = D[i]; } const dd = C[i] / peak - 1; if (dd < mdd) { mdd = dd; td = D[i]; } } return { mdd: r(mdd * 100, 2), peakDate: pd, troughDate: td }; })(),
}, null, 1));

log('=== LAST 40 BARS ===');
log('date,open,high,low,close,chg%,amount,vol,ma5,ma10,ma20,ma60');
for (let i = Math.max(0, n - 40); i < n; i++) {
  log([D[i], O[i], H[i], L[i], C[i], r((C[i] / C[i - 1] - 1) * 100, 2), A[i], V[i], r(sma(C, 5, i), 2), r(sma(C, 10, i), 2), r(sma(C, 20, i), 2), r(sma(C, 60, i), 2)].join(','));
}

log('=== MONTHLY CLOSES (last 24 months) ===');
const byMonth = {};
for (let i = 0; i < n; i++) { const m = D[i].slice(0, 7); if (!byMonth[m]) byMonth[m] = { first: C[i], last: C[i], high: H[i], low: L[i], amount: 0, vol: 0 }; byMonth[m].last = C[i]; byMonth[m].high = Math.max(byMonth[m].high, H[i]); byMonth[m].low = Math.min(byMonth[m].low, L[i]); byMonth[m].amount += A[i]; byMonth[m].vol += V[i]; }
const mk = Object.keys(byMonth).sort();
for (const m of mk.slice(-24)) { const b = byMonth[m]; log(m, 'close=' + b.last, 'high=' + b.high, 'low=' + b.low, 'chg%=' + r((b.last / b.first - 1) * 100, 2), 'amt=' + b.amount); }

log('=== YEARLY ===');
const byYear = {};
for (let i = 0; i < n; i++) { const y = D[i].slice(0, 4); if (!byYear[y]) byYear[y] = { first: C[i], last: C[i], high: H[i], low: L[i], amount: 0, days: 0 }; byYear[y].last = C[i]; byYear[y].high = Math.max(byYear[y].high, H[i]); byYear[y].low = Math.min(byYear[y].low, L[i]); byYear[y].amount += A[i]; byYear[y].days++; }
for (const y of Object.keys(byYear).sort()) { const b = byYear[y]; log(y, 'close=' + b.last, 'high=' + b.high, 'low=' + b.low, 'chg%=' + r((b.last / b.first - 1) * 100, 2), 'amtSum=' + b.amount, 'days=' + b.days); }

log('=== ALL SECTIONS JSON ===');
for (const k in secs) { log('--- ' + k + ' ---'); log(JSON.stringify(secs[k])); }

fs.writeFileSync('C:\\work\\260907 掌财智能体\\CodeX-st-wsp\\zhangcai-web-3003\\app-data\\harness\\tmp\\analyze_out.txt', out.join('\n'), 'utf8');
console.log('OK lines=' + out.length);
