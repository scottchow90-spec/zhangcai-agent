import http from 'node:http';
import { spawn } from 'node:child_process';
import path from 'node:path';
import process from 'node:process';

const HOST = process.env.ZHANGCAI_HOST || '0.0.0.0';
const PORT = Number(process.env.STOCK_QUICK_PORT || 4320);
const APP_ROOT = path.resolve(process.env.ZHANGCAI_APP_ROOT || process.cwd());
const SKILL_ROOT = path.resolve(process.env.ZHANGCAI_SKILLS_DIR || path.join(APP_ROOT, 'harness-skills'));
const PYTHON = process.env.ZHANGCAI_PYTHON || process.env.TDX_PYTHON || 'python';
const TDX_ROOT = process.env.ZHANGCAI_TDX_ROOT || 'C:\\new_tdx_mock';
const HUB = path.join(SKILL_ROOT, 'tdx-local-hub', 'scripts', 'tdx_hub.py');

function headers(req) {
  const origin = req.headers.origin;
  return {
    'Access-Control-Allow-Origin': typeof origin === 'string' && /^https?:\/\/[^/]+:\d+$/.test(origin) ? origin : 'http://localhost:3001',
    'Access-Control-Allow-Methods': 'GET,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Private-Network': 'true',
    'Content-Type': 'application/json; charset=utf-8',
  };
}
function send(res, status, value) { res.writeHead(status, headers(res.req)); res.end(JSON.stringify(value)); }
function run(symbol) {
  return new Promise((resolve, reject) => {
    const started = Date.now();
    const child = spawn(PYTHON, [HUB, 'five', symbol], { cwd: TDX_ROOT, windowsHide: true });
    let stdout = ''; let stderr = '';
    const timer = setTimeout(() => { if (child.pid) spawn('taskkill', ['/pid', String(child.pid), '/t', '/f'], { windowsHide: true }); reject(new Error('本地五公式计算超时（30秒）')); }, 30000);
    child.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
    child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
    child.on('error', (error) => { clearTimeout(timer); reject(error); });
    child.on('close', (code) => {
      clearTimeout(timer);
      if (code !== 0) { reject(new Error((stderr || stdout || `退出码 ${code}`).trim().slice(-2000))); return; }
      try {
        const value = JSON.parse(stdout.trim());
        const items = Array.isArray(value.items) ? value.items : [];
        resolve({ status: value.ok && items.every((item) => item.ok) ? 'ok' : 'error', symbol, source: 'TDX tdx-local-hub / five', elapsed_ms: Date.now() - started, formulas: items.map((item) => ({ formula: item.formula, tq_formula: item.tq_formula, ok: item.ok, result: item.result?.[symbol] || {}, elapsed_ms: item.elapsed_ms })), failed_formulas: value.failed_formulas || [] });
      } catch { reject(new Error('五公式返回格式无效')); }
    });
  });
}

http.createServer(async (req, res) => {
  if (req.method === 'OPTIONS') { res.writeHead(204, headers(req)); res.end(); return; }
  if (req.method !== 'GET') { send(res, 405, { status: 'error', error: '仅支持 GET' }); return; }
  const url = new URL(req.url || '/', `http://${HOST}:${PORT}`);
  if (url.pathname === '/health') { send(res, 200, { status: 'ok', service: 'zhangcai-stock-quick', port: PORT }); return; }
  if (url.pathname !== '/stock/quick') { send(res, 404, { status: 'error', error: '路径不存在' }); return; }
  const raw = (url.searchParams.get('symbol') || '').trim().toUpperCase();
  if (!/^\d{6}\.(SH|SZ|BJ)$/.test(raw)) { send(res, 400, { status: 'error', error: '需要六位代码和市场后缀，例如 300959.SZ' }); return; }
  try { send(res, 200, await run(raw)); } catch (error) { send(res, 502, { status: 'error', error: error instanceof Error ? error.message : '本地公式计算失败' }); }
}).listen(PORT, HOST, () => console.log(`掌财智能体 quick stock bridge listening at http://${HOST}:${PORT}`));
