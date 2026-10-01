import * as __viteRscAsyncHooks from "node:async_hooks";
import { AsyncLocalStorage } from "node:async_hooks";
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/record.js
function isUnknownRecord(value) {
	return value !== null && typeof value === "object" && !Array.isArray(value);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/internal/als-registry.js
globalThis.AsyncLocalStorage = __viteRscAsyncHooks.AsyncLocalStorage;
/**
* Shared helper for registering AsyncLocalStorage instances on `globalThis`
* via `Symbol.for(...)` so that they survive multiple module instances.
*
* Why this helper exists
* ----------------------
* Vite's multi-environment setup (RSC / SSR / client) and HMR can load a
* single source module under several different specifiers, producing more
* than one module instance at runtime. If each instance kept its own
* module-local `new AsyncLocalStorage()`, request-scoped state would silently
* fork across instances — `headers()` in one environment wouldn't see what
* `connection()` registered in another, concurrent requests would stomp each
* other, etc.
*
* The fix every shim was applying inline:
*
*   const _ALS_KEY = Symbol.for("vinext.foo.als");
*   const _g = globalThis as unknown as Record<PropertyKey, unknown>;
*   const _als = (_g[_ALS_KEY] ??=
*     new AsyncLocalStorage<T>()) as AsyncLocalStorage<T>;
*
* This helper packages that pattern.
*
* Cross-bundle singleton property — preserved
* -------------------------------------------
* - `Symbol.for(key)` consults the global symbol registry and returns the
*   same symbol regardless of which module instance calls it.
* - `globalThis[sym]` is a single slot shared by every module instance.
* - `??=` only assigns when the slot is empty, so the first caller wins and
*   every subsequent caller (in any module instance) reads the same ALS.
*
* The helper module itself never holds the ALS by reference — it always
* round-trips through `globalThis`. So even if this helper file is itself
* loaded under multiple module instances, every copy still hands back the
* one true ALS for a given key.
*/
var _g$1 = globalThis;
/**
* Every ALS handed out by `getOrCreateAls`, so `runOutsideRequestScopes` can
* exit all of them without an enumeration that goes stale as shims are added.
* Shares the `globalThis` slot for the same cross-module-instance reason.
*/
var _REGISTRY_KEY = Symbol.for("vinext.als.registry");
var _registry = _g$1[_REGISTRY_KEY] ??= /* @__PURE__ */ new Set();
/**
* No-op AsyncLocalStorage used when the runtime does not provide a usable
* `AsyncLocalStorage` constructor.
*
* In browser/client bundles `node:async_hooks` can resolve to a stub without a
* usable constructor (e.g. Vite's `__vite-browser-external`). Constructing such
* a value with `new` throws `TypeError: AsyncLocalStorage is not a constructor`
* at module-eval time, crashing every client-reachable shim that calls
* `getOrCreateAls` on import (request-context, headers, cache, …).
*
* Mirrors Next.js' `FakeAsyncLocalStorage` (and this repo's
* `async-hooks-stub.ts` client virtual module): `getStore()` returns
* `undefined` so shims fall back to their non-ALS code path, and the mutating
* methods are best-effort no-ops that still invoke the callback.
* See: https://github.com/vercel/next.js/blob/canary/packages/next/src/server/app-render/async-local-storage.ts
*/
var NoopAsyncLocalStorage = class {
	getStore() {}
	run(_store, fn, ...args) {
		return fn(...args);
	}
	exit(fn, ...args) {
		return fn(...args);
	}
	enterWith(_store) {}
	disable() {}
};
/**
* Get (or lazily create) the AsyncLocalStorage registered on `globalThis`
* under `Symbol.for(key)`. Multiple callers — including callers in different
* module instances — that pass the same `key` receive the same ALS instance.
*
* @param key - String key fed to `Symbol.for(...)`. By convention vinext
*   shims use a dotted namespace such as `"vinext.cache.als"`.
*/
function getOrCreateAls(key) {
	const sym = Symbol.for(key);
	const als = _g$1[sym] ??= typeof AsyncLocalStorage === "function" ? new AsyncLocalStorage() : new NoopAsyncLocalStorage();
	_registry.add(als);
	return als;
}
/**
* Enrol an ALS that is *not* created through `getOrCreateAls` into the
* scope-exit set. For stores that must stay module-local for identity reasons
* (`workUnitAsyncStorage` is a Next.js-compat external module third parties
* resolve by specifier) but still hold per-request state.
*
* Callers register themselves rather than being imported here, so this module
* keeps importing nothing but `node:async_hooks` and stays safe to evaluate in
* client bundles where that resolves to a constructor-less stub.
*/
function registerAlsForScopeExit(als) {
	_registry.add(als);
}
/**
* Run `fn` — and every async continuation it starts — outside every
* request-scoped AsyncLocalStorage vinext installs, so the callback observes no
* request at all.
*
* For one-time module evaluation whose result is cached for the isolate's
* lifetime: a dynamic `import()` propagates ALS into the imported module's
* top-level evaluation, so without this the first request to reach a route
* leaks into module scope and stays there for every request after it.
*
* Exiting a single store is not enough. The stores are entered at different
* depths — the Cloudflare entry enters the standalone execution-context ALS
* *outside* the unified request context, and prerendering enters the work-unit
* store *inside* it — so anything left entered stays visible. `after()` in
* particular takes its `getRequestExecutionContext()` fallback precisely when
* the unified store is absent, so a partial exit would enable that path rather
* than close it.
*/
function runOutsideRequestScopes(fn) {
	let run = fn;
	for (const als of _registry) {
		const inner = run;
		run = () => als.exit(inner);
	}
	return run();
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/unified-request-context.js
var _REQUEST_CONTEXT_ALS_KEY = Symbol.for("vinext.requestContext.als");
var _g = globalThis;
var _als = getOrCreateAls("vinext.unifiedRequestContext.als");
function _getInheritedExecutionContext() {
	const unifiedStore = _als.getStore();
	if (unifiedStore) return unifiedStore.executionContext;
	return _g[_REQUEST_CONTEXT_ALS_KEY]?.getStore() ?? null;
}
/**
* Create a fresh `UnifiedRequestContext` with defaults for all fields.
* Pass partial overrides for the fields you need to pre-populate.
*/
function createRequestContext(opts) {
	return {
		headersContext: null,
		actionRevalidationKind: 0,
		pendingRevalidatedTags: /* @__PURE__ */ new Set(),
		pendingRevalidations: /* @__PURE__ */ new Set(),
		dynamicUsageDetected: false,
		renderRequestApiUsage: /* @__PURE__ */ new Set(),
		connectionProbe: null,
		invalidDynamicUsageError: null,
		pendingSetCookies: [],
		draftModeCookieHeader: null,
		phase: "render",
		i18nContext: null,
		serverContext: null,
		serverInsertedHTMLCallbacks: [],
		requestScopedCacheLife: null,
		unstableCacheObservations: /* @__PURE__ */ new Map(),
		unstableCacheRevalidation: "foreground",
		_privateCache: null,
		cacheableFetchUrls: /* @__PURE__ */ new Set(),
		currentRequestTags: [],
		currentFetchSoftTags: [],
		currentFetchCacheMode: null,
		currentForceDynamicFetchDefault: false,
		dynamicFetchUrls: /* @__PURE__ */ new Set(),
		refreshStaleFetchesInForeground: false,
		isFetchDedupeActive: false,
		currentFetchDedupeEntries: /* @__PURE__ */ new Map(),
		executionContext: _getInheritedExecutionContext(),
		requestCache: /* @__PURE__ */ new WeakMap(),
		afterContext: {
			callbacks: [],
			responseClosed: false,
			pendingCallbacks: 0,
			pendingPromises: 0,
			completion: null,
			resolveCompletion: null
		},
		ssrContext: null,
		ssrHeadChildren: [],
		documentInitialHead: [],
		rootParams: null,
		...opts
	};
}
function ensureAfterCompletion(ctx) {
	const state = ctx.afterContext;
	if (state.resolveCompletion && state.completion) return;
	let resolveCompletion;
	const completion = new Promise((resolve) => {
		resolveCompletion = resolve;
	});
	state.completion = completion;
	state.resolveCompletion = resolveCompletion;
	ctx.executionContext?.waitUntil(completion);
}
function finishAfterCallbacksIfIdle(ctx) {
	const state = ctx.afterContext;
	if (!state.responseClosed || state.pendingCallbacks !== 0 || state.callbacks.length !== 0 || !state.resolveCompletion) return;
	const resolveCompletion = state.resolveCompletion;
	state.resolveCompletion = null;
	resolveCompletion();
}
function startAfterCallback(ctx, callback) {
	const state = ctx.afterContext;
	ensureAfterCompletion(ctx);
	state.pendingCallbacks += 1;
	Promise.resolve().then(callback).catch((error) => {
		console.error("[vinext] after() task failed:", error);
	}).finally(() => {
		state.pendingCallbacks -= 1;
		finishAfterCallbacksIfIdle(ctx);
	});
}
/**
* Release function-form `after()` work once the response body has closed.
* All queued callbacks start together, matching Next.js' unbounded PromiseQueue.
*/
async function closeAfterResponse(ctx) {
	const state = ctx.afterContext;
	if (!state.responseClosed) {
		state.responseClosed = true;
		const callbacks = state.callbacks.splice(0);
		for (const callback of callbacks) startAfterCallback(ctx, callback);
		finishAfterCallbacksIfIdle(ctx);
	}
	return state.completion ?? Promise.resolve();
}
/**
* Whether this request has function-form `after()` work that still needs to
* observe the response body closing.
*
* Promise-form `after(promise)` is included because its continuation can
* register a function-form `after()` before the promise settles. Function-form
* work needs the body's close observed because its contract is "run once the
* response has been sent". `resolveCompletion` stays non-null for as long as
* any callback is queued or in flight, so checking it alongside the explicit
* counters keeps this correct on re-entry after callbacks have started.
*/
function requiresResponseCloseTracking(ctx) {
	const state = ctx.afterContext;
	return state.callbacks.length > 0 || state.pendingCallbacks > 0 || state.pendingPromises > 0 || state.resolveCompletion !== null;
}
/**
* Mark a response whose body vinext constructed from a fully in-memory string
* or byte array, as opposed to a body handed back by user code, which could
* still be producing. With no producer left, no `after()` call can originate
* from this body — the one signal that makes it safe for
* `closeAfterResponseWithBody()` to skip close tracking.
*
* Not set for a metadata route's `result instanceof Response` passthrough (a
* user `icon.tsx`/`opengraph-image.tsx` can return a streaming
* `ImageResponse`) or any handler-returned `new Response(stream)` — those
* bodies can still be producing and must keep close tracking.
*/
function markFullyBufferedBody(response) {
	response.__vinextFullyBufferedBody = true;
	return response;
}
function isFullyBufferedBody(response) {
	return response.__vinextFullyBufferedBody === true;
}
/** Preserve the internal buffered-body signal when response metadata is rebuilt. */
function preserveFullyBufferedBodyMetadata(source, target) {
	return isFullyBufferedBody(source) ? markFullyBufferedBody(target) : target;
}
/**
* Wrap a response so deferred `after()` callbacks start on stream completion
* or cancellation. Skipped only when the body is marked fully buffered (see
* `markFullyBufferedBody`) and nothing is currently registered — that lets
* the runtime send it with an accurate `Content-Length` instead of chunked
* transfer encoding.
*/
function closeAfterResponseWithBody(response, ctx) {
	if (!response.body) {
		queueMicrotask(() => void closeAfterResponse(ctx));
		return response;
	}
	if (isFullyBufferedBody(response) && !requiresResponseCloseTracking(ctx)) return response;
	const passthrough = new TransformStream();
	response.body.pipeTo(passthrough.writable).then(() => void closeAfterResponse(ctx), () => void closeAfterResponse(ctx));
	const wrapped = new Response(passthrough.readable, {
		status: response.status,
		statusText: response.statusText,
		headers: response.headers
	});
	wrapped.__vinextStreamedHtmlResponse = response.__vinextStreamedHtmlResponse;
	wrapped.__vinextStreamedApiResponse = response.__vinextStreamedApiResponse;
	return wrapped;
}
function runWithRequestContext(ctx, fn) {
	return _als.run(ctx, fn);
}
function runWithUnifiedStateMutation(mutate, fn) {
	const parentCtx = _als.getStore();
	if (!parentCtx) return fn();
	const childCtx = { ...parentCtx };
	mutate(childCtx);
	return _als.run(childCtx, fn);
}
/**
* Get the current unified request context.
* Returns the ALS store when inside a `runWithRequestContext()` scope,
* or a fresh detached context otherwise. Unlike the legacy per-shim fallback
* singletons, this detached value is ephemeral — mutations do not persist
* across calls. This is intentional to prevent state leakage outside request
* scopes.
*
* Only direct callers observe this detached fallback. Shim `_getState()`
* helpers should continue to gate on `isInsideUnifiedScope()` and fall back
* to their standalone ALS/fallback singletons outside the unified scope.
* If called inside a standalone `runWithExecutionContext()` scope, the
* detached context still reflects that inherited `executionContext`.
*/
function getRequestContext() {
	return _als.getStore() ?? createRequestContext();
}
/**
* Check whether the current execution is inside a `runWithRequestContext()` scope.
* Shim modules use this to decide whether to read from the unified store
* or fall back to their own standalone ALS.
*/
function isInsideUnifiedScope() {
	return _als.getStore() != null;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/protocol-headers.js
/** Serialized middleware context (JSON) forwarded from dev server to RSC entry. */
var VINEXT_MW_CTX_HEADER = "x-vinext-mw-ctx";
/** Build-time prerender authentication secret. */
var VINEXT_PRERENDER_SECRET_HEADER = "x-vinext-prerender-secret";
/** URL-encoded JSON route params for build-time prerender renders. */
var VINEXT_PRERENDER_ROUTE_PARAMS_HEADER = "x-vinext-prerender-route-params";
/** Indicates a build-time prerender render is probing whether a route can be static. */
var VINEXT_PRERENDER_SPECULATIVE_HEADER = "x-vinext-prerender-speculative";
/** Logical hostname carried only by authenticated Node revalidation loopbacks. */
var VINEXT_REVALIDATE_HOST_HEADER = "x-vinext-revalidate-host";
/** Prefix for forwarded request headers (e.g. `x-middleware-request-cookie`). */
var MIDDLEWARE_REQUEST_HEADER_PREFIX = "x-middleware-request-";
/** Comma-separated list of header names that middleware wants to override. */
var MIDDLEWARE_OVERRIDE_HEADERS = "x-middleware-override-headers";
/** Carries cookies set by middleware for same-render reads. */
var MIDDLEWARE_SET_COOKIE_HEADER = "x-middleware-set-cookie";
/** Skip-middleware signal. */
var MIDDLEWARE_SKIP_HEADER = "x-middleware-skip";
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/headers.js
/**
* Internal HTTP header name constants used throughout vinext.
*
* Centralizes all custom header names so they are defined once and referenced
* everywhere via imports. Keeping them in one module prevents typos, makes
* rename-refactors trivial, and lets grep find every consumer instantly.
*
* Standard HTTP headers (Content-Type, Cache-Control, etc.) are intentionally
* omitted — only vinext-internal and Next.js-protocol headers belong here.
*/
/** ISR / page cache state indicator: "HIT" | "MISS" | "STALE" | "STATIC". */
var VINEXT_CACHE_HEADER = "X-Vinext-Cache";
/** Next.js public ISR / page cache state indicator. */
var NEXTJS_CACHE_HEADER = "x-nextjs-cache";
/** Next.js cache-tag metadata carried by prerendered App Router responses. */
var NEXT_CACHE_TAGS_HEADER = "x-next-cache-tags";
/** Static file signal — value is URL-encoded pathname. */
var VINEXT_STATIC_FILE_HEADER = "x-vinext-static-file";
/** Timing metrics: `handlerStart,compileMs,renderMs`. */
var VINEXT_TIMING_HEADER = "x-vinext-timing";
/** URL-encoded JSON route params carried on RSC responses. */
var VINEXT_PARAMS_HEADER = "X-Vinext-Params";
/** Deduplicated, sorted list of mounted layout slots for cache keying. */
var VINEXT_MOUNTED_SLOTS_HEADER = "X-Vinext-Mounted-Slots";
/** Per-page dynamic stale time in seconds for App Router RSC responses. */
var VINEXT_DYNAMIC_STALE_TIME_HEADER = "X-Vinext-Dynamic-Stale-Time";
/** Marks an RSC body carrying completion metadata after the Flight payload. */
var VINEXT_RSC_COMPLETION_METADATA_HEADER = "X-Vinext-Rsc-Completion-Metadata";
/** URL-encoded rendered path and search after middleware/config rewrites. */
var VINEXT_RENDERED_PATH_AND_SEARCH_HEADER = "X-Vinext-Rendered-Path-And-Search";
/** Prerender-only JSON side channel carrying request cacheLife metadata. */
var VINEXT_PRERENDER_CACHE_LIFE_HEADER = "x-vinext-prerender-cache-life";
/** Route interception context for parallel/intercepting routes. */
var VINEXT_INTERCEPTION_CONTEXT_HEADER = "X-Vinext-Interception-Context";
/** RSC render mode (e.g. "navigation", "prefetch"). */
var VINEXT_RSC_RENDER_MODE_HEADER = "X-Vinext-Rsc-Render-Mode";
/** Disabled-by-default client hint describing already-held App Router payload entries. */
var VINEXT_CLIENT_REUSE_MANIFEST_HEADER = "X-Vinext-Client-Reuse-Manifest";
/**
* Side-channel signal that an RSC response (HTTP 200) encodes a `redirect()`
* thrown during render. The header value is the redirect target (path-only
* for same-origin, absolute for cross-origin). The flight body still carries
* the canonical `NEXT_REDIRECT;...` digest so Next.js's own tests can read it
* via response.body; this header is purely for vinext's own client
* (`navigateRsc` in app-browser-entry.ts) to follow the redirect inside the
* same navigation transaction — keeping `useTransition`'s pending state
* continuous across the hop. Pre-1347 vinext relied on `fetch`'s auto-follow
* of a 307 for that, but the new 200 + flight format leaves it without a
* cheap way to detect the redirect ahead of stream decode.
*/
var VINEXT_RSC_REDIRECT_HEADER = "X-Vinext-Rsc-Redirect";
/** History update mode encoded by a streamed RSC redirect. */
var VINEXT_RSC_REDIRECT_TYPE_HEADER = "X-Vinext-Rsc-Redirect-Type";
/** Next.js action-not-found indicator (value "1"). */
var NEXTJS_ACTION_NOT_FOUND_HEADER = "x-nextjs-action-not-found";
/**
* Seconds the client router may reuse this response, resolved from the
* render's `cacheLife`. Mirrors Next.js's `NEXT_ROUTER_STALE_TIME_HEADER`;
* kept out of `Cache-Control`, which owns the shared-cache dimensions.
*/
var NEXT_ROUTER_STALE_TIME_HEADER = "x-nextjs-stale-time";
/**
* Marks a streamed cacheable RSC response whose `cacheLife` claim had not
* resolved at header time (value "1"). The client bounds such a response at
* min(30s floor, dynamic bound) instead of its fallback TTL.
*/
var VINEXT_STALE_TIME_PENDING_HEADER = "X-Vinext-Stale-Time-Pending";
/**
* Deployment ID header used by the Pages Router for deployment-skew
* protection. Set on every `/_next/data/` response so the client can detect
* when a new deployment has been rolled out and trigger a hard navigation.
* Mirrors `NEXT_NAV_DEPLOYMENT_ID_HEADER` from Next.js `lib/constants.ts`.
*/
var NEXTJS_DEPLOYMENT_ID_HEADER = "x-nextjs-deployment-id";
/** Forwarded action marker — set when a request has already been forwarded between workers. */
var ACTION_FORWARDED_HEADER = "x-action-forwarded";
/** Indicates revalidation occurred — value is JSON kind (1 = path/tag, 2 = dynamic-only). */
var ACTION_REVALIDATED_HEADER = "x-action-revalidated";
/** Signal from `NextResponse.next()` — value "1" means "continue to next handler". */
var MIDDLEWARE_NEXT_HEADER = "x-middleware-next";
/** Rewrite destination URL set by `NextResponse.rewrite()`. */
var MIDDLEWARE_REWRITE_HEADER = "x-middleware-rewrite";
/** Redirect URL set by middleware. */
var MIDDLEWARE_REDIRECT_HEADER = "x-middleware-redirect";
var NEXT_ROUTER_STATE_TREE_HEADER = "Next-Router-State-Tree";
var NEXT_ROUTER_PREFETCH_HEADER = "Next-Router-Prefetch";
var NEXT_ROUTER_SEGMENT_PREFETCH_HEADER = "Next-Router-Segment-Prefetch";
var NEXT_URL_HEADER = "Next-Url";
/** Lowercase flight header variants used in middleware forwarding. */
var FLIGHT_HEADERS = [
	"rsc",
	"next-router-state-tree",
	"next-router-prefetch",
	"next-hmr-refresh",
	"next-router-segment-prefetch"
];
/**
* Headers that must be stripped from external requests before any handler
* processes them. An attacker could forge these to influence routing or
* impersonate internal data fetches.
*
* Ported from Next.js `INTERNAL_HEADERS`:
* https://github.com/vercel/next.js/blob/canary/packages/next/src/server/lib/server-ipc/utils.ts
*/
var INTERNAL_HEADERS = [
	MIDDLEWARE_REWRITE_HEADER,
	MIDDLEWARE_REDIRECT_HEADER,
	MIDDLEWARE_SET_COOKIE_HEADER,
	MIDDLEWARE_SKIP_HEADER,
	MIDDLEWARE_OVERRIDE_HEADERS,
	MIDDLEWARE_NEXT_HEADER,
	"x-now-route-matches",
	"x-matched-path",
	"x-nextjs-data",
	"x-next-resume-state-length",
	ACTION_FORWARDED_HEADER
];
/** Vinext-only internal headers stripped alongside Next.js protocol internals. */
var VINEXT_INTERNAL_HEADERS = [
	VINEXT_PRERENDER_ROUTE_PARAMS_HEADER,
	VINEXT_PRERENDER_SPECULATIVE_HEADER,
	VINEXT_PRERENDER_CACHE_LIFE_HEADER,
	VINEXT_REVALIDATE_HOST_HEADER
];
//#endregion
export { MIDDLEWARE_REQUEST_HEADER_PREFIX as A, isInsideUnifiedScope as B, VINEXT_RSC_REDIRECT_HEADER as C, VINEXT_STATIC_FILE_HEADER as D, VINEXT_STALE_TIME_PENDING_HEADER as E, VINEXT_REVALIDATE_HOST_HEADER as F, registerAlsForScopeExit as G, runWithRequestContext as H, closeAfterResponse as I, runOutsideRequestScopes as K, closeAfterResponseWithBody as L, VINEXT_PRERENDER_ROUTE_PARAMS_HEADER as M, VINEXT_PRERENDER_SECRET_HEADER as N, VINEXT_TIMING_HEADER as O, VINEXT_PRERENDER_SPECULATIVE_HEADER as P, createRequestContext as R, VINEXT_RSC_COMPLETION_METADATA_HEADER as S, VINEXT_RSC_RENDER_MODE_HEADER as T, runWithUnifiedStateMutation as U, preserveFullyBufferedBodyMetadata as V, getOrCreateAls as W, VINEXT_INTERNAL_HEADERS as _, NEXTJS_CACHE_HEADER as a, VINEXT_PRERENDER_CACHE_LIFE_HEADER as b, NEXT_ROUTER_PREFETCH_HEADER as c, NEXT_ROUTER_STATE_TREE_HEADER as d, NEXT_URL_HEADER as f, VINEXT_INTERCEPTION_CONTEXT_HEADER as g, VINEXT_DYNAMIC_STALE_TIME_HEADER as h, NEXTJS_ACTION_NOT_FOUND_HEADER as i, VINEXT_MW_CTX_HEADER as j, MIDDLEWARE_OVERRIDE_HEADERS as k, NEXT_ROUTER_SEGMENT_PREFETCH_HEADER as l, VINEXT_CLIENT_REUSE_MANIFEST_HEADER as m, FLIGHT_HEADERS as n, NEXTJS_DEPLOYMENT_ID_HEADER as o, VINEXT_CACHE_HEADER as p, isUnknownRecord as q, INTERNAL_HEADERS as r, NEXT_CACHE_TAGS_HEADER as s, ACTION_REVALIDATED_HEADER as t, NEXT_ROUTER_STALE_TIME_HEADER as u, VINEXT_MOUNTED_SLOTS_HEADER as v, VINEXT_RSC_REDIRECT_TYPE_HEADER as w, VINEXT_RENDERED_PATH_AND_SEARCH_HEADER as x, VINEXT_PARAMS_HEADER as y, getRequestContext as z };
