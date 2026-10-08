import net from 'node:net';

// These probes are intentionally short-lived. The real child process binds
// the selected port immediately afterwards; the main-process identity check
// below prevents a race from ever being mistaken for the web service.
export function canBindLocalPort(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    let settled = false;
    const finish = (value) => {
      if (settled) return;
      settled = true;
      resolve(value);
    };
    server.unref();
    server.once('error', () => finish(false));
    server.listen({ host: '127.0.0.1', port }, () => {
      const address = server.address();
      const actualPort = address && typeof address === 'object' ? address.port : 0;
      server.close(() => finish(actualPort || false));
    });
  });
}

export async function findFreePort(preferred, { avoid = [], attempts = 48 } = {}) {
  const blocked = new Set(avoid.map((port) => Number(port)));
  for (let offset = 0; offset < attempts; offset += 1) {
    const candidate = Number(preferred) + offset;
    if (!candidate || candidate > 65535 || blocked.has(candidate)) continue;
    const available = await canBindLocalPort(candidate);
    if (available) return Number(available);
  }
  const fallback = await canBindLocalPort(0);
  if (fallback) return Number(fallback);
  throw new Error(`无法为桌面运行时分配本地端口（首选 ${preferred}）`);
}
