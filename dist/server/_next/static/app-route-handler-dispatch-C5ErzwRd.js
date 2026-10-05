import { r as __toESM } from "./rolldown-runtime-BT1X7o2_.js";
import { n as require_react_react_server } from "./framework~index~app-page-cache-render~app-page-cache~seed-cache~page~layout~page~app-route-~fe2f04fu-CQIcBs6F.js";
import { H as runWithRequestContext, I as closeAfterResponse, R as createRequestContext } from "./headers-lNUsrpBT.js";
import { C as getCollectedFetchTags, D as setCurrentFetchCacheMode, Ht as parseEdgeRequestCookieHeader, Mt as setHeadersAccessPhase, N as _drainPendingRevalidations, Nt as setHeadersContext, O as setCurrentFetchSoftTags, Rt as validateCookieName, S as ensureFetchPatch, Tt as markDynamicUsage, a as applyCdnResponseHeaders, bt as getAndClearPendingCookies, c as mergeMiddlewareResponseHeaders, gt as consumeDynamicUsage, ht as getRequestExecutionContext, k as setCurrentForceDynamicFetchDefault, n as NEVER_CACHE_CONTROL, t as setCacheStateHeaders, wt as isDraftModeRequest, xt as getDraftModeCookieHeader, yt as getActiveDraftModeState, zt as buildRequestHeadersFromMiddlewareResponse } from "./cache-headers-CBpU4sbE.js";
import { B as setNavigationContext, I as makeThenableParams, L as addBasePathToPathname, M as reportRequestError, P as processMiddlewareHeaders, R as hasBasePath, T as parseNextRedirectDigest, b as buildPageCacheTags, k as isrCacheControl, n as resolveAppRouteHandlerFetchCacheMode, s as isPossibleAppRouteActionRequest, v as runWithRootParamsUsage, w as parseNextHttpErrorDigest, z as stripBasePath } from "../../index.js";
import { n as buildAppRouteMissIsrCacheControl, r as decideIsr } from "./navigation-runtime-C2VuM21K.js";
import { createStaticGenerationHeadersContext, getAppRouteStaticGenerationErrorMessage } from "./app-static-generation-B6y5rJ3f.js";
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/url-safety.js
/**
* Shared URL safety utilities for Link, Form, and navigation shims.
*
* Centralizes dangerous URI scheme detection so all components and
* navigation functions use the same validation logic.
*/
/**
* Detect dangerous URI schemes that should never be navigated to.
*
* Adapted from Next.js's javascript URL detector:
* packages/next/src/client/lib/javascript-url.ts
* https://github.com/vercel/next.js/blob/canary/packages/next/src/client/lib/javascript-url.ts
*
* URL parsing ignores leading C0 control characters / spaces, and treats
* embedded tab/newline characters in the scheme as insignificant. We mirror
* that behavior here so obfuscated values like `java\nscript:` and
* `\x00javascript:` are still blocked.
*
* Vinext intentionally extends this handling to `data:` and `vbscript:` too,
* since both are also dangerous navigation targets.
*/
var LEADING_IGNORED = "[\\u0000-\\u001F \\u200B\\uFEFF]*";
var SCHEME_IGNORED = "[\\r\\n\\t]*";
function buildDangerousSchemeRegex(scheme) {
	const chars = scheme.split("").join(SCHEME_IGNORED);
	return new RegExp(`^${LEADING_IGNORED}${chars}${SCHEME_IGNORED}:`, "i");
}
var DANGEROUS_SCHEME_RES = [
	buildDangerousSchemeRegex("javascript"),
	buildDangerousSchemeRegex("data"),
	buildDangerousSchemeRegex("vbscript")
];
var DANGEROUS_URL_BLOCK_MESSAGE = "Next.js has blocked a javascript: URL as a security precaution.";
function isDangerousScheme(url) {
	const str = "" + url;
	return DANGEROUS_SCHEME_RES.some((re) => re.test(str));
}
/**
* Emit a `console.error` matching Next.js's blocked-navigation message.
*
* Next.js's `router.push` / `router.replace` / `router.prefetch` (and the
* Pages Router equivalents) throw an `Error` when the URL has a dangerous
* scheme. In the browser, React's event-handler runtime catches that throw
* and reports it through `console.error`, which is what the Next.js E2E
* `test/e2e/app-dir/javascript-urls` suite asserts on.
*
* Vinext's navigation guards run synchronously inside async event handlers
* (e.g. Link's `void handleClick(event)`), so a raw throw is dropped on the
* floor instead of bubbling up to React. Emitting the same `console.error`
* explicitly keeps observable behaviour aligned with Next.js — the test
* matcher uses `.includes("has blocked a javascript: URL as a security
* precaution.")` so any message containing that phrase satisfies it.
*
* Source reference (Next.js):
*   packages/next/src/client/components/segment-cache/navigation.ts:537
*   packages/next/src/client/components/app-router-instance.ts:345,402,442,460
*   packages/next/src/shared/lib/router/router.ts:1025,1057
*/
function reportBlockedDangerousNavigation() {
	console.error(DANGEROUS_URL_BLOCK_MESSAGE);
}
function assertSafeNavigationUrl(url, ErrorConstructor = Error) {
	if (isDangerousScheme(url)) {
		reportBlockedDangerousNavigation();
		throw new ErrorConstructor(DANGEROUS_URL_BLOCK_MESSAGE);
	}
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/internal/app-router-context.js
var import_react_react_server = /* @__PURE__ */ __toESM(require_react_react_server(), 1);
/**
* Shim for next/dist/shared/lib/app-router-context.shared-runtime
*
* Used by: @clerk/nextjs, next-intl, next-nprogress-bar, nextjs-toploader,
* next-view-transitions. Mostly type-only imports in published .d.ts files.
*
* We export the types and minimal context objects so these libraries resolve.
*/
var APP_ROUTER_CONTEXT_KEY = Symbol.for("vinext.appRouterContext");
var GLOBAL_LAYOUT_ROUTER_CONTEXT_KEY = Symbol.for("vinext.globalLayoutRouterContext");
var LAYOUT_ROUTER_CONTEXT_KEY = Symbol.for("vinext.layoutRouterContext");
var MISSING_SLOT_CONTEXT_KEY = Symbol.for("vinext.missingSlotContext");
var TEMPLATE_CONTEXT_KEY = Symbol.for("vinext.templateContext");
function getOrCreateContext(key, defaultValue) {
	if (typeof import_react_react_server.createContext !== "function") return null;
	const globalState = globalThis;
	if (!globalState[key]) globalState[key] = import_react_react_server.createContext(defaultValue);
	return globalState[key] ?? null;
}
getOrCreateContext(APP_ROUTER_CONTEXT_KEY, null);
getOrCreateContext(GLOBAL_LAYOUT_ROUTER_CONTEXT_KEY, null);
getOrCreateContext(LAYOUT_ROUTER_CONTEXT_KEY, null);
getOrCreateContext(MISSING_SLOT_CONTEXT_KEY, /* @__PURE__ */ new Set());
getOrCreateContext(TEMPLATE_CONTEXT_KEY, null);
/**
* TTL for prefetch cache entries in ms.
*
* Mirrors Next.js' `STATIC_STALETIME_MS` derivation. The plugin injects
* `process.env.__NEXT_CLIENT_ROUTER_STATIC_STALETIME` from
* `experimental.staleTimes.static` (in seconds) at build time; we convert
* to ms here.
*
* Falls back to vinext's historical default of 30s when the env var is
* absent (e.g. unit tests that import this module without going through
* the plugin's `define` pipeline). When the plugin is active and the user
* has not set `experimental.staleTimes`, Next.js' 300s default applies
* (see `resolveStaleTimes` in `config/next-config.ts`).
*/
function resolveClientRouterStaleTime(raw, fallbackMs) {
	if (raw === void 0 || raw === "") return fallbackMs;
	const seconds = Number(raw);
	if (!Number.isFinite(seconds) || seconds < 0) return fallbackMs;
	return seconds * 1e3;
}
resolveClientRouterStaleTime("0", 3e4);
resolveClientRouterStaleTime("300", 3e4);
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/cookie-utils.js
/**
* Parse the cookie name out of a serialised Set-Cookie line.
*
* Bounded by the first `;` so the attribute portion (e.g. `Path=/`) is never
* mistaken for part of the name when the value happens to contain another
* `=`. Returns null when the line is not parseable (defensive — callers keep
* unparseable entries verbatim so they don't drop user-supplied cookies).
*/
function getSetCookieName(cookie) {
	const equalsIndex = cookie.indexOf("=");
	if (equalsIndex <= 0) return null;
	const semicolonIndex = cookie.indexOf(";");
	const end = semicolonIndex === -1 ? equalsIndex : Math.min(equalsIndex, semicolonIndex);
	return cookie.slice(0, end);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-route-handler-response.js
var APP_ROUTE_REWRITE_ERROR = "NextResponse.rewrite() was used in a app route handler, this is not currently supported. Please remove the invocation to continue.";
var APP_ROUTE_NEXT_ERROR = "NextResponse.next() was used in a app route handler, this is not supported. See here for more info: https://nextjs.org/docs/messages/next-response-next-in-app-route-handler";
function hasMiddlewareHeader(headers) {
	for (const key of headers.keys()) if (key.startsWith("x-middleware-")) return true;
	return false;
}
function applyRouteHandlerMiddlewareContext(response, middlewareContext) {
	if (!middlewareContext.headers && middlewareContext.status == null) return response;
	const responseHeaders = new Headers(response.headers);
	mergeMiddlewareResponseHeaders(responseHeaders, middlewareContext.headers);
	return new Response(response.body, {
		status: middlewareContext.status ?? response.status,
		statusText: response.statusText,
		headers: responseHeaders
	});
}
function assertSupportedAppRouteHandlerResponse(response) {
	if (response.headers.has("x-middleware-rewrite")) throw new Error(APP_ROUTE_REWRITE_ERROR);
	if (response.headers.get("x-middleware-next") === "1") throw new Error(APP_ROUTE_NEXT_ERROR);
}
function buildRouteHandlerCachedResponse(cachedValue, options) {
	const headers = new Headers();
	for (const [key, value] of Object.entries(cachedValue.headers)) if (Array.isArray(value)) for (const entry of value) headers.append(key, entry);
	else headers.set(key, value);
	setCacheStateHeaders(headers, options.cacheState);
	const { cacheControl } = decideIsr({
		cacheState: options.cacheState,
		kind: "app-route",
		revalidateSeconds: options.revalidateSeconds,
		expireSeconds: options.expireSeconds,
		cacheControlMeta: options.cacheControl
	});
	applyCdnResponseHeaders(headers, { cacheControl });
	return new Response(options.isHead ? null : cachedValue.body, {
		status: cachedValue.status,
		headers
	});
}
function applyRouteHandlerRevalidateHeader(response, revalidateSeconds, expireSeconds, tags) {
	applyCdnResponseHeaders(response.headers, {
		cacheControl: buildAppRouteMissIsrCacheControl(revalidateSeconds, expireSeconds),
		tags
	});
}
function markRouteHandlerCacheMiss(response) {
	setCacheStateHeaders(response.headers, "MISS");
}
/**
* Returns true when the given Set-Cookie string already declares any of the
* attributes that follow the first `;` (case-insensitively). Used to detect
* whether a user-emitted Set-Cookie line already carries an explicit `Path=`,
* matching Next.js's `appendMutableCookies` which re-runs every cookie through
* `ResponseCookies.set` (and therefore picks up the `Path=/` default for any
* cookie that didn't supply one).
*/
function hasCookieAttribute(cookie, attributeName) {
	const target = attributeName.toLowerCase();
	let i = cookie.indexOf(";");
	while (i !== -1) {
		let start = i + 1;
		while (start < cookie.length && cookie[start] === " ") start++;
		const next = cookie.indexOf(";", start);
		const end = next === -1 ? cookie.length : next;
		const eq = cookie.indexOf("=", start);
		const attrEnd = eq === -1 || eq > end ? end : eq;
		if (cookie.slice(start, attrEnd).trim().toLowerCase() === target) return true;
		i = next;
	}
	return false;
}
/**
* Ensure each Set-Cookie line carries `Path=/` by default — Next.js's
* `appendMutableCookies` re-runs every returned cookie through
* `ResponseCookies.set`, which normalises a missing `path` to `/`. Without
* this, a raw `new Response(..., { headers: [['Set-Cookie', 'bar=bar2']] })`
* lands without `Path=/` and tests that assert on the full attribute set
* (e.g. Next.js's `app-action.test.ts` route-handler-overrides case, see
* issue #1484) break.
*/
function normalizeReturnedCookie(cookie) {
	if (hasCookieAttribute(cookie, "Path")) return cookie;
	return `${cookie.replace(/;\s*$/, "")}; Path=/`;
}
function applyMutableCookieFallbacks(headers, pendingCookies) {
	if (pendingCookies.length === 0) return;
	const returnedCookies = headers.getSetCookie();
	const returnedCookieNames = /* @__PURE__ */ new Set();
	for (const cookie of returnedCookies) {
		const name = getSetCookieName(cookie);
		if (name) returnedCookieNames.add(name);
	}
	const fallbackCookies = /* @__PURE__ */ new Map();
	const unkeyedFallbackCookies = [];
	for (const cookie of pendingCookies) {
		const name = getSetCookieName(cookie);
		if (!name) {
			unkeyedFallbackCookies.push(cookie);
			continue;
		}
		if (!returnedCookieNames.has(name)) fallbackCookies.set(name, cookie);
	}
	headers.delete("Set-Cookie");
	for (const cookie of unkeyedFallbackCookies) headers.append("Set-Cookie", cookie);
	for (const cookie of fallbackCookies.values()) headers.append("Set-Cookie", cookie);
	for (const cookie of returnedCookies) headers.append("Set-Cookie", normalizeReturnedCookie(cookie));
}
async function buildAppRouteCacheValue(response) {
	const body = await response.arrayBuffer();
	const headers = {};
	response.headers.forEach((value, key) => {
		if (key === "set-cookie" || key === "X-Vinext-Cache".toLowerCase() || key === "x-nextjs-cache".toLowerCase() || key === "cache-control" || key.startsWith("x-middleware-")) return;
		headers[key] = value;
	});
	const setCookies = response.headers.getSetCookie?.() ?? [];
	if (setCookies.length > 0) headers["set-cookie"] = setCookies;
	return {
		kind: "APP_ROUTE",
		body,
		status: response.status,
		headers
	};
}
function finalizeRouteHandlerResponse(response, options) {
	const { pendingCookies, draftCookie, isHead } = options;
	if (pendingCookies.length === 0 && !draftCookie && !isHead && !hasMiddlewareHeader(response.headers)) return response;
	const headers = new Headers(response.headers);
	processMiddlewareHeaders(headers);
	applyMutableCookieFallbacks(headers, pendingCookies);
	if (draftCookie) headers.append("Set-Cookie", draftCookie);
	return new Response(isHead ? null : response.body, {
		status: response.status,
		statusText: response.statusText,
		headers
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/server.js
var NextRequest = class extends Request {
	_nextUrl;
	_url;
	_cookies;
	constructor(input, init) {
		validateURL(typeof input !== "string" && "url" in input ? input.url : String(input));
		const { nextConfig: _nextConfig, ...requestInit } = init ?? {};
		if (input instanceof Request) {
			super(input, requestInit);
			const cf = Reflect.get(input, "cf");
			if (cf !== void 0) Object.defineProperty(this, "cf", {
				value: cf,
				enumerable: true,
				configurable: true
			});
		} else super(input, requestInit);
		const url = typeof input === "string" ? new URL(input, "http://localhost") : input instanceof URL ? input : new URL(input.url, "http://localhost");
		const i18n = _nextConfig?.i18n ? {
			locales: [..._nextConfig.i18n.locales],
			defaultLocale: _nextConfig.i18n.defaultLocale,
			domains: _nextConfig.i18n.domains?.map((domain) => ({
				...domain,
				locales: domain.locales ? [...domain.locales] : void 0
			}))
		} : void 0;
		const urlConfig = _nextConfig ? {
			basePath: _nextConfig.basePath,
			nextConfig: {
				i18n,
				trailingSlash: _nextConfig.trailingSlash
			}
		} : void 0;
		this._nextUrl = new NextURL(url, void 0, urlConfig);
		this._url = process.env.__NEXT_NO_MIDDLEWARE_URL_NORMALIZE ? url.toString() : this._nextUrl.toString();
		this._cookies = new RequestCookies(this.headers);
	}
	get nextUrl() {
		return this._nextUrl;
	}
	get url() {
		return this._url;
	}
	get cookies() {
		return this._cookies;
	}
	get page() {
		throw new Error("NextRequest.page has been removed; use URLPattern instead");
	}
	get ua() {
		throw new Error("NextRequest.ua has been removed; use userAgent() instead");
	}
	/**
	* Client IP address. Prefers Cloudflare's trusted CF-Connecting-IP header
	* over the spoofable X-Forwarded-For. Returns undefined if unavailable.
	*/
	get ip() {
		return this.headers.get("cf-connecting-ip") ?? this.headers.get("x-real-ip") ?? this.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? void 0;
	}
	/**
	* Geolocation data. Platform-dependent (e.g., Cloudflare, Vercel).
	* Returns undefined if not available.
	*/
	get geo() {
		const country = this.headers.get("cf-ipcountry") ?? this.headers.get("x-vercel-ip-country") ?? void 0;
		if (!country) return void 0;
		return {
			country,
			city: this.headers.get("cf-ipcity") ?? this.headers.get("x-vercel-ip-city") ?? void 0,
			region: this.headers.get("cf-region") ?? this.headers.get("x-vercel-ip-country-region") ?? void 0,
			latitude: this.headers.get("cf-iplatitude") ?? this.headers.get("x-vercel-ip-latitude") ?? void 0,
			longitude: this.headers.get("cf-iplongitude") ?? this.headers.get("x-vercel-ip-longitude") ?? void 0
		};
	}
	/**
	* The build ID of the Next.js application.
	* Delegates to `nextUrl.buildId` to match Next.js API surface.
	* Can be used in middleware to detect deployment skew between client and server.
	*/
	get buildId() {
		return this._nextUrl.buildId;
	}
};
function validateURL(url) {
	assertSafeNavigationUrl(String(url));
	try {
		return String(new URL(String(url)));
	} catch (error) {
		throw new Error(`URL is malformed "${String(url)}". Please use only absolute URLs - https://nextjs.org/docs/messages/middleware-relative-urls`, { cause: error });
	}
}
var NextURL = class NextURL {
	/** Internal URL stores the pathname WITHOUT basePath or locale prefix. */
	_url;
	/**
	* The configured basePath (from nextConfig). May differ from the active
	* `_basePath`: parsing only activates basePath when the URL's pathname
	* actually carries the configured prefix.
	*/
	_configBasePath;
	_basePath;
	_trailingSlash;
	_locale;
	_configDefaultLocale;
	_defaultLocale;
	_locales;
	_domains;
	_domainLocale;
	constructor(input, base, config) {
		this._url = new URL(input.toString(), base);
		this._configBasePath = config?.basePath ?? "";
		this._basePath = this._configBasePath;
		this._trailingSlash = config?.nextConfig?.trailingSlash ?? false;
		this._stripBasePath();
		const i18n = config?.nextConfig?.i18n;
		if (i18n) {
			this._locales = [...i18n.locales];
			this._domains = i18n.domains?.map((domain) => ({
				...domain,
				locales: domain.locales ? [...domain.locales] : void 0
			}));
			this._configDefaultLocale = i18n.defaultLocale;
			this._analyzeI18n();
		}
	}
	/** Strip basePath prefix from the internal pathname.
	* Mirrors Next.js's getNextPathnameInfo (re-run by NextURL.analyze() on
	* every parse, including `href` reassignment): basePath is only considered
	* active when the URL's pathname actually starts with the configured
	* basePath prefix. If the pathname is outside the basePath, the active
	* basePath is cleared to "" so that request.nextUrl.basePath reflects the
	* actual URL rather than the config value; if a later `href` assignment
	* moves the URL back inside the basePath, it is re-activated from the
	* configured value. This matches the Next.js behavior tested by
	* middleware-base-path's "should execute from absolute paths" case.
	*/
	_stripBasePath() {
		if (!this._configBasePath) return;
		if (!hasBasePath(this._url.pathname, this._configBasePath)) {
			this._basePath = "";
			return;
		}
		this._basePath = this._configBasePath;
		this._url.pathname = stripBasePath(this._url.pathname, this._configBasePath);
	}
	/** Extract locale from pathname, stripping it from the internal URL. */
	_detectPathnameLocale(locales) {
		const segments = this._url.pathname.split("/");
		const candidate = segments[1]?.toLowerCase();
		const match = locales.find((l) => l.toLowerCase() === candidate);
		if (match) this._url.pathname = "/" + segments.slice(2).join("/");
		return match;
	}
	_analyzeI18n() {
		if (!this._locales || !this._configDefaultLocale) return;
		const detectedLocale = this._detectPathnameLocale(this._locales);
		const detectedLocaleLower = detectedLocale?.toLowerCase();
		const hostname = this._url.hostname.toLowerCase();
		this._domainLocale = this._domains?.find((domain) => domain.domain.split(":", 1)[0].toLowerCase() === hostname || detectedLocaleLower === domain.defaultLocale.toLowerCase() || domain.locales?.some((locale) => locale.toLowerCase() === detectedLocaleLower));
		this._defaultLocale = this._domainLocale?.defaultLocale ?? this._configDefaultLocale;
		this._locale = detectedLocale ?? this._defaultLocale;
	}
	/**
	* Reconstruct the full pathname with basePath + locale prefix and apply
	* the configured trailingSlash policy.
	* Mirrors Next.js's internal formatNextPathnameInfo().
	*/
	_formatPathname() {
		let prefix = this._basePath;
		const inner = this._url.pathname;
		const innerLower = inner.toLowerCase();
		if (!(innerLower === "/api" || innerLower.startsWith("/api/")) && this._locale && this._locale !== this._defaultLocale) prefix += "/" + this._locale;
		const composed = !prefix ? inner : inner === "/" ? prefix : prefix + inner;
		return this._applyTrailingSlash(composed);
	}
	/**
	* Apply the configured trailingSlash policy to a composed pathname. Matches
	* Next.js's `formatNextPathnameInfo`: when `trailingSlash` is true, add a
	* trailing slash unless the path is empty/root; when false, strip a trailing
	* slash unless the path is empty/root.
	*/
	_applyTrailingSlash(pathname) {
		if (pathname === "" || pathname === "/") return pathname;
		if (this._trailingSlash) return pathname.endsWith("/") ? pathname : pathname + "/";
		return pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;
	}
	get href() {
		const formatted = this._formatPathname();
		if (formatted === this._url.pathname) return this._url.href;
		const { href, pathname, search, hash } = this._url;
		const baseEnd = href.length - pathname.length - search.length - hash.length;
		return href.slice(0, baseEnd) + formatted + search + hash;
	}
	set href(value) {
		this._url.href = value;
		this._stripBasePath();
		this._analyzeI18n();
	}
	get origin() {
		return this._url.origin;
	}
	get protocol() {
		return this._url.protocol;
	}
	set protocol(value) {
		this._url.protocol = value;
	}
	get username() {
		return this._url.username;
	}
	set username(value) {
		this._url.username = value;
	}
	get password() {
		return this._url.password;
	}
	set password(value) {
		this._url.password = value;
	}
	get host() {
		return this._url.host;
	}
	set host(value) {
		this._url.host = value;
	}
	get hostname() {
		return this._url.hostname;
	}
	set hostname(value) {
		this._url.hostname = value;
	}
	get port() {
		return this._url.port;
	}
	set port(value) {
		this._url.port = value;
	}
	/** Returns the pathname WITHOUT basePath or locale prefix. */
	get pathname() {
		return this._url.pathname;
	}
	set pathname(value) {
		this._url.pathname = value;
	}
	get search() {
		return this._url.search;
	}
	set search(value) {
		this._url.search = value;
	}
	get searchParams() {
		return this._url.searchParams;
	}
	get hash() {
		return this._url.hash;
	}
	set hash(value) {
		this._url.hash = value;
	}
	get basePath() {
		return this._basePath;
	}
	set basePath(value) {
		this._basePath = value === "" ? "" : value.startsWith("/") ? value : "/" + value;
	}
	get locale() {
		return this._locale ?? "";
	}
	set locale(value) {
		if (this._locales) {
			if (!value) {
				this._locale = this._defaultLocale;
				return;
			}
			if (!this._locales.includes(value)) throw new TypeError(`The locale "${value}" is not in the configured locales: ${this._locales.join(", ")}`);
		}
		this._locale = this._locales ? value : this._locale;
	}
	get defaultLocale() {
		return this._defaultLocale;
	}
	get domainLocale() {
		if (!this._domainLocale) return void 0;
		return {
			...this._domainLocale,
			locales: this._domainLocale.locales ? [...this._domainLocale.locales] : void 0
		};
	}
	get locales() {
		return this._locales ? [...this._locales] : void 0;
	}
	clone() {
		const nextConfig = {};
		if (this._locales) nextConfig.i18n = {
			locales: [...this._locales],
			defaultLocale: this._configDefaultLocale,
			domains: this._domains?.map((domain) => ({
				...domain,
				locales: domain.locales ? [...domain.locales] : void 0
			}))
		};
		if (this._trailingSlash) nextConfig.trailingSlash = true;
		const config = {
			basePath: this._configBasePath,
			nextConfig: Object.keys(nextConfig).length > 0 ? nextConfig : void 0
		};
		return new NextURL(this.href, void 0, config);
	}
	toString() {
		return this.href;
	}
	toJSON() {
		return this.href;
	}
	/**
	* The build ID of the Next.js application.
	* Set from `generateBuildId` in next.config.js, or a random UUID if not configured.
	* Can be used in middleware to detect deployment skew between client and server.
	* Matches the Next.js API: `request.nextUrl.buildId`.
	*/
	get buildId() {
		return "b4523198-dfc7-489f-8799-b05bddd8e10b";
	}
};
var RequestCookies = class {
	_headers;
	_parsed;
	constructor(headers) {
		this._headers = headers;
		this._parsed = parseEdgeRequestCookieHeader(headers.get("cookie") ?? "");
	}
	get(name) {
		const value = this._parsed.get(name);
		return value !== void 0 ? {
			name,
			value
		} : void 0;
	}
	getAll(nameOrOptions) {
		const name = typeof nameOrOptions === "string" ? nameOrOptions : nameOrOptions?.name;
		return [...this._parsed.entries()].filter(([cookieName]) => name === void 0 || cookieName === name).map(([cookieName, value]) => ({
			name: cookieName,
			value
		}));
	}
	has(name) {
		return this._parsed.has(name);
	}
	set(nameOrOptions, value) {
		let cookieName;
		let cookieValue;
		if (typeof nameOrOptions === "string") {
			cookieName = nameOrOptions;
			cookieValue = value ?? "";
		} else {
			cookieName = nameOrOptions.name;
			cookieValue = nameOrOptions.value;
		}
		validateCookieName(cookieName);
		this._parsed.set(cookieName, cookieValue);
		this._syncHeader();
		return this;
	}
	delete(names) {
		if (Array.isArray(names)) {
			const results = names.map((name) => {
				validateCookieName(name);
				return this._parsed.delete(name);
			});
			this._syncHeader();
			return results;
		}
		validateCookieName(names);
		const result = this._parsed.delete(names);
		this._syncHeader();
		return result;
	}
	clear() {
		this._parsed.clear();
		this._syncHeader();
		return this;
	}
	get size() {
		return this._parsed.size;
	}
	toString() {
		return this._serialize();
	}
	_serialize() {
		return [...this._parsed.entries()].map(([n, v]) => `${n}=${encodeURIComponent(v)}`).join("; ");
	}
	_syncHeader() {
		if (this._parsed.size === 0) this._headers.delete("cookie");
		else this._headers.set("cookie", this._serialize());
	}
	[Symbol.iterator]() {
		return new Map(this.getAll().map((cookie) => [cookie.name, cookie])).entries();
	}
};
var ReadonlyRequestCookiesError = class ReadonlyRequestCookiesError extends Error {
	constructor() {
		super("Cookies can only be modified in a Server Action or Route Handler. Read more: https://nextjs.org/docs/app/api-reference/functions/cookies#options");
	}
	static callable() {
		throw new ReadonlyRequestCookiesError();
	}
};
var REQUEST_HEADERS_MUTATING_METHODS = /* @__PURE__ */ new Set([
	"set",
	"delete",
	"append"
]);
var ReadonlyRequestHeadersError = class ReadonlyRequestHeadersError extends Error {
	constructor() {
		super("Headers cannot be modified. Read more: https://nextjs.org/docs/app/api-reference/functions/headers");
	}
	static callable() {
		throw new ReadonlyRequestHeadersError();
	}
};
function sealRequestHeaders(headers) {
	return new Proxy(headers, { get(target, prop) {
		if (typeof prop === "string" && REQUEST_HEADERS_MUTATING_METHODS.has(prop)) return ReadonlyRequestHeadersError.callable;
		const value = Reflect.get(target, prop, target);
		return typeof value === "function" ? value.bind(target) : value;
	} });
}
function sealRequestCookies(cookies) {
	return new Proxy(cookies, { get(target, prop) {
		if (prop === "set" || prop === "delete" || prop === "clear") return ReadonlyRequestCookiesError.callable;
		const value = Reflect.get(target, prop, target);
		return typeof value === "function" ? value.bind(target) : value;
	} });
}
globalThis.URLPattern;
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-route-handler-runtime.js
var ROUTE_HANDLER_HTTP_METHODS = [
	"GET",
	"HEAD",
	"POST",
	"PUT",
	"DELETE",
	"PATCH",
	"OPTIONS"
];
/**
* Checks whether a string is a recognized HTTP method for App Router route
* handlers. Invalid methods must be rejected with 400 before any auto-OPTIONS
* or 405 logic runs.
*
* @see https://github.com/vercel/next.js/blob/canary/packages/next/src/server/web/http.ts
*/
function isValidHTTPMethod(maybeMethod) {
	return ROUTE_HANDLER_HTTP_METHODS.includes(maybeMethod);
}
function collectRouteHandlerMethods(handler) {
	const methods = ROUTE_HANDLER_HTTP_METHODS.filter((method) => typeof handler[method] === "function");
	if (methods.includes("GET") && !methods.includes("HEAD")) methods.push("HEAD");
	return methods;
}
function buildRouteHandlerAllowHeader(exportedMethods) {
	const allow = new Set(exportedMethods);
	allow.add("OPTIONS");
	return Array.from(allow).sort().join(", ");
}
var _KNOWN_DYNAMIC_APP_ROUTE_HANDLERS_KEY = Symbol.for("vinext.appRouteHandlerRuntime.knownDynamicHandlers");
var _g = globalThis;
var knownDynamicAppRouteHandlers = _g[_KNOWN_DYNAMIC_APP_ROUTE_HANDLERS_KEY] ??= /* @__PURE__ */ new Set();
function isKnownDynamicAppRoute(pattern) {
	return knownDynamicAppRouteHandlers.has(pattern);
}
function markKnownDynamicAppRoute(pattern) {
	knownDynamicAppRouteHandlers.add(pattern);
}
function bindMethodIfNeeded(value, target) {
	return typeof value === "function" ? value.bind(target) : value;
}
function buildNextConfig(options) {
	if (!options.basePath && !options.i18n && !options.trailingSlash) return null;
	return {
		basePath: options.basePath,
		i18n: options.i18n ?? void 0,
		trailingSlash: options.trailingSlash
	};
}
function rebuildRequestWithHeaders(input, headers) {
	const method = input.method;
	const hasBody = method !== "GET" && method !== "HEAD";
	const init = {
		method,
		headers,
		cache: input.cache,
		credentials: input.credentials,
		integrity: input.integrity,
		keepalive: input.keepalive,
		mode: input.mode,
		redirect: input.redirect,
		referrer: input.referrer,
		referrerPolicy: input.referrerPolicy,
		signal: input.signal
	};
	if (hasBody && input.body) {
		init.body = input.body;
		init.duplex = "half";
	}
	return new Request(input.url, init);
}
function cleanStaticUrl(url) {
	const cleanUrl = new URL(url);
	cleanUrl.protocol = "http:";
	cleanUrl.host = "localhost:3000";
	cleanUrl.username = "";
	cleanUrl.password = "";
	cleanUrl.search = "";
	cleanUrl.hash = "";
	return cleanUrl.href;
}
function readEmptyBodyAsArrayBuffer() {
	return new Response(null).arrayBuffer();
}
function readEmptyBodyAsBlob() {
	return new Response(null).blob();
}
function readEmptyBodyAsFormData() {
	return new Response(null).formData();
}
function readEmptyBodyAsJson() {
	return new Response(null).json();
}
function readEmptyBodyAsText() {
	return new Response(null).text();
}
function createTrackedAppRouteRequest(request, options = {}) {
	let didAccessDynamicRequest = false;
	const requestMode = options.requestMode ?? "auto";
	const nextConfig = buildNextConfig(options);
	const markDynamicAccess = (access) => {
		didAccessDynamicRequest = true;
		options.onDynamicAccess?.(access);
	};
	const wrapNextUrl = (nextUrl) => {
		return new Proxy(nextUrl, { get(target, prop) {
			switch (prop) {
				case "search":
				case "searchParams":
				case "url":
				case "href":
				case "toJSON":
				case "toString":
				case "origin":
					markDynamicAccess(`nextUrl.${String(prop)}`);
					return bindMethodIfNeeded(Reflect.get(target, prop, target), target);
				case "clone": return () => wrapNextUrl(target.clone());
				default: return bindMethodIfNeeded(Reflect.get(target, prop, target), target);
			}
		} });
	};
	const wrapForceStaticNextUrl = (nextUrl) => {
		const emptySearchParams = new URLSearchParams();
		const staticHref = cleanStaticUrl(nextUrl.href);
		return new Proxy(nextUrl, { get(target, prop) {
			switch (prop) {
				case "search": return "";
				case "searchParams": return emptySearchParams;
				case "href": return staticHref;
				case "url": return;
				case "toJSON":
				case "toString": return () => staticHref;
				case "clone": return () => wrapForceStaticNextUrl(target.clone());
				default: return bindMethodIfNeeded(Reflect.get(target, prop, target), target);
			}
		} });
	};
	const throwStaticGenerationError = (expression) => {
		throw new Error(options.staticGenerationErrorMessage?.(expression) ?? `Route handler with \`dynamic = "error"\` used ${expression}.`);
	};
	const wrapRequireStaticNextUrl = (nextUrl) => {
		return new Proxy(nextUrl, { get(target, prop) {
			switch (prop) {
				case "search":
				case "searchParams":
				case "url":
				case "href":
				case "toJSON":
				case "toString":
				case "origin": return throwStaticGenerationError(`nextUrl.${String(prop)}`);
				case "clone": return () => wrapRequireStaticNextUrl(target.clone());
				default: return bindMethodIfNeeded(Reflect.get(target, prop, target), target);
			}
		} });
	};
	const wrapRequest = (rawInput) => {
		let input = rawInput;
		if (options.basePath) {
			const inputUrl = new URL(rawInput.url);
			const prefixedPathname = addBasePathToPathname(inputUrl.pathname, options.basePath);
			if (prefixedPathname !== inputUrl.pathname) {
				inputUrl.pathname = prefixedPathname;
				input = new Request(inputUrl, rawInput);
			}
		}
		const requestHeaders = options.middlewareHeaders ? buildRequestHeadersFromMiddlewareResponse(input.headers, options.middlewareHeaders) : null;
		const requestWithOverrides = requestHeaders ? rebuildRequestWithHeaders(input, requestHeaders) : input;
		const nextRequest = requestWithOverrides instanceof NextRequest ? requestWithOverrides : new NextRequest(requestWithOverrides, { nextConfig: nextConfig ?? void 0 });
		let proxiedNextUrl = null;
		let forceStaticNextUrl = null;
		let requireStaticNextUrl = null;
		let forceStaticHeaders = null;
		let forceStaticCookies = null;
		return new Proxy(nextRequest, { get(target, prop) {
			if (requestMode === "force-static") switch (prop) {
				case "nextUrl":
					forceStaticNextUrl ??= wrapForceStaticNextUrl(target.nextUrl);
					return forceStaticNextUrl;
				case "headers":
					forceStaticHeaders ??= sealRequestHeaders(new Headers());
					return forceStaticHeaders;
				case "cookies":
					forceStaticCookies ??= sealRequestCookies(new RequestCookies(new Headers()));
					return forceStaticCookies;
				case "url": return cleanStaticUrl(target.nextUrl.href);
				case "ip":
				case "geo": return;
				case "body": return null;
				case "arrayBuffer": return readEmptyBodyAsArrayBuffer;
				case "blob": return readEmptyBodyAsBlob;
				case "formData": return readEmptyBodyAsFormData;
				case "json": return readEmptyBodyAsJson;
				case "text": return readEmptyBodyAsText;
				case "clone": return () => wrapRequest(target.clone());
				default: return bindMethodIfNeeded(Reflect.get(target, prop, target), target);
			}
			if (requestMode === "error") switch (prop) {
				case "nextUrl":
					requireStaticNextUrl ??= wrapRequireStaticNextUrl(target.nextUrl);
					return requireStaticNextUrl;
				case "headers":
				case "cookies":
				case "url":
				case "ip":
				case "geo":
				case "body":
				case "blob":
				case "json":
				case "text":
				case "arrayBuffer":
				case "formData": return throwStaticGenerationError(`request.${String(prop)}`);
				case "clone": return () => wrapRequest(target.clone());
				default: return bindMethodIfNeeded(Reflect.get(target, prop, target), target);
			}
			switch (prop) {
				case "nextUrl":
					proxiedNextUrl ??= wrapNextUrl(target.nextUrl);
					return proxiedNextUrl;
				case "headers":
				case "cookies":
				case "ip":
				case "geo":
				case "url":
				case "body":
				case "blob":
				case "json":
				case "text":
				case "arrayBuffer":
				case "formData":
					markDynamicAccess(`request.${String(prop)}`);
					return bindMethodIfNeeded(Reflect.get(target, prop, target), target);
				case "clone": return () => wrapRequest(target.clone());
				default: return bindMethodIfNeeded(Reflect.get(target, prop, target), target);
			}
		} });
	};
	return {
		request: wrapRequest(request),
		didAccessDynamicRequest() {
			return didAccessDynamicRequest;
		}
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-route-handler-policy.js
function getAppRouteHandlerRevalidateSeconds(handler) {
	const { revalidate } = handler;
	if (revalidate === false) return Infinity;
	if (typeof revalidate !== "number" || !Number.isFinite(revalidate) || revalidate < 0) return null;
	return revalidate;
}
function hasAppRouteHandlerDefaultExport(handler) {
	return typeof handler.default === "function";
}
function resolveAppRouteHandlerMethod(handler, method) {
	const exportedMethods = collectRouteHandlerMethods(handler);
	const allowHeaderForOptions = buildRouteHandlerAllowHeader(exportedMethods);
	const shouldAutoRespondToOptions = method === "OPTIONS" && typeof handler.OPTIONS !== "function";
	let handlerFn = typeof handler[method] === "function" ? handler[method] : void 0;
	let isAutoHead = false;
	if (method === "HEAD" && typeof handler.HEAD !== "function" && typeof handler.GET === "function") {
		handlerFn = handler.GET;
		isAutoHead = true;
	}
	return {
		allowHeaderForOptions,
		exportedMethods,
		handlerFn,
		isAutoHead,
		shouldAutoRespondToOptions
	};
}
function shouldReadAppRouteHandlerCache(options) {
	return options.isProduction && options.revalidateSeconds !== null && options.revalidateSeconds > 0 && options.revalidateSeconds !== Infinity && options.dynamicConfig !== "force-dynamic" && !options.isDraftMode && !options.isKnownDynamic && (options.method === "GET" || options.isAutoHead) && typeof options.handlerFn === "function";
}
function shouldApplyAppRouteHandlerRevalidateHeader(options) {
	return options.revalidateSeconds !== null && !options.isDraftMode && !options.dynamicUsedInHandler && (options.method === "GET" || options.isAutoHead) && !options.handlerSetCacheControl;
}
function shouldWriteAppRouteHandlerCache(options) {
	return options.isProduction && options.revalidateSeconds !== null && options.revalidateSeconds > 0 && options.revalidateSeconds !== Infinity && options.dynamicConfig !== "force-dynamic" && !options.isDraftMode && shouldApplyAppRouteHandlerRevalidateHeader(options);
}
function resolveAppRouteHandlerSpecialError(error, requestUrl, options) {
	if (!(error && typeof error === "object" && "digest" in error)) return null;
	const digest = String(error.digest);
	const redirect = parseNextRedirectDigest(digest);
	if (redirect) return {
		kind: "redirect",
		location: new URL(redirect.url, requestUrl).toString(),
		statusCode: options?.isAction ? 303 : redirect.status
	};
	const httpError = parseNextHttpErrorDigest(digest);
	if (httpError) return {
		kind: "status",
		statusCode: httpError.status
	};
	return null;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-route-handler-execution.js
function applyDraftModeCachePolicy(response, isDraftMode) {
	if (!isDraftMode) return response;
	const headers = new Headers(response.headers);
	applyCdnResponseHeaders(headers, { cacheControl: NEVER_CACHE_CONTROL });
	return new Response(response.body, {
		status: response.status,
		statusText: response.statusText,
		headers
	});
}
function configureAppRouteStaticGenerationContext(options) {
	if (options.dynamicConfig === "force-static" || options.dynamicConfig === "error") {
		setHeadersContext(createStaticGenerationHeadersContext({
			draftModeEnabled: options.isDraftMode ?? (options.draftModeSecret !== void 0 && isDraftModeRequest(options.request, options.draftModeSecret)),
			draftModeSecret: options.draftModeSecret,
			dynamicConfig: options.dynamicConfig,
			routeKind: "route",
			routePattern: options.routePattern
		}));
		options.setHeadersAccessPhase?.("route-handler");
	}
}
async function runAppRouteHandler(options) {
	options.consumeDynamicUsage();
	configureAppRouteStaticGenerationContext(options);
	const trackedRequest = createTrackedAppRouteRequest(options.request, {
		basePath: options.basePath,
		i18n: options.i18n,
		trailingSlash: options.trailingSlash,
		middlewareHeaders: options.middlewareRequestHeaders,
		onDynamicAccess() {
			options.markDynamicUsage();
		},
		requestMode: options.dynamicConfig === "force-static" || options.dynamicConfig === "error" ? options.dynamicConfig : "auto",
		staticGenerationErrorMessage(expression) {
			return getAppRouteStaticGenerationErrorMessage(options.routePattern, expression);
		}
	});
	const response = await runWithRootParamsUsage({
		kind: "route-handler",
		routePattern: options.routePattern ?? new URL(options.request.url).pathname
	}, () => options.handlerFn(trackedRequest.request, { params: options.params }));
	return {
		dynamicUsedInHandler: options.consumeDynamicUsage(),
		response
	};
}
async function executeAppRouteHandler(options) {
	const previousHeadersPhase = options.setHeadersAccessPhase("route-handler");
	try {
		let handlerResult;
		try {
			handlerResult = await runAppRouteHandler({
				...options,
				dynamicConfig: options.handler.dynamic
			});
		} finally {
			await _drainPendingRevalidations();
		}
		const { dynamicUsedInHandler, response } = handlerResult;
		assertSupportedAppRouteHandlerResponse(response);
		const handlerSetCacheControl = response.headers.has("cache-control");
		if (dynamicUsedInHandler) markKnownDynamicAppRoute(options.routePattern);
		const pendingCookies = options.getAndClearPendingCookies();
		const handlerDraftCookie = options.getDraftModeCookieHeader();
		const draftCookie = handlerDraftCookie ?? options.initialDraftModeCookie;
		const shouldApplyDraftPolicy = (options.getActiveDraftModeState?.() ?? options.isDraftMode === true) || draftCookie != null;
		if (handlerDraftCookie != null) markKnownDynamicAppRoute(options.routePattern);
		const routeTags = options.buildPageCacheTags(options.cleanPathname, options.getCollectedFetchTags());
		if (shouldApplyAppRouteHandlerRevalidateHeader({
			dynamicUsedInHandler,
			handlerSetCacheControl,
			isAutoHead: options.isAutoHead,
			isDraftMode: shouldApplyDraftPolicy,
			method: options.method,
			revalidateSeconds: options.revalidateSeconds
		})) {
			const revalidateSeconds = options.revalidateSeconds;
			if (revalidateSeconds == null) throw new Error("Expected route handler revalidate seconds");
			applyRouteHandlerRevalidateHeader(response, revalidateSeconds, options.expireSeconds, routeTags);
		}
		if (shouldWriteAppRouteHandlerCache({
			dynamicConfig: options.handler.dynamic,
			dynamicUsedInHandler,
			handlerSetCacheControl,
			isAutoHead: options.isAutoHead,
			isDraftMode: shouldApplyDraftPolicy,
			isProduction: options.isProduction,
			method: options.method,
			revalidateSeconds: options.revalidateSeconds
		})) {
			markRouteHandlerCacheMiss(response);
			const routeClone = response.clone();
			const routeKey = options.isrRouteKey(options.cleanPathname);
			const revalidateSeconds = options.revalidateSeconds;
			if (revalidateSeconds == null) throw new Error("Expected route handler cache revalidate seconds");
			const routeWritePromise = (async () => {
				try {
					const routeCacheValue = await buildAppRouteCacheValue(routeClone);
					await options.isrSet(routeKey, routeCacheValue, {
						cacheControl: isrCacheControl(revalidateSeconds, { expireSeconds: options.expireSeconds }),
						tags: routeTags
					});
					options.isrDebug?.("route cache written", routeKey);
				} catch (cacheErr) {
					console.error("[vinext] ISR route cache write error:", cacheErr);
				}
			})();
			options.executionContext?.waitUntil(routeWritePromise);
		}
		options.clearRequestContext();
		return applyDraftModeCachePolicy(applyRouteHandlerMiddlewareContext(finalizeRouteHandlerResponse(response, {
			pendingCookies,
			draftCookie,
			isHead: options.isAutoHead
		}), options.middlewareContext), shouldApplyDraftPolicy);
	} catch (error) {
		const pendingCookies = options.getAndClearPendingCookies();
		const handlerDraftCookie = options.getDraftModeCookieHeader();
		const draftCookie = handlerDraftCookie ?? options.initialDraftModeCookie;
		const shouldApplyDraftPolicy = (options.getActiveDraftModeState?.() ?? options.isDraftMode === true) || draftCookie != null;
		if (handlerDraftCookie != null) markKnownDynamicAppRoute(options.routePattern);
		const specialError = resolveAppRouteHandlerSpecialError(error, options.request.url, { isAction: isPossibleAppRouteActionRequest(options.request) });
		options.clearRequestContext();
		if (specialError) {
			if (specialError.kind === "redirect") return applyDraftModeCachePolicy(applyRouteHandlerMiddlewareContext(finalizeRouteHandlerResponse(new Response(null, {
				status: specialError.statusCode,
				headers: { Location: specialError.location }
			}), {
				pendingCookies,
				draftCookie,
				isHead: options.isAutoHead
			}), options.middlewareContext), shouldApplyDraftPolicy);
			return applyDraftModeCachePolicy(applyRouteHandlerMiddlewareContext(new Response(null, { status: specialError.statusCode }), options.middlewareContext), shouldApplyDraftPolicy);
		}
		console.error("[vinext] Route handler error:", error);
		options.reportRequestError(error instanceof Error ? error : new Error(String(error)), {
			path: options.cleanPathname,
			method: options.request.method,
			headers: Object.fromEntries(options.request.headers.entries())
		}, {
			routerKind: "App Router",
			routePath: options.routePattern,
			routeType: "route"
		});
		return applyDraftModeCachePolicy(applyRouteHandlerMiddlewareContext(new Response(null, { status: 500 }), options.middlewareContext), shouldApplyDraftPolicy);
	} finally {
		options.setHeadersAccessPhase(previousHeadersPhase);
	}
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-route-handler-cache.js
var EMPTY_PARAMS = Object.freeze({});
function getCachedAppRouteValue(entry) {
	return entry?.value.value && entry.value.value.kind === "APP_ROUTE" ? entry.value.value : null;
}
async function readAppRouteHandlerCacheResponse(options) {
	const routeKey = options.isrRouteKey(options.cleanPathname);
	try {
		const cached = await options.isrGet(routeKey);
		const cachedValue = getCachedAppRouteValue(cached);
		if (cached?.isExpired) {
			options.isrDebug?.("MISS (expired route)", options.cleanPathname);
			return null;
		}
		if (cachedValue && !cached?.isStale) {
			options.isrDebug?.("HIT (route)", options.cleanPathname);
			options.clearRequestContext();
			return applyRouteHandlerMiddlewareContext(buildRouteHandlerCachedResponse(cachedValue, {
				cacheState: "HIT",
				cacheControl: cached?.value.cacheControl,
				expireSeconds: options.expireSeconds,
				isHead: options.isAutoHead,
				revalidateSeconds: options.revalidateSeconds
			}), options.middlewareContext);
		}
		if (cached?.isStale && cachedValue) {
			const staleValue = cachedValue;
			const revalidateSearchParams = new URLSearchParams(options.revalidateSearchParams);
			options.scheduleBackgroundRegeneration(routeKey, async () => {
				await options.runInRevalidationContext(async () => {
					options.setNavigationContext({
						pathname: options.cleanPathname,
						searchParams: revalidateSearchParams,
						params: options.params ?? EMPTY_PARAMS
					});
					const { dynamicUsedInHandler, response } = await runAppRouteHandler({
						basePath: options.basePath,
						consumeDynamicUsage: options.consumeDynamicUsage,
						dynamicConfig: options.dynamicConfig,
						handlerFn: options.handlerFn,
						i18n: options.i18n,
						trailingSlash: options.trailingSlash,
						markDynamicUsage: options.markDynamicUsage,
						params: options.params === null ? null : makeThenableParams(options.params),
						request: new Request(options.requestUrl, { method: "GET" }),
						routePattern: options.routePattern,
						setHeadersAccessPhase: options.setHeadersAccessPhase
					});
					options.setNavigationContext(null);
					assertSupportedAppRouteHandlerResponse(response);
					if (dynamicUsedInHandler) {
						markKnownDynamicAppRoute(options.routePattern);
						options.isrDebug?.("route regen skipped (dynamic usage)", options.cleanPathname);
						return;
					}
					const routeTags = options.buildPageCacheTags(options.cleanPathname, options.getCollectedFetchTags());
					const routeCacheValue = await buildAppRouteCacheValue(response);
					await options.isrSet(routeKey, routeCacheValue, {
						cacheControl: isrCacheControl(options.revalidateSeconds, { expireSeconds: options.expireSeconds }),
						tags: routeTags
					});
					options.isrDebug?.("route regen complete", routeKey);
				});
			});
			options.isrDebug?.("STALE (route)", options.cleanPathname);
			options.clearRequestContext();
			return applyRouteHandlerMiddlewareContext(buildRouteHandlerCachedResponse(staleValue, {
				cacheState: "STALE",
				cacheControl: cached.value.cacheControl,
				expireSeconds: options.expireSeconds,
				isHead: options.isAutoHead,
				revalidateSeconds: options.revalidateSeconds
			}), options.middlewareContext);
		}
	} catch (routeCacheError) {
		console.error("[vinext] ISR route cache read error:", routeCacheError);
	}
	return null;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-route-handler-dispatch.js
function isAppRouteHandlerFunction(value) {
	return typeof value === "function";
}
function buildRouteHandlerPageCacheTags(pathname, extraTags, routeSegments) {
	return buildPageCacheTags(pathname, extraTags, routeSegments, "route");
}
async function runInRouteHandlerRevalidationContext(options, renderFn) {
	const requestContext = createRequestContext({
		headersContext: createStaticGenerationHeadersContext({
			draftModeEnabled: false,
			draftModeSecret: options.draftModeSecret,
			dynamicConfig: options.dynamicConfig,
			routeKind: "route",
			routePattern: options.routePattern
		}),
		executionContext: getRequestExecutionContext(),
		unstableCacheRevalidation: "foreground"
	});
	const revalidation = runWithRequestContext(requestContext, async () => {
		ensureFetchPatch();
		setCurrentFetchSoftTags(buildRouteHandlerPageCacheTags(options.cleanPathname, [], options.routeSegments));
		setCurrentFetchCacheMode(options.fetchCacheMode);
		setCurrentForceDynamicFetchDefault(options.dynamicConfig === "force-dynamic");
		try {
			await renderFn();
		} finally {
			await _drainPendingRevalidations();
		}
	});
	try {
		await revalidation;
	} finally {
		await closeAfterResponse(requestContext);
	}
}
async function dispatchAppRouteHandler(options) {
	const { route } = options;
	const handler = route.routeHandler;
	const method = options.request.method.toUpperCase();
	const revalidateSeconds = getAppRouteHandlerRevalidateSeconds(handler);
	const isDevelopment = options.isDevelopment ?? false;
	const isProduction = options.isProduction ?? true;
	const isDraftMode = getActiveDraftModeState() ?? isDraftModeRequest(options.request, options.draftModeSecret);
	const initialDraftModeCookie = getDraftModeCookieHeader();
	const hasDraftModeTransition = initialDraftModeCookie != null;
	const finalizeFrameworkResponse = (response, isHead = false) => {
		const finalized = finalizeRouteHandlerResponse(response, {
			pendingCookies: getAndClearPendingCookies(),
			draftCookie: initialDraftModeCookie,
			isHead
		});
		options.clearRequestContext();
		return applyDraftModeCachePolicy(applyRouteHandlerMiddlewareContext(finalized, options.middlewareContext), isDraftMode || hasDraftModeTransition);
	};
	if (hasAppRouteHandlerDefaultExport(handler) && isDevelopment) console.error("[vinext] Detected default export in route handler " + route.pattern + ". Export a named export for each HTTP method instead.");
	if (!isValidHTTPMethod(method)) return finalizeFrameworkResponse(new Response(null, { status: 400 }));
	const { allowHeaderForOptions, handlerFn, isAutoHead, shouldAutoRespondToOptions } = resolveAppRouteHandlerMethod(handler, method);
	if (shouldAutoRespondToOptions) return finalizeFrameworkResponse(new Response(null, {
		status: 204,
		headers: { Allow: allowHeaderForOptions }
	}));
	const resolvedHandlerFn = isAppRouteHandlerFunction(handlerFn) ? handlerFn : void 0;
	const fetchCacheMode = resolveAppRouteHandlerFetchCacheMode(handler);
	setCurrentFetchCacheMode(fetchCacheMode);
	setCurrentForceDynamicFetchDefault(handler.dynamic === "force-dynamic");
	if (revalidateSeconds !== null && shouldReadAppRouteHandlerCache({
		dynamicConfig: handler.dynamic,
		handlerFn: resolvedHandlerFn,
		isAutoHead,
		isKnownDynamic: isKnownDynamicAppRoute(route.pattern),
		isDraftMode: isDraftMode || hasDraftModeTransition,
		isProduction,
		method,
		revalidateSeconds
	}) && resolvedHandlerFn) {
		const cachedRouteResponse = await readAppRouteHandlerCacheResponse({
			basePath: options.basePath,
			buildPageCacheTags(pathname, extraTags) {
				return buildRouteHandlerPageCacheTags(pathname, extraTags, route.routeSegments);
			},
			cleanPathname: options.cleanPathname,
			clearRequestContext: options.clearRequestContext,
			consumeDynamicUsage,
			dynamicConfig: handler.dynamic,
			getCollectedFetchTags,
			handlerFn: resolvedHandlerFn,
			i18n: options.i18n,
			trailingSlash: options.trailingSlash,
			isAutoHead,
			isrDebug: options.isrDebug,
			isrGet: options.isrGet,
			isrRouteKey: options.isrRouteKey,
			isrSet: options.isrSet,
			markDynamicUsage,
			middlewareContext: options.middlewareContext,
			params: options.params,
			requestUrl: options.request.url,
			revalidateSearchParams: options.searchParams,
			expireSeconds: options.expireSeconds,
			revalidateSeconds,
			routePattern: route.pattern,
			runInRevalidationContext(renderFn) {
				return runInRouteHandlerRevalidationContext({
					cleanPathname: options.cleanPathname,
					draftModeSecret: options.draftModeSecret,
					dynamicConfig: handler.dynamic,
					fetchCacheMode,
					routePattern: route.pattern,
					routeSegments: route.routeSegments
				}, renderFn);
			},
			scheduleBackgroundRegeneration(key, renderFn) {
				options.scheduleBackgroundRegeneration(key, renderFn, {
					routerKind: "App Router",
					routePath: route.pattern,
					routeType: "route"
				});
			},
			setHeadersAccessPhase,
			setNavigationContext
		});
		if (cachedRouteResponse) return cachedRouteResponse;
	}
	if (resolvedHandlerFn) return executeAppRouteHandler({
		basePath: options.basePath,
		buildPageCacheTags(pathname, extraTags) {
			return buildRouteHandlerPageCacheTags(pathname, extraTags, route.routeSegments);
		},
		cleanPathname: options.cleanPathname,
		clearRequestContext: options.clearRequestContext,
		consumeDynamicUsage,
		draftModeSecret: options.draftModeSecret,
		executionContext: getRequestExecutionContext(),
		getAndClearPendingCookies,
		getCollectedFetchTags,
		getActiveDraftModeState,
		getDraftModeCookieHeader,
		handler,
		handlerFn: resolvedHandlerFn,
		i18n: options.i18n,
		trailingSlash: options.trailingSlash,
		isAutoHead,
		initialDraftModeCookie,
		isDraftMode,
		isProduction,
		isrDebug: options.isrDebug,
		isrRouteKey: options.isrRouteKey,
		isrSet: options.isrSet,
		markDynamicUsage,
		method,
		middlewareContext: options.middlewareContext,
		middlewareRequestHeaders: options.middlewareRequestHeaders,
		params: options.params === null ? null : makeThenableParams(options.params),
		reportRequestError(error, request, context) {
			reportRequestError(error, request, context);
		},
		request: options.request,
		expireSeconds: options.expireSeconds,
		revalidateSeconds,
		routePattern: route.pattern,
		setHeadersAccessPhase
	});
	return finalizeFrameworkResponse(new Response(null, { status: 405 }));
}
//#endregion
export { dispatchAppRouteHandler };
