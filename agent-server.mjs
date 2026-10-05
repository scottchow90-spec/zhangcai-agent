import http from 'node:http';
import { spawn } from 'node:child_process';
import path from 'node:path';
import { accessSync, closeSync, cpSync, createReadStream, existsSync, mkdirSync, openSync, readFileSync, readSync, readdirSync, statSync, constants as fsConstants } from 'node:fs';
import { mkdir, rename, writeFile, unlink } from 'node:fs/promises';
import { randomUUID } from 'node:crypto';

let deepSeekCredentialSource = '';
const runtimeJsonWrites = new Map();

// Load the ignored local environment file before resolving the bridge
// configuration. This keeps scheduled/restarted bridge processes consistent
// without committing credentials to the project.
function loadLocalEnvFile() {
  const appRoot = path.resolve(process.env.ZHANGCAI_APP_ROOT || process.cwd());
  const packagedResourceRoot = process.env.LOCALAPPDATA && process.env.ZHANGCAI_PACKAGED === '1'
    ? path.join(process.env.LOCALAPPDATA, '掌财智能体-4319', 'resource-library')
    : '';
  const configuredResourceRoot = process.env.ZHANGCAI_RESOURCE_LIBRARY || packagedResourceRoot;
  const candidates = [
    process.env.ZHANGCAI_CREDENTIALS_FILE,
    configuredResourceRoot ? path.join(configuredResourceRoot, '.env.local') : '',
    process.env.ZHANGCAI_DATA_DIR ? path.join(process.env.ZHANGCAI_DATA_DIR, '.env.local') : '',
    path.join(appRoot, '.env.local'),
  ].filter(Boolean);
  for (const file of [...new Set(candidates)]) {
    if (!existsSync(file)) continue;
    try {
      for (const line of readFileSync(file, 'utf8').split(/\r?\n/)) {
        const match = line.match(/^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*?)\s*$/);
        if (match && !process.env[match[1]]) {
          process.env[match[1]] = match[2].replace(/^['"]|['"]$/g, '');
          if (match[1] === 'DEEPSEEK_API_KEY' && process.env.DEEPSEEK_API_KEY) deepSeekCredentialSource = file;
        }
      }
      if (process.env.DEEPSEEK_API_KEY) return;
    } catch (error) {
      console.warn(`[agent] 无法读取凭据配置：${error instanceof Error ? error.message : String(error)}`);
    }
  }
}
loadLocalEnvFile();

// The 14-skill web app is local by default. LAN exposure requires an explicit
// environment override and an authenticated front door.
const HOST = process.env.ZHANGCAI_HOST || '127.0.0.1';
const PORT = Number(process.env.ZHANGCAI_BRIDGE_PORT || 4319);
const BRIDGE_CAPABILITIES = ['runtime/tdx/open', 'runtime/environment'];
const APP_ROOT = path.resolve(process.env.ZHANGCAI_APP_ROOT || process.cwd());
// Development keeps data beside the project. The packaged desktop launcher
// sets ZHANGCAI_PACKAGED=1 and points ZHANGCAI_DATA_DIR at a user-writable
// directory so an install under Program Files never receives runtime writes.
const PACKAGED_RUNTIME = process.env.ZHANGCAI_PACKAGED === '1';
const configuredDataRoot = PACKAGED_RUNTIME ? process.env.ZHANGCAI_DATA_DIR : '';
const RESOURCE_LIBRARY_ROOT = path.resolve(
  process.env.ZHANGCAI_RESOURCE_LIBRARY
    || (PACKAGED_RUNTIME && process.env.LOCALAPPDATA
      ? path.join(process.env.LOCALAPPDATA, '掌财智能体-4319', 'resource-library')
      : path.join(APP_ROOT, 'app-data')),
);
const DATA_ROOT = path.resolve(configuredDataRoot || RESOURCE_LIBRARY_ROOT);
const CREDENTIALS_ENV_FILE = path.join(RESOURCE_LIBRARY_ROOT, '.env.local');
const RUNTIME_ROOT = path.join(DATA_ROOT, 'runtime');
const HARNESS_ROOT = path.join(DATA_ROOT, 'harness');
const HARNESS_CONTEXT_ROOT = path.join(HARNESS_ROOT, 'context');
const HARNESS_JOBS_ROOT = path.join(HARNESS_ROOT, 'jobs');
const MARKET_LATEST_FILE = path.join(RUNTIME_ROOT, 'market-latest.json');
const STRATEGY_JOBS_ROOT = path.join(HARNESS_ROOT, 'strategy-jobs');
const AFTER_CLOSE_SCHEDULE_FILE = path.join(HARNESS_ROOT, 'schedules', 'after-close-daily-refresh.json');
const RUNTIME_POLICY_FILE = path.join(HARNESS_CONTEXT_ROOT, 'runtime-policy.json');
const REPORT_ARCHIVE_ROOT = path.join(DATA_ROOT, 'reports', 'archive');
const REPORT_ARCHIVE_INDEX_FILE = path.join(REPORT_ARCHIVE_ROOT, 'index.json');
const UNIFIED_ARCHIVE_REPORT_ROOT = path.join(DATA_ROOT, 'reports', 'unified-archive');
const UNIFIED_ARCHIVE_OUTPUT_ROOT = path.join(DATA_ROOT, 'runtime', 'unified-archive-output');
const SKILL_SOURCE = path.resolve(process.env.ZHANGCAI_SKILLS_DIR || path.join(APP_ROOT, 'harness-skills'));
const DAILY_STATE_FILE = path.join(RUNTIME_ROOT, 'daily-refresh-state.json');
const DAILY_INDEX_INITIALIZATION_STATE_FILE = path.join(RUNTIME_ROOT, 'daily-index-initialization-state.json');
const SUPPLEMENTAL_STATE_FILE = path.join(RUNTIME_ROOT, 'supplemental-refresh-state.json');
const UNIFIED_ARCHIVE_STATE_FILE = path.join(RUNTIME_ROOT, 'unified-data-archive-state.json');
const UNIFIED_VERIFY_STATE_FILE = path.join(RUNTIME_ROOT, 'unified-data-verification-state.json');
const SKILL14_CATALOG_FILE = path.join(APP_ROOT, 'config', 'skill14-catalog.json');
const TDX_DAY_RECORD_SIZE = 32;
const TDX_HISTORY_INDEX_FILE = path.join(DATA_ROOT, 'market', 'daily', 'index', 'tdx-symbol-index.json');
const CANONICAL_DAILY_FILE = path.join(DATA_ROOT, 'market', 'daily', 'aggregate', 'tdx-bars.jsonl');
const CANONICAL_DAILY_INDEX_FILE = path.join(DATA_ROOT, 'market', 'daily', 'index', 'canonical-symbol-index.json');
const DAILY_DATA_INDEX_FILE = path.join(DATA_ROOT, 'market', 'daily', 'index', 'daily-data-index.json');
const DAILY_FALLBACK_ROOT = path.join(DATA_ROOT, 'market', 'daily', 'fallback');
const SUPPLEMENTAL_ROOT = path.join(DATA_ROOT, 'evidence', 'supplemental');
const SUPPLEMENTAL_LATEST_FILE = path.join(SUPPLEMENTAL_ROOT, 'latest.json');

function bridgeTdxRoot() {
  const configured = String(process.env.ZHANGCAI_TDX_ROOT || '').trim();
  // A packaged desktop without a configured client must report “not
  // configured”, never silently inspect the development machine's C: path.
  return configured || (PACKAGED_RUNTIME ? '' : 'C:\\new_tdx_mock');
}

function credentialStatus() {
  const value = String(process.env.DEEPSEEK_API_KEY || '');
  const configured = value.length > 0;
  return {
    configured,
    source: configured ? (deepSeekCredentialSource || 'process environment') : 'missing',
    keyHint: configured ? `${value.slice(0, 3)}…${value.slice(-4)}` : '',
  };
}

function resourceLibraryStatus() {
  let writable = false;
  try {
    accessSync(RESOURCE_LIBRARY_ROOT, fsConstants.W_OK);
    writable = true;
  } catch { /* startup creates the directory on first write */ }
  return { root: RESOURCE_LIBRARY_ROOT, writable };
}
// 复盘任务会携带 TDX 行业/主题、涨停梯队和榜单上下文；完整 JSON
// 通常超过 128KB。保留本地服务的明确上限，但避免超限时直接 socket hang up。
const MAX_BODY = 4 * 1024 * 1024;
// 结构化 Harness 报告可能包含多张行情/指标表。32KB 会在 JSON 结束前
// 截断，前端随后只能提示“JSON 对象未闭合”。保留一个合理上限，避免
// 无限输出，同时覆盖完整策略报告。
const MAX_OUTPUT = 256 * 1024;
function localPythonExecutable() {
  const configured = process.env.ZHANGCAI_PYTHON || process.env.TDX_PYTHON;
  if (configured && existsSync(configured)) return configured;
  const candidates = [
    path.join(APP_ROOT, '.runtime', 'python', 'python.exe'),
    path.join(APP_ROOT, 'runtime', 'python', 'python.exe'),
  ];
  // Prefer a Python runtime carried by the packaged application. If none is
  // bundled, use the operating-system command; never reach into an agent
  // cache because that would make the EXE depend on the host agent.
  return candidates.find((candidate) => candidate && existsSync(candidate)) || (process.platform === 'win32' ? 'python.exe' : 'python3');
}

function isLocalOnlyDataPolicy() {
  // Keep strict local-only mode available for diagnostics, but do not enable
  // it merely because the bridge is packaged. The desktop product supports
  // explicit public-source updates and TDX -> public fallback; each script
  // still writes its result into DATA_ROOT before Harness use.
  return process.env.ZHANGCAI_DATA_POLICY === 'local_tdx_only';
}

function localScriptEnvironment(extra = {}) {
  const requestedPythonPath = extra.PYTHONPATH || process.env.PYTHONPATH || '';
  const configuredTdxRoot = bridgeTdxRoot();
  // Python skill packages historically used both TDX_ROOT and
  // ZHANGCAI_TDX_ROOT. Always pass both names, and use an explicit sentinel
  // when the user has not selected a TDX directory. Passing an empty string
  // would make Path('') resolve to the current data directory on Windows.
  const childTdxRoot = configuredTdxRoot || path.join(DATA_ROOT, 'runtime', '__tdx_root_not_configured__');
  return {
    ...process.env,
    ...extra,
    ZHANGCAI_APP_ROOT: APP_ROOT,
    ZHANGCAI_DATA_DIR: DATA_ROOT,
    ZHANGCAI_TDX_ROOT: childTdxRoot,
    TDX_ROOT: childTdxRoot,
    TDX_ROOTS: childTdxRoot,
    BAIMAO_TDX_ROOT: childTdxRoot,
    ONESTOCK_STOCK_DATA_ROOT: DATA_ROOT,
    STOCK_SKILLS_ROOT: SKILL_SOURCE,
    ZHANGCAI_SKILLS_DIR: SKILL_SOURCE,
    ZHANGCAI_DATA_POLICY: isLocalOnlyDataPolicy() ? 'local_tdx_only' : (process.env.ZHANGCAI_DATA_POLICY || ''),
    PYTHONPATH: [path.join(APP_ROOT, 'scripts'), requestedPythonPath].filter(Boolean).join(path.delimiter),
  };
}

const HARNESS_JSON_SCHEMA = '最终只返回一个严格 JSON 对象，不要 Markdown、代码围栏或前后解释。字段必须为：status(string)、summary(string)、data_date(string)、data_scope(string)、cautions(string[])、findings({title:string,text:string}[])、tables({title:string,columns:string[],rows:string[][]}[])。所有结论只能引用传入数据，缺失项写入 cautions，不得虚构。报告按网页重点摘要标准输出：summary 不超过 120 字，findings 最多 5 条且每条不超过 100 字，tables 只保留最关键的 3 张表、每张最多 10 行；优先保留主线结论、核心指标、Top 候选和风险边界，省略重复解释。';
// DeepSeek Harness 启动、读取本地技能文件和补充数据通常需要较长时间；
// 研究技能统一给足 20 分钟，避免模型刚开始输出前被桥接层杀掉。独立
// 运行时仍可通过 DSH_TIMEOUT_MS 覆盖，但默认值必须适合完整研究链路。
const DEFAULT_TIMEOUT_MS = Number(process.env.DSH_TIMEOUT_MS || 1200000);
const SKILL_TIMEOUT_MS = {
  'five-dimension-resonance': 1200000,
  'a-share-leader-deep-research': 1200000,
  'a-share-limit-up-mining': 1200000,
  'limit-up-review': 1200000,
  'stock-analysis': 1200000,
  'stock-study': 1200000,
  'stock-research-engine': 1200000,
};
const CANONICAL_STRATEGY_IDS = new Set([
  'a-share-15d-selection',
  'a-share-bottom-fishing',
  'convertible-bond-screening-strategy',
  'buzhang-leader-mining',
  'chanlun-first-board',
  'dragon-pullback',
  'feilong-strategy',
  'five-dimension-resonance',
  'four-strategy-system',
  'golden-ignition',
  'nana-teacher-five-strategies',
  'oversold-first-board',
  'quality-track-stock-selection',
  'quant-strategy-bundle-chen',
  'quantitative-trading',
]);
const MINUTE_DATA_POLICIES = new Map([
  ['feilong-strategy', { mode: 'optional_degraded', purpose: '飞龙高级因子需要外部 LC5；缺少时只输出日线/公式部分。' }],
  ['convertible-bond-screening-strategy', { mode: 'optional_degraded', purpose: '部分可转债分钟特征按任务读取外部 LC5。' }],
  ['nana-teacher-five-strategies', { mode: 'optional_degraded', purpose: '5 分钟复核是可选辅助证据，不阻塞普通日线任务。' }],
  ['a-share-leader-deep-research', { mode: 'optional_degraded', purpose: '精确首封、炸板和重封时序需要外部 LC5；缺少时保留日线降级边界。' }],
]);
// 技能包目录使用带版本的展示 ID，但原始策略脚本保留历史目录名。
// 所有策略入口在桥接层统一归一化，避免把展示 ID 直接拼成不存在的路径。
const STRATEGY_ID_ALIASES = new Map([
  ['golden-ignition-v8', 'golden-ignition'],
]);
function canonicalStrategyId(skillId) {
  return STRATEGY_ID_ALIASES.get(skillId) || skillId;
}
const PARAMETER_REQUIRED_STRATEGIES = new Set(['golden-ignition']);
const SPECIAL_DATA_STRATEGIES = new Set(['convertible-bond-screening-strategy']);
const harnessJobs = new Map();
const harnessJobWriteChains = new Map();
const strategyJobs = new Map();
const dailyJobs = new Map();
const supplementalJobs = new Map();
const supplementalTargetJobs = new Map();
const unifiedArchiveJobs = new Map();
const unifiedVerificationJobs = new Map();
const dailyIndexInitializationJobs = new Map();
// A stock detail view and the Harness preparation step can request the same
// five-formula receipt at nearly the same time. Keep one live TQ child per
// symbol so the second request does not wait on the Python file lock and then
// report a misleading partial/HTTP-200 error.
const tqFormulaRequests = new Map();
// Index and full-market refreshes can finish in either order.  Serialize the
// read/merge/write cycle so a late request cannot write from an older file
// snapshot and erase the other refresh's newer fields.
let marketSnapshotWriteChain = Promise.resolve();
// DeepSeek Harness 使用本地单任务锁。没有这个锁时，启动个股技能会在
// 真正创建任务之前抛出 ReferenceError，前端看到的就是“连接被关闭”。
let activeHarnessExecution = null;
let tdxDailyIntegrityScanCache = null;
const TDX_DAILY_INTEGRITY_CACHE_TTL_MS = 60_000;

function formatHarnessElapsed(startedAt) {
  const seconds = Math.max(0, Math.floor((Date.now() - Number(startedAt || Date.now())) / 1000));
  return `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
}

function harnessBusyPayload(active = activeHarnessExecution) {
  const skillId = String(active?.skill_id || '通用研究');
  return {
    status: 'busy',
    error: `Harness 正在执行长任务（${skillId}，已运行 ${formatHarnessElapsed(active?.started_at)}），请稍后再试。`,
    active_job: active ? {
      id: active.id,
      skill_id: active.skill_id || null,
      started_at: active.started_at,
    } : null,
  };
}

function createHarnessBusyError(active = activeHarnessExecution) {
  const error = new Error(harnessBusyPayload(active).error);
  error.code = 'HARNESS_BUSY';
  return error;
}

function reserveHarnessExecution(id, skillId = '') {
  if (activeHarnessExecution && activeHarnessExecution.id !== id) return activeHarnessExecution;
  activeHarnessExecution = { id, skill_id: skillId || null, started_at: Date.now() };
  return null;
}

function releaseHarnessExecution(id) {
  if (activeHarnessExecution?.id === id) activeHarnessExecution = null;
}

function isHarnessBusyError(error) {
  return Boolean(error && typeof error === 'object' && error.code === 'HARNESS_BUSY');
}

function harnessJobFile(id) {
  return path.join(HARNESS_JOBS_ROOT, `${id}.json`);
}

function persistHarnessJob(job) {
  const id = String(job?.id || '');
  if (!id) return;
  const previous = harnessJobWriteChains.get(id) || Promise.resolve();
  const next = previous
    .catch(() => undefined)
    .then(() => writeRuntimeJson(harnessJobFile(id), job))
    .catch((error) => {
      console.error(`[agent] 无法保存 Harness 任务 ${id.slice(0, 8)}：${error instanceof Error ? error.message : String(error)}`);
    });
  harnessJobWriteChains.set(id, next);
  void next.finally(() => {
    if (harnessJobWriteChains.get(id) === next) harnessJobWriteChains.delete(id);
  });
}

function strategyJobFile(id) {
  return path.join(STRATEGY_JOBS_ROOT, `${id}.json`);
}

function persistStrategyJob(job) {
  void writeRuntimeJson(strategyJobFile(job.id), job).catch((error) => {
    console.error(`[agent] 无法保存策略任务 ${job.id.slice(0, 8)}：${error instanceof Error ? error.message : String(error)}`);
  });
}

function timeoutForSkill(skillId) {
  const configured = SKILL_TIMEOUT_MS[skillId] || DEFAULT_TIMEOUT_MS;
  return Number.isFinite(configured) && configured > 0 ? configured : 1200000;
}

function readTdxPrivateFormulaNames(tdxRoot = bridgeTdxRoot()) {
  const registryPath = path.join(tdxRoot, 'T0002', 'PriLoc.dat');
  if (!existsSync(registryPath)) return { path: registryPath, names: [] };
  try {
    const bytes = readFileSync(registryPath);
    const names = [];
    for (let offset = 24; offset + 20 <= bytes.length; offset += 56) {
      const raw = bytes.subarray(offset, offset + 20);
      const end = raw.indexOf(0);
      const text = raw.subarray(0, end >= 0 ? end : raw.length).toString('latin1').trim();
      if (text) names.push(text);
    }
    return { path: registryPath, names };
  } catch (error) {
    return { path: registryPath, names: [], error: error instanceof Error ? error.message : String(error) };
  }
}

function resolveSkillEntry(skillRoot) {
  const scripts = path.join(skillRoot, 'scripts');
  if (!existsSync(scripts)) return '';
  const preferred = path.join(scripts, 'runtime_entry.py');
  if (existsSync(preferred)) return preferred;
  try {
    const candidates = readdirSync(scripts)
      .filter((name) => /_entry\.py$/i.test(name) && !/^legacy_/i.test(name))
      .sort();
    return candidates.length ? path.join(scripts, candidates[0]) : '';
  } catch {
    return '';
  }
}

function corsHeaders(req) {
  const requestOrigin = req.headers?.origin;
  const localOrigins = new Set([
    'http://127.0.0.1:3003',
    'http://localhost:3003',
    'http://127.0.0.1:3004',
    'http://localhost:3004',
  ]);
  // The packaged Electron UI and bridge intentionally use different,
  // dynamically allocated loopback ports. Allow only local HTTP origins so
  // this does not broaden the bridge to LAN or public callers.
  const isLocalDynamicOrigin = typeof requestOrigin === 'string'
    && /^http:\/\/(?:127\.0\.0\.1|localhost):\d+$/.test(requestOrigin);
  const allowOrigin = typeof requestOrigin === 'string' && (localOrigins.has(requestOrigin) || isLocalDynamicOrigin)
    ? requestOrigin
    : 'http://127.0.0.1:3003';
  return {
    'Access-Control-Allow-Origin': allowOrigin,
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    // Chrome 的 Private Network Access 预检会要求此头部；网页运行在
    // localhost、桥接服务监听 127.0.0.1 时，缺少它会直接表现为 Failed to fetch。
    'Access-Control-Allow-Private-Network': 'true',
  };
}

function json(res, status, value) {
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    ...corsHeaders(res.req),
  });
  res.end(JSON.stringify(value));
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY) {
        reject(new Error('请求内容过大'));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', reject);
  });
}

function buildPrompt(task, market, skillId, context) {
  const isDataReplenishment = skillId === 'market-data-replenishment';
  const indices = Array.isArray(market.indices) ? market.indices : [];
  const indexText = indices.map((x) => `${x.name} ${x.close} (${x.pct}%)`).join('；');
  const gainText = Array.isArray(market.gainLeaders) ? JSON.stringify(market.gainLeaders) : '未提供';
  const amountText = Array.isArray(market.amountLeaders) ? JSON.stringify(market.amountLeaders) : '未提供';
  const lossText = Array.isArray(market.lossLeaders) ? JSON.stringify(market.lossLeaders) : '未提供';
  const limitDownText = Array.isArray(market.limitDownCandidates) ? JSON.stringify(market.limitDownCandidates) : '未提供';
  const limitText = Array.isArray(market.limitCandidates) ? JSON.stringify(market.limitCandidates) : '未提供';
  const themeText = Array.isArray(market.themes) ? JSON.stringify(market.themes) : '未提供';
  const sectorText = Array.isArray(market.sectors) ? JSON.stringify(market.sectors) : '未提供';
  const conceptText = Array.isArray(market.conceptBoards) ? JSON.stringify(market.conceptBoards) : '未提供';
  const intradayText = market.intradayProxy ? JSON.stringify(market.intradayProxy) : '未提供';
  const sourceText = market.dataSources ? JSON.stringify(market.dataSources) : '未提供';
  const priorText = market.priorLimitUpStats ? JSON.stringify(market.priorLimitUpStats) : '未提供';
  const dailyContext = readJson(path.join(HARNESS_CONTEXT_ROOT, 'latest-data.json'));
  const localDataPage = readJson(path.join(HARNESS_CONTEXT_ROOT, 'local-data-page.json'));
  const dailyDataIndex = readJson(DAILY_DATA_INDEX_FILE);
  const runtimePolicy = readJson(RUNTIME_POLICY_FILE);
  const supplementalData = context?.supplementalData || null;
  const resources = context?.resourceLibrary && typeof context.resourceLibrary === 'object'
    ? context.resourceLibrary
    : resourceLibraryContext();
  return [
    '你是掌财智能体的本地研究助手。',
    `当前技能：${skillId || '通用行情研究'}`,
    '网页已完成技能路由，当前技能由调用方提供；不要声称技能目录不可用，也不要要求重新安装技能。',
    task,
    '',
    isDataReplenishment
      ? '这是数据补全任务。先加载 market-data-replenishment 技能，严格按其公开数据源、交易日校验和保存规则执行。允许访问该技能列出的公开接口与本地项目文件；不得将模型推测写为数据。'
      : '优先使用下面的 3003 本地通达信摘要和本地公开来源快照。网页已经把可计算的榜单、TDX行业/主题成员聚合和涨停候选表传入，必须引用这些表；同时按本地数据落盘页读取当前应用已归档的行情、龙虎榜、连板和新闻快照。不要笼统声称缺少涨幅榜、成交额榜、跌幅榜、板块榜或涨停候选。跌停、前日涨停表现和盘中封板率是日线推导，必须标记为推导候选；TDX行业/主题映射可用于结构化候选，但不能当作交易所或申万官方行业事实。',
    `数据日期：${market.date || '未知'}`,
    `同日股票：${market.currentCount ?? '未知'}；上涨：${market.up ?? '未知'}；下跌：${market.down ?? '未知'}；平盘：${market.flat ?? '未知'}`,
    `样本成交额：${market.amount ?? '未知'}；指数：${indexText || '未提供'}`,
    `涨幅领先候选：${gainText}`,
    `成交额领先候选：${amountText}`,
    `跌幅/负反馈候选：${lossText}`,
    `跌停阈值候选：${limitDownText}`,
    `前日涨停表现（日线推导）：${priorText}`,
    `TDX行业板块聚合：${sectorText}`,
    `TDX主题板块聚合：${conceptText}`,
    `盘中封板/炸板代理（OHLC）：${intradayText}`,
    `数据源状态与新鲜度：${sourceText}`,
    supplementalData
      ? `财务/股本/指数日线/龙虎榜/融资融券统一补充快照（必须优先引用，status=missing/unavailable 时按缺失处理，不得用0替代）：${JSON.stringify(supplementalData)}`
      : '财务/股本/指数日线/龙虎榜/融资融券统一补充快照：未提供；如任务需要，必须在 cautions 中明确缺失。',
    `涨停/连板候选：${limitText}`,
    `主线名称聚类候选：${themeText}`,
    `TDX涨停文件：${Array.isArray(market.tdxLimitUpSource) ? market.tdxLimitUpSource.join('、') : '未提供'}`,
    localDataPage ? `本地数据落盘页（优先按此页读取应用数据）：${JSON.stringify(localDataPage)}` : '',
    dailyDataIndex ? `统一日线索引与降级状态（按 source_precedence 使用，不可将 degraded 当成 TDX 全历史）：${JSON.stringify({ path: DAILY_DATA_INDEX_FILE, source_precedence: dailyDataIndex.source_precedence, summary: dailyDataIndex.summary, dates: dailyDataIndex.dates })}` : '统一日线索引：未提供；如任务需要历史日线，必须在 cautions 中说明。',
    runtimePolicy ? `3003 自包含运行时政策（必须遵守）：${JSON.stringify(runtimePolicy)}` : '',
    dailyContext ? `本地每日更新上下文：${JSON.stringify(dailyContext)}` : '',
    resources ? `统一资源库上下文（所有公开研究、公式依赖、日线索引和统一清单均以此路径为准；资源状态为 DEGRADED 时必须保留边界）：${JSON.stringify(resources)}` : '',
    context ? `补充上下文：${JSON.stringify(context)}` : '',
    `如果信息不足，请在 cautions 中明确写出。${HARNESS_JSON_SCHEMA}`,
  ].join(' ');
}

function findLocalDshEntry() {
  const roots = [
    path.join(APP_ROOT, '.runtime', 'deepseek-harness'),
    path.join(APP_ROOT, 'runtime', 'deepseek-harness'),
    path.join(HARNESS_ROOT, 'runtime', 'deepseek-harness'),
    process.env.LOCALAPPDATA
      ? path.join(process.env.LOCALAPPDATA, 'pnpm', 'store', 'v11', 'links', '@deepseek-ai', 'dsh')
      : '',
    process.env.APPDATA
      ? path.join(process.env.APPDATA, 'npm', 'node_modules', '@deepseek-ai', 'dsh')
      : '',
  ].filter(Boolean);
  for (const root of roots) {
    if (!existsSync(root)) continue;
    const queue = [{ dir: root, depth: 0 }];
    while (queue.length) {
      const current = queue.shift();
      if (!current) continue;
      const entry = path.join(current.dir, 'lib', 'bin.js');
      if (existsSync(entry)) return entry;
      if (current.depth >= 6) continue;
      let children = [];
      try { children = readdirSync(current.dir, { withFileTypes: true }); } catch { continue; }
      for (const child of children) {
        if (child.isDirectory()) queue.push({ dir: path.join(current.dir, child.name), depth: current.depth + 1 });
      }
    }
  }
  return '';
}

function inspectMinuteData(tdxRoot = bridgeTdxRoot()) {
  const root = String(tdxRoot || '').trim();
  const policies = {
    source: 'external_tdx_lc5',
    mode: 'external_on_demand',
    packaged: false,
    sourceRoot: root,
    fileCount: 0,
    bytes: 0,
  };
  if (!root) return { ...policies, status: 'missing', reason: '未配置通达信目录；普通日线任务不受影响。' };
  for (const market of ['sh', 'sz', 'bj']) {
    const directory = path.join(root, 'vipdoc', market, 'fzline');
    let names = [];
    try { names = readdirSync(directory); } catch { names = []; }
    for (const name of names) {
      if (!String(name).toLowerCase().endsWith('.lc5')) continue;
      try {
        policies.fileCount += 1;
        policies.bytes += statSync(path.join(directory, name)).size;
      } catch { /* 由外部 TDX 文件状态决定是否可用 */ }
    }
  }
  return {
    ...policies,
    status: policies.fileCount > 0 ? 'available' : 'missing',
    reason: policies.fileCount > 0
      ? '原始 .lc5 不进入 EXE；仅由声明需要分钟数据的技能按股票按需读取。'
      : '未发现外部 .lc5；普通日线任务不受影响，需要分钟特征的技能标记 DEGRADED。',
  };
}

function strategyMinuteDataPreflight(skillId, tdxRoot = bridgeTdxRoot()) {
  const policy = MINUTE_DATA_POLICIES.get(skillId) || { mode: 'not_required', purpose: '普通任务不依赖 5 分钟线。' };
  const source = inspectMinuteData(tdxRoot);
  const degraded = policy.mode === 'optional_degraded' && source.status !== 'available';
  return {
    ...source,
    requirement: policy.mode,
    purpose: policy.purpose,
    result: degraded ? 'DEGRADED' : policy.mode === 'not_required' ? 'NOT_REQUIRED' : 'AVAILABLE',
  };
}

// 3002 个股页的十项技能在 3003 中使用同一批业务入口，但运行副本必须
// 固化在 resource-library/harness/skills，不能因为目录曾经存在就继续使用旧副本。
// 这样 DeepSeek Harness 直接从 3003 运行时读取技能，不回退到 3002。
const INDIVIDUAL_STOCK_SKILL_IDS = new Set([
  'baimao-score-system',
  'big-bull-analysis-scoring-system',
  'financial-roe-analysis',
  'stock-analysis',
  'stock-research-engine',
  'stock-study',
  'support-pressure-analysis-system',
  'risk-mine-clearance',
  'baimao-teacher-system',
  'technical-analysis',
  // These migrated runtimes also contain TDX readers. Sync their copies so
  // an upgrade cannot retain a stale C:\new_tdx_mock implementation.
  'golden-ignition',
  'stock-unified',
  'tdx-local-hub',
  'a-share-15d-selection',
]);

function ensureBundledSkills() {
  const source = SKILL_SOURCE;
  const destination = path.join(HARNESS_ROOT, 'skills');
  if (!existsSync(source)) return { status: 'missing', source, destination, count: 0 };
  try {
    mkdirSync(destination, { recursive: true });
    const names = readdirSync(source, { withFileTypes: true }).filter((entry) => entry.isDirectory()).map((entry) => entry.name);
    for (const name of names) {
      const target = path.join(destination, name);
      // This small, app-owned skill contains the local data-page contract.
      // Always sync it so a packaged/restarted bridge cannot keep an older
      // runtime copy after the source contract changes. Other bundled skills
      // remain immutable runtime copies.
      if (!existsSync(target) || name === 'market-data-replenishment' || INDIVIDUAL_STOCK_SKILL_IDS.has(name)) {
        cpSync(path.join(source, name), target, { recursive: true, force: true });
      }
    }
    return { status: 'ready', source, destination, count: names.length };
  } catch (error) {
    console.error(`[agent] skill bundle unavailable: ${error instanceof Error ? error.message : String(error)}`);
    return { status: 'error', source, destination, count: 0 };
  }
}

async function persistRuntimePolicy() {
  const policy = {
    schema: 'ZHANGCAI_3003_SELF_CONTAINED_RUNTIME_POLICY_V1',
    generated_at: new Date().toISOString(),
    application_root: APP_ROOT,
    data_root: DATA_ROOT,
    web_runtime: '3003 web scripts',
    report_runtime: 'DeepSeek Harness headless',
    local_skill_root: SKILL_SOURCE,
    allowed_data_roots: [...new Set([DATA_ROOT, RESOURCE_LIBRARY_ROOT, HARNESS_ROOT, RUNTIME_ROOT])],
    disabled_runtime_roots: [
      'imported-3002/',
      '3002/',
      'codex cache/runtime',
      'external report directories',
    ],
    rules: [
      '开发环境使用 application_root/app-data 兼容目录；桌面打包环境由 ZHANGCAI_DATA_DIR 指向 resource-library 内的用户可写目录。',
      '网页、数据状态、任务回执和报告只读取或写入本应用资源库。',
      'DeepSeek Harness 只接收 3003 网页脚本传入的本地结构化证据。',
      '历史兼容目录保留作人工追溯，但不参与任何生产查询、提示词、数据源清单或报告生成。',
      ...(isLocalOnlyDataPolicy()
        ? ['当前运行在严格本地模式：只允许本地数据和通达信/Mock 目录，公网行情、新闻和第三方补充入口均阻断。']
        : ['桌面版采用本地优先、按需公网补充：补充源先下载到本地资源库，保留 source/source_date/retrieved_at/sha256，并标记 degraded；TDX 不可用时允许公开源降级补齐。']),
    ],
  };
  await writeRuntimeJson(RUNTIME_POLICY_FILE, policy);
  return policy;
}

function commandFor(prompt) {
  if (PACKAGED_RUNTIME && (!process.env.DSH_ENTRY || !existsSync(process.env.DSH_ENTRY))) {
    throw new Error('内置 DeepSeek Harness 缺失，请修复主程序安装。');
  }
  const node = process.env.DSH_NODE || process.execPath;
  const entry = process.env.DSH_ENTRY || findLocalDshEntry();
  const cli = process.env.DSH_CLI;
  const pnpm = process.env.DSH_PNPM;
  const runtimePatch = path.join(APP_ROOT, 'harness-headless.patch.yml');
  const patchArgs = existsSync(runtimePatch) ? ['--patch', runtimePatch] : [];
  if (entry) return { command: node, args: [entry, '--profile', 'headless', ...patchArgs, prompt] };
  if (cli) return { command: cli, args: ['--profile', 'headless', ...patchArgs, prompt] };
  if (pnpm) {
    // The bundled Windows shim is a batch file. Resolve its Node entrypoint
    // so child_process.spawn never asks Node to parse the `@echo off` header.
    const pnpmEntry = process.platform === 'win32' && /\.cmd$/i.test(pnpm)
      ? path.resolve(path.dirname(pnpm), '..', '..', 'node', 'node_modules', 'pnpm', 'bin', 'pnpm.mjs')
      : pnpm;
    return { command: node, args: [pnpmEntry, 'dlx', '@deepseek-ai/dsh@0.1.2-rc.1', '--profile', 'headless', ...patchArgs, prompt] };
  }
  return { command: process.platform === 'win32' ? 'npx.cmd' : 'npx', args: ['@deepseek-ai/dsh@0.1.2-rc.1', '--profile', 'headless', ...patchArgs, prompt] };
}

function coerceHarnessJson(text) {
  const source = String(text || '').trim();
  const shape = (value) => {
    const row = value && typeof value === 'object' && !Array.isArray(value) ? value : {};
    return {
      ...row,
      status: typeof row.status === 'string' ? row.status : 'completed',
      summary: typeof row.summary === 'string' ? row.summary : '',
      data_date: typeof row.data_date === 'string' ? row.data_date : '',
      data_scope: typeof row.data_scope === 'string' ? row.data_scope : '',
      cautions: Array.isArray(row.cautions) ? row.cautions : [],
      findings: Array.isArray(row.findings) ? row.findings : [],
      tables: Array.isArray(row.tables) ? row.tables : [],
    };
  };
  const unwrapNestedRecord = (value) => {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return value;
    const row = value;
    if (typeof row.summary !== 'string') return row;
    let nested;
    const candidates = [
      row.summary,
      row.summary.replace(/([\]}])",(?=\s*["}])/g, '$1,'),
    ];
    for (const candidate of candidates) {
      try {
        nested = JSON.parse(candidate);
        break;
      } catch { /* try the repaired embedded JSON form */ }
    }
    if (!nested || typeof nested !== 'object' || Array.isArray(nested)) return row;
    const isReport = ['status', 'summary', 'data_date', 'data_scope', 'cautions', 'findings', 'tables']
      .some((key) => Object.prototype.hasOwnProperty.call(nested, key));
    if (!isReport) return row;
    const outerCautions = (Array.isArray(row.cautions) ? row.cautions : [])
      .filter((item) => !String(item).includes('Harness 原始输出未符合严格 JSON'));
    const nestedCautions = Array.isArray(nested.cautions) ? nested.cautions : [];
    return {
      ...row,
      ...nested,
      cautions: [...outerCautions, ...nestedCautions]
        .filter((item, index, values) => values.indexOf(item) === index),
      findings: Array.isArray(nested.findings) ? nested.findings : row.findings,
      tables: Array.isArray(nested.tables) ? nested.tables : row.tables,
    };
  };
  try {
    const value = JSON.parse(source);
    if (typeof value === 'string') {
      const decoded = JSON.parse(value);
      if (decoded && typeof decoded === 'object' && !Array.isArray(decoded)) return JSON.stringify(shape(unwrapNestedRecord(decoded)), null, 2);
    }
    if (value && typeof value === 'object' && !Array.isArray(value)) return JSON.stringify(shape(unwrapNestedRecord(value)), null, 2);
  } catch { /* try a JSON object embedded in a short model preamble */ }
  const start = source.indexOf('{');
  if (start >= 0) {
    let depth = 0;
    let quoted = false;
    let escaped = false;
    for (let index = start; index < source.length; index += 1) {
      const char = source[index];
      if (quoted) {
        if (escaped) escaped = false;
        else if (char === '\\') escaped = true;
        else if (char === '"') quoted = false;
      } else if (char === '"') quoted = true;
      else if (char === '{') depth += 1;
      else if (char === '}' && --depth === 0) {
        try {
          const value = JSON.parse(source.slice(start, index + 1));
          if (value && typeof value === 'object' && !Array.isArray(value)) return JSON.stringify(shape(unwrapNestedRecord(value)), null, 2);
        } catch { break; }
      }
    }
  }
  return JSON.stringify({
    status: 'normalized',
    summary: source,
    data_date: '',
    data_scope: '',
    cautions: ['Harness 原始输出未符合严格 JSON，已由桥接层包装为可解析结果。'],
    findings: source ? [{ title: '模型原文', text: source }] : [],
    tables: [],
  }, null, 2);
}

// Harness 只接收 DeepSeek 凭据。不要继承父进程中可能存在的其他模型
// 服务商密钥，以免未来桌面版误切换到非预期的 AI 提供方。
function harnessEnvironment(skillBundleRoot = '') {
  const configuredTdxRoot = bridgeTdxRoot();
  const childTdxRoot = configuredTdxRoot || path.join(DATA_ROOT, 'runtime', '__tdx_root_not_configured__');
  const env = {
    DEEPSEEK_API_KEY: process.env.DEEPSEEK_API_KEY,
    DSH_HOME: process.env.DSH_HOME || HARNESS_ROOT,
    DSH_SKILLS_ROOT: path.join(HARNESS_ROOT, 'skills'),
    ZHANGCAI_APP_ROOT: APP_ROOT,
    ZHANGCAI_DATA_DIR: DATA_ROOT,
    DSH_TELEMETRY_DISABLED: '1',
    ZHANGCAI_RESOURCE_LIBRARY: DATA_ROOT,
    ZHANGCAI_PACKAGED: PACKAGED_RUNTIME ? '1' : '0',
    // Keep the aliases together. The current tdx-local-hub uses TDX_ROOT,
    // while several migrated skills use ZHANGCAI_TDX_ROOT or BAIMAO_TDX_ROOT.
    // Omitting TDX_ROOT here made Harness fall back to C:\\new_tdx_mock on a
    // different computer even though the desktop bridge had the correct
    // user-selected directory.
    ZHANGCAI_TDX_ROOT: childTdxRoot,
    TDX_ROOT: childTdxRoot,
    TDX_ROOTS: childTdxRoot,
    BAIMAO_TDX_ROOT: childTdxRoot,
    ONESTOCK_STOCK_DATA_ROOT: DATA_ROOT,
    STOCK_SKILLS_ROOT: SKILL_SOURCE,
    ZHANGCAI_SKILLS_DIR: SKILL_SOURCE,
    TDX_HUB_PATH: path.join(SKILL_SOURCE, 'tdx-local-hub', 'scripts', 'tdx_hub.py'),
    STOCK_BACKTEST_RUNTIME_PATH: path.join(SKILL_SOURCE, 'stock-unified', 'scripts', 'stock_strategy_backtest.py'),
    ZHANGCAI_STRATEGY_RESULTS_DIR: path.join(DATA_ROOT, 'strategy-results'),
    ZHANGCAI_PYTHON: localPythonExecutable(),
    TDX_PYTHON: localPythonExecutable(),
    PYTHONPATH: path.join(APP_ROOT, 'scripts'),
    PYTHONIOENCODING: 'utf-8',
    ZHANGCAI_DATA_POLICY: process.env.ZHANGCAI_DATA_POLICY || 'local_first_on_demand',
  };
  if (skillBundleRoot) env.DSH_BUNDLED_SKILL_DIR = skillBundleRoot;
  const requiredSystemVariables = [
    'PATH', 'Path', 'PATHEXT', 'SystemRoot', 'SYSTEMROOT', 'WINDIR', 'ComSpec',
    'TEMP', 'TMP', 'APPDATA', 'LOCALAPPDATA', 'USERPROFILE', 'HOMEDRIVE',
    'HOMEPATH', 'PROGRAMDATA', 'ProgramFiles', 'ProgramFiles(x86)',
  ];
  for (const name of requiredSystemVariables) {
    if (process.env[name]) env[name] = process.env[name];
  }
  const inheritedPath = env.PATH || env.Path || '';
  delete env.Path;
  env.PATH = [path.dirname(process.execPath), path.dirname(localPythonExecutable()), inheritedPath].filter(Boolean).join(path.delimiter);
  return env;
}

async function prepareSkill14HarnessPackage(skillId) {
  if (!skill14Catalog().skills.some((skill) => skill?.id === skillId)) return null;
  const result = await runLocalScript(
    'skill14_data_runtime.py',
    ['prepare-harness-skill', '--skill-id', skillId],
    600000,
    24000,
  );
  let bundle;
  try { bundle = JSON.parse(result.output || '{}'); } catch { throw new Error('14 技能装载器返回了无效 JSON'); }
  if (bundle?.status !== 'available' || !bundle.harness_skill_root) {
    throw new Error(String(bundle?.error || `14 技能 ${skillId} 未能装载到 Harness`));
  }
  const root = path.resolve(String(bundle.harness_skill_root));
  const relative = path.relative(DATA_ROOT, root);
  if (!relative || relative === '..' || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
    throw new Error(`14 技能装载路径不在本应用数据目录中：${root}`);
  }
  if (!existsSync(path.join(root, 'SKILL.md'))) {
    throw new Error(`14 技能入口文件缺失：${path.join(root, 'SKILL.md')}`);
  }
  if (!bundle.skill_name) throw new Error(`14 技能缺少 Harness frontmatter name：${skillId}`);
  return { ...bundle, harness_skill_root: root };
}

function stopHarnessProcess(child) {
  return new Promise((resolve) => {
    if (!child?.pid || child.exitCode !== null) { resolve(); return; }
    if (process.platform !== 'win32') { child.kill('SIGKILL'); resolve(); return; }
    const killer = spawn('taskkill.exe', ['/PID', String(child.pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore' });
    killer.once('error', () => { child.kill(); resolve(); });
    killer.once('close', () => resolve());
  });
}

async function runHarness(prompt, skillId = '', options = {}) {
  // Resolve before entering the Promise: a thrown launcher error must reject
  // the task instead of escaping an async Promise executor and keeping its lock.
  const skill14Bundle = await prepareSkill14HarnessPackage(skillId);
  const harnessPrompt = skill14Bundle
    ? `本次必须调用已装载的 Harness 技能“${skill14Bundle.skill_name}”（掌财技能 ID：${skillId}），按其 SKILL.md 和相对 references 规则执行；不得改用同名旧副本。\n\n${prompt}`
    : prompt;
  const taskDir = path.join(HARNESS_ROOT, 'tasks');
  const taskFile = path.join(taskDir, `task-${randomUUID()}.txt`);
  const inline = options.inline === true && Buffer.byteLength(harnessPrompt, 'utf8') < 7000;
  const launchTask = inline ? harnessPrompt : `请读取并执行任务文件 ${taskFile}，最终只输出文件要求的结果。`;
  const spec = commandFor(launchTask);
  await mkdir(taskDir, { recursive: true });
  await writeFile(taskFile, harnessPrompt, 'utf8');
  return new Promise((resolve, reject) => {
    const timeoutMs = timeoutForSkill(skillId);
    const startedAt = Date.now();
    // Windows command lines are limited to roughly 8K. Deep research keeps the
    // full context in a local task file; daily validation receives an intentionally
    // compact metadata snapshot inline so it never needs to scan large raw data.
    const cleanup = () => { unlink(taskFile).catch(() => {}); };
    let child;
    try {
      child = spawn(spec.command, spec.args, {
        env: harnessEnvironment(skill14Bundle?.harness_skill_root || ''),
        cwd: DATA_ROOT,
        windowsHide: true,
      });
      if (typeof options.onProcess === 'function') options.onProcess(child);
    } catch (error) {
      cleanup();
      reject(error);
      return;
    }
    let stdout = '';
    let stderr = '';
    let timeoutError = null;
    const timer = setTimeout(() => {
      timeoutError = new Error(`DeepSeek Harness 超时（${Math.round(timeoutMs / 1000)} 秒，技能 ${skillId || '通用研究'}）`);
      void stopHarnessProcess(child).then(() => { cleanup(); reject(timeoutError); });
    }, timeoutMs);
    let outputOverflow = false;
    child.stdout.setEncoding('utf8');
    child.stderr.setEncoding('utf8');
    child.stdout.on('data', (chunk) => {
      if (stdout.length + chunk.length > MAX_OUTPUT * 4) { outputOverflow = true; return; }
      stdout += chunk;
    });
    child.stderr.on('data', (chunk) => { stderr = (stderr + chunk).slice(-16000); });
    child.on('error', (error) => { clearTimeout(timer); cleanup(); reject(error); });
    child.on('close', (code) => {
      clearTimeout(timer);
      cleanup();
      if (timeoutError) { reject(timeoutError); return; }
      if (outputOverflow) { reject(new Error('Harness 输出超过容量限制，未保存截断报告。')); return; }
      if (code !== 0) {
        const detail = (stderr || stdout).trim().slice(-2000);
        reject(new Error(`DeepSeek Harness 退出码 ${code}${detail ? `：${detail}` : ''}`));
        return;
      }
      let output = stdout.trim();
      if (!output) {
        reject(new Error('DeepSeek Harness 未返回内容'));
        return;
      }
      output = coerceHarnessJson(output);
      resolve({
        output,
        diagnostics: stderr.trim().slice(-2000),
        elapsedMs: Date.now() - startedAt,
        timeoutMs,
      });
    });
  });
}

// 网络出口偶发重置时，dsh 可能在自身退避结束后仍返回 TRANSPORT。
// 对同一任务再做两次低频重试，避免瞬时 API/代理抖动直接把报告判为失败。
async function runHarnessWithRetry(prompt, skillId = '', options = {}) {
  const executionId = String(options.executionId || randomUUID());
  const busy = reserveHarnessExecution(executionId, skillId);
  if (busy) throw createHarnessBusyError(busy);
  try {
    let lastError;
    for (let attempt = 0; attempt < 3; attempt += 1) {
      if (options.cancelled?.()) throw new Error('用户已取消 Harness 任务。');
      try {
        return await runHarness(prompt, skillId, options);
      } catch (error) {
        lastError = error;
        const message = error instanceof Error ? error.message : String(error);
        const retryable = /TRANSPORT|fetch failed|ECONNRESET|ECONNREFUSED|ETIMEDOUT|ENETUNREACH|EAI_AGAIN/i.test(message);
        if (!retryable || attempt >= 2 || options.cancelled?.()) throw error;
        const waitMs = 1500 * (attempt + 1);
        console.warn(`[agent] Harness 网络错误，${waitMs}ms 后重试 ${attempt + 1}/2：${message}`);
        await new Promise((resolve) => setTimeout(resolve, waitMs));
      }
    }
    throw lastError instanceof Error ? lastError : new Error(String(lastError || 'Harness 执行失败'));
  } finally {
    releaseHarnessExecution(executionId);
  }
}

const STOCK_RESEARCH_SKILL_IDS = new Set([
  'individual-stock-analysis-v31',
  'stock-analysis',
  'stock-study',
  'stock-research-engine',
  'technical-analysis',
  'risk-mine-clearance',
  'financial-roe-analysis',
  'baimao-score-system',
  'big-bull-analysis-scoring-system',
  'support-pressure-analysis-system',
  'baimao-teacher-system',
]);

function isStockResearchSkill(skillId) {
  return STOCK_RESEARCH_SKILL_IDS.has(String(skillId || ''));
}

function harnessProgressTemplate(skillId) {
  const stockResearch = isStockResearchSkill(skillId);
  return [
    {
      key: 'accepted',
      label: stockResearch ? 'Harness 接收高级股票研究任务' : 'Harness 接收研究任务',
      status: 'pending',
      started_at: null,
      finished_at: null,
      detail: '',
    },
    {
      key: 'tdx',
      label: stockResearch ? '完成本地 TDX 日线指标计算' : '完成本地行情与技能数据处理',
      status: 'pending',
      started_at: null,
      finished_at: null,
      detail: '',
    },
    {
      key: 'supplemental',
      label: stockResearch ? '完成财务、股本等补充数据处理' : '完成市场、板块等补充数据处理',
      status: 'pending',
      started_at: null,
      finished_at: null,
      detail: '',
    },
    {
      key: 'json',
      label: '生成最终 JSON 研究结果',
      status: 'pending',
      started_at: null,
      finished_at: null,
      detail: '',
    },
    {
      key: 'persist',
      label: '桥接写入 Harness job 和报告文件',
      status: 'pending',
      started_at: null,
      finished_at: null,
      detail: '',
    },
  ];
}

function updateHarnessJobProgress(job, key, status, detail = '') {
  if (!job || !Array.isArray(job.progress_steps)) return;
  const stage = job.progress_steps.find((item) => item.key === key);
  if (!stage) return;
  const now = Date.now();
  stage.status = status;
  if (detail) stage.detail = String(detail).slice(0, 500);
  if (status === 'running' && !stage.started_at) stage.started_at = now;
  if (['completed', 'failed', 'cancelled'].includes(status)) {
    if (!stage.started_at) stage.started_at = now;
    stage.finished_at = now;
  }
  job.current_stage = key;
  job.progress_updated_at = now;
  persistHarnessJob(job);
}

function startHarnessJob(prompt = '', skillId = '', options = {}) {
  const id = randomUUID();
  const busy = reserveHarnessExecution(id, skillId);
  if (busy) throw createHarnessBusyError(busy);
  const job = {
    id,
    status: 'running',
    skill_id: skillId || null,
    started_at: Date.now(),
    timeout_seconds: Math.round(timeoutForSkill(skillId) / 1000),
    progress_steps: harnessProgressTemplate(skillId),
  };
  harnessJobs.set(id, job);
  updateHarnessJobProgress(
    job,
    'accepted',
    'completed',
    '任务已接收，正在准备本地研究上下文。',
  );
  updateHarnessJobProgress(job, 'tdx', 'running', '正在整理本地行情与 TDX 输入。');
  let childProcess = null;
  job.cancel = () => {
    if (!childProcess?.pid) return false;
    void stopHarnessProcess(childProcess);
    return true;
  };
  const updateProgress = (key, status, detail = '') => {
    const current = harnessJobs.get(id);
    if (current) updateHarnessJobProgress(current, key, status, detail);
  };
  const cancelled = () => Boolean(harnessJobs.get(id)?.cancel_requested);
  void (async () => {
    let finalPrompt = prompt;
    try {
      if (typeof options.prepare === 'function') {
        finalPrompt = await options.prepare({
          job,
          updateProgress,
          cancelled,
        });
      } else {
        updateProgress('tdx', 'completed', '本地研究输入已准备完成。');
        updateProgress('supplemental', 'completed', '本技能无需额外个股补充快照。');
      }
      if (cancelled()) throw new Error('用户已取消 Harness 任务。');
      updateProgress('json', 'running', '正在调用 DeepSeek Harness，生成严格 JSON 研究结果。');
      const result = await runHarnessWithRetry(finalPrompt, skillId, {
        executionId: id,
        cancelled,
        onProcess: (child) => { childProcess = child; },
      });
      const current = harnessJobs.get(id);
      if (!current) return;
      if (cancelled()) throw new Error('用户已取消 Harness 任务。');
      updateProgress('json', 'completed', '最终 JSON 研究结果已生成。');
      updateProgress('persist', 'running', '正在写入任务记录和报告文件。');
      const reportPath = await persistHarnessReport({
        skillId,
        output: result.output,
        diagnostics: result.diagnostics,
        task: finalPrompt,
        jobId: id,
      });
      const latest = harnessJobs.get(id);
      if (!latest) return;
      latest.report_path = reportPath;
      updateProgress('persist', 'completed', 'Harness job 和研究报告已落盘。');
      Object.assign(latest, {
        status: 'completed',
        output: result.output,
        diagnostics: result.diagnostics,
        elapsed_ms: result.elapsedMs,
        timeout_seconds: Math.round(result.timeoutMs / 1000),
        completed_at: Date.now(),
      });
      persistHarnessJob(latest);
    } catch (error) {
      const current = harnessJobs.get(id);
      releaseHarnessExecution(id);
      if (!current) return;
      const status = current.cancel_requested ? 'cancelled' : 'failed';
      const message = current.cancel_requested
        ? '用户已取消 Harness 任务。'
        : (error instanceof Error ? error.message : String(error));
      const activeStage = current.progress_steps?.find((item) => item.status === 'running');
      if (activeStage) updateHarnessJobProgress(current, activeStage.key, status, message);
      Object.assign(current, {
        status,
        error: message,
        elapsed_ms: Date.now() - current.started_at,
        completed_at: Date.now(),
      });
      persistHarnessJob(current);
    }
  })();
  return job;
}

async function runPublicMarketRefresh() {
  if (isLocalOnlyDataPolicy()) {
    throw new Error('当前运行在严格本地模式，已阻断公网行情补充。');
  }
  const date = localTradeDate();
  await runLocalScript('public_market_sync.py', ['--date', date], 90000);
  const snapshot = readJson(path.join(DATA_ROOT, 'public', 'latest.json'));
  const sources = snapshot?.sources || {};
  const pool = sources?.eastmoneyLimitUp?.data?.data?.pool || sources?.akshareLimitUpPool?.data?.records;
  if (!Array.isArray(pool) || pool.length === 0) throw new Error('公开行情源未返回当日涨幅榜候选');
  const kpi = sources?.lianban?.data?.kpi || {};
  const stocks = pool.map((item) => {
    const pct = Number(item.zdp ?? item['涨跌幅'] ?? 0);
    const close = item.p != null ? Number(item.p) / 1000 : Number(item['最新价'] ?? item['价格'] ?? 0);
    return {
      code: String(item.c || item['代码'] || ''), name: String(item.n || item['名称'] || '').replace(/\s+/g, ''), market: Number(item.m) === 1 ? 'sh' : Number(item.m) === 2 ? 'bj' : String(item['代码'] || '').startsWith('6') ? 'sh' : 'sz',
      date: snapshot.date || date.replace(/-/g, ''), open: close, high: close, low: close, close,
      previousClose: close && Number.isFinite(pct) ? close / (1 + pct / 100) : close,
      pct: Number(pct.toFixed(2)), amount: Number(item.amount ?? item['封板资金'] ?? 0), volume: Number(item.vol ?? item['成交额'] ?? 0), realtime: true,
      limitPct: pct >= 19 ? 20 : 10, limitStreak: Number(item.lbc ?? item['连板数'] ?? item.zttj?.ct ?? 0), industryName: String(item.hybk || item['所属行业'] || ''),
    };
  }).sort((a, b) => b.pct - a.pct || b.amount - a.amount);
  const up = Number(kpi.adv || 0), down = Number(kpi.dec || 0), flat = Math.max(0, 5200 - up - down);
  return {
    status: 'ok', source: '东方财富涨停池 + 连板网公开快照', fetchedAt: snapshot.fetchedAt, tradeDate: snapshot.date || date,
    stocks, replaceLeaderboard: true,
    marketSummary: { currentCount: up + down + flat, up, down, flat, amount: stocks.reduce((total, stock) => total + stock.amount, 0), bins: [0, 0, down, flat, up, 0, Number(kpi.limit_up || stocks.length)] },
    scope: `已拉取 ${stocks.length} 条当日公开涨幅榜候选；市场广度来自连板网同日快照`,
  };
}

// 行情刷新结果必须跨浏览器刷新保留。lib/market.json 是随代码发布的
// 基线快照，不能把运行时 TQ 数据只放在前端内存里，否则页面重载会退回
// 到基线日期。运行时快照单独落到 data/runtime，既不污染源码，也方便
// exe 安装后继续复用最近一次成功数据。
function queueMarketSnapshotWrite(task) {
  const next = marketSnapshotWriteChain.then(task, task);
  marketSnapshotWriteChain = next.catch(() => undefined);
  return next;
}

function timestampOf(value) {
  const timestamp = Date.parse(String(value || ''));
  return Number.isFinite(timestamp) ? timestamp : 0;
}

async function persistMarketSnapshot(scope, result) {
  if (!result || result.status !== 'ok') return;
  return queueMarketSnapshotWrite(async () => {
    const baseline = readJson(path.join(APP_ROOT, 'lib', 'market.json')) || {};
    const previous = readJson(MARKET_LATEST_FILE) || {};
    const merged = { ...baseline, ...previous };
    const incomingFetchedAt = result.fetchedAt || new Date().toISOString();
    const incomingTimestamp = timestampOf(incomingFetchedAt);

    if (Array.isArray(result.indices) && result.indices.length) {
      const previousIndicesTimestamp = timestampOf(previous.indicesLatestDataAt || previous.indicesFetchedAt);
      // A slow retry must not roll the index cards back to an older quote.
      if (incomingTimestamp >= previousIndicesTimestamp || !previousIndicesTimestamp) {
        const baselineIndices = Array.isArray(baseline.indices) ? baseline.indices : [];
        const previousIndices = Array.isArray(previous.indices) ? previous.indices : [];
        const baselineByCode = new Map(baselineIndices.map((row) => [row.code, row]));
        const previousByCode = new Map(previousIndices.map((row) => [row.code, row]));
        merged.indices = result.indices.map((row) => {
          const previousRow = previousByCode.get(row.code);
          const baselineRow = baselineByCode.get(row.code);
          const existing = previousRow || baselineRow;
          return existing
            ? { ...existing, ...row, history: Array.isArray(row.history) && row.history.length ? row.history : (Array.isArray(existing.history) && existing.history.length ? existing.history : baselineRow?.history) }
            : row;
        });
        merged.indicesSource = result.source || previous.indicesSource || '';
        merged.indicesQuality = result.quality || result.dataQuality || 'primary';
        merged.indicesFallback = result.fallback === true || result.quality === 'degraded';
        merged.indicesQuoteMode = result.quoteMode || (merged.indicesFallback ? 'public_delayed' : 'tdx_realtime');
        merged.indicesLatestDataAt = incomingFetchedAt;
        merged.indicesFetchedAt = incomingFetchedAt;
      }
    }

    if (scope === 'market') {
      const isFallback = result.fallback === true || result.quality === 'degraded';
      const allStocks = Array.isArray(result.allStocks) ? result.allStocks : [];
      const previousMarketTimestamp = timestampOf(previous.marketLatestDataAt || previous.marketFetchedAt);
      // A valid local market snapshot must be a full same-day universe.  A
      // public fallback is intentionally compact and is allowed to replace
      // the homepage payload, but it must clear the old allStocks universe.
      const validLocal = !isFallback && allStocks.length >= 3000;
      const validFallback = isFallback && Array.isArray(result.stocks) && result.stocks.length > 0;
      if ((validLocal || validFallback) && (incomingTimestamp >= previousMarketTimestamp || !previousMarketTimestamp)) {
        merged.stocks = Array.isArray(result.stocks) ? result.stocks : allStocks;
        merged.allStocks = isFallback ? [] : allStocks;
        merged.date = result.tradeDate || result.date || merged.date;
        merged.tradeDate = result.tradeDate || result.date || merged.tradeDate;
        if (result.marketSummary) Object.assign(merged, result.marketSummary);
        merged.marketLatestDataAt = incomingFetchedAt;
        merged.marketFetchedAt = incomingFetchedAt;
        merged.fallback = isFallback;
         merged.quality = result.quality || (isFallback ? 'degraded' : 'primary');
         merged.dataQuality = result.dataQuality || result.quality || (isFallback ? 'degraded' : 'primary');
         merged.degraded = result.degraded === true || isFallback;
         merged.requestedTradeDate = result.requestedTradeDate || merged.requestedTradeDate || '';
         merged.degradationReason = result.degradationReason || merged.degradationReason || '';
        merged.provider = result.provider || merged.provider;
        merged.fallbackReason = result.fallbackReason || merged.fallbackReason || '';
      }
    } else if (scope === 'watchlist' && Array.isArray(result.stocks) && result.stocks.length) {
      const existing = new Map((merged.allStocks || merged.stocks || []).map((row) => [row.code, row]));
      for (const row of result.stocks) existing.set(row.code, { ...existing.get(row.code), ...row });
      merged.allStocks = [...existing.values()];
      merged.stocks = merged.allStocks;
    }

    merged.dataSources = { ...(merged.dataSources || {}), runtimeMarket: result.source || 'Tongdaxin TQ realtime snapshot' };
    merged.status = 'ok';
    merged.runtimeFetchedAt = new Date().toISOString();
    merged.runtimeScope = scope;
    merged.latestDataAt = [merged.marketLatestDataAt, merged.indicesLatestDataAt].map(timestampOf).reduce((latest, value) => Math.max(latest, value), 0)
      ? new Date(Math.max(timestampOf(merged.marketLatestDataAt), timestampOf(merged.indicesLatestDataAt))).toISOString()
      : incomingFetchedAt;
    merged.persistedAt = new Date().toISOString();
    await writeRuntimeJson(MARKET_LATEST_FILE, merged);
  });
}

async function persistPublicResearchFallback(result, reason = '') {
  if (!result || result.fallback !== true) return null;
  const fallbackRoot = path.join(DATA_ROOT, 'evidence', 'public');
  const fallbackPath = path.join(fallbackRoot, 'fallback-latest.json');
  const primaryPath = path.join(fallbackRoot, 'latest.json');
  const current = readJson(primaryPath) || {};
  const currentIsReal = current && typeof current === 'object' && !current.fallback_kind
    && Number(current.same_day_record_count || current.sameDayRecordCount || 0) > 0;
  const rows = [
    ...(Array.isArray(result.stocks) ? result.stocks : []),
    ...(Array.isArray(result.indices) ? result.indices : []),
  ].slice(0, 200);
  const source = ['eastmoney', 'tencent', 'public_market'].includes(String(result.provider || '').toLowerCase())
    ? 'public_market'
    : 'local_market';
  const tradeDate = String(result.tradeDate || result.dataDate || '').replace(/^(\d{4})(\d{2})(\d{2})$/, '$1-$2-$3');
  const fetchedAt = result.fetchedAt || new Date().toISOString();
  const record = {
    provider: source,
    source: result.source || source,
    title: source === 'public_market' ? 'Public market fallback snapshot' : 'Local daily close fallback snapshot',
    content: JSON.stringify({
      scope: result.dataScope || result.scope || '',
      tradeDate,
      rowCount: rows.length,
      rows: rows.slice(0, 20),
      marketSummary: result.marketSummary || {},
    }),
    source_timestamp: fetchedAt,
    source_date: tradeDate,
    kind: 'market_snapshot',
    degraded: true,
    fallback_reason: String(result.fallbackReason || reason || '').slice(0, 500),
    record_count: rows.length,
  };
  const payload = {
    schema: 'ZHANGCAI_PUBLIC_RESEARCH_FALLBACK_V1',
    status: 'degraded',
    fallback_kind: source === 'public_market' ? 'public_market_snapshot' : 'local_market_snapshot',
    archived_at: new Date().toISOString(),
    source_date: tradeDate,
    same_day_record_count: 1,
    provider_counts: { [source]: 1 },
    historical_fallback: false,
    data_boundary: source === 'public_market'
      ? 'Market-only public evidence. No news, announcement, sentiment or same-day article is inferred.'
      : 'Local daily close only. This is not public research, news or intraday evidence.',
    records: [record],
    snapshot: { schema: 'ZHANGCAI_PUBLIC_RESEARCH_FALLBACK_SNAPSHOT_V1', date: tradeDate, source_date: tradeDate, fetchedAt, records: [record] },
  };
  await writeRuntimeJson(fallbackPath, payload);
  if (!currentIsReal) await writeRuntimeJson(primaryPath, payload);
  return { path: dataRelativePath(fallbackPath), fallbackKind: payload.fallback_kind, sourceDate: tradeDate };
}

const PUBLIC_INDEX_QUOTES = [
  { key: 'sh000001', code: '000001', market: 'SH', secid: '1.000001', name: '上证指数' },
  { key: 'sz399001', code: '399001', market: 'SZ', secid: '0.399001', name: '深证成指' },
  { key: 'sz399006', code: '399006', market: 'SZ', secid: '0.399006', name: '创业板指' },
  { key: 'sh000688', code: '000688', market: 'SH', secid: '1.000688', name: '科创50' },
  { key: 'sh000016', code: '000016', market: 'SH', secid: '1.000016', name: '上证50' },
  { key: 'bj899050', code: '899050', market: 'BJ', secid: '0.899050', name: '北证50' },
];

function compactMarketDate(value) {
  return String(value || '').replace(/\D/g, '').slice(0, 8);
}

function publicTradeDateKey(now = new Date()) {
  // Eastmoney's quote payload does not expose a reliable trade date. Use the
  // latest Shanghai weekday visible to the quote service and keep the result
  // explicitly marked as a delayed public fallback.
  const shifted = new Date(now.getTime() + 8 * 60 * 60 * 1000);
  const beforeOpen = shifted.getUTCHours() < 9 || (shifted.getUTCHours() === 9 && shifted.getUTCMinutes() < 30);
  if (beforeOpen || shifted.getUTCDay() === 0 || shifted.getUTCDay() === 6) shifted.setUTCDate(shifted.getUTCDate() - 1);
  while (shifted.getUTCDay() === 0 || shifted.getUTCDay() === 6) shifted.setUTCDate(shifted.getUTCDate() - 1);
  return `${shifted.getUTCFullYear()}${String(shifted.getUTCMonth() + 1).padStart(2, '0')}${String(shifted.getUTCDate()).padStart(2, '0')}`;
}

function numericMarketField(value, fallback = 0) {
  const number = Number(String(value ?? '').replace(/,/g, ''));
  return Number.isFinite(number) ? number : fallback;
}

function localTdxHistory(code, market, limit = 60) {
  const root = bridgeTdxRoot();
  if (!root) return [];
  const normalized = normalizeHistorySymbol(`${code}.${market}`);
  if (!normalized) return [];
  const marketDir = normalized.market.toLowerCase();
  const file = path.join(path.resolve(root), 'vipdoc', marketDir, 'lday', `${marketDir}${normalized.code}.day`);
  try {
    if (!existsSync(file)) return [];
    return readTdxDayHistory(file, limit).map((row) => ({ ...row, date: compactMarketDate(row.date) }));
  } catch {
    return [];
  }
}

function appendMarketHistory(history, latest, limit = 60) {
  const bars = new Map();
  for (const row of Array.isArray(history) ? history : []) {
    const date = compactMarketDate(row?.date);
    if (date && numericMarketField(row?.close) > 0) bars.set(date, { ...row, date });
  }
  const latestDate = compactMarketDate(latest?.date);
  if (latestDate && numericMarketField(latest?.close) > 0) {
    bars.set(latestDate, {
      date: latestDate,
      open: numericMarketField(latest.open), high: numericMarketField(latest.high),
      low: numericMarketField(latest.low), close: numericMarketField(latest.close),
      amount: numericMarketField(latest.amount), volume: numericMarketField(latest.volume),
    });
  }
  return [...bars.values()].sort((a, b) => a.date.localeCompare(b.date)).slice(-limit);
}

function localTdxDailyProjection(row, historyLimit = 60) {
  const normalized = normalizeHistorySymbol(`${row?.code || ''}.${String(row?.market || '')}`);
  if (!normalized) return row;
  const history = localTdxHistory(normalized.code, normalized.market, historyLimit);
  if (!history.length) return row;
  const latest = history.at(-1);
  const previous = history.at(-2);
  const previousClose = numericMarketField(previous?.close, numericMarketField(row?.previousClose, numericMarketField(latest.close)));
  return {
    ...row,
    ...latest,
    code: String(row?.code || normalized.code),
    market: String(row?.market || normalized.market.toLowerCase()).toLowerCase(),
    date: compactMarketDate(latest.date),
    previousClose,
    pct: previousClose > 0 ? Number((((numericMarketField(latest.close) / previousClose) - 1) * 100).toFixed(2)) : 0,
    history,
    realtime: false,
    quoteMode: 'local_daily_close',
    latestDataAt: new Date().toISOString(),
    source: '通达信本地最近交易日收盘数据（降级）',
    quality: 'degraded',
  };
}

function localTdxQuoteProjection(code, market, seed = {}) {
  const normalized = normalizeHistorySymbol(`${code}.${market}`);
  if (!normalized) return null;
  const history = localTdxHistory(normalized.code, normalized.market, 60);
  if (!history.length) return null;
  const latest = history.at(-1);
  const previous = history.at(-2);
  const close = numericMarketField(latest?.close);
  if (!(close > 0)) return null;
  const previousClose = numericMarketField(previous?.close, numericMarketField(seed.previousClose, close));
  return {
    ...seed,
    ...latest,
    code: normalized.code,
    market: normalized.market.toLowerCase(),
    name: String(seed.name || normalized.code),
    date: compactMarketDate(latest.date),
    previousClose,
    pct: previousClose > 0 ? Number((((close / previousClose) - 1) * 100).toFixed(2)) : 0,
    history,
    realtime: false,
    quoteMode: 'local_daily_close',
    latestDataAt: new Date().toISOString(),
    source: '通达信本地最近交易日收盘数据（降级）',
    quality: 'degraded',
  };
}

function publicQueryString(params) {
  return Object.entries(params).map(([key, value]) => (
    `${encodeURIComponent(key)}=${encodeURIComponent(String(value)).replace(/%2C/gi, ',').replace(/%2E/gi, '.')}`
  )).join('&');
}

function publicJsonViaPowerShell(endpoint, params, timeoutMs = 12000) {
  return new Promise((resolve, reject) => {
    const target = `${endpoint}?${publicQueryString(params)}`;
    const escapedTarget = target.replace(/'/g, "''");
    const timeoutSeconds = Math.max(3, Math.ceil(timeoutMs / 1000));
    const script = [
      "$ErrorActionPreference='Stop'",
      "$ProgressPreference='SilentlyContinue'",
      `$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec ${timeoutSeconds} -Uri '${escapedTarget}' -Headers @{'User-Agent'='Mozilla/5.0';'Referer'='https://quote.eastmoney.com/';'Accept'='application/json,text/plain,*/*'}`,
      '$b=$r.RawContentStream.ToArray()',
      '$o=[Console]::OpenStandardOutput()',
      '$o.Write($b,0,$b.Length)',
      '$o.Flush()',
    ].join(';');
    const encoded = Buffer.from(script, 'utf16le').toString('base64');
    const child = spawn('powershell.exe', ['-NoProfile', '-NonInteractive', '-EncodedCommand', encoded], { windowsHide: true });
    const stdout = [];
    let stderr = '';
    let finished = false;
    const finish = (error, value) => {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      if (error) reject(error); else resolve(value);
    };
    const timer = setTimeout(() => {
      if (child.pid) spawn('taskkill', ['/pid', String(child.pid), '/t', '/f'], { windowsHide: true });
      finish(new Error('公开行情请求超时'));
    }, timeoutMs + 1500);
    child.stdout.on('data', (chunk) => stdout.push(Buffer.from(chunk)));
    child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
    child.on('error', (error) => finish(error));
    child.on('close', (code) => {
      if (finished) return;
      if (code !== 0) {
        finish(new Error(`公开行情请求失败${stderr.trim() ? `：${stderr.trim().slice(0, 180)}` : ''}`));
        return;
      }
      try { finish(null, JSON.parse(Buffer.concat(stdout).toString('utf8').replace(/^\uFEFF/, ''))); }
      catch { finish(new Error('公开行情返回格式无效')); }
    });
  });
}

function publicTextViaPowerShell(target, timeoutMs = 10000) {
  return new Promise((resolve, reject) => {
    const escapedTarget = String(target).replace(/'/g, "''");
    const timeoutSeconds = Math.max(3, Math.ceil(timeoutMs / 1000));
    const script = [
      "$ErrorActionPreference='Stop'",
      "$ProgressPreference='SilentlyContinue'",
      `$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec ${timeoutSeconds} -Uri '${escapedTarget}' -Headers @{'User-Agent'='Mozilla/5.0';'Referer'='https://finance.qq.com/';'Accept'='*/*'}`,
      '$b=[Text.Encoding]::UTF8.GetBytes([string]$r.Content)',
      '$o=[Console]::OpenStandardOutput()',
      '$o.Write($b,0,$b.Length)',
      '$o.Flush()',
    ].join(';');
    const encoded = Buffer.from(script, 'utf16le').toString('base64');
    const child = spawn('powershell.exe', ['-NoProfile', '-NonInteractive', '-EncodedCommand', encoded], { windowsHide: true });
    const stdout = [];
    let stderr = '';
    let finished = false;
    const finish = (error, value) => {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      if (error) reject(error); else resolve(value);
    };
    const timer = setTimeout(() => {
      if (child.pid) spawn('taskkill', ['/pid', String(child.pid), '/t', '/f'], { windowsHide: true });
      finish(new Error('腾讯公开行情请求超时'));
    }, timeoutMs + 1500);
    child.stdout.on('data', (chunk) => stdout.push(Buffer.from(chunk)));
    child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
    child.on('error', (error) => finish(error));
    child.on('close', (code) => {
      if (finished) return;
      if (code !== 0) {
        finish(new Error(`腾讯公开行情请求失败${stderr.trim() ? `：${stderr.trim().slice(0, 180)}` : ''}`));
        return;
      }
      finish(null, Buffer.concat(stdout).toString('utf8').replace(/^\uFEFF/, ''));
    });
  });
}

function parseTencentQuotes(text) {
  const rows = [];
  for (const match of String(text || '').matchAll(/v_([^=]+)="([^"]*)";?/g)) {
    const fields = match[2].split('~');
    if (fields.length < 35) continue;
    const amountParts = String(fields[35] || '').split('/');
    const stamp = String(fields[30] || '');
    const latestDataAt = /^\d{14}$/.test(stamp)
      ? `${stamp.slice(0, 4)}-${stamp.slice(4, 6)}-${stamp.slice(6, 8)}T${stamp.slice(8, 10)}:${stamp.slice(10, 12)}:${stamp.slice(12, 14)}+08:00`
      : new Date().toISOString();
    rows.push({
      key: match[1], name: fields[1], code: fields[2], close: numericMarketField(fields[3]),
      previousClose: numericMarketField(fields[4]), open: numericMarketField(fields[5]),
      volume: numericMarketField(fields[6]), date: compactMarketDate(stamp) || publicTradeDateKey(),
      pct: numericMarketField(fields[32]), high: numericMarketField(fields[33]), low: numericMarketField(fields[34]),
      amount: numericMarketField(amountParts[2], numericMarketField(fields[37]) * 10000), latestDataAt,
    });
  }
  return rows;
}

function marketSeedRows() {
  const snapshot = readJson(MARKET_LATEST_FILE) || readJson(path.join(APP_ROOT, 'lib', 'market.json')) || {};
  return {
    snapshot,
    stocks: Array.isArray(snapshot.allStocks) && snapshot.allStocks.length
      ? snapshot.allStocks
      : Array.isArray(snapshot.stocks) ? snapshot.stocks : [],
    indices: Array.isArray(snapshot.indices) ? snapshot.indices : [],
  };
}

function publicFallbackEnvelope(scope, rows, reason, source) {
  const fetchedAt = new Date().toISOString();
  const tradeDate = rows.map((row) => compactMarketDate(row?.date)).filter(Boolean).sort().at(-1) || publicTradeDateKey();
  return {
    status: 'ok', source, provider: source.includes('腾讯') ? 'tencent' : 'eastmoney', quality: 'degraded', fallback: true,
    fallbackReason: String(reason || '').slice(0, 500), fetchedAt, latestDataAt: fetchedAt,
    tradeDate, quoteMode: 'public_delayed', dataScope: scope,
    indices: scope === 'indices' ? rows : [],
    stocks: scope === 'watchlist' ? rows : [],
    allStocks: [], replaceLeaderboard: scope === 'watchlist',
    scope: `通达信实时行情暂不可用，已切换公开行情延时降级，数据日期 ${tradeDate}`,
    dataSources: {
      primary: 'TongdaXin/TQ', fallback: source,
      fallbackQuality: 'DEGRADED', fallbackReason: String(reason || '').slice(0, 500),
    },
  };
}

async function eastmoneyPublicWatchlistRefresh(codes, reason) {
  const requested = [...new Set(String(codes || '').split(',').map((value) => value.trim().split('.', 1)[0]).filter((value) => /^\d{6}$/.test(value)))];
  if (requested.length !== 1) throw new Error('快速公开行情仅处理单只股票');
  const code = requested[0];
  const normalized = normalizeHistorySymbol(code);
  if (!normalized) throw new Error('股票代码无效');
  const { stocks } = marketSeedRows();
  const old = stocks.find((row) => String(row?.code || '') === code) || {};
  const secid = `${normalized.market === 'SH' ? '1' : '0'}.${code}`;
  const body = await publicJsonViaPowerShell('https://push2delay.eastmoney.com/api/qt/stock/get', {
    secid, fields: 'f43,f44,f45,f46,f47,f48,f57,f58,f59,f60,f170',
  }, 10000);
  const data = body?.data;
  if (body?.rc !== 0 || !data || typeof data !== 'object') throw new Error('公开个股行情为空');
  const decimals = Math.max(0, Math.min(4, Math.trunc(numericMarketField(data.f59, 2))));
  const scale = 10 ** decimals;
  const close = numericMarketField(data.f43) / scale;
  const previousClose = numericMarketField(data.f60) / scale;
  if (!(close > 0)) throw new Error('公开个股行情没有有效价格');
  const tradeDate = publicTradeDateKey();
  const row = {
    ...old,
    code,
    market: normalized.market.toLowerCase(),
    name: String(data.f58 || old.name || code).replace(/\s+/g, ''),
    date: tradeDate,
    open: numericMarketField(data.f46) / scale || close,
    high: numericMarketField(data.f44) / scale || close,
    low: numericMarketField(data.f45) / scale || close,
    close,
    previousClose: previousClose > 0 ? previousClose : numericMarketField(old.previousClose, close),
    pct: Number((numericMarketField(data.f170) / 100).toFixed(2)),
    amount: numericMarketField(data.f48),
    volume: numericMarketField(data.f47),
    realtime: false,
    quoteMode: 'public_delayed',
    latestDataAt: new Date().toISOString(),
    source: '东方财富公开行情（延时降级）',
    quality: 'degraded',
  };
  const localHistory = localTdxHistory(code, normalized.market, 60);
  row.history = appendMarketHistory(localHistory.length ? localHistory : old.history, row);
  return publicFallbackEnvelope('watchlist', [row], reason, '东方财富公开个股行情（延时降级）');
}

async function eastmoneyPublicIndicesRefresh(reason) {
  const body = await publicJsonViaPowerShell('https://push2delay.eastmoney.com/api/qt/ulist.np/get', {
    fltt: '2', fields: 'f2,f3,f4,f5,f6,f12,f14,f15,f16,f17,f18',
    secids: PUBLIC_INDEX_QUOTES.map((item) => item.secid).join(','),
  }, 12000);
  const items = body?.data?.diff;
  if (body?.rc !== 0 || !Array.isArray(items)) throw new Error('公开指数行情为空');
  const { indices } = marketSeedRows();
  const oldByCode = new Map(indices.map((row) => [String(row?.code || ''), row]));
  const tradeDate = publicTradeDateKey();
  const rows = [];
  for (const item of items) {
    const config = PUBLIC_INDEX_QUOTES.find((entry) => entry.code === String(item?.f12 || '').padStart(6, '0'));
    if (!config) continue;
    const close = numericMarketField(item.f2);
    if (!(close > 0)) continue;
    const old = oldByCode.get(config.key) || {};
    const previousClose = numericMarketField(item.f18, numericMarketField(old.previousClose, close));
    const row = {
      ...old,
      code: config.key,
      market: config.market.toLowerCase(),
      name: String(item.f14 || old.name || config.name),
      date: tradeDate,
      open: numericMarketField(item.f17, close), high: numericMarketField(item.f15, close),
      low: numericMarketField(item.f16, close), close, previousClose,
      pct: Number(numericMarketField(item.f3, previousClose > 0 ? ((close / previousClose) - 1) * 100 : 0).toFixed(2)),
      amount: numericMarketField(item.f6), volume: numericMarketField(item.f5),
      realtime: false, quoteMode: 'public_delayed', latestDataAt: new Date().toISOString(),
      source: '东方财富公开指数行情（延时降级）', quality: 'degraded',
    };
    const localHistory = localTdxHistory(config.code, config.market, 60);
    row.historySource = localHistory.length ? '通达信本地日线历史 + 公开最新行情' : '页面历史 + 公开最新行情';
    row.history = appendMarketHistory(localHistory.length ? localHistory : old.history, row);
    rows.push(row);
  }
  if (rows.length < 3) throw new Error('公开指数有效数量不足');
  return publicFallbackEnvelope('indices', rows, reason, '东方财富公开指数行情（延时降级）');
}

async function tencentPublicWatchlistRefresh(codes, reason) {
  const requested = [...new Set(String(codes || '').split(',').map((value) => value.trim().split('.', 1)[0]).filter((value) => /^\d{6}$/.test(value)))];
  if (requested.length !== 1) throw new Error('腾讯快速公开行情仅处理单只股票');
  const code = requested[0];
  const normalized = normalizeHistorySymbol(code);
  if (!normalized) throw new Error('股票代码无效');
  const prefix = normalized.market === 'SH' ? 'sh' : normalized.market === 'BJ' ? 'bj' : 'sz';
  const text = await publicTextViaPowerShell(`https://qt.gtimg.cn/q=${prefix}${code}`, 8000);
  const quote = parseTencentQuotes(text).find((row) => row.code === code);
  if (!quote || !(quote.close > 0)) throw new Error('腾讯公开个股行情为空');
  const { stocks } = marketSeedRows();
  const old = stocks.find((row) => String(row?.code || '') === code) || {};
  const row = {
    ...old,
    ...quote,
    code,
    market: normalized.market.toLowerCase(),
    name: String(quote.name || old.name || code).replace(/\s+/g, ''),
    realtime: false,
    quoteMode: 'public_delayed',
    source: '腾讯公开行情（延时降级）',
    quality: 'degraded',
  };
  const localHistory = localTdxHistory(code, normalized.market, 60);
  row.history = appendMarketHistory(localHistory.length ? localHistory : old.history, row);
  return publicFallbackEnvelope('watchlist', [row], reason, '腾讯公开个股行情（延时降级）');
}

async function tencentPublicIndicesRefresh(reason) {
  const target = `https://qt.gtimg.cn/q=${PUBLIC_INDEX_QUOTES.map((item) => `${item.market.toLowerCase()}${item.code}`).join(',')}`;
  const text = await publicTextViaPowerShell(target, 10000);
  const quotes = parseTencentQuotes(text);
  const { indices } = marketSeedRows();
  const oldByCode = new Map(indices.map((row) => [String(row?.code || ''), row]));
  const rows = [];
  for (const config of PUBLIC_INDEX_QUOTES) {
    const quote = quotes.find((item) => item.key.toLowerCase() === `${config.market.toLowerCase()}${config.code}`);
    if (!quote || !(quote.close > 0)) continue;
    const old = oldByCode.get(config.key) || {};
    const row = {
      ...old,
      ...quote,
      code: config.key,
      market: config.market.toLowerCase(),
      name: quote.name || old.name || config.name,
      realtime: false,
      quoteMode: 'public_delayed',
      source: '腾讯公开指数行情（延时降级）',
      quality: 'degraded',
    };
    const localHistory = localTdxHistory(config.code, config.market, 60);
    row.historySource = localHistory.length ? '通达信本地日线历史 + 公开最新行情' : '页面历史 + 公开最新行情';
    row.history = appendMarketHistory(localHistory.length ? localHistory : old.history, row);
    rows.push(row);
  }
  if (rows.length < 3) throw new Error('腾讯公开指数有效数量不足');
  return publicFallbackEnvelope('indices', rows, reason, '腾讯公开指数行情（延时降级）');
}

async function fastPublicWatchlistRefresh(codes, reason) {
  try { return await eastmoneyPublicWatchlistRefresh(codes, reason); }
  catch { return tencentPublicWatchlistRefresh(codes, reason); }
}

async function fastPublicIndicesRefresh(reason) {
  try { return await eastmoneyPublicIndicesRefresh(reason); }
  catch { return tencentPublicIndicesRefresh(reason); }
}

async function fastPublicMarketRefresh(scope, codes, reason) {
  if (scope === 'watchlist') return fastPublicWatchlistRefresh(codes, reason);
  if (scope === 'indices') return fastPublicIndicesRefresh(reason);
  throw new Error('该范围不使用快速公开行情');
}

function localMarketFallback(scope, codes, reason) {
  const snapshot = readJson(MARKET_LATEST_FILE) || readJson(path.join(APP_ROOT, 'lib', 'market.json')) || {};
  const requested = new Set(String(codes || '').split(',').map((value) => value.trim().split('.', 1)[0]).filter(Boolean));
  const sourceRows = Array.isArray(snapshot.allStocks) && snapshot.allStocks.length
    ? snapshot.allStocks
    : Array.isArray(snapshot.stocks) ? snapshot.stocks : [];
  const selectedRows = scope === 'watchlist'
    ? sourceRows.filter((row) => requested.has(String(row?.code || '')))
    : sourceRows;
  const rows = selectedRows.map((row) => localTdxDailyProjection(row));
  if (scope === 'watchlist') {
    for (const code of requested) {
      if (rows.some((row) => String(row?.code || '') === code)) continue;
      const normalized = normalizeHistorySymbol(code);
      if (!normalized) continue;
      const quote = localTdxQuoteProjection(code, normalized.market);
      if (quote) rows.push(quote);
    }
  }
  const indices = (Array.isArray(snapshot.indices) ? snapshot.indices : []).map((row) => {
    const config = PUBLIC_INDEX_QUOTES.find((item) => item.key === String(row?.code || ''));
    return config
      ? localTdxDailyProjection({ ...row, code: config.code, market: config.market })
      : localTdxDailyProjection(row);
  }).map((row) => {
    const config = PUBLIC_INDEX_QUOTES.find((item) => item.code === String(row?.code || ''));
    return config ? { ...row, code: config.key, market: config.market.toLowerCase(), name: row.name || config.name } : row;
  });
  if (scope === 'indices' && !indices.length) return null;
  if (scope !== 'indices' && !rows.length) return null;
  const fetchedAt = new Date().toISOString();
  const source = '通达信本地最近交易日收盘数据（降级）';
  const withFallbackMetadata = (row) => ({ ...row, realtime: false, quoteMode: 'local_daily_close', source, quality: 'degraded' });
  const tradeDate = [...rows, ...indices].map((row) => compactMarketDate(row?.date)).filter(Boolean).sort().at(-1)
    || compactMarketDate(snapshot.tradeDate || snapshot.date);
  return {
    status: 'ok', source, provider: 'local_resource_library', quality: 'degraded', fallback: true,
    fallbackReason: String(reason || '').slice(0, 500), fetchedAt, latestDataAt: fetchedAt,
    tradeDate, quoteMode: 'local_daily_close',
    indices: scope === 'indices' ? indices.map(withFallbackMetadata) : [],
    stocks: scope === 'indices' ? [] : rows.slice(0, 200).map(withFallbackMetadata),
    allStocks: scope === 'market' ? rows.map(withFallbackMetadata) : [],
    marketSummary: scope === 'market' ? {
      currentCount: Number(snapshot.currentCount || rows.length), up: Number(snapshot.up || 0),
      down: Number(snapshot.down || 0), flat: Number(snapshot.flat || 0),
      amount: Number(snapshot.amount || 0), bins: Array.isArray(snapshot.bins) ? snapshot.bins : [],
    } : undefined,
    replaceLeaderboard: scope !== 'indices',
    scope: `通达信实时行情和公开行情暂不可用，已使用 ${tradeDate || '最近交易日'} 本地收盘数据`,
    dataSources: {
      primary: 'TongdaXin/TQ', fallback: 'Local TDX daily archive', fallbackQuality: 'DEGRADED',
      fallbackReason: String(reason || '').slice(0, 500),
    },
  };
}

async function runPublicOnlyMarketRefresh(scope, codes, reason) {
  const args = ['--scope', scope, '--public-only'];
  if (scope === 'watchlist' && codes) args.push('--codes', codes);
  const result = await runLocalScript('market_overview_refresh.py', args, 30000, 0);
  let value;
  try { value = JSON.parse(result.output || '{}'); } catch { throw new Error('Public fallback returned invalid JSON'); }
  if (!value || value.status === 'error') throw new Error(String(value?.error || 'Public fallback unavailable'));
  const normalized = { ...value, fallback: true, quality: 'degraded', fallbackReason: String(value.fallbackReason || reason || '').slice(0, 500) };
  await persistPublicResearchFallback(normalized, reason).catch(() => undefined);
  return normalized;
}

async function runMarketRefresh(scope = 'indices', codes = '') {
  if (scope === 'market') {
    try {
      // 市场全量快照包含数千只股票，不能使用普通脚本的 12KB 尾部截断，
      // 否则 JSON 会被截断后触发降级到旧的公开快照。
      const value = JSON.parse((await runLocalScript('market_overview_refresh.py', ['--scope', 'market'], 600000, 0)).output);
      return value;
    } catch (error) {
      if (isLocalOnlyDataPolicy()) throw error;
      // 本地完整日线不可用时保留公开涨停池作为降级数据，但把来源和日期
      // 明确交给页面，不能静默继续使用旧 market.json。
      const fallback = await runPublicMarketRefresh();
      return { ...fallback, scope: `${fallback.scope}；本地日线刷新失败：${error instanceof Error ? error.message : String(error)}` };
    }
  }
  const publicHedge = isLocalOnlyDataPolicy()
    ? null
    : new Promise((resolve) => setTimeout(resolve, 1200))
      .then(() => fastPublicMarketRefresh(scope, codes, '通达信实时请求等待中'))
      .then((value) => ({ ok: true, value }), (error) => ({ ok: false, error }));
  const primary = new Promise((resolve, reject) => {
    const python = localPythonExecutable();
    const script = path.join(APP_ROOT, 'scripts', 'market_overview_refresh.py');
    const args = [script, '--scope', scope];
    if (scope === 'watchlist' && codes) args.push('--codes', codes);
    const child = spawn(python, args, {
      windowsHide: true,
      env: localScriptEnvironment(scope === 'watchlist' && codes
        ? { ZHANGCAI_PUBLIC_WATCHLIST_CODES: codes }
        : {}),
    });
    let stdout = '';
    let stderr = '';
    const timeoutMs = scope === 'watchlist'
      ? Number(process.env.ZHANGCAI_TDX_QUOTE_TIMEOUT_MS || 15000)
      : Number(process.env.ZHANGCAI_TDX_INDEX_TIMEOUT_MS || 30000);
    const timer = setTimeout(() => {
      if (child.pid) spawn('taskkill', ['/pid', String(child.pid), '/t', '/f'], { windowsHide: true });
      reject(new Error(scope === 'watchlist' ? 'TDX signal timed out' : '通达信实时行情刷新超时'));
    }, timeoutMs);
    child.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
    child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
    child.on('error', (error) => { clearTimeout(timer); reject(error); });
    child.on('close', (code) => {
      clearTimeout(timer);
      if (code !== 0) { reject(new Error(readableScriptError('market_overview_refresh.py', stderr || stdout, code))); return; }
      try {
        const value = JSON.parse(stdout.trim());
        if (!value || value.status === 'error') {
          reject(new Error(String(value?.error || '实时行情刷新失败')));
          return;
        }
        if (value.fallback === true) void persistPublicResearchFallback(value).catch(() => undefined);
        if (scope === 'watchlist') void persistMarketSnapshot(scope, value).catch(() => undefined);
        resolve(value);
      } catch { reject(new Error('实时行情返回格式无效')); }
    });
  });
  try {
    const expectedWatchlistCode = scope === 'watchlist'
      ? String(codes || '').trim().split(',')[0].trim().split('.', 1)[0]
      : '';
    const primaryResult = primary.then(
      (value) => {
        if (!value || value.status === 'error') {
          return { kind: 'primary-error', error: new Error(String(value?.error || '行情桥接返回错误状态')) };
        }
        if (scope === 'watchlist' && expectedWatchlistCode) {
          const quote = (Array.isArray(value.stocks) ? value.stocks : [])
            .find((row) => String(row?.code || '') === expectedWatchlistCode);
          if (!quote || !(Number(quote.close) > 0)) {
            return { kind: 'primary-error', error: new Error(`行情桥接未返回 ${expectedWatchlistCode} 的有效价格`) };
          }
        }
        return { kind: 'primary', value };
      },
      (error) => ({ kind: 'primary-error', error }),
    );
    const candidates = [primaryResult];
    if (publicHedge) {
      const eligiblePublic = Promise.all([
        new Promise((resolve) => setTimeout(resolve, 7000)),
        publicHedge,
      ]).then(([, result]) => (
        result.ok
          ? { kind: 'public', value: result.value }
          : new Promise(() => {})
      ));
      candidates.push(eligiblePublic);
    }
    const winner = await Promise.race(candidates);
    if (winner.kind === 'primary') return winner.value;
    if (winner.kind === 'public') {
      const value = {
        ...winner.value,
        fallback: true,
        quality: 'degraded',
        fallbackReason: '通达信实时请求超过 7 秒，已先返回公开行情延时降级数据',
      };
      await persistPublicResearchFallback(value, value.fallbackReason).catch(() => undefined);
      return value;
    }
    throw winner.error;
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error);
    if (publicHedge) {
      const fast = await publicHedge;
      if (fast.ok) {
        const value = {
          ...fast.value,
          fallback: true,
          quality: 'degraded',
          fallbackReason: `TDX_SIGNAL_TIMEOUT: ${reason}`.slice(0, 500),
        };
        await persistPublicResearchFallback(value, reason).catch(() => undefined);
        return value;
      }
    }
    try {
      return await runPublicOnlyMarketRefresh(scope, codes, `TDX_SIGNAL_TIMEOUT: ${reason}`);
    } catch (publicError) {
      const local = localMarketFallback(scope, codes, `TDX_SIGNAL_TIMEOUT: ${reason}; public fallback failed: ${publicError instanceof Error ? publicError.message : String(publicError)}`);
      if (local) {
        await persistPublicResearchFallback(local).catch(() => undefined);
        return local;
      }
      throw error;
    }
  }
}


function runCanonicalStrategy(requestedSkillId) {
  return new Promise((resolve, reject) => {
    const skillId = canonicalStrategyId(requestedSkillId);
    if (!CANONICAL_STRATEGY_IDS.has(skillId)) {
      reject(new Error('该策略未配置原始技能入口'));
      return;
    }
    const skillRoot = path.join(SKILL_SOURCE, skillId);
    const entry = resolveSkillEntry(skillRoot);
    if (!existsSync(entry)) {
      reject(new Error(`未找到原始策略入口：${skillId}`));
      return;
    }
    const tdxRoot = bridgeTdxRoot();
    const minuteData = strategyMinuteDataPreflight(skillId, tdxRoot);
    if (PARAMETER_REQUIRED_STRATEGIES.has(skillId)) {
      resolve({
        status: 'PARAMETER_REQUIRED',
        skill_id: skillId,
        output: JSON.stringify({
          status: 'PARAMETER_REQUIRED',
          message: '黄金点火需要指定股票或可转债代码，当前策略页尚未提供标的输入框。',
          action: '请在个股研究页选择股票后运行，或在策略页补充代码输入。',
        }, null, 2),
      });
      return;
    }
    if (SPECIAL_DATA_STRATEGIES.has(skillId)) {
      resolve({
        status: 'DATA_REQUIRED',
        skill_id: skillId,
        output: JSON.stringify({
          status: 'DATA_REQUIRED',
          message: '可转债筛选需要可转债行情、正股映射和债券条款数据；当前本地快照未提供。',
          action: '先补齐可转债数据源后再启动原始策略。',
        }, null, 2),
      });
      return;
    }
    let dataDate = null;
    let requestedDataDate = null;
    let dailySource = '';
    let dailyDegraded = false;
    let dailyDegradationReason = '';
    try {
      // Prefer the newest date physically present in the configured TDX .day
      // files. The resource-library archive remains the fallback; a lagging
      // archive date must not block skills that can read the local TDX history.
      const dailyManifest = readJson(path.join(DATA_ROOT, 'status', 'tdx-daily-history.json')) || {};
      const dailyIndex = readJson(DAILY_DATA_INDEX_FILE) || {};
      const archiveCount = Number(
        dailyManifest.current_trade_date_symbols
          || dailyManifest.latest_date_source_files
          || dailyIndex.summary?.latest_symbol_count
          || 0,
      );
      const runtimeMarket = readJson(path.join(DATA_ROOT, 'runtime', 'market-latest.json')) || {};
      const archiveDate = String(dailyManifest.trade_date || '').replace(/\D/g, '') || null;
      const liveDaily = inspectTdxDailyIntegrity(tdxRoot);
      const liveDate = String(liveDaily.latestDate || '').replace(/\D/g, '') || null;
      const liveCount = Number(liveDaily.latestCount || 0);
      const archiveRequestedDate = String(
        dailyManifest.expected_trade_date
          || dailyManifest.freshness?.expected_trade_date
          || dailyIndex.latest_trade_date
          || archiveDate
          || '',
      ).replace(/\D/g, '') || null;
      const liveFreshness = dailyFreshnessSnapshot({ latestDate: liveDate || '' });
      requestedDataDate = liveDate
        ? (liveFreshness.updateDue ? liveFreshness.currentDate : liveDate)
        : String([
          archiveRequestedDate,
          runtimeMarket.tradeDate,
          runtimeMarket.trade_date,
          runtimeMarket.date,
        ].map((value) => String(value || '').replace(/\D/g, '')).filter((value) => /^\d{8}$/.test(value)).sort().at(-1) || archiveRequestedDate || '').replace(/\D/g, '') || null;
      const archiveFile = String(dailyManifest.file || 'market/daily/aggregate/tdx-bars.jsonl');
      const archivePath = path.isAbsolute(archiveFile) ? archiveFile : path.join(DATA_ROOT, archiveFile);
      const archiveUsable = Boolean(
        archiveDate
          && existsSync(archivePath)
          && archiveCount > 0
          && Number(dailyManifest.bar_records || 0) > 0,
      );
      const archiveStatus = String(dailyManifest.status || '').toLowerCase();
      const archiveReady = archiveUsable && ['available', 'degraded', 'stale'].includes(archiveStatus);
      const useLiveDaily = Boolean(liveDate && liveCount > 0 && (!archiveReady || liveDate > archiveDate));
      const selectedArchiveReady = archiveReady || useLiveDaily;
      const currentCount = useLiveDaily ? liveCount : archiveCount;
      dataDate = useLiveDaily ? liveDate : archiveReady ? archiveDate : null;
      dailySource = useLiveDaily ? 'configured_tdx_day_files' : archiveReady ? 'resource_library_archive' : '';
      dailyDegraded = Boolean(
        selectedArchiveReady
          && (useLiveDaily || (requestedDataDate && dataDate && requestedDataDate !== dataDate) || currentCount < 3000),
      );
      const degradationNotes = [];
      if (useLiveDaily && archiveDate && liveDate > archiveDate) {
        degradationNotes.push(`资源库归档停留在 ${archiveDate}，已改用通达信本地最新日线 ${liveDate}`);
      } else if (useLiveDaily && !archiveReady) {
        degradationNotes.push(`resource-library 日线归档不可用，本次直接读取通达信本地日线 ${liveDate}`);
      }
      if (requestedDataDate && dataDate && requestedDataDate !== dataDate) {
        degradationNotes.push(`请求日线 ${requestedDataDate} 尚未落盘，已使用最近可用日线 ${dataDate}`);
      }
      if (currentCount < 3000 && dataDate) {
        degradationNotes.push(`该日期可用证券覆盖 ${currentCount}，只允许按实际覆盖范围研究`);
      }
      dailyDegradationReason = degradationNotes.join('；');
      if (!archiveReady && !useLiveDaily) {
        resolve({
          status: 'BLOCKED',
          skill_id: skillId,
          output: JSON.stringify({
            status: 'BLOCKED',
            message: '未找到可用的通达信本地日线或 resource-library 日线归档，原始策略已阻断。',
            data_date: dataDate,
            requested_data_date: requestedDataDate,
            archive_status: dailyManifest.status || 'missing',
            archive_file: dailyManifest.file || '',
            action: '请确认通达信安装目录下存在 .day 历史，或先在数据与设置页完成日线落盘。',
            minute_data: minuteData,
          }, null, 2),
          data_date: dataDate,
          minute_data: minuteData,
        });
        return;
      }
      if (currentCount < 3000) {
        resolve({
          status: 'BLOCKED',
          skill_id: skillId,
          output: JSON.stringify({
            status: 'BLOCKED',
            message: '最新可用日线的全市场覆盖不足，原始策略按完整样本契约阻断；日期已回退至实际日线日期。',
            required_current_count: 3000,
            actual_current_count: currentCount,
            data_date: dataDate,
            requested_data_date: requestedDataDate,
            daily_source: dailySource,
            action: '对要求全市场完整覆盖的策略，补齐沪深北日线后重试；不会将部分样本标成全市场结果。',
            minute_data: minuteData,
          }, null, 2),
          minute_data: minuteData,
        });
        return;
      }
      if (skillId === 'a-share-15d-selection') {
        const formulaRegistry = readTdxPrivateFormulaNames(tdxRoot);
        const requiredFormulaFiles = [
          '大牛线撑压版.tn6',
          '飞龙在天.tn6',
          '游资资金监控.tn6',
          '机构资金监控.tn6',
          '庄家资金监控.tn6',
        ];
        const formulaFiles = requiredFormulaFiles.map((name) => ({
          name,
          path: path.join(tdxRoot, 'T0002', 'gs_bak', name),
          exists: existsSync(path.join(tdxRoot, 'T0002', 'gs_bak', name)),
        }));
        if (!formulaRegistry.names.length) {
          resolve({
            status: 'FORMULA_REGISTRATION_REQUIRED',
            skill_id: skillId,
            output: JSON.stringify({
              status: 'FORMULA_REGISTRATION_REQUIRED',
              message: '通达信 TQ 原生私有公式注册表为空，已停止全量运行，避免逐只候选重复等待。',
              registry_path: formulaRegistry.path,
              registry_count: 0,
              required_formulas: requiredFormulaFiles,
              formula_files: formulaFiles,
              action: '在通达信中打开“公式管理器/公式系统”，导入五个 .tn6 文件；导入完成后重新点击运行原始策略。',
              minute_data: minuteData,
            }, null, 2),
            data_date: dataDate,
            minute_data: minuteData,
          });
          return;
        }
      }
    } catch (error) {
      reject(new Error(`无法读取策略数据预检快照：${error instanceof Error ? error.message : String(error)}`));
      return;
    }
    const python = localPythonExecutable();
    const outputRoot = path.join(DATA_ROOT, 'strategy-results');
    const startedAt = Date.now();
    const child = spawn(python, [entry, 'run'], {
      cwd: skillRoot,
      windowsHide: true,
      env: localScriptEnvironment({
        ONESTOCK_STOCK_DATA_ROOT: outputRoot,
        STOCK_SKILLS_ROOT: SKILL_SOURCE,
        PYTHONPATH: [path.join(SKILL_SOURCE, 'stock-unified', 'scripts'), process.env.PYTHONPATH || ''].filter(Boolean).join(path.delimiter),
        ZHANGCAI_ANALYSIS_TRADE_DATE: dataDate || '',
        ZHANGCAI_REQUESTED_TRADE_DATE: requestedDataDate || '',
        ZHANGCAI_DAILY_DATA_QUALITY: dailyDegraded ? 'DEGRADED' : 'AVAILABLE',
        ZHANGCAI_DAILY_DATA_NOTICE: dailyDegradationReason,
        ZHANGCAI_DAILY_DATA_SOURCE: dailySource,
        ZHANGCAI_TDX_LATEST_DAILY_DATE: liveDate || '',
        ZHANGCAI_TDX_LATEST_DAILY_SYMBOLS: String(liveCount || 0),
      }),
    });
    let stdout = '';
    let stderr = '';
    const timeoutMs = 22 * 60 * 1000;
    const timer = setTimeout(() => {
      if (child.pid) spawn('taskkill', ['/pid', String(child.pid), '/t', '/f'], { windowsHide: true });
      reject(new Error(`原始策略执行超时（${Math.round(timeoutMs / 60000)} 分钟）`));
    }, timeoutMs);
    child.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
    child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
    child.on('error', (error) => { clearTimeout(timer); reject(error); });
    child.on('close', (code) => {
      clearTimeout(timer);
      const combined = `${stdout}\n${stderr}`.trim();
      const receiptMatch = combined.match(/STOCK_RUNTIME_RECEIPT\s+(\{.*\})/);
      let receipt = null;
      if (receiptMatch) {
        try { receipt = JSON.parse(receiptMatch[1]); } catch { /* 保留原始输出 */ }
      }
      const structured = collectStrategyStructured(receipt, combined, skillId);
      const rawStatus = receipt?.status || (code === 0 ? 'CLEAN_PASS' : 'BLOCKED');
      const minuteDegraded = minuteData.result === 'DEGRADED';
      const resultStatus = minuteDegraded && ['CLEAN_PASS', 'PASS', 'READY_FOR_VALIDATED_RUN', 'ok'].includes(String(rawStatus))
        ? 'DEGRADED'
        : rawStatus;
      const output = [
        combined,
        dailyDegraded
          ? `[日线降级] ${dailyDegradationReason}。本次结果仅使用该交易日收盘数据，不代表请求日盘中数据。`
          : '',
        minuteDegraded
          ? `[分钟线降级] ${minuteData.purpose} 当前未将原始 .lc5 写入 EXE，结果不得解释为完整分钟级结论。`
          : '',
      ].filter(Boolean).join('\n');
      resolve({
        status: resultStatus,
        output: output.slice(-MAX_OUTPUT),
        elapsed_ms: Date.now() - startedAt,
        receipt,
        structured,
        skill_id: skillId,
        minute_data: minuteData,
        data_date: dataDate,
        requested_data_date: requestedDataDate,
        daily_source: dailySource,
        data_quality: dailyDegraded ? 'DEGRADED' : 'AVAILABLE',
        data_degradation: dailyDegradationReason,
      });
    });
  });
}

function startStrategyJob(skillId) {
  const job = { id: randomUUID(), skill_id: skillId, status: 'running', started_at: Date.now() };
  strategyJobs.set(job.id, job);
  persistStrategyJob(job);
  void runCanonicalStrategy(skillId).then((result) => {
    const current = strategyJobs.get(job.id);
    if (!current) return;
    Object.assign(current, {
      status: 'completed',
      strategy_status: result.status || 'UNKNOWN',
      output: String(result.output || ''),
      result,
      elapsed_ms: Number(result.elapsed_ms || (Date.now() - job.started_at)),
      completed_at: Date.now(),
    });
    persistStrategyJob(current);
  }).catch((error) => {
    const current = strategyJobs.get(job.id);
    if (!current) return;
    Object.assign(current, {
      status: 'failed',
      error: error instanceof Error ? error.message : String(error),
      elapsed_ms: Date.now() - job.started_at,
      completed_at: Date.now(),
    });
    persistStrategyJob(current);
  });
  return job;
}

function compactDateText(value) {
  const raw = String(value || '').replace(/\D/g, '');
  return /^\d{8}$/.test(raw) ? raw : '';
}

function displayDateText(value) {
  const raw = compactDateText(value);
  return raw ? `${raw.slice(0, 4)}-${raw.slice(4, 6)}-${raw.slice(6)}` : '';
}

function localTradingCalendar() {
  const calendarFiles = [
    path.join(DATA_ROOT, 'harness', 'skills', 'a-share-15d-selection', 'references', 'trading-calendar.json'),
    path.join(APP_ROOT, 'harness-skills', 'a-share-15d-selection', 'references', 'trading-calendar.json'),
  ];
  for (const file of calendarFiles) {
    const value = readJson(file);
    if (Array.isArray(value?.closed_dates)) {
      return {
        closedDates: new Set(value.closed_dates.map((date) => compactDateText(date)).filter(Boolean)),
        source: file,
      };
    }
  }
  return { closedDates: new Set(), source: '' };
}

function isTradingDayDate(value) {
  const date = compactDateText(value);
  if (!date) return false;
  const day = new Date(Date.UTC(Number(date.slice(0, 4)), Number(date.slice(4, 6)) - 1, Number(date.slice(6))));
  return day.getUTCDay() !== 0 && day.getUTCDay() !== 6 && !localTradingCalendar().closedDates.has(date);
}

function shanghaiDateParts(now = new Date()) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(now).reduce((result, item) => ({ ...result, [item.type]: item.value }), {});
  return { year: Number(parts.year), month: Number(parts.month), day: Number(parts.day) };
}

function shanghaiDateText(now = new Date()) {
  const { year, month, day } = shanghaiDateParts(now);
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

function localTradeDate() {
  // 日期必须来自应用自己的可核验快照，而不是宿主机自然日。这样在
  // 16:30 后、周末或节假日重启桥接时，不会把没有行情的日期传给公开接口。
  const candidates = [];
  const add = (value, source) => {
    const date = compactDateText(value);
    if (date) candidates.push({ date, source });
  };
  add(readJson(path.join(DATA_ROOT, 'status', 'tdx-daily-history.json'))?.trade_date, 'tdx-daily-history');
  add(readJson(path.join(DATA_ROOT, 'runtime', 'market-latest.json'))?.tradeDate, 'market-latest');
  add(readJson(path.join(DATA_ROOT, 'runtime', 'market-latest.json'))?.trade_date, 'market-latest');
  add(readJson(path.join(DATA_ROOT, 'public', 'latest.json'))?.date, 'public-latest');
  add(readJson(path.join(DATA_ROOT, 'news', 'latest.json'))?.date, 'news-latest');
  add(readJson(SUPPLEMENTAL_LATEST_FILE)?.trade_date, 'supplemental-latest');
  const dailyIndex = readJson(DAILY_DATA_INDEX_FILE);
  for (const key of Object.keys(dailyIndex?.dates || {})) add(key, 'daily-data-index');
  try {
    const runtimeDir = path.join(DATA_ROOT, 'runtime');
    const reports = readdirSync(runtimeDir)
      .filter((name) => /^(?:tdx-daily-replenish|tdx-daily-integrity)-\d{8}-\d{6}\.json$/.test(name))
      .sort()
      .reverse();
    for (const name of reports.slice(0, 10)) {
      const value = readJson(path.join(runtimeDir, name));
      add(value?.targetDateAfter || value?.targetDate || value?.before?.targetDate || value?.after?.targetDate, name);
    }
  } catch { /* 首次运行尚无本地快照，继续使用自然日作为最后回退。 */ }
  const latest = candidates.sort((left, right) => right.date.localeCompare(left.date))[0];
  if (latest) return displayDateText(latest.date);
  return shanghaiDateText();
}

function readJson(file) {
  try { return JSON.parse(readFileSync(file, 'utf8')); } catch { return null; }
}

function supplementalDateKey(value) {
  const raw = String(value || '').replace(/\D/g, '');
  return /^\d{8}$/.test(raw) ? raw : localTradeDate().replace(/\D/g, '');
}

function supplementalStockFile(date, code, market = '') {
  const key = supplementalDateKey(date);
  const normalized = normalizeHistorySymbol(`${code}.${market || ''}`) || normalizeHistorySymbol(code);
  const suffix = normalized?.market || (String(market).toUpperCase() || 'SZ');
  return path.join(SUPPLEMENTAL_ROOT, key, `${String(code).replace(/\D/g, '').slice(-6)}.${suffix}.json`);
}

function readSupplementalSnapshot(date, code = '') {
  const key = supplementalDateKey(date);
  if (code) {
    const normalized = normalizeHistorySymbol(code);
    if (normalized) {
      const file = supplementalStockFile(key, normalized.code, normalized.market);
      const value = readJson(file);
      if (value) return { ...value, snapshot_path: file };
    }
  }
  const file = path.join(SUPPLEMENTAL_ROOT, key, 'market.json');
  const value = readJson(file);
  return value ? { ...value, snapshot_path: file } : null;
}

async function ensureStockSupplemental(rawCode, date) {
  const normalized = normalizeHistorySymbol(rawCode);
  if (!normalized) return null;
  const key = supplementalDateKey(date);
  const current = readSupplementalSnapshot(key, normalized.code);
  const currentCoverage = current?.coverage || {};
  if (current && current.requested_date?.replace(/\D/g, '') === key && currentCoverage.financial && currentCoverage.share_capital) return current;
  const jobKey = `${key}:${normalized.key}`;
  const running = supplementalTargetJobs.get(jobKey);
  if (running) return running;
  const job = (async () => {
    try {
      await runLocalScript(
        'supplemental_data_sync.py',
        ['--date', key, '--mode', 'stock', '--code', normalized.code],
        Number(process.env.ZHANGCAI_STOCK_SUPPLEMENTAL_TIMEOUT_MS || 600000),
        0,
      );
      return readSupplementalSnapshot(key, normalized.code);
    } catch (error) {
      console.warn(`[agent] 个股补充数据刷新失败 ${normalized.symbol}: ${error instanceof Error ? error.message : String(error)}`);
      return current || {
        schema: 'ZHANGCAI_SUPPLEMENTAL_DATA_V1', requested_date: key, trade_date: key,
        stock: { code: normalized.code }, coverage: {}, status: 'unavailable', error: error instanceof Error ? error.message : String(error),
      };
    } finally {
      supplementalTargetJobs.delete(jobKey);
    }
  })();
  supplementalTargetJobs.set(jobKey, job);
  return job;
}

async function enrichHarnessContext(context, onProgress) {
  if (!context || typeof context !== 'object') return context;
  const targetCode = context?.targetStock?.code;
  if (!targetCode) {
    onProgress?.('supplemental', 'completed', '本技能无需额外个股补充快照。');
    return context;
  }
  const date = context?.targetStock?.date || context?.historyMeta?.lastDate || localTradeDate();
  onProgress?.(
    'supplemental',
    'running',
    `正在处理 ${targetCode} 的财务、股本等补充快照。`,
  );
  const supplementalData = await ensureStockSupplemental(targetCode, date);
  onProgress?.(
    'supplemental',
    'completed',
    supplementalData?.status === 'unavailable'
      ? '补充数据处理完成，但部分来源不可用。'
      : '财务、股本等补充数据已写入研究上下文。',
  );
  return { ...context, supplementalData: supplementalData || { status: 'missing', requested_date: date, coverage: {} } };
}

function normalizeHistorySymbol(value) {
  const raw = String(value || '').trim().toUpperCase();
  const codeMatch = raw.match(/(?:^|[^0-9])(\d{6})(?:$|[^0-9])/);
  const code = codeMatch ? codeMatch[1] : raw.replace(/[^0-9]/g, '').slice(-6);
  if (!/^\d{6}$/.test(code)) return null;
  const explicitMarket = raw.match(/(?:^|[.\s])(SH|SZ|BJ|上交所|深交所|北交所)(?:$|[.\s])/i)?.[1]?.toUpperCase();
  const market = explicitMarket === 'SH' || explicitMarket === '上交所' || /^[569]/.test(code)
    ? 'SH'
    : explicitMarket === 'BJ' || explicitMarket === '北交所' || /^(920|[48])/.test(code)
      ? 'BJ'
      : 'SZ';
  return { code, market, key: `${market.toLowerCase()}${code}`, symbol: `${code}.${market}` };
}

function parseTdxDayRecord(buffer, offset = 0) {
  if (!buffer || offset < 0 || offset + TDX_DAY_RECORD_SIZE > buffer.length) return null;
  const dateNumber = buffer.readUInt32LE(offset);
  const date = String(dateNumber).replace(/^(\d{4})(\d{2})(\d{2})$/, '$1-$2-$3');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return null;
  return {
    date,
    open: Number((buffer.readUInt32LE(offset + 4) / 100).toFixed(2)),
    high: Number((buffer.readUInt32LE(offset + 8) / 100).toFixed(2)),
    low: Number((buffer.readUInt32LE(offset + 12) / 100).toFixed(2)),
    close: Number((buffer.readUInt32LE(offset + 16) / 100).toFixed(2)),
    amount: Number(buffer.readFloatLE(offset + 20).toFixed(2)),
    volume: buffer.readUInt32LE(offset + 24),
  };
}

function readTdxDayBoundary(file) {
  try {
    const size = statSync(file).size;
    const recordCount = Math.floor(size / TDX_DAY_RECORD_SIZE);
    const remainder = size % TDX_DAY_RECORD_SIZE;
    if (!recordCount || remainder) return null;
    const handle = openSync(file, 'r');
    const firstBuffer = Buffer.alloc(TDX_DAY_RECORD_SIZE);
    const lastBuffer = Buffer.alloc(TDX_DAY_RECORD_SIZE);
    try {
      readSync(handle, firstBuffer, 0, TDX_DAY_RECORD_SIZE, 0);
      readSync(handle, lastBuffer, 0, TDX_DAY_RECORD_SIZE, size - TDX_DAY_RECORD_SIZE);
    } finally {
      closeSync(handle);
    }
    const first = parseTdxDayRecord(firstBuffer);
    const last = parseTdxDayRecord(lastBuffer);
    if (!first || !last) return null;
    return { record_count: recordCount, first_date: first.date, last_date: last.date };
  } catch {
    return null;
  }
}

async function buildTdxHistoryIndex(force = false) {
  const configuredRoot = bridgeTdxRoot();
  const tdxRoot = configuredRoot ? path.resolve(configuredRoot) : '';
  const cached = readJson(TDX_HISTORY_INDEX_FILE);
  if (!force && cached?.schema === 'ZHANGCAI_TDX_SYMBOL_INDEX_V1' && cached.source_root === tdxRoot && cached.symbols && Object.keys(cached.symbols).length) {
    return { ...cached, cached: true };
  }
  const symbols = {};
  const marketDirs = ['sh', 'sz', 'bj'];
  for (const marketDir of marketDirs) {
    const directory = path.join(tdxRoot, 'vipdoc', marketDir, 'lday');
    if (!existsSync(directory)) continue;
    for (const name of readdirSync(directory)) {
      const match = name.match(/^(sh|sz|bj)(\d{6})\.day$/i);
      if (!match) continue;
      const normalized = normalizeHistorySymbol(`${match[2]}.${match[1]}`);
      if (!normalized) continue;
      const file = path.join(directory, name);
      const boundary = readTdxDayBoundary(file);
      if (!boundary) continue;
      symbols[normalized.key] = {
        symbol: normalized.symbol,
        code: normalized.code,
        market: normalized.market,
        file: path.relative(tdxRoot, file),
        ...boundary,
      };
    }
  }
  // TDX may be closed or disconnected. Never replace a previously verified
  // symbol index with an empty one: it is still useful for resolving the
  // fallback layer and for explaining which external source is unavailable.
  if (!Object.keys(symbols).length && cached?.schema === 'ZHANGCAI_TDX_SYMBOL_INDEX_V1' && cached.symbols && Object.keys(cached.symbols).length) {
    return { ...cached, cached: true, source_available: false, degraded_reason: '通达信源目录当前不可读，保留上次已生成的索引' };
  }
  const index = {
    schema: 'ZHANGCAI_TDX_SYMBOL_INDEX_V1',
    generated_at: new Date().toISOString(),
    source_root: tdxRoot,
    source_kind: 'Tongdaxin local .day files',
    symbol_count: Object.keys(symbols).length,
    symbols,
  };
  await writeRuntimeJson(TDX_HISTORY_INDEX_FILE, index);
  return { ...index, cached: false };
}

// The data installer carries one canonical, append-only JSONL archive.  Keep
// a small byte-range index beside it so a single-stock research request does
// not scan the multi-gigabyte archive from the beginning.  The archive is
// written by symbol, but the lookup still checks the symbol on every row so a
// future writer that interleaves symbols remains safe.
let canonicalDailyIndexBuild = null;

async function forEachCanonicalDailyLine(file, onLine) {
  const stream = createReadStream(file, { highWaterMark: 1024 * 1024 });
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

function canonicalDate(value) {
  const raw = String(value || '').replace(/\D/g, '');
  return /^\d{8}$/.test(raw) ? `${raw.slice(0, 4)}-${raw.slice(4, 6)}-${raw.slice(6)}` : String(value || '');
}

async function buildCanonicalDailyIndex(force = false) {
  if (!existsSync(CANONICAL_DAILY_FILE)) return null;
  let source;
  try { source = statSync(CANONICAL_DAILY_FILE); } catch { return null; }
  const cached = readJson(CANONICAL_DAILY_INDEX_FILE);
  if (!force
    && cached?.schema === 'ZHANGCAI_CANONICAL_DAILY_SYMBOL_INDEX_V1'
    && Number(cached.source_size) === Number(source.size)
    && Math.abs(Number(cached.source_mtime_ms) - Number(source.mtimeMs)) < 1
    && cached.symbols
    && Object.keys(cached.symbols).length) {
    return { ...cached, cached: true };
  }
  if (canonicalDailyIndexBuild) return canonicalDailyIndexBuild;
  canonicalDailyIndexBuild = (async () => {
    const symbols = {};
    let recordCount = 0;
    await forEachCanonicalDailyLine(CANONICAL_DAILY_FILE, async (line, offset) => {
      const text = line.toString('utf8').replace(/\r$/, '').trim();
      if (!text) return;
      let value;
      try { value = JSON.parse(text); } catch { return; }
      const normalized = normalizeHistorySymbol(value?.market ? `${value.symbol}.${value.market}` : String(value?.symbol || ''));
      if (!normalized) return;
      const endOffset = offset + line.length + 1;
      const date = canonicalDate(value.date);
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
    const index = {
      schema: 'ZHANGCAI_CANONICAL_DAILY_SYMBOL_INDEX_V1',
      generated_at: new Date().toISOString(),
      source_file: dataRelativePath(CANONICAL_DAILY_FILE),
      source_size: source.size,
      source_mtime_ms: source.mtimeMs,
      source_kind: 'Packaged canonical daily JSONL · byte-range lookup',
      symbol_count: Object.keys(symbols).length,
      record_count: recordCount,
      symbols,
    };
    await writeRuntimeJson(CANONICAL_DAILY_INDEX_FILE, index);
    return { ...index, cached: false };
  })();
  try { return await canonicalDailyIndexBuild; } finally { canonicalDailyIndexBuild = null; }
}

async function readCanonicalDailyHistory(normalized, limit = 0, forceIndex = false) {
  const index = await buildCanonicalDailyIndex(forceIndex);
  const entry = index?.symbols?.[normalized.key];
  if (!entry || !existsSync(CANONICAL_DAILY_FILE)) return null;
  const start = Math.max(0, Number(entry.start_offset || 0));
  const end = Math.max(start, Number(entry.end_offset || 0));
  if (end <= start) return null;
  const stream = createReadStream(CANONICAL_DAILY_FILE, { start, end: end - 1, encoding: 'utf8' });
  let pending = '';
  const rows = [];
  for await (const chunk of stream) {
    pending += chunk;
    const parts = pending.split(/\r?\n/);
    pending = parts.pop() || '';
    for (const line of parts) {
      if (!line.trim()) continue;
      try {
        const value = JSON.parse(line);
        const rowSymbol = normalizeHistorySymbol(value?.market ? `${value.symbol}.${value.market}` : String(value?.symbol || ''));
        if (!rowSymbol || rowSymbol.key !== normalized.key) continue;
        rows.push({
          date: canonicalDate(value.date),
          open: Number(value.open), high: Number(value.high), low: Number(value.low),
          close: Number(value.close), amount: value.amount == null ? null : Number(value.amount),
          volume: Number(value.volume), source: 'packaged-canonical-daily',
        });
      } catch { /* 跳过损坏行，保留同一股票的其他日线 */ }
    }
  }
  if (pending.trim()) {
    try {
      const value = JSON.parse(pending);
      const rowSymbol = normalizeHistorySymbol(value?.market ? `${value.symbol}.${value.market}` : String(value?.symbol || ''));
      if (rowSymbol?.key === normalized.key) rows.push({
        date: canonicalDate(value.date),
        open: Number(value.open), high: Number(value.high), low: Number(value.low),
        close: Number(value.close), amount: value.amount == null ? null : Number(value.amount),
        volume: Number(value.volume), source: 'packaged-canonical-daily',
      });
    } catch { /* ignore a truncated final line */ }
  }
  const unique = new Map(rows.filter((row) => row.date).map((row) => [row.date, row]));
  const ordered = [...unique.values()].sort((a, b) => a.date.localeCompare(b.date));
  return { index, entry, history: limit > 0 ? ordered.slice(-limit) : ordered, total: ordered.length };
}

function readPublicDailyFallbackHistory(normalized, limit = 0) {
  const rows = [];
  const filename = `${normalized.key}.jsonl`;
  if (!existsSync(DAILY_FALLBACK_ROOT)) return rows;
  let dates = [];
  try {
    dates = readdirSync(DAILY_FALLBACK_ROOT).filter((name) => /^\d{8}$/.test(name)).sort();
  } catch { return rows; }
  for (const date of dates) {
    const file = path.join(DAILY_FALLBACK_ROOT, date, filename);
    if (!existsSync(file)) continue;
    for (const line of readText(file, 2 * 1024 * 1024).split(/\r?\n/)) {
      if (!line.trim()) continue;
      try {
        const value = JSON.parse(line);
        if (value && value.date && value.symbol === normalized.key) rows.push({
          date: String(value.date).replace(/^(\d{4})(\d{2})(\d{2})$/, '$1-$2-$3'),
          open: Number(value.open), high: Number(value.high), low: Number(value.low),
          close: Number(value.close), amount: value.amount == null ? null : Number(value.amount),
          volume: Number(value.volume), source: value.source, source_date: value.source_date,
          status: value.status || 'degraded', missing_fields: value.missing_fields || [],
        });
      } catch { /* 跳过损坏的单行，索引仍可用于其他日期 */ }
    }
  }
  const unique = new Map(rows.map((row) => [row.date, row]));
  const ordered = [...unique.values()].sort((a, b) => a.date.localeCompare(b.date));
  return limit > 0 ? ordered.slice(-limit) : ordered;
}

function readTdxDayHistory(file, limit = 0) {
  const buffer = readFileSync(file);
  const history = [];
  const usableLength = buffer.length - (buffer.length % TDX_DAY_RECORD_SIZE);
  for (let offset = 0; offset < usableLength; offset += TDX_DAY_RECORD_SIZE) {
    const row = parseTdxDayRecord(buffer, offset);
    if (row) history.push(row);
  }
  history.sort((a, b) => a.date.localeCompare(b.date));
  return limit > 0 ? history.slice(-limit) : history;
}

async function queryTdxHistory(rawSymbol, rawLimit, forceIndex = false) {
  const normalized = normalizeHistorySymbol(rawSymbol);
  if (!normalized) throw new Error('需要六位股票代码，可附带 .SH、.SZ 或 .BJ');
  const index = await buildTdxHistoryIndex(forceIndex);
  let entry = index.symbols?.[normalized.key];
  if (!entry && !forceIndex) {
    const refreshed = await buildTdxHistoryIndex(true);
    entry = refreshed.symbols?.[normalized.key];
  }
  const parsedLimit = rawLimit === '0' ? 0 : Math.max(1, Math.min(Number(rawLimit) || 120, 20000));
  if (entry) {
    const configuredTdxRoot = bridgeTdxRoot();
    const selectedTdxRoot = index.source_available === false ? configuredTdxRoot : (index.source_root || configuredTdxRoot);
    const tdxRoot = selectedTdxRoot ? path.resolve(selectedTdxRoot) : '';
    if (tdxRoot) {
      const sourceFile = path.resolve(tdxRoot, entry.file);
      try {
        if (existsSync(sourceFile)) {
          const history = readTdxDayHistory(sourceFile, parsedLimit);
          if (history.length) {
            return {
              status: 'ok', quality: 'primary', symbol: entry.symbol, code: entry.code, market: entry.market,
              source: 'Tongdaxin local .day · indexed lookup', source_root: tdxRoot, source_file: sourceFile,
              index_path: TDX_HISTORY_INDEX_FILE, daily_data_index_path: DAILY_DATA_INDEX_FILE,
              history_scope: 'FULL_LOCAL_TDX_FILE', full_history_verified: history.length === entry.record_count || parsedLimit === 0,
              history_count: entry.record_count, returned_count: history.length, first_date: entry.first_date,
              last_date: entry.last_date, data_date: entry.last_date, history,
            };
          }
        }
      } catch { /* TDX 文件在查询期间不可读，继续走本地 canonical 降级层 */ }
    }
  }
  // A packaged data installer contains the complete canonical daily archive.
  // Use it before the small public fallback layer when the selected TDX
  // directory is missing, stale, or temporarily locked by the client.
  const canonical = await readCanonicalDailyHistory(normalized, parsedLimit, false);
  if (canonical?.history?.length) {
    return {
      status: 'ok', quality: 'canonical', symbol: normalized.symbol, code: normalized.code, market: normalized.market,
      source: 'Packaged canonical daily archive · indexed lookup', source_root: DATA_ROOT, source_file: CANONICAL_DAILY_FILE,
      index_path: canonical.index ? CANONICAL_DAILY_INDEX_FILE : TDX_HISTORY_INDEX_FILE,
      daily_data_index_path: DAILY_DATA_INDEX_FILE,
      history_scope: 'FULL_PACKAGED_CANONICAL_ARCHIVE', full_history_verified: parsedLimit === 0,
      history_count: canonical.total, returned_count: canonical.history.length,
      first_date: canonical.history[0].date, last_date: canonical.history.at(-1).date,
      data_date: canonical.history.at(-1).date, history: canonical.history,
      cautions: ['通达信当前目录不可读或目标 .day 文件不可用；本次读取使用安装到 EXE 资源库的全历史日线归档。'],
    };
  }
  const fallback = readPublicDailyFallbackHistory(normalized, parsedLimit);
  if (fallback.length) {
    return {
      status: 'ok', quality: 'degraded', degraded: true, symbol: normalized.symbol, code: normalized.code, market: normalized.market,
      source: 'Public daily fallback · indexed lookup', source_root: DATA_ROOT, source_file: null,
      index_path: TDX_HISTORY_INDEX_FILE, daily_data_index_path: DAILY_DATA_INDEX_FILE,
      history_scope: 'PUBLIC_FALLBACK_EXACT_DATES', full_history_verified: false, history_count: fallback.length,
      returned_count: fallback.length, first_date: fallback[0].date, last_date: fallback[fallback.length - 1].date,
      data_date: fallback[fallback.length - 1].date, history: fallback,
      cautions: ['通达信源目录当前不可用或目标文件缺失；仅返回已通过日期校验的公开降级记录，不能视为全历史 TDX 数据。'],
    };
  }
  return { status: 'missing', symbol: normalized.symbol, index_path: TDX_HISTORY_INDEX_FILE, daily_data_index_path: DAILY_DATA_INDEX_FILE, error: entry ? '通达信日线文件不可读，且应用内公开降级层没有该股票的已核验记录' : '本地 TDX 日线索引与应用内公开降级索引中都没有该股票' };
}

function readText(file, limit = 240000) {
  try {
    const value = readFileSync(file, 'utf8');
    return value.length > limit ? `${value.slice(0, limit)}\n\n[内容已截断]` : value;
  } catch { return ''; }
}

// Harness 任务记录落盘后，网页重新打开也能恢复指定技能的最新结果。
// 只读取 jobs 目录中的已完成任务，避免把 SKILL.md、提示词或中间日志误当成报告。
function latestHarnessSkillJob(skillId) {
  if (!skillId || !existsSync(HARNESS_JOBS_ROOT)) return null;
  const jobs = readdirSync(HARNESS_JOBS_ROOT)
    .filter((name) => name.toLowerCase().endsWith('.json'))
    .map((name) => readJson(path.join(HARNESS_JOBS_ROOT, name)))
    .filter((job) => job && job.skill_id === skillId && job.status === 'completed' && typeof job.output === 'string' && job.output.trim())
    .sort((a, b) => Number(b.completed_at || b.started_at || 0) - Number(a.completed_at || a.started_at || 0));
  return jobs[0] || null;
}

// 原始策略通常把完整报告写入文件，只在 stdout 返回 REPORT/ANALYSIS_JSON
// 路径。将这些产物随任务结果返回，网页才能展示结构化内容，而不是只显示
// canonical receipt 的原始 JSON。
function collectStrategyStructured(receipt, combined = '', skillId = '') {
  // Python receipt paths can be mojibake when they pass through a Windows
  // console. Resolve the run by its stable timestamp directory name under
  // the bridge data root instead of trusting the rendered drive prefix.
  let fullReceipt = null;
  const receiptPath = String(receipt?.receipt || '');
  if (receiptPath) {
    const receiptName = path.basename(receiptPath);
    const candidate = path.join(DATA_ROOT, 'strategy-results', 'executions', receiptName);
    fullReceipt = readJson(existsSync(receiptPath) ? receiptPath : candidate);
  }
  const rawRunDir = String(fullReceipt?.run_dir || receipt?.run_dir || '');
  const stdoutMatch = combined.match(/[\\/]runs[\\/](\d{8}-\d{6}-\d{6})[\\/]business_child\.stdout\.txt/i);
  const runName = stdoutMatch?.[1] || (rawRunDir ? path.basename(rawRunDir) : '');
  const fallbackRunDir = runName
    ? path.join(DATA_ROOT, 'strategy-results', 'executions', 'runs', runName)
    : '';
  const runDir = rawRunDir && existsSync(rawRunDir) ? rawRunDir : fallbackRunDir;
  const childStdoutPath = path.join(runDir, 'business_child.stdout.txt');
  const childStdout = childStdoutPath ? readText(childStdoutPath, 32000) : '';
  const findPath = (label) => {
    const match = childStdout.match(new RegExp(`^${label}=(.+)$`, 'm'));
    return match ? match[1].trim() : '';
  };
  let reportPath = findPath('REPORT');
  let analysisPath = findPath('ANALYSIS_JSON');
  const derivedPath = findPath('DERIVED_JSON');
  let reportMarkdown = reportPath ? readText(reportPath) : '';
  let analysis = analysisPath ? readJson(analysisPath) : null;
  const derived = derivedPath ? readJson(derivedPath) : null;
  // 部分原始策略返回的是一行 JSON 摘要，其中 report 字段指向完整交付物，
  // 而不是打印 REPORT= 标记。解析该摘要即可把结构化报告交给网页。
  if (!reportMarkdown && !analysis && childStdout) {
    try {
      const summary = JSON.parse(childStdout);
      const candidate = typeof summary?.report === 'string' ? summary.report : '';
      if (candidate) {
        reportPath = existsSync(candidate) ? candidate : path.join(APP_ROOT, candidate);
        reportMarkdown = readText(reportPath);
        analysisPath = reportPath;
        analysis = readJson(reportPath);
      }
    } catch { /* 摘要不是 JSON 时继续使用显式标记或回退报告 */ }
  }
  if (!reportMarkdown && !analysis && !derived) return null;
  return {
    reportPath,
    analysisPath,
    derivedPath,
    reportMarkdown,
    analysis,
    derived,
  };
}

function dailySnapshotSummary(dailyIntegritySnapshot = null) {
  const publicSnapshot = readJson(path.join(DATA_ROOT, 'public', 'latest.json'));
  const newsSnapshot = readJson(path.join(DATA_ROOT, 'news', 'latest.json'));
  const supplementalDate = String(publicSnapshot?.date || '').replace(/\D/g, '');
  const supplementalSnapshot = supplementalDate ? readSupplementalSnapshot(supplementalDate) : readJson(SUPPLEMENTAL_LATEST_FILE);
  const publicSources = publicSnapshot?.sources && typeof publicSnapshot.sources === 'object'
    ? Object.fromEntries(Object.entries(publicSnapshot.sources).map(([name, source]) => {
      const value = source && typeof source === 'object' ? source : {};
      const data = value.data && typeof value.data === 'object' ? value.data : {};
      const records = Array.isArray(data.records) ? data.records.length
        : Array.isArray(data?.data?.pool) ? data.data.pool.length
          : Array.isArray(data?.result?.data) ? data.result.data.length
            : name === 'lianban' && Array.isArray(data.themes) ? data.themes.length + (data.kpi ? 1 : 0) : null;
      return [name, {
        status: value.status || 'unknown', url: value.url || '', sha256: value.sha256 || '', bytes: value.bytes || 0,
        recordCount: records, providerSuccess: data.success ?? (name === 'eastmoneyLimitUp' ? data.rc === 0 : name === 'lianban' ? Boolean(data.kpi) : value.status === 'available' ? true : value.status === 'missing' ? false : null), providerMessage: data.message ?? value.error ?? null,
      }];
    })) : {};
  const kpi = publicSnapshot?.sources?.lianban?.data?.kpi || {};
  const up = Number(kpi.adv || 0), down = Number(kpi.dec || 0);
  const newsSource = newsSnapshot?.source && typeof newsSnapshot.source === 'object' ? newsSnapshot.source : {};
  const dailyIntegrity = dailyIntegritySnapshot || inspectTdxDailyIntegrity();
  const localDataPage = readJson(path.join(HARNESS_CONTEXT_ROOT, 'local-data-page.json'));
  const dailyDataIndex = readJson(DAILY_DATA_INDEX_FILE);
  const dailyDataSummary = dailyDataIndex?.summary || { symbol_count: 0, fallback_symbol_count: 0, fallback_record_count: 0, date_count: 0 };
  return {
    localDataPage,
    publicMarket: {
      schema: publicSnapshot?.schema || '', date: publicSnapshot?.date || '', fetchedAt: publicSnapshot?.fetchedAt || '', sources: publicSources,
      marketBreadth: { currentCount: up + down, up, down, flat: 0, limitUp: Number(kpi.limit_up || 0), limitDown: Number(kpi.limit_down || 0), lianban: Number(kpi.lianban || 0) },
    },
    tdxDailyIntegrity: dailyIntegrity.integrity ? {
      reportPath: dailyIntegrity.integrityReportPath,
      targetDate: dailyIntegrity.integrity.targetDate || dailyIntegrity.latestDate,
      stockListCount: dailyIntegrity.stockListCount,
      stockCompleteCount: dailyIntegrity.stockCompleteCount,
      stockMissingCount: dailyIntegrity.stockMissingCount,
      complete: dailyIntegrity.integrity.complete,
      // 完整清单保留在本地 integrity JSON/Markdown；Harness 上下文只带
      // 少量示例和计数，避免数千条 stale 记录导致校验提示超时。
      unresolved: dailyIntegrity.integrity.unresolved.slice(0, 100),
      unresolvedCount: dailyIntegrity.integrity.unresolved.length,
      repairs: dailyIntegrity.integrity.repairs.filter((item) => item && item.status === 'written').slice(0, 100),
      repairAttempts: dailyIntegrity.integrity.repairs.slice(0, 100),
      repairAttemptsCount: dailyIntegrity.integrity.repairs.length,
      refreshSubmissionCount: Number(dailyIntegrity.integrity.refreshSubmissionCount || dailyIntegrity.integrity.repairs.filter((item) => item?.status === 'refresh_submitted').length),
      writtenCount: Number(dailyIntegrity.integrity.writtenCount || dailyIntegrity.integrity.repairs.filter((item) => item?.status === 'written').length),
      manualActionRequired: dailyIntegrity.integrity.manualActionRequired === true,
      manualAction: String(dailyIntegrity.integrity.manualAction || ''),
      nonTrading: dailyIntegrity.integrity.nonTrading.slice(0, 100),
      nonTradingCount: dailyIntegrity.integrity.nonTrading.length,
    } : {
      reportPath: dailyIntegrity.integrityReportPath,
      targetDate: dailyIntegrity.latestDate,
      stockListCount: dailyIntegrity.stockListCount,
      stockCompleteCount: dailyIntegrity.stockCompleteCount,
      stockMissingCount: dailyIntegrity.stockMissingCount,
      complete: dailyIntegrity.complete,
      unresolved: [], repairs: [],
    },
    dailyDataIndex: {
      path: DAILY_DATA_INDEX_FILE,
      status: dailyDataIndex?.schema === 'ZHANGCAI_DAILY_DATA_INDEX_V1' ? 'available' : 'missing',
      sourcePrecedence: dailyDataIndex?.source_precedence || ['tdx_local_day', 'tdx_archive', 'public_daily_fallback'],
      summary: dailyDataSummary,
      dates: Object.fromEntries(Object.entries(dailyDataIndex?.dates || {}).slice(-10)),
    },
    news: {
      schema: newsSnapshot?.schema || '', date: newsSnapshot?.date || '', status: newsSnapshot?.status || 'missing', fetchedAt: newsSnapshot?.fetchedAt || '',
      sameDayRecordCount: newsSnapshot?.sameDayRecordCount || 0, source: {
        url: newsSource.url || '', httpStatus: newsSource.httpStatus || null, sha256: newsSource.sha256 || '', bytes: newsSource.bytes || 0,
        providerCode: newsSource.providerCode ?? null, recordCount: Array.isArray(newsSource.records) ? newsSource.records.length : 0,
      },
    },
    supplemental: supplementalSnapshot ? {
      status: supplementalSnapshot.status === 'completed' ? 'available' : supplementalSnapshot.status || 'available',
      path: supplementalSnapshot.snapshot_path || path.join(SUPPLEMENTAL_ROOT, supplementalDate, 'market.json'),
      date: supplementalSnapshot.trade_date || supplementalSnapshot.requested_date || '',
      generatedAt: supplementalSnapshot.generated_at || '',
      coverage: supplementalSnapshot.coverage || {},
      indexSymbolCount: supplementalSnapshot.market?.index_daily?.data?.symbol_count || 0,
      lhbRecordCount: supplementalSnapshot.market?.longhubang?.data?.record_count || 0,
      lhbMarketRecordCount: supplementalSnapshot.market?.longhubang?.data?.market_record_count || 0,
      marginRecordCount: supplementalSnapshot.market?.margin?.data?.record_count || 0,
      marginExactDate: supplementalSnapshot.market?.margin?.data?.exact_record_count || 0,
      marginLatestAvailableDate: supplementalSnapshot.market?.margin?.latest_available_date || '',
    } : { status: 'missing', path: path.join(SUPPLEMENTAL_ROOT, supplementalDate, 'market.json'), date: supplementalDate, coverage: {} },
  };
}

function latestFormulaReceipt(symbol = '') {
  const root = path.join(DATA_ROOT, 'evidence', 'formulas');
  if (!existsSync(root)) return null;
  const files = [];
  const queue = [{ directory: root, depth: 0 }];
  while (queue.length) {
    const current = queue.shift();
    if (!current) continue;
    let entries = [];
    try { entries = readdirSync(current.directory, { withFileTypes: true }); } catch { continue; }
    for (const entry of entries) {
      const file = path.join(current.directory, entry.name);
      if (entry.isDirectory() && current.depth < 3) queue.push({ directory: file, depth: current.depth + 1 });
      else if (entry.isFile() && entry.name.toLowerCase().endsWith('.json')) files.push(file);
    }
  }
  const expectedSymbol = String(symbol || '').trim().toUpperCase();
  const valid = files.map((file) => ({ file, value: readJson(file) })).filter(({ value }) => {
    const formulas = value?.formulas;
    return value?.schema === 'ZHANGCAI_TDX_TQ_FORMULA_RECEIPT_V1'
      && (!expectedSymbol || String(value.symbol || '').trim().toUpperCase() === expectedSymbol)
      && Array.isArray(formulas)
      && formulas.length >= 5
      && Array.isArray(value.failed_formulas)
      && value.failed_formulas.length === 0
      && formulas.every((item) => item && item.ok === true);
  });
  valid.sort((a, b) => String(a.value.executed_at || '').localeCompare(String(b.value.executed_at || '')));
  const latest = valid.at(-1);
  if (!latest) return null;
  return {
    path: dataRelativePath(latest.file),
    executedAt: latest.value.executed_at || '',
    dataDate: latest.value.data_date || '',
    symbol: latest.value.symbol || '',
    source: latest.value.source || '',
    formulas: latest.value.formulas,
    failedFormulas: latest.value.failed_formulas,
  };
}

function formulaReceiptFallback(symbol, reason = '') {
  const receipt = latestFormulaReceipt(symbol);
  if (!receipt) return null;
  return {
    status: 'degraded',
    symbol: receipt.symbol || symbol,
    source: 'resource-library · tdx_tq_formula receipt',
    elapsed_ms: 0,
    formulas: receipt.formulas,
    failed_formulas: [],
    client_open_required: false,
    resource_library_fallback: true,
    receipt_path: receipt.path,
    live_error: reason,
    action: '当前使用资源库最近一次完整五公式回执；如需实时刷新，请绑定并打开通达信客户端。',
  };
}

function resourceLibraryContext() {
  const status = readJson(path.join(DATA_ROOT, 'status', 'current.json')) || {};
  const statusAssets = status.assets && typeof status.assets === 'object' ? status.assets : {};
  const publicMarket = readJson(path.join(DATA_ROOT, 'public', 'latest.json')) || {};
  const publicResearchPrimaryFile = path.join(DATA_ROOT, 'evidence', 'public', 'latest.json');
  const publicResearchFallbackFile = path.join(DATA_ROOT, 'evidence', 'public', 'fallback-latest.json');
  const newsLatestFile = path.join(DATA_ROOT, 'news', 'latest.json');
  const publicResearchPrimary = readJson(publicResearchPrimaryFile) || {};
  const publicResearchFallback = readJson(publicResearchFallbackFile) || {};
  const newsLatest = readJson(newsLatestFile) || {};
  const researchStats = (value) => {
    const snapshot = value?.snapshot && typeof value.snapshot === 'object' ? value.snapshot : value;
    let records = Array.isArray(snapshot?.records) ? snapshot.records.filter((row) => row && typeof row === 'object') : [];
    if (!records.length && snapshot?.providers && typeof snapshot.providers === 'object') {
      records = Object.values(snapshot.providers).flatMap((provider) => Array.isArray(provider?.records) ? provider.records : []);
    }
    if (!records.length && snapshot?.source && Array.isArray(snapshot.source.records)) records = snapshot.source.records;
    const recordDates = records.map((row) => String(row?.source_timestamp || row?.publishedAt || row?.published_at || row?.publish_time || row?.date || '').match(/\d{4}-\d{1,2}-\d{1,2}/)?.[0] || '').filter(Boolean).map((date) => {
      const [year, month, day] = date.split('-');
      return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
    });
    const targetDate = String(value?.requested_trade_date || value?.requested_date || value?.target_date || value?.date || snapshot?.requested_date || snapshot?.date || '').replace(/\//g, '-').slice(0, 10);
    const sameDayRecordCount = records.filter((row) => {
      const raw = String(row?.source_timestamp || row?.publishedAt || row?.published_at || row?.publish_time || row?.date || '').match(/\d{4}-\d{1,2}-\d{1,2}/)?.[0] || '';
      if (!raw || !targetDate) return false;
      const [year, month, day] = raw.split('-');
      return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}` === targetDate;
    }).length;
    const fallbackKind = String(value?.fallback_kind || '');
    const providers = new Set(records.flatMap((row) => Array.isArray(row?.providers) ? row.providers : [row?.provider || row?.source].filter(Boolean)).map(String));
    return { snapshot, recordCount: records.length, latestRecordDate: recordDates.sort().at(-1) || '', sameDayRecordCount, targetDate, fallbackKind, providerCounts: value?.context_provider_counts || value?.provider_counts || snapshot?.provider_records || {}, providerNames: [...providers] };
  };
  const primaryStats = researchStats(publicResearchPrimary);
  const newsStats = researchStats(newsLatest);
  const fallbackStats = researchStats(publicResearchFallback);
  // A market-only fallback is useful context but must never mask real news
  // that was already downloaded to news/latest.json.
  const selectedResearch = primaryStats.recordCount > 0 && !primaryStats.fallbackKind
    ? [publicResearchPrimary, publicResearchPrimaryFile, primaryStats]
    : newsStats.recordCount > 0 && !newsStats.fallbackKind
      ? [newsLatest, newsLatestFile, newsStats]
      : primaryStats.fallbackKind
        ? [publicResearchPrimary, publicResearchPrimaryFile, primaryStats]
        : fallbackStats.recordCount > 0
          ? [publicResearchFallback, publicResearchFallbackFile, fallbackStats]
          : existsSync(publicResearchPrimaryFile)
            ? [publicResearchPrimary, publicResearchPrimaryFile, primaryStats]
            : [newsLatest, newsLatestFile, newsStats];
  const [publicResearch, publicResearchFile, selectedResearchStats] = selectedResearch;
  const formulaManifestFile = path.join(DATA_ROOT, 'evidence', 'formulas', 'package', 'manifest.json');
  const formulaManifest = readJson(formulaManifestFile) || {};
  const formulaPackageRoot = path.dirname(formulaManifestFile);
  const formulaRequiredFiles = Array.isArray(formulaManifest.required_files) && formulaManifest.required_files.length
    ? formulaManifest.required_files.map((item) => String(item).replace(/\\/g, '/'))
    : [
      'T0002/PriLoc.dat',
      'T0002/PriGS.dat',
      'T0002/PriCS.dat',
      'T0002/PriPack.dat',
      'T0002/gs_bak/大牛线撑压版.tn6',
      'T0002/gs_bak/飞龙在天.tn6',
      'T0002/gs_bak/游资资金监控.tn6',
      'T0002/gs_bak/机构资金监控.tn6',
      'T0002/gs_bak/庄家资金监控.tn6',
      'T0002/gs_bak/黄金点火选股.tn6',
      'PYPlugins/user/tdxdata_test.py',
    ];
  const formulaMissingFiles = formulaRequiredFiles.filter((item) => !existsSync(path.join(formulaPackageRoot, item)));
  const formulaCopiedFiles = formulaRequiredFiles.filter((item) => existsSync(path.join(formulaPackageRoot, item)));
  const formulaPackageStatus = formulaRequiredFiles.length === 0
    ? 'missing'
    : formulaMissingFiles.length === 0
      ? 'available'
      : formulaCopiedFiles.length
        ? 'degraded'
        : 'missing';
  const formulaAsset = statusAssets.tdx_tq_formula && typeof statusAssets.tdx_tq_formula === 'object'
    ? statusAssets.tdx_tq_formula
    : {};
  const publicAsset = statusAssets.public_research && typeof statusAssets.public_research === 'object'
    ? statusAssets.public_research
    : {};
  const publicSnapshot = selectedResearchStats.snapshot;
  const publicResearchFallbackKind = selectedResearchStats.fallbackKind;
  const publicTargetDate = String(publicAsset.target_date || statusAssets.tdx_daily_history?.trade_date || publicMarket.date || selectedResearchStats.targetDate || '');
  const publicResearchStatus = selectedResearchStats.recordCount > 0
    ? (selectedResearchStats.sameDayRecordCount > 0 && !publicResearchFallbackKind ? 'available' : 'degraded')
    : (publicResearchFallbackKind ? 'degraded' : 'missing');
  const latestReceipt = latestFormulaReceipt();
  const formulaRuntimeStatus = formulaAsset.status === 'available' || latestReceipt
    ? 'available'
    : formulaAsset.status === 'degraded' || formulaPackageStatus !== 'missing'
      ? 'degraded'
      : 'missing';
  return {
    schema: 'ZHANGCAI_RESOURCE_LIBRARY_CONTEXT_V1',
    generatedAt: new Date().toISOString(),
    root: DATA_ROOT,
    paths: {
      publicMarket: path.join(DATA_ROOT, 'public', 'latest.json'),
      publicResearch: publicResearchFile,
      publicResearchFallback: publicResearchFallbackFile,
      formulaPackage: path.join(DATA_ROOT, 'evidence', 'formulas', 'package'),
      formulaManifest: formulaManifestFile,
      formulaReceipts: path.join(DATA_ROOT, 'evidence', 'formulas'),
      dailyIndex: DAILY_DATA_INDEX_FILE,
      unifiedManifest: path.join(DATA_ROOT, 'evidence', 'sources', 'latest.json'),
    },
    assets: {
      public_research: publicResearchStatus,
      tdx_tq_formula: formulaRuntimeStatus,
      security_master: statusAssets.security_master?.status || 'missing',
      tdx_daily_history: statusAssets.tdx_daily_history?.status || 'missing',
      unified_source_manifest: statusAssets.unified_source_manifest?.status || 'missing',
    },
    public_research: {
      status: publicResearchStatus,
      path: dataRelativePath(publicResearchFile),
      sourceDate: selectedResearchStats.latestRecordDate || '',
      targetDate: publicTargetDate,
      sameDayRecordCount: selectedResearchStats.sameDayRecordCount,
      contextRecordCount: selectedResearchStats.recordCount,
      providerCounts: selectedResearchStats.providerCounts,
      providers: selectedResearchStats.providerNames,
      fallbackKind: publicResearchFallbackKind,
      reason: publicResearchStatus === 'degraded'
        ? `保留 ${selectedResearchStats.recordCount} 条公开资讯记录（最新来源日 ${selectedResearchStats.latestRecordDate || '未标注'}）；目标日 ${publicTargetDate || '未知'} 同日记录 ${selectedResearchStats.sameDayRecordCount} 条。`
        : publicResearchStatus === 'missing' ? '资源库中尚无可引用的公开资讯记录。' : '',
      fallbackPath: dataRelativePath(publicResearchFallbackFile),
      snapshot: publicSnapshot,
    },
    public_market: {
      status: publicMarket.sources ? 'available' : 'missing',
      path: dataRelativePath(path.join(DATA_ROOT, 'public', 'latest.json')),
      date: publicMarket.date || '',
      sources: publicMarket.sources || {},
    },
    tdx_tq_formula: {
      status: formulaRuntimeStatus,
      path: 'evidence/formulas/',
      package: {
        status: formulaPackageStatus,
        path: 'evidence/formulas/package/',
        requiredFiles: formulaRequiredFiles,
        copiedFiles: formulaCopiedFiles,
        missingFiles: formulaMissingFiles,
        sourceRoot: formulaManifest.source_root || formulaAsset.portable_package?.source_root || '',
      },
      latestReceipt,
      reason: formulaAsset.reason || '',
    },
  };
}

function archiveDateKey(value) {
  return compactDateText(value) || shanghaiDateText().replace(/-/g, '');
}

function archiveStateSteps(state) {
  return Array.isArray(state?.steps)
    ? state.steps.map(({ name, status, script, code, partial, finishedAt, error }) => ({ name, status, script, code, partial, finishedAt, error }))
    : [];
}

function buildHarnessArchiveContext(date, state, archiveType, stateFile) {
  const dateKey = archiveDateKey(date);
  const dateText = displayDateText(dateKey);
  const dailyManifestPath = path.join(DATA_ROOT, 'market', 'daily', dateKey, 'manifest.json');
  const dailyManifest = readJson(dailyManifestPath) || {};
  const dailyAggregate = String(dailyManifest.file || '').trim()
    ? path.join(DATA_ROOT, ...String(dailyManifest.file).split(/[\\/]/))
    : path.join(DATA_ROOT, 'market', 'daily', 'aggregate', 'tdx-bars.jsonl');
  const snapshots = dailySnapshotSummary();
  const context = {
    schema: 'ZHANGCAI_HARNESS_DATA_ARCHIVE_CONTEXT_V1',
    archive_type: archiveType,
    date: dateText,
    date_key: dateKey,
    generatedAt: new Date().toISOString(),
    dataRoot: DATA_ROOT,
    stateFile,
    state: state ? { schema: state.schema, status: state.status, date: state.date, startedAt: state.startedAt, finishedAt: state.finishedAt } : null,
    paths: {
      localDataPage: path.join(HARNESS_CONTEXT_ROOT, 'local-data-page.json'),
      tdxDailyHistory: path.join(DATA_ROOT, 'status', 'tdx-daily-history.json'),
      dailyManifest: dailyManifestPath,
      dailyAggregate,
      tdxDailyIndex: TDX_HISTORY_INDEX_FILE,
      dailyDataIndex: DAILY_DATA_INDEX_FILE,
      dailyJsonlIntegrity: path.join(DATA_ROOT, 'runtime', `daily-jsonl-integrity-${dateKey}.json`),
      publicLatest: path.join(DATA_ROOT, 'public', 'latest.json'),
      newsLatest: path.join(DATA_ROOT, 'news', 'latest.json'),
      supplemental: path.join(DATA_ROOT, 'evidence', 'supplemental', dateKey, 'market.json'),
      unifiedManifest: path.join(DATA_ROOT, 'evidence', 'sources', 'latest.json'),
      unifiedVerification: path.join(DATA_ROOT, 'evidence', 'sources', 'latest-verification.json'),
      packageSourceInventory: path.join(HARNESS_CONTEXT_ROOT, 'package-source-inventory.json'),
      packageSourceGaps: path.join(HARNESS_CONTEXT_ROOT, 'package-source-gap-report.json'),
      state: stateFile,
    },
    localDataPage: readJson(path.join(HARNESS_CONTEXT_ROOT, 'local-data-page.json')),
    tdxDailyHistory: readJson(path.join(DATA_ROOT, 'status', 'tdx-daily-history.json')),
    dailyManifest,
    dailyJsonlIntegrity: readJson(path.join(DATA_ROOT, 'runtime', `daily-jsonl-integrity-${dateKey}.json`)),
    unifiedManifest: readJson(path.join(DATA_ROOT, 'evidence', 'sources', 'latest.json')),
    unifiedVerification: readJson(path.join(DATA_ROOT, 'evidence', 'sources', 'latest-verification.json')),
    packageSourceInventory: readJson(path.join(HARNESS_CONTEXT_ROOT, 'package-source-inventory.json')),
    packageSourceGaps: readJson(path.join(HARNESS_CONTEXT_ROOT, 'package-source-gap-report.json')),
    snapshots,
    steps: archiveStateSteps(state),
    rules: {
      sourcePrecedence: ['tdx_local_day', 'tdx_archive', 'public_daily_fallback'],
      localArchiveIsPrimary: true,
      fallbackMustBeMarkedDegraded: true,
      allWritesStayUnderAppData: true,
    },
  };
  return { dateKey, dateText, context };
}

async function persistHarnessArchiveContext({ date, state, archiveType, stateFile, runValidation = true }) {
  let built = buildHarnessArchiveContext(date, state, archiveType, stateFile);
  const contextFile = path.join(HARNESS_CONTEXT_ROOT, `data-archive-${built.dateKey}.json`);
  const legacyContextFile = archiveType === 'daily'
    ? path.join(HARNESS_CONTEXT_ROOT, `daily-data-${built.dateKey}.json`)
    : archiveType === 'supplemental'
      ? path.join(HARNESS_CONTEXT_ROOT, `supplemental-data-${built.dateKey}.json`)
      : '';
  await writeRuntimeJson(contextFile, built.context);
  if (legacyContextFile) await writeRuntimeJson(legacyContextFile, built.context);
  await writeRuntimeJson(path.join(HARNESS_CONTEXT_ROOT, 'latest-archive.json'), built.context);
  await writeRuntimeJson(path.join(HARNESS_CONTEXT_ROOT, 'latest-data.json'), built.context);
  // The archive files themselves are runtime assets. Refresh the local data
  // page after creating them so its asset status cannot lag behind the
  // Harness context that points to those files.
  try { await runLocalScript('skill14_data_runtime.py', ['status'], 120000, 4000); } catch { /* 归档上下文已落盘，状态页下次刷新可恢复 */ }
  built = buildHarnessArchiveContext(date, state, archiveType, stateFile);
  await writeRuntimeJson(contextFile, built.context);
  if (legacyContextFile) await writeRuntimeJson(legacyContextFile, built.context);
  await writeRuntimeJson(path.join(HARNESS_CONTEXT_ROOT, 'latest-archive.json'), built.context);
  await writeRuntimeJson(path.join(HARNESS_CONTEXT_ROOT, 'latest-data.json'), built.context);

  // When the final context is rebuilt after the Harness call, keep the
  // existing receipt instead of replacing it with a misleading "skipped".
  // This is important because the unified archive state and its context are
  // written in two phases: first while the run is active, then once more
  // after the final status/report has been committed.
  let harness = !runValidation && state?.harness && state.harness.status !== 'pending'
    ? state.harness
    : { status: 'skipped', finishedAt: new Date().toISOString() };
  if (runValidation) {
    try {
      if (!process.env.DEEPSEEK_API_KEY) throw new Error('未设置 DEEPSEEK_API_KEY，已完成本地数据归档但无法进行 Harness 校验');
      const snapshots = built.context.snapshots || {};
      const breadth = snapshots.publicMarket?.marketBreadth || {};
      const output = await runHarnessWithRetry(buildPrompt(
        `这是本地数据源归档后的统一 Harness 校验。归档类型为 ${archiveType}，日期为 ${built.dateText}。以下是本机已经落盘的结构化证据：${JSON.stringify(built.context)}。只能依据这些字段核验文件、日期、来源、哈希、条数、索引、降级层和未覆盖项；禁止重新抓取、执行命令、读取未传入的文件或把历史兼容目录当作当前事实。日线按 sourcePrecedence 使用，public_daily_fallback 必须标记 degraded。${HARNESS_JSON_SCHEMA}`,
        {
          date: built.dateKey,
          currentCount: breadth.currentCount || 0,
          up: breadth.up || 0,
          down: breadth.down || 0,
          flat: breadth.flat || 0,
          amount: 0,
          dataSources: { archiveContext: contextFile, dailyManifest: built.context.paths.dailyManifest, unifiedManifest: built.context.paths.unifiedManifest, dailyIndex: built.context.paths.dailyDataIndex },
          limitCandidates: [{ count: breadth.limitUp || 0, lianban: breadth.lianban || 0 }],
        },
        'market-data-replenishment',
        { contextFile },
      ), 'market-data-replenishment', { inline: true });
      harness = { status: 'completed', finishedAt: new Date().toISOString(), output: output.output, elapsedMs: output.elapsedMs };
    } catch (error) {
      harness = { status: 'failed', finishedAt: new Date().toISOString(), error: error instanceof Error ? error.message : String(error) };
    }
  }
  const finalContext = { ...built.context, harness };
  await writeRuntimeJson(contextFile, finalContext);
  if (legacyContextFile) await writeRuntimeJson(legacyContextFile, finalContext);
  await writeRuntimeJson(path.join(HARNESS_CONTEXT_ROOT, 'latest-archive.json'), finalContext);
  await writeRuntimeJson(path.join(HARNESS_CONTEXT_ROOT, 'latest-data.json'), finalContext);
  await writeRuntimeJson(path.join(HARNESS_CONTEXT_ROOT, `data-archive-validation-${built.dateKey}.json`), finalContext);
  if (archiveType === 'daily') await writeRuntimeJson(path.join(HARNESS_CONTEXT_ROOT, `daily-validation-${built.dateKey}.json`), finalContext);
  if (state) state.harness = harness;
  return { ...built, context: finalContext, contextFile, harness };
}

async function writeRuntimeJsonAtomically(file, value) {
  await mkdir(path.dirname(file), { recursive: true });
  // Runtime state is read by the desktop UI and by the smoke/repair tools while
  // the bridge may be refreshing it.  Writing directly to the final path lets
  // readers observe a truncated JSON document (especially on slower disks).
  // Write a per-operation sibling first, then replace the visible file in one
  // rename so resource-library consumers only ever see a complete document.
  const temporaryFile = `${file}.tmp-${process.pid}-${randomUUID()}`;
  try {
    await writeFile(temporaryFile, JSON.stringify(value, null, 2), 'utf8');
    for (let attempt = 0; ; attempt += 1) {
      try {
        await rename(temporaryFile, file);
        break;
      } catch (error) {
        // Windows can briefly hold the destination while a UI/tool is reading
        // it. A bounded retry keeps the bridge alive without ever exposing a
        // partial JSON document.
        if (!['EPERM', 'EBUSY', 'EACCES'].includes(error?.code) || attempt >= 5) throw error;
        await new Promise((resolve) => setTimeout(resolve, 20 * (attempt + 1)));
      }
    }
  } finally {
    try { await unlink(temporaryFile); } catch { /* already renamed or absent */ }
  }
}

function writeRuntimeJson(file, value) {
  const prior = runtimeJsonWrites.get(file) || Promise.resolve();
  const current = prior.catch(() => undefined).then(() => writeRuntimeJsonAtomically(file, value));
  runtimeJsonWrites.set(file, current);
  void current.finally(() => {
    if (runtimeJsonWrites.get(file) === current) runtimeJsonWrites.delete(file);
  }).catch(() => undefined);
  return current;
}

function compactDateKey(value) {
  const raw = String(value || '').replace(/\D/g, '');
  return /^\d{8}$/.test(raw) ? raw : shanghaiDateText().replace(/-/g, '');
}

function dataRelativePath(file) {
  return path.relative(DATA_ROOT, file).replace(/\\/g, '/');
}

function htmlEscape(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function unifiedArchiveReportDescriptor(date) {
  const dateKey = compactDateKey(date);
  const directory = path.join(UNIFIED_ARCHIVE_REPORT_ROOT, dateKey);
  return {
    date: dateKey,
    directory,
    htmlFile: path.join(directory, 'index.html'),
    jsonFile: path.join(directory, 'report.json'),
    latestHtmlFile: path.join(UNIFIED_ARCHIVE_REPORT_ROOT, 'latest.html'),
    latestJsonFile: path.join(UNIFIED_ARCHIVE_REPORT_ROOT, 'latest.json'),
    htmlUrl: `/data/archive/report?date=${dateKey}`,
    jsonUrl: `/data/archive/report?date=${dateKey}&format=json`,
  };
}

function parseHarnessOutput(output) {
  try {
    const parsed = JSON.parse(String(output || ''));
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch {
    return {};
  }
}

function unifiedArchiveOutputFile(date, index, name, suffix = 'json') {
  const safeName = String(name || 'step').replace(/[^a-zA-Z0-9._\u4e00-\u9fff-]+/g, '_').slice(0, 80);
  const dateKey = compactDateKey(date);
  return path.join(UNIFIED_ARCHIVE_OUTPUT_ROOT, dateKey, `${String(index).padStart(2, '0')}-${safeName}.${suffix}`);
}

async function persistUnifiedStepOutput(date, step, index, result) {
  const output = String(result?.output || '').trim();
  if (!output) return null;
  const file = unifiedArchiveOutputFile(date, index, step?.name, 'json');
  await writeRuntimeJson(file, {
    schema: 'ZHANGCAI_UNIFIED_DATA_ARCHIVE_STEP_OUTPUT_V1',
    date: compactDateKey(date),
    step: step?.name || null,
    script: result?.script || step?.script || null,
    code: result?.code ?? null,
    partial: result?.partial === true,
    generatedAt: new Date().toISOString(),
    output,
  });
  return dataRelativePath(file);
}

function compactUnifiedArchiveState(state) {
  if (!state || typeof state !== 'object') return state;
  const rawHarness = state.harness && typeof state.harness === 'object' ? state.harness : {};
  const parsedHarness = parseHarnessOutput(rawHarness.output);
  const { output: _harnessOutput, ...harnessWithoutOutput } = rawHarness;
  const compactHarness = {
    ...harnessWithoutOutput,
    summary: String(harnessWithoutOutput.summary || parsedHarness.summary || ''),
    dataDate: String(harnessWithoutOutput.dataDate || parsedHarness.data_date || ''),
    cautionCount: Array.isArray(parsedHarness.cautions) ? parsedHarness.cautions.length : Number(harnessWithoutOutput.cautionCount || 0),
    findingCount: Array.isArray(parsedHarness.findings) ? parsedHarness.findings.length : Number(harnessWithoutOutput.findingCount || 0),
    tableCount: Array.isArray(parsedHarness.tables) ? parsedHarness.tables.length : Number(harnessWithoutOutput.tableCount || 0),
  };
  const steps = Array.isArray(state.steps) ? state.steps : [];
  return {
    ...state,
    steps: steps.map((step) => {
      const { output: _stepOutput, ...stepWithoutOutput } = step || {};
      return {
        ...stepWithoutOutput,
        resultStored: Boolean(step?.outputPath || step?.resultPath || step?.output),
      };
    }),
    harness: compactHarness,
  };
}

async function persistUnifiedHarnessOutput(date, harness) {
  const output = String(harness?.output || '').trim();
  if (!output) return null;
  const file = unifiedArchiveOutputFile(date, 99, 'harness', 'json');
  await writeRuntimeJson(file, {
    schema: 'ZHANGCAI_UNIFIED_DATA_ARCHIVE_HARNESS_OUTPUT_V1',
    date: compactDateKey(date),
    generatedAt: new Date().toISOString(),
    status: harness?.status || 'unknown',
    elapsedMs: harness?.elapsedMs ?? null,
    output,
  });
  return dataRelativePath(file);
}

function unifiedArchiveProgress(state) {
  const steps = Array.isArray(state?.steps) ? state.steps : [];
  // The unified pipeline has nine stable stages. Keep that denominator while
  // the next stage has not yet been appended, otherwise 1/1 would briefly
  // look like 100% after the first step.
  const total = Math.max(9, steps.length);
  const completed = steps.filter((step) => ['completed', 'partial', 'failed'].includes(String(step?.status || ''))).length;
  const active = steps.find((step) => step?.status === 'running');
  const failed = steps.filter((step) => ['partial', 'failed'].includes(String(step?.status || ''))).length;
  return {
    completed,
    total,
    percent: Math.min(100, Math.round((completed / total) * 100)),
    currentStep: active?.name || (state?.status === 'running' ? '正在准备下一步' : ''),
    failed,
  };
}

function unifiedArchiveReportPayload(state, context) {
  const report = unifiedArchiveReportDescriptor(state?.date);
  const progress = unifiedArchiveProgress(state);
  const steps = Array.isArray(state?.steps) ? state.steps : [];
  const harness = state?.harness && typeof state.harness === 'object' ? state.harness : {};
  const harnessOutput = parseHarnessOutput(harness.output);
  const manifest = context?.unifiedManifest && typeof context.unifiedManifest === 'object' ? context.unifiedManifest : {};
  const sources = Array.isArray(manifest.sources) ? manifest.sources : [];
  const missingSources = sources
    .filter((source) => !['available', 'partial'].includes(String(source?.status || '')))
    .map((source) => String(source?.name || source?.id || '未命名来源'));
  const cautions = Array.isArray(harnessOutput.cautions) ? harnessOutput.cautions.map(String).slice(0, 20) : [];
  const stepRows = steps.map((step) => ({
    name: String(step?.name || ''),
    status: String(step?.status || 'pending'),
    code: step?.code ?? null,
    startedAt: step?.startedAt || null,
    finishedAt: step?.finishedAt || null,
    error: step?.error ? String(step.error) : '',
    resultPath: step?.resultPath || step?.outputPath || null,
  }));
  const message = state?.status === 'completed'
    ? '统一数据落盘完成，全部步骤已结束。'
    : state?.status === 'partial'
      ? '统一数据落盘完成，但存在降级来源或未通过步骤，请查看缺失项和步骤明细。'
      : state?.status === 'failed'
        ? '统一数据落盘失败，请查看错误步骤和桥接服务日志。'
        : '统一数据落盘正在后台运行，页面会持续更新本报告。';
  return {
    schema: 'ZHANGCAI_UNIFIED_DATA_ARCHIVE_REPORT_V1',
    generatedAt: new Date().toISOString(),
    status: String(state?.status || 'missing'),
    message,
    date: String(state?.date || report.date),
    startedAt: state?.startedAt || null,
    finishedAt: state?.finishedAt || null,
    progress,
    steps: stepRows,
    harness: {
      status: String(harness.status || 'pending'),
      finishedAt: harness.finishedAt || null,
      summary: String(harness.summary || harnessOutput.summary || ''),
      dataDate: String(harness.dataDate || harnessOutput.data_date || ''),
      cautions: Array.isArray(harness.cautions) ? harness.cautions.map(String).slice(0, 20) : cautions,
      cautionCount: Number(harness.cautionCount || cautions.length || 0),
      findingCount: Number(harness.findingCount || (Array.isArray(harnessOutput.findings) ? harnessOutput.findings.length : 0)),
      tableCount: Number(harness.tableCount || (Array.isArray(harnessOutput.tables) ? harnessOutput.tables.length : 0)),
    },
    sources: {
      total: sources.length,
      available: sources.filter((source) => source?.status === 'available').length,
      partial: sources.filter((source) => source?.status === 'partial').length,
      missing: missingSources,
    },
    artifacts: {
      dataRoot: DATA_ROOT,
      reportJson: dataRelativePath(report.jsonFile),
      reportHtml: dataRelativePath(report.htmlFile),
      state: dataRelativePath(UNIFIED_ARCHIVE_STATE_FILE),
      harnessContext: dataRelativePath(path.join(HARNESS_CONTEXT_ROOT, 'latest-archive.json')),
    },
    context: { paths: context?.paths || {} },
    urls: { html: report.htmlUrl, json: report.jsonUrl },
  };
}

function unifiedArchiveReportHtml(payload) {
  const statusClass = payload.status === 'completed' ? 'ok' : payload.status === 'running' ? 'running' : 'warn';
  const statusText = payload.status === 'completed' ? '已完成' : payload.status === 'running' ? '运行中' : payload.status === 'partial' ? '部分完成' : '失败/缺失';
  const fmt = (value) => value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '—';
  const stepRows = payload.steps.map((step) => `<tr><td>${htmlEscape(step.name)}</td><td><span class="pill ${step.status === 'completed' ? 'ok' : step.status === 'running' ? 'running' : 'warn'}">${htmlEscape(step.status)}</span></td><td>${htmlEscape(step.code ?? '—')}</td><td>${htmlEscape(step.error || (step.resultPath ? '详细结果已单独落盘' : '—'))}</td></tr>`).join('');
  const missing = payload.sources.missing.length ? payload.sources.missing.map((item) => `<li>${htmlEscape(item)}</li>`).join('') : '<li>当前来源清单没有标记为缺失的来源</li>';
  const cautions = payload.harness.cautions.length ? payload.harness.cautions.map((item) => `<li>${htmlEscape(item)}</li>`).join('') : '<li>无 Harness 结构化提示</li>';
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>统一数据落盘报告 · ${htmlEscape(payload.date)}</title><style>
body{margin:0;background:#f7f8fa;color:#1f2937;font:14px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif}.wrap{max-width:1180px;margin:28px auto;padding:0 20px}.hero,.card{background:#fff;border:1px solid #e5e7eb;border-radius:12px;box-shadow:0 2px 8px rgba(15,23,42,.04)}.hero{padding:24px 28px;margin-bottom:16px}.hero h1{margin:0 0 6px;font-size:24px}.meta{color:#64748b}.status{display:inline-block;padding:3px 12px;border-radius:999px;font-weight:600}.status.ok,.pill.ok{color:#047857;background:#d1fae5}.status.running,.pill.running{color:#1d4ed8;background:#dbeafe}.status.warn,.pill.warn{color:#b45309;background:#fef3c7}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:16px}.card{padding:16px}.card b{display:block;color:#64748b;font-size:12px;margin-bottom:4px}.card strong{font-size:20px}.section{padding:20px 22px;margin-bottom:16px}.section h2{margin:0 0 12px;font-size:17px}table{width:100%;border-collapse:collapse;table-layout:fixed}th,td{text-align:left;vertical-align:top;border-bottom:1px solid #eef2f7;padding:9px 8px;overflow-wrap:anywhere}th{color:#64748b;background:#f8fafc;font-weight:600}th:nth-child(1){width:25%}th:nth-child(2){width:12%}th:nth-child(3){width:10%}.pill{display:inline-block;border-radius:999px;padding:1px 8px;font-size:12px}.columns{display:grid;grid-template-columns:1fr 1fr;gap:16px}.columns ul{margin:6px 0 0;padding-left:20px}.path{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:12px;overflow-wrap:anywhere;color:#475569}@media(max-width:800px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.columns{grid-template-columns:1fr}}
</style></head><body><main class="wrap"><section class="hero"><h1>统一数据落盘运行报告</h1><div class="meta">数据日期：${htmlEscape(payload.date)} · 生成时间：${fmt(payload.generatedAt)} · <span class="status ${statusClass}">${statusText}</span></div><p>${htmlEscape(payload.message)}</p></section><section class="grid"><div class="card"><b>步骤进度</b><strong>${payload.progress.completed}/${payload.progress.total}</strong><div>${payload.progress.percent}%${payload.progress.currentStep ? ` · ${htmlEscape(payload.progress.currentStep)}` : ''}</div></div><div class="card"><b>Harness 校验</b><strong>${htmlEscape(payload.harness.status)}</strong><div>${fmt(payload.harness.finishedAt)}</div></div><div class="card"><b>来源清单</b><strong>${payload.sources.available}/${payload.sources.total}</strong><div>可用 · 部分 ${payload.sources.partial}</div></div><div class="card"><b>运行时间</b><strong>${fmt(payload.startedAt)}</strong><div>结束：${fmt(payload.finishedAt)}</div></div></section><section class="card section"><h2>步骤状态</h2><table><thead><tr><th>步骤</th><th>状态</th><th>退出码</th><th>结果</th></tr></thead><tbody>${stepRows || '<tr><td colspan="4">尚未开始执行</td></tr>'}</tbody></table></section><section class="columns"><section class="card section"><h2>来源缺失或降级</h2><ul>${missing}</ul></section><section class="card section"><h2>Harness 摘要</h2><div>${htmlEscape(payload.harness.summary || '暂无结构化摘要')}</div><ul>${cautions}</ul></section></section><section class="card section"><h2>本地资产</h2><p>以下路径均位于 resource-library 内，供 EXE 和 Harness 独立读取：</p><div class="path">报告 JSON：${htmlEscape(payload.artifacts.reportJson)}<br>运行状态：${htmlEscape(payload.artifacts.state)}<br>Harness 上下文：${htmlEscape(payload.artifacts.harnessContext)}<br>数据目录：${htmlEscape(payload.artifacts.dataRoot)}</div></section></main></body></html>`;
}

async function writeUnifiedArchiveReport(state, context = null) {
  const descriptor = unifiedArchiveReportDescriptor(state?.date);
  const payload = unifiedArchiveReportPayload(state, context || readJson(path.join(HARNESS_CONTEXT_ROOT, 'latest-archive.json')) || {});
  const html = unifiedArchiveReportHtml(payload);
  await mkdir(descriptor.directory, { recursive: true });
  await writeRuntimeJson(descriptor.jsonFile, payload);
  await writeFile(descriptor.htmlFile, html, 'utf8');
  await writeRuntimeJson(descriptor.latestJsonFile, payload);
  await writeFile(descriptor.latestHtmlFile, html, 'utf8');
  return {
    date: descriptor.date,
    htmlUrl: descriptor.htmlUrl,
    jsonUrl: descriptor.jsonUrl,
    htmlPath: descriptor.htmlFile,
    jsonPath: descriptor.jsonFile,
    relativeHtml: dataRelativePath(descriptor.htmlFile),
    relativeJson: dataRelativePath(descriptor.jsonFile),
    generatedAt: payload.generatedAt,
  };
}

async function saveUnifiedArchiveState(state, context = null) {
  const compacted = compactUnifiedArchiveState(state);
  for (const key of Object.keys(state)) delete state[key];
  Object.assign(state, compacted);
  const report = await writeUnifiedArchiveReport(state, context);
  state.report = report;
  await writeRuntimeJson(UNIFIED_ARCHIVE_STATE_FILE, state);
  return report;
}

async function ensureUnifiedArchiveReport(state) {
  if (!state || typeof state !== 'object') return null;
  const compacted = compactUnifiedArchiveState(state);
  const wasVerbose = JSON.stringify(compacted) !== JSON.stringify(state);
  if (wasVerbose) {
    for (const key of Object.keys(state)) delete state[key];
    Object.assign(state, compacted);
    await writeRuntimeJson(UNIFIED_ARCHIVE_STATE_FILE, state);
  }
  const descriptor = unifiedArchiveReportDescriptor(state.date);
  let report = state.report;
  if (wasVerbose || !existsSync(descriptor.htmlFile) || !existsSync(descriptor.jsonFile)) {
    report = await writeUnifiedArchiveReport(state);
  } else if (!report) {
    report = {
      date: descriptor.date,
      htmlUrl: descriptor.htmlUrl,
      jsonUrl: descriptor.jsonUrl,
      htmlPath: descriptor.htmlFile,
      jsonPath: descriptor.jsonFile,
      relativeHtml: dataRelativePath(descriptor.htmlFile),
      relativeJson: dataRelativePath(descriptor.jsonFile),
    };
  }
  if (report && JSON.stringify(state.report) !== JSON.stringify(report)) {
    state.report = report;
    await writeRuntimeJson(UNIFIED_ARCHIVE_STATE_FILE, state);
  }
  return report;
}

async function persistHarnessReport({ skillId = '', output = '', diagnostics = '', task = '', dataDate = '', jobId = '' }) {
  const date = compactDateText(dataDate) || compactDateText(localTradeDate()) || shanghaiDateText().replace(/-/g, '');
  const safeSkill = String(skillId || 'general').replace(/[^a-zA-Z0-9._-]+/g, '_').slice(0, 80);
  const file = path.join(DATA_ROOT, 'reports', 'daily', date, 'harness', `${safeSkill}-${Date.now()}-${jobId || randomUUID()}.json`);
  const record = {
    schema: 'ZHANGCAI_DEEPSEEK_HARNESS_REPORT_V1',
    generated_at: new Date().toISOString(),
    engine: 'DeepSeek Harness headless',
    application_root: APP_ROOT,
    data_root: DATA_ROOT,
    skill_id: skillId || null,
    data_date: date,
    task,
    diagnostics,
    output,
  };
  await writeRuntimeJson(file, record);
  return file;
}

function safeReportArchiveId(value) {
  const id = String(value || '').trim();
  return /^[a-zA-Z0-9._-]{1,180}$/.test(id) ? id : '';
}

function isHarnessTaskRecord(record) {
  return record?.content?.kind === 'harness-task' || record?.reportType === 'Harness任务';
}

function safeReportArchivePart(value) {
  return String(value || '')
    .trim()
    .replace(/[^a-zA-Z0-9._:-]+/g, '_')
    .slice(0, 160);
}

function reportArchiveDate(value) {
  const digits = String(value || '').replace(/\D/g, '');
  return digits.length >= 8 ? digits.slice(0, 8) : safeReportArchivePart(value) || 'undated';
}

function cleanReportArchiveText(value) {
  return String(value || '')
    .replace(/3004\s+聊天研究报告/g, '聊天完整研究报告')
    .replace(/3004\s+Demo/g, '股票研究工作台')
    .replace(/3004\s+WEB\s+DEMO/g, '研究工作台')
    .replace(/3003\s+app-data\/runtime/g, 'resource-library/runtime')
    .replace(/3003\s+app-data/g, 'resource-library')
    .replace(/3003\s+网页脚本/g, '网页脚本')
    .replace(/3003\s+本地/g, '本地')
    .replace(/3003\s+原始/g, '原始')
    .replace(/3003(?=[\u4e00-\u9fff])/g, '')
    .replace(/3004(?=[\u4e00-\u9fffA-Za-z])/g, '')
    .trim();
}

function normalizeReportArchiveValue(value) {
  if (typeof value === 'string') return cleanReportArchiveText(value);
  if (Array.isArray(value)) return value.map(normalizeReportArchiveValue);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, normalizeReportArchiveValue(item)]));
  }
  return value;
}

function normalizeReportArchiveRecord(record) {
  return {
    ...record,
    title: cleanReportArchiveText(record.title),
    reportType: cleanReportArchiveText(record.reportType),
    generatedBy: cleanReportArchiveText(record.generatedBy),
    summary: cleanReportArchiveText(record.summary),
    dataScope: cleanReportArchiveText(record.dataScope),
    content: normalizeReportArchiveValue(record.content),
    raw: typeof record.raw === 'string' ? cleanReportArchiveText(record.raw) : record.raw,
  };
}

function reportArchiveKey(record) {
  const explicit = safeReportArchivePart(record?.archiveKey);
  if (explicit) {
    const dated = explicit.match(/^(chat|stock|skill14|strategy|golden|mainline|market):([^:]+):(.*)$/);
    return dated ? `${dated[1]}:${reportArchiveDate(dated[2])}:${dated[3]}` : explicit;
  }
  const content = record?.content && typeof record.content === 'object' ? record.content : {};
  const kind = String(content.kind || '');
  const date = reportArchiveDate(record?.date);
  const reportLabel = `${record?.title || ''} ${record?.reportType || ''}`;
  if (kind === 'market-report' || /行情复盘|历史复盘|结构化复盘|Harness 复盘/.test(reportLabel)) return 'market-review';
  if (kind === 'chat-report') {
    const skill = Number(content.planLength || 0) > 1 ? 'complete-plan' : safeReportArchivePart(content.skillId || 'complete-plan');
    const targets = Array.isArray(content.targetStocks)
      ? content.targetStocks.map((stock) => `${safeReportArchivePart(stock?.market || 'XX')}${safeReportArchivePart(stock?.code || stock?.name || 'market')}`).sort().join('_')
      : '';
    return `chat:${date}:${targets || 'market'}:${skill}`;
  }
  if (kind === 'stock-research') {
    const stock = content.stock && typeof content.stock === 'object' ? content.stock : {};
    return `stock:${date}:${safeReportArchivePart(stock.code || 'unknown-stock')}:${safeReportArchivePart(record?.generatedBy || 'stock-research')}`;
  }
  if (kind === 'harness-skill') return `skill14:${date}:${safeReportArchivePart(content.skillId || record?.generatedBy || 'unknown-skill')}`;
  if (kind === 'strategy-selection-harness' || kind === 'strategy-run') return `strategy:${date}:${safeReportArchivePart(content.strategyId || record?.generatedBy || 'unknown-strategy')}`;
  if (kind === 'golden-ignition-single-signal') {
    const result = content.result && typeof content.result === 'object' ? content.result : {};
    return `golden:${date}:${safeReportArchivePart(result.analysis_symbol || result.symbol || 'unknown-stock')}`;
  }
  return `report:${date}:${safeReportArchivePart(record?.reportType || kind || record?.title || 'general')}`;
}

function reportArchiveTimestamp(value) {
  if (typeof value === 'number' && Number.isFinite(value)) return value < 1e12 ? value * 1000 : value;
  const text = String(value || '').trim();
  if (!text) return 0;
  const numeric = Number(text);
  if (Number.isFinite(numeric) && numeric > 0) return numeric < 1e12 ? numeric * 1000 : numeric;
  const digits = text.replace(/\D/g, '');
  if (digits.length >= 14) {
    const timestamp = Date.UTC(
      Number(digits.slice(0, 4)), Number(digits.slice(4, 6)) - 1, Number(digits.slice(6, 8)),
      Number(digits.slice(8, 10)), Number(digits.slice(10, 12)), Number(digits.slice(12, 14)),
    );
    if (Number.isFinite(timestamp)) return timestamp;
  }
  if (digits.length >= 8) {
    const timestamp = Date.UTC(Number(digits.slice(0, 4)), Number(digits.slice(4, 6)) - 1, Number(digits.slice(6, 8)));
    if (Number.isFinite(timestamp)) return timestamp;
  }
  const parsed = Date.parse(text);
  return Number.isFinite(parsed) ? parsed : 0;
}

function collapseReportArchiveRows(records) {
  const latest = new Map();
  const sorted = [...records]
    .map(normalizeReportArchiveRecord)
    .filter((item) => item && typeof item.id === 'string' && !isHarnessTaskRecord(item))
    .sort((a, b) => (
      reportArchiveTimestamp(b.updatedAt || b.createdAt) - reportArchiveTimestamp(a.updatedAt || a.createdAt)
      || String(b.id || '').localeCompare(String(a.id || ''))
    ));
  for (const item of sorted) {
    const key = reportArchiveKey(item);
    if (!latest.has(key)) latest.set(key, { ...item, archiveKey: key });
  }
  return [...latest.values()].slice(0, 100);
}

function readRawLocalReportArchive() {
  const indexed = readJson(REPORT_ARCHIVE_INDEX_FILE, null);
  if (Array.isArray(indexed)) return indexed;
  if (!existsSync(REPORT_ARCHIVE_ROOT)) return [];
  try {
    return readdirSync(REPORT_ARCHIVE_ROOT)
      .filter((name) => name.toLowerCase().endsWith('.json') && name !== 'index.json')
      .map((name) => readJson(path.join(REPORT_ARCHIVE_ROOT, name), null))
      .filter((item) => item && typeof item.id === 'string');
  } catch { return []; }
}

function readLocalReportArchive() {
  return collapseReportArchiveRows(readRawLocalReportArchive());
}

let reportArchiveMutationTail = Promise.resolve();
function runReportArchiveMutation(operation) {
  const current = reportArchiveMutationTail.then(operation, operation);
  reportArchiveMutationTail = current.then(() => undefined, () => undefined);
  return current;
}

async function persistLocalReportArchive(record) {
  return runReportArchiveMutation(async () => {
  const id = safeReportArchiveId(record?.id);
  if (!id) throw new Error('报告缺少合法 ID');
  if (isHarnessTaskRecord(record)) {
    return { status: 'ignored', id, reason: '任务状态只保留在后台任务缓存，不作为第二份报告归档', count: readLocalReportArchive().length };
  }
  const normalized = { ...record, archiveKey: reportArchiveKey(record) };
  const existing = readRawLocalReportArchive().filter((item) => item.id !== id);
  const next = collapseReportArchiveRows([normalized, ...existing]);
  const keepIds = new Set(next.map((item) => item.id));
  // Commit the new record and index before removing superseded per-report
  // files. A failed index write must not destroy the last visible report.
  await writeRuntimeJson(path.join(REPORT_ARCHIVE_ROOT, `${id}.json`), normalized);
  await writeRuntimeJson(REPORT_ARCHIVE_INDEX_FILE, next);
  for (const item of existing) {
    if (item?.id && !keepIds.has(item.id)) {
      const staleId = safeReportArchiveId(item.id);
      if (staleId) {
        try { await unlink(path.join(REPORT_ARCHIVE_ROOT, `${staleId}.json`)); } catch { /* 已不存在 */ }
      }
    }
  }
  return { status: 'ok', id, path: path.join(DATA_ROOT, 'reports', 'archive', `${id}.json`), count: next.length };
  });
}

async function deleteLocalReportArchive(id) {
  return runReportArchiveMutation(async () => {
  const safeId = safeReportArchiveId(id);
  if (!safeId) throw new Error('报告 ID 无效');
  const next = readLocalReportArchive().filter((item) => item.id !== safeId);
  await writeRuntimeJson(REPORT_ARCHIVE_INDEX_FILE, next);
  try { await unlink(path.join(REPORT_ARCHIVE_ROOT, `${safeId}.json`)); } catch { /* 文件已不存在 */ }
  return { status: 'ok', id: safeId, count: next.length };
  });
}

function readableScriptError(scriptName, raw, code = 1) {
  const text = String(raw || '').trim();
  // tqcenter 在部分 Windows 环境会把 GBK 异常按 UTF-8 解码，原始
  // Traceback 既不可读也会把内部路径暴露到页面。行情刷新只返回用户
  // 能采取行动的提示，详细诊断仍保留在桥接服务日志中。
  if (scriptName === 'market_overview_refresh.py' && (/Traceback|tqcenter|TQ|RuntimeError|�/.test(text))) {
    return '通达信实时行情刷新失败：请确认通达信已打开并登录；若已打开，请稍后重试以释放 TQ 数据连接。';
  }
  if (scriptName === 'tdx_daily_integrity.py' && (/Traceback|tqcenter|TQ|RuntimeError|超时|�/.test(text))) {
    return '通达信日线补齐未完成：请确认 TdxW 已打开并登录，点击“打开通达信”后重新执行；全量下载允许后台运行至 10 分钟。';
  }
  return (text || `${scriptName} 退出码 ${code}`).slice(-2000);
}

function runLocalScript(scriptName, args = [], timeoutMs = 600000, outputLimit = 12000, acceptedExitCodes = [], extraEnv = {}) {
  return new Promise((resolve, reject) => {
    const python = localPythonExecutable();
    const script = path.join(APP_ROOT, 'scripts', scriptName);
    const child = spawn(python, [script, ...args], {
      cwd: APP_ROOT,
      windowsHide: true,
      env: localScriptEnvironment(extraEnv),
    });
    let stdout = '';
    let stderr = '';
    const timer = setTimeout(() => {
      if (child.pid) spawn('taskkill', ['/pid', String(child.pid), '/t', '/f'], { windowsHide: true });
      reject(new Error(`${scriptName} 超时（${Math.round(timeoutMs / 1000)} 秒）`));
    }, timeoutMs);
    child.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
    child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
    child.on('error', (error) => { clearTimeout(timer); reject(error); });
    child.on('close', (code) => {
      clearTimeout(timer);
      if (code !== 0 && !acceptedExitCodes.includes(code)) {
        reject(new Error(readableScriptError(scriptName, stderr || stdout, code)));
        return;
      }
      resolve({ script: scriptName, code, partial: code !== 0, output: outputLimit > 0 ? stdout.trim().slice(-outputLimit) : stdout.trim() });
    });
  });
}

async function runSelectionScoreRuntime(payload) {
  const runId = randomUUID();
  const requestPath = path.join(DATA_ROOT, 'strategy-results', 'selection-runtime', 'requests', `${runId}.json`);
  await writeRuntimeJson(requestPath, payload);
  try {
    const result = await runLocalScript('selection_score_runtime.py', [requestPath], 600000, 4 * 1024 * 1024);
    let value;
    try { value = JSON.parse(result.output || '{}'); } catch { throw new Error('原始策略评分运行时返回了无效 JSON'); }
    if (!value || value.status !== 'ok') throw new Error(String(value?.error || '原始策略评分运行时失败'));
    const resultDate = String(value.trade_date || payload?.date || localTradeDate()).replace(/[^0-9]/g, '').slice(0, 8);
    const artifactPath = path.join(
      DATA_ROOT,
      'strategy-results',
      'selection-runtime',
      String(payload?.strategyId || 'unknown'),
      `${resultDate}-${runId}.json`,
    );
    value.artifact_path = artifactPath;
    value.persisted_at = new Date().toISOString();
    await writeRuntimeJson(artifactPath, value);
    return value;
  } finally {
    await unlink(requestPath).catch(() => {});
  }
}

function skill14Catalog() {
  const value = readJson(SKILL14_CATALOG_FILE);
  if (!value || !Array.isArray(value.skills)) throw new Error('14 技能目录不可读取');
  return value;
}

async function runSkill14Runtime(command, args = [], timeoutMs = 600000) {
  const needsDailySource = command === 'status' || command === 'preflight';
  const liveDaily = needsDailySource ? inspectTdxDailyIntegrity() : null;
  const dailyFreshness = liveDaily ? dailyFreshnessSnapshot({ latestDate: liveDaily.latestDate }) : null;
  const requestedDailyDate = dailyFreshness?.updateDue
    ? dailyFreshness.currentDate
    : String(liveDaily?.latestDate || '');
  const result = await runLocalScript(
    'skill14_data_runtime.py',
    [command, ...args],
    timeoutMs,
    2 * 1024 * 1024,
    [],
    liveDaily ? {
      ZHANGCAI_TDX_LATEST_DAILY_DATE: liveDaily.latestDate || '',
      ZHANGCAI_TDX_LATEST_DAILY_SYMBOLS: String(liveDaily.latestCount || 0),
      ZHANGCAI_DAILY_REQUESTED_TRADE_DATE: requestedDailyDate,
    } : {},
  );
  let value;
  try { value = JSON.parse(result.output || '{}'); } catch { throw new Error('14 技能运行时返回了无效 JSON'); }
  if (value?.status === 'error') throw new Error(String(value.error || '14 技能运行时失败'));
  if (command === 'archive-daily') {
    const date = displayDateText(value?.trade_date || value?.tradeDate || localTradeDate());
    const stateFile = path.join(RUNTIME_ROOT, 'skill14-archive-harness-state.json');
    const state = {
      schema: 'ZHANGCAI_SKILL14_ARCHIVE_RUN_V1', date, startedAt: new Date().toISOString(),
      finishedAt: new Date().toISOString(), status: value?.status === 'error' ? 'partial' : 'completed',
      steps: [{ name: '14技能本地日线归档', status: 'completed', script: 'skill14_data_runtime.py', code: result.code }],
      harness: { status: 'pending' },
    };
    const archived = await persistHarnessArchiveContext({ date, state, archiveType: 'skill14', stateFile });
    await writeRuntimeJson(stateFile, state);
    value.harness_archive = { status: archived.harness.status, contextFile: archived.contextFile, latest: path.join(HARNESS_CONTEXT_ROOT, 'latest-archive.json') };
  }
  return value;
}

function inspectTdxDailyIntegrity(tdxRoot = bridgeTdxRoot()) {
  const rootText = String(tdxRoot || '').trim();
  if (!rootText) {
    return {
      root: '', directories: {}, fileCount: 0, latestDate: '', latestCount: 0,
      fileLatestCount: 0, stockListCount: null, stockCompleteCount: null,
      stockFileCompleteCount: null, stockNonTradingCount: 0, stockMissingCount: null,
      integrityReportPath: null, integrity: null, requiredMinimum: 3000, complete: false,
    };
  }
  const resolvedRoot = path.resolve(rootText);
  // A full scan opens several thousand .day files. Keep one verified snapshot
  // long enough to serve environment/status refreshes without rescanning on
  // every low-end desktop request; daily bars do not change intraday often.
  if (tdxDailyIntegrityScanCache?.root === resolvedRoot
    && Date.now() - tdxDailyIntegrityScanCache.checkedAt < TDX_DAILY_INTEGRITY_CACHE_TTL_MS) {
    return tdxDailyIntegrityScanCache.value;
  }
  const markets = ['sh', 'sz', 'bj'];
  const byMarket = {};
  const dateCounts = new Map();
  let fileCount = 0;
  for (const market of markets) {
    const directory = path.join(resolvedRoot, 'vipdoc', market, 'lday');
    let names = [];
    try { names = readdirSync(directory); } catch { names = []; }
    let marketCount = 0;
    const marketDates = new Map();
    for (const name of names) {
      if (!name.toLowerCase().endsWith('.day')) continue;
      try {
        const date = readTdxDayBoundary(path.join(directory, name))?.last_date;
        if (!date) continue;
        marketCount += 1;
        fileCount += 1;
        marketDates.set(date, (marketDates.get(date) || 0) + 1);
        dateCounts.set(date, (dateCounts.get(date) || 0) + 1);
      } catch { /* 单文件损坏计入缺口，不阻断其他市场检查 */ }
    }
    const latest = [...marketDates.entries()].sort((a, b) => b[0].localeCompare(a[0]))[0];
    byMarket[market.toUpperCase()] = { fileCount: marketCount, latestDate: latest?.[0] || '', latestCount: latest?.[1] || 0 };
  }
  const latest = [...dateCounts.entries()].sort((a, b) => b[0].localeCompare(a[0]))[0];
  const latestDate = latest?.[0] || '';
  const fileLatestCount = latest?.[1] || 0;
  let integrityReport = null;
  let integrityReportPath = '';
  try {
    const reportName = readdirSync(RUNTIME_ROOT)
      .filter((name) => /^tdx-daily-integrity-\d{8}-\d{6}\.json$/.test(name))
      .sort()
      .at(-1);
    if (reportName) {
      integrityReportPath = path.join(RUNTIME_ROOT, reportName);
      integrityReport = readJson(integrityReportPath);
    }
  } catch { /* 完整性报告尚未生成时仍返回文件级扫描结果 */ }
  const stockAfter = integrityReport?.after && typeof integrityReport.after === 'object' ? integrityReport.after : null;
  const reportTargetDate = String(integrityReport?.targetDate || stockAfter?.targetDate || '');
  const reportMatchesLatestFiles = Boolean(
    reportTargetDate.replace(/\D/g, '')
      && latestDate.replace(/\D/g, '')
      && reportTargetDate.replace(/\D/g, '') === latestDate.replace(/\D/g, ''),
  );
  const stockFileLatestCount = Number(stockAfter?.completeCount || 0);
  const stockNonTradingCount = Number(stockAfter?.nonTradingCount || 0);
  const stockLatestCount = Number(stockAfter?.effectiveCompleteCount ?? (stockFileLatestCount + stockNonTradingCount));
  const stockExpectedCount = Number(stockAfter?.stockCount || 0);
  const reportRepairs = Array.isArray(integrityReport?.repairs) ? integrityReport.repairs : [];
  const reportNonTrading = Array.isArray(integrityReport?.nonTrading) ? integrityReport.nonTrading : [];
  const reportUnresolved = Array.isArray(integrityReport?.unresolved) ? integrityReport.unresolved : [];
  const integritySummary = integrityReport ? {
    schema: integrityReport.schema,
    targetDate: reportTargetDate,
    latestFileDate: latestDate,
    reportMatchesLatestFiles,
    before: integrityReport.before,
    after: integrityReport.after,
    repairs: reportRepairs.slice(0, 100), repairsCount: reportRepairs.length,
    nonTrading: reportNonTrading.slice(0, 100), nonTradingCount: reportNonTrading.length,
    unresolved: reportUnresolved.slice(0, 10), unresolvedCount: reportUnresolved.length,
    refreshSubmissionCount: Number(integrityReport.refreshSubmissionCount || reportRepairs.filter((item) => item?.status === 'refresh_submitted').length),
    writtenCount: Number(integrityReport.writtenCount || reportRepairs.filter((item) => item?.status === 'written').length),
    manualActionRequired: integrityReport.manualActionRequired === true,
    manualAction: String(integrityReport.manualAction || ''),
    complete: reportMatchesLatestFiles && integrityReport.complete === true,
  } : null;
  const result = {
    root: resolvedRoot,
    directories: byMarket,
    fileCount,
    // The integrity report records its requested target date. Strategy
    // freshness must instead follow the newest date physically present in
    // the configured TDX .day files; an older report cannot override it.
    latestDate,
    latestCount: reportMatchesLatestFiles ? (stockLatestCount || fileLatestCount) : fileLatestCount,
    fileLatestCount,
    reportTargetDate,
    reportMatchesLatestFiles,
    stockListCount: reportMatchesLatestFiles ? (stockExpectedCount || null) : null,
    stockCompleteCount: reportMatchesLatestFiles ? (stockLatestCount || null) : null,
    stockFileCompleteCount: reportMatchesLatestFiles ? (stockFileLatestCount || null) : null,
    stockNonTradingCount: reportMatchesLatestFiles ? stockNonTradingCount : 0,
    stockMissingCount: reportMatchesLatestFiles && stockExpectedCount ? Math.max(0, stockExpectedCount - stockLatestCount) : null,
    integrityReportPath: integrityReportPath || null,
    integrity: integritySummary,
    requiredMinimum: 3000,
    complete: reportMatchesLatestFiles
      ? stockExpectedCount > 0 && stockLatestCount === stockExpectedCount
      : fileLatestCount >= 3000 && ['SH', 'SZ', 'BJ'].every((market) => byMarket[market].latestDate === latestDate),
  };
  tdxDailyIntegrityScanCache = { root: resolvedRoot, checkedAt: Date.now(), value: result };
  return result;
}

function dailyFreshnessSnapshot(daily, now = new Date()) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(now).reduce((result, item) => ({ ...result, [item.type]: item.value }), {});
  const year = Number(parts.year);
  const month = Number(parts.month);
  const day = Number(parts.day);
  const hour = Number(parts.hour);
  const minute = Number(parts.minute);
  const today = `${parts.year}${parts.month}${parts.day}`;
  const latestDate = String(daily?.latestDate || '').replace(/\D/g, '');
  const isTradingDay = isTradingDayDate(today);
  const afterClose = hour > 16 || (hour === 16 && minute >= 30);
  const updateDue = afterClose && isTradingDay && (!/^\d{8}$/.test(latestDate) || latestDate < today);
  return {
    currentDate: today,
    afterClose,
    isTradingDay,
    latestDate,
    updateDue,
    freshnessStatus: updateDue ? 'update_due' : 'current_or_not_trading_day',
    freshnessMessage: updateDue
      ? `已过 16:30，最新日线 ${latestDate || '无'}，请更新至 ${today}`
      : afterClose && !isTradingDay
        ? '今日为非交易日，不要求生成新日线'
        : `日线检查截止 ${today} ${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`,
  };
}

// 个股详情页的“五公式”走同一个本地桥接端口，避免前端再依赖一个
// 未启动的 4320 服务。tdx_hub.py 的 five 命令即使某一公式失败也会
// 返回完整 JSON（退出码 2），因此这里按 JSON 响应解析并把单项失败
// 交给页面展示，而不是把它误报成网络错误。
async function persistFormulaReceipt(result, requestedSymbol, startedAt) {
  const executedAt = new Date().toISOString();
  let dataDate = '';
  try { dataDate = String(inspectTdxDailyIntegrity().latestDate || ''); } catch { /* 日线扫描失败不应吞掉公式结果 */ }
  const receiptDate = /^\d{8}$/.test(dataDate)
    ? dataDate
    : executedAt.slice(0, 10).replace(/-/g, '');
  const safeSymbol = String(result.symbol || requestedSymbol || 'unknown')
    .replace(/[^A-Za-z0-9._-]/g, '_');
  const receipt = {
    schema: 'ZHANGCAI_TDX_TQ_FORMULA_RECEIPT_V1',
    asset: 'tdx_tq_formula',
    executed_at: executedAt,
    data_date: dataDate,
    symbol: result.symbol || requestedSymbol,
    source: result.source || '通达信 TQ · tdx-local-hub',
    source_root: bridgeTdxRoot(),
    formulas: Array.isArray(result.formulas) ? result.formulas : [],
    failed_formulas: Array.isArray(result.failed_formulas) ? result.failed_formulas : [],
    elapsed_ms: result.elapsed_ms || Math.max(0, Date.now() - startedAt),
    bridge_exit_code: result.bridge_exit_code,
  };
  const receiptPath = path.join(DATA_ROOT, 'evidence', 'formulas', receiptDate, `tdx-tq-${safeSymbol}-${Date.now()}.json`);
  await writeRuntimeJson(receiptPath, receipt);
  return path.relative(DATA_ROOT, receiptPath).replace(/\\/g, '/');
}

function runFiveFormulasLive(symbol, timeoutMs = 120000) {
  const portableFallback = formulaReceiptFallback(symbol);
  return new Promise((resolve, reject) => {
    const python = localPythonExecutable();
    const script = path.join(SKILL_SOURCE, 'tdx-local-hub', 'scripts', 'tdx_hub.py');
    if (!existsSync(script)) {
      const fallback = portableFallback || formulaReceiptFallback(symbol, `未找到通达信公式桥接脚本：${script}`);
      if (fallback) resolve(fallback);
      else reject(new Error(`未找到通达信公式桥接脚本：${script}`));
      return;
    }
    const child = spawn(python, [script, 'five', symbol], {
      cwd: APP_ROOT,
      windowsHide: true,
      env: localScriptEnvironment({
        TDX_ROOT: bridgeTdxRoot(),
        ONESTOCK_STOCK_DATA_ROOT: DATA_ROOT,
      }),
    });
    let stdout = '';
    let stderr = '';
    const startedAt = Date.now();
    const timer = setTimeout(() => {
      if (child.pid) spawn('taskkill', ['/pid', String(child.pid), '/t', '/f'], { windowsHide: true });
      const fallback = portableFallback || formulaReceiptFallback(symbol, `五公式计算超时（${Math.round(timeoutMs / 1000)} 秒）`);
      if (fallback) resolve(fallback);
      else reject(new Error(`五公式计算超时（${Math.round(timeoutMs / 1000)} 秒）`));
    }, timeoutMs);
    child.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
    child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
     child.on('error', (error) => {
       clearTimeout(timer);
       const fallback = portableFallback || formulaReceiptFallback(symbol, error instanceof Error ? error.message : String(error));
       if (fallback) resolve(fallback);
       else reject(error);
     });
    child.on('close', async (code) => {
      clearTimeout(timer);
      const text = stdout.trim();
      let payload;
      try {
        payload = JSON.parse(text);
      } catch {
        reject(new Error((stderr || text || `公式桥接退出码 ${code}`).trim().slice(-2000)));
        return;
      }
      const result = {
        status: 'partial',
        symbol: payload.symbol || symbol,
        source: '通达信 TQ · tdx-local-hub',
        elapsed_ms: payload.elapsed_ms || Date.now() - startedAt,
        formulas: Array.isArray(payload.items) ? payload.items.map((item) => ({
          formula: item.formula,
          tq_formula: item.tq_formula,
          ok: Boolean(item.ok),
          elapsed_ms: item.elapsed_ms,
          // tdx_hub 返回 {"300959.SZ": {...}, "ErrorId":"0"}，
          // 页面需要直接按指标名读取这一层结果。
          result: item.result && typeof item.result === 'object'
            ? (item.result[item.symbol || payload.symbol || symbol] || {})
            : {},
          error: item.error,
          client_open_required: Boolean(item.client_open_required),
          action: item.action,
        })) : [],
        failed_formulas: Array.isArray(payload.failed_formulas) ? payload.failed_formulas : [],
        client_open_required: Boolean(payload.client_open_required),
        action: payload.action || '',
        tdx_process: payload.tdx_process || null,
        tdx_root: payload.tdx_root || bridgeTdxRoot(),
        tq_init_path: payload.tq_init_path || '',
        session_reused: Boolean(payload.session_reused),
        lock_waited_ms: Number(payload.lock_waited_ms || 0),
        bridge_exit_code: code,
      };
      const liveFormulaSuccess = result.formulas.length >= 5
        && result.failed_formulas.length === 0
        && result.formulas.every((item) => item.ok === true);
      result.status = liveFormulaSuccess ? 'ok' : 'partial';
      if (!liveFormulaSuccess) {
        const fallback = portableFallback || formulaReceiptFallback(symbol, result.action || '通达信 TQ 未返回完整五公式结果');
        if (fallback) {
          resolve({ ...fallback, live_result: result });
          return;
        }
      }
      try {
        result.receipt_path = await persistFormulaReceipt(result, symbol, startedAt);
      } catch (error) {
        result.receipt_error = error instanceof Error ? error.message : String(error);
        console.error(`[agent] 无法保存 TQ 公式回执：${result.receipt_error}`);
      }
      resolve(result);
    });
  });
}

function runFiveFormulas(symbol, timeoutMs = 120000) {
  const key = String(symbol || '').trim().toUpperCase();
  const running = tqFormulaRequests.get(key);
  if (running) {
    return running.then((result) => ({ ...result, request_coalesced: true }));
  }
  const request = runFiveFormulasLive(symbol, timeoutMs).finally(() => {
    if (tqFormulaRequests.get(key) === request) tqFormulaRequests.delete(key);
  });
  tqFormulaRequests.set(key, request);
  return request;
}

function runFiveFormulasBatch(symbols, timeoutMs = 600000) {
  return new Promise((resolve, reject) => {
    const python = localPythonExecutable();
    const script = path.join(SKILL_SOURCE, 'tdx-local-hub', 'scripts', 'tdx_hub.py');
    if (!existsSync(script)) {
      reject(new Error(`未找到通达信公式桥接脚本：${script}`));
      return;
    }
    const child = spawn(python, [script, 'batch', ...symbols], {
      cwd: APP_ROOT,
      windowsHide: true,
      env: localScriptEnvironment({
        TDX_ROOT: bridgeTdxRoot(),
        ONESTOCK_STOCK_DATA_ROOT: DATA_ROOT,
      }),
    });
    let stdout = '';
    let stderr = '';
    const startedAt = Date.now();
    const timer = setTimeout(() => {
      if (child.pid) spawn('taskkill', ['/pid', String(child.pid), '/t', '/f'], { windowsHide: true });
      reject(new Error(`批量五公式计算超时（${Math.round(timeoutMs / 1000)} 秒）`));
    }, timeoutMs);
    child.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
    child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
    child.on('error', (error) => { clearTimeout(timer); reject(error); });
    child.on('close', async (code) => {
      clearTimeout(timer);
      let payload;
      try {
        payload = JSON.parse(stdout.trim());
      } catch {
        reject(new Error((stderr || stdout || `批量公式桥接退出码 ${code}`).trim().slice(-2000)));
        return;
      }
      const requested = Array.isArray(symbols) ? symbols : [];
      const formulas = Array.isArray(payload.items) ? payload.items.map((item) => ({
        formula: item.formula,
        tq_formula: item.tq_formula,
        ok: Boolean(item.ok),
        elapsed_ms: item.elapsed_ms,
        results: item.results && typeof item.results === 'object' ? item.results : {},
        error: item.error,
      })) : [];
      const result = {
        status: payload.ok ? 'ok' : 'partial',
        symbols: requested,
        source: '通达信 TQ · tdx-local-hub / batch',
        elapsed_ms: payload.elapsed_ms || Date.now() - startedAt,
        formulas,
        failed_formulas: Array.isArray(payload.failed_formulas) ? payload.failed_formulas : [],
        bridge_exit_code: code,
      };
      try {
        // 每只股票保留一份独立回执，供 Harness 和后续 exe 运行时按股票复用。
        await Promise.all(requested.map(async (symbol) => {
          const perSymbol = {
            ...result,
            symbol,
            formulas: formulas.map((item) => ({
              formula: item.formula,
              tq_formula: item.tq_formula,
              ok: item.ok,
              elapsed_ms: item.elapsed_ms,
              result: item.results[symbol] || {},
              error: item.error,
            })),
          };
          return persistFormulaReceipt(perSymbol, symbol, startedAt);
        }));
      } catch (error) {
        result.receipt_error = error instanceof Error ? error.message : String(error);
      }
      resolve(result);
    });
  });
}

function normalizeSingleSignalSymbol(value) {
  const raw = String(value || '').trim().toUpperCase();
  const digits = raw.replace(/\D/g, '');
  if (!/^\d{6}$/.test(digits)) return '';
  const explicitMarket = raw.match(/\.(SH|SZ|BJ)$/i)?.[1]?.toUpperCase();
  const market = explicitMarket || (/^(920|[48])/.test(digits)
    ? 'BJ'
    : /^[569]/.test(digits)
      ? 'SH'
      : 'SZ');
  return `${digits}.${market}`;
}

function parseLastJsonLine(output) {
  const lines = String(output || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  for (let index = lines.length - 1; index >= 0; index -= 1) {
    try { return JSON.parse(lines[index]); } catch { /* 继续向前找最终回执 */ }
  }
  return null;
}

function runGoldenIgnitionSymbol(symbol, lookback = 5, timeoutMs = 600000) {
  return new Promise((resolve, reject) => {
    const normalized = normalizeSingleSignalSymbol(symbol);
    if (!normalized) {
      reject(new Error('需要六位股票代码，可带 .SH、.SZ 或 .BJ 后缀'));
      return;
    }
    const script = path.join(SKILL_SOURCE, 'golden-ignition', 'scripts', 'entry_golden_ignition.py');
    if (!existsSync(script)) {
      reject(new Error(`未找到黄金点火单股入口：${script}`));
      return;
    }
    const python = localPythonExecutable();
    const safeLookback = Math.max(1, Math.min(30, Number(lookback) || 5));
    const startedAt = Date.now();
    const liveDaily = inspectTdxDailyIntegrity();
    const liveDailyFreshness = dailyFreshnessSnapshot({ latestDate: liveDaily.latestDate || '' });
    const requestedDailyDate = liveDailyFreshness.updateDue
      ? liveDailyFreshness.currentDate
      : String(liveDaily.latestDate || '');
    const child = spawn(python, [script, normalized, '--lookback', String(safeLookback)], {
      cwd: path.join(SKILL_SOURCE, 'golden-ignition'),
      windowsHide: true,
      env: localScriptEnvironment({
        ZHANGCAI_APP_ROOT: APP_ROOT,
        ZHANGCAI_DATA_DIR: DATA_ROOT,
        ZHANGCAI_TDX_ROOT: bridgeTdxRoot(),
        TDX_ROOT: bridgeTdxRoot(),
        TDX_HUB_PATH: path.join(SKILL_SOURCE, 'tdx-local-hub', 'scripts', 'tdx_hub.py'),
        TDX_BOND_MAP_PATH: path.join(bridgeTdxRoot(), 'T0002', 'hq_cache', 'speckzzdata.txt'),
        ZHANGCAI_STRATEGY_RESULTS_DIR: path.join(DATA_ROOT, 'strategy-results'),
        ONESTOCK_STOCK_DATA_ROOT: path.join(DATA_ROOT, 'strategy-results'),
        ONESTOCK_STOCK_CANONICAL_CHILD: '1',
        ZHANGCAI_DAILY_REQUESTED_TRADE_DATE: requestedDailyDate,
        ZHANGCAI_TDX_LATEST_DAILY_DATE: liveDaily.latestDate || '',
        PYTHONPATH: [
          path.join(SKILL_SOURCE, 'stock-unified', 'scripts'),
          process.env.PYTHONPATH || '',
        ].filter(Boolean).join(path.delimiter),
      }),
    });
    let stdout = '';
    let stderr = '';
    let settled = false;
    const finishError = (error) => {
      if (settled) return;
      settled = true;
      reject(error);
    };
    const timer = setTimeout(() => {
      if (child.pid) spawn('taskkill', ['/pid', String(child.pid), '/t', '/f'], { windowsHide: true });
      finishError(new Error(`黄金点火单股执行超时（${Math.round(timeoutMs / 1000)} 秒）`));
    }, timeoutMs);
    child.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
    child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
    child.on('error', (error) => { clearTimeout(timer); finishError(error); });
    child.on('close', async (code) => {
      clearTimeout(timer);
      if (settled) return;
      const summary = parseLastJsonLine(stdout);
      if (!summary || typeof summary !== 'object') {
        finishError(new Error((stderr || stdout || `黄金点火单股入口退出码 ${code}`).trim().slice(-3000)));
        return;
      }
      const resultPath = typeof summary.result_path === 'string' ? summary.result_path : '';
      const artifact = resultPath ? readJson(resultPath) : null;
      const result = artifact && typeof artifact === 'object'
        ? artifact
        : summary;
      resolve({
        status: result.status === 'PASS' ? 'ok' : 'blocked',
        skill_id: 'golden-ignition',
        input_symbol: result.input_symbol || summary.input_symbol || normalized,
        analysis_symbol: result.analysis_symbol || summary.analysis_symbol || normalized,
        latest_trading_date: result.latest_trading_date || summary.latest_trading_date || '',
        requested_trade_date: result.requested_trade_date || '',
        daily_data_quality: result.daily_data_quality || 'AVAILABLE',
        daily_data_notice: result.daily_data_notice || '',
        signal_status: result.signal_status || summary.signal_status || '',
        ignition_signal: Boolean(result.ignition_signal),
        lookback_trading_days: Number(result.lookback_trading_days || safeLookback),
        local_daily: result.local_daily && typeof result.local_daily === 'object' ? result.local_daily : {},
        tdx_formula: result.tdx_formula && typeof result.tdx_formula === 'object' ? result.tdx_formula : {},
        data_sources: result.data_sources && typeof result.data_sources === 'object' ? result.data_sources : {},
        risk_boundary: Array.isArray(result.risk_boundary) ? result.risk_boundary : [],
        error: result.error || undefined,
        result_path: resultPath,
        artifact: result,
        raw_summary: summary,
        bridge_exit_code: code,
        elapsed_ms: Date.now() - startedAt,
      });
    });
  });
}

async function runDailyRecovery(date, codes = '', maxSymbols = 0) {
  const args = ['--date', date];
  if (codes) args.push('--codes', codes);
  if (Number(maxSymbols) > 0) args.push('--max-symbols', String(Math.min(Number(maxSymbols), 10000)));
  const result = await runLocalScript(
    'daily_data_recovery.py', args,
    Number(process.env.ZHANGCAI_PUBLIC_DAILY_RECOVERY_TIMEOUT_MS || 300000),
    12000,
    [2],
  );
  let local = null;
  try { local = JSON.parse(String(result.output || '').trim()); } catch { local = parseLastJsonLine(result.output); }
  if (!local || typeof local !== 'object' || Array.isArray(local)) local = { status: result.partial ? 'degraded' : 'available', output: result.output };
  try { await runLocalScript('skill14_data_runtime.py', ['status'], 120000, 4000); } catch { /* 日线索引已先落盘，状态页下次刷新可恢复 */ }
  try { await runLocalScript('unified_data_archive.py', ['snapshot', '--date', date], 600000, 4000); } catch { /* 不阻断公开降级层本身 */ }
  const stateFile = path.join(RUNTIME_ROOT, `daily-fallback-recovery-${archiveDateKey(date)}.json`);
  const state = {
    schema: 'ZHANGCAI_DAILY_FALLBACK_RECOVERY_V1', date, startedAt: new Date().toISOString(),
    finishedAt: new Date().toISOString(), status: result.partial ? 'partial' : 'completed',
    steps: [{ name: '公开日线降级补齐', status: result.partial ? 'partial' : 'completed', script: 'daily_data_recovery.py', code: result.code }],
    recovery: local, harness: { status: 'pending' },
  };
  const archived = await persistHarnessArchiveContext({ date, state, archiveType: 'daily-fallback', stateFile });
  await writeRuntimeJson(stateFile, state);
  return { ...local, bridge: { partial: Boolean(result.partial), exitCode: result.code }, harness_archive: { status: archived.harness.status, contextFile: archived.contextFile } };
}

async function runDailyRefresh(date) {
  const startedAt = new Date().toISOString();
  const state = {
    schema: 'ZHANGCAI_DAILY_REFRESH_V1',
    date,
    startedAt,
    status: 'running',
    steps: [],
    harness: { status: 'pending' },
  };
  await writeRuntimeJson(DAILY_STATE_FILE, state);
  const execute = async (name, script, args, timeout, acceptedExitCodes = []) => {
    // 先落盘 running 状态。此前只有子进程结束后才写步骤，导致全量 TQ
    // 刷新期间网页永远停留在“等待 DeepSeek 校验”，无法判断实际卡点。
    const step = { name, status: 'running', startedAt: new Date().toISOString(), script };
    state.steps.push(step);
    await writeRuntimeJson(DAILY_STATE_FILE, state);
    let result = null;
    try {
      result = await runLocalScript(script, args, timeout, 12000, acceptedExitCodes);
      Object.assign(step, { status: result.partial ? 'partial' : 'completed', finishedAt: new Date().toISOString(), ...result });
    } catch (error) {
      Object.assign(step, { status: 'failed', finishedAt: new Date().toISOString(), error: error instanceof Error ? error.message : String(error) });
    }
    await writeRuntimeJson(DAILY_STATE_FILE, state);
    return result;
  };
  const tdxStatusResult = await execute('通达信运行状态', 'tdx_runtime_bridge.py', ['status'], 60000);
  let tdxReady = false;
  try {
    const parsed = JSON.parse(String(tdxStatusResult?.output || '{}'));
    tdxReady = Array.isArray(parsed.processes) && parsed.processes.some((item) => String(item?.Name || item?.name || '').toLowerCase() === 'tdxw');
  } catch { tdxReady = false; }
  // 收盘后以通达信补齐后的最近完整交易日为准，再拉取同日公开源，
  // 这样龙虎榜、涨停池和 Harness 上下文不会出现日期错位。
  // 完整性脚本用退出码 2 表示“报告已生成但仍有缺口”。这不是进程故障，
  // 必须保留其完整 stdout 交给 Harness，而不是只留下截断的错误尾部。
  const tdxRefresh = await execute('通达信日线完整性检查与补齐', 'tdx_daily_integrity.py', ['--refresh'], Number(process.env.ZHANGCAI_TDX_REFRESH_TIMEOUT_MS || 180000), [2]);
  await execute('14技能日线归档', 'skill14_data_runtime.py', ['archive-daily'], Number(process.env.ZHANGCAI_DAILY_ARCHIVE_TIMEOUT_MS || 300000));
  const effectiveDate = targetDateFromTdxResult(tdxRefresh, localTradeDate());
  state.date = effectiveDate;
  await writeRuntimeJson(DAILY_STATE_FILE, state);
  if (isLocalOnlyDataPolicy()) {
    state.steps.push({
      name: '公网行情、新闻和第三方补充源',
      status: 'blocked',
      finishedAt: new Date().toISOString(),
      error: 'desktop_local_tdx_only_policy',
    });
    await writeRuntimeJson(DAILY_STATE_FILE, state);
  } else {
    // 正常桌面模式也执行公开源补充：它是明确的本地落盘步骤，
    // 既用于补齐资讯，也用于 TDX 不可用时的降级层。
    await execute('公开日线缺口降级补齐', 'daily_data_recovery.py', ['--date', effectiveDate], Number(process.env.ZHANGCAI_PUBLIC_DAILY_RECOVERY_TIMEOUT_MS || 300000), [2]);
    await Promise.all([
      execute('公开行情补齐', 'public_market_sync.py', ['--date', effectiveDate], 90000),
      execute('新闻快讯补齐', 'news_sync.py', ['--date', effectiveDate], 90000),
    ]);
    await execute('财务、股本、指数、龙虎榜、融资融券统一落盘', 'supplemental_data_sync.py', ['--date', effectiveDate, '--mode', 'daily'], 240000);
    await execute('行情资讯能力包来源补充', 'package_source_sync.py', ['--date', effectiveDate], 360000);
  }
  // 先刷新会变化的状态页，再生成哈希清单，避免清单刚生成就被状态页覆盖。
  await execute('统一数据状态刷新', 'skill14_data_runtime.py', ['status'], 120000);
  await execute('统一数据源清单生成', 'unified_data_archive.py', ['snapshot', '--date', effectiveDate], 180000);

  await persistHarnessArchiveContext({ date: effectiveDate, state, archiveType: 'daily', stateFile: DAILY_STATE_FILE });
  state.finishedAt = new Date().toISOString();
  state.status = state.steps.some((step) => ['failed', 'partial'].includes(step.status)) || state.harness.status === 'failed' ? 'partial' : 'completed';
  await writeRuntimeJson(DAILY_STATE_FILE, state);
  return state;
}

async function runDailyIndexInitialization(job) {
  const state = {
    schema: 'ZHANGCAI_DAILY_INDEX_INITIALIZATION_V1',
    operation: 'rebuild-full-stock-index',
    startedAt: new Date().toISOString(),
    status: 'running',
    steps: [],
    tdxRoot: bridgeTdxRoot(),
    dataRoot: DATA_ROOT,
  };
  await writeRuntimeJson(DAILY_INDEX_INITIALIZATION_STATE_FILE, state);
  const step = async (name, run) => {
    const current = { name, status: 'running', startedAt: new Date().toISOString() };
    state.steps.push(current);
    await writeRuntimeJson(DAILY_INDEX_INITIALIZATION_STATE_FILE, state);
    try {
      const value = await run();
      Object.assign(current, { status: 'completed', finishedAt: new Date().toISOString(), result: value || null });
      await writeRuntimeJson(DAILY_INDEX_INITIALIZATION_STATE_FILE, state);
      return value;
    } catch (error) {
      Object.assign(current, { status: 'failed', finishedAt: new Date().toISOString(), error: error instanceof Error ? error.message : String(error) });
      await writeRuntimeJson(DAILY_INDEX_INITIALIZATION_STATE_FILE, state);
      return null;
    }
  };

  const tdxRoot = bridgeTdxRoot();
  const tdxHasLayout = Boolean(tdxRoot && (
    existsSync(path.join(tdxRoot, 'vipdoc')) || existsSync(path.join(tdxRoot, 'T0002'))
  ));
  let tdxIndex = await step('扫描通达信全部 .day 文件并重建股票索引', async () => {
    const index = await buildTdxHistoryIndex(true);
    return { symbolCount: Number(index?.symbol_count || 0), sourceAvailable: index?.source_available !== false, path: TDX_HISTORY_INDEX_FILE };
  });

  if (tdxHasLayout) {
    await step('读取通达信全历史并重建 canonical 日线主库', async () => {
      const value = await runSkill14Runtime(
        'archive-daily',
        [],
        Number(process.env.ZHANGCAI_DAILY_INDEX_INIT_TIMEOUT_MS || 1200000),
      );
      return {
        tradeDate: value?.trade_date || value?.tradeDate || '',
        archiveMode: value?.archive_mode || '',
        archivedSymbols: Number(value?.archived_symbols || 0),
        barRecords: Number(value?.bar_records || 0),
      };
    });
    // The Python archive refreshes this file as part of the same transaction.
    // Read it again so the completion receipt reflects the actual post-run
    // source set rather than the pre-run snapshot.
    tdxIndex = await step('复核通达信股票索引与最新日期', async () => {
      const index = await buildTdxHistoryIndex(true);
      return { symbolCount: Number(index?.symbol_count || 0), sourceAvailable: index?.source_available !== false, path: TDX_HISTORY_INDEX_FILE };
    });
  } else {
    const current = state.steps.at(-1);
    if (current?.status === 'completed') Object.assign(current, {
      status: 'partial',
      finishedAt: new Date().toISOString(),
      error: '未配置可读的通达信目录；保留本地数据包全历史并继续建立 canonical 索引。',
    });
    await writeRuntimeJson(DAILY_INDEX_INITIALIZATION_STATE_FILE, state);
  }

  const canonicalIndex = await step('建立全历史 JSONL 按股票定位索引', async () => {
    const index = await buildCanonicalDailyIndex(true);
    if (!index?.symbol_count) throw new Error('本地 canonical 日线归档为空，无法建立个股索引');
    return {
      symbolCount: Number(index.symbol_count || 0),
      recordCount: Number(index.record_count || 0),
      path: CANONICAL_DAILY_INDEX_FILE,
      sourceFile: CANONICAL_DAILY_FILE,
    };
  });
  state.finishedAt = new Date().toISOString();
  state.result = {
    tdxSymbolCount: Number(tdxIndex?.symbolCount || 0),
    canonicalSymbolCount: Number(canonicalIndex?.symbolCount || 0),
    canonicalRecordCount: Number(canonicalIndex?.recordCount || 0),
    tdxIndexPath: TDX_HISTORY_INDEX_FILE,
    canonicalIndexPath: CANONICAL_DAILY_INDEX_FILE,
    canonicalFile: CANONICAL_DAILY_FILE,
  };
  const hasFailedStep = state.steps.some((item) => item.status === 'failed');
  state.status = canonicalIndex?.symbolCount ? (hasFailedStep || state.steps.some((item) => item.status === 'partial') ? 'partial' : 'completed') : 'failed';
  await writeRuntimeJson(DAILY_INDEX_INITIALIZATION_STATE_FILE, state);
  return state;
}

function startDailyIndexInitialization(force = false) {
  const existing = readJson(DAILY_INDEX_INITIALIZATION_STATE_FILE);
  const running = [...dailyIndexInitializationJobs.values()].find((item) => item.status === 'running');
  if (running) return { status: 'accepted', job: running, state: existing };
  const conflictingDaily = [...dailyJobs.values()].find((item) => item.status === 'running');
  const conflictingArchive = [...unifiedArchiveJobs.values()].find((item) => item.status === 'running');
  if (conflictingDaily || conflictingArchive) {
    return { status: 'busy', error: '日线或统一落盘任务正在运行，请等待当前任务完成后再初始化。' };
  }
  if (!force && existing?.status === 'completed') return { status: 'current', state: existing };
  const job = { id: randomUUID(), operation: 'rebuild-full-stock-index', status: 'running', started_at: Date.now() };
  dailyIndexInitializationJobs.set(job.id, job);
  void runDailyIndexInitialization(job)
    .then((state) => Object.assign(job, { status: state.status, completed_at: Date.now(), state }))
    .catch((error) => Object.assign(job, { status: 'failed', completed_at: Date.now(), error: error instanceof Error ? error.message : String(error) }));
  return { status: 'accepted', job, state: existing };
}

// 只补齐公开行情、龙虎榜、涨停池与新闻，不重复触发通达信日线扫描。
// 该入口供设置页手动使用；完成后同样交给 DeepSeek Harness 做来源、日期和条数校验。
async function runSupplementalRefresh(date) {
  const state = {
    schema: 'ZHANGCAI_SUPPLEMENTAL_REFRESH_V1', date,
    startedAt: new Date().toISOString(), status: 'running', steps: [], harness: { status: 'pending' },
  };
  await writeRuntimeJson(SUPPLEMENTAL_STATE_FILE, state);
  if (isLocalOnlyDataPolicy()) {
    state.steps.push({
      name: '公网行情、新闻和第三方补充源',
      status: 'blocked',
      finishedAt: new Date().toISOString(),
      error: 'desktop_local_tdx_only_policy',
    });
    state.finishedAt = new Date().toISOString();
    state.status = 'blocked';
    await writeRuntimeJson(SUPPLEMENTAL_STATE_FILE, state);
    return state;
  }
  const execute = async (name, script, args, timeout) => {
    try {
      const result = await runLocalScript(script, args, timeout);
      state.steps.push({ name, status: 'completed', finishedAt: new Date().toISOString(), ...result });
      return result;
    } catch (error) {
      state.steps.push({ name, status: 'failed', finishedAt: new Date().toISOString(), error: error instanceof Error ? error.message : String(error) });
      return null;
    } finally {
      await writeRuntimeJson(SUPPLEMENTAL_STATE_FILE, state);
    }
  };
  await Promise.all([
    execute('公开行情补齐', 'public_market_sync.py', ['--date', date], 90000),
    execute('新闻快讯补齐', 'news_sync.py', ['--date', date], 90000),
  ]);
  await execute('财务、股本、指数、龙虎榜、融资融券统一落盘', 'supplemental_data_sync.py', ['--date', date, '--mode', 'daily'], 240000);
  await execute('行情资讯能力包来源补充', 'package_source_sync.py', ['--date', date], 360000);
  await execute('统一数据状态刷新', 'skill14_data_runtime.py', ['status'], 120000);
  await execute('统一数据源清单生成', 'unified_data_archive.py', ['snapshot', '--date', date], 180000);
  await persistHarnessArchiveContext({ date, state, archiveType: 'supplemental', stateFile: SUPPLEMENTAL_STATE_FILE });
  state.finishedAt = new Date().toISOString();
  state.status = state.steps.some((step) => step.status === 'failed') || state.harness.status === 'failed' ? 'partial' : 'completed';
  await writeRuntimeJson(SUPPLEMENTAL_STATE_FILE, state);
  return state;
}

function targetDateFromTdxResult(result, fallback) {
  try {
    const value = JSON.parse(String(result?.output || '{}'));
    const raw = String(value?.after?.targetDate || value?.targetDateAfter || value?.targetDate || '').replace(/\D/g, '');
    if (/^\d{8}$/.test(raw)) return `${raw.slice(0, 4)}-${raw.slice(4, 6)}-${raw.slice(6)}`;
  } catch { /* 保留回退日期 */ }
  const match = String(result?.output || '').match(/"targetDateAfter"\s*:\s*"(\d{8})"/);
  if (match) return `${match[1].slice(0, 4)}-${match[1].slice(4, 6)}-${match[1].slice(6)}`;
  return fallback;
}

async function runUnifiedDataArchive(date) {
  const state = {
    schema: 'ZHANGCAI_UNIFIED_DATA_ARCHIVE_RUN_V1',
    date,
    startedAt: new Date().toISOString(),
    status: 'running',
    steps: [],
    harness: { status: 'pending' },
  };
  await saveUnifiedArchiveState(state);
  const execute = async (name, script, args, timeout, acceptedExitCodes = []) => {
    const step = { name, status: 'running', startedAt: new Date().toISOString(), script };
    state.steps.push(step);
    await saveUnifiedArchiveState(state);
    try {
      const result = await runLocalScript(script, args, timeout, 12000, acceptedExitCodes);
      const resultPath = await persistUnifiedStepOutput(state.date, step, state.steps.length, result);
      Object.assign(step, {
        status: result.partial ? 'partial' : 'completed',
        finishedAt: new Date().toISOString(),
        code: result.code,
        partial: result.partial === true,
        resultPath,
        resultStored: Boolean(resultPath),
      });
      return result;
    } catch (error) {
      Object.assign(step, { status: 'failed', finishedAt: new Date().toISOString(), error: error instanceof Error ? error.message : String(error) });
      return null;
    } finally {
      await saveUnifiedArchiveState(state);
    }
  };

  const tdxRefresh = await execute(
    '通达信日线完整性检查与补齐',
    'tdx_daily_integrity.py',
    ['--refresh'],
    Number(process.env.ZHANGCAI_TDX_REFRESH_TIMEOUT_MS || 180000),
    [2],
  );
  const effectiveDate = targetDateFromTdxResult(tdxRefresh, localTradeDate());
  state.date = effectiveDate;
  await saveUnifiedArchiveState(state);
  await execute('通达信日线与证券资料归档', 'skill14_data_runtime.py', ['archive-daily'], Number(process.env.ZHANGCAI_DAILY_ARCHIVE_TIMEOUT_MS || 300000));
  if (isLocalOnlyDataPolicy()) {
    state.steps.push({
      name: '公网行情、新闻和第三方补充源',
      status: 'blocked',
      finishedAt: new Date().toISOString(),
      error: 'desktop_local_tdx_only_policy',
    });
    await saveUnifiedArchiveState(state);
  } else {
    await execute('公开日线缺口降级补齐', 'daily_data_recovery.py', ['--date', effectiveDate], Number(process.env.ZHANGCAI_PUBLIC_DAILY_RECOVERY_TIMEOUT_MS || 300000), [2]);
    await execute('财务、股本、指数、龙虎榜、融资融券统一落盘', 'supplemental_data_sync.py', ['--date', effectiveDate, '--mode', 'daily'], 240000);
    await execute('行情资讯能力包来源补充', 'package_source_sync.py', ['--date', effectiveDate], 360000);
    await Promise.all([
      execute('公开行情、涨停池与龙虎榜归档', 'public_market_sync.py', ['--date', effectiveDate], 90000),
      execute('东方财富 7×24 新闻归档', 'news_sync.py', ['--date', effectiveDate], 90000),
    ]);
  }
  await execute('统一数据状态刷新', 'skill14_data_runtime.py', ['status'], 120000);
  await execute('统一数据源清单生成', 'unified_data_archive.py', ['snapshot', '--date', effectiveDate], 180000);

  // Commit a terminal local status before writing the Harness context. The
  // first context write must never contain the stale "running" state that
  // used to remain in latest-archive.json after a completed run.
  state.finishedAt = new Date().toISOString();
  state.status = state.steps.some((step) => ['failed', 'partial'].includes(step.status)) ? 'partial' : 'completed';
  await saveUnifiedArchiveState(state);
  const archived = await persistHarnessArchiveContext({ date: effectiveDate, state, archiveType: 'unified', stateFile: UNIFIED_ARCHIVE_STATE_FILE });
  const harnessOutputPath = await persistUnifiedHarnessOutput(effectiveDate, archived.harness);
  state.harness = compactUnifiedArchiveState({ harness: { ...archived.harness, outputPath: harnessOutputPath } }).harness;
  state.finishedAt = new Date().toISOString();
  state.status = state.steps.some((step) => ['failed', 'partial'].includes(step.status)) || state.harness.status === 'failed' ? 'partial' : 'completed';
  // Rebuild the context once after the Harness receipt and terminal status
  // are known, so the context, state JSON, and HTML report agree exactly.
  await persistHarnessArchiveContext({ date: effectiveDate, state, archiveType: 'unified', stateFile: UNIFIED_ARCHIVE_STATE_FILE, runValidation: false });
  await saveUnifiedArchiveState(state, readJson(path.join(HARNESS_CONTEXT_ROOT, 'latest-archive.json')) || {});
  return state;
}

async function runUnifiedDataVerification(date) {
  const state = {
    schema: 'ZHANGCAI_UNIFIED_DATA_VERIFICATION_RUN_V1',
    date,
    startedAt: new Date().toISOString(),
    status: 'running',
    local: { status: 'pending' },
    harness: { status: 'pending' },
  };
  await writeRuntimeJson(UNIFIED_VERIFY_STATE_FILE, state);
  try {
    const local = await runLocalScript('unified_data_archive.py', ['verify', '--date', date], 300000, 12000, [2]);
    try { state.local = JSON.parse(local.output || '{}'); } catch { state.local = { status: 'error', error: '统一校验脚本返回了无效 JSON', output: local.output }; }
  } catch (error) {
    state.local = { status: 'error', error: error instanceof Error ? error.message : String(error) };
  }
  await writeRuntimeJson(UNIFIED_VERIFY_STATE_FILE, state);
  const contextFile = path.join(HARNESS_CONTEXT_ROOT, `unified-verification-${String(date).replace(/-/g, '')}.json`);
  const context = {
    schema: 'ZHANGCAI_HARNESS_UNIFIED_VERIFICATION_CONTEXT_V1',
    date,
    generatedAt: new Date().toISOString(),
    localVerification: state.local,
    manifest: path.join(DATA_ROOT, 'evidence', 'sources', String(date).replace(/-/g, ''), 'manifest.json'),
    localDataPage: path.join(HARNESS_CONTEXT_ROOT, 'local-data-page.json'),
    packageSourceInventory: path.join(HARNESS_CONTEXT_ROOT, 'package-source-inventory.json'),
  };
  await writeRuntimeJson(contextFile, context);
  try {
    if (!process.env.DEEPSEEK_API_KEY) throw new Error('未设置 DEEPSEEK_API_KEY，已完成本地文件校验但无法进行 Harness 复核');
    const output = await runHarnessWithRetry(buildPrompt(
      `这是统一数据落盘校验任务。仅依据以下本地校验结果、统一来源清单和本地数据页，核对文件存在性、哈希、交易日、来源状态及未快照来源。禁止重新抓取、执行命令、读取未传入的文件或猜测缺失数据：${JSON.stringify(context)}。${HARNESS_JSON_SCHEMA}`,
      { date: String(date).replace(/-/g, ''), dataSources: { unifiedManifest: context.manifest, localDataPage: context.localDataPage, packageSourceInventory: context.packageSourceInventory } },
      'market-data-replenishment',
      { contextFile, inline: true },
    ), 'market-data-replenishment', { inline: true });
    state.harness = { status: 'completed', finishedAt: new Date().toISOString(), output: output.output, elapsedMs: output.elapsedMs };
  } catch (error) {
    state.harness = { status: 'failed', finishedAt: new Date().toISOString(), error: error instanceof Error ? error.message : String(error) };
  }
  state.finishedAt = new Date().toISOString();
  state.status = state.local.status === 'CLEAN_PASS' && state.harness.status === 'completed' ? 'completed' : 'partial';
  await writeRuntimeJson(contextFile, { ...context, verification: state });
  await writeRuntimeJson(UNIFIED_VERIFY_STATE_FILE, state);
  return state;
}

function startUnifiedDataArchive(date, force = false) {
  const existing = readJson(UNIFIED_ARCHIVE_STATE_FILE);
  if (!force && existing?.date === date && ['completed', 'partial'].includes(existing.status)) {
    return {
      status: 'current',
      state: existing,
      progress: unifiedArchiveProgress(existing),
      report: existing.report || unifiedArchiveReportDescriptor(existing.date),
      message: '当前日期已经存在统一落盘结果，未重复启动。',
    };
  }
  const running = [...unifiedArchiveJobs.values()].find((job) => job.date === date && job.status === 'running');
  if (running) {
    const runningState = readJson(UNIFIED_ARCHIVE_STATE_FILE);
    return {
      status: 'accepted',
      job: running,
      state: runningState,
      progress: unifiedArchiveProgress(runningState),
      report: runningState?.report || unifiedArchiveReportDescriptor(date),
      message: '统一数据落盘任务已经在后台运行。',
    };
  }
  const job = { id: randomUUID(), date, status: 'running', started_at: Date.now() };
  unifiedArchiveJobs.set(job.id, job);
  void runUnifiedDataArchive(date).then((state) => Object.assign(job, { status: state.status, completed_at: Date.now(), state }))
    .catch((error) => Object.assign(job, { status: 'failed', completed_at: Date.now(), error: error instanceof Error ? error.message : String(error) }));
  const initialState = readJson(UNIFIED_ARCHIVE_STATE_FILE);
  return {
    status: 'accepted',
    job,
    state: initialState,
    progress: unifiedArchiveProgress(initialState),
    report: initialState?.report || unifiedArchiveReportDescriptor(date),
    message: '统一数据落盘任务已受理，正在后台执行；状态和报告会持续写入 resource-library。',
  };
}

function startUnifiedDataVerification(date, force = false) {
  const existing = readJson(UNIFIED_VERIFY_STATE_FILE);
  if (!force && existing?.date === date && ['completed', 'partial'].includes(existing.status)) return { status: 'current', state: existing };
  const running = [...unifiedVerificationJobs.values()].find((job) => job.date === date && job.status === 'running');
  if (running) return { status: 'accepted', job: running };
  const job = { id: randomUUID(), date, status: 'running', started_at: Date.now() };
  unifiedVerificationJobs.set(job.id, job);
  void runUnifiedDataVerification(date).then((state) => Object.assign(job, { status: state.status, completed_at: Date.now(), state }))
    .catch((error) => Object.assign(job, { status: 'failed', completed_at: Date.now(), error: error instanceof Error ? error.message : String(error) }));
  return { status: 'accepted', job };
}

function startSupplementalRefresh(date, force = false) {
  const existing = readJson(SUPPLEMENTAL_STATE_FILE);
  if (!force && existing?.date === date && ['completed', 'partial'].includes(existing.status)) return { status: 'current', state: existing };
  const running = [...supplementalJobs.values()].find((job) => job.date === date && job.status === 'running');
  if (running) return { status: 'accepted', job: running };
  const job = { id: randomUUID(), date, status: 'running', started_at: Date.now() };
  supplementalJobs.set(job.id, job);
  void runSupplementalRefresh(date).then((state) => Object.assign(job, { status: state.status, completed_at: Date.now(), state }))
    .catch((error) => Object.assign(job, { status: 'failed', completed_at: Date.now(), error: error instanceof Error ? error.message : String(error) }));
  return { status: 'accepted', job };
}

function startDailyRefresh(date, force = false) {
  const existing = readJson(DAILY_STATE_FILE);
  if (!force && existing?.date === date && ['completed', 'partial'].includes(existing.status)) return { status: 'current', state: existing };
  const running = [...dailyJobs.values()].find((job) => job.date === date && job.status === 'running');
  if (running) return { status: 'accepted', job: running };
  const job = { id: randomUUID(), date, status: 'running', started_at: Date.now() };
  dailyJobs.set(job.id, job);
  void runDailyRefresh(date).then((state) => Object.assign(job, { status: state.status, completed_at: Date.now(), state }))
    .catch((error) => Object.assign(job, { status: 'failed', completed_at: Date.now(), error: error instanceof Error ? error.message : String(error) }));
  return { status: 'accepted', job };
}

function nextAfterCloseTime(now = new Date()) {
  const { year, month, day } = shanghaiDateParts(now);
  // Asia/Shanghai 固定 UTC+8；用 UTC 构造避免宿主机时区影响计划时间。
  let target = new Date(Date.UTC(year, month - 1, day, 8, 30, 0, 0));
  const today = `${year}${String(month).padStart(2, '0')}${String(day).padStart(2, '0')}`;
  const afterClose = now.getTime() >= target.getTime();
  const existing = readJson(DAILY_STATE_FILE);
  const refreshAlreadyRunning = [...dailyJobs.values()].some((job) => job.date === displayDateText(today) && job.status === 'running');
  if (afterClose && refreshAlreadyRunning) {
    // Starting after 16:30 may arm an immediate recovery run. Do not arm a
    // second one-second timer while that run is still persisting its state.
    target = new Date(target.getTime() + 24 * 60 * 60 * 1000);
    while (!isTradingDayDate(target.toISOString().slice(0, 10).replace(/-/g, ''))) target = new Date(target.getTime() + 24 * 60 * 60 * 1000);
    return target;
  }
  // 服务若在当天 16:30 后才启动，立即补跑当天交易日；否则不要等到
  // 第二天，避免“重启后计划已存在但当天数据一直没刷新”。
  if (afterClose && isTradingDayDate(today) && existing?.date !== displayDateText(today)) return new Date(now.getTime() + 1000);
  if (target.getTime() <= now.getTime()) target = new Date(target.getTime() + 24 * 60 * 60 * 1000);
  while (!isTradingDayDate(target.toISOString().slice(0, 10).replace(/-/g, ''))) target = new Date(target.getTime() + 24 * 60 * 60 * 1000);
  return target;
}

function scheduleAfterCloseDailyRefresh() {
  const arm = () => {
    const next = nextAfterCloseTime();
    void writeRuntimeJson(AFTER_CLOSE_SCHEDULE_FILE, {
      schema: 'ZHANGCAI_HARNESS_AFTER_CLOSE_SCHEDULE_V1',
      enabled: true,
      timezone: 'Asia/Shanghai',
      schedule: '每个交易日收盘后 16:30',
      guard: '本地交易日历；周末和闭市日跳过；日期以本地可核验数据为准',
      nextRunAt: next.toISOString(),
      pipeline: ['通达信日线补齐', '公开行情与新闻同步', '统一数据源落盘', 'DeepSeek Harness 数据校验'],
      dataPolicy: isLocalOnlyDataPolicy() ? 'strict_local_only' : 'local_first_on_demand',
      fallback: 'TDX 不可用时按明确交易日下载公开日线/行情/资讯到本地降级层，再交给 Harness 校验',
    });
    const delay = Math.max(1000, next.getTime() - Date.now());
    setTimeout(() => {
      const date = shanghaiDateText();
      const dateKey = date.replace(/-/g, '');
      const started = isTradingDayDate(dateKey)
        ? startDailyRefresh(date)
        : { status: 'skipped_non_trading_day', date, calendar: localTradingCalendar().source };
      void writeRuntimeJson(AFTER_CLOSE_SCHEDULE_FILE, {
        schema: 'ZHANGCAI_HARNESS_AFTER_CLOSE_SCHEDULE_V1', enabled: true,
        timezone: 'Asia/Shanghai', schedule: '每个交易日收盘后 16:30',
        guard: '本地交易日历；周末和闭市日跳过；日期以本地可核验数据为准',
        lastTriggeredAt: new Date().toISOString(), lastTradeDate: date, result: started,
        pipeline: ['通达信日线补齐', '公开行情与新闻同步', '统一数据源落盘', 'DeepSeek Harness 数据校验'],
        dataPolicy: isLocalOnlyDataPolicy() ? 'strict_local_only' : 'local_first_on_demand',
        fallback: 'TDX 不可用时按明确交易日下载公开日线/行情/资讯到本地降级层，再交给 Harness 校验',
      });
      console.log(`[agent] 收盘后静默刷新触发：${date} · ${started.status}`);
      arm();
    }, delay);
  };
  arm();
}

const server = http.createServer(async (req, res) => {
  // CORS alone cannot prevent cross-site POST side effects. The packaged
  // bridge accepts browser requests only from its own allocated UI origin.
  if (PACKAGED_RUNTIME && req.headers.origin && req.headers.origin !== process.env.ZHANGCAI_DESKTOP_ORIGIN) {
    json(res, 403, { status: 'error', error: '请求来源不属于当前桌面客户端。' });
    return;
  }
  // 浏览器、旧版网页或手工配置可能把根地址和接口路径拼成
  // `//agent/start`。Node 不会自动折叠重复斜杠，原来会直接落到
  // “路径不存在”；在路由前只规范化 URL 路径，不改变查询参数。
  const rawRequestUrl = typeof req.url === 'string' && req.url ? req.url : '/';
  try {
    // URL("//agent/start", base) treats the first segment as a host, so
    // collapse leading slashes before constructing the absolute URL.
    const requestTarget = rawRequestUrl.replace(/^\/{2,}/, '/');
    const parsedRequestUrl = new URL(requestTarget, `http://${req.headers.host || `${HOST}:${PORT}`}`);
    const normalizedPath = parsedRequestUrl.pathname.replace(/\/{2,}/g, '/');
    req.url = `${normalizedPath}${parsedRequestUrl.search}`;
  } catch {
    req.url = rawRequestUrl.replace(/^\/{2,}/, '/');
  }
  if (req.method === 'OPTIONS') { res.writeHead(204, corsHeaders(req)); res.end(); return; }
  if (req.method === 'GET' && req.url === '/health') {
    json(res, 200, { status: 'ok', service: 'zhangcai-local-bridge', port: PORT, appRoot: APP_ROOT, dataRoot: DATA_ROOT, resourceLibrary: RESOURCE_LIBRARY_ROOT, codePolicy: PACKAGED_RUNTIME ? 'embedded-in-exe-resources' : 'workspace', skills: SKILL_SOURCE, harness: 'DeepSeek Harness headless', runtimePolicy: RUNTIME_POLICY_FILE, capabilities: BRIDGE_CAPABILITIES });
    return;
  }
  if (req.method === 'GET' && req.url === '/runtime/credentials') {
    json(res, 200, { status: 'ok', ...credentialStatus() });
    return;
  }
  if (req.method === 'POST' && req.url === '/runtime/credentials') {
    try {
      const payload = JSON.parse(await readBody(req) || '{}');
      const apiKey = typeof payload?.apiKey === 'string' ? payload.apiKey.trim() : '';
      if (apiKey.length < 12 || /[\r\n]/.test(apiKey)) {
        json(res, 422, { status: 'error', error: 'DeepSeek API 密钥格式无效' });
        return;
      }
      await mkdir(RESOURCE_LIBRARY_ROOT, { recursive: true });
      await writeFile(CREDENTIALS_ENV_FILE, `# 掌财桌面 Harness 凭据；仅保存在当前用户资源库。\nDEEPSEEK_API_KEY=${apiKey}\n`, { encoding: 'utf8', mode: 0o600 });
      process.env.DEEPSEEK_API_KEY = apiKey;
      deepSeekCredentialSource = CREDENTIALS_ENV_FILE;
      json(res, 200, { status: 'ok', ...credentialStatus(), resourceLibrary: resourceLibraryStatus() });
    } catch (error) {
      json(res, 500, { status: 'error', error: error instanceof Error ? error.message : 'Harness 凭据保存失败' });
    }
    return;
  }
  if (req.method === 'GET' && req.url === '/reports/archive') {
    json(res, 200, { status: 'ok', root: path.join(DATA_ROOT, 'reports', 'archive'), index: path.join(DATA_ROOT, 'reports', 'archive', 'index.json'), reports: readLocalReportArchive() });
    return;
  }
  if (req.method === 'POST' && req.url === '/reports/archive') {
    try {
      const record = JSON.parse(await readBody(req) || '{}');
      const saved = await persistLocalReportArchive(record);
      json(res, 200, saved);
    } catch (error) {
      json(res, 400, { status: 'error', error: error instanceof Error ? error.message : '报告本地落盘失败' });
    }
    return;
  }
  if (req.method === 'DELETE' && req.url.startsWith('/reports/archive/')) {
    try {
      const id = decodeURIComponent(req.url.slice('/reports/archive/'.length).split('?')[0]);
      json(res, 200, await deleteLocalReportArchive(id));
    } catch (error) {
      json(res, 400, { status: 'error', error: error instanceof Error ? error.message : '报告本地删除失败' });
    }
    return;
  }
  if (req.method === 'GET' && req.url === '/skill14/catalog') {
    try { json(res, 200, { status: 'ok', catalog: skill14Catalog() }); } catch (error) { json(res, 500, { status: 'error', error: error instanceof Error ? error.message : '目录读取失败' }); }
    return;
  }
  if (req.method === 'GET' && req.url === '/skill14/status') {
    try { json(res, 200, await runSkill14Runtime('status')); } catch (error) { json(res, 502, { status: 'error', error: error instanceof Error ? error.message : '数据状态读取失败' }); }
    return;
  }
  if (req.method === 'GET' && req.url === '/skill14/reports') {
    try { json(res, 200, await runSkill14Runtime('list-reports')); } catch (error) { json(res, 502, { status: 'error', error: error instanceof Error ? error.message : '报告目录读取失败' }); }
    return;
  }
  if (req.method === 'POST' && req.url === '/skill14/archive-daily') {
    try { json(res, 200, await runSkill14Runtime('archive-daily', [], Number(process.env.ZHANGCAI_DAILY_ARCHIVE_TIMEOUT_MS || 600000))); } catch (error) { json(res, 502, { status: 'error', error: error instanceof Error ? error.message : '日线归档失败' }); }
    return;
  }
  if (req.method === 'POST' && req.url === '/skill14/prepare-packages') {
    try { json(res, 200, await runSkill14Runtime('prepare-packages', [], Number(process.env.ZHANGCAI_SKILL14_PREPARE_TIMEOUT_MS || 600000))); } catch (error) { json(res, 502, { status: 'error', error: error instanceof Error ? error.message : '技能包部署失败' }); }
    return;
  }
  if (req.method === 'POST' && req.url === '/skill14/preflight') {
    try {
      const payload = JSON.parse(await readBody(req) || '{}');
      const skillId = typeof payload?.skillId === 'string' ? payload.skillId.slice(0, 100) : '';
      if (!skill14Catalog().skills.some((skill) => skill?.id === skillId)) { json(res, 422, { status: 'error', error: '未知的 14 技能 ID' }); return; }
      json(res, 200, await runSkill14Runtime('preflight', ['--skill-id', skillId]));
    } catch (error) {
      json(res, 502, { status: 'error', error: error instanceof Error ? error.message : '技能预检失败' });
    }
    return;
  }
  if (req.method === 'POST' && req.url === '/runtime/tdx/open') {
    try {
      const result = await runLocalScript('tdx_runtime_bridge.py', ['open'], 60000, 12000);
      const payload = JSON.parse(result.output || '{}');
      const accepted = ['accepted', 'already_open'].includes(String(payload?.status));
      json(res, accepted ? 200 : 503, payload);
    } catch (error) {
      json(res, 502, { status: 'error', error: error instanceof Error ? error.message : '打开通达信失败' });
    }
    return;
  }
  if (req.method === 'GET' && req.url === '/runtime/resource-context') {
    json(res, 200, resourceLibraryContext());
    return;
  }
  if (req.method === 'GET' && req.url.startsWith('/runtime/environment?')) {
    const requestUrl = new URL(req.url, `http://${HOST}:${PORT}`);
    if (requestUrl.searchParams.get('summary') === '1') {
      const cachedTdx = readJson(path.join(DATA_ROOT, 'runtime', 'tdx-runtime-status.json')) || {};
      const currentStatus = readJson(path.join(DATA_ROOT, 'status', 'current.json')) || {};
      const dailyArchive = readJson(path.join(DATA_ROOT, 'status', 'tdx-daily-history.json')) || {};
      const tdxAsset = currentStatus.assets?.tdx_daily_history || {};
      const checkedAt = cachedTdx.generatedAt || currentStatus.checked_at || dailyArchive.checked_at || '';
      const ageMs = checkedAt ? Math.max(0, Date.now() - Date.parse(checkedAt)) : Number.POSITIVE_INFINITY;
      const processState = cachedTdx.processState && typeof cachedTdx.processState === 'object' ? cachedTdx.processState : {};
      const cacheStale = !Number.isFinite(ageMs) || ageMs > 30000;
      const lastKnownTdxStatus = processState.running === true
        ? (processState.rootMatches === false ? 'path_mismatch' : processState.rootMatches === true ? 'open' : 'open_unverified')
        : processState.running === false ? 'closed' : 'unknown';
      const credentials = credentialStatus();
      json(res, 200, {
        status: 'ok',
        summary: true,
        stale: cacheStale,
        checkedAt,
        bridge: { status: 'ok', host: HOST, port: PORT },
        harness: { status: credentials.configured ? 'ready' : 'missing_credentials', credentialsConfigured: credentials.configured, credentialSource: credentials.source, keyHint: credentials.keyHint, base: 'DeepSeek Harness' },
        resourceLibrary: { ...resourceLibraryStatus(), assets: Object.fromEntries(Object.entries(currentStatus.assets || {}).map(([name, value]) => [name, value?.status || 'unknown'])) },
        codePolicy: PACKAGED_RUNTIME ? 'embedded-in-exe-resources' : 'workspace',
        minuteData: currentStatus.minute_data || { status: 'unknown', reason: '详细检查将在后台更新。' },
        tdx: {
          status: cacheStale ? 'unknown' : lastKnownTdxStatus,
          lastKnownStatus: lastKnownTdxStatus,
          rootMatches: typeof processState.rootMatches === 'boolean' ? processState.rootMatches : null,
          root: bridgeTdxRoot() || '',
          checkedAt,
        },
        daily: { status: tdxAsset.status || dailyArchive.status || 'unknown', date: dailyArchive.trade_date || tdxAsset.trade_date || tdxAsset.freshness?.selected_trade_date || '', freshness: tdxAsset.freshness || {} },
        dailyArchive: { status: dailyArchive.status || 'unknown', trade_date: dailyArchive.trade_date || '', checked_at: dailyArchive.checked_at || '' },
      });
      return;
    }
  }
  if (req.method === 'GET' && req.url === '/runtime/environment') {
    try {
      const tdxRoot = bridgeTdxRoot();
      const tdxStatusResult = await runLocalScript('tdx_runtime_bridge.py', ['status'], 60000, 0);
      const tdxStatus = JSON.parse(tdxStatusResult.output || '{}');
      const daily = inspectTdxDailyIntegrity(tdxRoot);
      const dailyFreshness = dailyFreshnessSnapshot(daily);
      const snapshots = dailySnapshotSummary(daily);
      const dailyState = readJson(DAILY_STATE_FILE) || {};
      const unifiedArchive = compactUnifiedArchiveState(readJson(UNIFIED_ARCHIVE_STATE_FILE) || {});
      const unifiedVerification = readJson(UNIFIED_VERIFY_STATE_FILE) || {};
      const unifiedManifest = readJson(path.join(DATA_ROOT, 'evidence', 'sources', 'latest.json')) || {};
      const dailyArchive = readJson(path.join(DATA_ROOT, 'status', 'tdx-daily-history.json')) || {};
      const harnessOutput = String(dailyState?.harness?.output || '');
      let harnessValidation = { status: dailyState?.harness?.status || 'missing', dataDate: '', summary: '', sourceCount: 0 };
      try {
        const parsed = JSON.parse(harnessOutput);
        harnessValidation = {
          status: String(parsed?.status || harnessValidation.status),
          dataDate: String(parsed?.data_date || ''),
          summary: String(parsed?.summary || ''),
          sourceCount: Array.isArray(parsed?.tables) ? parsed.tables.reduce((count, table) => count + (Array.isArray(table?.rows) ? table.rows.length : 0), 0) : 0,
        };
      } catch { /* 校验输出可能仍在生成，保留本地状态 */ }
      const targetDataDate = String(harnessValidation.dataDate || dailyState.date || snapshots.publicMarket.date || '');
      const rollingSources = new Set(['akshareLhbStockStatistic']);
      const publicSources = Object.entries(snapshots.publicMarket.sources || {}).map(([name, source]) => ({
        name,
        status: source.status,
        date: snapshots.publicMarket.date,
        fetchedAt: snapshots.publicMarket.fetchedAt,
        recordCount: source.recordCount,
        providerSuccess: source.providerSuccess,
        fresh: source.status === 'available' && snapshots.publicMarket.date === targetDataDate && !rollingSources.has(name),
      }));
      publicSources.push({
        name: 'news',
        status: snapshots.news.status,
        date: snapshots.news.date,
        fetchedAt: snapshots.news.fetchedAt,
        recordCount: snapshots.news.sameDayRecordCount,
        providerSuccess: snapshots.news.status === 'available',
        fresh: snapshots.news.status === 'available' && snapshots.news.date === targetDataDate,
      });
      const launcher = commandFor('environment-probe').command;
      const credentials = credentialStatus();
      const resourceContext = resourceLibraryContext();
      json(res, 200, {
        status: 'ok',
        checkedAt: new Date().toISOString(),
        bridge: { status: 'ok', host: HOST, port: PORT },
        harness: { status: credentials.configured ? 'ready' : 'missing_credentials', launcher, credentialsConfigured: credentials.configured, credentialSource: credentials.source, keyHint: credentials.keyHint, base: 'DeepSeek Harness' },
        resourceLibrary: { ...resourceLibraryStatus(), assets: resourceContext.assets, paths: resourceContext.paths },
        codePolicy: PACKAGED_RUNTIME ? 'embedded-in-exe-resources' : 'workspace',
        minuteData: inspectMinuteData(tdxRoot),
        tdx: {
          status: tdxStatus.processState?.running === true
            ? (tdxStatus.processState?.rootMatches === false ? 'path_mismatch' : tdxStatus.processState?.rootMatches === true ? 'open' : 'open_unverified')
            : tdxStatus.processState?.running === false ? 'closed' : 'unknown',
          rootMatches: tdxStatus.processState?.rootMatches ?? null,
          processes: tdxStatus.processes || [],
          root: tdxRoot,
          formulas: tdxStatus.formulaRegistry || {},
          freshness: tdxStatus.freshness || {},
        },
        daily: { ...daily, ...dailyFreshness },
        dailyArchive,
        dailyDataIndex: snapshots.dailyDataIndex,
        sources: publicSources,
        harnessValidation,
        supplemental: snapshots.supplemental,
        dailyRefresh: dailyState,
        dailyIndexInitialization: readJson(DAILY_INDEX_INITIALIZATION_STATE_FILE),
        canonicalDailyIndex: (() => {
          const index = readJson(CANONICAL_DAILY_INDEX_FILE);
          return index ? {
            status: 'ready', path: CANONICAL_DAILY_INDEX_FILE,
            symbolCount: Number(index.symbol_count || 0), recordCount: Number(index.record_count || 0),
            generatedAt: index.generated_at || '', sourceFile: CANONICAL_DAILY_FILE,
          } : { status: 'missing', path: CANONICAL_DAILY_INDEX_FILE, symbolCount: 0, recordCount: 0, generatedAt: '', sourceFile: CANONICAL_DAILY_FILE };
        })(),
        supplementalRefresh: readJson(SUPPLEMENTAL_STATE_FILE),
        unifiedArchive,
        unifiedVerification,
        unifiedSourceManifest: {
          status: unifiedManifest.status || 'missing',
          tradeDate: unifiedManifest.trade_date || '',
          manifest: unifiedManifest.manifest || 'evidence/sources/latest.json',
          sourceCount: Array.isArray(unifiedManifest.sources) ? unifiedManifest.sources.length : 0,
          availableSourceCount: Array.isArray(unifiedManifest.sources) ? unifiedManifest.sources.filter((source) => source?.status === 'available').length : 0,
          sources: Array.isArray(unifiedManifest.sources) ? unifiedManifest.sources : [],
        },
      });
    } catch (error) {
      json(res, 502, { status: 'error', error: error instanceof Error ? error.message : '运行环境检测失败' });
    }
    return;
  }
  if (req.method === 'GET' && req.url === '/data/archive/status') {
    const state = readJson(UNIFIED_ARCHIVE_STATE_FILE);
    let report = null;
    try { report = await ensureUnifiedArchiveReport(state); } catch (error) { console.warn(`[agent] 统一落盘报告生成失败：${error instanceof Error ? error.message : String(error)}`); }
    const progress = unifiedArchiveProgress(state);
    const runningJob = [...unifiedArchiveJobs.values()].find((job) => job.status === 'running');
    const message = runningJob
      ? `统一数据落盘正在运行：${progress.currentStep || '准备下一步'}（${progress.completed}/${progress.total}）`
      : state?.status === 'completed'
        ? '统一数据落盘已完成，报告和 Harness 上下文已写入 resource-library。'
        : state?.status === 'partial'
          ? '统一数据落盘已结束，但存在降级来源或未通过步骤，详见报告。'
          : state?.status === 'failed'
            ? '统一数据落盘失败，详见报告中的错误步骤。'
            : '尚未执行统一数据落盘。';
    json(res, 200, { status: 'ok', state, progress, report, message, jobs: [...unifiedArchiveJobs.values()].slice(-3) });
    return;
  }
  if (req.method === 'GET' && req.url === '/data/archive/verify/status') {
    json(res, 200, { status: 'ok', state: readJson(UNIFIED_VERIFY_STATE_FILE), jobs: [...unifiedVerificationJobs.values()].slice(-3) });
    return;
  }
  if (req.method === 'GET' && req.url === '/data/archive/manifest') {
    const manifest = readJson(path.join(DATA_ROOT, 'evidence', 'sources', 'latest.json'));
    json(res, manifest ? 200 : 404, manifest || { status: 'missing', error: '尚未生成统一数据源清单' });
    return;
  }
  if (req.method === 'GET' && (req.url.startsWith('/data/archive/report') || req.url.startsWith('/data/archive/report.json'))) {
    try {
      const requested = new URL(req.url, `http://${HOST}:${PORT}`);
      const dateKey = compactDateKey(requested.searchParams.get('date') || 'latest');
      const descriptor = unifiedArchiveReportDescriptor(dateKey);
      const wantsJson = requested.pathname === '/data/archive/report.json' || requested.searchParams.get('format') === 'json';
      const reportFile = wantsJson ? descriptor.jsonFile : descriptor.htmlFile;
      const fallbackFile = wantsJson ? descriptor.latestJsonFile : descriptor.latestHtmlFile;
      const file = existsSync(reportFile) ? reportFile : fallbackFile;
      if (!existsSync(file)) {
        json(res, 404, { status: 'missing', error: '统一数据落盘报告尚未生成', date: dateKey });
        return;
      }
      res.writeHead(200, {
        'Content-Type': wantsJson ? 'application/json; charset=utf-8' : 'text/html; charset=utf-8',
        'Cache-Control': 'no-store',
        ...corsHeaders(req),
      });
      res.end(readFileSync(file, 'utf8'));
    } catch (error) {
      json(res, 500, { status: 'error', error: error instanceof Error ? error.message : '统一数据落盘报告读取失败' });
    }
    return;
  }
  if (req.method === 'POST' && req.url === '/data/archive/start') {
    try {
      const payload = JSON.parse(await readBody(req) || '{}');
      const rawDate = typeof payload?.date === 'string' ? payload.date.replace(/[^0-9]/g, '') : '';
      const date = rawDate.length === 8 ? `${rawDate.slice(0, 4)}-${rawDate.slice(4, 6)}-${rawDate.slice(6)}` : localTradeDate();
      json(res, 202, startUnifiedDataArchive(date, payload?.force === true));
    } catch (error) {
      json(res, 400, { status: 'error', error: error instanceof Error ? error.message : '统一数据落盘启动失败' });
    }
    return;
  }
  if (req.method === 'POST' && req.url === '/data/archive/verify') {
    try {
      const payload = JSON.parse(await readBody(req) || '{}');
      const rawDate = typeof payload?.date === 'string' ? payload.date.replace(/[^0-9]/g, '') : '';
      const date = rawDate.length === 8 ? `${rawDate.slice(0, 4)}-${rawDate.slice(4, 6)}-${rawDate.slice(6)}` : localTradeDate();
      json(res, 202, startUnifiedDataVerification(date, payload?.force === true));
    } catch (error) {
      json(res, 400, { status: 'error', error: error instanceof Error ? error.message : '统一数据校验启动失败' });
    }
    return;
  }
  if (req.method === 'POST' && req.url === '/data/daily/initialize') {
    try {
      const payload = JSON.parse(await readBody(req) || '{}');
      const result = startDailyIndexInitialization(payload?.force === true);
      json(res, result.status === 'busy' ? 409 : 202, result);
    } catch (error) {
      json(res, 400, { status: 'error', error: error instanceof Error ? error.message : '全量个股索引初始化启动失败' });
    }
    return;
  }
  if (req.method === 'GET' && req.url === '/data/daily/initialize/status') {
    json(res, 200, {
      status: 'ok',
      state: readJson(DAILY_INDEX_INITIALIZATION_STATE_FILE),
      jobs: [...dailyIndexInitializationJobs.values()].slice(-3),
    });
    return;
  }
  if (req.method === 'GET' && req.url === '/data/daily/status') {
    json(res, 200, {
      status: 'ok',
      state: readJson(DAILY_STATE_FILE),
      jobs: [...dailyJobs.values()].slice(-3),
      initialization: readJson(DAILY_INDEX_INITIALIZATION_STATE_FILE),
    });
    return;
  }
  if (req.method === 'GET' && req.url === '/data/daily/integrity') {
    try {
      const reportName = readdirSync(RUNTIME_ROOT)
        .filter((name) => /^tdx-daily-integrity-\d{8}-\d{6}\.json$/.test(name))
        .sort()
        .at(-1);
      const report = reportName ? readJson(path.join(RUNTIME_ROOT, reportName)) : null;
      if (!report) { json(res, 404, { status: 'missing', error: '尚未生成日线完整性报告' }); return; }
      json(res, 200, { status: 'ok', report });
    } catch (error) {
      json(res, 500, { status: 'error', error: error instanceof Error ? error.message : '日线完整性报告读取失败' });
    }
    return;
  }
  if (req.method === 'GET' && req.url.startsWith('/data/daily/index')) {
    const index = readJson(DAILY_DATA_INDEX_FILE);
    json(res, index ? 200 : 404, index || { status: 'missing', path: DAILY_DATA_INDEX_FILE, error: '统一日线可用性索引不存在' });
    return;
  }
  if (req.method === 'POST' && req.url === '/data/daily/recover') {
    try {
      const payload = JSON.parse(await readBody(req) || '{}');
      const rawDate = typeof payload?.date === 'string' ? payload.date.replace(/[^0-9]/g, '') : '';
      const date = rawDate.length === 8 ? `${rawDate.slice(0, 4)}-${rawDate.slice(4, 6)}-${rawDate.slice(6)}` : localTradeDate();
      const codes = typeof payload?.codes === 'string' ? payload.codes : Array.isArray(payload?.codes) ? payload.codes.join(',') : '';
      json(res, 200, await runDailyRecovery(date, codes, payload?.maxSymbols));
    } catch (error) {
      json(res, 502, { status: 'error', error: error instanceof Error ? error.message : '公开日线降级补齐失败' });
    }
    return;
  }
  if (req.method === 'GET' && req.url === '/data/public/status') {
    json(res, 200, { status: 'ok', state: readJson(SUPPLEMENTAL_STATE_FILE), jobs: [...supplementalJobs.values()].slice(-3) });
    return;
  }
  if (req.method === 'GET' && req.url === '/data/public') {
    const snapshot = readJson(path.join(DATA_ROOT, 'public', 'latest.json'));
    json(res, snapshot ? 200 : 404, snapshot || { status: 'missing', error: '公开行情快照不存在' });
    return;
  }
  if (req.method === 'GET' && req.url.startsWith('/data/supplemental')) {
    try {
      const url = new URL(req.url, `http://${HOST}:${PORT}`);
      const requested = url.searchParams.get('date') || localTradeDate();
      const snapshot = readSupplementalSnapshot(requested);
      if (!snapshot) {
        json(res, 404, { status: 'missing', date: supplementalDateKey(requested), error: '统一补充数据快照不存在' });
        return;
      }
      const market = snapshot.market && typeof snapshot.market === 'object' ? snapshot.market : {};
      const index = market.index_daily || {};
      const lhb = market.longhubang || {};
      const margin = market.margin || {};
      json(res, 200, {
        status: 'ok',
        schema: snapshot.schema,
        date: snapshot.trade_date || snapshot.requested_date,
        generatedAt: snapshot.generated_at,
        snapshotPath: snapshot.snapshot_path,
        coverage: snapshot.coverage || {},
        market: {
          indexDaily: { status: index.status || 'missing', source: index.source || '', symbolCount: index.data?.symbol_count || 0, sourceDate: index.source_date || '' },
          longhubang: { status: lhb.status || 'missing', source: lhb.source || '', snapshotExists: lhb.data?.snapshot_exists === true, recordCount: lhb.data?.record_count || 0, marketRecordCount: lhb.data?.market_record_count || 0, sourceDate: lhb.source_date || '' },
          margin: { status: margin.status || 'missing', source: margin.source || '', exactDate: margin.exact_date === true, latestAvailableDate: margin.latest_available_date || '', recordCount: margin.data?.record_count || 0, exactRecordCount: margin.data?.exact_record_count || 0, sourceDate: margin.source_date || '' },
        },
      });
    } catch (error) {
      json(res, 502, { status: 'error', error: error instanceof Error ? error.message : '统一补充数据读取失败' });
    }
    return;
  }
  if (req.method === 'GET' && req.url === '/data/harness/daily') {
    const context = readJson(path.join(HARNESS_CONTEXT_ROOT, 'latest-data.json'));
    if (!context) { json(res, 404, { status: 'missing', error: 'Harness 每日校验结果不存在' }); return; }
    // Context files are immutable run receipts; refresh the lightweight index
    // view so the page/Harness sees newly added fallback coverage immediately.
    const snapshots = dailySnapshotSummary();
    json(res, 200, { ...context, snapshots, dailyDataIndex: snapshots.dailyDataIndex });
    return;
  }
  if (req.method === 'GET' && req.url.startsWith('/data/harness/skill/')) {
    const skillId = decodeURIComponent(req.url.slice('/data/harness/skill/'.length).split('?')[0]).slice(0, 160);
    const job = latestHarnessSkillJob(skillId);
    json(res, job ? 200 : 404, job || { status: 'missing', skill_id: skillId, error: '该技能尚无已完成 Harness 报告' });
    return;
  }
  if (req.method === 'POST' && req.url === '/data/daily/start') {
    try {
      const payload = JSON.parse(await readBody(req) || '{}');
      const rawDate = typeof payload?.date === 'string' ? payload.date.replace(/[^0-9]/g, '') : '';
      const date = rawDate.length === 8 ? `${rawDate.slice(0, 4)}-${rawDate.slice(4, 6)}-${rawDate.slice(6)}` : localTradeDate();
      json(res, 202, startDailyRefresh(date, payload?.force === true));
    } catch (error) {
      json(res, 400, { status: 'error', error: error instanceof Error ? error.message : '每日数据更新启动失败' });
    }
    return;
  }
  if (req.method === 'POST' && req.url === '/data/public/start') {
    try {
      const payload = JSON.parse(await readBody(req) || '{}');
      const rawDate = typeof payload?.date === 'string' ? payload.date.replace(/[^0-9]/g, '') : '';
      const date = rawDate.length === 8 ? `${rawDate.slice(0, 4)}-${rawDate.slice(4, 6)}-${rawDate.slice(6)}` : localTradeDate();
      json(res, 202, startSupplementalRefresh(date, payload?.force === true));
    } catch (error) {
      json(res, 400, { status: 'error', error: error instanceof Error ? error.message : '其他数据补齐启动失败' });
    }
    return;
  }
  if (req.method === 'GET' && req.url.startsWith('/stock/supplemental')) {
    try {
      const url = new URL(req.url, `http://${HOST}:${PORT}`);
      const normalized = normalizeHistorySymbol(url.searchParams.get('symbol') || url.searchParams.get('code') || '');
      if (!normalized) {
        json(res, 400, { status: 'error', error: '需要六位股票代码，可附带 .SH、.SZ 或 .BJ' });
        return;
      }
      const requested = url.searchParams.get('date') || localTradeDate();
      const data = await ensureStockSupplemental(normalized.symbol, requested);
      json(res, data ? 200 : 404, data || { status: 'missing', code: normalized.code, date: requested, error: '补充数据快照不存在' });
    } catch (error) {
      json(res, 502, { status: 'error', error: error instanceof Error ? error.message : '个股补充数据读取失败' });
    }
    return;
  }
  if (req.method === 'GET' && req.url.startsWith('/market/history')) {
    try {
      const url = new URL(req.url, `http://${HOST}:${PORT}`);
      if (url.pathname === '/market/history/index') {
        const index = await buildTdxHistoryIndex(url.searchParams.get('refresh') === '1');
        const symbol = url.searchParams.get('symbol');
        const normalized = symbol ? normalizeHistorySymbol(symbol) : null;
        json(res, 200, {
          status: 'ok',
          schema: index.schema,
          source_root: index.source_root,
          source_kind: index.source_kind,
          index_path: TDX_HISTORY_INDEX_FILE,
          daily_data_index_path: DAILY_DATA_INDEX_FILE,
          generated_at: index.generated_at,
          cached: index.cached === true,
          source_available: index.source_available !== false,
          degraded_reason: index.degraded_reason || '',
          symbol_count: index.symbol_count,
          fallback_index_summary: (() => { const daily = readJson(DAILY_DATA_INDEX_FILE); return daily?.summary || { symbol_count: 0, fallback_symbol_count: 0, fallback_record_count: 0, date_count: 0 }; })(),
          canonical_index: (() => { const canonical = readJson(CANONICAL_DAILY_INDEX_FILE); return canonical ? { path: CANONICAL_DAILY_INDEX_FILE, symbol_count: canonical.symbol_count || 0, record_count: canonical.record_count || 0, generated_at: canonical.generated_at || '', source_size: canonical.source_size || 0 } : { path: CANONICAL_DAILY_INDEX_FILE, symbol_count: 0, record_count: 0, generated_at: '', source_size: 0 }; })(),
          entry: normalized ? index.symbols?.[normalized.key] || null : undefined,
        });
        return;
      }
      if (url.pathname === '/market/history') {
        const result = await queryTdxHistory(
          url.searchParams.get('symbol') || '',
          url.searchParams.get('limit'),
          url.searchParams.get('refresh') === '1',
        );
        json(res, result.status === 'missing' ? 404 : 200, result);
        return;
      }
    } catch (error) {
      json(res, 502, { status: 'error', error: error instanceof Error ? error.message : '本地日线索引读取失败' });
    }
    return;
  }
  if (req.method === 'GET' && (req.url === '/market' || req.url.startsWith('/market?scope='))) {
    try {
      const url = new URL(req.url, `http://${HOST}:${PORT}`);
      const requestedScope = url.searchParams.get('scope') || '';
      if (requestedScope === 'latest') {
        const latest = readJson(path.join(RUNTIME_ROOT, 'market-latest.json'));
        if (!latest || latest.status !== 'ok') {
          json(res, 404, { status: 'missing', error: '尚无本地最新完整日线快照，请先执行一次市场数据刷新' });
          return;
        }
        json(res, 200, latest);
        return;
      }
      const scope = requestedScope === 'market' ? 'market' : requestedScope === 'watchlist' ? 'watchlist' : 'indices';
      const codes = url.searchParams.get('codes') || '';
      const result = await runMarketRefresh(scope, codes);
      if (scope === 'market' || scope === 'indices') await persistMarketSnapshot(scope, result);
      json(res, 200, result);
    } catch (error) {
      json(res, 502, { status: 'error', error: error instanceof Error ? error.message : '实时行情刷新失败' });
    }
    return;
  }
  if (req.method === 'GET' && req.url.startsWith('/stock/quote')) {
    try {
      const url = new URL(req.url, `http://${HOST}:${PORT}`);
      const normalized = normalizeHistorySymbol(url.searchParams.get('symbol') || url.searchParams.get('code') || '');
      if (!normalized) {
        json(res, 400, { status: 'error', error: '需要六位股票代码，可附带 .SH、.SZ 或 .BJ' });
        return;
      }
      const result = await runMarketRefresh('watchlist', normalized.code);
      const quote = (Array.isArray(result.stocks) ? result.stocks : [])
        .find((row) => String(row?.code || '') === normalized.code);
      if (!quote || Number(quote.close || 0) <= 0) {
        json(res, 404, {
          status: 'missing',
          symbol: normalized.symbol,
          source: result.source || '',
          fallback: result.fallback === true,
          error: '当前行情源没有返回该股票的最新价格',
        });
        return;
      }
      await persistMarketSnapshot('watchlist', result);
      json(res, 200, {
        status: 'ok',
        symbol: normalized.symbol,
        quote,
        source: result.source || '',
        quality: result.quality || (result.fallback === true ? 'degraded' : 'primary'),
        fallback: result.fallback === true,
        fallbackReason: result.fallbackReason || '',
        quoteMode: result.quoteMode || quote.quoteMode || '',
        fetchedAt: result.fetchedAt || new Date().toISOString(),
        tradeDate: result.tradeDate || quote.date || '',
        scope: result.scope || '个股最新价格',
      });
    } catch (error) {
      json(res, 502, { status: 'error', error: error instanceof Error ? error.message : '个股最新价格读取失败' });
    }
    return;
  }
  if (req.method === 'GET' && req.url.startsWith('/stock/quick')) {
    try {
      const url = new URL(req.url, `http://${HOST}:${PORT}`);
      const rawSymbol = url.searchParams.get('symbol') || '';
      const digits = rawSymbol.replace(/[^0-9]/g, '').slice(-6);
      if (digits.length !== 6) {
        json(res, 400, { status: 'error', error: '需要六位股票代码' });
        return;
      }
      // 北交所新代码 920xxx 也以 9 开头，必须优先判为 BJ；否则会被
      // 误送到 SH，TQ 只能返回 ErrorId=0 而没有任何指标字段。
      const market = /^(920|[48])/.test(digits)
        ? 'BJ'
        : /\\.(SH|上交所)$/i.test(rawSymbol) || /^[569]/.test(digits)
          ? 'SH'
          : 'SZ';
      const result = await runFiveFormulas(`${digits}.${market}`);
      json(res, 200, result);
    } catch (error) {
      json(res, 502, { status: 'error', error: error instanceof Error ? error.message : '五公式桥接执行失败' });
    }
    return;
  }
  if (req.method === 'POST' && req.url === '/stock/quick/batch') {
    try {
      const payload = JSON.parse(await readBody(req) || '{}');
      const rawSymbols = Array.isArray(payload?.symbols) ? payload.symbols : [];
      const symbols = [...new Set(rawSymbols.map((value) => String(value || '').trim().toUpperCase()))]
        .filter((value) => /^\d{6}\.(SH|SZ|BJ)$/.test(value))
        .slice(0, 10);
      if (!symbols.length) {
        json(res, 400, { status: 'error', error: '需要至少一只六位代码和市场后缀的股票' });
        return;
      }
      const result = await runFiveFormulasBatch(symbols);
      json(res, result.status === 'ok' ? 200 : 207, result);
    } catch (error) {
      json(res, 502, { status: 'error', error: error instanceof Error ? error.message : '批量五公式桥接执行失败' });
    }
    return;
  }
  if (req.method === 'POST' && req.url === '/strategy/golden-ignition/single') {
    try {
      const payload = JSON.parse(await readBody(req) || '{}');
      const normalized = normalizeSingleSignalSymbol(payload?.symbol);
      if (!normalized) {
        json(res, 400, { status: 'error', error: '需要六位股票代码，可带 .SH、.SZ 或 .BJ 后缀' });
        return;
      }
      const lookback = Math.max(1, Math.min(30, Number(payload?.lookback) || 5));
      const result = await runGoldenIgnitionSymbol(normalized, lookback);
      json(res, 200, result);
    } catch (error) {
      json(res, 502, { status: 'error', error: error instanceof Error ? error.message : '黄金点火单股执行失败' });
    }
    return;
  }
  if (req.method === 'POST' && req.url === '/strategy/selection/scored') {
    try {
      const payload = JSON.parse(await readBody(req) || '{}');
      const strategyId = String(payload?.strategyId || '');
      const allowed = new Set(['golden-ignition-v8', 'short-burst-score-v5', 'quant-production-v65']);
      if (!allowed.has(strategyId)) {
        json(res, 422, { status: 'error', error: '该策略未配置原始评分入口', strategy_id: strategyId });
        return;
      }
      const candidates = Array.isArray(payload?.candidates) ? payload.candidates.slice(0, 30) : [];
      if (!candidates.length) {
        json(res, 400, { status: 'error', error: '需要至少一只本地条件候选' });
        return;
      }
      const result = await runSelectionScoreRuntime({
        strategyId,
        date: String(payload?.date || localTradeDate()).replace(/[^0-9]/g, '').slice(0, 8),
        candidates,
      });
      json(res, 200, result);
    } catch (error) {
      json(res, 502, { status: 'error', error: error instanceof Error ? error.message : '原始策略评分执行失败' });
    }
    return;
  }
  if (req.method === 'POST' && req.url === '/strategy/start') {
    try {
      const payload = JSON.parse(await readBody(req) || '{}');
      const requestedSkillId = typeof payload?.skillId === 'string' ? payload.skillId.slice(0, 160) : '';
      const skillId = canonicalStrategyId(requestedSkillId);
      if (!CANONICAL_STRATEGY_IDS.has(skillId)) {
        json(res, 422, { status: 'error', error: '该策略未配置原始技能入口', skill_id: requestedSkillId });
        return;
      }
      const job = startStrategyJob(skillId);
      console.log(`[agent] strategy start ${job.id.slice(0, 8)} skill=${skillId}`);
      json(res, 202, {
        status: 'accepted',
        job_id: job.id,
        skill_id: requestedSkillId,
        canonical_skill_id: skillId,
        started_at: job.started_at,
        timeout_seconds: 22 * 60,
      });
    } catch (error) {
      json(res, 500, { status: 'error', error: error instanceof Error ? error.message : '策略后台任务启动失败' });
    }
    return;
  }
  if (req.method === 'GET' && req.url.startsWith('/strategy/job/')) {
    const id = req.url.slice('/strategy/job/'.length).split('?')[0];
    let job = strategyJobs.get(id) || readJson(strategyJobFile(id));
    if (job && job.status === 'running' && !strategyJobs.has(id)) {
      job = { ...job, status: 'failed', error: '桥接服务在原始策略返回前重启，任务未完成；可重新执行。', completed_at: Date.now() };
      persistStrategyJob(job);
    }
    if (!job) { json(res, 404, { status: 'error', error: '策略任务不存在或已过期' }); return; }
    json(res, 200, job);
    return;
  }
  if (req.method === 'POST' && req.url === '/strategy') {
    try {
      const payload = JSON.parse(await readBody(req));
      const requestedSkillId = typeof payload?.skillId === 'string' ? payload.skillId.slice(0, 160) : '';
      const result = await runCanonicalStrategy(requestedSkillId);
      json(res, 200, result);
    } catch (error) {
      json(res, 500, { status: 'error', error: error instanceof Error ? error.message : '原始策略执行失败' });
    }
    return;
  }
  if (req.method === 'POST' && req.url.startsWith('/agent/job/') && req.url.endsWith('/cancel')) {
    const id = req.url.slice('/agent/job/'.length, -'/cancel'.length);
    let job = harnessJobs.get(id) || readJson(harnessJobFile(id));
    if (!job) { json(res, 404, { status: 'error', error: 'Harness 任务不存在或已过期' }); return; }
    if (job.status !== 'running') {
      json(res, 200, { status: job.status, job_id: id, message: '任务已经结束，无需取消。' });
      return;
    }
    job.cancel_requested = true;
    job.cancelled_at = Date.now();
    harnessJobs.set(id, job);
    persistHarnessJob(job);
    if (typeof job.cancel === 'function') job.cancel();
    json(res, 202, { status: 'accepted', job_id: id, message: '已请求取消 Harness 任务。' });
    return;
  }
  if (req.method === 'GET' && req.url.startsWith('/agent/job/')) {
    const id = req.url.slice('/agent/job/'.length).split('?')[0];
    let job = harnessJobs.get(id);
    if (!job) {
      job = readJson(harnessJobFile(id));
      // 进程重启后无法继续持有原来的子进程，但任务记录不能消失。
      // 将其明确标记为未完成，前端可归档并显示，而不是得到误导性的 404。
      if (job && job.status === 'running') {
        job = {
          ...job,
          status: 'failed',
          error: '桥接服务在 Harness 返回前重启，任务未完成；可重新执行。',
          completed_at: Date.now(),
        };
        persistHarnessJob(job);
      }
    }
    console.log(`[agent] job ${id.slice(0, 8)} ${job?.status || 'missing'}`);
    if (!job) { json(res, 404, { status: 'error', error: 'Harness 任务不存在或已过期' }); return; }
    json(res, 200, job);
    return;
  }
  if (req.method === 'POST' && req.url === '/agent/start') {
    try {
      if (activeHarnessExecution) {
        json(res, 409, harnessBusyPayload());
        return;
      }
      const payload = JSON.parse(await readBody(req));
      if (!payload || typeof payload.task !== 'string' || !payload.task.trim() || !payload.market || typeof payload.market !== 'object') {
        json(res, 400, { status: 'error', error: '需要 task 和 market' });
        return;
      }
      if (!process.env.DEEPSEEK_API_KEY) {
        json(res, 503, { status: 'error', error: '未设置 DEEPSEEK_API_KEY 环境变量' });
        return;
      }
      const skillId = typeof payload.skillId === 'string' ? payload.skillId.slice(0, 160) : '';
      const task = payload.task.trim();
      const market = payload.market;
      const rawContext = payload.context;
      const job = startHarnessJob('', skillId, {
        prepare: async ({ updateProgress, cancelled }) => {
          const history = rawContext?.history;
          const count = Array.isArray(history?.bars) ? history.bars.length : 0;
          updateProgress(
            'tdx',
            'running',
            count
              ? `正在整理 ${count} 根本地 TDX 日线指标输入。`
              : '正在整理本地行情与技能输入。',
          );
          if (count) {
            updateProgress('tdx', 'completed', `已载入 ${count} 根本地日线指标输入。`);
          } else {
            updateProgress('tdx', 'completed', '本技能使用市场与技能上下文输入。');
          }
          if (cancelled()) throw new Error('用户已取消 Harness 任务。');
          const context = await enrichHarnessContext(rawContext, updateProgress);
          if (cancelled()) throw new Error('用户已取消 Harness 任务。');
          return buildPrompt(task, market, skillId, context);
        },
      });
      console.log(`[agent] start ${job.id.slice(0, 8)} skill=${skillId || 'generic'}`);
      json(res, 202, { status: 'accepted', job_id: job.id, skill_id: skillId || null, started_at: job.started_at, timeout_seconds: Math.round(timeoutForSkill(skillId) / 1000) });
    } catch (error) {
      json(res, isHarnessBusyError(error) ? 409 : 500, isHarnessBusyError(error)
        ? harnessBusyPayload()
        : { status: 'error', error: error instanceof Error ? error.message : 'Harness 后台任务启动失败' });
    }
    return;
  }
  if (req.method !== 'POST' || req.url !== '/agent') {
    json(res, 404, { status: 'error', error: '路径不存在' });
    return;
  }
  try {
    if (activeHarnessExecution) {
      json(res, 409, harnessBusyPayload());
      return;
    }
    const payload = JSON.parse(await readBody(req));
    if (!payload || typeof payload.task !== 'string' || !payload.task.trim() || !payload.market || typeof payload.market !== 'object') {
      json(res, 400, { status: 'error', error: '需要 task 和 market' });
      return;
    }
    if (!process.env.DEEPSEEK_API_KEY) {
      json(res, 503, { status: 'error', error: '未设置 DEEPSEEK_API_KEY 环境变量' });
      return;
    }
    const skillId = typeof payload.skillId === 'string' ? payload.skillId.slice(0, 160) : '';
    const context = await enrichHarnessContext(payload.context);
    const result = await runHarnessWithRetry(buildPrompt(payload.task.trim(), payload.market, skillId, context), skillId);
    const reportPath = await persistHarnessReport({ skillId, output: result.output, diagnostics: result.diagnostics, task: payload.task.trim(), dataDate: payload.market.date || '', jobId: randomUUID() });
    json(res, 200, { status: 'ok', output: result.output, diagnostics: result.diagnostics, elapsed_ms: result.elapsedMs, timeout_seconds: Math.round(result.timeoutMs / 1000), model: 'DeepSeek Harness headless', skill_id: skillId || null, data_date: payload.market.date || null, report_path: reportPath });
  } catch (error) {
    json(res, isHarnessBusyError(error) ? 409 : 500, isHarnessBusyError(error)
      ? harnessBusyPayload()
      : { status: 'error', error: error instanceof Error ? error.message : '桥接服务失败' });
  }
});

const skillBundle = ensureBundledSkills();
server.listen(PORT, HOST, () => {
  console.log(`掌财智能体 DeepSeek Harness bridge listening at http://${HOST}:${PORT} · skills ${skillBundle.status} (${skillBundle.count})`);
  void persistRuntimePolicy().catch((error) => console.error(`[agent] 无法写入自包含运行时政策：${error instanceof Error ? error.message : String(error)}`));
  scheduleAfterCloseDailyRefresh();
});
