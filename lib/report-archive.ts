'use client';

import { bridgeUrl } from '@/lib/bridge-url';

export type ReportArchiveRecord = {
  id: string;
  /** Stable semantic key. A newer record with the same key replaces the old one. */
  archiveKey?: string;
  createdAt: string;
  updatedAt: string;
  date: string;
  title: string;
  reportType: string;
  generatedBy: string;
  summary: string;
  dataScope: string;
  content: Record<string, unknown>;
  raw?: string;
};

const archiveKey = 'zhangcai.report.archive.v1';
const archiveChangedEvent = 'zhangcai-report-archive-updated';

function isHarnessTaskRecord(record: ReportArchiveRecord) {
  return record?.content?.kind === 'harness-task' || record?.reportType === 'Harness任务';
}

function safeArchivePart(value: unknown) {
  return String(value || '')
    .trim()
    .replace(/[^a-zA-Z0-9._:-]+/g, '_')
    .slice(0, 160);
}

function archiveDate(value: unknown) {
  const digits = String(value || '').replace(/\D/g, '');
  return digits.length >= 8 ? digits.slice(0, 8) : safeArchivePart(value) || 'undated';
}

function cleanArchiveText(value: unknown) {
  return String(value || '')
    .replace(/3004\s+聊天研究报告/g, '聊天完整研究报告')
    .replace(/3004\s+Demo/g, '股票研究工作台')
    .replace(/3004\s+WEB\s+DEMO/g, '研究工作台')
    .replace(/3003\s+app-data\/runtime/g, '本地运行目录')
    .replace(/3003\s+app-data/g, '本地运行目录')
    .replace(/3003\s+网页脚本/g, '网页脚本')
    .replace(/3003\s+本地/g, '本地')
    .replace(/3003\s+原始/g, '原始')
    .replace(/3003(?=[\u4e00-\u9fff])/g, '')
    .replace(/3004(?=[\u4e00-\u9fffA-Za-z])/g, '')
    .trim();
}

function normalizeArchiveValue(value: unknown): unknown {
  if (typeof value === 'string') return cleanArchiveText(value);
  if (Array.isArray(value)) return value.map(normalizeArchiveValue);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, normalizeArchiveValue(item)]));
  }
  return value;
}

function normalizeReportRecord(record: ReportArchiveRecord): ReportArchiveRecord {
  return {
    ...record,
    title: cleanArchiveText(record.title),
    reportType: cleanArchiveText(record.reportType),
    generatedBy: cleanArchiveText(record.generatedBy),
    summary: cleanArchiveText(record.summary),
    dataScope: cleanArchiveText(record.dataScope),
    content: normalizeArchiveValue(record.content) as Record<string, unknown>,
    raw: typeof record.raw === 'string' ? cleanArchiveText(record.raw) : record.raw,
  };
}

/**
 * Reports are user-facing deliverables, not an append-only event log. Keep a
 * stable semantic key so rerunning the same report updates the latest result
 * instead of creating another row with a new UUID.
 */
export function getReportArchiveKey(record: ReportArchiveRecord) {
  const explicit = safeArchivePart(record?.archiveKey);
  if (explicit) {
    const dated = explicit.match(/^(chat|stock|skill14|strategy|golden|mainline|market):([^:]+):(.*)$/);
    return dated ? `${dated[1]}:${archiveDate(dated[2])}:${dated[3]}` : explicit;
  }
  const content = record?.content && typeof record.content === 'object'
    ? record.content
    : {};
  const kind = String(content.kind || '');
  const date = archiveDate(record?.date);
  const reportLabel = `${record?.title || ''} ${record?.reportType || ''}`;
  if (kind === 'market-report' || /行情复盘|历史复盘|结构化复盘|Harness 复盘/.test(reportLabel)) {
    return 'market-review';
  }
  if (kind === 'chat-report') {
    const skill = Number(content.planLength || 0) > 1
      ? 'complete-plan'
      : safeArchivePart(content.skillId || 'complete-plan');
    const targetStocks = Array.isArray(content.targetStocks) ? content.targetStocks as Array<Record<string, unknown>> : [];
    const targets = targetStocks.map((stock) => `${safeArchivePart(stock.market || 'XX')}${safeArchivePart(stock.code || stock.name || 'market')}`).sort().join('_') || 'market';
    return `chat:${date}:${targets}:${skill}`;
  }
  if (kind === 'stock-research') {
    const stock = safeArchivePart((content.stock as Record<string, unknown> | undefined)?.code || 'unknown-stock');
    const skill = safeArchivePart(record?.generatedBy || 'stock-research');
    return `stock:${date}:${stock}:${skill}`;
  }
  if (kind === 'harness-skill') {
    return `skill14:${date}:${safeArchivePart(content.skillId || record?.generatedBy || 'unknown-skill')}`;
  }
  if (kind === 'strategy-selection-harness' || kind === 'strategy-run') {
    return `strategy:${date}:${safeArchivePart(content.strategyId || record?.generatedBy || 'unknown-strategy')}`;
  }
  if (kind === 'golden-ignition-single-signal') {
    const result = content.result as Record<string, unknown> | undefined;
    return `golden:${date}:${safeArchivePart(result?.analysis_symbol || result?.symbol || 'unknown-stock')}`;
  }
  return `report:${date}:${safeArchivePart(record?.reportType || kind || record?.title || 'general')}`;
}

function reportTimestamp(value: unknown) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value < 1e12 ? value * 1000 : value;
  }
  const text = String(value || '').trim();
  if (!text) return 0;
  const numeric = Number(text);
  if (Number.isFinite(numeric) && numeric > 0) return numeric < 1e12 ? numeric * 1000 : numeric;
  const digits = text.replace(/\D/g, '');
  if (digits.length >= 14) {
    const date = Date.UTC(
      Number(digits.slice(0, 4)), Number(digits.slice(4, 6)) - 1, Number(digits.slice(6, 8)),
      Number(digits.slice(8, 10)), Number(digits.slice(10, 12)), Number(digits.slice(12, 14)),
    );
    if (Number.isFinite(date)) return date;
  }
  if (digits.length >= 8) {
    const date = Date.UTC(Number(digits.slice(0, 4)), Number(digits.slice(4, 6)) - 1, Number(digits.slice(6, 8)));
    if (Number.isFinite(date)) return date;
  }
  const parsed = Date.parse(text);
  return Number.isFinite(parsed) ? parsed : 0;
}

function collapseReportRows(records: ReportArchiveRecord[]) {
  const latest = new Map<string, ReportArchiveRecord>();
  const sorted = [...records]
    .map(normalizeReportRecord)
    .filter((record) => record && typeof record.id === 'string' && !isHarnessTaskRecord(record))
    .sort((a, b) => (
      reportTimestamp(b.updatedAt || b.createdAt) - reportTimestamp(a.updatedAt || a.createdAt)
      || String(b.id || '').localeCompare(String(a.id || ''))
    ));
  for (const record of sorted) {
    const key = getReportArchiveKey(record);
    if (!latest.has(key)) latest.set(key, { ...record, archiveKey: key });
  }
  return [...latest.values()].slice(0, 100);
}

export function createReportId(prefix = 'report') {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function')
    return `${prefix}-${crypto.randomUUID()}`;
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function loadReportArchive(): ReportArchiveRecord[] {
  if (typeof window === 'undefined') return [];
  try {
    const value = JSON.parse(localStorage.getItem(archiveKey) || '[]');
    if (!Array.isArray(value)) return [];
    const rows = collapseReportRows(value as ReportArchiveRecord[]);
    if (JSON.stringify(rows) !== JSON.stringify(value)) localStorage.setItem(archiveKey, JSON.stringify(rows));
    return rows;
  } catch {
    return [];
  }
}

const excludedIndividualStockSkillIds = new Set([
  'support-pressure-analysis-system',
  'technical-analysis',
]);

/** Keep lightweight stock-detail calculations out of the durable report list. */
export function shouldShowInMyReports(record: ReportArchiveRecord): boolean {
  const content = record.content as Record<string, unknown> | undefined;
  if (content?.kind !== 'stock-research') return true;
  const skillId = String(content.skillId || '');
  if (excludedIndividualStockSkillIds.has(skillId)) return false;
  const generatedBy = String(record.generatedBy || '');
  return !(generatedBy.startsWith('Local Daily Formula')
    && (record.reportType.includes('支撑压力分析系统') || record.reportType.includes('技术分析')));
}

export async function saveReportArchive(record: ReportArchiveRecord): Promise<void> {
  if (typeof window === 'undefined') return;
  const normalized = { ...record, archiveKey: getReportArchiveKey(record) };
  const rows = loadReportArchive().filter((item) => item.id !== normalized.id);
  localStorage.setItem(archiveKey, JSON.stringify(collapseReportRows([normalized, ...rows])));
  window.dispatchEvent(new Event(archiveChangedEvent));
  // Write the browser cache first so the report is immediately visible, then
  // wait for the canonical EXE/web bridge copy. Waiting prevents a following
  // refresh from reading the old index and overwriting the newly generated row.
  try {
    const response = await fetch(bridgeUrl('/reports/archive'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(normalized),
    });
    if (!response.ok) throw new Error(`报告归档服务返回 ${response.status}`);
  } catch {
    // The local cache remains usable; the next archive sync retries it.
  }
}

export function deleteArchivedReport(id: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(
    archiveKey,
    JSON.stringify(loadReportArchive().filter((item) => item.id !== id)),
  );
  void fetch(`${bridgeUrl('/reports/archive')}/${encodeURIComponent(id)}`, { method: 'DELETE' }).catch(() => {});
  window.dispatchEvent(new Event(archiveChangedEvent));
}

export async function loadReportArchiveFromLocalRuntime(): Promise<ReportArchiveRecord[]> {
  if (typeof window === 'undefined') return [];
  const cached = loadReportArchive();
  try {
    const response = await fetch(bridgeUrl('/reports/archive'), { cache: 'no-store' });
    if (!response.ok) return cached;
    const body = await response.json() as { reports?: ReportArchiveRecord[] };
    const serverReports = Array.isArray(body.reports) ? body.reports : [];
    // Keep locally-created rows while the bridge index catches up. This also
    // makes the migration path safe when a report was generated just before a
    // page refresh or when the bridge was briefly restarting.
    const reports = collapseReportRows([...cached, ...serverReports]);
    const serverIds = new Set(serverReports.map((record) => record?.id));
    const pending = cached.filter((record) => !serverIds.has(record.id));
    if (pending.length) {
      await Promise.all(pending.slice(0, 100).map((record) => fetch(bridgeUrl('/reports/archive'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(record),
      }).catch(() => null)));
    }
    if (reports.length) localStorage.setItem(archiveKey, JSON.stringify(reports));
    return reports;
  } catch {
    return cached;
  }
}

export const reportArchiveChangedEvent = archiveChangedEvent;
