/** Resolve the local Harness bridge from the browser's current host.
 *
 * Keeping the hostname dynamic lets a browser on another LAN machine call
 * the bridge on the same workstation instead of accidentally calling that
 * remote machine's own 127.0.0.1.
 */
export function bridgeUrl(path = ''): string {
  const suffix = path.startsWith('/') ? path : `/${path}`;
  // When the app is published through the remote /test2/ prefix, route the
  // browser back through Nginx and the SSH tunnel. A browser on another
  // computer cannot resolve its own 127.0.0.1 to the workstation running the
  // bridge service.
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search);
    const desktopMode = params.get('desktop') === '1';
    // Only the remote /test2 deployment is reverse-proxied through the
    // same-origin /test2/bridge prefix.  The local 3004 chat page also lives
    // at /chat, but its bridge is still the standalone 4319 service; treating
    // /chat as a published prefix sends preflight calls to 3004/chat/bridge/*
    // where no route exists and produces a misleading 404.
    const publishedPrefix = /^\/(test2)(?:\/|$)/.exec(window.location.pathname)?.[1];
    if (!desktopMode && publishedPrefix) return `/${publishedPrefix}/bridge${suffix}`;
  }
  // The packaged Electron host allocates an isolated bridge port at startup.
  // It passes that port in the private `bridge` query parameter so the static
  // client bundle never falls back to the web development bridge on 4319.
  if (typeof window !== 'undefined') {
    const configured = new URLSearchParams(window.location.search).get('bridge');
    if (configured) {
      try {
        const parsed = new URL(configured);
        const localHost = ['127.0.0.1', 'localhost'].includes(parsed.hostname);
        if (parsed.protocol === 'http:' && localHost && parsed.port) {
          return `${parsed.origin}${suffix}`;
        }
      } catch {
        // Ignore malformed runtime configuration and use the safe default.
      }
    }
  }
  // Vinext's development proxy is unavailable in production builds. The
  // worker remains loopback-only and the desktop host overrides this default
  // at runtime; the normal web application continues to use port 4319.
  const configured = process.env.NEXT_PUBLIC_BRIDGE_URL || process.env.ZHANGCAI_BRIDGE_URL;
  return `${configured || 'http://127.0.0.1:4319'}${suffix}`;
}

/**
 * Human-readable endpoint label for status panels and error messages.
 * The packaged desktop host passes its dynamically allocated bridge through
 * the private `bridge` query parameter; web development keeps the legacy 4319
 * default. Never expose credentials or the full URL in this label.
 */
export function bridgeHostLabel(): string {
  try {
    return new URL(bridgeUrl()).host;
  } catch {
    return '本地专属桥接';
  }
}

export function isDesktopRuntime(): boolean {
  return typeof window !== 'undefined'
    && new URLSearchParams(window.location.search).get('desktop') === '1';
}
