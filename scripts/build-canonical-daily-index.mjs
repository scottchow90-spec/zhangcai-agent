import { createReadStream, statSync } from 'node:fs';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

const [sourceFileArg, outputFileArg] = process.argv.slice(2);
if (!sourceFileArg || !outputFileArg) {
  console.error('usage: node build-canonical-daily-index.mjs <canonical-jsonl> <index-json>');
  process.exit(2);
}

const sourceFile = path.resolve(sourceFileArg);
const outputFile = path.resolve(outputFileArg);
const source = statSync(sourceFile);
const symbols = {};
let recordCount = 0;

function normalizeSymbol(value) {
  const raw = String(value || '').trim().toLowerCase().replace(/\s+/g, '');
  const code = raw.match(/\d{6}/)?.[0] || '';
  const marketMatch = raw.match(/^(sh|sz|bj)|\.(sh|sz|bj)(?:$|\.)/);
  const market = marketMatch?.[1] || marketMatch?.[2] || '';
  if (!market || !code) return null;
  return { key: `${market}${code}`, symbol: `${code}.${market.toUpperCase()}`, market: market.toUpperCase(), code };
}

function dateText(value) {
  const raw = String(value || '').replace(/\D/g, '');
  return /^\d{8}$/.test(raw) ? `${raw.slice(0, 4)}-${raw.slice(4, 6)}-${raw.slice(6)}` : String(value || '');
}

async function scanLines(onLine) {
  const stream = createReadStream(sourceFile, { highWaterMark: 1024 * 1024 });
  let pending = Buffer.alloc(0);
  let pendingOffset = 0;
  for await (const chunk of stream) {
    const current = pending.length ? Buffer.concat([pending, chunk]) : chunk;
    let cursor = 0;
    while (true) {
      const newline = current.indexOf(0x0a, cursor);
      if (newline < 0) break;
      await onLine(current.subarray(cursor, newline), pendingOffset + cursor);
      cursor = newline + 1;
    }
    pendingOffset += cursor;
    pending = current.subarray(cursor);
  }
  if (pending.length) await onLine(pending, pendingOffset);
}

await scanLines(async (line, offset) => {
  const text = line.toString('utf8').replace(/\r$/, '').trim();
  if (!text) return;
  let value;
  try { value = JSON.parse(text); } catch { return; }
  const normalized = normalizeSymbol(value?.market ? `${value.symbol}.${value.market}` : value?.symbol);
  if (!normalized) return;
  const date = dateText(value.date);
  const endOffset = offset + line.length + 1;
  const existing = symbols[normalized.key];
  if (!existing) {
    symbols[normalized.key] = {
      symbol: normalized.symbol,
      code: normalized.code,
      market: normalized.market,
      start_offset: offset,
      end_offset: endOffset,
      record_count: 1,
      first_date: date,
      last_date: date,
    };
  } else {
    existing.start_offset = Math.min(Number(existing.start_offset || offset), offset);
    existing.end_offset = Math.max(Number(existing.end_offset || endOffset), endOffset);
    existing.record_count = Number(existing.record_count || 0) + 1;
    if (date && (!existing.first_date || date < existing.first_date)) existing.first_date = date;
    if (date && (!existing.last_date || date > existing.last_date)) existing.last_date = date;
  }
  recordCount += 1;
});

if (!Object.keys(symbols).length) throw new Error(`canonical 日线归档没有可索引的股票记录：${sourceFile}`);
const value = {
  schema: 'ZHANGCAI_CANONICAL_DAILY_SYMBOL_INDEX_V1',
  generated_at: new Date().toISOString(),
  source_file: sourceFile,
  source_size: source.size,
  source_mtime_ms: source.mtimeMs,
  source_kind: 'Packaged canonical daily JSONL · byte-range lookup',
  symbol_count: Object.keys(symbols).length,
  record_count: recordCount,
  symbols,
};
await mkdir(path.dirname(outputFile), { recursive: true });
await writeFile(outputFile, JSON.stringify(value, null, 2), 'utf8');
console.log(JSON.stringify({ status: 'PASS', sourceFile, outputFile, symbolCount: value.symbol_count, recordCount: value.record_count, sourceBytes: source.size }));
