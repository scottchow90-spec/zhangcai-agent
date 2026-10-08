// Maintainer-only generation after downloading exactly requirements-dev.txt.
import { createHash } from 'node:crypto';
import { readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('..', import.meta.url));
const directory = 'development-assets/python-dev-wheels';
const requirements = (await readFile(path.join(root,'requirements-dev.txt'),'utf8')).split(/\r?\n/).filter(x=>x && !x.startsWith('#'));
const files = (await readdir(path.join(root,directory))).filter(x=>x.endsWith('.whl')).sort();
if(files.length !== requirements.length) throw new Error('Unexpected wheel set');
const assets=[];
const locked=[];
for(const requirement of requirements) {
  const [name,version]=requirement.split('==');
  const prefix=`${name.replaceAll('-','_')}-${version}-`.toLowerCase();
  const file=files.find(x=>x.toLowerCase().startsWith(prefix));
  if(!file) throw new Error(`Missing wheel: ${requirement}`);
  const bytes=await readFile(path.join(root,directory,file));
  const sha256=createHash('sha256').update(bytes).digest('hex');
  assets.push({path:`${directory}/${file}`,bytes:bytes.length,sha256});
  locked.push(`${requirement} --hash=sha256:${sha256}`);
}
await writeFile(path.join(root,'requirements-dev-lock.txt'),'# Generated from the bundled wheel set.\n'+locked.join('\n')+'\n');
const manifest=JSON.parse(await readFile(path.join(root,'development-assets/manifest.json'),'utf8'));
manifest.pythonDevWheels=assets;
await writeFile(path.join(root,'development-assets/manifest.json'),JSON.stringify(manifest,null,2)+'\n');
console.log(JSON.stringify({status:'LOCKED',wheels:assets.length}));
