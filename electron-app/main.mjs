import { app, BrowserWindow, dialog, ipcMain, shell } from 'electron';
import { execFileSync, spawn } from 'node:child_process';
import { appendFileSync, copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, renameSync, statSync, unlinkSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { findFreePort } from './runtime-ports.mjs';
import { selectTdxRoot } from './tdx-root.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(here, '..');
const packaged = app.isPackaged;
const isolatedDesktopTest = !packaged && process.env.ZHANGCAI_DESKTOP_TEST === '1';
const resourceRoot = packaged ? path.join(process.resourcesPath, 'app') : projectRoot;
const runtimeRoot = packaged ? path.join(process.resourcesPath, 'runtime') : path.join(projectRoot, '.runtime');
const packagedInstallRoot = packaged ? path.dirname(process.execPath) : projectRoot;

function canWriteDirectory(directory) {
  try {
    mkdirSync(directory, { recursive: true });
    const probe = path.join(directory, `.write-probe-${process.pid}-${Date.now()}`);
    writeFileSync(probe, 'ok');
    unlinkSync(probe);
    return true;
  } catch {
    return false;
  }
}

function selectPackagedDataRoot() {
  // Prefer the user-selected installation drive. A per-machine install under
  // Program Files is commonly not writable by a standard Windows account, so
  // fall back only in that case. This keeps a writable D: install local while
  // still allowing a whiteboard machine to launch without elevation.
  const besideExe = path.join(packagedInstallRoot, 'data');
  if (canWriteDirectory(besideExe)) return besideExe;
  const localBase = process.env.LOCALAPPDATA
    || path.join(process.env.USERPROFILE || '.', 'AppData', 'Local');
  const fallback = path.join(localBase, '掌财桌面端', 'data');
  if (canWriteDirectory(fallback)) return fallback;
  return besideExe;
}

// A packaged desktop installation is self-contained at the user-selected
// install root whenever Windows permissions allow it. Test runs can still
// override the data roots through the environment below.
const packagedDataRoot = packaged ? selectPackagedDataRoot() : '';
if (packaged) {
  app.setPath('userData', path.join(packagedDataRoot, 'electron-user-data'));
  app.setPath('logs', path.join(packagedDataRoot, 'logs'));
}
const localDataBase = process.env.LOCALAPPDATA || app.getPath('userData');
const userDataRoot = packaged ? packagedDataRoot : path.join(localDataBase, '掌财智能体-4319');
const embeddedResourceLibraryRoot = packaged
  ? path.join(process.resourcesPath, 'resource-library')
  : path.join(projectRoot, 'electron-app', 'resource-library');
const resourceLibraryRoot = path.resolve(
  process.env.ZHANGCAI_RESOURCE_LIBRARY || (packaged ? path.join(userDataRoot, 'resource-library') : path.join(projectRoot, 'app-data')),
);
const dataRoot = path.resolve(process.env.ZHANGCAI_DATA_DIR || resourceLibraryRoot);
const logRoot = path.join(dataRoot, 'logs');
const desktopStateRoot = path.join(dataRoot, 'desktop');
const lastPageFile = path.join(desktopStateRoot, 'last-page.json');
const runtimeStateFile = path.join(desktopStateRoot, 'runtime.json');
const children = new Set();
const webPorts = new Set([3003, 3004, 4319]);
const runtimePorts = {
  ui: packaged || isolatedDesktopTest ? Number(process.env.ZHANGCAI_UI_PORT || 34303) : 3003,
  bridge: packaged || isolatedDesktopTest ? Number(process.env.ZHANGCAI_BRIDGE_PORT || 44319) : 4319,
};
const configuredBridgeStartTimeoutMs = Number(process.env.ZHANGCAI_BRIDGE_START_TIMEOUT_MS || 90000);
const configuredUiStartTimeoutMs = Number(process.env.ZHANGCAI_UI_START_TIMEOUT_MS || 180000);
const bridgeStartTimeoutMs = Number.isFinite(configuredBridgeStartTimeoutMs) && configuredBridgeStartTimeoutMs > 0
  ? configuredBridgeStartTimeoutMs : 90000;
const uiStartTimeoutMs = Number.isFinite(configuredUiStartTimeoutMs) && configuredUiStartTimeoutMs > 0
  ? configuredUiStartTimeoutMs : 180000;
let mainWindow;
let quitting = false;
let runtimeFailureShown = false;

function appendRuntimeLog(label, chunk) {
  try {
    mkdirSync(logRoot, { recursive: true });
    const log = path.join(logRoot, `${label}.log`);
    if (existsSync(log) && statSync(log).size > 2 * 1024 * 1024) renameSync(log, `${log}.previous`);
    const text = String(chunk).replace(/sk-[A-Za-z0-9_-]{8,}/g, '[REDACTED]');
    appendFileSync(log, text.slice(-16000));
  } catch { /* Logging must not stop the desktop shell. */ }
}
const hasSingleInstanceLock = app.requestSingleInstanceLock();
if (!hasSingleInstanceLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (!mainWindow) return;
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.show();
    mainWindow.focus();
  });
}

function configuredTdxRoot() {
  if (process.platform !== 'win32') return '';
  const configuredRoots = [];
  const addRoot = (value) => {
    const root = String(value || '').trim();
    if (root && !configuredRoots.some((existing) => existing.toLocaleLowerCase('en-US') === root.toLocaleLowerCase('en-US'))) {
      configuredRoots.push(root);
    }
  };
  addRoot(process.env.ZHANGCAI_TDX_ROOT);
  let registryRoot = '';
  try {
    const output = execFileSync('reg.exe', [
      'query',
      'HKCU\\Software\\Zhangcai\\Agent4319',
      '/v',
      'TDXRoot',
    ], { encoding: 'utf8', windowsHide: true, stdio: ['ignore', 'pipe', 'ignore'] });
    const line = output.split(/\r?\n/).find((item) => /\bTDXRoot\b/i.test(item));
    const match = line?.match(/\bTDXRoot\b\s+REG_\w+\s+(.+)$/i);
    if (match?.[1]) registryRoot = match[1].trim();
  } catch {
    // The installer may not have written the value yet; the bridge will expose
    // an unavailable TDX source instead of making the desktop process fail.
  }
  const savedConfig = path.join(desktopStateRoot, 'tdx-config.json');
  const installerConfig = path.join(desktopStateRoot, 'installer.ini');
  let savedRoot = '';
  let installerRoot = '';
  try {
    if (existsSync(installerConfig)) {
      const bytes = readFileSync(installerConfig);
      const text = bytes.toString(bytes[0] === 0xff && bytes[1] === 0xfe ? 'utf16le' : 'utf8');
      installerRoot = /^Root=(.*)$/m.exec(text)?.[1]?.trim() || '';
    }
  } catch { /* Continue with saved config and registry values. */ }
  try {
    const config = JSON.parse(readFileSync(savedConfig, 'utf8'));
    savedRoot = typeof config?.root === 'string' ? config.root.trim() : '';
  } catch { /* A config file is optional. */ }
  let installerIsNewer = Boolean(installerRoot && !savedRoot);
  try {
    if (installerRoot && savedRoot && existsSync(installerConfig) && existsSync(savedConfig)) {
      installerIsNewer = statSync(installerConfig).mtimeMs > statSync(savedConfig).mtimeMs;
    }
  } catch { /* Keep the saved configuration order if timestamps are unreadable. */ }
  if (installerIsNewer) {
    addRoot(installerRoot);
    addRoot(savedRoot);
  } else {
    addRoot(savedRoot);
    addRoot(installerRoot);
  }
  addRoot(registryRoot);

  return selectTdxRoot({
    configuredRoots,
    runningRoots: detectRunningTdxRoots(),
    isValidRoot: isValidTdxRoot,
  });
}

let tdxRoot = configuredTdxRoot();

function isValidTdxRoot(root) {
  if (!root || process.platform !== 'win32') return false;
  const resolved = path.resolve(root);
  return existsSync(path.join(resolved, 'vipdoc')) || existsSync(path.join(resolved, 'T0002'));
}

function detectRunningTdxRoots() {
  if (process.platform !== 'win32') return [];
  try {
    const output = execFileSync('powershell.exe', [
      '-NoProfile',
      '-NonInteractive',
      '-ExecutionPolicy',
      'Bypass',
      '-Command',
      "$rows = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(TdxW|tdx|new_tdx_mock)\.exe$' -and $_.ExecutablePath } | Select-Object Name,ExecutablePath,CreationDate | Sort-Object CreationDate -Descending); ConvertTo-Json -InputObject $rows -Compress",
    ], { encoding: 'utf8', windowsHide: true, stdio: ['ignore', 'pipe', 'ignore'], timeout: 10000 });
    const text = String(output || '').trim();
    if (!text) return [];
    const parsed = JSON.parse(text);
    const rows = Array.isArray(parsed) ? parsed : [parsed];
    const roots = [];
    for (const row of rows) {
      let candidate = path.dirname(String(row?.ExecutablePath || ''));
      for (let depth = 0; candidate && depth < 8; depth += 1) {
        if (isValidTdxRoot(candidate)) {
          roots.push(candidate);
          break;
        }
        const parent = path.dirname(candidate);
        if (parent === candidate) break;
        candidate = parent;
      }
    }
    return roots;
  } catch {
    return [];
  }
}

function persistTdxConfig(source = 'registry') {
  try {
    mkdirSync(desktopStateRoot, { recursive: true });
    writeFileSync(path.join(desktopStateRoot, 'tdx-config.json'), JSON.stringify({
      schema: 'ZHANGCAI_DESKTOP_TDX_CONFIG_V1',
      root: tdxRoot,
      source,
      updatedAt: new Date().toISOString(),
    }, null, 2));
  } catch (error) {
    console.warn(`[desktop] 无法写入通达信配置：${error instanceof Error ? error.message : String(error)}`);
  }
}

function writeTdxRegistry(root) {
  if (process.platform !== 'win32') throw new Error('桌面端通达信目录设置仅支持 Windows。');
  execFileSync('reg.exe', [
    'add',
    'HKCU\\Software\\Zhangcai\\Agent4319',
    '/v',
    'TDXRoot',
    '/t',
    'REG_SZ',
    '/d',
    root,
    '/f',
  ], { encoding: 'utf8', windowsHide: true });
}

function validateSender(event) {
  if (event.sender !== mainWindow?.webContents || event.senderFrame !== mainWindow.webContents.mainFrame
      || !isDesktopUrl(event.senderFrame.url)) throw new Error('拒绝来自非桌面页面的操作。');
}

function isDesktopUrl(url) {
  try { return new URL(url).origin === `http://127.0.0.1:${runtimePorts.ui}`; } catch { return false; }
}

ipcMain.handle('tdx:choose-directory', async (event) => {
  validateSender(event);
  const result = await dialog.showOpenDialog(mainWindow, {
    title: '选择通达信安装目录',
    defaultPath: tdxRoot || undefined,
    properties: ['openDirectory'],
  });
  if (result.canceled || !result.filePaths[0]) return { status: 'cancelled' };
  const selected = path.resolve(result.filePaths[0]);
  if (!isValidTdxRoot(selected)) {
    return {
      status: 'invalid',
      error: '所选目录未发现 vipdoc 或 T0002 子目录，请选择通达信安装目录。',
    };
  }
  try {
    writeTdxRegistry(selected);
    tdxRoot = selected;
    persistTdxConfig('desktop-ui');
    writeRuntimeState();
    return { status: 'saved', path: selected, restartRequired: true };
  } catch (error) {
    return {
      status: 'error',
      error: `通达信目录保存失败：${error instanceof Error ? error.message : String(error)}`,
    };
  }
});

ipcMain.handle('desktop:restart', (event) => {
  validateSender(event);
  app.relaunch();
  setTimeout(() => app.quit(), 100);
  return { status: 'restarting' };
});

ipcMain.handle('desktop:open-external', async (event, url) => {
  validateSender(event);
  if (url !== 'https://data.tdx.com.cn/mock/new_tdx_mock.exe') {
    throw new Error('只允许打开通达信 Mock 下载地址。');
  }
  await shell.openExternal(url);
  return { status: 'opened' };
});

function requireFile(target, label) {
  if (!existsSync(target)) throw new Error(`缺少${label}：${target}`);
  return target;
}

function copyMissingTree(sourceRoot, targetRoot) {
  if (!existsSync(sourceRoot)) return 0;
  mkdirSync(targetRoot, { recursive: true });
  let copied = 0;
  for (const entry of readdirSync(sourceRoot, { withFileTypes: true })) {
    const source = path.join(sourceRoot, entry.name);
    const target = path.join(targetRoot, entry.name);
    if (entry.isDirectory()) {
      copied += copyMissingTree(source, target);
    } else if (entry.isFile() && !existsSync(target)) {
      copyFileSync(source, target);
      copied += 1;
    }
  }
  return copied;
}

function ensureResourceLibrary() {
  mkdirSync(resourceLibraryRoot, { recursive: true });
  const seedManifest = path.join(embeddedResourceLibraryRoot, 'manifest.json');
  const targetManifest = path.join(resourceLibraryRoot, 'manifest.json');
  if (packaged && seedManifest !== targetManifest && existsSync(seedManifest) && !existsSync(targetManifest)) {
    copyFileSync(seedManifest, targetManifest);
  }
  // The main installer carries the small portable TQ formula source archive,
  // but not historical daily data. Merge only missing formula files into the
  // writable library so a data-pack install or a user-generated receipt is
  // never overwritten by an EXE upgrade.
  if (packaged) {
    copyMissingTree(
      path.join(embeddedResourceLibraryRoot, 'evidence', 'formulas', 'package'),
      path.join(resourceLibraryRoot, 'evidence', 'formulas', 'package'),
    );
  }
  persistTdxConfig(tdxRoot ? 'configured-or-running-client' : 'not-configured');
}

function startChild(label, command, args, extraEnv = {}) {
  const child = spawn(command, args, {
    cwd: resourceRoot,
    env: {
      ...process.env,
      ZHANGCAI_PACKAGED: packaged ? '1' : '0',
      ZHANGCAI_DATA_POLICY: packaged ? 'local_first_on_demand' : (process.env.ZHANGCAI_DATA_POLICY || ''),
      ZHANGCAI_APP_ROOT: resourceRoot,
      ZHANGCAI_DATA_DIR: dataRoot,
      ZHANGCAI_RESOURCE_LIBRARY: resourceLibraryRoot,
      ZHANGCAI_HOST: '127.0.0.1',
      // Preserve an explicitly empty packaged value so child scripts do not
      // silently fall back to the development C:\new_tdx_mock path.
      ...(packaged ? { ZHANGCAI_TDX_ROOT: tdxRoot } : (tdxRoot ? { ZHANGCAI_TDX_ROOT: tdxRoot } : {})),
      ...extraEnv,
    },
    windowsHide: true,
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  children.add(child);
  const record = (chunk) => appendRuntimeLog(label, chunk);
  child.stdout?.on('data', record);
  child.stderr?.on('data', record);
  child.once('exit', (code, signal) => {
    children.delete(child);
    record(`\nService exited: ${code ?? signal}\n`);
    if (!quitting && mainWindow && !runtimeFailureShown) {
      runtimeFailureShown = true;
      void dialog.showMessageBox(mainWindow, {
        type: 'error', title: '本地服务已停止',
        message: '本地服务意外退出，当前操作可能尚未完成。',
        detail: `日志已保存至 ${logRoot}。重启后可查看任务状态。`,
        buttons: ['重启客户端', '退出'], defaultId: 0, cancelId: 1,
      }).then(({ response }) => { if (response === 0) app.relaunch(); app.quit(); });
    }
  });
  child.once('error', (error) => record(error.message));
  return child;
}

async function waitForHttp(url, { label, child, validate, timeoutMs = 45000 } = {}) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (child?.exitCode !== null && child?.exitCode !== undefined) {
      throw new Error(`${label || '本地服务'}提前退出，退出码：${child.exitCode}`);
    }
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(Math.max(1, Math.min(3000, deadline - Date.now()))) });
      if (response.ok) {
        const body = await response.text();
        let parsed = body;
        try { parsed = JSON.parse(body); } catch { /* UI route returns HTML. */ }
        const identityError = validate?.(parsed);
        if (identityError) {
          const error = new Error(identityError);
          error.name = 'ServiceIdentityError';
          throw error;
        }
        return parsed;
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'ServiceIdentityError') throw error;
      // The child process may still be starting or the socket may have just
      // been released by a previous process.
    }
    await new Promise((resolve) => setTimeout(resolve, 350));
  }
  throw new Error(`等待${label || '本地服务'}超时：${url}`);
}

function stopChildren() {
  for (const child of children) {
    if (child.exitCode !== null || !child.pid) continue;
    try {
      if (process.platform === 'win32') {
        execFileSync('taskkill.exe', ['/PID', String(child.pid), '/T', '/F'], { windowsHide: true, timeout: 10000, stdio: 'ignore' });
      } else child.kill('SIGTERM');
    } catch { /* A child may have exited between the check and taskkill. */ }
  }
  children.clear();
}

function readLastPage() {
  try {
    const value = JSON.parse(readFileSync(lastPageFile, 'utf8'));
    return value?.path === '/chat' ? '/chat' : '/';
  } catch {
    return '/';
  }
}

function rememberPage(url) {
  if (!packaged || !runtimePorts.ui) return;
  try {
    const parsed = new URL(url);
    if (parsed.hostname !== '127.0.0.1' || Number(parsed.port) !== runtimePorts.ui) return;
    const page = parsed.pathname === '/chat' ? '/chat' : parsed.pathname === '/' ? '/' : '';
    if (!page) return;
    mkdirSync(desktopStateRoot, { recursive: true });
    writeFileSync(lastPageFile, JSON.stringify({ schema: 'ZHANGCAI_DESKTOP_LAST_PAGE_V1', path: page, updatedAt: new Date().toISOString() }, null, 2));
  } catch {
    // A navigation event must never interrupt the renderer.
  }
}

function buildUiUrl(page) {
  const target = new URL(page === '/chat' ? '/chat' : '/', `http://127.0.0.1:${runtimePorts.ui}`);
  if (packaged || isolatedDesktopTest) {
    target.searchParams.set('desktop', '1');
    target.searchParams.set('bridge', `http://127.0.0.1:${runtimePorts.bridge}`);
  }
  return target.toString();
}

function writeRuntimeState(extra = {}) {
  try {
    mkdirSync(desktopStateRoot, { recursive: true });
    writeFileSync(runtimeStateFile, JSON.stringify({
      schema: 'ZHANGCAI_DESKTOP_RUNTIME_V1',
      pid: process.pid,
      packaged,
      uiPort: runtimePorts.ui,
      bridgePort: runtimePorts.bridge,
      uiUrl: buildUiUrl('/'),
      bridgeUrl: `http://127.0.0.1:${runtimePorts.bridge}`,
       resourceRoot,
       dataRoot,
       resourceLibraryRoot,
       embeddedCodeRoot: resourceRoot,
       codePolicy: packaged ? 'embedded-in-exe-resources' : 'workspace',
      tdxRoot,
      updatedAt: new Date().toISOString(),
      ...extra,
    }, null, 2));
  } catch (error) {
    console.warn(`[desktop] 无法写入运行时状态：${error instanceof Error ? error.message : String(error)}`);
  }
}

async function startRuntime() {
  ensureResourceLibrary();
  mkdirSync(logRoot, { recursive: true });
  const node = requireFile(path.join(runtimeRoot, 'node', 'node.exe'), '程序内 Node');
  const python = requireFile(path.join(runtimeRoot, 'python', 'python.exe'), '程序内 Python');
  const bridge = requireFile(path.join(resourceRoot, 'agent-server.mjs'), '本地桥接入口');
  const vinext = requireFile(path.join(resourceRoot, 'node_modules', 'vinext', 'dist', 'cli.js'), 'Vinext CLI');
  const harnessEntry = path.join(packaged ? process.resourcesPath : projectRoot, 'deepseek-harness', 'lib', 'bin.js');
  if (packaged) requireFile(harnessEntry, '内置 DeepSeek Harness');
  const dshEnv = existsSync(harnessEntry) ? { DSH_ENTRY: harnessEntry, DSH_NODE: node } : {};

  if (packaged || isolatedDesktopTest) {
    runtimePorts.bridge = await findFreePort(44319, { avoid: [...webPorts] });
    runtimePorts.ui = await findFreePort(34303, { avoid: [...webPorts, runtimePorts.bridge] });
  }
  const bridgeUrl = `http://127.0.0.1:${runtimePorts.bridge}`;
  const bridgeChild = startChild('desktop-bridge', node, [bridge], {
    ZHANGCAI_BRIDGE_PORT: String(runtimePorts.bridge),
    ZHANGCAI_DESKTOP_ORIGIN: `http://127.0.0.1:${runtimePorts.ui}`,
    ZHANGCAI_PYTHON: python,
    DSH_HOME: path.join(dataRoot, 'harness'),
    ...dshEnv,
  });
  const uiChild = startChild('desktop-ui', node, [vinext, 'start', '--hostname', '127.0.0.1', '--port', String(runtimePorts.ui)], {
    ZHANGCAI_PYTHON: python,
    ZHANGCAI_BRIDGE_PORT: String(runtimePorts.bridge),
    ZHANGCAI_BRIDGE_URL: bridgeUrl,
    NEXT_PUBLIC_BRIDGE_URL: bridgeUrl,
  });

  await waitForHttp(`${bridgeUrl}/health`, {
    label: `桌面桥接 ${runtimePorts.bridge}`,
    child: bridgeChild,
    timeoutMs: bridgeStartTimeoutMs,
    validate: (body) => body?.status !== 'ok' || body?.appRoot !== resourceRoot || body?.dataRoot !== dataRoot || body?.resourceLibrary !== resourceLibraryRoot
      ? '检测到端口上的服务不属于当前 EXE，已拒绝启动以保护网页版数据。'
      : '',
  });
  await waitForHttp(`http://127.0.0.1:${runtimePorts.ui}/`, {
    label: `桌面页面 ${runtimePorts.ui}`,
    child: uiChild,
    timeoutMs: uiStartTimeoutMs,
    validate: (body) => typeof body === 'string' && /This page (?:couldn't|couldn’t|could not) load|createContext is not a function|Application error/i.test(body)
      ? '桌面页面返回了前端错误页；请查看 data\\logs\\desktop-ui.log。'
      : '',
  });
  writeRuntimeState();
}

async function createWindow() {
  await startRuntime();
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 1120,
    minHeight: 760,
    backgroundColor: '#fff8f9',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      preload: path.join(here, 'preload.cjs'),
    },
  });
  let rendererRuntimeError = '';
  mainWindow.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  mainWindow.webContents.on('will-navigate', (event, url) => { if (!isDesktopUrl(url)) event.preventDefault(); });
  mainWindow.webContents.on('did-navigate', (_event, url) => rememberPage(url));
  mainWindow.webContents.on('did-fail-load', (_event, errorCode, errorDescription, validatedURL, isMainFrame) => {
    if (isMainFrame) appendRuntimeLog('desktop-renderer', `did-fail-load ${errorCode} ${errorDescription} ${validatedURL}\n`);
  });
  mainWindow.webContents.on('console-message', (_event, level, message, line, sourceId) => {
    if (level >= 2) appendRuntimeLog('desktop-renderer', `console level=${level} ${sourceId}:${line} ${message}\n`);
    if (level >= 3 && /createContext is not a function|Calling `require` for|TypeError:|ReferenceError:|Minified React error #418|hydration|The above error occurred/i.test(message)) {
      rendererRuntimeError = message;
    }
  });
  mainWindow.webContents.on('render-process-gone', (_event, details) => {
    appendRuntimeLog('desktop-renderer', `render-process-gone reason=${details.reason} exitCode=${details.exitCode}\n`);
  });
  mainWindow.webContents.on('unresponsive', () => appendRuntimeLog('desktop-renderer', 'renderer became unresponsive\n'));
  // Program updates intentionally keep the same hashed asset names when the
  // low-memory client patch replaces a chunk. Clear Chromium's HTTP cache so
  // a previous 0.1.x renderer cannot combine an old client chunk with the new
  // framework shim. Local storage and the persisted last-page state remain.
  if (packaged || isolatedDesktopTest) await mainWindow.webContents.session.clearCache();
  await mainWindow.loadURL(buildUiUrl(readLastPage()));
  // React hydration errors can still leave the HTTP route at 200 while the
  // renderer shows a dead error page. Give hydration a short head start and
  // fail with a useful log path instead of exposing an unclickable shell.
  await new Promise((resolve) => setTimeout(resolve, 500));
  const pageHealth = await mainWindow.webContents.executeJavaScript(`(() => {
    const text = document.body?.innerText || '';
    const error = /This page (?:couldn't|couldn’t|could not) load|createContext is not a function|Application error/i.test(text);
    return { error, text: text.slice(0, 300) };
  })()`);
  if (rendererRuntimeError || pageHealth?.error) {
    const reason = rendererRuntimeError ? ` ${rendererRuntimeError}` : '';
    appendRuntimeLog('desktop-renderer', `page-health-error ${JSON.stringify(pageHealth)}${reason}\n`);
    throw new Error('桌面页面前端加载失败，请查看 data\\logs\\desktop-renderer.log。');
  }
  // Verify the privileged preload actually loaded, not just an HTTP 200 page.
  const desktopControlsReady = await mainWindow.webContents.executeJavaScript(
    "['chooseTdxDirectory','restart','openTdxDownload'].every(key => typeof window.zhangcaiDesktop?.[key] === 'function')",
  );
  if (!desktopControlsReady) throw new Error('桌面控制接口加载失败，请修复主程序安装。');
  writeRuntimeState({ desktopControlsReady });
  mainWindow.on('closed', () => { mainWindow = undefined; });
}

app.whenReady().then(async () => {
  if (!hasSingleInstanceLock) return;
  try {
    await createWindow();
  } catch (error) {
    stopChildren();
    await dialog.showMessageBox({
      type: 'error',
      title: '掌财桌面端启动失败',
      message: error instanceof Error ? error.message : String(error),
      detail: '桌面版使用独立端口和独立资源库；请检查程序运行时、专属桥接、Harness 凭据和数据目录配置。',
    });
    app.quit();
  }
});

app.on('before-quit', () => {
  if (quitting) return;
  quitting = true;
  stopChildren();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
