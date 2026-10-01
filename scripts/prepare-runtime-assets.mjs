import { cpSync, existsSync, mkdirSync, readdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const appRoot = path.resolve(process.cwd());
const source = path.resolve(process.env.ZHANGCAI_SKILLS_SOURCE || path.join(appRoot, 'harness-skills'));
const destination = path.resolve(process.env.ZHANGCAI_SKILLS_DIR || path.join(appRoot, 'harness-skills'));

if (!existsSync(source)) throw new Error(`未找到迁移技能源：${source}`);
mkdirSync(destination, { recursive: true });
const names = readdirSync(source, { withFileTypes: true }).filter((entry) => entry.isDirectory()).map((entry) => entry.name).sort();
for (const name of names) cpSync(path.join(source, name), path.join(destination, name), { recursive: true, force: true });
writeFileSync(path.join(destination, 'runtime-manifest.json'), JSON.stringify({ schema: 'ZHANGCAI_RUNTIME_SKILLS_V1', preparedAt: new Date().toISOString(), skillCount: names.length, skills: names }, null, 2), 'utf8');
console.log(JSON.stringify({ status: 'ok', source, destination, skillCount: names.length }));
