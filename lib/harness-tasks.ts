'use client';

import { bridgeUrl } from '@/lib/bridge-url';

export type HarnessTaskStatus = 'starting' | 'running' | 'completed' | 'failed';
export type HarnessTask = {
  id: string;
  backendJobId?: string;
  backendKind?: 'harness' | 'strategy';
  skillId: string;
  label: string;
  originPage: string;
  originStockCode?: string;
  expectedSeconds: number;
  startedAt: number;
  completedAt?: number;
  status: HarnessTaskStatus;
  output?: string;
  error?: string;
  strategyStatus?: string;
  receipt?: unknown;
  structured?: unknown;
};

const STORAGE_KEY = 'zhangcai.harness.tasks.v1';
const EVENT_NAME = 'zhangcai:harness-tasks';
// 3003 的生产网页没有 /bridge 代理路由；桥接服务本身已配置 CORS，
// 因此后台任务必须直接访问同一工作区的 4319，避免网页层返回 404。
const BRIDGE_ENDPOINTS: string[] = [];

function readTasks(): HarnessTask[] {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    return Array.isArray(value) ? value.filter((item) => item && typeof item.id === 'string') : [];
  } catch { return []; }
}
function writeTasks(tasks: HarnessTask[]) {
  const next = tasks.slice(0, 12);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  window.dispatchEvent(new CustomEvent(EVENT_NAME, { detail: next }));
  // 任务状态只属于后台任务栏和本地任务缓存，不再伪装成第二份报告。
  // 真正的 Harness/策略报告由各自的完成回调单独归档一次。
}
export function getHarnessTasks() { return readTasks(); }
export function subscribeHarnessTasks(listener: (tasks: HarnessTask[]) => void) {
  const handler = (event: Event) => listener((event as CustomEvent<HarnessTask[]>).detail || readTasks());
  const storage = (event: StorageEvent) => { if (event.key === STORAGE_KEY) listener(readTasks()); };
  window.addEventListener(EVENT_NAME, handler);
  window.addEventListener('storage', storage);
  listener(readTasks());
  return () => { window.removeEventListener(EVENT_NAME, handler); window.removeEventListener('storage', storage); };
}
export function createHarnessTask(input: Omit<HarnessTask, 'id' | 'status' | 'startedAt'>) {
  const task: HarnessTask = { ...input, id: `harness-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, status: 'starting', startedAt: Date.now() };
  writeTasks([task, ...readTasks().filter((item) => item.status === 'running' || item.status === 'starting')]);
  return task;
}
export function updateHarnessTask(id: string, patch: Partial<HarnessTask>) {
  writeTasks(readTasks().map((item) => item.id === id ? { ...item, ...patch } : item));
}
export function dismissHarnessTask(id: string) { writeTasks(readTasks().filter((item) => item.id !== id)); }

/** Continue polling a persisted task after the page has been refreshed. */
export async function resumeHarnessTask(task: HarnessTask) {
  if (!task.backendJobId) throw new Error('后台任务缺少桥接任务 ID，无法恢复');
  if (task.status === 'completed') {
    return {
      output: String(task.output || ''),
      elapsed_ms: Math.max(0, (task.completedAt || Date.now()) - task.startedAt),
      status: task.strategyStatus || 'completed',
      receipt: task.receipt,
      structured: task.structured,
      taskId: task.id,
    };
  }
  let connectivityFailures = 0;
  while (true) {
    const endpoint = task.backendKind === 'strategy' ? '/strategy/job/' : '/agent/job/';
    let response: Response;
    try {
      response = await fetchBridge(`${endpoint}${encodeURIComponent(task.backendJobId)}`, { cache: 'no-store' });
      connectivityFailures = 0;
    } catch (error) {
      connectivityFailures += 1;
      if (connectivityFailures <= 30) {
        await delay(Math.min(5000, 700 + connectivityFailures * 150));
        continue;
      }
      throw error;
    }
    const job = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(job.error || '后台任务状态读取失败');
    if (job.status === 'completed') {
      const result = job.result && typeof job.result === 'object' ? job.result : {};
      const output = String(job.output || result.output || '');
      const strategyStatus = String(result.status || job.strategy_status || 'completed');
      const patch: Partial<HarnessTask> = {
        status: 'completed', output, completedAt: Date.now(),
        strategyStatus,
        receipt: result.receipt,
        structured: result.structured,
      };
      updateHarnessTask(task.id, patch);
      return {
        output,
        elapsed_ms: Number(job.elapsed_ms || result.elapsed_ms || (Date.now() - task.startedAt)),
        status: strategyStatus,
        receipt: result.receipt,
        structured: result.structured,
        taskId: task.id,
      };
    }
    if (job.status === 'failed') {
      const message = String(job.error || '后台任务执行失败');
      updateHarnessTask(task.id, { status: 'failed', error: message, completedAt: Date.now() });
      throw new Error(message);
    }
    await delay(1000);
  }
}

async function delay(ms: number) { await new Promise((resolve) => window.setTimeout(resolve, ms)); }

async function fetchBridge(path: string, init?: RequestInit) {
  let lastError: unknown;
  let lastGatewayResponse: Response | undefined;
  const endpoints = [...BRIDGE_ENDPOINTS, bridgeUrl()];
  const suffix = path.startsWith('/') ? path : `/${path}`;
  for (let endpointIndex = 0; endpointIndex < endpoints.length; endpointIndex += 1) {
    for (let attempt = 0; attempt < 3; attempt += 1) {
      try {
        // bridgeUrl() 返回根地址时带一个结尾斜杠；直接拼接 /agent/start
        // 会变成 //agent/start，而 4319 会按未知路径返回“路径不存在”。
        const endpoint = endpoints[endpointIndex].replace(/\/+$/, '');
        const response = await fetch(`${endpoint}${suffix}`, init);
        // 4319 短暂重启时可能返回 502/503。把它视为连接失败，
        // 继续重试，避免前端过早结束已提交的后台任务。
        if (response.status >= 502 && response.status <= 504) {
          lastGatewayResponse = response;
          lastError = new Error(`桥接入口返回 ${response.status}`);
          if (attempt < 2) {
            await delay(350 * (attempt + 1));
            continue;
          }
          // The current endpoint is unavailable. Leave the retry loop so the
          // outer loop can try the next endpoint instead of returning 401/404.
          break;
        }
        return response;
      } catch (error) {
        lastError = error;
        // 服务重启或浏览器预检短暂失败时自动重试，再尝试另一个回环地址。
        if (attempt < 2) await delay(350 * (attempt + 1));
      }
    }
  }
  const reason = lastError instanceof Error
    ? lastError.message
    : lastGatewayResponse
      ? `桥接代理返回 ${lastGatewayResponse.status}`
      : String(lastError || '未知网络错误');
  throw new Error(`无法连接 DeepSeek Harness 桥接服务（4319）：${reason}`);
}

export async function startDailyDataRefresh(options: { force?: boolean } = {}) {
  const response = await fetchBridge('/data/daily/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ force: options.force === true }),
  });
  const value = await response.json().catch(() => ({}));
  if (!response.ok || !value || typeof value !== 'object') throw new Error(value?.error || `每日数据更新启动失败（${response.status}）`);
  return value as { status: string; state?: { status?: string; date?: string }; job?: { status?: string; date?: string } };
}

export async function getDailyDataRefreshStatus() {
  const response = await fetchBridge('/data/daily/status', { cache: 'no-store' });
  const value = await response.json().catch(() => ({}));
  if (!response.ok || !value || typeof value !== 'object') throw new Error(value?.error || `每日数据状态读取失败（${response.status}）`);
  return value as { status: string; state?: { status?: string; date?: string }; jobs?: unknown[] };
}

export async function startSupplementalDataRefresh(options: { force?: boolean } = {}) {
  const response = await fetchBridge('/data/public/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ force: options.force === true }),
  });
  const value = await response.json().catch(() => ({}));
  if (!response.ok || !value || typeof value !== 'object') throw new Error(value?.error || `其他数据补齐启动失败（${response.status}）`);
  return value as { status: string; state?: { status?: string; date?: string }; job?: { status?: string; date?: string } };
}

export async function getSupplementalDataRefreshStatus() {
  const response = await fetchBridge('/data/public/status', { cache: 'no-store' });
  const value = await response.json().catch(() => ({}));
  if (!response.ok || !value || typeof value !== 'object') throw new Error(value?.error || `其他数据状态读取失败（${response.status}）`);
  return value as { status: string; state?: { status?: string; date?: string }; jobs?: unknown[] };
}

export async function startUnifiedDataArchive(options: { force?: boolean } = {}) {
  const response = await fetchBridge('/data/archive/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ force: options.force === true }),
  });
  const value = await response.json().catch(() => ({}));
  if (!response.ok || !value || typeof value !== 'object') throw new Error(value?.error || `统一数据落盘启动失败（${response.status}）`);
  return value as UnifiedDataArchiveResponse;
}

export async function getUnifiedDataArchiveStatus() {
  const response = await fetchBridge('/data/archive/status', { cache: 'no-store' });
  const value = await response.json().catch(() => ({}));
  if (!response.ok || !value || typeof value !== 'object') throw new Error(value?.error || `统一数据落盘状态读取失败（${response.status}）`);
  return value as UnifiedDataArchiveResponse;
}

export type UnifiedDataArchiveResponse = {
  status: string;
  message?: string;
  state?: {
    status?: string;
    date?: string;
    startedAt?: string;
    finishedAt?: string;
    steps?: Array<Record<string, unknown>>;
    report?: UnifiedDataArchiveReport;
  };
  progress?: {
    completed?: number;
    total?: number;
    percent?: number;
    currentStep?: string;
    failed?: number;
  };
  report?: UnifiedDataArchiveReport;
  job?: { id?: string; status?: string; date?: string; started_at?: number };
  jobs?: unknown[];
};

export type UnifiedDataArchiveReport = {
  date?: string;
  htmlUrl?: string;
  jsonUrl?: string;
  htmlPath?: string;
  jsonPath?: string;
  relativeHtml?: string;
  relativeJson?: string;
  generatedAt?: string;
};

export async function startUnifiedDataVerification(options: { force?: boolean } = {}) {
  const response = await fetchBridge('/data/archive/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ force: options.force === true }),
  });
  const value = await response.json().catch(() => ({}));
  if (!response.ok || !value || typeof value !== 'object') throw new Error(value?.error || `统一数据校验启动失败（${response.status}）`);
  return value as { status: string; state?: { status?: string; date?: string }; job?: { status?: string; date?: string } };
}

export async function getUnifiedDataVerificationStatus() {
  const response = await fetchBridge('/data/archive/verify/status', { cache: 'no-store' });
  const value = await response.json().catch(() => ({}));
  if (!response.ok || !value || typeof value !== 'object') throw new Error(value?.error || `统一数据校验状态读取失败（${response.status}）`);
  return value as { status: string; state?: { status?: string; date?: string }; jobs?: unknown[] };
}

export async function runHarnessInBackground(input: {
  task: string;
  skillId: string;
  label: string;
  market: unknown;
  context?: unknown;
  originPage: string;
  originStockCode?: string;
  expectedSeconds: number;
}) {
  const local = createHarnessTask({ skillId: input.skillId, label: input.label, originPage: input.originPage, originStockCode: input.originStockCode, expectedSeconds: input.expectedSeconds, backendKind: 'harness' });
  try {
    const startResponse = await fetchBridge('/agent/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ task: input.task, skillId: input.skillId, market: input.market, context: input.context }) });
    const start = await startResponse.json().catch(() => ({}));
    if (startResponse.status === 409 || start.status === 'busy') {
      const message = String(start.error || 'Harness 正在执行长任务，请稍后再试。');
      // A rejected concurrent start is not a failed task. Remove its temporary
      // tray entry and surface the reason immediately on every calling page.
      dismissHarnessTask(local.id);
      window.alert(message);
      throw new Error(message);
    }
    if (!startResponse.ok || start.status !== 'accepted' || typeof start.job_id !== 'string') throw new Error(start.error || `Harness 后台任务启动失败（${startResponse.status}）`);
    updateHarnessTask(local.id, { backendJobId: start.job_id, status: 'running' });
    let connectivityFailures = 0;
    while (true) {
      let response: Response;
      try {
        response = await fetchBridge(`/agent/job/${encodeURIComponent(start.job_id)}`, { cache: 'no-store' });
        connectivityFailures = 0;
      } catch (error) {
        // 状态查询属于长任务轮询。开发服务器热更新、桥接进程重启或
        // 临时网络抖动不应让已经 accepted 的任务立即失败。
        connectivityFailures += 1;
        if (connectivityFailures <= 30) {
          await delay(Math.min(5000, 700 + connectivityFailures * 150));
          continue;
        }
        throw error;
      }
      const job = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(job.error || 'Harness 任务状态读取失败');
      if (job.status === 'completed') {
        updateHarnessTask(local.id, { status: 'completed', output: String(job.output || ''), completedAt: Date.now() });
        return { output: String(job.output || ''), elapsed_ms: Number(job.elapsed_ms || 0), taskId: local.id };
      }
      if (job.status === 'failed') {
        const message = String(job.error || 'DeepSeek Harness 执行失败');
        updateHarnessTask(local.id, { status: 'failed', error: message, completedAt: Date.now() });
        throw new Error(message);
      }
      await delay(1000);
    }
  } catch (error) {
    if (readTasks().some((item) => item.id === local.id && item.status !== 'failed')) updateHarnessTask(local.id, { status: 'failed', error: error instanceof Error ? error.message : String(error), completedAt: Date.now() });
    throw error;
  }
}

/** 启动独立的原始策略后台任务，允许多个策略并行执行。 */
export async function runStrategyInBackground(input: {
  skillId: string;
  label: string;
  originPage: string;
  expectedSeconds: number;
}) {
  const local = createHarnessTask({
    skillId: input.skillId,
    label: input.label,
    originPage: input.originPage,
    expectedSeconds: input.expectedSeconds,
    backendKind: 'strategy',
  });
  try {
    const startResponse = await fetchBridge('/strategy/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ skillId: input.skillId }),
    });
    const start = await startResponse.json().catch(() => ({}));
    if (!startResponse.ok || start.status !== 'accepted' || typeof start.job_id !== 'string') {
      throw new Error(start.error || `策略后台任务启动失败（${startResponse.status}）`);
    }
    updateHarnessTask(local.id, { backendJobId: start.job_id, status: 'running' });
    let connectivityFailures = 0;
    while (true) {
      let response: Response;
      try {
        response = await fetchBridge(`/strategy/job/${encodeURIComponent(start.job_id)}`, { cache: 'no-store' });
        connectivityFailures = 0;
      } catch (error) {
        connectivityFailures += 1;
        if (connectivityFailures <= 30) {
          await delay(Math.min(5000, 700 + connectivityFailures * 150));
          continue;
        }
        throw error;
      }
      const job = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(job.error || '策略任务状态读取失败');
      if (job.status === 'completed') {
        const output = String(job.output || '');
        const result = job.result && typeof job.result === 'object' ? job.result : {};
        updateHarnessTask(local.id, {
          status: 'completed',
          output,
          completedAt: Date.now(),
          strategyStatus: String(result.status || job.strategy_status || 'UNKNOWN'),
          receipt: result.receipt,
          structured: result.structured,
        });
        return {
          output,
          elapsed_ms: Number(job.elapsed_ms || result.elapsed_ms || 0),
          status: String(result.status || job.strategy_status || 'UNKNOWN'),
          receipt: result.receipt && typeof result.receipt === 'object' ? result.receipt : null,
          structured: result.structured && typeof result.structured === 'object' ? result.structured : null,
          taskId: local.id,
        };
      }
      if (job.status === 'failed') {
        const message = String(job.error || '原始策略执行失败');
        updateHarnessTask(local.id, { status: 'failed', error: message, completedAt: Date.now() });
        throw new Error(message);
      }
      await delay(1000);
    }
  } catch (error) {
    if (readTasks().some((item) => item.id === local.id && item.status !== 'failed')) {
      updateHarnessTask(local.id, { status: 'failed', error: error instanceof Error ? error.message : String(error), completedAt: Date.now() });
    }
    throw error;
  }
}

export async function resumeHarnessTasks() {
  for (const task of readTasks().filter((item) => item.status === 'starting' || item.status === 'running')) {
    if (!task.backendJobId) continue;
    try {
      const endpoint = task.backendKind === 'strategy' ? '/strategy/job/' : '/agent/job/';
      const response = await fetchBridge(`${endpoint}${encodeURIComponent(task.backendJobId)}`, { cache: 'no-store' });
      const job = await response.json().catch(() => ({}));
      if (job.status === 'completed') {
        const result = job.result && typeof job.result === 'object' ? job.result : {};
        updateHarnessTask(task.id, {
          status: 'completed',
          output: String(job.output || result.output || ''),
          completedAt: Date.now(),
          strategyStatus: task.backendKind === 'strategy' ? String(result.status || job.strategy_status || 'UNKNOWN') : task.strategyStatus,
          receipt: task.backendKind === 'strategy' ? result.receipt : task.receipt,
          structured: task.backendKind === 'strategy' ? result.structured : task.structured,
        });
      }
      else if (job.status === 'failed' || !response.ok) updateHarnessTask(task.id, { status: 'failed', error: String(job.error || 'Harness 任务状态读取失败'), completedAt: Date.now() });
    } catch { /* 下一次刷新继续恢复 */ }
  }
}
