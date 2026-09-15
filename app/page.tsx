import path from 'node:path';
import { existsSync, readFileSync } from 'node:fs';
import baselineMarket from '@/lib/market.json';
import HomeClient, { type MarketShape } from './home-client';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

function readInitialMarket(): MarketShape {
  const baseline = baselineMarket as unknown as MarketShape;
  const { allStocks: _baselineAllStocks, ...baselineLight } = baseline;
  const appRoot = process.env.ZHANGCAI_APP_ROOT || process.cwd();
  const runtimePath = path.join(appRoot, 'data', 'runtime', 'market-latest.json');
  if (!existsSync(runtimePath)) return baseline;
  try {
    const latest = JSON.parse(readFileSync(runtimePath, 'utf8')) as Partial<MarketShape>;
    if (!latest || latest.status !== 'ok') return baseline;
    const { allStocks: _latestAllStocks, ...latestLight } = latest;
    const incomingIndices = latest.indices || [];
    const incomingByCode = new Map(incomingIndices.map((row) => [row.code, row]));
    const mergedIndices = [
      ...baseline.indices.map((existing) => {
        const incoming = incomingByCode.get(existing.code);
        return incoming
          ? { ...existing, ...incoming, history: incoming.history?.length ? incoming.history : existing.history }
          : existing;
      }),
      ...incomingIndices.filter((row) => !baseline.indices.some((existing) => existing.code === row.code)),
    ];
    return {
      ...baselineLight,
      ...latestLight,
      indices: mergedIndices,
      stocks: latest.stocks?.length ? latest.stocks : baseline.stocks,
      allStocks: latest.allStocks?.length ? latest.allStocks.map((row) => ({ ...row, history: [] })) : undefined,
    };
  } catch {
    return baseline;
  }
}

export default function Page() {
  return <HomeClient initialMarket={readInitialMarket()} />;
}

