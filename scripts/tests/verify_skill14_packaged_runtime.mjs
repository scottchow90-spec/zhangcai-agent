import { spawnSync } from 'node:child_process';
import { mkdtemp, rm, realpath } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { defaultAppRoot, discover, loadProvider, readJson } from './harness-provider.mjs';

const appRoot = path.resolve(process.env.ZHANGCAI_RELEASE_APP_ROOT || defaultAppRoot);
const errors = [];
let prepared = 0, discovered = 0;
const temp = await mkdtemp(path.join(os.tmpdir(), 'zhangcai-skill14-check-'));
try {
  const { skills } = await readJson(path.join(appRoot, 'config/skill14-catalog.json'));
  const { archives } = await readJson(path.join(appRoot, 'config/skill14-archive-lock.json'));
  const expectedHashes = new Map(archives.map((row) => [row.id, row]));
  if (skills.length !== 14 || new Set(skills.map((row) => row.id)).size !== 14
    || archives.length !== 14 || expectedHashes.size !== 14) throw new Error('Expected fourteen unique skills and archive locks');
  const Provider = await loadProvider(appRoot);
  const python = process.env.ZHANGCAI_RELEASE_PYTHON || path.join(appRoot, '.runtime/python/python.exe');
  const env = { ...process.env, ZHANGCAI_APP_ROOT: appRoot, ZHANGCAI_DATA_DIR: temp,
    ZHANGCAI_PACKAGED: '1', PYTHONDONTWRITEBYTECODE: '1', PYTHONIOENCODING: 'utf-8',
    ZHANGCAI_TDX_ROOT: path.join(temp, '__tdx_not_configured__') };
  // The same recovered entry and command are used by agent-server.mjs.
  for (const skill of skills) {
    try {
      const result = spawnSync(python, ['-B', path.join(appRoot, 'scripts/skill14_data_runtime.py'),
        'prepare-harness-skill', '--skill-id', skill.id], { cwd: appRoot, env, encoding: 'utf8', timeout: 120000, maxBuffer: 1024 * 1024 });
      if (result.error) throw result.error;
      const bundle = JSON.parse(result.stdout);
      if (result.status !== 0 || bundle.status !== 'available' || bundle.skill_id !== skill.id) {
        throw new Error(bundle.error || `Skill preparation exited ${result.status}`);
      }
      const locked = expectedHashes.get(skill.id);
      if (!locked || locked.archive !== skill.archive || bundle.archive_sha256 !== locked.sha256) throw new Error('Prepared archive differs from the release lock');
      const preparedRoot = await realpath(bundle.harness_skill_root);
      const relative = path.relative(await realpath(temp), preparedRoot);
      if (!relative || relative.startsWith(`..${path.sep}`) || relative === '..' || path.isAbsolute(relative)) {
        throw new Error('Prepared skill escaped the isolated data root');
      }
      prepared++;
      await discover(Provider, preparedRoot, [{ name: bundle.skill_name, root: preparedRoot }]);
      discovered++;
    } catch (error) { errors.push(`${skill.id}: ${error.message}`); }
  }
} catch (error) { errors.push(error.message); }
finally { await rm(temp, { recursive: true, force: true }); }
const report = { status: errors.length === 0 && prepared === 14 && discovered === 14 ? 'CLEAN_PASS' : 'BLOCKED',
  prepared, discovered, business_execution_tested: false, errors };
console.log(JSON.stringify(report, null, 2));
process.exitCode = report.status === 'CLEAN_PASS' ? 0 : 1;
