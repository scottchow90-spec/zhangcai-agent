import { createHash } from 'node:crypto';
import { readFile, stat } from 'node:fs/promises';
import { createReadStream } from 'node:fs';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(fileURLToPath(new URL('..',import.meta.url)));
const json = async name => JSON.parse((await readFile(path.join(root,name),'utf8')).replace(/^\uFEFF/,''));
const errors = [];
async function checkAsset(asset) {
  try {
    const file = path.join(root,asset.path);
    if((await stat(file)).size !== asset.bytes) throw new Error('size differs (possibly an LFS pointer)');
    const hash = createHash('sha256');
    for await(const chunk of createReadStream(file)) hash.update(chunk);
    if(hash.digest('hex') !== asset.sha256) throw new Error('SHA-256 differs');
  } catch(error) { errors.push(`${asset.path}: ${error.message}`); }
}
const manifest = await json('development-assets/manifest.json');
const metadata = await json('package.json');
const lock = await json('config/skill14-archive-lock.json');
if(metadata.packageManager !== `pnpm@${manifest.pnpmVersion}`) errors.push('pnpm version is not locked to the developer toolchain');
if(manifest.pythonDevWheels?.length !== 6) errors.push('Missing locked Python development wheel set');
if(lock.archives.length !== 14 || new Set(lock.archives.map(x=>x.id)).size !== 14) errors.push('Skill14 catalog must contain fourteen unique archives');
for(const asset of [manifest.installer,manifest.update,manifest.tools,...(manifest.pythonDevWheels||[]),...lock.archives.map(x=>({...x,path:`skill-archives/${x.archive}`}))]) await checkAsset(asset);
for(const original of manifest.originalFrontendSources) {
  try { await stat(path.join(root,original.path)); } catch { errors.push(`Missing frontend source: ${original.path}`); }
  if(process.argv.includes('--original-release')) await checkAsset(original);
}
for(const required of ['agent-server.mjs','electron-app/main.mjs','electron-app/preload.cjs','electron-app/tdx-root.mjs','electron-app/runtime-ports.mjs','pnpm-lock.yaml','scripts/bootstrap-dev.ps1','scripts/stage-desktop-frontend.mjs','electron-app/resources/installer-icon.ico','electron-app/resource-library/evidence/formulas/package/manifest.json']) {
  try { await stat(path.join(root,required)); } catch { errors.push(`Missing source/build input: ${required}`); }
}
for(const [file,args,expected] of [
  ['.runtime/node/node.exe',['--version'],`v${manifest.nodeVersion}`],
  ['.runtime/python/python.exe',['--version'],`Python ${manifest.pythonVersion}`],
]) {
  const result=spawnSync(path.join(root,file),args,{encoding:'utf8'});
  if(result.status !== 0 || `${result.stdout||''}${result.stderr||''}`.trim() !== expected) errors.push(`Runtime mismatch: ${file}; run scripts/bootstrap-dev.ps1`);
}
console.log(JSON.stringify({status:errors.length?'BLOCKED':'CLEAN_PASS',productVersion:metadata.version,skillArchives:lock.archives.length,sourceFiles:manifest.originalFrontendSources.length,errors},null,2));
process.exitCode=errors.length?1:0;
