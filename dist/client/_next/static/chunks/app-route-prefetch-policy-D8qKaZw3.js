import { n as matchRouteWithTrie, r as stripBasePath, t as createRouteTrieCache } from "./index-Ix_szaz_.js";
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/internal/app-route-prefetch-policy.js
/** basePath from next.config.js, injected by the plugin at build time */
var __basePath = "";
var linkPrefetchRouteTrieCache = createRouteTrieCache();
function toSameOriginRouteHref(href) {
	let url;
	try {
		url = new URL(href, window.location.href);
	} catch {
		return null;
	}
	if (url.origin !== window.location.origin) return null;
	return `${stripBasePath(url.pathname, __basePath)}${url.search}`;
}
/** Href the manifest does not cover: no request, nothing reusable. */
var NO_APP_ROUTE_PREFETCH = {
	cacheForNavigation: false,
	fallbackTtl: "static",
	honorDynamicStaleTime: true,
	prefetchShellFirst: false,
	shouldPrefetch: false
};
function resolveAutoAppRoutePrefetch(href) {
	const routes = window.__VINEXT_LINK_PREFETCH_ROUTES__;
	if (!routes) return NO_APP_ROUTE_PREFETCH;
	const routeHref = toSameOriginRouteHref(href);
	if (routeHref === null) return NO_APP_ROUTE_PREFETCH;
	const match = matchRouteWithTrie(routeHref, routes, linkPrefetchRouteTrieCache);
	if (!match) return NO_APP_ROUTE_PREFETCH;
	const route = match.route;
	const hasSearchParams = new URL(routeHref, "http://vinext.local").search !== "";
	return {
		cacheForNavigation: !hasSearchParams && !route.canPrefetchLoadingShell && route.requiresDynamicNavigationRequest !== true,
		fallbackTtl: "static",
		honorDynamicStaleTime: true,
		prefetchShellFirst: hasSearchParams || !route.isDynamic,
		shouldPrefetch: true
	};
}
function resolveFullAppRoutePrefetch() {
	return {
		cacheForNavigation: true,
		fallbackTtl: "static",
		honorDynamicStaleTime: false,
		prefetchShellFirst: true,
		shouldPrefetch: true
	};
}
//#endregion
export { resolveAutoAppRoutePrefetch, resolveFullAppRoutePrefetch };
