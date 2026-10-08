import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const root = fileURLToPath(new URL('..',import.meta.url));
const result = spawnSync(path.join(root,'.runtime/python/python.exe'),['-B','-m','pytest',
  'scripts/tests','harness-skills/stock-unified/tests/test_portable_contract_paths.py',
  'harness-skills/stock-unified/tests/test_portable_tdx_paths.py','-q'],{
  cwd:root,stdio:'inherit',env:{...process.env,PYTHONUTF8:'1',PYTHONIOENCODING:'utf-8'},
});
if(result.error) console.error(result.error.message);
process.exitCode = result.status ?? 1;
