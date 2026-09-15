'use client';

import { saveReportArchive } from '@/lib/report-archive';
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
// 优先走网页开发服务器的同源代理，避免浏览器对 localhost -> 127.0.0.1
// 的 Private Network 请求策略；直连地址作为代理不可用时的兼容回退。
const BRIDGE_ENDPOINTS = ['/bridge'];

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
  // 任务状态与“我的报告”共用一个稳定 ID。这样刷新页面、桥接重启或
  // Harness 超时后，用户仍能看到“未完成”记录，而不是丢失这次操作。
  for (const task of next) {
    const now = new Date().toISOString();
    const date = now.slice(0, 10).replace(/-/g, '');
    const running = task.status === 'starting' || task.status === 'running';
    const summary = task.status === 'completed'
      ? 'Harness 任务已完成，结果已返回。'
      : task.status === 'failed'
        ? `任务未完成：${task.error || 'Harness 执行失败'}`
        : running
          ? 'Harness 任务正在后台运行，结果尚未返回。'
          : 'Harness 任务等待桥接服务受理。';
    saveReportArchive({
      id: `harness-task-${task.id}`,
      createdAt: new Date(task.startedAt).toISOString(),
      updatedAt: now,
      date,
      title: `掌财智能体 · ${task.label} · ${task.status === 'completed' ? '任务记录' : '未完成任务'}`,
      reportType: 'Harness任务',
      generatedBy: `DeepSeek Harness · ${task.skillId || '通用研究'}`,
      summary,
      dataScope: `${task.originPage}${task.originStockCode ? ` · ${task.originStockCode}` : ''}`,
      content: {
        kind: 'harness-task',
        taskId: task.id,
        backendJobId: task.backendJobId,
        backendKind: task.backendKind,
        status: task.status,
        startedAt: task.startedAt,
        completedAt: task.completedAt,
        expectedSeconds: task.expectedSeconds,
        error: task.error,
        strategyStatus: task.strategyStatus,
        receipt: task.receipt,
        structured: task.structured,
      },
      raw: task.output || task.error || '',
    });
  }
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
  // bridgeUrl() knows whether the page is local or served below /test on the
  // remote host, so prefer it. Keep /bridge as a development-proxy fallback.
  const endpoints = Array.from(new Set([bridgeUrl(), ...BRIDGE_ENDPOINTS]));
  for (let endpointIndex = 0; endpointIndex < endpoints.length; endpointIndex += 1) {
    for (let attempt = 0; attempt < 3; attempt += 1) {
      try {
        const response = await fetch(`${endpoints[endpointIndex]}${path}`, init);
        // 开发模式的同源代理只在 Vite 开发服务中存在；生产服务或远端
        // 8888 的旧首页可能分别返回 404/401。上述状态同样表示“当前
        // 入口不可用”，必须切换到 bridgeUrl() 的真实桥接地址。
        const endpointUnavailable = [401, 403, 404, 405, 502, 503, 504].includes(response.status);
        if (endpointUnavailable) {
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
  throw new Error(`无法连接 DeepSeek Harness 桥接服务（4318）：${reason}`);
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
