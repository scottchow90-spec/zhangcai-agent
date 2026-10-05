import { C as getCollectedFetchTags, M as _consumeRequestScopedCacheLife, _t as consumeInvalidDynamicUsageError, gt as consumeDynamicUsage } from "./cache-headers-CBpU4sbE.js";
import { c as consumeAppPageRenderObservationState, d as createAppPageRscOutputScope, g as teeAppPageRscStreamForCapture, h as buildAppPageFontLinkHeader, l as createAppPageHtmlOutputScope, m as isAppSsrRenderResult, o as readStreamAsText, p as buildAppPageLinkHeader, u as createAppPageRenderObservation, y as buildAppPageTags } from "../../index.js";
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/server/app-page-cache-render.js
/**
* Render an App page element to HTML (and optionally its RSC payload) for cache
* storage. Combines the RSC stream, SSR handler, observation consumption, and
* cache-tag construction used by both normal ISR revalidation and PPR fallback
* shell regeneration.
*/
async function renderAppPageCacheArtifacts(options) {
	const rscCapture = teeAppPageRscStreamForCapture(options.renderToReadableStream(options.element, { onError: options.onError }), options.captureRscData);
	const capturedRscDataRef = { value: null };
	const fontPreloads = options.getFontPreloads();
	const htmlResult = await (await options.loadSsrHandler()).handleSsr(rscCapture.ssrStream, options.getNavigationContext(), {
		links: options.getFontLinks(),
		styles: options.getFontStyles(),
		preloads: fontPreloads
	}, {
		basePath: options.basePath,
		clientTraceMetadata: options.clientTraceMetadata,
		reactMaxHeadersLength: options.reactMaxHeadersLength,
		rootParams: options.rootParams,
		waitForAllReady: options.waitForAllReady,
		...rscCapture.sideStream ? {
			sideStream: rscCapture.sideStream,
			capturedRscDataRef
		} : {}
	});
	const htmlStream = isAppSsrRenderResult(htmlResult) ? htmlResult.htmlStream : htmlResult;
	const linkHeader = buildAppPageLinkHeader(isAppSsrRenderResult(htmlResult) ? htmlResult.linkHeader : void 0, buildAppPageFontLinkHeader(fontPreloads), options.reactMaxHeadersLength);
	const html = await readStreamAsText(htmlStream);
	let rscData;
	if (options.captureRscData) {
		const capturedPromise = capturedRscDataRef.value;
		if (!capturedPromise) throw new Error("[vinext] Expected captured RSC data while rendering app page cache artifacts");
		rscData = await capturedPromise;
	}
	const cacheLife = _consumeRequestScopedCacheLife();
	const tags = buildAppPageTags(options.cleanPathname, getCollectedFetchTags(), options.route.routeSegments);
	const observationState = consumeAppPageRenderObservationState();
	consumeInvalidDynamicUsageError();
	consumeDynamicUsage();
	const result = {
		html,
		htmlRenderObservation: createAppPageRenderObservation({
			boundaryOutcome: { kind: "success" },
			cacheability: "public",
			cacheTags: tags,
			cleanPathname: options.cleanPathname,
			completeness: "complete",
			output: createAppPageHtmlOutputScope({
				element: options.element,
				renderEpoch: null,
				rootBoundaryId: null,
				routePattern: options.route.pattern
			}),
			params: options.navigationParams,
			state: observationState
		}),
		...linkHeader ? { linkHeader } : {},
		tags,
		cacheControl: typeof cacheLife?.revalidate === "number" ? {
			revalidate: cacheLife.revalidate,
			expire: cacheLife.expire,
			stale: cacheLife.stale
		} : void 0
	};
	if (options.captureRscData) {
		result.rscData = rscData;
		result.rscRenderObservation = createAppPageRenderObservation({
			boundaryOutcome: { kind: "success" },
			cacheability: "public",
			cacheTags: tags,
			cleanPathname: options.cleanPathname,
			completeness: "complete",
			output: createAppPageRscOutputScope({
				element: options.element,
				mountedSlotsHeader: options.mountedSlotsHeader,
				renderEpoch: null,
				rootBoundaryId: null,
				routePattern: options.route.pattern
			}),
			params: options.navigationParams,
			state: observationState
		});
	}
	return result;
}
//#endregion
export { renderAppPageCacheArtifacts };
