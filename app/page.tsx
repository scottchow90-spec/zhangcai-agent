import path from 'node:path';
import { existsSync, readFileSync } from 'node:fs';
import HomeClient, { type MarketShape } from './home-client';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

function readSupplementalSummary(dataRoot: string) {
  try {
    const publicPath = path.join(dataRoot, 'public', 'latest.json');
    const publicSnapshot = JSON.parse(readFileSync(publicPath, 'utf8')) as { date?: string };
    const date = String(publicSnapshot.date || '').replace(/\D/g, '').slice(0, 8);
    if (!/^\d{8}$/.test(date)) return undefined;
    const file = path.join(dataRoot, 'evidence', 'supplemental', date, 'market.json');
    if (!existsSync(file)) return undefined;
    const snapshot = JSON.parse(readFileSync(file, 'utf8')) as Record<string, unknown>;
    const market = (snapshot.market && typeof snapshot.market === 'object' ? snapshot.market : {}) as Record<string, any>;
    const index = (market.index_daily && typeof market.index_daily === 'object' ? market.index_daily : {}) as Record<string, any>;
    const lhb = (market.longhubang && typeof market.longhubang === 'object' ? market.longhubang : {}) as Record<string, any>;
    const margin = (market.margin && typeof market.margin === 'object' ? market.margin : {}) as Record<string, any>;
    return {
      status: snapshot.status === 'completed' ? 'available' : String(snapshot.status || 'available'),
      path: file,
      date: String(snapshot.trade_date || snapshot.requested_date || date),
      generatedAt: String(snapshot.generated_at || ''),
      coverage: (snapshot.coverage && typeof snapshot.coverage === 'object' ? snapshot.coverage : {}) as Record<string, boolean>,
      indexSymbolCount: Number(index.data?.symbol_count || 0),
      lhbRecordCount: Number(lhb.data?.record_count || 0),
      lhbMarketRecordCount: Number(lhb.data?.market_record_count || 0),
      marginRecordCount: Number(margin.data?.record_count || 0),
      marginExactDate: Number(margin.data?.exact_record_count || 0),
      marginLatestAvailableDate: String(margin.latest_available_date || ''),
    };
  } catch {
    return undefined;
  }
}

// The packaged UI must never present a stale seed snapshot as current market
// data. The server page only uses the local runtime snapshot; this
// empty shape keeps the shell renderable while the user starts a local refresh.
const EMPTY_MARKET: MarketShape = {
  date: '', total: 0, currentCount: 0, staleCount: 0, up: 0, down: 0, flat: 0,
  amount: 0, bins: [], importedAt: '', indices: [], stocks: [], allStocks: [],
  dataSources: { runtime: 'local runtime/market-latest.json', status: 'pending_refresh' },
};

// 页面只读取本应用程序包和本地运行目录；运行时数据与报告均由本地
// 网页脚本和 DeepSeek Harness 产生，不从其他网页实例回读，也不回退到
// 旧的打包行情样本。
function readInitialMarket(): MarketShape {
  const appRoot = process.env.ZHANGCAI_APP_ROOT || process.cwd();
  const dataRoot = path.resolve(process.env.ZHANGCAI_DATA_DIR || path.join(appRoot, 'app-data'));
  const supplemental = readSupplementalSummary(dataRoot);
  const runtimePath = path.join(dataRoot, 'runtime', 'market-latest.json');
  if (!existsSync(runtimePath)) return supplemental ? { ...EMPTY_MARKET, supplemental } : EMPTY_MARKET;
  try {
    const latest = JSON.parse(readFileSync(runtimePath, 'utf8')) as Partial<MarketShape>;
    if (!latest || latest.status !== 'ok') return supplemental ? { ...EMPTY_MARKET, supplemental } : EMPTY_MARKET;
    const latestLight = { ...latest };
    delete latestLight.allStocks;
    // Some runtime refreshes intentionally persist only the latest index bar.
    // Normalize sparse rows here so the page can render without requiring a
    // history array from every upstream source.
    const normalizeRows = (rows: unknown, limit = Number.POSITIVE_INFINITY, keepHistory = false) => Array.isArray(rows)
      ? rows.slice(0, limit).map((row) => {
          if (!row || typeof row !== 'object') return row;
          const item = row as Record<string, unknown>;
          // The browser fetches complete stock history through
          // /market/history after hydration.  Do not serialize every stock's
          // history into the SSR HTML: a full 5,000+ stock snapshot makes a
          // low-memory client spend its startup budget parsing data before
          // React can hydrate the page.
          const history = keepHistory && Array.isArray(item.history) ? item.history.slice(-60) : [];
          return { ...item, history };
        })
      : [];
    return {
      ...EMPTY_MARKET,
      ...latestLight,
      indices: normalizeRows(latest.indices, 8, true),
      // Keep only a small initial leaderboard.  The hydrated client restores
      // the complete universe from the local bridge, so this is a transport
      // optimization rather than a data reduction in the resource library.
      stocks: normalizeRows(latest.stocks, 120),
      // The public fallback is intentionally a homepage-only snapshot.  Do
      // not silently reattach the packaged 0908 universe after a fresh public
      // refresh, otherwise research pages would appear to have newer data
      // while still reading the old stock set.
      allStocks: [],
      supplemental: supplemental || (latest.supplemental as MarketShape['supplemental']),
    };
  } catch {
    return supplemental ? { ...EMPTY_MARKET, supplemental } : EMPTY_MARKET;
  }
}

export type { Board, IntradayProxy, Stock } from './home-client';

export default function Page() {
  return <HomeClient initialMarket={readInitialMarket()} />;
}
