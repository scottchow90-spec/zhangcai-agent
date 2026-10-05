import { t as require_jsx_runtime_react_server } from "./framework~index~app-page-cache-render~app-page-cache~seed-cache~page~layout~page~app-route-~fe2f04fu-CQIcBs6F.js";
import { V as registerClientReference } from "../../index.js";
import path from "node:path";
import { existsSync, readFileSync } from "node:fs";
//#region app/home-client.tsx
var home_client_default = /* @__PURE__ */ registerClientReference(() => {
	throw new Error("Unexpectedly client reference export 'default' is called on server");
}, "0132a7525229", "default");
//#endregion
//#region app/page.tsx
var import_jsx_runtime_react_server = require_jsx_runtime_react_server();
var dynamic = "force-dynamic";
var revalidate = 0;
function readSupplementalSummary(dataRoot) {
	try {
		const publicPath = path.join(dataRoot, "public", "latest.json");
		const publicSnapshot = JSON.parse(readFileSync(publicPath, "utf8"));
		const date = String(publicSnapshot.date || "").replace(/\D/g, "").slice(0, 8);
		if (!/^\d{8}$/.test(date)) return void 0;
		const file = path.join(dataRoot, "evidence", "supplemental", date, "market.json");
		if (!existsSync(file)) return void 0;
		const snapshot = JSON.parse(readFileSync(file, "utf8"));
		const market = snapshot.market && typeof snapshot.market === "object" ? snapshot.market : {};
		const index = market.index_daily && typeof market.index_daily === "object" ? market.index_daily : {};
		const lhb = market.longhubang && typeof market.longhubang === "object" ? market.longhubang : {};
		const margin = market.margin && typeof market.margin === "object" ? market.margin : {};
		return {
			status: snapshot.status === "completed" ? "available" : String(snapshot.status || "available"),
			path: file,
			date: String(snapshot.trade_date || snapshot.requested_date || date),
			generatedAt: String(snapshot.generated_at || ""),
			coverage: snapshot.coverage && typeof snapshot.coverage === "object" ? snapshot.coverage : {},
			indexSymbolCount: Number(index.data?.symbol_count || 0),
			lhbRecordCount: Number(lhb.data?.record_count || 0),
			lhbMarketRecordCount: Number(lhb.data?.market_record_count || 0),
			marginRecordCount: Number(margin.data?.record_count || 0),
			marginExactDate: Number(margin.data?.exact_record_count || 0),
			marginLatestAvailableDate: String(margin.latest_available_date || "")
		};
	} catch {
		return;
	}
}
var EMPTY_MARKET = {
	date: "",
	total: 0,
	currentCount: 0,
	staleCount: 0,
	up: 0,
	down: 0,
	flat: 0,
	amount: 0,
	bins: [],
	importedAt: "",
	indices: [],
	stocks: [],
	allStocks: [],
	dataSources: {
		runtime: "local runtime/market-latest.json",
		status: "pending_refresh"
	}
};
function readInitialMarket() {
	const appRoot = process.env.ZHANGCAI_APP_ROOT || process.cwd();
	const dataRoot = path.resolve(process.env.ZHANGCAI_DATA_DIR || path.join(appRoot, "app-data"));
	const supplemental = readSupplementalSummary(dataRoot);
	const runtimePath = path.join(dataRoot, "runtime", "market-latest.json");
	if (!existsSync(runtimePath)) return supplemental ? {
		...EMPTY_MARKET,
		supplemental
	} : EMPTY_MARKET;
	try {
		const latest = JSON.parse(readFileSync(runtimePath, "utf8"));
		if (!latest || latest.status !== "ok") return supplemental ? {
			...EMPTY_MARKET,
			supplemental
		} : EMPTY_MARKET;
		const latestLight = { ...latest };
		delete latestLight.allStocks;
		const normalizeRows = (rows, limit = Number.POSITIVE_INFINITY, keepHistory = false) => Array.isArray(rows) ? rows.slice(0, limit).map((row) => {
			if (!row || typeof row !== "object") return row;
			const item = row;
			const history = keepHistory && Array.isArray(item.history) ? item.history.slice(-60) : [];
			return {
				...item,
				history
			};
		}) : [];
		return {
			...EMPTY_MARKET,
			...latestLight,
			indices: normalizeRows(latest.indices, 8, true),
			stocks: normalizeRows(latest.stocks, 120),
			allStocks: [],
			supplemental: supplemental || latest.supplemental
		};
	} catch {
		return supplemental ? {
			...EMPTY_MARKET,
			supplemental
		} : EMPTY_MARKET;
	}
}
function Page() {
	return /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(home_client_default, { initialMarket: readInitialMarket() });
}
//#endregion
export { Page as default, dynamic, revalidate };
