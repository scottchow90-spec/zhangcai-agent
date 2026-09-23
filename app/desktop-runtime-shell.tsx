'use client';

import { useEffect, useState } from 'react';
import { Activity, CheckCircle2, Database, Home, MessageSquare, RefreshCw, X } from 'lucide-react';
import { bridgeUrl } from '@/lib/bridge-url';

type DesktopControlResult = { status?: string; path?: string; error?: string; restartRequired?: boolean };

declare global {
  interface Window {
    zhangcaiDesktop?: {
      chooseTdxDirectory: () => Promise<DesktopControlResult>;
      restart: () => Promise<DesktopControlResult>;
      openTdxDownload: () => Promise<DesktopControlResult>;
    };
  }
}

type EnvironmentSnapshot = {
  checkedAt?: string;
  bridge?: { status?: string; host?: string; port?: number };
  harness?: { status?: string; base?: string; credentialsConfigured?: boolean; credentialSource?: string; keyHint?: string };
  tdx?: { status?: string; root?: string };
  minuteData?: { status?: string; mode?: string; packaged?: boolean; fileCount?: number; reason?: string };
  daily?: { status?: string; date?: string };
  resourceLibrary?: { root?: string; writable?: boolean };
};

function uiUrl(pathname: '/' | '/chat') {
  const next = new URL(pathname, window.location.href);
  next.searchParams.set('desktop', '1');
  const bridge = new URLSearchParams(window.location.search).get('bridge');
  if (bridge) next.searchParams.set('bridge', bridge);
  return next.toString();
}

function resultMessage(body: Record<string, unknown>, fallback: string) {
  if (typeof body.message === 'string' && body.message) return body.message;
  if (typeof body.error === 'string' && body.error) return body.error;
  if (typeof body.status === 'string' && body.status) return `${fallback}：${body.status}`;
  return fallback;
}

function minuteDataLabel(value?: EnvironmentSnapshot['minuteData']) {
  if (!value || value.status === 'missing') return '未发现（普通任务不依赖）';
  if (value.status === 'available') return `外置按需（${value.fileCount || 0} 个）`;
  return value.status || '未知';
}

export default function DesktopRuntimeShell() {
  const [enabled, setEnabled] = useState(false);
  const [notice, setNotice] = useState('桌面运行时已隔离');
  const [environment, setEnvironment] = useState<EnvironmentSnapshot | null>(null);
  const [busy, setBusy] = useState('');
  const [credentialInput, setCredentialInput] = useState('');

  useEffect(() => {
    const desktop = new URLSearchParams(window.location.search).get('desktop') === '1';
    setEnabled(desktop);
  }, []);

  if (!enabled) return null;

  async function inspectEnvironment() {
    setBusy('environment');
    try {
      const response = await fetch(bridgeUrl('/runtime/environment'), { cache: 'no-store' });
      const body = await response.json().catch(() => ({})) as EnvironmentSnapshot & Record<string, unknown>;
      if (!response.ok) throw new Error(resultMessage(body, `运行环境检测失败（${response.status}）`));
      setEnvironment(body);
      setNotice('运行环境已检查');
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '运行环境检测失败');
    } finally {
      setBusy('');
    }
  }

  async function refreshMarket() {
    if (window.location.pathname === '/') {
      window.dispatchEvent(new CustomEvent('zhangcai:desktop-market-refresh'));
      setNotice('首页正在同步行情');
      return;
    }
    setBusy('market');
    try {
      const response = await fetch(bridgeUrl('/market?scope=indices'), { cache: 'no-store' });
      const body = await response.json().catch(() => ({})) as Record<string, unknown>;
      if (!response.ok) throw new Error(resultMessage(body, `行情同步失败（${response.status}）`));
      setNotice(resultMessage(body, '主要指数已同步'));
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '行情同步失败');
    } finally {
      setBusy('');
    }
  }

  async function openTdx() {
    setBusy('tdx');
    try {
      const response = await fetch(bridgeUrl('/runtime/tdx/open'), { method: 'POST' });
      const body = await response.json().catch(() => ({})) as Record<string, unknown>;
      if (!response.ok) throw new Error(resultMessage(body, `通达信启动失败（${response.status}）`));
      setNotice(resultMessage(body, '通达信启动请求已发送'));
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '通达信启动失败');
    } finally {
      setBusy('');
    }
  }

  async function chooseTdxDirectory() {
    const desktop = window.zhangcaiDesktop;
    if (!desktop) {
      setNotice('当前页面不是桌面端，无法打开目录选择器');
      return;
    }
    setBusy('tdx-directory');
    try {
      const result = await desktop.chooseTdxDirectory();
      if (result.status === 'cancelled') return;
      if (result.status !== 'saved') {
        setNotice(result.error || '通达信目录未保存');
        return;
      }
      setNotice(`通达信目录已保存：${result.path || ''}，正在重新启动桌面桥接…`);
      await desktop.restart();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '通达信目录设置失败');
    } finally {
      setBusy('');
    }
  }

  async function openTdxDownload() {
    try {
      await window.zhangcaiDesktop?.openTdxDownload();
      setNotice('已打开通达信 Mock 下载地址');
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '通达信下载地址打开失败');
    }
  }

  async function saveHarnessCredential() {
    const apiKey = credentialInput.trim();
    if (apiKey.length < 12) {
      setNotice('请输入有效的 DeepSeek API 密钥');
      return;
    }
    setBusy('credentials');
    try {
      const response = await fetch(bridgeUrl('/runtime/credentials'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ apiKey }),
      });
      const body = await response.json().catch(() => ({})) as Record<string, unknown>;
      if (!response.ok) throw new Error(resultMessage(body, `Harness 凭据保存失败（${response.status}）`));
      setCredentialInput('');
      setNotice('Harness 凭据已保存并生效');
      await inspectEnvironment();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Harness 凭据保存失败');
    } finally {
      setBusy('');
    }
  }

  return (
    <>
      <div className="desktop-runtime-spacer" aria-hidden="true" />
      <header className="desktop-runtime-shell" data-testid="desktop-runtime-shell">
        <div className="desktop-runtime-brand">
          <span className="desktop-runtime-mark" aria-label="掌财桌面端" />
          <b>掌财桌面端</b>
        </div>
        <nav className="desktop-runtime-nav" aria-label="桌面页面导航">
          <button type="button" onClick={() => { window.location.href = uiUrl('/'); }} className={window.location.pathname === '/' ? 'desktop-runtime-action is-active' : 'desktop-runtime-action'}>
            <Home size={14} />首页
          </button>
          <button type="button" onClick={() => { window.location.href = uiUrl('/chat'); }} className={window.location.pathname.startsWith('/chat') ? 'desktop-runtime-action is-chat-active' : 'desktop-runtime-action'}>
            <MessageSquare size={14} />聊天
          </button>
        </nav>
        <div className="desktop-runtime-tools">
          <button type="button" onClick={refreshMarket} disabled={Boolean(busy)} className="desktop-runtime-action">
            <RefreshCw size={14} className={busy === 'market' ? 'desktop-runtime-spin' : ''} />同步行情
          </button>
          <button type="button" onClick={openTdx} disabled={Boolean(busy)} className="desktop-runtime-action desktop-runtime-tdx">
            <Database size={14} />通达信
          </button>
          <button type="button" onClick={inspectEnvironment} disabled={Boolean(busy)} className="desktop-runtime-action">
            <Activity size={14} />运行环境
          </button>
        </div>
        <div className="desktop-runtime-status" title={notice}>
          <CheckCircle2 size={13} />
          <span>{notice}</span>
          <em>会话已持久化</em>
        </div>
      </header>
      {environment && (
        <aside className="desktop-runtime-panel" aria-label="桌面运行环境">
          <div className="desktop-runtime-panel-head">
            <b>桌面运行环境</b>
            <button type="button" onClick={() => setEnvironment(null)} aria-label="关闭运行环境"><X size={15} /></button>
          </div>
          <div className="desktop-runtime-panel-grid">
            <span>桥接端口</span><b>{environment.bridge?.port || '动态分配'}</b>
            <span>桥接状态</span><b>{environment.bridge?.status || '未知'}</b>
            <span>Harness</span><b>{environment.harness?.status || '未知'}</b>
            <span>通达信</span><b>{environment.tdx?.status || '未知'}</b>
            <span>TDX 目录</span><b title={environment.tdx?.root}>{environment.tdx?.root || '未设置'}</b>
            <span>5 分钟线</span><b title={environment.minuteData?.reason}>{minuteDataLabel(environment.minuteData)}</b>
            <span>行情日期</span><b>{environment.daily?.date || '等待刷新'}</b>
            <span>Harness 凭据</span><b>{environment.harness?.credentialsConfigured ? '已配置' : '未配置'}</b>
            <span>资源库</span><b title={environment.resourceLibrary?.root}>{environment.resourceLibrary?.writable ? '可写' : '未确认'}</b>
          </div>
          {!environment.harness?.credentialsConfigured && (
            <div className="desktop-runtime-credentials">
              <input
                type="password"
                value={credentialInput}
                onChange={(event) => setCredentialInput(event.target.value)}
                placeholder="输入 DeepSeek API 密钥"
                autoComplete="off"
                spellCheck={false}
              />
              <button type="button" onClick={() => void saveHarnessCredential()} disabled={busy === 'credentials'}>
                {busy === 'credentials' ? '保存中…' : '保存并启用'}
              </button>
            </div>
          )}
          <div className="desktop-runtime-settings">
            <button type="button" onClick={() => void chooseTdxDirectory()} disabled={Boolean(busy)}>
              设置通达信目录
            </button>
            <button type="button" onClick={() => void openTdxDownload()} disabled={Boolean(busy)}>
              下载 Mock
            </button>
          </div>
          <small>桌面版使用独立桥接和可写资源库，网页服务保持独立。</small>
        </aside>
      )}
    </>
  );
}
