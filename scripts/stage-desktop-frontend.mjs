import { createHash } from 'node:crypto';
import { cp, mkdir, mkdtemp, readFile, readdir, rename, stat, symlink, writeFile } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(fileURLToPath(new URL('..', import.meta.url)));
const metadata = JSON.parse(await readFile(path.join(root, 'package.json'), 'utf8'));
if (!/^\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?$/.test(metadata.version)) throw new Error('Invalid product version');
const sources = ['app','components','config','hooks','lib','public','package.json','tsconfig.json','vite.config.ts','next.config.ts','components.json','next-env.d.ts'];
async function digestTree(file, hash) {
  const info = await stat(file);
  if (info.isDirectory()) {
    for (const item of (await readdir(file)).sort()) await digestTree(path.join(file,item),hash);
  } else { hash.update(path.relative(root,file).replaceAll('\\','/')); hash.update(await readFile(file)); }
}
const hash = createHash('sha256');
for (const name of sources) await digestTree(path.join(root,name),hash);
hash.update(await readFile(path.join(root,'pnpm-lock.yaml')));
const sourceHash = hash.digest('hex');
const staging = path.join(root,'packaging/staging');
const target = path.join(staging,`site-build-${metadata.version}`);
try {
  const previous = JSON.parse(await readFile(path.join(target,'provenance.json'),'utf8'));
  if (previous.kind === 'source-build' && previous.sourceHash === sourceHash) {
    await stat(path.join(target,'dist/server/index.js'));
    console.log(JSON.stringify({status:'REUSED',target,sourceHash}));
    process.exit(0);
  }
} catch (error) { if (error.code !== 'ENOENT' && !(error instanceof SyntaxError)) throw error; }
await mkdir(staging,{recursive:true});
const work = await mkdtemp(path.join(staging,`site-work-${metadata.version}-`));
for (const name of sources) await cp(path.join(root,name),path.join(work,name),{recursive:true});
await symlink(path.join(root,'node_modules'),path.join(work,'node_modules'),process.platform === 'win32' ? 'junction' : 'dir');
const node = process.platform === 'win32' ? path.join(root,'.runtime/node/node.exe') : process.execPath;
const build = spawnSync(node,[path.join(root,'node_modules/vinext/dist/cli.js'),'build'],{cwd:work,stdio:'inherit',env:process.env});
if (build.status !== 0) process.exit(build.status || 1);
await stat(path.join(work,'dist/server/index.js'));
const assembled = await mkdtemp(path.join(staging,`.site-build-${metadata.version}-`));
await cp(path.join(work,'dist'),path.join(assembled,'dist'),{recursive:true});
await writeFile(path.join(assembled,'provenance.json'),JSON.stringify({kind:'source-build',productVersion:metadata.version,sourceHash,sourceWork:path.relative(root,work),builtAt:new Date().toISOString()},null,2)+'\n');
try { await stat(target); await rename(target,`${target}-previous-${Date.now()}`); } catch(error) { if(error.code !== 'ENOENT') throw error; }
await rename(assembled,target);
console.log(JSON.stringify({status:'BUILT_FROM_SOURCE',target,sourceHash}));
