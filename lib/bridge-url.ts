/** Resolve the local Harness bridge from the browser's current host.
 *
 * Keeping the hostname dynamic lets a browser on another LAN machine call
 * the bridge on the same workstation instead of accidentally calling that
 * remote machine's own 127.0.0.1.
 */
export function bridgeUrl(path = ''): string {
  const suffix = path ? (path.startsWith('/') ? path : `/${path}`) : '';
  if (typeof window === 'undefined') return `http://127.0.0.1:4318${suffix}`;
  const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
  const host = window.location.hostname || '127.0.0.1';
  const pathname = window.location.pathname || '/';
  if (window.location.port === '8888' && (pathname === '/test' || pathname.startsWith('/test/'))) {
    return `${protocol}//${host}:8888/test/bridge${suffix}`;
  }
  return `${protocol}//${host}:4318${suffix}`;
}
