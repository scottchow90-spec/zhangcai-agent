// Newly authored staging of verified release evidence; never rebuilds TSX.
import { createHash } from 'node:crypto';
import { lstat, mkdir, mkdtemp, readFile, readdir, rename, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');
async function json(file) { return JSON.parse((await readFile(file, 'utf8')).replace(/^\uFEFF/, '')); }

async function fileSet(root, prefix = '') {
  const result = [];
  for (const item of await readdir(path.join(root, prefix), { withFileTypes: true })) {
    const name = prefix ? `${prefix}/${item.name}` : item.name;
    if (item.isSymbolicLink()) throw new Error(`Release evidence cannot contain symlinks: ${name}`);
    if (item.isDirectory()) result.push(...await fileSet(root, name));
    else if (item.isFile()) result.push(name);
    else throw new Error(`Unsupported release entry: ${name}`);
  }
  return result.sort();
}

export async function verifyDist(root, records) {
  if ((await lstat(root)).isSymbolicLink()) throw new Error('Compiled evidence root cannot be a symlink');
  const expected = records.map((item) => item.path.slice('dist/'.length)).sort();
  if (new Set(expected).size !== expected.length) throw new Error('Duplicate compiled evidence path');
  for (const name of expected) {
    if (!name || name.split('/').some((part) => !part || part === '.' || part === '..') || name.includes('\\') || path.isAbsolute(name)) {
      throw new Error(`Invalid compiled evidence path: ${name}`);
    }
  }
  const actual = await fileSet(root);
  if (JSON.stringify(actual) !== JSON.stringify(expected)) throw new Error('Compiled evidence file set differs from the recovery manifest');
  for (const item of records) {
    const bytes = await readFile(path.join(root, item.path.slice(5)));
    if (bytes.length !== item.bytes || hash(bytes) !== item.sha256) throw new Error(`Compiled evidence hash mismatch: ${item.path}`);
  }
}

export async function verifyFormulaSeed(appRoot, recoveryFiles) {
  const prefix = 'evidence/formulas/package/';
  const root = path.join(appRoot, 'electron-app/resource-library', prefix);
  if ((await lstat(root)).isSymbolicLink()) throw new Error('Formula seed root cannot be a symlink');
  const releasePrefix = 'electron-app/resource-library/' + prefix;
  const records = recoveryFiles.filter((item) => item.path.startsWith(releasePrefix));
  const expected = records.map((item) => item.path.slice(releasePrefix.length)).sort();
  if (!records.length || new Set(expected).size !== expected.length
    || JSON.stringify(await fileSet(root)) !== JSON.stringify(expected)) throw new Error('Formula seed file set differs from the recovery manifest');
  for (const item of records) {
    const bytes = await readFile(path.join(appRoot, item.path));
    if (bytes.length !== item.bytes || hash(bytes) !== item.sha256) throw new Error(`Formula seed hash mismatch: ${item.path}`);
  }
  const manifest = await json(path.join(root, 'manifest.json'));
  const files = new Map(manifest.copied_files.map((item) => [item.path, item]));
  if (!manifest.required_files?.length) throw new Error('Formula seed has no required files');
  for (const name of manifest.required_files) {
    if (name.includes('\\') || name.split('/').some((part) => !part || part === '.' || part === '..') || path.isAbsolute(name)) throw new Error(`Invalid formula seed path: ${name}`);
    const record = files.get(prefix + name);
    const bytes = await readFile(path.join(root, name));
    if (!record || bytes.length !== record.bytes || hash(bytes) !== record.sha256) throw new Error(`Formula seed hash mismatch: ${name}`);
  }
  if ((await fileSet(root)).some((name) => /\.lc5$/i.test(name))) throw new Error('Formula seed contains raw minute data');
  return manifest.required_files.length;
}

export async function stageRecoveredFrontend(appRoot) {
  const packageMetadata = await json(path.join(appRoot, 'package.json'));
  const recovery = await json(path.join(appRoot, 'docs/recovery-0.1.22/recovery-manifest.json'));
  if (packageMetadata.version !== recovery.productVersion) throw new Error('Product version differs from the recovered release');
  const records = recovery.files.filter((item) => item.path.startsWith('dist/'));
  if (records.length === 0) throw new Error('Recovery manifest contains no compiled release evidence');
  const source = path.join(appRoot, 'dist');
  await verifyDist(source, records);
  const formulaFiles = await verifyFormulaSeed(appRoot, recovery.files);
  const parent = path.join(appRoot, 'packaging/staging');
  // Refuse a linked staging ancestor, so writes stay in this checkout.
  if ((await lstat(path.join(appRoot, 'packaging'))).isSymbolicLink()) throw new Error('Packaging directory cannot be a symlink');
  try {
    if ((await lstat(parent)).isSymbolicLink()) throw new Error(`Staging directory cannot be a symlink: ${parent}`);
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }
  await mkdir(parent, { recursive: true });
  const target = path.join(parent, `site-build-${packageMetadata.version}`);
  let reused = false;
  try {
    const stat = await lstat(target);
    if (!stat.isDirectory() || stat.isSymbolicLink()) throw new Error('Existing frontend staging is not a real directory');
    await verifyDist(path.join(target, 'dist'), records);
    const provenance = await json(path.join(target, 'provenance.json'));
    if (provenance.productVersion !== packageMetadata.version || provenance.kind !== 'exact-recovered-release') throw new Error('Existing staging provenance differs');
    reused = true;
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
    // A pre-existing incomplete staging must be preserved for review.
    try { await lstat(target); throw new Error('Existing frontend staging is incomplete; it was not overwritten'); }
    catch (probe) { if (probe.code !== 'ENOENT') throw probe; }
    const temporary = await mkdtemp(path.join(parent, '.recovered-frontend-'));
    try {
      for (const item of records) {
        const destination = path.join(temporary, item.path);
        await mkdir(path.dirname(destination), { recursive: true });
        await writeFile(destination, await readFile(path.join(appRoot, item.path)), { flag: 'wx' });
      }
      await verifyDist(path.join(temporary, 'dist'), records);
      await writeFile(path.join(temporary, 'provenance.json'), JSON.stringify({ kind: 'exact-recovered-release',
        productVersion: packageMetadata.version, source: 'docs/recovery-0.1.22/recovery-manifest.json',
        frontendSourceVersion: '0.1.18', files: records.length }, null, 2) + '\n');
      await rename(temporary, target);
    } finally { await rm(temporary, { recursive: true, force: true }); }
  }
  return { status: 'CLEAN_PASS', productVersion: packageMetadata.version, source: 'exact-recovered-release',
    frontendSourceVersion: '0.1.18', files: records.length, formulaFiles, reused, target };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { console.log(JSON.stringify(await stageRecoveredFrontend(path.resolve(fileURLToPath(new URL('..', import.meta.url)))), null, 2)); }
  catch (error) { console.log(JSON.stringify({ status: 'BLOCKED', errors: [error.message] }, null, 2)); process.exitCode = 1; }
}
