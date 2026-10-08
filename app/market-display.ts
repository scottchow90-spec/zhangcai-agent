/**
 * 日期与价格展示的单一入口。
 *
 * 行情日期来自本地可核验的日线归档，不使用系统当前日期补齐。这样当
 * 通达信最后一条日线仍是上一个交易日时，界面会明确告诉用户价格是哪一
 * 天的收盘价，而不会把它误称为“最新价”。
 */
export function normalizeTradingDate(value: unknown): string {
  const raw = String(value ?? '').trim();
  if (!raw) return '';

  const match = raw.match(/(\d{4})\D?(\d{2})\D?(\d{2})/);
  if (match) return `${match[1]}-${match[2]}-${match[3]}`;

  const digits = raw.replace(/\D/g, '');
  if (digits.length >= 8) {
    return `${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6, 8)}`;
  }
  return raw;
}

export function dateLabel(value: unknown): string {
  return normalizeTradingDate(value) || '—';
}

export function closeDateLabel(value: unknown): string {
  const normalized = normalizeTradingDate(value);
  const match = normalized.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return '最近可核验交易日收盘价格';
  return `${Number(match[2])}月${Number(match[3])}日收盘价格`;
}

export function closePriceLabel(value: unknown, date: unknown): string {
  const numeric = Number(value);
  const formatted = Number.isFinite(numeric) ? numeric.toFixed(2) : '—';
  return `${closeDateLabel(date)}：${formatted}`;
}
