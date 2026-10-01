import { r as __toESM } from "./rolldown-runtime-BT1X7o2_.js";
import { n as require_react_react_server, t as require_jsx_runtime_react_server } from "./framework~index~app-page-cache-render~app-page-cache~seed-cache~page~layout~page~app-route-~fe2f04fu-CQIcBs6F.js";
import { A as MIDDLEWARE_REQUEST_HEADER_PREFIX, B as isInsideUnifiedScope, T as VINEXT_RSC_RENDER_MODE_HEADER, U as runWithUnifiedStateMutation, W as getOrCreateAls, a as NEXTJS_CACHE_HEADER, c as NEXT_ROUTER_PREFETCH_HEADER, d as NEXT_ROUTER_STATE_TREE_HEADER, f as NEXT_URL_HEADER, g as VINEXT_INTERCEPTION_CONTEXT_HEADER, k as MIDDLEWARE_OVERRIDE_HEADERS, l as NEXT_ROUTER_SEGMENT_PREFETCH_HEADER, o as NEXTJS_DEPLOYMENT_ID_HEADER, p as VINEXT_CACHE_HEADER, q as isUnknownRecord, v as VINEXT_MOUNTED_SLOTS_HEADER, z as getRequestContext } from "./headers-lNUsrpBT.js";
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/cache-control-metadata.js
var import_react_react_server = /* @__PURE__ */ __toESM(require_react_react_server(), 1);
function readRecordField(ctx, field) {
	const value = ctx?.[field];
	return isUnknownRecord(value) ? value : void 0;
}
function readCacheControlNumberField(ctx, field) {
	const value = readRecordField(ctx, "cacheControl")?.[field] ?? ctx?.[field];
	return typeof value === "number" ? value : void 0;
}
function readCacheControlRevalidateField(ctx) {
	const value = readRecordField(ctx, "cacheControl")?.revalidate ?? ctx?.revalidate;
	return typeof value === "number" || value === false ? value : void 0;
}
function isFiniteNonNegative(value) {
	return typeof value === "number" && Number.isFinite(value) && value >= 0;
}
/**
* Client-reuse seconds from a resolved `cacheLife`. Shared by every emitter
* (ISR write, hit replay, prerender seed, done-script) so warm hits claim what
* the producing render claimed. Two rules: never synthesize `stale` from
* `revalidate`/`expire` (the `default` profile would license ~136y of reuse),
* and never clamp it by them (Next.js replays the stored value verbatim;
* `expire` is a serve-side ceiling, not a client bound). A literal `stale: 0`
* is still a real client claim; it must not be treated as absent.
*/
function resolveClientStaleTimeSeconds(cacheLife) {
	const stale = cacheLife?.stale;
	return isFiniteNonNegative(stale) ? stale : void 0;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/cache-handler.js
var DEFAULT_MEMORY_CACHE_MAX_SIZE = 50 * 1024 * 1024;
var MAX_REVALIDATED_TAG_ENTRIES = 1e4;
function estimateStringMapSize(map) {
	if (!map) return 0;
	let size = 0;
	for (const [key, value] of Object.entries(map)) {
		size += key.length;
		if (Array.isArray(value)) for (const item of value) size += item.length;
		else size += value.length;
	}
	return size;
}
function estimateIncrementalCacheValueSize(value) {
	if (value === null) return 25;
	switch (value.kind) {
		case "FETCH": return JSON.stringify(value.data ?? "").length;
		case "PAGES": return value.html.length + JSON.stringify(value.pageData ?? {}).length + estimateStringMapSize(value.headers);
		case "APP_PAGE": return value.html.length + (value.rscData?.byteLength ?? 0) + (value.postponed?.length ?? 0) + estimateStringMapSize(value.headers);
		case "APP_ROUTE": return value.body.byteLength + estimateStringMapSize(value.headers);
		case "REDIRECT": return JSON.stringify(value.props ?? {}).length;
		case "IMAGE": return value.buffer.byteLength + value.extension.length + value.etag.length;
		default: return JSON.stringify(value).length;
	}
}
function resolveMemoryCacheMaxSize(options) {
	if (typeof options === "number") return options;
	if (typeof options?.cacheMaxMemorySize === "number") return options.cacheMaxMemorySize;
	if (typeof options?.maxMemoryCacheSize === "number") return options.maxMemoryCacheSize;
	return DEFAULT_MEMORY_CACHE_MAX_SIZE;
}
function readStringArrayField(ctx, field) {
	const value = ctx?.[field];
	if (!Array.isArray(value)) return [];
	return value.filter((item) => typeof item === "string");
}
function readPositiveNumberField(ctx, field) {
	const value = ctx?.[field];
	return typeof value === "number" && value > 0 ? value : void 0;
}
var MemoryCacheHandler = class {
	store = /* @__PURE__ */ new Map();
	tagRevalidatedAt = /* @__PURE__ */ new Map();
	maxMemoryCacheSize;
	currentMemoryCacheSize = 0;
	constructor(options) {
		this.maxMemoryCacheSize = resolveMemoryCacheMaxSize(options);
	}
	estimateEntrySize(entry) {
		return estimateIncrementalCacheValueSize(entry.value) + entry.tags.reduce((sum, tag) => sum + tag.length, 0) + 64;
	}
	deleteEntry(key) {
		const existing = this.store.get(key);
		if (!existing) return;
		this.currentMemoryCacheSize -= this.estimateEntrySize(existing);
		this.store.delete(key);
	}
	touchEntry(key, entry) {
		this.store.delete(key);
		this.store.set(key, entry);
	}
	evictLeastRecentlyUsed() {
		while (this.maxMemoryCacheSize > 0 && this.currentMemoryCacheSize > this.maxMemoryCacheSize) {
			const oldestKey = this.store.keys().next().value;
			if (oldestKey === void 0) return;
			this.deleteEntry(oldestKey);
		}
	}
	async get(key, ctx) {
		const entry = this.store.get(key);
		if (!entry) return null;
		for (const tag of entry.tags) {
			const revalidatedAt = this.tagRevalidatedAt.get(tag);
			if (revalidatedAt && revalidatedAt >= entry.lastModified) {
				this.deleteEntry(key);
				return null;
			}
		}
		for (const tag of readStringArrayField(ctx, "softTags")) {
			const revalidatedAt = this.tagRevalidatedAt.get(tag);
			if (revalidatedAt && revalidatedAt >= entry.lastModified) return null;
		}
		this.touchEntry(key, entry);
		const now = Date.now();
		if (entry.expireAt !== null && now > entry.expireAt) return {
			lastModified: entry.lastModified,
			value: entry.value,
			cacheState: "expired",
			cacheControl: entry.cacheControl
		};
		const requestedRevalidate = readPositiveNumberField(ctx, "revalidate");
		const requestedRevalidateAt = requestedRevalidate === void 0 ? null : entry.lastModified + requestedRevalidate * 1e3;
		if (entry.revalidateAt !== null && now > entry.revalidateAt || requestedRevalidateAt !== null && now > requestedRevalidateAt) return {
			lastModified: entry.lastModified,
			value: entry.value,
			cacheState: "stale",
			cacheControl: entry.cacheControl
		};
		return {
			lastModified: entry.lastModified,
			value: entry.value,
			cacheControl: entry.cacheControl
		};
	}
	async set(key, data, ctx) {
		const tagSet = /* @__PURE__ */ new Set();
		if (data && "tags" in data && Array.isArray(data.tags)) for (const tag of data.tags) tagSet.add(tag);
		for (const tag of readStringArrayField(ctx, "tags")) tagSet.add(tag);
		const tags = [...tagSet];
		let effectiveRevalidate = readCacheControlRevalidateField(ctx);
		const effectiveExpire = readCacheControlNumberField(ctx, "expire");
		const effectiveStale = readCacheControlNumberField(ctx, "stale");
		if (data && "revalidate" in data && typeof data.revalidate === "number") effectiveRevalidate = data.revalidate;
		else if (data && "revalidate" in data && data.revalidate === false) effectiveRevalidate ??= false;
		if (effectiveRevalidate === 0) return;
		const now = Date.now();
		const revalidateAt = typeof effectiveRevalidate === "number" && effectiveRevalidate > 0 ? now + effectiveRevalidate * 1e3 : null;
		const expireAt = typeof effectiveExpire === "number" && effectiveExpire > 0 ? now + effectiveExpire * 1e3 : null;
		const cacheControl = typeof effectiveRevalidate === "number" || effectiveRevalidate === false ? {
			revalidate: effectiveRevalidate,
			...effectiveExpire === void 0 ? {} : { expire: effectiveExpire },
			...effectiveStale === void 0 ? {} : { stale: effectiveStale }
		} : void 0;
		if (this.maxMemoryCacheSize === 0) return;
		const entry = {
			value: data,
			tags,
			lastModified: now,
			revalidateAt,
			expireAt,
			cacheControl
		};
		const entrySize = this.estimateEntrySize(entry);
		if (entrySize > this.maxMemoryCacheSize) {
			this.deleteEntry(key);
			return;
		}
		this.deleteEntry(key);
		this.store.set(key, entry);
		this.currentMemoryCacheSize += entrySize;
		this.evictLeastRecentlyUsed();
	}
	async revalidateTag(tags) {
		const tagList = Array.isArray(tags) ? tags : [tags];
		const now = Date.now();
		for (const tag of tagList) {
			this.tagRevalidatedAt.set(tag, now);
			while (this.tagRevalidatedAt.size > MAX_REVALIDATED_TAG_ENTRIES) {
				const oldest = this.tagRevalidatedAt.keys().next().value;
				if (oldest === void 0) break;
				this.tagRevalidatedAt.delete(oldest);
			}
		}
	}
	resetRequestCache() {}
};
var HANDLER_KEY = Symbol.for("vinext.cacheHandler");
var globalHandlers = globalThis;
function getActiveHandler() {
	return globalHandlers[HANDLER_KEY] ?? (globalHandlers[HANDLER_KEY] = new MemoryCacheHandler());
}
function configureMemoryCacheHandler(options) {
	const current = globalHandlers[HANDLER_KEY];
	if (current && !(current instanceof MemoryCacheHandler)) return;
	globalHandlers[HANDLER_KEY] = new MemoryCacheHandler(options);
}
function getDataCacheHandler() {
	return getActiveHandler();
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/parse-cookie.js
function decodeCookieValue(value) {
	try {
		return {
			ok: true,
			value: decodeURIComponent(value)
		};
	} catch {
		return { ok: false };
	}
}
function forEachCookieHeaderPart(cookieHeader, visit) {
	for (const part of cookieHeader.split(/; */)) {
		if (!part) continue;
		visit(part, part.indexOf("="));
	}
}
/**
* Parse a Cookie header using the semantics of Next.js's compiled `cookie`
* package.
*/
function parseCookieHeader(cookieHeader) {
	const cookies = {};
	if (!cookieHeader) return cookies;
	forEachCookieHeaderPart(cookieHeader, (part, separator) => {
		if (separator < 0) return;
		const key = part.slice(0, separator).trim();
		let value = part.slice(separator + 1).trim();
		if (cookies[key] !== void 0) return;
		if (value.startsWith("\"")) value = value.slice(1, -1);
		const decoded = decodeCookieValue(value);
		cookies[key] = decoded.ok ? decoded.value : value;
	});
	return cookies;
}
/**
* Parse a Cookie header using Next.js/@edge-runtime RequestCookies semantics.
*/
function parseEdgeRequestCookieHeader(cookieHeader) {
	const cookies = /* @__PURE__ */ new Map();
	forEachCookieHeaderPart(cookieHeader, (part, separator) => {
		if (separator === -1) {
			cookies.set(part, "true");
			return;
		}
		const decoded = decodeCookieValue(part.slice(separator + 1));
		if (decoded.ok) cookies.set(part.slice(0, separator), decoded.value);
	});
	return cookies;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/middleware-request-headers.js
function getMiddlewareHeaderValue(source, key) {
	if (source instanceof Headers) return source.get(key);
	const value = source[key];
	if (value === void 0) return null;
	return Array.isArray(value) ? value[0] ?? null : value;
}
function parseOverrideHeaderNames(rawValue) {
	return rawValue.split(",").map((key) => key.trim()).filter(Boolean);
}
function getForwardedRequestHeaders(source) {
	const forwardedHeaders = /* @__PURE__ */ new Map();
	if (source instanceof Headers) {
		for (const [key, value] of source.entries()) if (key.startsWith("x-middleware-request-")) forwardedHeaders.set(key.slice(MIDDLEWARE_REQUEST_HEADER_PREFIX.length), value);
		return forwardedHeaders;
	}
	for (const [key, value] of Object.entries(source)) {
		if (!key.startsWith("x-middleware-request-")) continue;
		const normalizedValue = Array.isArray(value) ? value[0] ?? "" : value;
		forwardedHeaders.set(key.slice(MIDDLEWARE_REQUEST_HEADER_PREFIX.length), normalizedValue);
	}
	return forwardedHeaders;
}
/**
* Return truthy forwarded values that Next.js does not consume through the
* override list. Its subsequent generic middleware-header merge exposes these
* under their literal protocol-header names on both the request and response.
*/
function getUnconsumedMiddlewareRequestHeaders(source) {
	const rawOverrideHeader = getMiddlewareHeaderValue(source, MIDDLEWARE_OVERRIDE_HEADERS);
	const overriddenHeaders = rawOverrideHeader ? new Set(parseOverrideHeaderNames(rawOverrideHeader)) : null;
	const unconsumedHeaders = /* @__PURE__ */ new Map();
	for (const [key, value] of getForwardedRequestHeaders(source)) if (value && !overriddenHeaders?.has(key)) unconsumedHeaders.set(`${MIDDLEWARE_REQUEST_HEADER_PREFIX}${key}`, value);
	return unconsumedHeaders;
}
/**
* A non-empty `x-middleware-override-headers` value lists the complete
* post-middleware header set, so any name absent from it was deleted by
* middleware. Never re-add absent headers from the base request — that would
* resurrect credentials the app explicitly stripped before an external
* rewrite. Next.js treats the empty value emitted for `new Headers()` as no
* override. Any unconsumed `x-middleware-request-*` values are subsequently
* copied to the request under their literal protocol-header names.
*/
function buildRequestHeadersFromMiddlewareResponse(baseHeaders, middlewareHeaders) {
	const forwardedHeaders = getForwardedRequestHeaders(middlewareHeaders);
	const unconsumedHeaders = getUnconsumedMiddlewareRequestHeaders(middlewareHeaders);
	const rawOverrideHeader = getMiddlewareHeaderValue(middlewareHeaders, MIDDLEWARE_OVERRIDE_HEADERS);
	if (!rawOverrideHeader) {
		if (unconsumedHeaders.size === 0) return null;
		const nextHeaders = new Headers(baseHeaders);
		for (const [key, value] of unconsumedHeaders) nextHeaders.set(key, value);
		return nextHeaders;
	}
	const overrideHeaderNames = parseOverrideHeaderNames(rawOverrideHeader);
	const nextHeaders = new Headers();
	for (const key of overrideHeaderNames) {
		const value = forwardedHeaders.get(key);
		if (value !== void 0) nextHeaders.set(key, value);
	}
	for (const [key, value] of unconsumedHeaders) nextHeaders.set(key, value);
	return nextHeaders;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/internal/cookie-serialize.js
/**
* RFC 6265 §4.1.1: cookie-name is a token (RFC 2616 §2.2).
* Allowed: any visible ASCII (0x21-0x7E) except separators: ()<>@,;:\"/[]?={}
*/
var VALID_COOKIE_NAME_RE = /^[\x21\x23-\x27\x2A\x2B\x2D\x2E\x30-\x39\x41-\x5A\x5E-\x7A\x7C\x7E]+$/;
function validateCookieName(name) {
	if (!name || !VALID_COOKIE_NAME_RE.test(name)) throw new Error(`Invalid cookie name: ${JSON.stringify(name)}`);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/internal/make-hanging-promise.js
/**
* makeHangingPromise — returns a promise that never resolves during prerendering.
*
* When prerendering, `io()` must return a hanging promise to prevent
* React from executing past the IO boundary. The promise never resolves—it only
* rejects if the render signal is aborted (e.g., due to a dynamic error or
* cache-fill completion).
*
* Ported from Next.js: packages/next/src/server/dynamic-rendering-utils.ts
* https://github.com/vercel/next.js/blob/canary/packages/next/src/server/dynamic-rendering-utils.ts
*/
var HangingPromiseRejectionError = class extends Error {
	constructor(route, expression) {
		super(`Route ${route} used ${expression} during prerendering but the render was aborted. This is expected when prerendering is cut short (e.g. due to a dynamic access).`);
		this.name = "HangingPromiseRejectionError";
	}
};
var abortListenersBySignal = /* @__PURE__ */ new WeakMap();
function suppressUnhandledRejection() {}
function makeHangingPromise(signal, route, expression) {
	if (signal.aborted) {
		const rejected = Promise.reject(new HangingPromiseRejectionError(route, expression));
		rejected.catch(suppressUnhandledRejection);
		return rejected;
	}
	const hangingPromise = new Promise((_, reject) => {
		const boundRejection = reject.bind(null, new HangingPromiseRejectionError(route, expression));
		const currentListeners = abortListenersBySignal.get(signal);
		if (currentListeners) currentListeners.push(boundRejection);
		else {
			const listeners = [boundRejection];
			abortListenersBySignal.set(signal, listeners);
			signal.addEventListener("abort", () => {
				for (let i = 0; i < listeners.length; i++) listeners[i]();
				listeners.length = 0;
			}, { once: true });
		}
	});
	hangingPromise.catch(suppressUnhandledRejection);
	return hangingPromise;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/ppr-fallback-shell.js
var pprFallbackShellAls = getOrCreateAls("vinext.pprFallbackShell.als");
var pprFallbackShellCacheTaskStackAls = getOrCreateAls("vinext.pprFallbackShell.cacheTaskStack.als");
function noop() {}
function scheduleAfterTask(callback) {
	let firstTimer = setTimeout(() => {
		firstTimer = null;
		secondTimer = setTimeout(() => {
			secondTimer = null;
			callback();
		}, 0);
	}, 0);
	let secondTimer = null;
	return () => {
		if (firstTimer !== null) {
			clearTimeout(firstTimer);
			firstTimer = null;
		}
		if (secondTimer !== null) {
			clearTimeout(secondTimer);
			secondTimer = null;
		}
	};
}
function resolveCacheReadyIfSettled(state) {
	if (state.pendingCacheTasks !== 0) return;
	const resolvers = state.cacheReadyResolvers.splice(0);
	for (const resolve of resolvers) resolve();
}
function scheduleCacheReadyIfSettled(state) {
	if (state.pendingCacheTasks !== 0 || state.pendingCacheReadyCleanup !== null) return;
	state.pendingCacheReadyCleanup = scheduleAfterTask(() => {
		state.pendingCacheReadyCleanup = null;
		resolveCacheReadyIfSettled(state);
		if (state.phase === "final") scheduleAbortIfReady(state);
	});
}
function scheduleAbortIfReady(state) {
	if (state.phase !== "final" || !state.isFinalRenderStarted || !state.hasDynamicBoundary || state.pendingCacheTasks > 0 || state.pendingCacheReadyCleanup !== null || state.isAbortScheduled) return;
	state.isAbortScheduled = true;
	state.pendingAbortCleanup = scheduleAfterTask(() => {
		state.pendingAbortCleanup = null;
		state.isAbortScheduled = false;
		if (state.phase === "final" && state.hasDynamicBoundary && state.pendingCacheTasks === 0 && state.pendingCacheReadyCleanup === null && !state.reactAbortController.signal.aborted) {
			state.reactAbortController.abort();
			state.abortController.abort();
		}
	});
}
function completeCacheTask(state, task) {
	if (!task.isPending) return;
	task.isPending = false;
	if (task.epoch !== state.cacheEpoch) return;
	state.pendingCacheTasks--;
	scheduleCacheReadyIfSettled(state);
}
function ignoreCacheTask(state, task) {
	if (!task.isPending || task.isIgnored) return;
	task.isIgnored = true;
	completeCacheTask(state, task);
}
function getPprFallbackShellState() {
	return pprFallbackShellAls.getStore() ?? null;
}
function createPprFallbackShellSuspensePromiseForState(state, expression) {
	markPprFallbackShellDynamicBoundaryForState(state);
	if (state.phase === "final") scheduleAbortIfReady(state);
	const promise = makeHangingPromise(state.abortController.signal, state.routePattern, expression);
	promise.catch(noop);
	return promise;
}
function markPprFallbackShellDynamicBoundaryForState(state) {
	state.hasDynamicBoundary = true;
	for (const task of pprFallbackShellCacheTaskStackAls.getStore() ?? []) ignoreCacheTask(state, task);
	scheduleCacheReadyIfSettled(state);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/headers.js
/**
* next/headers shim
*
* Provides cookies() and headers() functions for App Router Server Components.
* These read from a request context set by the RSC handler before rendering.
*
* In Next.js 15+, cookies() and headers() return Promises (async).
* We support both the sync (legacy) and async patterns.
*/
var _FALLBACK_KEY$1 = Symbol.for("vinext.nextHeadersShim.fallback");
var _g$1 = globalThis;
var _als$2 = getOrCreateAls("vinext.nextHeadersShim.als");
var _fallbackState$1 = _g$1[_FALLBACK_KEY$1] ??= {
	headersContext: null,
	dynamicUsageDetected: false,
	renderRequestApiUsage: /* @__PURE__ */ new Set(),
	connectionProbe: null,
	invalidDynamicUsageError: null,
	pendingSetCookies: [],
	draftModeCookieHeader: null,
	phase: "render"
};
function _getState$1() {
	if (isInsideUnifiedScope()) return getRequestContext();
	return _als$2.getStore() ?? _fallbackState$1;
}
/**
* Dynamic usage flag — set when a component calls connection(), cookies(),
* headers(), or noStore() during rendering. When true, ISR caching is
* bypassed and the response gets Cache-Control: no-store.
*/
/**
* Mark the current render as requiring dynamic (uncached) rendering.
* Called by connection(), cookies(), headers(), and noStore().
*/
function markDynamicUsage() {
	const state = _getState$1();
	if (state.headersContext?.forceStatic) return;
	state.dynamicUsageDetected = true;
	forEachConnectionProbeTarget(state, (target) => {
		target.dynamicUsageDetected = true;
	});
}
function forEachConnectionProbeTarget(state, visit) {
	let target = state.connectionProbe?.dynamicUsageTarget ?? null;
	const seen = /* @__PURE__ */ new Set([state]);
	while (target && !seen.has(target)) {
		seen.add(target);
		visit(target);
		target = target.connectionProbe?.dynamicUsageTarget ?? null;
	}
}
function propagateInvalidDynamicUsageError(state, error) {
	forEachConnectionProbeTarget(state, (target) => {
		if (target.invalidDynamicUsageError == null) target.invalidDynamicUsageError = error;
	});
}
/**
* Measure dynamic usage in a child async scope without clearing the parent.
* Concurrent work that already belongs to the request (such as deferred
* metadata) keeps writing to the parent state and therefore remains visible
* to the final cache policy.
*/
async function runWithIsolatedDynamicUsage(fn) {
	const runInChildState = async (childState) => {
		return {
			result: await fn(),
			dynamicDetected: childState.dynamicUsageDetected
		};
	};
	if (isInsideUnifiedScope()) {
		let childState = null;
		return await runWithUnifiedStateMutation((context) => {
			context.dynamicUsageDetected = false;
			childState = context;
		}, () => {
			if (!childState) throw new Error("Dynamic usage scope was not initialized");
			return runInChildState(childState);
		});
	}
	const childState = {
		..._getState$1(),
		dynamicUsageDetected: false
	};
	return await _als$2.run(childState, () => runInChildState(childState));
}
function markRenderRequestApiUsage(kind) {
	_getState$1().renderRequestApiUsage.add(kind);
}
function throwIfStaticGenerationAccessError() {
	const accessError = _getState$1().headersContext?.accessError;
	if (accessError) throw accessError;
}
async function runWithConnectionProbe(fn) {
	const parentState = _getState$1();
	const parentInvalidDynamicUsageError = parentState.invalidDynamicUsageError;
	let interruptProbe = () => {};
	const interrupted = new Promise((resolve) => {
		interruptProbe = () => resolve({ completed: false });
	});
	const probe = {
		active: true,
		dynamicUsageTarget: parentState,
		interrupted: false,
		interrupt() {
			if (probe.interrupted) return;
			probe.interrupted = true;
			interruptProbe();
		},
		pending: new Promise(() => {})
	};
	const runInChildState = async (childState) => {
		try {
			const completed = Promise.resolve().then(fn).then((result) => ({
				completed: true,
				result
			}));
			return await Promise.race([completed, interrupted]);
		} finally {
			probe.active = false;
			childState.connectionProbe = parentState.connectionProbe ?? probe;
			if (childState.dynamicUsageDetected) parentState.dynamicUsageDetected = true;
			if (childState.invalidDynamicUsageError !== parentInvalidDynamicUsageError && parentState.invalidDynamicUsageError === parentInvalidDynamicUsageError) parentState.invalidDynamicUsageError = childState.invalidDynamicUsageError;
		}
	};
	if (isInsideUnifiedScope()) {
		let childState = null;
		return await runWithUnifiedStateMutation((context) => {
			context.connectionProbe = probe;
			childState = context;
		}, () => {
			if (!childState) throw new Error("Connection probe scope was not initialized");
			return runInChildState(childState);
		});
	}
	const childState = {
		...parentState,
		connectionProbe: probe
	};
	return await _als$2.run(childState, () => runInChildState(childState));
}
function peekRenderRequestApiUsage() {
	return [..._getState$1().renderRequestApiUsage].sort();
}
function consumeRenderRequestApiUsage() {
	const state = _getState$1();
	const observed = [...state.renderRequestApiUsage].sort();
	state.renderRequestApiUsage = /* @__PURE__ */ new Set();
	return observed;
}
/** Symbol used by cache-runtime.ts to store the "use cache" ALS on globalThis */
var _USE_CACHE_ALS_KEY = Symbol.for("vinext.cacheRuntime.contextAls");
/** Symbol used by cache.ts to store the unstable_cache ALS on globalThis */
var _UNSTABLE_CACHE_ALS_KEY = Symbol.for("vinext.unstableCache.als");
function _getGlobalCacheScopeStorage(key) {
	const value = Reflect.get(globalThis, key);
	if (!value || typeof value !== "object") return null;
	const getStore = Reflect.get(value, "getStore");
	if (typeof getStore !== "function") return null;
	return { getStore: () => getStore.call(value) };
}
function _getUseCacheGuardContext() {
	const store = _getGlobalCacheScopeStorage(_USE_CACHE_ALS_KEY)?.getStore();
	if (!store || typeof store !== "object") return null;
	return store;
}
function _isInsidePublicUseCache() {
	const ctx = _getUseCacheGuardContext();
	return ctx !== null && ctx.variant !== "private";
}
function _isInsideUnstableCache() {
	return _getGlobalCacheScopeStorage(_UNSTABLE_CACHE_ALS_KEY)?.getStore() === true;
}
/**
* Throw if the current execution is inside a "use cache" or unstable_cache()
* scope. Called by dynamic request APIs (headers, cookies, connection) to
* prevent request-specific data from being frozen into cached results.
*
* @param apiName - The name of the API being called (e.g. "connection()")
*/
function throwIfInsideCacheScope(apiName) {
	if (_isInsidePublicUseCache()) {
		const error = /* @__PURE__ */ new Error(`\`${apiName}\` cannot be called inside "use cache". If you need this data inside a cached function, call \`${apiName}\` outside and pass the required data as an argument.`);
		try {
			const cacheCtx = _getUseCacheGuardContext();
			if (cacheCtx) cacheCtx.invalidDynamicUsageError = error;
			const ctx = getRequestContext();
			if (ctx) ctx.invalidDynamicUsageError = error;
			propagateInvalidDynamicUsageError(_getState$1(), error);
		} catch {}
		throw error;
	}
	if (_isInsideUnstableCache()) {
		const error = /* @__PURE__ */ new Error(`\`${apiName}\` cannot be called inside a function cached with \`unstable_cache()\`. If you need this data inside a cached function, call \`${apiName}\` outside and pass the required data as an argument.`);
		try {
			const ctx = getRequestContext();
			if (ctx) ctx.invalidDynamicUsageError = error;
			propagateInvalidDynamicUsageError(_getState$1(), error);
		} catch {}
		throw error;
	}
}
/**
* Check, consume, and return any invalid dynamic usage error recorded during
* the render (e.g. cookies() called inside "use cache"). This error persists
* even if the throw was caught by user-code try/catch, so it can surface on
* client-side navigations where the static shell validation is skipped.
* Ported from Next.js: workStore.invalidDynamicUsageError in
* packages/next/src/server/app-render/app-render.tsx
* https://github.com/vercel/next.js/commit/f5e54c06726b571a042fce67417e40a29f6b8689
*/
function consumeInvalidDynamicUsageError() {
	const state = _getState$1();
	const err = state.invalidDynamicUsageError;
	state.invalidDynamicUsageError = null;
	return err;
}
/**
* Check and reset the dynamic usage flag.
* Called by the server after rendering to decide on caching.
*/
function consumeDynamicUsage() {
	const state = _getState$1();
	const used = state.dynamicUsageDetected;
	state.dynamicUsageDetected = false;
	return used;
}
/**
* Read the dynamic usage flag without resetting it.
* Used by the layout probe to fold a probe-scoped `markDynamicUsage()` into the
* per-layout observation before the isolated probe scope is discarded, so the
* observation captures `markDynamicUsage()` paths (e.g. `"use cache: private"`)
* that leave no other observable trace.
*/
function peekDynamicUsage() {
	return _getState$1().dynamicUsageDetected;
}
function _setStatePhase(state, phase) {
	const previous = state.phase;
	if (previous === "action" && phase === "render") state.headersContext?.mutableCookies?.[SYNCHRONIZE_REQUEST_COOKIES]();
	state.phase = phase;
	return previous;
}
function setHeadersAccessPhase(phase) {
	return _setStatePhase(_getState$1(), phase);
}
function getHeadersAccessPhase() {
	return _getState$1().phase;
}
/**
* Set the headers/cookies context for the current RSC render.
* Called by the framework's RSC entry before rendering each request.
*
* @deprecated Prefer runWithHeadersContext() which uses als.run() for
* proper per-request isolation. This function mutates the ALS store
* in-place and is only safe for cleanup (ctx=null) within an existing
* als.run() scope.
*/
/**
* Returns the current live HeadersContext from ALS (or the fallback).
* Used after applyMiddlewareRequestHeaders() to build a post-middleware
* request context for afterFiles/fallback rewrite has/missing evaluation.
*/
function getHeadersContext() {
	return _getState$1().headersContext;
}
function setHeadersContext(ctx) {
	const state = _getState$1();
	if (ctx !== null) {
		state.headersContext = ctx;
		state.dynamicUsageDetected = false;
		state.renderRequestApiUsage = /* @__PURE__ */ new Set();
		state.pendingSetCookies = [];
		state.draftModeCookieHeader = null;
		state.phase = "render";
	} else {
		state.headersContext = null;
		state.phase = "render";
	}
}
function runWithHeadersContext(ctx, fn) {
	if (isInsideUnifiedScope()) return runWithUnifiedStateMutation((uCtx) => {
		uCtx.headersContext = ctx;
		uCtx.dynamicUsageDetected = false;
		uCtx.renderRequestApiUsage = /* @__PURE__ */ new Set();
		uCtx.connectionProbe = null;
		uCtx.pendingSetCookies = [];
		uCtx.draftModeCookieHeader = null;
		uCtx.phase = "render";
	}, fn);
	const state = {
		headersContext: ctx,
		dynamicUsageDetected: false,
		renderRequestApiUsage: /* @__PURE__ */ new Set(),
		connectionProbe: null,
		invalidDynamicUsageError: null,
		pendingSetCookies: [],
		draftModeCookieHeader: null,
		phase: "render"
	};
	return _als$2.run(state, fn);
}
/** Methods on `Headers` that mutate state. Hoisted to module scope — static. */
var _HEADERS_MUTATING_METHODS = /* @__PURE__ */ new Set([
	"set",
	"delete",
	"append"
]);
/**
* Create a HeadersContext from a standard Request object.
*
* Performance note: In Workerd (Cloudflare Workers), `new Headers(request.headers)`
* copies the entire header map across the V8/C++ boundary, which shows up as
* ~815 ms self-time in production profiles when requests carry many headers.
* We defer this copy with a lazy proxy:
*
* - Reads (`get`, `has`, `entries`, …) are forwarded directly to the original
*   immutable `request.headers` — zero copy cost on the hot path.
* - The first mutating call (`set`, `delete`, `append`) materialises
*   `new Headers(request.headers)` once, then applies the mutation to the copy.
*   All subsequent operations go to the copy.
*
* This means the ~815 ms copy only occurs when middleware actually rewrites
* request headers via `NextResponse.next({ request: { headers } })`, which is
* uncommon.  Pure read requests (the vast majority) pay zero copy cost.
*
* Cookie parsing is also deferred: the `cookie` header string is not split
* until the first call to `cookies()` or `draftMode()`.
*/
function headersContextFromRequest(request, options) {
	let _mutable = null;
	const headersProxy = new Proxy(request.headers, { get(target, prop) {
		const src = _mutable ?? target;
		if (typeof prop === "string" && _HEADERS_MUTATING_METHODS.has(prop)) return (...args) => {
			if (!_mutable) _mutable = new Headers(target);
			return _mutable[prop](...args);
		};
		const value = Reflect.get(src, prop, src);
		return typeof value === "function" ? value.bind(src) : value;
	} });
	let _cookies = null;
	function getCookies() {
		if (_cookies) return _cookies;
		_cookies = parseEdgeRequestCookieHeader(headersProxy.get("cookie") || "");
		return _cookies;
	}
	return {
		headers: headersProxy,
		get cookies() {
			return getCookies();
		},
		draftModeSecret: options?.draftModeSecret
	};
}
/** Accumulated Set-Cookie headers from cookies().set() / .delete() calls */
/**
* Get and clear all pending Set-Cookie headers generated by cookies().set()/delete().
* Called by the framework after rendering to attach headers to the response.
*/
function getAndClearPendingCookies() {
	const state = _getState$1();
	const cookies = state.pendingSetCookies;
	state.pendingSetCookies = [];
	return cookies;
}
var DRAFT_MODE_COOKIE = "__prerender_bypass";
/**
* Get any Set-Cookie header generated by draftMode().enable()/disable().
* Called by the framework after rendering to attach the header to the response.
*/
function getDraftModeCookieHeader() {
	const state = _getState$1();
	const header = state.draftModeCookieHeader;
	state.draftModeCookieHeader = null;
	return header;
}
function validateDraftModeSecret(secret) {
	if (secret.length === 0) throw new Error("[vinext] draft mode secret must be a non-empty string.");
	return secret;
}
function isDraftModeRequest(request, draftModeSecret) {
	const cookieHeader = request.headers.get("cookie");
	if (!cookieHeader) return false;
	return parseEdgeRequestCookieHeader(cookieHeader).get(DRAFT_MODE_COOKIE) === validateDraftModeSecret(draftModeSecret);
}
/**
* Read draft mode from the live request context without recording request API
* usage. `null` means there is no active request context, which lets framework
* callers fall back to an explicitly supplied request when needed.
*/
function getActiveDraftModeState() {
	const context = _getState$1().headersContext;
	if (!context) return null;
	if (context.draftModeEnabled !== void 0) return context.draftModeEnabled;
	const secret = context.draftModeSecret;
	if (secret === void 0) return false;
	return context.cookies.get(DRAFT_MODE_COOKIE) === validateDraftModeSecret(secret);
}
var SYNCHRONIZE_REQUEST_COOKIES = Symbol("vinext.synchronize-request-cookies");
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/request-context.js
var import_jsx_runtime_react_server = require_jsx_runtime_react_server();
/**
* Request ExecutionContext — AsyncLocalStorage-backed accessor.
*
* Makes the Cloudflare Workers `ExecutionContext` (which provides
* `waitUntil`) available to any code on the call stack during a request
* without requiring it to be threaded through every function signature.
*
* Usage:
*
*   // In the worker entry, wrap the handler:
*   import { runWithExecutionContext } from "vinext/shims/request-context";
*   export default {
*     fetch(request, env, ctx) {
*       return runWithExecutionContext(ctx, () => handler.fetch(request, env, ctx));
*     }
*   };
*
*   // Anywhere downstream:
*   import { getRequestExecutionContext } from "vinext/shims/request-context";
*   const ctx = getRequestExecutionContext(); // null on Node.js dev
*   ctx?.waitUntil(somePromise);
*/
var _als$1 = getOrCreateAls("vinext.requestContext.als");
var OPEN_NEXT_CLOUDFLARE_CONTEXT_SYMBOL = Symbol.for("__cloudflare-context__");
var openNextCloudflareContextFallback;
function installOpenNextCloudflareContextBridge() {
	const descriptor = Object.getOwnPropertyDescriptor(globalThis, OPEN_NEXT_CLOUDFLARE_CONTEXT_SYMBOL);
	if (descriptor && !descriptor.configurable) return;
	openNextCloudflareContextFallback = descriptor && "value" in descriptor ? descriptor.value : descriptor?.get?.call(globalThis);
	Object.defineProperty(globalThis, OPEN_NEXT_CLOUDFLARE_CONTEXT_SYMBOL, {
		configurable: true,
		get() {
			const ctx = getRequestExecutionContext();
			return ctx ? { ctx } : openNextCloudflareContextFallback;
		},
		set(value) {
			openNextCloudflareContextFallback = value;
		}
	});
}
installOpenNextCloudflareContextBridge();
/**
* Get the `ExecutionContext` for the current request, or `null` when called
* outside a `runWithExecutionContext()` scope (e.g. on Node.js dev server).
*
* Use `ctx?.waitUntil(promise)` to schedule background work that must
* complete before the Worker isolate is torn down.
*/
function getRequestExecutionContext() {
	if (isInsideUnifiedScope()) return getRequestContext().executionContext;
	return _als$1.getStore() ?? null;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/normalize-path.js
function isInterceptionMatchedUrlPath(value) {
	return value.startsWith("/") && !value.startsWith("//") && !value.includes("?") && !value.includes("#") && !value.includes("\0");
}
/**
* Path normalization utility for request handling.
*
* Normalizes URL pathnames to a canonical form BEFORE any matching occurs
* (middleware, routing, redirects, rewrites). This ensures middleware and
* the router always see the same path, preventing path-confusion issues like
* double-slash mismatches.
*
* Normalization rules:
*  1. Collapse consecutive slashes: //foo///bar → /foo/bar
*  2. Resolve single-dot segments:  /foo/./bar  → /foo/bar
*  3. Resolve double-dot segments:  /foo/../bar → /bar
*  4. Ensure leading slash:         foo/bar     → /foo/bar
*  5. Preserve root:                /           → /
*
* This function does NOT:
*  - Strip or add trailing slashes (handled separately by trailingSlash config)
*  - Decode percent-encoded characters (callers should decode before calling this)
*  - Lowercase the path (route matching is case-sensitive)
*/
function normalizePath(pathname) {
	if (pathname === "/" || pathname.length > 1 && pathname[0] === "/" && !pathname.includes("//") && !pathname.includes("/./") && !pathname.includes("/../") && !pathname.endsWith("/.") && !pathname.endsWith("/..")) return pathname;
	const segments = pathname.split("/");
	const resolved = [];
	for (const segment of segments) {
		if (segment === "" || segment === ".") continue;
		if (segment === "..") resolved.pop();
		else resolved.push(segment);
	}
	return "/" + resolved.join("/");
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/cdn-cache.js
/**
* CDN cache adapter — owns the *page-level ISR serving strategy*.
*
* This is deliberately distinct from the data cache handler (see `./cache.ts`):
*
* - The **data cache** stores cached data (fetch, `"use cache"`,
*   `unstable_cache`, route-handler data). It is a pure key/value store.
*
* - The **CDN cache adapter** decides *how page-level ISR is served*: where the
*   rendered page/route/image artifacts live, what cache headers the response
*   carries, whether the origin runs background regeneration, and how
*   invalidation propagates to a CDN edge.
*
* Two strategies sit behind one interface:
*
* | Concern            | DefaultCdnCacheAdapter (origin-managed) | Edge adapter (CDN-managed)                  |
* | ------------------ | --------------------------------------- | ------------------------------------------- |
* | Serve from store?  | Yes — reads the data cache              | No — origin renders fresh, edge caches      |
* | Background regen   | In-process via `waitUntil`              | Edge re-requests origin                     |
* | Response headers   | `Cache-Control` (SWR)                   | `Cache-Control: no-store` + `CDN-Cache-Control: <SWR>` |
* | Invalidation       | (data cache handles tag invalidation)   | purge / revalidate via request context      |
*
* The default adapter is a thin shim over the data cache + the framework's
* existing header logic, so default behavior is byte-for-byte identical to the
* pre-split implementation.
*/
var PENDING_DYNAMIC_CACHE_CONTROL = "no-store, must-revalidate";
/**
* Default origin-managed ISR strategy: store page artifacts in the data cache,
* serve HIT/STALE from it, run in-process background regeneration, and emit the
* framework's standard `Cache-Control` headers.
*/
var DefaultCdnCacheAdapter = class {
	ownsBackgroundRevalidation = true;
	async get(key, ctx) {
		return getDataCacheHandler().get(key, ctx);
	}
	async set(key, data, ctx) {
		await getDataCacheHandler().set(key, data, ctx);
	}
	buildResponseHeaders(input) {
		if (input.pendingDynamicCheck) return { "Cache-Control": PENDING_DYNAMIC_CACHE_CONTROL };
		return { "Cache-Control": input.cacheControl };
	}
	async revalidateTag(_tags, _durations) {}
};
var _CDN_KEY = Symbol.for("vinext.cdnCacheAdapter");
var _gCdn = globalThis;
var _defaultAdapter = null;
/**
* Get the active CDN cache adapter. An explicitly configured adapter wins;
* otherwise the origin-managed {@link DefaultCdnCacheAdapter} is used.
*/
function getCdnCacheAdapter() {
	const active = _gCdn[_CDN_KEY];
	if (active) return active;
	return _defaultAdapter ??= new DefaultCdnCacheAdapter();
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/hash.js
/**
* FNV-1a hash producing a 64-bit result (two 32-bit rounds with different seeds).
* Used for deterministic key generation where collisions must be rare.
*
* This is a vinext-internal format: nothing outside vinext ever compares
* these values, so the algorithm only needs to be deterministic. For values
* that must be byte-for-byte identical to what Next.js emits (ETags), use
* `fnv1a52` below instead — the two are NOT interchangeable.
*/
function fnv1a64(input) {
	let h1 = 2166136261;
	for (let i = 0; i < input.length; i++) {
		h1 ^= input.charCodeAt(i);
		h1 = h1 * 16777619 >>> 0;
	}
	let h2 = 84696351;
	for (let i = 0; i < input.length; i++) {
		h2 ^= input.charCodeAt(i);
		h2 = h2 * 16777619 >>> 0;
	}
	return h1.toString(16).padStart(8, "0") + h2.toString(16).padStart(8, "0");
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/compare.js
var compareStrings = (left, right) => {
	if (left < right) return -1;
	if (left > right) return 1;
	return 0;
};
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/artifact-compatibility.js
var ARTIFACT_COMPATIBILITY_PROOF_FIELDS = [
	"schemaVersion",
	"graphVersion",
	"deploymentVersion",
	"appElementsSchemaVersion",
	"rscPayloadSchemaVersion",
	"rootBoundaryId",
	"renderEpoch"
];
function createArtifactCompatibilityEnvelope(input = {}) {
	return {
		schemaVersion: 1,
		graphVersion: input.graphVersion ?? null,
		deploymentVersion: input.deploymentVersion ?? null,
		appElementsSchemaVersion: 1,
		rscPayloadSchemaVersion: 1,
		rootBoundaryId: input.rootBoundaryId ?? null,
		renderEpoch: input.renderEpoch ?? null
	};
}
function createArtifactCompatibilityGraphVersion(input) {
	return `app-route-graph:${fnv1a64(JSON.stringify([input.routePattern, input.rootBoundaryId]))}`;
}
function isStringOrNull(value) {
	return typeof value === "string" || value === null;
}
function hasCurrentSchemaVersions(record) {
	return record.schemaVersion === 1 && record.appElementsSchemaVersion === 1 && record.rscPayloadSchemaVersion === 1;
}
function parseArtifactCompatibilityEnvelope(value) {
	if (!isUnknownRecord(value)) return null;
	if (!hasCurrentSchemaVersions(value)) return null;
	if (!isStringOrNull(value.graphVersion)) return null;
	if (!isStringOrNull(value.deploymentVersion)) return null;
	if (!isStringOrNull(value.rootBoundaryId)) return null;
	if (!isStringOrNull(value.renderEpoch)) return null;
	return {
		schemaVersion: 1,
		graphVersion: value.graphVersion,
		deploymentVersion: value.deploymentVersion,
		appElementsSchemaVersion: 1,
		rscPayloadSchemaVersion: 1,
		rootBoundaryId: value.rootBoundaryId,
		renderEpoch: value.renderEpoch
	};
}
function incompatible(reason) {
	return {
		kind: "incompatible",
		fallback: "renderFresh",
		reason
	};
}
function unknown(reason) {
	return {
		kind: "unknown",
		fallback: "renderFresh",
		reason
	};
}
function compareKnownField(currentValue, candidateValue, unknownReason, mismatchReason, notDeclaredCompatibleReason, compatibilitySets) {
	if (currentValue === null || candidateValue === null) return unknown(unknownReason);
	if (currentValue === candidateValue) return null;
	if (compatibilitySets === void 0) return incompatible(mismatchReason);
	return isDeclaredCompatible(currentValue, candidateValue, compatibilitySets) ? null : incompatible(notDeclaredCompatibleReason);
}
function isDeclaredCompatible(currentValue, candidateValue, compatibilitySets) {
	return compatibilitySets.some((compatibilitySet) => compatibilitySet.includes(currentValue) && compatibilitySet.includes(candidateValue));
}
function evaluateArtifactCompatibility(current, candidate, options = {}) {
	if (current.schemaVersion !== candidate.schemaVersion) return incompatible("schemaVersionMismatch");
	if (current.appElementsSchemaVersion !== candidate.appElementsSchemaVersion) return incompatible("appElementsSchemaVersionMismatch");
	if (current.rscPayloadSchemaVersion !== candidate.rscPayloadSchemaVersion) return incompatible("rscPayloadSchemaVersionMismatch");
	const graphDecision = compareKnownField(current.graphVersion, candidate.graphVersion, "graphVersionUnknown", "graphVersionMismatch", "graphVersionNotDeclaredCompatible", options.compatibilityMap?.graphVersions);
	if (graphDecision) return graphDecision;
	const deploymentDecision = compareKnownField(current.deploymentVersion, candidate.deploymentVersion, "deploymentVersionUnknown", "deploymentVersionMismatch", "deploymentVersionNotDeclaredCompatible", options.compatibilityMap?.deploymentVersions);
	if (deploymentDecision) return deploymentDecision;
	const rootBoundaryDecision = compareKnownField(current.rootBoundaryId, candidate.rootBoundaryId, "rootBoundaryIdUnknown", "rootBoundaryIdMismatch", "rootBoundaryIdNotDeclaredCompatible", options.compatibilityMap?.rootBoundaryIds);
	if (rootBoundaryDecision) return rootBoundaryDecision;
	const renderEpochDecision = compareKnownField(current.renderEpoch, candidate.renderEpoch, "renderEpochUnknown", "renderEpochMismatch", "renderEpochNotDeclaredCompatible", options.compatibilityMap?.renderEpochs);
	if (renderEpochDecision) return renderEpochDecision;
	return { kind: "compatible" };
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/promise.js
function isPromiseLike(value) {
	return Boolean(value && (typeof value === "object" || typeof value === "function") && "then" in value && typeof value.then === "function");
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-render-dependency.js
var REACT_CLIENT_REFERENCE = Symbol.for("react.client.reference");
var REACT_FORWARD_REF = Symbol.for("react.forward_ref");
var REACT_LAZY = Symbol.for("react.lazy");
var REACT_MEMO = Symbol.for("react.memo");
function isReactOwnedAppComponent(component) {
	const candidate = component;
	if (candidate?.$$typeof === REACT_MEMO || candidate?.$$typeof === REACT_LAZY || candidate?.$$typeof === REACT_FORWARD_REF) return false;
	return typeof candidate !== "function" || candidate.$$typeof === REACT_CLIENT_REFERENCE || candidate.prototype?.isReactComponent != null;
}
function invokeAppComponent(component, props) {
	const candidate = component;
	if (candidate.$$typeof === REACT_MEMO && candidate.type) return invokeAppComponent(candidate.type, props);
	if (candidate.$$typeof === REACT_LAZY && candidate._init) return invokeAppComponent(candidate._init(candidate._payload), props);
	if (candidate.$$typeof === REACT_FORWARD_REF && candidate.render) return candidate.render(props, void 0);
	if (isReactOwnedAppComponent(candidate)) return (0, import_react_react_server.createElement)(candidate, props);
	return candidate(props);
}
var appElementRenderDependencies = /* @__PURE__ */ new WeakMap();
function registerAppElementRenderDependencies(elements, dependenciesByElementId) {
	if (dependenciesByElementId.size === 0) return;
	appElementRenderDependencies.set(elements, dependenciesByElementId);
}
function releaseAppElementRenderDependency(elements, elementId) {
	appElementRenderDependencies.get(elements)?.get(elementId)?.release();
}
function createAppRenderDependency() {
	let released = false;
	let resolve;
	return {
		promise: new Promise((promiseResolve) => {
			resolve = promiseResolve;
		}),
		release() {
			if (released) return;
			released = true;
			resolve();
		}
	};
}
function createAppPageRenderDependency() {
	const initialization = createAppRenderDependency();
	let resultDependencies = [];
	return {
		...initialization,
		get resultDependencies() {
			return resultDependencies;
		},
		setResultDependencies(dependencies) {
			resultDependencies = dependencies;
		}
	};
}
function isAppRenderSuspension(error) {
	if (isPromiseLike(error)) return true;
	return error instanceof Error && error.message.startsWith("Suspense Exception: This is not a real error!");
}
function renderAfterAppDependencies(children, dependencies) {
	if (dependencies.length === 0) return children;
	const pendingDependencies = Promise.all(dependencies.map((dependency) => dependency.promise));
	function AwaitAppRenderDependencies() {
		(0, import_react_react_server.use)(pendingDependencies);
		return children;
	}
	return /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(AwaitAppRenderDependencies, {});
}
function renderAppComponentWithDependencyBarrier(component, props, dependency) {
	function AppComponentDependencyBarrier() {
		try {
			const result = invokeAppComponent(component, props);
			if (isPromiseLike(result)) return Promise.resolve(result).then((resolvedResult) => {
				dependency.release();
				return resolvedResult;
			}, (error) => {
				dependency.release();
				throw error;
			});
			dependency.release();
			return result;
		} catch (error) {
			if (!isAppRenderSuspension(error)) dependency.release();
			throw error;
		}
	}
	return (0, import_react_react_server.createElement)(AppComponentDependencyBarrier);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-elements-wire.js
var APP_INTERCEPTION_SEPARATOR = "\0";
var LEGACY_APP_SOURCE_PAGE_KEY = "__sourcePage";
var APP_ARTIFACT_COMPATIBILITY_KEY = "__artifactCompatibility";
var APP_CACHE_ENTRY_REUSE_PROOF_KEY = "__cacheEntryReuseProof";
var APP_DYNAMIC_STALE_TIME_KEY = "__dynamicStaleTime";
var APP_INTERCEPTION_KEY = "__interception";
var APP_INTERCEPTION_CONTEXT_KEY = "__interceptionContext";
var APP_LAYOUT_IDS_KEY = "__layoutIds";
var APP_LAYOUT_FLAGS_KEY = "__layoutFlags";
var APP_ROUTE_KEY = "__route";
var APP_ROOT_LAYOUT_KEY = "__rootLayout";
var APP_SKIPPED_LAYOUT_IDS_KEY = "__skippedLayoutIds";
var APP_SOURCE_PAGE_SEGMENTS_KEY = "__srcPage";
var APP_SLOT_BINDINGS_KEY = "__slotBindings";
/** Opaque per-segment identities derived at the server route-graph boundary. */
var APP_BFCACHE_SEGMENT_IDENTITIES_KEY = "__bfcacheSegmentIdentities";
/**
* Static sibling segment names for the matched route, surfaced so the client
* router can determine if a cached prefetch of a dynamic route can be reused
* when navigating to a static sibling URL.
*
* Mirrors Next.js's `staticSiblings` tuple element on the loader-tree dynamic
* segments (issue cloudflare/vinext#1525).
*/
var APP_STATIC_SIBLINGS_KEY = "__staticSiblings";
var APP_UNMATCHED_SLOT_WIRE_VALUE = "__VINEXT_UNMATCHED_SLOT__";
var UNMATCHED_SLOT = Symbol.for("vinext.unmatchedSlot");
var EMPTY_SKIPPED_LAYOUT_IDS = /* @__PURE__ */ new Set();
function createCacheProofRejectionCodeSet(codes) {
	return new Set(codes);
}
var CACHE_PROOF_REJECTION_CODES = createCacheProofRejectionCodeSet([
	"CP_CACHE_ENTRY_PROOF_MISSING",
	"CP_MODEL_DISABLED",
	"CP_ARTIFACT_COMPATIBILITY_INCOMPATIBLE",
	"CP_ARTIFACT_COMPATIBILITY_UNKNOWN",
	"CP_DIMENSION_COUNT_EXCEEDED",
	"CP_DIMENSION_NAME_MISSING",
	"CP_DIMENSION_NAME_TOO_LONG",
	"CP_DIMENSION_VALUE_COUNT_EXCEEDED",
	"CP_DIMENSION_VALUE_TOO_LONG",
	"CP_DIMENSION_VALUES_MISSING",
	"CP_ENCODED_VARIANT_TOO_LONG",
	"CP_INVALID_VARIANT_BUDGET",
	"CP_ROUTE_VARIANT_BUDGET_ROUTE_MISMATCH",
	"CP_ROUTE_VARIANT_CEILING_EXCEEDED",
	"CP_UNSAFE_PUBLIC_DIMENSION",
	"CP_BOUNDARY_OUTCOME_MISMATCH",
	"CP_BOUNDARY_OUTCOME_UNKNOWN",
	"CP_PRIVATE_DYNAMIC_DOWNGRADE",
	"CP_STATIC_LAYOUT_CANDIDATE_OUTPUT_KIND",
	"CP_STATIC_LAYOUT_CURRENT_OUTPUT_KIND",
	"CP_STATIC_LAYOUT_ID_MISMATCH",
	"CP_STATIC_LAYOUT_OBSERVATION_OUTPUT_KIND",
	"CP_STATIC_LAYOUT_OBSERVATION_OUTPUT_MISMATCH",
	"CP_STATIC_LAYOUT_PRIVATE_DYNAMIC_DOWNGRADE",
	"CP_STATIC_LAYOUT_REQUEST_API_OBSERVED",
	"CP_STATIC_LAYOUT_REQUEST_API_UNKNOWN",
	"CP_STATIC_LAYOUT_ROOT_BOUNDARY_MISMATCH",
	"CP_STATIC_LAYOUT_ROOT_BOUNDARY_UNKNOWN",
	"CP_STATIC_LAYOUT_VARIANT_DIMENSION_UNPROVEN"
]);
var compareAppElementsSlotIds = compareStrings;
function compareAppElementsSlotBindingsBySlotId(left, right) {
	return compareAppElementsSlotIds(left.slotId, right.slotId);
}
function normalizeAppElementsSlotBindings(slotBindings, options = {}) {
	const ownerLayoutIds = options.layoutIds ? new Set(options.layoutIds) : null;
	const seenSlotIds = /* @__PURE__ */ new Set();
	const normalized = [];
	for (const binding of slotBindings) {
		if (seenSlotIds.has(binding.slotId)) throw new Error("[vinext] Invalid __slotBindings in App Router payload: duplicate slot id");
		seenSlotIds.add(binding.slotId);
		if (ownerLayoutIds && binding.ownerLayoutId !== null && !ownerLayoutIds.has(binding.ownerLayoutId)) throw new Error("[vinext] Invalid __slotBindings in App Router payload: owner layout id missing from __layoutIds");
		normalized.push({ ...binding });
	}
	return normalized.sort(compareAppElementsSlotBindingsBySlotId);
}
function appendInterceptionContext(identity, interceptionContext) {
	return interceptionContext === null ? identity : `${identity}${APP_INTERCEPTION_SEPARATOR}${interceptionContext}`;
}
function createAppPayloadRouteId(routePath, interceptionContext) {
	return appendInterceptionContext(`route:${routePath}`, interceptionContext);
}
function createAppPayloadPageId(routePath, interceptionContext) {
	return appendInterceptionContext(`page:${routePath}`, interceptionContext);
}
function createAppPayloadLayoutId(treePath) {
	return `layout:${treePath}`;
}
function createAppPayloadTemplateId(treePath) {
	return `template:${treePath}`;
}
function createAppPayloadSlotId(slotName, treePath) {
	return `slot:${slotName}:${treePath}`;
}
function createAppPayloadCacheKey(rscUrl, interceptionContext) {
	return appendInterceptionContext(rscUrl, interceptionContext);
}
function parsePathWithInterception(input) {
	const separatorIndex = input.indexOf(APP_INTERCEPTION_SEPARATOR);
	const path = separatorIndex === -1 ? input : input.slice(0, separatorIndex);
	if (!path.startsWith("/")) return null;
	return {
		interceptionContext: separatorIndex === -1 ? null : input.slice(separatorIndex + 1),
		path
	};
}
/**
* AppElements tree paths are absolute route-tree paths on the wire.
* Bare segment names are not valid layout/template/slot tree identities.
*/
function parseTreePath(input) {
	return input.startsWith("/") ? input : null;
}
function parseAppElementsWireElementKey(key) {
	if (key.startsWith("route:")) {
		const parsed = parsePathWithInterception(key.slice(6));
		if (!parsed) return null;
		return {
			interceptionContext: parsed.interceptionContext,
			kind: "route",
			path: parsed.path
		};
	}
	if (key.startsWith("page:")) {
		const parsed = parsePathWithInterception(key.slice(5));
		if (!parsed) return null;
		return {
			interceptionContext: parsed.interceptionContext,
			kind: "page",
			path: parsed.path
		};
	}
	if (key.startsWith("layout:")) {
		const treePath = parseTreePath(key.slice(7));
		return treePath ? {
			kind: "layout",
			treePath
		} : null;
	}
	if (key.startsWith("template:")) {
		const treePath = parseTreePath(key.slice(9));
		return treePath ? {
			kind: "template",
			treePath
		} : null;
	}
	if (key.startsWith("slot:")) {
		const body = key.slice(5);
		const separatorIndex = body.indexOf(":");
		if (separatorIndex <= 0) return null;
		const name = body.slice(0, separatorIndex);
		const treePath = parseTreePath(body.slice(separatorIndex + 1));
		return treePath ? {
			kind: "slot",
			name,
			treePath
		} : null;
	}
	return null;
}
function isAppElementsWireBfcacheIdentityId(key) {
	const kind = parseAppElementsWireElementKey(key)?.kind;
	return kind === "page" || kind === "layout" || kind === "template" || kind === "slot";
}
function isAppElementsWireSlotId(key) {
	if (!key.startsWith("slot:")) return false;
	const body = key.slice(5);
	const separatorIndex = body.indexOf(":");
	return separatorIndex > 0 && body.charCodeAt(separatorIndex + 1) === 47;
}
function isSourcePageSegments(value) {
	return Array.isArray(value) && value.length > 0 && value.every((segment) => typeof segment === "string" && segment.length > 0 && !segment.includes("/"));
}
function encodeSourcePageSegments(sourcePage) {
	if (typeof sourcePage !== "string" || !sourcePage.startsWith("/")) return null;
	const segments = sourcePage.slice(1).split("/");
	return isSourcePageSegments(segments) ? segments : null;
}
function createAppElementsWireMetadataEntries(input) {
	const layoutIds = [...input.layoutIds ?? []];
	const sourcePageSegments = encodeSourcePageSegments(input.sourcePage);
	const entries = {
		[APP_ROUTE_KEY]: input.routeId,
		[APP_INTERCEPTION_CONTEXT_KEY]: input.interceptionContext,
		[APP_LAYOUT_IDS_KEY]: layoutIds,
		[APP_ROOT_LAYOUT_KEY]: input.rootLayoutTreePath,
		...input.dynamicStaleTimeSeconds === void 0 ? {} : { [APP_DYNAMIC_STALE_TIME_KEY]: input.dynamicStaleTimeSeconds },
		...input.bfcacheSegmentIdentities && Object.keys(input.bfcacheSegmentIdentities).length > 0 ? { [APP_BFCACHE_SEGMENT_IDENTITIES_KEY]: input.bfcacheSegmentIdentities } : {},
		...sourcePageSegments === null ? {} : { [APP_SOURCE_PAGE_SEGMENTS_KEY]: sourcePageSegments }
	};
	const entriesWithInterception = input.interception ? {
		...entries,
		[APP_INTERCEPTION_KEY]: input.interception
	} : entries;
	if (input.slotBindings && input.slotBindings.length > 0) return {
		...entriesWithInterception,
		[APP_SLOT_BINDINGS_KEY]: normalizeAppElementsSlotBindings(input.slotBindings, { layoutIds })
	};
	return entriesWithInterception;
}
function normalizeAppElements(elements) {
	let needsNormalization = false;
	for (const [key, value] of Object.entries(elements)) if (isAppElementsWireSlotId(key) && value === "__VINEXT_UNMATCHED_SLOT__") {
		needsNormalization = true;
		break;
	}
	if (!needsNormalization) return elements;
	const normalized = {};
	for (const [key, value] of Object.entries(elements)) normalized[key] = isAppElementsWireSlotId(key) && value === "__VINEXT_UNMATCHED_SLOT__" ? UNMATCHED_SLOT : value;
	return normalized;
}
function isLayoutFlagsRecord(value) {
	if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
	for (const v of Object.values(value)) if (v !== "s" && v !== "d") return false;
	return true;
}
function parseLayoutFlags(value) {
	if (isLayoutFlagsRecord(value)) return value;
	return {};
}
function parseLayoutIdList(value, fieldName) {
	if (value === void 0) return [];
	if (!Array.isArray(value)) throw new Error(`[vinext] Invalid ${fieldName} in App Router payload: expected layout id string[]`);
	const layoutIds = [];
	for (const entry of value) {
		if (typeof entry !== "string") throw new Error(`[vinext] Invalid ${fieldName} in App Router payload: expected layout id string[]`);
		if (parseAppElementsWireElementKey(entry)?.kind !== "layout") throw new Error(`[vinext] Invalid ${fieldName} in App Router payload: expected layout ids`);
		layoutIds.push(entry);
	}
	return layoutIds;
}
function parseLayoutIds(value) {
	return parseLayoutIdList(value, APP_LAYOUT_IDS_KEY);
}
function parseSkippedLayoutIds(value) {
	return parseLayoutIdList(value, APP_SKIPPED_LAYOUT_IDS_KEY);
}
function isSlotBindingState(value) {
	return value === "active" || value === "default" || value === "unmatched";
}
function parseSlotBindings(value, options = {}) {
	if (value === void 0) return [];
	if (!Array.isArray(value)) throw new Error("[vinext] Invalid __slotBindings in App Router payload: expected array");
	const slotBindings = [];
	for (const entry of value) {
		if (!isUnknownRecord(entry)) throw new Error("[vinext] Invalid __slotBindings in App Router payload: expected objects");
		const slotId = entry.slotId;
		if (typeof slotId !== "string" || parseAppElementsWireElementKey(slotId)?.kind !== "slot") throw new Error("[vinext] Invalid __slotBindings in App Router payload: expected slot ids");
		const ownerLayoutId = entry.ownerLayoutId;
		if (ownerLayoutId !== null && (typeof ownerLayoutId !== "string" || parseAppElementsWireElementKey(ownerLayoutId)?.kind !== "layout")) throw new Error("[vinext] Invalid __slotBindings in App Router payload: expected owner layout ids");
		const state = entry.state;
		if (!isSlotBindingState(state)) throw new Error("[vinext] Invalid __slotBindings in App Router payload: expected state");
		const activeRouteId = entry.activeRouteId;
		if (activeRouteId !== void 0 && activeRouteId !== null && (typeof activeRouteId !== "string" || parseAppElementsWireElementKey(activeRouteId)?.kind !== "route")) throw new Error("[vinext] Invalid __slotBindings in App Router payload: expected route ids");
		slotBindings.push({
			...activeRouteId !== void 0 ? { activeRouteId } : {},
			ownerLayoutId,
			slotId,
			state
		});
	}
	return normalizeAppElementsSlotBindings(slotBindings, options);
}
function readRequiredInterceptionString(entry, fieldName) {
	const value = entry[fieldName];
	if (typeof value !== "string") throw new Error("[vinext] Invalid __interception in App Router payload: expected strings");
	return value;
}
function parseInterceptionMatchedUrl(value) {
	if (!isInterceptionMatchedUrlPath(value)) throw new Error("[vinext] Invalid __interception in App Router payload: expected path URLs");
	return value;
}
function parseInterceptionRouteId(value, matchedUrl) {
	const parsed = parseAppElementsWireElementKey(value);
	if (parsed?.kind !== "route" || parsed.path !== matchedUrl || parsed.interceptionContext !== null) throw new Error("[vinext] Invalid __interception in App Router payload: expected route ids");
	return value;
}
function parseInterceptionSlotId(value) {
	if (parseAppElementsWireElementKey(value)?.kind !== "slot") throw new Error("[vinext] Invalid __interception in App Router payload: expected slot id");
	return value;
}
function parseInterceptionMetadata(value) {
	if (value === void 0 || value === null) return null;
	if (!isUnknownRecord(value)) throw new Error("[vinext] Invalid __interception in App Router payload: expected object");
	const sourceMatchedUrl = parseInterceptionMatchedUrl(readRequiredInterceptionString(value, "sourceMatchedUrl"));
	const targetMatchedUrl = parseInterceptionMatchedUrl(readRequiredInterceptionString(value, "targetMatchedUrl"));
	return {
		sourceMatchedUrl,
		sourceRouteId: parseInterceptionRouteId(readRequiredInterceptionString(value, "sourceRouteId"), sourceMatchedUrl),
		slotId: parseInterceptionSlotId(readRequiredInterceptionString(value, "slotId")),
		targetMatchedUrl,
		targetRouteId: parseInterceptionRouteId(readRequiredInterceptionString(value, "targetRouteId"), targetMatchedUrl)
	};
}
/**
* Type predicate for a plain (non-null, non-array) record of app payload values.
* Used to distinguish the App Router payload object from bare React elements at
* the render boundary. Narrows to `Readonly<Record<string, unknown>>` because
* the outgoing payload carries heterogeneous values (ReactNodes for the rendered
* tree, plus metadata like `__layoutFlags` which is a plain object). Delegates
* to React's canonical `isValidElement` so we don't depend on React's internal
* `$$typeof` marker scheme.
*/
function isAppElementsRecord(value) {
	if (typeof value !== "object" || value === null) return false;
	if (Array.isArray(value)) return false;
	if ((0, import_react_react_server.isValidElement)(value)) return false;
	return true;
}
function withLayoutFlags(elements, layoutFlags) {
	return {
		...elements,
		[APP_LAYOUT_FLAGS_KEY]: layoutFlags
	};
}
function buildOutgoingAppPayload(input) {
	if (!isAppElementsRecord(input.element)) return input.element;
	const skippedLayoutIds = createSkippedLayoutIds(input.skipDisposition);
	const payload = {};
	for (const [key, value] of Object.entries(input.element)) {
		if (skippedLayoutIds.has(key)) {
			releaseAppElementRenderDependency(input.element, key);
			continue;
		}
		payload[key] = value === UNMATCHED_SLOT ? APP_UNMATCHED_SLOT_WIRE_VALUE : value;
	}
	payload[APP_LAYOUT_FLAGS_KEY] = input.layoutFlags;
	if (skippedLayoutIds.size > 0) payload[APP_SKIPPED_LAYOUT_IDS_KEY] = [...skippedLayoutIds];
	payload[APP_ARTIFACT_COMPATIBILITY_KEY] = input.artifactCompatibility ?? createArtifactCompatibilityEnvelope();
	if (input.cacheEntryReuseProof) payload[APP_CACHE_ENTRY_REUSE_PROOF_KEY] = input.cacheEntryReuseProof;
	if (input.dynamicStaleTimeSeconds !== void 0) payload[APP_DYNAMIC_STALE_TIME_KEY] = input.dynamicStaleTimeSeconds;
	return payload;
}
function createSkippedLayoutIds(skipDisposition) {
	if (skipDisposition?.enabled !== true) return EMPTY_SKIPPED_LAYOUT_IDS;
	const skippedLayoutIds = /* @__PURE__ */ new Set();
	for (const id of skipDisposition.skippedEntryIds) if (parseAppElementsWireElementKey(id)?.kind === "layout") skippedLayoutIds.add(id);
	return skippedLayoutIds;
}
function readArtifactCompatibilityMetadata(value) {
	if (value === void 0) return createArtifactCompatibilityEnvelope();
	return parseArtifactCompatibilityEnvelope(value) ?? createArtifactCompatibilityEnvelope();
}
function readSourcePageMetadata(value) {
	if (value === void 0 || value === null) return null;
	if (typeof value === "string") return value.startsWith("/") ? value : null;
	if (!isSourcePageSegments(value)) return null;
	return `/${value.join("/")}`;
}
function createMissingCacheEntryReuseProof() {
	return {
		kind: "runtime-cache-entry",
		decision: null
	};
}
function isCacheProofRejectionCode(value) {
	return typeof value === "string" && CACHE_PROOF_REJECTION_CODES.has(value);
}
function isCacheProofFallbackMode(value) {
	return value === "renderFresh" || value === "privateUncacheable";
}
function isCacheProofFallbackScope(value) {
	return value === "affectedOutput" || value === "route";
}
function parseCacheEntryReuseProofMetadata(value) {
	if (value === void 0) return null;
	if (!isUnknownRecord(value) || value.kind !== "runtime-cache-entry") return createMissingCacheEntryReuseProof();
	const decision = value.decision;
	if (decision === null) return createMissingCacheEntryReuseProof();
	if (!isUnknownRecord(decision)) return createMissingCacheEntryReuseProof();
	if (decision.kind === "reuse" && decision.canReuse === true && decision.code === "CP_STATIC_LAYOUT_REUSE_PROVEN" && decision.reuseClass === "static-layout") return {
		kind: "runtime-cache-entry",
		decision: {
			canReuse: true,
			code: decision.code,
			kind: "reuse",
			reuseClass: decision.reuseClass
		}
	};
	if (decision.kind === "reject" && decision.canReuse === false && isCacheProofRejectionCode(decision.code) && isCacheProofFallbackMode(decision.mode) && isCacheProofFallbackScope(decision.scope)) return {
		kind: "runtime-cache-entry",
		decision: {
			canReuse: false,
			code: decision.code,
			kind: "reject",
			mode: decision.mode,
			scope: decision.scope
		}
	};
	return createMissingCacheEntryReuseProof();
}
function parseBfcacheSegmentIdentities(value) {
	if (!isUnknownRecord(value)) return {};
	const parsed = {};
	for (const [key, entry] of Object.entries(value)) {
		if (typeof entry !== "string" || !isAppElementsWireBfcacheIdentityId(key)) return {};
		parsed[key] = entry;
	}
	return parsed;
}
function readAppElementsMetadata(elements) {
	const routeId = elements[APP_ROUTE_KEY];
	if (typeof routeId !== "string") throw new Error("[vinext] Missing __route string in App Router payload");
	const interceptionContext = elements[APP_INTERCEPTION_CONTEXT_KEY];
	if (interceptionContext !== void 0 && interceptionContext !== null && typeof interceptionContext !== "string") throw new Error("[vinext] Invalid __interceptionContext in App Router payload");
	const rootLayoutTreePath = elements[APP_ROOT_LAYOUT_KEY];
	if (rootLayoutTreePath === void 0) throw new Error("[vinext] Missing __rootLayout key in App Router payload");
	if (rootLayoutTreePath !== null && typeof rootLayoutTreePath !== "string") throw new Error("[vinext] Invalid __rootLayout in App Router payload: expected string or null");
	const layoutFlags = parseLayoutFlags(elements[APP_LAYOUT_FLAGS_KEY]);
	const layoutIds = parseLayoutIds(elements[APP_LAYOUT_IDS_KEY]);
	const skippedLayoutIds = parseSkippedLayoutIds(elements[APP_SKIPPED_LAYOUT_IDS_KEY]);
	const slotBindings = parseSlotBindings(elements[APP_SLOT_BINDINGS_KEY], { layoutIds });
	const interception = parseInterceptionMetadata(elements[APP_INTERCEPTION_KEY]);
	const artifactCompatibility = readArtifactCompatibilityMetadata(elements[APP_ARTIFACT_COMPATIBILITY_KEY]);
	const cacheEntryReuseProof = parseCacheEntryReuseProofMetadata(elements[APP_CACHE_ENTRY_REUSE_PROOF_KEY]);
	const dynamicStaleTime = elements[APP_DYNAMIC_STALE_TIME_KEY];
	const dynamicStaleTimeSeconds = typeof dynamicStaleTime === "number" && Number.isFinite(dynamicStaleTime) && dynamicStaleTime >= 0 ? dynamicStaleTime : void 0;
	const sourcePage = Object.hasOwn(elements, "__srcPage") ? readSourcePageMetadata(elements[APP_SOURCE_PAGE_SEGMENTS_KEY]) : readSourcePageMetadata(elements[LEGACY_APP_SOURCE_PAGE_KEY]);
	const bfcacheSegmentIdentities = parseBfcacheSegmentIdentities(elements[APP_BFCACHE_SEGMENT_IDENTITIES_KEY]);
	return {
		artifactCompatibility,
		...cacheEntryReuseProof ? { cacheEntryReuseProof } : {},
		...dynamicStaleTimeSeconds === void 0 ? {} : { dynamicStaleTimeSeconds },
		interception,
		interceptionContext: interceptionContext ?? null,
		layoutIds,
		layoutFlags,
		routeId,
		rootLayoutTreePath,
		bfcacheSegmentIdentities,
		skippedLayoutIds,
		slotBindings,
		sourcePage
	};
}
var AppElementsWire = {
	keys: {
		artifactCompatibility: APP_ARTIFACT_COMPATIBILITY_KEY,
		cacheEntryReuseProof: APP_CACHE_ENTRY_REUSE_PROOF_KEY,
		dynamicStaleTime: APP_DYNAMIC_STALE_TIME_KEY,
		interception: APP_INTERCEPTION_KEY,
		interceptionContext: APP_INTERCEPTION_CONTEXT_KEY,
		layoutIds: APP_LAYOUT_IDS_KEY,
		layoutFlags: APP_LAYOUT_FLAGS_KEY,
		rootLayout: APP_ROOT_LAYOUT_KEY,
		route: APP_ROUTE_KEY,
		bfcacheSegmentIdentities: APP_BFCACHE_SEGMENT_IDENTITIES_KEY,
		skippedLayoutIds: APP_SKIPPED_LAYOUT_IDS_KEY,
		slotBindings: APP_SLOT_BINDINGS_KEY,
		sourcePageSegments: APP_SOURCE_PAGE_SEGMENTS_KEY
	},
	unmatchedSlotValue: APP_UNMATCHED_SLOT_WIRE_VALUE,
	createMetadataEntries: createAppElementsWireMetadataEntries,
	decode: normalizeAppElements,
	encodeCacheKey: createAppPayloadCacheKey,
	encodeLayoutId: createAppPayloadLayoutId,
	encodeOutgoingPayload: buildOutgoingAppPayload,
	encodePageId: createAppPayloadPageId,
	encodeRouteId: createAppPayloadRouteId,
	encodeSlotId: createAppPayloadSlotId,
	encodeTemplateId: createAppPayloadTemplateId,
	isSlotId: isAppElementsWireSlotId,
	parseElementKey: parseAppElementsWireElementKey,
	readMetadata: readAppElementsMetadata,
	withLayoutFlags
};
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-mounted-slots-header.js
/**
* Normalize the `x-vinext-mounted-slots` header for request handling and cache keying.
*
* The browser sends mounted slot ids as a space-separated list in the order slots were
* rendered, which changes across navigations. This normalizes to a canonical form
* (sorted, deduplicated) so equivalent slot sets map to the same RSC cache entry.
*
* Security: the value flows into the ISR RSC cache key (`appIsrRscKey`). Without
* bounds, an attacker who controls this header can fabricate unbounded distinct
* values to fan out KV writes (per-write billing) or fragment the cache. See
* `SECURITY-AUDIT-2026-05.md` finding F-PROD-1. The legitimate wire format is a
* whitespace-separated list of `slot:<name>:<treePath>` tokens (see
* `createAppPayloadSlotId` in `app-elements-wire.ts`); anything else is rejected.
*
* Bounds applied:
*   - Total raw header value capped at MAX_RAW_HEADER_LENGTH bytes (returns null
*     if exceeded so the request is treated as if the header were absent).
*   - Each token capped at MAX_TOKEN_LENGTH bytes.
*   - Token count capped at MAX_SLOT_TOKENS (extras are dropped after sort + dedup).
*   - Each token must match the legitimate slot-id shape, as defined by the
*     AppElements wire codec (`AppElementsWire.isSlotId`). Wire-format details
*     are intentionally kept inside the codec so this module does not duplicate
*     them. Malformed tokens are dropped silently rather than rejecting the
*     whole request — this matches the prior forgiving behavior for browsers
*     that send legitimate but stale formats during rolling deploys.
*
* Consumed by:
*   - app-rsc-request-normalization (request lifecycle, reads incoming header)
*   - app-elements (outgoing x-vinext-mounted-slots construction)
*   - isr-cache (RSC cache key generation)
*/
/** Hard cap on the raw header value byte length. Real values are <1 KB. */
var MAX_RAW_HEADER_LENGTH = 4096;
/** Hard cap on a single slot token byte length. */
var MAX_TOKEN_LENGTH = 256;
/** Hard cap on the number of slot tokens kept after normalization. */
var MAX_SLOT_TOKENS = 16;
/**
* Validate a single mounted-slot token. Shape validation is delegated to the
* AppElements wire codec so the wire format definition lives in exactly one
* place. This module only enforces the additional security cap on token byte
* length to bound cache-key cardinality.
*/
function isValidSlotToken(token) {
	if (token.length === 0 || token.length > MAX_TOKEN_LENGTH) return false;
	return AppElementsWire.isSlotId(token);
}
function normalizeMountedSlotsHeader(raw) {
	if (!raw) return null;
	if (raw.length > MAX_RAW_HEADER_LENGTH) return null;
	const validTokens = raw.split(/\s+/).filter((token) => token && isValidSlotToken(token));
	if (validTokens.length === 0) return null;
	return Array.from(new Set(validTokens)).sort().slice(0, MAX_SLOT_TOKENS).join(" ") || null;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-rsc-render-mode.js
var APP_RSC_RENDER_MODE_NAVIGATION = "navigation";
var APP_RSC_RENDER_MODE_PREFETCH_EMPTY = "prefetch-empty";
var APP_RSC_RENDER_MODE_PREFETCH_DYNAMIC_SHELL = "prefetch-dynamic-shell";
var APP_RSC_RENDER_MODE_PREFETCH_LOADING_SHELL = "prefetch-loading-shell";
function getRscRenderModeCacheVariant(mode) {
	if (mode === "prefetch-empty") return "prefetch-empty";
	if (mode === "prefetch-dynamic-shell") return "prefetch-dynamic-shell";
	if (mode === "prefetch-loading-shell") return "prefetch-loading-shell";
	return null;
}
function parseAppRscRenderMode(value) {
	switch (value) {
		case APP_RSC_RENDER_MODE_PREFETCH_EMPTY: return APP_RSC_RENDER_MODE_PREFETCH_EMPTY;
		case APP_RSC_RENDER_MODE_PREFETCH_DYNAMIC_SHELL: return APP_RSC_RENDER_MODE_PREFETCH_DYNAMIC_SHELL;
		case APP_RSC_RENDER_MODE_PREFETCH_LOADING_SHELL: return APP_RSC_RENDER_MODE_PREFETCH_LOADING_SHELL;
		default: return APP_RSC_RENDER_MODE_NAVIGATION;
	}
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-elements.js
var APP_PREFETCH_LOADING_SHELL_MARKER_KEY = "__prefetchLoadingShell";
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/encode-cache-tag.js
/**
* Cache-tag canonicalisation.
*
* Tags can flow into HTTP headers (e.g. `x-next-cache-tags` on ISR responses,
* Cloudflare cache-tag headers, downstream Worker code) where Node's
* `validateHeaderValue` rejects any byte outside `\t\x20-\x7e` and crashes
* the response with `ERR_INVALID_CHAR`. Even on platforms with permissive
* header setters, divergence between storage form and wire form silently
* breaks invalidation when a `revalidateTag` call's tag does not byte-match
* the form that was stored.
*
* The fix is to apply this encoding at every public boundary so storage,
* comparison, and the wire all see the same ASCII-safe form. The fast-path
* returns the input unchanged for already-ASCII tags (the common case), so
* pre-encoded `%xx` input round-trips losslessly without `decodeURIComponent`
* mangling literal `%xx` characters.
*
* The replacement matches *runs* of out-of-class code units rather than each
* code unit individually so surrogate pairs (emoji, non-BMP characters) are
* handed to `encodeURIComponent` as a complete code point — a per-code-unit
* regex would split the pair and throw `URIError`.
*
* Mirrors Next.js's `packages/next/src/server/lib/encode-cache-tag.ts`
* (introduced in vercel/next.js#93601).
*/
var OUT_OF_CLASS_CHAR = /[^\t\x20-\x7e]/;
var OUT_OF_CLASS_RUN = /[^\t\x20-\x7e]+/g;
function encodeCacheTag(tag) {
	return OUT_OF_CLASS_CHAR.test(tag) ? tag.replace(OUT_OF_CLASS_RUN, (run) => encodeURIComponent(run)) : tag;
}
function encodeCacheTags(tags) {
	return tags.map(encodeCacheTag);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/cache-request-state.js
var FALLBACK_KEY = Symbol.for("vinext.cache.fallback");
var globalState = globalThis;
var cacheAls = getOrCreateAls("vinext.cache.als");
var fallbackState = globalState[FALLBACK_KEY] ??= {
	actionRevalidationKind: 0,
	pendingRevalidatedTags: /* @__PURE__ */ new Set(),
	pendingRevalidations: /* @__PURE__ */ new Set(),
	requestScopedCacheLife: null,
	unstableCacheObservations: /* @__PURE__ */ new Map(),
	unstableCacheRevalidation: "foreground"
};
function getCacheState() {
	if (isInsideUnifiedScope()) return getRequestContext();
	return cacheAls.getStore() ?? fallbackState;
}
function hasRequestScopedCacheState() {
	if (isInsideUnifiedScope() || cacheAls.getStore() !== void 0) return true;
	const phase = getHeadersAccessPhase();
	return phase === "action" || phase === "route-handler";
}
/** @internal */
function _hasPendingRevalidatedTag(tags) {
	if (!hasRequestScopedCacheState()) return false;
	const pendingTags = getCacheState().pendingRevalidatedTags;
	return tags.some((tag) => pendingTags.has(tag));
}
/**
* Await and clear every cache invalidation queued in the current request.
* Clearing before awaiting also lets a later drain observe work enqueued by
* an async continuation while this batch is settling.
*
* @internal
*/
async function _drainPendingRevalidations() {
	const state = getCacheState();
	let didReject = false;
	let firstRejection;
	while (state.pendingRevalidations.size > 0) {
		const pending = [...state.pendingRevalidations];
		state.pendingRevalidations.clear();
		const results = await Promise.allSettled(pending);
		for (const result of results) if (result.status === "rejected" && !didReject) {
			didReject = true;
			firstRejection = result.reason;
		}
	}
	if (didReject) throw firstRejection;
}
function _setRequestScopedCacheLife(config) {
	const state = getCacheState();
	if (state.requestScopedCacheLife === null) {
		state.requestScopedCacheLife = { ...config };
		return;
	}
	if (config.stale !== void 0) state.requestScopedCacheLife.stale = state.requestScopedCacheLife.stale !== void 0 ? Math.min(state.requestScopedCacheLife.stale, config.stale) : config.stale;
	if (config.revalidate !== void 0) state.requestScopedCacheLife.revalidate = state.requestScopedCacheLife.revalidate !== void 0 ? Math.min(state.requestScopedCacheLife.revalidate, config.revalidate) : config.revalidate;
	if (config.expire !== void 0) state.requestScopedCacheLife.expire = state.requestScopedCacheLife.expire !== void 0 ? Math.min(state.requestScopedCacheLife.expire, config.expire) : config.expire;
}
function _peekRequestScopedCacheLife() {
	const config = getCacheState().requestScopedCacheLife;
	return config === null ? null : { ...config };
}
function _consumeRequestScopedCacheLife() {
	const state = getCacheState();
	const config = state.requestScopedCacheLife;
	state.requestScopedCacheLife = null;
	return config;
}
/**
* Capture access to the current request's cache-life slot for work that may
* finish after the AsyncLocalStorage request scope has returned. RSC response
* bodies are consumed by the server runtime later, so resolving the active
* store from a stream-finalization callback can otherwise read a detached
* context and lose cacheLife claims made while rendering the body.
*/
function _captureRequestScopedCacheLifeAccessors() {
	const state = getCacheState();
	return {
		consume() {
			const config = state.requestScopedCacheLife;
			state.requestScopedCacheLife = null;
			return config;
		},
		peek() {
			const config = state.requestScopedCacheLife;
			return config === null ? null : { ...config };
		}
	};
}
function _peekUnstableCacheObservations() {
	return [...getCacheState().unstableCacheObservations.values()].sort((a, b) => a.keyHash.localeCompare(b.keyHash));
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/fetch-cache.js
/**
* Extended fetch() with Next.js caching semantics.
*
* Patches `globalThis.fetch` during server rendering to support:
*
*   fetch(url, { next: { revalidate: 60, tags: ['posts'] } })
*   fetch(url, { cache: 'force-cache' })
*   fetch(url, { cache: 'no-store' })
*
* Cached responses are stored via the pluggable CacheHandler, so
* revalidateTag() and revalidatePath() invalidate fetch-level caches.
*
* Usage (in server entry):
*   import { withFetchCache, cleanupFetchCache } from './fetch-cache';
*   const cleanup = withFetchCache();
*   try { ... render ... } finally { cleanup(); }
*
* Or use the async helper:
*   await runWithFetchCache(async () => { ... render ... });
*/
/**
* Headers excluded from the cache key. These are W3C trace context headers
* that can break request caching and deduplication.
* All other headers ARE included in the cache key, matching Next.js behavior.
*/
var HEADER_BLOCKLIST = ["traceparent", "tracestate"];
var CACHE_KEY_PREFIX = "v4";
var MAX_CACHE_KEY_BODY_BYTES = 1024 * 1024;
var ONE_YEAR_SECONDS = 31536e3;
var BodyTooLargeForCacheKeyError = class extends Error {
	constructor() {
		super("Fetch body too large for cache key generation");
	}
};
var SkipCacheKeyGenerationError = class extends Error {
	constructor() {
		super("Fetch body could not be serialized for cache key generation");
	}
};
/**
* Collect all headers from the request, excluding the blocklist.
* RequestInit headers replace a Request input's headers rather than merging
* with them, matching the Request constructor's normalization behavior.
*/
function collectHeaders(input, init) {
	const headers = getEffectiveRequestHeaders(input, init);
	const collected = Object.fromEntries(headers.entries());
	for (const blocked of HEADER_BLOCKLIST) delete collected[blocked];
	return collected;
}
function getEffectiveRequestHeaders(input, init) {
	return init?.headers !== void 0 ? new Headers(init.headers) : input instanceof Request ? input.headers : new Headers();
}
/**
* Check whether a fetch request carries any per-user auth headers.
* Used for the safety bypass (skip caching when auth headers are present
* without an explicit cache opt-in).
*/
var AUTH_HEADERS = [
	"authorization",
	"cookie",
	"x-api-key"
];
function hasAuthHeaders(input, init) {
	const headers = collectHeaders(input, init);
	return AUTH_HEADERS.some((name) => name in headers);
}
var BYTE_HEX = Array.from({ length: 256 }, (_, value) => value.toString(16).padStart(2, "0"));
function encodeBodyBytes(bytes) {
	let encoded = "bytes:";
	for (const byte of bytes) encoded += BYTE_HEX[byte];
	return encoded;
}
function concatBodyBytes(chunks) {
	const length = chunks.reduce((total, chunk) => total + chunk.byteLength, 0);
	const bytes = new Uint8Array(length);
	let offset = 0;
	for (const chunk of chunks) {
		bytes.set(chunk, offset);
		offset += chunk.byteLength;
	}
	return bytes;
}
async function serializeFormData(formData, pushBodyChunk, getTotalBodyBytes) {
	const encoder = new TextEncoder();
	for (const [key, val] of formData.entries()) {
		if (typeof val === "string") {
			pushBodyChunk(JSON.stringify([key, {
				kind: "string",
				value: val
			}]));
			continue;
		}
		const metadataLowerBound = encoder.encode(key).byteLength + encoder.encode(val.name).byteLength + encoder.encode(val.type).byteLength;
		if (getTotalBodyBytes() + val.size + metadataLowerBound > MAX_CACHE_KEY_BODY_BYTES) throw new BodyTooLargeForCacheKeyError();
		const metadata = JSON.stringify([key, {
			kind: "file",
			name: val.name,
			type: val.type,
			value: "bytes:"
		}]);
		const metadataByteLength = encoder.encode(metadata).byteLength;
		if (getTotalBodyBytes() + val.size + metadataByteLength > MAX_CACHE_KEY_BODY_BYTES) throw new BodyTooLargeForCacheKeyError();
		const bytes = new Uint8Array(await val.arrayBuffer());
		pushBodyChunk(JSON.stringify([key, {
			kind: "file",
			name: val.name,
			type: val.type,
			value: encodeBodyBytes(bytes)
		}]), bytes.byteLength + metadataByteLength);
	}
}
function getParsedFormContentType(contentType) {
	const mediaType = contentType?.split(";")[0]?.trim().toLowerCase();
	if (mediaType === "multipart/form-data" || mediaType === "application/x-www-form-urlencoded") return mediaType;
}
function stripMultipartBoundary(contentType) {
	const [type, ...params] = contentType.split(";");
	const keptParams = params.map((param) => param.trim()).filter(Boolean).filter((param) => !/^boundary\s*=/i.test(param));
	const normalizedType = type.trim().toLowerCase();
	return keptParams.length > 0 ? `${normalizedType}; ${keptParams.join("; ")}` : normalizedType;
}
var NORMALIZED_FETCH_METHODS = /* @__PURE__ */ new Set([
	"DELETE",
	"GET",
	"HEAD",
	"OPTIONS",
	"POST",
	"PUT"
]);
function normalizeFetchMethod(method) {
	const upperMethod = method.toUpperCase();
	return NORMALIZED_FETCH_METHODS.has(upperMethod) ? upperMethod : method;
}
async function readRequestBodyChunksWithinLimit(request, effectiveHeaders) {
	const contentLengthHeader = effectiveHeaders.get("content-length");
	if (contentLengthHeader) {
		const contentLength = Number(contentLengthHeader);
		if (Number.isFinite(contentLength) && contentLength > MAX_CACHE_KEY_BODY_BYTES) throw new BodyTooLargeForCacheKeyError();
	}
	const requestClone = request.clone();
	const contentType = effectiveHeaders.get("content-type") ?? void 0;
	const reader = requestClone.body?.getReader();
	if (!reader) return {
		chunks: [],
		contentType
	};
	const chunks = [];
	let totalBodyBytes = 0;
	try {
		while (true) {
			const { done, value } = await reader.read();
			if (done) break;
			totalBodyBytes += value.byteLength;
			if (totalBodyBytes > MAX_CACHE_KEY_BODY_BYTES) throw new BodyTooLargeForCacheKeyError();
			chunks.push(value);
		}
	} catch (err) {
		reader.cancel().catch(() => {});
		throw err;
	}
	return {
		chunks,
		contentType
	};
}
/**
* Serialize request body into string chunks for cache key inclusion.
* Handles all body types: string, Uint8Array, ReadableStream, FormData, Blob,
* and Request object bodies.
* Returns the serialized body chunks and optionally stashes the original body
* on init as `_ogBody` so it can still be used after stream consumption.
*/
async function serializeBody(input, init) {
	if (!(init?.body !== void 0 && init.body !== null) && !(input instanceof Request && input.body)) return { bodyChunks: [] };
	const bodyChunks = [];
	const encoder = new TextEncoder();
	let totalBodyBytes = 0;
	let canonicalizedContentType;
	let defaultContentType;
	let bodyMetadata = "body-present";
	const hasEffectiveContentType = getEffectiveRequestHeaders(input, init).has("content-type");
	const pushBodyChunk = (chunk, byteLength = encoder.encode(chunk).byteLength) => {
		totalBodyBytes += byteLength;
		if (totalBodyBytes > MAX_CACHE_KEY_BODY_BYTES) throw new BodyTooLargeForCacheKeyError();
		bodyChunks.push(chunk);
	};
	const pushBodyBytes = (bytes) => {
		pushBodyChunk(encodeBodyBytes(bytes), bytes.byteLength);
	};
	const getTotalBodyBytes = () => totalBodyBytes;
	if (init?.body instanceof ArrayBuffer || init?.body && ArrayBuffer.isView(init.body)) {
		const bytes = init.body instanceof ArrayBuffer ? new Uint8Array(init.body) : new Uint8Array(init.body.buffer, init.body.byteOffset, init.body.byteLength);
		if (bytes.byteLength > MAX_CACHE_KEY_BODY_BYTES) throw new BodyTooLargeForCacheKeyError();
		pushBodyBytes(bytes);
		init._ogBody = init.body;
	} else if (init?.body && typeof init.body.getReader === "function") {
		const [bodyForHashing, bodyForFetch] = init.body.tee();
		init._ogBody = bodyForFetch;
		const reader = bodyForHashing.getReader();
		const chunks = [];
		try {
			while (true) {
				const { done, value } = await reader.read();
				if (done) break;
				const bytes = typeof value === "string" ? encoder.encode(value) : value;
				totalBodyBytes += bytes.byteLength;
				if (totalBodyBytes > MAX_CACHE_KEY_BODY_BYTES) throw new BodyTooLargeForCacheKeyError();
				chunks.push(bytes);
			}
			bodyChunks.push(encodeBodyBytes(concatBodyBytes(chunks)));
		} catch (err) {
			reader.cancel().catch(() => {});
			if (err instanceof BodyTooLargeForCacheKeyError) throw err;
			throw new SkipCacheKeyGenerationError();
		}
	} else if (init?.body instanceof URLSearchParams) {
		init._ogBody = init.body;
		pushBodyBytes(encoder.encode(init.body.toString()));
		if (!hasEffectiveContentType) defaultContentType = "application/x-www-form-urlencoded;charset=UTF-8";
	} else if (init?.body && typeof init.body.keys === "function") {
		const formData = init.body;
		init._ogBody = init.body;
		await serializeFormData(formData, pushBodyChunk, getTotalBodyBytes);
		if (!hasEffectiveContentType) {
			defaultContentType = "multipart/form-data";
			bodyMetadata = "body-present;valid-multipart-boundary";
		}
	} else if (init?.body && typeof init.body.arrayBuffer === "function") {
		const blob = init.body;
		if (blob.size > MAX_CACHE_KEY_BODY_BYTES) throw new BodyTooLargeForCacheKeyError();
		const arrayBuffer = await blob.arrayBuffer();
		pushBodyBytes(new Uint8Array(arrayBuffer));
		init._ogBody = new Blob([arrayBuffer], { type: blob.type });
		if (!hasEffectiveContentType) defaultContentType = blob.type || void 0;
	} else if (typeof init?.body === "string") {
		if (init.body.length > MAX_CACHE_KEY_BODY_BYTES) throw new BodyTooLargeForCacheKeyError();
		pushBodyBytes(encoder.encode(init.body));
		init._ogBody = init.body;
		if (!hasEffectiveContentType) defaultContentType = "text/plain;charset=UTF-8";
	} else if (input instanceof Request && input.body) {
		let chunks;
		let contentType;
		try {
			({chunks, contentType} = await readRequestBodyChunksWithinLimit(input, getEffectiveRequestHeaders(input, init)));
		} catch (err) {
			if (err instanceof BodyTooLargeForCacheKeyError) throw err;
			throw new SkipCacheKeyGenerationError();
		}
		const formContentType = getParsedFormContentType(contentType);
		if (formContentType) try {
			await serializeFormData(await new Request(input.url, {
				method: input.method,
				headers: contentType ? { "content-type": contentType } : void 0,
				body: new Blob(chunks)
			}).formData(), pushBodyChunk, getTotalBodyBytes);
			canonicalizedContentType = formContentType === "multipart/form-data" && contentType ? stripMultipartBoundary(contentType) : void 0;
			bodyMetadata = formContentType === "multipart/form-data" ? "body-present;valid-multipart-boundary" : "body-present";
			return {
				bodyChunks,
				canonicalizedContentType,
				bodyMetadata
			};
		} catch (err) {
			if (err instanceof BodyTooLargeForCacheKeyError) throw err;
			throw new SkipCacheKeyGenerationError();
		}
		pushBodyBytes(concatBodyBytes(chunks));
	}
	return {
		bodyChunks,
		canonicalizedContentType,
		defaultContentType,
		bodyMetadata
	};
}
/**
* Generate a deterministic cache key from a fetch request.
*
* Matches Next.js behavior: the key is a SHA-256 hash of a JSON array
* containing URL, method, all headers (minus blocklist), all RequestInit
* options, and the serialized body.
*/
async function buildFetchCacheKey(input, init) {
	let url;
	const inputRequest = input instanceof Request ? input : void 0;
	if (typeof input === "string") url = new Request(input).url;
	else if (input instanceof URL) url = new Request(input).url;
	else url = input.url;
	const method = normalizeFetchMethod(init?.method ?? inputRequest?.method ?? "GET");
	const headers = collectHeaders(input, init);
	const { bodyChunks, canonicalizedContentType, defaultContentType, bodyMetadata } = await serializeBody(input, init);
	if (canonicalizedContentType) headers["content-type"] = canonicalizedContentType;
	else if (defaultContentType && headers["content-type"] === void 0) headers["content-type"] = defaultContentType;
	const cacheString = JSON.stringify([
		CACHE_KEY_PREFIX,
		url,
		method,
		headers,
		init?.mode ?? inputRequest?.mode ?? "cors",
		init?.redirect ?? inputRequest?.redirect ?? "follow",
		init?.credentials ?? inputRequest?.credentials ?? "same-origin",
		init?.referrer ?? inputRequest?.referrer ?? "about:client",
		init?.referrerPolicy ?? inputRequest?.referrerPolicy ?? "",
		init?.integrity ?? inputRequest?.integrity ?? "",
		init?.cache ?? inputRequest?.cache ?? "default",
		bodyChunks,
		bodyMetadata
	]);
	const buffer = new TextEncoder().encode(cacheString);
	const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
	return Array.prototype.map.call(new Uint8Array(hashBuffer), (b) => b.toString(16).padStart(2, "0")).join("");
}
var _PENDING_KEY = Symbol.for("vinext.fetchCache.pendingRefetches");
var _gPending = globalThis;
var pendingRefetches = _gPending[_PENDING_KEY] ??= /* @__PURE__ */ new Map();
var DEDUP_TIMEOUT_MS = 6e4;
var _ORIG_FETCH_KEY = Symbol.for("vinext.fetchCache.originalFetch");
var _gFetch = globalThis;
var originalFetch = _gFetch[_ORIG_FETCH_KEY] ??= globalThis.fetch;
var _FALLBACK_KEY = Symbol.for("vinext.fetchCache.fallback");
var _g = globalThis;
var _als = getOrCreateAls("vinext.fetchCache.als");
var _noop = () => {};
var _responseBodyRegistry;
if (globalThis.FinalizationRegistry) _responseBodyRegistry = new FinalizationRegistry((weakRef) => {
	const stream = weakRef.deref();
	if (stream && !stream.locked) stream.cancel("Response object has been garbage collected").then(_noop, _noop);
});
var _fallbackState = _g[_FALLBACK_KEY] ??= {
	cacheableFetchUrls: /* @__PURE__ */ new Set(),
	currentRequestTags: [],
	currentFetchSoftTags: [],
	currentFetchCacheMode: null,
	currentForceDynamicFetchDefault: false,
	dynamicFetchUrls: /* @__PURE__ */ new Set(),
	refreshStaleFetchesInForeground: false,
	isFetchDedupeActive: false,
	currentFetchDedupeEntries: /* @__PURE__ */ new Map()
};
function _getState() {
	if (isInsideUnifiedScope()) return getRequestContext();
	return _als.getStore() ?? _fallbackState;
}
function getFetchObservationUrl(input) {
	return typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
}
function recordDynamicFetchObservation(input) {
	_getState().dynamicFetchUrls.add(getFetchObservationUrl(input));
}
function markUncachedFetchForPageOutput(input) {
	recordDynamicFetchObservation(input);
	markDynamicUsage();
}
function recordCacheableFetchObservation(input) {
	_getState().cacheableFetchUrls.add(getFetchObservationUrl(input));
}
function recordFiniteFetchRevalidate(revalidateSeconds) {
	if (Number.isFinite(revalidateSeconds) && revalidateSeconds > 0) _setRequestScopedCacheLife({ revalidate: revalidateSeconds });
}
function shouldRefreshStaleFetchInForeground() {
	return _getState().refreshStaleFetchesInForeground;
}
async function buildFetchCacheValue(response, tags, revalidateSeconds, options) {
	if (response.status !== 200) return null;
	const responseForCache = options?.cloneForReturn === false ? response : response.clone();
	const body = await responseForCache.text();
	const headers = {};
	responseForCache.headers.forEach((v, k) => {
		if (k.toLowerCase() === "set-cookie") return;
		headers[k] = v;
	});
	return {
		kind: "FETCH",
		data: {
			headers,
			body,
			url: response.url,
			status: responseForCache.status
		},
		tags,
		revalidate: revalidateSeconds
	};
}
async function writeFetchCacheResponse(handler, cacheKey, response, tags, revalidateSeconds, options) {
	const cacheValue = await buildFetchCacheValue(response, tags, revalidateSeconds, options);
	if (!cacheValue) return;
	await handler.set(cacheKey, cacheValue, {
		fetchCache: true,
		tags,
		revalidate: revalidateSeconds
	});
}
async function lowerFetchCacheRevalidateIfNeeded(handler, cacheKey, cachedValue, tags, revalidateSeconds) {
	if (!Number.isFinite(revalidateSeconds) || revalidateSeconds <= 0 || typeof cachedValue.revalidate !== "number" || cachedValue.revalidate <= revalidateSeconds) return;
	const mergedTags = Array.from(/* @__PURE__ */ new Set([...cachedValue.tags ?? [], ...tags]));
	const updatedValue = {
		...cachedValue,
		tags: mergedTags,
		revalidate: revalidateSeconds
	};
	await handler.set(cacheKey, updatedValue, {
		fetchCache: true,
		tags: mergedTags,
		revalidate: revalidateSeconds
	});
}
function peekCacheableFetchObservations() {
	return [..._getState().cacheableFetchUrls].sort();
}
function peekDynamicFetchObservations() {
	return [..._getState().dynamicFetchUrls].sort();
}
function consumeDynamicFetchObservations() {
	const state = _getState();
	const observed = [...state.dynamicFetchUrls].sort();
	state.dynamicFetchUrls = /* @__PURE__ */ new Set();
	return observed;
}
/**
* Get tags collected during the current render pass.
* Useful for associating page-level cache entries with all the
* fetch tags used during rendering.
*/
function getCollectedFetchTags() {
	return [..._getState().currentRequestTags];
}
/**
* Set path-derived implicit tags for fetch cache reads in the current render.
*
* These are intentionally not persisted on fetch entries. They mirror Next.js
* `softTags`: `revalidatePath()` should make a fetch miss while rendering the
* affected route, without permanently coupling a shared fetch entry to one path.
*/
function setCurrentFetchSoftTags(tags) {
	_getState().currentFetchSoftTags = [...tags];
}
function setCurrentFetchCacheMode(mode) {
	_getState().currentFetchCacheMode = mode;
}
function setCurrentForceDynamicFetchDefault(enabled) {
	_getState().currentForceDynamicFetchDefault = enabled;
}
function setRefreshStaleFetchesInForeground(enabled) {
	_getState().refreshStaleFetchesInForeground = enabled;
}
function isNoStoreFetch(cacheDirective, nextOpts) {
	return cacheDirective === "no-store" || cacheDirective === "no-cache" || nextOpts?.revalidate === 0;
}
function isCacheableFetch(cacheDirective, nextOpts) {
	return cacheDirective === "force-cache" || nextOpts?.revalidate === false || typeof nextOpts?.revalidate === "number" && nextOpts.revalidate > 0;
}
function hasExplicitRevalidateValue(nextOpts) {
	return nextOpts?.revalidate !== void 0;
}
function isFalsyRevalidate(nextOpts) {
	return !nextOpts?.revalidate;
}
function resolveSegmentCacheDirective(cacheDirective, nextOpts, mode, forceDynamicFetchDefault) {
	if (forceDynamicFetchDefault && (!mode || mode === "auto") && (cacheDirective === void 0 || cacheDirective === "default") && isFalsyRevalidate(nextOpts)) return "no-store";
	if (!mode || mode === "auto") return cacheDirective;
	switch (mode) {
		case "force-cache": return "force-cache";
		case "force-no-store": return "no-store";
		case "only-cache":
			if (isNoStoreFetch(cacheDirective, nextOpts)) throw new Error("Route segment config `fetchCache = \"only-cache\"` conflicts with no-store fetch.");
			return cacheDirective ?? "force-cache";
		case "only-no-store":
			if (isCacheableFetch(cacheDirective, nextOpts)) throw new Error("Route segment config `fetchCache = \"only-no-store\"` conflicts with cacheable fetch.");
			return cacheDirective ?? "no-store";
		case "default-cache": return cacheDirective ?? (hasExplicitRevalidateValue(nextOpts) ? void 0 : "force-cache");
		case "default-no-store": return cacheDirective ?? (hasExplicitRevalidateValue(nextOpts) ? void 0 : "no-store");
	}
	return cacheDirective;
}
function getFetchCacheDirective(input, init) {
	if (init?.cache !== void 0) return init.cache;
	if (!(input instanceof Request) || input.cache === "default") return;
	return input.cache;
}
function buildFetchDedupeKey(request) {
	const filteredHeaders = Array.from(request.headers.entries()).filter(([key]) => !HEADER_BLOCKLIST.includes(key.toLowerCase()));
	return JSON.stringify([
		request.method,
		filteredHeaders,
		request.mode,
		request.redirect,
		request.credentials,
		request.referrer,
		request.referrerPolicy,
		request.integrity
	]);
}
function createFetchDedupeCandidate(input, init) {
	if (init?.signal) return null;
	const method = (init?.method ?? (input instanceof Request ? input.method : "GET")).toUpperCase();
	if (method !== "GET" && method !== "HEAD") return null;
	if (init?.keepalive) return null;
	const request = input instanceof Request && !init ? input : new Request(input, init);
	if (request.method !== "GET" && request.method !== "HEAD" || request.keepalive) return null;
	return {
		url: request.url,
		key: buildFetchDedupeKey(request)
	};
}
function buildDedupeClone(body, source) {
	const cloned = new Response(body, {
		status: source.status,
		statusText: source.statusText,
		headers: new Headers(source.headers)
	});
	Object.defineProperty(cloned, "url", {
		value: source.url,
		configurable: true,
		enumerable: true,
		writable: false
	});
	if (_responseBodyRegistry && cloned.body) _responseBodyRegistry.register(cloned, new WeakRef(cloned.body));
	return cloned;
}
function cloneDedupeResponse(response) {
	if (!response.body) return [buildDedupeClone(null, response), buildDedupeClone(null, response)];
	const [body1, body2] = response.body.tee();
	return [buildDedupeClone(body1, response), buildDedupeClone(body2, response)];
}
function buildCachedFetchResponse(data, input) {
	const response = new Response(data.body, {
		status: data.status ?? 200,
		headers: data.headers
	});
	Object.defineProperty(response, "url", {
		value: data.url ?? getFetchObservationUrl(input),
		configurable: true,
		enumerable: true,
		writable: false
	});
	if (_responseBodyRegistry && response.body) _responseBodyRegistry.register(response, new WeakRef(response.body));
	return response;
}
function dedupeFetch(input, init) {
	const state = _getState();
	if (!state.isFetchDedupeActive) return originalFetch(input, init);
	const candidate = createFetchDedupeCandidate(input, init);
	if (!candidate) return originalFetch(input, init);
	const entriesByUrl = state.currentFetchDedupeEntries;
	let entries = entriesByUrl.get(candidate.url);
	if (!entries) {
		entries = [];
		entriesByUrl.set(candidate.url, entries);
	}
	for (const entry of entries) {
		if (entry.key !== candidate.key) continue;
		return entry.promise.then(() => {
			if (!entry.response) throw new Error("[vinext] Missing deduped fetch response");
			const [responseForCaller, responseForFutureCaller] = cloneDedupeResponse(entry.response);
			entry.response = responseForFutureCaller;
			return responseForCaller;
		});
	}
	const promise = originalFetch(input, init);
	const entry = {
		key: candidate.key,
		promise,
		response: null
	};
	entries.push(entry);
	return promise.then((response) => {
		const [responseForCaller, responseForFutureCaller] = cloneDedupeResponse(response);
		entry.response = responseForFutureCaller;
		return responseForCaller;
	}, (err) => {
		const idx = entries.indexOf(entry);
		if (idx !== -1) entries.splice(idx, 1);
		throw err;
	});
}
/**
* Create a patched fetch function with Next.js caching semantics.
*
* The patched fetch:
* 1. Checks `cache` and `next` options to determine caching behavior
* 2. On cache hit, returns the cached response without hitting the network
* 3. On cache miss, fetches from network, stores in cache, returns response
* 4. Respects `next.revalidate` for TTL-based revalidation
* 5. Respects `next.tags` for tag-based invalidation via revalidateTag()
*/
function createPatchedFetch() {
	return async function patchedFetch(input, init) {
		const nextOpts = init?.next;
		const cacheDirective = resolveSegmentCacheDirective(getFetchCacheDirective(input, init), nextOpts, _getState().currentFetchCacheMode, _getState().currentForceDynamicFetchDefault);
		if (!nextOpts && !cacheDirective) {
			recordDynamicFetchObservation(input);
			return dedupeFetch(input, init);
		}
		if (cacheDirective === "no-store" || cacheDirective === "no-cache" || nextOpts?.revalidate === 0) {
			const cleanInit = stripNextFromInit(init, cacheDirective);
			markUncachedFetchForPageOutput(input);
			return dedupeFetch(input, cleanInit);
		}
		if (!(cacheDirective === "force-cache" || nextOpts?.revalidate === false || typeof nextOpts?.revalidate === "number" && nextOpts.revalidate > 0) && hasAuthHeaders(input, init)) {
			const cleanInit = stripNextFromInit(init, cacheDirective);
			recordDynamicFetchObservation(input);
			return dedupeFetch(input, cleanInit);
		}
		let revalidateSeconds;
		if (cacheDirective === "force-cache") revalidateSeconds = nextOpts?.revalidate && typeof nextOpts.revalidate === "number" ? nextOpts.revalidate : ONE_YEAR_SECONDS;
		else if (nextOpts?.revalidate === false) revalidateSeconds = ONE_YEAR_SECONDS;
		else if (typeof nextOpts?.revalidate === "number" && nextOpts.revalidate > 0) revalidateSeconds = nextOpts.revalidate;
		else if (nextOpts?.tags && nextOpts.tags.length > 0) revalidateSeconds = ONE_YEAR_SECONDS;
		else {
			const cleanInit = stripNextFromInit(init, cacheDirective);
			recordDynamicFetchObservation(input);
			return dedupeFetch(input, cleanInit);
		}
		recordCacheableFetchObservation(input);
		recordFiniteFetchRevalidate(revalidateSeconds);
		const reqTags = _getState().currentRequestTags;
		const tags = encodeCacheTags(nextOpts?.tags ?? []);
		if (tags.length > 0) {
			for (const tag of tags) if (!reqTags.includes(tag)) reqTags.push(tag);
		}
		const softTags = _getState().currentFetchSoftTags;
		let fetchInit = stripNextFromInit(init, cacheDirective);
		let cacheKey;
		try {
			cacheKey = await buildFetchCacheKey(input, fetchInit);
			fetchInit = stripNextFromInit(fetchInit, cacheDirective);
		} catch (err) {
			if (err instanceof BodyTooLargeForCacheKeyError || err instanceof SkipCacheKeyGenerationError) {
				fetchInit = stripNextFromInit(fetchInit, cacheDirective);
				recordDynamicFetchObservation(input);
				return dedupeFetch(input, fetchInit);
			}
			throw err;
		}
		const handler = getDataCacheHandler();
		let mustBypassPendingRevalidation = _hasPendingRevalidatedTag([...tags, ...softTags]);
		try {
			let cached = mustBypassPendingRevalidation ? null : await handler.get(cacheKey, {
				kind: "FETCH",
				tags,
				softTags,
				revalidate: revalidateSeconds
			});
			if (cached?.value?.kind === "FETCH" && _hasPendingRevalidatedTag([
				...cached.value.tags ?? [],
				...tags,
				...softTags
			])) {
				mustBypassPendingRevalidation = true;
				cached = null;
			}
			if (cached?.value && cached.value.kind === "FETCH" && cached.cacheState !== "stale") {
				await lowerFetchCacheRevalidateIfNeeded(handler, cacheKey, cached.value, tags, revalidateSeconds);
				const cachedData = cached.value.data;
				return buildCachedFetchResponse(cachedData, input);
			}
			if (cached?.value && cached.value.kind === "FETCH" && cached.cacheState === "stale") {
				if (shouldRefreshStaleFetchInForeground()) {
					const freshResponse = await dedupeFetch(input, fetchInit);
					await writeFetchCacheResponse(handler, cacheKey, freshResponse, tags, revalidateSeconds);
					return freshResponse;
				}
				const staleData = cached.value.data;
				if (!pendingRefetches.has(cacheKey)) {
					const refetchPromise = originalFetch(input, fetchInit).then(async (freshResp) => {
						await writeFetchCacheResponse(handler, cacheKey, freshResp, tags, revalidateSeconds, { cloneForReturn: false });
					}).catch((err) => {
						const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
						console.error(`[vinext] fetch cache background revalidation failed for ${url} (key=${cacheKey.slice(0, 12)}...):`, err);
					}).finally(() => {
						if (pendingRefetches.get(cacheKey) === refetchPromise) pendingRefetches.delete(cacheKey);
						clearTimeout(timeoutId);
					});
					pendingRefetches.set(cacheKey, refetchPromise);
					const timeoutId = setTimeout(() => {
						if (pendingRefetches.get(cacheKey) === refetchPromise) pendingRefetches.delete(cacheKey);
					}, DEDUP_TIMEOUT_MS);
					getRequestExecutionContext()?.waitUntil(refetchPromise);
				}
				return buildCachedFetchResponse(staleData, input);
			}
		} catch (cacheErr) {
			console.error("[vinext] fetch cache read error:", cacheErr);
		}
		const response = await (mustBypassPendingRevalidation ? originalFetch(input, fetchInit) : dedupeFetch(input, fetchInit));
		const cacheValue = await buildFetchCacheValue(response, tags, revalidateSeconds);
		if (cacheValue) handler.set(cacheKey, cacheValue, {
			fetchCache: true,
			tags,
			revalidate: revalidateSeconds
		}).catch((err) => {
			console.error("[vinext] fetch cache write error:", err);
		});
		return response;
	};
}
/**
* Strip the `next` property from RequestInit before passing to real fetch.
* The `next` property is not a standard fetch option and would cause warnings
* in some environments.
*/
function stripNextFromInit(init, cacheOverride) {
	if (!init) return cacheOverride === void 0 ? void 0 : { cache: cacheOverride };
	const { next: _next, _ogBody, ...rest } = init;
	if (cacheOverride !== void 0) rest.cache = cacheOverride;
	if (_ogBody !== void 0) rest.body = _ogBody;
	return Object.keys(rest).length > 0 ? rest : void 0;
}
var _PATCH_KEY = Symbol.for("vinext.fetchCache.patchInstalled");
function _ensurePatchInstalled() {
	if (_g[_PATCH_KEY]) return;
	_g[_PATCH_KEY] = true;
	globalThis.fetch = createPatchedFetch();
}
function runWithFetchDedupe(fn) {
	_ensurePatchInstalled();
	const state = _getState();
	if (state.isFetchDedupeActive) return fn();
	if (isInsideUnifiedScope()) return runWithUnifiedStateMutation((uCtx) => {
		uCtx.isFetchDedupeActive = true;
		uCtx.currentFetchDedupeEntries = /* @__PURE__ */ new Map();
	}, fn);
	return _als.run({
		...state,
		isFetchDedupeActive: true,
		currentFetchDedupeEntries: /* @__PURE__ */ new Map()
	}, fn);
}
/**
* Install the patched fetch without creating a standalone ALS scope.
*
* `runWithFetchCache()` is the standalone helper: it installs the patch and
* creates an isolated per-request tag store. The unified request context owns
* that isolation itself via `currentRequestTags`, so callers inside
* `runWithRequestContext()` only need the process-global fetch monkey-patch.
*/
function ensureFetchPatch() {
	_ensurePatchInstalled();
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/deployment-id.js
function getDeploymentId() {}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-rsc-cache-busting.js
/**
* RSC cache-busting hashes cover the headers that make an RSC payload vary.
* Client-side variant headers must survive transit through CDNs and reverse
* proxies; stripping them changes the server hash and turns stale URLs into
* repeated canonicalization redirects.
*/
var VINEXT_RSC_CACHE_BUSTING_SEARCH_PARAM = "_rsc";
var VINEXT_RSC_COMPATIBILITY_ID_HEADER = "X-Vinext-RSC-Compatibility-Id";
var VINEXT_RSC_CONTENT_TYPE = "text/x-component";
var VINEXT_RSC_VARY_HEADER = [
	"RSC",
	NEXT_ROUTER_STATE_TREE_HEADER,
	NEXT_ROUTER_PREFETCH_HEADER,
	NEXT_ROUTER_SEGMENT_PREFETCH_HEADER,
	NEXT_URL_HEADER,
	VINEXT_INTERCEPTION_CONTEXT_HEADER,
	VINEXT_MOUNTED_SLOTS_HEADER,
	VINEXT_RSC_RENDER_MODE_HEADER
].join(", ");
var CACHE_BUSTING_DIGEST_BYTES = 12;
var textEncoder = new TextEncoder();
function encodeBase64Url(bytes) {
	let binary = "";
	for (const byte of bytes) binary += String.fromCharCode(byte);
	return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
}
function normalizeHeaderValue(value) {
	return value ?? "0";
}
function normalizeCompatibilityId(value) {
	return value && value.length > 0 ? value : null;
}
function getVinextRscCompatibilityId() {
	return normalizeCompatibilityId("226b8b94-6582-4f59-a2b3-58ff91ffc2e5");
}
function applyRscCompatibilityIdHeader(headers, compatibilityId = getVinextRscCompatibilityId()) {
	const normalized = normalizeCompatibilityId(compatibilityId);
	if (normalized) headers.set(VINEXT_RSC_COMPATIBILITY_ID_HEADER, normalized);
	else headers.delete(VINEXT_RSC_COMPATIBILITY_ID_HEADER);
}
function applyRscDeploymentIdHeader(headers) {
	headers.delete(NEXTJS_DEPLOYMENT_ID_HEADER);
}
function normalizeRenderModeHeaderValue(value) {
	const renderMode = parseAppRscRenderMode(value);
	return renderMode === "navigation" ? null : renderMode;
}
function createCacheBustingInput(headers, options = {}) {
	const values = [
		headers.get(NEXT_ROUTER_PREFETCH_HEADER),
		headers.get(NEXT_ROUTER_SEGMENT_PREFETCH_HEADER),
		headers.get(NEXT_ROUTER_STATE_TREE_HEADER),
		headers.get(NEXT_URL_HEADER),
		headers.get(VINEXT_INTERCEPTION_CONTEXT_HEADER),
		headers.get(VINEXT_MOUNTED_SLOTS_HEADER),
		...options.includeRenderModeHeader === false ? [] : [normalizeRenderModeHeaderValue(headers.get(VINEXT_RSC_RENDER_MODE_HEADER))]
	];
	if (values.every((value) => value === null)) return null;
	return values.map(normalizeHeaderValue).join(",");
}
async function sha256CacheBustingHash(input) {
	const digest = await globalThis.crypto.subtle.digest("SHA-256", textEncoder.encode(input));
	return encodeBase64Url(new Uint8Array(digest).subarray(0, CACHE_BUSTING_DIGEST_BYTES));
}
function computeLegacyRscCacheBustingSearchParam(headers) {
	const input = createCacheBustingInput(headers);
	return input === null ? "" : fnv1a64(input);
}
async function computePreviousRscCacheBustingSearchParam(headers) {
	const input = createCacheBustingInput(headers, { includeRenderModeHeader: false });
	if (input === null) return null;
	return sha256CacheBustingHash(input);
}
function computePreviousLegacyRscCacheBustingSearchParam(headers) {
	const input = createCacheBustingInput(headers, { includeRenderModeHeader: false });
	return input === null ? null : fnv1a64(input);
}
function getSearchPairsWithoutRscCacheBusting(url) {
	return (url.search.startsWith("?") ? url.search.slice(1) : url.search).split("&").filter((pair) => pair.length > 0 && !isRscCacheBustingSearchPair(pair));
}
function isRscCacheBustingSearchPair(pair) {
	const separatorIndex = pair.indexOf("=");
	const rawKey = separatorIndex === -1 ? pair : pair.slice(0, separatorIndex);
	try {
		return decodeURIComponent(rawKey.replaceAll("+", " ")) === VINEXT_RSC_CACHE_BUSTING_SEARCH_PARAM;
	} catch {
		return rawKey === VINEXT_RSC_CACHE_BUSTING_SEARCH_PARAM;
	}
}
/**
* Detect the internal RSC cache-busting search param using the same
* encoding-aware matching as `stripRscCacheBustingSearchParam`
* (`isRscCacheBustingSearchPair`). The two share a single matcher so a guard
* built on this helper and the stripper can never disagree on which pairs
* count as `_rsc`, including encoded-key edge cases like `%5Frsc`.
*/
function hasRscCacheBustingSearchParam(url) {
	return (url.search.startsWith("?") ? url.search.slice(1) : url.search).split("&").some((pair) => pair.length > 0 && isRscCacheBustingSearchPair(pair));
}
async function computeRscCacheBustingSearchParam(headers) {
	const input = createCacheBustingInput(headers);
	if (input === null) return "";
	return sha256CacheBustingHash(input);
}
function setRscCacheBustingSearchParam(url, hash) {
	const pairs = getSearchPairsWithoutRscCacheBusting(url);
	pairs.push(hash.length > 0 ? `${VINEXT_RSC_CACHE_BUSTING_SEARCH_PARAM}=${hash}` : VINEXT_RSC_CACHE_BUSTING_SEARCH_PARAM);
	url.search = `?${pairs.join("&")}`;
}
function stripRscCacheBustingSearchParam(url) {
	const pairs = getSearchPairsWithoutRscCacheBusting(url);
	url.search = pairs.length > 0 ? `?${pairs.join("&")}` : "";
}
/**
* Remove a trailing `.rsc` suffix from a pathname. Returns the pathname
* unchanged when the suffix is absent.
*/
function stripRscSuffix(pathname) {
	return pathname.endsWith(".rsc") ? pathname.slice(0, -4) : pathname;
}
function toRscRequestPath(href) {
	const hashIndex = href.indexOf("#");
	return hashIndex === -1 ? href : href.slice(0, hashIndex);
}
async function createRscRequestUrl(href, headers) {
	const url = new URL(toRscRequestPath(href), "http://vinext.local");
	setRscCacheBustingSearchParam(url, await computeRscCacheBustingSearchParam(headers));
	return `${url.pathname}${url.search}`;
}
async function createRscRedirectLocation(location, request) {
	const requestUrl = new URL(request.url);
	const destinationUrl = new URL(location, requestUrl);
	if (destinationUrl.origin !== requestUrl.origin) return destinationUrl.toString();
	const rscPath = await createRscRequestUrl(`${destinationUrl.pathname}${destinationUrl.search}`, request.headers);
	return `${destinationUrl.origin}${rscPath}`;
}
async function resolveInvalidRscCacheBustingRequest(options) {
	if (!options.isRscRequest || options.request.method !== "GET" && options.request.method !== "HEAD") return null;
	const url = new URL(options.request.url);
	const actualHash = url.searchParams.get(VINEXT_RSC_CACHE_BUSTING_SEARCH_PARAM);
	const expectedHash = await computeRscCacheBustingSearchParam(options.request.headers);
	if (actualHash === null && expectedHash === "" && url.pathname.endsWith(".rsc")) return null;
	const acceptedHashes = /* @__PURE__ */ new Set([expectedHash]);
	if (actualHash !== null && actualHash !== expectedHash) {
		acceptedHashes.add(computeLegacyRscCacheBustingSearchParam(options.request.headers));
		if (normalizeRenderModeHeaderValue(options.request.headers.get("X-Vinext-Rsc-Render-Mode")) === null) {
			const previousHash = await computePreviousRscCacheBustingSearchParam(options.request.headers);
			const previousLegacyHash = computePreviousLegacyRscCacheBustingSearchParam(options.request.headers);
			if (previousHash !== null) acceptedHashes.add(previousHash);
			if (previousLegacyHash !== null) acceptedHashes.add(previousLegacyHash);
		}
	}
	if (actualHash !== null && acceptedHashes.has(actualHash)) return null;
	setRscCacheBustingSearchParam(url, expectedHash);
	return new Response(null, {
		status: 307,
		headers: { Location: `${url.pathname}${url.search}` }
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/middleware-response-headers.js
var ADDITIVE_RESPONSE_HEADER_NAMES = /* @__PURE__ */ new Set(["set-cookie", "vary"]);
function mergeVaryHeader(target, value) {
	const existing = target.get("Vary");
	const tokens = (existing ? `${existing}, ${value}` : value).split(",").map((token) => token.trim()).filter((token) => token.length > 0);
	if (tokens.some((token) => token === "*")) {
		target.set("Vary", "*");
		return;
	}
	const seen = /* @__PURE__ */ new Set();
	const merged = [];
	for (const token of tokens) {
		const normalized = token.toLowerCase();
		if (seen.has(normalized)) continue;
		seen.add(normalized);
		merged.push(token);
	}
	target.set("Vary", merged.join(", "));
}
/**
* Merge middleware response headers into a target Headers object.
*
* Set-Cookie and Vary are accumulated (append) since multiple sources can
* contribute values. All other headers use set() so middleware owns singular
* response headers like Cache-Control.
*/
function mergeMiddlewareResponseHeaders(target, middlewareHeaders) {
	if (!middlewareHeaders) return;
	for (const [key, value] of middlewareHeaders) {
		if (key.toLowerCase() === "vary") {
			mergeVaryHeader(target, value);
			continue;
		}
		if (ADDITIVE_RESPONSE_HEADER_NAMES.has(key.toLowerCase())) {
			target.append(key, value);
			continue;
		}
		target.set(key, value);
	}
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/cache-control.js
var NEVER_CACHE_CONTROL = "private, no-cache, no-store, max-age=0, must-revalidate";
var BROWSER_REVALIDATE_CACHE_CONTROL = "public, max-age=0, must-revalidate";
var STATIC_CACHE_CONTROL = "s-maxage=31536000, stale-while-revalidate";
var STALE_REVALIDATE_CACHE_CONTROL = "s-maxage=0, stale-while-revalidate";
var NO_STORE_CACHE_CONTROL = "no-store, must-revalidate";
var SHARED_CACHE_DIRECTIVE_RE = /(?:^|,)\s*s-maxage\s*=/i;
function shouldUseNextDeployCacheControl() {
	return process.env.VINEXT_NEXT_DEPLOY_CACHE_CONTROL === "1";
}
function isSharedCacheControl(cacheControl) {
	return SHARED_CACHE_DIRECTIVE_RE.test(cacheControl);
}
/**
* Route a cacheable response's headers through the active CDN cache adapter and
* apply the result to `headers`. The default adapter yields a single
* `Cache-Control` identical to `input.cacheControl` (no behavior change); edge
* adapters may instead emit `CDN-Cache-Control` / `Cache-Tag`.
*
* We only clear `Cache-Control` — the one header vinext stamps internally — so
* a stale vinext value never lingers if an adapter chooses not to emit one. The
* adapter's own headers are applied via `set()`, which overrides prior values
* for names it emits. Callers that must also discard provider-specific headers
* before the adapter recomputes policy clear those explicitly.
*/
function applyCdnResponseHeaders(headers, input) {
	headers.delete("Cache-Control");
	if (shouldUseNextDeployCacheControl() && isSharedCacheControl(input.cacheControl)) {
		headers.set("Cache-Control", BROWSER_REVALIDATE_CACHE_CONTROL);
		return;
	}
	const map = getCdnCacheAdapter().buildResponseHeaders(input);
	for (const [name, value] of Object.entries(map)) {
		if (value === null) {
			headers.delete(name);
			continue;
		}
		if (value === "") continue;
		headers.set(name, value);
	}
}
/**
* Matches Next.js's `getCacheControlHeader` stale window semantics while
* preserving vinext's legacy unbounded SWR header when no expire ceiling is
* available yet.
*
* Next.js source:
* https://github.com/vercel/next.js/blob/canary/packages/next/src/server/lib/cache-control.ts
*/
function buildRevalidateCacheControl(revalidateSeconds, expireSeconds) {
	if (revalidateSeconds === false) return STATIC_CACHE_CONTROL;
	if (expireSeconds === void 0) return `s-maxage=${revalidateSeconds}, stale-while-revalidate`;
	if (revalidateSeconds >= expireSeconds) return `s-maxage=${revalidateSeconds}`;
	return `s-maxage=${revalidateSeconds}, stale-while-revalidate=${expireSeconds - revalidateSeconds}`;
}
/**
* Builds Cache-Control for ISR cache reads. HIT responses and STALE responses
* with stored expire metadata use the same route policy because Next.js derives
* this header from cache-control metadata, not from the cache hit/stale state.
* STALE entries without expire metadata keep vinext's legacy `s-maxage=0`
* fallback so older cache entries are not treated as newly fresh downstream.
*/
function buildCachedRevalidateCacheControl(cacheState, revalidateSeconds, expireSeconds) {
	if (revalidateSeconds === false || revalidateSeconds === Infinity) return STATIC_CACHE_CONTROL;
	if (cacheState === "STALE" && expireSeconds === void 0) return STALE_REVALIDATE_CACHE_CONTROL;
	return buildRevalidateCacheControl(revalidateSeconds, expireSeconds);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/cache-headers.js
function toNextJsCacheState(cacheState) {
	return cacheState === "STATIC" ? "HIT" : cacheState;
}
function setCacheStateHeaders(headers, cacheState) {
	headers.set(VINEXT_CACHE_HEADER, cacheState);
	headers.set(NEXTJS_CACHE_HEADER, toNextJsCacheState(cacheState));
}
//#endregion
export { invokeAppComponent as $, setRefreshStaleFetchesInForeground as A, runWithHeadersContext as At, APP_RSC_RENDER_MODE_PREFETCH_EMPTY as B, getUnconsumedMiddlewareRequestHeaders as Bt, getCollectedFetchTags as C, headersContextFromRequest as Ct, setCurrentFetchCacheMode as D, peekDynamicUsage as Dt, runWithFetchDedupe as E, markRenderRequestApiUsage as Et, _peekUnstableCacheObservations as F, throwIfStaticGenerationAccessError as Ft, APP_LAYOUT_IDS_KEY as G, getRscRenderModeCacheVariant as H, parseEdgeRequestCookieHeader as Ht, encodeCacheTag as I, createPprFallbackShellSuspensePromiseForState as It, AppElementsWire as J, APP_ROOT_LAYOUT_KEY as K, APP_PREFETCH_LOADING_SHELL_MARKER_KEY as L, getPprFallbackShellState as Lt, _consumeRequestScopedCacheLife as M, setHeadersAccessPhase as Mt, _drainPendingRevalidations as N, setHeadersContext as Nt, setCurrentFetchSoftTags as O, peekRenderRequestApiUsage as Ot, _peekRequestScopedCacheLife as P, throwIfInsideCacheScope as Pt, createAppRenderDependency as Q, APP_RSC_RENDER_MODE_NAVIGATION as R, validateCookieName as Rt, ensureFetchPatch as S, getHeadersContext as St, peekDynamicFetchObservations as T, markDynamicUsage as Tt, parseAppRscRenderMode as U, configureMemoryCacheHandler as Ut, APP_RSC_RENDER_MODE_PREFETCH_LOADING_SHELL as V, parseCookieHeader as Vt, normalizeMountedSlotsHeader as W, resolveClientStaleTimeSeconds as Wt, normalizeAppElementsSlotBindings as X, isAppElementsRecord as Y, createAppPageRenderDependency as Z, resolveInvalidRscCacheBustingRequest as _, consumeInvalidDynamicUsageError as _t, applyCdnResponseHeaders as a, isPromiseLike as at, getDeploymentId as b, getAndClearPendingCookies as bt, mergeMiddlewareResponseHeaders as c, createArtifactCompatibilityGraphVersion as ct, VINEXT_RSC_CONTENT_TYPE as d, fnv1a64 as dt, isAppRenderSuspension as et, VINEXT_RSC_VARY_HEADER as f, getCdnCacheAdapter as ft, hasRscCacheBustingSearchParam as g, consumeDynamicUsage as gt, createRscRedirectLocation as h, getRequestExecutionContext as ht, STATIC_CACHE_CONTROL as i, renderAppComponentWithDependencyBarrier as it, _captureRequestScopedCacheLifeAccessors as j, runWithIsolatedDynamicUsage as jt, setCurrentForceDynamicFetchDefault as k, runWithConnectionProbe as kt, mergeVaryHeader as l, evaluateArtifactCompatibility as lt, applyRscDeploymentIdHeader as m, normalizePath as mt, NEVER_CACHE_CONTROL as n, registerAppElementRenderDependencies as nt, buildCachedRevalidateCacheControl as o, ARTIFACT_COMPATIBILITY_PROOF_FIELDS as ot, applyRscCompatibilityIdHeader as p, isInterceptionMatchedUrlPath as pt, APP_STATIC_SIBLINGS_KEY as q, NO_STORE_CACHE_CONTROL as r, renderAfterAppDependencies as rt, buildRevalidateCacheControl as s, createArtifactCompatibilityEnvelope as st, setCacheStateHeaders as t, isReactOwnedAppComponent as tt, VINEXT_RSC_CACHE_BUSTING_SEARCH_PARAM as u, parseArtifactCompatibilityEnvelope as ut, stripRscCacheBustingSearchParam as v, consumeRenderRequestApiUsage as vt, peekCacheableFetchObservations as w, isDraftModeRequest as wt, consumeDynamicFetchObservations as x, getDraftModeCookieHeader as xt, stripRscSuffix as y, getActiveDraftModeState as yt, APP_RSC_RENDER_MODE_PREFETCH_DYNAMIC_SHELL as z, buildRequestHeadersFromMiddlewareResponse as zt };
