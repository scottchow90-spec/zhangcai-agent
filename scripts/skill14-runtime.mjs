import { existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import path from 'node:path';

const appRoot = path.resolve(process.cwd());
const configured = process.env.ZHANGCAI_PYTHON || process.env.TDX_PYTHON;
const python = [configured, path.join(appRoot, '.runtime', 'python', 'python.exe'), path.join(appRoot, 'runtime', 'python', 'python.exe')]
  .find((candidate) => candidate && existsSync(candidate));

if (!python) {
  console.error('未找到程序包内 Python：请设置 ZHANGCAI_PYTHON，或在 EXE 中内置 .runtime/python/python.exe。');
  process.exit(1);
}

const result = spawnSync(python, [path.join(appRoot, 'scripts', 'skill14_data_runtime.py'), ...process.argv.slice(2)], {
  cwd: appRoot,
  env: { ...process.env, ZHANGCAI_APP_ROOT: appRoot, ZHANGCAI_DATA_DIR: process.env.ZHANGCAI_DATA_DIR || path.join(appRoot, 'app-data') },
  stdio: 'inherit',
  windowsHide: true,
});
process.exit(result.status ?? 1);
