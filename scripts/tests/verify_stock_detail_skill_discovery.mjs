import path from 'node:path';
import { defaultAppRoot, discover, loadProvider, readJson } from './harness-provider.mjs';

const appRoot = path.resolve(process.env.ZHANGCAI_RELEASE_APP_ROOT || defaultAppRoot);
let report;
try {
  const { skills } = await readJson(path.join(appRoot, 'config/stock-detail-release.json'));
  if (!Array.isArray(skills) || skills.length !== 10 || new Set(skills).size !== 10
    || skills.some((name) => typeof name !== 'string' || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(name))) throw new Error('Expected exactly ten stock-detail skills');
  const Provider = await loadProvider(appRoot);
  const root = path.join(appRoot, 'harness-skills');
  const result = await discover(Provider, root, skills.map((name) => ({ name, root: path.join(root, name) })));
  report = { status: 'CLEAN_PASS', dsh_discovered: result.found.length, skills: result.found, warnings: result.warnings, errors: [] };
} catch (error) {
  report = { status: 'BLOCKED', dsh_discovered: 0, errors: [error.message] };
}
console.log(JSON.stringify(report, null, 2));
process.exitCode = report.status === 'CLEAN_PASS' ? 0 : 1;
