import assert from 'node:assert/strict';
import { test } from 'node:test';
import vm from 'node:vm';
import path from 'node:path';
import os from 'node:os';
import { readFileSync, existsSync } from 'node:fs';
import { mkdtemp, mkdir, writeFile, unlink, rm } from 'node:fs/promises';
import { randomUUID } from 'node:crypto';
import { spawn } from 'node:child_process';
import ts from 'typescript';

const source = readFileSync(new URL('../agent-server.mjs', import.meta.url), 'utf8');
const ast = ts.createSourceFile('agent-server.mjs', source, ts.ScriptTarget.Latest, true, ts.ScriptKind.JS);
const functions = new Map(ast.statements.filter(ts.isFunctionDeclaration).map(node => [node.name.text, node.getText(ast)]));
function context(names, overrides = {}) {
  return vm.createContext({ console, process, Buffer, path, existsSync, mkdir, writeFile, unlink, randomUUID, spawn,
    setTimeout, clearTimeout, MAX_OUTPUT: 256 * 1024, ...overrides,
    code: names.map(name => { assert.ok(functions.has(name), name); return functions.get(name); }).join('\n') });
}
function load(ctx) { vm.runInContext(ctx.code, ctx); return ctx; }

test('packaged Harness fails closed without bundled entry', () => {
  const c = load(context(['commandFor'], { PACKAGED_RUNTIME: true, process: { env: {}, execPath: process.execPath }, APP_ROOT: os.tmpdir() }));
  assert.throws(() => c.commandFor('probe'), /内置 DeepSeek Harness 缺失/);
});

test('Harness environment carries selected paths and excludes other provider keys', () => {
  const c = load(context(['harnessEnvironment'], { DATA_ROOT: 'D:\\client\\data\\resource-library', APP_ROOT: 'D:\\client\\resources\\app',
    HARNESS_ROOT: 'D:\\client\\data\\resource-library\\harness', PACKAGED_RUNTIME: true,
    SKILL_SOURCE: 'D:\\client\\resources\\app\\harness-skills',
    bridgeTdxRoot: () => 'E:\\通达信', localPythonExecutable: () => 'D:\\runtime\\python.exe',
    process: { execPath: process.execPath, env: { PATH: 'old', OPENAI_API_KEY: 'must-not-leak', DEEPSEEK_API_KEY: 'test-only' } } }));
  const env = c.harnessEnvironment();
  assert.equal(env.ZHANGCAI_TDX_ROOT, 'E:\\通达信');
  assert.equal(env.TDX_ROOT, 'E:\\通达信');
  assert.equal(env.TDX_ROOTS, 'E:\\通达信');
  assert.equal(env.ONESTOCK_STOCK_DATA_ROOT, 'D:\\client\\data\\resource-library');
  assert.equal(env.TDX_HUB_PATH, 'D:\\client\\resources\\app\\harness-skills\\tdx-local-hub\\scripts\\tdx_hub.py');
  assert.equal(env.ZHANGCAI_RESOURCE_LIBRARY, env.ZHANGCAI_DATA_DIR);
  assert.equal(env.OPENAI_API_KEY, undefined);
  assert.equal(env.ZHANGCAI_PACKAGED, '1');
  assert.ok(env.PATH.startsWith(path.dirname(process.execPath)));
});

test('real subprocess: Unicode chunks, large JSON, empty output, failure, timeout, overflow', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'zhangcai-harness-test-'));
  let script = '';
  let timeout = 5000;
  const c = load(context(['stopHarnessProcess', 'coerceHarnessJson', 'runHarness'], {
    HARNESS_ROOT: root, DATA_ROOT: root, timeoutForSkill: () => timeout,
    harnessEnvironment: () => ({ ...process.env }),
    commandFor: () => ({ command: process.execPath, args: ['-e', script] }),
  }));
  try {
    script = `const b=Buffer.from(JSON.stringify({summary:'中文报价'}));process.stdout.write(b.subarray(0,14));setTimeout(()=>process.stdout.write(b.subarray(14)),20);`;
    assert.equal(JSON.parse((await c.runHarness('test')).output).summary, '中文报价');
    script = `console.log(JSON.stringify({summary:'x'.repeat(280000)}))`;
    assert.equal(JSON.parse((await c.runHarness('test')).output).summary.length, 280000);
    script = '';
    await assert.rejects(c.runHarness('test'), /未返回内容/);
    script = `process.stderr.write('controlled failure');process.exit(3)`;
    await assert.rejects(c.runHarness('test'), /退出码 3/);
    script = `process.stdout.write('x'.repeat(1100000))`;
    await assert.rejects(c.runHarness('test'), /超过容量限制/);
    timeout = 150;
    script = `setInterval(()=>{},1000)`;
    await assert.rejects(c.runHarness('test'), /超时/);
  } finally { await rm(root, { recursive: true, force: true }); }
});

test('launcher rejection propagates and cancelled network retries release lock', async () => {
  let released = false;
  let calls = 0;
  let cancelled = false;
  const c = load(context(['runHarnessWithRetry'], {
    reserveHarnessExecution: () => null, releaseHarnessExecution: () => { released = true; },
    runHarness: async () => { calls++; cancelled = true; throw new Error('ECONNRESET'); },
  }));
  await assert.rejects(c.runHarnessWithRetry('probe', '', { cancelled: () => cancelled }), /ECONNRESET/);
  assert.equal(calls, 1);
  assert.equal(released, true);
  const d = load(context(['runHarness'], { HARNESS_ROOT: os.tmpdir(), commandFor: () => { throw new Error('launcher missing'); } }));
  await assert.rejects(d.runHarness('probe'), /launcher missing/);
});
