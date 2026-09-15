export type HarnessFinding = { title: string; text: string };
export type HarnessTable = {
  title: string;
  columns: string[];
  rows: string[][];
};

export type HarnessOutput = {
  status: string;
  summary: string;
  dataDate: string;
  dataScope: string;
  cautions: string[];
  findings: HarnessFinding[];
  tables: HarnessTable[];
  jsonValid: boolean;
  parseError?: string;
  value: Record<string, unknown>;
};

function cleanText(value: unknown): string {
  if (typeof value === 'string') return value.trim();
  if (value == null) return '';
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  try { return JSON.stringify(value); } catch { return ''; }
}

/** Extract the first complete JSON object/array, allowing Harness to prepend a short status line. */
function extractJson(raw: string): string {
  const text = raw.trim().replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '').trim();
  const objectStart = text.indexOf('{');
  const arrayStart = text.indexOf('[');
  const start = objectStart < 0 ? arrayStart : arrayStart < 0 ? objectStart : Math.min(objectStart, arrayStart);
  if (start < 0) throw new Error('未找到 JSON 对象');
  const opener = text[start];
  const closer = opener === '{' ? '}' : ']';
  let depth = 0;
  let quote = false;
  let escaped = false;
  for (let i = start; i < text.length; i += 1) {
    const char = text[i];
    if (quote) {
      if (escaped) escaped = false;
      else if (char === '\\') escaped = true;
      else if (char === '"') quote = false;
      continue;
    }
    if (char === '"') { quote = true; continue; }
    if (char === opener) depth += 1;
    if (char === closer) {
      depth -= 1;
      if (depth === 0) return text.slice(start, i + 1);
    }
  }
  throw new Error('JSON 对象未闭合');
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return value == null ? [] : [cleanText(value)].filter(Boolean);
  return value.map(cleanText).filter(Boolean);
}

function parseJsonRecord(value: unknown): Record<string, unknown> | null {
  let current = value;
  for (let depth = 0; depth < 3; depth += 1) {
    if (current && typeof current === 'object' && !Array.isArray(current)) {
      return current as Record<string, unknown>;
    }
    if (typeof current !== 'string') return null;
    const text = current.trim();
    if (!text) return null;
    const repaired = text.replace(/([\]}])",(?=\s*["}])/g, '$1,');
    for (const candidate of [text, repaired]) {
      try {
        current = JSON.parse(candidate);
        break;
      } catch {
        try {
          current = JSON.parse(extractJson(candidate));
          break;
        } catch {
          current = null;
        }
      }
    }
    if (current == null) return null;
  }
  return current && typeof current === 'object' && !Array.isArray(current)
    ? current as Record<string, unknown>
    : null;
}

function unwrapNestedHarnessRecord(row: Record<string, unknown>): Record<string, unknown> {
  let current = row;
  for (let depth = 0; depth < 2; depth += 1) {
    const nested = parseJsonRecord(current.summary);
    if (!nested) break;
    const isReport = [
      'status', 'summary', 'data_date', 'data_scope', 'cautions', 'findings', 'tables',
    ].some((key) => Object.prototype.hasOwnProperty.call(nested, key));
    if (!isReport) break;
    const cautions = [
      ...asStringArray(current.cautions).filter((item) => !item.includes('Harness 原始输出未符合严格 JSON')),
      ...asStringArray(nested.cautions),
    ].filter((item, index, values) => values.indexOf(item) === index);
    current = {
      ...current,
      ...nested,
      cautions,
      findings: Array.isArray(nested.findings) ? nested.findings : current.findings,
      tables: Array.isArray(nested.tables) ? nested.tables : current.tables,
    };
  }
  return current;
}

function normalizeFindings(value: unknown): HarnessFinding[] {
  if (!Array.isArray(value)) return [];
  return value.map((item, index) => {
    if (typeof item === 'string') return { title: `结论 ${index + 1}`, text: item.trim() };
    if (!item || typeof item !== 'object') return { title: `结论 ${index + 1}`, text: cleanText(item) };
    const row = item as Record<string, unknown>;
    return {
      title: cleanText(row.title || row.name || row.label) || `结论 ${index + 1}`,
      text: cleanText(row.text || row.content || row.summary || row.value) || cleanText(row),
    };
  }).filter((item) => item.text);
}

function normalizeTables(value: unknown): HarnessTable[] {
  if (!Array.isArray(value)) return [];
  return value.map((item, index) => {
    const source: Record<string, unknown> = item && typeof item === 'object' && !Array.isArray(item)
      ? item as Record<string, unknown>
      : { rows: item };
    const rawRows = Array.isArray(source.rows) ? source.rows : [];
    const explicitColumns = Array.isArray(source.columns) ? source.columns.map((column: unknown) => cleanText(column)).filter(Boolean) : [];
    let columns = explicitColumns;
    let rows: string[][] = [];
    if (rawRows.length && rawRows.every((row) => Array.isArray(row))) {
      rows = rawRows.map((row) => (row as unknown[]).map(cleanText));
    } else if (rawRows.length) {
      const objects = rawRows.filter((row): row is Record<string, unknown> => !!row && typeof row === 'object' && !Array.isArray(row));
      if (!columns.length) columns = [...new Set(objects.flatMap((row) => Object.keys(row)))];
      rows = objects.map((row) => columns.map((column) => cleanText(row[column])));
    }
    if (!columns.length && rows.length) columns = rows[0].map((_, i) => `字段 ${i + 1}`);
    const width = columns.length;
    rows = rows.map((row) => width ? [...row.slice(0, width), ...Array(Math.max(0, width - row.length)).fill('—')] : row);
    return {
      title: cleanText(source.title || source.name) || `数据表 ${index + 1}`,
      columns,
      rows,
    };
  }).filter((table) => table.columns.length && table.rows.length);
}

/**
 * Recover the complete fields that appear before a bridge-truncated JSON tail.
 * Harness reports are deliberately data-only, so closing the open string and
 * container stack is safe for presentation while the result remains marked
 * jsonValid=false and carries a clear partial-output caution.
 */
function repairTruncatedJson(raw: string): { value: Record<string, unknown>; error: string } | null {
  const text = raw.trim().replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '').trim();
  const start = text.indexOf('{');
  if (start < 0) return null;
  const source = text.slice(start);
  const stack: string[] = [];
  let quoted = false;
  let escaped = false;
  for (let index = 0; index < source.length; index += 1) {
    const char = source[index];
    if (quoted) {
      if (escaped) escaped = false;
      else if (char === '\\') escaped = true;
      else if (char === '"') quoted = false;
      continue;
    }
    if (char === '"') { quoted = true; continue; }
    if (char === '{') stack.push('}');
    else if (char === '[') stack.push(']');
    else if (char === '}' || char === ']') {
      if (stack[stack.length - 1] === char) stack.pop();
      else return null;
    }
  }
  let candidate = source;
  if (quoted) candidate += '"';
  candidate = candidate.replace(/,\s*$/, '');
  while (stack.length) candidate += stack.pop();
  candidate = candidate.replace(/,\s*([}\]])/g, '$1');
  try {
    const parsed = JSON.parse(candidate);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return null;
    return {
      value: parsed as Record<string, unknown>,
      error: 'JSON 对象未闭合，已从桥接截断内容恢复已完成字段',
    };
  } catch {
    return null;
  }
}

export function normalizeHarnessOutput(raw: string): HarnessOutput {
  const fallbackValue: Record<string, unknown> = {};
  try {
    const parsed = JSON.parse(extractJson(raw));
    const value = Array.isArray(parsed) ? { rows: parsed } : (parsed && typeof parsed === 'object' ? parsed : fallbackValue);
    const row = unwrapNestedHarnessRecord(value as Record<string, unknown>);
    const findings = normalizeFindings(row.findings || row.conclusions || row.insights);
    const tables = normalizeTables(row.tables || row.data_tables || row.table);
    return {
      status: cleanText(row.status) || 'completed',
      summary: cleanText(row.summary || row.overview || row.conclusion),
      dataDate: cleanText(row.data_date || row.date),
      dataScope: cleanText(row.data_scope || row.scope),
      cautions: asStringArray(row.cautions || row.risks || row.limitations),
      findings,
      tables,
      jsonValid: true,
      value: row,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'JSON 解析失败';
    const repaired = repairTruncatedJson(raw);
    if (repaired) {
      const row = repaired.value;
      return {
        status: cleanText(row.status) || 'partial',
        summary: cleanText(row.summary || row.overview || row.conclusion),
        dataDate: cleanText(row.data_date || row.date),
        dataScope: cleanText(row.data_scope || row.scope),
        cautions: [
          '本次 Harness 输出曾被旧版桥接层截断，以下表格由已完成字段恢复；请重新执行以获得完整报告。',
          ...asStringArray(row.cautions || row.risks || row.limitations),
        ],
        findings: normalizeFindings(row.findings || row.conclusions || row.insights),
        tables: normalizeTables(row.tables || row.data_tables || row.table),
        jsonValid: false,
        parseError: repaired.error,
        value: row,
      };
    }
    return {
      status: 'normalized',
      summary: raw.trim(),
      dataDate: '',
      dataScope: '',
      cautions: ['Harness 返回未符合严格 JSON schema，已提取可读文本；请检查模型输出。'],
      findings: raw.trim() ? [{ title: '模型原文', text: raw.trim() }] : [],
      tables: [],
      jsonValid: false,
      parseError: message,
      value: fallbackValue,
    };
  }
}

export const HARNESS_JSON_SCHEMA = '只返回一个严格 JSON 对象，不要 Markdown、代码围栏或前后解释。字段必须为：status(string)、summary(string)、data_date(string)、data_scope(string)、cautions(string[])、findings({title:string,text:string}[])、tables({title:string,columns:string[],rows:string[][]}[])。所有结论只能引用传入数据，缺失项写入 cautions，不得虚构。报告按网页重点摘要标准输出：summary 不超过 120 字，findings 最多 5 条且每条不超过 100 字，tables 只保留最关键的 3 张表、每张最多 10 行；优先保留主线结论、核心指标、Top 候选和风险边界，省略重复解释。';
