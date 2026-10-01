import { n as __exportAll, r as __toESM } from "./_next/static/rolldown-runtime-BT1X7o2_.js";
import { n as require_react_react_server, t as require_jsx_runtime_react_server } from "./_next/static/framework~index~app-page-cache-render~app-page-cache~seed-cache~page~layout~page~app-route-~fe2f04fu-CQIcBs6F.js";
import { n as require_server_edge, t as require_client_edge } from "./_next/static/framework~index~page~layout~page~app-route-handler-dispatch-DTpbAJcP.js";
import { t as require_static_edge } from "./_next/static/framework~index-D6rQwtmb.js";
import { B as isInsideUnifiedScope, C as VINEXT_RSC_REDIRECT_HEADER, D as VINEXT_STATIC_FILE_HEADER, E as VINEXT_STALE_TIME_PENDING_HEADER, F as VINEXT_REVALIDATE_HOST_HEADER, G as registerAlsForScopeExit, H as runWithRequestContext, I as closeAfterResponse, K as runOutsideRequestScopes, L as closeAfterResponseWithBody, M as VINEXT_PRERENDER_ROUTE_PARAMS_HEADER, N as VINEXT_PRERENDER_SECRET_HEADER, O as VINEXT_TIMING_HEADER, P as VINEXT_PRERENDER_SPECULATIVE_HEADER, R as createRequestContext, S as VINEXT_RSC_COMPLETION_METADATA_HEADER, T as VINEXT_RSC_RENDER_MODE_HEADER, U as runWithUnifiedStateMutation, V as preserveFullyBufferedBodyMetadata, W as getOrCreateAls, _ as VINEXT_INTERNAL_HEADERS, a as NEXTJS_CACHE_HEADER, b as VINEXT_PRERENDER_CACHE_LIFE_HEADER, d as NEXT_ROUTER_STATE_TREE_HEADER, f as NEXT_URL_HEADER, g as VINEXT_INTERCEPTION_CONTEXT_HEADER, h as VINEXT_DYNAMIC_STALE_TIME_HEADER, i as NEXTJS_ACTION_NOT_FOUND_HEADER, j as VINEXT_MW_CTX_HEADER, m as VINEXT_CLIENT_REUSE_MANIFEST_HEADER, n as FLIGHT_HEADERS, o as NEXTJS_DEPLOYMENT_ID_HEADER, p as VINEXT_CACHE_HEADER, q as isUnknownRecord, r as INTERNAL_HEADERS, s as NEXT_CACHE_TAGS_HEADER, t as ACTION_REVALIDATED_HEADER, u as NEXT_ROUTER_STALE_TIME_HEADER, v as VINEXT_MOUNTED_SLOTS_HEADER, w as VINEXT_RSC_REDIRECT_TYPE_HEADER, x as VINEXT_RENDERED_PATH_AND_SEARCH_HEADER, y as VINEXT_PARAMS_HEADER, z as getRequestContext } from "./_next/static/headers-lNUsrpBT.js";
import { $ as invokeAppComponent, A as setRefreshStaleFetchesInForeground, At as runWithHeadersContext, B as APP_RSC_RENDER_MODE_PREFETCH_EMPTY, Bt as getUnconsumedMiddlewareRequestHeaders, C as getCollectedFetchTags, Ct as headersContextFromRequest, D as setCurrentFetchCacheMode, Dt as peekDynamicUsage, E as runWithFetchDedupe, Et as markRenderRequestApiUsage, F as _peekUnstableCacheObservations, Ft as throwIfStaticGenerationAccessError, G as APP_LAYOUT_IDS_KEY, H as getRscRenderModeCacheVariant, I as encodeCacheTag, It as createPprFallbackShellSuspensePromiseForState, J as AppElementsWire, K as APP_ROOT_LAYOUT_KEY, L as APP_PREFETCH_LOADING_SHELL_MARKER_KEY, Lt as getPprFallbackShellState, M as _consumeRequestScopedCacheLife, Nt as setHeadersContext, O as setCurrentFetchSoftTags, Ot as peekRenderRequestApiUsage, P as _peekRequestScopedCacheLife, Pt as throwIfInsideCacheScope, Q as createAppRenderDependency, R as APP_RSC_RENDER_MODE_NAVIGATION, S as ensureFetchPatch, St as getHeadersContext, T as peekDynamicFetchObservations, Tt as markDynamicUsage, U as parseAppRscRenderMode, Ut as configureMemoryCacheHandler, V as APP_RSC_RENDER_MODE_PREFETCH_LOADING_SHELL, Vt as parseCookieHeader, W as normalizeMountedSlotsHeader, Wt as resolveClientStaleTimeSeconds, X as normalizeAppElementsSlotBindings, Y as isAppElementsRecord, Z as createAppPageRenderDependency, _ as resolveInvalidRscCacheBustingRequest, _t as consumeInvalidDynamicUsageError, a as applyCdnResponseHeaders, at as isPromiseLike, b as getDeploymentId, bt as getAndClearPendingCookies, c as mergeMiddlewareResponseHeaders, ct as createArtifactCompatibilityGraphVersion, d as VINEXT_RSC_CONTENT_TYPE, dt as fnv1a64, et as isAppRenderSuspension, f as VINEXT_RSC_VARY_HEADER, ft as getCdnCacheAdapter, g as hasRscCacheBustingSearchParam, gt as consumeDynamicUsage, h as createRscRedirectLocation, ht as getRequestExecutionContext, i as STATIC_CACHE_CONTROL, it as renderAppComponentWithDependencyBarrier, j as _captureRequestScopedCacheLifeAccessors, jt as runWithIsolatedDynamicUsage, k as setCurrentForceDynamicFetchDefault, kt as runWithConnectionProbe, l as mergeVaryHeader, lt as evaluateArtifactCompatibility, m as applyRscDeploymentIdHeader, mt as normalizePath, n as NEVER_CACHE_CONTROL, nt as registerAppElementRenderDependencies, ot as ARTIFACT_COMPATIBILITY_PROOF_FIELDS, p as applyRscCompatibilityIdHeader, pt as isInterceptionMatchedUrlPath, q as APP_STATIC_SIBLINGS_KEY, r as NO_STORE_CACHE_CONTROL, rt as renderAfterAppDependencies, s as buildRevalidateCacheControl, st as createArtifactCompatibilityEnvelope, t as setCacheStateHeaders, tt as isReactOwnedAppComponent, u as VINEXT_RSC_CACHE_BUSTING_SEARCH_PARAM, ut as parseArtifactCompatibilityEnvelope, v as stripRscCacheBustingSearchParam, vt as consumeRenderRequestApiUsage, w as peekCacheableFetchObservations, wt as isDraftModeRequest, x as consumeDynamicFetchObservations, xt as getDraftModeCookieHeader, y as stripRscSuffix, z as APP_RSC_RENDER_MODE_PREFETCH_DYNAMIC_SHELL } from "./_next/static/cache-headers-CBpU4sbE.js";
import { AsyncLocalStorage } from "node:async_hooks";
import path from "node:path";
import "node:fs";
import "./vinext-client-assets.js";
import __vite_rsc_assets_manifest__ from "./__vite_rsc_assets_manifest.js";
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/server-globals.js
/**
* Server runtime global setup shared by vinext's generated server entries.
*
* This module intentionally runs its installer at import time. Generated entry
* modules import user pages and layouts as static dependencies, so any global
* correction that must happen before user module evaluation has to live in a
* side-effect dependency. A runtime function call from the generated entry
* body would run after static user imports have already evaluated.
*/
function clearBrowserGlobal(name) {
	const descriptor = Object.getOwnPropertyDescriptor(globalThis, name);
	if (!descriptor && typeof Reflect.get(globalThis, name) === "undefined") return;
	if (!descriptor) Object.defineProperty(globalThis, name, {
		configurable: true,
		value: void 0,
		writable: true
	});
	else if (descriptor.configurable) Reflect.deleteProperty(globalThis, name);
	else Reflect.set(globalThis, name, void 0);
	if (typeof Reflect.get(globalThis, name) !== "undefined") throw new Error(`[vinext] Server runtime exposes a non-removable \`${name}\` global. This breaks Next.js SSR semantics where browser globals must be absent.`);
}
function installServerGlobals() {
	clearBrowserGlobal("window");
	clearBrowserGlobal("document");
	if (typeof Reflect.get(globalThis, "AsyncLocalStorage") === "undefined") Object.defineProperty(globalThis, "AsyncLocalStorage", {
		configurable: true,
		value: AsyncLocalStorage,
		writable: true
	});
}
installServerGlobals();
//#endregion
//#region ../../../node_modules/.pnpm/@vitejs+plugin-rsc@0.5.26_r_d7be5b5d64a64a218ac22ba955ebe0d2/node_modules/@vitejs/plugin-rsc/dist/dist-rz-Bnebz.js
function tinyassert(value, message) {
	if (value) return;
	if (message instanceof Error) throw message;
	throw new TinyAssertionError(message, tinyassert);
}
var TinyAssertionError = class extends Error {
	constructor(message, stackStartFunction) {
		super(message ?? "TinyAssertionError");
		if (stackStartFunction && "captureStackTrace" in Error) Error.captureStackTrace(this, stackStartFunction);
	}
};
//#endregion
//#region ../../../node_modules/.pnpm/@vitejs+plugin-rsc@0.5.26_r_d7be5b5d64a64a218ac22ba955ebe0d2/node_modules/@vitejs/plugin-rsc/dist/core/rsc.js
var import_server_edge = /* @__PURE__ */ __toESM(require_server_edge(), 1);
function createClientManifest(options) {
	const cacheTag = "";
	return new Proxy({}, { get(_target, $$id, _receiver) {
		tinyassert(typeof $$id === "string");
		let [id, name] = $$id.split("#");
		tinyassert(id);
		tinyassert(name);
		options?.onClientReference?.({
			id,
			name
		});
		return {
			id: id + cacheTag,
			name,
			chunks: [],
			async: true
		};
	} });
}
require_client_edge();
function renderToReadableStream$1(data, options, extraOptions) {
	return import_server_edge.renderToReadableStream(data, createClientManifest({ onClientReference: extraOptions?.onClientReference }), options);
}
function registerClientReference(proxy, id, name) {
	return import_server_edge.registerClientReference(proxy, id, name);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/rsc-stream-hints.js
var import_static_edge = require_static_edge();
var REACT_FLIGHT_STYLESHEET_PRELOAD_HINT = /^([0-9a-f]*:HL\[.*?),"stylesheet"(\]|,)/;
var STYLESHEET_TO_STYLE_JSON_PADDING = " ".repeat(5);
var LENGTH_PREFIXED_ROW_TAGS = /* @__PURE__ */ new Set([
	"T",
	"A",
	"O",
	"o",
	"b",
	"U",
	"S",
	"s",
	"L",
	"l",
	"G",
	"g",
	"M",
	"m",
	"V"
]);
var NEWLINE_PREFIXED_ROW_TAGS = /* @__PURE__ */ new Set([
	"I",
	"H",
	"E",
	"N",
	"D",
	"J",
	"W",
	"R",
	"r",
	"X",
	"x",
	"C",
	"P",
	"#"
]);
var decoder$1 = new TextDecoder();
var encoder$1 = new TextEncoder();
/** Rewrite only a complete React Flight stylesheet hint row. */
function normalizeReactFlightHintLine(line) {
	const text = decoder$1.decode(line);
	const normalized = text.replace(REACT_FLIGHT_STYLESHEET_PRELOAD_HINT, `$1,"style"${STYLESHEET_TO_STYLE_JSON_PADDING}$2`);
	if (normalized === text) return line;
	const normalizedBytes = encoder$1.encode(normalized);
	return normalizedBytes.byteLength === line.byteLength ? normalizedBytes : line;
}
function concatBytes(first, second) {
	if (first.byteLength === 0) return second;
	const combined = new Uint8Array(first.byteLength + second.byteLength);
	combined.set(first);
	combined.set(second, first.byteLength);
	return combined;
}
function indexOfByte(bytes, byte, from = 0) {
	for (let index = from; index < bytes.byteLength; index++) if (bytes[index] === byte) return index;
	return -1;
}
function parseHexBytes(bytes, start, end) {
	if (start === end) return null;
	let value = 0;
	for (let index = start; index < end; index++) {
		const byte = bytes[index];
		const digit = byte >= 48 && byte <= 57 ? byte - 48 : byte >= 97 && byte <= 102 ? byte - 87 : -1;
		if (digit === -1) return null;
		value = value * 16 + digit;
		if (!Number.isSafeInteger(value)) return null;
	}
	return value;
}
function isUntaggedJsonRowStart(byte) {
	return byte === 34 || byte === 45 || byte >= 48 && byte <= 57 || byte === 91 || byte === 102 || byte === 110 || byte === 116 || byte === 123;
}
function normalizeReactFlightPreloadHints(stream) {
	let carry = /* @__PURE__ */ new Uint8Array();
	let rawBytesRemaining = 0;
	let passThrough = false;
	return stream.pipeThrough(new TransformStream({
		transform(chunk, controller) {
			if (passThrough) {
				controller.enqueue(chunk);
				return;
			}
			let bytes = concatBytes(carry, chunk);
			carry = /* @__PURE__ */ new Uint8Array();
			while (bytes.byteLength > 0) {
				if (rawBytesRemaining > 0) {
					const length = Math.min(rawBytesRemaining, bytes.byteLength);
					controller.enqueue(bytes.slice(0, length));
					rawBytesRemaining -= length;
					bytes = bytes.subarray(length);
					continue;
				}
				const colon = indexOfByte(bytes, 58);
				if (colon === -1 || colon + 1 === bytes.byteLength) {
					carry = bytes.slice();
					return;
				}
				const tag = String.fromCharCode(bytes[colon + 1]);
				if (LENGTH_PREFIXED_ROW_TAGS.has(tag)) {
					const comma = indexOfByte(bytes, 44, colon + 2);
					if (comma === -1) {
						carry = bytes.slice();
						return;
					}
					const length = parseHexBytes(bytes, colon + 2, comma);
					if (length != null) {
						controller.enqueue(bytes.slice(0, comma + 1));
						rawBytesRemaining = length;
						bytes = bytes.subarray(comma + 1);
						continue;
					}
					passThrough = true;
					controller.enqueue(bytes);
					return;
				}
				const tagByte = bytes[colon + 1];
				if (!NEWLINE_PREFIXED_ROW_TAGS.has(tag) && !isUntaggedJsonRowStart(tagByte)) {
					passThrough = true;
					controller.enqueue(bytes);
					return;
				}
				const newline = indexOfByte(bytes, 10);
				if (newline === -1) {
					carry = bytes.slice();
					return;
				}
				controller.enqueue(normalizeReactFlightHintLine(bytes.slice(0, newline + 1)));
				bytes = bytes.subarray(newline + 1);
			}
		},
		flush(controller) {
			if (carry.byteLength > 0) controller.enqueue(rawBytesRemaining > 0 ? carry : normalizeReactFlightHintLine(carry));
		}
	}));
}
function createRscRenderer(render) {
	return (model, options) => normalizeReactFlightPreloadHints(render(model, options));
}
function createRscPrerenderer(prerender) {
	return async (model, options) => {
		return { prelude: normalizeReactFlightPreloadHints((await prerender(model, options)).prelude) };
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/navigation-context-state.js
var import_react_react_server = /* @__PURE__ */ __toESM(require_react_react_server(), 1);
var SERVER_INSERTED_HTML_CONTEXT_KEY = Symbol.for("vinext.serverInsertedHTMLContext");
var NAVIGATION_FALLBACK_STATE_KEY = Symbol.for("vinext.navigation.fallback");
function createContextIfAvailable(defaultValue) {
	return typeof import_react_react_server.createContext === "function" ? import_react_react_server.createContext(defaultValue) : null;
}
function getServerInsertedHTMLContext() {
	const globalState = globalThis;
	if (!globalState[SERVER_INSERTED_HTML_CONTEXT_KEY]) globalState[SERVER_INSERTED_HTML_CONTEXT_KEY] = createContextIfAvailable(null);
	return globalState[SERVER_INSERTED_HTML_CONTEXT_KEY] ?? null;
}
getServerInsertedHTMLContext();
var GLOBAL_ACCESSORS_KEY = Symbol.for("vinext.navigation.globalAccessors");
function getFallbackState() {
	const globalState = globalThis;
	return globalState[NAVIGATION_FALLBACK_STATE_KEY] ??= {
		serverContext: null,
		serverInsertedHTMLCallbacks: []
	};
}
function getGlobalAccessors() {
	return globalThis[GLOBAL_ACCESSORS_KEY];
}
var getServerContext = () => {
	return getGlobalAccessors()?.getServerContext() ?? getFallbackState().serverContext;
};
var setServerContext = (context) => {
	const accessors = getGlobalAccessors();
	if (accessors) accessors.setServerContext(context);
	else getFallbackState().serverContext = context;
};
/**
* Register request-scoped accessors supplied by navigation-state.ts.
* The global accessor key also bridges separate Vite module instances.
*/
function _registerStateAccessors(accessors) {
	getServerContext = accessors.getServerContext;
	setServerContext = accessors.setServerContext;
	accessors.getInsertedHTMLCallbacks;
	accessors.clearInsertedHTMLCallbacks;
}
function getNavigationContext() {
	return getServerContext();
}
function setNavigationContext(context) {
	setServerContext(context);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/redirect-digest.js
var NEXT_REDIRECT_PREFIX = "NEXT_REDIRECT;";
function parseRedirectDigest(digest) {
	if (!digest.startsWith(NEXT_REDIRECT_PREFIX)) return null;
	const firstSemi = digest.indexOf(";", 14);
	if (firstSemi === -1) return null;
	const rest = digest.slice(firstSemi + 1);
	const statusMatch = rest.match(/;(303|307|308);?$/);
	const isCanonical = rest !== "" && digest.endsWith(";");
	if (isCanonical && !statusMatch) return null;
	const target = statusMatch ? rest.slice(0, -statusMatch[0].length) : rest;
	let url = target;
	if (!isCanonical) try {
		url = decodeURIComponent(target);
	} catch {
		return null;
	}
	return {
		status: statusMatch ? Number(statusMatch[1]) : 307,
		type: digest.slice(14, firstSemi) || null,
		url
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/navigation-errors.js
function isHTTPAccessFallbackError(error) {
	if (!error || typeof error !== "object" || !("digest" in error)) return false;
	const digest = String(error.digest);
	return digest === "NEXT_NOT_FOUND" || digest.startsWith(`NEXT_HTTP_ERROR_FALLBACK;`);
}
/**
* vinext accepts its three-part redirect digest and Next.js's five-part form.
* This is deliberately only a cheap prefix gate because vinext permits an
* empty redirect type; parseRedirectDigest is the authoritative validator.
*/
function isRedirectError(error) {
	return !!error && typeof error === "object" && "digest" in error && typeof error.digest === "string" && error.digest.startsWith("NEXT_REDIRECT;");
}
function isNextRouterError(error) {
	return isRedirectError(error) || isHTTPAccessFallbackError(error);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/client-hook-error.js
/**
* Shared error helper for client-only hooks called in Server Components.
*
* Used by `.react-server.ts` shim variants to provide a clear, actionable
* error message when a developer forgets the "use client" directive.
*
* @see https://github.com/cloudflare/vinext/issues/834
*/
function buildClientHookErrorMessage(hookName) {
	return `${hookName} only works in Client Components. Add the "use client" directive at the top of the file to use it. Read more: https://nextjs.org/docs/messages/react-client-hook-in-server-component`;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/base-path.js
/**
* Shared basePath helpers.
*
* Next.js only treats a pathname as being under basePath when it is an exact
* match ("/app") or starts with the basePath followed by a path separator
* ("/app/..."). Prefix-only matches like "/application" must be left intact.
*/
/**
* Check whether a pathname is inside the configured basePath.
*/
function hasBasePath(pathname, basePath) {
	if (!basePath) return false;
	return pathname === basePath || pathname.startsWith(basePath + "/");
}
/**
* Strip the basePath prefix from a pathname when it matches on a segment
* boundary. Returns the original pathname when it is outside the basePath.
*/
function stripBasePath(pathname, basePath) {
	if (!hasBasePath(pathname, basePath)) return pathname;
	return pathname.slice(basePath.length) || "/";
}
/**
* Add the configured basePath to a pathname unless it is already inside that
* basePath. Query strings and hashes must be handled by callers before calling
* this pathname-only helper.
*/
function addBasePathToPathname(pathname, basePath) {
	if (!basePath || hasBasePath(pathname, basePath)) return pathname;
	return pathname === "/" ? basePath : `${basePath}${pathname}`;
}
/**
* Remove trailing slashes from a pathname while preserving the root "/".
* Collapses any number of trailing slashes ("/a//" → "/a"). Used by the
* trailing-slash redirect path and route pattern normalization.
*/
function removeTrailingSlash(pathname) {
	if (pathname === "/") return "/";
	let end = pathname.length;
	while (end > 0 && pathname.charCodeAt(end - 1) === 47) end--;
	return end === 0 ? "/" : pathname.slice(0, end);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/url-utils.js
/**
* Shared URL utilities for same-origin detection.
*
* Used by link.tsx, navigation.ts, and router.ts to normalize
* same-origin absolute URLs to local paths for client-side navigation.
*/
var ABSOLUTE_URL_REGEX = /^[a-zA-Z][a-zA-Z\d+\-.]*?:/;
function isAbsoluteUrl(url) {
	const firstChar = url.charCodeAt(0);
	return (firstChar >= 65 && firstChar <= 90 || firstChar >= 97 && firstChar <= 122) && ABSOLUTE_URL_REGEX.test(url);
}
function isAbsoluteOrProtocolRelativeUrl(url) {
	return isAbsoluteUrl(url) || url.startsWith("//");
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/thenable-params.js
function hasParamProperty(obj, prop) {
	return Object.prototype.hasOwnProperty.call(obj, prop);
}
var wellKnownProperties = /* @__PURE__ */ new Set([
	"hasOwnProperty",
	"isPrototypeOf",
	"propertyIsEnumerable",
	"toString",
	"valueOf",
	"toLocaleString",
	"then",
	"catch",
	"finally",
	"status",
	"value",
	"error",
	"displayName",
	"_debugInfo",
	"toJSON",
	"$$typeof",
	"__esModule",
	"@@iterator"
]);
function isWellKnownProperty(prop) {
	return wellKnownProperties.has(prop);
}
function observeParamKeys(observer, keys) {
	if (observer) observer.observeParamAccess(keys);
}
function observeAllParamKeys(observer, plain) {
	observeParamKeys(observer, Object.keys(plain));
}
function observeReadableParamKeys(observer, plain) {
	observeParamKeys(observer, Object.keys(plain).filter((key) => !isWellKnownProperty(key)));
}
function isPromiseContinuation(prop) {
	return prop === "then" || prop === "catch" || prop === "finally";
}
/**
* Build a proxy around `plain` that preserves fallback-key suspension.
* This is the value `await params` resolves to during fallback-shell
* prerendering. Known params are readable synchronously; fallback params
* suspend (throw a hanging promise) only when actually accessed.
*
* The handler is typed as `ProxyHandler<T>` and no cast is needed because
* the target is already `plain: T`.
*/
function createResolvedParamsProxy(plain, fallbackParamNames, observer, getFallbackShellPromise) {
	if (!fallbackParamNames || fallbackParamNames.size === 0) return plain;
	function isFallbackParam(prop) {
		return typeof prop === "string" && fallbackParamNames !== null && fallbackParamNames.has(prop);
	}
	return new Proxy(plain, {
		get(_target, prop, _receiver) {
			if (typeof prop === "string" && !isWellKnownProperty(prop)) observeParamKeys(observer, [prop]);
			if (!isWellKnownProperty(prop) && hasParamProperty(plain, prop)) {
				if (isFallbackParam(prop)) {
					const p = getFallbackShellPromise();
					if (p) throw p;
				}
				return Reflect.get(plain, prop);
			}
			return Reflect.get(plain, prop);
		},
		getOwnPropertyDescriptor(_target, prop) {
			if (typeof prop === "string" && !isWellKnownProperty(prop)) observeParamKeys(observer, [prop]);
			if (!isWellKnownProperty(prop) && hasParamProperty(plain, prop)) {
				if (isFallbackParam(prop)) return {
					configurable: true,
					enumerable: true,
					get() {
						const p = getFallbackShellPromise();
						if (p) throw p;
					}
				};
				return {
					configurable: true,
					enumerable: true,
					value: Reflect.get(plain, prop),
					writable: true
				};
			}
			return Reflect.getOwnPropertyDescriptor(plain, prop);
		},
		has(_target, prop) {
			if (typeof prop === "string" && !isWellKnownProperty(prop)) observeParamKeys(observer, [prop]);
			return Reflect.has(plain, prop) || !isWellKnownProperty(prop) && hasParamProperty(plain, prop);
		},
		ownKeys() {
			observeReadableParamKeys(observer, plain);
			return Reflect.ownKeys(plain).filter((prop) => !isWellKnownProperty(prop));
		}
	});
}
/**
* Wrap a `Promise<T>` with a proxy that also exposes param properties for
* synchronous access. TypeScript cannot prove this hybrid shape statically,
* so the single `as ThenableParams<T>` cast is isolated here.
*/
function createThenableParamsProxy(promise, handler) {
	return new Proxy(promise, handler);
}
function makeThenableParams(obj, observer) {
	const plain = { ...obj };
	const fallbackShellState = getPprFallbackShellState();
	const fallbackParamNames = fallbackShellState && Object.keys(plain).some((key) => fallbackShellState.fallbackParamNames.has(key)) ? fallbackShellState.fallbackParamNames : null;
	let fallbackShellPromise = null;
	let fallbackShellPromiseController = null;
	function getFallbackShellPromise() {
		if (!fallbackParamNames || !fallbackShellState) return null;
		if (fallbackShellPromise && fallbackShellPromiseController === fallbackShellState.abortController) return fallbackShellPromise;
		fallbackShellPromiseController = fallbackShellState.abortController;
		fallbackShellPromise = createPprFallbackShellSuspensePromiseForState(fallbackShellState, "`params`");
		return fallbackShellPromise;
	}
	const resolvedParams = createResolvedParamsProxy(plain, fallbackParamNames, observer, getFallbackShellPromise);
	const promise = Promise.resolve(resolvedParams);
	function isFallbackParam(prop) {
		return typeof prop === "string" && (fallbackParamNames?.has(prop) ?? false);
	}
	return createThenableParamsProxy(promise, {
		get(target, prop, receiver) {
			if (isPromiseContinuation(prop)) {
				const value = Reflect.get(target, prop, receiver);
				if (typeof value !== "function") return value;
				return (...args) => {
					if (!fallbackParamNames) observeAllParamKeys(observer, plain);
					return Reflect.apply(value, target, args);
				};
			}
			if (prop === "status" && observer?.observeReactPromiseStatus === true) observeAllParamKeys(observer, plain);
			if (typeof prop === "string" && !isWellKnownProperty(prop)) observeParamKeys(observer, [prop]);
			if (!isWellKnownProperty(prop) && hasParamProperty(plain, prop)) {
				if (isFallbackParam(prop)) {
					const p = getFallbackShellPromise();
					if (p) throw p;
				}
				return Reflect.get(plain, prop);
			}
			const value = Reflect.get(target, prop, receiver);
			return typeof value === "function" ? value.bind(target) : value;
		},
		getOwnPropertyDescriptor(target, prop) {
			if (typeof prop === "string" && !isWellKnownProperty(prop)) observeParamKeys(observer, [prop]);
			if (!isWellKnownProperty(prop) && hasParamProperty(plain, prop)) {
				if (isFallbackParam(prop)) return {
					configurable: true,
					enumerable: true,
					get() {
						const p = getFallbackShellPromise();
						if (p) throw p;
					}
				};
				return {
					configurable: true,
					enumerable: true,
					value: Reflect.get(plain, prop),
					writable: true
				};
			}
			return Reflect.getOwnPropertyDescriptor(target, prop);
		},
		has(target, prop) {
			if (typeof prop === "string" && !isWellKnownProperty(prop)) observeParamKeys(observer, [prop]);
			return Reflect.has(target, prop) || !isWellKnownProperty(prop) && hasParamProperty(plain, prop);
		},
		ownKeys() {
			observeReadableParamKeys(observer, plain);
			return Reflect.ownKeys(plain).filter((prop) => !isWellKnownProperty(prop));
		}
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/metadata.js
var import_jsx_runtime_react_server = require_jsx_runtime_react_server();
/**
* Metadata support for App Router.
*
* Handles `export const metadata` and `export async function generateMetadata()`.
* Resolves metadata from layouts and pages (pages override layouts).
*/
var USE_CACHE_FUNCTION_SYMBOL = Symbol.for("vinext.useCacheFunction");
var USE_CACHE_ACCEPTS_SECOND_ARGUMENT_SYMBOL = Symbol.for("vinext.useCacheAcceptsSecondArgument");
/**
* Resolve viewport config from a module. Handles both static `viewport` export
* and async `generateViewport()` function.
*/
async function resolveModuleViewport(mod, params = {}, searchParams, parent = Promise.resolve(mergeViewport([])), searchParamsObserver) {
	if (typeof mod.generateViewport === "function") {
		const asyncParams = makeThenableParams(params);
		const props = searchParams === void 0 ? { params: asyncParams } : {
			params: asyncParams,
			searchParams: makeThenableParams(searchParams, searchParamsObserver)
		};
		return await mod.generateViewport(props, parent);
	}
	if (mod.viewport && typeof mod.viewport === "object") return mod.viewport;
	return null;
}
/**
* Merge viewport configs from multiple sources (layouts + page).
* Later entries override earlier ones.
*/
var DEFAULT_VIEWPORT = {
	width: "device-width",
	initialScale: 1,
	themeColor: null,
	colorScheme: null
};
function mergeViewport(viewportList) {
	const merged = { ...DEFAULT_VIEWPORT };
	for (const viewport of viewportList) for (const viewportKey in viewport) switch (viewportKey) {
		case "themeColor":
			merged.themeColor = resolveThemeColor(viewport.themeColor);
			break;
		case "colorScheme":
			merged.colorScheme = viewport.colorScheme || null;
			break;
		case "width":
			merged.width = viewport.width;
			break;
		case "height":
			merged.height = viewport.height;
			break;
		case "initialScale":
			merged.initialScale = viewport.initialScale;
			break;
		case "minimumScale":
			merged.minimumScale = viewport.minimumScale;
			break;
		case "maximumScale":
			merged.maximumScale = viewport.maximumScale;
			break;
		case "userScalable":
			merged.userScalable = viewport.userScalable;
			break;
		case "viewportFit":
			merged.viewportFit = viewport.viewportFit;
			break;
		case "interactiveWidget":
			merged.interactiveWidget = viewport.interactiveWidget;
			break;
		default:
	}
	return merged;
}
var VIEWPORT_META_NAMES = {
	width: "width",
	height: "height",
	initialScale: "initial-scale",
	minimumScale: "minimum-scale",
	maximumScale: "maximum-scale",
	userScalable: "user-scalable",
	viewportFit: "viewport-fit",
	interactiveWidget: "interactive-widget"
};
/**
* React component that renders viewport meta tags into <head>.
*/
function ViewportHead({ viewport }) {
	const resolvedViewport = mergeViewport([viewport]);
	const elements = [];
	let key = 0;
	const parts = [];
	for (const key of Object.keys(VIEWPORT_META_NAMES)) {
		const value = resolvedViewport[key];
		if (value == null) continue;
		parts.push(`${VIEWPORT_META_NAMES[key]}=${key === "userScalable" ? value ? "yes" : "no" : value}`);
	}
	if (parts.length > 0) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
		name: "viewport",
		content: parts.join(", ")
	}, key++));
	if (resolvedViewport.themeColor) for (const entry of resolvedViewport.themeColor) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
		name: "theme-color",
		content: entry.color,
		...entry.media ? { media: entry.media } : {}
	}, key++));
	if (resolvedViewport.colorScheme) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
		name: "color-scheme",
		content: resolvedViewport.colorScheme
	}, key++));
	return /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(import_jsx_runtime_react_server.Fragment, { children: elements });
}
function resolveThemeColor(themeColor) {
	if (!themeColor) return null;
	return (Array.isArray(themeColor) ? themeColor : [themeColor]).map((descriptor) => typeof descriptor === "string" ? { color: descriptor } : {
		color: descriptor.color,
		media: descriptor.media
	});
}
function isPlainObject(value) {
	return typeof value === "object" && value !== null && !Array.isArray(value) && !(value instanceof URL);
}
function isOtherMetadata(value) {
	if (!isPlainObject(value)) return false;
	return Object.values(value).every((item) => {
		if (typeof item === "string") return true;
		return Array.isArray(item) && item.every((nestedItem) => typeof nestedItem === "string");
	});
}
/**
* Extract a plain string title from a metadata title value.
*/
function resolveStringTitle(title) {
	if (typeof title === "string") return title;
	if (title && typeof title === "object") return title.absolute ?? title.default ?? void 0;
}
function applyTitleTemplate(template, title) {
	return template ? template.replace(/%s/g, title) : title;
}
function resolveTitle(title, stashedTemplate) {
	if (typeof title === "string") return applyTitleTemplate(stashedTemplate, title);
	if (title && typeof title === "object") {
		let resolved = title.default === void 0 ? void 0 : applyTitleTemplate(stashedTemplate, title.default);
		if (title.absolute) resolved = title.absolute;
		return resolved;
	}
}
/**
* Post-process merged metadata to cross-fill openGraph and Twitter fields.
*
* Next.js runs this once after all layouts/pages and file-based metadata
* have been resolved. When openGraph exists, it auto-fills missing
* twitter:title/description/images from openGraph (falling back to root
* metadata title/description). Existing openGraph/twitter objects also inherit
* missing title/description from root metadata.
*
* Ported from Next.js:
* https://github.com/vercel/next.js/blob/canary/packages/next/src/lib/metadata/resolve-metadata.ts
*/
function postProcessMetadata(merged) {
	const result = { ...merged };
	const resolvedTitle = resolveStringTitle(result.title);
	if (result.openGraph) {
		const og = { ...result.openGraph };
		if (!og.title && resolvedTitle) og.title = resolvedTitle;
		if (!og.description && result.description) og.description = result.description;
		result.openGraph = og;
	}
	if (result.openGraph) {
		const autoFill = {};
		const existingTwitter = result.twitter;
		const hasTwTitle = existingTwitter ? Boolean(existingTwitter.title) : false;
		const hasTwDescription = existingTwitter ? Boolean(existingTwitter.description) : false;
		const hasTwImages = existingTwitter ? Object.prototype.hasOwnProperty.call(existingTwitter, "images") && Boolean(existingTwitter.images) : false;
		if (!hasTwTitle) {
			if (result.openGraph.title) autoFill.title = result.openGraph.title;
			else if (resolvedTitle) autoFill.title = resolvedTitle;
		}
		if (!hasTwDescription) autoFill.description = result.openGraph.description || result.description || void 0;
		if (!hasTwImages && result.openGraph.images !== void 0) autoFill.images = result.openGraph.images;
		if (Object.keys(autoFill).length > 0) if (existingTwitter) result.twitter = {
			...existingTwitter,
			...autoFill
		};
		else result.twitter = autoFill;
	}
	if (result.twitter) {
		const tw = { ...result.twitter };
		if (!tw.title && resolvedTitle) tw.title = resolvedTitle;
		if (!tw.description && result.description) tw.description = result.description;
		result.twitter = tw;
	}
	if (result.twitter) {
		const tw = { ...result.twitter };
		if (!tw.card) {
			const images = tw.images;
			tw.card = (Array.isArray(images) ? images.length > 0 : Boolean(images)) ? "summary_large_image" : "summary";
		}
		result.twitter = tw;
	}
	return result;
}
/**
* Merge metadata from multiple sources (layouts + page).
*
* The list is ordered [rootLayout, nestedLayout, ..., page].
* Title template from layouts applies to the page title but NOT to
* the segment that defines the template itself. `title.absolute`
* skips all templates. `title.default` is the fallback when no
* child provides a title.
*
* For top-level keys, later entries override earlier ones. `other` custom meta
* tags are the exception: Next.js merges those across segments.
*/
function mergeMetadataEntries(entries) {
	if (entries.length === 0) return {};
	const merged = {};
	let parentTemplate;
	for (const entry of entries) {
		const meta = entry.metadata;
		const isPage = Boolean(entry.isPage);
		const contributesTitle = entry.contributesTitle !== false;
		for (const key of Object.keys(meta)) {
			if (key === "title") continue;
			const incoming = meta[key];
			const existing = merged[key];
			if (key === "other" && isOtherMetadata(existing) && isOtherMetadata(incoming)) merged.other = {
				...existing,
				...incoming
			};
			else merged[key] = incoming;
		}
		if (contributesTitle && meta.title !== void 0) merged.title = resolveTitle(meta.title, parentTemplate);
		if (contributesTitle && !isPage && meta.title && typeof meta.title === "object" && meta.title.template) parentTemplate = meta.title.template;
	}
	return merged;
}
/**
* Resolve metadata from a module. Handles both static `metadata` export
* and async `generateMetadata()` function.
*
* @param parent - A Promise that resolves to the accumulated (merged) metadata
*   from all ancestor segments. Passed as the second argument to
*   `generateMetadata()`, matching Next.js's eager-execution-with-serial-
*   resolution approach. If not provided, defaults to a promise that resolves
*   to an empty object (so `await parent` never throws).
*/
async function resolveModuleMetadata$1(mod, params = {}, searchParams, parent = Promise.resolve({}), searchParamsObserver) {
	if (typeof mod.generateMetadata === "function") {
		const generateMetadata = mod.generateMetadata;
		const asyncParams = makeThenableParams(params);
		const props = searchParams === void 0 ? { params: asyncParams } : {
			params: asyncParams,
			searchParams: makeThenableParams(searchParams, searchParamsObserver)
		};
		const isUseCacheFunction = Reflect.get(generateMetadata, USE_CACHE_FUNCTION_SYMBOL) === true;
		const acceptsSecondArgument = Reflect.get(generateMetadata, USE_CACHE_ACCEPTS_SECOND_ARGUMENT_SYMBOL);
		return await (!isUseCacheFunction || (typeof acceptsSecondArgument === "boolean" ? acceptsSecondArgument : generateMetadata.length >= 2) ? generateMetadata(props, parent) : generateMetadata(props));
	}
	if (mod.metadata && typeof mod.metadata === "object") return mod.metadata;
	return null;
}
/**
* React component that renders metadata as HTML head elements.
* Used by the RSC entry to inject into the <head>.
*/
function isIconDescriptor(value) {
	if (typeof value !== "object" || value === null || value instanceof URL || Array.isArray(value)) return false;
	const urlValue = Reflect.get(value, "url");
	return typeof urlValue === "string" || urlValue instanceof URL;
}
function isIconsMap(value) {
	return typeof value === "object" && !(value instanceof URL) && !Array.isArray(value) && !isIconDescriptor(value);
}
function normalizeUrlDescriptor(value, createDescriptor) {
	if (typeof value === "string" || value instanceof URL) return createDescriptor(value);
	return value;
}
function normalizeUrlDescriptorEntries(value, createDescriptor) {
	if (!value) return [];
	if (Array.isArray(value)) return value.map((entry) => normalizeUrlDescriptor(entry, createDescriptor));
	return [normalizeUrlDescriptor(value, createDescriptor)];
}
function stringifyUrl(url) {
	return typeof url === "string" ? url : url.toString();
}
function createLocalMetadataBase() {
	const protocol = process.env.__NEXT_EXPERIMENTAL_HTTPS ? "https" : "http";
	return new URL(`${protocol}://localhost:${process.env.PORT || 3e3}`);
}
function getPreviewDeploymentUrl() {
	const origin = process.env.VERCEL_BRANCH_URL || process.env.VERCEL_URL;
	return origin ? new URL(`https://${origin}`) : null;
}
function getProductionDeploymentUrl() {
	const origin = process.env.VERCEL_PROJECT_PRODUCTION_URL;
	return origin ? new URL(`https://${origin}`) : null;
}
function getSocialImageMetadataBaseFallback(metadataBase) {
	const defaultMetadataBase = createLocalMetadataBase();
	const previewDeploymentUrl = getPreviewDeploymentUrl();
	const productionDeploymentUrl = getProductionDeploymentUrl();
	if (process.env.VERCEL_ENV === "preview" && previewDeploymentUrl) return previewDeploymentUrl;
	return metadataBase || productionDeploymentUrl || defaultMetadataBase;
}
function trimSlashes(value) {
	return value.replace(/^\/+|\/+$/g, "");
}
function joinMetadataPath(basePathname, pathname) {
	if (!basePathname || basePathname === "/") return pathname;
	const base = trimSlashes(basePathname);
	const path = trimSlashes(pathname);
	return path ? `/${base}/${path}` : `/${base}`;
}
function resolveRelativeMetadataUrl(url, pathname) {
	if (url === "." || url === "./") return pathname || "/";
	if (!url.startsWith("./")) return url;
	return `${pathname === "/" ? "" : pathname.replace(/\/+$/g, "")}/${url.slice(2)}`;
}
function formatResolvedMetadataUrl(url) {
	if (url.pathname === "/" && url.search === "" && url.hash === "") return url.origin;
	return url.href;
}
var TRAILING_SLASH_FILE_REGEX = /^(?:\/((?!\.well-known(?:\/.*)?)((?:[^/]+\/)*)([^/]+\.\w+)))(\/?|$)/i;
function resolveMetadataUrl(url, metadataBase, trailingSlash) {
	const value = stringifyUrl(url);
	if (!metadataBase) return value;
	try {
		const isAbsolute = isAbsoluteOrProtocolRelativeUrl(value);
		const composed = isAbsolute ? new URL(value, metadataBase) : new URL(joinMetadataPath(metadataBase.pathname, value), metadataBase);
		if (isAbsolute && composed.origin !== metadataBase.origin) return value;
		if (trailingSlash === true && composed.search === "") {
			if (composed.pathname !== "/" && !composed.pathname.endsWith("/") && !TRAILING_SLASH_FILE_REGEX.test(composed.pathname)) composed.pathname += "/";
		}
		const result = formatResolvedMetadataUrl(composed);
		if (trailingSlash === true && result === metadataBase.origin) return `${metadataBase.origin}/`;
		return result;
	} catch {
		return value;
	}
}
function resolveCanonicalUrl(url, metadataBase, pathname, trailingSlash) {
	if (url instanceof URL) return resolveMetadataUrl(url, metadataBase, trailingSlash);
	return resolveMetadataUrl(resolveRelativeMetadataUrl(url, pathname), metadataBase, trailingSlash);
}
function resolveAlternateUrl(url, metadataBase, pathname, trailingSlash) {
	if (url instanceof URL) {
		const resolvedUrl = new URL(pathname, url);
		url.searchParams.forEach((value, key) => resolvedUrl.searchParams.set(key, value));
		return resolveMetadataUrl(resolvedUrl, metadataBase, trailingSlash);
	}
	return resolveCanonicalUrl(url, metadataBase, pathname, trailingSlash);
}
function isSocialImageDescriptor(value) {
	return typeof value === "object" && !(value instanceof URL);
}
function isMetadataRouteSocialImage(value) {
	return Reflect.get(value, "metadataRoute") === true;
}
function resolveSocialImageUrl(image, metadataBase) {
	const imageUrl = isSocialImageDescriptor(image) ? image.url : image;
	const metadataRoute = isSocialImageDescriptor(image) && isMetadataRouteSocialImage(image);
	if (typeof imageUrl === "string" && !isAbsoluteOrProtocolRelativeUrl(imageUrl) && (!metadataBase || metadataRoute)) return resolveMetadataUrl(imageUrl, getSocialImageMetadataBaseFallback(metadataBase));
	return resolveMetadataUrl(imageUrl, metadataBase);
}
function escapeHtmlText(value) {
	return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}
function escapeHtmlAttribute(value) {
	return escapeHtmlText(value).replaceAll("\"", "&quot;");
}
function renderMetadataText(node) {
	if (node === null || node === void 0 || typeof node === "boolean") return "";
	if (Array.isArray(node)) return node.map(renderMetadataText).join("");
	if (typeof node === "string" || typeof node === "number" || typeof node === "bigint") return escapeHtmlText(String(node));
	return "";
}
function renderMetadataAttributes(props, names) {
	const attributes = [];
	for (const name of names) {
		const value = Reflect.get(props, name);
		if (value === null || value === void 0 || typeof value === "boolean") continue;
		const htmlName = name === "hrefLang" ? "hreflang" : name;
		attributes.push(`${htmlName}="${escapeHtmlAttribute(String(value))}"`);
	}
	return attributes.length > 0 ? ` ${attributes.join(" ")}` : "";
}
function renderMetadataElementToHtml(node) {
	if (node === null || node === void 0 || typeof node === "boolean") return "";
	if (Array.isArray(node)) return node.map(renderMetadataElementToHtml).join("");
	if (!import_react_react_server.isValidElement(node)) return renderMetadataText(node);
	const props = typeof node.props === "object" && node.props !== null ? node.props : {};
	if (node.type === import_react_react_server.Fragment) return renderMetadataElementToHtml(Reflect.get(props, "children"));
	if (typeof node.type !== "string") return "";
	switch (node.type) {
		case "title": return `<title>${renderMetadataText(Reflect.get(props, "children"))}</title>`;
		case "meta": return `<meta${renderMetadataAttributes(props, [
			"name",
			"property",
			"content"
		])}>`;
		case "link": return `<link${renderMetadataAttributes(props, [
			"data-vinext-streamed-icon",
			"rel",
			"href",
			"hrefLang",
			"type",
			"sizes",
			"color",
			"media",
			"fetchPriority"
		])}>`;
		default: return "";
	}
}
function renderMetadataToHtml(metadata, pathname = "/", options) {
	return renderMetadataElementToHtml(MetadataHead({
		metadata,
		pathname,
		trailingSlash: options?.trailingSlash,
		streamedIconKey: options?.streamedIconKey
	}));
}
function MetadataHead({ metadata, pathname = "/", trailingSlash, streamedIconKey }) {
	const elements = [];
	let key = 0;
	const base = metadata.metadataBase;
	function resolveUrl(url) {
		if (!url) return void 0;
		return resolveMetadataUrl(url, base);
	}
	const title = typeof metadata.title === "string" ? metadata.title : typeof metadata.title === "object" ? metadata.title.absolute || metadata.title.default : void 0;
	if (title) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("title", { children: title }, key++));
	if (metadata.description) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
		name: "description",
		content: metadata.description
	}, key++));
	if (metadata.generator) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
		name: "generator",
		content: metadata.generator
	}, key++));
	if (metadata.applicationName) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
		name: "application-name",
		content: metadata.applicationName
	}, key++));
	if (metadata.referrer) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
		name: "referrer",
		content: metadata.referrer
	}, key++));
	if (metadata.keywords) {
		const kw = Array.isArray(metadata.keywords) ? metadata.keywords.join(",") : metadata.keywords;
		elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			name: "keywords",
			content: kw
		}, key++));
	}
	if (metadata.authors) {
		const authorList = Array.isArray(metadata.authors) ? metadata.authors : [metadata.authors];
		for (const author of authorList) {
			if (author.name) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
				name: "author",
				content: author.name
			}, key++));
			if (author.url) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("link", {
				rel: "author",
				href: author.url
			}, key++));
		}
	}
	if (metadata.creator) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
		name: "creator",
		content: metadata.creator
	}, key++));
	if (metadata.publisher) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
		name: "publisher",
		content: metadata.publisher
	}, key++));
	if (metadata.formatDetection) {
		const parts = [];
		if (metadata.formatDetection.telephone === false) parts.push("telephone=no");
		if (metadata.formatDetection.address === false) parts.push("address=no");
		if (metadata.formatDetection.email === false) parts.push("email=no");
		if (parts.length > 0) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			name: "format-detection",
			content: parts.join(", ")
		}, key++));
	}
	if (metadata.category) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
		name: "category",
		content: metadata.category
	}, key++));
	if (metadata.robots) if (typeof metadata.robots === "string") elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
		name: "robots",
		content: metadata.robots
	}, key++));
	else {
		const { googleBot, ...robotsRest } = metadata.robots;
		const robotParts = [];
		for (const [k, v] of Object.entries(robotsRest)) if (v === true) robotParts.push(k);
		else if (v === false) robotParts.push(`no${k}`);
		else if (typeof v === "string" || typeof v === "number") robotParts.push(`${k}:${v}`);
		if (robotParts.length > 0) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			name: "robots",
			content: robotParts.join(", ")
		}, key++));
		if (googleBot) if (typeof googleBot === "string") elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			name: "googlebot",
			content: googleBot
		}, key++));
		else {
			const gbParts = [];
			for (const [k, v] of Object.entries(googleBot)) if (v === true) gbParts.push(k);
			else if (v === false) gbParts.push(`no${k}`);
			else if (typeof v === "string" || typeof v === "number") gbParts.push(`${k}:${v}`);
			if (gbParts.length > 0) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
				name: "googlebot",
				content: gbParts.join(", ")
			}, key++));
		}
	}
	if (metadata.openGraph) {
		const og = metadata.openGraph;
		if (og.title) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			property: "og:title",
			content: og.title
		}, key++));
		if (og.description) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			property: "og:description",
			content: og.description
		}, key++));
		if (og.url) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			property: "og:url",
			content: resolveCanonicalUrl(og.url, base, pathname, trailingSlash)
		}, key++));
		if (og.siteName) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			property: "og:site_name",
			content: og.siteName
		}, key++));
		if (og.type) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			property: "og:type",
			content: og.type
		}, key++));
		if (og.locale) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			property: "og:locale",
			content: og.locale
		}, key++));
		if (og.publishedTime) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			property: "article:published_time",
			content: og.publishedTime
		}, key++));
		if (og.modifiedTime) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			property: "article:modified_time",
			content: og.modifiedTime
		}, key++));
		if (og.authors) for (const author of og.authors) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			property: "article:author",
			content: author
		}, key++));
		if (og.images) {
			const imgList = typeof og.images === "string" || og.images instanceof URL ? [{ url: og.images }] : Array.isArray(og.images) ? og.images : [og.images];
			for (const img of imgList) {
				elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
					property: "og:image",
					content: resolveSocialImageUrl(img, base)
				}, key++));
				if (typeof img !== "string" && !(img instanceof URL)) {
					if (img.width) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
						property: "og:image:width",
						content: String(img.width)
					}, key++));
					if (img.height) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
						property: "og:image:height",
						content: String(img.height)
					}, key++));
					if (img.type) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
						property: "og:image:type",
						content: img.type
					}, key++));
					if (img.alt) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
						property: "og:image:alt",
						content: img.alt
					}, key++));
				}
			}
		}
		if (og.videos) for (const video of og.videos) {
			elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
				property: "og:video",
				content: resolveUrl(video.url)
			}, key++));
			if (video.width) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
				property: "og:video:width",
				content: String(video.width)
			}, key++));
			if (video.height) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
				property: "og:video:height",
				content: String(video.height)
			}, key++));
		}
		if (og.audio) for (const audio of og.audio) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			property: "og:audio",
			content: resolveUrl(audio.url)
		}, key++));
	}
	if (metadata.twitter) {
		const tw = metadata.twitter;
		if (tw.card) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			name: "twitter:card",
			content: tw.card
		}, key++));
		if (tw.site) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			name: "twitter:site",
			content: tw.site
		}, key++));
		if (tw.siteId) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			name: "twitter:site:id",
			content: tw.siteId
		}, key++));
		if (tw.title) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			name: "twitter:title",
			content: tw.title
		}, key++));
		if (tw.description) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			name: "twitter:description",
			content: tw.description
		}, key++));
		if (tw.creator) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			name: "twitter:creator",
			content: tw.creator
		}, key++));
		if (tw.creatorId) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			name: "twitter:creator:id",
			content: tw.creatorId
		}, key++));
		if (tw.images) {
			const imgList = typeof tw.images === "string" || tw.images instanceof URL ? [tw.images] : Array.isArray(tw.images) ? tw.images : [tw.images];
			for (const img of imgList) {
				elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
					name: "twitter:image",
					content: resolveSocialImageUrl(img, base)
				}, key++));
				if (typeof img !== "string" && !(img instanceof URL)) {
					if (img.type) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
						name: "twitter:image:type",
						content: img.type
					}, key++));
					if (img.width) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
						name: "twitter:image:width",
						content: String(img.width)
					}, key++));
					if (img.height) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
						name: "twitter:image:height",
						content: String(img.height)
					}, key++));
					if (img.alt) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
						name: "twitter:image:alt",
						content: img.alt
					}, key++));
				}
			}
		}
		if (tw.card === "player" && tw.players) {
			const players = Array.isArray(tw.players) ? tw.players : [tw.players];
			for (const player of players) {
				const playerUrl = player.playerUrl.toString();
				const streamUrl = player.streamUrl.toString();
				elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
					name: "twitter:player",
					content: resolveUrl(playerUrl)
				}, key++));
				elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
					name: "twitter:player:stream",
					content: resolveUrl(streamUrl)
				}, key++));
				elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
					name: "twitter:player:width",
					content: String(player.width)
				}, key++));
				elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
					name: "twitter:player:height",
					content: String(player.height)
				}, key++));
			}
		}
		if (tw.card === "app" && tw.app) {
			const { app } = tw;
			for (const platform of [
				"iphone",
				"ipad",
				"googleplay"
			]) {
				if (app.name) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
					name: `twitter:app:name:${platform}`,
					content: app.name
				}, key++));
				if (app.id[platform]) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
					name: `twitter:app:id:${platform}`,
					content: String(app.id[platform])
				}, key++));
				if (app.url?.[platform]) {
					const appUrl = app.url[platform].toString();
					elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
						name: `twitter:app:url:${platform}`,
						content: resolveUrl(appUrl)
					}, key++));
				}
			}
		}
	}
	if (metadata.icons) {
		const iconEntries = isIconsMap(metadata.icons) ? normalizeUrlDescriptorEntries(metadata.icons.icon, (url) => ({ url })) : normalizeUrlDescriptorEntries(metadata.icons, (url) => ({ url }));
		let streamedIconOrder = 0;
		const appendIcons = (entries, defaultRel) => {
			for (const { url, rel, type, sizes, color, media, fetchPriority } of entries) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("link", {
				"data-vinext-streamed-icon": streamedIconKey ? `${streamedIconKey}:${streamedIconOrder++}` : void 0,
				rel: rel || defaultRel,
				href: stringifyUrl(url),
				type,
				sizes,
				color,
				media,
				fetchPriority
			}, key++));
		};
		if (isIconsMap(metadata.icons) && metadata.icons.shortcut) appendIcons(normalizeUrlDescriptorEntries(metadata.icons.shortcut, (url) => ({ url })), "shortcut icon");
		if (iconEntries.length > 0) appendIcons(iconEntries, "icon");
		if (isIconsMap(metadata.icons) && metadata.icons.apple) appendIcons(normalizeUrlDescriptorEntries(metadata.icons.apple, (url) => ({ url })), "apple-touch-icon");
		if (isIconsMap(metadata.icons) && metadata.icons.other) appendIcons(normalizeUrlDescriptorEntries(metadata.icons.other, (url) => ({ url })), "icon");
	}
	if (metadata.manifest) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("link", {
		rel: "manifest",
		href: stringifyUrl(metadata.manifest)
	}, key++));
	if (metadata.alternates) {
		const alt = metadata.alternates;
		if (alt.canonical) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("link", {
			rel: "canonical",
			href: resolveCanonicalUrl(alt.canonical, base, pathname, trailingSlash)
		}, key++));
		if (alt.languages) for (const [lang, href] of Object.entries(alt.languages)) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("link", {
			rel: "alternate",
			hrefLang: lang,
			href: resolveAlternateUrl(href, base, pathname, trailingSlash)
		}, key++));
		if (alt.media) for (const [media, href] of Object.entries(alt.media)) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("link", {
			rel: "alternate",
			media,
			href: resolveAlternateUrl(href, base, pathname, trailingSlash)
		}, key++));
		if (alt.types) for (const [type, href] of Object.entries(alt.types)) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("link", {
			rel: "alternate",
			type,
			href: resolveAlternateUrl(href, base, pathname, trailingSlash)
		}, key++));
	}
	if (metadata.verification) {
		const v = metadata.verification;
		if (v.google) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			name: "google-site-verification",
			content: v.google
		}, key++));
		if (v.yahoo) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			name: "y_key",
			content: v.yahoo
		}, key++));
		if (v.yandex) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			name: "yandex-verification",
			content: v.yandex
		}, key++));
		if (v.other) for (const [name, content] of Object.entries(v.other)) {
			const values = Array.isArray(content) ? content : [content];
			for (const val of values) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
				name,
				content: val
			}, key++));
		}
	}
	if (metadata.appleWebApp) {
		const awa = metadata.appleWebApp;
		if (awa.capable !== false) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			name: "mobile-web-app-capable",
			content: "yes"
		}, key++));
		if (awa.title) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			name: "apple-mobile-web-app-title",
			content: awa.title
		}, key++));
		if (awa.statusBarStyle) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			name: "apple-mobile-web-app-status-bar-style",
			content: awa.statusBarStyle
		}, key++));
		if (awa.startupImage) {
			const imgs = typeof awa.startupImage === "string" ? [{ url: awa.startupImage }] : awa.startupImage;
			for (const img of imgs) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("link", {
				rel: "apple-touch-startup-image",
				href: resolveUrl(img.url),
				...img.media ? { media: img.media } : {}
			}, key++));
		}
	}
	if (metadata.itunes) {
		const { appId, appArgument } = metadata.itunes;
		let content = `app-id=${appId}`;
		if (appArgument) content += `, app-argument=${appArgument}`;
		elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			name: "apple-itunes-app",
			content
		}, key++));
	}
	if (metadata.appLinks) {
		const al = metadata.appLinks;
		for (const platform of [
			"ios",
			"iphone",
			"ipad",
			"android",
			"windows_phone",
			"windows",
			"windows_universal",
			"web"
		]) {
			const entries = al[platform];
			if (!entries) continue;
			const list = Array.isArray(entries) ? entries : [entries];
			for (const entry of list) for (const [k, v] of Object.entries(entry)) {
				if (v === void 0 || v === null) continue;
				const str = String(v);
				const content = k === "url" ? resolveUrl(str) : str;
				elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
					property: `al:${platform}:${k}`,
					content
				}, key++));
			}
		}
	}
	if (metadata.other) for (const [name, content] of Object.entries(metadata.other)) {
		const values = Array.isArray(content) ? content : [content];
		for (const val of values) elements.push(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", {
			name,
			content: val
		}, key++));
	}
	return /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(import_jsx_runtime_react_server.Fragment, { children: elements });
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/routing/utils.js
var PATH_DELIMITER_REGEX = /([/#?\\]|%(2f|23|3f|5c))/gi;
function encodePathDelimiters(segment) {
	return segment.replace(PATH_DELIMITER_REGEX, (char) => encodeURIComponent(char));
}
/**
* Decode a filesystem or URL path segment while preserving encoded path delimiters.
* Mirrors Next.js segment-wise decoding so "%5F" becomes "_" but "%2F" stays "%2F".
*/
function decodeRouteSegment(segment) {
	try {
		return encodePathDelimiters(decodeURIComponent(segment));
	} catch {
		return segment;
	}
}
/**
* Strict variant for request pipelines that should reject malformed percent-encoding.
*/
function decodeRouteSegmentStrict(segment) {
	return encodePathDelimiters(decodeURIComponent(segment));
}
/**
* Normalize a pathname for route matching by decoding each segment independently.
* This prevents encoded slashes from turning into real path separators.
*/
function normalizePathnameForRouteMatch(pathname) {
	return pathname.split("/").map((segment) => decodeRouteSegment(segment)).join("/");
}
function splitPathnameForRouteMatch(pathname) {
	return normalizePathnameForRouteMatch(pathname).split("/").filter(Boolean);
}
/**
* Strict pathname normalization for live request handling.
* Throws on malformed percent-encoding so callers can return 400.
*/
function normalizePathnameForRouteMatchStrict(pathname) {
	return pathname.split("/").map((segment) => decodeRouteSegmentStrict(segment)).join("/");
}
function decodeMatchedParam(value) {
	try {
		return decodeURIComponent(value);
	} catch {
		return value;
	}
}
/**
* Build a params object from ordered entries, preserving insertion order.
*
* Used by trie matchers to reconstruct the params Record after collecting
* entries in declaration order via DFS backtracking. Object.create(null)
* avoids prototype pollution.
*
* @param entries - Ordered [paramName, value] tuples from forward traversal
*/
function buildParams(entries) {
	const params = Object.create(null);
	for (const [key, value] of entries) params[key] = value;
	return params;
}
/**
* Decode captured route params with `decodeURIComponent`, mirroring Next.js
* route-matcher.ts:25-27. Mutates the params object in place. Catch-all
* arrays are decoded element-wise. Malformed escapes are preserved (the
* strict normalization layer rejects them at the request boundary).
*/
function decodeMatchedParams(params) {
	for (const key of Object.keys(params)) {
		const value = params[key];
		if (Array.isArray(value)) params[key] = value.map(decodeMatchedParam);
		else params[key] = decodeMatchedParam(value);
	}
}
/** Split a pathname into its non-empty segments without decoding. */
function splitPathSegments(pathname) {
	return pathname.split("/").filter(Boolean);
}
/**
* Catch-all filesystem segment, e.g. `[...slug]`. Browser-safe predicate shared
* with the route graph's segment parsing (dynamicParamNameFromSegment) so the
* bracket conventions live in one place. The length guard rejects empty names
* (`[...]`).
*/
function isCatchAllSegment(segment) {
	return segment.startsWith("[...") && segment.endsWith("]") && segment.length > 5;
}
/**
* Optional-catch-all filesystem segment, e.g. `[[...slug]]`. Unlike a catch-all,
* this matches zero or more URL segments.
*/
function isOptionalCatchAllSegment(segment) {
	return segment.startsWith("[[...") && segment.endsWith("]]") && segment.length > 7;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/config/request-context.js
function parseCookies(cookieHeader) {
	return parseCookieHeader(cookieHeader);
}
function normalizeHost(hostHeader, fallbackHostname) {
	return (hostHeader ?? fallbackHostname).split(":", 1)[0].toLowerCase();
}
/** Build a lazily parsed request context from a Web Request. */
function requestContextFromRequest(request) {
	const url = new URL(request.url);
	let cookies;
	let query;
	return {
		headers: request.headers,
		get cookies() {
			return cookies ??= parseCookies(request.headers.get("cookie"));
		},
		get query() {
			return query ??= url.searchParams;
		},
		host: normalizeHost(request.headers.get("host"), url.hostname)
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/http-error-responses.js
var METHOD_NOT_ALLOWED_BODY_HEADERS = [
	"content-encoding",
	"content-length",
	"content-range",
	"content-type",
	"transfer-encoding"
];
function sanitizeMethodNotAllowedHeaders(headers, allowedMethods) {
	for (const name of METHOD_NOT_ALLOWED_BODY_HEADERS) headers.delete(name);
	headers.set("Allow", allowedMethods);
	headers.set("Content-Type", "text/plain; charset=utf-8");
}
/**
* Build a 400 Bad Request plain-text response.
*
* Used for malformed percent-encoding, invalid HTTP methods (where Next.js
* returns 400), and other request-shape validation failures.
*/
function badRequestResponse(init) {
	return new Response("Bad Request", {
		status: 400,
		headers: init?.headers
	});
}
/**
* Build a 404 Not Found plain-text response.
*
* The body matches Next.js's plain-text 404 response exactly. Next.js writes
* `res.end('This page could not be found')` (no trailing period) for the
* fallback 404 path; see in `.nextjs-ref`:
*   - packages/next/src/server/route-modules/pages/pages-handler.ts L121, L535
*   - packages/next/src/build/templates/app-route.ts L170, L349
*   - packages/next/src/build/templates/app-page.ts L701, L1043
* (The React-rendered not-found component in `packages/next/src/client/components/builtin/not-found.tsx`
* uses the same text with a trailing period — that variant is rendered as HTML,
* not returned as the plain-text body.)
*
* The `headers` option lets call sites merge middleware response headers into
* the 404, matching the pattern used by `app-rsc-handler` after a route match
* fails but middleware has already contributed headers.
*/
function notFoundResponse(init) {
	return new Response("This page could not be found", {
		status: 404,
		headers: init?.headers
	});
}
/**
* Build a 405 Method Not Allowed plain-text response with the `Allow` header set.
*
* `allowedMethods` is rendered as the comma-separated `Allow` header value.
* Existing headers (e.g. middleware response headers) can be merged via `init.headers`;
* the `Allow` header takes precedence and overwrites any colliding entry.
*/
function methodNotAllowedResponse(allowedMethods, init) {
	const headers = new Headers(init?.headers);
	sanitizeMethodNotAllowedHeaders(headers, allowedMethods);
	return new Response("Method Not Allowed", {
		status: 405,
		headers
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/open-redirect.js
/**
* Returns true if a request pathname looks like a protocol-relative open
* redirect, in either literal or percent-encoded form.
*
* A pathname is considered "open redirect shaped" when its first segment,
* after decoding backslashes and encoded delimiters, would cause a browser
* to resolve a `Location` containing the pathname as protocol-relative.
*/
function isOpenRedirectShaped(rawPathname) {
	if (!rawPathname.startsWith("/")) return false;
	const afterSlash = rawPathname.slice(1);
	if (afterSlash.startsWith("/") || afterSlash.startsWith("\\")) return true;
	if (afterSlash.length >= 3 && afterSlash[0] === "%") {
		const encoded = afterSlash.slice(0, 3).toLowerCase();
		if (encoded === "%5c" || encoded === "%2f") return true;
	}
	return false;
}
new URL("http://vinext.invalid/");
/**
* Shared request pipeline utilities.
*
* Extracted from generated entries and server hot paths to keep codegen focused
* on app shape while normal modules own request behavior. Some dev-server and
* worker-template setup code still has inline normalization that should be
* migrated in follow-up work.
*
* These utilities handle the common request lifecycle steps: protocol-
* relative URL guards, basePath stripping, trailing slash normalization,
* and CSRF origin validation.
*
* Plain-text error response builders (forbidden / not-found / etc.) live in
* `./http-error-responses.ts`.
*/
/**
* Guard against protocol-relative URL open redirects.
*
* Paths like `//example.com/` would be redirected to `//example.com` by the
* trailing-slash normalizer, which browsers interpret as `http://example.com`.
* Backslashes are equivalent to forward slashes in the URL spec
* (e.g. `/\evil.com` is treated as `//evil.com` by browsers).
*
* Next.js returns 404 for these paths. We check the RAW pathname before
* normalization so the guard fires before normalizePath collapses `//`.
*
* Percent-encoded variants are also blocked because:
*   - `%5C` decodes to `\` (browsers treat `/\evil.com` as `//evil.com`).
*   - `%2F` decodes to `/` (so `/%2F/evil.com` effectively becomes `//evil.com`).
* These forms survive segment-wise decoding that re-encodes path delimiters
* (e.g. `normalizePathnameForRouteMatchStrict`), so a later trailing-slash
* redirect would still echo the encoded form in its `Location` header. See
* `isOpenRedirectShaped` for the full list of rejected leading-segment forms.
*
* @param rawPathname - The raw pathname from the URL, before any normalization
* @returns A 404 Response if the path is protocol-relative, or null to continue
*/
function guardProtocolRelativeUrl(rawPathname) {
	if (isOpenRedirectShaped(rawPathname)) return notFoundResponse();
	return null;
}
var FILE_LIKE_PATHNAME_RE = /\.[^/]+\/?$/;
function isWellKnownPathname(pathname) {
	return pathname === "/.well-known" || pathname.startsWith("/.well-known/");
}
function createStaticFileSignal(pathname, context) {
	const headers = new Headers({ [VINEXT_STATIC_FILE_HEADER]: encodeURIComponent(pathname) });
	if (context.headers) for (const [key, value] of context.headers) headers.append(key, value);
	return new Response(null, {
		status: context.status ?? 200,
		headers
	});
}
/**
* Resolve the public/ filesystem-route slot in the Next.js routing order.
*
* Public files are checked after middleware and before afterFiles/fallback
* rewrites. The generated App Router entry provides the public-file set; this
* helper owns the RSC exclusion, existence-first method enforcement, and
* static-file signaling. Missing mutation targets continue through routing.
*/
function resolvePublicFileRoute(options) {
	if (options.pathname.endsWith(".rsc")) return null;
	if (!options.publicFiles.has(options.cleanPathname)) return null;
	if (options.request.method !== "GET" && options.request.method !== "HEAD") return methodNotAllowedResponse("GET, HEAD", { headers: options.middlewareContext.headers ?? void 0 });
	return createStaticFileSignal(options.cleanPathname, options.middlewareContext);
}
function normalizeTrailingSlashPathname(pathname, trailingSlash) {
	if (pathname === "/" || pathname === "/api" || pathname.startsWith("/api/")) return null;
	const hasTrailing = pathname.endsWith("/");
	if (trailingSlash) {
		if (isWellKnownPathname(pathname)) return null;
		if (FILE_LIKE_PATHNAME_RE.test(pathname)) {
			const normalized = removeTrailingSlash(pathname);
			return normalized === pathname ? null : normalized;
		}
		if (!hasTrailing && !pathname.endsWith(".rsc")) return `${pathname}/`;
		return null;
	}
	if (hasTrailing) return removeTrailingSlash(pathname);
	return null;
}
/**
* Check if the pathname needs a trailing slash redirect, and return the
* redirect Response if so.
*
* Follows Next.js behavior:
* - `/api` routes are never redirected
* - The root path `/` is never redirected
* - If `trailingSlash` is true, redirect `/about` → `/about/`
* - If `trailingSlash` is true, redirect file-looking `/file.ext/` → `/file.ext`
* - If `trailingSlash` is true, do not redirect `/.well-known/*`
* - If `trailingSlash` is false (default), redirect `/about/` → `/about`
*
* @param pathname - The basePath-stripped pathname
* @param basePath - The basePath to prepend to the redirect Location
* @param trailingSlash - Whether trailing slashes should be enforced
* @param search - The query string (including `?`) to preserve in the redirect
* @returns A 308 redirect Response, or null if no redirect is needed
*/
function normalizeTrailingSlash(pathname, basePath, trailingSlash, search) {
	if (pathname === "/" || pathname === "/api" || pathname.startsWith("/api/")) return null;
	if (isOpenRedirectShaped(pathname)) return notFoundResponse();
	const normalizedPathname = normalizeTrailingSlashPathname(pathname, trailingSlash);
	if (normalizedPathname === null) return null;
	const encodedPathname = normalizedPathname.replace(/[^A-Za-z0-9\-._~!$&'()*+,;=:@/%]/gu, encodeURIComponent);
	return new Response(null, {
		status: 308,
		headers: { Location: basePath + encodedPathname + search }
	});
}
/**
* Strip internal `x-middleware-*` headers from a Headers object.
*
* Middleware uses `x-middleware-*` headers as internal signals (e.g.
* `x-middleware-next`, `x-middleware-rewrite`, `x-middleware-request-*`).
* Consumed protocol headers must be removed before sending the response to the
* client. Next.js exposes truthy unconsumed `x-middleware-request-*` values as
* literal request and response headers, so those are intentionally preserved.
*
* @param headers - The Headers object to modify in place
*/
function processMiddlewareHeaders(headers) {
	const keysToDelete = [];
	const unconsumedRequestHeaders = getUnconsumedMiddlewareRequestHeaders(headers);
	for (const key of headers.keys()) if (key.startsWith("x-middleware-") && key !== "x-middleware-cache" && !unconsumedRequestHeaders.has(key)) keysToDelete.push(key);
	for (const key of keysToDelete) headers.delete(key);
}
var STRIPPED_INTERNAL_HEADERS = /* @__PURE__ */ new Set([...INTERNAL_HEADERS, ...VINEXT_INTERNAL_HEADERS]);
/**
* Strip internal headers from an inbound request so they cannot be forged by
* an external attacker to influence routing or impersonate internal state.
*
* Must be called at every request entry point BEFORE middleware, routing,
* or any handler logic accesses the request headers.
*
* Returns a new Headers object with internal headers removed. The input
* is never mutated — Request.headers is immutable in Workers/miniflare
* environments (see applyMiddlewareRequestHeaders in config-matchers.ts
* for the same cloning pattern).
*
* @param headers - The source Headers (never modified)
* @returns A new Headers with internal framework headers removed
*/
function filterInternalHeaders(headers) {
	const filtered = new Headers();
	for (const [key, value] of headers) if (!STRIPPED_INTERNAL_HEADERS.has(key.toLowerCase())) filtered.append(key, value);
	return filtered;
}
function getRequestCf(request) {
	const cf = Reflect.get(request, "cf");
	return cf === void 0 ? void 0 : cf;
}
/**
* Re-attach the Workers-specific `cf` metadata from `source` onto a rebuilt
* Request. `new Request()` never copies it, and middleware/authorization code
* can key off `request.cf` (geo checks, bot scores), so every reconstruction
* must restore it explicitly.
*/
function attachRequestCfMetadata(target, source) {
	const cf = getRequestCf(source);
	if (cf !== void 0) Object.defineProperty(target, "cf", {
		value: cf,
		enumerable: true,
		configurable: true
	});
	return target;
}
/**
* Clone a Request while overriding headers, preserving metadata when possible.
*
* Some runtimes (Workers) allow `new Request(request, { headers })` which
* retains redirect/signal/cf data. Others (Node/undici across realms) can throw
* when cloning a foreign Request instance. In that case, fall back to building
* a RequestInit with best-effort metadata.
*/
function cloneRequestWithHeaders(request, headers) {
	let cloned;
	try {
		cloned = new Request(request, { headers });
	} catch {
		const init = {
			method: request.method,
			headers,
			body: request.body ?? void 0,
			redirect: request.redirect,
			signal: request.signal,
			integrity: request.integrity,
			cache: request.cache,
			mode: request.mode,
			credentials: request.credentials,
			referrer: request.referrer,
			referrerPolicy: request.referrerPolicy
		};
		if (request.body) init.duplex = "half";
		cloned = new Request(request.url, init);
	}
	return attachRequestCfMetadata(cloned, request);
}
/**
* Clone a Request while overriding the URL, preserving headers and metadata
* when possible.
*
* Mirrors `cloneRequestWithHeaders`, but rewrites the URL instead of the
* headers. Workers support `new Request(url, request)` to copy method/headers/
* body onto a new URL; Node/undici can throw on a foreign Request instance, so
* we fall back to a manual RequestInit. `new Request()` does not copy the
* Workers-specific `cf` property and omits `duplex` for streaming bodies, so
* both are handled explicitly — the same reasons `cloneRequestWithHeaders`
* exists.
*/
function cloneRequestWithUrl(request, url) {
	let cloned;
	try {
		cloned = new Request(url, request);
	} catch {
		const init = {
			method: request.method,
			headers: request.headers,
			body: request.body ?? void 0,
			redirect: request.redirect,
			signal: request.signal,
			integrity: request.integrity,
			cache: request.cache,
			mode: request.mode,
			credentials: request.credentials,
			referrer: request.referrer,
			referrerPolicy: request.referrerPolicy
		};
		if (request.body) init.duplex = "half";
		cloned = new Request(url, init);
	}
	return attachRequestCfMetadata(cloned, request);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/domain-locale.js
function normalizeDomainHostname(hostname) {
	if (!hostname) return void 0;
	return hostname.split(",", 1)[0]?.trim().split(":", 1)[0]?.toLowerCase() || void 0;
}
/**
* Match a configured domain either by hostname or locale.
* When both are provided, the checks intentionally use OR semantics so the
* same helper can cover Next.js's hostname lookup and preferred-locale lookup.
* If both are passed, the first domain matching either input wins, so callers
* should pass hostname or detectedLocale, not both.
*/
function detectDomainLocale(domainItems, hostname, detectedLocale) {
	if (!domainItems?.length) return void 0;
	const normalizedHostname = normalizeDomainHostname(hostname);
	const normalizedLocale = detectedLocale?.toLowerCase();
	for (const item of domainItems) if (normalizedHostname === normalizeDomainHostname(item.domain) || normalizedLocale === item.defaultLocale.toLowerCase() || item.locales?.some((locale) => locale.toLowerCase() === normalizedLocale)) return item;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/pages-i18n.js
/**
* Prepend the default locale prefix to a pathname when i18n is configured and
* the path does not already carry a locale prefix. Mirrors Next.js's
* server-side path normalisation in `resolve-routes.ts` (lines ~250-263):
*
*   if (!initialLocaleResult.detectedLocale && !pathname.startsWith('/_next/')) {
*     parsedUrl.pathname = `/${defaultLocale}${pathname === '/' ? '' : pathname}`
*   }
*
* Run this **before** matching against `next.config.js` redirects/rewrites
* (which are emitted by `applyLocaleToRoutes` in locale-prefixed forms) so
* that requests arriving without a locale prefix still match those rules.
*
* Skips internal paths that Next.js leaves alone:
*   - `/_next/*` (build assets, prerender manifests, image optimisation)
*   - `/__vinext/*` (vinext-internal endpoints)
*
* Returns the input unchanged when i18n is not configured or when the path
* already starts with one of the configured locales. The host-based default
* locale (i18n.domains[].defaultLocale) is preferred over the global default
* when supplied, matching Next.js's `domainLocale.defaultLocale` branch.
*
* Item 4 of issue #1336: without this normalisation, requests like
* `/to-sv` (default locale = en) against a rule `source: '/:locale/to-sv'`
* with `locale: false` do not match because there is no segment for
* `:locale`. After normalisation the request looks like `/en/to-sv` and
* the rule matches with `:locale=en`.
*
* Ported from Next.js: packages/next/src/server/lib/router-utils/resolve-routes.ts
* https://github.com/vercel/next.js/blob/canary/packages/next/src/server/lib/router-utils/resolve-routes.ts
*/
function normalizeDefaultLocalePathname(pathname, i18n, options = {}) {
	if (!i18n) return pathname;
	if (pathname.startsWith("/_next/") || pathname.startsWith("/__vinext/")) return pathname;
	const parts = pathname.split("/", 3);
	if (parts[1] && i18n.locales.includes(parts[1])) return pathname;
	const defaultLocale = detectDomainLocale(i18n.domains, options.hostname ?? void 0)?.defaultLocale ?? i18n.defaultLocale;
	if (pathname === "/") return `/${defaultLocale}`;
	return `/${defaultLocale}${pathname}`;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/deps/.pnpm/pathslash@0.1.0/deps/pathslash/dist/index.js
var BACKSLASH_RE = /\\/g;
var isWindows = process.platform === "win32";
/**
* Flip backslashes to forward slashes, used to slash-ify `node:path.win32`
* output. `\\?\` (extended-length) paths are left untouched: there a forward
* slash is a literal character, not a separator.
*/
var toForwardSlash = (path) => path.startsWith("\\\\?\\") ? path : path.replace(BACKSLASH_RE, "/");
var w = path.win32;
function slashed(fn) {
	return (...args) => toForwardSlash(fn(...args));
}
var win32 = {
	resolve: slashed(w.resolve),
	normalize: slashed(w.normalize),
	join: slashed(w.join),
	relative: slashed(w.relative),
	dirname: slashed(w.dirname),
	format: slashed(w.format),
	parse: (path) => {
		const parsed = w.parse(path);
		parsed.root = toForwardSlash(parsed.root);
		parsed.dir = toForwardSlash(parsed.dir);
		return parsed;
	},
	basename: w.basename,
	extname: w.extname,
	isAbsolute: w.isAbsolute,
	matchesGlob: w.matchesGlob,
	toNamespacedPath: w.toNamespacedPath,
	delimiter: w.delimiter,
	sep: "/"
};
var posix = { ...path.posix };
posix.posix = win32.posix = posix;
posix.win32 = win32.win32 = win32;
var path$1 = isWindows ? win32 : posix;
var { basename, delimiter, dirname, extname, format, isAbsolute, join, matchesGlob, normalize, parse, relative, resolve, sep, toNamespacedPath } = path$1;
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/instrumentation.js
/**
* Get the registered onRequestError handler (if any).
*
* Reads from globalThis so it works across Vite environment boundaries.
*/
function getOnRequestErrorHandler() {
	return globalThis.__VINEXT_onRequestErrorHandler__ ?? null;
}
/**
* Report a request error via the instrumentation handler.
*
* No-op if no onRequestError handler is registered.
*
* Reads the handler from globalThis so this function works correctly regardless
* of which environment it is called from.
*/
function reportRequestError(error, request, context) {
	const handler = getOnRequestErrorHandler();
	if (!handler) return Promise.resolve();
	const promise = (async () => {
		try {
			await handler(error, request, context);
		} catch (reportErr) {
			console.error("[vinext] onRequestError handler threw:", reportErr instanceof Error ? reportErr.message : String(reportErr));
		}
	})();
	getRequestExecutionContext()?.waitUntil(promise);
	return promise;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-render-identity.js
function normalizeAppPageRenderMatchedPathname(pathname) {
	if (!pathname.startsWith("/")) throw new Error(`[vinext] App Router render pathname must be absolute: ${pathname}`);
	return normalizePath(normalizePathnameForRouteMatch(pathname));
}
function normalizeAppPageInterceptionProofPathname(pathname) {
	if (pathname === null || !isInterceptionMatchedUrlPath(pathname)) return null;
	return normalizeAppPageRenderMatchedPathname(pathname);
}
function createAppPageRenderIdentity(input) {
	const interceptionContext = input.interceptionContext ?? null;
	const targetMatchedPathname = normalizeAppPageRenderMatchedPathname(input.targetMatchedPathname ?? input.displayPathname);
	const requestedMatchedRoutePathname = normalizeAppPageRenderMatchedPathname(input.matchedRoutePathname ?? input.targetMatchedPathname ?? input.displayPathname);
	const sourceMatchedPathname = normalizeAppPageInterceptionProofPathname(input.interceptSourceMatchedUrl ?? null);
	const slotId = input.interceptSlotId ?? null;
	const matchedRoutePathname = sourceMatchedPathname ?? requestedMatchedRoutePathname;
	const routeId = AppElementsWire.encodeRouteId(matchedRoutePathname, null);
	const pageId = AppElementsWire.encodePageId(matchedRoutePathname, null);
	const interception = sourceMatchedPathname === null || slotId === null ? null : {
		sourceMatchedUrl: sourceMatchedPathname,
		sourceRouteId: AppElementsWire.encodeRouteId(sourceMatchedPathname, null),
		slotId,
		targetMatchedUrl: targetMatchedPathname,
		targetRouteId: AppElementsWire.encodeRouteId(targetMatchedPathname, null)
	};
	return {
		displayPathname: input.displayPathname,
		interception,
		interceptionContext,
		matchedRoutePathname,
		pageId,
		routeId,
		targetMatchedPathname
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/isr-cache.js
function getRevalidateSecret() {
	return "60293c7f9de7cae81d06d08970f4edb26a13bc0d99040c9ad1334e5aaf302162";
}
/**
* Constant-time string equality. Avoids leaking secret length / prefix via
* early-exit timing on the on-demand revalidation auth check. Returns false
* for length mismatch (the only safe option without revealing the secret
* length, and equality is impossible anyway).
*/
function safeEqual(a, b) {
	if (a.length !== b.length) return false;
	let mismatch = 0;
	for (let i = 0; i < a.length; i++) mismatch |= a.charCodeAt(i) ^ b.charCodeAt(i);
	return mismatch === 0;
}
function isRevalidateSecret(value) {
	if (typeof value !== "string" || value.length === 0) return false;
	return safeEqual(value, getRevalidateSecret());
}
/**
* Authorize an incoming request as an on-demand revalidation trigger. Mirrors
* Next.js's `checkIsOnDemandRevalidate`: the {@link PRERENDER_REVALIDATE_HEADER}
* value must *equal* the process revalidate secret. Header presence alone is
* NOT sufficient — see the security note on {@link PRERENDER_REVALIDATE_HEADER}.
*/
function isOnDemandRevalidateRequest(headerValue) {
	if (typeof headerValue !== "string") return false;
	return isRevalidateSecret(headerValue);
}
/**
* Get a cache entry with staleness information.
*
* Returns { value, isStale: false } for fresh entries,
* { value, isStale: true } for stale-but-usable entries,
* { value, isStale: true, isExpired: true } for entries that must be retained
* as regeneration input but not served, or null for cache misses.
*/
async function isrGet(key) {
	const result = await getCdnCacheAdapter().get(key);
	if (!result) return null;
	const isExpired = result.cacheState === "expired";
	return {
		value: result,
		isStale: isExpired || result.cacheState === "stale",
		...isExpired ? { isExpired: true } : {}
	};
}
/**
* Assemble cache-control metadata, omitting the dimensions the producing
* render made no claim about. Shared by every ISR writer so `expire`/`stale`
* are never invented from `revalidate`.
*/
function isrCacheControl(revalidateSeconds, claims = {}) {
	return {
		revalidate: revalidateSeconds,
		...claims.expireSeconds === void 0 ? {} : { expire: claims.expireSeconds },
		...claims.staleSeconds === void 0 ? {} : { stale: claims.staleSeconds }
	};
}
/**
* Store a value in the ISR cache under the given write policy.
*/
async function isrSet(key, data, policy) {
	await getCdnCacheAdapter().set(key, data, {
		cacheControl: policy.cacheControl,
		revalidate: policy.cacheControl.revalidate,
		tags: policy.tags ?? []
	});
}
async function isrSetPrerenderedAppPage(key, data, metadata) {
	const revalidateSeconds = metadata.revalidateSeconds;
	const tags = metadata.tags;
	if (process.env.NEXT_PRIVATE_DEBUG_CACHE) console.debug("[vinext] ISR: seed", key);
	const ctx = {};
	if (revalidateSeconds !== void 0) {
		ctx.revalidate = revalidateSeconds;
		ctx.cacheControl = isrCacheControl(revalidateSeconds, metadata);
	}
	if (tags && tags.length > 0) ctx.tags = tags;
	await getCdnCacheAdapter().set(key, data, ctx);
	if (revalidateSeconds !== void 0) setRevalidateDuration(key, revalidateSeconds);
}
var _PENDING_REGEN_KEY = Symbol.for("vinext.isrCache.pendingRegenerations");
var _g$4 = globalThis;
var pendingRegenerations = _g$4[_PENDING_REGEN_KEY] ??= /* @__PURE__ */ new Map();
var _PENDING_ON_DEMAND_REGEN_KEY = Symbol.for("vinext.isrCache.pendingOnDemandRegenerations");
_g$4[_PENDING_ON_DEMAND_REGEN_KEY] ??= /* @__PURE__ */ new Map();
/**
* Trigger a background regeneration for a cache key.
*
* If a regeneration for this key is already in progress, this is a no-op.
* The renderFn should produce the new cache value and call isrSet internally.
*
* On Cloudflare Workers the regeneration promise is registered with
* `ctx.waitUntil()` via the ALS-backed ExecutionContext, keeping the isolate
* alive until the regeneration completes even after the Response is returned.
*
* When `errorContext` is provided and the render function fails, the error
* is reported via `reportRequestError` (instrumentation hook) with
* `revalidateReason: "stale"`.
*/
function triggerBackgroundRegeneration(key, renderFn, errorContext) {
	if (!getCdnCacheAdapter().ownsBackgroundRevalidation) return;
	if (pendingRegenerations.has(key)) return;
	const promise = renderFn().catch((err) => {
		console.error(`[vinext] ISR background regeneration failed for ${key}:`, err);
		if (errorContext) reportRequestError(err instanceof Error ? err : new Error(String(err)), {
			path: key,
			method: "GET",
			headers: {}
		}, {
			routerKind: errorContext.routerKind,
			routePath: errorContext.routePath,
			routeType: errorContext.routeType,
			revalidateReason: "stale"
		});
	}).finally(() => {
		pendingRegenerations.delete(key);
	});
	pendingRegenerations.set(key, promise);
	getRequestExecutionContext()?.waitUntil(promise);
}
/**
* Build a CachedAppPageValue for the App Router ISR cache.
*/
function buildAppPageCacheValue(html, rscData, status, renderObservation, headers) {
	const value = {
		kind: "APP_PAGE",
		html,
		rscData,
		headers,
		postponed: void 0,
		status
	};
	if (renderObservation) value.renderObservation = renderObservation;
	return value;
}
function normalizeCachePathname(pathname) {
	return pathname === "/" ? "/" : pathname.replace(/\/$/, "");
}
function buildCacheKey(prefix, pathname, suffix) {
	const normalized = normalizeCachePathname(pathname);
	const suffixPart = suffix ? `:${suffix}` : "";
	const key = `${prefix}:${normalized}${suffixPart}`;
	if (key.length <= 200) return key;
	return `${prefix}:__hash:${fnv1a64(normalized)}${suffixPart}`;
}
/**
* Compute an ISR cache key for a given router type and pathname.
* Long pathnames are hashed to stay within KV key-length limits (512 bytes).
*/
function isrCacheKey(router, pathname, buildId) {
	return buildCacheKey(buildId ? `${router}:${buildId}` : router, pathname);
}
/**
* Compute an App Router ISR key for one cache artifact.
*
* App pages store HTML, RSC payloads, and route-handler responses separately.
* The suffix mirrors Next.js's separate on-disk app artifacts while keeping the
* Cloudflare KV key under its 512-byte limit for long pathnames.
*/
function appIsrCacheKey(pathname, suffix, buildId = "b4523198-dfc7-489f-8799-b05bddd8e10b") {
	return buildCacheKey(buildId ? `app:${buildId}` : "app", pathname, suffix);
}
function appIsrHtmlKey(pathname) {
	return appIsrCacheKey(pathname, "html");
}
function normalizeInterceptionContextForCacheKey(interceptionContext) {
	return normalizeAppPageInterceptionProofPathname(interceptionContext);
}
/**
* Build the ISR cache key for an RSC payload.
*
* Variants are sequenced in order: `source:<hash>` (intercepted source context,
* only when an interception context is present), `slots:<hash>` (mounted parallel
* route slots), and optionally `<render-mode-variant>` (for example,
* `prefetch-loading-shell`). Existing cached entries under the old format will
* become unreachable after deployment. This is acceptable because ISR entries
* have TTLs and will be regenerated on the next request.
*/
function appIsrRscKey(pathname, mountedSlotsHeader, renderMode = APP_RSC_RENDER_MODE_NAVIGATION, interceptionContext) {
	const normalizedMountedSlotsHeader = normalizeMountedSlotsHeader(mountedSlotsHeader);
	const sourceVariant = interceptionContext === void 0 || interceptionContext === null ? null : normalizeInterceptionContextForCacheKey(interceptionContext);
	const variant = [
		sourceVariant ? `source:${fnv1a64(sourceVariant)}` : null,
		normalizedMountedSlotsHeader ? `slots:${fnv1a64(normalizedMountedSlotsHeader)}` : null,
		getRscRenderModeCacheVariant(renderMode)
	].filter((part) => part !== null).join(":");
	return appIsrCacheKey(pathname, variant ? `rsc:${variant}` : "rsc");
}
function appIsrRouteKey(pathname) {
	return appIsrCacheKey(pathname, "route");
}
var MAX_REVALIDATE_ENTRIES = 1e4;
var _REVALIDATE_KEY = Symbol.for("vinext.isrCache.revalidateDurations");
var revalidateDurations = _g$4[_REVALIDATE_KEY] ??= /* @__PURE__ */ new Map();
/**
* Store the revalidate duration for a cache key.
* Uses insertion-order LRU eviction to prevent unbounded growth.
*/
function setRevalidateDuration(key, seconds) {
	revalidateDurations.delete(key);
	revalidateDurations.set(key, seconds);
	while (revalidateDurations.size > MAX_REVALIDATE_ENTRIES) {
		const first = revalidateDurations.keys().next().value;
		if (first !== void 0) revalidateDurations.delete(first);
		else break;
	}
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/query.js
/**
* Merge the original request URL's query parameters into a rewrite-target URL.
*
* Matches Next.js behavior: original query params are preserved on rewrites,
* but the rewrite-target URL wins on key conflicts. Ported from Next.js
* `Object.assign(parsedUrl.query, rewrittenParsedUrl.query)` in
* route-modules/route-module.ts.
*
* https://github.com/vercel/next.js/blob/canary/packages/next/src/server/route-modules/route-module.ts
*
* The fragment from `rewriteUrl` is preserved (origin/pathname always come
* from the rewrite target). Absolute rewrite URLs are returned unchanged when
* the origin differs from the original — external rewrites are proxied
* elsewhere and shouldn't have local query params smuggled in.
*/
function mergeRewriteQuery(originalUrl, rewriteUrl) {
	const originalSearchIndex = originalUrl.indexOf("?");
	if (originalSearchIndex === -1) return rewriteUrl;
	const originalQuery = originalUrl.slice(originalSearchIndex + 1).split("#")[0];
	if (!originalQuery) return rewriteUrl;
	const hashIndex = rewriteUrl.indexOf("#");
	const beforeHash = hashIndex === -1 ? rewriteUrl : rewriteUrl.slice(0, hashIndex);
	const hash = hashIndex === -1 ? "" : rewriteUrl.slice(hashIndex);
	const queryIndex = beforeHash.indexOf("?");
	const base = queryIndex === -1 ? beforeHash : beforeHash.slice(0, queryIndex);
	const rewriteQuery = queryIndex === -1 ? "" : beforeHash.slice(queryIndex + 1);
	const merged = new URLSearchParams(originalQuery);
	const rewriteParams = new URLSearchParams(rewriteQuery);
	const rewriteKeys = /* @__PURE__ */ new Set();
	for (const key of rewriteParams.keys()) rewriteKeys.add(key);
	for (const key of rewriteKeys) merged.delete(key);
	for (const [key, value] of rewriteParams) merged.append(key, value);
	const search = merged.toString();
	return `${base}${search ? `?${search}` : ""}${hash}`;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/csp.js
var ESCAPE_REGEX = /[&><\u2028\u2029]/;
function getScriptNonceFromHeader(cspHeaderValue) {
	const directives = cspHeaderValue.split(";").map((directive) => directive.trim());
	const directive = directives.find((value) => value.startsWith("script-src")) ?? directives.find((value) => value.startsWith("default-src"));
	if (!directive) return;
	const nonce = directive.split(" ").slice(1).map((source) => source.trim()).find((source) => source.startsWith("'nonce-") && source.length > 8 && source.endsWith("'"))?.slice(7, -1);
	if (!nonce) return;
	if (ESCAPE_REGEX.test(nonce)) throw new Error("Nonce value from Content-Security-Policy contained HTML escape characters.\nLearn more: https://nextjs.org/docs/messages/nonce-contained-invalid-characters");
	return nonce;
}
function getScriptNonceFromHeaders(headers) {
	const csp = headers?.get("content-security-policy") ?? headers?.get("content-security-policy-report-only");
	if (!csp) return;
	return getScriptNonceFromHeader(csp);
}
function getScriptNonceFromHeaderSources(...headersList) {
	for (const headers of headersList) {
		const nonce = getScriptNonceFromHeaders(headers);
		if (nonce) return nonce;
	}
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/pages-data-route.js
/**
* Helpers for the Pages Router `/_next/data/{buildId}/{...page}.json` endpoint.
*
* Next.js uses this endpoint for client-side navigations in the Pages Router:
* `next/link` and `router.push()` fetch `pageProps` from this URL instead of
* doing a full HTML navigation. The server must:
*   1. Match the URL pattern and extract the page pathname (with the buildId
*      and `.json` extension removed, locale prefix preserved).
*   2. Normalize the URL BEFORE middleware runs so middleware sees the page
*      path (e.g. `/about`) rather than the raw `/_next/data/.../about.json`.
*   3. Invoke the same `getServerSideProps` / `getStaticProps` machinery as
*      the HTML page and serialize the resulting props as a JSON envelope:
*      `{ pageProps: ... }` with `Content-Type: application/json`.
*
* Ported from Next.js:
*   - `packages/next/src/server/normalizers/request/next-data.ts` — prefix/suffix matcher.
*   - `packages/next/src/server/base-server.ts` (`handleNextDataRequest`) — pipeline normalization.
*   - `packages/next/src/server/render.tsx` — JSON envelope emission (`isNextDataRequest`).
*/
var NEXT_DATA_PREFIX = "/_next/data/";
var NEXT_DATA_SUFFIX = ".json";
/**
* Returns true if the pathname looks like a `_next/data` request, regardless
* of buildId. Used by the request pipeline to short-circuit before middleware
* even when the buildId is wrong (so we can still return a 404 JSON response).
*/
function isNextDataPathname(pathname) {
	return pathname.startsWith(NEXT_DATA_PREFIX) && pathname.endsWith(NEXT_DATA_SUFFIX);
}
/**
* Parse `/_next/data/<buildId>/<...page>.json` and return the normalized page
* pathname. Returns `null` if the pathname does not match the pattern or if
* the buildId segment does not match the server's buildId.
*
* The returned `pagePathname` is the page route path Next.js would render for
* the equivalent HTML navigation — including any locale prefix, which is then
* stripped by `resolvePagesI18nRequest` downstream.
*
* `/_next/data/<buildId>/about.json`         → `/about`
* `/_next/data/<buildId>/en/about.json`      → `/en/about`
* `/_next/data/<buildId>/index.json`         → `/`
* `/_next/data/<buildId>/en.json`            → `/en`
* `/_next/data/<wrong-id>/about.json`        → null
* `/_next/data/<buildId>/about`              → null  (missing .json suffix)
*/
function parseNextDataPathname(pathname, buildId) {
	if (!buildId) return null;
	if (!isNextDataPathname(pathname)) return null;
	const expectedPrefix = `${NEXT_DATA_PREFIX}${buildId}/`;
	if (!pathname.startsWith(expectedPrefix)) return null;
	const rest = pathname.slice(expectedPrefix.length, -5);
	if (rest.length === 0) return null;
	if (rest === "index") return { pagePathname: "/" };
	if (rest.endsWith("/index")) return { pagePathname: `/${rest.slice(0, -6)}` };
	if (rest.startsWith("index/")) return { pagePathname: `/${rest.slice(6)}` };
	return { pagePathname: `/${rest}` };
}
function normalizeNextDataPagePathname(pagePathname, trailingSlash = false) {
	if (!trailingSlash || pagePathname === "/" || pagePathname.endsWith("/")) return pagePathname;
	return `${pagePathname}/`;
}
/**
* Build the 404 response Next.js returns for an unknown `_next/data` page.
* Next.js renders this as a normal 404 page, but the body shape that clients
* see for a missing page-data endpoint is the literal string `"{ }"` for the
* body and a 404 status with `application/json` so client-side hard-navigation
* fallback fires (see `__N_SSP` handling in `router.ts`).
*
* We match Next.js' behavior: 404 status + JSON content type. The body is an
* empty JSON object so clients that blindly call `res.json()` do not throw
* before checking the status code.
*/
function buildNextDataNotFoundResponse() {
	return new Response("{}", {
		status: 404,
		headers: { "Content-Type": "application/json" }
	});
}
/**
* Detect and normalize `/_next/data/<buildId>/<page>.json` requests in one
* place so the Pages Router pipeline and middleware shim do not need to know
* about the data-endpoint protocol.
*
* Returns:
* - `isDataReq: false, notFoundResponse: null` — not a data request.
* - `isDataReq: true, normalizedPathname: null` — looks like a data URL but
*   the buildId does not match. Callers may defer `notFoundResponse` until
*   after middleware so `skipProxyUrlNormalize` middleware can intercept the
*   original URL.
* - `isDataReq: true` — valid data request; `request` is re-pointed at the
*   normalized page path, `normalizedPathname` carries the bare page path, and
*   `search` carries the original query string for callers that need to
*   preserve it.
*
* Extracted from `entries/pages-server-entry.ts` so both `renderPage` and
* `runMiddleware` share a single implementation.
*/
function normalizePagesDataRequest(request, buildId, basePath = "", trailingSlash = false) {
	const reqUrl = new URL(request.url);
	const hadBasePath = !!basePath && hasBasePath(reqUrl.pathname, basePath);
	const dataPathname = basePath ? stripBasePath(reqUrl.pathname, basePath) : reqUrl.pathname;
	if (!isNextDataPathname(dataPathname)) return {
		isDataReq: false,
		request,
		normalizedPathname: null,
		search: "",
		notFoundResponse: null
	};
	const dataMatch = buildId ? parseNextDataPathname(dataPathname, buildId) : null;
	if (!dataMatch) return {
		isDataReq: true,
		request,
		normalizedPathname: null,
		search: reqUrl.search,
		notFoundResponse: buildNextDataNotFoundResponse()
	};
	const pagePathname = normalizeNextDataPagePathname(dataMatch.pagePathname, trailingSlash);
	const normalizedUrl = new URL(reqUrl);
	normalizedUrl.pathname = hadBasePath ? addBasePathToPathname(pagePathname, basePath) : pagePathname;
	return {
		isDataReq: true,
		request: new Request(normalizedUrl, request),
		normalizedPathname: pagePathname,
		search: reqUrl.search,
		notFoundResponse: null
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/image-optimization.js
/**
* Returns true when `pathname` is either supported image optimization
* endpoint.
*
* A single trailing slash is accepted (`/_next/image/`): with
* `trailingSlash: true`, Next.js 308-redirects `/_next/image?url=...` to
* `/_next/image/?url=...` and then serves the slashed form — its route
* matching strips a trailing slash before matching internal paths (see
* getItem in packages/next/src/server/lib/router-utils/filesystem.ts).
* Rejecting the slashed form 404'd every dev-mode next/image request under
* `trailingSlash: true`.
*/
function isImageOptimizationPath(pathname) {
	if (pathname.length > 1 && pathname.endsWith("/")) pathname = pathname.slice(0, -1);
	return pathname === "/_next/image" || pathname === "/_vinext/image";
}
/**
* Next.js default device sizes and image sizes.
* These are the allowed widths for image optimization when no custom
* config is provided. Matches Next.js defaults exactly.
*/
var DEFAULT_DEVICE_SIZES = [
	640,
	750,
	828,
	1080,
	1200,
	1920,
	2048,
	3840
];
var DEFAULT_IMAGE_SIZES = [
	32,
	48,
	64,
	96,
	128,
	256,
	384
];
var DEV_BLUR_MAX_WIDTH = 8;
var DEV_BLUR_QUALITY = 70;
function resolveDevImageRedirect(requestUrl, allowedWidths = [...DEFAULT_DEVICE_SIZES, ...DEFAULT_IMAGE_SIZES], allowedQualities, options = { isDev: true }) {
	const params = parseImageParams(requestUrl, allowedWidths, allowedQualities, options);
	if (!params) return null;
	if (params.imageUrl.startsWith("/@") || params.imageUrl.startsWith("/__vite") || params.imageUrl.startsWith("/node_modules")) return null;
	const resolved = new URL(params.imageUrl, requestUrl.origin);
	if (resolved.origin !== requestUrl.origin) return null;
	return resolved.pathname + resolved.search;
}
/**
* Parse and validate image optimization query parameters.
* Returns null if the request is malformed.
*
* Ported from Next.js:
* test/integration/image-optimizer/test/index.test.ts
* https://github.com/vercel/next.js/blob/canary/test/integration/image-optimizer/test/index.test.ts
*/
function parseImageParams(url, allowedWidths = [...DEFAULT_DEVICE_SIZES, ...DEFAULT_IMAGE_SIZES], allowedQualities, options = {}) {
	const allowedParamNames = /* @__PURE__ */ new Set([
		"url",
		"w",
		"q",
		"dpl"
	]);
	for (const name of url.searchParams.keys()) if (!allowedParamNames.has(name) || url.searchParams.getAll(name).length !== 1) return null;
	const imageUrl = url.searchParams.get("url");
	if (!imageUrl) return null;
	if (imageUrl.length > 3072) return null;
	const widthParam = url.searchParams.get("w");
	const qualityParam = url.searchParams.get("q");
	if (!widthParam || !/^[0-9]+$/.test(widthParam)) return null;
	if (!qualityParam || !/^[0-9]+$/.test(qualityParam)) return null;
	const width = Number.parseInt(widthParam, 10);
	const quality = Number.parseInt(qualityParam, 10);
	if (String(width) !== widthParam || String(quality) !== qualityParam) return null;
	const isDevBlurWidth = options.isDev && width <= DEV_BLUR_MAX_WIDTH;
	const isDevBlurQuality = options.isDev && quality === DEV_BLUR_QUALITY;
	if (width <= 0 || !allowedWidths.includes(width) && !isDevBlurWidth) return null;
	if (quality < 1 || quality > 100) return null;
	if (allowedQualities && !allowedQualities.includes(quality) && !isDevBlurQuality) return null;
	const normalizedUrl = imageUrl.replaceAll("\\", "/");
	if (!normalizedUrl.startsWith("/") || normalizedUrl.startsWith("//")) return null;
	try {
		const base = "https://localhost";
		if (new URL(normalizedUrl, base).origin !== base) return null;
	} catch {
		return null;
	}
	return {
		imageUrl: normalizedUrl,
		width,
		quality
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-response.js
function applyTimingHeader(headers, timing) {
	if (!timing) return;
	const handlerStart = Math.round(timing.handlerStart);
	const compileMs = timing.compileEnd !== void 0 ? Math.round(timing.compileEnd - timing.handlerStart) : -1;
	const renderMs = timing.responseKind === "html" && timing.renderEnd !== void 0 && timing.compileEnd !== void 0 ? Math.round(timing.renderEnd - timing.compileEnd) : -1;
	headers.set(VINEXT_TIMING_HEADER, `${handlerStart},${compileMs},${renderMs}`);
}
function applyDynamicStaleTimeHeader(headers, dynamicStaleTimeSeconds) {
	if (dynamicStaleTimeSeconds !== void 0 && Number.isInteger(dynamicStaleTimeSeconds) && dynamicStaleTimeSeconds >= 0) headers.set(VINEXT_DYNAMIC_STALE_TIME_HEADER, String(dynamicStaleTimeSeconds));
}
/**
* Only ever set from a *completed* render's cacheLife (cache replay or
* prerender seed) — `use cache` scopes keep resolving after headers commit,
* so a streaming response can never carry it.
*/
function applyClientStaleTimeHeader(headers, staleTimeSeconds) {
	if (staleTimeSeconds === void 0) return;
	headers.set(NEXT_ROUTER_STALE_TIME_HEADER, String(Math.floor(staleTimeSeconds)));
}
function applyPrerenderCacheLifeHeader(headers, requestCacheLife) {
	if (!requestCacheLife) return;
	const payload = {};
	if (typeof requestCacheLife.revalidate === "number" && Number.isFinite(requestCacheLife.revalidate)) payload.revalidate = requestCacheLife.revalidate;
	if (typeof requestCacheLife.expire === "number" && Number.isFinite(requestCacheLife.expire)) payload.expire = requestCacheLife.expire;
	const stale = resolveClientStaleTimeSeconds(requestCacheLife);
	if (stale !== void 0) payload.stale = stale;
	if (payload.revalidate === void 0 && payload.expire === void 0 && payload.stale === void 0) return;
	headers.set(VINEXT_PRERENDER_CACHE_LIFE_HEADER, JSON.stringify(payload));
}
function applyPrerenderCacheTagsHeader(headers, cacheTags) {
	if (cacheTags && cacheTags.length > 0) headers.set(NEXT_CACHE_TAGS_HEADER, cacheTags.join(","));
}
function resolveAppPageRscResponsePolicy(options) {
	if (options.isDraftMode) return { cacheControl: NO_STORE_CACHE_CONTROL };
	if (options.isForceDynamic || options.dynamicUsedDuringBuild) return { cacheControl: NO_STORE_CACHE_CONTROL };
	if (options.revalidateSeconds === 0) return { cacheControl: NO_STORE_CACHE_CONTROL };
	if ((options.isForceStatic || options.isDynamicError) && !options.revalidateSeconds || options.revalidateSeconds === Infinity) return {
		cacheControl: STATIC_CACHE_CONTROL,
		cacheState: "STATIC"
	};
	if (options.revalidateSeconds) return {
		cacheControl: buildRevalidateCacheControl(options.revalidateSeconds, options.expireSeconds),
		cacheState: options.isProduction ? "MISS" : void 0
	};
	return {};
}
function resolveAppPageHtmlResponsePolicy(options) {
	if (options.isDraftMode) return {
		cacheControl: NO_STORE_CACHE_CONTROL,
		shouldWriteToCache: false
	};
	if (options.isForceDynamic) return {
		cacheControl: NO_STORE_CACHE_CONTROL,
		shouldWriteToCache: false
	};
	if (options.hasScriptNonce) return {
		cacheControl: NO_STORE_CACHE_CONTROL,
		shouldWriteToCache: false
	};
	if (options.isProgressiveActionRender) return {
		cacheControl: NO_STORE_CACHE_CONTROL,
		shouldWriteToCache: false
	};
	if (options.revalidateSeconds === 0) return {
		cacheControl: NO_STORE_CACHE_CONTROL,
		shouldWriteToCache: false
	};
	if ((options.isForceStatic || options.isDynamicError) && options.revalidateSeconds === null) return {
		cacheControl: STATIC_CACHE_CONTROL,
		cacheState: options.isProduction ? "MISS" : "STATIC",
		shouldWriteToCache: options.isProduction
	};
	if (options.dynamicUsedDuringRender) return {
		cacheControl: NO_STORE_CACHE_CONTROL,
		shouldWriteToCache: false
	};
	if (options.revalidateSeconds !== null && options.revalidateSeconds > 0 && options.revalidateSeconds !== Infinity) return {
		cacheControl: buildRevalidateCacheControl(options.revalidateSeconds, options.expireSeconds),
		cacheState: options.isProduction ? "MISS" : void 0,
		shouldWriteToCache: options.isProduction
	};
	if (options.revalidateSeconds === Infinity) return {
		cacheControl: STATIC_CACHE_CONTROL,
		cacheState: options.isProduction ? "MISS" : "STATIC",
		shouldWriteToCache: options.isProduction
	};
	return { shouldWriteToCache: false };
}
/**
* Mirror Next.js' edge-runtime marker (set in edge-ssr-app.ts). Only routes
* whose resolved segment config is `runtime = "edge"` should advertise it —
* nodejs-runtime routes must not, otherwise downstream consumers can't tell
* the configured runtime from the response. Centralized so every response
* construction site can opt in without re-deriving the header name.
*/
function applyEdgeRuntimeHeader(headers, isEdgeRuntime) {
	if (isEdgeRuntime) headers.set("x-edge-runtime", "1");
}
function buildAppPageRscResponse(body, options) {
	const headers = new Headers({
		"Content-Type": VINEXT_RSC_CONTENT_TYPE,
		Vary: VINEXT_RSC_VARY_HEADER
	});
	applyEdgeRuntimeHeader(headers, options.isEdgeRuntime);
	if (options.params && Object.keys(options.params).length > 0) headers.set(VINEXT_PARAMS_HEADER, encodeURIComponent(JSON.stringify(options.params)));
	if (options.mountedSlotsHeader) headers.set(VINEXT_MOUNTED_SLOTS_HEADER, options.mountedSlotsHeader);
	applyDynamicStaleTimeHeader(headers, options.dynamicStaleTimeSeconds);
	if (options.staleTimePending) headers.set(VINEXT_STALE_TIME_PENDING_HEADER, "1");
	if (options.policy.cacheControl) headers.set("Cache-Control", options.policy.cacheControl);
	if (options.policy.cacheState) setCacheStateHeaders(headers, options.policy.cacheState);
	mergeMiddlewareResponseHeaders(headers, options.middlewareContext.headers);
	if (options.renderedPathAndSearch) headers.set(VINEXT_RENDERED_PATH_AND_SEARCH_HEADER, encodeURIComponent(options.renderedPathAndSearch));
	applyRscCompatibilityIdHeader(headers);
	applyRscDeploymentIdHeader(headers);
	applyPrerenderCacheLifeHeader(headers, options.requestCacheLife);
	applyPrerenderCacheTagsHeader(headers, options.cacheTags);
	applyTimingHeader(headers, options.timing);
	return new Response(body, {
		status: options.middlewareContext.status ?? 200,
		headers
	});
}
function buildAppPageHtmlResponse(body, options) {
	const headers = new Headers({
		"Content-Type": "text/html; charset=utf-8",
		Vary: VINEXT_RSC_VARY_HEADER
	});
	applyEdgeRuntimeHeader(headers, options.isEdgeRuntime);
	if (options.policy.cacheControl) headers.set("Cache-Control", options.policy.cacheControl);
	if (options.policy.cacheState) setCacheStateHeaders(headers, options.policy.cacheState);
	if (options.draftCookie) headers.append("Set-Cookie", options.draftCookie);
	if (options.linkHeader) headers.set("Link", options.linkHeader);
	mergeMiddlewareResponseHeaders(headers, options.middlewareContext.headers);
	applyPrerenderCacheLifeHeader(headers, options.requestCacheLife);
	applyPrerenderCacheTagsHeader(headers, options.cacheTags);
	applyTimingHeader(headers, options.timing);
	return new Response(body, {
		status: options.middlewareContext.status ?? 200,
		headers
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/next-error-digest.js
/**
* Helpers for parsing Next.js error `digest` strings shared across the App
* Router execution paths (server actions, page renders, route handlers).
*
* Special control flow is encoded as thrown errors carrying a `digest` field.
* Redirect digests may appear as vinext's encoded three-part form or Next.js's
* raw, semicolon-terminated form:
*  - `NEXT_REDIRECT;<type>;<url>[;<status>[;]]` — `redirect()` / `permanentRedirect()`
*  - `NEXT_NOT_FOUND` — `notFound()`
*  - `NEXT_HTTP_ERROR_FALLBACK;<status>` — `forbidden()` / `unauthorized()` / etc.
*
* Each call site needs slightly different post-processing (URL resolution
* against the request, 303-vs-307 status overrides for actions, etc.), so
* these helpers only handle the parsing — callers shape the result.
*/
/**
* Pulls a stringified `digest` off an unknown thrown value, or returns null
* when the value is not a digest-bearing error.
*/
function getNextErrorDigest(error) {
	if (!error || typeof error !== "object" || !("digest" in error)) return null;
	return String(error.digest);
}
/**
* Parses redirect digests from vinext's encoded three-part form and Next.js's
* raw, semicolon-terminated form. Returns null when the digest is not a
* redirect digest. Vinext's encoded URL is decoded with `decodeURIComponent`;
* Next.js's canonical raw URL is preserved verbatim. The `status` defaults to
* 307 when omitted; an omitted `type` is left as null so the caller can apply
* the correct context-sensitive default.
*/
function parseNextRedirectDigest(digest) {
	return parseRedirectDigest(digest);
}
/**
* Parses a `NEXT_NOT_FOUND` or `NEXT_HTTP_ERROR_FALLBACK;<status>` digest.
* Returns `{ status: 404 }` for `NEXT_NOT_FOUND` and the parsed status code
* for the fallback form. Returns null otherwise.
*/
function parseNextHttpErrorDigest(digest) {
	if (digest === "NEXT_NOT_FOUND") return { status: 404 };
	if (digest.startsWith("NEXT_HTTP_ERROR_FALLBACK;")) return { status: parseInt(digest.split(";")[1], 10) };
	return null;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/prerender-route-params.js
function isPrerenderRouteParams(value) {
	if (!isUnknownRecord(value)) return false;
	for (const [, param] of Object.entries(value)) {
		if (typeof param === "string") continue;
		if (Array.isArray(param) && param.every((item) => typeof item === "string")) continue;
		return false;
	}
	return true;
}
function isPrerenderRouteParamsPayload(value) {
	if (!isUnknownRecord(value)) return false;
	const keys = Object.keys(value);
	if (keys.length !== 2 && keys.length !== 3) return false;
	if (keys.some((key) => key !== "fallbackParamNames" && key !== "params" && key !== "routePattern")) return false;
	if ("fallbackParamNames" in value && (!Array.isArray(value.fallbackParamNames) || !value.fallbackParamNames.every((name) => typeof name === "string"))) return false;
	return typeof value.routePattern === "string" && value.routePattern.startsWith("/") && isPrerenderRouteParams(value.params);
}
function serializePrerenderRouteParamsHeader(payload) {
	if (payload === null || Object.keys(payload.params).length === 0) return null;
	return encodeURIComponent(JSON.stringify(payload));
}
function parsePrerenderRouteParamsHeader(value) {
	if (value === null || value === "") return null;
	try {
		const parsed = JSON.parse(decodeURIComponent(value));
		return isPrerenderRouteParamsPayload(parsed) ? parsed : null;
	} catch {
		return null;
	}
}
function readTrustedPrerenderRouteParamsFromHeaders(headers, expectedSecret) {
	if (process.env.VINEXT_PRERENDER !== "1") return null;
	const secret = headers.get(VINEXT_PRERENDER_SECRET_HEADER);
	if (secret === null) return null;
	if (expectedSecret !== void 0 && secret !== expectedSecret) return null;
	const header = headers.get(VINEXT_PRERENDER_ROUTE_PARAMS_HEADER);
	if (header === null) return null;
	const params = parsePrerenderRouteParamsHeader(header);
	if (params === null) throw new Error("[vinext] Invalid internal prerender route params header.");
	return params;
}
function readTrustedPrerenderRouteParams(request) {
	return readTrustedPrerenderRouteParamsFromHeaders(request.headers);
}
function decodePrerenderRouteParam(value) {
	try {
		return decodeURIComponent(value);
	} catch {
		return null;
	}
}
function decodedPrerenderRouteParamEquals(prerenderValue, matchedValue) {
	if (Array.isArray(prerenderValue) || Array.isArray(matchedValue)) {
		if (!Array.isArray(prerenderValue) || !Array.isArray(matchedValue)) return false;
		if (prerenderValue.length !== matchedValue.length) return false;
		return prerenderValue.every((item, index) => {
			const decoded = decodePrerenderRouteParam(item);
			return item === matchedValue[index] || decoded !== null && decoded === matchedValue[index];
		});
	}
	const decoded = decodePrerenderRouteParam(prerenderValue);
	return prerenderValue === matchedValue || decoded !== null && decoded === matchedValue;
}
function matchPrerenderRouteParamsPayload(payload, routePattern, params) {
	if (payload === null) return null;
	if (payload.routePattern !== routePattern) return null;
	if (Object.keys(payload.params).length !== Object.keys(params).length) return null;
	for (const [key, prerenderValue] of Object.entries(payload.params)) {
		const matchedValue = params[key];
		if (matchedValue === void 0) return null;
		if (!decodedPrerenderRouteParamEquals(prerenderValue, matchedValue)) return null;
	}
	if (payload.fallbackParamNames) {
		const routeParamNames = new Set(routePattern.split("/").filter((part) => part.startsWith(":")).map((part) => part.endsWith("+") || part.endsWith("*") ? part.slice(1, -1) : part.slice(1)));
		const fallbackParamNames = payload.fallbackParamNames.filter((name, index, names) => routeParamNames.has(name) && names.indexOf(name) === index);
		if (fallbackParamNames.length !== payload.fallbackParamNames.length) return null;
		if (fallbackParamNames.length === 0) return null;
		return {
			fallbackParamNames,
			kind: "fallback-shell",
			params: payload.params
		};
	}
	return {
		kind: "exact",
		params: payload.params
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/pregenerated-concrete-paths.js
function normalizePregeneratedPathname(pathname) {
	return normalizePath(normalizePathnameForRouteMatch(pathname));
}
/**
* Stores concrete URL paths pre-rendered at build time per route pattern.
* Used by the PPR fallback-shell guard to avoid serving fallback shells for
* known routes whose exact cache entry is temporarily absent.
*
* Populated by `seed-cache.ts` (Node) or from `globalThis.__VINEXT_PREGENERATED_CONCRETE_PATHS`
* injected by `deploy.ts` after prerender (Workers).
*/
var concreteUrlPathsByRoute = /* @__PURE__ */ new Map();
function clearPregeneratedConcretePaths() {
	concreteUrlPathsByRoute.clear();
}
function addPregeneratedConcretePath(routePattern, pathname) {
	let paths = concreteUrlPathsByRoute.get(routePattern);
	if (!paths) {
		paths = /* @__PURE__ */ new Set();
		concreteUrlPathsByRoute.set(routePattern, paths);
	}
	paths.add(normalizePregeneratedPathname(pathname));
}
function getRenderedConcreteUrlPathsForRoute$1(routePattern) {
	return concreteUrlPathsByRoute.get(routePattern);
}
/**
* Populate the registry from `globalThis.__VINEXT_PREGENERATED_CONCRETE_PATHS`.
* No-op when the global is not set (Node path — seed-cache handles it later).
* Pathnames are normalised so they match the runtime `cleanPathname`.
*/
function initPregeneratedPathsFromGlobals() {
	const raw = globalThis.__VINEXT_PREGENERATED_CONCRETE_PATHS;
	const data = parsePregeneratedConcretePaths(raw);
	if (!data) return;
	clearPregeneratedConcretePaths();
	for (const [routePattern, pathnames] of data) for (const pathname of pathnames) addPregeneratedConcretePath(routePattern, pathname);
}
function parsePregeneratedConcretePaths(value) {
	if (!Array.isArray(value)) return void 0;
	const result = [];
	for (const entry of value) {
		if (!Array.isArray(entry)) return void 0;
		if (entry.length !== 2) return void 0;
		const [pattern, paths] = entry;
		if (typeof pattern !== "string") return void 0;
		if (!Array.isArray(paths)) return void 0;
		const strings = [];
		for (const p of paths) {
			if (typeof p !== "string") return void 0;
			strings.push(p);
		}
		result.push([pattern, strings]);
	}
	return result;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/server-action-not-found.js
var SERVER_ACTION_NOT_FOUND_DOCS = "https://nextjs.org/docs/messages/failed-to-find-server-action";
var SERVER_ACTION_NOT_FOUND_BODY = "Server action not found.";
function getServerActionNotFoundPrefix(actionId) {
	return `Failed to find Server Action${actionId ? ` "${actionId}"` : ""}.`;
}
function getServerActionNotFoundMessage(actionId) {
	return `${getServerActionNotFoundPrefix(actionId)} This request might be from an older or newer deployment.\nRead more: ${SERVER_ACTION_NOT_FOUND_DOCS}`;
}
function createServerActionNotFoundResponse() {
	return new Response(SERVER_ACTION_NOT_FOUND_BODY, {
		status: 404,
		headers: {
			[NEXTJS_ACTION_NOT_FOUND_HEADER]: "1",
			"content-type": "text/plain"
		}
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/implicit-tags.js
var NEXT_CACHE_IMPLICIT_TAG_ID = "_N_T_";
function appendUnique(tags, tag) {
	if (!tags.includes(tag)) tags.push(tag);
}
function normalizeRouteSegment(segment) {
	if (!segment || segment === "." || segment.startsWith("@")) return null;
	return segment;
}
function buildRouteCachePath(routeSegments, leafKind) {
	const parts = [];
	for (const segment of routeSegments) {
		const normalized = normalizeRouteSegment(segment);
		if (normalized) parts.push(normalized);
	}
	parts.push(leafKind);
	return `/${parts.join("/")}`;
}
function appendDerivedTags(tags, routePath) {
	appendUnique(tags, `${NEXT_CACHE_IMPLICIT_TAG_ID}/layout`);
	if (!routePath.startsWith("/")) return;
	const routeParts = routePath.split("/");
	const leafIndex = routeParts.length - 1;
	for (let i = 1; i <= routeParts.length; i++) {
		let currentPathname = routeParts.slice(0, i).join("/");
		if (!currentPathname) continue;
		if (!(i - 1 === leafIndex)) currentPathname = `${currentPathname}/layout`;
		appendUnique(tags, `${NEXT_CACHE_IMPLICIT_TAG_ID}${currentPathname}`);
	}
}
function buildAppPageTags(cleanPathname, extraTags, routeSegments) {
	return buildPageCacheTags(cleanPathname, extraTags, [...routeSegments], "page");
}
function buildPageCacheTags(pathname, extraTags, routeSegments, leafKind) {
	const tags = [pathname, `${NEXT_CACHE_IMPLICIT_TAG_ID}${pathname.length > 1 && pathname.endsWith("/") ? pathname.slice(0, -1) : pathname}`];
	if (pathname === "/") appendUnique(tags, `${NEXT_CACHE_IMPLICIT_TAG_ID}/index`);
	if (pathname === "/index") appendUnique(tags, `${NEXT_CACHE_IMPLICIT_TAG_ID}/`);
	appendDerivedTags(tags, buildRouteCachePath(routeSegments, leafKind));
	for (const tag of extraTags) appendUnique(tags, tag);
	return tags.map(encodeCacheTag);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-post-middleware-context.js
/**
* Build a request context from the live ALS HeadersContext, which reflects
* any x-middleware-request-* header mutations applied by middleware.
* Used for afterFiles and fallback rewrite has/missing evaluation — these
* run after middleware in the App Router execution order.
*
* Falls back to `requestContextFromRequest(request)` when no HeadersContext
* is set (no middleware ran, or middleware didn't set request headers).
*/
function buildPostMwRequestContext(request) {
	const url = new URL(request.url);
	const ctx = getHeadersContext();
	if (!ctx) return requestContextFromRequest(request);
	const cookiesRecord = Object.fromEntries(ctx.cookies);
	return {
		headers: ctx.headers,
		cookies: cookiesRecord,
		query: url.searchParams,
		host: normalizeHost(ctx.headers.get("host"), url.hostname)
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/root-params.js
var _FALLBACK_KEY$1 = Symbol.for("vinext.rootParams.fallback");
var _g$3 = globalThis;
var _als$1 = getOrCreateAls("vinext.rootParams.als");
var _usageAls = getOrCreateAls("vinext.rootParams.usage.als");
var _fallbackState$1 = _g$3[_FALLBACK_KEY$1] ??= { rootParams: null };
function getState() {
	if (isInsideUnifiedScope()) return getRequestContext();
	return _als$1.getStore() ?? _fallbackState$1;
}
function pickRootParams(params, rootParamNames) {
	const picked = {};
	for (const name of rootParamNames ?? []) picked[name] = params[name];
	return picked;
}
function setRootParams(params) {
	getState().rootParams = params;
}
function runWithRootParamsUsage(usage, fn, controller) {
	const state = {
		...usage,
		phase: "active"
	};
	if (controller) controller.transitionToRender = () => {
		if (usage.kind === "server-action") state.phase = "render";
	};
	return _usageAls.run(state, fn);
}
function runWithRootParamsScope(params, fn) {
	if (isInsideUnifiedScope()) return runWithUnifiedStateMutation((ctx) => {
		ctx.rootParams = params;
	}, fn);
	else return _als$1.run({ rootParams: params }, fn);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-route-tree-prefetch.js
var PARENT_INLINED_INTO_SELF = 32;
var INLINED_INTO_CHILD = 64;
var HEAD_INLINED_INTO_SELF = 128;
var PAGE_SEGMENT = "__PAGE__";
var SLOT_SEGMENT = "(__SLOT__)";
var SEGMENT_INLINE_SIZE = 1;
var SEGMENT_OUTLINE_SIZE = 4096;
var DEFAULT_SEGMENT_INLINE_THRESHOLD = 2048;
var HEAD_INLINE_SIZE = 1;
var DEFAULT_MAX_INLINE_BUNDLE_SIZE = 10240;
var NEXT_DID_POSTPONE_HEADER = "x-nextjs-postponed";
function isRouteTreePrefetchRequest(request) {
	return request.headers.get("RSC") === "1" && request.headers.get("Next-Router-Prefetch") === "1" && request.headers.get("Next-Router-Segment-Prefetch") === "/_tree";
}
function createNode$1(segment, module) {
	const { name, param } = routeTreeSegment(segment);
	return {
		name,
		param,
		prefetchSize: estimatePrefetchSize(module) ?? ((module === null || module === void 0) && segment !== PAGE_SEGMENT ? SEGMENT_INLINE_SIZE : null),
		prefetchHints: 0,
		slots: null
	};
}
function ensureSlots(node) {
	if (node.slots === null) node.slots = {};
	return node.slots;
}
function addChild(node, key, child) {
	ensureSlots(node)[key] = child;
}
function routeTreeSegment(segment) {
	if (segment.startsWith(":")) {
		const rest = segment.slice(1);
		if (rest.endsWith("+")) return dynamicRouteTreeSegment(rest.slice(0, -1), "c");
		if (rest.endsWith("*")) return dynamicRouteTreeSegment(rest.slice(0, -1), "oc");
		return dynamicRouteTreeSegment(rest, "d");
	}
	if (segment.startsWith("[[...") && segment.endsWith("]]")) return dynamicRouteTreeSegment(segment.slice(5, -2), "oc");
	if (segment.startsWith("[...") && segment.endsWith("]")) return dynamicRouteTreeSegment(segment.slice(4, -1), "c");
	if (segment.startsWith("[") && segment.endsWith("]")) return dynamicRouteTreeSegment(segment.slice(1, -1), "d");
	return {
		name: segment,
		param: null
	};
}
function dynamicRouteTreeSegment(name, type) {
	return {
		name,
		param: {
			key: null,
			siblings: null,
			type
		}
	};
}
function explicitPrefetchSize(module) {
	if (typeof module !== "object" || module === null) return null;
	const value = module.prefetchSize;
	if (value === "large") return SEGMENT_OUTLINE_SIZE;
	if (value === "small") return SEGMENT_INLINE_SIZE;
	return typeof value === "number" && Number.isFinite(value) && value >= 0 ? value : null;
}
function estimatePrefetchSize(module) {
	const explicitSize = explicitPrefetchSize(module);
	if (explicitSize !== null) return explicitSize;
	if (typeof module !== "object" || module === null) return null;
	return typeof module.default === "function" ? SEGMENT_INLINE_SIZE : null;
}
function layoutModuleByTreePosition(route) {
	const layouts = route.layouts ?? [];
	const positions = route.layoutTreePositions ?? [];
	const byPosition = /* @__PURE__ */ new Map();
	for (const [index, position] of positions.entries()) byPosition.set(position, layouts[index]);
	return byPosition;
}
function modulesByTreePosition(modules, positions) {
	const byPosition = /* @__PURE__ */ new Map();
	for (const [index, position] of (positions ?? []).entries()) byPosition.set(position, modules?.[index]);
	return byPosition;
}
async function buildTree(route) {
	const layoutsByPosition = layoutModuleByTreePosition(route);
	const root = createNode$1("", layoutsByPosition.get(0));
	const nodesByPosition = /* @__PURE__ */ new Map([[0, root]]);
	let current = root;
	for (const [index, segment] of route.routeSegments.entries()) {
		const position = index + 1;
		const child = createNode$1(segment, layoutsByPosition.get(position));
		addChild(current, "children", child);
		nodesByPosition.set(position, child);
		current = child;
	}
	addChild(current, "children", createNode$1(PAGE_SEGMENT, route.page));
	for (const slot of Object.values(route.slots ?? {})) {
		const ownerPosition = slot.layoutIndex === void 0 || slot.layoutIndex < 0 ? route.routeSegments.length : route.layoutTreePositions?.[slot.layoutIndex] ?? route.routeSegments.length;
		const owner = nodesByPosition.get(ownerPosition) ?? current;
		const slotRoot = createNode$1(SLOT_SEGMENT, slot.layout);
		let slotCurrent = slotRoot;
		const slotConfigLayoutsByPosition = modulesByTreePosition(slot.configLayouts, slot.configLayoutTreePositions);
		const slotRouteSegments = slot.routeSegments ?? [];
		for (const [index, segment] of slotRouteSegments.entries()) {
			const position = index + 1;
			const child = createNode$1(segment, slotConfigLayoutsByPosition.get(position));
			addChild(slotCurrent, "children", child);
			slotCurrent = child;
		}
		addChild(slotCurrent, "children", createNode$1(PAGE_SEGMENT, slot.page ?? slot.default));
		addChild(owner, slot.name, slotRoot);
	}
	return root;
}
function computePrefetchHints(node, parentGzipSize, headInlineState, config) {
	const currentGzipSize = node.prefetchSize;
	const sizeToInline = currentGzipSize !== null && currentGzipSize < config.maxSize ? currentGzipSize : null;
	let didInlineIntoChild = false;
	let acceptingChildInlinedBytes = 0;
	let smallestChildInlinedBytes = Number.POSITIVE_INFINITY;
	let hasChildren = false;
	for (const child of Object.values(node.slots ?? {})) {
		hasChildren = true;
		const childInlinedBytes = computePrefetchHints(child, didInlineIntoChild ? null : sizeToInline, headInlineState, config);
		if ((child.prefetchHints & PARENT_INLINED_INTO_SELF) !== 0) {
			didInlineIntoChild = true;
			acceptingChildInlinedBytes = childInlinedBytes;
		} else if (!didInlineIntoChild && childInlinedBytes < smallestChildInlinedBytes) smallestChildInlinedBytes = childInlinedBytes;
	}
	if (!hasChildren) smallestChildInlinedBytes = 0;
	let hints = node.prefetchHints;
	if (didInlineIntoChild) hints |= INLINED_INTO_CHILD;
	let inlinedBytes = didInlineIntoChild ? acceptingChildInlinedBytes : smallestChildInlinedBytes;
	const isBundleTerminal = !didInlineIntoChild;
	if (!headInlineState.inlined && isBundleTerminal && node.name === PAGE_SEGMENT && inlinedBytes + HEAD_INLINE_SIZE < config.maxBundleSize) {
		hints |= HEAD_INLINED_INTO_SELF;
		inlinedBytes += HEAD_INLINE_SIZE;
		headInlineState.inlined = true;
	}
	if (parentGzipSize !== null) {
		if (inlinedBytes + parentGzipSize < config.maxBundleSize) {
			hints |= PARENT_INLINED_INTO_SELF;
			inlinedBytes += parentGzipSize;
		}
	}
	node.prefetchHints = hints;
	return inlinedBytes;
}
function stripMutableFields(node) {
	const slots = node.slots === null ? null : Object.fromEntries(Object.entries(node.slots).map(([key, child]) => [key, stripMutableFields(child)]));
	return {
		name: node.name,
		param: node.param,
		prefetchHints: node.prefetchHints,
		slots
	};
}
function resolvePrefetchInliningConfig(config) {
	if (config) return config;
	return {
		maxBundleSize: DEFAULT_MAX_INLINE_BUNDLE_SIZE,
		maxSize: DEFAULT_SEGMENT_INLINE_THRESHOLD
	};
}
async function createRouteTreePrefetchResponse(route, options = {}) {
	const tree = await buildTree(route);
	computePrefetchHints(tree, null, { inlined: false }, resolvePrefetchInliningConfig(options.prefetchInlining));
	const headers = new Headers({
		"Cache-Control": "no-store",
		"Content-Type": VINEXT_RSC_CONTENT_TYPE,
		[NEXT_DID_POSTPONE_HEADER]: "2",
		Vary: VINEXT_RSC_VARY_HEADER
	});
	applyRscCompatibilityIdHeader(headers);
	const deploymentId = options.deploymentId ?? getDeploymentId();
	if (deploymentId) headers.set(NEXTJS_DEPLOYMENT_ID_HEADER, deploymentId);
	const payload = {
		tree: stripMutableFields(tree),
		staleTime: -1
	};
	if (options.buildId) payload.buildId = options.buildId;
	return new Response(`0:${JSON.stringify(payload)}\n`, { headers });
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-rsc-response-finalizer.js
var configHeadersAlreadyApplied = /* @__PURE__ */ new WeakSet();
/** Apply only the matching next.config headers for an App Router request. */
async function applyAppRscConfigHeaders(headers, request, options) {}
/**
* Apply App Router response finalization that must happen outside individual
* route dispatchers.
*
* Called once per request in the outer handler() wrapper, after all route
* handling, so that every response path (page, route handler, server action,
* metadata, not-found) gets headers applied consistently.
*
* Skips 3xx redirect responses. Response.redirect() creates immutable
* headers that throw on mutation, and Next.js does not apply config headers
* to redirects regardless.
*/
async function finalizeAppRscResponse(response, request, options) {
	if (response.status >= 300 && response.status < 400) return response;
	if (!response.headers.has("x-vinext-static-file")) {
		const varyHeader = response.headers.get("Vary");
		if (varyHeader === null) response.headers.set("Vary", VINEXT_RSC_VARY_HEADER);
		else if (varyHeader !== VINEXT_RSC_VARY_HEADER) mergeVaryHeader(response.headers, VINEXT_RSC_VARY_HEADER);
	}
	if (!response.headers.has("Cache-Control")) applyCdnResponseHeaders(response.headers, { cacheControl: "" });
	if (configHeadersAlreadyApplied.has(response)) return response;
	await applyAppRscConfigHeaders(response.headers, request, options);
	if (response.status === 405 && response.headers.get("Allow") === "GET, HEAD") sanitizeMethodNotAllowedHeaders(response.headers, "GET, HEAD");
	return response;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/number.js
function isNonNegativeSafeInteger(value) {
	return typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/client-reuse-manifest.js
var CLIENT_REUSE_MANIFEST_HASH_ALGORITHM = "fnv1a64";
var DEFAULT_CLIENT_REUSE_MANIFEST_LIMITS = {
	maxEntryCount: 64,
	maxEntryIdLength: 512,
	maxManifestBytes: 4096,
	maxPayloadHashLength: 16,
	maxVariantCacheKeyLength: 256
};
var HASH_DIGEST_PATTERN = /^[0-9a-z]+$/;
var textEncoder = new TextEncoder();
function createRejection(code, fields = {}) {
	return {
		code,
		fields
	};
}
function rejectManifest(code, fields = {}) {
	return {
		kind: "rejected",
		rejection: createRejection(code, fields)
	};
}
function rejectEntry(code, entryId, fields = {}) {
	return {
		code,
		entryId,
		fields
	};
}
function countUtf8Bytes(input) {
	return textEncoder.encode(input).length;
}
function parseReplayWindow(value, visibleCommitVersion) {
	if (!isUnknownRecord(value)) return {
		kind: "rejected",
		rejection: createRejection("SKIP_REPLAY_WINDOW_INVALID", { field: "replayWindow" })
	};
	const validFromVisibleCommitVersion = value.validFromVisibleCommitVersion;
	const validUntilVisibleCommitVersion = value.validUntilVisibleCommitVersion;
	if (!isNonNegativeSafeInteger(validFromVisibleCommitVersion) || !isNonNegativeSafeInteger(validUntilVisibleCommitVersion) || validFromVisibleCommitVersion > validUntilVisibleCommitVersion || visibleCommitVersion < validFromVisibleCommitVersion || visibleCommitVersion > validUntilVisibleCommitVersion) return {
		kind: "rejected",
		rejection: createRejection("SKIP_REPLAY_WINDOW_INVALID", {
			validFromVisibleCommitVersion: isNonNegativeSafeInteger(validFromVisibleCommitVersion) ? validFromVisibleCommitVersion : null,
			validUntilVisibleCommitVersion: isNonNegativeSafeInteger(validUntilVisibleCommitVersion) ? validUntilVisibleCommitVersion : null,
			visibleCommitVersion
		})
	};
	return {
		kind: "parsed",
		replayWindow: {
			validFromVisibleCommitVersion,
			validUntilVisibleCommitVersion
		}
	};
}
function currentCommitVersionMatchesReplayWindow(currentVisibleCommitVersion, replayWindow) {
	if (currentVisibleCommitVersion === void 0) return true;
	return currentVisibleCommitVersion >= replayWindow.validFromVisibleCommitVersion && currentVisibleCommitVersion <= replayWindow.validUntilVisibleCommitVersion;
}
function parseEntryKind(id) {
	const parsed = AppElementsWire.parseElementKey(id);
	if (parsed === null) return null;
	return parsed.kind;
}
function isValidPayloadHash(value, limits) {
	return typeof value === "string" && value.length > 0 && value.length <= limits.maxPayloadHashLength && HASH_DIGEST_PATTERN.test(value);
}
function parseManifestEntry(value, limits, index) {
	if (!isUnknownRecord(value)) return rejectEntry("SKIP_ENTRY_MALFORMED", null, { index });
	const id = value.id;
	if (typeof id !== "string" || id.length === 0) return rejectEntry("SKIP_ENTRY_ID_INVALID", null, { index });
	if (id.length > limits.maxEntryIdLength) return rejectEntry("SKIP_ENTRY_ID_TOO_LONG", id, {
		idHash: createClientReusePayloadHash(id),
		maxEntryIdLength: limits.maxEntryIdLength
	});
	const kind = parseEntryKind(id);
	if (kind === null) return rejectEntry("SKIP_UNKNOWN_ENTRY", id, { idHash: createClientReusePayloadHash(id) });
	const privacy = value.privacy;
	if (privacy === "private") return rejectEntry("SKIP_PRIVATE_ENTRY", id, { privacy });
	if (privacy !== "public") return rejectEntry("SKIP_ENTRY_MALFORMED", id, { field: "privacy" });
	const payloadHash = value.payloadHash;
	if (!isValidPayloadHash(payloadHash, limits)) return rejectEntry("SKIP_ENTRY_HASH_INVALID", id, { maxPayloadHashLength: limits.maxPayloadHashLength });
	const variantCacheKey = value.variantCacheKey;
	if (typeof variantCacheKey !== "string" || variantCacheKey.length === 0) return rejectEntry("SKIP_VARIANT_CACHE_KEY_INVALID", id, { field: "variantCacheKey" });
	if (variantCacheKey.length > limits.maxVariantCacheKeyLength) return rejectEntry("SKIP_VARIANT_CACHE_KEY_TOO_LONG", id, {
		maxVariantCacheKeyLength: limits.maxVariantCacheKeyLength,
		variantCacheKeyHash: createClientReusePayloadHash(variantCacheKey)
	});
	const artifactCompatibility = parseArtifactCompatibilityEnvelope(value.artifactCompatibility);
	if (artifactCompatibility === null) return rejectEntry("SKIP_ARTIFACT_COMPATIBILITY_INVALID", id, { field: "artifactCompatibility" });
	return {
		artifactCompatibility,
		id,
		kind,
		payloadHash,
		privacy,
		variantCacheKey
	};
}
function createClientReusePayloadHash(input) {
	return fnv1a64(input);
}
function parseClientReuseManifestHeader(rawHeader, options = {}) {
	const header = rawHeader?.trim();
	if (!header) return { kind: "absent" };
	const limits = options.limits ?? DEFAULT_CLIENT_REUSE_MANIFEST_LIMITS;
	const manifestBytes = countUtf8Bytes(header);
	if (manifestBytes > limits.maxManifestBytes) return rejectManifest("SKIP_MANIFEST_TOO_LARGE", {
		manifestBytes,
		maxManifestBytes: limits.maxManifestBytes
	});
	let decoded;
	try {
		decoded = JSON.parse(header);
	} catch {
		return rejectManifest("SKIP_MANIFEST_MALFORMED");
	}
	if (!isUnknownRecord(decoded)) return rejectManifest("SKIP_MANIFEST_MALFORMED", { field: "manifest" });
	if (decoded.schemaVersion !== 1) return rejectManifest("SKIP_MANIFEST_SCHEMA_UNSUPPORTED", { schemaVersion: typeof decoded.schemaVersion === "number" || typeof decoded.schemaVersion === "string" ? decoded.schemaVersion : null });
	if (decoded.hashAlgorithm !== "fnv1a64") return rejectManifest("SKIP_HASH_ALGORITHM_UNSUPPORTED", { hashAlgorithm: typeof decoded.hashAlgorithm === "string" ? decoded.hashAlgorithm : null });
	const visibleCommitVersion = decoded.visibleCommitVersion;
	if (!isNonNegativeSafeInteger(visibleCommitVersion)) return rejectManifest("SKIP_VISIBLE_COMMIT_VERSION_INVALID", { visibleCommitVersion: null });
	const replayWindowResult = parseReplayWindow(decoded.replayWindow, visibleCommitVersion);
	if (replayWindowResult.kind === "rejected") return {
		kind: "rejected",
		rejection: replayWindowResult.rejection
	};
	const { replayWindow } = replayWindowResult;
	if (!currentCommitVersionMatchesReplayWindow(options.currentVisibleCommitVersion, replayWindow)) return rejectManifest("SKIP_VISIBLE_COMMIT_VERSION_MISMATCH", {
		currentVisibleCommitVersion: options.currentVisibleCommitVersion ?? null,
		validFromVisibleCommitVersion: replayWindow.validFromVisibleCommitVersion,
		validUntilVisibleCommitVersion: replayWindow.validUntilVisibleCommitVersion,
		visibleCommitVersion
	});
	const entriesValue = decoded.entries;
	if (!Array.isArray(entriesValue)) return rejectManifest("SKIP_MANIFEST_MALFORMED", { field: "entries" });
	if (entriesValue.length > limits.maxEntryCount) return rejectManifest("SKIP_ENTRY_COUNT_EXCEEDED", {
		entryCount: entriesValue.length,
		maxEntryCount: limits.maxEntryCount
	});
	const entries = [];
	const entryRejections = [];
	let previousEntryId = null;
	for (let index = 0; index < entriesValue.length; index++) {
		const value = entriesValue[index];
		if (isUnknownRecord(value) && typeof value.id === "string") {
			if (previousEntryId !== null && value.id <= previousEntryId) return rejectManifest("SKIP_ENTRY_ORDER_NON_CANONICAL", {
				entryIdHash: createClientReusePayloadHash(value.id),
				previousEntryIdHash: createClientReusePayloadHash(previousEntryId)
			});
			previousEntryId = value.id;
		}
		const parsedEntry = parseManifestEntry(value, limits, index);
		if ("code" in parsedEntry) entryRejections.push(parsedEntry);
		else entries.push(parsedEntry);
	}
	return {
		entryRejections,
		kind: "parsed",
		manifest: {
			entries,
			hashAlgorithm: CLIENT_REUSE_MANIFEST_HASH_ALGORITHM,
			replayWindow,
			schemaVersion: 1,
			visibleCommitVersion
		},
		skipDisposition: {
			code: "SKIP_MODEL_DISABLED",
			enabled: false,
			mode: "renderAndSend"
		}
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-interception-context-header.js
/**
* Normalize the `x-vinext-interception-context` header from inbound requests.
*
* The browser sends the current pathname (e.g. `/feed`) as interception context
* so the server can decide whether to render an intercepted parallel route.
* The legitimate value is always a same-origin URL pathname produced by the
* vinext browser entry — never an arbitrary string.
*
* Security: this value flows into cache-key construction (via
* `getOptimisticRouteTemplateKey`, `getOptimisticPrefetchSourceKey`, and
* outbound RSC payload cache keys). Without bounds, an attacker who controls
* this header can fabricate unbounded distinct values to fragment the cache
* or drive per-write KV billing. See `SECURITY-AUDIT-2026-05.md` finding
* F-PROD-1.
*
* Bounds applied:
*   - Null bytes are stripped (header-injection defense).
*   - The value must start with `/` (a pathname).
*   - Whitespace is rejected (real pathnames do not contain raw whitespace;
*     legitimate spaces would be percent-encoded).
*   - Length capped at MAX_INTERCEPTION_CONTEXT_LENGTH bytes. Values that
*     exceed the cap are treated as absent so the request is still served,
*     just without interception.
*
* Anything that fails validation returns null, matching the prior behavior of
* an absent header. This is intentionally more permissive than rejecting the
* whole request — interception is a progressive enhancement.
*/
/** Hard cap on the byte length of the interception-context header value. */
var MAX_INTERCEPTION_CONTEXT_LENGTH = 1024;
function normalizeInterceptionContextHeader(raw) {
	if (!raw) return null;
	const stripped = raw.replaceAll("\0", "");
	if (stripped.length === 0) return null;
	if (stripped.length > MAX_INTERCEPTION_CONTEXT_LENGTH) return null;
	if (!stripped.startsWith("/")) return null;
	if (/\s/.test(stripped)) return null;
	return stripped;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-rsc-request-normalization.js
function extractFlightRouterStatePath(value, depth = 0) {
	if (!Array.isArray(value) || value.length < 2 || depth > 64) return null;
	const rawSegment = value[0];
	const segment = Array.isArray(rawSegment) ? rawSegment[1] : rawSegment;
	if (typeof segment !== "string") return null;
	if (segment === "__DEFAULT__" || /^(?:\(\.\)|\(\.\.\)|\(\.\.\.\))/.test(segment)) return null;
	const parallelRoutes = value[1];
	if (!parallelRoutes || typeof parallelRoutes !== "object" || Array.isArray(parallelRoutes)) return null;
	let childPath = null;
	const children = Reflect.get(parallelRoutes, "children");
	if (children !== void 0) childPath = extractFlightRouterStatePath(children, depth + 1);
	if (childPath === null) for (const [key, child] of Object.entries(parallelRoutes)) {
		if (key === "children") continue;
		childPath = extractFlightRouterStatePath(child, depth + 1);
		if (childPath !== null) break;
	}
	return `/${[segment === "" || segment === "children" || segment.startsWith("__PAGE__") || segment.startsWith("(") && segment.endsWith(")") ? "" : segment.replace(/^\/+/, ""), ...childPath === null ? [] : childPath.split("/")].filter(Boolean).join("/")}`;
}
function parsePrefetchRouterState(value) {
	if (!value) return null;
	try {
		const parsed = JSON.parse(decodeURIComponent(value));
		if (Array.isArray(parsed)) {
			const pathAndSearch = extractFlightRouterStatePath(parsed);
			return pathAndSearch === null ? null : { pathAndSearch };
		}
		if (!parsed || typeof parsed !== "object") return null;
		const pathAndSearch = Reflect.get(parsed, "pathAndSearch");
		const routeId = Reflect.get(parsed, "routeId");
		if (typeof pathAndSearch !== "string" || !pathAndSearch.startsWith("/") || typeof routeId !== "string" || routeId.length === 0) return null;
		return { pathAndSearch };
	} catch {
		return null;
	}
}
function normalizeComparablePathAndSearch(value, basePath, baseUrl) {
	const parsed = new URL(value, baseUrl);
	const pathname = basePath && hasBasePath(parsed.pathname, basePath) ? stripBasePath(parsed.pathname, basePath) : parsed.pathname;
	const search = parsed.searchParams.toString();
	return `${pathname}${search ? `?${search}` : ""}`;
}
function tryNormalizeComparablePathAndSearch(value, basePath, baseUrl) {
	try {
		return normalizeComparablePathAndSearch(value, basePath, baseUrl);
	} catch {
		return null;
	}
}
/**
* Normalize an App Router RSC request.
*
* Performs all security-sensitive and compatibility-sensitive preprocessing before
* route matching. The ordering of steps is security-critical — changing it introduces
* vulnerabilities:
*
*   1. Parse URL
*   2. Protocol-relative URL guard — on the raw pathname, BEFORE normalizePath collapses
*      `//` to `/`. If the guard ran after normalization, `//evil.com` → `/evil.com`
*      would bypass the check and reach the trailing-slash redirector, which echoes the
*      path into a `Location` header that browsers interpret as protocol-relative.
*   3. Strict percent-decode each segment — throws on malformed sequences (→ 400). Must
*      run before basePath check so %2F-encoded slashes cannot create fake basePath prefixes.
*   4. Collapse double-slashes, resolve `.` and `..` segments (normalizePath)
*   5. basePath check + strip — 404 when pathname lacks the basePath prefix.
*      `/__vinext/` bypasses this for internal prerender endpoints.
*   6. RSC detection: `.rsc` suffix or Next-style `RSC: 1`. The internal
*      `_rsc` cache-busting query is validated separately so full-route Flight
*      responses do not share the canonical HTML URL in caches that ignore Vary.
*   7. cleanPathname — pathname with `.rsc` suffix stripped
*   8. Sanitize X-Vinext-Interception-Context — strip null bytes (header injection)
*   9. Normalize x-vinext-mounted-slots — dedup and sort for canonical cache keys
*   10. Read semantic render mode for refresh/action payload rendering
*   11. Parse ClientReuseManifest hints on canonical RSC payload requests
*
* @returns A 400 or 404 Response for invalid or out-of-scope inputs,
*          or a NormalizedRscRequest for valid requests.
*/
function normalizeRscRequest(request, basePath, allowOutsideBasePath = false) {
	const url = new URL(request.url);
	const protoGuard = guardProtocolRelativeUrl(url.pathname);
	if (protoGuard) return protoGuard;
	let decoded;
	try {
		decoded = normalizePathnameForRouteMatchStrict(url.pathname);
	} catch {
		return badRequestResponse();
	}
	let pathname = normalizePath(decoded);
	let requestPathname = url.pathname;
	let hadBasePath = true;
	if (basePath) {
		hadBasePath = hasBasePath(requestPathname, basePath);
		if (!hadBasePath && !pathname.startsWith("/__vinext/") && !allowOutsideBasePath) return notFoundResponse();
		if (hadBasePath) {
			pathname = stripBasePath(pathname, basePath);
			requestPathname = stripBasePath(requestPathname, basePath);
		}
	}
	const isRscRequest = pathname.endsWith(".rsc") || request.headers.get("RSC") === "1";
	const cleanPathname = stripRscSuffix(pathname);
	const requestCleanPathname = stripRscSuffix(requestPathname);
	const interceptionContextHeader = normalizeInterceptionContextHeader(request.headers.get(VINEXT_INTERCEPTION_CONTEXT_HEADER));
	const mountedSlotsHeader = normalizeMountedSlotsHeader(request.headers.get(VINEXT_MOUNTED_SLOTS_HEADER));
	let renderMode = isRscRequest ? parseAppRscRenderMode(request.headers.get(VINEXT_RSC_RENDER_MODE_HEADER)) : APP_RSC_RENDER_MODE_NAVIGATION;
	if (isRscRequest && renderMode === "navigation" && request.headers.get("Next-Router-Prefetch") === "1" && request.headers.get("Next-Router-Segment-Prefetch") === null) {
		const nextUrl = request.headers.get(NEXT_URL_HEADER);
		const routerState = parsePrefetchRouterState(request.headers.get(NEXT_ROUTER_STATE_TREE_HEADER));
		if (nextUrl && routerState) {
			const targetUrl = new URL(url);
			targetUrl.pathname = cleanPathname;
			targetUrl.searchParams.delete(VINEXT_RSC_CACHE_BUSTING_SEARCH_PARAM);
			const routerPathAndSearch = tryNormalizeComparablePathAndSearch(routerState.pathAndSearch, basePath, url);
			const nextPathAndSearch = tryNormalizeComparablePathAndSearch(nextUrl, basePath, url);
			const targetPathAndSearch = normalizeComparablePathAndSearch(targetUrl.href, basePath, url);
			if (routerPathAndSearch !== null && nextPathAndSearch !== null) renderMode = routerPathAndSearch === nextPathAndSearch && routerPathAndSearch === targetPathAndSearch ? APP_RSC_RENDER_MODE_PREFETCH_EMPTY : APP_RSC_RENDER_MODE_PREFETCH_LOADING_SHELL;
		}
	}
	return {
		clientReuseManifest: isRscRequest ? parseClientReuseManifestHeader(request.headers.get(VINEXT_CLIENT_REUSE_MANIFEST_HEADER)) : { kind: "absent" },
		hadBasePath,
		url,
		pathname,
		cleanPathname,
		requestCleanPathname,
		isRscRequest,
		interceptionContextHeader,
		mountedSlotsHeader,
		renderMode
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/internal/work-unit-async-storage.js
/**
* Shim for next/dist/server/app-render/work-unit-async-storage.external
* and next/dist/client/components/request-async-storage.external
*
* Tracks the current rendering context type so that dynamic APIs
* (io, headers, cookies, etc.) can branch on whether they're
* inside a request, prerender, cache scope, or other context.
*
* Used by: @sentry/nextjs (runtime resolve for request context injection),
* io() for hanging-promise behavior during prerendering.
*/
var workUnitAsyncStorage = new AsyncLocalStorage();
registerAlsForScopeExit(workUnitAsyncStorage);
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/prerender-work-unit-setup.js
/**
* Sets up the work unit async storage for prerendering.
*
* When VINEXT_PRERENDER=1, wraps execution in a workUnitAsyncStorage.run()
* with a PrerenderStore so that dynamic APIs (e.g., io()) can
* detect the prerender context and return hanging promises.
*
* Used by: app-rsc-entry.ts handler template.
*
* TODO: If future dynamic APIs need request-scoped stores for normal (non-prerender)
* requests, add a `{ type: "request" }` store during normal request handling.
*/
function runWithPrerenderWorkUnit(fn, options) {
	if (process.env.VINEXT_PRERENDER === "1") {
		const controller = new AbortController();
		const route = typeof options?.route === "function" ? options.route() : options?.route;
		return workUnitAsyncStorage.run({
			type: "prerender",
			renderSignal: controller.signal,
			route
		}, fn).finally(() => controller.abort());
	}
	return fn();
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-rsc-handler.js
function haveSameRequestCookies(first, second) {
	if (first.size !== second.size) return false;
	for (const [name, value] of first) if (second.get(name) !== value) return false;
	return true;
}
function haveSamePageParams(first, second) {
	const firstKeys = Object.keys(first);
	const secondKeys = Object.keys(second);
	if (firstKeys.length !== secondKeys.length) return false;
	for (const key of firstKeys) {
		const firstValue = first[key];
		const secondValue = second[key];
		if (Array.isArray(firstValue)) {
			if (!Array.isArray(secondValue) || firstValue.length !== secondValue.length || firstValue.some((value, index) => value !== secondValue[index])) return false;
		} else if (firstValue !== secondValue) return false;
	}
	return true;
}
function applyMiddlewareContextToResponse(response, middlewareContext) {
	if (!middlewareContext.headers && middlewareContext.status == null) return response;
	const headers = new Headers(response.headers);
	mergeMiddlewareResponseHeaders(headers, middlewareContext.headers);
	return preserveFullyBufferedBodyMetadata(response, new Response(response.body, {
		status: middlewareContext.status ?? response.status,
		statusText: response.statusText,
		headers
	}));
}
function hasProperty(value, key) {
	return key in value;
}
function isEdgeRouteHandler(handler) {
	if (!handler || typeof handler !== "object" || !hasProperty(handler, "runtime")) return false;
	return handler.runtime === "edge" || handler.runtime === "experimental-edge";
}
function isExecutionContextLike(value) {
	if (!value || typeof value !== "object") return false;
	return hasProperty(value, "waitUntil") && typeof value.waitUntil === "function";
}
function createMissingServerActionResponse(options, actionId) {
	console.warn(getServerActionNotFoundMessage(actionId));
	options.clearRequestContext();
	return createServerActionNotFoundResponse();
}
async function applyRewrite(options, cleanPathname) {
	return null;
}
function requestContextForResolvedUrl(requestContext, resolvedUrl, baseUrl) {
	return {
		cookies: requestContext.cookies,
		headers: requestContext.headers,
		host: requestContext.host,
		query: new URL(resolvedUrl, baseUrl).searchParams
	};
}
function pathnameForResolvedUrl(resolvedUrl) {
	return resolvedUrl.split("#", 1)[0].split("?", 1)[0];
}
async function applyConfigHeadersToMiddlewareRedirect(response, options) {
	if (response.status < 300 || response.status >= 400) return response;
	return response;
}
function requestWithoutRscCacheBustingSearchParam(request) {
	const url = new URL(request.url);
	if (!hasRscCacheBustingSearchParam(url)) return request;
	stripRscCacheBustingSearchParam(url);
	return cloneRequestWithUrl(request, url.toString());
}
function requestWithoutRscSuffix(request) {
	const url = new URL(request.url);
	const pathname = stripRscSuffix(url.pathname);
	if (pathname === url.pathname) return request;
	url.pathname = pathname;
	return cloneRequestWithUrl(request, url.toString());
}
async function handleAppRscRequest(options, request, preMiddlewareRequestContext, isDataRequest, isMiddlewareDataRequest, pagesDataRequest, dispatchInternalRequest, allowInternalRscDocumentFallback) {
	const handlerStart = 0;
	const canHandleOutsideBasePath = Boolean(options.runMiddleware) || [
		...options.configRedirects,
		...options.configRewrites.beforeFiles,
		...options.configRewrites.afterFiles,
		...options.configRewrites.fallback,
		...options.configHeaders
	].some((rule) => rule.basePath === false);
	const normalized = normalizeRscRequest(request, options.basePath, canHandleOutsideBasePath);
	if (normalized instanceof Response) return normalized;
	const { url, isRscRequest, interceptionContextHeader, mountedSlotsHeader, renderMode, clientReuseManifest, hadBasePath } = normalized;
	const { requestCleanPathname } = normalized;
	let { pathname, cleanPathname } = normalized;
	let resolvedUrl = cleanPathname + url.search;
	const originalResolvedUrl = resolvedUrl;
	const getResolvedSearchParams = () => new URL(resolvedUrl, url).searchParams;
	const canonicalPathname = cleanPathname;
	const basePathState = {
		basePath: options.basePath,
		hadBasePath
	};
	let cleanPathnameIsRequestPathname = true;
	const matchCleanPathname = () => cleanPathnameIsRequestPathname && options.matchRequestRoute ? options.matchRequestRoute(requestCleanPathname) : options.matchRoute(cleanPathname);
	if (pathname === "/__vinext/prerender/static-params" || pathname === "/__vinext/prerender/pages-static-paths") {
		const { handleAppPrerenderEndpoint } = await import("./_next/static/app-prerender-endpoints-B4dGrXJz.js");
		const prerenderEndpointResponse = await handleAppPrerenderEndpoint(request, {
			isPrerenderEnabled() {
				return process.env.VINEXT_PRERENDER === "1";
			},
			loadPagesRoutes: options.loadPrerenderPagesRoutes,
			pathname,
			rootParamNamesByPattern: options.rootParamNamesByPattern,
			staticParamsMap: options.staticParamsMap
		});
		if (prerenderEndpointResponse) return prerenderEndpointResponse;
	}
	const trailingSlashRedirect = normalizeTrailingSlash(requestCleanPathname, hadBasePath ? options.basePath : "", options.trailingSlash, url.search);
	if (trailingSlashRedirect) return trailingSlashRedirect;
	const matchPathname = (p) => normalizeDefaultLocalePathname(p, options.i18nConfig, { hostname: url.hostname });
	matchPathname(requestCleanPathname);
	const rscCacheBustingRedirect = hadBasePath ? await resolveInvalidRscCacheBustingRequest({
		isRscRequest,
		request
	}) : null;
	if (rscCacheBustingRedirect) return rscCacheBustingRedirect;
	let filesystemRouteEligible = hadBasePath;
	const validateClaimedOutsideBasePathRsc = async (routeClaimed = filesystemRouteEligible) => {
		if (hadBasePath || !routeClaimed) return null;
		return resolveInvalidRscCacheBustingRequest({
			isRscRequest,
			request
		});
	};
	const runMiddleware = isOnDemandRevalidateRequest(request.headers.get("x-prerender-revalidate")) ? void 0 : options.runMiddleware;
	const isolatedMiddlewareSource = runMiddleware && request.body && !request.bodyUsed ? request.clone() : null;
	const normalizedUserlandRequest = requestWithoutRscSuffix(request);
	const userlandRequest = requestWithoutRscCacheBustingSearchParam(normalizedUserlandRequest);
	const isolatedMiddlewareRequest = isolatedMiddlewareSource ? requestWithoutRscCacheBustingSearchParam(requestWithoutRscSuffix(isolatedMiddlewareSource)) : void 0;
	const middlewareContext = {
		headers: null,
		requestHeaders: null,
		status: null
	};
	let didMiddlewareRewrite = false;
	let didMiddlewareRewritePathname = false;
	if (runMiddleware) {
		const middlewareResult = await runMiddleware({
			cleanPathname,
			context: middlewareContext,
			externalRewriteRequest: normalizedUserlandRequest,
			hadBasePath,
			isDataRequest: isMiddlewareDataRequest,
			middlewareRequest: isolatedMiddlewareRequest,
			request: userlandRequest,
			validateExternalRewriteRequest: () => validateClaimedOutsideBasePathRsc(true)
		});
		if (middlewareResult.kind === "response") {
			if (request.body && !request.body.locked) request.body.cancel().catch(() => {});
			return applyConfigHeadersToMiddlewareRedirect(middlewareResult.response, {
				basePathState,
				configHeaders: options.configHeaders,
				pathname: matchPathname(requestCleanPathname),
				requestContext: preMiddlewareRequestContext
			});
		}
		cleanPathname = middlewareResult.cleanPathname;
		didMiddlewareRewrite = middlewareResult.rewritten;
		if (didMiddlewareRewrite || cleanPathname !== normalized.cleanPathname) cleanPathnameIsRequestPathname = false;
		didMiddlewareRewritePathname = cleanPathname !== normalized.cleanPathname;
		if (middlewareResult.search !== null) url.search = middlewareResult.search;
		resolvedUrl = cleanPathname + url.search;
	}
	const scriptNonce = getScriptNonceFromHeaderSources(request.headers, middlewareContext.headers);
	const postMiddlewareRequestContext = buildPostMwRequestContext(userlandRequest);
	filesystemRouteEligible ||= didMiddlewareRewrite;
	for (const rewrite of options.configRewrites.beforeFiles) {
		const beforeFilesRewrite = await applyRewrite({
			basePathState,
			clearRequestContext: options.clearRequestContext,
			request: normalizedUserlandRequest,
			requestContext: requestContextForResolvedUrl(postMiddlewareRequestContext, resolvedUrl, url),
			paramsPathname: matchPathname(cleanPathnameIsRequestPathname ? requestCleanPathname : cleanPathname),
			rewrites: [rewrite],
			validateExternalRewriteRequest: () => validateClaimedOutsideBasePathRsc(true)
		}, matchPathname(cleanPathname));
		if (beforeFilesRewrite instanceof Response) return beforeFilesRewrite;
		if (beforeFilesRewrite) {
			resolvedUrl = mergeRewriteQuery(resolvedUrl, beforeFilesRewrite);
			cleanPathname = pathnameForResolvedUrl(resolvedUrl);
			cleanPathnameIsRequestPathname = false;
			filesystemRouteEligible = true;
		}
	}
	const claimedRscCacheBustingRedirect = await validateClaimedOutsideBasePathRsc();
	if (claimedRscCacheBustingRedirect) return claimedRscCacheBustingRedirect;
	const actionId = request.headers.get("x-rsc-action") ?? request.headers.get("next-action");
	const isPostRequest = request.method.toUpperCase() === "POST";
	const contentType = request.headers.get("content-type") || "";
	const isProgressiveActionRequest = isPostRequest && !actionId && contentType.startsWith("multipart/form-data");
	let resolvedLateRewritesForAction = false;
	if (!filesystemRouteEligible && (actionId || isProgressiveActionRequest)) {
		let actionMatch = null;
		for (const rewrite of options.configRewrites.afterFiles) {
			const rewritten = await applyRewrite({
				basePathState,
				clearRequestContext: options.clearRequestContext,
				request: normalizedUserlandRequest,
				requestContext: requestContextForResolvedUrl(postMiddlewareRequestContext, resolvedUrl, url),
				paramsPathname: matchPathname(cleanPathnameIsRequestPathname ? requestCleanPathname : cleanPathname),
				rewrites: [rewrite],
				validateExternalRewriteRequest: () => validateClaimedOutsideBasePathRsc(true)
			}, matchPathname(cleanPathname));
			if (rewritten instanceof Response) return rewritten;
			if (!rewritten) continue;
			resolvedUrl = mergeRewriteQuery(resolvedUrl, rewritten);
			cleanPathname = pathnameForResolvedUrl(resolvedUrl);
			cleanPathnameIsRequestPathname = false;
			filesystemRouteEligible = true;
			actionMatch = matchCleanPathname();
			if (actionMatch) break;
		}
		if (!actionMatch) for (const rewrite of options.configRewrites.fallback) {
			const rewritten = await applyRewrite({
				basePathState,
				clearRequestContext: options.clearRequestContext,
				request: normalizedUserlandRequest,
				requestContext: requestContextForResolvedUrl(postMiddlewareRequestContext, resolvedUrl, url),
				paramsPathname: matchPathname(cleanPathnameIsRequestPathname ? requestCleanPathname : cleanPathname),
				rewrites: [rewrite],
				validateExternalRewriteRequest: () => validateClaimedOutsideBasePathRsc(true)
			}, matchPathname(cleanPathname));
			if (rewritten instanceof Response) return rewritten;
			if (!rewritten) continue;
			resolvedUrl = mergeRewriteQuery(resolvedUrl, rewritten);
			cleanPathname = pathnameForResolvedUrl(resolvedUrl);
			cleanPathnameIsRequestPathname = false;
			filesystemRouteEligible = true;
			actionMatch = matchCleanPathname();
			if (actionMatch) break;
		}
		resolvedLateRewritesForAction = filesystemRouteEligible;
	}
	const lateActionRscCacheBustingRedirect = await validateClaimedOutsideBasePathRsc();
	if (lateActionRscCacheBustingRedirect) return lateActionRscCacheBustingRedirect;
	if (filesystemRouteEligible && isImageOptimizationPath(cleanPathname)) {
		const imageRedirect = resolveDevImageRedirect(url, [...options.imageConfig?.deviceSizes ?? DEFAULT_DEVICE_SIZES, ...options.imageConfig?.imageSizes ?? DEFAULT_IMAGE_SIZES], options.imageConfig?.qualities, { isDev: options.isDev });
		if (!imageRedirect) return new Response("Invalid image optimization parameters", { status: 400 });
		return Response.redirect(new URL(imageRedirect, url.origin).href, 302);
	}
	if (filesystemRouteEligible && options.handleMetadataRouteRequest) {
		const metadataRouteResponse = await options.handleMetadataRouteRequest(cleanPathname);
		if (metadataRouteResponse) return applyMiddlewareContextToResponse(metadataRouteResponse, middlewareContext);
	}
	const publicFileResponse = filesystemRouteEligible ? resolvePublicFileRoute({
		cleanPathname,
		middlewareContext,
		pathname,
		publicFiles: options.publicFiles,
		request
	}) : null;
	if (publicFileResponse) {
		options.clearRequestContext();
		return publicFileResponse;
	}
	stripRscCacheBustingSearchParam(url);
	const resolved = new URL(resolvedUrl, url);
	stripRscCacheBustingSearchParam(resolved);
	resolvedUrl = resolved.pathname + resolved.search + resolved.hash;
	options.setNavigationContext({
		pathname: canonicalPathname,
		searchParams: getResolvedSearchParams(),
		params: {}
	});
	const directPreActionMatch = filesystemRouteEligible ? matchCleanPathname() : null;
	const preActionRoutePathname = cleanPathnameIsRequestPathname ? requestCleanPathname : cleanPathname;
	let interceptionSourcePathname = null;
	if (filesystemRouteEligible && isRscRequest && interceptionContextHeader !== null) try {
		if (!isInterceptionMatchedUrlPath(interceptionContextHeader)) throw new Error("Invalid interception source pathname");
		interceptionSourcePathname = normalizePath(normalizePathnameForRouteMatchStrict(interceptionContextHeader));
	} catch {
		options.clearRequestContext();
		return badRequestResponse();
	}
	const interceptionSourceMatch = interceptionSourcePathname !== null && interceptionContextHeader !== null ? options.matchInterceptRoute?.(preActionRoutePathname, interceptionContextHeader) ?? null : null;
	if (interceptionSourceMatch !== null && interceptionSourcePathname !== null && runMiddleware && interceptionSourceMatch.route !== directPreActionMatch?.route) {
		const sourceUrl = new URL(userlandRequest.url);
		sourceUrl.search = new URL(resolvedUrl, url).search;
		sourceUrl.pathname = hadBasePath ? addBasePathToPathname(interceptionSourcePathname, options.basePath) : interceptionSourcePathname;
		const sourceRequest = userlandRequest.body ? userlandRequest.clone() : userlandRequest;
		const sourceMiddlewareRequest = cloneRequestWithUrl(sourceRequest, sourceUrl.href);
		sourceMiddlewareRequest.headers.delete(VINEXT_MW_CTX_HEADER);
		for (const header of FLIGHT_HEADERS) sourceMiddlewareRequest.headers.delete(header);
		const targetHeadersContext = getHeadersContext();
		const targetRequestHeaders = targetHeadersContext ? new Headers(targetHeadersContext.headers) : null;
		targetRequestHeaders?.delete(VINEXT_MW_CTX_HEADER);
		for (const header of FLIGHT_HEADERS) targetRequestHeaders?.delete(header);
		if (targetRequestHeaders) {
			const sourceHeaderNames = Array.from(sourceMiddlewareRequest.headers.keys());
			for (const header of sourceHeaderNames) sourceMiddlewareRequest.headers.delete(header);
			for (const [name, value] of targetRequestHeaders) sourceMiddlewareRequest.headers.append(name, value);
		}
		const sourceMiddlewareContext = {
			headers: null,
			requestHeaders: null,
			status: null
		};
		const sourceHeadersContext = headersContextFromRequest(sourceMiddlewareRequest, { draftModeSecret: options.draftModeSecret });
		let sourceMiddlewareResult;
		try {
			sourceMiddlewareResult = await runWithHeadersContext(sourceHeadersContext, () => runMiddleware({
				cleanPathname: interceptionSourcePathname,
				context: sourceMiddlewareContext,
				externalRewriteRequest: normalizedUserlandRequest,
				hadBasePath,
				isDataRequest: isMiddlewareDataRequest,
				request: sourceMiddlewareRequest,
				validateExternalRewriteRequest: () => validateClaimedOutsideBasePathRsc(true)
			}));
		} finally {
			if (sourceMiddlewareRequest.body && !sourceMiddlewareRequest.bodyUsed && !sourceMiddlewareRequest.body.locked) sourceMiddlewareRequest.body.cancel().catch(() => {});
			if (sourceRequest !== userlandRequest && sourceRequest.body && !sourceRequest.bodyUsed && !sourceRequest.body.locked) sourceRequest.body.cancel().catch(() => {});
		}
		if (sourceMiddlewareResult.kind === "response") {
			options.clearRequestContext();
			return sourceMiddlewareResult.response;
		}
		let sourceHeadersCompatible = true;
		if (targetRequestHeaders) {
			for (const [name, value] of targetRequestHeaders) if (sourceHeadersContext.headers.get(name) !== value) {
				sourceHeadersCompatible = false;
				break;
			}
		}
		if (!targetHeadersContext || !targetRequestHeaders || !sourceHeadersCompatible || !haveSameRequestCookies(targetHeadersContext.cookies, sourceHeadersContext.cookies)) {
			options.clearRequestContext();
			return notFoundResponse();
		}
		let addedSourceHeader = false;
		for (const [name, value] of sourceHeadersContext.headers) if (!targetRequestHeaders.has(name)) {
			targetHeadersContext.headers.set(name, value);
			addedSourceHeader = true;
		}
		if (addedSourceHeader) targetHeadersContext.readonlyHeaders = void 0;
		if (sourceMiddlewareResult.rewritten) {
			const rewrittenSourceMatch = options.matchRoute(sourceMiddlewareResult.cleanPathname);
			if (sourceMiddlewareResult.search !== sourceUrl.search || rewrittenSourceMatch?.route !== interceptionSourceMatch.route || !haveSamePageParams(rewrittenSourceMatch.params, interceptionSourceMatch.params)) {
				options.clearRequestContext();
				return notFoundResponse();
			}
		}
	}
	const interceptionPreActionMatch = filesystemRouteEligible && directPreActionMatch === null && isRscRequest && interceptionSourcePathname !== null ? interceptionSourceMatch : null;
	const preActionMatch = directPreActionMatch ?? interceptionPreActionMatch;
	const isInterceptionMatch = interceptionPreActionMatch !== null;
	if (preActionMatch) setRootParams(pickRootParams(preActionMatch.params, preActionMatch.route.rootParamNames));
	if (pagesDataRequest && didMiddlewareRewritePathname && preActionMatch && !preActionMatch.route.isDynamic) {
		const headers = new Headers();
		mergeMiddlewareResponseHeaders(headers, middlewareContext.headers);
		headers.set("content-type", "application/json");
		headers.set("x-nextjs-rewrite", resolvedUrl);
		options.clearRequestContext();
		return new Response("{}", { headers });
	}
	if (!filesystemRouteEligible && isPostRequest && actionId) {
		options.clearRequestContext();
		return notFoundResponse();
	}
	let progressiveActionResult = null;
	if (filesystemRouteEligible && isPostRequest && contentType.startsWith("multipart/form-data") && !actionId) {
		if (options.handleProgressiveActionRequest) progressiveActionResult = await options.handleProgressiveActionRequest({
			actionId,
			cleanPathname,
			contentType,
			middlewareContext,
			request,
			routeMatch: preActionMatch
		});
		else if (preActionMatch?.route.__loadPage && !preActionMatch.route.__loadRouteHandler) return createMissingServerActionResponse(options, null);
	}
	if (progressiveActionResult instanceof Response) return progressiveActionResult;
	const progressiveActionFormState = progressiveActionResult?.kind === "form-state" ? progressiveActionResult : null;
	const isProgressiveActionRender = progressiveActionFormState !== null;
	const formState = progressiveActionFormState?.formState ?? null;
	const failedProgressiveActionResult = progressiveActionFormState && "actionError" in progressiveActionFormState ? progressiveActionFormState : null;
	const actionFailed = failedProgressiveActionResult !== null;
	const actionError = failedProgressiveActionResult?.actionError;
	const actionErrorDigest = actionError && typeof actionError === "object" && "digest" in actionError ? String(actionError.digest) : null;
	const actionHttpFallbackStatus = actionErrorDigest ? parseNextHttpErrorDigest(actionErrorDigest)?.status ?? null : null;
	const normalizedProgressiveActionError = actionHttpFallbackStatus === null || actionHttpFallbackStatus === 404 ? actionError : { digest: "NEXT_NOT_FOUND" };
	if (actionFailed && middlewareContext.status === null && actionHttpFallbackStatus === null) middlewareContext.status = 500;
	let sourceConfigHeaders = null;
	if (filesystemRouteEligible && isPostRequest && actionId && options.handleServerActionRequest) {
		sourceConfigHeaders = new Headers();
		const sourceConfigUrl = new URL(request.url);
		sourceConfigUrl.pathname = hadBasePath ? addBasePathToPathname(requestCleanPathname, options.basePath) : requestCleanPathname;
		await applyAppRscConfigHeaders(sourceConfigHeaders, cloneRequestWithUrl(request, sourceConfigUrl.toString()), {
			basePath: options.basePath,
			configHeaders: options.configHeaders,
			i18nConfig: options.i18nConfig,
			requestContext: preMiddlewareRequestContext
		});
	}
	const serverActionResponse = filesystemRouteEligible && isPostRequest && actionId && options.handleServerActionRequest ? await options.handleServerActionRequest({
		actionId,
		cleanPathname,
		contentType,
		interceptionContext: interceptionContextHeader,
		isRscRequest,
		middlewareContext,
		mountedSlotsHeader,
		request,
		scriptNonce,
		routeMatch: preActionMatch,
		routePathname: preActionRoutePathname,
		dispatchRedirectTargetRequest: dispatchInternalRequest,
		sourceConfigHeaders,
		searchParams: getResolvedSearchParams()
	}) : null;
	if (serverActionResponse) return serverActionResponse;
	if (filesystemRouteEligible && isPostRequest && actionId && !options.handleServerActionRequest) return createMissingServerActionResponse(options, actionId);
	let match = preActionMatch;
	const renderPagesForMatchKind = async (matchKind) => {
		if (!filesystemRouteEligible) return null;
		const response = !isInterceptionMatch && (match === null || match.route.isDynamic) ? await options.renderPagesFallback?.({
			appRouteMatch: match ?? null,
			allowRscDocumentFallback: didMiddlewareRewritePathname || allowInternalRscDocumentFallback,
			isDataRequest,
			isRscRequest,
			matchKind,
			middlewareContext,
			pathname: resolvedUrl,
			pagesDataRequest,
			request,
			url
		}) ?? null : null;
		if (!response || !pagesDataRequest || resolvedUrl === originalResolvedUrl) return response;
		const headers = new Headers(response.headers);
		headers.set("x-nextjs-rewrite", resolvedUrl);
		return new Response(response.body, {
			headers,
			status: response.status,
			statusText: response.statusText
		});
	};
	const staticPagesFallbackResponse = await renderPagesForMatchKind("static");
	if (staticPagesFallbackResponse) {
		options.clearRequestContext();
		return staticPagesFallbackResponse;
	}
	if (!isInterceptionMatch && !resolvedLateRewritesForAction && (!match || match.route.isDynamic)) for (const rewrite of options.configRewrites.afterFiles) {
		const afterFilesRewrite = await applyRewrite({
			basePathState,
			clearRequestContext: options.clearRequestContext,
			request: normalizedUserlandRequest,
			requestContext: requestContextForResolvedUrl(postMiddlewareRequestContext, resolvedUrl, url),
			paramsPathname: matchPathname(cleanPathnameIsRequestPathname ? requestCleanPathname : cleanPathname),
			rewrites: [rewrite],
			validateExternalRewriteRequest: () => validateClaimedOutsideBasePathRsc(true)
		}, matchPathname(cleanPathname));
		if (afterFilesRewrite instanceof Response) return afterFilesRewrite;
		if (!afterFilesRewrite) continue;
		resolvedUrl = mergeRewriteQuery(resolvedUrl, afterFilesRewrite);
		cleanPathname = pathnameForResolvedUrl(resolvedUrl);
		cleanPathnameIsRequestPathname = false;
		filesystemRouteEligible = true;
		const claimedRscCacheBustingRedirect = await validateClaimedOutsideBasePathRsc();
		if (claimedRscCacheBustingRedirect) return claimedRscCacheBustingRedirect;
		match = matchCleanPathname();
		const rewrittenStaticPagesResponse = await renderPagesForMatchKind("static");
		if (rewrittenStaticPagesResponse) {
			options.clearRequestContext();
			return rewrittenStaticPagesResponse;
		}
		const rewrittenDynamicPagesResponse = await renderPagesForMatchKind("dynamic");
		if (rewrittenDynamicPagesResponse) {
			options.clearRequestContext();
			return rewrittenDynamicPagesResponse;
		}
		if (match) break;
	}
	const dynamicPagesFallbackResponse = await renderPagesForMatchKind("dynamic");
	if (dynamicPagesFallbackResponse) {
		options.clearRequestContext();
		return dynamicPagesFallbackResponse;
	}
	if (!resolvedLateRewritesForAction && !match) for (const rewrite of options.configRewrites.fallback) {
		const fallbackRewrite = await applyRewrite({
			basePathState,
			clearRequestContext: options.clearRequestContext,
			request: normalizedUserlandRequest,
			requestContext: requestContextForResolvedUrl(postMiddlewareRequestContext, resolvedUrl, url),
			paramsPathname: matchPathname(cleanPathnameIsRequestPathname ? requestCleanPathname : cleanPathname),
			rewrites: [rewrite],
			validateExternalRewriteRequest: () => validateClaimedOutsideBasePathRsc(true)
		}, matchPathname(cleanPathname));
		if (fallbackRewrite instanceof Response) return fallbackRewrite;
		if (!fallbackRewrite) continue;
		resolvedUrl = mergeRewriteQuery(resolvedUrl, fallbackRewrite);
		cleanPathname = pathnameForResolvedUrl(resolvedUrl);
		cleanPathnameIsRequestPathname = false;
		filesystemRouteEligible = true;
		const claimedRscCacheBustingRedirect = await validateClaimedOutsideBasePathRsc();
		if (claimedRscCacheBustingRedirect) return claimedRscCacheBustingRedirect;
		match = matchCleanPathname();
		const rewrittenStaticPagesResponse = await renderPagesForMatchKind("static");
		if (rewrittenStaticPagesResponse) {
			options.clearRequestContext();
			return rewrittenStaticPagesResponse;
		}
		const rewrittenDynamicPagesResponse = await renderPagesForMatchKind("dynamic");
		if (rewrittenDynamicPagesResponse) {
			options.clearRequestContext();
			return rewrittenDynamicPagesResponse;
		}
		if (match) break;
	}
	if (!filesystemRouteEligible) {
		options.clearRequestContext();
		const headers = new Headers();
		mergeMiddlewareResponseHeaders(headers, middlewareContext.headers);
		return notFoundResponse({ headers });
	}
	if (pagesDataRequest) {
		options.clearRequestContext();
		if (runMiddleware && (middlewareContext.status === null || middlewareContext.status === 200 || middlewareContext.status === 404)) {
			const response = buildNextDataNotFoundResponse();
			const headers = new Headers(response.headers);
			mergeMiddlewareResponseHeaders(headers, middlewareContext.headers);
			headers.set("x-nextjs-matched-path", matchPathname(canonicalPathname));
			if (resolvedUrl !== originalResolvedUrl) headers.set("x-nextjs-rewrite", resolvedUrl);
			return new Response("{}", {
				status: 200,
				headers
			});
		}
		return buildNextDataNotFoundResponse();
	}
	if (!match) {
		const renderedNotFoundResponse = await options.renderNotFound({
			isRscRequest,
			middlewareContext,
			request,
			route: null,
			scriptNonce
		});
		if (renderedNotFoundResponse) return renderedNotFoundResponse;
		options.clearRequestContext();
		const headers = new Headers();
		mergeMiddlewareResponseHeaders(headers, middlewareContext.headers);
		return notFoundResponse({ headers });
	}
	const { route, params } = match;
	if (options.ensureRouteLoaded) await options.ensureRouteLoaded(route);
	const resolvedSearchParams = getResolvedSearchParams();
	if (isRouteTreePrefetchRequest(request) && !route.routeHandler) {
		const response = await createRouteTreePrefetchResponse(route, {
			buildId: options.buildId,
			prefetchInlining: options.prefetchInlining
		});
		options.clearRequestContext();
		return applyMiddlewareContextToResponse(response, middlewareContext);
	}
	const prerenderRouteParamsMatch = matchPrerenderRouteParamsPayload(readTrustedPrerenderRouteParams(request), route.pattern, params);
	const prerenderRouteParams = prerenderRouteParamsMatch?.params ?? null;
	const isPrerenderFallbackShell = prerenderRouteParamsMatch?.kind === "fallback-shell";
	const renderParams = prerenderRouteParams ?? params;
	let runtimeFallbackShells = [];
	if (options.createPprFallbackShells && request.method === "GET" && !isRscRequest && !isPrerenderFallbackShell && route.params) runtimeFallbackShells = options.createPprFallbackShells({
		params: route.params,
		pattern: route.pattern,
		rootParamNames: route.rootParamNames
	}, params);
	options.setNavigationContext({
		pathname: canonicalPathname,
		searchParams: resolvedSearchParams,
		params: renderParams
	});
	const rootParams = pickRootParams(renderParams, route.rootParamNames);
	setRootParams(rootParams);
	if (route.routeHandler) {
		setCurrentFetchSoftTags(buildPageCacheTags(cleanPathname, [], [...route.routeSegments], "route"));
		const routeHandlerRequest = isEdgeRouteHandler(route.routeHandler) ? userlandRequest : normalizedUserlandRequest;
		const routeHandlerUrl = new URL(routeHandlerRequest.url);
		const internalRscValues = isEdgeRouteHandler(route.routeHandler) ? [] : routeHandlerUrl.searchParams.getAll(VINEXT_RSC_CACHE_BUSTING_SEARCH_PARAM);
		routeHandlerUrl.search = resolvedSearchParams.toString();
		for (const internalRscValue of internalRscValues) routeHandlerUrl.searchParams.append(VINEXT_RSC_CACHE_BUSTING_SEARCH_PARAM, internalRscValue);
		return options.dispatchMatchedRouteHandler({
			cleanPathname,
			middlewareContext,
			params: route.isDynamic ? renderParams : null,
			request: new Request(routeHandlerUrl, routeHandlerRequest),
			route,
			searchParams: resolvedSearchParams
		});
	}
	const pageResponse = await options.dispatchMatchedPage({
		clientReuseManifest,
		cleanPathname,
		displayPathname: canonicalPathname,
		formState,
		actionError: normalizedProgressiveActionError,
		actionFailed,
		handlerStart,
		interceptionContext: interceptionContextHeader,
		interceptionPathname: cleanPathnameIsRequestPathname ? requestCleanPathname : cleanPathname,
		isProgressiveActionRender,
		isRscRequest,
		middlewareContext,
		mountedSlotsHeader,
		params: renderParams,
		pprFallbackCacheShells: runtimeFallbackShells,
		pprFallbackShell: isPrerenderFallbackShell ? {
			fallbackParamNames: prerenderRouteParamsMatch.fallbackParamNames,
			routePattern: route.pattern
		} : void 0,
		renderedConcreteUrlPaths: getRenderedConcreteUrlPathsForRoute$1(route.pattern),
		skipStaticParamsValidation: isPrerenderFallbackShell,
		staticParamsValidationParams: prerenderRouteParams === null || isPrerenderFallbackShell ? void 0 : params,
		rootParams,
		request,
		renderedPathAndSearch: resolvedUrl,
		route,
		scriptNonce,
		searchParams: resolvedSearchParams,
		renderMode
	});
	if (isProgressiveActionRender) return applyProgressiveActionSideEffects(pageResponse, progressiveActionFormState);
	return pageResponse;
}
/**
* Append `Set-Cookie` headers and the `x-action-revalidated` marker captured
* during progressive (no-JS) server action execution to the page render
* response. See issue #1483.
*
* Falls back to rebuilding the response when the headers object is immutable
* (e.g. `Response.redirect()`), so cookies set by the action ride out on a
* redirect issued during the rerender too.
*/
function applyProgressiveActionSideEffects(response, sideEffects) {
	const hasPendingCookies = sideEffects.pendingCookies.length > 0;
	const hasDraftCookie = Boolean(sideEffects.draftCookie);
	const hasRevalidationKind = sideEffects.revalidationKind !== 0;
	if (!hasPendingCookies && !hasDraftCookie && !hasRevalidationKind) return response;
	const applyTo = (headers) => {
		for (const cookie of sideEffects.pendingCookies) headers.append("Set-Cookie", cookie);
		if (sideEffects.draftCookie) headers.append("Set-Cookie", sideEffects.draftCookie);
		if (hasRevalidationKind) headers.set(ACTION_REVALIDATED_HEADER, JSON.stringify(sideEffects.revalidationKind));
	};
	try {
		applyTo(response.headers);
		return response;
	} catch {
		const headers = new Headers(response.headers);
		applyTo(headers);
		return new Response(response.body, {
			status: response.status,
			statusText: response.statusText,
			headers
		});
	}
}
function createAppRscHandler(options) {
	return async function appRscHandler(rawRequest, ctx, allowInternalRscDocumentFallback = false) {
		options.registerCacheAdapters();
		await options.ensureInstrumentation?.();
		const mwCtx = rawRequest.headers.get(VINEXT_MW_CTX_HEADER);
		const pagesDataUrl = new URL(rawRequest.url);
		const pagesDataInScope = !options.basePath || hasBasePath(pagesDataUrl.pathname, options.basePath);
		if (pagesDataInScope) pagesDataUrl.pathname = stripBasePath(pagesDataUrl.pathname, options.basePath);
		const pagesDataCandidate = pagesDataInScope ? cloneRequestWithUrl(rawRequest, pagesDataUrl.toString()) : null;
		const pagesDataNormalization = options.renderPagesFallback && pagesDataCandidate ? normalizePagesDataRequest(pagesDataCandidate, options.buildId, "", typeof options.runMiddleware === "function" && options.trailingSlash) : null;
		if (pagesDataNormalization?.notFoundResponse) return pagesDataNormalization.notFoundResponse;
		const isPagesDataRequest = pagesDataNormalization?.isDataReq === true;
		const executionContext = isExecutionContextLike(ctx) ? ctx : getRequestExecutionContext() ?? null;
		const prerenderRouteParamsPayload = readTrustedPrerenderRouteParams(rawRequest);
		const isTrustedSpeculativePrerender = process.env.VINEXT_PRERENDER === "1" && rawRequest.headers.get("x-vinext-prerender-secret") !== null && rawRequest.headers.get("x-vinext-prerender-speculative") === "1";
		const filteredHeaders = executionContext?.isInternalPagesRevalidation ? new Headers(rawRequest.headers) : filterInternalHeaders(rawRequest.headers);
		filteredHeaders.delete(VINEXT_REVALIDATE_HOST_HEADER);
		if (mwCtx !== null) filteredHeaders.set(VINEXT_MW_CTX_HEADER, mwCtx);
		const prerenderRouteParamsHeader = serializePrerenderRouteParamsHeader(prerenderRouteParamsPayload);
		if (prerenderRouteParamsHeader !== null) filteredHeaders.set(VINEXT_PRERENDER_ROUTE_PARAMS_HEADER, prerenderRouteParamsHeader);
		if (isTrustedSpeculativePrerender) filteredHeaders.set(VINEXT_PRERENDER_SPECULATIVE_HEADER, "1");
		let appRequest = rawRequest;
		if (pagesDataNormalization?.isDataReq) {
			const appRequestUrl = new URL(pagesDataNormalization.request.url);
			appRequestUrl.pathname = addBasePathToPathname(appRequestUrl.pathname, options.basePath);
			appRequest = cloneRequestWithUrl(pagesDataCandidate, appRequestUrl.toString());
		}
		const request = cloneRequestWithHeaders(appRequest, filteredHeaders);
		const pagesDataRequest = pagesDataNormalization?.isDataReq ? cloneRequestWithHeaders(pagesDataCandidate, filteredHeaders) : null;
		const requestContext = createRequestContext({
			headersContext: headersContextFromRequest(request, { draftModeSecret: options.draftModeSecret }),
			executionContext,
			unstableCacheRevalidation: "background"
		});
		const responsePromise = runWithRequestContext(requestContext, () => runWithPrerenderWorkUnit(async () => {
			ensureFetchPatch();
			const preMiddlewareRequestContext = requestContextFromRequest(request);
			let response;
			try {
				response = await handleAppRscRequest(options, request, preMiddlewareRequestContext, isPagesDataRequest, isPagesDataRequest, pagesDataRequest, (internalRequest) => appRscHandler(internalRequest, ctx, true), allowInternalRscDocumentFallback);
			} catch (error) {
				throw error;
			}
			return finalizeAppRscResponse(response, request, {
				basePath: options.basePath,
				configHeaders: options.configHeaders,
				i18nConfig: options.i18nConfig,
				requestContext: preMiddlewareRequestContext
			});
		}, { route: () => new URL(request.url).pathname }));
		let response;
		try {
			response = await responsePromise;
		} catch (error) {
			await closeAfterResponse(requestContext);
			throw error;
		}
		return closeAfterResponseWithBody(response, requestContext);
	};
}
//#endregion
//#region \0virtual:vinext-cache-adapters
function registerConfiguredCacheAdapters() {}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/navigation-signal.js
function getErrorDigest(error) {
	if (!error || typeof error !== "object" || !("digest" in error)) return null;
	return String(error.digest);
}
function isNavigationSignalError(error) {
	const digest = getErrorDigest(error);
	if (digest === null) return false;
	return digest === "NEXT_NOT_FOUND" || digest.startsWith("NEXT_HTTP_ERROR_FALLBACK;") || digest.startsWith("NEXT_REDIRECT;");
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/html.js
/**
* HTML-safe JSON serialization for embedding data in <script> tags.
*
* JSON.stringify does NOT escape characters that are meaningful to the
* HTML parser. If a JSON string value contains "<\/script>", the browser
* closes the script tag early — anything after it executes as HTML.
* This is a well-known stored XSS vector in SSR frameworks.
*
* Next.js mitigates this with htmlEscapeJsonString(). We do the same.
*
* Characters escaped:
*   <   → \u003c   (prevents <\/script> and <!-- breakout)
*   >   → \u003e   (prevents --> and other HTML close sequences)
*   &   → \u0026   (prevents &lt; entity interpretation in XHTML)
*   \u2028 → \\u2028 (line separator — invalid in JS string literals pre-ES2019)
*   \u2029 → \\u2029 (paragraph separator — same)
*
* The result is valid JSON that is also safe to embed in any HTML context
* without additional escaping.
*/
function safeJsonStringify(data) {
	return JSON.stringify(data).replace(/</g, "\\u003c").replace(/>/g, "\\u003e").replace(/&/g, "\\u0026").replace(/\u2028/g, "\\u2028").replace(/\u2029/g, "\\u2029");
}
function escapeHtmlAttr(value) {
	return value.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function createNonceAttribute(nonce) {
	if (!nonce) return "";
	return ` nonce="${escapeHtmlAttr(nonce)}"`;
}
function createInlineScriptTag(content, nonce) {
	return `<script${createNonceAttribute(nonce)}>${content}<\/script>`;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-ssr-error-meta.js
var PERMANENT_REDIRECT_STATUS = 308;
function prefixRedirectLocation(location, basePath) {
	if (!basePath || !location.startsWith("/")) return location;
	const hashIndex = location.indexOf("#");
	const queryIndex = location.indexOf("?");
	const pathnameEnd = queryIndex === -1 ? hashIndex === -1 ? location.length : hashIndex : hashIndex === -1 ? queryIndex : Math.min(queryIndex, hashIndex);
	return addBasePathToPathname(location.slice(0, pathnameEnd), basePath) + location.slice(pathnameEnd);
}
function renderSsrErrorMetaTag(error, options) {
	const digest = getNextErrorDigest(error);
	if (!digest) return "";
	if (parseNextHttpErrorDigest(digest)) {
		let html = "<meta name=\"robots\" content=\"noindex\"/>";
		if ((options.nodeEnv ?? "production") === "development") html += "<meta name=\"next-error\" content=\"not-found\"/>";
		return html;
	}
	const redirect = parseNextRedirectDigest(digest);
	if (!redirect) return "";
	const delay = redirect.status === PERMANENT_REDIRECT_STATUS ? 0 : 1;
	const location = prefixRedirectLocation(redirect.url, options.basePath);
	return "<meta id=\"__next-page-redirect\" http-equiv=\"refresh\" content=\"" + delay + ";url=" + escapeHtmlAttr(location) + "\"/>";
}
function renderSsrErrorMetaTags(errors, options = {}) {
	let html = "";
	for (const error of errors) html += renderSsrErrorMetaTag(error, options);
	return html;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-rsc-redirect-flight.js
/**
* Encoding of a `redirect()` for RSC transport: the canonical
* `NEXT_REDIRECT;<type>;<url>;<status>;` digest and the flight payload that
* carries it. Kept in one module so the digest format and the stream that
* serializes it have a single owner; `buildAppPageSpecialErrorResponse` and the
* boundary/dispatch special-error paths all depend on this contract.
*/
/**
* Builds the canonical `NEXT_REDIRECT;<type>;<url>;<status>;` digest that
* Next.js encodes on `redirect()` / `permanentRedirect()` throws. Used when we
* synthesize a flight payload for an RSC navigation: the digest must round-trip
* through the client's `RedirectErrorBoundary` so the same
* `getURLFromRedirectError` / `getRedirectTypeFromError` helpers decode it.
*
* The URL is included verbatim, not encoded — Next.js's `getRedirectError`
* sets `digest = ${CODE};${type};${url};${status};` with the raw URL, and the
* client decodes via `error.digest.split(';').slice(2, -2).join(';')`. We
* default `type=replace` because `redirect()` is replace-style outside of
* server actions, matching Next.js's `getRedirectError` default.
*
* Reference:
*   `.nextjs-ref/packages/next/src/client/components/redirect.ts:20-23`
*   `.nextjs-ref/packages/next/src/client/components/redirect-error.ts`
*/
function formatNextRedirectDigest(options) {
	return `NEXT_REDIRECT;${options.type};${options.url};${options.statusCode};`;
}
/**
* Error thrown by the redirect-flight renderer below. Its `digest` is the
* canonical `NEXT_REDIRECT;...` string that react-server-dom's `onError`
* reports so the client's `RedirectErrorBoundary` can decode it. A named
* subclass keeps `digest` a real field rather than an `as`-cast on a plain
* `Error`.
*/
var RscRedirectFlightError = class extends Error {
	digest;
	constructor(digest) {
		super("NEXT_REDIRECT");
		this.digest = digest;
	}
};
/**
* Builds an RSC flight payload that encodes a `redirect()` as a React error
* carrying the canonical `NEXT_REDIRECT;<type>;<url>;<status>;` digest. We
* render a tiny element that throws immediately; `renderToReadableStream`'s
* `onError` returns the digest, react-server-dom-webpack serializes the error
* into the stream, and the client's `RedirectErrorBoundary` decodes it via
* `getURLFromRedirectError` / `getRedirectTypeFromError`. The HTTP response
* stays 200 because the redirect rides in the flight body, not the status line.
*
* Mirrors Next.js's `generateDynamicFlightRenderResult` in `app-render.tsx`,
* where a redirect thrown during RSC rendering propagates through
* `renderToFlightStream`'s `onError` into the flight payload.
*
* This is the single owner of the redirect-flight encoding: the matched
* dispatch paths (`renderLayoutSpecialError` / `renderPageSpecialError`) and the
* route-miss boundary path (`renderBoundarySpecialErrorResponse`) both call it
* through the `buildRscRedirectFlightStream` option of
* `buildAppPageSpecialErrorResponse`.
*/
function buildRscRedirectFlightStream(options) {
	const { digest } = options;
	const throwingElement = (0, import_react_react_server.createElement)(function NextRedirectFlightThrower() {
		throw new RscRedirectFlightError(digest);
	});
	return options.renderToReadableStream(throwingElement, { onError: () => digest });
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-execution.js
/**
* Marker we tag onto a thrown redirect/notFound error when it originates from
* `generateMetadata()` (vs. a server component itself). Metadata resolution is
* suspended/streamed in Next.js, so a redirect from metadata is not emitted as
* a plain HTTP-level 307. Instead the transport depends on the request:
*   - RSC navigation requests (`Rsc: 1`) ride inside the flight payload with a
*     200 status; the client router decodes the redirect digest.
*   - Streaming-capable document requests get a 200 HTML response carrying a
*     refresh meta tag (the streamed document can't switch to a 307 after the
*     head has flushed).
*   - html-limited bots (which Next.js serves a blocking, non-streamed
*     response) get the HTTP-level 307.
* Page-level redirect()s, by contrast, still produce a 307 for SSR document
* requests.
*
* See Next.js test:
*   test/e2e/app-dir/metadata-streaming/metadata-streaming.test.ts
*/
var APP_PAGE_METADATA_ERROR_MARKER = Symbol.for("vinext.appPage.metadataError");
function tagAppPageMetadataError(error) {
	if (error && typeof error === "object") try {
		Object.defineProperty(error, APP_PAGE_METADATA_ERROR_MARKER, {
			value: true,
			enumerable: false,
			configurable: true,
			writable: false
		});
	} catch {}
	return error;
}
function getAppPageStatusText(statusCode) {
	return statusCode === 403 ? "Forbidden" : statusCode === 401 ? "Unauthorized" : "Not Found";
}
function mergeAppPageSpecialErrorHeaders(response, middlewareContext) {
	const headers = new Headers(response.headers);
	mergeMiddlewareResponseHeaders(headers, middlewareContext?.headers ?? null);
	return new Response(response.body, {
		headers,
		status: response.status,
		statusText: response.statusText
	});
}
function resolveAppPageSpecialError(error) {
	if (!(error && typeof error === "object" && "digest" in error)) return null;
	const digest = String(error.digest);
	const fromMetadata = Reflect.get(error, APP_PAGE_METADATA_ERROR_MARKER) === true;
	const redirect = parseNextRedirectDigest(digest);
	if (redirect) return {
		kind: "redirect",
		location: redirect.url,
		statusCode: redirect.status,
		type: redirect.type === "push" ? "push" : "replace",
		...fromMetadata ? { fromMetadata: true } : {}
	};
	const httpError = parseNextHttpErrorDigest(digest);
	if (httpError) return {
		kind: "http-access-fallback",
		statusCode: httpError.status,
		...fromMetadata ? { fromMetadata: true } : {}
	};
	return null;
}
/**
* Resolves a redirect() target against the request URL and prepends the
* configured basePath when the target is an app-internal absolute path.
*
* Mirrors Next.js's `addPathPrefix(getURLFromRedirectError(err), basePath)`
* in `app-render.tsx`: a `redirect("/about")` call from a page mounted at
* `/blog` (basePath) produces `Location: /blog/about`.
*
* Skips prefixing only when basePath is unset or the raw target does not start
* with `/`, matching Next.js's literal `addPathPrefix()` contract.
*/
function applyAppPageRedirectBasePath(location, basePath) {
	if (!basePath || !location.startsWith("/")) return location;
	const queryIndex = location.indexOf("?");
	const hashIndex = location.indexOf("#");
	const suffixIndex = queryIndex === -1 ? hashIndex : hashIndex === -1 ? queryIndex : Math.min(queryIndex, hashIndex);
	return `${basePath}${suffixIndex === -1 ? location : location.slice(0, suffixIndex)}${suffixIndex === -1 ? "" : location.slice(suffixIndex)}`;
}
/**
* Returns a path-relative form (`/foo?bar`) of an absolute URL when it shares
* the request's origin; otherwise returns the URL verbatim. Used so the digest
* we embed in the flight payload matches Next.js's convention — the digest
* stores the path the developer passed to `redirect("/about")`, not a
* fully-qualified URL like `https://example.com/about`.
*/
function sameOriginPathOrAbsolute(location, requestUrl) {
	try {
		const resolved = new URL(location, requestUrl);
		const requestOrigin = new URL(requestUrl).origin;
		if (resolved.origin !== requestOrigin) return resolved.toString();
		return `${resolved.pathname}${resolved.search}${resolved.hash}`;
	} catch {
		return location;
	}
}
function buildMetadataRedirectHtmlResponse(options) {
	const headers = new Headers({ "Content-Type": "text/html; charset=utf-8" });
	applyEdgeRuntimeHeader(headers, options.isEdgeRuntime);
	mergeMiddlewareResponseHeaders(headers, options.middlewareContext?.headers ?? null);
	const pendingCookies = options.getAndClearPendingCookies?.() ?? [];
	for (const cookie of pendingCookies) headers.append("Set-Cookie", cookie);
	const errorMetaTags = renderSsrErrorMetaTags([{ digest: options.digest }]);
	return new Response(`<!DOCTYPE html><html><head>${errorMetaTags}</head><body></body></html>`, {
		headers,
		status: 200
	});
}
async function buildAppPageSpecialErrorResponse(options) {
	if (options.specialError.kind === "redirect") {
		options.clearRequestContext();
		const prefixedLocation = applyAppPageRedirectBasePath(options.specialError.location, options.basePath);
		const digestUrl = sameOriginPathOrAbsolute(prefixedLocation, options.request.url);
		const digest = formatNextRedirectDigest({
			type: options.specialError.type ?? "replace",
			url: digestUrl,
			statusCode: options.specialError.statusCode
		});
		if (options.specialError.fromMetadata === true && !options.isRscRequest && options.serveStreamingMetadata !== false) return buildMetadataRedirectHtmlResponse({
			digest,
			getAndClearPendingCookies: options.getAndClearPendingCookies,
			isEdgeRuntime: options.isEdgeRuntime,
			middlewareContext: options.middlewareContext
		});
		if (Boolean(options.buildRscRedirectFlightStream) && options.isRscRequest && options.buildRscRedirectFlightStream) {
			const stream = options.buildRscRedirectFlightStream({ digest });
			const headers = new Headers({ "Content-Type": VINEXT_RSC_CONTENT_TYPE });
			applyEdgeRuntimeHeader(headers, options.isEdgeRuntime);
			applyRscCompatibilityIdHeader(headers);
			applyRscDeploymentIdHeader(headers);
			mergeMiddlewareResponseHeaders(headers, options.middlewareContext?.headers ?? null);
			headers.set(VINEXT_RSC_REDIRECT_HEADER, digestUrl);
			headers.set(VINEXT_RSC_REDIRECT_TYPE_HEADER, options.specialError.type ?? "replace");
			const pendingCookies = options.getAndClearPendingCookies?.() ?? [];
			for (const cookie of pendingCookies) headers.append("Set-Cookie", cookie);
			return new Response(stream, {
				headers,
				status: 200
			});
		}
		const location = options.isRscRequest ? await createRscRedirectLocation(prefixedLocation, options.request) : prefixedLocation;
		const headers = new Headers({ Location: location });
		mergeMiddlewareResponseHeaders(headers, options.middlewareContext?.headers ?? null);
		const pendingCookies = options.getAndClearPendingCookies?.() ?? [];
		for (const cookie of pendingCookies) headers.append("Set-Cookie", cookie);
		return new Response(null, {
			headers,
			status: options.specialError.statusCode
		});
	}
	if (options.renderFallbackPage) {
		const fallbackResponse = await options.renderFallbackPage(options.specialError.statusCode);
		if (fallbackResponse) return mergeAppPageSpecialErrorHeaders(options.specialError.fromMetadata === true && options.serveStreamingMetadata !== false ? new Response(fallbackResponse.body, {
			headers: fallbackResponse.headers,
			status: 200,
			statusText: fallbackResponse.statusText
		}) : fallbackResponse, options.middlewareContext);
	}
	options.clearRequestContext();
	const responseStatus = options.specialError.fromMetadata === true && options.serveStreamingMetadata !== false ? 200 : options.specialError.statusCode;
	return mergeAppPageSpecialErrorHeaders(new Response(getAppPageStatusText(options.specialError.statusCode), { status: responseStatus }), options.middlewareContext);
}
/** See `LayoutFlags` type docblock in app-elements.ts for lifecycle. */
async function probeAppPageLayouts(options) {
	const layoutFlags = {};
	const cls = options.classification ?? null;
	return {
		response: await options.runWithSuppressedHookWarning(async () => {
			for (let layoutIndex = options.layoutCount - 1; layoutIndex >= 0; layoutIndex--) {
				const buildTimeResult = cls?.buildTimeClassifications?.get(layoutIndex);
				if (cls && buildTimeResult) {
					const layoutId = cls.getLayoutId(layoutIndex);
					layoutFlags[layoutId] = buildTimeResult === "static" ? "s" : "d";
					const errorResponse = await probeLayoutForErrors(options, layoutIndex);
					if (errorResponse) return errorResponse;
					const observationDynamic = cls.isLayoutObservationDynamic?.(layoutId) === true;
					layoutFlags[layoutId] = buildTimeResult === "dynamic" || observationDynamic ? "d" : "s";
					if (cls.debugClassification) if (observationDynamic && buildTimeResult === "static") cls.debugClassification(layoutId, {
						layer: "runtime-probe",
						outcome: "dynamic"
					});
					else cls.debugClassification(layoutId, cls.buildTimeReasons?.get(layoutIndex) ?? { layer: "no-classifier" });
					continue;
				}
				if (cls) {
					const layoutId = cls.getLayoutId(layoutIndex);
					try {
						const { dynamicDetected } = await cls.runWithIsolatedDynamicScope(async () => {
							const outcome = await runWithConnectionProbe(() => options.probeLayoutAt(layoutIndex));
							return outcome.completed ? outcome.result : null;
						});
						const observationDynamic = cls.isLayoutObservationDynamic?.(layoutId) === true;
						const layoutDynamic = dynamicDetected || observationDynamic;
						layoutFlags[layoutId] = layoutDynamic ? "d" : "s";
						if (cls.debugClassification) cls.debugClassification(layoutId, {
							layer: "runtime-probe",
							outcome: layoutDynamic ? "dynamic" : "static"
						});
					} catch (error) {
						layoutFlags[layoutId] = "d";
						if (cls.debugClassification) cls.debugClassification(layoutId, {
							layer: "runtime-probe",
							outcome: "dynamic",
							error: error instanceof Error ? error.message : String(error)
						});
						const errorResponse = await options.onLayoutError(error, layoutIndex);
						if (errorResponse) return errorResponse;
					}
					continue;
				}
				const errorResponse = await probeLayoutForErrors(options, layoutIndex);
				if (errorResponse) return errorResponse;
			}
			return null;
		}),
		layoutFlags
	};
}
async function probeLayoutForErrors(options, layoutIndex) {
	const outcome = await runWithConnectionProbe(async () => {
		try {
			const layoutResult = options.probeLayoutAt(layoutIndex);
			if (isPromiseLike(layoutResult)) await layoutResult;
		} catch (error) {
			return options.onLayoutError(error, layoutIndex);
		}
		return null;
	});
	return outcome.completed ? outcome.result : null;
}
async function probeAppPageComponent(options) {
	return options.runWithSuppressedHookWarning(async () => {
		const outcome = await runWithConnectionProbe(async () => {
			try {
				const pageResult = options.probePage();
				if (isPromiseLike(pageResult)) if (options.awaitAsyncResult) await pageResult;
				else Promise.resolve(pageResult).catch(() => {});
			} catch (error) {
				return options.onError(error);
			}
			return null;
		});
		return outcome.completed ? outcome.result : null;
	});
}
async function probeAppPageThrownError(options) {
	return options.runWithSuppressedHookWarning(async () => {
		const outcome = await runWithConnectionProbe(async () => {
			try {
				const pageResult = options.probePage();
				if (isPromiseLike(pageResult)) await pageResult;
			} catch (error) {
				return {
					error,
					thrown: true
				};
			}
			return {
				error: null,
				thrown: false
			};
		});
		return outcome.completed && outcome.result.thrown ? outcome.result.error : null;
	});
}
async function readAppPageBinaryStream(stream) {
	const reader = stream.getReader();
	const chunks = [];
	let totalLength = 0;
	for (;;) {
		const { done, value } = await reader.read();
		if (done) break;
		chunks.push(value);
		totalLength += value.byteLength;
	}
	const buffer = new Uint8Array(totalLength);
	let offset = 0;
	for (const chunk of chunks) {
		buffer.set(chunk, offset);
		offset += chunk.byteLength;
	}
	return buffer.buffer;
}
async function bufferAppPageBinaryStream(stream) {
	const reader = stream.getReader();
	const chunks = [];
	for (;;) {
		const { done, value } = await reader.read();
		if (done) break;
		chunks.push(value);
	}
	return new ReadableStream({ start(controller) {
		for (const chunk of chunks) controller.enqueue(chunk);
		controller.close();
	} });
}
function teeAppPageRscStreamForCapture(stream, shouldCapture) {
	if (!shouldCapture) return { ssrStream: stream };
	const [ssrStream, sideStream] = stream.tee();
	return {
		ssrStream,
		sideStream
	};
}
function buildAppPageFontLinkHeader(preloads) {
	if (!preloads || preloads.length === 0) return "";
	return preloads.map((preload) => `<${preload.href}>; rel=preload; as=font; type=${preload.type}; crossorigin`).join(", ");
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-rsc-errors.js
var ORIGINAL_SERVER_ERROR = Symbol.for("vinext.originalServerError");
function hasDigest(error) {
	return Boolean(error && typeof error === "object" && "digest" in error);
}
var BAILOUT_TO_CSR_DIGEST = "BAILOUT_TO_CLIENT_SIDE_RENDERING";
var DYNAMIC_SERVER_USAGE_DIGEST = "DYNAMIC_SERVER_USAGE";
function isAbortError(error) {
	if (!error || typeof error !== "object") return false;
	const name = Reflect.get(error, "name");
	return name === "AbortError" || name === "ResponseAborted";
}
/**
* vinext's mirror of Next.js's `getDigestForWellKnownError`: returns the digest
* string only when the error is a genuine control-flow signal — a redirect,
* notFound/HTTP-access fallback, bail-out-to-client-side-rendering, or
* dynamic-server-usage throw. Any other digest (e.g. a hashed digest stamped on
* a real error, or an obfuscated digest transported from a nested boundary)
* returns undefined so the caller still reports it as a real error. Mere
* presence of a `digest` field is NOT enough — that conflation swallowed a class
* of server render errors with no instrumentation/telemetry.
*/
function getDigestForWellKnownError(error) {
	if (!hasDigest(error)) return;
	const digest = String(error.digest);
	if (isNavigationSignalError(error) || digest === BAILOUT_TO_CSR_DIGEST || digest === DYNAMIC_SERVER_USAGE_DIGEST) return digest;
}
function getThrownValueMessage(error) {
	return error instanceof Error ? error.message : String(error);
}
function getThrownValueStack(error) {
	return error instanceof Error ? error.stack || "" : "";
}
/**
* djb2 hash matching Next.js's string-hash package for RSC error digests.
*/
function errorDigest(input) {
	let hash = 5381;
	for (let i = input.length - 1; i >= 0; i--) hash = hash * 33 ^ input.charCodeAt(i);
	return (hash >>> 0).toString();
}
function sanitizeErrorForClient(error, nodeEnv = "production") {
	if (resolveAppPageSpecialError(error)) return error;
	if (nodeEnv !== "production") return error;
	const sanitized = /* @__PURE__ */ new Error("An error occurred in the Server Components render. The specific message is omitted in production builds to avoid leaking sensitive details. A digest property is included on this error instance which may provide additional details about the nature of the error.");
	sanitized.digest = hasDigest(error) ? String(error.digest) : errorDigest(getThrownValueMessage(error) + getThrownValueStack(error));
	Object.defineProperty(sanitized, ORIGINAL_SERVER_ERROR, {
		configurable: false,
		enumerable: false,
		value: error,
		writable: false
	});
	return sanitized;
}
function createRscOnErrorHandler$1(options) {
	return (error) => {
		const nodeEnv = options.nodeEnv ?? "production";
		if (isAbortError(error)) return;
		const wellKnownDigest = getDigestForWellKnownError(error);
		if (wellKnownDigest !== void 0) return wellKnownDigest;
		if (nodeEnv !== "production" && error instanceof Error && error.message.includes("Only plain objects, and a few built-ins, can be passed to Client Components")) {
			console.error("[vinext] RSC serialization error: a non-plain object was passed from a Server Component to a Client Component.\n\nCommon causes:\n  * Passing a module namespace (import * as X) directly as a prop.\n    Unlike Next.js (webpack), Vite produces real ESM module namespace objects\n    which are not serializable. Fix: pass individual values instead,\n    e.g. <Comp value={module.value} />\n  * Passing a class instance (new Foo()) as a prop.\n    Fix: convert to a plain object, e.g. { id: foo.id, name: foo.name }\n  * Passing a Date, Map, or Set. Use .toISOString(), [...map.entries()], etc.\n  * Passing Object.create(null). Use { ...obj } to restore a prototype.\n\nOriginal error:", error.message);
			return;
		}
		if (options.requestInfo && options.errorContext && error) {
			const reportableError = typeof error === "object" && ORIGINAL_SERVER_ERROR in error ? Reflect.get(error, ORIGINAL_SERVER_ERROR) : error;
			options.reportRequestError(reportableError instanceof Error ? reportableError : new Error(getThrownValueMessage(reportableError)), options.requestInfo, options.errorContext);
		}
		if (nodeEnv !== "production" && error && !hasDigest(error)) {
			const loggableError = typeof error === "object" && ORIGINAL_SERVER_ERROR in error ? Reflect.get(error, ORIGINAL_SERVER_ERROR) : error;
			console.error("[vinext] Server render error:", loggableError);
		}
		if (hasDigest(error)) return String(error.digest);
		if (error) {
			const digest = errorDigest(getThrownValueMessage(error) + getThrownValueStack(error));
			if (error instanceof Error) try {
				Object.assign(error, { digest });
			} catch {}
			return digest;
		}
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-rsc-error-handler.js
/**
* Build a per-request RSC error handler that extracts request metadata from
* the incoming Web `Request`, wires it into a `createRscOnErrorHandler` call,
* and binds the configured `reportRequestError` reporter.
*
* Pure factory: takes all deps explicitly — no closure over module-level state.
*/
function createAppRscOnErrorHandler(reportRequestError, request, pathname, routePath) {
	const requestHeaders = Object.fromEntries(request.headers.entries());
	const requestInfo = {
		path: pathname,
		method: request.method,
		headers: requestHeaders
	};
	return createRscOnErrorHandler$1({
		errorContext: {
			routerKind: "App Router",
			routePath: routePath || pathname,
			routeType: "render"
		},
		reportRequestError,
		requestInfo
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/default-global-error.js
var default_global_error_default = /* @__PURE__ */ registerClientReference(() => {
	throw new Error("Unexpectedly client reference export 'default' is called on server");
}, "8c59b4cfb786", "default");
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/default-global-error-module.js
/**
* Module-shaped wrapper around vinext's built-in default global error
* component. Used as the fallback when an app does not define its own
* `app/global-error.tsx`. The runtime treats any `{ default: Component }`
* record as a "global error module", so wrapping the component this way lets
* us thread the default through the existing `globalErrorModule` plumbing
* without introducing a parallel code path.
*
* Mirrors Next.js's `defaultGlobalErrorPath`
* (`next/dist/client/components/builtin/global-error.js`), which is selected
* automatically when the user has not supplied a custom global error file:
* https://github.com/vercel/next.js/blob/canary/packages/next/src/build/webpack/loaders/next-app-loader/index.ts
*/
var DEFAULT_GLOBAL_ERROR_MODULE = { default: default_global_error_default };
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/html-limited-bots.js
var HTML_LIMITED_BOT_UA_RE_STRING = String.raw`(?:^|[^\w-])[\w-]+-Google|Google-[\w-]+|Chrome-Lighthouse|Slurp|DuckDuckBot|baiduspider|yandex|sogou|bitlybot|tumblr|vkShare|quora link preview|redditbot|ia_archiver|Bingbot|BingPreview|applebot|facebookexternalhit|facebookcatalog|meta-externalagent|meta-externalfetcher|Twitterbot|LinkedInBot|Slackbot|Discordbot|WhatsApp|SkypeUriPreview|Yeti|googleweblight`;
var htmlLimitedBotRegexCache = /* @__PURE__ */ new Map();
function getHtmlLimitedBotRegex(htmlLimitedBots) {
	const source = htmlLimitedBots || HTML_LIMITED_BOT_UA_RE_STRING;
	const cached = htmlLimitedBotRegexCache.get(source);
	if (cached) return cached;
	const regex = new RegExp(source, "i");
	htmlLimitedBotRegexCache.set(source, regex);
	return regex;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/streaming-metadata.js
function shouldServeStreamingMetadata(userAgent, htmlLimitedBots) {
	if (!userAgent) return true;
	return !getHtmlLimitedBotRegex(htmlLimitedBots).test(userAgent);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/error-boundary.js
var ErrorBoundary = /* @__PURE__ */ registerClientReference(() => {
	throw new Error("Unexpectedly client reference export 'ErrorBoundary' is called on server");
}, "be06c29e631a", "ErrorBoundary");
var ForbiddenBoundary = /* @__PURE__ */ registerClientReference(() => {
	throw new Error("Unexpectedly client reference export 'ForbiddenBoundary' is called on server");
}, "be06c29e631a", "ForbiddenBoundary");
var GlobalErrorBoundary = /* @__PURE__ */ registerClientReference(() => {
	throw new Error("Unexpectedly client reference export 'GlobalErrorBoundary' is called on server");
}, "be06c29e631a", "GlobalErrorBoundary");
var NotFoundBoundary = /* @__PURE__ */ registerClientReference(() => {
	throw new Error("Unexpectedly client reference export 'NotFoundBoundary' is called on server");
}, "be06c29e631a", "NotFoundBoundary");
var RedirectBoundary = /* @__PURE__ */ registerClientReference(() => {
	throw new Error("Unexpectedly client reference export 'RedirectBoundary' is called on server");
}, "be06c29e631a", "RedirectBoundary");
var SerializedErrorBoundary = /* @__PURE__ */ registerClientReference(() => {
	throw new Error("Unexpectedly client reference export 'SerializedErrorBoundary' is called on server");
}, "be06c29e631a", "SerializedErrorBoundary");
var UnauthorizedBoundary = /* @__PURE__ */ registerClientReference(() => {
	throw new Error("Unexpectedly client reference export 'UnauthorizedBoundary' is called on server");
}, "be06c29e631a", "UnauthorizedBoundary");
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/layout-segment-context.js
/**
* Layout segment context provider.
*
* Must be "use client" so that Vite's RSC bundler renders this component in
* the SSR/browser environment where React.createContext is available. The RSC
* entry imports and renders LayoutSegmentProvider directly, but because of the
* "use client" boundary the actual execution happens on the SSR/client side
* where the context can be created and consumed by useSelectedLayoutSegment(s).
*
* Without "use client", this runs in the RSC environment where
* React.createContext is undefined, getLayoutSegmentContext() returns null,
* the provider becomes a no-op, and useSelectedLayoutSegments always returns [].
*
* The context is shared with navigation.ts via getLayoutSegmentContext()
* to avoid creating separate contexts in different modules.
*/
/**
* Wraps children with the layout segment context.
*
* Each layout in the App Router tree wraps its children with this provider,
* passing a map of parallel route key to segment path. The "children" key is
* always present (the default parallel route). Named parallel slots at this
* layout level add their own keys.
*
* Components inside the provider call useSelectedLayoutSegments(parallelRoutesKey)
* to read the segments for a specific parallel route.
*/
var LayoutSegmentProvider = /* @__PURE__ */ registerClientReference(() => {
	throw new Error("Unexpectedly client reference export 'LayoutSegmentProvider' is called on server");
}, "243ee20defce", "LayoutSegmentProvider");
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-params.js
function getAppPageSegmentParamName(segment) {
	if (segment.startsWith("[[...") && segment.endsWith("]]") && segment.length > 7) return segment.slice(5, -2);
	if (segment.startsWith("[...") && segment.endsWith("]") && segment.length > 5) return segment.slice(4, -1);
	if (segment.startsWith("[") && segment.endsWith("]") && !segment.includes(".") && segment.length > 2) return segment.slice(1, -1);
	return null;
}
function isEmptyOptionalCatchAll(segment, paramValue) {
	return segment.startsWith("[[...") && Array.isArray(paramValue) && paramValue.length === 0;
}
function resolveAppPageSegmentParamScopeKeys(routeSegments, treePosition) {
	const paramNames = [];
	const seen = /* @__PURE__ */ new Set();
	const segments = routeSegments ?? [];
	const end = Math.min(Math.max(treePosition, 0), segments.length);
	for (let index = 0; index < end; index++) {
		const paramName = getAppPageSegmentParamName(segments[index]);
		if (!paramName || seen.has(paramName)) continue;
		seen.add(paramName);
		paramNames.push(paramName);
	}
	return paramNames;
}
function resolveAppPageSegmentParams(routeSegments, treePosition, matchedParams) {
	const segmentParams = {};
	const segments = routeSegments ?? [];
	const end = Math.min(Math.max(treePosition, 0), segments.length);
	for (let index = 0; index < end; index++) {
		const segment = segments[index];
		const paramName = getAppPageSegmentParamName(segment);
		if (!paramName) continue;
		const paramValue = matchedParams[paramName];
		if (paramValue === void 0 || isEmptyOptionalCatchAll(segment, paramValue)) continue;
		segmentParams[paramName] = paramValue;
	}
	return segmentParams;
}
function resolveAppPageBranchParams(branchSegments, treePosition, matchedParams, scopedSegments = branchSegments) {
	const branchParamNames = new Set(branchSegments.map(getAppPageSegmentParamName).filter((name) => name !== null));
	const scopedParams = {};
	for (const [name, value] of Object.entries(matchedParams)) if (!branchParamNames.has(name)) scopedParams[name] = value;
	Object.assign(scopedParams, resolveAppPageSegmentParams(scopedSegments, treePosition, matchedParams));
	return scopedParams;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-head.js
/**
* Wrapped {@link _resolveModuleMetadata} that tags any thrown error with the
* `APP_PAGE_METADATA_ERROR_MARKER` symbol. The marker lets downstream special-
* error handling distinguish a `generateMetadata()` redirect/notFound from a
* page-component redirect/notFound, which matters because metadata is
* suspended/streamed in Next.js. Its redirects no longer become a plain
* HTTP 307: RSC navigation rides inside the flight payload (200), streaming
* document SSR gets an HTML refresh meta tag (200), and html-limited bots
* get a blocking 307 — whereas page redirects still emit a 307 for SSR.
* See https://github.com/cloudflare/vinext/issues/1347
* and Next.js test/e2e/app-dir/metadata-streaming.
*/
async function resolveModuleMetadata(...args) {
	try {
		return await resolveModuleMetadata$1(...args);
	} catch (error) {
		throw tagAppPageMetadataError(error);
	}
}
function resolveActiveParallelRouteHeadInputs(options) {
	return Object.entries(options.slots ?? {}).map(([slotKey, slot]) => {
		const ownerTreePosition = options.layoutTreePositions?.[slot.layoutIndex ?? 0] ?? 0;
		const ownerParams = resolveAppPageSegmentParams(options.routeSegments, ownerTreePosition, options.params);
		const slotParams = options.slotParams?.[slotKey] ?? options.params;
		const notFoundParams = slot.notFound ? {
			...ownerParams,
			...resolveParallelLayoutParams(slot.routeSegments ?? options.routeSegments, slot.notFoundTreePosition ?? 0, slotParams)
		} : null;
		if (options.interceptSlotKey === slotKey && options.interceptPage) {
			const interceptLayouts = options.interceptLayouts ?? [];
			const inheritedSlotNotFound = slot.notFoundTreePosition === 0 ? slot.notFound ?? null : null;
			const interceptNotFound = options.interceptNotFound ?? inheritedSlotNotFound;
			const interceptNotFoundParams = interceptNotFound ? {
				...ownerParams,
				...resolveParallelLayoutParams(options.interceptNotFoundBranchSegments ?? options.interceptBranchSegments ?? options.routeSegments, options.interceptNotFound ? options.interceptNotFoundTreePosition ?? 0 : slot.notFoundTreePosition ?? 0, options.interceptParams ?? options.params)
			} : null;
			return {
				head: {
					layoutModules: [slot.layout, ...interceptLayouts].filter(isPresent$1),
					layoutParams: [...slot.layout ? [ownerParams] : [], ...interceptLayouts.filter(isPresent$1).map((_, index) => {
						const segments = options.interceptLayoutSegments?.[index] ?? [];
						return {
							...ownerParams,
							...resolveParallelLayoutParams(options.interceptBranchSegments ?? segments, segments.length, options.interceptParams ?? options.params)
						};
					})],
					layoutTreePositions: [...slot.layout ? [0] : [], ...interceptLayouts.filter(isPresent$1).map(() => options.routeSegments.length)],
					pageModule: options.interceptPage,
					params: options.interceptParams ?? options.params,
					routeSegments: options.interceptSourcePageSegments ?? options.routeSegments
				},
				...interceptNotFound ? {
					notFoundModule: interceptNotFound,
					notFoundParams: interceptNotFoundParams
				} : {},
				ownerTreePosition
			};
		}
		return {
			head: {
				layoutModules: [slot.layout, ...slot.configLayouts ?? []].filter(isPresent$1),
				layoutParams: [...slot.layout ? [ownerParams] : [], ...(slot.configLayoutTreePositions ?? []).map((treePosition) => ({
					...ownerParams,
					...resolveParallelLayoutParams(slot.routeSegments ?? options.routeSegments, treePosition, options.slotParams?.[slotKey] ?? options.params)
				}))],
				layoutTreePositions: [...slot.layout ? [0] : [], ...slot.configLayoutTreePositions ?? []],
				pageModule: slot.page,
				params: slotParams,
				routeSegments: slot.routeSegments ?? options.routeSegments
			},
			...slot.notFound ? {
				notFoundModule: slot.notFound,
				notFoundParams
			} : {},
			ownerTreePosition
		};
	}).sort((left, right) => right.ownerTreePosition - left.ownerTreePosition);
}
function isPresent$1(value) {
	return value !== null && value !== void 0;
}
function resolveParallelLayoutParams(routeSegments, treePosition, params) {
	return resolveAppPageBranchParams(routeSegments, treePosition, params);
}
function hasGenerateMetadata(module) {
	return typeof module?.generateMetadata === "function";
}
function collectAppPageSearchParams(searchParams) {
	const pageSearchParams = Object.create(null);
	let hasSearchParams = false;
	searchParams?.forEach((value, key) => {
		hasSearchParams = true;
		const currentValue = pageSearchParams[key];
		if (Array.isArray(currentValue)) {
			pageSearchParams[key] = [...currentValue, value];
			return;
		}
		if (currentValue !== void 0) {
			pageSearchParams[key] = [currentValue, value];
			return;
		}
		pageSearchParams[key] = value;
	});
	return {
		hasSearchParams,
		pageSearchParams
	};
}
function createMetadataSources(metadataResults, routeSegments, layoutTreePositions, pageMetadata, includePageSource) {
	const metadataSources = metadataResults.map((metadata, index) => ({
		routeSegments: routeSegments.slice(0, layoutTreePositions[index] ?? 0),
		metadata
	}));
	if (includePageSource) metadataSources.push({
		routeSegments,
		metadata: pageMetadata
	});
	return metadataSources;
}
async function finalizeAppPageMetadata(metadata, metadataSources, options) {
	let resolvedMetadata = metadata;
	if (options.applyFileBasedMetadata && options.metadataRoutes.length > 0) try {
		resolvedMetadata = await options.applyFileBasedMetadata(metadata, options.routePath, options.params, options.metadataRoutes, {
			routeSegments: options.routeSegments ?? [],
			metadataSources,
			basePath: options.basePath ?? ""
		});
	} catch (error) {
		if (!options.fallbackOnFileMetadataError) throw error;
		console.error(`[vinext] File-based metadata resolution failed while rendering error boundary for ${options.routePath}:`, error);
	}
	return resolvedMetadata ? postProcessMetadata(resolvedMetadata) : null;
}
function createLayoutInputs(layoutModules, layoutTreePositions) {
	const layoutInputs = [];
	for (let index = 0; index < layoutModules.length; index++) {
		const layoutModule = layoutModules[index];
		if (!isPresent$1(layoutModule)) continue;
		layoutInputs.push({
			module: layoutModule,
			treePosition: layoutTreePositions[index] ?? 0
		});
	}
	return layoutInputs;
}
async function resolveLayoutMetadata(layoutInputs, params, routeSegments) {
	const layoutMetadataPromises = [];
	let accumulatedMetadata = Promise.resolve({});
	for (const layoutInput of layoutInputs) {
		const parentForLayout = accumulatedMetadata;
		const layoutParams = resolveAppPageSegmentParams(routeSegments, layoutInput.treePosition, params);
		const metadataPromise = resolveModuleMetadata(layoutInput.module, layoutParams, void 0, parentForLayout);
		layoutMetadataPromises.push(metadataPromise);
		metadataPromise.catch(() => null);
		accumulatedMetadata = metadataPromise.then(async (metadataResult) => {
			if (metadataResult) return mergeMetadataEntries([{ metadata: await parentForLayout }, { metadata: metadataResult }]);
			return parentForLayout;
		});
		accumulatedMetadata.catch(() => null);
	}
	return Promise.all(layoutMetadataPromises);
}
function resolveLayoutViewport(layoutInputs, params, routeSegments) {
	const viewportPromises = [];
	let accumulatedViewport = Promise.resolve(mergeViewport([]));
	for (const layoutInput of layoutInputs) {
		const parentForLayout = accumulatedViewport;
		const layoutParams = resolveAppPageSegmentParams(routeSegments, layoutInput.treePosition, params);
		const viewportPromise = resolveModuleViewport(layoutInput.module, layoutParams, void 0, parentForLayout);
		viewportPromises.push(viewportPromise);
		viewportPromise.catch(() => null);
		accumulatedViewport = mergeResolvedViewport(parentForLayout, viewportPromise);
		accumulatedViewport.catch(() => null);
	}
	return {
		resolvedViewport: accumulatedViewport,
		viewportResults: Promise.all(viewportPromises)
	};
}
function mergeResolvedViewport(parent, viewport) {
	return Promise.all([parent, viewport]).then(([resolvedParent, resolvedViewport]) => resolvedViewport ? mergeViewport([resolvedParent, resolvedViewport]) : resolvedParent);
}
function getParallelRouteModules(parallelRoute) {
	return [...parallelRoute.layoutModules ?? [], parallelRoute.layoutModule].filter(isPresent$1);
}
function parallelRouteHasDynamicMetadata(parallelRoute) {
	return getParallelRouteModules(parallelRoute).some(hasGenerateMetadata) || hasGenerateMetadata(parallelRoute.pageModule);
}
async function resolveParallelRouteMetadata(parallelRoute, fallbackParams, fallbackRouteSegments, pageSearchParams, parent, searchParamsObserver) {
	const params = parallelRoute.params ?? fallbackParams;
	const routeSegments = parallelRoute.routeSegments ?? fallbackRouteSegments;
	const metadataResults = [];
	const metadataSources = [];
	let accumulatedMetadata = parent;
	const layoutModules = getParallelRouteModules(parallelRoute);
	const layoutTreePositions = parallelRoute.layoutTreePositions ?? [];
	const layoutParams = parallelRoute.layoutParams ?? [];
	for (const [index, layoutModule] of layoutModules.entries()) {
		const layoutMetadata = await resolveModuleMetadata(layoutModule, layoutParams[index] ?? resolveParallelLayoutParams(routeSegments, layoutTreePositions[index] ?? 0, params), void 0, accumulatedMetadata);
		metadataResults.push(layoutMetadata);
		metadataSources.push({
			metadata: layoutMetadata,
			routeSegments
		});
		if (layoutMetadata) {
			accumulatedMetadata = accumulatedMetadata.then(async (parentMetadata) => mergeMetadataEntries([{ metadata: parentMetadata }, { metadata: layoutMetadata }]));
			accumulatedMetadata.catch(() => null);
		}
	}
	if (parallelRoute.pageModule) {
		const pageMetadata = await resolveModuleMetadata(parallelRoute.pageModule, params, pageSearchParams, accumulatedMetadata, searchParamsObserver);
		metadataResults.push(pageMetadata);
		metadataSources.push({
			metadata: pageMetadata,
			routeSegments
		});
	}
	return {
		metadataResults,
		metadataSources
	};
}
function resolveParallelRouteViewport(parallelRoute, fallbackParams, fallbackRouteSegments, pageSearchParams, parent, searchParamsObserver) {
	const params = parallelRoute.params ?? fallbackParams;
	const routeSegments = parallelRoute.routeSegments ?? fallbackRouteSegments;
	const layoutModules = getParallelRouteModules(parallelRoute);
	const layoutTreePositions = parallelRoute.layoutTreePositions ?? [];
	const layoutParams = parallelRoute.layoutParams ?? [];
	const viewportPromises = [];
	let accumulatedViewport = parent;
	for (const [index, layoutModule] of layoutModules.entries()) {
		const parentForLayout = accumulatedViewport;
		const viewportPromise = resolveModuleViewport(layoutModule, layoutParams[index] ?? resolveParallelLayoutParams(routeSegments, layoutTreePositions[index] ?? 0, params), void 0, parentForLayout);
		viewportPromises.push(viewportPromise);
		viewportPromise.catch(() => null);
		accumulatedViewport = mergeResolvedViewport(parentForLayout, viewportPromise);
		accumulatedViewport.catch(() => null);
	}
	if (parallelRoute.pageModule) {
		const parentForPage = accumulatedViewport;
		const viewportPromise = resolveModuleViewport(parallelRoute.pageModule, params, pageSearchParams, parentForPage, searchParamsObserver);
		viewportPromises.push(viewportPromise);
		viewportPromise.catch(() => null);
		accumulatedViewport = mergeResolvedViewport(parentForPage, viewportPromise);
		accumulatedViewport.catch(() => null);
	}
	return {
		resolvedViewport: accumulatedViewport,
		viewportResults: Promise.all(viewportPromises)
	};
}
/**
* Resolve an explicit metadata-source sequence.
*
* Route-specific conventions own source selection and ordering. This resolver
* only supplies each source with its accumulated parent, merges the results,
* and applies file-based metadata at the end.
*/
function resolveOrderedAppPageMetadata(options) {
	return runWithFetchDedupe(async () => {
		const metadataPromises = [];
		let accumulatedEntriesPromise = Promise.resolve([]);
		for (const source of options.sources) {
			const parentPromise = accumulatedEntriesPromise.then((entries) => entries.length > 0 ? mergeMetadataEntries(entries) : {});
			const metadataPromise = resolveModuleMetadata(source.module, source.params, source.searchParams, parentPromise, source.searchParamsObserver);
			metadataPromises.push(metadataPromise);
			metadataPromise.catch(() => null);
			accumulatedEntriesPromise = Promise.all([accumulatedEntriesPromise, metadataPromise]).then(([entries, metadata]) => metadata ? [...entries, { metadata }] : entries);
			accumulatedEntriesPromise.catch(() => null);
		}
		const [metadataEntries, metadataResults] = await Promise.all([accumulatedEntriesPromise, Promise.all(metadataPromises)]);
		const metadataSources = options.sources.flatMap((source, index) => {
			const metadata = metadataResults[index] ?? null;
			return metadata || source.includeWhenEmpty ? [{
				metadata,
				routeSegments: source.routeSegments
			}] : [];
		});
		return finalizeAppPageMetadata(metadataEntries.length > 0 ? mergeMetadataEntries(metadataEntries) : null, metadataSources, options);
	});
}
async function resolveAppPageHead(options) {
	const prepared = prepareAppPageHead(options);
	const [metadata, viewport] = await Promise.all([prepared.metadata, prepared.viewport]);
	return {
		...prepared,
		metadata,
		viewport
	};
}
/**
* Start metadata and viewport resolution without coupling their completion.
*
* Live document renders can place the metadata promise behind Suspense while
* still waiting for viewport tags before the shell is emitted. Blocking
* callers use {@link resolveAppPageHead} and observe the same result as before.
*/
function prepareAppPageHead(options) {
	return runWithFetchDedupe(() => prepareAppPageHeadInner(options));
}
function prepareAppPageHeadInner(options) {
	const routeSegments = options.routeSegments ?? [];
	const layoutTreePositions = options.layoutTreePositions ?? [];
	const layoutInputs = createLayoutInputs(options.layoutModules, layoutTreePositions);
	const layoutSourcePositions = layoutInputs.map((input) => input.treePosition);
	const primaryHasDynamicMetadata = layoutInputs.some((input) => hasGenerateMetadata(input.module)) || hasGenerateMetadata(options.pageModule);
	const { hasSearchParams, pageSearchParams } = collectAppPageSearchParams(options.searchParams);
	const layoutMetadataPromise = resolveLayoutMetadata(layoutInputs, options.params, routeSegments);
	const layoutViewport = resolveLayoutViewport(layoutInputs, options.params, routeSegments);
	const layoutViewportPromise = layoutViewport.viewportResults;
	const layoutMetadataResultsForParent = layoutMetadataPromise.then((metadataResults) => metadataResults.filter(isPresent$1));
	layoutMetadataResultsForParent.catch(() => null);
	const pageParentPromise = layoutMetadataResultsForParent.then((metadataResults) => metadataResults.length > 0 ? mergeMetadataEntries(metadataResults.map((metadata) => ({ metadata }))) : {});
	pageParentPromise.catch(() => null);
	const pageMetadataPromise = options.pageModule ? resolveModuleMetadata(options.pageModule, options.params, pageSearchParams, pageParentPromise, options.searchParamsObserver) : Promise.resolve(null);
	const parallelRoutes = options.parallelRoutes ?? [];
	const parallelRouteMetadataPromise = Promise.all(parallelRoutes.map((parallelRoute) => resolveParallelRouteMetadata(parallelRoute, options.params, routeSegments, pageSearchParams, pageParentPromise, options.searchParamsObserver)));
	const parallelRouteViewportPromises = [];
	let accumulatedViewport = layoutViewport.resolvedViewport;
	const pageParentViewport = accumulatedViewport;
	const pageViewportPromise = options.pageModule ? resolveModuleViewport(options.pageModule, options.params, pageSearchParams, pageParentViewport, options.searchParamsObserver) : Promise.resolve(null);
	if (options.pageModule) {
		accumulatedViewport = mergeResolvedViewport(pageParentViewport, pageViewportPromise);
		accumulatedViewport.catch(() => null);
	}
	for (const parallelRoute of parallelRoutes) {
		const parallelViewport = resolveParallelRouteViewport(parallelRoute, options.params, routeSegments, pageSearchParams, accumulatedViewport, options.searchParamsObserver);
		parallelRouteViewportPromises.push(parallelViewport.viewportResults);
		accumulatedViewport = parallelViewport.resolvedViewport;
	}
	const parallelRouteViewportPromise = Promise.all(parallelRouteViewportPromises);
	const hasDynamicMetadata = primaryHasDynamicMetadata || parallelRoutes.some(parallelRouteHasDynamicMetadata);
	const metadata = Promise.all([
		layoutMetadataPromise,
		pageMetadataPromise,
		parallelRouteMetadataPromise
	]).then(async ([layoutMetadataResults, pageMetadata, parallelRouteMetadata]) => {
		const parallelMetadataResults = parallelRouteMetadata.flatMap((head) => head.metadataResults);
		const parallelMetadataSources = parallelRouteMetadata.flatMap((head) => head.metadataSources);
		const primaryPageHasTitle = pageMetadata != null && pageMetadata.title !== void 0;
		const metadataEntries = [
			...layoutMetadataResults.filter(isPresent$1).map((entry) => ({ metadata: entry })),
			...pageMetadata ? [{
				isPage: true,
				metadata: pageMetadata
			}] : [],
			...parallelMetadataResults.filter(isPresent$1).map((entry) => ({
				contributesTitle: !primaryPageHasTitle,
				metadata: entry
			}))
		];
		const resolvedMetadataBase = metadataEntries.length > 0 ? mergeMetadataEntries(metadataEntries) : null;
		const metadataSources = createMetadataSources(layoutMetadataResults, routeSegments, layoutSourcePositions, pageMetadata, Boolean(options.pageModule));
		metadataSources.push(...parallelMetadataSources);
		return finalizeAppPageMetadata(resolvedMetadataBase, metadataSources, options);
	});
	const viewport = Promise.all([
		layoutViewportPromise,
		pageViewportPromise,
		parallelRouteViewportPromise
	]).then(([layoutViewportResults, pageViewport, parallelRouteViewports]) => mergeViewport([
		...layoutViewportResults.filter(isPresent$1),
		...pageViewport ? [pageViewport] : [],
		...parallelRouteViewports.flat().filter(isPresent$1)
	]));
	metadata.catch(() => null);
	viewport.catch(() => null);
	return {
		hasDynamicMetadata,
		hasSearchParams,
		metadata,
		pageSearchParams,
		viewport
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/app-router-scroll.js
var AppRouterScrollTarget = /* @__PURE__ */ registerClientReference(() => {
	throw new Error("Unexpectedly client reference export 'AppRouterScrollTarget' is called on server");
}, "0604f93d3a06", "AppRouterScrollTarget");
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/default-not-found.js
/**
* Ported from Next.js's built-in default not-found component:
*   https://github.com/vercel/next.js/blob/canary/packages/next/src/client/components/builtin/not-found.tsx
*   https://github.com/vercel/next.js/blob/canary/packages/next/src/client/components/http-access-fallback/error-fallback.tsx
*
* Rendered when an App Router request resolves to a 404 and the user has not
* supplied their own `app/not-found.tsx` (or `app/global-not-found.tsx`).
* Matches Next.js's `HTTPAccessErrorFallback` exactly: a centered 404 / message
* pair with minified theme CSS and dark-mode media query.
*
* The message string `"This page could not be found."` (note the trailing
* period) is the canonical body asserted by Next.js's deploy suite
* (`test/e2e/app-dir/prefetching-not-found/prefetching-not-found.test.ts`,
* `test/e2e/basepath/error-pages.test.ts`).
*/
var styles = {
	error: {
		fontFamily: "system-ui,\"Segoe UI\",Roboto,Helvetica,Arial,sans-serif,\"Apple Color Emoji\",\"Segoe UI Emoji\"",
		height: "100vh",
		textAlign: "center",
		display: "flex",
		flexDirection: "column",
		alignItems: "center",
		justifyContent: "center"
	},
	desc: { display: "inline-block" },
	h1: {
		display: "inline-block",
		margin: "0 20px 0 0",
		padding: "0 23px 0 0",
		fontSize: 24,
		fontWeight: 500,
		verticalAlign: "top",
		lineHeight: "49px"
	},
	h2: {
		fontSize: 14,
		fontWeight: 400,
		lineHeight: "49px",
		margin: 0
	}
};
var STATUS = 404;
var MESSAGE = "This page could not be found.";
/**
* Mirrors `<HTTPAccessErrorFallback status={404} message="This page could not be found." />`
* from Next.js. Kept in sync with the upstream component's structure so HTML
* snapshot diffs between Next.js and vinext stay minimal.
*/
function DefaultNotFound() {
	return import_react_react_server.createElement(import_react_react_server.Fragment, null, import_react_react_server.createElement("title", null, `${STATUS}: ${MESSAGE}`), import_react_react_server.createElement("div", { style: styles.error }, import_react_react_server.createElement("div", null, import_react_react_server.createElement("style", { dangerouslySetInnerHTML: { __html: "body{color:#000;background:#fff;margin:0}.next-error-h1{border-right:1px solid rgba(0,0,0,.3)}@media (prefers-color-scheme:dark){body{color:#fff;background:#000}.next-error-h1{border-right:1px solid rgba(255,255,255,.3)}}" } }), import_react_react_server.createElement("h1", {
		className: "next-error-h1",
		style: styles.h1
	}, STATUS), import_react_react_server.createElement("div", { style: styles.desc }, import_react_react_server.createElement("h2", { style: styles.h2 }, MESSAGE)))));
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/slot.js
var BfcacheSegmentBoundary = /* @__PURE__ */ registerClientReference(() => {
	throw new Error("Unexpectedly client reference export 'BfcacheSegmentBoundary' is called on server");
}, "9d9ddb30364a", "BfcacheSegmentBoundary");
var Children = /* @__PURE__ */ registerClientReference(() => {
	throw new Error("Unexpectedly client reference export 'Children' is called on server");
}, "9d9ddb30364a", "Children");
var ParallelSlot = /* @__PURE__ */ registerClientReference(() => {
	throw new Error("Unexpectedly client reference export 'ParallelSlot' is called on server");
}, "9d9ddb30364a", "ParallelSlot");
var Slot = /* @__PURE__ */ registerClientReference(() => {
	throw new Error("Unexpectedly client reference export 'Slot' is called on server");
}, "9d9ddb30364a", "Slot");
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/streamed-icons.js
var StreamedIconsInsertion = /* @__PURE__ */ registerClientReference(() => {
	throw new Error("Unexpectedly client reference export 'StreamedIconsInsertion' is called on server");
}, "de80fbf070f4", "StreamedIconsInsertion");
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/internal/app-page-props-cache-key.js
var APP_PAGE_PROPS_CACHE_KEY_MARKER = Symbol.for("vinext.appPagePropsCacheKeyMarker");
function markAppPagePropsForUseCache(props) {
	Object.defineProperty(props, APP_PAGE_PROPS_CACHE_KEY_MARKER, {
		configurable: false,
		enumerable: false,
		value: true,
		writable: false
	});
	return props;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-search-params-observation.js
function markAppPageSearchParamsAccess(markDynamic) {
	throwIfStaticGenerationAccessError();
	throwIfInsideCacheScope("searchParams");
	if (markDynamic) markDynamicUsage();
	markRenderRequestApiUsage("searchParams");
}
function createAppPageSearchParamsObserver(options = {}) {
	return { observeParamAccess() {
		markAppPageSearchParamsAccess(options.markDynamic !== false);
	} };
}
function makeObservedAppPageSearchParamsThenable(pageSearchParams, options = {}) {
	const observer = createAppPageSearchParamsObserver(options);
	if (options.observeReactPromiseStatus === true) return makeThenableParams(pageSearchParams, {
		...observer,
		observeReactPromiseStatus: true
	});
	return makeThenableParams(pageSearchParams, observer);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-probe.js
var DEFAULT_SUBTREE_PROBE_MAX_DEPTH = 32;
var DEFAULT_SUBTREE_PROBE_MAX_NODES = 1e3;
var REACT_FORWARD_REF_TYPE = Symbol.for("react.forward_ref");
var REACT_LAZY_TYPE = Symbol.for("react.lazy");
var REACT_MEMO_TYPE = Symbol.for("react.memo");
var REACT_CLIENT_REFERENCE_TYPE = Symbol.for("react.client.reference");
var AppPageSubtreeProbeLimitError = class extends Error {
	constructor(message) {
		super(message);
		this.name = "AppPageSubtreeProbeLimitError";
	}
};
var AppPageSubtreeProbeUnsupportedIterableError = class extends Error {
	constructor() {
		super("App page layout subtree probe cannot safely inspect iterable children");
		this.name = "AppPageSubtreeProbeUnsupportedIterableError";
	}
};
function isIterable(value) {
	return Boolean(value && typeof value !== "string" && typeof value === "object" && Symbol.iterator in value && typeof value[Symbol.iterator] === "function");
}
function isProbeReactElement(value) {
	return (0, import_react_react_server.isValidElement)(value);
}
function isObjectLike(value) {
	return (typeof value === "object" || typeof value === "function") && value !== null;
}
function isUnknownFunction(value) {
	return typeof value === "function";
}
function isReactClientReference(value) {
	return isObjectLike(value) && Reflect.get(value, "$$typeof") === REACT_CLIENT_REFERENCE_TYPE;
}
function readReactMemoType(value) {
	if (!isObjectLike(value) || Reflect.get(value, "$$typeof") !== REACT_MEMO_TYPE) return null;
	return { innerType: Reflect.get(value, "type") };
}
function readReactLazyType(value) {
	if (!isObjectLike(value) || Reflect.get(value, "$$typeof") !== REACT_LAZY_TYPE) return null;
	const init = Reflect.get(value, "_init");
	if (!isUnknownFunction(init)) return null;
	return {
		init,
		payload: Reflect.get(value, "_payload")
	};
}
function readReactForwardRefRender(value) {
	if (!isObjectLike(value) || Reflect.get(value, "$$typeof") !== REACT_FORWARD_REF_TYPE) return null;
	const render = Reflect.get(value, "render");
	return isUnknownFunction(render) ? render : null;
}
async function resolveReactLazyType(lazyType) {
	try {
		return lazyType.init(lazyType.payload);
	} catch (error) {
		if (!isPromiseLike(error)) throw error;
		await error;
		return lazyType.init(lazyType.payload);
	}
}
/**
* Invokes server-component children returned by a layout probe so per-layout
* skip eligibility observes data dependencies created below the layout's
* immediate function body. The real RSC render remains authoritative; probe
* failures only make static-layout skip fall back to render-and-send.
*/
async function probeReactServerSubtree(node, options = {}) {
	const maxDepth = options.maxDepth ?? DEFAULT_SUBTREE_PROBE_MAX_DEPTH;
	const maxNodes = options.maxNodes ?? DEFAULT_SUBTREE_PROBE_MAX_NODES;
	let visitedNodes = 0;
	const enterProbeNode = (depth) => {
		if (depth > maxDepth) throw new AppPageSubtreeProbeLimitError("App page layout subtree probe exceeded max depth");
		visitedNodes += 1;
		if (visitedNodes > maxNodes) throw new AppPageSubtreeProbeLimitError("App page layout subtree probe exceeded max nodes");
	};
	const renderElementType = async (type, props, depth, wrapperDepth = 0) => {
		if (wrapperDepth > maxDepth) throw new AppPageSubtreeProbeLimitError("App page layout subtree probe exceeded max depth");
		if (isReactClientReference(type)) return false;
		if (isUnknownFunction(type)) {
			await visit(type(props), depth + 1);
			return true;
		}
		const memoType = readReactMemoType(type);
		if (memoType) return renderElementType(memoType.innerType, props, depth, wrapperDepth + 1);
		const lazyType = readReactLazyType(type);
		if (lazyType) return renderElementType(await resolveReactLazyType(lazyType), props, depth, wrapperDepth + 1);
		const forwardRefRender = readReactForwardRefRender(type);
		if (forwardRefRender) {
			await visit(forwardRefRender(props, null), depth + 1);
			return true;
		}
		return false;
	};
	const visit = async (value, depth) => {
		enterProbeNode(depth);
		if (value == null || typeof value === "boolean" || typeof value === "number") return;
		if (typeof value === "string" || typeof value === "bigint") return;
		if (isPromiseLike(value)) {
			await visit(await value, depth);
			return;
		}
		if (Array.isArray(value)) {
			for (const child of value) await visit(child, depth + 1);
			return;
		}
		if (isIterable(value) && !isProbeReactElement(value)) throw new AppPageSubtreeProbeUnsupportedIterableError();
		if (!isProbeReactElement(value)) return;
		if (value.type === import_react_react_server.Fragment || typeof value.type === "string") {
			await visit(value.props.children, depth + 1);
			return;
		}
		if (await renderElementType(value.type, value.props, depth)) return;
		await visit(value.props.children, depth + 1);
	};
	await visit(node, 0);
}
async function probeReactServerSubtreeForDynamicUsage(node) {
	try {
		await probeReactServerSubtree(node);
	} catch (error) {
		if (isNextRouterError(error)) return;
		throw error;
	}
}
/**
* Build a probePage() invocation for the App Router request lifecycle.
*
* The generated RSC entry calls this once per request after route matching to
* eagerly invoke the page component. Surfacing redirect()/notFound() throws
* here lets the probe lifecycle turn them into proper HTTP responses before
* RSC streaming begins (see `probeAppPageBeforeRender`).
*
* The helper exists to keep the generated entry thin (a single delegation
* call) and to make the search-params wiring directly unit-testable. A bug
* here previously slipped through because the entry hand-rolled the call and
* read a non-existent key off `collectAppPageSearchParams`'s return value
* (see https://github.com/cloudflare/vinext/issues/1235).
*
* Returns `null` when the route has no page component (eg. interception-only
* routes), matching the caller contract on `probePage`.
*/
function probeAppPage(options) {
	const { pageComponent, asyncRouteParams, searchParams } = options;
	if (typeof pageComponent !== "function") return null;
	const { pageSearchParams } = collectAppPageSearchParams(searchParams);
	const result = pageComponent(markAppPagePropsForUseCache({
		params: asyncRouteParams,
		searchParams: makeObservedAppPageSearchParamsThenable(pageSearchParams, { observeReactPromiseStatus: true })
	}));
	if (isPromiseLike(result)) return result.then(async (resolved) => {
		await probeReactServerSubtreeForDynamicUsage(resolved);
		return resolved;
	});
	if ((0, import_react_react_server.isValidElement)(result) || Array.isArray(result)) return probeReactServerSubtreeForDynamicUsage(result).then(() => result);
	return result;
}
/**
* Fan out the per-request page probes for the App Router dispatch lifecycle.
*
* A single request can render more than one page component: the matched page,
* each active parallel-route slot page, and an interception page when one
* matches. Each must be probed so searchParams access anywhere in the rendered
* tree bails the request out of the query-invariant static cache.
*
* Extracted out of the generated RSC entry so the fan-out is directly
* unit-testable and the entry stays codegen glue (see AGENTS.md "Generated
* Entry Modules Should Stay Thin"). Returns a list of resolved promises so the
* caller can `Promise.all` them.
*
* The fan-out is scoped to the page components that render for this request:
*
* - **Interception override:** when an interception matches it replaces the
*   page of the slot named by `intercept.slotKey` (the element builder sets
*   `overrides[slotKey].pageModule` to the interception page, which wins over
*   `slot.page` in `app-page-route-wiring.tsx`). We probe the interception page
*   in place of that slot's own page rather than probing both — probing the
*   overridden slot page would mark an otherwise-static request dynamic for a
*   component that never renders.
* - **Non-overridden slots:** `slot.page?.default` is exactly what renders.
*   `app-page-route-wiring.tsx` resolves a slot to `overrideOrPageComponent ??
*   defaultComponent`, so whenever a slot has a `page.tsx` that page renders.
*   When a slot has only a `default.tsx` (including the soft-nav case at
*   `app-page-route-wiring.tsx:741` that skips an already-mounted slot), there
*   is no `slot.page?.default`, so `probeAppPage` short-circuits to `null` and
*   probes nothing — a no-op, not an over-bail.
*
* Interception only fires for RSC navigations (`resolveAppPageInterceptState`
* returns `kind: "none"` when `!isRscRequest`, app-page-request.ts:324), so the
* interception handling here is gated on `isRscRequest`. For non-RSC (HTML)
* requests the matched route renders normally, so we probe every slot's own
* page and skip the interception probe entirely. The remaining "source-route"
* interception case (where a *different* route renders, app-page-request.ts:342)
* never reaches this probe: `dispatchAppPage` returns the intercepted response
* before calling `probePage`, so by the time this runs any matched interception
* is the current-route override case above.
*
* A `default.tsx` that itself awaits `searchParams` is not probed here, but the
* real render still observes that access and skips the query-invariant cache
* write (the same loading.tsx backstop), so this cannot under-bail.
*/
function buildAppPageProbes(options) {
	const { route, pageComponent, asyncRouteParams, searchParams, matchedParams } = options;
	const intercept = options.isRscRequest ? options.intercept : null;
	const probes = [probeAppPage({
		pageComponent,
		asyncRouteParams,
		searchParams
	})];
	const overriddenSlotKey = intercept?.slotKey ?? null;
	for (const [slotKey, slot] of Object.entries(route.slots ?? {})) {
		if (overriddenSlotKey !== null && slotKey === overriddenSlotKey) continue;
		if (slot?.loading?.default || slot?.loadings?.some((loading) => loading?.default)) continue;
		probes.push(probeAppPage({
			pageComponent: slot?.page?.default,
			asyncRouteParams,
			searchParams
		}));
	}
	const interceptedSlot = intercept?.slotKey ? route.slots?.[intercept.slotKey] : null;
	const interceptedSlotHasRootLoading = Boolean(interceptedSlot?.loading?.default || interceptedSlot?.loadings?.some((loading, index) => loading?.default && interceptedSlot.loadingTreePositions?.[index] === 0));
	const interceptHasLoadingBoundary = Boolean(intercept?.interceptLoadings?.some((loading) => loading?.default) || interceptedSlotHasRootLoading);
	if (intercept && !interceptHasLoadingBoundary) probes.push(probeAppPage({
		pageComponent: intercept.page?.default,
		asyncRouteParams: options.makeThenableParams(intercept.matchedParams ?? matchedParams),
		searchParams
	}));
	return probes.map((probe) => Promise.resolve(probe));
}
async function probeAppPageBeforeRender(options) {
	let layoutFlags = {};
	if (options.skipProbes) return {
		response: null,
		layoutFlags
	};
	if (options.layoutCount > 0) {
		const layoutProbeResult = await probeAppPageLayouts({
			layoutCount: options.layoutCount,
			async onLayoutError(layoutError, layoutIndex) {
				const specialError = options.resolveSpecialError(layoutError);
				if (!specialError) return null;
				return options.renderLayoutSpecialError(specialError, layoutIndex);
			},
			probeLayoutAt: options.probeLayoutAt,
			runWithSuppressedHookWarning(probe) {
				return options.runWithSuppressedHookWarning(probe);
			},
			classification: options.classification
		});
		layoutFlags = layoutProbeResult.layoutFlags;
		if (layoutProbeResult.response) return {
			response: layoutProbeResult.response,
			layoutFlags
		};
	}
	if (options.hasLoadingBoundary || options.probePageBeforeRender === false) return {
		response: null,
		layoutFlags
	};
	return {
		response: await probeAppPageComponent({
			awaitAsyncResult: true,
			async onError(pageError) {
				const specialError = options.resolveSpecialError(pageError);
				if (specialError) return options.renderPageSpecialError(specialError);
				return null;
			},
			probePage: options.probePage,
			runWithSuppressedHookWarning(probe) {
				return options.runWithSuppressedHookWarning(probe);
			}
		}),
		layoutFlags
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-segment-state.js
var APP_PAGE_SEGMENT_KEY = "__PAGE__";
function isDynamicSegment$1(segment) {
	return segment.startsWith("[") && segment.endsWith("]") && !segment.includes(".");
}
function isAppPageRouteGroupSegment(segment) {
	return segment.startsWith("(") && segment.endsWith(")");
}
function formatParamSegmentValue(value) {
	if (Array.isArray(value)) return value.join("/");
	return value;
}
function readSegmentParam(segment) {
	if (isOptionalCatchAllSegment(segment)) return {
		name: segment.slice(5, -2),
		type: "oc"
	};
	if (isCatchAllSegment(segment)) return {
		name: segment.slice(4, -1),
		type: "c"
	};
	if (isDynamicSegment$1(segment)) return {
		name: segment.slice(1, -1),
		type: "d"
	};
	return null;
}
function formatSegmentStateParamValue(param, params, fallbackSegment) {
	const value = params[param.name];
	if (param.type === "oc" && (value === void 0 || Array.isArray(value) && value.length === 0)) return "";
	return formatParamSegmentValue(value) ?? fallbackSegment;
}
function resolveSingleSegmentStateKey(segment, params) {
	const param = readSegmentParam(segment);
	if (!param) return segment;
	return `${param.name}|${formatSegmentStateParamValue(param, params, segment)}|${param.type}`;
}
function resolveAppPageChildSegments(routeSegments, treePosition, params) {
	const rawSegments = routeSegments.slice(treePosition);
	const resolvedSegments = [];
	for (const segment of rawSegments) {
		if (isOptionalCatchAllSegment(segment)) {
			const paramValue = params[segment.slice(5, -2)];
			if (Array.isArray(paramValue) && paramValue.length === 0) continue;
			const resolvedValue = formatParamSegmentValue(paramValue);
			if (resolvedValue !== void 0) resolvedSegments.push(resolvedValue);
			continue;
		}
		if (isCatchAllSegment(segment)) {
			const paramName = segment.slice(4, -1);
			resolvedSegments.push(formatParamSegmentValue(params[paramName]) ?? segment);
			continue;
		}
		if (isDynamicSegment$1(segment)) {
			const paramName = segment.slice(1, -1);
			resolvedSegments.push(formatParamSegmentValue(params[paramName]) ?? segment);
			continue;
		}
		resolvedSegments.push(segment);
	}
	resolvedSegments.push(APP_PAGE_SEGMENT_KEY);
	return resolvedSegments;
}
function resolveAppPageSegmentStateKey(routeSegments, treePosition, params) {
	for (const segment of routeSegments.slice(treePosition)) if (!isAppPageRouteGroupSegment(segment)) return resolveSingleSegmentStateKey(segment, params);
	return "";
}
function resolveAppPageSemanticSegmentStateKey(semanticSegment, params) {
	const { marker, segment } = semanticSegment;
	if (isAppPageRouteGroupSegment(segment)) return segment;
	const stateKey = resolveSingleSegmentStateKey(segment, params);
	return marker ? JSON.stringify([marker, stateKey]) : stateKey;
}
function resolveAppPageRouteStateKey(routeSegments, params) {
	const statePath = [];
	for (const segment of routeSegments) if (!isAppPageRouteGroupSegment(segment)) statePath.push(resolveSingleSegmentStateKey(segment, params));
	return statePath.length > 0 ? JSON.stringify(statePath) : "";
}
function resolveAppPagePatternStateKey(patternParts, params) {
	return resolveAppPageRouteStateKey(patternParts.map((part) => {
		if (!part.startsWith(":")) return part;
		if (part.endsWith("*")) return `[[...${part.slice(1, -1)}]]`;
		if (part.endsWith("+")) return `[...${part.slice(1, -1)}]`;
		return `[${part.slice(1)}]`;
	}), params);
}
function resolveAppPageTemplateStateKey(routeSegments, treePosition, params) {
	const end = treePosition < routeSegments.length ? treePosition + 1 : routeSegments.length;
	const statePath = routeSegments.slice(0, end).map((segment) => resolveSingleSegmentStateKey(segment, params));
	return statePath.length > 0 ? JSON.stringify(statePath) : "";
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/bfcache-identity.js
var NESTED_BFCACHE_SLOT_SEGMENT_PREFIX = "slot:\0vinext_bfcache_segment_";
function createNestedBfcacheSlotParentPrefix(parentSlotId) {
	const encodedParent = encodeURIComponent(parentSlotId);
	return `${NESTED_BFCACHE_SLOT_SEGMENT_PREFIX}${encodedParent.length}_${encodedParent}_`;
}
function createNestedBfcacheSlotSegmentId(parentSlotId, level) {
	return `${createNestedBfcacheSlotParentPrefix(parentSlotId)}${level}:/`;
}
function deriveBfcacheSegmentIdentity(descriptor) {
	switch (descriptor.kind) {
		case "page":
		case "layout":
		case "template": return JSON.stringify([
			descriptor.kind,
			descriptor.graphId,
			descriptor.rootBoundaryId,
			descriptor.boundSegmentKey
		]);
		case "slot-shell": return JSON.stringify([
			"slot-shell",
			descriptor.slotGraphId,
			descriptor.ownerLayoutGraphId,
			descriptor.boundOwnerSegmentKey
		]);
		case "slot": return JSON.stringify([
			"slot",
			descriptor.slotGraphId,
			descriptor.ownerLayoutGraphId,
			descriptor.state,
			descriptor.activeRouteGraphId,
			descriptor.interceptionTargetRouteGraphId,
			descriptor.boundSegmentKey
		]);
		case "sibling-interception": return JSON.stringify([
			"sibling-interception",
			descriptor.sourceRouteGraphId,
			descriptor.interceptionGraphId,
			descriptor.rootBoundaryId,
			descriptor.boundSegmentKey,
			descriptor.sourceBoundSegmentKey
		]);
	}
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-segment-plan.js
function requireGraphSequenceId(ids, index, kind) {
	const id = ids[index];
	if (id === void 0) throw new Error(`[vinext] Missing App Router graph ${kind} id at index ${index}`);
	return id;
}
/**
* Serialise the resolved route/render model into the BFCache identities and
* per-slot reset keys the browser treats as opaque. Route matching owns the
* semantics — which segment intercepts, which params bind it — so this layer
* only binds keys and derives identities from graph ids.
*/
function createAppPageSegmentPlan(options) {
	const identities = {};
	const graphIds = options.route.ids;
	const rootBoundaryId = graphIds ? graphIds.rootBoundary : options.rootLayoutTreePath;
	const routeResetKey = resolveAppPageRouteStateKey(options.routeSegments, options.matchedParams);
	const routePrefixStateKeys = /* @__PURE__ */ new Map();
	const resolveRoutePrefixStateKey = (treePosition) => {
		const cached = routePrefixStateKeys.get(treePosition);
		if (cached !== void 0) return cached;
		const stateKey = resolveAppPageRouteStateKey(options.routeSegments.slice(0, treePosition), options.matchedParams);
		routePrefixStateKeys.set(treePosition, stateKey);
		return stateKey;
	};
	for (const [index, layoutEntry] of options.layoutEntries.entries()) identities[layoutEntry.id] = deriveBfcacheSegmentIdentity({
		boundSegmentKey: resolveRoutePrefixStateKey(layoutEntry.treePosition),
		graphId: graphIds ? requireGraphSequenceId(graphIds.layouts, index, "layout") : layoutEntry.id,
		kind: "layout",
		rootBoundaryId
	});
	for (const [index, templateEntry] of options.templateEntries.entries()) identities[templateEntry.id] = deriveBfcacheSegmentIdentity({
		boundSegmentKey: resolveAppPageTemplateStateKey(options.routeSegments, templateEntry.treePosition, options.matchedParams),
		graphId: graphIds ? requireGraphSequenceId(graphIds.templates, index, "template") : templateEntry.id,
		kind: "template",
		rootBoundaryId
	});
	const slotBindingsById = new Map(options.slotBindings.map((binding) => [binding.slotId, binding]));
	const layoutIndicesById = new Map(options.layoutEntries.map((layoutEntry, index) => [layoutEntry.id, index]));
	const resolveOwnerLayoutGraphId = (ownerLayoutId) => {
		if (ownerLayoutId === null || !graphIds) return ownerLayoutId;
		const ownerLayoutIndex = layoutIndicesById.get(ownerLayoutId);
		if (ownerLayoutIndex === void 0) throw new Error(`[vinext] Missing App Router owner layout for ${ownerLayoutId}`);
		return requireGraphSequenceId(graphIds.layouts, ownerLayoutIndex, "layout");
	};
	const deriveSlotIdentity = (slotGraphId, slotId, slotBinding, boundSegmentKey, includeInterceptionTarget = true) => {
		const isIntercepted = includeInterceptionTarget && options.interception?.slotId === slotId;
		const interceptionTargetRouteGraphId = isIntercepted ? graphIds ? options.semanticInterceptionTargetRouteId : slotBinding.activeRouteId ?? options.interception?.targetRouteId ?? null : null;
		if (isIntercepted && graphIds && interceptionTargetRouteGraphId === null) return null;
		return deriveBfcacheSegmentIdentity({
			activeRouteGraphId: slotBinding.state !== "active" ? null : isIntercepted ? interceptionTargetRouteGraphId : null,
			boundSegmentKey,
			interceptionTargetRouteGraphId,
			kind: "slot",
			ownerLayoutGraphId: resolveOwnerLayoutGraphId(slotBinding.ownerLayoutId),
			slotGraphId,
			state: slotBinding.state
		});
	};
	const pageBinding = options.route.childrenSlot ? slotBindingsById.get(options.pageElementId) : void 0;
	if (options.route.childrenSlot && !pageBinding) throw new Error(`[vinext] Missing App Router slot binding for ${options.pageElementId}`);
	if (options.semanticPageIdentity !== void 0) {
		if (options.semanticPageIdentity !== null) identities[options.pageElementId] = deriveBfcacheSegmentIdentity({
			boundSegmentKey: options.semanticPageIdentity.boundSegmentKey,
			interceptionGraphId: options.semanticPageIdentity.interceptionGraphId,
			kind: "sibling-interception",
			rootBoundaryId,
			sourceBoundSegmentKey: options.semanticPageIdentity.sourceBoundSegmentKey,
			sourceRouteGraphId: options.semanticPageIdentity.sourceRouteGraphId
		});
	} else if (pageBinding) {
		const identity = deriveSlotIdentity(options.route.childrenSlot.id, options.pageElementId, pageBinding, routeResetKey);
		if (identity !== null) identities[options.pageElementId] = identity;
	} else {
		const pageGraphId = graphIds ? graphIds.page ?? graphIds.route : options.pageElementId;
		identities[options.pageElementId] = deriveBfcacheSegmentIdentity({
			boundSegmentKey: routeResetKey,
			graphId: pageGraphId,
			kind: "page",
			rootBoundaryId
		});
	}
	const slots = Object.entries(options.route.slots ?? {}).map(([slotKey, slot]) => {
		const targetIndex = slot.layoutIndex >= 0 ? slot.layoutIndex : options.layoutEntries.length - 1;
		const targetTreePosition = options.layoutEntries[targetIndex]?.treePosition ?? 0;
		const ownerTreePosition = slot.ownerTreePosition ?? targetTreePosition;
		const treePath = options.layoutEntries[targetIndex]?.treePath ?? "/";
		const slotId = AppElementsWire.encodeSlotId(slot.name, treePath);
		const slotBinding = slotBindingsById.get(slotId);
		if (!slotBinding) throw new Error(`[vinext] Missing App Router slot binding for ${slotId}`);
		const slotOverride = options.resolveSlotOverride(slotKey, slot.name);
		const params = slotOverride?.params ?? options.matchedParams;
		const routeSegments = slotOverride?.routeSegments ?? slot.routeSegments ?? [];
		const branchSegments = slotOverride?.branchSegments ?? routeSegments;
		const resetKey = resolveAppPageRouteStateKey(routeSegments, params);
		const ownerStateKey = resolveRoutePrefixStateKey(ownerTreePosition);
		const bindOwnerState = (segmentKey) => ownerStateKey ? JSON.stringify([ownerStateKey, segmentKey]) : segmentKey;
		const branchSegmentPositions = branchSegments.flatMap((segment, treePosition) => segment.startsWith("@") ? [] : [treePosition]);
		const overrideIdentitySegments = slotOverride?.identitySegments ?? null;
		const identitySegmentsAlignWithBranch = overrideIdentitySegments === null || overrideIdentitySegments.length === branchSegmentPositions.length;
		const semanticSegments = [];
		if (identitySegmentsAlignWithBranch) {
			const boundSegmentKeys = [];
			for (const [index, treePosition] of branchSegmentPositions.entries()) {
				const semanticSegment = overrideIdentitySegments?.[index] ?? {
					marker: null,
					paramSource: "slot",
					segment: branchSegments[treePosition]
				};
				boundSegmentKeys.push(resolveAppPageSemanticSegmentStateKey(semanticSegment, semanticSegment.paramSource === "route" ? options.matchedParams : params));
				semanticSegments.push({
					identityKey: JSON.stringify(boundSegmentKeys),
					stateKey: boundSegmentKeys[index],
					treePosition
				});
			}
		}
		const includedInPayload = options.includeSlot(ownerTreePosition, targetTreePosition);
		const graphId = graphIds ? graphIds.slots[slotKey] : slot.id ?? slotId;
		if (graphId === void 0) throw new Error(`[vinext] Missing App Router graph slot id for ${slotKey}`);
		const nestedBfcacheSegmentCandidates = !identitySegmentsAlignWithBranch ? [{
			identityKey: resetKey,
			stateKey: resetKey || slotBinding.state,
			treePosition: null
		}] : semanticSegments.length > 0 ? semanticSegments : [{
			identityKey: "",
			stateKey: slotBinding.state,
			treePosition: 0
		}];
		const nestedBfcacheSegments = [];
		if (includedInPayload) {
			if (identitySegmentsAlignWithBranch) identities[slotId] = deriveBfcacheSegmentIdentity({
				boundOwnerSegmentKey: ownerStateKey,
				kind: "slot-shell",
				ownerLayoutGraphId: resolveOwnerLayoutGraphId(slotBinding.ownerLayoutId),
				slotGraphId: graphId
			});
			for (const [level, segment] of nestedBfcacheSegmentCandidates.entries()) {
				const id = createNestedBfcacheSlotSegmentId(slotId, level + 1);
				if (identitySegmentsAlignWithBranch) {
					const nestedIdentity = deriveSlotIdentity(graphId, slotId, slotBinding, bindOwnerState(segment.identityKey), false);
					if (nestedIdentity !== null) identities[id] = nestedIdentity;
				}
				nestedBfcacheSegments.push({
					id,
					stateKey: segment.stateKey,
					treePosition: segment.treePosition
				});
			}
		}
		return Object.freeze({
			branchSegments,
			includedInPayload,
			key: slotKey,
			nestedBfcacheSegments: Object.freeze(nestedBfcacheSegments),
			ownerTreePosition,
			params,
			resetKey,
			routeSegments,
			slot,
			slotId,
			slotOverride,
			targetIndex
		});
	});
	return Object.freeze({
		bfcacheSegmentIdentities: Object.freeze(identities),
		routeResetKey,
		slots: Object.freeze(slots)
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-route-wiring.js
var APP_PAGE_LAYOUT_PROBE_CHILD = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(import_react_react_server.Fragment, {});
var DEFAULT_GLOBAL_ERROR_COMPONENT$1 = default_global_error_default;
var DEFAULT_NOT_FOUND_COMPONENT = DefaultNotFound;
function resolveSlotLayoutParams(routeSegments, treePosition, params) {
	return resolveAppPageBranchParams(routeSegments, treePosition, params);
}
function getDefaultExport$1(module) {
	return module?.default ?? null;
}
function getErrorBoundaryExport(module) {
	return module?.default ?? null;
}
function createAppPageTreePath(routeSegments, treePosition) {
	const treePathSegments = routeSegments?.slice(0, treePosition) ?? [];
	if (treePathSegments.length === 0) return "/";
	return `/${treePathSegments.join("/")}`;
}
function readFiniteRevalidateSeconds(module) {
	const revalidate = module?.revalidate;
	return typeof revalidate === "number" && Number.isFinite(revalidate) && revalidate > 0 ? revalidate : null;
}
function recordLayoutSkipObservationScope(options) {
	options.layoutParamAccess?.recordLayoutParamScope(options.layoutId, resolveAppPageSegmentParamScopeKeys(options.routeSegments, options.treePosition));
	const revalidateSeconds = readFiniteRevalidateSeconds(options.layoutModule);
	if (revalidateSeconds !== null) options.layoutParamAccess?.recordLayoutFiniteRevalidate(options.layoutId, revalidateSeconds);
}
function probeAppPageLayoutWithTracking(options) {
	const treePosition = options.route.layoutTreePositions?.[options.layoutIndex] ?? 0;
	const treePath = createAppPageTreePath(options.route.routeSegments, treePosition);
	const layoutId = AppElementsWire.encodeLayoutId(treePath);
	const probe = () => {
		const layoutModule = options.route.layouts[options.layoutIndex];
		const LayoutComponent = getDefaultExport$1(layoutModule);
		if (!LayoutComponent) return null;
		recordLayoutSkipObservationScope({
			layoutId,
			layoutModule,
			layoutParamAccess: options.layoutParamAccess,
			routeSegments: options.route.routeSegments,
			treePosition
		});
		const layoutParams = resolveAppPageSegmentParams(options.route.routeSegments, treePosition, options.matchedParams);
		return probeReactServerSubtree(/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(LayoutComponent, {
			params: options.makeThenableParams(layoutParams, options.layoutParamAccess?.createThenableParamsObserver(layoutId)),
			children: APP_PAGE_LAYOUT_PROBE_CHILD
		}));
	};
	return options.layoutParamAccess ? options.layoutParamAccess.runLayoutProbe(layoutId, probe) : probe();
}
function createAppPageLayoutEntries(route) {
	return route.layouts.map((layoutModule, index) => {
		const treePosition = route.layoutTreePositions?.[index] ?? 0;
		const treePath = createAppPageTreePath(route.routeSegments, treePosition);
		return {
			errorModule: route.errorTreePositions ? null : route.errors?.[index] ?? null,
			forbiddenModule: route.forbiddens?.[index] ?? null,
			id: AppElementsWire.encodeLayoutId(treePath),
			layoutModule,
			notFoundModule: route.notFounds?.[index] ?? null,
			unauthorizedModule: route.unauthorizeds?.[index] ?? null,
			treePath,
			treePosition
		};
	});
}
function createAppPageTemplateEntries(route) {
	return (route.templates ?? []).map((templateModule, index) => {
		const treePosition = route.templateTreePositions?.[index] ?? 0;
		const treePath = createAppPageTreePath(route.routeSegments, treePosition);
		return {
			id: AppElementsWire.encodeTemplateId(treePath),
			templateModule,
			treePath,
			treePosition
		};
	});
}
function createAppPageSourcePage(routeSegments) {
	return `/${[...routeSegments ?? [], "page"].join("/")}`;
}
function resolveAppPageLayoutSegmentProviderSegments(routeSegments, treePosition, params) {
	const segments = resolveAppPageChildSegments(routeSegments, treePosition, params);
	return segments.at(-1) === "__PAGE__" ? segments.slice(0, -1) : segments;
}
function createAppPageErrorEntries(route) {
	return (route.errorPaths ?? route.errors ?? []).flatMap((errorModule, index) => {
		if (!errorModule) return [];
		const treePosition = route.errorTreePositions?.[index];
		if (treePosition === void 0) return [];
		return [{
			errorModule,
			treePosition
		}];
	});
}
function createAppPageLoadingEntries(route) {
	return (route.loadings ?? []).flatMap((loadingModule, index) => {
		if (!loadingModule) return [];
		const treePosition = route.loadingTreePositions?.[index];
		if (treePosition === void 0) return [];
		return [{
			loadingModule,
			treePosition
		}];
	});
}
function resolveAppPageLoadingModuleAtOrAbove(route, treePosition) {
	let nearest = null;
	for (const entry of createAppPageLoadingEntries(route)) if (entry.treePosition <= treePosition && getDefaultExport$1(entry.loadingModule) !== null && (nearest === null || entry.treePosition > nearest.treePosition)) nearest = entry;
	if (nearest?.loadingModule) return nearest.loadingModule;
	return getDefaultExport$1(route.loading) === null ? null : route.loading ?? null;
}
function getPrefetchLoadingEntry(route) {
	let rootEntry = null;
	let firstNestedEntry = null;
	for (const [index, loadingModule] of (route.loadings ?? []).entries()) {
		if (!getDefaultExport$1(loadingModule)) continue;
		const treePosition = route.loadingTreePositions?.[index];
		if (treePosition === void 0) continue;
		if (treePosition === 0) rootEntry ??= {
			loadingModule,
			treePosition
		};
		else if (firstNestedEntry === null || treePosition < firstNestedEntry.treePosition) firstNestedEntry = {
			loadingModule,
			treePosition
		};
	}
	if (firstNestedEntry) return firstNestedEntry;
	if (rootEntry) return rootEntry;
	return getDefaultExport$1(route.loading) ? {
		loadingModule: route.loading,
		treePosition: route.routeSegments?.length ?? 0
	} : null;
}
function createAppPageSlotLoadingEntries(slot, override) {
	const entries = [];
	const slotLoadingModules = (slot.loadings?.length ?? 0) > 0 ? slot.loadings : slot.loading ? [slot.loading] : [];
	const slotLoadingTreePositions = (slot.loadingTreePositions?.length ?? 0) > 0 ? slot.loadingTreePositions : [0];
	for (const [index, loadingModule] of slotLoadingModules.entries()) {
		const treePosition = slotLoadingTreePositions[index];
		if (!getDefaultExport$1(loadingModule) || treePosition === void 0) continue;
		if (override && treePosition !== 0) continue;
		entries.push({
			loadingModule,
			treePosition
		});
	}
	for (const [index, loadingModule] of (override?.loadingModules ?? []).entries()) {
		const treePosition = override?.loadingTreePositions?.[index];
		if (!getDefaultExport$1(loadingModule) || treePosition === void 0) continue;
		entries.push({
			loadingModule,
			treePosition
		});
	}
	return entries;
}
function getFirstLoadingEntry(entries) {
	return entries.reduce((first, entry) => first === null || entry.treePosition < first.treePosition ? entry : first, null);
}
function createAppPageParallelSlotEntries(layoutIndex, layoutEntries, route, getEffectiveSlotParams, resolveSlotOverride) {
	const parallelSlots = {};
	for (const [slotKey, slot] of Object.entries(route.slots ?? {})) {
		const slotName = slot.name;
		const targetIndex = slot.layoutIndex >= 0 ? slot.layoutIndex : layoutEntries.length - 1;
		if (targetIndex !== layoutIndex) continue;
		const slotId = resolveAppPageSlotId(slot, layoutEntries[targetIndex]?.treePath ?? "/");
		const slotParams = getEffectiveSlotParams(slotKey, slotName);
		const routeSegments = resolveSlotOverride(slotKey, slotName)?.routeSegments ?? slot.routeSegments;
		parallelSlots[slotName] = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(LayoutSegmentProvider, {
			providerId: slotId,
			segmentMap: { children: routeSegments ? resolveAppPageLayoutSegmentProviderSegments(routeSegments, 0, slotParams) : [] },
			children: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(Slot, { id: slotId })
		});
	}
	return Object.keys(parallelSlots).length > 0 ? parallelSlots : void 0;
}
function resolveAppPageSlotId(slot, treePath) {
	return AppElementsWire.encodeSlotId(slot.name, treePath);
}
function resolveAppPageChildrenSlotId(childrenSlot) {
	return AppElementsWire.encodeSlotId("children", childrenSlot.ownerTreePath);
}
function resolveAppPageSlotBindingState(slot, override) {
	if (getDefaultExport$1(override?.pageModule) ?? getDefaultExport$1(slot.page)) return "active";
	if (getDefaultExport$1(slot.default)) return "default";
	return "unmatched";
}
function createAppPageSlotBindings(route, layoutEntries, resolveSlotOverride, options) {
	const bindings = [];
	if (route.childrenSlot) {
		const ownerLayoutId = layoutEntries.find((layoutEntry) => layoutEntry.treePath === route.childrenSlot?.ownerTreePath)?.id;
		const slotId = resolveAppPageChildrenSlotId(route.childrenSlot);
		bindings.push({
			...route.childrenSlot.state === "active" ? { activeRouteId: options.routeId } : {},
			ownerLayoutId: ownerLayoutId ?? null,
			slotId,
			state: route.childrenSlot.state
		});
	}
	for (const [slotKey, slot] of Object.entries(route.slots ?? {})) {
		const layoutEntry = layoutEntries[slot.layoutIndex >= 0 ? slot.layoutIndex : layoutEntries.length - 1] ?? null;
		const ownerLayoutId = layoutEntry?.id ?? null;
		const override = resolveSlotOverride(slotKey, slot.name);
		const slotId = resolveAppPageSlotId(slot, layoutEntry?.treePath ?? "/");
		const state = resolveAppPageSlotBindingState(slot, override);
		const activeRouteId = state === "active" ? options.interception?.slotId === slotId ? options.interception.targetRouteId : AppElementsWire.encodeRouteId(options.routePath, null) : null;
		bindings.push({
			...activeRouteId !== null ? { activeRouteId } : {},
			ownerLayoutId,
			slotId,
			state
		});
	}
	return normalizeAppElementsSlotBindings(bindings, { layoutIds: layoutEntries.map((entry) => entry.id) });
}
function createAppPageRouteHead(metadata, viewport, pathname, metadataPlacement, trailingSlash) {
	return /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsxs)(import_jsx_runtime_react_server.Fragment, { children: [
		/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("meta", { charSet: "utf-8" }),
		metadata && metadataPlacement === "head" ? /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(MetadataHead, {
			metadata,
			pathname,
			trailingSlash
		}) : null,
		/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(ViewportHead, { viewport })
	] });
}
function hasStreamedIcons(metadata) {
	const icons = metadata.icons;
	if (!icons) return false;
	if (typeof icons === "string" || icons instanceof URL || Array.isArray(icons)) return !Array.isArray(icons) || icons.length > 0;
	if ("url" in icons) return true;
	return Boolean(icons.shortcut || icons.icon || icons.apple || icons.other);
}
function createStreamedIconKey(pathname, metadataHtml) {
	let hash = 2166136261;
	for (let index = 0; index < metadataHtml.length; index++) {
		hash ^= metadataHtml.charCodeAt(index);
		hash = Math.imul(hash, 16777619);
	}
	return `${pathname}:${(hash >>> 0).toString(36)}`;
}
var STREAMED_ICON_KEY_PLACEHOLDER = "vinext-pending-streamed-icon-key";
var REINSERT_STREAMED_ICONS_SCRIPT = `document.querySelectorAll('body link[rel="icon"], body link[rel="apple-touch-icon"]').forEach(el => document.head.appendChild(el));const a='data-vinext-streamed-icon',o=el=>{const m=el.getAttribute(a),i=m.lastIndexOf(':');return Number(m.slice(i+1))};[...document.querySelectorAll('link['+a+']')].sort((l,r)=>o(l)-o(r)).forEach(el=>document.head.appendChild(el))`;
function createAppPageRouteBodyMetadata(metadata, pathname, metadataPlacement, trailingSlash, scriptNonce) {
	if (!metadata || metadataPlacement !== "body") return null;
	const streamedIconKey = hasStreamedIcons(metadata) ? STREAMED_ICON_KEY_PLACEHOLDER : void 0;
	const renderedMetadataHtml = renderMetadataToHtml(metadata, pathname, {
		trailingSlash,
		streamedIconKey
	});
	const metadataKey = streamedIconKey ? createStreamedIconKey(pathname, renderedMetadataHtml) : "";
	return /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsxs)(import_jsx_runtime_react_server.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("div", {
		hidden: true,
		suppressHydrationWarning: true,
		dangerouslySetInnerHTML: { __html: (streamedIconKey ? renderedMetadataHtml.replaceAll(`<link data-vinext-streamed-icon="${STREAMED_ICON_KEY_PLACEHOLDER}:`, `<link data-vinext-streamed-icon="${escapeHtmlAttr(metadataKey)}:`) : renderedMetadataHtml) + createInlineScriptTag(REINSERT_STREAMED_ICONS_SCRIPT, scriptNonce) }
	}), /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(StreamedIconsInsertion, { metadataKey })] });
}
async function AppPageStreamingMetadata(props) {
	try {
		return createAppPageRouteBodyMetadata(await props.metadata, props.pathname, "body", props.trailingSlash, props.scriptNonce);
	} catch {
		return null;
	}
}
AppPageStreamingMetadata.displayName = "Vinext.StreamingMetadata";
async function AppPageMetadataOutlet(props) {
	await props.metadata;
	return null;
}
AppPageMetadataOutlet.displayName = "Vinext.MetadataOutlet";
function createAppPageStreamingMetadataOutlet(elementId, suspended = true) {
	if (!elementId) return null;
	const outlet = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(Slot, { id: elementId });
	return suspended ? /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(import_react_react_server.Suspense, {
		fallback: null,
		children: outlet
	}) : outlet;
}
function createAppPageStreamingMetadataBody(elementId) {
	if (!elementId) return null;
	return /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("div", {
		hidden: true,
		children: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(import_react_react_server.Suspense, {
			fallback: null,
			children: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(Slot, { id: elementId })
		})
	});
}
function buildAppPageElements(options) {
	const renderIdentity = options.renderIdentity;
	const interceptionContext = renderIdentity?.interceptionContext ?? options.interceptionContext ?? null;
	const renderMode = options.renderMode ?? "navigation";
	const routeSegments = options.route.routeSegments ?? [];
	const routeId = renderIdentity?.routeId ?? AppElementsWire.encodeRouteId(options.routePath, interceptionContext);
	const pageId = renderIdentity?.pageId ?? AppElementsWire.encodePageId(options.routePath, interceptionContext);
	const pageElementId = options.route.childrenSlot ? resolveAppPageChildrenSlotId(options.route.childrenSlot) : pageId;
	const streamingMetadataBodyId = options.streamingMetadata ? `__vinext_streaming_metadata_body:${routeId}` : null;
	const streamingMetadataOutletId = options.streamingMetadataOutlet ? `__vinext_streaming_metadata_outlet:${routeId}` : null;
	const layoutEntries = createAppPageLayoutEntries(options.route);
	const templateEntries = createAppPageTemplateEntries(options.route);
	const loadingEntries = createAppPageLoadingEntries(options.route);
	const errorEntries = createAppPageErrorEntries(options.route);
	const findNearestAncestorLoadingEntry = (treePosition) => {
		for (let index = loadingEntries.length - 1; index >= 0; index--) if (loadingEntries[index].treePosition < treePosition) return loadingEntries[index];
	};
	const findNearestLoadingEntryAtOrAbove = (treePosition) => {
		let nearest;
		for (const entry of loadingEntries) if (entry.treePosition <= treePosition && (!nearest || entry.treePosition > nearest.treePosition)) nearest = entry;
		return nearest;
	};
	const isPrefetchEmpty = renderMode === APP_RSC_RENDER_MODE_PREFETCH_EMPTY;
	const isPrefetchLoadingShell = renderMode === APP_RSC_RENDER_MODE_PREFETCH_LOADING_SHELL;
	const pageRenderDependency = isPrefetchLoadingShell ? null : options.pageRenderDependency;
	const prefetchLoadingEntry = isPrefetchLoadingShell ? getPrefetchLoadingEntry(options.route) : null;
	const metadataPlacement = options.metadataPlacement ?? "head";
	const layoutEntriesByTreePosition = /* @__PURE__ */ new Map();
	const templateEntriesByTreePosition = /* @__PURE__ */ new Map();
	const loadingEntriesByTreePosition = /* @__PURE__ */ new Map();
	const errorEntriesByTreePosition = /* @__PURE__ */ new Map();
	for (const layoutEntry of layoutEntries) layoutEntriesByTreePosition.set(layoutEntry.treePosition, layoutEntry);
	for (const templateEntry of templateEntries) templateEntriesByTreePosition.set(templateEntry.treePosition, templateEntry);
	for (const loadingEntry of loadingEntries) loadingEntriesByTreePosition.set(loadingEntry.treePosition, loadingEntry);
	for (const errorEntry of errorEntries) errorEntriesByTreePosition.set(errorEntry.treePosition, errorEntry);
	const layoutIndicesByTreePosition = /* @__PURE__ */ new Map();
	for (let index = 0; index < layoutEntries.length; index++) layoutIndicesByTreePosition.set(layoutEntries[index].treePosition, index);
	const layoutDependenciesByIndex = /* @__PURE__ */ new Map();
	const renderDependenciesByElementId = /* @__PURE__ */ new Map();
	const layoutDependenciesBefore = [];
	const slotDependenciesByLayoutIndex = [];
	const templateDependenciesById = /* @__PURE__ */ new Map();
	const templateDependenciesBeforeById = /* @__PURE__ */ new Map();
	const pageDependencies = [];
	const rootLayoutTreePath = layoutEntries[0]?.treePath ?? null;
	const slotNameCounts = /* @__PURE__ */ new Map();
	for (const slot of Object.values(options.route.slots ?? {})) {
		const slotName = slot.name;
		slotNameCounts.set(slotName, (slotNameCounts.get(slotName) ?? 0) + 1);
	}
	const orderedTreePositions = Array.from(/* @__PURE__ */ new Set([
		...layoutEntries.map((entry) => entry.treePosition),
		...templateEntries.map((entry) => entry.treePosition),
		...loadingEntries.map((entry) => entry.treePosition),
		...errorEntries.map((entry) => entry.treePosition)
	])).sort((left, right) => left - right);
	const resolveSlotOverride = (slotKey, slotName) => {
		const overrideByKey = options.slotOverrides?.[slotKey];
		if (overrideByKey) return overrideByKey;
		if (slotKey === slotName || (slotNameCounts.get(slotName) ?? 0) === 1) return options.slotOverrides?.[slotName];
	};
	const interception = renderIdentity?.interception ?? options.interception ?? null;
	const slotBindings = createAppPageSlotBindings(options.route, layoutEntries, resolveSlotOverride, {
		interception,
		routeId,
		routePath: options.routePath
	});
	const prefetchSlotLoadingEntries = isPrefetchLoadingShell ? Object.entries(options.route.slots ?? {}).flatMap(([slotKey, slot]) => {
		return getFirstLoadingEntry(createAppPageSlotLoadingEntries(slot, resolveSlotOverride(slotKey, slot.name) ?? null)) ? [{ ownerTreePosition: slot.ownerTreePosition ?? 0 }] : [];
	}) : [];
	const prefetchCutoffTreePosition = isPrefetchLoadingShell ? prefetchLoadingEntry?.treePosition ?? prefetchSlotLoadingEntries.reduce((deepest, entry) => Math.max(deepest, entry.ownerTreePosition), 0) : null;
	const includesPrefetchTreePosition = (treePosition) => prefetchCutoffTreePosition === null || treePosition <= prefetchCutoffTreePosition;
	const segmentPlan = createAppPageSegmentPlan({
		includeSlot(ownerTreePosition, targetTreePosition) {
			if (isPrefetchEmpty) return false;
			if (!isPrefetchLoadingShell) return true;
			return prefetchLoadingEntry ? ownerTreePosition <= prefetchLoadingEntry.treePosition : includesPrefetchTreePosition(targetTreePosition);
		},
		interception,
		layoutEntries,
		matchedParams: options.matchedParams,
		pageElementId,
		resolveSlotOverride,
		rootLayoutTreePath,
		route: options.route,
		routeSegments,
		semanticPageIdentity: options.semanticPageIdentity,
		semanticInterceptionTargetRouteId: options.semanticInterceptionTargetRouteId ?? null,
		slotBindings,
		templateEntries
	});
	const routeResetKey = segmentPlan.routeResetKey;
	const slotPlansByKey = new Map(segmentPlan.slots.map((slot) => [slot.key, slot]));
	const resolveRouteSegmentResetKey = (treePosition) => resolveAppPageSegmentStateKey(routeSegments, treePosition, options.matchedParams);
	const metadataEntries = AppElementsWire.createMetadataEntries({
		bfcacheSegmentIdentities: segmentPlan.bfcacheSegmentIdentities,
		interception,
		interceptionContext,
		layoutIds: layoutEntries.map((entry) => entry.id),
		rootLayoutTreePath,
		routeId,
		sourcePage: createAppPageSourcePage(options.sourcePageSegments ?? routeSegments),
		slotBindings
	});
	if (isPrefetchEmpty) return {
		...metadataEntries,
		[APP_LAYOUT_IDS_KEY]: [],
		[APP_ROOT_LAYOUT_KEY]: null,
		[pageElementId]: null,
		[routeId]: null
	};
	const elements = {};
	for (const slotPlan of segmentPlan.slots) for (const segment of slotPlan.nestedBfcacheSegments) elements[segment.id] = null;
	if (options.route.staticSiblings && options.route.staticSiblings.length > 0) elements[APP_STATIC_SIBLINGS_KEY] = options.route.staticSiblings;
	if (options.streamingMetadata && streamingMetadataBodyId) elements[streamingMetadataBodyId] = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(AppPageStreamingMetadata, {
		metadata: options.streamingMetadataTags ?? options.streamingMetadata,
		pathname: options.resolvedMetadataPathname ?? options.routePath,
		scriptNonce: options.scriptNonce,
		trailingSlash: options.trailingSlash
	});
	if (options.streamingMetadataOutlet && streamingMetadataOutletId) elements[streamingMetadataOutletId] = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(AppPageMetadataOutlet, { metadata: options.streamingMetadataOutlet });
	const getEffectiveSlotParams = (slotKey, _slotName) => slotPlansByKey.get(slotKey)?.params ?? options.matchedParams;
	for (const treePosition of orderedTreePositions) {
		if (isPrefetchLoadingShell && !includesPrefetchTreePosition(treePosition)) continue;
		const layoutIndex = layoutIndicesByTreePosition.get(treePosition);
		if (layoutIndex !== void 0) {
			const layoutEntry = layoutEntries[layoutIndex];
			layoutDependenciesBefore[layoutIndex] = [...pageDependencies];
			if (getDefaultExport$1(layoutEntry.layoutModule)) {
				const layoutDependency = createAppRenderDependency();
				layoutDependenciesByIndex.set(layoutIndex, layoutDependency);
				renderDependenciesByElementId.set(layoutEntry.id, layoutDependency);
				pageDependencies.push(layoutDependency);
			}
			slotDependenciesByLayoutIndex[layoutIndex] = [...pageDependencies];
		}
		const templateEntry = templateEntriesByTreePosition.get(treePosition);
		if (!templateEntry || !getDefaultExport$1(templateEntry.templateModule)) continue;
		const templateDependency = createAppRenderDependency();
		templateDependenciesById.set(templateEntry.id, templateDependency);
		templateDependenciesBeforeById.set(templateEntry.id, [...pageDependencies]);
		pageDependencies.push(templateDependency);
	}
	pageRenderDependency?.setResultDependencies(pageDependencies);
	const routeLoadingComponent = getDefaultExport$1(options.route.loading);
	const prefetchLoadingComponent = getDefaultExport$1(prefetchLoadingEntry?.loadingModule);
	const shouldRenderPrefetchLoadingShell = isPrefetchLoadingShell && (prefetchLoadingComponent !== null || prefetchSlotLoadingEntries.length > 0);
	if (shouldRenderPrefetchLoadingShell) elements[APP_PREFETCH_LOADING_SHELL_MARKER_KEY] = "LoadingBoundary";
	const pageLoadingModule = resolveAppPageLoadingModuleAtOrAbove(options.route, routeSegments.length);
	const PageLoadingComponent = pageRenderDependency ? getDefaultExport$1(pageLoadingModule) : null;
	const pageElement = PageLoadingComponent ? /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(import_react_react_server.Suspense, {
		fallback: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(PageLoadingComponent, {}),
		children: options.element
	}, routeResetKey) : options.element;
	elements[pageElementId] = isPrefetchLoadingShell ? null : pageRenderDependency ? pageElement : renderAfterAppDependencies(pageElement, pageDependencies);
	for (const templateEntry of templateEntries) {
		if (isPrefetchLoadingShell && !includesPrefetchTreePosition(templateEntry.treePosition)) continue;
		const templateComponent = getDefaultExport$1(templateEntry.templateModule);
		if (!templateComponent) continue;
		const TemplateComponent = templateComponent;
		const templateDependency = templateDependenciesById.get(templateEntry.id);
		let templateElement = templateDependency ? renderAppComponentWithDependencyBarrier(TemplateComponent, { children: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(Children, {}) }, templateDependency) : /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(TemplateComponent, { children: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(Children, {}) });
		const ancestorLoadingEntry = findNearestAncestorLoadingEntry(templateEntry.treePosition);
		const ancestorLoadingComponent = getDefaultExport$1(ancestorLoadingEntry?.loadingModule);
		if (ancestorLoadingComponent && ancestorLoadingEntry) {
			const AncestorLoadingComponent = ancestorLoadingComponent;
			const loadingResetKey = resolveRouteSegmentResetKey(ancestorLoadingEntry.treePosition);
			templateElement = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(import_react_react_server.Suspense, {
				fallback: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(AncestorLoadingComponent, {}),
				children: templateElement
			}, loadingResetKey || routeResetKey);
		}
		elements[templateEntry.id] = renderAfterAppDependencies(templateElement, [...pageRenderDependency ? [pageRenderDependency] : [], ...templateDependenciesBeforeById.get(templateEntry.id) ?? []]);
	}
	for (let index = 0; index < layoutEntries.length; index++) {
		const layoutEntry = layoutEntries[index];
		if (isPrefetchLoadingShell && !includesPrefetchTreePosition(layoutEntry.treePosition)) continue;
		const layoutComponent = getDefaultExport$1(layoutEntry.layoutModule);
		if (!layoutComponent) continue;
		const layoutParams = resolveAppPageSegmentParams(options.route.routeSegments, layoutEntry.treePosition, options.matchedParams);
		recordLayoutSkipObservationScope({
			layoutId: layoutEntry.id,
			layoutModule: layoutEntry.layoutModule,
			layoutParamAccess: options.layoutParamAccess,
			routeSegments: options.route.routeSegments,
			treePosition: layoutEntry.treePosition
		});
		const layoutProps = { params: options.makeThenableParams(layoutParams, options.layoutParamAccess?.createThenableParamsObserver(layoutEntry.id)) };
		for (const slot of Object.values(options.route.slots ?? {})) {
			const slotName = slot.name;
			if ((slot.layoutIndex >= 0 ? slot.layoutIndex : layoutEntries.length - 1) !== index) continue;
			layoutProps[slotName] = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(ParallelSlot, { name: slotName });
		}
		const LayoutComponent = layoutComponent;
		const layoutDependency = layoutDependenciesByIndex.get(index);
		let layoutElement = layoutDependency ? renderAppComponentWithDependencyBarrier(LayoutComponent, {
			...layoutProps,
			children: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(Children, {})
		}, layoutDependency) : /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(LayoutComponent, {
			...layoutProps,
			children: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(Children, {})
		});
		const ancestorLoadingEntry = findNearestAncestorLoadingEntry(layoutEntry.treePosition);
		const ancestorLoadingComponent = getDefaultExport$1(ancestorLoadingEntry?.loadingModule);
		if (ancestorLoadingComponent && ancestorLoadingEntry) {
			const AncestorLoadingComponent = ancestorLoadingComponent;
			const loadingResetKey = resolveRouteSegmentResetKey(ancestorLoadingEntry.treePosition);
			layoutElement = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(import_react_react_server.Suspense, {
				fallback: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(AncestorLoadingComponent, {}),
				children: layoutElement
			}, loadingResetKey || routeResetKey);
		}
		elements[layoutEntry.id] = renderAfterAppDependencies(layoutElement, [...pageRenderDependency ? [pageRenderDependency] : [], ...layoutDependenciesBefore[index] ?? []]);
	}
	for (const slotPlan of segmentPlan.slots) {
		const { branchSegments, includedInPayload, nestedBfcacheSegments, ownerTreePosition, params: slotParams, resetKey: slotResetKey, routeSegments: slotRouteSegments, slot, slotId, slotOverride, targetIndex } = slotPlan;
		const isOwnedAtRoutePrefetchCutoff = isPrefetchLoadingShell && prefetchLoadingEntry !== null && ownerTreePosition === prefetchLoadingEntry.treePosition;
		if (!includedInPayload) continue;
		const slotOwnerParams = resolveAppPageSegmentParams(options.route.routeSegments, layoutEntries[targetIndex]?.treePosition ?? 0, options.matchedParams);
		const hasSlotTreeOverride = slotOverride?.pageModule != null || slotOverride?.layoutModules !== void 0;
		const slotLoadingEntries = createAppPageSlotLoadingEntries(slot, hasSlotTreeOverride ? slotOverride ?? null : null);
		const prefetchSlotLoadingEntry = isOwnedAtRoutePrefetchCutoff ? prefetchLoadingEntry : isPrefetchLoadingShell ? getFirstLoadingEntry(slotLoadingEntries) : null;
		if (isPrefetchLoadingShell && prefetchSlotLoadingEntry === null) continue;
		const overrideOrPageComponent = getDefaultExport$1(slotOverride?.pageModule) ?? getDefaultExport$1(slot.page);
		const defaultComponent = getDefaultExport$1(slot.default);
		if (!overrideOrPageComponent && defaultComponent && options.isRscRequest && options.mountedSlotIds?.has(slotId)) continue;
		const slotComponent = overrideOrPageComponent ?? defaultComponent;
		if (!slotComponent && !isOwnedAtRoutePrefetchCutoff) {
			elements[slotId] = AppElementsWire.unmatchedSlotValue;
			continue;
		}
		let slotElement;
		if (prefetchSlotLoadingEntry) slotElement = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(getDefaultExport$1(prefetchSlotLoadingEntry.loadingModule), {});
		else {
			const slotProps = { params: options.makeThenableParams(slotParams) };
			if (options.searchParams !== void 0) slotProps.searchParams = options.searchParams;
			if (slotOverride?.props) Object.assign(slotProps, slotOverride.props);
			slotElement = options.createPageElement ? options.createPageElement(slotComponent, slotProps) : /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(slotComponent, { ...slotProps });
			if (overrideOrPageComponent) slotElement = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(import_react_react_server.Fragment, { children: slotElement }, slotResetKey);
		}
		const branchLayouts = /* @__PURE__ */ new Map();
		const addBranchLayout = (treePosition, entry) => {
			const entries = branchLayouts.get(treePosition) ?? [];
			entries.push(entry);
			branchLayouts.set(treePosition, entries);
		};
		if (hasSlotTreeOverride) for (const [layoutIndex, layoutModule] of (slotOverride?.layoutModules ?? []).entries()) {
			const component = getDefaultExport$1(layoutModule);
			if (!component) continue;
			const treePosition = slotOverride?.layoutSegments?.[layoutIndex]?.length ?? branchSegments.length;
			addBranchLayout(treePosition, {
				component,
				params: resolveSlotLayoutParams(branchSegments, treePosition, slotParams)
			});
		}
		else for (const [layoutIndex, layoutModule] of (slot.configLayouts ?? []).entries()) {
			const component = getDefaultExport$1(layoutModule);
			if (!component) continue;
			const treePosition = slot.configLayoutTreePositions?.[layoutIndex] ?? 0;
			addBranchLayout(treePosition, {
				component,
				params: {
					...slotOwnerParams,
					...resolveSlotLayoutParams(slotRouteSegments, treePosition, slotParams)
				}
			});
		}
		const slotLayoutComponent = overrideOrPageComponent ? getDefaultExport$1(slot.layout) : null;
		if (slotLayoutComponent) {
			const rootEntries = branchLayouts.get(0) ?? [];
			branchLayouts.set(0, [{
				component: slotLayoutComponent,
				params: slotOwnerParams
			}, ...rootEntries]);
		}
		const branchLoadings = /* @__PURE__ */ new Map();
		for (const entry of slotLoadingEntries) {
			const component = getDefaultExport$1(entry.loadingModule);
			if (!component) continue;
			const components = branchLoadings.get(entry.treePosition) ?? [];
			components.push(component);
			branchLoadings.set(entry.treePosition, components);
		}
		const slotErrorComponent = getErrorBoundaryExport(slot.error);
		const branchTreePositions = Array.from(/* @__PURE__ */ new Set([
			...branchLayouts.keys(),
			...branchLoadings.keys(),
			...slotErrorComponent ? [0] : [],
			...nestedBfcacheSegments.flatMap((segment) => segment.treePosition === null ? [] : [segment.treePosition])
		])).filter((treePosition) => !prefetchSlotLoadingEntry || !isOwnedAtRoutePrefetchCutoff && treePosition <= prefetchSlotLoadingEntry.treePosition).sort((left, right) => left - right);
		for (let index = branchTreePositions.length - 1; index >= 0; index--) {
			const treePosition = branchTreePositions[index];
			const nestedBfcacheSegment = nestedBfcacheSegments.find((segment) => segment.treePosition === treePosition);
			if (nestedBfcacheSegment) slotElement = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(BfcacheSegmentBoundary, {
				id: nestedBfcacheSegment.id,
				stateKey: nestedBfcacheSegment.stateKey,
				children: slotElement
			});
			const loadingComponents = prefetchSlotLoadingEntry ? [] : branchLoadings.get(treePosition) ?? [];
			for (let loadingIndex = loadingComponents.length - 1; loadingIndex >= 0; loadingIndex--) {
				const LoadingComponent = loadingComponents[loadingIndex];
				const loadingResetKey = resolveAppPageSegmentStateKey(branchSegments, treePosition, slotParams);
				slotElement = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(import_react_react_server.Suspense, {
					fallback: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(LoadingComponent, {}),
					children: slotElement
				}, loadingResetKey || slotResetKey);
			}
			if (treePosition === 0 && slotErrorComponent) slotElement = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(ErrorBoundary, {
				resetKey: slotResetKey,
				fallback: slotErrorComponent,
				children: slotElement
			});
			const layoutEntriesAtPosition = branchLayouts.get(treePosition) ?? [];
			for (let layoutIndex = layoutEntriesAtPosition.length - 1; layoutIndex >= 0; layoutIndex--) {
				const layoutEntry = layoutEntriesAtPosition[layoutIndex];
				const LayoutComponent = layoutEntry.component;
				slotElement = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(LayoutComponent, {
					params: options.makeThenableParams(layoutEntry.params),
					children: slotElement
				});
			}
		}
		const unalignedBfcacheSegment = nestedBfcacheSegments.find((segment) => segment.treePosition === null);
		if (unalignedBfcacheSegment) slotElement = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(BfcacheSegmentBoundary, {
			id: unalignedBfcacheSegment.id,
			stateKey: unalignedBfcacheSegment.stateKey,
			children: slotElement
		});
		const ownerLoadingEntry = isPrefetchLoadingShell ? void 0 : findNearestLoadingEntryAtOrAbove(ownerTreePosition);
		const ownerLoadingComponent = getDefaultExport$1(ownerLoadingEntry?.loadingModule);
		if (ownerLoadingComponent && ownerLoadingEntry) {
			const OwnerLoadingComponent = ownerLoadingComponent;
			const ownerResetKey = resolveRouteSegmentResetKey(ownerLoadingEntry.treePosition);
			slotElement = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(import_react_react_server.Suspense, {
				fallback: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(OwnerLoadingComponent, {}),
				children: slotElement
			}, ownerResetKey || slotResetKey);
		}
		elements[slotId] = renderAfterAppDependencies(slotElement, [...pageRenderDependency ? [pageRenderDependency] : [], ...targetIndex >= 0 ? slotDependenciesByLayoutIndex[targetIndex] ?? [] : []]);
	}
	let routeChildren = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsxs)(import_jsx_runtime_react_server.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(LayoutSegmentProvider, {
		providerId: pageElementId,
		segmentMap: { children: [APP_PAGE_SEGMENT_KEY] },
		children: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(Slot, { id: pageElementId })
	}), createAppPageStreamingMetadataOutlet(streamingMetadataOutletId, options.streamingMetadataOutletSuspended)] });
	if (isPrefetchLoadingShell) if (prefetchLoadingComponent === null) routeChildren = null;
	else routeChildren = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(prefetchLoadingComponent, {});
	else {
		routeChildren = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(RedirectBoundary, { children: routeChildren });
		if (routeLoadingComponent) routeChildren = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(import_react_react_server.Suspense, {
			fallback: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(routeLoadingComponent, {}),
			children: routeChildren
		}, routeResetKey);
		routeChildren = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(AppRouterScrollTarget, { children: routeChildren });
	}
	const lastLayoutErrorModule = errorEntries.length > 0 ? errorEntries[errorEntries.length - 1].errorModule : null;
	const configuredNotFoundComponent = getDefaultExport$1(options.route.notFound) ?? getDefaultExport$1(options.rootNotFoundModule);
	const defaultNotFoundOwnerLayoutId = configuredNotFoundComponent === null ? layoutEntries[0]?.id ?? null : null;
	const notFoundComponent = configuredNotFoundComponent ?? (defaultNotFoundOwnerLayoutId === null ? DEFAULT_NOT_FOUND_COMPONENT : null);
	if (notFoundComponent) routeChildren = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(NotFoundBoundary, {
		resetKey: routeResetKey,
		fallback: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(notFoundComponent, {}),
		children: routeChildren
	});
	const forbiddenComponent = getDefaultExport$1(options.route.forbidden) ?? getDefaultExport$1(options.rootForbiddenModule);
	if (forbiddenComponent) routeChildren = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(ForbiddenBoundary, {
		resetKey: routeResetKey,
		fallback: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(forbiddenComponent, {}),
		children: routeChildren
	});
	const unauthorizedComponent = getDefaultExport$1(options.route.unauthorized) ?? getDefaultExport$1(options.rootUnauthorizedModule);
	if (unauthorizedComponent) routeChildren = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(UnauthorizedBoundary, {
		resetKey: routeResetKey,
		fallback: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(unauthorizedComponent, {}),
		children: routeChildren
	});
	const pageErrorComponent = getErrorBoundaryExport(options.route.error);
	if (pageErrorComponent && options.route.error !== lastLayoutErrorModule) routeChildren = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(ErrorBoundary, {
		resetKey: routeResetKey,
		fallback: pageErrorComponent,
		children: routeChildren
	});
	const renderedTreePositions = isPrefetchLoadingShell ? orderedTreePositions.filter(includesPrefetchTreePosition) : orderedTreePositions;
	for (let index = renderedTreePositions.length - 1; index >= 0; index--) {
		const treePosition = renderedTreePositions[index];
		const segmentResetKey = resolveRouteSegmentResetKey(treePosition);
		let segmentChildren = routeChildren;
		const layoutEntry = layoutEntriesByTreePosition.get(treePosition);
		const templateEntry = templateEntriesByTreePosition.get(treePosition);
		const loadingEntry = loadingEntriesByTreePosition.get(treePosition);
		const errorEntry = errorEntriesByTreePosition.get(treePosition);
		if (!isPrefetchLoadingShell && treePosition < routeSegments.length) {
			const segmentLoadingComponent = getDefaultExport$1(loadingEntry?.loadingModule);
			if (segmentLoadingComponent) segmentChildren = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(import_react_react_server.Suspense, {
				fallback: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(segmentLoadingComponent, {}),
				children: segmentChildren
			}, segmentResetKey || routeResetKey);
		}
		if (layoutEntry) {
			const layoutNotFoundComponent = getDefaultExport$1(layoutEntry.notFoundModule) ?? (layoutEntry.id === defaultNotFoundOwnerLayoutId ? DEFAULT_NOT_FOUND_COMPONENT : null);
			if (layoutNotFoundComponent) segmentChildren = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(NotFoundBoundary, {
				resetKey: segmentResetKey,
				fallback: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(layoutNotFoundComponent, {}),
				children: segmentChildren
			});
			const layoutForbiddenComponent = getDefaultExport$1(layoutEntry.forbiddenModule);
			if (layoutForbiddenComponent) segmentChildren = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(ForbiddenBoundary, {
				resetKey: segmentResetKey,
				fallback: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(layoutForbiddenComponent, {}),
				children: segmentChildren
			});
			const layoutUnauthorizedComponent = getDefaultExport$1(layoutEntry.unauthorizedModule);
			if (layoutUnauthorizedComponent) segmentChildren = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(UnauthorizedBoundary, {
				resetKey: segmentResetKey,
				fallback: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(layoutUnauthorizedComponent, {}),
				children: segmentChildren
			});
		}
		const segmentErrorComponent = getErrorBoundaryExport(errorEntry?.errorModule ?? layoutEntry?.errorModule);
		if (segmentErrorComponent) segmentChildren = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(ErrorBoundary, {
			resetKey: segmentResetKey,
			fallback: segmentErrorComponent,
			children: segmentChildren
		});
		if (templateEntry && getDefaultExport$1(templateEntry.templateModule)) {
			const templateStateKey = resolveAppPageTemplateStateKey(routeSegments, templateEntry.treePosition, options.matchedParams);
			segmentChildren = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(Slot, {
				id: templateEntry.id,
				children: segmentChildren
			}, String(false) === "true" ? void 0 : templateStateKey);
		}
		if (!layoutEntry) {
			routeChildren = segmentChildren;
			continue;
		}
		const layoutHasElement = getDefaultExport$1(layoutEntry.layoutModule) !== null;
		const layoutIndex = layoutIndicesByTreePosition.get(treePosition) ?? -1;
		const segmentMap = { children: resolveAppPageLayoutSegmentProviderSegments(options.route.childrenRouteSegments ?? routeSegments, layoutEntry.treePosition, options.matchedParams) };
		for (const [slotKey, slot] of Object.entries(options.route.slots ?? {})) {
			const slotName = slot.name;
			if ((slot.layoutIndex >= 0 ? slot.layoutIndex : layoutEntries.length - 1) !== layoutIndex) continue;
			const slotParams = getEffectiveSlotParams(slotKey, slotName);
			const slotOverride = resolveSlotOverride(slotKey, slotName);
			if (!(getDefaultExport$1(slotOverride?.pageModule) !== null || getDefaultExport$1(slot.page) !== null) && options.isRscRequest && options.mountedSlotIds?.has(resolveAppPageSlotId(slot, layoutEntry.treePath))) continue;
			const slotRouteSegments = slotOverride?.routeSegments ?? slot.routeSegments;
			segmentMap[slotName] = slotRouteSegments ? resolveAppPageLayoutSegmentProviderSegments(slotRouteSegments, 0, slotParams) : [];
		}
		routeChildren = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(LayoutSegmentProvider, {
			providerId: layoutEntry.id,
			segmentMap,
			children: layoutHasElement ? /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(Slot, {
				id: layoutEntry.id,
				parallelSlots: createAppPageParallelSlotEntries(layoutIndex, layoutEntries, options.route, getEffectiveSlotParams, resolveSlotOverride),
				children: segmentChildren
			}) : segmentChildren
		});
	}
	const globalErrorComponent = getErrorBoundaryExport(options.globalErrorModule);
	routeChildren = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(GlobalErrorBoundary, {
		fallback: DEFAULT_GLOBAL_ERROR_COMPONENT$1,
		children: globalErrorComponent ? /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(ErrorBoundary, {
			fallback: globalErrorComponent,
			children: routeChildren
		}) : routeChildren
	});
	const routeElement = /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsxs)(import_jsx_runtime_react_server.Fragment, { children: [
		createAppPageRouteHead(options.resolvedMetadata, options.resolvedViewport, options.resolvedMetadataPathname ?? options.routePath, metadataPlacement, options.trailingSlash),
		routeChildren,
		createAppPageRouteBodyMetadata(options.resolvedMetadata, options.resolvedMetadataPathname ?? options.routePath, metadataPlacement, options.trailingSlash, options.scriptNonce),
		createAppPageStreamingMetadataBody(streamingMetadataBodyId)
	] });
	elements[routeId] = pageRenderDependency ? renderAfterAppDependencies(routeElement, [pageRenderDependency]) : routeElement;
	Object.assign(elements, metadataEntries, options.route.staticSiblings && options.route.staticSiblings.length > 0 ? { [APP_STATIC_SIBLINGS_KEY]: options.route.staticSiblings } : {}, shouldRenderPrefetchLoadingShell ? { [APP_PREFETCH_LOADING_SHELL_MARKER_KEY]: "LoadingBoundary" } : {});
	registerAppElementRenderDependencies(elements, renderDependenciesByElementId);
	return elements;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-http-access-fallback-metadata.js
function isPresent(value) {
	return value !== null && value !== void 0;
}
/**
* Translate HTTP-access boundary semantics into the exact metadata source
* order used by Next.js's loader-tree walk.
*
* The not-found convention is appended at every active leaf. A sibling
* intercept is the primary leaf and therefore precedes the ordinary slot
* branches; otherwise the convention also represents the primary page leaf.
*/
function createHttpAccessFallbackPlan(options, fallbackLeafMode) {
	const routeSegments = options.routeSegments ?? [];
	const plan = [];
	for (const [index, layoutModule] of options.layoutModules.entries()) {
		if (!isPresent(layoutModule)) continue;
		const treePosition = options.layoutTreePositions?.[index] ?? 0;
		plan.push({
			kind: "source",
			source: {
				includeWhenEmpty: true,
				module: layoutModule,
				params: resolveAppPageSegmentParams(routeSegments, treePosition, options.params),
				routeSegments: routeSegments.slice(0, treePosition)
			}
		});
	}
	let activeBoundaryModule = options.boundaryModule;
	let activeBoundaryParams = options.boundaryParams;
	let activeBoundaryRouteSegments = routeSegments;
	const appendFallbackLeaf = () => {
		if (fallbackLeafMode === "final") {
			plan.push({ kind: "fallback-leaf" });
			return;
		}
		if (!activeBoundaryModule) return;
		plan.push({
			kind: "source",
			source: {
				includeWhenEmpty: true,
				module: activeBoundaryModule,
				params: activeBoundaryParams,
				routeSegments: activeBoundaryRouteSegments
			}
		});
	};
	if (!options.primaryParallelBranch) appendFallbackLeaf();
	const parallelBranches = [...options.primaryParallelBranch ? [options.primaryParallelBranch] : [], ...[...options.parallelBranches ?? []].sort((left, right) => right.ownerTreePosition - left.ownerTreePosition)];
	for (const branch of parallelBranches) {
		const parallelRoute = branch.head;
		const parallelParams = parallelRoute.params ?? options.params;
		const parallelRouteSegments = parallelRoute.routeSegments ?? routeSegments;
		const layoutModules = [...parallelRoute.layoutModules ?? [], parallelRoute.layoutModule].filter(isPresent);
		const layoutTreePositions = parallelRoute.layoutTreePositions ?? [];
		const layoutParams = parallelRoute.layoutParams ?? [];
		for (const [index, layoutModule] of layoutModules.entries()) plan.push({
			kind: "source",
			source: {
				includeWhenEmpty: true,
				module: layoutModule,
				params: layoutParams[index] ?? resolveAppPageBranchParams(parallelRouteSegments, layoutTreePositions[index] ?? 0, parallelParams),
				routeSegments: parallelRouteSegments
			}
		});
		if (options.branchNotFoundConventions !== false && branch.notFoundModule) {
			activeBoundaryModule = branch.notFoundModule;
			activeBoundaryParams = branch.notFoundParams ?? parallelParams;
			activeBoundaryRouteSegments = parallelRouteSegments;
		}
		appendFallbackLeaf();
	}
	return plan.flatMap((item) => {
		if (item.kind === "source") return [item.source];
		if (!activeBoundaryModule) return [];
		return [{
			includeWhenEmpty: true,
			module: activeBoundaryModule,
			params: activeBoundaryParams,
			routeSegments: activeBoundaryRouteSegments
		}];
	});
}
function createHttpAccessFallbackMetadataPlan(options) {
	return createHttpAccessFallbackPlan(options, "final");
}
function resolveHttpAccessFallbackMetadata(options) {
	return resolveOrderedAppPageMetadata({
		applyFileBasedMetadata: options.applyFileBasedMetadata,
		basePath: options.basePath,
		fallbackOnFileMetadataError: options.fallbackOnFileMetadataError,
		metadataRoutes: options.metadataRoutes,
		params: options.params,
		routePath: options.routePath,
		routeSegments: options.routeSegments,
		sources: createHttpAccessFallbackMetadataPlan(options)
	});
}
async function resolveHttpAccessFallbackViewport(options) {
	let accumulatedViewport = Promise.resolve(mergeViewport([]));
	for (const source of createHttpAccessFallbackPlan(options, "snapshot")) {
		const parentForSource = accumulatedViewport;
		const viewportPromise = resolveModuleViewport(source.module, source.params, void 0, parentForSource);
		viewportPromise.catch(() => null);
		accumulatedViewport = Promise.all([parentForSource, viewportPromise]).then(([parent, viewport]) => viewport ? mergeViewport([parent, viewport]) : parent);
		accumulatedViewport.catch(() => null);
	}
	return accumulatedViewport;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/routing/route-trie.js
function createNode() {
	return {
		staticChildren: /* @__PURE__ */ new Map(),
		dynamicChild: null,
		catchAllChild: null,
		optionalCatchAllChild: null,
		route: null
	};
}
/**
* Build a trie from pre-sorted routes.
*
* Routes must have a `patternParts` property (string[] of URL segments).
* Pattern segment conventions:
*   - `:name`  — dynamic segment
*   - `:name+` — catch-all (1+ segments)
*   - `:name*` — optional catch-all (0+ segments)
*   - anything else — static segment
*
* First route to claim a terminal position wins (routes are pre-sorted
* by precedence, so insertion order preserves correct priority).
*/
function buildRouteTrie(routes) {
	const root = createNode();
	for (const route of routes) {
		const parts = route.patternParts;
		if (parts.length === 0) {
			if (root.route === null) root.route = route;
			continue;
		}
		let node = root;
		for (let i = 0; i < parts.length; i++) {
			const part = parts[i];
			if (part.endsWith("+") && part.startsWith(":")) {
				if (i !== parts.length - 1) break;
				const paramName = part.slice(1, -1);
				if (node.catchAllChild === null) node.catchAllChild = {
					paramName,
					route
				};
				break;
			}
			if (part.endsWith("*") && part.startsWith(":")) {
				if (i !== parts.length - 1) break;
				const paramName = part.slice(1, -1);
				if (node.optionalCatchAllChild === null) node.optionalCatchAllChild = {
					paramName,
					route
				};
				break;
			}
			if (part.startsWith(":")) {
				const paramName = part.slice(1);
				if (node.dynamicChild === null) node.dynamicChild = {
					paramName,
					node: createNode()
				};
				node = node.dynamicChild.node;
				if (i === parts.length - 1) {
					if (node.route === null) node.route = route;
				}
				continue;
			}
			let child = node.staticChildren.get(part);
			if (!child) {
				child = createNode();
				node.staticChildren.set(part, child);
			}
			node = child;
			if (i === parts.length - 1) {
				if (node.route === null) node.route = route;
			}
		}
	}
	return root;
}
function trieMatchRaw(root, urlParts) {
	return match(root, urlParts, 0, []);
}
function match(node, urlParts, index, entries) {
	if (index === urlParts.length) {
		if (node.route !== null) return {
			route: node.route,
			params: buildParams(entries)
		};
		if (node.optionalCatchAllChild !== null) return {
			route: node.optionalCatchAllChild.route,
			params: buildParams(entries)
		};
		return null;
	}
	const segment = urlParts[index];
	const staticChild = node.staticChildren.get(segment);
	if (staticChild) {
		const result = match(staticChild, urlParts, index + 1, entries);
		if (result !== null) return result;
	}
	if (node.dynamicChild !== null) {
		entries.push([node.dynamicChild.paramName, segment]);
		const result = match(node.dynamicChild.node, urlParts, index + 1, entries);
		if (result !== null) return result;
		entries.pop();
	}
	if (node.catchAllChild !== null) {
		const remaining = urlParts.slice(index);
		const params = buildParams(entries);
		params[node.catchAllChild.paramName] = remaining;
		return {
			route: node.catchAllChild.route,
			params
		};
	}
	if (node.optionalCatchAllChild !== null) {
		const params = buildParams(entries);
		params[node.optionalCatchAllChild.paramName] = urlParts.slice(index);
		return {
			route: node.optionalCatchAllChild.route,
			params
		};
	}
	return null;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/routing/route-pattern.js
function matchRoutePattern(urlParts, patternParts) {
	const params = matchRoutePatternRaw(urlParts, patternParts);
	if (params) decodeMatchedParams(params);
	return params;
}
function matchRoutePatternRaw(urlParts, patternParts) {
	const params = Object.create(null);
	function matchFrom(urlIndex, patternIndex) {
		if (patternIndex === patternParts.length) return urlIndex === urlParts.length;
		const patternPart = patternParts[patternIndex];
		if (patternPart.startsWith(":") && (patternPart.endsWith("+") || patternPart.endsWith("*"))) {
			const paramName = patternPart.slice(1, -1);
			const minLength = patternPart.endsWith("+") ? 1 : 0;
			for (let endIndex = urlIndex + minLength; endIndex <= urlParts.length; endIndex++) {
				const value = urlParts.slice(urlIndex, endIndex);
				if (value.length > 0) params[paramName] = value;
				else delete params[paramName];
				if (matchFrom(endIndex, patternIndex + 1)) return true;
			}
			delete params[paramName];
			return false;
		}
		if (patternPart.startsWith(":")) {
			if (urlIndex >= urlParts.length) return false;
			const paramName = patternPart.slice(1);
			params[paramName] = urlParts[urlIndex];
			if (matchFrom(urlIndex + 1, patternIndex + 1)) return true;
			delete params[paramName];
			return false;
		}
		if (urlIndex >= urlParts.length || urlParts[urlIndex] !== patternPart) return false;
		return matchFrom(urlIndex + 1, patternIndex + 1);
	}
	return matchFrom(0, 0) ? params : null;
}
function matchRoutePatternPrefix(pathParts, patternParts) {
	let pathIndex = 0;
	for (let patternIndex = 0; patternIndex < patternParts.length; patternIndex++) {
		const patternPart = patternParts[patternIndex];
		const isTerminal = patternIndex === patternParts.length - 1;
		if (patternPart.startsWith(":") && patternPart.endsWith("+")) return isTerminal && pathParts.length - pathIndex >= 1;
		if (patternPart.startsWith(":") && patternPart.endsWith("*")) return isTerminal;
		if (pathIndex >= pathParts.length) return false;
		if (patternPart.startsWith(":")) {
			pathIndex++;
			continue;
		}
		if (pathParts[pathIndex] !== patternPart) return false;
		pathIndex++;
	}
	return true;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-rsc-route-matching.js
/**
* Sentinel slot key used for sibling-style interception entries.
* When a matched intercept carries this key, the render layer replaces the
* route's main page element instead of a parallel slot.
*/
var SIBLING_PAGE_INTERCEPT_SLOT_KEY = "__vinext_page_intercept";
function createRouteParams() {
	return Object.create(null);
}
function appRscPathnameParts(pathname, isNormalized = false) {
	const pathOnly = pathname.split("?")[0];
	const normalizedPathname = pathOnly === "/" ? "/" : pathOnly.replace(/\/$/, "");
	return isNormalized ? splitPathSegments(normalizedPathname) : splitPathnameForRouteMatch(normalizedPathname);
}
function appRscInterceptionSourcePathnameParts(pathname) {
	const pathOnly = pathname.split("?")[0];
	return splitPathSegments(pathOnly === "/" ? "/" : pathOnly.replace(/\/$/, "")).map((segment) => {
		try {
			return decodeURIComponent(segment);
		} catch {
			return segment;
		}
	});
}
function canonicalizeAppPageParam(value) {
	try {
		return encodeURIComponent(decodeURIComponent(value));
	} catch {
		return value;
	}
}
function canonicalizeAppPageParams(params) {
	for (const key of Object.keys(params)) {
		const value = params[key];
		params[key] = Array.isArray(value) ? value.map(canonicalizeAppPageParam) : canonicalizeAppPageParam(value);
	}
}
function isAppRouteHandlerRoute(route) {
	return route.routeHandler != null || typeof route.__loadRouteHandler === "function";
}
function normalizeMatchedParamsForRoute(result) {
	if (isAppRouteHandlerRoute(result.route)) decodeMatchedParams(result.params);
	else canonicalizeAppPageParams(result.params);
}
function extractRawParamsForMatchedRoute(patternParts, pathnameParts) {
	const params = createRouteParams();
	let pathnameIndex = 0;
	for (const part of patternParts) {
		if (!part.startsWith(":")) {
			pathnameIndex += 1;
			continue;
		}
		const isCatchAll = part.endsWith("+") || part.endsWith("*");
		const paramName = part.slice(1, isCatchAll ? -1 : void 0);
		if (isCatchAll) {
			const remaining = pathnameParts.slice(pathnameIndex);
			if (remaining.length > 0) params[paramName] = [...remaining];
			break;
		}
		const value = pathnameParts[pathnameIndex];
		if (value !== void 0) params[paramName] = value;
		pathnameIndex += 1;
	}
	return params;
}
function createAppRscRouteMatcher(routes) {
	const routeTrie = buildRouteTrie(routes);
	const interceptLookup = createInterceptLookup(routes);
	const routeIndexes = new Map(routes.map((route, index) => [route, index]));
	return {
		matchRoute(url) {
			const rawParts = appRscPathnameParts(url, true);
			const result = trieMatchRaw(routeTrie, appRscPathnameParts(url, false));
			if (!result) return null;
			result.params = extractRawParamsForMatchedRoute(result.route.patternParts, rawParts);
			normalizeMatchedParamsForRoute(result);
			return result;
		},
		matchRequestRoute(url) {
			const result = trieMatchRaw(routeTrie, appRscPathnameParts(url, true));
			if (!result) return null;
			normalizeMatchedParamsForRoute(result);
			return result;
		},
		findIntercept(pathname, sourcePathname = null) {
			if (sourcePathname === null) return null;
			const urlParts = appRscPathnameParts(pathname, true);
			const sourceParts = appRscInterceptionSourcePathnameParts(sourcePathname);
			const matchedSourceRoute = trieMatchRaw(routeTrie, sourceParts);
			for (const entry of interceptLookup) {
				if (!matchInterceptSource(sourceParts, entry)) continue;
				const params = matchRoutePatternRaw(urlParts, entry.targetPatternParts);
				if (params === null) continue;
				canonicalizeAppPageParams(params);
				const concreteSourceRoute = matchedSourceRoute && entry.sourceMatchPatternParts !== null && !isAppRouteHandlerRoute(matchedSourceRoute.route) ? matchedSourceRoute : null;
				const concreteSourceRouteIndex = concreteSourceRoute ? routeIndexes.get(concreteSourceRoute.route) ?? entry.sourceRouteIndex : entry.sourceRouteIndex;
				const sourceRoute = routes[concreteSourceRouteIndex];
				if (sourceRoute && isAppRouteHandlerRoute(sourceRoute)) continue;
				const matchedSourceParams = concreteSourceRoute ? concreteSourceRoute.params : sourceRoute ? matchSlotOwnerSourceParams(sourceParts, sourceRoute.patternParts, entry.sourceMatchPatternParts !== null) : null;
				if (matchedSourceParams === null && entry.sourceMatchPatternParts === null) continue;
				const sourceParams = matchedSourceParams && entry.sourceMatchPatternParts !== null ? pickPatternParams(matchedSourceParams, entry.sourceMatchPatternParts) : matchedSourceParams ?? createRouteParams();
				return {
					...entry,
					page: entry.__loadState.page,
					sourceRouteIndex: concreteSourceRouteIndex,
					matchedParams: mergeMatchedParams(sourceParams, params),
					sourceMatchedParams: matchedSourceParams ?? createRouteParams()
				};
			}
			return null;
		}
	};
}
/**
* Params for the slot owner when interception falls back to it instead of a
* concrete descendant source route. The owner is what renders, and
* `matchInterceptRoute` reads the promoted route's params solely from these,
* so dropping them would render a dynamic owner without its segments.
*
* An exact match covers a source that names the owner itself. It cannot
* succeed when the source names a deeper descendant — a rejected Route
* Handler, or a path with no concrete route — so once the descendants-allowed
* gate has approved the source, take the owner's params from that prefix.
*/
function matchSlotOwnerSourceParams(sourceParts, patternParts, descendantsAllowed) {
	const exact = matchRoutePatternRaw(sourceParts, patternParts);
	if (exact !== null) return exact;
	if (!descendantsAllowed || !matchRoutePatternPrefix(sourceParts, patternParts)) return null;
	return extractRawParamsForMatchedRoute(patternParts, sourceParts);
}
/**
* Check whether the request's source pathname (Next-URL / interception
* context) satisfies the intercept entry's intercepting-route pattern, with
* descendants allowed. Mirrors the header regex shape Next.js emits for the
* generated interception rewrite: `^<pattern>(?:/.*)?$`.
*
* When the entry has no declared `sourceMatchPatternParts`, fall back to the
* legacy behavior of accepting any source (we still require the source to be
* non-null at the caller — see `findIntercept`).
*/
function matchInterceptSource(sourceParts, entry) {
	const patternParts = entry.sourceMatchPatternParts;
	if (!patternParts) return true;
	if (patternParts.length === 0) return true;
	return matchRoutePatternPrefix(sourceParts, patternParts);
}
function interceptSegmentPrecedence(segment) {
	if (!segment.startsWith(":")) return 0;
	if (segment.endsWith("*")) return 3;
	if (segment.endsWith("+")) return 2;
	return 1;
}
function compareInterceptTargetPatterns(a, b) {
	const sharedLength = Math.min(a.targetPatternParts.length, b.targetPatternParts.length);
	for (let index = 0; index < sharedLength; index++) {
		const aSegment = a.targetPatternParts[index];
		const bSegment = b.targetPatternParts[index];
		const precedence = interceptSegmentPrecedence(aSegment) - interceptSegmentPrecedence(bSegment);
		if (precedence !== 0) return precedence;
		if (aSegment !== bSegment) return aSegment.localeCompare(bSegment);
	}
	const lengthDifference = a.targetPatternParts.length - b.targetPatternParts.length;
	return lengthDifference !== 0 ? lengthDifference : a.targetPattern.localeCompare(b.targetPattern);
}
function createRoutePatternStructureKey(patternParts) {
	return JSON.stringify(patternParts.map((part) => {
		if (!part.startsWith(":")) return ["static", part];
		if (part.endsWith("*")) return ["optional-catch-all"];
		if (part.endsWith("+")) return ["catch-all"];
		return ["dynamic"];
	}));
}
function createPatternStructureToRouteGraphId(routes) {
	const routeGraphIds = /* @__PURE__ */ new Map();
	for (const route of routes) {
		const routeGraphId = route.ids?.route;
		if (typeof routeGraphId !== "string") continue;
		const key = createRoutePatternStructureKey(route.patternParts);
		const previous = routeGraphIds.get(key);
		if (previous === void 0) routeGraphIds.set(key, routeGraphId);
		else if (previous !== routeGraphId) routeGraphIds.set(key, null);
	}
	return routeGraphIds;
}
function createInterceptLookup(routes) {
	const patternToIndex = new Map(routes.map((r, i) => [r.pattern, i]));
	const patternStructureToRouteGraphId = createPatternStructureToRouteGraphId(routes);
	const resolveTargetRouteGraphId = (targetPattern) => patternStructureToRouteGraphId.get(createRoutePatternStructureKey(targetPattern.split("/").filter(Boolean))) ?? null;
	const interceptLookup = [];
	for (let routeIndex = 0; routeIndex < routes.length; routeIndex++) {
		const route = routes[routeIndex];
		if (route.slots) for (const [slotKey, slotModule] of Object.entries(route.slots)) {
			if (!slotModule.intercepts) continue;
			for (const intercept of slotModule.intercepts) {
				const sourceMatchPattern = intercept.sourceMatchPattern ?? null;
				const sourceMatchPatternParts = sourceMatchPattern ? sourceMatchPattern.split("/").filter(Boolean) : null;
				const ownerRouteIndex = sourceMatchPattern !== null ? patternToIndex.get(sourceMatchPattern) ?? routeIndex : routeIndex;
				interceptLookup.push({
					interceptionGraphId: null,
					sourceRouteIndex: ownerRouteIndex,
					slotKey,
					slotId: typeof slotModule.id === "string" ? slotModule.id : null,
					targetRouteGraphId: resolveTargetRouteGraphId(intercept.targetPattern),
					targetPattern: intercept.targetPattern,
					targetPatternParts: intercept.targetPattern.split("/").filter(Boolean),
					sourceMatchPattern,
					sourceMatchPatternParts,
					sourcePageSegments: intercept.sourcePageSegments ?? null,
					interceptLayouts: intercept.interceptLayouts,
					interceptLayoutSegments: intercept.interceptLayoutSegments,
					interceptBranchSegments: intercept.interceptBranchSegments,
					interceptLoadings: intercept.interceptLoadings,
					interceptLoadingTreePositions: intercept.interceptLoadingTreePositions,
					interceptNotFoundBranchSegments: intercept.interceptNotFoundBranchSegments,
					__loadInterceptLayouts: intercept.__loadInterceptLayouts,
					__loadInterceptLoadings: intercept.__loadInterceptLoadings,
					page: intercept.page,
					__pageLoader: intercept.__pageLoader,
					notFound: intercept.notFound,
					__loadNotFound: intercept.__loadNotFound,
					notFoundTreePosition: intercept.notFoundTreePosition,
					__loadState: {
						page: intercept.page,
						pageLoading: null,
						notFound: intercept.notFound,
						notFoundLoading: null,
						interceptLayoutsLoading: null
					},
					params: intercept.params
				});
			}
		}
		if (route.siblingIntercepts) for (const intercept of route.siblingIntercepts) {
			const sourceMatchPattern = intercept.sourceMatchPattern ?? null;
			const sourceMatchPatternParts = sourceMatchPattern ? sourceMatchPattern.split("/").filter(Boolean) : null;
			interceptLookup.push({
				interceptionGraphId: typeof intercept.id === "string" ? intercept.id : null,
				sourceRouteIndex: routeIndex,
				slotKey: SIBLING_PAGE_INTERCEPT_SLOT_KEY,
				slotId: typeof intercept.slotId === "string" ? intercept.slotId : null,
				targetRouteGraphId: resolveTargetRouteGraphId(intercept.targetPattern),
				targetPattern: intercept.targetPattern,
				targetPatternParts: intercept.targetPattern.split("/").filter(Boolean),
				sourceMatchPattern,
				sourceMatchPatternParts,
				sourcePageSegments: intercept.sourcePageSegments ?? null,
				interceptLayouts: intercept.interceptLayouts,
				interceptLayoutSegments: intercept.interceptLayoutSegments,
				interceptBranchSegments: intercept.interceptBranchSegments,
				interceptLoadings: intercept.interceptLoadings,
				interceptLoadingTreePositions: intercept.interceptLoadingTreePositions,
				interceptNotFoundBranchSegments: intercept.interceptNotFoundBranchSegments,
				__loadInterceptLayouts: intercept.__loadInterceptLayouts,
				__loadInterceptLoadings: intercept.__loadInterceptLoadings,
				page: intercept.page,
				__pageLoader: intercept.__pageLoader,
				notFound: intercept.notFound,
				__loadNotFound: intercept.__loadNotFound,
				notFoundTreePosition: intercept.notFoundTreePosition,
				__loadState: {
					page: intercept.page,
					pageLoading: null,
					notFound: intercept.notFound,
					notFoundLoading: null,
					interceptLayoutsLoading: null
				},
				params: intercept.params
			});
		}
	}
	return interceptLookup.sort(compareInterceptTargetPatterns);
}
function mergeMatchedParams(sourceParams, targetParams) {
	return Object.assign(createRouteParams(), sourceParams, targetParams);
}
function pickPatternParams(params, patternParts) {
	const picked = createRouteParams();
	for (const patternPart of patternParts) {
		if (!patternPart.startsWith(":")) continue;
		const paramName = patternPart.endsWith("+") || patternPart.endsWith("*") ? patternPart.slice(1, -1) : patternPart.slice(1);
		const value = params[paramName];
		if (value !== void 0) picked[paramName] = value;
	}
	return picked;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-boundary.js
function resolveAppPageHttpAccessBoundaryModule(options) {
	let boundaryModule;
	if (options.statusCode === 403) boundaryModule = options.routeForbiddenModule ?? options.rootForbiddenModule;
	else if (options.statusCode === 401) boundaryModule = options.routeUnauthorizedModule ?? options.rootUnauthorizedModule;
	else boundaryModule = options.routeNotFoundModule ?? options.rootNotFoundModule;
	return boundaryModule ?? null;
}
function resolveAppPageParentHttpAccessBoundaryModule(options) {
	return resolveAppPageParentHttpAccessBoundary(options).module;
}
/**
* Like {@link resolveAppPageParentHttpAccessBoundaryModule}, but also returns
* the layout index that owns the resolved boundary so callers can slice the
* layouts array to skip rendering layouts below the boundary owner.
*
* `layoutIndex` is the per-layout index where the boundary lives, or `null` if
* the resolved boundary is the root module (which conceptually sits above all
* layouts when no layout-level boundary is present).
*
* Used by the page-error fast path to make `forbidden()` / `unauthorized()` /
* `notFound()` escalate past intermediate layouts that lack a boundary file,
* matching Next.js's `create-component-tree.tsx` behavior where the nearest
* ancestor boundary owns the fallback subtree.
*
* @see https://github.com/vercel/next.js/blob/canary/packages/next/src/server/app-render/create-component-tree.tsx
*/
function resolveAppPageParentHttpAccessBoundary(options) {
	let routeModules = options.routeNotFoundModules;
	let rootModule = options.rootNotFoundModule;
	if (options.statusCode === 403) {
		routeModules = options.routeForbiddenModules;
		rootModule = options.rootForbiddenModule;
	} else if (options.statusCode === 401) {
		routeModules = options.routeUnauthorizedModules;
		rootModule = options.rootUnauthorizedModule;
	}
	if (routeModules) for (let index = options.layoutIndex - 1; index >= 0; index--) {
		const module = routeModules[index];
		if (module) return {
			module,
			layoutIndex: index
		};
	}
	return {
		module: rootModule ?? null,
		layoutIndex: null
	};
}
function resolveAppPageErrorBoundary(options) {
	const pageErrorComponent = options.getDefaultExport(options.pageErrorModule);
	if (pageErrorComponent) return {
		component: pageErrorComponent,
		isGlobalError: false
	};
	const segmentErrorModules = options.errorModules ?? options.layoutErrorModules;
	if (segmentErrorModules) for (let index = segmentErrorModules.length - 1; index >= 0; index--) {
		const segmentErrorComponent = options.getDefaultExport(segmentErrorModules[index]);
		if (segmentErrorComponent) return {
			component: segmentErrorComponent,
			isGlobalError: false
		};
	}
	const globalErrorComponent = options.getDefaultExport(options.globalErrorModule);
	return {
		component: globalErrorComponent ?? null,
		isGlobalError: Boolean(globalErrorComponent)
	};
}
function wrapAppPageBoundaryElement(options) {
	let element = options.element;
	if (!options.skipLayoutWrapping) for (let index = options.layoutModules.length - 1; index >= 0; index--) {
		const layoutComponent = options.getDefaultExport(options.layoutModules[index]);
		if (!layoutComponent) continue;
		const treePosition = options.layoutTreePositions ? options.layoutTreePositions[index] : 0;
		const asyncParams = options.makeThenableParams(resolveAppPageSegmentParams(options.routeSegments, treePosition, options.matchedParams));
		element = options.renderLayout(layoutComponent, element, asyncParams);
		if (options.isRscRequest && options.renderLayoutSegmentProvider && options.resolveChildSegments) {
			const childSegments = options.resolveChildSegments(options.routeSegments ?? [], treePosition, options.matchedParams);
			element = options.renderLayoutSegmentProvider({ children: childSegments }, element);
		}
	}
	if (options.isRscRequest && options.includeGlobalErrorBoundary && options.globalErrorComponent) element = options.renderErrorBoundary(options.globalErrorComponent, element);
	return element;
}
async function renderAppPageBoundaryResponse(options) {
	const rscStream = runWithFetchDedupe(() => options.renderToReadableStream(options.element, { onError: options.createRscOnErrorHandler() }));
	if (options.isRscRequest) {
		const headers = new Headers({
			"Content-Type": VINEXT_RSC_CONTENT_TYPE,
			Vary: VINEXT_RSC_VARY_HEADER
		});
		applyEdgeRuntimeHeader(headers, options.isEdgeRuntime);
		mergeMiddlewareResponseHeaders(headers, options.middlewareHeaders ?? null);
		applyRscCompatibilityIdHeader(headers);
		applyRscDeploymentIdHeader(headers);
		return new Response(rscStream, {
			status: options.status,
			headers
		});
	}
	return options.createHtmlResponse(rscStream, options.status);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-element-builder.js
function resolveInterceptLayoutParams(branchSegments, layoutSegments, params) {
	return resolveAppPageBranchParams(branchSegments, layoutSegments.length, params, layoutSegments);
}
/**
* Build the App Router element tree for a matched route.
*
* This is the central element-construction path for the App Router RSC
* handler. It resolves page head metadata (including parallel route metadata),
* creates the page React element, and wires it into the nested layout +
* boundary tree via {@link buildAppPageElements}.
*
* The function is extracted from the generated RSC entry template so it can
* be unit-tested independently of the code-generation machinery.
*
* Next.js equivalent: the component tree construction in
* {@link https://github.com/vercel/next.js/blob/canary/packages/next/src/server/app-render/create-component-tree.tsx|create-component-tree.tsx}
* and the page head resolution in
* {@link https://github.com/vercel/next.js/blob/canary/packages/next/src/server/app-render/create-metadata.tsx|create-metadata.tsx}.
*/
async function buildPageElements$1(options) {
	const { route, params, routePath, displayPathname = routePath, pageRequest, globalErrorModule, rootNotFoundModule, rootForbiddenModule, rootUnauthorizedModule, metadataRoutes } = options;
	const slotParamOverrides = resolveSlotParamOverrides(route, routePath);
	const { opts, searchParams, isRscRequest, mountedSlotsHeader, renderMode = APP_RSC_RENDER_MODE_NAVIGATION, observeMetadataSearchParamsAccess = false, observePageSearchParamsAccess = false, serveStreamingMetadata, isProduction = true } = pageRequest;
	const pageModule = route.page;
	const isSiblingIntercept = opts?.interceptSlotKey === "__vinext_page_intercept" && !!opts?.interceptPage;
	const effectivePageModule = isSiblingIntercept ? opts.interceptPage : pageModule;
	const EffectivePageComponent = effectivePageModule?.default;
	const effectiveParams = isSiblingIntercept ? opts.interceptParams ?? params : params;
	const sourcePageSegments = isSiblingIntercept ? opts?.interceptSourcePageSegments : route.routeSegments;
	const semanticPageIdentity = isSiblingIntercept ? route.ids?.route && opts?.interceptGraphId && opts.interceptTargetPatternParts ? {
		boundSegmentKey: resolveAppPagePatternStateKey(opts.interceptTargetPatternParts, effectiveParams),
		interceptionGraphId: opts.interceptGraphId,
		sourceBoundSegmentKey: resolveAppPageRouteStateKey(route.routeSegments ?? [], params),
		sourceRouteGraphId: route.ids.route
	} : null : void 0;
	const hasPageModule = !!pageModule;
	const renderIdentity = createAppPageRenderIdentity({
		displayPathname,
		matchedRoutePathname: routePath,
		targetMatchedPathname: routePath,
		interceptionContext: opts?.interceptionContext ?? null,
		interceptSourceMatchedUrl: opts?.interceptSourceMatchedUrl ?? null,
		interceptSlotId: isSiblingIntercept ? null : opts?.interceptSlotId ?? null
	});
	if ((hasPageModule || isSiblingIntercept) && !EffectivePageComponent) {
		let noExportRootLayout = null;
		const noExportLayoutIds = route.layouts.map((_, index) => AppElementsWire.encodeLayoutId(createAppPageTreePath(route.routeSegments, route.layoutTreePositions?.[index] ?? 0)));
		if (route.layouts?.length > 0) {
			const treePosition = route.layoutTreePositions?.[0] ?? 0;
			noExportRootLayout = createAppPageTreePath(route.routeSegments, treePosition);
		}
		return {
			...AppElementsWire.createMetadataEntries({
				interception: renderIdentity.interception,
				interceptionContext: renderIdentity.interceptionContext,
				layoutIds: noExportLayoutIds,
				rootLayoutTreePath: noExportRootLayout,
				routeId: renderIdentity.routeId,
				sourcePage: createAppPageSourcePage(sourcePageSegments)
			}),
			[renderIdentity.routeId]: (0, import_react_react_server.createElement)("div", null, "Page has no default export")
		};
	}
	const activeParallelRouteHeadInputs = resolveActiveParallelRouteHeadInputs({
		interceptBranchSegments: opts?.interceptBranchSegments ?? null,
		interceptLayouts: opts?.interceptLayouts ?? null,
		interceptLayoutSegments: opts?.interceptLayoutSegments ?? null,
		interceptNotFoundBranchSegments: opts?.interceptNotFoundBranchSegments ?? null,
		interceptNotFound: opts?.interceptNotFound ?? null,
		interceptNotFoundTreePosition: opts?.interceptNotFoundTreePosition ?? null,
		interceptPage: opts?.interceptPage ?? null,
		interceptParams: opts?.interceptParams ?? null,
		interceptSlotKey: opts?.interceptSlotKey ?? null,
		interceptSourcePageSegments: opts?.interceptSourcePageSegments ?? null,
		layoutTreePositions: route.layoutTreePositions,
		params,
		routeSegments: route.routeSegments ?? [],
		slotParams: slotParamOverrides,
		slots: route.slots ?? null
	});
	const primaryParallelRouteHeadInput = isSiblingIntercept ? {
		head: {
			layoutModules: opts?.interceptLayouts ?? [],
			layoutParams: (opts?.interceptLayoutSegments ?? []).map((segments) => resolveInterceptLayoutParams(opts?.interceptBranchSegments ?? segments, segments, effectiveParams)),
			pageModule: effectivePageModule ?? null,
			params: effectiveParams,
			routeSegments: opts?.interceptSourcePageSegments ?? route.routeSegments ?? []
		},
		...opts?.interceptNotFound ? {
			notFoundModule: opts.interceptNotFound,
			notFoundParams: resolveAppPageBranchParams(opts.interceptNotFoundBranchSegments ?? opts.interceptBranchSegments ?? route.routeSegments ?? [], opts.interceptNotFoundTreePosition ?? 0, effectiveParams)
		} : {},
		ownerTreePosition: route.routeSegments?.length ?? 0
	} : null;
	const parallelRoutes = [...primaryParallelRouteHeadInput ? [primaryParallelRouteHeadInput.head] : [], ...activeParallelRouteHeadInputs.map((input) => input.head)];
	const metadataSearchParamsObserver = observeMetadataSearchParamsAccess ? createAppPageSearchParamsObserver() : void 0;
	const preparedHead = prepareAppPageHead({
		applyFileBasedMetadata: options.applyFileBasedMetadata,
		basePath: options.basePath ?? "",
		layoutModules: route.layouts,
		layoutTreePositions: route.layoutTreePositions,
		metadataRoutes,
		pageModule: isSiblingIntercept ? null : effectivePageModule ?? null,
		parallelRoutes,
		params: effectiveParams,
		routePath: route.pattern,
		routeSegments: route.routeSegments ?? null,
		searchParams,
		searchParamsObserver: metadataSearchParamsObserver
	});
	const { hasDynamicMetadata, pageSearchParams } = preparedHead;
	const streamGeneratedHead = serveStreamingMetadata ?? shouldServeStreamingMetadata(pageRequest.request.headers.get("user-agent") ?? "", options.htmlLimitedBots);
	const metadataPlacement = hasDynamicMetadata && streamGeneratedHead ? "body" : "head";
	const shouldDeferMetadata = metadataPlacement === "body";
	const streamingMetadata = shouldDeferMetadata ? isProduction ? preparedHead.metadata.catch((error) => {
		throw sanitizeErrorForClient(error, "production");
	}) : preparedHead.metadata : null;
	streamingMetadata?.catch(() => null);
	const resolveNotFoundFallbackPlanOptions = () => {
		const routeBoundaryModule = route.notFound;
		const parentBoundary = resolveAppPageParentHttpAccessBoundary({
			layoutIndex: route.layouts.length,
			rootForbiddenModule,
			rootNotFoundModule,
			rootUnauthorizedModule,
			routeForbiddenModules: route.forbiddens,
			routeNotFoundModules: route.notFounds,
			routeUnauthorizedModules: route.unauthorizeds,
			statusCode: 404
		});
		const boundaryModule = routeBoundaryModule ?? parentBoundary.module;
		const boundaryTreePosition = routeBoundaryModule ? route.notFoundTreePosition : parentBoundary.layoutIndex === null ? null : route.layoutTreePositions?.[parentBoundary.layoutIndex];
		return {
			boundaryModule,
			boundaryParams: boundaryModule && boundaryTreePosition != null ? resolveAppPageSegmentParams(route.routeSegments ?? [], boundaryTreePosition, effectiveParams) : {},
			layoutModules: route.layouts,
			layoutTreePositions: route.layoutTreePositions,
			parallelBranches: activeParallelRouteHeadInputs,
			params: effectiveParams,
			primaryParallelBranch: primaryParallelRouteHeadInput,
			routeSegments: route.routeSegments ?? null
		};
	};
	let viewportErrorOutlet = null;
	let metadataErrorOutlet = null;
	const resolveMetadataErrorTags = async (error) => {
		if (resolveAppPageSpecialError(error)?.kind !== "http-access-fallback") return null;
		return resolveHttpAccessFallbackMetadata({
			applyFileBasedMetadata: options.applyFileBasedMetadata,
			basePath: options.basePath ?? "",
			...resolveNotFoundFallbackPlanOptions(),
			metadataRoutes,
			routePath: route.pattern
		}).catch(() => null);
	};
	const [resolvedMetadata, resolvedViewport] = await Promise.all([shouldDeferMetadata ? Promise.resolve(null) : preparedHead.metadata.catch((error) => {
		metadataErrorOutlet = Promise.reject(isProduction ? sanitizeErrorForClient(error, "production") : error);
		metadataErrorOutlet.catch(() => null);
		return resolveMetadataErrorTags(error);
	}), preparedHead.viewport.catch(async (error) => {
		const specialError = resolveAppPageSpecialError(error);
		viewportErrorOutlet = Promise.reject(isProduction ? sanitizeErrorForClient(error, "production") : error);
		viewportErrorOutlet.catch(() => null);
		return specialError?.kind === "http-access-fallback" ? resolveHttpAccessFallbackViewport(resolveNotFoundFallbackPlanOptions()).catch(() => ({})) : {};
	})]);
	const streamingMetadataTags = shouldDeferMetadata ? preparedHead.metadata.catch(resolveMetadataErrorTags) : null;
	const streamingMetadataOutletInputs = [
		streamingMetadata,
		metadataErrorOutlet,
		viewportErrorOutlet
	].filter((promise) => promise !== null).map((promise) => Promise.resolve(promise));
	const streamingMetadataOutlet = streamingMetadataOutletInputs.length > 0 ? Promise.all(streamingMetadataOutletInputs).then(() => null) : null;
	streamingMetadataOutlet?.catch(() => null);
	const pageProps = { params: makeThenableParams(effectiveParams) };
	const hasRequestSearchParams = Object.keys(pageSearchParams).length > 0;
	const pageTreePosition = (sourcePageSegments ?? route.routeSegments ?? []).length;
	const hasPageLoadingBoundary = resolveAppPageLoadingModuleAtOrAbove(route, pageTreePosition) !== null || isSiblingIntercept && resolveAppPageLoadingModuleAtOrAbove({
		loading: null,
		loadings: opts?.interceptLoadings,
		loadingTreePositions: opts?.interceptLoadingTreePositions
	}, pageTreePosition) !== null;
	const pageRenderDependency = EffectivePageComponent && !isReactOwnedAppComponent(EffectivePageComponent) ? createAppPageRenderDependency() : null;
	const createPageElement = (PageComponent, props, renderDependency) => {
		if (isReactOwnedAppComponent(PageComponent)) {
			const invocationProps = { ...props };
			if (searchParams) invocationProps.searchParams = observePageSearchParamsAccess ? makeObservedAppPageSearchParamsThenable(pageSearchParams, { markDynamic: hasRequestSearchParams }) : makeThenableParams(pageSearchParams);
			return (0, import_react_react_server.createElement)(PageComponent, invocationProps);
		}
		const PageInvoker = () => {
			const invocationProps = { ...props };
			if (searchParams) invocationProps.searchParams = observePageSearchParamsAccess ? makeObservedAppPageSearchParamsThenable(pageSearchParams) : makeThenableParams(pageSearchParams);
			try {
				const result = invokeAppComponent(PageComponent, invocationProps);
				if (isPromiseLike(result)) {
					if (renderDependency) Promise.resolve().then(() => renderDependency.release());
					return Promise.resolve(result).then((resolvedResult) => renderDependency ? renderAfterAppDependencies(resolvedResult, renderDependency.resultDependencies) : resolvedResult);
				}
				renderDependency?.release();
				return renderDependency ? renderAfterAppDependencies(result, renderDependency.resultDependencies) : result;
			} catch (error) {
				if (isAppRenderSuspension(error)) {
					if (renderDependency && hasPageLoadingBoundary) Promise.resolve().then(() => renderDependency.release());
					throw error;
				}
				renderDependency?.release();
				throw error;
			}
		};
		return (0, import_react_react_server.createElement)(PageInvoker);
	};
	const pageSearchParamsThenable = searchParams ? makeThenableParams(pageSearchParams) : void 0;
	const mountedSlotIds = mountedSlotsHeader ? new Set(mountedSlotsHeader.split(" ")) : null;
	const slotOverrides = buildSlotOverrides(route, params, routePath, opts);
	let siblingInterceptElement = isSiblingIntercept && EffectivePageComponent ? createPageElement(EffectivePageComponent, pageProps, pageRenderDependency) : null;
	if (isSiblingIntercept && siblingInterceptElement !== null) {
		const layoutIndexesByTreePosition = /* @__PURE__ */ new Map();
		for (const [index, layoutModule] of (opts?.interceptLayouts ?? []).entries()) {
			if (!layoutModule?.default) continue;
			const treePosition = opts?.interceptLayoutSegments?.[index]?.length ?? 0;
			const indexes = layoutIndexesByTreePosition.get(treePosition) ?? [];
			indexes.push(index);
			layoutIndexesByTreePosition.set(treePosition, indexes);
		}
		const loadingIndexesByTreePosition = /* @__PURE__ */ new Map();
		for (const [index, loadingModule] of (opts?.interceptLoadings ?? []).entries()) {
			if (!loadingModule?.default) continue;
			const treePosition = opts?.interceptLoadingTreePositions?.[index];
			if (treePosition !== void 0) loadingIndexesByTreePosition.set(treePosition, index);
		}
		const treePositions = Array.from(/* @__PURE__ */ new Set([...layoutIndexesByTreePosition.keys(), ...loadingIndexesByTreePosition.keys()])).sort((left, right) => left - right);
		for (let index = treePositions.length - 1; index >= 0; index--) {
			const treePosition = treePositions[index];
			const loadingIndex = loadingIndexesByTreePosition.get(treePosition);
			const LoadingComponent = loadingIndex === void 0 ? null : opts?.interceptLoadings?.[loadingIndex]?.default;
			if (LoadingComponent) siblingInterceptElement = (0, import_react_react_server.createElement)(import_react_react_server.Suspense, { fallback: (0, import_react_react_server.createElement)(LoadingComponent) }, siblingInterceptElement);
			const layoutIndexes = layoutIndexesByTreePosition.get(treePosition) ?? [];
			for (let layoutOffset = layoutIndexes.length - 1; layoutOffset >= 0; layoutOffset--) {
				const layoutIndex = layoutIndexes[layoutOffset];
				const LayoutComponent = opts?.interceptLayouts?.[layoutIndex]?.default;
				if (!LayoutComponent) continue;
				const interceptLayoutSegments = opts?.interceptLayoutSegments?.[layoutIndex] ?? [];
				siblingInterceptElement = (0, import_react_react_server.createElement)(LayoutComponent, { params: makeThenableParams(resolveInterceptLayoutParams(opts?.interceptBranchSegments ?? interceptLayoutSegments, interceptLayoutSegments, effectiveParams)) }, siblingInterceptElement);
			}
		}
	}
	return buildAppPageElements({
		element: isSiblingIntercept ? siblingInterceptElement : EffectivePageComponent ? createPageElement(EffectivePageComponent, pageProps, pageRenderDependency) : null,
		createPageElement,
		globalErrorModule: globalErrorModule ?? DEFAULT_GLOBAL_ERROR_MODULE,
		isRscRequest,
		layoutParamAccess: options.layoutParamAccess,
		mountedSlotIds,
		makeThenableParams,
		matchedParams: params,
		pageRenderDependency,
		metadataPlacement,
		resolvedMetadata,
		resolvedMetadataPathname: routePath,
		resolvedViewport,
		scriptNonce: options.scriptNonce,
		streamingMetadata,
		streamingMetadataOutlet,
		streamingMetadataOutletSuspended: streamGeneratedHead,
		streamingMetadataTags,
		renderIdentity,
		routePath,
		semanticPageIdentity,
		semanticInterceptionTargetRouteId: opts?.interceptTargetRouteGraphId ?? null,
		sourcePageSegments,
		rootNotFoundModule: rootNotFoundModule ?? null,
		rootForbiddenModule: rootForbiddenModule ?? null,
		rootUnauthorizedModule: rootUnauthorizedModule ?? null,
		route,
		searchParams: pageSearchParamsThenable,
		slotOverrides,
		renderMode,
		trailingSlash: options.trailingSlash
	});
}
/**
* Build the per-request `slotOverrides` map. Combines:
*  - Interception overrides (existing behavior — swap in the intercepting page
*    and its layouts when the request is intercepted into this slot).
*  - Slot-specific param extraction for inherited slots whose URL pattern
*    has different param names than the route's. The runtime matches the
*    cleaned request path against `slot.slotPatternParts` to produce
*    slot-scoped params, which `app-page-route-wiring` then hands to the
*    slot page instead of the route's matched params.
*
* `routePath` is the already-normalized request pathname (basePath stripped,
* RSC suffix removed). Re-parsing `request.url` here would re-introduce the
* basePath and silently break the match for any app that configures one.
*/
function buildSlotOverrides(route, routeParams, routePath, opts) {
	const overrides = {};
	if (opts && opts.interceptSlotKey && opts.interceptPage && opts.interceptSlotKey !== "__vinext_page_intercept") overrides[opts.interceptSlotKey] = {
		branchSegments: opts.interceptBranchSegments ?? null,
		identitySegments: resolveInterceptedSlotIdentitySegments(opts.interceptSourcePageSegments, opts.interceptSlotKey),
		layoutModules: opts.interceptLayouts || null,
		layoutSegments: opts.interceptLayoutSegments ?? null,
		loadingModules: opts.interceptLoadings || null,
		loadingTreePositions: opts.interceptLoadingTreePositions ?? null,
		pageModule: opts.interceptPage,
		params: opts.interceptParams || routeParams,
		routeSegments: resolveInterceptedSlotSegments(opts.interceptSourcePageSegments, opts.interceptSlotKey)
	};
	const slotParamOverrides = resolveSlotParamOverrides(route, routePath);
	for (const [slotKey, params] of Object.entries(slotParamOverrides ?? {})) {
		const existing = overrides[slotKey];
		overrides[slotKey] = existing ? {
			...existing,
			params: existing.params ?? params
		} : { params };
	}
	return Object.keys(overrides).length > 0 ? overrides : null;
}
var APP_PAGE_INTERCEPTION_MARKER_TRAVERSALS = [
	{
		prefix: "(...)",
		levels: Number.POSITIVE_INFINITY
	},
	{
		prefix: "(..)(..)",
		levels: 2
	},
	{
		prefix: "(..)",
		levels: 1
	},
	{
		prefix: "(.)",
		levels: 0
	}
];
function resolveInterceptedSlotSource(sourcePageSegments, slotKey) {
	if (!sourcePageSegments) return null;
	const slotPathSeparator = slotKey.indexOf("@");
	const ownerSegments = (slotPathSeparator >= 0 ? slotKey.slice(slotPathSeparator + 1) : "").split("/").filter(Boolean);
	let segmentStart = ownerSegments.length;
	if (segmentStart === 0 || !ownerSegments.every((segment, index) => sourcePageSegments[index] === segment)) {
		let slotName = null;
		for (let index = ownerSegments.length - 1; index >= 0; index--) if (ownerSegments[index].startsWith("@")) {
			slotName = ownerSegments[index];
			break;
		}
		let slotIndex = -1;
		if (slotName) for (let index = sourcePageSegments.length - 1; index >= 0; index--) {
			const hasOwnedMarker = sourcePageSegments.slice(index + 1).some((segment) => APP_PAGE_INTERCEPTION_MARKER_TRAVERSALS.some(({ prefix }) => segment.startsWith(prefix)));
			if (sourcePageSegments[index] === slotName && hasOwnedMarker) {
				slotIndex = index;
				break;
			}
		}
		if (slotIndex < 0) return null;
		segmentStart = slotIndex + 1;
	}
	const markerOffset = sourcePageSegments.slice(segmentStart).findIndex((segment) => APP_PAGE_INTERCEPTION_MARKER_TRAVERSALS.some(({ prefix }) => segment.startsWith(prefix)));
	if (markerOffset < 0) return null;
	const markerIndex = segmentStart + markerOffset;
	const markerSegment = sourcePageSegments[markerIndex];
	const marker = APP_PAGE_INTERCEPTION_MARKER_TRAVERSALS.find(({ prefix }) => markerSegment.startsWith(prefix));
	return marker ? {
		marker,
		markerIndex,
		segmentStart
	} : null;
}
function isInterceptedSlotIdentitySegment(segment) {
	return !segment.startsWith("@");
}
function isVisibleInterceptedSlotSegment(segment) {
	return isInterceptedSlotIdentitySegment(segment) && !isAppPageRouteGroupSegment(segment);
}
/**
* Resolve the slot's semantic branch: the segments that give the intercepted
* slot its identity, with the interception marker split off and each segment
* already bound to the param map that owns it (the route's params up to the
* marker, the slot's params from the marker on).
*/
function resolveInterceptedSlotIdentitySegments(sourcePageSegments, slotKey) {
	const source = resolveInterceptedSlotSource(sourcePageSegments, slotKey);
	if (!source || !sourcePageSegments) return null;
	const semanticSegments = [];
	let beforeMarker = true;
	for (let index = source.segmentStart; index < sourcePageSegments.length; index++) {
		const segment = sourcePageSegments[index];
		if (!isInterceptedSlotIdentitySegment(segment)) continue;
		const isMarkerSegment = index === source.markerIndex;
		semanticSegments.push({
			marker: isMarkerSegment ? source.marker.prefix : null,
			paramSource: beforeMarker && !isMarkerSegment ? "route" : "slot",
			segment: isMarkerSegment ? segment.slice(source.marker.prefix.length) : segment
		});
		if (isMarkerSegment) beforeMarker = false;
	}
	return semanticSegments;
}
function resolveInterceptedSlotSegments(sourcePageSegments, slotKey) {
	const source = resolveInterceptedSlotSource(sourcePageSegments, slotKey);
	if (!source || !sourcePageSegments) return null;
	const { marker, markerIndex, segmentStart } = source;
	const routeSegments = sourcePageSegments.slice(segmentStart, markerIndex).filter(isVisibleInterceptedSlotSegment);
	const markerSegment = sourcePageSegments[markerIndex];
	if (Number.isFinite(marker.levels)) routeSegments.splice(Math.max(0, routeSegments.length - marker.levels), marker.levels);
	else routeSegments.length = 0;
	const targetSegment = markerSegment.slice(marker.prefix.length);
	if (targetSegment) routeSegments.push(targetSegment);
	routeSegments.push(...sourcePageSegments.slice(markerIndex + 1).filter(isVisibleInterceptedSlotSegment));
	return routeSegments;
}
function resolveSlotParamOverrides(route, routePath) {
	const overrides = {};
	const slots = route.slots;
	if (slots) {
		let urlParts = null;
		const routeParamSet = collectParamNameSet(route.params);
		for (const [slotKey, slot] of Object.entries(slots)) {
			const patternParts = slot.slotPatternParts;
			const paramNames = slot.slotParamNames;
			if (!patternParts || patternParts.length === 0) continue;
			if (paramNames && paramNames.every((name) => routeParamSet.has(name))) continue;
			if (urlParts === null) urlParts = routePath.split("/").filter(Boolean);
			const matched = matchRoutePattern(urlParts, patternParts);
			if (!matched) continue;
			overrides[slotKey] = matched;
		}
	}
	return Object.keys(overrides).length > 0 ? overrides : null;
}
function mergeAppPageParams(target, source) {
	for (const [key, value] of Object.entries(source)) target[key] = value;
}
function isDefaultExportModule(module) {
	return typeof module === "object" && module !== null;
}
function hasDefaultExport(module) {
	if (!isDefaultExportModule(module)) return false;
	return module?.default !== null && module?.default !== void 0;
}
function resolveAppPageNavigationParams(route, routeParams, routePath, opts) {
	const navigationParams = { ...routeParams };
	const slotParamOverrides = resolveSlotParamOverrides(route, routePath);
	for (const [slotKey, slot] of Object.entries(route.slots ?? {})) {
		const isInterceptedSlot = opts?.interceptSlotKey === slotKey && opts.interceptSlotKey !== "__vinext_page_intercept" && hasDefaultExport(opts.interceptPage);
		if (!isInterceptedSlot && !hasDefaultExport(slot.page) && !hasDefaultExport(slot.default)) continue;
		mergeAppPageParams(navigationParams, isInterceptedSlot ? opts?.interceptParams ?? routeParams : slotParamOverrides?.[slotKey] ?? routeParams);
	}
	return navigationParams;
}
function collectParamNameSet(params) {
	const set = /* @__PURE__ */ new Set();
	if (params) for (const name of params) set.add(name);
	return set;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/defer-until-stream-consumed.js
/**
* Defers cleanup until the downstream consumer drains or cancels the stream.
*/
function deferUntilStreamConsumed(stream, onFlush) {
	let called = false;
	const once = () => {
		if (!called) {
			called = true;
			onFlush();
		}
	};
	const cleanup = new TransformStream({ flush() {
		once();
	} });
	const reader = stream.pipeThrough(cleanup).getReader();
	return new ReadableStream({
		pull(controller) {
			return reader.read().then(({ done, value }) => {
				if (done) controller.close();
				else controller.enqueue(value);
			}, (error) => {
				once();
				controller.error(error);
			});
		},
		cancel(reason) {
			once();
			return reader.cancel(reason);
		}
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-stream.js
function isAppSsrRenderResult(value) {
	return typeof value === "object" && value !== null && "htmlStream" in value && "metadataReady" in value;
}
var resolvedMetadataReady = Promise.resolve();
function normalizeAppSsrRenderResult(raw, fallbackCapturedRscData = null) {
	if (isAppSsrRenderResult(raw)) return raw;
	return {
		htmlStream: raw,
		metadataReady: resolvedMetadataReady,
		capturedRscData: fallbackCapturedRscData,
		shellErrorRecovered: false
	};
}
/**
* Combine the React-emitted preload `Link` header with vinext's font preload
* `Link` header, capping the result to `reactMaxHeadersLength`.
*
* React already caps its own portion, but vinext emits font preloads through a
* separate channel. Mirroring Next.js — where every preload flows through a
* single capped `onHeaders` callback — we cap the *combined* header here,
* keeping only whole entries that fit and dropping the rest once the limit is
* exceeded. `0` disables emission entirely (matches React); `undefined` falls
* back to the React default of 6000.
*
* React's hints (scripts/modules/styles) come first so that under a tight cap
* the render-critical entries survive and trailing font preloads are dropped
* first.
*/
function buildAppPageLinkHeader(reactLinkHeader, fontLinkHeader, maxHeadersLength) {
	const limit = typeof maxHeadersLength === "number" ? maxHeadersLength : 6e3;
	if (limit <= 0) return "";
	const entries = [];
	for (const source of [reactLinkHeader, fontLinkHeader]) {
		if (!source) continue;
		for (const entry of source.split(", ")) if (entry.length > 0) entries.push(entry);
	}
	let header = "";
	for (const entry of entries) {
		const next = header.length === 0 ? entry : `${header}, ${entry}`;
		if (next.length > limit) break;
		header = next;
	}
	return header;
}
function createAppPageFontData(options) {
	return {
		links: options.getLinks(),
		preloads: options.getPreloads(),
		styles: options.getStyles()
	};
}
async function renderAppPageHtmlStream(options) {
	const ssrOptions = {
		formState: options.formState ?? null,
		scriptNonce: options.scriptNonce,
		basePath: options.basePath,
		clientTraceMetadata: options.clientTraceMetadata,
		reactMaxHeadersLength: options.reactMaxHeadersLength,
		rootParams: options.rootParams,
		sideStream: options.sideStream,
		capturedRscDataRef: options.capturedRscDataRef,
		pprFallbackShellSignal: options.pprFallbackShellSignal,
		waitForAllReady: options.waitForAllReady,
		initialDevServerError: options.initialDevServerError,
		fallbackToErrorDocumentOnShellError: options.fallbackToErrorDocumentOnShellError ?? (options.waitForAllReady !== true && options.hasCustomGlobalError === false),
		dynamicStaleTimeSeconds: options.dynamicStaleTimeSeconds,
		getInitialNavigationCacheMetadata: options.getInitialNavigationCacheMetadata
	};
	return normalizeAppSsrRenderResult(await options.ssrHandler.handleSsr(options.rscStream, options.navigationContext, options.fontData, ssrOptions), options.capturedRscDataRef?.value ?? null);
}
async function renderAppPageHtmlResponse(options) {
	const { htmlStream } = await renderAppPageHtmlStream(options);
	const safeStream = deferUntilStreamConsumed(htmlStream, () => {
		options.clearRequestContext();
	});
	const headers = new Headers({
		"Content-Type": "text/html; charset=utf-8",
		Vary: VINEXT_RSC_VARY_HEADER
	});
	applyEdgeRuntimeHeader(headers, options.isEdgeRuntime);
	if (options.fontLinkHeader) headers.set("Link", options.fontLinkHeader);
	mergeMiddlewareResponseHeaders(headers, options.middlewareHeaders ?? null);
	return new Response(safeStream, {
		status: options.status,
		headers
	});
}
async function renderAppPageHtmlStreamWithRecovery(options) {
	try {
		const { htmlStream, metadataReady, capturedRscData, linkHeader, shellErrorRecovered } = normalizeAppSsrRenderResult(await options.renderHtmlStream());
		options.onShellRendered?.();
		return {
			htmlStream,
			response: null,
			metadataReady,
			capturedRscData,
			shellErrorRecovered: shellErrorRecovered === true,
			linkHeader
		};
	} catch (error) {
		const specialError = options.resolveSpecialError(error);
		if (specialError) return {
			htmlStream: null,
			response: await options.renderSpecialErrorResponse(specialError),
			metadataReady: resolvedMetadataReady,
			capturedRscData: null,
			shellErrorRecovered: false
		};
		const boundaryResponse = await options.renderErrorBoundaryResponse(error);
		if (boundaryResponse) return {
			htmlStream: null,
			response: boundaryResponse,
			metadataReady: resolvedMetadataReady,
			capturedRscData: null,
			shellErrorRecovered: false
		};
		throw error;
	}
}
function createAppPageRscErrorTracker(baseOnError) {
	let capturedError = null;
	let capturedSpecialError = null;
	return {
		getCapturedError() {
			return capturedError;
		},
		getCapturedSpecialError() {
			return capturedSpecialError;
		},
		onRenderError(error, requestInfo, errorContext) {
			if (isNavigationSignalError(error)) {
				if (capturedSpecialError === null) capturedSpecialError = error;
			} else capturedError = error;
			return baseOnError(error, requestInfo, errorContext);
		}
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-boundary-render.js
var DEFAULT_GLOBAL_ERROR_COMPONENT = default_global_error_default;
function getDefaultExport(module) {
	return module?.default ?? null;
}
function resolveHttpAccessBoundaryTreePosition(route, boundaryModule, statusCode) {
	if (!route || !boundaryModule) return null;
	const routeBoundary = statusCode === 403 ? route.forbidden : statusCode === 401 ? route.unauthorized : route.notFound;
	const layoutBoundaries = statusCode === 403 ? route.forbiddens : statusCode === 401 ? route.unauthorizeds : route.notFounds;
	if (boundaryModule === routeBoundary && statusCode === 404) return route.notFoundTreePosition ?? null;
	if (boundaryModule === routeBoundary && statusCode === 403) return route.forbiddenTreePosition ?? null;
	if (boundaryModule === routeBoundary && statusCode === 401) return route.unauthorizedTreePosition ?? null;
	for (let index = (layoutBoundaries?.length ?? 0) - 1; index >= 0; index--) if (layoutBoundaries?.[index] === boundaryModule) return route.layoutTreePositions?.[index] ?? null;
	return null;
}
function wrapRenderedBoundaryElement(options) {
	return wrapAppPageBoundaryElement({
		element: options.element,
		getDefaultExport,
		globalErrorComponent: getDefaultExport(options.globalErrorModule),
		includeGlobalErrorBoundary: options.includeGlobalErrorBoundary,
		isRscRequest: options.isRscRequest,
		layoutModules: options.layoutModules,
		layoutTreePositions: options.layoutTreePositions,
		makeThenableParams: options.makeThenableParams,
		matchedParams: options.matchedParams,
		renderErrorBoundary(GlobalErrorComponent, children) {
			return (0, import_react_react_server.createElement)(GlobalErrorBoundary, {
				fallback: DEFAULT_GLOBAL_ERROR_COMPONENT,
				children: (0, import_react_react_server.createElement)(ErrorBoundary, {
					fallback: GlobalErrorComponent,
					children
				})
			});
		},
		renderLayout(LayoutComponent, children, asyncParams) {
			return (0, import_react_react_server.createElement)(LayoutComponent, {
				children,
				params: asyncParams
			});
		},
		renderLayoutSegmentProvider(segmentMap, children) {
			return (0, import_react_react_server.createElement)(LayoutSegmentProvider, { segmentMap }, children);
		},
		resolveChildSegments: options.resolveChildSegments,
		routeSegments: options.routeSegments ?? [],
		skipLayoutWrapping: options.skipLayoutWrapping
	});
}
function createAppPageBoundaryLayoutEntries(route, layoutModules) {
	if (!route || layoutModules.length === 0) return [];
	return createAppPageLayoutEntries({
		errors: route.errors,
		layoutTreePositions: route.layoutTreePositions,
		layouts: layoutModules,
		notFounds: null,
		routeSegments: route.routeSegments
	});
}
function resolveHttpAccessFallbackHeadRouteSegments(route, layoutModules) {
	if (!route?.routeSegments) return;
	if (!route.layouts || layoutModules.length >= route.layouts.length) return route.routeSegments;
	const lastIncludedLayoutIndex = layoutModules.length - 1;
	if (lastIncludedLayoutIndex < 0) return [];
	const segmentCount = route.layoutTreePositions?.[lastIncludedLayoutIndex] ?? 0;
	return route.routeSegments.slice(0, segmentCount);
}
function resolveHttpAccessFallbackHeadLayoutTreePositions(route, layoutModules) {
	if (!route?.layouts || layoutModules.length >= route.layouts.length) return route?.layoutTreePositions;
	return route.layoutTreePositions?.slice(0, layoutModules.length);
}
function createAppPageBoundaryRscPayload(options) {
	const routeId = AppElementsWire.encodeRouteId(options.pathname, null);
	const layoutEntries = createAppPageBoundaryLayoutEntries(options.route, options.layoutModules);
	const sourcePageSegments = options.sourcePageSegments ?? options.route?.routeSegments;
	return {
		...AppElementsWire.createMetadataEntries({
			interceptionContext: null,
			layoutIds: layoutEntries.map((entry) => entry.id),
			rootLayoutTreePath: layoutEntries[0]?.treePath ?? null,
			routeId,
			sourcePage: sourcePageSegments ? createAppPageSourcePage(sourcePageSegments) : null
		}),
		[routeId]: options.element
	};
}
function renderBoundarySpecialErrorResponse(options, specialError) {
	return buildAppPageSpecialErrorResponse({
		basePath: options.basePath,
		buildRscRedirectFlightStream: (rscOptions) => buildRscRedirectFlightStream({
			renderToReadableStream: options.renderToReadableStream,
			digest: rscOptions.digest
		}),
		clearRequestContext: options.clearRequestContext,
		getAndClearPendingCookies: options.getAndClearPendingCookies,
		isEdgeRuntime: options.isEdgeRuntime,
		isRscRequest: options.isRscRequest,
		middlewareContext: options.middlewareContext,
		serveStreamingMetadata: options.serveStreamingMetadata,
		request: options.request,
		specialError
	});
}
async function renderAppPageBoundaryElementResponse(options) {
	const requestUrl = new URL(options.requestUrl);
	const pathname = requestUrl.pathname;
	const payload = createAppPageBoundaryRscPayload({
		element: options.element,
		layoutModules: options.layoutModules,
		pathname,
		route: options.route,
		sourcePageSegments: options.sourcePageSegments
	});
	const rscErrorTracker = createAppPageRscErrorTracker(options.createRscOnErrorHandler(pathname, options.routePattern ?? pathname));
	const resolveCapturedSpecialError = (error) => resolveAppPageSpecialError(error) ?? resolveAppPageSpecialError(rscErrorTracker.getCapturedSpecialError());
	const renderSpecialErrorResponse = (specialError) => renderBoundarySpecialErrorResponse(options, specialError);
	const handleSpecialErrors = options.handleSpecialErrors === true;
	let response;
	try {
		response = await renderAppPageBoundaryResponse({
			async createHtmlResponse(rscStream, responseStatus) {
				const fontData = createAppPageFontData({
					getLinks: options.getFontLinks,
					getPreloads: options.getFontPreloads,
					getStyles: options.getFontStyles
				});
				const ssrHandler = await options.loadSsrHandler();
				return renderAppPageHtmlResponse({
					clearRequestContext: options.clearRequestContext,
					fontData,
					fontLinkHeader: options.buildFontLinkHeader(fontData.preloads),
					isEdgeRuntime: options.isEdgeRuntime,
					middlewareHeaders: options.middlewareContext.headers,
					navigationContext: options.getNavigationContext() ?? {
						pathname,
						searchParams: requestUrl.searchParams,
						params: options.navigationParams ?? options.route?.params ?? {}
					},
					rscStream,
					scriptNonce: options.scriptNonce,
					ssrHandler,
					status: responseStatus,
					initialDevServerError: options.initialDevServerError
				});
			},
			createRscOnErrorHandler() {
				return rscErrorTracker.onRenderError;
			},
			element: payload,
			isEdgeRuntime: options.isEdgeRuntime,
			isRscRequest: options.isRscRequest,
			middlewareHeaders: options.middlewareContext.headers,
			renderToReadableStream: options.renderToReadableStream,
			status: options.status
		});
	} catch (error) {
		const specialError = handleSpecialErrors ? resolveCapturedSpecialError(error) : null;
		if (specialError !== null) return renderSpecialErrorResponse(specialError);
		throw error;
	}
	if (!handleSpecialErrors) return response;
	if (options.isRscRequest && response.body) {
		const bufferedStream = await bufferAppPageBinaryStream(response.body);
		response = new Response(bufferedStream, {
			status: response.status,
			headers: response.headers
		});
	}
	const specialError = resolveCapturedSpecialError();
	if (!specialError) return response;
	if (response.body) try {
		await response.body.cancel();
	} catch {}
	return renderSpecialErrorResponse(specialError);
}
async function renderAppPageHttpAccessFallback(options) {
	const resolvedBoundaryModule = resolveAppPageHttpAccessBoundaryModule({
		rootForbiddenModule: options.rootForbiddenModule,
		rootNotFoundModule: options.rootNotFoundModule,
		rootUnauthorizedModule: options.rootUnauthorizedModule,
		routeForbiddenModule: options.route?.forbidden,
		routeNotFoundModule: options.route?.notFound,
		routeUnauthorizedModule: options.route?.unauthorized,
		statusCode: options.statusCode
	});
	const boundaryModule = options.boundaryModule ?? resolvedBoundaryModule;
	const boundaryComponent = options.boundaryComponent ?? getDefaultExport(boundaryModule);
	if (!boundaryComponent) return null;
	const layoutModules = options.layoutModules ?? options.route?.layouts ?? options.rootLayouts;
	const pathname = new URL(options.requestUrl).pathname;
	const routePathname = options.routePathname ?? stripRscSuffix(stripBasePath(pathname, options.basePath ?? ""));
	const routeSegments = resolveHttpAccessFallbackHeadRouteSegments(options.route, layoutModules);
	const fallbackRouteSegments = routeSegments ?? [];
	let head;
	try {
		if ([
			401,
			403,
			404
		].includes(options.statusCode)) {
			const boundaryTreePosition = resolveHttpAccessBoundaryTreePosition(options.route, boundaryModule, options.statusCode);
			const boundaryParams = boundaryTreePosition == null ? {} : resolveAppPageSegmentParams(fallbackRouteSegments, boundaryTreePosition, options.matchedParams);
			const intercept = options.intercept;
			const isSiblingIntercept = intercept?.interceptSlotKey === "__vinext_page_intercept" && intercept.interceptPage != null;
			const effectiveParams = isSiblingIntercept ? intercept.interceptParams ?? options.matchedParams : options.matchedParams;
			const slotParams = resolveSlotParamOverrides({ slots: options.route?.slots ?? null }, routePathname);
			const parallelBranches = resolveActiveParallelRouteHeadInputs({
				interceptBranchSegments: intercept?.interceptBranchSegments ?? null,
				interceptLayouts: intercept?.interceptLayouts ?? null,
				interceptLayoutSegments: intercept?.interceptLayoutSegments ?? null,
				interceptNotFoundBranchSegments: intercept?.interceptNotFoundBranchSegments ?? null,
				interceptNotFound: intercept?.interceptNotFound ?? null,
				interceptNotFoundTreePosition: intercept?.interceptNotFoundTreePosition ?? null,
				interceptPage: intercept?.interceptPage ?? null,
				interceptParams: intercept?.interceptParams ?? null,
				interceptSlotKey: intercept?.interceptSlotKey ?? null,
				interceptSourcePageSegments: intercept?.interceptSourcePageSegments ?? null,
				layoutTreePositions: options.route?.layoutTreePositions,
				params: options.matchedParams,
				routeSegments: fallbackRouteSegments,
				slotParams,
				slots: options.route?.slots ?? null
			});
			const primaryParallelBranch = isSiblingIntercept ? {
				head: {
					layoutModules: intercept?.interceptLayouts ?? [],
					layoutParams: (intercept?.interceptLayoutSegments ?? []).map((segments) => resolveAppPageBranchParams(intercept?.interceptBranchSegments ?? segments, segments.length, effectiveParams, segments)),
					pageModule: intercept?.interceptPage ?? null,
					params: effectiveParams,
					routeSegments: intercept?.interceptSourcePageSegments ?? fallbackRouteSegments
				},
				...intercept?.interceptNotFound ? {
					notFoundModule: intercept.interceptNotFound,
					notFoundParams: resolveAppPageBranchParams(intercept.interceptNotFoundBranchSegments ?? intercept.interceptBranchSegments ?? fallbackRouteSegments, intercept.interceptNotFoundTreePosition ?? 0, effectiveParams)
				} : {},
				ownerTreePosition: fallbackRouteSegments.length
			} : null;
			const fallbackHeadOptions = {
				boundaryModule,
				boundaryParams,
				branchNotFoundConventions: options.statusCode === 404,
				layoutModules,
				layoutTreePositions: resolveHttpAccessFallbackHeadLayoutTreePositions(options.route, layoutModules),
				parallelBranches,
				params: options.matchedParams,
				primaryParallelBranch,
				routeSegments
			};
			const [metadata, viewport] = await Promise.all([resolveHttpAccessFallbackMetadata({
				applyFileBasedMetadata: options.applyFileBasedMetadata,
				basePath: options.basePath ?? "",
				...fallbackHeadOptions,
				metadataRoutes: options.metadataRoutes,
				routePath: options.route?.pattern ?? pathname
			}), resolveHttpAccessFallbackViewport(fallbackHeadOptions)]);
			head = {
				metadata,
				viewport
			};
		} else head = await resolveAppPageHead({
			applyFileBasedMetadata: options.applyFileBasedMetadata,
			basePath: options.basePath ?? "",
			layoutModules,
			layoutTreePositions: resolveHttpAccessFallbackHeadLayoutTreePositions(options.route, layoutModules),
			metadataRoutes: options.metadataRoutes,
			pageModule: boundaryModule,
			params: options.matchedParams,
			routePath: options.route?.pattern ?? pathname,
			routeSegments
		});
	} catch (error) {
		const specialError = resolveAppPageSpecialError(error);
		if (specialError) return renderBoundarySpecialErrorResponse(options, specialError);
		throw error;
	}
	const { metadata, viewport } = head;
	const headElements = [(0, import_react_react_server.createElement)("meta", {
		charSet: "utf-8",
		key: "charset"
	}), (0, import_react_react_server.createElement)("meta", {
		key: "robots",
		name: "robots",
		content: "noindex"
	})];
	if (metadata) headElements.push((0, import_react_react_server.createElement)(MetadataHead, {
		key: "metadata",
		metadata,
		pathname,
		trailingSlash: options.trailingSlash
	}));
	headElements.push((0, import_react_react_server.createElement)(ViewportHead, {
		key: "viewport",
		viewport
	}));
	const skipLayoutWrapping = options.skipLayoutWrapping ?? false;
	const element = wrapRenderedBoundaryElement({
		element: (0, import_react_react_server.createElement)(import_react_react_server.Fragment, null, ...headElements, (0, import_react_react_server.createElement)(boundaryComponent)),
		globalErrorModule: options.globalErrorModule,
		includeGlobalErrorBoundary: true,
		isRscRequest: options.isRscRequest,
		layoutModules,
		layoutTreePositions: options.route?.layoutTreePositions,
		makeThenableParams: options.makeThenableParams,
		matchedParams: options.matchedParams,
		resolveChildSegments: options.resolveChildSegments,
		routeSegments: options.route?.routeSegments,
		skipLayoutWrapping
	});
	return renderAppPageBoundaryElementResponse({
		...options,
		element,
		handleSpecialErrors: true,
		layoutModules: skipLayoutWrapping ? [] : layoutModules,
		navigationParams: options.matchedParams,
		route: skipLayoutWrapping ? null : options.route,
		routePattern: options.route?.pattern,
		status: options.statusCode
	});
}
async function renderAppPageErrorBoundary(options) {
	const errorBoundary = resolveAppPageErrorBoundary({
		getDefaultExport,
		errorModules: options.route?.errorPaths,
		globalErrorModule: options.globalErrorModule,
		layoutErrorModules: options.route?.errors,
		pageErrorModule: options.route?.error
	});
	if (!errorBoundary.component) return null;
	const rawError = options.error instanceof Error ? options.error : new Error(String(options.error));
	rewriteClientHookError(rawError);
	const errorObject = options.errorOrigin === "ssr" ? rawError : options.sanitizeErrorForClient(rawError);
	const matchedParams = options.matchedParams ?? options.route?.params ?? {};
	const layoutModules = options.route?.layouts ?? options.rootLayouts;
	const pathname = new URL(options.requestUrl).pathname;
	const headElements = [(0, import_react_react_server.createElement)("meta", {
		charSet: "utf-8",
		key: "charset"
	})];
	if (!errorBoundary.isGlobalError) try {
		const { metadata, viewport } = await resolveAppPageHead({
			applyFileBasedMetadata: options.applyFileBasedMetadata,
			basePath: options.basePath ?? "",
			fallbackOnFileMetadataError: true,
			layoutModules,
			layoutTreePositions: options.route?.layoutTreePositions,
			metadataRoutes: options.metadataRoutes,
			params: matchedParams,
			routePath: options.route?.pattern ?? pathname,
			routeSegments: options.route?.routeSegments
		});
		if (metadata) headElements.push((0, import_react_react_server.createElement)(MetadataHead, {
			key: "metadata",
			metadata,
			pathname,
			trailingSlash: options.trailingSlash
		}));
		headElements.push((0, import_react_react_server.createElement)(ViewportHead, {
			key: "viewport",
			viewport
		}));
	} catch (error) {
		console.error(`[vinext] App page error boundary head resolution failed for ${options.route?.pattern ?? pathname}:`, error);
	}
	const buildElement = (BoundaryComponent) => {
		const serializedError = {
			digest: "digest" in errorObject ? String(errorObject.digest) : void 0,
			message: errorObject.message,
			name: errorObject.name,
			stack: void 0
		};
		const boundaryElement = errorBoundary.isGlobalError && BoundaryComponent !== DEFAULT_GLOBAL_ERROR_COMPONENT ? (0, import_react_react_server.createElement)(SerializedErrorBoundary, {
			error: serializedError,
			fallback: BoundaryComponent
		}) : (0, import_react_react_server.createElement)(BoundaryComponent, { error: errorObject });
		return wrapRenderedBoundaryElement({
			element: (0, import_react_react_server.createElement)(import_react_react_server.Fragment, null, ...headElements, errorBoundary.isGlobalError ? (0, import_react_react_server.createElement)(GlobalErrorBoundary, {
				fallback: DEFAULT_GLOBAL_ERROR_COMPONENT,
				children: boundaryElement
			}) : boundaryElement),
			globalErrorModule: options.globalErrorModule,
			includeGlobalErrorBoundary: !errorBoundary.isGlobalError,
			isRscRequest: options.isRscRequest,
			layoutModules,
			layoutTreePositions: options.route?.layoutTreePositions,
			makeThenableParams: options.makeThenableParams,
			matchedParams,
			resolveChildSegments: options.resolveChildSegments,
			routeSegments: options.route?.routeSegments,
			skipLayoutWrapping: errorBoundary.isGlobalError
		});
	};
	const renderWith = async (BoundaryComponent) => {
		const response = await renderAppPageBoundaryElementResponse({
			...options,
			element: buildElement(BoundaryComponent),
			initialDevServerError: rawError,
			layoutModules,
			navigationParams: matchedParams,
			route: options.route,
			routePattern: options.route?.pattern,
			status: errorBoundary.isGlobalError ? 500 : 200
		});
		if (errorBoundary.isGlobalError) {
			response.headers.set("Cache-Control", NEVER_CACHE_CONTROL);
			response.headers.delete("CDN-Cache-Control");
			response.headers.delete("Cloudflare-CDN-Cache-Control");
			response.headers.delete("Cache-Tag");
		}
		return response;
	};
	try {
		return await renderWith(errorBoundary.component);
	} catch (renderError) {
		if (errorBoundary.isGlobalError && !isNavigationSignalError(renderError) && !resolveAppPageSpecialError(renderError)) {
			console.error(`[vinext] global-error.tsx threw while rendering for ${options.route?.pattern ?? pathname}; falling back to the built-in default global-error:`, renderError);
			return renderWith(DEFAULT_GLOBAL_ERROR_COMPONENT);
		}
		throw renderError;
	}
}
var _clientHookPattern = /\b(useState|useEffect|useReducer|useRef|useContext|useLayoutEffect|useInsertionEffect|useSyncExternalStore|useTransition|useImperativeHandle|useDeferredValue|useActionState|useOptimistic|useEffectEvent)\b.*is not a function/;
function rewriteClientHookError(error) {
	const match = error.message.match(_clientHookPattern);
	if (match) error.message = buildClientHookErrorMessage(`${match[1]}()`);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/default-global-not-found-module.js
function DefaultGlobalNotFound() {
	return import_react_react_server.createElement("html", null, import_react_react_server.createElement("body", null, import_react_react_server.createElement(DefaultNotFound)));
}
/**
* Module-shaped wrapper around Next.js's built-in global not-found document.
* Unlike the regular default not-found boundary, this component owns the
* document shell because global not-found responses skip the root layout.
*/
var DEFAULT_GLOBAL_NOT_FOUND_MODULE = { default: DefaultGlobalNotFound };
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/default-not-found-module.js
/**
* Module-shaped wrapper around vinext's built-in default not-found component.
* Used as the fallback when an app does not define its own `app/not-found.tsx`
* (and has not opted into `app/global-not-found.tsx`). The runtime treats any
* `{ default: Component }` record as a "not-found module", so wrapping the
* component this way lets us thread the default through the existing
* `rootNotFoundModule` plumbing without introducing a parallel code path.
*
* Mirrors Next.js's `defaultNotFoundPath`
* (`next/dist/client/components/builtin/not-found.js`), which is selected
* automatically when the user has not supplied a custom not-found file:
* https://github.com/vercel/next.js/blob/canary/packages/next/src/build/webpack/loaders/next-app-loader/index.ts
*/
var DEFAULT_NOT_FOUND_MODULE = { default: DefaultNotFound };
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-fallback-renderer.js
var EMPTY_MW_CTX = {
	headers: null,
	status: null
};
function createAppFallbackRenderer(options) {
	const { applyFileBasedMetadata, basePath = "", htmlLimitedBots, clearRequestContext, createRscOnErrorHandler: buildRscOnErrorHandler, fontProviders, getAndClearPendingCookies, getNavigationContext, globalErrorModule, globalNotFoundEnabled = false, loadGlobalNotFoundModule, makeThenableParams, metadataRoutes, resolveChildSegments, rootBoundaries, rscRenderer, sanitizer, ssrLoader, trailingSlash } = options;
	const { rootForbiddenModule, rootLayouts, rootNotFoundModule, rootUnauthorizedModule } = rootBoundaries;
	const effectiveGlobalErrorModule = globalErrorModule ?? DEFAULT_GLOBAL_ERROR_MODULE;
	const effectiveRootNotFoundModule = rootNotFoundModule ?? DEFAULT_NOT_FOUND_MODULE;
	let globalNotFoundModulePromise = null;
	function resolveGlobalNotFoundModule() {
		if (!loadGlobalNotFoundModule) return null;
		if (globalNotFoundModulePromise === null) globalNotFoundModulePromise = runOutsideRequestScopes(() => Promise.resolve().then(loadGlobalNotFoundModule));
		return globalNotFoundModulePromise;
	}
	return {
		async renderHttpAccessFallback(route, statusCode, isRscRequest, request, opts, scriptNonce, middlewareContext, callContext) {
			const serveStreamingMetadata = shouldServeStreamingMetadata(request.headers.get("user-agent") ?? "", htmlLimitedBots);
			const useGlobalNotFound = statusCode === 404 && globalNotFoundEnabled && !route && !opts?.boundaryComponent;
			if (useGlobalNotFound && loadGlobalNotFoundModule) {
				const globalNotFoundModule = await resolveGlobalNotFoundModule();
				const globalNotFoundComponent = globalNotFoundModule?.default ?? null;
				if (globalNotFoundComponent) return renderAppPageHttpAccessFallback({
					applyFileBasedMetadata,
					basePath,
					trailingSlash,
					boundaryComponent: globalNotFoundComponent,
					boundaryModule: globalNotFoundModule ?? null,
					buildFontLinkHeader: fontProviders.buildFontLinkHeader,
					clearRequestContext,
					createRscOnErrorHandler(pathname, routePath) {
						return buildRscOnErrorHandler(request, pathname, routePath);
					},
					getFontLinks: fontProviders.getFontLinks,
					getFontPreloads: fontProviders.getFontPreloads,
					getFontStyles: fontProviders.getFontStyles,
					getAndClearPendingCookies,
					getNavigationContext,
					globalErrorModule: effectiveGlobalErrorModule,
					isEdgeRuntime: callContext?.isEdgeRuntime,
					isRscRequest,
					layoutModules: [],
					loadSsrHandler: ssrLoader,
					makeThenableParams,
					matchedParams: opts?.matchedParams ?? {},
					middlewareContext: middlewareContext ?? EMPTY_MW_CTX,
					metadataRoutes,
					request,
					requestUrl: request.url,
					resolveChildSegments,
					rootForbiddenModule: null,
					rootLayouts: [],
					rootNotFoundModule: null,
					rootUnauthorizedModule: null,
					route: null,
					renderToReadableStream: rscRenderer,
					scriptNonce,
					serveStreamingMetadata,
					skipLayoutWrapping: true,
					statusCode
				});
			}
			const routeMissRootNotFoundModule = useGlobalNotFound ? DEFAULT_GLOBAL_NOT_FOUND_MODULE : effectiveRootNotFoundModule;
			return renderAppPageHttpAccessFallback({
				applyFileBasedMetadata,
				basePath,
				trailingSlash,
				boundaryComponent: opts?.boundaryComponent ?? null,
				boundaryModule: opts?.boundaryModule ?? null,
				buildFontLinkHeader: fontProviders.buildFontLinkHeader,
				clearRequestContext,
				createRscOnErrorHandler(pathname, routePath) {
					return buildRscOnErrorHandler(request, pathname, routePath);
				},
				getFontLinks: fontProviders.getFontLinks,
				getFontPreloads: fontProviders.getFontPreloads,
				getFontStyles: fontProviders.getFontStyles,
				getAndClearPendingCookies,
				getNavigationContext,
				globalErrorModule: effectiveGlobalErrorModule,
				intercept: opts?.intercept ?? null,
				isEdgeRuntime: callContext?.isEdgeRuntime,
				isRscRequest,
				layoutModules: useGlobalNotFound ? [] : opts?.layouts ?? null,
				loadSsrHandler: ssrLoader,
				makeThenableParams,
				matchedParams: opts?.matchedParams ?? route?.params ?? {},
				middlewareContext: middlewareContext ?? EMPTY_MW_CTX,
				metadataRoutes,
				request,
				requestUrl: request.url,
				resolveChildSegments,
				rootForbiddenModule,
				rootLayouts: useGlobalNotFound ? [] : rootLayouts,
				rootNotFoundModule: routeMissRootNotFoundModule,
				rootUnauthorizedModule,
				route: useGlobalNotFound ? null : route,
				routePathname: callContext?.routePathname,
				renderToReadableStream: rscRenderer,
				scriptNonce,
				serveStreamingMetadata,
				skipLayoutWrapping: useGlobalNotFound,
				sourcePageSegments: callContext?.sourcePageSegments,
				statusCode
			});
		},
		renderNotFound(route, isRscRequest, request, matchedParams, scriptNonce, middlewareContext, callContext) {
			return this.renderHttpAccessFallback(route, 404, isRscRequest, request, { matchedParams }, scriptNonce, middlewareContext, callContext);
		},
		renderErrorBoundary(route, error, isRscRequest, request, matchedParams, scriptNonce, middlewareContext, callContext, errorOrigin = "rsc") {
			return renderAppPageErrorBoundary({
				applyFileBasedMetadata,
				basePath,
				trailingSlash,
				buildFontLinkHeader: fontProviders.buildFontLinkHeader,
				clearRequestContext,
				createRscOnErrorHandler(pathname, routePath) {
					return buildRscOnErrorHandler(request, pathname, routePath);
				},
				error,
				errorOrigin,
				getFontLinks: fontProviders.getFontLinks,
				getFontPreloads: fontProviders.getFontPreloads,
				getFontStyles: fontProviders.getFontStyles,
				getAndClearPendingCookies,
				getNavigationContext,
				globalErrorModule: effectiveGlobalErrorModule,
				isEdgeRuntime: callContext?.isEdgeRuntime,
				isRscRequest,
				loadSsrHandler: ssrLoader,
				makeThenableParams,
				matchedParams: matchedParams ?? route?.params ?? {},
				middlewareContext: middlewareContext ?? EMPTY_MW_CTX,
				metadataRoutes,
				request,
				requestUrl: request.url,
				resolveChildSegments,
				rootLayouts,
				route,
				renderToReadableStream: rscRenderer,
				sanitizeErrorForClient: sanitizer,
				scriptNonce,
				sourcePageSegments: callContext?.sourcePageSegments
			});
		}
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/sorted-array.js
function findSortedStringPosition(values, candidate) {
	let lower = 0;
	let upper = values.length;
	while (lower < upper) {
		const middle = lower + Math.floor((upper - lower) / 2);
		if (values[middle] === candidate) return {
			found: true,
			index: middle
		};
		if (values[middle] < candidate) lower = middle + 1;
		else upper = middle;
	}
	return {
		found: false,
		index: lower
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/cache-proof.js
var DEFAULT_CACHE_VARIANT_BUDGET = {
	maxDimensionCount: 8,
	maxDimensionNameLength: 64,
	maxDimensionValueLength: 256,
	maxEncodedLength: 1024,
	maxValuesPerDimension: 8,
	maxVariantsPerRoute: 64
};
var ALL_RENDER_REQUEST_API_KINDS = [
	"connection",
	"cookies",
	"draftMode",
	"headers",
	"params",
	"searchParams"
];
var PUBLIC_UNSAFE_DIMENSION_SOURCES = /* @__PURE__ */ new Set([
	"auth",
	"cookie",
	"draft-mode",
	"header",
	"session"
]);
function buildBreakerFallback(code, fields = {}, mode = "renderFresh", scope = "affectedOutput") {
	return {
		kind: "breakerFallback",
		code,
		mode,
		scope,
		fields
	};
}
function sortedUnique(values) {
	return [...new Set(values)].sort();
}
function normalizeDimensionName(name) {
	return name.trim().toLowerCase();
}
function redactValue(value) {
	return `h:${fnv1a64(value)}`;
}
function sortedUniqueRedacted(values) {
	return sortedUnique(sortedUnique(values).map(redactValue));
}
function encodeParts(parts) {
	return JSON.stringify(parts);
}
function compareDimensions(a, b) {
	return a.source.localeCompare(b.source) || a.name.localeCompare(b.name) || a.privacy.localeCompare(b.privacy);
}
function encodeNullable(value) {
	return value;
}
function assertNever$1(value) {
	throw new Error(`Unhandled cache proof variant: ${String(value)}`);
}
function encodeOutputScope(output) {
	switch (output.kind) {
		case "app-html": return encodeParts([
			output.kind,
			output.routeId,
			encodeNullable(output.rootBoundaryId),
			encodeNullable(output.renderEpoch)
		]);
		case "app-rsc": return encodeParts([
			output.kind,
			output.routeId,
			encodeNullable(output.rootBoundaryId),
			encodeNullable(output.renderEpoch),
			encodeNullable(output.mountedSlotsFingerprint)
		]);
		case "layout": return encodeParts([
			output.kind,
			output.routeId,
			output.layoutId,
			encodeNullable(output.rootBoundaryId)
		]);
		case "page": return encodeParts([
			output.kind,
			output.routeId,
			output.pageId,
			encodeNullable(output.rootBoundaryId)
		]);
		case "route-handler": return encodeParts([
			output.kind,
			output.routeId,
			output.routeHandlerId
		]);
		case "slot": return encodeParts([
			output.kind,
			output.routeId,
			output.slotId,
			encodeNullable(output.rootBoundaryId)
		]);
		case "template": return encodeParts([
			output.kind,
			output.routeId,
			output.templateId,
			encodeNullable(output.rootBoundaryId)
		]);
		default: return assertNever$1(output);
	}
}
function validateBudgetNumber(name, value) {
	if (Number.isInteger(value) && value >= 0) return null;
	return buildBreakerFallback("CP_INVALID_VARIANT_BUDGET", { budgetField: name });
}
function validateBudget(budget) {
	return validateBudgetNumber("maxDimensionCount", budget.maxDimensionCount) ?? validateBudgetNumber("maxDimensionNameLength", budget.maxDimensionNameLength) ?? validateBudgetNumber("maxDimensionValueLength", budget.maxDimensionValueLength) ?? validateBudgetNumber("maxEncodedLength", budget.maxEncodedLength) ?? validateBudgetNumber("maxValuesPerDimension", budget.maxValuesPerDimension) ?? validateBudgetNumber("maxVariantsPerRoute", budget.maxVariantsPerRoute);
}
function buildDimension(input, budget) {
	const name = normalizeDimensionName(input.name);
	if (name.length === 0) return buildBreakerFallback("CP_DIMENSION_NAME_MISSING", { source: input.source });
	if (name.length > budget.maxDimensionNameLength) return buildBreakerFallback("CP_DIMENSION_NAME_TOO_LONG", {
		maxLength: budget.maxDimensionNameLength,
		nameHash: redactValue(name),
		source: input.source
	});
	if (input.privacy === "public" && PUBLIC_UNSAFE_DIMENSION_SOURCES.has(input.source)) return buildBreakerFallback("CP_UNSAFE_PUBLIC_DIMENSION", {
		name,
		source: input.source
	}, "privateUncacheable");
	const values = sortedUnique(input.values);
	if (values.length === 0) return buildBreakerFallback("CP_DIMENSION_VALUES_MISSING", {
		name,
		source: input.source
	});
	if (values.length > budget.maxValuesPerDimension) return buildBreakerFallback("CP_DIMENSION_VALUE_COUNT_EXCEEDED", {
		maxValues: budget.maxValuesPerDimension,
		name,
		source: input.source,
		valueCount: values.length
	});
	for (const value of values) if (value.length > budget.maxDimensionValueLength) return buildBreakerFallback("CP_DIMENSION_VALUE_TOO_LONG", {
		maxLength: budget.maxDimensionValueLength,
		name,
		source: input.source,
		valueHash: redactValue(value)
	});
	const valueHashes = values.map(redactValue);
	return {
		encoded: encodeParts([
			input.source,
			input.privacy,
			name,
			valueHashes
		]),
		name,
		privacy: input.privacy,
		source: input.source,
		valueCount: valueHashes.length,
		valueHashes
	};
}
function isCacheProofBreakerFallback(value) {
	return "code" in value;
}
function getDimensionBucket(bySource, source, privacy) {
	const existingByPrivacy = bySource.get(source);
	const byPrivacy = existingByPrivacy ?? /* @__PURE__ */ new Map();
	if (!existingByPrivacy) bySource.set(source, byPrivacy);
	const existingByName = byPrivacy.get(privacy);
	const byName = existingByName ?? /* @__PURE__ */ new Map();
	if (!existingByName) byPrivacy.set(privacy, byName);
	return byName;
}
function mergeDimensionInputs(dimensions) {
	const bySource = /* @__PURE__ */ new Map();
	const orderedDimensions = [];
	for (const dimension of dimensions) {
		const name = normalizeDimensionName(dimension.name);
		const bucket = getDimensionBucket(bySource, dimension.source, dimension.privacy);
		const existing = bucket.get(name);
		if (existing) {
			existing.values.push(...dimension.values);
			continue;
		}
		const accumulator = {
			name,
			privacy: dimension.privacy,
			source: dimension.source,
			values: [...dimension.values]
		};
		bucket.set(name, accumulator);
		orderedDimensions.push(accumulator);
	}
	return orderedDimensions;
}
function buildCacheVariant(input) {
	const budgetFallback = validateBudget(input.budget);
	if (budgetFallback) return {
		kind: "breakerFallback",
		fallback: budgetFallback
	};
	const dimensionInputs = mergeDimensionInputs(input.dimensions);
	if (dimensionInputs.length > input.budget.maxDimensionCount) return {
		kind: "breakerFallback",
		fallback: buildBreakerFallback("CP_DIMENSION_COUNT_EXCEEDED", {
			dimensionCount: dimensionInputs.length,
			maxDimensionCount: input.budget.maxDimensionCount,
			routeId: input.output.routeId
		})
	};
	const dimensions = [];
	for (const dimensionInput of dimensionInputs) {
		const dimension = buildDimension(dimensionInput, input.budget);
		if (isCacheProofBreakerFallback(dimension)) return {
			kind: "breakerFallback",
			fallback: dimension
		};
		dimensions.push(dimension);
	}
	dimensions.sort(compareDimensions);
	const encoded = [
		`schema:1`,
		encodeOutputScope(input.output),
		...dimensions.map((dimension) => dimension.encoded)
	].join("|");
	if (encoded.length > input.budget.maxEncodedLength) return {
		kind: "breakerFallback",
		fallback: buildBreakerFallback("CP_ENCODED_VARIANT_TOO_LONG", {
			encodedHash: redactValue(encoded),
			encodedLength: encoded.length,
			maxEncodedLength: input.budget.maxEncodedLength,
			routeId: input.output.routeId
		})
	};
	return {
		kind: "variant",
		variant: {
			schemaVersion: 1,
			cacheKey: `cp1:${fnv1a64(encoded)}`,
			output: input.output,
			dimensions,
			encodedLength: encoded.length,
			budget: { ...input.budget }
		}
	};
}
function normalizeRouteBudget(input) {
	return {
		routeId: input.routeId,
		variantCacheKeys: sortedUnique(input.variantCacheKeys)
	};
}
function buildRouteVariantCeilingFallback(variant, existingVariantCount) {
	return buildBreakerFallback("CP_ROUTE_VARIANT_CEILING_EXCEEDED", {
		existingVariantCount,
		maxVariantsPerRoute: variant.budget.maxVariantsPerRoute,
		routeId: variant.output.routeId
	}, "privateUncacheable", "route");
}
function enforceCacheVariantRouteBudget(input) {
	if (input.routeBudget && input.routeBudget.routeId !== input.variant.output.routeId) return {
		kind: "breakerFallback",
		routeBudget: normalizeRouteBudget(input.routeBudget),
		fallback: buildBreakerFallback("CP_ROUTE_VARIANT_BUDGET_ROUTE_MISMATCH", {
			budgetRouteId: input.routeBudget.routeId,
			routeId: input.variant.output.routeId
		}, "privateUncacheable", "route")
	};
	const routeBudget = normalizeRouteBudget(input.routeBudget ?? {
		routeId: input.variant.output.routeId,
		variantCacheKeys: []
	});
	const existingVariantCount = routeBudget.variantCacheKeys.length;
	const variantKeyPosition = findSortedStringPosition(routeBudget.variantCacheKeys, input.variant.cacheKey);
	if (existingVariantCount > input.variant.budget.maxVariantsPerRoute) return {
		kind: "breakerFallback",
		routeBudget,
		fallback: buildRouteVariantCeilingFallback(input.variant, existingVariantCount)
	};
	if (variantKeyPosition.found) return {
		kind: "variant",
		variant: input.variant,
		routeBudget,
		didConsumeRouteVariantBudget: false
	};
	if (existingVariantCount >= input.variant.budget.maxVariantsPerRoute) return {
		kind: "breakerFallback",
		routeBudget,
		fallback: buildRouteVariantCeilingFallback(input.variant, existingVariantCount)
	};
	return {
		kind: "variant",
		variant: input.variant,
		routeBudget: {
			routeId: routeBudget.routeId,
			variantCacheKeys: [
				...routeBudget.variantCacheKeys.slice(0, variantKeyPosition.index),
				input.variant.cacheKey,
				...routeBudget.variantCacheKeys.slice(variantKeyPosition.index)
			]
		},
		didConsumeRouteVariantBudget: true
	};
}
function buildCacheVariantWithRouteBudget(input) {
	const variantResult = buildCacheVariant({
		budget: input.budget,
		dimensions: input.dimensions,
		output: input.output
	});
	if (variantResult.kind === "breakerFallback") return {
		kind: "breakerFallback",
		routeBudget: input.routeBudget ? normalizeRouteBudget(input.routeBudget) : null,
		fallback: variantResult.fallback
	};
	return enforceCacheVariantRouteBudget({
		routeBudget: input.routeBudget,
		variant: variantResult.variant
	});
}
function boundaryOutcomesMatch(expected, candidate) {
	switch (expected.kind) {
		case "error": return candidate.kind === "error" && (expected.digest ?? "") === (candidate.digest ?? "");
		case "forbidden": return candidate.kind === "forbidden";
		case "globalError": return candidate.kind === "globalError" && (expected.digest ?? "") === (candidate.digest ?? "");
		case "notFound": return candidate.kind === "notFound";
		case "redirect": return candidate.kind === "redirect" && expected.status === candidate.status && expected.location === candidate.location;
		case "success": return candidate.kind === "success";
		case "unauthorized": return candidate.kind === "unauthorized";
		case "unknown": return false;
		default: return assertNever$1(expected);
	}
}
function buildBoundaryOutcomeCompatibility(input) {
	if (input.expected.kind === "unknown" || input.candidate.kind === "unknown") return {
		kind: "incompatible",
		expected: input.expected,
		candidate: input.candidate,
		fallback: buildBreakerFallback("CP_BOUNDARY_OUTCOME_UNKNOWN", {
			candidateKind: input.candidate.kind,
			expectedKind: input.expected.kind
		})
	};
	if (boundaryOutcomesMatch(input.expected, input.candidate)) return {
		kind: "compatible",
		outcome: input.candidate,
		reason: "CP_BOUNDARY_OUTCOME_MATCH"
	};
	return {
		kind: "incompatible",
		expected: input.expected,
		candidate: input.candidate,
		fallback: buildBreakerFallback("CP_BOUNDARY_OUTCOME_MISMATCH", {
			candidateKind: input.candidate.kind,
			expectedKind: input.expected.kind
		})
	};
}
function requestApiStatusRank(status) {
	switch (status) {
		case "notObserved": return 0;
		case "unknown": return 1;
		case "observed": return 2;
		default: return assertNever$1(status);
	}
}
function normalizeRequestApiObservations(observations) {
	const byKind = /* @__PURE__ */ new Map();
	for (const observation of observations) {
		const current = byKind.get(observation.kind);
		if (current === void 0 || requestApiStatusRank(observation.status) > requestApiStatusRank(current)) byKind.set(observation.kind, observation.status);
	}
	return [...byKind.entries()].sort(([left], [right]) => left.localeCompare(right)).map(([kind, status]) => ({
		kind,
		status
	}));
}
function cacheProofDowngradeTargetRank(target) {
	switch (target) {
		case "public": return 0;
		case "publicVariant": return 1;
		case "private": return 2;
		case "privateUncacheable": return 3;
		case "freshRender": return 4;
		default: return assertNever$1(target);
	}
}
function maxCacheProofDowngradeTarget(current, candidate) {
	return cacheProofDowngradeTargetRank(candidate) > cacheProofDowngradeTargetRank(current) ? candidate : current;
}
function createDowngradeFallback(target, reasons) {
	switch (target) {
		case "public":
		case "publicVariant":
		case "private": return null;
		case "privateUncacheable": return buildBreakerFallback("CP_PRIVATE_DYNAMIC_DOWNGRADE", {
			reasonCodes: reasons.map((reason) => reason.code),
			target
		}, "privateUncacheable");
		case "freshRender": return buildBreakerFallback("CP_PRIVATE_DYNAMIC_DOWNGRADE", {
			reasonCodes: reasons.map((reason) => reason.code),
			target
		});
		default: return assertNever$1(target);
	}
}
function classifyObservedRequestApiDowngrade(kind) {
	switch (kind) {
		case "connection": return {
			code: "CP_DOWNGRADE_DYNAMIC_REQUEST_API",
			requestApi: "connection",
			target: "freshRender"
		};
		case "cookies": return {
			code: "CP_DOWNGRADE_PRIVATE_REQUEST_API",
			requestApi: "cookies",
			target: "private"
		};
		case "draftMode": return {
			code: "CP_DOWNGRADE_DRAFT_MODE",
			requestApi: "draftMode",
			target: "privateUncacheable"
		};
		case "headers": return {
			code: "CP_DOWNGRADE_PRIVATE_REQUEST_API",
			requestApi: "headers",
			target: "private"
		};
		case "params": return {
			code: "CP_DOWNGRADE_PUBLIC_REQUEST_API",
			requestApi: "params",
			target: "publicVariant"
		};
		case "searchParams": return {
			code: "CP_DOWNGRADE_PUBLIC_REQUEST_API",
			requestApi: "searchParams",
			target: "publicVariant"
		};
		default: return assertNever$1(kind);
	}
}
function classifyRenderObservationDowngrade(input) {
	const reasons = [];
	let target = "public";
	switch (input.cacheability) {
		case "public": break;
		case "private": {
			const reason = {
				code: "CP_DOWNGRADE_CACHEABILITY_PRIVATE",
				target: "private"
			};
			reasons.push(reason);
			target = maxCacheProofDowngradeTarget(target, reason.target);
			break;
		}
		case "uncacheable": {
			const reason = {
				code: "CP_DOWNGRADE_CACHEABILITY_UNCACHEABLE",
				target: "privateUncacheable"
			};
			reasons.push(reason);
			target = maxCacheProofDowngradeTarget(target, reason.target);
			break;
		}
		case "unknown": {
			const reason = {
				code: "CP_DOWNGRADE_CACHEABILITY_UNKNOWN",
				target: "freshRender"
			};
			reasons.push(reason);
			target = maxCacheProofDowngradeTarget(target, reason.target);
			break;
		}
		default: assertNever$1(input.cacheability);
	}
	if (input.completeness !== "complete") {
		const reason = {
			code: "CP_DOWNGRADE_INCOMPLETE_OBSERVATION",
			completeness: input.completeness,
			target: "freshRender"
		};
		reasons.push(reason);
		target = maxCacheProofDowngradeTarget(target, reason.target);
	}
	if (input.dynamicFetches.length > 0) {
		const reason = {
			code: "CP_DOWNGRADE_DYNAMIC_FETCH",
			dynamicFetchCount: input.dynamicFetches.length,
			target: "freshRender"
		};
		reasons.push(reason);
		target = maxCacheProofDowngradeTarget(target, reason.target);
	}
	const requestApis = normalizeRequestApiObservations(input.requestApis);
	for (const requestApi of requestApis) {
		if (requestApi.status === "notObserved") continue;
		const reason = requestApi.status === "unknown" ? {
			code: "CP_DOWNGRADE_UNKNOWN_REQUEST_API",
			requestApi: requestApi.kind,
			target: "freshRender"
		} : classifyObservedRequestApiDowngrade(requestApi.kind);
		reasons.push(reason);
		target = maxCacheProofDowngradeTarget(target, reason.target);
	}
	return {
		target,
		reasons,
		fallback: createDowngradeFallback(target, reasons),
		isPublicCacheCandidate: target === "public" || target === "publicVariant"
	};
}
function buildRenderRequestApiObservations(input) {
	const observedKinds = new Set(input.observed);
	const absentStatus = input.completeness === "complete" ? "notObserved" : "unknown";
	return ALL_RENDER_REQUEST_API_KINDS.map((kind) => ({
		kind,
		status: observedKinds.has(kind) ? "observed" : absentStatus
	}));
}
function buildRenderObservation(input) {
	const requestApis = normalizeRequestApiObservations(input.requestApis);
	const dynamicFetches = sortedUniqueRedacted(input.dynamicFetches);
	return {
		schemaVersion: 1,
		output: input.output,
		completeness: input.completeness,
		boundaryOutcome: input.boundaryOutcome,
		requestApis,
		dynamicFetches,
		cacheTags: sortedUnique(input.cacheTags),
		pathTags: sortedUnique(input.pathTags),
		cacheability: input.cacheability,
		downgrade: classifyRenderObservationDowngrade({
			cacheability: input.cacheability,
			completeness: input.completeness,
			dynamicFetches,
			requestApis
		})
	};
}
function hasCompleteNegativeRequestApiProof(observation, requiredApis) {
	if (observation.completeness !== "complete") return false;
	const statuses = /* @__PURE__ */ new Map();
	for (const requestApi of normalizeRequestApiObservations(observation.requestApis)) statuses.set(requestApi.kind, requestApi.status);
	for (const api of requiredApis) if (statuses.get(api) !== "notObserved") return false;
	return true;
}
function isStaticLayoutOutputScope(output) {
	return output.kind === "layout";
}
function rejectStaticLayoutReuseProof(code, fields, mode = "renderFresh") {
	return {
		kind: "rejected",
		fallback: buildBreakerFallback(code, fields, mode)
	};
}
function getRequestApiStatus(observations, kind) {
	let status = null;
	for (const requestApi of observations) {
		if (requestApi.kind !== kind) continue;
		if (status === null || requestApiStatusRank(requestApi.status) > requestApiStatusRank(status)) status = requestApi.status;
	}
	return status ?? "missing";
}
function createStaticLayoutDowngradeFallback(downgrade) {
	const mode = downgrade.target === "privateUncacheable" ? "privateUncacheable" : "renderFresh";
	return buildBreakerFallback("CP_STATIC_LAYOUT_PRIVATE_DYNAMIC_DOWNGRADE", {
		reasonCodes: downgrade.reasons.map((reason) => reason.code),
		target: downgrade.target
	}, mode);
}
function outputFieldMismatch(candidate, observation) {
	if (candidate.layoutId !== observation.layoutId) return "layoutId";
	if (candidate.rootBoundaryId !== observation.rootBoundaryId) return "rootBoundaryId";
	if (candidate.routeId !== observation.routeId) return "routeId";
	return null;
}
function buildStaticLayoutReuseProof(input) {
	if (!isStaticLayoutOutputScope(input.currentOutput)) return rejectStaticLayoutReuseProof("CP_STATIC_LAYOUT_CURRENT_OUTPUT_KIND", { currentOutputKind: input.currentOutput.kind });
	if (!isStaticLayoutOutputScope(input.candidateVariant.output)) return rejectStaticLayoutReuseProof("CP_STATIC_LAYOUT_CANDIDATE_OUTPUT_KIND", { candidateOutputKind: input.candidateVariant.output.kind });
	if (!isStaticLayoutOutputScope(input.candidateObservation.output)) return rejectStaticLayoutReuseProof("CP_STATIC_LAYOUT_OBSERVATION_OUTPUT_KIND", { observationOutputKind: input.candidateObservation.output.kind });
	const currentOutput = input.currentOutput;
	const candidateOutput = input.candidateVariant.output;
	const observationOutput = input.candidateObservation.output;
	const requestApis = normalizeRequestApiObservations(input.candidateObservation.requestApis);
	const candidateObservation = {
		...input.candidateObservation,
		requestApis,
		downgrade: classifyRenderObservationDowngrade({
			cacheability: input.candidateObservation.cacheability,
			completeness: input.candidateObservation.completeness,
			dynamicFetches: input.candidateObservation.dynamicFetches,
			requestApis
		})
	};
	const observedOutputMismatch = outputFieldMismatch(candidateOutput, observationOutput);
	if (observedOutputMismatch) return rejectStaticLayoutReuseProof("CP_STATIC_LAYOUT_OBSERVATION_OUTPUT_MISMATCH", {
		candidateLayoutId: candidateOutput.layoutId,
		candidateRootBoundaryId: candidateOutput.rootBoundaryId,
		candidateRouteId: candidateOutput.routeId,
		field: observedOutputMismatch,
		observationLayoutId: observationOutput.layoutId,
		observationRootBoundaryId: observationOutput.rootBoundaryId,
		observationRouteId: observationOutput.routeId
	});
	if (currentOutput.layoutId !== candidateOutput.layoutId) return rejectStaticLayoutReuseProof("CP_STATIC_LAYOUT_ID_MISMATCH", {
		candidateLayoutId: candidateOutput.layoutId,
		currentLayoutId: currentOutput.layoutId
	});
	if (currentOutput.rootBoundaryId === null || candidateOutput.rootBoundaryId === null) return rejectStaticLayoutReuseProof("CP_STATIC_LAYOUT_ROOT_BOUNDARY_UNKNOWN", {
		candidateRootBoundaryId: candidateOutput.rootBoundaryId,
		currentRootBoundaryId: currentOutput.rootBoundaryId
	});
	if (currentOutput.rootBoundaryId !== candidateOutput.rootBoundaryId) return rejectStaticLayoutReuseProof("CP_STATIC_LAYOUT_ROOT_BOUNDARY_MISMATCH", {
		candidateRootBoundaryId: candidateOutput.rootBoundaryId,
		currentRootBoundaryId: currentOutput.rootBoundaryId
	});
	const boundaryCompatibility = buildBoundaryOutcomeCompatibility({
		candidate: candidateObservation.boundaryOutcome,
		expected: { kind: "success" }
	});
	if (boundaryCompatibility.kind === "incompatible") return {
		kind: "rejected",
		fallback: boundaryCompatibility.fallback
	};
	if (input.candidateVariant.dimensions.length > 0) return rejectStaticLayoutReuseProof("CP_STATIC_LAYOUT_VARIANT_DIMENSION_UNPROVEN", {
		dimensionCount: input.candidateVariant.dimensions.length,
		sources: sortedUnique(input.candidateVariant.dimensions.map((dimension) => dimension.source))
	});
	if (!candidateObservation.downgrade.isPublicCacheCandidate) return {
		kind: "rejected",
		fallback: createStaticLayoutDowngradeFallback(candidateObservation.downgrade)
	};
	const requiredNegativeRequestApis = ALL_RENDER_REQUEST_API_KINDS;
	for (const api of requiredNegativeRequestApis) {
		const status = getRequestApiStatus(candidateObservation.requestApis, api);
		if (status === "notObserved") continue;
		return rejectStaticLayoutReuseProof(status === "missing" ? "CP_STATIC_LAYOUT_REQUEST_API_UNKNOWN" : "CP_STATIC_LAYOUT_REQUEST_API_OBSERVED", {
			requestApi: api,
			status
		});
	}
	return {
		kind: "proof",
		proof: {
			authorizesRuntimeReuse: true,
			candidateOutput,
			code: "CP_STATIC_LAYOUT_REUSE_PROVEN",
			currentOutput,
			fields: {
				candidateRouteId: candidateOutput.routeId,
				currentRouteId: currentOutput.routeId,
				layoutId: currentOutput.layoutId,
				rootBoundaryId: currentOutput.rootBoundaryId
			},
			observation: candidateObservation,
			requiredNegativeRequestApis: [...requiredNegativeRequestApis],
			reuseClass: "static-layout",
			variant: input.candidateVariant
		}
	};
}
function createCacheProofHotPathMetric(outcome, code, fields) {
	return {
		name: "vinext.cache.static_layout_artifact_reuse",
		outcome,
		code,
		fields
	};
}
function createStaticLayoutArtifactReuseFallback(fallback) {
	return {
		kind: "fallback",
		canReuse: false,
		fallback,
		metric: createCacheProofHotPathMetric("fallback", fallback.code, fallback.fields)
	};
}
function createStaticLayoutArtifactReuseDecision(input) {
	if (input.candidateVariant.kind === "breakerFallback") return createStaticLayoutArtifactReuseFallback(input.candidateVariant.fallback);
	const artifactCompatibility = evaluateArtifactCompatibility(input.currentArtifactCompatibility, input.candidateArtifactCompatibility, { compatibilityMap: input.compatibilityMap });
	if (artifactCompatibility.kind === "unknown") return createStaticLayoutArtifactReuseFallback(buildBreakerFallback("CP_ARTIFACT_COMPATIBILITY_UNKNOWN", {
		compatibilityFallback: artifactCompatibility.fallback,
		reason: artifactCompatibility.reason
	}));
	if (artifactCompatibility.kind === "incompatible") return createStaticLayoutArtifactReuseFallback(buildBreakerFallback("CP_ARTIFACT_COMPATIBILITY_INCOMPATIBLE", {
		compatibilityFallback: artifactCompatibility.fallback,
		reason: artifactCompatibility.reason
	}));
	const proof = buildStaticLayoutReuseProof({
		candidateObservation: input.candidateObservation,
		candidateVariant: input.candidateVariant.variant,
		currentOutput: input.currentOutput
	});
	if (proof.kind === "rejected") return createStaticLayoutArtifactReuseFallback(proof.fallback);
	return {
		kind: "reuse",
		canReuse: true,
		proof: {
			...proof.proof,
			candidateArtifactCompatibility: { ...input.candidateArtifactCompatibility }
		},
		metric: createCacheProofHotPathMetric("reuse", proof.proof.code, proof.proof.fields)
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-render-observation.js
function readRootBoundaryId$1(element) {
	const rootLayoutTreePath = element[AppElementsWire.keys.rootLayout];
	return typeof rootLayoutTreePath === "string" ? rootLayoutTreePath : null;
}
function readRouteId(element, routePattern) {
	if (isAppElementsRecord(element)) {
		const routeId = element[AppElementsWire.keys.route];
		if (typeof routeId === "string") return routeId;
	}
	return AppElementsWire.encodeRouteId(routePattern, null);
}
function createMountedSlotsFingerprint(mountedSlotsHeader) {
	const normalized = normalizeMountedSlotsHeader(mountedSlotsHeader);
	return normalized ? `slots:${fnv1a64(normalized)}` : null;
}
function mergeObservedRequestApis(observed, params) {
	const merged = new Set(observed);
	if (Object.keys(params).length > 0) merged.add("params");
	return [...merged].sort();
}
function createEmptyAppPageRenderObservationState() {
	return {
		dynamicFetches: [],
		requestApis: []
	};
}
function consumeAppPageRenderObservationState() {
	return {
		dynamicFetches: consumeDynamicFetchObservations(),
		requestApis: consumeRenderRequestApiUsage()
	};
}
function discardAppPageRenderState() {
	_consumeRequestScopedCacheLife();
	consumeDynamicFetchObservations();
	consumeRenderRequestApiUsage();
	consumeInvalidDynamicUsageError();
	consumeDynamicUsage();
}
function createAppPageRenderObservation(options) {
	return buildRenderObservation({
		boundaryOutcome: options.boundaryOutcome,
		cacheability: options.cacheability,
		cacheTags: options.cacheTags,
		completeness: options.completeness,
		dynamicFetches: options.state.dynamicFetches,
		output: options.output,
		pathTags: [options.cleanPathname],
		requestApis: buildRenderRequestApiObservations({
			completeness: options.completeness,
			observed: mergeObservedRequestApis(options.state.requestApis, options.params)
		})
	});
}
function createAppPageRscOutputScope(options) {
	return {
		kind: "app-rsc",
		mountedSlotsFingerprint: createMountedSlotsFingerprint(options.mountedSlotsHeader),
		renderEpoch: options.renderEpoch,
		rootBoundaryId: options.rootBoundaryId ?? (isAppElementsRecord(options.element) ? readRootBoundaryId$1(options.element) : null),
		routeId: readRouteId(options.element, options.routePattern)
	};
}
function createAppPageHtmlOutputScope(options) {
	return {
		kind: "app-html",
		renderEpoch: options.renderEpoch,
		rootBoundaryId: options.rootBoundaryId ?? (isAppElementsRecord(options.element) ? readRootBoundaryId$1(options.element) : null),
		routeId: readRouteId(options.element, options.routePattern)
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-layout-param-observation.js
var STATIC_LAYOUT_OBSERVATION_SKIP_RULES = [
	["SKIP_LAYOUT_PARAMS_OBSERVATION_INCOMPLETE", (observation) => observation.completeness !== "complete"],
	["SKIP_LAYOUT_PARAMS_PRESENT", (observation) => observation.paramScopeKeys.length > 0],
	["SKIP_LAYOUT_PARAMS_OBSERVED", (observation) => observation.observed],
	["SKIP_LAYOUT_DYNAMIC_USAGE_OBSERVED", (observation) => observation.dynamicUsageObserved],
	["SKIP_LAYOUT_REQUEST_API_OBSERVED", (observation) => observation.requestApis.length > 0],
	["SKIP_LAYOUT_REVALIDATE_PRESENT", (observation) => observation.finiteRevalidateSeconds !== null],
	["SKIP_LAYOUT_CACHE_LIFE_OBSERVED", (observation) => observation.cacheLifeObserved],
	["SKIP_LAYOUT_UNSTABLE_CACHE_OBSERVED", (observation) => observation.unstableCaches.length > 0],
	["SKIP_LAYOUT_CACHE_TAGS_OBSERVED", (observation) => observation.cacheTags.length > 0],
	["SKIP_LAYOUT_CACHEABLE_FETCHES_OBSERVED", (observation) => observation.cacheableFetchCount > 0],
	["SKIP_LAYOUT_DYNAMIC_FETCHES_OBSERVED", (observation) => observation.dynamicFetchCount > 0]
];
function createStaticLayoutObservationTraceFields(observation) {
	return {
		cacheLifeObserved: observation.cacheLifeObserved,
		cacheTags: observation.cacheTags,
		cacheableFetchCount: observation.cacheableFetchCount,
		dynamicFetchCount: observation.dynamicFetchCount,
		dynamicUsageObserved: observation.dynamicUsageObserved,
		finiteRevalidateSeconds: observation.finiteRevalidateSeconds,
		observedParamKeys: observation.keys,
		paramScopeKeys: observation.paramScopeKeys,
		requestApis: observation.requestApis,
		unstableCacheCount: observation.unstableCaches.length,
		unstableCacheKeyHashes: observation.unstableCaches.map((cache) => cache.keyHash),
		unstableCacheRevalidates: observation.unstableCaches.map((cache) => String(cache.revalidate)),
		unstableCacheTagCounts: observation.unstableCaches.map((cache) => String(cache.tagCount)),
		unstableCacheTagHashes: observation.unstableCaches.map((cache) => cache.tagHash ?? "none")
	};
}
function getStaticLayoutObservationSkipRejection(observation) {
	for (const [code, matches] of STATIC_LAYOUT_OBSERVATION_SKIP_RULES) if (matches(observation)) return {
		code,
		fields: createStaticLayoutObservationTraceFields(observation)
	};
	return null;
}
function isAppLayoutObservationUnsafeForStaticReuse(observation) {
	return getStaticLayoutObservationSkipRejection(observation) !== null;
}
function createAppLayoutParamAccessTracker() {
	const observations = /* @__PURE__ */ new Map();
	const ensureObservation = (layoutId) => {
		const existing = observations.get(layoutId);
		if (existing) return existing;
		const created = {
			cacheLifeObserved: false,
			cacheTags: /* @__PURE__ */ new Set(),
			cacheableFetches: /* @__PURE__ */ new Set(),
			dynamicFetches: /* @__PURE__ */ new Set(),
			dynamicUsageObserved: false,
			finiteRevalidateSeconds: null,
			keys: /* @__PURE__ */ new Set(),
			observed: false,
			paramScopeKeys: /* @__PURE__ */ new Set(),
			probeComplete: false,
			requestApis: /* @__PURE__ */ new Set(),
			unstableCaches: /* @__PURE__ */ new Map()
		};
		observations.set(layoutId, created);
		return created;
	};
	const markObserved = (layoutId, keys) => {
		const observation = ensureObservation(layoutId);
		observation.observed = true;
		for (const key of keys) observation.keys.add(key);
	};
	const markProbeComplete = (layoutId) => {
		ensureObservation(layoutId).probeComplete = true;
	};
	const runWithIsolatedProbeDependencies = (probe) => {
		if (!isInsideUnifiedScope()) return probe();
		return runWithUnifiedStateMutation((ctx) => {
			ctx.cacheableFetchUrls = /* @__PURE__ */ new Set();
			ctx.currentRequestTags = [];
			ctx.currentFetchSoftTags = [];
			ctx.dynamicFetchUrls = /* @__PURE__ */ new Set();
			ctx.dynamicUsageDetected = false;
			ctx.renderRequestApiUsage = /* @__PURE__ */ new Set();
			ctx.requestScopedCacheLife = null;
			ctx.unstableCacheObservations = /* @__PURE__ */ new Map();
		}, probe);
	};
	const recordProbeDependencies = (layoutId) => {
		const observation = ensureObservation(layoutId);
		if (peekDynamicUsage()) observation.dynamicUsageObserved = true;
		if (_peekRequestScopedCacheLife() !== null) observation.cacheLifeObserved = true;
		for (const tag of getCollectedFetchTags()) observation.cacheTags.add(tag);
		for (const url of peekCacheableFetchObservations()) observation.cacheableFetches.add(url);
		for (const url of peekDynamicFetchObservations()) observation.dynamicFetches.add(url);
		for (const requestApi of peekRenderRequestApiUsage()) observation.requestApis.add(requestApi);
		for (const unstableCache of _peekUnstableCacheObservations()) observation.unstableCaches.set(unstableCache.keyHash, unstableCache);
	};
	return {
		createThenableParamsObserver(layoutId) {
			return { observeParamAccess(keys) {
				markObserved(layoutId, keys);
			} };
		},
		getLayoutObservation(layoutId) {
			const observation = observations.get(layoutId);
			if (!observation) return {
				cacheLifeObserved: false,
				cacheTags: [],
				cacheableFetchCount: 0,
				completeness: "unknown",
				dynamicFetchCount: 0,
				dynamicUsageObserved: false,
				finiteRevalidateSeconds: null,
				keys: [],
				observed: false,
				paramScopeKeys: [],
				requestApis: [],
				unstableCaches: []
			};
			return {
				cacheLifeObserved: observation.cacheLifeObserved,
				cacheTags: [...observation.cacheTags].sort(),
				cacheableFetchCount: observation.cacheableFetches.size,
				completeness: observation.probeComplete ? "complete" : "unknown",
				dynamicFetchCount: observation.dynamicFetches.size,
				dynamicUsageObserved: observation.dynamicUsageObserved,
				finiteRevalidateSeconds: observation.finiteRevalidateSeconds,
				keys: [...observation.keys].sort(),
				observed: observation.observed,
				paramScopeKeys: [...observation.paramScopeKeys].sort(),
				requestApis: [...observation.requestApis].sort(),
				unstableCaches: [...observation.unstableCaches.values()].sort((a, b) => a.keyHash.localeCompare(b.keyHash))
			};
		},
		recordLayoutFiniteRevalidate(layoutId, revalidateSeconds) {
			if (!Number.isFinite(revalidateSeconds) || revalidateSeconds <= 0) return;
			const observation = ensureObservation(layoutId);
			observation.finiteRevalidateSeconds = observation.finiteRevalidateSeconds === null ? revalidateSeconds : Math.min(observation.finiteRevalidateSeconds, revalidateSeconds);
		},
		recordLayoutParamScope(layoutId, paramScopeKeys) {
			const observation = ensureObservation(layoutId);
			for (const key of paramScopeKeys) observation.paramScopeKeys.add(key);
		},
		runLayoutProbe(layoutId, probe) {
			return runWithIsolatedProbeDependencies(() => {
				const result = probe();
				if (!isPromiseLike(result)) {
					recordProbeDependencies(layoutId);
					markProbeComplete(layoutId);
					return result;
				}
				return Promise.resolve(result).then((resolved) => {
					recordProbeDependencies(layoutId);
					markProbeComplete(layoutId);
					return resolved;
				}, (error) => {
					recordProbeDependencies(layoutId);
					throw error;
				});
			});
		}
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-action-request.js
function isPossibleAppRouteActionRequest(request) {
	if (request.method.toUpperCase() !== "POST") return false;
	const contentType = request.headers.get("content-type");
	return request.headers.has("x-rsc-action") || request.headers.has("next-action") || contentType === "application/x-www-form-urlencoded" || contentType?.startsWith("multipart/form-data") === true;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-method.js
function isNonGetOrHead(method) {
	const normalizedMethod = method.toUpperCase();
	return normalizedMethod !== "GET" && normalizedMethod !== "HEAD";
}
function isStaticOrSsgAppPageCandidate(options) {
	if (options.dynamicConfig === "force-dynamic" || options.revalidateSeconds === 0) return false;
	if (options.dynamicConfig === "force-static" || options.dynamicConfig === "error") return true;
	if (options.revalidateSeconds !== null && options.revalidateSeconds > 0) return true;
	if (options.hasGenerateStaticParams) return true;
	return !options.isDynamicRoute;
}
function resolveAppPageMethodResponse(options) {
	if (!isNonGetOrHead(options.request.method)) return null;
	if (isPossibleAppRouteActionRequest(options.request)) return null;
	if (!isStaticOrSsgAppPageCandidate(options)) return null;
	const headers = new Headers();
	mergeMiddlewareResponseHeaders(headers, options.middlewareHeaders ?? null);
	return methodNotAllowedResponse("GET, HEAD", { headers });
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-route-module-loader.js
/**
* Lazy route-module hydration for the App Router RSC entry.
*
* The generated route table (see `entries/app-rsc-manifest.ts`) emits page and
* route-handler modules as lazy `() => import()` thunks instead of eager
* `import * as mod_N` namespaces. This keeps those modules out of the RSC
* entry's top-level evaluation, so an app with many routes — or routes with
* expensive module-level initialization — does not pay to evaluate every route
* module at Worker startup. Only the module(s) for the matched route are
* evaluated, on demand.
*
* `ensureAppRouteModulesLoaded` resolves a route's lazy thunks and populates
* the synchronous module fields that the rest of the request pipeline reads
* directly (`page`, `routeHandler`, layouts, templates, boundaries, and
* parallel-slot modules). It is:
*
*  - idempotent: once a route is loaded it returns immediately;
*  - dedup'd: concurrent calls for the same route share one in-flight promise,
*    so a burst of requests to the same route triggers a single import.
*
* Callers must `await` it before any synchronous read of route modules
* (segment config, fetch-cache mode, runtime resolution, dispatch branch,
* element building, etc.).
*
* Every thunk is invoked via `runOutsideRequestScopes`. Hydration runs inside
* the matched request's scopes, and a dynamic `import()` propagates
* AsyncLocalStorage into the imported module's top-level evaluation — so
* without that guard, module-scope `headers()`/`cookies()`/`after()` would bind
* to whichever request happened to be first. Since a module evaluates once per
* isolate and its namespace is cached here, that first request's data would
* then be served to every later one. Matching Next.js, which loads components
* before entering the request store, module scope simply sees no request.
*/
function pushFieldLoad(loads, target, field, loader) {
	if (!loader || target[field] != null) return;
	loads.push(runOutsideRequestScopes(loader).then((module) => {
		target[field] = module;
	}));
}
function pushArrayLoads(loads, target, loaders) {
	if (!target || !loaders) return;
	const slots = target;
	for (const [index, loader] of loaders.entries()) {
		if (index >= slots.length || !loader || slots[index] != null) continue;
		loads.push(runOutsideRequestScopes(loader).then((module) => {
			slots[index] = module;
		}));
	}
}
/**
* Hydrate one lazily-imported intercept module onto the intercept, dedup'd
* through `__loadState` so concurrent navigations share a single import.
*
* The intercept's page and not-found modules were loaded inline at their call
* sites, which meant they missed the isolation every other route module gets.
* They are user modules cached for the isolate's lifetime just like the rest,
* so they belong on this path.
*/
async function hydrateInterceptModule(intercept, loader, field, loadingField) {
	const loadState = intercept.__loadState;
	const cached = loadState?.[field];
	if (cached != null) intercept[field] = cached;
	if (!loader || intercept[field] != null) return;
	const loading = loadState?.[loadingField] ?? runOutsideRequestScopes(loader).then((module) => {
		intercept[field] = module;
		if (loadState) {
			loadState[field] = module;
			loadState[loadingField] = null;
		}
		return module;
	}).catch((error) => {
		if (loadState) loadState[loadingField] = null;
		throw error;
	});
	if (loadState) loadState[loadingField] = loading;
	intercept[field] = await loading;
}
/** Hydrate an intercepting route's page module onto `intercept.page`. */
function loadAppInterceptPage(intercept) {
	return hydrateInterceptModule(intercept, intercept.__pageLoader, "page", "pageLoading");
}
/** Hydrate an intercepting route's not-found boundary onto `intercept.notFound`. */
function loadAppInterceptNotFound(intercept) {
	return hydrateInterceptModule(intercept, intercept.__loadNotFound, "notFound", "notFoundLoading");
}
function loadAppInterceptLayouts(intercept) {
	const loadState = intercept.__loadState;
	if (loadState?.interceptLayoutsLoading) return loadState.interceptLayoutsLoading;
	const loads = [];
	pushArrayLoads(loads, intercept.interceptLayouts, intercept.__loadInterceptLayouts);
	pushArrayLoads(loads, intercept.interceptLoadings, intercept.__loadInterceptLoadings);
	if (loads.length === 0) return Promise.resolve(intercept.interceptLayouts ?? []);
	const loading = Promise.all(loads).then(() => {
		if (loadState) loadState.interceptLayoutsLoading = null;
		return intercept.interceptLayouts ?? [];
	}).catch((error) => {
		if (loadState) loadState.interceptLayoutsLoading = null;
		throw error;
	});
	if (loadState) loadState.interceptLayoutsLoading = loading;
	return loading;
}
/**
* Resolve a route's lazy modules and assign them onto the route's synchronous
* module fields. Returns the same route reference (synchronously when already
* loaded, otherwise after the in-flight import resolves). Safe to call on
* `null`/`undefined` routes and on eager routes that have no lazy thunks.
*/
function ensureAppRouteModulesLoaded(route) {
	if (!route || route.__loaded) return route;
	if (route.__loading) return route.__loading;
	const loadPage = route.__loadPage;
	const loadRouteHandler = route.__loadRouteHandler;
	const loads = [];
	pushFieldLoad(loads, route, "page", loadPage);
	pushFieldLoad(loads, route, "routeHandler", loadRouteHandler);
	pushFieldLoad(loads, route, "loading", route.__loadLoading);
	pushFieldLoad(loads, route, "error", route.__loadError);
	pushFieldLoad(loads, route, "notFound", route.__loadNotFound);
	pushFieldLoad(loads, route, "forbidden", route.__loadForbidden);
	pushFieldLoad(loads, route, "unauthorized", route.__loadUnauthorized);
	pushArrayLoads(loads, route.layouts, route.__loadLayouts);
	pushArrayLoads(loads, route.templates, route.__loadTemplates);
	pushArrayLoads(loads, route.loadings, route.__loadLoadings);
	pushArrayLoads(loads, route.errors, route.__loadErrors);
	pushArrayLoads(loads, route.errorPaths, route.__loadErrorPaths);
	pushArrayLoads(loads, route.notFounds, route.__loadNotFounds);
	pushArrayLoads(loads, route.forbiddens, route.__loadForbiddens);
	pushArrayLoads(loads, route.unauthorizeds, route.__loadUnauthorizeds);
	for (const slot of Object.values(route.slots ?? {})) {
		pushFieldLoad(loads, slot, "page", slot.__loadPage);
		pushFieldLoad(loads, slot, "default", slot.__loadDefault);
		pushFieldLoad(loads, slot, "layout", slot.__loadLayout);
		pushArrayLoads(loads, slot.configLayouts, slot.__loadConfigLayouts);
		pushFieldLoad(loads, slot, "loading", slot.__loadLoading);
		pushArrayLoads(loads, slot.loadings, slot.__loadLoadings);
		pushFieldLoad(loads, slot, "error", slot.__loadError);
		pushFieldLoad(loads, slot, "notFound", slot.__loadNotFound);
	}
	if (loads.length === 0) {
		route.__loaded = true;
		return route;
	}
	const loading = Promise.all(loads).then(() => {
		route.__loaded = true;
		route.__loading = null;
		return route;
	}).catch((error) => {
		route.__loading = null;
		throw error;
	});
	route.__loading = loading;
	return loading;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-request.js
function pickRouteParams(matchedParams, routeParamNames) {
	const params = {};
	for (const paramName of routeParamNames) {
		const value = matchedParams[paramName];
		if (value !== void 0) params[paramName] = value;
	}
	return params;
}
function remapRouteParams(matchedParams, source) {
	if (source.paramPatternParts && source.routePatternParts) {
		const urlParts = [];
		for (const part of source.routePatternParts) {
			if (!part.startsWith(":")) {
				urlParts.push(part);
				continue;
			}
			const value = matchedParams[part.slice(1).replace(/[+*]$/, "")];
			if (Array.isArray(value)) urlParts.push(...value.map(encodeURIComponent));
			else if (value !== void 0) urlParts.push(encodeURIComponent(value));
		}
		const slotParams = matchRoutePattern(urlParts, source.paramPatternParts);
		if (slotParams) return slotParams;
	}
	if (!source.paramAliases) return matchedParams;
	const params = { ...matchedParams };
	for (const [routeParamName, sourceParamName] of Object.entries(source.paramAliases)) {
		const value = matchedParams[routeParamName];
		if (value === void 0) continue;
		delete params[routeParamName];
		params[sourceParamName] = value;
	}
	return params;
}
function collectParentParamNames(routeSegments, boundaryPosition) {
	const limit = Math.max(0, Math.min(boundaryPosition, routeSegments.length));
	const names = [];
	for (const segment of routeSegments.slice(0, limit)) {
		const name = getAppPageSegmentParamName(segment);
		if (name && !names.includes(name)) names.push(name);
	}
	return names;
}
function getLayoutGenerateStaticParamsBoundary(routeSegments, layoutTreePosition) {
	let boundary = Math.min((layoutTreePosition ?? 0) - 1, routeSegments.length - 1);
	while (boundary >= 0) {
		const segment = routeSegments[boundary];
		if (!segment.startsWith("@") && !(segment.startsWith("(") && segment.endsWith(")"))) break;
		boundary -= 1;
	}
	return boundary;
}
function getParallelParentParamNames(routeParamNames, branch, boundaryPosition) {
	const slotParamNames = branch.paramNames ?? routeParamNames;
	const branchParamNames = collectParentParamNames(branch.routeSegments ?? [], boundaryPosition);
	const branchParamNameSet = new Set((branch.routeSegments ?? []).flatMap((segment) => {
		const name = getAppPageSegmentParamName(segment);
		return name ? [name] : [];
	}));
	const ownerParamNames = slotParamNames.filter((name) => !branchParamNameSet.has(name));
	return [.../* @__PURE__ */ new Set([...ownerParamNames, ...branchParamNames])];
}
function resolveAppPageGenerateStaticParamsSources(options) {
	const sources = [];
	options.layouts?.forEach((layout, index) => {
		if (typeof layout?.generateStaticParams !== "function") return;
		sources.push({
			chained: true,
			generateStaticParams: layout.generateStaticParams,
			parentParamNames: collectParentParamNames(options.routeSegments, getLayoutGenerateStaticParamsBoundary(options.routeSegments, options.layoutTreePositions?.[index]))
		});
	});
	if (typeof options.page?.generateStaticParams === "function") sources.push({
		chained: true,
		generateStaticParams: options.page.generateStaticParams,
		parentParamNames: collectParentParamNames(options.routeSegments, Math.max(0, options.routeSegments.length - 1))
	});
	const routeParamNames = options.routeSegments.flatMap((segment) => {
		const name = getAppPageSegmentParamName(segment);
		return name ? [name] : [];
	});
	for (const [independentChain, parallelBranch] of (options.parallelBranches ?? []).entries()) {
		if (!parallelBranch) continue;
		const slotParamNames = parallelBranch.paramNames ?? routeParamNames;
		const paramAliases = Object.fromEntries(routeParamNames.flatMap((routeParamName, index) => {
			const slotParamName = slotParamNames[index];
			return slotParamName && slotParamName !== routeParamName ? [[routeParamName, slotParamName]] : [];
		}));
		const addParallelSource = (module, boundaryPosition) => {
			if (typeof module?.generateStaticParams !== "function") return;
			sources.push({
				generateStaticParams: module.generateStaticParams,
				independentChain,
				...Object.keys(paramAliases).length > 0 ? { paramAliases } : {},
				...parallelBranch.patternParts ? { paramPatternParts: parallelBranch.patternParts } : {},
				...options.routePatternParts ? { routePatternParts: options.routePatternParts } : {},
				parentParamNames: getParallelParentParamNames(routeParamNames, parallelBranch, boundaryPosition)
			});
		};
		addParallelSource(parallelBranch.layout, -1);
		parallelBranch.configLayouts?.forEach((layout, index) => {
			addParallelSource(layout, getLayoutGenerateStaticParamsBoundary(parallelBranch.routeSegments ?? [], parallelBranch.configLayoutTreePositions?.[index]));
		});
		addParallelSource(parallelBranch.page, Math.max(0, (parallelBranch.routeSegments?.length ?? 0) - 1));
	}
	return sources;
}
function areStaticParamsAllowed(params, staticParams, allowMissingValues = false) {
	const paramKeys = Object.keys(params);
	const stringParamMatches = (value, staticValue) => value === encodeURIComponent(staticValue);
	return staticParams.some((staticParamSet) => paramKeys.every((key) => {
		const value = params[key];
		const staticValue = staticParamSet[key];
		if (!Object.hasOwn(staticParamSet, key)) return allowMissingValues;
		if (Array.isArray(value)) return Array.isArray(staticValue) && value.length === staticValue.length && value.every((part, index) => typeof staticValue[index] === "string" ? stringParamMatches(part, staticValue[index]) : part === staticValue[index]);
		if (typeof staticValue === "string") return stringParamMatches(value, staticValue);
		if (typeof staticValue === "number" || typeof staticValue === "boolean") return String(value) === String(staticValue);
		return JSON.stringify(value) === JSON.stringify(staticValue);
	}));
}
function remapStaticParamsToRouteParams(staticParams, source) {
	if (!source.paramAliases) return [...staticParams];
	const routeParamNamesBySourceName = new Map(Object.entries(source.paramAliases).map(([routeParamName, sourceParamName]) => [sourceParamName, routeParamName]));
	return staticParams.map((params) => Object.fromEntries(Object.entries(params).map(([name, value]) => [routeParamNamesBySourceName.get(name) ?? name, value])));
}
async function generateIndependentStaticParams(sources, primaryParams, requestParams) {
	let rows = (primaryParams ?? []).map((params) => ({
		params,
		branchParams: {}
	}));
	let hasParentParams = rows.length > 0;
	let validated = false;
	for (const source of sources) {
		const parents = hasParentParams ? rows : [{
			params: {},
			branchParams: {}
		}];
		const nextRows = [];
		for (const parent of parents) {
			const sourceParams = remapRouteParams({
				...requestParams,
				...parent.params
			}, source);
			const branchParams = remapRouteParams(parent.branchParams, source);
			const result = await runWithFetchDedupe(() => source.generateStaticParams({ params: {
				...pickRouteParams(sourceParams, source.parentParamNames),
				...branchParams
			} }));
			if (!Array.isArray(result)) {
				if (hasParentParams) nextRows.push(parent);
				continue;
			}
			validated = true;
			const routeResults = remapStaticParamsToRouteParams(result, source);
			if (routeResults.length === 0) {
				if (hasParentParams) nextRows.push(parent);
				continue;
			}
			for (const routeResult of routeResults) nextRows.push({
				params: {
					...parent.params,
					...routeResult
				},
				branchParams: {
					...parent.branchParams,
					...routeResult
				}
			});
		}
		rows = nextRows;
		hasParentParams = rows.length > 0;
	}
	return {
		staticParams: rows.map((row) => row.params),
		validated
	};
}
async function generateChainedStaticParams(sources) {
	let generatedParams = [];
	for (const source of sources) {
		const hasParentParams = generatedParams.length > 0;
		const parents = hasParentParams ? generatedParams : [{}];
		const nextParams = [];
		for (const parentParams of parents) {
			const result = await runWithFetchDedupe(() => source.generateStaticParams({ params: parentParams }));
			if (Array.isArray(result) && result.length > 0) {
				for (const item of result) if (item !== null && typeof item === "object" && !Array.isArray(item)) nextParams.push({
					...parentParams,
					...item
				});
			} else if (hasParentParams) nextParams.push(parentParams);
		}
		generatedParams = nextParams;
	}
	return generatedParams;
}
function normalizeGenerateStaticParams(generateStaticParams) {
	return (Array.isArray(generateStaticParams) ? generateStaticParams : [generateStaticParams]).flatMap((source) => {
		if (typeof source === "function") return [{
			generateStaticParams: source,
			parentParamNames: []
		}];
		if (typeof source?.generateStaticParams === "function") return [source];
		return [];
	});
}
async function validateAppPageDynamicParams(options) {
	if (!options.enforceStaticParamsOnly || !options.isDynamicRoute) return null;
	const generateStaticParamsSources = normalizeGenerateStaticParams(options.generateStaticParams);
	if (generateStaticParamsSources.length === 0) return notFoundResponse();
	const chainedSources = generateStaticParamsSources.filter((source) => source.chained);
	let chainedStaticParams = null;
	if (chainedSources.length > 0) chainedStaticParams = await generateChainedStaticParams(chainedSources);
	const independentChains = /* @__PURE__ */ new Map();
	for (const source of generateStaticParamsSources.filter((source) => !source.chained)) {
		const chain = independentChains.get(source.independentChain ?? source) ?? [];
		chain.push(source);
		independentChains.set(source.independentChain ?? source, chain);
	}
	let validatedIndependentResults = false;
	for (const sources of independentChains.values()) {
		const result = await generateIndependentStaticParams(sources, chainedStaticParams, options.params);
		if (result.validated) {
			validatedIndependentResults = true;
			if (!areStaticParamsAllowed(options.params, result.staticParams, true)) return notFoundResponse();
		}
	}
	if (chainedStaticParams && !validatedIndependentResults) {
		if (!areStaticParamsAllowed(options.params, chainedStaticParams)) return notFoundResponse();
	}
	return null;
}
async function resolveAppPageInterceptState(options) {
	if (!options.isRscRequest) return { kind: "none" };
	const intercept = options.findIntercept(options.cleanPathname);
	if (!intercept) return { kind: "none" };
	await loadAppInterceptPage(intercept);
	await loadAppInterceptNotFound(intercept);
	if (intercept.__loadInterceptLayouts || intercept.__loadInterceptLoadings) await loadAppInterceptLayouts(intercept);
	const sourceRoute = await options.getSourceRoute(intercept.sourceRouteIndex);
	if (!sourceRoute) return { kind: "none" };
	if (sourceRoute === options.currentRoute) return {
		kind: "current-route",
		intercept
	};
	return {
		kind: "source-route",
		intercept,
		sourceRoute
	};
}
async function resolveAppPageInterceptionRerenderTarget(options) {
	const interceptState = await resolveAppPageInterceptState({
		cleanPathname: options.cleanPathname,
		currentRoute: options.currentRoute,
		findIntercept: options.findIntercept,
		getRouteParamNames: options.getRouteParamNames,
		getSourceRoute: options.getSourceRoute,
		isRscRequest: options.isRscRequest,
		toInterceptOpts: options.toInterceptOpts
	});
	if (interceptState.kind === "source-route") {
		const sourceMatchedParams = interceptState.intercept.sourceMatchedParams ?? interceptState.intercept.matchedParams;
		return {
			interceptOpts: options.toInterceptOpts(interceptState.intercept),
			navigationParams: {
				...sourceMatchedParams,
				...interceptState.intercept.matchedParams
			},
			params: pickRouteParams(sourceMatchedParams, options.getRouteParamNames(interceptState.sourceRoute)),
			route: interceptState.sourceRoute
		};
	}
	return {
		interceptOpts: interceptState.kind === "current-route" ? options.toInterceptOpts(interceptState.intercept) : void 0,
		navigationParams: options.currentParams,
		params: options.currentParams,
		route: options.currentRoute
	};
}
async function resolveAppPageIntercept(options) {
	const interceptState = await resolveAppPageInterceptState({
		cleanPathname: options.cleanPathname,
		currentRoute: options.currentRoute,
		findIntercept: options.findIntercept,
		getRouteParamNames: options.getRouteParamNames,
		getSourceRoute: options.getSourceRoute,
		isRscRequest: options.isRscRequest,
		toInterceptOpts: options.toInterceptOpts
	});
	if (interceptState.kind === "source-route") {
		const renderRoute = interceptState.sourceRoute;
		const interceptOpts = options.toInterceptOpts(interceptState.intercept);
		const sourceMatchedParams = interceptState.intercept.sourceMatchedParams ?? interceptState.intercept.matchedParams;
		const navigationParams = {
			...sourceMatchedParams,
			...interceptState.intercept.matchedParams
		};
		const renderSearchParams = options.resolveSearchParams ? await options.resolveSearchParams(renderRoute, options.searchParams) : options.searchParams;
		const renderParams = pickRouteParams(sourceMatchedParams, options.getRouteParamNames(interceptState.sourceRoute));
		options.setNavigationContext({
			params: options.resolveNavigationParams(renderRoute, navigationParams, options.cleanPathname, interceptOpts),
			pathname: options.cleanPathname,
			searchParams: renderSearchParams
		});
		const interceptElement = await options.buildPageElement(renderRoute, renderParams, interceptOpts, renderSearchParams, options.layoutParamAccess);
		return {
			interceptOpts: void 0,
			response: await options.renderInterceptResponse(renderRoute, interceptElement)
		};
	}
	return {
		interceptOpts: interceptState.kind === "current-route" ? options.toInterceptOpts(interceptState.intercept) : void 0,
		response: null
	};
}
async function buildAppPageElement(options) {
	try {
		return {
			element: await options.buildPageElement(),
			response: null
		};
	} catch (error) {
		const buildSpecialError = options.resolveSpecialError(error);
		const specialError = (buildSpecialError ? await options.probePageSpecialError?.() : null) ?? buildSpecialError;
		if (specialError) return {
			element: null,
			response: await options.renderSpecialError(specialError)
		};
		const errorBoundaryResponse = await options.renderErrorBoundaryPage(error);
		if (errorBoundaryResponse) return {
			element: null,
			response: errorBoundaryResponse
		};
		throw error;
	}
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/text-stream.js
/**
* Helpers for the repeated `new TextDecoder()` + `ReadableStream` chunk-loop
* pattern used across the server. Each helper handles the streaming-decode
* boundary correctly (final empty `decoder.decode()` flush so any incomplete
* trailing UTF-8 sequence is reported).
*
* Sites with additional load-bearing behaviour (line-buffered transforms,
* raw-byte accumulators, mixed string/Uint8Array streams, cache-key body
* canonicalisation) intentionally still inline their own decoder.
*/
/**
* Drain a UTF-8 byte stream and return the full decoded text. The stream
* reader is released on both success and failure.
*/
async function readStreamAsText(stream) {
	const reader = stream.getReader();
	const decoder = new TextDecoder();
	const chunks = [];
	try {
		for (;;) {
			const { done, value } = await reader.read();
			if (done) break;
			chunks.push(decoder.decode(value, { stream: true }));
		}
		chunks.push(decoder.decode());
		return chunks.join("");
	} finally {
		reader.releaseLock();
	}
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-cache-finalizer.js
function applyPendingDynamicCdnHeaders(headers, tags, options = {}) {
	clearSharedCacheOverrides(headers);
	applyCdnResponseHeaders(headers, {
		cacheControl: headers.get("Cache-Control") ?? "",
		pendingDynamicCheck: true,
		tags
	});
	finalizePendingCacheStateHeaders(headers, options);
}
function applyMountedSlotRscNoStoreHeaders(headers, options = {}) {
	clearSharedCacheOverrides(headers);
	applyCdnResponseHeaders(headers, { cacheControl: NO_STORE_CACHE_CONTROL });
	finalizePendingCacheStateHeaders(headers, {
		...options,
		preserveMissingCacheState: true
	});
}
function clearSharedCacheOverrides(headers) {
	headers.delete("CDN-Cache-Control");
	headers.delete("Cloudflare-CDN-Cache-Control");
	headers.delete("Cache-Tag");
}
function finalizePendingCacheStateHeaders(headers, options = {}) {
	const hadCacheState = headers.has("X-Vinext-Cache") || headers.has("x-nextjs-cache");
	if (options.omitCacheState === true || options.preserveMissingCacheState === true && !hadCacheState) {
		headers.delete(VINEXT_CACHE_HEADER);
		headers.delete(NEXTJS_CACHE_HEADER);
		return;
	}
	setCacheStateHeaders(headers, "MISS");
}
function resolveAppPageCacheControl(options) {
	let revalidateSeconds = options.revalidateSeconds;
	let expireSeconds = options.expireSeconds;
	const requestCacheLife = options.requestCacheLife;
	if (requestCacheLife?.revalidate !== void 0) revalidateSeconds = revalidateSeconds === null ? requestCacheLife.revalidate : Math.min(revalidateSeconds, requestCacheLife.revalidate);
	if (requestCacheLife?.expire !== void 0) expireSeconds = requestCacheLife.expire;
	if (revalidateSeconds === null || Number.isNaN(revalidateSeconds) || revalidateSeconds <= 0) return null;
	return isrCacheControl(revalidateSeconds, {
		expireSeconds,
		staleSeconds: resolveClientStaleTimeSeconds(requestCacheLife)
	});
}
function finalizeAppPageHtmlCacheResponse(response, options) {
	if (!response.body) return response;
	const [streamForClient, streamForCache] = response.body.tee();
	const htmlKey = options.isrHtmlKey(options.cleanPathname);
	const rscKey = options.isrRscKey(options.cleanPathname, null, void 0, options.interceptionContext);
	const clientHeaders = new Headers(response.headers);
	if (options.preserveClientResponseHeaders !== true) applyPendingDynamicCdnHeaders(clientHeaders, options.getPageTags(), { omitCacheState: options.omitPendingDynamicCacheState === true });
	const cachePromise = (async () => {
		try {
			const cachedHtml = await readStreamAsText(streamForCache);
			if (options.capturedDynamicUsageBeforeContextCleanup?.() === true || options.consumeDynamicUsage()) {
				options.isrDebug?.("HTML cache write skipped (dynamic usage during render)", htmlKey);
				return;
			}
			const cacheControl = resolveAppPageCacheControl({
				expireSeconds: options.expireSeconds,
				requestCacheLife: options.getRequestCacheLife?.(),
				revalidateSeconds: options.revalidateSeconds
			});
			if (!cacheControl) {
				options.isrDebug?.("HTML cache write skipped (no cache policy)", htmlKey);
				return;
			}
			const pageTags = options.getPageTags();
			const observationState = options.consumeRenderObservationState?.() ?? createEmptyAppPageRenderObservationState();
			const htmlRenderObservation = options.createHtmlRenderObservation?.({
				cacheTags: pageTags,
				state: observationState
			});
			const rscRenderObservation = options.createRscRenderObservation?.({
				cacheTags: pageTags,
				state: observationState
			});
			const linkHeader = response.headers.get("link");
			const writes = [options.isrSet(htmlKey, buildAppPageCacheValue(cachedHtml, void 0, 200, htmlRenderObservation, linkHeader ? { link: linkHeader } : void 0), {
				cacheControl,
				tags: pageTags
			})];
			if (options.capturedRscDataPromise) writes.push(options.capturedRscDataPromise.then((rscData) => options.isrSet(rscKey, buildAppPageCacheValue("", rscData, 200, rscRenderObservation), {
				cacheControl,
				tags: pageTags
			})));
			await Promise.all(writes);
			options.isrDebug?.("HTML cache written", htmlKey);
		} catch (cacheError) {
			console.error("[vinext] ISR cache write error:", cacheError);
		}
	})();
	options.waitUntil?.(cachePromise);
	return new Response(streamForClient, {
		status: response.status,
		statusText: response.statusText,
		headers: clientHeaders
	});
}
function finalizeAppPageRscCacheResponse(response, options) {
	scheduleAppPageRscCacheWrite(options);
	const isMountedSlotVariant = Boolean(options.mountedSlotsHeader);
	if (options.preserveClientResponseHeaders === true && !isMountedSlotVariant) return response;
	const clientHeaders = new Headers(response.headers);
	if (isMountedSlotVariant) applyMountedSlotRscNoStoreHeaders(clientHeaders, { omitCacheState: options.omitPendingDynamicCacheState === true });
	else applyPendingDynamicCdnHeaders(clientHeaders, options.getPageTags(), { omitCacheState: options.omitPendingDynamicCacheState === true });
	return new Response(response.body, {
		status: response.status,
		statusText: response.statusText,
		headers: clientHeaders
	});
}
function scheduleAppPageRscCacheWrite(options) {
	const capturedRscDataPromise = options.capturedRscDataPromise;
	if (!capturedRscDataPromise || options.dynamicUsedDuringBuild || options.mountedSlotsHeader) return false;
	const rscKey = options.isrRscKey(options.cleanPathname, null, options.renderMode, options.interceptionContext);
	const cachePromise = (async () => {
		try {
			const rscData = await capturedRscDataPromise;
			if (options.consumeDynamicUsage()) {
				options.isrDebug?.("RSC cache write skipped (dynamic usage during render)", rscKey);
				return;
			}
			const cacheControl = resolveAppPageCacheControl({
				expireSeconds: options.expireSeconds,
				requestCacheLife: options.getRequestCacheLife?.(),
				revalidateSeconds: options.revalidateSeconds
			});
			if (!cacheControl) {
				options.isrDebug?.("RSC cache write skipped (no cache policy)", rscKey);
				return;
			}
			const pageTags = options.getPageTags();
			const observationState = options.consumeRenderObservationState?.() ?? createEmptyAppPageRenderObservationState();
			const rscRenderObservation = options.createRscRenderObservation?.({
				cacheTags: pageTags,
				state: observationState
			});
			await options.isrSet(rscKey, buildAppPageCacheValue("", rscData, 200, rscRenderObservation), {
				cacheControl,
				tags: pageTags
			});
			options.isrDebug?.("RSC cache written", rscKey);
		} catch (cacheError) {
			console.error("[vinext] ISR RSC cache write error:", cacheError);
		}
	})();
	options.waitUntil?.(cachePromise);
	return true;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/static-layout-client-reuse-proof.js
function createStaticLayoutClientReuseRouteId(layoutId) {
	return `static-layout:${createClientReusePayloadHash(layoutId)}`;
}
function createCanonicalProofPairs(input) {
	return ARTIFACT_COMPATIBILITY_PROOF_FIELDS.map((field) => [field, input.artifactCompatibility[field]]);
}
function createStaticLayoutClientReusePayloadHash(input) {
	return createClientReusePayloadHash(JSON.stringify({
		artifactCompatibilityPairs: createCanonicalProofPairs(input),
		layoutId: input.layoutId,
		rootBoundaryId: input.rootBoundaryId,
		variantCacheKey: input.variantCacheKey
	}));
}
function createStaticLayoutClientReuseArtifactCompatibility(input) {
	return {
		...input.artifactCompatibility,
		graphVersion: `static-layout-graph:${createClientReusePayloadHash(JSON.stringify({
			layoutId: input.layoutId,
			rootBoundaryId: input.rootBoundaryId
		}))}`,
		renderEpoch: `static-layout:${createClientReusePayloadHash(JSON.stringify({
			layoutId: input.layoutId,
			rootBoundaryId: input.rootBoundaryId,
			variantCacheKey: input.variantCacheKey
		}))}`
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/rsc-completion-metadata.js
var encoder = new TextEncoder();
new TextDecoder();
var FRAME_ESCAPE_BYTE = 255;
var FOOTER_TAG_BYTE = 0;
var FOOTER_PREFIX_BYTES = 2;
var FOOTER_LENGTH_BYTES = 4;
var MAX_FOOTER_BYTES = 256;
function encodeFooter(metadata) {
	const payload = encoder.encode(JSON.stringify(metadata));
	const footer = new Uint8Array(payload.byteLength + FOOTER_LENGTH_BYTES + FOOTER_PREFIX_BYTES);
	if (footer.byteLength > MAX_FOOTER_BYTES) throw new Error("RSC completion metadata exceeded its framing limit");
	footer[0] = FRAME_ESCAPE_BYTE;
	footer[1] = FOOTER_TAG_BYTE;
	footer.set(payload, FOOTER_PREFIX_BYTES);
	new DataView(footer.buffer).setUint32(FOOTER_PREFIX_BYTES + payload.byteLength, payload.byteLength);
	return footer;
}
function escapeFlightChunk(chunk) {
	const firstEscape = chunk.indexOf(FRAME_ESCAPE_BYTE);
	if (firstEscape === -1) return chunk;
	let escapeCount = 1;
	for (let index = firstEscape + 1; index < chunk.byteLength; index++) if (chunk[index] === FRAME_ESCAPE_BYTE) escapeCount++;
	const escaped = new Uint8Array(chunk.byteLength + escapeCount);
	escaped.set(chunk.subarray(0, firstEscape), 0);
	let output = firstEscape;
	for (let index = firstEscape; index < chunk.byteLength; index++) {
		const byte = chunk[index];
		escaped[output++] = byte;
		if (byte === FRAME_ESCAPE_BYTE) escaped[output++] = FRAME_ESCAPE_BYTE;
	}
	return escaped;
}
function appendRscCompletionMetadata(source, getMetadata) {
	const reader = source.getReader();
	return new ReadableStream({
		async pull(controller) {
			const next = await reader.read();
			if (!next.done) {
				controller.enqueue(escapeFlightChunk(next.value));
				return;
			}
			const metadata = getMetadata();
			if (metadata) controller.enqueue(encodeFooter(metadata));
			controller.close();
		},
		cancel(reason) {
			return reader.cancel(reason);
		}
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/skip-cache-proof.js
function createDisabledSkipDisposition() {
	return {
		code: "SKIP_MODEL_DISABLED",
		enabled: false,
		mode: "renderAndSend"
	};
}
function createStaticLayoutSkipDisposition(skippedEntryIds) {
	return {
		code: "SKIP_STATIC_LAYOUT_VERIFIED",
		enabled: true,
		mode: "skipStaticLayout",
		skippedEntryIds: [...skippedEntryIds]
	};
}
function rejectSkipCacheCrossCheck(entry, code, fields = {}) {
	return {
		kind: "rejected",
		rejection: {
			code,
			entryId: entry.id,
			fields
		},
		skipDisposition: createDisabledSkipDisposition()
	};
}
function collectArtifactCompatibilityProofMismatches(artifactCompatibility, proofCompatibility) {
	const mismatchedFields = [];
	for (const field of ARTIFACT_COMPATIBILITY_PROOF_FIELDS) if (artifactCompatibility[field] !== proofCompatibility[field]) mismatchedFields.push(field);
	return mismatchedFields;
}
function isExactArtifactCompatibility(artifactCompatibility, entryCompatibility) {
	return collectArtifactCompatibilityProofMismatches(artifactCompatibility, entryCompatibility).length === 0;
}
function assertNever(value) {
	throw new Error(`Unhandled skip/cache proof state: ${String(value)}`);
}
function createRenderAndSendPlan(options) {
	return {
		kind: "renderAndSend",
		entryRejections: options.entryRejections ?? [],
		...options.manifestRejection ? { manifestRejection: options.manifestRejection } : {},
		skipDisposition: createDisabledSkipDisposition(),
		skipIneligibleEntryIds: options.skipIneligibleEntryIds ?? [],
		skippedEntryIds: []
	};
}
function createVerificationBudgetExceededRejection(totalWireEntries, maxWireEntriesToVerify) {
	return {
		code: "SKIP_VERIFICATION_BUDGET_EXCEEDED",
		fields: {
			totalWireEntries,
			maxWireEntriesToVerify
		}
	};
}
function crossCheckInvalidationProof(entry, invalidation) {
	switch (invalidation.kind) {
		case "valid": return null;
		case "unknown": return rejectSkipCacheCrossCheck(entry, "SKIP_CACHE_INVALIDATION_UNKNOWN");
		case "invalidated": return rejectSkipCacheCrossCheck(entry, "SKIP_CACHE_INVALIDATED", { invalidationEpoch: invalidation.invalidationEpoch });
		default: return assertNever(invalidation);
	}
}
function crossCheckClientReuseManifestEntryWithCache(input) {
	const { cacheDecision, entry } = input;
	if (cacheDecision === null) return rejectSkipCacheCrossCheck(entry, "SKIP_CACHE_PROOF_MISSING");
	if (cacheDecision.kind === "fallback") return rejectSkipCacheCrossCheck(entry, "SKIP_CACHE_PROOF_REJECTED", {
		cacheProofCode: cacheDecision.fallback.code,
		cacheProofMode: cacheDecision.fallback.mode,
		cacheProofScope: cacheDecision.fallback.scope
	});
	const { proof } = cacheDecision;
	if (entry.kind !== "layout" || proof.reuseClass !== "static-layout") return rejectSkipCacheCrossCheck(entry, "SKIP_CACHE_REUSE_CLASS_UNSUPPORTED", {
		entryKind: entry.kind,
		reuseClass: proof.reuseClass
	});
	if (entry.id !== proof.candidateOutput.layoutId) return rejectSkipCacheCrossCheck(entry, "SKIP_CACHE_ENTRY_ID_MISMATCH", {
		cacheEntryId: proof.candidateOutput.layoutId,
		manifestEntryId: entry.id
	});
	const artifactProofMismatches = collectArtifactCompatibilityProofMismatches(input.artifact.compatibility, proof.candidateArtifactCompatibility);
	if (artifactProofMismatches.length > 0) return rejectSkipCacheCrossCheck(entry, "SKIP_CACHE_ARTIFACT_PROOF_MISMATCH", { mismatchedFields: artifactProofMismatches });
	const artifactCompatibility = evaluateArtifactCompatibility(input.artifact.compatibility, entry.artifactCompatibility, { compatibilityMap: input.compatibilityMap });
	if (artifactCompatibility.kind === "unknown") return rejectSkipCacheCrossCheck(entry, "SKIP_CACHE_ARTIFACT_COMPATIBILITY_UNKNOWN", {
		compatibilityFallback: artifactCompatibility.fallback,
		reason: artifactCompatibility.reason
	});
	if (artifactCompatibility.kind === "incompatible") return rejectSkipCacheCrossCheck(entry, "SKIP_CACHE_ARTIFACT_COMPATIBILITY_INCOMPATIBLE", {
		compatibilityFallback: artifactCompatibility.fallback,
		reason: artifactCompatibility.reason
	});
	if (entry.variantCacheKey !== proof.variant.cacheKey) return rejectSkipCacheCrossCheck(entry, "SKIP_CACHE_VARIANT_MISMATCH", {
		cacheVariantCacheKeyHash: createClientReusePayloadHash(proof.variant.cacheKey),
		entryVariantCacheKeyHash: createClientReusePayloadHash(entry.variantCacheKey)
	});
	if (input.artifact.payloadHash === null) return rejectSkipCacheCrossCheck(entry, "SKIP_CACHE_PAYLOAD_HASH_MISSING");
	if (entry.payloadHash !== input.artifact.payloadHash) return rejectSkipCacheCrossCheck(entry, "SKIP_CACHE_PAYLOAD_HASH_MISMATCH", {
		cachePayloadHash: input.artifact.payloadHash,
		entryPayloadHash: entry.payloadHash
	});
	const invalidationRejection = crossCheckInvalidationProof(entry, input.artifact.invalidation);
	if (invalidationRejection) return invalidationRejection;
	const skipDisposition = isExactArtifactCompatibility(input.artifact.compatibility, entry.artifactCompatibility) ? createStaticLayoutSkipDisposition([entry.id]) : createDisabledSkipDisposition();
	return {
		kind: "verified",
		code: "SKIP_CACHE_CROSS_CHECK_PASSED",
		entryId: entry.id,
		fields: {
			entryKind: entry.kind,
			reuseClass: proof.reuseClass,
			variantCacheKeyHash: createClientReusePayloadHash(proof.variant.cacheKey)
		},
		skipDisposition
	};
}
function createClientReuseSkipTransportPlan(input) {
	const { manifest } = input;
	if (manifest.kind === "absent") return createRenderAndSendPlan({});
	if (manifest.kind === "rejected") return createRenderAndSendPlan({ manifestRejection: manifest.rejection });
	const maxWireEntriesToVerify = input.maxWireEntriesToVerify ?? 8;
	if (!Number.isSafeInteger(maxWireEntriesToVerify) || maxWireEntriesToVerify < 0) throw new RangeError("maxWireEntriesToVerify must be a non-negative safe integer");
	const totalWireEntries = manifest.manifest.entries.length + manifest.entryRejections.length;
	if (totalWireEntries > maxWireEntriesToVerify) return createRenderAndSendPlan({
		entryRejections: manifest.entryRejections,
		manifestRejection: createVerificationBudgetExceededRejection(totalWireEntries, maxWireEntriesToVerify)
	});
	const skippedEntryIds = [];
	const skipIneligibleEntryIds = [];
	const entryRejections = [...manifest.entryRejections];
	for (const entry of manifest.manifest.entries) {
		const verification = input.verifyEntry(entry);
		if (verification.kind === "rejected") {
			entryRejections.push(verification.rejection);
			continue;
		}
		if (verification.entryId !== entry.id) {
			entryRejections.push({
				code: "SKIP_CACHE_ENTRY_ID_MISMATCH",
				entryId: entry.id,
				fields: {
					verifierEntryId: verification.entryId,
					manifestEntryId: entry.id
				}
			});
			continue;
		}
		if (verification.skipDisposition.enabled) skippedEntryIds.push(entry.id);
		else skipIneligibleEntryIds.push(entry.id);
	}
	if (skippedEntryIds.length === 0) return createRenderAndSendPlan({
		entryRejections,
		skipIneligibleEntryIds
	});
	return {
		kind: "skip",
		entryRejections,
		skipDisposition: createStaticLayoutSkipDisposition(skippedEntryIds),
		skipIneligibleEntryIds,
		skippedEntryIds
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-render.js
function buildResponseTiming(options) {
	if (options.isProduction) return;
	return {
		compileEnd: options.compileEnd,
		handlerStart: options.handlerStart,
		renderEnd: options.renderEnd,
		responseKind: options.responseKind
	};
}
function readRequestCacheLifeForPrerender(options) {
	if (options.isEdgeRuntime && options.revalidateSeconds === null) return (options.peekRequestCacheLife?.() ?? options.getRequestCacheLife())?.revalidate !== void 0 ? { revalidate: 0 } : null;
	return options.peekRequestCacheLife?.() ?? options.getRequestCacheLife();
}
function resolveConfiguredDynamicStaleTimeSeconds() {
	const seconds = 0;
	return Number.isInteger(seconds) && seconds >= 0 ? seconds : 0;
}
function readRequestCacheLifeForCachePolicy(options) {
	const requestCacheLife = options.getRequestCacheLife();
	if (options.isEdgeRuntime && options.revalidateSeconds === null) return null;
	return requestCacheLife;
}
function applyRequestCacheLife(options) {
	let revalidateSeconds = options.revalidateSeconds;
	let expireSeconds = options.expireSeconds;
	const requestCacheLife = options.requestCacheLife;
	if (requestCacheLife?.revalidate !== void 0) revalidateSeconds = revalidateSeconds === null ? requestCacheLife.revalidate : Math.min(revalidateSeconds, requestCacheLife.revalidate);
	if (requestCacheLife?.expire !== void 0) expireSeconds = requestCacheLife.expire;
	return {
		expireSeconds,
		revalidateSeconds
	};
}
function resolveAppPageCacheWriteRevalidateSeconds(options) {
	if (options.revalidateSeconds === null && (options.isForceStatic || options.isDynamicError)) return Infinity;
	return options.revalidateSeconds;
}
function readRootBoundaryId(element) {
	const rootLayoutTreePath = element[AppElementsWire.keys.rootLayout];
	return typeof rootLayoutTreePath === "string" ? rootLayoutTreePath : null;
}
function createAppPageArtifactCompatibility(element, routePattern) {
	if (!isAppElementsRecord(element)) return;
	const rootBoundaryId = readRootBoundaryId(element);
	return createArtifactCompatibilityEnvelope({
		graphVersion: createArtifactCompatibilityGraphVersion({
			routePattern,
			rootBoundaryId
		}),
		deploymentVersion: "b4523198-dfc7-489f-8799-b05bddd8e10b",
		rootBoundaryId
	});
}
function readStringMetadata(element, key) {
	const value = element[key];
	return typeof value === "string" ? value : null;
}
function createStaticLayoutOutputScope(input) {
	const routeId = readStringMetadata(input.element, AppElementsWire.keys.route);
	if (routeId === null) return null;
	return {
		kind: "layout",
		layoutId: input.layoutId,
		rootBoundaryId: input.artifactCompatibility.rootBoundaryId,
		routeId
	};
}
function createRenderAndSendSkipDisposition() {
	return {
		code: "SKIP_MODEL_DISABLED",
		enabled: false,
		mode: "renderAndSend"
	};
}
function rejectStaticLayoutObservation(entry, code, fields = {}) {
	return {
		kind: "rejected",
		rejection: {
			code,
			entryId: entry.id,
			fields
		},
		skipDisposition: createRenderAndSendSkipDisposition()
	};
}
function rejectUnsafeStaticLayoutObservation(entry, layoutParamAccess) {
	const observation = layoutParamAccess?.getLayoutObservation(entry.id);
	if (!observation) return rejectStaticLayoutObservation(entry, "SKIP_LAYOUT_PARAMS_OBSERVATION_INCOMPLETE");
	const observationRejection = getStaticLayoutObservationSkipRejection(observation);
	if (observationRejection) return rejectStaticLayoutObservation(entry, observationRejection.code, observationRejection.fields);
	return null;
}
function createRenderLifecycleSkipDisposition(input) {
	if (!input.isRscRequest || input.clientReuseManifest === void 0) return;
	const clientReuseManifest = input.clientReuseManifest;
	if (clientReuseManifest.kind !== "parsed" || clientReuseManifest.manifest.entries.length === 0) return;
	if (!isAppElementsRecord(input.element) || input.artifactCompatibility === void 0) return {
		code: "SKIP_MODEL_DISABLED",
		enabled: false,
		mode: "renderAndSend"
	};
	const element = input.element;
	const artifactCompatibility = input.artifactCompatibility;
	const staticLayoutIds = new Set(Object.entries(input.layoutFlags).filter(([, flag]) => flag === "s").map(([layoutId]) => layoutId));
	return createClientReuseSkipTransportPlan({
		manifest: clientReuseManifest,
		verifyEntry(entry) {
			if (entry.kind !== "layout" || !staticLayoutIds.has(entry.id) || AppElementsWire.parseElementKey(entry.id)?.kind !== "layout") return crossCheckClientReuseManifestEntryWithCache({
				artifact: {
					compatibility: artifactCompatibility,
					invalidation: { kind: "unknown" },
					payloadHash: null
				},
				cacheDecision: null,
				entry
			});
			const currentOutput = createStaticLayoutOutputScope({
				artifactCompatibility,
				element,
				layoutId: entry.id
			});
			if (currentOutput === null) return crossCheckClientReuseManifestEntryWithCache({
				artifact: {
					compatibility: artifactCompatibility,
					invalidation: { kind: "unknown" },
					payloadHash: null
				},
				cacheDecision: null,
				entry
			});
			const observationRejection = rejectUnsafeStaticLayoutObservation(entry, input.layoutParamAccess);
			if (observationRejection) return observationRejection;
			const candidateRouteId = createStaticLayoutClientReuseRouteId(entry.id);
			const candidateOutput = {
				...currentOutput,
				routeId: candidateRouteId
			};
			const candidateVariant = buildCacheVariantWithRouteBudget({
				budget: DEFAULT_CACHE_VARIANT_BUDGET,
				dimensions: [],
				output: candidateOutput,
				routeBudget: {
					routeId: candidateRouteId,
					variantCacheKeys: []
				}
			});
			const skipArtifactCompatibility = candidateVariant.kind === "variant" ? createStaticLayoutClientReuseArtifactCompatibility({
				artifactCompatibility,
				layoutId: entry.id,
				rootBoundaryId: candidateOutput.rootBoundaryId,
				routeId: candidateOutput.routeId,
				variantCacheKey: candidateVariant.variant.cacheKey
			}) : artifactCompatibility;
			const cacheDecision = createStaticLayoutArtifactReuseDecision({
				candidateArtifactCompatibility: skipArtifactCompatibility,
				candidateObservation: buildRenderObservation({
					boundaryOutcome: { kind: "success" },
					cacheability: "public",
					cacheTags: [],
					completeness: "complete",
					dynamicFetches: [],
					output: candidateOutput,
					pathTags: [input.cleanPathname],
					requestApis: buildRenderRequestApiObservations({
						completeness: "complete",
						observed: []
					})
				}),
				candidateVariant,
				currentArtifactCompatibility: skipArtifactCompatibility,
				currentOutput
			});
			return crossCheckClientReuseManifestEntryWithCache({
				artifact: {
					compatibility: skipArtifactCompatibility,
					invalidation: { kind: "valid" },
					payloadHash: candidateVariant.kind === "variant" ? createStaticLayoutClientReusePayloadHash({
						artifactCompatibility: skipArtifactCompatibility,
						layoutId: entry.id,
						rootBoundaryId: candidateOutput.rootBoundaryId,
						routeId: candidateOutput.routeId,
						variantCacheKey: candidateVariant.variant.cacheKey
					}) : null
				},
				cacheDecision,
				entry
			});
		}
	}).skipDisposition;
}
function isSkipTransportEnabled(skipDisposition) {
	return skipDisposition?.enabled === true;
}
/**
* Wraps an RSC response body to report invalid dynamic usage errors after the
* stream is fully consumed. In dev mode, errors from cookies()/headers() inside
* "use cache" may be caught by user try/catch and silently swallowed — this
* wrapper waits for the stream to drain and surfaces any recorded error to the
* terminal (and, via HMR, the browser dev overlay).
*
* Dedups against React's Flight error chunk: if the recorded error already
* carries a `digest`, React's serverComponentsErrorHandler has already stamped
* it and emitted it into the RSC stream. Skipping `console.error` prevents
* double-logging. Caught cases (no digest) still surface here.
*
* Ported from Next.js:
*   https://github.com/vercel/next.js/commit/f5e54c06726b571a042fce67417e40a29f6b8689
*   https://github.com/vercel/next.js/pull/93706
*/
function wrapRscResponseForDevErrorReporting(response, consumeInvalidDynamicUsageError) {
	const originalBody = response.body;
	if (!originalBody) return response;
	let consumed = false;
	const onConsumed = () => {
		if (consumed) return;
		consumed = true;
		const error = consumeInvalidDynamicUsageError();
		if (!error) return;
		if (!hasDigest(error)) console.error("[vinext] Invalid dynamic usage:", error);
	};
	const cleanup = new TransformStream({ flush() {
		onConsumed();
	} });
	const reader = originalBody.pipeThrough(cleanup).getReader();
	const wrappedStream = new ReadableStream({
		pull(controller) {
			return reader.read().then(({ done, value }) => {
				if (done) controller.close();
				else controller.enqueue(value);
			}, (streamError) => {
				onConsumed();
				controller.error(streamError);
			});
		},
		cancel(reason) {
			onConsumed();
			return reader.cancel(reason);
		}
	});
	return new Response(wrappedStream, {
		status: response.status,
		statusText: response.statusText,
		headers: response.headers
	});
}
async function renderAppPageLifecycle(options) {
	let dynamicUsageObserved = false;
	let dynamicUsageFinalized = false;
	const consumeRenderDynamicUsage = () => {
		if (!dynamicUsageObserved) dynamicUsageObserved = options.consumeDynamicUsage();
		return dynamicUsageObserved;
	};
	const finalizeRenderDynamicUsage = () => {
		if (!dynamicUsageFinalized) {
			consumeRenderDynamicUsage();
			dynamicUsageFinalized = true;
		}
		return dynamicUsageObserved;
	};
	const configuredProbePageBeforeRender = options.probePageBeforeRender ?? options.isRscRequest;
	const probePageBeforeRender = options.isRscRequest || configuredProbePageBeforeRender && !(options.peekDynamicUsage?.() ?? false);
	const preRenderResult = await probeAppPageBeforeRender({
		hasLoadingBoundary: options.hasLoadingBoundary,
		probePageBeforeRender,
		skipProbes: options.pprFallbackShellSignal !== void 0,
		layoutCount: options.layoutCount,
		probeLayoutAt(layoutIndex) {
			return options.probeLayoutAt(layoutIndex);
		},
		probePage() {
			return options.probePage();
		},
		renderLayoutSpecialError(specialError, layoutIndex) {
			return options.renderLayoutSpecialError(specialError, layoutIndex);
		},
		renderPageSpecialError(specialError) {
			return options.renderPageSpecialError(specialError);
		},
		resolveSpecialError: resolveAppPageSpecialError,
		runWithSuppressedHookWarning(probe) {
			return options.runWithSuppressedHookWarning(probe);
		},
		classification: options.classification
	});
	if (preRenderResult.response) return preRenderResult.response;
	const layoutFlags = preRenderResult.layoutFlags;
	const artifactCompatibility = createAppPageArtifactCompatibility(options.element, options.routePattern);
	const rootBoundaryId = artifactCompatibility?.rootBoundaryId ?? null;
	const renderEpoch = artifactCompatibility?.renderEpoch ?? null;
	const rscOutputScope = createAppPageRscOutputScope({
		element: options.element,
		mountedSlotsHeader: options.mountedSlotsHeader,
		renderEpoch,
		rootBoundaryId,
		routePattern: options.routePattern
	});
	const htmlOutputScope = createAppPageHtmlOutputScope({
		element: options.element,
		renderEpoch,
		rootBoundaryId,
		routePattern: options.routePattern
	});
	const skipDisposition = options.skipDisposition ?? createRenderLifecycleSkipDisposition({
		artifactCompatibility,
		cleanPathname: options.cleanPathname,
		clientReuseManifest: options.clientReuseManifest,
		element: options.element,
		isRscRequest: options.isRscRequest,
		layoutFlags,
		layoutParamAccess: options.layoutParamAccess
	});
	const shouldBypassRscCacheForSkipTransport = options.isRscRequest && isSkipTransportEnabled(skipDisposition);
	const dynamicStaleTimeSeconds = options.dynamicStaleTimeSeconds ?? resolveConfiguredDynamicStaleTimeSeconds();
	const outgoingElement = AppElementsWire.encodeOutgoingPayload({
		element: options.element,
		layoutFlags,
		...dynamicStaleTimeSeconds !== void 0 && options.isPrerender !== true && !options.isForceStatic ? { dynamicStaleTimeSeconds } : {},
		...artifactCompatibility ? { artifactCompatibility } : {},
		skipDisposition: options.isRscRequest ? skipDisposition : void 0
	});
	const compileEnd = options.isProduction ? void 0 : performance.now();
	const rscErrorTracker = createAppPageRscErrorTracker(options.createRscOnErrorHandler(options.cleanPathname, options.routePattern));
	let rscStream = await runWithFetchDedupe(async () => {
		if (options.pprFallbackShellSignal && options.prerenderToReadableStream) {
			const reactSignal = options.pprFallbackShellReactSignal ?? options.pprFallbackShellSignal;
			const pendingResult = options.prerenderToReadableStream(outgoingElement, {
				onError: rscErrorTracker.onRenderError,
				signal: reactSignal
			});
			if (options.abortPprFallbackShell) setTimeout(options.abortPprFallbackShell, 0);
			return (await pendingResult).prelude;
		}
		return options.renderToReadableStream(outgoingElement, { onError: rscErrorTracker.onRenderError });
	});
	let pprFallbackShellRsc = null;
	if (options.pprFallbackShellSignal) pprFallbackShellRsc = new Uint8Array(await readAppPageBinaryStream(rscStream));
	let revalidateSeconds = options.revalidateSeconds;
	let expireSeconds = options.expireSeconds;
	const shouldWaitForAllReady = options.isPrerender === true && options.isSpeculativePrerender !== true;
	const shouldReadRequestCacheLifeForPrerender = options.isPrerender === true;
	const mayResolveCacheLifeAfterHeaders = options.isProgressiveActionRender !== true && (revalidateSeconds === null || revalidateSeconds > 0 && revalidateSeconds !== Infinity) && !options.isDraftMode && !options.isForceDynamic && !shouldBypassRscCacheForSkipTransport;
	const shouldCaptureRscForCacheMetadata = (options.isProduction || options.isPrerender === true) && mayResolveCacheLifeAfterHeaders;
	const createBufferedRscStream = (close) => new ReadableStream({ start(controller) {
		if (pprFallbackShellRsc) controller.enqueue(pprFallbackShellRsc);
		if (close) controller.close();
	} });
	const rscCapture = pprFallbackShellRsc ? {
		ssrStream: createBufferedRscStream(false),
		...shouldCaptureRscForCacheMetadata ? { sideStream: createBufferedRscStream(true) } : {}
	} : teeAppPageRscStreamForCapture(rscStream, shouldCaptureRscForCacheMetadata);
	const rscForResponse = rscCapture.ssrStream;
	const capturedRscDataRef = { value: null };
	if (rscCapture.sideStream && options.isRscRequest) capturedRscDataRef.value = readAppPageBinaryStream(rscCapture.sideStream);
	if (options.isRscRequest) {
		let requestCacheLifeForPrerender = null;
		if (shouldWaitForAllReady) await settleCapturedRscRenderForCacheMetadata(capturedRscDataRef.value);
		if (shouldReadRequestCacheLifeForPrerender) {
			requestCacheLifeForPrerender = readRequestCacheLifeForPrerender(options);
			({expireSeconds, revalidateSeconds} = applyRequestCacheLife({
				expireSeconds,
				requestCacheLife: requestCacheLifeForPrerender,
				revalidateSeconds
			}));
		}
		const dynamicUsedDuringBuild = consumeRenderDynamicUsage();
		const rscResponsePolicy = shouldBypassRscCacheForSkipTransport ? { cacheControl: NO_STORE_CACHE_CONTROL } : resolveAppPageRscResponsePolicy({
			dynamicUsedDuringBuild,
			isDraftMode: options.isDraftMode,
			isDynamicError: options.isDynamicError,
			isForceDynamic: options.isForceDynamic,
			isForceStatic: options.isForceStatic,
			isProduction: options.isProduction,
			expireSeconds,
			revalidateSeconds
		});
		if (shouldBypassRscCacheForSkipTransport) options.isrDebug?.("RSC cache write skipped (skip transport payload)", options.cleanPathname);
		const shouldEmitDynamicStaleTime = dynamicStaleTimeSeconds !== void 0 && options.isPrerender !== true && !options.isForceStatic && (dynamicUsedDuringBuild || options.isForceDynamic);
		const staleTimePending = options.isPrerender !== true && mayResolveCacheLifeAfterHeaders && !dynamicUsedDuringBuild;
		const rscResponse = buildAppPageRscResponse(rscForResponse, {
			cacheTags: options.isPrerender === true ? options.getPageTags() : void 0,
			staleTimePending,
			dynamicStaleTimeSeconds: shouldEmitDynamicStaleTime ? dynamicStaleTimeSeconds : void 0,
			isEdgeRuntime: options.isEdgeRuntime,
			middlewareContext: options.middlewareContext,
			mountedSlotsHeader: options.mountedSlotsHeader,
			params: options.navigationParams,
			policy: rscResponsePolicy,
			renderedPathAndSearch: options.renderedPathAndSearch,
			requestCacheLife: requestCacheLifeForPrerender,
			timing: buildResponseTiming({
				compileEnd,
				handlerStart: options.handlerStart,
				isProduction: options.isProduction,
				responseKind: "rsc"
			})
		});
		const completionHeaders = new Headers(rscResponse.headers);
		completionHeaders.set(VINEXT_RSC_COMPLETION_METADATA_HEADER, "1");
		const completionResponse = dynamicStaleTimeSeconds !== void 0 && options.isPrerender !== true && !options.isForceStatic && rscResponse.body ? new Response(appendRscCompletionMetadata(rscResponse.body, () => {
			if (!finalizeRenderDynamicUsage()) return void 0;
			const completedServerStaleTimeSeconds = resolveClientStaleTimeSeconds(options.peekRequestCacheLife?.());
			if (shouldEmitDynamicStaleTime && completedServerStaleTimeSeconds === void 0) return;
			return {
				dynamicStaleTimeSeconds,
				serverStaleTimeSeconds: completedServerStaleTimeSeconds === void 0 ? null : Math.floor(completedServerStaleTimeSeconds)
			};
		}), {
			status: rscResponse.status,
			statusText: rscResponse.statusText,
			headers: completionHeaders
		}) : rscResponse;
		return finalizeAppPageRscCacheResponse(!options.isProduction && completionResponse.body && options.consumeInvalidDynamicUsageError ? wrapRscResponseForDevErrorReporting(completionResponse, options.consumeInvalidDynamicUsageError) : completionResponse, {
			capturedRscDataPromise: options.isProduction && shouldCaptureRscForCacheMetadata ? capturedRscDataRef.value : null,
			cleanPathname: options.cleanPathname,
			consumeDynamicUsage: finalizeRenderDynamicUsage,
			consumeRenderObservationState: options.consumeRenderObservationState,
			createRscRenderObservation(input) {
				return createAppPageRenderObservation({
					boundaryOutcome: { kind: "success" },
					cacheability: "public",
					cacheTags: input.cacheTags,
					cleanPathname: options.cleanPathname,
					completeness: "complete",
					output: rscOutputScope,
					params: options.navigationParams,
					state: input.state
				});
			},
			dynamicUsedDuringBuild,
			getPageTags() {
				return options.getPageTags();
			},
			getRequestCacheLife() {
				return readRequestCacheLifeForCachePolicy(options);
			},
			isrDebug: options.isrDebug,
			isrRscKey: options.isrRscKey,
			isrSet: options.isrSet,
			interceptionContext: options.interceptionContext,
			mountedSlotsHeader: options.mountedSlotsHeader,
			omitPendingDynamicCacheState: options.omitPendingDynamicCacheState,
			renderMode: options.renderMode,
			preserveClientResponseHeaders: rscResponsePolicy.cacheState !== "MISS",
			expireSeconds,
			revalidateSeconds: resolveAppPageCacheWriteRevalidateSeconds({
				isDynamicError: options.isDynamicError,
				isForceStatic: options.isForceStatic,
				revalidateSeconds
			}),
			waitUntil(promise) {
				options.waitUntil?.(promise);
			}
		});
	}
	const fontData = createAppPageFontData({
		getLinks: options.getFontLinks,
		getPreloads: options.getFontPreloads,
		getStyles: options.getFontStyles
	});
	const fontLinkHeader = buildAppPageFontLinkHeader(fontData.preloads);
	let requestCacheLifeForPrerender = null;
	let dynamicUsedDuringHtmlRender = false;
	let renderEnd;
	const htmlRender = await renderAppPageHtmlStreamWithRecovery({
		onShellRendered() {
			if (!options.isProduction) renderEnd = performance.now();
		},
		renderErrorBoundaryResponse(error) {
			const capturedRscError = rscErrorTracker.getCapturedError();
			return options.renderErrorBoundaryResponse(capturedRscError ?? error, capturedRscError === null ? "ssr" : "rsc");
		},
		async renderHtmlStream() {
			const ssrHandler = await options.loadSsrHandler();
			return renderAppPageHtmlStream({
				capturedRscDataRef,
				getInitialNavigationCacheMetadata: () => {
					let kind;
					if (options.isForceStatic) kind = "static";
					else if (options.isForceDynamic || dynamicUsedDuringHtmlRender || peekDynamicUsage()) kind = "dynamic";
					else {
						const observation = options.peekRenderObservationState?.();
						kind = observation && (observation.dynamicFetches.length > 0 || observation.requestApis.length > 0) ? "dynamic" : "static";
					}
					const staleTimeSeconds = resolveClientStaleTimeSeconds(options.isPrerender === true ? requestCacheLifeForPrerender : options.peekRequestCacheLife?.());
					return {
						kind,
						...kind === "dynamic" && dynamicStaleTimeSeconds !== void 0 && options.isPrerender !== true ? { dynamicStaleTimeSeconds } : {},
						...staleTimeSeconds === void 0 ? {} : { staleTimeSeconds: Math.floor(staleTimeSeconds) }
					};
				},
				fontData,
				hasCustomGlobalError: options.hasCustomGlobalError,
				navigationContext: options.getNavigationContext(),
				basePath: options.basePath,
				clientTraceMetadata: options.clientTraceMetadata,
				reactMaxHeadersLength: options.reactMaxHeadersLength,
				rootParams: options.rootParams,
				pprFallbackShellSignal: options.pprFallbackShellSignal,
				formState: options.formState ?? null,
				rscStream: rscForResponse,
				scriptNonce: options.scriptNonce,
				sideStream: rscCapture.sideStream,
				ssrHandler,
				fallbackToErrorDocumentOnShellError: options.isPrerender === true && options.isSpeculativePrerender === true ? false : void 0,
				waitForAllReady: shouldWaitForAllReady
			});
		},
		renderSpecialErrorResponse(specialError) {
			return options.renderPageSpecialError(specialError);
		},
		resolveSpecialError: resolveAppPageSpecialError
	});
	if (htmlRender.response) return htmlRender.response;
	let htmlStream = htmlRender.htmlStream;
	if (!htmlStream) throw new Error("[vinext] Expected an HTML stream when no fallback response was returned");
	const linkHeader = buildAppPageLinkHeader(htmlRender.linkHeader, fontLinkHeader, options.reactMaxHeadersLength);
	if (options.isPrerender === true) await htmlRender.metadataReady;
	if (options.hasLoadingBoundary || !probePageBeforeRender) {
		const captured = rscErrorTracker.getCapturedSpecialError();
		if (captured) {
			const specialError = resolveAppPageSpecialError(captured);
			if (specialError) {
				htmlStream.cancel().catch(() => {});
				return options.renderPageSpecialError(specialError);
			}
		}
	}
	let dynamicUsedDuringRender = consumeRenderDynamicUsage();
	dynamicUsedDuringHtmlRender = dynamicUsedDuringRender;
	const stopSpeculativeMetadataWaitOnDynamicUsage = options.isSpeculativePrerender === true && shouldReadRequestCacheLifeForPrerender ? () => {
		if (dynamicUsedDuringRender || (options.peekDynamicUsage?.() ?? peekDynamicUsage())) {
			dynamicUsedDuringRender = true;
			dynamicUsedDuringHtmlRender = true;
			return true;
		}
		return false;
	} : void 0;
	if (shouldWaitForAllReady || shouldReadRequestCacheLifeForPrerender) await settleCapturedRscRenderForCacheMetadata(htmlRender.capturedRscData, stopSpeculativeMetadataWaitOnDynamicUsage);
	if (shouldReadRequestCacheLifeForPrerender) {
		requestCacheLifeForPrerender = readRequestCacheLifeForPrerender(options);
		({expireSeconds, revalidateSeconds} = applyRequestCacheLife({
			expireSeconds,
			requestCacheLife: requestCacheLifeForPrerender,
			revalidateSeconds
		}));
	}
	dynamicUsedDuringRender = dynamicUsedDuringRender || consumeRenderDynamicUsage();
	dynamicUsedDuringHtmlRender = dynamicUsedDuringRender;
	const draftCookie = options.getDraftModeCookieHeader();
	let dynamicUsedBeforeContextCleanup = dynamicUsedDuringRender;
	const safeHtmlStream = deferUntilStreamConsumed(htmlStream, () => {
		dynamicUsedBeforeContextCleanup = dynamicUsedBeforeContextCleanup || consumeRenderDynamicUsage();
		dynamicUsedDuringHtmlRender = dynamicUsedBeforeContextCleanup;
		options.clearRequestContext();
	});
	const htmlResponsePolicy = resolveAppPageHtmlResponsePolicy({
		dynamicUsedDuringRender,
		isProgressiveActionRender: options.isProgressiveActionRender === true,
		hasScriptNonce: Boolean(options.scriptNonce),
		isDraftMode: options.isDraftMode,
		isDynamicError: options.isDynamicError,
		isForceDynamic: options.isForceDynamic,
		isForceStatic: options.isForceStatic,
		isProduction: options.isProduction,
		expireSeconds,
		revalidateSeconds
	});
	const htmlResponseTiming = buildResponseTiming({
		compileEnd,
		handlerStart: options.handlerStart,
		isProduction: options.isProduction,
		renderEnd,
		responseKind: "html"
	});
	if (htmlRender.shellErrorRecovered) {
		const response = buildAppPageHtmlResponse(safeHtmlStream, {
			cacheTags: options.isPrerender === true ? options.getPageTags() : void 0,
			draftCookie,
			linkHeader,
			isEdgeRuntime: options.isEdgeRuntime,
			middlewareContext: {
				headers: options.middlewareContext.headers,
				status: 500
			},
			policy: { cacheControl: NEVER_CACHE_CONTROL },
			requestCacheLife: requestCacheLifeForPrerender,
			timing: htmlResponseTiming
		});
		applyCdnResponseHeaders(response.headers, { cacheControl: NEVER_CACHE_CONTROL });
		return response;
	}
	const shouldSpeculativelyWriteCache = options.isProduction && shouldCaptureRscForCacheMetadata && !options.isEdgeRuntime && revalidateSeconds === null && !options.isDynamicError && !options.isForceStatic && !options.scriptNonce && options.isProgressiveActionRender !== true && !dynamicUsedDuringRender;
	if (htmlResponsePolicy.shouldWriteToCache || shouldSpeculativelyWriteCache) {
		const isrResponse = buildAppPageHtmlResponse(safeHtmlStream, {
			cacheTags: options.isPrerender === true ? options.getPageTags() : void 0,
			draftCookie,
			linkHeader,
			isEdgeRuntime: options.isEdgeRuntime,
			middlewareContext: options.middlewareContext,
			policy: htmlResponsePolicy,
			requestCacheLife: requestCacheLifeForPrerender,
			timing: htmlResponseTiming
		});
		if (options.isPrerender === true) return isrResponse;
		return finalizeAppPageHtmlCacheResponse(isrResponse, {
			capturedDynamicUsageBeforeContextCleanup() {
				return dynamicUsedBeforeContextCleanup;
			},
			capturedRscDataPromise: capturedRscDataRef.value,
			cleanPathname: options.cleanPathname,
			consumeDynamicUsage: consumeRenderDynamicUsage,
			consumeRenderObservationState: options.consumeRenderObservationState,
			createHtmlRenderObservation(input) {
				return createAppPageRenderObservation({
					boundaryOutcome: { kind: "success" },
					cacheability: "public",
					cacheTags: input.cacheTags,
					cleanPathname: options.cleanPathname,
					completeness: "complete",
					output: htmlOutputScope,
					params: options.navigationParams,
					state: input.state
				});
			},
			createRscRenderObservation(input) {
				return createAppPageRenderObservation({
					boundaryOutcome: { kind: "success" },
					cacheability: "public",
					cacheTags: input.cacheTags,
					cleanPathname: options.cleanPathname,
					completeness: "complete",
					output: rscOutputScope,
					params: options.navigationParams,
					state: input.state
				});
			},
			getPageTags() {
				return options.getPageTags();
			},
			getRequestCacheLife() {
				return readRequestCacheLifeForCachePolicy(options);
			},
			isrDebug: options.isrDebug,
			isrHtmlKey: options.isrHtmlKey,
			isrRscKey: options.isrRscKey,
			isrSet: options.isrSet,
			interceptionContext: options.interceptionContext,
			omitPendingDynamicCacheState: options.omitPendingDynamicCacheState,
			preserveClientResponseHeaders: !htmlResponsePolicy.shouldWriteToCache,
			expireSeconds,
			revalidateSeconds: resolveAppPageCacheWriteRevalidateSeconds({
				isDynamicError: options.isDynamicError,
				isForceStatic: options.isForceStatic,
				revalidateSeconds
			}),
			waitUntil(cachePromise) {
				options.waitUntil?.(cachePromise);
			}
		});
	}
	return buildAppPageHtmlResponse(safeHtmlStream, {
		cacheTags: options.isPrerender === true ? options.getPageTags() : void 0,
		draftCookie,
		linkHeader,
		isEdgeRuntime: options.isEdgeRuntime,
		middlewareContext: options.middlewareContext,
		policy: htmlResponsePolicy,
		requestCacheLife: requestCacheLifeForPrerender,
		timing: htmlResponseTiming
	});
}
async function settleCapturedRscRenderForCacheMetadata(capturedRscDataPromise, shouldStopWaiting) {
	if (!capturedRscDataPromise) return;
	if (!shouldStopWaiting) {
		try {
			await capturedRscDataPromise;
		} catch {}
		return;
	}
	let settled = false;
	const settledPromise = capturedRscDataPromise.catch(() => {}).then(() => {
		settled = true;
	});
	try {
		while (!settled && !shouldStopWaiting()) await Promise.race([settledPromise, new Promise((resolve) => setTimeout(resolve, 0))]);
	} finally {}
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-dispatch.js
function getActiveLoadingTreePositions(route) {
	const positions = [];
	for (const [index, loadingModule] of (route.loadings ?? []).entries()) {
		if (!loadingModule?.default) continue;
		const treePosition = route.loadingTreePositions?.[index];
		if (treePosition !== void 0) positions.push(treePosition);
	}
	if (positions.length === 0 && route.loading?.default) positions.push(route.routeSegments.length);
	return positions;
}
function getAppPageLayoutProbeCount(route, loadingTreePositions) {
	const firstLoadingTreePosition = loadingTreePositions.reduce((first, position) => first === null || position < first ? position : first, null);
	if (firstLoadingTreePosition === null) return route.layouts.length;
	const firstSuspendedLayoutIndex = (route.layoutTreePositions ?? []).findIndex((position) => position > firstLoadingTreePosition);
	return firstSuspendedLayoutIndex === -1 ? route.layouts.length : firstSuspendedLayoutIndex;
}
function resolveAppPageRouteBoundaryModule(route, statusCode) {
	if (statusCode === 403) return route.forbidden ?? null;
	if (statusCode === 401) return route.unauthorized ?? null;
	if (statusCode === 404) return route.notFound ?? null;
	return null;
}
/**
* Request-time counterpart to the build-time `classifyLayoutSegmentConfig`
* (`build/report.ts`). Both classify a layout by its `dynamic`/`revalidate`
* segment config and agree on the shared cases (the build-time version
* normalizes `revalidate = false` to `Infinity` upstream, so both treat it as
* static); keep them aligned when either changes.
*
* The meaningful difference is scope, not logic: this request-time pass reads
* the resolved module value, so it classifies layouts that were never captured
* at build time (e.g. dev mode). Its result is merged on top of the build-time
* classification map in `createEffectiveLayoutClassifications`, so such layouts
* are classified here where they previously were not.
*/
function classifyLayoutSegmentConfigFromModule(layout) {
	if (!layout) return null;
	switch (layout.dynamic) {
		case "force-dynamic": return {
			kind: "dynamic",
			reason: {
				layer: "segment-config",
				key: "dynamic",
				value: "force-dynamic"
			}
		};
		case "force-static":
		case "error": return {
			kind: "static",
			reason: {
				layer: "segment-config",
				key: "dynamic",
				value: layout.dynamic
			}
		};
	}
	if (layout.revalidate === false || layout.revalidate === Infinity) return {
		kind: "static",
		reason: {
			layer: "segment-config",
			key: "revalidate",
			value: Infinity
		}
	};
	if (layout.revalidate === 0) return {
		kind: "dynamic",
		reason: {
			layer: "segment-config",
			key: "revalidate",
			value: 0
		}
	};
	return null;
}
function createEffectiveLayoutClassifications(route, includeReasons) {
	const classifications = new Map(route.__buildTimeClassifications ?? []);
	const reasons = includeReasons ? new Map(route.__buildTimeReasons ?? []) : null;
	for (let index = 0; index < route.layouts.length; index++) {
		const classification = classifyLayoutSegmentConfigFromModule(route.layouts[index]);
		if (classification === null) continue;
		classifications.set(index, classification.kind);
		reasons?.set(index, classification.reason);
	}
	return {
		buildTimeClassifications: classifications.size > 0 ? classifications : null,
		buildTimeReasons: reasons && reasons.size > 0 ? reasons : null
	};
}
function getEffectiveLayoutClassifications(route, debugClassification) {
	return createEffectiveLayoutClassifications(route, debugClassification !== void 0);
}
function shouldReadAppPageCache(options) {
	return options.isProduction && !options.isProgressiveActionRender && !options.isDraftMode && !options.isForceDynamic && (options.isRscRequest || !options.scriptNonce) && (options.revalidateSeconds === null || options.revalidateSeconds > 0);
}
function resolveAppPageCacheReadRevalidateSeconds(options) {
	if (options.revalidateSeconds === null && (options.isForceStatic || options.isDynamicError)) return Infinity;
	return options.revalidateSeconds ?? 0;
}
function hasSearchParams(searchParams) {
	return searchParams !== null && searchParams !== void 0 && searchParams.size > 0;
}
async function runAppPageRevalidationContext(options, renderFn) {
	const { createStaticGenerationHeadersContext } = await import("./_next/static/app-static-generation-B6y5rJ3f.js");
	const requestContext = createRequestContext({
		headersContext: createStaticGenerationHeadersContext({
			draftModeEnabled: false,
			draftModeSecret: options.draftModeSecret,
			dynamicConfig: options.dynamicConfig,
			routeKind: "page",
			routePattern: options.routePattern
		}),
		currentFetchCacheMode: options.currentFetchCacheMode ?? null,
		currentForceDynamicFetchDefault: options.dynamicConfig === "force-dynamic",
		executionContext: getRequestExecutionContext(),
		unstableCacheRevalidation: "foreground"
	});
	const revalidation = runWithRequestContext(requestContext, async () => {
		ensureFetchPatch();
		setRefreshStaleFetchesInForeground(process.env.VINEXT_PRERENDER === "1");
		setCurrentFetchSoftTags(buildAppPageTags(options.cleanPathname, [], options.routeSegments));
		options.setNavigationContext({
			pathname: options.displayPathname ?? options.cleanPathname,
			searchParams: new URLSearchParams(),
			params: options.params
		});
		return await runWithFetchDedupe(renderFn);
	});
	try {
		return await revalidation;
	} finally {
		await closeAfterResponse(requestContext);
	}
}
function toInterceptOptions(interceptionContext, intercept) {
	return {
		interceptGraphId: intercept.interceptionGraphId ?? null,
		interceptionContext,
		interceptLayouts: intercept.interceptLayouts,
		interceptLayoutSegments: intercept.interceptLayoutSegments,
		interceptBranchSegments: intercept.interceptBranchSegments,
		interceptLoadings: intercept.interceptLoadings,
		interceptLoadingTreePositions: intercept.interceptLoadingTreePositions,
		interceptNotFoundBranchSegments: intercept.interceptNotFoundBranchSegments,
		interceptNotFound: intercept.notFound,
		interceptNotFoundTreePosition: intercept.notFoundTreePosition,
		interceptPage: intercept.page,
		interceptParams: intercept.matchedParams,
		interceptSlotId: intercept.slotId ?? null,
		interceptSlotKey: intercept.slotKey,
		interceptSourceMatchedUrl: interceptionContext,
		interceptSourcePageSegments: intercept.sourcePageSegments ?? null,
		interceptTargetPatternParts: intercept.targetPatternParts ?? null,
		interceptTargetRouteGraphId: intercept.targetRouteGraphId ?? null
	};
}
async function dispatchAppPage(options) {
	const dispatch = () => runWithFetchDedupe(() => dispatchAppPageInner(options));
	if (!options.pprFallbackShell || !options.pprRuntime) return await dispatch();
	return await options.pprRuntime.run(options.pprFallbackShell, dispatch);
}
async function dispatchAppPageInner(options) {
	const route = options.route;
	const dynamicConfig = options.dynamicConfig;
	const currentRevalidateSeconds = options.revalidateSeconds;
	const isForceStatic = dynamicConfig === "force-static";
	const isDynamicError = dynamicConfig === "error";
	const isForceDynamic = dynamicConfig === "force-dynamic";
	const isPrerender = process.env.VINEXT_PRERENDER === "1";
	const serveStreamingMetadata = shouldServeStreamingMetadata(options.request.headers.get("user-agent") ?? "", options.htmlLimitedBots);
	const placeGeneratedMetadataInBody = (!isPrerender || options.pprFallbackShell !== void 0) && serveStreamingMetadata;
	const isPrefetchDynamicShell = options.renderMode === APP_RSC_RENDER_MODE_PREFETCH_DYNAMIC_SHELL;
	const isDraftMode = isDraftModeRequest(options.request, options.draftModeSecret);
	const requestHeadersContext = getHeadersContext();
	const shouldUseEmptySearchParams = isForceStatic || isPrefetchDynamicShell;
	const hasRequestSearchParams = !shouldUseEmptySearchParams && hasSearchParams(options.searchParams);
	const pageSearchParams = shouldUseEmptySearchParams ? new URLSearchParams() : options.searchParams;
	const layoutParamAccess = createAppLayoutParamAccessTracker();
	const activeLoadingTreePositions = getActiveLoadingTreePositions(route);
	const hasActiveLoadingBoundary = activeLoadingTreePositions.length > 0;
	setCurrentFetchSoftTags(buildAppPageTags(options.cleanPathname, [], route.routeSegments));
	setCurrentFetchCacheMode(options.fetchCache ?? null);
	setCurrentForceDynamicFetchDefault(isForceDynamic);
	if (options.hasPageModule && !options.hasPageDefaultExport) {
		options.clearRequestContext();
		return new Response("Page has no default export", { status: 500 });
	}
	const methodResponse = resolveAppPageMethodResponse({
		dynamicConfig,
		hasGenerateStaticParams: options.hasGenerateStaticParams,
		isDynamicRoute: route.isDynamic,
		middlewareHeaders: options.middlewareContext.headers,
		request: options.request,
		revalidateSeconds: currentRevalidateSeconds
	});
	if (methodResponse) {
		options.clearRequestContext();
		return methodResponse;
	}
	if (isForceStatic || isDynamicError) {
		const { createStaticGenerationHeadersContext } = await import("./_next/static/app-static-generation-B6y5rJ3f.js");
		setHeadersContext(createStaticGenerationHeadersContext({
			draftModeEnabled: isDraftMode,
			draftModeSecret: options.draftModeSecret,
			dynamicConfig,
			routeKind: "page",
			routePattern: route.pattern
		}));
		const staticNavigationParams = resolveAppPageNavigationParams(route, options.params, options.cleanPathname, null);
		options.setNavigationContext({
			pathname: options.displayPathname ?? options.cleanPathname,
			searchParams: new URLSearchParams(),
			params: staticNavigationParams
		});
	}
	if (shouldReadAppPageCache({
		isDraftMode,
		isForceDynamic,
		isProgressiveActionRender: options.isProgressiveActionRender === true,
		isProduction: options.isProduction,
		isRscRequest: options.isRscRequest,
		revalidateSeconds: currentRevalidateSeconds,
		scriptNonce: options.scriptNonce
	})) {
		const { readAppPageCacheResponse } = await import("./_next/static/app-page-cache-BZmChaPj.js");
		const cachedPageResponse = await readAppPageCacheResponse({
			cleanPathname: options.cleanPathname,
			clearRequestContext: options.clearRequestContext,
			hasRequestSearchParams,
			isEdgeRuntime: options.isEdgeRuntime,
			isRscRequest: options.isRscRequest,
			isrDebug: options.isrDebug,
			isrGet: options.isrGet,
			isrHtmlKey: options.isrHtmlKey,
			isrRscKey: options.isrRscKey,
			isrSet: options.isrSet,
			interceptionContext: options.interceptionContext,
			middlewareHeaders: options.middlewareContext.headers,
			middlewareStatus: options.middlewareContext.status,
			mountedSlotsHeader: options.mountedSlotsHeader,
			renderMode: options.renderMode,
			expireSeconds: options.expireSeconds,
			revalidateSeconds: resolveAppPageCacheReadRevalidateSeconds({
				isDynamicError,
				isForceStatic,
				revalidateSeconds: currentRevalidateSeconds
			}),
			renderFreshPageForCache: async () => {
				const revalidationTarget = await resolveAppPageInterceptionRerenderTarget({
					cleanPathname: options.cleanPathname,
					currentParams: options.params,
					currentRoute: route,
					findIntercept: options.findIntercept,
					getRouteParamNames(sourceRoute) {
						return sourceRoute.params;
					},
					getSourceRoute(sourceRouteIndex) {
						return options.getSourceRoute(sourceRouteIndex);
					},
					isRscRequest: options.isRscRequest,
					toInterceptOpts(intercept) {
						return toInterceptOptions(options.interceptionContext, intercept);
					}
				});
				revalidationTarget.navigationParams = resolveAppPageNavigationParams(revalidationTarget.route, revalidationTarget.navigationParams, options.cleanPathname, revalidationTarget.interceptOpts);
				await options.ensureRouteLoaded?.(revalidationTarget.route);
				const revalidationDynamicConfig = options.resolveRouteDynamicConfig?.(revalidationTarget.route) ?? (revalidationTarget.route === route ? dynamicConfig : void 0);
				return runAppPageRevalidationContext({
					cleanPathname: options.cleanPathname,
					displayPathname: options.displayPathname,
					currentFetchCacheMode: options.resolveRouteFetchCacheMode?.(revalidationTarget.route) ?? (revalidationTarget.route === route ? options.fetchCache ?? null : null),
					draftModeSecret: options.draftModeSecret,
					dynamicConfig: revalidationDynamicConfig,
					params: revalidationTarget.navigationParams,
					routePattern: revalidationTarget.route.pattern,
					routeSegments: revalidationTarget.route.routeSegments,
					setNavigationContext: options.setNavigationContext
				}, async () => {
					const { renderAppPageCacheArtifacts } = await import("./_next/static/app-page-cache-render-CHSUQZnS.js");
					const revalidatedElement = await options.buildPageElement(revalidationTarget.route, revalidationTarget.params, revalidationTarget.interceptOpts, new URLSearchParams(), void 0, {
						observeMetadataSearchParamsAccess: revalidationDynamicConfig !== "force-static",
						observePageSearchParamsAccess: revalidationDynamicConfig !== "force-static",
						serveStreamingMetadata: false
					});
					const revalidatedOnError = options.createRscOnErrorHandler(options.cleanPathname, revalidationTarget.route.pattern);
					const rendered = await renderAppPageCacheArtifacts({
						basePath: options.basePath,
						captureRscData: true,
						cleanPathname: options.cleanPathname,
						clientTraceMetadata: options.clientTraceMetadata,
						element: revalidatedElement,
						getFontLinks: options.getFontLinks,
						getFontPreloads: options.getFontPreloads,
						getFontStyles: options.getFontStyles,
						getNavigationContext: options.getNavigationContext,
						loadSsrHandler: options.loadSsrHandler,
						mountedSlotsHeader: options.mountedSlotsHeader,
						navigationParams: revalidationTarget.navigationParams,
						onError: revalidatedOnError,
						reactMaxHeadersLength: options.reactMaxHeadersLength,
						renderToReadableStream: options.renderToReadableStream,
						rootParams: options.rootParams,
						route: revalidationTarget.route,
						waitForAllReady: true
					});
					options.clearRequestContext();
					return {
						html: rendered.html,
						htmlRenderObservation: rendered.htmlRenderObservation,
						linkHeader: rendered.linkHeader,
						rscData: rendered.rscData,
						rscRenderObservation: rendered.rscRenderObservation,
						tags: rendered.tags,
						cacheControl: rendered.cacheControl
					};
				});
			},
			scheduleBackgroundRegeneration(key, renderFn) {
				options.scheduleBackgroundRegeneration(key, renderFn, {
					routerKind: "App Router",
					routePath: route.pattern,
					routeType: "render"
				});
			}
		});
		if (cachedPageResponse) return cachedPageResponse;
	}
	if (options.skipStaticParamsValidation !== true && !(options.isProduction && isForceDynamic)) {
		const dynamicParamsResponse = await validateAppPageDynamicParams({
			enforceStaticParamsOnly: options.dynamicParamsConfig === false,
			generateStaticParams: options.generateStaticParams,
			isDynamicRoute: route.isDynamic,
			params: options.staticParamsValidationParams ?? options.params
		});
		if (dynamicParamsResponse) {
			const renderedNotFound = await options.renderHttpAccessFallbackPage(404, { matchedParams: options.params }, options.middlewareContext);
			if (renderedNotFound) return renderedNotFound;
			options.clearRequestContext();
			return dynamicParamsResponse;
		}
	}
	const fallbackShellResponse = options.pprRuntime ? await options.pprRuntime.tryServe(options, currentRevalidateSeconds, isDraftMode, isForceStatic, isForceDynamic) : null;
	if (fallbackShellResponse) return fallbackShellResponse;
	let interceptDynamicConfig;
	let interceptDynamicConfigResolved = false;
	const interceptResult = await resolveAppPageIntercept({
		async buildPageElement(interceptRoute, interceptParams, interceptOpts, interceptSearchParams, interceptLayoutParamAccess) {
			const sourceDynamicConfig = interceptDynamicConfigResolved ? interceptDynamicConfig : options.resolveRouteDynamicConfig?.(interceptRoute);
			if (sourceDynamicConfig === "force-static" || sourceDynamicConfig === "error") {
				const { createStaticGenerationHeadersContext } = await import("./_next/static/app-static-generation-B6y5rJ3f.js");
				setHeadersContext(createStaticGenerationHeadersContext({
					draftModeEnabled: isDraftMode,
					draftModeSecret: options.draftModeSecret,
					dynamicConfig: sourceDynamicConfig,
					routeKind: "page",
					routePattern: interceptRoute.pattern
				}));
			} else setHeadersContext(requestHeadersContext);
			setCurrentFetchCacheMode(options.resolveRouteFetchCacheMode?.(interceptRoute) ?? null);
			setCurrentForceDynamicFetchDefault(sourceDynamicConfig === "force-dynamic");
			return options.buildPageElement(interceptRoute, interceptParams, interceptOpts, interceptSearchParams, interceptLayoutParamAccess, {
				observeMetadataSearchParamsAccess: sourceDynamicConfig !== "force-static",
				observePageSearchParamsAccess: sourceDynamicConfig !== "force-static",
				serveStreamingMetadata: placeGeneratedMetadataInBody
			});
		},
		cleanPathname: options.cleanPathname,
		currentRoute: route,
		findIntercept(pathname) {
			return options.findIntercept(pathname);
		},
		getRouteParamNames(sourceRoute) {
			return sourceRoute.params;
		},
		getSourceRoute(sourceRouteIndex) {
			return options.getSourceRoute(sourceRouteIndex);
		},
		isRscRequest: options.isRscRequest,
		layoutParamAccess,
		resolveNavigationParams(sourceRoute, navigationParams, pathname, interceptOpts) {
			return resolveAppPageNavigationParams(sourceRoute, navigationParams, pathname, interceptOpts);
		},
		renderInterceptResponse(sourceRoute, interceptElement) {
			const interceptOnError = options.createRscOnErrorHandler(options.cleanPathname, sourceRoute.pattern);
			const interceptStream = options.renderToReadableStream(interceptElement, { onError: interceptOnError });
			const interceptHeaders = new Headers({
				"Content-Type": VINEXT_RSC_CONTENT_TYPE,
				Vary: VINEXT_RSC_VARY_HEADER
			});
			mergeMiddlewareResponseHeaders(interceptHeaders, options.middlewareContext.headers);
			applyRscCompatibilityIdHeader(interceptHeaders);
			applyRscDeploymentIdHeader(interceptHeaders);
			return new Response(interceptStream, {
				status: options.middlewareContext.status ?? 200,
				headers: interceptHeaders
			});
		},
		async resolveSearchParams(sourceRoute, searchParams) {
			await options.ensureRouteLoaded?.(sourceRoute);
			interceptDynamicConfig = options.resolveRouteDynamicConfig?.(sourceRoute);
			interceptDynamicConfigResolved = true;
			return interceptDynamicConfig === "force-static" ? new URLSearchParams() : searchParams;
		},
		searchParams: options.searchParams,
		setNavigationContext: options.setNavigationContext,
		toInterceptOpts(intercept) {
			return toInterceptOptions(options.interceptionContext, intercept);
		}
	});
	if (interceptResult.response) return interceptResult.response;
	const buildCurrentPageElement = () => buildAppPageElement({
		buildPageElement() {
			if (options.actionFailed) throw options.actionError;
			return options.buildPageElement(route, options.params, interceptResult.interceptOpts, pageSearchParams, layoutParamAccess, {
				observeMetadataSearchParamsAccess: !isForceStatic,
				observePageSearchParamsAccess: !isForceStatic,
				serveStreamingMetadata: placeGeneratedMetadataInBody
			});
		},
		async probePageSpecialError() {
			if (hasActiveLoadingBoundary) return null;
			return resolveAppPageSpecialError(await probeAppPageThrownError({
				probePage: () => options.probePage(pageSearchParams),
				runWithSuppressedHookWarning(probe) {
					return options.runWithSuppressedHookWarning(probe);
				}
			}));
		},
		renderErrorBoundaryPage(buildError) {
			return options.renderErrorBoundaryPage(buildError);
		},
		renderSpecialError(specialError) {
			return renderPageSpecialError(options, specialError, serveStreamingMetadata, interceptResult.interceptOpts);
		},
		resolveSpecialError: resolveAppPageSpecialError
	});
	const fallbackShellState = options.pprRuntime?.getState() ?? null;
	if (fallbackShellState && process.env.VINEXT_PRERENDER === "1" && !options.isRscRequest) {
		const warmupBuildResult = await buildCurrentPageElement();
		if (warmupBuildResult.response) return warmupBuildResult.response;
		await options.pprRuntime.warm({
			element: warmupBuildResult.element,
			onError: options.createRscOnErrorHandler(options.cleanPathname, route.pattern),
			renderToReadableStream: options.renderToReadableStream,
			state: fallbackShellState
		});
		discardAppPageRenderState();
	}
	const pageBuildResult = await buildCurrentPageElement();
	if (pageBuildResult.response) return pageBuildResult.response;
	const navigationParams = resolveAppPageNavigationParams(route, options.params, options.cleanPathname, interceptResult.interceptOpts);
	options.setNavigationContext({
		pathname: options.displayPathname ?? options.cleanPathname,
		searchParams: pageSearchParams,
		params: navigationParams
	});
	const layoutClassifications = getEffectiveLayoutClassifications(route, options.debugClassification);
	const activeFallbackShellState = options.pprRuntime?.getState() ?? null;
	const pprFallbackShellSignal = activeFallbackShellState?.abortController.signal;
	const pprFallbackShellReactSignal = activeFallbackShellState?.reactAbortController.signal;
	const isSpeculativePrerender = isPrerender && options.request.headers.get("x-vinext-prerender-speculative") === "1";
	const requestCacheLife = _captureRequestScopedCacheLifeAccessors();
	return renderAppPageLifecycle({
		basePath: options.basePath,
		clientTraceMetadata: options.clientTraceMetadata,
		reactMaxHeadersLength: options.reactMaxHeadersLength,
		cleanPathname: options.cleanPathname,
		clearRequestContext: options.clearRequestContext,
		consumeDynamicUsage,
		peekDynamicUsage,
		consumeInvalidDynamicUsageError,
		consumeRenderObservationState: consumeAppPageRenderObservationState,
		createRscOnErrorHandler(pathname, routePath) {
			return options.createRscOnErrorHandler(pathname, routePath);
		},
		element: pageBuildResult.element,
		clientReuseManifest: options.clientReuseManifest,
		getDraftModeCookieHeader,
		getFontLinks: options.getFontLinks,
		getFontPreloads: options.getFontPreloads,
		getFontStyles: options.getFontStyles,
		getNavigationContext: options.getNavigationContext,
		getPageTags() {
			return buildAppPageTags(options.cleanPathname, getCollectedFetchTags(), route.routeSegments);
		},
		getRequestCacheLife() {
			return requestCacheLife.consume();
		},
		peekRequestCacheLife() {
			return requestCacheLife.peek();
		},
		handlerStart: options.handlerStart,
		hasLoadingBoundary: hasActiveLoadingBoundary,
		omitPendingDynamicCacheState: hasRequestSearchParams,
		formState: options.formState ?? null,
		isProgressiveActionRender: options.isProgressiveActionRender === true,
		isDynamicError,
		isDraftMode,
		isForceDynamic,
		isForceStatic,
		isEdgeRuntime: options.isEdgeRuntime === true,
		isPrerender,
		isSpeculativePrerender,
		isProduction: options.isProduction,
		isRscRequest: options.isRscRequest,
		isrDebug: options.isrDebug,
		isrHtmlKey: options.isrHtmlKey,
		isrRscKey: options.isrRscKey,
		isrSet: options.isrSet,
		interceptionContext: options.interceptionContext,
		expireSeconds: options.expireSeconds,
		layoutCount: getAppPageLayoutProbeCount(route, activeLoadingTreePositions),
		loadSsrHandler: options.loadSsrHandler,
		middlewareContext: options.middlewareContext,
		navigationParams,
		params: options.params,
		pprFallbackShellSignal,
		pprFallbackShellReactSignal,
		renderedPathAndSearch: options.renderedPathAndSearch,
		abortPprFallbackShell: activeFallbackShellState ? () => {
			options.pprRuntime.beginFinalRender(activeFallbackShellState);
		} : void 0,
		layoutParamAccess,
		rootParams: options.rootParams,
		peekRenderObservationState() {
			return {
				dynamicFetches: peekDynamicFetchObservations(),
				requestApis: peekRenderRequestApiUsage()
			};
		},
		probeLayoutAt(layoutIndex) {
			return options.probeLayoutAt(layoutIndex, layoutParamAccess);
		},
		probePage() {
			return options.probePage(pageSearchParams);
		},
		probePageBeforeRender: options.isRscRequest,
		classification: {
			getLayoutId(index) {
				const treePosition = route.layoutTreePositions?.[index] ?? 0;
				return AppElementsWire.encodeLayoutId(createAppPageTreePath([...route.routeSegments], treePosition));
			},
			buildTimeClassifications: layoutClassifications.buildTimeClassifications,
			buildTimeReasons: layoutClassifications.buildTimeReasons,
			debugClassification: options.debugClassification,
			isLayoutObservationDynamic(layoutId) {
				return isAppLayoutObservationUnsafeForStaticReuse(layoutParamAccess.getLayoutObservation(layoutId));
			},
			async runWithIsolatedDynamicScope(fn) {
				return runWithIsolatedDynamicUsage(fn);
			}
		},
		dynamicStaleTimeSeconds: options.dynamicStaleTimeSeconds,
		revalidateSeconds: currentRevalidateSeconds,
		mountedSlotsHeader: options.mountedSlotsHeader,
		renderMode: options.renderMode ?? "navigation",
		renderErrorBoundaryResponse(renderError, errorOrigin) {
			return options.renderErrorBoundaryPage(renderError, errorOrigin);
		},
		renderLayoutSpecialError(specialError, layoutIndex) {
			return renderLayoutSpecialError(options, specialError, layoutIndex, serveStreamingMetadata);
		},
		renderPageSpecialError(specialError) {
			return renderPageSpecialError(options, specialError, serveStreamingMetadata, interceptResult.interceptOpts);
		},
		renderToReadableStream: options.renderToReadableStream,
		hasCustomGlobalError: options.hasCustomGlobalError,
		prerenderToReadableStream: options.prerenderToReadableStream,
		routePattern: route.pattern,
		runWithSuppressedHookWarning(probe) {
			return options.runWithSuppressedHookWarning(probe);
		},
		scriptNonce: options.scriptNonce,
		waitUntil(cachePromise) {
			getRequestExecutionContext()?.waitUntil(cachePromise);
		}
	});
}
async function renderLayoutSpecialError(options, specialError, layoutIndex, serveStreamingMetadata) {
	return buildAppPageSpecialErrorResponse({
		basePath: options.basePath,
		buildRscRedirectFlightStream: (rscOptions) => buildRscRedirectFlightStream({
			renderToReadableStream: options.renderToReadableStream,
			digest: rscOptions.digest
		}),
		clearRequestContext: options.clearRequestContext,
		getAndClearPendingCookies,
		serveStreamingMetadata,
		isEdgeRuntime: options.isEdgeRuntime,
		isRscRequest: options.isRscRequest,
		middlewareContext: options.middlewareContext,
		renderFallbackPage(statusCode) {
			const parentBoundaryModule = resolveAppPageParentHttpAccessBoundaryModule({
				layoutIndex,
				rootForbiddenModule: options.rootForbiddenModule,
				rootNotFoundModule: options.rootNotFoundModule,
				rootUnauthorizedModule: options.rootUnauthorizedModule,
				routeForbiddenModules: options.route.forbiddens,
				routeNotFoundModules: options.route.notFounds,
				routeUnauthorizedModules: options.route.unauthorizeds,
				statusCode
			});
			const fallbackOptions = {
				layouts: options.route.layouts.slice(0, layoutIndex),
				matchedParams: options.params
			};
			if (parentBoundaryModule) {
				fallbackOptions.boundaryComponent = parentBoundaryModule.default;
				fallbackOptions.boundaryModule = parentBoundaryModule;
			}
			return options.renderHttpAccessFallbackPage(statusCode, fallbackOptions, null);
		},
		request: options.request,
		specialError
	});
}
async function renderPageSpecialError(options, specialError, serveStreamingMetadata, intercept) {
	return buildAppPageSpecialErrorResponse({
		basePath: options.basePath,
		buildRscRedirectFlightStream: (rscOptions) => buildRscRedirectFlightStream({
			renderToReadableStream: options.renderToReadableStream,
			digest: rscOptions.digest
		}),
		clearRequestContext: options.clearRequestContext,
		getAndClearPendingCookies,
		serveStreamingMetadata,
		isEdgeRuntime: options.isEdgeRuntime,
		isRscRequest: options.isRscRequest,
		middlewareContext: options.middlewareContext,
		renderFallbackPage(statusCode) {
			const routeBoundaryModule = resolveAppPageRouteBoundaryModule(options.route, statusCode);
			const layoutCount = options.route.layouts.length;
			const { module: parentBoundaryModule, layoutIndex: boundaryLayoutIndex } = resolveAppPageParentHttpAccessBoundary({
				layoutIndex: layoutCount,
				rootForbiddenModule: options.rootForbiddenModule,
				rootNotFoundModule: options.rootNotFoundModule,
				rootUnauthorizedModule: options.rootUnauthorizedModule,
				routeForbiddenModules: options.route.forbiddens,
				routeNotFoundModules: options.route.notFounds,
				routeUnauthorizedModules: options.route.unauthorizeds,
				statusCode
			});
			const useLayoutAlignedBoundary = boundaryLayoutIndex !== null && (routeBoundaryModule === null || routeBoundaryModule === parentBoundaryModule);
			const fallbackOptions = {
				intercept,
				matchedParams: options.params
			};
			if (useLayoutAlignedBoundary && boundaryLayoutIndex !== null) {
				fallbackOptions.layouts = options.route.layouts.slice(0, boundaryLayoutIndex + 1);
				if (parentBoundaryModule) {
					fallbackOptions.boundaryComponent = parentBoundaryModule.default;
					fallbackOptions.boundaryModule = parentBoundaryModule;
				}
			}
			return options.renderHttpAccessFallbackPage(statusCode, fallbackOptions, null);
		},
		request: options.request,
		specialError
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/edge-api-runtime.js
function isEdgeApiRuntime(runtime) {
	return runtime === "edge" || runtime === "experimental-edge";
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-segment-config.js
var DYNAMIC_VALUES = /* @__PURE__ */ new Set([
	"auto",
	"error",
	"force-dynamic",
	"force-static"
]);
var FETCH_CACHE_VALUES = /* @__PURE__ */ new Set([
	"auto",
	"default-cache",
	"default-no-store",
	"force-cache",
	"force-no-store",
	"only-cache",
	"only-no-store"
]);
function isRouteSegmentDynamic(value) {
	return DYNAMIC_VALUES.has(value);
}
function isRouteSegmentFetchCache(value) {
	return FETCH_CACHE_VALUES.has(value);
}
function isRouteSegmentRuntime(value) {
	return value === "edge" || value === "experimental-edge" || value === "nodejs";
}
function resolveRevalidateSeconds(current, value) {
	if (value === false) {
		if (current === null) return Infinity;
		return current === Infinity ? Infinity : current;
	}
	if (typeof value !== "number") return current;
	if (current === null) return value;
	return value < current ? value : current;
}
function resolveDynamicStaleTimeSeconds(current, value) {
	if (typeof value !== "number" || !Number.isInteger(value) || value < 0) return current;
	return current === void 0 ? value : Math.min(current, value);
}
function isDynamicSegment(segment) {
	return segment.startsWith("[") && segment.endsWith("]");
}
function resolveSegmentConfigOwnerPosition(routeSegments, treePosition) {
	let ownerPosition = Math.min(treePosition - 1, routeSegments.length - 1);
	while (ownerPosition >= 0) {
		const segment = routeSegments[ownerPosition];
		if (!segment.startsWith("@") && !(segment.startsWith("(") && segment.endsWith(")"))) break;
		ownerPosition -= 1;
	}
	return ownerPosition;
}
function getParallelSegments(options) {
	if (!options.parallelBranches) return options.parallelSegments ?? [];
	return options.parallelBranches.flatMap((branch) => branch ? [
		branch.layout,
		...branch.configLayouts ?? [],
		branch.page
	] : []);
}
function resolveDynamicParamsConfig(options) {
	const parallelSegments = getParallelSegments(options);
	const segments = [
		...options.layouts ?? [],
		options.page,
		...parallelSegments
	];
	let dynamicParamsConfig;
	for (const segment of segments) if (segment?.dynamicParams === false) dynamicParamsConfig = false;
	else if (segment?.dynamicParams === true && dynamicParamsConfig !== false) dynamicParamsConfig = true;
	if (dynamicParamsConfig !== false || !options.routeSegments) return dynamicParamsConfig;
	const routeSegments = options.routeSegments;
	let lastDynamicPosition = -1;
	for (let index = routeSegments.length - 1; index >= 0; index--) if (isDynamicSegment(routeSegments[index])) {
		lastDynamicPosition = index;
		break;
	}
	if (lastDynamicPosition < 0) return dynamicParamsConfig;
	const layouts = options.layouts ?? [];
	const layoutPositions = options.layoutTreePositions ?? [];
	let lastDynamicSegmentIsStaticOnly = false;
	let lastDynamicSegmentHasStaticParams = false;
	layouts.forEach((layout, index) => {
		if (resolveSegmentConfigOwnerPosition(routeSegments, layoutPositions[index] ?? 0) !== lastDynamicPosition) return;
		if (layout?.dynamicParams === false) lastDynamicSegmentIsStaticOnly = true;
		if (typeof layout?.generateStaticParams === "function") lastDynamicSegmentHasStaticParams = true;
	});
	if (options.page?.dynamicParams === false) lastDynamicSegmentIsStaticOnly = true;
	if (typeof options.page?.generateStaticParams === "function") lastDynamicSegmentHasStaticParams = true;
	for (const branch of options.parallelBranches ?? []) {
		if (!branch) continue;
		const branchStartPosition = routeSegments.length - (branch.routeSegments?.length ?? 0);
		const checkSegment = (segment, ownerPosition) => {
			if (ownerPosition !== lastDynamicPosition) return;
			if (segment?.dynamicParams === false) lastDynamicSegmentIsStaticOnly = true;
			if (typeof segment?.generateStaticParams === "function") lastDynamicSegmentHasStaticParams = true;
		};
		checkSegment(branch.layout, branchStartPosition - 1);
		branch.configLayouts?.forEach((layout, index) => {
			checkSegment(layout, branchStartPosition + (branch.configLayoutTreePositions?.[index] ?? 0) - 1);
		});
		checkSegment(branch.page, branchStartPosition + (branch.routeSegments?.length ?? 0) - 1);
	}
	if (!options.parallelBranches) for (const segment of parallelSegments) {
		if (segment?.dynamicParams === false) lastDynamicSegmentIsStaticOnly = true;
		if (typeof segment?.generateStaticParams === "function") lastDynamicSegmentHasStaticParams = true;
	}
	return lastDynamicSegmentIsStaticOnly || lastDynamicSegmentHasStaticParams ? false : void 0;
}
function isCacheFetchCacheMode(value) {
	return value === "default-cache" || value === "force-cache" || value === "only-cache";
}
function describeFetchCacheConflict(value) {
	return `Route segment config has incompatible fetchCache values including "${value}".`;
}
/**
* Resolve the route segment config that applies to an App page route.
*
* Next.js collects config from every segment in the loader tree and reduces it
* into the effective route config. The generated vinext entry already knows
* the concrete layout/page modules for a route, so it should only describe
* those modules and delegate the behavior to this helper.
*/
function resolveAppPageSegmentConfig(options) {
	const segments = [...options.layouts ?? [], options.page];
	const parallelSegments = getParallelSegments(options);
	const config = { revalidateSeconds: null };
	config.dynamicParamsConfig = resolveDynamicParamsConfig(options);
	let hasForceCache = false;
	let hasForceNoStore = false;
	let hasOnlyCache = false;
	let hasOnlyNoStore = false;
	let hasParentDefaultNoStore = false;
	let hasForceDynamic = false;
	for (const segment of segments) {
		if (!segment) continue;
		if (isRouteSegmentDynamic(segment.dynamic)) {
			if (segment.dynamic === "force-dynamic") hasForceDynamic = true;
			config.dynamicConfig = hasForceDynamic ? "force-dynamic" : segment.dynamic;
		}
		if (isRouteSegmentRuntime(segment.runtime)) config.runtime = segment.runtime;
		if (isRouteSegmentFetchCache(segment.fetchCache)) {
			const fetchCache = segment.fetchCache;
			if (hasParentDefaultNoStore && (fetchCache === "auto" || isCacheFetchCacheMode(fetchCache))) throw new Error(describeFetchCacheConflict(fetchCache));
			if (fetchCache === "force-cache") hasForceCache = true;
			if (fetchCache === "force-no-store") hasForceNoStore = true;
			if (fetchCache === "only-cache") hasOnlyCache = true;
			if (fetchCache === "only-no-store") hasOnlyNoStore = true;
			if (hasForceCache && hasForceNoStore || !hasForceCache && !hasForceNoStore && hasOnlyCache && hasOnlyNoStore) throw new Error(describeFetchCacheConflict(fetchCache));
			if (fetchCache === "default-no-store") hasParentDefaultNoStore = true;
			if (hasForceCache) config.fetchCache = "force-cache";
			else if (hasForceNoStore) config.fetchCache = "force-no-store";
			else if (hasOnlyCache) config.fetchCache = "only-cache";
			else if (hasOnlyNoStore) config.fetchCache = "only-no-store";
			else config.fetchCache = fetchCache;
		}
		config.revalidateSeconds = resolveRevalidateSeconds(config.revalidateSeconds, segment.revalidate);
	}
	for (const segment of parallelSegments) {
		if (!segment) continue;
		if (segment.dynamic === "force-dynamic") {
			hasForceDynamic = true;
			config.dynamicConfig = "force-dynamic";
		} else if (config.dynamicConfig === void 0 && isRouteSegmentDynamic(segment.dynamic)) config.dynamicConfig = segment.dynamic;
		if (config.runtime === void 0 && isRouteSegmentRuntime(segment.runtime)) config.runtime = segment.runtime;
		if (isRouteSegmentFetchCache(segment.fetchCache)) {
			const fetchCache = segment.fetchCache;
			if (hasParentDefaultNoStore && (fetchCache === "auto" || isCacheFetchCacheMode(fetchCache))) throw new Error(describeFetchCacheConflict(fetchCache));
			if (fetchCache === "force-cache") hasForceCache = true;
			if (fetchCache === "force-no-store") hasForceNoStore = true;
			if (fetchCache === "only-cache") hasOnlyCache = true;
			if (fetchCache === "only-no-store") hasOnlyNoStore = true;
			if (hasForceCache && hasForceNoStore || !hasForceCache && !hasForceNoStore && hasOnlyCache && hasOnlyNoStore) throw new Error(describeFetchCacheConflict(fetchCache));
			if (fetchCache === "default-no-store") hasParentDefaultNoStore = true;
			if (hasForceCache) config.fetchCache = "force-cache";
			else if (hasForceNoStore) config.fetchCache = "force-no-store";
			else if (hasOnlyCache) config.fetchCache = "only-cache";
			else if (hasOnlyNoStore) config.fetchCache = "only-no-store";
			else if (config.fetchCache === void 0) config.fetchCache = fetchCache;
		}
		config.revalidateSeconds = resolveRevalidateSeconds(config.revalidateSeconds, segment.revalidate);
	}
	for (const segment of [options.page, ...options.parallelPages ?? []]) {
		if (!segment) continue;
		config.dynamicStaleTimeSeconds = resolveDynamicStaleTimeSeconds(config.dynamicStaleTimeSeconds, segment.unstable_dynamicStaleTime);
	}
	if (config.dynamicConfig === "force-dynamic") config.revalidateSeconds = 0;
	if (config.fetchCache === void 0) {
		if (config.dynamicConfig === "error") config.fetchCache = "only-cache";
	}
	return config;
}
function resolveAppPageFetchCacheMode(options) {
	return resolveAppPageSegmentConfig(options).fetchCache ?? null;
}
/**
* Resolve the `fetchCache` segment config exported by a route handler module.
*
* Route handlers have no layout chain, so the module's own export applies
* directly. Mirrors upstream's app-route module, which copies
* `userland.fetchCache` into the work store before invoking the handler.
*/
function resolveAppRouteHandlerFetchCacheMode(handler) {
	return isRouteSegmentFetchCache(handler.fetchCache) ? handler.fetchCache : null;
}
function isEdgeRuntime(runtime) {
	return isEdgeApiRuntime(runtime);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/navigation-state.js
/**
* Server-only navigation state backed by AsyncLocalStorage.
*
* This module provides request-scoped isolation for navigation context
* and useServerInsertedHTML callbacks. Without ALS, concurrent requests
* on Cloudflare Workers would share module-level state and leak data
* (pathnames, params, CSS-in-JS styles) between requests.
*
* This module is server-only — it imports node:async_hooks and must NOT
* be bundled for the browser. The dual-environment navigation.ts shim
* uses a registration pattern so it works in both environments.
*/
var _FALLBACK_KEY = Symbol.for("vinext.navigation.fallback");
var _g$2 = globalThis;
var _als = getOrCreateAls("vinext.navigation.als");
var _fallbackState = _g$2[_FALLBACK_KEY] ??= {
	serverContext: null,
	serverInsertedHTMLCallbacks: []
};
function _getState() {
	if (isInsideUnifiedScope()) return getRequestContext();
	return _als.getStore() ?? _fallbackState;
}
var _accessors = {
	getServerContext() {
		return _getState().serverContext;
	},
	setServerContext(ctx) {
		_getState().serverContext = ctx;
	},
	getInsertedHTMLCallbacks() {
		return _getState().serverInsertedHTMLCallbacks;
	},
	clearInsertedHTMLCallbacks() {
		_getState().serverInsertedHTMLCallbacks = [];
	}
};
_registerStateAccessors(_accessors);
globalThis[GLOBAL_ACCESSORS_KEY] = _accessors;
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/font-utils.js
/**
* Escape a string for safe interpolation inside a CSS single-quoted string.
*
* Prevents CSS injection by escaping characters that could break out of
* a `'...'` CSS string context: backslashes, single quotes, and newlines.
*
* Used by font-google-base.ts, font-local.ts, and fallback-metrics.ts.
*/
function escapeCSSString(value) {
	return value.replace(/\\/g, "\\\\").replace(/'/g, "\\'").replace(/\n/g, "\\a ").replace(/\r/g, "\\d ");
}
/**
* Validate a CSS custom property name (e.g. `--font-inter`).
*
* Custom properties must start with `--` and only contain alphanumeric
* characters, hyphens, and underscores. Anything else could be used to
* break out of the CSS declaration and inject arbitrary rules.
*
* Returns the name if valid, undefined otherwise.
*/
function sanitizeCSSVarName(name) {
	if (/^--[a-zA-Z0-9_-]+$/.test(name)) return name;
}
/**
* Sanitize a CSS font-family fallback name.
*
* Generic family names (sans-serif, serif, monospace, etc.) are used as-is.
* Named families are wrapped in escaped quotes. This prevents injection via
* crafted fallback values like `); } body { color: red; } .x {`.
*/
function sanitizeFallback(name) {
	const generics = /* @__PURE__ */ new Set([
		"serif",
		"sans-serif",
		"monospace",
		"cursive",
		"fantasy",
		"system-ui",
		"ui-serif",
		"ui-sans-serif",
		"ui-monospace",
		"ui-rounded",
		"emoji",
		"math",
		"fangsong"
	]);
	const trimmed = name.trim();
	if (generics.has(trimmed)) return trimmed;
	return `'${escapeCSSString(trimmed)}'`;
}
function singleFontOptionValue(value) {
	if (Array.isArray(value)) return new Set(value).size === 1 ? value[0] : void 0;
	return value;
}
function sanitizeFontDescriptorValue(value) {
	if (/[{};]|\/\*|\*\/|<\//i.test(value)) return void 0;
	return value;
}
function resolveFontWeight(weight) {
	const value = singleFontOptionValue(weight);
	if (!value || value.includes(" ")) return void 0;
	const numericWeight = Number(value);
	return Number.isFinite(numericWeight) ? numericWeight : void 0;
}
function resolveFontStyle(style) {
	const value = singleFontOptionValue(style);
	if (!value || value.includes(" ")) return void 0;
	return sanitizeFontDescriptorValue(value);
}
function resolveGoogleFontStyle(style) {
	if (style === void 0) return "normal";
	const value = singleFontOptionValue(style);
	if (!value) return void 0;
	if (value === "normal" || value === "italic") return value;
}
function resolveSingleFaceStyle(input) {
	const fontWeight = input.internalWeight ?? resolveFontWeight(input.weight);
	const fontStyle = (input.internalStyle ? sanitizeFontDescriptorValue(input.internalStyle) : void 0) ?? (input.google ? resolveGoogleFontStyle(input.style) : resolveFontStyle(input.style));
	return {
		fontFamily: input.fontFamily,
		...fontWeight !== void 0 ? { fontWeight } : {},
		...fontStyle ? { fontStyle } : {}
	};
}
function formatFontClassRule(className, style) {
	const fontStyle = style.fontStyle ? sanitizeFontDescriptorValue(style.fontStyle) : void 0;
	return `.${className} { ${[
		`font-family: ${style.fontFamily}`,
		...style.fontWeight !== void 0 ? [`font-weight: ${style.fontWeight}`] : [],
		...fontStyle ? [`font-style: ${fontStyle}`] : []
	].join("; ")}; }\n`;
}
/**
* Determine the MIME type for a font file based on its extension.
* Uses endsWith() only to avoid false positives from substring matches
* (e.g. ".woff" matching ".woff2").
*/
function getFontMimeType(pathOrUrl) {
	if (pathOrUrl.endsWith(".woff2")) return "font/woff2";
	if (pathOrUrl.endsWith(".woff")) return "font/woff";
	if (pathOrUrl.endsWith(".ttf")) return "font/ttf";
	if (pathOrUrl.endsWith(".otf")) return "font/opentype";
	return "font/woff2";
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/build/google-fonts/sort-variants.js
function sortFontsVariantValues(valA, valB) {
	if (valA.includes(",") && valB.includes(",")) {
		const [aPrefix, aSuffix] = valA.split(",", 2);
		const [bPrefix, bSuffix] = valB.split(",", 2);
		if (aPrefix === bPrefix) return parseInt(aSuffix) - parseInt(bSuffix);
		return parseInt(aPrefix) - parseInt(bPrefix);
	}
	return parseInt(valA) - parseInt(valB);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/build/google-fonts/build-url.js
function buildGoogleFontsUrl$1(fontFamily, axes, display) {
	const variants = [];
	if (axes.wght) for (const wght of axes.wght) if (!axes.ital) variants.push([["wght", wght], ...axes.variableAxes ?? []]);
	else for (const ital of axes.ital) variants.push([
		["ital", ital],
		["wght", wght],
		...axes.variableAxes ?? []
	]);
	else if (axes.variableAxes) variants.push([...axes.variableAxes]);
	if (axes.variableAxes) for (const variant of variants) variant.sort(([a], [b]) => {
		const aIsLowercase = a.charCodeAt(0) > 96;
		const bIsLowercase = b.charCodeAt(0) > 96;
		if (aIsLowercase && !bIsLowercase) return -1;
		if (bIsLowercase && !aIsLowercase) return 1;
		return a > b ? 1 : -1;
	});
	let url = `https://fonts.googleapis.com/css2?family=${fontFamily.replace(/ /g, "+")}`;
	if (variants.length > 0) {
		const keyList = variants[0].map(([key]) => key).join(",");
		const valueLists = variants.map((variant) => variant.map(([, val]) => val).join(",")).sort(sortFontsVariantValues).join(";");
		url = `${url}:${keyList}@${valueLists}`;
	}
	return `${url}&display=${display}`;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/font-google-base.js
/**
* next/font/google shim
*
* Provides a compatible shim for Next.js Google Fonts.
*
* Two modes:
* 1. **Dev / CDN mode** (default): Loads fonts from Google Fonts CDN via <link> tags.
* 2. **Self-hosted mode** (production build): The vinext:google-fonts Vite plugin
*    fetches font CSS + .woff2 files at build time, caches them locally, and injects
*    @font-face CSS pointing at local assets. No requests to Google at runtime.
*
* Usage:
*   import { Inter } from 'next/font/google';
*   const inter = Inter({ subsets: ['latin'], weight: ['400', '700'] });
*   // inter.className -> stable CSS class for this font/options pair
*   // inter.style -> { fontFamily: "'Inter', 'Inter Fallback'", fontStyle: "normal" }
*   // inter.variable -> CSS class that sets the font CSS variable when requested
*/
var _INJECTED_FONTS_KEY$1 = Symbol.for("vinext.font.injectedFonts");
var _INJECTED_CLASS_RULES_KEY$1 = Symbol.for("vinext.font.injectedClassRules");
var _INJECTED_VARIABLE_RULES_KEY$1 = Symbol.for("vinext.font.injectedVariableRules");
var _INJECTED_SELF_HOSTED_KEY = Symbol.for("vinext.font.injectedSelfHosted");
var _SSR_FONT_STYLES_KEY$1 = Symbol.for("vinext.font.ssrFontStyles");
var _SSR_FONT_URLS_KEY = Symbol.for("vinext.font.ssrFontUrls");
var _SSR_FONT_PRELOADS_KEY$1 = Symbol.for("vinext.font.ssrFontPreloads");
var _SSR_FONT_PRELOAD_HREFS_KEY$1 = Symbol.for("vinext.font.ssrFontPreloadHrefs");
var _g$1 = globalThis;
var injectedFonts$1 = _g$1[_INJECTED_FONTS_KEY$1] ??= /* @__PURE__ */ new Set();
/**
* Convert a font family name to a CSS variable name.
* e.g., "Inter" -> "--font-inter", "Roboto Mono" -> "--font-roboto-mono"
*/
function toVarName(family) {
	return "--font-" + family.toLowerCase().replace(/\s+/g, "-");
}
function fontClassSegment(family) {
	return family.toLowerCase().replace(/[^a-z0-9_-]+/g, "_").replace(/^_+|_+$/g, "") || "font";
}
function normalizeStringSetOption(value) {
	if (!value) return "";
	return [...new Set((Array.isArray(value) ? value : [value]).map((item) => item.trim()).filter(Boolean))].sort().join(",");
}
function normalizeWeightOption(value) {
	const normalized = normalizeStringSetOption(value);
	return normalized === "variable" ? "" : normalized;
}
function normalizeStyleOption(value) {
	const values = new Set((Array.isArray(value) ? value : value ? [value] : []).map((item) => item.trim()).filter(Boolean));
	const hasItalic = values.has("italic");
	const hasNormal = values.has("normal");
	if (!hasItalic) return "";
	return hasNormal ? "italic,normal" : "italic";
}
function normalizeFallbackOption(value) {
	if (!value) return "";
	return value.map((item) => item.trim()).join(",");
}
function normalizeBooleanOption(value) {
	if (value === void 0) return "";
	return value ? "1" : "0";
}
function normalizeStringOrBooleanOption(value) {
	if (value === void 0) return "";
	return typeof value === "boolean" ? normalizeBooleanOption(value) : value;
}
function hashString(value) {
	let hash = 2166136261;
	for (let i = 0; i < value.length; i++) {
		hash ^= value.charCodeAt(i);
		hash = Math.imul(hash, 16777619) >>> 0;
	}
	return hash.toString(36).padStart(7, "0");
}
function createFontIdentity(family, options, cssVarName, fallback) {
	return hashString([
		family,
		cssVarName,
		normalizeWeightOption(options.weight),
		normalizeStyleOption(options.style),
		normalizeStringSetOption(options.subsets),
		options.display ?? "swap",
		normalizeBooleanOption(options.preload),
		normalizeFallbackOption(fallback),
		normalizeStringOrBooleanOption(options.adjustFontFallback),
		normalizeStringSetOption(options.axes),
		options._vinext?.font?.selfHostedCSS ?? "",
		options._vinext?.font?.fontWeight?.toString() ?? "",
		options._vinext?.font?.fontStyle ?? ""
	].join("\0"));
}
/**
* Build a Google Fonts CSS URL.
*
* In production this code path is dead. The build plugin
* (`vinext:google-fonts` in `src/plugins/fonts.ts`) statically resolves
* each font call's axis values against the bundled metadata, fetches the
* Google Fonts CSS, and injects the resulting CSS as
* `_vinext.font.selfHostedCSS` so the runtime never queries Google. The shim
* only reaches this builder when the plugin's static parser bails (dynamic
* options, eval-only shapes), which is dev-only.
*
* The dev fallback intentionally has no metadata: shipping the 388 KB
* `font-data.json` to the Worker bundle would dwarf the rest of the shim,
* and the production path already has the metadata-aware variant. The
* tradeoff is that the dev fallback cannot resolve a variable font's
* actual `wght` axis range. It emits no axis segment when no `weight` is
* given, which makes Google return the default static face (200) instead
* of the broken `:wght@100..900` URL that issue #885 reports.
*/
function buildGoogleFontsUrl(family, options) {
	const weights = options.weight ? Array.isArray(options.weight) ? options.weight : [options.weight] : [];
	const styles = options.style ? Array.isArray(options.style) ? options.style : [options.style] : [];
	const hasItalic = styles.includes("italic");
	const hasNormal = styles.includes("normal");
	const ital = hasItalic ? [...hasNormal ? ["0"] : [], "1"] : void 0;
	const normalizedWeights = weights.length === 1 && weights[0] === "variable" ? [] : weights;
	return buildGoogleFontsUrl$1(family, {
		wght: normalizedWeights.length > 0 ? normalizedWeights : ital ? ["400"] : void 0,
		ital
	}, options.display ?? "swap");
}
/**
* Inject a <link> tag for the font (client-side only).
* On the server, we track font URLs for SSR head injection.
*/
function injectFontStylesheet(url) {
	if (injectedFonts$1.has(url)) return;
	injectedFonts$1.add(url);
	if (typeof document !== "undefined") {
		const link = document.createElement("link");
		link.rel = "stylesheet";
		link.href = url;
		document.head.appendChild(link);
	}
}
/** Track which className CSS rules have been injected. */
var injectedClassRules$1 = _g$1[_INJECTED_CLASS_RULES_KEY$1] ??= /* @__PURE__ */ new Set();
/**
* Inject a CSS rule that maps a className to the exported font style.
*
* This is what makes `<div className={inter.className}>` apply the font.
* Next.js generates equivalent rules at build time.
*
* In Next.js, the .className class sets font-family and any single
* font-weight/font-style. CSS variables are handled separately by .variable.
*/
function injectClassNameRule(className, fontStyle) {
	if (injectedClassRules$1.has(className)) return;
	injectedClassRules$1.add(className);
	const css = formatFontClassRule(className, fontStyle);
	if (typeof document === "undefined") {
		ssrFontStyles$1.push(css);
		return;
	}
	const styleElement = document.createElement("style");
	styleElement.textContent = css;
	styleElement.setAttribute("data-vinext-font-class", className);
	document.head.appendChild(styleElement);
}
/** Track which variable class CSS rules have been injected. */
var injectedVariableRules$1 = _g$1[_INJECTED_VARIABLE_RULES_KEY$1] ??= /* @__PURE__ */ new Set();
/**
* Inject a CSS rule that sets a CSS variable on an element.
* This is what makes `<html className={inter.variable}>` set the CSS variable
* that can be referenced by other styles (e.g., Tailwind's font-sans).
*
* In Next.js, the .variable class ONLY sets the CSS variable — it does NOT
* set font-family. This is critical because apps commonly apply multiple
* .variable classes to <body> (e.g., geistSans.variable + geistMono.variable).
* If we also set font-family here, the last class wins due to CSS cascade,
* causing all text to use that font (e.g., everything becomes monospace).
*/
function injectVariableClassRule(variableClassName, cssVarName, fontFamily) {
	if (injectedVariableRules$1.has(variableClassName)) return;
	injectedVariableRules$1.add(variableClassName);
	const css = `.${variableClassName} { ${cssVarName}: ${fontFamily}; }\n`;
	if (typeof document === "undefined") {
		ssrFontStyles$1.push(css);
		return;
	}
	const style = document.createElement("style");
	style.textContent = css;
	style.setAttribute("data-vinext-font-variable", variableClassName);
	document.head.appendChild(style);
}
var ssrFontStyles$1 = _g$1[_SSR_FONT_STYLES_KEY$1] ??= [];
/**
* Get collected SSR font class styles (used by the renderer).
* Note: We don't clear the arrays because fonts are loaded at module import
* time and need to persist across all requests in the Workers environment.
*/
function getSSRFontStyles$1() {
	return [...ssrFontStyles$1];
}
var ssrFontUrls = _g$1[_SSR_FONT_URLS_KEY] ??= [];
/**
* Get collected SSR font URLs (used by the renderer).
* Note: We don't clear the arrays because fonts are loaded at module import
* time and need to persist across all requests in the Workers environment.
*/
function getSSRFontLinks() {
	return [...ssrFontUrls];
}
var ssrFontPreloads$1 = _g$1[_SSR_FONT_PRELOADS_KEY$1] ??= [];
var ssrFontPreloadHrefs$1 = _g$1[_SSR_FONT_PRELOAD_HREFS_KEY$1] ??= /* @__PURE__ */ new Set();
/**
* Get collected SSR font preload data (used by the renderer).
* Returns an array of { href, type } objects for emitting
* <link rel="preload" as="font" ...> tags.
*/
function getSSRFontPreloads$1() {
	return [...ssrFontPreloads$1];
}
/**
* Collect build-selected font file URLs for preload link generation.
* Only collects on the server (SSR). Deduplicates by href using a Set for O(1) lookups.
*/
function collectFontPreloads(urls) {
	if (typeof document !== "undefined") return;
	for (const href of urls) if (href.startsWith("/") && !ssrFontPreloadHrefs$1.has(href)) {
		ssrFontPreloadHrefs$1.add(href);
		ssrFontPreloads$1.push({
			href,
			type: getFontMimeType(href)
		});
	}
}
/** Track injected self-hosted @font-face blocks (deduplicate) */
var injectedSelfHosted = _g$1[_INJECTED_SELF_HOSTED_KEY] ??= /* @__PURE__ */ new Set();
/**
* Inject self-hosted @font-face CSS (from the build plugin).
* This replaces the CDN <link> tag with inline CSS.
*/
function injectSelfHostedCSS(css, preloadUrls = []) {
	collectFontPreloads(preloadUrls);
	if (injectedSelfHosted.has(css)) return;
	injectedSelfHosted.add(css);
	if (typeof document === "undefined") {
		ssrFontStyles$1.push(css);
		return;
	}
	const style = document.createElement("style");
	style.textContent = css;
	style.setAttribute("data-vinext-font-selfhosted", "true");
	document.head.appendChild(style);
}
function createFontLoader(family) {
	return function fontLoader(options = {}) {
		const internal = options._vinext?.font;
		const fallback = options.fallback ?? [];
		const adjustedFallback = options.adjustFontFallback === false || !internal?.adjustedFallbackCSS ? [] : [`'${escapeCSSString(family)} Fallback'`];
		const fontFamily = [
			`'${escapeCSSString(family)}'`,
			...adjustedFallback,
			...fallback.map(sanitizeFallback)
		].join(", ");
		const defaultVarName = toVarName(family);
		const cssVarName = options.variable ? sanitizeCSSVarName(options.variable) ?? defaultVarName : defaultVarName;
		const id = createFontIdentity(family, options, cssVarName, fallback);
		const classSegment = fontClassSegment(family);
		const className = `__font_${classSegment}_${id}`;
		const variableClassName = `__variable_${classSegment}_${id}`;
		const style = resolveSingleFaceStyle({
			fontFamily,
			weight: options.weight,
			style: options.style,
			internalWeight: internal?.fontWeight,
			internalStyle: internal?.fontStyle,
			google: true
		});
		if (internal?.selfHostedCSS) injectSelfHostedCSS(internal.selfHostedCSS, internal.preloadUrls);
		else {
			const url = buildGoogleFontsUrl(family, options);
			injectFontStylesheet(url);
			if (typeof document === "undefined") {
				if (!ssrFontUrls.includes(url)) ssrFontUrls.push(url);
			}
		}
		if (options.adjustFontFallback !== false && internal?.adjustedFallbackCSS) injectSelfHostedCSS(internal.adjustedFallbackCSS);
		injectClassNameRule(className, style);
		if (options.variable) injectVariableClassRule(variableClassName, cssVarName, fontFamily);
		return {
			className,
			style,
			...options.variable ? { variable: variableClassName } : {}
		};
	};
}
var googleFonts = new Proxy({}, { get(_target, prop) {
	if (typeof prop !== "string") return void 0;
	if (prop === "__esModule") return true;
	if (prop === "default") return googleFonts;
	return createFontLoader(prop.replace(/_/g, " ").replace(/([a-z])([A-Z])/g, "$1 $2"));
} });
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/font-local.js
var _INJECTED_FONTS_KEY = Symbol.for("vinext.fontLocal.injectedFonts");
var _INJECTED_CLASS_RULES_KEY = Symbol.for("vinext.fontLocal.injectedClassRules");
var _INJECTED_VARIABLE_RULES_KEY = Symbol.for("vinext.fontLocal.injectedVariableRules");
var _INJECTED_ROOT_VARIABLES_KEY = Symbol.for("vinext.fontLocal.injectedRootVariables");
var _SSR_FONT_STYLES_KEY = Symbol.for("vinext.fontLocal.ssrFontStyles");
var _SSR_FONT_PRELOADS_KEY = Symbol.for("vinext.fontLocal.ssrFontPreloads");
var _SSR_FONT_PRELOAD_HREFS_KEY = Symbol.for("vinext.fontLocal.ssrFontPreloadHrefs");
var _g = globalThis;
_g[_INJECTED_FONTS_KEY] ??= /* @__PURE__ */ new Set();
var ssrFontStyles = _g[_SSR_FONT_STYLES_KEY] ??= [];
var ssrFontPreloads = _g[_SSR_FONT_PRELOADS_KEY] ??= [];
_g[_SSR_FONT_PRELOAD_HREFS_KEY] ??= /* @__PURE__ */ new Set();
/**
* Get collected SSR font styles (used by the renderer).
* Note: We don't clear the arrays because fonts are loaded at module import
* time and need to persist across all requests in the Workers environment.
*/
function getSSRFontStyles() {
	return [...ssrFontStyles];
}
/**
* Get collected SSR font preload data (used by the renderer).
* Returns an array of { href, type } objects for emitting
* <link rel="preload" as="font" ...> tags.
*/
function getSSRFontPreloads() {
	return [...ssrFontPreloads];
}
_g[_INJECTED_CLASS_RULES_KEY] ??= /* @__PURE__ */ new Set();
_g[_INJECTED_VARIABLE_RULES_KEY] ??= /* @__PURE__ */ new Set();
_g[_INJECTED_ROOT_VARIABLES_KEY] ??= /* @__PURE__ */ new Set();
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-hook-warning-suppression.js
var suppressHookWarningAls = new AsyncLocalStorage();
var _origConsoleError = console.error;
console.error = (...args) => {
	if (suppressHookWarningAls.getStore() === true && typeof args[0] === "string" && args[0].includes("Invalid hook call")) return;
	_origConsoleError.apply(console, args);
};
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-request-context.js
/**
* Set navigation context in the ALS-backed store. "use client" components
* rendered during SSR need the pathname/searchParams/params but the SSR
* environment has a separate module instance of next/navigation.
*
* Clearing nav context (ctx === null) also clears root params.
*/
function setAppNavigationContext(ctx) {
	setNavigationContext(ctx);
	if (ctx === null) setRootParams(null);
}
/**
* Clear all per-request ALS state owned by the App Router handler.
* Must be called before returning a non-page response (redirect, public
* file proxy, etc.) to prevent state leaking between requests on Workers.
*
* Clears: headers, navigation context, root params.
*/
function clearAppRequestContext() {
	setHeadersContext(null);
	setAppNavigationContext(null);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-prerender-static-params.js
async function callAppPrerenderStaticParams(options) {
	return runWithRootParamsScope(pickRootParams(options.params, options.rootParamNamesByPattern[options.pattern]), () => options.fn({ params: options.params }));
}
var Resources = ((React, deps, RemoveDuplicateServerCss, precedence) => {
	return function Resources() {
		return React.createElement(React.Fragment, null, [...deps.css.map((href) => React.createElement("link", {
			key: "css:" + href,
			rel: "stylesheet",
			...precedence ? { precedence } : {},
			href,
			"data-rsc-css-href": href
		})), RemoveDuplicateServerCss && React.createElement(RemoveDuplicateServerCss, { key: "remove-duplicate-css" })]);
	};
})(import_react_react_server.default, __vite_rsc_assets_manifest__.serverResources["app/layout.tsx"], void 0, "vite-rsc/importer-resources");
//#endregion
//#region app/desktop-runtime-shell.tsx
var desktop_runtime_shell_default = /* @__PURE__ */ registerClientReference(() => {
	throw new Error("Unexpectedly client reference export 'default' is called on server");
}, "e97a5adc44a3", "default");
//#endregion
//#region app/layout.tsx
var layout_exports = /* @__PURE__ */ __exportAll({
	default: () => $$wrap_RootLayout,
	metadata: () => metadata
});
var metadata = {
	title: "掌财桌面端",
	description: "14 个股票研究技能的本地运行、数据落盘与降级控制。",
	icons: {
		icon: "/favicon.png",
		shortcut: "/favicon.png",
		apple: "/favicon.png"
	}
};
function RootLayout({ children }) {
	return /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)("html", {
		lang: "zh-CN",
		children: /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsxs)("body", { children: [/* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(desktop_runtime_shell_default, {}), children] })
	});
}
var $$wrap_RootLayout = /* @__PURE__ */ __vite_rsc_wrap_css__(RootLayout, "default");
function __vite_rsc_wrap_css__(value, name) {
	if (typeof value !== "function") return value;
	function __wrapper(props) {
		return import_react_react_server.createElement(import_react_react_server.Fragment, null, import_react_react_server.createElement(Resources), import_react_react_server.createElement(value, props));
	}
	Object.defineProperty(__wrapper, "name", { value: name });
	return __wrapper;
}
//#endregion
//#region \0virtual:vinext-rsc-entry
var renderToReadableStream = createRscRenderer(renderToReadableStream$1);
var prerenderToReadableStream = createRscPrerenderer(async (model, options) => (0, import_static_edge.prerender)(model, createClientManifest(), options));
var __loadAppRouteHandlerDispatch = () => import("./_next/static/app-route-handler-dispatch-C5ErzwRd.js");
function _getSSRFontStyles() {
	return [...getSSRFontStyles$1(), ...getSSRFontStyles()];
}
function _getSSRFontPreloads() {
	return [...getSSRFontPreloads$1(), ...getSSRFontPreloads()];
}
configureMemoryCacheHandler({ cacheMaxMemorySize: void 0 });
var __draftModeSecret = "624c59b6d6098d0573ec0e9c9965ebd3";
initPregeneratedPathsFromGlobals();
var __isrDebug = process.env.NEXT_PRIVATE_DEBUG_CACHE ? console.debug.bind(console, "[vinext] ISR:") : void 0;
var __classDebug = process.env.VINEXT_DEBUG_CLASSIFICATION ? function(layoutId, reason) {
	console.debug("[vinext] CLS:", layoutId, reason);
} : void 0;
function __resolveRouteFetchCacheMode(route) {
	return resolveAppPageFetchCacheMode({
		layouts: route.layouts,
		page: route.page,
		parallelSegments: Object.values(route.slots ?? {}).flatMap((slot) => [
			slot.layout,
			...slot.configLayouts ?? [],
			slot.page ?? slot.default
		])
	});
}
function __resolveRouteDynamicConfig(route) {
	return resolveAppPageSegmentConfig({
		layouts: route.layouts,
		page: route.page,
		parallelSegments: Object.values(route.slots ?? {}).flatMap((slot) => [
			slot.layout,
			...slot.configLayouts ?? [],
			slot.page ?? slot.default
		])
	}).dynamicConfig ?? null;
}
function __resolveRouteRuntime(route) {
	return resolveAppPageSegmentConfig({
		layouts: route.layouts,
		page: route.page,
		parallelSegments: Object.values(route.slots ?? {}).flatMap((slot) => [
			slot.layout,
			...slot.configLayouts ?? [],
			slot.page ?? slot.default
		])
	}).runtime ?? null;
}
var load_0 = () => import("./_next/static/page-DfltEFnm.js");
var load_1 = () => Promise.resolve().then(() => layout_exports);
var load_2 = () => import("./_next/static/route-0b7rqtuk.js");
var load_3 = () => import("./_next/static/page-BkSmj4UC.js");
function __VINEXT_CLASS(routeIdx) {
	return ((routeIdx) => {
		switch (routeIdx) {
			case 0: return new Map([[0, "static"]]);
			case 1: return new Map([[0, "static"]]);
			case 2: return new Map([[0, "static"]]);
			default: return null;
		}
	})(routeIdx);
}
function __VINEXT_CLASS_REASONS(routeIdx) {
	return null;
}
var routes = [
	{
		__buildTimeClassifications: __VINEXT_CLASS(0),
		__buildTimeReasons: __classDebug ? __VINEXT_CLASS_REASONS(0) : null,
		ids: {
			"route": "route:/",
			"page": "page:/",
			"routeHandler": null,
			"rootBoundary": "root-boundary:/",
			"layouts": ["layout:/"],
			"templates": [],
			"slots": {}
		},
		pattern: "/",
		patternParts: [],
		isDynamic: false,
		params: [],
		staticSiblings: [],
		rootParamNames: [],
		page: null,
		__loadPage: load_0,
		routeHandler: null,
		__loadRouteHandler: null,
		layouts: [null],
		__loadLayouts: [load_1],
		routeSegments: [],
		childrenRouteSegments: null,
		templateTreePositions: [],
		layoutTreePositions: [0],
		templates: [],
		__loadTemplates: [],
		loadings: [],
		__loadLoadings: [],
		loadingTreePositions: [],
		errors: [null],
		__loadErrors: [null],
		errorPaths: [],
		__loadErrorPaths: [],
		errorTreePositions: [],
		slots: {},
		childrenSlot: null,
		siblingIntercepts: [],
		loading: null,
		__loadLoading: null,
		error: null,
		__loadError: null,
		notFound: null,
		__loadNotFound: null,
		notFoundTreePosition: null,
		notFounds: [null],
		__loadNotFounds: [null],
		forbidden: null,
		__loadForbidden: null,
		forbiddenTreePosition: null,
		forbiddens: [null],
		__loadForbiddens: [null],
		unauthorized: null,
		__loadUnauthorized: null,
		unauthorizedTreePosition: null,
		unauthorizeds: [null],
		__loadUnauthorizeds: [null]
	},
	{
		__buildTimeClassifications: __VINEXT_CLASS(1),
		__buildTimeReasons: __classDebug ? __VINEXT_CLASS_REASONS(1) : null,
		ids: {
			"route": "route:/api/runtime/ensure-bridge",
			"page": null,
			"routeHandler": "route-handler:/api/runtime/ensure-bridge",
			"rootBoundary": "root-boundary:/",
			"layouts": ["layout:/"],
			"templates": [],
			"slots": {}
		},
		pattern: "/api/runtime/ensure-bridge",
		patternParts: [
			"api",
			"runtime",
			"ensure-bridge"
		],
		isDynamic: false,
		params: [],
		staticSiblings: [],
		rootParamNames: [],
		page: null,
		__loadPage: null,
		routeHandler: null,
		__loadRouteHandler: load_2,
		layouts: [null],
		__loadLayouts: [load_1],
		routeSegments: [
			"api",
			"runtime",
			"ensure-bridge"
		],
		childrenRouteSegments: null,
		templateTreePositions: [],
		layoutTreePositions: [0],
		templates: [],
		__loadTemplates: [],
		loadings: [],
		__loadLoadings: [],
		loadingTreePositions: [],
		errors: [null],
		__loadErrors: [null],
		errorPaths: [],
		__loadErrorPaths: [],
		errorTreePositions: [],
		slots: {},
		childrenSlot: null,
		siblingIntercepts: [],
		loading: null,
		__loadLoading: null,
		error: null,
		__loadError: null,
		notFound: null,
		__loadNotFound: null,
		notFoundTreePosition: null,
		notFounds: [null],
		__loadNotFounds: [null],
		forbidden: null,
		__loadForbidden: null,
		forbiddenTreePosition: null,
		forbiddens: [null],
		__loadForbiddens: [null],
		unauthorized: null,
		__loadUnauthorized: null,
		unauthorizedTreePosition: null,
		unauthorizeds: [null],
		__loadUnauthorizeds: [null]
	},
	{
		__buildTimeClassifications: __VINEXT_CLASS(2),
		__buildTimeReasons: __classDebug ? __VINEXT_CLASS_REASONS(2) : null,
		ids: {
			"route": "route:/chat",
			"page": "page:/chat",
			"routeHandler": null,
			"rootBoundary": "root-boundary:/",
			"layouts": ["layout:/"],
			"templates": [],
			"slots": {}
		},
		pattern: "/chat",
		patternParts: ["chat"],
		isDynamic: false,
		params: [],
		staticSiblings: [],
		rootParamNames: [],
		page: null,
		__loadPage: load_3,
		routeHandler: null,
		__loadRouteHandler: null,
		layouts: [null],
		__loadLayouts: [load_1],
		routeSegments: ["chat"],
		childrenRouteSegments: null,
		templateTreePositions: [],
		layoutTreePositions: [0],
		templates: [],
		__loadTemplates: [],
		loadings: [],
		__loadLoadings: [],
		loadingTreePositions: [],
		errors: [null],
		__loadErrors: [null],
		errorPaths: [],
		__loadErrorPaths: [],
		errorTreePositions: [],
		slots: {},
		childrenSlot: null,
		siblingIntercepts: [],
		loading: null,
		__loadLoading: null,
		error: null,
		__loadError: null,
		notFound: null,
		__loadNotFound: null,
		notFoundTreePosition: null,
		notFounds: [null],
		__loadNotFounds: [null],
		forbidden: null,
		__loadForbidden: null,
		forbiddenTreePosition: null,
		forbiddens: [null],
		__loadForbiddens: [null],
		unauthorized: null,
		__loadUnauthorized: null,
		unauthorizedTreePosition: null,
		unauthorizeds: [null],
		__loadUnauthorizeds: [null]
	}
];
var __routeMatcher = createAppRscRouteMatcher(routes);
var metadataRoutes = [];
var __basePath = "";
var __trailingSlash = false;
var __htmlLimitedBots = void 0;
var rootNotFoundModule = null;
var rootForbiddenModule = null;
var rootUnauthorizedModule = null;
var rootLayouts = [layout_exports];
var __loadGlobalNotFoundModule = null;
var createRscOnErrorHandler = (request, pathname, routePath) => createAppRscOnErrorHandler(reportRequestError, request, pathname, routePath);
var __fallbackRenderer = createAppFallbackRenderer({
	basePath: "",
	trailingSlash: __trailingSlash,
	htmlLimitedBots: __htmlLimitedBots,
	rootBoundaries: {
		rootForbiddenModule,
		rootLayouts,
		rootNotFoundModule,
		rootUnauthorizedModule
	},
	globalErrorModule: null,
	loadGlobalNotFoundModule: __loadGlobalNotFoundModule,
	globalNotFoundEnabled: false,
	metadataRoutes,
	ssrLoader() {
		return import("./ssr/index.js");
	},
	fontProviders: {
		buildFontLinkHeader: buildAppPageFontLinkHeader,
		getFontLinks: getSSRFontLinks,
		getFontPreloads: _getSSRFontPreloads,
		getFontStyles: _getSSRFontStyles
	},
	makeThenableParams,
	sanitizer: sanitizeErrorForClient,
	rscRenderer: renderToReadableStream,
	getAndClearPendingCookies,
	getNavigationContext,
	resolveChildSegments: resolveAppPageChildSegments,
	clearRequestContext() {
		clearAppRequestContext();
	},
	createRscOnErrorHandler(request, pathname, routePath) {
		return createRscOnErrorHandler(request, pathname, routePath);
	}
});
function matchRoute(url) {
	return __routeMatcher.matchRoute(url);
}
function matchRequestRoute(url) {
	return __routeMatcher.matchRequestRoute(url);
}
/**
* Check if a pathname matches any intercepting route.
* Returns the match info or null.
*/
function findIntercept(pathname, sourcePathname = null) {
	return __routeMatcher.findIntercept(pathname, sourcePathname);
}
async function buildPageElements(route, params, routePath, pageRequest, layoutParamAccess, displayPathname = routePath, scriptNonce) {
	await ensureAppRouteModulesLoaded(route);
	return buildPageElements$1({
		route,
		params,
		routePath,
		displayPathname,
		pageRequest,
		globalErrorModule: null,
		rootNotFoundModule: null,
		rootForbiddenModule: null,
		rootUnauthorizedModule: null,
		metadataRoutes,
		layoutParamAccess,
		basePath: "",
		trailingSlash: __trailingSlash,
		htmlLimitedBots: __htmlLimitedBots,
		scriptNonce
	});
}
var __i18nConfig = null;
var authorizeOnDemandRevalidate = isOnDemandRevalidateRequest;
var __configRedirects = [];
var __configRewrites = {
	"beforeFiles": [],
	"afterFiles": [],
	"fallback": []
};
var __configHeaders = [];
var __runtimeImageConfig = {};
var __publicFiles = new Set([
	"/favicon.png",
	"/favicon.svg",
	"/zhangcai-icon.png"
]);
var __expireTime = 31536e3;
var __clientTraceMetadata = void 0;
var __reactMaxHeadersLength = 6e3;
var __assetPrefix = "";
var __imageAllowedWidths = [
	640,
	750,
	828,
	1080,
	1200,
	1920,
	2048,
	3840,
	32,
	48,
	64,
	96,
	128,
	256,
	384
];
var __imageConfig = {};
var __inlineCss = false;
var __hasPagesDir = false;
var getRenderedConcreteUrlPathsForRoute = getRenderedConcreteUrlPathsForRoute$1;
async function seedMemoryCacheFromPrerender(serverDir) {
	const { seedMemoryCacheFromPrerender: __seedMemoryCacheFromPrerender } = await import("./_next/static/seed-cache-KGlzaKyZ.js");
	return __seedMemoryCacheFromPrerender(serverDir, {
		buildAppPageHtmlKey(pathname) {
			return appIsrHtmlKey(pathname);
		},
		buildAppPageRscKey(pathname) {
			return appIsrRscKey(pathname);
		},
		writeAppPageEntry(key, data, metadata) {
			return isrSetPrerenderedAppPage(key, data, metadata);
		}
	});
}
var __allowedDevOrigins = [];
var __safeDevHosts = [
	"localhost",
	"127.0.0.1",
	"[::1]"
];
function __forbidden() {
	return new Response("Forbidden", {
		status: 403,
		headers: { "Content-Type": "text/plain" }
	});
}
function __validateDevRequestOrigin(request) {
	if (request.headers.get("sec-fetch-mode") === "no-cors" && request.headers.get("sec-fetch-site") === "cross-site") {
		console.warn("[vinext] Blocked cross-site no-cors request to " + new URL(request.url).pathname);
		return __forbidden();
	}
	const origin = request.headers.get("origin");
	if (!origin) return null;
	if (origin === "null") {
		if (!__allowedDevOrigins.includes("null")) {
			console.warn("[vinext] Blocked request with Origin: null. Add \"null\" to allowedDevOrigins to allow sandboxed contexts.");
			return __forbidden();
		}
		return null;
	}
	let originHostname;
	try {
		originHostname = new URL(origin).hostname.toLowerCase();
	} catch {
		return __forbidden();
	}
	if (__safeDevHosts.includes(originHostname) || originHostname.endsWith(".localhost")) return null;
	const hostHeader = (request.headers.get("x-forwarded-host") || request.headers.get("host") || "").split(",")[0].trim().split(":")[0].toLowerCase();
	if (hostHeader && originHostname === hostHeader) return null;
	for (const pattern of __allowedDevOrigins) if (pattern.startsWith("*.")) {
		const suffix = pattern.slice(1);
		if (originHostname === pattern.slice(2) || originHostname.endsWith(suffix)) return null;
	} else if (originHostname === pattern) return null;
	console.warn(`[vinext] Blocked cross-origin request from "${origin}" to ${new URL(request.url).pathname}. To allow this origin, add it to allowedDevOrigins in next.config.js.`);
	return __forbidden();
}
var generateStaticParamsMap = {};
var _virtual_vinext_rsc_entry_default = createAppRscHandler({
	basePath: "",
	buildId: "b4523198-dfc7-489f-8799-b05bddd8e10b",
	ensureRouteLoaded: ensureAppRouteModulesLoaded,
	prefetchInlining: false,
	clearRequestContext() {
		clearAppRequestContext();
	},
	registerCacheAdapters: registerConfiguredCacheAdapters,
	configHeaders: __configHeaders,
	configRedirects: __configRedirects,
	configRewrites: __configRewrites,
	imageConfig: __runtimeImageConfig,
	isDev: false,
	draftModeSecret: __draftModeSecret,
	dispatchMatchedPage({ clientReuseManifest, cleanPathname, displayPathname, formState, actionError, actionFailed, handlerStart, interceptionContext, interceptionPathname, isProgressiveActionRender, isRscRequest, middlewareContext, mountedSlotsHeader, params, pprFallbackCacheShells, pprFallbackShell, renderedConcreteUrlPaths, skipStaticParamsValidation, staticParamsValidationParams, rootParams, request, renderedPathAndSearch, route, scriptNonce, searchParams, renderMode }) {
		const PageComponent = route.page?.default;
		const __segmentConfig = resolveAppPageSegmentConfig({
			layouts: route.layouts,
			layoutTreePositions: route.layoutTreePositions,
			page: route.page,
			parallelBranches: Object.values(route.slots ?? {}).map((slot) => ({
				layout: slot.layout,
				configLayouts: slot.configLayouts,
				configLayoutTreePositions: slot.configLayoutTreePositions,
				page: slot.page ?? slot.default,
				routeSegments: slot.routeSegments
			})),
			parallelPages: Object.values(route.slots ?? {}).map((slot) => slot.page ?? slot.default),
			routeSegments: route.routeSegments
		});
		const __generateStaticParams = resolveAppPageGenerateStaticParamsSources({
			layouts: route.layouts,
			layoutTreePositions: route.layoutTreePositions,
			page: route.page,
			parallelBranches: Object.values(route.slots ?? {}).map((slot) => ({
				layout: slot.layout,
				configLayouts: slot.configLayouts,
				configLayoutTreePositions: slot.configLayoutTreePositions,
				page: slot.page ?? slot.default,
				paramNames: slot.slotParamNames,
				patternParts: slot.slotPatternParts,
				routeSegments: slot.routeSegments
			})),
			routePatternParts: route.patternParts,
			routeSegments: route.routeSegments
		});
		const _asyncRouteParams = makeThenableParams(params);
		return dispatchAppPage({
			basePath: "",
			ensureRouteLoaded: ensureAppRouteModulesLoaded,
			clientTraceMetadata: __clientTraceMetadata,
			reactMaxHeadersLength: __reactMaxHeadersLength,
			buildPageElement(targetRoute, targetParams, targetOpts, targetSearchParams, layoutParamAccess, buildOptions) {
				return buildPageElements(targetRoute, targetParams, cleanPathname, {
					opts: targetOpts,
					searchParams: targetSearchParams,
					isRscRequest,
					request,
					mountedSlotsHeader,
					renderMode,
					observeMetadataSearchParamsAccess: buildOptions?.observeMetadataSearchParamsAccess === true,
					observePageSearchParamsAccess: buildOptions?.observePageSearchParamsAccess === true,
					serveStreamingMetadata: buildOptions?.serveStreamingMetadata,
					isProduction: true
				}, layoutParamAccess, displayPathname, scriptNonce);
			},
			clientReuseManifest,
			cleanPathname,
			displayPathname,
			clearRequestContext() {
				clearAppRequestContext();
			},
			createRscOnErrorHandler(pathname, routePath) {
				return createRscOnErrorHandler(request, pathname, routePath);
			},
			debugClassification: __classDebug,
			draftModeSecret: __draftModeSecret,
			dynamicConfig: __segmentConfig.dynamicConfig,
			dynamicStaleTimeSeconds: __segmentConfig.dynamicStaleTimeSeconds,
			dynamicParamsConfig: __segmentConfig.dynamicParamsConfig,
			fetchCache: __segmentConfig.fetchCache ?? null,
			isEdgeRuntime: isEdgeRuntime(__segmentConfig.runtime),
			findIntercept(pathname) {
				return findIntercept(pathname === cleanPathname ? interceptionPathname : pathname, interceptionContext);
			},
			generateStaticParams: __generateStaticParams,
			getFontLinks: getSSRFontLinks,
			getFontPreloads: _getSSRFontPreloads,
			getFontStyles: _getSSRFontStyles,
			getNavigationContext,
			getSourceRoute(sourceRouteIndex) {
				return routes[sourceRouteIndex];
			},
			hasCustomGlobalError: false,
			hasGenerateStaticParams: __generateStaticParams.length > 0,
			hasPageDefaultExport: !!PageComponent,
			hasPageModule: !!route.page,
			handlerStart,
			htmlLimitedBots: __htmlLimitedBots,
			interceptionContext,
			expireSeconds: __expireTime,
			formState,
			actionError,
			actionFailed,
			isProgressiveActionRender,
			isProduction: true,
			isRscRequest,
			isrDebug: __isrDebug,
			isrGet,
			isrHtmlKey: appIsrHtmlKey,
			isrRscKey: appIsrRscKey,
			isrSet,
			loadSsrHandler() {
				return import("./ssr/index.js");
			},
			middlewareContext,
			mountedSlotsHeader,
			params,
			pprFallbackCacheShells,
			pprFallbackShell,
			pprRuntime: void 0,
			renderedConcreteUrlPaths,
			skipStaticParamsValidation,
			staticParamsValidationParams,
			rootParams,
			probeLayoutAt(li, layoutParamAccess) {
				return probeAppPageLayoutWithTracking({
					layoutIndex: li,
					layoutParamAccess,
					makeThenableParams,
					matchedParams: params,
					route
				});
			},
			async probePage(probeSearchParams = searchParams) {
				const __probeIntercept = findIntercept(interceptionPathname, interceptionContext);
				if (__probeIntercept) await loadAppInterceptPage(__probeIntercept);
				return Promise.all(buildAppPageProbes({
					route,
					pageComponent: PageComponent,
					asyncRouteParams: _asyncRouteParams,
					searchParams: probeSearchParams,
					intercept: __probeIntercept,
					isRscRequest,
					matchedParams: params,
					makeThenableParams
				}));
			},
			renderErrorBoundaryPage(renderErr, errorOrigin) {
				const __activeIntercept = findIntercept(interceptionPathname, interceptionContext);
				return __fallbackRenderer.renderErrorBoundary(route, renderErr, isRscRequest, request, params, scriptNonce, middlewareContext, {
					isEdgeRuntime: isEdgeRuntime(__segmentConfig.runtime),
					sourcePageSegments: __activeIntercept?.slotKey === "__vinext_page_intercept" ? __activeIntercept.sourcePageSegments : null
				}, errorOrigin);
			},
			renderHttpAccessFallbackPage(statusCode, opts, currentMiddlewareContext) {
				const __activeIntercept = findIntercept(interceptionPathname, interceptionContext);
				return __fallbackRenderer.renderHttpAccessFallback(route, statusCode, isRscRequest, request, opts, scriptNonce, currentMiddlewareContext, {
					isEdgeRuntime: isEdgeRuntime(__segmentConfig.runtime),
					routePathname: cleanPathname,
					sourcePageSegments: __activeIntercept?.slotKey === "__vinext_page_intercept" ? __activeIntercept.sourcePageSegments : null
				});
			},
			renderToReadableStream,
			prerenderToReadableStream,
			request,
			revalidateSeconds: __segmentConfig.revalidateSeconds,
			renderedPathAndSearch,
			resolveRouteFetchCacheMode(targetRoute) {
				return __resolveRouteFetchCacheMode(targetRoute);
			},
			resolveRouteDynamicConfig(targetRoute) {
				return __resolveRouteDynamicConfig(targetRoute);
			},
			rootForbiddenModule,
			rootNotFoundModule,
			rootUnauthorizedModule,
			route,
			runWithSuppressedHookWarning(probe) {
				return suppressHookWarningAls.run(true, probe);
			},
			scheduleBackgroundRegeneration(key, renderFn, errorContext) {
				triggerBackgroundRegeneration(key, renderFn, errorContext);
			},
			scriptNonce,
			searchParams,
			setNavigationContext: setAppNavigationContext,
			renderMode
		});
	},
	async dispatchMatchedRouteHandler({ cleanPathname, middlewareContext, params, request, route, searchParams }) {
		const { dispatchAppRouteHandler: __dispatchAppRouteHandler } = await __loadAppRouteHandlerDispatch();
		return __dispatchAppRouteHandler({
			basePath: "",
			cleanPathname,
			clearRequestContext() {
				clearAppRequestContext();
			},
			draftModeSecret: __draftModeSecret,
			i18n: null,
			trailingSlash: __trailingSlash,
			isrDebug: __isrDebug,
			isrGet,
			isrRouteKey: appIsrRouteKey,
			isrSet,
			middlewareContext,
			middlewareRequestHeaders: middlewareContext.requestHeaders,
			params,
			request,
			route: {
				pattern: route.pattern,
				routeHandler: route.routeHandler,
				routeSegments: route.routeSegments
			},
			scheduleBackgroundRegeneration: triggerBackgroundRegeneration,
			searchParams
		});
	},
	i18nConfig: null,
	matchRoute,
	matchRequestRoute,
	matchInterceptRoute(pathname, sourcePathname) {
		const intercept = findIntercept(pathname, sourcePathname);
		if (!intercept) return null;
		const route = routes[intercept.sourceRouteIndex];
		if (!route) return null;
		const params = Object.create(null);
		for (const name of route.params) if (Object.prototype.hasOwnProperty.call(intercept.sourceMatchedParams, name)) params[name] = intercept.sourceMatchedParams[name];
		return {
			route,
			params
		};
	},
	publicFiles: __publicFiles,
	renderNotFound({ isRscRequest, matchedParams, middlewareContext, request, route, scriptNonce }) {
		const __isEdge = route ? isEdgeRuntime(__resolveRouteRuntime(route)) : false;
		return __fallbackRenderer.renderNotFound(route, isRscRequest, request, matchedParams, scriptNonce, middlewareContext, { isEdgeRuntime: __isEdge });
	},
	rootParamNamesByPattern: {},
	setNavigationContext: setAppNavigationContext,
	staticParamsMap: generateStaticParamsMap,
	trailingSlash: __trailingSlash,
	validateDevRequestOrigin: __validateDevRequestOrigin
});
//#endregion
export { isrCacheKey as A, setNavigationContext as B, normalizePregeneratedPathname as C, applyEdgeRuntimeHeader as D, applyClientStaleTimeHeader as E, notFoundResponse as F, makeThenableParams as I, addBasePathToPathname as L, reportRequestError as M, path$1 as N, buildAppPageCacheValue as O, processMiddlewareHeaders as P, hasBasePath as R, clearPregeneratedConcretePaths as S, parseNextRedirectDigest as T, registerClientReference as V, safeJsonStringify as _, __assetPrefix, __basePath, __hasPagesDir, __i18nConfig, __imageAllowedWidths, __imageConfig, __inlineCss, scheduleAppPageRscCacheWrite as a, authorizeOnDemandRevalidate, buildPageCacheTags as b, consumeAppPageRenderObservationState as c, createAppPageRscOutputScope as d, _virtual_vinext_rsc_entry_default as default, hasCompleteNegativeRequestApiProof as f, teeAppPageRscStreamForCapture as g, generateStaticParamsMap, getRenderedConcreteUrlPathsForRoute, buildAppPageFontLinkHeader as h, finalizeAppPageRscCacheResponse as i, isrSetPrerenderedAppPage as j, isrCacheControl as k, createAppPageHtmlOutputScope as l, isAppSsrRenderResult as m, resolveAppRouteHandlerFetchCacheMode as n, readStreamAsText as o, buildAppPageLinkHeader as p, finalizeAppPageHtmlCacheResponse as r, isPossibleAppRouteActionRequest as s, seedMemoryCacheFromPrerender, callAppPrerenderStaticParams as t, createAppPageRenderObservation as u, runWithRootParamsUsage as v, parseNextHttpErrorDigest as w, addPregeneratedConcretePath as x, buildAppPageTags as y, stripBasePath as z };
