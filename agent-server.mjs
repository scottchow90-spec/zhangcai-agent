import http from 'node:http';
import { spawn } from 'node:child_process';
import path from 'node:path';
import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync } from 'node:fs';
import { mkdir, writeFile, unlink } from 'node:fs/promises';
import { randomUUID } from 'node:crypto';

// Load the ignored local environment file before resolving the bridge
// configuration. This keeps scheduled/restarted bridge processes consistent
// without committing credentials to the project.
function loadLocalEnvFile() {
  const file = path.join(path.resolve(process.env.ZHANGCAI_APP_ROOT || process.cwd()), '.env.local');
  if (!existsSync(file)) return;
  try {
    for (const line of readFileSync(file, 'utf8').split(/\r?\n/)) {
      const match = line.match(/^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*?)\s*$/);
      if (match && !process.env[match[1]]) process.env[match[1]] = match[2].replace(/^['"]|['"]$/g, '');
    }
  } catch (error) {
    console.warn(`[agent] 无法读取本地环境文件：${error instanceof Error ? error.message : String(error)}`);
  }
}
loadLocalEnvFile();

// 允许同一局域网的浏览器访问；可通过 ZHANGCAI_HOST 收紧到指定网卡。
const HOST = process.env.ZHANGCAI_HOST || '0.0.0.0';
// Harness 桥接端口固定为 4318。网页、桌面启动器和恢复轮询都使用这一端口，
// 避免环境变量变化后出现任务已启动但状态查询落到另一服务的问题。
const PORT = Number(process.env.ZHANGCAI_BRIDGE_PORT || 4318);
const APP_ROOT = path.resolve(process.env.ZHANGCAI_APP_ROOT || process.cwd());
const DATA_ROOT = path.resolve(process.env.ZHANGCAI_DATA_DIR || path.join(APP_ROOT, 'data'));
const RUNTIME_ROOT = path.join(DATA_ROOT, 'runtime');
const HARNESS_ROOT = path.join(DATA_ROOT, 'harness');
const HARNESS_CONTEXT_ROOT = path.join(HARNESS_ROOT, 'context');
const HARNESS_JOBS_ROOT = path.join(HARNESS_ROOT, 'jobs');
const STRATEGY_JOBS_ROOT = path.join(HARNESS_ROOT, 'strategy-jobs');
const AFTER_CLOSE_SCHEDULE_FILE = path.join(HARNESS_ROOT, 'schedules', 'after-close-daily-refresh.json');
const SKILL_SOURCE = path.resolve(process.env.ZHANGCAI_SKILLS_DIR || path.join(APP_ROOT, 'harness-skills'));
const DAILY_STATE_FILE = path.join(RUNTIME_ROOT, 'daily-refresh-state.json');
const SUPPLEMENTAL_STATE_FILE = path.join(RUNTIME_ROOT, 'supplemental-refresh-state.json');
// 复盘任务会携带 TDX 行业/主题、涨停梯队和榜单上下文；完整 JSON
// 通常超过 128KB。保留本地服务的明确上限，但避免超限时直接 socket hang up。
const MAX_BODY = 4 * 1024 * 1024;
// 结构化 Harness 报告可能包含多张行情/指标表。32KB 会在 JSON 结束前
// 截断，前端随后只能提示“JSON 对象未闭合”。保留一个合理上限，避免
// 无限输出，同时覆盖完整策略报告。
const MAX_OUTPUT = 256 * 1024;
function localPythonExecutable() {
  const configured = process.env.ZHANGCAI_PYTHON || process.env.TDX_PYTHON;
  if (configured) return configured;
  const candidates = [
    path.join(APP_ROOT, '.runtime', 'python', 'python.exe'),
    path.join(APP_ROOT, 'runtime', 'python', 'python.exe'),
    process.env.USERPROFILE ? path.join(process.env.USERPROFILE, '.cache', 'codex-runtimes', 'codex-primary-runtime', 'dependencies', 'python', 'python.exe') : '',
  ];
  return candidates.find((candidate) => candidate && existsSync(candidate)) || 'python';
}
const HARNESS_JSON_SCHEMA = '最终只返回一个严格 JSON 对象，不要 Markdown、代码围栏或前后解释。字段必须为：status(string)、summary(string)、data_date(string)、data_scope(string)、cautions(string[])、findings({title:string,text:string}[])、tables({title:string,columns:string[],rows:string[][]}[])。所有结论只能引用传入数据，缺失项写入 cautions，不得虚构。报告按网页重点摘要标准输出：summary 不超过 120 字，findings 最多 5 条且每条不超过 100 字，tables 只保留最关键的 3 张表、每张最多 10 行；优先保留主线结论、核心指标、Top 候选和风险边界，省略重复解释。';
// DeepSeek Harness 启动和读取本地技能文件本身通常需要几十秒；复杂复盘
// 若仍固定 240 秒会在模型刚开始输出前被桥接层杀掉。默认给足 10 分钟，
// 仍可通过 DSH_TIMEOUT_MS 在独立运行时收紧。
const DEFAULT_TIMEOUT_MS = Number(process.env.DSH_TIMEOUT_MS || 600000);
const SKILL_TIMEOUT_MS = {
  'five-dimension-resonance': 600000,
  'a-share-leader-deep-research': 600000,
  'a-share-limit-up-mining': 600000,
  'limit-up-review': 600000,
  'stock-analysis': 600000,
  'stock-study': 600000,
  'stock-research-engine': 600000,
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
const PARAMETER_REQUIRED_STRATEGIES = new Set(['golden-ignition']);
const SPECIAL_DATA_STRATEGIES = new Set(['convertible-bond-screening-strategy']);
const harnessJobs = new Map();
const strategyJobs = new Map();
const dailyJobs = new Map();
const supplementalJobs = new Map();

function harnessJobFile(id) {
  return path.join(HARNESS_JOBS_ROOT, `${id}.json`);
}

function persistHarnessJob(job) {
  void writeRuntimeJson(harnessJobFile(job.id), job).catch((error) => {
    console.error(`[agent] 无法保存 Harness 任务 ${job.id.slice(0, 8)}：${error instanceof Error ? error.message : String(error)}`);
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
  return Number.isFinite(configured) && configured > 0 ? configured : 240000;
}

function readTdxPrivateFormulaNames(tdxRoot = 'C:\\new_tdx_mock') {
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
  const allowOrigin = typeof requestOrigin === 'string' && /^https?:\/\/[^/]+:\d+$/.test(requestOrigin)
    ? requestOrigin
    : 'http://localhost:3001';
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
  return [
    '你是掌财智能体的本地研究助手。',
    `当前技能：${skillId || '通用行情研究'}`,
    '网页已完成技能路由，当前技能由调用方提供；不要声称技能目录不可用，也不要要求重新安装技能。',
    task,
    '',
    isDataReplenishment
      ? '这是数据补全任务。先加载 market-data-replenishment 技能，严格按其公开数据源、交易日校验和保存规则执行。允许访问该技能列出的公开接口与本地项目文件；不得将模型推测写为数据。'
      : '只允许使用下面的本地通达信摘要。网页已经把可计算的榜单、TDX行业/主题成员聚合和涨停候选表传入，必须引用这些表；不要笼统声称缺少涨幅榜、成交额榜、跌幅榜、板块榜或涨停候选。跌停、前日涨停表现和盘中封板率是日线推导，必须标记为推导候选；TDX行业/主题映射可用于结构化候选，但不能当作交易所或申万官方行业事实。',
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
    `涨停/连板候选：${limitText}`,
    `主线名称聚类候选：${themeText}`,
    `TDX涨停文件：${Array.isArray(market.tdxLimitUpSource) ? market.tdxLimitUpSource.join('、') : '未提供'}`,
    dailyContext ? `本地每日更新上下文：${JSON.stringify(dailyContext)}` : '',
    context ? `补充上下文：${JSON.stringify(context)}` : '',
    `如果信息不足，请在 cautions 中明确写出。${HARNESS_JSON_SCHEMA}`,
  ].join(' ');
}

function findLocalDshEntry() {
  const roots = [
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

function ensureBundledSkills() {
  const source = SKILL_SOURCE;
  const destination = path.join(HARNESS_ROOT, 'skills');
  if (!existsSync(source)) return { status: 'missing', source, destination, count: 0 };
  try {
    mkdirSync(destination, { recursive: true });
    const names = readdirSync(source, { withFileTypes: true }).filter((entry) => entry.isDirectory()).map((entry) => entry.name);
    for (const name of names) {
      const target = path.join(destination, name);
      if (!existsSync(target)) cpSync(path.join(source, name), target, { recursive: true });
    }
    return { status: 'ready', source, destination, count: names.length };
  } catch (error) {
    console.error(`[agent] skill bundle unavailable: ${error instanceof Error ? error.message : String(error)}`);
    return { status: 'error', source, destination, count: 0 };
  }
}

function commandFor(prompt) {
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
    return { command: node, args: [pnpmEntry, 'dlx', '@deepseek-ai/dsh', '--profile', 'headless', ...patchArgs, prompt] };
  }
  return { command: process.platform === 'win32' ? 'npx.cmd' : 'npx', args: ['@deepseek-ai/dsh', '--profile', 'headless', ...patchArgs, prompt] };
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
  try {
    const value = JSON.parse(source);
    if (value && typeof value === 'object' && !Array.isArray(value)) return JSON.stringify(shape(value), null, 2);
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
          if (value && typeof value === 'object' && !Array.isArray(value)) return JSON.stringify(shape(value), null, 2);
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
function harnessEnvironment() {
  const env = {
    DEEPSEEK_API_KEY: process.env.DEEPSEEK_API_KEY,
    DSH_HOME: process.env.DSH_HOME || HARNESS_ROOT,
    DSH_TELEMETRY_DISABLED: '1',
  };
  const requiredSystemVariables = [
    'PATH', 'Path', 'PATHEXT', 'SystemRoot', 'SYSTEMROOT', 'WINDIR', 'ComSpec',
    'TEMP', 'TMP', 'APPDATA', 'LOCALAPPDATA', 'USERPROFILE', 'HOMEDRIVE',
    'HOMEPATH', 'PROGRAMDATA', 'ProgramFiles', 'ProgramFiles(x86)',
  ];
  for (const name of requiredSystemVariables) {
    if (process.env[name]) env[name] = process.env[name];
  }
  return env;
}

function runHarness(prompt, skillId = '', options = {}) {
  return new Promise(async (resolve, reject) => {
    const timeoutMs = timeoutForSkill(skillId);
    const startedAt = Date.now();
    const taskDir = path.join(HARNESS_ROOT, 'tasks');
    const taskFile = path.join(taskDir, `task-${randomUUID()}.txt`);
    try {
      await mkdir(taskDir, { recursive: true });
      await writeFile(taskFile, prompt, 'utf8');
    } catch (error) {
      reject(new Error(`无法写入 Harness 任务文件：${error instanceof Error ? error.message : String(error)}`));
      return;
    }
    // Windows command lines are limited to roughly 8K. Deep research keeps the
    // full context in a local task file; daily validation receives an intentionally
    // compact metadata snapshot inline so it never needs to scan large raw data.
    const inline = options.inline === true && Buffer.byteLength(prompt, 'utf8') < 7000;
    const launchTask = inline ? prompt : `请读取并执行任务文件 ${taskFile}，最终只输出文件要求的结果。`;
    const spec = commandFor(launchTask);
    const cleanup = () => { unlink(taskFile).catch(() => {}); };
    let child;
    try {
      child = spawn(spec.command, spec.args, {
        env: harnessEnvironment(),
        windowsHide: true,
      });
    } catch (error) {
      cleanup();
      reject(error);
      return;
    }
    let stdout = '';
    let stderr = '';
    const timer = setTimeout(() => {
      if (process.platform === 'win32' && child.pid) {
        spawn('taskkill', ['/pid', String(child.pid), '/t', '/f'], { windowsHide: true });
      } else {
        child.kill('SIGKILL');
      }
      cleanup();
      reject(new Error(`DeepSeek Harness 超时（${Math.round(timeoutMs / 1000)} 秒，技能 ${skillId || '通用研究'}）`));
    }, timeoutMs);
    child.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
    child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
    child.on('error', (error) => { clearTimeout(timer); cleanup(); reject(error); });
    child.on('close', (code) => {
      clearTimeout(timer);
      cleanup();
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
        output: output.slice(0, MAX_OUTPUT),
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
  let lastError;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      return await runHarness(prompt, skillId, options);
    } catch (error) {
      lastError = error;
      const message = error instanceof Error ? error.message : String(error);
      const retryable = /TRANSPORT|fetch failed|ECONNRESET|ECONNREFUSED|ETIMEDOUT|ENETUNREACH|EAI_AGAIN/i.test(message);
      if (!retryable || attempt >= 2) throw error;
      const waitMs = 1500 * (attempt + 1);
      console.warn(`[agent] Harness 网络错误，${waitMs}ms 后重试 ${attempt + 1}/2：${message}`);
      await new Promise((resolve) => setTimeout(resolve, waitMs));
    }
  }
  throw lastError instanceof Error ? lastError : new Error(String(lastError || 'Harness 执行失败'));
}

function startHarnessJob(prompt, skillId = '') {
  const id = randomUUID();
  const job = { id, status: 'running', skill_id: skillId || null, started_at: Date.now() };
  harnessJobs.set(id, job);
  persistHarnessJob(job);
  void runHarnessWithRetry(prompt, skillId).then((result) => {
    const current = harnessJobs.get(id);
    if (!current) return;
    Object.assign(current, {
      status: 'completed',
      output: result.output,
      diagnostics: result.diagnostics,
      elapsed_ms: result.elapsedMs,
      timeout_seconds: Math.round(result.timeoutMs / 1000),
      completed_at: Date.now(),
    });
    persistHarnessJob(current);
  }).catch((error) => {
    const current = harnessJobs.get(id);
    if (!current) return;
    Object.assign(current, {
      status: 'failed',
      error: error instanceof Error ? error.message : String(error),
      elapsed_ms: Date.now() - current.started_at,
      completed_at: Date.now(),
    });
    persistHarnessJob(current);
  });
  return job;
}

async function runPublicMarketRefresh() {
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

async function runMarketRefresh(scope = 'indices', codes = '') {
  if (scope === 'market') {
    try {
      // 市场全量快照包含数千只股票，不能使用普通脚本的 12KB 尾部截断，
      // 否则 JSON 会被截断后触发降级到旧的公开快照。
      const value = await runLocalScript('market_overview_refresh.py', ['--scope', 'market'], 180000, 0);
      return JSON.parse(value.output);
    } catch (error) {
      // 本地完整日线不可用时保留公开涨停池作为降级数据，但把来源和日期
      // 明确交给页面，不能静默继续使用旧 market.json。
      const fallback = await runPublicMarketRefresh();
      return { ...fallback, scope: `${fallback.scope}；本地日线刷新失败：${error instanceof Error ? error.message : String(error)}` };
    }
  }
  return new Promise((resolve, reject) => {
    const python = localPythonExecutable();
    const script = path.join(APP_ROOT, 'scripts', 'market_overview_refresh.py');
    const args = [script, '--scope', scope];
    if (scope === 'watchlist' && codes) args.push('--codes', codes);
    const child = spawn(python, args, { windowsHide: true });
    let stdout = '';
    let stderr = '';
    const timer = setTimeout(() => {
      if (child.pid) spawn('taskkill', ['/pid', String(child.pid), '/t', '/f'], { windowsHide: true });
      reject(new Error('通达信实时行情刷新超时（120 秒）'));
    }, 120000);
    child.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
    child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
    child.on('error', (error) => { clearTimeout(timer); reject(error); });
    child.on('close', (code) => {
      clearTimeout(timer);
      if (code !== 0) { reject(new Error(readableScriptError('market_overview_refresh.py', stderr || stdout, code))); return; }
      try { resolve(JSON.parse(stdout.trim())); } catch { reject(new Error('实时行情返回格式无效')); }
    });
  });
}

function runCanonicalStrategy(skillId) {
  return new Promise((resolve, reject) => {
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
    try {
      const snapshot = JSON.parse(readFileSync(path.join(APP_ROOT, 'lib', 'market.json'), 'utf8'));
      const tdxRoot = process.env.ZHANGCAI_TDX_ROOT || 'C:\\new_tdx_mock';
      const tdxDirs = ['sh', 'sz', 'bj'].map((market) => path.join(tdxRoot, 'vipdoc', market, 'lday'));
      const dateCounts = new Map();
      for (const directory of tdxDirs) {
        if (!existsSync(directory)) continue;
        for (const name of readdirSync(directory)) {
          if (!name.toLowerCase().endsWith('.day')) continue;
          try {
            const filePath = path.join(directory, name);
            const bytes = readFileSync(filePath);
            if (bytes.length >= 32) {
              const date = String(bytes.readUInt32LE(bytes.length - 32));
              dateCounts.set(date, (dateCounts.get(date) || 0) + 1);
            }
          } catch { /* 单个文件读取失败由原始技能继续审计 */ }
        }
      }
      const tdxDateEntry = [...dateCounts.entries()].sort((a, b) => b[1] - a[1])[0];
      const currentCount = tdxDateEntry ? Number(tdxDateEntry[1]) : Number(snapshot.currentCount || 0);
      const dataDate = tdxDateEntry ? tdxDateEntry[0] : snapshot.date || null;
      if (currentCount < 3000) {
        resolve({
          status: 'BLOCKED',
          skill_id: skillId,
          output: JSON.stringify({
            status: 'BLOCKED',
            message: '通达信当日全市场日线覆盖不足，原始策略已按完整样本契约阻断。',
            required_current_count: 3000,
            actual_current_count: currentCount,
            data_date: dataDate,
            action: '刷新并补齐沪深北日线后重新运行；不会使用部分样本替代全市场扫描。',
          }, null, 2),
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
            }, null, 2),
            data_date: dataDate,
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
      env: {
        ...process.env,
        ONESTOCK_STOCK_DATA_ROOT: outputRoot,
        STOCK_SKILLS_ROOT: SKILL_SOURCE,
        PYTHONPATH: [path.join(APP_ROOT, 'scripts'), path.join(SKILL_SOURCE, 'stock-unified', 'scripts'), process.env.PYTHONPATH || ''].filter(Boolean).join(path.delimiter),
      },
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
      resolve({
        status: receipt?.status || (code === 0 ? 'CLEAN_PASS' : 'BLOCKED'),
        output: combined.slice(-MAX_OUTPUT),
        elapsed_ms: Date.now() - startedAt,
        receipt,
        structured,
        skill_id: skillId,
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

function localTradeDate() {
  // 通达信日线可能在收盘后仍以“最近完整交易日”落盘；优先使用补齐回执，
  // 避免自然日已跨到下一天却把无行情的日期传给龙虎榜/涨停接口。
  try {
    const runtimeDir = path.join(DATA_ROOT, 'runtime');
    const candidates = readdirSync(runtimeDir)
      .filter((name) => /^(?:tdx-daily-replenish|tdx-daily-integrity)-\d{8}-\d{6}\.json$/.test(name))
      .sort()
      .reverse();
    for (const name of candidates) {
      const value = readJson(path.join(runtimeDir, name));
      const raw = String(value?.targetDateAfter || value?.targetDate || value?.before?.targetDate || value?.after?.targetDate || '').replace(/\D/g, '');
      if (/^\d{8}$/.test(raw)) return `${raw.slice(0, 4)}-${raw.slice(4, 6)}-${raw.slice(6)}`;
    }
  } catch { /* 首次运行尚无补齐回执，回退到本地自然日。 */ }
  const values = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(new Date()).reduce((result, item) => ({ ...result, [item.type]: item.value }), {});
  return `${values.year}-${values.month}-${values.day}`;
}

function readJson(file) {
  try { return JSON.parse(readFileSync(file, 'utf8')); } catch { return null; }
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
  // The five-dimension runner writes its canonical JSON report directly to
  // the skill reports directory and only prints a compact summary to stdout;
  // there is no REPORT= marker to discover. Expose that report as the same
  // structured payload used by the other strategy runners so the page can
  // render the Top10 table instead of only the receipt status.
  if (!reportMarkdown && !analysis && !derived && skillId === 'five-dimension-resonance') {
    const fallbackPath = path.join(APP_ROOT, 'reports', '2026-06-03_five_dimension_feilong_block_hardening', 'feilong_block_resonance_scan.json');
    const fallback = readJson(fallbackPath);
    if (fallback && typeof fallback === 'object') {
      return { reportPath: fallbackPath, analysisPath: fallbackPath, derivedPath: '', reportMarkdown: '', analysis: fallback, derived: null };
    }
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

function dailySnapshotSummary() {
  const publicSnapshot = readJson(path.join(DATA_ROOT, 'public', 'latest.json'));
  const newsSnapshot = readJson(path.join(DATA_ROOT, 'news', 'latest.json'));
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
  const dailyIntegrity = inspectTdxDailyIntegrity();
  return {
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
      unresolved: dailyIntegrity.integrity.unresolved,
      repairs: dailyIntegrity.integrity.repairs.filter((item) => item && item.status === 'written'),
      repairAttempts: dailyIntegrity.integrity.repairs,
      nonTrading: dailyIntegrity.integrity.nonTrading,
    } : {
      reportPath: dailyIntegrity.integrityReportPath,
      targetDate: dailyIntegrity.latestDate,
      stockListCount: dailyIntegrity.stockListCount,
      stockCompleteCount: dailyIntegrity.stockCompleteCount,
      stockMissingCount: dailyIntegrity.stockMissingCount,
      complete: dailyIntegrity.complete,
      unresolved: [], repairs: [],
    },
    news: {
      schema: newsSnapshot?.schema || '', date: newsSnapshot?.date || '', status: newsSnapshot?.status || 'missing', fetchedAt: newsSnapshot?.fetchedAt || '',
      sameDayRecordCount: newsSnapshot?.sameDayRecordCount || 0, source: {
        url: newsSource.url || '', httpStatus: newsSource.httpStatus || null, sha256: newsSource.sha256 || '', bytes: newsSource.bytes || 0,
        providerCode: newsSource.providerCode ?? null, recordCount: Array.isArray(newsSource.records) ? newsSource.records.length : 0,
      },
    },
  };
}

async function writeRuntimeJson(file, value) {
  await mkdir(path.dirname(file), { recursive: true });
  await writeFile(file, JSON.stringify(value, null, 2), 'utf8');
}

function readableScriptError(scriptName, raw, code = 1) {
  const text = String(raw || '').trim();
  // tqcenter 在部分 Windows 环境会把 GBK 异常按 UTF-8 解码，原始
  // Traceback 既不可读也会把内部路径暴露到页面。行情刷新只返回用户
  // 能采取行动的提示，详细诊断仍保留在桥接服务日志中。
  if (scriptName === 'market_overview_refresh.py' && (/Traceback|tqcenter|TQ|RuntimeError|�/.test(text))) {
    return '通达信实时行情刷新失败：请确认通达信已打开并登录；若已打开，请稍后重试以释放 TQ 数据连接。';
  }
  return (text || `${scriptName} 退出码 ${code}`).slice(-2000);
}

function runLocalScript(scriptName, args = [], timeoutMs = 120000, outputLimit = 12000, acceptedExitCodes = []) {
  return new Promise((resolve, reject) => {
    const python = localPythonExecutable();
    const script = path.join(APP_ROOT, 'scripts', scriptName);
    const child = spawn(python, [script, ...args], {
      cwd: APP_ROOT,
      windowsHide: true,
      env: { ...process.env, ZHANGCAI_APP_ROOT: APP_ROOT, ZHANGCAI_DATA_DIR: DATA_ROOT },
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

function inspectTdxDailyIntegrity(tdxRoot = process.env.ZHANGCAI_TDX_ROOT || 'C:\\new_tdx_mock') {
  const markets = ['sh', 'sz', 'bj'];
  const byMarket = {};
  const dateCounts = new Map();
  let fileCount = 0;
  for (const market of markets) {
    const directory = path.join(tdxRoot, 'vipdoc', market, 'lday');
    let names = [];
    try { names = readdirSync(directory); } catch { names = []; }
    let marketCount = 0;
    const marketDates = new Map();
    for (const name of names) {
      if (!name.toLowerCase().endsWith('.day')) continue;
      try {
        const bytes = readFileSync(path.join(directory, name));
        if (bytes.length < 32) continue;
        const date = String(bytes.readUInt32LE(bytes.length - 32));
        if (!/^\d{8}$/.test(date)) continue;
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
  const stockTargetDate = String(integrityReport?.targetDate || stockAfter?.targetDate || latestDate);
  const stockFileLatestCount = Number(stockAfter?.completeCount || 0);
  const stockNonTradingCount = Number(stockAfter?.nonTradingCount || 0);
  const stockLatestCount = Number(stockAfter?.effectiveCompleteCount ?? (stockFileLatestCount + stockNonTradingCount));
  const stockExpectedCount = Number(stockAfter?.stockCount || 0);
  const integritySummary = integrityReport ? {
    schema: integrityReport.schema,
    targetDate: integrityReport.targetDate || stockTargetDate,
    before: integrityReport.before,
    after: integrityReport.after,
    repairs: Array.isArray(integrityReport.repairs) ? integrityReport.repairs : [],
    nonTrading: Array.isArray(integrityReport.nonTrading) ? integrityReport.nonTrading : [],
    unresolved: Array.isArray(integrityReport.unresolved) ? integrityReport.unresolved : [],
    complete: integrityReport.complete === true,
  } : null;
  return {
    root: tdxRoot,
    directories: byMarket,
    fileCount,
    latestDate: stockTargetDate,
    latestCount: stockLatestCount || fileLatestCount,
    fileLatestCount,
    stockListCount: stockExpectedCount || null,
    stockCompleteCount: stockLatestCount || null,
    stockFileCompleteCount: stockFileLatestCount || null,
    stockNonTradingCount,
    stockMissingCount: stockExpectedCount ? Math.max(0, stockExpectedCount - stockLatestCount) : null,
    integrityReportPath: integrityReportPath || null,
    integrity: integritySummary,
    requiredMinimum: 3000,
    complete: stockAfter ? stockExpectedCount > 0 && stockLatestCount === stockExpectedCount : fileLatestCount >= 3000 && ['SH', 'SZ', 'BJ'].every((market) => byMarket[market].latestDate === latestDate),
  };
}

// 个股详情页的“五公式”走同一个本地桥接端口，避免前端再依赖一个
// 未启动的 4320 服务。tdx_hub.py 的 five 命令即使某一公式失败也会
// 返回完整 JSON（退出码 2），因此这里按 JSON 响应解析并把单项失败
// 交给页面展示，而不是把它误报成网络错误。
function runFiveFormulas(symbol, timeoutMs = 120000) {
  return new Promise((resolve, reject) => {
    const python = localPythonExecutable();
    const script = path.join(SKILL_SOURCE, 'tdx-local-hub', 'scripts', 'tdx_hub.py');
    if (!existsSync(script)) {
      reject(new Error(`未找到通达信公式桥接脚本：${script}`));
      return;
    }
    const child = spawn(python, [script, 'five', symbol], {
      cwd: APP_ROOT,
      windowsHide: true,
      env: {
        ...process.env,
        TDX_ROOT: process.env.ZHANGCAI_TDX_ROOT || 'C:\\new_tdx_mock',
        ONESTOCK_STOCK_DATA_ROOT: DATA_ROOT,
      },
    });
    let stdout = '';
    let stderr = '';
    const startedAt = Date.now();
    const timer = setTimeout(() => {
      if (child.pid) spawn('taskkill', ['/pid', String(child.pid), '/t', '/f'], { windowsHide: true });
      reject(new Error(`五公式计算超时（${Math.round(timeoutMs / 1000)} 秒）`));
    }, timeoutMs);
    child.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
    child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
    child.on('error', (error) => { clearTimeout(timer); reject(error); });
    child.on('close', (code) => {
      clearTimeout(timer);
      const text = stdout.trim();
      let payload;
      try {
        payload = JSON.parse(text);
      } catch {
        reject(new Error((stderr || text || `公式桥接退出码 ${code}`).trim().slice(-2000)));
        return;
      }
      resolve({
        status: 'ok',
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
        })) : [],
        failed_formulas: Array.isArray(payload.failed_formulas) ? payload.failed_formulas : [],
        bridge_exit_code: code,
      });
    });
  });
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
    let result = null;
    try {
      result = await runLocalScript(script, args, timeout, 12000, acceptedExitCodes);
      state.steps.push({ name, status: result.partial ? 'partial' : 'completed', finishedAt: new Date().toISOString(), ...result });
    } catch (error) {
      state.steps.push({ name, status: 'failed', finishedAt: new Date().toISOString(), error: error instanceof Error ? error.message : String(error) });
    }
    await writeRuntimeJson(DAILY_STATE_FILE, state);
    return result;
  };
  await execute('通达信运行状态', 'tdx_runtime_bridge.py', ['status'], 60000);
  // 收盘后以通达信补齐后的最近完整交易日为准，再拉取同日公开源，
  // 这样龙虎榜、涨停池和 Harness 上下文不会出现日期错位。
  // 完整性脚本用退出码 2 表示“报告已生成但仍有缺口”。这不是进程故障，
  // 必须保留其完整 stdout 交给 Harness，而不是只留下截断的错误尾部。
  const tdxRefresh = await execute('通达信日线完整性检查与补齐', 'tdx_daily_integrity.py', ['--refresh'], Number(process.env.ZHANGCAI_TDX_REFRESH_TIMEOUT_MS || 180000), [2]);
  let refreshedDate = '';
  try {
    const integrity = JSON.parse(String(tdxRefresh?.output || '{}'));
    refreshedDate = String(integrity?.after?.targetDate || integrity?.targetDateAfter || integrity?.targetDate || '').replace(/\D/g, '');
  } catch {
    refreshedDate = String(tdxRefresh?.output || '').match(/"targetDateAfter"\s*:\s*"(\d{8})"/)?.[1] || '';
  }
  const effectiveDate = /^\d{8}$/.test(refreshedDate)
    ? `${refreshedDate.slice(0, 4)}-${refreshedDate.slice(4, 6)}-${refreshedDate.slice(6)}`
    : date;
  state.date = effectiveDate;
  await writeRuntimeJson(DAILY_STATE_FILE, state);
  await Promise.all([
    execute('公开行情补齐', 'public_market_sync.py', ['--date', effectiveDate], 90000),
    execute('新闻快讯补齐', 'news_sync.py', ['--date', effectiveDate], 90000),
  ]);

  const contextFile = path.join(HARNESS_CONTEXT_ROOT, `daily-data-${effectiveDate.replace(/-/g, '')}.json`);
  const snapshots = dailySnapshotSummary();
  const context = {
    schema: 'ZHANGCAI_HARNESS_DAILY_CONTEXT_V1',
    date: effectiveDate,
    generatedAt: new Date().toISOString(),
    runtimeRoot: RUNTIME_ROOT,
    publicSnapshot: path.join(DATA_ROOT, 'public', 'latest.json'),
    newsSnapshot: path.join(DATA_ROOT, 'news', 'latest.json'),
    dailyState: DAILY_STATE_FILE,
    steps: state.steps.map(({ name, status, script, code, finishedAt, error }) => ({ name, status, script, code, finishedAt, error })),
    snapshots,
  };
  await writeRuntimeJson(contextFile, context);
  await writeRuntimeJson(path.join(HARNESS_CONTEXT_ROOT, 'latest-data.json'), context);
  try {
    if (!process.env.DEEPSEEK_API_KEY) throw new Error('未设置 DEEPSEEK_API_KEY，已完成本地快照但无法进行 Harness 校验');
    const output = await runHarnessWithRetry(buildPrompt(
      `这是每日首次打开后的数据更新校验。以下是本机脚本已提取的紧凑元数据：${JSON.stringify(context)}。仅依据这些字段核验来源、日期、哈希、条数与缺失项。日线有效完整率以 snapshots.tdxDailyIntegrity.effectiveCompleteCount 和 complete 为准；其中 nonTrading 列出的未上市/停牌/目标日无交易证券按用户规则计入完整，repairAttempts 只是补齐尝试记录，不得把其中的 nonTrading 项重新计入缺失。禁止读取文件、执行命令、访问网络、重新抓取或猜测数据。${HARNESS_JSON_SCHEMA}`,
      { date: effectiveDate.replace(/-/g, ''), currentCount: snapshots.publicMarket.marketBreadth.currentCount, up: snapshots.publicMarket.marketBreadth.up, down: snapshots.publicMarket.marketBreadth.down, flat: snapshots.publicMarket.marketBreadth.flat, amount: 0, dataSources: { dailyContext: contextFile, publicSources: snapshots.publicMarket.sources }, limitCandidates: [{ count: snapshots.publicMarket.marketBreadth.limitUp, lianban: snapshots.publicMarket.marketBreadth.lianban }] },
      'market-data-replenishment',
      { contextFile },
    ), 'market-data-replenishment', { inline: true });
    state.harness = { status: 'completed', finishedAt: new Date().toISOString(), output: output.output, elapsedMs: output.elapsedMs };
    await writeRuntimeJson(path.join(HARNESS_CONTEXT_ROOT, `daily-validation-${effectiveDate.replace(/-/g, '')}.json`), {
      ...context,
      harness: state.harness,
    });
    await writeRuntimeJson(path.join(HARNESS_CONTEXT_ROOT, 'latest-data.json'), {
      ...context,
      harness: state.harness,
    });
  } catch (error) {
    state.harness = { status: 'failed', finishedAt: new Date().toISOString(), error: error instanceof Error ? error.message : String(error) };
  }
  state.finishedAt = new Date().toISOString();
  state.status = state.steps.some((step) => ['failed', 'partial'].includes(step.status)) || state.harness.status === 'failed' ? 'partial' : 'completed';
  await writeRuntimeJson(DAILY_STATE_FILE, state);
  return state;
}

// 只补齐公开行情、龙虎榜、涨停池与新闻，不重复触发通达信日线扫描。
// 该入口供设置页手动使用；完成后同样交给 DeepSeek Harness 做来源、日期和条数校验。
async function runSupplementalRefresh(date) {
  const state = {
    schema: 'ZHANGCAI_SUPPLEMENTAL_REFRESH_V1', date,
    startedAt: new Date().toISOString(), status: 'running', steps: [], harness: { status: 'pending' },
  };
  await writeRuntimeJson(SUPPLEMENTAL_STATE_FILE, state);
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
  const contextFile = path.join(HARNESS_CONTEXT_ROOT, `supplemental-data-${date.replace(/-/g, '')}.json`);
  const snapshots = dailySnapshotSummary();
  const context = { schema: 'ZHANGCAI_HARNESS_SUPPLEMENTAL_CONTEXT_V1', date, generatedAt: new Date().toISOString(), dailyState: SUPPLEMENTAL_STATE_FILE, snapshots };
  await writeRuntimeJson(contextFile, context);
  try {
    if (!process.env.DEEPSEEK_API_KEY) throw new Error('未设置 DEEPSEEK_API_KEY，已完成公开数据快照但无法进行 Harness 校验');
    const output = await runHarnessWithRetry(buildPrompt(
      `这是公开行情与新闻数据补齐校验。以下是本机脚本提取的元数据：${JSON.stringify(context)}。仅核验来源、日期、哈希、条数和缺失项，不得读取文件、执行命令、访问网络或猜测数据。${HARNESS_JSON_SCHEMA}`,
      { date: date.replace(/-/g, ''), currentCount: snapshots.publicMarket.marketBreadth.currentCount, up: snapshots.publicMarket.marketBreadth.up, down: snapshots.publicMarket.marketBreadth.down, flat: snapshots.publicMarket.marketBreadth.flat, amount: 0, dataSources: { dailyContext: contextFile, publicSources: snapshots.publicMarket.sources, news: snapshots.news }, limitCandidates: [{ count: snapshots.publicMarket.marketBreadth.limitUp, lianban: snapshots.publicMarket.marketBreadth.lianban }] },
      'market-data-replenishment', { contextFile },
    ), 'market-data-replenishment', { inline: true });
    state.harness = { status: 'completed', finishedAt: new Date().toISOString(), output: output.output, elapsedMs: output.elapsedMs };
  } catch (error) {
    state.harness = { status: 'failed', finishedAt: new Date().toISOString(), error: error instanceof Error ? error.message : String(error) };
  }
  state.finishedAt = new Date().toISOString();
  state.status = state.steps.some((step) => step.status === 'failed') || state.harness.status === 'failed' ? 'partial' : 'completed';
  await writeRuntimeJson(SUPPLEMENTAL_STATE_FILE, state);
  return state;
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

function shanghaiDateParts(now = new Date()) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(now).reduce((result, item) => ({ ...result, [item.type]: item.value }), {});
  return { year: Number(parts.year), month: Number(parts.month), day: Number(parts.day) };
}

function nextAfterCloseTime(now = new Date()) {
  const { year, month, day } = shanghaiDateParts(now);
  // Asia/Shanghai 固定 UTC+8；用 UTC 构造避免宿主机时区影响计划时间。
  let target = new Date(Date.UTC(year, month - 1, day, 8, 50, 0, 0));
  if (target.getTime() <= now.getTime()) target = new Date(target.getTime() + 24 * 60 * 60 * 1000);
  while (target.getUTCDay() === 0 || target.getUTCDay() === 6) target = new Date(target.getTime() + 24 * 60 * 60 * 1000);
  return target;
}

function shanghaiDateText(now = new Date()) {
  const { year, month, day } = shanghaiDateParts(now);
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

function scheduleAfterCloseDailyRefresh() {
  const arm = () => {
    const next = nextAfterCloseTime();
    void writeRuntimeJson(AFTER_CLOSE_SCHEDULE_FILE, {
      schema: 'ZHANGCAI_HARNESS_AFTER_CLOSE_SCHEDULE_V1',
      enabled: true,
      timezone: 'Asia/Shanghai',
      schedule: '每个工作日 16:50',
      nextRunAt: next.toISOString(),
      pipeline: ['通达信日线补齐', '公开行情与新闻同步', 'DeepSeek Harness 数据校验'],
    });
    const delay = Math.max(1000, next.getTime() - Date.now());
    setTimeout(() => {
      const date = shanghaiDateText();
      const started = startDailyRefresh(date);
      void writeRuntimeJson(AFTER_CLOSE_SCHEDULE_FILE, {
        schema: 'ZHANGCAI_HARNESS_AFTER_CLOSE_SCHEDULE_V1', enabled: true,
        timezone: 'Asia/Shanghai', schedule: '每个工作日 16:50',
        lastTriggeredAt: new Date().toISOString(), lastTradeDate: date, result: started,
        pipeline: ['通达信日线补齐', '公开行情与新闻同步', 'DeepSeek Harness 数据校验'],
      });
      console.log(`[agent] 收盘后静默刷新触发：${date} · ${started.status}`);
      arm();
    }, delay);
  };
  arm();
}

const server = http.createServer(async (req, res) => {
  if (req.method === 'OPTIONS') { res.writeHead(204, corsHeaders(req)); res.end(); return; }
  if (req.method === 'GET' && req.url === '/health') {
    json(res, 200, { status: 'ok', service: 'zhangcai-local-bridge', port: PORT, appRoot: APP_ROOT, dataRoot: DATA_ROOT, skills: SKILL_SOURCE });
    return;
  }
  if (req.method === 'GET' && req.url === '/runtime/environment') {
    try {
      const tdxRoot = process.env.ZHANGCAI_TDX_ROOT || 'C:\\new_tdx_mock';
      const tdxStatusResult = await runLocalScript('tdx_runtime_bridge.py', ['status'], 60000, 0);
      const tdxStatus = JSON.parse(tdxStatusResult.output || '{}');
      const daily = inspectTdxDailyIntegrity(tdxRoot);
      const snapshots = dailySnapshotSummary();
      const dailyState = readJson(DAILY_STATE_FILE) || {};
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
      const harnessReady = Boolean(process.env.DEEPSEEK_API_KEY);
      json(res, 200, {
        status: 'ok',
        checkedAt: new Date().toISOString(),
        bridge: { status: 'ok', host: HOST, port: PORT },
        harness: { status: harnessReady ? 'ready' : 'missing_credentials', launcher, credentialsConfigured: harnessReady, base: 'DeepSeek Harness' },
        tdx: { status: Array.isArray(tdxStatus.processes) && tdxStatus.processes.length > 0 ? 'open' : 'closed', processes: tdxStatus.processes || [], root: tdxRoot, formulas: tdxStatus.formulaRegistry || {}, freshness: tdxStatus.freshness || {} },
        daily,
        sources: publicSources,
        harnessValidation,
        dailyRefresh: dailyState,
        supplementalRefresh: readJson(SUPPLEMENTAL_STATE_FILE),
      });
    } catch (error) {
      json(res, 502, { status: 'error', error: error instanceof Error ? error.message : '运行环境检测失败' });
    }
    return;
  }
  if (req.method === 'GET' && req.url === '/data/daily/status') {
    json(res, 200, { status: 'ok', state: readJson(DAILY_STATE_FILE), jobs: [...dailyJobs.values()].slice(-3) });
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
  if (req.method === 'GET' && req.url === '/data/public/status') {
    json(res, 200, { status: 'ok', state: readJson(SUPPLEMENTAL_STATE_FILE), jobs: [...supplementalJobs.values()].slice(-3) });
    return;
  }
  if (req.method === 'GET' && req.url === '/data/public') {
    const snapshot = readJson(path.join(DATA_ROOT, 'public', 'latest.json'));
    json(res, snapshot ? 200 : 404, snapshot || { status: 'missing', error: '公开行情快照不存在' });
    return;
  }
  if (req.method === 'GET' && req.url === '/data/harness/daily') {
    const context = readJson(path.join(HARNESS_CONTEXT_ROOT, 'latest-data.json'));
    json(res, context ? 200 : 404, context || { status: 'missing', error: 'Harness 每日校验结果不存在' });
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
  if (req.method === 'GET' && (req.url === '/market' || req.url.startsWith('/market?scope='))) {
    try {
      const url = new URL(req.url, `http://${HOST}:${PORT}`);
      const scope = url.searchParams.get('scope') === 'market' ? 'market' : url.searchParams.get('scope') === 'watchlist' ? 'watchlist' : 'indices';
      const codes = url.searchParams.get('codes') || '';
      const result = await runMarketRefresh(scope, codes);
      json(res, 200, result);
    } catch (error) {
      json(res, 502, { status: 'error', error: error instanceof Error ? error.message : '实时行情刷新失败' });
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
  if (req.method === 'POST' && req.url === '/strategy/start') {
    try {
      const payload = JSON.parse(await readBody(req) || '{}');
      const skillId = typeof payload?.skillId === 'string' ? payload.skillId.slice(0, 160) : '';
      if (!CANONICAL_STRATEGY_IDS.has(skillId)) {
        json(res, 422, { status: 'error', error: '该策略未配置原始技能入口', skill_id: skillId });
        return;
      }
      const job = startStrategyJob(skillId);
      console.log(`[agent] strategy start ${job.id.slice(0, 8)} skill=${skillId}`);
      json(res, 202, { status: 'accepted', job_id: job.id, skill_id: skillId, started_at: job.started_at, timeout_seconds: 22 * 60 });
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
      const skillId = typeof payload?.skillId === 'string' ? payload.skillId.slice(0, 160) : '';
      const result = await runCanonicalStrategy(skillId);
      json(res, 200, result);
    } catch (error) {
      json(res, 500, { status: 'error', error: error instanceof Error ? error.message : '原始策略执行失败' });
    }
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
      const job = startHarnessJob(buildPrompt(payload.task.trim(), payload.market, skillId, payload.context), skillId);
      console.log(`[agent] start ${job.id.slice(0, 8)} skill=${skillId || 'generic'}`);
      json(res, 202, { status: 'accepted', job_id: job.id, skill_id: skillId || null, started_at: job.started_at, timeout_seconds: Math.round(timeoutForSkill(skillId) / 1000) });
    } catch (error) {
      json(res, 500, { status: 'error', error: error instanceof Error ? error.message : 'Harness 后台任务启动失败' });
    }
    return;
  }
  if (req.method !== 'POST' || req.url !== '/agent') {
    json(res, 404, { status: 'error', error: '路径不存在' });
    return;
  }
  try {
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
    const result = await runHarnessWithRetry(buildPrompt(payload.task.trim(), payload.market, skillId, payload.context), skillId);
    json(res, 200, { status: 'ok', output: result.output, diagnostics: result.diagnostics, elapsed_ms: result.elapsedMs, timeout_seconds: Math.round(result.timeoutMs / 1000), model: 'DeepSeek Harness headless', skill_id: skillId || null, data_date: payload.market.date || null });
  } catch (error) {
    json(res, 500, { status: 'error', error: error instanceof Error ? error.message : '桥接服务失败' });
  }
});

const skillBundle = ensureBundledSkills();
server.listen(PORT, HOST, () => {
  console.log(`掌财智能体 DeepSeek Harness bridge listening at http://${HOST}:${PORT} · skills ${skillBundle.status} (${skillBundle.count})`);
  scheduleAfterCloseDailyRefresh();
});
