'use client';

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

export function createReportId(prefix = 'report') {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function')
    return `${prefix}-${crypto.randomUUID()}`;
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function loadReportArchive(): ReportArchiveRecord[] {
  if (typeof window === 'undefined') return [];
  try {
    const value = JSON.parse(localStorage.getItem(archiveKey) || '[]');
    return Array.isArray(value) ? (value as ReportArchiveRecord[]) : [];
  } catch {
    return [];
  }
}

export function saveReportArchive(record: ReportArchiveRecord) {
  if (typeof window === 'undefined') return;
  const rows = loadReportArchive().filter((item) => item.id !== record.id);
  rows.unshift(record);
  rows.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
  localStorage.setItem(archiveKey, JSON.stringify(rows.slice(0, 100)));
  window.dispatchEvent(new Event(archiveChangedEvent));
}

export function deleteArchivedReport(id: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(
    archiveKey,
    JSON.stringify(loadReportArchive().filter((item) => item.id !== id)),
  );
  window.dispatchEvent(new Event(archiveChangedEvent));
}

export const reportArchiveChangedEvent = archiveChangedEvent;
