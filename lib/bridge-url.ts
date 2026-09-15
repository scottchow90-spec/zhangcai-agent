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
  if (typeof window !== 'undefined' && /^\/test2(?:\/|$)/.test(window.location.pathname)) {
    return `/test2/bridge${suffix}`;
  }
  // Vinext's development proxy is unavailable in production builds. The
  // worker remains loopback-only and whitelists port 3003 in CORS, so local
  // development and packaged production use the same private endpoint.
  if (typeof window !== 'undefined') return `http://127.0.0.1:4319${suffix}`;
  return `http://127.0.0.1:4319${suffix}`;
}
