'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import type { CSSProperties, ReactNode } from 'react';
import {
  ArrowUpRight,
  Check,
  Database,
  Download,
  FileText,
  FolderOpen,
  Info,
  Layers,
  LoaderCircle,
  RefreshCw,
  Search,
  Sparkles,
  Star,
  TableProperties,
  Target,
  Trash2,
  Workflow,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { bridgeHostLabel, bridgeUrl, isDesktopRuntime } from '@/lib/bridge-url';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import skill14Catalog from '@/config/skill14-catalog.json';
import strategyCatalog from '@/lib/strategy-catalog.json';
import type { Board, IntradayProxy, Stock } from './page';
import {
  createReportId,
  deleteArchivedReport,
  loadReportArchive,
  loadReportArchiveFromLocalRuntime,
  shouldShowInMyReports,
  reportArchiveChangedEvent,
  saveReportArchive,
  type ReportArchiveRecord,
} from '@/lib/report-archive';
import { getDailyDataRefreshStatus, getDailyIndexInitializationStatus, getHarnessTasks, getSupplementalDataRefreshStatus, getUnifiedDataArchiveStatus, getUnifiedDataVerificationStatus, resumeHarnessTask, runHarnessInBackground, startDailyDataRefresh, startDailyIndexInitialization, startSupplementalDataRefresh, startUnifiedDataArchive, startUnifiedDataVerification, type HarnessTask } from '@/lib/harness-tasks';
import { HARNESS_JSON_SCHEMA, normalizeHarnessOutput, type HarnessTable } from '@/lib/harness-output';
import { closeDateLabel, dateLabel as marketDateLabel } from './market-display';

type Skill = {
  id: string;
  name: string;
  alias: string;
  group: string;
  dependencies: string[];
  entry: string;
  state: string;
  note: string;
};
type SkillPreflightResult = {
  status?: string;
  required_missing?: string[];
  optional_missing?: string[];
  degraded_missing?: string[];
  minute_data?: { status?: string; requirement?: string; purpose?: string; packaged?: boolean; file_count?: number; reason?: string };
  degrade_policy?: string;
  execution_note?: string;
  [key: string]: unknown;
};
type RankedStock = Pick<
  Stock,
  'code' | 'name' | 'pct' | 'amount' | 'close' | 'market'
>;
type SelectionCandidate = RankedStock & {
  score: number;
  wave: string;
  primary_model?: string;
  primary_model_candidate?: string;
  youzi: string;
  institution: string;
  risk: string;
  score_source: string;
  formula_status: string;
  formula_evidence: Record<string, unknown>;
  strategy_score?: number | null;
  strategy_score_status?: string;
  strategy_score_source?: string;
  strategy_missing?: string[];
  strategy_fields?: Record<string, unknown>;
};
type StrategyScoreResponse = {
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
type BatchFormulaItem = {
  formula?: string;
  tq_formula?: string;
  ok?: boolean;
  results?: Record<string, Record<string, unknown>>;
  error?: string;
};
type BatchFormulaResponse = {
  status?: string;
  formulas?: BatchFormulaItem[];
  failed_formulas?: string[];
};
type SingleSignalResult = {
  status?: string;
  error?: string;
  input_symbol?: string;
  analysis_symbol?: string;
  signal_status?: string;
  ignition_signal?: boolean;
  latest_trading_date?: string;
  lookback_trading_days?: number;
  local_daily?: Record<string, unknown>;
  tdx_formula?: {
    ok?: boolean;
    public_name?: string;
    runtime_name?: string;
    symbol?: string;
    fields?: Record<string, unknown>;
    current_triggered?: boolean;
  };
  data_sources?: Record<string, unknown>;
  risk_boundary?: string[];
  result_path?: string;
  elapsed_ms?: number;
  artifact?: Record<string, unknown>;
};

function formulaText(value: unknown): string {
  if (Array.isArray(value)) {
    return value.map((item) => formulaText(item)).filter(Boolean).at(-1) || '';
  }
  if (value == null) return '';
  return String(value).trim();
}

function formulaField(row: Record<string, unknown> | undefined, keys: string[]): string {
  if (!row) return '';
  for (const key of keys) {
    const value = formulaText(row[key]);
    if (value) return value;
  }
  return '';
}

function formulaNumber(value: string): number | null {
  const parsed = Number(String(value || '').replace(/,/g, ''));
  return Number.isFinite(parsed) ? parsed : null;
}

function bounded(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

function selectionSymbol(stock: RankedStock) {
  return `${stock.code}.${String(stock.market || '').toUpperCase()}`;
}

function selectionVenueRisk(stock: RankedStock) {
  if (/^(300|301)/.test(stock.code)) return '创业板';
  if (/^688/.test(stock.code)) return '科创板';
  if (/^(4|8|920)/.test(stock.code)) return '北交所';
  return '主板';
}

function baseSelectionScore(stock: Stock, pool: Stock[]) {
  const maxPct = Math.max(1, ...pool.map((item) => Math.max(0, Number(item.pct) || 0)));
  const maxAmount = Math.max(1, ...pool.map((item) => Number(item.amount) || 0));
  const history = [...(Array.isArray(stock.history) ? stock.history : []), stock]
    .map((item) => Number(item.close))
    .filter((item) => Number.isFinite(item) && item > 0);
  const first = history[0] || stock.close;
  const last = history.at(-1) || stock.close;
  const trend = last >= first ? 10 : 2;
  const limit = Number(stock.limitStreak || 0) > 0
    ? 10
    : Number(stock.pct) >= Number(stock.limitPct || 10) - 0.5
      ? 8
      : 0;
  return Math.round(
    bounded((Math.max(0, Number(stock.pct) || 0) / maxPct) * 25, 0, 25)
      + bounded((Number(stock.amount) || 0) / maxAmount * 15, 0, 15)
      + trend
      + limit,
  );
}

function enrichSelectionCandidate(
  stock: Stock,
  pool: Stock[],
  batch: BatchFormulaResponse | null,
  formulaError = '',
): SelectionCandidate {
  const symbol = selectionSymbol(stock);
  const items = Array.isArray(batch?.formulas) ? batch.formulas : [];
  const formulaMap = new Map(items.map((item) => [String(item.formula || ''), item]));
  const read = (name: string) => formulaMap.get(name)?.results?.[symbol];
  const daniu = read('大牛线4.0');
  const feilong = read('飞龙在天');
  const youzi = read('游资资金监控');
  const institution = read('机构资金监控');
  const daniuSignal = formulaField(daniu, ['OUTPUT61', 'OUTPUT55']);
  const waveSignal = formulaField(feilong, ['OUTPUT6']);
  const waveValue = formulaField(feilong, ['波']);
  const sectionValue = formulaField(feilong, ['段']);
  const buyIntent = formulaField(youzi, ['买方意向']);
  const aaa = formulaField(youzi, ['AAA']);
  const ddd = formulaField(youzi, ['DDD']);
  const institutionIn = formulaField(institution, ['机构大单进']);
  const institutionOut = formulaField(institution, ['机构大单出']);
  const largeOrder = formulaField(institution, ['大单动向']);
  const formulaOk = items.length >= 5 && items.every((item) => item.ok && item.results?.[symbol]);
  const ignition = /点火|买/.test(`${daniuSignal} ${formulaField(daniu, ['OUTPUT55'])}`);
  const waveBoost = /主升|启动|上升|多头/.test(waveSignal) ? 12 : /回落|调整|空头/.test(waveSignal) ? -4 : 0;
  const buyBoost = bounded((formulaNumber(buyIntent) || 0) * 1.5, 0, 8);
  const institutionBoost = bounded((formulaNumber(largeOrder) || 0) * 1.5, 0, 5);
  const score = Math.round(bounded(
    baseSelectionScore(stock, pool)
      + (ignition ? 15 : 0)
      + (formulaNumber(formulaField(daniu, ['OUTPUT59'])) || 0) * 4
      + (formulaNumber(formulaField(daniu, ['OUTPUT60'])) || 0) * 4
      + waveBoost
      + buyBoost
      + institutionBoost,
    0,
    100,
  ));
  const wave = waveSignal
    ? `${waveSignal}${waveValue || sectionValue ? `（波${waveValue || '—'} / 段${sectionValue || '—'}）` : ''}`
    : historyTrendText(stock);
  const youziText = buyIntent || aaa || ddd
    ? `买方意向 ${buyIntent || '—'}；AAA ${aaa || '—'}；DDD ${ddd || '—'}`
    : `未执行（${formulaError || '本地 TDX 回执未提供'}）`;
  const institutionText = institutionIn || institutionOut || largeOrder
    ? `机构大单进 ${institutionIn || '—'}；机构大单出 ${institutionOut || '—'}；大单动向 ${largeOrder || '—'}`
    : institution
      ? '公式已执行；机构资金字段未返回值（源端无值）'
      : `未执行（${formulaError || '本地 TDX 回执未提供'}）`;
  const risks = [selectionVenueRisk(stock)];
  if (/ST/i.test(stock.name)) risks.push('ST');
  if (Number(stock.pct) >= Number(stock.limitPct || 10) - 0.5) risks.push(`接近涨停阈值 ${stock.limitPct || 10}%`);
  if (formulaOk && !ignition) risks.push('大牛线未显示点火');
  if (!formulaOk) risks.push(`五公式${formulaError ? `未完整执行：${formulaError}` : '回执不完整'}`);
  return {
    code: stock.code,
    name: stock.name,
    close: stock.close,
    pct: stock.pct,
    amount: stock.amount,
    market: stock.market,
    score,
    wave,
    youzi: youziText,
    institution: institutionText,
    risk: risks.join('；'),
    score_source: '本地日线 + TDX 五公式复合分（网页适配层）',
    formula_status: formulaOk ? '五公式已执行' : `五公式${formulaError ? `异常：${formulaError}` : '部分可用'}`,
    formula_evidence: {
      symbol,
      daniu_signal: daniuSignal || '—',
      ignition,
      wave_signal: waveSignal || '—',
      wave: waveValue || '—',
      section: sectionValue || '—',
      youzi: { buy_intent: buyIntent || '—', AAA: aaa || '—', DDD: ddd || '—' },
      institution: { in: institutionIn || '—', out: institutionOut || '—', large_order: largeOrder || '—' },
      status: formulaOk ? 'available' : 'partial',
    },
  };
}

function historyTrendText(stock: Stock) {
  const history = [...(Array.isArray(stock.history) ? stock.history : []), stock]
    .map((item) => Number(item.close))
    .filter((item) => Number.isFinite(item) && item > 0);
  const first = history[0] || stock.close;
  const last = history.at(-1) || stock.close;
  return `${last >= first ? '日线上行' : '日线回落'}（飞龙公式未返回文字信号）`;
}

function strategyScoreCandidate(
  stock: Stock,
  raw: Record<string, unknown> | undefined,
  strategyId: string,
  scoreReceipt: StrategyScoreResponse,
): SelectionCandidate {
  const row = raw || {};
  const numberValue = (...keys: string[]) => {
    for (const key of keys) {
      const value = Number(row[key]);
      if (Number.isFinite(value)) return value;
    }
    return null;
  };
  const textValue = (...keys: string[]) => {
    for (const key of keys) {
      const value = formulaText(row[key]);
      if (value) return value;
    }
    return '';
  };
  const scoreComponents = row.score_components && typeof row.score_components === 'object'
    ? row.score_components as Record<string, unknown>
    : {};
  const modelScores = row.model_scores && typeof row.model_scores === 'object'
    ? row.model_scores as Record<string, unknown>
    : {};
  const modelStates = row.model_states && typeof row.model_states === 'object'
    ? row.model_states as Record<string, unknown>
    : {};
  const modelDiagnostics = Object.entries(modelStates).map(([name, value]) => ({
    name,
    state: value && typeof value === 'object' ? value as Record<string, unknown> : {},
  }));
  const actualScore = numberValue('score', 'final_score', 'short_burst_score', 'primary_score', 'model_c_score', 'model_a_score', 'model_b_score');
  const missing = Array.isArray(row.missing) ? row.missing.map(String) : (scoreReceipt.missing || []).map(String);
  let wave = '';
  let primaryModel = '';
  let primaryModelCandidate = '';
  let youzi = '';
  let institution = '';
  let risk = '';
  if (strategyId === 'golden-ignition-v8') {
    const a = numberValue('model_a_score');
    const b = numberValue('model_b_score');
    const c = numberValue('model_c_score');
    wave = `阶段 ${textValue('golden_stage') || '未命中'} · A ${a == null ? '—' : a.toFixed(1)} / B ${b == null ? '—' : b.toFixed(1)} / C ${c == null ? '—' : c.toFixed(1)}`;
    youzi = `模型B弱转强 ${b == null ? '—' : b.toFixed(1)}`;
    institution = `模型C黄金点火 ${c == null ? '—' : c.toFixed(1)}`;
    risk = textValue('golden_fail_reasons') || (row.final_pass ? 'V8三模型均未通过' : 'V8硬条件未通过');
  } else if (strategyId === 'short-burst-score-v5') {
    wave = `${textValue('stage') || '阶段未知'} · ${textValue('position') || '地位未知'} · ${textValue('overheat') || '透支未知'}`;
    youzi = `资金质量 ${formulaText(scoreComponents['资金质量']) || '—'}`;
    institution = `资金弹性 ${formulaText(scoreComponents['资金弹性']) || '—'}`;
    risk = (Array.isArray(row.hard_reject_reasons) ? row.hard_reject_reasons.map(String).join('；') : '') || textValue('conclusion') || '无硬否决回执';
  } else {
    const labels = Array.isArray(row.model_labels) ? row.model_labels.map(String).join('、') : '';
    const diagnosticTriggered = modelDiagnostics.filter(({ state }) => state.status === 'TRIGGERED').map(({ name }) => name).join('、');
    const triggered = labels || diagnosticTriggered;
    const hasUnknownEnvironment = modelDiagnostics.some(({ state }) => state.core === true && (state.environment === null || state.environment === undefined));
    const hasCore = modelDiagnostics.some(({ state }) => state.core === true);
    const rejectReasons = Array.isArray(row.reject_reasons)
      ? row.reject_reasons.map(String).filter(Boolean)
      : [];
    const unknownModels = modelDiagnostics.filter(({ state }) => state.core === true && (state.environment === null || state.environment === undefined)).map(({ name }) => name);
    const gateReason = hasUnknownEnvironment
      ? `行业环境未闭合${unknownModels.length ? `（${unknownModels.join('、')}）` : ''}`
      : hasCore
        ? '核心结构已计算，环境/评分门未通过'
        : rejectReasons.length
          ? `核心结构未触发（${rejectReasons.slice(0, 2).join('；')}）`
          : '核心结构未触发';
    const scoreText = Object.entries(modelScores).map(([key, value]) => `${key} ${formulaText(value) || '—'}`).join('；');
    primaryModel = textValue('primary_model');
    primaryModelCandidate = textValue('primary_model_candidate');
    wave = triggered ? `触发：${triggered}` : `未触发 · ${gateReason}`;
    youzi = scoreText ? `模型分量 ${scoreText}` : `四模型评分 ${actualScore == null ? '—' : actualScore.toFixed(1)}`;
    const stateText = modelDiagnostics.map(({ name, state }) => `${name}:${String(state.status || 'UNKNOWN')}`).join('；');
    institution = `共振 ${formulaText(row.resonance_count) || '0'} · ${textValue('market_state') || '市场状态未知'}${stateText ? ` · ${stateText}` : ''}`;
    risk = rejectReasons.join('；') || '量化模型未授权生产';
  }
  const riskWithMissing = missing.length ? `${risk}；缺失：${missing.slice(0, 3).join('、')}` : risk;
  return {
    code: stock.code,
    name: stock.name,
    close: stock.close,
    pct: stock.pct,
    amount: stock.amount,
    market: stock.market,
    score: actualScore == null ? 0 : actualScore,
    wave,
    primary_model: primaryModel || undefined,
    primary_model_candidate: primaryModelCandidate || undefined,
    youzi,
    institution,
    risk: riskWithMissing,
    score_source: String(row.score_source || (typeof scoreReceipt.score_source === 'string' ? scoreReceipt.score_source : '原始策略引擎本地适配')),
    formula_status: String(row.score_status || scoreReceipt.score_status || 'UNKNOWN'),
    formula_evidence: row,
    strategy_score: actualScore,
    strategy_score_status: String(row.score_status || scoreReceipt.score_status || 'UNKNOWN'),
    strategy_score_source: String(row.score_source || ''),
    strategy_missing: missing,
    strategy_fields: row,
  };
}

async function enrichSelectionCandidates(candidates: Stock[], pool: Stock[]) {
  const fallback = (error = '') => candidates.map((stock) => enrichSelectionCandidate(stock, pool, null, error));
  if (!candidates.length) return [];
  try {
    const response = await fetch(bridgeUrl('/stock/quick/batch'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbols: candidates.map(selectionSymbol) }),
      cache: 'no-store',
    });
    const body = await response.json().catch(() => ({})) as BatchFormulaResponse & { error?: string };
    if (!response.ok && response.status !== 207) throw new Error(body.error || `批量五公式服务返回 ${response.status}`);
    return candidates.map((stock) => enrichSelectionCandidate(stock, pool, body, body.failed_formulas?.length ? body.failed_formulas.join('、') : ''));
  } catch (error) {
    return fallback(error instanceof Error ? error.message : '批量五公式服务不可用');
  }
}

function reconcileSelectionHarnessOutput(raw: string, candidates: SelectionCandidate[], date: string, scoreReceipt?: StrategyScoreResponse) {
  const parsed = normalizeHarnessOutput(raw);
  const value = parsed.value && typeof parsed.value === 'object' ? { ...parsed.value } : {};
  const isQuant = scoreReceipt?.strategy_id === 'quant-production-v65'
    || candidates.some((candidate) => candidate.strategy_fields?.model_states);
  const localRows = candidates.map((candidate, index) => [
    String(index + 1),
    candidate.code,
    candidate.name,
    String(candidate.score),
    candidate.wave,
    ...(isQuant ? [candidate.primary_model ? `已触发：${candidate.primary_model}` : candidate.primary_model_candidate ? `待闭合：${candidate.primary_model_candidate}` : '无主模型'] : []),
    candidate.youzi,
    candidate.institution,
    candidate.risk,
  ]);
  const tables = Array.isArray(value.tables) ? [...value.tables] as Record<string, unknown>[] : [];
  const topIndex = tables.findIndex((table) => String(table?.title || '').includes('Top') || String(table?.title || '').includes('候选'));
  const topTable = {
    ...(topIndex >= 0 ? tables[topIndex] : {}),
    title: 'Top 候选',
    columns: isQuant
      ? ['排名', '代码', '名称', '评分', '波段', '主模型', '游资', '机构', '风险']
      : ['排名', '代码', '名称', '评分', '波段', '游资', '机构', '风险'],
    rows: localRows,
  };
  if (topIndex >= 0) tables[topIndex] = topTable;
  else tables.unshift(topTable);
  const cautions = Array.isArray(value.cautions) ? value.cautions.map(String) : [];
  const localNote = 'Top 候选的评分字段已由对应原始策略引擎在本地日线候选上计算；Harness 负责解释、缺失项和风险边界，不得用涨幅或成交额替代策略评分。';
  if (!cautions.includes(localNote)) cautions.unshift(localNote);
  const missing = Array.isArray(scoreReceipt?.missing) ? scoreReceipt.missing.map(String).filter(Boolean) : [];
  if (missing.length) {
    const missingNote = `本次策略评分缺失部分（已降级，不代表生产授权）：${missing.join('；')}`;
    if (!cautions.includes(missingNote)) cautions.unshift(missingNote);
  }
  return JSON.stringify({
    ...value,
    status: String(value.status || parsed.status || 'COMPLETED'),
    summary: String(value.summary || parsed.summary || '本地候选与 TDX 五公式分析已完成。'),
    data_date: String(value.data_date || parsed.dataDate || date),
    data_scope: String(value.data_scope || parsed.dataScope || `本地 TDX 日线 ${date} · Top${candidates.length} · 五公式回执`),
    cautions,
    tables,
  });
}
type PriorLimitUpStats = {
  previousDate?: string;
  count?: number;
  todayAvgPct?: number | null;
  todayUp?: number;
  todayDown?: number;
  todayFlat?: number;
};
type DataAvailability = {
  item: string;
  status: '可用' | '推导' | '按需' | '缺失';
  evidence: string;
  solution: string;
};
type SupplementalSummary = {
  status?: string;
  path?: string;
  date?: string;
  generatedAt?: string;
  coverage?: Record<string, boolean>;
  indexSymbolCount?: number;
  lhbRecordCount?: number;
  lhbMarketRecordCount?: number;
  marginRecordCount?: number;
  marginExactDate?: number;
  marginLatestAvailableDate?: string;
};
type Market = {
  date: string;
  total: number;
  currentCount: number;
  staleCount: number;
  up: number;
  down: number;
  flat: number;
  amount: number;
  importedAt: string;
  indices: Stock[];
  stocks: Stock[];
  allStocks?: Stock[];
  tdxLimitUpCodes?: string[];
  tdxLimitUpFiles?: string[];
  tdxLimitDownCodes?: string[];
  priorLimitUpCodes?: string[];
  priorLimitUpStats?: PriorLimitUpStats;
  sectors?: Board[];
  conceptBoards?: Board[];
  intradayProxy?: IntradayProxy;
  dataSources?: Record<string, unknown>;
  supplemental?: SupplementalSummary;
  quality?: string;
  dataQuality?: string;
  degraded?: boolean;
  publicLhbRecords?: { SECURITY_CODE?: string; SECURITY_NAME_ABBR?: string; TRADE_DATE?: string; BILLBOARD_NET_AMT?: number; BILLBOARD_BUY_AMT?: number; BILLBOARD_SELL_AMT?: number; EXPLAIN?: string }[];
};
type Theme = {
  name: string;
  tag: string;
  count: number;
  avgPct: number;
  amount: number;
  leaders: Pick<Stock, 'code' | 'name' | 'pct' | 'amount' | 'close' | 'market'>[];
  color: string;
};
type LimitCandidate = {
  stock: Stock;
  limitPct: number;
  streak: number;
  currentPct: number;
  confirmed: boolean;
};
type Report = {
  title: string;
  generatedBy: string;
  date: string;
  source: string;
  scope: string;
  summary: string;
  metrics: { label: string; value: string; detail: string }[];
  indices: Stock[];
  themes: Theme[];
  ladder: LimitCandidate[];
  gainLeaders: RankedStock[];
  amountLeaders: RankedStock[];
  lossLeaders: RankedStock[];
  limitDownCandidates: RankedStock[];
  priorLimitUpStats?: PriorLimitUpStats;
  sectors: Board[];
  conceptBoards: Board[];
  intradayProxy?: IntradayProxy;
  availability: DataAvailability[];
  cautions: string[];
  actions: string[];
  raw?: string;
  aiPresentation?: {
    headline: string;
    findings: { title: string; text: string }[];
    tables?: HarnessTable[];
    jsonValid?: boolean;
    parseError?: string;
  };
};
type StrategyRun = {
  busy: boolean;
  output: string;
  harnessOutput: string;
  status: string;
  phase: string;
  startedAt: number | null;
  elapsed: number;
  structured?: StructuredStrategy | null;
  receipt?: Record<string, unknown> | null;
};

function strategyRunHasReport(run?: StrategyRun) {
  return Boolean(run && !run.busy && run.phase === 'completed' && (run.harnessOutput || run.structured));
}

function strategyRunHasFailure(run?: StrategyRun) {
  return Boolean(run && !run.busy && !strategyRunHasReport(run) && (
    run.phase === 'strategy_error' || run.phase === 'harness_error' || run.phase === 'resume_error' ||
    run.status === 'ERROR' || run.status === 'HARNESS_ERROR'
  ));
}
type StrategyCatalogItem = {
  id: string;
  dataStatus: 'available' | 'partial' | 'missing';
  missingData: string[];
  dataNote: string;
  businessEntry: string;
  businessHash: string;
  legacyEntryHash: string;
  minuteData?: { mode?: string; purpose?: string };
};

const groupNames: Record<string, string> = {
  selection: '策略选股',
  mainline: '主线追踪',
  ladder: '涨停与连板',
  capital: '资金透视',
  research: '个股研究',
  watchlist: '我的工作台',
  reports: '复盘与报告',
  'my-reports': '我的报告',
  settings: '数据与底层能力',
};
const skill14AssetNames: Record<string, string> = {
  tdx_daily_history: '本地日线快照',
  security_master: '证券基础资料',
  limit_up_pool: '涨停池快照',
  lhb_data: '龙虎榜原始快照',
  public_research: '公开资讯与公告证据',
  tdx_tq_formula: '通达信 TQ 公式现场证据',
  tdx_formula_source_archive: '通达信公式源归档',
  unified_source_manifest: '统一数据源落盘清单',
  unified_source_verification: '统一数据源落盘校验',
  package_source_inventory: '行情能力包来源目录',
  execution_evidence: '任务回执与报告',
};
const skill14Groups: Record<string, string> = {
  'individual-stock-analysis-v31': 'research',
  'golden-ignition-v8': 'selection',
  'limit-advance-v44': 'ladder',
  'leader-deep-research': 'mainline',
  'unified-shortterm-score-v4': 'research',
  'limit-up-review': 'ladder',
  'short-burst-score-v5': 'selection',
  'short-term-sentiment-v22': 'mainline',
  'quant-production-v65': 'selection',
  'lhb-postmarket-v43': 'capital',
  'market-environment-v5': 'mainline',
  'market-data-capabilities': 'settings',
  'morning-intelligence-plan': 'reports',
  'workbuddy-evolution-v22': 'settings',
};
const skills: Skill[] = skill14Catalog.skills.map((skill) => ({
  id: skill.id,
  name: skill.name,
  alias: `${skill.mode} · ${skill.category}`,
  group: skill14Groups[skill.id] || 'settings',
  dependencies: [...new Set([...skill.required, ...skill.optional])].map((asset) => skill14AssetNames[asset] || asset),
  entry: '本地 14 技能数据预检',
  state: '已适配本地预检',
  note: `${skill.summary} ${skill.degrade}`,
}));
const d = (s: string) => marketDateLabel(s);
const p = (n: number) => `${n > 0 ? '+' : ''}${n.toFixed(2)}%`;
const money = (n: number) => `${(n / 1e8).toFixed(2)} 亿`;
type CapitalRawSource = { status?: string; data?: { records?: Record<string, unknown>[]; result?: { data?: Record<string, unknown>[] } } };
type CapitalSnapshot = { date?: string; fetchedAt?: string; sources?: Record<string, CapitalRawSource> };
type CapitalRow = { code: string; name: string; net: number; buy: number; sell: number; reason: string };
const dataSourceLabels: Record<string, string> = {
  'tdx-local': '通达信本地日线',
  eastmoney: '东方财富行情接口',
  lianban: '连板网涨停/连板',
  akshare: 'AkShare 聚合接口',
  tencent: '腾讯行情接口',
  sina: '新浪行情接口',
  baidu: '百度股市通',
  ths: '同花顺接口',
  iwencai: '同花顺问财',
  cls: '财联社',
  baostock: 'BaoStock',
  sw: '申万行业数据',
  cninfo: '巨潮资讯',
  'exchange-official': '交易所官方',
  macro: '宏观数据接口',
  'public-web': '公开网页来源',
  'eastmoney-news': '东方财富快讯',
  'sina-financial': '新浪财务三表',
  'tencent-share-capital': '腾讯流通股本/总股本',
  'tdx-index-daily': '通达信指数日线',
  'longhubang-snapshot': '龙虎榜统一快照',
  'eastmoney-margin': '东方财富融资融券',
  eastmoneyLimitUp: '东方财富涨停池',
  eastmoneyLhb: '东方财富龙虎榜',
  akshareLhb: 'AkShare 龙虎榜',
  akshareLhbSina: 'AkShare 新浪龙虎榜',
  akshareLhbStockStatistic: 'AkShare 龙虎榜统计',
  akshareLimitUpPool: 'AkShare 涨停池',
  akshareLhbStockDetail: 'AkShare 席位明细',
  news: '东财快讯新闻',
};
const numericField = (row: Record<string, unknown>, ...keys: string[]) => {
  for (const key of keys) {
    const value = row[key];
    if (value !== undefined && value !== null && value !== '') {
      const parsed = Number(String(value).replace(/,/g, ''));
      if (Number.isFinite(parsed)) return parsed;
    }
  }
  return 0;
};
const normalizeCapitalRows = (snapshot: CapitalSnapshot | null): CapitalRow[] => {
  const eastmoneyRows = snapshot?.sources?.eastmoneyLhb?.data?.result?.data || [];
  const rows = eastmoneyRows.length ? eastmoneyRows : snapshot?.sources?.akshareLhb?.data?.records || [];
  return rows.map((row) => ({
    code: String(row.SECURITY_CODE || row['代码'] || row['股票代码'] || ''),
    name: String(row.SECURITY_NAME_ABBR || row['名称'] || row['股票名称'] || '—'),
    net: numericField(row, 'BILLBOARD_NET_AMT', '龙虎榜净买额', '净额'),
    buy: numericField(row, 'BILLBOARD_BUY_AMT', '买入额', '买入金额'),
    sell: numericField(row, 'BILLBOARD_SELL_AMT', '卖出额', '卖出金额'),
    reason: String(row.EXPLAIN || row['上榜原因'] || row['解读'] || '—'),
  })).filter((row) => row.code).sort((a, b) => b.net - a.net);
};
const reportKey = (date: string) => `zhangcai.report.v2.${date}`;
const strategyRunsKey = 'zhangcai.strategy.runs.v1';
const selectedStrategyKey = 'zhangcai.strategy.selected.v1';
const strategyCatalogById = new Map<string, StrategyCatalogItem>(
  (strategyCatalog as StrategyCatalogItem[]).map((item) => [item.id, item]),
);
const strategyCatalogAliases: Record<string, string> = {
  'golden-ignition-v8': 'golden-ignition',
};
function strategyCatalogItem(id: string) {
  return strategyCatalogById.get(id) || strategyCatalogById.get(strategyCatalogAliases[id] || id);
}
function strategyDataStatus(id: string): StrategyCatalogItem['dataStatus'] {
  if (DATA_INSUFFICIENT_SKILLS.has(id)) return 'missing';
  return strategyCatalogItem(id)?.dataStatus || 'available';
}
function loadStrategyRuns(): Record<string, StrategyRun> {
  if (typeof window === 'undefined') return {};
  try {
    const value = JSON.parse(localStorage.getItem(strategyRunsKey) || '{}');
    return value && typeof value === 'object' ? value as Record<string, StrategyRun> : {};
  } catch { return {}; }
}
const strategyPreflightDisplayNote = '说明：已调用对应原始策略评分引擎完成本地数值回执；Harness 负责基于同一份回执解释结果、列出缺失项与风险边界，不生成买卖建议。';
function strategyPreflightDisplayText(output: unknown): string {
  return String(output || '').replace(
    '说明：本报告是网页适配层的真实数据预检与落盘运行单；未调用原始策略入口，因此不构成策略已执行或投资结论。',
    strategyPreflightDisplayNote,
  );
}
function strategyRunDataDate(run: StrategyRun): string {
  const parsed = run.harnessOutput ? normalizeHarnessOutput(run.harnessOutput) : null;
  const harnessDate = String(parsed?.dataDate || '').replace(/\D/g, '');
  if (harnessDate.length >= 8) return harnessDate.slice(0, 8);
  const assets = run.receipt?.assets;
  const daily = assets && typeof assets === 'object' ? (assets as Record<string, unknown>).tdx_daily_history : null;
  const receiptDate = daily && typeof daily === 'object' ? String((daily as Record<string, unknown>).trade_date || '').replace(/\D/g, '') : '';
  return receiptDate.length >= 8 ? receiptDate.slice(0, 8) : '';
}
const nonEquityNames = new Set([
  '上证指数',
  '深证成指',
  '创业板指',
  '科创50',
  '上证50',
  '北证50',
]);
const harnessEstimateSeconds: Record<string, number> = {
  'five-dimension-resonance': 900,
  'stock-analysis': 240,
  'stock-study': 240,
  'stock-research-engine': 240,
  'a-share-leader-deep-research': 300,
  'a-share-limit-up-mining': 300,
  'limit-up-review': 300,
  'morning-intelligence-plan': 300,
};
const estimateSeconds = (skillId: string) =>
  harnessEstimateSeconds[skillId] || 300;
const formatDuration = (seconds: number) =>
  `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;

// 这些能力当前没有完整的数据链，卡片保留详情但不允许误触发 Harness。
const DATA_INSUFFICIENT_SKILLS = new Set([
  'convertible-bond-screening-strategy',
  'a-share-longhubang-analysis',
  'a-share-leader-deep-research',
  'a-share-limit-up-leader-classification',
  'a-share-limit-up-mining',
  'youzi-capital-monitoring',
  'stock-recap-video',
]);
const BASIC_SKILLS = new Set([
  'stock-unified',
  'tdx-local-hub',
  'stock-hard-gate',
  'stock-watchlist',
  'kaipanla',
  // 基础能力只作为架构、来源与质量规则说明，不启动预检或 Harness。
  'market-data-capabilities',
  'workbuddy-evolution-v22',
]);
const skillMode = (skillId: string) =>
  DATA_INSUFFICIENT_SKILLS.has(skillId)
    ? 'data'
    : BASIC_SKILLS.has(skillId)
      ? 'basic'
      : 'runnable';
const skillIntroductions: Record<string, string> = {
  'a-share-15d-selection': '从通达信日线和多维强势因子中筛选短线候选，保留交易日与样本范围。',
  'five-dimension-resonance': '组合趋势、量价、资金、情绪与题材等维度，输出共振候选和数据边界。',
  'dragon-pullback': '识别强势股回调后的再启动形态，依据本地日线生成龙回头候选。',
  'a-share-hotspot-sentiment-analysis': '汇总行情、热点和新闻线索，形成主线与情绪结构的只读研判。',
  'core-mainline-scoring-system': '按板块强度、扩散度和代表股表现给当日主线候选评分。',
  'a-share-longhubang-analysis': '读取龙虎榜公开记录，整理净买额、席位和资金方向线索。',
  'limit-up-review': '复盘涨停候选、连板梯队和前一交易日表现，区分事实与日线推导。',
  'stock-analysis': '围绕单只股票整理行情、技术面、公告和风险信息，生成结构化研究。',
  'financial-roe-analysis': '从净资产收益率及杜邦分解观察公司的盈利质量和变化来源。',
  'technical-analysis': '基于本地 K 线计算趋势、支撑压力和常用技术指标。',
  'risk-mine-clearance': '检查个股公告、经营和行情风险线索，给出可核验的排雷清单。',
  'tdx-local-hub': '连接通达信本地日线、板块、公式和缓存，为其他技能提供数据底座。',
  'market-data-capabilities': '统一说明公开行情、资讯、通达信、本地落盘和降级来源的接入范围、实际状态与适用边界。',
  'workbuddy-evolution-v22': '说明用户纠错、硬规则、回归校验和交付闸门如何形成质量闭环，并区分规则说明与真实执行证据。',
};
function skillIntroduction(skill: Skill) {
  return skillIntroductions[skill.id] || `${groupNames[skill.group] || '股票研究'}能力：围绕${skill.name}整理当日数据、执行边界与可核验结果。`;
}

function Box({
  title,
  children,
  extra,
  className = '',
}: {
  title: string;
  children: ReactNode;
  extra?: ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-head">
        <h2>{title}</h2>
        {extra}
      </div>
      {children}
    </section>
  );
}
function Empty({ title, body }: { title: string; body: string }) {
  return (
    <div className="empty-state">
      <FolderOpen size={32} />
      <h3>{title}</h3>
      <p>{body}</p>
    </div>
  );
}
function Tags({ list }: { list: string[] }) {
  return (
    <div className="tags">
      {list.map((t) => (
        <span key={t}>{t}</span>
      ))}
    </div>
  );
}

function limitPct(stock: Stock) {
  if (stock.name.includes('ST') || stock.name.includes('*ST')) return 5;
  if (stock.market === 'bj' || stock.code.startsWith('920')) return 30;
  if (/^(300|301|688|689)/.test(stock.code)) return 20;
  return 10;
}
function stockRows(stock: Stock) {
  const rows = Array.isArray(stock.history) ? [...stock.history] : [];
  if (!rows.length || rows[rows.length - 1].date !== stock.date)
    rows.push(stock);
  return rows;
}
function limitCandidate(
  stock: Stock,
  officialCodes: string[] = [],
): LimitCandidate {
  const rows = stockRows(stock);
  const threshold = typeof stock.limitPct === 'number'
    ? stock.limitPct
    : limitPct(stock);
  let streak = typeof stock.limitStreak === 'number' ? stock.limitStreak : 0;
  if (!streak) {
    for (let i = rows.length - 1; i >= 0; i -= 1) {
      const current = rows[i];
      const prev = rows[i - 1];
      const change =
        i === rows.length - 1
          ? stock.pct
          : prev?.close
            ? (current.close / prev.close - 1) * 100
            : 0;
      if (change >= threshold - 0.35) streak += 1;
      else break;
    }
  }
  const confirmed = officialCodes.length
    ? officialCodes.includes(stock.code)
    : stock.pct >= threshold - 0.35;
  return {
    stock,
    limitPct: threshold,
    streak,
    currentPct: stock.pct,
    confirmed,
  };
}
function buildLadder(stocks: Stock[], officialCodes: string[] = []) {
  return stocks
    .map((x) => limitCandidate(x, officialCodes))
    .filter((x) => x.confirmed)
    .sort(
      (a, b) =>
        b.streak - a.streak ||
        b.currentPct - a.currentPct ||
        b.stock.amount - a.stock.amount,
    );
}

function rankRows(
  stocks: Stock[],
  sort: 'pct' | 'amount' | 'loss',
  size = 10,
): RankedStock[] {
  return stocks
    .filter((s) => s.date === stocks[0]?.date)
    .filter((s) => !nonEquityNames.has(s.name))
    .sort((a, b) =>
      sort === 'pct'
        ? b.pct - a.pct || b.amount - a.amount
        : sort === 'loss'
          ? a.pct - b.pct || b.amount - a.amount
        : b.amount - a.amount || b.pct - a.pct,
    )
    .slice(0, size)
    .map(({ code, name, pct, amount, close, market }) => ({
      code,
      name,
      pct,
      amount,
      close,
      market,
    }));
}
function buildAvailability(
  market: Market,
  ladder: LimitCandidate[],
): DataAvailability[] {
  const official = (market.tdxLimitUpCodes || []).length > 0;
  const proxy = market.intradayProxy;
  const sectorCoverage = market.sectors?.length
    ? Math.max(...market.sectors.map((x) => x.count))
    : 0;
  const source = market.dataSources || {};
  const supplemental = market.supplemental || {};
  const coverage = supplemental.coverage || {};
  const indexDailyAvailable = coverage.index_daily === true;
  const lhbAvailable = coverage.longhubang_snapshot === true || Boolean(market.publicLhbRecords?.length);
  const lhbMarketCount = supplemental.lhbMarketRecordCount || supplemental.lhbRecordCount || market.publicLhbRecords?.length || 0;
  const marginAvailable = coverage.margin_snapshot === true;
  const marginDate = supplemental.marginLatestAvailableDate || supplemental.date || market.date;
  return [
    {
      item: '市场广度与主要指数',
      status: '可用',
      evidence: `${market.currentCount} 只同日样本、${market.indices.length} 个指数`,
      solution: '随通达信日线刷新',
    },
    {
      item: '主要指数历史日线',
      status: indexDailyAvailable ? '可用' : '缺失',
      evidence: indexDailyAvailable
        ? `本地补充快照已提供 ${supplemental.indexSymbolCount || 0} 组指数完整日线，并保留起止日期`
        : '尚未读取 evidence/supplemental/<date>/market.json 的指数日线快照',
      solution: indexDailyAvailable
        ? 'Harness 通过统一补充快照复用，不再扫描巨型全市场 JSONL'
        : '执行“补齐其他数据”或统一落盘，先从 TDX .day 生成指数索引',
    },
    {
      item: '财务三表',
      status: coverage.financial === true ? '可用' : '按需',
      evidence: coverage.financial === true
        ? '目标股票财务三表已按股东权益、利润表和现金流量表落盘'
        : '财务三表不是全市场每日快照，进入个股研究/Harness 后按目标代码读取新浪财务源',
      solution: '请求个股研究时自动写入 evidence/supplemental/<date>/<code>.<market>.json，并保留报告期日期',
    },
    {
      item: '流通股本与总股本',
      status: coverage.share_capital === true ? '可用' : '按需',
      evidence: coverage.share_capital === true
        ? '腾讯报价原始字段 72/73 已解析为流通股本/总股本，并同步保存市值与估值字段'
        : '股本属于个股维度，当前市场页未指定目标代码，等待个股请求按需读取',
      solution: '个股 Harness 启动前自动补齐并把股本快照传入 context，不用市值反推股本',
    },
    {
      item: '个股涨幅榜',
      status: '可用',
      evidence: `已从同日 ${market.currentCount} 只样本排序`,
      solution: '报告直接引用当日榜单',
    },
    {
      item: '个股成交额榜',
      status: '可用',
      evidence: '日线文件含 amount 字段，已排序',
      solution: '报告直接引用当日榜单',
    },
    {
      item: '涨停与连板梯队',
      status: official ? '可用' : '推导',
      evidence: official
        ? `TDX ${market.tdxLimitUpFiles?.join('、') || 'ZTC/FLZT'} 提供 ${market.tdxLimitUpCodes?.length} 个代码，连板由历史日线计算`
        : `${ladder.length} 个涨跌停阈值候选，连板由历史日线计算`,
      solution: '继续校验交易所涨停名单、炸板和停牌状态',
    },
    {
      item: '跌停与负反馈榜',
      status: market.stocks.some((s) => s.pct < 0) ? '推导' : '缺失',
      evidence: market.stocks.some((s) => s.pct < 0)
        ? `按 ${market.currentCount} 只同日样本排序跌幅榜；达到各市场跌停阈值的候选 ${market.tdxLimitDownCodes?.length || 0} 只`
        : '本地没有 FLDT 或同等跌停名单文件',
      solution:
        '当前使用日线阈值推导；接入交易所跌停名单和盘中状态后升级为官方负反馈榜',
    },
    {
      item: '封板率/炸板/首封时刻',
      status: proxy?.upperHitCount ? '推导' : '缺失',
      evidence: proxy?.upperHitCount
        ? `OHLC 代理识别触板 ${proxy.upperHitCount} 只、收盘封板 ${proxy.upperClosedCount} 只、触板后开板 ${proxy.openedAfterHitCount} 只；封板率 ${proxy.sealRatePct ?? '—'}%，炸板率 ${proxy.explosionRatePct ?? '—'}%，首封时刻未提供（5 分钟文件同日覆盖 ${proxy.lc5CurrentDateCount}/${proxy.lc5Files}）`
        : '收盘日线不包含盘中封板过程',
      solution: proxy?.upperHitCount
        ? '当前先用日线 high/close 代理并明确标注；接入同日 1 分钟/逐笔数据后替换为首封、回封和精确炸板率'
        : '接入 1 分钟或逐笔数据，计算首封、开板、回封、封板率和炸板率',
    },
    {
      item: '前日涨停表现与情绪周期',
      status: market.priorLimitUpStats?.count ? '推导' : '缺失',
      evidence: market.priorLimitUpStats?.count
        ? `由 ${market.priorLimitUpStats.previousDate || '前一交易日'} 日线涨停候选配对今日表现，共 ${market.priorLimitUpStats.count} 只，今日均值 ${market.priorLimitUpStats.todayAvgPct ?? 0}%`
        : '当前快照没有前一交易日涨停池与次日表现配对表',
      solution:
        '当前使用历史日线推导晋级表现；保存每日官方涨停池快照后再计算正式情绪周期',
    },
    {
      item: '融资融券/北向资金',
      status: marginAvailable ? '可用' : '缺失',
      evidence: marginAvailable
        ? `融资融券已落盘 ${supplemental.marginRecordCount || 0} 条，最近可得日期 ${d(marginDate)}；精确到目标日 ${supplemental.marginExactDate || 0} 条。北向资金仍单独标注为未接入`
        : `已发现 TDX 融资融券页面配置（${(source.financing as { configFile?: string } | undefined)?.configFile || 'func_gx_rzrq101.xml'}），但本地补充快照未返回可用记录；北向资金仍需单独接入`,
      solution: marginAvailable
        ? 'Harness 使用融资余额、融资买入/偿还、融券余额等原始字段；无目标日记录时保留最近可得日期，不用 0 代替'
        : '执行“补齐其他数据”，通过东方财富 datacenter 生成同日/最近可得融资融券快照',
    },
    {
      item: '板块涨幅榜',
      status: market.sectors?.length ? '可用' : '缺失',
      evidence: market.sectors?.length
        ? `TDX 行业成员映射覆盖 ${market.sectors.reduce((n, x) => n + x.count, 0)} 只同日样本，已按平均涨跌、成交额、涨停家数排序；最大单板块 ${sectorCoverage} 只`
        : '本地没有可用的行业成员映射',
      solution: market.sectors?.length
        ? '网页已直接呈现 TDX 行业榜和主题成员聚合；如需交易所官方板块指数，再配置对应板块日线源'
        : '接入行业分类与板块日线，按板块成交额和涨停家数排序',
    },
    {
      item: '龙虎榜净买与席位',
      status: lhbAvailable ? '可用' : '缺失',
      evidence: lhbAvailable
        ? `东方财富同日全市场龙虎榜快照已落盘 ${lhbMarketCount} 条；目标股票无匹配记录时按“无上榜记录”处理，不判为快照缺失`
        : '本地补充快照没有同日龙虎榜文件',
      solution: lhbAvailable
        ? 'Harness 读取上榜日期、买卖额、净买额及可用席位明细；身份映射仍保持独立缺口'
        : '执行“补齐其他数据”，接入交易所/东方财富公开龙虎榜并保存来源日期',
    },
    {
      item: '主力资金流向',
      status: '缺失',
      evidence: '成交额不是净流入，TQ 公式桥接尚未启用（Num=0）',
      solution: '启用 TQ/L2 资金公式并记录公式版本、授权和时间戳',
    },
    {
      item: '新闻公告/催化',
      status: '缺失',
      evidence: 'msg_zx 与 msg_web 目录不存在',
      solution: '接入可追溯新闻公告源，保留发布时间、原文链接和证券映射',
    },
    {
      item: '盘中封板/炸板/封单',
      status: proxy?.upperHitCount || proxy?.lowerHitCount ? '推导' : '缺失',
      evidence: proxy?.upperHitCount || proxy?.lowerHitCount
        ? `已生成涨停触板/收盘封板/开板代理和跌停触板代理；同日 5 分钟文件 ${proxy.lc5CurrentDateCount}/${proxy.lc5Files}，封单额与首封时间仍为空`
        : '只有收盘日线，不能重建盘中过程',
      solution: proxy?.upperHitCount || proxy?.lowerHitCount
        ? '当前使用可复算 OHLC 代理；接入同日 1 分钟或逐笔快照后补首封、回封和封单额'
        : '接入 1 分钟或逐笔快照，记录首封、开板、回封和封单额',
    },
  ];
}

const themeDefs = [
  {
    name: '科技与AI',
    tag: '名称聚类',
    color: '#bd1f35',
    words: [
      'AI',
      '人工智能',
      '算力',
      '芯片',
      '半导体',
      '软件',
      '科技',
      '智能',
      '机器人',
      '通信',
      '数据',
    ],
  },
  {
    name: '新能源与电力',
    tag: '名称聚类',
    color: '#d75b65',
    words: ['电力', '能源', '光伏', '风电', '储能', '锂', '电池', '充电', '氢'],
  },
  {
    name: '医药与生物',
    tag: '名称聚类',
    color: '#c77382',
    words: ['医药', '生物', '医疗', '药业', '制药', '疫苗', '器械', '蛋白'],
  },
  {
    name: '消费与农业',
    tag: '名称聚类',
    color: '#d39a54',
    words: [
      '食品',
      '乳业',
      '酒',
      '零售',
      '消费',
      '农业',
      '种业',
      '粮',
      '猪',
      '鸡',
      '牧业',
    ],
  },
  {
    name: '高端制造',
    tag: '名称聚类',
    color: '#a94b61',
    words: ['机械', '装备', '材料', '制造', '工业', '汽车', '航空', '轨道'],
  },
  {
    name: '资源与化工',
    tag: '名称聚类',
    color: '#b45d4b',
    words: ['化工', '能源', '煤', '钢', '有色', '矿', '石油', '铝', '铜'],
  },
];
function boardThemes(boards: Board[], colors: string[], limit = 12): Theme[] {
  return boards.slice(0, limit).map((board, index) => ({
    name: board.name,
    tag: board.tag || 'TDX板块成员聚合',
    count: board.count,
    avgPct: board.avgPct,
    amount: board.amount,
    leaders: board.leaders || [],
    color: colors[index % colors.length],
  }));
}
function buildThemes(
  stocks: Stock[],
  conceptBoards: Board[] = [],
  sectors: Board[] = [],
): Theme[] {
  const boardRows = conceptBoards.length ? conceptBoards : sectors;
  if (boardRows.length) {
    return boardThemes(
      boardRows,
      ['#bd1f35', '#d75b65', '#c77382', '#d39a54', '#a94b61', '#b45d4b'],
    );
  }
  const buckets = themeDefs.map((def) => ({ ...def, rows: [] as Stock[] }));
  stocks
    .filter((s) => s.date === stocks[0]?.date)
    .forEach((stock) => {
      const def = buckets.find((x) =>
        x.words.some((word) =>
          stock.name.toUpperCase().includes(word.toUpperCase()),
        ),
      );
      if (def) def.rows.push(stock);
    });
  return buckets
    .filter((x) => x.rows.length)
    .map((x) => ({
      name: x.name,
      tag: x.tag,
      count: x.rows.length,
      avgPct: x.rows.reduce((sum, s) => sum + s.pct, 0) / x.rows.length,
      amount: x.rows.reduce((sum, s) => sum + s.amount, 0),
      leaders: [...x.rows].sort((a, b) => b.pct - a.pct).slice(0, 3),
      color: x.color,
    }))
    .sort((a, b) => b.avgPct - a.avgPct || b.count - a.count);
}

function makeBaseReport(
  market: Market,
  themes: Theme[],
  ladder: LimitCandidate[],
): Report {
  const ratio = market.currentCount
    ? (market.up / market.currentCount) * 100
    : 0;
  const gainLeaders = rankRows(market.stocks, 'pct', 10);
  const amountLeaders = rankRows(market.stocks, 'amount', 10);
  const lossLeaders = rankRows(market.stocks, 'loss', 10);
  const limitDownCandidates = market.tdxLimitDownCodes?.length
    ? market.stocks
        .filter((s) => market.tdxLimitDownCodes?.includes(s.code))
        .sort((a, b) => a.pct - b.pct)
        .slice(0, 10)
        .map(({ code, name, pct, amount, close, market: venue }) => ({
          code,
          name,
          pct,
          amount,
          close,
          market: venue,
        }))
    : lossLeaders.filter((s) => s.pct < -9.5);
  const availability = buildAvailability(market, ladder);
  return {
    title: `掌财智能体 · ${d(market.date)} 行情复盘`,
    generatedBy: '网页脚本 + 本地规则',
    date: market.date,
    source: '本地日线归档',
    scope: `同日样本 ${market.currentCount} 只，覆盖沪深北；排除旧日期 ${market.staleCount} 只`,
    summary: `市场上涨 ${market.up} 只、下跌 ${market.down} 只、平盘 ${market.flat} 只，上涨占比 ${ratio.toFixed(1)}%。已接入 TDX 榜单、指数日线、龙虎榜和融资融券补充快照；财务与股本在个股研究时按代码按需补齐。`,
    metrics: [
      {
        label: '同日样本',
        value: `${market.currentCount} 只`,
        detail: `总可读 ${market.total} 只`,
      },
      {
        label: '上涨 / 下跌',
        value: `${market.up} / ${market.down}`,
        detail: `平盘 ${market.flat} 只`,
      },
      {
        label: '样本成交额',
        value: `${(market.amount / 1e12).toFixed(2)} 万亿`,
        detail: '沪深北样本合计',
      },
      {
        label: '日线涨停候选',
        value: `${ladder.length} 只`,
        detail: market.tdxLimitUpCodes?.length
          ? `TDX ZTC/FLZT ${market.tdxLimitUpCodes.length} 个代码`
          : '按涨跌停阈值推导',
      },
      {
        label: '行业板块榜',
        value: `${market.sectors?.length || 0} 个`,
        detail: market.sectors?.length
          ? 'TDX 行业成员聚合并按平均涨跌排序'
          : '等待行业映射',
      },
      {
        label: '触板/封板代理',
        value: `${market.intradayProxy?.upperHitCount || 0} / ${market.intradayProxy?.upperClosedCount || 0} 只`,
        detail: '日线 OHLC 代理；首封时刻未提供',
      },
      {
        label: '缺失数据项',
        value: `${availability.filter((x) => x.status === '缺失').length} 项`,
        detail: '报告已逐项列出解决办法',
      },
    ],
    indices: market.indices,
    themes,
    ladder: ladder.slice(0, 12),
    gainLeaders,
    amountLeaders,
    lossLeaders,
    limitDownCandidates,
    priorLimitUpStats: market.priorLimitUpStats,
    sectors: market.sectors || [],
    conceptBoards: market.conceptBoards || [],
    intradayProxy: market.intradayProxy,
    availability,
    cautions: [
      '本报告只使用本地通达信日线快照，不代表实时行情。',
      '主线与行业榜使用 TDX 本地成员映射和主题成员聚合；代表股是候选，不等同于交易所官方行业龙头。',
      '跌停、前日涨停表现和封板率已由日线推导；龙虎榜与融资融券使用已落盘的公开快照，目标日无精确融资记录时显示最近可得日期；北向资金、主力资金和当日新闻仍需各自来源确认。',
    ],
    actions: [
      '用 DeepSeek Harness 对 TDX 行业/主题榜、涨幅榜、成交额榜、主线候选和涨停梯队做结构化复核。',
      '个股研究会自动补齐财务三表与流通/总股本；继续补入北向、主力公式、新闻和同日 1 分钟快照后，相关状态会独立升级。',
    ],
  };
}
function loadReport(date: string) {
  if (typeof window === 'undefined') return null;
  try {
    const value = JSON.parse(localStorage.getItem(reportKey(date)) || 'null');
    return value && value.date === date ? (value as Report) : null;
  } catch {
    return null;
  }
}

function parseHarnessOutput(raw: string) {
  const parsed = normalizeHarnessOutput(raw);
  return {
    ...parsed,
    dataScope: parsed.dataScope,
  };
}

function buildAiPresentation(
  raw: string,
  base: Report,
  label: string,
) {
  const parsed = parseHarnessOutput(raw);
  const summary = parsed.summary || base.summary;
  const themes = base.themes
    .slice(0, 3)
    .map((item) => `${item.name} ${p(item.avgPct)}`)
    .join('、');
  const ladder = base.ladder
    .slice(0, 3)
    .map((item) => `${item.stock.name} ${item.streak}天`)
    .join('、');
  return {
    summary,
    cautions: parsed.cautions,
    dataScope: parsed.dataScope,
    presentation: {
      headline: `${label}已按本地 ${d(base.date)} 行情整理为可读结论。`,
      findings: [
        { title: '模型摘要', text: summary },
        {
          title: '行情证据',
          text: `主线候选：${themes || '暂无足够主题样本'}；涨停与连板候选：${ladder || '暂无'}。`,
        },
        {
          title: '数据边界',
          text: `报告使用${base.scope}。缺失项仍以“缺失”标示，未用模型内容替代原始行情。`,
        },
        ...parsed.findings,
      ],
      tables: parsed.tables,
      jsonValid: parsed.jsonValid,
      parseError: parsed.parseError,
    },
  };
}

function ReportVisual({ report }: { report: Report }) {
  const max = Math.max(...report.themes.slice(0, 5).map((item) => Math.abs(item.avgPct)), 1);
  return (
    <section className="report-visual" aria-label="市场结构图">
      <div className="report-visual-head">
        <div>
          <span>图文速览</span>
          <h4>市场结构图</h4>
        </div>
        <p>以同日通达信快照绘制，不含实时盘中数据。</p>
      </div>
      <div className="report-visual-grid">
        <div className="report-breadth-card">
          <small>上涨 / 下跌 / 平盘</small>
          <div className="report-breadth-bar">
            <span className="up-fill" style={{ flex: Number(report.metrics.find((x) => x.label === '上涨家数')?.value.replace(/\D/g, '') || 0) }} />
            <span className="flat-fill" style={{ flex: Number(report.metrics.find((x) => x.label === '平盘家数')?.value.replace(/\D/g, '') || 0) }} />
            <span className="down-fill" style={{ flex: Number(report.metrics.find((x) => x.label === '下跌家数')?.value.replace(/\D/g, '') || 0) }} />
          </div>
          <p>{report.metrics.filter((x) => /上涨家数|下跌家数|平盘家数/.test(x.label)).map((x) => `${x.label.replace('家数', '')} ${x.value}`).join(' · ')}</p>
        </div>
        <div className="report-theme-chart">
          <small>主题候选平均涨跌</small>
          {report.themes.slice(0, 5).map((item) => (
            <div className="report-theme-row" key={`chart-${item.name}`}>
              <span>{item.name}</span>
              <i><b className={item.avgPct >= 0 ? 'up-fill' : 'down-fill'} style={{ width: `${Math.max(8, Math.abs(item.avgPct) / max * 100)}%` }} /></i>
              <em className={item.avgPct >= 0 ? 'up' : 'down'}>{p(item.avgPct)}</em>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function harnessParseNotice(error: string | undefined, prefix = '输出'): string {
  if (error?.includes('恢复已完成字段')) {
    return '旧版桥接输出曾被截断，已恢复已完成字段并排版；重新执行后会保存完整 JSON。';
  }
  return `${prefix}已做兼容规范化：${error || '未通过严格 JSON 校验'}。`;
}

function harnessStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    ok: '已完成', completed: '已完成', CLEAN_PASS: '校验通过', available: '数据可用',
    running: '运行中', pending: '等待中', BLOCKED: '数据阻塞', FAILED: '失败', failed: '失败',
  };
  return labels[status] || status || '未知';
}

function HarnessOutput({ raw, structured, compact = true }: { raw: string; structured?: StructuredStrategy | null; compact?: boolean }) {
  const parsed = parseHarnessOutput(raw);
  const structuredAnalysis = structured?.analysis || {};
  const structuredSummary = structuredAnalysis.name || structuredAnalysis.symbol
    ? `${strategyValue(structuredAnalysis.name)}（${strategyValue(structuredAnalysis.symbol)}）策略交付物已生成，已按行情、公式输出和子系统结果排版。`
    : '';
  const visibleFindings = compact ? parsed.findings.slice(0, 5) : parsed.findings;
  const visibleTables = compact ? parsed.tables.slice(0, 3) : parsed.tables;
  const hiddenFindings = compact ? parsed.findings.slice(5) : [];
  const hiddenTables = compact ? parsed.tables.slice(3) : [];
  const compactTable = (table: HarnessTable): HarnessTable => ({
    ...table,
    rows: compact ? table.rows.slice(0, 10) : table.rows,
  });
  return (
    <section className="harness-output-card">
      <div className="ai-report-reading-head"><Sparkles size={16} /><b>已排版的技能输出</b><span>已存入我的报告</span></div>
      <Table>
        <TableHeader><TableRow><TableHead>运行状态</TableHead><TableHead>数据日期</TableHead><TableHead>数据范围</TableHead></TableRow></TableHeader>
        <TableBody><TableRow><TableCell><span className={parsed.status === 'CLEAN_PASS' || parsed.status === 'ok' || parsed.status === 'completed' ? 'status-good' : 'status-warn'}>{harnessStatusLabel(parsed.status)}</span></TableCell><TableCell>{parsed.dataDate || '—'}</TableCell><TableCell>{parsed.dataScope || '—'}</TableCell></TableRow></TableBody>
      </Table>
      <StructuredStrategyOutput structured={structured} />
      <p>{parsed.summary || structuredSummary || 'Harness 未返回摘要，请在下方查看原始响应。'}</p>
      {!parsed.jsonValid && <p className="form-error">{harnessParseNotice(parsed.parseError, '输出')}</p>}
      {visibleFindings.length > 0 && <div className="ai-finding-grid">{visibleFindings.map((item, index) => <article key={`${item.title}-${index}`}><h5>{item.title}</h5><p>{item.text}</p></article>)}</div>}
      {visibleTables.length > 0 && visibleTables.map((table, index) => <HarnessDataTable key={`${table.title}-${index}`} table={compactTable(table)} />)}
      {compact && (hiddenFindings.length > 0 || hiddenTables.length > 0 || parsed.tables.some((table) => table.rows.length > 10)) && (
        <details className="harness-more"><summary>查看完整分析（保留全部结论与表格）</summary>
          {hiddenFindings.length > 0 && <div className="ai-finding-grid">{hiddenFindings.map((item, index) => <article key={`${item.title}-more-${index}`}><h5>{item.title}</h5><p>{item.text}</p></article>)}</div>}
          {hiddenTables.map((table, index) => <HarnessDataTable key={`${table.title}-more-${index}`} table={table} />)}
          {visibleTables.filter((table) => table.rows.length > 10).map((table, index) => <HarnessDataTable key={`${table.title}-rows-${index}`} table={{ ...table, rows: table.rows.slice(10) }} />)}
        </details>
      )}
      {parsed.cautions.length > 0 && (
        <Table>
          <TableHeader><TableRow><TableHead>风险与数据边界</TableHead></TableRow></TableHeader>
          <TableBody>{parsed.cautions.map((item) => <TableRow key={item}><TableCell>{item}</TableCell></TableRow>)}</TableBody>
        </Table>
      )}
      <details className="report-raw"><summary>查看原始 JSON</summary><pre>{raw}</pre></details>
    </section>
  );
}

function harnessTableCellText(table: HarnessTable, column: string, cell: string) {
  const value = cell || '—';
  if (!table.title.includes('候选')) return value;
  // Candidate diagnostics contain several independent facts. Keep them in the
  // same schema, but render each fact on its own line so a single cell does not
  // become a narrow vertical wall of text.
  if (column === '波段') return value.replace(/\s*·\s*/g, '\n');
  if (column === '游资' || column === '机构' || column === '风险') {
    return value.replace(/\s*；\s*/g, '\n');
  }
  return value;
}

function HarnessDataTable({ table }: { table: HarnessTable }) {
  const candidateTable = table.title.includes('候选');
  const quantCandidateTable = candidateTable && (
    table.columns.includes('主模型')
    || table.rows.some((row) => row[5]?.startsWith('模型分量') || row[4]?.includes('核心结构') || row[4]?.includes('主模型'))
  );
  const displayTable = quantCandidateTable && !table.columns.includes('主模型')
    ? {
      ...table,
      columns: ['排名', '代码', '名称', '评分', '波段', '主模型', '游资', '机构', '风险'],
      rows: table.rows.map((row) => {
        const parts = String(row[4] || '').split(/\s*·\s*/);
        const last = parts.at(-1) || '';
        const hasModel = /^(待闭合：|已触发：|无主模型)/.test(last);
        return [
          ...row.slice(0, 4),
          hasModel ? parts.slice(0, -1).join(' · ') : row[4] || '—',
          hasModel ? last : '无主模型',
          ...row.slice(5),
        ];
      }),
    }
    : table;
  const displayCandidateTable = displayTable.title.includes('候选');
  const displayQuantTable = displayCandidateTable && displayTable.columns.includes('主模型');
  return <section className={`harness-data-table${displayCandidateTable ? ' harness-candidate-table' : ''}`}>
    <h5>{displayTable.title}</h5>
    <Table className={displayCandidateTable ? `harness-candidate-table-grid${displayQuantTable ? ' harness-candidate-table-grid-v2' : ''}` : undefined}>
      {displayCandidateTable && <colgroup>{displayTable.columns.map((column, index) => <col key={`${column}-${index}`} className={`harness-col-${column}`} />)}</colgroup>}
      <TableHeader><TableRow>{displayTable.columns.map((column) => <TableHead key={column}>{column}</TableHead>)}</TableRow></TableHeader>
      <TableBody>{displayTable.rows.map((row, rowIndex) => <TableRow key={rowIndex}>{row.map((cell, cellIndex) => <TableCell key={`${rowIndex}-${cellIndex}`}><span className="harness-table-cell-text">{harnessTableCellText(displayTable, displayTable.columns[cellIndex] || '', cell)}</span></TableCell>)}</TableRow>)}</TableBody>
    </Table>
  </section>;
}

type StructuredStrategy = {
  reportPath?: string;
  analysisPath?: string;
  derivedPath?: string;
  reportMarkdown?: string;
  analysis?: Record<string, unknown> | null;
  derived?: Record<string, unknown> | null;
};

function strategyValue(value: unknown): string {
  if (value == null || value === '') return '—';
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
  try { return JSON.stringify(value); } catch { return String(value); }
}

function StructuredStrategyOutput({ structured }: { structured?: StructuredStrategy | null }) {
  if (!structured) return null;
  const analysis = structured.analysis || {};
  const dateContext = (analysis.date_context && typeof analysis.date_context === 'object' ? analysis.date_context : {}) as Record<string, unknown>;
  const realtime = (analysis.realtime_calc && typeof analysis.realtime_calc === 'object' ? analysis.realtime_calc : {}) as Record<string, unknown>;
  const latest = (analysis.latest_outputs && typeof analysis.latest_outputs === 'object' ? analysis.latest_outputs : {}) as Record<string, unknown>;
  const derived = (structured.derived || analysis.derived || {}) as Record<string, unknown>;
  const realtimeFields: [string, string][] = [
    ['收盘价', 'last_close'], ['涨跌幅', 'change_pct'], ['日线开盘', 'open'],
    ['日线最高', 'high'], ['日线最低', 'low'], ['成交量（手）', 'volume_lot'], ['成交额（万元）', 'amount_wan'],
  ];
  const dateFields: [string, string][] = [
    ['分析基准日', 'analysis_as_of_date'], ['公式最新日期', 'formula_latest_date'], ['日线最新日期', 'kline_latest_date'], ['数据模式', 'mode'],
  ];
  const realtimeRows = realtimeFields.filter(([, key]) => realtime[key] != null).map(([label, key]) => [label, strategyValue(realtime[key])]);
  const formulaRows = Object.entries(latest).map(([key, value]) => [key, strategyValue(value)]);
  const derivedRows = Object.entries(derived).map(([key, value]) => [key, strategyValue(value)]);
  return <section className="strategy-structured-report">
    <div className="ai-report-reading-head"><Sparkles size={16} /><b>结构化策略报告</b><span>已读取策略交付物</span></div>
    <Table><TableHeader><TableRow><TableHead>项目</TableHead><TableHead>结果</TableHead></TableRow></TableHeader><TableBody>
      <TableRow><TableCell>标的</TableCell><TableCell>{strategyValue(analysis.name)} · {strategyValue(analysis.symbol)}</TableCell></TableRow>
      {dateFields.filter(([, key]) => dateContext[key] != null).map(([label, key]) => <TableRow key={key}><TableCell>{label}</TableCell><TableCell>{strategyValue(dateContext[key])}</TableCell></TableRow>)}
    </TableBody></Table>
    {realtimeRows.length > 0 && <HarnessDataTable table={{ title: '收盘行情快照', columns: ['项目', '数值'], rows: realtimeRows }} />}
    {formulaRows.length > 0 && <HarnessDataTable table={{ title: '飞龙在天公式输出', columns: ['输出字段', '当日值'], rows: formulaRows }} />}
    {derivedRows.length > 0 && <HarnessDataTable table={{ title: '子系统计算结果', columns: ['计算项', '结果'], rows: derivedRows }} />}
    {structured.reportMarkdown && <details className="strategy-markdown"><summary>查看完整排版报告</summary><pre>{structured.reportMarkdown}</pre></details>}
  </section>;
}

function StrategyRunVisual({ run }: { run: StrategyRun }) {
  const analysis = run.structured?.analysis || {};
  const realtime = analysis.realtime_calc && typeof analysis.realtime_calc === 'object'
    ? analysis.realtime_calc as Record<string, unknown>
    : {};
  const numeric = Object.entries(realtime)
    .map(([label, value]) => [label, Number(value)] as const)
    .filter(([, value]) => Number.isFinite(value))
    .slice(0, 6);
  const max = Math.max(...numeric.map(([, value]) => Math.abs(value)), 1);
  const hasReport = strategyRunHasReport(run);
  const status = hasReport ? '已完成' : strategyRunHasFailure(run) ? '运行失败' : run.busy ? '执行中' : run.status || '已运行';
  return (
    <div className="strategy-run-visual">
      <div className="strategy-run-visual-head">
        <b>最新运行摘要</b>
        <span className={hasReport ? 'strategy-report-ok' : 'strategy-report-warn'}>{status}</span>
      </div>
      <div className="strategy-run-visual-meta">
        <span>原始策略：{run.output ? '已返回' : '未返回'}</span>
        <span>Harness：{run.harnessOutput ? '已解读' : '等待解读'}</span>
        {run.receipt && <span>交付物：已记录</span>}
      </div>
      {numeric.length > 0 ? (
        <div className="strategy-run-bars" aria-label="策略最新数值摘要图">
          {numeric.map(([label, value]) => (
            <div className="strategy-run-bar" key={label}>
              <span title={label}>{label}</span>
              <i><b style={{ width: `${Math.max(4, Math.min(100, Math.abs(value) / max * 100))}%` }} /></i>
              <em>{strategyValue(value)}</em>
            </div>
          ))}
        </div>
      ) : (
        <p className="strategy-run-visual-empty">该次运行没有可绘制的数值字段，详细结论与表格见下方 Harness 解读。</p>
      )}
    </div>
  );
}

function CompactStrategyReport({ raw, structured }: { raw: string; structured?: StructuredStrategy | null }) {
  const parsed = parseHarnessOutput(raw);
  // Some canonical runners (notably five-dimension-resonance) return only a
  // receipt summary on stdout while the full Top10 JSON is exposed through
  // `structured.analysis`. Use that payload as the table source when the raw
  // response has no candidate array.
  const source = parsed.value || {};
  const structuredSource = structured?.analysis && typeof structured.analysis === 'object' ? structured.analysis : {};
  const sourceRows = ['top10', 'top5', 'ranked', 'results', 'candidates']
    .map((key) => source[key] ?? structuredSource[key])
    .find((value) => Array.isArray(value)) as unknown[] | undefined;
  const compactRows = sourceRows?.filter((row) => row && typeof row === 'object' && !Array.isArray(row)).slice(0, 10) || [];
  const firstTable = parsed.tables.find((table) => table.rows.length > 0);
  const rows = firstTable?.rows.slice(0, 10) || compactRows.map((row) => {
    const item = row as Record<string, unknown>;
    return [
      strategyValue(item.rank || item.ranking || item.排名),
      strategyValue(item.code || item.symbol || item.代码),
      strategyValue(item.name || item.名称),
      strategyValue(item.score || item.final_score || item.评分),
      strategyValue(item['飞龙波段'] || item.wave || item.波段),
      strategyValue(item.游资 || item.youzi),
      strategyValue(item.机构 || item.jigou),
      strategyValue(item.风险 || item.risk),
    ];
  });
  const columns = firstTable?.columns?.slice(0, 8) || ['排名', '代码', '名称', '评分', '波段', '游资', '机构', '风险'];
  const hasTop = rows.length > 0;
  return (
    <section className="compact-strategy-report">
      <div className="compact-strategy-head"><b>策略报告</b><span className={parsed.status === 'CLEAN_PASS' ? 'strategy-report-ok' : 'strategy-report-warn'}>{parsed.status || 'UNKNOWN'}</span></div>
      <Table><TableHeader><TableRow><TableHead>状态</TableHead><TableHead>数据日期</TableHead><TableHead>数据范围</TableHead><TableHead>输出</TableHead></TableRow></TableHeader><TableBody><TableRow><TableCell>{harnessStatusLabel(parsed.status)}</TableCell><TableCell>{parsed.dataDate || '—'}</TableCell><TableCell>{parsed.dataScope || '—'}</TableCell><TableCell>{hasTop ? `Top${rows.length}` : '暂无候选表'}</TableCell></TableRow></TableBody></Table>
      {parsed.summary && <p className="compact-strategy-summary">{parsed.summary}</p>}
      {hasTop ? <HarnessDataTable table={{ title: 'Top 候选', columns, rows }} /> : <p className="strategy-run-visual-empty">策略尚未产出 Top10 交付物；当前仅保留运行状态和原始响应。</p>}
      {parsed.cautions.length > 0 && <p className="compact-strategy-caution">{parsed.cautions.slice(0, 2).join('；')}</p>}
      {structured?.reportPath && <small className="compact-strategy-path">交付物已记录：{structured.reportPath}</small>}
    </section>
  );
}

function StrategyReportGallery({ strategies, runs }: { strategies: Skill[]; runs: Record<string, StrategyRun> }) {
  const entries = strategies
    .map((skill) => ({ skill, run: runs[skill.id] }))
    .filter(({ run }) => !!run && !!(run.output || run.harnessOutput || run.structured));
  if (!entries.length) return null;
  return (
    <Box title={`策略运行回执 · ${entries.length} 项`} className="strategy-report-gallery">
      <div className="strategy-report-gallery-intro">每项保留最近一次本地预检与 Harness 分析；权威 JSON、任务记录和 Markdown 回执已保存到应用数据目录。</div>
      <div className="strategy-report-gallery-grid">
        {entries.map(({ skill, run }) => (
          <article className="strategy-report-card" key={skill.id}>
            <div className="strategy-report-card-head">
              <div><b>{skill.name}</b><small>{skill.id}</small></div>
              <span className={run?.phase === 'completed' ? 'strategy-report-ok' : 'strategy-report-warn'}>{run?.status === 'ERROR' ? '运行失败' : run?.phase === 'completed' ? 'Harness 已完成' : `预检 ${run?.status || 'UNKNOWN'}`}</span>
            </div>
            <div className="strategy-run-output ready"><pre>{strategyPreflightDisplayText(run?.output) || '暂无预检回执。'}</pre></div>
            {run?.harnessOutput && <HarnessOutput raw={run.harnessOutput} compact={false} />}
          </article>
        ))}
      </div>
    </Box>
  );
}

function ArchivedStockReport({ item }: { item: ReportArchiveRecord }) {
  const stock = (item.content.stock || {}) as Record<string, unknown>;
  const parsed = normalizeHarnessOutput(item.raw || item.summary);
  const visibleFindings = parsed.findings.slice(0, 5);
  const visibleTables = parsed.tables;
  const textValue = (value: unknown, fallback = '—') => typeof value === 'string' || typeof value === 'number' ? String(value) : fallback;
  return <section className="stock-research-report"><div className="ai-report-reading-head"><Sparkles size={16} /><b>个股研究报告</b><span>已归档 · {parsed.jsonValid ? 'JSON 已校验' : '已兼容规范化'}</span></div><p>{parsed.summary || item.summary}</p><Table><TableHeader><TableRow><TableHead>标的</TableHead><TableHead>{closeDateLabel(item.date)}</TableHead><TableHead>涨跌幅</TableHead><TableHead>数据日期</TableHead><TableHead>数据范围</TableHead></TableRow></TableHeader><TableBody><TableRow><TableCell>{textValue(stock.name)} · {textValue(stock.code)}</TableCell><TableCell title={closeDateLabel(item.date)}>{stock.close == null ? '—' : Number(stock.close).toFixed(2)}</TableCell><TableCell className={Number(stock.pct || 0) >= 0 ? 'up' : 'down'}>{stock.pct == null ? '—' : `${Number(stock.pct) >= 0 ? '+' : ''}${Number(stock.pct).toFixed(2)}%`}</TableCell><TableCell>{d(item.date)}</TableCell><TableCell>{item.dataScope}</TableCell></TableRow></TableBody></Table>{visibleFindings.length > 0 && <div className="ai-finding-grid">{visibleFindings.map((finding, index) => <article key={`${finding.title}-${index}`}><h5>{finding.title}</h5><p>{finding.text}</p></article>)}</div>}{visibleTables.map((table, index) => <HarnessDataTable key={`${table.title}-${index}`} table={table} />)}{parsed.findings.length > 5 && <details className="harness-more"><summary>查看其余结论</summary>{parsed.findings.slice(5).map((finding, index) => <article key={`more-${index}`}><h5>{finding.title}</h5><p>{finding.text}</p></article>)}</details>}{parsed.cautions.length > 0 && <><h4>数据边界</h4><ul className="report-list">{parsed.cautions.slice(0, 6).map((caution, index) => <li key={`${caution}-${index}`}>{caution}</li>)}</ul></>}{!parsed.jsonValid && <p className="form-error">{harnessParseNotice(parsed.parseError, '输出')}</p>}<details className="report-raw"><summary>查看原始 JSON</summary><pre>{item.raw || ''}</pre></details></section>;
}

function ReportView({ report }: { report: Report }) {
  return (
    <div className="report-document">
      <div className="report-document-head">
        <div>
          <h3>{report.title}</h3>
          <p>
            {report.source} · {report.scope}
          </p>
        </div>
        <span className="status-good">{report.generatedBy}</span>
      </div>
      <p className="report-summary">{report.summary}</p>
      {report.aiPresentation && (
        <section className="ai-report-reading">
          <div className="ai-report-reading-head"><Sparkles size={16} /><b>AI 排版解读</b><span>已保留原始数据边界</span></div>
          <p>{report.aiPresentation.headline}</p>
          <div className="ai-finding-grid">
            {report.aiPresentation.findings.map((item, index) => <article key={`${item.title}-${index}`}><h5>{item.title}</h5><p>{item.text}</p></article>)}
          </div>
          {report.aiPresentation.tables?.map((table, index) => <HarnessDataTable key={`${table.title}-${index}`} table={table} />)}
          {report.aiPresentation.jsonValid === false && <p className="form-error">{harnessParseNotice(report.aiPresentation.parseError, '模型输出')}</p>}
        </section>
      )}
      <ReportVisual report={report} />
      <h4>一、市场概况</h4>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>指标</TableHead>
            <TableHead>数值</TableHead>
            <TableHead>说明</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {report.metrics.map((row) => (
            <TableRow key={row.label}>
              <TableCell>{row.label}</TableCell>
              <TableCell className="numeric">
                <b>{row.value}</b>
              </TableCell>
              <TableCell>{row.detail}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <h4>二、指数表现</h4>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>指数</TableHead>
            <TableHead>收盘</TableHead>
            <TableHead>涨跌</TableHead>
            <TableHead>日期</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {report.indices.map((row) => (
            <TableRow key={row.code}>
              <TableCell>
                {row.name}
                <small className="table-sub">{row.code}</small>
              </TableCell>
              <TableCell className="numeric">{row.close.toFixed(2)}</TableCell>
              <TableCell className={`numeric ${row.pct >= 0 ? 'up' : 'down'}`}>
                {p(row.pct)}
              </TableCell>
              <TableCell>{d(row.date)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <h4>三、主线与板块候选（TDX行业/主题聚合）</h4>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>方向</TableHead>
            <TableHead>样本数</TableHead>
            <TableHead>平均涨跌</TableHead>
            <TableHead>成交额</TableHead>
            <TableHead>代表股</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {report.themes.map((row) => (
            <TableRow key={row.name}>
              <TableCell>
                <b>{row.name}</b>
                <small className="table-sub">{row.tag}</small>
              </TableCell>
              <TableCell>{row.count}</TableCell>
              <TableCell
                className={`numeric ${row.avgPct >= 0 ? 'up' : 'down'}`}
              >
                {p(row.avgPct)}
              </TableCell>
              <TableCell className="numeric">{money(row.amount)}</TableCell>
              <TableCell>
                {row.leaders.map((x) => x.name).join('、') || '—'}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <p className="muted-copy">
        主线候选优先使用 TDX 主题成员，其次使用 TDX 行业成员；代表股按同日涨跌与成交额排序，仅作候选参考。
      </p>
      <h5>TDX 行业板块涨幅榜</h5>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>板块</TableHead>
            <TableHead>样本</TableHead>
            <TableHead>平均涨跌</TableHead>
            <TableHead>成交额</TableHead>
            <TableHead>涨停家数</TableHead>
            <TableHead>代表股</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {(report.sectors || []).slice(0, 12).map((row) => (
            <TableRow key={`sector-${row.code}`}>
              <TableCell>
                <b>{row.name}</b>
                <small className="table-sub">{row.code}</small>
              </TableCell>
              <TableCell>{row.count}</TableCell>
              <TableCell className={`numeric ${(row.avgPct || 0) >= 0 ? 'up' : 'down'}`}>
                {p(row.avgPct || 0)}
              </TableCell>
              <TableCell className="numeric">{money(row.amount || 0)}</TableCell>
              <TableCell>{row.limitCount ?? 0}</TableCell>
              <TableCell>{(row.leaders || []).map((x) => x.name).join('、') || '—'}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <p className="muted-copy">
        行业榜来源：C:\\new_tdx_mock\\T0002\\hq_cache\\tdxhy.cfg 与 cloud_cfg 行业树；未标注为申万或交易所官方板块指数。
      </p>
      <h4>四、涨停与连板候选</h4>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>股票</TableHead>
            <TableHead>涨跌</TableHead>
            <TableHead>阈值</TableHead>
            <TableHead>连续候选</TableHead>
            <TableHead>成交额</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {report.ladder.map((row) => (
            <TableRow key={row.stock.code}>
              <TableCell>
                {row.stock.name}
                <small className="table-sub">{row.stock.code}</small>
              </TableCell>
              <TableCell className="numeric up">{p(row.currentPct)}</TableCell>
              <TableCell>{row.limitPct}%</TableCell>
              <TableCell>{row.streak} 天</TableCell>
              <TableCell className="numeric">
                {money(row.stock.amount)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <h4>五、个股强弱与成交额榜</h4>
      <div className="report-rank-grid">
        <div>
          <h5>涨幅领先（候选）</h5>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>股票</TableHead>
                <TableHead>涨跌</TableHead>
                <TableHead>成交额</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(report.gainLeaders || []).map((row) => (
                <TableRow key={`gain-${row.code}`}>
                  <TableCell>
                    {row.name}
                    <small className="table-sub">{row.code}</small>
                  </TableCell>
                  <TableCell className="numeric up">{p(row.pct)}</TableCell>
                  <TableCell className="numeric">{money(row.amount)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        <div>
          <h5>成交额领先</h5>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>股票</TableHead>
                <TableHead>涨跌</TableHead>
                <TableHead>成交额</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(report.amountLeaders || []).map((row) => (
                <TableRow key={`amount-${row.code}`}>
                  <TableCell>
                    {row.name}
                    <small className="table-sub">{row.code}</small>
                  </TableCell>
                  <TableCell className={`numeric ${row.pct >= 0 ? 'up' : 'down'}`}>
                    {p(row.pct)}
                  </TableCell>
                  <TableCell className="numeric">{money(row.amount)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
      <p className="muted-copy">
        榜单来自同日收盘日线；这些是“龙头候选”证据，仍需板块归属、龙虎榜和盘中行为确认。
      </p>
      <h4>六、负反馈与前日涨停表现（本地推导）</h4>
      <div className="report-rank-grid">
        <div>
          <h5>跌幅领先（负反馈候选）</h5>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>股票</TableHead>
                <TableHead>涨跌</TableHead>
                <TableHead>成交额</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(report.lossLeaders || []).map((row) => (
                <TableRow key={`loss-${row.code}`}>
                  <TableCell>
                    {row.name}
                    <small className="table-sub">{row.code}</small>
                  </TableCell>
                  <TableCell className="numeric down">{p(row.pct)}</TableCell>
                  <TableCell className="numeric">{money(row.amount)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        <div>
          <h5>跌停阈值候选</h5>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>股票</TableHead>
                <TableHead>涨跌</TableHead>
                <TableHead>成交额</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(report.limitDownCandidates || []).map((row) => (
                <TableRow key={`limit-down-${row.code}`}>
                  <TableCell>
                    {row.name}
                    <small className="table-sub">{row.code}</small>
                  </TableCell>
                  <TableCell className="numeric down">{p(row.pct)}</TableCell>
                  <TableCell className="numeric">{money(row.amount)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
      {report.priorLimitUpStats && (
        <p className="muted-copy">
          前一交易日 {report.priorLimitUpStats.previousDate || '—'} 涨停候选{' '}
          {report.priorLimitUpStats.count || 0} 只，今日平均{' '}
          {report.priorLimitUpStats.todayAvgPct == null
            ? '—'
            : p(report.priorLimitUpStats.todayAvgPct)}；上涨{' '}
          {report.priorLimitUpStats.todayUp || 0} 只、下跌{' '}
          {report.priorLimitUpStats.todayDown || 0} 只、平盘{' '}
          {report.priorLimitUpStats.todayFlat || 0} 只。该指标由历史日线推导，仍需官方涨停池快照复核。
        </p>
      )}
      {report.intradayProxy && (
        <>
          <h4>七、盘中封板与炸板（OHLC代理）</h4>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>指标</TableHead>
                <TableHead>数值</TableHead>
                <TableHead>口径</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow><TableCell>涨停触板</TableCell><TableCell>{report.intradayProxy.upperHitCount} 只</TableCell><TableCell>日线最高价达到涨停阈值</TableCell></TableRow>
              <TableRow><TableCell>收盘封板</TableCell><TableCell>{report.intradayProxy.upperClosedCount} 只</TableCell><TableCell>触板且收盘仍在阈值</TableCell></TableRow>
              <TableRow><TableCell>触板后开板</TableCell><TableCell>{report.intradayProxy.openedAfterHitCount} 只</TableCell><TableCell>触板但收盘未封</TableCell></TableRow>
              <TableRow><TableCell>代理封板率</TableCell><TableCell>{report.intradayProxy.sealRatePct == null ? '—' : `${report.intradayProxy.sealRatePct.toFixed(2)}%`}</TableCell><TableCell>收盘封板 ÷ 触板</TableCell></TableRow>
              <TableRow><TableCell>代理炸板率</TableCell><TableCell>{report.intradayProxy.explosionRatePct == null ? '—' : `${report.intradayProxy.explosionRatePct.toFixed(2)}%`}</TableCell><TableCell>触板后开板 ÷ 触板</TableCell></TableRow>
              <TableRow><TableCell>同日5分钟文件</TableCell><TableCell>{report.intradayProxy.lc5CurrentDateCount} / {report.intradayProxy.lc5Files}</TableCell><TableCell>{report.intradayProxy.dataFresh ? '可用于同日盘中复核' : '当前文件日期不匹配'}</TableCell></TableRow>
              <TableRow><TableCell>首封时刻 / 封单额</TableCell><TableCell>未提供</TableCell><TableCell>需要同日1分钟或逐笔/盘口快照</TableCell></TableRow>
            </TableBody>
          </Table>
          <p className="muted-copy">上述涨停数据由日线 high/close 复算，属于可复算代理，不等同于官方盘中封板、回封或封单数据。</p>
        </>
      )}
      <h4>八、数据充分性与缺口</h4>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>数据项</TableHead>
            <TableHead>状态</TableHead>
            <TableHead>当前证据</TableHead>
            <TableHead>解决办法</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {(report.availability || []).map((row) => (
            <TableRow key={row.item}>
              <TableCell><b>{row.item}</b></TableCell>
              <TableCell>
                <span className={`availability-${row.status === '可用' ? 'ok' : row.status === '推导' ? 'derived' : row.status === '按需' ? 'ondemand' : 'missing'}`}>
                  {row.status}
                </span>
              </TableCell>
              <TableCell>{row.evidence}</TableCell>
              <TableCell>{row.solution}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <h4>九、风险与下一步</h4>
      <ul className="report-list">
        {report.cautions.map((x) => (
          <li key={x}>{x}</li>
        ))}
        {report.actions.map((x) => (
          <li key={x}>
            <b>下一步：</b>
            {x}
          </li>
        ))}
      </ul>
      {report.raw && (
        <details className="report-raw">
          <summary>查看 Harness 原始 JSON</summary>
          <pre>{report.raw}</pre>
        </details>
      )}
    </div>
  );
}

export default function WorkspacePages({
  page,
  market,
  onSelect,
  onSelectCode,
  onRefreshMarket,
  marketRefreshing = false,
  marketRefreshMessage = '',
  watch,
  onWatch,
  navigate,
}: {
  page: string;
  market: Market;
  onSelect: (s: Stock) => void;
  onSelectCode?: (code: string) => boolean;
  onRefreshMarket?: () => Promise<void> | void;
  marketRefreshing?: boolean;
  marketRefreshMessage?: string;
  watch: string[];
  onWatch: (code: string) => void;
  navigate: (id: string) => void;
}) {
  const [search, setSearch] = useState(''),
    [group, setGroup] = useState('all'),
    [skill, setSkill] = useState<Skill | null>(null),
    [researchCode, setResearchCode] = useState(''),
    [researchCodeError, setResearchCodeError] = useState(''),
    [theme, setTheme] = useState(0),
    [selectedStrategy, setSelectedStrategy] = useState('golden-ignition-v8');
  const [minPct, setMinPct] = useState('3'),
    [minAmount, setMinAmount] = useState('1'),
    [filterRan, setFilterRan] = useState(false),
    [filtered, setFiltered] = useState<Stock[]>([]),
    [filterError, setFilterError] = useState(''),
    [report, setReport] = useState<Report | null>(() =>
      loadReport(market.date),
    ),
    [reportBusy, setReportBusy] = useState(false),
    [aiBusy, setAiBusy] = useState(false),
    [aiError, setAiError] = useState(''),
    [skillBusy, setSkillBusy] = useState(false),
    [skillOutput, setSkillOutput] = useState(''),
    [skillHarnessBusy, setSkillHarnessBusy] = useState(false),
    [skillHarnessOutput, setSkillHarnessOutput] = useState(''),
    [skillHarnessError, setSkillHarnessError] = useState(''),
    [harnessSkillId, setHarnessSkillId] = useState(''),
    [harnessStartedAt, setHarnessStartedAt] = useState<number | null>(null),
    [harnessElapsed, setHarnessElapsed] = useState(0),
    [pageNo, setPageNo] = useState(0),
    [sort, setSort] = useState('gain'),
    [archiveRows, setArchiveRows] = useState<ReportArchiveRecord[]>(() =>
      loadReportArchive().filter(shouldShowInMyReports),
    ),
    [openedArchive, setOpenedArchive] = useState<ReportArchiveRecord | null>(null),
    [watchRefreshing, setWatchRefreshing] = useState(false),
    [watchRefreshMessage, setWatchRefreshMessage] = useState(''),
    [strategyRuns, setStrategyRuns] = useState<Record<string, StrategyRun>>({}),
    [strategyPrefsReady, setStrategyPrefsReady] = useState(false);
  const [singleSignalCode, setSingleSignalCode] = useState('');
  const [singleSignalBusy, setSingleSignalBusy] = useState(false);
  const [singleSignalError, setSingleSignalError] = useState('');
  const [singleSignalResult, setSingleSignalResult] = useState<SingleSignalResult | null>(null);
  const resumedStrategyIds = useRef(new Set<string>());
  const [, forceWatchRender] = useState(0);
  useEffect(() => {
    if (!openedArchive) return;
    window.requestAnimationFrame(() => {
      document.querySelector<HTMLElement>('.archive-sheet')?.scrollTo({ top: 0, left: 0, behavior: 'auto' });
    });
  }, [openedArchive?.id]);
  useEffect(() => {
    if (!skill) return;
    window.requestAnimationFrame(() => {
      document.querySelector<HTMLElement>('.skill-sheet')?.scrollTo({ top: 0, left: 0, behavior: 'auto' });
    });
  }, [skill?.id]);
  const [capitalSnapshot, setCapitalSnapshot] = useState<CapitalSnapshot | null>(null);
  const [capitalHarnessOutput, setCapitalHarnessOutput] = useState('');
  const [capitalLoading, setCapitalLoading] = useState(false);
  const [capitalRefreshNonce, setCapitalRefreshNonce] = useState(0);
  const [mainlineHarnessOutput, setMainlineHarnessOutput] = useState('');
  const [mainlineHarnessLoading, setMainlineHarnessLoading] = useState(false);
  const [environmentSnapshot, setEnvironmentSnapshot] = useState<Record<string, unknown> | null>(null);
  const [environmentLoading, setEnvironmentLoading] = useState(false);
  const [environmentMessage, setEnvironmentMessage] = useState('');
  const [dailyRefreshRunning, setDailyRefreshRunning] = useState(false);
  const [indexRebuildRunning, setIndexRebuildRunning] = useState(false);
  const [supplementalRefreshRunning, setSupplementalRefreshRunning] = useState(false);
  const [unifiedArchiveRunning, setUnifiedArchiveRunning] = useState(false);
  const [unifiedVerificationRunning, setUnifiedVerificationRunning] = useState(false);
  const [resourceLibraryContext, setResourceLibraryContext] = useState<Record<string, unknown> | null>(null);
  useEffect(() => {
    let active = true;
    void fetch(bridgeUrl('/runtime/resource-context'), { cache: 'no-store' })
      .then((response) => response.ok ? response.json() : null)
      .then((value) => {
        if (active && value && typeof value === 'object') setResourceLibraryContext(value as Record<string, unknown>);
      })
      .catch(() => undefined);
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (page !== 'capital') return;
    let active = true;
    setCapitalLoading(true);
    Promise.all([
      fetch(bridgeUrl('/data/public'), { cache: 'no-store' }).then((response) => response.ok ? response.json() : null),
      fetch(bridgeUrl('/data/harness/daily'), { cache: 'no-store' }).then((response) => response.ok ? response.json() : null),
    ]).then(([snapshot, context]) => {
      if (!active) return;
      setCapitalSnapshot(snapshot as CapitalSnapshot | null);
      const output = context?.harness?.output;
      setCapitalHarnessOutput(typeof output === 'string' ? output : '');
    }).catch(() => {
      if (active) { setCapitalSnapshot(null); setCapitalHarnessOutput(''); }
    }).finally(() => { if (active) setCapitalLoading(false); });
    return () => { active = false; };
  }, [page, capitalRefreshNonce]);
  useEffect(() => {
    if (page !== 'mainline') return;
    let active = true;
    setMainlineHarnessLoading(true);
    fetch(bridgeUrl('/data/harness/skill/short-term-sentiment-v22'), { cache: 'no-store' })
      .then((response) => response.ok ? response.json() : null)
      .then((job) => {
        if (!active) return;
        const raw = typeof job?.output === 'string' ? job.output : '';
        setMainlineHarnessOutput(raw);
        if (raw && (!job?.status || job.status === 'completed')) {
          const parsed = parseHarnessOutput(raw);
          const reportDate = String(parsed.dataDate || job?.date || market.date || '');
          const time = new Date().toISOString();
          void saveReportArchive({
            id: createReportId('mainline'),
            archiveKey: `mainline:${reportDate}:short-term-sentiment-v22`,
            createdAt: time,
            updatedAt: time,
            date: reportDate,
            title: `主线追踪 · A股短线市场情绪 V2.2 · ${d(reportDate)}`,
            reportType: '主线追踪 Harness 报告',
            generatedBy: 'DeepSeek Harness · short-term-sentiment-v22',
            summary: parsed.summary || '主线追踪研究报告已完成。',
            dataScope: parsed.dataScope || `市场情绪技能 · ${reportDate || '日期未提供'}`,
            content: { kind: 'harness-skill', skillId: 'short-term-sentiment-v22', skillName: 'A股短线市场情绪 V2.2', raw },
            raw,
          });
        }
      })
      .catch(() => { if (active) setMainlineHarnessOutput(''); })
      .finally(() => { if (active) setMainlineHarnessLoading(false); });
    return () => { active = false; };
  }, [page]);
  const capitalRows = useMemo(() => normalizeCapitalRows(capitalSnapshot), [capitalSnapshot]);
  const themes = useMemo(
    () => buildThemes(market.stocks, market.conceptBoards || [], market.sectors || []),
    [market.stocks, market.conceptBoards, market.sectors],
  );
  const ladder = useMemo(
    () => buildLadder(market.stocks, market.tdxLimitUpCodes || []),
    [market.stocks, market.tdxLimitUpCodes],
  );
  const gainLeaders = useMemo(() => rankRows(market.stocks, 'pct', 20), [market.stocks]);
  const amountLeaders = useMemo(() => rankRows(market.stocks, 'amount', 20), [market.stocks]);
  const lossLeaders = useMemo(() => rankRows(market.stocks, 'loss', 20), [market.stocks]);
  const limitDownCandidates = useMemo(
    () =>
      market.tdxLimitDownCodes?.length
        ? market.stocks
            .filter((s) => market.tdxLimitDownCodes?.includes(s.code))
            .sort((a, b) => a.pct - b.pct)
            .slice(0, 20)
            .map(({ code, name, pct, amount, close, market: venue }) => ({
              code,
              name,
              pct,
              amount,
              close,
              market: venue,
            }))
        : lossLeaders.filter((s) => s.pct < -9.5),
    [market.stocks, market.tdxLimitDownCodes, lossLeaders],
  );
  const related = skills.filter((x) => x.group === page);
  const visibleSkills = skills.filter(
    (item) =>
      (group === 'all' || item.group === group) &&
      `${item.name} ${item.alias} ${item.id}`.includes(search),
  );
  const visibleSkillGroups = Object.entries(groupNames).filter(([groupId]) =>
    visibleSkills.some((item) => item.group === groupId),
  );
  const selectedStrategyRun = strategyRuns[selectedStrategy] || { busy: false, output: '', harnessOutput: '', status: '', phase: '', startedAt: null, elapsed: 0 };
  const selectedStrategyHasReport = strategyRunHasReport(selectedStrategyRun);
  const selectedStrategyHasFailure = strategyRunHasFailure(selectedStrategyRun);
  const selectedStrategyMeta = strategyCatalogItem(selectedStrategy);
  const selectedStrategyStatus = strategyDataStatus(selectedStrategy);
  // 个股研究使用 resource-library 的完整日线档案。若请求日未落盘，
  // 桥接层会把 rows 统一降级到最近完整交易日；这里不能再按“当日”
  // 过滤，否则会把合法的最近交易日档案全部过滤掉。
  const searchableStocks = useMemo(() => {
    const source = market.allStocks?.length ? market.allStocks : market.stocks;
    return source.filter((row) => Boolean(row.code && row.date));
  }, [market.allStocks, market.stocks]);
  const filteredStocks = useMemo(() => {
    let rows = searchableStocks.filter((x) =>
      `${x.name} ${x.code}`.includes(search.trim()),
    );
    if (sort === 'gain') rows = [...rows].sort((a, b) => b.pct - a.pct || b.amount - a.amount);
    if (sort === 'amount') rows = [...rows].sort((a, b) => b.amount - a.amount);
    if (sort === 'loss') rows = [...rows].sort((a, b) => a.pct - b.pct);
    return rows;
  }, [searchableStocks, search, sort]);
  const harnessRunning = aiBusy || skillBusy || skillHarnessBusy;
  async function refreshEnvironment() {
    if (environmentLoading) return;
    setEnvironmentLoading(true);
    setEnvironmentMessage('正在检测通达信、日线文件和 DeepSeek Harness…');
    try {
      const readEnvironment = async () => {
        const response = await fetch(bridgeUrl('/runtime/environment'), { cache: 'no-store' });
        const body = await response.json().catch(() => ({}));
        if (!response.ok || body.status !== 'ok') throw new Error(body.error || `运行环境检测失败（${response.status}）`);
        return body as Record<string, unknown>;
      };
      let body: Record<string, unknown>;
      try {
        body = await readEnvironment();
      } catch (firstError) {
        // 桥接进程停止时由网页服务器触发本地启动脚本，再重试一次。
        await fetch('/api/runtime/ensure-bridge', { method: 'POST' }).catch(() => undefined);
        await new Promise((resolve) => window.setTimeout(resolve, 1400));
        body = await readEnvironment().catch(() => { throw firstError; });
      }
      setEnvironmentSnapshot(body as Record<string, unknown>);
      const dailyState = body.dailyRefresh as Record<string, unknown> | undefined;
      setDailyRefreshRunning(dailyState?.status === 'running');
      const indexState = body.dailyIndexInitialization as Record<string, unknown> | undefined;
      setIndexRebuildRunning(indexState?.status === 'running');
      const archiveState = body.unifiedArchive as Record<string, unknown> | undefined;
      const verificationState = body.unifiedVerification as Record<string, unknown> | undefined;
      setUnifiedArchiveRunning(archiveState?.status === 'running');
      setUnifiedVerificationRunning(verificationState?.status === 'running');
      const checkedAt = typeof body.checkedAt === 'string' || typeof body.checkedAt === 'number' ? body.checkedAt : Date.now();
      setEnvironmentMessage(`检测完成 · ${new Date(checkedAt).toLocaleTimeString('zh-CN', { hour12: false })}`);
    } catch (error) {
      setEnvironmentMessage(error instanceof Error ? error.message : '运行环境检测失败');
    } finally {
      setEnvironmentLoading(false);
    }
  }
  async function openTongdaxin() {
    setEnvironmentMessage('正在打开通达信客户端…');
    try {
      const response = await fetch(bridgeUrl('/runtime/tdx/open'), { method: 'POST' });
      const body = await response.json().catch(() => ({}));
      if (!response.ok || !['accepted', 'already_open'].includes(String(body.status))) throw new Error(body.error || '打开通达信失败');
      setEnvironmentMessage(body.status === 'already_open' ? '通达信已打开，请完成登录后重新检测。' : '已请求打开通达信，请完成登录后重新检测。');
      window.setTimeout(() => { void refreshEnvironment(); }, 2500);
    } catch (error) {
      setEnvironmentMessage(error instanceof Error ? error.message : '打开通达信失败');
    }
  }
  useEffect(() => {
    if (page !== 'settings') return;
    void refreshEnvironment();
  }, [page]);
  async function replenishDailyData() {
    if (dailyRefreshRunning) return;
    setDailyRefreshRunning(true);
    setEnvironmentMessage('已提交 Harness 日线补全任务：正在调用通达信并等待 DeepSeek 校验…');
    try {
      const started = await startDailyDataRefresh({ force: true });
      let status = started.state?.status || started.job?.status || 'running';
      for (let attempt = 0; attempt < 180 && status === 'running'; attempt += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 2000));
        const current = await getDailyDataRefreshStatus();
        const currentState = current.state as Record<string, unknown> | undefined;
        const steps = Array.isArray(currentState?.steps) ? currentState.steps as Record<string, unknown>[] : [];
        const activeStep = steps.find((step) => step.status === 'running');
        if (activeStep) {
          const startedAt = Date.parse(String(activeStep.startedAt || ''));
          const elapsed = Number.isFinite(startedAt) ? Math.max(0, Math.floor((Date.now() - startedAt) / 1000)) : 0;
          const mm = String(Math.floor(elapsed / 60)).padStart(2, '0');
          const ss = String(elapsed % 60).padStart(2, '0');
          setEnvironmentMessage(`${String(activeStep.name || '日线补全')}进行中 · 已运行 ${mm}:${ss} · 通达信正在处理，完成后由 DeepSeek Harness 校验`);
        } else if (currentState?.harness && typeof currentState.harness === 'object' && (currentState.harness as Record<string, unknown>).status === 'pending') {
          setEnvironmentMessage('通达信日线步骤已结束 · 正在等待 DeepSeek Harness 校验结果');
        }
        const latestJob = Array.isArray(current.jobs)
          ? current.jobs.at(-1) as Record<string, unknown> | undefined
          : undefined;
        status = String(currentState?.status || latestJob?.status || '') || status;
      }
      setEnvironmentMessage(status === 'completed' ? '日线补全与 Harness 校验已完成。' : status === 'partial' ? '日线补全已结束，但有步骤未完成，请查看下方状态。' : '日线补全仍在后台运行，可稍后重新检测。');
      await refreshEnvironment();
    } catch (error) {
      setEnvironmentMessage(error instanceof Error ? error.message : '日线补全启动失败');
    } finally {
      setDailyRefreshRunning(false);
    }
  }
  async function rebuildAllIndices() {
    if (indexRebuildRunning || dailyRefreshRunning) return;
    setIndexRebuildRunning(true);
    setEnvironmentMessage('已提交初始化任务：正在扫描所选通达信目录全部 .day，并重建全量个股索引；完成后复核本地 canonical 日线库…');
    try {
      const started = await startDailyIndexInitialization({ force: true });
      let status = String(started.state?.status || started.job?.status || 'running');
      for (let attempt = 0; attempt < 900 && status === 'running'; attempt += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 2000));
        const current = await getDailyIndexInitializationStatus();
        const state = current.state || {};
        const steps = Array.isArray(state.steps) ? state.steps as Record<string, unknown>[] : [];
        const activeStep = steps.find((step) => step.status === 'running');
        if (activeStep) {
          const startedAt = Date.parse(String(activeStep.startedAt || ''));
          const elapsed = Number.isFinite(startedAt) ? Math.max(0, Math.floor((Date.now() - startedAt) / 1000)) : 0;
          const mm = String(Math.floor(elapsed / 60)).padStart(2, '0');
          const ss = String(elapsed % 60).padStart(2, '0');
          setEnvironmentMessage(`${String(activeStep.name || '全量索引初始化')}进行中 · 已运行 ${mm}:${ss} · 页面可继续使用`);
        }
        const latestJob = Array.isArray(current.jobs)
          ? current.jobs.at(-1) as Record<string, unknown> | undefined
          : undefined;
        status = String(state.status || latestJob?.status || '') || status;
      }
      setEnvironmentMessage(status === 'completed'
        ? '初始化完成：已重建通达信股票索引和本地全历史日线定位索引。'
        : status === 'partial'
          ? '初始化已完成本地全历史索引，但通达信目录存在缺口；详见下方步骤状态。'
          : status === 'failed'
            ? '初始化失败：请检查通达信安装目录、磁盘空间和数据包是否完整。'
            : '初始化仍在后台运行，可稍后重新检测。');
      await refreshEnvironment();
    } catch (error) {
      setEnvironmentMessage(error instanceof Error ? error.message : '全量个股索引初始化启动失败');
    } finally {
      setIndexRebuildRunning(false);
    }
  }
  async function replenishSupplementalData() {
    if (supplementalRefreshRunning) return;
    setSupplementalRefreshRunning(true);
    setEnvironmentMessage('已提交 Harness 其他数据补齐任务：正在刷新公开行情、龙虎榜、涨停池和新闻…');
    try {
      const started = await startSupplementalDataRefresh({ force: true });
      let status = started.state?.status || started.job?.status || 'running';
      for (let attempt = 0; attempt < 180 && status === 'running'; attempt += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 2000));
        const current = await getSupplementalDataRefreshStatus();
        const latestJob = Array.isArray(current.jobs)
          ? current.jobs.at(-1) as Record<string, unknown> | undefined
          : undefined;
        status = current.state?.status || String(latestJob?.status || '') || status;
      }
      setEnvironmentMessage(status === 'completed' ? '其他数据补齐与 Harness 校验已完成。' : status === 'partial' ? '其他数据补齐结束，但有来源未通过校验，请查看来源状态。' : '其他数据补齐仍在后台运行，可稍后重新检测。');
      await refreshEnvironment();
    } catch (error) {
      setEnvironmentMessage(error instanceof Error ? error.message : '其他数据补齐启动失败');
    } finally {
      setSupplementalRefreshRunning(false);
    }
  }
  async function archiveAllData() {
    if (unifiedArchiveRunning) return;
    setUnifiedArchiveRunning(true);
    setEnvironmentMessage('已提交统一数据落盘任务：正在汇总日线、行情、资讯、公式证据和本地来源清单…');
    try {
      const started = await startUnifiedDataArchive({ force: true });
      let status = started.state?.status || started.job?.status || 'running';
      for (let attempt = 0; attempt < 180 && status === 'running'; attempt += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 2000));
        const current = await getUnifiedDataArchiveStatus();
        const currentState = current.state as Record<string, unknown> | undefined;
        const steps = Array.isArray(currentState?.steps) ? currentState.steps as Record<string, unknown>[] : [];
        const activeStep = steps.find((step) => step.status === 'running');
        if (activeStep) setEnvironmentMessage(`统一数据落盘：${String(activeStep.name || '正在执行')} · 所有可用数据将写入 resource-library`);
        const latestJob = Array.isArray(current.jobs)
          ? current.jobs.at(-1) as Record<string, unknown> | undefined
          : undefined;
        status = String(currentState?.status || latestJob?.status || '') || status;
      }
      setEnvironmentMessage(status === 'completed' ? '统一数据落盘已完成，来源清单已更新。' : status === 'partial' ? '统一数据落盘已结束，但有来源未配置或步骤失败，请查看来源清单。' : '统一数据落盘仍在后台运行，可稍后重新检测。');
      await refreshEnvironment();
    } catch (error) {
      setEnvironmentMessage(error instanceof Error ? error.message : '统一数据落盘启动失败');
    } finally {
      setUnifiedArchiveRunning(false);
    }
  }
  async function verifyAllData() {
    if (unifiedVerificationRunning) return;
    setUnifiedVerificationRunning(true);
    setEnvironmentMessage('已提交本地数据校验任务：正在校验文件、来源清单，并调用 DeepSeek Harness…');
    try {
      const started = await startUnifiedDataVerification({ force: true });
      let status = started.state?.status || started.job?.status || 'running';
      for (let attempt = 0; attempt < 180 && status === 'running'; attempt += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 2000));
        const current = await getUnifiedDataVerificationStatus();
        const currentState = current.state as Record<string, unknown> | undefined;
        const steps = Array.isArray(currentState?.steps) ? currentState.steps as Record<string, unknown>[] : [];
        const activeStep = steps.find((step) => step.status === 'running');
        if (activeStep) setEnvironmentMessage(`本地数据校验：${String(activeStep.name || '正在执行')} · 完成后写入校验回执`);
        const latestJob = Array.isArray(current.jobs)
          ? current.jobs.at(-1) as Record<string, unknown> | undefined
          : undefined;
        status = String(currentState?.status || latestJob?.status || '') || status;
      }
      setEnvironmentMessage(status === 'completed' ? '本地数据校验与 Harness 复核已完成。' : status === 'partial' ? '本地数据校验完成，但有来源或 Harness 未通过，请查看校验回执。' : '本地数据校验仍在后台运行，可稍后重新检测。');
      await refreshEnvironment();
    } catch (error) {
      setEnvironmentMessage(error instanceof Error ? error.message : '本地数据校验启动失败');
    } finally {
      setUnifiedVerificationRunning(false);
    }
  }
  async function refreshWatchlist() {
    if (watchRefreshing || !watch.length) return;
    setWatchRefreshing(true);
    setWatchRefreshMessage('正在读取自选股实时行情…');
    try {
      const response = await fetch(bridgeUrl(`/market?scope=watchlist&codes=${encodeURIComponent(watch.join(','))}`), { cache: 'no-store' });
      const body = await response.json().catch(() => ({}));
      if (!response.ok || body.status !== 'ok') throw new Error(body.error || `自选行情服务返回 ${response.status}`);
      const updates = new Map<string, Stock>((body.stocks || []).map((row: Stock) => [row.code, row]));
      const merge = (rows: Stock[]) => rows.map((row) => updates.has(row.code) ? { ...row, ...updates.get(row.code) } : row);
      market.stocks = merge(market.stocks);
      if (market.allStocks) market.allStocks = merge(market.allStocks);
      forceWatchRender((v) => v + 1);
      setWatchRefreshMessage(`已刷新 ${updates.size} 只自选股 · ${new Date(body.fetchedAt || Date.now()).toLocaleTimeString('zh-CN', { hour12: false })}`);
    } catch (error) {
      setWatchRefreshMessage(error instanceof Error ? error.message : '自选股刷新失败');
    } finally {
      setWatchRefreshing(false);
    }
  }
  useEffect(() => {
    const refresh = () => setArchiveRows(loadReportArchive().filter(shouldShowInMyReports));
    void loadReportArchiveFromLocalRuntime().then((reports) => {
      if (reports.length) setArchiveRows(reports.filter(shouldShowInMyReports));
    });
    const migratedKey = `zhangcai.report.archive.migrated.${market.date}`;
    const legacy = loadReport(market.date);
    if (legacy && !localStorage.getItem(migratedKey)) {
      const now = new Date().toISOString();
      void saveReportArchive({
        id: createReportId('legacy-market'),
        archiveKey: 'market-review',
        createdAt: now,
        updatedAt: now,
        date: legacy.date,
        title: legacy.title,
        reportType: '历史复盘',
        generatedBy: legacy.generatedBy,
        summary: legacy.summary,
        dataScope: `${legacy.source} · ${legacy.scope}`,
        content: { kind: 'market-report', report: legacy as unknown as Record<string, unknown> },
        raw: legacy.raw,
      });
      localStorage.setItem(migratedKey, '1');
    }
    refresh();
    window.addEventListener(reportArchiveChangedEvent, refresh);
    return () => window.removeEventListener(reportArchiveChangedEvent, refresh);
  }, [market.date]);
  useEffect(() => {
    if (!harnessStartedAt) return;
    const tick = () =>
      setHarnessElapsed(Math.max(0, Math.floor((Date.now() - harnessStartedAt) / 1000)));
    tick();
    const timer = window.setInterval(tick, 1000);
    return () => window.clearInterval(timer);
  }, [harnessStartedAt]);
  useEffect(() => {
    const timer = window.setInterval(() => {
      const now = Date.now();
      setStrategyRuns((previous) => {
        const next = { ...previous };
        for (const [id, run] of Object.entries(next)) {
          if (run.busy && run.startedAt) next[id] = { ...run, elapsed: Math.max(0, Math.floor((now - run.startedAt) / 1000)) };
        }
        return next;
      });
    }, 1000);
    return () => window.clearInterval(timer);
  }, []);
  useEffect(() => {
    try {
      const currentDate = String(market.date || '').replace(/\D/g, '').slice(0, 8);
      const savedRuns = loadStrategyRuns();
      // Strategy-run state is a current-date view. Keep completed historical
      // reports in the archive, but do not render a 0908 Harness result beside
      // a newly loaded 0911 market snapshot.
      const currentRuns = Object.fromEntries(Object.entries(savedRuns).filter(([, run]) => {
        if (run.busy || !currentDate) return true;
        const runDate = strategyRunDataDate(run);
        return !runDate || runDate === currentDate;
      }));
      setStrategyRuns(currentRuns);
      const saved = localStorage.getItem(selectedStrategyKey) || '';
      if (skills.some((item) => item.id === saved)) setSelectedStrategy(saved);
    } catch { /* 使用默认策略状态 */ }
    setStrategyPrefsReady(true);
  }, []);
  useEffect(() => {
    if (!strategyPrefsReady) return;
    try { localStorage.setItem(strategyRunsKey, JSON.stringify(strategyRuns)); } catch { /* 保留内存状态，等待下次刷新 */ }
  }, [strategyRuns, strategyPrefsReady]);
  useEffect(() => {
    if (!strategyPrefsReady) return;
    try { localStorage.setItem(selectedStrategyKey, selectedStrategy); } catch { /* 忽略本地存储不可用 */ }
  }, [selectedStrategy, strategyPrefsReady]);
  function beginHarness(skillId: string) {
    setHarnessSkillId(skillId);
    setHarnessStartedAt(Date.now());
    setHarnessElapsed(0);
  }
  function endHarness() {
    setHarnessSkillId('');
    setHarnessStartedAt(null);
    setHarnessElapsed(0);
  }
  async function archiveMarketReport(value: Report, reportType: string, archiveKey = 'market-review') {
    const now = new Date().toISOString();
    await saveReportArchive({
      id: createReportId('market'),
      archiveKey,
      createdAt: now,
      updatedAt: now,
      date: value.date,
      title: value.title,
      reportType,
      generatedBy: value.generatedBy,
      summary: value.summary,
      dataScope: `${value.source} · ${value.scope}`,
      content: { kind: 'market-report', report: value as unknown as Record<string, unknown> },
      raw: value.raw,
    });
  }
  function harnessProgress() {
    if (!harnessRunning || !harnessStartedAt) return null;
    const expected = estimateSeconds(harnessSkillId);
    const overdue = harnessElapsed > expected;
    return (
      <div className={`harness-progress ${overdue ? 'overdue' : ''}`} role="status">
        <LoaderCircle className="spin" size={15} />
        <span>
          {harnessSkillId || 'morning-intelligence-plan'} 运行中 · 已运行 {formatDuration(harnessElapsed)} ·
          预计 {formatDuration(expected)}
          {overdue ? ' · 已超过预计时间，仍在等待 Harness 返回' : ''}
        </span>
      </div>
    );
  }
  useEffect(() => {
    if (page === 'reports') setReport(loadReport(market.date));
  }, [page, market.date]);
  useEffect(() => {
    if (report)
      localStorage.setItem(reportKey(market.date), JSON.stringify(report));
  }, [report, market.date]);
  useEffect(() => {
    if (!report) return;
    const current = makeBaseReport(market, themes, ladder);
    const dataCorrection = `数据校正：本报告已提供 ${current.gainLeaders.length} 条当日涨幅榜、${current.amountLeaders.length} 条成交额榜、${current.ladder.length} 条 TDX 涨停/连板候选；其余 ${current.availability.filter((x) => x.status === '缺失').length} 项数据缺口已在下表逐项列出，因此当前结论仍标为“龙头候选”。`;
    if (
      (report.availability || []).length < current.availability.length ||
      (report.gainLeaders || []).length === 0 ||
      (report.amountLeaders || []).length === 0 ||
      (report.lossLeaders || []).length === 0 ||
      (report.limitDownCandidates || []).length === 0 ||
      !Array.isArray(report.sectors) ||
      !Array.isArray(report.conceptBoards) ||
      !report.intradayProxy ||
      (report.amountLeaders || []).some((value) => value.name === '北证50') ||
      !(report.summary || '').includes('结论仍标为“龙头候选”') ||
      (report.cautions || []).some((value) =>
        /不含行业、板块及个股明细|缺少行业\/板块涨跌幅/.test(value),
      )
    ) {
      setReport({
        ...report,
        metrics: current.metrics,
        indices: current.indices,
        themes: current.themes,
        gainLeaders: current.gainLeaders,
        amountLeaders: current.amountLeaders,
        lossLeaders: current.lossLeaders,
        limitDownCandidates: current.limitDownCandidates,
        priorLimitUpStats: current.priorLimitUpStats,
        sectors: current.sectors,
        conceptBoards: current.conceptBoards,
        intradayProxy: current.intradayProxy,
        availability: current.availability,
        ladder: current.ladder,
        summary: `${current.summary} ${dataCorrection}`,
        cautions: current.cautions,
        actions: current.actions,
      });
    }
  }, [report, market, themes, ladder]);
  const openById = (id: string) =>
    setSkill(skills.find((x) => x.id === id) || null);
  const marketPayload = {
    date: market.date,
    currentCount: market.currentCount,
    up: market.up,
    down: market.down,
    flat: market.flat,
    amount: market.amount,
    indices: market.indices.map((x) => ({
      name: x.name,
      close: x.close,
      pct: x.pct,
    })),
    gainLeaders,
    amountLeaders,
    lossLeaders,
    limitDownCandidates,
    priorLimitUpStats: market.priorLimitUpStats,
    sectors: market.sectors || [],
    conceptBoards: market.conceptBoards || [],
    intradayProxy: market.intradayProxy,
    dataSources: market.dataSources || {},
    supplemental: market.supplemental,
    limitCandidates: ladder.slice(0, 30).map((x) => ({
      code: x.stock.code,
      name: x.stock.name,
      pct: x.currentPct,
      limitPct: x.limitPct,
      streak: x.streak,
      amount: x.stock.amount,
    })),
    themes: themes.map((x) => ({
      name: x.name,
      tag: x.tag,
      count: x.count,
      avgPct: Number(x.avgPct.toFixed(2)),
      amount: x.amount,
      leaders: x.leaders.map((s) => s.name),
    })),
    tdxLimitUpSource: market.tdxLimitUpFiles || [],
  };
  async function callHarness(
    task: string,
    skillId = 'morning-intelligence-plan',
    _context?: unknown,
    label = skillId,
  ) {
    let latestResourceLibrary = resourceLibraryContext || {};
    try {
      const response = await fetch(bridgeUrl('/runtime/resource-context'), { cache: 'no-store' });
      if (response.ok) {
        latestResourceLibrary = await response.json() as Record<string, unknown>;
        setResourceLibraryContext(latestResourceLibrary);
      }
    } catch { /* 继续使用页面缓存，并在报告中保留资源库边界。 */ }
    const resourceContext = _context && typeof _context === 'object'
      ? { ...(_context as Record<string, unknown>), resourceLibrary: latestResourceLibrary }
      : { resourceLibrary: latestResourceLibrary };
    const result = await runHarnessInBackground({
      task,
      skillId,
      label,
      market: marketPayload,
      context: resourceContext,
      originPage: page,
      expectedSeconds: estimateSeconds(skillId),
    });
    return result.output;
  }
  const strategyHarnessPrompt = (name: string) => `请把“${name}”原始策略结果整理成简短网页报告，直接给出类似 Top10 选股列表的结构化结果。只返回一个严格 JSON 对象：status、summary、data_date、data_scope、cautions、findings、tables。tables 只保留一张“Top 候选”表，最多 10 行，列为排名、代码、名称、评分、波段、游资、机构、风险；如果没有候选，表格 rows 为空并在 cautions 说明原因。summary 不超过 80 字，findings 最多 3 条，每条不超过 50 字。只引用原始交付物和本地行情，不虚构结论。${HARNESS_JSON_SCHEMA}`;
  const selectionHarnessPrompt = (name: string, preflightStatus: string, scoreReceipt?: StrategyScoreResponse) => {
    const columns = name.includes('V6.5') ? '排名、代码、名称、评分、波段、主模型、游资、机构、风险' : '排名、代码、名称、评分、波段、游资、机构、风险';
    return `请对“${name}”完成策略选股网页分析。当前网页预检状态为 ${preflightStatus}，并已调用对应原始策略评分引擎完成本地数值回执。候选数组中的 score、wave、primary_model、primary_model_candidate、youzi、institution、risk 来自原始策略评分字段的网页适配展示；不得用涨幅、成交额、候选排名或 TDX 五公式复合分替代 score。必须原样引用 score_source、strategy_score_status、strategy_missing 和 strategy_fields 中能支持的字段。评分回执的 score_status=${scoreReceipt?.score_status || '未知'}；缺失项=${(scoreReceipt?.missing || []).join('、') || '无'}。若 score_status 为 DEGRADED，只能称为本地降级研究评分，必须在 cautions 写出缺失项；若为 BLOCKED，不得把候选表写成已执行策略结果。请严格基于传入的本地行情、原始评分回执、条件候选和预检结果输出分析。只返回一个严格 JSON 对象：status、summary、data_date、data_scope、cautions、findings、tables。tables 只保留一张“Top 候选”表，最多 10 行，列为${columns}；候选不足时 rows 为空并在 cautions 说明原因。summary 不超过 80 字，findings 最多 3 条，每条不超过 50 字。只读研究，不给出买卖建议，不虚构未传入的数据。${HARNESS_JSON_SCHEMA}`;
  };
  async function resumeStrategyAfterRefresh(target: Skill, run: StrategyRun, rawTask: HarnessTask, harnessTask?: HarnessTask) {
    const startedAt = run.startedAt || rawTask.startedAt || Date.now();
    let strategyOutput = run.output || rawTask.output || '';
    let strategyStructured = run.structured || (rawTask.structured && typeof rawTask.structured === 'object' ? rawTask.structured as StructuredStrategy : null);
    let strategyStatus = run.status || rawTask.strategyStatus || 'UNKNOWN';
    let receipt = run.receipt || (rawTask.receipt && typeof rawTask.receipt === 'object' ? rawTask.receipt as Record<string, unknown> : null);
    try {
      setStrategyRuns((previous) => ({ ...previous, [target.id]: { ...previous[target.id], busy: true, phase: rawTask.status === 'completed' ? 'harness' : 'strategy', startedAt, elapsed: Math.floor((Date.now() - startedAt) / 1000) } }));
      if (rawTask.status !== 'completed') {
        const result = await resumeHarnessTask(rawTask);
        strategyOutput = result.output || strategyOutput;
        strategyStructured = result.structured && typeof result.structured === 'object' ? result.structured as StructuredStrategy : strategyStructured;
        strategyStatus = result.status || strategyStatus;
        receipt = result.receipt && typeof result.receipt === 'object' ? result.receipt as Record<string, unknown> : receipt;
      }
      if (!strategyOutput) throw new Error('原始策略已恢复，但没有可供 Harness 解读的交付物');
      setStrategyRuns((previous) => ({ ...previous, [target.id]: { ...previous[target.id], busy: true, output: strategyOutput, status: strategyStatus, phase: 'harness', structured: strategyStructured, receipt, startedAt, elapsed: Math.floor((Date.now() - startedAt) / 1000) } }));
      let harnessOutput = run.harnessOutput || '';
      if (harnessTask && harnessTask.status !== 'completed') {
        const result = await resumeHarnessTask(harnessTask);
        harnessOutput = result.output;
      } else if (!harnessOutput) {
        harnessOutput = await callHarness(
          strategyHarnessPrompt(target.name),
          target.id,
          { strategy_status: strategyStatus, strategy_output: strategyOutput, strategy_delivery: strategyStructured },
          `${target.name} · Harness 解读`,
        );
      }
      setStrategyRuns((previous) => ({ ...previous, [target.id]: { ...previous[target.id], busy: false, output: strategyOutput, harnessOutput, status: 'CLEAN_PASS', phase: 'completed', structured: strategyStructured, receipt, startedAt: null, elapsed: Math.floor((Date.now() - startedAt) / 1000) } }));
      const now = new Date().toISOString();
      await saveReportArchive({
        id: `strategy-${target.id}-${Date.now()}`,
        archiveKey: `strategy:${target.id}:${market.date}`,
        createdAt: now,
        updatedAt: now,
        date: market.date,
        title: `掌财智能体 · ${target.name} · 策略运行报告`,
        reportType: '策略运行',
        generatedBy: '网页脚本 + DeepSeek Harness',
        summary: '刷新后已恢复原始策略与 Harness 解读，结构化报告已生成',
        dataScope: `本地日线归档 · ${d(market.date)} · 已恢复后台交付物`,
        content: { kind: 'strategy-run', strategyId: target.id, status: 'CLEAN_PASS', receipt, structured: strategyStructured, harnessOutput },
        raw: harnessOutput,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : '刷新后恢复策略失败';
      setStrategyRuns((previous) => ({ ...previous, [target.id]: { ...previous[target.id], busy: false, output: strategyOutput || message, harnessOutput: run.harnessOutput || '', status: 'ERROR', phase: 'resume_error', structured: strategyStructured, receipt, startedAt: null, elapsed: Math.floor((Date.now() - startedAt) / 1000) } }));
      setAiError(`${target.name} 刷新后恢复失败：${message}`);
    }
  }
  useEffect(() => {
    // 等待客户端恢复本地策略状态后再接管后台任务，避免刷新时漏掉正在运行的任务。
    if (!strategyPrefsReady || page !== 'selection') return;
    const tasks = getHarnessTasks();
    // 页面刷新或桥接重启后，localStorage 里可能残留 busy=true，但对应
    // 的后台任务已经不存在。先把这类孤儿状态收敛为失败/已完成，避免
    // 策略按钮永久显示“运行中”。
    setStrategyRuns((previous) => {
      let changed = false;
      const next = { ...previous };
      for (const [strategyId, run] of Object.entries(previous)) {
        if (!run.busy) continue;
        const target = skills.find((item) => item.id === strategyId);
        if (!target) continue;
        const after = (run.startedAt || 0) - 5000;
        const matches = tasks.filter((task) => task.skillId === strategyId && task.originPage === 'selection' && task.startedAt >= after);
        const rawTask = [...matches].reverse().find((task) => task.backendKind === 'strategy' && task.label === `策略 · ${target.name}`);
        if (rawTask) continue;
        changed = true;
        next[strategyId] = {
          ...run,
          busy: false,
          phase: run.harnessOutput || run.structured ? 'completed' : 'resume_error',
          status: run.harnessOutput || run.structured ? 'CLEAN_PASS' : 'ERROR',
          startedAt: null,
        };
      }
      return changed ? next : previous;
    });
    for (const [strategyId, run] of Object.entries(strategyRuns)) {
      if (!run.busy || resumedStrategyIds.current.has(strategyId)) continue;
      const target = skills.find((item) => item.id === strategyId);
      if (!target) continue;
      const after = (run.startedAt || 0) - 5000;
      const matches = tasks.filter((task) => task.skillId === strategyId && task.originPage === 'selection' && task.startedAt >= after);
      const rawTask = [...matches].reverse().find((task) => task.backendKind === 'strategy' && task.label === `策略 · ${target.name}`);
      if (!rawTask) continue;
      const harnessTask = [...matches].reverse().find((task) => task.backendKind === 'harness' && task.label === `${target.name} · Harness 解读`);
      resumedStrategyIds.current.add(strategyId);
      void resumeStrategyAfterRefresh(target, run, rawTask, harnessTask);
    }
  }, [page, strategyPrefsReady]);
  async function makeHarnessReport(
    skillId = 'morning-intelligence-plan',
    context?: unknown,
  ) {
    setAiBusy(true);
    beginHarness(skillId);
    setAiError('');
    try {
      const raw = await callHarness(
        `请按照技能职责完成当日A股研究复盘。${HARNESS_JSON_SCHEMA}不得给出买卖建议，不得虚构新闻、龙虎榜或实时数据。`,
        skillId,
        context,
      );
      const base = makeBaseReport(market, themes, ladder);
      const parsed = parseHarnessOutput(raw);
      const modelCautions = parsed.cautions
        .filter(
          (value) =>
            !/不含.*个股|缺少.*(涨跌幅|成交额|涨跌停|连板)/.test(value),
        );
      const modelSummary = String(parsed.summary || raw)
        .replace(/本输出不含任何个股或板块结论[。；]?/g, '')
        .replace(/缺少涨停\/连板梯队、板块涨幅榜和个股成交额榜[。；]?/g, '')
        .trim();
      const candidateNote = `候选提示：当日涨幅领先为 ${base.gainLeaders.slice(0, 3).map((x) => `${x.name} ${p(x.pct)}`).join('、')}；连续候选最高为 ${base.ladder.slice(0, 3).map((x) => `${x.stock.name} ${x.streak}板`).join('、')}。这些是日线候选，不是已核实龙头。`;
      const dataCorrection = `数据校正：本报告已提供 ${base.gainLeaders.length} 条当日涨幅榜、${base.amountLeaders.length} 条成交额榜、${base.ladder.length} 条 TDX 涨停/连板候选；其余 ${base.availability.filter((x) => x.status === '缺失').length} 项数据缺口已在下表逐项列出，因此当前结论仍标为“龙头候选”。 ${candidateNote}`;
      const rendered = buildAiPresentation(raw, base, 'DeepSeek Harness 复盘');
      if (skillId === 'short-term-sentiment-v22') setMainlineHarnessOutput(raw);
      const nextReport: Report = {
        ...base,
        generatedBy: `DeepSeek Harness · ${skillId}`,
        summary: `${modelSummary || base.summary} ${dataCorrection}`,
        cautions: [
          ...modelCautions,
          ...base.cautions,
        ].filter((value, index, values) => values.indexOf(value) === index),
        raw,
        aiPresentation: rendered.presentation,
      };
      setReport(nextReport);
      const reportDate = String(parsed.dataDate || base.date || market.date || '');
      const archiveKey = skillId === 'short-term-sentiment-v22'
        ? `mainline:${reportDate}:short-term-sentiment-v22`
        : `market:${reportDate}:${skillId}`;
      await archiveMarketReport(nextReport, 'Harness 复盘', archiveKey);
    } catch (error) {
      setAiError(
        error instanceof Error ? error.message : 'DeepSeek Harness 调用失败',
      );
    } finally {
      setAiBusy(false);
      endHarness();
    }
  }
  async function fetchSkillPreflight(target: Skill) {
    const response = await fetch(bridgeUrl('/skill14/preflight'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ skillId: target.id }),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.error || `本地预检服务返回异常（${response.status}）`);
    return result as SkillPreflightResult;
  }
  function formatSkillPreflight(target: Skill, result: SkillPreflightResult) {
    const missingRequired = Array.isArray(result.required_missing) && result.required_missing.length ? result.required_missing.join('、') : '无';
    const degraded = Array.isArray(result.degraded_missing) ? result.degraded_missing : [];
    const missingOptionalValues = [
      ...(Array.isArray(result.optional_missing) ? result.optional_missing : []),
      ...degraded,
    ];
    const missingOptional = missingOptionalValues.length ? missingOptionalValues.join('、') : '无';
    const minute = result.minute_data;
    return [
      `${target.name} · 本地数据预检`,
      `状态：${result.status || '未知'}`,
      `缺少必需数据：${missingRequired}`,
      `缺少可降级数据：${missingOptional}`,
      `5 分钟线：${minute?.requirement === 'not_required' || !minute ? '普通任务不依赖，未写入 EXE' : `${minute.status === 'available' ? '外部可按需读取' : '未发现，已降级'} · ${minute.purpose || '仅用于分钟级特征'}`}`,
      `规则：${result.degrade_policy || target.note}`,
      `说明：${result.execution_note || '预检回执已写入应用数据目录。'}`,
    ].join('\n');
  }
  async function runSkill(target: Skill) {
    setSkillBusy(true);
    setSkillOutput('');
    try {
      const result = await fetchSkillPreflight(target);
      setSkillOutput(formatSkillPreflight(target, result));
    } catch (error) {
      setSkillOutput(error instanceof Error ? error.message : '本地数据预检失败');
    } finally {
      setSkillBusy(false);
    }
  }
  async function runSkillHarness(target: Skill) {
    if (skillHarnessBusy) return;
    setSkillHarnessBusy(true);
    setSkillHarnessOutput('');
    setSkillHarnessError('');
    beginHarness(target.id);
    let preflight: SkillPreflightResult = { status: 'PREFLIGHT_UNAVAILABLE' };
    try {
      try {
        preflight = await fetchSkillPreflight(target);
        setSkillOutput(formatSkillPreflight(target, preflight));
      } catch (error) {
        preflight = {
          status: 'PREFLIGHT_UNAVAILABLE',
          error: error instanceof Error ? error.message : '本地预检失败',
        };
        setSkillOutput(`${target.name} · 本地预检未完成\n${String(preflight.error)}`);
      }
      const catalog = skill14Catalog.skills.find((item) => item.id === target.id);
      const raw = await callHarness(
        `请加载并执行电脑版技能“${target.name}”（技能 ID：${target.id}）的网页适配任务。先核对随附的本地预检结果，再严格按照技能包的职责、依赖和降级规则输出结果。预检为 BLOCKED 时只能输出阻塞诊断和补数清单，不得生成正式结论；预检为 DEGRADED 时必须明确标记降级范围。只读研究，不给出买卖建议，不得虚构未传入的行情、新闻、公告、龙虎榜或公式结果。${HARNESS_JSON_SCHEMA}`,
        target.id,
        {
          skill: catalog || { id: target.id, name: target.name, dependencies: target.dependencies, note: target.note },
          preflight,
          request: { page: 'skills', date: market.date },
        },
        `${target.name} · Harness`,
      );
      setSkillHarnessOutput(raw);
      const parsed = normalizeHarnessOutput(raw);
      const now = new Date().toISOString();
      await saveReportArchive({
        id: createReportId('skill14-harness'),
        archiveKey: `skill14:${target.id}:${market.date}`,
        createdAt: now,
        updatedAt: now,
        date: market.date,
        title: `${target.name} · Harness 报告 · ${d(market.date)}`,
        reportType: '14技能 Harness',
        generatedBy: `DeepSeek Harness · ${target.id}`,
        summary: parsed.summary || `${target.name} Harness 结果已生成。`,
        dataScope: parsed.dataScope || `本地行情快照 · ${d(market.date)} · 14 技能适配`,
        content: { kind: 'harness-skill', skillId: target.id, skillName: target.name, preflight, raw },
        raw,
      });
    } catch (error) {
      setSkillHarnessError(error instanceof Error ? error.message : 'Harness 调用失败');
    } finally {
      setSkillHarnessBusy(false);
      endHarness();
    }
  }
  function makeLocalReport() {
    setReportBusy(true);
    window.setTimeout(() => {
      const nextReport = makeBaseReport(market, themes, ladder);
      setReport(nextReport);
      void archiveMarketReport(nextReport, '结构化复盘');
      setReportBusy(false);
    }, 180);
  }
  function runFilter() {
    const g = Number(minPct),
      a = Number(minAmount);
    if (
      !minPct.trim() ||
      !minAmount.trim() ||
      !Number.isFinite(g) ||
      !Number.isFinite(a) ||
      g < -100 ||
      g > 100 ||
      a < 0
    ) {
      setFilterError('请输入有效条件：涨幅 -100 至 100，成交额不小于 0。');
      return;
    }
    setFilterError('');
    setFiltered(market.stocks.filter((s) => s.pct >= g && s.amount >= a * 1e8));
    setFilterRan(true);
  }
  async function runSingleGoldenIgnition() {
    const digits = singleSignalCode.trim().replace(/\D/g, '').slice(0, 6);
    if (!/^\d{6}$/.test(digits)) {
      setSingleSignalError('请输入 6 位股票代码，例如 300563。');
      setSingleSignalResult(null);
      return;
    }
    if (singleSignalBusy) return;
    setSingleSignalBusy(true);
    setSingleSignalError('');
    setSingleSignalResult(null);
    try {
      const response = await fetch(bridgeUrl('/strategy/golden-ignition/single'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: digits, lookback: 5 }),
      });
      const body = await response.json().catch(() => ({})) as SingleSignalResult;
      if (!response.ok) throw new Error(body.error || `单股黄金点火服务返回 ${response.status}`);
      setSingleSignalResult(body);
      const resultDate = String(body.latest_trading_date || market.date || '').replace(/\D/g, '').slice(0, 8);
      const now = new Date().toISOString();
      await saveReportArchive({
        id: `golden-ignition-single-${digits}-${Date.now()}`,
        archiveKey: `golden:${digits}:${resultDate || market.date}`,
        createdAt: now,
        updatedAt: now,
        date: resultDate || market.date,
        title: `黄金点火 · ${digits} · 单股执行信号`,
        reportType: '黄金点火单股信号',
        generatedBy: '黄金点火本地业务入口',
        summary: `${body.signal_status === 'HIT' ? '命中点火信号' : '未触发点火信号'} · ${body.analysis_symbol || digits}`,
        dataScope: `通达信本地日线 · ${d(body.latest_trading_date || market.date)} · 黄金点火AI`,
        content: { kind: 'golden-ignition-single-signal', result: body },
        raw: JSON.stringify(body, null, 2),
      });
    } catch (error) {
      setSingleSignalError(error instanceof Error ? error.message : '单股黄金点火执行失败');
    } finally {
      setSingleSignalBusy(false);
    }
  }
  async function runSelectedStrategy() {
    const target = skills.find((item) => item.id === selectedStrategy);
    runFilter();
    if (!target || strategyRuns[target.id]?.busy) return;
    const startedAt = Date.now();
    setStrategyRuns((previous) => ({
      ...previous,
      [target.id]: { busy: true, output: '', harnessOutput: '', status: 'RUNNING', phase: 'preflight', startedAt, elapsed: 0, structured: null },
    }));
    try {
      const response = await fetch(bridgeUrl('/skill14/preflight'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skillId: target.id }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.error || '本地预检服务返回异常');
      const missingRequired = Array.isArray(result.required_missing) && result.required_missing.length ? result.required_missing.join('、') : '无';
      const missingOptional = Array.isArray(result.optional_missing) && result.optional_missing.length ? result.optional_missing.join('、') : '无';
      const output = [
        `${target.name} · 本地数据预检`,
        `状态：${result.status || '未知'}`,
        `缺少必需数据：${missingRequired}`,
        `缺少可降级数据：${missingOptional}`,
        `规则：${result.degrade_policy || target.note}`,
        '说明：已调用对应原始策略评分引擎完成本地数值回执；Harness 负责基于同一份回执解释结果、列出缺失项与风险边界，不生成买卖建议。',
      ].join('\n');
      const filterPct = Number(minPct);
      const filterAmount = Number(minAmount);
      const candidateSource = market.allStocks?.length ? market.allStocks : market.stocks;
      const candidatePool = candidateSource
        .filter((stock) => stock.pct >= filterPct && stock.amount >= filterAmount * 1e8)
        .filter((stock) => !market.date || !stock.date || String(stock.date) === String(market.date))
        .sort((a, b) => b.pct - a.pct || b.amount - a.amount)
        .slice(0, 30);
      const scoreResponse = await fetch(bridgeUrl('/strategy/selection/scored'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategyId: target.id, date: market.date, candidates: candidatePool }),
        cache: 'no-store',
      });
      const scoreReceipt = await scoreResponse.json().catch(() => ({})) as StrategyScoreResponse & { error?: string };
      if (!scoreResponse.ok || scoreReceipt.status !== 'ok') {
        throw new Error(scoreReceipt.error || `原始策略评分服务返回 ${scoreResponse.status}`);
      }
      const scoreMap = new Map((Array.isArray(scoreReceipt.results) ? scoreReceipt.results : []).map((item) => [String(item.code || ''), item]));
      const localCandidates = candidatePool
        .map((stock) => strategyScoreCandidate(stock, scoreMap.get(stock.code), target.id, scoreReceipt))
        .sort((a, b) => {
          if (target.id === 'quant-production-v65') {
            const priority = (candidate: SelectionCandidate) => {
              const fields = candidate.strategy_fields || {};
              const labels = Array.isArray(fields.model_labels) ? fields.model_labels.length : 0;
              const states = fields.model_states && typeof fields.model_states === 'object'
                ? Object.values(fields.model_states as Record<string, unknown>)
                : [];
              const core = states.some((state) => state && typeof state === 'object' && (state as Record<string, unknown>).core === true);
              return labels > 0 ? 2 : core ? 1 : 0;
            };
            return priority(b) - priority(a) || b.score - a.score || b.pct - a.pct || b.amount - a.amount;
          }
          return b.score - a.score || b.pct - a.pct || b.amount - a.amount;
        })
        .slice(0, 10);
      const scoreStatus = String(scoreReceipt.score_status || 'UNKNOWN');
      const scoreMissing = Array.isArray(scoreReceipt.missing) && scoreReceipt.missing.length ? scoreReceipt.missing.join('、') : '无';
      setStrategyRuns((previous) => ({
        ...previous,
        [target.id]: {
          ...previous[target.id],
          busy: true,
          output: `${output}\n原始评分：${scoreStatus} · 已评分 ${scoreReceipt.candidate_count || localCandidates.length} 只\n评分缺失：${scoreMissing}`,
          harnessOutput: '',
          status: String(result.status || 'UNKNOWN'),
          phase: 'formula',
          startedAt,
          elapsed: Math.floor((Date.now() - startedAt) / 1000),
          structured: null,
          receipt: { ...result, scoring: scoreReceipt },
        },
      }));
      setStrategyRuns((previous) => ({
        ...previous,
        [target.id]: {
          ...previous[target.id],
          phase: 'harness',
          elapsed: Math.floor((Date.now() - startedAt) / 1000),
        },
      }));
      const rawHarnessOutput = await callHarness(
        selectionHarnessPrompt(target.name, String(result.status || 'UNKNOWN'), scoreReceipt),
        target.id,
        {
          page: 'selection',
          filters: { minPct: filterPct, minAmountYi: filterAmount },
          preflight: result,
          strategy_score: {
            status: scoreStatus,
            missing: scoreReceipt.missing || [],
            source: scoreReceipt.score_source || 'embedded_original_engine',
            artifact_path: scoreReceipt.artifact_path || '',
          },
          candidates: localCandidates,
        },
        `${target.name} · Harness 分析`,
      );
      // Harness 负责解释与风险边界；候选字段由本地回执重新落到最终 JSON，
      // 防止模型因字段命名差异把已计算值误标成“缺”。
      const harnessOutput = reconcileSelectionHarnessOutput(rawHarnessOutput, localCandidates, market.date, scoreReceipt);
      const parsed = normalizeHarnessOutput(harnessOutput);
      const now = new Date().toISOString();
      setStrategyRuns((previous) => ({
        ...previous,
        [target.id]: {
          ...previous[target.id],
          busy: false,
          output,
          harnessOutput,
          status: parsed.status || 'COMPLETED',
          phase: 'completed',
          startedAt: null,
          elapsed: Math.floor((Date.now() - startedAt) / 1000),
          structured: null,
          receipt: { ...result, scoring: scoreReceipt },
        },
      }));
      await saveReportArchive({
        id: `strategy-harness-${target.id}-${Date.now()}`,
        archiveKey: `strategy:${target.id}:${market.date}`,
        createdAt: now,
        updatedAt: now,
        date: market.date,
        title: `掌财智能体 · ${target.name} · Harness 分析`,
        reportType: '策略选股 Harness',
        generatedBy: `DeepSeek Harness · ${target.id}`,
        summary: parsed.summary || `${target.name} 的本地预检与 Harness 分析已完成。`,
        dataScope: `本地行情快照 · ${d(market.date)} · 条件候选 ${localCandidates.length} 只`,
        content: {
          kind: 'strategy-selection-harness',
          strategyId: target.id,
          preflight: result,
          scoring: scoreReceipt,
          filters: { minPct: filterPct, minAmountYi: filterAmount },
          candidates: localCandidates,
          harnessOutput,
        },
        raw: harnessOutput,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : '本地数据预检失败';
      setStrategyRuns((previous) => ({ ...previous, [target.id]: { ...previous[target.id], busy: false, output: previous[target.id]?.output || message, harnessOutput: previous[target.id]?.harnessOutput || '', status: 'ERROR', phase: ['formula', 'harness'].includes(previous[target.id]?.phase || '') ? `${previous[target.id]?.phase}_error` : 'strategy_error', startedAt: null, elapsed: Math.floor((Date.now() - startedAt) / 1000), structured: null } }));
    }
  }
  function download() {
    if (!report) return;
    const text = [
      `# ${report.title}`,
      `生成方式：${report.generatedBy}`,
      `数据来源：${report.source}`,
      '',
      report.summary,
      '',
      '## 市场概况',
      ...report.metrics.map((x) => `- ${x.label}：${x.value}（${x.detail}）`),
      '',
      '## 主线候选',
      ...report.themes.map(
        (x) =>
          `- ${x.name}：${x.count}只，平均${p(x.avgPct)}，代表股${x.leaders.map((s) => s.name).join('、')}`,
      ),
      '',
      '## TDX行业板块涨幅榜',
      ...(report.sectors || []).slice(0, 12).map(
        (x, i) => `${i + 1}. ${x.name}（${x.code}）${x.count}只，平均${p(x.avgPct)}，成交额${money(x.amount)}，涨停${x.limitCount || 0}只，代表股${(x.leaders || []).map((s) => s.name).join('、')}`,
      ),
      '',
      '## 涨停与连板候选',
      ...report.ladder.map(
        (x) => `- ${x.stock.name}：${p(x.currentPct)}，连续候选${x.streak}天`,
      ),
      '',
      '## 个股涨幅榜',
      ...(report.gainLeaders || []).map((x, i) => `${i + 1}. ${x.name}（${x.code}）${p(x.pct)}，成交额 ${money(x.amount)}`),
      '',
      '## 个股成交额榜',
      ...(report.amountLeaders || []).map((x, i) => `${i + 1}. ${x.name}（${x.code}）${p(x.pct)}，成交额 ${money(x.amount)}`),
      '',
      '## 负反馈与前日涨停表现（本地推导）',
      ...(report.lossLeaders || []).map((x, i) => `${i + 1}. 跌幅 ${x.name}（${x.code}）${p(x.pct)}，成交额 ${money(x.amount)}`),
      ...(report.limitDownCandidates || []).map((x) => `- 跌停阈值候选：${x.name}（${x.code}）${p(x.pct)}`),
      report.priorLimitUpStats ? `- 前日涨停候选 ${report.priorLimitUpStats.count || 0} 只，今日平均 ${report.priorLimitUpStats.todayAvgPct == null ? '—' : p(report.priorLimitUpStats.todayAvgPct)}` : '',
      '',
      '## 盘中封板与炸板（OHLC代理）',
      report.intradayProxy ? `- 涨停触板 ${report.intradayProxy.upperHitCount} 只，收盘封板 ${report.intradayProxy.upperClosedCount} 只，触板后开板 ${report.intradayProxy.openedAfterHitCount} 只，代理封板率 ${report.intradayProxy.sealRatePct == null ? '—' : p(report.intradayProxy.sealRatePct)}，代理炸板率 ${report.intradayProxy.explosionRatePct == null ? '—' : p(report.intradayProxy.explosionRatePct)}。` : '- 未生成盘中代理数据',
      report.intradayProxy ? `- 同日5分钟文件 ${report.intradayProxy.lc5CurrentDateCount}/${report.intradayProxy.lc5Files}；首封时刻与封单额未提供。该段仅为日线OHLC代理。` : '',
      '',
      '## 数据充分性与缺口',
      ...(report.availability || []).map((x) => `- ${x.item}：${x.status}。${x.evidence}。解决：${x.solution}`),
      '',
      '## 风险与下一步',
      ...report.cautions.map((x) => `- ${x}`),
      ...report.actions.map((x) => `- 下一步：${x}`),
    ].join('\n');
    const url = URL.createObjectURL(
      new Blob(['\ufeff' + text], { type: 'text/markdown;charset=utf-8' }),
    );
    const a = document.createElement('a');
    a.href = url;
    a.download = `掌财复盘报告-${report.date}.md`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function stockTable(rows: Stock[]) {
    return (
      <Table>
        <TableHeader>
          <TableRow>
            {['股票', closeDateLabel(market.date), '涨跌幅', '成交额', '自选'].map((x) => (
              <TableHead key={x}>{x}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((s) => (
            <TableRow key={s.code}>
              <TableCell>
                <button className="stock-name" onClick={() => onSelect(s)}>
                  {s.name}
                  <small>{s.code}</small>
                </button>
              </TableCell>
              <TableCell className="numeric" title={closeDateLabel(s.date)}>{s.close.toFixed(2)}</TableCell>
              <TableCell className={`numeric ${s.pct >= 0 ? 'up' : 'down'}`}>
                {p(s.pct)}
              </TableCell>
              <TableCell className="numeric">{money(s.amount)}</TableCell>
              <TableCell>
                <button
                  className={`star-button ${watch.includes(s.code) ? 'saved' : ''}`}
                  onClick={() => onWatch(s.code)}
                  aria-label={`${watch.includes(s.code) ? '移除' : '添加'}自选 ${s.name}`}
                >
                  <Star
                    size={16}
                    fill={watch.includes(s.code) ? 'currentColor' : 'none'}
                  />
                </button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    );
  }
  const skillDestination = (item: Skill) => {
    // 只有个股研究类技能需要先进入个股页输入代码；其他技能保留原有详情和执行方式。
    return item.group === 'research' ? 'research' : null;
  };
  function handleSkillClick(item: Skill) {
    const destination = skillDestination(item);
    if (destination && destination !== page) {
      setSkill(null);
      navigate(destination);
      return;
    }
    setSkillOutput('');
    setSkillHarnessOutput('');
    setSkillHarnessError('');
    setSkill(item);
  }
  function openResearchCode() {
    const code = researchCode.trim().replace(/\D/g, '').slice(-6);
    if (!/^\d{6}$/.test(code)) {
      setResearchCodeError('请输入 6 位股票代码');
      return;
    }
    const opened = onSelectCode
      ? onSelectCode(code)
      : Boolean(searchableStocks.find((row) => row.code === code));
    if (!onSelectCode) {
      const row = searchableStocks.find((item) => item.code === code);
      if (row) onSelect(row);
    }
    if (!opened && onSelectCode) {
      setResearchCodeError(`当日日线中未找到 ${code}，请先刷新行情`);
      return;
    }
    if (!opened && !onSelectCode) {
      setResearchCodeError(`当日日线中未找到 ${code}，请先刷新行情`);
      return;
    }
    setResearchCodeError('');
  }
  function skillCards(list: Skill[]) {
    return (
      <div className="skill-grid">
        {list.map((s, i) => {
          const catalogStatus = s.group === 'selection' ? strategyDataStatus(s.id) : null;
          const mode = catalogStatus === 'missing' ? 'data' : catalogStatus === 'partial' ? 'partial' : skillMode(s.id);
          const detailOnly = mode === 'basic';
          const run = s.group === 'selection' ? strategyRuns[s.id] : undefined;
          const hasReport = strategyRunHasReport(run);
          const hasFailure = strategyRunHasFailure(run);
          return <button className={`skill-card skill-card-${mode}`} key={s.id} onClick={() => handleSkillClick(s)}>
            <div className="skill-card-top">
              <span className="skill-icon">
                {i % 3 === 0 ? (
                  <Target size={19} />
                ) : i % 3 === 1 ? (
                  <Layers size={19} />
                ) : (
                  <Workflow size={19} />
                )}
              </span>
              <small className="skill-ready">{detailOnly ? '基础能力 · 仅详情' : '本地数据预检'}</small>
            </div>
            <h3>{s.name}</h3>
            <p>{skillIntroduction(s)} {detailOnly ? '本页仅展示技能详情，不启动预检或 Harness。' : '先校验已落盘数据与降级规则；进入详情后可生成预检，也可直接调用 Harness。'}</p>
            <small className="skill-original-id">原始技能：{s.id}</small>
            <Tags list={s.dependencies.slice(0, 3)} />
            <div className="skill-card-bottom">
              <span>{groupNames[s.group]}</span>
              <span>
                {detailOnly ? '查看技能详情' : run?.busy ? '正在预检…' : hasReport ? '查看最新回执' : hasFailure ? '查看失败详情' : '查看并预检'}
                <ArrowUpRight size={14} />
              </span>
            </div>
          </button>;
        })}
      </div>
    );
  }
  function mainlineTable(rows: Theme[]) {
    return (
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>方向</TableHead>
            <TableHead>样本</TableHead>
            <TableHead>平均涨跌</TableHead>
            <TableHead>成交额</TableHead>
            <TableHead>代表股</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((x) => (
            <TableRow key={x.name}>
              <TableCell>
                <b>{x.name}</b>
                <small className="table-sub">{x.tag}</small>
              </TableCell>
              <TableCell>{x.count}</TableCell>
              <TableCell className={`numeric ${x.avgPct >= 0 ? 'up' : 'down'}`}>
                {p(x.avgPct)}
              </TableCell>
              <TableCell className="numeric">{money(x.amount)}</TableCell>
              <TableCell>{x.leaders.map((s) => s.name).join('、')}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    );
  }
  const environment = environmentSnapshot || {};
  const environmentTdx = (environment.tdx && typeof environment.tdx === 'object' ? environment.tdx : {}) as Record<string, unknown>;
  const environmentDaily = (environment.daily && typeof environment.daily === 'object' ? environment.daily : {}) as Record<string, unknown>;
  const environmentHarness = (environment.harness && typeof environment.harness === 'object' ? environment.harness : {}) as Record<string, unknown>;
  const environmentIndexInitialization = (environment.dailyIndexInitialization && typeof environment.dailyIndexInitialization === 'object' ? environment.dailyIndexInitialization : {}) as Record<string, unknown>;
  const environmentCanonicalIndex = (environment.canonicalDailyIndex && typeof environment.canonicalDailyIndex === 'object' ? environment.canonicalDailyIndex : {}) as Record<string, unknown>;
  const runtimeStorageLabel = isDesktopRuntime() ? 'EXE 资源库' : '本地运行目录';
  const environmentDailyState = (environment.dailyRefresh && typeof environment.dailyRefresh === 'object' ? environment.dailyRefresh : {}) as Record<string, unknown>;
  const environmentSupplementalState = (environment.supplementalRefresh && typeof environment.supplementalRefresh === 'object' ? environment.supplementalRefresh : {}) as Record<string, unknown>;
  const environmentSupplemental = (environment.supplemental && typeof environment.supplemental === 'object' ? environment.supplemental : {}) as Record<string, unknown>;
  const environmentDailyArchive = (environment.dailyArchive && typeof environment.dailyArchive === 'object' ? environment.dailyArchive : {}) as Record<string, unknown>;
  const environmentDailyIndex = (environment.dailyDataIndex && typeof environment.dailyDataIndex === 'object' ? environment.dailyDataIndex : {}) as Record<string, unknown>;
  const environmentDailyIndexSummary = (environmentDailyIndex.summary && typeof environmentDailyIndex.summary === 'object' ? environmentDailyIndex.summary : {}) as Record<string, unknown>;
  const environmentUnifiedArchive = (environment.unifiedArchive && typeof environment.unifiedArchive === 'object' ? environment.unifiedArchive : {}) as Record<string, unknown>;
  const environmentUnifiedVerification = (environment.unifiedVerification && typeof environment.unifiedVerification === 'object' ? environment.unifiedVerification : {}) as Record<string, unknown>;
  const unifiedArchiveStatus = String(environmentUnifiedArchive.status || '未执行');
  const unifiedArchiveSteps = Array.isArray(environmentUnifiedArchive.steps)
    ? environmentUnifiedArchive.steps as Record<string, unknown>[]
    : [];
  const unifiedArchiveProgress = unifiedArchiveSteps.filter((step) => ['completed', 'partial', 'failed'].includes(String(step.status || ''))).length;
  const unifiedArchiveTotal = unifiedArchiveSteps.length || 9;
  const unifiedArchiveActiveStep = unifiedArchiveSteps.find((step) => step.status === 'running');
  const unifiedArchiveReport = (environmentUnifiedArchive.report && typeof environmentUnifiedArchive.report === 'object' ? environmentUnifiedArchive.report : {}) as Record<string, unknown>;
  const unifiedArchiveHarness = (environmentUnifiedArchive.harness && typeof environmentUnifiedArchive.harness === 'object' ? environmentUnifiedArchive.harness : {}) as Record<string, unknown>;
  const unifiedArchiveReportUrl = typeof unifiedArchiveReport.htmlUrl === 'string'
    ? bridgeUrl(unifiedArchiveReport.htmlUrl)
    : bridgeUrl('/data/archive/report');
  const unifiedArchiveBadge = unifiedArchiveStatus === 'completed'
    ? '已完成'
    : unifiedArchiveStatus === 'running'
      ? '运行中'
      : unifiedArchiveStatus === 'partial'
        ? '部分完成'
        : unifiedArchiveStatus === 'failed'
          ? '失败'
          : '待执行';
  const environmentSourceManifest = (environment.unifiedSourceManifest && typeof environment.unifiedSourceManifest === 'object' ? environment.unifiedSourceManifest : {}) as Record<string, unknown>;
  const environmentSourceRows = Array.isArray(environmentSourceManifest.sources) ? environmentSourceManifest.sources as Record<string, unknown>[] : [];
  const environmentIntegrity = (environmentDaily.integrity && typeof environmentDaily.integrity === 'object' ? environmentDaily.integrity : {}) as Record<string, unknown>;
  const environmentIntegrityAfter = (environmentIntegrity.after && typeof environmentIntegrity.after === 'object' ? environmentIntegrity.after : {}) as Record<string, unknown>;
  const environmentIntegrityUnresolved = Array.isArray(environmentIntegrity.unresolved) ? environmentIntegrity.unresolved as Record<string, unknown>[] : [];
  const environmentIntegrityUnresolvedCount = Number(environmentIntegrity.unresolvedCount ?? environmentIntegrityUnresolved.length);
  const environmentIntegrityRepairs = Array.isArray(environmentIntegrity.repairs) ? environmentIntegrity.repairs as Record<string, unknown>[] : [];
  const environmentIntegrityNonTrading = Array.isArray(environmentIntegrity.nonTrading) ? environmentIntegrity.nonTrading as Record<string, unknown>[] : [];
  const environmentIntegrityRepairedCount = environmentIntegrityRepairs.filter((item) => item.status === 'written').length;
  const environmentIntegrityManualAction = String(environmentIntegrity.manualAction || '');
  const environmentRunningStep = Array.isArray(environmentDailyState.steps)
    ? (environmentDailyState.steps as Record<string, unknown>[]).find((step) => step.status === 'running')
    : undefined;
  const environmentSources = Array.isArray(environment.sources) ? environment.sources as Record<string, unknown>[] : [];
  const environmentValidation = (environment.harnessValidation && typeof environment.harnessValidation === 'object' ? environment.harnessValidation : {}) as Record<string, unknown>;
  return (
    <div className="secondary-page">
      {harnessProgress()}
      {page === 'skills' && (
        <>
          <div className="section-intro">
            <div>
              <h2>电脑版技能目录 · 14 项</h2>
              <p>列表仅包含本次导入的 14 个电脑版技能包，沿用原有工作台分组与卡片版面。每项先生成本地数据预检和落盘回执。</p>
            </div>
            <span className="big-count">
              14<small>项技能</small>
            </span>
          </div>
          <div className="filter-toolbar">
            <div className="search-field">
              <Search size={17} />
              <Input
                aria-label="搜索技能"
                placeholder="搜索技能名称、调用别名…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Select value={group} onValueChange={(v) => setGroup(v || 'all')}>
              <SelectTrigger aria-label="技能分类" className="filter-select">
                <SelectValue>
                  {group === 'all' ? '全部分类' : groupNames[group]}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部分类</SelectItem>
                {Object.entries(groupNames).map(([k, v]) => (
                  <SelectItem key={k} value={k}>
                    {v}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <span className="subtle">
              {visibleSkills.length}{' '}
              项匹配
            </span>
          </div>
          {visibleSkillGroups.map(([groupId, groupName]) => {
            const rows = visibleSkills.filter((item) => item.group === groupId);
            return (
              <section key={groupId} className="skill-type-section">
                <div className="section-label">{groupName} <span>{rows.length} 项</span></div>
                {skillCards(rows)}
              </section>
            );
          })}
          {!visibleSkills.length && (
            <Empty
              title="没有匹配技能"
              body="尝试搜索“龙头”“评分”或切换分类。"
            />
          )}
        </>
      )}
      {page === 'mainline' && (
        <>
          <div className="sample-banner">
            <RefreshCw size={16} />
            <span>
              已按 {d(market.date)}{' '}
              通达信日线与 TDX 行业/主题成员刷新；连板网 PDF
              仅作历史口径参考。
            </span>
            <Button
              variant="outline"
              disabled={aiBusy}
              onClick={() =>
                makeHarnessReport('short-term-sentiment-v22', {
                  themes,
                })
              }
            >
              {aiBusy ? (
                <LoaderCircle className="spin" size={15} />
              ) : (
                <Sparkles size={15} />
              )}{' '}
              Harness 主线研判
            </Button>
          </div>
          <Box title="主线研判 · short-term-sentiment-v22" extra={<span className="example-label">重点摘要</span>}>
            <div className="content-pad">
              {mainlineHarnessLoading ? (
                <p className="muted-copy">正在读取最近一次 Harness 报告…</p>
              ) : mainlineHarnessOutput ? (
                <HarnessOutput raw={mainlineHarnessOutput} compact />
              ) : (
                <Empty title="暂无已完成的主线研判报告" body="点击上方按钮运行 Harness；完成后报告会自动持久化并在此处显示。" />
              )}
            </div>
          </Box>
          <div className="theme-grid">
            {themes.slice(0, 6).map((t, i) => (
              <button
                key={t.name}
                onClick={() => setTheme(i)}
                className={`theme-card ${theme === i ? 'chosen' : ''}`}
                style={{ '--theme-color': t.color } as CSSProperties}
              >
                <div>
                  <span>{t.tag}</span>
                  <ArrowUpRight size={16} />
                </div>
                <h2>{t.name}</h2>
                <p>
                  <b>{t.count}</b> 只样本{' '}
                  <span className={t.avgPct >= 0 ? 'up' : 'down'}>
                    {p(t.avgPct)} 平均涨跌
                  </span>
                </p>
                <div className="theme-meter">
                  <span
                    style={{
                      width: `${Math.min(100, (t.count / Math.max(...themes.map((x) => x.count), 1)) * 100)}%`,
                    }}
                  />
                </div>
              </button>
            ))}
          </div>
          {themes.length ? (
            <div className="two-column">
              <Box
                title={`${themes[theme]?.name || themes[0].name} · 当日候选`}
                extra={<span className="example-label">{d(market.date)}</span>}
              >
                <div className="content-pad">
                  <TableProperties size={17} />
                  {mainlineTable([themes[theme] || themes[0]])}
                  <p className="muted-copy">
                    代表股来自当日样本涨幅排序；TDX 行业/主题映射已提供结构候选，新闻催化和失效条件仍需由 Harness 结合外部证据核验。
                  </p>
                </div>
              </Box>
              <Box title="主线研判逻辑">
                <div className="content-pad">
                  <div className="logic-steps">
                    <div>
                      <b>1</b>
                      <span>优先读取 TDX 主题成员，缺失时使用 TDX 行业成员</span>
                    </div>
                    <div>
                      <b>2</b>
                      <span>按样本数、平均涨跌、成交额和涨停家数排序</span>
                    </div>
                    <div>
                      <b>3</b>
                      <span>取涨幅领先个股作为代表股</span>
                    </div>
                  </div>
                  <Button
                    className="primary-button"
                    disabled={aiBusy}
                    onClick={() =>
                        makeHarnessReport('market-environment-v5', {
                        themes,
                      })
                    }
                  >
                    <Sparkles size={15} />用 Harness 生成主线报告
                  </Button>
                </div>
              </Box>
            </div>
          ) : (
            <Empty title="当日没有形成聚类" body="请刷新行情文件后重试。" />
          )}
          <div className="section-label">
            本页对应技能 <span>{related.length} 项</span>
          </div>
          {skillCards(related)}
        </>
      )}
      {page === 'ladder' && (
        <>
          <div className="sample-banner">
            <RefreshCw size={16} />
            <span>
              已按 {d(market.date)}{' '}
              日线数据刷新。涨停为按主板、创业板、科创板、北交所和 ST
              阈值识别的候选，连板按近 30 个交易日连续阈值计算。
            </span>
            <Button
              variant="outline"
              disabled={aiBusy}
              onClick={() =>
                makeHarnessReport('limit-up-review', {
                  ladder: ladder.slice(0, 30),
                })
              }
            >
              {aiBusy ? (
                <LoaderCircle className="spin" size={15} />
              ) : (
                <Sparkles size={15} />
              )}{' '}
              Harness 连板复盘
            </Button>
          </div>
          <div className="metric-grid">
            {[
              ['涨停候选', `${ladder.length}`, `数据日 ${d(market.date)}`],
              [
                '连板候选',
                `${ladder.filter((x) => x.streak > 1).length}`,
                '近 30 日连续阈值',
              ],
              [
                '最高连续',
                `${Math.max(0, ...ladder.map((x) => x.streak))} 天`,
                ladder[0]?.stock.name || '—',
              ],
              ['样本范围', `${market.currentCount} 只`, '同日股票'],
            ].map(([l, v, n]) => (
              <div className="metric-card" key={l}>
                <span>{l}</span>
                <b>{v}</b>
                <small>{n}</small>
              </div>
            ))}
          </div>
          <Box
            title="当日涨停与连板候选"
            extra={<span className="example-label">自动刷新</span>}
          >
            {ladder.length ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>股票</TableHead>
                    <TableHead>涨跌幅</TableHead>
                    <TableHead>适用阈值</TableHead>
                    <TableHead>连续候选</TableHead>
                    <TableHead>成交额</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {ladder.slice(0, 40).map((x) => (
                    <TableRow key={x.stock.code}>
                      <TableCell>
                        <button
                          className="stock-name"
                          onClick={() => onSelect(x.stock)}
                        >
                          {x.stock.name}
                          <small>{x.stock.code}</small>
                        </button>
                      </TableCell>
                      <TableCell className="numeric up">
                        {p(x.currentPct)}
                      </TableCell>
                      <TableCell>{x.limitPct}%</TableCell>
                      <TableCell>
                        <b>{x.streak} 天</b>
                      </TableCell>
                      <TableCell className="numeric">
                        {money(x.stock.amount)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <Empty
                title="今日没有涨停候选"
                body="请确认通达信日线文件已更新。"
              />
            )}
            <div className="panel-footnote">
              日线无法确认盘中封板、炸板和停牌过程；正式报告会保留“候选”标记。
            </div>
          </Box>
          <div className="section-label">
            涨停研究与监控 <span>{related.length} 项技能</span>
          </div>
          {skillCards(related)}
        </>
      )}
      {page === 'selection' && (
        <>
          <div className="selection-layout">
            <Box title="选择策略">
              <div className="strategy-menu">
                {skills
                  .filter((s) => s.group === 'selection')
                  .map((s) => {
                    const catalog = strategyCatalogItem(s.id);
                    const status = strategyDataStatus(s.id);
                    const run = strategyRuns[s.id];
                    return (
                      <button
                        key={s.id}
                        className={selectedStrategy === s.id ? 'selected' : ''}
                        disabled={run?.busy}
                        title={catalog?.dataNote || '生成本地数据预检与落盘运行单'}
                        onClick={() => {
                          setSelectedStrategy(s.id);
                          setFilterRan(false);
                        }}
                      >
                        <Target size={15} />
                        <span className="strategy-menu-copy"><b>{s.name}</b><small>{run?.busy ? (run.phase === 'harness' ? 'Harness 分析中' : '本地预检中') : run?.phase === 'completed' ? 'Harness 已完成' : run?.phase === 'preflight' ? `预检 ${run.status}` : strategyRunHasFailure(run) ? '上次运行失败' : '可运行'}</small></span>
                        {selectedStrategy === s.id && <Check size={15} />}
                      </button>
                    );
                  })}
              </div>
              <div className="strategy-menu-audit">
                本区保留 3 个选股类电脑版技能；点击运行后先做本地预检，再调用对应技能的 Harness 分析，任务与结果会保存到应用数据目录。
              </div>
            </Box>
            <div>
              <Box
                title={
                  skills.find((s) => s.id === selectedStrategy)?.name ||
                  '策略选股'
                }
                extra={
                  <button
                    className="text-link"
                    onClick={() => openById(selectedStrategy)}
                  >
                    技能说明
                    <ArrowUpRight size={14} />
                  </button>
                }
              >
                <div className="content-pad">
                  <div className="sample-banner">
                    <Info size={16} />
                    保持原有筛选布局；运行流程为“本地数据预检 → 对应技能 Harness 分析”，不再直接拼接旧版不存在的策略路径。
                  </div>
                  <div className="form-grid">
                    <label>
                      最小日涨幅（%）
                      <Input
                        type="number"
                        min="-100"
                        max="100"
                        value={minPct}
                        onChange={(e) => setMinPct(e.target.value)}
                      />
                    </label>
                    <label>
                      最小成交额（亿元）
                      <Input
                        type="number"
                        min="0"
                        value={minAmount}
                        onChange={(e) => setMinAmount(e.target.value)}
                      />
                    </label>
                    <label>
                      数据范围
                      <div className="readonly-input">
                        沪深北 · {market.currentCount} 只同日样本 ·{' '}
                        {d(market.date)}
                      </div>
                    </label>
                  </div>
                  {selectedStrategy === 'golden-ignition-v8' && (
                    <div className="single-signal-section">
                      <div className="research-code-entry">
                        <div className="research-code-copy">
                          <b>单股执行信号</b>
                          <span>输入股票代码，执行黄金点火本地业务入口；结果不参与 Top10 筛选。</span>
                        </div>
                        <div className="research-code-controls">
                          <Input
                            aria-label="单股股票代码"
                            placeholder="股票代码，如 300563"
                            value={singleSignalCode}
                            maxLength={6}
                            onChange={(e) => {
                              setSingleSignalCode(e.target.value.replace(/\D/g, '').slice(0, 6));
                              setSingleSignalError('');
                            }}
                            onKeyDown={(e) => { if (e.key === 'Enter') void runSingleGoldenIgnition(); }}
                          />
                          <Button
                            variant="outline"
                            aria-label="执行单股信号"
                            disabled={singleSignalBusy}
                            onClick={() => void runSingleGoldenIgnition()}
                          >
                            {singleSignalBusy ? <LoaderCircle className="spin" size={15} /> : <Target size={15} />}
                            {singleSignalBusy ? '执行中…' : '执行单股信号'}
                          </Button>
                        </div>
                        {singleSignalError && <span className="form-error" role="alert">{singleSignalError}</span>}
                      </div>
                      {singleSignalResult && (
                        <div className={`strategy-run-output ${singleSignalResult.status === 'ok' ? 'ready' : 'blocked'}`} role="status">
                          <b>单股信号回执：{singleSignalResult.signal_status === 'HIT' ? 'HIT · 已触发' : singleSignalResult.signal_status === 'NO_SIGNAL' ? 'NO_SIGNAL · 未触发' : singleSignalResult.status || 'BLOCKED'}</b>
                          <div className="settings-list">
                            <div><dt>输入 / 分析标的</dt><dd>{singleSignalResult.input_symbol || '—'} / {singleSignalResult.analysis_symbol || '—'}</dd></div>
                            <div><dt>最新交易日</dt><dd>{d(singleSignalResult.latest_trading_date || '')}</dd></div>
                            <div><dt>最新收盘 / EMA3 / EMA21</dt><dd>{formulaText(singleSignalResult.local_daily?.latest_close) || '—'} / {formulaText(singleSignalResult.local_daily?.latest_ema3) || '—'} / {formulaText(singleSignalResult.local_daily?.latest_ema21) || '—'}</dd></div>
                            <div><dt>OUTPUT59 / OUTPUT60 / OUTPUT61</dt><dd>{formulaText(singleSignalResult.tdx_formula?.fields?.OUTPUT59) || '—'} / {formulaText(singleSignalResult.tdx_formula?.fields?.OUTPUT60) || '—'} / {formulaText(singleSignalResult.tdx_formula?.fields?.OUTPUT61) || '—'}</dd></div>
                            <div><dt>点火布尔 / 公式状态</dt><dd>{singleSignalResult.ignition_signal ? 'true' : 'false'} / {singleSignalResult.tdx_formula?.ok ? '已返回' : '未返回或无值'}</dd></div>
                            <div><dt>本地回执</dt><dd>{singleSignalResult.result_path || '已生成，但路径未返回'}</dd></div>
                          </div>
                          {singleSignalResult.error && <p className="muted-copy">{singleSignalResult.error}</p>}
                          {Array.isArray(singleSignalResult.risk_boundary) && singleSignalResult.risk_boundary.length > 0 && (
                            <p className="muted-copy">风险边界：{singleSignalResult.risk_boundary.join('；')}</p>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                  <div className="action-row">
                    <Button className="primary-button" aria-label="生成本地预检并调用 Harness 分析" disabled={selectedStrategyRun.busy} onClick={runSelectedStrategy}>
                      {selectedStrategyRun.busy ? <LoaderCircle className="spin" size={15} /> : <Workflow size={15} />}
                      {selectedStrategyRun.busy ? (selectedStrategyRun.phase === 'harness' ? 'Harness 分析中…' : '生成预检中…') : selectedStrategyRun.phase === 'completed' ? '重新预检并调用 Harness 分析' : selectedStrategyRun.phase === 'preflight' ? '重新预检并调用 Harness 分析' : selectedStrategyHasFailure ? '重试预检并调用 Harness 分析' : '生成预检并调用 Harness 分析'}
                    </Button>
                    <span className="harness-eta">
                      预检核验落盘数据与降级边界；通过后由 Harness 基于同一份本地数据和候选进行分析，不生成买卖建议。
                    </span>
                  </div>
                  {selectedStrategyRun.busy && (
                    <div className="harness-progress" role="status">
                      <LoaderCircle className="spin" size={15} />
                      <span>
                        {selectedStrategy} {selectedStrategyRun.phase === 'harness' ? 'Harness 分析中' : '本地预检中'} · 已运行 {formatDuration(selectedStrategyRun.elapsed)} · {selectedStrategyRun.phase === 'harness' ? '正在整理本地候选与预检回执' : '正在核验日线、公式与辅助数据依赖'}
                      </span>
                    </div>
                  )}
                  {selectedStrategyRun.output && (
                    <div className={`strategy-run-output ${selectedStrategyRun.status === 'READY_FOR_VALIDATED_RUN' ? 'ready' : 'blocked'}`}>
                      <b>本地数据预检：{selectedStrategyRun.status || 'UNKNOWN'}</b>
                      <pre>{strategyPreflightDisplayText(selectedStrategyRun.output)}</pre>
                    </div>
                  )}
                  {selectedStrategyRun.harnessOutput && (
                    <div className="strategy-run-output ready">
                      <b>Harness 分析结果</b>
                      <HarnessOutput raw={selectedStrategyRun.harnessOutput} />
                    </div>
                  )}
                  {filterError && (
                    <p className="form-error" role="alert">
                      {filterError}
                    </p>
                  )}
                </div>
              </Box>
              <div className="section-spacer" />
              <Box
                title={
                  filterRan
                    ? `基础条件匹配 · ${filtered.length} 只`
                    : '本地条件候选'
                }
                extra={
                  filterRan ? (
                    <span className="subtle">
                      展示前 30 只 · {d(market.date)}
                    </span>
                  ) : undefined
                }
              >
                {filterRan ? (
                  filtered.length ? (
                    stockTable(filtered.slice(0, 30))
                  ) : (
                    <Empty
                      title="没有符合条件的股票"
                      body="请调整条件后重试。"
                    />
                  )
                ) : (
                  <Empty
                      title="生成本地数据预检后查看回执"
                      body="页面会同时展示本地条件候选和 14 技能的预检状态。"
                  />
                )}
              </Box>
            </div>
          </div>
          <StrategyReportGallery strategies={skills.filter((s) => s.group === 'selection')} runs={strategyRuns} />
        </>
      )}
      {page === 'research' && (
        <>
          <div className="research-code-entry">
            <div className="research-code-copy">
              <b>按代码打开个股</b>
              <span>
                {market.degraded === true || market.dataQuality === 'degraded' || market.quality === 'degraded'
                  ? `目标日未落盘，已降级使用 ${d(market.date)} 日线收盘数据`
                  : `使用 ${d(market.date)} 日线收盘数据`}
                {' · 输入后可查看十项个股技能'}
              </span>
            </div>
            <div className="research-code-controls">
              <Input
                aria-label="输入股票代码"
                placeholder="股票代码，如 300959"
                value={researchCode}
                maxLength={6}
                onChange={(e) => {
                  setResearchCode(e.target.value.replace(/\D/g, '').slice(0, 6));
                  setResearchCodeError('');
                }}
                onKeyDown={(e) => { if (e.key === 'Enter') openResearchCode(); }}
              />
              <Button variant="outline" onClick={openResearchCode}>查看个股</Button>
              {onRefreshMarket && (
                <Button variant="outline" onClick={() => void onRefreshMarket()} disabled={marketRefreshing}>
                  {marketRefreshing ? <LoaderCircle className="spin" size={15} /> : <RefreshCw size={15} />}
                  刷新行情
                </Button>
              )}
            </div>
            {researchCodeError && <span className="form-error">{researchCodeError}</span>}
            {marketRefreshMessage && <span className="subtle research-refresh-message">{marketRefreshMessage}</span>}
          </div>
          <div className="filter-toolbar">
            <div className="search-field">
              <Search size={17} />
              <Input
                aria-label="搜索本地股票"
                placeholder="搜索全部本地股票：代码或名称"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPageNo(0);
                }}
              />
            </div>
            <Select
              value={sort}
              onValueChange={(v) => {
                setSort(v || 'gain');
                setPageNo(0);
              }}
            >
              <SelectTrigger aria-label="个股排序" className="filter-select">
                <SelectValue>
                  {sort === 'gain'
                    ? '涨幅优先'
                    : sort === 'loss'
                      ? '跌幅优先'
                      : '成交额优先'}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="gain">涨幅优先</SelectItem>
                <SelectItem value="loss">跌幅优先</SelectItem>
                <SelectItem value="amount">成交额优先</SelectItem>
              </SelectContent>
            </Select>
            <span className="subtle">{filteredStocks.length} 只匹配</span>
          </div>
          <Box
            title="全量个股档案"
            extra={<span className="subtle">
              {searchableStocks.length} 只 {d(market.date)} 日线股票
              {(market.degraded === true || market.dataQuality === 'degraded' || market.quality === 'degraded') ? '（最近完整交易日降级）' : ''}
              {' · 点击查看行情详情'}
            </span>}
            >
            {filteredStocks.length ? (
              stockTable(filteredStocks.slice(pageNo * 15, pageNo * 15 + 15))
            ) : (
                <Empty
                title="暂无可用日线股票"
                body="请先刷新行情或完成本地日线归档；随后可按六位代码或中文名称检索。"
              />
            )}
            {filteredStocks.length > 0 && (
              <div className="pagination-row">
                <span>
                  第 {pageNo + 1} / {Math.ceil(filteredStocks.length / 15)} 页
                </span>
                <Button
                  variant="outline"
                  disabled={!pageNo}
                  onClick={() => setPageNo((v) => v - 1)}
                >
                  上一页
                </Button>
                <Button
                  variant="outline"
                  disabled={(pageNo + 1) * 15 >= filteredStocks.length}
                  onClick={() => setPageNo((v) => v + 1)}
                >
                  下一页
                </Button>
              </div>
            )}
          </Box>
          <div className="section-label">
            研究工具 <span>{related.length} 项技能</span>
          </div>
          {skillCards(related)}
        </>
      )}
      {page === 'watchlist' && (
        <>
          <Tabs defaultValue="watch" className="workspace-tabs">
            <TabsList className="workspace-tabs-list">
              <TabsTrigger value="watch">我的自选 · {watch.length}</TabsTrigger>
              <TabsTrigger value="holdings">持仓监控</TabsTrigger>
              <TabsTrigger value="journal">研究日志 · {archiveRows.length}</TabsTrigger>
            </TabsList>
            <TabsContent value="watch">
              <Box
                title="自选观察池"
                extra={
                  <div className="watchlist-actions"><Button variant="outline" onClick={() => navigate('research')}><Search size={14} />添加股票</Button><Button variant="outline" onClick={refreshWatchlist} disabled={watchRefreshing || !watch.length}>{watchRefreshing ? <LoaderCircle className="spin" size={14} /> : <RefreshCw size={14} />}刷新自选行情</Button></div>
                }
              >
                {watch.length ? (
                  (() => {
                    const source = [...(market.allStocks || []), ...market.stocks];
                    const rows = watch
                      .map((code) => source.find((s) => s.code === code))
                      .filter((s): s is Stock => Boolean(s));
                    return rows.length ? stockTable(rows) : <div className="watchlist-missing">自选代码已持久保存，但当前行情快照暂未返回对应报价。刷新行情后会自动补齐。</div>;
                  })()
                ) : (
                  <Empty
                    title="把关注的股票放到这里"
                    body="在行情榜单、策略筛选或个股研究中点击星标加入自选。"
                  />
                )}
                {watchRefreshMessage && <div className="watchlist-refresh-message">{watchRefreshMessage}</div>}
              </Box>
            </TabsContent>
            <TabsContent value="holdings">
              <Box title="持仓股监控">
                <Empty
                  title="尚未导入持仓"
                  body="正式版需要成本价、数量、行情源及告警服务。"
                />
              </Box>
            </TabsContent>
            <TabsContent value="journal">
              <Box title="研究日志" extra={<span className="subtle">与“我的报告”实时同步</span>}>
                {archiveRows.length ? <div className="research-journal-list">{archiveRows.slice(0, 20).map((item) => <button className="research-journal-item" key={item.id} onClick={() => setOpenedArchive(item)}><span className="journal-type">{item.reportType}</span><div><b>{item.title}</b><small>{new Date(item.updatedAt || item.createdAt).toLocaleString('zh-CN', { hour12: false })} · {item.generatedBy}</small><p>{item.summary.slice(0, 120)}{item.summary.length > 120 ? '…' : ''}</p></div><ArrowUpRight size={15} /></button>)}</div> : <Empty title="还没有研究记录" body="从复盘、个股研究或技能中心生成报告后，研究日志会自动出现。" />}
              </Box>
            </TabsContent>
          </Tabs>
          <div className="section-label">工作台技能</div>
          {skillCards(related)}
        </>
      )}
      {page === 'reports' && (
        <>
          <div className="report-layout">
            <div>
              <Box
                title="智能复盘流程"
                extra={<span className="example-label">当日数据</span>}
              >
                <div className="report-flow">
                  {[
                    ['01', '短线市场情绪', '判断市场宽度与指数分化'],
                    ['02', '核心主线评分', '按当日聚类并交给 Harness 复核'],
                    ['03', '涨停板深度复盘', '识别日线涨停与连续候选'],
                    ['04', '投研交付与验收', '保留数据日期、范围和风险'],
                  ].map(([n, t, b]) => (
                    <div key={n}>
                      <span>{n}</span>
                      <section>
                        <b>{t}</b>
                        <small>{b}</small>
                      </section>
                      <label>已接入</label>
                    </div>
                  ))}
                </div>
                <div className="content-pad">
                  <div className="report-actions">
                    <Button
                      className="primary-button"
                      disabled={reportBusy}
                      onClick={makeLocalReport}
                    >
                      {reportBusy ? (
                        <LoaderCircle className="spin" size={16} />
                      ) : (
                        <FileText size={16} />
                      )}
                      生成结构化报告
                    </Button>
                    <Button
                      variant="outline"
                      disabled={aiBusy}
                      onClick={() =>
                        makeHarnessReport('morning-intelligence-plan', {
                          themes,
                          ladder: ladder.slice(0, 30),
                        })
                      }
                    >
                      {aiBusy ? (
                        <LoaderCircle className="spin" size={16} />
                      ) : (
                        <Sparkles size={16} />
                      )}
                      DeepSeek Harness 复盘
                    </Button>
                  </div>
                  <p className="muted-copy">
                    报告按数据日期保存到当前浏览器，刷新页面后仍会保留；Harness
                    输出作为摘要和风险字段写入同一份报告。
                  </p>
                  {aiError && (
                    <p className="form-error" role="alert">
                      {aiError}
                    </p>
                  )}
                </div>
              </Box>
            </div>
            <Box
              title="报告预览"
              extra={
                report && (
                  <Button variant="outline" onClick={download}>
                    <Download size={15} />
                    下载报告
                  </Button>
                )
              }
            >
              {report ? (
                <ReportView report={report} />
              ) : (
                <Empty
                  title="生成一份可追溯的复盘报告"
                  body="报告包含市场概况、指数表、主线候选表、涨停连板候选表和风险下一步。"
                />
              )}
            </Box>
          </div>
          <div className="section-label">
            复盘、写作与交付 <span>{related.length} 项技能</span>
          </div>
          {skillCards(related)}
        </>
      )}
      {page === 'my-reports' && (
        <>
          <div className="section-intro">
            <div>
              <h2>我的报告</h2>
              <p>每次本地复盘、Harness 复盘、技能研究和个股研究都会保存在此浏览器。刷新页面不会丢失。</p>
            </div>
            <div className="big-count">{archiveRows.length}<small>份</small></div>
          </div>
          <Box title="已生成报告" extra={<span className="subtle">按生成时间排序 · 最多保留 100 份</span>}>
            {archiveRows.length ? (
              <Table>
                <TableHeader><TableRow><TableHead>报告</TableHead><TableHead>类型</TableHead><TableHead>数据日期</TableHead><TableHead>生成时间</TableHead><TableHead>操作</TableHead></TableRow></TableHeader>
                <TableBody>
                  {archiveRows.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell><b>{item.title}</b><small className="table-sub">{item.generatedBy} · {item.summary.slice(0, 62)}{item.summary.length > 62 ? '…' : ''}</small></TableCell>
                      <TableCell><span className={item.content.kind === 'harness-task' && String(item.content.status || '') !== 'completed' ? 'status-warning' : 'status-good'}>{item.content.kind === 'harness-task' && String(item.content.status || '') !== 'completed' ? `未完成 · ${item.reportType}` : item.reportType}</span></TableCell>
                      <TableCell>{d(item.date)}</TableCell>
                      <TableCell>{new Date(item.updatedAt || item.createdAt).toLocaleString('zh-CN', { hour12: false })}</TableCell>
                      <TableCell className="archive-actions"><Button variant="outline" size="sm" onClick={() => setOpenedArchive(item)}><FileText size={14} />查看</Button><button className="archive-delete" aria-label={`删除 ${item.title}`} onClick={() => deleteArchivedReport(item.id)}><Trash2 size={15} /></button></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : <Empty title="还没有生成报告" body="从“复盘与报告”生成市场报告，或从任一技能运行 Harness 后，这里会自动归档。" />}
          </Box>
          <Sheet open={!!openedArchive} onOpenChange={(open) => !open && setOpenedArchive(null)}>
            <SheetContent className="archive-sheet">
              <SheetHeader><SheetTitle>{openedArchive?.title}</SheetTitle><SheetDescription>{openedArchive?.reportType} · {openedArchive ? d(openedArchive.date) : ''} · {openedArchive?.generatedBy}</SheetDescription></SheetHeader>
              {openedArchive && (
                <div className="detail-body">
                  {openedArchive.content.kind === 'market-report' && openedArchive.content.report ? <ReportView report={openedArchive.content.report as unknown as Report} /> : openedArchive.content.kind === 'stock-research' ? <ArchivedStockReport item={openedArchive} /> : <HarnessOutput raw={openedArchive.raw || openedArchive.summary} compact={false} structured={openedArchive.content.structured as StructuredStrategy | null | undefined} />}
                </div>
              )}
            </SheetContent>
          </Sheet>
        </>
      )}
      {page === 'capital' && (
        <>
          <Tabs defaultValue="lhb" className="workspace-tabs capital-tabs">
            <TabsList className="workspace-tabs-list">
              <TabsTrigger value="lhb">龙虎榜</TabsTrigger>
              <TabsTrigger value="youzi">游资追踪</TabsTrigger>
              <TabsTrigger value="institution">机构与庄家</TabsTrigger>
            </TabsList>
            <TabsContent value="lhb">
              <Box title="龙虎榜资金席位" extra={<Button variant="outline" size="sm" onClick={() => setCapitalRefreshNonce((value) => value + 1)} disabled={capitalLoading}>{capitalLoading ? <LoaderCircle className="spin" size={14} /> : <RefreshCw size={14} />}刷新龙虎榜</Button>}>
                <div className="capital-source-meta"><span>{capitalLoading ? '正在读取 Harness 落盘数据…' : `数据日 ${d(capitalSnapshot?.date || market.date)} · ${capitalRows.length} 条龙虎榜记录`}</span><small>{capitalSnapshot?.fetchedAt ? `同步于 ${new Date(capitalSnapshot.fetchedAt).toLocaleTimeString('zh-CN', { hour12: false })}` : '等待最新快照'}</small></div>
                {capitalRows.length ? <Table><TableHeader><TableRow><TableHead>股票</TableHead><TableHead>净买额</TableHead><TableHead>买入额</TableHead><TableHead>卖出额</TableHead><TableHead>上榜原因</TableHead></TableRow></TableHeader><TableBody>{capitalRows.slice(0,20).map((row,i)=><TableRow key={`${row.code}-${i}`}><TableCell><b>{row.name}</b><small>{row.code}</small></TableCell><TableCell className={row.net>=0?'up':'down'}>{money(row.net)}</TableCell><TableCell>{money(row.buy)}</TableCell><TableCell>{money(row.sell)}</TableCell><TableCell>{row.reason}</TableCell></TableRow>)}</TableBody></Table> : <Empty title="等待龙虎榜数据源" body="公开行情快照尚未返回龙虎榜记录，请稍后重试数据更新。"/>}
                {capitalHarnessOutput && <div className="capital-harness-report"><h4>Harness 资金数据校验</h4><HarnessOutput raw={capitalHarnessOutput} /></div>}
              </Box>
            </TabsContent>
            <TabsContent value="youzi">
              <Box title="游资追踪" extra={<span className="status-warning">部分数据待接入</span>}>
                <div className="capital-gap-grid"><div className="capital-gap-card ready"><Check size={16}/><div><b>龙虎榜上榜记录</b><small>已接入同日 59 条公开记录</small></div></div><div className="capital-gap-card missing"><X size={16}/><div><b>营业部 / 游资身份映射</b><small>缺少席位名称到游资标签的核验表</small></div></div><div className="capital-gap-card missing"><X size={16}/><div><b>席位买卖明细</b><small>公开快照只有个股买卖汇总，没有席位逐笔明细</small></div></div><div className="capital-gap-card missing"><X size={16}/><div><b>连续交易日跟踪</b><small>缺少同一席位的多日净买、锁仓和接力统计</small></div></div><div className="capital-gap-card missing"><X size={16}/><div><b>TQ / L2 主力公式</b><small>本机公式授权与实时资金字段尚未验证</small></div></div><div className="capital-gap-card missing"><X size={16}/><div><b>盘中逐笔与封单</b><small>当前只有收盘日线和 OHLC 触板代理</small></div></div></div><div className="content-pad capital-next-step"><b>补全条件</b><p>需要席位明细源、游资身份映射表、同席位多日历史，以及 TQ/L2 授权后的资金公式快照。接入后，Harness 才会生成游资净买、接力路径和活跃度变化。</p></div>
              </Box>
            </TabsContent>
            <TabsContent value="institution">
              <Box title="机构与庄家资金">
                <Empty
                  title="等待本机公式与 TQ 验证"
                  body="当前不把成交额冒充资金净流入。"
                />
              </Box>
            </TabsContent>
          </Tabs>
          <div className="section-label">
            资金研究技能 <span>{related.length} 项技能</span>
          </div>
          {skillCards(related)}
        </>
      )}
      {page === 'settings' && (
        <>
          <Box title="运行环境检测" extra={<Button variant="outline" onClick={refreshEnvironment} disabled={environmentLoading}>{environmentLoading ? <LoaderCircle className="spin" size={14} /> : <RefreshCw size={14} />}重新检测</Button>}>
            <div className="content-pad environment-panel">
              <div className="environment-grid">
                <div className={`environment-card ${environmentTdx.status === 'open' ? 'ready' : 'warn'}`}>
                  <Database size={20} />
                  <div><b>通达信客户端</b><small>{environmentTdx.status === 'open' ? '进程已打开，可调用 TQ' : '未检测到 TdxW 进程'}</small></div>
                  {environmentTdx.status === 'open' ? <strong>已打开</strong> : <Button variant="outline" size="sm" onClick={openTongdaxin}>打开通达信</Button>}
                </div>
                <div className={`environment-card ${environmentDaily.updateDue === true || environmentDaily.complete !== true ? 'warn' : 'ready'}`}>
                  <Database size={20} />
                  <div><b>日线完整性</b><small>最新 {d(String(environmentDaily.latestDate || ''))} · {String(environmentDaily.latestCount || 0)} 只{environmentDaily.freshnessMessage ? ` · ${String(environmentDaily.freshnessMessage)}` : ''}</small></div>
                  <strong>{environmentDaily.updateDue === true ? '需更新' : environmentDaily.complete === true ? '完整' : '需补全'}</strong>
                </div>
                <div className={`environment-card ${environmentHarness.status === 'ready' ? 'ready' : 'warn'}`}>
                  <Workflow size={20} />
                   <div><b>本地 14 技能桥接</b><small>{environmentHarness.base ? String(environmentHarness.base) : '本地数据预检服务'} · {bridgeHostLabel()}</small></div>
                  <strong>{environmentHarness.status === 'ready' ? '已就绪' : '需配置'}</strong>
                </div>
                <div className={`environment-card ${['completed', 'running'].includes(unifiedArchiveStatus) ? 'ready' : 'warn'}`}>
                  <Layers size={20} />
                  <div><b>统一落盘与校验</b><small>落盘 {unifiedArchiveBadge} · 校验 {String(environmentUnifiedVerification.status || '未执行')}</small></div>
                  <strong>{unifiedArchiveBadge}</strong>
                </div>
              </div>
              {environmentSnapshot && <div className="environment-details"><span>沪 {String((environmentDaily.directories as Record<string, unknown> | undefined)?.SH ? ((environmentDaily.directories as Record<string, Record<string, unknown>>).SH.fileCount || 0) : 0)} 文件</span><span>深 {String((environmentDaily.directories as Record<string, Record<string, unknown>> | undefined)?.SZ?.fileCount || 0)} 文件</span><span>北 {String((environmentDaily.directories as Record<string, Record<string, unknown>> | undefined)?.BJ?.fileCount || 0)} 文件</span><span>数据目录 {environmentTdx.root ? String(environmentTdx.root) : '未配置'}</span><span>日线状态 {String(environmentDailyState.status || '未执行')}</span><span>日线时效 {environmentDaily.updateDue === true ? '收盘后待更新' : '已与最新交易日核对'}</span><span>日线索引 {String(environmentDailyIndex.status || '未生成')} · 降级 {String(environmentDailyIndexSummary.fallback_symbol_count || 0)} 股/{String(environmentDailyIndexSummary.fallback_record_count || 0)} 条</span><span>全历史索引 {String(environmentCanonicalIndex.status || '未生成')} · {String(environmentCanonicalIndex.symbolCount || 0)} 股/{String(environmentCanonicalIndex.recordCount || 0)} 条</span><span>索引初始化 {String(environmentIndexInitialization.status || '未执行')}</span><span>其他数据任务 {String(environmentSupplementalState.status || '未执行')}</span><span>补充覆盖：财务 {environmentSupplemental.coverage && (environmentSupplemental.coverage as Record<string, boolean>).financial ? '按需可用' : '按需'} · 股本 {environmentSupplemental.coverage && (environmentSupplemental.coverage as Record<string, boolean>).share_capital ? '已取' : '按需'} · 指数 {String(environmentSupplemental.indexSymbolCount || 0)} 组 · 龙虎榜 {String(environmentSupplemental.lhbMarketRecordCount || environmentSupplemental.lhbRecordCount || 0)} 条 · 融资融券 {String(environmentSupplemental.marginRecordCount || 0)} 条</span></div>}
              <div className="environment-validation"><b>统一落盘计划</b>：每个交易日收盘后 16:30（Asia/Shanghai）自动执行日线、行情、资讯、公式证据和本地来源清单归档；周末及交易所闭市日跳过，并以本地交易日历和实际数据日期为准。当前清单 {d(String(environmentSourceManifest.tradeDate || ''))}，已落盘来源 {String(environmentSourceManifest.availableSourceCount || 0)}/{String(environmentSourceManifest.sourceCount || 0)}。日线归档：{String(environmentDailyArchive.archive_mode || 'unknown')}，本次新增 {String(environmentDailyArchive.incremental_records || 0)} 条；统一落盘：{unifiedArchiveBadge}；校验：{String(environmentUnifiedVerification.status || '未执行')}。</div>
              {environmentRunningStep && <div className="environment-validation">当前数据刷新步骤：{String(environmentRunningStep.name || '日线补全')} · 已在后台运行，页面可继续使用</div>}
              <div className="environment-source-list unified-archive-run-card">
                 <div className="environment-source-title"><b>统一落盘运行状态</b><small>状态 JSON、Harness 上下文和 HTML 报告全部保存在 {runtimeStorageLabel} 内</small></div>
                <div className="environment-details">
                  <span>状态 <strong>{unifiedArchiveBadge}</strong></span>
                  <span>步骤 {unifiedArchiveProgress}/{unifiedArchiveTotal}</span>
                  <span>日期 {d(String(environmentUnifiedArchive.date || ''))}</span>
                  <span>开始 {environmentUnifiedArchive.startedAt ? new Date(String(environmentUnifiedArchive.startedAt)).toLocaleString('zh-CN', { hour12: false }) : '—'}</span>
                  <span>结束 {environmentUnifiedArchive.finishedAt ? new Date(String(environmentUnifiedArchive.finishedAt)).toLocaleString('zh-CN', { hour12: false }) : '—'}</span>
                </div>
                {unifiedArchiveActiveStep && <div className="environment-validation">正在执行：{String(unifiedArchiveActiveStep.name || '准备下一步')} · 完成后自动更新报告</div>}
                {unifiedArchiveSteps.length > 0 && <Table><TableHeader><TableRow><TableHead>步骤</TableHead><TableHead>状态</TableHead><TableHead>返回码</TableHead><TableHead>结果</TableHead></TableRow></TableHeader><TableBody>{unifiedArchiveSteps.map((step, index) => <TableRow key={`${String(step.name || 'step')}-${index}`}><TableCell>{String(step.name || '未命名步骤')}</TableCell><TableCell className={step.status === 'completed' ? 'up' : step.status === 'running' ? '' : 'down'}>{String(step.status || 'pending')}</TableCell><TableCell>{step.code === undefined || step.code === null ? '—' : String(step.code)}</TableCell><TableCell>{step.error ? String(step.error).slice(-160) : step.status === 'running' ? '执行中' : step.resultStored || step.resultPath ? '结果已单独落盘' : '已完成'}</TableCell></TableRow>)}</TableBody></Table>}
                <div className="environment-actions">
                  <Button variant="outline" onClick={() => window.open(unifiedArchiveReportUrl, '_blank', 'noopener,noreferrer')} disabled={!unifiedArchiveReport.htmlUrl && unifiedArchiveStatus === '未执行'}><ArrowUpRight size={15} />查看运行报告</Button>
                  <span>{unifiedArchiveReport.relativeHtml ? `HTML：${String(unifiedArchiveReport.relativeHtml)}` : '报告将在任务启动后生成'}{unifiedArchiveHarness.status ? ` · Harness：${String(unifiedArchiveHarness.status)}` : ''}</span>
                </div>
              </div>
              {environmentSources.length > 0 && <div className="environment-source-list"><div className="environment-source-title"><b>其他数据源新鲜度</b><small>来源快照与 Harness 校验结果</small></div><Table><TableHeader><TableRow><TableHead>数据源</TableHead><TableHead>状态</TableHead><TableHead>日期</TableHead><TableHead>记录</TableHead><TableHead>校验</TableHead></TableRow></TableHeader><TableBody>{environmentSources.map((source, index) => { const name = String(source.name || `source-${index}`); const fresh = source.fresh === true; return <TableRow key={`${name}-${index}`}><TableCell>{dataSourceLabels[name] || name}</TableCell><TableCell className={source.status === 'available' ? 'up' : 'down'}>{source.status === 'available' ? '可用' : String(source.status || '缺失')}</TableCell><TableCell>{d(String(source.date || ''))}</TableCell><TableCell>{source.recordCount === null || source.recordCount === undefined ? '—' : String(source.recordCount)}</TableCell><TableCell className={fresh ? 'up' : 'down'}>{fresh ? '同日最新' : '需复核'}</TableCell></TableRow>; })}</TableBody></Table><div className="environment-validation">Harness 校验：{String(environmentValidation.status || '未执行')} · 数据日 {d(String(environmentValidation.dataDate || environmentDaily.date || ''))}{environmentValidation.summary ? ` · ${String(environmentValidation.summary).slice(0, 120)}` : ''}</div></div>}
              {environmentSourceRows.length > 0 && <div className="environment-source-list"><div className="environment-source-title"><b>统一数据源落盘清单</b><small>压缩包声明来源、当前实际快照和降级状态均写入本地，Harness 只使用可用文件</small></div><Table><TableHeader><TableRow><TableHead>来源</TableHead><TableHead>数据层</TableHead><TableHead>状态</TableHead><TableHead>说明</TableHead></TableRow></TableHeader><TableBody>{environmentSourceRows.map((source, index) => { const sourceId = String(source.id || source.name || `source-${index}`); const sourceStatus = String(source.status || 'missing'); const statusText = sourceStatus === 'available' ? '已落盘' : sourceStatus === 'partial' ? '部分落盘' : sourceStatus === 'declared_not_snapshotted' ? '仅声明未快照' : sourceStatus === 'not_configured' ? '未配置' : sourceStatus === 'blocked' ? '需凭据/受阻' : sourceStatus; return <TableRow key={`${sourceId}-${index}`}><TableCell>{dataSourceLabels[sourceId] || String(source.name || sourceId)}</TableCell><TableCell>{String(source.layer || '—')}</TableCell><TableCell className={sourceStatus === 'available' ? 'up' : 'down'}>{statusText}</TableCell><TableCell>{String(source.reason || '—')}</TableCell></TableRow>; })}</TableBody></Table></div>}
              {environmentIntegrityAfter.stockCount !== undefined && <div className="environment-source-list"><div className="environment-source-title"><b>个股日线完整性报告</b><small>按 TQ 股票清单逐代码核验 .day 文件最后一条记录，并用公开历史 K 线作缺口兜底</small></div><div className="environment-details"><span>目标交易日 {d(String(environmentIntegrity.targetDate || environmentIntegrityAfter.targetDate || ''))}</span><span>应有 {String(environmentIntegrityAfter.stockCount || 0)} 只</span><span>文件已齐 {String(environmentIntegrityAfter.completeCount || 0)} 只</span><span className="up">未上市/停牌计入 {environmentIntegrityNonTrading.length} 只</span><span className={environmentIntegrityUnresolvedCount ? 'down' : 'up'}>仍需补齐 {environmentIntegrityUnresolvedCount} 只</span><span className="up">本次补写 {environmentIntegrityRepairedCount} 条</span></div>{environmentIntegrityUnresolved.length > 0 && <><div className="subtle">以下仅展示前 10 条，完整清单保存在本地完整性报告中。</div><Table><TableHeader><TableRow><TableHead>代码</TableHead><TableHead>市场</TableHead><TableHead>状态</TableHead><TableHead>说明</TableHead></TableRow></TableHeader><TableBody>{environmentIntegrityUnresolved.map((item, index) => <TableRow key={`${String(item.code || 'unknown')}-${index}`}><TableCell>{String(item.code || '—')}</TableCell><TableCell>{String(item.market || '—')}</TableCell><TableCell className="down">未补齐</TableCell><TableCell>TQ 与公开历史 K 线均未返回 {d(String(environmentIntegrity.targetDate || environmentIntegrityAfter.targetDate || ''))} 数据</TableCell></TableRow>)}</TableBody></Table></>}{environmentIntegrityNonTrading.length > 0 && <Table><TableHeader><TableRow><TableHead>代码</TableHead><TableHead>处理</TableHead><TableHead>依据</TableHead></TableRow></TableHeader><TableBody>{environmentIntegrityNonTrading.map((item, index) => <TableRow key={`${String(item.code || 'non-trading')}-${index}`}><TableCell>{String(item.code || '—')}</TableCell><TableCell className="up">{String(item.type || 'non_trading') === 'unlisted' ? '未上市，计入完整' : '停牌/无交易，计入完整'}</TableCell><TableCell>{String(item.reason || '目标交易日无成交记录')}</TableCell></TableRow>)}</TableBody></Table>}</div>}
              <div className="environment-validation environment-manual-guide"><b>日线补齐操作顺序</b><br /><span>① 优先进入通达信客户端并登录，执行“盘后数据下载/日线数据下载”。</span><br /><span>② 点击“通过 Harness 补全通达信日线”，先核验 TDX 并增量写入；若 TDX 断开，系统自动将公开源精确交易日 OHLCV 写入日线降级层和索引。</span><br /><strong>公开降级层只补明确缺失日期，保持 degraded 标记；不能替代 TDX 全历史或 TQ 公式现场回执。</strong></div>
              {environmentIntegrityManualAction && <div className="environment-validation">{environmentIntegrityManualAction}</div>}
              <div className="environment-actions"><Button className="primary-button" onClick={archiveAllData} disabled={unifiedArchiveRunning}>{unifiedArchiveRunning ? <LoaderCircle className="spin" size={15} /> : <Download size={15} />}立即统一落盘（全源）</Button><Button variant="outline" onClick={verifyAllData} disabled={unifiedVerificationRunning}>{unifiedVerificationRunning ? <LoaderCircle className="spin" size={15} /> : <Check size={15} />}校验落盘并调用 Harness</Button><Button variant="outline" onClick={rebuildAllIndices} disabled={indexRebuildRunning || dailyRefreshRunning}>{indexRebuildRunning ? <LoaderCircle className="spin" size={15} /> : <RefreshCw size={15} />}初始化并重建全量索引</Button><Button variant="outline" onClick={replenishDailyData} disabled={dailyRefreshRunning || indexRebuildRunning}>{dailyRefreshRunning ? <LoaderCircle className="spin" size={15} /> : <RefreshCw size={15} />}刷新交易日行情（日线+市场信息）</Button><Button variant="outline" onClick={replenishSupplementalData} disabled={supplementalRefreshRunning}>{supplementalRefreshRunning ? <LoaderCircle className="spin" size={15} /> : <Database size={15} />}仅补齐其他数据</Button><span>{environmentMessage || '页面打开时检测一次；自动计划在每个交易日收盘后 16:30 落盘。初始化会读取所选通达信目录全部 .day，建立全量个股索引；普通任务不依赖 5 分钟线。'}</span></div>
            </div>
          </Box>
          <div className="section-spacer" />
          <div className="two-column">
            <Box title="本地数据源">
              <div className="content-pad">
                <div className="source-status">
                  <Database size={25} />
                  <div>
                    <b>通达信日线</b>
                    <small>已读取为当日网页快照</small>
                  </div>
                  <span className="status-good">已导入</span>
                </div>
                <dl className="settings-list">
                  <div>
                    <dt>行情位置</dt>
                    <dd>{environmentTdx.root ? String(environmentTdx.root) : '未配置'}</dd>
                  </div>
                  <div>
                    <dt>全历史资源库</dt>
                    <dd>{environmentCanonicalIndex.sourceFile ? `${String(environmentCanonicalIndex.sourceFile)} · ${String(environmentCanonicalIndex.symbolCount || 0)} 股` : '未建立，请点击“初始化并重建全量索引”'}</dd>
                  </div>
                  <div>
                    <dt>最新文件日期</dt>
                    <dd>{d(market.date)}</dd>
                  </div>
                  <div>
                    <dt>股票覆盖</dt>
                    <dd>
                      {market.total} 只 · 同日 {market.currentCount} 只
                    </dd>
                  </div>
                  <div>
                    <dt>涨停候选</dt>
                    <dd>
                      {ladder.length} 只 · 连续候选{' '}
                      {ladder.filter((x) => x.streak > 1).length} 只
                    </dd>
                  </div>
                  <div>
                    <dt>TDX行业 / 主题</dt>
                    <dd>{market.sectors?.length || 0} / {market.conceptBoards?.length || 0} 个聚合榜</dd>
                  </div>
                  <div>
                    <dt>盘中数据</dt>
                    <dd>{market.intradayProxy?.upperHitCount || 0} 只触板 · OHLC代理；5分钟同日 {market.intradayProxy?.lc5CurrentDateCount || 0}/{market.intradayProxy?.lc5Files || 0}</dd>
                  </div>
                  <div>
                    <dt>待接入快照</dt>
                    <dd>北向资金 · 主力资金 · 当日新闻（融资融券与龙虎榜已接入）</dd>
                  </div>
                </dl>
              </div>
            </Box>
            <Box title="DeepSeek Harness">
              <div className="content-pad">
                <div className="source-status">
                  <Workflow size={25} />
                  <div>
                    <b>DeepSeek Harness</b>
                    <small>本地 headless 桥接</small>
                  </div>
                  <span className="status-good">已接入</span>
                </div>
                <dl className="settings-list">
                  <div>
                    <dt>受控技能包</dt>
                    <dd>14 项</dd>
                  </div>
                  <div>
                    <dt>网页桥接</dt>
                     <dd>{bridgeHostLabel()}</dd>
                  </div>
                  <div>
                    <dt>密钥保存</dt>
                    <dd>仅环境变量</dd>
                  </div>
                  <div>
                    <dt>报告保存</dt>
                    <dd>浏览器 localStorage</dd>
                  </div>
                </dl>
              </div>
            </Box>
          </div>
          <div className="section-label">
            系统与数据能力 <span>{related.length} 项</span>
          </div>
          {skillCards(related)}
        </>
      )}
      <Sheet open={!!skill} onOpenChange={(open) => !open && setSkill(null)}>
        <SheetContent className="skill-sheet">
          <SheetHeader>
            <SheetTitle>{skill?.name}</SheetTitle>
            <SheetDescription>
              统一技能入口 · {skill?.id} · 当日数据 {d(market.date)}
            </SheetDescription>
          </SheetHeader>
          {skill && (
            <div className="detail-body">
              <p className="skill-introduction">{skillIntroduction(skill)}</p>
              <div className="skill-original-meta"><b>原始技能 ID：</b>{skill.id}<br /><b>原始别名：</b>{skill.alias}<br /><b>迁移说明：</b>{skill.note}</div>
              {skill.group === 'selection' && strategyCatalogItem(skill.id) && (() => {
                const catalog = strategyCatalogItem(skill.id)!;
                return <div className="skill-original-meta"><b>数据状态：</b>{catalog.dataStatus === 'available' ? '可用' : catalog.dataStatus === 'partial' ? '部分缺口' : '缺失，已置灰'}<br /><b>业务入口：</b>{catalog.businessEntry}<br /><b>业务代码指纹：</b>{catalog.businessHash.slice(0, 16)}…<br /><b>执行方式：</b>网页脚本 + DeepSeek Harness{catalog.minuteData?.mode === 'optional_degraded' && <><br /><b>5 分钟线：</b>外部按需读取；缺少时标记 DEGRADED，不进入 EXE</>}{catalog.missingData.length > 0 && <><br /><b>缺少数据：</b>{catalog.missingData.join('、')}</>}</div>;
              })()}
              <div className="skill-detail-id">
                <b>依赖：</b>
                {skill.dependencies.join(' · ')}
              </div>
              {skillMode(skill.id) === 'basic' ? (
                <>
                  <div className="skill-detail-status skill-detail-status-basic">
                    <b>基础技能 · 仅展示详情</b><br />
                    该能力用于说明系统的数据接入、质量规则和内部支撑边界，不是一次性分析任务。本页不会生成本地预检，不会启动 Harness，也不会写入运行报告。
                  </div>
                  <div className="detail-title">技能详情</div>
                  <p className="muted-copy">{skill.note}</p>
                  <p className="harness-eta">如需运行具体分析，请进入对应的行情、策略或个股研究技能；基础能力本身只作为网页端可核验的能力说明。</p>
                </>
              ) : (
                <>
                  <div className="detail-title">执行说明</div>
                  <p className="muted-copy">网页适配层先生成本地数据预检与落盘运行单；随后可把同一份预检和当日行情交给对应技能的 Harness。缺数据时仍允许调用，但只返回阻塞诊断或降级报告。</p>
                  <p className="harness-eta">预检不调用模型、不补造数据，也不把预检结果写成策略结论。预检回执写入应用数据目录；Harness 任务与结果也会由桥接服务落盘。</p>
                  <div className="action-row">
                    <Button
                      className="primary-button"
                      disabled={skillBusy || skillHarnessBusy}
                      onClick={() => runSkill(skill)}
                    >
                      {skillBusy ? <LoaderCircle className="spin" size={15} /> : <Database size={15} />}
                      {skillBusy ? '生成预检中…' : '生成本地数据预检'}
                    </Button>
                    <Button
                      variant="outline"
                      disabled={skillBusy || skillHarnessBusy || aiBusy}
                      onClick={() => runSkillHarness(skill)}
                    >
                      {skillHarnessBusy ? <LoaderCircle className="spin" size={15} /> : <Sparkles size={15} />}
                      {skillHarnessBusy ? 'Harness 运行中…' : '调用 Harness'}
                    </Button>
                  </div>
                  {skillOutput && <div className="strategy-run-output ready"><pre>{skillOutput}</pre></div>}
                  {skillHarnessError && <p className="form-error" role="alert">{skillHarnessError}</p>}
                  {skillHarnessOutput && <div className="strategy-run-output ready"><HarnessOutput raw={skillHarnessOutput} /></div>}
                </>
              )}
              <Button variant="outline" onClick={() => setSkill(null)}>
                <X size={15} />
                关闭
              </Button>
            </div>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
