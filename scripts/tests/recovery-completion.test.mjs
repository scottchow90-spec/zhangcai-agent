import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { mkdtemp, mkdir, readFile, rm, symlink, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { stageRecoveredFrontend } from '../stage-recovered-frontend.mjs';

const appRoot = fileURLToPath(new URL('../..', import.meta.url));
const sha = (value) => createHash('sha256').update(value).digest('hex');
async function write(root, name, value) {
  await mkdir(path.dirname(path.join(root, name)), { recursive: true });
  await writeFile(path.join(root, name), value);
}
async function fixture() {
  const root = await mkdtemp(path.join(os.tmpdir(), 'zhangcai-staging-fixture-'));
  const files = [];
  for (const name of ['dist/client/example.js', 'dist/server/index.js']) {
    const value = Buffer.from('Synthetic compiled test fixture.\n');
    await write(root, name, value);
    files.push({ path: name, bytes: value.length, sha256: sha(value) });
  }
  await write(root, 'package.json', JSON.stringify({ version: '0.1.22' }));
  const prefix = 'electron-app/resource-library/evidence/formulas/package/';
  await write(root, prefix + 'formula.txt', 'Synthetic formula test fixture.');
  const content = await readFile(path.join(root, prefix + 'formula.txt'));
  await write(root, prefix + 'manifest.json', JSON.stringify({ required_files: ['formula.txt'],
    copied_files: [{ path: 'evidence/formulas/package/formula.txt', bytes: content.length, sha256: sha(content) }] }));
  for (const name of ['formula.txt', 'manifest.json']) {
    const value = await readFile(path.join(root, prefix + name));
    files.push({ path: prefix + name, bytes: value.length, sha256: sha(value) });
  }
  await write(root, 'docs/recovery-0.1.22/recovery-manifest.json', JSON.stringify({ productVersion: '0.1.22', files }));
  await mkdir(path.join(root, 'packaging'));
  return root;
}

test('staging preserves source bytes and reuses an identical stage', async () => {
  const root = await fixture();
  try {
    const first = await stageRecoveredFrontend(root);
    assert.equal(first.reused, false);
    const before = await readFile(path.join(root, 'dist/server/index.js'));
    assert.deepEqual(await readFile(path.join(first.target, 'dist/server/index.js')), before);
    const second = await stageRecoveredFrontend(root);
    assert.equal(second.reused, true);
    assert.deepEqual(await readFile(path.join(root, 'dist/server/index.js')), before);
    await writeFile(path.join(first.target, 'dist/server/index.js'), 'Existing stage changed');
    await assert.rejects(stageRecoveredFrontend(root), /hash mismatch/);
    assert.equal(await readFile(path.join(first.target, 'dist/server/index.js'), 'utf8'), 'Existing stage changed');
  } finally { await rm(root, { recursive: true, force: true }); }
});

test('changed or extra compiled files fail before creating staging', async () => {
  for (const extra of [false, true]) {
    const root = await fixture();
    try {
      await write(root, extra ? 'dist/client/extra.js' : 'dist/server/index.js', 'Unexpected bytes');
      await assert.rejects(stageRecoveredFrontend(root), extra ? /file set differs/ : /hash mismatch/);
      assert.equal(existsSync(path.join(root, 'packaging/staging')), false);
    } finally { await rm(root, { recursive: true, force: true }); }
  }
});

test('an incomplete existing stage is retained for review', async () => {
  const root = await fixture();
  try {
    const target = path.join(root, 'packaging/staging/site-build-0.1.22');
    await mkdir(target, { recursive: true });
    await writeFile(path.join(target, 'keep.txt'), 'Do not overwrite');
    await assert.rejects(stageRecoveredFrontend(root), /incomplete/);
    assert.equal(await readFile(path.join(target, 'keep.txt'), 'utf8'), 'Do not overwrite');
  } finally { await rm(root, { recursive: true, force: true }); }
});

test('formula tampering blocks staging without consulting user app-data', async () => {
  const root = await fixture();
  try {
    await write(root, 'electron-app/resource-library/evidence/formulas/package/formula.txt', 'Changed seed');
    await assert.rejects(stageRecoveredFrontend(root), /Formula seed hash mismatch/);
    assert.equal(existsSync(path.join(root, 'app-data')), false);
  } finally { await rm(root, { recursive: true, force: true }); }
});

test('formula manifest tampering cannot authorize changed embedded files', async () => {
  const root = await fixture();
  try {
    const prefix = 'electron-app/resource-library/evidence/formulas/package/';
    const changed = Buffer.from('Tampered embedded formula');
    await write(root, prefix + 'formula.txt', changed);
    await write(root, prefix + 'manifest.json', JSON.stringify({ required_files: ['formula.txt'],
      copied_files: [{ path: 'evidence/formulas/package/formula.txt', bytes: changed.length, sha256: sha(changed) }] }));
    await assert.rejects(stageRecoveredFrontend(root), /Formula seed hash mismatch/);
  } finally { await rm(root, { recursive: true, force: true }); }
});

test('Windows build hooks stage verified evidence before preflight', async () => {
  for (const name of ['package-win.ps1', 'package-win-dir.ps1']) {
    const script = await readFile(path.join(appRoot, 'scripts', name), 'utf8');
    assert.ok(script.indexOf('stage-recovered-frontend.mjs') > 0);
    assert.ok(script.indexOf('stage-recovered-frontend.mjs') < script.indexOf('package-preflight.ps1'));
    assert.equal(script.includes('stage-desktop-formula-seed.ps1'), false);
  }
  const preflight = await readFile(path.join(appRoot, 'scripts/package-preflight.ps1'), 'utf8');
  assert.equal(preflight.includes("Require-Path 'app-data"), false);
  const dependency = JSON.parse(await readFile(path.join(appRoot, 'packaging/dependency-manifest.json'), 'utf8'));
  assert.equal(dependency.mainProgramMustExclude.includes('skill-archives'), false);
});

test('linked staging directories are rejected', { skip: process.platform === 'win32' }, async () => {
  const root = await fixture();
  const outside = await mkdtemp(path.join(os.tmpdir(), 'zhangcai-outside-fixture-'));
  try {
    await symlink(outside, path.join(root, 'packaging/staging'));
    await assert.rejects(stageRecoveredFrontend(root), /symlink/);
    assert.equal(existsSync(path.join(outside, 'site-build-0.1.22')), false);
  } finally { await rm(root, { recursive: true, force: true }); await rm(outside, { recursive: true, force: true }); }
});

test('missing Harness provider produces BLOCKED and a nonzero exit', () => {
  const result = spawnSync(process.execPath, [path.join(appRoot, 'scripts/tests/verify_stock_detail_skill_discovery.mjs')], {
    env: { ...process.env, ZHANGCAI_RELEASE_DSH_ROOT: path.join(os.tmpdir(), 'zhangcai-missing-provider') }, encoding: 'utf8', timeout: 30000 });
  assert.equal(result.status, 1);
  const report = JSON.parse(result.stdout);
  assert.equal(report.status, 'BLOCKED');
  assert.equal(report.dsh_discovered, 0);
});

test('archive gate rejects missing, changed, corrupt and unsafe ZIPs', () => {
  const bundled = path.join(appRoot, '.runtime/python/python.exe');
  const python = process.env.ZHANGCAI_RELEASE_PYTHON || (existsSync(bundled) ? bundled : 'python3');
  const result = spawnSync(python, ['-B', path.join(appRoot, 'scripts/tests/test_release_verification.py')], {
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' }, encoding: 'utf8', timeout: 60000 });
  assert.equal(result.status, 0, result.error?.message || result.stderr);
});
