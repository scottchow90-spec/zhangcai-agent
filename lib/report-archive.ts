'use client';

import { bridgeUrl } from '@/lib/bridge-url';

export type ReportArchiveRecord = {
  id: string;
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

// A report slot identifies one logical report on the current webpage. A new
// run for the same skill/strategy/stock and data date replaces the old row,
// even when the model produces different text.
function reportSlot(record: ReportArchiveRecord) {
  const content = record.content || {};
  const kind = String(content.kind || record.reportType || 'report');
  let subject = String(record.title || record.reportType || 'report');
  if (kind === 'harness-skill') subject = String(content.skillId || subject);
  else if (kind === 'strategy-selection-harness' || kind === 'strategy-run') subject = String(content.strategyId || subject);
  else if (kind === 'stock-research') {
    const stock = content.stock && typeof content.stock === 'object' ? content.stock as Record<string, unknown> : {};
    subject = `${String(stock.code || '')}|${record.reportType || subject}`;
  }
  return `${String(record.date || '')}|${kind}|${subject}`;
}

function collapseReportRows(records: ReportArchiveRecord[]) {
  const seen = new Set<string>();
  return [...records]
    .filter((record) => record && typeof record.id === 'string' && !isHarnessTaskRecord(record))
    .sort((a, b) => String(b.updatedAt || '').localeCompare(String(a.updatedAt || '')))
    .filter((record) => {
      const slot = reportSlot(record);
      if (seen.has(slot)) return false;
      seen.add(slot);
      return true;
    })
    .slice(0, 100);
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
    return Array.isArray(value) ? collapseReportRows(value as ReportArchiveRecord[]) : [];
  } catch {
    return [];
  }
}

export function saveReportArchive(record: ReportArchiveRecord) {
  if (typeof window === 'undefined') return;
  const slot = reportSlot(record);
  const rows = loadReportArchive().filter((item) => item.id !== record.id && reportSlot(item) !== slot);
  localStorage.setItem(archiveKey, JSON.stringify(collapseReportRows([record, ...rows])));
  // localStorage keeps the page responsive, while the bridge is the
  // canonical EXE-friendly copy under 3003/app-data/reports/archive.
  void fetch(bridgeUrl('/reports/archive'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(record),
  }).catch(() => { /* bridge may be restarting; the next page refresh retries */ });
  window.dispatchEvent(new Event(archiveChangedEvent));
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
  try {
    const response = await fetch(bridgeUrl('/reports/archive'), { cache: 'no-store' });
    if (!response.ok) return [];
    const body = await response.json() as { reports?: ReportArchiveRecord[] };
    const reports = Array.isArray(body.reports) ? collapseReportRows(body.reports) : [];
    if (reports.length) {
      localStorage.setItem(archiveKey, JSON.stringify(reports.slice(0, 100)));
      return reports;
    }
    // One-time migration for reports created before the app-data archive was
    // introduced. The browser cache is never the authority after this sync.
    const cached = loadReportArchive();
    if (cached.length) {
      await Promise.all(cached.slice(0, 100).map((record) => fetch(bridgeUrl('/reports/archive'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(record),
      }).catch(() => null)));
    }
    return cached;
  } catch {
    return [];
  }
}

export const reportArchiveChangedEvent = archiveChangedEvent;
