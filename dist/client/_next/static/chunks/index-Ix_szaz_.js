const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["_next/static/chunks/home-client-zukx_Gw-.js","_next/static/chunks/rolldown-runtime-DFEGrk7x.js","_next/static/chunks/bridge-url-BGLefqYS.js","_next/static/chunks/framework-BiZY8KgM.js","_next/static/chunks/activity-CIQ0-S25.js","_next/static/chunks/harness-output-CHMDwSlK.js","_next/static/chunks/layout-segment-context-D_56FSh-.js","_next/static/chunks/chat-client-DVoAPlt2.js","_next/static/chunks/circle-check-GbKYDpNs.js","_next/static/chunks/streamed-icons-C6b-hnDa.js","_next/static/chunks/desktop-runtime-shell-wr2eh9Il.js"])))=>i.map(i=>d[i]);
import { n as __exportAll, r as __toESM, t as __commonJSMin } from "./rolldown-runtime-DFEGrk7x.js";
import { i as require_react, n as require_react_dom, r as require_jsx_runtime, t as require_client } from "./framework-BiZY8KgM.js";
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/client/react-instance.js
var VINEXT_CLIENT_REACT = Symbol.for("vinext.client.react");
/**
* Return the React instance registered by the vinext browser entry.
*
* Module Federation remotes can call this with their local React namespace to
* reuse the host instance. The first browser registration wins so evaluating
* another copy of this module (for example after HMR) cannot replace it.
* Server and RSC environments always keep their condition-specific React
* instance local.
*/
function getVinextReact(reactInstance) {
	const registeredReact = Reflect.get(globalThis, VINEXT_CLIENT_REACT);
	if (registeredReact !== void 0) return registeredReact;
	Reflect.set(globalThis, VINEXT_CLIENT_REACT, reactInstance);
	return reactInstance;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/client/react-instance-bootstrap.js
var import_react = /* @__PURE__ */ __toESM(require_react(), 1);
getVinextReact(import_react);
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/record.js
function isUnknownRecord(value) {
	return value !== null && typeof value === "object" && !Array.isArray(value);
}
var NAVIGATION_RUNTIME_KEY = Symbol.for("vinext.navigationRuntime");
var ROUTE_MANIFEST_SEGMENT_GRAPH_MAP_KEYS = [
	"boundaries",
	"defaults",
	"interceptions",
	"interceptionsBySlotId",
	"layouts",
	"pages",
	"rootBoundaries",
	"routeHandlers",
	"routes",
	"slotBindings",
	"slots",
	"templates"
];
function createNavigationRuntime() {
	return {
		bootstrap: {
			routeManifest: null,
			rsc: void 0
		},
		functions: {}
	};
}
function readRuntimeWindow() {
	return window;
}
function isNavigationRuntimeFunctions(value) {
	if (!isUnknownRecord(value)) return false;
	return isOptionalRuntimeFunction(Reflect.get(value, "clearNavigationCaches")) && isOptionalRuntimeFunction(Reflect.get(value, "commitHashNavigation")) && isOptionalRuntimeFunction(Reflect.get(value, "navigateExternal")) && isOptionalRuntimeFunction(Reflect.get(value, "navigate")) && isOptionalRuntimeFunction(Reflect.get(value, "getPrefetchRouterState")) && isOptionalRuntimeFunction(Reflect.get(value, "notifyLinkNavigationStart")) && isOptionalRuntimeFunction(Reflect.get(value, "pingVisibleLinks")) && isOptionalRuntimeFunction(Reflect.get(value, "preparePrefetchResponse"));
}
function isNavigationRuntimeRscChunk(value) {
	if (typeof value === "string") return true;
	return Array.isArray(value) && value.length === 2 && value[0] === 3 && typeof value[1] === "string";
}
function isNavigationRuntimeSnapshot(value) {
	if (!isUnknownRecord(value)) return false;
	const pathname = Reflect.get(value, "pathname");
	const searchParams = Reflect.get(value, "searchParams");
	return typeof pathname === "string" && Array.isArray(searchParams) && searchParams.every((entry) => Array.isArray(entry) && entry.length === 2 && typeof entry[0] === "string" && typeof entry[1] === "string");
}
function isNavigationRuntimeParams(value) {
	if (!isUnknownRecord(value)) return false;
	return Object.values(value).every((entry) => typeof entry === "string" || Array.isArray(entry) && entry.every((part) => typeof part === "string"));
}
function isNavigationRuntimeRscBootstrap(value) {
	if (!isUnknownRecord(value)) return false;
	const done = Reflect.get(value, "done");
	const dynamicStaleTimeSeconds = Reflect.get(value, "dynamicStaleTimeSeconds");
	const initialCacheKind = Reflect.get(value, "initialCacheKind");
	const nav = Reflect.get(value, "nav");
	const params = Reflect.get(value, "params");
	const rsc = Reflect.get(value, "rsc");
	const staleTimeSeconds = Reflect.get(value, "staleTimeSeconds");
	return (done === void 0 || typeof done === "boolean") && isOptionalStaleTimeSeconds(dynamicStaleTimeSeconds) && (initialCacheKind === void 0 || initialCacheKind === "dynamic" || initialCacheKind === "static") && (nav === void 0 || isNavigationRuntimeSnapshot(nav)) && (params === void 0 || isNavigationRuntimeParams(params)) && Array.isArray(rsc) && rsc.every(isNavigationRuntimeRscChunk) && isOptionalStaleTimeSeconds(staleTimeSeconds);
}
function isOptionalStaleTimeSeconds(value) {
	return value === void 0 || typeof value === "number" && Number.isFinite(value) && value >= 0;
}
function isReadonlyStringArray(value) {
	return Array.isArray(value) && value.every((entry) => typeof entry === "string");
}
function isNullableString(value) {
	return value === null || typeof value === "string";
}
function isNavigationRuntimeInterception(value) {
	if (!isUnknownRecord(value)) return false;
	return typeof value.id === "string" && typeof value.sourcePattern === "string" && isReadonlyStringArray(value.sourcePatternParts) && typeof value.targetPattern === "string" && isReadonlyStringArray(value.targetPatternParts) && typeof value.slotId === "string" && isNullableString(value.ownerLayoutId) && isNullableString(value.interceptingRouteId) && isNullableString(value.targetRouteId);
}
function isNavigationRuntimeInterceptionArray(value) {
	return Array.isArray(value) && value.every(isNavigationRuntimeInterception);
}
function isNavigationRuntimeRouteManifest(value) {
	if (!isUnknownRecord(value)) return false;
	const graphVersion = Reflect.get(value, "graphVersion");
	const segmentGraph = Reflect.get(value, "segmentGraph");
	if (typeof graphVersion !== "string" || !isUnknownRecord(segmentGraph)) return false;
	const interceptions = Reflect.get(segmentGraph, "interceptions");
	const interceptionsBySlotId = Reflect.get(segmentGraph, "interceptionsBySlotId");
	if (!ROUTE_MANIFEST_SEGMENT_GRAPH_MAP_KEYS.every((key) => Reflect.get(segmentGraph, key) instanceof Map) || !(interceptions instanceof Map) || !(interceptionsBySlotId instanceof Map)) return false;
	for (const interception of interceptions.values()) if (!isNavigationRuntimeInterception(interception)) return false;
	for (const slotInterceptions of interceptionsBySlotId.values()) if (!isNavigationRuntimeInterceptionArray(slotInterceptions)) return false;
	return true;
}
function isNavigationRuntimeBootstrap(value) {
	if (!isUnknownRecord(value)) return false;
	const routeManifest = Reflect.get(value, "routeManifest");
	const rsc = Reflect.get(value, "rsc");
	return (routeManifest === null || isNavigationRuntimeRouteManifest(routeManifest)) && (rsc === void 0 || isNavigationRuntimeRscBootstrap(rsc));
}
function isNavigationRuntime(value) {
	if (!isUnknownRecord(value)) return false;
	if (!("bootstrap" in value) || !("functions" in value)) return false;
	const { bootstrap, functions } = value;
	return isNavigationRuntimeBootstrap(bootstrap) && isNavigationRuntimeFunctions(functions);
}
function isOptionalRuntimeFunction(value) {
	return value === void 0 || typeof value === "function";
}
function getNavigationRuntime() {
	const runtimeWindow = readRuntimeWindow();
	if (runtimeWindow === null) return null;
	const runtime = Reflect.get(runtimeWindow, NAVIGATION_RUNTIME_KEY);
	return isNavigationRuntime(runtime) ? runtime : null;
}
/**
* Returns the registered browser runtime, creating it when a window exists.
* Without a window, callers receive a detached runtime and must retain the
* returned reference themselves; server calls are intentionally not global.
*/
function ensureNavigationRuntime() {
	const runtimeWindow = readRuntimeWindow();
	if (runtimeWindow === null) return createNavigationRuntime();
	const existingRuntime = Reflect.get(runtimeWindow, NAVIGATION_RUNTIME_KEY);
	const runtime = isNavigationRuntime(existingRuntime) ? existingRuntime : createNavigationRuntime();
	Reflect.set(runtimeWindow, NAVIGATION_RUNTIME_KEY, runtime);
	return runtime;
}
function registerNavigationRuntimeBootstrap(bootstrap) {
	const runtime = ensureNavigationRuntime();
	runtime.bootstrap = {
		...runtime.bootstrap,
		...bootstrap
	};
	return runtime;
}
function registerNavigationRuntimeFunctions(functions) {
	const runtime = ensureNavigationRuntime();
	runtime.functions = {
		...runtime.functions,
		...functions
	};
	return runtime;
}
function ensureNavigationRuntimeRscBootstrap() {
	return ensureNavigationRuntimeRscBootstrapForRuntime(ensureNavigationRuntime());
}
function ensureNavigationRuntimeRscBootstrapForRuntime(runtime) {
	const rscBootstrap = runtime.bootstrap.rsc;
	if (rscBootstrap === void 0) {
		const nextRscBootstrap = { rsc: [] };
		runtime.bootstrap.rsc = nextRscBootstrap;
		return nextRscBootstrap;
	}
	return rscBootstrap;
}
function hasAppNavigationRuntime() {
	return typeof getNavigationRuntime()?.functions.navigate === "function";
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/headers.js
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
var NEXT_ROUTER_STATE_TREE_HEADER = "Next-Router-State-Tree";
var NEXT_ROUTER_PREFETCH_HEADER = "Next-Router-Prefetch";
var NEXT_ROUTER_SEGMENT_PREFETCH_HEADER = "Next-Router-Segment-Prefetch";
var NEXT_URL_HEADER = "Next-Url";
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
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/compare.js
var compareStrings = (left, right) => {
	if (left < right) return -1;
	if (left > right) return 1;
	return 0;
};
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
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-render-dependency.js
var import_jsx_runtime = require_jsx_runtime();
var appElementRenderDependencies = /* @__PURE__ */ new WeakMap();
function releaseAppElementRenderDependency(elements, elementId) {
	appElementRenderDependencies.get(elements)?.get(elementId)?.release();
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
	if ((0, import_react.isValidElement)(value)) return false;
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
function readAppElementsMetadata$1(elements) {
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
	readMetadata: readAppElementsMetadata$1,
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
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-elements.js
function getMountedSlotIds(elements) {
	return Object.keys(elements).filter((key) => {
		const value = elements[key];
		const parsed = AppElementsWire.parseElementKey(key);
		return parsed?.kind === "slot" && parsed.name !== "children" && value !== null && value !== void 0 && value !== UNMATCHED_SLOT;
	}).sort();
}
function getMountedSlotIdsHeader(elements) {
	return normalizeMountedSlotsHeader(getMountedSlotIds(elements).join(" "));
}
function resolveVisitedResponseInterceptionContext(requestInterceptionContext, payloadInterceptionContext) {
	return payloadInterceptionContext ?? requestInterceptionContext;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/internal/app-router-context.js
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
	if (typeof import_react.createContext !== "function") return null;
	const globalState = globalThis;
	if (!globalState[key]) globalState[key] = import_react.createContext(defaultValue);
	return globalState[key] ?? null;
}
var AppRouterContext = getOrCreateContext(APP_ROUTER_CONTEXT_KEY, null);
getOrCreateContext(GLOBAL_LAYOUT_ROUTER_CONTEXT_KEY, null);
getOrCreateContext(LAYOUT_ROUTER_CONTEXT_KEY, null);
getOrCreateContext(MISSING_SLOT_CONTEXT_KEY, /* @__PURE__ */ new Set());
getOrCreateContext(TEMPLATE_CONTEXT_KEY, null);
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/client/window-next.js
/**
* Build-time replacement for the vinext package version, injected by the
* Vite plugin via `define` (see `index.ts` — `process.env.__NEXT_VERSION`
* is mirrored from `packages/vinext/package.json#version` so library
* callers that read `process.env.__NEXT_VERSION` see a real value).
*
* In environments where the define did not run (standalone unit tests
* that import this module without going through the plugin), the
* `?? "vinext"` fallback prevents a literal `undefined` from landing on
* `window.next.version`.
*/
var VINEXT_VERSION = "1.0.0-beta.5";
/**
* Install `window.next` if it has not already been installed in this
* document. Subsequent calls update fields in place so both the Pages
* Router and the App Router bootstraps can call this without clobbering
* each other (e.g. for hybrid `pages/` + `app/` setups).
*
* When called a second time, `router` and `appDir` overwrite the previous
* values. This mirrors Next.js's load order: in a hybrid app the App
* Router's `app-bootstrap.ts` runs after Pages Router's `next.ts` and the
* App Router instance wins.
*
* No module-level cache: we read and write through `window.next` directly
* so that a test (or userland code) that deletes `window.next` cleanly
* resets state.
*/
function installWindowNext(fields) {
	const existing = window.next;
	if (existing) {
		if (fields.version !== void 0) existing.version = fields.version;
		if (fields.appDir !== void 0) existing.appDir = fields.appDir;
		if (fields.router !== void 0) existing.router = fields.router;
		if (fields.__pendingUrl !== void 0) existing.__pendingUrl = fields.__pendingUrl;
		if (fields.__internal_src_page !== void 0) existing.__internal_src_page = fields.__internal_src_page;
		return;
	}
	window.next = {
		version: fields.version ?? VINEXT_VERSION,
		...fields
	};
}
function setWindowNextInternalSourcePage(sourcePage) {
	installWindowNext({});
	if (sourcePage === null) {
		delete window.next?.__internal_src_page;
		return;
	}
	const next = window.next;
	if (!next) return;
	next.__internal_src_page = sourcePage;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/hash-scroll.js
function decodeHashFragment(fragment) {
	try {
		return decodeURIComponent(fragment);
	} catch {
		return fragment;
	}
}
function scrollToHashTarget(hash) {
	const fragment = decodeHashFragment(hash.startsWith("#") ? hash.slice(1) : hash);
	if (fragment === "" || fragment === "top") {
		window.scrollTo(0, 0);
		return;
	}
	const idElement = document.getElementById(fragment);
	if (idElement) {
		idElement.scrollIntoView({ behavior: "auto" });
		return;
	}
	const namedElement = document.getElementsByName(fragment)[0];
	if (namedElement) {
		namedElement.scrollIntoView({ behavior: "auto" });
		return;
	}
	window.scrollTo(0, 0);
}
function scrollToHashTargetOnNextFrame(hash, shouldScroll) {
	requestAnimationFrame(() => {
		if (shouldScroll && !shouldScroll()) return;
		scrollToHashTarget(hash);
	});
}
function retryScrollTo(x, y, opts) {
	const minFrames = opts?.minFrames ?? 0;
	const shouldContinue = opts?.shouldContinue ?? (() => true);
	let attempts = 0;
	const restore = () => {
		if (!shouldContinue()) return;
		window.scrollTo(x, y);
		const reachedTarget = Math.abs(window.scrollY - y) <= 1;
		if (!shouldContinue() || reachedTarget && attempts >= minFrames || attempts >= 60) return;
		attempts += 1;
		requestAnimationFrame(restore);
	};
	restore();
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/navigation-context-state.js
var LAYOUT_SEGMENT_CONTEXT_KEY = Symbol.for("vinext.layoutSegmentContext");
var SERVER_INSERTED_HTML_CONTEXT_KEY = Symbol.for("vinext.serverInsertedHTMLContext");
var BFCACHE_ID_MAP_CONTEXT_KEY = Symbol.for("vinext.bfcacheIdMapContext");
var BFCACHE_SEGMENT_ID_CONTEXT_KEY = Symbol.for("vinext.bfcacheSegmentIdContext");
var GLOBAL_HYDRATION_CONTEXT_KEY = Symbol.for("vinext.navigation.clientHydrationContext");
var NAVIGATION_FALLBACK_STATE_KEY = Symbol.for("vinext.navigation.fallback");
function createContextIfAvailable(defaultValue) {
	return typeof import_react.createContext === "function" ? import_react.createContext(defaultValue) : null;
}
function getServerInsertedHTMLContext() {
	const globalState = globalThis;
	if (!globalState[SERVER_INSERTED_HTML_CONTEXT_KEY]) globalState[SERVER_INSERTED_HTML_CONTEXT_KEY] = createContextIfAvailable(null);
	return globalState[SERVER_INSERTED_HTML_CONTEXT_KEY] ?? null;
}
getServerInsertedHTMLContext();
function getLayoutSegmentContext() {
	const globalState = globalThis;
	if (!globalState[LAYOUT_SEGMENT_CONTEXT_KEY]) globalState[LAYOUT_SEGMENT_CONTEXT_KEY] = createContextIfAvailable({ children: [] });
	return globalState[LAYOUT_SEGMENT_CONTEXT_KEY] ?? null;
}
function getBfcacheIdMapContext() {
	const globalState = globalThis;
	if (!globalState[BFCACHE_ID_MAP_CONTEXT_KEY]) globalState[BFCACHE_ID_MAP_CONTEXT_KEY] = createContextIfAvailable(null);
	return globalState[BFCACHE_ID_MAP_CONTEXT_KEY] ?? null;
}
function getBfcacheSegmentIdContext() {
	const globalState = globalThis;
	if (!globalState[BFCACHE_SEGMENT_ID_CONTEXT_KEY]) globalState[BFCACHE_SEGMENT_ID_CONTEXT_KEY] = createContextIfAvailable(null);
	return globalState[BFCACHE_SEGMENT_ID_CONTEXT_KEY] ?? null;
}
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
function getClientHydrationContext() {
	const globalState = globalThis;
	if (Object.prototype.hasOwnProperty.call(globalState, GLOBAL_HYDRATION_CONTEXT_KEY)) return globalState[GLOBAL_HYDRATION_CONTEXT_KEY] ?? null;
}
function setClientHydrationContext(context) {
	globalThis[GLOBAL_HYDRATION_CONTEXT_KEY] = context;
}
function clearClientHydrationContext() {
	setClientHydrationContext(null);
}
var getServerContext = () => {
	{
		const hydrationContext = getClientHydrationContext();
		return hydrationContext !== void 0 ? hydrationContext : getFallbackState().serverContext;
	}
	return getGlobalAccessors()?.getServerContext() ?? getFallbackState().serverContext;
};
var setServerContext = (context) => {
	getFallbackState().serverContext = context;
	setClientHydrationContext(context);
};
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
/**
* Server-safe navigation control-flow errors and predicates.
*
* This module intentionally has no React or browser-runtime dependencies so
* RSC, SSR, and the public next/navigation shim can share one implementation.
*/
var HTTP_ERROR_FALLBACK_ERROR_CODE = "NEXT_HTTP_ERROR_FALLBACK";
var VinextNavigationError = class extends Error {
	digest;
	constructor(message, digest) {
		super(message);
		this.digest = digest;
	}
};
function notFound() {
	throw new VinextNavigationError("NEXT_NOT_FOUND", `${HTTP_ERROR_FALLBACK_ERROR_CODE};404`);
}
/**
* vinext accepts its three-part redirect digest and Next.js's five-part form.
* This is deliberately only a cheap prefix gate because vinext permits an
* empty redirect type; parseRedirectDigest is the authoritative validator.
*/
function isRedirectError(error) {
	return !!error && typeof error === "object" && "digest" in error && typeof error.digest === "string" && error.digest.startsWith("NEXT_REDIRECT;");
}
function decodeRedirectError(digest) {
	const redirect = parseRedirectDigest(digest);
	if (!redirect) return null;
	return {
		url: redirect.url,
		type: redirect.type === "push" ? "push" : "replace"
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/default-global-error.js
var default_global_error_exports = /* @__PURE__ */ __exportAll({ default: () => DefaultGlobalError });
var errorStyles = {
	container: {
		fontFamily: "system-ui,\"Segoe UI\",Roboto,Helvetica,Arial,sans-serif,\"Apple Color Emoji\",\"Segoe UI Emoji\"",
		height: "100vh",
		display: "flex",
		alignItems: "center",
		justifyContent: "center"
	},
	card: {
		marginTop: "-32px",
		maxWidth: "325px",
		padding: "32px 28px",
		textAlign: "left"
	},
	icon: { marginBottom: "24px" },
	title: {
		fontSize: "24px",
		fontWeight: 500,
		letterSpacing: "-0.02em",
		lineHeight: "32px",
		margin: "0 0 12px 0",
		color: "var(--next-error-title)"
	},
	message: {
		fontSize: "14px",
		fontWeight: 400,
		lineHeight: "21px",
		margin: "0 0 20px 0",
		color: "var(--next-error-message)"
	},
	form: { margin: 0 },
	buttonGroup: {
		display: "flex",
		gap: "8px",
		alignItems: "center"
	},
	button: {
		display: "inline-flex",
		alignItems: "center",
		justifyContent: "center",
		height: "32px",
		padding: "0 12px",
		fontSize: "14px",
		fontWeight: 500,
		lineHeight: "20px",
		borderRadius: "6px",
		cursor: "pointer",
		color: "var(--next-error-btn-text)",
		background: "var(--next-error-btn-bg)",
		border: "var(--next-error-btn-border)"
	},
	buttonSecondary: {
		display: "inline-flex",
		alignItems: "center",
		justifyContent: "center",
		height: "32px",
		padding: "0 12px",
		fontSize: "14px",
		fontWeight: 500,
		lineHeight: "20px",
		borderRadius: "6px",
		cursor: "pointer",
		color: "var(--next-error-btn-secondary-text)",
		background: "var(--next-error-btn-secondary-bg)",
		border: "var(--next-error-btn-secondary-border)"
	},
	digestFooter: {
		position: "fixed",
		bottom: "32px",
		left: "0",
		right: "0",
		textAlign: "center",
		fontFamily: "ui-monospace,SFMono-Regular,\"SF Mono\",Menlo,Consolas,monospace",
		fontSize: "12px",
		lineHeight: "18px",
		fontWeight: 400,
		margin: "0",
		color: "var(--next-error-digest)"
	}
};
var errorThemeCss = `
:root {
  --next-error-bg: #fff;
  --next-error-text: #171717;
  --next-error-title: #171717;
  --next-error-message: #171717;
  --next-error-digest: #666666;
  --next-error-btn-text: #fff;
  --next-error-btn-bg: #171717;
  --next-error-btn-border: none;
  --next-error-btn-secondary-text: #171717;
  --next-error-btn-secondary-bg: transparent;
  --next-error-btn-secondary-border: 1px solid rgba(0,0,0,0.08);
}
@media (prefers-color-scheme: dark) {
  :root {
    --next-error-bg: #0a0a0a;
    --next-error-text: #ededed;
    --next-error-title: #ededed;
    --next-error-message: #ededed;
    --next-error-digest: #a0a0a0;
    --next-error-btn-text: #0a0a0a;
    --next-error-btn-bg: #ededed;
    --next-error-btn-border: none;
    --next-error-btn-secondary-text: #ededed;
    --next-error-btn-secondary-bg: transparent;
    --next-error-btn-secondary-border: 1px solid rgba(255,255,255,0.14);
  }
}
body { margin: 0; color: var(--next-error-text); background: var(--next-error-bg); }
`.replace(/\n\s*/g, "");
function WarningIcon() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("svg", {
		width: "32",
		height: "32",
		viewBox: "-0.2 -1.5 32 32",
		fill: "none",
		style: errorStyles.icon,
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("path", {
			d: "M16.9328 0C18.0839 0.000116771 19.1334 0.658832 19.634 1.69531L31.4299 26.1309C32.0708 27.4588 31.1036 28.9999 29.6291 29H2.00215C0.527541 29 -0.439628 27.4588 0.201371 26.1309L11.9973 1.69531C12.4979 0.658823 13.5474 7.75066e-05 14.6984 0H16.9328ZM3.59493 26H28.0363L16.9328 3H14.6984L3.59493 26ZM15.8156 19C16.9202 19.0001 17.8156 19.8955 17.8156 21C17.8156 22.1045 16.9202 22.9999 15.8156 23C14.7111 23 13.8156 22.1046 13.8156 21C13.8156 19.8954 14.7111 19 15.8156 19ZM17.3156 16.5H14.3156V8.5H17.3156V16.5Z",
			fill: "var(--next-error-title)"
		})
	});
}
function handleBackClick() {
	if (window.history.length > 1) window.history.back();
	else window.location.href = "/";
}
function DefaultGlobalError({ error }) {
	const digest = error?.digest;
	const isServerError = !!digest;
	const message = isServerError ? "A server error occurred. Reload to try again." : "Reload to try again, or go back.";
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("html", {
		id: "__next_error__",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("head", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("style", { dangerouslySetInnerHTML: { __html: errorThemeCss } }) }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("body", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			style: errorStyles.container,
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				style: errorStyles.card,
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(WarningIcon, {}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h1", {
						style: errorStyles.title,
						children: "This page couldn’t load"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						style: errorStyles.message,
						children: message
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						style: errorStyles.buttonGroup,
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("form", {
							style: errorStyles.form,
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
								type: "submit",
								style: errorStyles.button,
								children: "Reload"
							})
						}), !isServerError && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
							type: "button",
							style: errorStyles.buttonSecondary,
							onClick: handleBackClick,
							children: "Back"
						})]
					})
				]
			})
		}), digest && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
			style: errorStyles.digestFooter,
			children: ["ERROR ", digest]
		})] })]
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/client/app-nav-failure-handler.js
function getPendingUrl() {
	return window.next?.__pendingUrl ?? null;
}
function getAppNavigationFailureTarget(href) {
	const pendingUrl = getPendingUrl();
	if (pendingUrl === null || false) return null;
	return pendingUrl.href === new URL(href, window.location.href).href ? pendingUrl : null;
}
function clearAppNavigationFailureTarget(target) {
	if (window.next?.__pendingUrl === void 0) return;
	if (target instanceof URL) {
		if (window.next.__pendingUrl !== target) return;
	} else if (target !== void 0 && window.next.__pendingUrl.href !== new URL(target, window.location.href).href) return;
	delete window.next.__pendingUrl;
}
function handleAppNavigationFailure(error) {
	return false;
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
//#endregion
//#region \0vinext:async-hooks-stub
var AsyncLocalStorage = class {
	run(_store, fn, ...args) {
		return fn(...args);
	}
	getStore() {}
	enterWith() {}
	exit(fn, ...args) {
		return fn(...args);
	}
	disable() {}
};
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/internal/als-registry.js
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
var _g = globalThis;
/**
* Every ALS handed out by `getOrCreateAls`, so `runOutsideRequestScopes` can
* exit all of them without an enumeration that goes stale as shims are added.
* Shares the `globalThis` slot for the same cross-module-instance reason.
*/
var _REGISTRY_KEY = Symbol.for("vinext.als.registry");
var _registry = _g[_REGISTRY_KEY] ??= /* @__PURE__ */ new Set();
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
	const als = _g[sym] ??= typeof AsyncLocalStorage === "function" ? new AsyncLocalStorage() : new NoopAsyncLocalStorage();
	_registry.add(als);
	return als;
}
getOrCreateAls("vinext.pprFallbackShell.als");
getOrCreateAls("vinext.pprFallbackShell.cacheTaskStack.als");
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/error-boundary-navigation.js
var CLIENT_NAVIGATION_STATE_KEY = Symbol.for("vinext.clientNavigationState");
var CLIENT_NAVIGATION_RENDER_CONTEXT_KEY = Symbol.for("vinext.clientNavigationRenderContext");
var BASE_PATH = "";
function getClientNavigationState$1() {
	return globalThis[CLIENT_NAVIGATION_STATE_KEY];
}
function getClientPathnameSnapshot() {
	return getClientNavigationState$1()?.cachedPathname ?? stripBasePath(window.location.pathname, BASE_PATH);
}
function getServerPathnameSnapshot() {
	return getNavigationContext()?.pathname ?? "/";
}
function subscribeToCommittedPathname(listener) {
	const state = getClientNavigationState$1();
	if (!state) return () => {};
	state.listeners.add(listener);
	return () => state.listeners.delete(listener);
}
function getClientNavigationRenderContext$1() {
	const globalState = globalThis;
	return globalState[CLIENT_NAVIGATION_RENDER_CONTEXT_KEY] ??= import_react.createContext(null);
}
function useErrorBoundaryPathname() {
	const renderSnapshot = import_react.useContext(getClientNavigationRenderContext$1());
	const committedPathname = import_react.useSyncExternalStore(subscribeToCommittedPathname, getClientPathnameSnapshot, getServerPathnameSnapshot);
	if (renderSnapshot && (getClientNavigationState$1()?.navigationSnapshotActiveCount ?? 0) > 0) return renderSnapshot.pathname;
	return committedPathname;
}
function useErrorBoundaryRouter() {
	if (!AppRouterContext || typeof import_react.useContext !== "function") throw new Error("invariant expected app router to be mounted");
	const router = import_react.useContext(AppRouterContext);
	if (router === null) throw new Error("invariant expected app router to be mounted");
	return router;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/dev-error-recovery-event.js
var VINEXT_DEV_ERROR_RECOVERY_EVENT = "vinext:dev-error-recovery";
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
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/error-boundary.js
var error_boundary_exports = /* @__PURE__ */ __exportAll({
	DevRecoveryBoundary: () => DevRecoveryBoundary,
	ErrorBoundary: () => ErrorBoundary,
	ErrorBoundaryInner: () => ErrorBoundaryInner,
	ForbiddenBoundary: () => ForbiddenBoundary,
	ForbiddenBoundaryInner: () => ForbiddenBoundaryInner,
	GlobalErrorBoundary: () => GlobalErrorBoundary,
	NotFoundBoundary: () => NotFoundBoundary,
	RedirectBoundary: () => RedirectBoundary,
	RedirectErrorBoundary: () => RedirectErrorBoundary,
	SerializedErrorBoundary: () => SerializedErrorBoundary,
	UnauthorizedBoundary: () => UnauthorizedBoundary,
	UnauthorizedBoundaryInner: () => UnauthorizedBoundaryInner
});
function SerializedErrorBoundary({ fallback: Fallback, error }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Fallback, {
		error: Object.assign(new Error(error.message), {
			digest: error.digest,
			name: error.name ?? "Error",
			stack: error.stack
		}),
		reset: () => globalThis.location?.reload()
	});
}
function normalizeBoundaryResetKey(resetKey) {
	return resetKey === void 0 || resetKey === null || resetKey === "" ? null : resetKey;
}
function readBoundaryResetState(props) {
	return {
		previousPathname: props.pathname,
		previousResetKey: normalizeBoundaryResetKey(props.resetKey)
	};
}
function shouldResetBoundary(nextResetState, previousResetState) {
	const nextResetKey = normalizeBoundaryResetKey(nextResetState.previousResetKey);
	const previousResetKey = normalizeBoundaryResetKey(previousResetState.previousResetKey);
	if (nextResetKey !== null || previousResetKey !== null) return nextResetKey !== previousResetKey;
	return nextResetState.previousPathname !== previousResetState.previousPathname;
}
function addDevErrorRecoveryListener(listener) {
	window.addEventListener(VINEXT_DEV_ERROR_RECOVERY_EVENT, listener);
}
function removeDevErrorRecoveryListener(listener) {
	window.removeEventListener(VINEXT_DEV_ERROR_RECOVERY_EVENT, listener);
}
function HandleRedirect({ redirect, redirectType, reset }) {
	const router = useErrorBoundaryRouter();
	import_react.useEffect(() => {
		import_react.startTransition(() => {
			if (redirectType === "push") router.push(redirect);
			else router.replace(redirect);
			reset();
		});
	}, [
		redirect,
		redirectType,
		reset,
		router
	]);
	return null;
}
var RedirectErrorBoundary = class extends import_react.Component {
	constructor(props) {
		super(props);
		this.state = {
			redirect: null,
			redirectType: null
		};
	}
	static getDerivedStateFromError(error) {
		if (isRedirectError(error)) {
			if ("handled" in error && error.handled) return {
				redirect: null,
				redirectType: null
			};
			const result = decodeRedirectError(error.digest);
			if (!result) throw error;
			return {
				redirect: result.url,
				redirectType: result.type
			};
		}
		throw error;
	}
	render() {
		const { redirect, redirectType } = this.state;
		if (redirect !== null && redirectType !== null) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(HandleRedirect, {
			redirect,
			redirectType,
			reset: () => this.setState({
				redirect: null,
				redirectType: null
			})
		});
		return this.props.children;
	}
};
function RedirectBoundary({ children }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(RedirectErrorBoundary, { children });
}
/**
* Generic ErrorBoundary used to wrap route segments with error.tsx.
* This must be a client component since error boundaries use
* componentDidCatch / getDerivedStateFromError.
*/
var ErrorBoundaryInner = class extends import_react.Component {
	constructor(props) {
		super(props);
		this.state = {
			error: null,
			...readBoundaryResetState(props)
		};
	}
	static getDerivedStateFromProps(props, state) {
		const nextResetState = readBoundaryResetState(props);
		if (state.error && handleAppNavigationFailure(state.error.thrownValue)) return {
			error: null,
			...nextResetState
		};
		if (state.error && shouldResetBoundary(nextResetState, state)) return {
			error: null,
			...nextResetState
		};
		return {
			error: state.error,
			...nextResetState
		};
	}
	static getDerivedStateFromError(error) {
		if (isNavigationSignalError(error)) throw error;
		return { error: { thrownValue: error } };
	}
	handleDevErrorRecovery = () => {
		if (!this.state.error) return;
		this.setState({
			error: null,
			...readBoundaryResetState(this.props)
		});
	};
	componentDidMount() {
		addDevErrorRecoveryListener(this.handleDevErrorRecovery);
	}
	componentWillUnmount() {
		removeDevErrorRecoveryListener(this.handleDevErrorRecovery);
	}
	reset = () => {
		this.setState({ error: null });
	};
	render() {
		if (this.state.error) {
			const FallbackComponent = this.props.fallback;
			return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(FallbackComponent, {
				error: this.state.error.thrownValue,
				reset: this.reset
			});
		}
		return this.props.children;
	}
};
function ErrorBoundary({ fallback, children, resetKey }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ErrorBoundaryInner, {
		pathname: useErrorBoundaryPathname(),
		resetKey,
		fallback,
		children
	});
}
function GlobalErrorBoundary({ fallback, children }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ErrorBoundaryInner, {
		pathname: useErrorBoundaryPathname(),
		fallback,
		isImplicitRootErrorBoundary: fallback === DefaultGlobalError,
		children
	});
}
/**
* Inner class component that catches notFound() errors and renders the
* not-found.tsx fallback. Resets on the caller's segment reset key when one is
* provided, otherwise falls back to pathname changes for legacy callers.
*
* The ErrorBoundary above re-throws notFound errors so they propagate up to this
* boundary. This must be placed above the ErrorBoundary in the component tree.
*/
var NotFoundBoundaryInner = class extends import_react.Component {
	constructor(props) {
		super(props);
		this.state = {
			notFound: false,
			...readBoundaryResetState(props)
		};
	}
	static getDerivedStateFromProps(props, state) {
		const nextResetState = readBoundaryResetState(props);
		if (state.notFound && shouldResetBoundary(nextResetState, state)) return {
			notFound: false,
			...nextResetState
		};
		return {
			notFound: state.notFound,
			...nextResetState
		};
	}
	static getDerivedStateFromError(error) {
		if (error && typeof error === "object" && "digest" in error) {
			const digest = String(error.digest);
			if (digest === "NEXT_NOT_FOUND" || digest === "NEXT_HTTP_ERROR_FALLBACK;404") return { notFound: true };
		}
		throw error;
	}
	render() {
		if (this.state.notFound) return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("meta", {
			name: "robots",
			content: "noindex"
		}), this.props.fallback] });
		return this.props.children;
	}
};
/**
* Wrapper that reads the current pathname and passes it to the inner class
* component. Segment reset keys own App Router remount semantics when present.
*/
function NotFoundBoundary({ fallback, children, resetKey }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(NotFoundBoundaryInner, {
		pathname: useErrorBoundaryPathname(),
		resetKey,
		fallback,
		children
	});
}
var ForbiddenBoundaryInner = class extends import_react.Component {
	constructor(props) {
		super(props);
		this.state = {
			forbidden: false,
			...readBoundaryResetState(props)
		};
	}
	static getDerivedStateFromProps(props, state) {
		const nextResetState = readBoundaryResetState(props);
		if (state.forbidden && shouldResetBoundary(nextResetState, state)) return {
			forbidden: false,
			...nextResetState
		};
		return {
			forbidden: state.forbidden,
			...nextResetState
		};
	}
	static getDerivedStateFromError(error) {
		if (error && typeof error === "object" && "digest" in error) {
			if (String(error.digest) === "NEXT_HTTP_ERROR_FALLBACK;403") return { forbidden: true };
		}
		throw error;
	}
	render() {
		if (this.state.forbidden) return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("meta", {
			name: "robots",
			content: "noindex"
		}), this.props.fallback] });
		return this.props.children;
	}
};
function ForbiddenBoundary({ fallback, children, resetKey }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ForbiddenBoundaryInner, {
		pathname: useErrorBoundaryPathname(),
		resetKey,
		fallback,
		children
	});
}
var UnauthorizedBoundaryInner = class extends import_react.Component {
	constructor(props) {
		super(props);
		this.state = {
			unauthorized: false,
			...readBoundaryResetState(props)
		};
	}
	static getDerivedStateFromProps(props, state) {
		const nextResetState = readBoundaryResetState(props);
		if (state.unauthorized && shouldResetBoundary(nextResetState, state)) return {
			unauthorized: false,
			...nextResetState
		};
		return {
			unauthorized: state.unauthorized,
			...nextResetState
		};
	}
	static getDerivedStateFromError(error) {
		if (error && typeof error === "object" && "digest" in error) {
			if (String(error.digest) === "NEXT_HTTP_ERROR_FALLBACK;401") return { unauthorized: true };
		}
		throw error;
	}
	render() {
		if (this.state.unauthorized) return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("meta", {
			name: "robots",
			content: "noindex"
		}), this.props.fallback] });
		return this.props.children;
	}
};
function UnauthorizedBoundary({ fallback, children, resetKey }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(UnauthorizedBoundaryInner, {
		pathname: useErrorBoundaryPathname(),
		resetKey,
		fallback,
		children
	});
}
var DevRecoveryBoundary = class extends import_react.Component {
	constructor(props) {
		super(props);
		this.state = {
			error: null,
			previousResetKey: props.resetKey
		};
	}
	static getDerivedStateFromProps(props, state) {
		if (props.resetKey === state.previousResetKey) return null;
		return {
			error: null,
			previousResetKey: props.resetKey
		};
	}
	static getDerivedStateFromError(error) {
		if (isNavigationSignalError(error)) throw error;
		return { error: { thrownValue: error } };
	}
	handleDevErrorRecovery = () => {
		if (!this.state.error) return;
		this.setState({
			error: null,
			previousResetKey: this.props.resetKey
		});
	};
	componentDidMount() {
		addDevErrorRecoveryListener(this.handleDevErrorRecovery);
	}
	componentWillUnmount() {
		removeDevErrorRecoveryListener(this.handleDevErrorRecovery);
	}
	componentDidCatch() {
		this.props.onCatch?.(this.props.resetKey);
	}
	render() {
		if (this.state.error) return null;
		return this.props.children;
	}
};
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/app-router-scroll-state.js
var _SCROLL_INTENT_KEY = Symbol.for("vinext.appRouterScrollIntent");
function getScrollIntentStore() {
	const globalState = globalThis;
	globalState[_SCROLL_INTENT_KEY] ??= {
		nextId: 0,
		pending: null
	};
	return globalState[_SCROLL_INTENT_KEY];
}
function beginAppRouterScrollIntent(hash) {
	const store = getScrollIntentStore();
	store.nextId += 1;
	const intent = {
		commitId: null,
		hash,
		headElements: typeof document === "undefined" ? null : new Set(document.head?.children ?? []),
		id: store.nextId,
		targetHoistedInHead: false
	};
	store.pending = intent;
	return intent;
}
function clearAppRouterScrollIntent() {
	const store = getScrollIntentStore();
	store.nextId += 1;
	store.pending = null;
}
function getPendingAppRouterScrollIntent() {
	return getScrollIntentStore().pending;
}
function isLatestAppRouterScrollIntent(expected) {
	return expected !== null && expected !== void 0 && getScrollIntentStore().nextId === expected.id;
}
function claimAppRouterScrollIntentForCommit(expected, commitId) {
	const store = getScrollIntentStore();
	const intent = store.pending;
	if (expected === null || expected === void 0 || intent === null) return;
	if (intent.id !== expected.id) return;
	store.pending = {
		...intent,
		commitId
	};
}
function markAppRouterScrollIntentHeadHoisted(expected, commitId) {
	const store = getScrollIntentStore();
	const intent = store.pending;
	if (expected === null || expected === void 0 || intent === null) return;
	if (intent.id !== expected.id) return;
	if (intent.commitId !== commitId) return;
	store.pending = {
		...intent,
		targetHoistedInHead: true
	};
}
function consumeAppRouterScrollIntent(expected, commitId) {
	if (expected === null || expected === void 0) return null;
	const store = getScrollIntentStore();
	const intent = store.pending;
	if (intent === null) return null;
	if (intent.id !== expected.id) return null;
	if (commitId !== void 0 && intent.commitId !== commitId) return null;
	store.pending = null;
	return intent;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/app-router-scroll.js
var app_router_scroll_exports = /* @__PURE__ */ __exportAll({
	AppRouterScrollCommitProvider: () => AppRouterScrollCommitProvider,
	AppRouterScrollTarget: () => AppRouterScrollTarget,
	AppRouterScrollTargetInner: () => AppRouterScrollTargetInner
});
var import_react_dom = /* @__PURE__ */ __toESM(require_react_dom(), 1);
var AppRouterScrollCommitContext = import_react.createContext(null);
var reactDomInternalsKey = "__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE";
var rectProperties = [
	"bottom",
	"height",
	"left",
	"right",
	"top",
	"width",
	"x",
	"y"
];
function readFindDOMNode() {
	const internals = Reflect.get(import_react_dom, reactDomInternalsKey);
	if (typeof internals !== "object" || internals === null) return null;
	const findDOMNode = Reflect.get(internals, "findDOMNode");
	return typeof findDOMNode === "function" ? findDOMNode : null;
}
function findDOMNode(instance) {
	const findDOMNodeImpl = readFindDOMNode();
	if (!findDOMNodeImpl) return null;
	const node = findDOMNodeImpl(instance);
	return node instanceof Element || node instanceof Text ? node : null;
}
function shouldSkipElement(element) {
	const position = getComputedStyle(element).position;
	if (position === "fixed" || position === "sticky") return true;
	const rect = element.getBoundingClientRect();
	return rectProperties.every((property) => rect[property] === 0);
}
function topOfElementInViewport(element, viewportHeight) {
	const rects = element.getClientRects();
	if (rects.length === 0) return false;
	let elementTop = Number.POSITIVE_INFINITY;
	for (const rect of rects) if (rect.top < elementTop) elementTop = rect.top;
	return elementTop >= 0 && elementTop <= viewportHeight;
}
function getHashFragmentDomNode(hash) {
	const fragment = decodeHashFragment(hash.startsWith("#") ? hash.slice(1) : hash);
	if (fragment === "top") return document.body;
	return document.getElementById(fragment) ?? document.getElementsByName(fragment)[0] ?? null;
}
function isInDocumentHead(node) {
	const head = node.ownerDocument?.head;
	return head != null && head.contains(node);
}
function findNextScrollTarget(node) {
	if (!(node instanceof Element)) return null;
	if (isInDocumentHead(node)) return null;
	let target = node;
	while (!(target instanceof HTMLElement) || shouldSkipElement(target)) {
		if (target.nextElementSibling === null) return null;
		target = target.nextElementSibling;
	}
	return {
		kind: "element",
		element: target
	};
}
function scrollToElement(target, hash) {
	if (hash !== null) {
		target.scrollIntoView({ behavior: "auto" });
		return;
	}
	const htmlElement = document.documentElement;
	const viewportHeight = htmlElement.clientHeight;
	if (topOfElementInViewport(target, viewportHeight)) return;
	htmlElement.scrollTop = 0;
	if (!topOfElementInViewport(target, viewportHeight)) target.scrollIntoView({
		behavior: "auto",
		block: "start",
		inline: "nearest"
	});
}
var AppRouterScrollTargetInner = class extends import_react.Component {
	scheduledCommitId = null;
	schedulePotentialScroll = () => {
		const commitId = this.props.commitId;
		this.scheduledCommitId = commitId;
		queueMicrotask(() => {
			if (this.scheduledCommitId !== commitId) return;
			this.handlePotentialScroll();
		});
	};
	handlePotentialScroll = () => {
		const intent = getPendingAppRouterScrollIntent();
		if (intent === null) return;
		if (this.props.commitId === null || intent.commitId !== this.props.commitId) return;
		let node;
		if (intent.hash !== null) node = getHashFragmentDomNode(intent.hash);
		else node = null;
		if (node === null) {
			node = findDOMNode(this);
			const headElement = node instanceof Element ? node : node?.parentElement;
			if (node !== null && headElement != null && isInDocumentHead(node) && !intent.headElements?.has(headElement)) {
				markAppRouterScrollIntentHeadHoisted(intent, this.props.commitId);
				return;
			}
		}
		const next = findNextScrollTarget(node);
		if (next === null) return;
		const target = next.element;
		const consumed = consumeAppRouterScrollIntent(intent, this.props.commitId);
		if (consumed === null) return;
		scrollToElement(target, consumed.hash);
		target.focus();
	};
	componentDidMount() {
		this.schedulePotentialScroll();
	}
	componentDidUpdate() {
		this.schedulePotentialScroll();
	}
	componentWillUnmount() {
		this.scheduledCommitId = null;
	}
	render() {
		return this.props.children;
	}
};
function AppRouterScrollCommitProvider({ children, commitId }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(AppRouterScrollCommitContext.Provider, {
		value: commitId,
		children
	});
}
function AppRouterScrollTarget({ children }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(AppRouterScrollTargetInner, {
		commitId: import_react.useContext(AppRouterScrollCommitContext),
		children
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/bfcache-identity.js
var NESTED_BFCACHE_SLOT_SEGMENT_PREFIX = "slot:\0vinext_bfcache_segment_";
function createNestedBfcacheSlotParentPrefix(parentSlotId) {
	const encodedParent = encodeURIComponent(parentSlotId);
	return `${NESTED_BFCACHE_SLOT_SEGMENT_PREFIX}${encodedParent.length}_${encodedParent}_`;
}
function isNestedBfcacheSlotSegmentId(id) {
	return id.startsWith(NESTED_BFCACHE_SLOT_SEGMENT_PREFIX);
}
function isNestedBfcacheSlotSegmentIdFor(id, parentSlotId) {
	return isNestedBfcacheSlotSegmentId(id) && id.startsWith(createNestedBfcacheSlotParentPrefix(parentSlotId));
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/slot.js
var slot_exports = /* @__PURE__ */ __exportAll({
	BfcacheIdentityMapContext: () => BfcacheIdentityMapContext,
	BfcacheSegmentBoundary: () => BfcacheSegmentBoundary,
	Children: () => Children,
	ChildrenContext: () => ChildrenContext,
	ElementsContext: () => ElementsContext,
	ParallelSlot: () => ParallelSlot,
	ParallelSlotsContext: () => ParallelSlotsContext,
	Slot: () => Slot,
	UNMATCHED_SLOT: () => UNMATCHED_SLOT,
	getNonCacheComponentsSegmentKey: () => getNonCacheComponentsSegmentKey,
	mergeElements: () => mergeElements,
	resolveBfcacheSegmentStateKey: () => resolveBfcacheSegmentStateKey,
	stageBfcacheSlotEntryForRender: () => stageBfcacheSlotEntryForRender,
	updateBfcacheSlotEntryOrder: () => updateBfcacheSlotEntryOrder
});
var EMPTY_ELEMENTS = Object.freeze({});
/**
* Holds resolved AppElements (not a Promise). React 19's use(Promise) during
* hydration triggers "async Client Component" for native Promises that lack
* React's internal .status property. Storing resolved values sidesteps this.
*/
var ElementsContext = import_react.createContext(EMPTY_ELEMENTS);
var ChildrenContext = import_react.createContext(null);
var ParallelSlotsContext = import_react.createContext(null);
var BfcacheIdMapContext$1 = getBfcacheIdMapContext();
var BfcacheSegmentIdContext = getBfcacheSegmentIdContext();
var EMPTY_BFCACHE_STATE_KEYS = Object.freeze({});
var MAX_BFCACHE_SLOT_ENTRIES_WITH_CACHE_COMPONENTS = 3;
var MAX_BFCACHE_SLOT_ENTRIES_WITHOUT_CACHE_COMPONENTS = 1;
var BfcacheIdentityMapContext = import_react.createContext(EMPTY_BFCACHE_STATE_KEYS);
function isCacheComponentsEnabled() {
	return String(false) === "true";
}
function getBfcacheSlotEntryLimit() {
	return isCacheComponentsEnabled() ? MAX_BFCACHE_SLOT_ENTRIES_WITH_CACHE_COMPONENTS : MAX_BFCACHE_SLOT_ENTRIES_WITHOUT_CACHE_COMPONENTS;
}
function normalizeBfcacheSlotEntryLimit(maxEntries) {
	if (!Number.isFinite(maxEntries)) return 1;
	return Math.max(1, Math.trunc(maxEntries));
}
function updateBfcacheSlotEntryOrder(previousOrder, activeStateKey, maxEntries = getBfcacheSlotEntryLimit()) {
	const entryLimit = normalizeBfcacheSlotEntryLimit(maxEntries);
	const nextOrder = [activeStateKey];
	for (const stateKey of previousOrder) {
		if (nextOrder.length >= entryLimit) break;
		if (stateKey === activeStateKey) continue;
		nextOrder.push(stateKey);
	}
	return nextOrder;
}
function pruneBfcacheSlotEntrySnapshots(snapshotsByStateKey, retainedOrder) {
	const retainedKeys = new Set(retainedOrder);
	for (const stateKey of snapshotsByStateKey.keys()) if (!retainedKeys.has(stateKey)) snapshotsByStateKey.delete(stateKey);
}
function haveSameBfcacheSlotEntryOrder(left, right) {
	if (left.length !== right.length) return false;
	for (let index = 0; index < left.length; index++) if (left[index] !== right[index]) return false;
	return true;
}
function stageBfcacheSlotEntryForRender(committedSnapshots, committedOrder, activeEntry, maxEntries = getBfcacheSlotEntryLimit()) {
	const snapshots = new Map(committedSnapshots);
	snapshots.set(activeEntry.stateKey, activeEntry);
	const order = updateBfcacheSlotEntryOrder(committedOrder, activeEntry.stateKey, maxEntries);
	pruneBfcacheSlotEntrySnapshots(snapshots, order);
	return {
		entries: order.map((stateKey) => snapshots.get(stateKey)).filter((entry) => entry !== void 0),
		order,
		snapshots
	};
}
function isLayoutFlagsValue(value) {
	if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
	const entries = Object.values(value);
	return entries.length > 0 && entries.every((entry) => entry === "s" || entry === "d");
}
function isArtifactCompatibilityEnvelopeValue(value) {
	if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
	return "schemaVersion" in value && "appElementsSchemaVersion" in value && "rscPayloadSchemaVersion" in value && "graphVersion" in value && "deploymentVersion" in value && "rootBoundaryId" in value && "renderEpoch" in value;
}
function isSlotBindingValue(value) {
	if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
	return "ownerLayoutId" in value && "slotId" in value && "state" in value;
}
function isSlotBindingListValue(value) {
	return Array.isArray(value) && value.length > 0 && value.every(isSlotBindingValue);
}
function isSkippedLayoutIdsMetadataValue(id, value) {
	return id === "__skippedLayoutIds" && Array.isArray(value) && value.every((entry) => typeof entry === "string");
}
function isBfcacheSegmentIdentitiesMetadataValue(id, value) {
	if (id !== "__bfcacheSegmentIdentities" || typeof value !== "object" || value === null || Array.isArray(value)) return false;
	return Object.entries(value).every(([elementId, identity]) => {
		const parsed = AppElementsWire.parseElementKey(elementId);
		return parsed !== null && parsed.kind !== "route" && typeof identity === "string";
	});
}
function isInterceptionMetadataValue(value) {
	if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
	return "sourceMatchedUrl" in value && typeof value.sourceMatchedUrl === "string" && "sourceRouteId" in value && typeof value.sourceRouteId === "string" && "slotId" in value && typeof value.slotId === "string" && "targetMatchedUrl" in value && typeof value.targetMatchedUrl === "string" && "targetRouteId" in value && typeof value.targetRouteId === "string";
}
function isCacheEntryReuseProofValue(value) {
	if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
	return "kind" in value && value.kind === "runtime-cache-entry" && "decision" in value;
}
function isTransportMetadataValue(id, value) {
	return isLayoutFlagsValue(value) || isBfcacheSegmentIdentitiesMetadataValue(id, value) || isArtifactCompatibilityEnvelopeValue(value) || isCacheEntryReuseProofValue(value) || isInterceptionMetadataValue(value) || isSkippedLayoutIdsMetadataValue(id, value) || isSlotBindingListValue(value);
}
/**
* Provider stack for Activity-retained BFCache entries. Each retained entry
* re-provides the elements, state-key map, and segment id it was captured with,
* falling back to the live boundary values for entries that predate per-entry
* capture.
*/
function BfcacheEntryProviders({ entry, fallbackElements, fallbackSegmentId, fallbackStateKeyMap, SegmentContext }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(BfcacheIdentityMapContext.Provider, {
		value: entry.stateKeyMap ?? fallbackStateKeyMap,
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ElementsContext.Provider, {
			value: entry.elements ?? fallbackElements,
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SegmentContext.Provider, {
				value: entry.segmentId ?? fallbackSegmentId,
				children: entry.content
			})
		})
	});
}
function useBfcacheSlotEntries(activeEntry) {
	const snapshotsByStateKey = import_react.useRef(/* @__PURE__ */ new Map());
	const [entryOrder, setEntryOrder] = import_react.useState(() => [activeEntry.stateKey]);
	const staged = stageBfcacheSlotEntryForRender(snapshotsByStateKey.current, entryOrder, activeEntry);
	const nextOrder = staged.order;
	const orderChanged = !haveSameBfcacheSlotEntryOrder(entryOrder, nextOrder);
	import_react.useLayoutEffect(() => {
		snapshotsByStateKey.current = staged.snapshots;
	}, [staged.snapshots]);
	if (orderChanged) setEntryOrder(nextOrder);
	return staged.entries;
}
function BfcacheActivitySlotBoundary({ activeStateKey, content, elements, id, SegmentContext, stateKeyMap }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(import_jsx_runtime.Fragment, { children: useBfcacheSlotEntries({
		content,
		elements,
		segmentId: id,
		stateKey: activeStateKey,
		stateKeyMap
	}).map((entry) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(import_react.Activity, {
		mode: entry.stateKey === activeStateKey ? "visible" : "hidden",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(BfcacheEntryProviders, {
			entry,
			fallbackElements: elements,
			fallbackSegmentId: id,
			fallbackStateKeyMap: stateKeyMap,
			SegmentContext
		})
	}, entry.stateKey)) });
}
/**
* Adds a nested segment-owned Activity cache inside a flattened AppElements
* entry. Named parallel routes are transported as one slot value, but Next.js
* retains each descendant segment independently. This boundary recreates that
* ownership without requiring a separate wire entry for every nested segment.
*/
function BfcacheSegmentBoundary({ children, id, stateKey }) {
	const elements = import_react.useContext(ElementsContext);
	const identityMap = import_react.useContext(BfcacheIdentityMapContext);
	const activeStateKey = resolveBfcacheSegmentStateKey(id, identityMap, import_react.useContext(BfcacheIdMapContext$1));
	if (!BfcacheSegmentIdContext || activeStateKey === void 0) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(import_react.Fragment, { children }, stateKey);
	if (!isCacheComponentsEnabled()) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(BfcacheSegmentIdContext.Provider, {
		value: id,
		children
	}, activeStateKey);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(BfcacheActivitySlotBoundary, {
		activeStateKey,
		content: children,
		elements,
		id,
		SegmentContext: BfcacheSegmentIdContext,
		stateKeyMap: identityMap
	});
}
function getNonCacheComponentsSegmentKey(id, activeStateKey) {
	const parsed = AppElementsWire.parseElementKey(id);
	return parsed !== null && parsed.kind !== "route" ? activeStateKey : void 0;
}
function resolveBfcacheSegmentStateKey(id, identityMap, bfcacheIdMap) {
	return identityMap[id] ?? bfcacheIdMap?.[id];
}
function BfcacheSlotBoundary({ content, id }) {
	const SegmentContext = BfcacheSegmentIdContext;
	const elements = import_react.useContext(ElementsContext);
	const identityMap = import_react.useContext(BfcacheIdentityMapContext);
	const activeStateKey = resolveBfcacheSegmentStateKey(id, identityMap, import_react.useContext(BfcacheIdMapContext$1));
	if (!SegmentContext) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(import_jsx_runtime.Fragment, { children: content });
	if (activeStateKey === void 0) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SegmentContext.Provider, {
		value: id,
		children: content
	});
	if (!isCacheComponentsEnabled()) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SegmentContext.Provider, {
		value: id,
		children: content
	}, getNonCacheComponentsSegmentKey(id, activeStateKey));
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(BfcacheActivitySlotBoundary, {
		activeStateKey,
		content,
		elements,
		id,
		SegmentContext,
		stateKeyMap: identityMap
	});
}
function mergeElements(prev, next, options = {}) {
	const clearAbsentSlots = typeof options === "boolean" ? options : options.clearAbsentSlots ?? false;
	const preserveAbsentSlots = typeof options === "boolean" ? !options : options.preserveAbsentSlots ?? true;
	const preserveElementIds = typeof options === "boolean" ? [] : options.preserveElementIds ?? [];
	const preservePreviousSlotIds = typeof options === "boolean" ? [] : options.preservePreviousSlotIds ?? [];
	const merged = { ...next };
	const preservedIdentityIds = /* @__PURE__ */ new Set();
	for (const id of preserveElementIds) if (Object.hasOwn(prev, id)) {
		const value = prev[id];
		if (value !== void 0) {
			merged[id] = value;
			preservedIdentityIds.add(id);
		}
	}
	const slotKeys = new Set([...Object.keys(prev), ...Object.keys(next)].filter((key) => AppElementsWire.isSlotId(key) && !isNestedBfcacheSlotSegmentId(key)));
	if (clearAbsentSlots) {
		for (const key of slotKeys) if (!Object.hasOwn(next, key)) delete merged[key];
	} else if (preserveAbsentSlots) {
		for (const key of slotKeys) if (!Object.hasOwn(merged, key) && Object.hasOwn(prev, key)) {
			const value = prev[key];
			if (value !== void 0) {
				merged[key] = value;
				preservedIdentityIds.add(key);
			}
		}
	}
	for (const id of preservePreviousSlotIds) {
		if (!AppElementsWire.isSlotId(id)) continue;
		if (!Object.hasOwn(prev, id)) continue;
		const value = prev[id];
		if (value !== void 0 && value !== UNMATCHED_SLOT) {
			merged[id] = value;
			preservedIdentityIds.add(id);
			for (const nestedId of Object.keys(prev)) {
				if (!isNestedBfcacheSlotSegmentIdFor(nestedId, id)) continue;
				const nestedValue = prev[nestedId];
				if (nestedValue !== void 0) merged[nestedId] = nestedValue;
				preservedIdentityIds.add(nestedId);
			}
		}
	}
	if (preservedIdentityIds.size > 0) {
		const previousIdentityValue = prev[APP_BFCACHE_SEGMENT_IDENTITIES_KEY];
		const nextIdentityValue = next[APP_BFCACHE_SEGMENT_IDENTITIES_KEY];
		const hasPreviousIdentities = isBfcacheSegmentIdentitiesMetadataValue(APP_BFCACHE_SEGMENT_IDENTITIES_KEY, previousIdentityValue);
		const hasNextIdentities = isBfcacheSegmentIdentitiesMetadataValue(APP_BFCACHE_SEGMENT_IDENTITIES_KEY, nextIdentityValue);
		const previousIdentities = hasPreviousIdentities ? { ...previousIdentityValue } : {};
		const mergedIdentities = hasNextIdentities ? { ...nextIdentityValue } : {};
		const identityIds = /* @__PURE__ */ new Set([...Object.keys(previousIdentities), ...Object.keys(mergedIdentities)]);
		const preservedParentIds = new Set(preservedIdentityIds);
		for (const parentId of preservedParentIds) for (const identityId of identityIds) if (isNestedBfcacheSlotSegmentIdFor(identityId, parentId)) preservedIdentityIds.add(identityId);
		for (const id of preservedIdentityIds) {
			const previousIdentity = previousIdentities[id];
			if (previousIdentity === void 0) delete mergedIdentities[id];
			else mergedIdentities[id] = previousIdentity;
		}
		if (hasPreviousIdentities || hasNextIdentities) merged[APP_BFCACHE_SEGMENT_IDENTITIES_KEY] = mergedIdentities;
	}
	return merged;
}
function Slot({ id, children, parallelSlots }) {
	const elements = import_react.useContext(ElementsContext);
	if (!Object.hasOwn(elements, id)) return null;
	const element = elements[id];
	if (isTransportMetadataValue(id, element)) return null;
	if (element === UNMATCHED_SLOT) notFound();
	if (element === null) return null;
	const content = /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ParallelSlotsContext.Provider, {
		value: parallelSlots ?? null,
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ChildrenContext.Provider, {
			value: children ?? null,
			children: element
		})
	});
	return BfcacheIdMapContext$1 && BfcacheSegmentIdContext ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(BfcacheSlotBoundary, {
		id,
		content
	}) : content;
}
function Children() {
	return import_react.useContext(ChildrenContext);
}
function ParallelSlot({ name }) {
	return import_react.useContext(ParallelSlotsContext)?.[name] ?? null;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-rsc-render-mode.js
var APP_RSC_RENDER_MODE_NAVIGATION = "navigation";
var APP_RSC_RENDER_MODE_PREFETCH_EMPTY = "prefetch-empty";
var APP_RSC_RENDER_MODE_PREFETCH_DYNAMIC_SHELL = "prefetch-dynamic-shell";
var APP_RSC_RENDER_MODE_PREFETCH_LOADING_SHELL = "prefetch-loading-shell";
function parseAppRscRenderMode(value) {
	switch (value) {
		case APP_RSC_RENDER_MODE_PREFETCH_EMPTY: return APP_RSC_RENDER_MODE_PREFETCH_EMPTY;
		case APP_RSC_RENDER_MODE_PREFETCH_DYNAMIC_SHELL: return APP_RSC_RENDER_MODE_PREFETCH_DYNAMIC_SHELL;
		case APP_RSC_RENDER_MODE_PREFETCH_LOADING_SHELL: return APP_RSC_RENDER_MODE_PREFETCH_LOADING_SHELL;
		default: return APP_RSC_RENDER_MODE_NAVIGATION;
	}
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/deployment-id.js
var NEXT_DEPLOYMENT_ID_HEADER = "x-deployment-id";
function applyDeploymentIdHeader(headers, deploymentId = void 0) {
	if (deploymentId) headers.set(NEXT_DEPLOYMENT_ID_HEADER, deploymentId);
}
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
[
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
var textEncoder$2 = new TextEncoder();
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
function isRscCompatibilityIdCompatible(responseCompatibilityId, clientCompatibilityId = getVinextRscCompatibilityId()) {
	const normalizedResponseCompatibilityId = normalizeCompatibilityId(responseCompatibilityId);
	const normalizedClientCompatibilityId = normalizeCompatibilityId(clientCompatibilityId);
	return normalizedClientCompatibilityId === null || normalizedResponseCompatibilityId !== null && normalizedResponseCompatibilityId === normalizedClientCompatibilityId;
}
function resolveHardNavigationTargetFromRscResponse(responseUrl, currentHref, origin) {
	if (!responseUrl) return currentHref;
	const parsed = new URL(responseUrl, origin);
	stripRscCacheBustingSearchParam(parsed);
	const origUrl = new URL(currentHref, origin);
	let pathname = stripRscSuffix(parsed.pathname);
	if (origUrl.pathname.length > 1 && origUrl.pathname.endsWith("/") && !pathname.endsWith("/")) pathname += "/";
	let hardNavigationTarget = pathname + parsed.search;
	if (origUrl.hash) hardNavigationTarget += origUrl.hash;
	return hardNavigationTarget;
}
function resolveRscCompatibilityNavigationDecision(options) {
	if (isRscCompatibilityIdCompatible(options.responseCompatibilityId, options.clientCompatibilityId)) return { kind: "compatible" };
	return {
		hardNavigationTarget: resolveHardNavigationTargetFromRscResponse(options.responseUrl, options.currentHref, options.origin),
		kind: "hard-navigate"
	};
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
	const digest = await globalThis.crypto.subtle.digest("SHA-256", textEncoder$2.encode(input));
	return encodeBase64Url(new Uint8Array(digest).subarray(0, CACHE_BUSTING_DIGEST_BYTES));
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
function createRscRequestHeaders(options = {}) {
	const headers = new Headers({
		Accept: VINEXT_RSC_CONTENT_TYPE,
		["RSC"]: "1"
	});
	applyDeploymentIdHeader(headers);
	if (options.prefetchRouterState) {
		if (options.includePrefetchHeader !== false) headers.set(NEXT_ROUTER_PREFETCH_HEADER, "1");
		headers.set(NEXT_ROUTER_STATE_TREE_HEADER, encodeURIComponent(JSON.stringify(options.prefetchRouterState)));
	}
	if (options.nextUrl) headers.set(NEXT_URL_HEADER, options.nextUrl);
	if (options.interceptionContext !== void 0 && options.interceptionContext !== null) headers.set(VINEXT_INTERCEPTION_CONTEXT_HEADER, options.interceptionContext);
	if (options.mountedSlotsHeader !== void 0 && options.mountedSlotsHeader !== null) headers.set(VINEXT_MOUNTED_SLOTS_HEADER, options.mountedSlotsHeader);
	if (options.clientReuseManifestHeader !== void 0 && options.clientReuseManifestHeader !== null) headers.set(VINEXT_CLIENT_REUSE_MANIFEST_HEADER, options.clientReuseManifestHeader);
	const renderMode = options.renderMode ?? "navigation";
	if (renderMode !== "navigation") headers.set(VINEXT_RSC_RENDER_MODE_HEADER, renderMode);
	return headers;
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
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/client/instrumentation-client-state.js
var clientInstrumentationHooks$1 = null;
function normalizeClientInstrumentationHooks(hooks) {
	return Object.values(hooks).some((value) => typeof value === "function") ? hooks : null;
}
function setClientInstrumentationHooks(hooks) {
	clientInstrumentationHooks$1 = hooks;
	return clientInstrumentationHooks$1;
}
function notifyAppRouterTransitionStart(href, navigationType) {
	clientInstrumentationHooks$1?.onRouterTransitionStart?.(href, navigationType);
}
setClientInstrumentationHooks(normalizeClientInstrumentationHooks(/* @__PURE__ */ __exportAll({})));
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/number.js
function isNonNegativeSafeInteger(value) {
	return typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-history-state.js
var VINEXT_PREVIOUS_NEXT_URL_HISTORY_STATE_KEY = "__vinext_previousNextUrl";
var VINEXT_HISTORY_INDEX_HISTORY_STATE_KEY = "__vinext_historyIndex";
var VINEXT_BFCACHE_IDS_HISTORY_STATE_KEY = "__vinext_bfcacheIds";
var VINEXT_BFCACHE_VERSION_HISTORY_STATE_KEY = "__vinext_bfcacheVersion";
var HistoryStateSnapshotCache = class {
	#maxEntries;
	#snapshots = /* @__PURE__ */ new Map();
	constructor(options) {
		this.#maxEntries = options.maxEntries;
	}
	clear() {
		this.#snapshots.clear();
	}
	remember(options) {
		if (options.historyIndex === null) return;
		this.#snapshots.delete(options.historyIndex);
		this.#snapshots.set(options.historyIndex, {
			bfcacheVersion: options.bfcacheVersion,
			state: options.state
		});
		if (this.#snapshots.size <= this.#maxEntries) return;
		const oldestIndex = this.#snapshots.keys().next().value;
		if (typeof oldestIndex === "number") this.#snapshots.delete(oldestIndex);
	}
	resolveRestore(options) {
		const targetHistoryIndex = readHistoryStateTraversalIndex(options.historyState);
		if (targetHistoryIndex === null) return {
			kind: "skip",
			reason: "missing-history-index",
			targetHistoryIndex
		};
		const snapshot = this.#snapshots.get(targetHistoryIndex);
		if (!snapshot) return {
			kind: "skip",
			reason: "missing-snapshot",
			targetHistoryIndex
		};
		if (options.guarded) return {
			kind: "skip",
			reason: "guarded",
			targetHistoryIndex
		};
		if (snapshot.bfcacheVersion !== options.currentBfcacheVersion) {
			this.#snapshots.delete(targetHistoryIndex);
			return {
				kind: "skip",
				reason: "stale-bfcache-version",
				targetHistoryIndex
			};
		}
		return {
			kind: "restore",
			state: snapshot.state,
			targetHistoryIndex
		};
	}
};
var RestorableClientStateController = class {
	#currentBfcacheVersion;
	#pendingCacheInvalidationGuards = 0;
	#snapshots;
	constructor(options) {
		const initialHistoryBfcacheVersion = readHistoryStateBfcacheVersion(options.initialHistoryState);
		this.#currentBfcacheVersion = initialHistoryBfcacheVersion === null ? 0 : initialHistoryBfcacheVersion + 1;
		this.#snapshots = new HistoryStateSnapshotCache({ maxEntries: options.maxHistoryStateSnapshots });
	}
	get currentBfcacheVersion() {
		return this.#currentBfcacheVersion;
	}
	beginCacheInvalidationGuard() {
		this.#pendingCacheInvalidationGuards += 1;
		let released = false;
		return () => {
			if (released) return;
			released = true;
			this.#pendingCacheInvalidationGuards = Math.max(0, this.#pendingCacheInvalidationGuards - 1);
		};
	}
	isCacheInvalidationGuarded() {
		return this.#pendingCacheInvalidationGuards > 0;
	}
	isCurrentBfcacheVersion(historyState) {
		return isHistoryStateBfcacheVersionCurrent(historyState, this.#currentBfcacheVersion);
	}
	readCurrentBfcacheVersionHistoryIds(historyState) {
		if (this.isCacheInvalidationGuarded()) return null;
		const ids = readHistoryStateBfcacheIds(historyState);
		if (ids === null) return null;
		return this.isCurrentBfcacheVersion(historyState) ? ids : null;
	}
	#invalidateBfcacheIds() {
		this.#currentBfcacheVersion += 1;
	}
	invalidateClientState() {
		this.#snapshots.clear();
		this.#invalidateBfcacheIds();
	}
	rememberHistoryStateSnapshot(options) {
		this.#snapshots.remember({
			bfcacheVersion: this.#currentBfcacheVersion,
			historyIndex: options.historyIndex,
			state: options.state
		});
	}
	resolveHistoryStateSnapshotRestore(historyState) {
		return this.#snapshots.resolveRestore({
			currentBfcacheVersion: this.#currentBfcacheVersion,
			guarded: this.isCacheInvalidationGuarded(),
			historyState
		});
	}
};
function cloneHistoryState(state) {
	if (!state || typeof state !== "object") return {};
	const nextState = {};
	for (const [key, value] of Object.entries(state)) nextState[key] = value;
	return nextState;
}
function readHistoryStateRecord(state) {
	if (!state || typeof state !== "object" || Array.isArray(state)) return null;
	return state;
}
function createHistoryStateWithNavigationMetadata(state, metadata) {
	const nextState = cloneHistoryState(state);
	const bfcacheIdsWereCleared = metadata.bfcacheIds !== void 0 && (metadata.bfcacheIds === null || Object.keys(metadata.bfcacheIds).length === 0);
	if (metadata.previousNextUrl === null) delete nextState[VINEXT_PREVIOUS_NEXT_URL_HISTORY_STATE_KEY];
	else nextState[VINEXT_PREVIOUS_NEXT_URL_HISTORY_STATE_KEY] = metadata.previousNextUrl;
	if (metadata.traversalIndex !== void 0) if (isNonNegativeSafeInteger(metadata.traversalIndex)) nextState[VINEXT_HISTORY_INDEX_HISTORY_STATE_KEY] = metadata.traversalIndex;
	else delete nextState[VINEXT_HISTORY_INDEX_HISTORY_STATE_KEY];
	if (metadata.bfcacheIds !== void 0) if (bfcacheIdsWereCleared) {
		delete nextState[VINEXT_BFCACHE_IDS_HISTORY_STATE_KEY];
		delete nextState[VINEXT_BFCACHE_VERSION_HISTORY_STATE_KEY];
	} else nextState[VINEXT_BFCACHE_IDS_HISTORY_STATE_KEY] = { ...metadata.bfcacheIds };
	if (metadata.bfcacheVersion !== void 0) if (bfcacheIdsWereCleared) delete nextState[VINEXT_BFCACHE_VERSION_HISTORY_STATE_KEY];
	else if (isNonNegativeSafeInteger(metadata.bfcacheVersion)) nextState[VINEXT_BFCACHE_VERSION_HISTORY_STATE_KEY] = metadata.bfcacheVersion;
	else delete nextState[VINEXT_BFCACHE_VERSION_HISTORY_STATE_KEY];
	return Object.keys(nextState).length > 0 ? nextState : null;
}
function createExternalHistoryStatePreservingMetadata(callerState, currentHistoryState) {
	const previousNextUrl = readHistoryStatePreviousNextUrl(currentHistoryState);
	const traversalIndex = readHistoryStateTraversalIndex(currentHistoryState);
	const bfcacheIds = readHistoryStateBfcacheIds(currentHistoryState);
	const bfcacheVersion = readHistoryStateBfcacheVersion(currentHistoryState);
	if (previousNextUrl === null && traversalIndex === null && bfcacheIds === null) return callerState;
	return createHistoryStateWithNavigationMetadata(callerState, {
		bfcacheIds,
		bfcacheVersion: bfcacheIds === null ? void 0 : bfcacheVersion,
		previousNextUrl,
		traversalIndex
	});
}
function readHistoryStatePreviousNextUrl(state) {
	const value = readHistoryStateRecord(state)?.[VINEXT_PREVIOUS_NEXT_URL_HISTORY_STATE_KEY];
	return typeof value === "string" ? value : null;
}
function isBfcacheSegmentId(id) {
	const parsed = AppElementsWire.parseElementKey(id);
	return parsed?.kind === "layout" || parsed?.kind === "page" || parsed?.kind === "slot" || parsed?.kind === "template";
}
function readHistoryStateBfcacheIds(state) {
	const value = readHistoryStateRecord(state)?.[VINEXT_BFCACHE_IDS_HISTORY_STATE_KEY];
	if (!value || typeof value !== "object" || Array.isArray(value)) return null;
	const ids = {};
	for (const [key, id] of Object.entries(value)) {
		if (!isBfcacheSegmentId(key) || typeof id !== "string") return null;
		ids[key] = id;
	}
	return ids;
}
function readHistoryStateBfcacheVersion(state) {
	const value = readHistoryStateRecord(state)?.[VINEXT_BFCACHE_VERSION_HISTORY_STATE_KEY];
	return isNonNegativeSafeInteger(value) ? value : null;
}
/**
* Whether a history entry's stored bfcache version matches the document's
* current version. A missing/invalid stored version (null) is NEVER current:
* coercing it to 0 would let un-versioned entries (older builds / external
* pushState) pass the gate on a fresh document whose current version is 0,
* defeating the document-scoped stale-id rejection. App-written entries always
* carry an explicit version, so the legitimate first-document path (0 === 0)
* still matches.
*/
function isHistoryStateBfcacheVersionCurrent(state, currentVersion) {
	const version = readHistoryStateBfcacheVersion(state);
	return version !== null && version === currentVersion;
}
function createHashOnlyHistoryStatePreservingNavigationMetadata(state) {
	const previousNextUrl = readHistoryStatePreviousNextUrl(state);
	const bfcacheIds = readHistoryStateBfcacheIds(state);
	const bfcacheVersion = readHistoryStateBfcacheVersion(state);
	if (previousNextUrl === null && bfcacheIds === null) return null;
	return createHistoryStateWithNavigationMetadata(null, {
		bfcacheIds,
		bfcacheVersion: bfcacheIds === null ? void 0 : bfcacheVersion,
		previousNextUrl
	});
}
function readHistoryStateTraversalIndex(state) {
	const value = readHistoryStateRecord(state)?.[VINEXT_HISTORY_INDEX_HISTORY_STATE_KEY];
	return isNonNegativeSafeInteger(value) ? value : null;
}
function resolveHistoryTraversalIntent(options) {
	const targetHistoryIndex = readHistoryStateTraversalIndex(options.historyState);
	let direction = "unknown";
	if (options.currentHistoryIndex !== null && targetHistoryIndex !== null) {
		if (targetHistoryIndex < options.currentHistoryIndex) direction = "back";
		else if (targetHistoryIndex > options.currentHistoryIndex) direction = "forward";
	}
	return {
		direction,
		historyState: options.historyState,
		targetHistoryIndex
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-bfcache-id.js
var PUBLIC_INITIAL_BFCACHE_ID = "_b_0_";
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-bfcache-identity.js
var nextBfcacheId = 0;
function rememberBfcacheId(value) {
	const match = /^_b_(\d+)_$/.exec(value);
	if (!match) return;
	nextBfcacheId = Math.max(nextBfcacheId, Number(match[1]));
}
function mintBfcacheId() {
	nextBfcacheId += 1;
	return `_b_${nextBfcacheId}_`;
}
function readAppElementsMetadata(elements) {
	try {
		return AppElementsWire.readMetadata(elements);
	} catch {
		return null;
	}
}
function collectBfcacheSegmentIds(elements, metadata) {
	const ids = new Set(Object.keys(elements));
	const parsedMetadata = metadata === void 0 ? readAppElementsMetadata(elements) : metadata;
	for (const layoutId of parsedMetadata?.layoutIds ?? []) ids.add(layoutId);
	for (const identityId of Object.keys(parsedMetadata?.bfcacheSegmentIdentities ?? {})) ids.add(identityId);
	return Array.from(ids).filter(isBfcacheSegmentId);
}
function createInitialBfcacheIdMap(elements) {
	const bfcacheIds = {};
	for (const id of collectBfcacheSegmentIds(elements)) bfcacheIds[id] = "0";
	return bfcacheIds;
}
function createBfcacheSegmentIdentityMap(options) {
	return readAppElementsMetadata(options.elements)?.bfcacheSegmentIdentities ?? {};
}
function createNextBfcacheIdMap(options) {
	const current = options.reuseCurrent === false ? {} : options.current;
	for (const value of Object.values(current)) rememberBfcacheId(value);
	for (const value of Object.values(options.restored ?? {})) rememberBfcacheId(value);
	const currentMetadata = readAppElementsMetadata(options.currentElements);
	const nextMetadata = readAppElementsMetadata(options.elements);
	const ids = {};
	for (const id of collectBfcacheSegmentIds(options.elements, nextMetadata)) {
		const currentIdentity = currentMetadata?.bfcacheSegmentIdentities[id];
		const nextIdentity = nextMetadata?.bfcacheSegmentIdentities[id];
		const currentValue = currentIdentity !== void 0 && currentIdentity === nextIdentity ? current[id] : void 0;
		const value = (nextIdentity === void 0 ? void 0 : options.restored?.[id]) ?? currentValue ?? mintBfcacheId();
		ids[id] = value;
		rememberBfcacheId(value);
	}
	return ids;
}
function preserveBfcacheIdsForMergedElements(options) {
	const ids = {};
	const preservePreviousIds = new Set(options.preservePreviousIds ?? []);
	const preservedElementIds = new Set(options.preservedElementIds ?? []);
	const preservedParentIds = [...preservedElementIds];
	const identities = createBfcacheSegmentIdentityMap({ elements: options.elements });
	for (const id of collectBfcacheSegmentIds(options.elements)) {
		const isPreservedNestedSegment = preservedParentIds.some((parentId) => isNestedBfcacheSlotSegmentIdFor(id, parentId));
		const value = (preservedElementIds.has(id) || isPreservedNestedSegment) && identities[id] === void 0 ? mintBfcacheId() : preservePreviousIds.has(id) || isPreservedNestedSegment ? options.previous[id] ?? options.next[id] : options.next[id] ?? options.previous[id];
		if (value === void 0) continue;
		ids[id] = value;
		rememberBfcacheId(value);
	}
	return ids;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-browser-action-result.js
function resolveServerActionOperationLane(revalidation) {
	return revalidation === "none" ? "server-action" : "refresh";
}
function shouldScheduleRefreshForDiscardedServerAction(revalidation) {
	return revalidation !== "none";
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
function encodeParts(parts) {
	return JSON.stringify(parts);
}
function compareDimensions(a, b) {
	return a.source.localeCompare(b.source) || a.name.localeCompare(b.name) || a.privacy.localeCompare(b.privacy);
}
function encodeNullable(value) {
	return value;
}
function assertNever(value) {
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
		default: return assertNever(output);
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
function createCacheEntryReuseProof(decision) {
	if (decision === null) return {
		kind: "runtime-cache-entry",
		decision: null
	};
	switch (decision.kind) {
		case "reuse": return {
			kind: "runtime-cache-entry",
			decision: {
				canReuse: true,
				code: decision.proof.code,
				kind: "reuse",
				reuseClass: decision.proof.reuseClass
			}
		};
		case "fallback": return {
			kind: "runtime-cache-entry",
			decision: {
				canReuse: false,
				code: decision.fallback.code,
				kind: "reject",
				mode: decision.fallback.mode,
				scope: decision.fallback.scope
			}
		};
		default: return assertNever(decision);
	}
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
var textEncoder$1 = new TextEncoder();
function compareManifestEntries(left, right) {
	if (left.id < right.id) return -1;
	if (left.id > right.id) return 1;
	return 0;
}
function createCanonicalWireEntries(entries) {
	const entriesById = /* @__PURE__ */ new Map();
	for (const entry of entries) if (!entriesById.has(entry.id)) entriesById.set(entry.id, entry);
	return Array.from(entriesById.values()).sort(compareManifestEntries);
}
function countUtf8Bytes(input) {
	return textEncoder$1.encode(input).length;
}
function createClientReusePayloadHash(input) {
	return fnv1a64(input);
}
function createClientReuseManifest(input) {
	const replayWindow = input.replayWindow ?? {
		validFromVisibleCommitVersion: input.visibleCommitVersion,
		validUntilVisibleCommitVersion: input.visibleCommitVersion
	};
	return {
		entries: createCanonicalWireEntries(input.entries),
		hashAlgorithm: CLIENT_REUSE_MANIFEST_HASH_ALGORITHM,
		replayWindow,
		schemaVersion: 1,
		visibleCommitVersion: input.visibleCommitVersion
	};
}
function serializeClientReuseManifest(input) {
	return JSON.stringify(createClientReuseManifest(input));
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
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-browser-client-reuse-manifest.js
function capClientReuseManifestProducerLimits(limits) {
	return {
		...limits,
		maxEntryCount: Math.min(limits.maxEntryCount, 8)
	};
}
function serializeBoundedClientReuseManifest(input) {
	const entries = input.entries.slice(0, input.limits.maxEntryCount);
	let low = 1;
	let high = entries.length;
	let best = null;
	while (low <= high) {
		const size = Math.floor((low + high) / 2);
		const serialized = serializeClientReuseManifest({
			entries: entries.slice(0, size),
			replayWindow: {
				validFromVisibleCommitVersion: input.visibleCommitVersion,
				validUntilVisibleCommitVersion: input.visibleCommitVersion
			},
			visibleCommitVersion: input.visibleCommitVersion
		});
		if (countUtf8Bytes(serialized) <= input.limits.maxManifestBytes) {
			best = serialized;
			low = size + 1;
		} else high = size - 1;
	}
	return best;
}
function hasRetainedElement(elements, elementId) {
	return Object.hasOwn(elements, elementId);
}
function createStaticLayoutEntry(input) {
	const routeId = createStaticLayoutClientReuseRouteId(input.layoutId);
	const output = {
		kind: "layout",
		layoutId: input.layoutId,
		rootBoundaryId: input.artifactCompatibility.rootBoundaryId,
		routeId
	};
	const candidateVariant = buildCacheVariantWithRouteBudget({
		budget: DEFAULT_CACHE_VARIANT_BUDGET,
		dimensions: [],
		output,
		routeBudget: {
			routeId: output.routeId,
			variantCacheKeys: []
		}
	});
	if (candidateVariant.kind !== "variant") return null;
	const artifactCompatibility = createStaticLayoutClientReuseArtifactCompatibility({
		artifactCompatibility: input.artifactCompatibility,
		layoutId: input.layoutId,
		rootBoundaryId: output.rootBoundaryId,
		routeId: output.routeId,
		variantCacheKey: candidateVariant.variant.cacheKey
	});
	return {
		artifactCompatibility,
		id: input.layoutId,
		payloadHash: createStaticLayoutClientReusePayloadHash({
			artifactCompatibility,
			layoutId: input.layoutId,
			rootBoundaryId: output.rootBoundaryId,
			routeId: output.routeId,
			variantCacheKey: candidateVariant.variant.cacheKey
		}),
		privacy: "public",
		variantCacheKey: candidateVariant.variant.cacheKey
	};
}
function createClientReuseManifestHeaderFromVisibleAppState(state, options = {}) {
	const limits = capClientReuseManifestProducerLimits(options.limits ?? DEFAULT_CLIENT_REUSE_MANIFEST_LIMITS);
	const metadata = AppElementsWire.readMetadata(state.elements);
	const entries = [];
	for (const layoutId of metadata.layoutIds) {
		if (entries.length >= limits.maxEntryCount) break;
		if (layoutId.length > limits.maxEntryIdLength) continue;
		if (metadata.layoutFlags[layoutId] !== "s") continue;
		if (!hasRetainedElement(state.elements, layoutId)) continue;
		if (AppElementsWire.parseElementKey(layoutId)?.kind !== "layout") continue;
		const entry = createStaticLayoutEntry({
			artifactCompatibility: metadata.artifactCompatibility,
			layoutId
		});
		if (entry) entries.push(entry);
	}
	if (entries.length === 0) return null;
	return serializeBoundedClientReuseManifest({
		entries,
		limits,
		visibleCommitVersion: state.visibleCommitVersion
	});
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
* Normalize a pathname for route matching by decoding each segment independently.
* This prevents encoded slashes from turning into real path separators.
*/
function normalizePathnameForRouteMatch(pathname) {
	return pathname.split("/").map((segment) => decodeRouteSegment(segment)).join("/");
}
function splitPathnameForRouteMatch(pathname) {
	return normalizePathnameForRouteMatch(pathname).split("/").filter(Boolean);
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
function matchRoutePatternWithOptionalDynamicSegments(pathParts, patternParts) {
	function matchFrom(pathIndex, patternIndex) {
		if (patternIndex === patternParts.length) return pathIndex === pathParts.length;
		const patternPart = patternParts[patternIndex];
		if (patternPart.startsWith(":") && (patternPart.endsWith("+") || patternPart.endsWith("*"))) {
			const minLength = patternPart.endsWith("+") ? 1 : 0;
			for (let endIndex = pathIndex + minLength; endIndex <= pathParts.length; endIndex++) if (matchFrom(endIndex, patternIndex + 1)) return true;
			return false;
		}
		if (patternPart.startsWith(":")) return matchFrom(pathIndex, patternIndex + 1) || pathIndex < pathParts.length && matchFrom(pathIndex + 1, patternIndex + 1);
		if (pathIndex >= pathParts.length || pathParts[pathIndex] !== patternPart) return false;
		return matchFrom(pathIndex + 1, patternIndex + 1);
	}
	return matchFrom(0, 0);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-browser-interception-context.js
/**
* Resolve the first-hop interception context from declared route topology.
*
* This is intentionally manifest-only: it lets a normal browser navigation
* ask the server for an intercepted payload when the current URL is a declared
* interception source for the target URL, without reintroducing snapshot
* topology as route/layout/slot authority.
*
* When multiple manifest interceptions match, the first one wins. That order
* is owned by the deterministic route graph builder.
*/
function resolveManifestNavigationInterceptionContext(options) {
	if (options.routeManifest === null) return null;
	const currentPathname = stripBasePath(options.currentPathname, options.basePath);
	const targetPathname = stripBasePath(options.targetPathname, options.basePath);
	const sourceParts = splitPathnameForRouteMatch(currentPathname);
	const targetParts = splitPathnameForRouteMatch(targetPathname);
	for (const interception of options.routeManifest.segmentGraph.interceptions.values()) {
		if (!matchRoutePatternPrefix(sourceParts, interception.sourcePatternParts)) continue;
		if (matchRoutePattern(targetParts, interception.targetPatternParts) === null) continue;
		return currentPathname;
	}
	return null;
}
function resolveMiddlewareRewriteNavigationInterceptionContext(options) {
	if (options.routeManifest === null) return null;
	const currentPathname = stripBasePath(options.currentPathname, options.basePath);
	const currentMatchedPathname = options.currentMatchedPathname ? stripBasePath(options.currentMatchedPathname, options.basePath) : null;
	const targetPathname = stripBasePath(options.targetPathname, options.basePath);
	const sourceParts = splitPathnameForRouteMatch(currentPathname);
	const matchedSourceParts = currentMatchedPathname ? splitPathnameForRouteMatch(currentMatchedPathname) : null;
	const targetParts = splitPathnameForRouteMatch(targetPathname);
	for (const interception of options.routeManifest.segmentGraph.interceptions.values()) {
		if (!matchRoutePatternWithOptionalDynamicSegments(targetParts, interception.targetPatternParts)) continue;
		if (matchRoutePatternPrefix(sourceParts, interception.sourcePatternParts)) return currentPathname;
		if (currentMatchedPathname !== null && matchedSourceParts !== null && matchRoutePatternPrefix(matchedSourceParts, interception.sourcePatternParts)) return currentMatchedPathname;
	}
	return null;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-browser-mpa-navigation.js
var NEXT_APP_ROUTER_PAGE_REDIRECT_MARKER_ID = "__next-page-redirect";
function hasPendingAppRouterPageRedirect(targetDocument) {
	if (typeof targetDocument !== "object" || targetDocument === null) return false;
	if (!("getElementById" in targetDocument)) return false;
	const { getElementById } = targetDocument;
	if (typeof getElementById !== "function") return false;
	return getElementById.call(targetDocument, NEXT_APP_ROUTER_PAGE_REDIRECT_MARKER_ID) !== null;
}
var AppBrowserMpaNavigationScheduler = class {
	#pendingNavigation = null;
	#nextToken = 0;
	reset() {
		this.#pendingNavigation = null;
	}
	navigate(targetWindow, href, historyUpdateMode) {
		const pendingNavigation = this.#pendingNavigation;
		if (pendingNavigation?.href === href && pendingNavigation.historyUpdateMode === historyUpdateMode) return;
		const token = this.#nextToken + 1;
		this.#nextToken = token;
		this.#pendingNavigation = {
			href,
			historyUpdateMode,
			token
		};
		const navigate = () => {
			const currentNavigation = this.#pendingNavigation;
			if (currentNavigation?.href !== href || currentNavigation.historyUpdateMode !== historyUpdateMode || currentNavigation.token !== token) return;
			if (historyUpdateMode === "replace") targetWindow.location.replace(href);
			else targetWindow.location.assign(href);
		};
		if (typeof targetWindow.requestAnimationFrame === "function") {
			targetWindow.requestAnimationFrame(() => {
				targetWindow.setTimeout(navigate, 0);
			});
			return;
		}
		targetWindow.setTimeout(navigate, 0);
	}
};
new TextEncoder();
var decoder = new TextDecoder();
var FRAME_ESCAPE_BYTE = 255;
var FOOTER_TAG_BYTE = 0;
var FOOTER_PREFIX_BYTES = 2;
var FOOTER_LENGTH_BYTES = 4;
var MAX_FOOTER_BYTES = 256;
function isDynamicStaleTimeSeconds(value) {
	return typeof value === "number" && Number.isFinite(value) && value >= 0;
}
function invalidFooter() {
	throw new Error("Invalid or truncated RSC completion metadata footer");
}
function parseFooterCandidate(candidate) {
	if (candidate.byteLength > MAX_FOOTER_BYTES) throw new Error("RSC completion metadata exceeded its framing limit");
	if (candidate.byteLength < 6 || candidate[0] !== FRAME_ESCAPE_BYTE || candidate[1] !== FOOTER_TAG_BYTE) return invalidFooter();
	const lengthOffset = candidate.byteLength - FOOTER_LENGTH_BYTES;
	if (new DataView(candidate.buffer, candidate.byteOffset + lengthOffset, FOOTER_LENGTH_BYTES).getUint32(0) !== lengthOffset - FOOTER_PREFIX_BYTES) return invalidFooter();
	try {
		const parsed = JSON.parse(decoder.decode(candidate.subarray(FOOTER_PREFIX_BYTES, lengthOffset)));
		if (typeof parsed !== "object" || parsed === null) return invalidFooter();
		const fields = parsed;
		if (!isDynamicStaleTimeSeconds(fields.dynamicStaleTimeSeconds)) return invalidFooter();
		const hasServerStaleTime = Object.hasOwn(fields, "serverStaleTimeSeconds");
		const serverStaleTimeSeconds = fields.serverStaleTimeSeconds;
		if (hasServerStaleTime && serverStaleTimeSeconds !== null && !isDynamicStaleTimeSeconds(serverStaleTimeSeconds)) return invalidFooter();
		return {
			dynamicStaleTimeSeconds: fields.dynamicStaleTimeSeconds,
			...hasServerStaleTime ? { serverStaleTimeSeconds } : {}
		};
	} catch {
		return invalidFooter();
	}
}
function extractRscCompletionMetadata(buffer) {
	const bytes = new Uint8Array(buffer);
	const firstEscape = bytes.indexOf(FRAME_ESCAPE_BYTE);
	if (firstEscape === -1) return { buffer };
	const decoded = new Uint8Array(bytes.byteLength);
	decoded.set(bytes.subarray(0, firstEscape));
	let output = firstEscape;
	for (let index = firstEscape; index < bytes.byteLength; index++) {
		const byte = bytes[index];
		if (byte !== FRAME_ESCAPE_BYTE) {
			decoded[output++] = byte;
			continue;
		}
		const escapedByte = bytes[++index];
		if (escapedByte === void 0) throw new Error("Truncated RSC completion metadata escape sequence");
		if (escapedByte === FRAME_ESCAPE_BYTE) {
			decoded[output++] = FRAME_ESCAPE_BYTE;
			continue;
		}
		if (escapedByte !== FOOTER_TAG_BYTE) throw new Error("Invalid RSC completion metadata escape sequence");
		return {
			buffer: decoded.buffer.slice(0, output),
			metadata: parseFooterCandidate(bytes.subarray(index - 1))
		};
	}
	return { buffer: decoded.buffer.slice(0, output) };
}
function stripRscCompletionMetadata(source) {
	let escapePending = false;
	let footerCandidate;
	return source.pipeThrough(new TransformStream({
		transform(chunk, controller) {
			const output = [];
			const flushOutput = () => {
				if (output.length === 0) return;
				controller.enqueue(Uint8Array.from(output));
				output.length = 0;
			};
			let offset = 0;
			while (offset < chunk.byteLength) {
				if (footerCandidate) {
					footerCandidate.push(chunk[offset++]);
					if (footerCandidate.length > MAX_FOOTER_BYTES) {
						controller.error(/* @__PURE__ */ new Error("RSC completion metadata exceeded its framing limit"));
						return;
					}
					continue;
				}
				if (escapePending) {
					const escapedByte = chunk[offset++];
					escapePending = false;
					if (escapedByte === FRAME_ESCAPE_BYTE) {
						output.push(FRAME_ESCAPE_BYTE);
						continue;
					}
					if (escapedByte === FOOTER_TAG_BYTE) {
						footerCandidate = [FRAME_ESCAPE_BYTE, FOOTER_TAG_BYTE];
						continue;
					}
					controller.error(/* @__PURE__ */ new Error("Invalid RSC completion metadata escape sequence"));
					return;
				}
				const escapeOffset = chunk.indexOf(FRAME_ESCAPE_BYTE, offset);
				if (escapeOffset === -1) {
					flushOutput();
					controller.enqueue(chunk.subarray(offset));
					return;
				}
				if (escapeOffset > offset) {
					flushOutput();
					controller.enqueue(chunk.subarray(offset, escapeOffset));
				}
				escapePending = true;
				offset = escapeOffset + 1;
			}
			flushOutput();
		},
		flush(controller) {
			if (escapePending) {
				controller.error(/* @__PURE__ */ new Error("Truncated RSC completion metadata escape sequence"));
				return;
			}
			if (footerCandidate) {
				const candidate = Uint8Array.from(footerCandidate);
				try {
					parseFooterCandidate(candidate);
				} catch (error) {
					controller.error(error);
				}
			}
		}
	}));
}
/** Remove vinext's internal completion footer before React reads a Flight response. */
function stripRscCompletionMetadataResponse(response) {
	if (response.headers.get("X-Vinext-Rsc-Completion-Metadata") !== "1" || !response.body) return response;
	return new Response(stripRscCompletionMetadata(response.body), {
		headers: response.headers,
		status: response.status,
		statusText: response.statusText
	});
}
//#endregion
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
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-browser-rsc-redirect.js
var MAX_RSC_REDIRECT_DEPTH = 10;
function blockDangerousStreamedRscRedirect(response, streamedRedirectTarget) {
	if (streamedRedirectTarget === null || !isDangerousScheme(streamedRedirectTarget)) return false;
	response.body?.cancel().catch(() => {});
	reportBlockedDangerousNavigation();
	return true;
}
function toVisibleAppHref(href, origin) {
	const url = new URL(href, origin);
	stripRscCacheBustingSearchParam(url);
	return `${stripRscSuffix(url.pathname)}${url.search}${url.hash}`;
}
function toStreamedRedirectVisibleAppHref(href, origin) {
	const url = new URL(href, origin);
	return `${url.pathname}${url.search}${url.hash}`;
}
function resolveRedirectLifecycleHopFromTarget(options) {
	if (options.targetUrl.origin !== options.origin) return {
		href: options.targetUrl.href,
		kind: "terminal-hard-navigation",
		reason: "externalRedirect",
		redirectDepth: options.redirectDepth
	};
	const redirectedHref = options.redirectedHref;
	if (redirectedHref === toVisibleAppHref(options.currentHref, options.origin)) return {
		href: redirectedHref,
		kind: "no-redirect"
	};
	const maxRedirectDepth = options.maxRedirectDepth ?? MAX_RSC_REDIRECT_DEPTH;
	if (options.redirectDepth >= maxRedirectDepth) return {
		href: redirectedHref,
		kind: "terminal-hard-navigation",
		reason: "maxRedirectsExceeded",
		redirectDepth: options.redirectDepth
	};
	return {
		href: redirectedHref,
		historyUpdateMode: options.historyUpdateMode,
		kind: "follow",
		previousNextUrl: options.requestPreviousNextUrl,
		redirectDepth: options.redirectDepth + 1
	};
}
function resolveRscRedirectLifecycleHop(options) {
	const responseUrl = new URL(options.responseUrl, options.origin);
	return resolveRedirectLifecycleHopFromTarget({
		...options,
		redirectedHref: resolveHardNavigationTargetFromRscResponse(responseUrl.href, options.currentHref, options.origin),
		targetUrl: responseUrl
	});
}
function resolveStreamedRscRedirectLifecycleHop(options) {
	const streamedRedirectUrl = new URL(options.streamedRedirectTarget, options.origin);
	return resolveRedirectLifecycleHopFromTarget({
		...options,
		redirectedHref: toStreamedRedirectVisibleAppHref(options.streamedRedirectTarget, options.origin),
		targetUrl: streamedRedirectUrl
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/navigation-trace.js
var NavigationTraceReasonCodes = {
	cacheProofRejected: "NC_CACHE_REJECT",
	cacheReuseTokenRejected: "NC_CACHE_TOKEN_REJECT",
	commitCurrent: "NC_COMMIT",
	crossDocumentFlight: "NC_CROSS_DOC_FLIGHT",
	fetchFresh: "NC_FETCH_FRESH",
	invalidRscPayload: "NC_RSC_INVALID",
	interceptedCommitCurrent: "NC_INTERCEPT_COMMIT",
	interceptedRejectedIncompatibleRoot: "NC_INTERCEPT_REJECT_ROOT",
	interceptedRejectedMissingProof: "NC_INTERCEPT_REJECT_MISSING_PROOF",
	interceptedRejectedMissingSlotProof: "NC_INTERCEPT_REJECT_SLOT",
	interceptedRejectedTargetMismatch: "NC_INTERCEPT_REJECT_TARGET",
	interceptedRejectedUndeclaredTopology: "NC_INTERCEPT_REJECT_GRAPH",
	interceptedRejectedUnknownSource: "NC_INTERCEPT_REJECT_SOURCE",
	optimisticRouteShell: "NC_OPTIMISTIC_SHELL",
	prefetchOnly: "NC_PREFETCH_ONLY",
	prefetchResponseReuse: "NC_PREFETCH_REUSE",
	proceedToCommit: "NC_RSC_PROCEED",
	redirectFollow: "NC_RSC_REDIRECT_FOLLOW",
	redirectTerminalDepth: "NC_RSC_REDIRECT_DEPTH",
	redirectTerminalExternal: "NC_RSC_REDIRECT_EXTERNAL",
	requestWork: "NC_REQUEST",
	rootBoundaryChanged: "NC_ROOT",
	rootBoundaryUnknown: "NC_ROOT_UNKNOWN",
	rscCompatibilityMismatch: "NC_RSC_COMPAT_MISMATCH",
	rscNavigationError: "NC_RSC_NAV_ERROR",
	sameDocumentScroll: "NC_SAME_DOC_SCROLL",
	samePageSearch: "NC_SAME_PAGE_SEARCH",
	serverActionRedirectCompatibilityMismatch: "NC_SA_REDIRECT_COMPAT",
	serverActionRscCompatibilityMismatch: "NC_SA_RSC_COMPAT",
	staleOperation: "NC_STALE",
	streamedRedirectLoop: "NC_RSC_STREAMED_REDIRECT_LOOP",
	visitedResponseReuse: "NC_VISITED_REUSE"
};
var NavigationTraceTransactionCodes = {
	hardNavigate: "NT_HARD_NAVIGATE",
	noCommit: "NT_NO_COMMIT",
	visibleCommit: "NT_VISIBLE_COMMIT"
};
function createNavigationLifecycleTraceFields(options) {
	return {
		...options.activeNavigationId !== void 0 ? { activeNavigationId: options.activeNavigationId } : {},
		currentRootLayoutTreePath: options.currentRootLayoutTreePath,
		currentVisibleCommitVersion: options.currentVisibleCommitVersion,
		nextRootLayoutTreePath: options.nextRootLayoutTreePath,
		...options.startedNavigationId !== void 0 ? { startedNavigationId: options.startedNavigationId } : {},
		startedVisibleCommitVersion: options.startedVisibleCommitVersion
	};
}
function createNavigationTraceEntry(code, fields = {}) {
	return {
		code,
		fields: { ...fields }
	};
}
function createNavigationTrace(code, fields = {}) {
	return {
		schemaVersion: 0,
		entries: [createNavigationTraceEntry(code, fields)]
	};
}
function prependNavigationTraceEntry(trace, code, fields = {}) {
	return {
		schemaVersion: trace.schemaVersion,
		entries: [createNavigationTraceEntry(code, fields), ...trace.entries]
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/operation-token.js
var DIMENSION_ORDER = [
	"navigation",
	"visibleCommit",
	"graphVersion",
	"cacheVariant"
];
function evaluateDimension(dimension, token, authority) {
	switch (dimension) {
		case "navigation": return token.navigationId === authority.activeNavigationId ? { kind: "satisfied" } : {
			kind: "mismatch",
			reason: "staleNavigation"
		};
		case "visibleCommit": return token.baseVisibleCommitVersion === authority.visibleCommitVersion ? { kind: "satisfied" } : {
			kind: "mismatch",
			reason: "staleVisibleCommit"
		};
		case "graphVersion":
			if (token.graphVersion === null || authority.graphVersion === null) return {
				kind: "absent",
				missingReason: "graphVersionMissing"
			};
			return token.graphVersion === authority.graphVersion ? { kind: "satisfied" } : {
				kind: "mismatch",
				reason: "graphVersionMismatch"
			};
		case "cacheVariant": {
			const tokenVariant = token.cacheVariantFingerprint;
			const installedVariant = authority.installedCacheVariantFingerprint;
			if (tokenVariant === void 0 || installedVariant === null) return {
				kind: "absent",
				missingReason: "cacheVariantMissing"
			};
			return tokenVariant === installedVariant ? { kind: "satisfied" } : {
				kind: "mismatch",
				reason: "cacheVariantMismatch"
			};
		}
		default: throw new Error("[vinext] Unknown operation-token dimension: " + String(dimension));
	}
}
function verifyOperationToken(token, authority, policy) {
	const required = new Set(policy.require);
	const evaluated = /* @__PURE__ */ new Set([...policy.check, ...policy.require]);
	for (const dimension of DIMENSION_ORDER) {
		if (!evaluated.has(dimension)) continue;
		const status = evaluateDimension(dimension, token, authority);
		if (status.kind === "mismatch") return {
			authorized: false,
			reason: status.reason
		};
		if (status.kind === "absent" && required.has(dimension)) return {
			authorized: false,
			reason: status.missingReason
		};
	}
	return {
		authorized: true,
		token
	};
}
function verifyOperationTokenForCommit(token, authority) {
	return verifyOperationToken(token, {
		activeNavigationId: authority.activeNavigationId,
		visibleCommitVersion: authority.visibleCommitVersion,
		graphVersion: token.graphVersion,
		installedCacheVariantFingerprint: token.cacheVariantFingerprint ?? null
	}, {
		check: ["navigation", "visibleCommit"],
		require: ["navigation", "visibleCommit"]
	});
}
function verifyOperationTokenForCacheReuse(token, authority) {
	return verifyOperationToken(token, {
		activeNavigationId: token.navigationId,
		visibleCommitVersion: token.baseVisibleCommitVersion,
		graphVersion: authority.graphVersion,
		installedCacheVariantFingerprint: authority.installedCacheVariantFingerprint
	}, {
		check: ["graphVersion", "cacheVariant"],
		require: []
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/navigation-planner.js
function mergeRscRedirectHistoryMode(navigationMode, redirectType) {
	return navigationMode === "push" || redirectType === "push" ? "push" : "replace";
}
var ROUTE_INTERCEPTION_CONTEXT_SEPARATOR = "\0";
var CACHE_ENTRY_PROOF_MISSING_CODE = "CP_CACHE_ENTRY_PROOF_MISSING";
function createRequestWorkDecision(options) {
	const traverseFields = options.work.kind === "traverseFlight" ? { traverseDirection: options.work.direction } : {};
	return {
		kind: "requestWork",
		token: options.state.nextOperationToken,
		work: options.work,
		trace: createNavigationTrace(NavigationTraceReasonCodes.requestWork, {
			eventKind: options.eventKind,
			targetHref: getRequestedWorkTargetHref(options.work),
			...traverseFields
		})
	};
}
function getRequestedWorkTargetHref(work) {
	switch (work.kind) {
		case "flight":
		case "prefetch": return work.href;
		case "traverseFlight": return null;
		default: throw new Error("[vinext] Unknown requested navigation work: " + String(work));
	}
}
function createRscFetchResultTraceFields(facts, fields = {}) {
	return {
		fetchResultSource: facts.source,
		...fields
	};
}
function createRscFetchResultHardNavigationDecision(options) {
	return {
		discardBody: options.discardBody,
		kind: "hardNavigate",
		...options.hardNavigationMode !== void 0 ? { hardNavigationMode: options.hardNavigationMode } : {},
		reason: options.reason,
		trace: createNavigationTrace(options.reasonCode, createRscFetchResultTraceFields(options.facts, {
			...options.redirectSignal !== void 0 ? { redirectSignal: options.redirectSignal } : {},
			redirectDepth: options.facts.redirectDepth,
			targetHref: options.url
		})),
		url: options.url
	};
}
function createRscFetchResultFollowRedirectDecision(options) {
	return {
		discardBody: options.discardBody,
		kind: "followRedirect",
		redirect: options.redirect,
		trace: createNavigationTrace(NavigationTraceReasonCodes.redirectFollow, createRscFetchResultTraceFields(options.facts, {
			redirectDepth: options.redirect.redirectDepth,
			redirectSignal: options.redirectSignal,
			targetHref: options.redirect.href
		}))
	};
}
function mapRscRedirectTerminalReason(reason) {
	switch (reason) {
		case "externalRedirect": return {
			hardNavigationReason: "externalRedirectTarget",
			traceReasonCode: NavigationTraceReasonCodes.redirectTerminalExternal
		};
		case "maxRedirectsExceeded": return {
			hardNavigationReason: "redirectDepthExhausted",
			traceReasonCode: NavigationTraceReasonCodes.redirectTerminalDepth
		};
		default: throw new Error("[vinext] Unknown RSC redirect terminal reason: " + String(reason));
	}
}
function classifyRscFetchResult(facts) {
	if (!facts.responseOk || !facts.isRscContentType || !facts.hasBody) {
		const url = resolveHardNavigationTargetFromRscResponse(facts.responseUrl, facts.currentHref, facts.origin);
		return createRscFetchResultHardNavigationDecision({
			discardBody: false,
			facts,
			reason: "invalidRscPayload",
			reasonCode: NavigationTraceReasonCodes.invalidRscPayload,
			url
		});
	}
	const compatibilityDecision = resolveRscCompatibilityNavigationDecision({
		clientCompatibilityId: facts.clientCompatibilityId,
		currentHref: facts.currentHref,
		origin: facts.origin,
		responseCompatibilityId: facts.compatibilityIdHeader,
		responseUrl: facts.responseUrl
	});
	if (compatibilityDecision.kind === "hard-navigate") return createRscFetchResultHardNavigationDecision({
		discardBody: false,
		facts,
		reason: "rscCompatibilityMismatch",
		reasonCode: NavigationTraceReasonCodes.rscCompatibilityMismatch,
		url: compatibilityDecision.hardNavigationTarget
	});
	if (facts.responseUrl !== null) {
		const redirectDecision = resolveRscRedirectLifecycleHop({
			currentHref: facts.currentHref,
			historyUpdateMode: facts.effectiveHistoryUpdateMode,
			origin: facts.origin,
			redirectDepth: facts.redirectDepth,
			requestPreviousNextUrl: facts.requestPreviousNextUrl,
			responseUrl: facts.responseUrl
		});
		if (redirectDecision.kind === "terminal-hard-navigation") {
			const terminalReason = mapRscRedirectTerminalReason(redirectDecision.reason);
			return createRscFetchResultHardNavigationDecision({
				discardBody: false,
				facts,
				reason: terminalReason.hardNavigationReason,
				reasonCode: terminalReason.traceReasonCode,
				redirectSignal: "response-url",
				url: redirectDecision.href
			});
		}
		if (redirectDecision.kind === "follow") return createRscFetchResultFollowRedirectDecision({
			discardBody: false,
			facts,
			redirect: {
				href: redirectDecision.href,
				historyUpdateMode: facts.effectiveHistoryUpdateMode,
				previousNextUrl: redirectDecision.previousNextUrl,
				redirectDepth: redirectDecision.redirectDepth
			},
			redirectSignal: "response-url"
		});
	}
	if (facts.streamedRedirectTarget !== null) {
		const streamedHistoryMode = mergeRscRedirectHistoryMode(facts.effectiveHistoryUpdateMode, facts.streamedRedirectType);
		const redirectDecision = resolveStreamedRscRedirectLifecycleHop({
			currentHref: facts.currentHref,
			historyUpdateMode: streamedHistoryMode,
			origin: facts.origin,
			redirectDepth: facts.redirectDepth,
			requestPreviousNextUrl: facts.requestPreviousNextUrl,
			streamedRedirectTarget: facts.streamedRedirectTarget
		});
		if (redirectDecision.kind === "terminal-hard-navigation") {
			const terminalReason = mapRscRedirectTerminalReason(redirectDecision.reason);
			return createRscFetchResultHardNavigationDecision({
				discardBody: true,
				facts,
				reason: terminalReason.hardNavigationReason,
				reasonCode: terminalReason.traceReasonCode,
				redirectSignal: "streamed-header",
				hardNavigationMode: streamedHistoryMode === "push" ? "assign" : "replace",
				url: redirectDecision.href
			});
		}
		if (redirectDecision.kind === "follow") return createRscFetchResultFollowRedirectDecision({
			discardBody: true,
			facts,
			redirect: {
				href: redirectDecision.href,
				historyUpdateMode: streamedHistoryMode,
				previousNextUrl: redirectDecision.previousNextUrl,
				redirectDepth: redirectDecision.redirectDepth
			},
			redirectSignal: "streamed-header"
		});
		return createRscFetchResultHardNavigationDecision({
			discardBody: true,
			facts,
			reason: "streamedRedirectLoop",
			reasonCode: NavigationTraceReasonCodes.streamedRedirectLoop,
			redirectSignal: "streamed-header",
			url: redirectDecision.href
		});
	}
	return {
		discardBody: false,
		kind: "proceedToCommit",
		trace: createNavigationTrace(NavigationTraceReasonCodes.proceedToCommit, createRscFetchResultTraceFields(facts))
	};
}
function createEarlyNavigationIntentTrace(reasonCode, facts) {
	return createNavigationTrace(reasonCode, { targetHref: facts.targetHref });
}
function classifyEarlyNavigationIntent(facts) {
	let current;
	let next;
	try {
		current = new URL(facts.currentHref);
		next = new URL(facts.targetHref, facts.currentHref);
	} catch {
		return {
			bypassNavigationCache: false,
			kind: "flightNavigation",
			trace: createEarlyNavigationIntentTrace(NavigationTraceReasonCodes.crossDocumentFlight, facts)
		};
	}
	const samePathname = current.origin === next.origin && stripBasePath(current.pathname, facts.basePath) === stripBasePath(next.pathname, facts.basePath);
	const sameSearch = current.searchParams.toString() === next.searchParams.toString();
	if (samePathname && sameSearch && next.hash !== "") return {
		hash: next.hash,
		kind: "sameDocumentScroll",
		mode: facts.mode,
		scroll: facts.scroll,
		trace: createEarlyNavigationIntentTrace(NavigationTraceReasonCodes.sameDocumentScroll, facts)
	};
	if (samePathname && !sameSearch) return {
		bypassNavigationCache: true,
		kind: "flightNavigation",
		trace: createEarlyNavigationIntentTrace(NavigationTraceReasonCodes.samePageSearch, facts)
	};
	return {
		bypassNavigationCache: false,
		kind: "flightNavigation",
		trace: createEarlyNavigationIntentTrace(NavigationTraceReasonCodes.crossDocumentFlight, facts)
	};
}
function classifyVisitedResponseCacheCandidate(facts) {
	if (facts.candidate === "missing") return { kind: "miss" };
	if (!facts.mountedSlotsMatch) return {
		kind: "evict",
		reason: "mountedSlotsMismatch"
	};
	if (facts.navigationKind === "refresh") return {
		kind: "evict",
		reason: "refresh"
	};
	if (!facts.fresh) return {
		kind: "evict",
		reason: "stale"
	};
	return { kind: "reuse" };
}
function createNavigationReuseTrace(code, facts, fields = {}) {
	return createNavigationTrace(code, {
		eventKind: facts.navigationKind,
		targetHref: facts.targetHref,
		...fields
	});
}
function createFreshFetchDecision(facts, reason) {
	return {
		kind: "fetchFresh",
		reason,
		trace: createNavigationReuseTrace(NavigationTraceReasonCodes.fetchFresh, facts, { freshFetchReason: reason })
	};
}
function classifyNavigationReuse(facts) {
	if (facts.navigationKind === "refresh") return createFreshFetchDecision(facts, "refresh");
	if (!facts.bypassNavigationCache && facts.visitedResponse.status === "available") return {
		kind: "reuseVisitedResponse",
		trace: createNavigationReuseTrace(NavigationTraceReasonCodes.visitedResponseReuse, facts)
	};
	if (!facts.bypassNavigationCache && facts.prefetch.status === "available") return {
		kind: "consumePrefetch",
		trace: createNavigationReuseTrace(NavigationTraceReasonCodes.prefetchResponseReuse, facts)
	};
	if (facts.navigationKind === "navigate") {
		if (facts.optimisticRouteShell.status === "available") return {
			kind: "attemptOptimisticRouteShell",
			trace: createNavigationReuseTrace(NavigationTraceReasonCodes.optimisticRouteShell, facts)
		};
		return createFreshFetchDecision(facts, facts.bypassNavigationCache ? "cacheBypassed" : facts.optimisticRouteShell.reason);
	}
	if (facts.bypassNavigationCache) return createFreshFetchDecision(facts, "cacheBypassed");
	return createFreshFetchDecision(facts, "cacheMiss");
}
function classifyNavigationPrefetchProbe(facts) {
	if (facts.visitedResponse.status === "available") return {
		kind: "skip",
		reason: "visitedResponseAvailable"
	};
	if (facts.navigationKind === "refresh") return {
		kind: "skip",
		reason: "refresh"
	};
	if (facts.bypassNavigationCache) return {
		kind: "skip",
		reason: "cacheBypassed"
	};
	return { kind: "probe" };
}
function createSnapshotRouteTopology(snapshot) {
	return {
		layoutIds: snapshot.layoutIds,
		rootBoundaryId: snapshot.rootBoundaryId,
		rootLayoutTreePath: snapshot.rootBoundaryId,
		slotBindings: snapshot.slotBindings
	};
}
function stripInterceptionContextFromRouteId(routeId) {
	const separatorIndex = routeId.indexOf(ROUTE_INTERCEPTION_CONTEXT_SEPARATOR);
	return separatorIndex === -1 ? routeId : routeId.slice(0, separatorIndex);
}
function matchedUrlFromConcreteRouteId(routeId) {
	const normalizedRouteId = stripInterceptionContextFromRouteId(routeId);
	if (!normalizedRouteId.startsWith("route:/")) return null;
	return normalizedRouteId.slice(6);
}
function getMatchedUrlPathname(matchedUrl) {
	try {
		return new URL(matchedUrl, "https://vinext.local").pathname;
	} catch {
		const [withoutHash = ""] = matchedUrl.split("#");
		const [pathname = ""] = withoutHash.split("?");
		return pathname === "" ? "/" : pathname;
	}
}
function splitMatchedUrlIntoRouteParts(matchedUrl) {
	return splitPathnameForRouteMatch(getMatchedUrlPathname(matchedUrl));
}
function findRouteManifestRouteByMatchedUrl(routeManifest, matchedUrl) {
	const urlParts = splitMatchedUrlIntoRouteParts(matchedUrl);
	for (const route of routeManifest.segmentGraph.routes.values()) if (matchRoutePattern(urlParts, route.patternParts) !== null) return route;
	return null;
}
function routeManifestRouteMatchesUrl(route, matchedUrl) {
	return matchRoutePattern(splitMatchedUrlIntoRouteParts(matchedUrl), route.patternParts) !== null;
}
function findRouteManifestRouteByIdOrMatchedUrl(options) {
	const routeId = stripInterceptionContextFromRouteId(options.routeId);
	const route = options.routeManifest.segmentGraph.routes.get(routeId);
	if (route && routeManifestRouteMatchesUrl(route, options.matchedUrl)) return route;
	const concreteRouteMatchedUrl = route === void 0 ? matchedUrlFromConcreteRouteId(options.routeId) : null;
	if (concreteRouteMatchedUrl !== null) {
		const concreteRoute = findRouteManifestRouteByMatchedUrl(options.routeManifest, concreteRouteMatchedUrl);
		if (concreteRoute !== null) return concreteRoute;
	}
	return findRouteManifestRouteByMatchedUrl(options.routeManifest, options.matchedUrl);
}
function findRouteManifestRouteForSnapshot(routeManifest, snapshot) {
	if (snapshot.interception !== null) return findRouteManifestRouteByIdOrMatchedUrl({
		matchedUrl: snapshot.interception.sourceMatchedUrl,
		routeId: snapshot.interception.sourceRouteId,
		routeManifest
	});
	return findRouteManifestRouteByIdOrMatchedUrl({
		matchedUrl: snapshot.matchedUrl,
		routeId: snapshot.routeId,
		routeManifest
	});
}
function resolveRouteManifestSlotBindings(routeManifest, route) {
	const bindings = [];
	for (const slotId of route.slotIds) {
		const binding = routeManifest.segmentGraph.slotBindings.get(`${route.id}::${slotId}`);
		if (!binding) continue;
		bindings.push({
			ownerLayoutId: binding.ownerLayoutId,
			slotId: binding.slotId,
			state: binding.state
		});
	}
	return bindings.sort((left, right) => compareAppElementsSlotIds(left.slotId, right.slotId));
}
function resolveRouteManifestRootLayoutTreePath(routeManifest, route) {
	if (route.rootBoundaryId === null) return null;
	return routeManifest.segmentGraph.rootBoundaries.get(route.rootBoundaryId)?.treePath ?? null;
}
function resolveRouteTopologySnapshot(options) {
	const route = options.routeManifest === null ? null : findRouteManifestRouteForSnapshot(options.routeManifest, options.snapshot);
	if (route === null || options.routeManifest === null) return { kind: "unknown" };
	const shouldUseManifestSlotBindings = options.slotBindingSource === "manifestTarget" && options.snapshot.interception === null;
	return {
		kind: "known",
		topology: {
			layoutIds: route.layoutIds,
			rootBoundaryId: route.rootBoundaryId,
			rootLayoutTreePath: resolveRouteManifestRootLayoutTreePath(options.routeManifest, route),
			slotBindings: shouldUseManifestSlotBindings ? resolveRouteManifestSlotBindings(options.routeManifest, route) : options.snapshot.slotBindings
		}
	};
}
function findRouteManifestInterceptionForProof(routeManifest, proof) {
	const sourceParts = splitMatchedUrlIntoRouteParts(proof.sourceMatchedUrl);
	const targetParts = splitMatchedUrlIntoRouteParts(proof.targetMatchedUrl);
	const targetRoute = findRouteManifestRouteByIdOrMatchedUrl({
		matchedUrl: proof.targetMatchedUrl,
		routeId: proof.targetRouteId,
		routeManifest
	});
	const candidateInterceptions = routeManifest.segmentGraph.interceptionsBySlotId.get(proof.slotId) ?? [];
	for (const interception of candidateInterceptions) {
		if (!matchRoutePatternPrefix(sourceParts, interception.sourcePatternParts)) continue;
		const exactTargetParams = matchRoutePattern(targetParts, interception.targetPatternParts);
		const allowsMiddlewareRewriteTarget = exactTargetParams === null && matchRoutePatternWithOptionalDynamicSegments(targetParts, interception.targetPatternParts);
		if (exactTargetParams === null && !allowsMiddlewareRewriteTarget) continue;
		if (!allowsMiddlewareRewriteTarget && interception.targetRouteId !== null && targetRoute?.id !== interception.targetRouteId) continue;
		return interception;
	}
	return null;
}
function createRootBoundaryTraceFields(options) {
	if (options.state.traceFields) return {
		...options.state.traceFields,
		currentRootLayoutTreePath: options.currentRootLayoutTreePath,
		nextRootLayoutTreePath: options.nextRootLayoutTreePath
	};
	return createNavigationLifecycleTraceFields({
		currentRootLayoutTreePath: options.currentRootLayoutTreePath,
		currentVisibleCommitVersion: options.state.visibleCommitVersion,
		nextRootLayoutTreePath: options.nextRootLayoutTreePath,
		startedVisibleCommitVersion: options.event.token.baseVisibleCommitVersion
	});
}
function classifyRootBoundaryTransition(currentRootBoundaryId, nextRootBoundaryId) {
	if (currentRootBoundaryId === null || nextRootBoundaryId === null) return "rootBoundaryUnknown";
	return currentRootBoundaryId === nextRootBoundaryId ? "currentRootBoundary" : "rootBoundaryChanged";
}
function resolveSameLayoutAncestorPersistence(currentSnapshot, targetSnapshot) {
	return resolveSameLayoutAncestorPersistenceForTopologies(createSnapshotRouteTopology(currentSnapshot), createSnapshotRouteTopology(targetSnapshot));
}
function resolveSameLayoutAncestorPersistenceForTopologies(currentTopology, targetTopology) {
	if (classifyRootBoundaryTransition(currentTopology.rootBoundaryId, targetTopology.rootBoundaryId) !== "currentRootBoundary") return [];
	const commonLayoutIds = [];
	const maxLength = Math.min(currentTopology.layoutIds.length, targetTopology.layoutIds.length);
	for (let index = 0; index < maxLength; index++) {
		const layoutId = currentTopology.layoutIds[index];
		if (layoutId !== targetTopology.layoutIds[index]) break;
		commonLayoutIds.push(layoutId);
	}
	return commonLayoutIds;
}
function resolveMountedParallelSlotPersistence(currentSnapshot, targetSnapshot) {
	return resolveMountedParallelSlotPersistenceForLayouts(currentSnapshot, resolveSameLayoutAncestorPersistence(currentSnapshot, targetSnapshot));
}
function resolveMountedParallelSlotPersistenceForLayouts(currentSnapshot, preservedLayoutIds) {
	if (preservedLayoutIds.length === 0) return [];
	const preservedLayoutIdSet = new Set(preservedLayoutIds);
	const preservedSlotIds = [];
	const seenSlotIds = /* @__PURE__ */ new Set();
	for (const slot of currentSnapshot.mountedParallelSlots) {
		if (slot.ownerLayoutId === null) continue;
		if (!preservedLayoutIdSet.has(slot.ownerLayoutId)) continue;
		if (seenSlotIds.has(slot.slotId)) continue;
		preservedSlotIds.push(slot.slotId);
		seenSlotIds.add(slot.slotId);
	}
	return preservedSlotIds;
}
function resolveCurrentRootBoundaryElementPersistence(currentSnapshot, targetSnapshot) {
	const preservedLayoutIds = resolveSameLayoutAncestorPersistence(currentSnapshot, targetSnapshot);
	return [...preservedLayoutIds, ...resolveMountedParallelSlotPersistenceForLayouts(currentSnapshot, preservedLayoutIds)];
}
function resolveCurrentRootBoundaryCommitElementPersistence(options) {
	return resolveSameLayoutAncestorPersistenceForTopologies(options.currentTopology, options.targetTopology);
}
function resolveCurrentRootBoundaryCommitSlotPersistence(options) {
	if (options.lane === "traverse") return [];
	const preservedLayoutIds = resolveSameLayoutAncestorPersistenceForTopologies(options.currentTopology, options.targetTopology);
	if (preservedLayoutIds.length === 0) return [];
	return resolveDefaultOrUnmatchedSlotPersistenceForLayouts({
		currentSlotBindings: options.currentTopology.slotBindings,
		preservedLayoutIds,
		targetSlotBindings: options.targetTopology.slotBindings
	});
}
/**
* Default/unmatched slot preservation law:
*
* A target default/unmatched slot may reuse previous content only when:
* - the slot's owner layout is part of the preserved layout ancestor set;
* - the current visible snapshot proves the same slot had renderable content;
* - the navigation is not a traversal.
*
* Wire absence and UNMATCHED_SLOT markers are not semantic proof.
*/
function resolveDefaultOrUnmatchedSlotPersistenceForLayouts(options) {
	const preservedLayoutIdSet = new Set(options.preservedLayoutIds);
	const slotIdsWithContent = /* @__PURE__ */ new Set();
	for (const binding of options.currentSlotBindings) {
		if (binding.state === "unmatched") continue;
		slotIdsWithContent.add(binding.slotId);
	}
	const preservedSlotIds = [];
	const seenSlotIds = /* @__PURE__ */ new Set();
	for (const binding of options.targetSlotBindings) {
		if (binding.ownerLayoutId === null) continue;
		if (!preservedLayoutIdSet.has(binding.ownerLayoutId)) continue;
		if (binding.state === "active") continue;
		if (!slotIdsWithContent.has(binding.slotId)) continue;
		if (seenSlotIds.has(binding.slotId)) continue;
		preservedSlotIds.push(binding.slotId);
		seenSlotIds.add(binding.slotId);
	}
	return preservedSlotIds.sort(compareAppElementsSlotIds);
}
function getVisibleInterceptionSourceIdentity(snapshot) {
	if (snapshot.interception) return {
		matchedUrl: snapshot.interception.sourceMatchedUrl,
		routeId: snapshot.interception.sourceRouteId
	};
	return {
		matchedUrl: matchedUrlFromConcreteRouteId(snapshot.routeId) ?? snapshot.matchedUrl,
		routeId: snapshot.routeId
	};
}
function createInterceptionProofRejectedDecision(options) {
	return {
		kind: "hardNavigate",
		reason: "interceptionProofRejected",
		token: options.event.token,
		trace: createNavigationTrace(options.reasonCode, options.traceFields),
		url: options.event.result.href
	};
}
function evaluateCacheEntryReuseProof(proof) {
	if (proof === void 0) return {
		kind: "accepted",
		decision: null
	};
	if (proof.decision === null) return {
		kind: "rejected",
		decision: null
	};
	if (proof.decision.canReuse) return {
		kind: "accepted",
		decision: proof.decision
	};
	return {
		kind: "rejected",
		decision: proof.decision
	};
}
function createCacheProofRejectedTraceFields(traceFields, decision) {
	if (decision === null) return {
		...traceFields,
		cacheProofCode: CACHE_ENTRY_PROOF_MISSING_CODE
	};
	return {
		...traceFields,
		cacheProofCode: decision.code,
		cacheProofMode: decision.mode,
		cacheProofScope: decision.scope
	};
}
function createCacheProofRejectedDecision(options) {
	return {
		kind: "hardNavigate",
		reason: "cacheProofRejected",
		token: options.event.token,
		trace: createNavigationTrace(NavigationTraceReasonCodes.cacheProofRejected, createCacheProofRejectedTraceFields(options.traceFields, options.rejection.decision)),
		url: options.event.result.href
	};
}
function createCacheReuseTokenRejectedDecision(options) {
	return {
		kind: "hardNavigate",
		reason: "cacheReuseTokenRejected",
		token: options.event.token,
		trace: createNavigationTrace(NavigationTraceReasonCodes.cacheReuseTokenRejected, {
			...options.traceFields,
			cacheReuseTokenReason: options.reason
		}),
		url: options.event.result.href
	};
}
function createAcceptedCacheProofTraceFields(traceFields, decision) {
	if (decision === null) return traceFields;
	return {
		...traceFields,
		cacheProofCode: decision.code,
		cacheProofReuseClass: decision.reuseClass
	};
}
function createCacheEntryProposalFields(decision) {
	if (decision === null) return {};
	return { cacheEntryReuseDecision: decision };
}
function validateInterceptedPreservation(options) {
	const proof = options.targetSnapshot.interception;
	if (!proof) return {
		kind: "rejected",
		reasonCode: NavigationTraceReasonCodes.interceptedRejectedMissingProof
	};
	if (proof.targetMatchedUrl !== options.targetSnapshot.matchedUrl) return {
		kind: "rejected",
		reasonCode: NavigationTraceReasonCodes.interceptedRejectedTargetMismatch
	};
	const sourceIdentity = getVisibleInterceptionSourceIdentity(options.currentSnapshot);
	if (!options.restoredHistorySnapshot && (proof.sourceMatchedUrl !== sourceIdentity.matchedUrl || proof.sourceRouteId !== sourceIdentity.routeId)) return {
		kind: "rejected",
		reasonCode: NavigationTraceReasonCodes.interceptedRejectedUnknownSource
	};
	const declaredInterception = options.routeManifest === null ? null : findRouteManifestInterceptionForProof(options.routeManifest, proof);
	if (options.routeManifest !== null && declaredInterception === null) return {
		kind: "rejected",
		reasonCode: NavigationTraceReasonCodes.interceptedRejectedUndeclaredTopology
	};
	const preservedLayoutIds = resolveSameLayoutAncestorPersistenceForTopologies(options.currentTopology, options.targetTopology);
	if (preservedLayoutIds.length === 0) return {
		kind: "rejected",
		reasonCode: NavigationTraceReasonCodes.interceptedRejectedIncompatibleRoot
	};
	const preservedLayoutIdSet = new Set(preservedLayoutIds);
	const targetSlotBinding = options.targetTopology.slotBindings.find((binding) => binding.slotId === proof.slotId);
	if (!targetSlotBinding || targetSlotBinding.state !== "active" || targetSlotBinding.ownerLayoutId === null || !preservedLayoutIdSet.has(targetSlotBinding.ownerLayoutId)) return {
		kind: "rejected",
		reasonCode: NavigationTraceReasonCodes.interceptedRejectedMissingSlotProof
	};
	if (declaredInterception !== null && targetSlotBinding.ownerLayoutId !== declaredInterception.ownerLayoutId) return {
		kind: "rejected",
		reasonCode: NavigationTraceReasonCodes.interceptedRejectedUndeclaredTopology
	};
	return {
		kind: "approved",
		preserveElementIds: preservedLayoutIds,
		preservePreviousSlotIds: resolveDefaultOrUnmatchedSlotPersistenceForLayouts({
			currentSlotBindings: options.currentTopology.slotBindings,
			preservedLayoutIds,
			targetSlotBindings: options.targetTopology.slotBindings
		}).filter((slotId) => slotId !== proof.slotId)
	};
}
function planFlightResponseArrived(options) {
	const targetSnapshot = options.event.result.targetSnapshot;
	const currentTopology = resolveRouteTopologySnapshot({
		routeManifest: options.routeManifest,
		slotBindingSource: "snapshot",
		snapshot: options.state.visibleSnapshot
	});
	const targetTopology = resolveRouteTopologySnapshot({
		routeManifest: options.routeManifest,
		slotBindingSource: "manifestTarget",
		snapshot: targetSnapshot
	});
	const traceFields = createRootBoundaryTraceFields({
		currentRootLayoutTreePath: currentTopology.kind === "known" ? currentTopology.topology.rootLayoutTreePath : null,
		event: options.event,
		nextRootLayoutTreePath: targetTopology.kind === "known" ? targetTopology.topology.rootLayoutTreePath : null,
		state: options.state
	});
	if (options.event.token.lane === "prefetch") return {
		kind: "noCommit",
		reason: "prefetchOnly",
		token: options.event.token,
		trace: createNavigationTrace(NavigationTraceReasonCodes.prefetchOnly, traceFields)
	};
	const cacheEntryProofEvaluation = evaluateCacheEntryReuseProof(options.event.result.cacheEntryReuseProof);
	if (cacheEntryProofEvaluation.kind === "rejected") return createCacheProofRejectedDecision({
		event: options.event,
		rejection: cacheEntryProofEvaluation,
		traceFields
	});
	const acceptedCacheEntryDecision = cacheEntryProofEvaluation.decision;
	if (acceptedCacheEntryDecision !== null) {
		const reuseVerdict = verifyOperationTokenForCacheReuse(options.event.token, {
			graphVersion: options.routeManifest?.graphVersion ?? null,
			installedCacheVariantFingerprint: null
		});
		if (!reuseVerdict.authorized) return createCacheReuseTokenRejectedDecision({
			event: options.event,
			reason: reuseVerdict.reason,
			traceFields
		});
	}
	const commitTraceFields = createAcceptedCacheProofTraceFields(traceFields, acceptedCacheEntryDecision);
	const cacheEntryProposalFields = createCacheEntryProposalFields(acceptedCacheEntryDecision);
	if (targetSnapshot.interception !== null) {
		if (currentTopology.kind === "unknown" || targetTopology.kind === "unknown") return createInterceptionProofRejectedDecision({
			event: options.event,
			reasonCode: NavigationTraceReasonCodes.interceptedRejectedUndeclaredTopology,
			traceFields: commitTraceFields
		});
		const validation = validateInterceptedPreservation({
			currentSnapshot: options.state.visibleSnapshot,
			currentTopology: currentTopology.topology,
			restoredHistorySnapshot: options.event.result.restoredHistorySnapshot === true,
			routeManifest: options.routeManifest,
			targetSnapshot,
			targetTopology: targetTopology.topology
		});
		if (validation.kind === "rejected") return createInterceptionProofRejectedDecision({
			event: options.event,
			reasonCode: validation.reasonCode,
			traceFields: commitTraceFields
		});
		return {
			kind: "proposeCommit",
			proposal: {
				...cacheEntryProposalFields,
				preserveAbsentSlots: false,
				preserveElementIds: validation.preserveElementIds,
				preservePreviousSlotIds: validation.preservePreviousSlotIds,
				reason: "interceptedCurrentRootBoundary",
				targetSnapshot
			},
			token: options.event.token,
			trace: createNavigationTrace(NavigationTraceReasonCodes.interceptedCommitCurrent, commitTraceFields)
		};
	}
	const transition = currentTopology.kind === "unknown" || targetTopology.kind === "unknown" ? "rootBoundaryUnknown" : classifyRootBoundaryTransition(currentTopology.topology.rootBoundaryId, targetTopology.topology.rootBoundaryId);
	if (transition === "rootBoundaryChanged") return {
		kind: "hardNavigate",
		reason: "rootBoundaryChanged",
		token: options.event.token,
		trace: createNavigationTrace(NavigationTraceReasonCodes.rootBoundaryChanged, commitTraceFields),
		url: options.event.result.href
	};
	if (transition === "rootBoundaryUnknown") return {
		kind: "proposeCommit",
		proposal: {
			...cacheEntryProposalFields,
			preserveAbsentSlots: false,
			preserveElementIds: [],
			preservePreviousSlotIds: [],
			reason: "unprovenTopologyFallback",
			targetSnapshot
		},
		token: options.event.token,
		trace: createNavigationTrace(NavigationTraceReasonCodes.rootBoundaryUnknown, commitTraceFields)
	};
	if (currentTopology.kind !== "known" || targetTopology.kind !== "known") throw new Error("[vinext] Current-root navigation planning requires manifest topology");
	return {
		kind: "proposeCommit",
		proposal: {
			...cacheEntryProposalFields,
			preserveAbsentSlots: false,
			preserveElementIds: resolveCurrentRootBoundaryCommitElementPersistence({
				currentTopology: currentTopology.topology,
				lane: options.event.token.lane,
				targetTopology: targetTopology.topology
			}),
			preservePreviousSlotIds: resolveCurrentRootBoundaryCommitSlotPersistence({
				currentTopology: currentTopology.topology,
				lane: options.event.token.lane,
				targetTopology: targetTopology.topology
			}),
			reason: "currentRootBoundary",
			targetSnapshot
		},
		token: options.event.token,
		trace: createNavigationTrace(NavigationTraceReasonCodes.commitCurrent, commitTraceFields)
	};
}
function planNavigation(input) {
	switch (input.event.kind) {
		case "navigate": return createRequestWorkDecision({
			eventKind: input.event.kind,
			state: input.state,
			work: {
				href: input.event.href,
				kind: "flight",
				mode: input.event.mode
			}
		});
		case "refresh": return createRequestWorkDecision({
			eventKind: input.event.kind,
			state: input.state,
			work: {
				href: input.state.visibleSnapshot.displayUrl,
				kind: "flight",
				mode: "refresh"
			}
		});
		case "traverse": return createRequestWorkDecision({
			eventKind: input.event.kind,
			state: input.state,
			work: {
				direction: input.event.direction,
				historyState: input.event.historyState,
				kind: "traverseFlight"
			}
		});
		case "prefetch": return createRequestWorkDecision({
			eventKind: input.event.kind,
			state: input.state,
			work: {
				href: input.event.href,
				kind: "prefetch"
			}
		});
		case "flightResponseArrived": return planFlightResponseArrived({
			event: input.event,
			routeManifest: input.routeManifest,
			state: input.state
		});
		default: {
			const _exhaustive = input.event;
			throw new Error("[vinext] Unknown navigation event: " + String(_exhaustive));
		}
	}
}
function classifyServerActionResult(facts) {
	if (facts.clientCompatibilityId === null) return {
		kind: "proceed",
		trace: createNavigationTrace(NavigationTraceReasonCodes.proceedToCommit, {})
	};
	if (!facts.isRscContentType) return {
		kind: "proceed",
		trace: createNavigationTrace(NavigationTraceReasonCodes.proceedToCommit, {})
	};
	if (resolveRscCompatibilityNavigationDecision({
		clientCompatibilityId: facts.clientCompatibilityId,
		currentHref: facts.currentHref,
		origin: facts.origin,
		responseCompatibilityId: facts.compatibilityIdHeader,
		responseUrl: facts.responseUrl
	}).kind === "compatible") return {
		kind: "proceed",
		trace: createNavigationTrace(NavigationTraceReasonCodes.proceedToCommit, {})
	};
	if (facts.actionRedirectHref !== null) return {
		kind: "hardNavigate",
		url: facts.actionRedirectHref,
		historyMode: facts.actionRedirectType === "push" ? "assign" : "replace",
		clearClientNavigationCaches: true,
		reason: "serverActionRedirectCompatibilityMismatch",
		trace: createNavigationTrace(NavigationTraceReasonCodes.serverActionRedirectCompatibilityMismatch, { targetHref: facts.actionRedirectHref })
	};
	const targetUrl = facts.currentHref;
	return {
		kind: "hardNavigate",
		url: targetUrl,
		clearClientNavigationCaches: false,
		reason: "serverActionRscCompatibilityMismatch",
		trace: createNavigationTrace(NavigationTraceReasonCodes.serverActionRscCompatibilityMismatch, { targetHref: targetUrl })
	};
}
function classifyRscNavigationError(facts) {
	return {
		kind: "hardNavigate",
		url: facts.currentHref,
		reason: "rscNavigationError",
		trace: createNavigationTrace(NavigationTraceReasonCodes.rscNavigationError, { targetHref: facts.currentHref })
	};
}
var navigationPlanner = {
	classifyEarlyNavigationIntent,
	classifyNavigationPrefetchProbe,
	classifyNavigationReuse,
	classifyRscFetchResult,
	classifyRscNavigationError,
	classifyRootBoundaryTransition,
	classifyServerActionResult,
	classifyVisitedResponseCacheCandidate,
	plan: planNavigation,
	resolveCurrentRootBoundaryElementPersistence,
	resolveMountedParallelSlotPersistence,
	resolveSameLayoutAncestorPersistence
};
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/external-url.js
/** Detect an absolute URL with any scheme, or a protocol-relative URL. */
function isExternalUrl(url) {
	return /^[a-z][a-z0-9+.-]*:/i.test(url) || url.startsWith("//");
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/routing/route-trie.js
function createNode$1() {
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
function buildRouteTrie$1(routes) {
	const root = createNode$1();
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
					node: createNode$1()
				};
				node = node.dynamicChild.node;
				if (i === parts.length - 1) {
					if (node.route === null) node.route = route;
				}
				continue;
			}
			let child = node.staticChildren.get(part);
			if (!child) {
				child = createNode$1();
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
/**
* Match a URL against the trie.
*
* Returns decoded param values — `decodeURIComponent` is applied to
* individual param entries so that `%2F` → `/`, `%23` → `#`, etc.
* Segment boundaries (the original `/` splits) are preserved by the
* upstream normalization layer; this step only decodes the captured
* param strings the caller sees.
*
* Mirrors Next.js route-matcher.ts:25-27.
*
* @param root - Trie root built by `buildRouteTrie`
* @param urlParts - Pre-split URL segments (no empty strings)
* @returns Match result with route and extracted params, or null
*/
function trieMatch(root, urlParts) {
	const result = trieMatchRaw(root, urlParts);
	if (result) decodeMatchedParams(result.params);
	return result;
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
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/routing/route-matching.js
/**
* Shared route-match preamble used by both Pages Router and App Router.
*
* Both routers normalize URLs and call `trieMatch` with nearly-identical
* preamble: strip query, trailing-slash normalize, run
* `normalizePathnameForRouteMatch`, split into url parts, then look up via a
* per-routes-array trie cache. This module factors that out so each router
* just calls `matchRouteWithTrie(url, routes)`.
*/
function createRouteTrieCache() {
	return /* @__PURE__ */ new WeakMap();
}
function getOrBuildTrie(cache, routes) {
	let trie = cache.get(routes);
	if (!trie) {
		trie = buildRouteTrie$1(routes);
		cache.set(routes, trie);
	}
	return trie;
}
/**
* Match a URL path against a list of routes via the shared preamble:
*   1. strip query string
*   2. trailing-slash normalize (preserving root "/")
*   3. run `normalizePathnameForRouteMatch`
*   4. split into url parts and look up via the (cached) trie
*
* Generic over the route shape; both Pages `Route` and App `AppRoute`
* satisfy `{ patternParts: string[] }`.
*/
function matchRouteWithTrie(url, routes, cache) {
	const pathname = url.split("?")[0];
	let normalizedUrl = pathname === "/" ? "/" : pathname.replace(/\/$/, "");
	normalizedUrl = normalizePathnameForRouteMatch(normalizedUrl);
	const urlParts = normalizedUrl.split("/").filter(Boolean);
	return trieMatch(getOrBuildTrie(cache, routes), urlParts);
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
function getWindowOrigin() {
	const { origin, href } = window.location;
	if (origin) return origin;
	try {
		return new URL(href).origin;
	} catch {
		return null;
	}
}
/**
* If `url` is an absolute same-origin URL, return the local path
* (pathname + search + hash). Returns null for truly external URLs
* or on the server (where origin is unknown).
*/
function toSameOriginPath(url) {
	const origin = getWindowOrigin();
	if (!origin) return null;
	try {
		const parsed = url.startsWith("//") ? new URL(url, origin) : new URL(url);
		if (parsed.origin === origin) return parsed.pathname + parsed.search + parsed.hash;
	} catch {}
	return null;
}
/**
* If `url` is an absolute same-origin URL, return the app-relative path
* (basePath stripped from the pathname, if configured). Returns null for
* truly external URLs or on the server.
*/
function toSameOriginAppPath(url, basePath) {
	const localPath = toSameOriginPath(url);
	if (localPath == null || !basePath) return localPath;
	try {
		const parsed = new URL(localPath, "http://vinext.local");
		if (!hasBasePath(parsed.pathname, basePath)) return null;
		return stripBasePath(parsed.pathname, basePath) + parsed.search + parsed.hash;
	} catch {
		return localPath;
	}
}
/**
* Prepend basePath to a local path for browser URLs / fetches.
*/
function withBasePath(path, basePath) {
	if (!basePath || !path.startsWith("/") || isAbsoluteOrProtocolRelativeUrl(path)) return path;
	return basePath + path;
}
/**
* Resolve a potentially relative href against the current URL.
* Handles: "#hash", "?query", "?query#hash", and relative paths.
*/
function resolveRelativeHref(href, currentUrl, basePath = "") {
	const base = currentUrl ?? window.location.href;
	if (!base) return href;
	if (href.startsWith("/") || isAbsoluteOrProtocolRelativeUrl(href)) return href;
	try {
		const resolved = new URL(href, base);
		return (basePath && resolved.pathname === basePath ? "" : basePath ? stripBasePath(resolved.pathname, basePath) : resolved.pathname) + resolved.search + resolved.hash;
	} catch {
		return href;
	}
}
/**
* Convert a local navigation target into the browser URL that should be used
* for history entries, fetches, and onNavigate callbacks.
*/
function toBrowserNavigationHref(href, currentUrl, basePath = "") {
	const resolved = resolveRelativeHref(href, currentUrl, basePath);
	if (!basePath) return withBasePath(resolved, basePath);
	if (resolved === "") return basePath;
	if (resolved.startsWith("?") || resolved.startsWith("#")) return basePath + resolved;
	return withBasePath(resolved, basePath);
}
function isHashOnlyBrowserUrlChange(href, currentHref, basePath = "") {
	try {
		const current = new URL(currentHref);
		const next = new URL(href, currentHref);
		return stripBasePath(current.pathname, basePath) === stripBasePath(next.pathname, basePath) && current.search === next.search && next.hash !== "";
	} catch {
		return false;
	}
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/html-limited-bots.js
var HTML_LIMITED_BOT_UA_RE_STRING = String.raw`(?:^|[^\w-])[\w-]+-Google|Google-[\w-]+|Chrome-Lighthouse|Slurp|DuckDuckBot|baiduspider|yandex|sogou|bitlybot|tumblr|vkShare|quora link preview|redditbot|ia_archiver|Bingbot|BingPreview|applebot|facebookexternalhit|facebookcatalog|meta-externalagent|meta-externalfetcher|Twitterbot|LinkedInBot|Slackbot|Discordbot|WhatsApp|SkypeUriPreview|Yeti|googleweblight`;
var HEADLESS_BROWSER_BOT_UA_RE = /Googlebot(?!-)|Googlebot$/i;
var htmlLimitedBotRegexCache = /* @__PURE__ */ new Map();
function getHtmlLimitedBotRegex(htmlLimitedBots) {
	const source = htmlLimitedBots || HTML_LIMITED_BOT_UA_RE_STRING;
	const cached = htmlLimitedBotRegexCache.get(source);
	if (cached) return cached;
	const regex = new RegExp(source, "i");
	htmlLimitedBotRegexCache.set(source, regex);
	return regex;
}
/**
* Returns true when the User-Agent matches a known crawler/bot. Combines
* Next.js's "headless browser bot" check (Googlebot proper) with the
* "HTML-limited bot" list (Bingbot, DuckDuckBot, facebookexternalhit, …).
*
* Used by the Pages Router fallback path: a bot hitting an unlisted
* `fallback: true` route should get a synchronous render (real content) and
* not the loading shell, so the crawler indexes the actual page. Mirrors
* Next.js's `isBot()` in `.nextjs-ref/packages/next/src/shared/lib/router/utils/is-bot.ts`
* and the bot-aware fallback flip in
* `.nextjs-ref/packages/next/src/server/route-modules/pages/pages-handler.ts`.
*
* `htmlLimitedBots` allows next.config to override the HTML-limited list
* (same flag that drives `getHtmlLimitedBotRegex`), so a custom list applies
* to both streaming metadata gating and bot-aware fallback rendering.
*/
function isBotUserAgent(userAgent, htmlLimitedBots) {
	if (!userAgent) return false;
	if (HEADLESS_BROWSER_BOT_UA_RE.test(userAgent)) return true;
	return getHtmlLimitedBotRegex(htmlLimitedBots).test(userAgent);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/readonly-url-search-params.js
var ReadonlyURLSearchParamsError = class extends Error {
	constructor() {
		super("Method unavailable on `ReadonlyURLSearchParams`. Read more: https://nextjs.org/docs/app/api-reference/functions/use-search-params#updating-searchparams");
	}
};
/**
* Read-only URLSearchParams wrapper matching Next.js runtime behavior.
* Mutation methods remain present for instanceof/API compatibility but throw.
*/
var ReadonlyURLSearchParams = class extends URLSearchParams {
	append() {
		throw new ReadonlyURLSearchParamsError();
	}
	delete() {
		throw new ReadonlyURLSearchParamsError();
	}
	set() {
		throw new ReadonlyURLSearchParamsError();
	}
	sort() {
		throw new ReadonlyURLSearchParamsError();
	}
};
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/internal/app-prefetch-fetch-queue.js
var app_prefetch_fetch_queue_exports = /* @__PURE__ */ __exportAll({
	cancelAppPrefetchFetch: () => cancelAppPrefetchFetch,
	promoteAppPrefetchFetch: () => promoteAppPrefetchFetch,
	releaseAppPrefetchFetchSlot: () => releaseAppPrefetchFetchSlot,
	scheduleAppPrefetchFetch: () => scheduleAppPrefetchFetch
});
var APP_PREFETCH_FETCH_SLOT_RELEASE_KEY = Symbol.for("vinext.appPrefetchFetchSlotRelease");
var MAX_DEFAULT_APP_PREFETCH_REQUESTS = 4;
var defaultAppPrefetchQueue = [];
/** Lets a consumer promote or cancel the request behind a promise it already holds. */
var appPrefetchFetchControls = /* @__PURE__ */ new WeakMap();
var activeDefaultAppPrefetchRequests = 0;
var defaultAppPrefetchDrainScheduled = false;
function drainDefaultAppPrefetchQueue() {
	defaultAppPrefetchDrainScheduled = false;
	while (activeDefaultAppPrefetchRequests < MAX_DEFAULT_APP_PREFETCH_REQUESTS) {
		const run = defaultAppPrefetchQueue.shift();
		if (!run) return;
		activeDefaultAppPrefetchRequests += 1;
		run();
	}
}
function scheduleDefaultAppPrefetchDrain() {
	if (defaultAppPrefetchDrainScheduled) return;
	defaultAppPrefetchDrainScheduled = true;
	queueMicrotask(drainDefaultAppPrefetchQueue);
}
function releaseAppPrefetchFetchSlot(response) {
	const release = response[APP_PREFETCH_FETCH_SLOT_RELEASE_KEY];
	if (release === void 0) return;
	response[APP_PREFETCH_FETCH_SLOT_RELEASE_KEY] = void 0;
	release();
}
/**
* Low-priority App Router prefetches share a small request queue. The consumer
* must either snapshot the returned Response with snapshotRscResponse() or call
* releaseAppPrefetchFetchSlot() when it drops the response without consuming it.
*/
function scheduleAppPrefetchFetch(fetcher, priority) {
	const controller = new AbortController();
	if (priority === "high") {
		const promise = fetcher(controller.signal);
		appPrefetchFetchControls.set(promise, { cancel: () => controller.abort() });
		promise.then((response) => {
			response[APP_PREFETCH_FETCH_SLOT_RELEASE_KEY] = () => appPrefetchFetchControls.delete(promise);
		}, () => appPrefetchFetchControls.delete(promise));
		return promise;
	}
	let runner;
	let rejectPromise;
	let started = false;
	const promise = new Promise((resolve, reject) => {
		rejectPromise = reject;
		runner = () => {
			started = true;
			let didRelease = false;
			const release = () => {
				if (didRelease) return;
				didRelease = true;
				appPrefetchFetchControls.delete(promise);
				activeDefaultAppPrefetchRequests -= 1;
				drainDefaultAppPrefetchQueue();
			};
			try {
				fetcher(controller.signal).then((response) => {
					response[APP_PREFETCH_FETCH_SLOT_RELEASE_KEY] = release;
					resolve(response);
				}, (error) => {
					appPrefetchFetchControls.delete(promise);
					release();
					reject(error);
				});
			} catch (error) {
				appPrefetchFetchControls.delete(promise);
				release();
				reject(error);
			}
		};
	});
	defaultAppPrefetchQueue.push(runner);
	appPrefetchFetchControls.set(promise, {
		runner,
		cancel: () => {
			if (started) {
				controller.abort();
				return;
			}
			const index = defaultAppPrefetchQueue.indexOf(runner);
			if (index === -1) return;
			defaultAppPrefetchQueue.splice(index, 1);
			appPrefetchFetchControls.delete(promise);
			controller.abort();
			rejectPromise(controller.signal.reason);
		}
	});
	scheduleDefaultAppPrefetchDrain();
	return promise;
}
/** Cancel a queued or in-flight prefetch request. No-op once it has settled. */
function cancelAppPrefetchFetch(promise) {
	if (promise === void 0) return;
	appPrefetchFetchControls.get(promise)?.cancel();
}
/**
* Start a still-queued prefetch request immediately.
*
* A navigation that reuses an in-flight prefetch awaits that prefetch's
* promise. When the request is only queued, the navigation would otherwise wait
* for unrelated prefetch response bodies to finish before its own request even
* starts — indefinitely if one of those streams stalls. A promoted request is
* no longer a prefetch, it is the navigation, so it bypasses the concurrency
* cap instead of waiting for a slot.
*
* No-op when the request has already started or was never queued.
*/
function promoteAppPrefetchFetch(promise) {
	if (promise === void 0) return;
	const runner = appPrefetchFetchControls.get(promise)?.runner;
	if (runner === void 0) return;
	const index = defaultAppPrefetchQueue.indexOf(runner);
	if (index === -1) return;
	defaultAppPrefetchQueue.splice(index, 1);
	activeDefaultAppPrefetchRequests += 1;
	runner();
}
//#endregion
//#region \0vite/preload-helper.js
var scriptRel = "modulepreload";
var assetsURL = function(dep) {
	return "/" + dep;
};
var seen = {};
var __vitePreload = function preload(baseModule, deps, importerUrl) {
	let promise = Promise.resolve();
	if (deps && deps.length > 0) {
		const links = document.getElementsByTagName("link");
		const cspNonceMeta = document.querySelector("meta[property=csp-nonce]");
		const cspNonce = cspNonceMeta?.nonce || cspNonceMeta?.getAttribute("nonce");
		function allSettled(promises) {
			return Promise.all(promises.map((p) => Promise.resolve(p).then((value) => ({
				status: "fulfilled",
				value
			}), (reason) => ({
				status: "rejected",
				reason
			}))));
		}
		promise = allSettled(deps.map((dep) => {
			dep = assetsURL(dep, importerUrl);
			if (dep in seen) return;
			seen[dep] = true;
			const isCss = dep.endsWith(".css");
			const cssSelector = isCss ? "[rel=\"stylesheet\"]" : "";
			if (!!importerUrl) for (let i = links.length - 1; i >= 0; i--) {
				const link = links[i];
				if (link.href === dep && (!isCss || link.rel === "stylesheet")) return;
			}
			else if (document.querySelector(`link[href="${dep}"]${cssSelector}`)) return;
			const link = document.createElement("link");
			link.rel = isCss ? "stylesheet" : scriptRel;
			if (!isCss) link.as = "script";
			link.crossOrigin = "";
			link.href = dep;
			if (cspNonce) link.setAttribute("nonce", cspNonce);
			document.head.appendChild(link);
			if (isCss) return new Promise((res, rej) => {
				link.addEventListener("load", res);
				link.addEventListener("error", () => rej(/* @__PURE__ */ new Error(`Unable to preload CSS for ${dep}`)));
			});
		}));
	}
	function handlePreloadError(err) {
		const e = new Event("vite:preloadError", { cancelable: true });
		e.payload = err;
		window.dispatchEvent(e);
		if (!e.defaultPrevented) throw err;
	}
	return promise.then((res) => {
		for (const item of res || []) {
			if (item.status !== "rejected") continue;
			handlePreloadError(item.reason);
		}
		return baseModule().catch(handlePreloadError);
	});
};
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/navigation.js
function resolveHybridClientRouteOwner(href) {
	return null;
}
var PAGES_NAVIGATION_NOTIFY_KEY = Symbol.for("vinext.navigation.pagesNavigationNotify");
var PREFETCH_CACHE_EVICTION_TARGET_SIZE = 50 * 1024 * 1024 * .9;
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
var DYNAMIC_NAVIGATION_CACHE_TTL = resolveClientRouterStaleTime("0", 3e4);
var PREFETCH_CACHE_TTL = resolveClientRouterStaleTime("300", 3e4);
/**
* Floor for any server-declared `cacheLife` stale time, mirroring Next.js's
* `getStaleTimeMs` (`Math.max(staleTimeSeconds, 30) * 1000`). One rule for
* both client caches, so behavior does not depend on which cache a route hit.
*/
var MIN_SERVER_STALE_TIME_SECONDS = 30;
var MIN_PREFETCH_STALE_TIME_MS = MIN_SERVER_STALE_TIME_SECONDS * 1e3;
function getPrefetchInterceptionContext(targetHref) {
	let targetUrl;
	try {
		targetUrl = new URL(targetHref, window.location.href);
	} catch {
		return null;
	}
	return resolveManifestNavigationInterceptionContext({
		basePath: "",
		currentPathname: window.location.pathname,
		routeManifest: getNavigationRuntime()?.bootstrap.routeManifest ?? null,
		targetPathname: targetUrl.pathname
	});
}
function getCurrentNextUrl() {
	return window.location.pathname + window.location.search;
}
function createAppPrefetchRequestHeaders(options) {
	const prefetchRouterState = getNavigationRuntime()?.functions.getPrefetchRouterState?.() ?? null;
	return createRscRequestHeaders({
		...options,
		nextUrl: getCurrentNextUrl(),
		includePrefetchHeader: options.prefetchKind !== "full",
		prefetchRouterState
	});
}
/** Get or create the shared in-memory RSC prefetch cache on window. */
function getPrefetchCache() {
	if (!window.__VINEXT_RSC_PREFETCH_CACHE__) window.__VINEXT_RSC_PREFETCH_CACHE__ = /* @__PURE__ */ new Map();
	return window.__VINEXT_RSC_PREFETCH_CACHE__;
}
/**
* Get or create the shared set of already-prefetched RSC URLs on window.
* Keyed by interception-aware cache key so distinct source routes do not alias.
*/
function getPrefetchedUrls() {
	if (!window.__VINEXT_RSC_PREFETCHED_URLS__) window.__VINEXT_RSC_PREFETCHED_URLS__ = /* @__PURE__ */ new Set();
	return window.__VINEXT_RSC_PREFETCHED_URLS__;
}
function isStaleTimeSeconds(value) {
	return typeof value === "number" && Number.isFinite(value) && Number.isInteger(value) && value >= 0;
}
function isCacheExpiresAt(value) {
	return typeof value === "number" && Number.isFinite(value) && value >= 0;
}
function parseStaleTimeSecondsHeader(value) {
	if (value === null || value === "") return void 0;
	const seconds = Number(value);
	return isStaleTimeSeconds(seconds) ? seconds : void 0;
}
/**
* The floor a `cacheLife` claim licenses. A pending claim contributes exactly
* the floor — the least any resolution of it could have granted.
*/
function serverStaleTimeSeconds(server) {
	if (server === void 0) return void 0;
	if (server.kind === "pending") return MIN_SERVER_STALE_TIME_SECONDS;
	return Math.max(server.seconds, MIN_SERVER_STALE_TIME_SECONDS);
}
/**
* Min-combine the two independent staleness lattices a response can carry:
* `dynamicStaleTimeSeconds` (from `experimental.staleTimes` config) and
* `serverStaleTime` (from the render's `cacheLife`) — neither may override
* the other. The cacheLife value is floored *before* the min so the floor
* never raises the config bound. Undefined = no signal; the caller's
* fallback TTL stays in force.
*/
function resolveRscResponseStaleTimeSeconds(cached) {
	const dynamic = cached.dynamicStaleTimeSeconds;
	const server = serverStaleTimeSeconds(cached.serverStaleTime);
	if (!isStaleTimeSeconds(dynamic)) return server;
	return server === void 0 ? dynamic : Math.min(dynamic, server);
}
function resolveCachedRscResponseTtlMs(cached, fallbackTtlMs) {
	const seconds = resolveRscResponseStaleTimeSeconds(cached);
	if (seconds === void 0) return fallbackTtlMs;
	return seconds * 1e3;
}
function resolveCachedRscResponseExpiresAt(timestamp, cached, fallbackTtlMs) {
	if (isCacheExpiresAt(cached.expiresAt)) return cached.expiresAt;
	return timestamp + resolveCachedRscResponseTtlMs(cached, fallbackTtlMs);
}
function resolvePrefetchedRscResponseExpiresAt(timestamp, cached, fallbackTtlMs, honorDynamicStaleTime) {
	if (isCacheExpiresAt(cached.expiresAt)) return cached.expiresAt;
	const serverSeconds = serverStaleTimeSeconds(cached.serverStaleTime);
	if (serverSeconds !== void 0) return timestamp + serverSeconds * 1e3;
	const seconds = isStaleTimeSeconds(cached.dynamicStaleTimeSeconds) ? cached.dynamicStaleTimeSeconds : void 0;
	if (seconds === void 0) return timestamp + Math.max(fallbackTtlMs, MIN_PREFETCH_STALE_TIME_MS);
	return honorDynamicStaleTime ? timestamp + seconds * 1e3 : timestamp + Math.max(seconds * 1e3, MIN_PREFETCH_STALE_TIME_MS);
}
function resolvePrefetchCacheEntryExpiresAt(entry) {
	if (entry.expiresAt !== void 0) return entry.expiresAt;
	if (entry.snapshot) return resolveCachedRscResponseExpiresAt(entry.timestamp, entry.snapshot, PREFETCH_CACHE_TTL);
	return entry.timestamp + PREFETCH_CACHE_TTL;
}
function resolvePrefetchCacheEntryMountedSlotsHeader(entry) {
	if (entry.mountedSlotsHeader !== void 0) return entry.mountedSlotsHeader;
	return entry.snapshot?.mountedSlotsHeader ?? null;
}
function normalizeRscCacheLookupUrl(rscUrl) {
	try {
		const url = new URL(rscUrl, "http://vinext.local");
		stripRscCacheBustingSearchParam(url);
		return `${url.pathname}${url.search}`;
	} catch {
		return null;
	}
}
function parsePrefetchCacheKey$1(cacheKey) {
	const separatorIndex = cacheKey.indexOf("\0");
	if (separatorIndex === -1) return {
		interceptionContext: null,
		rscUrl: cacheKey
	};
	return {
		interceptionContext: cacheKey.slice(separatorIndex + 1),
		rscUrl: cacheKey.slice(0, separatorIndex)
	};
}
function isPrefetchCacheEntryCompatibleWithMountedSlots(entry, mountedSlotsHeader) {
	if (resolvePrefetchCacheEntryMountedSlotsHeader(entry) === mountedSlotsHeader) return true;
	return (entry.snapshot?.mountedSlotsHeader ?? null) === mountedSlotsHeader;
}
function findPrefetchCacheEntryForNavigation(rscUrl, interceptionContext, mountedSlotsHeader, additionalRscUrls = []) {
	const cache = getPrefetchCache();
	const rscUrls = [rscUrl, ...additionalRscUrls];
	for (const lookupRscUrl of rscUrls) {
		const exactCacheKey = AppElementsWire.encodeCacheKey(lookupRscUrl, interceptionContext);
		const exactEntry = cache.get(exactCacheKey);
		if (exactEntry && exactEntry.cacheForNavigation !== false && isPrefetchCacheEntryCompatibleWithMountedSlots(exactEntry, mountedSlotsHeader)) return {
			cacheKey: exactCacheKey,
			entry: exactEntry
		};
	}
	const normalizedTargets = new Set(rscUrls.map((lookupRscUrl) => normalizeRscCacheLookupUrl(lookupRscUrl)).filter((lookupRscUrl) => lookupRscUrl !== null));
	if (normalizedTargets.size === 0) return null;
	for (const [cacheKey, entry] of cache) {
		if (entry.cacheForNavigation === false) continue;
		const source = parsePrefetchCacheKey$1(cacheKey);
		if (source.interceptionContext !== interceptionContext) continue;
		const normalizedSource = normalizeRscCacheLookupUrl(source.rscUrl);
		if (normalizedSource === null || !normalizedTargets.has(normalizedSource)) continue;
		if (!isPrefetchCacheEntryCompatibleWithMountedSlots(entry, mountedSlotsHeader)) continue;
		return {
			cacheKey,
			entry
		};
	}
	return null;
}
function hasPrefetchCacheEntryForNavigation(rscUrl, interceptionContext = null, mountedSlotsHeader = null, options = {}) {
	const match = findPrefetchCacheEntryForNavigation(rscUrl, interceptionContext, mountedSlotsHeader, options.additionalRscUrls);
	if (match === null) return false;
	if (match.entry.pending !== void 0 || resolvePrefetchCacheEntryExpiresAt(match.entry) > Date.now()) {
		touchPrefetchCacheEntry(getPrefetchCache(), match.cacheKey, match.entry);
		attachPrefetchInvalidationToEntry(match.cacheKey, match.entry, options.onInvalidate);
		return true;
	}
	deletePrefetchCacheEntry(getPrefetchCache(), getPrefetchedUrls(), match.cacheKey, match.entry, options.notifyInvalidation ?? true);
	return false;
}
function getPrefetchCacheEntrySize(entry) {
	return entry.snapshot?.buffer.byteLength ?? entry.size ?? 0;
}
var trackedPrefetchCache = null;
var trackedPrefetchCacheByteSize = 0;
function getPrefetchCacheByteSize(cache) {
	if (trackedPrefetchCache === cache) return trackedPrefetchCacheByteSize;
	let total = 0;
	const seen = /* @__PURE__ */ new Set();
	for (const entry of cache.values()) {
		if (seen.has(entry)) continue;
		seen.add(entry);
		total += getPrefetchCacheEntrySize(entry);
	}
	trackedPrefetchCache = cache;
	trackedPrefetchCacheByteSize = total;
	return total;
}
function adjustPrefetchCacheByteSize(cache, delta) {
	if (trackedPrefetchCache !== cache) return;
	trackedPrefetchCacheByteSize = Math.max(0, trackedPrefetchCacheByteSize + delta);
}
function touchPrefetchCacheEntry(cache, cacheKey, entry) {
	if (cache.get(cacheKey) !== entry) return;
	cache.delete(cacheKey);
	cache.set(cacheKey, entry);
	for (const key of entry.cacheKeys ?? []) {
		if (key === cacheKey || cache.get(key) !== entry) continue;
		cache.delete(key);
		cache.set(key, entry);
	}
}
/**
* Evict prefetch cache entries if buffered payloads exceed the byte budget.
* Sweeps expired entries only after the cheap byte-budget check says cleanup is
* needed, then evicts least-recently-used entries down to the target size.
*/
function evictPrefetchCacheIfNeeded() {
	const cache = getPrefetchCache();
	let totalSize = getPrefetchCacheByteSize(cache);
	if (totalSize <= 52428800) return;
	const now = Date.now();
	const prefetched = getPrefetchedUrls();
	for (const [key, entry] of cache) if (resolvePrefetchCacheEntryExpiresAt(entry) <= now) deletePrefetchCacheEntry(cache, prefetched, key, entry, true);
	totalSize = getPrefetchCacheByteSize(cache);
	if (totalSize <= 52428800) return;
	let inspectedEntries = 0;
	while (totalSize > PREFETCH_CACHE_EVICTION_TARGET_SIZE && inspectedEntries < cache.size) {
		const oldest = cache.keys().next().value;
		if (oldest !== void 0) {
			const entry = cache.get(oldest);
			if (entry) {
				const entrySize = getPrefetchCacheEntrySize(entry);
				if (entry.pending !== void 0 && entrySize === 0) {
					touchPrefetchCacheEntry(cache, oldest, entry);
					inspectedEntries += 1;
					continue;
				}
				totalSize -= entrySize;
				deletePrefetchCacheEntry(cache, prefetched, oldest, entry, true);
				inspectedEntries = 0;
			} else {
				cache.delete(oldest);
				prefetched.delete(oldest);
				inspectedEntries += 1;
			}
		} else break;
	}
}
var pendingPrefetchSetups = /* @__PURE__ */ new Set();
function beginPrefetchSetup(destination) {
	const setup = {
		destination,
		cancelled: false
	};
	pendingPrefetchSetups.add(setup);
	return setup;
}
/** Passing `null` cancels every pending setup regardless of destination. */
function cancelPendingPrefetchSetups(destination) {
	for (const setup of pendingPrefetchSetups) if (destination === null || setup.destination === destination) setup.cancelled = true;
}
/**
* Normalize a navigation or prefetch target to the browser href both sides
* compare on. Returns null when the target is not same-origin — no same-origin
* prefetch can be a duplicate of it — and on the server, where
* `navigateClientSide` can still be reached but there is nothing to cancel.
*/
function toAppPrefetchDestination(href) {
	let localHref = href;
	if (isExternalUrl(href)) {
		const localPath = toSameOriginAppPath(href, "");
		if (localPath == null) return null;
		localHref = localPath;
	}
	const browserHref = toBrowserNavigationHref(localHref, window.location.href, "");
	try {
		const url = new URL(browserHref, window.location.href);
		return `${url.pathname}${url.search}`;
	} catch {
		return browserHref.split("#", 1)[0];
	}
}
function clearPrefetchInvalidation(entry) {
	if (entry.invalidationTimer !== void 0) {
		clearTimeout(entry.invalidationTimer);
		entry.invalidationTimer = void 0;
	}
}
function runInvalidationCallback(onInvalidate) {
	try {
		onInvalidate();
	} catch (error) {
		if (typeof reportError === "function") reportError(error);
		else console.error(error);
	}
}
function notifyPrefetchInvalidated(entry) {
	clearPrefetchInvalidation(entry);
	const callbacks = entry.onInvalidateCallbacks;
	entry.onInvalidateCallbacks = void 0;
	if (callbacks === void 0) return;
	for (const onInvalidate of callbacks) runInvalidationCallback(onInvalidate);
}
var retainedPrefetchInvalidations = /* @__PURE__ */ new Set();
function retainPrefetchInvalidationAfterConsume(entry) {
	const callbacks = entry.onInvalidateCallbacks;
	if (callbacks === void 0 || callbacks.size === 0) return;
	const delay = Math.max(0, resolvePrefetchCacheEntryExpiresAt(entry) - Date.now());
	const retained = {
		callbacks,
		timer: setTimeout(() => fireRetainedPrefetchInvalidation(retained), delay)
	};
	retainedPrefetchInvalidations.add(retained);
}
function fireRetainedPrefetchInvalidation(retained) {
	if (!retainedPrefetchInvalidations.delete(retained)) return;
	clearTimeout(retained.timer);
	for (const onInvalidate of retained.callbacks) runInvalidationCallback(onInvalidate);
}
function deletePrefetchCacheEntry(cache, prefetched, cacheKey, entry, notify) {
	const cacheKeys = entry.cacheKeys ?? /* @__PURE__ */ new Set([cacheKey]);
	let removedOwnedKey = false;
	for (const key of cacheKeys) if (cache.get(key) === entry) {
		cache.delete(key);
		prefetched.delete(key);
		removedOwnedKey = true;
	}
	if (!removedOwnedKey) return;
	adjustPrefetchCacheByteSize(cache, -getPrefetchCacheEntrySize(entry));
	entry.cacheKeys = void 0;
	if (notify) notifyPrefetchInvalidated(entry);
	else {
		clearPrefetchInvalidation(entry);
		entry.onInvalidateCallbacks = void 0;
	}
}
function discardLearningOnlyPrefetchCacheEntry(rscUrl, interceptionContext = null) {
	const cache = getPrefetchCache();
	const prefetched = getPrefetchedUrls();
	const normalizedTarget = normalizeRscCacheLookupUrl(rscUrl);
	if (normalizedTarget === null) return false;
	const superseded = [];
	for (const [cacheKey, entry] of cache) {
		if (entry.cacheForNavigation !== false || entry.prefetchKind !== "navigation") continue;
		const source = parsePrefetchCacheKey$1(cacheKey);
		if (source.interceptionContext !== interceptionContext) continue;
		if (normalizeRscCacheLookupUrl(source.rscUrl) !== normalizedTarget) continue;
		superseded.push([cacheKey, entry]);
	}
	for (const [cacheKey, entry] of superseded) {
		cancelAppPrefetchFetch(entry.fetchPromise);
		deletePrefetchCacheEntry(cache, prefetched, cacheKey, entry, true);
	}
	return superseded.length > 0;
}
function invalidatePrefetchCacheEntry(cacheKey) {
	const cache = getPrefetchCache();
	const entry = cache.get(cacheKey);
	if (!entry) return;
	deletePrefetchCacheEntry(cache, getPrefetchedUrls(), cacheKey, entry, true);
}
function schedulePrefetchInvalidation(cacheKey, entry) {
	if (entry.onInvalidateCallbacks === void 0 || entry.onInvalidateCallbacks.size === 0) return;
	clearPrefetchInvalidation(entry);
	const delay = Math.max(0, resolvePrefetchCacheEntryExpiresAt(entry) - Date.now());
	entry.invalidationTimer = setTimeout(() => {
		invalidatePrefetchCacheEntry(cacheKey);
	}, delay);
}
function addPrefetchInvalidationCallback(entry, onInvalidate) {
	if (onInvalidate === void 0) return;
	if (entry.onInvalidateCallbacks === void 0) entry.onInvalidateCallbacks = /* @__PURE__ */ new Set();
	entry.onInvalidateCallbacks.add(onInvalidate);
}
/**
* Attach `onInvalidate` to an entry the caller already holds. A settled entry
* needs its invalidation timer started here — nothing else will schedule one
* once `prefetchRscResponse` has finished with it.
*/
function attachPrefetchInvalidationToEntry(cacheKey, entry, onInvalidate) {
	if (onInvalidate === void 0) return;
	addPrefetchInvalidationCallback(entry, onInvalidate);
	if (entry.outcome === "cache-seeded") schedulePrefetchInvalidation(cacheKey, entry);
}
function attachPrefetchInvalidationCallback(cacheKey, onInvalidate) {
	if (onInvalidate === void 0) return;
	const entry = getPrefetchCache().get(cacheKey);
	if (!entry) return;
	attachPrefetchInvalidationToEntry(cacheKey, entry, onInvalidate);
}
function invalidatePrefetchCache() {
	cancelPendingPrefetchSetups(null);
	const cache = getPrefetchCache();
	const prefetched = getPrefetchedUrls();
	for (const [cacheKey, entry] of cache) deletePrefetchCacheEntry(cache, prefetched, cacheKey, entry, true);
	prefetched.clear();
	for (const retained of retainedPrefetchInvalidations) fireRetainedPrefetchInvalidation(retained);
	getNavigationRuntime()?.functions.pingVisibleLinks?.();
}
function seedPrefetchResponseSnapshot(rscUrl, snapshot, interceptionContext = null, mountedSlotsHeader = null, fallbackTtlMs = DYNAMIC_NAVIGATION_CACHE_TTL) {
	const cacheKey = AppElementsWire.encodeCacheKey(rscUrl, interceptionContext);
	const cache = getPrefetchCache();
	const existing = cache.get(cacheKey);
	if (existing) deletePrefetchCacheEntry(cache, getPrefetchedUrls(), cacheKey, existing, false);
	const timestamp = Date.now();
	const entry = {
		cacheForNavigation: true,
		cacheKeys: /* @__PURE__ */ new Set([cacheKey]),
		expiresAt: resolveCachedRscResponseExpiresAt(timestamp, snapshot, fallbackTtlMs),
		mountedSlotsHeader,
		outcome: "cache-seeded",
		size: snapshot.buffer.byteLength,
		snapshot,
		timestamp
	};
	cache.set(cacheKey, entry);
	adjustPrefetchCacheByteSize(cache, snapshot.buffer.byteLength);
	getPrefetchedUrls().add(cacheKey);
	schedulePrefetchInvalidation(cacheKey, entry);
	evictPrefetchCacheIfNeeded();
}
function deletePrefetchResponseSnapshot(rscUrl, snapshot, interceptionContext = null) {
	const cacheKey = AppElementsWire.encodeCacheKey(rscUrl, interceptionContext);
	const cache = getPrefetchCache();
	const entry = cache.get(cacheKey);
	if (entry?.snapshot !== snapshot) return;
	deletePrefetchCacheEntry(cache, getPrefetchedUrls(), cacheKey, entry, false);
}
function createCachedRscResponseSnapshot(response, buffer, responseUrl = null) {
	const headerDynamicStaleTimeSeconds = parseStaleTimeSecondsHeader(response.headers.get(VINEXT_DYNAMIC_STALE_TIME_HEADER));
	const completionMode = response.headers.get(VINEXT_RSC_COMPLETION_METADATA_HEADER);
	const extracted = completionMode === "1" ? extractRscCompletionMetadata(buffer) : { buffer };
	const completedDynamicStaleTimeSeconds = completionMode === "resolved" ? headerDynamicStaleTimeSeconds : extracted.metadata?.dynamicStaleTimeSeconds ?? headerDynamicStaleTimeSeconds;
	const dynamicStaleTimeSeconds = completedDynamicStaleTimeSeconds ?? headerDynamicStaleTimeSeconds;
	const parsedServerStaleTime = parseServerStaleTimeHeaders(response.headers);
	const serverStaleTime = extracted.metadata !== void 0 && Object.hasOwn(extracted.metadata, "serverStaleTimeSeconds") ? extracted.metadata?.serverStaleTimeSeconds === null ? void 0 : {
		kind: "resolved",
		seconds: extracted.metadata.serverStaleTimeSeconds
	} : parsedServerStaleTime;
	return {
		compatibilityIdHeader: response.headers.get(VINEXT_RSC_COMPATIBILITY_ID_HEADER),
		buffer: extracted.buffer,
		...completedDynamicStaleTimeSeconds !== void 0 ? { completedDynamicStaleTimeSeconds } : {},
		contentType: response.headers.get("content-type") ?? "text/x-component",
		...dynamicStaleTimeSeconds !== void 0 ? { dynamicStaleTimeSeconds } : {},
		mountedSlotsHeader: response.headers.get(VINEXT_MOUNTED_SLOTS_HEADER),
		paramsHeader: response.headers.get(VINEXT_PARAMS_HEADER),
		renderedPathAndSearch: parseRenderedPathAndSearchHeader(response.headers.get(VINEXT_RENDERED_PATH_AND_SEARCH_HEADER)),
		...serverStaleTime === void 0 ? {} : { serverStaleTime },
		url: responseUrl ?? response.url
	};
}
/**
* Collapse the two mutually-exclusive wire headers into one state. A pending
* marker wins: it says the render committed headers before `cacheLife` settled,
* so any resolved value alongside it cannot describe the completed render.
*/
function parseServerStaleTimeHeaders(headers) {
	if (headers.get("X-Vinext-Stale-Time-Pending") === "1") return { kind: "pending" };
	const seconds = parseStaleTimeSecondsHeader(headers.get(NEXT_ROUTER_STALE_TIME_HEADER));
	return seconds === void 0 ? void 0 : {
		kind: "resolved",
		seconds
	};
}
function parseRenderedPathAndSearchHeader(value) {
	if (value === null || value === "") return null;
	try {
		const decoded = decodeURIComponent(value);
		return decoded.startsWith("/") ? decoded : null;
	} catch {
		return null;
	}
}
/**
* Snapshot an RSC response to an ArrayBuffer for caching and replay.
* Consumes the response body and stores it with content-type and URL metadata.
*/
async function snapshotRscResponse(response) {
	try {
		return createCachedRscResponseSnapshot(response, await response.arrayBuffer());
	} finally {
		releaseAppPrefetchFetchSlot(response);
	}
}
/**
* Reconstruct a Response from a cached RSC snapshot.
* Creates a new Response with the original ArrayBuffer so createFromFetch
* can consume the stream from scratch.
*
* NOTE: The reconstructed Response always has `url === ""` — the Response
* constructor does not accept a `url` option, and `response.url` is read-only
* set by the fetch infrastructure. Callers that need the original URL should
* read it from `cached.url` directly rather than from the restored Response.
*
* @param copy - When true (default), copies the ArrayBuffer so the cached
*   snapshot remains replayable (needed for the visited-response cache).
*   Pass false for single-consumption paths (e.g. prefetch cache entries
*   that are deleted after consumption) to avoid the extra allocation.
*/
function restoreRscResponse(cached, copy = true) {
	const headers = new Headers({ "content-type": cached.contentType });
	if (cached.mountedSlotsHeader != null) headers.set(VINEXT_MOUNTED_SLOTS_HEADER, cached.mountedSlotsHeader);
	if (cached.compatibilityIdHeader != null) headers.set(VINEXT_RSC_COMPATIBILITY_ID_HEADER, cached.compatibilityIdHeader);
	if (isStaleTimeSeconds(cached.dynamicStaleTimeSeconds)) headers.set(VINEXT_DYNAMIC_STALE_TIME_HEADER, String(cached.dynamicStaleTimeSeconds));
	if (isStaleTimeSeconds(cached.completedDynamicStaleTimeSeconds)) headers.set(VINEXT_RSC_COMPLETION_METADATA_HEADER, "resolved");
	if (cached.serverStaleTime?.kind === "pending") headers.set(VINEXT_STALE_TIME_PENDING_HEADER, "1");
	else if (cached.serverStaleTime !== void 0) headers.set(NEXT_ROUTER_STALE_TIME_HEADER, String(cached.serverStaleTime.seconds));
	if (cached.paramsHeader != null) headers.set(VINEXT_PARAMS_HEADER, cached.paramsHeader);
	if (cached.renderedPathAndSearch != null) headers.set(VINEXT_RENDERED_PATH_AND_SEARCH_HEADER, encodeURIComponent(cached.renderedPathAndSearch));
	return new Response(copy ? cached.buffer.slice(0) : cached.buffer, {
		status: 200,
		headers
	});
}
/**
* `prefetchRscResponse`'s `prepareSnapshot` for navigation-reusable entries:
* decode the cached payload through the App Router runtime so a later
* navigation can commit it without re-parsing. Shared by `<Link>` and
* `router.prefetch()`.
*/
async function prepareNavigationPrefetchSnapshot(snapshot) {
	const preparePrefetchResponse = getNavigationRuntime()?.functions.preparePrefetchResponse;
	if (!preparePrefetchResponse) throw new Error("App Router prefetch preparation is unavailable");
	return await preparePrefetchResponse(restoreRscResponse(snapshot));
}
/**
* Prefetch an RSC response and snapshot it for later consumption.
* Stores the in-flight promise so immediate clicks can await it instead
* of firing a duplicate fetch.
* Enforces a maximum cache size to prevent unbounded memory growth on
* link-heavy pages.
*/
function prefetchRscResponse(rscUrl, fetchPromise, interceptionContext = null, mountedSlotsHeader = null, options, behavior = {}) {
	const cacheKey = AppElementsWire.encodeCacheKey(rscUrl, interceptionContext);
	const cache = getPrefetchCache();
	const prefetched = getPrefetchedUrls();
	const now = Date.now();
	const existing = cache.get(cacheKey);
	if (existing) deletePrefetchCacheEntry(cache, prefetched, cacheKey, existing, false);
	const entry = {
		cacheForNavigation: behavior.cacheForNavigation ?? true,
		cacheKeys: /* @__PURE__ */ new Set([cacheKey]),
		mountedSlotsHeader,
		optimisticRouteShell: behavior.optimisticRouteShell === true,
		outcome: "pending",
		prefetchKind: behavior.prefetchKind ?? (behavior.optimisticRouteShell === true ? "loading-shell" : "navigation"),
		searchAgnosticShell: behavior.searchAgnosticShell === true,
		timestamp: now
	};
	addPrefetchInvalidationCallback(entry, options?.onInvalidate);
	entry.fetchPromise = fetchPromise;
	entry.pending = fetchPromise.then(async (response) => {
		if (response.ok) {
			const snapshot = await snapshotRscResponse(response);
			if (cache.get(cacheKey) !== entry) return;
			const previousSize = getPrefetchCacheEntrySize(entry);
			entry.snapshot = snapshot;
			entry.size = snapshot.buffer.byteLength;
			adjustPrefetchCacheByteSize(cache, entry.size - previousSize);
			entry.expiresAt = resolvePrefetchedRscResponseExpiresAt(entry.timestamp, entry.snapshot, behavior.fallbackTtlMs ?? PREFETCH_CACHE_TTL, behavior.honorDynamicStaleTime !== false && behavior.searchAgnosticShell !== true);
			if (behavior.prepareSnapshot) try {
				const preparedElements = await behavior.prepareSnapshot(snapshot);
				if (cache.get(cacheKey) !== entry) return;
				entry.preparedElements = preparedElements;
			} catch {}
			addRenderedPathAndSearchPrefetchAlias(cache, prefetched, cacheKey, entry);
			evictPrefetchCacheIfNeeded();
		} else {
			releaseAppPrefetchFetchSlot(response);
			deletePrefetchCacheEntry(cache, prefetched, cacheKey, entry, false);
		}
	}).catch(() => {
		deletePrefetchCacheEntry(cache, prefetched, cacheKey, entry, false);
	}).finally(() => {
		if (cache.get(cacheKey) !== entry) return;
		entry.pending = void 0;
		entry.fetchPromise = void 0;
		if (entry.snapshot) {
			entry.outcome = "cache-seeded";
			schedulePrefetchInvalidation(cacheKey, entry);
		}
	});
	cache.set(cacheKey, entry);
	evictPrefetchCacheIfNeeded();
}
function addRenderedPathAndSearchPrefetchAlias(cache, prefetched, primaryCacheKey, entry) {
	if (entry.cacheForNavigation === false) return;
	const renderedPathAndSearch = entry.snapshot?.renderedPathAndSearch;
	if (!renderedPathAndSearch) return;
	const source = parsePrefetchCacheKey$1(primaryCacheKey);
	const aliasCacheKey = AppElementsWire.encodeCacheKey(renderedPathAndSearch, source.interceptionContext);
	if (aliasCacheKey === primaryCacheKey) return;
	const existing = cache.get(aliasCacheKey);
	if (existing && existing !== entry) deletePrefetchCacheEntry(cache, prefetched, aliasCacheKey, existing, false);
	entry.cacheKeys ??= /* @__PURE__ */ new Set([primaryCacheKey]);
	entry.cacheKeys.add(aliasCacheKey);
	cache.set(aliasCacheKey, entry);
	prefetched.add(aliasCacheKey);
}
function peekPrefetchResponseForNavigation(rscUrl, interceptionContext = null, mountedSlotsHeader = null, options) {
	const match = findPrefetchCacheEntryForNavigation(rscUrl, interceptionContext, mountedSlotsHeader, options?.additionalRscUrls);
	if (!match) return null;
	const { cacheKey, entry } = match;
	if (entry.pending || entry.outcome !== "cache-seeded") return null;
	if (entry.cacheForNavigation === false || !entry.snapshot) return null;
	if (resolvePrefetchCacheEntryExpiresAt(entry) <= Date.now()) {
		deletePrefetchCacheEntry(getPrefetchCache(), getPrefetchedUrls(), cacheKey, entry, true);
		return null;
	}
	if (entry.expiresAt !== void 0 || entry.snapshot.expiresAt !== void 0) return {
		...entry.snapshot,
		expiresAt: resolvePrefetchCacheEntryExpiresAt(entry)
	};
	return entry.snapshot;
}
/**
* Consume a prefetched response for a given rscUrl.
* Only returns settled (non-pending) snapshots synchronously.
* Returns null if the entry is still in flight or doesn't exist.
*/
function consumePrefetchResponse(rscUrl, interceptionContext = null, mountedSlotsHeader = null, options) {
	const cache = getPrefetchCache();
	const exactCacheKey = AppElementsWire.encodeCacheKey(rscUrl, interceptionContext);
	const exactEntry = cache.get(exactCacheKey);
	if (exactEntry && exactEntry.cacheForNavigation !== false && !isPrefetchCacheEntryCompatibleWithMountedSlots(exactEntry, mountedSlotsHeader)) deletePrefetchCacheEntry(cache, getPrefetchedUrls(), exactCacheKey, exactEntry, false);
	const match = findPrefetchCacheEntryForNavigation(rscUrl, interceptionContext, mountedSlotsHeader, options?.additionalRscUrls);
	if (!match) return null;
	const { cacheKey, entry } = match;
	return consumeMatchedPrefetchResponse(cacheKey, entry, mountedSlotsHeader);
}
function consumeMatchedPrefetchResponse(cacheKey, entry, mountedSlotsHeader, allowExpiredInFlightHandoff = false) {
	const cache = getPrefetchCache();
	if (entry.pending || entry.outcome !== "cache-seeded") return null;
	if (entry.cacheForNavigation === false) return null;
	if (entry.snapshot) {
		if (!isPrefetchCacheEntryCompatibleWithMountedSlots(entry, mountedSlotsHeader)) return null;
		if (!allowExpiredInFlightHandoff && resolvePrefetchCacheEntryExpiresAt(entry) <= Date.now()) {
			deletePrefetchCacheEntry(cache, getPrefetchedUrls(), cacheKey, entry, true);
			return null;
		}
		retainPrefetchInvalidationAfterConsume(entry);
		deletePrefetchCacheEntry(cache, getPrefetchedUrls(), cacheKey, entry, false);
		const snapshot = entry.snapshot;
		if (entry.expiresAt !== void 0 || entry.snapshot.expiresAt !== void 0) return {
			...snapshot,
			expiresAt: resolvePrefetchCacheEntryExpiresAt(entry),
			...entry.preparedElements ? { preparedElements: entry.preparedElements } : {}
		};
		return entry.preparedElements ? {
			...snapshot,
			preparedElements: entry.preparedElements
		} : snapshot;
	}
	return null;
}
async function consumePrefetchResponseForNavigation(rscUrl, interceptionContext = null, mountedSlotsHeader = null, options) {
	const cache = getPrefetchCache();
	const match = findPrefetchCacheEntryForNavigation(rscUrl, interceptionContext, mountedSlotsHeader, options?.additionalRscUrls);
	if (!match) return null;
	const { cacheKey, entry } = match;
	if (options?.shouldConsume?.() === false) return null;
	const allowExpiredInFlightHandoff = entry.pending !== void 0;
	if (entry.pending !== void 0) {
		promoteAppPrefetchFetch(entry.fetchPromise);
		await entry.pending.catch(() => {});
		if (cache.get(cacheKey) !== entry) return null;
		if (options?.shouldConsume?.() === false) return null;
	}
	return consumeMatchedPrefetchResponse(cacheKey, entry, mountedSlotsHeader, allowExpiredInFlightHandoff);
}
var _CLIENT_NAV_STATE_KEY = Symbol.for("vinext.clientNavigationState");
var _MOUNTED_SLOTS_HEADER_KEY = Symbol.for("vinext.mountedSlotsHeader");
function setMountedSlotsHeader(header) {
	const globalState = window;
	globalState[_MOUNTED_SLOTS_HEADER_KEY] = header;
}
function getMountedSlotsHeader() {
	return window[_MOUNTED_SLOTS_HEADER_KEY] ?? null;
}
function getClientNavigationState() {
	const globalState = window;
	globalState[_CLIENT_NAV_STATE_KEY] ??= {
		listeners: /* @__PURE__ */ new Set(),
		cachedSearch: window.location.search,
		cachedReadonlySearchParams: new ReadonlyURLSearchParams(window.location.search),
		cachedPathname: stripBasePath(window.location.pathname, ""),
		clientParams: {},
		clientParamsJson: "{}",
		pendingClientParams: null,
		pendingClientParamsJson: null,
		pendingPathname: null,
		pendingPathnameNavId: null,
		originalPushState: window.history.pushState.bind(window.history),
		originalReplaceState: window.history.replaceState.bind(window.history),
		patchInstalled: false,
		hasPendingNavigationUpdate: false,
		suppressUrlNotifyCount: 0,
		navigationSnapshotActiveCount: 0
	};
	return globalState[_CLIENT_NAV_STATE_KEY];
}
function notifyNavigationListeners() {
	const state = getClientNavigationState();
	if (!state) return;
	for (const fn of state.listeners) fn();
}
globalThis[PAGES_NAVIGATION_NOTIFY_KEY] = notifyNavigationListeners;
function syncCommittedUrlStateFromLocation() {
	const state = getClientNavigationState();
	if (!state) return false;
	let changed = false;
	const pathname = stripBasePath(window.location.pathname, "");
	if (pathname !== state.cachedPathname) {
		state.cachedPathname = pathname;
		changed = true;
	}
	const search = window.location.search;
	if (search !== state.cachedSearch) {
		state.cachedSearch = search;
		state.cachedReadonlySearchParams = new ReadonlyURLSearchParams(search);
		changed = true;
	}
	return changed;
}
/**
* Mark a navigation snapshot as active. Called before startTransition
* in renderNavigationPayload. While active, hooks prefer the snapshot
* context value over useSyncExternalStore. Uses a counter (not boolean)
* to handle overlapping navigations — rapid clicks can interleave
* activate/deactivate if multiple transitions are in flight.
*/
function activateNavigationSnapshot() {
	const state = getClientNavigationState();
	if (state) state.navigationSnapshotActiveCount++;
}
var _CLIENT_NAV_RENDER_CTX_KEY = Symbol.for("vinext.clientNavigationRenderContext");
function getClientNavigationRenderContext() {
	if (typeof import_react.createContext !== "function") return null;
	const globalState = globalThis;
	if (!globalState[_CLIENT_NAV_RENDER_CTX_KEY]) globalState[_CLIENT_NAV_RENDER_CTX_KEY] = import_react.createContext(null);
	return globalState[_CLIENT_NAV_RENDER_CTX_KEY] ?? null;
}
function createClientNavigationRenderSnapshot(href, params) {
	const origin = window.location.origin;
	const url = new URL(href, origin);
	return {
		pathname: stripBasePath(url.pathname, ""),
		searchParams: new ReadonlyURLSearchParams(url.search),
		params
	};
}
function createSnapshotPathAndSearch(snapshot) {
	const query = snapshot.searchParams.toString();
	return query === "" ? snapshot.pathname : `${snapshot.pathname}?${query}`;
}
var _fallbackClientParamsJson = "{}";
function setClientParams(params) {
	const state = getClientNavigationState();
	if (!state) {
		const json = JSON.stringify(params);
		if (json !== _fallbackClientParamsJson) _fallbackClientParamsJson = json;
		return;
	}
	const json = JSON.stringify(params);
	if (json !== state.clientParamsJson) {
		state.clientParams = params;
		state.clientParamsJson = json;
		state.pendingClientParams = null;
		state.pendingClientParamsJson = null;
		notifyNavigationListeners();
	}
}
function replaceClientParamsWithoutNotify(params) {
	const state = getClientNavigationState();
	if (!state) return;
	const json = JSON.stringify(params);
	if (json !== state.clientParamsJson && json !== state.pendingClientParamsJson) {
		state.pendingClientParams = params;
		state.pendingClientParamsJson = json;
		state.hasPendingNavigationUpdate = true;
	}
}
/**
* Set the pending pathname for client-side navigation.
* Strips the base path before storing. Associates the pathname with the given navId
* so only that navigation (or a newer one) can clear it.
*/
function setPendingPathname(pathname, navId) {
	const state = getClientNavigationState();
	if (!state) return;
	state.pendingPathname = stripBasePath(pathname, "");
	state.pendingPathnameNavId = navId;
}
/**
* Clear the pending pathname, but only if the given navId matches the one
* that set it, or if pendingPathnameNavId is null (no active owner).
* This prevents superseded navigations from clearing state belonging to newer navigations.
*/
function clearPendingPathname(navId) {
	const state = getClientNavigationState();
	if (!state) return;
	if (state.pendingPathnameNavId === null || state.pendingPathnameNavId === navId) {
		state.pendingPathname = null;
		state.pendingPathnameNavId = null;
	}
}
function withSuppressedUrlNotifications(fn) {
	const state = getClientNavigationState();
	if (!state) return fn();
	state.suppressUrlNotifyCount += 1;
	try {
		return fn();
	} finally {
		state.suppressUrlNotifyCount -= 1;
	}
}
/**
* Commit pending client navigation state to committed snapshots.
*
* navId is optional: callers that don't own pendingPathname (for example,
* superseded pre-paint cleanup) may pass undefined to flush URL/params state
* without clearing pendingPathname owned by the active navigation. Such callers
* must opt in explicitly if they also own an activated render snapshot.
*/
function commitClientNavigationState(navId, options) {
	const state = getClientNavigationState();
	if (!state) return;
	if ((options?.releaseSnapshot ?? navId !== void 0) && state.navigationSnapshotActiveCount > 0) state.navigationSnapshotActiveCount -= 1;
	const urlChanged = syncCommittedUrlStateFromLocation();
	let paramsChanged = false;
	if (state.pendingClientParams !== null && state.pendingClientParamsJson !== null) {
		state.clientParams = state.pendingClientParams;
		state.clientParamsJson = state.pendingClientParamsJson;
		state.pendingClientParams = null;
		state.pendingClientParamsJson = null;
		paramsChanged = true;
	}
	if (state.pendingPathnameNavId === null || navId !== void 0 && state.pendingPathnameNavId === navId) {
		state.pendingPathname = null;
		state.pendingPathnameNavId = null;
	}
	const shouldNotify = urlChanged || state.hasPendingNavigationUpdate;
	state.hasPendingNavigationUpdate = false;
	if (urlChanged || paramsChanged) clearClientHydrationContext();
	if (shouldNotify) notifyNavigationListeners();
}
function pushHistoryStateWithoutNotify(data, unused, url) {
	withSuppressedUrlNotifications(() => {
		getClientNavigationState()?.originalPushState.call(window.history, data, unused, url);
	});
}
function replaceHistoryStateWithoutNotify(data, unused, url) {
	withSuppressedUrlNotifications(() => {
		getClientNavigationState()?.originalReplaceState.call(window.history, data, unused, url);
	});
}
/**
* Save the current scroll position into the current history state.
* Called before every navigation to enable scroll restoration on back/forward.
*
* Uses replaceHistoryStateWithoutNotify to avoid triggering the patched
* history.replaceState interception (which would cause spurious re-renders).
*/
function saveScrollPosition() {
	replaceHistoryStateWithoutNotify({
		...window.history.state ?? {},
		__vinext_scrollX: window.scrollX,
		__vinext_scrollY: window.scrollY
	}, "");
}
function commitHashOnlyHistoryState(href, mode, scroll) {
	const commitAppRouterHashNavigation = getNavigationRuntime()?.functions.commitHashNavigation;
	if (commitAppRouterHashNavigation) {
		commitAppRouterHashNavigation(href, mode, scroll);
		return;
	}
	const historyState = createHashOnlyHistoryStatePreservingNavigationMetadata(window.history.state);
	if (mode === "replace") replaceHistoryStateWithoutNotify(historyState, "", href);
	else pushHistoryStateWithoutNotify(historyState, "", href);
}
function applyAppRouterScrollFallback(intent) {
	if (typeof document === "undefined" || false) return;
	if (intent.hash !== null) {
		scrollToHashTargetOnNextFrame(intent.hash, () => isLatestAppRouterScrollIntent(intent));
		return;
	}
	if (intent.targetHoistedInHead) return;
	document.documentElement.scrollTop = 0;
}
function scheduleAppRouterScrollFallback(intent) {
	queueMicrotask(() => {
		const pendingIntent = getPendingAppRouterScrollIntent();
		if (pendingIntent === null || pendingIntent.id !== intent.id) return;
		const fallbackIntent = consumeAppRouterScrollIntent(intent);
		if (fallbackIntent) applyAppRouterScrollFallback(fallbackIntent);
	});
}
/**
* Restore scroll position from a history state object (used on popstate).
*
* When an RSC navigation is in flight (back/forward triggers both this
* handler and the browser entry's popstate handler which calls the registered
* navigation runtime), we must wait for the new content to render
* before scrolling. Otherwise the user sees old content flash at the
* restored scroll position.
*
* This handler fires before the browser entry's popstate handler (because
* navigation.ts is loaded before hydration completes), so we defer via a
* microtask to give the browser entry handler a chance to set
* __VINEXT_RSC_PENDING__. Promise.resolve() schedules a microtask
* that runs after all synchronous event listeners have completed.
*/
function restoreScrollPosition(state) {
	if (state && typeof state === "object" && "__vinext_scrollY" in state) {
		const { __vinext_scrollX: x, __vinext_scrollY: y } = state;
		Promise.resolve().then(() => {
			const pending = window.__VINEXT_RSC_PENDING__ ?? null;
			if (pending) pending.then(() => retryScrollTo(x, y));
			else retryScrollTo(x, y);
		});
	}
}
/**
* Hard-navigate to a URL via `window.location`, preserving push/replace
* semantics. Used for URLs the App Router cannot serve (Pages-owned
* targets in a hybrid build) and for catch-all RSC failures.
*/
function hardNavigateTo(fullHref, mode) {
	if (mode === "replace") window.location.replace(fullHref);
	else window.location.assign(fullHref);
}
/**
* Reset any link still showing a `useLinkStatus()` pending state that did not
* initiate the navigation now starting (e.g. a programmatic router.push, a form
* submit, or a raw history update). A <Link> click registers itself first, so
* the hook keeps that link pending.
*/
function resetStaleLinkStatus() {
	getNavigationRuntime()?.functions.notifyLinkNavigationStart?.();
}
/**
* Signal that a navigation to `href` is starting, for the callers that will
* fetch the destination. Separate from `resetStaleLinkStatus()` because a raw
* `history.pushState` also supersedes a pending link but issues no request —
* cancelling a prefetch there would drop it with nothing to take its place.
*/
function notifyAppNavigationStart(href) {
	const destination = toAppPrefetchDestination(href);
	if (destination !== null && !isHashOnlyBrowserUrlChange(href, window.location.href, "")) cancelPendingPrefetchSetups(destination);
	resetStaleLinkStatus();
}
/**
* popstate variant. The browser has already applied the history entry by the
* time this runs, so the pre-navigation URL that `isHashOnlyBrowserUrlChange`
* needs is gone. Back/forward across a route boundary does drive an RSC fetch
* (`app-browser-entry.ts`'s popstate handler), so cancelling by destination is
* right; a hash-only entry over-cancels, which costs one re-prefetch and can
* never cause a duplicate request.
*/
function notifyAppPopstateNavigationStart() {
	const destination = toAppPrefetchDestination(window.location.href);
	if (destination !== null) cancelPendingPrefetchSetups(destination);
	resetStaleLinkStatus();
}
/**
* Navigate to a URL, handling external URLs, hash-only changes, and RSC navigation.
*/
async function navigateClientSide(href, mode, scroll, programmaticTransition = false, visibleCommitMode = "transition") {
	notifyAppNavigationStart(href);
	let normalizedHref = href;
	if (isExternalUrl(href)) {
		const localPath = toSameOriginAppPath(href, "");
		if (localPath == null) {
			notifyAppRouterTransitionStart(href, mode);
			const externalNavigate = getNavigationRuntime()?.functions.navigateExternal;
			if (externalNavigate) {
				await externalNavigate(href, mode);
				return;
			}
			hardNavigateTo(href, mode);
			await new Promise(() => {});
			return;
		}
		normalizedHref = localPath;
	}
	const hybridOwner = resolveHybridClientRouteOwner(normalizedHref);
	if (hybridOwner === "pages" || hybridOwner === "document") {
		const fullHref = toBrowserNavigationHref(normalizedHref, window.location.href, "");
		notifyAppRouterTransitionStart(fullHref, mode);
		if (mode === "push") saveScrollPosition();
		hardNavigateTo(fullHref, mode);
		await new Promise(() => {});
		return;
	}
	const fullHref = toBrowserNavigationHref(normalizedHref, window.location.href, "");
	notifyAppRouterTransitionStart(fullHref, mode);
	if (mode === "push") saveScrollPosition();
	const earlyIntent = navigationPlanner.classifyEarlyNavigationIntent({
		basePath: "",
		currentHref: window.location.href,
		mode,
		scroll,
		targetHref: fullHref
	});
	if (earlyIntent.kind === "sameDocumentScroll") {
		clearAppRouterScrollIntent();
		commitHashOnlyHistoryState(fullHref, earlyIntent.mode, earlyIntent.scroll);
		clearAppNavigationFailureTarget(fullHref);
		commitClientNavigationState();
		if (earlyIntent.scroll) scrollToHashTarget(earlyIntent.hash);
		return;
	}
	if (hasPendingAppRouterPageRedirect(typeof document === "undefined" ? void 0 : document)) {
		const mpaNavigate = getNavigationRuntime()?.functions.navigateExternal;
		if (mpaNavigate) {
			await mpaNavigate(fullHref, mode);
			return;
		}
		hardNavigateTo(fullHref, mode);
		await new Promise(() => {});
		return;
	}
	const hashIdx = fullHref.indexOf("#");
	const hash = hashIdx !== -1 ? fullHref.slice(hashIdx) : "";
	const scrollIntent = scroll ? beginAppRouterScrollIntent(hash || null) : null;
	if (!scroll) clearAppRouterScrollIntent();
	const appNavigate = getNavigationRuntime()?.functions.navigate;
	try {
		if (appNavigate) await appNavigate(fullHref, 0, "navigate", mode, void 0, programmaticTransition, void 0, scrollIntent, visibleCommitMode);
		else {
			if (mode === "replace") replaceHistoryStateWithoutNotify(null, "", fullHref);
			else pushHistoryStateWithoutNotify(null, "", fullHref);
			commitClientNavigationState();
		}
	} catch (error) {
		if (scrollIntent) consumeAppRouterScrollIntent(scrollIntent);
		throw error;
	}
	if (scrollIntent) scheduleAppRouterScrollFallback(scrollIntent);
}
var scheduledAppRouterNavigationCount = 0;
function trackScheduledAppRouterNavigation() {
	scheduledAppRouterNavigationCount += 1;
	let released = false;
	return () => {
		if (released) return;
		released = true;
		scheduledAppRouterNavigationCount = Math.max(0, scheduledAppRouterNavigationCount - 1);
	};
}
function hasScheduledAppRouterNavigation() {
	return scheduledAppRouterNavigationCount > 0;
}
function releaseScheduledAppRouterNavigationAfterCurrentTask(release) {
	queueMicrotask(release);
}
/**
* App Router public router instance. Mirrors Next.js's
* `publicAppRouterInstance` from
* `packages/next/src/client/components/app-router-instance.ts`.
*
* Exported so the App Router browser entry can install it on
* `window.next.router` for Next.js parity (see `client/window-next.ts`).
* Internal callers in this file continue to use `_appRouter` for brevity.
*/
var _appRouter = {
	bfcacheId: "0",
	push(href, options) {
		assertSafeNavigationUrl(href);
		notifyAppNavigationStart(href);
		const releaseNavigation = trackScheduledAppRouterNavigation();
		try {
			import_react.startTransition(() => {
				navigateClientSide(href, "push", options?.scroll !== false, true);
			});
		} catch (error) {
			releaseNavigation();
			throw error;
		}
		releaseScheduledAppRouterNavigationAfterCurrentTask(releaseNavigation);
	},
	replace(href, options) {
		assertSafeNavigationUrl(href);
		notifyAppNavigationStart(href);
		const releaseNavigation = trackScheduledAppRouterNavigation();
		try {
			import_react.startTransition(() => {
				navigateClientSide(href, "replace", options?.scroll !== false, true);
			});
		} catch (error) {
			releaseNavigation();
			throw error;
		}
		releaseScheduledAppRouterNavigationAfterCurrentTask(releaseNavigation);
	},
	back() {
		window.history.back();
	},
	forward() {
		window.history.forward();
	},
	refresh() {
		getNavigationRuntime()?.functions.clearNavigationCaches?.();
		if (hasScheduledAppRouterNavigation()) return;
		const rscNavigate = getNavigationRuntime()?.functions.navigate;
		if (rscNavigate) {
			const navigate = () => {
				rscNavigate(window.location.href, 0, "refresh", void 0, void 0, true);
			};
			import_react.startTransition(navigate);
		}
	},
	prefetch(href, options) {
		assertSafeNavigationUrl(href);
		if (isBotUserAgent(window.navigator?.userAgent ?? "")) return;
		try {
			new URL(withBasePath(href, ""), window.location.href);
		} catch {
			throw new Error(`Cannot prefetch '${href}' because it cannot be converted to a URL.`);
		}
		const prefetchHref = isExternalUrl(href) ? toSameOriginAppPath(href, "") : href;
		if (prefetchHref == null) return;
		const fullHref = toAppPrefetchDestination(prefetchHref);
		if (fullHref === null) return;
		const interceptionContext = getPrefetchInterceptionContext(fullHref);
		const mountedSlotsHeader = getMountedSlotsHeader();
		const headers = createAppPrefetchRequestHeaders({
			fetchPriority: "low",
			interceptionContext,
			mountedSlotsHeader: mountedSlotsHeader || null
		});
		const setup = beginPrefetchSetup(fullHref);
		(async () => {
			const hybridOwner = resolveHybridClientRouteOwner(fullHref);
			if (hybridOwner === "pages" || hybridOwner === "document") return;
			const rewrittenPrefetchHref = null;
			const kind = options?.kind === "full" ? "full" : "auto";
			const { resolveAutoAppRoutePrefetch, resolveFullAppRoutePrefetch } = await __vitePreload(async () => {
				const { resolveAutoAppRoutePrefetch, resolveFullAppRoutePrefetch } = await import("./app-route-prefetch-policy-D8qKaZw3.js");
				return {
					resolveAutoAppRoutePrefetch,
					resolveFullAppRoutePrefetch
				};
			}, []);
			const policy = kind === "full" ? resolveFullAppRoutePrefetch() : resolveAutoAppRoutePrefetch(rewrittenPrefetchHref ?? fullHref);
			const reusable = policy.shouldPrefetch && policy.cacheForNavigation;
			if (reusable && kind === "full") headers.delete(NEXT_ROUTER_PREFETCH_HEADER);
			if (reusable && kind === "auto") {
				headers.set(NEXT_ROUTER_PREFETCH_HEADER, "1");
				headers.set(NEXT_ROUTER_SEGMENT_PREFETCH_HEADER, "1");
			}
			const [rscUrl, ...additionalRscUrls] = await Promise.all([createRscRequestUrl(fullHref, headers), ...rewrittenPrefetchHref !== null && rewrittenPrefetchHref !== fullHref ? [createRscRequestUrl(rewrittenPrefetchHref, headers)] : []]);
			if (setup.cancelled) return;
			const cacheKey = AppElementsWire.encodeCacheKey(rscUrl, interceptionContext);
			const prefetched = getPrefetchedUrls();
			if (reusable) {
				discardLearningOnlyPrefetchCacheEntry(rscUrl, interceptionContext);
				if (hasPrefetchCacheEntryForNavigation(rscUrl, interceptionContext, mountedSlotsHeader, {
					additionalRscUrls,
					onInvalidate: options?.onInvalidate
				})) return;
			} else if (prefetched.has(cacheKey)) {
				attachPrefetchInvalidationCallback(cacheKey, options?.onInvalidate);
				return;
			}
			prefetched.add(cacheKey);
			prefetchRscResponse(rscUrl, scheduleAppPrefetchFetch((signal) => fetch(rscUrl, {
				headers,
				credentials: "include",
				priority: "low",
				signal
			}), "low"), interceptionContext, mountedSlotsHeader, options, reusable ? {
				cacheForNavigation: true,
				fallbackTtlMs: policy.fallbackTtl === "dynamic" ? DYNAMIC_NAVIGATION_CACHE_TTL : PREFETCH_CACHE_TTL,
				honorDynamicStaleTime: policy.honorDynamicStaleTime,
				optimisticRouteShell: false,
				prefetchKind: "navigation",
				prepareSnapshot: prepareNavigationPrefetchSnapshot
			} : {
				cacheForNavigation: false,
				optimisticRouteShell: true,
				prefetchKind: "navigation"
			});
		})().catch((error) => {
			console.error("[vinext] RSC prefetch setup error:", error);
		}).finally(() => {
			pendingPrefetchSetups.delete(setup);
		});
	}
};
function formatPublicBfcacheId(value) {
	if (!value || value === "0") return PUBLIC_INITIAL_BFCACHE_ID;
	return value;
}
function readBfcacheIdFromContext() {
	const segmentContext = getBfcacheSegmentIdContext();
	const idMapContext = getBfcacheIdMapContext();
	if (!segmentContext || !idMapContext || typeof import_react.useContext !== "function") return formatPublicBfcacheId(null);
	try {
		const segmentId = import_react.useContext(segmentContext);
		const idMap = import_react.useContext(idMapContext);
		return formatPublicBfcacheId(segmentId !== null ? idMap?.[segmentId] : null);
	} catch (error) {
		return formatPublicBfcacheId(null);
	}
}
/**
* Public App Router instance, exposed for the browser entry so it can wire
* `window.next.router` to the same singleton returned from `useRouter()`.
*
* Mirrors `publicAppRouterInstance` from Next.js's
* `packages/next/src/client/components/app-router-instance.ts` (line 392).
*/
var appRouterInstance = _appRouter;
/**
* App Router's useRouter — returns push/replace/back/forward/refresh.
* Different from Pages Router's useRouter (next/router).
*
* Preserves the mounted AppRouterContext router as the authority for methods
* and layers the nearest segment's contextual `bfcacheId` on top.
*/
function useRouter() {
	if (!AppRouterContext || typeof import_react.useContext !== "function" || typeof import_react.useMemo !== "function") throw new Error("invariant expected app router to be mounted");
	const router = import_react.useContext(AppRouterContext);
	if (router === null) throw new Error("invariant expected app router to be mounted");
	const bfcacheId = readBfcacheIdFromContext();
	return import_react.useMemo(() => ({
		...router,
		bfcacheId
	}), [router, bfcacheId]);
}
{
	const state = getClientNavigationState();
	if (state && !state.patchInstalled) {
		state.patchInstalled = true;
		window.addEventListener("popstate", () => {
			notifyAppPopstateNavigationStart();
		});
		window.addEventListener("popstate", (event) => {
			if (!hasAppNavigationRuntime()) {
				commitClientNavigationState();
				restoreScrollPosition(event.state);
			}
		});
		window.history.pushState = function patchedPushState(data, unused, url) {
			state.originalPushState.call(window.history, createExternalHistoryStatePreservingMetadata(data, window.history.state), unused, url);
			if (state.suppressUrlNotifyCount === 0) {
				resetStaleLinkStatus();
				commitClientNavigationState();
			}
		};
		window.history.replaceState = function patchedReplaceState(data, unused, url) {
			state.originalReplaceState.call(window.history, createExternalHistoryStatePreservingMetadata(data, window.history.state), unused, url);
			if (state.suppressUrlNotifyCount === 0) {
				resetStaleLinkStatus();
				commitClientNavigationState();
			}
		};
	}
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-rsc-embedded-chunks.js
var textEncoder = new TextEncoder();
function base64ToBytes(base64) {
	const binary = atob(base64);
	const bytes = new Uint8Array(binary.length);
	for (let index = 0; index < binary.length; index++) bytes[index] = binary.charCodeAt(index);
	return bytes;
}
function decodeRscEmbeddedChunk(chunk) {
	if (typeof chunk === "string") return textEncoder.encode(chunk);
	return base64ToBytes(chunk[1]);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-browser-stream.js
function getVinextBrowserGlobal() {
	return globalThis;
}
function createUnexpectedRscStreamCloseError() {
	return /* @__PURE__ */ new Error("The connection to the page was unexpectedly closed, possibly due to the stop button being clicked, loss of Wi-Fi, or an unstable internet connection.");
}
/**
* Convert embedded chunks back to a ReadableStream of Uint8Array chunks.
*/
function chunksToReadableStream(chunks) {
	return new ReadableStream({ start(controller) {
		for (const chunk of chunks) controller.enqueue(decodeRscEmbeddedChunk(chunk));
		controller.close();
	} });
}
function getNavigationRuntimeRscBootstrap() {
	return getNavigationRuntime()?.bootstrap.rsc ?? null;
}
/**
* Create a ReadableStream from progressively-embedded RSC chunks.
*
* The server pushes chunks into the typed navigation runtime via inline
* <script> tags. We monkey-patch `push()` so new chunks stream to React
* immediately instead of polling with setTimeout.
*/
function createProgressiveRscStream() {
	let cancelStream;
	return new ReadableStream({
		start(controller) {
			const vinext = getVinextBrowserGlobal();
			const runtimeRsc = getNavigationRuntimeRscBootstrap();
			const initialChunks = runtimeRsc?.rsc ?? vinext.__VINEXT_RSC_CHUNKS__ ?? [];
			for (const chunk of initialChunks) controller.enqueue(decodeRscEmbeddedChunk(chunk));
			if (runtimeRsc?.done || vinext.__VINEXT_RSC_DONE__) {
				controller.close();
				return;
			}
			let closed = false;
			let cancelDocumentCompletionCheck;
			const cancelPendingDocumentCompletionCheck = () => {
				const cancel = cancelDocumentCompletionCheck;
				cancelDocumentCompletionCheck = void 0;
				cancel?.();
			};
			const closeOnce = () => {
				if (!closed) {
					closed = true;
					cancelPendingDocumentCompletionCheck();
					controller.close();
				}
			};
			const scheduleCloseOnce = () => {
				if (typeof queueMicrotask === "function") queueMicrotask(closeOnce);
				else Promise.resolve().then(closeOnce);
			};
			const errorOnce = () => {
				if (!closed) {
					closed = true;
					cancelPendingDocumentCompletionCheck();
					controller.error(createUnexpectedRscStreamCloseError());
				}
			};
			cancelStream = () => {
				if (!closed) {
					closed = true;
					cancelPendingDocumentCompletionCheck();
				}
			};
			const liveRuntimeRsc = getNavigationRuntime() === null ? null : ensureNavigationRuntimeRscBootstrap();
			const arr = liveRuntimeRsc?.rsc ?? (vinext.__VINEXT_RSC_CHUNKS__ ??= []);
			arr.push = function(...chunks) {
				const length = Array.prototype.push.apply(this, chunks);
				if (closed) return length;
				for (const chunk of chunks) controller.enqueue(decodeRscEmbeddedChunk(chunk));
				if (liveRuntimeRsc?.done || vinext.__VINEXT_RSC_DONE__) closeOnce();
				return length;
			};
			if (liveRuntimeRsc) {
				let done = Boolean(liveRuntimeRsc.done);
				Object.defineProperty(liveRuntimeRsc, "done", {
					configurable: true,
					enumerable: true,
					get() {
						return done;
					},
					set(value) {
						done = Boolean(value);
						if (done) scheduleCloseOnce();
					}
				});
			} else {
				let done = Boolean(vinext.__VINEXT_RSC_DONE__);
				Object.defineProperty(vinext, "__VINEXT_RSC_DONE__", {
					configurable: true,
					enumerable: true,
					get() {
						return done;
					},
					set(value) {
						done = Boolean(value);
						if (done) scheduleCloseOnce();
					}
				});
			}
			if (typeof document !== "undefined") if (document.readyState === "loading") {
				document.addEventListener("DOMContentLoaded", errorOnce);
				cancelDocumentCompletionCheck = () => document.removeEventListener("DOMContentLoaded", errorOnce);
			} else {
				const timeoutId = setTimeout(errorOnce);
				cancelDocumentCompletionCheck = () => clearTimeout(timeoutId);
			}
		},
		cancel() {
			cancelStream?.();
		}
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-browser-state.js
var COMMITTED_CACHE_APP_NAVIGATION_PAYLOAD_ORIGIN = { origin: "committed-cache" };
var FRESH_APP_NAVIGATION_PAYLOAD_ORIGIN = { origin: "fresh" };
var VISITED_CACHE_APP_NAVIGATION_PAYLOAD_ORIGIN = { origin: "visited-cache" };
function createOperationRecord(options) {
	return {
		id: options.id,
		lane: options.lane,
		...options.navigationCommitKind !== void 0 ? { navigationCommitKind: options.navigationCommitKind } : {},
		...options.navigationId !== void 0 ? { navigationId: options.navigationId } : {},
		startedVisibleCommitVersion: options.startedVisibleCommitVersion,
		state: "pending"
	};
}
function isCompleteAppPayloadMetadata(metadata) {
	return metadata.skippedLayoutIds.length === 0;
}
function isCacheRestorableAppPayloadMetadata(metadata) {
	return metadata.cacheEntryReuseProof !== void 0 && isCompleteAppPayloadMetadata(metadata);
}
function requiresCacheEntryReuseProof(origin) {
	switch (origin.origin) {
		case "committed-cache":
		case "fresh": return false;
		case "visited-cache": return true;
		default: throw new Error("[vinext] Unknown App Router payload origin: " + String(origin));
	}
}
function normalizeNavigationSnapshotMatchedUrl(pathname) {
	return normalizePath(normalizePathnameForRouteMatch(pathname));
}
function createRouteSnapshotRouteId(options) {
	if (options.interception !== null) return options.routeId;
	const parsed = AppElementsWire.parseElementKey(options.routeId);
	if (parsed?.kind !== "route" || parsed.interceptionContext === null) return options.routeId;
	return AppElementsWire.encodeRouteId(parsed.path, null);
}
function resolveInterceptionContextFromPreviousNextUrl(previousNextUrl, basePath = "") {
	if (previousNextUrl === null) return null;
	return stripBasePath(new URL(previousNextUrl, "http://localhost").pathname, basePath);
}
function resolvePendingNavigationCommitDispositionDecision(options) {
	const traceFields = createPendingNavigationTraceFields(options);
	const targetSnapshot = createPendingRouteSnapshot(options.pending);
	const token = createPendingNavigationOperationToken({
		pending: options.pending,
		routeManifest: options.routeManifest ?? null,
		startedNavigationId: options.startedNavigationId,
		targetSnapshot
	});
	if (options.pending.action.operation.navigationCommitKind === "detached" && options.currentState.activeOperation?.navigationId === options.startedNavigationId && options.currentState.activeOperation.navigationCommitKind === "authoritative") return {
		disposition: "skip",
		preserveElementIds: [],
		trace: createNavigationTrace(NavigationTraceReasonCodes.staleOperation, traceFields)
	};
	const visibleCommitVersion = options.currentState.activeOperation?.navigationId === options.startedNavigationId && options.currentState.activeOperation.navigationCommitKind === "detached" && options.pending.action.operation.navigationCommitKind === "authoritative" ? options.pending.action.operation.startedVisibleCommitVersion : options.currentState.visibleCommitVersion;
	const verdict = verifyOperationTokenForCommit(token, {
		activeNavigationId: options.activeNavigationId,
		visibleCommitVersion
	});
	if (!verdict.authorized) return {
		disposition: "skip",
		preserveElementIds: [],
		trace: createNavigationTrace(NavigationTraceReasonCodes.staleOperation, traceFields)
	};
	const decision = mapNavigationDecisionToPendingDisposition(planPendingRootBoundaryFlightResponse({
		currentState: options.currentState,
		pending: options.pending,
		routeManifest: options.routeManifest ?? null,
		targetHref: options.targetHref,
		targetSnapshot,
		token: verdict.token,
		traceFields
	}));
	return mergeSkippedLayoutPreservation({
		currentState: options.currentState,
		decision,
		pending: options.pending
	});
}
function createPendingNavigationTraceFields(options) {
	return {
		...createNavigationLifecycleTraceFields({
			activeNavigationId: options.activeNavigationId,
			currentRootLayoutTreePath: options.currentState.rootLayoutTreePath,
			currentVisibleCommitVersion: options.currentState.visibleCommitVersion,
			nextRootLayoutTreePath: options.pending.rootLayoutTreePath,
			startedNavigationId: options.startedNavigationId,
			startedVisibleCommitVersion: options.pending.action.operation.startedVisibleCommitVersion
		}),
		...options.targetHref !== void 0 ? { targetHref: options.targetHref } : {}
	};
}
function createMountedParallelSlotSnapshots(elements) {
	const snapshots = [];
	for (const slotId of getMountedSlotIds(elements)) {
		const parsed = AppElementsWire.parseElementKey(slotId);
		if (parsed?.kind !== "slot") continue;
		snapshots.push({
			ownerLayoutId: AppElementsWire.encodeLayoutId(parsed.treePath),
			slotId
		});
	}
	return snapshots;
}
function createVisibleRouteSnapshot(state) {
	const displayUrl = createSnapshotPathAndSearch(state.navigationSnapshot);
	const matchedUrl = state.interception?.targetMatchedUrl ?? normalizeNavigationSnapshotMatchedUrl(state.navigationSnapshot.pathname);
	return {
		displayUrl,
		interception: state.interception,
		interceptionContext: state.interceptionContext,
		layoutIds: state.layoutIds,
		matchedUrl,
		mountedParallelSlots: createMountedParallelSlotSnapshots(state.elements),
		rootBoundaryId: state.rootLayoutTreePath,
		routeId: createRouteSnapshotRouteId({
			interception: state.interception,
			routeId: state.routeId
		}),
		slotBindings: state.slotBindings
	};
}
function createPendingRouteSnapshot(pending) {
	const displayUrl = createSnapshotPathAndSearch(pending.action.navigationSnapshot);
	const matchedUrl = pending.action.interception?.targetMatchedUrl ?? normalizeNavigationSnapshotMatchedUrl(pending.action.navigationSnapshot.pathname);
	return {
		displayUrl,
		interception: pending.action.interception,
		interceptionContext: pending.action.interceptionContext,
		layoutIds: pending.action.layoutIds,
		matchedUrl,
		mountedParallelSlots: createMountedParallelSlotSnapshots(pending.action.elements),
		rootBoundaryId: pending.rootLayoutTreePath,
		routeId: createRouteSnapshotRouteId({
			interception: pending.action.interception,
			routeId: pending.routeId
		}),
		slotBindings: pending.action.slotBindings
	};
}
function createPendingNavigationOperationToken(options) {
	return {
		baseVisibleCommitVersion: options.pending.action.operation.startedVisibleCommitVersion,
		deploymentVersion: null,
		graphVersion: options.routeManifest?.graphVersion ?? null,
		lane: options.pending.action.operation.lane,
		navigationId: options.startedNavigationId,
		operationId: options.pending.action.operation.id,
		targetSnapshotFingerprint: createRootBoundarySnapshotFingerprint(options.targetSnapshot)
	};
}
function createRootBoundarySnapshotFingerprint(snapshot) {
	return `${snapshot.routeId}|root:${snapshot.rootBoundaryId ?? "unknown"}`;
}
function planPendingRootBoundaryFlightResponse(options) {
	const cacheEntryReuseProof = options.pending.cacheEntryReuseProof;
	return navigationPlanner.plan({
		routeManifest: options.routeManifest,
		state: {
			nextOperationToken: options.token,
			traceFields: options.traceFields,
			visibleCommitVersion: options.currentState.visibleCommitVersion,
			visibleSnapshot: createVisibleRouteSnapshot(options.currentState)
		},
		event: {
			kind: "flightResponseArrived",
			result: {
				...cacheEntryReuseProof ? { cacheEntryReuseProof } : {},
				...options.pending.restoredHistorySnapshot ? { restoredHistorySnapshot: true } : {},
				href: options.targetHref ?? options.targetSnapshot.displayUrl,
				targetSnapshot: options.targetSnapshot
			},
			token: options.token
		}
	});
}
function mapNavigationDecisionToPendingDisposition(decision) {
	switch (decision.kind) {
		case "proposeCommit": return {
			disposition: "dispatch",
			preserveAbsentSlots: decision.proposal.preserveAbsentSlots,
			preserveElementIds: decision.proposal.preserveElementIds,
			preservePreviousSlotIds: decision.proposal.preservePreviousSlotIds,
			trace: decision.trace
		};
		case "hardNavigate": return {
			disposition: "hard-navigate",
			preserveElementIds: [],
			trace: decision.trace
		};
		case "noCommit": return {
			disposition: "skip",
			preserveElementIds: [],
			trace: decision.trace
		};
		case "requestWork": throw new Error(`[vinext] Root-boundary commit planning returned requestWork (${decision.work.kind}); flightResponseArrived should never request work`);
		default: throw new Error("[vinext] Unknown navigation decision: " + String(decision));
	}
}
function mergeSkippedLayoutPreservation(options) {
	if (options.decision.disposition !== "dispatch") return options.decision;
	if (options.pending.skippedLayoutIds.length === 0) return options.decision;
	const currentLayoutIds = new Set(options.currentState.layoutIds);
	const targetLayoutIds = new Set(options.pending.action.layoutIds);
	const preserveElementIds = [...options.decision.preserveElementIds];
	const seenPreservedIds = new Set(preserveElementIds);
	const newlyPreservedLayoutIds = [];
	for (const id of options.pending.skippedLayoutIds) {
		if (seenPreservedIds.has(id)) continue;
		if (AppElementsWire.parseElementKey(id)?.kind !== "layout") continue;
		if (!currentLayoutIds.has(id) || !targetLayoutIds.has(id)) continue;
		if (!Object.hasOwn(options.currentState.elements, id)) continue;
		preserveElementIds.push(id);
		seenPreservedIds.add(id);
		newlyPreservedLayoutIds.push(id);
	}
	if (newlyPreservedLayoutIds.length === 0) return options.decision;
	const preservePreviousSlotIds = mergeSkippedLayoutSlotPreservation({
		currentSlotBindings: options.currentState.slotBindings,
		preservePreviousSlotIds: options.decision.preservePreviousSlotIds,
		skippedLayoutIds: newlyPreservedLayoutIds,
		targetSlotBindings: options.pending.action.slotBindings
	});
	return {
		...options.decision,
		preserveElementIds,
		preservePreviousSlotIds
	};
}
function mergeSkippedLayoutSlotPreservation(options) {
	const ownedSlotIds = resolveDefaultOrUnmatchedSlotPersistenceForLayouts({
		currentSlotBindings: options.currentSlotBindings,
		preservedLayoutIds: options.skippedLayoutIds,
		targetSlotBindings: options.targetSlotBindings
	});
	if (ownedSlotIds.length === 0) return options.preservePreviousSlotIds;
	const preservePreviousSlotIds = [...options.preservePreviousSlotIds];
	const seenSlotIds = new Set(preservePreviousSlotIds);
	for (const slotId of ownedSlotIds) {
		if (seenSlotIds.has(slotId)) continue;
		preservePreviousSlotIds.push(slotId);
		seenSlotIds.add(slotId);
	}
	return preservePreviousSlotIds;
}
function createPendingNavigationCommitFromElements(options) {
	const elements = options.nextElements;
	const metadata = AppElementsWire.readMetadata(elements);
	const cacheEntryReuseProof = metadata.cacheEntryReuseProof ?? (requiresCacheEntryReuseProof(options.payloadOrigin) ? createCacheEntryReuseProof(null) : void 0);
	const requestedPreviousNextUrl = options.previousNextUrl !== void 0 ? options.previousNextUrl : options.currentState.previousNextUrl;
	const previousNextUrl = metadata.interception === null ? null : requestedPreviousNextUrl;
	return {
		action: {
			bfcacheIds: createNextBfcacheIdMap({
				current: options.currentState.bfcacheIds,
				currentElements: options.currentState.elements,
				elements,
				restored: options.restoredBfcacheIds,
				reuseCurrent: options.reuseCurrentBfcacheIds
			}),
			...cacheEntryReuseProof ? { cacheEntryReuseProof } : {},
			elements,
			interception: metadata.interception,
			interceptionContext: metadata.interceptionContext,
			layoutIds: metadata.layoutIds,
			layoutFlags: metadata.layoutFlags,
			slotBindings: metadata.slotBindings,
			navigationSnapshot: options.navigationSnapshot,
			operation: createOperationRecord({
				id: options.renderId,
				lane: options.operationLane,
				navigationCommitKind: options.navigationCommitKind,
				navigationId: options.navigationId,
				startedVisibleCommitVersion: options.currentState.visibleCommitVersion
			}),
			previousNextUrl,
			renderId: options.renderId,
			rootLayoutTreePath: metadata.rootLayoutTreePath,
			reuseCurrentBfcacheIds: options.reuseCurrentBfcacheIds ?? true,
			routeId: metadata.routeId,
			skippedLayoutIds: metadata.skippedLayoutIds,
			type: options.type
		},
		...cacheEntryReuseProof ? { cacheEntryReuseProof } : {},
		interception: metadata.interception,
		interceptionContext: metadata.interceptionContext,
		previousNextUrl,
		rootLayoutTreePath: metadata.rootLayoutTreePath,
		routeId: metadata.routeId,
		skippedLayoutIds: metadata.skippedLayoutIds
	};
}
async function createPendingNavigationCommit(options) {
	return createPendingNavigationCommitFromElements({
		...options,
		nextElements: await options.nextElements
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-browser-visible-commit.js
var approvedVisibleCommitBrand = Symbol("ApprovedVisibleCommit");
function applyApprovedVisibleCommit(state, commit) {
	assertApprovedVisibleCommit(commit);
	return reduceApprovedVisibleCommitState(state, commit);
}
function assertApprovedVisibleCommit(commit) {
	if (commit[approvedVisibleCommitBrand] !== true) throw new Error("[vinext] Visible router state mutation requires ApprovedVisibleCommit");
}
function commitOperationRecord(operation, visibleCommitVersion) {
	return {
		id: operation.id,
		lane: operation.lane,
		...operation.navigationCommitKind !== void 0 ? { navigationCommitKind: operation.navigationCommitKind } : {},
		...operation.navigationId !== void 0 ? { navigationId: operation.navigationId } : {},
		startedVisibleCommitVersion: operation.startedVisibleCommitVersion,
		state: "committed",
		visibleCommitVersion
	};
}
function commitVisibleRouterState(state, nextState, operation) {
	const visibleCommitVersion = state.visibleCommitVersion + 1;
	return {
		...nextState,
		activeOperation: commitOperationRecord(operation, visibleCommitVersion),
		visibleCommitVersion
	};
}
function mergeSlotBindings(previousBindings, nextBindings, layoutIds, preservePreviousSlotIds) {
	if (preservePreviousSlotIds.length === 0) return nextBindings;
	const preservedSlotIds = new Set(preservePreviousSlotIds);
	const previousBindingsBySlotId = /* @__PURE__ */ new Map();
	for (const binding of previousBindings) {
		if (!preservedSlotIds.has(binding.slotId)) continue;
		previousBindingsBySlotId.set(binding.slotId, binding);
	}
	const mergedBindings = [];
	const seenSlotIds = /* @__PURE__ */ new Set();
	for (const binding of nextBindings) {
		const previousBinding = previousBindingsBySlotId.get(binding.slotId);
		mergedBindings.push(previousBinding ?? binding);
		seenSlotIds.add(binding.slotId);
	}
	for (const slotId of preservePreviousSlotIds) {
		if (seenSlotIds.has(slotId)) continue;
		const previousBinding = previousBindingsBySlotId.get(slotId);
		if (previousBinding) mergedBindings.push(previousBinding);
	}
	return normalizeAppElementsSlotBindings(mergedBindings, { layoutIds });
}
function reduceApprovedVisibleCommitState(state, commit) {
	const { action } = commit;
	switch (action.type) {
		case "traverse":
		case "navigate":
		case "replace": {
			const bfcacheCompatiblePreserveElementIds = action.reuseCurrentBfcacheIds && action.operation.lane !== "refresh" ? commit.decision.preserveElementIds.filter((id) => {
				const previousBfcacheId = state.bfcacheIds[id];
				return previousBfcacheId !== void 0 && action.bfcacheIds[id] === previousBfcacheId;
			}) : [];
			const preservedSlotOwnerElementIdSet = new Set(bfcacheCompatiblePreserveElementIds);
			const preservePreviousSlotIds = action.reuseCurrentBfcacheIds ? commit.decision.preservePreviousSlotIds.filter((slotId) => {
				const targetBinding = action.slotBindings.find((binding) => binding.slotId === slotId);
				return targetBinding?.ownerLayoutId !== null && targetBinding?.ownerLayoutId !== void 0 && preservedSlotOwnerElementIdSet.has(targetBinding.ownerLayoutId);
			}) : [];
			const previousBfcacheIdentities = createBfcacheSegmentIdentityMap({ elements: state.elements });
			const preservePreviousBfcacheIdIds = preservePreviousSlotIds.filter((id) => previousBfcacheIdentities[id] !== void 0);
			const hmrPreservedSlotOwnerLayoutIds = action.operation.lane === "hmr" ? bfcacheCompatiblePreserveElementIds.filter((id) => preservePreviousSlotIds.some((slotId) => {
				return action.slotBindings.find((binding) => binding.slotId === slotId)?.ownerLayoutId === id;
			})) : [];
			const hmrPreserveElementIds = action.operation.lane === "hmr" && state.routeId === action.routeId && Object.hasOwn(state.elements, state.routeId) ? [state.routeId, ...hmrPreservedSlotOwnerLayoutIds] : hmrPreservedSlotOwnerLayoutIds;
			const hmrUniquePreserveElementIds = hmrPreserveElementIds.length > 1 ? [...new Set(hmrPreserveElementIds)] : hmrPreserveElementIds;
			const preserveElementIds = action.operation.lane === "hmr" ? hmrUniquePreserveElementIds : bfcacheCompatiblePreserveElementIds;
			const mergedElements = mergeElements(state.elements, action.elements, {
				clearAbsentSlots: action.type === "traverse" || !action.reuseCurrentBfcacheIds,
				preserveAbsentSlots: action.reuseCurrentBfcacheIds && commit.decision.preserveAbsentSlots,
				preserveElementIds,
				preservePreviousSlotIds
			});
			return commitVisibleRouterState(state, {
				bfcacheIds: preserveBfcacheIdsForMergedElements({
					elements: mergedElements,
					next: action.bfcacheIds,
					previous: action.reuseCurrentBfcacheIds ? state.bfcacheIds : {},
					preservedElementIds: preservePreviousSlotIds,
					preservePreviousIds: preservePreviousBfcacheIdIds
				}),
				elements: mergedElements,
				interception: action.interception,
				interceptionContext: action.interceptionContext,
				layoutFlags: mergeLayoutFlags(state.layoutFlags, action.layoutFlags, preserveElementIds),
				layoutIds: action.layoutIds,
				navigationSnapshot: action.navigationSnapshot,
				previousNextUrl: action.previousNextUrl,
				renderId: action.renderId,
				rootLayoutTreePath: action.rootLayoutTreePath,
				routeId: action.routeId,
				slotBindings: mergeSlotBindings(state.slotBindings, action.slotBindings, action.layoutIds, preservePreviousSlotIds)
			}, action.operation);
		}
		default: {
			const _exhaustive = action.type;
			throw new Error("[vinext] Unknown router action: " + String(_exhaustive));
		}
	}
}
function resolvePendingNavigationCommitDecision(options) {
	const decision = resolvePendingNavigationCommitDispositionDecision(options);
	switch (decision.disposition) {
		case "skip": return {
			disposition: "no-commit",
			trace: decision.trace
		};
		case "hard-navigate": return {
			disposition: "hard-navigate",
			trace: decision.trace
		};
		case "dispatch": return createVisibleCommitDecision(decision.trace, decision.preserveElementIds, decision.preserveAbsentSlots, decision.preservePreviousSlotIds);
		default: throw new Error("[vinext] Unknown navigation commit disposition: " + String(decision));
	}
}
function createVisibleCommitDecision(trace = createNavigationTrace(NavigationTraceReasonCodes.commitCurrent), preserveElementIds = [], preserveAbsentSlots = false, preservePreviousSlotIds = []) {
	return {
		disposition: "commit",
		preserveAbsentSlots,
		preserveElementIds: [...preserveElementIds],
		preservePreviousSlotIds: [...preservePreviousSlotIds],
		trace
	};
}
function mergeLayoutFlags(previousFlags, nextFlags, preserveElementIds) {
	const merged = { ...nextFlags };
	for (const id of preserveElementIds) {
		if (Object.hasOwn(merged, id)) continue;
		const value = previousFlags[id];
		if (value) merged[id] = value;
	}
	return merged;
}
function createApprovedVisibleCommit(options) {
	return {
		[approvedVisibleCommitBrand]: true,
		action: options.pending.action,
		decision: options.decision,
		interception: options.pending.interception,
		interceptionContext: options.pending.interceptionContext,
		previousNextUrl: options.pending.previousNextUrl,
		rootLayoutTreePath: options.pending.rootLayoutTreePath,
		routeId: options.pending.routeId
	};
}
function createCommitTransactionFields(pending) {
	return {
		operationLane: pending.action.operation.lane,
		pendingOperationId: pending.action.operation.id,
		startedVisibleCommitVersion: pending.action.operation.startedVisibleCommitVersion
	};
}
function prependCommitTransactionTrace(trace, code, pending) {
	return prependNavigationTraceEntry(trace, code, createCommitTransactionFields(pending));
}
function addCommitTransactionTrace(decision, pending) {
	switch (decision.disposition) {
		case "commit": return {
			...decision,
			trace: prependCommitTransactionTrace(decision.trace, NavigationTraceTransactionCodes.visibleCommit, pending)
		};
		case "hard-navigate": return {
			...decision,
			trace: prependCommitTransactionTrace(decision.trace, NavigationTraceTransactionCodes.hardNavigate, pending)
		};
		case "no-commit": return {
			...decision,
			trace: prependCommitTransactionTrace(decision.trace, NavigationTraceTransactionCodes.noCommit, pending)
		};
		default: throw new Error("[vinext] Unknown commit decision: " + String(decision));
	}
}
function approveHmrVisibleCommit(options) {
	const { currentState, pending } = options;
	if (pending.action.operation.lane !== "hmr") throw new Error("[vinext] HMR visible commit approval requires an HMR pending operation");
	const tracedDecision = addCommitTransactionTrace(resolvePendingNavigationCommitDecision({
		activeNavigationId: pending.action.operation.id,
		currentState,
		pending,
		routeManifest: options.routeManifest,
		startedNavigationId: pending.action.operation.id,
		targetHref: options.targetHref
	}), pending);
	if (tracedDecision.disposition === "commit") return {
		approvedCommit: createApprovedVisibleCommit({
			decision: tracedDecision,
			pending
		}),
		decision: tracedDecision
	};
	return {
		approvedCommit: null,
		decision: tracedDecision
	};
}
function approvePendingNavigationCommit(options) {
	const decision = addCommitTransactionTrace(resolvePendingNavigationCommitDecision({
		activeNavigationId: options.activeNavigationId,
		currentState: options.currentState,
		pending: options.pending,
		routeManifest: options.routeManifest ?? null,
		startedNavigationId: options.startedNavigationId,
		targetHref: options.targetHref
	}), options.pending);
	switch (decision.disposition) {
		case "commit": return {
			approvedCommit: createApprovedVisibleCommit({
				decision,
				pending: options.pending
			}),
			decision
		};
		case "hard-navigate":
		case "no-commit": return {
			approvedCommit: null,
			decision
		};
		default: throw new Error("[vinext] Unknown commit decision: " + String(decision));
	}
}
async function resolveAndClassifyNavigationCommit(options) {
	const pending = await createPendingNavigationCommit({
		currentState: options.currentState,
		navigationCommitKind: void 0,
		navigationId: options.startedNavigationId,
		nextElements: options.nextElements,
		navigationSnapshot: options.navigationSnapshot,
		operationLane: options.operationLane,
		payloadOrigin: options.payloadOrigin,
		previousNextUrl: options.previousNextUrl,
		renderId: options.renderId,
		type: options.type
	});
	const approvalState = options.getCurrentStateForApproval?.() ?? options.currentState;
	const approval = approvePendingNavigationCommit({
		activeNavigationId: options.getActiveNavigationId?.() ?? options.activeNavigationId,
		currentState: approvalState,
		pending,
		routeManifest: options.routeManifest ?? null,
		startedNavigationId: options.startedNavigationId,
		targetHref: options.targetHref
	});
	return {
		approvedCommit: approval.approvedCommit,
		decision: approval.decision,
		pending,
		trace: approval.decision.trace
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-browser-navigation-controller.js
var HARD_NAVIGATION_LOOP_GUARD_KEY = "__vinext_hard_navigation_target__";
function normalizeBrowserHref(href) {
	try {
		return new URL(href, window.location.href).href;
	} catch {
		return href;
	}
}
function readHardNavigationLoopGuard() {
	try {
		return window.sessionStorage.getItem(HARD_NAVIGATION_LOOP_GUARD_KEY);
	} catch {
		return null;
	}
}
function writeHardNavigationLoopGuard(targetHref) {
	try {
		window.sessionStorage.setItem(HARD_NAVIGATION_LOOP_GUARD_KEY, targetHref);
		return window.sessionStorage.getItem(HARD_NAVIGATION_LOOP_GUARD_KEY) === targetHref;
	} catch {
		return false;
	}
}
function clearHardNavigationLoopGuard() {
	try {
		window.sessionStorage.removeItem(HARD_NAVIGATION_LOOP_GUARD_KEY);
	} catch {}
}
function performHardNavigationWithLoopGuard(href, mode = "assign") {
	const targetHref = normalizeBrowserHref(href);
	const currentHref = normalizeBrowserHref(window.location.href);
	if (readHardNavigationLoopGuard() === targetHref && currentHref === targetHref) {
		clearHardNavigationLoopGuard();
		console.error(`[vinext] Prevented repeated hard navigation to ${targetHref}; leaving the current document in place to avoid a reload loop.`);
		return false;
	}
	if (!writeHardNavigationLoopGuard(targetHref) && currentHref === targetHref) {
		console.error(`[vinext] Hard navigation to ${targetHref} requires a reload-loop guard, but sessionStorage is unavailable; leaving the current document in place.`);
		return false;
	}
	if (mode === "replace") window.location.replace(href);
	else window.location.assign(href);
	return true;
}
function createBasePathStrippedPathAndSearch(url, basePath) {
	const pathname = stripBasePath(url.pathname, basePath);
	const query = new URLSearchParams(url.search).toString();
	return query === "" ? pathname : `${pathname}?${query}`;
}
function isSnapshotTargetHref(basePath, snapshot, targetHref) {
	try {
		const baseHref = window.location.href;
		return createBasePathStrippedPathAndSearch(new URL(targetHref, baseHref), basePath) === createSnapshotPathAndSearch(snapshot);
	} catch {
		return false;
	}
}
function createAppBrowserNavigationController(deps = {}) {
	const basePath = deps.basePath ?? "";
	const commitClientNavigationStateImpl = deps.commitClientNavigationState ?? commitClientNavigationState;
	const performHardNavigation = deps.performHardNavigation ?? performHardNavigationWithLoopGuard;
	const getRouteManifest = deps.getRouteManifest ?? (() => null);
	const syncHistoryStatePreviousNextUrl = deps.syncHistoryStatePreviousNextUrl ?? (() => {});
	let nextNavigationRenderId = 0;
	let activeNavigationId = 0;
	let pendingUserNavigationId = null;
	let pendingUserNavigationLane = null;
	let latestHmrUpdateId = 0;
	const pendingNavigationCommits = /* @__PURE__ */ new Map();
	const pendingNavigationFailureTargets = /* @__PURE__ */ new Map();
	const pendingNavigationPrePaintEffects = /* @__PURE__ */ new Map();
	let setBrowserRouterState = null;
	let browserRouterStateRef = null;
	let activePendingBrowserRouterState = null;
	let resolveBrowserRouterStateReady = null;
	let browserRouterStateReadyPromise = null;
	let browserRouterStateHasCommitted = false;
	function getBrowserRouterStateSetter() {
		if (!setBrowserRouterState) throw new Error("[vinext] Browser router state setter is not initialized");
		return setBrowserRouterState;
	}
	function getBrowserRouterState() {
		if (!browserRouterStateRef) throw new Error("[vinext] Browser router state is not initialized");
		return browserRouterStateRef.current;
	}
	function waitForBrowserRouterStateReady() {
		if (browserRouterStateRef || browserRouterStateHasCommitted) return Promise.resolve();
		if (!browserRouterStateReadyPromise) browserRouterStateReadyPromise = new Promise((resolve) => {
			resolveBrowserRouterStateReady = resolve;
		});
		return browserRouterStateReadyPromise;
	}
	function markBrowserRouterStateReady() {
		browserRouterStateHasCommitted = true;
		const resolveReady = resolveBrowserRouterStateReady;
		resolveBrowserRouterStateReady = null;
		browserRouterStateReadyPromise = null;
		resolveReady?.();
	}
	function beginNavigation() {
		latestHmrUpdateId += 1;
		activeNavigationId += 1;
		pendingUserNavigationId = activeNavigationId;
		pendingUserNavigationLane = null;
		return activeNavigationId;
	}
	function getActiveNavigationId() {
		return activeNavigationId;
	}
	function allocateRenderId() {
		nextNavigationRenderId += 1;
		return nextNavigationRenderId;
	}
	function hasBrowserRouterState() {
		return browserRouterStateRef !== null;
	}
	function isCurrentNavigation(navId) {
		return navId === activeNavigationId;
	}
	function beginPendingBrowserRouterState() {
		const setter = getBrowserRouterStateSetter();
		if (activePendingBrowserRouterState && !activePendingBrowserRouterState.settled) {
			activePendingBrowserRouterState.settled = true;
			activePendingBrowserRouterState.resolve(getBrowserRouterState());
		}
		let resolvePending;
		const promise = new Promise((resolve) => {
			resolvePending = resolve;
		});
		if (!resolvePending) throw new Error("[vinext] Failed to initialize browser router promise");
		const pending = {
			promise,
			resolve: resolvePending,
			settled: false
		};
		activePendingBrowserRouterState = pending;
		setter(promise);
		return pending;
	}
	function settlePendingBrowserRouterState(pending) {
		if (!pending || pending.settled) return;
		pending.settled = true;
		pending.resolve(getBrowserRouterState());
		if (activePendingBrowserRouterState === pending) activePendingBrowserRouterState = null;
	}
	function finalizeNavigation(navId, pending) {
		settlePendingBrowserRouterState(pending);
		if (isCurrentNavigation(navId)) {
			pendingUserNavigationId = null;
			pendingUserNavigationLane = null;
			clearPendingPathname(navId);
		}
	}
	function queuePrePaintNavigationEffect(renderId, effect) {
		if (!effect) return;
		pendingNavigationPrePaintEffects.set(renderId, effect);
	}
	/**
	* Run all queued pre-paint effects for renderIds up to and including the
	* given renderId. When React supersedes a startTransition update (rapid
	* clicks on same-route links), the superseded NavigationCommitSignal never
	* mounts, so its pre-paint effect never fires. By draining all effects
	* <= the committed renderId here, the winning transition cleans up after
	* any superseded ones, keeping the counter balanced.
	*
	* Invariant: each superseded navigation gets a commitClientNavigationState()
	* to balance the activateNavigationSnapshot() from its renderNavigationPayload call.
	*/
	function drainPrePaintEffects(upToRenderId) {
		for (const [id, effect] of pendingNavigationPrePaintEffects) {
			if (id > upToRenderId) continue;
			pendingNavigationPrePaintEffects.delete(id);
			if (id === upToRenderId) effect();
			else commitClientNavigationStateImpl(void 0, { releaseSnapshot: true });
		}
	}
	/**
	* Settle all pending navigation renders through the supplied renderId. Only
	* the exact render whose layout effect ran is a successful commit; older
	* superseded renders and cleanup-only settlements resolve as no-commit.
	*/
	function settleNavigationCommits(renderId, committed) {
		for (const [pendingId, pendingCommit] of pendingNavigationCommits) {
			if (pendingId > renderId) continue;
			pendingNavigationCommits.delete(pendingId);
			const didCommit = committed && pendingId === renderId;
			if (didCommit && pendingCommit.committedState !== null) pendingCommit.onCommittedState?.(pendingCommit.committedState);
			pendingCommit.resolve(didCommit);
		}
	}
	function clearCommittedNavigationFailureTargets(renderId) {
		for (const [pendingId, targetHref] of pendingNavigationFailureTargets) {
			if (pendingId > renderId) continue;
			pendingNavigationFailureTargets.delete(pendingId);
			clearAppNavigationFailureTarget(targetHref);
		}
	}
	async function hmrReplaceTree(nextElements, navigationSnapshot) {
		const hmrUpdateId = ++latestHmrUpdateId;
		const startedDuringUserNavigation = pendingUserNavigationLane === "navigation";
		if (!hasBrowserRouterState()) return;
		const pending = await createPendingNavigationCommit({
			currentState: getBrowserRouterState(),
			nextElements,
			navigationSnapshot,
			operationLane: "hmr",
			payloadOrigin: FRESH_APP_NAVIGATION_PAYLOAD_ORIGIN,
			renderId: allocateRenderId(),
			type: "replace"
		});
		if (hmrUpdateId !== latestHmrUpdateId || startedDuringUserNavigation) return;
		if (!hasBrowserRouterState()) return;
		const approval = approveHmrVisibleCommit({
			currentState: getBrowserRouterState(),
			pending,
			routeManifest: deps.getRouteManifest?.() ?? null,
			targetHref: createSnapshotPathAndSearch(navigationSnapshot)
		});
		if (approval.approvedCommit) dispatchSynchronousVisibleCommit(approval.approvedCommit);
		else if (approval.decision.disposition === "hard-navigate") performHardNavigation(createSnapshotPathAndSearch(navigationSnapshot));
	}
	function NavigationCommitSignal({ renderId, children }) {
		(0, import_react.useInsertionEffect)(() => {
			clearCommittedNavigationFailureTargets(renderId);
		}, [renderId]);
		(0, import_react.useLayoutEffect)(() => {
			drainPrePaintEffects(renderId);
			settleNavigationCommits(renderId, true);
			return () => {
				settleNavigationCommits(renderId, false);
			};
		}, [renderId]);
		return children;
	}
	function dispatchApprovedVisibleCommit(renderId, commit, pendingRouterState, visibleCommitMode) {
		const setter = getBrowserRouterStateSetter();
		const pendingCommit = pendingNavigationCommits.get(renderId);
		const captureCandidateState = (state) => {
			if (pendingCommit) pendingCommit.committedState = state;
			return state;
		};
		if (pendingRouterState) {
			if (pendingRouterState.settled) return;
			const committedState = captureCandidateState(applyApprovedVisibleCommit(getBrowserRouterState(), commit));
			pendingRouterState.settled = true;
			pendingRouterState.resolve(committedState);
			if (activePendingBrowserRouterState === pendingRouterState) activePendingBrowserRouterState = null;
			if (visibleCommitMode === "synchronous") (0, import_react_dom.flushSync)(() => {
				setter(committedState);
			});
			return;
		}
		if (visibleCommitMode === "synchronous") {
			(0, import_react_dom.flushSync)(() => {
				setter(captureCandidateState(applyApprovedVisibleCommit(getBrowserRouterState(), commit)));
			});
			return;
		}
		(0, import_react.startTransition)(() => {
			setter(captureCandidateState(applyApprovedVisibleCommit(getBrowserRouterState(), commit)));
		});
	}
	function dispatchSynchronousVisibleCommit(commit) {
		getBrowserRouterStateSetter()(applyApprovedVisibleCommit(getBrowserRouterState(), commit));
	}
	function createRestoredHistorySnapshotCommit(options) {
		const operation = {
			id: options.renderId,
			lane: "traverse",
			startedVisibleCommitVersion: options.currentState.visibleCommitVersion,
			state: "pending"
		};
		return {
			action: {
				bfcacheIds: options.restoredState.bfcacheIds,
				elements: options.restoredState.elements,
				interception: options.restoredState.interception,
				interceptionContext: options.restoredState.interceptionContext,
				layoutFlags: options.restoredState.layoutFlags,
				layoutIds: options.restoredState.layoutIds,
				navigationSnapshot: options.restoredState.navigationSnapshot,
				operation,
				previousNextUrl: options.restoredState.previousNextUrl,
				renderId: options.renderId,
				rootLayoutTreePath: options.restoredState.rootLayoutTreePath,
				reuseCurrentBfcacheIds: false,
				routeId: options.restoredState.routeId,
				skippedLayoutIds: [],
				slotBindings: options.restoredState.slotBindings,
				type: "traverse"
			},
			interception: options.restoredState.interception,
			interceptionContext: options.restoredState.interceptionContext,
			previousNextUrl: options.restoredState.previousNextUrl,
			rootLayoutTreePath: options.restoredState.rootLayoutTreePath,
			routeId: options.restoredState.routeId,
			restoredHistorySnapshot: true,
			skippedLayoutIds: []
		};
	}
	function restoreHistorySnapshotVisibleState(options) {
		if (!isSnapshotTargetHref(basePath, options.state.navigationSnapshot, options.targetHref)) return false;
		const currentState = getBrowserRouterState();
		const pending = createRestoredHistorySnapshotCommit({
			currentState,
			renderId: allocateRenderId(),
			restoredState: options.state
		});
		const approval = approvePendingNavigationCommit({
			activeNavigationId,
			currentState,
			pending,
			routeManifest: getRouteManifest(),
			startedNavigationId: options.navId,
			targetHref: options.targetHref
		});
		if (approval.approvedCommit === null) return false;
		options.beforeCommit?.();
		dispatchSynchronousVisibleCommit(approval.approvedCommit);
		return true;
	}
	function notifyDiscardedServerActionRevalidation(lifecycleOptions) {
		if (!shouldScheduleRefreshForDiscardedServerAction(lifecycleOptions?.revalidation ?? "none")) return;
		lifecycleOptions?.onDiscardedRevalidation?.();
	}
	function isSamePathSearchHashCommit(targetHref) {
		try {
			const currentUrl = new URL(window.location.href);
			const targetUrl = new URL(targetHref, currentUrl.href);
			return targetUrl.origin === currentUrl.origin && targetUrl.pathname === currentUrl.pathname && targetUrl.search !== currentUrl.search && targetUrl.hash !== "";
		} catch {
			return false;
		}
	}
	function shouldForceSynchronousCommit(options) {
		if (options.actionType === "traverse") return false;
		if (options.historyUpdateMode === void 0) return false;
		if (options.scrollIntent?.hash == null) return false;
		return isSamePathSearchHashCommit(options.targetHref);
	}
	async function renderNavigationPayload(options) {
		if (options.navId === pendingUserNavigationId) pendingUserNavigationLane = options.operationLane;
		const renderId = allocateRenderId();
		const failureTarget = getAppNavigationFailureTarget(options.targetHref);
		if (failureTarget) pendingNavigationFailureTargets.set(renderId, failureTarget);
		let resolveCommitted;
		const committed = new Promise((resolve) => {
			resolveCommitted = resolve;
			pendingNavigationCommits.set(renderId, {
				committedState: null,
				onCommittedState: options.onCommittedState,
				resolve
			});
		});
		let snapshotActivated = false;
		try {
			const pendingOptions = {
				currentState: options.navigationInitiationState,
				navigationCommitKind: options.navigationCommitKind,
				navigationId: options.navId,
				navigationSnapshot: options.navigationSnapshot,
				operationLane: options.operationLane,
				payloadOrigin: options.payloadOrigin,
				previousNextUrl: options.previousNextUrl,
				renderId,
				restoredBfcacheIds: options.restoredBfcacheIds,
				reuseCurrentBfcacheIds: options.reuseCurrentBfcacheIds,
				type: options.actionType
			};
			const pending = options.nextElements instanceof Promise ? await createPendingNavigationCommit({
				...pendingOptions,
				nextElements: options.nextElements
			}) : createPendingNavigationCommitFromElements({
				...pendingOptions,
				nextElements: options.nextElements
			});
			const approval = approvePendingNavigationCommit({
				activeNavigationId,
				currentState: getBrowserRouterState(),
				pending,
				routeManifest: getRouteManifest(),
				startedNavigationId: options.navId,
				targetHref: options.targetHref
			});
			if (approval.decision.disposition === "no-commit") {
				settlePendingBrowserRouterState(options.pendingRouterState);
				pendingNavigationFailureTargets.delete(renderId);
				if (failureTarget) clearAppNavigationFailureTarget(failureTarget);
				pendingNavigationCommits.delete(renderId);
				resolveCommitted?.(false);
				consumeAppRouterScrollIntent(options.scrollIntent ?? null);
				return "no-commit";
			}
			if (approval.decision.disposition === "hard-navigate") {
				settlePendingBrowserRouterState(options.pendingRouterState);
				pendingNavigationFailureTargets.delete(renderId);
				pendingNavigationCommits.delete(renderId);
				consumeAppRouterScrollIntent(options.scrollIntent ?? null);
				if (performHardNavigation(options.targetHref)) return "hard-navigate";
				if (failureTarget) clearAppNavigationFailureTarget(failureTarget);
				return "no-commit";
			}
			const approvedCommit = approval.approvedCommit;
			if (approvedCommit === null) throw new Error("[vinext] Commit decision did not approve a visible commit");
			queuePrePaintNavigationEffect(renderId, options.createNavigationCommitEffect({
				bfcacheIds: approvedCommit.action.bfcacheIds,
				href: options.targetHref,
				historyUpdateMode: options.historyUpdateMode,
				navId: options.navId,
				params: options.params,
				previousNextUrl: approvedCommit.previousNextUrl,
				targetHistoryIndex: options.targetHistoryIndex
			}));
			claimAppRouterScrollIntentForCommit(options.scrollIntent, renderId);
			activateNavigationSnapshot();
			snapshotActivated = true;
			dispatchApprovedVisibleCommit(renderId, approvedCommit, options.pendingRouterState, shouldForceSynchronousCommit(options) ? "synchronous" : options.visibleCommitMode ?? "transition");
		} catch (error) {
			pendingNavigationFailureTargets.delete(renderId);
			pendingNavigationPrePaintEffects.delete(renderId);
			pendingNavigationCommits.delete(renderId);
			if (snapshotActivated) commitClientNavigationStateImpl(options.navId);
			settlePendingBrowserRouterState(options.pendingRouterState);
			resolveCommitted?.(false);
			throw error;
		}
		return committed.then((didCommit) => didCommit ? "committed" : "no-commit");
	}
	async function commitSameUrlNavigatePayload(nextElements, navigationSnapshot, returnValue, actionInitiationState, lifecycleOptions) {
		const currentState = actionInitiationState ?? getBrowserRouterState();
		const startedNavigationId = lifecycleOptions?.startedNavigationId ?? activeNavigationId;
		const targetHref = lifecycleOptions?.targetHref ?? window.location.href;
		const { approvedCommit, decision, pending, trace: _navigationTrace } = await resolveAndClassifyNavigationCommit({
			activeNavigationId,
			currentState,
			getActiveNavigationId: () => activeNavigationId,
			getCurrentStateForApproval: getBrowserRouterState,
			navigationSnapshot,
			nextElements,
			renderId: allocateRenderId(),
			operationLane: resolveServerActionOperationLane(lifecycleOptions?.revalidation ?? "none"),
			payloadOrigin: FRESH_APP_NAVIGATION_PAYLOAD_ORIGIN,
			startedNavigationId,
			routeManifest: getRouteManifest(),
			targetHref,
			type: "navigate"
		});
		if (decision.disposition === "hard-navigate") {
			performHardNavigation(targetHref);
			return;
		}
		if (approvedCommit) {
			const latestApproval = approvePendingNavigationCommit({
				activeNavigationId,
				currentState: getBrowserRouterState(),
				pending,
				routeManifest: getRouteManifest(),
				startedNavigationId,
				targetHref
			});
			if (latestApproval.decision.disposition === "hard-navigate") {
				performHardNavigation(targetHref);
				return;
			}
			if (latestApproval.approvedCommit) {
				const approvedRevalidationCommit = latestApproval.approvedCommit;
				(0, import_react.startTransition)(() => {
					dispatchSynchronousVisibleCommit(approvedRevalidationCommit);
				});
				syncHistoryStatePreviousNextUrl(approvedRevalidationCommit.previousNextUrl, approvedRevalidationCommit.action.bfcacheIds);
			} else notifyDiscardedServerActionRevalidation(lifecycleOptions);
		} else if (decision.disposition === "no-commit") notifyDiscardedServerActionRevalidation(lifecycleOptions);
		if (returnValue) {
			if (!returnValue.ok) throw returnValue.data;
			return returnValue.data;
		}
	}
	function attachBrowserRouterState(setter, stateRef) {
		setBrowserRouterState = setter;
		browserRouterStateRef = stateRef;
		markBrowserRouterStateReady();
		return () => {
			if (setBrowserRouterState === setter) setBrowserRouterState = null;
			if (browserRouterStateRef === stateRef) {
				browserRouterStateRef = null;
				browserRouterStateHasCommitted = false;
			}
		};
	}
	return {
		beginNavigation,
		getActiveNavigationId,
		hasBrowserRouterState,
		getBrowserRouterState,
		isCurrentNavigation,
		performHardNavigation,
		waitForBrowserRouterStateReady,
		attachBrowserRouterState,
		beginPendingBrowserRouterState,
		finalizeNavigation,
		restoreHistorySnapshotVisibleState,
		renderNavigationPayload,
		commitSameUrlNavigatePayload,
		hmrReplaceTree,
		drainPrePaintEffects,
		clearCommittedNavigationFailureTargets,
		NavigationCommitSignal
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-browser-hydration.js
var RSC_FORM_STATE_GLOBAL = "__VINEXT_RSC_FORM_STATE__";
function consumeInitialFormState(global) {
	const formState = global["__VINEXT_RSC_FORM_STATE__"] ?? null;
	delete global[RSC_FORM_STATE_GLOBAL];
	return formState;
}
function createVinextHydrateRootOptions(options) {
	const hydrateOptions = {
		formState: options.formState,
		...options.onRecoverableError ? { onRecoverableError: options.onRecoverableError } : {},
		onUncaughtError: options.onUncaughtError
	};
	if (options.onCaughtError) return {
		...hydrateOptions,
		onCaughtError: options.onCaughtError
	};
	return hydrateOptions;
}
function hydrateRootInTransition(options) {
	let root;
	options.startTransition(() => {
		root = options.hydrateRoot(options.container, options.children, options.options);
	});
	if (root === void 0) throw new Error("[vinext] React.startTransition did not synchronously start hydration");
	return root;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-browser-history-controller.js
function createCanonicalBrowserHistoryHref(href) {
	const url = new URL(href);
	return `${url.pathname}${url.search}${url.hash}`;
}
function stripVinextScrollState(state) {
	if (!state || typeof state !== "object") return state;
	const nextState = {};
	for (const [key, value] of Object.entries(state)) {
		if (key === "__vinext_scrollX" || key === "__vinext_scrollY") continue;
		nextState[key] = value;
	}
	return Object.keys(nextState).length > 0 ? nextState : null;
}
/**
* Owns App Router browser-history metadata and traversal bookkeeping behind a
* typed seam: traversal index allocation/commit, push/replace/traverse/hash-only
* history-state writes, BFCache epoch/snapshot invalidation through
* `RestorableClientStateController`, and restorable-snapshot candidate
* resolution.
*
* Ownership boundary: this is not a second router or visible-state authority. It
* resolves history facts and delegates visible restoration through an injected
* approved-commit callback. It never sets router state directly, never imports
* `applyApprovedVisibleCommit()`, and never bypasses the `ApprovedVisibleCommit`
* boundary owned by `AppBrowserNavigationController`.
*/
var AppBrowserHistoryController = class {
	#restorableClientState;
	#readHistoryState;
	#readCurrentHref;
	#pushHistoryState;
	#replaceHistoryState;
	#readVisibleNavigationMetadata;
	#currentHistoryTraversalIndex;
	#nextHistoryTraversalIndex;
	constructor(deps) {
		this.#readHistoryState = deps.readHistoryState;
		this.#readCurrentHref = deps.readCurrentHref;
		this.#pushHistoryState = deps.pushHistoryState;
		this.#replaceHistoryState = deps.replaceHistoryState;
		this.#readVisibleNavigationMetadata = deps.readVisibleNavigationMetadata;
		this.#restorableClientState = new RestorableClientStateController({
			initialHistoryState: deps.initialHistoryState,
			maxHistoryStateSnapshots: deps.maxHistoryStateSnapshots
		});
		this.#currentHistoryTraversalIndex = readHistoryStateTraversalIndex(deps.initialHistoryState) ?? 0;
		this.#nextHistoryTraversalIndex = this.#currentHistoryTraversalIndex;
	}
	get currentHistoryTraversalIndex() {
		return this.#currentHistoryTraversalIndex;
	}
	allocateNavigationHistoryTraversalIndex(historyUpdateMode) {
		switch (historyUpdateMode) {
			case "push": return this.#nextHistoryTraversalIndex + 1;
			case "replace": return this.#currentHistoryTraversalIndex;
			case void 0: return null;
			default: throw new Error("[vinext] Unknown history update mode: " + String(historyUpdateMode));
		}
	}
	commitHistoryTraversalIndex(index) {
		this.#currentHistoryTraversalIndex = index;
		if (index !== null) this.#nextHistoryTraversalIndex = Math.max(this.#nextHistoryTraversalIndex, index);
	}
	commitTraversalIndexFromHistoryState(historyState) {
		this.commitHistoryTraversalIndex(readHistoryStateTraversalIndex(historyState));
	}
	resolveTraversalIntent(historyState) {
		return resolveHistoryTraversalIntent({
			currentHistoryIndex: this.#currentHistoryTraversalIndex,
			historyState
		});
	}
	readCurrentBfcacheVersionHistoryIds(historyState) {
		return this.#restorableClientState.readCurrentBfcacheVersionHistoryIds(historyState);
	}
	isCacheInvalidationGuarded() {
		return this.#restorableClientState.isCacheInvalidationGuarded();
	}
	isCurrentBfcacheVersion(historyState) {
		return this.#restorableClientState.isCurrentBfcacheVersion(historyState);
	}
	beginCacheInvalidationGuard() {
		return this.#restorableClientState.beginCacheInvalidationGuard();
	}
	invalidateRestorableClientState() {
		this.#restorableClientState.invalidateClientState();
	}
	rememberHistoryStateSnapshot(state) {
		this.#restorableClientState.rememberHistoryStateSnapshot({
			historyIndex: this.#currentHistoryTraversalIndex,
			state
		});
	}
	commitHashOnlyNavigation(href, historyUpdateMode, scroll) {
		const navigationHistoryIndex = this.allocateNavigationHistoryTraversalIndex(historyUpdateMode);
		const historyState = this.#readHistoryState();
		const visible = this.#readVisibleNavigationMetadata();
		const previousNextUrl = visible ? visible.previousNextUrl : readHistoryStatePreviousNextUrl(historyState);
		const bfcacheIds = visible ? visible.bfcacheIds : this.#restorableClientState.readCurrentBfcacheVersionHistoryIds(historyState);
		const nextHistoryState = createHistoryStateWithNavigationMetadata(this.#createHashOnlyNavigationBaseHistoryState(historyUpdateMode, scroll), {
			bfcacheIds,
			bfcacheVersion: bfcacheIds === null ? void 0 : this.#restorableClientState.currentBfcacheVersion,
			previousNextUrl,
			traversalIndex: navigationHistoryIndex
		});
		if (historyUpdateMode === "replace") this.#replaceHistoryState(nextHistoryState, href);
		else this.#pushHistoryState(nextHistoryState, href);
		this.commitHistoryTraversalIndex(navigationHistoryIndex);
	}
	#createHashOnlyNavigationBaseHistoryState(historyUpdateMode, scroll) {
		if (historyUpdateMode !== "replace") return null;
		const historyState = this.#readHistoryState();
		return scroll ? stripVinextScrollState(historyState) : historyState;
	}
	/**
	* Writes the history entry for an approved push/replace/traverse commit and
	* advances the traversal index. `stageClientParams` runs at the exact point it
	* ran inline in the browser-entry commit effect so client-param staging stays
	* ordered relative to the history write. Mirrors Next.js committing tree state
	* into the history entry during the navigation commit.
	*/
	commitNavigationHistory(options) {
		const currentHref = this.#readCurrentHref();
		const origin = new URL(currentHref).origin;
		const targetHref = new URL(options.href, origin).href;
		const preserveExistingState = options.historyUpdateMode === "replace";
		const navigationHistoryIndex = options.targetHistoryIndex !== void 0 ? options.targetHistoryIndex : this.allocateNavigationHistoryTraversalIndex(options.historyUpdateMode);
		const historyState = createHistoryStateWithNavigationMetadata(preserveExistingState ? this.#readHistoryState() : null, {
			bfcacheIds: options.bfcacheIds,
			bfcacheVersion: this.#restorableClientState.currentBfcacheVersion,
			previousNextUrl: options.previousNextUrl,
			traversalIndex: navigationHistoryIndex
		});
		let wroteHistoryState = false;
		if (options.historyUpdateMode === "replace" && currentHref !== targetHref) {
			options.stageClientParams();
			this.#replaceHistoryState(historyState, options.href);
			wroteHistoryState = true;
			this.commitHistoryTraversalIndex(navigationHistoryIndex);
		} else if (options.historyUpdateMode === "push" && currentHref !== targetHref) {
			options.stageClientParams();
			this.#pushHistoryState(historyState, options.href);
			wroteHistoryState = true;
			this.commitHistoryTraversalIndex(navigationHistoryIndex);
		}
		if (!wroteHistoryState) {
			this.syncCurrentHistoryStatePreviousNextUrl(options.previousNextUrl, options.bfcacheIds);
			options.stageClientParams();
			if (options.targetHistoryIndex !== void 0) this.commitHistoryTraversalIndex(options.targetHistoryIndex);
		}
	}
	syncCurrentHistoryStatePreviousNextUrl(previousNextUrl, bfcacheIds) {
		if (this.#isHistoryStateNavigationMetadataInSync(this.#readHistoryState(), previousNextUrl, bfcacheIds)) return;
		const nextHistoryState = createHistoryStateWithNavigationMetadata(this.#readHistoryState(), {
			bfcacheIds,
			bfcacheVersion: bfcacheIds === void 0 ? void 0 : this.#restorableClientState.currentBfcacheVersion,
			previousNextUrl
		});
		this.#replaceHistoryState(nextHistoryState);
		if (this.#isHistoryStateNavigationMetadataInSync(this.#readHistoryState(), previousNextUrl, bfcacheIds)) return;
		this.#replaceHistoryState(nextHistoryState);
	}
	#isHistoryStateNavigationMetadataInSync(state, previousNextUrl, bfcacheIds) {
		return readHistoryStatePreviousNextUrl(state) === previousNextUrl && (bfcacheIds === void 0 || areBfcacheIdMapsEqual(readHistoryStateBfcacheIds(state), bfcacheIds) && this.#restorableClientState.isCurrentBfcacheVersion(state));
	}
	/** Initial history write performed before hydration starts. */
	writeBootstrapHistoryMetadata() {
		this.#replaceHistoryState(createHistoryStateWithNavigationMetadata(this.#readHistoryState(), {
			previousNextUrl: null,
			traversalIndex: this.#currentHistoryTraversalIndex
		}), createCanonicalBrowserHistoryHref(this.#readCurrentHref()));
	}
	/** History write performed on the first committed (hydrated) render. */
	writeHydratedHistoryMetadata(options) {
		this.#replaceHistoryState(createHistoryStateWithNavigationMetadata(this.#readHistoryState(), {
			bfcacheIds: options.bfcacheIds,
			bfcacheVersion: this.#restorableClientState.currentBfcacheVersion,
			previousNextUrl: options.previousNextUrl,
			traversalIndex: this.#currentHistoryTraversalIndex
		}));
	}
	/**
	* Resolves a restorable snapshot candidate for the given history entry and
	* commits the traversal index after, and only after, the injected
	* approved-visible-restore callback succeeds. The traversal-index commit and
	* client-param staging run inside `beforeCommit`, which the
	* `AppBrowserNavigationController` invokes only once the `ApprovedVisibleCommit`
	* is approved. Returns false when no snapshot is restorable or the restore is
	* not approved.
	*/
	restoreHistorySnapshot(options) {
		const decision = this.#restorableClientState.resolveHistoryStateSnapshotRestore(options.historyState);
		if (decision.kind === "skip") return false;
		return options.approveVisibleRestore({
			state: decision.state,
			beforeCommit: () => {
				this.commitHistoryTraversalIndex(decision.targetHistoryIndex);
				options.stageClientParams(decision.state.navigationSnapshot.params);
			}
		});
	}
};
function areBfcacheIdMapsEqual(a, b) {
	if (a === b) return true;
	if (a === null || b === null) return false;
	const aEntries = Object.entries(a);
	const bEntries = Object.entries(b);
	if (aEntries.length !== bEntries.length) return false;
	return aEntries.every(([key, value]) => b[key] === value);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-visited-response-cache.js
var MAX_TRAVERSAL_CACHE_TTL = 30 * 6e4;
function createVisitedResponseCacheEntry(options) {
	return {
		createdAt: options.now,
		...options.elements ? { elements: options.elements } : {},
		expiresAt: resolveCachedRscResponseExpiresAt(options.now, options.response, options.fallbackTtlMs ?? 3e5),
		mountedSlotsHeader: options.mountedSlotsHeader ?? null,
		params: options.params,
		response: options.response
	};
}
function isVisitedResponseCacheEntryFresh(entry, options) {
	if (options.navigationKind === "refresh") return false;
	if (options.navigationKind === "traverse") return options.now - entry.createdAt < MAX_TRAVERSAL_CACHE_TTL;
	return entry.expiresAt > options.now;
}
function normalizeVisitedResponseCacheLookupUrl(rscUrl) {
	try {
		const url = new URL(rscUrl, "http://vinext.local");
		stripRscCacheBustingSearchParam(url);
		return `${url.pathname}${url.search}`;
	} catch {
		return null;
	}
}
function parseVisitedResponseCacheKey(cacheKey) {
	const separatorIndex = cacheKey.indexOf("\0");
	if (separatorIndex === -1) return {
		interceptionContext: null,
		rscUrl: cacheKey
	};
	return {
		interceptionContext: cacheKey.slice(separatorIndex + 1),
		rscUrl: cacheKey.slice(0, separatorIndex)
	};
}
function findVisitedResponseCacheEntry(cache, rscUrl, interceptionContext) {
	const exactCacheKey = AppElementsWire.encodeCacheKey(rscUrl, interceptionContext);
	const exactEntry = cache.get(exactCacheKey);
	if (exactEntry) return {
		cacheKey: exactCacheKey,
		entry: exactEntry
	};
	const normalizedTarget = normalizeVisitedResponseCacheLookupUrl(rscUrl);
	if (normalizedTarget === null) return null;
	for (const [cacheKey, entry] of cache) {
		const source = parseVisitedResponseCacheKey(cacheKey);
		if (source.interceptionContext !== interceptionContext) continue;
		if (normalizeVisitedResponseCacheLookupUrl(source.rscUrl) !== normalizedTarget) continue;
		return {
			cacheKey,
			entry
		};
	}
	return null;
}
function deleteVisitedResponseCacheEntry(cache, rscUrl, interceptionContext) {
	const match = findVisitedResponseCacheEntry(cache, rscUrl, interceptionContext);
	if (!match) return false;
	return cache.delete(match.cacheKey);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-browser-popstate.js
function hasSavedScrollPosition(state) {
	return Boolean(state && typeof state === "object" && "__vinext_scrollY" in state);
}
function restoreSynchronousPopstateScrollPosition(deps, state) {
	const navId = deps.getActiveNavigationId();
	deps.markScrollRestoreConsumed(navId);
	deps.restorePopstateScrollPosition(state, { shouldContinue: () => deps.isCurrentNavigation(navId) });
}
function scheduleAfterFrame(callback) {
	if (typeof window.requestAnimationFrame === "function") {
		window.requestAnimationFrame(callback);
		return;
	}
	queueMicrotask(callback);
}
function createPopstateTraversalIntent(historyState) {
	return {
		direction: "unknown",
		historyState,
		targetHistoryIndex: readHistoryStateTraversalIndex(historyState)
	};
}
function createPopstateRestoreHandler(deps) {
	return (event) => {
		deps.notifyAppRouterTransitionStart(window.location.href);
		const pendingNavigation = deps.getNavigate()?.(window.location.href, 0, "traverse", void 0, void 0, false, createPopstateTraversalIntent(event.state)) ?? Promise.resolve();
		const popstateNavId = deps.getActiveNavigationId();
		deps.setPendingNavigation(pendingNavigation);
		const shouldRestoreSavedScroll = hasSavedScrollPosition(event.state);
		const shouldRestoreScrollForNavigation = () => deps.isCurrentNavigation(popstateNavId) && !deps.shouldSkipScrollRestore(popstateNavId);
		if (shouldRestoreSavedScroll) scheduleAfterFrame(() => {
			if (shouldRestoreScrollForNavigation()) deps.restorePopstateScrollPosition(event.state, { shouldContinue: shouldRestoreScrollForNavigation });
		});
		pendingNavigation.finally(() => {
			if (shouldRestoreScrollForNavigation() && !shouldRestoreSavedScroll) deps.restorePopstateScrollPosition(event.state);
			if (deps.getPendingNavigation() === pendingNavigation) deps.setPendingNavigation(null);
		});
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-browser-error.js
function isImplicitRootErrorBoundary(errorInfo) {
	if (!isUnknownRecord(errorInfo.errorBoundary)) return false;
	const props = errorInfo.errorBoundary.props;
	return isUnknownRecord(props) && props.isImplicitRootErrorBoundary === true;
}
function logCaughtError(error, errorInfo) {
	console.error(error);
	if (errorInfo?.componentStack) console.error("The above error occurred in a React component:\n" + errorInfo.componentStack);
}
function reportGlobalError(error) {
	if (typeof globalThis.reportError === "function") {
		globalThis.reportError(error);
		return;
	}
	console.error(error);
}
function createOnUncaughtError() {
	return (error) => {
		reportGlobalError(error);
	};
}
function createProdOnCaughtError(onImplicitRootError) {
	return (error, errorInfo) => {
		if (isNavigationSignalError(error)) return;
		if (isImplicitRootErrorBoundary(errorInfo)) {
			onImplicitRootError(error, errorInfo);
			return;
		}
		logCaughtError(error, errorInfo);
	};
}
function prodOnRecoverableError(error) {
	reportGlobalError(error instanceof Error && error.cause !== void 0 ? error.cause : error);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-hydration-cache-publication.js
function createHydrationCachePublication() {
	let state = "pending";
	let pendingPublication = null;
	let invalidatePublishedCandidate = null;
	const publishPendingCandidate = () => {
		if (state !== "committed" && state !== "complete" || pendingPublication === null) return;
		const publishCandidate = pendingPublication;
		pendingPublication = null;
		invalidatePublishedCandidate = publishCandidate();
	};
	return {
		commit() {
			if (state !== "pending") return;
			state = "committed";
			publishPendingCandidate();
		},
		complete() {
			if (state === "committed") state = "complete";
		},
		fail() {
			if (state === "complete" || state === "invalidated") return;
			state = "invalidated";
			pendingPublication = null;
			invalidatePublishedCandidate?.();
			invalidatePublishedCandidate = null;
		},
		invalidate() {
			if (state === "invalidated") return;
			state = "invalidated";
			pendingPublication = null;
			invalidatePublishedCandidate?.();
			invalidatePublishedCandidate = null;
		},
		publish(publishCandidate) {
			if (state === "invalidated") return;
			pendingPublication = publishCandidate;
			publishPendingCandidate();
		}
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-browser-prefetch-response.js
function peekSettledPrefetchResponseForNavigation(options) {
	if (options.navigationKind !== "navigate" || options.bypassNavigationCache) return null;
	return (options.peek ?? peekPrefetchResponseForNavigation)(options.targetPathAndSearch, options.interceptionContext, options.mountedSlotsHeader, { additionalRscUrls: options.additionalRscUrls });
}
function normalizeBrowserRscUrlForReuse(url, origin) {
	if (!url) return null;
	try {
		const parsed = new URL(url, origin);
		stripRscCacheBustingSearchParam(parsed);
		return `${parsed.pathname}${parsed.search}`;
	} catch {
		return null;
	}
}
function isSameOriginBrowserRscUrl(url, origin) {
	try {
		return new URL(url, origin).origin === new URL(origin).origin;
	} catch {
		return false;
	}
}
function canonicalizeBrowserRscResponseUrl(responseUrl, origin) {
	try {
		const parsed = new URL(responseUrl, origin);
		if (parsed.origin === new URL(origin).origin) return `${parsed.pathname}${parsed.search}`;
	} catch {}
	return responseUrl;
}
function resolvePrefetchNavigationResponseUrl(options) {
	const normalizedResponseUrl = normalizeBrowserRscUrlForReuse(options.responseUrl, options.origin);
	return normalizedResponseUrl !== null && isSameOriginBrowserRscUrl(options.responseUrl, options.origin) && options.additionalRscUrls.some((additionalRscUrl) => normalizeBrowserRscUrlForReuse(additionalRscUrl, options.origin) === normalizedResponseUrl) ? options.visibleRscUrl : canonicalizeBrowserRscResponseUrl(options.responseUrl, options.origin);
}
function prepareConsumedPrefetchResponseForPublication(response, responseUrl) {
	const { expiresAt, preparedElements, ...snapshot } = response;
	return {
		expiresAt,
		preparedElements,
		snapshot: {
			...snapshot,
			url: responseUrl
		}
	};
}
function preserveCommittedPrefetchExpiry(snapshot, expiresAt) {
	return expiresAt === void 0 ? snapshot : {
		...snapshot,
		expiresAt
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-optimistic-routing.js
var routeTrieCache = /* @__PURE__ */ new WeakMap();
var OPTIMISTIC_ROUTE_SEGMENT_SUSPENSE_TRIGGER = new Promise(() => {});
function getOptimisticRouteTemplateKey(options) {
	return `${options.routeId}\0${options.interceptionContext ?? ""}\0${options.mountedSlotsHeader ?? ""}`;
}
function getOptimisticPrefetchSourceKey(options) {
	return `${options.cacheKey}\0${options.interceptionContext ?? ""}\0${options.mountedSlotsHeader ?? ""}`;
}
function createNode() {
	return {
		catchAllChild: null,
		dynamicChild: null,
		optionalCatchAllChild: null,
		route: null,
		staticChildren: /* @__PURE__ */ new Map()
	};
}
function buildRouteTrie(routeManifest) {
	const root = createNode();
	for (const route of routeManifest.segmentGraph.routes.values()) {
		let node = root;
		const parts = route.patternParts;
		if (parts.length === 0) {
			node.route ??= route;
			continue;
		}
		for (const [index, part] of parts.entries()) {
			const isTerminal = index === parts.length - 1;
			if (part.startsWith(":") && part.endsWith("+")) {
				if (isTerminal && node.catchAllChild === null) node.catchAllChild = {
					paramName: part.slice(1, -1),
					route
				};
				break;
			}
			if (part.startsWith(":") && part.endsWith("*")) {
				if (isTerminal && node.optionalCatchAllChild === null) node.optionalCatchAllChild = {
					paramName: part.slice(1, -1),
					route
				};
				break;
			}
			if (part.startsWith(":")) {
				const paramName = part.slice(1);
				if (node.dynamicChild === null) node.dynamicChild = {
					node: createNode(),
					paramName
				};
				else if (node.dynamicChild.paramName !== paramName && false);
				node = node.dynamicChild.node;
				if (isTerminal) node.route ??= route;
				continue;
			}
			let staticChild = node.staticChildren.get(part);
			if (staticChild === void 0) {
				staticChild = createNode();
				node.staticChildren.set(part, staticChild);
			}
			node = staticChild;
			if (isTerminal) node.route ??= route;
		}
	}
	return root;
}
function getRouteTrie(routeManifest) {
	const existing = routeTrieCache.get(routeManifest);
	if (existing) return existing;
	const trie = buildRouteTrie(routeManifest);
	routeTrieCache.set(routeManifest, trie);
	return trie;
}
function matchNode(node, urlParts, index, entries) {
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
	if (staticChild !== void 0) return matchNode(staticChild, urlParts, index + 1, entries);
	if (node.dynamicChild !== null) {
		entries.push([node.dynamicChild.paramName, segment]);
		const match = matchNode(node.dynamicChild.node, urlParts, index + 1, entries);
		if (match !== null) return match;
		entries.pop();
	}
	if (node.catchAllChild !== null) {
		const params = buildParams(entries);
		params[node.catchAllChild.paramName] = urlParts.slice(index);
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
function hrefToRouteParts(href, basePath) {
	let url;
	try {
		url = new URL(href, "https://vinext.local");
	} catch {
		return null;
	}
	stripRscCacheBustingSearchParam(url);
	const appPathname = stripBasePath(stripRscSuffix(url.pathname), basePath);
	return splitPathnameForRouteMatch(appPathname === "" ? "/" : appPathname);
}
function matchOptimisticRouteManifestRoute(options) {
	const urlParts = hrefToRouteParts(options.href, options.basePath);
	if (urlParts === null) return null;
	const match = matchNode(getRouteTrie(options.routeManifest), urlParts, 0, []);
	if (match === null) return null;
	decodeMatchedParams(match.params);
	return match;
}
function mergeParams(target, source) {
	for (const [key, value] of Object.entries(source)) target[key] = value;
}
function resolveOptimisticNavigationParams(options) {
	const navigationParams = { ...options.match.params };
	for (const binding of options.routeManifest.segmentGraph.slotBindings.values()) {
		if (binding.routeId !== options.match.route.id || binding.state !== "active") continue;
		const patternParts = binding.slotPatternParts;
		if (!patternParts) continue;
		const matched = matchRoutePattern(options.urlParts, patternParts);
		if (matched) mergeParams(navigationParams, matched);
	}
	return navigationParams;
}
function elementHasSuspenseFallback(value, depth = 0) {
	if (depth > 100) return false;
	if (Array.isArray(value)) return value.some((entry) => elementHasSuspenseFallback(entry, depth + 1));
	if (!(0, import_react.isValidElement)(value)) return false;
	const props = Reflect.get(value, "props");
	if (value.type === import_react.Suspense && isUnknownRecord(props)) {
		const fallback = Reflect.get(props, "fallback");
		if (fallback !== null && fallback !== void 0) return true;
	}
	if (!isUnknownRecord(props)) return false;
	return elementHasSuspenseFallback(Reflect.get(props, "children"), depth + 1);
}
function getPageElementIds(elements, route) {
	const pageElementIds = /* @__PURE__ */ new Set();
	if (route.pageId && Object.hasOwn(elements, route.pageId)) pageElementIds.add(route.pageId);
	for (const slotId of route.slotIds) {
		const parsed = AppElementsWire.parseElementKey(slotId);
		if (parsed?.kind === "slot" && parsed.name === "children" && Object.hasOwn(elements, slotId)) pageElementIds.add(slotId);
	}
	for (const key of Object.keys(elements)) if (AppElementsWire.parseElementKey(key)?.kind === "page") pageElementIds.add(key);
	return Array.from(pageElementIds).sort();
}
function OptimisticRouteSegment() {
	throw OPTIMISTIC_ROUTE_SEGMENT_SUSPENSE_TRIGGER;
}
function createOptimisticRouteTemplate(options) {
	const match = matchOptimisticRouteManifestRoute({
		basePath: options.basePath,
		href: options.href,
		routeManifest: options.routeManifest
	});
	if (match === null || !options.allowLoadingShell && !match.route.isDynamic) return null;
	if (options.interceptionContext !== null) return null;
	const metadata = AppElementsWire.readMetadata(options.elements);
	if (metadata.interception !== null || metadata.interceptionContext !== null) return null;
	const routeElement = options.elements[metadata.routeId];
	if (!options.allowLoadingShell && !elementHasSuspenseFallback(routeElement)) return null;
	if (options.allowLoadingShell && options.elements["__prefetchLoadingShell"] !== "LoadingBoundary") return null;
	if (options.allowLoadingShell && (routeElement === void 0 || routeElement === null)) return null;
	const pageElementIds = getPageElementIds(options.elements, match.route);
	if (pageElementIds.length === 0) return null;
	return {
		elements: options.elements,
		mountedSlotsHeader: options.mountedSlotsHeader,
		pageElementIds,
		routeId: match.route.id
	};
}
function createOptimisticRouteElements(template) {
	const elements = { ...template.elements };
	for (const pageElementId of template.pageElementIds) elements[pageElementId] = (0, import_react.createElement)(OptimisticRouteSegment);
	return elements;
}
function resolveOptimisticNavigationPayload(options) {
	if (options.interceptionContext !== null) return null;
	const urlParts = hrefToRouteParts(options.href, options.basePath);
	if (urlParts === null) return null;
	const match = matchOptimisticRouteManifestRoute({
		basePath: options.basePath,
		href: options.href,
		routeManifest: options.routeManifest
	});
	if (match === null) return null;
	const template = options.templates.get(getOptimisticRouteTemplateKey({
		interceptionContext: options.interceptionContext,
		mountedSlotsHeader: options.mountedSlotsHeader,
		routeId: match.route.id
	}));
	if (template === void 0) return null;
	if (template.mountedSlotsHeader !== options.mountedSlotsHeader) return null;
	return {
		elements: createOptimisticRouteElements(template),
		params: resolveOptimisticNavigationParams({
			match,
			routeManifest: options.routeManifest,
			urlParts
		}),
		template
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/html.js
var HTML_SPACE_RE = /[\t\n\f\r ]+/;
function htmlTokenListContains(value, token) {
	if (value === null) return false;
	return value.split(HTML_SPACE_RE).some((part) => part.length > 0 && part.toLowerCase() === token.toLowerCase());
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-inline-css-client.js
function inlineStyleCoversStylesheetHref(styleHref, linkHref) {
	for (const candidate of styleHref.split(/\s+/)) {
		if (candidate === linkHref) return true;
		try {
			const candidateUrl = new URL(candidate, window.location.href);
			const linkUrl = new URL(linkHref, window.location.href);
			if (candidateUrl.href === linkUrl.href) return true;
		} catch {}
	}
	return false;
}
function isInlineCssStylesheetLinkElement(link) {
	return htmlTokenListContains(link.getAttribute("rel"), "stylesheet") && link.hasAttribute("href") && (link.hasAttribute("data-precedence") || link.hasAttribute("precedence"));
}
function removeStylesheetLinksCoveredByInlineCss() {
	const inlineStyles = document.head.querySelectorAll("style[data-vinext-inline-css][data-href]");
	if (inlineStyles.length === 0) return;
	const links = document.head.querySelectorAll("link[rel][href]");
	for (const link of links) {
		if (!isInlineCssStylesheetLinkElement(link)) continue;
		const href = link.getAttribute("href");
		if (!href) continue;
		for (const style of inlineStyles) {
			const styleHref = style.getAttribute("data-href");
			if (styleHref && inlineStyleCoversStylesheetHref(styleHref, href)) {
				link.remove();
				break;
			}
		}
	}
}
//#endregion
//#region ../../../node_modules/.pnpm/@vitejs+plugin-rsc@0.5.26_r_d7be5b5d64a64a218ac22ba955ebe0d2/node_modules/@vitejs/plugin-rsc/dist/dist-rz-Bnebz.js
var import_client = require_client();
function safeFunctionCast(f) {
	return f;
}
function memoize(f, options) {
	const keyFn = options?.keyFn ?? ((...args) => args[0]);
	const cache = options?.cache ?? /* @__PURE__ */ new Map();
	return safeFunctionCast(function(...args) {
		const key = keyFn(...args);
		const value = cache.get(key);
		if (typeof value !== "undefined") return value;
		const newValue = f.apply(this, args);
		cache.set(key, newValue);
		return newValue;
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/@vitejs+plugin-rsc@0.5.26_r_d7be5b5d64a64a218ac22ba955ebe0d2/node_modules/@vitejs/plugin-rsc/dist/shared-BViDMJTQ.js
function removeReferenceCacheTag(id) {
	return id.split("$$cache=")[0];
}
function setInternalRequire() {
	globalThis.__vite_rsc_require__ = (id) => {
		if (id.startsWith("$$server:")) {
			id = id.slice(9);
			return globalThis.__vite_rsc_server_require__(id);
		}
		return globalThis.__vite_rsc_client_require__(id);
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/@vitejs+plugin-rsc@0.5.26_r_d7be5b5d64a64a218ac22ba955ebe0d2/node_modules/@vitejs/plugin-rsc/dist/core/browser.js
var init = false;
function setRequireModule(options) {
	if (init) return;
	init = true;
	const requireModule = memoize((id) => {
		return options.load(removeReferenceCacheTag(id));
	});
	globalThis.__vite_rsc_client_require__ = requireModule;
	setInternalRequire();
}
//#endregion
//#region ../../../node_modules/.pnpm/react-server-dom-webpack@19_30d794e78d18a882de9dd6dc6e476909/node_modules/react-server-dom-webpack/cjs/react-server-dom-webpack-client.browser.production.js
/**
* @license React
* react-server-dom-webpack-client.browser.production.js
*
* Copyright (c) Meta Platforms, Inc. and affiliates.
*
* This source code is licensed under the MIT license found in the
* LICENSE file in the root directory of this source tree.
*/
var require_react_server_dom_webpack_client_browser_production = /* @__PURE__ */ __commonJSMin(((exports) => {
	var ReactDOM = require_react_dom(), decoderOptions = { stream: !0 }, hasOwnProperty = Object.prototype.hasOwnProperty;
	function resolveClientReference(bundlerConfig, metadata) {
		if (bundlerConfig) {
			var moduleExports = bundlerConfig[metadata[0]];
			if (bundlerConfig = moduleExports && moduleExports[metadata[2]]) moduleExports = bundlerConfig.name;
			else {
				bundlerConfig = moduleExports && moduleExports["*"];
				if (!bundlerConfig) throw Error("Could not find the module \"" + metadata[0] + "\" in the React Server Consumer Manifest. This is probably a bug in the React Server Components bundler.");
				moduleExports = metadata[2];
			}
			return 4 === metadata.length ? [
				bundlerConfig.id,
				bundlerConfig.chunks,
				moduleExports,
				1
			] : [
				bundlerConfig.id,
				bundlerConfig.chunks,
				moduleExports
			];
		}
		return metadata;
	}
	function resolveServerReference(bundlerConfig, id) {
		var name = "", resolvedModuleData = bundlerConfig[id];
		if (resolvedModuleData) name = resolvedModuleData.name;
		else {
			var idx = id.lastIndexOf("#");
			-1 !== idx && (name = id.slice(idx + 1), resolvedModuleData = bundlerConfig[id.slice(0, idx)]);
			if (!resolvedModuleData) throw Error("Could not find the module \"" + id + "\" in the React Server Manifest. This is probably a bug in the React Server Components bundler.");
		}
		return resolvedModuleData.async ? [
			resolvedModuleData.id,
			resolvedModuleData.chunks,
			name,
			1
		] : [
			resolvedModuleData.id,
			resolvedModuleData.chunks,
			name
		];
	}
	var chunkCache = /* @__PURE__ */ new Map();
	function requireAsyncModule(id) {
		var promise = __vite_rsc_require__(id);
		if ("function" !== typeof promise.then || "fulfilled" === promise.status) return null;
		promise.then(function(value) {
			promise.status = "fulfilled";
			promise.value = value;
		}, function(reason) {
			promise.status = "rejected";
			promise.reason = reason;
		});
		return promise;
	}
	function ignoreReject() {}
	function preloadModule(metadata) {
		for (var chunks = metadata[1], promises = [], i = 0; i < chunks.length;) {
			var chunkId = chunks[i++], chunkFilename = chunks[i++], entry = chunkCache.get(chunkId);
			void 0 === entry ? (chunkMap.set(chunkId, chunkFilename), chunkFilename = __webpack_chunk_load__(chunkId), promises.push(chunkFilename), entry = chunkCache.set.bind(chunkCache, chunkId, null), chunkFilename.then(entry, ignoreReject), chunkCache.set(chunkId, chunkFilename)) : null !== entry && promises.push(entry);
		}
		return 4 === metadata.length ? 0 === promises.length ? requireAsyncModule(metadata[0]) : Promise.all(promises).then(function() {
			return requireAsyncModule(metadata[0]);
		}) : 0 < promises.length ? Promise.all(promises) : null;
	}
	function requireModule(metadata) {
		var moduleExports = __vite_rsc_require__(metadata[0]);
		if (4 === metadata.length && "function" === typeof moduleExports.then) if ("fulfilled" === moduleExports.status) moduleExports = moduleExports.value;
		else throw moduleExports.reason;
		if ("*" === metadata[2]) return moduleExports;
		if ("" === metadata[2]) return moduleExports.__esModule ? moduleExports.default : moduleExports;
		if (hasOwnProperty.call(moduleExports, metadata[2])) return moduleExports[metadata[2]];
	}
	var chunkMap = /* @__PURE__ */ new Map(), webpackGetChunkFilename = {}.u;
	({}).u = function(chunkId) {
		var flightChunk = chunkMap.get(chunkId);
		return void 0 !== flightChunk ? flightChunk : webpackGetChunkFilename(chunkId);
	};
	var ReactDOMSharedInternals = ReactDOM.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE, REACT_ELEMENT_TYPE = Symbol.for("react.transitional.element"), REACT_LAZY_TYPE = Symbol.for("react.lazy"), ASYNC_ITERATOR = Symbol.asyncIterator;
	Array.isArray;
	var knownServerReferences = /* @__PURE__ */ new WeakMap();
	function registerBoundServerReference(reference, id, bound) {
		knownServerReferences.has(reference) || knownServerReferences.set(reference, {
			id,
			originalBind: reference.bind,
			bound
		});
	}
	function createBoundServerReference(metaData, callServer) {
		function action() {
			var args = Array.prototype.slice.call(arguments);
			return bound ? "fulfilled" === bound.status ? callServer(id, bound.value.concat(args)) : Promise.resolve(bound).then(function(boundArgs) {
				return callServer(id, boundArgs.concat(args));
			}) : callServer(id, args);
		}
		var id = metaData.id, bound = metaData.bound;
		registerBoundServerReference(action, id, bound);
		return action;
	}
	function ReactPromise(status, value, reason) {
		this.status = status;
		this.value = value;
		this.reason = reason;
	}
	ReactPromise.prototype = Object.create(Promise.prototype);
	ReactPromise.prototype.then = function(resolve, reject) {
		switch (this.status) {
			case "resolved_model":
				initializeModelChunk(this);
				break;
			case "resolved_module": initializeModuleChunk(this);
		}
		switch (this.status) {
			case "fulfilled":
				"function" === typeof resolve && resolve(this.value);
				break;
			case "pending":
			case "blocked":
				"function" === typeof resolve && (null === this.value && (this.value = []), this.value.push(resolve));
				"function" === typeof reject && (null === this.reason && (this.reason = []), this.reason.push(reject));
				break;
			case "halted": break;
			default: "function" === typeof reject && reject(this.reason);
		}
	};
	function readChunk(chunk) {
		switch (chunk.status) {
			case "resolved_model":
				initializeModelChunk(chunk);
				break;
			case "resolved_module": initializeModuleChunk(chunk);
		}
		switch (chunk.status) {
			case "fulfilled": return chunk.value;
			case "pending":
			case "blocked":
			case "halted": throw chunk;
			default: throw chunk.reason;
		}
	}
	function wakeChunk(listeners, value, chunk) {
		for (var i = 0; i < listeners.length; i++) {
			var listener = listeners[i];
			"function" === typeof listener ? listener(value) : fulfillReference(listener, value, chunk);
		}
	}
	function rejectChunk(listeners, error) {
		for (var i = 0; i < listeners.length; i++) {
			var listener = listeners[i];
			"function" === typeof listener ? listener(error) : rejectReference(listener, error);
		}
	}
	function resolveBlockedCycle(resolvedChunk, reference) {
		var referencedChunk = reference.handler.chunk;
		if (null === referencedChunk) return null;
		if (referencedChunk === resolvedChunk) return reference.handler;
		reference = referencedChunk.value;
		if (null !== reference) for (referencedChunk = 0; referencedChunk < reference.length; referencedChunk++) {
			var listener = reference[referencedChunk];
			if ("function" !== typeof listener && (listener = resolveBlockedCycle(resolvedChunk, listener), null !== listener)) return listener;
		}
		return null;
	}
	function wakeChunkIfInitialized(chunk, resolveListeners, rejectListeners) {
		switch (chunk.status) {
			case "fulfilled":
				wakeChunk(resolveListeners, chunk.value, chunk);
				break;
			case "blocked": for (var i = 0; i < resolveListeners.length; i++) {
				var listener = resolveListeners[i];
				if ("function" !== typeof listener) {
					var cyclicHandler = resolveBlockedCycle(chunk, listener);
					if (null !== cyclicHandler) switch (fulfillReference(listener, cyclicHandler.value, chunk), resolveListeners.splice(i, 1), i--, null !== rejectListeners && (listener = rejectListeners.indexOf(listener), -1 !== listener && rejectListeners.splice(listener, 1)), chunk.status) {
						case "fulfilled":
							wakeChunk(resolveListeners, chunk.value, chunk);
							return;
						case "rejected":
							null !== rejectListeners && rejectChunk(rejectListeners, chunk.reason);
							return;
					}
				}
			}
			case "pending":
				if (chunk.value) for (i = 0; i < resolveListeners.length; i++) chunk.value.push(resolveListeners[i]);
				else chunk.value = resolveListeners;
				if (chunk.reason) {
					if (rejectListeners) for (resolveListeners = 0; resolveListeners < rejectListeners.length; resolveListeners++) chunk.reason.push(rejectListeners[resolveListeners]);
				} else chunk.reason = rejectListeners;
				break;
			case "rejected": rejectListeners && rejectChunk(rejectListeners, chunk.reason);
		}
	}
	function triggerErrorOnChunk(response, chunk, error) {
		"pending" !== chunk.status && "blocked" !== chunk.status ? chunk.reason.error(error) : (response = chunk.reason, chunk.status = "rejected", chunk.reason = error, null !== response && rejectChunk(response, error));
	}
	function createResolvedIteratorResultChunk(response, value, done) {
		return new ReactPromise("resolved_model", (done ? "{\"done\":true,\"value\":" : "{\"done\":false,\"value\":") + value + "}", response);
	}
	function resolveIteratorResultChunk(response, chunk, value, done) {
		resolveModelChunk(response, chunk, (done ? "{\"done\":true,\"value\":" : "{\"done\":false,\"value\":") + value + "}");
	}
	function resolveModelChunk(response, chunk, value) {
		if ("pending" !== chunk.status) chunk.reason.enqueueModel(value);
		else {
			var resolveListeners = chunk.value, rejectListeners = chunk.reason;
			chunk.status = "resolved_model";
			chunk.value = value;
			chunk.reason = response;
			null !== resolveListeners && (initializeModelChunk(chunk), wakeChunkIfInitialized(chunk, resolveListeners, rejectListeners));
		}
	}
	function resolveModuleChunk(response, chunk, value) {
		if ("pending" === chunk.status || "blocked" === chunk.status) {
			response = chunk.value;
			var rejectListeners = chunk.reason;
			chunk.status = "resolved_module";
			chunk.value = value;
			chunk.reason = null;
			null !== response && (initializeModuleChunk(chunk), wakeChunkIfInitialized(chunk, response, rejectListeners));
		}
	}
	var initializingHandler = null;
	function initializeModelChunk(chunk) {
		var prevHandler = initializingHandler;
		initializingHandler = null;
		var resolvedModel = chunk.value, response = chunk.reason;
		chunk.status = "blocked";
		chunk.value = null;
		chunk.reason = null;
		try {
			var value = JSON.parse(resolvedModel, response._fromJSON), resolveListeners = chunk.value;
			if (null !== resolveListeners) for (chunk.value = null, chunk.reason = null, resolvedModel = 0; resolvedModel < resolveListeners.length; resolvedModel++) {
				var listener = resolveListeners[resolvedModel];
				"function" === typeof listener ? listener(value) : fulfillReference(listener, value, chunk);
			}
			if (null !== initializingHandler) {
				if (initializingHandler.errored) throw initializingHandler.reason;
				if (0 < initializingHandler.deps) {
					initializingHandler.value = value;
					initializingHandler.chunk = chunk;
					return;
				}
			}
			chunk.status = "fulfilled";
			chunk.value = value;
		} catch (error) {
			chunk.status = "rejected", chunk.reason = error;
		} finally {
			initializingHandler = prevHandler;
		}
	}
	function initializeModuleChunk(chunk) {
		try {
			var value = requireModule(chunk.value);
			chunk.status = "fulfilled";
			chunk.value = value;
		} catch (error) {
			chunk.status = "rejected", chunk.reason = error;
		}
	}
	function reportGlobalError(weakResponse, error) {
		weakResponse._closed = !0;
		weakResponse._closedReason = error;
		weakResponse._chunks.forEach(function(chunk) {
			"pending" === chunk.status ? triggerErrorOnChunk(weakResponse, chunk, error) : "fulfilled" === chunk.status && null !== chunk.reason && chunk.reason.error(error);
		});
	}
	function createLazyChunkWrapper(chunk) {
		return {
			$$typeof: REACT_LAZY_TYPE,
			_payload: chunk,
			_init: readChunk
		};
	}
	function getChunk(response, id) {
		var chunks = response._chunks, chunk = chunks.get(id);
		chunk || (chunk = response._closed ? new ReactPromise("rejected", null, response._closedReason) : new ReactPromise("pending", null, null), chunks.set(id, chunk));
		return chunk;
	}
	function fulfillReference(reference, value) {
		var response = reference.response, handler = reference.handler, parentObject = reference.parentObject, key = reference.key, map = reference.map, path = reference.path;
		try {
			for (var i = 1; i < path.length; i++) {
				for (; "object" === typeof value && null !== value && value.$$typeof === REACT_LAZY_TYPE;) {
					var referencedChunk = value._payload;
					if (referencedChunk === handler.chunk) value = handler.value;
					else {
						switch (referencedChunk.status) {
							case "resolved_model":
								initializeModelChunk(referencedChunk);
								break;
							case "resolved_module": initializeModuleChunk(referencedChunk);
						}
						switch (referencedChunk.status) {
							case "fulfilled":
								value = referencedChunk.value;
								continue;
							case "blocked":
								var cyclicHandler = resolveBlockedCycle(referencedChunk, reference);
								if (null !== cyclicHandler) {
									value = cyclicHandler.value;
									continue;
								}
							case "pending":
								path.splice(0, i - 1);
								null === referencedChunk.value ? referencedChunk.value = [reference] : referencedChunk.value.push(reference);
								null === referencedChunk.reason ? referencedChunk.reason = [reference] : referencedChunk.reason.push(reference);
								return;
							case "halted": return;
							default:
								rejectReference(reference, referencedChunk.reason);
								return;
						}
					}
				}
				var name = path[i];
				if ("object" === typeof value && null !== value && hasOwnProperty.call(value, name)) value = value[name];
				else throw Error("Invalid reference.");
			}
			for (; "object" === typeof value && null !== value && value.$$typeof === REACT_LAZY_TYPE;) {
				var referencedChunk$44 = value._payload;
				if (referencedChunk$44 === handler.chunk) value = handler.value;
				else {
					switch (referencedChunk$44.status) {
						case "resolved_model":
							initializeModelChunk(referencedChunk$44);
							break;
						case "resolved_module": initializeModuleChunk(referencedChunk$44);
					}
					switch (referencedChunk$44.status) {
						case "fulfilled":
							value = referencedChunk$44.value;
							continue;
					}
					break;
				}
			}
			var mappedValue = map(response, value, parentObject, key);
			"__proto__" !== key && (parentObject[key] = mappedValue);
			"" === key && null === handler.value && (handler.value = mappedValue);
			if (parentObject[0] === REACT_ELEMENT_TYPE && "object" === typeof handler.value && null !== handler.value && handler.value.$$typeof === REACT_ELEMENT_TYPE) {
				var element = handler.value;
				switch (key) {
					case "3": element.props = mappedValue;
				}
			}
		} catch (error) {
			rejectReference(reference, error);
			return;
		}
		handler.deps--;
		0 === handler.deps && (reference = handler.chunk, null !== reference && "blocked" === reference.status && (value = reference.value, reference.status = "fulfilled", reference.value = handler.value, reference.reason = handler.reason, null !== value && wakeChunk(value, handler.value, reference)));
	}
	function rejectReference(reference, error) {
		var handler = reference.handler;
		reference = reference.response;
		handler.errored || (handler.errored = !0, handler.value = null, handler.reason = error, handler = handler.chunk, null !== handler && "blocked" === handler.status && triggerErrorOnChunk(reference, handler, error));
	}
	function waitForReference(referencedChunk, parentObject, key, response, map, path) {
		if (initializingHandler) {
			var handler = initializingHandler;
			handler.deps++;
		} else handler = initializingHandler = {
			parent: null,
			chunk: null,
			value: null,
			reason: null,
			deps: 1,
			errored: !1
		};
		parentObject = {
			response,
			handler,
			parentObject,
			key,
			map,
			path
		};
		null === referencedChunk.value ? referencedChunk.value = [parentObject] : referencedChunk.value.push(parentObject);
		null === referencedChunk.reason ? referencedChunk.reason = [parentObject] : referencedChunk.reason.push(parentObject);
		return null;
	}
	function loadServerReference(response, metaData, parentObject, key) {
		if (!response._serverReferenceConfig) return createBoundServerReference(metaData, response._callServer);
		var serverReference = resolveServerReference(response._serverReferenceConfig, metaData.id), promise = preloadModule(serverReference);
		if (promise) metaData.bound && (promise = Promise.all([promise, metaData.bound]));
		else if (metaData.bound) promise = Promise.resolve(metaData.bound);
		else return promise = requireModule(serverReference), registerBoundServerReference(promise, metaData.id, metaData.bound), promise;
		if (initializingHandler) {
			var handler = initializingHandler;
			handler.deps++;
		} else handler = initializingHandler = {
			parent: null,
			chunk: null,
			value: null,
			reason: null,
			deps: 1,
			errored: !1
		};
		promise.then(function() {
			var resolvedValue = requireModule(serverReference);
			if (metaData.bound) {
				var boundArgs = metaData.bound.value.slice(0);
				boundArgs.unshift(null);
				resolvedValue = resolvedValue.bind.apply(resolvedValue, boundArgs);
			}
			registerBoundServerReference(resolvedValue, metaData.id, metaData.bound);
			"__proto__" !== key && (parentObject[key] = resolvedValue);
			"" === key && null === handler.value && (handler.value = resolvedValue);
			if (parentObject[0] === REACT_ELEMENT_TYPE && "object" === typeof handler.value && null !== handler.value && handler.value.$$typeof === REACT_ELEMENT_TYPE) switch (boundArgs = handler.value, key) {
				case "3": boundArgs.props = resolvedValue;
			}
			handler.deps--;
			0 === handler.deps && (resolvedValue = handler.chunk, null !== resolvedValue && "blocked" === resolvedValue.status && (boundArgs = resolvedValue.value, resolvedValue.status = "fulfilled", resolvedValue.value = handler.value, resolvedValue.reason = null, null !== boundArgs && wakeChunk(boundArgs, handler.value, resolvedValue)));
		}, function(error) {
			if (!handler.errored) {
				handler.errored = !0;
				handler.value = null;
				handler.reason = error;
				var chunk = handler.chunk;
				null !== chunk && "blocked" === chunk.status && triggerErrorOnChunk(response, chunk, error);
			}
		});
		return null;
	}
	function getOutlinedModel(response, reference, parentObject, key, map) {
		reference = reference.split(":");
		var id = parseInt(reference[0], 16);
		id = getChunk(response, id);
		switch (id.status) {
			case "resolved_model":
				initializeModelChunk(id);
				break;
			case "resolved_module": initializeModuleChunk(id);
		}
		switch (id.status) {
			case "fulfilled":
				id = id.value;
				for (var i = 1; i < reference.length; i++) {
					for (; "object" === typeof id && null !== id && id.$$typeof === REACT_LAZY_TYPE;) {
						id = id._payload;
						switch (id.status) {
							case "resolved_model":
								initializeModelChunk(id);
								break;
							case "resolved_module": initializeModuleChunk(id);
						}
						switch (id.status) {
							case "fulfilled":
								id = id.value;
								break;
							case "blocked":
							case "pending": return waitForReference(id, parentObject, key, response, map, reference.slice(i - 1));
							case "halted": return initializingHandler ? (response = initializingHandler, response.deps++) : initializingHandler = {
								parent: null,
								chunk: null,
								value: null,
								reason: null,
								deps: 1,
								errored: !1
							}, null;
							default: return initializingHandler ? (initializingHandler.errored = !0, initializingHandler.value = null, initializingHandler.reason = id.reason) : initializingHandler = {
								parent: null,
								chunk: null,
								value: null,
								reason: id.reason,
								deps: 0,
								errored: !0
							}, null;
						}
					}
					id = id[reference[i]];
				}
				for (; "object" === typeof id && null !== id && id.$$typeof === REACT_LAZY_TYPE;) {
					reference = id._payload;
					switch (reference.status) {
						case "resolved_model":
							initializeModelChunk(reference);
							break;
						case "resolved_module": initializeModuleChunk(reference);
					}
					switch (reference.status) {
						case "fulfilled":
							id = reference.value;
							continue;
					}
					break;
				}
				return map(response, id, parentObject, key);
			case "pending":
			case "blocked": return waitForReference(id, parentObject, key, response, map, reference);
			case "halted": return initializingHandler ? (response = initializingHandler, response.deps++) : initializingHandler = {
				parent: null,
				chunk: null,
				value: null,
				reason: null,
				deps: 1,
				errored: !1
			}, null;
			default: return initializingHandler ? (initializingHandler.errored = !0, initializingHandler.value = null, initializingHandler.reason = id.reason) : initializingHandler = {
				parent: null,
				chunk: null,
				value: null,
				reason: id.reason,
				deps: 0,
				errored: !0
			}, null;
		}
	}
	function createMap(response, model) {
		return new Map(model);
	}
	function createSet(response, model) {
		return new Set(model);
	}
	function createBlob(response, model) {
		return new Blob(model.slice(1), { type: model[0] });
	}
	function createFormData(response, model) {
		response = new FormData();
		for (var i = 0; i < model.length; i++) response.append(model[i][0], model[i][1]);
		return response;
	}
	function extractIterator(response, model) {
		return model[Symbol.iterator]();
	}
	function createModel(response, model) {
		return model;
	}
	function parseModelString(response, parentObject, key, value) {
		if ("$" === value[0]) {
			if ("$" === value) return null !== initializingHandler && "0" === key && (initializingHandler = {
				parent: initializingHandler,
				chunk: null,
				value: null,
				reason: null,
				deps: 0,
				errored: !1
			}), REACT_ELEMENT_TYPE;
			switch (value[1]) {
				case "$": return value.slice(1);
				case "L": return parentObject = parseInt(value.slice(2), 16), response = getChunk(response, parentObject), createLazyChunkWrapper(response);
				case "@": return parentObject = parseInt(value.slice(2), 16), getChunk(response, parentObject);
				case "S": return Symbol.for(value.slice(2));
				case "h": return value = value.slice(2), getOutlinedModel(response, value, parentObject, key, loadServerReference);
				case "T":
					parentObject = "$" + value.slice(2);
					response = response._tempRefs;
					if (null == response) throw Error("Missing a temporary reference set but the RSC response returned a temporary reference. Pass a temporaryReference option with the set that was used with the reply.");
					return response.get(parentObject);
				case "Q": return value = value.slice(2), getOutlinedModel(response, value, parentObject, key, createMap);
				case "W": return value = value.slice(2), getOutlinedModel(response, value, parentObject, key, createSet);
				case "B": return value = value.slice(2), getOutlinedModel(response, value, parentObject, key, createBlob);
				case "K": return value = value.slice(2), getOutlinedModel(response, value, parentObject, key, createFormData);
				case "Z": return resolveErrorProd();
				case "i": return value = value.slice(2), getOutlinedModel(response, value, parentObject, key, extractIterator);
				case "I": return Infinity;
				case "-": return "$-0" === value ? -0 : -Infinity;
				case "N": return NaN;
				case "u": return;
				case "D": return new Date(Date.parse(value.slice(2)));
				case "n": return BigInt(value.slice(2));
				default: return value = value.slice(1), getOutlinedModel(response, value, parentObject, key, createModel);
			}
		}
		return value;
	}
	function missingCall() {
		throw Error("Trying to call a function from \"use server\" but the callServer option was not implemented in your router runtime.");
	}
	function ResponseInstance(bundlerConfig, serverReferenceConfig, moduleLoading, callServer, encodeFormAction, nonce, temporaryReferences) {
		var chunks = /* @__PURE__ */ new Map();
		this._bundlerConfig = bundlerConfig;
		this._serverReferenceConfig = serverReferenceConfig;
		this._moduleLoading = moduleLoading;
		this._callServer = void 0 !== callServer ? callServer : missingCall;
		this._encodeFormAction = encodeFormAction;
		this._nonce = nonce;
		this._chunks = chunks;
		this._stringDecoder = new TextDecoder();
		this._fromJSON = null;
		this._closed = !1;
		this._closedReason = null;
		this._tempRefs = temporaryReferences;
		this._fromJSON = createFromJSONCallback(this);
	}
	function resolveBuffer(response, id, buffer) {
		response = response._chunks;
		var chunk = response.get(id);
		chunk && "pending" !== chunk.status ? chunk.reason.enqueueValue(buffer) : (buffer = new ReactPromise("fulfilled", buffer, null), response.set(id, buffer));
	}
	function resolveModule(response, id, model) {
		var chunks = response._chunks, chunk = chunks.get(id);
		model = JSON.parse(model, response._fromJSON);
		var clientReference = resolveClientReference(response._bundlerConfig, model);
		if (model = preloadModule(clientReference)) {
			if (chunk) {
				var blockedChunk = chunk;
				blockedChunk.status = "blocked";
			} else blockedChunk = new ReactPromise("blocked", null, null), chunks.set(id, blockedChunk);
			model.then(function() {
				return resolveModuleChunk(response, blockedChunk, clientReference);
			}, function(error) {
				return triggerErrorOnChunk(response, blockedChunk, error);
			});
		} else chunk ? resolveModuleChunk(response, chunk, clientReference) : (chunk = new ReactPromise("resolved_module", clientReference, null), chunks.set(id, chunk));
	}
	function resolveStream(response, id, stream, controller) {
		response = response._chunks;
		var chunk = response.get(id);
		chunk ? "pending" === chunk.status && (id = chunk.value, chunk.status = "fulfilled", chunk.value = stream, chunk.reason = controller, null !== id && wakeChunk(id, chunk.value, chunk)) : (stream = new ReactPromise("fulfilled", stream, controller), response.set(id, stream));
	}
	function startReadableStream(response, id, type) {
		var controller = null, closed = !1;
		type = new ReadableStream({
			type,
			start: function(c) {
				controller = c;
			}
		});
		var previousBlockedChunk = null;
		resolveStream(response, id, type, {
			enqueueValue: function(value) {
				null === previousBlockedChunk ? controller.enqueue(value) : previousBlockedChunk.then(function() {
					controller.enqueue(value);
				});
			},
			enqueueModel: function(json) {
				if (null === previousBlockedChunk) {
					var chunk = new ReactPromise("resolved_model", json, response);
					initializeModelChunk(chunk);
					"fulfilled" === chunk.status ? controller.enqueue(chunk.value) : (chunk.then(function(v) {
						return controller.enqueue(v);
					}, function(e) {
						return controller.error(e);
					}), previousBlockedChunk = chunk);
				} else {
					chunk = previousBlockedChunk;
					var chunk$55 = new ReactPromise("pending", null, null);
					chunk$55.then(function(v) {
						return controller.enqueue(v);
					}, function(e) {
						return controller.error(e);
					});
					previousBlockedChunk = chunk$55;
					chunk.then(function() {
						previousBlockedChunk === chunk$55 && (previousBlockedChunk = null);
						resolveModelChunk(response, chunk$55, json);
					});
				}
			},
			close: function() {
				if (!closed) if (closed = !0, null === previousBlockedChunk) controller.close();
				else {
					var blockedChunk = previousBlockedChunk;
					previousBlockedChunk = null;
					blockedChunk.then(function() {
						return controller.close();
					});
				}
			},
			error: function(error) {
				if (!closed) if (closed = !0, null === previousBlockedChunk) controller.error(error);
				else {
					var blockedChunk = previousBlockedChunk;
					previousBlockedChunk = null;
					blockedChunk.then(function() {
						return controller.error(error);
					});
				}
			}
		});
	}
	function asyncIterator() {
		return this;
	}
	function createIterator(next) {
		next = { next };
		next[ASYNC_ITERATOR] = asyncIterator;
		return next;
	}
	function startAsyncIterable(response, id, iterator) {
		var buffer = [], closed = !1, nextWriteIndex = 0, iterable = {};
		iterable[ASYNC_ITERATOR] = function() {
			var nextReadIndex = 0;
			return createIterator(function(arg) {
				if (void 0 !== arg) throw Error("Values cannot be passed to next() of AsyncIterables passed to Client Components.");
				if (nextReadIndex === buffer.length) {
					if (closed) return new ReactPromise("fulfilled", {
						done: !0,
						value: void 0
					}, null);
					buffer[nextReadIndex] = new ReactPromise("pending", null, null);
				}
				return buffer[nextReadIndex++];
			});
		};
		resolveStream(response, id, iterator ? iterable[ASYNC_ITERATOR]() : iterable, {
			enqueueValue: function(value) {
				if (nextWriteIndex === buffer.length) buffer[nextWriteIndex] = new ReactPromise("fulfilled", {
					done: !1,
					value
				}, null);
				else {
					var chunk = buffer[nextWriteIndex], resolveListeners = chunk.value, rejectListeners = chunk.reason;
					chunk.status = "fulfilled";
					chunk.value = {
						done: !1,
						value
					};
					chunk.reason = null;
					null !== resolveListeners && wakeChunkIfInitialized(chunk, resolveListeners, rejectListeners);
				}
				nextWriteIndex++;
			},
			enqueueModel: function(value) {
				nextWriteIndex === buffer.length ? buffer[nextWriteIndex] = createResolvedIteratorResultChunk(response, value, !1) : resolveIteratorResultChunk(response, buffer[nextWriteIndex], value, !1);
				nextWriteIndex++;
			},
			close: function(value) {
				if (!closed) for (closed = !0, nextWriteIndex === buffer.length ? buffer[nextWriteIndex] = createResolvedIteratorResultChunk(response, value, !0) : resolveIteratorResultChunk(response, buffer[nextWriteIndex], value, !0), nextWriteIndex++; nextWriteIndex < buffer.length;) resolveIteratorResultChunk(response, buffer[nextWriteIndex++], "\"$undefined\"", !0);
			},
			error: function(error) {
				if (!closed) for (closed = !0, nextWriteIndex === buffer.length && (buffer[nextWriteIndex] = new ReactPromise("pending", null, null)); nextWriteIndex < buffer.length;) triggerErrorOnChunk(response, buffer[nextWriteIndex++], error);
			}
		});
	}
	function resolveErrorProd() {
		var error = Error("An error occurred in the Server Components render. The specific message is omitted in production builds to avoid leaking sensitive details. A digest property is included on this error instance which may provide additional details about the nature of the error.");
		error.stack = "Error: " + error.message;
		return error;
	}
	function mergeBuffer(buffer, lastChunk) {
		for (var l = buffer.length, byteLength = lastChunk.length, i = 0; i < l; i++) byteLength += buffer[i].byteLength;
		byteLength = new Uint8Array(byteLength);
		for (var i$56 = i = 0; i$56 < l; i$56++) {
			var chunk = buffer[i$56];
			byteLength.set(chunk, i);
			i += chunk.byteLength;
		}
		byteLength.set(lastChunk, i);
		return byteLength;
	}
	function resolveTypedArray(response, id, buffer, lastChunk, constructor, bytesPerElement) {
		buffer = 0 === buffer.length && 0 === lastChunk.byteOffset % bytesPerElement ? lastChunk : mergeBuffer(buffer, lastChunk);
		constructor = new constructor(buffer.buffer, buffer.byteOffset, buffer.byteLength / bytesPerElement);
		resolveBuffer(response, id, constructor);
	}
	function processFullBinaryRow(response, streamState, id, tag, buffer, chunk) {
		switch (tag) {
			case 65:
				resolveBuffer(response, id, mergeBuffer(buffer, chunk).buffer);
				return;
			case 79:
				resolveTypedArray(response, id, buffer, chunk, Int8Array, 1);
				return;
			case 111:
				resolveBuffer(response, id, 0 === buffer.length ? chunk : mergeBuffer(buffer, chunk));
				return;
			case 85:
				resolveTypedArray(response, id, buffer, chunk, Uint8ClampedArray, 1);
				return;
			case 83:
				resolveTypedArray(response, id, buffer, chunk, Int16Array, 2);
				return;
			case 115:
				resolveTypedArray(response, id, buffer, chunk, Uint16Array, 2);
				return;
			case 76:
				resolveTypedArray(response, id, buffer, chunk, Int32Array, 4);
				return;
			case 108:
				resolveTypedArray(response, id, buffer, chunk, Uint32Array, 4);
				return;
			case 71:
				resolveTypedArray(response, id, buffer, chunk, Float32Array, 4);
				return;
			case 103:
				resolveTypedArray(response, id, buffer, chunk, Float64Array, 8);
				return;
			case 77:
				resolveTypedArray(response, id, buffer, chunk, BigInt64Array, 8);
				return;
			case 109:
				resolveTypedArray(response, id, buffer, chunk, BigUint64Array, 8);
				return;
			case 86:
				resolveTypedArray(response, id, buffer, chunk, DataView, 1);
				return;
		}
		streamState = response._stringDecoder;
		for (var row = "", i = 0; i < buffer.length; i++) row += streamState.decode(buffer[i], decoderOptions);
		buffer = row += streamState.decode(chunk);
		switch (tag) {
			case 73:
				resolveModule(response, id, buffer);
				break;
			case 72:
				id = buffer[0];
				buffer = buffer.slice(1);
				response = JSON.parse(buffer, response._fromJSON);
				buffer = ReactDOMSharedInternals.d;
				switch (id) {
					case "D":
						buffer.D(response);
						break;
					case "C":
						"string" === typeof response ? buffer.C(response) : buffer.C(response[0], response[1]);
						break;
					case "L":
						id = response[0];
						tag = response[1];
						3 === response.length ? buffer.L(id, tag, response[2]) : buffer.L(id, tag);
						break;
					case "m":
						"string" === typeof response ? buffer.m(response) : buffer.m(response[0], response[1]);
						break;
					case "X":
						"string" === typeof response ? buffer.X(response) : buffer.X(response[0], response[1]);
						break;
					case "S":
						"string" === typeof response ? buffer.S(response) : buffer.S(response[0], 0 === response[1] ? void 0 : response[1], 3 === response.length ? response[2] : void 0);
						break;
					case "M": "string" === typeof response ? buffer.M(response) : buffer.M(response[0], response[1]);
				}
				break;
			case 69:
				tag = response._chunks;
				chunk = tag.get(id);
				buffer = JSON.parse(buffer);
				streamState = resolveErrorProd();
				streamState.digest = buffer.digest;
				chunk ? triggerErrorOnChunk(response, chunk, streamState) : (response = new ReactPromise("rejected", null, streamState), tag.set(id, response));
				break;
			case 84:
				response = response._chunks;
				(tag = response.get(id)) && "pending" !== tag.status ? tag.reason.enqueueValue(buffer) : (buffer = new ReactPromise("fulfilled", buffer, null), response.set(id, buffer));
				break;
			case 78:
			case 68:
			case 74:
			case 87: throw Error("Failed to read a RSC payload created by a development version of React on the server while using a production version on the client. Always use matching versions on the server and the client.");
			case 82:
				startReadableStream(response, id, void 0);
				break;
			case 114:
				startReadableStream(response, id, "bytes");
				break;
			case 88:
				startAsyncIterable(response, id, !1);
				break;
			case 120:
				startAsyncIterable(response, id, !0);
				break;
			case 67:
				(id = response._chunks.get(id)) && "fulfilled" === id.status && id.reason.close("" === buffer ? "\"$undefined\"" : buffer);
				break;
			default: tag = response._chunks, (chunk = tag.get(id)) ? resolveModelChunk(response, chunk, buffer) : (response = new ReactPromise("resolved_model", buffer, response), tag.set(id, response));
		}
	}
	function createFromJSONCallback(response) {
		return function(key, value) {
			if ("__proto__" !== key) {
				if ("string" === typeof value) return parseModelString(response, this, key, value);
				if ("object" === typeof value && null !== value) {
					if (value[0] === REACT_ELEMENT_TYPE) {
						if (key = {
							$$typeof: REACT_ELEMENT_TYPE,
							type: value[1],
							key: value[2],
							ref: null,
							props: value[3]
						}, null !== initializingHandler) {
							if (value = initializingHandler, initializingHandler = value.parent, value.errored) key = new ReactPromise("rejected", null, value.reason), key = createLazyChunkWrapper(key);
							else if (0 < value.deps) {
								var blockedChunk = new ReactPromise("blocked", null, null);
								value.value = key;
								value.chunk = blockedChunk;
								key = createLazyChunkWrapper(blockedChunk);
							}
						}
					} else key = value;
					return key;
				}
				return value;
			}
		};
	}
	function close(weakResponse) {
		reportGlobalError(weakResponse, Error("Connection closed."));
	}
	function createResponseFromOptions(options) {
		return new ResponseInstance(null, null, null, options && options.callServer ? options.callServer : void 0, void 0, void 0, options && options.temporaryReferences ? options.temporaryReferences : void 0);
	}
	function startReadingFromStream(response, stream, onDone) {
		function progress(_ref2) {
			var value = _ref2.value;
			if (_ref2.done) return onDone();
			var i = 0, rowState = streamState._rowState;
			_ref2 = streamState._rowID;
			for (var rowTag = streamState._rowTag, rowLength = streamState._rowLength, buffer = streamState._buffer, chunkLength = value.length; i < chunkLength;) {
				var lastIdx = -1;
				switch (rowState) {
					case 0:
						lastIdx = value[i++];
						58 === lastIdx ? rowState = 1 : _ref2 = _ref2 << 4 | (96 < lastIdx ? lastIdx - 87 : lastIdx - 48);
						continue;
					case 1:
						rowState = value[i];
						84 === rowState || 65 === rowState || 79 === rowState || 111 === rowState || 85 === rowState || 83 === rowState || 115 === rowState || 76 === rowState || 108 === rowState || 71 === rowState || 103 === rowState || 77 === rowState || 109 === rowState || 86 === rowState ? (rowTag = rowState, rowState = 2, i++) : 64 < rowState && 91 > rowState || 35 === rowState || 114 === rowState || 120 === rowState ? (rowTag = rowState, rowState = 3, i++) : (rowTag = 0, rowState = 3);
						continue;
					case 2:
						lastIdx = value[i++];
						44 === lastIdx ? rowState = 4 : rowLength = rowLength << 4 | (96 < lastIdx ? lastIdx - 87 : lastIdx - 48);
						continue;
					case 3:
						lastIdx = value.indexOf(10, i);
						break;
					case 4: lastIdx = i + rowLength, lastIdx > value.length && (lastIdx = -1);
				}
				var offset = value.byteOffset + i;
				if (-1 < lastIdx) rowLength = new Uint8Array(value.buffer, offset, lastIdx - i), processFullBinaryRow(response, streamState, _ref2, rowTag, buffer, rowLength), i = lastIdx, 3 === rowState && i++, rowLength = _ref2 = rowTag = rowState = 0, buffer.length = 0;
				else {
					value = new Uint8Array(value.buffer, offset, value.byteLength - i);
					buffer.push(value);
					rowLength -= value.byteLength;
					break;
				}
			}
			streamState._rowState = rowState;
			streamState._rowID = _ref2;
			streamState._rowTag = rowTag;
			streamState._rowLength = rowLength;
			return reader.read().then(progress).catch(error);
		}
		function error(e) {
			reportGlobalError(response, e);
		}
		var streamState = {
			_rowState: 0,
			_rowID: 0,
			_rowTag: 0,
			_rowLength: 0,
			_buffer: []
		}, reader = stream.getReader();
		reader.read().then(progress).catch(error);
	}
	exports.createFromFetch = function(promiseForResponse, options) {
		var response = createResponseFromOptions(options);
		promiseForResponse.then(function(r) {
			startReadingFromStream(response, r.body, close.bind(null, response));
		}, function(e) {
			reportGlobalError(response, e);
		});
		return getChunk(response, 0);
	};
	exports.createFromReadableStream = function(stream, options) {
		options = createResponseFromOptions(options);
		startReadingFromStream(options, stream, close.bind(null, options));
		return getChunk(options, 0);
	};
}));
//#endregion
//#region ../../../node_modules/.pnpm/@vitejs+plugin-rsc@0.5.26_r_d7be5b5d64a64a218ac22ba955ebe0d2/node_modules/@vitejs/plugin-rsc/dist/react/browser.js
var import_client_browser = /* @__PURE__ */ __toESM((/* @__PURE__ */ __commonJSMin(((exports, module) => {
	module.exports = require_react_server_dom_webpack_client_browser_production();
})))(), 1);
function createFromReadableStream(stream, options = {}) {
	return import_client_browser.createFromReadableStream(stream, {
		callServer,
		findSourceMapURL,
		...options
	});
}
function createFromFetch(promiseForResponse, options = {}) {
	return import_client_browser.createFromFetch(promiseForResponse, {
		callServer,
		findSourceMapURL,
		...options
	});
}
function callServer(...args) {
	return globalThis.__viteRscCallServer(...args);
}
function findSourceMapURL(filename, environmentName) {
	const url = new URL(
		/* @vite-ignore */
		"/__vite_rsc_findSourceMapURL",
		import.meta.url
	);
	url.searchParams.set("filename", filename);
	url.searchParams.set("environmentName", environmentName);
	return url.toString();
}
//#endregion
//#region \0virtual:vite-rsc/client-references
var client_references_default = {
	"0132a7525229": async () => {
		const m = await __vitePreload(() => import("./home-client-zukx_Gw-.js"), __vite__mapDeps([0,1,2,3,4,5]));
		return { get "default"() {
			return m["default"];
		} };
	},
	"0604f93d3a06": async () => {
		const m = await __vitePreload(() => Promise.resolve().then(() => app_router_scroll_exports), void 0);
		return { get "AppRouterScrollTarget"() {
			return m["AppRouterScrollTarget"];
		} };
	},
	"243ee20defce": async () => {
		const m = await __vitePreload(() => import("./layout-segment-context-D_56FSh-.js"), __vite__mapDeps([6,1,3]));
		return { get "LayoutSegmentProvider"() {
			return m["LayoutSegmentProvider"];
		} };
	},
	"878821595ec6": async () => {
		const m = await __vitePreload(() => import("./chat-client-DVoAPlt2.js"), __vite__mapDeps([7,1,2,3,5,8]));
		return { get "default"() {
			return m["default"];
		} };
	},
	"8c59b4cfb786": async () => {
		const m = await __vitePreload(() => Promise.resolve().then(() => default_global_error_exports), void 0);
		return { get "default"() {
			return m["default"];
		} };
	},
	"9d9ddb30364a": async () => {
		const m = await __vitePreload(() => Promise.resolve().then(() => slot_exports), void 0);
		return {
			get "BfcacheSegmentBoundary"() {
				return m["BfcacheSegmentBoundary"];
			},
			get "Children"() {
				return m["Children"];
			},
			get "ParallelSlot"() {
				return m["ParallelSlot"];
			},
			get "Slot"() {
				return m["Slot"];
			}
		};
	},
	"be06c29e631a": async () => {
		const m = await __vitePreload(() => Promise.resolve().then(() => error_boundary_exports), void 0);
		return {
			get "ErrorBoundary"() {
				return m["ErrorBoundary"];
			},
			get "ForbiddenBoundary"() {
				return m["ForbiddenBoundary"];
			},
			get "GlobalErrorBoundary"() {
				return m["GlobalErrorBoundary"];
			},
			get "NotFoundBoundary"() {
				return m["NotFoundBoundary"];
			},
			get "RedirectBoundary"() {
				return m["RedirectBoundary"];
			},
			get "SerializedErrorBoundary"() {
				return m["SerializedErrorBoundary"];
			},
			get "UnauthorizedBoundary"() {
				return m["UnauthorizedBoundary"];
			}
		};
	},
	"c5e0424ad109": async () => {
		await __vitePreload(() => Promise.resolve().then(() => app_prefetch_fetch_queue_exports), void 0);
		return {};
	},
	"de80fbf070f4": async () => {
		const m = await __vitePreload(() => import("./streamed-icons-C6b-hnDa.js"), __vite__mapDeps([9,1,3]));
		return { get "StreamedIconsInsertion"() {
			return m["StreamedIconsInsertion"];
		} };
	},
	"e97a5adc44a3": async () => {
		const m = await __vitePreload(() => import("./desktop-runtime-shell-wr2eh9Il.js"), __vite__mapDeps([10,1,2,3,4,8]));
		return { get "default"() {
			return m["default"];
		} };
	}
};
//#endregion
//#region ../../../node_modules/.pnpm/@vitejs+plugin-rsc@0.5.26_r_d7be5b5d64a64a218ac22ba955ebe0d2/node_modules/@vitejs/plugin-rsc/dist/browser.js
initialize();
function initialize() {
	setRequireModule({ load: async (id) => {
		{
			const import_ = client_references_default[id];
			if (!import_) throw new Error(`client reference not found '${id}'`);
			return import_();
		}
	} });
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-browser-entry.js
function toActionType(kind) {
	return kind === "traverse" ? "traverse" : "navigate";
}
function toOperationLane(kind) {
	switch (kind) {
		case "navigate": return "navigation";
		case "refresh": return "refresh";
		case "traverse": return "traverse";
		default: throw new Error("[vinext] Unknown navigation kind: " + String(kind));
	}
}
var MAX_VISITED_RESPONSE_CACHE_SIZE = 50;
var CLIENT_RSC_COMPATIBILITY_ID = getVinextRscCompatibilityId();
var optimisticRouteTemplates = /* @__PURE__ */ new Map();
var optimisticRouteTemplateSources = /* @__PURE__ */ new Set();
var optimisticRouteTemplateLearning = /* @__PURE__ */ new Map();
function claimInitialAppRouterBootstrap() {
	if (window.__VINEXT_RSC_ROOT__ || window.__VINEXT_RSC_BOOTSTRAP_STATE__) return false;
	window.__VINEXT_RSC_BOOTSTRAP_STATE__ = "starting";
	return true;
}
function markInitialAppRouterBootstrapHydrated() {
	window.__VINEXT_RSC_BOOTSTRAP_STATE__ = "hydrated";
}
function getBrowserRouteManifest() {
	return getNavigationRuntime()?.bootstrap.routeManifest ?? null;
}
var historyController = new AppBrowserHistoryController({
	initialHistoryState: window.history.state,
	maxHistoryStateSnapshots: 50,
	readHistoryState: () => window.history.state,
	readCurrentHref: () => window.location.href,
	pushHistoryState: (state, href) => pushHistoryStateWithoutNotify(state, "", href),
	replaceHistoryState: (state, href) => replaceHistoryStateWithoutNotify(state, "", href),
	readVisibleNavigationMetadata: () => {
		if (!hasBrowserRouterState()) return null;
		const routerState = getBrowserRouterState();
		return {
			bfcacheIds: routerState.bfcacheIds,
			previousNextUrl: routerState.previousNextUrl
		};
	}
});
var browserNavigationController = createAppBrowserNavigationController({
	basePath: "",
	getRouteManifest: getBrowserRouteManifest,
	syncHistoryStatePreviousNextUrl: (previousNextUrl, bfcacheIds) => historyController.syncCurrentHistoryStatePreviousNextUrl(previousNextUrl, bfcacheIds)
});
var discardedServerActionRefreshScheduler = {
	markNavigationSettled() {},
	markNavigationStart() {},
	schedule() {}
};
var NavigationCommitSignal = browserNavigationController.NavigationCommitSignal;
var ACTION_HTTP_FALLBACK_ROBOTS_META_ATTR = "data-vinext-action-http-fallback";
function syncServerActionHttpFallbackHead(status) {
	document.head.querySelectorAll(`meta[${ACTION_HTTP_FALLBACK_ROBOTS_META_ATTR}="robots"]`).forEach((node) => node.remove());
	if (status !== 404) return;
	const robots = document.createElement("meta");
	robots.name = "robots";
	robots.content = "noindex";
	robots.setAttribute(ACTION_HTTP_FALLBACK_ROBOTS_META_ATTR, "robots");
	document.head.appendChild(robots);
}
var BfcacheIdMapContext = getBfcacheIdMapContext();
function parseEncodedJsonHeader(value) {
	if (!value) return null;
	try {
		return JSON.parse(decodeURIComponent(value));
	} catch {
		return null;
	}
}
function isRouterStatePromise(value) {
	return value instanceof Promise;
}
var latestClientParams = {};
var visitedResponseCache = /* @__PURE__ */ new Map();
var clientNavigationCacheGeneration = 0;
var initialPrefetchRouterState = null;
var mpaNavigationScheduler = new AppBrowserMpaNavigationScheduler();
var unresolvedMpaNavigation = new Promise(() => {});
var DEFAULT_GLOBAL_ERROR_COMPONENT = DefaultGlobalError;
var synchronousPopstateScrollRestoreNavigationId = null;
function restoreHistoryStateSnapshot(historyState, navId, onApprovedBeforeCommit) {
	let restored = false;
	(0, import_react_dom.flushSync)(() => {
		restored = historyController.restoreHistorySnapshot({
			historyState,
			stageClientParams,
			approveVisibleRestore: ({ state, beforeCommit }) => browserNavigationController.restoreHistorySnapshotVisibleState({
				beforeCommit: () => {
					onApprovedBeforeCommit?.();
					beforeCommit();
				},
				navId,
				state,
				targetHref: window.location.href
			})
		});
	});
	if (!restored) return false;
	commitClientNavigationState(navId, { releaseSnapshot: false });
	return true;
}
function getBrowserRouterState() {
	return browserNavigationController.getBrowserRouterState();
}
function hasBrowserRouterState() {
	return browserNavigationController.hasBrowserRouterState();
}
function waitForBrowserRouterStateReady() {
	return browserNavigationController.waitForBrowserRouterStateReady();
}
function beginPendingBrowserRouterState() {
	return browserNavigationController.beginPendingBrowserRouterState();
}
function applyClientParams(params) {
	latestClientParams = params;
	setClientParams(params);
}
function stageClientParams(params) {
	latestClientParams = params;
	replaceClientParamsWithoutNotify(params);
}
function clearVisitedResponseCache() {
	visitedResponseCache.clear();
}
function clearPrefetchState() {
	invalidatePrefetchCache();
	optimisticRouteTemplates.clear();
	optimisticRouteTemplateSources.clear();
	optimisticRouteTemplateLearning.clear();
}
function clearClientNavigationCaches() {
	clientNavigationCacheGeneration += 1;
	clearVisitedResponseCache();
	clearPrefetchState();
	historyController.invalidateRestorableClientState();
}
function isSettledPrefetchCacheEntry(entry) {
	return entry.outcome === "cache-seeded" && entry.pending === void 0 && entry.snapshot !== void 0;
}
function parsePrefetchCacheKey(cacheKey) {
	const separatorIndex = cacheKey.indexOf("\0");
	if (separatorIndex === -1) return {
		interceptionContext: null,
		rscUrl: cacheKey
	};
	return {
		interceptionContext: cacheKey.slice(separatorIndex + 1),
		rscUrl: cacheKey.slice(0, separatorIndex)
	};
}
async function learnOptimisticRouteTemplateFromPrefetch(options) {
	const source = parsePrefetchCacheKey(options.cacheKey);
	if (source.interceptionContext !== options.interceptionContext) return false;
	if (resolvePrefetchCacheEntryMountedSlotsHeader(options.entry) !== options.mountedSlotsHeader) return false;
	if (options.interceptionContext !== null) return false;
	const elements = await decodeAppElementsPromise(createFromFetch(Promise.resolve(restoreRscResponse(options.entry.snapshot))));
	const template = createOptimisticRouteTemplate({
		allowLoadingShell: options.entry.optimisticRouteShell === true,
		basePath: "",
		elements,
		href: options.entry.snapshot.url || source.rscUrl,
		interceptionContext: options.interceptionContext,
		mountedSlotsHeader: options.mountedSlotsHeader,
		routeManifest: options.routeManifest
	});
	if (template === null) return false;
	optimisticRouteTemplates.set(getOptimisticRouteTemplateKey({
		interceptionContext: options.interceptionContext,
		mountedSlotsHeader: options.mountedSlotsHeader,
		routeId: template.routeId
	}), template);
	return true;
}
async function learnOptimisticRouteTemplatesFromPrefetchCache(options) {
	if (options.routeManifest === null) return;
	const learning = [...optimisticRouteTemplateLearning.values()];
	for (const [cacheKey, entry] of getPrefetchCache()) {
		const sourceKey = getOptimisticPrefetchSourceKey({
			cacheKey,
			interceptionContext: options.interceptionContext,
			mountedSlotsHeader: options.mountedSlotsHeader
		});
		if (optimisticRouteTemplateSources.has(sourceKey)) continue;
		if (optimisticRouteTemplateLearning.has(sourceKey)) continue;
		if (!isSettledPrefetchCacheEntry(entry)) continue;
		if (entry.prefetchKind === "route-tree") continue;
		const promise = learnOptimisticRouteTemplateFromPrefetch({
			cacheKey,
			entry,
			interceptionContext: options.interceptionContext,
			mountedSlotsHeader: options.mountedSlotsHeader,
			routeManifest: options.routeManifest
		}).then((learned) => {
			if (learned) optimisticRouteTemplateSources.add(sourceKey);
		}).finally(() => {
			optimisticRouteTemplateLearning.delete(sourceKey);
		});
		optimisticRouteTemplateLearning.set(sourceKey, promise);
		learning.push(promise);
	}
	if (learning.length === 0) return;
	await Promise.allSettled(learning);
}
function createNavigationCommitEffect(options) {
	const { bfcacheIds, href, historyUpdateMode, navId, params, previousNextUrl, targetHistoryIndex } = options;
	return () => {
		if (!browserNavigationController.isCurrentNavigation(navId)) {
			commitClientNavigationState(void 0, { releaseSnapshot: true });
			return;
		}
		historyController.commitNavigationHistory({
			bfcacheIds,
			href,
			historyUpdateMode,
			previousNextUrl,
			stageClientParams: () => stageClientParams(params),
			targetHistoryIndex
		});
		clearAppNavigationFailureTarget(href);
		commitClientNavigationState(navId);
	};
}
async function renderNavigationPayload(options) {
	syncServerActionHttpFallbackHead(null);
	return browserNavigationController.renderNavigationPayload({
		actionType: options.actionType ?? "navigate",
		createNavigationCommitEffect,
		historyUpdateMode: options.historyUpdateMode,
		navigationCommitKind: options.navigationCommitKind,
		navigationInitiationState: options.navigationInitiationState,
		navigationSnapshot: options.navigationSnapshot,
		navId: options.navId,
		nextElements: options.payload,
		onCommittedState: options.onCommittedState,
		operationLane: options.operationLane ?? "navigation",
		params: options.params,
		payloadOrigin: options.payloadOrigin,
		pendingRouterState: options.pendingRouterState,
		previousNextUrl: options.previousNextUrl,
		restoredBfcacheIds: options.restoredBfcacheIds ?? null,
		reuseCurrentBfcacheIds: options.reuseCurrentBfcacheIds ?? true,
		scrollIntent: options.scrollIntent ?? null,
		targetHistoryIndex: options.traversalIntent?.targetHistoryIndex,
		targetHref: options.targetHref,
		visibleCommitMode: options.visibleCommitMode ?? "transition"
	});
}
function evictVisitedResponseCacheIfNeeded() {
	while (visitedResponseCache.size >= MAX_VISITED_RESPONSE_CACHE_SIZE) {
		const oldest = visitedResponseCache.keys().next().value;
		if (oldest === void 0) return;
		visitedResponseCache.delete(oldest);
	}
}
function readVisitedResponseCacheCandidate(rscUrl, interceptionContext, mountedSlotsHeader, navigationKind) {
	const cacheKey = AppElementsWire.encodeCacheKey(rscUrl, interceptionContext);
	const match = findVisitedResponseCacheEntry(visitedResponseCache, rscUrl, interceptionContext);
	if (!match) return {
		cacheKey,
		entry: null,
		facts: {
			candidate: "missing",
			navigationKind
		}
	};
	return {
		cacheKey: match.cacheKey,
		entry: match.entry,
		facts: {
			candidate: "present",
			fresh: isVisitedResponseCacheEntryFresh(match.entry, {
				navigationKind,
				now: Date.now()
			}),
			mountedSlotsMatch: match.entry.elements !== void 0 || match.entry.mountedSlotsHeader === mountedSlotsHeader,
			navigationKind
		}
	};
}
function applyVisitedResponseCacheCandidateDecision(candidate, decision) {
	if (candidate.entry === null) return null;
	if (decision.kind === "reuse") {
		visitedResponseCache.delete(candidate.cacheKey);
		visitedResponseCache.set(candidate.cacheKey, candidate.entry);
		return candidate.entry;
	}
	visitedResponseCache.delete(candidate.cacheKey);
	return null;
}
function deleteVisitedResponse(rscUrl, interceptionContext) {
	deleteVisitedResponseCacheEntry(visitedResponseCache, rscUrl, interceptionContext);
}
function storeVisitedResponseSnapshot(rscUrl, interceptionContext, snapshot, params, prefetchFallbackTtlMs = DYNAMIC_NAVIGATION_CACHE_TTL, requestMountedSlotsHeader = snapshot.mountedSlotsHeader ?? null, elements, seedPrefetchCache = true, prefetchSnapshot = snapshot) {
	const cacheKey = AppElementsWire.encodeCacheKey(rscUrl, interceptionContext);
	visitedResponseCache.delete(cacheKey);
	evictVisitedResponseCacheIfNeeded();
	const entry = createVisitedResponseCacheEntry({
		fallbackTtlMs: prefetchFallbackTtlMs,
		elements,
		now: Date.now(),
		mountedSlotsHeader: requestMountedSlotsHeader,
		params,
		response: snapshot
	});
	visitedResponseCache.set(cacheKey, entry);
	if (seedPrefetchCache) seedPrefetchResponseSnapshot(rscUrl, prefetchSnapshot, interceptionContext, requestMountedSlotsHeader, prefetchFallbackTtlMs);
	return () => {
		if (visitedResponseCache.get(cacheKey) === entry) visitedResponseCache.delete(cacheKey);
		if (seedPrefetchCache) deletePrefetchResponseSnapshot(rscUrl, prefetchSnapshot, interceptionContext);
	};
}
function clientNavigationSnapshotHref(snapshot) {
	return `${window.location.origin}${createSnapshotPathAndSearch(snapshot)}`;
}
function getCurrentMatchedRoutePathname() {
	const routeKey = AppElementsWire.parseElementKey(getBrowserRouterState().routeId);
	return routeKey?.kind === "route" ? routeKey.path : null;
}
function getRequestState(navigationKind, targetPathname, previousNextUrlOverride, traverseHistoryState) {
	if (previousNextUrlOverride !== void 0) return {
		interceptionContext: resolveInterceptionContextFromPreviousNextUrl(previousNextUrlOverride, ""),
		previousNextUrl: previousNextUrlOverride
	};
	switch (navigationKind) {
		case "navigate": {
			const currentPreviousNextUrl = getBrowserRouterState().previousNextUrl;
			if (currentPreviousNextUrl !== null) return {
				interceptionContext: resolveInterceptionContextFromPreviousNextUrl(currentPreviousNextUrl, ""),
				previousNextUrl: currentPreviousNextUrl
			};
			const manifestInterceptionContext = resolveManifestNavigationInterceptionContext({
				basePath: "",
				currentPathname: window.location.pathname,
				routeManifest: getBrowserRouteManifest(),
				targetPathname
			});
			if (manifestInterceptionContext !== null) return {
				interceptionContext: manifestInterceptionContext,
				previousNextUrl: window.location.pathname + window.location.search
			};
			const middlewareRewriteInterceptionContext = resolveMiddlewareRewriteNavigationInterceptionContext({
				basePath: "",
				currentMatchedPathname: getCurrentMatchedRoutePathname(),
				currentPathname: window.location.pathname,
				routeManifest: getBrowserRouteManifest(),
				targetPathname
			});
			if (middlewareRewriteInterceptionContext !== null) return {
				interceptionContext: middlewareRewriteInterceptionContext,
				previousNextUrl: window.location.pathname + window.location.search
			};
			return {
				interceptionContext: null,
				previousNextUrl: null
			};
		}
		case "traverse": {
			const previousNextUrl = readHistoryStatePreviousNextUrl(traverseHistoryState ?? window.history.state);
			return {
				interceptionContext: resolveInterceptionContextFromPreviousNextUrl(previousNextUrl, ""),
				previousNextUrl
			};
		}
		case "refresh": {
			const currentPreviousNextUrl = getBrowserRouterState().previousNextUrl;
			return {
				interceptionContext: resolveInterceptionContextFromPreviousNextUrl(currentPreviousNextUrl, ""),
				previousNextUrl: currentPreviousNextUrl
			};
		}
		default: throw new Error("[vinext] Unknown navigation kind: " + String(navigationKind));
	}
}
function isMpaNavigationState(value) {
	return value !== null && typeof value === "object" && "kind" in value && value.kind === "mpa-navigation";
}
function performMpaNavigation(href, historyUpdateMode) {
	mpaNavigationScheduler.navigate(window, href, historyUpdateMode);
}
function AppRouterRedirectBridge({ children }) {
	const router = useRouter();
	(0, import_react.useEffect)(() => {
		const handleUnhandledRedirect = (event) => {
			const error = "reason" in event ? event.reason : event.error;
			if (!isRedirectError(error)) return;
			const result = decodeRedirectError(error.digest);
			if (!result) return;
			event.preventDefault();
			(0, import_react.startTransition)(() => {
				if (result.type === "push") router.push(result.url);
				else router.replace(result.url);
			});
		};
		window.addEventListener("error", handleUnhandledRedirect);
		window.addEventListener("unhandledrejection", handleUnhandledRedirect);
		return () => {
			window.removeEventListener("error", handleUnhandledRedirect);
			window.removeEventListener("unhandledrejection", handleUnhandledRedirect);
		};
	}, [router]);
	return children ?? null;
}
function decodeAppElementsPromise(payload) {
	return Promise.resolve(payload).then((elements) => AppElementsWire.decode(elements));
}
function BrowserRoot({ hydrationCachePublication, initialElements, initialNavigationSnapshot }) {
	const resolvedElements = (0, import_react.use)(initialElements);
	const initialMetadata = AppElementsWire.readMetadata(resolvedElements);
	const [treeStateValue, setTreeStateValue] = (0, import_react.useState)(() => ({
		activeOperation: null,
		bfcacheIds: createInitialBfcacheIdMap(resolvedElements),
		elements: resolvedElements,
		interception: initialMetadata.interception,
		interceptionContext: initialMetadata.interceptionContext,
		layoutIds: initialMetadata.layoutIds,
		layoutFlags: initialMetadata.layoutFlags,
		navigationSnapshot: initialNavigationSnapshot,
		previousNextUrl: null,
		renderId: 0,
		rootLayoutTreePath: initialMetadata.rootLayoutTreePath,
		routeId: initialMetadata.routeId,
		slotBindings: initialMetadata.slotBindings,
		visibleCommitVersion: 0
	}));
	if (isMpaNavigationState(treeStateValue)) {
		performMpaNavigation(treeStateValue.href, treeStateValue.historyUpdateMode);
		throw unresolvedMpaNavigation;
	}
	const treeState = isRouterStatePromise(treeStateValue) ? (0, import_react.use)(treeStateValue) : treeStateValue;
	const stateRef = (0, import_react.useRef)(treeState);
	stateRef.current = treeState;
	(0, import_react.useLayoutEffect)(() => {
		const setAppRouterStateValue = (value) => {
			setTreeStateValue(value);
		};
		const detach = browserNavigationController.attachBrowserRouterState(setAppRouterStateValue, stateRef);
		registerNavigationRuntimeFunctions({ navigateExternal: (href, historyUpdateMode) => {
			setTreeStateValue({
				href,
				historyUpdateMode,
				kind: "mpa-navigation"
			});
			return new Promise(() => {});
		} });
		hydrationCachePublication.commit();
		return () => {
			hydrationCachePublication.invalidate();
			registerNavigationRuntimeFunctions({ navigateExternal: void 0 });
			detach();
			setMountedSlotsHeader(null);
		};
	}, [hydrationCachePublication, setTreeStateValue]);
	(0, import_react.useEffect)(() => {
		hydrationCachePublication.complete();
		const hydratedAt = performance.now();
		window.__VINEXT_HYDRATED_AT = hydratedAt;
		window.__NEXT_HYDRATED = true;
		window.__NEXT_HYDRATED_AT = hydratedAt;
		window.__NEXT_HYDRATED_CB?.();
	}, [hydrationCachePublication]);
	(0, import_react.useLayoutEffect)(() => {
		historyController.rememberHistoryStateSnapshot(treeState);
	}, [treeState]);
	(0, import_react.useEffect)(() => {
		setWindowNextInternalSourcePage(AppElementsWire.readMetadata(treeState.elements).sourcePage);
	}, [treeState.elements]);
	(0, import_react.useLayoutEffect)(() => {
		const previousMountedSlotsHeader = getMountedSlotsHeader();
		const nextMountedSlotsHeader = getMountedSlotIdsHeader(stateRef.current.elements);
		setMountedSlotsHeader(nextMountedSlotsHeader);
		removeStylesheetLinksCoveredByInlineCss();
		if (previousMountedSlotsHeader === nextMountedSlotsHeader) return;
		const pingTimer = window.setTimeout(() => {
			getNavigationRuntime()?.functions.pingVisibleLinks?.();
		}, 0);
		return () => {
			window.clearTimeout(pingTimer);
		};
	}, [treeState.elements]);
	(0, import_react.useLayoutEffect)(() => {
		if (treeState.renderId !== 0) return;
		historyController.writeHydratedHistoryMetadata({
			bfcacheIds: treeState.bfcacheIds,
			previousNextUrl: treeState.previousNextUrl
		});
	}, [
		treeState.bfcacheIds,
		treeState.previousNextUrl,
		treeState.renderId
	]);
	const routeTree = (0, import_react.createElement)(RedirectBoundary, null, (0, import_react.createElement)(NavigationCommitSignal, { renderId: treeState.renderId }, (0, import_react.createElement)(ElementsContext.Provider, { value: treeState.elements }, (0, import_react.createElement)(Slot, { id: treeState.routeId }))));
	const bfcacheSegmentIdentities = (0, import_react.useMemo)(() => createBfcacheSegmentIdentityMap({ elements: treeState.elements }), [treeState.elements]);
	const identityMapTree = (0, import_react.createElement)(BfcacheIdentityMapContext.Provider, { value: bfcacheSegmentIdentities }, routeTree);
	const redirectedTree = (0, import_react.createElement)(AppRouterRedirectBridge, null, BfcacheIdMapContext ? (0, import_react.createElement)(BfcacheIdMapContext.Provider, { value: treeState.bfcacheIds }, identityMapTree) : identityMapTree);
	const committedTree = AppRouterContext ? (0, import_react.createElement)(AppRouterContext.Provider, { value: appRouterInstance }, redirectedTree) : redirectedTree;
	const rootErrorTree = (0, import_react.createElement)(GlobalErrorBoundary, {
		fallback: DEFAULT_GLOBAL_ERROR_COMPONENT,
		children: (0, import_react.createElement)(AppRouterScrollCommitProvider, { commitId: treeState.renderId }, committedTree)
	});
	const ClientNavigationRenderContext = getClientNavigationRenderContext();
	if (!ClientNavigationRenderContext) return rootErrorTree;
	return (0, import_react.createElement)(ClientNavigationRenderContext.Provider, { value: treeState.navigationSnapshot }, rootErrorTree);
}
function restoreHydrationNavigationContext(pathname, searchParams, params) {
	setNavigationContext({
		pathname,
		searchParams: new URLSearchParams(searchParams),
		params
	});
}
function restorePopstateScrollPosition(state, options) {
	const shouldContinue = options?.shouldContinue ?? (() => true);
	if (!shouldContinue()) return;
	if (!(state && typeof state === "object" && "__vinext_scrollY" in state)) {
		if (window.location.hash) scrollToHashTargetOnNextFrame(window.location.hash);
		return;
	}
	const y = Number(state.__vinext_scrollY);
	retryScrollTo("__vinext_scrollX" in state ? Number(state.__vinext_scrollX) : 0, y, {
		minFrames: 1,
		shouldContinue
	});
}
function isSameAppRoutePopstateTarget(href) {
	if (!hasBrowserRouterState()) return false;
	const target = new URL(href, window.location.origin);
	const routerState = getBrowserRouterState();
	return createBasePathStrippedPathAndSearch(target, "") === createSnapshotPathAndSearch(routerState.navigationSnapshot);
}
var isPageUnloading = false;
var RSC_RELOAD_KEY = "__vinext_rsc_initial_reload__";
function readReloadFlag() {
	try {
		return sessionStorage.getItem(RSC_RELOAD_KEY);
	} catch {
		return null;
	}
}
function writeReloadFlag(path) {
	try {
		sessionStorage.setItem(RSC_RELOAD_KEY, path);
	} catch {}
}
function clearReloadFlag() {
	try {
		sessionStorage.removeItem(RSC_RELOAD_KEY);
	} catch {}
}
function recoverFromBadInitialRscResponse(reason) {
	const currentPath = window.location.pathname + window.location.search;
	if (readReloadFlag() === currentPath) {
		clearReloadFlag();
		console.error(`[vinext] Initial RSC fetch ${reason} after reload; aborting hydration. Server-rendered HTML remains visible; client components will not hydrate.`);
		return null;
	}
	writeReloadFlag(currentPath);
	if (readReloadFlag() !== currentPath) {
		console.error(`[vinext] Initial RSC fetch ${reason}; sessionStorage unavailable so the reload-loop guard cannot persist — aborting hydration. Server-rendered HTML remains visible; client components will not hydrate.`);
		return null;
	}
	console.warn(`[vinext] Initial RSC fetch ${reason}; reloading once to let the server render the HTML error page`);
	window.location.reload();
	return null;
}
async function readInitialRscStream() {
	const vinext = getVinextBrowserGlobal();
	const runtimeRsc = getNavigationRuntime()?.bootstrap.rsc;
	if (runtimeRsc || vinext.__VINEXT_RSC_CHUNKS__ || vinext.__VINEXT_RSC_DONE__) {
		clearReloadFlag();
		clearHardNavigationLoopGuard();
		if (runtimeRsc) {
			applyRuntimeRscBootstrap(runtimeRsc);
			if (runtimeRsc.done) {
				registerNavigationRuntimeBootstrap({ rsc: void 0 });
				return chunksToReadableStream(runtimeRsc.rsc);
			}
			return createProgressiveRscStream();
		}
		const params = vinext.__VINEXT_RSC_PARAMS__ ?? {};
		if (vinext.__VINEXT_RSC_PARAMS__) applyClientParams(vinext.__VINEXT_RSC_PARAMS__);
		if (vinext.__VINEXT_RSC_NAV__) restoreHydrationNavigationContext(vinext.__VINEXT_RSC_NAV__.pathname, vinext.__VINEXT_RSC_NAV__.searchParams, params);
		return createProgressiveRscStream();
	}
	const rscHeaders = createRscRequestHeaders();
	const rscResponse = await fetch(await createRscRequestUrl(window.location.pathname + window.location.search, rscHeaders), {
		credentials: "include",
		headers: rscHeaders
	});
	if (!rscResponse.ok) return recoverFromBadInitialRscResponse(`returned ${rscResponse.status}`);
	const contentType = rscResponse.headers.get("content-type") ?? "";
	if (!contentType.startsWith("text/x-component")) return recoverFromBadInitialRscResponse(`returned non-RSC content-type "${contentType || "(missing)"}"`);
	if (!rscResponse.body) return recoverFromBadInitialRscResponse("returned empty body");
	clearReloadFlag();
	clearHardNavigationLoopGuard();
	const parsedParams = parseEncodedJsonHeader(rscResponse.headers.get(VINEXT_PARAMS_HEADER));
	const params = parsedParams ?? {};
	if (parsedParams) try {
		applyClientParams(parsedParams);
	} catch {}
	restoreHydrationNavigationContext(window.location.pathname, window.location.search, params);
	return rscResponse.body;
}
function applyRuntimeRscBootstrap(rsc) {
	const params = rsc.params ?? {};
	if (rsc.params) applyClientParams(rsc.params);
	if (rsc.nav) restoreHydrationNavigationContext(rsc.nav.pathname, rsc.nav.searchParams, params);
}
async function main() {
	if (!claimInitialAppRouterBootstrap()) return;
	let devErrorOverlay = null;
	const initialRscBootstrap = getNavigationRuntime()?.bootstrap.rsc;
	const rscStream = await readInitialRscStream();
	if (rscStream === null) return;
	bootstrapHydration(rscStream, devErrorOverlay, initialRscBootstrap);
}
function bootstrapHydration(rscStream, devErrorOverlay, initialRscBootstrap) {
	const hydrationCachePublication = createHydrationCachePublication();
	const cacheGeneration = clientNavigationCacheGeneration;
	const [reactBranch, cacheBranch] = rscStream.tee();
	const root = decodeAppElementsPromise(createFromReadableStream(reactBranch));
	const initialNavigationSnapshot = createClientNavigationRenderSnapshot(window.location.href, latestClientParams);
	const initialParams = initialNavigationSnapshot.params;
	const initialPathAndSearch = createSnapshotPathAndSearch(initialNavigationSnapshot);
	const initialCacheBuffer = new Response(cacheBranch).arrayBuffer();
	Promise.all([root, initialCacheBuffer]).then(async ([elements, buffer]) => {
		if (cacheGeneration !== clientNavigationCacheGeneration) return;
		const metadata = AppElementsWire.readMetadata(elements);
		initialPrefetchRouterState = {
			pathAndSearch: initialPathAndSearch,
			routeId: metadata.routeId
		};
		if (!isCompleteAppPayloadMetadata(metadata)) return;
		const mountedSlotsHeader = getMountedSlotIdsHeader(elements);
		const rscUrl = await createRscRequestUrl(initialPathAndSearch, createRscRequestHeaders({ mountedSlotsHeader }));
		if (cacheGeneration !== clientNavigationCacheGeneration) return;
		const snapshot = {
			compatibilityIdHeader: CLIENT_RSC_COMPATIBILITY_ID,
			buffer,
			contentType: VINEXT_RSC_CONTENT_TYPE,
			...initialRscBootstrap?.dynamicStaleTimeSeconds !== void 0 ? { dynamicStaleTimeSeconds: initialRscBootstrap.dynamicStaleTimeSeconds } : {},
			...initialRscBootstrap?.staleTimeSeconds === void 0 ? {} : { serverStaleTime: {
				kind: "resolved",
				seconds: initialRscBootstrap.staleTimeSeconds
			} },
			mountedSlotsHeader,
			paramsHeader: encodeURIComponent(JSON.stringify(initialParams)),
			renderedPathAndSearch: null,
			url: rscUrl
		};
		const fallbackTtlMs = initialRscBootstrap?.initialCacheKind === "static" ? PREFETCH_CACHE_TTL : DYNAMIC_NAVIGATION_CACHE_TTL;
		hydrationCachePublication.publish(() => {
			if (cacheGeneration !== clientNavigationCacheGeneration) return () => {};
			return storeVisitedResponseSnapshot(rscUrl, metadata.interceptionContext, snapshot, initialParams, fallbackTtlMs, mountedSlotsHeader, elements, false);
		});
	}).catch(() => {});
	historyController.writeBootstrapHistoryMetadata();
	const reportUncaughtError = createOnUncaughtError();
	const onUncaughtError = (...args) => {
		hydrationCachePublication.fail();
		reportUncaughtError(...args);
	};
	const onRecoverableError = (...args) => {
		hydrationCachePublication.fail();
		prodOnRecoverableError(...args);
	};
	const invalidateOnCaughtError = (handler) => ((...args) => {
		hydrationCachePublication.fail();
		handler(...args);
	});
	const hydrateRootOptions = createVinextHydrateRootOptions({
		formState: consumeInitialFormState(getVinextBrowserGlobal()),
		onCaughtError: invalidateOnCaughtError(createProdOnCaughtError(onUncaughtError)),
		onRecoverableError,
		onUncaughtError
	});
	const children = (0, import_react.createElement)(BrowserRoot, {
		hydrationCachePublication,
		initialElements: root,
		initialNavigationSnapshot
	});
	const errorShellStyles = document.querySelectorAll("style[data-vinext-error-shell-style]");
	if (document.documentElement.id === "__next_error__") {
		const { formState: _inertFormState, ...createRootOptions } = hydrateRootOptions;
		for (const style of errorShellStyles) style.remove();
		(0, import_react.startTransition)(() => {
			const clientRoot = (0, import_client.createRoot)(document, createRootOptions);
			clientRoot.render(children);
			window.__VINEXT_RSC_ROOT__ = clientRoot;
		});
	} else window.__VINEXT_RSC_ROOT__ = hydrateRootInTransition({
		children,
		container: document,
		hydrateRoot: import_client.hydrateRoot,
		options: hydrateRootOptions,
		startTransition: import_react.startTransition
	});
	markInitialAppRouterBootstrapHydrated();
	let activeNavigationAbortController = null;
	function abortSupersededNavigation() {
		activeNavigationAbortController?.abort();
		activeNavigationAbortController = null;
	}
	registerNavigationRuntimeFunctions({
		clearNavigationCaches: clearClientNavigationCaches,
		commitHashNavigation: (href, historyUpdateMode, scroll) => historyController.commitHashOnlyNavigation(href, historyUpdateMode, scroll),
		getPrefetchRouterState: () => {
			if (!browserNavigationController.hasBrowserRouterState()) {
				if (initialPrefetchRouterState) return initialPrefetchRouterState;
				const routeManifest = getNavigationRuntime()?.bootstrap.routeManifest ?? null;
				const match = routeManifest ? matchOptimisticRouteManifestRoute({
					basePath: "",
					href: window.location.href,
					routeManifest
				}) : null;
				return match ? {
					pathAndSearch: createBasePathStrippedPathAndSearch(new URL(window.location.href), ""),
					routeId: match.route.id
				} : null;
			}
			const state = browserNavigationController.getBrowserRouterState();
			return {
				pathAndSearch: createSnapshotPathAndSearch(state.navigationSnapshot),
				routeId: state.routeId
			};
		},
		navigate: async function navigateRsc(href, redirectDepth = 0, navigationKind = "navigate", historyUpdateMode, previousNextUrlOverride, programmaticTransition = false, traversalIntent, scrollIntent, visibleCommitMode = "transition") {
			abortSupersededNavigation();
			const navigationAbortController = new AbortController();
			activeNavigationAbortController = navigationAbortController;
			let pendingRouterState = null;
			const navId = browserNavigationController.beginNavigation();
			const navigationCacheGeneration = clientNavigationCacheGeneration;
			discardedServerActionRefreshScheduler.markNavigationStart();
			let currentHref = href;
			let currentHistoryMode = historyUpdateMode;
			let currentPrevNextUrl = previousNextUrlOverride;
			let redirectCount = redirectDepth;
			let detachedNavigationCommits = false;
			const activeTraversalIntent = navigationKind === "traverse" ? traversalIntent ?? historyController.resolveTraversalIntent(window.history.state) : null;
			const performHardNavigationForScrollIntent = (targetHref, mode) => {
				consumeAppRouterScrollIntent(scrollIntent ?? null);
				const didNavigate = browserNavigationController.performHardNavigation(targetHref, mode);
				if (!didNavigate) clearAppNavigationFailureTarget(targetHref);
				return didNavigate;
			};
			let restoredBfcacheIds = navigationKind === "traverse" ? historyController.readCurrentBfcacheVersionHistoryIds(activeTraversalIntent?.historyState ?? window.history.state) : null;
			const reuseCurrentBfcacheIds = navigationKind !== "traverse" || !historyController.isCacheInvalidationGuarded() && historyController.isCurrentBfcacheVersion(activeTraversalIntent?.historyState ?? window.history.state);
			try {
				const shouldUsePendingRouterState = programmaticTransition;
				if (hasBrowserRouterState()) {
					if (shouldUsePendingRouterState) pendingRouterState = beginPendingBrowserRouterState();
				} else {
					await waitForBrowserRouterStateReady();
					if (!browserNavigationController.isCurrentNavigation(navId)) return;
					if (shouldUsePendingRouterState) pendingRouterState = beginPendingBrowserRouterState();
				}
				const navigationInitiationState = getBrowserRouterState();
				const mountedSlotsHeader = getMountedSlotIdsHeader(navigationInitiationState.elements);
				while (true) {
					const url = new URL(currentHref, window.location.origin);
					const requestState = getRequestState(navigationKind, url.pathname, currentPrevNextUrl, activeTraversalIntent?.historyState);
					const requestInterceptionContext = requestState.interceptionContext;
					const requestPreviousNextUrl = requestState.previousNextUrl;
					if (navigationKind === "refresh") historyController.syncCurrentHistoryStatePreviousNextUrl(requestPreviousNextUrl, getBrowserRouterState().bfcacheIds);
					setPendingPathname(url.pathname, navId);
					const earlyIntentDecision = navigationKind === "navigate" ? navigationPlanner.classifyEarlyNavigationIntent({
						basePath: "",
						currentHref: clientNavigationSnapshotHref(navigationInitiationState.navigationSnapshot),
						mode: "push",
						scroll: false,
						targetHref: url.href
					}) : null;
					const shouldBypassNavigationCache = earlyIntentDecision?.kind === "flightNavigation" && earlyIntentDecision.bypassNavigationCache;
					const requestHeaders = createRscRequestHeaders({
						fetchPriority: "auto",
						interceptionContext: requestInterceptionContext,
						mountedSlotsHeader
					});
					const targetPathAndSearch = url.pathname + url.search;
					const additionalPrefetchPathAndSearch = [];
					const settledPrefetchedResponse = peekSettledPrefetchResponseForNavigation({
						additionalRscUrls: additionalPrefetchPathAndSearch,
						bypassNavigationCache: shouldBypassNavigationCache,
						interceptionContext: requestInterceptionContext,
						mountedSlotsHeader,
						navigationKind,
						targetPathAndSearch
					});
					const rscUrl = settledPrefetchedResponse ? resolvePrefetchNavigationResponseUrl({
						additionalRscUrls: additionalPrefetchPathAndSearch,
						origin: window.location.origin,
						responseUrl: settledPrefetchedResponse.url,
						visibleRscUrl: targetPathAndSearch
					}) : await createRscRequestUrl(targetPathAndSearch, requestHeaders);
					const additionalPrefetchRscUrls = settledPrefetchedResponse ? additionalPrefetchPathAndSearch : await Promise.all(additionalPrefetchPathAndSearch.map((href) => createRscRequestUrl(href, requestHeaders)));
					const visitedResponseCandidate = shouldBypassNavigationCache ? {
						cacheKey: AppElementsWire.encodeCacheKey(rscUrl, requestInterceptionContext),
						entry: null,
						facts: {
							candidate: "missing",
							navigationKind
						}
					} : readVisitedResponseCacheCandidate(rscUrl, requestInterceptionContext, mountedSlotsHeader, navigationKind);
					const cachedRoute = applyVisitedResponseCacheCandidateDecision(visitedResponseCandidate, navigationPlanner.classifyVisitedResponseCacheCandidate(visitedResponseCandidate.facts));
					const visitedResponse = cachedRoute === null ? { status: "unavailable" } : { status: "available" };
					const prefetchProbeDecision = navigationPlanner.classifyNavigationPrefetchProbe({
						bypassNavigationCache: shouldBypassNavigationCache,
						navigationKind,
						visitedResponse
					});
					let routeManifest = navigationKind === "navigate" ? getBrowserRouteManifest() : null;
					const hasPrefetchCandidate = settledPrefetchedResponse !== null || prefetchProbeDecision.kind === "probe" && hasPrefetchCacheEntryForNavigation(rscUrl, requestInterceptionContext, mountedSlotsHeader, {
						additionalRscUrls: additionalPrefetchRscUrls,
						notifyInvalidation: false
					});
					const reuseDecision = navigationPlanner.classifyNavigationReuse({
						bypassNavigationCache: shouldBypassNavigationCache,
						navigationKind,
						optimisticRouteShell: routeManifest === null ? {
							reason: "routeManifestMissing",
							status: "unavailable"
						} : { status: "available" },
						prefetch: hasPrefetchCandidate ? { status: "available" } : { status: "unavailable" },
						targetHref: currentHref,
						visitedResponse
					});
					if (reuseDecision.kind === "reuseVisitedResponse" && cachedRoute) {
						const cachedFetchDecision = navigationPlanner.classifyRscFetchResult({
							clientCompatibilityId: CLIENT_RSC_COMPATIBILITY_ID,
							compatibilityIdHeader: cachedRoute.response.compatibilityIdHeader ?? null,
							currentHref,
							effectiveHistoryUpdateMode: currentHistoryMode ?? "replace",
							hasBody: true,
							isRscContentType: true,
							origin: window.location.origin,
							redirectDepth: redirectCount,
							requestPreviousNextUrl,
							responseOk: true,
							responseUrl: cachedRoute.response.url,
							source: "cached",
							streamedRedirectTarget: null
						});
						if (cachedFetchDecision.kind === "hardNavigate") {
							if (cachedFetchDecision.reason === "redirectDepthExhausted") console.error("[vinext] Too many RSC redirects — aborting navigation to prevent infinite loop.");
							performHardNavigationForScrollIntent(cachedFetchDecision.url);
							return;
						}
						if (cachedFetchDecision.kind === "followRedirect") {
							if (navigationKind === "traverse") restoredBfcacheIds = null;
							currentHref = cachedFetchDecision.redirect.href;
							currentHistoryMode = cachedFetchDecision.redirect.historyUpdateMode;
							currentPrevNextUrl = cachedFetchDecision.redirect.previousNextUrl;
							redirectCount = cachedFetchDecision.redirect.redirectDepth;
							continue;
						}
						if (!browserNavigationController.isCurrentNavigation(navId)) return;
						const cachedParams = cachedRoute.params;
						const cachedNavigationSnapshot = createClientNavigationRenderSnapshot(currentHref, cachedParams);
						const cachedPayload = cachedRoute.elements ? Promise.resolve(cachedRoute.elements) : decodeAppElementsPromise(createFromFetch(Promise.resolve(restoreRscResponse(cachedRoute.response))));
						if (!browserNavigationController.isCurrentNavigation(navId)) return;
						if (await renderNavigationPayload({
							actionType: toActionType(navigationKind),
							historyUpdateMode: currentHistoryMode,
							navigationCommitKind: detachedNavigationCommits ? "authoritative" : void 0,
							navigationInitiationState,
							navigationSnapshot: cachedNavigationSnapshot,
							navId,
							operationLane: toOperationLane(navigationKind),
							params: cachedParams,
							payload: cachedPayload,
							payloadOrigin: cachedRoute.elements ? COMMITTED_CACHE_APP_NAVIGATION_PAYLOAD_ORIGIN : VISITED_CACHE_APP_NAVIGATION_PAYLOAD_ORIGIN,
							pendingRouterState: detachedNavigationCommits ? null : pendingRouterState,
							previousNextUrl: requestPreviousNextUrl,
							restoredBfcacheIds,
							reuseCurrentBfcacheIds,
							scrollIntent,
							targetHref: currentHref,
							traversalIntent: activeTraversalIntent,
							visibleCommitMode
						}) === "no-commit") {
							if (!browserNavigationController.isCurrentNavigation(navId)) return;
							deleteVisitedResponse(rscUrl, requestInterceptionContext);
							continue;
						}
						return;
					}
					let navResponse;
					let navResponseExpiresAt;
					let navResponseUrl = null;
					let consumedPrefetchSnapshot;
					let prefetchedElements;
					let fallbackReuseDecision = reuseDecision;
					if (reuseDecision.kind === "consumePrefetch") {
						const prefetchedResponse = settledPrefetchedResponse ? consumePrefetchResponse(targetPathAndSearch, requestInterceptionContext, mountedSlotsHeader, { additionalRscUrls: additionalPrefetchPathAndSearch }) : await consumePrefetchResponseForNavigation(rscUrl, requestInterceptionContext, mountedSlotsHeader, {
							additionalRscUrls: additionalPrefetchRscUrls,
							shouldConsume: () => browserNavigationController.isCurrentNavigation(navId)
						});
						if (!browserNavigationController.isCurrentNavigation(navId)) return;
						if (prefetchedResponse) {
							navResponse = restoreRscResponse(prefetchedResponse, false);
							navResponseUrl = resolvePrefetchNavigationResponseUrl({
								additionalRscUrls: additionalPrefetchRscUrls,
								origin: window.location.origin,
								responseUrl: prefetchedResponse.url,
								visibleRscUrl: rscUrl
							});
							const publication = prepareConsumedPrefetchResponseForPublication(prefetchedResponse, navResponseUrl);
							consumedPrefetchSnapshot = publication.snapshot;
							prefetchedElements = publication.preparedElements;
							navResponseExpiresAt = publication.expiresAt;
						}
						if (!navResponse) {
							routeManifest = navigationKind === "navigate" ? getBrowserRouteManifest() : null;
							fallbackReuseDecision = navigationPlanner.classifyNavigationReuse({
								bypassNavigationCache: shouldBypassNavigationCache,
								navigationKind,
								optimisticRouteShell: routeManifest === null ? {
									reason: "routeManifestMissing",
									status: "unavailable"
								} : { status: "available" },
								prefetch: { status: "unavailable" },
								targetHref: currentHref,
								visitedResponse: { status: "unavailable" }
							});
						}
					}
					if (!navResponse && fallbackReuseDecision.kind === "attemptOptimisticRouteShell") {
						await learnOptimisticRouteTemplatesFromPrefetchCache({
							interceptionContext: requestInterceptionContext,
							mountedSlotsHeader,
							routeManifest
						});
						if (!browserNavigationController.isCurrentNavigation(navId)) return;
						if (routeManifest !== null) {
							const optimisticPayload = resolveOptimisticNavigationPayload({
								basePath: "",
								href: currentHref,
								interceptionContext: requestInterceptionContext,
								mountedSlotsHeader,
								routeManifest,
								templates: optimisticRouteTemplates
							});
							if (optimisticPayload !== null) {
								detachedNavigationCommits = true;
								const optimisticNavigationSnapshot = createClientNavigationRenderSnapshot(currentHref, optimisticPayload.params);
								renderNavigationPayload({
									actionType: toActionType(navigationKind),
									historyUpdateMode: currentHistoryMode,
									navigationCommitKind: "detached",
									navigationInitiationState,
									navigationSnapshot: optimisticNavigationSnapshot,
									navId,
									operationLane: toOperationLane(navigationKind),
									params: optimisticPayload.params,
									payload: Promise.resolve(optimisticPayload.elements),
									payloadOrigin: FRESH_APP_NAVIGATION_PAYLOAD_ORIGIN,
									pendingRouterState: null,
									previousNextUrl: requestPreviousNextUrl,
									restoredBfcacheIds,
									reuseCurrentBfcacheIds,
									scrollIntent,
									targetHref: currentHref,
									traversalIntent: activeTraversalIntent,
									visibleCommitMode
								}).catch((error) => {
									if (browserNavigationController.isCurrentNavigation(navId)) console.error("[vinext] Optimistic RSC navigation error:", error);
								});
							}
						}
					}
					if (!navResponse) {
						if (navigationKind === "navigate") {
							const clientReuseManifestHeader = createClientReuseManifestHeaderFromVisibleAppState(navigationInitiationState);
							if (clientReuseManifestHeader !== null) requestHeaders.set(VINEXT_CLIENT_REUSE_MANIFEST_HEADER, clientReuseManifestHeader);
						}
						navResponse = await fetch(rscUrl, {
							headers: requestHeaders,
							credentials: "include",
							priority: "auto",
							signal: navigationAbortController.signal
						});
					}
					if (!browserNavigationController.isCurrentNavigation(navId)) return;
					const navContentType = navResponse.headers.get("content-type") ?? "";
					const streamedRedirectTarget = navResponse.headers.get(VINEXT_RSC_REDIRECT_HEADER);
					const streamedRedirectTypeHeader = navResponse.headers.get(VINEXT_RSC_REDIRECT_TYPE_HEADER);
					const streamedRedirectType = streamedRedirectTypeHeader === "push" || streamedRedirectTypeHeader === "replace" ? streamedRedirectTypeHeader : null;
					if (blockDangerousStreamedRscRedirect(navResponse, streamedRedirectTarget)) return;
					const liveFetchDecision = navigationPlanner.classifyRscFetchResult({
						clientCompatibilityId: CLIENT_RSC_COMPATIBILITY_ID,
						compatibilityIdHeader: navResponse.headers.get(VINEXT_RSC_COMPATIBILITY_ID_HEADER),
						currentHref,
						effectiveHistoryUpdateMode: currentHistoryMode ?? "replace",
						hasBody: navResponse.body !== null,
						isRscContentType: navContentType.startsWith(VINEXT_RSC_CONTENT_TYPE),
						origin: window.location.origin,
						redirectDepth: redirectCount,
						requestPreviousNextUrl,
						responseOk: navResponse.ok,
						responseUrl: navResponseUrl ?? navResponse.url,
						source: "live",
						streamedRedirectTarget,
						streamedRedirectType
					});
					if (liveFetchDecision.kind === "hardNavigate") {
						if (liveFetchDecision.discardBody) navResponse.body?.cancel().catch(() => {});
						if (liveFetchDecision.reason === "redirectDepthExhausted") console.error("[vinext] Too many RSC redirects — aborting navigation to prevent infinite loop.");
						if (liveFetchDecision.reason === "streamedRedirectLoop") console.error("[vinext] RSC streamed redirect resolved to the current URL — aborting navigation to prevent infinite loop.");
						performHardNavigationForScrollIntent(liveFetchDecision.url, liveFetchDecision.hardNavigationMode);
						return;
					}
					if (liveFetchDecision.kind === "followRedirect") {
						if (liveFetchDecision.discardBody) navResponse.body?.cancel().catch(() => {});
						if (navigationKind === "traverse") restoredBfcacheIds = null;
						currentHref = liveFetchDecision.redirect.href;
						currentHistoryMode = liveFetchDecision.redirect.historyUpdateMode;
						currentPrevNextUrl = liveFetchDecision.redirect.previousNextUrl;
						redirectCount = liveFetchDecision.redirect.redirectDepth;
						continue;
					}
					const navParams = parseEncodedJsonHeader(navResponse.headers.get("X-Vinext-Params")) ?? {};
					const navigationSnapshot = createClientNavigationRenderSnapshot(currentHref, navParams);
					const navBody = navResponse.body;
					if (!navBody) return;
					const [reactBranch, cacheBranch] = navBody.tee();
					const reactResponse = stripRscCompletionMetadataResponse(new Response(reactBranch, {
						status: navResponse.status,
						headers: navResponse.headers
					}));
					const cacheBufferPromise = new Response(cacheBranch).arrayBuffer();
					cacheBufferPromise.catch(() => {});
					if (!browserNavigationController.isCurrentNavigation(navId)) return;
					if (prefetchedElements) reactResponse.body?.cancel().catch(() => {});
					const rscPayload = prefetchedElements ? prefetchedElements : decodeAppElementsPromise(createFromFetch(Promise.resolve(reactResponse)));
					if (!browserNavigationController.isCurrentNavigation(navId)) return;
					let committedState = null;
					if (await renderNavigationPayload({
						actionType: toActionType(navigationKind),
						historyUpdateMode: currentHistoryMode,
						navigationCommitKind: detachedNavigationCommits ? "authoritative" : void 0,
						navigationInitiationState,
						navigationSnapshot,
						navId,
						onCommittedState: (state) => {
							committedState = state;
							if (activeNavigationAbortController === navigationAbortController) activeNavigationAbortController = null;
						},
						operationLane: toOperationLane(navigationKind),
						params: navParams,
						payload: rscPayload,
						payloadOrigin: FRESH_APP_NAVIGATION_PAYLOAD_ORIGIN,
						pendingRouterState: detachedNavigationCommits ? null : pendingRouterState,
						previousNextUrl: requestPreviousNextUrl,
						restoredBfcacheIds,
						reuseCurrentBfcacheIds,
						scrollIntent,
						targetHref: currentHref,
						traversalIntent: activeTraversalIntent,
						visibleCommitMode: prefetchedElements ? "synchronous" : visibleCommitMode
					}) !== "committed") return;
					committedState ??= getBrowserRouterState();
					try {
						const renderedElements = await rscPayload;
						if (navigationCacheGeneration !== clientNavigationCacheGeneration) return;
						const metadata = AppElementsWire.readMetadata(renderedElements);
						if (navigationCacheGeneration !== clientNavigationCacheGeneration) return;
						const responseSnapshot = consumedPrefetchSnapshot ?? createCachedRscResponseSnapshot(navResponse, await cacheBufferPromise, navResponseUrl);
						const cacheRestorable = !(responseSnapshot.completedDynamicStaleTimeSeconds !== void 0) && isCacheRestorableAppPayloadMetadata(metadata);
						const { completedDynamicStaleTimeSeconds: _staticCompletedDynamicStaleTime, dynamicStaleTimeSeconds: _staticDynamicStaleTime, ...staticResponseSnapshot } = responseSnapshot;
						const snapshot = {
							...cacheRestorable ? staticResponseSnapshot : {
								...responseSnapshot,
								...responseSnapshot.dynamicStaleTimeSeconds === void 0 && metadata.dynamicStaleTimeSeconds !== void 0 ? { dynamicStaleTimeSeconds: metadata.dynamicStaleTimeSeconds } : {}
							},
							mountedSlotsHeader: getMountedSlotIdsHeader(renderedElements)
						};
						const prefetchSnapshot = preserveCommittedPrefetchExpiry(snapshot, navResponseExpiresAt);
						const interceptionContext = resolveVisitedResponseInterceptionContext(requestInterceptionContext, metadata.interceptionContext);
						if (cacheRestorable) {
							if (navigationCacheGeneration !== clientNavigationCacheGeneration) return;
							storeVisitedResponseSnapshot(rscUrl, interceptionContext, snapshot, navParams, PREFETCH_CACHE_TTL, mountedSlotsHeader, void 0, true, prefetchSnapshot);
						} else {
							const state = committedState;
							const committedElements = {
								...state.elements,
								[AppElementsWire.keys.layoutFlags]: state.layoutFlags,
								[AppElementsWire.keys.layoutIds]: state.layoutIds,
								[AppElementsWire.keys.skippedLayoutIds]: [],
								[AppElementsWire.keys.slotBindings]: state.slotBindings
							};
							if (navigationCacheGeneration !== clientNavigationCacheGeneration) return;
							storeVisitedResponseSnapshot(rscUrl, interceptionContext, snapshot, navParams, DYNAMIC_NAVIGATION_CACHE_TTL, mountedSlotsHeader, committedElements, true, prefetchSnapshot);
						}
					} catch {}
					return;
				}
			} catch (error) {
				if (!browserNavigationController.isCurrentNavigation(navId)) return;
				if (!isPageUnloading) console.error("[vinext] RSC navigation error:", error);
				performHardNavigationForScrollIntent(navigationPlanner.classifyRscNavigationError({ currentHref }).url);
			} finally {
				if (activeNavigationAbortController === navigationAbortController) activeNavigationAbortController = null;
				browserNavigationController.finalizeNavigation(navId, pendingRouterState);
				discardedServerActionRefreshScheduler.markNavigationSettled();
			}
		},
		preparePrefetchResponse: (response) => decodeAppElementsPromise(createFromFetch(Promise.resolve(response)))
	});
	const handlePopstate = createPopstateRestoreHandler({
		getActiveNavigationId: browserNavigationController.getActiveNavigationId.bind(browserNavigationController),
		getPendingNavigation: () => window.__VINEXT_RSC_PENDING__,
		getNavigate: () => getNavigationRuntime()?.functions.navigate,
		isCurrentNavigation: browserNavigationController.isCurrentNavigation.bind(browserNavigationController),
		notifyAppRouterTransitionStart: (href) => {
			notifyAppRouterTransitionStart(href, "traverse");
		},
		restorePopstateScrollPosition,
		setPendingNavigation: (pendingNavigation) => {
			window.__VINEXT_RSC_PENDING__ = pendingNavigation;
		},
		shouldSkipScrollRestore: (navId) => synchronousPopstateScrollRestoreNavigationId === navId
	});
	window.addEventListener("popstate", (event) => {
		const href = window.location.href;
		if (isSameAppRoutePopstateTarget(href)) {
			notifyAppRouterTransitionStart(href, "traverse");
			historyController.commitTraversalIndexFromHistoryState(event.state);
			restorePopstateScrollPosition(event.state);
			return;
		}
		const snapshotNavigationId = browserNavigationController.beginNavigation();
		if (restoreHistoryStateSnapshot(event.state, snapshotNavigationId, () => {
			abortSupersededNavigation();
			notifyAppRouterTransitionStart(href, "traverse");
		})) {
			window.__VINEXT_RSC_PENDING__ = null;
			restoreSynchronousPopstateScrollPosition({
				getActiveNavigationId: () => browserNavigationController.getActiveNavigationId(),
				isCurrentNavigation: (navId) => browserNavigationController.isCurrentNavigation(navId),
				markScrollRestoreConsumed: (navId) => {
					synchronousPopstateScrollRestoreNavigationId = navId;
				},
				restorePopstateScrollPosition
			}, event.state);
			browserNavigationController.finalizeNavigation(snapshotNavigationId, null);
			return;
		}
		browserNavigationController.finalizeNavigation(snapshotNavigationId, null);
		handlePopstate(event);
	});
}
if (typeof document !== "undefined") {
	installWindowNext({
		appDir: true,
		router: appRouterInstance
	});
	window.addEventListener("pagehide", () => {
		isPageUnloading = true;
	});
	window.addEventListener("pageshow", (event) => {
		isPageUnloading = false;
		if (event.persisted) mpaNavigationScheduler.reset();
	});
	main();
}
//#endregion
//#region \0virtual:vinext-app-browser-entry
window.__VINEXT_LINK_PREFETCH_ROUTES__ = [
	{
		"canPrefetchLoadingShell": false,
		"patternParts": [],
		"isDynamic": false
	},
	{
		"canPrefetchLoadingShell": false,
		"documentOnly": true,
		"patternParts": [
			"api",
			"runtime",
			"ensure-bridge"
		],
		"isDynamic": false
	},
	{
		"canPrefetchLoadingShell": false,
		"patternParts": ["chat"],
		"isDynamic": false
	}
];
window.__VINEXT_PAGES_LINK_PREFETCH_ROUTES__ = [];
window.__VINEXT_CLIENT_REWRITES__ = {
	"beforeFiles": [],
	"afterFiles": [],
	"fallback": []
};
registerNavigationRuntimeBootstrap({ routeManifest: {
	graphVersion: "graph:5162cc5a06ea8607bbabea04d31c58955cbf84a9af5297011f754d0d4112f963",
	segmentGraph: {
		routes: new Map([
			["route:/", {
				"id": "route:/",
				"pattern": "/",
				"patternParts": [],
				"isDynamic": false,
				"paramNames": [],
				"rootParamNames": [],
				"rootBoundaryId": "root-boundary:/",
				"pageId": "page:/",
				"routeHandlerId": null,
				"layoutIds": ["layout:/"],
				"templateIds": [],
				"slotIds": []
			}],
			["route:/api/runtime/ensure-bridge", {
				"id": "route:/api/runtime/ensure-bridge",
				"pattern": "/api/runtime/ensure-bridge",
				"patternParts": [
					"api",
					"runtime",
					"ensure-bridge"
				],
				"isDynamic": false,
				"paramNames": [],
				"rootParamNames": [],
				"rootBoundaryId": "root-boundary:/",
				"pageId": null,
				"routeHandlerId": "route-handler:/api/runtime/ensure-bridge",
				"layoutIds": ["layout:/"],
				"templateIds": [],
				"slotIds": []
			}],
			["route:/chat", {
				"id": "route:/chat",
				"pattern": "/chat",
				"patternParts": ["chat"],
				"isDynamic": false,
				"paramNames": [],
				"rootParamNames": [],
				"rootBoundaryId": "root-boundary:/",
				"pageId": "page:/chat",
				"routeHandlerId": null,
				"layoutIds": ["layout:/"],
				"templateIds": [],
				"slotIds": []
			}]
		]),
		pages: new Map([["page:/", {
			"id": "page:/",
			"routeId": "route:/",
			"pattern": "/"
		}], ["page:/chat", {
			"id": "page:/chat",
			"routeId": "route:/chat",
			"pattern": "/chat"
		}]]),
		routeHandlers: new Map([["route-handler:/api/runtime/ensure-bridge", {
			"id": "route-handler:/api/runtime/ensure-bridge",
			"routeId": "route:/api/runtime/ensure-bridge",
			"pattern": "/api/runtime/ensure-bridge"
		}]]),
		layouts: new Map([["layout:/", {
			"id": "layout:/",
			"treePath": "/",
			"patternParts": [],
			"paramNames": [],
			"rootBoundaryId": "root-boundary:/"
		}]]),
		templates: /* @__PURE__ */ new Map([]),
		slots: /* @__PURE__ */ new Map([]),
		defaults: /* @__PURE__ */ new Map([]),
		slotBindings: /* @__PURE__ */ new Map([]),
		interceptions: /* @__PURE__ */ new Map([]),
		interceptionsBySlotId: /* @__PURE__ */ new Map([]),
		boundaries: /* @__PURE__ */ new Map([]),
		rootBoundaries: new Map([["root-boundary:/", {
			"id": "root-boundary:/",
			"layoutId": "layout:/",
			"treePath": "/"
		}]])
	}
} });
//#endregion
export { getLayoutSegmentContext as i, matchRouteWithTrie as n, stripBasePath as r, createRouteTrieCache as t };
