// Newly authored release verification using the pinned upstream provider API.
import { createRequire } from 'node:module';
import { readFile, realpath } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const defaultAppRoot = path.resolve(fileURLToPath(new URL('../..', import.meta.url)));
export async function readJson(file) { return JSON.parse((await readFile(file, 'utf8')).replace(/^\uFEFF/, '')); }

export async function loadProvider(appRoot) {
  const dshRoot = path.resolve(process.env.ZHANGCAI_RELEASE_DSH_ROOT
    || path.join(appRoot, 'packaging/staging/desktop-runtime/deepseek-harness'));
  const require = createRequire(path.join(dshRoot, 'package.json'));
  const entry = require.resolve('@deepseek-ai/dsh-skill-filesystem');
  const metadata = await readJson(path.join(path.dirname(entry), '..', 'package.json'));
  if (metadata.version !== '0.1.2-rc.1') throw new Error(`Harness provider version must be 0.1.2-rc.1; got ${metadata.version}`);
  const { FileSystemSkillProvider } = await import(pathToFileURL(entry).href);
  if (typeof FileSystemSkillProvider !== 'function') throw new Error('Pinned Harness filesystem provider API is unavailable');
  return FileSystemSkillProvider;
}

export async function discover(FileSystemSkillProvider, root, expected) {
  const warnings = [];
  const abort = new AbortController();
  const provider = new FileSystemSkillProvider({ get: () => undefined, logger: { warn: (text) => warnings.push(String(text)) } },
    { signal: abort.signal, invalidate: () => {} },
    { includeDefaultRoots: false, bundledSkillDir: root, watch: false });
  try {
    const observation = await provider.list({});
    if (!Array.isArray(observation) && observation.complete !== true) throw new Error('Harness discovery was incomplete');
    const candidates = Array.isArray(observation) ? observation : observation.candidates;
    const found = [];
    for (const item of expected) {
      const expectedFile = await realpath(path.join(item.root, 'SKILL.md'));
      const matches = [];
      for (const candidate of candidates.filter((row) => row.name === item.name)) {
        if (await realpath(candidate.path) === expectedFile) matches.push(candidate);
      }
      if (matches.length !== 1) throw new Error(`Harness must discover exactly one ${item.name} at its prepared path`);
      const definition = await provider.get(matches[0], {});
      if (!definition?.description?.trim() || !definition?.content?.trim()
        || await realpath(definition.path) !== expectedFile) throw new Error(`Harness failed to load ${item.name}`);
      found.push(item.name);
    }
    return { found, warnings };
  } finally {
    await provider.dispose();
    abort.abort();
  }
}
