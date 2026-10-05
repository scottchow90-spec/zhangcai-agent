import { createRequire } from "node:module";
import __vite_rsc_assets_manifest from "./__vite_rsc_assets_manifest.js";
import * as __viteRscAsyncHooks from "node:async_hooks";
import { AsyncLocalStorage } from "node:async_hooks";
import * as React$1 from "react";
import React, { Fragment, createElement, isValidElement, use } from "react";
import { Fragment as Fragment$1, jsx, jsxs } from "react/jsx-runtime";
import { renderToReadableStream, renderToStaticMarkup } from "react-dom/server.edge";
import * as ReactDOM from "react-dom";
import { preinitModule } from "react-dom";
import pagesClientAssets from "./vinext-client-assets.js";
//#region \0rolldown/runtime.js
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __commonJSMin = (cb, mod) => () => (mod || (cb((mod = { exports: {} }).exports, mod), cb = null), mod.exports);
var __exportAll = (all, no_symbols) => {
	let target = {};
	for (var name in all) __defProp(target, name, {
		get: all[name],
		enumerable: true
	});
	if (!no_symbols) __defProp(target, Symbol.toStringTag, { value: "Module" });
	return target;
};
var __copyProps = (to, from, except, desc) => {
	if (from && typeof from === "object" || typeof from === "function") for (var keys = __getOwnPropNames(from), i = 0, n = keys.length, key; i < n; i++) {
		key = keys[i];
		if (!__hasOwnProp.call(to, key) && key !== except) __defProp(to, key, {
			get: ((k) => from[k]).bind(null, key),
			enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable
		});
	}
	return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", {
	value: mod,
	enumerable: true
}) : target, mod));
var __require = /* @__PURE__ */ createRequire(import.meta.url);
//#endregion
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
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/http-error-responses.js
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
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/normalize-path.js
function isInterceptionMatchedUrlPath(value) {
	return value.startsWith("/") && !value.startsWith("//") && !value.includes("?") && !value.includes("#") && !value.includes("\0");
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/compare.js
var compareStrings = (left, right) => {
	if (left < right) return -1;
	if (left > right) return 1;
	return 0;
};
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/record.js
function isUnknownRecord(value) {
	return value !== null && typeof value === "object" && !Array.isArray(value);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/artifact-compatibility.js
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
	if (isValidElement(value)) return false;
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
var _g$3 = globalThis;
/**
* Every ALS handed out by `getOrCreateAls`, so `runOutsideRequestScopes` can
* exit all of them without an enumeration that goes stale as shims are added.
* Shares the `globalThis` slot for the same cross-module-instance reason.
*/
var _REGISTRY_KEY = Symbol.for("vinext.als.registry");
var _registry = _g$3[_REGISTRY_KEY] ??= /* @__PURE__ */ new Set();
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
	const als = _g$3[sym] ??= typeof AsyncLocalStorage === "function" ? new AsyncLocalStorage() : new NoopAsyncLocalStorage();
	_registry.add(als);
	return als;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/ppr-fallback-shell.js
var pprFallbackShellAls = getOrCreateAls("vinext.pprFallbackShell.als");
var pprFallbackShellCacheTaskStackAls = getOrCreateAls("vinext.pprFallbackShell.cacheTaskStack.als");
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
function markPprFallbackShellDynamicBoundaryForState(state) {
	state.hasDynamicBoundary = true;
	for (const task of pprFallbackShellCacheTaskStackAls.getStore() ?? []) ignoreCacheTask(state, task);
	scheduleCacheReadyIfSettled(state);
}
function markPprFallbackShellDynamicBoundary() {
	const state = getPprFallbackShellState();
	if (state === null || state.fallbackParamNames.size === 0) return;
	markPprFallbackShellDynamicBoundaryForState(state);
}
function isPprFallbackShellAbortError(error) {
	if (typeof DOMException !== "undefined" && error instanceof DOMException && error.name === "AbortError") return true;
	return error instanceof Error && error.name === "HangingPromiseRejectionError";
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
	if (typeof React$1.createContext !== "function") return null;
	const globalState = globalThis;
	if (!globalState[key]) globalState[key] = React$1.createContext(defaultValue);
	return globalState[key] ?? null;
}
var AppRouterContext = getOrCreateContext(APP_ROUTER_CONTEXT_KEY, null);
getOrCreateContext(GLOBAL_LAYOUT_ROUTER_CONTEXT_KEY, null);
getOrCreateContext(LAYOUT_ROUTER_CONTEXT_KEY, null);
getOrCreateContext(MISSING_SLOT_CONTEXT_KEY, /* @__PURE__ */ new Set());
getOrCreateContext(TEMPLATE_CONTEXT_KEY, null);
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/utils/deployment-id.js
function appendDeploymentIdQuery(value, deploymentId = void 0) {
	if (!deploymentId) return value;
	const hashIndex = value.indexOf("#");
	const url = hashIndex === -1 ? value : value.slice(0, hashIndex);
	const fragment = hashIndex === -1 ? "" : value.slice(hashIndex);
	if (new URL(url, "http://vinext.local").searchParams.has("dpl")) return value;
	return `${url}${url.includes("?") ? "&" : "?"}dpl=${deploymentId}${fragment}`;
}
function appendAssetDeploymentIdQuery(value, deploymentId = void 0) {
	if (!new URL(value, "http://vinext.local").pathname.includes("/_next/static/")) return value;
	return appendDeploymentIdQuery(value, deploymentId);
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/script-nonce-context.js
var ScriptNonceContext = typeof React.createContext === "function" ? React.createContext(void 0) : null;
function ScriptNonceProvider(props) {
	if (!ScriptNonceContext) return React.createElement(React.Fragment, null, props.children);
	return React.createElement(ScriptNonceContext.Provider, { value: props.nonce }, props.children);
}
function withScriptNonce(element, nonce) {
	if (!nonce || !ScriptNonceContext) return element;
	return React.createElement(ScriptNonceProvider, { nonce }, element);
}
function createScriptNonceHook(context) {
	if (!context || typeof React.useContext !== "function") return function useScriptNonceFromContext() {};
	return function useScriptNonceFromContext() {
		return React.useContext(context);
	};
}
createScriptNonceHook(ScriptNonceContext);
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
var HTML_SPACE_RE = /[\t\n\f\r ]+/;
function htmlTokenListContains(value, token) {
	if (value === null) return false;
	return value.split(HTML_SPACE_RE).some((part) => part.length > 0 && part.toLowerCase() === token.toLowerCase());
}
function createNonceAttribute(nonce) {
	if (!nonce) return "";
	return ` nonce="${escapeHtmlAttr(nonce)}"`;
}
function createInlineScriptTag(content, nonce) {
	return `<script${createNonceAttribute(nonce)}>${content}<\/script>`;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/client-trace-metadata.js
/**
* Client trace metadata renderer.
*
* When `experimental.clientTraceMetadata` is configured in `next.config`,
* vinext emits `<meta name="..." content="...">` tags in the SSR HTML head
* for each configured key. The values are sourced from the active
* OpenTelemetry context via the registered propagator.
*
* This mirrors Next.js' implementation:
*  - packages/next/src/server/lib/trace/utils.ts (getTracedMetadata)
*  - packages/next/src/server/app-render/make-get-server-inserted-html.tsx (traceMetaTags)
*
* OpenTelemetry is an optional peer — we resolve `@opentelemetry/api` at
* runtime and silently no-op when it is not installed. This matches user
* expectations: apps that don't configure OTel get no meta tags, and apps
* that do get the filtered subset they asked for in `clientTraceMetadata`.
*/
var carrierSetter = { set(carrier, key, value) {
	if (typeof key !== "string" || typeof value !== "string") return;
	carrier.push({
		key,
		value
	});
} };
var OPEN_TELEMETRY_API_SYMBOL = Symbol.for("opentelemetry.js.api.1");
var OPEN_TELEMETRY_SPAN_SYMBOL = Symbol.for("OpenTelemetry Context Key SPAN");
function getRegisteredOpenTelemetryTraceData() {
	let metadataSpan = null;
	try {
		const registry = globalThis[OPEN_TELEMETRY_API_SYMBOL];
		if (!registry?.context || !registry.propagation) return null;
		const contextApi = registry.context;
		const propagation = registry.propagation;
		const activeContext = contextApi.active();
		metadataSpan = activeContext.getValue(OPEN_TELEMETRY_SPAN_SYMBOL) !== void 0 ? null : registry.trace?.getTracer("vinext").startSpan("vinext.clientTraceMetadata", void 0, activeContext) ?? null;
		const context = metadataSpan ? activeContext.setValue(OPEN_TELEMETRY_SPAN_SYMBOL, metadataSpan) : activeContext;
		const entries = [];
		contextApi.with(context, () => {
			propagation.inject(context, entries, carrierSetter);
		});
		return entries;
	} catch {
		return [];
	} finally {
		metadataSpan?.end();
	}
}
function getOpenTelemetryTraceData() {
	const registeredEntries = getRegisteredOpenTelemetryTraceData();
	if (registeredEntries) return registeredEntries;
	let api;
	try {
		const req = globalThis.require;
		if (typeof req === "function") api = req("@opentelemetry/api");
	} catch {
		return [];
	}
	if (!api) return [];
	try {
		const activeContext = api.context.active();
		const entries = [];
		api.propagation.inject(activeContext, entries, carrierSetter);
		return entries;
	} catch {
		return [];
	}
}
/**
* Filter an entry list against the configured `clientTraceMetadata` allow-list.
* Returns `undefined` when the allow-list is unset so callers can skip
* rendering altogether.
*/
function filterClientTraceMetadata(entries, allowList) {
	if (!allowList || allowList.length === 0) return void 0;
	const allowSet = new Set(allowList);
	return entries.filter(({ key }) => allowSet.has(key));
}
/**
* Render the filtered entries as a sequence of self-closing `<meta>` tags.
* Names and values are HTML-attribute escaped. Returns an empty string when
* `entries` is empty or undefined so callers can append unconditionally.
*/
function renderClientTraceMetadataTags(entries) {
	if (!entries || entries.length === 0) return "";
	let html = "";
	for (const { key, value } of entries) html += `<meta name="${escapeHtmlAttr(key)}" content="${escapeHtmlAttr(value)}"/>`;
	return html;
}
/**
* Convenience helper: read OTel propagation data, filter against the
* configured allow-list, and render the resulting `<meta>` tags. Returns an
* empty string when the allow-list is unset, OTel is not installed, or no
* matching keys were emitted by the propagator.
*
* Safe to call unconditionally on every SSR render — when nothing is
* configured/active this is a few `try/catch`-bounded operations and returns
* `""`.
*/
function getClientTraceMetadataHTML(allowList) {
	if (!allowList || allowList.length === 0) return "";
	if (typeof process !== "undefined" && process.env.VINEXT_PRERENDER === "1") return "";
	return renderClientTraceMetadataTags(filterClientTraceMetadata(getOpenTelemetryTraceData(), allowList));
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/navigation-context-state.js
var LAYOUT_SEGMENT_CONTEXT_KEY = Symbol.for("vinext.layoutSegmentContext");
var SERVER_INSERTED_HTML_CONTEXT_KEY = Symbol.for("vinext.serverInsertedHTMLContext");
var BFCACHE_ID_MAP_CONTEXT_KEY = Symbol.for("vinext.bfcacheIdMapContext");
var BFCACHE_SEGMENT_ID_CONTEXT_KEY = Symbol.for("vinext.bfcacheSegmentIdContext");
var NAVIGATION_FALLBACK_STATE_KEY = Symbol.for("vinext.navigation.fallback");
function createContextIfAvailable(defaultValue) {
	return typeof React$1.createContext === "function" ? React$1.createContext(defaultValue) : null;
}
function getServerInsertedHTMLContext() {
	const globalState = globalThis;
	if (!globalState[SERVER_INSERTED_HTML_CONTEXT_KEY]) globalState[SERVER_INSERTED_HTML_CONTEXT_KEY] = createContextIfAvailable(null);
	return globalState[SERVER_INSERTED_HTML_CONTEXT_KEY] ?? null;
}
var ServerInsertedHTMLContext = getServerInsertedHTMLContext();
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
var getServerContext = () => {
	return getGlobalAccessors()?.getServerContext() ?? getFallbackState().serverContext;
};
var setServerContext = (context) => {
	const accessors = getGlobalAccessors();
	if (accessors) accessors.setServerContext(context);
	else getFallbackState().serverContext = context;
};
var getInsertedHTMLCallbacks = () => getGlobalAccessors()?.getInsertedHTMLCallbacks() ?? getFallbackState().serverInsertedHTMLCallbacks;
var clearInsertedHTMLCallbacks = () => {
	const accessors = getGlobalAccessors();
	if (accessors) accessors.clearInsertedHTMLCallbacks();
	else getFallbackState().serverInsertedHTMLCallbacks = [];
};
/**
* Register request-scoped accessors supplied by navigation-state.ts.
* The global accessor key also bridges separate Vite module instances.
*/
function _registerStateAccessors(accessors) {
	getServerContext = accessors.getServerContext;
	setServerContext = accessors.setServerContext;
	getInsertedHTMLCallbacks = accessors.getInsertedHTMLCallbacks;
	clearInsertedHTMLCallbacks = accessors.clearInsertedHTMLCallbacks;
}
function getNavigationContext() {
	return getServerContext();
}
function setNavigationContext(context) {
	setServerContext(context);
}
function registerServerInsertedHTMLCallback(callback) {
	getInsertedHTMLCallbacks().push(callback);
}
function renderInsertedHTMLCallbacks(clear) {
	const callbacks = getInsertedHTMLCallbacks();
	const results = [];
	for (const callback of callbacks) try {
		const result = callback();
		if (result != null) results.push(result);
	} catch {}
	if (clear) callbacks.length = 0;
	return results;
}
function renderServerInsertedHTML() {
	return renderInsertedHTMLCallbacks(false);
}
function clearServerInsertedHTML() {
	clearInsertedHTMLCallbacks();
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
	return /* @__PURE__ */ jsx("svg", {
		width: "32",
		height: "32",
		viewBox: "-0.2 -1.5 32 32",
		fill: "none",
		style: errorStyles.icon,
		children: /* @__PURE__ */ jsx("path", {
			d: "M16.9328 0C18.0839 0.000116771 19.1334 0.658832 19.634 1.69531L31.4299 26.1309C32.0708 27.4588 31.1036 28.9999 29.6291 29H2.00215C0.527541 29 -0.439628 27.4588 0.201371 26.1309L11.9973 1.69531C12.4979 0.658823 13.5474 7.75066e-05 14.6984 0H16.9328ZM3.59493 26H28.0363L16.9328 3H14.6984L3.59493 26ZM15.8156 19C16.9202 19.0001 17.8156 19.8955 17.8156 21C17.8156 22.1045 16.9202 22.9999 15.8156 23C14.7111 23 13.8156 22.1046 13.8156 21C13.8156 19.8954 14.7111 19 15.8156 19ZM17.3156 16.5H14.3156V8.5H17.3156V16.5Z",
			fill: "var(--next-error-title)"
		})
	});
}
function handleBackClick() {}
function DefaultGlobalError({ error }) {
	const digest = error?.digest;
	const isServerError = !!digest;
	const message = isServerError ? "A server error occurred. Reload to try again." : "Reload to try again, or go back.";
	return /* @__PURE__ */ jsxs("html", {
		id: "__next_error__",
		children: [/* @__PURE__ */ jsx("head", { children: /* @__PURE__ */ jsx("style", { dangerouslySetInnerHTML: { __html: errorThemeCss } }) }), /* @__PURE__ */ jsxs("body", { children: [/* @__PURE__ */ jsx("div", {
			style: errorStyles.container,
			children: /* @__PURE__ */ jsxs("div", {
				style: errorStyles.card,
				children: [
					/* @__PURE__ */ jsx(WarningIcon, {}),
					/* @__PURE__ */ jsx("h1", {
						style: errorStyles.title,
						children: "This page couldn’t load"
					}),
					/* @__PURE__ */ jsx("p", {
						style: errorStyles.message,
						children: message
					}),
					/* @__PURE__ */ jsxs("div", {
						style: errorStyles.buttonGroup,
						children: [/* @__PURE__ */ jsx("form", {
							style: errorStyles.form,
							children: /* @__PURE__ */ jsx("button", {
								type: "submit",
								style: errorStyles.button,
								children: "Reload"
							})
						}), !isServerError && /* @__PURE__ */ jsx("button", {
							type: "button",
							style: errorStyles.buttonSecondary,
							onClick: handleBackClick,
							children: "Back"
						})]
					})
				]
			})
		}), digest && /* @__PURE__ */ jsxs("p", {
			style: errorStyles.digestFooter,
			children: ["ERROR ", digest]
		})] })]
	});
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
var ElementsContext = React$1.createContext(EMPTY_ELEMENTS);
var ChildrenContext = React$1.createContext(null);
var ParallelSlotsContext = React$1.createContext(null);
var BfcacheIdMapContext$1 = getBfcacheIdMapContext();
var BfcacheSegmentIdContext = getBfcacheSegmentIdContext();
var EMPTY_BFCACHE_STATE_KEYS = Object.freeze({});
var MAX_BFCACHE_SLOT_ENTRIES_WITH_CACHE_COMPONENTS = 3;
var MAX_BFCACHE_SLOT_ENTRIES_WITHOUT_CACHE_COMPONENTS = 1;
var BfcacheIdentityMapContext = React$1.createContext(EMPTY_BFCACHE_STATE_KEYS);
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
	return /* @__PURE__ */ jsx(BfcacheIdentityMapContext.Provider, {
		value: entry.stateKeyMap ?? fallbackStateKeyMap,
		children: /* @__PURE__ */ jsx(ElementsContext.Provider, {
			value: entry.elements ?? fallbackElements,
			children: /* @__PURE__ */ jsx(SegmentContext.Provider, {
				value: entry.segmentId ?? fallbackSegmentId,
				children: entry.content
			})
		})
	});
}
function useBfcacheSlotEntries(activeEntry) {
	const snapshotsByStateKey = React$1.useRef(/* @__PURE__ */ new Map());
	const [entryOrder, setEntryOrder] = React$1.useState(() => [activeEntry.stateKey]);
	const staged = stageBfcacheSlotEntryForRender(snapshotsByStateKey.current, entryOrder, activeEntry);
	const nextOrder = staged.order;
	const orderChanged = !haveSameBfcacheSlotEntryOrder(entryOrder, nextOrder);
	React$1.useLayoutEffect(() => {
		snapshotsByStateKey.current = staged.snapshots;
	}, [staged.snapshots]);
	if (orderChanged) setEntryOrder(nextOrder);
	return staged.entries;
}
function BfcacheActivitySlotBoundary({ activeStateKey, content, elements, id, SegmentContext, stateKeyMap }) {
	return /* @__PURE__ */ jsx(Fragment$1, { children: useBfcacheSlotEntries({
		content,
		elements,
		segmentId: id,
		stateKey: activeStateKey,
		stateKeyMap
	}).map((entry) => /* @__PURE__ */ jsx(React$1.Activity, {
		mode: entry.stateKey === activeStateKey ? "visible" : "hidden",
		children: /* @__PURE__ */ jsx(BfcacheEntryProviders, {
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
	const elements = React$1.useContext(ElementsContext);
	const identityMap = React$1.useContext(BfcacheIdentityMapContext);
	const activeStateKey = resolveBfcacheSegmentStateKey(id, identityMap, React$1.useContext(BfcacheIdMapContext$1));
	if (!BfcacheSegmentIdContext || activeStateKey === void 0) return /* @__PURE__ */ jsx(React$1.Fragment, { children }, stateKey);
	if (!isCacheComponentsEnabled()) return /* @__PURE__ */ jsx(BfcacheSegmentIdContext.Provider, {
		value: id,
		children
	}, activeStateKey);
	return /* @__PURE__ */ jsx(BfcacheActivitySlotBoundary, {
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
	const elements = React$1.useContext(ElementsContext);
	const identityMap = React$1.useContext(BfcacheIdentityMapContext);
	const activeStateKey = resolveBfcacheSegmentStateKey(id, identityMap, React$1.useContext(BfcacheIdMapContext$1));
	if (!SegmentContext) return /* @__PURE__ */ jsx(Fragment$1, { children: content });
	if (activeStateKey === void 0) return /* @__PURE__ */ jsx(SegmentContext.Provider, {
		value: id,
		children: content
	});
	if (!isCacheComponentsEnabled()) return /* @__PURE__ */ jsx(SegmentContext.Provider, {
		value: id,
		children: content
	}, getNonCacheComponentsSegmentKey(id, activeStateKey));
	return /* @__PURE__ */ jsx(BfcacheActivitySlotBoundary, {
		activeStateKey,
		content,
		elements,
		id,
		SegmentContext,
		stateKeyMap: identityMap
	});
}
function Slot({ id, children, parallelSlots }) {
	const elements = React$1.useContext(ElementsContext);
	if (!Object.hasOwn(elements, id)) return null;
	const element = elements[id];
	if (isTransportMetadataValue(id, element)) return null;
	if (element === UNMATCHED_SLOT) notFound();
	if (element === null) return null;
	const content = /* @__PURE__ */ jsx(ParallelSlotsContext.Provider, {
		value: parallelSlots ?? null,
		children: /* @__PURE__ */ jsx(ChildrenContext.Provider, {
			value: children ?? null,
			children: element
		})
	});
	return BfcacheIdMapContext$1 && BfcacheSegmentIdContext ? /* @__PURE__ */ jsx(BfcacheSlotBoundary, {
		id,
		content
	}) : content;
}
function Children() {
	return React$1.useContext(ChildrenContext);
}
function ParallelSlot({ name }) {
	return React$1.useContext(ParallelSlotsContext)?.[name] ?? null;
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
function createSsrErrorMetaRenderer(options = {}) {
	const capturedErrors = [];
	let flushedUntil = 0;
	return {
		capture(error) {
			capturedErrors.push(error);
		},
		flush() {
			if (flushedUntil >= capturedErrors.length) return "";
			const html = renderSsrErrorMetaTags(capturedErrors.slice(flushedUntil), options);
			flushedUntil = capturedErrors.length;
			return html;
		}
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-rsc-embedded-chunks.js
var BASE64_CHUNK_SIZE = 32768;
new TextEncoder();
function bytesToBase64(bytes) {
	let binary = "";
	for (let offset = 0; offset < bytes.byteLength; offset += BASE64_CHUNK_SIZE) binary += String.fromCharCode(...bytes.subarray(offset, offset + BASE64_CHUNK_SIZE));
	return btoa(binary);
}
function concatUint8Arrays(chunks) {
	let totalLength = 0;
	for (const chunk of chunks) totalLength += chunk.byteLength;
	const result = new Uint8Array(totalLength);
	let offset = 0;
	for (const chunk of chunks) {
		result.set(chunk, offset);
		offset += chunk.byteLength;
	}
	return result;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/client/navigation-runtime.js
var NAVIGATION_RUNTIME_SYMBOL_DESCRIPTION = "vinext.navigationRuntime";
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-ssr-stream.js
function waitAtLeastOneReactRenderTask() {
	return new Promise((resolve) => setTimeout(resolve, 0));
}
var NAVIGATION_RUNTIME_REFERENCE = `self[Symbol.for(${safeJsonStringify(NAVIGATION_RUNTIME_SYMBOL_DESCRIPTION)})]`;
function navigationRuntimeRscBootstrapExpression() {
	return `((${NAVIGATION_RUNTIME_REFERENCE}??={bootstrap:{routeManifest:null},functions:{}}).bootstrap.rsc??={rsc:[]})`;
}
function createNavigationRuntimeRscMetadataScript(params, nav, dynamicStaleTimeSeconds) {
	return "Object.assign(" + navigationRuntimeRscBootstrapExpression() + ",{params:" + safeJsonStringify(params) + ",nav:" + safeJsonStringify(nav) + (dynamicStaleTimeSeconds === void 0 ? "" : ",dynamicStaleTimeSeconds:" + safeJsonStringify(dynamicStaleTimeSeconds)) + "})";
}
function createNavigationRuntimeRscChunkScript(chunk) {
	return navigationRuntimeRscBootstrapExpression() + ".rsc.push(" + safeJsonStringify(chunk) + ")";
}
function createNavigationRuntimeRscDoneScript(metadata) {
	const bootstrap = navigationRuntimeRscBootstrapExpression();
	return (metadata === void 0 ? "" : "Object.assign(" + bootstrap + "," + safeJsonStringify({
		initialCacheKind: metadata.kind,
		...metadata.dynamicStaleTimeSeconds === void 0 ? {} : { dynamicStaleTimeSeconds: metadata.dynamicStaleTimeSeconds },
		...metadata.staleTimeSeconds === void 0 ? {} : { staleTimeSeconds: metadata.staleTimeSeconds }
	}) + ");") + bootstrap + ".done=true";
}
/**
* Create a helper that progressively embeds RSC chunks as inline <script> tags.
* The browser entry turns the embedded chunks back into Uint8Array data.
*/
function createRscEmbedTransform(embedStream, scriptNonce, getInitialNavigationCacheMetadata) {
	const reader = embedStream.getReader();
	let pendingChunks = [];
	const rawChunks = [];
	let reading = false;
	async function pumpReader() {
		if (reading) return;
		reading = true;
		try {
			while (true) {
				const result = await reader.read();
				if (result.done) break;
				rawChunks.push(result.value);
				try {
					const text = new TextDecoder("utf-8", { fatal: true }).decode(result.value);
					pendingChunks.push(text);
				} catch {
					pendingChunks.push([3, bytesToBase64(result.value)]);
				}
			}
		} catch (error) {
			throw error;
		} finally {
			reading = false;
		}
	}
	const pumpPromise = pumpReader();
	return {
		flush() {
			if (pendingChunks.length === 0) return "";
			const chunks = pendingChunks;
			pendingChunks = [];
			let scripts = "";
			for (const chunk of chunks) scripts += createInlineScriptTag(createNavigationRuntimeRscChunkScript(chunk), scriptNonce);
			return scripts;
		},
		async finalize() {
			await pumpPromise;
			let scripts = this.flush();
			scripts += createInlineScriptTag(createNavigationRuntimeRscDoneScript(getInitialNavigationCacheMetadata?.()), scriptNonce);
			return scripts;
		},
		async getRawBuffer() {
			await pumpPromise;
			const buffer = concatUint8Arrays(rawChunks);
			rawChunks.length = 0;
			return buffer.buffer;
		}
	};
}
/**
* Fix invalid preload "as" values in server-rendered HTML.
* React Fizz emits <link rel="preload" as="stylesheet"> for CSS, but the
* HTML spec requires as="style" for <link rel="preload">.
*/
function fixPreloadAs(html) {
	return html.replace(/<link(?=[^>]*\srel="preload")[^>]*>/g, (tag) => tag.replace(" as=\"stylesheet\"", " as=\"style\""));
}
var LINK_TAG_RE = /<link\b[^>]*>/gi;
var HTML_REWRITE_EXCLUDED_REGION_RE = /<!--[\s\S]*?-->|<(script|style|textarea|title)\b[^>]*>[\s\S]*?<\/\1\s*>/gi;
var HTML_REWRITE_EXCLUDED_REGION_START_RE = /<!--|<(script|style|textarea|title)\b[^>]*>/gi;
var CLOSE_TAG_RES = {
	script: /<\/script\s*>/i,
	style: /<\/style\s*>/i,
	textarea: /<\/textarea\s*>/i,
	title: /<\/title\s*>/i
};
function getHtmlAttribute(tag, name) {
	const attrRe = /\s([^\s"'=<>`]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?/g;
	let match;
	while ((match = attrRe.exec(tag)) !== null) {
		if (match[1]?.toLowerCase() !== name.toLowerCase()) continue;
		return match[2] ?? match[3] ?? match[4] ?? "";
	}
	return null;
}
function htmlAttributeHasToken(tag, name, token) {
	return htmlTokenListContains(getHtmlAttribute(tag, name), token);
}
function getInlineCss(manifest, href) {
	if (Object.prototype.hasOwnProperty.call(manifest, href)) return manifest[href] ?? "";
	try {
		const pathname = new URL(href).pathname;
		if (Object.prototype.hasOwnProperty.call(manifest, pathname)) return manifest[pathname] ?? "";
	} catch {}
	return null;
}
var TRAILING_LINK_OPEN_RE = /<link/gi;
function splitTrailingIncompleteLinkTag(html) {
	TRAILING_LINK_OPEN_RE.lastIndex = 0;
	let lastIndex = -1;
	let match;
	while ((match = TRAILING_LINK_OPEN_RE.exec(html)) !== null) lastIndex = match.index;
	if (lastIndex === -1) return {
		complete: html,
		trailing: ""
	};
	if (html.indexOf(">", lastIndex) !== -1) return {
		complete: html,
		trailing: ""
	};
	return {
		complete: html.slice(0, lastIndex),
		trailing: html.slice(lastIndex)
	};
}
function findTrailingOpenHtmlRewriteExcludedRegionStart(html) {
	let match;
	HTML_REWRITE_EXCLUDED_REGION_START_RE.lastIndex = 0;
	while ((match = HTML_REWRITE_EXCLUDED_REGION_START_RE.exec(html)) !== null) {
		const start = match.index;
		if (match[0] === "<!--") {
			const close = html.indexOf("-->", HTML_REWRITE_EXCLUDED_REGION_START_RE.lastIndex);
			if (close === -1) return start;
			HTML_REWRITE_EXCLUDED_REGION_START_RE.lastIndex = close + 3;
			continue;
		}
		const tagName = match[1]?.toLowerCase();
		if (!tagName) continue;
		const closeTagRe = CLOSE_TAG_RES[tagName];
		if (!closeTagRe) continue;
		const close = closeTagRe.exec(html.slice(HTML_REWRITE_EXCLUDED_REGION_START_RE.lastIndex));
		if (!close) return start;
		HTML_REWRITE_EXCLUDED_REGION_START_RE.lastIndex += close.index + close[0].length;
	}
	return null;
}
function splitTrailingInlineCssRewriteBoundary(html) {
	const linkSplit = splitTrailingIncompleteLinkTag(html);
	const incompleteLinkStart = linkSplit.trailing ? linkSplit.complete.length : null;
	const openRegionStart = findTrailingOpenHtmlRewriteExcludedRegionStart(html);
	const trailingStart = incompleteLinkStart === null ? openRegionStart : openRegionStart === null ? incompleteLinkStart : Math.min(incompleteLinkStart, openRegionStart);
	if (trailingStart === null) return {
		complete: html,
		trailing: ""
	};
	return {
		complete: html.slice(0, trailingStart),
		trailing: html.slice(trailingStart)
	};
}
function escapeStyleText(css) {
	return css.replace(/<\/style/gi, "<\\/style");
}
var CSS_PREPEND_UNSAFE_PREAMBLE_RE = /^\uFEFF?(?:\s|\/\*[\s\S]*?\*\/)*@(charset|import|layer|namespace)\b/i;
function canPrependCss(css) {
	return !CSS_PREPEND_UNSAFE_PREAMBLE_RE.test(css);
}
function replaceLinkTags(html, replaceLinkTag) {
	LINK_TAG_RE.lastIndex = 0;
	return html.replace(LINK_TAG_RE, replaceLinkTag);
}
function replaceLinkTagsOutsideRawText(html, replaceLinkTag) {
	let rewritten = "";
	let cursor = 0;
	let match;
	HTML_REWRITE_EXCLUDED_REGION_RE.lastIndex = 0;
	while ((match = HTML_REWRITE_EXCLUDED_REGION_RE.exec(html)) !== null) {
		rewritten += replaceLinkTags(html.slice(cursor, match.index), replaceLinkTag);
		rewritten += match[0];
		cursor = match.index + match[0].length;
	}
	const tail = html.slice(cursor);
	const openRegionStart = findTrailingOpenHtmlRewriteExcludedRegionStart(tail);
	if (openRegionStart === null) return rewritten + replaceLinkTags(tail, replaceLinkTag);
	return rewritten + replaceLinkTags(tail.slice(0, openRegionStart), replaceLinkTag) + tail.slice(openRegionStart);
}
function rewriteInlineCssStylesheetLinks(html, inlineCssManifest, prependCss, ssrScriptNonce) {
	if (!inlineCssManifest || Object.keys(inlineCssManifest).length === 0) return {
		html,
		consumedPrependCss: false
	};
	let consumedPrependCss = false;
	return {
		html: replaceLinkTagsOutsideRawText(html, (tag) => {
			if (!htmlAttributeHasToken(tag, "rel", "stylesheet")) return tag;
			const href = getHtmlAttribute(tag, "href");
			const precedence = getHtmlAttribute(tag, "data-precedence") ?? getHtmlAttribute(tag, "precedence");
			if (!href || !precedence) return tag;
			const css = getInlineCss(inlineCssManifest, href);
			if (css === null) return tag;
			const effectiveNonce = getHtmlAttribute(tag, "nonce") ?? ssrScriptNonce;
			const nonceAttr = effectiveNonce ? ` nonce="${escapeHtmlAttr(effectiveNonce)}"` : "";
			const cssPrefix = !consumedPrependCss && prependCss.length > 0 && canPrependCss(css) ? `${prependCss}\n` : "";
			consumedPrependCss ||= cssPrefix.length > 0;
			return `<style data-vinext-inline-css${nonceAttr} data-precedence="${escapeHtmlAttr(precedence)}" data-href="${escapeHtmlAttr(href)}">${escapeStyleText(cssPrefix + css)}</style>`;
		}),
		consumedPrependCss
	};
}
/**
* Match the `<head ...>` opening tag in a chunk. Matches both bare `<head>`
* and `<head class="foo">` shapes. Used to splice HTML immediately after the
* opening tag so injected content runs before any React-emitted resource
* hints (stylesheets, modulepreloads) that React Float hoists into `<head>`.
*/
var HEAD_OPEN_RE = /<head\b[^>]*>/;
/**
* Final closing tags of the streamed HTML document. We track this suffix
* separately so we can move it to the very end of the stream — trailing flight
* chunks and preinit scripts emitted by `rscEmbed.finalize()` are appended in
* `flush()`, which would otherwise land them after `</body></html>` and break
* any consumer that asserts the document terminates with a well-formed close.
*
* Ported from Next.js: packages/next/src/server/stream-utils/node-web-streams-helper.ts
* https://github.com/vercel/next.js/blob/canary/packages/next/src/server/stream-utils/node-web-streams-helper.ts
* (see `createMoveSuffixStream` and `CLOSE_TAG`)
*/
var DOCUMENT_CLOSE_SUFFIX = "</body></html>";
/**
* Create the tick-buffered HTML transform that injects RSC scripts between
* React Fizz flush cycles without corrupting split HTML chunks.
*
* Two insertion points are supported in tandem:
*
*  - `injectHTML` is emitted immediately before `</head>`. This is where the
*    bulk of vinext's head additions live (RSC navigation runtime metadata,
*    bootstrap modulepreload, server-inserted HTML, font preloads, etc.).
*  - `injectAfterHeadOpenHTML` is emitted immediately after the `<head ...>`
*    opening tag so the content runs before any React-emitted resource
*    hints. This is where inline `<Script strategy="beforeInteractive">`
*    captures land so the no-flash dark-mode pattern works.
*
* Fallback behaviour differs by insertion point:
*
*  - `injectHTML` is emitted at end-of-stream by the `flush` handler when no
*    chunk ever contained `</head>` — callers still see the payload on
*    highly fragmented streams (just at the end of the body rather than in
*    the head).
*  - `injectAfterHeadOpenHTML` is silently dropped when `<head ...>` is not
*    found in a discoverable chunk. Emitting it at end-of-stream would put
*    it after the document body, defeating the point — the splice has to
*    happen before resource hints to be useful, so the safer behaviour is
*    to no-op and let the user-rendered Script (in its source-order
*    position) ship as-is.
*/
function createTickBufferedTransform(rscEmbed, injectHTML = "", injectAfterHeadOpenHTML = "", inlineCssManifest, inlineCssPrependCss = "", inlineCssPrependFallbackHTML = "", inlineCssScriptNonce) {
	const decoder = new TextDecoder();
	const encoder = new TextEncoder();
	const insertsPerFlush = typeof injectHTML === "function";
	let injected = false;
	let preHeadInjected = false;
	let suffixStripped = false;
	let buffered = [];
	let pendingHtml = "";
	let timeoutId = null;
	const hasInlineCssManifest = inlineCssManifest !== void 0 && Object.keys(inlineCssManifest).length > 0;
	/**
	* Strip the first occurrence of `</body></html>` from `chunk` so it can be
	* re-emitted at the very end of the stream. Returns the rewritten chunk and
	* a flag indicating whether a suffix was found. If `suffixStripped` is
	* already true (i.e. an earlier chunk contained the suffix), this is a
	* no-op — additional matches in later chunks shouldn't happen in practice,
	* but we leave them alone to avoid corrupting unexpected output.
	*/
	const stripDocumentCloseSuffix = (chunk) => {
		if (suffixStripped) return chunk;
		const index = chunk.indexOf(DOCUMENT_CLOSE_SUFFIX);
		if (index === -1) return chunk;
		suffixStripped = true;
		return chunk.slice(0, index) + chunk.slice(index + 14);
	};
	const readInsertion = () => typeof injectHTML === "function" ? injectHTML() : injectHTML;
	const readPreHeadInsertion = () => typeof injectAfterHeadOpenHTML === "function" ? injectAfterHeadOpenHTML() : injectAfterHeadOpenHTML;
	const readInlineCssPrependFallback = () => {
		if (!inlineCssPrependCss || !inlineCssPrependFallbackHTML) return "";
		inlineCssPrependCss = "";
		return inlineCssPrependFallbackHTML;
	};
	const emitInsertion = (controller) => {
		const insertion = readInlineCssPrependFallback() + readInsertion();
		if (insertion) controller.enqueue(encoder.encode(insertion));
	};
	/**
	* Splice the pre-head insertion (typically captured beforeInteractive inline
	* scripts) immediately after the `<head ...>` opening tag. Returns the
	* rewritten chunk and a flag indicating whether the splice happened, so the
	* caller can mark `preHeadInjected` and stop scanning further chunks.
	*
	* NOTE: This is called only when `<head ...>` lies fully inside the current
	* tick-buffered batch. We deliberately avoid retaining arbitrary output until
	* a future chunk completes `<head ...>`, which would delay TTFB and complicate
	* the existing `</head>` injection path. In practice React Fizz emits the
	* opening shell as a single batch.
	*/
	const spliceAfterHeadOpen = (chunk) => {
		if (preHeadInjected) return {
			chunk,
			spliced: false
		};
		const insertion = readPreHeadInsertion();
		if (!insertion) return {
			chunk,
			spliced: false
		};
		const match = HEAD_OPEN_RE.exec(chunk);
		if (!match) return {
			chunk,
			spliced: false
		};
		const insertAt = match.index + match[0].length;
		return {
			chunk: chunk.slice(0, insertAt) + insertion + chunk.slice(insertAt),
			spliced: true
		};
	};
	const flushBuffered = (controller, final = false) => {
		if (buffered.length === 0 && !pendingHtml) return;
		const rawHtml = pendingHtml + buffered.join("");
		buffered = [];
		pendingHtml = "";
		const split = final || !hasInlineCssManifest ? {
			complete: rawHtml,
			trailing: ""
		} : splitTrailingInlineCssRewriteBoundary(rawHtml);
		if (split.trailing) pendingHtml = split.trailing;
		if (!split.complete) return;
		if (injected && insertsPerFlush) emitInsertion(controller);
		const preparedHtml = fixPreloadAs(split.complete);
		const inlineCssResult = hasInlineCssManifest ? rewriteInlineCssStylesheetLinks(preparedHtml, inlineCssManifest, inlineCssPrependCss, inlineCssScriptNonce) : {
			html: preparedHtml,
			consumedPrependCss: false
		};
		if (inlineCssResult.consumedPrependCss) inlineCssPrependCss = "";
		let working = inlineCssResult.html;
		if (!preHeadInjected) {
			const result = spliceAfterHeadOpen(working);
			if (result.spliced) {
				working = result.chunk;
				preHeadInjected = true;
			}
		}
		if (!injected) {
			const headEnd = working.indexOf("</head>");
			if (headEnd !== -1) {
				const before = working.slice(0, headEnd);
				const after = stripDocumentCloseSuffix(working.slice(headEnd));
				controller.enqueue(encoder.encode(before + readInlineCssPrependFallback() + readInsertion() + after));
				injected = true;
				return;
			}
		}
		working = stripDocumentCloseSuffix(working);
		controller.enqueue(encoder.encode(working));
	};
	return new TransformStream({
		transform(chunk, controller) {
			buffered.push(decoder.decode(chunk, { stream: true }));
			if (timeoutId !== null) return;
			timeoutId = setTimeout(() => {
				try {
					flushBuffered(controller);
					const rscScripts = rscEmbed.flush();
					if (rscScripts) controller.enqueue(encoder.encode(rscScripts));
				} catch {}
				timeoutId = null;
			}, 0);
		},
		async flush(controller) {
			if (timeoutId !== null) {
				clearTimeout(timeoutId);
				timeoutId = null;
			}
			const remainder = decoder.decode();
			if (remainder) buffered.push(remainder);
			flushBuffered(controller, true);
			if (!injected) {
				emitInsertion(controller);
				injected = true;
			} else if (insertsPerFlush) emitInsertion(controller);
			const finalScripts = await rscEmbed.finalize();
			if (finalScripts) controller.enqueue(encoder.encode(finalScripts));
			controller.enqueue(encoder.encode(DOCUMENT_CLOSE_SUFFIX));
		}
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-history-state.js
function isBfcacheSegmentId(id) {
	const parsed = AppElementsWire.parseElementKey(id);
	return parsed?.kind === "layout" || parsed?.kind === "page" || parsed?.kind === "slot" || parsed?.kind === "template";
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-bfcache-identity.js
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
function createInitialBfcacheMaps(options) {
	const metadata = options.metadata;
	const bfcacheIds = {};
	for (const id of collectBfcacheSegmentIds(options.elements, metadata)) bfcacheIds[id] = "0";
	return {
		bfcacheIds,
		identities: metadata.bfcacheSegmentIdentities
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-browser-hydration.js
var RSC_FORM_STATE_GLOBAL = "__VINEXT_RSC_FORM_STATE__";
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-client-reference-preloader.js
var resolvedPreload = Promise.resolve();
function createClientReferencePreloader(options) {
	let allReferencesPreloaded = false;
	let allReferencesPreloadPromise = null;
	const preloadedReferences = /* @__PURE__ */ new Set();
	const referencePreloadPromises = /* @__PURE__ */ new Map();
	function preloadReference(id, clientRequire) {
		if (preloadedReferences.has(id)) return resolvedPreload;
		const existing = referencePreloadPromises.get(id);
		if (existing) return existing;
		const preloadPromise = clientRequire(id).catch((error) => {
			options.onPreloadError?.(id, error);
		}).then(() => {
			preloadedReferences.add(id);
		}).finally(() => {
			referencePreloadPromises.delete(id);
		});
		referencePreloadPromises.set(id, preloadPromise);
		return preloadPromise;
	}
	function preloadReferenceSet(referenceIds, refs, clientRequire) {
		const pending = [];
		for (const id of referenceIds) if (Object.hasOwn(refs, id)) pending.push(preloadReference(id, clientRequire));
		if (pending.length === 0) return resolvedPreload;
		return Promise.all(pending).then(() => {});
	}
	return { preload(referenceIds) {
		const refs = options.getReferences();
		const clientRequire = options.getClientRequire();
		if (!refs || !clientRequire) return resolvedPreload;
		if (referenceIds) return preloadReferenceSet(referenceIds, refs, clientRequire);
		if (allReferencesPreloaded) return resolvedPreload;
		if (allReferencesPreloadPromise) return allReferencesPreloadPromise;
		allReferencesPreloadPromise = preloadReferenceSet(Object.keys(refs), refs, clientRequire).then(() => {
			allReferencesPreloaded = true;
		}).finally(() => {
			allReferencesPreloadPromise = null;
		});
		return allReferencesPreloadPromise;
	} };
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
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/unified-request-context.js
var _REQUEST_CONTEXT_ALS_KEY = Symbol.for("vinext.requestContext.als");
var _g$2 = globalThis;
var _als$2 = getOrCreateAls("vinext.unifiedRequestContext.als");
function _getInheritedExecutionContext() {
	const unifiedStore = _als$2.getStore();
	if (unifiedStore) return unifiedStore.executionContext;
	return _g$2[_REQUEST_CONTEXT_ALS_KEY]?.getStore() ?? null;
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
function runWithUnifiedStateMutation(mutate, fn) {
	const parentCtx = _als$2.getStore();
	if (!parentCtx) return fn();
	const childCtx = { ...parentCtx };
	mutate(childCtx);
	return _als$2.run(childCtx, fn);
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
	return _als$2.getStore() ?? createRequestContext();
}
/**
* Check whether the current execution is inside a `runWithRequestContext()` scope.
* Shim modules use this to decide whether to read from the unified store
* or fall back to their own standalone ALS.
*/
function isInsideUnifiedScope() {
	return _als$2.getStore() != null;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/root-params.js
var _FALLBACK_KEY$1 = Symbol.for("vinext.rootParams.fallback");
var _g$1 = globalThis;
var _als$1 = getOrCreateAls("vinext.rootParams.als");
getOrCreateAls("vinext.rootParams.usage.als");
_g$1[_FALLBACK_KEY$1] ??= { rootParams: null };
function runWithRootParamsScope(params, fn) {
	if (isInsideUnifiedScope()) return runWithUnifiedStateMutation((ctx) => {
		ctx.rootParams = params;
	}, fn);
	else return _als$1.run({ rootParams: params }, fn);
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
var _g = globalThis;
var _als = getOrCreateAls("vinext.navigation.als");
var _fallbackState = _g[_FALLBACK_KEY] ??= {
	serverContext: null,
	serverInsertedHTMLCallbacks: []
};
function _getState() {
	if (isInsideUnifiedScope()) return getRequestContext();
	return _als.getStore() ?? _fallbackState;
}
function runWithNavigationContext(fn) {
	if (isInsideUnifiedScope()) return runWithUnifiedStateMutation((uCtx) => {
		uCtx.serverContext = null;
		uCtx.serverInsertedHTMLCallbacks = [];
	}, fn);
	return _als.run({
		serverContext: null,
		serverInsertedHTMLCallbacks: []
	}, fn);
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
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/before-interactive-context.js
var BeforeInteractiveContext = React.createContext(null);
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/before-interactive-head.js
var VALID_ATTR_NAME = /^[a-zA-Z][\w.-]*$/;
var EVENT_HANDLER_ATTR_NAME = /^on/i;
/**
* Render captured `<Script strategy="beforeInteractive">` scripts to HTML,
* ready to splice immediately after `<head ...>` opens. Each entry has already
* had its inline content escaped via `escapeInlineContent(..., "script")`
* inside the Script shim, so this function only quotes the attributes that
* actually go on the tag (id, src, nonce, plus the residual passthroughs).
*
* Keeping this function in its own module makes the boundary obvious: anything
* passed through here is being concatenated directly into HTML; treat the
* inputs accordingly.
*/
function renderBeforeInteractiveInlineScripts(scripts) {
	if (scripts.length === 0) return "";
	let html = "";
	for (const script of scripts) {
		let attrs = "";
		if (script.id) attrs += ` id="${escapeHtmlAttr(script.id)}"`;
		if (script.src) attrs += ` src="${escapeHtmlAttr(script.src)}"`;
		attrs += createNonceAttribute(script.nonce);
		if (script.attributes) for (const [key, value] of Object.entries(script.attributes)) {
			if (!VALID_ATTR_NAME.test(key)) continue;
			if (EVENT_HANDLER_ATTR_NAME.test(key)) continue;
			if (key === "data-nscript") continue;
			if (value === true) attrs += ` ${key}`;
			else if (typeof value === "string") attrs += ` ${key}="${escapeHtmlAttr(value)}"`;
		}
		attrs += ` data-nscript="beforeInteractive"`;
		html += `<script${attrs}>${script.innerHTML ?? ""}<\/script>`;
	}
	return html;
}
//#endregion
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/dev-initial-server-error.js
var INITIAL_DEV_SERVER_ERRORS_GLOBAL = "__VINEXT_INITIAL_DEV_ERRORS__";
function stringifyThrownValue(error) {
	if (typeof error === "string") return error;
	try {
		return String(error);
	} catch {
		return Object.prototype.toString.call(error);
	}
}
function createInitialDevServerErrorPayload(error) {
	if (error instanceof Error) return {
		message: error.message,
		name: error.name || void 0,
		stack: error.stack || void 0
	};
	return { message: stringifyThrownValue(error) };
}
function createInitialDevServerErrorScript(error, scriptNonce, nodeEnv = "production") {
	if (error == null || nodeEnv === "production") return "";
	const globalRef = "self[" + safeJsonStringify(INITIAL_DEV_SERVER_ERRORS_GLOBAL) + "]";
	return createInlineScriptTag(`${globalRef}=${globalRef}||[];${globalRef}.push(${safeJsonStringify(createInitialDevServerErrorPayload(error))})`, scriptNonce);
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
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-ssr-router-instance.js
function validateNavigationHref(href) {
	assertSafeNavigationUrl(href);
}
var ssrAppRouterInstance = {
	bfcacheId: "0",
	back() {},
	forward() {},
	refresh() {},
	push(href, _options) {
		validateNavigationHref(href);
	},
	replace(href, _options) {
		validateNavigationHref(href);
	},
	prefetch(href) {
		validateNavigationHref(href);
	}
};
//#endregion
//#region ../../../node_modules/.pnpm/@vitejs+plugin-rsc@0.5.26_r_d7be5b5d64a64a218ac22ba955ebe0d2/node_modules/@vitejs/plugin-rsc/dist/dist-rz-Bnebz.js
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
//#region ../../../node_modules/.pnpm/@vitejs+plugin-rsc@0.5.26_r_d7be5b5d64a64a218ac22ba955ebe0d2/node_modules/@vitejs/plugin-rsc/dist/core/ssr.js
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
function createServerConsumerManifest() {
	return {};
}
//#endregion
//#region ../../../node_modules/.pnpm/react-server-dom-webpack@19_30d794e78d18a882de9dd6dc6e476909/node_modules/react-server-dom-webpack/cjs/react-server-dom-webpack-client.edge.production.js
/**
* @license React
* react-server-dom-webpack-client.edge.production.js
*
* Copyright (c) Meta Platforms, Inc. and affiliates.
*
* This source code is licensed under the MIT license found in the
* LICENSE file in the root directory of this source tree.
*/
var require_react_server_dom_webpack_client_edge_production = /* @__PURE__ */ __commonJSMin(((exports) => {
	var ReactDOM$1 = __require("react-dom"), decoderOptions = { stream: !0 }, hasOwnProperty = Object.prototype.hasOwnProperty;
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
			var chunkId = chunks[i++];
			chunks[i++];
			var entry = chunkCache.get(chunkId);
			if (void 0 === entry) {
				entry = __webpack_chunk_load__(chunkId);
				promises.push(entry);
				var resolve = chunkCache.set.bind(chunkCache, chunkId, null);
				entry.then(resolve, ignoreReject);
				chunkCache.set(chunkId, entry);
			} else null !== entry && promises.push(entry);
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
	function prepareDestinationWithChunks(moduleLoading, chunks, nonce$jscomp$0) {
		if (null !== moduleLoading) for (var i = 1; i < chunks.length; i += 2) {
			var nonce = nonce$jscomp$0, JSCompiler_temp_const = ReactDOMSharedInternals.d, JSCompiler_temp_const$jscomp$0 = JSCompiler_temp_const.X, JSCompiler_temp_const$jscomp$1 = moduleLoading.prefix + chunks[i];
			var JSCompiler_inline_result = moduleLoading.crossOrigin;
			JSCompiler_inline_result = "string" === typeof JSCompiler_inline_result ? "use-credentials" === JSCompiler_inline_result ? JSCompiler_inline_result : "" : void 0;
			JSCompiler_temp_const$jscomp$0.call(JSCompiler_temp_const, JSCompiler_temp_const$jscomp$1, {
				crossOrigin: JSCompiler_inline_result,
				nonce
			});
		}
	}
	var ReactDOMSharedInternals = ReactDOM$1.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE, REACT_ELEMENT_TYPE = Symbol.for("react.transitional.element"), REACT_LAZY_TYPE = Symbol.for("react.lazy"), MAYBE_ITERATOR_SYMBOL = Symbol.iterator;
	function getIteratorFn(maybeIterable) {
		if (null === maybeIterable || "object" !== typeof maybeIterable) return null;
		maybeIterable = MAYBE_ITERATOR_SYMBOL && maybeIterable[MAYBE_ITERATOR_SYMBOL] || maybeIterable["@@iterator"];
		return "function" === typeof maybeIterable ? maybeIterable : null;
	}
	var ASYNC_ITERATOR = Symbol.asyncIterator, isArrayImpl = Array.isArray, getPrototypeOf = Object.getPrototypeOf, ObjectPrototype = Object.prototype, knownServerReferences = /* @__PURE__ */ new WeakMap();
	function serializeNumber(number) {
		return Number.isFinite(number) ? 0 === number && -Infinity === 1 / number ? "$-0" : number : Infinity === number ? "$Infinity" : -Infinity === number ? "$-Infinity" : "$NaN";
	}
	function processReply(root, formFieldPrefix, temporaryReferences, resolve, reject) {
		function serializeTypedArray(tag, typedArray) {
			typedArray = new Blob([new Uint8Array(typedArray.buffer, typedArray.byteOffset, typedArray.byteLength)]);
			var blobId = nextPartId++;
			null === formData && (formData = new FormData());
			formData.append(formFieldPrefix + blobId, typedArray);
			return "$" + tag + blobId.toString(16);
		}
		function serializeBinaryReader(reader) {
			function progress(entry) {
				entry.done ? (entry = nextPartId++, data.append(formFieldPrefix + entry, new Blob(buffer)), data.append(formFieldPrefix + streamId, "\"$o" + entry.toString(16) + "\""), data.append(formFieldPrefix + streamId, "C"), pendingParts--, 0 === pendingParts && resolve(data)) : (buffer.push(entry.value), reader.read(new Uint8Array(1024)).then(progress, reject));
			}
			null === formData && (formData = new FormData());
			var data = formData;
			pendingParts++;
			var streamId = nextPartId++, buffer = [];
			reader.read(new Uint8Array(1024)).then(progress, reject);
			return "$r" + streamId.toString(16);
		}
		function serializeReader(reader) {
			function progress(entry) {
				if (entry.done) data.append(formFieldPrefix + streamId, "C"), pendingParts--, 0 === pendingParts && resolve(data);
				else try {
					var partJSON = JSON.stringify(entry.value, resolveToJSON);
					data.append(formFieldPrefix + streamId, partJSON);
					reader.read().then(progress, reject);
				} catch (x) {
					reject(x);
				}
			}
			null === formData && (formData = new FormData());
			var data = formData;
			pendingParts++;
			var streamId = nextPartId++;
			reader.read().then(progress, reject);
			return "$R" + streamId.toString(16);
		}
		function serializeReadableStream(stream) {
			try {
				var binaryReader = stream.getReader({ mode: "byob" });
			} catch (x) {
				return serializeReader(stream.getReader());
			}
			return serializeBinaryReader(binaryReader);
		}
		function serializeAsyncIterable(iterable, iterator) {
			function progress(entry) {
				if (entry.done) {
					if (void 0 === entry.value) data.append(formFieldPrefix + streamId, "C");
					else try {
						var partJSON = JSON.stringify(entry.value, resolveToJSON);
						data.append(formFieldPrefix + streamId, "C" + partJSON);
					} catch (x) {
						reject(x);
						return;
					}
					pendingParts--;
					0 === pendingParts && resolve(data);
				} else try {
					var partJSON$21 = JSON.stringify(entry.value, resolveToJSON);
					data.append(formFieldPrefix + streamId, partJSON$21);
					iterator.next().then(progress, reject);
				} catch (x$22) {
					reject(x$22);
				}
			}
			null === formData && (formData = new FormData());
			var data = formData;
			pendingParts++;
			var streamId = nextPartId++;
			iterable = iterable === iterator;
			iterator.next().then(progress, reject);
			return "$" + (iterable ? "x" : "X") + streamId.toString(16);
		}
		function resolveToJSON(key, value) {
			if (null === value) return null;
			if ("object" === typeof value) {
				switch (value.$$typeof) {
					case REACT_ELEMENT_TYPE:
						if (void 0 !== temporaryReferences && -1 === key.indexOf(":")) {
							var parentReference = writtenObjects.get(this);
							if (void 0 !== parentReference) return temporaryReferences.set(parentReference + ":" + key, value), "$T";
						}
						throw Error("React Element cannot be passed to Server Functions from the Client without a temporary reference set. Pass a TemporaryReferenceSet to the options.");
					case REACT_LAZY_TYPE:
						parentReference = value._payload;
						var init = value._init;
						null === formData && (formData = new FormData());
						pendingParts++;
						try {
							var resolvedModel = init(parentReference), lazyId = nextPartId++, partJSON = serializeModel(resolvedModel, lazyId);
							formData.append(formFieldPrefix + lazyId, partJSON);
							return "$" + lazyId.toString(16);
						} catch (x) {
							if ("object" === typeof x && null !== x && "function" === typeof x.then) {
								pendingParts++;
								var lazyId$23 = nextPartId++;
								parentReference = function() {
									try {
										var partJSON$24 = serializeModel(value, lazyId$23), data$25 = formData;
										data$25.append(formFieldPrefix + lazyId$23, partJSON$24);
										pendingParts--;
										0 === pendingParts && resolve(data$25);
									} catch (reason) {
										reject(reason);
									}
								};
								x.then(parentReference, parentReference);
								return "$" + lazyId$23.toString(16);
							}
							reject(x);
							return null;
						} finally {
							pendingParts--;
						}
				}
				parentReference = writtenObjects.get(value);
				if ("function" === typeof value.then) {
					if (void 0 !== parentReference) if (modelRoot === value) modelRoot = null;
					else return parentReference;
					null === formData && (formData = new FormData());
					pendingParts++;
					var promiseId = nextPartId++;
					key = "$@" + promiseId.toString(16);
					writtenObjects.set(value, key);
					value.then(function(partValue) {
						try {
							var previousReference = writtenObjects.get(partValue);
							var partJSON$27 = void 0 !== previousReference ? JSON.stringify(previousReference) : serializeModel(partValue, promiseId);
							partValue = formData;
							partValue.append(formFieldPrefix + promiseId, partJSON$27);
							pendingParts--;
							0 === pendingParts && resolve(partValue);
						} catch (reason) {
							reject(reason);
						}
					}, reject);
					return key;
				}
				if (void 0 !== parentReference) if (modelRoot === value) modelRoot = null;
				else return parentReference;
				else -1 === key.indexOf(":") && (parentReference = writtenObjects.get(this), void 0 !== parentReference && (key = parentReference + ":" + key, writtenObjects.set(value, key), void 0 !== temporaryReferences && temporaryReferences.set(key, value)));
				if (isArrayImpl(value)) return value;
				if (value instanceof FormData) {
					null === formData && (formData = new FormData());
					var data$31 = formData;
					key = nextPartId++;
					var prefix = formFieldPrefix + "_" + key + "_";
					value.forEach(function(originalValue, originalKey) {
						data$31.append(prefix + originalKey, originalValue);
					});
					return "$K" + key.toString(16);
				}
				if (value instanceof Map) return key = nextPartId++, parentReference = serializeModel(Array.from(value), key), null === formData && (formData = new FormData()), formData.append(formFieldPrefix + key, parentReference), "$Q" + key.toString(16);
				if (value instanceof Set) return key = nextPartId++, parentReference = serializeModel(Array.from(value), key), null === formData && (formData = new FormData()), formData.append(formFieldPrefix + key, parentReference), "$W" + key.toString(16);
				if (value instanceof ArrayBuffer) return key = new Blob([value]), parentReference = nextPartId++, null === formData && (formData = new FormData()), formData.append(formFieldPrefix + parentReference, key), "$A" + parentReference.toString(16);
				if (value instanceof Int8Array) return serializeTypedArray("O", value);
				if (value instanceof Uint8Array) return serializeTypedArray("o", value);
				if (value instanceof Uint8ClampedArray) return serializeTypedArray("U", value);
				if (value instanceof Int16Array) return serializeTypedArray("S", value);
				if (value instanceof Uint16Array) return serializeTypedArray("s", value);
				if (value instanceof Int32Array) return serializeTypedArray("L", value);
				if (value instanceof Uint32Array) return serializeTypedArray("l", value);
				if (value instanceof Float32Array) return serializeTypedArray("G", value);
				if (value instanceof Float64Array) return serializeTypedArray("g", value);
				if (value instanceof BigInt64Array) return serializeTypedArray("M", value);
				if (value instanceof BigUint64Array) return serializeTypedArray("m", value);
				if (value instanceof DataView) return serializeTypedArray("V", value);
				if ("function" === typeof Blob && value instanceof Blob) return null === formData && (formData = new FormData()), key = nextPartId++, formData.append(formFieldPrefix + key, value), "$B" + key.toString(16);
				if (key = getIteratorFn(value)) return parentReference = key.call(value), parentReference === value ? (key = nextPartId++, parentReference = serializeModel(Array.from(parentReference), key), null === formData && (formData = new FormData()), formData.append(formFieldPrefix + key, parentReference), "$i" + key.toString(16)) : Array.from(parentReference);
				if ("function" === typeof ReadableStream && value instanceof ReadableStream) return serializeReadableStream(value);
				key = value[ASYNC_ITERATOR];
				if ("function" === typeof key) return serializeAsyncIterable(value, key.call(value));
				key = getPrototypeOf(value);
				if (key !== ObjectPrototype && (null === key || null !== getPrototypeOf(key))) {
					if (void 0 === temporaryReferences) throw Error("Only plain objects, and a few built-ins, can be passed to Server Functions. Classes or null prototypes are not supported.");
					return "$T";
				}
				return value;
			}
			if ("string" === typeof value) {
				if ("Z" === value[value.length - 1] && this[key] instanceof Date) return "$D" + value;
				key = "$" === value[0] ? "$" + value : value;
				return key;
			}
			if ("boolean" === typeof value) return value;
			if ("number" === typeof value) return serializeNumber(value);
			if ("undefined" === typeof value) return "$undefined";
			if ("function" === typeof value) {
				parentReference = knownServerReferences.get(value);
				if (void 0 !== parentReference) {
					key = writtenObjects.get(value);
					if (void 0 !== key) return key;
					key = JSON.stringify({
						id: parentReference.id,
						bound: parentReference.bound
					}, resolveToJSON);
					null === formData && (formData = new FormData());
					parentReference = nextPartId++;
					formData.set(formFieldPrefix + parentReference, key);
					key = "$h" + parentReference.toString(16);
					writtenObjects.set(value, key);
					return key;
				}
				if (void 0 !== temporaryReferences && -1 === key.indexOf(":") && (parentReference = writtenObjects.get(this), void 0 !== parentReference)) return temporaryReferences.set(parentReference + ":" + key, value), "$T";
				throw Error("Client Functions cannot be passed directly to Server Functions. Only Functions passed from the Server can be passed back again.");
			}
			if ("symbol" === typeof value) {
				if (void 0 !== temporaryReferences && -1 === key.indexOf(":") && (parentReference = writtenObjects.get(this), void 0 !== parentReference)) return temporaryReferences.set(parentReference + ":" + key, value), "$T";
				throw Error("Symbols cannot be passed to a Server Function without a temporary reference set. Pass a TemporaryReferenceSet to the options.");
			}
			if ("bigint" === typeof value) return "$n" + value.toString(10);
			throw Error("Type " + typeof value + " is not supported as an argument to a Server Function.");
		}
		function serializeModel(model, id) {
			"object" === typeof model && null !== model && (id = "$" + id.toString(16), writtenObjects.set(model, id), void 0 !== temporaryReferences && temporaryReferences.set(id, model));
			modelRoot = model;
			return JSON.stringify(model, resolveToJSON);
		}
		var nextPartId = 1, pendingParts = 0, formData = null, writtenObjects = /* @__PURE__ */ new WeakMap(), modelRoot = root, json = serializeModel(root, 0);
		null === formData ? resolve(json) : (formData.set(formFieldPrefix + "0", json), 0 === pendingParts && resolve(formData));
		return function() {
			0 < pendingParts && (pendingParts = 0, null === formData ? resolve(json) : resolve(formData));
		};
	}
	var boundCache = /* @__PURE__ */ new WeakMap();
	function encodeFormData(reference) {
		var resolve, reject, thenable = new Promise(function(res, rej) {
			resolve = res;
			reject = rej;
		});
		processReply(reference, "", void 0, function(body) {
			if ("string" === typeof body) {
				var data = new FormData();
				data.append("0", body);
				body = data;
			}
			thenable.status = "fulfilled";
			thenable.value = body;
			resolve(body);
		}, function(e) {
			thenable.status = "rejected";
			thenable.reason = e;
			reject(e);
		});
		return thenable;
	}
	function defaultEncodeFormAction(identifierPrefix) {
		var referenceClosure = knownServerReferences.get(this);
		if (!referenceClosure) throw Error("Tried to encode a Server Action from a different instance than the encoder is from. This is a bug in React.");
		var data = null;
		if (null !== referenceClosure.bound) {
			data = boundCache.get(referenceClosure);
			data || (data = encodeFormData({
				id: referenceClosure.id,
				bound: referenceClosure.bound
			}), boundCache.set(referenceClosure, data));
			if ("rejected" === data.status) throw data.reason;
			if ("fulfilled" !== data.status) throw data;
			referenceClosure = data.value;
			var prefixedData = new FormData();
			referenceClosure.forEach(function(value, key) {
				prefixedData.append("$ACTION_" + identifierPrefix + ":" + key, value);
			});
			data = prefixedData;
			referenceClosure = "$ACTION_REF_" + identifierPrefix;
		} else referenceClosure = "$ACTION_ID_" + referenceClosure.id;
		return {
			name: referenceClosure,
			method: "POST",
			encType: "multipart/form-data",
			data
		};
	}
	function isSignatureEqual(referenceId, numberOfBoundArgs) {
		var referenceClosure = knownServerReferences.get(this);
		if (!referenceClosure) throw Error("Tried to encode a Server Action from a different instance than the encoder is from. This is a bug in React.");
		if (referenceClosure.id !== referenceId) return !1;
		var boundPromise = referenceClosure.bound;
		if (null === boundPromise) return 0 === numberOfBoundArgs;
		switch (boundPromise.status) {
			case "fulfilled": return boundPromise.value.length === numberOfBoundArgs;
			case "pending": throw boundPromise;
			case "rejected": throw boundPromise.reason;
			default: throw "string" !== typeof boundPromise.status && (boundPromise.status = "pending", boundPromise.then(function(boundArgs) {
				boundPromise.status = "fulfilled";
				boundPromise.value = boundArgs;
			}, function(error) {
				boundPromise.status = "rejected";
				boundPromise.reason = error;
			})), boundPromise;
		}
	}
	function registerBoundServerReference(reference, id, bound, encodeFormAction) {
		knownServerReferences.has(reference) || (knownServerReferences.set(reference, {
			id,
			originalBind: reference.bind,
			bound
		}), Object.defineProperties(reference, {
			$$FORM_ACTION: { value: void 0 === encodeFormAction ? defaultEncodeFormAction : function() {
				var referenceClosure = knownServerReferences.get(this);
				if (!referenceClosure) throw Error("Tried to encode a Server Action from a different instance than the encoder is from. This is a bug in React.");
				var boundPromise = referenceClosure.bound;
				null === boundPromise && (boundPromise = Promise.resolve([]));
				return encodeFormAction(referenceClosure.id, boundPromise);
			} },
			$$IS_SIGNATURE_EQUAL: { value: isSignatureEqual },
			bind: { value: bind }
		}));
	}
	var FunctionBind = Function.prototype.bind, ArraySlice = Array.prototype.slice;
	function bind() {
		var referenceClosure = knownServerReferences.get(this);
		if (!referenceClosure) return FunctionBind.apply(this, arguments);
		var newFn = referenceClosure.originalBind.apply(this, arguments), args = ArraySlice.call(arguments, 1), boundPromise = null;
		boundPromise = null !== referenceClosure.bound ? Promise.resolve(referenceClosure.bound).then(function(boundArgs) {
			return boundArgs.concat(args);
		}) : Promise.resolve(args);
		knownServerReferences.set(newFn, {
			id: referenceClosure.id,
			originalBind: newFn.bind,
			bound: boundPromise
		});
		Object.defineProperties(newFn, {
			$$FORM_ACTION: { value: this.$$FORM_ACTION },
			$$IS_SIGNATURE_EQUAL: { value: isSignatureEqual },
			bind: { value: bind }
		});
		return newFn;
	}
	function createBoundServerReference(metaData, callServer, encodeFormAction) {
		function action() {
			var args = Array.prototype.slice.call(arguments);
			return bound ? "fulfilled" === bound.status ? callServer(id, bound.value.concat(args)) : Promise.resolve(bound).then(function(boundArgs) {
				return callServer(id, boundArgs.concat(args));
			}) : callServer(id, args);
		}
		var id = metaData.id, bound = metaData.bound;
		registerBoundServerReference(action, id, bound, encodeFormAction);
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
		if (!response._serverReferenceConfig) return createBoundServerReference(metaData, response._callServer, response._encodeFormAction);
		var serverReference = resolveServerReference(response._serverReferenceConfig, metaData.id), promise = preloadModule(serverReference);
		if (promise) metaData.bound && (promise = Promise.all([promise, metaData.bound]));
		else if (metaData.bound) promise = Promise.resolve(metaData.bound);
		else return promise = requireModule(serverReference), registerBoundServerReference(promise, metaData.id, metaData.bound, response._encodeFormAction), promise;
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
			registerBoundServerReference(resolvedValue, metaData.id, metaData.bound, response._encodeFormAction);
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
		prepareDestinationWithChunks(response._moduleLoading, model[1], response._nonce);
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
	function noServerCall() {
		throw Error("Server Functions cannot be called during initial render. This would create a fetch waterfall. Try to use a Server Component to pass data to Client Components instead.");
	}
	function createResponseFromOptions(options) {
		return new ResponseInstance(options.serverConsumerManifest.moduleMap, options.serverConsumerManifest.serverModuleMap, options.serverConsumerManifest.moduleLoading, noServerCall, options.encodeFormAction, "string" === typeof options.nonce ? options.nonce : void 0, options && options.temporaryReferences ? options.temporaryReferences : void 0);
	}
	function startReadingFromStream(response, stream, onDone) {
		function progress(_ref) {
			var value = _ref.value;
			if (_ref.done) return onDone();
			var i = 0, rowState = streamState._rowState;
			_ref = streamState._rowID;
			for (var rowTag = streamState._rowTag, rowLength = streamState._rowLength, buffer = streamState._buffer, chunkLength = value.length; i < chunkLength;) {
				var lastIdx = -1;
				switch (rowState) {
					case 0:
						lastIdx = value[i++];
						58 === lastIdx ? rowState = 1 : _ref = _ref << 4 | (96 < lastIdx ? lastIdx - 87 : lastIdx - 48);
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
				if (-1 < lastIdx) rowLength = new Uint8Array(value.buffer, offset, lastIdx - i), processFullBinaryRow(response, streamState, _ref, rowTag, buffer, rowLength), i = lastIdx, 3 === rowState && i++, rowLength = _ref = rowTag = rowState = 0, buffer.length = 0;
				else {
					value = new Uint8Array(value.buffer, offset, value.byteLength - i);
					buffer.push(value);
					rowLength -= value.byteLength;
					break;
				}
			}
			streamState._rowState = rowState;
			streamState._rowID = _ref;
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
	exports.createFromReadableStream = function(stream, options) {
		options = createResponseFromOptions(options);
		startReadingFromStream(options, stream, close.bind(null, options));
		return getChunk(options, 0);
	};
}));
//#endregion
//#region ../../../node_modules/.pnpm/@vitejs+plugin-rsc@0.5.26_r_d7be5b5d64a64a218ac22ba955ebe0d2/node_modules/@vitejs/plugin-rsc/dist/react/ssr.js
var import_client_edge = /* @__PURE__ */ __toESM((/* @__PURE__ */ __commonJSMin(((exports, module) => {
	module.exports = require_react_server_dom_webpack_client_edge_production();
})))(), 1);
function createFromReadableStream(stream, options = {}) {
	return import_client_edge.createFromReadableStream(stream, {
		serverConsumerManifest: createServerConsumerManifest(),
		...options
	});
}
//#endregion
//#region \0virtual:vite-rsc/client-references
var client_references_default = {
	"0132a7525229": async () => {
		const m = await import("./_next/static/home-client-CxWd5hi7.js");
		return { get "default"() {
			return m["default"];
		} };
	},
	"0604f93d3a06": async () => {
		const m = await import("./_next/static/app-router-scroll-DO385Tog.js");
		return { get "AppRouterScrollTarget"() {
			return m["AppRouterScrollTarget"];
		} };
	},
	"243ee20defce": async () => {
		const m = await import("./_next/static/layout-segment-context-EY4ZX1zT.js");
		return { get "LayoutSegmentProvider"() {
			return m["LayoutSegmentProvider"];
		} };
	},
	"878821595ec6": async () => {
		const m = await import("./_next/static/chat-client-DCTwKbdB.js");
		return { get "default"() {
			return m["default"];
		} };
	},
	"8c59b4cfb786": async () => {
		const m = await Promise.resolve().then(() => default_global_error_exports);
		return { get "default"() {
			return m["default"];
		} };
	},
	"9d9ddb30364a": async () => {
		const m = await Promise.resolve().then(() => slot_exports);
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
		const m = await import("./_next/static/error-boundary-BW4zQve8.js");
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
		await import("./_next/static/app-prefetch-fetch-queue-C9180ymC.js");
		return {};
	},
	"de80fbf070f4": async () => {
		const m = await import("./_next/static/streamed-icons-Cok9EkWr.js");
		return { get "StreamedIconsInsertion"() {
			return m["StreamedIconsInsertion"];
		} };
	},
	"e97a5adc44a3": async () => {
		const m = await import("./_next/static/desktop-runtime-shell-CrylNd9h.js");
		return { get "default"() {
			return m["default"];
		} };
	}
};
//#endregion
//#region ../../../node_modules/.pnpm/@vitejs+plugin-rsc@0.5.26_r_d7be5b5d64a64a218ac22ba955ebe0d2/node_modules/@vitejs/plugin-rsc/dist/ssr.js
var onClientReference;
initialize();
function initialize() {
	setRequireModule({ load: async (id) => {
		{
			const import_ = client_references_default[id];
			if (!import_) throw new Error(`client reference not found '${id}'`);
			const deps = __vite_rsc_assets_manifest.clientReferenceDeps[id] ?? {
				js: [],
				css: []
			};
			preloadDeps(deps);
			onClientReference?.({
				id,
				deps
			});
			return wrapResourceProxy(await import_(), id, deps);
		}
	} });
}
function wrapResourceProxy(mod, id, deps) {
	return new Proxy(mod, { get(target, p, receiver) {
		if (p in mod) {
			preloadDeps(deps);
			onClientReference?.({
				id,
				deps
			});
		}
		return Reflect.get(target, p, receiver);
	} });
}
function preloadDeps(deps) {
	for (const href of deps.js) ReactDOM.preloadModule(href, {
		as: "script",
		crossOrigin: ""
	});
	for (const href of deps.css) ReactDOM.preinit(href, {
		as: "style",
		precedence: __vite_rsc_assets_manifest.cssLinkPrecedence !== false ? "vite-rsc/client-reference" : void 0
	});
}
/**
* Default cap for the preload `Link` header, matching Next.js's
* `defaultConfig.reactMaxHeadersLength`. Used when no config value threads
* through (e.g. error-boundary renders) so React's internal cap agrees with
* the response-layer combine cap.
*/
var DEFAULT_REACT_MAX_HEADERS_LENGTH = 6e3;
function isReactDevelopmentRuntime() {
	return false;
}
function isStaticPrerenderModule(value) {
	return typeof value === "object" && value !== null && "prerender" in value && typeof value.prerender === "function";
}
async function loadStaticPrerender() {
	const staticRenderer = await import("react-dom/static.edge");
	if (isStaticPrerenderModule(staticRenderer)) return staticRenderer.prerender;
	if (isReactDevelopmentRuntime()) try {
		const [{ createRequire }, path] = await Promise.all([import("node:module"), import("node:path")]);
		const reactDomPackageJson = createRequire(import.meta.url).resolve("react-dom/package.json");
		const reactDomDir = path.dirname(reactDomPackageJson);
		const devRenderer = await import(
			/* @vite-ignore */
			path.join(reactDomDir, "cjs/react-dom-server.edge.development.js")
);
		if (isStaticPrerenderModule(devRenderer)) return devRenderer.prerender;
		const devRendererDefault = typeof devRenderer === "object" && devRenderer !== null && "default" in devRenderer && devRenderer.default;
		if (isStaticPrerenderModule(devRendererDefault)) return devRendererDefault.prerender;
		throw new Error("react-dom development renderer did not expose prerender().");
	} catch (error) {
		throw new Error("[vinext] Failed to load React static development renderer.", { cause: error });
	}
	throw new Error("[vinext] react-dom/static.edge did not expose prerender().");
}
function createUtf8Stream(html) {
	const encoder = new TextEncoder();
	return new ReadableStream({ start(controller) {
		controller.enqueue(encoder.encode(html));
		controller.close();
	} });
}
function buildBootstrapModuleScript(bootstrapModuleUrl, nonce) {
	if (!bootstrapModuleUrl) return "";
	return `<script type="module"${createNonceAttribute(nonce)} src="` + escapeHtmlAttr(bootstrapModuleUrl) + "\" id=\"_R_\" async=\"\"><\/script>";
}
function renderSsrErrorDocumentShell(bootstrapModuleUrl, nonce) {
	const html = renderToStaticMarkup(createElement(DefaultGlobalError, { error: null })).replace("<style>", "<style data-vinext-error-shell-style=\"\">");
	const bootstrapScript = buildBootstrapModuleScript(bootstrapModuleUrl, nonce);
	if (!bootstrapScript) return createUtf8Stream(`<!DOCTYPE html>${html}`);
	const documentClose = "</body></html>";
	if (!html.endsWith(documentClose)) return createUtf8Stream(`<!DOCTYPE html>${html}${bootstrapScript}`);
	return createUtf8Stream(`<!DOCTYPE html>${html.slice(0, -14)}${bootstrapScript}${documentClose}`);
}
var clientReferencePreloader = createClientReferencePreloader({
	getReferences() {
		return client_references_default;
	},
	getClientRequire() {
		return globalThis.__vite_rsc_client_require__;
	},
	onPreloadError(id, error) {}
});
var BfcacheIdMapContext = getBfcacheIdMapContext();
function ssrErrorDigest(input) {
	let hash = 5381;
	for (let i = input.length - 1; i >= 0; i--) hash = hash * 33 ^ input.charCodeAt(i);
	return (hash >>> 0).toString();
}
function getErrorMessage(error) {
	if (error instanceof Error) return error.message;
	if (typeof error === "string") return error;
	return Object.prototype.toString.call(error);
}
function renderInsertedHtml(insertedElements) {
	let insertedHTML = "";
	for (const element of insertedElements) try {
		insertedHTML += renderToStaticMarkup(createElement(Fragment, null, element));
	} catch {}
	return insertedHTML;
}
function renderFontHtml(fontData, nonce, options = {}) {
	if (!fontData) return "";
	let fontHTML = "";
	const nonceAttr = createNonceAttribute(nonce);
	const includeStyles = options.includeStyles ?? true;
	for (const url of fontData.links ?? []) fontHTML += `<link rel="stylesheet"${nonceAttr} href="${escapeHtmlAttr(appendAssetDeploymentIdQuery(url))}" />\n`;
	for (const preload of fontData.preloads ?? []) fontHTML += `<link rel="preload"${nonceAttr} href="${escapeHtmlAttr(preload.href)}" as="font" type="${escapeHtmlAttr(preload.type)}" crossorigin />\n`;
	if (includeStyles && fontData.styles && fontData.styles.length > 0) fontHTML += `<style data-vinext-fonts${nonceAttr}>${fontData.styles.join("\n")}</style>\n`;
	return fontHTML;
}
function hasInlineCssManifest(manifest) {
	return manifest !== void 0 && Object.keys(manifest).length > 0;
}
/**
* Extract the bootstrap module URL from the `import("...")` string that
* `import.meta.viteRsc.loadBootstrapScriptContent("index")` returns.
*
* The plugin-rsc helper returns the bootstrap as an inline call so we can
* inject it via `bootstrapScriptContent`. We instead pass the URL to
* React's `bootstrapModules` option so a real
* `<script type="module" src="…">` tag ends up in the streamed HTML —
* this exposes the URL to anything that reads `script.attribs.src` (e.g.
* the Next.js asset-prefix fixture test). The same URL also feeds the
* `<link rel="modulepreload">` we emit ahead of the bootstrap.
*
* Returns `undefined` when the helper produced no URL (older plugin-rsc
* versions, or a custom client entry that disables bootstrap content).
*/
function extractBootstrapModuleUrl(bootstrapScriptContent) {
	if (!bootstrapScriptContent) return void 0;
	return bootstrapScriptContent.match(/import\(["']([^"']+)["']\)/)?.[1] ?? void 0;
}
function buildModulePreloadHtml(bootstrapModuleUrl, nonce) {
	if (!bootstrapModuleUrl) return "";
	return `<link rel="modulepreload"${createNonceAttribute(nonce)} href="${escapeHtmlAttr(bootstrapModuleUrl)}" />\n`;
}
function buildHeadInjectionHtml(navContext, bootstrapModuleUrl, formState, insertedHTML, fontHTML, dynamicStaleTimeSeconds, scriptNonce) {
	const navPayload = {
		pathname: navContext.pathname,
		searchParams: [...navContext.searchParams.entries()]
	};
	return createInlineScriptTag(createNavigationRuntimeRscMetadataScript(navContext.params, navPayload, dynamicStaleTimeSeconds), scriptNonce) + (formState === null ? "" : createInlineScriptTag("self[" + safeJsonStringify(RSC_FORM_STATE_GLOBAL) + "]=" + safeJsonStringify(formState), scriptNonce)) + buildModulePreloadHtml(bootstrapModuleUrl, scriptNonce) + insertedHTML + fontHTML;
}
function requireNavigationContext(navContext) {
	if (!navContext) throw new Error("App SSR requires navigation context for BFCache state keys");
	return navContext;
}
async function handleSsr(rscStream, navContext, fontData, options) {
	return runWithNavigationContext(async () => {
		const ssrNavigationContext = requireNavigationContext(navContext);
		await clientReferencePreloader.preload();
		setNavigationContext(ssrNavigationContext);
		clearServerInsertedHTML();
		const cleanup = () => {
			setNavigationContext(null);
			clearServerInsertedHTML();
		};
		return runWithRootParamsScope(options?.rootParams ?? {}, async () => {
			try {
				let ssrStream;
				let rscEmbed;
				if (options?.sideStream) {
					ssrStream = rscStream;
					rscEmbed = createRscEmbedTransform(options.sideStream, options?.scriptNonce, options?.getInitialNavigationCacheMetadata);
					if (options.capturedRscDataRef) options.capturedRscDataRef.value = rscEmbed.getRawBuffer();
				} else {
					const [s1, s2] = rscStream.tee();
					ssrStream = s1;
					rscEmbed = createRscEmbedTransform(s2, options?.scriptNonce, options?.getInitialNavigationCacheMetadata);
				}
				let flightRoot = null;
				function VinextFlightRoot() {
					for (const moduleUrl of pagesClientAssets.appBootstrapPreinitModules ?? []) preinitModule(moduleUrl, {
						as: "script",
						nonce: options?.scriptNonce
					});
					if (!flightRoot) flightRoot = createFromReadableStream(ssrStream);
					const wireElements = use(flightRoot);
					const elements = AppElementsWire.decode(wireElements);
					const metadata = AppElementsWire.readMetadata(elements);
					const bfcacheMaps = createInitialBfcacheMaps({
						elements,
						metadata
					});
					const routeTree = createElement(ElementsContext.Provider, { value: elements }, createElement(Slot, { id: metadata.routeId }));
					const identityMapTree = createElement(BfcacheIdentityMapContext.Provider, { value: bfcacheMaps.identities }, routeTree);
					return BfcacheIdMapContext ? createElement(BfcacheIdMapContext.Provider, { value: bfcacheMaps.bfcacheIds }, identityMapTree) : identityMapTree;
				}
				const flightRootElement = createElement(VinextFlightRoot);
				const root = AppRouterContext ? createElement(AppRouterContext.Provider, { value: ssrAppRouterInstance }, flightRootElement) : flightRootElement;
				const ssrTree = ServerInsertedHTMLContext ? createElement(ServerInsertedHTMLContext.Provider, { value: registerServerInsertedHTMLCallback }, root) : root;
				const beforeInteractiveInlineScripts = [];
				const registerBeforeInteractiveInlineScript = (script) => {
					beforeInteractiveInlineScripts.push(script);
				};
				const ssrRoot = withScriptNonce(createElement(BeforeInteractiveContext.Provider, { value: registerBeforeInteractiveInlineScript }, ssrTree), options?.scriptNonce);
				const bootstrapModuleUrl = extractBootstrapModuleUrl(await Promise.resolve(__vite_rsc_assets_manifest.bootstrapScriptContent));
				const errorMetaRenderer = createSsrErrorMetaRenderer({ basePath: options?.basePath });
				const pprFallbackShellSignal = options?.pprFallbackShellSignal;
				let reactLinkHeader = "";
				const maxHeadersLength = options?.reactMaxHeadersLength ?? DEFAULT_REACT_MAX_HEADERS_LENGTH;
				const captureHeaders = maxHeadersLength > 0;
				const renderOptions = {
					bootstrapModules: bootstrapModuleUrl ? [bootstrapModuleUrl] : void 0,
					formState: options?.formState ?? null,
					nonce: options?.scriptNonce,
					onHeaders: captureHeaders ? (headers) => {
						const link = headers.get("Link");
						if (link) reactLinkHeader = link;
					} : void 0,
					maxHeadersLength: captureHeaders ? maxHeadersLength : void 0,
					onError(error) {
						if (pprFallbackShellSignal && isPprFallbackShellAbortError(error)) return;
						errorMetaRenderer.capture(error);
						if (error && typeof error === "object" && "digest" in error) return String(error.digest);
						if (error) return ssrErrorDigest(getErrorMessage(error) + (error instanceof Error ? error.stack ?? "" : ""));
					}
				};
				let htmlStream;
				let shellErrorRecovered = false;
				let shouldDelayInitialHtmlPull = false;
				if (pprFallbackShellSignal) {
					const prerender = await loadStaticPrerender();
					const htmlAbortController = new AbortController();
					const pendingHtml = prerender(ssrRoot, {
						...renderOptions,
						signal: htmlAbortController.signal
					});
					setTimeout(() => htmlAbortController.abort(), 0);
					htmlStream = (await pendingHtml).prelude;
				} else {
					let streamingHtmlStream;
					try {
						streamingHtmlStream = await renderToReadableStream(ssrRoot, { ...renderOptions });
						if (options?.waitForAllReady === true) await streamingHtmlStream.allReady;
						else shouldDelayInitialHtmlPull = true;
						htmlStream = streamingHtmlStream;
					} catch (error) {
						streamingHtmlStream?.cancel().catch(() => {});
						if (options?.fallbackToErrorDocumentOnShellError !== true || options?.waitForAllReady === true || typeof error?.digest === "string") throw error;
						shellErrorRecovered = true;
						htmlStream = renderSsrErrorDocumentShell(bootstrapModuleUrl, options?.scriptNonce);
					}
				}
				const inlineCssManifest = globalThis.__VINEXT_INLINE_CSS__;
				const fontStyles = fontData?.styles ?? [];
				const mergeFontStylesIntoInlineCss = fontStyles.length > 0 && hasInlineCssManifest(inlineCssManifest);
				const inlineCssFontStyles = mergeFontStylesIntoInlineCss ? fontStyles.join("\n") : "";
				const inlineCssFontStyleFallbackHTML = mergeFontStylesIntoInlineCss ? renderFontHtml({ styles: fontStyles }, options?.scriptNonce) : "";
				const fontHTML = renderFontHtml(fontData, options?.scriptNonce, { includeStyles: !mergeFontStylesIntoInlineCss });
				let traceMetaHTML = null;
				const getTraceMetaHTML = () => {
					if (traceMetaHTML === null) traceMetaHTML = getClientTraceMetadataHTML(options?.clientTraceMetadata);
					return traceMetaHTML;
				};
				let didInjectHeadHTML = false;
				const getInsertedHTML = () => {
					const insertedHTML = renderInsertedHtml(renderServerInsertedHTML());
					const errorMetaHTML = errorMetaRenderer.flush();
					const initialDevServerErrorHTML = createInitialDevServerErrorScript(options?.initialDevServerError, options?.scriptNonce);
					if (didInjectHeadHTML) return insertedHTML + errorMetaHTML;
					didInjectHeadHTML = true;
					return buildHeadInjectionHtml(ssrNavigationContext, bootstrapModuleUrl, options?.formState ?? null, insertedHTML + errorMetaHTML + getTraceMetaHTML() + initialDevServerErrorHTML, fontHTML, options?.dynamicStaleTimeSeconds, options?.scriptNonce);
				};
				const getBeforeInteractiveHeadHTML = () => renderBeforeInteractiveInlineScripts(beforeInteractiveInlineScripts);
				if (shouldDelayInitialHtmlPull) await waitAtLeastOneReactRenderTask();
				return {
					htmlStream: deferUntilStreamConsumed(htmlStream.pipeThrough(createTickBufferedTransform(rscEmbed, getInsertedHTML, getBeforeInteractiveHeadHTML, inlineCssManifest, inlineCssFontStyles, inlineCssFontStyleFallbackHTML, options?.scriptNonce)), cleanup),
					metadataReady: Promise.resolve(),
					capturedRscData: options?.capturedRscDataRef?.value ?? null,
					shellErrorRecovered,
					linkHeader: reactLinkHeader
				};
			} catch (error) {
				cleanup();
				throw error;
			}
		});
	});
}
var app_ssr_entry_default = { async fetch(request) {
	if (isOpenRedirectShaped(new URL(request.url).pathname)) return notFoundResponse();
	const result = await (await import("../index.js")).default(request);
	if (result instanceof Response) return result;
	if (result == null) return notFoundResponse();
	return new Response(String(result), { status: 200 });
} };
//#endregion
export { getLayoutSegmentContext as a, markPprFallbackShellDynamicBoundary as c, app_ssr_entry_default as default, handleSsr, isRedirectError as i, __commonJSMin as l, DefaultGlobalError as n, getNavigationContext as o, decodeRedirectError as r, AppRouterContext as s, stripBasePath as t, __require as u };
