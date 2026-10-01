import { v as VINEXT_MOUNTED_SLOTS_HEADER } from "./headers-lNUsrpBT.js";
import { I as encodeCacheTag, Wt as resolveClientStaleTimeSeconds, a as applyCdnResponseHeaders, c as mergeMiddlewareResponseHeaders, d as VINEXT_RSC_CONTENT_TYPE, f as VINEXT_RSC_VARY_HEADER, m as applyRscDeploymentIdHeader, p as applyRscCompatibilityIdHeader, t as setCacheStateHeaders } from "./cache-headers-CBpU4sbE.js";
import { D as applyEdgeRuntimeHeader, E as applyClientStaleTimeHeader, O as buildAppPageCacheValue, _ as safeJsonStringify, f as hasCompleteNegativeRequestApiProof, k as isrCacheControl } from "../../index.js";
import { r as decideIsr, t as NAVIGATION_RUNTIME_SYMBOL_DESCRIPTION } from "./navigation-runtime-C2VuM21K.js";
new TextEncoder();
`${safeJsonStringify(NAVIGATION_RUNTIME_SYMBOL_DESCRIPTION)}`;
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-cache.js
function recordAppPageCacheOutcome(recordCacheOutcome, input) {
	try {
		recordCacheOutcome?.(input);
	} catch {}
}
function buildAppPageCacheTags(pathname, extraTags) {
	const tags = [
		pathname,
		`_N_T_${pathname.length > 1 && pathname.endsWith("/") ? pathname.slice(0, -1) : pathname}`,
		"_N_T_/layout"
	];
	const segments = pathname.split("/");
	let built = "";
	for (let index = 1; index < segments.length; index++) {
		const segment = segments[index];
		if (segment) {
			built += `/${segment}`;
			tags.push(`_N_T_${built}/layout`);
		}
	}
	tags.push(`_N_T_${built}/page`);
	for (const tag of extraTags) if (!tags.includes(tag)) tags.push(tag);
	return tags.map(encodeCacheTag);
}
function buildAppPageCachedHeaders(options) {
	const headers = new Headers({
		"Content-Type": options.contentType,
		Vary: VINEXT_RSC_VARY_HEADER
	});
	applyCdnResponseHeaders(headers, { cacheControl: options.cacheControl });
	setCacheStateHeaders(headers, options.cacheState);
	applyEdgeRuntimeHeader(headers, options.isEdgeRuntime);
	if (options.linkHeader) if (Array.isArray(options.linkHeader)) for (const value of options.linkHeader) headers.append("Link", value);
	else headers.set("Link", options.linkHeader);
	if (options.mountedSlotsHeader) headers.set(VINEXT_MOUNTED_SLOTS_HEADER, options.mountedSlotsHeader);
	applyClientStaleTimeHeader(headers, options.staleTimeSeconds);
	mergeMiddlewareResponseHeaders(headers, options.middlewareHeaders ?? null);
	return headers;
}
function getCachedAppPageValue(entry) {
	return entry?.value.value && entry.value.value.kind === "APP_PAGE" ? entry.value.value : null;
}
function hasQueryInvariantAppPageProof(cachedValue) {
	return cachedValue.renderObservation !== void 0 && hasCompleteNegativeRequestApiProof(cachedValue.renderObservation, ["searchParams"]);
}
function resolveRegeneratedAppPageCacheControl(options) {
	let revalidateSeconds = options.routeRevalidateSeconds;
	const renderRevalidateSeconds = options.renderCacheControl?.revalidate;
	if (typeof renderRevalidateSeconds === "number") revalidateSeconds = revalidateSeconds > 0 ? Math.min(revalidateSeconds, renderRevalidateSeconds) : renderRevalidateSeconds;
	return isrCacheControl(revalidateSeconds, {
		expireSeconds: options.renderCacheControl?.expire ?? options.expireSeconds,
		staleSeconds: resolveClientStaleTimeSeconds(options.renderCacheControl)
	});
}
function buildAppPageCachedResponse(cachedValue, options) {
	const status = options.middlewareStatus ?? (cachedValue.status || 200);
	const { cacheControl } = decideIsr({
		cacheState: options.cacheState,
		kind: "app-page",
		revalidateSeconds: options.revalidateSeconds,
		expireSeconds: options.expireSeconds,
		cacheControlMeta: options.cacheControl
	});
	const staleTimeSeconds = resolveClientStaleTimeSeconds(options.cacheControl);
	if (options.isRscRequest) {
		if (!cachedValue.rscData) return null;
		const rscHeaders = buildAppPageCachedHeaders({
			cacheControl,
			cacheState: options.cacheState,
			contentType: VINEXT_RSC_CONTENT_TYPE,
			isEdgeRuntime: options.isEdgeRuntime,
			middlewareHeaders: options.middlewareHeaders,
			mountedSlotsHeader: options.mountedSlotsHeader,
			staleTimeSeconds
		});
		applyRscCompatibilityIdHeader(rscHeaders);
		applyRscDeploymentIdHeader(rscHeaders);
		return new Response(cachedValue.rscData, {
			status,
			headers: rscHeaders
		});
	}
	if (typeof cachedValue.html !== "string" || cachedValue.html.length === 0) return null;
	const htmlHeaders = buildAppPageCachedHeaders({
		cacheControl,
		cacheState: options.cacheState,
		contentType: "text/html; charset=utf-8",
		isEdgeRuntime: options.isEdgeRuntime,
		linkHeader: cachedValue.headers?.link,
		middlewareHeaders: options.middlewareHeaders,
		staleTimeSeconds
	});
	return new Response(cachedValue.html, {
		status,
		headers: htmlHeaders
	});
}
async function readAppPageCacheResponse(options) {
	if (options.isRscRequest && options.mountedSlotsHeader) {
		options.isrDebug?.("MISS (mounted slots RSC variant)", options.cleanPathname);
		return null;
	}
	const isrKey = options.isRscRequest ? options.isrRscKey(options.cleanPathname, null, options.renderMode, options.interceptionContext) : options.isrHtmlKey(options.cleanPathname);
	const artifact = options.isRscRequest ? "rsc" : "html";
	try {
		const cached = await options.isrGet(isrKey);
		const cachedValue = getCachedAppPageValue(cached);
		if (cached?.isExpired) {
			recordAppPageCacheOutcome(options.recordCacheOutcome, {
				artifact,
				cacheKey: isrKey,
				outcome: "miss",
				reason: "expired"
			});
			options.isrDebug?.("MISS (expired)", options.cleanPathname);
			return null;
		}
		if (cached && !cachedValue) {
			recordAppPageCacheOutcome(options.recordCacheOutcome, {
				artifact,
				cacheKey: isrKey,
				outcome: "miss",
				reason: "non-app-page-entry"
			});
			options.isrDebug?.("MISS (non app-page cache entry)", options.cleanPathname);
			return null;
		}
		if (cachedValue && options.hasRequestSearchParams === true && !hasQueryInvariantAppPageProof(cachedValue)) {
			recordAppPageCacheOutcome(options.recordCacheOutcome, {
				artifact,
				cacheKey: isrKey,
				outcome: "miss",
				reason: "query-variant-unproven"
			});
			options.isrDebug?.("MISS (query-bearing request lacks cache proof)", options.cleanPathname);
			return null;
		}
		if (cachedValue && !cached?.isStale) {
			const hitResponse = buildAppPageCachedResponse(cachedValue, {
				cacheState: "HIT",
				cacheControl: cached?.value.cacheControl,
				expireSeconds: options.expireSeconds,
				isEdgeRuntime: options.isEdgeRuntime,
				isRscRequest: options.isRscRequest,
				middlewareHeaders: options.middlewareHeaders,
				middlewareStatus: options.middlewareStatus,
				mountedSlotsHeader: options.mountedSlotsHeader,
				revalidateSeconds: options.revalidateSeconds
			});
			if (hitResponse) {
				recordAppPageCacheOutcome(options.recordCacheOutcome, {
					artifact,
					cacheKey: isrKey,
					outcome: "hit",
					reason: "served"
				});
				options.isrDebug?.(options.isRscRequest ? "HIT (RSC)" : "HIT (HTML)", options.cleanPathname);
				options.clearRequestContext();
				return hitResponse;
			}
			recordAppPageCacheOutcome(options.recordCacheOutcome, {
				artifact,
				cacheKey: isrKey,
				outcome: "miss",
				reason: "empty-entry"
			});
			options.isrDebug?.("MISS (empty cached entry)", options.cleanPathname);
		}
		if (cached?.isStale && cachedValue) {
			options.scheduleBackgroundRegeneration(isrKey, async () => {
				const revalidatedPage = await options.renderFreshPageForCache();
				const cacheControl = resolveRegeneratedAppPageCacheControl({
					expireSeconds: options.expireSeconds,
					renderCacheControl: revalidatedPage.cacheControl,
					routeRevalidateSeconds: options.revalidateSeconds
				});
				const writes = [options.isrSet(options.isRscRequest ? isrKey : options.isrRscKey(options.cleanPathname, null, options.renderMode, options.interceptionContext), buildAppPageCacheValue("", revalidatedPage.rscData, 200, revalidatedPage.rscRenderObservation), {
					cacheControl,
					tags: revalidatedPage.tags
				})];
				if (!options.isRscRequest) writes.push(options.isrSet(isrKey, buildAppPageCacheValue(revalidatedPage.html, void 0, 200, revalidatedPage.htmlRenderObservation, revalidatedPage.linkHeader ? { link: revalidatedPage.linkHeader } : void 0), {
					cacheControl,
					tags: revalidatedPage.tags
				}));
				await Promise.all(writes);
				options.isrDebug?.("regen complete", options.cleanPathname);
			});
			const staleResponse = buildAppPageCachedResponse(cachedValue, {
				cacheState: "STALE",
				cacheControl: cached.value.cacheControl,
				expireSeconds: options.expireSeconds,
				isEdgeRuntime: options.isEdgeRuntime,
				isRscRequest: options.isRscRequest,
				middlewareHeaders: options.middlewareHeaders,
				middlewareStatus: options.middlewareStatus,
				mountedSlotsHeader: options.mountedSlotsHeader,
				revalidateSeconds: options.revalidateSeconds
			});
			if (staleResponse) {
				recordAppPageCacheOutcome(options.recordCacheOutcome, {
					artifact,
					cacheKey: isrKey,
					outcome: "stale",
					reason: "served"
				});
				options.isrDebug?.(options.isRscRequest ? "STALE (RSC)" : "STALE (HTML)", options.cleanPathname);
				options.clearRequestContext();
				return staleResponse;
			}
			recordAppPageCacheOutcome(options.recordCacheOutcome, {
				artifact,
				cacheKey: isrKey,
				outcome: "miss",
				reason: "stale-empty-entry"
			});
			options.isrDebug?.("STALE MISS (empty stale entry)", options.cleanPathname);
		}
		if (!cached) {
			recordAppPageCacheOutcome(options.recordCacheOutcome, {
				artifact,
				cacheKey: isrKey,
				outcome: "miss",
				reason: "no-entry"
			});
			options.isrDebug?.("MISS (no cache entry)", options.cleanPathname);
		}
	} catch (isrReadError) {
		recordAppPageCacheOutcome(options.recordCacheOutcome, {
			artifact,
			cacheKey: isrKey,
			outcome: "miss",
			reason: "read-error"
		});
		console.error("[vinext] ISR cache read error:", isrReadError);
	}
	return null;
}
//#endregion
export { buildAppPageCacheTags, readAppPageCacheResponse };
