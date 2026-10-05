import { r as __toESM } from "./rolldown-runtime-DFEGrk7x.js";
import { i as require_react } from "./framework-BiZY8KgM.js";
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/streamed-icons.js
var import_react = /* @__PURE__ */ __toESM(require_react(), 1);
var STREAMED_ICON_ATTRIBUTE = "data-vinext-streamed-icon";
function getStreamedIconOrder(icon, metadataKey) {
	const marker = icon.getAttribute(STREAMED_ICON_ATTRIBUTE);
	const prefix = `${metadataKey}:`;
	if (!marker?.startsWith(prefix)) return null;
	const order = Number(marker.slice(prefix.length));
	return Number.isInteger(order) && order >= 0 ? order : null;
}
function reconcileStreamedIcons(metadataKey) {
	document.querySelectorAll(`body link[${STREAMED_ICON_ATTRIBUTE}]`).forEach((icon) => document.head.appendChild(icon));
	const ownedIcons = [...document.querySelectorAll(`head link[${STREAMED_ICON_ATTRIBUTE}]`)];
	const retainedIcons = /* @__PURE__ */ new Map();
	for (const icon of ownedIcons) {
		const order = getStreamedIconOrder(icon, metadataKey);
		if (order === null) {
			icon.remove();
			continue;
		}
		const previousIcon = retainedIcons.get(order);
		if (previousIcon) previousIcon.remove();
		retainedIcons.set(order, icon);
	}
	for (const [, icon] of [...retainedIcons].sort(([leftOrder], [rightOrder]) => leftOrder - rightOrder)) document.head.appendChild(icon);
}
function StreamedIconsInsertion({ metadataKey }) {
	(0, import_react.useLayoutEffect)(() => reconcileStreamedIcons(metadataKey), [metadataKey]);
	return null;
}
//#endregion
export { StreamedIconsInsertion, reconcileStreamedIcons };
