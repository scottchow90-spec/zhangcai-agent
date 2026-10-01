import * as React$1 from "react";
import { jsx } from "react/jsx-runtime";
import "react-dom";
//#region ../../../node_modules/.pnpm/vinext@1.0.0-beta.5_@vitejs_b79f96eac0df69dff29a3f5c3c8024f5/node_modules/vinext/dist/shims/hash-scroll.js
function decodeHashFragment(fragment) {
	try {
		return decodeURIComponent(fragment);
	} catch {
		return fragment;
	}
}
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
function getPendingAppRouterScrollIntent() {
	return getScrollIntentStore().pending;
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
var AppRouterScrollCommitContext = React$1.createContext(null);
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
function findDOMNode(instance) {
	return null;
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
var AppRouterScrollTargetInner = class extends React$1.Component {
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
function AppRouterScrollTarget({ children }) {
	return /* @__PURE__ */ jsx(AppRouterScrollTargetInner, {
		commitId: React$1.useContext(AppRouterScrollCommitContext),
		children
	});
}
//#endregion
export { AppRouterScrollTarget };
