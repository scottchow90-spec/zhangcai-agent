'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Archive,
  BarChart3,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleHelp,
  Clock3,
  Database,
  FileText,
  History,
  LayoutDashboard,
  LoaderCircle,
  MessageSquarePlus,
  Minus,
  MoreHorizontal,
  PanelRight,
  Play,
  Plus,
  RefreshCw,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  X,
  XCircle,
  Zap,
} from 'lucide-react';
import skill14Catalog from '@/config/skill14-catalog.json';
import { bridgeHostLabel, bridgeUrl } from '@/lib/bridge-url';
import {
  createReportId,
  loadReportArchiveFromLocalRuntime,
  saveReportArchive,
  type ReportArchiveRecord,
} from '@/lib/report-archive';
import {
  HARNESS_JSON_SCHEMA,
  normalizeHarnessOutput,
  type HarnessOutput,
} from '@/lib/harness-output';

type SkillEntry = (typeof skill14Catalog.skills)[number] & {
  estimate: number;
  aliases: string[];
};
type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  kind: 'text' | 'route' | 'status' | 'report';
  text: string;
  createdAt: string;
  report?: HarnessOutput;
  skillName?: string;
};
type ChatSession = {
  id: string;
  title: string;
  updatedAt: string;
  messages: ChatMessage[];
};
type ReportTextScale = 'small' | 'standard' | 'large';
type Preflight = {
  status?: string;
  required_missing?: string[];
  optional_missing?: string[];
  degrade_policy?: string;
  execution_note?: string;
  error?: string;
  [key: string]: unknown;
};
type MarketSnapshot = {
  status?: string;
  date?: string;
  tradeDate?: string;
  currentCount?: number;
  total?: number;
  up?: number;
  down?: number;
  flat?: number;
  amount?: number;
  indices?: Array<Record<string, unknown>>;
  stocks?: Array<Record<string, unknown>>;
  allStocks?: Array<Record<string, unknown>>;
  sectors?: Array<Record<string, unknown>>;
  conceptBoards?: Array<Record<string, unknown>>;
  dataSources?: Record<string, unknown>;
  [key: string]: unknown;
};
type EnvironmentSnapshot = {
  status?: string;
  harness?: Record<string, unknown>;
  tdx?: Record<string, unknown>;
  [key: string]: unknown;
};
type PendingRoute = {
  skill: SkillEntry;
  request: string;
  preflight?: Preflight;
  stockCode?: string;
  stockName?: string;
  plan?: PendingRoute[];
};
type ActiveRunRecord = {
  version: 1;
  sessionId: string;
  pending: PendingRoute;
  jobId: string;
  startedAt: number;
  stepIndex: number;
  completedReports?: CompletedRunReport[];
};
type CompletedRunReport = {
  stepIndex: number;
  skillId: string;
  skillName: string;
  report: HarnessOutput;
};
type RunProgressStage = {
  key: string;
  label: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  detail?: string;
  startedAt?: number | null;
  completedAt?: number | null;
};
type RouteCandidate = { skill: SkillEntry; score: number; reason: string };
type StrategyScoreReceipt = {
  status?: string;
  strategy_id?: string;
  trade_date?: string;
  score_status?: string;
  score_source?: Record<string, unknown> | string;
  candidate_count?: number;
  missing?: string[];
  results?: Record<string, unknown>[];
  artifact_path?: string;
  audit?: Record<string, unknown>;
};
type SelectionCandidate = {
  code: string;
  name: string;
  pct: number;
  amount: number;
  score: number;
  wave: string;
  youzi: string;
  institution: string;
  risk: string;
  raw: Record<string, unknown>;
};

const SESSION_KEY = 'zhangcai.chat.sessions.v1';
const ACTIVE_SESSION_KEY = 'zhangcai.chat.active-session.v1';
const ACTIVE_RUN_KEY = 'zhangcai.chat.active-run.v1';
const REPORT_SCALE_KEY = 'zhangcai.chat.report-text-scale.v1';
const DEFAULT_ESTIMATE_SECONDS = 900;
const estimates: Record<string, number> = {
  'individual-stock-analysis-v31': 900,
  'golden-ignition-v8': 900,
  'limit-advance-v44': 900,
  'leader-deep-research': 900,
  'unified-shortterm-score-v4': 720,
  'limit-up-review': 900,
  'short-burst-score-v5': 900,
  'short-term-sentiment-v22': 720,
  'quant-production-v65': 1200,
  'lhb-postmarket-v43': 900,
  'market-environment-v5': 720,
  'market-data-capabilities': 600,
  'morning-intelligence-plan': 900,
  'workbuddy-evolution-v22': 900,
};
const aliases: Record<string, string[]> = {
  'individual-stock-analysis-v31': [
    '个股',
    '个股分析',
    '股票分析',
    '走势',
    '技术面',
    '基本面',
    '风险排雷',
    '风险分析',
    '深度研究',
  ],
  'golden-ignition-v8': ['黄金点火', '点火策略', '平台突破', '龙回头'],
  'limit-advance-v44': ['连板晋级', '一进二', '二进三', '晋级', '接力'],
  'leader-deep-research': ['龙头研究', '龙头分析', '龙头深度'],
  'unified-shortterm-score-v4': ['短线评分', '个股评分', '评分系统'],
  'limit-up-review': ['涨停复盘', '涨停板复盘', '涨停深度复盘'],
  'short-burst-score-v5': ['爆发力', '短线爆发'],
  'short-term-sentiment-v22': ['短线情绪', '市场情绪', '情绪周期', '梯队'],
  'quant-production-v65': ['量化选股', '量化生产', '模型选股'],
  'lhb-postmarket-v43': ['龙虎榜', '席位', '游资'],
  'market-environment-v5': ['市场环境', '大盘环境', '指数', '风险闸门'],
  'market-data-capabilities': ['行情资讯', '数据源', '接口', '数据能力'],
  'morning-intelligence-plan': ['早盘', '盘前', '盘前计划', '晨报'],
  'workbuddy-evolution-v22': ['质量控制', '回归验证', '纠错', '自我进化'],
};
const skills: SkillEntry[] = skill14Catalog.skills.map((skill) => ({
  ...skill,
  estimate: estimates[skill.id] || DEFAULT_ESTIMATE_SECONDS,
  aliases: aliases[skill.id] || [],
}));
const visibleSkillDirectory = skills.filter(
  (skill) =>
    skill.id !== 'market-data-capabilities' &&
    skill.id !== 'workbuddy-evolution-v22',
);
function restorePendingRoute(value: unknown): PendingRoute | null {
  if (!value || typeof value !== 'object') return null;
  const raw = value as Record<string, unknown>;
  const rawSkill =
    raw.skill && typeof raw.skill === 'object'
      ? (raw.skill as Record<string, unknown>)
      : undefined;
  const skillId =
    (typeof raw.skillId === 'string' && raw.skillId) ||
    (typeof rawSkill?.id === 'string' && rawSkill.id) ||
    '';
  const skill = skills.find((item) => item.id === skillId);
  const request = typeof raw.request === 'string' ? raw.request : '';
  if (!skill || !request) return null;
  const plan = Array.isArray(raw.plan)
    ? raw.plan
        .map((item) => restorePendingRoute(item))
        .filter((item): item is PendingRoute => Boolean(item))
    : undefined;
  return {
    skill,
    request,
    preflight:
      raw.preflight && typeof raw.preflight === 'object'
        ? (raw.preflight as Preflight)
        : undefined,
    stockCode: typeof raw.stockCode === 'string' ? raw.stockCode : undefined,
    stockName: typeof raw.stockName === 'string' ? raw.stockName : undefined,
    plan: plan?.length ? plan : undefined,
  };
}
function restoreActiveRun(value: unknown): ActiveRunRecord | null {
  if (!value || typeof value !== 'object') return null;
  const raw = value as Record<string, unknown>;
  const pending = restorePendingRoute(raw.pending);
  const sessionId = typeof raw.sessionId === 'string' ? raw.sessionId : '';
  const jobId = typeof raw.jobId === 'string' ? raw.jobId : '';
  const startedAt = typeof raw.startedAt === 'number' ? raw.startedAt : 0;
  const stepIndex = typeof raw.stepIndex === 'number' ? raw.stepIndex : 0;
  const completedReports = Array.isArray(raw.completedReports)
    ? raw.completedReports.filter((item): item is CompletedRunReport => Boolean(
        item && typeof item === 'object' &&
        typeof (item as CompletedRunReport).stepIndex === 'number' &&
        typeof (item as CompletedRunReport).skillId === 'string' &&
        typeof (item as CompletedRunReport).skillName === 'string' &&
        (item as CompletedRunReport).report && typeof (item as CompletedRunReport).report === 'object',
      ))
    : [];
  if (!pending || !sessionId || !Number.isFinite(startedAt) || startedAt <= 0)
    return null;
  return {
    version: 1,
    sessionId,
    pending,
    jobId,
    startedAt,
    stepIndex: Math.max(0, Math.floor(stepIndex)),
    completedReports,
  };
}
const scopeWords = [
  '股票',
  '个股',
  '选股',
  '股市',
  'A股',
  '行情',
  '大盘',
  '板块',
  '龙头',
  '涨停',
  '连板',
  '龙虎榜',
  '盘前',
  '盘后',
  '技术',
  '基本面',
  '风险',
  '走势',
  '代码',
  '指数',
  '情绪',
  '主线',
  '量化',
  '游资',
];
const labels: Record<string, string> = {
  READY: '数据完整',
  DEGRADED: '降级运行',
  BLOCKED: '已阻塞',
  FAILED: '运行失败',
  CANCELLED: '已取消',
  INTERRUPTED: '已中断',
  WAITING: '等待确认',
  RUNNING: '运行中',
};
const selectionSkillIds = new Set([
  'golden-ignition-v8',
  'short-burst-score-v5',
  'quant-production-v65',
]);

function uid(prefix: string) {
  return typeof crypto !== 'undefined' && crypto.randomUUID
    ? prefix + '-' + crypto.randomUUID()
    : prefix + '-' + Date.now() + '-' + Math.random().toString(36).slice(2, 8);
}
function iso() {
  return new Date().toISOString();
}
function safeText(value: unknown) {
  return typeof value === 'string' || typeof value === 'number'
    ? String(value)
    : '';
}
function dateText(value: unknown) {
  const digits = safeText(value).replace(/\D/g, '');
  return digits.length === 8
    ? digits.slice(0, 4) + '-' + digits.slice(4, 6) + '-' + digits.slice(6, 8)
    : '等待数据';
}
function duration(seconds: number) {
  return seconds < 60
    ? '约 ' + seconds + ' 秒'
    : '约 ' + Math.round(seconds / 60) + ' 分钟';
}
function stageClock(value: unknown) {
  const timestamp = Number(value);
  if (!Number.isFinite(timestamp) || timestamp <= 0) return '--:--:--';
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}
function normalizeRunProgress(value: unknown): RunProgressStage[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item): item is Record<string, unknown> => Boolean(item && typeof item === 'object'))
    .map((item) => {
      const rawStatus = safeText(item.status);
      const status: RunProgressStage['status'] =
        rawStatus === 'running' ||
        rawStatus === 'completed' ||
        rawStatus === 'failed' ||
        rawStatus === 'cancelled'
          ? rawStatus
          : 'pending';
      return {
        key: safeText(item.key),
        label: safeText(item.label) || safeText(item.key) || '研究阶段',
        status,
        detail: safeText(item.detail),
        startedAt: Number.isFinite(Number(item.started_at ?? item.startedAt))
          ? Number(item.started_at ?? item.startedAt)
          : null,
        completedAt: Number.isFinite(Number(item.finished_at ?? item.completedAt))
          ? Number(item.finished_at ?? item.completedAt)
          : null,
      };
    })
    .filter((item) => item.key);
}
function progressStatusText(status: RunProgressStage['status']) {
  if (status === 'completed') return '已完成';
  if (status === 'running') return '进行中';
  if (status === 'failed') return '失败';
  if (status === 'cancelled') return '已取消';
  return '等待';
}
function progressBubbleText(stage: RunProgressStage) {
  const detail = stage.detail ? ' · ' + stage.detail : '';
  return (
    '研究阶段 · ' +
    stageClock(stage.completedAt || stage.startedAt) +
    ' · ' +
    stage.label +
    ' · ' +
    progressStatusText(stage.status) +
    detail
  );
}
function normalizeStatus(value: unknown) {
  const text = safeText(value).toUpperCase();
  if (text.includes('BLOCK')) return 'BLOCKED';
  if (text.includes('DEGRAD')) return 'DEGRADED';
  if (text.includes('FAIL')) return 'FAILED';
  if (text.includes('CANCEL')) return 'CANCELLED';
  if (text.includes('INTERRUPT')) return 'INTERRUPTED';
  if (text === 'OK' || text.includes('COMPLETE') || text.includes('READY'))
    return 'READY';
  return text || 'READY';
}
function composeCompleteChatReport(
  completed: CompletedRunReport[],
  steps: PendingRoute[],
  fallbackDate: string,
): HarnessOutput {
  const reports = completed.map((item) => item.report);
  const status = reports.some((item) => normalizeStatus(item.status) === 'BLOCKED')
    ? 'BLOCKED'
    : reports.some((item) => normalizeStatus(item.status) === 'FAILED')
      ? 'FAILED'
      : reports.some((item) => normalizeStatus(item.status) === 'DEGRADED')
        ? 'DEGRADED'
        : 'READY';
  const findings = completed.flatMap((item) =>
    item.report.findings.map((finding) => ({
      title: `${item.skillName} · ${finding.title}`,
      text: finding.text,
    })),
  );
  const tables = completed.flatMap((item) =>
    item.report.tables.map((table) => ({
      ...table,
      title: `${item.skillName} · ${table.title}`,
    })),
  );
  const cautions = [...new Set(completed.flatMap((item) => item.report.cautions))];
  const dataDate = [...completed]
    .reverse()
    .map((item) => item.report.dataDate)
    .find(Boolean) || fallbackDate;
  const dataScope = [...new Set(completed.map((item) => item.report.dataScope).filter(Boolean))].join('；');
  const summary = completed.length === 1
    ? completed[0].report.summary
    : `已完成 ${completed.length} 步研究计划：${completed.map((item) => item.skillName).join('、')}。各步骤结论、数据表和风险边界已合并为一份完整报告。`;
  const value: Record<string, unknown> = {
    status,
    summary,
    data_date: dataDate,
    data_scope: dataScope,
    cautions,
    findings,
    tables,
    plan: completed.map((item) => ({
      step: item.stepIndex + 1,
      skill_id: item.skillId,
      skill_name: item.skillName,
      report: item.report.value,
    })),
  };
  return {
    status,
    summary,
    dataDate,
    dataScope,
    cautions,
    findings,
    tables,
    jsonValid: completed.every((item) => item.report.jsonValid),
    value,
  };
}
function stockCode(text: string) {
  return text.match(
    /(?<!\d)(?:600|601|603|605|000|001|002|003|300|301|688|689)\d{3}(?!\d)/,
  )?.[0];
}
function isStockRequest(text: string, market: MarketSnapshot | null = null) {
  const normalized = text.toLowerCase();
  const matchedSkill = skills.some((skill) =>
    [skill.name, skill.category, ...skill.aliases].some((term) =>
      normalized.includes(String(term).toLowerCase()),
    ),
  );
  return (
    scopeWords.some((word) => text.includes(word)) ||
    Boolean(stockCode(text)) ||
    Boolean(findStock(market, text)) ||
    matchedSkill
  );
}
function initialSession(): ChatSession {
  return {
    id: uid('session'),
    title: '新的研究会话',
    updatedAt: iso(),
    messages: [
      {
        id: uid('message'),
        role: 'assistant',
        kind: 'text',
        createdAt: iso(),
        text: '你好，我是掌财研究工作台。\\n我只处理沪深 A 股的选股、行情、个股研究和复盘，不执行任何交易操作。\\n\\n你可以直接告诉我想研究什么；识别到技能后，我会先展示技能、预计耗时和数据完整性，等你确认后才运行。',
      },
    ],
  };
}
function sessionActivityTime(session: ChatSession) {
  const updated = Date.parse(session.updatedAt);
  const latestMessage = session.messages.reduce((latest, message) => {
    const created = Date.parse(message.createdAt);
    return Number.isFinite(created) ? Math.max(latest, created) : latest;
  }, 0);
  return Math.max(Number.isFinite(updated) ? updated : 0, latestMessage);
}
function sortSessionsByActivity(list: ChatSession[]) {
  return [...list].sort(
    (left, right) => sessionActivityTime(right) - sessionActivityTime(left),
  );
}
function route(
  text: string,
  market: MarketSnapshot | null = null,
): RouteCandidate[] {
  const normalized = text.toLowerCase();
  return skills
    .map((skill) => {
      const hits = [
        skill.name,
        skill.category,
        skill.summary,
        ...skill.aliases,
      ].filter((item) => normalized.includes(String(item).toLowerCase()));
      const codeBoost =
        skill.id === 'individual-stock-analysis-v31' && stockCode(text) ? 3 : 0;
      const researchBoost =
        skill.id === 'individual-stock-analysis-v31' &&
        /分析|研究|风险|走势/.test(text)
          ? 1
          : 0;
      const stockNameBoost =
        skill.id === 'individual-stock-analysis-v31' && findStock(market, text)
          ? 2
          : 0;
      return {
        skill,
        score: hits.length * 2 + codeBoost + researchBoost + stockNameBoost,
        reason: hits.slice(0, 2).join('、') || 'A 股研究请求',
      };
    })
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 4);
}
function splitPlanRequests(text: string) {
  if (!/(先|首先|然后|再|最后)/.test(text)) return [];
  return text
    .split(/先|首先|然后|再|最后/)
    .map((part) => part.replace(/^[做看分析评估检查研究]+/, '').trim())
    .map((part) => part.replace(/^[，,；;。\s]+|[，,；;。\s]+$/g, ''))
    .filter((part) => part.length > 1);
}
function routePlan(
  text: string,
  market: MarketSnapshot | null = null,
): PendingRoute[] | null {
  const parts = splitPlanRequests(text);
  if (parts.length < 2) return null;
  const steps: PendingRoute[] = [];
  for (const part of parts) {
    const found = route(part, market);
    if (!found.length || (found[1] && found[0].score === found[1].score))
      return null;
    steps.push({ skill: found[0].skill, request: part });
  }
  return steps;
}
async function fetchPreflight(skillId: string) {
  const response = await fetch(bridgeUrl('/skill14/preflight'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ skillId }),
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok)
    throw new Error(result.error || '技能预检失败（' + response.status + '）');
  return result as Preflight;
}
function findStock(market: MarketSnapshot | null, request: string) {
  const rows = [...(market?.allStocks || []), ...(market?.stocks || [])];
  const code = stockCode(request);
  if (code) return rows.find((row) => safeText(row.code) === code);
  return rows.find(
    (row) =>
      safeText(row.name).trim() &&
      request.replace(/\s/g, '').includes(safeText(row.name).trim()),
  );
}
function isIndividualStockSkill(skill: SkillEntry) {
  return skill.id === 'individual-stock-analysis-v31';
}
function stockIdentity(market: MarketSnapshot | null, request: string) {
  const stock = findStock(market, request);
  return {
    stock,
    code: safeText(stock?.code) || stockCode(request) || '',
    name: safeText(stock?.name),
  };
}
function compactMarket(market: MarketSnapshot) {
  const rows = (market.allStocks || market.stocks || []).slice(0, 80);
  return {
    date: market.date || market.tradeDate || '',
    currentCount: market.currentCount || market.total || rows.length,
    up: market.up || 0,
    down: market.down || 0,
    flat: market.flat || 0,
    amount: market.amount || 0,
    indices: (market.indices || []).slice(0, 8),
    stocks: rows,
    sectors: (market.sectors || []).slice(0, 30),
    conceptBoards: (market.conceptBoards || []).slice(0, 30),
    dataSources: market.dataSources || {},
    scope:
      '本地行情快照 · ' +
      dateText(market.date || market.tradeDate) +
      ' · 当前传入 ' +
      rows.length +
      ' 条候选行',
  };
}
function missingData(preflight?: Preflight) {
  return {
    required: Array.isArray(preflight?.required_missing)
      ? preflight.required_missing
      : [],
    optional: Array.isArray(preflight?.optional_missing)
      ? preflight.optional_missing
      : [],
  };
}
function localReport(
  status: string,
  summary: string,
  cautions: string[],
  findings: Array<{ title: string; text: string }>,
  date = '',
  scope = '',
): HarnessOutput {
  return {
    status,
    summary,
    dataDate: date,
    dataScope: scope,
    cautions,
    findings,
    tables: [],
    jsonValid: true,
    value: {
      status,
      summary,
      data_date: date,
      data_scope: scope,
      cautions,
      findings,
      tables: [],
    },
  };
}

function isSelectionSkill(skillId: string) {
  return selectionSkillIds.has(skillId);
}

function selectionNumber(row: Record<string, unknown>, ...keys: string[]) {
  for (const key of keys) {
    const value = Number(row[key]);
    if (Number.isFinite(value)) return value;
  }
  return null;
}

function selectionText(row: Record<string, unknown>, ...keys: string[]) {
  for (const key of keys) {
    const value = safeText(row[key]);
    if (value) return value;
  }
  return '';
}

function selectionCandidatePool(market: MarketSnapshot) {
  const source = market.allStocks?.length
    ? market.allStocks
    : market.stocks || [];
  // These defaults match the original strategy engine. Keeping the
  // pool contract identical is important: the chat UI must not silently
  // replace the original engine with a different candidate universe.
  return source
    .filter(
      (stock) =>
        Number(stock.pct) >= 3 &&
        Number(stock.amount) >= 1e8 &&
        (!market.date ||
          !safeText(stock.date) ||
          safeText(stock.date) === safeText(market.date)),
    )
    .sort(
      (a, b) =>
        Number(b.pct || 0) - Number(a.pct || 0) ||
        Number(b.amount || 0) - Number(a.amount || 0),
    )
    .slice(0, 30);
}

function selectionCandidates(
  market: MarketSnapshot,
  receipt: StrategyScoreReceipt,
  skillId: string,
) {
  const resultMap = new Map(
    (Array.isArray(receipt.results) ? receipt.results : []).map((row) => [
      safeText(row.code),
      row,
    ]),
  );
  const candidates = selectionCandidatePool(market).map((stock) => {
    const raw = resultMap.get(safeText(stock.code)) || {};
    const score =
      selectionNumber(
        raw,
        'score',
        'final_score',
        'short_burst_score',
        'primary_score',
        'model_c_score',
        'model_a_score',
        'model_b_score',
      ) || 0;
    const a = selectionNumber(raw, 'model_a_score');
    const b = selectionNumber(raw, 'model_b_score');
    const c = selectionNumber(raw, 'model_c_score');
    const wave =
      skillId === 'golden-ignition-v8'
        ? `阶段 ${selectionText(raw, 'golden_stage') || '未命中'} · A ${a == null ? '—' : a.toFixed(1)} / B ${b == null ? '—' : b.toFixed(1)} / C ${c == null ? '—' : c.toFixed(1)}`
        : `${selectionText(raw, 'stage') || '阶段未知'} · ${selectionText(raw, 'position') || '地位未知'} · ${selectionText(raw, 'overheat') || '透支未知'}`;
    const youzi =
      skillId === 'golden-ignition-v8'
        ? `模型B弱转强 ${b == null ? '—' : b.toFixed(1)}`
        : `资金质量 ${selectionText(raw, '资金质量') || '—'}`;
    const institution =
      skillId === 'golden-ignition-v8'
        ? `模型C黄金点火 ${c == null ? '—' : c.toFixed(1)}`
        : `资金弹性 ${selectionText(raw, '资金弹性') || '—'}`;
    const rejectReasons = Array.isArray(raw.hard_reject_reasons)
      ? raw.hard_reject_reasons.map(String).filter(Boolean).join('；')
      : '';
    const risk =
      skillId === 'golden-ignition-v8'
        ? selectionText(raw, 'golden_fail_reasons') ||
          (raw.final_pass ? 'V8三模型均未通过' : 'V8硬条件未通过')
        : rejectReasons || selectionText(raw, 'conclusion') || '无硬否决回执';
    return {
      code: safeText(stock.code),
      name: safeText(stock.name) || safeText(raw.name) || safeText(stock.code),
      pct: Number(stock.pct) || 0,
      amount: Number(stock.amount) || 0,
      score,
      wave,
      youzi,
      institution,
      risk,
      raw,
    } satisfies SelectionCandidate;
  });
  return candidates.sort(
    (a, b) => b.score - a.score || b.pct - a.pct || b.amount - a.amount,
  );
}

function selectionColumns(skillId: string) {
  return skillId === 'quant-production-v65'
    ? ['排名', '代码', '名称', '评分', '波段', '游资', '机构', '风险']
    : ['排名', '代码', '名称', '评分', '波段', '游资', '机构', '风险'];
}

function selectionReport(
  skill: SkillEntry,
  market: MarketSnapshot,
  receipt: StrategyScoreReceipt,
  candidates: SelectionCandidate[],
  extraCautions: string[] = [],
): HarnessOutput {
  const scoreStatus = safeText(receipt.score_status || 'UNKNOWN').toUpperCase();
  const status = scoreStatus.includes('BLOCK')
    ? 'BLOCKED'
    : scoreStatus.includes('DEGRAD')
      ? 'DEGRADED'
      : 'READY';
  const date = safeText(receipt.trade_date || market.date || market.tradeDate);
  const missing = Array.isArray(receipt.missing)
    ? receipt.missing.map(String).filter(Boolean)
    : [];
  const rows = candidates
    .slice(0, 10)
    .map((candidate, index) => [
      String(index + 1),
      candidate.code,
      candidate.name,
      String(candidate.score),
      candidate.wave,
      candidate.youzi,
      candidate.institution,
      candidate.risk,
    ]);
  const cautions = [
    `本地原始评分状态：${scoreStatus}；评分字段由对应原始策略引擎计算。`,
    ...(missing.length ? [`评分缺失项：${missing.join('；')}`] : []),
    ...extraCautions,
  ];
  const top = candidates.slice(0, 3);
  const summary = top.length
    ? `${skill.name} 已完成本地候选评分：${top.map((item) => `${item.name} ${item.score}分`).join('、')}；当前为${status === 'DEGRADED' ? '降级' : '可用'}研究结果。`
    : `${skill.name} 未形成候选评分结果；当前不生成策略结论。`;
  const value = {
    status,
    summary,
    data_date: date,
    data_scope: `本地同日行情 · ${dateText(date)} · 条件候选 ${candidates.length} 只 · 原始引擎 ${scoreStatus}`,
    cautions,
    findings: [
      {
        title: '原始评分回执',
        text: `原始引擎返回 ${candidates.length} 只候选，score_status=${scoreStatus}。`,
      },
      ...(top.length
        ? [
            {
              title: '当前评分靠前',
              text: top
                .map((item) => `${item.name}（${item.code}）${item.score}分`)
                .join('、'),
            },
          ]
        : []),
    ],
    tables: [
      {
        title: 'Top 候选',
        columns: selectionColumns(skill.id),
        rows,
      },
    ],
  };
  return {
    status,
    summary,
    dataDate: date,
    dataScope: String(value.data_scope),
    cautions,
    findings: value.findings,
    tables: value.tables,
    jsonValid: true,
    value,
  };
}

function reconcileSelectionReport(
  raw: string,
  local: HarnessOutput,
  receipt: StrategyScoreReceipt,
) {
  const parsed = normalizeHarnessOutput(raw);
  const scoreStatus = safeText(receipt.score_status || '').toUpperCase();
  const status = scoreStatus.includes('BLOCK')
    ? 'BLOCKED'
    : scoreStatus.includes('DEGRAD')
      ? 'DEGRADED'
      : normalizeStatus(parsed.status);
  const cautions = Array.from(
    new Set([
      'Top 候选的评分字段已由原始策略引擎计算；Harness 只负责解释、缺失项和风险边界。',
      ...local.cautions,
      ...parsed.cautions,
    ]),
  );
  const value = {
    ...parsed.value,
    status,
    summary: parsed.summary || local.summary,
    data_date: parsed.dataDate || local.dataDate,
    data_scope: parsed.dataScope || local.dataScope,
    cautions,
    findings: parsed.findings.length ? parsed.findings : local.findings,
    tables: local.tables,
  };
  return {
    ...parsed,
    status,
    summary: String(value.summary || local.summary),
    dataDate: String(value.data_date || local.dataDate),
    dataScope: String(value.data_scope || local.dataScope),
    cautions,
    findings: Array.isArray(value.findings) ? value.findings : local.findings,
    tables: local.tables,
    value,
  } satisfies HarnessOutput;
}
async function loadHistory(stock: Record<string, unknown> | undefined) {
  if (!stock?.code) return undefined;
  const code = safeText(stock.code);
  const symbol =
    code +
    '.' +
    safeText(
      stock.market || (code.startsWith('6') ? 'SH' : 'SZ'),
    ).toUpperCase();
  try {
    const response = await fetch(
      bridgeUrl(
        // Individual research needs the same complete local TDX history used
        // by the stock workflow. The bridge treats limit=0 as full-file
        // mode and still caps the response at its safety maximum.
        '/market/history?symbol=' + encodeURIComponent(symbol) + '&limit=0',
      ),
      { cache: 'no-store' },
    );
    if (!response.ok) return undefined;
    const body = await response.json().catch(() => ({}));
    return {
      symbol,
      status: body.status || 'ok',
      source: body.source || '本地日线',
      bars: Array.isArray(body.bars)
        ? body.bars
        : Array.isArray(body.history)
          ? body.history
          : [],
      meta: body,
    };
  } catch {
    return undefined;
  }
}
class CancelledRunError extends Error {
  constructor() {
    super('用户已取消本次研究任务');
  }
}
async function waitForHarnessJob(input: {
  jobId: string;
  cancelled: () => boolean;
  onProgress?: (stages: RunProgressStage[]) => void;
}) {
  while (true) {
    if (input.cancelled()) {
      await fetch(
        bridgeUrl('/agent/job/' + encodeURIComponent(input.jobId) + '/cancel'),
        { method: 'POST' },
      ).catch(() => undefined);
      throw new CancelledRunError();
    }
    const jobResponse = await fetch(
      bridgeUrl('/agent/job/' + encodeURIComponent(input.jobId)),
      { cache: 'no-store' },
    );
    const job = await jobResponse.json().catch(() => ({}));
    if (!jobResponse.ok)
      throw new Error(
        job.error || 'Harness 状态读取失败（' + jobResponse.status + '）',
      );
    input.onProgress?.(normalizeRunProgress(job.progress_steps));
    if (job.status === 'completed')
      return { output: String(job.output || ''), jobId: input.jobId };
    if (job.status === 'cancelled') throw new CancelledRunError();
    if (job.status === 'failed')
      throw new Error(job.error || 'DeepSeek Harness 执行失败');
    await new Promise((resolve) => window.setTimeout(resolve, 1000));
  }
}
async function runHarness(input: {
  task: string;
  skillId: string;
  market: unknown;
  context: unknown;
  onStarted: (id: string) => void;
  cancelled: () => boolean;
  onProgress?: (stages: RunProgressStage[]) => void;
  resumeJobId?: string;
}) {
  if (input.resumeJobId) {
    input.onStarted(input.resumeJobId);
    return waitForHarnessJob({
      jobId: input.resumeJobId,
      cancelled: input.cancelled,
      onProgress: input.onProgress,
    });
  }
  const response = await fetch(bridgeUrl('/agent/start'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      task: input.task,
      skillId: input.skillId,
      market: input.market,
      context: input.context,
    }),
  });
  const start = await response.json().catch(() => ({}));
  if (response.status === 409 || start.status === 'busy')
    throw new Error(start.error || 'Harness 正在执行其他任务，请稍后再试。');
  if (
    !response.ok ||
    start.status !== 'accepted' ||
    typeof start.job_id !== 'string'
  )
    throw new Error(
      start.error || 'Harness 任务启动失败（' + response.status + '）',
    );
  input.onStarted(start.job_id);
  return waitForHarnessJob({
    jobId: start.job_id,
    cancelled: input.cancelled,
    onProgress: input.onProgress,
  });
}

async function runSelectionSkill(input: {
  skill: SkillEntry;
  request: string;
  market: MarketSnapshot;
  preflight?: Preflight;
  context: unknown;
  onStarted: (id: string) => void;
  cancelled: () => boolean;
  onProgress?: (stages: RunProgressStage[]) => void;
  resumeJobId?: string;
}) {
  const scoreStartedAt = Date.now();
  input.onProgress?.([
    {
      key: 'accepted',
      label: '研究任务已接收',
      status: 'completed',
      startedAt: scoreStartedAt,
      completedAt: scoreStartedAt,
      detail: '正在复用原始策略评分引擎。',
    },
    {
      key: 'tdx',
      label: '完成本地行情与技能数据处理',
      status: 'running',
      startedAt: scoreStartedAt,
      detail: '正在形成候选数值回执。',
    },
  ]);
  const candidatePool = selectionCandidatePool(input.market);
  if (!candidatePool.length) {
    throw new Error('原始策略没有形成满足默认条件的同日候选池。');
  }
  const scoreResponse = await fetch(bridgeUrl('/strategy/selection/scored'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      strategyId: input.skill.id,
      date: input.market.date || input.market.tradeDate,
      candidates: candidatePool,
    }),
    cache: 'no-store',
  });
  const scoreReceipt = (await scoreResponse
    .json()
    .catch(() => ({}))) as StrategyScoreReceipt & {
    error?: string;
  };
  if (!scoreResponse.ok || scoreReceipt.status !== 'ok') {
    throw new Error(
      scoreReceipt.error || `原始策略评分服务返回 ${scoreResponse.status}`,
    );
  }
  input.onProgress?.([
    {
      key: 'accepted',
      label: '研究任务已接收',
      status: 'completed',
      startedAt: scoreStartedAt,
      completedAt: scoreStartedAt,
      detail: '正在复用原始策略评分引擎。',
    },
    {
      key: 'tdx',
      label: '完成本地行情与技能数据处理',
      status: 'completed',
      startedAt: scoreStartedAt,
      completedAt: Date.now(),
      detail: `已形成 ${scoreReceipt.candidate_count || candidatePool.length} 条候选评分回执。`,
    },
    {
      key: 'supplemental',
      label: '完成市场、板块等补充数据处理',
      status: 'completed',
      startedAt: scoreStartedAt,
      completedAt: Date.now(),
      detail: '候选评分所需的本地市场补充数据已准备。',
    },
  ]);
  if (input.cancelled()) throw new CancelledRunError();
  const candidates = selectionCandidates(
    input.market,
    scoreReceipt,
    input.skill.id,
  );
  const local = selectionReport(
    input.skill,
    input.market,
    scoreReceipt,
    candidates,
  );
  const missing = Array.isArray(scoreReceipt.missing)
    ? scoreReceipt.missing.map(String).filter(Boolean)
    : [];
  const columns = selectionColumns(input.skill.id).join('、');
  const task =
    `请对“${input.skill.name}”完成策略选股网页分析。当前网页预检状态为 ${input.preflight?.status || '未知'}，并已调用对应原始策略评分引擎完成本地数值回执。候选数组中的 score、wave、youzi、institution、risk 来自原始策略评分字段的网页适配展示；不得用涨幅、成交额、候选排名或其他代理值替代 score。必须原样引用 strategy_score_status、strategy_missing 和 strategy_fields 中能支持的字段。评分回执的 score_status=${scoreReceipt.score_status || '未知'}；缺失项=${missing.join('、') || '无'}。若 score_status 为 DEGRADED，只能称为本地降级研究评分，必须在 cautions 写出缺失项；若为 BLOCKED，不得把候选表写成已执行策略结果。请严格基于传入的本地行情、原始评分回执、条件候选和预检结果输出分析。只返回一个严格 JSON 对象：status、summary、data_date、data_scope、cautions、findings、tables。tables 只保留一张“Top 候选”表，最多 10 行，列为${columns}；候选不足时 rows 为空并在 cautions 说明原因。summary 不超过 80 字，findings 最多 3 条，每条不超过 50 字。只读研究，不给出买卖建议，不虚构未传入的数据。` +
    HARNESS_JSON_SCHEMA;
  try {
    const result = await runHarness({
      task,
      skillId: input.skill.id,
      market: compactMarket(input.market),
      context: {
        ...(input.context && typeof input.context === 'object'
          ? input.context
          : {}),
        page: 'chat-selection',
        preflight: input.preflight,
        strategy_score: {
          status: scoreReceipt.score_status || 'UNKNOWN',
          missing: scoreReceipt.missing || [],
          source: scoreReceipt.score_source || 'embedded_original_engine',
          artifact_path: scoreReceipt.artifact_path || '',
        },
        candidates: candidates.map((candidate) => ({
          ...candidate,
          strategy_score: candidate.score,
          strategy_score_status: scoreReceipt.score_status || 'UNKNOWN',
          strategy_score_source: scoreReceipt.score_source || '',
          strategy_missing: Array.isArray(candidate.raw.missing)
            ? candidate.raw.missing
            : scoreReceipt.missing || [],
          strategy_fields: candidate.raw,
        })),
      },
      onStarted: input.onStarted,
      cancelled: input.cancelled,
      onProgress: input.onProgress,
      resumeJobId: input.resumeJobId,
    });
    const reconciled = reconcileSelectionReport(
      result.output,
      local,
      scoreReceipt,
    );
    return { output: JSON.stringify(reconciled.value), jobId: result.jobId };
  } catch (error) {
    if (error instanceof CancelledRunError || input.cancelled()) throw error;
    const message = error instanceof Error ? error.message : String(error);
    const fallback = selectionReport(
      input.skill,
      input.market,
      scoreReceipt,
      candidates,
      [
        `Harness 解读未完成：${message}`,
        '已保留原始评分回执；当前报告只作为本地降级研究结果，不代表 Harness 已完成。',
      ],
    );
    return { output: JSON.stringify(fallback.value), jobId: '' };
  }
}

const reportScaleLabels: Record<ReportTextScale, string> = {
  small: '小字号',
  standard: '标准',
  large: '大字号',
};

function ReportTextControls({
  scale,
  onChange,
}: {
  scale: ReportTextScale;
  onChange: (next: ReportTextScale) => void;
}) {
  return (
    <div className="report-text-controls" aria-label="报告文字大小">
      <span className="report-text-controls-label">文字大小</span>
      <button
        type="button"
        className="report-text-button"
        aria-label="缩小报告文字"
        title="缩小报告文字"
        disabled={scale === 'small'}
        onClick={() =>
          onChange(scale === 'large' ? 'standard' : 'small')
        }
      >
        <Minus size={13} />
      </button>
      <button
        type="button"
        className="report-text-scale"
        aria-label="恢复标准报告字号"
        title="恢复标准报告字号"
        onClick={() => onChange('standard')}
      >
        {reportScaleLabels[scale]}
      </button>
      <button
        type="button"
        className="report-text-button"
        aria-label="放大报告文字"
        title="放大报告文字"
        disabled={scale === 'large'}
        onClick={() =>
          onChange(scale === 'small' ? 'standard' : 'large')
        }
      >
        <Plus size={13} />
      </button>
    </div>
  );
}

function ReportCard({
  report,
  skill,
  skillName,
  textScale,
  onTextScaleChange,
}: {
  report: HarnessOutput;
  skill?: SkillEntry;
  skillName?: string;
  textScale: ReportTextScale;
  onTextScaleChange: (next: ReportTextScale) => void;
}) {
  const status = normalizeStatus(report.status);
  return (
    <article
      className={
        'chat-report-card report-' +
        status.toLowerCase() +
        ' report-text-' +
        textScale
      }
    >
      <div className="chat-report-head">
        <div>
          <span className="report-kicker">
            <FileText size={13} />
            研究报告
          </span>
          <h3>{skill?.name || skillName || '股票研究结果'}</h3>
        </div>
        <div className="report-head-actions">
          <span className={'chat-status status-' + status.toLowerCase()}>
            <span className="status-dot" />
            {labels[status] || status}
          </span>
          <ReportTextControls
            scale={textScale}
            onChange={onTextScaleChange}
          />
        </div>
      </div>
      <div className="chat-report-meta">
        <span>
          <Database size={13} />
          {dateText(report.dataDate)}
        </span>
        <span>
          <BarChart3 size={13} />
          {report.dataScope || '本地股票研究数据'}
        </span>
      </div>
      <div className="report-conclusion">
        <span>一句话结论</span>
        <p>{report.summary || '本次任务没有返回摘要。'}</p>
      </div>
      {report.findings.length > 0 ? (
        <div className="report-findings">
          <span className="section-label">分析依据</span>
          {report.findings.slice(0, 5).map((item, index) => (
            <div className="finding-row" key={item.title + index}>
              <span>{String(index + 1).padStart(2, '0')}</span>
              <div>
                <b>{item.title}</b>
                <p>{item.text}</p>
              </div>
            </div>
          ))}
        </div>
      ) : null}
      {report.tables.length > 0 ? (
        <div className="report-tables">
          <span className="section-label">关键数据</span>
          {report.tables.slice(0, 3).map((table) => (
            <div className="report-table-wrap" key={table.title}>
              <h4>{table.title}</h4>
              <div className="report-table-scroll">
                <table>
                  <thead>
                    <tr>
                      {table.columns.map((column) => (
                        <th key={column}>{column}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {table.rows.slice(0, 10).map((row, rowIndex) => (
                      <tr key={rowIndex}>
                        {row.map((cell, cellIndex) => (
                          <td key={rowIndex + '-' + cellIndex}>
                            {cell || '—'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      ) : null}
      {report.cautions.length > 0 ? (
        <div className="report-cautions">
          <span className="section-label">风险与数据边界</span>
          {report.cautions.slice(0, 6).map((item, index) => (
            <p key={item + index}>
              <span>!</span>
              {item}
            </p>
          ))}
        </div>
      ) : null}
      <details className="report-raw">
        <summary>查看原始结构化结果</summary>
        <pre>{JSON.stringify(report.value || {}, null, 2)}</pre>
      </details>
    </article>
  );
}

export default function ChatClient() {
  const [session, setSession] = useState<ChatSession>(() => initialSession());
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [hydrated, setHydrated] = useState(false);
  const [input, setInput] = useState('');
  const [market, setMarket] = useState<MarketSnapshot | null>(null);
  const [environment, setEnvironment] = useState<EnvironmentSnapshot | null>(
    null,
  );
  const [resourceLibraryContext, setResourceLibraryContext] = useState<Record<string, unknown> | null>(null);
  const [marketLoading, setMarketLoading] = useState(true);
  const [environmentLoading, setEnvironmentLoading] = useState(true);
  const [candidates, setCandidates] = useState<RouteCandidate[]>([]);
  const [pending, setPending] = useState<PendingRoute | null>(null);
  const [routeLoading, setRouteLoading] = useState(false);
  const [runStatus, setRunStatus] = useState<'idle' | 'running' | 'cancelled'>(
    'idle',
  );
  const [runElapsed, setRunElapsed] = useState(0);
  const [runStartedAt, setRunStartedAt] = useState<number | null>(null);
  const [runStepIndex, setRunStepIndex] = useState(0);
  const [runStages, setRunStages] = useState<RunProgressStage[]>([]);
  const [jobId, setJobId] = useState('');
  const [resumeRun, setResumeRun] = useState<ActiveRunRecord | null>(null);
  const [completedRunReports, setCompletedRunReports] = useState<CompletedRunReport[]>([]);
  const [archiveRows, setArchiveRows] = useState<ReportArchiveRecord[]>([]);
  const [archiveOpen, setArchiveOpen] = useState(false);
  const [selectedArchive, setSelectedArchive] =
    useState<ReportArchiveRecord | null>(null);
  const [reportTextScale, setReportTextScale] =
    useState<ReportTextScale>('large');
  const cancelRef = useRef(false);
  const runProgressFingerprintRef = useRef(new Set<string>());
  const messageListRef = useRef<HTMLDivElement | null>(null);
  const latestMessageRef = useRef<HTMLDivElement | null>(null);

  const runtimeLabel = useMemo(() => {
    if (environmentLoading) return '检查中';
    if (
      environment?.harness?.status === 'ready' ||
      environment?.harness?.status === 'available'
    )
      return 'Harness 就绪';
    return safeText(environment?.harness?.status) || '待检查';
  }, [environment, environmentLoading]);

  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem(SESSION_KEY) || '[]');
      const storedReportTextScale = localStorage.getItem(REPORT_SCALE_KEY);
      if (
        storedReportTextScale === 'small' ||
        storedReportTextScale === 'standard' ||
        storedReportTextScale === 'large'
      ) {
        // eslint-disable-next-line react/react-compiler
        setReportTextScale(storedReportTextScale);
      }
      if (Array.isArray(stored) && stored.length) {
        const ordered = sortSessionsByActivity(
          stored.filter(
            (item: unknown): item is ChatSession =>
              Boolean(
                item &&
                  typeof item === 'object' &&
                  typeof (item as ChatSession).id === 'string' &&
                  Array.isArray((item as ChatSession).messages),
              ),
          ),
        );
        const active = ordered[0];
        if (!active) throw new Error('没有可恢复的有效研究会话');
        // Restore the browser-persisted session after the server-rendered
        // shell has mounted. This is intentionally a client hydration write.
        // eslint-disable-next-line react/react-compiler
        setSession(active);
        // eslint-disable-next-line react/react-compiler
        setSessions(ordered);
      } else {
        const first = initialSession();
        // eslint-disable-next-line react/react-compiler
        setSession(first);
        // eslint-disable-next-line react/react-compiler
        setSessions([first]);
      }
      const activeRunRaw = localStorage.getItem(ACTIVE_RUN_KEY);
      const activeRun = activeRunRaw
        ? restoreActiveRun(JSON.parse(activeRunRaw))
        : null;
      if (activeRun) {
        setPending(activeRun.pending);
        setRunStatus('running');
        setRunStartedAt(activeRun.startedAt);
        setRunStepIndex(activeRun.stepIndex);
        setJobId(activeRun.jobId);
        setCompletedRunReports(activeRun.completedReports || []);
        setResumeRun(activeRun);
      } else if (activeRunRaw) {
        localStorage.removeItem(ACTIVE_RUN_KEY);
      }
    } catch {
      const first = initialSession();
      // eslint-disable-next-line react/react-compiler
      setSession(first);
      // eslint-disable-next-line react/react-compiler
      setSessions([first]);
    }
    setHydrated(true);
    void loadReportArchiveFromLocalRuntime().then(setArchiveRows);
  }, []);
  useEffect(() => {
    if (!hydrated) return;
    localStorage.setItem(SESSION_KEY, JSON.stringify(sessions));
    localStorage.setItem(ACTIVE_SESSION_KEY, session.id);
  }, [hydrated, session.id, sessions]);
  useEffect(() => {
    if (!hydrated) return;
    localStorage.setItem(REPORT_SCALE_KEY, reportTextScale);
  }, [hydrated, reportTextScale]);
  useEffect(() => {
    if (!hydrated) return;
    if (runStatus === 'running' && pending && runStartedAt) {
      const record: ActiveRunRecord = {
        version: 1,
        sessionId: session.id,
        pending,
        jobId,
        startedAt: runStartedAt,
        stepIndex: runStepIndex,
        completedReports: completedRunReports,
      };
      localStorage.setItem(ACTIVE_RUN_KEY, JSON.stringify(record));
      return;
    }
    localStorage.removeItem(ACTIVE_RUN_KEY);
  }, [
    hydrated,
    jobId,
    pending,
    runStartedAt,
    runStatus,
    runStepIndex,
    completedRunReports,
    session.id,
  ]);
  useEffect(() => {
    if (!hydrated) return;
    // Keep the sidebar session index synchronized with the active transcript.
    // eslint-disable-next-line react/react-compiler
    setSessions((previous) =>
      sortSessionsByActivity(
        previous.some((item) => item.id === session.id)
          ? previous.map((item) => (item.id === session.id ? session : item))
          : [session, ...previous],
      ),
    );
  }, [hydrated, session]);
  useEffect(() => {
    void Promise.allSettled([
      fetch(bridgeUrl('/market?scope=latest'), { cache: 'no-store' }).then(
        async (response) => (response.ok ? response.json() : null),
      ),
      fetch(bridgeUrl('/runtime/environment?summary=1'), { cache: 'no-store' }).then(
        async (response) => (response.ok ? response.json() : null),
      ),
      fetch(bridgeUrl('/runtime/resource-context'), { cache: 'no-store' }).then(
        async (response) => (response.ok ? response.json() : null),
      ),
    ]).then(([marketResult, environmentResult, resourceResult]) => {
      if (
        marketResult.status === 'fulfilled' &&
        marketResult.value?.status === 'ok'
      )
        setMarket(marketResult.value);
      if (environmentResult.status === 'fulfilled' && environmentResult.value)
        setEnvironment(environmentResult.value);
      if (resourceResult.status === 'fulfilled' && resourceResult.value)
        setResourceLibraryContext(resourceResult.value as Record<string, unknown>);
      setMarketLoading(false);
      setEnvironmentLoading(false);
    });
  }, []);
  useEffect(() => {
    if (runStatus !== 'running' || !runStartedAt) return;
    const updateElapsed = () =>
      setRunElapsed(Math.max(0, Math.floor((Date.now() - runStartedAt) / 1000)));
    updateElapsed();
    const timer = window.setInterval(
      updateElapsed,
      1000,
    );
    return () => window.clearInterval(timer);
  }, [runStartedAt, runStatus]);
  useEffect(() => {
    if (!hydrated) return;
    let firstFrame = 0;
    let secondFrame = 0;
    const settle = () => {
      const list = messageListRef.current;
      if (!list) return;
      // Set the scroll container directly and also use the last-message
      // anchor. The latter still works when the browser has not finalized the
      // flex layout at the first paint after hydration.
      list.scrollTop = list.scrollHeight;
      latestMessageRef.current?.scrollIntoView({
        block: 'end',
        inline: 'nearest',
        behavior: 'auto',
      });
      list.scrollTop = list.scrollHeight;
    };
    firstFrame = window.requestAnimationFrame(() => {
      secondFrame = window.requestAnimationFrame(settle);
    });
    const delayedSettle = window.setTimeout(settle, 120);
    return () => {
      window.cancelAnimationFrame(firstFrame);
      window.cancelAnimationFrame(secondFrame);
      window.clearTimeout(delayedSettle);
    };
  }, [hydrated, session.id, session.messages.length]);

  const append = useCallback(
    (message: Omit<ChatMessage, 'id' | 'createdAt'>) => {
      setSession((previous) => {
        const next = [
          ...previous.messages,
          { ...message, id: uid('message'), createdAt: iso() },
        ];
        return {
          ...previous,
          title:
            next.find((item) => item.role === 'user')?.text.slice(0, 24) ||
            previous.title,
          updatedAt: iso(),
          messages: next,
        };
      });
    },
    [],
  );
  function newSession() {
    const next = initialSession();
    setSession(next);
    setSessions((previous) =>
      sortSessionsByActivity([next, ...previous]).slice(0, 20),
    );
    setPending(null);
    setCandidates([]);
  }
  function switchSession(next: ChatSession) {
    if (runStatus === 'running') return;
    setSession({ ...next, updatedAt: iso() });
    setPending(null);
    setCandidates([]);
  }
  async function prepare(candidate: RouteCandidate, request: string) {
    setRouteLoading(true);
    setCandidates([]);
    const identity = stockIdentity(market, request);
    const base: PendingRoute = {
      skill: candidate.skill,
      request,
      stockCode: identity.code,
      stockName: identity.name,
    };
    setPending(base);
    try {
      const result = await fetchPreflight(candidate.skill.id);
      setPending((previous) =>
        previous ? { ...previous, preflight: result } : previous,
      );
      append({
        role: 'assistant',
        kind: 'route',
        text:
          '已识别为「' +
          candidate.skill.name +
          '」。本次只做本地数据预检，尚未唤醒 Harness；请在右侧确认是否运行。',
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : '技能预检失败';
      const unavailable: Preflight = {
        status: 'PREFLIGHT_UNAVAILABLE',
        error: message,
      };
      setPending({ ...base, preflight: unavailable });
      append({
        role: 'assistant',
        kind: 'route',
        text:
          '已识别为「' +
          candidate.skill.name +
          '」，但预检暂时不可用：' +
          message +
          '\\n仍可确认运行，运行结果会保留真实失败状态。',
      });
    } finally {
      setRouteLoading(false);
    }
  }
  async function preparePlan(steps: PendingRoute[], request: string) {
    setRouteLoading(true);
    setCandidates([]);
    const enrichedSteps = steps.map((step) => {
      const identity = stockIdentity(market, step.request);
      return {
        ...step,
        stockCode: identity.code,
        stockName: identity.name,
      };
    });
    const first = enrichedSteps[0];
    if (!first) return;
    setPending({ ...first, request, plan: enrichedSteps });
    try {
      const prepared = await Promise.all(
        enrichedSteps.map(async (step) => {
          try {
            return { ...step, preflight: await fetchPreflight(step.skill.id) };
          } catch (error) {
            return {
              ...step,
              preflight: {
                status: 'PREFLIGHT_UNAVAILABLE',
                error: error instanceof Error ? error.message : '技能预检失败',
              } satisfies Preflight,
            };
          }
        }),
      );
      setPending({ ...prepared[0], request, plan: prepared });
      append({
        role: 'assistant',
        kind: 'route',
        text:
          '已识别为一个 ' +
          prepared.length +
          ' 步研究计划：' +
          prepared
            .map((step, index) => index + 1 + '. ' + step.skill.name)
            .join(' → ') +
          '。已完成各步骤本地预检，尚未唤醒 Harness；请在右侧一次确认后按顺序运行。',
      });
    } finally {
      setRouteLoading(false);
    }
  }
  async function send(event?: { preventDefault: () => void }) {
    event?.preventDefault();
    const request = input.trim();
    if (!request || routeLoading || runStatus === 'running') return;
    setInput('');
    append({ role: 'user', kind: 'text', text: request });
    if (!isStockRequest(request, market)) {
      append({
        role: 'assistant',
        kind: 'text',
        text: '这个工作台只处理沪深 A 股的选股、行情、个股分析和复盘问题。\\n请换成股票代码、股票名称、板块、市场环境或具体研究任务。',
      });
      return;
    }
    const plan = routePlan(request, market);
    if (plan) {
      await preparePlan(plan, request);
      return;
    }
    const found = route(request, market);
    if (!found.length) {
      append({
        role: 'assistant',
        kind: 'text',
        text: '我识别到这是股票研究请求，但暂时没有匹配到明确技能。\\n你可以补充股票代码、研究目标，或直接说“个股分析、市场环境、盘前计划、涨停复盘、龙虎榜”。',
      });
      return;
    }
    if (found.length > 1 && found[0].score === found[1].score) {
      setCandidates(found);
      append({
        role: 'assistant',
        kind: 'route',
        text: '这句话可能对应多个股票技能。请先选择一个技能；选择后我会再做数据预检，并等待你的运行确认。',
      });
      return;
    }
    await prepare(found[0], request);
  }
  const blockedReport = useCallback(
    (reason: string, solution: string, target?: PendingRoute) => {
      const source = target || pending;
      if (!source) return null;
      const steps = source.plan?.length ? source.plan : [source];
      const missing = {
        required: Array.from(
          new Set(
            steps.flatMap((step) => missingData(step.preflight).required),
          ),
        ),
        optional: Array.from(
          new Set(
            steps.flatMap((step) => missingData(step.preflight).optional),
          ),
        ),
      };
      const label =
        steps.length > 1 ? steps.length + ' 步研究计划' : source.skill.name;
      return localReport(
        'BLOCKED',
        label + ' 暂未满足正式运行条件，本次不生成业务结论。',
        [
          reason,
          solution,
          ...missing.required.map((item) => '缺少必需数据：' + item),
          ...missing.optional.map((item) => '缺少可降级数据：' + item),
        ],
        [{ title: '处理建议', text: solution }],
        String(market?.date || market?.tradeDate || ''),
        '股票研究工作台 · ' + source.skill.category,
      );
    },
    [market, pending],
  );
  const runPending = useCallback(async (resume?: ActiveRunRecord) => {
    if ((!pending && !resume) || (runStatus === 'running' && !resume)) return;
    const current = resume?.pending || pending;
    if (!current) return;
    const steps = current.plan?.length ? current.plan : [current];
    let latestResourceContext = resourceLibraryContext || {};
    cancelRef.current = false;
    const firstStepIndex = Math.min(
      Math.max(resume?.stepIndex || 0, 0),
      Math.max(steps.length - 1, 0),
    );
    let collectedReports: CompletedRunReport[] = [...(resume?.completedReports || [])];
    runProgressFingerprintRef.current.clear();
    setRunStages([]);
    setCompletedRunReports(collectedReports);
    setRunStartedAt(resume?.startedAt || Date.now());
    setRunStatus('running');
    setRunStepIndex(firstStepIndex);
    setJobId(resume?.jobId || '');
    append({
      role: 'assistant',
      kind: 'status',
      text: resume
        ? '页面刷新后已恢复「' +
          current.skill.name +
          '」任务，正在继续读取原任务结果；计时从原任务开始时间持续计算。'
        : (steps.length > 1
            ? '已确认按顺序运行 ' +
              steps.length +
              ' 步研究计划：' +
              steps
                .map((step, index) => index + 1 + '. ' + step.skill.name)
                .join(' → ')
            : '已确认运行「' + current.skill.name + '」') +
          '。正在核对数据并启动研究任务；预计 ' +
          duration(
            steps.reduce((total, step) => total + step.skill.estimate, 0),
          ) +
          '。',
    });
    try {
      if (!market || market.status === 'missing') {
        append({
          role: 'assistant',
          kind: 'status',
          text: '运行进度 · 数据快照尚未准备好，正在生成阻塞诊断。',
        });
        const report = blockedReport(
          '尚未读取到本地最新行情快照。',
          '请先刷新本地行情，确认 TDX 日线归档可用后重试。',
          current,
        );
        if (report)
          append({
            role: 'assistant',
            kind: 'report',
            text: report.summary,
            report,
            skillName: steps.length > 1 ? '多步骤研究计划' : current.skill.name,
          });
        setRunStatus('idle');
        setRunStartedAt(null);
        setRunStepIndex(0);
        setJobId('');
        setResumeRun(null);
        setPending(null);
        return;
      }
      try {
        const response = await fetch(bridgeUrl('/runtime/resource-context'), { cache: 'no-store' });
        if (response.ok) {
          latestResourceContext = await response.json() as Record<string, unknown>;
          setResourceLibraryContext(latestResourceContext);
        }
      } catch { /* 继续使用页面缓存；Harness 输出仍需注明资源缺口。 */ }
      const marketRows = (market.allStocks || market.stocks || []).length;
      append({
        role: 'assistant',
        kind: 'status',
        text:
          '运行进度 · 数据快照已读取：' +
          marketRows +
          ' 条股票记录，日期 ' +
          dateText(String(market.date || market.tradeDate || '')) +
          '；正在检查技能数据边界。',
      });
      const blockedStep = steps.find((step) =>
        String(step.preflight?.status || '')
          .toUpperCase()
          .includes('BLOCK'),
      );
      if (blockedStep) {
        const blockedMissing = missingData(blockedStep.preflight);
        const report = blockedReport(
          blockedMissing.required.length
            ? '步骤「' +
                blockedStep.skill.name +
                '」必需数据未齐全：' +
                blockedMissing.required.join('、')
            : '技能预检返回 BLOCKED。',
          '请按缺失数据清单补齐本地行情或公开证据，再重新执行；当前仅保留阻塞诊断。',
          current,
        );
        if (report)
          append({
            role: 'assistant',
            kind: 'report',
            text: report.summary,
            report,
            skillName: steps.length > 1 ? '多步骤研究计划' : current.skill.name,
          });
        setRunStatus('idle');
        setRunStartedAt(null);
        setRunStepIndex(0);
        setJobId('');
        setResumeRun(null);
        setPending(null);
        return;
      }
      append({
        role: 'assistant',
        kind: 'status',
        text:
          '运行进度 · 数据预检已通过，' +
          steps.length +
          ' 个步骤已排入固定顺序；正在准备研究上下文。',
      });
      for (let index = firstStepIndex; index < steps.length; index += 1) {
        const step = steps[index];
        setRunStepIndex(index);
        append({
          role: 'assistant',
          kind: 'status',
          text:
            (steps.length > 1
              ? '步骤 ' +
                (index + 1) +
                '/' +
                steps.length +
                '：开始运行「' +
                step.skill.name +
                '」，前一步完成后才会进入下一步。'
              : '运行进度 · 正在准备「' +
                step.skill.name +
                '」的本地行情和研究上下文。'),
        });
        if (cancelRef.current) throw new CancelledRunError();
        const missing = missingData(step.preflight);
        const stock = findStock(market, step.request);
        const history = await loadHistory(stock);
        append({
          role: 'assistant',
          kind: 'status',
          text:
            '运行进度 · 步骤 ' +
            (index + 1) +
            '/' +
            steps.length +
            ' · 本地上下文已准备' +
            (history?.bars?.length
              ? '（历史行情 ' + history.bars.length + ' 条）'
              : '（未取得额外历史行情）') +
            '，正在提交研究任务。',
        });
        const task =
          '你正在掌财股票研究工作台中执行已获用户确认的技能“' +
          step.skill.name +
          '”（技能 ID：' +
          step.skill.id +
          '）。用户原始请求：' +
          step.request +
          '。' +
          HARNESS_JSON_SCHEMA +
          '本次是只读研究，禁止下单、撤单、自动交易和收益承诺。严格基于传入的本地行情、预检结果和上下文输出；不要虚构未传入的新闻、公告、龙虎榜、行业事实或实时盘口。预检状态为 ' +
          (step.preflight?.status || '未知') +
          '；缺少必需数据：' +
          (missing.required.join('、') || '无') +
          '；缺少可降级数据：' +
          (missing.optional.join('、') || '无') +
          '。若状态为 DEGRADED，必须在 status 和 cautions 中明确降级范围；若证据不足，输出 BLOCKED 并给出补数方案。';
        const runContext = {
          sessionId: session.id,
          planStep: index + 1,
          planLength: steps.length,
          stock: stock || {
            code: step.stockCode || '',
            name: step.stockName || '',
          },
          targetStock: {
            code: step.stockCode || safeText(stock?.code) || '',
            name: step.stockName || safeText(stock?.name) || '',
            date:
              safeText(history?.meta?.last_date) ||
              safeText(history?.meta?.lastDate) ||
              safeText(
                history?.bars?.[Math.max((history?.bars?.length || 1) - 1, 0)]?.date,
              ) ||
              safeText(market.date || market.tradeDate),
          },
          historyMeta: {
            returnedCount: history?.bars?.length || 0,
            historyCount: Number(
              history?.meta?.history_count ||
                history?.meta?.historyCount ||
                history?.bars?.length ||
                0,
            ),
            firstDate:
              safeText(history?.meta?.first_date) ||
              safeText(history?.meta?.firstDate) ||
              safeText(history?.bars?.[0]?.date),
            lastDate:
              safeText(history?.meta?.last_date) ||
              safeText(history?.meta?.lastDate) ||
              safeText(
                history?.bars?.[Math.max((history?.bars?.length || 1) - 1, 0)]?.date,
              ),
            source: history?.source || '本地日线',
          },
          history,
          preflight: step.preflight,
          request: step.request,
          environment: environment || {},
          resourceLibrary: latestResourceContext,
        };
        // The strategy page does not send selection skills straight to
        // generic Harness reasoning. It first runs the same local scoring
        // adapter, then gives that compact receipt to Harness. Keep this
        // branch in chat so Golden Ignition cannot time out while trying to
        // rediscover a full strategy from prose and a large market snapshot.
        const resumeJobId =
          resume && index === firstStepIndex ? resume.jobId : undefined;
        const onJobStarted = (startedId: string) => {
          setJobId(startedId);
          append({
            role: 'assistant',
            kind: 'status',
            text:
              '运行进度 · 步骤 ' +
              (index + 1) +
              '/' +
              steps.length +
              ' · ' +
              (resumeJobId ? '已重新连接原任务' : 'Harness 任务已启动') +
              '（' +
              startedId.slice(0, 8) +
              '…），正在等待结构化结果。',
          });
        };
        const onProgress = (incoming: RunProgressStage[]) => {
          const stages = normalizeRunProgress(incoming);
          if (!stages.length) return;
          setRunStages(stages);
          stages.forEach((stage) => {
            if (stage.status === 'pending') return;
            const fingerprint =
              index + ':' +
              step.skill.id + ':' +
              stage.key + ':' +
              stage.status + ':' +
              stage.detail;
            if (runProgressFingerprintRef.current.has(fingerprint)) return;
            runProgressFingerprintRef.current.add(fingerprint);
            append({
              role: 'assistant',
              kind: 'status',
              text:
                '步骤 ' +
                (index + 1) +
                '/' +
                steps.length +
                ' · ' +
                progressBubbleText(stage),
            });
          });
        };
        const selectionRun = isSelectionSkill(step.skill.id);
        append({
          role: 'assistant',
          kind: 'status',
          text: selectionRun
            ? '运行进度 · 正在复用原始策略评分引擎，完成候选数值回执后再交给 Harness 解读。'
            : '运行进度 · 正在调用 DeepSeek Harness，等待结构化研究结果。',
        });
        const result = selectionRun
          ? await runSelectionSkill({
              skill: step.skill,
              request: step.request,
              market,
              preflight: step.preflight,
              context: runContext,
              onStarted: onJobStarted,
              onProgress,
              cancelled: () => cancelRef.current,
              resumeJobId,
            })
          : await runHarness({
              task,
              skillId: step.skill.id,
              market: compactMarket(market),
              context: runContext,
              onStarted: onJobStarted,
              onProgress,
              cancelled: () => cancelRef.current,
              resumeJobId,
            });
        append({
          role: 'assistant',
          kind: 'status',
          text:
            '运行进度 · 步骤 ' +
            (index + 1) +
            '/' +
            steps.length +
            ' · 已收到任务回执，正在校验报告字段和数据边界。',
        });
        const parsed = normalizeHarnessOutput(result.output);
        const report = { ...parsed, status: normalizeStatus(parsed.status) };
        collectedReports = [
          ...collectedReports.filter((item) => item.stepIndex !== index),
          {
            stepIndex: index,
            skillId: step.skill.id,
            skillName: step.skill.name,
            report,
          },
        ].sort((a, b) => a.stepIndex - b.stepIndex);
        setCompletedRunReports(collectedReports);
        append({
          role: 'assistant',
          kind: 'status',
          text:
            '运行进度 · 步骤 ' +
            (index + 1) +
            '/' +
            steps.length +
            ' 已完成，结果已纳入最后一份完整报告。',
        });
        setJobId('');
      }
      const completeReport = composeCompleteChatReport(
        collectedReports,
        steps,
        String(market?.date || market?.tradeDate || ''),
      );
      const completeSkillIds = steps.map((step) => step.skill.id).join('+');
      const completeSkillNames = steps.map((step) => step.skill.name).join('、');
      const targetStocks = [...new Map(steps.map((step) => {
        const identity = stockIdentity(market, step.request);
        const stock = identity.stock;
        const code = identity.code || step.stockCode || '';
        const exchange = String(stock?.market || '').toUpperCase().slice(0, 2);
        const key = code ? `${exchange || 'XX'}${code}` : `name-${identity.name || step.stockName || 'market'}`;
        return [key, { code, market: exchange, name: identity.name || step.stockName || '' }] as const;
      }))].map(([key, value]) => ({ key, ...value })).sort((a, b) => a.key.localeCompare(b.key));
      const targetKey = targetStocks.length ? targetStocks.map((item) => item.key).join('_') : 'market';
      append({
        role: 'assistant',
        kind: 'report',
        text: completeReport.summary || completeSkillNames + ' 已完成。',
        report: completeReport,
        skillName: steps.length > 1 ? '完整研究报告' : steps[0].skill.name,
      });
      const time = iso();
      await saveReportArchive({
        id: createReportId('chat-report'),
        archiveKey: `chat:${completeReport.dataDate || market?.date || ''}:${targetKey}:${completeSkillIds}`,
        createdAt: time,
        updatedAt: time,
        date: completeReport.dataDate || String(market?.date || market?.tradeDate || ''),
        title:
          (steps.length > 1 ? '完整研究计划' : steps[0].skill.name) +
          ' · ' +
          (steps[0].stockName || steps[0].stockCode || '市场研究'),
        reportType: '聊天完整研究报告',
        generatedBy: 'DeepSeek Harness · ' + completeSkillIds,
        summary: completeReport.summary || completeSkillNames + ' 已完成。',
        dataScope: completeReport.dataScope || '股票研究工作台 · ' + completeSkillNames,
        content: {
          kind: 'chat-report',
          sessionId: session.id,
          planLength: steps.length,
          skillId: steps.length === 1 ? steps[0].skill.id : 'complete-plan',
          skillName: completeSkillNames,
          skills: steps.map((step) => ({ id: step.skill.id, name: step.skill.name })),
          targetStocks,
          request: current.request,
          status: completeReport.status,
          report: completeReport.value,
        },
        raw: JSON.stringify(completeReport.value, null, 2),
      });
      append({
        role: 'assistant',
        kind: 'status',
        text: '运行进度 · 全部研究步骤完成，只生成并归档一份完整报告。',
      });
      setArchiveRows(await loadReportArchiveFromLocalRuntime());
      setRunStatus('idle');
      setRunStartedAt(null);
      setRunStepIndex(0);
      setResumeRun(null);
      setPending(null);
      setCompletedRunReports([]);
    } catch (error) {
      if (error instanceof CancelledRunError || cancelRef.current) {
        setRunStatus('cancelled');
        setRunStages((previous) =>
          previous.map((stage) =>
            stage.status === 'running'
              ? {
                  ...stage,
                  status: 'cancelled',
                  detail: '用户已取消本次研究任务。',
                  completedAt: Date.now(),
                }
              : stage,
          ),
        );
        append({
          role: 'assistant',
          kind: 'status',
          text: '本次任务已取消。已经产生的会话内容和运行记录保留在当前会话中；如需继续，可以重新确认运行。',
        });
        window.setTimeout(() => setRunStatus('idle'), 250);
      } else {
        const message =
          error instanceof Error ? error.message : '研究任务执行失败';
        setRunStages((previous) =>
          previous.map((stage) =>
            stage.status === 'running'
              ? {
                  ...stage,
                  status: 'failed',
                  detail: message,
                  completedAt: Date.now(),
                }
              : stage,
          ),
        );
        const report = localReport(
          'FAILED',
          '本次研究任务没有形成可用业务结论。',
           [message, `请检查 Harness 凭据、${bridgeHostLabel()} 桥接服务和本地数据状态后重试。`],
          [{ title: '运行失败', text: message }],
          String(market?.date || market?.tradeDate || ''),
          '股票研究工作台 · ' + current.skill.category,
        );
        append({
          role: 'assistant',
          kind: 'report',
          text: report.summary,
          report,
          skillName: current.skill.name,
        });
        setRunStatus('idle');
      }
      setJobId('');
      setRunStartedAt(null);
      setRunStepIndex(0);
      setResumeRun(null);
    }
  }, [
    append,
    blockedReport,
    environment,
    market,
    pending,
    resourceLibraryContext,
    runStatus,
    session.id,
  ]);
  async function cancelRun() {
    cancelRef.current = true;
    if (jobId)
      await fetch(
        bridgeUrl('/agent/job/' + encodeURIComponent(jobId) + '/cancel'),
        { method: 'POST' },
      ).catch(() => undefined);
  }

  const resumeAttemptedRef = useRef(false);
  useEffect(() => {
    if (
      !hydrated ||
      !market ||
      !resumeRun ||
      runStatus !== 'running' ||
      session.id !== resumeRun.sessionId ||
      resumeAttemptedRef.current
    )
      return;
    resumeAttemptedRef.current = true;
    void runPending(resumeRun);
  }, [hydrated, market, resumeRun, runPending, runStatus, session.id]);

  const selectedSkill = pending?.skill;
  const preflight = pending?.preflight;
  const pendingSteps = pending?.plan?.length
    ? pending.plan
    : pending
      ? [pending]
      : [];
  const pendingIsPlan = pendingSteps.length > 1;
  const planMissing = {
    required: Array.from(
      new Set(
        pendingSteps.flatMap((step) => missingData(step.preflight).required),
      ),
    ),
    optional: Array.from(
      new Set(
        pendingSteps.flatMap((step) => missingData(step.preflight).optional),
      ),
    ),
  };
  const pendingEstimate = pendingSteps.reduce(
    (total, step) => total + step.skill.estimate,
    0,
  );
  const planBlocked = pendingSteps.some((step) =>
    String(step.preflight?.status || '')
      .toUpperCase()
      .includes('BLOCK'),
  );
  const preflightUnavailable = pendingSteps.some((step) =>
    String(step.preflight?.status || '')
      .toUpperCase()
      .includes('PREFLIGHT_UNAVAILABLE'),
  );
  const loadedRows = market
    ? (market.allStocks || market.stocks || []).length
    : 0;

  return (
    <main className="chat-workspace-shell">
      <aside className="chat-workspace-sidebar">
        <div className="brand">
          <span className="brand-symbol" aria-label="掌财智能体" />
          <div>
            掌财智能体<small>ZHANGCAI RESEARCH</small>
          </div>
        </div>
        <div className="chat-sidebar-section">
          <div className="chat-sidebar-label">研究工作台</div>
          <button className="chat-nav-item active">
            <LayoutDashboard size={16} />
            <span>研究对话</span>
            <span className="nav-pill">研究</span>
          </button>
          <button
            className="chat-nav-item"
            onClick={() => setArchiveOpen(true)}
          >
            <Archive size={16} />
            <span>我的报告</span>
            <span className="nav-count">{archiveRows.length}</span>
          </button>
        </div>
        <div className="chat-sidebar-section session-directory">
          <div className="chat-sidebar-label">
            <span>历史会话</span>
            <span className="directory-count">{sessions.length}</span>
          </div>
          {sessions.slice(0, 5).map((item) => (
            <button
              key={item.id}
              className="chat-session-item"
              onClick={() => switchSession(item)}
            >
              <span className="session-dot" />
              <span>{item.title || '新的研究会话'}</span>
            </button>
          ))}
        </div>
        <div className="chat-sidebar-section skill-directory">
          <div className="chat-sidebar-label">
            <span>当前研究技能</span>
            <span className="directory-count">{visibleSkillDirectory.length}</span>
          </div>
          {visibleSkillDirectory.map((skill) => (
            <button
              key={skill.id}
              className={
                'chat-skill-item ' +
                (selectedSkill?.id === skill.id ? 'selected' : '')
              }
              onClick={() => setInput('请运行' + skill.name)}
            >
              <span className="skill-icon">
                <Sparkles size={13} />
              </span>
              <span>
                <b>{skill.name}</b>
                <small>{skill.category}</small>
              </span>
            </button>
          ))}
        </div>
        <div className="chat-sidebar-bottom">
          <div className="chat-runtime-box">
            <span className="runtime-dot" />
            <div>
              <b>本地研究运行时</b>
               <small>{runtimeLabel} · {bridgeHostLabel()}</small>
            </div>
          </div>
          <button className="chat-settings-link">
            <CircleHelp size={15} />
            激活码 / 登录接口预留
          </button>
          <div className="chat-user">
            <span className="avatar">掌</span>
            <div>
              <b>本地研究空间</b>
              <small>本地运行版</small>
            </div>
            <MoreHorizontal size={16} />
          </div>
        </div>
      </aside>
      <section className="chat-workspace-main">
        <header className="chat-topbar">
          <div className="chat-breadcrumb">
            <span>工作空间</span>
            <ChevronRight size={14} />
            <strong>研究对话</strong>
          </div>
          <div className="chat-top-actions">
            <span className="preview-tag">研究工作台</span>
            <span className="chat-data-chip">
              <span
                className={
                  'status-dot ' +
                  (marketLoading
                    ? 'is-loading'
                    : market
                      ? 'is-ready'
                      : 'is-missing')
                }
              />
              {marketLoading
                ? '行情检查中'
                : market
                  ? '数据 ' + dateText(market.date || market.tradeDate)
                  : '数据待刷新'}
            </span>
            <button
              className="icon-button"
              title="刷新运行状态"
              onClick={() => window.location.reload()}
            >
              <RefreshCw size={16} />
            </button>
          </div>
        </header>
        <div className="chat-workspace">
          <div className="chat-heading">
            <div>
              <div className="eyebrow">A-SHARE RESEARCH CHAT</div>
              <h1>
                研究对话{' '}
                <span className="live-label">
                  <span />
                  确认后运行
                </span>
              </h1>
              <p>
                用自然语言唤醒股票技能，先看数据边界，再决定是否执行。
              </p>
            </div>
            <button className="secondary-button" onClick={newSession}>
              <MessageSquarePlus size={15} />
              新建会话
            </button>
          </div>
          <div className="chat-status-banner">
            <ShieldCheck size={16} />
            <span>
              研究边界：沪深 A 股 · 只读分析 · 禁止交易 · 不输出确定性收益承诺
            </span>
            <span className="banner-divider" />
            <span>
              <Database size={14} />
              {loadedRows
                ? '已加载 ' + loadedRows + ' 条本地候选'
                : '等待本地行情'}
            </span>
          </div>
          <div className="chat-columns">
            <section className="conversation-panel panel">
              <div className="conversation-head">
                <div>
                  <span className="panel-overline">
                    <History size={13} />
                    当前会话
                  </span>
                  <h2>{session.title}</h2>
                </div>
                <button
                  className="icon-button"
                  onClick={() => setArchiveOpen(true)}
                  title="查看报告归档"
                >
                  <Archive size={16} />
                </button>
              </div>
              <div className="message-list" ref={messageListRef}>
                {session.messages.map((message, index) => (
                  <div
                    key={message.id}
                    ref={
                      index === session.messages.length - 1
                        ? latestMessageRef
                        : undefined
                    }
                    className={
                      'message-row ' + message.role + ' message-' + message.kind
                    }
                  >
                    <div className="message-avatar">
                      {message.role === 'user' ? '我' : <Sparkles size={15} />}
                    </div>
                    <div className="message-body">
                      <div className="message-meta">
                        <b>{message.role === 'user' ? '你' : '掌财研究助手'}</b>
                        <span>
                          {new Date(message.createdAt).toLocaleTimeString(
                            'zh-CN',
                            { hour: '2-digit', minute: '2-digit' },
                          )}
                        </span>
                      </div>
                      {message.kind === 'report' && message.report ? (
                        <ReportCard
                          report={message.report}
                          skill={selectedSkill}
                          skillName={message.skillName}
                          textScale={reportTextScale}
                          onTextScaleChange={setReportTextScale}
                        />
                      ) : (
                        <div className="message-bubble">
                          {message.text.split('\\n').map((line, index) => (
                            <span key={index}>
                              {line}
                              {index < message.text.split('\\n').length - 1 && (
                                <br />
                              )}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {routeLoading && (
                  <div className="message-row assistant">
                    <div className="message-avatar">
                      <Sparkles size={15} />
                    </div>
                    <div className="message-body">
                      <div className="message-bubble typing">
                        <LoaderCircle size={15} className="spin" />
                        正在读取技能预检…
                      </div>
                    </div>
                  </div>
                )}
                <div />
              </div>
              <form className="chat-composer" onSubmit={send}>
                <div className="composer-hint">
                  <Sparkles size={14} />
                  <span>研究请求会先进入技能确认，不会直接执行</span>
                </div>
                <div className="composer-row">
                  <textarea
                    value={input}
                    onChange={(event) => setInput(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();
                        void send();
                      }
                    }}
                    placeholder="例如：分析 600519 最近走势并排查风险…"
                    rows={2}
                    disabled={runStatus === 'running'}
                  />
                  <button
                    className="send-button"
                    type="submit"
                    disabled={!input.trim() || runStatus === 'running'}
                    aria-label="发送"
                  >
                    <Send size={17} />
                  </button>
                </div>
                <div className="composer-examples">
                  <button
                    type="button"
                    onClick={() => setInput('分析 600519 最近走势并排查风险')}
                  >
                    个股分析
                  </button>
                  <button
                    type="button"
                    onClick={() => setInput('帮我做今天市场环境和短线情绪分析')}
                  >
                    市场情绪
                  </button>
                  <button
                    type="button"
                    onClick={() => setInput('生成今天的盘前计划')}
                  >
                    盘前计划
                  </button>
                </div>
              </form>
            </section>
            <aside className="chat-inspector">
              {candidates.length > 0 && (
                <section className="inspector-card candidate-card">
                  <div className="inspector-title">
                    <div>
                      <span className="panel-overline">
                        <Search size={13} />
                        技能候选
                      </span>
                      <h3>请选择要运行的研究技能</h3>
                    </div>
                    <span className="candidate-count">
                      {candidates.length} 个候选
                    </span>
                  </div>
                  <p className="inspector-note">
                    自然语言存在多种解释，选择技能后仍需再次确认才会运行。
                  </p>
                  <div className="candidate-list">
                    {candidates.map((candidate) => (
                      <button
                        key={candidate.skill.id}
                        className="candidate-item"
                        onClick={() =>
                          void prepare(
                            candidate,
                            session.messages.findLast(
                              (message) => message.role === 'user',
                            )?.text || '',
                          )
                        }
                      >
                        <span className="candidate-icon">
                          <Zap size={15} />
                        </span>
                        <span>
                          <b>{candidate.skill.name}</b>
                          <small>
                            {candidate.skill.category} · {candidate.reason}
                          </small>
                        </span>
                        <ChevronRight size={15} />
                      </button>
                    ))}
                  </div>
                </section>
              )}
              {pending && (
                <section className="inspector-card confirmation-card">
                  <div className="inspector-title">
                    <div>
                      <span className="panel-overline">
                        <ShieldCheck size={13} />
                        运行前确认
                      </span>
                      <h3>
                        {pendingIsPlan
                          ? '是否按顺序运行这组技能？'
                          : '是否运行这项技能？'}
                      </h3>
                    </div>
                    <span className="waiting-badge">WAITING</span>
                  </div>
                  <div className="skill-confirm-box">
                    <div className="confirm-icon">
                      <Sparkles size={18} />
                    </div>
                    <div>
                      <b>
                        {pendingIsPlan ? '多技能顺序计划' : pending.skill.name}
                      </b>
                      <small>
                        {pendingIsPlan
                          ? pendingSteps.length + ' 个步骤 · 固定顺序执行'
                          : pending.skill.category + ' · ' + pending.skill.id}
                      </small>
                    </div>
                  </div>
                  {pendingIsPlan && (
                    <div className="execution-chain">
                      {pendingSteps.map((step, index) => (
                        <span key={step.skill.id}>
                          {index > 0 ? ' → ' : ''}
                          {index + 1}. {step.skill.name}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="confirm-grid">
                    <div>
                      <span>预计耗时</span>
                      <b>
                        <Clock3 size={14} />
                        {duration(pendingEstimate)}
                      </b>
                    </div>
                    <div>
                      <span>分析对象</span>
                      <b>
                        {pendingIsPlan
                          ? pendingSteps.length + ' 个研究步骤'
                          : pending.stockName && pending.stockCode
                            ? pending.stockName + ' · ' + pending.stockCode
                            : pending.stockName ||
                              pending.stockCode ||
                              '当前 A 股市场'}
                      </b>
                    </div>
                    <div>
                      <span>数据完整性</span>
                      <b
                        className={
                          routeLoading
                            ? 'is-pending'
                            : preflightUnavailable
                              ? 'is-degraded'
                              : planMissing.required.length
                                ? 'is-blocked'
                                : 'is-ready'
                        }
                      >
                        {routeLoading
                          ? '预检中'
                          : preflightUnavailable
                            ? '预检不可用'
                            : planMissing.required.length
                              ? '必需数据缺失'
                              : '已通过'}
                      </b>
                    </div>
                    <div>
                      <span>降级情况</span>
                      <b
                        className={
                          planMissing.optional.length
                            ? 'is-degraded'
                            : 'is-ready'
                        }
                      >
                        {planMissing.optional.length ? '可能降级' : '暂无'}
                      </b>
                    </div>
                  </div>
                  {!pendingIsPlan && isIndividualStockSkill(pending.skill) && (
                    <div className="confirm-stock-identity">
                      <div>
                        <span>股票名称</span>
                        <b>{pending.stockName || '未从本地股票库匹配'}</b>
                      </div>
                      <div>
                        <span>股票代码</span>
                        <b>{pending.stockCode || '未从请求中识别'}</b>
                      </div>
                    </div>
                  )}
                  <div className="confirm-scope">
                    <CheckCircle2 size={15} />
                    <span>只读研究，不执行下单、撤单或任何交易操作。</span>
                  </div>
                  {planMissing.required.length > 0 && (
                    <div className="missing-list">
                      <b>缺少必需数据</b>
                      {planMissing.required.map((item) => (
                        <span key={item}>· {item}</span>
                      ))}
                    </div>
                  )}
                  {planMissing.optional.length > 0 && (
                    <div className="missing-list degraded">
                      <b>缺少可降级数据</b>
                      {planMissing.optional.map((item) => (
                        <span key={item}>· {item}</span>
                      ))}
                    </div>
                  )}
                  {preflight?.error && (
                    <div className="preflight-error">
                      <XCircle size={14} />
                      {preflight.error}
                    </div>
                  )}
                  {preflightUnavailable && !preflight?.error && (
                    <div className="preflight-error">
                      <XCircle size={14} />
                       至少一个步骤的本地预检暂时不可用，确认后仍以 {bridgeHostLabel()}
                       的真实运行结果为准。
                    </div>
                  )}
                  <div className="confirm-actions">
                    <button
                      className="primary-button"
                      onClick={() => void runPending()}
                      disabled={routeLoading || runStatus === 'running'}
                    >
                      <Play size={15} />
                      {runStatus === 'running'
                        ? '运行中'
                        : planBlocked
                          ? '运行阻塞诊断'
                          : pendingIsPlan
                            ? '确认按顺序运行'
                            : '确认运行技能'}
                    </button>
                    <button
                      className="secondary-button"
                      onClick={() => {
                        setPending(null);
                        setCandidates([]);
                        append({
                          role: 'assistant',
                          kind: 'text',
                          text: '已取消本次技能唤醒，尚未运行 Harness。',
                        });
                      }}
                    >
                      <X size={15} />
                      取消
                    </button>
                  </div>
                </section>
              )}
              {runStatus === 'running' && (
                <section className="inspector-card running-card">
                  <div className="inspector-title">
                    <div>
                      <span className="panel-overline">
                        <LoaderCircle size={13} className="spin" />
                        执行中
                      </span>
                      <h3>{selectedSkill?.name || '研究任务'}</h3>
                    </div>
                    <span className="running-badge">RUNNING</span>
                  </div>
                  <div className="running-time">
                    <strong>
                      {String(Math.floor(runElapsed / 60)).padStart(2, '0')}:
                      {String(runElapsed % 60).padStart(2, '0')}
                    </strong>
                    <span>
                      已运行 · 预计 {duration(
                        selectedSkill?.estimate || DEFAULT_ESTIMATE_SECONDS,
                      )}
                    </span>
                  </div>
                  <div className="progress-line">
                    <span
                      style={{
                        width:
                          Math.min(
                            94,
                            Math.max(
                              8,
                              (runElapsed /
                                Math.max(
                                  selectedSkill?.estimate ||
                                    DEFAULT_ESTIMATE_SECONDS,
                                  1,
                                )) *
                                100,
                            ),
                          ) + '%',
                      }}
                    />
                  </div>
                  {runStages.length > 0 && (
                    <div className="run-stage-list" aria-label="研究阶段">
                      <div className="run-stage-heading">研究阶段</div>
                      {runStages.map((stage) => (
                        <div
                          className={'run-stage-row ' + stage.status}
                          key={stage.key}
                        >
                          <span className="run-stage-marker">
                            {stage.status === 'completed' ? (
                              <Check size={12} />
                            ) : stage.status === 'running' ? (
                              <LoaderCircle size={12} className="spin" />
                            ) : stage.status === 'failed' || stage.status === 'cancelled' ? (
                              <XCircle size={12} />
                            ) : (
                              <Clock3 size={12} />
                            )}
                          </span>
                          <span className="run-stage-copy">
                            <b>{stage.label}</b>
                            <small>
                              {stage.detail || progressStatusText(stage.status)}
                            </small>
                          </span>
                          <time>
                            {stageClock(stage.completedAt || stage.startedAt)}
                          </time>
                        </div>
                      ))}
                    </div>
                  )}
                  <p className="inspector-note">
                    Harness
                    正在基于已确认的本地数据生成结构化研究结果。你可以取消，已产生的会话内容会保留。
                  </p>
                  <button
                    className="danger-outline"
                    onClick={() => void cancelRun()}
                  >
                    <XCircle size={15} />
                    取消当前任务
                  </button>
                </section>
              )}
              {!pending && runStatus !== 'running' && (
                <section className="inspector-card empty-inspector">
                  <div className="empty-orbit">
                    <PanelRight size={20} />
                  </div>
                  <h3>确认区</h3>
                  <p>
                    发送股票研究问题后，这里会显示技能候选、预计耗时、数据完整性和运行确认。
                  </p>
                  <div className="empty-steps">
                    <div>
                      <span>01</span>自然语言识别
                    </div>
                    <div>
                      <span>02</span>数据预检和确认
                    </div>
                    <div>
                      <span>03</span>生成并归档报告
                    </div>
                  </div>
                </section>
              )}
              <section className="inspector-card runtime-card">
                <div className="inspector-title">
                  <div>
                    <span className="panel-overline">
                      <Database size={13} />
                      运行环境
                    </span>
                    <h3>本地数据状态</h3>
                  </div>
                  <button
                    className="icon-button"
                    onClick={() => window.location.reload()}
                  >
                    <RefreshCw size={14} />
                  </button>
                </div>
                <div className="runtime-row">
                  <span>Harness</span>
                  <b
                    className={
                      runtimeLabel === 'Harness 就绪' ? 'is-ready' : ''
                    }
                  >
                    {environmentLoading
                      ? '检查中'
                      : safeText(environment?.harness?.status) || '未知'}
                  </b>
                </div>
                <div className="runtime-row">
                  <span>通达信 / TDX</span>
                  <b>
                    {environmentLoading
                      ? '检查中'
                      : safeText(environment?.tdx?.status) || '未知'}
                  </b>
                </div>
                <div className="runtime-row">
                  <span>最近行情</span>
                  <b>{dateText(market?.date || market?.tradeDate)}</b>
                </div>
                <div className="runtime-foot">
                  <Check size={13} />
                  仅展示本地可验证数据
                </div>
              </section>
            </aside>
          </div>
          <footer className="chat-footer">
            <span>
              <span className="footer-dot" />
              独立研究工作台
            </span>
            <span>掌财投研工作空间</span>
            <span>报告自动归档到本地运行时</span>
          </footer>
        </div>
      </section>
      {archiveOpen && (
        <dialog open className="archive-overlay">
          <button
            type="button"
            className="archive-backdrop"
            aria-label="关闭报告弹层"
            onClick={() => {
            setArchiveOpen(false);
            setSelectedArchive(null);
            }}
          />
          <div className="archive-drawer">
            <div className="archive-head">
              <div>
                <span className="panel-overline">
                  <Archive size={13} />
                  本地归档
                </span>
                <h2>我的研究报告</h2>
              </div>
              <button
                className="icon-button"
                onClick={() => {
                  setArchiveOpen(false);
                  setSelectedArchive(null);
                }}
              >
                <X size={17} />
              </button>
            </div>
            {selectedArchive ? (
              <div className="archive-detail">
                <button
                  className="back-link"
                  onClick={() => setSelectedArchive(null)}
                >
                  <ChevronRight size={14} className="back-icon" />
                  返回报告列表
                </button>
                <h3>{selectedArchive.title}</h3>
                <p className="archive-detail-meta">
                  {dateText(selectedArchive.date)} ·{' '}
                  {selectedArchive.reportType} · {selectedArchive.generatedBy}
                </p>
                <ReportCard
                  report={normalizeHarnessOutput(
                    selectedArchive.raw ||
                      JSON.stringify(selectedArchive.content || {}),
                  )}
                  skillName={safeText(
                    (selectedArchive.content as Record<string, unknown>)
                      ?.skillName,
                  )}
                  textScale={reportTextScale}
                  onTextScaleChange={setReportTextScale}
                />
              </div>
            ) : (
              <div className="archive-list">
                {archiveRows.length ? (
                  archiveRows.map((row) => (
                    <button
                      className="archive-row"
                      key={row.id}
                      onClick={() => setSelectedArchive(row)}
                    >
                      <span className="archive-row-icon">
                        <FileText size={15} />
                      </span>
                      <span>
                        <b>{row.title}</b>
                        <small>
                          {dateText(row.date)} · {row.summary || '暂无摘要'}
                        </small>
                      </span>
                      <ChevronRight size={15} />
                    </button>
                  ))
                ) : (
                  <div className="archive-empty">
                    <Archive size={24} />
                    <b>还没有归档报告</b>
                    <p>确认并完成一次技能运行后，报告会自动保存到本地。</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </dialog>
      )}
    </main>
  );
}
