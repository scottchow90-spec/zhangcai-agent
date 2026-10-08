import { existsSync } from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';

export const runtime = 'nodejs';

let launchInProgress = false;

export async function POST() {
  const port = Number(process.env.ZHANGCAI_BRIDGE_PORT || 4319);
  // Electron owns both child processes in packaged mode. The web route must
  // not start a second development bridge or report the legacy 4319 port.
  if (process.env.ZHANGCAI_PACKAGED === '1') {
    return Response.json({ status: 'ready', packaged: true, port });
  }
  const appRoot = path.resolve(process.env.ZHANGCAI_APP_ROOT || process.cwd());
  const launcher = path.join(appRoot, 'scripts', 'start-local.ps1');
  if (!existsSync(launcher)) {
    return Response.json({ status: 'error', error: `本地启动脚本不存在：${launcher}` }, { status: 500 });
  }
  if (!launchInProgress) {
    launchInProgress = true;
    const child = spawn('powershell.exe', [
      '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', launcher,
    ], { cwd: appRoot, detached: true, windowsHide: true, stdio: 'ignore' });
    child.unref();
    setTimeout(() => { launchInProgress = false; }, 5000);
  }
  return Response.json({ status: 'starting', port, launcher: 'scripts/start-local.ps1' }, { status: 202 });
}
