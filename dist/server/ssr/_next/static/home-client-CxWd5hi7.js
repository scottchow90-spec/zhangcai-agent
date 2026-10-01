import { l as __commonJSMin, u as __require } from "../../index.js";
import { a as RefreshCw, i as X, n as bridgeUrl, o as Database, r as isDesktopRuntime, s as createLucideIcon, t as bridgeHostLabel } from "./bridge-url-D6eZPRbG.js";
import { _ as CircleQuestionMark, a as loadReportArchive, c as saveReportArchive, d as Sparkles, f as ShieldCheck, g as FileText, h as LayoutDashboard, i as deleteArchivedReport, l as shouldShowInMyReports, m as LoaderCircle, n as normalizeHarnessOutput, o as loadReportArchiveFromLocalRuntime, p as Search, r as createReportId, s as reportArchiveChangedEvent, t as HARNESS_JSON_SCHEMA, u as skill14_catalog_default, v as ChevronRight, y as Check } from "./harness-output-SfiT4htq.js";
import { t as Activity } from "./activity-J2y4hB5k.js";
import * as React$3 from "react";
import { createElement, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Fragment as Fragment$1, jsx, jsxs } from "react/jsx-runtime";
import * as ReactDOM from "react-dom";
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var ArrowRight = createLucideIcon("arrow-right", [["path", {
	d: "M5 12h14",
	key: "1ays0h"
}], ["path", {
	d: "m12 5 7 7-7 7",
	key: "xquz4c"
}]]);
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var ArrowUpRight = createLucideIcon("arrow-up-right", [["path", {
	d: "M7 7h10v10",
	key: "1tivn9"
}], ["path", {
	d: "M7 17 17 7",
	key: "1vkiza"
}]]);
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var BookOpen = createLucideIcon("book-open", [["path", {
	d: "M12 5v16",
	key: "1f6ucr"
}], ["path", {
	d: "M20.001 19A2 2 0 0022 17V5a2 2 0 00-1.999-2L16 3.002A5 5 0 0012 5a5 5 0 00-4-2H4a2 2 0 00-2 2v12a2 2 0 001.999 2H8a5 5 0 014 2 5 5 0 014-2z",
	key: "1fyvmf"
}]]);
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var ChartCandlestick = createLucideIcon("chart-candlestick", [
	["path", {
		d: "M9 5v4",
		key: "14uxtq"
	}],
	["rect", {
		width: "4",
		height: "6",
		x: "7",
		y: "9",
		rx: "1",
		key: "f4fvz0"
	}],
	["path", {
		d: "M9 15v2",
		key: "r5rk32"
	}],
	["path", {
		d: "M17 3v2",
		key: "1l2re6"
	}],
	["rect", {
		width: "4",
		height: "8",
		x: "15",
		y: "5",
		rx: "1",
		key: "z38je5"
	}],
	["path", {
		d: "M17 13v3",
		key: "5l0wba"
	}],
	["path", {
		d: "M3 3v16a2 2 0 0 0 2 2h16",
		key: "c24i48"
	}]
]);
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var Layers = createLucideIcon("layers", [
	["path", {
		d: "M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z",
		key: "zw3jo"
	}],
	["path", {
		d: "M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12",
		key: "1wduqc"
	}],
	["path", {
		d: "M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17",
		key: "kqbvx6"
	}]
]);
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var Settings2 = createLucideIcon("settings-2", [
	["path", {
		d: "M14 17H5",
		key: "gfn3mx"
	}],
	["path", {
		d: "M19 7h-9",
		key: "6i9tg"
	}],
	["circle", {
		cx: "17",
		cy: "17",
		r: "3",
		key: "18b49y"
	}],
	["circle", {
		cx: "7",
		cy: "7",
		r: "3",
		key: "dfmy0x"
	}]
]);
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var SlidersHorizontal = createLucideIcon("sliders-horizontal", [
	["path", {
		d: "M10 5H3",
		key: "1qgfaw"
	}],
	["path", {
		d: "M12 19H3",
		key: "yhmn1j"
	}],
	["path", {
		d: "M14 3v4",
		key: "1sua03"
	}],
	["path", {
		d: "M16 17v4",
		key: "1q0r14"
	}],
	["path", {
		d: "M21 12h-9",
		key: "1o4lsq"
	}],
	["path", {
		d: "M21 19h-5",
		key: "1rlt1p"
	}],
	["path", {
		d: "M21 5h-7",
		key: "1oszz2"
	}],
	["path", {
		d: "M8 10v4",
		key: "tgpxqk"
	}],
	["path", {
		d: "M8 12H3",
		key: "a7s4jb"
	}]
]);
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var Star = createLucideIcon("star", [["path", {
	d: "M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z",
	key: "r04s7s"
}]]);
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var TrendingUp = createLucideIcon("trending-up", [["path", {
	d: "M16 7h6v6",
	key: "box55l"
}], ["path", {
	d: "m22 7-8.5 8.5-5-5L2 17",
	key: "1t1m79"
}]]);
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var Workflow = createLucideIcon("workflow", [
	["rect", {
		width: "8",
		height: "8",
		x: "3",
		y: "3",
		rx: "2",
		key: "by2w9f"
	}],
	["path", {
		d: "M7 11v4a2 2 0 0 0 2 2h4",
		key: "xkn7yn"
	}],
	["rect", {
		width: "8",
		height: "8",
		x: "13",
		y: "13",
		rx: "2",
		key: "1cgmvn"
	}]
]);
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/mergeObjects.mjs
function mergeObjects(a, b) {
	if (a && !b) return a;
	if (!a && b) return b;
	if (a || b) return {
		...a,
		...b
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/merge-props/mergeProps.mjs
var EMPTY_PROPS = {};
/**
* Merges multiple sets of React props. It follows the Object.assign pattern where the rightmost object's fields overwrite
* the conflicting ones from others. This doesn't apply to event handlers, `className` and `style` props.
*
* Event handlers are merged and called in right-to-left order (rightmost handler executes first, leftmost last).
* For React synthetic events, the rightmost handler can prevent prior (left-positioned) handlers from executing
* by calling `event.preventBaseUIHandler()`. For non-synthetic events (custom events with primitive/object values),
* all handlers always execute without prevention capability.
*
* The `className` prop is merged by concatenating classes in right-to-left order (rightmost class appears first in the string).
* The `style` prop is merged with rightmost styles overwriting the prior ones.
*
* Props can either be provided as objects or as functions that take the previous props as an argument.
* The function will receive the merged props up to that point (going from left to right):
* so in the case of `(obj1, obj2, fn, obj3)`, `fn` will receive the merged props of `obj1` and `obj2`.
* The function is responsible for chaining event handlers if needed (that is, we don't run the merge logic).
*
* Event handlers returned by the functions are not automatically prevented when `preventBaseUIHandler` is called.
* They must check `event.baseUIHandlerPrevented` themselves and bail out if it's true.
*
* @important **`ref` is not merged.**
* @param a Props object to merge.
* @param b Props object to merge. The function will overwrite conflicting props from `a`.
* @param c Props object to merge. The function will overwrite conflicting props from previous parameters.
* @param d Props object to merge. The function will overwrite conflicting props from previous parameters.
* @param e Props object to merge. The function will overwrite conflicting props from previous parameters.
* @returns The merged props.
* @public
*/
function mergeProps(a, b, c, d, e) {
	if (!c && !d && !e && !a) return createInitialMergedProps(b);
	let merged = createInitialMergedProps(a);
	if (b) merged = mergeInto(merged, b);
	if (c) merged = mergeInto(merged, c);
	if (d) merged = mergeInto(merged, d);
	if (e) merged = mergeInto(merged, e);
	return merged;
}
/**
* Merges an arbitrary number of React props using the same logic as {@link mergeProps}.
* This function accepts an array of props instead of individual arguments.
*
* This has slightly lower performance than {@link mergeProps} due to accepting an array
* instead of a fixed number of arguments. Prefer {@link mergeProps} when merging 5 or
* fewer prop sets for better performance.
*
* @param props Array of props to merge.
* @returns The merged props.
* @see mergeProps
* @public
*/
function mergePropsN(props) {
	if (props.length === 0) return EMPTY_PROPS;
	if (props.length === 1) return createInitialMergedProps(props[0]);
	let merged = createInitialMergedProps(props[0]);
	for (let i = 1; i < props.length; i += 1) merged = mergeInto(merged, props[i]);
	return merged;
}
function createInitialMergedProps(inputProps) {
	if (isPropsGetter(inputProps)) return { ...resolvePropsGetter(inputProps, EMPTY_PROPS) };
	return copyInitialProps(inputProps);
}
function mergeInto(merged, inputProps) {
	if (isPropsGetter(inputProps)) return resolvePropsGetter(inputProps, merged);
	return mutablyMergeInto(merged, inputProps);
}
function copyInitialProps(inputProps) {
	const copiedProps = { ...inputProps };
	for (const propName in copiedProps) {
		const propValue = copiedProps[propName];
		if (isEventHandler(propName, propValue)) copiedProps[propName] = wrapEventHandler(propValue);
	}
	return copiedProps;
}
/**
* Merges two sets of props. In case of conflicts, the external props take precedence.
*/
function mutablyMergeInto(mergedProps, externalProps) {
	if (!externalProps) return mergedProps;
	for (const propName in externalProps) {
		const externalPropValue = externalProps[propName];
		switch (propName) {
			case "style":
				mergedProps[propName] = mergeObjects(mergedProps.style, externalPropValue);
				break;
			case "className":
				mergedProps[propName] = mergeClassNames(mergedProps.className, externalPropValue);
				break;
			default: if (isEventHandler(propName, externalPropValue)) mergedProps[propName] = mergeEventHandlers(mergedProps[propName], externalPropValue);
			else mergedProps[propName] = externalPropValue;
		}
	}
	return mergedProps;
}
function isEventHandler(key, value) {
	const code0 = key.charCodeAt(0);
	const code1 = key.charCodeAt(1);
	const code2 = key.charCodeAt(2);
	return code0 === 111 && code1 === 110 && code2 >= 65 && code2 <= 90 && (typeof value === "function" || typeof value === "undefined");
}
function isPropsGetter(inputProps) {
	return typeof inputProps === "function";
}
function resolvePropsGetter(inputProps, previousProps) {
	if (isPropsGetter(inputProps)) return inputProps(previousProps);
	return inputProps ?? EMPTY_PROPS;
}
function mergeEventHandlers(ourHandler, theirHandler) {
	if (!theirHandler) return ourHandler;
	if (!ourHandler) return wrapEventHandler(theirHandler);
	return (...args) => {
		const event = args[0];
		if (isSyntheticEvent(event)) {
			const baseUIEvent = event;
			makeEventPreventable(baseUIEvent);
			const result = theirHandler(...args);
			if (!baseUIEvent.baseUIHandlerPrevented) ourHandler?.(...args);
			return result;
		}
		const result = theirHandler(...args);
		ourHandler?.(...args);
		return result;
	};
}
function wrapEventHandler(handler) {
	if (!handler) return handler;
	return (...args) => {
		const event = args[0];
		if (isSyntheticEvent(event)) makeEventPreventable(event);
		return handler(...args);
	};
}
function makeEventPreventable(event) {
	event.preventBaseUIHandler = () => {
		event.baseUIHandlerPrevented = true;
	};
	return event;
}
function mergeClassNames(ourClassName, theirClassName) {
	if (theirClassName) {
		if (ourClassName) return theirClassName + " " + ourClassName;
		return theirClassName;
	}
	return ourClassName;
}
function isSyntheticEvent(event) {
	return event != null && typeof event === "object" && "nativeEvent" in event;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/formatErrorMessage.mjs
/**
* Creates a formatErrorMessage function with a custom URL and prefix.
* @param baseUrl - The base URL for the error page (e.g., 'https://base-ui.com/production-error')
* @param prefix - The prefix for the error message (e.g., 'Base UI')
* @returns A function that formats error messages with the given URL and prefix
*/
function createFormatErrorMessage(baseUrl, prefix) {
	return function formatErrorMessage(code, ...args) {
		const url = new URL(baseUrl);
		url.searchParams.set("code", code.toString());
		args.forEach((arg) => url.searchParams.append("args[]", arg));
		return `${prefix} error #${code}; visit ${url} for the full message.`;
	};
}
/**
* WARNING: Don't import this directly. It's imported by the code generated by
* `@mui/internal-babel-plugin-minify-errors`. Make sure to always use string literals in `Error`
* constructors to ensure the plugin works as expected. Supported patterns include:
*   throw new Error('My message');
*   throw new Error(`My message: ${foo}`);
*   throw new Error(`My message: ${foo}` + 'another string');
*   ...
*/
var formatErrorMessage = createFormatErrorMessage("https://base-ui.com/production-error", "Base UI");
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/useRefWithInit.mjs
var UNINITIALIZED = {};
/**
* A React.useRef() that is initialized with a function. Note that it accepts an optional
* initialization argument, so the initialization function doesn't need to be an inline closure.
*
* @usage
*   const ref = useRefWithInit(sortColumns, columns)
*/
function useRefWithInit(init, initArg) {
	const ref = React$3.useRef(UNINITIALIZED);
	if (ref.current === UNINITIALIZED) ref.current = init(initArg);
	return ref;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/useMergedRefs.mjs
/**
* Merges refs into a single memoized callback ref or `null`.
* This makes sure multiple refs are updated together and have the same value.
*
* This function accepts up to four refs. If you need to merge more, or have an unspecified number of refs to merge,
* use `useMergedRefsN` instead.
*/
function useMergedRefs(a, b, c, d) {
	const forkRef = useRefWithInit(createForkRef).current;
	if (didChange(forkRef, a, b, c, d)) update(forkRef, [
		a,
		b,
		c,
		d
	]);
	return forkRef.callback;
}
/**
* Merges an array of refs into a single memoized callback ref or `null`.
*
* If you need to merge a fixed number (up to four) of refs, use `useMergedRefs` instead for better performance.
*/
function useMergedRefsN(refs) {
	const forkRef = useRefWithInit(createForkRef).current;
	if (didChangeN(forkRef, refs)) update(forkRef, refs);
	return forkRef.callback;
}
function createForkRef() {
	return {
		callback: null,
		cleanup: null,
		refs: []
	};
}
function didChange(forkRef, a, b, c, d) {
	return forkRef.refs[0] !== a || forkRef.refs[1] !== b || forkRef.refs[2] !== c || forkRef.refs[3] !== d;
}
function didChangeN(forkRef, newRefs) {
	return forkRef.refs.length !== newRefs.length || forkRef.refs.some((ref, index) => ref !== newRefs[index]);
}
function update(forkRef, refs) {
	forkRef.refs = refs;
	if (refs.every((ref) => ref == null)) {
		forkRef.callback = null;
		return;
	}
	forkRef.callback = (instance) => {
		if (forkRef.cleanup) {
			forkRef.cleanup();
			forkRef.cleanup = null;
		}
		if (instance != null) {
			const cleanupCallbacks = Array(refs.length).fill(null);
			for (let i = 0; i < refs.length; i += 1) {
				const ref = refs[i];
				if (ref == null) continue;
				switch (typeof ref) {
					case "function": {
						const refCleanup = ref(instance);
						if (typeof refCleanup === "function") cleanupCallbacks[i] = refCleanup;
						break;
					}
					case "object":
						ref.current = instance;
						break;
					default:
				}
			}
			forkRef.cleanup = () => {
				for (let i = 0; i < refs.length; i += 1) {
					const ref = refs[i];
					if (ref == null) continue;
					switch (typeof ref) {
						case "function": {
							const cleanupCallback = cleanupCallbacks[i];
							if (typeof cleanupCallback === "function") cleanupCallback();
							else ref(null);
							break;
						}
						case "object":
							ref.current = null;
							break;
						default:
					}
				}
			};
		}
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/reactVersion.mjs
var majorVersion = parseInt(React$3.version, 10);
function isReactVersionAtLeast(reactVersionToCheck) {
	return majorVersion >= reactVersionToCheck;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/getReactElementRef.mjs
/**
* Extracts the `ref` from a React element, handling different React versions.
*/
function getReactElementRef(element) {
	if (!/* @__PURE__ */ React$3.isValidElement(element)) return null;
	const reactElement = element;
	const propsWithRef = reactElement.props;
	return (isReactVersionAtLeast(19) ? propsWithRef?.ref : reactElement.ref) ?? null;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/empty.mjs
function NOOP() {}
var EMPTY_ARRAY$1 = Object.freeze([]);
var EMPTY_OBJECT = Object.freeze({});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/getStateAttributesProps.mjs
function getStateAttributesProps(state, customMapping) {
	const props = {};
	for (const key in state) {
		const value = state[key];
		if (customMapping?.hasOwnProperty(key)) {
			const customProps = customMapping[key](value);
			if (customProps != null) Object.assign(props, customProps);
			continue;
		}
		if (value === true) props[`data-${key.toLowerCase()}`] = "";
		else if (value) props[`data-${key.toLowerCase()}`] = value.toString();
	}
	return props;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/resolveClassName.mjs
/**
* If the provided className is a string, it will be returned as is.
* Otherwise, the function will call the className function with the state as the first argument.
*
* @param className
* @param state
*/
function resolveClassName(className, state) {
	return typeof className === "function" ? className(state) : className;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/resolveStyle.mjs
/**
* If the provided style is an object, it will be returned as is.
* Otherwise, the function will call the style function with the state as the first argument.
*
* @param style
* @param state
*/
function resolveStyle(style, state) {
	return typeof style === "function" ? style(state) : style;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/useRenderElement.mjs
/**
* Renders a Base UI element.
*
* @param element The default HTML element to render. Can be overridden by the `render` prop.
* @param componentProps An object containing the `render` and `className` props to be used for element customization. Other props are ignored.
* @param params Additional parameters for rendering the element.
*/
function useRenderElement(element, componentProps, params = {}) {
	const renderProp = componentProps.render;
	const outProps = useRenderElementProps(componentProps, params);
	if (params.enabled === false) return null;
	return evaluateRenderProp(element, renderProp, outProps, params.state ?? EMPTY_OBJECT);
}
/**
* Computes render element final props.
*/
function useRenderElementProps(componentProps, params = {}) {
	const { className: classNameProp, style: styleProp, render: renderProp } = componentProps;
	const { state = EMPTY_OBJECT, ref, props, stateAttributesMapping, enabled = true } = params;
	const className = enabled ? resolveClassName(classNameProp, state) : void 0;
	const style = enabled ? resolveStyle(styleProp, state) : void 0;
	const stateProps = enabled ? getStateAttributesProps(state, stateAttributesMapping) : EMPTY_OBJECT;
	const resolvedProps = enabled && props ? resolveRenderFunctionProps(props) : void 0;
	const outProps = enabled ? mergeObjects(stateProps, resolvedProps) ?? {} : EMPTY_OBJECT;
	if (typeof document !== "undefined") if (!enabled) useMergedRefs(null, null);
	else if (Array.isArray(ref)) outProps.ref = useMergedRefsN([
		outProps.ref,
		getReactElementRef(renderProp),
		...ref
	]);
	else outProps.ref = useMergedRefs(outProps.ref, getReactElementRef(renderProp), ref);
	if (!enabled) return EMPTY_OBJECT;
	if (className !== void 0) outProps.className = mergeClassNames(outProps.className, className);
	if (style !== void 0) outProps.style = mergeObjects(outProps.style, style);
	return outProps;
}
function resolveRenderFunctionProps(props) {
	if (Array.isArray(props)) return mergePropsN(props);
	return mergeProps(void 0, props);
}
var REACT_LAZY_TYPE = Symbol.for("react.lazy");
function evaluateRenderProp(element, render, props, state) {
	if (render) {
		if (typeof render === "function") return render(props, state);
		const mergedProps = mergeProps(props, render.props);
		mergedProps.ref = props.ref;
		let newElement = render;
		if (newElement?.$$typeof === REACT_LAZY_TYPE) newElement = React$3.Children.toArray(render)[0];
		return /* @__PURE__ */ React$3.cloneElement(newElement, mergedProps);
	}
	if (element) {
		if (typeof element === "string") return renderTag(element, props);
	}
	throw new Error(formatErrorMessage(8));
}
function renderTag(Tag, props) {
	if (Tag === "button") return /* @__PURE__ */ createElement("button", {
		type: "button",
		...props,
		key: props.key
	});
	if (Tag === "img") return /* @__PURE__ */ createElement("img", {
		alt: "",
		...props,
		key: props.key
	});
	return /* @__PURE__ */ React$3.createElement(Tag, props);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/use-render/useRender.mjs
/**
* Renders a Base UI element.
*
* @public
*/
function useRender(params) {
	return useRenderElement(params.defaultTagName ?? "div", params, params);
}
//#endregion
//#region ../../../node_modules/.pnpm/clsx@2.1.1/node_modules/clsx/dist/clsx.mjs
function r(e) {
	var t, f, n = "";
	if ("string" == typeof e || "number" == typeof e) n += e;
	else if ("object" == typeof e) if (Array.isArray(e)) {
		var o = e.length;
		for (t = 0; t < o; t++) e[t] && (f = r(e[t])) && (n && (n += " "), n += f);
	} else for (f in e) e[f] && (n && (n += " "), n += f);
	return n;
}
function clsx() {
	for (var e, t, f = 0, n = "", o = arguments.length; f < o; f++) (e = arguments[f]) && (t = r(e)) && (n && (n += " "), n += t);
	return n;
}
//#endregion
//#region ../../../node_modules/.pnpm/class-variance-authority@0.7.1/node_modules/class-variance-authority/dist/index.mjs
/**
* Copyright 2022 Joe Bell. All rights reserved.
*
* This file is licensed to you under the Apache License, Version 2.0
* (the "License"); you may not use this file except in compliance with the
* License. You may obtain a copy of the License at
*
*   http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
* WARRANTIES OR REPRESENTATIONS OF ANY KIND, either express or implied. See the
* License for the specific language governing permissions and limitations under
* the License.
*/ var falsyToString = (value) => typeof value === "boolean" ? `${value}` : value === 0 ? "0" : value;
var cx = clsx;
var cva = (base, config) => (props) => {
	var _config_compoundVariants;
	if ((config === null || config === void 0 ? void 0 : config.variants) == null) return cx(base, props === null || props === void 0 ? void 0 : props.class, props === null || props === void 0 ? void 0 : props.className);
	const { variants, defaultVariants } = config;
	const getVariantClassNames = Object.keys(variants).map((variant) => {
		const variantProp = props === null || props === void 0 ? void 0 : props[variant];
		const defaultVariantProp = defaultVariants === null || defaultVariants === void 0 ? void 0 : defaultVariants[variant];
		if (variantProp === null) return null;
		const variantKey = falsyToString(variantProp) || falsyToString(defaultVariantProp);
		return variants[variant][variantKey];
	});
	const propsWithoutUndefined = props && Object.entries(props).reduce((acc, param) => {
		let [key, value] = param;
		if (value === void 0) return acc;
		acc[key] = value;
		return acc;
	}, {});
	return cx(base, getVariantClassNames, config === null || config === void 0 ? void 0 : (_config_compoundVariants = config.compoundVariants) === null || _config_compoundVariants === void 0 ? void 0 : _config_compoundVariants.reduce((acc, param) => {
		let { class: cvClass, className: cvClassName, ...compoundVariantOptions } = param;
		return Object.entries(compoundVariantOptions).every((param) => {
			let [key, value] = param;
			return Array.isArray(value) ? value.includes({
				...defaultVariants,
				...propsWithoutUndefined
			}[key]) : {
				...defaultVariants,
				...propsWithoutUndefined
			}[key] === value;
		}) ? [
			...acc,
			cvClass,
			cvClassName
		] : acc;
	}, []), props === null || props === void 0 ? void 0 : props.class, props === null || props === void 0 ? void 0 : props.className);
};
//#endregion
//#region hooks/use-mobile.ts
var MOBILE_BREAKPOINT = 768;
function useIsMobile() {
	const [isMobile, setIsMobile] = React$3.useState(void 0);
	React$3.useEffect(() => {
		const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);
		const onChange = () => {
			setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
		};
		mql.addEventListener("change", onChange);
		setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
		return () => mql.removeEventListener("change", onChange);
	}, []);
	return !!isMobile;
}
//#endregion
//#region ../../../node_modules/.pnpm/tailwind-merge@3.6.0/node_modules/tailwind-merge/dist/bundle-mjs.mjs
/**
* Concatenates two arrays faster than the array spread operator.
*/
var concatArrays = (array1, array2) => {
	const combinedArray = new Array(array1.length + array2.length);
	for (let i = 0; i < array1.length; i++) combinedArray[i] = array1[i];
	for (let i = 0; i < array2.length; i++) combinedArray[array1.length + i] = array2[i];
	return combinedArray;
};
var createClassValidatorObject = (classGroupId, validator) => ({
	classGroupId,
	validator
});
var createClassPartObject = (nextPart = /* @__PURE__ */ new Map(), validators = null, classGroupId) => ({
	nextPart,
	validators,
	classGroupId
});
var CLASS_PART_SEPARATOR = "-";
var EMPTY_CONFLICTS = [];
var ARBITRARY_PROPERTY_PREFIX = "arbitrary..";
var createClassGroupUtils = (config) => {
	const classMap = createClassMap(config);
	const { conflictingClassGroups, conflictingClassGroupModifiers } = config;
	const getClassGroupId = (className) => {
		if (className.startsWith("[") && className.endsWith("]")) return getGroupIdForArbitraryProperty(className);
		const classParts = className.split(CLASS_PART_SEPARATOR);
		return getGroupRecursive(classParts, classParts[0] === "" && classParts.length > 1 ? 1 : 0, classMap);
	};
	const getConflictingClassGroupIds = (classGroupId, hasPostfixModifier) => {
		if (hasPostfixModifier) {
			const modifierConflicts = conflictingClassGroupModifiers[classGroupId];
			const baseConflicts = conflictingClassGroups[classGroupId];
			if (modifierConflicts) {
				if (baseConflicts) return concatArrays(baseConflicts, modifierConflicts);
				return modifierConflicts;
			}
			return baseConflicts || EMPTY_CONFLICTS;
		}
		return conflictingClassGroups[classGroupId] || EMPTY_CONFLICTS;
	};
	return {
		getClassGroupId,
		getConflictingClassGroupIds
	};
};
var getGroupRecursive = (classParts, startIndex, classPartObject) => {
	if (classParts.length - startIndex === 0) return classPartObject.classGroupId;
	const currentClassPart = classParts[startIndex];
	const nextClassPartObject = classPartObject.nextPart.get(currentClassPart);
	if (nextClassPartObject) {
		const result = getGroupRecursive(classParts, startIndex + 1, nextClassPartObject);
		if (result) return result;
	}
	const validators = classPartObject.validators;
	if (validators === null) return;
	const classRest = startIndex === 0 ? classParts.join(CLASS_PART_SEPARATOR) : classParts.slice(startIndex).join(CLASS_PART_SEPARATOR);
	const validatorsLength = validators.length;
	for (let i = 0; i < validatorsLength; i++) {
		const validatorObj = validators[i];
		if (validatorObj.validator(classRest)) return validatorObj.classGroupId;
	}
};
/**
* Get the class group ID for an arbitrary property.
*
* @param className - The class name to get the group ID for. Is expected to be string starting with `[` and ending with `]`.
*/
var getGroupIdForArbitraryProperty = (className) => className.slice(1, -1).indexOf(":") === -1 ? void 0 : (() => {
	const content = className.slice(1, -1);
	const colonIndex = content.indexOf(":");
	const property = content.slice(0, colonIndex);
	return property ? ARBITRARY_PROPERTY_PREFIX + property : void 0;
})();
/**
* Exported for testing only
*/
var createClassMap = (config) => {
	const { theme, classGroups } = config;
	return processClassGroups(classGroups, theme);
};
var processClassGroups = (classGroups, theme) => {
	const classMap = createClassPartObject();
	for (const classGroupId in classGroups) {
		const group = classGroups[classGroupId];
		processClassesRecursively(group, classMap, classGroupId, theme);
	}
	return classMap;
};
var processClassesRecursively = (classGroup, classPartObject, classGroupId, theme) => {
	const len = classGroup.length;
	for (let i = 0; i < len; i++) {
		const classDefinition = classGroup[i];
		processClassDefinition(classDefinition, classPartObject, classGroupId, theme);
	}
};
var processClassDefinition = (classDefinition, classPartObject, classGroupId, theme) => {
	if (typeof classDefinition === "string") {
		processStringDefinition(classDefinition, classPartObject, classGroupId);
		return;
	}
	if (typeof classDefinition === "function") {
		processFunctionDefinition(classDefinition, classPartObject, classGroupId, theme);
		return;
	}
	processObjectDefinition(classDefinition, classPartObject, classGroupId, theme);
};
var processStringDefinition = (classDefinition, classPartObject, classGroupId) => {
	const classPartObjectToEdit = classDefinition === "" ? classPartObject : getPart(classPartObject, classDefinition);
	classPartObjectToEdit.classGroupId = classGroupId;
};
var processFunctionDefinition = (classDefinition, classPartObject, classGroupId, theme) => {
	if (isThemeGetter(classDefinition)) {
		processClassesRecursively(classDefinition(theme), classPartObject, classGroupId, theme);
		return;
	}
	if (classPartObject.validators === null) classPartObject.validators = [];
	classPartObject.validators.push(createClassValidatorObject(classGroupId, classDefinition));
};
var processObjectDefinition = (classDefinition, classPartObject, classGroupId, theme) => {
	const entries = Object.entries(classDefinition);
	const len = entries.length;
	for (let i = 0; i < len; i++) {
		const [key, value] = entries[i];
		processClassesRecursively(value, getPart(classPartObject, key), classGroupId, theme);
	}
};
var getPart = (classPartObject, path) => {
	let current = classPartObject;
	const parts = path.split(CLASS_PART_SEPARATOR);
	const len = parts.length;
	for (let i = 0; i < len; i++) {
		const part = parts[i];
		let next = current.nextPart.get(part);
		if (!next) {
			next = createClassPartObject();
			current.nextPart.set(part, next);
		}
		current = next;
	}
	return current;
};
var isThemeGetter = (func) => "isThemeGetter" in func && func.isThemeGetter === true;
var createLruCache = (maxCacheSize) => {
	if (maxCacheSize < 1) return {
		get: () => void 0,
		set: () => {}
	};
	let cacheSize = 0;
	let cache = Object.create(null);
	let previousCache = Object.create(null);
	const update = (key, value) => {
		cache[key] = value;
		cacheSize++;
		if (cacheSize > maxCacheSize) {
			cacheSize = 0;
			previousCache = cache;
			cache = Object.create(null);
		}
	};
	return {
		get(key) {
			let value = cache[key];
			if (value !== void 0) return value;
			if ((value = previousCache[key]) !== void 0) {
				update(key, value);
				return value;
			}
		},
		set(key, value) {
			if (key in cache) cache[key] = value;
			else update(key, value);
		}
	};
};
var IMPORTANT_MODIFIER = "!";
var MODIFIER_SEPARATOR = ":";
var EMPTY_MODIFIERS = [];
var createResultObject = (modifiers, hasImportantModifier, baseClassName, maybePostfixModifierPosition, isExternal) => ({
	modifiers,
	hasImportantModifier,
	baseClassName,
	maybePostfixModifierPosition,
	isExternal
});
var createParseClassName = (config) => {
	const { prefix, experimentalParseClassName } = config;
	/**
	* Parse class name into parts.
	*
	* Inspired by `splitAtTopLevelOnly` used in Tailwind CSS
	* @see https://github.com/tailwindlabs/tailwindcss/blob/v3.2.2/src/util/splitAtTopLevelOnly.js
	*/
	let parseClassName = (className) => {
		const modifiers = [];
		let bracketDepth = 0;
		let parenDepth = 0;
		let modifierStart = 0;
		let postfixModifierPosition;
		const len = className.length;
		for (let index = 0; index < len; index++) {
			const currentCharacter = className[index];
			if (bracketDepth === 0 && parenDepth === 0) {
				if (currentCharacter === MODIFIER_SEPARATOR) {
					modifiers.push(className.slice(modifierStart, index));
					modifierStart = index + 1;
					continue;
				}
				if (currentCharacter === "/") {
					postfixModifierPosition = index;
					continue;
				}
			}
			if (currentCharacter === "[") bracketDepth++;
			else if (currentCharacter === "]") bracketDepth--;
			else if (currentCharacter === "(") parenDepth++;
			else if (currentCharacter === ")") parenDepth--;
		}
		const baseClassNameWithImportantModifier = modifiers.length === 0 ? className : className.slice(modifierStart);
		let baseClassName = baseClassNameWithImportantModifier;
		let hasImportantModifier = false;
		if (baseClassNameWithImportantModifier.endsWith(IMPORTANT_MODIFIER)) {
			baseClassName = baseClassNameWithImportantModifier.slice(0, -1);
			hasImportantModifier = true;
		} else if (baseClassNameWithImportantModifier.startsWith(IMPORTANT_MODIFIER)) {
			baseClassName = baseClassNameWithImportantModifier.slice(1);
			hasImportantModifier = true;
		}
		const maybePostfixModifierPosition = postfixModifierPosition && postfixModifierPosition > modifierStart ? postfixModifierPosition - modifierStart : void 0;
		return createResultObject(modifiers, hasImportantModifier, baseClassName, maybePostfixModifierPosition);
	};
	if (prefix) {
		const fullPrefix = prefix + MODIFIER_SEPARATOR;
		const parseClassNameOriginal = parseClassName;
		parseClassName = (className) => className.startsWith(fullPrefix) ? parseClassNameOriginal(className.slice(fullPrefix.length)) : createResultObject(EMPTY_MODIFIERS, false, className, void 0, true);
	}
	if (experimentalParseClassName) {
		const parseClassNameOriginal = parseClassName;
		parseClassName = (className) => experimentalParseClassName({
			className,
			parseClassName: parseClassNameOriginal
		});
	}
	return parseClassName;
};
/**
* Sorts modifiers according to following schema:
* - Predefined modifiers are sorted alphabetically
* - When an arbitrary variant appears, it must be preserved which modifiers are before and after it
*/
var createSortModifiers = (config) => {
	const modifierWeights = /* @__PURE__ */ new Map();
	config.orderSensitiveModifiers.forEach((mod, index) => {
		modifierWeights.set(mod, 1e6 + index);
	});
	return (modifiers) => {
		const result = [];
		let currentSegment = [];
		for (let i = 0; i < modifiers.length; i++) {
			const modifier = modifiers[i];
			const isArbitrary = modifier[0] === "[";
			const isOrderSensitive = modifierWeights.has(modifier);
			if (isArbitrary || isOrderSensitive) {
				if (currentSegment.length > 0) {
					currentSegment.sort();
					result.push(...currentSegment);
					currentSegment = [];
				}
				result.push(modifier);
			} else currentSegment.push(modifier);
		}
		if (currentSegment.length > 0) {
			currentSegment.sort();
			result.push(...currentSegment);
		}
		return result;
	};
};
var createConfigUtils = (config) => ({
	cache: createLruCache(config.cacheSize),
	parseClassName: createParseClassName(config),
	sortModifiers: createSortModifiers(config),
	postfixLookupClassGroupIds: createPostfixLookupClassGroupIds(config),
	...createClassGroupUtils(config)
});
var createPostfixLookupClassGroupIds = (config) => {
	const lookup = Object.create(null);
	const classGroupIds = config.postfixLookupClassGroups;
	if (classGroupIds) for (let i = 0; i < classGroupIds.length; i++) lookup[classGroupIds[i]] = true;
	return lookup;
};
var SPLIT_CLASSES_REGEX = /\s+/;
var mergeClassList = (classList, configUtils) => {
	const { parseClassName, getClassGroupId, getConflictingClassGroupIds, sortModifiers, postfixLookupClassGroupIds } = configUtils;
	/**
	* Set of classGroupIds in following format:
	* `{importantModifier}{variantModifiers}{classGroupId}`
	* @example 'float'
	* @example 'hover:focus:bg-color'
	* @example 'md:!pr'
	*/
	const classGroupsInConflict = [];
	const classNames = classList.trim().split(SPLIT_CLASSES_REGEX);
	let result = "";
	for (let index = classNames.length - 1; index >= 0; index -= 1) {
		const originalClassName = classNames[index];
		const { isExternal, modifiers, hasImportantModifier, baseClassName, maybePostfixModifierPosition } = parseClassName(originalClassName);
		if (isExternal) {
			result = originalClassName + (result.length > 0 ? " " + result : result);
			continue;
		}
		let hasPostfixModifier = !!maybePostfixModifierPosition;
		let classGroupId;
		if (hasPostfixModifier) {
			classGroupId = getClassGroupId(baseClassName.substring(0, maybePostfixModifierPosition));
			const classGroupIdWithPostfix = classGroupId && postfixLookupClassGroupIds[classGroupId] ? getClassGroupId(baseClassName) : void 0;
			if (classGroupIdWithPostfix && classGroupIdWithPostfix !== classGroupId) {
				classGroupId = classGroupIdWithPostfix;
				hasPostfixModifier = false;
			}
		} else classGroupId = getClassGroupId(baseClassName);
		if (!classGroupId) {
			if (!hasPostfixModifier) {
				result = originalClassName + (result.length > 0 ? " " + result : result);
				continue;
			}
			classGroupId = getClassGroupId(baseClassName);
			if (!classGroupId) {
				result = originalClassName + (result.length > 0 ? " " + result : result);
				continue;
			}
			hasPostfixModifier = false;
		}
		const variantModifier = modifiers.length === 0 ? "" : modifiers.length === 1 ? modifiers[0] : sortModifiers(modifiers).join(":");
		const modifierId = hasImportantModifier ? variantModifier + IMPORTANT_MODIFIER : variantModifier;
		const classId = modifierId + classGroupId;
		if (classGroupsInConflict.indexOf(classId) > -1) continue;
		classGroupsInConflict.push(classId);
		const conflictGroups = getConflictingClassGroupIds(classGroupId, hasPostfixModifier);
		for (let i = 0; i < conflictGroups.length; ++i) {
			const group = conflictGroups[i];
			classGroupsInConflict.push(modifierId + group);
		}
		result = originalClassName + (result.length > 0 ? " " + result : result);
	}
	return result;
};
/**
* The code in this file is copied from https://github.com/lukeed/clsx and modified to suit the needs of tailwind-merge better.
*
* Specifically:
* - Runtime code from https://github.com/lukeed/clsx/blob/v1.2.1/src/index.js
* - TypeScript types from https://github.com/lukeed/clsx/blob/v1.2.1/clsx.d.ts
*
* Original code has MIT license: Copyright (c) Luke Edwards <luke.edwards05@gmail.com> (lukeed.com)
*/
var twJoin = (...classLists) => {
	let index = 0;
	let argument;
	let resolvedValue;
	let string = "";
	while (index < classLists.length) if (argument = classLists[index++]) {
		if (resolvedValue = toValue(argument)) {
			string && (string += " ");
			string += resolvedValue;
		}
	}
	return string;
};
var toValue = (mix) => {
	if (typeof mix === "string") return mix;
	let resolvedValue;
	let string = "";
	for (let k = 0; k < mix.length; k++) if (mix[k]) {
		if (resolvedValue = toValue(mix[k])) {
			string && (string += " ");
			string += resolvedValue;
		}
	}
	return string;
};
var createTailwindMerge = (createConfigFirst, ...createConfigRest) => {
	let configUtils;
	let cacheGet;
	let cacheSet;
	let functionToCall;
	const initTailwindMerge = (classList) => {
		configUtils = createConfigUtils(createConfigRest.reduce((previousConfig, createConfigCurrent) => createConfigCurrent(previousConfig), createConfigFirst()));
		cacheGet = configUtils.cache.get;
		cacheSet = configUtils.cache.set;
		functionToCall = tailwindMerge;
		return tailwindMerge(classList);
	};
	const tailwindMerge = (classList) => {
		const cachedResult = cacheGet(classList);
		if (cachedResult) return cachedResult;
		const result = mergeClassList(classList, configUtils);
		cacheSet(classList, result);
		return result;
	};
	functionToCall = initTailwindMerge;
	return (...args) => functionToCall(twJoin(...args));
};
var fallbackThemeArr = [];
var fromTheme = (key) => {
	const themeGetter = (theme) => theme[key] || fallbackThemeArr;
	themeGetter.isThemeGetter = true;
	return themeGetter;
};
var arbitraryValueRegex = /^\[(?:(\w[\w-]*):)?(.+)\]$/i;
var arbitraryVariableRegex = /^\((?:(\w[\w-]*):)?(.+)\)$/i;
var fractionRegex = /^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/;
var tshirtUnitRegex = /^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/;
var lengthUnitRegex = /\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/;
var colorFunctionRegex = /^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/;
var shadowRegex = /^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/;
var imageRegex = /^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/;
var isFraction = (value) => fractionRegex.test(value);
var isNumber = (value) => !!value && !Number.isNaN(Number(value));
var isInteger = (value) => !!value && Number.isInteger(Number(value));
var isPercent = (value) => value.endsWith("%") && isNumber(value.slice(0, -1));
var isTshirtSize = (value) => tshirtUnitRegex.test(value);
var isAny = () => true;
var isLengthOnly = (value) => lengthUnitRegex.test(value) && !colorFunctionRegex.test(value);
var isNever = () => false;
var isShadow = (value) => shadowRegex.test(value);
var isImage = (value) => imageRegex.test(value);
var isAnyNonArbitrary = (value) => !isArbitraryValue(value) && !isArbitraryVariable(value);
var isNamedContainerQuery = (value) => value.startsWith("@container") && (value[10] === "/" && value[11] !== void 0 || value[11] === "s" && value[16] !== void 0 && value.startsWith("-size/", 10) || value[11] === "n" && value[18] !== void 0 && value.startsWith("-normal/", 10));
var isArbitrarySize = (value) => getIsArbitraryValue(value, isLabelSize, isNever);
var isArbitraryValue = (value) => arbitraryValueRegex.test(value);
var isArbitraryLength = (value) => getIsArbitraryValue(value, isLabelLength, isLengthOnly);
var isArbitraryNumber = (value) => getIsArbitraryValue(value, isLabelNumber, isNumber);
var isArbitraryWeight = (value) => getIsArbitraryValue(value, isLabelWeight, isAny);
var isArbitraryFamilyName = (value) => getIsArbitraryValue(value, isLabelFamilyName, isNever);
var isArbitraryPosition = (value) => getIsArbitraryValue(value, isLabelPosition, isNever);
var isArbitraryImage = (value) => getIsArbitraryValue(value, isLabelImage, isImage);
var isArbitraryShadow = (value) => getIsArbitraryValue(value, isLabelShadow, isShadow);
var isArbitraryVariable = (value) => arbitraryVariableRegex.test(value);
var isArbitraryVariableLength = (value) => getIsArbitraryVariable(value, isLabelLength);
var isArbitraryVariableFamilyName = (value) => getIsArbitraryVariable(value, isLabelFamilyName);
var isArbitraryVariablePosition = (value) => getIsArbitraryVariable(value, isLabelPosition);
var isArbitraryVariableSize = (value) => getIsArbitraryVariable(value, isLabelSize);
var isArbitraryVariableImage = (value) => getIsArbitraryVariable(value, isLabelImage);
var isArbitraryVariableShadow = (value) => getIsArbitraryVariable(value, isLabelShadow, true);
var isArbitraryVariableWeight = (value) => getIsArbitraryVariable(value, isLabelWeight, true);
var getIsArbitraryValue = (value, testLabel, testValue) => {
	const result = arbitraryValueRegex.exec(value);
	if (result) {
		if (result[1]) return testLabel(result[1]);
		return testValue(result[2]);
	}
	return false;
};
var getIsArbitraryVariable = (value, testLabel, shouldMatchNoLabel = false) => {
	const result = arbitraryVariableRegex.exec(value);
	if (result) {
		if (result[1]) return testLabel(result[1]);
		return shouldMatchNoLabel;
	}
	return false;
};
var isLabelPosition = (label) => label === "position" || label === "percentage";
var isLabelImage = (label) => label === "image" || label === "url";
var isLabelSize = (label) => label === "length" || label === "size" || label === "bg-size";
var isLabelLength = (label) => label === "length";
var isLabelNumber = (label) => label === "number";
var isLabelFamilyName = (label) => label === "family-name";
var isLabelWeight = (label) => label === "number" || label === "weight";
var isLabelShadow = (label) => label === "shadow";
var getDefaultConfig = () => {
	/**
	* Theme getters for theme variable namespaces
	* @see https://tailwindcss.com/docs/theme#theme-variable-namespaces
	*/
	const themeColor = fromTheme("color");
	const themeFont = fromTheme("font");
	const themeText = fromTheme("text");
	const themeFontWeight = fromTheme("font-weight");
	const themeTracking = fromTheme("tracking");
	const themeLeading = fromTheme("leading");
	const themeBreakpoint = fromTheme("breakpoint");
	const themeContainer = fromTheme("container");
	const themeSpacing = fromTheme("spacing");
	const themeRadius = fromTheme("radius");
	const themeShadow = fromTheme("shadow");
	const themeInsetShadow = fromTheme("inset-shadow");
	const themeTextShadow = fromTheme("text-shadow");
	const themeDropShadow = fromTheme("drop-shadow");
	const themeBlur = fromTheme("blur");
	const themePerspective = fromTheme("perspective");
	const themeAspect = fromTheme("aspect");
	const themeEase = fromTheme("ease");
	const themeAnimate = fromTheme("animate");
	/**
	* Helpers to avoid repeating the same scales
	*
	* We use functions that create a new array every time they're called instead of static arrays.
	* This ensures that users who modify any scale by mutating the array (e.g. with `array.push(element)`) don't accidentally mutate arrays in other parts of the config.
	*/
	const scaleBreak = () => [
		"auto",
		"avoid",
		"all",
		"avoid-page",
		"page",
		"left",
		"right",
		"column"
	];
	const scalePosition = () => [
		"center",
		"top",
		"bottom",
		"left",
		"right",
		"top-left",
		"left-top",
		"top-right",
		"right-top",
		"bottom-right",
		"right-bottom",
		"bottom-left",
		"left-bottom"
	];
	const scalePositionWithArbitrary = () => [
		...scalePosition(),
		isArbitraryVariable,
		isArbitraryValue
	];
	const scaleOverflow = () => [
		"auto",
		"hidden",
		"clip",
		"visible",
		"scroll"
	];
	const scaleOverscroll = () => [
		"auto",
		"contain",
		"none"
	];
	const scaleUnambiguousSpacing = () => [
		isArbitraryVariable,
		isArbitraryValue,
		themeSpacing
	];
	const scaleInset = () => [
		isFraction,
		"full",
		"auto",
		...scaleUnambiguousSpacing()
	];
	const scaleGridTemplateColsRows = () => [
		isInteger,
		"none",
		"subgrid",
		isArbitraryVariable,
		isArbitraryValue
	];
	const scaleGridColRowStartAndEnd = () => [
		"auto",
		{ span: [
			"full",
			isInteger,
			isArbitraryVariable,
			isArbitraryValue
		] },
		isInteger,
		isArbitraryVariable,
		isArbitraryValue
	];
	const scaleGridColRowStartOrEnd = () => [
		isInteger,
		"auto",
		isArbitraryVariable,
		isArbitraryValue
	];
	const scaleGridAutoColsRows = () => [
		"auto",
		"min",
		"max",
		"fr",
		isArbitraryVariable,
		isArbitraryValue
	];
	const scaleAlignPrimaryAxis = () => [
		"start",
		"end",
		"center",
		"between",
		"around",
		"evenly",
		"stretch",
		"baseline",
		"center-safe",
		"end-safe"
	];
	const scaleAlignSecondaryAxis = () => [
		"start",
		"end",
		"center",
		"stretch",
		"center-safe",
		"end-safe"
	];
	const scaleMargin = () => ["auto", ...scaleUnambiguousSpacing()];
	const scaleSizing = () => [
		isFraction,
		"auto",
		"full",
		"dvw",
		"dvh",
		"lvw",
		"lvh",
		"svw",
		"svh",
		"min",
		"max",
		"fit",
		...scaleUnambiguousSpacing()
	];
	const scaleSizingInline = () => [
		isFraction,
		"screen",
		"full",
		"dvw",
		"lvw",
		"svw",
		"min",
		"max",
		"fit",
		...scaleUnambiguousSpacing()
	];
	const scaleSizingBlock = () => [
		isFraction,
		"screen",
		"full",
		"lh",
		"dvh",
		"lvh",
		"svh",
		"min",
		"max",
		"fit",
		...scaleUnambiguousSpacing()
	];
	const scaleColor = () => [
		themeColor,
		isArbitraryVariable,
		isArbitraryValue
	];
	const scaleBgPosition = () => [
		...scalePosition(),
		isArbitraryVariablePosition,
		isArbitraryPosition,
		{ position: [isArbitraryVariable, isArbitraryValue] }
	];
	const scaleBgRepeat = () => ["no-repeat", { repeat: [
		"",
		"x",
		"y",
		"space",
		"round"
	] }];
	const scaleBgSize = () => [
		"auto",
		"cover",
		"contain",
		isArbitraryVariableSize,
		isArbitrarySize,
		{ size: [isArbitraryVariable, isArbitraryValue] }
	];
	const scaleGradientStopPosition = () => [
		isPercent,
		isArbitraryVariableLength,
		isArbitraryLength
	];
	const scaleRadius = () => [
		"",
		"none",
		"full",
		themeRadius,
		isArbitraryVariable,
		isArbitraryValue
	];
	const scaleBorderWidth = () => [
		"",
		isNumber,
		isArbitraryVariableLength,
		isArbitraryLength
	];
	const scaleLineStyle = () => [
		"solid",
		"dashed",
		"dotted",
		"double"
	];
	const scaleBlendMode = () => [
		"normal",
		"multiply",
		"screen",
		"overlay",
		"darken",
		"lighten",
		"color-dodge",
		"color-burn",
		"hard-light",
		"soft-light",
		"difference",
		"exclusion",
		"hue",
		"saturation",
		"color",
		"luminosity"
	];
	const scaleMaskImagePosition = () => [
		isNumber,
		isPercent,
		isArbitraryVariablePosition,
		isArbitraryPosition
	];
	const scaleBlur = () => [
		"",
		"none",
		themeBlur,
		isArbitraryVariable,
		isArbitraryValue
	];
	const scaleRotate = () => [
		"none",
		isNumber,
		isArbitraryVariable,
		isArbitraryValue
	];
	const scaleScale = () => [
		"none",
		isNumber,
		isArbitraryVariable,
		isArbitraryValue
	];
	const scaleSkew = () => [
		isNumber,
		isArbitraryVariable,
		isArbitraryValue
	];
	const scaleTranslate = () => [
		isFraction,
		"full",
		...scaleUnambiguousSpacing()
	];
	return {
		cacheSize: 500,
		theme: {
			animate: [
				"spin",
				"ping",
				"pulse",
				"bounce"
			],
			aspect: ["video"],
			blur: [isTshirtSize],
			breakpoint: [isTshirtSize],
			color: [isAny],
			container: [isTshirtSize],
			"drop-shadow": [isTshirtSize],
			ease: [
				"in",
				"out",
				"in-out"
			],
			font: [isAnyNonArbitrary],
			"font-weight": [
				"thin",
				"extralight",
				"light",
				"normal",
				"medium",
				"semibold",
				"bold",
				"extrabold",
				"black"
			],
			"inset-shadow": [isTshirtSize],
			leading: [
				"none",
				"tight",
				"snug",
				"normal",
				"relaxed",
				"loose"
			],
			perspective: [
				"dramatic",
				"near",
				"normal",
				"midrange",
				"distant",
				"none"
			],
			radius: [isTshirtSize],
			shadow: [isTshirtSize],
			spacing: ["px", isNumber],
			text: [isTshirtSize],
			"text-shadow": [isTshirtSize],
			tracking: [
				"tighter",
				"tight",
				"normal",
				"wide",
				"wider",
				"widest"
			]
		},
		classGroups: {
			/**
			* Aspect Ratio
			* @see https://tailwindcss.com/docs/aspect-ratio
			*/
			aspect: [{ aspect: [
				"auto",
				"square",
				isFraction,
				isArbitraryValue,
				isArbitraryVariable,
				themeAspect
			] }],
			/**
			* Container
			* @see https://tailwindcss.com/docs/container
			* @deprecated since Tailwind CSS v4.0.0
			*/
			container: ["container"],
			/**
			* Container Type
			* @see https://tailwindcss.com/docs/responsive-design#container-queries
			*/
			"container-type": [{ "@container": [
				"",
				"normal",
				"size",
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Container Name
			* @see https://tailwindcss.com/docs/responsive-design#named-containers
			*/
			"container-named": [isNamedContainerQuery],
			/**
			* Columns
			* @see https://tailwindcss.com/docs/columns
			*/
			columns: [{ columns: [
				isNumber,
				isArbitraryValue,
				isArbitraryVariable,
				themeContainer
			] }],
			/**
			* Break After
			* @see https://tailwindcss.com/docs/break-after
			*/
			"break-after": [{ "break-after": scaleBreak() }],
			/**
			* Break Before
			* @see https://tailwindcss.com/docs/break-before
			*/
			"break-before": [{ "break-before": scaleBreak() }],
			/**
			* Break Inside
			* @see https://tailwindcss.com/docs/break-inside
			*/
			"break-inside": [{ "break-inside": [
				"auto",
				"avoid",
				"avoid-page",
				"avoid-column"
			] }],
			/**
			* Box Decoration Break
			* @see https://tailwindcss.com/docs/box-decoration-break
			*/
			"box-decoration": [{ "box-decoration": ["slice", "clone"] }],
			/**
			* Box Sizing
			* @see https://tailwindcss.com/docs/box-sizing
			*/
			box: [{ box: ["border", "content"] }],
			/**
			* Display
			* @see https://tailwindcss.com/docs/display
			*/
			display: [
				"block",
				"inline-block",
				"inline",
				"flex",
				"inline-flex",
				"table",
				"inline-table",
				"table-caption",
				"table-cell",
				"table-column",
				"table-column-group",
				"table-footer-group",
				"table-header-group",
				"table-row-group",
				"table-row",
				"flow-root",
				"grid",
				"inline-grid",
				"contents",
				"list-item",
				"hidden"
			],
			/**
			* Screen Reader Only
			* @see https://tailwindcss.com/docs/display#screen-reader-only
			*/
			sr: ["sr-only", "not-sr-only"],
			/**
			* Floats
			* @see https://tailwindcss.com/docs/float
			*/
			float: [{ float: [
				"right",
				"left",
				"none",
				"start",
				"end"
			] }],
			/**
			* Clear
			* @see https://tailwindcss.com/docs/clear
			*/
			clear: [{ clear: [
				"left",
				"right",
				"both",
				"none",
				"start",
				"end"
			] }],
			/**
			* Isolation
			* @see https://tailwindcss.com/docs/isolation
			*/
			isolation: ["isolate", "isolation-auto"],
			/**
			* Object Fit
			* @see https://tailwindcss.com/docs/object-fit
			*/
			"object-fit": [{ object: [
				"contain",
				"cover",
				"fill",
				"none",
				"scale-down"
			] }],
			/**
			* Object Position
			* @see https://tailwindcss.com/docs/object-position
			*/
			"object-position": [{ object: scalePositionWithArbitrary() }],
			/**
			* Overflow
			* @see https://tailwindcss.com/docs/overflow
			*/
			overflow: [{ overflow: scaleOverflow() }],
			/**
			* Overflow X
			* @see https://tailwindcss.com/docs/overflow
			*/
			"overflow-x": [{ "overflow-x": scaleOverflow() }],
			/**
			* Overflow Y
			* @see https://tailwindcss.com/docs/overflow
			*/
			"overflow-y": [{ "overflow-y": scaleOverflow() }],
			/**
			* Overscroll Behavior
			* @see https://tailwindcss.com/docs/overscroll-behavior
			*/
			overscroll: [{ overscroll: scaleOverscroll() }],
			/**
			* Overscroll Behavior X
			* @see https://tailwindcss.com/docs/overscroll-behavior
			*/
			"overscroll-x": [{ "overscroll-x": scaleOverscroll() }],
			/**
			* Overscroll Behavior Y
			* @see https://tailwindcss.com/docs/overscroll-behavior
			*/
			"overscroll-y": [{ "overscroll-y": scaleOverscroll() }],
			/**
			* Position
			* @see https://tailwindcss.com/docs/position
			*/
			position: [
				"static",
				"fixed",
				"absolute",
				"relative",
				"sticky"
			],
			/**
			* Inset
			* @see https://tailwindcss.com/docs/top-right-bottom-left
			*/
			inset: [{ inset: scaleInset() }],
			/**
			* Inset Inline
			* @see https://tailwindcss.com/docs/top-right-bottom-left
			*/
			"inset-x": [{ "inset-x": scaleInset() }],
			/**
			* Inset Block
			* @see https://tailwindcss.com/docs/top-right-bottom-left
			*/
			"inset-y": [{ "inset-y": scaleInset() }],
			/**
			* Inset Inline Start
			* @see https://tailwindcss.com/docs/top-right-bottom-left
			* @todo class group will be renamed to `inset-s` in next major release
			*/
			start: [{
				"inset-s": scaleInset(),
				/**
				* @deprecated since Tailwind CSS v4.2.0 in favor of `inset-s-*` utilities.
				* @see https://github.com/tailwindlabs/tailwindcss/pull/19613
				*/
				start: scaleInset()
			}],
			/**
			* Inset Inline End
			* @see https://tailwindcss.com/docs/top-right-bottom-left
			* @todo class group will be renamed to `inset-e` in next major release
			*/
			end: [{
				"inset-e": scaleInset(),
				/**
				* @deprecated since Tailwind CSS v4.2.0 in favor of `inset-e-*` utilities.
				* @see https://github.com/tailwindlabs/tailwindcss/pull/19613
				*/
				end: scaleInset()
			}],
			/**
			* Inset Block Start
			* @see https://tailwindcss.com/docs/top-right-bottom-left
			*/
			"inset-bs": [{ "inset-bs": scaleInset() }],
			/**
			* Inset Block End
			* @see https://tailwindcss.com/docs/top-right-bottom-left
			*/
			"inset-be": [{ "inset-be": scaleInset() }],
			/**
			* Top
			* @see https://tailwindcss.com/docs/top-right-bottom-left
			*/
			top: [{ top: scaleInset() }],
			/**
			* Right
			* @see https://tailwindcss.com/docs/top-right-bottom-left
			*/
			right: [{ right: scaleInset() }],
			/**
			* Bottom
			* @see https://tailwindcss.com/docs/top-right-bottom-left
			*/
			bottom: [{ bottom: scaleInset() }],
			/**
			* Left
			* @see https://tailwindcss.com/docs/top-right-bottom-left
			*/
			left: [{ left: scaleInset() }],
			/**
			* Visibility
			* @see https://tailwindcss.com/docs/visibility
			*/
			visibility: [
				"visible",
				"invisible",
				"collapse"
			],
			/**
			* Z-Index
			* @see https://tailwindcss.com/docs/z-index
			*/
			z: [{ z: [
				isInteger,
				"auto",
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Flex Basis
			* @see https://tailwindcss.com/docs/flex-basis
			*/
			basis: [{ basis: [
				isFraction,
				"full",
				"auto",
				themeContainer,
				...scaleUnambiguousSpacing()
			] }],
			/**
			* Flex Direction
			* @see https://tailwindcss.com/docs/flex-direction
			*/
			"flex-direction": [{ flex: [
				"row",
				"row-reverse",
				"col",
				"col-reverse"
			] }],
			/**
			* Flex Wrap
			* @see https://tailwindcss.com/docs/flex-wrap
			*/
			"flex-wrap": [{ flex: [
				"nowrap",
				"wrap",
				"wrap-reverse"
			] }],
			/**
			* Flex
			* @see https://tailwindcss.com/docs/flex
			*/
			flex: [{ flex: [
				isNumber,
				isFraction,
				"auto",
				"initial",
				"none",
				isArbitraryValue
			] }],
			/**
			* Flex Grow
			* @see https://tailwindcss.com/docs/flex-grow
			*/
			grow: [{ grow: [
				"",
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Flex Shrink
			* @see https://tailwindcss.com/docs/flex-shrink
			*/
			shrink: [{ shrink: [
				"",
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Order
			* @see https://tailwindcss.com/docs/order
			*/
			order: [{ order: [
				isInteger,
				"first",
				"last",
				"none",
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Grid Template Columns
			* @see https://tailwindcss.com/docs/grid-template-columns
			*/
			"grid-cols": [{ "grid-cols": scaleGridTemplateColsRows() }],
			/**
			* Grid Column Start / End
			* @see https://tailwindcss.com/docs/grid-column
			*/
			"col-start-end": [{ col: scaleGridColRowStartAndEnd() }],
			/**
			* Grid Column Start
			* @see https://tailwindcss.com/docs/grid-column
			*/
			"col-start": [{ "col-start": scaleGridColRowStartOrEnd() }],
			/**
			* Grid Column End
			* @see https://tailwindcss.com/docs/grid-column
			*/
			"col-end": [{ "col-end": scaleGridColRowStartOrEnd() }],
			/**
			* Grid Template Rows
			* @see https://tailwindcss.com/docs/grid-template-rows
			*/
			"grid-rows": [{ "grid-rows": scaleGridTemplateColsRows() }],
			/**
			* Grid Row Start / End
			* @see https://tailwindcss.com/docs/grid-row
			*/
			"row-start-end": [{ row: scaleGridColRowStartAndEnd() }],
			/**
			* Grid Row Start
			* @see https://tailwindcss.com/docs/grid-row
			*/
			"row-start": [{ "row-start": scaleGridColRowStartOrEnd() }],
			/**
			* Grid Row End
			* @see https://tailwindcss.com/docs/grid-row
			*/
			"row-end": [{ "row-end": scaleGridColRowStartOrEnd() }],
			/**
			* Grid Auto Flow
			* @see https://tailwindcss.com/docs/grid-auto-flow
			*/
			"grid-flow": [{ "grid-flow": [
				"row",
				"col",
				"dense",
				"row-dense",
				"col-dense"
			] }],
			/**
			* Grid Auto Columns
			* @see https://tailwindcss.com/docs/grid-auto-columns
			*/
			"auto-cols": [{ "auto-cols": scaleGridAutoColsRows() }],
			/**
			* Grid Auto Rows
			* @see https://tailwindcss.com/docs/grid-auto-rows
			*/
			"auto-rows": [{ "auto-rows": scaleGridAutoColsRows() }],
			/**
			* Gap
			* @see https://tailwindcss.com/docs/gap
			*/
			gap: [{ gap: scaleUnambiguousSpacing() }],
			/**
			* Gap X
			* @see https://tailwindcss.com/docs/gap
			*/
			"gap-x": [{ "gap-x": scaleUnambiguousSpacing() }],
			/**
			* Gap Y
			* @see https://tailwindcss.com/docs/gap
			*/
			"gap-y": [{ "gap-y": scaleUnambiguousSpacing() }],
			/**
			* Justify Content
			* @see https://tailwindcss.com/docs/justify-content
			*/
			"justify-content": [{ justify: [...scaleAlignPrimaryAxis(), "normal"] }],
			/**
			* Justify Items
			* @see https://tailwindcss.com/docs/justify-items
			*/
			"justify-items": [{ "justify-items": [...scaleAlignSecondaryAxis(), "normal"] }],
			/**
			* Justify Self
			* @see https://tailwindcss.com/docs/justify-self
			*/
			"justify-self": [{ "justify-self": ["auto", ...scaleAlignSecondaryAxis()] }],
			/**
			* Align Content
			* @see https://tailwindcss.com/docs/align-content
			*/
			"align-content": [{ content: ["normal", ...scaleAlignPrimaryAxis()] }],
			/**
			* Align Items
			* @see https://tailwindcss.com/docs/align-items
			*/
			"align-items": [{ items: [...scaleAlignSecondaryAxis(), { baseline: ["", "last"] }] }],
			/**
			* Align Self
			* @see https://tailwindcss.com/docs/align-self
			*/
			"align-self": [{ self: [
				"auto",
				...scaleAlignSecondaryAxis(),
				{ baseline: ["", "last"] }
			] }],
			/**
			* Place Content
			* @see https://tailwindcss.com/docs/place-content
			*/
			"place-content": [{ "place-content": scaleAlignPrimaryAxis() }],
			/**
			* Place Items
			* @see https://tailwindcss.com/docs/place-items
			*/
			"place-items": [{ "place-items": [...scaleAlignSecondaryAxis(), "baseline"] }],
			/**
			* Place Self
			* @see https://tailwindcss.com/docs/place-self
			*/
			"place-self": [{ "place-self": ["auto", ...scaleAlignSecondaryAxis()] }],
			/**
			* Padding
			* @see https://tailwindcss.com/docs/padding
			*/
			p: [{ p: scaleUnambiguousSpacing() }],
			/**
			* Padding Inline
			* @see https://tailwindcss.com/docs/padding
			*/
			px: [{ px: scaleUnambiguousSpacing() }],
			/**
			* Padding Block
			* @see https://tailwindcss.com/docs/padding
			*/
			py: [{ py: scaleUnambiguousSpacing() }],
			/**
			* Padding Inline Start
			* @see https://tailwindcss.com/docs/padding
			*/
			ps: [{ ps: scaleUnambiguousSpacing() }],
			/**
			* Padding Inline End
			* @see https://tailwindcss.com/docs/padding
			*/
			pe: [{ pe: scaleUnambiguousSpacing() }],
			/**
			* Padding Block Start
			* @see https://tailwindcss.com/docs/padding
			*/
			pbs: [{ pbs: scaleUnambiguousSpacing() }],
			/**
			* Padding Block End
			* @see https://tailwindcss.com/docs/padding
			*/
			pbe: [{ pbe: scaleUnambiguousSpacing() }],
			/**
			* Padding Top
			* @see https://tailwindcss.com/docs/padding
			*/
			pt: [{ pt: scaleUnambiguousSpacing() }],
			/**
			* Padding Right
			* @see https://tailwindcss.com/docs/padding
			*/
			pr: [{ pr: scaleUnambiguousSpacing() }],
			/**
			* Padding Bottom
			* @see https://tailwindcss.com/docs/padding
			*/
			pb: [{ pb: scaleUnambiguousSpacing() }],
			/**
			* Padding Left
			* @see https://tailwindcss.com/docs/padding
			*/
			pl: [{ pl: scaleUnambiguousSpacing() }],
			/**
			* Margin
			* @see https://tailwindcss.com/docs/margin
			*/
			m: [{ m: scaleMargin() }],
			/**
			* Margin Inline
			* @see https://tailwindcss.com/docs/margin
			*/
			mx: [{ mx: scaleMargin() }],
			/**
			* Margin Block
			* @see https://tailwindcss.com/docs/margin
			*/
			my: [{ my: scaleMargin() }],
			/**
			* Margin Inline Start
			* @see https://tailwindcss.com/docs/margin
			*/
			ms: [{ ms: scaleMargin() }],
			/**
			* Margin Inline End
			* @see https://tailwindcss.com/docs/margin
			*/
			me: [{ me: scaleMargin() }],
			/**
			* Margin Block Start
			* @see https://tailwindcss.com/docs/margin
			*/
			mbs: [{ mbs: scaleMargin() }],
			/**
			* Margin Block End
			* @see https://tailwindcss.com/docs/margin
			*/
			mbe: [{ mbe: scaleMargin() }],
			/**
			* Margin Top
			* @see https://tailwindcss.com/docs/margin
			*/
			mt: [{ mt: scaleMargin() }],
			/**
			* Margin Right
			* @see https://tailwindcss.com/docs/margin
			*/
			mr: [{ mr: scaleMargin() }],
			/**
			* Margin Bottom
			* @see https://tailwindcss.com/docs/margin
			*/
			mb: [{ mb: scaleMargin() }],
			/**
			* Margin Left
			* @see https://tailwindcss.com/docs/margin
			*/
			ml: [{ ml: scaleMargin() }],
			/**
			* Space Between X
			* @see https://tailwindcss.com/docs/margin#adding-space-between-children
			*/
			"space-x": [{ "space-x": scaleUnambiguousSpacing() }],
			/**
			* Space Between X Reverse
			* @see https://tailwindcss.com/docs/margin#adding-space-between-children
			*/
			"space-x-reverse": ["space-x-reverse"],
			/**
			* Space Between Y
			* @see https://tailwindcss.com/docs/margin#adding-space-between-children
			*/
			"space-y": [{ "space-y": scaleUnambiguousSpacing() }],
			/**
			* Space Between Y Reverse
			* @see https://tailwindcss.com/docs/margin#adding-space-between-children
			*/
			"space-y-reverse": ["space-y-reverse"],
			/**
			* Size
			* @see https://tailwindcss.com/docs/width#setting-both-width-and-height
			*/
			size: [{ size: scaleSizing() }],
			/**
			* Inline Size
			* @see https://tailwindcss.com/docs/width
			*/
			"inline-size": [{ inline: ["auto", ...scaleSizingInline()] }],
			/**
			* Min-Inline Size
			* @see https://tailwindcss.com/docs/min-width
			*/
			"min-inline-size": [{ "min-inline": ["auto", ...scaleSizingInline()] }],
			/**
			* Max-Inline Size
			* @see https://tailwindcss.com/docs/max-width
			*/
			"max-inline-size": [{ "max-inline": ["none", ...scaleSizingInline()] }],
			/**
			* Block Size
			* @see https://tailwindcss.com/docs/height
			*/
			"block-size": [{ block: ["auto", ...scaleSizingBlock()] }],
			/**
			* Min-Block Size
			* @see https://tailwindcss.com/docs/min-height
			*/
			"min-block-size": [{ "min-block": ["auto", ...scaleSizingBlock()] }],
			/**
			* Max-Block Size
			* @see https://tailwindcss.com/docs/max-height
			*/
			"max-block-size": [{ "max-block": ["none", ...scaleSizingBlock()] }],
			/**
			* Width
			* @see https://tailwindcss.com/docs/width
			*/
			w: [{ w: [
				themeContainer,
				"screen",
				...scaleSizing()
			] }],
			/**
			* Min-Width
			* @see https://tailwindcss.com/docs/min-width
			*/
			"min-w": [{ "min-w": [
				themeContainer,
				"screen",
				"none",
				...scaleSizing()
			] }],
			/**
			* Max-Width
			* @see https://tailwindcss.com/docs/max-width
			*/
			"max-w": [{ "max-w": [
				themeContainer,
				"screen",
				"none",
				"prose",
				{ screen: [themeBreakpoint] },
				...scaleSizing()
			] }],
			/**
			* Height
			* @see https://tailwindcss.com/docs/height
			*/
			h: [{ h: [
				"screen",
				"lh",
				...scaleSizing()
			] }],
			/**
			* Min-Height
			* @see https://tailwindcss.com/docs/min-height
			*/
			"min-h": [{ "min-h": [
				"screen",
				"lh",
				"none",
				...scaleSizing()
			] }],
			/**
			* Max-Height
			* @see https://tailwindcss.com/docs/max-height
			*/
			"max-h": [{ "max-h": [
				"screen",
				"lh",
				...scaleSizing()
			] }],
			/**
			* Font Size
			* @see https://tailwindcss.com/docs/font-size
			*/
			"font-size": [{ text: [
				"base",
				themeText,
				isArbitraryVariableLength,
				isArbitraryLength
			] }],
			/**
			* Font Smoothing
			* @see https://tailwindcss.com/docs/font-smoothing
			*/
			"font-smoothing": ["antialiased", "subpixel-antialiased"],
			/**
			* Font Style
			* @see https://tailwindcss.com/docs/font-style
			*/
			"font-style": ["italic", "not-italic"],
			/**
			* Font Weight
			* @see https://tailwindcss.com/docs/font-weight
			*/
			"font-weight": [{ font: [
				themeFontWeight,
				isArbitraryVariableWeight,
				isArbitraryWeight
			] }],
			/**
			* Font Stretch
			* @see https://tailwindcss.com/docs/font-stretch
			*/
			"font-stretch": [{ "font-stretch": [
				"ultra-condensed",
				"extra-condensed",
				"condensed",
				"semi-condensed",
				"normal",
				"semi-expanded",
				"expanded",
				"extra-expanded",
				"ultra-expanded",
				isPercent,
				isArbitraryValue
			] }],
			/**
			* Font Family
			* @see https://tailwindcss.com/docs/font-family
			*/
			"font-family": [{ font: [
				isArbitraryVariableFamilyName,
				isArbitraryFamilyName,
				themeFont
			] }],
			/**
			* Font Feature Settings
			* @see https://tailwindcss.com/docs/font-feature-settings
			*/
			"font-features": [{ "font-features": [isArbitraryValue] }],
			/**
			* Font Variant Numeric
			* @see https://tailwindcss.com/docs/font-variant-numeric
			*/
			"fvn-normal": ["normal-nums"],
			/**
			* Font Variant Numeric
			* @see https://tailwindcss.com/docs/font-variant-numeric
			*/
			"fvn-ordinal": ["ordinal"],
			/**
			* Font Variant Numeric
			* @see https://tailwindcss.com/docs/font-variant-numeric
			*/
			"fvn-slashed-zero": ["slashed-zero"],
			/**
			* Font Variant Numeric
			* @see https://tailwindcss.com/docs/font-variant-numeric
			*/
			"fvn-figure": ["lining-nums", "oldstyle-nums"],
			/**
			* Font Variant Numeric
			* @see https://tailwindcss.com/docs/font-variant-numeric
			*/
			"fvn-spacing": ["proportional-nums", "tabular-nums"],
			/**
			* Font Variant Numeric
			* @see https://tailwindcss.com/docs/font-variant-numeric
			*/
			"fvn-fraction": ["diagonal-fractions", "stacked-fractions"],
			/**
			* Letter Spacing
			* @see https://tailwindcss.com/docs/letter-spacing
			*/
			tracking: [{ tracking: [
				themeTracking,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Line Clamp
			* @see https://tailwindcss.com/docs/line-clamp
			*/
			"line-clamp": [{ "line-clamp": [
				isNumber,
				"none",
				isArbitraryVariable,
				isArbitraryNumber
			] }],
			/**
			* Line Height
			* @see https://tailwindcss.com/docs/line-height
			*/
			leading: [{ leading: [themeLeading, ...scaleUnambiguousSpacing()] }],
			/**
			* List Style Image
			* @see https://tailwindcss.com/docs/list-style-image
			*/
			"list-image": [{ "list-image": [
				"none",
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* List Style Position
			* @see https://tailwindcss.com/docs/list-style-position
			*/
			"list-style-position": [{ list: ["inside", "outside"] }],
			/**
			* List Style Type
			* @see https://tailwindcss.com/docs/list-style-type
			*/
			"list-style-type": [{ list: [
				"disc",
				"decimal",
				"none",
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Text Alignment
			* @see https://tailwindcss.com/docs/text-align
			*/
			"text-alignment": [{ text: [
				"left",
				"center",
				"right",
				"justify",
				"start",
				"end"
			] }],
			/**
			* Placeholder Color
			* @deprecated since Tailwind CSS v3.0.0
			* @see https://v3.tailwindcss.com/docs/placeholder-color
			*/
			"placeholder-color": [{ placeholder: scaleColor() }],
			/**
			* Text Color
			* @see https://tailwindcss.com/docs/text-color
			*/
			"text-color": [{ text: scaleColor() }],
			/**
			* Text Decoration
			* @see https://tailwindcss.com/docs/text-decoration
			*/
			"text-decoration": [
				"underline",
				"overline",
				"line-through",
				"no-underline"
			],
			/**
			* Text Decoration Style
			* @see https://tailwindcss.com/docs/text-decoration-style
			*/
			"text-decoration-style": [{ decoration: [...scaleLineStyle(), "wavy"] }],
			/**
			* Text Decoration Thickness
			* @see https://tailwindcss.com/docs/text-decoration-thickness
			*/
			"text-decoration-thickness": [{ decoration: [
				isNumber,
				"from-font",
				"auto",
				isArbitraryVariable,
				isArbitraryLength
			] }],
			/**
			* Text Decoration Color
			* @see https://tailwindcss.com/docs/text-decoration-color
			*/
			"text-decoration-color": [{ decoration: scaleColor() }],
			/**
			* Text Underline Offset
			* @see https://tailwindcss.com/docs/text-underline-offset
			*/
			"underline-offset": [{ "underline-offset": [
				isNumber,
				"auto",
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Text Transform
			* @see https://tailwindcss.com/docs/text-transform
			*/
			"text-transform": [
				"uppercase",
				"lowercase",
				"capitalize",
				"normal-case"
			],
			/**
			* Text Overflow
			* @see https://tailwindcss.com/docs/text-overflow
			*/
			"text-overflow": [
				"truncate",
				"text-ellipsis",
				"text-clip"
			],
			/**
			* Text Wrap
			* @see https://tailwindcss.com/docs/text-wrap
			*/
			"text-wrap": [{ text: [
				"wrap",
				"nowrap",
				"balance",
				"pretty"
			] }],
			/**
			* Text Indent
			* @see https://tailwindcss.com/docs/text-indent
			*/
			indent: [{ indent: scaleUnambiguousSpacing() }],
			/**
			* Tab Size
			* @see https://tailwindcss.com/docs/tab-size
			*/
			"tab-size": [{ tab: [
				isInteger,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Vertical Alignment
			* @see https://tailwindcss.com/docs/vertical-align
			*/
			"vertical-align": [{ align: [
				"baseline",
				"top",
				"middle",
				"bottom",
				"text-top",
				"text-bottom",
				"sub",
				"super",
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Whitespace
			* @see https://tailwindcss.com/docs/whitespace
			*/
			whitespace: [{ whitespace: [
				"normal",
				"nowrap",
				"pre",
				"pre-line",
				"pre-wrap",
				"break-spaces"
			] }],
			/**
			* Word Break
			* @see https://tailwindcss.com/docs/word-break
			*/
			break: [{ break: [
				"normal",
				"words",
				"all",
				"keep"
			] }],
			/**
			* Overflow Wrap
			* @see https://tailwindcss.com/docs/overflow-wrap
			*/
			wrap: [{ wrap: [
				"break-word",
				"anywhere",
				"normal"
			] }],
			/**
			* Hyphens
			* @see https://tailwindcss.com/docs/hyphens
			*/
			hyphens: [{ hyphens: [
				"none",
				"manual",
				"auto"
			] }],
			/**
			* Content
			* @see https://tailwindcss.com/docs/content
			*/
			content: [{ content: [
				"none",
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Background Attachment
			* @see https://tailwindcss.com/docs/background-attachment
			*/
			"bg-attachment": [{ bg: [
				"fixed",
				"local",
				"scroll"
			] }],
			/**
			* Background Clip
			* @see https://tailwindcss.com/docs/background-clip
			*/
			"bg-clip": [{ "bg-clip": [
				"border",
				"padding",
				"content",
				"text"
			] }],
			/**
			* Background Origin
			* @see https://tailwindcss.com/docs/background-origin
			*/
			"bg-origin": [{ "bg-origin": [
				"border",
				"padding",
				"content"
			] }],
			/**
			* Background Position
			* @see https://tailwindcss.com/docs/background-position
			*/
			"bg-position": [{ bg: scaleBgPosition() }],
			/**
			* Background Repeat
			* @see https://tailwindcss.com/docs/background-repeat
			*/
			"bg-repeat": [{ bg: scaleBgRepeat() }],
			/**
			* Background Size
			* @see https://tailwindcss.com/docs/background-size
			*/
			"bg-size": [{ bg: scaleBgSize() }],
			/**
			* Background Image
			* @see https://tailwindcss.com/docs/background-image
			*/
			"bg-image": [{ bg: [
				"none",
				{
					linear: [
						{ to: [
							"t",
							"tr",
							"r",
							"br",
							"b",
							"bl",
							"l",
							"tl"
						] },
						isInteger,
						isArbitraryVariable,
						isArbitraryValue
					],
					radial: [
						"",
						isArbitraryVariable,
						isArbitraryValue
					],
					conic: [
						isInteger,
						isArbitraryVariable,
						isArbitraryValue
					]
				},
				isArbitraryVariableImage,
				isArbitraryImage
			] }],
			/**
			* Background Color
			* @see https://tailwindcss.com/docs/background-color
			*/
			"bg-color": [{ bg: scaleColor() }],
			/**
			* Gradient Color Stops From Position
			* @see https://tailwindcss.com/docs/gradient-color-stops
			*/
			"gradient-from-pos": [{ from: scaleGradientStopPosition() }],
			/**
			* Gradient Color Stops Via Position
			* @see https://tailwindcss.com/docs/gradient-color-stops
			*/
			"gradient-via-pos": [{ via: scaleGradientStopPosition() }],
			/**
			* Gradient Color Stops To Position
			* @see https://tailwindcss.com/docs/gradient-color-stops
			*/
			"gradient-to-pos": [{ to: scaleGradientStopPosition() }],
			/**
			* Gradient Color Stops From
			* @see https://tailwindcss.com/docs/gradient-color-stops
			*/
			"gradient-from": [{ from: scaleColor() }],
			/**
			* Gradient Color Stops Via
			* @see https://tailwindcss.com/docs/gradient-color-stops
			*/
			"gradient-via": [{ via: scaleColor() }],
			/**
			* Gradient Color Stops To
			* @see https://tailwindcss.com/docs/gradient-color-stops
			*/
			"gradient-to": [{ to: scaleColor() }],
			/**
			* Border Radius
			* @see https://tailwindcss.com/docs/border-radius
			*/
			rounded: [{ rounded: scaleRadius() }],
			/**
			* Border Radius Start
			* @see https://tailwindcss.com/docs/border-radius
			*/
			"rounded-s": [{ "rounded-s": scaleRadius() }],
			/**
			* Border Radius End
			* @see https://tailwindcss.com/docs/border-radius
			*/
			"rounded-e": [{ "rounded-e": scaleRadius() }],
			/**
			* Border Radius Top
			* @see https://tailwindcss.com/docs/border-radius
			*/
			"rounded-t": [{ "rounded-t": scaleRadius() }],
			/**
			* Border Radius Right
			* @see https://tailwindcss.com/docs/border-radius
			*/
			"rounded-r": [{ "rounded-r": scaleRadius() }],
			/**
			* Border Radius Bottom
			* @see https://tailwindcss.com/docs/border-radius
			*/
			"rounded-b": [{ "rounded-b": scaleRadius() }],
			/**
			* Border Radius Left
			* @see https://tailwindcss.com/docs/border-radius
			*/
			"rounded-l": [{ "rounded-l": scaleRadius() }],
			/**
			* Border Radius Start Start
			* @see https://tailwindcss.com/docs/border-radius
			*/
			"rounded-ss": [{ "rounded-ss": scaleRadius() }],
			/**
			* Border Radius Start End
			* @see https://tailwindcss.com/docs/border-radius
			*/
			"rounded-se": [{ "rounded-se": scaleRadius() }],
			/**
			* Border Radius End End
			* @see https://tailwindcss.com/docs/border-radius
			*/
			"rounded-ee": [{ "rounded-ee": scaleRadius() }],
			/**
			* Border Radius End Start
			* @see https://tailwindcss.com/docs/border-radius
			*/
			"rounded-es": [{ "rounded-es": scaleRadius() }],
			/**
			* Border Radius Top Left
			* @see https://tailwindcss.com/docs/border-radius
			*/
			"rounded-tl": [{ "rounded-tl": scaleRadius() }],
			/**
			* Border Radius Top Right
			* @see https://tailwindcss.com/docs/border-radius
			*/
			"rounded-tr": [{ "rounded-tr": scaleRadius() }],
			/**
			* Border Radius Bottom Right
			* @see https://tailwindcss.com/docs/border-radius
			*/
			"rounded-br": [{ "rounded-br": scaleRadius() }],
			/**
			* Border Radius Bottom Left
			* @see https://tailwindcss.com/docs/border-radius
			*/
			"rounded-bl": [{ "rounded-bl": scaleRadius() }],
			/**
			* Border Width
			* @see https://tailwindcss.com/docs/border-width
			*/
			"border-w": [{ border: scaleBorderWidth() }],
			/**
			* Border Width Inline
			* @see https://tailwindcss.com/docs/border-width
			*/
			"border-w-x": [{ "border-x": scaleBorderWidth() }],
			/**
			* Border Width Block
			* @see https://tailwindcss.com/docs/border-width
			*/
			"border-w-y": [{ "border-y": scaleBorderWidth() }],
			/**
			* Border Width Inline Start
			* @see https://tailwindcss.com/docs/border-width
			*/
			"border-w-s": [{ "border-s": scaleBorderWidth() }],
			/**
			* Border Width Inline End
			* @see https://tailwindcss.com/docs/border-width
			*/
			"border-w-e": [{ "border-e": scaleBorderWidth() }],
			/**
			* Border Width Block Start
			* @see https://tailwindcss.com/docs/border-width
			*/
			"border-w-bs": [{ "border-bs": scaleBorderWidth() }],
			/**
			* Border Width Block End
			* @see https://tailwindcss.com/docs/border-width
			*/
			"border-w-be": [{ "border-be": scaleBorderWidth() }],
			/**
			* Border Width Top
			* @see https://tailwindcss.com/docs/border-width
			*/
			"border-w-t": [{ "border-t": scaleBorderWidth() }],
			/**
			* Border Width Right
			* @see https://tailwindcss.com/docs/border-width
			*/
			"border-w-r": [{ "border-r": scaleBorderWidth() }],
			/**
			* Border Width Bottom
			* @see https://tailwindcss.com/docs/border-width
			*/
			"border-w-b": [{ "border-b": scaleBorderWidth() }],
			/**
			* Border Width Left
			* @see https://tailwindcss.com/docs/border-width
			*/
			"border-w-l": [{ "border-l": scaleBorderWidth() }],
			/**
			* Divide Width X
			* @see https://tailwindcss.com/docs/border-width#between-children
			*/
			"divide-x": [{ "divide-x": scaleBorderWidth() }],
			/**
			* Divide Width X Reverse
			* @see https://tailwindcss.com/docs/border-width#between-children
			*/
			"divide-x-reverse": ["divide-x-reverse"],
			/**
			* Divide Width Y
			* @see https://tailwindcss.com/docs/border-width#between-children
			*/
			"divide-y": [{ "divide-y": scaleBorderWidth() }],
			/**
			* Divide Width Y Reverse
			* @see https://tailwindcss.com/docs/border-width#between-children
			*/
			"divide-y-reverse": ["divide-y-reverse"],
			/**
			* Border Style
			* @see https://tailwindcss.com/docs/border-style
			*/
			"border-style": [{ border: [
				...scaleLineStyle(),
				"hidden",
				"none"
			] }],
			/**
			* Divide Style
			* @see https://tailwindcss.com/docs/border-style#setting-the-divider-style
			*/
			"divide-style": [{ divide: [
				...scaleLineStyle(),
				"hidden",
				"none"
			] }],
			/**
			* Border Color
			* @see https://tailwindcss.com/docs/border-color
			*/
			"border-color": [{ border: scaleColor() }],
			/**
			* Border Color Inline
			* @see https://tailwindcss.com/docs/border-color
			*/
			"border-color-x": [{ "border-x": scaleColor() }],
			/**
			* Border Color Block
			* @see https://tailwindcss.com/docs/border-color
			*/
			"border-color-y": [{ "border-y": scaleColor() }],
			/**
			* Border Color Inline Start
			* @see https://tailwindcss.com/docs/border-color
			*/
			"border-color-s": [{ "border-s": scaleColor() }],
			/**
			* Border Color Inline End
			* @see https://tailwindcss.com/docs/border-color
			*/
			"border-color-e": [{ "border-e": scaleColor() }],
			/**
			* Border Color Block Start
			* @see https://tailwindcss.com/docs/border-color
			*/
			"border-color-bs": [{ "border-bs": scaleColor() }],
			/**
			* Border Color Block End
			* @see https://tailwindcss.com/docs/border-color
			*/
			"border-color-be": [{ "border-be": scaleColor() }],
			/**
			* Border Color Top
			* @see https://tailwindcss.com/docs/border-color
			*/
			"border-color-t": [{ "border-t": scaleColor() }],
			/**
			* Border Color Right
			* @see https://tailwindcss.com/docs/border-color
			*/
			"border-color-r": [{ "border-r": scaleColor() }],
			/**
			* Border Color Bottom
			* @see https://tailwindcss.com/docs/border-color
			*/
			"border-color-b": [{ "border-b": scaleColor() }],
			/**
			* Border Color Left
			* @see https://tailwindcss.com/docs/border-color
			*/
			"border-color-l": [{ "border-l": scaleColor() }],
			/**
			* Divide Color
			* @see https://tailwindcss.com/docs/divide-color
			*/
			"divide-color": [{ divide: scaleColor() }],
			/**
			* Outline Style
			* @see https://tailwindcss.com/docs/outline-style
			*/
			"outline-style": [{ outline: [
				...scaleLineStyle(),
				"none",
				"hidden"
			] }],
			/**
			* Outline Offset
			* @see https://tailwindcss.com/docs/outline-offset
			*/
			"outline-offset": [{ "outline-offset": [
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Outline Width
			* @see https://tailwindcss.com/docs/outline-width
			*/
			"outline-w": [{ outline: [
				"",
				isNumber,
				isArbitraryVariableLength,
				isArbitraryLength
			] }],
			/**
			* Outline Color
			* @see https://tailwindcss.com/docs/outline-color
			*/
			"outline-color": [{ outline: scaleColor() }],
			/**
			* Box Shadow
			* @see https://tailwindcss.com/docs/box-shadow
			*/
			shadow: [{ shadow: [
				"",
				"none",
				themeShadow,
				isArbitraryVariableShadow,
				isArbitraryShadow
			] }],
			/**
			* Box Shadow Color
			* @see https://tailwindcss.com/docs/box-shadow#setting-the-shadow-color
			*/
			"shadow-color": [{ shadow: scaleColor() }],
			/**
			* Inset Box Shadow
			* @see https://tailwindcss.com/docs/box-shadow#adding-an-inset-shadow
			*/
			"inset-shadow": [{ "inset-shadow": [
				"none",
				themeInsetShadow,
				isArbitraryVariableShadow,
				isArbitraryShadow
			] }],
			/**
			* Inset Box Shadow Color
			* @see https://tailwindcss.com/docs/box-shadow#setting-the-inset-shadow-color
			*/
			"inset-shadow-color": [{ "inset-shadow": scaleColor() }],
			/**
			* Ring Width
			* @see https://tailwindcss.com/docs/box-shadow#adding-a-ring
			*/
			"ring-w": [{ ring: scaleBorderWidth() }],
			/**
			* Ring Width Inset
			* @see https://v3.tailwindcss.com/docs/ring-width#inset-rings
			* @deprecated since Tailwind CSS v4.0.0
			* @see https://github.com/tailwindlabs/tailwindcss/blob/v4.0.0/packages/tailwindcss/src/utilities.ts#L4158
			*/
			"ring-w-inset": ["ring-inset"],
			/**
			* Ring Color
			* @see https://tailwindcss.com/docs/box-shadow#setting-the-ring-color
			*/
			"ring-color": [{ ring: scaleColor() }],
			/**
			* Ring Offset Width
			* @see https://v3.tailwindcss.com/docs/ring-offset-width
			* @deprecated since Tailwind CSS v4.0.0
			* @see https://github.com/tailwindlabs/tailwindcss/blob/v4.0.0/packages/tailwindcss/src/utilities.ts#L4158
			*/
			"ring-offset-w": [{ "ring-offset": [isNumber, isArbitraryLength] }],
			/**
			* Ring Offset Color
			* @see https://v3.tailwindcss.com/docs/ring-offset-color
			* @deprecated since Tailwind CSS v4.0.0
			* @see https://github.com/tailwindlabs/tailwindcss/blob/v4.0.0/packages/tailwindcss/src/utilities.ts#L4158
			*/
			"ring-offset-color": [{ "ring-offset": scaleColor() }],
			/**
			* Inset Ring Width
			* @see https://tailwindcss.com/docs/box-shadow#adding-an-inset-ring
			*/
			"inset-ring-w": [{ "inset-ring": scaleBorderWidth() }],
			/**
			* Inset Ring Color
			* @see https://tailwindcss.com/docs/box-shadow#setting-the-inset-ring-color
			*/
			"inset-ring-color": [{ "inset-ring": scaleColor() }],
			/**
			* Text Shadow
			* @see https://tailwindcss.com/docs/text-shadow
			*/
			"text-shadow": [{ "text-shadow": [
				"none",
				themeTextShadow,
				isArbitraryVariableShadow,
				isArbitraryShadow
			] }],
			/**
			* Text Shadow Color
			* @see https://tailwindcss.com/docs/text-shadow#setting-the-shadow-color
			*/
			"text-shadow-color": [{ "text-shadow": scaleColor() }],
			/**
			* Opacity
			* @see https://tailwindcss.com/docs/opacity
			*/
			opacity: [{ opacity: [
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Mix Blend Mode
			* @see https://tailwindcss.com/docs/mix-blend-mode
			*/
			"mix-blend": [{ "mix-blend": [
				...scaleBlendMode(),
				"plus-darker",
				"plus-lighter"
			] }],
			/**
			* Background Blend Mode
			* @see https://tailwindcss.com/docs/background-blend-mode
			*/
			"bg-blend": [{ "bg-blend": scaleBlendMode() }],
			/**
			* Mask Clip
			* @see https://tailwindcss.com/docs/mask-clip
			*/
			"mask-clip": [{ "mask-clip": [
				"border",
				"padding",
				"content",
				"fill",
				"stroke",
				"view"
			] }, "mask-no-clip"],
			/**
			* Mask Composite
			* @see https://tailwindcss.com/docs/mask-composite
			*/
			"mask-composite": [{ mask: [
				"add",
				"subtract",
				"intersect",
				"exclude"
			] }],
			/**
			* Mask Image
			* @see https://tailwindcss.com/docs/mask-image
			*/
			"mask-image-linear-pos": [{ "mask-linear": [isNumber] }],
			"mask-image-linear-from-pos": [{ "mask-linear-from": scaleMaskImagePosition() }],
			"mask-image-linear-to-pos": [{ "mask-linear-to": scaleMaskImagePosition() }],
			"mask-image-linear-from-color": [{ "mask-linear-from": scaleColor() }],
			"mask-image-linear-to-color": [{ "mask-linear-to": scaleColor() }],
			"mask-image-t-from-pos": [{ "mask-t-from": scaleMaskImagePosition() }],
			"mask-image-t-to-pos": [{ "mask-t-to": scaleMaskImagePosition() }],
			"mask-image-t-from-color": [{ "mask-t-from": scaleColor() }],
			"mask-image-t-to-color": [{ "mask-t-to": scaleColor() }],
			"mask-image-r-from-pos": [{ "mask-r-from": scaleMaskImagePosition() }],
			"mask-image-r-to-pos": [{ "mask-r-to": scaleMaskImagePosition() }],
			"mask-image-r-from-color": [{ "mask-r-from": scaleColor() }],
			"mask-image-r-to-color": [{ "mask-r-to": scaleColor() }],
			"mask-image-b-from-pos": [{ "mask-b-from": scaleMaskImagePosition() }],
			"mask-image-b-to-pos": [{ "mask-b-to": scaleMaskImagePosition() }],
			"mask-image-b-from-color": [{ "mask-b-from": scaleColor() }],
			"mask-image-b-to-color": [{ "mask-b-to": scaleColor() }],
			"mask-image-l-from-pos": [{ "mask-l-from": scaleMaskImagePosition() }],
			"mask-image-l-to-pos": [{ "mask-l-to": scaleMaskImagePosition() }],
			"mask-image-l-from-color": [{ "mask-l-from": scaleColor() }],
			"mask-image-l-to-color": [{ "mask-l-to": scaleColor() }],
			"mask-image-x-from-pos": [{ "mask-x-from": scaleMaskImagePosition() }],
			"mask-image-x-to-pos": [{ "mask-x-to": scaleMaskImagePosition() }],
			"mask-image-x-from-color": [{ "mask-x-from": scaleColor() }],
			"mask-image-x-to-color": [{ "mask-x-to": scaleColor() }],
			"mask-image-y-from-pos": [{ "mask-y-from": scaleMaskImagePosition() }],
			"mask-image-y-to-pos": [{ "mask-y-to": scaleMaskImagePosition() }],
			"mask-image-y-from-color": [{ "mask-y-from": scaleColor() }],
			"mask-image-y-to-color": [{ "mask-y-to": scaleColor() }],
			"mask-image-radial": [{ "mask-radial": [isArbitraryVariable, isArbitraryValue] }],
			"mask-image-radial-from-pos": [{ "mask-radial-from": scaleMaskImagePosition() }],
			"mask-image-radial-to-pos": [{ "mask-radial-to": scaleMaskImagePosition() }],
			"mask-image-radial-from-color": [{ "mask-radial-from": scaleColor() }],
			"mask-image-radial-to-color": [{ "mask-radial-to": scaleColor() }],
			"mask-image-radial-shape": [{ "mask-radial": ["circle", "ellipse"] }],
			"mask-image-radial-size": [{ "mask-radial": [{
				closest: ["side", "corner"],
				farthest: ["side", "corner"]
			}] }],
			"mask-image-radial-pos": [{ "mask-radial-at": scalePosition() }],
			"mask-image-conic-pos": [{ "mask-conic": [isNumber] }],
			"mask-image-conic-from-pos": [{ "mask-conic-from": scaleMaskImagePosition() }],
			"mask-image-conic-to-pos": [{ "mask-conic-to": scaleMaskImagePosition() }],
			"mask-image-conic-from-color": [{ "mask-conic-from": scaleColor() }],
			"mask-image-conic-to-color": [{ "mask-conic-to": scaleColor() }],
			/**
			* Mask Mode
			* @see https://tailwindcss.com/docs/mask-mode
			*/
			"mask-mode": [{ mask: [
				"alpha",
				"luminance",
				"match"
			] }],
			/**
			* Mask Origin
			* @see https://tailwindcss.com/docs/mask-origin
			*/
			"mask-origin": [{ "mask-origin": [
				"border",
				"padding",
				"content",
				"fill",
				"stroke",
				"view"
			] }],
			/**
			* Mask Position
			* @see https://tailwindcss.com/docs/mask-position
			*/
			"mask-position": [{ mask: scaleBgPosition() }],
			/**
			* Mask Repeat
			* @see https://tailwindcss.com/docs/mask-repeat
			*/
			"mask-repeat": [{ mask: scaleBgRepeat() }],
			/**
			* Mask Size
			* @see https://tailwindcss.com/docs/mask-size
			*/
			"mask-size": [{ mask: scaleBgSize() }],
			/**
			* Mask Type
			* @see https://tailwindcss.com/docs/mask-type
			*/
			"mask-type": [{ "mask-type": ["alpha", "luminance"] }],
			/**
			* Mask Image
			* @see https://tailwindcss.com/docs/mask-image
			*/
			"mask-image": [{ mask: [
				"none",
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Filter
			* @see https://tailwindcss.com/docs/filter
			*/
			filter: [{ filter: [
				"",
				"none",
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Blur
			* @see https://tailwindcss.com/docs/blur
			*/
			blur: [{ blur: scaleBlur() }],
			/**
			* Brightness
			* @see https://tailwindcss.com/docs/brightness
			*/
			brightness: [{ brightness: [
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Contrast
			* @see https://tailwindcss.com/docs/contrast
			*/
			contrast: [{ contrast: [
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Drop Shadow
			* @see https://tailwindcss.com/docs/drop-shadow
			*/
			"drop-shadow": [{ "drop-shadow": [
				"",
				"none",
				themeDropShadow,
				isArbitraryVariableShadow,
				isArbitraryShadow
			] }],
			/**
			* Drop Shadow Color
			* @see https://tailwindcss.com/docs/filter-drop-shadow#setting-the-shadow-color
			*/
			"drop-shadow-color": [{ "drop-shadow": scaleColor() }],
			/**
			* Grayscale
			* @see https://tailwindcss.com/docs/grayscale
			*/
			grayscale: [{ grayscale: [
				"",
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Hue Rotate
			* @see https://tailwindcss.com/docs/hue-rotate
			*/
			"hue-rotate": [{ "hue-rotate": [
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Invert
			* @see https://tailwindcss.com/docs/invert
			*/
			invert: [{ invert: [
				"",
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Saturate
			* @see https://tailwindcss.com/docs/saturate
			*/
			saturate: [{ saturate: [
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Sepia
			* @see https://tailwindcss.com/docs/sepia
			*/
			sepia: [{ sepia: [
				"",
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Backdrop Filter
			* @see https://tailwindcss.com/docs/backdrop-filter
			*/
			"backdrop-filter": [{ "backdrop-filter": [
				"",
				"none",
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Backdrop Blur
			* @see https://tailwindcss.com/docs/backdrop-blur
			*/
			"backdrop-blur": [{ "backdrop-blur": scaleBlur() }],
			/**
			* Backdrop Brightness
			* @see https://tailwindcss.com/docs/backdrop-brightness
			*/
			"backdrop-brightness": [{ "backdrop-brightness": [
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Backdrop Contrast
			* @see https://tailwindcss.com/docs/backdrop-contrast
			*/
			"backdrop-contrast": [{ "backdrop-contrast": [
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Backdrop Grayscale
			* @see https://tailwindcss.com/docs/backdrop-grayscale
			*/
			"backdrop-grayscale": [{ "backdrop-grayscale": [
				"",
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Backdrop Hue Rotate
			* @see https://tailwindcss.com/docs/backdrop-hue-rotate
			*/
			"backdrop-hue-rotate": [{ "backdrop-hue-rotate": [
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Backdrop Invert
			* @see https://tailwindcss.com/docs/backdrop-invert
			*/
			"backdrop-invert": [{ "backdrop-invert": [
				"",
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Backdrop Opacity
			* @see https://tailwindcss.com/docs/backdrop-opacity
			*/
			"backdrop-opacity": [{ "backdrop-opacity": [
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Backdrop Saturate
			* @see https://tailwindcss.com/docs/backdrop-saturate
			*/
			"backdrop-saturate": [{ "backdrop-saturate": [
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Backdrop Sepia
			* @see https://tailwindcss.com/docs/backdrop-sepia
			*/
			"backdrop-sepia": [{ "backdrop-sepia": [
				"",
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Border Collapse
			* @see https://tailwindcss.com/docs/border-collapse
			*/
			"border-collapse": [{ border: ["collapse", "separate"] }],
			/**
			* Border Spacing
			* @see https://tailwindcss.com/docs/border-spacing
			*/
			"border-spacing": [{ "border-spacing": scaleUnambiguousSpacing() }],
			/**
			* Border Spacing X
			* @see https://tailwindcss.com/docs/border-spacing
			*/
			"border-spacing-x": [{ "border-spacing-x": scaleUnambiguousSpacing() }],
			/**
			* Border Spacing Y
			* @see https://tailwindcss.com/docs/border-spacing
			*/
			"border-spacing-y": [{ "border-spacing-y": scaleUnambiguousSpacing() }],
			/**
			* Table Layout
			* @see https://tailwindcss.com/docs/table-layout
			*/
			"table-layout": [{ table: ["auto", "fixed"] }],
			/**
			* Caption Side
			* @see https://tailwindcss.com/docs/caption-side
			*/
			caption: [{ caption: ["top", "bottom"] }],
			/**
			* Transition Property
			* @see https://tailwindcss.com/docs/transition-property
			*/
			transition: [{ transition: [
				"",
				"all",
				"colors",
				"opacity",
				"shadow",
				"transform",
				"none",
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Transition Behavior
			* @see https://tailwindcss.com/docs/transition-behavior
			*/
			"transition-behavior": [{ transition: ["normal", "discrete"] }],
			/**
			* Transition Duration
			* @see https://tailwindcss.com/docs/transition-duration
			*/
			duration: [{ duration: [
				isNumber,
				"initial",
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Transition Timing Function
			* @see https://tailwindcss.com/docs/transition-timing-function
			*/
			ease: [{ ease: [
				"linear",
				"initial",
				themeEase,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Transition Delay
			* @see https://tailwindcss.com/docs/transition-delay
			*/
			delay: [{ delay: [
				isNumber,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Animation
			* @see https://tailwindcss.com/docs/animation
			*/
			animate: [{ animate: [
				"none",
				themeAnimate,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Backface Visibility
			* @see https://tailwindcss.com/docs/backface-visibility
			*/
			backface: [{ backface: ["hidden", "visible"] }],
			/**
			* Perspective
			* @see https://tailwindcss.com/docs/perspective
			*/
			perspective: [{ perspective: [
				themePerspective,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Perspective Origin
			* @see https://tailwindcss.com/docs/perspective-origin
			*/
			"perspective-origin": [{ "perspective-origin": scalePositionWithArbitrary() }],
			/**
			* Rotate
			* @see https://tailwindcss.com/docs/rotate
			*/
			rotate: [{ rotate: scaleRotate() }],
			/**
			* Rotate X
			* @see https://tailwindcss.com/docs/rotate
			*/
			"rotate-x": [{ "rotate-x": scaleRotate() }],
			/**
			* Rotate Y
			* @see https://tailwindcss.com/docs/rotate
			*/
			"rotate-y": [{ "rotate-y": scaleRotate() }],
			/**
			* Rotate Z
			* @see https://tailwindcss.com/docs/rotate
			*/
			"rotate-z": [{ "rotate-z": scaleRotate() }],
			/**
			* Scale
			* @see https://tailwindcss.com/docs/scale
			*/
			scale: [{ scale: scaleScale() }],
			/**
			* Scale X
			* @see https://tailwindcss.com/docs/scale
			*/
			"scale-x": [{ "scale-x": scaleScale() }],
			/**
			* Scale Y
			* @see https://tailwindcss.com/docs/scale
			*/
			"scale-y": [{ "scale-y": scaleScale() }],
			/**
			* Scale Z
			* @see https://tailwindcss.com/docs/scale
			*/
			"scale-z": [{ "scale-z": scaleScale() }],
			/**
			* Scale 3D
			* @see https://tailwindcss.com/docs/scale
			*/
			"scale-3d": ["scale-3d"],
			/**
			* Skew
			* @see https://tailwindcss.com/docs/skew
			*/
			skew: [{ skew: scaleSkew() }],
			/**
			* Skew X
			* @see https://tailwindcss.com/docs/skew
			*/
			"skew-x": [{ "skew-x": scaleSkew() }],
			/**
			* Skew Y
			* @see https://tailwindcss.com/docs/skew
			*/
			"skew-y": [{ "skew-y": scaleSkew() }],
			/**
			* Transform
			* @see https://tailwindcss.com/docs/transform
			*/
			transform: [{ transform: [
				isArbitraryVariable,
				isArbitraryValue,
				"",
				"none",
				"gpu",
				"cpu"
			] }],
			/**
			* Transform Origin
			* @see https://tailwindcss.com/docs/transform-origin
			*/
			"transform-origin": [{ origin: scalePositionWithArbitrary() }],
			/**
			* Transform Style
			* @see https://tailwindcss.com/docs/transform-style
			*/
			"transform-style": [{ transform: ["3d", "flat"] }],
			/**
			* Translate
			* @see https://tailwindcss.com/docs/translate
			*/
			translate: [{ translate: scaleTranslate() }],
			/**
			* Translate X
			* @see https://tailwindcss.com/docs/translate
			*/
			"translate-x": [{ "translate-x": scaleTranslate() }],
			/**
			* Translate Y
			* @see https://tailwindcss.com/docs/translate
			*/
			"translate-y": [{ "translate-y": scaleTranslate() }],
			/**
			* Translate Z
			* @see https://tailwindcss.com/docs/translate
			*/
			"translate-z": [{ "translate-z": scaleTranslate() }],
			/**
			* Translate None
			* @see https://tailwindcss.com/docs/translate
			*/
			"translate-none": ["translate-none"],
			/**
			* Zoom
			* @see https://tailwindcss.com/docs/zoom
			*/
			zoom: [{ zoom: [
				isInteger,
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Accent Color
			* @see https://tailwindcss.com/docs/accent-color
			*/
			accent: [{ accent: scaleColor() }],
			/**
			* Appearance
			* @see https://tailwindcss.com/docs/appearance
			*/
			appearance: [{ appearance: ["none", "auto"] }],
			/**
			* Caret Color
			* @see https://tailwindcss.com/docs/just-in-time-mode#caret-color-utilities
			*/
			"caret-color": [{ caret: scaleColor() }],
			/**
			* Color Scheme
			* @see https://tailwindcss.com/docs/color-scheme
			*/
			"color-scheme": [{ scheme: [
				"normal",
				"dark",
				"light",
				"light-dark",
				"only-dark",
				"only-light"
			] }],
			/**
			* Cursor
			* @see https://tailwindcss.com/docs/cursor
			*/
			cursor: [{ cursor: [
				"auto",
				"default",
				"pointer",
				"wait",
				"text",
				"move",
				"help",
				"not-allowed",
				"none",
				"context-menu",
				"progress",
				"cell",
				"crosshair",
				"vertical-text",
				"alias",
				"copy",
				"no-drop",
				"grab",
				"grabbing",
				"all-scroll",
				"col-resize",
				"row-resize",
				"n-resize",
				"e-resize",
				"s-resize",
				"w-resize",
				"ne-resize",
				"nw-resize",
				"se-resize",
				"sw-resize",
				"ew-resize",
				"ns-resize",
				"nesw-resize",
				"nwse-resize",
				"zoom-in",
				"zoom-out",
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Field Sizing
			* @see https://tailwindcss.com/docs/field-sizing
			*/
			"field-sizing": [{ "field-sizing": ["fixed", "content"] }],
			/**
			* Pointer Events
			* @see https://tailwindcss.com/docs/pointer-events
			*/
			"pointer-events": [{ "pointer-events": ["auto", "none"] }],
			/**
			* Resize
			* @see https://tailwindcss.com/docs/resize
			*/
			resize: [{ resize: [
				"none",
				"",
				"y",
				"x"
			] }],
			/**
			* Scroll Behavior
			* @see https://tailwindcss.com/docs/scroll-behavior
			*/
			"scroll-behavior": [{ scroll: ["auto", "smooth"] }],
			/**
			* Scrollbar Thumb Color
			* @see https://tailwindcss.com/docs/scrollbar-color
			*/
			"scrollbar-thumb-color": [{ "scrollbar-thumb": scaleColor() }],
			/**
			* Scrollbar Track Color
			* @see https://tailwindcss.com/docs/scrollbar-color
			*/
			"scrollbar-track-color": [{ "scrollbar-track": scaleColor() }],
			/**
			* Scrollbar Gutter
			* @see https://tailwindcss.com/docs/scrollbar-gutter
			*/
			"scrollbar-gutter": [{ "scrollbar-gutter": [
				"auto",
				"stable",
				"both"
			] }],
			/**
			* Scrollbar Width
			* @see https://tailwindcss.com/docs/scrollbar-width
			*/
			"scrollbar-w": [{ scrollbar: [
				"auto",
				"thin",
				"none"
			] }],
			/**
			* Scroll Margin
			* @see https://tailwindcss.com/docs/scroll-margin
			*/
			"scroll-m": [{ "scroll-m": scaleUnambiguousSpacing() }],
			/**
			* Scroll Margin Inline
			* @see https://tailwindcss.com/docs/scroll-margin
			*/
			"scroll-mx": [{ "scroll-mx": scaleUnambiguousSpacing() }],
			/**
			* Scroll Margin Block
			* @see https://tailwindcss.com/docs/scroll-margin
			*/
			"scroll-my": [{ "scroll-my": scaleUnambiguousSpacing() }],
			/**
			* Scroll Margin Inline Start
			* @see https://tailwindcss.com/docs/scroll-margin
			*/
			"scroll-ms": [{ "scroll-ms": scaleUnambiguousSpacing() }],
			/**
			* Scroll Margin Inline End
			* @see https://tailwindcss.com/docs/scroll-margin
			*/
			"scroll-me": [{ "scroll-me": scaleUnambiguousSpacing() }],
			/**
			* Scroll Margin Block Start
			* @see https://tailwindcss.com/docs/scroll-margin
			*/
			"scroll-mbs": [{ "scroll-mbs": scaleUnambiguousSpacing() }],
			/**
			* Scroll Margin Block End
			* @see https://tailwindcss.com/docs/scroll-margin
			*/
			"scroll-mbe": [{ "scroll-mbe": scaleUnambiguousSpacing() }],
			/**
			* Scroll Margin Top
			* @see https://tailwindcss.com/docs/scroll-margin
			*/
			"scroll-mt": [{ "scroll-mt": scaleUnambiguousSpacing() }],
			/**
			* Scroll Margin Right
			* @see https://tailwindcss.com/docs/scroll-margin
			*/
			"scroll-mr": [{ "scroll-mr": scaleUnambiguousSpacing() }],
			/**
			* Scroll Margin Bottom
			* @see https://tailwindcss.com/docs/scroll-margin
			*/
			"scroll-mb": [{ "scroll-mb": scaleUnambiguousSpacing() }],
			/**
			* Scroll Margin Left
			* @see https://tailwindcss.com/docs/scroll-margin
			*/
			"scroll-ml": [{ "scroll-ml": scaleUnambiguousSpacing() }],
			/**
			* Scroll Padding
			* @see https://tailwindcss.com/docs/scroll-padding
			*/
			"scroll-p": [{ "scroll-p": scaleUnambiguousSpacing() }],
			/**
			* Scroll Padding Inline
			* @see https://tailwindcss.com/docs/scroll-padding
			*/
			"scroll-px": [{ "scroll-px": scaleUnambiguousSpacing() }],
			/**
			* Scroll Padding Block
			* @see https://tailwindcss.com/docs/scroll-padding
			*/
			"scroll-py": [{ "scroll-py": scaleUnambiguousSpacing() }],
			/**
			* Scroll Padding Inline Start
			* @see https://tailwindcss.com/docs/scroll-padding
			*/
			"scroll-ps": [{ "scroll-ps": scaleUnambiguousSpacing() }],
			/**
			* Scroll Padding Inline End
			* @see https://tailwindcss.com/docs/scroll-padding
			*/
			"scroll-pe": [{ "scroll-pe": scaleUnambiguousSpacing() }],
			/**
			* Scroll Padding Block Start
			* @see https://tailwindcss.com/docs/scroll-padding
			*/
			"scroll-pbs": [{ "scroll-pbs": scaleUnambiguousSpacing() }],
			/**
			* Scroll Padding Block End
			* @see https://tailwindcss.com/docs/scroll-padding
			*/
			"scroll-pbe": [{ "scroll-pbe": scaleUnambiguousSpacing() }],
			/**
			* Scroll Padding Top
			* @see https://tailwindcss.com/docs/scroll-padding
			*/
			"scroll-pt": [{ "scroll-pt": scaleUnambiguousSpacing() }],
			/**
			* Scroll Padding Right
			* @see https://tailwindcss.com/docs/scroll-padding
			*/
			"scroll-pr": [{ "scroll-pr": scaleUnambiguousSpacing() }],
			/**
			* Scroll Padding Bottom
			* @see https://tailwindcss.com/docs/scroll-padding
			*/
			"scroll-pb": [{ "scroll-pb": scaleUnambiguousSpacing() }],
			/**
			* Scroll Padding Left
			* @see https://tailwindcss.com/docs/scroll-padding
			*/
			"scroll-pl": [{ "scroll-pl": scaleUnambiguousSpacing() }],
			/**
			* Scroll Snap Align
			* @see https://tailwindcss.com/docs/scroll-snap-align
			*/
			"snap-align": [{ snap: [
				"start",
				"end",
				"center",
				"align-none"
			] }],
			/**
			* Scroll Snap Stop
			* @see https://tailwindcss.com/docs/scroll-snap-stop
			*/
			"snap-stop": [{ snap: ["normal", "always"] }],
			/**
			* Scroll Snap Type
			* @see https://tailwindcss.com/docs/scroll-snap-type
			*/
			"snap-type": [{ snap: [
				"none",
				"x",
				"y",
				"both"
			] }],
			/**
			* Scroll Snap Type Strictness
			* @see https://tailwindcss.com/docs/scroll-snap-type
			*/
			"snap-strictness": [{ snap: ["mandatory", "proximity"] }],
			/**
			* Touch Action
			* @see https://tailwindcss.com/docs/touch-action
			*/
			touch: [{ touch: [
				"auto",
				"none",
				"manipulation"
			] }],
			/**
			* Touch Action X
			* @see https://tailwindcss.com/docs/touch-action
			*/
			"touch-x": [{ "touch-pan": [
				"x",
				"left",
				"right"
			] }],
			/**
			* Touch Action Y
			* @see https://tailwindcss.com/docs/touch-action
			*/
			"touch-y": [{ "touch-pan": [
				"y",
				"up",
				"down"
			] }],
			/**
			* Touch Action Pinch Zoom
			* @see https://tailwindcss.com/docs/touch-action
			*/
			"touch-pz": ["touch-pinch-zoom"],
			/**
			* User Select
			* @see https://tailwindcss.com/docs/user-select
			*/
			select: [{ select: [
				"none",
				"text",
				"all",
				"auto"
			] }],
			/**
			* Will Change
			* @see https://tailwindcss.com/docs/will-change
			*/
			"will-change": [{ "will-change": [
				"auto",
				"scroll",
				"contents",
				"transform",
				isArbitraryVariable,
				isArbitraryValue
			] }],
			/**
			* Fill
			* @see https://tailwindcss.com/docs/fill
			*/
			fill: [{ fill: ["none", ...scaleColor()] }],
			/**
			* Stroke Width
			* @see https://tailwindcss.com/docs/stroke-width
			*/
			"stroke-w": [{ stroke: [
				isNumber,
				isArbitraryVariableLength,
				isArbitraryLength,
				isArbitraryNumber
			] }],
			/**
			* Stroke
			* @see https://tailwindcss.com/docs/stroke
			*/
			stroke: [{ stroke: ["none", ...scaleColor()] }],
			/**
			* Forced Color Adjust
			* @see https://tailwindcss.com/docs/forced-color-adjust
			*/
			"forced-color-adjust": [{ "forced-color-adjust": ["auto", "none"] }]
		},
		conflictingClassGroups: {
			"container-named": ["container-type"],
			overflow: ["overflow-x", "overflow-y"],
			overscroll: ["overscroll-x", "overscroll-y"],
			inset: [
				"inset-x",
				"inset-y",
				"inset-bs",
				"inset-be",
				"start",
				"end",
				"top",
				"right",
				"bottom",
				"left"
			],
			"inset-x": ["right", "left"],
			"inset-y": ["top", "bottom"],
			flex: [
				"basis",
				"grow",
				"shrink"
			],
			gap: ["gap-x", "gap-y"],
			p: [
				"px",
				"py",
				"ps",
				"pe",
				"pbs",
				"pbe",
				"pt",
				"pr",
				"pb",
				"pl"
			],
			px: ["pr", "pl"],
			py: ["pt", "pb"],
			m: [
				"mx",
				"my",
				"ms",
				"me",
				"mbs",
				"mbe",
				"mt",
				"mr",
				"mb",
				"ml"
			],
			mx: ["mr", "ml"],
			my: ["mt", "mb"],
			size: ["w", "h"],
			"font-size": ["leading"],
			"fvn-normal": [
				"fvn-ordinal",
				"fvn-slashed-zero",
				"fvn-figure",
				"fvn-spacing",
				"fvn-fraction"
			],
			"fvn-ordinal": ["fvn-normal"],
			"fvn-slashed-zero": ["fvn-normal"],
			"fvn-figure": ["fvn-normal"],
			"fvn-spacing": ["fvn-normal"],
			"fvn-fraction": ["fvn-normal"],
			"line-clamp": ["display", "overflow"],
			rounded: [
				"rounded-s",
				"rounded-e",
				"rounded-t",
				"rounded-r",
				"rounded-b",
				"rounded-l",
				"rounded-ss",
				"rounded-se",
				"rounded-ee",
				"rounded-es",
				"rounded-tl",
				"rounded-tr",
				"rounded-br",
				"rounded-bl"
			],
			"rounded-s": ["rounded-ss", "rounded-es"],
			"rounded-e": ["rounded-se", "rounded-ee"],
			"rounded-t": ["rounded-tl", "rounded-tr"],
			"rounded-r": ["rounded-tr", "rounded-br"],
			"rounded-b": ["rounded-br", "rounded-bl"],
			"rounded-l": ["rounded-tl", "rounded-bl"],
			"border-spacing": ["border-spacing-x", "border-spacing-y"],
			"border-w": [
				"border-w-x",
				"border-w-y",
				"border-w-s",
				"border-w-e",
				"border-w-bs",
				"border-w-be",
				"border-w-t",
				"border-w-r",
				"border-w-b",
				"border-w-l"
			],
			"border-w-x": ["border-w-r", "border-w-l"],
			"border-w-y": ["border-w-t", "border-w-b"],
			"border-color": [
				"border-color-x",
				"border-color-y",
				"border-color-s",
				"border-color-e",
				"border-color-bs",
				"border-color-be",
				"border-color-t",
				"border-color-r",
				"border-color-b",
				"border-color-l"
			],
			"border-color-x": ["border-color-r", "border-color-l"],
			"border-color-y": ["border-color-t", "border-color-b"],
			translate: [
				"translate-x",
				"translate-y",
				"translate-none"
			],
			"translate-none": [
				"translate",
				"translate-x",
				"translate-y",
				"translate-z"
			],
			"scroll-m": [
				"scroll-mx",
				"scroll-my",
				"scroll-ms",
				"scroll-me",
				"scroll-mbs",
				"scroll-mbe",
				"scroll-mt",
				"scroll-mr",
				"scroll-mb",
				"scroll-ml"
			],
			"scroll-mx": ["scroll-mr", "scroll-ml"],
			"scroll-my": ["scroll-mt", "scroll-mb"],
			"scroll-p": [
				"scroll-px",
				"scroll-py",
				"scroll-ps",
				"scroll-pe",
				"scroll-pbs",
				"scroll-pbe",
				"scroll-pt",
				"scroll-pr",
				"scroll-pb",
				"scroll-pl"
			],
			"scroll-px": ["scroll-pr", "scroll-pl"],
			"scroll-py": ["scroll-pt", "scroll-pb"],
			touch: [
				"touch-x",
				"touch-y",
				"touch-pz"
			],
			"touch-x": ["touch"],
			"touch-y": ["touch"],
			"touch-pz": ["touch"]
		},
		conflictingClassGroupModifiers: { "font-size": ["leading"] },
		postfixLookupClassGroups: ["container-type"],
		orderSensitiveModifiers: [
			"*",
			"**",
			"after",
			"backdrop",
			"before",
			"details-content",
			"file",
			"first-letter",
			"first-line",
			"marker",
			"placeholder",
			"selection"
		]
	};
};
var twMerge = /* @__PURE__ */ createTailwindMerge(getDefaultConfig);
//#endregion
//#region lib/utils.ts
function cn(...inputs) {
	return twMerge(clsx(inputs));
}
//#endregion
//#region ../../../node_modules/.pnpm/@floating-ui+utils@0.2.12/node_modules/@floating-ui/utils/dist/floating-ui.utils.dom.mjs
function hasWindow() {
	return false;
}
function getNodeName(node) {
	if (isNode(node)) return (node.nodeName || "").toLowerCase();
	return "#document";
}
function getWindow(node) {
	var _node$ownerDocument;
	return (node == null || (_node$ownerDocument = node.ownerDocument) == null ? void 0 : _node$ownerDocument.defaultView) || window;
}
function getDocumentElement(node) {
	var _ref;
	return (_ref = (isNode(node) ? node.ownerDocument : node.document) || window.document) == null ? void 0 : _ref.documentElement;
}
function isNode(value) {
	if (!hasWindow()) return false;
	return value instanceof Node || value instanceof getWindow(value).Node;
}
function isElement(value) {
	if (!hasWindow()) return false;
	return value instanceof Element || value instanceof getWindow(value).Element;
}
function isHTMLElement(value) {
	if (!hasWindow()) return false;
	return value instanceof HTMLElement || value instanceof getWindow(value).HTMLElement;
}
function isShadowRoot(value) {
	if (!hasWindow() || typeof ShadowRoot === "undefined") return false;
	return value instanceof ShadowRoot || value instanceof getWindow(value).ShadowRoot;
}
function isOverflowElement(element) {
	const { overflow, overflowX, overflowY, display } = getComputedStyle$1(element);
	return /auto|scroll|overlay|hidden|clip/.test(overflow + overflowY + overflowX) && display !== "inline" && display !== "contents";
}
function isTableElement(element) {
	return /^(table|td|th)$/.test(getNodeName(element));
}
function isTopLayer(element) {
	try {
		if (element.matches(":popover-open")) return true;
	} catch (_e) {}
	try {
		return element.matches(":modal");
	} catch (_e) {
		return false;
	}
}
var willChangeRe = /transform|translate|scale|rotate|perspective|filter/;
var containRe = /paint|layout|strict|content/;
var isNotNone = (value) => !!value && value !== "none";
var isWebKitValue;
function isContainingBlock(elementOrCss) {
	const css = isElement(elementOrCss) ? getComputedStyle$1(elementOrCss) : elementOrCss;
	return isNotNone(css.transform) || isNotNone(css.translate) || isNotNone(css.scale) || isNotNone(css.rotate) || isNotNone(css.perspective) || !isWebKit() && (isNotNone(css.backdropFilter) || isNotNone(css.filter)) || willChangeRe.test(css.willChange || "") || containRe.test(css.contain || "");
}
function getContainingBlock(element) {
	let currentNode = getParentNode(element);
	while (isHTMLElement(currentNode) && !isLastTraversableNode(currentNode)) {
		if (isContainingBlock(currentNode)) return currentNode;
		else if (isTopLayer(currentNode)) return null;
		currentNode = getParentNode(currentNode);
	}
	return null;
}
function isWebKit() {
	if (isWebKitValue == null) isWebKitValue = typeof CSS !== "undefined" && CSS.supports && CSS.supports("-webkit-backdrop-filter", "none");
	return isWebKitValue;
}
function isLastTraversableNode(node) {
	return /^(html|body|#document)$/.test(getNodeName(node));
}
function getComputedStyle$1(element) {
	return getWindow(element).getComputedStyle(element);
}
function getNodeScroll(element) {
	if (isElement(element)) return {
		scrollLeft: element.scrollLeft,
		scrollTop: element.scrollTop
	};
	return {
		scrollLeft: element.scrollX,
		scrollTop: element.scrollY
	};
}
function getParentNode(node) {
	if (getNodeName(node) === "html") return node;
	const result = node.assignedSlot || node.parentNode || isShadowRoot(node) && node.host || getDocumentElement(node);
	return isShadowRoot(result) ? result.host : result;
}
function getNearestOverflowAncestor(node) {
	const parentNode = getParentNode(node);
	if (isLastTraversableNode(parentNode)) return (node.ownerDocument || node).body;
	if (isHTMLElement(parentNode) && isOverflowElement(parentNode)) return parentNode;
	return getNearestOverflowAncestor(parentNode);
}
function getOverflowAncestors(node, list, traverseIframes) {
	var _node$ownerDocument2;
	if (list === void 0) list = [];
	if (traverseIframes === void 0) traverseIframes = true;
	const scrollableAncestor = getNearestOverflowAncestor(node);
	const isBody = scrollableAncestor === ((_node$ownerDocument2 = node.ownerDocument) == null ? void 0 : _node$ownerDocument2.body);
	const win = getWindow(scrollableAncestor);
	if (isBody) {
		const frameElement = getFrameElement(win);
		return list.concat(win, win.visualViewport || [], isOverflowElement(scrollableAncestor) ? scrollableAncestor : [], frameElement && traverseIframes ? getOverflowAncestors(frameElement) : []);
	} else return list.concat(scrollableAncestor, getOverflowAncestors(scrollableAncestor, [], traverseIframes));
}
function getFrameElement(win) {
	return win.parent && Object.getPrototypeOf(win.parent) ? win.frameElement : null;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/safeReact.mjs
/**
* A clone of the React namespace for reading APIs that may be missing in older
* supported React versions. Bundlers can rewrite direct `React.someNewApi`
* reads into named imports, which breaks React 17. Reading from this cloned
* object keeps those lookups optional.
*
* @see https://github.com/mui/material-ui/issues/41190#issuecomment-2040873379
*/
var SafeReact = { ...React$3 };
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/useStableCallback.mjs
var useInsertionEffect = SafeReact.useInsertionEffect;
var useSafeInsertionEffect = useInsertionEffect && useInsertionEffect !== SafeReact.useLayoutEffect ? useInsertionEffect : (fn) => fn();
/**
* Stabilizes the function passed so it's always the same between renders.
*
* The function becomes non-reactive to any values it captures.
* It can safely be passed as a dependency of `React.useMemo` and `React.useEffect` without re-triggering them if its captured values change.
*
* The function must only be called inside effects and event handlers, never during render (which throws an error).
*
* This hook is a more permissive version of React 19.2's `React.useEffectEvent` in that it can be passed through contexts and called in event handler props, not just effects.
*/
function useStableCallback(callback) {
	const stable = useRefWithInit(createStableCallback).current;
	stable.next = callback;
	useSafeInsertionEffect(stable.effect);
	return stable.trampoline;
}
function createStableCallback() {
	const stable = {
		next: void 0,
		callback: assertNotCalled,
		trampoline: (...args) => stable.callback?.(...args),
		effect: () => {
			stable.callback = stable.next;
		}
	};
	return stable;
}
function assertNotCalled() {}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/useIsoLayoutEffect.mjs
var noop = () => {};
var useIsoLayoutEffect = typeof document !== "undefined" ? React$3.useLayoutEffect : noop;
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/composite/root/CompositeRootContext.mjs
var CompositeRootContext = /* @__PURE__ */ React$3.createContext(void 0);
function useCompositeRootContext(optional = false) {
	const context = React$3.useContext(CompositeRootContext);
	if (context === void 0 && !optional) throw new Error(formatErrorMessage(16));
	return context;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/useFocusableWhenDisabled.mjs
function useFocusableWhenDisabled(parameters) {
	const { focusableWhenDisabled, disabled, composite = false, tabIndex: tabIndexProp = 0, isNativeButton } = parameters;
	const isFocusableComposite = composite && focusableWhenDisabled !== false;
	const isNonFocusableComposite = composite && focusableWhenDisabled === false;
	return { props: React$3.useMemo(() => {
		const additionalProps = { onKeyDown(event) {
			if (disabled && focusableWhenDisabled && event.key !== "Tab") event.preventDefault();
		} };
		if (!composite) {
			additionalProps.tabIndex = tabIndexProp;
			if (!isNativeButton && disabled) additionalProps.tabIndex = focusableWhenDisabled ? tabIndexProp : -1;
		}
		if (isNativeButton && (focusableWhenDisabled || isFocusableComposite) || !isNativeButton && disabled) additionalProps["aria-disabled"] = disabled;
		if (isNativeButton && (!focusableWhenDisabled || isNonFocusableComposite)) additionalProps.disabled = disabled;
		return additionalProps;
	}, [
		composite,
		disabled,
		focusableWhenDisabled,
		isFocusableComposite,
		isNonFocusableComposite,
		isNativeButton,
		tabIndexProp
	]) };
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/owner.mjs
function ownerDocument(node) {
	return node?.ownerDocument || document;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/dispatchClickWithModifiers.mjs
/**
* Dispatches a constructed click on the target so it carries the source event's
* modifier state, which `click()` always reports as unpressed. Like `click()`,
* the untrusted click still runs native activation behavior (form submission,
* link navigation).
* `detail` defaults to 0 (the native convention for keyboard-generated clicks);
* pass `detail: 1` when the click represents a mouse gesture so consumers keying
* off `detail === 0` don't classify it as a keyboard activation.
*/
function dispatchClickWithModifiers(target, sourceEvent, { detail = 0 } = {}) {
	target.dispatchEvent(new (getWindow(target)).PointerEvent("click", {
		bubbles: true,
		cancelable: true,
		composed: true,
		detail,
		shiftKey: sourceEvent.shiftKey,
		ctrlKey: sourceEvent.ctrlKey,
		altKey: sourceEvent.altKey,
		metaKey: sourceEvent.metaKey
	}));
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/use-button/useButton.mjs
function useButton(parameters = {}) {
	const { disabled = false, focusableWhenDisabled, tabIndex = 0, native: isNativeButton = true, composite: compositeProp } = parameters;
	const elementRef = React$3.useRef(null);
	const compositeRootContext = useCompositeRootContext(true);
	const isCompositeItem = compositeProp ?? compositeRootContext !== void 0;
	const { props: focusableWhenDisabledProps } = useFocusableWhenDisabled({
		focusableWhenDisabled,
		disabled,
		composite: isCompositeItem,
		tabIndex,
		isNativeButton
	});
	const updateDisabled = React$3.useCallback(() => {
		const element = elementRef.current;
		if (!isButtonElement(element)) return;
		if (isCompositeItem && disabled && focusableWhenDisabledProps.disabled === void 0 && element.disabled) element.disabled = false;
	}, [
		disabled,
		focusableWhenDisabledProps.disabled,
		isCompositeItem
	]);
	useIsoLayoutEffect(updateDisabled, [updateDisabled]);
	return {
		getButtonProps: React$3.useCallback((externalProps = {}) => {
			const { onClick: externalOnClick, onMouseDown: externalOnMouseDown, onKeyUp: externalOnKeyUp, onKeyDown: externalOnKeyDown, onPointerDown: externalOnPointerDown, ...otherExternalProps } = externalProps;
			return mergeProps({
				onClick(event) {
					if (disabled) {
						event.preventDefault();
						return;
					}
					externalOnClick?.(event);
				},
				onMouseDown(event) {
					if (!disabled) externalOnMouseDown?.(event);
				},
				onKeyDown(event) {
					if (disabled) return;
					makeEventPreventable(event);
					externalOnKeyDown?.(event);
					if (event.baseUIHandlerPrevented) return;
					const isCurrentTarget = event.target === event.currentTarget;
					const currentTarget = event.currentTarget;
					const isButton = isButtonElement(currentTarget);
					const isLink = !isNativeButton && isValidLinkElement(currentTarget);
					const shouldClick = isCurrentTarget && (isNativeButton ? isButton : !isLink);
					const isEnterKey = event.key === "Enter";
					const isSpaceKey = event.key === " ";
					const role = currentTarget.getAttribute("role");
					const isTextNavigationRole = role?.startsWith("menuitem") || role === "option" || role === "gridcell";
					if (isCurrentTarget && isCompositeItem && isSpaceKey) {
						if (event.defaultPrevented && isTextNavigationRole) return;
						event.preventDefault();
						if (!isNativeButton || isButton) {
							event.preventBaseUIHandler();
							dispatchClickWithModifiers(currentTarget, event);
						}
						return;
					}
					if (!shouldClick || isNativeButton || !isSpaceKey && !isEnterKey) {
						if (isCurrentTarget && isLink && isSpaceKey) event.preventDefault();
						return;
					}
					if (event.defaultPrevented) return;
					event.preventDefault();
					if (isEnterKey) {
						event.preventBaseUIHandler();
						dispatchClickWithModifiers(currentTarget, event);
					}
				},
				onKeyUp(event) {
					if (disabled) return;
					makeEventPreventable(event);
					externalOnKeyUp?.(event);
					if (event.target === event.currentTarget && isNativeButton && isCompositeItem && isButtonElement(event.currentTarget) && event.key === " ") {
						event.preventDefault();
						return;
					}
					if (event.baseUIHandlerPrevented) return;
					if (event.target === event.currentTarget && !isNativeButton && !isCompositeItem && !event.defaultPrevented && event.key === " ") {
						event.preventBaseUIHandler();
						dispatchClickWithModifiers(event.currentTarget, event);
					}
				},
				onPointerDown(event) {
					if (disabled) {
						event.preventDefault();
						return;
					}
					externalOnPointerDown?.(event);
				}
			}, isNativeButton ? { type: "button" } : { role: "button" }, focusableWhenDisabledProps, otherExternalProps);
		}, [
			disabled,
			focusableWhenDisabledProps,
			isCompositeItem,
			isNativeButton
		]),
		buttonRef: useStableCallback((element) => {
			elementRef.current = element;
			updateDisabled();
		})
	};
}
function isButtonElement(elem) {
	return isHTMLElement(elem) && elem.tagName === "BUTTON";
}
function isValidLinkElement(elem) {
	return isHTMLElement(elem) && elem.tagName === "A" && Boolean(elem.href);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/button/Button.mjs
/**
* A button component that can be used to trigger actions.
* Renders a `<button>` element.
*
* Documentation: [Base UI Button](https://base-ui.com/react/components/button)
*/
var Button$1 = /* @__PURE__ */ React$3.forwardRef(function Button(componentProps, forwardedRef) {
	const { render, className, disabled = false, focusableWhenDisabled = false, nativeButton = true, style, ...elementProps } = componentProps;
	const { getButtonProps, buttonRef } = useButton({
		disabled,
		focusableWhenDisabled,
		native: nativeButton
	});
	return useRenderElement("button", componentProps, {
		state: { disabled },
		ref: [forwardedRef, buttonRef],
		props: [elementProps, getButtonProps]
	});
});
//#endregion
//#region components/ui/button.tsx
var buttonVariants = cva("group/button inline-flex shrink-0 items-center justify-center rounded-lg border border-transparent bg-clip-padding text-sm font-medium whitespace-nowrap transition-all outline-none select-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 active:not-aria-[haspopup]:translate-y-px disabled:pointer-events-none disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4", {
	variants: {
		variant: {
			default: "bg-primary text-primary-foreground hover:bg-primary/80",
			outline: "border-border bg-background hover:bg-muted hover:text-foreground aria-expanded:bg-muted aria-expanded:text-foreground dark:border-input dark:bg-input/30 dark:hover:bg-input/50",
			secondary: "bg-secondary text-secondary-foreground hover:bg-[color-mix(in_oklch,var(--secondary),var(--foreground)_5%)] aria-expanded:bg-secondary aria-expanded:text-secondary-foreground",
			ghost: "hover:bg-muted hover:text-foreground aria-expanded:bg-muted aria-expanded:text-foreground dark:hover:bg-muted/50",
			destructive: "bg-destructive/10 text-destructive hover:bg-destructive/20 focus-visible:border-destructive/40 focus-visible:ring-destructive/20 dark:bg-destructive/20 dark:hover:bg-destructive/30 dark:focus-visible:ring-destructive/40",
			link: "text-primary underline-offset-4 hover:underline"
		},
		size: {
			default: "h-8 gap-1.5 px-2.5 has-data-[icon=inline-end]:pr-2 has-data-[icon=inline-start]:pl-2",
			xs: "h-6 gap-1 rounded-[min(var(--radius-md),10px)] px-2 text-xs in-data-[slot=button-group]:rounded-lg has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3",
			sm: "h-7 gap-1 rounded-[min(var(--radius-md),12px)] px-2.5 text-[0.8rem] in-data-[slot=button-group]:rounded-lg has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3.5",
			lg: "h-9 gap-1.5 px-2.5 has-data-[icon=inline-end]:pr-2 has-data-[icon=inline-start]:pl-2",
			icon: "size-8",
			"icon-xs": "size-6 rounded-[min(var(--radius-md),10px)] in-data-[slot=button-group]:rounded-lg [&_svg:not([class*='size-'])]:size-3",
			"icon-sm": "size-7 rounded-[min(var(--radius-md),12px)] in-data-[slot=button-group]:rounded-lg",
			"icon-lg": "size-9"
		}
	},
	defaultVariants: {
		variant: "default",
		size: "default"
	}
});
function Button({ className, variant = "default", size = "default", ...props }) {
	return /* @__PURE__ */ jsx(Button$1, {
		"data-slot": "button",
		className: cn(buttonVariants({
			variant,
			size,
			className
		})),
		...props
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/field-constants/constants.mjs
var DEFAULT_VALIDITY_STATE = {
	badInput: false,
	customError: false,
	patternMismatch: false,
	rangeOverflow: false,
	rangeUnderflow: false,
	stepMismatch: false,
	tooLong: false,
	tooShort: false,
	typeMismatch: false,
	valid: null,
	valueMissing: false
};
var DEFAULT_FIELD_ROOT_STATE = {
	disabled: false,
	valid: null,
	touched: false,
	dirty: false,
	filled: false,
	focused: false
};
var fieldValidityMapping = { valid(value) {
	if (value === null) return null;
	if (value) return { "data-valid": "" };
	return { "data-invalid": "" };
} };
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/field-root-context/FieldRootContext.mjs
var DEFAULT_FIELD_ROOT_CONTEXT = {
	invalid: void 0,
	name: void 0,
	validityData: {
		state: DEFAULT_VALIDITY_STATE,
		errors: [],
		error: "",
		value: "",
		initialValue: null
	},
	setValidityData: NOOP,
	disabled: void 0,
	setTouched: NOOP,
	setDirty: NOOP,
	setFilled: NOOP,
	setFocused: NOOP,
	validationMode: "onSubmit",
	shouldValidateOnChange: () => false,
	state: DEFAULT_FIELD_ROOT_STATE,
	registerFieldControl: NOOP,
	validation: {
		getValidationProps: (_disabled, props = EMPTY_OBJECT) => props,
		inputRef: { current: null },
		registeredInputs: /* @__PURE__ */ new Map(),
		registerInput: NOOP,
		getInputControl: () => null,
		commit: async () => {},
		change: NOOP
	}
};
var FieldRootContext = /* @__PURE__ */ React$3.createContext(DEFAULT_FIELD_ROOT_CONTEXT);
function useFieldRootContext(optional = true) {
	const context = React$3.useContext(FieldRootContext);
	if (context.setValidityData === NOOP && !optional) throw new Error(formatErrorMessage(28));
	return context;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/form-context/FormContext.mjs
var FormContext = /* @__PURE__ */ React$3.createContext({
	elementRef: { current: null },
	formRef: { current: { fields: /* @__PURE__ */ new Map() } },
	errors: {},
	clearErrors: NOOP,
	validationMode: "onSubmit",
	submitAttemptedRef: { current: false }
});
function useFormContext() {
	return React$3.useContext(FormContext);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/useId.mjs
var globalId = 0;
function useGlobalId(idOverride, prefix = "mui") {
	const [defaultId, setDefaultId] = React$3.useState(idOverride);
	const id = idOverride || defaultId;
	React$3.useEffect(() => {
		if (defaultId == null) {
			globalId += 1;
			setDefaultId(`${prefix}-${globalId}`);
		}
	}, [defaultId, prefix]);
	return id;
}
var maybeReactUseId = SafeReact.useId;
/**
*
* @example <div id={useId()} />
* @param idOverride
* @returns {string}
*/
function useId(idOverride, prefix) {
	if (maybeReactUseId !== void 0) {
		const reactId = maybeReactUseId();
		return idOverride ?? (prefix ? `${prefix}-${reactId}` : reactId);
	}
	return useGlobalId(idOverride, prefix);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/useBaseUiId.mjs
/**
* Wraps `useId` and prefixes generated `id`s with `base-ui-`
* @param {string | undefined} idOverride overrides the generated id when provided
* @returns {string | undefined}
*/
function useBaseUiId(idOverride) {
	return useId(idOverride, "base-ui");
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/labelable-provider/LabelableContext.mjs
/**
* A context for providing [labelable elements](https://html.spec.whatwg.org/multipage/forms.html#category-label)\
* with an accessible name (label) and description.
*/
var LabelableContext = /* @__PURE__ */ React$3.createContext({
	controlId: void 0,
	registerControlId: NOOP,
	labelId: void 0,
	setLabelId: NOOP,
	messageIds: [],
	setMessageIds: NOOP,
	getDescriptionProps: (externalProps) => externalProps
});
function useLabelableContext() {
	return React$3.useContext(LabelableContext);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/labelable-provider/useLabelableId.mjs
function useLabelableId(params = {}) {
	const { id, implicit = false, controlRef } = params;
	const { controlId, registerControlId } = useLabelableContext();
	const defaultId = useBaseUiId(id);
	const controlIdForEffect = implicit ? controlId : void 0;
	const controlSourceRef = useRefWithInit(() => Symbol());
	const hasRegisteredRef = React$3.useRef(false);
	const hadExplicitIdRef = React$3.useRef(id != null);
	const unregisterControlId = useStableCallback(() => {
		if (!hasRegisteredRef.current || registerControlId === NOOP) return;
		hasRegisteredRef.current = false;
		registerControlId(controlSourceRef.current, void 0);
	});
	useIsoLayoutEffect(() => {
		if (registerControlId === NOOP) return;
		let nextId;
		if (implicit) {
			const elem = controlRef?.current;
			if (isElement(elem) && elem.closest("label") != null) nextId = id ?? null;
			else nextId = controlIdForEffect ?? defaultId;
		} else if (id != null) {
			hadExplicitIdRef.current = true;
			nextId = id;
		} else if (hadExplicitIdRef.current) nextId = defaultId;
		else {
			unregisterControlId();
			return;
		}
		if (nextId === void 0) {
			unregisterControlId();
			return;
		}
		hasRegisteredRef.current = true;
		registerControlId(controlSourceRef.current, nextId);
	}, [
		id,
		controlRef,
		controlIdForEffect,
		registerControlId,
		implicit,
		defaultId,
		controlSourceRef,
		unregisterControlId
	]);
	React$3.useEffect(() => {
		return unregisterControlId;
	}, [unregisterControlId]);
	return controlId ?? defaultId;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/platform/shared.mjs
/**
* Reads `navigator.userAgent` / `navigator.platform` (legacy but universally
* supported) into a normalized shape. In development, prefers the modern
* `navigator.userAgentData` API on Chromium to avoid DevTools warnings about
* the deprecated reads; that branch is dead-code-eliminated in production
* builds to keep the bundle small.
*
* Returns empty/zero values when `navigator` is undefined (SSR), so every
* derived flag safely evaluates to `false`.
*/
function readRawData() {
	if (typeof navigator === "undefined") return {
		userAgent: "",
		platform: "",
		maxTouchPoints: 0
	};
	return {
		userAgent: navigator.userAgent,
		platform: navigator.platform ?? "",
		maxTouchPoints: navigator.maxTouchPoints ?? 0
	};
}
var { userAgent, platform: platform$1, maxTouchPoints } = readRawData();
var lowerUserAgent = userAgent.toLowerCase();
var lowerPlatform = platform$1.toLowerCase();
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/platform/os.mjs
/** iPhone, iPad (including iPadOS 13+ reporting as macOS), iPod. */
var ios = /^i(os$|p)/.test(lowerPlatform) || lowerPlatform === "macintel" && maxTouchPoints > 1;
/** Android phones, tablets, and embedded Android browsers. */
var ANDROID_STRING = "android";
var android = lowerPlatform === ANDROID_STRING || lowerUserAgent.includes(ANDROID_STRING);
/** macOS desktop. Excludes iPadOS, which reports as `MacIntel`. */
var mac = !ios && lowerPlatform.startsWith("mac");
lowerPlatform.startsWith("win");
!android && /^(linux|chrome os)/.test(lowerPlatform);
/** Any Apple OS (`mac || ios`). */
var apple = mac || ios;
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/platform/engine.mjs
/** WebKit: Safari, all iOS browsers, GNOME Web. Excludes Blink. */
var webkit = typeof CSS !== "undefined" && !!CSS.supports?.("-webkit-backdrop-filter:none");
!webkit && lowerUserAgent.includes("firefox");
!webkit && lowerUserAgent.includes("chrom");
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/platform/screen-reader.mjs
/**
* The user *may* be using VoiceOver — actual activation is not detectable.
* True on any Apple platform (macOS, iOS, iPadOS).
*/
var voiceOver = apple;
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/platform/env.mjs
/** Running in jsdom or HappyDOM (used by unit tests). */
var jsdom = /jsdom|happydom/.test(lowerUserAgent);
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/utils/constants.mjs
var FOCUSABLE_ATTRIBUTE = "data-base-ui-focusable";
var TYPEABLE_SELECTOR = "input:not([type='hidden']):not([disabled]),[contenteditable]:not([contenteditable='false']),textarea:not([disabled])";
var ARROW_LEFT$1 = "ArrowLeft";
var ARROW_RIGHT$1 = "ArrowRight";
var ARROW_UP$1 = "ArrowUp";
var ARROW_DOWN$1 = "ArrowDown";
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/shadowDom.mjs
function activeElement(doc) {
	let element = doc.activeElement;
	while (element?.shadowRoot?.activeElement != null) element = element.shadowRoot.activeElement;
	return element;
}
function contains(parent, child) {
	if (!parent || !child) return false;
	const rootNode = child.getRootNode?.();
	if (parent.contains(child)) return true;
	if (rootNode && isShadowRoot(rootNode)) {
		let next = child;
		while (next) {
			if (parent === next) return true;
			next = next.parentNode || next.host;
		}
	}
	return false;
}
function getTarget(event) {
	if ("composedPath" in event) return event.composedPath()[0];
	return event.target;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/utils/element.mjs
function isTargetInsideEnabledTrigger(target, triggerElements) {
	if (!isElement(target)) return false;
	const targetElement = target;
	if (triggerElements.hasElement(targetElement)) return !targetElement.hasAttribute("data-trigger-disabled");
	for (const [, trigger] of triggerElements.entries()) if (contains(trigger, targetElement)) return !trigger.hasAttribute("data-trigger-disabled");
	return false;
}
function isEventTargetWithin(event, node) {
	if (node == null) return false;
	if ("composedPath" in event) return event.composedPath().includes(node);
	const eventAgain = event;
	return eventAgain.target != null && node.contains(eventAgain.target);
}
function isRootElement(element) {
	return element.matches("html,body");
}
function isTypeableElement(element) {
	return isHTMLElement(element) && element.matches("input:not([type='hidden']):not([disabled]),[contenteditable]:not([contenteditable='false']),textarea:not([disabled])");
}
function isInteractiveElement(element) {
	return element?.closest(`button,a[href],[role="button"],select,[tabindex]:not([tabindex="-1"]),${TYPEABLE_SELECTOR}`) != null;
}
function isTypeableCombobox(element) {
	if (!element) return false;
	return element.getAttribute("role") === "combobox" && isTypeableElement(element);
}
function matchesFocusVisible(element) {
	if (!element || jsdom) return true;
	try {
		return element.matches(":focus-visible");
	} catch (_e) {
		return true;
	}
}
function getFloatingFocusElement(floatingElement) {
	if (!floatingElement) return null;
	return floatingElement.hasAttribute("data-base-ui-focusable") ? floatingElement : floatingElement.querySelector(`[data-base-ui-focusable]`) || floatingElement;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/utils/nodes.mjs
function getNodeChildren(nodes, id, onlyOpenChildren = true) {
	return nodes.filter((node) => node.parentId === id).flatMap((child) => [...!onlyOpenChildren || child.context?.open ? [child] : [], ...getNodeChildren(nodes, child.id, onlyOpenChildren)]);
}
function getNodeAncestors(nodes, id) {
	let allAncestors = [];
	let currentParentId = nodes.find((node) => node.id === id)?.parentId;
	while (currentParentId) {
		const currentNode = nodes.find((node) => node.id === currentParentId);
		currentParentId = currentNode?.parentId;
		if (currentNode) allAncestors = allAncestors.concat(currentNode);
	}
	return allAncestors;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/utils/event.mjs
function stopEvent(event) {
	event.preventDefault();
	event.stopPropagation();
}
function isReactEvent(event) {
	return "nativeEvent" in event;
}
function isVirtualClick(event) {
	if (event.pointerType === "" && event.isTrusted) return true;
	if (android && event.pointerType) return event.type === "click" && event.buttons === 1;
	return event.detail === 0 && !event.pointerType;
}
function isVirtualPointerEvent(event) {
	if (jsdom) return false;
	return !android && event.width === 0 && event.height === 0 || android && event.width === 1 && event.height === 1 && event.pressure === 0 && event.detail === 0 && event.pointerType === "mouse" || event.width < 1 && event.height < 1 && event.pressure === 0 && event.detail === 0 && event.pointerType === "touch";
}
function isMouseLikePointerType(pointerType, strict) {
	const values = ["mouse", "pen"];
	if (!strict) values.push("", void 0);
	return values.includes(pointerType);
}
function isClickLikeEvent(event) {
	const type = event.type;
	return type === "click" || type === "mousedown" || type === "keydown" || type === "keyup";
}
//#endregion
//#region ../../../node_modules/.pnpm/@floating-ui+utils@0.2.12/node_modules/@floating-ui/utils/dist/floating-ui.utils.mjs
var min = Math.min;
var max = Math.max;
var round = Math.round;
var floor = Math.floor;
var createCoords = (v) => ({
	x: v,
	y: v
});
var oppositeSideMap = {
	left: "right",
	right: "left",
	bottom: "top",
	top: "bottom"
};
function clamp$1(start, value, end) {
	return max(start, min(value, end));
}
function evaluate(value, param) {
	return typeof value === "function" ? value(param) : value;
}
function getSide(placement) {
	return placement.split("-")[0];
}
function getAlignment(placement) {
	return placement.split("-")[1];
}
function getOppositeAxis(axis) {
	return axis === "x" ? "y" : "x";
}
function getAxisLength(axis) {
	return axis === "y" ? "height" : "width";
}
function getSideAxis(placement) {
	const firstChar = placement[0];
	return firstChar === "t" || firstChar === "b" ? "y" : "x";
}
function getAlignmentAxis(placement) {
	return getOppositeAxis(getSideAxis(placement));
}
function getAlignmentSides(placement, rects, rtl) {
	if (rtl === void 0) rtl = false;
	const alignment = getAlignment(placement);
	const alignmentAxis = getAlignmentAxis(placement);
	const length = getAxisLength(alignmentAxis);
	let mainAlignmentSide = alignmentAxis === "x" ? alignment === (rtl ? "end" : "start") ? "right" : "left" : alignment === "start" ? "bottom" : "top";
	if (rects.reference[length] > rects.floating[length]) mainAlignmentSide = getOppositePlacement(mainAlignmentSide);
	return [mainAlignmentSide, getOppositePlacement(mainAlignmentSide)];
}
function getExpandedPlacements(placement) {
	const oppositePlacement = getOppositePlacement(placement);
	return [
		getOppositeAlignmentPlacement(placement),
		oppositePlacement,
		getOppositeAlignmentPlacement(oppositePlacement)
	];
}
function getOppositeAlignmentPlacement(placement) {
	return placement.includes("start") ? placement.replace("start", "end") : placement.replace("end", "start");
}
var lrPlacement = ["left", "right"];
var rlPlacement = ["right", "left"];
var tbPlacement = ["top", "bottom"];
var btPlacement = ["bottom", "top"];
function getSideList(side, isStart, rtl) {
	switch (side) {
		case "top":
		case "bottom":
			if (rtl) return isStart ? rlPlacement : lrPlacement;
			return isStart ? lrPlacement : rlPlacement;
		case "left":
		case "right": return isStart ? tbPlacement : btPlacement;
		default: return [];
	}
}
function getOppositeAxisPlacements(placement, flipAlignment, direction, rtl) {
	const alignment = getAlignment(placement);
	let list = getSideList(getSide(placement), direction === "start", rtl);
	if (alignment) {
		list = list.map((side) => side + "-" + alignment);
		if (flipAlignment) list = list.concat(list.map(getOppositeAlignmentPlacement));
	}
	return list;
}
function getOppositePlacement(placement) {
	const side = getSide(placement);
	return oppositeSideMap[side] + placement.slice(side.length);
}
function expandPaddingObject(padding) {
	var _padding$top, _padding$right, _padding$bottom, _padding$left;
	return {
		top: (_padding$top = padding.top) != null ? _padding$top : 0,
		right: (_padding$right = padding.right) != null ? _padding$right : 0,
		bottom: (_padding$bottom = padding.bottom) != null ? _padding$bottom : 0,
		left: (_padding$left = padding.left) != null ? _padding$left : 0
	};
}
function getPaddingObject(padding) {
	return typeof padding !== "number" ? expandPaddingObject(padding) : {
		top: padding,
		right: padding,
		bottom: padding,
		left: padding
	};
}
function rectToClientRect(rect) {
	const { x, y, width, height } = rect;
	return {
		width,
		height,
		top: y,
		left: x,
		right: x + width,
		bottom: y + height,
		x,
		y
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/utils/composite.mjs
function isIndexOutOfListBounds(list, index) {
	return index < 0 || index >= list.length;
}
function getMinListIndex(listRef, disabledIndices) {
	return findNonDisabledListIndex(listRef.current, { disabledIndices });
}
function getMaxListIndex(listRef, disabledIndices) {
	return findNonDisabledListIndex(listRef.current, {
		decrement: true,
		startingIndex: listRef.current.length,
		disabledIndices
	});
}
function findNonDisabledListIndex(list, { startingIndex = -1, decrement = false, disabledIndices, amount = 1 } = {}) {
	let index = startingIndex;
	do
		index += decrement ? -amount : amount;
	while (index >= 0 && index <= list.length - 1 && isListIndexDisabled(list, index, disabledIndices));
	return index;
}
function isListIndexDisabled(list, index, disabledIndices) {
	if (typeof disabledIndices === "function" ? disabledIndices(index) : disabledIndices?.includes(index) ?? false) return true;
	const element = list[index];
	if (!element) return false;
	if (!isElementVisible(element)) return true;
	if (element.matches(":disabled")) return true;
	return !disabledIndices && (element.hasAttribute("disabled") || element.getAttribute("aria-disabled") === "true");
}
function isHiddenByStyles(styles) {
	return styles.visibility === "hidden" || styles.visibility === "collapse";
}
function isElementVisible(element, styles = element ? getComputedStyle$1(element) : null) {
	if (!element || !element.isConnected || !styles || isHiddenByStyles(styles)) return false;
	if (typeof element.checkVisibility === "function") return element.checkVisibility();
	return styles.display !== "none" && styles.display !== "contents";
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/utils/tabbable.mjs
var CANDIDATE_SELECTOR = "a[href],button,input,select,textarea,summary,details,iframe,object,embed,[tabindex],[contenteditable]:not([contenteditable=\"false\"]),audio[controls],video[controls]";
function getParentElement(element) {
	const assignedSlot = element.assignedSlot;
	if (assignedSlot) return assignedSlot;
	if (element.parentElement) return element.parentElement;
	const rootNode = element.getRootNode();
	return isShadowRoot(rootNode) ? rootNode.host : null;
}
function getDetailsSummary(details) {
	for (const child of Array.from(details.children)) if (getNodeName(child) === "summary") return child;
	return null;
}
function isWithinOpenDetailsSummary(element, details) {
	const summary = getDetailsSummary(details);
	return !!summary && (element === summary || contains(summary, element));
}
function isFocusableCandidate(element) {
	const nodeName = element ? getNodeName(element) : "";
	return element != null && element.matches(CANDIDATE_SELECTOR) && (nodeName !== "summary" || element.parentElement != null && getNodeName(element.parentElement) === "details" && getDetailsSummary(element.parentElement) === element) && (nodeName !== "details" || getDetailsSummary(element) == null) && (nodeName !== "input" || element.type !== "hidden");
}
function isFocusableElement(element) {
	if (!isFocusableCandidate(element) || !element.isConnected || element.matches(":disabled")) return false;
	for (let current = element; current; current = getParentElement(current)) {
		const isAncestor = current !== element;
		const isSlot = getNodeName(current) === "slot";
		if (current.hasAttribute("inert")) return false;
		if (isAncestor && getNodeName(current) === "details" && !current.open && !isWithinOpenDetailsSummary(element, current) || current.hasAttribute("hidden") || !isSlot && !isVisibleInTabbableTree(current, isAncestor)) return false;
	}
	return true;
}
function isVisibleInTabbableTree(element, isAncestor) {
	const styles = getComputedStyle$1(element);
	if (!isAncestor) return isElementVisible(element, styles);
	return styles.display !== "none";
}
function getTabIndex(element) {
	const tabIndex = element.tabIndex;
	if (tabIndex < 0) {
		const nodeName = getNodeName(element);
		if (nodeName === "details" || nodeName === "audio" || nodeName === "video" || isHTMLElement(element) && element.isContentEditable) return 0;
	}
	return tabIndex;
}
function getNamedRadioInput(element) {
	if (getNodeName(element) !== "input") return null;
	const input = element;
	return input.type === "radio" && input.name !== "" ? input : null;
}
function isTabbableRadio(element, candidates) {
	const input = getNamedRadioInput(element);
	if (!input) return true;
	const checkedRadio = candidates.find((candidate) => {
		const radio = getNamedRadioInput(candidate);
		return radio?.name === input.name && radio.form === input.form && radio.checked;
	});
	if (checkedRadio) return checkedRadio === input;
	return candidates.find((candidate) => {
		const radio = getNamedRadioInput(candidate);
		return radio?.name === input.name && radio.form === input.form;
	}) === input;
}
function getComposedChildren(container) {
	if (isHTMLElement(container) && getNodeName(container) === "slot") {
		const assignedElements = container.assignedElements({ flatten: true });
		if (assignedElements.length > 0) return assignedElements;
	}
	if (isHTMLElement(container) && container.shadowRoot) return Array.from(container.shadowRoot.children);
	return Array.from(container.children);
}
function appendCandidates(container, list) {
	getComposedChildren(container).forEach((child) => {
		if (isFocusableCandidate(child)) list.push(child);
		appendCandidates(child, list);
	});
}
function appendMatchingElements(container, selector, list) {
	getComposedChildren(container).forEach((child) => {
		if (isHTMLElement(child) && child.matches(selector)) list.push(child);
		appendMatchingElements(child, selector, list);
	});
}
function isTabbable(element) {
	return isFocusableElement(element) && getTabIndex(element) >= 0;
}
function focusable(container) {
	const candidates = [];
	appendCandidates(container, candidates);
	return candidates.filter(isFocusableElement);
}
function tabbable(container) {
	const candidates = focusable(container);
	return candidates.filter((element) => getTabIndex(element) >= 0 && isTabbableRadio(element, candidates));
}
function getTabbableIn(container, dir) {
	const list = tabbable(container);
	const len = list.length;
	if (len === 0) return;
	const active = activeElement(ownerDocument(container));
	const index = list.indexOf(active);
	return list[index === -1 ? dir === 1 ? 0 : len - 1 : index + dir];
}
function getNextTabbable(referenceElement) {
	return getTabbableIn(ownerDocument(referenceElement).body, 1) || referenceElement;
}
function getPreviousTabbable(referenceElement) {
	return getTabbableIn(ownerDocument(referenceElement).body, -1) || referenceElement;
}
function isOutsideEvent(event, container) {
	const containerElement = container || event.currentTarget;
	const relatedTarget = event.relatedTarget;
	return !relatedTarget || !contains(containerElement, relatedTarget);
}
function disableFocusInside(container) {
	tabbable(container).forEach((element) => {
		element.dataset.tabindex = element.getAttribute("tabindex") || "";
		element.setAttribute("tabindex", "-1");
	});
}
function enableFocusInside(container) {
	const elements = [];
	appendMatchingElements(container, "[data-tabindex]", elements);
	elements.forEach((element) => {
		const tabindex = element.dataset.tabindex;
		delete element.dataset.tabindex;
		if (tabindex) element.setAttribute("tabindex", tabindex);
		else element.removeAttribute("tabindex");
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/useOnMount.mjs
/**
* A React.useEffect equivalent that runs once, when the component is mounted.
*/
function useOnMount(fn) {
	React$3.useEffect(fn, EMPTY_ARRAY$1);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/useTimeout.mjs
var EMPTY$1 = 0;
var Timeout = class Timeout {
	static create() {
		return new Timeout();
	}
	currentId = EMPTY$1;
	/**
	* Executes `fn` after `delay`, clearing any previously scheduled call.
	*/
	start(delay, fn) {
		this.clear();
		this.currentId = setTimeout(() => {
			this.currentId = EMPTY$1;
			fn();
		}, delay);
	}
	isStarted() {
		return this.currentId !== EMPTY$1;
	}
	clear = () => {
		if (this.currentId !== EMPTY$1) {
			clearTimeout(this.currentId);
			this.currentId = EMPTY$1;
		}
	};
	disposeEffect = () => {
		return this.clear;
	};
};
/**
* A `setTimeout` with automatic cleanup and guard.
*/
function useTimeout() {
	const timeout = useRefWithInit(Timeout.create).current;
	useOnMount(timeout.disposeEffect);
	return timeout;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/useAnimationFrame.mjs
/** Unlike `setTimeout`, rAF doesn't guarantee a positive integer return value, so we can't have
* a monomorphic `uint` type with `0` meaning empty.
* See warning note at:
* https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame#return_value */
var EMPTY = null;
globalThis.requestAnimationFrame;
var Scheduler = class {
	callbacks = [];
	callbacksCount = 0;
	nextId = 1;
	startId = 1;
	isScheduled = false;
	tick = (timestamp) => {
		this.isScheduled = false;
		const currentCallbacks = this.callbacks;
		const currentCallbacksCount = this.callbacksCount;
		this.callbacks = [];
		this.callbacksCount = 0;
		this.startId = this.nextId;
		if (currentCallbacksCount > 0) for (let i = 0; i < currentCallbacks.length; i += 1) currentCallbacks[i]?.(timestamp);
	};
	request(fn) {
		const id = this.nextId;
		this.nextId += 1;
		this.callbacks.push(fn);
		this.callbacksCount += 1;
		if (!this.isScheduled || false) {
			requestAnimationFrame(this.tick);
			this.isScheduled = true;
		}
		return id;
	}
	cancel(id) {
		const index = id - this.startId;
		if (index < 0 || index >= this.callbacks.length) return;
		this.callbacks[index] = null;
		this.callbacksCount -= 1;
	}
};
var scheduler = new Scheduler();
var AnimationFrame = class AnimationFrame {
	static create() {
		return new AnimationFrame();
	}
	static request(fn) {
		return scheduler.request(fn);
	}
	static cancel(id) {
		return scheduler.cancel(id);
	}
	currentId = EMPTY;
	/**
	* Executes `fn` after `delay`, clearing any previously scheduled call.
	*/
	request(fn) {
		this.cancel();
		this.currentId = scheduler.request(() => {
			this.currentId = EMPTY;
			fn();
		});
	}
	cancel = () => {
		if (this.currentId !== EMPTY) {
			scheduler.cancel(this.currentId);
			this.currentId = EMPTY;
		}
	};
	disposeEffect = () => {
		return this.cancel;
	};
};
/**
* A `requestAnimationFrame` with automatic cleanup and guard.
*/
function useAnimationFrame() {
	const timeout = useRefWithInit(AnimationFrame.create).current;
	useOnMount(timeout.disposeEffect);
	return timeout;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/resolveRef.mjs
/**
* If the provided argument is a ref object, returns its `current` value.
* Otherwise, returns the argument itself.
*/
function resolveRef(maybeRef) {
	if (maybeRef == null) return maybeRef;
	return "current" in maybeRef ? maybeRef.current : maybeRef;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/useAnimationsFinished.mjs
/**
* Executes a function once all animations have finished on the provided element.
* If an animation is canceled, waits for any replacement animations before executing.
* @param elementOrRef - The element to watch for animations.
* @param waitForStartingStyleRemoved - Whether to wait for [data-starting-style] to be removed before checking for animations.
* @returns A function that takes a callback to execute once all animations have finished, and an optional AbortSignal to abort the callback
*/
function useAnimationsFinished(elementOrRef, waitForStartingStyleRemoved = false) {
	const frame = useAnimationFrame();
	return useStableCallback((fnToExecute, signal = null) => {
		frame.cancel();
		const element = resolveRef(elementOrRef);
		if (element == null) return;
		const resolvedElement = element;
		const done = () => {
			ReactDOM.flushSync(fnToExecute);
		};
		if (typeof resolvedElement.getAnimations !== "function" || globalThis.BASE_UI_ANIMATIONS_DISABLED) {
			fnToExecute();
			return;
		}
		function exec() {
			Promise.all(resolvedElement.getAnimations().map((animation) => animation.finished)).then(() => {
				if (!signal?.aborted) done();
			}, () => {
				if (signal?.aborted) return;
				if (resolvedElement.getAnimations().some((animation) => animation.pending || animation.playState !== "finished")) {
					exec();
					return;
				}
				done();
			});
		}
		if (waitForStartingStyleRemoved) {
			const startingStyleAttribute = "data-starting-style";
			if (!resolvedElement.hasAttribute(startingStyleAttribute)) {
				frame.request(exec);
				return;
			}
			const attributeObserver = new MutationObserver(() => {
				if (!resolvedElement.hasAttribute(startingStyleAttribute)) {
					attributeObserver.disconnect();
					exec();
				}
			});
			attributeObserver.observe(resolvedElement, {
				attributes: true,
				attributeFilter: [startingStyleAttribute]
			});
			signal?.addEventListener("abort", () => attributeObserver.disconnect(), { once: true });
			return;
		}
		frame.request(exec);
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/useOpenChangeComplete.mjs
/**
* Calls the provided function when the CSS open/close animation or transition completes.
*/
function useOpenChangeComplete(parameters) {
	const { enabled = true, open, ref, onComplete: onCompleteParam } = parameters;
	const onComplete = useStableCallback(onCompleteParam);
	const runOnceAnimationsFinish = useAnimationsFinished(ref, open);
	React$3.useEffect(() => {
		if (!enabled) return;
		const abortController = new AbortController();
		runOnceAnimationsFinish(onComplete, abortController.signal);
		return () => {
			abortController.abort();
		};
	}, [
		enabled,
		open,
		onComplete,
		runOnceAnimationsFinish
	]);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/stateAttributesMapping.mjs
var TransitionStatusDataAttributes = /* @__PURE__ */ function(TransitionStatusDataAttributes) {
	/**
	* Present when the component begins animating in.
	*/
	TransitionStatusDataAttributes["startingStyle"] = "data-starting-style";
	/**
	* Present when the component is animating out.
	*/
	TransitionStatusDataAttributes["endingStyle"] = "data-ending-style";
	return TransitionStatusDataAttributes;
}({});
var STARTING_HOOK = { "data-starting-style": "" };
var ENDING_HOOK = { "data-ending-style": "" };
var transitionStatusMapping = { transitionStatus(value) {
	if (value === "starting") return STARTING_HOOK;
	if (value === "ending") return ENDING_HOOK;
	return null;
} };
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/useTransitionStatus.mjs
/**
* Provides a status string for CSS animations.
* @param open - a boolean that determines if the element is open.
* @param enableIdleState - a boolean that enables the `'idle'` state between `'starting'` and `'ending'`
*/
function useTransitionStatus(open, enableIdleState = false, deferEndingState = false) {
	const [transitionStatus, setTransitionStatus] = React$3.useState(open && enableIdleState ? "idle" : void 0);
	const [mounted, setMounted] = React$3.useState(open);
	if (open && !mounted) {
		setMounted(true);
		setTransitionStatus("starting");
	}
	if (!open && mounted && transitionStatus !== "ending" && !deferEndingState) setTransitionStatus("ending");
	if (!open && !mounted && transitionStatus === "ending") setTransitionStatus(void 0);
	useIsoLayoutEffect(() => {
		if (!open && mounted && transitionStatus !== "ending" && deferEndingState) {
			const frame = AnimationFrame.request(() => {
				setTransitionStatus("ending");
			});
			return () => {
				AnimationFrame.cancel(frame);
			};
		}
	}, [
		open,
		mounted,
		transitionStatus,
		deferEndingState
	]);
	useIsoLayoutEffect(() => {
		if (!open || enableIdleState) return;
		const frame = AnimationFrame.request(() => {
			setTransitionStatus(void 0);
		});
		return () => {
			AnimationFrame.cancel(frame);
		};
	}, [enableIdleState, open]);
	useIsoLayoutEffect(() => {
		if (!open || !enableIdleState) return;
		if (open && mounted && transitionStatus !== "idle") setTransitionStatus("starting");
		const frame = AnimationFrame.request(() => {
			setTransitionStatus("idle");
		});
		return () => {
			AnimationFrame.cancel(frame);
		};
	}, [
		enableIdleState,
		open,
		mounted,
		transitionStatus
	]);
	return {
		mounted,
		setMounted,
		transitionStatus
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/useControlled.mjs
function useControlled({ controlled, default: defaultProp, name, state = "value" }) {
	const { current: isControlled } = React$3.useRef(controlled !== void 0);
	const [valueState, setValue] = React$3.useState(defaultProp);
	return [isControlled ? controlled : valueState, React$3.useCallback((newValue) => {
		if (!isControlled) setValue(newValue);
	}, [])];
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/field-register-control/useRegisterFieldControl.mjs
function useRegisterFieldControl(controlRef, id, value, getFormValueOverride, enabled = true, name) {
	const { registerFieldControl } = useFieldRootContext();
	const sourceRef = useRefWithInit(() => Symbol());
	useIsoLayoutEffect(() => {
		const source = sourceRef.current;
		if (!enabled) {
			registerFieldControl(source, void 0);
			return;
		}
		registerFieldControl(source, {
			controlRef,
			getValue: getFormValueOverride,
			id,
			name,
			value
		});
	}, [
		controlRef,
		enabled,
		getFormValueOverride,
		id,
		name,
		registerFieldControl,
		sourceRef,
		value
	]);
	useIsoLayoutEffect(() => {
		const source = sourceRef.current;
		return () => {
			registerFieldControl(source, void 0);
		};
	}, [registerFieldControl, sourceRef]);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/reason-parts.mjs
var none = "none";
var triggerPress = "trigger-press";
var triggerHover = "trigger-hover";
var triggerFocus = "trigger-focus";
var outsidePress = "outside-press";
var itemPress = "item-press";
var closePress = "close-press";
var focusOut = "focus-out";
var escapeKey = "escape-key";
var listNavigation = "list-navigation";
var cancelOpen = "cancel-open";
var disabled = "disabled";
var missing = "missing";
var initial = "initial";
var imperativeAction = "imperative-action";
var windowResize = "window-resize";
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/createBaseUIEventDetails.mjs
/**
* Maps a change `reason` string to the corresponding native event type.
*/
/**
* Details of custom change events emitted by Base UI components.
*/
/**
* Details of custom generic events emitted by Base UI components.
*/
/**
* Creates a Base UI event details object with the given reason and utilities
* for preventing Base UI's internal event handling.
*/
function createChangeEventDetails(reason, event, trigger, customProperties) {
	let canceled = false;
	let allowPropagation = false;
	const custom = customProperties ?? EMPTY_OBJECT;
	return {
		reason,
		event: event ?? new Event("base-ui"),
		cancel() {
			canceled = true;
		},
		allowPropagation() {
			allowPropagation = true;
		},
		get isCanceled() {
			return canceled;
		},
		get isPropagationAllowed() {
			return allowPropagation;
		},
		trigger,
		...custom
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/field/control/FieldControl.mjs
/**
* The form control to label and validate.
* Renders an `<input>` element.
*
* You can omit this part and use any Base UI input component instead. For example,
* [Input](https://base-ui.com/react/components/input), [Checkbox](https://base-ui.com/react/components/checkbox),
* or [Select](https://base-ui.com/react/components/select), among others, will work with Field out of the box.
*
* Documentation: [Base UI Field](https://base-ui.com/react/components/field)
*/
var FieldControl = /* @__PURE__ */ React$3.forwardRef(function FieldControl(componentProps, forwardedRef) {
	const { render, className, id: idProp, name: nameProp, value: valueProp, disabled: disabledProp = false, onValueChange, defaultValue, autoFocus = false, style, ...elementProps } = componentProps;
	const { state: fieldState, name: fieldName, disabled: fieldDisabled, setTouched, setDirty, validityData, setFocused, setFilled, validationMode, validation } = useFieldRootContext();
	const { clearErrors } = useFormContext();
	const disabled = fieldDisabled || disabledProp;
	const name = fieldName ?? nameProp;
	const state = {
		...fieldState,
		disabled
	};
	const { labelId } = useLabelableContext();
	const id = useLabelableId({ id: idProp });
	useIsoLayoutEffect(() => {
		const hasExternalValue = valueProp != null;
		if (validation.inputRef.current?.value || hasExternalValue && valueProp !== "") setFilled(true);
		else if (hasExternalValue && valueProp === "") setFilled(false);
	}, [
		validation.inputRef,
		setFilled,
		valueProp
	]);
	const inputRef = React$3.useRef(null);
	useIsoLayoutEffect(() => {
		if (autoFocus && inputRef.current === activeElement(ownerDocument(inputRef.current))) setFocused(true);
	}, [autoFocus, setFocused]);
	const [valueUnwrapped] = useControlled({
		controlled: valueProp,
		default: defaultValue,
		name: "FieldControl",
		state: "value"
	});
	const isControlled = valueProp !== void 0;
	const value = isControlled ? valueUnwrapped : void 0;
	const getValueFromInput = useStableCallback(() => validation.inputRef.current?.value);
	useRegisterFieldControl(validation.inputRef, id, value, getValueFromInput, !disabled, nameProp);
	return useRenderElement("input", componentProps, {
		ref: [forwardedRef, inputRef],
		state,
		props: [
			{
				id,
				disabled,
				name,
				ref: validation.inputRef,
				"aria-labelledby": labelId,
				autoFocus,
				...isControlled ? { value } : { defaultValue },
				onChange(event) {
					const inputValue = event.currentTarget.value;
					onValueChange?.(inputValue, createChangeEventDetails(none, event.nativeEvent));
					setDirty(inputValue !== (validityData.initialValue ?? ""));
					setFilled(inputValue !== "");
					if (!event.nativeEvent.defaultPrevented) {
						clearErrors(name);
						validation.change(inputValue);
					}
				},
				onFocus() {
					setFocused(true);
				},
				onBlur(event) {
					setTouched(true);
					setFocused(false);
					if (validationMode === "onBlur") validation.commit(event.currentTarget.value);
				},
				onKeyDown(event) {
					if (event.currentTarget.tagName === "INPUT" && event.key === "Enter") {
						setTouched(true);
						validation.commit(event.currentTarget.value);
					}
				}
			},
			elementProps,
			(props) => validation.getValidationProps(disabled, props)
		],
		stateAttributesMapping: fieldValidityMapping
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/input/Input.mjs
/**
* A native input element that automatically works with [Field](https://base-ui.com/react/components/field).
* Renders an `<input>` element.
*
* Documentation: [Base UI Input](https://base-ui.com/react/components/input)
*/
var Input$1 = /* @__PURE__ */ React$3.forwardRef(function Input(props, forwardedRef) {
	return /* @__PURE__ */ jsx(FieldControl, {
		ref: forwardedRef,
		...props
	});
});
//#endregion
//#region components/ui/input.tsx
function Input({ className, type, ...props }) {
	return /* @__PURE__ */ jsx(Input$1, {
		type,
		"data-slot": "input",
		className: cn("h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-base transition-colors outline-none file:inline-flex file:h-6 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-input/50 disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 md:text-sm dark:bg-input/30 dark:disabled:bg-input/80 dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40", className),
		...props
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/dialog/root/DialogRootContext.mjs
var DialogRootContext = /* @__PURE__ */ React$3.createContext(void 0);
function useDialogRootContext(optional) {
	const store = React$3.useContext(DialogRootContext);
	if (!optional && store === void 0) throw new Error(formatErrorMessage(27));
	return store;
}
(function(CommonPopupDataAttributes) {
	/**
	* Present when the popup is open.
	*/
	CommonPopupDataAttributes["open"] = "data-open";
	/**
	* Present when the popup is closed.
	*/
	CommonPopupDataAttributes["closed"] = "data-closed";
	/**
	* Present when the popup begins animating in.
	*/
	CommonPopupDataAttributes[CommonPopupDataAttributes["startingStyle"] = TransitionStatusDataAttributes.startingStyle] = "startingStyle";
	/**
	* Present when the popup is animating out.
	*/
	CommonPopupDataAttributes[CommonPopupDataAttributes["endingStyle"] = TransitionStatusDataAttributes.endingStyle] = "endingStyle";
	/**
	* Present when the anchor is hidden.
	*/
	CommonPopupDataAttributes["anchorHidden"] = "data-anchor-hidden";
	/**
	* Indicates which side the popup is positioned relative to the trigger.
	* @type { 'top' | 'bottom' | 'left' | 'right' | 'inline-end' | 'inline-start'}
	*/
	CommonPopupDataAttributes["side"] = "data-side";
	/**
	* Indicates how the popup is aligned relative to specified side.
	* @type {'start' | 'center' | 'end'}
	*/
	CommonPopupDataAttributes["align"] = "data-align";
	return CommonPopupDataAttributes;
})({});
var TRIGGER_HOOK = { "data-popup-open": "" };
var PRESSABLE_TRIGGER_HOOK = {
	"data-popup-open": "",
	"data-pressed": ""
};
var POPUP_OPEN_HOOK = { "data-open": "" };
var POPUP_CLOSED_HOOK = { "data-closed": "" };
var ANCHOR_HIDDEN_HOOK = { "data-anchor-hidden": "" };
var triggerOpenStateMapping = { open(value) {
	if (value) return TRIGGER_HOOK;
	return null;
} };
var pressableTriggerOpenStateMapping = { open(value) {
	if (value) return PRESSABLE_TRIGGER_HOOK;
	return null;
} };
var popupStateMapping = {
	open(value) {
		if (value) return POPUP_OPEN_HOOK;
		return POPUP_CLOSED_HOOK;
	},
	anchorHidden(value) {
		if (value) return ANCHOR_HIDDEN_HOOK;
		return null;
	}
};
var popupTransitionStateMapping = {
	...popupStateMapping,
	...transitionStatusMapping
};
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/dialog/backdrop/DialogBackdrop.mjs
/**
* An overlay displayed beneath the popup.
* Renders a `<div>` element.
*
* Documentation: [Base UI Dialog](https://base-ui.com/react/components/dialog)
*/
var DialogBackdrop = /* @__PURE__ */ React$3.forwardRef(function DialogBackdrop(componentProps, forwardedRef) {
	const { render, className, style, forceRender = false, ...elementProps } = componentProps;
	const store = useDialogRootContext();
	const open = store.useState("open");
	const nested = store.useState("nested");
	const mounted = store.useState("mounted");
	return useRenderElement("div", componentProps, {
		state: {
			open,
			transitionStatus: store.useState("transitionStatus")
		},
		ref: [store.context.backdropRef, forwardedRef],
		stateAttributesMapping: popupTransitionStateMapping,
		props: [{
			role: "presentation",
			hidden: !mounted,
			style: {
				userSelect: "none",
				WebkitUserSelect: "none"
			}
		}, elementProps],
		enabled: forceRender || !nested
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/dialog/close/DialogClose.mjs
/**
* A button that closes the dialog.
* Renders a `<button>` element.
*
* Documentation: [Base UI Dialog](https://base-ui.com/react/components/dialog)
*/
var DialogClose = /* @__PURE__ */ React$3.forwardRef(function DialogClose(componentProps, forwardedRef) {
	const { render, className, style, disabled = false, nativeButton = true, ...elementProps } = componentProps;
	const store = useDialogRootContext();
	const open = store.useState("open");
	const { getButtonProps, buttonRef } = useButton({
		disabled,
		native: nativeButton
	});
	const state = { disabled };
	function handleClick(event) {
		if (open) store.setOpen(false, createChangeEventDetails(closePress, event.nativeEvent));
	}
	return useRenderElement("button", componentProps, {
		state,
		ref: [forwardedRef, buttonRef],
		props: [
			{ onClick: handleClick },
			elementProps,
			getButtonProps
		]
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/dialog/description/DialogDescription.mjs
/**
* A paragraph with additional information about the dialog.
* Renders a `<p>` element.
*
* Documentation: [Base UI Dialog](https://base-ui.com/react/components/dialog)
*/
var DialogDescription = /* @__PURE__ */ React$3.forwardRef(function DialogDescription(componentProps, forwardedRef) {
	const { render, className, style, id: idProp, ...elementProps } = componentProps;
	const store = useDialogRootContext();
	const id = useBaseUiId(idProp);
	store.useSyncedValueWithCleanup("descriptionElementId", id);
	return useRenderElement("p", componentProps, {
		ref: forwardedRef,
		props: [{ id }, elementProps]
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/hooks/useHoverShared.mjs
function resolveValue(value, pointerType) {
	if (pointerType != null && !isMouseLikePointerType(pointerType)) return 0;
	if (typeof value === "function") return value();
	return value;
}
function getDelay(value, prop, pointerType) {
	const result = resolveValue(value, pointerType);
	if (typeof result === "number") return result;
	return result?.[prop];
}
function getRestMs(value) {
	if (typeof value === "function") return value();
	return value;
}
function isClickLikeOpenEvent(openEventType, interactedInside) {
	return interactedInside || openEventType === "click" || openEventType === "mousedown";
}
function isHoverOpenEvent(openEventType) {
	return openEventType?.includes("mouse") && openEventType !== "mousedown";
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/components/FloatingDelayGroup.mjs
var FloatingDelayGroupContext = /* @__PURE__ */ React$3.createContext({
	hasProvider: false,
	timeoutMs: 0,
	delayRef: { current: 0 },
	initialDelayRef: { current: 0 },
	timeout: new Timeout(),
	currentIdRef: { current: null },
	currentContextRef: { current: null }
});
function resetDelayRef(delayRef, initialDelayRef) {
	delayRef.current = initialDelayRef.current;
}
/**
* Enables grouping when called inside a component that's a child of a
* `FloatingDelayGroup`.
* @see https://floating-ui.com/docs/FloatingDelayGroup
* @internal
*/
function useDelayGroup(context, options = { open: false }) {
	const { open } = options;
	const store = "rootStore" in context ? context.rootStore : context;
	const floatingId = store.useState("floatingId");
	const { currentIdRef, delayRef, timeoutMs, initialDelayRef, currentContextRef, hasProvider, timeout } = React$3.useContext(FloatingDelayGroupContext);
	const [isInstantPhase, setIsInstantPhase] = React$3.useState(false);
	const openRef = React$3.useRef(open);
	useIsoLayoutEffect(() => {
		openRef.current = open;
	}, [open]);
	useIsoLayoutEffect(() => {
		function unset() {
			currentContextRef.current?.setIsInstantPhase(false);
			currentIdRef.current = null;
			currentContextRef.current = null;
			delayRef.current = initialDelayRef.current;
			timeout.clear();
		}
		if (!currentIdRef.current) return;
		if (!open && currentIdRef.current === floatingId) {
			setIsInstantPhase(false);
			if (timeoutMs) {
				const closingId = floatingId;
				timeout.start(timeoutMs, () => {
					if (store.select("open") || currentIdRef.current && currentIdRef.current !== closingId) return;
					unset();
				});
				return () => {
					if (openRef.current || currentIdRef.current !== closingId) timeout.clear();
				};
			}
			unset();
		}
	}, [
		open,
		floatingId,
		currentIdRef,
		delayRef,
		timeoutMs,
		initialDelayRef,
		currentContextRef,
		timeout,
		store
	]);
	useIsoLayoutEffect(() => {
		if (!open) return;
		const prevContext = currentContextRef.current;
		const prevId = currentIdRef.current;
		timeout.clear();
		currentContextRef.current = {
			onOpenChange: store.setOpen,
			setIsInstantPhase
		};
		currentIdRef.current = floatingId;
		delayRef.current = {
			open: 0,
			close: getDelay(initialDelayRef.current, "close")
		};
		if (prevId !== null && prevId !== floatingId) {
			setIsInstantPhase(true);
			prevContext?.setIsInstantPhase(true);
			prevContext?.onOpenChange(false, createChangeEventDetails(none));
		} else {
			setIsInstantPhase(false);
			prevContext?.setIsInstantPhase(false);
		}
	}, [
		open,
		floatingId,
		store,
		currentIdRef,
		delayRef,
		initialDelayRef,
		currentContextRef,
		timeout
	]);
	useIsoLayoutEffect(() => {
		return () => {
			if (currentIdRef.current === floatingId) {
				currentContextRef.current = null;
				if (!openRef.current) return;
				currentIdRef.current = null;
				resetDelayRef(delayRef, initialDelayRef);
				timeout.clear();
			}
		};
	}, [
		currentContextRef,
		currentIdRef,
		delayRef,
		floatingId,
		initialDelayRef,
		timeout
	]);
	return React$3.useMemo(() => ({
		hasProvider,
		delayRef,
		isInstantPhase
	}), [
		hasProvider,
		delayRef,
		isInstantPhase
	]);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/addEventListener.mjs
/**
* Adds an event listener and returns a cleanup function to remove it.
*/
function addEventListener(target, type, listener, options) {
	target.addEventListener(type, listener, options);
	return () => {
		target.removeEventListener(type, listener, options);
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/mergeCleanups.mjs
/**
* Combines multiple cleanup functions into a single cleanup function.
*/
function mergeCleanups(...cleanups) {
	return () => {
		for (let i = 0; i < cleanups.length; i += 1) {
			const cleanup = cleanups[i];
			if (cleanup) cleanup();
		}
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/useValueAsRef.mjs
/**
* Untracks the provided value by turning it into a ref to remove its reactivity.
*
* Used to access the passed value inside `React.useEffect` without causing the effect to re-run when the value changes.
*/
function useValueAsRef(value) {
	const latest = useRefWithInit(createLatestRef, value).current;
	latest.next = value;
	useIsoLayoutEffect(latest.effect);
	return latest;
}
function createLatestRef(value) {
	const latest = {
		current: value,
		next: value,
		effect: () => {
			latest.current = latest.next;
		}
	};
	return latest;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/visuallyHidden.mjs
var visuallyHiddenBase = {
	clipPath: "inset(50%)",
	overflow: "hidden",
	whiteSpace: "nowrap",
	border: 0,
	padding: 0,
	width: 1,
	height: 1,
	margin: -1
};
var visuallyHidden = {
	...visuallyHiddenBase,
	position: "fixed",
	top: 0,
	left: 0
};
var visuallyHiddenInput = {
	...visuallyHiddenBase,
	position: "absolute"
};
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/FocusGuard.mjs
/**
* @internal
*/
var FocusGuard = /* @__PURE__ */ React$3.forwardRef(function FocusGuard(props, ref) {
	const [role, setRole] = React$3.useState();
	useIsoLayoutEffect(() => {
		if (voiceOver && webkit) setRole("button");
	}, []);
	const restProps = {
		tabIndex: 0,
		role
	};
	return /* @__PURE__ */ jsx("span", {
		...props,
		ref,
		style: visuallyHidden,
		"aria-hidden": role ? void 0 : true,
		...restProps,
		"data-base-ui-focus-guard": ""
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/utils/createAttribute.mjs
function createAttribute(name) {
	return `data-base-ui-${name}`;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/utils/enqueueFocus.mjs
var rafId = 0;
function enqueueFocus(el, options = {}) {
	const { preventScroll = false, sync = false, shouldFocus } = options;
	cancelAnimationFrame(rafId);
	function exec() {
		if (shouldFocus && !shouldFocus()) return;
		el?.focus({ preventScroll });
	}
	if (sync) {
		exec();
		return NOOP;
	}
	const currentRafId = requestAnimationFrame(exec);
	rafId = currentRafId;
	return () => {
		if (rafId === currentRafId) {
			cancelAnimationFrame(currentRafId);
			rafId = 0;
		}
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/utils/markOthers.mjs
var counters = {
	inert: /* @__PURE__ */ new WeakMap(),
	"aria-hidden": /* @__PURE__ */ new WeakMap()
};
var markerName = "data-base-ui-inert";
var uncontrolledElementsSets = {
	inert: /* @__PURE__ */ new WeakSet(),
	"aria-hidden": /* @__PURE__ */ new WeakSet()
};
var markerCounterMap = /* @__PURE__ */ new WeakMap();
var lockCount = 0;
function getUncontrolledElementsSet(controlAttribute) {
	return uncontrolledElementsSets[controlAttribute];
}
function unwrapHost(node) {
	if (!node) return null;
	return isShadowRoot(node) ? node.host : unwrapHost(node.parentNode);
}
var correctElements = (parent, targets) => targets.map((target) => {
	if (parent.contains(target)) return target;
	const correctedTarget = unwrapHost(target);
	if (parent.contains(correctedTarget)) return correctedTarget;
	return null;
}).filter((x) => x != null);
var buildKeepSet = (targets) => {
	const keep = /* @__PURE__ */ new Set();
	targets.forEach((target) => {
		let node = target;
		while (node && !keep.has(node)) {
			keep.add(node);
			node = node.parentNode;
		}
	});
	return keep;
};
var collectOutsideElements = (root, keepElements, stopElements) => {
	const outside = [];
	const walk = (parent) => {
		if (!parent || stopElements.has(parent)) return;
		Array.from(parent.children).forEach((node) => {
			if (getNodeName(node) === "script") return;
			if (keepElements.has(node)) walk(node);
			else outside.push(node);
		});
	};
	walk(root);
	return outside;
};
function applyAttributeToOthers(uncorrectedAvoidElements, body, ariaHidden, inert, { mark = true }) {
	let controlAttribute = null;
	if (inert) controlAttribute = "inert";
	else if (ariaHidden) controlAttribute = "aria-hidden";
	let counterMap = null;
	let uncontrolledElementsSet = null;
	const avoidElements = correctElements(body, uncorrectedAvoidElements);
	const markerTargets = mark ? collectOutsideElements(body, buildKeepSet(avoidElements), new Set(avoidElements)) : [];
	const hiddenElements = [];
	const markedElements = [];
	if (controlAttribute) {
		const map = counters[controlAttribute];
		const currentUncontrolledElementsSet = getUncontrolledElementsSet(controlAttribute);
		uncontrolledElementsSet = currentUncontrolledElementsSet;
		counterMap = map;
		const ariaLiveElements = correctElements(body, Array.from(body.querySelectorAll("[aria-live]")));
		const controlElements = avoidElements.concat(ariaLiveElements);
		collectOutsideElements(body, buildKeepSet(controlElements), new Set(controlElements)).forEach((node) => {
			const attr = node.getAttribute(controlAttribute);
			const alreadyHidden = attr !== null && attr !== "false";
			const counterValue = (map.get(node) || 0) + 1;
			map.set(node, counterValue);
			hiddenElements.push(node);
			if (counterValue === 1 && alreadyHidden) currentUncontrolledElementsSet.add(node);
			if (!alreadyHidden) node.setAttribute(controlAttribute, controlAttribute === "inert" ? "" : "true");
		});
	}
	if (mark) markerTargets.forEach((node) => {
		const markerValue = (markerCounterMap.get(node) || 0) + 1;
		markerCounterMap.set(node, markerValue);
		markedElements.push(node);
		if (markerValue === 1) node.setAttribute(markerName, "");
	});
	lockCount += 1;
	return () => {
		if (counterMap) hiddenElements.forEach((element) => {
			const counterValue = (counterMap.get(element) || 0) - 1;
			counterMap.set(element, counterValue);
			if (!counterValue) {
				if (!uncontrolledElementsSet?.has(element) && controlAttribute) element.removeAttribute(controlAttribute);
				uncontrolledElementsSet?.delete(element);
			}
		});
		if (mark) markedElements.forEach((element) => {
			const markerValue = (markerCounterMap.get(element) || 0) - 1;
			markerCounterMap.set(element, markerValue);
			if (!markerValue) element.removeAttribute(markerName);
		});
		lockCount -= 1;
		if (!lockCount) {
			counters.inert = /* @__PURE__ */ new WeakMap();
			counters["aria-hidden"] = /* @__PURE__ */ new WeakMap();
			uncontrolledElementsSets.inert = /* @__PURE__ */ new WeakSet();
			uncontrolledElementsSets["aria-hidden"] = /* @__PURE__ */ new WeakSet();
			markerCounterMap = /* @__PURE__ */ new WeakMap();
		}
	};
}
function markOthers(avoidElements, options = {}) {
	const { ariaHidden = false, inert = false, mark = true } = options;
	const body = ownerDocument(avoidElements[0]).body;
	return applyAttributeToOthers(avoidElements, body, ariaHidden, inert, { mark });
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/constants.mjs
var DISABLED_TRANSITIONS_STYLE = { style: { transition: "none" } };
var BASE_UI_SWIPE_IGNORE_ATTRIBUTE = "data-base-ui-swipe-ignore";
var LEGACY_SWIPE_IGNORE_ATTRIBUTE = "data-swipe-ignore";
`${BASE_UI_SWIPE_IGNORE_ATTRIBUTE}`;
`${LEGACY_SWIPE_IGNORE_ATTRIBUTE}`;
/**
* Used for dropdowns that usually strictly prefer top/bottom placements and
* use `var(--available-height)` to limit their height.
*/
var DROPDOWN_COLLISION_AVOIDANCE = { fallbackAxisSide: "none" };
/**
* Used by regular popups that usually aren't scrollable and are allowed to
* freely flip to any axis of placement.
*/
var POPUP_COLLISION_AVOIDANCE = { fallbackAxisSide: "end" };
/**
* Special visually hidden styles for the aria-owns owner element to ensure owned element
* accessibility in iOS/Safari/VoiceControl.
* The owner element is an empty span, so most of the common visually hidden styles are not needed.
* @see https://github.com/floating-ui/floating-ui/issues/3403
*/
var ownerVisuallyHidden = {
	clipPath: "inset(50%)",
	position: "fixed",
	top: 0,
	left: 0
};
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/components/FloatingPortal.mjs
var PortalContext = /* @__PURE__ */ React$3.createContext(null);
var usePortalContext = () => React$3.useContext(PortalContext);
var attr = createAttribute("portal");
function useFloatingPortalNode(props = {}) {
	const { ref, container: containerProp, componentProps = EMPTY_OBJECT, elementProps } = props;
	const uniqueId = useId();
	const parentPortalNode = usePortalContext()?.portalNode;
	const [containerElement, setContainerElement] = React$3.useState(null);
	const [portalNode, setPortalNode] = React$3.useState(null);
	const setPortalNodeRef = useStableCallback((node) => {
		if (node !== null) setPortalNode(node);
	});
	const containerRef = React$3.useRef(null);
	useIsoLayoutEffect(() => {
		if (containerProp === null) {
			if (containerRef.current) {
				containerRef.current = null;
				setPortalNode(null);
				setContainerElement(null);
			}
			return;
		}
		const resolvedContainer = (containerProp && (isNode(containerProp) ? containerProp : containerProp.current)) ?? parentPortalNode ?? document.body;
		if (resolvedContainer == null) {
			if (containerRef.current) {
				containerRef.current = null;
				setPortalNode(null);
				setContainerElement(null);
			}
			return;
		}
		if (containerRef.current !== resolvedContainer) {
			containerRef.current = resolvedContainer;
			setPortalNode(null);
			setContainerElement(resolvedContainer);
		}
	}, [containerProp, parentPortalNode]);
	const portalElement = useRenderElement("div", componentProps, {
		ref: [ref, setPortalNodeRef],
		props: [{
			id: uniqueId,
			[attr]: ""
		}, elementProps]
	});
	const portalSubtree = containerElement && portalElement ? /* @__PURE__ */ ReactDOM.createPortal(portalElement, containerElement) : null;
	return {
		node: portalNode,
		nodeId: /* @__PURE__ */ React$3.isValidElement(portalElement) ? portalElement.props.id : void 0,
		subtree: portalSubtree
	};
}
/**
* Portals the floating element into a given container element — by default,
* outside of the app root and into the body.
* This is necessary to ensure the floating element can appear outside any
* potential parent containers that cause clipping (such as `overflow: hidden`),
* while retaining its location in the React tree.
* @see https://floating-ui.com/docs/FloatingPortal
* @internal
*/
var FloatingPortal = /* @__PURE__ */ React$3.forwardRef(function FloatingPortal(componentProps, forwardedRef) {
	const { render, className, style, children, container, ...elementProps } = componentProps;
	const { node: portalNode, nodeId: portalNodeId, subtree: portalSubtree } = useFloatingPortalNode({
		container,
		ref: forwardedRef,
		componentProps,
		elementProps
	});
	const beforeOutsideRef = React$3.useRef(null);
	const afterOutsideRef = React$3.useRef(null);
	const beforeInsideRef = React$3.useRef(null);
	const afterInsideRef = React$3.useRef(null);
	const [focusManagerState, setFocusManagerState] = React$3.useState(null);
	const focusInsideDisabledRef = React$3.useRef(false);
	const modal = focusManagerState?.modal;
	const open = focusManagerState?.open;
	const shouldRenderGuards = !!focusManagerState && !focusManagerState.modal && focusManagerState.open && !!portalNode;
	React$3.useEffect(() => {
		if (!portalNode || modal) return;
		function onFocus(event) {
			if (portalNode && event.relatedTarget && isOutsideEvent(event)) if (event.type === "focusin") {
				if (focusInsideDisabledRef.current) {
					enableFocusInside(portalNode);
					focusInsideDisabledRef.current = false;
				}
			} else {
				disableFocusInside(portalNode);
				focusInsideDisabledRef.current = true;
			}
		}
		return mergeCleanups(addEventListener(portalNode, "focusin", onFocus, true), addEventListener(portalNode, "focusout", onFocus, true));
	}, [portalNode, modal]);
	useIsoLayoutEffect(() => {
		if (!portalNode || open !== true || !focusInsideDisabledRef.current) return;
		enableFocusInside(portalNode);
		focusInsideDisabledRef.current = false;
	}, [open, portalNode]);
	const portalContextValue = React$3.useMemo(() => ({
		beforeOutsideRef,
		afterOutsideRef,
		beforeInsideRef,
		afterInsideRef,
		portalNode,
		setFocusManagerState
	}), [portalNode]);
	return /* @__PURE__ */ jsxs(React$3.Fragment, { children: [portalSubtree, /* @__PURE__ */ jsxs(PortalContext.Provider, {
		value: portalContextValue,
		children: [
			shouldRenderGuards && portalNode && /* @__PURE__ */ jsx(FocusGuard, {
				"data-type": "outside",
				ref: beforeOutsideRef,
				onFocus: (event) => {
					if (isOutsideEvent(event, portalNode)) beforeInsideRef.current?.focus();
					else getPreviousTabbable(focusManagerState ? focusManagerState.domReference : null)?.focus();
				}
			}),
			shouldRenderGuards && portalNode && /* @__PURE__ */ jsx("span", {
				"aria-owns": portalNodeId,
				style: ownerVisuallyHidden
			}),
			portalNode && /* @__PURE__ */ ReactDOM.createPortal(children, portalNode),
			shouldRenderGuards && portalNode && /* @__PURE__ */ jsx(FocusGuard, {
				"data-type": "outside",
				ref: afterOutsideRef,
				onFocus: (event) => {
					if (isOutsideEvent(event, portalNode)) afterInsideRef.current?.focus();
					else {
						getNextTabbable(focusManagerState ? focusManagerState.domReference : null)?.focus();
						if (focusManagerState?.closeOnFocusOut) focusManagerState?.onOpenChange(false, createChangeEventDetails("focus-out", event.nativeEvent));
					}
				}
			})
		]
	})] });
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/utils/createEventEmitter.mjs
function createEventEmitter() {
	const map = /* @__PURE__ */ new Map();
	return {
		emit(event, data) {
			map.get(event)?.forEach((listener) => listener(data));
		},
		on(event, listener) {
			if (!map.has(event)) map.set(event, /* @__PURE__ */ new Set());
			map.get(event).add(listener);
		},
		off(event, listener) {
			map.get(event)?.delete(listener);
		}
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/components/FloatingTree.mjs
var FloatingNodeContext = /* @__PURE__ */ React$3.createContext(null);
var FloatingTreeContext = /* @__PURE__ */ React$3.createContext(null);
var useFloatingParentNodeId = () => React$3.useContext(FloatingNodeContext)?.id || null;
/**
* Returns the nearest floating tree context, if available.
*/
var useFloatingTree = (externalTree) => {
	const contextTree = React$3.useContext(FloatingTreeContext);
	return externalTree ?? contextTree;
};
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/components/FloatingFocusManager.mjs
function getEventType(event, lastInteractionType) {
	const win = getWindow(getTarget(event));
	if (event instanceof win.KeyboardEvent) return "keyboard";
	if (event instanceof win.FocusEvent) return lastInteractionType || "keyboard";
	if ("pointerType" in event) return event.pointerType || "keyboard";
	if ("touches" in event) return "touch";
	if (event instanceof win.MouseEvent) return lastInteractionType || (event.detail === 0 ? "keyboard" : "mouse");
	return "";
}
var LIST_LIMIT = 20;
var previouslyFocusedElements = [];
function clearDisconnectedPreviouslyFocusedElements() {
	previouslyFocusedElements = previouslyFocusedElements.filter((entry) => {
		return entry.deref()?.isConnected;
	});
}
function addPreviouslyFocusedElement(element) {
	clearDisconnectedPreviouslyFocusedElements();
	if (element && getNodeName(element) !== "body") {
		previouslyFocusedElements.push(new WeakRef(element));
		if (previouslyFocusedElements.length > LIST_LIMIT) previouslyFocusedElements = previouslyFocusedElements.slice(-LIST_LIMIT);
	}
}
function getPreviouslyFocusedElement() {
	clearDisconnectedPreviouslyFocusedElements();
	return previouslyFocusedElements[previouslyFocusedElements.length - 1]?.deref();
}
function getFirstTabbableElement(container) {
	if (!container) return null;
	if (isTabbable(container)) return container;
	return tabbable(container)[0] || container;
}
function handleTabIndex(floatingFocusElement) {
	if (floatingFocusElement.hasAttribute("tabindex") && !floatingFocusElement.hasAttribute("data-tabindex")) return;
	if (!floatingFocusElement.getAttribute("role")?.includes("dialog")) return;
	const tabbableContent = focusable(floatingFocusElement).filter((element) => {
		const dataTabIndex = element.getAttribute("data-tabindex") || "";
		return isTabbable(element) || element.hasAttribute("data-tabindex") && !dataTabIndex.startsWith("-");
	});
	const tabIndex = floatingFocusElement.getAttribute("tabindex");
	if (tabbableContent.length === 0) {
		if (tabIndex !== "0") {
			floatingFocusElement.setAttribute("tabindex", "0");
			floatingFocusElement.setAttribute("data-tabindex", "0");
		}
	} else if (tabIndex !== "-1" || floatingFocusElement.hasAttribute("data-tabindex") && floatingFocusElement.getAttribute("data-tabindex") !== "-1") {
		floatingFocusElement.setAttribute("tabindex", "-1");
		floatingFocusElement.setAttribute("data-tabindex", "-1");
	}
}
/**
* Provides focus management for the floating element.
* @see https://floating-ui.com/docs/FloatingFocusManager
* @internal
*/
function FloatingFocusManager(props) {
	const { context, children, disabled = false, initialFocus = true, returnFocus = true, restoreFocus = false, modal = true, closeOnFocusOut = true, openInteractionType = "", nextFocusableElement, previousFocusableElement, beforeContentFocusGuardRef, externalTree, getInsideElements } = props;
	const store = "rootStore" in context ? context.rootStore : context;
	const open = store.useState("open");
	const domReference = store.useState("domReferenceElement");
	const floating = store.useState("floatingElement");
	const { events, dataRef } = store.context;
	const getNodeId = useStableCallback(() => dataRef.current.floatingContext?.nodeId);
	const ignoreInitialFocus = initialFocus === false;
	const isUntrappedTypeableCombobox = isTypeableCombobox(domReference) && ignoreInitialFocus;
	const initialFocusRef = useValueAsRef(initialFocus);
	const returnFocusRef = useValueAsRef(returnFocus);
	const openInteractionTypeRef = useValueAsRef(openInteractionType);
	const openRef = useValueAsRef(open);
	const tree = useFloatingTree(externalTree);
	const portalContext = usePortalContext();
	const preventReturnFocusRef = React$3.useRef(false);
	const isPointerDownRef = React$3.useRef(false);
	const pointerDownOutsideRef = React$3.useRef(false);
	const lastFocusedTabbableRef = React$3.useRef(null);
	const closeTypeRef = React$3.useRef("");
	const lastInteractionTypeRef = React$3.useRef("");
	const beforeGuardRef = React$3.useRef(null);
	const afterGuardRef = React$3.useRef(null);
	const mergedBeforeGuardRef = useMergedRefs(beforeGuardRef, beforeContentFocusGuardRef, portalContext?.beforeInsideRef);
	const mergedAfterGuardRef = useMergedRefs(afterGuardRef, portalContext?.afterInsideRef);
	const blurTimeout = useTimeout();
	const pointerDownTimeout = useTimeout();
	const restoreFocusFrame = useAnimationFrame();
	const isInsidePortal = portalContext != null;
	const floatingFocusElement = getFloatingFocusElement(floating);
	const getTabbableContent = useStableCallback((container = floatingFocusElement) => {
		return container ? tabbable(container) : [];
	});
	const getResolvedInsideElements = useStableCallback(() => getInsideElements?.().filter((element) => element != null) ?? []);
	React$3.useEffect(() => {
		if (disabled || !modal) return;
		function onKeyDown(event) {
			if (event.key === "Tab") {
				if (contains(floatingFocusElement, activeElement(ownerDocument(floatingFocusElement))) && getTabbableContent().length === 0 && !isUntrappedTypeableCombobox) stopEvent(event);
			}
		}
		return addEventListener(ownerDocument(floatingFocusElement), "keydown", onKeyDown);
	}, [
		disabled,
		floatingFocusElement,
		modal,
		isUntrappedTypeableCombobox,
		getTabbableContent
	]);
	React$3.useEffect(() => {
		if (disabled || !open) return;
		const doc = ownerDocument(floatingFocusElement);
		function clearPointerDownOutside() {
			pointerDownOutsideRef.current = false;
		}
		function onPointerDown(event) {
			const target = getTarget(event);
			const insideElements = getResolvedInsideElements();
			pointerDownOutsideRef.current = !(contains(floating, target) || contains(domReference, target) || contains(portalContext?.portalNode, target) || insideElements.some((element) => element === target || contains(element, target)));
			lastInteractionTypeRef.current = event.pointerType || "keyboard";
			if (target?.closest(`[data-base-ui-click-trigger]`)) {
				isPointerDownRef.current = true;
				pointerDownTimeout.start(0, () => {
					isPointerDownRef.current = false;
				});
			}
		}
		function onKeyDown() {
			lastInteractionTypeRef.current = "keyboard";
		}
		return mergeCleanups(addEventListener(doc, "pointerdown", onPointerDown, true), addEventListener(doc, "pointerup", clearPointerDownOutside, true), addEventListener(doc, "pointercancel", clearPointerDownOutside, true), addEventListener(doc, "keydown", onKeyDown, true), clearPointerDownOutside);
	}, [
		disabled,
		floating,
		domReference,
		floatingFocusElement,
		open,
		portalContext,
		pointerDownTimeout,
		getResolvedInsideElements
	]);
	React$3.useEffect(() => {
		if (disabled || !closeOnFocusOut) return;
		const doc = ownerDocument(floatingFocusElement);
		function handlePointerDown() {
			isPointerDownRef.current = true;
			pointerDownTimeout.start(0, () => {
				isPointerDownRef.current = false;
			});
		}
		function handleFocusIn(event) {
			const target = getTarget(event);
			if (isTabbable(target)) lastFocusedTabbableRef.current = target;
		}
		function handleFocusOutside(event) {
			const relatedTarget = event.relatedTarget;
			const currentTarget = event.currentTarget;
			const target = getTarget(event);
			if (modal && relatedTarget == null && target != null && contains(floating, target)) addPreviouslyFocusedElement(target);
			queueMicrotask(() => {
				const nodeId = getNodeId();
				const triggers = store.context.triggerElements;
				const insideElements = getResolvedInsideElements();
				const isRelatedFocusGuard = relatedTarget?.hasAttribute(createAttribute("focus-guard")) && [
					beforeGuardRef.current,
					afterGuardRef.current,
					portalContext?.beforeInsideRef.current,
					portalContext?.afterInsideRef.current,
					portalContext?.beforeOutsideRef.current,
					portalContext?.afterOutsideRef.current,
					resolveRef(previousFocusableElement),
					resolveRef(nextFocusableElement)
				].includes(relatedTarget);
				const movedToUnrelatedNode = !(contains(domReference, relatedTarget) || contains(floating, relatedTarget) || contains(relatedTarget, floating) || contains(portalContext?.portalNode, relatedTarget) || insideElements.some((element) => element === relatedTarget || contains(element, relatedTarget)) || triggers.hasMatchingElement((trigger) => contains(trigger, relatedTarget)) || isRelatedFocusGuard || tree && (getNodeChildren(tree.nodesRef.current, nodeId).find((node) => contains(node.context?.elements.floating, relatedTarget) || contains(node.context?.elements.domReference, relatedTarget)) || getNodeAncestors(tree.nodesRef.current, nodeId).find((node) => [node.context?.elements.floating, getFloatingFocusElement(node.context?.elements.floating)].includes(relatedTarget) || node.context?.elements.domReference === relatedTarget)));
				if (currentTarget === domReference && floatingFocusElement) handleTabIndex(floatingFocusElement);
				if (restoreFocus && currentTarget !== domReference && !isElementVisible(target) && activeElement(doc) === doc.body) {
					if (isHTMLElement(floatingFocusElement)) {
						floatingFocusElement.focus();
						if (restoreFocus === "popup") {
							restoreFocusFrame.request(() => {
								floatingFocusElement.focus();
							});
							return;
						}
					}
					const tabbableContent = getTabbableContent();
					const prevTabbable = lastFocusedTabbableRef.current;
					const nodeToFocus = (prevTabbable && tabbableContent.includes(prevTabbable) ? prevTabbable : null) || tabbableContent[tabbableContent.length - 1] || floatingFocusElement;
					if (isHTMLElement(nodeToFocus)) nodeToFocus.focus();
				}
				if (dataRef.current.insideReactTree) {
					dataRef.current.insideReactTree = false;
					return;
				}
				if ((isUntrappedTypeableCombobox ? true : !modal) && relatedTarget && movedToUnrelatedNode && !isPointerDownRef.current && (isUntrappedTypeableCombobox || relatedTarget !== getPreviouslyFocusedElement())) {
					preventReturnFocusRef.current = true;
					store.setOpen(false, createChangeEventDetails(focusOut, event));
				}
			});
		}
		function markInsideReactTree() {
			if (pointerDownOutsideRef.current) return;
			dataRef.current.insideReactTree = true;
			blurTimeout.start(0, () => {
				dataRef.current.insideReactTree = false;
			});
		}
		const domReferenceElement = isHTMLElement(domReference) ? domReference : null;
		if (!floating && !domReferenceElement) return;
		return mergeCleanups(domReferenceElement && addEventListener(domReferenceElement, "focusout", handleFocusOutside), domReferenceElement && addEventListener(domReferenceElement, "pointerdown", handlePointerDown), floating && addEventListener(floating, "focusin", handleFocusIn), floating && addEventListener(floating, "focusout", handleFocusOutside), floating && portalContext && addEventListener(floating, "focusout", markInsideReactTree, true));
	}, [
		disabled,
		domReference,
		floating,
		floatingFocusElement,
		modal,
		tree,
		portalContext,
		store,
		closeOnFocusOut,
		restoreFocus,
		getTabbableContent,
		isUntrappedTypeableCombobox,
		getNodeId,
		dataRef,
		blurTimeout,
		pointerDownTimeout,
		restoreFocusFrame,
		nextFocusableElement,
		previousFocusableElement,
		getResolvedInsideElements
	]);
	React$3.useEffect(() => {
		if (disabled || !floating || !open) return;
		const portalNodes = Array.from(portalContext?.portalNode?.querySelectorAll(`[${createAttribute("portal")}]`) || []);
		const rootAncestorComboboxDomReference = (tree ? getNodeAncestors(tree.nodesRef.current, getNodeId()) : []).find((node) => isTypeableCombobox(node.context?.elements.domReference || null))?.context?.elements.domReference;
		const ariaHiddenCleanup = markOthers([
			...[
				floating,
				...portalNodes,
				beforeGuardRef.current,
				afterGuardRef.current,
				portalContext?.beforeOutsideRef.current,
				portalContext?.afterOutsideRef.current,
				...getResolvedInsideElements()
			],
			rootAncestorComboboxDomReference,
			resolveRef(previousFocusableElement),
			resolveRef(nextFocusableElement),
			isUntrappedTypeableCombobox ? domReference : null
		].filter((x) => x != null), {
			ariaHidden: modal || isUntrappedTypeableCombobox,
			mark: false
		});
		const markerCleanup = markOthers([floating, ...portalNodes].filter((x) => x != null));
		return () => {
			markerCleanup();
			ariaHiddenCleanup();
		};
	}, [
		open,
		disabled,
		domReference,
		floating,
		modal,
		portalContext,
		isUntrappedTypeableCombobox,
		tree,
		getNodeId,
		nextFocusableElement,
		previousFocusableElement,
		getResolvedInsideElements
	]);
	useIsoLayoutEffect(() => {
		if (!open || disabled || !isHTMLElement(floatingFocusElement)) return;
		closeTypeRef.current = "";
		lastInteractionTypeRef.current = "";
		const doc = ownerDocument(floatingFocusElement);
		const previouslyFocusedElement = activeElement(doc);
		queueMicrotask(() => {
			const initialFocusValueOrFn = initialFocusRef.current;
			const resolvedInitialFocus = typeof initialFocusValueOrFn === "function" ? initialFocusValueOrFn(openInteractionTypeRef.current || "") : initialFocusValueOrFn;
			if (resolvedInitialFocus === void 0 || resolvedInitialFocus === false) return;
			if (contains(floatingFocusElement, previouslyFocusedElement)) return;
			let focusableElements = null;
			const getDefaultFocusElement = () => {
				if (focusableElements == null) focusableElements = getTabbableContent(floatingFocusElement);
				return focusableElements[0] || floatingFocusElement;
			};
			let elToFocus;
			if (resolvedInitialFocus === true || resolvedInitialFocus === null) elToFocus = getDefaultFocusElement();
			else elToFocus = resolveRef(resolvedInitialFocus);
			elToFocus = elToFocus || getDefaultFocusElement();
			const hadFocusInside = contains(floatingFocusElement, activeElement(doc));
			enqueueFocus(elToFocus, {
				preventScroll: elToFocus === floatingFocusElement,
				shouldFocus() {
					if (!openRef.current) return false;
					if (hadFocusInside) return true;
					const currentActiveElement = activeElement(doc);
					return !(currentActiveElement !== elToFocus && contains(floatingFocusElement, currentActiveElement));
				}
			});
		});
	}, [
		disabled,
		open,
		floatingFocusElement,
		getTabbableContent,
		initialFocusRef,
		openInteractionTypeRef,
		openRef
	]);
	useIsoLayoutEffect(() => {
		if (disabled || !floatingFocusElement) return;
		const doc = ownerDocument(floatingFocusElement);
		const elementFocusedBeforeOpen = activeElement(doc);
		const preferPreviousFocus = openInteractionTypeRef.current == null;
		addPreviouslyFocusedElement(elementFocusedBeforeOpen);
		function onOpenChangeLocal(details) {
			if (!details.open) closeTypeRef.current = getEventType(details.nativeEvent, lastInteractionTypeRef.current);
			if (details.reason === "trigger-hover" && details.nativeEvent.type === "mouseleave") preventReturnFocusRef.current = true;
			if (details.reason !== "outside-press") return;
			if (details.nested) preventReturnFocusRef.current = false;
			else if (isVirtualClick(details.nativeEvent) || isVirtualPointerEvent(details.nativeEvent)) preventReturnFocusRef.current = false;
			else {
				let isPreventScrollSupported = false;
				ownerDocument(floatingFocusElement).createElement("div").focus({ get preventScroll() {
					isPreventScrollSupported = true;
					return false;
				} });
				if (isPreventScrollSupported) preventReturnFocusRef.current = false;
				else preventReturnFocusRef.current = true;
			}
		}
		events.on("openchange", onOpenChangeLocal);
		function getReturnElement(closeType) {
			const returnFocusValueOrFn = returnFocusRef.current;
			let resolvedReturnFocusValue = typeof returnFocusValueOrFn === "function" ? returnFocusValueOrFn(closeType) : returnFocusValueOrFn;
			if (resolvedReturnFocusValue === void 0 || resolvedReturnFocusValue === false) return null;
			if (resolvedReturnFocusValue === null) resolvedReturnFocusValue = true;
			const referenceReturnElement = domReference?.isConnected ? domReference : null;
			const previousReturnElement = elementFocusedBeforeOpen?.isConnected && getNodeName(elementFocusedBeforeOpen) !== "body" ? elementFocusedBeforeOpen : null;
			let defaultReturnElement = preferPreviousFocus ? previousReturnElement || referenceReturnElement : referenceReturnElement || previousReturnElement;
			if (!defaultReturnElement) defaultReturnElement = getPreviouslyFocusedElement() || null;
			if (typeof resolvedReturnFocusValue === "boolean") return defaultReturnElement;
			return resolveRef(resolvedReturnFocusValue) || defaultReturnElement || null;
		}
		return () => {
			events.off("openchange", onOpenChangeLocal);
			const activeEl = activeElement(doc);
			const insideElements = getResolvedInsideElements();
			const isFocusInsideFloatingTree = contains(floating, activeEl) || insideElements.some((element) => element === activeEl || contains(element, activeEl)) || tree && getNodeChildren(tree.nodesRef.current, getNodeId(), false).some((node) => contains(node.context?.elements.floating, activeEl));
			const returnFocusValueOrFn = returnFocusRef.current;
			const closeType = closeTypeRef.current;
			const returnElement = getReturnElement(closeType);
			queueMicrotask(() => {
				const tabbableReturnElement = getFirstTabbableElement(returnElement);
				const hasExplicitReturnFocus = typeof returnFocusValueOrFn !== "boolean";
				if (returnFocusValueOrFn && !preventReturnFocusRef.current && isHTMLElement(tabbableReturnElement) && (!hasExplicitReturnFocus && tabbableReturnElement !== activeEl && activeEl !== doc.body ? isFocusInsideFloatingTree : true)) {
					const focusOptions = { preventScroll: true };
					if (closeType === "keyboard") focusOptions.focusVisible = true;
					tabbableReturnElement.focus(focusOptions);
				}
				preventReturnFocusRef.current = false;
			});
		};
	}, [
		disabled,
		floating,
		floatingFocusElement,
		returnFocusRef,
		openInteractionTypeRef,
		events,
		tree,
		domReference,
		getNodeId,
		getResolvedInsideElements
	]);
	useIsoLayoutEffect(() => {
		if (!webkit || open || !floating) return;
		const activeEl = activeElement(ownerDocument(floating));
		if (!isHTMLElement(activeEl) || !isTypeableElement(activeEl)) return;
		if (contains(floating, activeEl)) activeEl.blur();
	}, [open, floating]);
	useIsoLayoutEffect(() => {
		if (disabled || !portalContext) return;
		portalContext.setFocusManagerState({
			modal,
			closeOnFocusOut,
			open,
			onOpenChange: store.setOpen,
			domReference
		});
		return () => {
			portalContext.setFocusManagerState(null);
		};
	}, [
		disabled,
		portalContext,
		modal,
		open,
		store,
		closeOnFocusOut,
		domReference
	]);
	useIsoLayoutEffect(() => {
		if (disabled || !floatingFocusElement) return;
		handleTabIndex(floatingFocusElement);
		return () => {
			queueMicrotask(clearDisconnectedPreviouslyFocusedElements);
		};
	}, [disabled, floatingFocusElement]);
	const shouldRenderGuards = !disabled && (modal ? !isUntrappedTypeableCombobox : true) && (isInsidePortal || modal);
	return /* @__PURE__ */ jsxs(React$3.Fragment, { children: [
		shouldRenderGuards && /* @__PURE__ */ jsx(FocusGuard, {
			"data-type": "inside",
			ref: mergedBeforeGuardRef,
			onFocus: (event) => {
				if (modal) {
					const els = getTabbableContent();
					enqueueFocus(els[els.length - 1]);
				} else if (portalContext?.portalNode) {
					preventReturnFocusRef.current = false;
					if (isOutsideEvent(event, portalContext.portalNode)) getNextTabbable(domReference)?.focus();
					else resolveRef(previousFocusableElement ?? portalContext.beforeOutsideRef)?.focus();
				}
			}
		}),
		children,
		shouldRenderGuards && /* @__PURE__ */ jsx(FocusGuard, {
			"data-type": "inside",
			ref: mergedAfterGuardRef,
			onFocus: (event) => {
				if (modal) enqueueFocus(getTabbableContent()[0]);
				else if (portalContext?.portalNode) {
					if (closeOnFocusOut) preventReturnFocusRef.current = true;
					if (isOutsideEvent(event, portalContext.portalNode)) getPreviousTabbable(domReference)?.focus();
					else resolveRef(nextFocusableElement ?? portalContext.afterOutsideRef)?.focus();
				}
			}
		})
	] });
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/hooks/useClick.mjs
/**
* Opens or closes the floating element when clicking the reference element.
* @see https://floating-ui.com/docs/useClick
*/
function useClick(context, props = {}) {
	const { enabled = true, event: eventOption = "click", toggle = true, ignoreMouse = false, stickIfOpen = true, touchOpenDelay = 0, reason = triggerPress } = props;
	const store = "rootStore" in context ? context.rootStore : context;
	const dataRef = store.context.dataRef;
	const pointerTypeRef = React$3.useRef(void 0);
	const frame = useAnimationFrame();
	const touchOpenTimeout = useTimeout();
	const reference = React$3.useMemo(() => {
		function setOpenWithTouchDelay(nextOpen, nativeEvent, target, pointerType) {
			const details = createChangeEventDetails(reason, nativeEvent, target);
			if (nextOpen && pointerType === "touch" && touchOpenDelay > 0) touchOpenTimeout.start(touchOpenDelay, () => {
				store.setOpen(true, details);
			});
			else store.setOpen(nextOpen, details);
		}
		function getNextOpen(open, currentTarget, isClickLikeOpenEvent) {
			const openEvent = dataRef.current.openEvent;
			const hasClickedOnInactiveTrigger = store.select("domReferenceElement") !== currentTarget;
			if (open && hasClickedOnInactiveTrigger) return true;
			if (!open) return true;
			if (!toggle) return true;
			if (openEvent && stickIfOpen) return !isClickLikeOpenEvent(openEvent.type);
			return false;
		}
		return {
			onPointerDown(event) {
				pointerTypeRef.current = isMouseLikePointerType(event.pointerType, true) && isVirtualPointerEvent(event.nativeEvent) ? "virtual" : event.pointerType;
			},
			onMouseDown(event) {
				const pointerType = pointerTypeRef.current;
				const nativeEvent = event.nativeEvent;
				const open = store.select("open");
				if (event.button !== 0 || eventOption === "click" || isMouseLikePointerType(pointerType, true) && ignoreMouse) return;
				const nextOpen = getNextOpen(open, event.currentTarget, (openEventType) => openEventType === "click" || openEventType === "mousedown");
				const target = getTarget(nativeEvent);
				if (isTypeableElement(target)) {
					setOpenWithTouchDelay(nextOpen, nativeEvent, target, pointerType);
					return;
				}
				const eventCurrentTarget = event.currentTarget;
				frame.request(() => {
					setOpenWithTouchDelay(nextOpen, nativeEvent, eventCurrentTarget, pointerType);
				});
			},
			onClick(event) {
				if (eventOption === "mousedown-only") return;
				const pointerType = pointerTypeRef.current;
				if (eventOption === "mousedown" && pointerType) {
					pointerTypeRef.current = void 0;
					return;
				}
				if (isMouseLikePointerType(pointerType, true) && ignoreMouse) return;
				setOpenWithTouchDelay(getNextOpen(store.select("open"), event.currentTarget, (openEventType) => openEventType === "click" || openEventType === "mousedown" || openEventType === "keydown" || openEventType === "keyup"), event.nativeEvent, event.currentTarget, pointerType);
			},
			onKeyDown() {
				pointerTypeRef.current = void 0;
			}
		};
	}, [
		dataRef,
		eventOption,
		ignoreMouse,
		reason,
		store,
		stickIfOpen,
		toggle,
		frame,
		touchOpenTimeout,
		touchOpenDelay
	]);
	return React$3.useMemo(() => enabled ? { reference } : EMPTY_OBJECT, [enabled, reference]);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/hooks/useClientPoint.mjs
function createVirtualElement(domElement, data) {
	let offsetX = null;
	let offsetY = null;
	let isAutoUpdateEvent = false;
	return {
		contextElement: domElement || void 0,
		getBoundingClientRect() {
			const domRect = domElement?.getBoundingClientRect() || {
				width: 0,
				height: 0,
				x: 0,
				y: 0
			};
			const isXAxis = data.axis === "x" || data.axis === "both";
			const isYAxis = data.axis === "y" || data.axis === "both";
			const canTrackCursorOnAutoUpdate = ["mouseenter", "mousemove"].includes(data.dataRef.current.openEvent?.type || "") && data.pointerType !== "touch";
			let width = domRect.width;
			let height = domRect.height;
			let x = domRect.x;
			let y = domRect.y;
			if (offsetX == null && data.x && isXAxis) offsetX = domRect.x - data.x;
			if (offsetY == null && data.y && isYAxis) offsetY = domRect.y - data.y;
			x -= offsetX || 0;
			y -= offsetY || 0;
			width = 0;
			height = 0;
			if (!isAutoUpdateEvent || canTrackCursorOnAutoUpdate) {
				width = data.axis === "y" ? domRect.width : 0;
				height = data.axis === "x" ? domRect.height : 0;
				x = isXAxis && data.x != null ? data.x : x;
				y = isYAxis && data.y != null ? data.y : y;
			} else if (isAutoUpdateEvent && !canTrackCursorOnAutoUpdate) {
				height = data.axis === "x" ? domRect.height : height;
				width = data.axis === "y" ? domRect.width : width;
			}
			isAutoUpdateEvent = true;
			return {
				width,
				height,
				x,
				y,
				top: y,
				right: x + width,
				bottom: y + height,
				left: x
			};
		}
	};
}
function isMouseBasedEvent(event) {
	return event != null && event.clientX != null;
}
/**
* Positions the floating element relative to a client point (in the viewport),
* such as the mouse position. By default, it follows the mouse cursor.
* @see https://floating-ui.com/docs/useClientPoint
*/
function useClientPoint(context, props = {}) {
	const { enabled = true, axis = "both" } = props;
	const store = "rootStore" in context ? context.rootStore : context;
	const open = store.useState("open");
	const floating = store.useState("floatingElement");
	const domReference = store.useState("domReferenceElement");
	const dataRef = store.context.dataRef;
	const initialRef = React$3.useRef(false);
	const cleanupListenerRef = React$3.useRef(null);
	const [pointerType, setPointerType] = React$3.useState();
	const [reactive, setReactive] = React$3.useState([]);
	const resetReference = useStableCallback((reference) => {
		store.set("positionReference", reference);
	});
	const setReference = useStableCallback((newX, newY, referenceElement) => {
		if (initialRef.current) return;
		if (dataRef.current.openEvent && !isMouseBasedEvent(dataRef.current.openEvent)) return;
		store.set("positionReference", createVirtualElement(referenceElement ?? domReference, {
			x: newX,
			y: newY,
			axis,
			dataRef,
			pointerType
		}));
	});
	const handleReferenceEnterOrMove = useStableCallback((event) => {
		if (!open) setReference(event.clientX, event.clientY, event.currentTarget);
		else if (!cleanupListenerRef.current) {
			setReference(event.clientX, event.clientY, event.currentTarget);
			setReactive([]);
		}
	});
	const openCheck = isMouseLikePointerType(pointerType) ? floating : open;
	React$3.useEffect(() => {
		if (!enabled) {
			resetReference(domReference);
			return;
		}
		if (!openCheck) return;
		function cleanupListener() {
			cleanupListenerRef.current?.();
			cleanupListenerRef.current = null;
		}
		const win = getWindow(floating);
		function handleMouseMove(event) {
			if (!contains(floating, getTarget(event))) setReference(event.clientX, event.clientY);
			else cleanupListener();
		}
		if (!dataRef.current.openEvent || isMouseBasedEvent(dataRef.current.openEvent)) cleanupListenerRef.current = addEventListener(win, "mousemove", handleMouseMove);
		else resetReference(domReference);
		return cleanupListener;
	}, [
		openCheck,
		enabled,
		floating,
		dataRef,
		domReference,
		store,
		setReference,
		resetReference,
		reactive
	]);
	React$3.useEffect(() => () => {
		store.set("positionReference", null);
	}, [store]);
	React$3.useEffect(() => {
		if (enabled && !floating) initialRef.current = false;
	}, [enabled, floating]);
	React$3.useEffect(() => {
		if (!enabled && open) initialRef.current = true;
	}, [enabled, open]);
	const reference = React$3.useMemo(() => {
		function setPointerTypeRef(event) {
			setPointerType(event.pointerType);
		}
		return {
			onPointerDown: setPointerTypeRef,
			onPointerEnter: setPointerTypeRef,
			onMouseMove: handleReferenceEnterOrMove,
			onMouseEnter: handleReferenceEnterOrMove
		};
	}, [handleReferenceEnterOrMove]);
	return React$3.useMemo(() => enabled ? {
		reference,
		trigger: reference
	} : {}, [enabled, reference]);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/hooks/useDismiss.mjs
function alwaysFalse() {
	return false;
}
function normalizeProp(normalizable) {
	return {
		escapeKey: typeof normalizable === "boolean" ? normalizable : normalizable?.escapeKey ?? false,
		outsidePress: typeof normalizable === "boolean" ? normalizable : normalizable?.outsidePress ?? true
	};
}
/**
* Closes the floating element when a dismissal is requested — by default, when
* the user presses the `escape` key or outside of the floating element.
* @see https://floating-ui.com/docs/useDismiss
*/
function useDismiss(context, props = {}) {
	const { enabled = true, escapeKey: escapeKey$1 = true, outsidePress: outsidePressProp = true, outsidePressEvent = "sloppy", referencePress = alwaysFalse, bubbles, externalTree } = props;
	const store = "rootStore" in context ? context.rootStore : context;
	const open = store.useState("open");
	const floatingElement = store.useState("floatingElement");
	const { dataRef } = store.context;
	const tree = useFloatingTree(externalTree);
	const outsidePressFn = useStableCallback(typeof outsidePressProp === "function" ? outsidePressProp : () => false);
	const outsidePress$1 = typeof outsidePressProp === "function" ? outsidePressFn : outsidePressProp;
	const outsidePressEnabled = outsidePress$1 !== false;
	const getOutsidePressEventProp = useStableCallback(() => outsidePressEvent);
	const { escapeKey: escapeKeyBubbles, outsidePress: outsidePressBubbles } = normalizeProp(bubbles);
	const pressStartedInsideRef = React$3.useRef(false);
	const pressStartPreventedRef = React$3.useRef(false);
	const suppressNextOutsideClickRef = React$3.useRef(false);
	const isComposingRef = React$3.useRef(false);
	const currentPointerTypeRef = React$3.useRef("");
	const touchStateRef = React$3.useRef(null);
	const cancelDismissOnEndTimeout = useTimeout();
	const clearInsideReactTreeTimeout = useTimeout();
	const clearInsideReactTree = useStableCallback(() => {
		clearInsideReactTreeTimeout.clear();
		dataRef.current.insideReactTree = false;
	});
	const hasBlockingChild = useStableCallback((bubbleKey) => {
		const nodeId = dataRef.current.floatingContext?.nodeId;
		return (tree ? getNodeChildren(tree.nodesRef.current, nodeId) : []).some((child) => child.context?.open && !child.context.dataRef.current[bubbleKey]);
	});
	const isEventWithinOwnElements = useStableCallback((event) => {
		return isEventTargetWithin(event, store.select("floatingElement")) || isEventTargetWithin(event, store.select("domReferenceElement"));
	});
	const closeOnReferencePress = useStableCallback((event) => {
		if (!referencePress()) return;
		store.setOpen(false, createChangeEventDetails(triggerPress, event.nativeEvent));
	});
	const closeOnEscapeKeyDown = useStableCallback((event) => {
		if (!open || !enabled || !escapeKey$1 || event.key !== "Escape") return;
		if (isComposingRef.current) return;
		if (!escapeKeyBubbles && hasBlockingChild("__escapeKeyBubbles")) return;
		const eventDetails = createChangeEventDetails(escapeKey, isReactEvent(event) ? event.nativeEvent : event);
		store.setOpen(false, eventDetails);
		if (!eventDetails.isCanceled) event.preventDefault();
		if (!escapeKeyBubbles && !eventDetails.isPropagationAllowed) event.stopPropagation();
	});
	const markInsideReactTree = useStableCallback(() => {
		dataRef.current.insideReactTree = true;
		clearInsideReactTreeTimeout.start(0, clearInsideReactTree);
	});
	const markPressStartedInsideReactTree = useStableCallback((event) => {
		if (!open || !enabled || event.button !== 0) return;
		const target = getTarget(event.nativeEvent);
		if (!contains(store.select("floatingElement"), target)) return;
		if (!pressStartedInsideRef.current) {
			pressStartedInsideRef.current = true;
			pressStartPreventedRef.current = false;
		}
	});
	const markInsidePressStartPrevented = useStableCallback((event) => {
		if (!open || !enabled) return;
		if (!(event.defaultPrevented || event.nativeEvent.defaultPrevented)) return;
		if (pressStartedInsideRef.current) pressStartPreventedRef.current = true;
	});
	React$3.useEffect(() => {
		if (!open || !enabled) return clearInsideReactTree;
		dataRef.current.__escapeKeyBubbles = escapeKeyBubbles;
		dataRef.current.__outsidePressBubbles = outsidePressBubbles;
		const compositionTimeout = new Timeout();
		const preventedPressSuppressionTimeout = new Timeout();
		function handleCompositionStart() {
			compositionTimeout.clear();
			isComposingRef.current = true;
		}
		function handleCompositionEnd() {
			compositionTimeout.start(webkit ? 5 : 0, () => {
				isComposingRef.current = false;
			});
		}
		function suppressImmediateOutsideClickAfterPreventedStart() {
			suppressNextOutsideClickRef.current = true;
			preventedPressSuppressionTimeout.start(0, () => {
				suppressNextOutsideClickRef.current = false;
			});
		}
		function resetPressStartState() {
			pressStartedInsideRef.current = false;
			pressStartPreventedRef.current = false;
		}
		function getOutsidePressEvent() {
			const type = currentPointerTypeRef.current;
			const computedType = type === "pen" || !type ? "mouse" : type;
			const outsidePressEventValue = getOutsidePressEventProp();
			const resolved = typeof outsidePressEventValue === "function" ? outsidePressEventValue() : outsidePressEventValue;
			if (typeof resolved === "string") return resolved;
			return resolved[computedType];
		}
		function shouldIgnoreEvent(event) {
			const computedOutsidePressEvent = getOutsidePressEvent();
			return computedOutsidePressEvent === "intentional" && event.type !== "click" || computedOutsidePressEvent === "sloppy" && event.type === "click";
		}
		function isEventWithinFloatingTree(event) {
			const nodeId = dataRef.current.floatingContext?.nodeId;
			const targetIsInsideChildren = tree && getNodeChildren(tree.nodesRef.current, nodeId).some((node) => isEventTargetWithin(event, node.context?.elements.floating));
			return isEventWithinOwnElements(event) || targetIsInsideChildren;
		}
		function closeOnPressOutside(event) {
			if (shouldIgnoreEvent(event)) {
				if (event.type !== "click" && !isEventWithinOwnElements(event)) {
					preventedPressSuppressionTimeout.clear();
					suppressNextOutsideClickRef.current = false;
				}
				clearInsideReactTree();
				return;
			}
			if (dataRef.current.insideReactTree) {
				clearInsideReactTree();
				return;
			}
			const target = getTarget(event);
			const inertSelector = `[${createAttribute("inert")}]`;
			const targetRoot = isElement(target) ? target.getRootNode() : null;
			const markers = Array.from((isShadowRoot(targetRoot) ? targetRoot : ownerDocument(store.select("floatingElement"))).querySelectorAll(inertSelector));
			const triggers = store.context.triggerElements;
			if (target && (triggers.hasElement(target) || triggers.hasMatchingElement((trigger) => contains(trigger, target)))) return;
			let targetRootAncestor = isElement(target) ? target : null;
			while (targetRootAncestor && !isLastTraversableNode(targetRootAncestor)) {
				const nextParent = getParentNode(targetRootAncestor);
				if (isLastTraversableNode(nextParent) || !isElement(nextParent)) break;
				targetRootAncestor = nextParent;
			}
			if (markers.length && isElement(target) && !isRootElement(target) && !contains(target, store.select("floatingElement")) && markers.every((marker) => !contains(targetRootAncestor, marker))) return;
			if (isHTMLElement(target) && !("touches" in event)) {
				const lastTraversableNode = isLastTraversableNode(target);
				const style = getComputedStyle$1(target);
				const scrollRe = /auto|scroll/;
				const isScrollableX = lastTraversableNode || scrollRe.test(style.overflowX);
				const isScrollableY = lastTraversableNode || scrollRe.test(style.overflowY);
				const canScrollX = isScrollableX && target.clientWidth > 0 && target.scrollWidth > target.clientWidth;
				const canScrollY = isScrollableY && target.clientHeight > 0 && target.scrollHeight > target.clientHeight;
				const isRTL = style.direction === "rtl";
				const pressedVerticalScrollbar = canScrollY && (isRTL ? event.offsetX <= target.offsetWidth - target.clientWidth : event.offsetX > target.clientWidth);
				const pressedHorizontalScrollbar = canScrollX && event.offsetY > target.clientHeight;
				if (pressedVerticalScrollbar || pressedHorizontalScrollbar) return;
			}
			if (isEventWithinFloatingTree(event)) return;
			if (getOutsidePressEvent() === "intentional" && suppressNextOutsideClickRef.current) {
				preventedPressSuppressionTimeout.clear();
				suppressNextOutsideClickRef.current = false;
				return;
			}
			if (typeof outsidePress$1 === "function" && !outsidePress$1(event)) return;
			if (hasBlockingChild("__outsidePressBubbles")) return;
			store.setOpen(false, createChangeEventDetails(outsidePress, event));
			clearInsideReactTree();
		}
		function handlePointerDown(event) {
			if (getOutsidePressEvent() !== "sloppy" || event.pointerType === "touch" || !store.select("open") || !enabled || isEventWithinOwnElements(event)) return;
			closeOnPressOutside(event);
		}
		function handleTouchStart(event) {
			if (getOutsidePressEvent() !== "sloppy" || !store.select("open") || !enabled || isEventWithinOwnElements(event)) return;
			const touch = event.touches[0];
			if (touch) {
				touchStateRef.current = {
					startTime: Date.now(),
					startX: touch.clientX,
					startY: touch.clientY,
					dismissOnTouchEnd: false,
					dismissOnMouseDown: true
				};
				cancelDismissOnEndTimeout.start(1e3, () => {
					if (touchStateRef.current) {
						touchStateRef.current.dismissOnTouchEnd = false;
						touchStateRef.current.dismissOnMouseDown = false;
					}
				});
			}
		}
		function addTargetEventListenerOnce(event, listener) {
			const target = getTarget(event);
			if (!target) return;
			const unsubscribe = addEventListener(target, event.type, () => {
				listener(event);
				unsubscribe();
			});
		}
		function handleTouchStartCapture(event) {
			currentPointerTypeRef.current = "touch";
			addTargetEventListenerOnce(event, handleTouchStart);
		}
		function closeOnPressOutsideCapture(event) {
			cancelDismissOnEndTimeout.clear();
			if (event.type === "pointerdown") currentPointerTypeRef.current = event.pointerType;
			if (event.type === "mousedown" && touchStateRef.current && !touchStateRef.current.dismissOnMouseDown) return;
			addTargetEventListenerOnce(event, (targetEvent) => {
				if (targetEvent.type === "pointerdown") handlePointerDown(targetEvent);
				else closeOnPressOutside(targetEvent);
			});
		}
		function handlePressEndCapture(event) {
			if (!pressStartedInsideRef.current) return;
			const pressStartedInsideDefaultPrevented = pressStartPreventedRef.current;
			resetPressStartState();
			if (getOutsidePressEvent() !== "intentional") return;
			if (event.type === "pointercancel") {
				if (pressStartedInsideDefaultPrevented) suppressImmediateOutsideClickAfterPreventedStart();
				return;
			}
			if (isEventWithinFloatingTree(event)) return;
			if (pressStartedInsideDefaultPrevented) {
				suppressImmediateOutsideClickAfterPreventedStart();
				return;
			}
			if (typeof outsidePress$1 === "function" && !outsidePress$1(event)) return;
			preventedPressSuppressionTimeout.clear();
			suppressNextOutsideClickRef.current = true;
			clearInsideReactTree();
		}
		function handleTouchMove(event) {
			if (getOutsidePressEvent() !== "sloppy" || !touchStateRef.current || isEventWithinOwnElements(event)) return;
			const touch = event.touches[0];
			if (!touch) return;
			const deltaX = Math.abs(touch.clientX - touchStateRef.current.startX);
			const deltaY = Math.abs(touch.clientY - touchStateRef.current.startY);
			const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
			if (distance > 5) touchStateRef.current.dismissOnTouchEnd = true;
			if (distance > 10) {
				closeOnPressOutside(event);
				cancelDismissOnEndTimeout.clear();
				touchStateRef.current = null;
			}
		}
		function handleTouchMoveCapture(event) {
			addTargetEventListenerOnce(event, handleTouchMove);
		}
		function handleTouchEnd(event) {
			if (getOutsidePressEvent() !== "sloppy" || !touchStateRef.current || isEventWithinOwnElements(event)) return;
			if (touchStateRef.current.dismissOnTouchEnd) closeOnPressOutside(event);
			cancelDismissOnEndTimeout.clear();
			touchStateRef.current = null;
		}
		function handleTouchEndCapture(event) {
			addTargetEventListenerOnce(event, handleTouchEnd);
		}
		const doc = ownerDocument(floatingElement);
		const unsubscribe = mergeCleanups(escapeKey$1 && mergeCleanups(addEventListener(doc, "keydown", closeOnEscapeKeyDown), addEventListener(doc, "compositionstart", handleCompositionStart), addEventListener(doc, "compositionend", handleCompositionEnd)), outsidePressEnabled && mergeCleanups(addEventListener(doc, "click", closeOnPressOutsideCapture, true), addEventListener(doc, "pointerdown", closeOnPressOutsideCapture, true), addEventListener(doc, "pointerup", handlePressEndCapture, true), addEventListener(doc, "pointercancel", handlePressEndCapture, true), addEventListener(doc, "mousedown", closeOnPressOutsideCapture, true), addEventListener(doc, "mouseup", handlePressEndCapture, true), addEventListener(doc, "touchstart", handleTouchStartCapture, true), addEventListener(doc, "touchmove", handleTouchMoveCapture, true), addEventListener(doc, "touchend", handleTouchEndCapture, true)));
		return () => {
			unsubscribe();
			compositionTimeout.clear();
			preventedPressSuppressionTimeout.clear();
			resetPressStartState();
			suppressNextOutsideClickRef.current = false;
			clearInsideReactTree();
		};
	}, [
		dataRef,
		floatingElement,
		escapeKey$1,
		outsidePressEnabled,
		outsidePress$1,
		open,
		enabled,
		escapeKeyBubbles,
		outsidePressBubbles,
		closeOnEscapeKeyDown,
		clearInsideReactTree,
		getOutsidePressEventProp,
		hasBlockingChild,
		isEventWithinOwnElements,
		tree,
		store,
		cancelDismissOnEndTimeout
	]);
	const reference = React$3.useMemo(() => ({
		onKeyDown: closeOnEscapeKeyDown,
		onPointerDown: closeOnReferencePress,
		onClick: closeOnReferencePress
	}), [closeOnEscapeKeyDown, closeOnReferencePress]);
	const floating = React$3.useMemo(() => ({
		onKeyDown: closeOnEscapeKeyDown,
		onPointerDown: markInsidePressStartPrevented,
		onMouseDown: markInsidePressStartPrevented,
		onClickCapture: markInsideReactTree,
		onMouseDownCapture(event) {
			markInsideReactTree();
			markPressStartedInsideReactTree(event);
		},
		onPointerDownCapture(event) {
			markInsideReactTree();
			markPressStartedInsideReactTree(event);
		},
		onMouseUpCapture: markInsideReactTree,
		onTouchEndCapture: markInsideReactTree,
		onTouchMoveCapture: markInsideReactTree
	}), [
		closeOnEscapeKeyDown,
		markInsideReactTree,
		markPressStartedInsideReactTree,
		markInsidePressStartPrevented
	]);
	return React$3.useMemo(() => enabled ? {
		reference,
		floating,
		trigger: reference
	} : {}, [
		enabled,
		reference,
		floating
	]);
}
//#endregion
//#region ../../../node_modules/.pnpm/@floating-ui+core@1.8.0/node_modules/@floating-ui/core/dist/floating-ui.core.mjs
function computeCoordsFromPlacement(_ref, placement, rtl) {
	let { reference, floating } = _ref;
	const sideAxis = getSideAxis(placement);
	const alignmentAxis = getAlignmentAxis(placement);
	const alignLength = getAxisLength(alignmentAxis);
	const side = getSide(placement);
	const isVertical = sideAxis === "y";
	const commonX = reference.x + reference.width / 2 - floating.width / 2;
	const commonY = reference.y + reference.height / 2 - floating.height / 2;
	const commonAlign = reference[alignLength] / 2 - floating[alignLength] / 2;
	let coords;
	switch (side) {
		case "top":
			coords = {
				x: commonX,
				y: reference.y - floating.height
			};
			break;
		case "bottom":
			coords = {
				x: commonX,
				y: reference.y + reference.height
			};
			break;
		case "right":
			coords = {
				x: reference.x + reference.width,
				y: commonY
			};
			break;
		case "left":
			coords = {
				x: reference.x - floating.width,
				y: commonY
			};
			break;
		default: coords = {
			x: reference.x,
			y: reference.y
		};
	}
	const alignment = getAlignment(placement);
	if (alignment) coords[alignmentAxis] += commonAlign * (alignment === "end" ? 1 : -1) * (rtl && isVertical ? -1 : 1);
	return coords;
}
/**
* Resolves with an object of overflow side offsets that determine how much the
* element is overflowing a given clipping boundary on each side.
* - positive = overflowing the boundary by that number of pixels
* - negative = how many pixels left before it will overflow
* - 0 = lies flush with the boundary
* @see https://floating-ui.com/docs/detectOverflow
*/
async function detectOverflow(state, options) {
	var _await$platform$isEle;
	if (options === void 0) options = {};
	const { x, y, platform, rects, elements, strategy } = state;
	const { boundary = "clippingAncestors", rootBoundary = "viewport", elementContext = "floating", altBoundary = false, padding = 0 } = evaluate(options, state);
	const paddingObject = getPaddingObject(padding);
	const element = elements[altBoundary ? elementContext === "floating" ? "reference" : "floating" : elementContext];
	const clippingClientRect = rectToClientRect(await platform.getClippingRect({
		element: ((_await$platform$isEle = await (platform.isElement == null ? void 0 : platform.isElement(element))) != null ? _await$platform$isEle : true) ? element : element.contextElement || await (platform.getDocumentElement == null ? void 0 : platform.getDocumentElement(elements.floating)),
		boundary,
		rootBoundary,
		strategy
	}));
	const rect = elementContext === "floating" ? {
		x,
		y,
		width: rects.floating.width,
		height: rects.floating.height
	} : rects.reference;
	const offsetParent = await (platform.getOffsetParent == null ? void 0 : platform.getOffsetParent(elements.floating));
	const offsetScale = await (platform.isElement == null ? void 0 : platform.isElement(offsetParent)) && await (platform.getScale == null ? void 0 : platform.getScale(offsetParent)) || {
		x: 1,
		y: 1
	};
	const elementClientRect = rectToClientRect(platform.convertOffsetParentRelativeRectToViewportRelativeRect ? await platform.convertOffsetParentRelativeRectToViewportRelativeRect({
		elements,
		rect,
		offsetParent,
		strategy
	}) : rect);
	return {
		top: (clippingClientRect.top - elementClientRect.top + paddingObject.top) / offsetScale.y,
		bottom: (elementClientRect.bottom - clippingClientRect.bottom + paddingObject.bottom) / offsetScale.y,
		left: (clippingClientRect.left - elementClientRect.left + paddingObject.left) / offsetScale.x,
		right: (elementClientRect.right - clippingClientRect.right + paddingObject.right) / offsetScale.x
	};
}
var MAX_RESET_COUNT = 50;
/**
* Computes the `x` and `y` coordinates that will place the floating element
* next to a given reference element.
*
* This export does not have any `platform` interface logic. You will need to
* write one for the platform you are using Floating UI with.
*/
var computePosition$1 = async (reference, floating, config) => {
	const { placement = "bottom", strategy = "absolute", middleware = [], platform } = config;
	const platformWithDetectOverflow = platform.detectOverflow ? platform : {
		...platform,
		detectOverflow
	};
	const rtl = await (platform.isRTL == null ? void 0 : platform.isRTL(floating));
	let rects = await platform.getElementRects({
		reference,
		floating,
		strategy
	});
	let { x, y } = computeCoordsFromPlacement(rects, placement, rtl);
	let statefulPlacement = placement;
	let resetCount = 0;
	const middlewareData = {};
	for (let i = 0; i < middleware.length; i++) {
		const currentMiddleware = middleware[i];
		if (!currentMiddleware) continue;
		const { name, fn } = currentMiddleware;
		const { x: nextX, y: nextY, data, reset } = await fn({
			x,
			y,
			initialPlacement: placement,
			placement: statefulPlacement,
			strategy,
			middlewareData,
			rects,
			platform: platformWithDetectOverflow,
			elements: {
				reference,
				floating
			}
		});
		x = nextX != null ? nextX : x;
		y = nextY != null ? nextY : y;
		middlewareData[name] = {
			...middlewareData[name],
			...data
		};
		if (reset && resetCount < MAX_RESET_COUNT) {
			resetCount++;
			if (typeof reset === "object") {
				if (reset.placement) statefulPlacement = reset.placement;
				if (reset.rects) rects = reset.rects === true ? await platform.getElementRects({
					reference,
					floating,
					strategy
				}) : reset.rects;
				({x, y} = computeCoordsFromPlacement(rects, statefulPlacement, rtl));
			}
			i = -1;
		}
	}
	return {
		x,
		y,
		placement: statefulPlacement,
		strategy,
		middlewareData
	};
};
/**
* Optimizes the visibility of the floating element by flipping the `placement`
* in order to keep it in view when the preferred placement(s) will overflow the
* clipping boundary. Alternative to `autoPlacement`.
* @see https://floating-ui.com/docs/flip
*/
var flip$2 = function(options) {
	if (options === void 0) options = {};
	return {
		name: "flip",
		options,
		async fn(state) {
			var _middlewareData$arrow, _middlewareData$flip;
			const { placement, middlewareData, rects, initialPlacement, platform, elements } = state;
			const { mainAxis: checkMainAxis = true, crossAxis: checkCrossAxis = true, fallbackPlacements: specifiedFallbackPlacements, fallbackStrategy = "bestFit", fallbackAxisSideDirection = "none", flipAlignment = true, ...detectOverflowOptions } = evaluate(options, state);
			if ((_middlewareData$arrow = middlewareData.arrow) != null && _middlewareData$arrow.alignmentOffset) return {};
			const side = getSide(placement);
			const initialSideAxis = getSideAxis(initialPlacement);
			const isBasePlacement = getSide(initialPlacement) === initialPlacement;
			const rtl = await (platform.isRTL == null ? void 0 : platform.isRTL(elements.floating));
			const fallbackPlacements = specifiedFallbackPlacements || (isBasePlacement || !flipAlignment ? [getOppositePlacement(initialPlacement)] : getExpandedPlacements(initialPlacement));
			const hasFallbackAxisSideDirection = fallbackAxisSideDirection !== "none";
			if (!specifiedFallbackPlacements && hasFallbackAxisSideDirection) fallbackPlacements.push(...getOppositeAxisPlacements(initialPlacement, flipAlignment, fallbackAxisSideDirection, rtl));
			const placements = [initialPlacement, ...fallbackPlacements];
			const overflow = await platform.detectOverflow(state, detectOverflowOptions);
			const overflows = [];
			let overflowsData = ((_middlewareData$flip = middlewareData.flip) == null ? void 0 : _middlewareData$flip.overflows) || [];
			if (checkMainAxis) overflows.push(overflow[side]);
			if (checkCrossAxis) {
				const sides = getAlignmentSides(placement, rects, rtl);
				overflows.push(overflow[sides[0]], overflow[sides[1]]);
			}
			overflowsData = [...overflowsData, {
				placement,
				overflows
			}];
			if (!overflows.every((side) => side <= 0)) {
				var _middlewareData$flip2, _overflowsData$filter;
				const nextIndex = (((_middlewareData$flip2 = middlewareData.flip) == null ? void 0 : _middlewareData$flip2.index) || 0) + 1;
				const nextPlacement = placements[nextIndex];
				if (nextPlacement) {
					if (!(checkCrossAxis === "alignment" ? initialSideAxis !== getSideAxis(nextPlacement) : false) || overflowsData.every((d) => getSideAxis(d.placement) === initialSideAxis ? d.overflows[0] > 0 : true)) return {
						data: {
							index: nextIndex,
							overflows: overflowsData
						},
						reset: { placement: nextPlacement }
					};
				}
				let resetPlacement = (_overflowsData$filter = overflowsData.filter((d) => d.overflows[0] <= 0).sort((a, b) => a.overflows[1] - b.overflows[1])[0]) == null ? void 0 : _overflowsData$filter.placement;
				if (!resetPlacement) switch (fallbackStrategy) {
					case "bestFit": {
						var _overflowsData$filter2;
						const placement = (_overflowsData$filter2 = overflowsData.filter((d) => {
							if (hasFallbackAxisSideDirection) {
								const currentSideAxis = getSideAxis(d.placement);
								return currentSideAxis === initialSideAxis || currentSideAxis === "y";
							}
							return true;
						}).map((d) => [d.placement, d.overflows.filter((overflow) => overflow > 0).reduce((acc, overflow) => acc + overflow, 0)]).sort((a, b) => a[1] - b[1])[0]) == null ? void 0 : _overflowsData$filter2[0];
						if (placement) resetPlacement = placement;
						break;
					}
					case "initialPlacement":
						resetPlacement = initialPlacement;
						break;
				}
				if (placement !== resetPlacement) return { reset: { placement: resetPlacement } };
			}
			return {};
		}
	};
};
var originSides = /* @__PURE__ */ new Set(["left", "top"]);
async function convertValueToCoords(state, options) {
	const { placement, platform, elements } = state;
	const rtl = await (platform.isRTL == null ? void 0 : platform.isRTL(elements.floating));
	const side = getSide(placement);
	const alignment = getAlignment(placement);
	const isVertical = getSideAxis(placement) === "y";
	const mainAxisMulti = originSides.has(side) ? -1 : 1;
	const crossAxisMulti = rtl && isVertical ? -1 : 1;
	const rawValue = evaluate(options, state);
	let { mainAxis, crossAxis, alignmentAxis } = typeof rawValue === "number" ? {
		mainAxis: rawValue,
		crossAxis: 0,
		alignmentAxis: null
	} : {
		mainAxis: rawValue.mainAxis || 0,
		crossAxis: rawValue.crossAxis || 0,
		alignmentAxis: rawValue.alignmentAxis
	};
	if (alignment && typeof alignmentAxis === "number") crossAxis = alignment === "end" ? alignmentAxis * -1 : alignmentAxis;
	return isVertical ? {
		x: crossAxis * crossAxisMulti,
		y: mainAxis * mainAxisMulti
	} : {
		x: mainAxis * mainAxisMulti,
		y: crossAxis * crossAxisMulti
	};
}
/**
* Modifies the placement by translating the floating element along the
* specified axes.
* A number (shorthand for `mainAxis` or distance), or an axes configuration
* object may be passed.
* @see https://floating-ui.com/docs/offset
*/
var offset$2 = function(options) {
	if (options === void 0) options = 0;
	return {
		name: "offset",
		options,
		async fn(state) {
			var _middlewareData$offse, _middlewareData$arrow;
			const { x, y, placement, middlewareData } = state;
			const diffCoords = await convertValueToCoords(state, options);
			if (placement === ((_middlewareData$offse = middlewareData.offset) == null ? void 0 : _middlewareData$offse.placement) && (_middlewareData$arrow = middlewareData.arrow) != null && _middlewareData$arrow.alignmentOffset) return {};
			return {
				x: x + diffCoords.x,
				y: y + diffCoords.y,
				data: {
					...diffCoords,
					placement
				}
			};
		}
	};
};
/**
* Optimizes the visibility of the floating element by shifting it in order to
* keep it in view when it will overflow the clipping boundary.
* @see https://floating-ui.com/docs/shift
*/
var shift$2 = function(options) {
	if (options === void 0) options = {};
	return {
		name: "shift",
		options,
		async fn(state) {
			const { x, y, placement, platform } = state;
			const { mainAxis: checkMainAxis = true, crossAxis: checkCrossAxis = false, limiter = { fn: (_ref) => {
				let { x, y } = _ref;
				return {
					x,
					y
				};
			} }, ...detectOverflowOptions } = evaluate(options, state);
			const coords = {
				x,
				y
			};
			const overflow = await platform.detectOverflow(state, detectOverflowOptions);
			const crossAxis = getSideAxis(placement);
			const mainAxis = getOppositeAxis(crossAxis);
			let mainAxisCoord = coords[mainAxis];
			let crossAxisCoord = coords[crossAxis];
			const clampCoord = (axis, coord) => clamp$1(coord + overflow[axis === "y" ? "top" : "left"], coord, coord - overflow[axis === "y" ? "bottom" : "right"]);
			if (checkMainAxis) mainAxisCoord = clampCoord(mainAxis, mainAxisCoord);
			if (checkCrossAxis) crossAxisCoord = clampCoord(crossAxis, crossAxisCoord);
			const limitedCoords = limiter.fn({
				...state,
				[mainAxis]: mainAxisCoord,
				[crossAxis]: crossAxisCoord
			});
			return {
				...limitedCoords,
				data: {
					x: limitedCoords.x - x,
					y: limitedCoords.y - y,
					enabled: {
						[mainAxis]: checkMainAxis,
						[crossAxis]: checkCrossAxis
					}
				}
			};
		}
	};
};
/**
* Built-in `limiter` that will stop `shift()` at a certain point.
*/
var limitShift$2 = function(options) {
	if (options === void 0) options = {};
	return {
		options,
		fn(state) {
			var _rawOffset$mainAxis, _rawOffset$crossAxis;
			const { x, y, placement, rects, middlewareData } = state;
			const { offset = 0, mainAxis: checkMainAxis = true, crossAxis: checkCrossAxis = true } = evaluate(options, state);
			const coords = {
				x,
				y
			};
			const crossAxis = getSideAxis(placement);
			const mainAxis = getOppositeAxis(crossAxis);
			let mainAxisCoord = coords[mainAxis];
			let crossAxisCoord = coords[crossAxis];
			const rawOffset = evaluate(offset, state);
			const computedOffset = typeof rawOffset === "number" ? {
				mainAxis: rawOffset,
				crossAxis: 0
			} : {
				mainAxis: (_rawOffset$mainAxis = rawOffset.mainAxis) != null ? _rawOffset$mainAxis : 0,
				crossAxis: (_rawOffset$crossAxis = rawOffset.crossAxis) != null ? _rawOffset$crossAxis : 0
			};
			if (checkMainAxis) {
				const len = mainAxis === "y" ? "height" : "width";
				const limitMin = rects.reference[mainAxis] - rects.floating[len] + computedOffset.mainAxis;
				const limitMax = rects.reference[mainAxis] + rects.reference[len] - computedOffset.mainAxis;
				if (mainAxisCoord < limitMin) mainAxisCoord = limitMin;
				else if (mainAxisCoord > limitMax) mainAxisCoord = limitMax;
			}
			if (checkCrossAxis) {
				var _middlewareData$offse, _middlewareData$offse2;
				const len = mainAxis === "y" ? "width" : "height";
				const isOriginSide = originSides.has(getSide(placement));
				const limitMin = rects.reference[crossAxis] - rects.floating[len] + (isOriginSide ? ((_middlewareData$offse = middlewareData.offset) == null ? void 0 : _middlewareData$offse[crossAxis]) || 0 : 0) + (isOriginSide ? 0 : computedOffset.crossAxis);
				const limitMax = rects.reference[crossAxis] + rects.reference[len] + (isOriginSide ? 0 : ((_middlewareData$offse2 = middlewareData.offset) == null ? void 0 : _middlewareData$offse2[crossAxis]) || 0) - (isOriginSide ? computedOffset.crossAxis : 0);
				if (crossAxisCoord < limitMin) crossAxisCoord = limitMin;
				else if (crossAxisCoord > limitMax) crossAxisCoord = limitMax;
			}
			return {
				[mainAxis]: mainAxisCoord,
				[crossAxis]: crossAxisCoord
			};
		}
	};
};
/**
* Provides data that allows you to change the size of the floating element —
* for instance, prevent it from overflowing the clipping boundary or match the
* width of the reference element.
* @see https://floating-ui.com/docs/size
*/
var size$2 = function(options) {
	if (options === void 0) options = {};
	return {
		name: "size",
		options,
		async fn(state) {
			const { placement, rects, platform, elements } = state;
			const { apply = () => {}, ...detectOverflowOptions } = evaluate(options, state);
			const overflow = await platform.detectOverflow(state, detectOverflowOptions);
			const side = getSide(placement);
			const alignment = getAlignment(placement);
			const isYAxis = getSideAxis(placement) === "y";
			const { width, height } = rects.floating;
			let heightSide;
			let widthSide;
			if (side === "top" || side === "bottom") {
				heightSide = side;
				widthSide = alignment === (await (platform.isRTL == null ? void 0 : platform.isRTL(elements.floating)) ? "start" : "end") ? "left" : "right";
			} else {
				widthSide = side;
				heightSide = alignment === "end" ? "top" : "bottom";
			}
			const maximumClippingHeight = height - overflow.top - overflow.bottom;
			const maximumClippingWidth = width - overflow.left - overflow.right;
			const overflowAvailableHeight = min(height - overflow[heightSide], maximumClippingHeight);
			const overflowAvailableWidth = min(width - overflow[widthSide], maximumClippingWidth);
			const shiftData = state.middlewareData.shift;
			const noShift = !shiftData;
			let availableHeight = overflowAvailableHeight;
			let availableWidth = overflowAvailableWidth;
			if (shiftData != null && shiftData.enabled.x) availableWidth = maximumClippingWidth;
			if (shiftData != null && shiftData.enabled.y) availableHeight = maximumClippingHeight;
			if (noShift && !alignment) if (isYAxis) availableWidth = width - 2 * max(overflow.left, overflow.right);
			else availableHeight = height - 2 * max(overflow.top, overflow.bottom);
			await apply({
				...state,
				availableWidth,
				availableHeight
			});
			const nextDimensions = await platform.getDimensions(elements.floating);
			if (width !== nextDimensions.width || height !== nextDimensions.height) return { reset: { rects: true } };
			return {};
		}
	};
};
//#endregion
//#region ../../../node_modules/.pnpm/@floating-ui+dom@1.8.0/node_modules/@floating-ui/dom/dist/floating-ui.dom.mjs
function getCssDimensions(element) {
	const css = getComputedStyle$1(element);
	let width = parseFloat(css.width) || 0;
	let height = parseFloat(css.height) || 0;
	const hasOffset = isHTMLElement(element);
	const offsetWidth = hasOffset ? element.offsetWidth : width;
	const offsetHeight = hasOffset ? element.offsetHeight : height;
	const shouldFallback = round(width) !== offsetWidth || round(height) !== offsetHeight;
	if (shouldFallback) {
		width = offsetWidth;
		height = offsetHeight;
	}
	return {
		width,
		height,
		$: shouldFallback
	};
}
function unwrapElement(element) {
	return !isElement(element) ? element.contextElement : element;
}
function getScale$1(element) {
	const domElement = unwrapElement(element);
	if (!isHTMLElement(domElement)) return createCoords(1);
	const rect = domElement.getBoundingClientRect();
	const { width, height, $ } = getCssDimensions(domElement);
	let x = ($ ? round(rect.width) : rect.width) / width;
	let y = ($ ? round(rect.height) : rect.height) / height;
	if (!x || !Number.isFinite(x)) x = 1;
	if (!y || !Number.isFinite(y)) y = 1;
	return {
		x,
		y
	};
}
var noOffsets = /* @__PURE__ */ createCoords(0);
function getVisualOffsets(element) {
	const win = getWindow(element);
	if (!isWebKit() || !win.visualViewport) return noOffsets;
	return {
		x: win.visualViewport.offsetLeft,
		y: win.visualViewport.offsetTop
	};
}
function shouldAddVisualOffsets(element, isFixed, floatingOffsetParent) {
	if (isFixed === void 0) isFixed = false;
	return !!floatingOffsetParent && isFixed && floatingOffsetParent === getWindow(element);
}
function getBoundingClientRect(element, includeScale, isFixedStrategy, offsetParent) {
	if (includeScale === void 0) includeScale = false;
	if (isFixedStrategy === void 0) isFixedStrategy = false;
	const clientRect = element.getBoundingClientRect();
	const domElement = unwrapElement(element);
	let scale = createCoords(1);
	if (includeScale) if (offsetParent) {
		if (isElement(offsetParent)) scale = getScale$1(offsetParent);
	} else scale = getScale$1(element);
	const visualOffsets = shouldAddVisualOffsets(domElement, isFixedStrategy, offsetParent) ? getVisualOffsets(domElement) : createCoords(0);
	let x = (clientRect.left + visualOffsets.x) / scale.x;
	let y = (clientRect.top + visualOffsets.y) / scale.y;
	let width = clientRect.width / scale.x;
	let height = clientRect.height / scale.y;
	if (domElement && offsetParent) {
		const win = getWindow(domElement);
		const offsetWin = isElement(offsetParent) ? getWindow(offsetParent) : offsetParent;
		let currentWin = win;
		let currentIFrame = getFrameElement(currentWin);
		while (currentIFrame && offsetWin !== currentWin) {
			const iframeScale = getScale$1(currentIFrame);
			const iframeRect = currentIFrame.getBoundingClientRect();
			const css = getComputedStyle$1(currentIFrame);
			const left = iframeRect.left + (currentIFrame.clientLeft + parseFloat(css.paddingLeft)) * iframeScale.x;
			const top = iframeRect.top + (currentIFrame.clientTop + parseFloat(css.paddingTop)) * iframeScale.y;
			x *= iframeScale.x;
			y *= iframeScale.y;
			width *= iframeScale.x;
			height *= iframeScale.y;
			x += left;
			y += top;
			currentWin = getWindow(currentIFrame);
			currentIFrame = getFrameElement(currentWin);
		}
	}
	return rectToClientRect({
		width,
		height,
		x,
		y
	});
}
function getWindowScrollBarX(element, rect) {
	const leftScroll = getNodeScroll(element).scrollLeft;
	if (!rect) return getBoundingClientRect(getDocumentElement(element)).left + leftScroll;
	return rect.left + leftScroll;
}
function getHTMLOffset(documentElement, scroll) {
	const htmlRect = documentElement.getBoundingClientRect();
	return {
		x: htmlRect.left + scroll.scrollLeft - getWindowScrollBarX(documentElement, htmlRect),
		y: htmlRect.top + scroll.scrollTop
	};
}
function convertOffsetParentRelativeRectToViewportRelativeRect(_ref) {
	let { elements, rect, offsetParent, strategy } = _ref;
	const isFixed = strategy === "fixed";
	const documentElement = getDocumentElement(offsetParent);
	const topLayer = elements ? isTopLayer(elements.floating) : false;
	if (offsetParent === documentElement || topLayer && isFixed) return rect;
	let scroll = {
		scrollLeft: 0,
		scrollTop: 0
	};
	let scale = createCoords(1);
	const offsets = createCoords(0);
	const isOffsetParentAnElement = isHTMLElement(offsetParent);
	if (isOffsetParentAnElement || !isFixed) {
		if (getNodeName(offsetParent) !== "body" || isOverflowElement(documentElement)) scroll = getNodeScroll(offsetParent);
		if (isOffsetParentAnElement) {
			const offsetRect = getBoundingClientRect(offsetParent);
			scale = getScale$1(offsetParent);
			offsets.x = offsetRect.x + offsetParent.clientLeft;
			offsets.y = offsetRect.y + offsetParent.clientTop;
		}
	}
	const htmlOffset = documentElement && !isOffsetParentAnElement && !isFixed ? getHTMLOffset(documentElement, scroll) : createCoords(0);
	return {
		width: rect.width * scale.x,
		height: rect.height * scale.y,
		x: rect.x * scale.x - scroll.scrollLeft * scale.x + offsets.x + htmlOffset.x,
		y: rect.y * scale.y - scroll.scrollTop * scale.y + offsets.y + htmlOffset.y
	};
}
function getClientRects(element) {
	return element.getClientRects ? Array.from(element.getClientRects()) : [];
}
function getDocumentRect(html) {
	const scroll = getNodeScroll(html);
	const body = html.ownerDocument.body;
	const width = max(html.scrollWidth, html.clientWidth, body.scrollWidth, body.clientWidth);
	const height = max(html.scrollHeight, html.clientHeight, body.scrollHeight, body.clientHeight);
	let x = -scroll.scrollLeft + getWindowScrollBarX(html);
	const y = -scroll.scrollTop;
	if (getComputedStyle$1(body).direction === "rtl") x += max(html.clientWidth, body.clientWidth) - width;
	return {
		width,
		height,
		x,
		y
	};
}
var SCROLLBAR_MAX = 25;
function getViewportRect(element, strategy, rootBoundary) {
	if (rootBoundary === void 0) rootBoundary = "viewport";
	const isLayoutViewport = rootBoundary === "layoutViewport";
	const win = getWindow(element);
	const html = getDocumentElement(element);
	const visualViewport = win.visualViewport;
	let width = html.clientWidth;
	let height = html.clientHeight;
	let x = 0;
	let y = 0;
	if (visualViewport) {
		const layoutRelativeClientCoords = !isWebKit() || strategy === "fixed";
		if (isLayoutViewport) {
			if (!layoutRelativeClientCoords) {
				x = -visualViewport.offsetLeft;
				y = -visualViewport.offsetTop;
			}
		} else {
			width = visualViewport.width;
			height = visualViewport.height;
			if (layoutRelativeClientCoords) {
				x = visualViewport.offsetLeft;
				y = visualViewport.offsetTop;
			}
		}
	}
	if (getWindowScrollBarX(html) <= 0) {
		const doc = html.ownerDocument;
		const body = doc.body;
		const bodyStyles = getComputedStyle(body);
		const bodyMarginInline = doc.compatMode === "CSS1Compat" ? parseFloat(bodyStyles.marginLeft) + parseFloat(bodyStyles.marginRight) || 0 : 0;
		const reservedWidth = Math.abs(html.clientWidth - body.clientWidth - bodyMarginInline);
		const gutter = getComputedStyle(html).scrollbarGutter === "stable both-edges" ? reservedWidth / 2 : reservedWidth;
		if (gutter <= SCROLLBAR_MAX) width -= gutter;
	}
	return {
		width,
		height,
		x,
		y
	};
}
function getInnerBoundingClientRect(element, strategy) {
	const clientRect = getBoundingClientRect(element, true, strategy === "fixed");
	const top = clientRect.top + element.clientTop;
	const left = clientRect.left + element.clientLeft;
	const scale = getScale$1(element);
	return {
		width: element.clientWidth * scale.x,
		height: element.clientHeight * scale.y,
		x: left * scale.x,
		y: top * scale.y
	};
}
function getClientRectFromClippingAncestor(element, clippingAncestor, strategy) {
	let rect;
	if (clippingAncestor === "viewport" || clippingAncestor === "layoutViewport") rect = getViewportRect(element, strategy, clippingAncestor);
	else if (clippingAncestor === "document") rect = getDocumentRect(getDocumentElement(element));
	else if (isElement(clippingAncestor)) rect = getInnerBoundingClientRect(clippingAncestor, strategy);
	else {
		const visualOffsets = getVisualOffsets(element);
		rect = {
			x: clippingAncestor.x - visualOffsets.x,
			y: clippingAncestor.y - visualOffsets.y,
			width: clippingAncestor.width,
			height: clippingAncestor.height
		};
	}
	return rectToClientRect(rect);
}
function getClippingElementAncestors(element, cache) {
	const cachedResult = cache.get(element);
	if (cachedResult) return cachedResult;
	let result = getOverflowAncestors(element, [], false).filter((el) => isElement(el) && getNodeName(el) !== "body");
	let lastKeptComputedStyle = null;
	const elementIsFixed = getComputedStyle$1(element).position === "fixed";
	let currentNode = elementIsFixed ? getParentNode(element) : element;
	while (isElement(currentNode) && !isLastTraversableNode(currentNode)) {
		const computedStyle = getComputedStyle$1(currentNode);
		const currentNodeIsContaining = isContainingBlock(currentNode);
		const lastPosition = lastKeptComputedStyle ? lastKeptComputedStyle.position : elementIsFixed ? "fixed" : "";
		if (!currentNodeIsContaining && (lastPosition === "fixed" || lastPosition === "absolute" && computedStyle.position === "static")) result = result.filter((ancestor) => ancestor !== currentNode);
		else lastKeptComputedStyle = computedStyle;
		currentNode = getParentNode(currentNode);
	}
	cache.set(element, result);
	return result;
}
function getClippingRect(_ref) {
	let { element, boundary, rootBoundary, strategy } = _ref;
	const clippingAncestors = [...boundary === "clippingAncestors" ? isTopLayer(element) ? [] : getClippingElementAncestors(element, this._c) : [].concat(boundary), rootBoundary];
	const firstRect = getClientRectFromClippingAncestor(element, clippingAncestors[0], strategy);
	let top = firstRect.top;
	let right = firstRect.right;
	let bottom = firstRect.bottom;
	let left = firstRect.left;
	for (let i = 1; i < clippingAncestors.length; i++) {
		const rect = getClientRectFromClippingAncestor(element, clippingAncestors[i], strategy);
		top = max(rect.top, top);
		right = min(rect.right, right);
		bottom = min(rect.bottom, bottom);
		left = max(rect.left, left);
	}
	return {
		width: right - left,
		height: bottom - top,
		x: left,
		y: top
	};
}
function getDimensions(element) {
	const { width, height } = getCssDimensions(element);
	return {
		width,
		height
	};
}
function getRectRelativeToOffsetParent(element, offsetParent, strategy) {
	const isOffsetParentAnElement = isHTMLElement(offsetParent);
	const documentElement = getDocumentElement(offsetParent);
	const isFixed = strategy === "fixed";
	const rect = getBoundingClientRect(element, true, isFixed, offsetParent);
	let scroll = {
		scrollLeft: 0,
		scrollTop: 0
	};
	const offsets = createCoords(0);
	if (isOffsetParentAnElement || !isFixed) {
		if (getNodeName(offsetParent) !== "body" || isOverflowElement(documentElement)) scroll = getNodeScroll(offsetParent);
		if (isOffsetParentAnElement) {
			const offsetRect = getBoundingClientRect(offsetParent, true, isFixed, offsetParent);
			offsets.x = offsetRect.x + offsetParent.clientLeft;
			offsets.y = offsetRect.y + offsetParent.clientTop;
		}
	}
	if (!isOffsetParentAnElement && documentElement) offsets.x = getWindowScrollBarX(documentElement);
	const htmlOffset = documentElement && !isOffsetParentAnElement && !isFixed ? getHTMLOffset(documentElement, scroll) : createCoords(0);
	return {
		x: rect.left + scroll.scrollLeft - offsets.x - htmlOffset.x,
		y: rect.top + scroll.scrollTop - offsets.y - htmlOffset.y,
		width: rect.width,
		height: rect.height
	};
}
function isStaticPositioned(element) {
	return getComputedStyle$1(element).position === "static";
}
function getTrueOffsetParent(element, polyfill) {
	if (!isHTMLElement(element) || getComputedStyle$1(element).position === "fixed") return null;
	if (polyfill) return polyfill(element);
	let rawOffsetParent = element.offsetParent;
	if (getDocumentElement(element) === rawOffsetParent) rawOffsetParent = rawOffsetParent.ownerDocument.body;
	return rawOffsetParent;
}
function getOffsetParent(element, polyfill) {
	const win = getWindow(element);
	if (isTopLayer(element)) return win;
	if (!isHTMLElement(element)) {
		let svgOffsetParent = getParentNode(element);
		while (svgOffsetParent && !isLastTraversableNode(svgOffsetParent)) {
			if (isElement(svgOffsetParent) && !isStaticPositioned(svgOffsetParent)) return svgOffsetParent;
			svgOffsetParent = getParentNode(svgOffsetParent);
		}
		return win;
	}
	let offsetParent = getTrueOffsetParent(element, polyfill);
	while (offsetParent && isTableElement(offsetParent) && isStaticPositioned(offsetParent)) offsetParent = getTrueOffsetParent(offsetParent, polyfill);
	if (offsetParent && isLastTraversableNode(offsetParent) && isStaticPositioned(offsetParent) && !isContainingBlock(offsetParent)) return win;
	return offsetParent || getContainingBlock(element) || win;
}
var getElementRects = async function(data) {
	const getOffsetParentFn = this.getOffsetParent || getOffsetParent;
	const getDimensionsFn = this.getDimensions;
	const floatingDimensions = await getDimensionsFn(data.floating);
	return {
		reference: getRectRelativeToOffsetParent(data.reference, await getOffsetParentFn(data.floating), data.strategy),
		floating: {
			x: 0,
			y: 0,
			width: floatingDimensions.width,
			height: floatingDimensions.height
		}
	};
};
function isRTL(element) {
	return getComputedStyle$1(element).direction === "rtl";
}
var platform = {
	convertOffsetParentRelativeRectToViewportRelativeRect,
	getDocumentElement,
	getClippingRect,
	getOffsetParent,
	getElementRects,
	getClientRects,
	getDimensions,
	getScale: getScale$1,
	isElement,
	isRTL
};
function rectsAreEqual(a, b) {
	return a.x === b.x && a.y === b.y && a.width === b.width && a.height === b.height;
}
function observeMove(element, onMove, ancestorResize) {
	let io = null;
	let timeoutId;
	const root = getDocumentElement(element);
	function cleanup() {
		var _io;
		clearTimeout(timeoutId);
		(_io = io) == null || _io.disconnect();
		io = null;
	}
	function refresh(skip, threshold) {
		if (skip === void 0) skip = false;
		if (threshold === void 0) threshold = 1;
		cleanup();
		const elementRectForRootMargin = element.getBoundingClientRect();
		const { left, top, width, height } = elementRectForRootMargin;
		if (!skip) onMove();
		if (!width || !height) return;
		const insetTop = floor(top);
		const insetRight = floor(root.clientWidth - (left + width));
		const insetBottom = floor(root.clientHeight - (top + height));
		const insetLeft = floor(left);
		const options = {
			rootMargin: -insetTop + "px " + -insetRight + "px " + -insetBottom + "px " + -insetLeft + "px",
			threshold: max(0, min(1, threshold)) || 1
		};
		let isFirstUpdate = true;
		function handleObserve(entries) {
			const ratio = entries[0].intersectionRatio;
			if (!rectsAreEqual(elementRectForRootMargin, element.getBoundingClientRect())) return refresh();
			if (ratio !== threshold) {
				if (!isFirstUpdate) return refresh();
				if (!ratio) timeoutId = setTimeout(() => {
					refresh(false, 1e-7);
				}, 1e3);
				else refresh(false, ratio);
			}
			isFirstUpdate = false;
		}
		try {
			io = new IntersectionObserver(handleObserve, {
				...options,
				root: root.ownerDocument
			});
		} catch (_e) {
			io = new IntersectionObserver(handleObserve, options);
		}
		io.observe(element);
	}
	const win = getWindow(element);
	const handleResize = () => refresh(ancestorResize);
	win.addEventListener("resize", handleResize);
	refresh(true);
	return () => {
		win.removeEventListener("resize", handleResize);
		cleanup();
	};
}
/**
* Automatically updates the position of the floating element when necessary.
* Should only be called when the floating element is mounted on the DOM or
* visible on the screen.
* @returns cleanup function that should be invoked when the floating element is
* removed from the DOM or hidden from the screen.
* @see https://floating-ui.com/docs/autoUpdate
*/
function autoUpdate(reference, floating, update, options) {
	if (options === void 0) options = {};
	const { ancestorScroll = true, ancestorResize = true, elementResize = typeof ResizeObserver === "function", layoutShift = typeof IntersectionObserver === "function", animationFrame = false } = options;
	const referenceEl = unwrapElement(reference);
	const ancestors = ancestorScroll || ancestorResize ? [...referenceEl ? getOverflowAncestors(referenceEl) : [], ...floating ? getOverflowAncestors(floating) : []] : [];
	ancestors.forEach((ancestor) => {
		ancestorScroll && ancestor.addEventListener("scroll", update);
		ancestorResize && ancestor.addEventListener("resize", update);
	});
	const cleanupIo = referenceEl && layoutShift ? observeMove(referenceEl, update, ancestorResize) : null;
	let reobserveFrame = -1;
	let resizeObserver = null;
	if (elementResize) {
		resizeObserver = new ResizeObserver((_ref) => {
			let [firstEntry] = _ref;
			if (firstEntry && firstEntry.target === referenceEl && resizeObserver && floating) {
				resizeObserver.unobserve(floating);
				cancelAnimationFrame(reobserveFrame);
				reobserveFrame = requestAnimationFrame(() => {
					var _resizeObserver;
					(_resizeObserver = resizeObserver) == null || _resizeObserver.observe(floating);
				});
			}
			update();
		});
		if (referenceEl && !animationFrame) resizeObserver.observe(referenceEl);
		if (floating) resizeObserver.observe(floating);
	}
	let frameId;
	let prevRefRect = animationFrame ? getBoundingClientRect(reference) : null;
	if (animationFrame) frameLoop();
	function frameLoop() {
		const nextRefRect = getBoundingClientRect(reference);
		if (prevRefRect && !rectsAreEqual(prevRefRect, nextRefRect)) update();
		prevRefRect = nextRefRect;
		frameId = requestAnimationFrame(frameLoop);
	}
	update();
	return () => {
		var _resizeObserver2;
		ancestors.forEach((ancestor) => {
			ancestorScroll && ancestor.removeEventListener("scroll", update);
			ancestorResize && ancestor.removeEventListener("resize", update);
		});
		cleanupIo?.();
		(_resizeObserver2 = resizeObserver) == null || _resizeObserver2.disconnect();
		resizeObserver = null;
		if (animationFrame) cancelAnimationFrame(frameId);
	};
}
/**
* Modifies the placement by translating the floating element along the
* specified axes.
* A number (shorthand for `mainAxis` or distance), or an axes configuration
* object may be passed.
* @see https://floating-ui.com/docs/offset
*/
var offset$1 = offset$2;
/**
* Optimizes the visibility of the floating element by shifting it in order to
* keep it in view when it will overflow the clipping boundary.
* @see https://floating-ui.com/docs/shift
*/
var shift$1 = shift$2;
/**
* Optimizes the visibility of the floating element by flipping the `placement`
* in order to keep it in view when the preferred placement(s) will overflow the
* clipping boundary. Alternative to `autoPlacement`.
* @see https://floating-ui.com/docs/flip
*/
var flip$1 = flip$2;
/**
* Provides data that allows you to change the size of the floating element —
* for instance, prevent it from overflowing the clipping boundary or match the
* width of the reference element.
* @see https://floating-ui.com/docs/size
*/
var size$1 = size$2;
/**
* Built-in `limiter` that will stop `shift()` at a certain point.
*/
var limitShift$1 = limitShift$2;
/**
* Computes the `x` and `y` coordinates that will place the floating element
* next to a given reference element.
*/
var computePosition = (reference, floating, options) => {
	const cache = /* @__PURE__ */ new Map();
	const mergedOptions = options != null ? options : {};
	const platformWithCache = {
		...platform,
		...mergedOptions.platform,
		_c: cache
	};
	return computePosition$1(reference, floating, {
		...mergedOptions,
		platform: platformWithCache
	});
};
//#endregion
//#region ../../../node_modules/.pnpm/@floating-ui+react-dom@2.1._4d1b94ad0aba41d4082f69fd75c7603b/node_modules/@floating-ui/react-dom/dist/floating-ui.react-dom.mjs
var index = typeof document !== "undefined" ? useLayoutEffect : function noop() {};
function deepEqual(a, b) {
	if (a === b) return true;
	if (typeof a !== typeof b) return false;
	if (typeof a === "function" && a.toString() === b.toString()) return true;
	let length;
	let i;
	let keys;
	if (a && b && typeof a === "object") {
		if (Array.isArray(a)) {
			length = a.length;
			if (length !== b.length) return false;
			for (i = length; i-- !== 0;) if (!deepEqual(a[i], b[i])) return false;
			return true;
		}
		keys = Object.keys(a);
		length = keys.length;
		if (length !== Object.keys(b).length) return false;
		for (i = length; i-- !== 0;) if (!{}.hasOwnProperty.call(b, keys[i])) return false;
		for (i = length; i-- !== 0;) {
			const key = keys[i];
			if (key === "_owner" && a.$$typeof) continue;
			if (!deepEqual(a[key], b[key])) return false;
		}
		return true;
	}
	return a !== a && b !== b;
}
function getDPR(element) {
	return 1;
}
function roundByDPR(element, value) {
	const dpr = getDPR(element);
	return Math.round(value * dpr) / dpr;
}
function useLatestRef(value) {
	const ref = React$3.useRef(value);
	index(() => {
		ref.current = value;
	});
	return ref;
}
/**
* Provides data to position a floating element.
* @see https://floating-ui.com/docs/useFloating
*/
function useFloating(options) {
	if (options === void 0) options = {};
	const { placement = "bottom", strategy = "absolute", middleware = [], platform, elements: { reference: externalReference, floating: externalFloating } = {}, transform = true, whileElementsMounted, open } = options;
	const [data, setData] = React$3.useState({
		x: 0,
		y: 0,
		strategy,
		placement,
		middlewareData: {},
		isPositioned: false
	});
	const [latestMiddleware, setLatestMiddleware] = React$3.useState(middleware);
	if (!deepEqual(latestMiddleware, middleware)) setLatestMiddleware(middleware);
	const [_reference, _setReference] = React$3.useState(null);
	const [_floating, _setFloating] = React$3.useState(null);
	const setReference = React$3.useCallback((node) => {
		if (node !== referenceRef.current) {
			referenceRef.current = node;
			_setReference(node);
		}
	}, []);
	const setFloating = React$3.useCallback((node) => {
		if (node !== floatingRef.current) {
			floatingRef.current = node;
			_setFloating(node);
		}
	}, []);
	const referenceEl = externalReference || _reference;
	const floatingEl = externalFloating || _floating;
	const referenceRef = React$3.useRef(null);
	const floatingRef = React$3.useRef(null);
	const dataRef = React$3.useRef(data);
	const hasWhileElementsMounted = whileElementsMounted != null;
	const whileElementsMountedRef = useLatestRef(whileElementsMounted);
	const platformRef = useLatestRef(platform);
	const openRef = useLatestRef(open);
	const update = React$3.useCallback(() => {
		if (!referenceRef.current || !floatingRef.current) return;
		const config = {
			placement,
			strategy,
			middleware: latestMiddleware
		};
		if (platformRef.current) config.platform = platformRef.current;
		computePosition(referenceRef.current, floatingRef.current, config).then((data) => {
			const fullData = {
				...data,
				isPositioned: openRef.current !== false
			};
			if (isMountedRef.current && !deepEqual(dataRef.current, fullData)) {
				dataRef.current = fullData;
				ReactDOM.flushSync(() => {
					setData(fullData);
				});
			}
		});
	}, [
		latestMiddleware,
		placement,
		strategy,
		platformRef,
		openRef
	]);
	index(() => {
		if (open === false && dataRef.current.isPositioned) {
			dataRef.current.isPositioned = false;
			setData((data) => ({
				...data,
				isPositioned: false
			}));
		}
	}, [open]);
	const isMountedRef = React$3.useRef(false);
	index(() => {
		isMountedRef.current = true;
		return () => {
			isMountedRef.current = false;
		};
	}, []);
	index(() => {
		if (referenceEl) referenceRef.current = referenceEl;
		if (floatingEl) floatingRef.current = floatingEl;
		if (referenceEl && floatingEl) {
			if (whileElementsMountedRef.current) return whileElementsMountedRef.current(referenceEl, floatingEl, update);
			update();
		}
	}, [
		referenceEl,
		floatingEl,
		update,
		whileElementsMountedRef,
		hasWhileElementsMounted
	]);
	const refs = React$3.useMemo(() => ({
		reference: referenceRef,
		floating: floatingRef,
		setReference,
		setFloating
	}), [setReference, setFloating]);
	const elements = React$3.useMemo(() => ({
		reference: referenceEl,
		floating: floatingEl
	}), [referenceEl, floatingEl]);
	const floatingStyles = React$3.useMemo(() => {
		const initialStyles = {
			position: strategy,
			left: 0,
			top: 0
		};
		if (!elements.floating) return initialStyles;
		const x = roundByDPR(elements.floating, data.x);
		const y = roundByDPR(elements.floating, data.y);
		if (transform) return {
			...initialStyles,
			transform: "translate(" + x + "px, " + y + "px)",
			...getDPR(elements.floating) >= 1.5 && { willChange: "transform" }
		};
		return {
			position: strategy,
			left: x,
			top: y
		};
	}, [
		strategy,
		transform,
		elements.floating,
		data.x,
		data.y
	]);
	return React$3.useMemo(() => ({
		...data,
		update,
		refs,
		elements,
		floatingStyles
	}), [
		data,
		update,
		refs,
		elements,
		floatingStyles
	]);
}
/**
* Modifies the placement by translating the floating element along the
* specified axes.
* A number (shorthand for `mainAxis` or distance), or an axes configuration
* object may be passed.
* @see https://floating-ui.com/docs/offset
*/
var offset = (options, deps) => {
	const result = offset$1(options);
	return {
		name: result.name,
		fn: result.fn,
		options: [options, deps]
	};
};
/**
* Optimizes the visibility of the floating element by shifting it in order to
* keep it in view when it will overflow the clipping boundary.
* @see https://floating-ui.com/docs/shift
*/
var shift = (options, deps) => {
	const result = shift$1(options);
	return {
		name: result.name,
		fn: result.fn,
		options: [options, deps]
	};
};
/**
* Built-in `limiter` that will stop `shift()` at a certain point.
*/
var limitShift = (options, deps) => {
	return {
		fn: limitShift$1(options).fn,
		options: [options, deps]
	};
};
/**
* Optimizes the visibility of the floating element by flipping the `placement`
* in order to keep it in view when the preferred placement(s) will overflow the
* clipping boundary. Alternative to `autoPlacement`.
* @see https://floating-ui.com/docs/flip
*/
var flip = (options, deps) => {
	const result = flip$1(options);
	return {
		name: result.name,
		fn: result.fn,
		options: [options, deps]
	};
};
/**
* Provides data that allows you to change the size of the floating element —
* for instance, prevent it from overflowing the clipping boundary or match the
* width of the reference element.
* @see https://floating-ui.com/docs/size
*/
var size = (options, deps) => {
	const result = size$1(options);
	return {
		name: result.name,
		fn: result.fn,
		options: [options, deps]
	};
};
//#endregion
//#region ../../../node_modules/.pnpm/use-sync-external-store@1.6.0_react@19.2.6/node_modules/use-sync-external-store/cjs/use-sync-external-store-shim.production.js
/**
* @license React
* use-sync-external-store-shim.production.js
*
* Copyright (c) Meta Platforms, Inc. and affiliates.
*
* This source code is licensed under the MIT license found in the
* LICENSE file in the root directory of this source tree.
*/
var require_use_sync_external_store_shim_production = /* @__PURE__ */ __commonJSMin(((exports) => {
	var React$2 = __require("react");
	React$2.useState;
	React$2.useEffect;
	React$2.useLayoutEffect;
	React$2.useDebugValue;
	function useSyncExternalStore$1(subscribe, getSnapshot) {
		return getSnapshot();
	}
	var shim = useSyncExternalStore$1;
	exports.useSyncExternalStore = void 0 !== React$2.useSyncExternalStore ? React$2.useSyncExternalStore : shim;
}));
//#endregion
//#region ../../../node_modules/.pnpm/use-sync-external-store@1.6.0_react@19.2.6/node_modules/use-sync-external-store/shim/index.js
var require_shim = /* @__PURE__ */ __commonJSMin(((exports, module) => {
	module.exports = require_use_sync_external_store_shim_production();
}));
//#endregion
//#region ../../../node_modules/.pnpm/use-sync-external-store@1.6.0_react@19.2.6/node_modules/use-sync-external-store/cjs/use-sync-external-store-shim/with-selector.production.js
/**
* @license React
* use-sync-external-store-shim/with-selector.production.js
*
* Copyright (c) Meta Platforms, Inc. and affiliates.
*
* This source code is licensed under the MIT license found in the
* LICENSE file in the root directory of this source tree.
*/
var require_with_selector_production = /* @__PURE__ */ __commonJSMin(((exports) => {
	var React$1 = __require("react"), shim = require_shim();
	function is(x, y) {
		return x === y && (0 !== x || 1 / x === 1 / y) || x !== x && y !== y;
	}
	var objectIs = "function" === typeof Object.is ? Object.is : is, useSyncExternalStore = shim.useSyncExternalStore, useRef = React$1.useRef, useEffect = React$1.useEffect, useMemo = React$1.useMemo, useDebugValue = React$1.useDebugValue;
	exports.useSyncExternalStoreWithSelector = function(subscribe, getSnapshot, getServerSnapshot, selector, isEqual) {
		var instRef = useRef(null);
		if (null === instRef.current) {
			var inst = {
				hasValue: !1,
				value: null
			};
			instRef.current = inst;
		} else inst = instRef.current;
		instRef = useMemo(function() {
			function memoizedSelector(nextSnapshot) {
				if (!hasMemo) {
					hasMemo = !0;
					memoizedSnapshot = nextSnapshot;
					nextSnapshot = selector(nextSnapshot);
					if (void 0 !== isEqual && inst.hasValue) {
						var currentSelection = inst.value;
						if (isEqual(currentSelection, nextSnapshot)) return memoizedSelection = currentSelection;
					}
					return memoizedSelection = nextSnapshot;
				}
				currentSelection = memoizedSelection;
				if (objectIs(memoizedSnapshot, nextSnapshot)) return currentSelection;
				var nextSelection = selector(nextSnapshot);
				if (void 0 !== isEqual && isEqual(currentSelection, nextSelection)) return memoizedSnapshot = nextSnapshot, currentSelection;
				memoizedSnapshot = nextSnapshot;
				return memoizedSelection = nextSelection;
			}
			var hasMemo = !1, memoizedSnapshot, memoizedSelection, maybeGetServerSnapshot = void 0 === getServerSnapshot ? null : getServerSnapshot;
			return [function() {
				return memoizedSelector(getSnapshot());
			}, null === maybeGetServerSnapshot ? void 0 : function() {
				return memoizedSelector(maybeGetServerSnapshot());
			}];
		}, [
			getSnapshot,
			getServerSnapshot,
			selector,
			isEqual
		]);
		var value = useSyncExternalStore(subscribe, instRef[0], instRef[1]);
		useEffect(function() {
			inst.hasValue = !0;
			inst.value = value;
		}, [value]);
		useDebugValue(value);
		return value;
	};
}));
//#endregion
//#region ../../../node_modules/.pnpm/use-sync-external-store@1.6.0_react@19.2.6/node_modules/use-sync-external-store/shim/with-selector.js
var require_with_selector = /* @__PURE__ */ __commonJSMin(((exports, module) => {
	module.exports = require_with_selector_production();
}));
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/fastHooks.mjs
var hooks = [];
var currentInstance = void 0;
function getInstance() {
	return currentInstance;
}
function register(hook) {
	hooks.push(hook);
}
/**
* Wraps a component function to enable performance optimizations for internal hooks.
*
* **Performance Optimization:**
* Components wrapped with `fastComponent` have access to a shared "instance" context that enables
* specialized hook implementations to batch operations and reduce overhead. The wrapper creates a
* stable instance object that persists across renders, sets it as the current context, calls
* registered hooks before and after rendering, then clears the context. The primary benefit is
* with `useStore`, where multiple store subscriptions within the same component are collapsed into
* a single `useSyncExternalStore` subscription per store, significantly reducing re-render overhead.
* This optimization is only active on React 19+; on earlier versions `useStore` falls back to a
* separate subscription per call.
*
* **Requirements:**
* - The component function should follow standard React component patterns
* - `useStore` calls must keep a stable order and count across renders, as batched hooks are
*   matched by call index
* - Do not rely on the instance context outside of specialized hooks
*
* @param fn - The component function to wrap
* @returns A wrapped component with the same signature as the input function
*
* @example
* ```tsx
* // Wrapping a component to enable optimized useStore batching
* export const TooltipRoot = fastComponent(function TooltipRoot(props) {
*   // These useStore calls share a single subscription
*   const open = useStore(store, (state) => state.open);
*   const disabled = useStore(store, (state) => state.disabled);
*   const value = useStore(store, (state) => state.value);
*   // ...
* });
* ```
*/
function fastComponent(fn) {
	const FastComponent = (props, forwardedRef) => {
		const instance = useRefWithInit(createInstance).current;
		let result;
		try {
			currentInstance = instance;
			for (const hook of hooks) hook.before(instance);
			result = fn(props, forwardedRef);
			for (const hook of hooks) hook.after(instance);
			instance.didInitialize = true;
		} finally {
			currentInstance = void 0;
		}
		return result;
	};
	FastComponent.displayName = fn.displayName || fn.name;
	return FastComponent;
}
/**
* Wraps a component function with ref forwarding to enable performance optimizations for internal hooks.
*
* This is a convenience wrapper that combines `fastComponent` with `React.forwardRef`, enabling
* both performance optimizations and proper ref forwarding. See `fastComponent` for details on
* the performance benefits.
*
* @param fn - The component function that accepts props and a forwarded ref
* @returns A wrapped component with ref forwarding enabled
*
* @example
* ```tsx
* // Wrapping a component with ref forwarding and optimized hooks
* export const TooltipTrigger = fastComponentRef(function TooltipTrigger(
*   props,
*   forwardedRef
* ) {
*   const store = useContext(TooltipContext);
*   const open = useStore(store, (state) => state.open);
*   // ... component logic with ref
*   return <button ref={forwardedRef} {...props} />;
* });
* ```
*/
function fastComponentRef(fn) {
	return /* @__PURE__ */ React$3.forwardRef(fastComponent(fn));
}
function createInstance() {
	return { didInitialize: false };
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/store/useStore.mjs
var import_shim = require_shim();
var import_with_selector = require_with_selector();
var useStoreImplementation = isReactVersionAtLeast(19) ? useStoreFast : useStoreLegacy;
function useStore(store, selector, a1, a2, a3) {
	return useStoreImplementation(store, selector, a1, a2, a3);
}
function useStoreR19(store, selector, a1, a2, a3) {
	const getSelection = React$3.useCallback(() => selector(store.getSnapshot(), a1, a2, a3), [
		store,
		selector,
		a1,
		a2,
		a3
	]);
	return (0, import_shim.useSyncExternalStore)(store.subscribe, getSelection, getSelection);
}
register({
	before(instance) {
		instance.syncIndex = 0;
		if (!instance.didInitialize) {
			instance.syncTick = 1;
			instance.syncHooks = [];
			instance.didChangeStore = true;
			instance.getSnapshot = () => {
				let didChange = false;
				for (let i = 0; i < instance.syncHooks.length; i += 1) {
					const hook = instance.syncHooks[i];
					const value = hook.selector(hook.store.state, hook.a1, hook.a2, hook.a3);
					if (!Object.is(hook.value, value)) {
						didChange = true;
						hook.value = value;
					}
				}
				if (didChange) instance.syncTick += 1;
				return instance.syncTick;
			};
		}
	},
	after(instance) {
		if (instance.syncHooks.length > 0) {
			if (instance.didChangeStore) {
				instance.didChangeStore = false;
				instance.subscribe = (onStoreChange) => {
					const stores = /* @__PURE__ */ new Set();
					for (const hook of instance.syncHooks) stores.add(hook.store);
					const unsubscribes = [];
					for (const store of stores) unsubscribes.push(store.subscribe(onStoreChange));
					return () => {
						for (const unsubscribe of unsubscribes) unsubscribe();
					};
				};
			}
			(0, import_shim.useSyncExternalStore)(instance.subscribe, instance.getSnapshot, instance.getSnapshot);
		}
	}
});
function useStoreFast(store, selector, a1, a2, a3) {
	const instance = getInstance();
	if (!instance) return useStoreR19(store, selector, a1, a2, a3);
	const index = instance.syncIndex;
	instance.syncIndex += 1;
	let hook;
	if (!instance.didInitialize) {
		hook = {
			store,
			selector,
			a1,
			a2,
			a3,
			value: selector(store.getSnapshot(), a1, a2, a3)
		};
		instance.syncHooks.push(hook);
	} else {
		hook = instance.syncHooks[index];
		if (hook.store !== store || hook.selector !== selector || !Object.is(hook.a1, a1) || !Object.is(hook.a2, a2) || !Object.is(hook.a3, a3)) {
			if (hook.store !== store) instance.didChangeStore = true;
			hook.store = store;
			hook.selector = selector;
			hook.a1 = a1;
			hook.a2 = a2;
			hook.a3 = a3;
			hook.value = selector(store.getSnapshot(), a1, a2, a3);
		}
	}
	return hook.value;
}
function useStoreLegacy(store, selector, a1, a2, a3) {
	return (0, import_with_selector.useSyncExternalStoreWithSelector)(store.subscribe, store.getSnapshot, store.getSnapshot, (state) => selector(state, a1, a2, a3));
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/store/Store.mjs
/**
* A data store implementation that allows subscribing to state changes and updating the state.
* It uses an observer pattern to notify subscribers when the state changes.
*/
var Store = class {
	/**
	* The current state of the store.
	* This property is updated immediately when the state changes as a result of calling {@link setState}, {@link update}, or {@link set}.
	* To subscribe to state changes, use the {@link useState} method. The value returned by {@link useState} is updated after the component renders (similarly to React's useState).
	* The values can be used directly (to avoid subscribing to the store) in effects or event handlers.
	*
	* Do not modify properties in state directly. Instead, use the provided methods to ensure proper state management and listener notification.
	*/
	constructor(state) {
		this.state = state;
		this.listeners = /* @__PURE__ */ new Set();
		this.updateTick = 0;
	}
	/**
	* Registers a listener that will be called whenever the store's state changes.
	*
	* @param fn The listener function to be called on state changes.
	* @returns A function to unsubscribe the listener.
	*/
	subscribe = (fn) => {
		this.listeners.add(fn);
		return () => {
			this.listeners.delete(fn);
		};
	};
	/**
	* Returns the current state of the store.
	*/
	getSnapshot = () => {
		return this.state;
	};
	/**
	* Updates the entire store's state and notifies all registered listeners.
	*
	* @param newState The new state to set for the store.
	*/
	setState(newState) {
		if (this.state === newState) return;
		this.state = newState;
		this.updateTick += 1;
		const currentTick = this.updateTick;
		for (const listener of this.listeners) {
			if (currentTick !== this.updateTick) return;
			listener(newState);
		}
	}
	/**
	* Merges the provided changes into the current state and notifies listeners if there are changes.
	*
	* @param changes An object containing the changes to apply to the current state.
	*/
	update(changes) {
		for (const key in changes) if (!Object.is(this.state[key], changes[key])) {
			this.setState({
				...this.state,
				...changes
			});
			return;
		}
	}
	/**
	* Sets a specific key in the store's state to a new value and notifies listeners if the value has changed.
	*
	* @param key The key in the store's state to update.
	* @param value The new value to set for the specified key.
	*/
	set(key, value) {
		if (!Object.is(this.state[key], value)) this.setState({
			...this.state,
			[key]: value
		});
	}
	/**
	* Gives the state a new reference and updates all registered listeners.
	*/
	notifyAll() {
		const newState = { ...this.state };
		this.setState(newState);
	}
	use(selector, a1, a2, a3) {
		return useStore(this, selector, a1, a2, a3);
	}
};
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/store/ReactStore.mjs
/**
* A Store that supports controlled state keys, non-reactive values and provides utility methods for React.
*/
var ReactStore = class extends Store {
	/**
	* Creates a new ReactStore instance.
	*
	* @param state Initial state of the store.
	* @param context Non-reactive context values.
	* @param selectors Optional selectors for use with `useState`.
	*/
	constructor(state, context = {}, selectors) {
		super(state);
		this.context = context;
		this.selectors = selectors;
	}
	/**
	* Non-reactive values such as refs, callbacks, etc.
	*/
	/**
	* Synchronizes a single external value into the store.
	*
	* Note that the while the value in `state` is updated immediately, the value returned
	* by `useState` is updated before the next render (similarly to React's `useState`).
	*/
	useSyncedValue(key, value) {
		React$3.useDebugValue(key);
		const store = this;
		useIsoLayoutEffect(() => {
			if (store.state[key] !== value) store.set(key, value);
		}, [
			store,
			key,
			value
		]);
	}
	/**
	* Synchronizes a single external value into the store and
	* cleans it up (sets to `undefined`) on unmount.
	*
	* Note that the while the value in `state` is updated immediately, the value returned
	* by `useState` is updated before the next render (similarly to React's `useState`).
	*/
	useSyncedValueWithCleanup(key, value) {
		const store = this;
		useIsoLayoutEffect(() => {
			if (store.state[key] !== value) store.set(key, value);
			return () => {
				store.set(key, void 0);
			};
		}, [
			store,
			key,
			value
		]);
	}
	/**
	* Synchronizes multiple external values into the store.
	*
	* Note that the while the values in `state` are updated immediately, the values returned
	* by `useState` are updated before the next render (similarly to React's `useState`).
	*/
	useSyncedValues(statePart) {
		const store = this;
		useIsoLayoutEffect(() => {
			store.update(statePart);
		}, [store, ...Object.values(statePart)]);
	}
	/**
	* Registers a controllable prop pair (`controlled`, `defaultValue`) for a specific key. If `controlled`
	* is non-undefined, the store's state at `key` is updated to match `controlled`.
	*/
	useControlledProp(key, controlled) {
		React$3.useDebugValue(key);
		const store = this;
		const isControlled = controlled !== void 0;
		useIsoLayoutEffect(() => {
			if (isControlled && !Object.is(store.state[key], controlled)) store.setState({
				...store.state,
				[key]: controlled
			});
		}, [
			store,
			key,
			controlled,
			isControlled
		]);
	}
	/** Gets the current value from the store using a selector with the provided key.
	*
	* @param key Key of the selector to use.
	*/
	select(key, a1, a2, a3) {
		const selector = this.selectors[key];
		return selector(this.state, a1, a2, a3);
	}
	/**
	* Returns a value from the store's state using a selector function.
	* Used to subscribe to specific parts of the state.
	* This methods causes a rerender whenever the selected state changes.
	*
	* @param key Key of the selector to use.
	*/
	useState(key, a1, a2, a3) {
		React$3.useDebugValue(key);
		return useStore(this, this.selectors[key], a1, a2, a3);
	}
	/**
	* Wraps a function with `useStableCallback` to ensure it has a stable reference
	* and assigns it to the context.
	*
	* @param key Key of the event callback. Must be a function in the context.
	* @param fn Function to assign.
	*/
	useContextCallback(key, fn) {
		React$3.useDebugValue(key);
		const stableFunction = useStableCallback(fn ?? NOOP);
		this.context[key] = stableFunction;
	}
	/**
	* Returns a stable setter function for a specific key in the store's state.
	* It's commonly used to pass as a ref callback to React elements.
	*
	* @param key Key of the state to set.
	*/
	useStateSetter(key) {
		const ref = React$3.useRef(void 0);
		if (ref.current === void 0) ref.current = (value) => {
			this.set(key, value);
		};
		return ref.current;
	}
	/**
	* Observes changes derived from the store's selectors and calls the listener when the selected value changes.
	*
	* @param key Key of the selector to observe.
	* @param listener Listener function called when the selector result changes.
	*/
	observe(selector, listener) {
		let selectFn;
		if (typeof selector === "function") selectFn = selector;
		else selectFn = this.selectors[selector];
		let prevValue = selectFn(this.state);
		listener(prevValue, prevValue, this);
		return this.subscribe((nextState) => {
			const nextValue = selectFn(nextState);
			if (!Object.is(prevValue, nextValue)) {
				const oldValue = prevValue;
				prevValue = nextValue;
				listener(nextValue, oldValue, this);
			}
		});
	}
};
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/components/FloatingRootStore.mjs
var selectors$3 = {
	open: (state) => state.open,
	transitionStatus: (state) => state.transitionStatus,
	domReferenceElement: (state) => state.domReferenceElement,
	referenceElement: (state) => state.positionReference ?? state.referenceElement,
	floatingElement: (state) => state.floatingElement,
	floatingId: (state) => state.floatingId
};
var FloatingRootStore = class extends ReactStore {
	constructor(options) {
		const { syncOnly, nested, onOpenChange, triggerElements, ...initialState } = options;
		super({
			...initialState,
			positionReference: initialState.referenceElement,
			domReferenceElement: initialState.referenceElement
		}, {
			onOpenChange,
			dataRef: { current: {} },
			events: createEventEmitter(),
			nested,
			triggerElements
		}, selectors$3);
		this.syncOnly = syncOnly;
	}
	/**
	* Syncs the event used by hover logic to distinguish hover-open from click-like interaction.
	*/
	syncOpenEvent = (newOpen, event) => {
		if (!newOpen || !this.state.open || event != null && isClickLikeEvent(event)) this.context.dataRef.current.openEvent = newOpen ? event : void 0;
	};
	/**
	* Runs the root-owned side effects for an open state change.
	*/
	dispatchOpenChange = (newOpen, eventDetails) => {
		this.syncOpenEvent(newOpen, eventDetails.event);
		const details = {
			open: newOpen,
			reason: eventDetails.reason,
			nativeEvent: eventDetails.event,
			nested: this.context.nested,
			triggerElement: eventDetails.trigger
		};
		this.context.events.emit("openchange", details);
	};
	/**
	* Emits the `openchange` event through the internal event emitter and calls the `onOpenChange` handler with the provided arguments.
	*
	* @param newOpen The new open state.
	* @param eventDetails Details about the event that triggered the open state change.
	*/
	setOpen = (newOpen, eventDetails) => {
		if (this.syncOnly) {
			this.context.onOpenChange?.(newOpen, eventDetails);
			return;
		}
		this.dispatchOpenChange(newOpen, eventDetails);
		this.context.onOpenChange?.(newOpen, eventDetails);
	};
};
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/hooks/useSyncedFloatingRootContext.mjs
/**
* Keeps a FloatingRootStore in sync with the provided PopupStore.
* Uses the provided FloatingRootStore when one exists, otherwise creates one once and updates it on every render.
*/
function useSyncedFloatingRootContext(options) {
	const { popupStore, treatPopupAsFloatingElement = false, floatingRootContext: floatingRootContextProp, floatingId, nested, onOpenChange } = options;
	const open = popupStore.useState("open");
	const referenceElement = popupStore.useState("activeTriggerElement");
	const floatingElement = popupStore.useState(treatPopupAsFloatingElement ? "popupElement" : "positionerElement");
	const triggerElements = popupStore.context.triggerElements;
	const handleOpenChange = onOpenChange;
	const internalStoreRef = React$3.useRef(null);
	if (floatingRootContextProp === void 0 && internalStoreRef.current === null) internalStoreRef.current = new FloatingRootStore({
		open,
		transitionStatus: void 0,
		referenceElement,
		floatingElement,
		triggerElements,
		onOpenChange: handleOpenChange,
		floatingId,
		syncOnly: true,
		nested
	});
	const store = floatingRootContextProp ?? internalStoreRef.current;
	popupStore.useSyncedValue("floatingId", floatingId);
	useIsoLayoutEffect(() => {
		const valuesToSync = {
			open,
			floatingId,
			referenceElement,
			floatingElement
		};
		if (isElement(referenceElement)) valuesToSync.domReferenceElement = referenceElement;
		if (store.state.positionReference === store.state.referenceElement) valuesToSync.positionReference = referenceElement;
		store.update(valuesToSync);
	}, [
		open,
		floatingId,
		referenceElement,
		floatingElement,
		store
	]);
	store.context.onOpenChange = handleOpenChange;
	store.context.nested = nested;
	return store;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/popups/popupStoreUtils.mjs
var FOCUSABLE_POPUP_PROPS = {
	tabIndex: -1,
	[FOCUSABLE_ATTRIBUTE]: ""
};
/**
* Returns the default `initialFocus` resolver for a popup. When opened by touch it focuses the
* popup element itself to prevent the virtual keyboard from opening (required for Android
* specifically; iOS handles this automatically). Otherwise it falls back to the default behavior.
*/
function createDefaultInitialFocus(popupRef) {
	return (interactionType) => interactionType === "touch" ? popupRef.current : true;
}
/**
* The subset of a popup handle that a Root needs to bind its store to. Both the real handle classes
* and any test double satisfy it.
*/
/**
* Creates and owns a popup store on behalf of a Root part. The store is created exactly once, with
* controlled props and root state synced separately after creation. Sets up the synced floating
* root context and returns the store.
*
* @param createStore Factory that builds the store. Called exactly once, receiving the floating id
* and whether the popup is nested inside another floating element, both resolved on the first render.
* @param treatPopupAsFloatingElement Whether the popup element is passed to Floating UI as the
* floating element instead of the default positioner.
*/
function usePopupRootStore(createStore, treatPopupAsFloatingElement = false) {
	const floatingId = useId();
	const nested = useFloatingParentNodeId() != null;
	const store = useRefWithInit(() => createStore(floatingId, nested)).current;
	useSyncedFloatingRootContext({
		popupStore: store,
		treatPopupAsFloatingElement,
		floatingRootContext: store.state.floatingRootContext,
		floatingId,
		nested,
		onOpenChange: store.setOpen
	});
	return store;
}
/**
* Attaches a Root's store to a handle for this component's committed lifetime. Popup Roots render
* it before their interactions and user children so its layout effect runs before descendant layout
* effects. This lets descendants call the handle during the Root's initial commit without attaching
* during render, which would leak suspended or abandoned stores. Store subscribers are notified by
* `attachStore` in this ordinary layout phase, where React permits synchronous updates.
*
* Popup Roots must render this component only when a handle is present so handle-less Roots avoid
* mounting an extra fiber and layout effect.
*/
function PopupHandleAttachment({ handle, store }) {
	useIsoLayoutEffect(() => {
		return handle.attachStore(store);
	}, [handle, store]);
	return null;
}
/**
* Returns a callback ref that registers/unregisters the trigger element in the store.
*
* @param store The Store instance where the trigger should be registered.
*/
function useTriggerRegistration(id, store) {
	const registeredElementIdRef = React$3.useRef(null);
	const registeredElementRef = React$3.useRef(null);
	return React$3.useCallback((element) => {
		if (id === void 0) return;
		let shouldSyncTriggerCount = false;
		if (registeredElementIdRef.current !== null) {
			const registeredId = registeredElementIdRef.current;
			const registeredElement = registeredElementRef.current;
			const currentElement = store.context.triggerElements.getById(registeredId);
			if (registeredElement && currentElement === registeredElement) {
				store.context.triggerElements.delete(registeredId);
				shouldSyncTriggerCount = true;
			}
			registeredElementIdRef.current = null;
			registeredElementRef.current = null;
		}
		if (element !== null) {
			registeredElementIdRef.current = id;
			registeredElementRef.current = element;
			store.context.triggerElements.add(id, element);
			shouldSyncTriggerCount = true;
		}
		if (shouldSyncTriggerCount) {
			const triggerCount = store.context.triggerElements.size;
			if (store.select("open") && store.state.triggerCount !== triggerCount) store.set("triggerCount", triggerCount);
		}
	}, [store, id]);
}
function setPopupOpenState(state, open, trigger, preventUnmountOnClose = false) {
	if (open) state.preventUnmountingOnClose = false;
	else if (preventUnmountOnClose) state.preventUnmountingOnClose = true;
	const triggerId = trigger?.id ?? null;
	if (triggerId || open) {
		state.activeTriggerId = triggerId;
		state.activeTriggerElement = trigger ?? null;
	}
}
function attachPreventUnmountOnClose(eventDetails) {
	let preventUnmountOnClose = false;
	eventDetails.preventUnmountOnClose = () => {
		preventUnmountOnClose = true;
	};
	return () => preventUnmountOnClose;
}
/**
* Runs the shared open-change sequence for a popup store: notifies `onOpenChange`,
* honors cancellation, dispatches the floating root change, maps the reason to an
* `instantType`, and commits the state update (synchronously for hover so
* `getAnimations()` observes it). Stores supply their own differences via
* `extraState` (e.g. the last change reason) and `onBeforeDispatch` (e.g. updating
* inline-rect coordinates).
*/
function applyPopupOpenChange(store, nextOpen, eventDetails, options = {}) {
	const reason = eventDetails.reason;
	const isHover = reason === triggerHover;
	const isFocusOpen = nextOpen && reason === "trigger-focus";
	const isDismissClose = !nextOpen && (reason === "trigger-press" || reason === "escape-key");
	const shouldPreventUnmountOnClose = attachPreventUnmountOnClose(eventDetails);
	store.context.onOpenChange?.(nextOpen, eventDetails);
	if (eventDetails.isCanceled) return;
	options.onBeforeDispatch?.();
	store.state.floatingRootContext.dispatchOpenChange(nextOpen, eventDetails);
	const changeState = () => {
		const updatedState = {
			...options.extraState,
			open: nextOpen
		};
		if (isFocusOpen) updatedState.instantType = "focus";
		else if (isDismissClose) updatedState.instantType = "dismiss";
		else if (isHover) updatedState.instantType = void 0;
		setPopupOpenState(updatedState, nextOpen, eventDetails.trigger, shouldPreventUnmountOnClose());
		store.update(updatedState);
	};
	if (isHover) ReactDOM.flushSync(changeState);
	else changeState();
}
/**
* Sets up trigger data forwarding to the store.
*
* @param triggerId Id of the trigger.
* @param triggerElementRef Ref for the trigger DOM element.
* @param store The Store instance managing the popup state.
* @param stateUpdates An object with state updates to apply when the trigger is active.
*/
function useTriggerDataForwarding(triggerId, triggerElementRef, store, stateUpdates) {
	const isMountedByThisTrigger = store.useState("isMountedByTrigger", triggerId);
	const baseRegisterTrigger = useTriggerRegistration(triggerId, store);
	const applyTriggerData = useStableCallback((element) => {
		const open = store.select("open");
		const activeTriggerId = store.select("activeTriggerId");
		if (activeTriggerId === triggerId) {
			store.update({
				activeTriggerElement: element,
				...open ? stateUpdates : null
			});
			return;
		}
		if (activeTriggerId == null && open) store.update({
			activeTriggerId: triggerId,
			activeTriggerElement: element,
			...stateUpdates
		});
	});
	const registerTrigger = React$3.useCallback((element) => {
		baseRegisterTrigger(element);
		if (element) applyTriggerData(element);
	}, [baseRegisterTrigger, applyTriggerData]);
	useIsoLayoutEffect(() => {
		if (isMountedByThisTrigger) store.update({
			activeTriggerElement: triggerElementRef.current,
			...stateUpdates
		});
	}, [
		isMountedByThisTrigger,
		store,
		triggerElementRef,
		...Object.values(stateUpdates)
	]);
	return {
		registerTrigger,
		isMountedByThisTrigger
	};
}
/**
* Keeps trigger registration state synchronized while the popup is open.
*
* When a popup opens without an explicit trigger id and exactly one trigger is registered, that
* trigger is claimed as the active trigger. When the active trigger id is still registered but its
* element changed, the active element is refreshed. When the active trigger id is missing from the
* registry but the same element is still registered under a different id (e.g. the rendered trigger
* carries its own DOM `id` that differs from Base UI's internal trigger id), the active id is
* reassociated to the registered id instead of being treated as lost. When the active trigger
* unregisters, the default path preserves existing ownership so non-closing popup families do not
* silently claim a different trigger while staying open.
*
* If `closeOnActiveTriggerUnmount` is enabled, unregistering a previously resolved active trigger
* requests a close after a microtask so a same-tick replacement trigger with the same id can
* register first. An active trigger id that has not matched a registered trigger yet is treated as
* pending and does not request a close.
*
* This should be called on the Root part.
*
* @param store The Store instance managing the popup state.
* @param options Options for active trigger unmount behavior.
*/
function useImplicitActiveTrigger(store, options = {}) {
	const { closeOnActiveTriggerUnmount = false } = options;
	const resolvedActiveTriggerIdRef = React$3.useRef(null);
	const open = store.useState("open");
	useIsoLayoutEffect(() => {
		if (!open) {
			resolvedActiveTriggerIdRef.current = null;
			if (store.state.triggerCount !== 0) store.set("triggerCount", 0);
			return;
		}
		const triggerCount = store.context.triggerElements.size;
		const stateUpdates = {};
		if (store.state.triggerCount !== triggerCount) stateUpdates.triggerCount = triggerCount;
		const currentActiveTriggerId = store.select("activeTriggerId");
		let lostActiveTriggerId = null;
		if (currentActiveTriggerId) {
			const activeTriggerElement = store.context.triggerElements.getById(currentActiveTriggerId);
			if (!activeTriggerElement) {
				for (const [triggerId, triggerElement] of store.context.triggerElements.entries()) if (triggerElement === store.state.activeTriggerElement) {
					stateUpdates.activeTriggerId = triggerId;
					stateUpdates.activeTriggerElement = triggerElement;
					resolvedActiveTriggerIdRef.current = triggerId;
					break;
				}
				if (stateUpdates.activeTriggerId === void 0) if (resolvedActiveTriggerIdRef.current === currentActiveTriggerId) lostActiveTriggerId = currentActiveTriggerId;
				else resolvedActiveTriggerIdRef.current = null;
			} else {
				resolvedActiveTriggerIdRef.current = currentActiveTriggerId;
				if (activeTriggerElement !== store.state.activeTriggerElement) stateUpdates.activeTriggerElement = activeTriggerElement;
			}
		} else resolvedActiveTriggerIdRef.current = null;
		if (!lostActiveTriggerId && !currentActiveTriggerId && triggerCount === 1) {
			const iteratorResult = store.context.triggerElements.entries().next();
			if (!iteratorResult.done) {
				const [implicitTriggerId, implicitTriggerElement] = iteratorResult.value;
				stateUpdates.activeTriggerId = implicitTriggerId;
				stateUpdates.activeTriggerElement = implicitTriggerElement;
				resolvedActiveTriggerIdRef.current = implicitTriggerId;
			}
		}
		if (stateUpdates.triggerCount !== void 0 || stateUpdates.activeTriggerId !== void 0 || stateUpdates.activeTriggerElement !== void 0) store.update(stateUpdates);
		if (lostActiveTriggerId) {
			if (closeOnActiveTriggerUnmount) queueMicrotask(() => {
				if (store.select("open") && store.select("activeTriggerId") === lostActiveTriggerId && !store.context.triggerElements.getById(lostActiveTriggerId)) {
					const eventDetails = createChangeEventDetails(none);
					store.setOpen(false, eventDetails);
					if (!eventDetails.isCanceled) store.update({
						activeTriggerId: null,
						activeTriggerElement: null
					});
				}
			});
		}
	}, [
		open,
		store,
		store.useState("triggerCount"),
		store.useState("activeTriggerId"),
		store.useState("activeTriggerElement"),
		closeOnActiveTriggerUnmount
	]);
}
/**
* Manages the mounted state of the popup.
* Sets up the transition status listeners and handles unmounting when needed.
* Updates the `mounted`, `transitionStatus`, and `preventUnmountingOnClose` states in the store.
*
* @param open Whether the popup is open.
* @param store The Store instance managing the popup state.
* @param onUnmount Optional callback to be called when the popup is unmounted.
*
* @returns A function to forcibly unmount the popup.
*/
function useOpenStateTransitions(open, store, onUnmount) {
	const { mounted, setMounted, transitionStatus } = useTransitionStatus(open);
	const preventUnmountingOnClose = store.useState("preventUnmountingOnClose");
	const syncedPreventUnmountingOnClose = open ? false : preventUnmountingOnClose;
	store.useSyncedValues({
		mounted,
		transitionStatus,
		preventUnmountingOnClose: syncedPreventUnmountingOnClose
	});
	const forceUnmount = useStableCallback(() => {
		setMounted(false);
		store.update({
			activeTriggerId: null,
			activeTriggerElement: null,
			mounted: false,
			preventUnmountingOnClose: false
		});
		onUnmount?.();
		store.context.onOpenChangeComplete?.(false);
	});
	useOpenChangeComplete({
		enabled: mounted && !open && !syncedPreventUnmountingOnClose,
		open,
		ref: store.context.popupRef,
		onComplete() {
			if (!open) forceUnmount();
		}
	});
	return {
		forceUnmount,
		transitionStatus
	};
}
function usePopupInteractionProps(store, statePart) {
	store.useSyncedValues(statePart);
	useIsoLayoutEffect(() => () => {
		store.update({
			activeTriggerProps: EMPTY_OBJECT,
			inactiveTriggerProps: EMPTY_OBJECT,
			popupProps: EMPTY_OBJECT
		});
	}, [store]);
}
function usePopupRootSync(store, open) {
	useIsoLayoutEffect(() => {
		if (!open && store.state.openMethod !== null) store.set("openMethod", null);
	}, [open, store]);
	useIsoLayoutEffect(() => () => {
		if (store.state.openMethod !== null) store.set("openMethod", null);
	}, [store]);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/popups/popupTriggerMap.mjs
/**
* Data structure to keep track of popup trigger elements by their IDs.
*
* Element lookups iterate the id map rather than maintaining a parallel Set. Registration is O(1),
* while `hasElement` and `hasMatchingElement` are linear in the number of triggers.
*/
var PopupTriggerMap = class {
	constructor() {
		this.idMap = /* @__PURE__ */ new Map();
	}
	/**
	* Adds a trigger element with the given ID.
	*
	* Note: The provided element is assumed to not be registered under multiple IDs.
	*/
	add(id, element) {
		this.idMap.set(id, element);
	}
	/**
	* Removes the trigger element with the given ID.
	*/
	delete(id) {
		this.idMap.delete(id);
	}
	/**
	* Whether the given element is registered as a trigger.
	*/
	hasElement(element) {
		for (const registered of this.idMap.values()) if (registered === element) return true;
		return false;
	}
	/**
	* Whether there is a registered trigger element matching the given predicate.
	*/
	hasMatchingElement(predicate) {
		for (const element of this.idMap.values()) if (predicate(element)) return true;
		return false;
	}
	/**
	* Returns the trigger element associated with the given ID, or undefined if no such element exists.
	*/
	getById(id) {
		return this.idMap.get(id);
	}
	/**
	* Returns an iterable of all registered trigger entries, where each entry is a tuple of [id, element].
	*/
	entries() {
		return this.idMap.entries();
	}
	/**
	* Returns an iterable of all registered trigger elements.
	*/
	elements() {
		return this.idMap.values();
	}
	/**
	* Returns the number of registered trigger elements.
	*/
	get size() {
		return this.idMap.size;
	}
};
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/utils/getEmptyRootContext.mjs
function getEmptyRootContext() {
	return new FloatingRootStore({
		open: false,
		transitionStatus: void 0,
		floatingElement: null,
		referenceElement: null,
		triggerElements: new PopupTriggerMap(),
		floatingId: void 0,
		syncOnly: false,
		nested: false,
		onOpenChange: void 0
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/popups/store.mjs
/**
* State common to all popup stores.
*/
function createInitialPopupStoreState() {
	return {
		open: false,
		openProp: void 0,
		mounted: false,
		transitionStatus: void 0,
		floatingRootContext: getEmptyRootContext(),
		floatingId: void 0,
		triggerCount: 0,
		preventUnmountingOnClose: false,
		payload: void 0,
		activeTriggerId: null,
		activeTriggerElement: null,
		triggerIdProp: void 0,
		popupElement: null,
		positionerElement: null,
		activeTriggerProps: EMPTY_OBJECT,
		inactiveTriggerProps: EMPTY_OBJECT,
		popupProps: EMPTY_OBJECT
	};
}
function createPopupFloatingRootContext(triggerElements, floatingId, nested = false) {
	return new FloatingRootStore({
		open: false,
		transitionStatus: void 0,
		floatingElement: null,
		referenceElement: null,
		triggerElements,
		floatingId,
		syncOnly: true,
		nested,
		onOpenChange: void 0
	});
}
var activeTriggerIdSelector = (state) => state.triggerIdProp ?? state.activeTriggerId;
var openSelector = (state) => state.openProp ?? state.open;
var popupIdSelector = (state) => {
	return (state.popupElement?.id ?? state.floatingId) || void 0;
};
function triggerOwnsOpenPopup(state, triggerId) {
	return triggerId !== void 0 && openSelector(state) && activeTriggerIdSelector(state) === triggerId;
}
function triggerOwnsOpenPopupOrIsOnlyTrigger(state, triggerId) {
	if (triggerOwnsOpenPopup(state, triggerId)) return true;
	return triggerId !== void 0 && openSelector(state) && activeTriggerIdSelector(state) == null && state.triggerCount === 1;
}
var popupStoreSelectors = {
	open: openSelector,
	mounted: (state) => state.mounted,
	transitionStatus: (state) => state.transitionStatus,
	floatingRootContext: (state) => state.floatingRootContext,
	triggerCount: (state) => state.triggerCount,
	preventUnmountingOnClose: (state) => state.preventUnmountingOnClose,
	payload: (state) => state.payload,
	activeTriggerId: activeTriggerIdSelector,
	activeTriggerElement: (state) => state.mounted ? state.activeTriggerElement : null,
	popupId: popupIdSelector,
	/**
	* Whether the trigger with the given ID was used to open the popup.
	*/
	isTriggerActive: (state, triggerId) => triggerId !== void 0 && activeTriggerIdSelector(state) === triggerId,
	/**
	* Whether the popup is open and was activated by a trigger with the given ID.
	*/
	isOpenedByTrigger: (state, triggerId) => triggerOwnsOpenPopup(state, triggerId),
	/**
	* Whether the popup is mounted and was activated by a trigger with the given ID.
	*/
	isMountedByTrigger: (state, triggerId) => triggerId !== void 0 && activeTriggerIdSelector(state) === triggerId && state.mounted,
	triggerProps: (state, isActive) => isActive ? state.activeTriggerProps : state.inactiveTriggerProps,
	/**
	* Popup id for the trigger that currently owns the open popup.
	*/
	triggerPopupId: (state, triggerId) => triggerOwnsOpenPopupOrIsOnlyTrigger(state, triggerId) ? popupIdSelector(state) : void 0,
	popupProps: (state) => state.popupProps,
	popupElement: (state) => state.popupElement,
	positionerElement: (state) => state.positionerElement
};
/**
* Store members a detached handle-backed trigger reads or invokes for trigger registration and data
* forwarding. `set`/`update` are included only for trigger-count and trigger-data bookkeeping; on a
* detached (inert) store they are intentionally no-ops, so a write through them is not guaranteed to
* be durable. Component handle-store views Pick these from their concrete store (preserving its
* context and selectors) and add any component-specific trigger-invoked members such as `setOpen`.
*/
/**
* The subset of a popup store that trigger registration and data forwarding rely on. Narrow enough
* that an inert store can be passed while detached.
*/
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/popups/usePopupHandleStore.mjs
/**
* Reads the store currently exposed by a popup handle and subscribes to store-pointer changes.
* Detached triggers use this to follow a handle as a root attaches or detaches: while no root is
* attached, the handle exposes its fallback store; once a root attaches, subscribers re-render and
* read from the live root store.
*
* Returns `undefined` when no handle is provided so callers can fall back to their root context.
*
* @param handle The popup handle to read from, or `undefined` when the trigger is not handle-bound.
*/
function usePopupHandleStore(handle) {
	return (0, import_shim.useSyncExternalStore)(React$3.useCallback((listener) => {
		if (handle === void 0) return NOOP;
		return handle.subscribeStore(listener);
	}, [handle]), React$3.useCallback(() => {
		return handle === void 0 ? void 0 : handle.store;
	}, [handle]), () => handle?.serverStore);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/hooks/useFloatingRootContext.mjs
function useFloatingRootContext(options) {
	const { open = false, onOpenChange, elements = {} } = options;
	const floatingId = useId();
	const nested = useFloatingParentNodeId() != null;
	const store = useRefWithInit(() => new FloatingRootStore({
		open,
		transitionStatus: void 0,
		onOpenChange,
		referenceElement: elements.reference ?? null,
		floatingElement: elements.floating ?? null,
		triggerElements: new PopupTriggerMap(),
		floatingId,
		syncOnly: false,
		nested
	})).current;
	useIsoLayoutEffect(() => {
		const valuesToSync = {
			open,
			floatingId
		};
		if (elements.reference !== void 0) {
			valuesToSync.referenceElement = elements.reference;
			valuesToSync.domReferenceElement = isElement(elements.reference) ? elements.reference : null;
		}
		if (elements.floating !== void 0) valuesToSync.floatingElement = elements.floating;
		store.update(valuesToSync);
	}, [
		open,
		floatingId,
		elements.reference,
		elements.floating,
		store
	]);
	store.context.onOpenChange = onOpenChange;
	store.context.nested = nested;
	return store;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/hooks/useFloating.mjs
/**
* Base UI's private `useFloating` path. The caller must supply the root store, so this skips the
* internal root-context hook used by the public Floating UI-compatible API.
*/
function useBaseUIFloating(options) {
	return useFloatingWithStore(options, options.rootContext);
}
function useFloatingWithStore(options, store) {
	const { nodeId, externalTree } = options;
	const referenceElement = store.useState("referenceElement");
	const floatingElement = store.useState("floatingElement");
	const domReferenceElement = store.useState("domReferenceElement");
	const open = store.useState("open");
	const floatingId = store.useState("floatingId");
	const [positionReference, setPositionReferenceRaw] = React$3.useState(null);
	const [localDomReference, setLocalDomReference] = React$3.useState(void 0);
	const [localFloatingElement, setLocalFloatingElement] = React$3.useState(void 0);
	const domReferenceRef = React$3.useRef(null);
	const tree = useFloatingTree(externalTree);
	const storeElements = React$3.useMemo(() => ({
		reference: referenceElement,
		floating: floatingElement,
		domReference: domReferenceElement
	}), [
		referenceElement,
		floatingElement,
		domReferenceElement
	]);
	const position = useFloating({
		...options,
		elements: {
			...storeElements,
			...positionReference && { reference: positionReference }
		}
	});
	const localDomReferenceElement = isElement(localDomReference) ? localDomReference : null;
	const syncedFloatingElement = localFloatingElement === void 0 ? store.state.floatingElement : localFloatingElement;
	store.useSyncedValue("referenceElement", localDomReference ?? null);
	store.useSyncedValue("domReferenceElement", localDomReference === void 0 ? domReferenceElement : localDomReferenceElement);
	store.useSyncedValue("floatingElement", syncedFloatingElement);
	const setPositionReference = React$3.useCallback((node) => {
		const computedPositionReference = isElement(node) ? {
			getBoundingClientRect: () => node.getBoundingClientRect(),
			getClientRects: () => node.getClientRects(),
			contextElement: node
		} : node;
		setPositionReferenceRaw(computedPositionReference);
		position.refs.setReference(computedPositionReference);
	}, [position.refs]);
	const setReference = React$3.useCallback((node) => {
		if (isElement(node) || node === null) {
			domReferenceRef.current = node;
			setLocalDomReference(node);
		}
		if (isElement(position.refs.reference.current) || position.refs.reference.current === null || node !== null && !isElement(node)) position.refs.setReference(node);
	}, [position.refs, setLocalDomReference]);
	const setFloating = React$3.useCallback((node) => {
		setLocalFloatingElement(node);
		position.refs.setFloating(node);
	}, [position.refs]);
	const refs = React$3.useMemo(() => ({
		...position.refs,
		setReference,
		setFloating,
		setPositionReference,
		domReference: domReferenceRef
	}), [
		position.refs,
		setReference,
		setFloating,
		setPositionReference
	]);
	const elements = React$3.useMemo(() => ({
		...position.elements,
		domReference: domReferenceElement
	}), [position.elements, domReferenceElement]);
	const context = React$3.useMemo(() => ({
		...position,
		dataRef: store.context.dataRef,
		open,
		onOpenChange: store.setOpen,
		events: store.context.events,
		floatingId,
		refs,
		elements,
		nodeId,
		rootStore: store
	}), [
		position,
		refs,
		elements,
		nodeId,
		store,
		open,
		floatingId
	]);
	useIsoLayoutEffect(() => {
		if (domReferenceElement) domReferenceRef.current = domReferenceElement;
	}, [domReferenceElement]);
	useIsoLayoutEffect(() => {
		store.context.dataRef.current.floatingContext = context;
		const node = tree?.nodesRef.current.find((n) => n.id === nodeId);
		if (node) node.context = context;
	});
	return React$3.useMemo(() => ({
		...position,
		context,
		refs,
		elements,
		rootStore: store
	}), [
		position,
		refs,
		elements,
		context,
		store
	]);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/hooks/useFocus.mjs
var isMacSafari = mac && webkit;
/**
* Opens the floating element while the reference element has focus, like CSS
* `:focus`.
* @see https://floating-ui.com/docs/useFocus
*/
function useFocus(context, props = {}) {
	const { enabled = true, delay } = props;
	const store = "rootStore" in context ? context.rootStore : context;
	const { events, dataRef } = store.context;
	const blockFocusRef = React$3.useRef(false);
	const blockedReferenceRef = React$3.useRef(null);
	const keyboardModalityRef = React$3.useRef(true);
	const timeout = useTimeout();
	React$3.useEffect(() => {
		const domReference = store.select("domReferenceElement");
		if (!enabled) return;
		const win = getWindow(domReference);
		function onBlur() {
			const currentDomReference = store.select("domReferenceElement");
			if (!store.select("open") && isHTMLElement(currentDomReference) && currentDomReference === activeElement(ownerDocument(currentDomReference))) blockFocusRef.current = true;
		}
		function onKeyDown() {
			keyboardModalityRef.current = true;
		}
		function onPointerDown() {
			keyboardModalityRef.current = false;
		}
		return mergeCleanups(addEventListener(win, "blur", onBlur), isMacSafari && addEventListener(win, "keydown", onKeyDown, true), isMacSafari && addEventListener(win, "pointerdown", onPointerDown, true));
	}, [store, enabled]);
	React$3.useEffect(() => {
		if (!enabled) return;
		function onOpenChangeLocal(details) {
			if (details.reason === "trigger-press" || details.reason === "escape-key") {
				const referenceElement = store.select("domReferenceElement");
				if (isElement(referenceElement)) {
					blockedReferenceRef.current = referenceElement;
					blockFocusRef.current = true;
				}
			}
		}
		events.on("openchange", onOpenChangeLocal);
		return () => {
			events.off("openchange", onOpenChangeLocal);
		};
	}, [
		events,
		enabled,
		store
	]);
	const reference = React$3.useMemo(() => {
		function resetBlockedFocus() {
			blockFocusRef.current = false;
			blockedReferenceRef.current = null;
		}
		return {
			onMouseLeave() {
				resetBlockedFocus();
			},
			onFocus(event) {
				const focusTarget = event.currentTarget;
				if (blockFocusRef.current) {
					if (blockedReferenceRef.current === focusTarget) return;
					resetBlockedFocus();
				}
				const target = getTarget(event.nativeEvent);
				if (isElement(target)) {
					if (isMacSafari && !event.relatedTarget) {
						if (!keyboardModalityRef.current && !isTypeableElement(target)) return;
					} else if (!matchesFocusVisible(target)) return;
				}
				const movedFromOtherEnabledTrigger = isTargetInsideEnabledTrigger(event.relatedTarget, store.context.triggerElements);
				const { nativeEvent, currentTarget } = event;
				const delayValue = typeof delay === "function" ? delay() : delay;
				if (store.select("open") && movedFromOtherEnabledTrigger || delayValue === 0 || delayValue === void 0) {
					store.setOpen(true, createChangeEventDetails(triggerFocus, nativeEvent, currentTarget));
					return;
				}
				timeout.start(delayValue, () => {
					if (blockFocusRef.current) return;
					store.setOpen(true, createChangeEventDetails(triggerFocus, nativeEvent, currentTarget));
				});
			},
			onBlur(event) {
				resetBlockedFocus();
				const relatedTarget = event.relatedTarget;
				const nativeEvent = event.nativeEvent;
				const movedToFocusGuard = isElement(relatedTarget) && relatedTarget.hasAttribute(createAttribute("focus-guard")) && relatedTarget.getAttribute("data-type") === "outside";
				timeout.start(0, () => {
					const domReference = store.select("domReferenceElement");
					const activeEl = activeElement(ownerDocument(domReference));
					if (!relatedTarget && activeEl === domReference) return;
					if (contains(dataRef.current.floatingContext?.refs.floating.current, activeEl) || contains(domReference, activeEl) || movedToFocusGuard) return;
					if (isTargetInsideEnabledTrigger(relatedTarget ?? activeEl, store.context.triggerElements)) return;
					store.setOpen(false, createChangeEventDetails(triggerFocus, nativeEvent));
				});
			}
		};
	}, [
		dataRef,
		delay,
		store,
		timeout
	]);
	return React$3.useMemo(() => enabled ? {
		reference,
		trigger: reference
	} : {}, [enabled, reference]);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/hooks/useHoverInteractionSharedState.mjs
var HoverInteraction = class HoverInteraction {
	constructor() {
		this.pointerType = void 0;
		this.interactedInside = false;
		this.handler = void 0;
		this.blockMouseMove = true;
		this.performedPointerEventsMutation = false;
		this.pointerEventsScopeElement = null;
		this.pointerEventsReferenceElement = null;
		this.pointerEventsFloatingElement = null;
		this.restTimeoutPending = false;
		this.openChangeTimeout = new Timeout();
		this.restTimeout = new Timeout();
		this.handleCloseOptions = void 0;
	}
	static create() {
		return new HoverInteraction();
	}
	dispose = () => {
		this.openChangeTimeout.clear();
		this.restTimeout.clear();
	};
	disposeEffect = () => {
		return this.dispose;
	};
};
var pointerEventsMutationOwnerByScopeElement = /* @__PURE__ */ new WeakMap();
function clearSafePolygonPointerEventsMutation(instance) {
	if (!instance.performedPointerEventsMutation) return;
	const scopeElement = instance.pointerEventsScopeElement;
	if (scopeElement && pointerEventsMutationOwnerByScopeElement.get(scopeElement) === instance) {
		instance.pointerEventsScopeElement?.style.removeProperty("pointer-events");
		instance.pointerEventsReferenceElement?.style.removeProperty("pointer-events");
		instance.pointerEventsFloatingElement?.style.removeProperty("pointer-events");
		pointerEventsMutationOwnerByScopeElement.delete(scopeElement);
	}
	instance.performedPointerEventsMutation = false;
	instance.pointerEventsScopeElement = null;
	instance.pointerEventsReferenceElement = null;
	instance.pointerEventsFloatingElement = null;
}
function applySafePolygonPointerEventsMutation(instance, options) {
	const { scopeElement, referenceElement, floatingElement } = options;
	const existingOwner = pointerEventsMutationOwnerByScopeElement.get(scopeElement);
	if (existingOwner && existingOwner !== instance) clearSafePolygonPointerEventsMutation(existingOwner);
	clearSafePolygonPointerEventsMutation(instance);
	instance.performedPointerEventsMutation = true;
	instance.pointerEventsScopeElement = scopeElement;
	instance.pointerEventsReferenceElement = referenceElement;
	instance.pointerEventsFloatingElement = floatingElement;
	pointerEventsMutationOwnerByScopeElement.set(scopeElement, instance);
	scopeElement.style.pointerEvents = "none";
	referenceElement.style.pointerEvents = "auto";
	floatingElement.style.pointerEvents = "auto";
}
function useHoverInteractionSharedState(store) {
	const data = store.context.dataRef.current;
	const instance = useRefWithInit(() => data.hoverInteractionState ?? HoverInteraction.create()).current;
	if (!data.hoverInteractionState) data.hoverInteractionState = instance;
	useOnMount(data.hoverInteractionState.disposeEffect);
	return data.hoverInteractionState;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/hooks/useHoverFloatingInteraction.mjs
/**
* Provides hover interactions that should be attached to the floating element.
*/
function useHoverFloatingInteraction(context, parameters = {}) {
	const { enabled = true, closeDelay: closeDelayProp = 0, nodeId: nodeIdProp } = parameters;
	const store = "rootStore" in context ? context.rootStore : context;
	const open = store.useState("open");
	const floatingElement = store.useState("floatingElement");
	const domReferenceElement = store.useState("domReferenceElement");
	const { dataRef } = store.context;
	const tree = useFloatingTree();
	const parentId = useFloatingParentNodeId();
	const instance = useHoverInteractionSharedState(store);
	const childClosedTimeout = useTimeout();
	const isClickLikeOpenEvent$2 = useStableCallback(() => {
		return isClickLikeOpenEvent(dataRef.current.openEvent?.type, instance.interactedInside);
	});
	const isHoverOpen = useStableCallback(() => {
		return isHoverOpenEvent(dataRef.current.openEvent?.type);
	});
	const clearPointerEvents = useStableCallback(() => {
		clearSafePolygonPointerEventsMutation(instance);
	});
	useIsoLayoutEffect(() => {
		if (!open) {
			instance.pointerType = void 0;
			instance.restTimeoutPending = false;
			instance.interactedInside = false;
			clearPointerEvents();
		}
	}, [
		open,
		instance,
		clearPointerEvents
	]);
	React$3.useEffect(() => {
		return clearPointerEvents;
	}, [clearPointerEvents]);
	useIsoLayoutEffect(() => {
		if (!enabled) return;
		if (open && instance.handleCloseOptions?.blockPointerEvents && isHoverOpen() && isElement(domReferenceElement) && floatingElement) {
			const ref = domReferenceElement;
			const floatingEl = floatingElement;
			const doc = ownerDocument(floatingElement);
			const parentFloating = tree?.nodesRef.current.find((node) => node.id === parentId)?.context?.elements.floating;
			if (parentFloating) parentFloating.style.pointerEvents = "";
			const cachedScopeElement = instance.pointerEventsScopeElement !== floatingEl ? instance.pointerEventsScopeElement : null;
			const parentScopeElement = parentFloating !== floatingEl ? parentFloating : null;
			applySafePolygonPointerEventsMutation(instance, {
				scopeElement: instance.handleCloseOptions?.getScope?.() ?? cachedScopeElement ?? parentScopeElement ?? ref.closest("[data-rootownerid]") ?? doc.body,
				referenceElement: ref,
				floatingElement: floatingEl
			});
			return () => {
				clearPointerEvents();
			};
		}
	}, [
		enabled,
		open,
		domReferenceElement,
		floatingElement,
		instance,
		isHoverOpen,
		tree,
		parentId,
		clearPointerEvents
	]);
	React$3.useEffect(() => {
		if (!enabled) return;
		function hasParentChildren() {
			return !!(tree && parentId && getNodeChildren(tree.nodesRef.current, parentId).length > 0);
		}
		function closeWithDelay(event) {
			const closeDelay = getDelay(closeDelayProp, "close", instance.pointerType);
			const close = () => {
				store.setOpen(false, createChangeEventDetails(triggerHover, event));
				tree?.events.emit("floating.closed", event);
			};
			if (closeDelay) instance.openChangeTimeout.start(closeDelay, close);
			else {
				instance.openChangeTimeout.clear();
				close();
			}
		}
		function handleInteractInside(event) {
			const target = getTarget(event);
			if (!isInteractiveElement(target)) {
				instance.interactedInside = false;
				return;
			}
			instance.interactedInside = target?.closest("[aria-haspopup]") != null;
		}
		function onFloatingMouseEnter() {
			instance.openChangeTimeout.clear();
			childClosedTimeout.clear();
			tree?.events.off("floating.closed", onNodeClosed);
			clearPointerEvents();
		}
		function onFloatingMouseLeave(event) {
			if (hasParentChildren() && tree) {
				tree.events.on("floating.closed", onNodeClosed);
				return;
			}
			if (isTargetInsideEnabledTrigger(event.relatedTarget, store.context.triggerElements)) return;
			const currentNodeId = dataRef.current.floatingContext?.nodeId ?? nodeIdProp;
			const relatedTarget = event.relatedTarget;
			if (tree && currentNodeId && isElement(relatedTarget) && getNodeChildren(tree.nodesRef.current, currentNodeId, false).some((node) => contains(node.context?.elements.floating, relatedTarget))) return;
			if (instance.handler) {
				instance.handler(event);
				return;
			}
			clearPointerEvents();
			if (isHoverOpen() && !isClickLikeOpenEvent$2()) closeWithDelay(event);
		}
		function onNodeClosed(event) {
			if (!tree || !parentId || hasParentChildren()) return;
			childClosedTimeout.start(0, () => {
				tree.events.off("floating.closed", onNodeClosed);
				store.setOpen(false, createChangeEventDetails(triggerHover, event));
				tree.events.emit("floating.closed", event);
			});
		}
		const floating = floatingElement;
		return mergeCleanups(floating && addEventListener(floating, "mouseenter", onFloatingMouseEnter), floating && addEventListener(floating, "mouseleave", onFloatingMouseLeave), floating && addEventListener(floating, "pointerdown", handleInteractInside, true), () => {
			tree?.events.off("floating.closed", onNodeClosed);
		});
	}, [
		enabled,
		floatingElement,
		store,
		dataRef,
		closeDelayProp,
		nodeIdProp,
		isHoverOpen,
		isClickLikeOpenEvent$2,
		clearPointerEvents,
		instance,
		tree,
		parentId,
		childClosedTimeout
	]);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/hooks/useHoverReferenceInteraction.mjs
var EMPTY_REF = { current: null };
/**
* Provides hover interactions that should be attached to reference or trigger
* elements.
*/
function useHoverReferenceInteraction(context, props = {}) {
	const { enabled = true, delay = 0, handleClose = null, mouseOnly = false, restMs = 0, move = true, triggerElementRef = EMPTY_REF, externalTree, isActiveTrigger = true, getHandleCloseContext, isClosing, shouldOpen: shouldOpenProp, guardStaleOpen = false } = props;
	const store = "rootStore" in context ? context.rootStore : context;
	const { dataRef, events } = store.context;
	const tree = useFloatingTree(externalTree);
	const instance = useHoverInteractionSharedState(store);
	const isHoverCloseActiveRef = React$3.useRef(false);
	const handleCloseRef = useValueAsRef(handleClose);
	const delayRef = useValueAsRef(delay);
	const restMsRef = useValueAsRef(restMs);
	const enabledRef = useValueAsRef(enabled);
	const shouldOpenRef = useValueAsRef(shouldOpenProp);
	const isClosingRef = useValueAsRef(isClosing);
	const isClickLikeOpenEvent$1 = useStableCallback(() => {
		return isClickLikeOpenEvent(dataRef.current.openEvent?.type, instance.interactedInside);
	});
	const checkShouldOpen = useStableCallback(() => {
		return shouldOpenRef.current?.() !== false;
	});
	const isOverInactiveTrigger = useStableCallback((currentDomReference, currentTarget, target) => {
		const allTriggers = store.context.triggerElements;
		if (allTriggers.hasElement(currentTarget)) return !currentDomReference || !contains(currentDomReference, currentTarget);
		if (!isElement(target)) return false;
		const targetElement = target;
		return allTriggers.hasMatchingElement((trigger) => contains(trigger, targetElement)) && (!currentDomReference || !contains(currentDomReference, targetElement));
	});
	const cleanupMouseMoveHandler = useStableCallback(() => {
		if (!instance.handler) return;
		ownerDocument(store.select("domReferenceElement")).removeEventListener("mousemove", instance.handler);
		instance.handler = void 0;
	});
	const clearPointerEvents = useStableCallback(() => {
		clearSafePolygonPointerEventsMutation(instance);
	});
	if (isActiveTrigger) instance.handleCloseOptions = handleCloseRef.current?.__options;
	React$3.useEffect(() => cleanupMouseMoveHandler, [cleanupMouseMoveHandler]);
	React$3.useEffect(() => {
		if (!enabled) return;
		function onOpenChangeLocal(details) {
			if (!details.open) {
				isHoverCloseActiveRef.current = details.reason === triggerHover;
				cleanupMouseMoveHandler();
				instance.openChangeTimeout.clear();
				instance.restTimeout.clear();
				instance.blockMouseMove = true;
				instance.restTimeoutPending = false;
			} else isHoverCloseActiveRef.current = false;
		}
		events.on("openchange", onOpenChangeLocal);
		return () => {
			events.off("openchange", onOpenChangeLocal);
		};
	}, [
		enabled,
		events,
		instance,
		cleanupMouseMoveHandler
	]);
	React$3.useEffect(() => {
		if (!enabled) return;
		function closeWithDelay(event, runElseBranch = true) {
			const closeDelay = getDelay(delayRef.current, "close", instance.pointerType);
			if (closeDelay) instance.openChangeTimeout.start(closeDelay, () => {
				store.setOpen(false, createChangeEventDetails(triggerHover, event));
				tree?.events.emit("floating.closed", event);
			});
			else if (runElseBranch) {
				instance.openChangeTimeout.clear();
				store.setOpen(false, createChangeEventDetails(triggerHover, event));
				tree?.events.emit("floating.closed", event);
			}
		}
		const trigger = triggerElementRef.current ?? (isActiveTrigger ? store.select("domReferenceElement") : null);
		if (!isElement(trigger)) return;
		function onMouseEnter(event) {
			instance.openChangeTimeout.clear();
			instance.blockMouseMove = false;
			if (mouseOnly && !isMouseLikePointerType(instance.pointerType)) return;
			const restMsValue = getRestMs(restMsRef.current);
			const openDelay = getDelay(delayRef.current, "open", instance.pointerType);
			const eventTarget = getTarget(event);
			const currentTarget = event.currentTarget ?? null;
			const currentDomReference = store.select("domReferenceElement");
			let triggerNode = currentTarget;
			if (isElement(eventTarget) && !store.context.triggerElements.hasElement(eventTarget)) {
				for (const triggerElement of store.context.triggerElements.elements()) if (contains(triggerElement, eventTarget)) {
					triggerNode = triggerElement;
					break;
				}
			}
			if (isElement(currentTarget) && isElement(currentDomReference) && !store.context.triggerElements.hasElement(currentTarget) && contains(currentTarget, currentDomReference)) triggerNode = currentDomReference;
			const isOverInactive = triggerNode == null ? false : isOverInactiveTrigger(currentDomReference, triggerNode, eventTarget);
			const isOpen = store.select("open");
			const isInClosingTransition = isClosingRef.current?.() ?? store.select("transitionStatus") === "ending";
			const isHoverCloseTransition = !isOpen && isInClosingTransition && isHoverCloseActiveRef.current;
			const isReenteringSameTriggerDuringCloseTransition = !isOverInactive && isElement(triggerNode) && isElement(currentDomReference) && contains(currentDomReference, triggerNode) && isHoverCloseTransition;
			const isRestOnlyDelay = restMsValue > 0 && !openDelay;
			const shouldOpenImmediately = isOverInactive && (isOpen || isHoverCloseTransition) || isReenteringSameTriggerDuringCloseTransition;
			const shouldOpen = !isOpen || isOverInactive;
			if (shouldOpenImmediately) {
				if (checkShouldOpen()) store.setOpen(true, createChangeEventDetails(triggerHover, event, triggerNode));
				return;
			}
			if (isRestOnlyDelay) return;
			if (openDelay) instance.openChangeTimeout.start(openDelay, () => {
				if (shouldOpen && checkShouldOpen()) store.setOpen(true, createChangeEventDetails(triggerHover, event, triggerNode));
			});
			else if (shouldOpen) {
				if (checkShouldOpen()) store.setOpen(true, createChangeEventDetails(triggerHover, event, triggerNode));
			}
		}
		function onMouseLeave(event) {
			if (isClickLikeOpenEvent$1()) {
				clearPointerEvents();
				return;
			}
			cleanupMouseMoveHandler();
			const doc = ownerDocument(store.select("domReferenceElement"));
			instance.restTimeout.clear();
			instance.restTimeoutPending = false;
			const handleCloseContextBase = dataRef.current.floatingContext ?? getHandleCloseContext?.();
			if (isTargetInsideEnabledTrigger(event.relatedTarget, store.context.triggerElements)) return;
			if (handleCloseRef.current && handleCloseContextBase) {
				if (!store.select("open")) instance.openChangeTimeout.clear();
				const currentTrigger = triggerElementRef.current;
				instance.handler = handleCloseRef.current({
					...handleCloseContextBase,
					tree,
					x: event.clientX,
					y: event.clientY,
					onClose() {
						clearPointerEvents();
						cleanupMouseMoveHandler();
						if (enabledRef.current && !isClickLikeOpenEvent$1() && currentTrigger === store.select("domReferenceElement")) closeWithDelay(event, true);
					}
				});
				doc.addEventListener("mousemove", instance.handler);
				instance.handler(event);
				return;
			}
			if (instance.pointerType === "touch" ? !contains(store.select("floatingElement"), event.relatedTarget) : true) closeWithDelay(event);
		}
		function onMouseOut(event) {
			if (contains(trigger, event.relatedTarget)) return;
			instance.openChangeTimeout.clear();
			instance.restTimeout.clear();
			instance.restTimeoutPending = false;
		}
		const staleOpenGuard = guardStaleOpen ? addEventListener(trigger, "mouseout", onMouseOut) : void 0;
		if (move) return mergeCleanups(addEventListener(trigger, "mousemove", onMouseEnter, { once: true }), addEventListener(trigger, "mouseenter", onMouseEnter), addEventListener(trigger, "mouseleave", onMouseLeave), staleOpenGuard);
		return mergeCleanups(addEventListener(trigger, "mouseenter", onMouseEnter), addEventListener(trigger, "mouseleave", onMouseLeave), staleOpenGuard);
	}, [
		cleanupMouseMoveHandler,
		clearPointerEvents,
		dataRef,
		delayRef,
		store,
		enabled,
		handleCloseRef,
		instance,
		isActiveTrigger,
		isOverInactiveTrigger,
		isClickLikeOpenEvent$1,
		mouseOnly,
		move,
		restMsRef,
		triggerElementRef,
		tree,
		enabledRef,
		getHandleCloseContext,
		isClosingRef,
		checkShouldOpen,
		guardStaleOpen
	]);
	return React$3.useMemo(() => {
		if (!enabled) return;
		function setPointerRef(event) {
			instance.pointerType = event.pointerType;
		}
		return {
			onPointerDown: setPointerRef,
			onPointerEnter: setPointerRef,
			onMouseMove(event) {
				const { nativeEvent } = event;
				const trigger = event.currentTarget;
				const currentDomReference = store.select("domReferenceElement");
				const currentOpen = store.select("open");
				const isOverInactive = isOverInactiveTrigger(currentDomReference, trigger, event.target);
				if (mouseOnly && !isMouseLikePointerType(instance.pointerType)) return;
				if (currentOpen && isOverInactive && instance.handleCloseOptions?.blockPointerEvents) {
					const floatingElement = store.select("floatingElement");
					if (floatingElement) applySafePolygonPointerEventsMutation(instance, {
						scopeElement: instance.handleCloseOptions?.getScope?.() ?? trigger.ownerDocument.body,
						referenceElement: trigger,
						floatingElement
					});
				}
				const restMsValue = getRestMs(restMsRef.current);
				if (currentOpen && !isOverInactive || restMsValue === 0) return;
				if (!isOverInactive && instance.restTimeoutPending && event.movementX ** 2 + event.movementY ** 2 < 2) return;
				instance.restTimeout.clear();
				function handleMouseMove() {
					instance.restTimeoutPending = false;
					if (isClickLikeOpenEvent$1()) return;
					const latestOpen = store.select("open");
					if (!instance.blockMouseMove && (!latestOpen || isOverInactive) && checkShouldOpen()) store.setOpen(true, createChangeEventDetails(triggerHover, nativeEvent, trigger));
				}
				if (instance.pointerType === "touch") ReactDOM.flushSync(() => {
					handleMouseMove();
				});
				else if (isOverInactive && currentOpen) handleMouseMove();
				else {
					instance.restTimeoutPending = true;
					instance.restTimeout.start(restMsValue, handleMouseMove);
				}
			}
		};
	}, [
		enabled,
		instance,
		isClickLikeOpenEvent$1,
		isOverInactiveTrigger,
		mouseOnly,
		store,
		restMsRef,
		checkShouldOpen
	]);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/hooks/useListNavigation.mjs
var ESCAPE = "Escape";
function isStationaryWebKitPointer(event) {
	return webkit && event.movementX === 0 && event.movementY === 0;
}
function doSwitch(orientation, vertical, horizontal) {
	switch (orientation) {
		case "vertical": return vertical;
		case "horizontal": return horizontal;
		default: return vertical || horizontal;
	}
}
function isMainOrientationKey(key, orientation) {
	return doSwitch(orientation, key === "ArrowUp" || key === "ArrowDown", key === "ArrowLeft" || key === "ArrowRight");
}
function isMainOrientationToEndKey(key, orientation, rtl) {
	return doSwitch(orientation, key === "ArrowDown", rtl ? key === "ArrowLeft" : key === "ArrowRight") || key === "Enter" || key === " " || key === "";
}
function isCrossOrientationOpenKey(key, orientation, rtl) {
	return doSwitch(orientation, rtl ? key === ARROW_LEFT$1 : key === ARROW_RIGHT$1, key === ARROW_DOWN$1);
}
function isCrossOrientationCloseKey(key, orientation, rtl, grid) {
	const vertical = rtl ? key === ARROW_RIGHT$1 : key === ARROW_LEFT$1;
	const horizontal = key === ARROW_UP$1;
	if (orientation === "both" || orientation === "horizontal" && grid) return key === ESCAPE;
	return doSwitch(orientation, vertical, horizontal);
}
/**
* Adds arrow key-based navigation of a list of items, either using real DOM
* focus or virtual focus.
* @see https://floating-ui.com/docs/useListNavigation
*/
function useListNavigation(context, props) {
	const { listRef, activeIndex, onNavigate: onNavigateProp = () => {}, enabled = true, selectedIndex = null, allowEscape = false, loopFocus = false, nested = false, rtl = false, virtual = false, focusItemOnOpen = "auto", focusItemOnHover = true, openOnArrowKeyDown = true, disabledIndices = void 0, orientation = "vertical", parentOrientation, id, resetOnPointerLeave = true, externalTree, grid: navigateGrid } = props;
	const isGrid = navigateGrid != null;
	const store = "rootStore" in context ? context.rootStore : context;
	const open = store.useState("open");
	const floatingElement = store.useState("floatingElement");
	const domReferenceElement = store.useState("domReferenceElement");
	const dataRef = store.context.dataRef;
	const floatingFocusElement = getFloatingFocusElement(floatingElement);
	const typeableComboboxReference = isTypeableCombobox(domReferenceElement);
	const floatingFocusElementRef = useValueAsRef(floatingFocusElement);
	const parentId = useFloatingParentNodeId();
	const tree = useFloatingTree(externalTree);
	const focusItemOnOpenRef = React$3.useRef(focusItemOnOpen);
	const indexRef = React$3.useRef(selectedIndex ?? -1);
	const keyRef = React$3.useRef(null);
	const isPointerModalityRef = React$3.useRef(true);
	const onNavigate = useStableCallback((event) => {
		onNavigateProp(indexRef.current === -1 ? null : indexRef.current, event);
	});
	const previousMountedRef = React$3.useRef(!!floatingElement);
	const previousOpenRef = React$3.useRef(open);
	const forceSyncFocusRef = React$3.useRef(false);
	const forceScrollIntoViewRef = React$3.useRef(false);
	const cancelQueuedFocusRef = React$3.useRef(null);
	const disabledIndicesRef = useValueAsRef(disabledIndices);
	const latestOpenRef = useValueAsRef(open);
	const selectedIndexRef = useValueAsRef(selectedIndex);
	const resetOnPointerLeaveRef = useValueAsRef(resetOnPointerLeave);
	const focusFrame = useAnimationFrame();
	const waitForListPopulatedFrame = useAnimationFrame();
	const focusItem = useStableCallback(() => {
		function runFocus(item) {
			if (virtual) tree?.events.emit("virtualfocus", item);
			else cancelQueuedFocusRef.current = enqueueFocus(item, {
				sync: forceSyncFocusRef.current,
				preventScroll: true
			});
		}
		const initialItem = listRef.current[indexRef.current];
		const forceScrollIntoView = forceScrollIntoViewRef.current;
		if (initialItem) runFocus(initialItem);
		(forceSyncFocusRef.current ? (callback) => callback() : (callback) => focusFrame.request(callback))(() => {
			const waitedItem = listRef.current[indexRef.current] || initialItem;
			if (!waitedItem) return;
			if (!initialItem) runFocus(waitedItem);
			if (item && (forceScrollIntoView || !isPointerModalityRef.current)) waitedItem.scrollIntoView?.({
				block: "nearest",
				inline: "nearest"
			});
		});
	});
	useIsoLayoutEffect(() => {
		dataRef.current.orientation = orientation;
	}, [dataRef, orientation]);
	useIsoLayoutEffect(() => {
		if (!enabled) return;
		if (open && floatingElement) {
			indexRef.current = selectedIndex ?? -1;
			if (focusItemOnOpenRef.current && selectedIndex != null) {
				forceScrollIntoViewRef.current = true;
				onNavigate();
			}
		} else if (previousMountedRef.current) {
			indexRef.current = -1;
			onNavigate();
		}
	}, [
		enabled,
		open,
		floatingElement,
		selectedIndex,
		onNavigate
	]);
	useIsoLayoutEffect(() => {
		if (!enabled) return;
		if (!open) {
			forceSyncFocusRef.current = false;
			return;
		}
		if (!floatingElement) return;
		if (activeIndex == null) {
			forceSyncFocusRef.current = false;
			if (selectedIndexRef.current != null) return;
			if (previousMountedRef.current) {
				indexRef.current = -1;
				focusItem();
			}
			if ((!previousOpenRef.current || !previousMountedRef.current) && focusItemOnOpenRef.current && (keyRef.current != null || focusItemOnOpenRef.current === true && keyRef.current == null)) {
				let runs = 0;
				const waitForListPopulated = () => {
					if (listRef.current[0] == null) {
						if (runs < 2) (runs ? (callback) => waitForListPopulatedFrame.request(callback) : queueMicrotask)(waitForListPopulated);
						runs += 1;
					} else {
						indexRef.current = keyRef.current == null || isMainOrientationToEndKey(keyRef.current, orientation, rtl) || nested ? getMinListIndex(listRef) : getMaxListIndex(listRef);
						keyRef.current = null;
						onNavigate();
					}
				};
				waitForListPopulated();
			}
		} else if (!isIndexOutOfListBounds(listRef.current, activeIndex)) {
			indexRef.current = activeIndex;
			focusItem();
			forceScrollIntoViewRef.current = false;
		}
	}, [
		enabled,
		open,
		floatingElement,
		activeIndex,
		selectedIndexRef,
		nested,
		listRef,
		orientation,
		rtl,
		onNavigate,
		focusItem,
		waitForListPopulatedFrame
	]);
	useIsoLayoutEffect(() => {
		if (!enabled || floatingElement || !tree || virtual || !previousMountedRef.current) return;
		const nodes = tree.nodesRef.current;
		const parent = nodes.find((node) => node.id === parentId)?.context?.elements.floating;
		const activeEl = activeElement(ownerDocument(domReferenceElement ?? parent ?? null));
		const treeContainsActiveEl = nodes.some((node) => node.context && contains(node.context.elements.floating, activeEl));
		if (parent && !treeContainsActiveEl && isPointerModalityRef.current) parent.focus({ preventScroll: true });
	}, [
		enabled,
		floatingElement,
		domReferenceElement,
		tree,
		parentId,
		virtual
	]);
	useIsoLayoutEffect(() => {
		previousOpenRef.current = open;
		previousMountedRef.current = !!floatingElement;
	});
	useIsoLayoutEffect(() => {
		if (!open) {
			keyRef.current = null;
			focusItemOnOpenRef.current = focusItemOnOpen;
		}
	}, [open, focusItemOnOpen]);
	const hasActiveIndex = activeIndex != null;
	const syncCurrentTarget = useStableCallback((event) => {
		if (!latestOpenRef.current) return;
		const index = listRef.current.indexOf(event.currentTarget);
		if (index !== -1 && (indexRef.current !== index || activeIndex !== index)) {
			indexRef.current = index;
			onNavigate(event);
		}
	});
	const getParentOrientation = useStableCallback(() => {
		return parentOrientation ?? tree?.nodesRef.current.find((node) => node.id === parentId)?.context?.dataRef?.current.orientation;
	});
	const getMinEnabledIndex = useStableCallback(() => {
		return getMinListIndex(listRef, disabledIndicesRef.current);
	});
	const commonOnKeyDown = useStableCallback((event) => {
		isPointerModalityRef.current = false;
		forceSyncFocusRef.current = true;
		if (event.which === 229) return;
		if (!latestOpenRef.current && event.currentTarget === floatingFocusElementRef.current) return;
		if (nested && isCrossOrientationCloseKey(event.key, orientation, rtl, isGrid)) {
			if (!isMainOrientationKey(event.key, getParentOrientation())) stopEvent(event);
			store.setOpen(false, createChangeEventDetails(listNavigation, event.nativeEvent));
			if (isHTMLElement(domReferenceElement)) if (virtual) tree?.events.emit("virtualfocus", domReferenceElement);
			else domReferenceElement.focus();
			return;
		}
		const currentIndex = indexRef.current;
		const minIndex = getMinListIndex(listRef, disabledIndices);
		const maxIndex = getMaxListIndex(listRef, disabledIndices);
		if (!typeableComboboxReference) {
			if (event.key === "Home") {
				stopEvent(event);
				indexRef.current = minIndex;
				onNavigate(event);
			}
			if (event.key === "End") {
				stopEvent(event);
				indexRef.current = maxIndex;
				onNavigate(event);
			}
		}
		if (navigateGrid != null) {
			const index = navigateGrid(event, indexRef.current, listRef, orientation, loopFocus, rtl, disabledIndices, minIndex, maxIndex);
			if (index != null) {
				indexRef.current = index;
				onNavigate(event);
			}
			if (orientation === "both") return;
		}
		if (isMainOrientationKey(event.key, orientation)) {
			stopEvent(event);
			if (open && !virtual && activeElement(event.currentTarget.ownerDocument) === event.currentTarget) {
				indexRef.current = isMainOrientationToEndKey(event.key, orientation, rtl) ? minIndex : maxIndex;
				onNavigate(event);
				return;
			}
			if (isMainOrientationToEndKey(event.key, orientation, rtl)) if (loopFocus) if (currentIndex >= maxIndex) if (allowEscape && currentIndex !== listRef.current.length) indexRef.current = -1;
			else {
				forceSyncFocusRef.current = false;
				indexRef.current = minIndex;
			}
			else indexRef.current = findNonDisabledListIndex(listRef.current, {
				startingIndex: currentIndex,
				disabledIndices
			});
			else indexRef.current = Math.min(maxIndex, findNonDisabledListIndex(listRef.current, {
				startingIndex: currentIndex,
				disabledIndices
			}));
			else if (loopFocus) if (currentIndex <= minIndex) if (allowEscape && currentIndex !== -1) indexRef.current = listRef.current.length;
			else {
				forceSyncFocusRef.current = false;
				indexRef.current = maxIndex;
			}
			else indexRef.current = findNonDisabledListIndex(listRef.current, {
				startingIndex: currentIndex,
				decrement: true,
				disabledIndices
			});
			else indexRef.current = Math.max(minIndex, findNonDisabledListIndex(listRef.current, {
				startingIndex: currentIndex,
				decrement: true,
				disabledIndices
			}));
			if (isIndexOutOfListBounds(listRef.current, indexRef.current)) indexRef.current = -1;
			onNavigate(event);
		}
	});
	const item = React$3.useMemo(() => {
		return {
			onFocus(event) {
				forceSyncFocusRef.current = true;
				syncCurrentTarget(event);
			},
			onClick: ({ currentTarget }) => currentTarget.focus({ preventScroll: true }),
			onMouseMove(event) {
				if (isStationaryWebKitPointer(event)) return;
				forceSyncFocusRef.current = true;
				forceScrollIntoViewRef.current = false;
				if (focusItemOnHover) syncCurrentTarget(event);
			},
			onPointerLeave(event) {
				if (!latestOpenRef.current || !isPointerModalityRef.current || event.pointerType === "touch") return;
				forceSyncFocusRef.current = true;
				const relatedTarget = event.relatedTarget;
				if (!focusItemOnHover || listRef.current.includes(relatedTarget)) return;
				if (!resetOnPointerLeaveRef.current) return;
				cancelQueuedFocusRef.current?.();
				cancelQueuedFocusRef.current = null;
				indexRef.current = -1;
				onNavigate(event);
				if (!virtual) {
					const floatingFocusEl = floatingFocusElementRef.current;
					const activeEl = activeElement(ownerDocument(floatingFocusEl));
					if (floatingFocusEl && contains(floatingFocusEl, activeEl)) floatingFocusEl.focus({ preventScroll: true });
				}
			}
		};
	}, [
		syncCurrentTarget,
		latestOpenRef,
		floatingFocusElementRef,
		focusItemOnHover,
		listRef,
		onNavigate,
		resetOnPointerLeaveRef,
		virtual
	]);
	const ariaActiveDescendantProp = React$3.useMemo(() => {
		return virtual && open && hasActiveIndex && { "aria-activedescendant": `${id}-${activeIndex}` };
	}, [
		virtual,
		open,
		hasActiveIndex,
		id,
		activeIndex
	]);
	const floating = React$3.useMemo(() => {
		return {
			"aria-orientation": orientation === "both" ? void 0 : orientation,
			...!typeableComboboxReference ? ariaActiveDescendantProp : {},
			onKeyDown(event) {
				if (event.key === "Tab" && event.shiftKey && open && !virtual) {
					const target = getTarget(event.nativeEvent);
					if (target && !contains(floatingFocusElementRef.current, target)) return;
					stopEvent(event);
					store.setOpen(false, createChangeEventDetails(focusOut, event.nativeEvent));
					if (isHTMLElement(domReferenceElement)) domReferenceElement.focus();
					return;
				}
				commonOnKeyDown(event);
			},
			onPointerMove(event) {
				if (isStationaryWebKitPointer(event)) return;
				isPointerModalityRef.current = true;
			}
		};
	}, [
		ariaActiveDescendantProp,
		commonOnKeyDown,
		floatingFocusElementRef,
		orientation,
		typeableComboboxReference,
		store,
		open,
		virtual,
		domReferenceElement
	]);
	const trigger = React$3.useMemo(() => {
		function openOnNavigationKeyDown(event) {
			store.setOpen(true, createChangeEventDetails(listNavigation, event.nativeEvent, event.currentTarget));
		}
		function checkVirtualMouse(event) {
			if (focusItemOnOpen === "auto" && isVirtualClick(event.nativeEvent)) focusItemOnOpenRef.current = !virtual;
		}
		function checkVirtualPointer(event) {
			focusItemOnOpenRef.current = focusItemOnOpen;
			if (focusItemOnOpen === "auto" && isVirtualPointerEvent(event.nativeEvent)) focusItemOnOpenRef.current = true;
		}
		return {
			onKeyDown(event) {
				const currentOpen = store.select("open");
				isPointerModalityRef.current = false;
				const isArrowKey = event.key.startsWith("Arrow");
				const isParentCrossOpenKey = isCrossOrientationOpenKey(event.key, getParentOrientation(), rtl);
				const isMainKey = isMainOrientationKey(event.key, orientation);
				const isNavigationKey = (nested ? isParentCrossOpenKey : isMainKey) || event.key === "Enter" || event.key.trim() === "";
				if (virtual && currentOpen) return commonOnKeyDown(event);
				if (!currentOpen && !openOnArrowKeyDown && isArrowKey) return;
				if (isNavigationKey) {
					const isParentMainKey = isMainOrientationKey(event.key, getParentOrientation());
					keyRef.current = nested && isParentMainKey ? null : event.key;
				}
				if (nested) {
					if (isParentCrossOpenKey) {
						stopEvent(event);
						if (currentOpen) {
							indexRef.current = getMinEnabledIndex();
							onNavigate(event);
						} else openOnNavigationKeyDown(event);
					}
					return;
				}
				if (isMainKey) {
					if (selectedIndexRef.current != null) indexRef.current = selectedIndexRef.current;
					stopEvent(event);
					if (!currentOpen && openOnArrowKeyDown) openOnNavigationKeyDown(event);
					else commonOnKeyDown(event);
					if (currentOpen) onNavigate(event);
				}
			},
			onFocus(event) {
				if (store.select("open") && !virtual) {
					indexRef.current = -1;
					onNavigate(event);
				}
			},
			onPointerDown: checkVirtualPointer,
			onPointerEnter: checkVirtualPointer,
			onMouseDown: checkVirtualMouse,
			onClick: checkVirtualMouse
		};
	}, [
		commonOnKeyDown,
		focusItemOnOpen,
		getMinEnabledIndex,
		nested,
		onNavigate,
		store,
		openOnArrowKeyDown,
		orientation,
		getParentOrientation,
		rtl,
		selectedIndexRef,
		virtual
	]);
	const reference = React$3.useMemo(() => {
		return {
			...ariaActiveDescendantProp,
			...trigger
		};
	}, [ariaActiveDescendantProp, trigger]);
	return React$3.useMemo(() => enabled ? {
		reference,
		floating,
		item,
		trigger
	} : {}, [
		enabled,
		reference,
		floating,
		trigger,
		item
	]);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/hooks/useTypeahead.mjs
/**
* Provides a matching callback that can be used to focus an item as the user
* types, often used in tandem with `useListNavigation()`.
* @see https://floating-ui.com/docs/useTypeahead
*/
function useTypeahead(context, props) {
	const { listRef, elementsRef, activeIndex, onMatch: onMatchProp, disabledIndices, onTyping, enabled = true, resetMs = 750, selectedIndex = null } = props;
	const store = "rootStore" in context ? context.rootStore : context;
	const open = store.useState("open");
	const timeout = useTimeout();
	const stringRef = React$3.useRef("");
	const prevIndexRef = React$3.useRef(selectedIndex ?? activeIndex ?? -1);
	const matchIndexRef = React$3.useRef(null);
	const onKeyDown = useStableCallback((event) => {
		function getElement(index) {
			return elementsRef?.current[index];
		}
		function isItemAvailable(index) {
			const element = getElement(index);
			if (element && !isElementVisible(element) || element?.matches(":disabled")) return false;
			return disabledIndices == null || !isListIndexDisabled(EMPTY_ARRAY$1, index, disabledIndices);
		}
		function getMatchingIndex(list, string, startIndex = 0) {
			if (list.length === 0) return -1;
			const normalizedStartIndex = (startIndex % list.length + list.length) % list.length;
			const lowerString = string.toLowerCase();
			for (let offset = 0; offset < list.length; offset += 1) {
				const index = (normalizedStartIndex + offset) % list.length;
				if (!list[index]?.toLowerCase().startsWith(lowerString) || !isItemAvailable(index)) continue;
				return index;
			}
			return -1;
		}
		const listContent = listRef.current;
		if (stringRef.current.length > 0 && event.key === " ") {
			stopEvent(event);
			onTyping?.(true);
		}
		if (stringRef.current.length > 0 && stringRef.current[0] !== " ") {
			if (getMatchingIndex(listContent, stringRef.current) === -1 && event.key !== " ") onTyping?.(false);
		}
		if (listContent == null || event.key.length !== 1 || event.ctrlKey || event.metaKey || event.altKey) return;
		if (open && event.key !== " ") {
			stopEvent(event);
			onTyping?.(true);
		}
		const isNewSession = stringRef.current === "";
		if (isNewSession) prevIndexRef.current = selectedIndex ?? activeIndex ?? -1;
		if (listContent.every((text, index) => text && isItemAvailable(index) ? text[0]?.toLowerCase() !== text[1]?.toLowerCase() : true) && stringRef.current === event.key) {
			stringRef.current = "";
			prevIndexRef.current = matchIndexRef.current;
		}
		stringRef.current += event.key;
		timeout.start(resetMs, () => {
			stringRef.current = "";
			prevIndexRef.current = matchIndexRef.current;
			onTyping?.(false);
		});
		const startIndex = ((isNewSession ? selectedIndex ?? activeIndex ?? -1 : prevIndexRef.current) ?? 0) + 1;
		const index = getMatchingIndex(listContent, stringRef.current, startIndex);
		if (index !== -1) {
			onMatchProp?.(index);
			matchIndexRef.current = index;
		} else if (event.key !== " ") {
			stringRef.current = "";
			onTyping?.(false);
		}
	});
	const onBlur = useStableCallback((event) => {
		const next = event.relatedTarget;
		const currentDomReferenceElement = store.select("domReferenceElement");
		const currentFloatingElement = store.select("floatingElement");
		if (contains(currentDomReferenceElement, next) || contains(currentFloatingElement, next)) return;
		timeout.clear();
		stringRef.current = "";
		prevIndexRef.current = matchIndexRef.current;
		onTyping?.(false);
	});
	useIsoLayoutEffect(() => {
		if (!open && selectedIndex !== null) return;
		timeout.clear();
		matchIndexRef.current = null;
		if (stringRef.current !== "") stringRef.current = "";
	}, [
		open,
		selectedIndex,
		timeout
	]);
	const sharedProps = React$3.useMemo(() => ({
		onKeyDown,
		onBlur
	}), [onKeyDown, onBlur]);
	return React$3.useMemo(() => enabled ? {
		reference: sharedProps,
		floating: sharedProps
	} : {}, [enabled, sharedProps]);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/safePolygon.mjs
var CURSOR_SPEED_THRESHOLD = .1;
var CURSOR_SPEED_THRESHOLD_SQUARED = CURSOR_SPEED_THRESHOLD * CURSOR_SPEED_THRESHOLD;
var POLYGON_BUFFER = .5;
function hasIntersectingEdge(pointX, pointY, xi, yi, xj, yj) {
	return yi >= pointY !== yj >= pointY && pointX <= (xj - xi) * (pointY - yi) / (yj - yi) + xi;
}
function isPointInQuadrilateral(pointX, pointY, x1, y1, x2, y2, x3, y3, x4, y4) {
	let isInsideValue = false;
	if (hasIntersectingEdge(pointX, pointY, x1, y1, x2, y2)) isInsideValue = !isInsideValue;
	if (hasIntersectingEdge(pointX, pointY, x2, y2, x3, y3)) isInsideValue = !isInsideValue;
	if (hasIntersectingEdge(pointX, pointY, x3, y3, x4, y4)) isInsideValue = !isInsideValue;
	if (hasIntersectingEdge(pointX, pointY, x4, y4, x1, y1)) isInsideValue = !isInsideValue;
	return isInsideValue;
}
function isInsideRect(pointX, pointY, rect) {
	return pointX >= rect.x && pointX <= rect.x + rect.width && pointY >= rect.y && pointY <= rect.y + rect.height;
}
function isInsideAxisAlignedRect(pointX, pointY, x1, y1, x2, y2) {
	return pointX >= Math.min(x1, x2) && pointX <= Math.max(x1, x2) && pointY >= Math.min(y1, y2) && pointY <= Math.max(y1, y2);
}
/**
* Generates a safe polygon area that the user can traverse without closing the
* floating element once leaving the reference element.
* @see https://floating-ui.com/docs/useHover#safepolygon
*/
function safePolygon(options = {}) {
	const { blockPointerEvents = false } = options;
	const timeout = new Timeout();
	const fn = ({ x, y, placement, elements, onClose, nodeId, tree }) => {
		const side = placement?.split("-")[0];
		let hasLanded = false;
		let lastX = null;
		let lastY = null;
		let lastCursorTime = typeof performance !== "undefined" ? performance.now() : 0;
		function isCursorMovingSlowly(nextX, nextY) {
			const currentTime = performance.now();
			const elapsedTime = currentTime - lastCursorTime;
			if (lastX === null || lastY === null || elapsedTime === 0) {
				lastX = nextX;
				lastY = nextY;
				lastCursorTime = currentTime;
				return false;
			}
			const deltaX = nextX - lastX;
			const deltaY = nextY - lastY;
			const distanceSquared = deltaX * deltaX + deltaY * deltaY;
			const thresholdSquared = elapsedTime * elapsedTime * CURSOR_SPEED_THRESHOLD_SQUARED;
			lastX = nextX;
			lastY = nextY;
			lastCursorTime = currentTime;
			return distanceSquared < thresholdSquared;
		}
		function close() {
			timeout.clear();
			onClose();
		}
		return function onMouseMove(event) {
			timeout.clear();
			const domReference = elements.domReference;
			const floating = elements.floating;
			if (!domReference || !floating || side == null || x == null || y == null) return;
			const { clientX, clientY } = event;
			const target = getTarget(event);
			const isLeave = event.type === "mouseleave";
			const isOverFloatingEl = contains(floating, target);
			const isOverReferenceEl = contains(domReference, target);
			if (isOverFloatingEl) {
				hasLanded = true;
				if (!isLeave) return;
			}
			if (isOverReferenceEl) {
				hasLanded = false;
				if (!isLeave) {
					hasLanded = true;
					return;
				}
			}
			if (isLeave && isElement(event.relatedTarget) && contains(floating, event.relatedTarget)) return;
			function hasOpenChildNode() {
				return Boolean(tree && getNodeChildren(tree.nodesRef.current, nodeId).length > 0);
			}
			function closeIfNoOpenChild() {
				if (!hasOpenChildNode()) close();
			}
			if (hasOpenChildNode()) return;
			const refRect = domReference.getBoundingClientRect();
			const rect = floating.getBoundingClientRect();
			const cursorLeaveFromRight = x > rect.right - rect.width / 2;
			const cursorLeaveFromBottom = y > rect.bottom - rect.height / 2;
			const isFloatingWider = rect.width > refRect.width;
			const isFloatingTaller = rect.height > refRect.height;
			const left = (isFloatingWider ? refRect : rect).left;
			const right = (isFloatingWider ? refRect : rect).right;
			const top = (isFloatingTaller ? refRect : rect).top;
			const bottom = (isFloatingTaller ? refRect : rect).bottom;
			if (side === "top" && y >= refRect.bottom - 1 || side === "bottom" && y <= refRect.top + 1 || side === "left" && x >= refRect.right - 1 || side === "right" && x <= refRect.left + 1) {
				closeIfNoOpenChild();
				return;
			}
			let isInsideTroughRect = false;
			switch (side) {
				case "top":
					isInsideTroughRect = isInsideAxisAlignedRect(clientX, clientY, left, refRect.top + 1, right, rect.bottom - 1);
					break;
				case "bottom":
					isInsideTroughRect = isInsideAxisAlignedRect(clientX, clientY, left, rect.top + 1, right, refRect.bottom - 1);
					break;
				case "left":
					isInsideTroughRect = isInsideAxisAlignedRect(clientX, clientY, rect.right - 1, bottom, refRect.left + 1, top);
					break;
				case "right":
					isInsideTroughRect = isInsideAxisAlignedRect(clientX, clientY, refRect.right - 1, bottom, rect.left + 1, top);
					break;
				default:
			}
			if (isInsideTroughRect) return;
			if (hasLanded && !isInsideRect(clientX, clientY, refRect)) {
				closeIfNoOpenChild();
				return;
			}
			if (!isLeave && isCursorMovingSlowly(clientX, clientY)) {
				closeIfNoOpenChild();
				return;
			}
			let isInsidePolygon = false;
			switch (side) {
				case "top": {
					const cursorXOffset = isFloatingWider ? POLYGON_BUFFER / 2 : POLYGON_BUFFER * 4;
					const cursorPointOneX = isFloatingWider ? x + cursorXOffset : cursorLeaveFromRight ? x + cursorXOffset : x - cursorXOffset;
					const cursorPointTwoX = isFloatingWider ? x - cursorXOffset : cursorLeaveFromRight ? x + cursorXOffset : x - cursorXOffset;
					const cursorPointY = y + POLYGON_BUFFER + 1;
					const commonYLeft = cursorLeaveFromRight ? rect.bottom - POLYGON_BUFFER : isFloatingWider ? rect.bottom - POLYGON_BUFFER : rect.top;
					const commonYRight = cursorLeaveFromRight ? isFloatingWider ? rect.bottom - POLYGON_BUFFER : rect.top : rect.bottom - POLYGON_BUFFER;
					isInsidePolygon = isPointInQuadrilateral(clientX, clientY, cursorPointOneX, cursorPointY, cursorPointTwoX, cursorPointY, rect.left, commonYLeft, rect.right, commonYRight);
					break;
				}
				case "bottom": {
					const cursorXOffset = isFloatingWider ? POLYGON_BUFFER / 2 : POLYGON_BUFFER * 4;
					const cursorPointOneX = isFloatingWider ? x + cursorXOffset : cursorLeaveFromRight ? x + cursorXOffset : x - cursorXOffset;
					const cursorPointTwoX = isFloatingWider ? x - cursorXOffset : cursorLeaveFromRight ? x + cursorXOffset : x - cursorXOffset;
					const cursorPointY = y - POLYGON_BUFFER;
					const commonYLeft = cursorLeaveFromRight ? rect.top + POLYGON_BUFFER : isFloatingWider ? rect.top + POLYGON_BUFFER : rect.bottom;
					const commonYRight = cursorLeaveFromRight ? isFloatingWider ? rect.top + POLYGON_BUFFER : rect.bottom : rect.top + POLYGON_BUFFER;
					isInsidePolygon = isPointInQuadrilateral(clientX, clientY, cursorPointOneX, cursorPointY, cursorPointTwoX, cursorPointY, rect.left, commonYLeft, rect.right, commonYRight);
					break;
				}
				case "left": {
					const cursorYOffset = isFloatingTaller ? POLYGON_BUFFER / 2 : POLYGON_BUFFER * 4;
					const cursorPointOneY = isFloatingTaller ? y + cursorYOffset : cursorLeaveFromBottom ? y + cursorYOffset : y - cursorYOffset;
					const cursorPointTwoY = isFloatingTaller ? y - cursorYOffset : cursorLeaveFromBottom ? y + cursorYOffset : y - cursorYOffset;
					const cursorPointX = x + POLYGON_BUFFER + 1;
					const commonXTop = cursorLeaveFromBottom ? rect.right - POLYGON_BUFFER : isFloatingTaller ? rect.right - POLYGON_BUFFER : rect.left;
					const commonXBottom = cursorLeaveFromBottom ? isFloatingTaller ? rect.right - POLYGON_BUFFER : rect.left : rect.right - POLYGON_BUFFER;
					isInsidePolygon = isPointInQuadrilateral(clientX, clientY, commonXTop, rect.top, commonXBottom, rect.bottom, cursorPointX, cursorPointOneY, cursorPointX, cursorPointTwoY);
					break;
				}
				case "right": {
					const cursorYOffset = isFloatingTaller ? POLYGON_BUFFER / 2 : POLYGON_BUFFER * 4;
					const cursorPointOneY = isFloatingTaller ? y + cursorYOffset : cursorLeaveFromBottom ? y + cursorYOffset : y - cursorYOffset;
					const cursorPointTwoY = isFloatingTaller ? y - cursorYOffset : cursorLeaveFromBottom ? y + cursorYOffset : y - cursorYOffset;
					const cursorPointX = x - POLYGON_BUFFER;
					const commonXTop = cursorLeaveFromBottom ? rect.left + POLYGON_BUFFER : isFloatingTaller ? rect.left + POLYGON_BUFFER : rect.right;
					const commonXBottom = cursorLeaveFromBottom ? isFloatingTaller ? rect.left + POLYGON_BUFFER : rect.right : rect.left + POLYGON_BUFFER;
					isInsidePolygon = isPointInQuadrilateral(clientX, clientY, cursorPointX, cursorPointOneY, cursorPointX, cursorPointTwoY, commonXTop, rect.top, commonXBottom, rect.bottom);
					break;
				}
				default:
			}
			if (!isInsidePolygon) closeIfNoOpenChild();
			else if (!hasLanded) timeout.start(40, closeIfNoOpenChild);
		};
	};
	fn.__options = {
		...options,
		blockPointerEvents
	};
	return fn;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/dialog/portal/DialogPortalContext.mjs
var DialogPortalContext = /* @__PURE__ */ React$3.createContext(void 0);
function useDialogPortalContext() {
	const value = React$3.useContext(DialogPortalContext);
	if (value === void 0) throw new Error(formatErrorMessage(26));
	return value;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/composite/composite.mjs
var ARROW_UP = "ArrowUp";
var ARROW_DOWN = "ArrowDown";
var ARROW_LEFT = "ArrowLeft";
var ARROW_RIGHT = "ArrowRight";
var COMPOSITE_KEYS = new Set([
	ARROW_UP,
	ARROW_DOWN,
	ARROW_LEFT,
	ARROW_RIGHT,
	"Home",
	"End"
]);
var MODIFIER_KEYS = [
	"Shift",
	"Control",
	"Alt",
	"Meta"
];
function isInputElement(element) {
	return isHTMLElement(element) && element.tagName === "INPUT";
}
function isNativeInput(element) {
	if (isInputElement(element) && element.selectionStart != null) return true;
	if (isHTMLElement(element) && element.tagName === "TEXTAREA") return true;
	return false;
}
function scrollIntoViewIfNeeded(scrollContainer, element, direction, orientation) {
	if (!scrollContainer || !element || !element.scrollTo) return;
	let targetX = scrollContainer.scrollLeft;
	let targetY = scrollContainer.scrollTop;
	const isOverflowingX = scrollContainer.clientWidth < scrollContainer.scrollWidth;
	const isOverflowingY = scrollContainer.clientHeight < scrollContainer.scrollHeight;
	if (isOverflowingX && orientation !== "vertical") {
		const elementOffsetLeft = getOffset(scrollContainer, element, "left");
		const containerStyles = getStyles(scrollContainer);
		const elementStyles = getStyles(element);
		if (direction === "ltr") {
			if (elementOffsetLeft + element.offsetWidth + elementStyles.scrollMarginRight > scrollContainer.scrollLeft + scrollContainer.clientWidth - containerStyles.scrollPaddingRight) targetX = elementOffsetLeft + element.offsetWidth + elementStyles.scrollMarginRight - scrollContainer.clientWidth + containerStyles.scrollPaddingRight;
			else if (elementOffsetLeft - elementStyles.scrollMarginLeft < scrollContainer.scrollLeft + containerStyles.scrollPaddingLeft) targetX = elementOffsetLeft - elementStyles.scrollMarginLeft - containerStyles.scrollPaddingLeft;
		}
		if (direction === "rtl") {
			if (elementOffsetLeft - elementStyles.scrollMarginLeft < scrollContainer.scrollLeft + containerStyles.scrollPaddingLeft) targetX = elementOffsetLeft - elementStyles.scrollMarginLeft - containerStyles.scrollPaddingLeft;
			else if (elementOffsetLeft + element.offsetWidth + elementStyles.scrollMarginRight > scrollContainer.scrollLeft + scrollContainer.clientWidth - containerStyles.scrollPaddingRight) targetX = elementOffsetLeft + element.offsetWidth + elementStyles.scrollMarginRight - scrollContainer.clientWidth + containerStyles.scrollPaddingRight;
		}
	}
	if (isOverflowingY && orientation !== "horizontal") {
		const elementOffsetTop = getOffset(scrollContainer, element, "top");
		const containerStyles = getStyles(scrollContainer);
		const elementStyles = getStyles(element);
		if (elementOffsetTop - elementStyles.scrollMarginTop < scrollContainer.scrollTop + containerStyles.scrollPaddingTop) targetY = elementOffsetTop - elementStyles.scrollMarginTop - containerStyles.scrollPaddingTop;
		else if (elementOffsetTop + element.offsetHeight + elementStyles.scrollMarginBottom > scrollContainer.scrollTop + scrollContainer.clientHeight - containerStyles.scrollPaddingBottom) targetY = elementOffsetTop + element.offsetHeight + elementStyles.scrollMarginBottom - scrollContainer.clientHeight + containerStyles.scrollPaddingBottom;
	}
	scrollContainer.scrollTo({
		left: targetX,
		top: targetY,
		behavior: "auto"
	});
}
function getOffset(ancestor, element, side) {
	const propName = side === "left" ? "offsetLeft" : "offsetTop";
	let result = 0;
	while (element.offsetParent) {
		result += element[propName];
		if (element.offsetParent === ancestor) break;
		element = element.offsetParent;
	}
	return result;
}
function getStyles(element) {
	const styles = getComputedStyle(element);
	return {
		scrollMarginTop: parseFloat(styles.scrollMarginTop) || 0,
		scrollMarginRight: parseFloat(styles.scrollMarginRight) || 0,
		scrollMarginBottom: parseFloat(styles.scrollMarginBottom) || 0,
		scrollMarginLeft: parseFloat(styles.scrollMarginLeft) || 0,
		scrollPaddingTop: parseFloat(styles.scrollPaddingTop) || 0,
		scrollPaddingRight: parseFloat(styles.scrollPaddingRight) || 0,
		scrollPaddingBottom: parseFloat(styles.scrollPaddingBottom) || 0,
		scrollPaddingLeft: parseFloat(styles.scrollPaddingLeft) || 0
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/dialog/utils/stateAttributesMapping.mjs
/**
* Shared by `Dialog.Popup` and `Dialog.Viewport`, whose states have the same shape.
* `nested` is not mapped: unmapped `true` booleans already render as `data-nested`.
*/
var dialogStateAttributesMapping = {
	...popupStateMapping,
	...transitionStatusMapping,
	nestedDialogOpen(value) {
		return value ? { "data-nested-dialog-open": "" } : null;
	}
};
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/dialog/popup/DialogPopup.mjs
/**
* A container for the dialog contents.
* Renders a `<div>` element.
*
* Documentation: [Base UI Dialog](https://base-ui.com/react/components/dialog)
*/
var DialogPopup = /* @__PURE__ */ React$3.forwardRef(function DialogPopup(componentProps, forwardedRef) {
	const { render, className, style, finalFocus, initialFocus, ...elementProps } = componentProps;
	const store = useDialogRootContext();
	const descriptionElementId = store.useState("descriptionElementId");
	const disablePointerDismissal = store.useState("disablePointerDismissal");
	const floatingRootContext = store.useState("floatingRootContext");
	const rootPopupProps = store.useState("popupProps");
	const modal = store.useState("modal");
	const mounted = store.useState("mounted");
	const nested = store.useState("nested");
	const nestedOpenDialogCount = store.useState("nestedOpenDialogCount");
	const open = store.useState("open");
	const openMethod = store.useState("openMethod");
	const titleElementId = store.useState("titleElementId");
	const transitionStatus = store.useState("transitionStatus");
	const role = store.useState("role");
	const floatingId = floatingRootContext.useState("floatingId");
	useDialogPortalContext();
	useOpenChangeComplete({
		open,
		ref: store.context.popupRef,
		onComplete() {
			if (open) store.context.onOpenChangeComplete?.(true);
		}
	});
	const resolvedInitialFocus = initialFocus === void 0 ? createDefaultInitialFocus(store.context.popupRef) : initialFocus;
	const nestedDialogOpen = nestedOpenDialogCount > 0;
	const setPopupElement = store.useStateSetter("popupElement");
	const element = useRenderElement("div", componentProps, {
		state: {
			open,
			nested,
			transitionStatus,
			nestedDialogOpen
		},
		props: [
			rootPopupProps,
			{
				id: floatingId,
				"aria-labelledby": titleElementId,
				"aria-describedby": descriptionElementId,
				role,
				...FOCUSABLE_POPUP_PROPS,
				hidden: !mounted,
				onKeyDown(event) {
					if (COMPOSITE_KEYS.has(event.key)) event.stopPropagation();
				},
				style: { "--nested-dialogs": nestedOpenDialogCount }
			},
			elementProps
		],
		ref: [
			forwardedRef,
			store.context.popupRef,
			setPopupElement
		],
		stateAttributesMapping: dialogStateAttributesMapping
	});
	return /* @__PURE__ */ jsx(FloatingFocusManager, {
		context: floatingRootContext,
		openInteractionType: openMethod,
		disabled: !mounted,
		closeOnFocusOut: !disablePointerDismissal,
		initialFocus: resolvedInitialFocus,
		returnFocus: finalFocus,
		modal: modal !== false,
		restoreFocus: "popup",
		children: element
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/inertValue.mjs
function inertValue(value) {
	if (isReactVersionAtLeast(19)) return value;
	return value ? "true" : void 0;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/InternalBackdrop.mjs
/**
* @internal
*/
var InternalBackdrop = /* @__PURE__ */ React$3.forwardRef(function InternalBackdrop(props, ref) {
	const { cutout, ...otherProps } = props;
	let clipPath;
	if (cutout) {
		const rect = cutout.getBoundingClientRect();
		clipPath = `polygon(0% 0%,100% 0%,100% 100%,0% 100%,0% 0%,${rect.left}px ${rect.top}px,${rect.left}px ${rect.bottom}px,${rect.right}px ${rect.bottom}px,${rect.right}px ${rect.top}px,${rect.left}px ${rect.top}px)`;
	}
	return /* @__PURE__ */ jsx("div", {
		ref,
		role: "presentation",
		"data-base-ui-inert": "",
		...otherProps,
		style: {
			position: "fixed",
			inset: 0,
			userSelect: "none",
			WebkitUserSelect: "none",
			clipPath
		}
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/dialog/portal/DialogPortal.mjs
/**
* A portal element that moves the popup to a different part of the DOM.
* By default, the portal element is appended to `<body>`.
* Renders a `<div>` element.
*
* Documentation: [Base UI Dialog](https://base-ui.com/react/components/dialog)
*/
var DialogPortal = /* @__PURE__ */ React$3.forwardRef(function DialogPortal(props, forwardedRef) {
	const { keepMounted = false, ...portalProps } = props;
	const store = useDialogRootContext();
	const mounted = store.useState("mounted");
	const modal = store.useState("modal");
	const open = store.useState("open");
	if (!(mounted || keepMounted)) return null;
	return /* @__PURE__ */ jsx(DialogPortalContext.Provider, {
		value: keepMounted,
		children: /* @__PURE__ */ jsxs(FloatingPortal, {
			ref: forwardedRef,
			...portalProps,
			children: [mounted && modal === true && /* @__PURE__ */ jsx(InternalBackdrop, {
				ref: store.context.internalBackdropRef,
				inert: inertValue(!open)
			}), props.children]
		})
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/useScrollLock.mjs
var originalHtmlStyles = {};
var originalBodyStyles = {};
var originalHtmlScrollBehavior = "";
function getViewportScroller(html, body) {
	return isOverflowElement(html) ? html : body;
}
function isPageScrollLocked(win, html, body) {
	return /hidden|clip/.test(win.getComputedStyle(getViewportScroller(html, body)).overflowY);
}
function hasInsetScrollbars(referenceElement) {
	if (typeof document === "undefined") return false;
	const doc = ownerDocument(referenceElement);
	return getWindow(doc).innerWidth - doc.documentElement.clientWidth > 0;
}
function supportsStableScrollbarGutter(referenceElement) {
	if (!(typeof CSS !== "undefined" && CSS.supports && CSS.supports("scrollbar-gutter", "stable")) || typeof document === "undefined") return false;
	const doc = ownerDocument(referenceElement);
	const html = doc.documentElement;
	const body = doc.body;
	const scrollContainer = getViewportScroller(html, body);
	const originalScrollContainerOverflowY = scrollContainer.style.overflowY;
	const originalHtmlStyleGutter = html.style.scrollbarGutter;
	html.style.scrollbarGutter = "stable";
	scrollContainer.style.overflowY = "scroll";
	const before = scrollContainer.offsetWidth;
	scrollContainer.style.overflowY = "hidden";
	const after = scrollContainer.offsetWidth;
	scrollContainer.style.overflowY = originalScrollContainerOverflowY;
	html.style.scrollbarGutter = originalHtmlStyleGutter;
	return before === after;
}
function preventScrollOverlayScrollbars(referenceElement) {
	const doc = ownerDocument(referenceElement);
	const html = doc.documentElement;
	const body = doc.body;
	const elementToLock = getViewportScroller(html, body);
	const originalElementToLockStyles = {
		overflowY: elementToLock.style.overflowY,
		overflowX: elementToLock.style.overflowX
	};
	Object.assign(elementToLock.style, {
		overflowY: "hidden",
		overflowX: "hidden"
	});
	return () => {
		Object.assign(elementToLock.style, originalElementToLockStyles);
	};
}
function preventScrollInsetScrollbars(referenceElement) {
	const doc = ownerDocument(referenceElement);
	const html = doc.documentElement;
	const body = doc.body;
	const win = getWindow(html);
	let scrollTop = 0;
	let scrollLeft = 0;
	let updateGutterOnly = false;
	const resizeFrame = AnimationFrame.create();
	if (webkit && (win.visualViewport?.scale ?? 1) !== 1) return () => {};
	function lockScroll() {
		const htmlStyles = win.getComputedStyle(html);
		const bodyStyles = win.getComputedStyle(body);
		const scrollbarGutterValue = (htmlStyles.scrollbarGutter || "").includes("both-edges") ? "stable both-edges" : "stable";
		scrollTop = html.scrollTop;
		scrollLeft = html.scrollLeft;
		originalHtmlStyles = {
			scrollbarGutter: html.style.scrollbarGutter,
			overflowY: html.style.overflowY,
			overflowX: html.style.overflowX
		};
		originalHtmlScrollBehavior = html.style.scrollBehavior;
		originalBodyStyles = {
			position: body.style.position,
			height: body.style.height,
			width: body.style.width,
			boxSizing: body.style.boxSizing,
			overflowY: body.style.overflowY,
			overflowX: body.style.overflowX,
			scrollBehavior: body.style.scrollBehavior
		};
		const isScrollableY = html.scrollHeight > html.clientHeight;
		const isScrollableX = html.scrollWidth > html.clientWidth;
		const hasConstantOverflowY = htmlStyles.overflowY === "scroll" || bodyStyles.overflowY === "scroll";
		const hasConstantOverflowX = htmlStyles.overflowX === "scroll" || bodyStyles.overflowX === "scroll";
		const scrollbarWidth = Math.max(0, win.innerWidth - body.clientWidth);
		const scrollbarHeight = Math.max(0, win.innerHeight - body.clientHeight);
		const marginY = parseFloat(bodyStyles.marginTop) + parseFloat(bodyStyles.marginBottom);
		const marginX = parseFloat(bodyStyles.marginLeft) + parseFloat(bodyStyles.marginRight);
		const elementToLock = getViewportScroller(html, body);
		updateGutterOnly = supportsStableScrollbarGutter(referenceElement);
		if (updateGutterOnly) {
			html.style.scrollbarGutter = scrollbarGutterValue;
			elementToLock.style.overflowY = "hidden";
			elementToLock.style.overflowX = "hidden";
			return;
		}
		Object.assign(html.style, {
			scrollbarGutter: scrollbarGutterValue,
			overflowY: "hidden",
			overflowX: "hidden"
		});
		if (isScrollableY || hasConstantOverflowY) html.style.overflowY = "scroll";
		if (isScrollableX || hasConstantOverflowX) html.style.overflowX = "scroll";
		Object.assign(body.style, {
			position: "relative",
			height: marginY || scrollbarHeight ? `calc(100dvh - ${marginY + scrollbarHeight}px)` : "100dvh",
			width: marginX || scrollbarWidth ? `calc(100vw - ${marginX + scrollbarWidth}px)` : "100vw",
			boxSizing: "border-box",
			overflowY: "hidden",
			overflowX: "hidden",
			scrollBehavior: "unset"
		});
		body.scrollTop = scrollTop;
		body.scrollLeft = scrollLeft;
		html.setAttribute("data-base-ui-scroll-locked", "");
		html.style.scrollBehavior = "unset";
	}
	function cleanup() {
		Object.assign(html.style, originalHtmlStyles);
		Object.assign(body.style, originalBodyStyles);
		if (!updateGutterOnly) {
			html.scrollTop = scrollTop;
			html.scrollLeft = scrollLeft;
			html.removeAttribute("data-base-ui-scroll-locked");
			html.style.scrollBehavior = originalHtmlScrollBehavior;
		}
	}
	function handleResize() {
		cleanup();
		resizeFrame.request(lockScroll);
	}
	lockScroll();
	const unsubscribeResize = addEventListener(win, "resize", handleResize);
	return () => {
		resizeFrame.cancel();
		cleanup();
		if (typeof win.removeEventListener === "function") unsubscribeResize();
	};
}
var ScrollLocker = class {
	lockCount = 0;
	restore = null;
	timeoutLock = Timeout.create();
	timeoutUnlock = Timeout.create();
	acquire(referenceElement) {
		this.lockCount += 1;
		if (this.lockCount === 1 && this.restore === null) this.timeoutLock.start(0, () => this.lock(referenceElement));
		return this.release;
	}
	release = () => {
		this.lockCount -= 1;
		if (this.lockCount === 0 && this.restore) this.timeoutUnlock.start(0, this.unlock);
	};
	unlock = () => {
		if (this.lockCount === 0 && this.restore) {
			this.restore?.();
			this.restore = null;
		}
	};
	lock(referenceElement) {
		if (this.lockCount === 0 || this.restore !== null) return;
		const doc = ownerDocument(referenceElement);
		const html = doc.documentElement;
		const body = doc.body;
		const win = getWindow(html);
		if (isPageScrollLocked(win, html, body)) {
			const observer = new win.MutationObserver(() => {
				if (isPageScrollLocked(win, html, body)) return;
				observer.disconnect();
				this.restore = null;
				this.lock(referenceElement);
			});
			const options = { attributes: true };
			observer.observe(html, options);
			observer.observe(body, options);
			this.restore = () => observer.disconnect();
			return;
		}
		const hasOverlayScrollbars = ios || !hasInsetScrollbars(referenceElement);
		this.restore = hasOverlayScrollbars ? preventScrollOverlayScrollbars(referenceElement) : preventScrollInsetScrollbars(referenceElement);
	}
};
var SCROLL_LOCKER = new ScrollLocker();
/**
* Locks the scroll of the document when enabled.
*
* @param enabled - Whether to enable the scroll lock.
* @param referenceElement - Element to use as a reference for lock calculations.
*/
function useScrollLock(enabled = true, referenceElement = null) {
	useIsoLayoutEffect(() => {
		if (!enabled) return;
		return SCROLL_LOCKER.acquire(referenceElement);
	}, [enabled, referenceElement]);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/dialog/root/useDialogRoot.mjs
function DialogInteractions({ store, parentContext, isDrawer }) {
	const open = store.useState("open");
	const disablePointerDismissal = store.useState("disablePointerDismissal");
	const modal = store.useState("modal");
	const popupElement = store.useState("popupElement");
	const floatingRootContext = store.useState("floatingRootContext");
	const [ownNestedOpenDialogs, setOwnNestedOpenDialogs] = React$3.useState(0);
	const [ownNestedOpenDrawers, setOwnNestedOpenDrawers] = React$3.useState(0);
	const isTopmost = ownNestedOpenDialogs === 0;
	const dismiss = useDismiss(floatingRootContext, {
		outsidePressEvent() {
			if (store.context.internalBackdropRef.current || store.context.backdropRef.current) return "intentional";
			return {
				mouse: modal === "trap-focus" ? "sloppy" : "intentional",
				touch: "sloppy"
			};
		},
		outsidePress(event) {
			if (!store.context.outsidePressEnabledRef.current) return false;
			if ("button" in event && event.button !== 0) return false;
			if ("touches" in event) {
				if (event.type === "touchend") {
					if (event.changedTouches.length !== 1 || event.touches.length !== 0) return false;
				} else if (event.touches.length !== 1) return false;
			}
			const target = getTarget(event);
			if (isTopmost && !disablePointerDismissal) {
				if (modal) {
					const internalBackdrop = store.context.internalBackdropRef.current;
					const backdrop = store.context.backdropRef.current;
					return internalBackdrop || backdrop ? internalBackdrop === target || backdrop === target || contains(target, popupElement) && !target?.hasAttribute("data-base-ui-portal") : true;
				}
				return true;
			}
			return false;
		},
		escapeKey: isTopmost
	});
	useScrollLock(open && modal === true, popupElement);
	store.useContextCallback("onNestedDialogOpen", (dialogCount, drawerCount) => {
		setOwnNestedOpenDialogs(dialogCount);
		setOwnNestedOpenDrawers(drawerCount);
	});
	useIsoLayoutEffect(() => {
		if (parentContext?.onNestedDialogOpen) if (open) parentContext.onNestedDialogOpen(ownNestedOpenDialogs + 1, ownNestedOpenDrawers + (isDrawer ? 1 : 0));
		else parentContext.onNestedDialogOpen(0, 0);
		return () => {
			if (parentContext?.onNestedDialogOpen && open) parentContext.onNestedDialogOpen(0, 0);
		};
	}, [
		isDrawer,
		open,
		ownNestedOpenDialogs,
		ownNestedOpenDrawers,
		parentContext
	]);
	usePopupInteractionProps(store, {
		activeTriggerProps: dismiss.reference,
		inactiveTriggerProps: dismiss.trigger,
		popupProps: dismiss.floating,
		nestedOpenDialogCount: ownNestedOpenDialogs,
		nestedOpenDrawerCount: ownNestedOpenDrawers
	});
	return null;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/dialog/store/DialogStore.mjs
var selectors$2 = {
	...popupStoreSelectors,
	modal: (state) => state.modal,
	nested: (state) => state.nested,
	nestedOpenDialogCount: (state) => state.nestedOpenDialogCount,
	nestedOpenDrawerCount: (state) => state.nestedOpenDrawerCount,
	disablePointerDismissal: (state) => state.disablePointerDismissal,
	openMethod: (state) => state.openMethod,
	descriptionElementId: (state) => state.descriptionElementId,
	titleElementId: (state) => state.titleElementId,
	viewportElement: (state) => state.viewportElement,
	role: (state) => state.role
};
/**
* The subset of `DialogStore` that detached handle-backed triggers rely on. Both the real
* `DialogStore` and the inert fallback store satisfy it, so a trigger can read from whichever
* store the handle currently exposes.
*/
var DialogStore = class extends ReactStore {
	constructor(initialState, floatingId, nested) {
		const triggerElements = new PopupTriggerMap();
		const state = createInitialState$1(initialState, triggerElements, floatingId, nested);
		super(state, createInitialContext$1(triggerElements), selectors$2);
	}
	setOpen = (nextOpen, eventDetails) => {
		eventDetails.preventUnmountOnClose = () => {
			this.set("preventUnmountingOnClose", true);
		};
		if (!nextOpen && eventDetails.trigger == null && this.state.activeTriggerId != null) eventDetails.trigger = this.state.activeTriggerElement ?? void 0;
		this.context.onOpenChange?.(nextOpen, eventDetails);
		if (eventDetails.isCanceled) return;
		this.state.floatingRootContext.dispatchOpenChange(nextOpen, eventDetails);
		const updatedState = { open: nextOpen };
		setPopupOpenState(updatedState, nextOpen, eventDetails.trigger);
		this.update(updatedState);
	};
};
function createInitialState$1(initialState, triggerElements, floatingId, nested = false) {
	const state = {
		...createInitialPopupStoreState(),
		modal: true,
		disablePointerDismissal: false,
		viewportElement: null,
		descriptionElementId: void 0,
		titleElementId: void 0,
		openMethod: null,
		nested: false,
		nestedOpenDialogCount: 0,
		nestedOpenDrawerCount: 0,
		role: "dialog",
		...initialState
	};
	state.floatingRootContext = createPopupFloatingRootContext(triggerElements, floatingId, nested);
	return state;
}
function createInitialContext$1(triggerElements) {
	return {
		popupRef: /* @__PURE__ */ React$3.createRef(),
		backdropRef: /* @__PURE__ */ React$3.createRef(),
		internalBackdropRef: /* @__PURE__ */ React$3.createRef(),
		outsidePressEnabledRef: { current: true },
		triggerElements,
		onOpenChange: void 0,
		onOpenChangeComplete: void 0
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/dialog/root/useRenderDialogRoot.mjs
function useRenderDialogRoot(mode, props) {
	const { children, open: openProp, defaultOpen = false, onOpenChange, onOpenChangeComplete, disablePointerDismissal: disablePointerDismissalProp = false, modal: modalProp = true, actionsRef, handle, triggerId: triggerIdProp, defaultTriggerId: defaultTriggerIdProp = null } = props;
	const isDrawer = mode === "drawer";
	const isAlertDialog = mode === "alert-dialog";
	const modal = isAlertDialog ? true : modalProp;
	const disablePointerDismissal = isAlertDialog || disablePointerDismissalProp;
	const role = isAlertDialog ? "alertdialog" : "dialog";
	const parentStore = useDialogRootContext(true);
	const rootState = {
		modal,
		disablePointerDismissal,
		nested: parentStore != null,
		role
	};
	const store = usePopupRootStore((floatingId, floatingNested) => new DialogStore({
		open: defaultOpen,
		openProp,
		activeTriggerId: defaultTriggerIdProp,
		triggerIdProp,
		...rootState
	}, floatingId, floatingNested), true);
	store.useControlledProp("openProp", openProp);
	store.useControlledProp("triggerIdProp", triggerIdProp);
	store.useSyncedValues(rootState);
	store.useContextCallback("onOpenChange", onOpenChange);
	store.useContextCallback("onOpenChangeComplete", onOpenChangeComplete);
	const open = store.useState("open");
	const mounted = store.useState("mounted");
	const payload = store.useState("payload");
	usePopupRootSync(store, open);
	useImplicitActiveTrigger(store);
	const { forceUnmount } = useOpenStateTransitions(open, store);
	React$3.useImperativeHandle(actionsRef, () => ({
		unmount: forceUnmount,
		close: () => store.setOpen(false, createChangeEventDetails(imperativeAction))
	}), [forceUnmount, store]);
	const shouldRenderInteractions = open || mounted;
	return /* @__PURE__ */ jsxs(DialogRootContext.Provider, {
		value: store,
		children: [
			handle && /* @__PURE__ */ jsx(PopupHandleAttachment, {
				handle,
				store
			}),
			shouldRenderInteractions && /* @__PURE__ */ jsx(DialogInteractions, {
				store,
				parentContext: parentStore?.context,
				isDrawer
			}),
			typeof children === "function" ? children({ payload }) : children
		]
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/dialog/root/DialogRoot.mjs
/**
* Groups all parts of the dialog.
* Doesn't render its own HTML element.
*
* Documentation: [Base UI Dialog](https://base-ui.com/react/components/dialog)
*/
function DialogRoot(props) {
	return useRenderDialogRoot("dialog", props);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/dialog/title/DialogTitle.mjs
/**
* A heading that labels the dialog.
* Renders an `<h2>` element.
*
* Documentation: [Base UI Dialog](https://base-ui.com/react/components/dialog)
*/
var DialogTitle = /* @__PURE__ */ React$3.forwardRef(function DialogTitle(componentProps, forwardedRef) {
	const { render, className, style, id: idProp, ...elementProps } = componentProps;
	const store = useDialogRootContext();
	const id = useBaseUiId(idProp);
	store.useSyncedValueWithCleanup("titleElementId", id);
	return useRenderElement("h2", componentProps, {
		ref: forwardedRef,
		props: [{ id }, elementProps]
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/useEnhancedClickHandler.mjs
/**
* Provides a cross-browser way to determine the type of the pointer used to click.
* Safari and Firefox do not provide the PointerEvent to the click handler (they use MouseEvent) yet.
* Additionally, this implementation detects if the click was triggered by the keyboard.
*
* @param handler The function to be called when the button is clicked. The first parameter is the original event and the second parameter is the pointer type.
*/
function useEnhancedClickHandler(handler) {
	const lastClickInteractionTypeRef = React$3.useRef("");
	const handlePointerDown = React$3.useCallback((event) => {
		if (event.defaultPrevented) return;
		lastClickInteractionTypeRef.current = event.pointerType;
		handler(event, event.pointerType);
	}, [handler]);
	return {
		onClick: React$3.useCallback((event) => {
			if (event.detail === 0) {
				handler(event, "keyboard");
				return;
			}
			if ("pointerType" in event) handler(event, event.pointerType);
			else handler(event, lastClickInteractionTypeRef.current);
			lastClickInteractionTypeRef.current = "";
		}, [handler]),
		onPointerDown: handlePointerDown
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/useValueChanged.mjs
function useValueChanged(value, onChange) {
	const valueRef = React$3.useRef(value);
	const onChangeCallback = useStableCallback(onChange);
	useIsoLayoutEffect(() => {
		if (valueRef.current !== value) onChangeCallback(valueRef.current);
		valueRef.current = value;
	}, [value, onChangeCallback]);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/useOpenInteractionType.mjs
function useOpenMethodTriggerProps(open, setOpenMethod) {
	const { onClick, onPointerDown } = useEnhancedClickHandler(useStableCallback((_, interactionType) => {
		if (!(typeof open === "function" ? open() : open)) setOpenMethod(interactionType || (ios ? "touch" : ""));
	}));
	return React$3.useMemo(() => ({
		onClick,
		onPointerDown
	}), [onClick, onPointerDown]);
}
/**
* Determines the interaction type (keyboard, mouse, touch, etc.) that opened the component.
*
* @param open The open state of the component.
*/
function useOpenInteractionType(open) {
	const [openMethod, setOpenMethod] = React$3.useState(null);
	const triggerProps = useOpenMethodTriggerProps(open, setOpenMethod);
	useValueChanged(open, (previousOpen) => {
		if (previousOpen && !open) setOpenMethod(null);
	});
	return React$3.useMemo(() => ({
		openMethod,
		triggerProps
	}), [openMethod, triggerProps]);
}
//#endregion
//#region components/ui/sheet.tsx
function Sheet({ ...props }) {
	return /* @__PURE__ */ jsx(DialogRoot, {
		"data-slot": "sheet",
		...props
	});
}
function SheetPortal({ ...props }) {
	return /* @__PURE__ */ jsx(DialogPortal, {
		"data-slot": "sheet-portal",
		...props
	});
}
function SheetOverlay({ className, ...props }) {
	return /* @__PURE__ */ jsx(DialogBackdrop, {
		"data-slot": "sheet-overlay",
		className: cn("bg-black/10 supports-backdrop-filter:backdrop-blur-xs fixed inset-0 z-50 transition-opacity duration-150 data-ending-style:opacity-0 data-starting-style:opacity-0", className),
		...props
	});
}
function SheetContent({ className, children, side = "right", showCloseButton = true, ...props }) {
	return /* @__PURE__ */ jsxs(SheetPortal, { children: [/* @__PURE__ */ jsx(SheetOverlay, {}), /* @__PURE__ */ jsxs(DialogPopup, {
		"data-slot": "sheet-content",
		"data-side": side,
		className: cn("bg-popover text-popover-foreground fixed z-50 flex flex-col gap-4 bg-clip-padding text-sm shadow-lg transition duration-200 ease-in-out data-[side=bottom]:inset-x-0 data-[side=bottom]:bottom-0 data-[side=bottom]:h-auto data-[side=bottom]:border-t data-[side=left]:inset-y-0 data-[side=left]:left-0 data-[side=left]:h-full data-[side=left]:w-3/4 data-[side=left]:border-r data-[side=right]:inset-y-0 data-[side=right]:right-0 data-[side=right]:h-full data-[side=right]:w-3/4 data-[side=right]:border-l data-[side=top]:inset-x-0 data-[side=top]:top-0 data-[side=top]:h-auto data-[side=top]:border-b data-[side=left]:sm:max-w-sm data-[side=right]:sm:max-w-sm data-ending-style:opacity-0 data-starting-style:opacity-0 data-[side=bottom]:data-ending-style:translate-y-[2.5rem] data-[side=bottom]:data-starting-style:translate-y-[2.5rem] data-[side=left]:data-ending-style:translate-x-[-2.5rem] data-[side=left]:data-starting-style:translate-x-[-2.5rem] data-[side=right]:data-ending-style:translate-x-[2.5rem] data-[side=right]:data-starting-style:translate-x-[2.5rem] data-[side=top]:data-ending-style:translate-y-[-2.5rem] data-[side=top]:data-starting-style:translate-y-[-2.5rem]", className),
		...props,
		children: [showCloseButton && /* @__PURE__ */ jsxs(DialogClose, {
			"data-slot": "sheet-close",
			render: /* @__PURE__ */ jsx(Button, {
				variant: "ghost",
				className: "absolute top-3 right-3",
				size: "icon-sm"
			}),
			children: [/* @__PURE__ */ jsx(X, {}), /* @__PURE__ */ jsx("span", {
				className: "sr-only",
				children: "Close"
			})]
		}), children]
	})] });
}
function SheetHeader({ className, ...props }) {
	return /* @__PURE__ */ jsx("div", {
		"data-slot": "sheet-header",
		className: cn("gap-0.5 p-4 flex flex-col", className),
		...props
	});
}
function SheetTitle({ className, ...props }) {
	return /* @__PURE__ */ jsx(DialogTitle, {
		"data-slot": "sheet-title",
		className: cn("text-foreground text-base font-medium cn-font-heading", className),
		...props
	});
}
function SheetDescription({ className, ...props }) {
	return /* @__PURE__ */ jsx(DialogDescription, {
		"data-slot": "sheet-description",
		className: cn("text-muted-foreground text-sm", className),
		...props
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/tooltip/root/TooltipRootContext.mjs
var TooltipRootContext = /* @__PURE__ */ React$3.createContext(void 0);
function useTooltipRootContext(optional) {
	const context = React$3.useContext(TooltipRootContext);
	if (context === void 0 && !optional) throw new Error(formatErrorMessage(72));
	return context;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/tooltip/store/TooltipStore.mjs
var selectors$1 = {
	...popupStoreSelectors,
	disabled: (state) => state.disabled,
	instantType: (state) => state.instantType,
	isInstantPhase: (state) => state.isInstantPhase,
	trackCursorAxis: (state) => state.trackCursorAxis,
	disableHoverablePopup: (state) => state.disableHoverablePopup,
	lastOpenChangeReason: (state) => state.openChangeReason,
	closeOnClick: (state) => state.closeOnClick,
	closeDelay: (state) => state.closeDelay,
	adaptiveOrigin: (state) => state.adaptiveOrigin
};
/**
* The store view that detached handle-backed triggers read from. Both the real `TooltipStore` and
* the inert fallback store satisfy it, so a trigger can read from whichever store the handle
* currently exposes. Narrowed to the members a trigger actually uses — the trigger-data members plus
* `setOpen`/`cancelPendingOpen` (called directly by the trigger) and `useSyncedValue` — so the
* exposed surface can't bypass the open-change pipeline; on the detached fallback store every one of
* these mutations is a no-op.
*/
var TooltipStore = class extends ReactStore {
	constructor(initialState, floatingId, nested) {
		const triggerElements = new PopupTriggerMap();
		super(createInitialState(initialState, triggerElements, floatingId, nested), createInitialContext(triggerElements), selectors$1);
	}
	setOpen = (nextOpen, eventDetails) => {
		applyPopupOpenChange(this, nextOpen, eventDetails, { extraState: { openChangeReason: eventDetails.reason } });
	};
	cancelPendingOpen(event) {
		this.state.floatingRootContext.dispatchOpenChange(false, createChangeEventDetails(triggerPress, event));
	}
};
function createInitialState(initialState, triggerElements, floatingId, nested = false) {
	const state = {
		...createInitialPopupStoreState(),
		disabled: false,
		instantType: void 0,
		isInstantPhase: false,
		trackCursorAxis: "none",
		disableHoverablePopup: false,
		openChangeReason: null,
		closeOnClick: true,
		closeDelay: 0,
		adaptiveOrigin: void 0,
		...initialState
	};
	state.floatingRootContext = createPopupFloatingRootContext(triggerElements, floatingId, nested);
	return state;
}
function createInitialContext(triggerElements) {
	return {
		popupRef: /* @__PURE__ */ React$3.createRef(),
		onOpenChange: void 0,
		onOpenChangeComplete: void 0,
		triggerElements
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/tooltip/root/TooltipRoot.mjs
/**
* Groups all parts of the tooltip.
* Doesn't render its own HTML element.
*
* Documentation: [Base UI Tooltip](https://base-ui.com/react/components/tooltip)
*/
var TooltipRoot = fastComponent(function TooltipRoot(props) {
	const { disabled: disabled$1 = false, defaultOpen = false, open: openProp, disableHoverablePopup = false, trackCursorAxis = "none", actionsRef, onOpenChange, onOpenChangeComplete, handle, triggerId: triggerIdProp, defaultTriggerId: defaultTriggerIdProp = null, children } = props;
	const store = usePopupRootStore((floatingId, nested) => new TooltipStore({
		open: defaultOpen,
		openProp,
		activeTriggerId: defaultTriggerIdProp,
		triggerIdProp
	}, floatingId, nested));
	store.useControlledProp("openProp", openProp);
	store.useControlledProp("triggerIdProp", triggerIdProp);
	store.useContextCallback("onOpenChange", onOpenChange);
	store.useContextCallback("onOpenChangeComplete", onOpenChangeComplete);
	const openState = store.useState("open");
	const open = !disabled$1 && openState;
	const activeTriggerId = store.useState("activeTriggerId");
	const mounted = store.useState("mounted");
	const payload = store.useState("payload");
	store.useSyncedValues({
		trackCursorAxis,
		disableHoverablePopup,
		disabled: disabled$1
	});
	useImplicitActiveTrigger(store, { closeOnActiveTriggerUnmount: true });
	const { forceUnmount, transitionStatus } = useOpenStateTransitions(open, store);
	const isInstantPhase = store.useState("isInstantPhase");
	const instantType = store.useState("instantType");
	const lastOpenChangeReason = store.useState("lastOpenChangeReason");
	const previousInstantTypeRef = React$3.useRef(null);
	useIsoLayoutEffect(() => {
		if (openState && disabled$1) store.setOpen(false, createChangeEventDetails(disabled));
	}, [
		openState,
		disabled$1,
		store
	]);
	useIsoLayoutEffect(() => {
		if (transitionStatus === "ending" && lastOpenChangeReason === "none" || transitionStatus !== "ending" && isInstantPhase) {
			if (instantType !== "delay") previousInstantTypeRef.current = instantType;
			store.set("instantType", "delay");
		} else if (previousInstantTypeRef.current !== null) {
			store.set("instantType", previousInstantTypeRef.current);
			previousInstantTypeRef.current = null;
		}
	}, [
		transitionStatus,
		isInstantPhase,
		lastOpenChangeReason,
		instantType,
		store
	]);
	useIsoLayoutEffect(() => {
		if (open) {
			if (activeTriggerId == null) store.set("payload", void 0);
		}
	}, [
		store,
		activeTriggerId,
		open
	]);
	React$3.useImperativeHandle(actionsRef, () => ({
		unmount: forceUnmount,
		close: () => store.setOpen(false, createChangeEventDetails(imperativeAction))
	}), [forceUnmount, store]);
	const shouldRenderInteractions = open || mounted || !disabled$1 && trackCursorAxis !== "none";
	return /* @__PURE__ */ jsxs(TooltipRootContext.Provider, {
		value: store,
		children: [
			handle && /* @__PURE__ */ jsx(PopupHandleAttachment, {
				handle,
				store
			}),
			shouldRenderInteractions && /* @__PURE__ */ jsx(TooltipInteractions, {
				store,
				disabled: disabled$1,
				trackCursorAxis
			}),
			typeof children === "function" ? children({ payload }) : children
		]
	});
});
function TooltipInteractions({ store, disabled, trackCursorAxis }) {
	const floatingRootContext = store.useState("floatingRootContext");
	const dismiss = useDismiss(floatingRootContext, {
		enabled: !disabled,
		referencePress: () => store.select("closeOnClick")
	});
	const clientPoint = useClientPoint(floatingRootContext, {
		enabled: !disabled && trackCursorAxis !== "none",
		axis: trackCursorAxis === "none" ? void 0 : trackCursorAxis
	});
	const triggerProps = React$3.useMemo(() => mergeProps(clientPoint.reference, dismiss.reference), [clientPoint.reference, dismiss.reference]);
	usePopupInteractionProps(store, {
		activeTriggerProps: triggerProps,
		inactiveTriggerProps: triggerProps,
		popupProps: dismiss.floating ?? EMPTY_OBJECT
	});
	return null;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/tooltip/provider/TooltipProviderContext.mjs
/**
* Holds the provider's `delay` value. `closeDelay` is handled by the delay group.
*/
var TooltipProviderContext = /* @__PURE__ */ React$3.createContext(void 0);
function useTooltipProviderContext() {
	return React$3.useContext(TooltipProviderContext);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/tooltip/trigger/TooltipTrigger.mjs
var TOOLTIP_TRIGGER_IDENTIFIER = "data-base-ui-tooltip-trigger";
function getTargetElement(event) {
	if ("composedPath" in event) {
		const path = event.composedPath();
		for (let i = 0; i < path.length; i += 1) {
			const element = path[i];
			if (isElement(element)) return element;
		}
	}
	const target = event.target;
	if (isElement(target)) return target;
	return null;
}
function closestEnabledTooltipTrigger(element) {
	let current = element;
	while (current) {
		const trigger = current.closest(`[${TOOLTIP_TRIGGER_IDENTIFIER}]`);
		if (trigger) return trigger;
		const root = current.getRootNode();
		current = "host" in root && isElement(root.host) ? root.host : null;
	}
	return null;
}
/**
* An element to attach the tooltip to.
* Renders a `<button>` element.
*
* Documentation: [Base UI Tooltip](https://base-ui.com/react/components/tooltip)
*/
var TooltipTrigger$1 = fastComponentRef(function TooltipTrigger(componentProps, forwardedRef) {
	const { render, className, style, handle, payload, disabled: disabledProp, delay, closeOnClick = true, closeDelay, id: idProp, ...elementProps } = componentProps;
	const rootContext = useTooltipRootContext(true);
	const store = usePopupHandleStore(handle) ?? rootContext;
	if (!store) throw new Error(formatErrorMessage(82));
	const thisTriggerId = useBaseUiId(idProp);
	const isTriggerActive = store.useState("isTriggerActive", thisTriggerId);
	const isOpenedByThisTrigger = store.useState("isOpenedByTrigger", thisTriggerId);
	const floatingRootContext = store.useState("floatingRootContext");
	const triggerElementRef = React$3.useRef(null);
	const delayWithDefault = delay ?? 600;
	const closeDelayWithDefault = closeDelay ?? 0;
	const { registerTrigger, isMountedByThisTrigger } = useTriggerDataForwarding(thisTriggerId, triggerElementRef, store, {
		payload,
		closeOnClick,
		closeDelay: closeDelayWithDefault
	});
	const providerDelay = useTooltipProviderContext();
	const { delayRef, isInstantPhase, hasProvider } = useDelayGroup(floatingRootContext, { open: isOpenedByThisTrigger });
	const hoverInteraction = useHoverInteractionSharedState(floatingRootContext);
	store.useSyncedValue("isInstantPhase", isInstantPhase);
	const rootDisabled = store.useState("disabled");
	const disabled = disabledProp ?? rootDisabled;
	const disabledRef = useValueAsRef(disabled);
	const trackCursorAxis = store.useState("trackCursorAxis");
	const disableHoverablePopup = store.useState("disableHoverablePopup");
	const isNestedTriggerHoveredRef = React$3.useRef(false);
	const nestedTriggerOpenTimeout = useTimeout();
	const pointerTypeRef = React$3.useRef(void 0);
	function getOpenDelay() {
		if (!hasProvider) return delayWithDefault;
		return getDelay(delayRef.current, "open") === 0 ? 0 : delay ?? providerDelay ?? 600;
	}
	function isEnabledNestedTriggerTarget(target) {
		const triggerEl = triggerElementRef.current;
		if (!triggerEl || !target) return false;
		const nearestTrigger = closestEnabledTooltipTrigger(target);
		return nearestTrigger !== null && nearestTrigger !== triggerEl && contains(triggerEl, nearestTrigger);
	}
	function detectNestedTriggerHover(target) {
		const nestedTriggerHovered = isEnabledNestedTriggerTarget(target);
		isNestedTriggerHoveredRef.current = nestedTriggerHovered;
		if (nestedTriggerHovered) {
			hoverInteraction.openChangeTimeout.clear();
			hoverInteraction.restTimeout.clear();
			hoverInteraction.restTimeoutPending = false;
			nestedTriggerOpenTimeout.clear();
		}
		return nestedTriggerHovered;
	}
	const hoverProps = useHoverReferenceInteraction(floatingRootContext, {
		enabled: !disabled,
		mouseOnly: true,
		move: false,
		handleClose: !disableHoverablePopup && trackCursorAxis !== "both" ? safePolygon() : null,
		restMs: getOpenDelay,
		delay() {
			if (closeDelay == null && hasProvider) return { close: getDelay(delayRef.current, "close") };
			return { close: closeDelayWithDefault };
		},
		triggerElementRef,
		isActiveTrigger: isTriggerActive,
		isClosing: () => store.select("transitionStatus") === "ending",
		shouldOpen() {
			return !isNestedTriggerHoveredRef.current;
		}
	});
	const focusProps = useFocus(floatingRootContext, { enabled: !disabled }).reference;
	const handleNestedTriggerHover = (event) => {
		const wasNestedTriggerHovered = isNestedTriggerHoveredRef.current;
		const target = getTargetElement(event);
		const nestedTriggerHovered = detectNestedTriggerHover(target);
		const triggerEl = triggerElementRef.current;
		const targetInsideTrigger = triggerEl && target && contains(triggerEl, target);
		if (nestedTriggerHovered && store.select("open") && store.select("lastOpenChangeReason") === "trigger-hover") {
			store.setOpen(false, createChangeEventDetails(triggerHover, event));
			return;
		}
		if (wasNestedTriggerHovered && !nestedTriggerHovered && targetInsideTrigger && !disabledRef.current && !store.select("open") && triggerEl && isMouseLikePointerType(pointerTypeRef.current)) {
			const open = () => {
				if (!isNestedTriggerHoveredRef.current && !disabledRef.current && !store.select("open")) store.setOpen(true, createChangeEventDetails(triggerHover, event, triggerEl));
			};
			const openDelay = getOpenDelay();
			if (openDelay === 0) {
				nestedTriggerOpenTimeout.clear();
				open();
			} else nestedTriggerOpenTimeout.start(openDelay, open);
		}
	};
	const rootTriggerProps = store.useState("triggerProps", isMountedByThisTrigger);
	return useRenderElement("button", componentProps, {
		state: { open: isOpenedByThisTrigger },
		ref: [
			forwardedRef,
			registerTrigger,
			triggerElementRef
		],
		props: [
			hoverProps,
			focusProps,
			isMountedByThisTrigger || trackCursorAxis !== "none" ? rootTriggerProps : void 0,
			{
				onMouseOver(event) {
					handleNestedTriggerHover(event.nativeEvent);
				},
				onFocus(event) {
					if (isEnabledNestedTriggerTarget(getTargetElement(event.nativeEvent))) event.preventBaseUIHandler();
				},
				onMouseLeave() {
					isNestedTriggerHoveredRef.current = false;
					nestedTriggerOpenTimeout.clear();
					pointerTypeRef.current = void 0;
				},
				onPointerEnter(event) {
					pointerTypeRef.current = event.pointerType;
				},
				onPointerDown(event) {
					pointerTypeRef.current = event.pointerType;
					store.set("closeOnClick", closeOnClick);
					if (closeOnClick && !store.select("open")) store.cancelPendingOpen(event.nativeEvent);
				},
				onClick(event) {
					if (closeOnClick && !store.select("open")) store.cancelPendingOpen(event.nativeEvent);
				},
				id: thisTriggerId,
				"data-trigger-disabled": disabled ? "" : void 0,
				[TOOLTIP_TRIGGER_IDENTIFIER]: disabled ? void 0 : ""
			},
			elementProps
		],
		stateAttributesMapping: triggerOpenStateMapping
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/tooltip/portal/TooltipPortalContext.mjs
var TooltipPortalContext = /* @__PURE__ */ React$3.createContext(void 0);
function useTooltipPortalContext() {
	const value = React$3.useContext(TooltipPortalContext);
	if (value === void 0) throw new Error(formatErrorMessage(70));
	return value;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/FloatingPortalLite.mjs
/**
* `FloatingPortal` includes tabbable logic handling for focus management.
* For components that don't need tabbable logic, use `FloatingPortalLite`.
* @internal
*/
var FloatingPortalLite = /* @__PURE__ */ React$3.forwardRef(function FloatingPortalLite(componentProps, forwardedRef) {
	const { children, container, className, render, style, ...elementProps } = componentProps;
	const { node: portalNode, subtree: portalSubtree } = useFloatingPortalNode({
		container,
		ref: forwardedRef,
		componentProps,
		elementProps
	});
	if (!portalSubtree && !portalNode) return null;
	return /* @__PURE__ */ jsxs(React$3.Fragment, { children: [portalSubtree, portalNode && /* @__PURE__ */ ReactDOM.createPortal(children, portalNode)] });
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/tooltip/portal/TooltipPortal.mjs
/**
* A portal element that moves the popup to a different part of the DOM.
* By default, the portal element is appended to `<body>`.
* Renders a `<div>` element.
*
* Documentation: [Base UI Tooltip](https://base-ui.com/react/components/tooltip)
*/
var TooltipPortal = /* @__PURE__ */ React$3.forwardRef(function TooltipPortal(props, forwardedRef) {
	const { keepMounted = false, ...portalProps } = props;
	if (!(useTooltipRootContext().useState("mounted") || keepMounted)) return null;
	return /* @__PURE__ */ jsx(TooltipPortalContext.Provider, {
		value: keepMounted,
		children: /* @__PURE__ */ jsx(FloatingPortalLite, {
			ref: forwardedRef,
			...portalProps
		})
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/tooltip/positioner/TooltipPositionerContext.mjs
var TooltipPositionerContext = /* @__PURE__ */ React$3.createContext(void 0);
function useTooltipPositionerContext() {
	const context = React$3.useContext(TooltipPositionerContext);
	if (context === void 0) throw new Error(formatErrorMessage(71));
	return context;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/direction-context/DirectionContext.mjs
var DirectionContext = /* @__PURE__ */ React$3.createContext(void 0);
function useDirection() {
	return React$3.useContext(DirectionContext)?.direction ?? "ltr";
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/floating-ui-react/middleware/arrow.mjs
/**
* Fork of the original `arrow` middleware from Floating UI that allows
* configuring the offset parent.
*/
var baseArrow = (options) => ({
	name: "arrow",
	options,
	async fn(state) {
		const { x, y, placement, rects, platform, elements, middlewareData } = state;
		const { element, padding = 0, offsetParent = "real" } = evaluate(options, state) || {};
		if (element == null) return {};
		const paddingObject = getPaddingObject(padding);
		const coords = {
			x,
			y
		};
		const axis = getAlignmentAxis(placement);
		const length = getAxisLength(axis);
		const arrowDimensions = await platform.getDimensions(element);
		const isYAxis = axis === "y";
		const minProp = isYAxis ? "top" : "left";
		const maxProp = isYAxis ? "bottom" : "right";
		const clientProp = isYAxis ? "clientHeight" : "clientWidth";
		const endDiff = rects.reference[length] + rects.reference[axis] - coords[axis] - rects.floating[length];
		const startDiff = coords[axis] - rects.reference[axis];
		const arrowOffsetParent = offsetParent === "real" ? await platform.getOffsetParent?.(element) : elements.floating;
		let clientSize = elements.floating[clientProp] || rects.floating[length];
		if (!clientSize || !await platform.isElement?.(arrowOffsetParent)) clientSize = elements.floating[clientProp] || rects.floating[length];
		const centerToReference = endDiff / 2 - startDiff / 2;
		const largestPossiblePadding = clientSize / 2 - arrowDimensions[length] / 2 - 1;
		const minPadding = Math.min(paddingObject[minProp], largestPossiblePadding);
		const maxPadding = Math.min(paddingObject[maxProp], largestPossiblePadding);
		const min = minPadding;
		const max = clientSize - arrowDimensions[length] - maxPadding;
		const center = clientSize / 2 - arrowDimensions[length] / 2 + centerToReference;
		const offset = clamp$1(min, center, max);
		const shouldAddOffset = !middlewareData.arrow && getAlignment(placement) != null && center !== offset && rects.reference[length] / 2 - (center < min ? minPadding : maxPadding) - arrowDimensions[length] / 2 < 0;
		const alignmentOffset = shouldAddOffset ? center < min ? center - min : center - max : 0;
		return {
			[axis]: coords[axis] + alignmentOffset,
			data: {
				[axis]: offset,
				centerOffset: center - offset - alignmentOffset,
				...shouldAddOffset && { alignmentOffset }
			},
			reset: shouldAddOffset
		};
	}
});
/**
* Provides data to position an inner element of the floating element so that it
* appears centered to the reference element.
* This wraps the core `arrow` middleware to allow React refs as the element.
* @see https://floating-ui.com/docs/arrow
*/
var arrow = (options, deps) => ({
	...baseArrow(options),
	options: [options, deps]
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/hideMiddleware.mjs
var hide = {
	name: "hide",
	async fn(state) {
		const { width, height, x, y } = state.rects.reference;
		const anchorHidden = width === 0 && height === 0 && x === 0 && y === 0;
		const overflow = await state.platform.detectOverflow(state, { elementContext: "reference" });
		return { data: { referenceHidden: overflow.top - height >= 0 || overflow.right - width >= 0 || overflow.bottom - height >= 0 || overflow.left - width >= 0 || anchorHidden } };
	}
};
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/adaptiveOriginConstants.mjs
var DEFAULT_SIDES = {
	sideX: "left",
	sideY: "top"
};
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/useAnchorPositioning.mjs
var AVAILABLE_WIDTH_VAR = "--available-width";
var AVAILABLE_HEIGHT_VAR = "--available-height";
function getLogicalSide(sideParam, renderedSide, isRtl) {
	const isLogicalSideParam = sideParam === "inline-start" || sideParam === "inline-end";
	return {
		top: "top",
		right: isLogicalSideParam ? isRtl ? "inline-start" : "inline-end" : "right",
		bottom: "bottom",
		left: isLogicalSideParam ? isRtl ? "inline-end" : "inline-start" : "left"
	}[renderedSide];
}
function getOffsetData(state, sideParam, isRtl) {
	const { rects, placement } = state;
	return {
		side: getLogicalSide(sideParam, getSide(placement), isRtl),
		align: getAlignment(placement) || "center",
		anchor: {
			width: rects.reference.width,
			height: rects.reference.height
		},
		positioner: {
			width: rects.floating.width,
			height: rects.floating.height
		}
	};
}
/**
* Provides standardized anchor positioning behavior for floating elements. Wraps Floating UI's
* `useFloating` hook.
*/
function useAnchorPositioning(params) {
	return useAnchorPositioningWithHook(params, useBaseUIFloating);
}
function useAnchorPositioningWithHook(params, useFloatingHook) {
	const { anchor, positionMethod = "absolute", side: sideParam = "bottom", sideOffset = 0, align = "center", alignOffset = 0, collisionBoundary, collisionPadding: collisionPaddingParam = 5, sticky = false, arrowPadding = 5, disableAnchorTracking = false, inline: inlineMiddleware, keepMounted = false, floatingRootContext, mounted, collisionAvoidance, shift: shift$3, nodeId, adaptiveOrigin, lazyFlip = false, externalTree } = params;
	const [mountSide, setMountSide] = React$3.useState(null);
	if (!mounted && mountSide !== null) setMountSide(null);
	const collisionAvoidanceSide = collisionAvoidance.side || "flip";
	const collisionAvoidanceAlign = collisionAvoidance.align || "flip";
	const collisionAvoidanceFallbackAxisSide = collisionAvoidance.fallbackAxisSide || "end";
	const shiftCrossAxis = shift$3?.crossAxis ?? false;
	const shiftRootBoundary = shift$3?.rootBoundary;
	const anchorFn = typeof anchor === "function" ? anchor : void 0;
	const anchorFnCallback = useStableCallback(anchorFn);
	const anchorDep = anchorFn ? anchorFnCallback : anchor;
	const anchorValueRef = useValueAsRef(anchor);
	const mountedRef = useValueAsRef(mounted);
	const isRtl = useDirection() === "rtl";
	const side = mountSide || {
		top: "top",
		right: "right",
		bottom: "bottom",
		left: "left",
		"inline-end": isRtl ? "left" : "right",
		"inline-start": isRtl ? "right" : "left"
	}[sideParam];
	const placement = align === "center" ? side : `${side}-${align}`;
	let collisionPadding = collisionPaddingParam;
	if (typeof collisionPadding === "number") collisionPadding = {
		top: collisionPadding,
		right: collisionPadding,
		bottom: collisionPadding,
		left: collisionPadding
	};
	else if (collisionPadding) collisionPadding = {
		top: collisionPadding.top || 0,
		right: collisionPadding.right || 0,
		bottom: collisionPadding.bottom || 0,
		left: collisionPadding.left || 0
	};
	const bias = 1;
	const biasTop = sideParam === "bottom" ? bias : 0;
	const biasBottom = sideParam === "top" ? bias : 0;
	const biasLeft = sideParam === "right" ? bias : 0;
	const biasRight = sideParam === "left" ? bias : 0;
	const commonCollisionProps = {
		boundary: collisionBoundary === "clipping-ancestors" ? "clippingAncestors" : collisionBoundary,
		padding: collisionPadding
	};
	const arrowRef = React$3.useRef(null);
	const sideOffsetRef = useValueAsRef(sideOffset);
	const alignOffsetRef = useValueAsRef(alignOffset);
	const sideOffsetDep = typeof sideOffset !== "function" ? sideOffset : 0;
	const alignOffsetDep = typeof alignOffset !== "function" ? alignOffset : 0;
	const middleware = [];
	if (inlineMiddleware) middleware.push(inlineMiddleware);
	middleware.push(offset((state) => {
		const data = getOffsetData(state, sideParam, isRtl);
		const sideAxis = typeof sideOffsetRef.current === "function" ? sideOffsetRef.current(data) : sideOffsetRef.current;
		const alignAxis = typeof alignOffsetRef.current === "function" ? alignOffsetRef.current(data) : alignOffsetRef.current;
		return {
			mainAxis: sideAxis,
			crossAxis: alignAxis,
			alignmentAxis: alignAxis
		};
	}, [
		sideOffsetDep,
		alignOffsetDep,
		isRtl,
		sideParam
	]));
	const shiftDisabled = collisionAvoidanceAlign === "none" && collisionAvoidanceSide !== "shift";
	const crossAxisShiftEnabled = !shiftDisabled && (sticky || shiftCrossAxis || collisionAvoidanceSide === "shift");
	const flipMiddleware = collisionAvoidanceSide === "none" ? null : flip({
		...commonCollisionProps,
		padding: {
			top: collisionPadding.top + bias + biasTop,
			right: collisionPadding.right + bias + biasRight,
			bottom: collisionPadding.bottom + bias + biasBottom,
			left: collisionPadding.left + bias + biasLeft
		},
		mainAxis: !shiftCrossAxis && collisionAvoidanceSide === "flip",
		crossAxis: collisionAvoidanceAlign === "flip" ? "alignment" : false,
		fallbackAxisSideDirection: collisionAvoidanceFallbackAxisSide
	});
	const shiftMiddleware = shiftDisabled ? null : shift({
		...commonCollisionProps,
		rootBoundary: shiftRootBoundary,
		mainAxis: collisionAvoidanceAlign !== "none",
		crossAxis: crossAxisShiftEnabled,
		limiter: sticky || shiftCrossAxis ? void 0 : limitShift((limitData) => {
			if (!arrowRef.current) return {};
			const { width, height } = arrowRef.current.getBoundingClientRect();
			const sideAxis = getSideAxis(getSide(limitData.placement));
			const arrowSize = sideAxis === "y" ? width : height;
			const offsetAmount = sideAxis === "y" ? collisionPadding.left + collisionPadding.right : collisionPadding.top + collisionPadding.bottom;
			return { offset: arrowSize / 2 + offsetAmount / 2 };
		})
	}, [
		commonCollisionProps,
		sticky,
		shiftCrossAxis,
		shiftRootBoundary,
		collisionPadding,
		collisionAvoidanceAlign
	]);
	if (collisionAvoidanceSide === "shift" || collisionAvoidanceAlign === "shift" || align === "center") middleware.push(shiftMiddleware, flipMiddleware);
	else middleware.push(flipMiddleware, shiftMiddleware);
	middleware.push(size({
		...commonCollisionProps,
		apply({ elements: { floating }, availableWidth, availableHeight, rects }) {
			if (!mountedRef.current) return;
			const floatingStyle = floating.style;
			floatingStyle.setProperty(AVAILABLE_WIDTH_VAR, `${availableWidth}px`);
			floatingStyle.setProperty(AVAILABLE_HEIGHT_VAR, `${availableHeight}px`);
			const dpr = getWindow(floating).devicePixelRatio || 1;
			const { x, y, width, height } = rects.reference;
			const anchorWidth = (Math.round((x + width) * dpr) - Math.round(x * dpr)) / dpr;
			const anchorHeight = (Math.round((y + height) * dpr) - Math.round(y * dpr)) / dpr;
			floatingStyle.setProperty("--anchor-width", `${anchorWidth}px`);
			floatingStyle.setProperty("--anchor-height", `${anchorHeight}px`);
		}
	}), arrow((state) => ({
		element: arrowRef.current || ownerDocument(state.elements.floating).createElement("div"),
		padding: arrowPadding,
		offsetParent: "floating"
	}), [arrowPadding]), {
		name: "transformOrigin",
		fn(state) {
			const { elements, middlewareData, placement: renderedPlacement, rects, y } = state;
			const currentRenderedSide = getSide(renderedPlacement);
			const currentRenderedAxis = getSideAxis(currentRenderedSide);
			const arrowEl = arrowRef.current;
			const arrowX = middlewareData.arrow?.x || 0;
			const arrowY = middlewareData.arrow?.y || 0;
			const arrowWidth = arrowEl?.clientWidth || 0;
			const arrowHeight = arrowEl?.clientHeight || 0;
			const transformX = arrowX + arrowWidth / 2;
			const transformY = arrowY + arrowHeight / 2;
			const shiftY = Math.abs(middlewareData.shift?.y || 0);
			const halfAnchorHeight = rects.reference.height / 2;
			const sideOffsetValue = typeof sideOffset === "function" ? sideOffset(getOffsetData(state, sideParam, isRtl)) : sideOffset;
			const isOverlappingAnchor = shiftY > sideOffsetValue;
			const adjacentTransformOrigin = {
				top: `${transformX}px calc(100% + ${sideOffsetValue}px)`,
				bottom: `${transformX}px ${-sideOffsetValue}px`,
				left: `calc(100% + ${sideOffsetValue}px) ${transformY}px`,
				right: `${-sideOffsetValue}px ${transformY}px`
			}[currentRenderedSide];
			const overlapTransformOrigin = `${transformX}px ${rects.reference.y + halfAnchorHeight - y}px`;
			elements.floating.style.setProperty("--transform-origin", crossAxisShiftEnabled && currentRenderedAxis === "y" && isOverlappingAnchor ? overlapTransformOrigin : adjacentTransformOrigin);
			return {};
		}
	}, hide, adaptiveOrigin);
	useIsoLayoutEffect(() => {
		if (!mounted && floatingRootContext) floatingRootContext.update({
			referenceElement: null,
			floatingElement: null,
			domReferenceElement: null,
			positionReference: null
		});
	}, [mounted, floatingRootContext]);
	const autoUpdateOptions = React$3.useMemo(() => ({
		elementResize: !disableAnchorTracking && typeof ResizeObserver !== "undefined",
		layoutShift: !disableAnchorTracking && typeof IntersectionObserver !== "undefined"
	}), [disableAnchorTracking]);
	const { refs, elements, x, y, middlewareData, update, placement: renderedPlacement, context, isPositioned, floatingStyles: originalFloatingStyles } = useFloatingHook({
		rootContext: floatingRootContext,
		open: keepMounted ? mounted : void 0,
		placement,
		middleware,
		strategy: positionMethod,
		whileElementsMounted: keepMounted ? void 0 : (...args) => autoUpdate(...args, autoUpdateOptions),
		nodeId,
		externalTree
	});
	const { sideX, sideY } = middlewareData.adaptiveOrigin || DEFAULT_SIDES;
	const resolvedPosition = isPositioned ? positionMethod : "fixed";
	const floatingStyles = React$3.useMemo(() => {
		let base;
		if (!isPositioned) base = {
			position: resolvedPosition,
			top: 0,
			left: 0
		};
		else if (adaptiveOrigin) base = {
			position: resolvedPosition,
			[sideX]: x,
			[sideY]: y
		};
		else base = {
			...originalFloatingStyles,
			position: resolvedPosition
		};
		base[AVAILABLE_WIDTH_VAR] = "100vw";
		base[AVAILABLE_HEIGHT_VAR] = "100vh";
		if (!isPositioned) base.opacity = 0;
		return base;
	}, [
		adaptiveOrigin,
		resolvedPosition,
		sideX,
		x,
		sideY,
		y,
		originalFloatingStyles,
		isPositioned
	]);
	const registeredPositionReferenceRef = React$3.useRef(null);
	useIsoLayoutEffect(() => {
		if (!mounted) return;
		const anchorValue = anchorValueRef.current;
		const resolvedAnchor = typeof anchorValue === "function" ? anchorValue() : anchorValue;
		const finalAnchor = (isRef(resolvedAnchor) ? resolvedAnchor.current : resolvedAnchor) || null;
		if (finalAnchor !== registeredPositionReferenceRef.current) {
			refs.setPositionReference(finalAnchor);
			registeredPositionReferenceRef.current = finalAnchor;
		}
	}, [
		mounted,
		refs,
		anchorDep,
		anchorValueRef
	]);
	React$3.useEffect(() => {
		if (!mounted) return;
		const anchorValue = anchorValueRef.current;
		if (typeof anchorValue === "function") return;
		if (isRef(anchorValue) && anchorValue.current !== registeredPositionReferenceRef.current) {
			refs.setPositionReference(anchorValue.current);
			registeredPositionReferenceRef.current = anchorValue.current;
		}
	}, [
		mounted,
		refs,
		anchorDep,
		anchorValueRef
	]);
	React$3.useEffect(() => {
		if (keepMounted && mounted && elements.reference && elements.floating) return autoUpdate(elements.reference, elements.floating, update, autoUpdateOptions);
	}, [
		keepMounted,
		mounted,
		elements,
		update,
		autoUpdateOptions
	]);
	const renderedSide = getSide(renderedPlacement);
	const logicalRenderedSide = getLogicalSide(sideParam, renderedSide, isRtl);
	const renderedAlign = getAlignment(renderedPlacement) || "center";
	const anchorHidden = Boolean(middlewareData.hide?.referenceHidden);
	useIsoLayoutEffect(() => {
		if (lazyFlip && mounted && isPositioned && renderedSide !== side) setMountSide(renderedSide);
	}, [
		lazyFlip,
		mounted,
		isPositioned,
		renderedSide,
		side
	]);
	const arrowStyles = React$3.useMemo(() => ({
		position: "absolute",
		top: middlewareData.arrow?.y,
		left: middlewareData.arrow?.x
	}), [middlewareData.arrow]);
	const arrowUncentered = middlewareData.arrow?.centerOffset !== 0;
	return React$3.useMemo(() => ({
		positionerStyles: floatingStyles,
		arrowStyles,
		arrowRef,
		arrowUncentered,
		side: logicalRenderedSide,
		align: renderedAlign,
		physicalSide: renderedSide,
		anchorHidden,
		refs,
		context,
		isPositioned,
		update
	}), [
		floatingStyles,
		arrowStyles,
		arrowRef,
		arrowUncentered,
		logicalRenderedSide,
		renderedAlign,
		renderedSide,
		anchorHidden,
		refs,
		context,
		isPositioned,
		update
	]);
}
function isRef(param) {
	return param != null && "current" in param;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/getDisabledMountTransitionStyles.mjs
function getDisabledMountTransitionStyles(transitionStatus) {
	return transitionStatus === "starting" ? DISABLED_TRANSITIONS_STYLE : EMPTY_OBJECT;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/usePositioner.mjs
/**
* Renders the shared outer Positioner element used by popup components.
* Applies the common role, hidden state, transition styles, state attributes, and optional inert styling.
*/
function usePositioner(componentProps, state, { styles, transitionStatus, props, refs, hidden, inert = false }) {
	const style = { ...styles };
	if (inert) style.pointerEvents = "none";
	return useRenderElement("div", componentProps, {
		state,
		ref: refs,
		props: [
			{
				role: "presentation",
				hidden,
				style
			},
			getDisabledMountTransitionStyles(transitionStatus),
			props
		],
		stateAttributesMapping: popupStateMapping
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/tooltip/positioner/TooltipPositioner.mjs
/**
* Positions the tooltip against the trigger.
* Renders a `<div>` element.
*
* Documentation: [Base UI Tooltip](https://base-ui.com/react/components/tooltip)
*/
var TooltipPositioner = /* @__PURE__ */ React$3.forwardRef(function TooltipPositioner(componentProps, forwardedRef) {
	const { render, className, anchor, positionMethod = "absolute", side = "top", align = "center", sideOffset = 0, alignOffset = 0, collisionBoundary = "clipping-ancestors", collisionPadding = 5, arrowPadding = 5, sticky = false, disableAnchorTracking = false, collisionAvoidance = POPUP_COLLISION_AVOIDANCE, style, ...elementProps } = componentProps;
	const store = useTooltipRootContext();
	const keepMounted = useTooltipPortalContext();
	const open = store.useState("open");
	const mounted = store.useState("mounted");
	const trackCursorAxis = store.useState("trackCursorAxis");
	const disableHoverablePopup = store.useState("disableHoverablePopup");
	const floatingRootContext = store.useState("floatingRootContext");
	const instantType = store.useState("instantType");
	const transitionStatus = store.useState("transitionStatus");
	const positioning = useAnchorPositioning({
		anchor,
		positionMethod,
		floatingRootContext,
		mounted,
		side,
		sideOffset,
		align,
		alignOffset,
		collisionBoundary,
		collisionPadding,
		sticky,
		arrowPadding,
		disableAnchorTracking,
		keepMounted,
		collisionAvoidance,
		adaptiveOrigin: store.useState("adaptiveOrigin")
	});
	const element = usePositioner(componentProps, React$3.useMemo(() => ({
		open,
		side: positioning.side,
		align: positioning.align,
		anchorHidden: positioning.anchorHidden,
		instant: trackCursorAxis !== "none" ? "tracking-cursor" : instantType
	}), [
		open,
		positioning.side,
		positioning.align,
		positioning.anchorHidden,
		trackCursorAxis,
		instantType
	]), {
		styles: positioning.positionerStyles,
		transitionStatus,
		props: elementProps,
		refs: [forwardedRef, store.useStateSetter("positionerElement")],
		hidden: !mounted,
		inert: !open || trackCursorAxis === "both" || disableHoverablePopup
	});
	return /* @__PURE__ */ jsx(TooltipPositionerContext.Provider, {
		value: positioning,
		children: element
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/tooltip/popup/TooltipPopup.mjs
/**
* A container for the tooltip contents.
* Renders a `<div>` element.
*
* Documentation: [Base UI Tooltip](https://base-ui.com/react/components/tooltip)
*/
var TooltipPopup = /* @__PURE__ */ React$3.forwardRef(function TooltipPopup(componentProps, forwardedRef) {
	const { render, className, style, ...elementProps } = componentProps;
	const store = useTooltipRootContext();
	const { side, align } = useTooltipPositionerContext();
	const open = store.useState("open");
	const instantType = store.useState("instantType");
	const transitionStatus = store.useState("transitionStatus");
	const popupProps = store.useState("popupProps");
	const floatingContext = store.useState("floatingRootContext");
	const disabled = store.useState("disabled");
	const closeDelay = store.useState("closeDelay");
	useOpenChangeComplete({
		open,
		ref: store.context.popupRef,
		onComplete() {
			if (open) store.context.onOpenChangeComplete?.(true);
		}
	});
	useHoverFloatingInteraction(floatingContext, {
		enabled: !disabled,
		closeDelay
	});
	const setPopupElement = store.useStateSetter("popupElement");
	return useRenderElement("div", componentProps, {
		state: {
			open,
			side,
			align,
			instant: instantType,
			transitionStatus
		},
		ref: [
			forwardedRef,
			store.context.popupRef,
			setPopupElement
		],
		props: [
			FOCUSABLE_POPUP_PROPS,
			popupProps,
			getDisabledMountTransitionStyles(transitionStatus),
			elementProps
		],
		stateAttributesMapping: popupTransitionStateMapping
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/tooltip/arrow/TooltipArrow.mjs
/**
* Displays an element positioned against the tooltip anchor.
* Renders a `<div>` element.
*
* Documentation: [Base UI Tooltip](https://base-ui.com/react/components/tooltip)
*/
var TooltipArrow = /* @__PURE__ */ React$3.forwardRef(function TooltipArrow(componentProps, forwardedRef) {
	const { render, className, style, ...elementProps } = componentProps;
	const store = useTooltipRootContext();
	const { arrowRef, side, align, arrowUncentered, arrowStyles } = useTooltipPositionerContext();
	return useRenderElement("div", componentProps, {
		state: {
			open: store.useState("open"),
			side,
			align,
			uncentered: arrowUncentered,
			instant: store.useState("instantType")
		},
		ref: [forwardedRef, arrowRef],
		props: [{
			style: arrowStyles,
			"aria-hidden": true
		}, elementProps],
		stateAttributesMapping: popupStateMapping
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/usePreviousValue.mjs
/**
* Returns a previous value of its argument.
* @param value Current value.
* @returns Previous value, or null if there is no previous value.
*/
function usePreviousValue(value) {
	const [state, setState] = React$3.useState({
		current: value,
		previous: null
	});
	if (!Object.is(value, state.current)) setState({
		current: value,
		previous: state.current
	});
	return state.previous;
}
//#endregion
//#region components/ui/tooltip.tsx
function Tooltip({ ...props }) {
	return /* @__PURE__ */ jsx(TooltipRoot, {
		"data-slot": "tooltip",
		...props
	});
}
function TooltipTrigger({ ...props }) {
	return /* @__PURE__ */ jsx(TooltipTrigger$1, {
		"data-slot": "tooltip-trigger",
		...props
	});
}
function TooltipContent({ className, side = "top", sideOffset = 4, align = "center", alignOffset = 0, children, ...props }) {
	return /* @__PURE__ */ jsx(TooltipPortal, { children: /* @__PURE__ */ jsx(TooltipPositioner, {
		align,
		alignOffset,
		side,
		sideOffset,
		className: "isolate z-50",
		children: /* @__PURE__ */ jsxs(TooltipPopup, {
			"data-slot": "tooltip-content",
			className: cn("z-50 inline-flex w-fit max-w-xs origin-(--transform-origin) items-center gap-1.5 rounded-md bg-foreground px-3 py-1.5 text-xs text-background has-data-[slot=kbd]:pr-1.5 data-[side=bottom]:slide-in-from-top-2 data-[side=inline-end]:slide-in-from-left-2 data-[side=inline-start]:slide-in-from-right-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 **:data-[slot=kbd]:relative **:data-[slot=kbd]:isolate **:data-[slot=kbd]:z-50 **:data-[slot=kbd]:rounded-sm data-[state=delayed-open]:animate-in data-[state=delayed-open]:fade-in-0 data-[state=delayed-open]:zoom-in-95 data-open:animate-in data-open:fade-in-0 data-open:zoom-in-95 data-closed:animate-out data-closed:fade-out-0 data-closed:zoom-out-95", className),
			...props,
			children: [children, /* @__PURE__ */ jsx(TooltipArrow, { className: "z-50 size-2.5 translate-y-[calc(-50%-2px)] rotate-45 rounded-[2px] bg-foreground fill-foreground data-[side=bottom]:top-1 data-[side=inline-end]:top-1/2! data-[side=inline-end]:-left-1 data-[side=inline-end]:-translate-y-1/2 data-[side=inline-start]:top-1/2! data-[side=inline-start]:-right-1 data-[side=inline-start]:-translate-y-1/2 data-[side=left]:top-1/2! data-[side=left]:-right-1 data-[side=left]:-translate-y-1/2 data-[side=right]:top-1/2! data-[side=right]:-left-1 data-[side=right]:-translate-y-1/2 data-[side=top]:-bottom-2.5" })]
		})
	}) });
}
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var PanelLeft = createLucideIcon("panel-left", [["rect", {
	width: "18",
	height: "18",
	x: "3",
	y: "3",
	rx: "2",
	key: "afitv7"
}], ["path", {
	d: "M9 3v18",
	key: "fh3hqa"
}]]);
//#endregion
//#region components/ui/sidebar.tsx
var SIDEBAR_COOKIE_NAME = "sidebar_state";
var SIDEBAR_COOKIE_MAX_AGE = 3600 * 24 * 7;
var SIDEBAR_WIDTH = "16rem";
var SIDEBAR_WIDTH_MOBILE = "18rem";
var SIDEBAR_WIDTH_ICON = "3rem";
var SIDEBAR_KEYBOARD_SHORTCUT = "b";
var SidebarContext = React$3.createContext(null);
function useSidebar() {
	const context = React$3.useContext(SidebarContext);
	if (!context) throw new Error("useSidebar must be used within a SidebarProvider.");
	return context;
}
function SidebarProvider({ defaultOpen = true, open: openProp, onOpenChange: setOpenProp, className, style, children, ...props }) {
	const isMobile = useIsMobile();
	const [openMobile, setOpenMobile] = React$3.useState(false);
	const [_open, _setOpen] = React$3.useState(defaultOpen);
	const open = openProp ?? _open;
	const setOpen = React$3.useCallback((value) => {
		const openState = typeof value === "function" ? value(open) : value;
		if (setOpenProp) setOpenProp(openState);
		else _setOpen(openState);
		document.cookie = `${SIDEBAR_COOKIE_NAME}=${openState}; path=/; max-age=${SIDEBAR_COOKIE_MAX_AGE}`;
	}, [setOpenProp, open]);
	const toggleSidebar = React$3.useCallback(() => {
		return isMobile ? setOpenMobile((open) => !open) : setOpen((open) => !open);
	}, [
		isMobile,
		setOpen,
		setOpenMobile
	]);
	React$3.useEffect(() => {
		const handleKeyDown = (event) => {
			if (event.key === SIDEBAR_KEYBOARD_SHORTCUT && (event.metaKey || event.ctrlKey)) {
				event.preventDefault();
				toggleSidebar();
			}
		};
		window.addEventListener("keydown", handleKeyDown);
		return () => window.removeEventListener("keydown", handleKeyDown);
	}, [toggleSidebar]);
	const state = open ? "expanded" : "collapsed";
	const contextValue = React$3.useMemo(() => ({
		state,
		open,
		setOpen,
		isMobile,
		openMobile,
		setOpenMobile,
		toggleSidebar
	}), [
		state,
		open,
		setOpen,
		isMobile,
		openMobile,
		setOpenMobile,
		toggleSidebar
	]);
	return /* @__PURE__ */ jsx(SidebarContext.Provider, {
		value: contextValue,
		children: /* @__PURE__ */ jsx("div", {
			"data-slot": "sidebar-wrapper",
			style: {
				"--sidebar-width": SIDEBAR_WIDTH,
				"--sidebar-width-icon": SIDEBAR_WIDTH_ICON,
				...style
			},
			className: cn("group/sidebar-wrapper flex min-h-svh w-full has-data-[variant=inset]:bg-sidebar", className),
			...props,
			children
		})
	});
}
function Sidebar({ side = "left", variant = "sidebar", collapsible = "offcanvas", className, children, dir, ...props }) {
	const { isMobile, state, openMobile, setOpenMobile } = useSidebar();
	if (collapsible === "none") return /* @__PURE__ */ jsx("div", {
		"data-slot": "sidebar",
		className: cn("flex h-full w-(--sidebar-width) flex-col bg-sidebar text-sidebar-foreground", className),
		...props,
		children
	});
	if (isMobile) return /* @__PURE__ */ jsx(Sheet, {
		open: openMobile,
		onOpenChange: setOpenMobile,
		...props,
		children: /* @__PURE__ */ jsxs(SheetContent, {
			dir,
			"data-sidebar": "sidebar",
			"data-slot": "sidebar",
			"data-mobile": "true",
			className: "w-(--sidebar-width) bg-sidebar p-0 text-sidebar-foreground [&>button]:hidden",
			style: { "--sidebar-width": SIDEBAR_WIDTH_MOBILE },
			side,
			children: [/* @__PURE__ */ jsxs(SheetHeader, {
				className: "sr-only",
				children: [/* @__PURE__ */ jsx(SheetTitle, { children: "Sidebar" }), /* @__PURE__ */ jsx(SheetDescription, { children: "Displays the mobile sidebar." })]
			}), /* @__PURE__ */ jsx("div", {
				className: "flex h-full w-full flex-col",
				children
			})]
		})
	});
	return /* @__PURE__ */ jsxs("div", {
		className: "group peer hidden text-sidebar-foreground md:block",
		"data-state": state,
		"data-collapsible": state === "collapsed" ? collapsible : "",
		"data-variant": variant,
		"data-side": side,
		"data-slot": "sidebar",
		children: [/* @__PURE__ */ jsx("div", {
			"data-slot": "sidebar-gap",
			className: cn("transition-[width] duration-200 ease-linear relative w-(--sidebar-width) bg-transparent", "group-data-[collapsible=offcanvas]:w-0", "group-data-[side=right]:rotate-180", variant === "floating" || variant === "inset" ? "group-data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)+(--spacing(4)))]" : "group-data-[collapsible=icon]:w-(--sidebar-width-icon)")
		}), /* @__PURE__ */ jsx("div", {
			"data-slot": "sidebar-container",
			"data-side": side,
			className: cn("fixed inset-y-0 z-10 hidden h-svh w-(--sidebar-width) transition-[left,right,width] duration-200 ease-linear data-[side=left]:left-0 data-[side=left]:group-data-[collapsible=offcanvas]:left-[calc(var(--sidebar-width)*-1)] data-[side=right]:right-0 data-[side=right]:group-data-[collapsible=offcanvas]:right-[calc(var(--sidebar-width)*-1)] md:flex", variant === "floating" || variant === "inset" ? "p-2 group-data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)+(--spacing(4))+2px)]" : "group-data-[collapsible=icon]:w-(--sidebar-width-icon) group-data-[side=left]:border-r group-data-[side=right]:border-l", className),
			...props,
			children: /* @__PURE__ */ jsx("div", {
				"data-sidebar": "sidebar",
				"data-slot": "sidebar-inner",
				className: "bg-sidebar group-data-[variant=floating]:ring-sidebar-border group-data-[variant=floating]:rounded-lg group-data-[variant=floating]:shadow-sm group-data-[variant=floating]:ring-1 flex size-full flex-col",
				children
			})
		})]
	});
}
function SidebarTrigger({ className, onClick, ...props }) {
	const { toggleSidebar } = useSidebar();
	return /* @__PURE__ */ jsxs(Button, {
		"data-sidebar": "trigger",
		"data-slot": "sidebar-trigger",
		variant: "ghost",
		size: "icon-sm",
		className: cn(className),
		onClick: (event) => {
			onClick?.(event);
			toggleSidebar();
		},
		...props,
		children: [/* @__PURE__ */ jsx(PanelLeft, { className: "cn-rtl-flip" }), /* @__PURE__ */ jsx("span", {
			className: "sr-only",
			children: "Toggle Sidebar"
		})]
	});
}
function SidebarHeader({ className, ...props }) {
	return /* @__PURE__ */ jsx("div", {
		"data-slot": "sidebar-header",
		"data-sidebar": "header",
		className: cn("gap-2 p-2 flex flex-col", className),
		...props
	});
}
function SidebarFooter({ className, ...props }) {
	return /* @__PURE__ */ jsx("div", {
		"data-slot": "sidebar-footer",
		"data-sidebar": "footer",
		className: cn("gap-2 p-2 flex flex-col", className),
		...props
	});
}
function SidebarContent({ className, ...props }) {
	return /* @__PURE__ */ jsx("div", {
		"data-slot": "sidebar-content",
		"data-sidebar": "content",
		className: cn("no-scrollbar gap-0 flex min-h-0 flex-1 flex-col overflow-auto group-data-[collapsible=icon]:overflow-hidden", className),
		...props
	});
}
function SidebarMenu({ className, ...props }) {
	return /* @__PURE__ */ jsx("ul", {
		"data-slot": "sidebar-menu",
		"data-sidebar": "menu",
		className: cn("gap-0 flex w-full min-w-0 flex-col", className),
		...props
	});
}
function SidebarMenuItem({ className, ...props }) {
	return /* @__PURE__ */ jsx("li", {
		"data-slot": "sidebar-menu-item",
		"data-sidebar": "menu-item",
		className: cn("group/menu-item relative", className),
		...props
	});
}
var sidebarMenuButtonVariants = cva("ring-sidebar-ring hover:bg-sidebar-accent hover:text-sidebar-accent-foreground active:bg-sidebar-accent active:text-sidebar-accent-foreground data-active:bg-sidebar-accent data-active:text-sidebar-accent-foreground data-open:hover:bg-sidebar-accent data-open:hover:text-sidebar-accent-foreground gap-2 rounded-md p-2 text-left text-sm transition-[width,height,padding] group-has-data-[sidebar=menu-action]/menu-item:pr-8 group-data-[collapsible=icon]:size-8! group-data-[collapsible=icon]:p-2! focus-visible:ring-2 data-active:font-medium peer/menu-button group/menu-button flex w-full items-center overflow-hidden outline-hidden disabled:pointer-events-none disabled:opacity-50 aria-disabled:pointer-events-none aria-disabled:opacity-50 [&_svg]:size-4 [&_svg]:shrink-0 [&>span:last-child]:truncate", {
	variants: {
		variant: {
			default: "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
			outline: "bg-background hover:bg-sidebar-accent hover:text-sidebar-accent-foreground shadow-[0_0_0_1px_var(--sidebar-border)] hover:shadow-[0_0_0_1px_var(--sidebar-accent)]"
		},
		size: {
			default: "h-8 text-sm",
			sm: "h-7 text-xs",
			lg: "h-12 text-sm group-data-[collapsible=icon]:p-0!"
		}
	},
	defaultVariants: {
		variant: "default",
		size: "default"
	}
});
function SidebarMenuButton({ render, isActive = false, variant = "default", size = "default", tooltip, className, ...props }) {
	const { isMobile, state } = useSidebar();
	const comp = useRender({
		defaultTagName: "button",
		props: mergeProps({ className: cn(sidebarMenuButtonVariants({
			variant,
			size
		}), className) }, props),
		render: !tooltip ? render : /* @__PURE__ */ jsx(TooltipTrigger, { render }),
		state: {
			slot: "sidebar-menu-button",
			sidebar: "menu-button",
			size,
			active: isActive
		}
	});
	if (!tooltip) return comp;
	if (typeof tooltip === "string") tooltip = { children: tooltip };
	return /* @__PURE__ */ jsxs(Tooltip, { children: [comp, /* @__PURE__ */ jsx(TooltipContent, {
		side: "right",
		align: "center",
		hidden: state !== "collapsed" || isMobile,
		...tooltip
	})] });
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/composite/list/CompositeListContext.mjs
var CompositeListContext = /* @__PURE__ */ React$3.createContext({
	register: () => {},
	unregister: () => {},
	subscribeMapChange: () => () => {},
	nextIndexRef: { current: 0 }
});
function useCompositeListContext() {
	return React$3.useContext(CompositeListContext);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/composite/list/CompositeList.mjs
/**
* Provides context for a list of items in a composite component.
*/
function CompositeList(props) {
	const { children, elementsRef, labelsRef, onMapChange: onMapChangeProp } = props;
	const onMapChange = useStableCallback(onMapChangeProp);
	const [, setMapTick] = React$3.useState(false);
	const listeners = useRefWithInit(createListeners).current;
	const map = useRefWithInit(createMap).current;
	const nextIndexRef = React$3.useRef(0);
	const isDirtyRef = React$3.useRef(true);
	const itemsRef = React$3.useRef([]);
	const mutationObserverRef = React$3.useRef(null);
	const scheduleMapUpdate = useStableCallback(() => {
		if (isDirtyRef.current) return;
		isDirtyRef.current = true;
		setMapTick((tick) => !tick);
	});
	const register = useStableCallback((node, registration) => {
		map.set(node, registration);
		scheduleMapUpdate();
	});
	const unregister = useStableCallback((node) => {
		map.delete(node);
		scheduleMapUpdate();
	});
	const syncRefs = useStableCallback((items) => {
		const nextMap = /* @__PURE__ */ new Map();
		elementsRef.current.length = 0;
		if (labelsRef) labelsRef.current.length = 0;
		items.forEach((item) => {
			nextMap.set(item.element, {
				...item.registration.metadata ?? {},
				index: item.index
			});
			elementsRef.current[item.index] = item.element;
			if (labelsRef) labelsRef.current[item.index] = item.registration.label !== void 0 ? item.registration.label : item.registration.textRef?.current?.textContent ?? item.element.textContent;
		});
		nextIndexRef.current = elementsRef.current.length;
		return nextMap;
	});
	function observe(sortedNodes) {
		mutationObserverRef.current?.disconnect();
		mutationObserverRef.current = null;
		if (typeof MutationObserver !== "function" || sortedNodes.length < 2) return;
		const mutationObserver = new MutationObserver((entries) => {
			if (!hasMovedNode(entries)) return;
			let previousConnectedNode = null;
			for (const node of sortedNodes) {
				if (!node.isConnected) continue;
				if (previousConnectedNode && sortByDocumentPosition(previousConnectedNode, node) > 0) {
					mutationObserver.disconnect();
					scheduleMapUpdate();
					return;
				}
				previousConnectedNode = node;
			}
		});
		mutationObserverRef.current = mutationObserver;
		const roots = /* @__PURE__ */ new Set();
		for (let i = 1; i < sortedNodes.length; i += 1) {
			const root = getCommonAncestor(sortedNodes[i - 1], sortedNodes[i]);
			if (root) roots.add(root);
		}
		roots.forEach((root) => mutationObserver.observe(root, { childList: true }));
	}
	const flush = useStableCallback(() => {
		const [items, automaticNodes] = getCompositeListSnapshot(map);
		const nextMap = syncRefs(items);
		observe(automaticNodes);
		itemsRef.current = items;
		isDirtyRef.current = false;
		listeners.forEach((listener) => listener(nextMap));
		onMapChange(nextMap);
	});
	useIsoLayoutEffect(() => {
		if (!isDirtyRef.current) syncRefs(itemsRef.current);
		return () => {
			elementsRef.current = [];
			if (labelsRef) labelsRef.current = [];
		};
	}, [
		elementsRef,
		labelsRef,
		syncRefs
	]);
	useIsoLayoutEffect(() => {
		if (isDirtyRef.current) flush();
	});
	useIsoLayoutEffect(() => {
		return () => {
			mutationObserverRef.current?.disconnect();
			isDirtyRef.current = true;
		};
	}, []);
	const subscribeMapChange = useStableCallback((fn) => {
		listeners.add(fn);
		return () => {
			listeners.delete(fn);
		};
	});
	const contextValue = React$3.useMemo(() => ({
		register,
		unregister,
		subscribeMapChange,
		nextIndexRef
	}), [
		register,
		unregister,
		subscribeMapChange,
		nextIndexRef
	]);
	return /* @__PURE__ */ jsx(CompositeListContext.Provider, {
		value: contextValue,
		children
	});
}
function createMap() {
	return /* @__PURE__ */ new Map();
}
function createListeners() {
	return /* @__PURE__ */ new Set();
}
function getCompositeListSnapshot(map) {
	const reservedIndices = /* @__PURE__ */ new Set();
	const items = [];
	const automaticItems = [];
	map.forEach((registration, node) => {
		if (!node.isConnected) return;
		const index = registration.index;
		const item = {
			index: index ?? -1,
			element: node,
			registration
		};
		if (index === null) automaticItems.push(item);
		else if (index >= 0) {
			reservedIndices.add(index);
			items.push(item);
		}
	});
	let nextAutomaticIndex = 0;
	automaticItems.sort((a, b) => sortByDocumentPosition(a.element, b.element));
	automaticItems.forEach((item) => {
		while (reservedIndices.has(nextAutomaticIndex)) nextAutomaticIndex += 1;
		item.index = nextAutomaticIndex;
		items.push(item);
		nextAutomaticIndex += 1;
	});
	if (reservedIndices.size > 0) items.sort((a, b) => a.index - b.index);
	return [items, automaticItems.map((item) => item.element)];
}
function getCommonAncestor(firstNode, lastNode) {
	let ancestor = firstNode.parentElement;
	while (ancestor && !ancestor.contains(lastNode)) ancestor = ancestor.parentElement;
	return ancestor;
}
function hasMovedNode(entries) {
	for (const entry of entries) for (let i = 0; i < entry.removedNodes.length; i += 1) if (entry.removedNodes[i].isConnected) return true;
	return false;
}
function sortByDocumentPosition(a, b) {
	return a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/tabs/root/TabsRootContext.mjs
/**
* @internal
*/
var TabsRootContext = /* @__PURE__ */ React$3.createContext(void 0);
function useTabsRootContext() {
	const context = React$3.useContext(TabsRootContext);
	if (context === void 0) throw new Error(formatErrorMessage(64));
	return context;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/tabs/root/stateAttributesMapping.mjs
var tabsStateAttributesMapping = { tabActivationDirection: (dir) => ({ "data-activation-direction": dir }) };
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/tabs/root/TabsRoot.mjs
/**
* Groups the tabs and the corresponding panels.
* Renders a `<div>` element.
*
* Documentation: [Base UI Tabs](https://base-ui.com/react/components/tabs)
*/
var TabsRoot = /* @__PURE__ */ React$3.forwardRef(function TabsRoot(componentProps, forwardedRef) {
	const { className, defaultValue: defaultValueProp = 0, onValueChange: onValueChangeProp, orientation = "horizontal", render, value: valueProp, style, ...elementProps } = componentProps;
	const hasExplicitDefaultValueProp = componentProps.defaultValue !== void 0;
	const tabPanelRefs = React$3.useRef([]);
	const [mountedTabPanels, setMountedTabPanels] = React$3.useState(() => /* @__PURE__ */ new Map());
	const [value, setValue] = useControlled({
		controlled: valueProp,
		default: defaultValueProp,
		name: "Tabs",
		state: "value"
	});
	const isControlled = valueProp !== void 0;
	const [tabMap, setTabMap] = React$3.useState(() => /* @__PURE__ */ new Map());
	const lastKnownTabElementRef = React$3.useRef(void 0);
	const getTabElementBySelectedValue = React$3.useCallback((selectedValue) => findTabElement(tabMap, selectedValue), [tabMap]);
	const [activationDirectionState, setActivationDirectionState] = React$3.useState(() => ({
		previousValue: value,
		tabActivationDirection: "none"
	}));
	const { previousValue, tabActivationDirection: committedTabActivationDirection } = activationDirectionState;
	let tabActivationDirection = committedTabActivationDirection;
	let directionComputationIncomplete = false;
	if (previousValue !== value) {
		tabActivationDirection = computeActivationDirection(previousValue, value, orientation, tabMap);
		directionComputationIncomplete = previousValue != null && value != null && getTabElementBySelectedValue(value) == null;
	}
	const nextPreviousValue = directionComputationIncomplete ? previousValue : value;
	const shouldSyncActivationDirectionState = previousValue !== nextPreviousValue || committedTabActivationDirection !== tabActivationDirection;
	useIsoLayoutEffect(() => {
		if (!shouldSyncActivationDirectionState) return;
		setActivationDirectionState({
			previousValue: nextPreviousValue,
			tabActivationDirection
		});
	}, [
		nextPreviousValue,
		shouldSyncActivationDirectionState,
		tabActivationDirection
	]);
	const onValueChange = useStableCallback((newValue, eventDetails) => {
		eventDetails.activationDirection = computeActivationDirection(value, newValue, orientation, tabMap);
		onValueChangeProp?.(newValue, eventDetails);
		if (eventDetails.isCanceled) return;
		setValue(newValue);
	});
	const notifyAutomaticValueChange = useStableCallback((nextValue, reason) => {
		onValueChangeProp?.(nextValue, createChangeEventDetails(reason, void 0, void 0, { activationDirection: "none" }));
	});
	const registerMountedTabPanel = useStableCallback((panelValue, panelId) => {
		setMountedTabPanels((prev) => {
			const next = new Map(prev);
			next.set(panelValue, panelId);
			return next;
		});
		return () => {
			setMountedTabPanels((prev) => {
				if (prev.get(panelValue) !== panelId) return prev;
				const next = new Map(prev);
				next.delete(panelValue);
				return next;
			});
		};
	});
	const getTabPanelIdByValue = React$3.useCallback((tabValue) => {
		return mountedTabPanels.get(tabValue);
	}, [mountedTabPanels]);
	const getTabIdByPanelValue = React$3.useCallback((tabPanelValue) => {
		for (const tabMetadata of tabMap.values()) if (tabPanelValue === tabMetadata.value) return tabMetadata.id;
	}, [tabMap]);
	const tabsContextValue = React$3.useMemo(() => ({
		getTabElementBySelectedValue,
		getTabIdByPanelValue,
		getTabPanelIdByValue,
		onValueChange,
		orientation,
		registerMountedTabPanel,
		setTabMap,
		tabActivationDirection,
		value
	}), [
		getTabElementBySelectedValue,
		getTabIdByPanelValue,
		getTabPanelIdByValue,
		onValueChange,
		orientation,
		registerMountedTabPanel,
		setTabMap,
		tabActivationDirection,
		value
	]);
	const selectedTabMetadata = React$3.useMemo(() => {
		for (const tabMetadata of tabMap.values()) if (tabMetadata.value === value) return tabMetadata;
	}, [tabMap, value]);
	const firstEnabledTabValue = React$3.useMemo(() => {
		for (const tabMetadata of tabMap.values()) if (!tabMetadata.disabled) return tabMetadata.value;
	}, [tabMap]);
	const shouldNotifyInitialValueChangeRef = React$3.useRef(!hasExplicitDefaultValueProp);
	const initialDefaultValueRef = React$3.useRef(defaultValueProp);
	const shouldHonorDisabledDefaultValueRef = React$3.useRef(hasExplicitDefaultValueProp);
	const didRegisterTabsRef = React$3.useRef(false);
	useIsoLayoutEffect(() => {
		if (isControlled) return;
		function commitAutomaticValueChange(fallbackValue, fallbackReason) {
			setValue(fallbackValue);
			setActivationDirectionState({
				previousValue: fallbackValue,
				tabActivationDirection: "none"
			});
			notifyAutomaticValueChange(fallbackValue, fallbackReason);
			shouldNotifyInitialValueChangeRef.current = false;
		}
		if (tabMap.size === 0) {
			if (didRegisterTabsRef.current && value !== null && !lastKnownTabElementRef.current?.isConnected) commitAutomaticValueChange(null, missing);
			return;
		}
		didRegisterTabsRef.current = true;
		lastKnownTabElementRef.current = tabMap.keys().next().value;
		const selectionIsDisabled = selectedTabMetadata?.disabled;
		const selectionIsMissing = selectedTabMetadata == null && value !== null;
		if (!selectionIsDisabled && value === initialDefaultValueRef.current) shouldHonorDisabledDefaultValueRef.current = false;
		if (shouldHonorDisabledDefaultValueRef.current && selectionIsDisabled && value === initialDefaultValueRef.current) return;
		const shouldNotifyInitialValueChange = shouldNotifyInitialValueChangeRef.current;
		if (selectionIsDisabled || selectionIsMissing) {
			const fallbackValue = firstEnabledTabValue ?? null;
			if (value === fallbackValue) {
				shouldNotifyInitialValueChangeRef.current = false;
				return;
			}
			let fallbackReason = missing;
			if (shouldNotifyInitialValueChange) fallbackReason = initial;
			else if (selectionIsDisabled) fallbackReason = disabled;
			commitAutomaticValueChange(fallbackValue, fallbackReason);
			return;
		}
		if (shouldNotifyInitialValueChange && selectedTabMetadata != null) {
			notifyAutomaticValueChange(value, initial);
			shouldNotifyInitialValueChangeRef.current = false;
		}
	}, [
		firstEnabledTabValue,
		isControlled,
		notifyAutomaticValueChange,
		selectedTabMetadata,
		setValue,
		tabMap,
		value
	]);
	const element = useRenderElement("div", componentProps, {
		state: {
			orientation,
			tabActivationDirection
		},
		ref: forwardedRef,
		props: elementProps,
		stateAttributesMapping: tabsStateAttributesMapping
	});
	return /* @__PURE__ */ jsx(TabsRootContext.Provider, {
		value: tabsContextValue,
		children: /* @__PURE__ */ jsx(CompositeList, {
			elementsRef: tabPanelRefs,
			children: element
		})
	});
});
function findTabElement(tabMap, value) {
	for (const [tabElement, tabMetadata] of tabMap.entries()) if (value === tabMetadata.value) return tabElement;
	return null;
}
function computeActivationDirection(oldValue, newValue, orientation, tabMap) {
	if (oldValue == null || newValue == null) return "none";
	const [positionProp, backward, forward] = orientation === "horizontal" ? [
		"left",
		"left",
		"right"
	] : [
		"top",
		"up",
		"down"
	];
	const oldTab = findTabElement(tabMap, oldValue);
	const newTab = findTabElement(tabMap, newValue);
	if (oldTab == null || newTab == null) {
		if (oldTab !== newTab && (typeof oldValue === "number" || typeof oldValue === "string") && typeof oldValue === typeof newValue) return newValue > oldValue ? forward : backward;
		return "none";
	}
	const oldPosition = oldTab.getBoundingClientRect()[positionProp];
	const newPosition = newTab.getBoundingClientRect()[positionProp];
	if (newPosition < oldPosition) return backward;
	if (newPosition > oldPosition) return forward;
	return "none";
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/composite/constants.mjs
var ACTIVE_COMPOSITE_ITEM = "data-composite-item-active";
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/composite/list/useCompositeListItem.mjs
/**
* Used to register a list item and its index (DOM position) in the `CompositeList`.
*/
function useCompositeListItem(params = {}) {
	const { guess, label, metadata, textRef, index: externalIndex } = params;
	const { register, unregister, subscribeMapChange, nextIndexRef } = useCompositeListContext();
	const indexRef = React$3.useRef(-1);
	const [internalIndex, setInternalIndex] = React$3.useState(externalIndex == null && guess ? () => {
		if (indexRef.current === -1) {
			const newIndex = nextIndexRef.current;
			nextIndexRef.current += 1;
			indexRef.current = newIndex;
		}
		return indexRef.current;
	} : -1);
	const index = externalIndex ?? internalIndex;
	const componentRef = React$3.useRef(null);
	const ref = React$3.useCallback((node) => {
		const previousNode = componentRef.current;
		if (previousNode) unregister(previousNode);
		componentRef.current = node;
		if (node) register(node, {
			metadata: metadata ?? null,
			index: externalIndex ?? null,
			label,
			textRef
		});
	}, [
		externalIndex,
		register,
		unregister,
		metadata,
		label,
		textRef
	]);
	useIsoLayoutEffect(() => {
		if (externalIndex != null) return;
		return subscribeMapChange((map) => {
			const i = componentRef.current ? map.get(componentRef.current)?.index : null;
			if (i != null) setInternalIndex(i);
		});
	}, [externalIndex, subscribeMapChange]);
	return {
		ref,
		index
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/composite/item/useCompositeItem.mjs
function useCompositeItem(params = {}) {
	const { highlightItemOnHover, highlightedIndex, onHighlightedIndexChange } = useCompositeRootContext();
	const { ref, index } = useCompositeListItem(params);
	const isHighlighted = highlightedIndex === index;
	const itemRef = React$3.useRef(null);
	const mergedRef = useMergedRefs(ref, itemRef);
	return {
		compositeProps: {
			tabIndex: isHighlighted ? 0 : -1,
			onFocus() {
				onHighlightedIndexChange(index);
			},
			onMouseMove() {
				const item = itemRef.current;
				if (!highlightItemOnHover || !item) return;
				const disabled = item.hasAttribute("disabled") || item.ariaDisabled === "true";
				if (!isHighlighted && !disabled) item.focus();
			}
		},
		compositeRef: mergedRef,
		index
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/tabs/list/TabsListContext.mjs
var TabsListContext = /* @__PURE__ */ React$3.createContext(void 0);
function useTabsListContext() {
	const context = React$3.useContext(TabsListContext);
	if (context === void 0) throw new Error(formatErrorMessage(65));
	return context;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/tabs/tab/TabsTab.mjs
/**
* An individual interactive tab button that toggles the corresponding panel.
* Renders a `<button>` element.
*
* Documentation: [Base UI Tabs](https://base-ui.com/react/components/tabs)
*/
var TabsTab = /* @__PURE__ */ React$3.forwardRef(function TabsTab(componentProps, forwardedRef) {
	const { className, disabled = false, render, value, id: idProp, nativeButton = true, style, ...elementProps } = componentProps;
	const { value: activeTabValue, getTabPanelIdByValue, onValueChange, orientation, tabActivationDirection } = useTabsRootContext();
	const { activateOnFocus, registerTabResizeObserverElement, tabsListElement } = useTabsListContext();
	const { highlightedIndex, onHighlightedIndexChange } = useCompositeRootContext();
	const id = useBaseUiId(idProp);
	const { compositeProps, compositeRef, index } = useCompositeItem({ metadata: React$3.useMemo(() => ({
		disabled,
		id,
		value
	}), [
		disabled,
		id,
		value
	]) });
	const active = value === activeTabValue;
	const isNavigatingRef = React$3.useRef(false);
	const unobserveTabElementRef = React$3.useRef(null);
	const observeTabElement = useStableCallback((element) => {
		unobserveTabElementRef.current?.();
		unobserveTabElementRef.current = element ? registerTabResizeObserverElement(element) : null;
	});
	useIsoLayoutEffect(() => {
		if (isNavigatingRef.current) {
			isNavigatingRef.current = false;
			return;
		}
		if (!(active && index > -1 && highlightedIndex !== index)) return;
		const listElement = tabsListElement;
		if (listElement != null) {
			const activeEl = activeElement(ownerDocument(listElement));
			if (activeEl && contains(listElement, activeEl)) return;
		}
		if (!disabled) onHighlightedIndexChange(index);
	}, [
		active,
		index,
		highlightedIndex,
		onHighlightedIndexChange,
		disabled,
		tabsListElement
	]);
	const { getButtonProps, buttonRef } = useButton({
		disabled,
		native: nativeButton,
		focusableWhenDisabled: true
	});
	const tabPanelId = getTabPanelIdByValue(value);
	const isPressingRef = React$3.useRef(false);
	const isMainButtonRef = React$3.useRef(false);
	function activate(event) {
		onValueChange(value, createChangeEventDetails(none, event.nativeEvent, void 0, { activationDirection: "none" }));
	}
	function onClick(event) {
		if (active || disabled) return;
		activate(event);
	}
	function onFocus(event) {
		if (active || disabled) return;
		if (activateOnFocus && (!isPressingRef.current || isMainButtonRef.current)) activate(event);
	}
	function onPointerDown(event) {
		if (active || disabled) return;
		isPressingRef.current = true;
		isMainButtonRef.current = event.button === 0;
		const doc = ownerDocument(event.currentTarget);
		function handlePointerEnd() {
			isPressingRef.current = false;
			isMainButtonRef.current = false;
			doc.removeEventListener("pointerup", handlePointerEnd);
			doc.removeEventListener("pointercancel", handlePointerEnd);
		}
		doc.addEventListener("pointerup", handlePointerEnd);
		doc.addEventListener("pointercancel", handlePointerEnd);
	}
	return useRenderElement("button", componentProps, {
		state: {
			disabled,
			active,
			orientation,
			tabActivationDirection
		},
		ref: [
			forwardedRef,
			buttonRef,
			compositeRef,
			observeTabElement
		],
		props: [
			compositeProps,
			{
				role: "tab",
				"aria-controls": tabPanelId,
				"aria-selected": active,
				id,
				onClick,
				onFocus,
				onPointerDown,
				[ACTIVE_COMPOSITE_ITEM]: active ? "" : void 0,
				onKeyDownCapture() {
					isNavigatingRef.current = true;
				}
			},
			elementProps,
			getButtonProps
		],
		stateAttributesMapping: tabsStateAttributesMapping
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/csp-context/CSPContext.mjs
var CSPContext = /* @__PURE__ */ React$3.createContext(void 0);
var DEFAULT_CSP_CONTEXT_VALUE = { disableStyleElements: false };
function useCSPContext() {
	return React$3.useContext(CSPContext) ?? DEFAULT_CSP_CONTEXT_VALUE;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/tabs/panel/TabsPanel.mjs
var stateAttributesMapping$3 = {
	...tabsStateAttributesMapping,
	...transitionStatusMapping
};
/**
* A panel displayed when the corresponding tab is active.
* Renders a `<div>` element.
*
* Documentation: [Base UI Tabs](https://base-ui.com/react/components/tabs)
*/
var TabsPanel = /* @__PURE__ */ React$3.forwardRef(function TabsPanel(componentProps, forwardedRef) {
	const { className, value, render, keepMounted = false, style, ...elementProps } = componentProps;
	const { value: selectedValue, getTabIdByPanelValue, orientation, tabActivationDirection, registerMountedTabPanel } = useTabsRootContext();
	const id = useBaseUiId();
	const { ref: listItemRef, index } = useCompositeListItem();
	const open = value === selectedValue;
	const { mounted, transitionStatus, setMounted } = useTransitionStatus(open);
	const hidden = !mounted;
	const correspondingTabId = getTabIdByPanelValue(value);
	const state = {
		hidden,
		orientation,
		tabActivationDirection,
		transitionStatus
	};
	const panelRef = React$3.useRef(null);
	const element = useRenderElement("div", componentProps, {
		state,
		ref: [
			forwardedRef,
			listItemRef,
			panelRef
		],
		props: [{
			"aria-labelledby": correspondingTabId,
			hidden,
			id,
			role: "tabpanel",
			tabIndex: open ? 0 : -1,
			inert: inertValue(!open),
			["data-index"]: index
		}, elementProps],
		stateAttributesMapping: stateAttributesMapping$3
	});
	useOpenChangeComplete({
		open,
		ref: panelRef,
		onComplete() {
			if (!open) setMounted(false);
		}
	});
	useIsoLayoutEffect(() => {
		if (id == null || hidden && !keepMounted) return;
		return registerMountedTabPanel(value, id);
	}, [
		hidden,
		keepMounted,
		value,
		id,
		registerMountedTabPanel
	]);
	if (!(keepMounted || mounted)) return null;
	return element;
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/isElementDisabled.mjs
function isElementDisabled(element) {
	return element == null || element.hasAttribute("disabled") || element.getAttribute("aria-disabled") === "true";
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/composite/root/useCompositeRoot.mjs
var EMPTY_ARRAY = [];
function useCompositeRoot(params) {
	const { loopFocus = true, orientation = "both", grid, onLoop, direction, highlightedIndex: externalHighlightedIndex, onHighlightedIndexChange: externalSetHighlightedIndex, rootRef: externalRef, enableHomeAndEndKeys = false, stopEventPropagation, disabledIndices, modifierKeys = EMPTY_ARRAY } = params;
	const [internalHighlightedIndex, internalSetHighlightedIndex] = React$3.useState(0);
	const isGrid = grid != null;
	const rootRef = React$3.useRef(null);
	const mergedRef = useMergedRefs(rootRef, externalRef);
	const elementsRef = React$3.useRef([]);
	const hasSetDefaultIndexRef = React$3.useRef(false);
	const highlightedIndex = externalHighlightedIndex ?? internalHighlightedIndex;
	const onHighlightedIndexChange = useStableCallback((index, shouldScrollIntoView = false) => {
		(externalSetHighlightedIndex ?? internalSetHighlightedIndex)(index);
		if (shouldScrollIntoView) {
			const newActiveItem = elementsRef.current[index];
			scrollIntoViewIfNeeded(rootRef.current, newActiveItem, direction, orientation);
		}
	});
	const onMapChange = useStableCallback((map) => {
		if (map.size === 0 || hasSetDefaultIndexRef.current) return;
		hasSetDefaultIndexRef.current = true;
		const sortedElements = Array.from(map.keys());
		const activeItem = sortedElements.find((compositeElement) => compositeElement?.hasAttribute("data-composite-item-active")) ?? null;
		const activeIndex = activeItem ? map.get(activeItem)?.index ?? -1 : -1;
		if (activeIndex !== -1) onHighlightedIndexChange(activeIndex);
		else if (isListIndexDisabled(sortedElements, highlightedIndex, disabledIndices)) {
			const firstEnabledIndex = findNonDisabledListIndex(sortedElements, { disabledIndices });
			if (!isIndexOutOfListBounds(sortedElements, firstEnabledIndex)) onHighlightedIndexChange(firstEnabledIndex);
		}
		scrollIntoViewIfNeeded(rootRef.current, activeItem, direction, orientation);
	});
	useIsoLayoutEffect(() => {
		if (disabledIndices == null || externalHighlightedIndex != null || !hasSetDefaultIndexRef.current) return;
		const elements = elementsRef.current;
		if (isListIndexDisabled(elements, highlightedIndex, disabledIndices)) {
			const firstEnabledIndex = findNonDisabledListIndex(elements, { disabledIndices });
			if (!isIndexOutOfListBounds(elements, firstEnabledIndex)) onHighlightedIndexChange(firstEnabledIndex);
		}
	}, [
		disabledIndices,
		externalHighlightedIndex,
		highlightedIndex,
		elementsRef,
		onHighlightedIndexChange
	]);
	const wrappedOnLoop = useStableCallback((event, prevIndex, nextIndex) => {
		if (!onLoop) return nextIndex;
		return onLoop(event, prevIndex, nextIndex, elementsRef);
	});
	const onKeyDown = useStableCallback((event) => {
		const isHomeOrEnd = event.key === "Home" || event.key === "End";
		if (!COMPOSITE_KEYS.has(event.key) || !enableHomeAndEndKeys && isHomeOrEnd) return;
		if (isModifierKeySet(event, modifierKeys)) return;
		if (!rootRef.current) return;
		const isRtl = direction === "rtl";
		const horizontalForwardKey = isRtl ? ARROW_LEFT : ARROW_RIGHT;
		const horizontalBackwardKey = isRtl ? ARROW_RIGHT : ARROW_LEFT;
		const forwardKey = orientation === "vertical" ? ARROW_DOWN : horizontalForwardKey;
		const backwardKey = orientation === "vertical" ? ARROW_UP : horizontalBackwardKey;
		const target = getTarget(event.nativeEvent);
		if (target != null && isNativeInput(target) && !isElementDisabled(target)) {
			const selectionStart = target.selectionStart;
			const selectionEnd = target.selectionEnd;
			const textContent = target.value;
			if (selectionStart == null || event.shiftKey || selectionStart !== selectionEnd) return;
			if (event.key !== backwardKey && selectionStart < textContent.length) return;
			if (event.key !== forwardKey && selectionStart > 0) return;
		}
		let nextIndex = highlightedIndex;
		const minIndex = getMinListIndex(elementsRef, disabledIndices);
		const maxIndex = getMaxListIndex(elementsRef, disabledIndices);
		if (grid != null) nextIndex = grid({
			disabledIndices,
			elementsRef,
			event,
			highlightedIndex,
			loopFocus,
			maxIndex,
			minIndex,
			onLoop: wrappedOnLoop,
			orientation,
			rtl: isRtl
		});
		const isForwardKey = orientation !== "vertical" && event.key === horizontalForwardKey || orientation !== "horizontal" && event.key === "ArrowDown";
		const isBackwardKey = orientation !== "vertical" && event.key === horizontalBackwardKey || orientation !== "horizontal" && event.key === "ArrowUp";
		if (enableHomeAndEndKeys) {
			if (event.key === "Home") nextIndex = minIndex;
			else if (event.key === "End") nextIndex = maxIndex;
		}
		if (nextIndex === highlightedIndex && (isForwardKey || isBackwardKey)) if (loopFocus && nextIndex === maxIndex && isForwardKey) {
			nextIndex = minIndex;
			if (onLoop) nextIndex = onLoop(event, highlightedIndex, nextIndex, elementsRef);
		} else if (loopFocus && nextIndex === minIndex && isBackwardKey) {
			nextIndex = maxIndex;
			if (onLoop) nextIndex = onLoop(event, highlightedIndex, nextIndex, elementsRef);
		} else nextIndex = findNonDisabledListIndex(elementsRef.current, {
			startingIndex: nextIndex,
			decrement: isBackwardKey,
			disabledIndices
		});
		if (nextIndex !== highlightedIndex && !isIndexOutOfListBounds(elementsRef.current, nextIndex)) {
			if (stopEventPropagation) event.stopPropagation();
			if (isGrid || isHomeOrEnd || isForwardKey || isBackwardKey) event.preventDefault();
			onHighlightedIndexChange(nextIndex, true);
			queueMicrotask(() => {
				elementsRef.current[nextIndex]?.focus();
			});
		}
	});
	return {
		props: {
			ref: mergedRef,
			onFocus(event) {
				const element = rootRef.current;
				const target = getTarget(event.nativeEvent);
				if (!element || target == null || !isNativeInput(target)) return;
				target.setSelectionRange(0, target.value.length);
			},
			onKeyDown
		},
		highlightedIndex,
		onHighlightedIndexChange,
		elementsRef,
		onMapChange,
		relayKeyboardEvent: onKeyDown
	};
}
function isModifierKeySet(event, ignoredModifierKeys) {
	for (const key of MODIFIER_KEYS) {
		if (ignoredModifierKeys.includes(key)) continue;
		if (event.getModifierState(key)) return true;
	}
	return false;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/composite/root/CompositeRoot.mjs
function CompositeRoot(componentProps) {
	const { render, className, style, refs = EMPTY_ARRAY$1, props = EMPTY_ARRAY$1, state = EMPTY_OBJECT, stateAttributesMapping, highlightedIndex: highlightedIndexProp, onHighlightedIndexChange: onHighlightedIndexChangeProp, orientation, grid, loopFocus, onLoop, enableHomeAndEndKeys, onMapChange: onMapChangeProp, stopEventPropagation = true, rootRef, disabledIndices, modifierKeys, highlightItemOnHover = false, tag = "div", ...elementProps } = componentProps;
	const { props: defaultProps, highlightedIndex, onHighlightedIndexChange, elementsRef, onMapChange: onMapChangeUnwrapped, relayKeyboardEvent } = useCompositeRoot({
		grid,
		loopFocus,
		onLoop,
		orientation,
		highlightedIndex: highlightedIndexProp,
		onHighlightedIndexChange: onHighlightedIndexChangeProp,
		rootRef,
		stopEventPropagation,
		enableHomeAndEndKeys,
		direction: useDirection(),
		disabledIndices,
		modifierKeys
	});
	const element = useRenderElement(tag, componentProps, {
		state,
		ref: refs,
		props: [
			defaultProps,
			...props,
			elementProps
		],
		stateAttributesMapping
	});
	const contextValue = React$3.useMemo(() => ({
		highlightedIndex,
		onHighlightedIndexChange,
		highlightItemOnHover,
		relayKeyboardEvent
	}), [
		highlightedIndex,
		onHighlightedIndexChange,
		highlightItemOnHover,
		relayKeyboardEvent
	]);
	return /* @__PURE__ */ jsx(CompositeRootContext.Provider, {
		value: contextValue,
		children: /* @__PURE__ */ jsx(CompositeList, {
			elementsRef,
			onMapChange: (newMap) => {
				onMapChangeProp?.(newMap);
				onMapChangeUnwrapped(newMap);
			},
			children: element
		})
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/tabs/list/TabsList.mjs
/**
* Groups the individual tab buttons.
* Renders a `<div>` element.
*
* Documentation: [Base UI Tabs](https://base-ui.com/react/components/tabs)
*/
var TabsList$1 = /* @__PURE__ */ React$3.forwardRef(function TabsList(componentProps, forwardedRef) {
	const { activateOnFocus = false, className, loopFocus = true, render, style, ...elementProps } = componentProps;
	const { orientation, setTabMap, tabActivationDirection } = useTabsRootContext();
	const [highlightedTabIndex, setHighlightedTabIndex] = React$3.useState(0);
	const [tabsListElement, setTabsListElement] = React$3.useState(null);
	const indicatorUpdateListenersRef = React$3.useRef(/* @__PURE__ */ new Set());
	const tabResizeObserverElementsRef = React$3.useRef(/* @__PURE__ */ new Set());
	const resizeObserverRef = React$3.useRef(null);
	useIsoLayoutEffect(() => {
		if (typeof ResizeObserver === "undefined") return;
		const resizeObserver = new ResizeObserver(() => {
			indicatorUpdateListenersRef.current.forEach((listener) => {
				listener();
			});
		});
		resizeObserverRef.current = resizeObserver;
		if (tabsListElement) resizeObserver.observe(tabsListElement);
		tabResizeObserverElementsRef.current.forEach((element) => {
			resizeObserver.observe(element);
		});
		return () => {
			resizeObserver.disconnect();
			resizeObserverRef.current = null;
		};
	}, [tabsListElement]);
	const registerIndicatorUpdateListener = useStableCallback((listener) => {
		indicatorUpdateListenersRef.current.add(listener);
		return () => {
			indicatorUpdateListenersRef.current.delete(listener);
		};
	});
	const registerTabResizeObserverElement = useStableCallback((element) => {
		tabResizeObserverElementsRef.current.add(element);
		resizeObserverRef.current?.observe(element);
		return () => {
			tabResizeObserverElementsRef.current.delete(element);
			resizeObserverRef.current?.unobserve(element);
		};
	});
	const state = {
		orientation,
		tabActivationDirection
	};
	const defaultProps = {
		"aria-orientation": orientation === "vertical" ? "vertical" : void 0,
		role: "tablist"
	};
	const tabsListContextValue = React$3.useMemo(() => ({
		activateOnFocus,
		registerIndicatorUpdateListener,
		registerTabResizeObserverElement,
		tabsListElement
	}), [
		activateOnFocus,
		registerIndicatorUpdateListener,
		registerTabResizeObserverElement,
		tabsListElement
	]);
	return /* @__PURE__ */ jsx(TabsListContext.Provider, {
		value: tabsListContextValue,
		children: /* @__PURE__ */ jsx(CompositeRoot, {
			render,
			className,
			style,
			state,
			refs: [forwardedRef, setTabsListElement],
			props: [defaultProps, elementProps],
			stateAttributesMapping: tabsStateAttributesMapping,
			highlightedIndex: highlightedTabIndex,
			enableHomeAndEndKeys: true,
			loopFocus,
			orientation,
			onHighlightedIndexChange: setHighlightedTabIndex,
			onMapChange: setTabMap,
			disabledIndices: EMPTY_ARRAY$1
		})
	});
});
//#endregion
//#region components/ui/tabs.tsx
function Tabs({ className, orientation = "horizontal", ...props }) {
	return /* @__PURE__ */ jsx(TabsRoot, {
		"data-slot": "tabs",
		"data-orientation": orientation,
		className: cn("group/tabs flex gap-2 data-horizontal:flex-col", className),
		...props
	});
}
var tabsListVariants = cva("group/tabs-list inline-flex w-fit items-center justify-center rounded-lg p-[3px] text-muted-foreground group-data-horizontal/tabs:h-8 group-data-vertical/tabs:h-fit group-data-vertical/tabs:flex-col data-[variant=line]:rounded-none", {
	variants: { variant: {
		default: "bg-muted",
		line: "gap-1 bg-transparent"
	} },
	defaultVariants: { variant: "default" }
});
function TabsList({ className, variant = "default", ...props }) {
	return /* @__PURE__ */ jsx(TabsList$1, {
		"data-slot": "tabs-list",
		"data-variant": variant,
		className: cn(tabsListVariants({ variant }), className),
		...props
	});
}
function TabsTrigger({ className, ...props }) {
	return /* @__PURE__ */ jsx(TabsTab, {
		"data-slot": "tabs-trigger",
		className: cn("relative inline-flex h-[calc(100%-1px)] flex-1 items-center justify-center gap-1.5 rounded-md border border-transparent px-1.5 py-0.5 text-sm font-medium whitespace-nowrap text-foreground/60 transition-all group-data-vertical/tabs:w-full group-data-vertical/tabs:justify-start hover:text-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-1 focus-visible:outline-ring disabled:pointer-events-none disabled:opacity-50 has-data-[icon=inline-end]:pr-1 has-data-[icon=inline-start]:pl-1 aria-disabled:pointer-events-none aria-disabled:opacity-50 dark:text-muted-foreground dark:hover:text-foreground group-data-[variant=default]/tabs-list:data-active:shadow-sm group-data-[variant=line]/tabs-list:data-active:shadow-none [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4", "group-data-[variant=line]/tabs-list:bg-transparent group-data-[variant=line]/tabs-list:data-active:bg-transparent dark:group-data-[variant=line]/tabs-list:data-active:border-transparent dark:group-data-[variant=line]/tabs-list:data-active:bg-transparent", "data-active:bg-background data-active:text-foreground dark:data-active:border-input dark:data-active:bg-input/30 dark:data-active:text-foreground", "after:absolute after:bg-foreground after:opacity-0 after:transition-opacity group-data-horizontal/tabs:after:inset-x-0 group-data-horizontal/tabs:after:bottom-[-5px] group-data-horizontal/tabs:after:h-0.5 group-data-vertical/tabs:after:inset-y-0 group-data-vertical/tabs:after:-right-1 group-data-vertical/tabs:after:w-0.5 group-data-[variant=line]/tabs-list:data-active:after:opacity-100", className),
		...props
	});
}
function TabsContent({ className, ...props }) {
	return /* @__PURE__ */ jsx(TabsPanel, {
		"data-slot": "tabs-content",
		className: cn("flex-1 text-sm outline-none", className),
		...props
	});
}
//#endregion
//#region components/ui/table.tsx
function Table({ className, ...props }) {
	return /* @__PURE__ */ jsx("div", {
		"data-slot": "table-container",
		className: "relative w-full overflow-x-auto",
		children: /* @__PURE__ */ jsx("table", {
			"data-slot": "table",
			className: cn("w-full caption-bottom text-sm", className),
			...props
		})
	});
}
function TableHeader({ className, ...props }) {
	return /* @__PURE__ */ jsx("thead", {
		"data-slot": "table-header",
		className: cn("[&_tr]:border-b", className),
		...props
	});
}
function TableBody({ className, ...props }) {
	return /* @__PURE__ */ jsx("tbody", {
		"data-slot": "table-body",
		className: cn("[&_tr:last-child]:border-0", className),
		...props
	});
}
function TableRow({ className, ...props }) {
	return /* @__PURE__ */ jsx("tr", {
		"data-slot": "table-row",
		className: cn("hover:bg-muted/50 data-[state=selected]:bg-muted border-b transition-colors has-aria-expanded:bg-muted/50", className),
		...props
	});
}
function TableHead({ className, ...props }) {
	return /* @__PURE__ */ jsx("th", {
		"data-slot": "table-head",
		className: cn("text-foreground h-10 px-2 text-left align-middle font-medium whitespace-nowrap [&:has([role=checkbox])]:pr-0", className),
		...props
	});
}
function TableCell({ className, ...props }) {
	return /* @__PURE__ */ jsx("td", {
		"data-slot": "table-cell",
		className: cn("p-2 align-middle whitespace-nowrap [&:has([role=checkbox])]:pr-0", className),
		...props
	});
}
//#endregion
//#region lib/harness-tasks.ts
var STORAGE_KEY = "zhangcai.harness.tasks.v1";
var EVENT_NAME = "zhangcai:harness-tasks";
var BRIDGE_ENDPOINTS = [];
function readTasks() {
	try {
		const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
		return Array.isArray(value) ? value.filter((item) => item && typeof item.id === "string") : [];
	} catch {
		return [];
	}
}
function writeTasks(tasks) {
	const next = tasks.slice(0, 12);
	localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
	window.dispatchEvent(new CustomEvent(EVENT_NAME, { detail: next }));
}
function getHarnessTasks() {
	return readTasks();
}
function subscribeHarnessTasks(listener) {
	const handler = (event) => listener(event.detail || readTasks());
	const storage = (event) => {
		if (event.key === STORAGE_KEY) listener(readTasks());
	};
	window.addEventListener(EVENT_NAME, handler);
	window.addEventListener("storage", storage);
	listener(readTasks());
	return () => {
		window.removeEventListener(EVENT_NAME, handler);
		window.removeEventListener("storage", storage);
	};
}
function createHarnessTask(input) {
	const task = {
		...input,
		id: `harness-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
		status: "starting",
		startedAt: Date.now()
	};
	writeTasks([task, ...readTasks().filter((item) => item.status === "running" || item.status === "starting")]);
	return task;
}
function updateHarnessTask(id, patch) {
	writeTasks(readTasks().map((item) => item.id === id ? {
		...item,
		...patch
	} : item));
}
function dismissHarnessTask(id) {
	writeTasks(readTasks().filter((item) => item.id !== id));
}
/** Continue polling a persisted task after the page has been refreshed. */
async function resumeHarnessTask(task) {
	if (!task.backendJobId) throw new Error("后台任务缺少桥接任务 ID，无法恢复");
	if (task.status === "completed") return {
		output: String(task.output || ""),
		elapsed_ms: Math.max(0, (task.completedAt || Date.now()) - task.startedAt),
		status: task.strategyStatus || "completed",
		receipt: task.receipt,
		structured: task.structured,
		taskId: task.id
	};
	let connectivityFailures = 0;
	while (true) {
		const endpoint = task.backendKind === "strategy" ? "/strategy/job/" : "/agent/job/";
		let response;
		try {
			response = await fetchBridge(`${endpoint}${encodeURIComponent(task.backendJobId)}`, { cache: "no-store" });
			connectivityFailures = 0;
		} catch (error) {
			connectivityFailures += 1;
			if (connectivityFailures <= 30) {
				await delay(Math.min(5e3, 700 + connectivityFailures * 150));
				continue;
			}
			throw error;
		}
		const job = await response.json().catch(() => ({}));
		if (!response.ok) throw new Error(job.error || "后台任务状态读取失败");
		if (job.status === "completed") {
			const result = job.result && typeof job.result === "object" ? job.result : {};
			const output = String(job.output || result.output || "");
			const strategyStatus = String(result.status || job.strategy_status || "completed");
			const patch = {
				status: "completed",
				output,
				completedAt: Date.now(),
				strategyStatus,
				receipt: result.receipt,
				structured: result.structured
			};
			updateHarnessTask(task.id, patch);
			return {
				output,
				elapsed_ms: Number(job.elapsed_ms || result.elapsed_ms || Date.now() - task.startedAt),
				status: strategyStatus,
				receipt: result.receipt,
				structured: result.structured,
				taskId: task.id
			};
		}
		if (job.status === "failed") {
			const message = String(job.error || "后台任务执行失败");
			updateHarnessTask(task.id, {
				status: "failed",
				error: message,
				completedAt: Date.now()
			});
			throw new Error(message);
		}
		await delay(1e3);
	}
}
async function delay(ms) {
	await new Promise((resolve) => window.setTimeout(resolve, ms));
}
async function fetchBridge(path, init) {
	let lastError;
	let lastGatewayResponse;
	const endpoints = [...BRIDGE_ENDPOINTS, bridgeUrl()];
	if (isDesktopRuntime()) try {
		if (new URL(endpoints[endpoints.length - 1]).port === "4319") throw new Error("桌面版桥接配置缺失，已拒绝回退到网页 4319。");
	} catch (error) {
		if (error instanceof Error && error.message.includes("拒绝回退")) throw error;
	}
	const suffix = path.startsWith("/") ? path : `/${path}`;
	for (let endpointIndex = 0; endpointIndex < endpoints.length; endpointIndex += 1) for (let attempt = 0; attempt < 3; attempt += 1) try {
		const endpoint = endpoints[endpointIndex].replace(/\/+$/, "");
		const response = await fetch(`${endpoint}${suffix}`, init);
		if (response.status >= 502 && response.status <= 504) {
			lastGatewayResponse = response;
			lastError = /* @__PURE__ */ new Error(`桥接入口返回 ${response.status}`);
			if (attempt < 2) {
				await delay(350 * (attempt + 1));
				continue;
			}
			break;
		}
		return response;
	} catch (error) {
		lastError = error;
		if (attempt < 2) await delay(350 * (attempt + 1));
	}
	const reason = lastError instanceof Error ? lastError.message : lastGatewayResponse ? `桥接代理返回 ${lastGatewayResponse.status}` : String(lastError || "未知网络错误");
	throw new Error(`无法连接 DeepSeek Harness 桥接服务（${bridgeHostLabel()}）：${reason}`);
}
async function startDailyDataRefresh(options = {}) {
	const response = await fetchBridge("/data/daily/start", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ force: options.force === true })
	});
	const value = await response.json().catch(() => ({}));
	if (!response.ok || !value || typeof value !== "object") throw new Error(value?.error || `每日数据更新启动失败（${response.status}）`);
	return value;
}
async function getDailyDataRefreshStatus() {
	const response = await fetchBridge("/data/daily/status", { cache: "no-store" });
	const value = await response.json().catch(() => ({}));
	if (!response.ok || !value || typeof value !== "object") throw new Error(value?.error || `每日数据状态读取失败（${response.status}）`);
	return value;
}
async function startDailyIndexInitialization(options = {}) {
	const response = await fetchBridge("/data/daily/initialize", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ force: options.force === true })
	});
	const value = await response.json().catch(() => ({}));
	if (!response.ok || !value || typeof value !== "object") throw new Error(value?.error || `全量个股索引初始化启动失败（${response.status}）`);
	return value;
}
async function getDailyIndexInitializationStatus() {
	const response = await fetchBridge("/data/daily/initialize/status", { cache: "no-store" });
	const value = await response.json().catch(() => ({}));
	if (!response.ok || !value || typeof value !== "object") throw new Error(value?.error || `全量个股索引初始化状态读取失败（${response.status}）`);
	return value;
}
async function startSupplementalDataRefresh(options = {}) {
	const response = await fetchBridge("/data/public/start", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ force: options.force === true })
	});
	const value = await response.json().catch(() => ({}));
	if (!response.ok || !value || typeof value !== "object") throw new Error(value?.error || `其他数据补齐启动失败（${response.status}）`);
	return value;
}
async function getSupplementalDataRefreshStatus() {
	const response = await fetchBridge("/data/public/status", { cache: "no-store" });
	const value = await response.json().catch(() => ({}));
	if (!response.ok || !value || typeof value !== "object") throw new Error(value?.error || `其他数据状态读取失败（${response.status}）`);
	return value;
}
async function startUnifiedDataArchive(options = {}) {
	const response = await fetchBridge("/data/archive/start", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ force: options.force === true })
	});
	const value = await response.json().catch(() => ({}));
	if (!response.ok || !value || typeof value !== "object") throw new Error(value?.error || `统一数据落盘启动失败（${response.status}）`);
	return value;
}
async function getUnifiedDataArchiveStatus() {
	const response = await fetchBridge("/data/archive/status", { cache: "no-store" });
	const value = await response.json().catch(() => ({}));
	if (!response.ok || !value || typeof value !== "object") throw new Error(value?.error || `统一数据落盘状态读取失败（${response.status}）`);
	return value;
}
async function startUnifiedDataVerification(options = {}) {
	const response = await fetchBridge("/data/archive/verify", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ force: options.force === true })
	});
	const value = await response.json().catch(() => ({}));
	if (!response.ok || !value || typeof value !== "object") throw new Error(value?.error || `统一数据校验启动失败（${response.status}）`);
	return value;
}
async function getUnifiedDataVerificationStatus() {
	const response = await fetchBridge("/data/archive/verify/status", { cache: "no-store" });
	const value = await response.json().catch(() => ({}));
	if (!response.ok || !value || typeof value !== "object") throw new Error(value?.error || `统一数据校验状态读取失败（${response.status}）`);
	return value;
}
async function runHarnessInBackground(input) {
	const local = createHarnessTask({
		skillId: input.skillId,
		label: input.label,
		originPage: input.originPage,
		originStockCode: input.originStockCode,
		expectedSeconds: input.expectedSeconds,
		backendKind: "harness"
	});
	try {
		const startResponse = await fetchBridge("/agent/start", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				task: input.task,
				skillId: input.skillId,
				market: input.market,
				context: input.context
			})
		});
		const start = await startResponse.json().catch(() => ({}));
		if (startResponse.status === 409 || start.status === "busy") {
			const message = String(start.error || "Harness 正在执行长任务，请稍后再试。");
			dismissHarnessTask(local.id);
			window.alert(message);
			throw new Error(message);
		}
		if (!startResponse.ok || start.status !== "accepted" || typeof start.job_id !== "string") throw new Error(start.error || `Harness 后台任务启动失败（${startResponse.status}）`);
		updateHarnessTask(local.id, {
			backendJobId: start.job_id,
			status: "running"
		});
		let connectivityFailures = 0;
		while (true) {
			let response;
			try {
				response = await fetchBridge(`/agent/job/${encodeURIComponent(start.job_id)}`, { cache: "no-store" });
				connectivityFailures = 0;
			} catch (error) {
				connectivityFailures += 1;
				if (connectivityFailures <= 30) {
					await delay(Math.min(5e3, 700 + connectivityFailures * 150));
					continue;
				}
				throw error;
			}
			const job = await response.json().catch(() => ({}));
			if (!response.ok) throw new Error(job.error || "Harness 任务状态读取失败");
			if (job.status === "completed") {
				updateHarnessTask(local.id, {
					status: "completed",
					output: String(job.output || ""),
					completedAt: Date.now()
				});
				return {
					output: String(job.output || ""),
					elapsed_ms: Number(job.elapsed_ms || 0),
					taskId: local.id
				};
			}
			if (job.status === "failed") {
				const message = String(job.error || "DeepSeek Harness 执行失败");
				updateHarnessTask(local.id, {
					status: "failed",
					error: message,
					completedAt: Date.now()
				});
				throw new Error(message);
			}
			await delay(1e3);
		}
	} catch (error) {
		if (readTasks().some((item) => item.id === local.id && item.status !== "failed")) updateHarnessTask(local.id, {
			status: "failed",
			error: error instanceof Error ? error.message : String(error),
			completedAt: Date.now()
		});
		throw error;
	}
}
async function resumeHarnessTasks() {
	for (const task of readTasks().filter((item) => item.status === "starting" || item.status === "running")) {
		if (!task.backendJobId) continue;
		try {
			const response = await fetchBridge(`${task.backendKind === "strategy" ? "/strategy/job/" : "/agent/job/"}${encodeURIComponent(task.backendJobId)}`, { cache: "no-store" });
			const job = await response.json().catch(() => ({}));
			if (job.status === "completed") {
				const result = job.result && typeof job.result === "object" ? job.result : {};
				updateHarnessTask(task.id, {
					status: "completed",
					output: String(job.output || result.output || ""),
					completedAt: Date.now(),
					strategyStatus: task.backendKind === "strategy" ? String(result.status || job.strategy_status || "UNKNOWN") : task.strategyStatus,
					receipt: task.backendKind === "strategy" ? result.receipt : task.receipt,
					structured: task.backendKind === "strategy" ? result.structured : task.structured
				});
			} else if (job.status === "failed" || !response.ok) updateHarnessTask(task.id, {
				status: "failed",
				error: String(job.error || "Harness 任务状态读取失败"),
				completedAt: Date.now()
			});
		} catch {}
	}
}
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var Download = createLucideIcon("download", [
	["path", {
		d: "M12 15V3",
		key: "m9g1x1"
	}],
	["path", {
		d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4",
		key: "ih7n3h"
	}],
	["path", {
		d: "m7 10 5 5 5-5",
		key: "brsn70"
	}]
]);
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var FolderOpen = createLucideIcon("folder-open", [["path", {
	d: "m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2",
	key: "usdka0"
}]]);
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var Info = createLucideIcon("info", [
	["circle", {
		cx: "12",
		cy: "12",
		r: "10",
		key: "1mglay"
	}],
	["path", {
		d: "M12 16v-4",
		key: "1dtifu"
	}],
	["path", {
		d: "M12 8h.01",
		key: "e9boi3"
	}]
]);
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var TableProperties = createLucideIcon("table-properties", [
	["path", {
		d: "M15 3v18",
		key: "14nvp0"
	}],
	["rect", {
		width: "18",
		height: "18",
		x: "3",
		y: "3",
		rx: "2",
		key: "afitv7"
	}],
	["path", {
		d: "M21 9H3",
		key: "1338ky"
	}],
	["path", {
		d: "M21 15H3",
		key: "9uk58r"
	}]
]);
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var Target = createLucideIcon("target", [
	["circle", {
		cx: "12",
		cy: "12",
		r: "10",
		key: "1mglay"
	}],
	["circle", {
		cx: "12",
		cy: "12",
		r: "6",
		key: "1vlfrh"
	}],
	["circle", {
		cx: "12",
		cy: "12",
		r: "2",
		key: "1c9p78"
	}]
]);
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var Trash2 = createLucideIcon("trash-2", [
	["path", {
		d: "M10 11v6",
		key: "nco0om"
	}],
	["path", {
		d: "M14 11v6",
		key: "outv1u"
	}],
	["path", {
		d: "M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6",
		key: "miytrc"
	}],
	["path", {
		d: "M3 6h18",
		key: "d0wm0j"
	}],
	["path", {
		d: "M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2",
		key: "e791ji"
	}]
]);
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+utils@0.3.2_@types_cb475dbffe3dec9e898f6077a0a349f0/node_modules/@base-ui/utils/useOnFirstRender.mjs
function useOnFirstRender(fn) {
	const ref = React$3.useRef(true);
	if (ref.current) {
		ref.current = false;
		fn();
	}
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/select/root/SelectRootContext.mjs
var SelectRootContext = /* @__PURE__ */ React$3.createContext(null);
function useSelectRootContext() {
	const context = React$3.useContext(SelectRootContext);
	if (context === null) throw new Error(formatErrorMessage(60));
	return context;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/itemEquality.mjs
var defaultItemEquality = (itemValue, selectedValue) => Object.is(itemValue, selectedValue);
function compareItemEquality(itemValue, selectedValue, comparer) {
	if (itemValue == null || selectedValue == null) return Object.is(itemValue, selectedValue);
	return comparer(itemValue, selectedValue);
}
function findItemIndex(itemValues, selectedValue, comparer) {
	if (!itemValues || itemValues.length === 0) return -1;
	return itemValues.findIndex((itemValue) => {
		if (itemValue === void 0) return false;
		return compareItemEquality(itemValue, selectedValue, comparer);
	});
}
function removeItem(selectedValues, itemValue, comparer) {
	return selectedValues.filter((selectedValue) => !compareItemEquality(itemValue, selectedValue, comparer));
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/serializeValue.mjs
function serializeValue(value) {
	if (value == null) return "";
	if (typeof value === "string") return value;
	try {
		return JSON.stringify(value);
	} catch {
		return String(value);
	}
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/resolveValueLabel.mjs
function isGroupedItems(items) {
	return items != null && items.length > 0 && typeof items[0] === "object" && items[0] != null && "items" in items[0];
}
/**
* Checks if the items array contains an item with a null value that has a non-null label.
*/
function hasNullItemLabel(items) {
	if (!Array.isArray(items)) return items != null && "null" in items;
	const arrayItems = items;
	if (isGroupedItems(arrayItems)) {
		for (const group of arrayItems) for (const item of group.items) if (item && item.value == null && item.label != null) return true;
		return false;
	}
	for (const item of arrayItems) if (item && item.value == null && item.label != null) return true;
	return false;
}
function stringifyAsLabel(item, itemToStringLabel) {
	if (itemToStringLabel && item != null) return itemToStringLabel(item) ?? "";
	if (item && typeof item === "object") {
		if ("label" in item && item.label != null) return String(item.label);
		if ("value" in item) return String(item.value);
	}
	return serializeValue(item);
}
function stringifyAsValue(item, itemToStringValue) {
	if (itemToStringValue && item != null) return itemToStringValue(item) ?? "";
	if (item && typeof item === "object" && "value" in item && "label" in item) return serializeValue(item.value);
	return serializeValue(item);
}
function resolveSelectedLabel(value, items, itemToStringLabel) {
	function fallback() {
		return stringifyAsLabel(value, itemToStringLabel);
	}
	if (itemToStringLabel && value != null) return itemToStringLabel(value);
	if (value && typeof value === "object" && "label" in value && value.label != null) return value.label;
	if (items && !Array.isArray(items)) return items[value] ?? fallback();
	if (Array.isArray(items)) {
		const arrayItems = items;
		const flatItems = isGroupedItems(arrayItems) ? arrayItems.flatMap((group) => group.items) : arrayItems;
		if (value == null || typeof value !== "object") {
			const match = flatItems.find((item) => item.value === value);
			if (match && match.label != null) return match.label;
			return fallback();
		}
		if ("value" in value) {
			const match = flatItems.find((item) => item && item.value === value.value);
			if (match && match.label != null) return match.label;
		}
	}
	return fallback();
}
function resolveMultipleLabels(values, items, itemToStringLabel) {
	return values.reduce((acc, value, index) => {
		if (index > 0) acc.push(", ");
		acc.push(/* @__PURE__ */ jsx(React$3.Fragment, { children: resolveSelectedLabel(value, items, itemToStringLabel) }, index));
		return acc;
	}, []);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/select/store.mjs
var selectors = {
	id: (state) => state.id,
	labelId: (state) => state.labelId,
	modal: (state) => state.modal,
	items: (state) => state.items,
	itemToStringLabel: (state) => state.itemToStringLabel,
	isItemEqualToValue: (state) => state.isItemEqualToValue,
	value: (state) => state.value,
	hasSelectedValue: (state) => {
		const { value, multiple, itemToStringValue } = state;
		if (value == null) return false;
		if (multiple && Array.isArray(value)) return value.length > 0;
		return stringifyAsValue(value, itemToStringValue) !== "";
	},
	hasNullItemLabel: (state, enabled) => {
		return enabled ? hasNullItemLabel(state.items) : false;
	},
	open: (state) => state.open,
	mounted: (state) => state.mounted,
	forceMount: (state) => state.forceMount,
	transitionStatus: (state) => state.transitionStatus,
	openMethod: (state) => state.openMethod,
	activeIndex: (state) => state.activeIndex,
	selectedIndex: (state) => state.selectedIndex,
	isActive: (state, index) => state.activeIndex === index,
	isSelected: (state, itemValue) => {
		const comparer = state.isItemEqualToValue;
		const storeValue = state.value;
		if (state.multiple) return Array.isArray(storeValue) && storeValue.some((selectedItem) => compareItemEquality(itemValue, selectedItem, comparer));
		return compareItemEquality(itemValue, storeValue, comparer);
	},
	isSelectedByFocus: (state, index) => {
		return state.selectedIndex === index;
	},
	popupProps: (state) => state.popupProps,
	triggerProps: (state) => state.triggerProps,
	triggerElement: (state) => state.triggerElement,
	positionerElement: (state) => state.positionerElement,
	listElement: (state) => state.listElement,
	popupSide: (state) => state.popupSide,
	scrollUpArrowVisible: (state) => state.scrollUpArrowVisible,
	scrollDownArrowVisible: (state) => state.scrollDownArrowVisible,
	hasScrollArrows: (state) => state.hasScrollArrows
};
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/areArraysEqual.mjs
function areArraysEqual(array1, array2, itemComparer = (a, b) => a === b) {
	return array1.length === array2.length && array1.every((value, index) => itemComparer(value, array2[index]));
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/internals/clamp.mjs
function clamp(val, min = Number.MIN_SAFE_INTEGER, max = Number.MAX_SAFE_INTEGER) {
	return Math.max(min, Math.min(val, max));
}
function getMaxScrollOffset(scrollSize, clientSize) {
	return Math.max(0, scrollSize - clientSize);
}
function normalizeScrollOffset(value, max) {
	if (max <= 0) return 0;
	const clamped = clamp(value, 0, max);
	const startDistance = clamped;
	const endDistance = max - clamped;
	const withinStartTolerance = startDistance <= 1;
	const withinEndTolerance = endDistance <= 1;
	if (withinStartTolerance && withinEndTolerance) return startDistance <= endDistance ? 0 : max;
	if (withinStartTolerance) return 0;
	if (withinEndTolerance) return max;
	return clamped;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/select/root/SelectRoot.mjs
/**
* Groups all parts of the select.
* Doesn't render its own HTML element.
*
* Documentation: [Base UI Select](https://base-ui.com/react/components/select)
*/
function SelectRoot(props) {
	const { id, value: valueProp, defaultValue = null, onValueChange, open: openProp, defaultOpen = false, onOpenChange, name: nameProp, form, autoComplete, disabled: disabledProp = false, readOnly = false, required = false, modal = true, actionsRef, inputRef, onOpenChangeComplete, items, multiple = false, itemToStringLabel, itemToStringValue, isItemEqualToValue = defaultItemEquality, highlightItemOnHover = true, children } = props;
	const { clearErrors } = useFormContext();
	const { setDirty, setTouched, setFocused, validityData, setFilled, name: fieldName, disabled: fieldDisabled, validation, validationMode } = useFieldRootContext();
	const generatedId = useLabelableId({ id });
	const disabled = fieldDisabled || disabledProp;
	const name = fieldName ?? nameProp;
	const [value, setValueUnwrapped] = useControlled({
		controlled: valueProp,
		default: multiple ? defaultValue ?? EMPTY_ARRAY$1 : defaultValue,
		name: "Select",
		state: "value"
	});
	const [open, setOpenUnwrapped] = useControlled({
		controlled: openProp,
		default: defaultOpen,
		name: "Select",
		state: "open"
	});
	const listRef = React$3.useRef([]);
	const labelsRef = React$3.useRef([]);
	const popupRef = React$3.useRef(null);
	const scrollHandlerRef = React$3.useRef(null);
	const scrollArrowsMountedCountRef = React$3.useRef(0);
	const valueRef = React$3.useRef(null);
	const valuesRef = React$3.useRef([]);
	const typingRef = React$3.useRef(false);
	const firstItemTextRef = React$3.useRef(null);
	const selectedItemTextRef = React$3.useRef(null);
	const selectionRef = React$3.useRef({
		allowSelectedMouseUp: false,
		allowUnselectedMouseUp: false,
		dragY: 0
	});
	const alignItemWithTriggerActiveRef = React$3.useRef(false);
	const { mounted, setMounted, transitionStatus } = useTransitionStatus(open);
	const { openMethod, triggerProps: interactionTypeProps } = useOpenInteractionType(open);
	const store = useRefWithInit(() => new ReactStore({
		id: generatedId,
		labelId: void 0,
		modal,
		multiple,
		itemToStringLabel,
		itemToStringValue,
		isItemEqualToValue,
		value,
		open,
		mounted,
		transitionStatus,
		items,
		forceMount: false,
		openMethod: null,
		activeIndex: null,
		selectedIndex: null,
		popupProps: {},
		triggerProps: {},
		triggerElement: null,
		positionerElement: null,
		listElement: null,
		popupSide: null,
		scrollUpArrowVisible: false,
		scrollDownArrowVisible: false,
		hasScrollArrows: false
	})).current;
	const activeIndex = useStore(store, selectors.activeIndex);
	const selectedIndex = useStore(store, selectors.selectedIndex);
	const triggerElement = useStore(store, selectors.triggerElement);
	const positionerElement = useStore(store, selectors.positionerElement);
	const previousOpenMethod = usePreviousValue(openMethod);
	const renderedOpenMethod = openMethod ?? previousOpenMethod;
	const serializedValue = React$3.useMemo(() => {
		if (multiple) return "";
		return stringifyAsValue(value, itemToStringValue);
	}, [
		multiple,
		value,
		itemToStringValue
	]);
	const fieldStringValue = React$3.useMemo(() => {
		if (multiple && Array.isArray(value)) return value.map((currentValue) => stringifyAsValue(currentValue, itemToStringValue));
		return stringifyAsValue(value, itemToStringValue);
	}, [
		multiple,
		value,
		itemToStringValue
	]);
	useRegisterFieldControl(useValueAsRef(triggerElement), generatedId, value, useStableCallback(() => fieldStringValue), !disabled, nameProp);
	const initialValueRef = React$3.useRef(value);
	const hasSelectedValue = multiple ? Array.isArray(value) && value.length > 0 : value != null && serializedValue !== "";
	useIsoLayoutEffect(() => {
		setFilled(hasSelectedValue);
	}, [hasSelectedValue, setFilled]);
	useIsoLayoutEffect(function syncSelectedIndex() {
		let target = value;
		let empty = false;
		if (multiple) {
			const currentValue = Array.isArray(value) ? value : [];
			empty = currentValue.length === 0;
			target = currentValue[currentValue.length - 1];
		}
		const index = empty ? -1 : findItemIndex(valuesRef.current, target, isItemEqualToValue);
		const nextIndex = index === -1 ? null : index;
		if (nextIndex === null) selectedItemTextRef.current = null;
		if (open) return;
		store.set("selectedIndex", nextIndex);
	}, [
		multiple,
		open,
		value,
		isItemEqualToValue,
		store
	]);
	function isSelectedValueDirty(currentValue) {
		const initialValue = validityData.initialValue;
		if (Array.isArray(currentValue) && Array.isArray(initialValue)) return !areArraysEqual(currentValue, initialValue, (itemValue, initialItemValue) => compareItemEquality(itemValue, initialItemValue, isItemEqualToValue));
		return currentValue !== initialValue;
	}
	useValueChanged(value, () => {
		clearErrors(name);
		setDirty(isSelectedValueDirty(value));
		validation.change(value);
	});
	const setOpen = useStableCallback((nextOpen, eventDetails) => {
		onOpenChange?.(nextOpen, eventDetails);
		if (eventDetails.isCanceled) return;
		setOpenUnwrapped(nextOpen);
		if (!nextOpen && (eventDetails.reason === "focus-out" || eventDetails.reason === "outside-press")) {
			setTouched(true);
			setFocused(false);
			if (validationMode === "onBlur") validation.commit(value);
		}
	});
	const handleUnmount = useStableCallback(() => {
		setMounted(false);
		store.update({
			activeIndex: null,
			openMethod: null,
			scrollUpArrowVisible: false,
			scrollDownArrowVisible: false
		});
		onOpenChangeComplete?.(false);
	});
	useOpenChangeComplete({
		enabled: !actionsRef,
		open,
		ref: popupRef,
		onComplete() {
			if (!open) handleUnmount();
		}
	});
	React$3.useImperativeHandle(actionsRef, () => ({ unmount: handleUnmount }), [handleUnmount]);
	const setValue = useStableCallback((nextValue, eventDetails) => {
		onValueChange?.(nextValue, eventDetails);
		if (eventDetails.isCanceled) return;
		setValueUnwrapped(nextValue);
	});
	const handleScrollArrowVisibility = useStableCallback((scroller) => {
		const maxScrollTop = getMaxScrollOffset(scroller.scrollHeight, scroller.clientHeight);
		const scrollTop = normalizeScrollOffset(scroller.scrollTop, maxScrollTop);
		const shouldShowUp = scrollTop > 0;
		const shouldShowDown = scrollTop < maxScrollTop;
		store.set("scrollUpArrowVisible", shouldShowUp);
		store.set("scrollDownArrowVisible", shouldShowDown);
	});
	const floatingContext = useFloatingRootContext({
		open,
		onOpenChange: setOpen,
		elements: {
			reference: triggerElement,
			floating: positionerElement
		}
	});
	const click = useClick(floatingContext, {
		enabled: !readOnly && !disabled,
		event: "mousedown"
	});
	const dismiss = useDismiss(floatingContext);
	const listNavigation = useListNavigation(floatingContext, {
		enabled: !readOnly && !disabled,
		listRef,
		activeIndex,
		selectedIndex,
		disabledIndices: EMPTY_ARRAY$1,
		onNavigate(nextActiveIndex) {
			if (nextActiveIndex === null && !open) return;
			store.set("activeIndex", nextActiveIndex);
		},
		focusItemOnHover: highlightItemOnHover
	});
	const typeahead = useTypeahead(floatingContext, {
		enabled: !readOnly && !disabled && (open || !multiple),
		listRef: labelsRef,
		activeIndex,
		selectedIndex,
		disabledIndices: (index) => isElementDisabled(listRef.current[index]),
		onMatch(index) {
			if (open) store.set("activeIndex", index);
			else setValue(valuesRef.current[index], createChangeEventDetails(none));
		},
		onTyping(typing) {
			typingRef.current = typing;
		}
	});
	const mergedTriggerProps = React$3.useMemo(() => mergeProps(typeahead.reference, listNavigation.reference, dismiss.reference, click.reference, interactionTypeProps), [
		click.reference,
		typeahead.reference,
		listNavigation.reference,
		dismiss.reference,
		interactionTypeProps
	]);
	const popupProps = React$3.useMemo(() => mergeProps(FOCUSABLE_POPUP_PROPS, typeahead.floating, listNavigation.floating, dismiss.floating), [
		typeahead.floating,
		listNavigation.floating,
		dismiss.floating
	]);
	const itemProps = listNavigation.item ?? EMPTY_OBJECT;
	useOnFirstRender(() => {
		store.update({
			popupProps,
			triggerProps: mergedTriggerProps
		});
	});
	store.useSyncedValues({
		id: generatedId,
		modal,
		multiple,
		value,
		open,
		mounted,
		transitionStatus,
		popupProps,
		triggerProps: mergedTriggerProps,
		items,
		itemToStringLabel,
		itemToStringValue,
		isItemEqualToValue,
		openMethod: renderedOpenMethod
	});
	const contextValue = React$3.useMemo(() => ({
		store,
		floatingContext,
		required,
		disabled,
		readOnly,
		multiple,
		highlightItemOnHover,
		setValue,
		setOpen,
		listRef,
		popupRef,
		scrollHandlerRef,
		handleScrollArrowVisibility,
		scrollArrowsMountedCountRef,
		itemProps,
		valueRef,
		valuesRef,
		labelsRef,
		typingRef,
		selectionRef,
		firstItemTextRef,
		selectedItemTextRef,
		validation,
		onOpenChangeComplete,
		alignItemWithTriggerActiveRef,
		initialValueRef
	}), [
		store,
		floatingContext,
		required,
		disabled,
		readOnly,
		multiple,
		highlightItemOnHover,
		setValue,
		setOpen,
		itemProps,
		validation,
		onOpenChangeComplete,
		handleScrollArrowVisibility
	]);
	const ref = useMergedRefs(inputRef, validation.inputRef);
	const hiddenInputName = multiple ? void 0 : name;
	const hiddenInputs = React$3.useMemo(() => {
		if (!multiple || !Array.isArray(value) || !name) return null;
		return value.map((v) => {
			const currentSerializedValue = stringifyAsValue(v, itemToStringValue);
			return /* @__PURE__ */ jsx("input", {
				type: "hidden",
				form,
				name,
				value: currentSerializedValue,
				disabled
			}, currentSerializedValue);
		});
	}, [
		multiple,
		value,
		form,
		name,
		itemToStringValue,
		disabled
	]);
	return /* @__PURE__ */ jsxs(SelectRootContext.Provider, {
		value: contextValue,
		children: [
			children,
			/* @__PURE__ */ jsx("input", {
				...validation.getValidationProps(disabled, {
					onFocus() {
						store.state.triggerElement?.focus({ focusVisible: true });
					},
					onChange(event) {
						if (event.nativeEvent.defaultPrevented || disabled || readOnly) return;
						const nextValue = event.currentTarget.value;
						const details = createChangeEventDetails(none, event.nativeEvent);
						function handleChange() {
							if (multiple) return;
							const nextValueLower = nextValue.toLowerCase();
							let matchingIndex = valuesRef.current.findIndex((candidate) => stringifyAsValue(candidate, itemToStringValue).toLowerCase() === nextValueLower || stringifyAsLabel(candidate, itemToStringLabel).toLowerCase() === nextValueLower);
							if (matchingIndex === -1) matchingIndex = valuesRef.current.findIndex((_, index) => {
								const renderedLabel = labelsRef.current[index];
								return renderedLabel != null && renderedLabel.toLowerCase() === nextValueLower;
							});
							const matchingValue = valuesRef.current[matchingIndex];
							if (matchingValue != null) setValue(matchingValue, details);
						}
						store.set("forceMount", true);
						queueMicrotask(handleChange);
					}
				}),
				id: generatedId && hiddenInputName == null ? `${generatedId}-hidden-input` : void 0,
				form,
				name: hiddenInputName,
				autoComplete,
				value: serializedValue,
				disabled,
				required: required && !(multiple && hasSelectedValue),
				readOnly,
				ref,
				style: name ? visuallyHiddenInput : visuallyHidden,
				tabIndex: -1,
				"aria-hidden": true,
				suppressHydrationWarning: true
			}),
			hiddenInputs
		]
	});
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/resolveAriaLabelledBy.mjs
function resolveAriaLabelledBy(fieldLabelId, localLabelId) {
	return fieldLabelId ?? localLabelId;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/getPseudoElementBounds.mjs
var BOUNDARY_OFFSET = 5;
/**
* Determines if a mouse event occurred within the bounds of an element
* (including its pseudo-elements), with a small tolerance for pointer drift.
*/
function isMouseWithinBounds(event, element) {
	const bounds = getPseudoElementBounds(element);
	return event.clientX >= bounds.left - BOUNDARY_OFFSET && event.clientX <= bounds.right + BOUNDARY_OFFSET && event.clientY >= bounds.top - BOUNDARY_OFFSET && event.clientY <= bounds.bottom + BOUNDARY_OFFSET;
}
function getPseudoElementBounds(element) {
	const elementRect = element.getBoundingClientRect();
	const win = getWindow(element);
	if (jsdom) return elementRect;
	const beforeStyles = win.getComputedStyle(element, "::before");
	const afterStyles = win.getComputedStyle(element, "::after");
	if (!(beforeStyles.content !== "none" || afterStyles.content !== "none")) return elementRect;
	const beforeWidth = parseFloat(beforeStyles.width) || 0;
	const beforeHeight = parseFloat(beforeStyles.height) || 0;
	const afterWidth = parseFloat(afterStyles.width) || 0;
	const afterHeight = parseFloat(afterStyles.height) || 0;
	const totalWidth = Math.max(elementRect.width, beforeWidth, afterWidth);
	const totalHeight = Math.max(elementRect.height, beforeHeight, afterHeight);
	const widthDiff = totalWidth - elementRect.width;
	const heightDiff = totalHeight - elementRect.height;
	return {
		left: elementRect.left - widthDiff / 2,
		right: elementRect.right + widthDiff / 2,
		top: elementRect.top - heightDiff / 2,
		bottom: elementRect.bottom + heightDiff / 2
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/select/trigger/SelectTrigger.mjs
var SELECTED_DELAY = 400;
var stateAttributesMapping$2 = {
	...pressableTriggerOpenStateMapping,
	...fieldValidityMapping,
	popupSide: (side) => side ? { "data-popup-side": side } : null,
	value: () => null
};
/**
* A button that opens the select popup.
* Renders a `<button>` element.
*
* Documentation: [Base UI Select](https://base-ui.com/react/components/select)
*/
var SelectTrigger$1 = /* @__PURE__ */ React$3.forwardRef(function SelectTrigger(componentProps, forwardedRef) {
	const { render, className, id: idProp, disabled: disabledProp = false, nativeButton = true, style, ...elementProps } = componentProps;
	const { setTouched, setFocused, validationMode, state: fieldState, disabled: fieldDisabled } = useFieldRootContext();
	const { labelId: fieldLabelId } = useLabelableContext();
	const { store, setOpen, selectionRef, validation, readOnly, required, alignItemWithTriggerActiveRef, disabled: selectDisabled } = useSelectRootContext();
	const disabled = fieldDisabled || selectDisabled || disabledProp;
	const open = useStore(store, selectors.open);
	const mounted = useStore(store, selectors.mounted);
	const value = useStore(store, selectors.value);
	const triggerProps = useStore(store, selectors.triggerProps);
	const positionerElement = useStore(store, selectors.positionerElement);
	const listElement = useStore(store, selectors.listElement);
	const popupSideValue = useStore(store, selectors.popupSide);
	const rootId = useStore(store, selectors.id);
	const selectLabelId = useStore(store, selectors.labelId);
	const hasSelectedValue = useStore(store, selectors.hasSelectedValue);
	const popupSide = mounted && positionerElement ? popupSideValue : null;
	const id = idProp ?? rootId;
	const ariaLabelledBy = resolveAriaLabelledBy(fieldLabelId, selectLabelId);
	useLabelableId({ id });
	const positionerRef = useValueAsRef(positionerElement);
	const triggerRef = React$3.useRef(null);
	const { getButtonProps, buttonRef } = useButton({
		disabled,
		native: nativeButton
	});
	const setTriggerElement = store.useStateSetter("triggerElement");
	const timeoutFocus = useTimeout();
	const timeoutMouseDown = useTimeout();
	const selectedDelayTimeout = useTimeout();
	React$3.useEffect(() => {
		if (open) {
			selectedDelayTimeout.start(SELECTED_DELAY, () => {
				selectionRef.current.allowUnselectedMouseUp = true;
				selectionRef.current.allowSelectedMouseUp = true;
			});
			return () => {
				selectedDelayTimeout.clear();
			};
		}
		selectionRef.current = {
			allowSelectedMouseUp: false,
			allowUnselectedMouseUp: false,
			dragY: 0
		};
		timeoutMouseDown.clear();
	}, [
		open,
		selectionRef,
		timeoutMouseDown,
		selectedDelayTimeout
	]);
	const mergedProps = mergeProps(triggerProps, {
		id,
		role: "combobox",
		"aria-expanded": open,
		"aria-haspopup": "listbox",
		"aria-controls": open ? listElement?.id ?? getFloatingFocusElement(positionerElement)?.id : void 0,
		"aria-labelledby": ariaLabelledBy,
		"aria-readonly": readOnly || void 0,
		"aria-required": required || void 0,
		tabIndex: disabled ? -1 : 0,
		onFocus(event) {
			setFocused(true);
			if (open && alignItemWithTriggerActiveRef.current) setOpen(false, createChangeEventDetails(none, event.nativeEvent));
			timeoutFocus.start(0, () => {
				store.set("forceMount", true);
			});
		},
		onBlur(event) {
			if (contains(positionerElement, event.relatedTarget)) return;
			setTouched(true);
			setFocused(false);
			if (validationMode === "onBlur") validation.commit(value);
		},
		onMouseDown(event) {
			if (open) return;
			const doc = ownerDocument(event.currentTarget);
			function handleMouseUp(mouseEvent) {
				if (!triggerRef.current) return;
				const mouseUpTarget = mouseEvent.target;
				if (contains(triggerRef.current, mouseUpTarget) || contains(positionerRef.current, mouseUpTarget)) return;
				if (isMouseWithinBounds(mouseEvent, triggerRef.current)) return;
				setOpen(false, createChangeEventDetails(cancelOpen, mouseEvent));
			}
			timeoutMouseDown.start(0, () => {
				doc.addEventListener("mouseup", handleMouseUp, { once: true });
			});
		}
	}, elementProps, getButtonProps);
	const props = validation.getValidationProps(disabled, mergedProps);
	props.role = "combobox";
	const state = {
		...fieldState,
		open,
		disabled,
		value,
		readOnly,
		popupSide,
		placeholder: !hasSelectedValue
	};
	return useRenderElement("button", componentProps, {
		ref: [
			forwardedRef,
			triggerRef,
			buttonRef,
			setTriggerElement
		],
		state,
		stateAttributesMapping: stateAttributesMapping$2,
		props
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/select/value/SelectValue.mjs
var stateAttributesMapping$1 = { value: () => null };
/**
* A text label of the currently selected item.
* Renders a `<span>` element.
*
* Documentation: [Base UI Select](https://base-ui.com/react/components/select)
*/
var SelectValue$1 = /* @__PURE__ */ React$3.forwardRef(function SelectValue(componentProps, forwardedRef) {
	const { className, render, children: childrenProp, placeholder, style, ...elementProps } = componentProps;
	const { store, valueRef } = useSelectRootContext();
	const value = useStore(store, selectors.value);
	const items = useStore(store, selectors.items);
	const itemToStringLabel = useStore(store, selectors.itemToStringLabel);
	const hasSelectedValue = useStore(store, selectors.hasSelectedValue);
	const shouldCheckNullItemLabel = !hasSelectedValue && placeholder != null && childrenProp == null;
	const hasNullLabel = useStore(store, selectors.hasNullItemLabel, shouldCheckNullItemLabel);
	const state = {
		value,
		placeholder: !hasSelectedValue
	};
	let children = null;
	if (typeof childrenProp === "function") children = childrenProp(value);
	else if (childrenProp != null) children = childrenProp;
	else if (shouldCheckNullItemLabel && !hasNullLabel) children = placeholder;
	else if (Array.isArray(value)) children = resolveMultipleLabels(value, items, itemToStringLabel);
	else children = resolveSelectedLabel(value, items, itemToStringLabel);
	return useRenderElement("span", componentProps, {
		state,
		ref: [forwardedRef, valueRef],
		props: [{ children }, elementProps],
		stateAttributesMapping: stateAttributesMapping$1
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/select/icon/SelectIcon.mjs
/**
* An icon that indicates that the trigger button opens a select popup.
* Renders a `<span>` element.
*
* Documentation: [Base UI Select](https://base-ui.com/react/components/select)
*/
var SelectIcon = /* @__PURE__ */ React$3.forwardRef(function SelectIcon(componentProps, forwardedRef) {
	const { render, className, style, ...elementProps } = componentProps;
	const { store } = useSelectRootContext();
	return useRenderElement("span", componentProps, {
		state: { open: useStore(store, selectors.open) },
		ref: forwardedRef,
		props: [{
			"aria-hidden": true,
			children: "▼"
		}, elementProps],
		stateAttributesMapping: triggerOpenStateMapping
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/select/portal/SelectPortal.mjs
/**
* A portal element that moves the popup to a different part of the DOM.
* By default, the portal element is appended to `<body>`.
* Renders a `<div>` element.
*
* Documentation: [Base UI Select](https://base-ui.com/react/components/select)
*/
var SelectPortal = /* @__PURE__ */ React$3.forwardRef(function SelectPortal(portalProps, forwardedRef) {
	const { store } = useSelectRootContext();
	const mounted = useStore(store, selectors.mounted);
	const forceMount = useStore(store, selectors.forceMount);
	if (!(mounted || forceMount)) return null;
	return /* @__PURE__ */ jsx(FloatingPortal, {
		ref: forwardedRef,
		...portalProps
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/select/positioner/SelectPositionerContext.mjs
var SelectPositionerContext = /* @__PURE__ */ React$3.createContext(void 0);
function useSelectPositionerContext() {
	const context = React$3.useContext(SelectPositionerContext);
	if (!context) throw new Error(formatErrorMessage(59));
	return context;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/select/popup/utils.mjs
function clearStyles(element, originalStyles) {
	if (element) Object.assign(element.style, originalStyles);
}
var LIST_FUNCTIONAL_STYLES = {
	position: "relative",
	maxHeight: "100%",
	overflowX: "hidden",
	overflowY: "auto"
};
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/useAnchoredPopupScrollLock.mjs
var VIEWPORT_WIDTH_TOLERANCE_PX = 20;
/**
* Manages scroll lock for anchored popups. For non-touch opens, scroll lock is applied when
* enabled. For touch opens, scroll lock is applied only when the positioner width is effectively
* viewport-sized.
*/
function useAnchoredPopupScrollLock(enabled, touchOpen, positionerElement, referenceElement) {
	const [touchOpenShouldLockScroll, setTouchOpenShouldLockScroll] = React$3.useState(false);
	useIsoLayoutEffect(() => {
		if (!enabled || !touchOpen || positionerElement == null) {
			setTouchOpenShouldLockScroll(false);
			return;
		}
		const viewportWidth = ownerDocument(positionerElement).documentElement.clientWidth;
		const popupWidth = positionerElement.offsetWidth;
		setTouchOpenShouldLockScroll(viewportWidth > 0 && popupWidth > 0 && popupWidth >= viewportWidth - VIEWPORT_WIDTH_TOLERANCE_PX);
	}, [
		enabled,
		touchOpen,
		positionerElement
	]);
	useScrollLock(enabled && (!touchOpen || touchOpenShouldLockScroll), referenceElement);
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/select/positioner/SelectPositioner.mjs
var FIXED = { position: "fixed" };
/**
* Positions the select popup.
* Renders a `<div>` element.
*
* Documentation: [Base UI Select](https://base-ui.com/react/components/select)
*/
var SelectPositioner = /* @__PURE__ */ React$3.forwardRef(function SelectPositioner(componentProps, forwardedRef) {
	const { anchor, className, render, positionMethod, side, align, sideOffset, alignOffset, collisionBoundary = "clipping-ancestors", collisionPadding, arrowPadding, sticky, disableAnchorTracking, alignItemWithTrigger = true, collisionAvoidance = DROPDOWN_COLLISION_AVOIDANCE, style, ...elementProps } = componentProps;
	const { store, listRef, labelsRef, alignItemWithTriggerActiveRef, selectedItemTextRef, valuesRef, initialValueRef, popupRef, setValue, floatingContext: floatingRootContext } = useSelectRootContext();
	const open = useStore(store, selectors.open);
	const mounted = useStore(store, selectors.mounted);
	const modal = useStore(store, selectors.modal);
	const value = useStore(store, selectors.value);
	const openMethod = useStore(store, selectors.openMethod);
	const positionerElement = useStore(store, selectors.positionerElement);
	const triggerElement = useStore(store, selectors.triggerElement);
	const isItemEqualToValue = useStore(store, selectors.isItemEqualToValue);
	const transitionStatus = useStore(store, selectors.transitionStatus);
	const scrollUpArrowRef = React$3.useRef(null);
	const scrollDownArrowRef = React$3.useRef(null);
	const [controlledAlignItemWithTrigger, setControlledAlignItemWithTrigger] = React$3.useState(alignItemWithTrigger);
	const alignItemWithTriggerActive = mounted && controlledAlignItemWithTrigger && openMethod !== "touch";
	if (!mounted && controlledAlignItemWithTrigger !== alignItemWithTrigger) setControlledAlignItemWithTrigger(alignItemWithTrigger);
	React$3.useImperativeHandle(alignItemWithTriggerActiveRef, () => alignItemWithTriggerActive);
	useAnchoredPopupScrollLock((alignItemWithTriggerActive || modal) && open, openMethod === "touch", positionerElement, triggerElement);
	const positioning = useAnchorPositioning({
		anchor,
		floatingRootContext,
		positionMethod,
		mounted,
		side,
		sideOffset,
		align,
		alignOffset,
		arrowPadding,
		collisionBoundary,
		collisionPadding,
		sticky,
		disableAnchorTracking: disableAnchorTracking ?? alignItemWithTriggerActive,
		collisionAvoidance,
		keepMounted: true
	});
	const renderedSide = alignItemWithTriggerActive ? "none" : positioning.side;
	const positionerStyles = alignItemWithTriggerActive ? FIXED : positioning.positionerStyles;
	const state = {
		open,
		side: renderedSide,
		align: positioning.align,
		anchorHidden: positioning.anchorHidden
	};
	useIsoLayoutEffect(() => {
		store.set("popupSide", positioning.side);
	}, [store, positioning.side]);
	const element = usePositioner(componentProps, state, {
		styles: positionerStyles,
		transitionStatus,
		props: elementProps,
		refs: [forwardedRef, store.useStateSetter("positionerElement")],
		hidden: !mounted,
		inert: !open
	});
	const prevMapSizeRef = React$3.useRef(0);
	const onMapChange = useStableCallback((map) => {
		if (valuesRef.current.length === 0) return;
		const prevSize = prevMapSizeRef.current;
		prevMapSizeRef.current = map.size;
		if (map.size === prevSize) return;
		const eventDetails = createChangeEventDetails(none);
		if (prevSize !== 0 && !store.state.multiple && value !== null) {
			if (findItemIndex(valuesRef.current, value, isItemEqualToValue) === -1) {
				const initialSelectedValue = initialValueRef.current;
				const nextValue = initialSelectedValue != null && findItemIndex(valuesRef.current, initialSelectedValue, isItemEqualToValue) !== -1 ? initialSelectedValue : null;
				setValue(nextValue, eventDetails);
				if (nextValue === null) {
					store.set("selectedIndex", null);
					selectedItemTextRef.current = null;
				}
			}
		}
		if (prevSize !== 0 && store.state.multiple && Array.isArray(value)) {
			const nextValue = value.filter((selectedItemValue) => findItemIndex(valuesRef.current, selectedItemValue, isItemEqualToValue) !== -1);
			if (nextValue.length !== value.length) {
				setValue(nextValue, eventDetails);
				if (nextValue.length === 0) {
					store.set("selectedIndex", null);
					selectedItemTextRef.current = null;
				}
			}
		}
		if (open && alignItemWithTriggerActive) {
			store.update({
				scrollUpArrowVisible: false,
				scrollDownArrowVisible: false
			});
			const stylesToClear = { height: "" };
			clearStyles(positionerElement, stylesToClear);
			clearStyles(popupRef.current, stylesToClear);
		}
	});
	const contextValue = React$3.useMemo(() => ({
		...positioning,
		side: renderedSide,
		alignItemWithTriggerActive,
		setControlledAlignItemWithTrigger,
		scrollUpArrowRef,
		scrollDownArrowRef
	}), [
		positioning,
		renderedSide,
		alignItemWithTriggerActive,
		setControlledAlignItemWithTrigger
	]);
	return /* @__PURE__ */ jsx(CompositeList, {
		elementsRef: listRef,
		labelsRef,
		onMapChange,
		children: /* @__PURE__ */ jsxs(SelectPositionerContext.Provider, {
			value: contextValue,
			children: [mounted && modal && /* @__PURE__ */ jsx(InternalBackdrop, {
				inert: inertValue(!open),
				cutout: triggerElement
			}), element]
		})
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/utils/styles.mjs
var DISABLE_SCROLLBAR_CLASS_NAME = "base-ui-disable-scrollbar";
var styleDisableScrollbar = {
	className: DISABLE_SCROLLBAR_CLASS_NAME,
	getElement(nonce) {
		return /* @__PURE__ */ jsx("style", {
			nonce,
			href: DISABLE_SCROLLBAR_CLASS_NAME,
			precedence: "base-ui:low",
			children: `.${DISABLE_SCROLLBAR_CLASS_NAME}{scrollbar-width:none}.${DISABLE_SCROLLBAR_CLASS_NAME}::-webkit-scrollbar{display:none}`
		});
	}
};
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/toolbar/root/ToolbarRootContext.mjs
var ToolbarRootContext = /* @__PURE__ */ React$3.createContext(void 0);
function useToolbarRootContext(optional) {
	const context = React$3.useContext(ToolbarRootContext);
	if (context === void 0 && !optional) throw new Error(formatErrorMessage(69));
	return context;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/select/popup/SelectPopup.mjs
var stateAttributesMapping = {
	...popupStateMapping,
	...transitionStatusMapping
};
/**
* A container for the select list.
* Renders a `<div>` element.
*
* Documentation: [Base UI Select](https://base-ui.com/react/components/select)
*/
var SelectPopup = /* @__PURE__ */ React$3.forwardRef(function SelectPopup(componentProps, forwardedRef) {
	const { render, className, style, finalFocus, ...elementProps } = componentProps;
	const { store, popupRef, onOpenChangeComplete, setOpen, valueRef, firstItemTextRef, selectedItemTextRef, multiple, handleScrollArrowVisibility, scrollHandlerRef, listRef, highlightItemOnHover, floatingContext: floatingRootContext } = useSelectRootContext();
	const { side, align, alignItemWithTriggerActive, isPositioned, setControlledAlignItemWithTrigger } = useSelectPositionerContext();
	const insideToolbar = useToolbarRootContext(true) != null;
	const direction = useDirection();
	const { nonce, disableStyleElements } = useCSPContext();
	const id = useStore(store, selectors.id);
	const open = useStore(store, selectors.open);
	const openMethod = useStore(store, selectors.openMethod);
	const mounted = useStore(store, selectors.mounted);
	const popupProps = useStore(store, selectors.popupProps);
	const transitionStatus = useStore(store, selectors.transitionStatus);
	const triggerElement = useStore(store, selectors.triggerElement);
	const positionerElement = useStore(store, selectors.positionerElement);
	const listElement = useStore(store, selectors.listElement);
	const reachedMaxHeightRef = React$3.useRef(false);
	const initialPlacedRef = React$3.useRef(false);
	const originalPositionerStylesRef = React$3.useRef({});
	const scrollArrowFrame = useAnimationFrame();
	const handleScroll = useStableCallback((scroller) => {
		if (!positionerElement || !popupRef.current || !initialPlacedRef.current) return;
		const isTopPositioned = positionerElement.style.top === "0px";
		const isBottomPositioned = positionerElement.style.bottom === "0px";
		if (reachedMaxHeightRef.current || !alignItemWithTriggerActive || !isTopPositioned && !isBottomPositioned) {
			handleScrollArrowVisibility(scroller);
			return;
		}
		const scale = getScale(positionerElement);
		const currentHeight = normalizeSize(positionerElement.getBoundingClientRect().height, "y", scale);
		const doc = ownerDocument(positionerElement);
		const win = getWindow(positionerElement);
		const positionerStyles = win.getComputedStyle(positionerElement);
		const marginTop = parseFloat(positionerStyles.marginTop);
		const marginBottom = parseFloat(positionerStyles.marginBottom);
		const maxPopupHeight = getMaxPopupHeight(win.getComputedStyle(popupRef.current));
		const maxAvailableHeight = Math.min(doc.documentElement.clientHeight - marginTop - marginBottom, maxPopupHeight);
		const scrollTop = scroller.scrollTop;
		const maxScrollTop = getMaxScrollTop(scroller);
		let nextScrollTop = null;
		const setHeight = (height) => {
			positionerElement.style.height = `${height}px`;
		};
		const diff = isTopPositioned ? maxScrollTop - scrollTop : scrollTop;
		const nextHeight = Math.min(currentHeight + diff, maxAvailableHeight);
		if (diff <= 1) {
			const heightDelta = clamp(diff, 0, maxAvailableHeight - currentHeight);
			if (heightDelta > 0) setHeight(currentHeight + heightDelta);
			scroller.scrollTop = isTopPositioned ? maxScrollTop : 0;
			if (maxAvailableHeight - (currentHeight + heightDelta) <= 1) reachedMaxHeightRef.current = true;
			handleScrollArrowVisibility(scroller);
			return;
		}
		if (maxAvailableHeight - nextHeight > 1) nextScrollTop = isTopPositioned ? Infinity : 0;
		else if (isBottomPositioned && scrollTop < maxScrollTop) nextScrollTop = scrollTop - (diff - (currentHeight + diff - maxAvailableHeight));
		const nextPositionerHeight = Math.ceil(nextHeight);
		if (nextPositionerHeight !== 0) setHeight(nextPositionerHeight);
		if (nextScrollTop != null) {
			const target = clamp(nextScrollTop, 0, getMaxScrollTop(scroller));
			if (Math.abs(scroller.scrollTop - target) > 1) scroller.scrollTop = target;
		}
		if (nextPositionerHeight >= maxAvailableHeight - 1) reachedMaxHeightRef.current = true;
		handleScrollArrowVisibility(scroller);
	});
	React$3.useImperativeHandle(scrollHandlerRef, () => handleScroll, [handleScroll]);
	useOpenChangeComplete({
		open,
		ref: popupRef,
		onComplete() {
			if (open) onOpenChangeComplete?.(true);
		}
	});
	const state = {
		open,
		transitionStatus,
		side,
		align
	};
	useIsoLayoutEffect(() => {
		if (!positionerElement || !popupRef.current || Object.keys(originalPositionerStylesRef.current).length) return;
		originalPositionerStylesRef.current = {
			top: positionerElement.style.top || "0",
			left: positionerElement.style.left || "0",
			right: positionerElement.style.right,
			height: positionerElement.style.height,
			bottom: positionerElement.style.bottom,
			minHeight: positionerElement.style.minHeight,
			maxHeight: positionerElement.style.maxHeight,
			marginTop: positionerElement.style.marginTop,
			marginBottom: positionerElement.style.marginBottom
		};
	}, [popupRef, positionerElement]);
	useIsoLayoutEffect(() => {
		if (open || alignItemWithTriggerActive) return;
		initialPlacedRef.current = false;
		reachedMaxHeightRef.current = false;
		clearStyles(positionerElement, originalPositionerStylesRef.current);
	}, [
		open,
		alignItemWithTriggerActive,
		positionerElement,
		popupRef
	]);
	useIsoLayoutEffect(() => {
		const popupElement = popupRef.current;
		if (!open || !triggerElement || !positionerElement || !popupElement || alignItemWithTriggerActive && !isPositioned || store.state.transitionStatus === "ending") return;
		initialPlacedRef.current = true;
		popupElement.style.removeProperty("--transform-origin");
		if (!alignItemWithTriggerActive) {
			scrollArrowFrame.request(() => handleScrollArrowVisibility(listElement || popupElement));
			return;
		}
		const restoreTransformStyles = unsetTransformStyles(popupElement);
		try {
			let textElement = selectedItemTextRef.current;
			if (!textElement?.isConnected) textElement = !selectors.hasSelectedValue(store.state) && firstItemTextRef.current?.isConnected ? firstItemTextRef.current : null;
			const valueElement = valueRef.current;
			const win = getWindow(positionerElement);
			const positionerStyles = win.getComputedStyle(positionerElement);
			const popupStyles = win.getComputedStyle(popupElement);
			const doc = ownerDocument(triggerElement);
			const scale = getScale(triggerElement);
			const triggerRect = normalizeRect(triggerElement.getBoundingClientRect(), scale);
			const positionerRect = normalizeRect(positionerElement.getBoundingClientRect(), scale);
			const triggerHeight = triggerRect.height;
			const scroller = listElement || popupElement;
			const scrollHeight = scroller.scrollHeight;
			const borderBottom = parseFloat(popupStyles.borderBottomWidth);
			const marginTop = parseFloat(positionerStyles.marginTop) || 10;
			const marginBottom = parseFloat(positionerStyles.marginBottom) || 10;
			const minHeight = parseFloat(positionerStyles.minHeight) || 100;
			const maxPopupHeight = getMaxPopupHeight(popupStyles);
			const paddingLeft = 5;
			const paddingRight = 5;
			const triggerCollisionThreshold = 20;
			const viewportHeight = doc.documentElement.clientHeight - marginTop - marginBottom;
			const viewportWidth = doc.documentElement.clientWidth;
			const availableSpaceBeneathTrigger = viewportHeight - triggerRect.bottom + triggerHeight;
			let textRect;
			let alignedLeft = direction === "rtl" ? triggerRect.right - positionerRect.width : triggerRect.left;
			let offsetY = 0;
			if (textElement && valueElement) {
				const valueRect = normalizeRect(valueElement.getBoundingClientRect(), scale);
				textRect = normalizeRect(textElement.getBoundingClientRect(), scale);
				alignedLeft = positionerRect.left + (direction === "rtl" ? valueRect.right - textRect.right : valueRect.left - textRect.left);
				const valueCenterFromTriggerTop = valueRect.top - triggerRect.top + valueRect.height / 2;
				offsetY = textRect.top - positionerRect.top + textRect.height / 2 - valueCenterFromTriggerTop;
			}
			const idealHeight = availableSpaceBeneathTrigger + offsetY + marginBottom + borderBottom;
			let height = Math.min(viewportHeight, idealHeight);
			const maxHeight = viewportHeight - marginTop - marginBottom;
			const scrollTop = idealHeight - height;
			const maxRight = viewportWidth - paddingRight;
			positionerElement.style.left = `${clamp(alignedLeft, paddingLeft, maxRight - positionerRect.width)}px`;
			positionerElement.style.height = `${height}px`;
			positionerElement.style.maxHeight = "none";
			positionerElement.style.marginTop = `${marginTop}px`;
			positionerElement.style.marginBottom = `${marginBottom}px`;
			popupElement.style.height = "100%";
			const maxScrollTop = getMaxScrollTop(scroller);
			const isTopPositioned = scrollTop >= maxScrollTop - 1;
			if (isTopPositioned) height = Math.min(viewportHeight, positionerRect.height) - (scrollTop - maxScrollTop);
			const fallbackToAlignPopupToTrigger = triggerRect.top < triggerCollisionThreshold || triggerRect.bottom > viewportHeight - triggerCollisionThreshold || Math.ceil(height) + 1 < Math.min(scrollHeight, minHeight);
			const isPinchZoomed = (win.visualViewport?.scale ?? 1) !== 1 && webkit;
			if (fallbackToAlignPopupToTrigger || isPinchZoomed) {
				clearStyles(positionerElement, originalPositionerStylesRef.current);
				setControlledAlignItemWithTrigger(false);
				return;
			}
			const initialHeight = Math.max(minHeight, height);
			if (isTopPositioned) {
				const topOffset = Math.max(0, viewportHeight - idealHeight);
				positionerElement.style.top = positionerRect.height >= maxHeight ? "0" : `${topOffset}px`;
				positionerElement.style.height = `${height}px`;
				scroller.scrollTop = getMaxScrollTop(scroller);
			} else {
				positionerElement.style.bottom = "0";
				scroller.scrollTop = scrollTop;
			}
			if (textRect) {
				const popupTop = positionerRect.top;
				const popupHeight = positionerRect.height;
				const textCenterY = textRect.top + textRect.height / 2;
				const clampedY = clamp(popupHeight > 0 ? (textCenterY - popupTop) / popupHeight * 100 : 50, 0, 100);
				popupElement.style.setProperty("--transform-origin", `50% ${clampedY}%`);
			}
			if (initialHeight === viewportHeight || height >= maxPopupHeight) reachedMaxHeightRef.current = true;
			handleScrollArrowVisibility(scroller);
			if (highlightItemOnHover && store.state.selectedIndex === null && store.state.activeIndex === null && listRef.current[0] != null) store.set("activeIndex", 0);
		} finally {
			restoreTransformStyles();
		}
	}, [
		store,
		open,
		positionerElement,
		triggerElement,
		valueRef,
		firstItemTextRef,
		selectedItemTextRef,
		popupRef,
		handleScrollArrowVisibility,
		alignItemWithTriggerActive,
		setControlledAlignItemWithTrigger,
		scrollArrowFrame,
		listElement,
		listRef,
		highlightItemOnHover,
		direction,
		isPositioned
	]);
	React$3.useEffect(() => {
		if (!alignItemWithTriggerActive || !positionerElement || !open) return;
		const win = getWindow(positionerElement);
		function handleResize(event) {
			setOpen(false, createChangeEventDetails(windowResize, event));
		}
		return addEventListener(win, "resize", handleResize);
	}, [
		setOpen,
		alignItemWithTriggerActive,
		positionerElement,
		open
	]);
	const defaultProps = {
		...listElement ? {
			role: "presentation",
			"aria-orientation": void 0
		} : {
			role: "listbox",
			"aria-multiselectable": multiple || void 0,
			id: `${id}-list`
		},
		onKeyDown(event) {
			if (insideToolbar && COMPOSITE_KEYS.has(event.key)) event.stopPropagation();
		},
		onScroll(event) {
			if (listElement) return;
			handleScroll(event.currentTarget);
		},
		...alignItemWithTriggerActive && { style: listElement ? { height: "100%" } : LIST_FUNCTIONAL_STYLES },
		className: !listElement && alignItemWithTriggerActive ? styleDisableScrollbar.className : void 0
	};
	const element = useRenderElement("div", componentProps, {
		ref: [forwardedRef, popupRef],
		state,
		stateAttributesMapping,
		props: [
			popupProps,
			defaultProps,
			getDisabledMountTransitionStyles(transitionStatus),
			elementProps
		]
	});
	return /* @__PURE__ */ jsxs(React$3.Fragment, { children: [!disableStyleElements && styleDisableScrollbar.getElement(nonce), /* @__PURE__ */ jsx(FloatingFocusManager, {
		context: floatingRootContext,
		modal: false,
		disabled: !mounted,
		openInteractionType: openMethod,
		returnFocus: finalFocus,
		restoreFocus: true,
		children: element
	})] });
});
function getMaxPopupHeight(popupStyles) {
	const maxHeightStyle = popupStyles.maxHeight;
	return maxHeightStyle.endsWith("px") ? parseFloat(maxHeightStyle) || Infinity : Infinity;
}
function getMaxScrollTop(scroller) {
	return getMaxScrollOffset(scroller.scrollHeight, scroller.clientHeight);
}
function getScale(element) {
	return platform.getScale(element);
}
function normalizeSize(size, axis, scale) {
	return size / scale[axis];
}
function normalizeRect(rect, scale) {
	return rectToClientRect({
		x: normalizeSize(rect.x, "x", scale),
		y: normalizeSize(rect.y, "y", scale),
		width: normalizeSize(rect.width, "x", scale),
		height: normalizeSize(rect.height, "y", scale)
	});
}
var TRANSFORM_STYLE_RESETS = [
	["transform", "none"],
	["scale", "1"],
	["translate", "0 0"]
];
function unsetTransformStyles(popupElement) {
	const { style } = popupElement;
	const originalStyles = {};
	for (const [property, value] of TRANSFORM_STYLE_RESETS) {
		originalStyles[property] = style.getPropertyValue(property);
		style.setProperty(property, value, "important");
	}
	return () => {
		for (const [property] of TRANSFORM_STYLE_RESETS) {
			const originalValue = originalStyles[property];
			if (originalValue) style.setProperty(property, originalValue);
			else style.removeProperty(property);
		}
	};
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/select/list/SelectList.mjs
/**
* A container for the select items.
* Renders a `<div>` element.
*
* Documentation: [Base UI Select](https://base-ui.com/react/components/select)
*/
var SelectList = /* @__PURE__ */ React$3.forwardRef(function SelectList(componentProps, forwardedRef) {
	const { render, className, style, ...elementProps } = componentProps;
	const { store, scrollHandlerRef, multiple } = useSelectRootContext();
	const { alignItemWithTriggerActive } = useSelectPositionerContext();
	const hasScrollArrows = useStore(store, selectors.hasScrollArrows);
	const openMethod = useStore(store, selectors.openMethod);
	const defaultProps = {
		id: `${useStore(store, selectors.id)}-list`,
		role: "listbox",
		"aria-multiselectable": multiple || void 0,
		onScroll(event) {
			scrollHandlerRef.current?.(event.currentTarget);
		},
		...alignItemWithTriggerActive && { style: LIST_FUNCTIONAL_STYLES },
		className: hasScrollArrows && openMethod !== "touch" ? styleDisableScrollbar.className : void 0
	};
	return useRenderElement("div", componentProps, {
		ref: [forwardedRef, store.useStateSetter("listElement")],
		props: [defaultProps, elementProps]
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/select/item/SelectItemContext.mjs
var SelectItemContext = /* @__PURE__ */ React$3.createContext(void 0);
function useSelectItemContext() {
	const context = React$3.useContext(SelectItemContext);
	if (!context) throw new Error(formatErrorMessage(57));
	return context;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/select/item/SelectItem.mjs
/**
* An individual option in the select popup.
* Renders a `<div>` element.
*
* Documentation: [Base UI Select](https://base-ui.com/react/components/select)
*/
var SelectItem$1 = /* @__PURE__ */ React$3.memo(/* @__PURE__ */ React$3.forwardRef(function SelectItem(componentProps, forwardedRef) {
	const { render, className, style, value: itemValue = null, label, disabled: disabledProp = false, nativeButton = false, ...elementProps } = componentProps;
	const textRef = React$3.useRef(null);
	const listItem = useCompositeListItem({
		guess: true,
		label,
		textRef
	});
	const { store, itemProps, setOpen, setValue, selectionRef, typingRef, valuesRef, multiple, selectedItemTextRef, disabled: selectDisabled, readOnly } = useSelectRootContext();
	const disabled = selectDisabled || disabledProp;
	const highlighted = useStore(store, selectors.isActive, listItem.index);
	const open = useStore(store, selectors.open);
	const selected = useStore(store, selectors.isSelected, itemValue);
	const selectedByFocus = useStore(store, selectors.isSelectedByFocus, listItem.index);
	const isItemEqualToValue = useStore(store, selectors.isItemEqualToValue);
	const index = listItem.index;
	const itemRef = React$3.useRef(null);
	useIsoLayoutEffect(() => {
		const values = valuesRef.current;
		values[index] = itemValue;
		return () => {
			delete values[index];
		};
	}, [
		index,
		itemValue,
		valuesRef
	]);
	useIsoLayoutEffect(() => {
		const selectedValue = store.state.value;
		let selectedCandidate = selectedValue;
		if (multiple && Array.isArray(selectedValue)) selectedCandidate = selectedValue.length > 0 ? selectedValue[selectedValue.length - 1] : void 0;
		if (selectedCandidate !== void 0 && compareItemEquality(itemValue, selectedCandidate, isItemEqualToValue)) {
			store.set("selectedIndex", index);
			if (textRef.current) selectedItemTextRef.current = textRef.current;
		}
	}, [
		index,
		multiple,
		isItemEqualToValue,
		store,
		itemValue,
		selectedItemTextRef
	]);
	const pointerTypeRef = React$3.useRef("mouse");
	const allowMouseSelectionRef = React$3.useRef(false);
	const { getButtonProps, buttonRef } = useButton({
		disabled,
		focusableWhenDisabled: true,
		native: nativeButton,
		composite: true
	});
	const state = {
		disabled,
		selected,
		highlighted
	};
	function commitSelection(event) {
		if (selectDisabled || readOnly) return;
		const selectedValue = store.state.value;
		if (multiple) {
			const currentValue = Array.isArray(selectedValue) ? selectedValue : [];
			setValue(selected ? removeItem(currentValue, itemValue, isItemEqualToValue) : [...currentValue, itemValue], createChangeEventDetails(itemPress, event));
		} else {
			setValue(itemValue, createChangeEventDetails(itemPress, event));
			setOpen(false, createChangeEventDetails(itemPress, event));
		}
	}
	function resetDragMovement() {
		selectionRef.current.dragY = 0;
	}
	const defaultProps = {
		role: "option",
		"aria-selected": selected,
		tabIndex: open && highlighted ? 0 : -1,
		onKeyDown(event) {
			store.set("activeIndex", index);
			if (event.key === " " && typingRef.current) event.preventDefault();
		},
		onClick(event) {
			const isMouseClick = pointerTypeRef.current !== "touch";
			const clickPointerType = event.nativeEvent.pointerType;
			const isVirtualMouseClick = isMouseClick && isVirtualClick(event.nativeEvent) && (clickPointerType !== void 0 || highlighted);
			const isInvalidMouseClick = isMouseClick && !isVirtualMouseClick && !allowMouseSelectionRef.current;
			allowMouseSelectionRef.current = false;
			if (disabled || isInvalidMouseClick) return;
			commitSelection(event.nativeEvent);
		},
		onPointerEnter(event) {
			pointerTypeRef.current = event.pointerType;
		},
		onPointerMove(event) {
			if (event.pointerType === "mouse" && event.buttons === 1) {
				const selection = selectionRef.current;
				selection.dragY += event.movementY;
				if (selection.dragY ** 2 >= 64) selection.allowUnselectedMouseUp = true;
			}
		},
		onPointerDown(event) {
			pointerTypeRef.current = event.pointerType;
			allowMouseSelectionRef.current = true;
			resetDragMovement();
		},
		onMouseUp() {
			resetDragMovement();
			if (disabled || pointerTypeRef.current === "touch") return;
			if (allowMouseSelectionRef.current) return;
			const disallowSelectedMouseUp = !selectionRef.current.allowSelectedMouseUp && selected;
			const disallowUnselectedMouseUp = !selectionRef.current.allowUnselectedMouseUp && !selected;
			if (disallowSelectedMouseUp || disallowUnselectedMouseUp) return;
			allowMouseSelectionRef.current = true;
			itemRef.current?.click();
			allowMouseSelectionRef.current = false;
		}
	};
	const element = useRenderElement("div", componentProps, {
		ref: [
			buttonRef,
			forwardedRef,
			listItem.ref,
			itemRef
		],
		state,
		props: [
			itemProps,
			defaultProps,
			elementProps,
			getButtonProps
		]
	});
	const contextValue = React$3.useMemo(() => ({
		selected,
		index,
		textRef,
		selectedByFocus
	}), [
		selected,
		index,
		textRef,
		selectedByFocus
	]);
	return /* @__PURE__ */ jsx(SelectItemContext.Provider, {
		value: contextValue,
		children: element
	});
}));
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/select/item-indicator/SelectItemIndicator.mjs
/**
* Indicates whether the select item is selected.
* Renders a `<span>` element.
*
* Documentation: [Base UI Select](https://base-ui.com/react/components/select)
*/
var SelectItemIndicator = /* @__PURE__ */ React$3.forwardRef(function SelectItemIndicator(componentProps, forwardedRef) {
	const { selected } = useSelectItemContext();
	if (!(componentProps.keepMounted || selected)) return null;
	return /* @__PURE__ */ jsx(Inner, {
		...componentProps,
		ref: forwardedRef
	});
});
var Inner = /* @__PURE__ */ React$3.memo(/* @__PURE__ */ React$3.forwardRef((componentProps, forwardedRef) => {
	const { render, className, style, keepMounted, ...elementProps } = componentProps;
	const { selected } = useSelectItemContext();
	const indicatorRef = React$3.useRef(null);
	const { transitionStatus, setMounted } = useTransitionStatus(selected);
	const element = useRenderElement("span", componentProps, {
		ref: [forwardedRef, indicatorRef],
		state: {
			selected,
			transitionStatus
		},
		props: [{
			"aria-hidden": true,
			children: "✔️"
		}, elementProps],
		stateAttributesMapping: transitionStatusMapping
	});
	useOpenChangeComplete({
		open: selected,
		ref: indicatorRef,
		onComplete() {
			if (!selected) setMounted(false);
		}
	});
	return element;
}));
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/select/item-text/SelectItemText.mjs
/**
* A text label of the select item.
* Renders a `<div>` element.
*
* Documentation: [Base UI Select](https://base-ui.com/react/components/select)
*/
var SelectItemText = /* @__PURE__ */ React$3.memo(/* @__PURE__ */ React$3.forwardRef(function SelectItemText(componentProps, forwardedRef) {
	const { index, textRef, selectedByFocus } = useSelectItemContext();
	const { firstItemTextRef, selectedItemTextRef } = useSelectRootContext();
	const { render, className, style, ...elementProps } = componentProps;
	return useRenderElement("div", componentProps, {
		ref: [
			React$3.useCallback((node) => {
				if (!node) return;
				if (index === 0) firstItemTextRef.current = node;
				if (selectedByFocus) selectedItemTextRef.current = node;
			}, [
				firstItemTextRef,
				selectedItemTextRef,
				index,
				selectedByFocus
			]),
			forwardedRef,
			textRef
		],
		props: elementProps
	});
}));
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/select/scroll-arrow/SelectScrollArrow.mjs
/**
* @internal
*/
var SelectScrollArrow = /* @__PURE__ */ React$3.forwardRef(function SelectScrollArrow(componentProps, forwardedRef) {
	const { render, className, style, direction, keepMounted, ...elementProps } = componentProps;
	const isUp = direction === "up";
	const { store, popupRef, listRef, handleScrollArrowVisibility, scrollArrowsMountedCountRef } = useSelectRootContext();
	const { side, scrollDownArrowRef, scrollUpArrowRef } = useSelectPositionerContext();
	const stateVisible = useStore(store, isUp ? selectors.scrollUpArrowVisible : selectors.scrollDownArrowVisible);
	const openMethod = useStore(store, selectors.openMethod);
	const visible = stateVisible && openMethod !== "touch";
	const timeout = useTimeout();
	const scrollArrowRef = isUp ? scrollUpArrowRef : scrollDownArrowRef;
	const { mounted, transitionStatus, setMounted } = useTransitionStatus(visible);
	useIsoLayoutEffect(() => {
		scrollArrowsMountedCountRef.current += 1;
		store.set("hasScrollArrows", true);
		return () => {
			scrollArrowsMountedCountRef.current = Math.max(0, scrollArrowsMountedCountRef.current - 1);
			if (scrollArrowsMountedCountRef.current === 0) store.set("hasScrollArrows", false);
		};
	}, [store, scrollArrowsMountedCountRef]);
	useOpenChangeComplete({
		open: visible,
		ref: scrollArrowRef,
		onComplete() {
			if (!visible) setMounted(false);
		}
	});
	const element = useRenderElement("div", componentProps, {
		ref: [forwardedRef, scrollArrowRef],
		state: {
			direction,
			visible,
			side,
			transitionStatus
		},
		props: [{
			"aria-hidden": true,
			children: isUp ? "▲" : "▼",
			style: { position: "absolute" },
			onMouseMove(event) {
				if (event.movementX === 0 && event.movementY === 0 || timeout.isStarted()) return;
				store.set("activeIndex", null);
				function scrollNextItem() {
					const scroller = store.state.listElement ?? popupRef.current;
					if (!scroller) return;
					store.set("activeIndex", null);
					handleScrollArrowVisibility(scroller);
					const maxScrollTop = getMaxScrollOffset(scroller.scrollHeight, scroller.clientHeight);
					const scrollTop = normalizeScrollOffset(scroller.scrollTop, maxScrollTop);
					const isScrolledToEdge = scrollTop === (isUp ? 0 : maxScrollTop);
					const items = listRef.current;
					if (scrollTop !== scroller.scrollTop) scroller.scrollTop = scrollTop;
					if (isScrolledToEdge) {
						timeout.clear();
						return;
					}
					if (items.length > 0) {
						const scrollArrowHeight = scrollArrowRef.current?.offsetHeight || 0;
						scroller.scrollTop = getTargetScrollTop(items, isUp, scrollTop, scroller.clientHeight, scrollArrowHeight, maxScrollTop);
					}
					timeout.start(40, scrollNextItem);
				}
				timeout.start(40, scrollNextItem);
			},
			onMouseLeave() {
				timeout.clear();
			}
		}, elementProps],
		stateAttributesMapping: transitionStatusMapping
	});
	if (!(mounted || keepMounted)) return null;
	return element;
});
function getTargetScrollTop(items, isUp, scrollTop, clientHeight, scrollArrowHeight, maxScrollTop) {
	if (isUp) {
		let firstVisibleIndex = 0;
		const visibleTop = scrollTop + scrollArrowHeight - 1;
		for (let i = 0; i < items.length; i += 1) {
			const item = items[i];
			if (item && item.offsetTop >= visibleTop) {
				firstVisibleIndex = i;
				break;
			}
		}
		const targetIndex = Math.max(0, firstVisibleIndex - 1);
		const targetItem = items[targetIndex];
		return targetIndex < firstVisibleIndex && targetItem ? normalizeScrollOffset(targetItem.offsetTop - scrollArrowHeight, maxScrollTop) : 0;
	}
	let lastVisibleIndex = items.length - 1;
	const visibleBottom = scrollTop + clientHeight - scrollArrowHeight + 1;
	for (let i = 0; i < items.length; i += 1) {
		const item = items[i];
		if (item && item.offsetTop + item.offsetHeight > visibleBottom) {
			lastVisibleIndex = Math.max(0, i - 1);
			break;
		}
	}
	const targetIndex = Math.min(items.length - 1, lastVisibleIndex + 1);
	const targetItem = items[targetIndex];
	return targetIndex > lastVisibleIndex && targetItem ? normalizeScrollOffset(targetItem.offsetTop + targetItem.offsetHeight - clientHeight + scrollArrowHeight, maxScrollTop) : maxScrollTop;
}
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/select/scroll-down-arrow/SelectScrollDownArrow.mjs
/**
* An element that scrolls the select popup down when hovered. Does not render when using touch input.
* Renders a `<div>` element.
*
* Documentation: [Base UI Select](https://base-ui.com/react/components/select)
*/
var SelectScrollDownArrow = /* @__PURE__ */ React$3.forwardRef(function SelectScrollDownArrow(props, forwardedRef) {
	return /* @__PURE__ */ jsx(SelectScrollArrow, {
		...props,
		ref: forwardedRef,
		direction: "down"
	});
});
//#endregion
//#region ../../../node_modules/.pnpm/@base-ui+react@1.7.0_@date-_628258a3ea3cacf06f3d8216c02e09ef/node_modules/@base-ui/react/select/scroll-up-arrow/SelectScrollUpArrow.mjs
/**
* An element that scrolls the select popup up when hovered. Does not render when using touch input.
* Renders a `<div>` element.
*
* Documentation: [Base UI Select](https://base-ui.com/react/components/select)
*/
var SelectScrollUpArrow = /* @__PURE__ */ React$3.forwardRef(function SelectScrollUpArrow(props, forwardedRef) {
	return /* @__PURE__ */ jsx(SelectScrollArrow, {
		...props,
		ref: forwardedRef,
		direction: "up"
	});
});
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var ChevronDown = createLucideIcon("chevron-down", [["path", {
	d: "m6 9 6 6 6-6",
	key: "qrunsl"
}]]);
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var ChevronUp = createLucideIcon("chevron-up", [["path", {
	d: "m18 15-6-6-6 6",
	key: "153udz"
}]]);
//#endregion
//#region components/ui/select.tsx
var Select = SelectRoot;
function SelectValue({ className, ...props }) {
	return /* @__PURE__ */ jsx(SelectValue$1, {
		"data-slot": "select-value",
		className: cn("flex flex-1 text-left", className),
		...props
	});
}
function SelectTrigger({ className, size = "default", children, ...props }) {
	return /* @__PURE__ */ jsxs(SelectTrigger$1, {
		"data-slot": "select-trigger",
		"data-size": size,
		className: cn("flex w-fit items-center justify-between gap-1.5 rounded-lg border border-input bg-transparent py-2 pr-2 pl-2.5 text-sm whitespace-nowrap transition-colors outline-none select-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 data-placeholder:text-muted-foreground data-[size=default]:h-8 data-[size=sm]:h-7 data-[size=sm]:rounded-[min(var(--radius-md),10px)] *:data-[slot=select-value]:line-clamp-1 *:data-[slot=select-value]:flex *:data-[slot=select-value]:items-center *:data-[slot=select-value]:gap-1.5 dark:bg-input/30 dark:hover:bg-input/50 dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4", className),
		...props,
		children: [children, /* @__PURE__ */ jsx(SelectIcon, { render: /* @__PURE__ */ jsx(ChevronDown, { className: "pointer-events-none size-4 text-muted-foreground" }) })]
	});
}
function SelectContent({ className, children, side = "bottom", sideOffset = 4, align = "center", alignOffset = 0, alignItemWithTrigger = true, ...props }) {
	return /* @__PURE__ */ jsx(SelectPortal, { children: /* @__PURE__ */ jsx(SelectPositioner, {
		side,
		sideOffset,
		align,
		alignOffset,
		alignItemWithTrigger,
		className: "isolate z-50",
		children: /* @__PURE__ */ jsxs(SelectPopup, {
			"data-slot": "select-content",
			"data-align-trigger": alignItemWithTrigger,
			className: cn("relative isolate z-50 max-h-(--available-height) w-(--anchor-width) min-w-36 origin-(--transform-origin) overflow-x-hidden overflow-y-auto rounded-lg bg-popover text-popover-foreground shadow-md ring-1 ring-foreground/10 duration-100 data-[align-trigger=true]:animate-none data-[side=bottom]:slide-in-from-top-2 data-[side=inline-end]:slide-in-from-left-2 data-[side=inline-start]:slide-in-from-right-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 data-open:animate-in data-open:fade-in-0 data-open:zoom-in-95 data-closed:animate-out data-closed:fade-out-0 data-closed:zoom-out-95", className),
			...props,
			children: [
				/* @__PURE__ */ jsx(SelectScrollUpButton, {}),
				/* @__PURE__ */ jsx(SelectList, { children }),
				/* @__PURE__ */ jsx(SelectScrollDownButton, {})
			]
		})
	}) });
}
function SelectItem({ className, children, ...props }) {
	return /* @__PURE__ */ jsxs(SelectItem$1, {
		"data-slot": "select-item",
		className: cn("relative flex w-full cursor-default items-center gap-1.5 rounded-md py-1 pr-8 pl-1.5 text-sm outline-hidden select-none focus:bg-accent focus:text-accent-foreground not-data-[variant=destructive]:focus:**:text-accent-foreground data-disabled:pointer-events-none data-disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4 *:[span]:last:flex *:[span]:last:items-center *:[span]:last:gap-2", className),
		...props,
		children: [/* @__PURE__ */ jsx(SelectItemText, {
			className: "flex flex-1 shrink-0 gap-2 whitespace-nowrap",
			children
		}), /* @__PURE__ */ jsx(SelectItemIndicator, {
			render: /* @__PURE__ */ jsx("span", { className: "pointer-events-none absolute right-2 flex size-4 items-center justify-center" }),
			children: /* @__PURE__ */ jsx(Check, { className: "pointer-events-none" })
		})]
	});
}
function SelectScrollUpButton({ className, ...props }) {
	return /* @__PURE__ */ jsx(SelectScrollUpArrow, {
		"data-slot": "select-scroll-up-button",
		className: cn("top-0 z-10 flex w-full cursor-default items-center justify-center bg-popover py-1 [&_svg:not([class*='size-'])]:size-4", className),
		...props,
		children: /* @__PURE__ */ jsx(ChevronUp, {})
	});
}
function SelectScrollDownButton({ className, ...props }) {
	return /* @__PURE__ */ jsx(SelectScrollDownArrow, {
		"data-slot": "select-scroll-down-button",
		className: cn("bottom-0 z-10 flex w-full cursor-default items-center justify-center bg-popover py-1 [&_svg:not([class*='size-'])]:size-4", className),
		...props,
		children: /* @__PURE__ */ jsx(ChevronDown, {})
	});
}
//#endregion
//#region lib/strategy-catalog.json
var strategy_catalog_default = [
	{
		"id": "a-share-15d-selection",
		"dataStatus": "partial",
		"missingData": ["9月9日仍有少量个股日线缺口（每日补全记录）"],
		"dataNote": "市场主体数据可用，但部分个股日线尚有缺口，报告会保留缺口提示。",
		"businessEntry": "scripts/run_a_share_15d.py",
		"businessHash": "E0570CD26EE7D7B332656E47AFCE84F76685C2A4078690B42E996C0C0F59A57B",
		"codexEntryHash": "50F983020454E3E1B4548F5118F591D84D5FCCB5FFD2C79C5B8B4D487B04392F",
		"legacyEntryHash": "D13CDB22D000880FA3B419DCEEDA5E67DDB5C4B27E9FA84CD034A1F7085EFC7A",
		"codexWrapperShared": true
	},
	{
		"id": "a-share-bottom-fishing",
		"dataStatus": "available",
		"missingData": [],
		"dataNote": "日线行情、数据新鲜度与对应技能依赖已发现，可提交 Harness 运行。",
		"businessEntry": "scripts/抄底策略.py",
		"businessHash": "C40E24C8486BEDC7E8F923ABD151BD3C48B88AAE097E960D4F5A0C9898DB15B7",
		"codexEntryHash": "50F983020454E3E1B4548F5118F591D84D5FCCB5FFD2C79C5B8B4D487B04392F",
		"legacyEntryHash": "D3A18CADCFFE6F76C34E7C6EF0D6826CEDF095EE0C651D107E633360A4AD854C",
		"codexWrapperShared": true
	},
	{
		"id": "convertible-bond-screening-strategy",
		"dataStatus": "missing",
		"minuteData": {
			"mode": "optional_degraded",
			"purpose": "部分可转债分钟特征按任务读取外部 LC5；原始 .lc5 不进入 EXE。"
		},
		"missingData": ["可转债日线行情", "可转债基础资料/转股价与赎回公告快照"],
		"dataNote": "当前项目仅有可转债算法与校验代码，没有可转债行情快照，运行会被数据闸门拦截。",
		"businessEntry": "scripts/run_convertible_bond_screening.py",
		"businessHash": "776BFDC8CE924E7C68F53B03BF0DDA97061C24089C6B196BF2AF9311F3710B6E",
		"codexEntryHash": "9AFD0B37C6FCBDAC576F078A43A838AC1AF0885B3B4DE45BF00252043DAF0667",
		"legacyEntryHash": "E39F16CBB98A3FE4FEF1180B5B7BFFF1194D95FEA4CCE678048E7110D8E008CD",
		"codexWrapperShared": false
	},
	{
		"id": "buzhang-leader-mining",
		"dataStatus": "available",
		"missingData": [],
		"dataNote": "日线行情、数据新鲜度与对应技能依赖已发现，可提交 Harness 运行。",
		"businessEntry": "scripts/business_entry.py",
		"businessHash": "F6B2CC71715A94C678888A624D5F649C1A6CCB707747A12334EBCF74E19A4D49",
		"codexEntryHash": "50F983020454E3E1B4548F5118F591D84D5FCCB5FFD2C79C5B8B4D487B04392F",
		"legacyEntryHash": "DB9CB64647EE43A12267481D697C4ED83A9E51ACD6FEC04C125AE358D150BA83",
		"codexWrapperShared": true
	},
	{
		"id": "chanlun-first-board",
		"dataStatus": "available",
		"missingData": [],
		"dataNote": "日线行情、数据新鲜度与对应技能依赖已发现，可提交 Harness 运行。",
		"businessEntry": "scripts/run_chanlun_first_board.py",
		"businessHash": "3CA556DF216798CF22FBB017F4F9F0E15C9E98A1119123BBB2142934C08B0E2C",
		"codexEntryHash": "50F983020454E3E1B4548F5118F591D84D5FCCB5FFD2C79C5B8B4D487B04392F",
		"legacyEntryHash": "FBC17FB0F4781141CBB6A07B8F45BD639BCC97E766ED13416E55319154483022",
		"codexWrapperShared": true
	},
	{
		"id": "dragon-pullback",
		"dataStatus": "available",
		"missingData": [],
		"dataNote": "日线行情、数据新鲜度与对应技能依赖已发现，可提交 Harness 运行。",
		"businessEntry": "scripts/run_strong_leader_first_yin.py",
		"businessHash": "4D183266F034C71F4F0468366B421C113A6AB7D3ED4D6A1A3D960D3C7ABEF99D",
		"codexEntryHash": "50F983020454E3E1B4548F5118F591D84D5FCCB5FFD2C79C5B8B4D487B04392F",
		"legacyEntryHash": "73AD09AFB908BBD23A91B857CE154246E3E1845856102848447CD38B9535A9E6",
		"codexWrapperShared": true
	},
	{
		"id": "feilong-strategy",
		"dataStatus": "available",
		"minuteData": {
			"mode": "optional_degraded",
			"purpose": "飞龙高级因子需要外部 LC5；缺少时只允许输出日线/公式部分，并标记 DEGRADED。"
		},
		"missingData": [],
		"dataNote": "日线行情、数据新鲜度与对应技能依赖已发现，可提交 Harness 运行。",
		"businessEntry": "scripts/feilong_realtime_report.py",
		"businessHash": "38CA8577E14ADA53465E981B43021DEF8E0D18A671B4EA877744DA96AE51ED68",
		"codexEntryHash": "50F983020454E3E1B4548F5118F591D84D5FCCB5FFD2C79C5B8B4D487B04392F",
		"legacyEntryHash": "B0EC045ED656E23B0D54020F8D8CF96C88284934AB1B295F61D17684194F0727",
		"codexWrapperShared": true
	},
	{
		"id": "five-dimension-resonance",
		"dataStatus": "available",
		"missingData": [],
		"dataNote": "日线行情、数据新鲜度与对应技能依赖已发现，可提交 Harness 运行。",
		"businessEntry": "scripts/run_feilong_block_resonance.py",
		"businessHash": "91CA9390015483F498A3905E6F1E091F1B25D3E137CB975ED9534B2202FCE6F5",
		"codexEntryHash": "50F983020454E3E1B4548F5118F591D84D5FCCB5FFD2C79C5B8B4D487B04392F",
		"legacyEntryHash": "D9AF1CCB32158D43171A4A36272DEADDB7D16D165B92AD8F825811614C777D0A",
		"codexWrapperShared": true
	},
	{
		"id": "four-strategy-system",
		"dataStatus": "available",
		"missingData": [],
		"dataNote": "日线行情、数据新鲜度与对应技能依赖已发现，可提交 Harness 运行。",
		"businessEntry": "scripts/run_four_strategy_smoke.py",
		"businessHash": "A624684C81B80C9D0B5B7545ED5569009ABDFD9BA4D57C72F48564EBB250ABA4",
		"codexEntryHash": "50F983020454E3E1B4548F5118F591D84D5FCCB5FFD2C79C5B8B4D487B04392F",
		"legacyEntryHash": "1E1B699BBB27D040360C130FEADF21827699302228C6F18C4B0735F07853775B",
		"codexWrapperShared": true
	},
	{
		"id": "golden-ignition",
		"dataStatus": "available",
		"missingData": [],
		"dataNote": "日线行情、数据新鲜度与对应技能依赖已发现，可提交 Harness 运行。",
		"businessEntry": "scripts/entry_golden_ignition.py",
		"businessHash": "25126102BDED0E19ABD222E701F996957B6782EF358A778772A1332070694E58",
		"codexEntryHash": "50F983020454E3E1B4548F5118F591D84D5FCCB5FFD2C79C5B8B4D487B04392F",
		"legacyEntryHash": "BB94FB7C58DECD4FB8CF0E4530663DFBB7FD0D5499DDC6790259C337A5E67B97",
		"codexWrapperShared": true
	},
	{
		"id": "nana-teacher-five-strategies",
		"dataStatus": "available",
		"minuteData": {
			"mode": "optional_degraded",
			"purpose": "5 分钟复核属于可选辅助证据，不阻塞普通日线任务。"
		},
		"missingData": [],
		"dataNote": "日线行情、数据新鲜度与对应技能依赖已发现，可提交 Harness 运行。",
		"businessEntry": "scripts/business_entry.py",
		"businessHash": "14F1FE49958150A78569A1D273BA59A155819B6B1A4B7D47C2260886597797D6",
		"codexEntryHash": "50F983020454E3E1B4548F5118F591D84D5FCCB5FFD2C79C5B8B4D487B04392F",
		"legacyEntryHash": "CFCDF8758F94E6AD09D37EE46C91099D8762F04279AD173C26118CC2DEE16DAE",
		"codexWrapperShared": true
	},
	{
		"id": "oversold-first-board",
		"dataStatus": "available",
		"missingData": [],
		"dataNote": "日线行情、数据新鲜度与对应技能依赖已发现，可提交 Harness 运行。",
		"businessEntry": "scripts/run_oversold_first_board_smoke.py",
		"businessHash": "EC20DF56E18D8AD4BE7F567025637FFE21827284D3D371212CAB76A3A6E11FC3",
		"codexEntryHash": "50F983020454E3E1B4548F5118F591D84D5FCCB5FFD2C79C5B8B4D487B04392F",
		"legacyEntryHash": "5C2B4E81AC25A3F6671E806F59DFE5F2CBDC0C827136D4C9E8BC12E4EEA98383",
		"codexWrapperShared": true
	},
	{
		"id": "quality-track-stock-selection",
		"dataStatus": "available",
		"missingData": [],
		"dataNote": "日线行情、数据新鲜度与对应技能依赖已发现，可提交 Harness 运行。",
		"businessEntry": "scripts/legacy_codex_entry.py",
		"businessHash": "FBB51D2587A7F12754636065C495BB868EFBC371B4856A8F9220E4E2E89E581B",
		"codexEntryHash": "50F983020454E3E1B4548F5118F591D84D5FCCB5FFD2C79C5B8B4D487B04392F",
		"legacyEntryHash": "FBB51D2587A7F12754636065C495BB868EFBC371B4856A8F9220E4E2E89E581B",
		"codexWrapperShared": true
	},
	{
		"id": "quant-strategy-bundle-chen",
		"dataStatus": "available",
		"missingData": [],
		"dataNote": "日线行情、数据新鲜度与对应技能依赖已发现，可提交 Harness 运行。",
		"businessEntry": "scripts/run_quant_bundle.py",
		"businessHash": "C14C4C2FE8347C5EF6C2CF9C6CCEA1E8ED8AD1A748530F20122234F8BF34B036",
		"codexEntryHash": "50F983020454E3E1B4548F5118F591D84D5FCCB5FFD2C79C5B8B4D487B04392F",
		"legacyEntryHash": "2FF9E3C7522D9F91D3E3AAB298FB53293AAF27922EEDB5353A94784B06F30093",
		"codexWrapperShared": true
	},
	{
		"id": "quantitative-trading",
		"dataStatus": "available",
		"missingData": [],
		"dataNote": "日线行情、数据新鲜度与对应技能依赖已发现，可提交 Harness 运行。",
		"businessEntry": "scripts/run_quantitative_trading_smoke.py",
		"businessHash": "D0DBFC832A7FA3B194BD26C078B1FE09683EC1EB61A0C88C7C89A92DAE0952F3",
		"codexEntryHash": "50F983020454E3E1B4548F5118F591D84D5FCCB5FFD2C79C5B8B4D487B04392F",
		"legacyEntryHash": "329D5442529FC6B67C9A42CF96F749DD216D073B21BC502EE247965B8DB66194",
		"codexWrapperShared": true
	},
	{
		"id": "old-leader-oversold-rebound",
		"dataStatus": "available",
		"missingData": [],
		"dataNote": "日线行情、数据新鲜度与对应技能依赖已发现，可提交 Harness 运行。",
		"businessEntry": "scripts/legacy_codex_entry.py",
		"businessHash": "A6985FD4DF80784C032845CCFEFEF369E9B07DCA19B21E4367FB5F81351FA377",
		"codexEntryHash": "50F983020454E3E1B4548F5118F591D84D5FCCB5FFD2C79C5B8B4D487B04392F",
		"legacyEntryHash": "A6985FD4DF80784C032845CCFEFEF369E9B07DCA19B21E4367FB5F81351FA377",
		"codexWrapperShared": true
	}
];
//#endregion
//#region app/market-display.ts
/**
* 日期与价格展示的单一入口。
*
* 行情日期来自本地可核验的日线归档，不使用系统当前日期补齐。这样当
* 通达信最后一条日线仍是上一个交易日时，界面会明确告诉用户价格是哪一
* 天的收盘价，而不会把它误称为“最新价”。
*/
function normalizeTradingDate(value) {
	const raw = String(value ?? "").trim();
	if (!raw) return "";
	const match = raw.match(/(\d{4})\D?(\d{2})\D?(\d{2})/);
	if (match) return `${match[1]}-${match[2]}-${match[3]}`;
	const digits = raw.replace(/\D/g, "");
	if (digits.length >= 8) return `${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6, 8)}`;
	return raw;
}
function dateLabel$1(value) {
	return normalizeTradingDate(value) || "—";
}
function closeDateLabel(value) {
	const match = normalizeTradingDate(value).match(/^(\d{4})-(\d{2})-(\d{2})$/);
	if (!match) return "最近可核验交易日收盘价格";
	return `${Number(match[2])}月${Number(match[3])}日收盘价格`;
}
//#endregion
//#region app/workspace-pages.tsx
function formulaText(value) {
	if (Array.isArray(value)) return value.map((item) => formulaText(item)).filter(Boolean).at(-1) || "";
	if (value == null) return "";
	return String(value).trim();
}
function strategyScoreCandidate(stock, raw, strategyId, scoreReceipt) {
	const row = raw || {};
	const numberValue = (...keys) => {
		for (const key of keys) {
			const value = Number(row[key]);
			if (Number.isFinite(value)) return value;
		}
		return null;
	};
	const textValue = (...keys) => {
		for (const key of keys) {
			const value = formulaText(row[key]);
			if (value) return value;
		}
		return "";
	};
	const scoreComponents = row.score_components && typeof row.score_components === "object" ? row.score_components : {};
	const modelScores = row.model_scores && typeof row.model_scores === "object" ? row.model_scores : {};
	const modelStates = row.model_states && typeof row.model_states === "object" ? row.model_states : {};
	const modelDiagnostics = Object.entries(modelStates).map(([name, value]) => ({
		name,
		state: value && typeof value === "object" ? value : {}
	}));
	const actualScore = numberValue("score", "final_score", "short_burst_score", "primary_score", "model_c_score", "model_a_score", "model_b_score");
	const missing = Array.isArray(row.missing) ? row.missing.map(String) : (scoreReceipt.missing || []).map(String);
	let wave = "";
	let primaryModel = "";
	let primaryModelCandidate = "";
	let youzi = "";
	let institution = "";
	let risk = "";
	if (strategyId === "golden-ignition-v8") {
		const a = numberValue("model_a_score");
		const b = numberValue("model_b_score");
		const c = numberValue("model_c_score");
		wave = `阶段 ${textValue("golden_stage") || "未命中"} · A ${a == null ? "—" : a.toFixed(1)} / B ${b == null ? "—" : b.toFixed(1)} / C ${c == null ? "—" : c.toFixed(1)}`;
		youzi = `模型B弱转强 ${b == null ? "—" : b.toFixed(1)}`;
		institution = `模型C黄金点火 ${c == null ? "—" : c.toFixed(1)}`;
		risk = textValue("golden_fail_reasons") || (row.final_pass ? "V8三模型均未通过" : "V8硬条件未通过");
	} else if (strategyId === "short-burst-score-v5") {
		wave = `${textValue("stage") || "阶段未知"} · ${textValue("position") || "地位未知"} · ${textValue("overheat") || "透支未知"}`;
		youzi = `资金质量 ${formulaText(scoreComponents["资金质量"]) || "—"}`;
		institution = `资金弹性 ${formulaText(scoreComponents["资金弹性"]) || "—"}`;
		risk = (Array.isArray(row.hard_reject_reasons) ? row.hard_reject_reasons.map(String).join("；") : "") || textValue("conclusion") || "无硬否决回执";
	} else {
		const labels = Array.isArray(row.model_labels) ? row.model_labels.map(String).join("、") : "";
		const diagnosticTriggered = modelDiagnostics.filter(({ state }) => state.status === "TRIGGERED").map(({ name }) => name).join("、");
		const triggered = labels || diagnosticTriggered;
		const hasUnknownEnvironment = modelDiagnostics.some(({ state }) => state.core === true && (state.environment === null || state.environment === void 0));
		const hasCore = modelDiagnostics.some(({ state }) => state.core === true);
		const rejectReasons = Array.isArray(row.reject_reasons) ? row.reject_reasons.map(String).filter(Boolean) : [];
		const unknownModels = modelDiagnostics.filter(({ state }) => state.core === true && (state.environment === null || state.environment === void 0)).map(({ name }) => name);
		const gateReason = hasUnknownEnvironment ? `行业环境未闭合${unknownModels.length ? `（${unknownModels.join("、")}）` : ""}` : hasCore ? "核心结构已计算，环境/评分门未通过" : rejectReasons.length ? `核心结构未触发（${rejectReasons.slice(0, 2).join("；")}）` : "核心结构未触发";
		const scoreText = Object.entries(modelScores).map(([key, value]) => `${key} ${formulaText(value) || "—"}`).join("；");
		primaryModel = textValue("primary_model");
		primaryModelCandidate = textValue("primary_model_candidate");
		wave = triggered ? `触发：${triggered}` : `未触发 · ${gateReason}`;
		youzi = scoreText ? `模型分量 ${scoreText}` : `四模型评分 ${actualScore == null ? "—" : actualScore.toFixed(1)}`;
		const stateText = modelDiagnostics.map(({ name, state }) => `${name}:${String(state.status || "UNKNOWN")}`).join("；");
		institution = `共振 ${formulaText(row.resonance_count) || "0"} · ${textValue("market_state") || "市场状态未知"}${stateText ? ` · ${stateText}` : ""}`;
		risk = rejectReasons.join("；") || "量化模型未授权生产";
	}
	const riskWithMissing = missing.length ? `${risk}；缺失：${missing.slice(0, 3).join("、")}` : risk;
	return {
		code: stock.code,
		name: stock.name,
		close: stock.close,
		pct: stock.pct,
		amount: stock.amount,
		market: stock.market,
		score: actualScore == null ? 0 : actualScore,
		wave,
		primary_model: primaryModel || void 0,
		primary_model_candidate: primaryModelCandidate || void 0,
		youzi,
		institution,
		risk: riskWithMissing,
		score_source: String(row.score_source || (typeof scoreReceipt.score_source === "string" ? scoreReceipt.score_source : "原始策略引擎本地适配")),
		formula_status: String(row.score_status || scoreReceipt.score_status || "UNKNOWN"),
		formula_evidence: row,
		strategy_score: actualScore,
		strategy_score_status: String(row.score_status || scoreReceipt.score_status || "UNKNOWN"),
		strategy_score_source: String(row.score_source || ""),
		strategy_missing: missing,
		strategy_fields: row
	};
}
function reconcileSelectionHarnessOutput(raw, candidates, date, scoreReceipt) {
	const parsed = normalizeHarnessOutput(raw);
	const value = parsed.value && typeof parsed.value === "object" ? { ...parsed.value } : {};
	const isQuant = scoreReceipt?.strategy_id === "quant-production-v65" || candidates.some((candidate) => candidate.strategy_fields?.model_states);
	const localRows = candidates.map((candidate, index) => [
		String(index + 1),
		candidate.code,
		candidate.name,
		String(candidate.score),
		candidate.wave,
		...isQuant ? [candidate.primary_model ? `已触发：${candidate.primary_model}` : candidate.primary_model_candidate ? `待闭合：${candidate.primary_model_candidate}` : "无主模型"] : [],
		candidate.youzi,
		candidate.institution,
		candidate.risk
	]);
	const tables = Array.isArray(value.tables) ? [...value.tables] : [];
	const topIndex = tables.findIndex((table) => String(table?.title || "").includes("Top") || String(table?.title || "").includes("候选"));
	const topTable = {
		...topIndex >= 0 ? tables[topIndex] : {},
		title: "Top 候选",
		columns: isQuant ? [
			"排名",
			"代码",
			"名称",
			"评分",
			"波段",
			"主模型",
			"游资",
			"机构",
			"风险"
		] : [
			"排名",
			"代码",
			"名称",
			"评分",
			"波段",
			"游资",
			"机构",
			"风险"
		],
		rows: localRows
	};
	if (topIndex >= 0) tables[topIndex] = topTable;
	else tables.unshift(topTable);
	const cautions = Array.isArray(value.cautions) ? value.cautions.map(String) : [];
	const localNote = "Top 候选的评分字段已由对应原始策略引擎在本地日线候选上计算；Harness 负责解释、缺失项和风险边界，不得用涨幅或成交额替代策略评分。";
	if (!cautions.includes(localNote)) cautions.unshift(localNote);
	const missing = Array.isArray(scoreReceipt?.missing) ? scoreReceipt.missing.map(String).filter(Boolean) : [];
	if (missing.length) {
		const missingNote = `本次策略评分缺失部分（已降级，不代表生产授权）：${missing.join("；")}`;
		if (!cautions.includes(missingNote)) cautions.unshift(missingNote);
	}
	return JSON.stringify({
		...value,
		status: String(value.status || parsed.status || "COMPLETED"),
		summary: String(value.summary || parsed.summary || "本地候选与 TDX 五公式分析已完成。"),
		data_date: String(value.data_date || parsed.dataDate || date),
		data_scope: String(value.data_scope || parsed.dataScope || `本地 TDX 日线 ${date} · Top${candidates.length} · 五公式回执`),
		cautions,
		tables
	});
}
function strategyRunHasReport(run) {
	return Boolean(run && !run.busy && run.phase === "completed" && (run.harnessOutput || run.structured));
}
function strategyRunHasFailure(run) {
	return Boolean(run && !run.busy && !strategyRunHasReport(run) && (run.phase === "strategy_error" || run.phase === "harness_error" || run.phase === "resume_error" || run.status === "ERROR" || run.status === "HARNESS_ERROR"));
}
var groupNames = {
	selection: "策略选股",
	mainline: "主线追踪",
	ladder: "涨停与连板",
	capital: "资金透视",
	research: "个股研究",
	watchlist: "我的工作台",
	reports: "复盘与报告",
	"my-reports": "我的报告",
	settings: "数据与底层能力"
};
var skill14AssetNames = {
	tdx_daily_history: "本地日线快照",
	security_master: "证券基础资料",
	limit_up_pool: "涨停池快照",
	lhb_data: "龙虎榜原始快照",
	public_research: "公开资讯与公告证据",
	tdx_tq_formula: "通达信 TQ 公式现场证据",
	tdx_formula_source_archive: "通达信公式源归档",
	unified_source_manifest: "统一数据源落盘清单",
	unified_source_verification: "统一数据源落盘校验",
	package_source_inventory: "行情能力包来源目录",
	execution_evidence: "任务回执与报告"
};
var skill14Groups = {
	"individual-stock-analysis-v31": "research",
	"golden-ignition-v8": "selection",
	"limit-advance-v44": "ladder",
	"leader-deep-research": "mainline",
	"unified-shortterm-score-v4": "research",
	"limit-up-review": "ladder",
	"short-burst-score-v5": "selection",
	"short-term-sentiment-v22": "mainline",
	"quant-production-v65": "selection",
	"lhb-postmarket-v43": "capital",
	"market-environment-v5": "mainline",
	"market-data-capabilities": "settings",
	"morning-intelligence-plan": "reports",
	"workbuddy-evolution-v22": "settings"
};
var skills = skill14_catalog_default.skills.map((skill) => ({
	id: skill.id,
	name: skill.name,
	alias: `${skill.mode} · ${skill.category}`,
	group: skill14Groups[skill.id] || "settings",
	dependencies: [...new Set([...skill.required, ...skill.optional])].map((asset) => skill14AssetNames[asset] || asset),
	entry: "本地 14 技能数据预检",
	state: "已适配本地预检",
	note: `${skill.summary} ${skill.degrade}`
}));
var d = (s) => dateLabel$1(s);
var p = (n) => `${n > 0 ? "+" : ""}${n.toFixed(2)}%`;
var money = (n) => `${(n / 1e8).toFixed(2)} 亿`;
var dataSourceLabels = {
	"tdx-local": "通达信本地日线",
	eastmoney: "东方财富行情接口",
	lianban: "连板网涨停/连板",
	akshare: "AkShare 聚合接口",
	tencent: "腾讯行情接口",
	sina: "新浪行情接口",
	baidu: "百度股市通",
	ths: "同花顺接口",
	iwencai: "同花顺问财",
	cls: "财联社",
	baostock: "BaoStock",
	sw: "申万行业数据",
	cninfo: "巨潮资讯",
	"exchange-official": "交易所官方",
	macro: "宏观数据接口",
	"public-web": "公开网页来源",
	"eastmoney-news": "东方财富快讯",
	"sina-financial": "新浪财务三表",
	"tencent-share-capital": "腾讯流通股本/总股本",
	"tdx-index-daily": "通达信指数日线",
	"longhubang-snapshot": "龙虎榜统一快照",
	"eastmoney-margin": "东方财富融资融券",
	eastmoneyLimitUp: "东方财富涨停池",
	eastmoneyLhb: "东方财富龙虎榜",
	akshareLhb: "AkShare 龙虎榜",
	akshareLhbSina: "AkShare 新浪龙虎榜",
	akshareLhbStockStatistic: "AkShare 龙虎榜统计",
	akshareLimitUpPool: "AkShare 涨停池",
	akshareLhbStockDetail: "AkShare 席位明细",
	news: "东财快讯新闻"
};
var numericField = (row, ...keys) => {
	for (const key of keys) {
		const value = row[key];
		if (value !== void 0 && value !== null && value !== "") {
			const parsed = Number(String(value).replace(/,/g, ""));
			if (Number.isFinite(parsed)) return parsed;
		}
	}
	return 0;
};
var normalizeCapitalRows = (snapshot) => {
	const eastmoneyRows = snapshot?.sources?.eastmoneyLhb?.data?.result?.data || [];
	return (eastmoneyRows.length ? eastmoneyRows : snapshot?.sources?.akshareLhb?.data?.records || []).map((row) => ({
		code: String(row.SECURITY_CODE || row["代码"] || row["股票代码"] || ""),
		name: String(row.SECURITY_NAME_ABBR || row["名称"] || row["股票名称"] || "—"),
		net: numericField(row, "BILLBOARD_NET_AMT", "龙虎榜净买额", "净额"),
		buy: numericField(row, "BILLBOARD_BUY_AMT", "买入额", "买入金额"),
		sell: numericField(row, "BILLBOARD_SELL_AMT", "卖出额", "卖出金额"),
		reason: String(row.EXPLAIN || row["上榜原因"] || row["解读"] || "—")
	})).filter((row) => row.code).sort((a, b) => b.net - a.net);
};
var reportKey = (date) => `zhangcai.report.v2.${date}`;
var strategyRunsKey = "zhangcai.strategy.runs.v1";
var selectedStrategyKey = "zhangcai.strategy.selected.v1";
var strategyCatalogById = new Map(strategy_catalog_default.map((item) => [item.id, item]));
var strategyCatalogAliases = { "golden-ignition-v8": "golden-ignition" };
function strategyCatalogItem(id) {
	return strategyCatalogById.get(id) || strategyCatalogById.get(strategyCatalogAliases[id] || id);
}
function strategyDataStatus(id) {
	if (DATA_INSUFFICIENT_SKILLS.has(id)) return "missing";
	return strategyCatalogItem(id)?.dataStatus || "available";
}
function loadStrategyRuns() {
	return {};
}
var strategyPreflightDisplayNote = "说明：已调用对应原始策略评分引擎完成本地数值回执；Harness 负责基于同一份回执解释结果、列出缺失项与风险边界，不生成买卖建议。";
function strategyPreflightDisplayText(output) {
	return String(output || "").replace("说明：本报告是网页适配层的真实数据预检与落盘运行单；未调用原始策略入口，因此不构成策略已执行或投资结论。", strategyPreflightDisplayNote);
}
function strategyRunDataDate(run) {
	const parsed = run.harnessOutput ? normalizeHarnessOutput(run.harnessOutput) : null;
	const harnessDate = String(parsed?.dataDate || "").replace(/\D/g, "");
	if (harnessDate.length >= 8) return harnessDate.slice(0, 8);
	const assets = run.receipt?.assets;
	const daily = assets && typeof assets === "object" ? assets.tdx_daily_history : null;
	const receiptDate = daily && typeof daily === "object" ? String(daily.trade_date || "").replace(/\D/g, "") : "";
	return receiptDate.length >= 8 ? receiptDate.slice(0, 8) : "";
}
var nonEquityNames = new Set([
	"上证指数",
	"深证成指",
	"创业板指",
	"科创50",
	"上证50",
	"北证50"
]);
var harnessEstimateSeconds = {
	"five-dimension-resonance": 900,
	"stock-analysis": 240,
	"stock-study": 240,
	"stock-research-engine": 240,
	"a-share-leader-deep-research": 300,
	"a-share-limit-up-mining": 300,
	"limit-up-review": 300,
	"morning-intelligence-plan": 300
};
var estimateSeconds = (skillId) => harnessEstimateSeconds[skillId] || 300;
var formatDuration = (seconds) => `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
var DATA_INSUFFICIENT_SKILLS = new Set([
	"convertible-bond-screening-strategy",
	"a-share-longhubang-analysis",
	"a-share-leader-deep-research",
	"a-share-limit-up-leader-classification",
	"a-share-limit-up-mining",
	"youzi-capital-monitoring",
	"stock-recap-video"
]);
var BASIC_SKILLS = new Set([
	"stock-unified",
	"tdx-local-hub",
	"stock-hard-gate",
	"stock-watchlist",
	"kaipanla",
	"market-data-capabilities",
	"workbuddy-evolution-v22"
]);
var skillMode = (skillId) => DATA_INSUFFICIENT_SKILLS.has(skillId) ? "data" : BASIC_SKILLS.has(skillId) ? "basic" : "runnable";
var skillIntroductions = {
	"a-share-15d-selection": "从通达信日线和多维强势因子中筛选短线候选，保留交易日与样本范围。",
	"five-dimension-resonance": "组合趋势、量价、资金、情绪与题材等维度，输出共振候选和数据边界。",
	"dragon-pullback": "识别强势股回调后的再启动形态，依据本地日线生成龙回头候选。",
	"a-share-hotspot-sentiment-analysis": "汇总行情、热点和新闻线索，形成主线与情绪结构的只读研判。",
	"core-mainline-scoring-system": "按板块强度、扩散度和代表股表现给当日主线候选评分。",
	"a-share-longhubang-analysis": "读取龙虎榜公开记录，整理净买额、席位和资金方向线索。",
	"limit-up-review": "复盘涨停候选、连板梯队和前一交易日表现，区分事实与日线推导。",
	"stock-analysis": "围绕单只股票整理行情、技术面、公告和风险信息，生成结构化研究。",
	"financial-roe-analysis": "从净资产收益率及杜邦分解观察公司的盈利质量和变化来源。",
	"technical-analysis": "基于本地 K 线计算趋势、支撑压力和常用技术指标。",
	"risk-mine-clearance": "检查个股公告、经营和行情风险线索，给出可核验的排雷清单。",
	"tdx-local-hub": "连接通达信本地日线、板块、公式和缓存，为其他技能提供数据底座。",
	"market-data-capabilities": "统一说明公开行情、资讯、通达信、本地落盘和降级来源的接入范围、实际状态与适用边界。",
	"workbuddy-evolution-v22": "说明用户纠错、硬规则、回归校验和交付闸门如何形成质量闭环，并区分规则说明与真实执行证据。"
};
function skillIntroduction(skill) {
	return skillIntroductions[skill.id] || `${groupNames[skill.group] || "股票研究"}能力：围绕${skill.name}整理当日数据、执行边界与可核验结果。`;
}
function Box({ title, children, extra, className = "" }) {
	return /* @__PURE__ */ jsxs("section", {
		className: `panel ${className}`,
		children: [/* @__PURE__ */ jsxs("div", {
			className: "panel-head",
			children: [/* @__PURE__ */ jsx("h2", { children: title }), extra]
		}), children]
	});
}
function Empty({ title, body }) {
	return /* @__PURE__ */ jsxs("div", {
		className: "empty-state",
		children: [
			/* @__PURE__ */ jsx(FolderOpen, { size: 32 }),
			/* @__PURE__ */ jsx("h3", { children: title }),
			/* @__PURE__ */ jsx("p", { children: body })
		]
	});
}
function Tags({ list }) {
	return /* @__PURE__ */ jsx("div", {
		className: "tags",
		children: list.map((t) => /* @__PURE__ */ jsx("span", { children: t }, t))
	});
}
function limitPct(stock) {
	if (stock.name.includes("ST") || stock.name.includes("*ST")) return 5;
	if (stock.market === "bj" || stock.code.startsWith("920")) return 30;
	if (/^(300|301|688|689)/.test(stock.code)) return 20;
	return 10;
}
function stockRows(stock) {
	const rows = Array.isArray(stock.history) ? [...stock.history] : [];
	if (!rows.length || rows[rows.length - 1].date !== stock.date) rows.push(stock);
	return rows;
}
function limitCandidate(stock, officialCodes = []) {
	const rows = stockRows(stock);
	const threshold = typeof stock.limitPct === "number" ? stock.limitPct : limitPct(stock);
	let streak = typeof stock.limitStreak === "number" ? stock.limitStreak : 0;
	if (!streak) for (let i = rows.length - 1; i >= 0; i -= 1) {
		const current = rows[i];
		const prev = rows[i - 1];
		if ((i === rows.length - 1 ? stock.pct : prev?.close ? (current.close / prev.close - 1) * 100 : 0) >= threshold - .35) streak += 1;
		else break;
	}
	const confirmed = officialCodes.length ? officialCodes.includes(stock.code) : stock.pct >= threshold - .35;
	return {
		stock,
		limitPct: threshold,
		streak,
		currentPct: stock.pct,
		confirmed
	};
}
function buildLadder(stocks, officialCodes = []) {
	return stocks.map((x) => limitCandidate(x, officialCodes)).filter((x) => x.confirmed).sort((a, b) => b.streak - a.streak || b.currentPct - a.currentPct || b.stock.amount - a.stock.amount);
}
function rankRows(stocks, sort, size = 10) {
	return stocks.filter((s) => s.date === stocks[0]?.date).filter((s) => !nonEquityNames.has(s.name)).sort((a, b) => sort === "pct" ? b.pct - a.pct || b.amount - a.amount : sort === "loss" ? a.pct - b.pct || b.amount - a.amount : b.amount - a.amount || b.pct - a.pct).slice(0, size).map(({ code, name, pct, amount, close, market }) => ({
		code,
		name,
		pct,
		amount,
		close,
		market
	}));
}
function buildAvailability(market, ladder) {
	const official = (market.tdxLimitUpCodes || []).length > 0;
	const proxy = market.intradayProxy;
	const sectorCoverage = market.sectors?.length ? Math.max(...market.sectors.map((x) => x.count)) : 0;
	const source = market.dataSources || {};
	const supplemental = market.supplemental || {};
	const coverage = supplemental.coverage || {};
	const indexDailyAvailable = coverage.index_daily === true;
	const lhbAvailable = coverage.longhubang_snapshot === true || Boolean(market.publicLhbRecords?.length);
	const lhbMarketCount = supplemental.lhbMarketRecordCount || supplemental.lhbRecordCount || market.publicLhbRecords?.length || 0;
	const marginAvailable = coverage.margin_snapshot === true;
	const marginDate = supplemental.marginLatestAvailableDate || supplemental.date || market.date;
	return [
		{
			item: "市场广度与主要指数",
			status: "可用",
			evidence: `${market.currentCount} 只同日样本、${market.indices.length} 个指数`,
			solution: "随通达信日线刷新"
		},
		{
			item: "主要指数历史日线",
			status: indexDailyAvailable ? "可用" : "缺失",
			evidence: indexDailyAvailable ? `本地补充快照已提供 ${supplemental.indexSymbolCount || 0} 组指数完整日线，并保留起止日期` : "尚未读取 evidence/supplemental/<date>/market.json 的指数日线快照",
			solution: indexDailyAvailable ? "Harness 通过统一补充快照复用，不再扫描巨型全市场 JSONL" : "执行“补齐其他数据”或统一落盘，先从 TDX .day 生成指数索引"
		},
		{
			item: "财务三表",
			status: coverage.financial === true ? "可用" : "按需",
			evidence: coverage.financial === true ? "目标股票财务三表已按股东权益、利润表和现金流量表落盘" : "财务三表不是全市场每日快照，进入个股研究/Harness 后按目标代码读取新浪财务源",
			solution: "请求个股研究时自动写入 evidence/supplemental/<date>/<code>.<market>.json，并保留报告期日期"
		},
		{
			item: "流通股本与总股本",
			status: coverage.share_capital === true ? "可用" : "按需",
			evidence: coverage.share_capital === true ? "腾讯报价原始字段 72/73 已解析为流通股本/总股本，并同步保存市值与估值字段" : "股本属于个股维度，当前市场页未指定目标代码，等待个股请求按需读取",
			solution: "个股 Harness 启动前自动补齐并把股本快照传入 context，不用市值反推股本"
		},
		{
			item: "个股涨幅榜",
			status: "可用",
			evidence: `已从同日 ${market.currentCount} 只样本排序`,
			solution: "报告直接引用当日榜单"
		},
		{
			item: "个股成交额榜",
			status: "可用",
			evidence: "日线文件含 amount 字段，已排序",
			solution: "报告直接引用当日榜单"
		},
		{
			item: "涨停与连板梯队",
			status: official ? "可用" : "推导",
			evidence: official ? `TDX ${market.tdxLimitUpFiles?.join("、") || "ZTC/FLZT"} 提供 ${market.tdxLimitUpCodes?.length} 个代码，连板由历史日线计算` : `${ladder.length} 个涨跌停阈值候选，连板由历史日线计算`,
			solution: "继续校验交易所涨停名单、炸板和停牌状态"
		},
		{
			item: "跌停与负反馈榜",
			status: market.stocks.some((s) => s.pct < 0) ? "推导" : "缺失",
			evidence: market.stocks.some((s) => s.pct < 0) ? `按 ${market.currentCount} 只同日样本排序跌幅榜；达到各市场跌停阈值的候选 ${market.tdxLimitDownCodes?.length || 0} 只` : "本地没有 FLDT 或同等跌停名单文件",
			solution: "当前使用日线阈值推导；接入交易所跌停名单和盘中状态后升级为官方负反馈榜"
		},
		{
			item: "封板率/炸板/首封时刻",
			status: proxy?.upperHitCount ? "推导" : "缺失",
			evidence: proxy?.upperHitCount ? `OHLC 代理识别触板 ${proxy.upperHitCount} 只、收盘封板 ${proxy.upperClosedCount} 只、触板后开板 ${proxy.openedAfterHitCount} 只；封板率 ${proxy.sealRatePct ?? "—"}%，炸板率 ${proxy.explosionRatePct ?? "—"}%，首封时刻未提供（5 分钟文件同日覆盖 ${proxy.lc5CurrentDateCount}/${proxy.lc5Files}）` : "收盘日线不包含盘中封板过程",
			solution: proxy?.upperHitCount ? "当前先用日线 high/close 代理并明确标注；接入同日 1 分钟/逐笔数据后替换为首封、回封和精确炸板率" : "接入 1 分钟或逐笔数据，计算首封、开板、回封、封板率和炸板率"
		},
		{
			item: "前日涨停表现与情绪周期",
			status: market.priorLimitUpStats?.count ? "推导" : "缺失",
			evidence: market.priorLimitUpStats?.count ? `由 ${market.priorLimitUpStats.previousDate || "前一交易日"} 日线涨停候选配对今日表现，共 ${market.priorLimitUpStats.count} 只，今日均值 ${market.priorLimitUpStats.todayAvgPct ?? 0}%` : "当前快照没有前一交易日涨停池与次日表现配对表",
			solution: "当前使用历史日线推导晋级表现；保存每日官方涨停池快照后再计算正式情绪周期"
		},
		{
			item: "融资融券/北向资金",
			status: marginAvailable ? "可用" : "缺失",
			evidence: marginAvailable ? `融资融券已落盘 ${supplemental.marginRecordCount || 0} 条，最近可得日期 ${d(marginDate)}；精确到目标日 ${supplemental.marginExactDate || 0} 条。北向资金仍单独标注为未接入` : `已发现 TDX 融资融券页面配置（${source.financing?.configFile || "func_gx_rzrq101.xml"}），但本地补充快照未返回可用记录；北向资金仍需单独接入`,
			solution: marginAvailable ? "Harness 使用融资余额、融资买入/偿还、融券余额等原始字段；无目标日记录时保留最近可得日期，不用 0 代替" : "执行“补齐其他数据”，通过东方财富 datacenter 生成同日/最近可得融资融券快照"
		},
		{
			item: "板块涨幅榜",
			status: market.sectors?.length ? "可用" : "缺失",
			evidence: market.sectors?.length ? `TDX 行业成员映射覆盖 ${market.sectors.reduce((n, x) => n + x.count, 0)} 只同日样本，已按平均涨跌、成交额、涨停家数排序；最大单板块 ${sectorCoverage} 只` : "本地没有可用的行业成员映射",
			solution: market.sectors?.length ? "网页已直接呈现 TDX 行业榜和主题成员聚合；如需交易所官方板块指数，再配置对应板块日线源" : "接入行业分类与板块日线，按板块成交额和涨停家数排序"
		},
		{
			item: "龙虎榜净买与席位",
			status: lhbAvailable ? "可用" : "缺失",
			evidence: lhbAvailable ? `东方财富同日全市场龙虎榜快照已落盘 ${lhbMarketCount} 条；目标股票无匹配记录时按“无上榜记录”处理，不判为快照缺失` : "本地补充快照没有同日龙虎榜文件",
			solution: lhbAvailable ? "Harness 读取上榜日期、买卖额、净买额及可用席位明细；身份映射仍保持独立缺口" : "执行“补齐其他数据”，接入交易所/东方财富公开龙虎榜并保存来源日期"
		},
		{
			item: "主力资金流向",
			status: "缺失",
			evidence: "成交额不是净流入，TQ 公式桥接尚未启用（Num=0）",
			solution: "启用 TQ/L2 资金公式并记录公式版本、授权和时间戳"
		},
		{
			item: "新闻公告/催化",
			status: "缺失",
			evidence: "msg_zx 与 msg_web 目录不存在",
			solution: "接入可追溯新闻公告源，保留发布时间、原文链接和证券映射"
		},
		{
			item: "盘中封板/炸板/封单",
			status: proxy?.upperHitCount || proxy?.lowerHitCount ? "推导" : "缺失",
			evidence: proxy?.upperHitCount || proxy?.lowerHitCount ? `已生成涨停触板/收盘封板/开板代理和跌停触板代理；同日 5 分钟文件 ${proxy.lc5CurrentDateCount}/${proxy.lc5Files}，封单额与首封时间仍为空` : "只有收盘日线，不能重建盘中过程",
			solution: proxy?.upperHitCount || proxy?.lowerHitCount ? "当前使用可复算 OHLC 代理；接入同日 1 分钟或逐笔快照后补首封、回封和封单额" : "接入 1 分钟或逐笔快照，记录首封、开板、回封和封单额"
		}
	];
}
var themeDefs = [
	{
		name: "科技与AI",
		tag: "名称聚类",
		color: "#bd1f35",
		words: [
			"AI",
			"人工智能",
			"算力",
			"芯片",
			"半导体",
			"软件",
			"科技",
			"智能",
			"机器人",
			"通信",
			"数据"
		]
	},
	{
		name: "新能源与电力",
		tag: "名称聚类",
		color: "#d75b65",
		words: [
			"电力",
			"能源",
			"光伏",
			"风电",
			"储能",
			"锂",
			"电池",
			"充电",
			"氢"
		]
	},
	{
		name: "医药与生物",
		tag: "名称聚类",
		color: "#c77382",
		words: [
			"医药",
			"生物",
			"医疗",
			"药业",
			"制药",
			"疫苗",
			"器械",
			"蛋白"
		]
	},
	{
		name: "消费与农业",
		tag: "名称聚类",
		color: "#d39a54",
		words: [
			"食品",
			"乳业",
			"酒",
			"零售",
			"消费",
			"农业",
			"种业",
			"粮",
			"猪",
			"鸡",
			"牧业"
		]
	},
	{
		name: "高端制造",
		tag: "名称聚类",
		color: "#a94b61",
		words: [
			"机械",
			"装备",
			"材料",
			"制造",
			"工业",
			"汽车",
			"航空",
			"轨道"
		]
	},
	{
		name: "资源与化工",
		tag: "名称聚类",
		color: "#b45d4b",
		words: [
			"化工",
			"能源",
			"煤",
			"钢",
			"有色",
			"矿",
			"石油",
			"铝",
			"铜"
		]
	}
];
function boardThemes(boards, colors, limit = 12) {
	return boards.slice(0, limit).map((board, index) => ({
		name: board.name,
		tag: board.tag || "TDX板块成员聚合",
		count: board.count,
		avgPct: board.avgPct,
		amount: board.amount,
		leaders: board.leaders || [],
		color: colors[index % colors.length]
	}));
}
function buildThemes(stocks, conceptBoards = [], sectors = []) {
	const boardRows = conceptBoards.length ? conceptBoards : sectors;
	if (boardRows.length) return boardThemes(boardRows, [
		"#bd1f35",
		"#d75b65",
		"#c77382",
		"#d39a54",
		"#a94b61",
		"#b45d4b"
	]);
	const buckets = themeDefs.map((def) => ({
		...def,
		rows: []
	}));
	stocks.filter((s) => s.date === stocks[0]?.date).forEach((stock) => {
		const def = buckets.find((x) => x.words.some((word) => stock.name.toUpperCase().includes(word.toUpperCase())));
		if (def) def.rows.push(stock);
	});
	return buckets.filter((x) => x.rows.length).map((x) => ({
		name: x.name,
		tag: x.tag,
		count: x.rows.length,
		avgPct: x.rows.reduce((sum, s) => sum + s.pct, 0) / x.rows.length,
		amount: x.rows.reduce((sum, s) => sum + s.amount, 0),
		leaders: [...x.rows].sort((a, b) => b.pct - a.pct).slice(0, 3),
		color: x.color
	})).sort((a, b) => b.avgPct - a.avgPct || b.count - a.count);
}
function makeBaseReport(market, themes, ladder) {
	const ratio = market.currentCount ? market.up / market.currentCount * 100 : 0;
	const gainLeaders = rankRows(market.stocks, "pct", 10);
	const amountLeaders = rankRows(market.stocks, "amount", 10);
	const lossLeaders = rankRows(market.stocks, "loss", 10);
	const limitDownCandidates = market.tdxLimitDownCodes?.length ? market.stocks.filter((s) => market.tdxLimitDownCodes?.includes(s.code)).sort((a, b) => a.pct - b.pct).slice(0, 10).map(({ code, name, pct, amount, close, market: venue }) => ({
		code,
		name,
		pct,
		amount,
		close,
		market: venue
	})) : lossLeaders.filter((s) => s.pct < -9.5);
	const availability = buildAvailability(market, ladder);
	return {
		title: `掌财智能体 · ${d(market.date)} 行情复盘`,
		generatedBy: "网页脚本 + 本地规则",
		date: market.date,
		source: "本地日线归档",
		scope: `同日样本 ${market.currentCount} 只，覆盖沪深北；排除旧日期 ${market.staleCount} 只`,
		summary: `市场上涨 ${market.up} 只、下跌 ${market.down} 只、平盘 ${market.flat} 只，上涨占比 ${ratio.toFixed(1)}%。已接入 TDX 榜单、指数日线、龙虎榜和融资融券补充快照；财务与股本在个股研究时按代码按需补齐。`,
		metrics: [
			{
				label: "同日样本",
				value: `${market.currentCount} 只`,
				detail: `总可读 ${market.total} 只`
			},
			{
				label: "上涨 / 下跌",
				value: `${market.up} / ${market.down}`,
				detail: `平盘 ${market.flat} 只`
			},
			{
				label: "样本成交额",
				value: `${(market.amount / 0xe8d4a51000).toFixed(2)} 万亿`,
				detail: "沪深北样本合计"
			},
			{
				label: "日线涨停候选",
				value: `${ladder.length} 只`,
				detail: market.tdxLimitUpCodes?.length ? `TDX ZTC/FLZT ${market.tdxLimitUpCodes.length} 个代码` : "按涨跌停阈值推导"
			},
			{
				label: "行业板块榜",
				value: `${market.sectors?.length || 0} 个`,
				detail: market.sectors?.length ? "TDX 行业成员聚合并按平均涨跌排序" : "等待行业映射"
			},
			{
				label: "触板/封板代理",
				value: `${market.intradayProxy?.upperHitCount || 0} / ${market.intradayProxy?.upperClosedCount || 0} 只`,
				detail: "日线 OHLC 代理；首封时刻未提供"
			},
			{
				label: "缺失数据项",
				value: `${availability.filter((x) => x.status === "缺失").length} 项`,
				detail: "报告已逐项列出解决办法"
			}
		],
		indices: market.indices,
		themes,
		ladder: ladder.slice(0, 12),
		gainLeaders,
		amountLeaders,
		lossLeaders,
		limitDownCandidates,
		priorLimitUpStats: market.priorLimitUpStats,
		sectors: market.sectors || [],
		conceptBoards: market.conceptBoards || [],
		intradayProxy: market.intradayProxy,
		availability,
		cautions: [
			"本报告只使用本地通达信日线快照，不代表实时行情。",
			"主线与行业榜使用 TDX 本地成员映射和主题成员聚合；代表股是候选，不等同于交易所官方行业龙头。",
			"跌停、前日涨停表现和封板率已由日线推导；龙虎榜与融资融券使用已落盘的公开快照，目标日无精确融资记录时显示最近可得日期；北向资金、主力资金和当日新闻仍需各自来源确认。"
		],
		actions: ["用 DeepSeek Harness 对 TDX 行业/主题榜、涨幅榜、成交额榜、主线候选和涨停梯队做结构化复核。", "个股研究会自动补齐财务三表与流通/总股本；继续补入北向、主力公式、新闻和同日 1 分钟快照后，相关状态会独立升级。"]
	};
}
function loadReport(date) {
	return null;
}
function parseHarnessOutput(raw) {
	const parsed = normalizeHarnessOutput(raw);
	return {
		...parsed,
		dataScope: parsed.dataScope
	};
}
function buildAiPresentation(raw, base, label) {
	const parsed = parseHarnessOutput(raw);
	const summary = parsed.summary || base.summary;
	const themes = base.themes.slice(0, 3).map((item) => `${item.name} ${p(item.avgPct)}`).join("、");
	const ladder = base.ladder.slice(0, 3).map((item) => `${item.stock.name} ${item.streak}天`).join("、");
	return {
		summary,
		cautions: parsed.cautions,
		dataScope: parsed.dataScope,
		presentation: {
			headline: `${label}已按本地 ${d(base.date)} 行情整理为可读结论。`,
			findings: [
				{
					title: "模型摘要",
					text: summary
				},
				{
					title: "行情证据",
					text: `主线候选：${themes || "暂无足够主题样本"}；涨停与连板候选：${ladder || "暂无"}。`
				},
				{
					title: "数据边界",
					text: `报告使用${base.scope}。缺失项仍以“缺失”标示，未用模型内容替代原始行情。`
				},
				...parsed.findings
			],
			tables: parsed.tables,
			jsonValid: parsed.jsonValid,
			parseError: parsed.parseError
		}
	};
}
function ReportVisual({ report }) {
	const max = Math.max(...report.themes.slice(0, 5).map((item) => Math.abs(item.avgPct)), 1);
	return /* @__PURE__ */ jsxs("section", {
		className: "report-visual",
		"aria-label": "市场结构图",
		children: [/* @__PURE__ */ jsxs("div", {
			className: "report-visual-head",
			children: [/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("span", { children: "图文速览" }), /* @__PURE__ */ jsx("h4", { children: "市场结构图" })] }), /* @__PURE__ */ jsx("p", { children: "以同日通达信快照绘制，不含实时盘中数据。" })]
		}), /* @__PURE__ */ jsxs("div", {
			className: "report-visual-grid",
			children: [/* @__PURE__ */ jsxs("div", {
				className: "report-breadth-card",
				children: [
					/* @__PURE__ */ jsx("small", { children: "上涨 / 下跌 / 平盘" }),
					/* @__PURE__ */ jsxs("div", {
						className: "report-breadth-bar",
						children: [
							/* @__PURE__ */ jsx("span", {
								className: "up-fill",
								style: { flex: Number(report.metrics.find((x) => x.label === "上涨家数")?.value.replace(/\D/g, "") || 0) }
							}),
							/* @__PURE__ */ jsx("span", {
								className: "flat-fill",
								style: { flex: Number(report.metrics.find((x) => x.label === "平盘家数")?.value.replace(/\D/g, "") || 0) }
							}),
							/* @__PURE__ */ jsx("span", {
								className: "down-fill",
								style: { flex: Number(report.metrics.find((x) => x.label === "下跌家数")?.value.replace(/\D/g, "") || 0) }
							})
						]
					}),
					/* @__PURE__ */ jsx("p", { children: report.metrics.filter((x) => /上涨家数|下跌家数|平盘家数/.test(x.label)).map((x) => `${x.label.replace("家数", "")} ${x.value}`).join(" · ") })
				]
			}), /* @__PURE__ */ jsxs("div", {
				className: "report-theme-chart",
				children: [/* @__PURE__ */ jsx("small", { children: "主题候选平均涨跌" }), report.themes.slice(0, 5).map((item) => /* @__PURE__ */ jsxs("div", {
					className: "report-theme-row",
					children: [
						/* @__PURE__ */ jsx("span", { children: item.name }),
						/* @__PURE__ */ jsx("i", { children: /* @__PURE__ */ jsx("b", {
							className: item.avgPct >= 0 ? "up-fill" : "down-fill",
							style: { width: `${Math.max(8, Math.abs(item.avgPct) / max * 100)}%` }
						}) }),
						/* @__PURE__ */ jsx("em", {
							className: item.avgPct >= 0 ? "up" : "down",
							children: p(item.avgPct)
						})
					]
				}, `chart-${item.name}`))]
			})]
		})]
	});
}
function harnessParseNotice(error, prefix = "输出") {
	if (error?.includes("恢复已完成字段")) return "旧版桥接输出曾被截断，已恢复已完成字段并排版；重新执行后会保存完整 JSON。";
	return `${prefix}已做兼容规范化：${error || "未通过严格 JSON 校验"}。`;
}
function harnessStatusLabel(status) {
	return {
		ok: "已完成",
		completed: "已完成",
		CLEAN_PASS: "校验通过",
		available: "数据可用",
		running: "运行中",
		pending: "等待中",
		BLOCKED: "数据阻塞",
		FAILED: "失败",
		failed: "失败"
	}[status] || status || "未知";
}
function HarnessOutput({ raw, structured, compact = true }) {
	const parsed = parseHarnessOutput(raw);
	const structuredAnalysis = structured?.analysis || {};
	const structuredSummary = structuredAnalysis.name || structuredAnalysis.symbol ? `${strategyValue(structuredAnalysis.name)}（${strategyValue(structuredAnalysis.symbol)}）策略交付物已生成，已按行情、公式输出和子系统结果排版。` : "";
	const visibleFindings = compact ? parsed.findings.slice(0, 5) : parsed.findings;
	const visibleTables = compact ? parsed.tables.slice(0, 3) : parsed.tables;
	const hiddenFindings = compact ? parsed.findings.slice(5) : [];
	const hiddenTables = compact ? parsed.tables.slice(3) : [];
	const compactTable = (table) => ({
		...table,
		rows: compact ? table.rows.slice(0, 10) : table.rows
	});
	return /* @__PURE__ */ jsxs("section", {
		className: "harness-output-card",
		children: [
			/* @__PURE__ */ jsxs("div", {
				className: "ai-report-reading-head",
				children: [
					/* @__PURE__ */ jsx(Sparkles, { size: 16 }),
					/* @__PURE__ */ jsx("b", { children: "已排版的技能输出" }),
					/* @__PURE__ */ jsx("span", { children: "已存入我的报告" })
				]
			}),
			/* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
				/* @__PURE__ */ jsx(TableHead, { children: "运行状态" }),
				/* @__PURE__ */ jsx(TableHead, { children: "数据日期" }),
				/* @__PURE__ */ jsx(TableHead, { children: "数据范围" })
			] }) }), /* @__PURE__ */ jsx(TableBody, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
				/* @__PURE__ */ jsx(TableCell, { children: /* @__PURE__ */ jsx("span", {
					className: parsed.status === "CLEAN_PASS" || parsed.status === "ok" || parsed.status === "completed" ? "status-good" : "status-warn",
					children: harnessStatusLabel(parsed.status)
				}) }),
				/* @__PURE__ */ jsx(TableCell, { children: parsed.dataDate || "—" }),
				/* @__PURE__ */ jsx(TableCell, { children: parsed.dataScope || "—" })
			] }) })] }),
			/* @__PURE__ */ jsx(StructuredStrategyOutput, { structured }),
			/* @__PURE__ */ jsx("p", { children: parsed.summary || structuredSummary || "Harness 未返回摘要，请在下方查看原始响应。" }),
			!parsed.jsonValid && /* @__PURE__ */ jsx("p", {
				className: "form-error",
				children: harnessParseNotice(parsed.parseError, "输出")
			}),
			visibleFindings.length > 0 && /* @__PURE__ */ jsx("div", {
				className: "ai-finding-grid",
				children: visibleFindings.map((item, index) => /* @__PURE__ */ jsxs("article", { children: [/* @__PURE__ */ jsx("h5", { children: item.title }), /* @__PURE__ */ jsx("p", { children: item.text })] }, `${item.title}-${index}`))
			}),
			visibleTables.length > 0 && visibleTables.map((table, index) => /* @__PURE__ */ jsx(HarnessDataTable, { table: compactTable(table) }, `${table.title}-${index}`)),
			compact && (hiddenFindings.length > 0 || hiddenTables.length > 0 || parsed.tables.some((table) => table.rows.length > 10)) && /* @__PURE__ */ jsxs("details", {
				className: "harness-more",
				children: [
					/* @__PURE__ */ jsx("summary", { children: "查看完整分析（保留全部结论与表格）" }),
					hiddenFindings.length > 0 && /* @__PURE__ */ jsx("div", {
						className: "ai-finding-grid",
						children: hiddenFindings.map((item, index) => /* @__PURE__ */ jsxs("article", { children: [/* @__PURE__ */ jsx("h5", { children: item.title }), /* @__PURE__ */ jsx("p", { children: item.text })] }, `${item.title}-more-${index}`))
					}),
					hiddenTables.map((table, index) => /* @__PURE__ */ jsx(HarnessDataTable, { table }, `${table.title}-more-${index}`)),
					visibleTables.filter((table) => table.rows.length > 10).map((table, index) => /* @__PURE__ */ jsx(HarnessDataTable, { table: {
						...table,
						rows: table.rows.slice(10)
					} }, `${table.title}-rows-${index}`))
				]
			}),
			parsed.cautions.length > 0 && /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsx(TableRow, { children: /* @__PURE__ */ jsx(TableHead, { children: "风险与数据边界" }) }) }), /* @__PURE__ */ jsx(TableBody, { children: parsed.cautions.map((item) => /* @__PURE__ */ jsx(TableRow, { children: /* @__PURE__ */ jsx(TableCell, { children: item }) }, item)) })] }),
			/* @__PURE__ */ jsxs("details", {
				className: "report-raw",
				children: [/* @__PURE__ */ jsx("summary", { children: "查看原始 JSON" }), /* @__PURE__ */ jsx("pre", { children: raw })]
			})
		]
	});
}
function harnessTableCellText(table, column, cell) {
	const value = cell || "—";
	if (!table.title.includes("候选")) return value;
	if (column === "波段") return value.replace(/\s*·\s*/g, "\n");
	if (column === "游资" || column === "机构" || column === "风险") return value.replace(/\s*；\s*/g, "\n");
	return value;
}
function HarnessDataTable({ table }) {
	const displayTable = table.title.includes("候选") && (table.columns.includes("主模型") || table.rows.some((row) => row[5]?.startsWith("模型分量") || row[4]?.includes("核心结构") || row[4]?.includes("主模型"))) && !table.columns.includes("主模型") ? {
		...table,
		columns: [
			"排名",
			"代码",
			"名称",
			"评分",
			"波段",
			"主模型",
			"游资",
			"机构",
			"风险"
		],
		rows: table.rows.map((row) => {
			const parts = String(row[4] || "").split(/\s*·\s*/);
			const last = parts.at(-1) || "";
			const hasModel = /^(待闭合：|已触发：|无主模型)/.test(last);
			return [
				...row.slice(0, 4),
				hasModel ? parts.slice(0, -1).join(" · ") : row[4] || "—",
				hasModel ? last : "无主模型",
				...row.slice(5)
			];
		})
	} : table;
	const displayCandidateTable = displayTable.title.includes("候选");
	const displayQuantTable = displayCandidateTable && displayTable.columns.includes("主模型");
	return /* @__PURE__ */ jsxs("section", {
		className: `harness-data-table${displayCandidateTable ? " harness-candidate-table" : ""}`,
		children: [/* @__PURE__ */ jsx("h5", { children: displayTable.title }), /* @__PURE__ */ jsxs(Table, {
			className: displayCandidateTable ? `harness-candidate-table-grid${displayQuantTable ? " harness-candidate-table-grid-v2" : ""}` : void 0,
			children: [
				displayCandidateTable && /* @__PURE__ */ jsx("colgroup", { children: displayTable.columns.map((column, index) => /* @__PURE__ */ jsx("col", { className: `harness-col-${column}` }, `${column}-${index}`)) }),
				/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsx(TableRow, { children: displayTable.columns.map((column) => /* @__PURE__ */ jsx(TableHead, { children: column }, column)) }) }),
				/* @__PURE__ */ jsx(TableBody, { children: displayTable.rows.map((row, rowIndex) => /* @__PURE__ */ jsx(TableRow, { children: row.map((cell, cellIndex) => /* @__PURE__ */ jsx(TableCell, { children: /* @__PURE__ */ jsx("span", {
					className: "harness-table-cell-text",
					children: harnessTableCellText(displayTable, displayTable.columns[cellIndex] || "", cell)
				}) }, `${rowIndex}-${cellIndex}`)) }, rowIndex)) })
			]
		})]
	});
}
function strategyValue(value) {
	if (value == null || value === "") return "—";
	if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value);
	try {
		return JSON.stringify(value);
	} catch {
		return String(value);
	}
}
function StructuredStrategyOutput({ structured }) {
	if (!structured) return null;
	const analysis = structured.analysis || {};
	const dateContext = analysis.date_context && typeof analysis.date_context === "object" ? analysis.date_context : {};
	const realtime = analysis.realtime_calc && typeof analysis.realtime_calc === "object" ? analysis.realtime_calc : {};
	const latest = analysis.latest_outputs && typeof analysis.latest_outputs === "object" ? analysis.latest_outputs : {};
	const derived = structured.derived || analysis.derived || {};
	const realtimeFields = [
		["收盘价", "last_close"],
		["涨跌幅", "change_pct"],
		["日线开盘", "open"],
		["日线最高", "high"],
		["日线最低", "low"],
		["成交量（手）", "volume_lot"],
		["成交额（万元）", "amount_wan"]
	];
	const dateFields = [
		["分析基准日", "analysis_as_of_date"],
		["公式最新日期", "formula_latest_date"],
		["日线最新日期", "kline_latest_date"],
		["数据模式", "mode"]
	];
	const realtimeRows = realtimeFields.filter(([, key]) => realtime[key] != null).map(([label, key]) => [label, strategyValue(realtime[key])]);
	const formulaRows = Object.entries(latest).map(([key, value]) => [key, strategyValue(value)]);
	const derivedRows = Object.entries(derived).map(([key, value]) => [key, strategyValue(value)]);
	return /* @__PURE__ */ jsxs("section", {
		className: "strategy-structured-report",
		children: [
			/* @__PURE__ */ jsxs("div", {
				className: "ai-report-reading-head",
				children: [
					/* @__PURE__ */ jsx(Sparkles, { size: 16 }),
					/* @__PURE__ */ jsx("b", { children: "结构化策略报告" }),
					/* @__PURE__ */ jsx("span", { children: "已读取策略交付物" })
				]
			}),
			/* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [/* @__PURE__ */ jsx(TableHead, { children: "项目" }), /* @__PURE__ */ jsx(TableHead, { children: "结果" })] }) }), /* @__PURE__ */ jsxs(TableBody, { children: [/* @__PURE__ */ jsxs(TableRow, { children: [/* @__PURE__ */ jsx(TableCell, { children: "标的" }), /* @__PURE__ */ jsxs(TableCell, { children: [
				strategyValue(analysis.name),
				" · ",
				strategyValue(analysis.symbol)
			] })] }), dateFields.filter(([, key]) => dateContext[key] != null).map(([label, key]) => /* @__PURE__ */ jsxs(TableRow, { children: [/* @__PURE__ */ jsx(TableCell, { children: label }), /* @__PURE__ */ jsx(TableCell, { children: strategyValue(dateContext[key]) })] }, key))] })] }),
			realtimeRows.length > 0 && /* @__PURE__ */ jsx(HarnessDataTable, { table: {
				title: "收盘行情快照",
				columns: ["项目", "数值"],
				rows: realtimeRows
			} }),
			formulaRows.length > 0 && /* @__PURE__ */ jsx(HarnessDataTable, { table: {
				title: "飞龙在天公式输出",
				columns: ["输出字段", "当日值"],
				rows: formulaRows
			} }),
			derivedRows.length > 0 && /* @__PURE__ */ jsx(HarnessDataTable, { table: {
				title: "子系统计算结果",
				columns: ["计算项", "结果"],
				rows: derivedRows
			} }),
			structured.reportMarkdown && /* @__PURE__ */ jsxs("details", {
				className: "strategy-markdown",
				children: [/* @__PURE__ */ jsx("summary", { children: "查看完整排版报告" }), /* @__PURE__ */ jsx("pre", { children: structured.reportMarkdown })]
			})
		]
	});
}
function StrategyReportGallery({ strategies, runs }) {
	const entries = strategies.map((skill) => ({
		skill,
		run: runs[skill.id]
	})).filter(({ run }) => !!run && !!(run.output || run.harnessOutput || run.structured));
	if (!entries.length) return null;
	return /* @__PURE__ */ jsxs(Box, {
		title: `策略运行回执 · ${entries.length} 项`,
		className: "strategy-report-gallery",
		children: [/* @__PURE__ */ jsx("div", {
			className: "strategy-report-gallery-intro",
			children: "每项保留最近一次本地预检与 Harness 分析；权威 JSON、任务记录和 Markdown 回执已保存到应用数据目录。"
		}), /* @__PURE__ */ jsx("div", {
			className: "strategy-report-gallery-grid",
			children: entries.map(({ skill, run }) => /* @__PURE__ */ jsxs("article", {
				className: "strategy-report-card",
				children: [
					/* @__PURE__ */ jsxs("div", {
						className: "strategy-report-card-head",
						children: [/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: skill.name }), /* @__PURE__ */ jsx("small", { children: skill.id })] }), /* @__PURE__ */ jsx("span", {
							className: run?.phase === "completed" ? "strategy-report-ok" : "strategy-report-warn",
							children: run?.status === "ERROR" ? "运行失败" : run?.phase === "completed" ? "Harness 已完成" : `预检 ${run?.status || "UNKNOWN"}`
						})]
					}),
					/* @__PURE__ */ jsx("div", {
						className: "strategy-run-output ready",
						children: /* @__PURE__ */ jsx("pre", { children: strategyPreflightDisplayText(run?.output) || "暂无预检回执。" })
					}),
					run?.harnessOutput && /* @__PURE__ */ jsx(HarnessOutput, {
						raw: run.harnessOutput,
						compact: false
					})
				]
			}, skill.id))
		})]
	});
}
function ArchivedStockReport({ item }) {
	const stock = item.content.stock || {};
	const parsed = normalizeHarnessOutput(item.raw || item.summary);
	const visibleFindings = parsed.findings.slice(0, 5);
	const visibleTables = parsed.tables;
	const textValue = (value, fallback = "—") => typeof value === "string" || typeof value === "number" ? String(value) : fallback;
	return /* @__PURE__ */ jsxs("section", {
		className: "stock-research-report",
		children: [
			/* @__PURE__ */ jsxs("div", {
				className: "ai-report-reading-head",
				children: [
					/* @__PURE__ */ jsx(Sparkles, { size: 16 }),
					/* @__PURE__ */ jsx("b", { children: "个股研究报告" }),
					/* @__PURE__ */ jsxs("span", { children: ["已归档 · ", parsed.jsonValid ? "JSON 已校验" : "已兼容规范化"] })
				]
			}),
			/* @__PURE__ */ jsx("p", { children: parsed.summary || item.summary }),
			/* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
				/* @__PURE__ */ jsx(TableHead, { children: "标的" }),
				/* @__PURE__ */ jsx(TableHead, { children: closeDateLabel(item.date) }),
				/* @__PURE__ */ jsx(TableHead, { children: "涨跌幅" }),
				/* @__PURE__ */ jsx(TableHead, { children: "数据日期" }),
				/* @__PURE__ */ jsx(TableHead, { children: "数据范围" })
			] }) }), /* @__PURE__ */ jsx(TableBody, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
				/* @__PURE__ */ jsxs(TableCell, { children: [
					textValue(stock.name),
					" · ",
					textValue(stock.code)
				] }),
				/* @__PURE__ */ jsx(TableCell, {
					title: closeDateLabel(item.date),
					children: stock.close == null ? "—" : Number(stock.close).toFixed(2)
				}),
				/* @__PURE__ */ jsx(TableCell, {
					className: Number(stock.pct || 0) >= 0 ? "up" : "down",
					children: stock.pct == null ? "—" : `${Number(stock.pct) >= 0 ? "+" : ""}${Number(stock.pct).toFixed(2)}%`
				}),
				/* @__PURE__ */ jsx(TableCell, { children: d(item.date) }),
				/* @__PURE__ */ jsx(TableCell, { children: item.dataScope })
			] }) })] }),
			visibleFindings.length > 0 && /* @__PURE__ */ jsx("div", {
				className: "ai-finding-grid",
				children: visibleFindings.map((finding, index) => /* @__PURE__ */ jsxs("article", { children: [/* @__PURE__ */ jsx("h5", { children: finding.title }), /* @__PURE__ */ jsx("p", { children: finding.text })] }, `${finding.title}-${index}`))
			}),
			visibleTables.map((table, index) => /* @__PURE__ */ jsx(HarnessDataTable, { table }, `${table.title}-${index}`)),
			parsed.findings.length > 5 && /* @__PURE__ */ jsxs("details", {
				className: "harness-more",
				children: [/* @__PURE__ */ jsx("summary", { children: "查看其余结论" }), parsed.findings.slice(5).map((finding, index) => /* @__PURE__ */ jsxs("article", { children: [/* @__PURE__ */ jsx("h5", { children: finding.title }), /* @__PURE__ */ jsx("p", { children: finding.text })] }, `more-${index}`))]
			}),
			parsed.cautions.length > 0 && /* @__PURE__ */ jsxs(Fragment$1, { children: [/* @__PURE__ */ jsx("h4", { children: "数据边界" }), /* @__PURE__ */ jsx("ul", {
				className: "report-list",
				children: parsed.cautions.slice(0, 6).map((caution, index) => /* @__PURE__ */ jsx("li", { children: caution }, `${caution}-${index}`))
			})] }),
			!parsed.jsonValid && /* @__PURE__ */ jsx("p", {
				className: "form-error",
				children: harnessParseNotice(parsed.parseError, "输出")
			}),
			/* @__PURE__ */ jsxs("details", {
				className: "report-raw",
				children: [/* @__PURE__ */ jsx("summary", { children: "查看原始 JSON" }), /* @__PURE__ */ jsx("pre", { children: item.raw || "" })]
			})
		]
	});
}
function ReportView({ report }) {
	return /* @__PURE__ */ jsxs("div", {
		className: "report-document",
		children: [
			/* @__PURE__ */ jsxs("div", {
				className: "report-document-head",
				children: [/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("h3", { children: report.title }), /* @__PURE__ */ jsxs("p", { children: [
					report.source,
					" · ",
					report.scope
				] })] }), /* @__PURE__ */ jsx("span", {
					className: "status-good",
					children: report.generatedBy
				})]
			}),
			/* @__PURE__ */ jsx("p", {
				className: "report-summary",
				children: report.summary
			}),
			report.aiPresentation && /* @__PURE__ */ jsxs("section", {
				className: "ai-report-reading",
				children: [
					/* @__PURE__ */ jsxs("div", {
						className: "ai-report-reading-head",
						children: [
							/* @__PURE__ */ jsx(Sparkles, { size: 16 }),
							/* @__PURE__ */ jsx("b", { children: "AI 排版解读" }),
							/* @__PURE__ */ jsx("span", { children: "已保留原始数据边界" })
						]
					}),
					/* @__PURE__ */ jsx("p", { children: report.aiPresentation.headline }),
					/* @__PURE__ */ jsx("div", {
						className: "ai-finding-grid",
						children: report.aiPresentation.findings.map((item, index) => /* @__PURE__ */ jsxs("article", { children: [/* @__PURE__ */ jsx("h5", { children: item.title }), /* @__PURE__ */ jsx("p", { children: item.text })] }, `${item.title}-${index}`))
					}),
					report.aiPresentation.tables?.map((table, index) => /* @__PURE__ */ jsx(HarnessDataTable, { table }, `${table.title}-${index}`)),
					report.aiPresentation.jsonValid === false && /* @__PURE__ */ jsx("p", {
						className: "form-error",
						children: harnessParseNotice(report.aiPresentation.parseError, "模型输出")
					})
				]
			}),
			/* @__PURE__ */ jsx(ReportVisual, { report }),
			/* @__PURE__ */ jsx("h4", { children: "一、市场概况" }),
			/* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
				/* @__PURE__ */ jsx(TableHead, { children: "指标" }),
				/* @__PURE__ */ jsx(TableHead, { children: "数值" }),
				/* @__PURE__ */ jsx(TableHead, { children: "说明" })
			] }) }), /* @__PURE__ */ jsx(TableBody, { children: report.metrics.map((row) => /* @__PURE__ */ jsxs(TableRow, { children: [
				/* @__PURE__ */ jsx(TableCell, { children: row.label }),
				/* @__PURE__ */ jsx(TableCell, {
					className: "numeric",
					children: /* @__PURE__ */ jsx("b", { children: row.value })
				}),
				/* @__PURE__ */ jsx(TableCell, { children: row.detail })
			] }, row.label)) })] }),
			/* @__PURE__ */ jsx("h4", { children: "二、指数表现" }),
			/* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
				/* @__PURE__ */ jsx(TableHead, { children: "指数" }),
				/* @__PURE__ */ jsx(TableHead, { children: "收盘" }),
				/* @__PURE__ */ jsx(TableHead, { children: "涨跌" }),
				/* @__PURE__ */ jsx(TableHead, { children: "日期" })
			] }) }), /* @__PURE__ */ jsx(TableBody, { children: report.indices.map((row) => /* @__PURE__ */ jsxs(TableRow, { children: [
				/* @__PURE__ */ jsxs(TableCell, { children: [row.name, /* @__PURE__ */ jsx("small", {
					className: "table-sub",
					children: row.code
				})] }),
				/* @__PURE__ */ jsx(TableCell, {
					className: "numeric",
					children: row.close.toFixed(2)
				}),
				/* @__PURE__ */ jsx(TableCell, {
					className: `numeric ${row.pct >= 0 ? "up" : "down"}`,
					children: p(row.pct)
				}),
				/* @__PURE__ */ jsx(TableCell, { children: d(row.date) })
			] }, row.code)) })] }),
			/* @__PURE__ */ jsx("h4", { children: "三、主线与板块候选（TDX行业/主题聚合）" }),
			/* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
				/* @__PURE__ */ jsx(TableHead, { children: "方向" }),
				/* @__PURE__ */ jsx(TableHead, { children: "样本数" }),
				/* @__PURE__ */ jsx(TableHead, { children: "平均涨跌" }),
				/* @__PURE__ */ jsx(TableHead, { children: "成交额" }),
				/* @__PURE__ */ jsx(TableHead, { children: "代表股" })
			] }) }), /* @__PURE__ */ jsx(TableBody, { children: report.themes.map((row) => /* @__PURE__ */ jsxs(TableRow, { children: [
				/* @__PURE__ */ jsxs(TableCell, { children: [/* @__PURE__ */ jsx("b", { children: row.name }), /* @__PURE__ */ jsx("small", {
					className: "table-sub",
					children: row.tag
				})] }),
				/* @__PURE__ */ jsx(TableCell, { children: row.count }),
				/* @__PURE__ */ jsx(TableCell, {
					className: `numeric ${row.avgPct >= 0 ? "up" : "down"}`,
					children: p(row.avgPct)
				}),
				/* @__PURE__ */ jsx(TableCell, {
					className: "numeric",
					children: money(row.amount)
				}),
				/* @__PURE__ */ jsx(TableCell, { children: row.leaders.map((x) => x.name).join("、") || "—" })
			] }, row.name)) })] }),
			/* @__PURE__ */ jsx("p", {
				className: "muted-copy",
				children: "主线候选优先使用 TDX 主题成员，其次使用 TDX 行业成员；代表股按同日涨跌与成交额排序，仅作候选参考。"
			}),
			/* @__PURE__ */ jsx("h5", { children: "TDX 行业板块涨幅榜" }),
			/* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
				/* @__PURE__ */ jsx(TableHead, { children: "板块" }),
				/* @__PURE__ */ jsx(TableHead, { children: "样本" }),
				/* @__PURE__ */ jsx(TableHead, { children: "平均涨跌" }),
				/* @__PURE__ */ jsx(TableHead, { children: "成交额" }),
				/* @__PURE__ */ jsx(TableHead, { children: "涨停家数" }),
				/* @__PURE__ */ jsx(TableHead, { children: "代表股" })
			] }) }), /* @__PURE__ */ jsx(TableBody, { children: (report.sectors || []).slice(0, 12).map((row) => /* @__PURE__ */ jsxs(TableRow, { children: [
				/* @__PURE__ */ jsxs(TableCell, { children: [/* @__PURE__ */ jsx("b", { children: row.name }), /* @__PURE__ */ jsx("small", {
					className: "table-sub",
					children: row.code
				})] }),
				/* @__PURE__ */ jsx(TableCell, { children: row.count }),
				/* @__PURE__ */ jsx(TableCell, {
					className: `numeric ${(row.avgPct || 0) >= 0 ? "up" : "down"}`,
					children: p(row.avgPct || 0)
				}),
				/* @__PURE__ */ jsx(TableCell, {
					className: "numeric",
					children: money(row.amount || 0)
				}),
				/* @__PURE__ */ jsx(TableCell, { children: row.limitCount ?? 0 }),
				/* @__PURE__ */ jsx(TableCell, { children: (row.leaders || []).map((x) => x.name).join("、") || "—" })
			] }, `sector-${row.code}`)) })] }),
			/* @__PURE__ */ jsx("p", {
				className: "muted-copy",
				children: "行业榜来源：C:\\\\new_tdx_mock\\\\T0002\\\\hq_cache\\\\tdxhy.cfg 与 cloud_cfg 行业树；未标注为申万或交易所官方板块指数。"
			}),
			/* @__PURE__ */ jsx("h4", { children: "四、涨停与连板候选" }),
			/* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
				/* @__PURE__ */ jsx(TableHead, { children: "股票" }),
				/* @__PURE__ */ jsx(TableHead, { children: "涨跌" }),
				/* @__PURE__ */ jsx(TableHead, { children: "阈值" }),
				/* @__PURE__ */ jsx(TableHead, { children: "连续候选" }),
				/* @__PURE__ */ jsx(TableHead, { children: "成交额" })
			] }) }), /* @__PURE__ */ jsx(TableBody, { children: report.ladder.map((row) => /* @__PURE__ */ jsxs(TableRow, { children: [
				/* @__PURE__ */ jsxs(TableCell, { children: [row.stock.name, /* @__PURE__ */ jsx("small", {
					className: "table-sub",
					children: row.stock.code
				})] }),
				/* @__PURE__ */ jsx(TableCell, {
					className: "numeric up",
					children: p(row.currentPct)
				}),
				/* @__PURE__ */ jsxs(TableCell, { children: [row.limitPct, "%"] }),
				/* @__PURE__ */ jsxs(TableCell, { children: [row.streak, " 天"] }),
				/* @__PURE__ */ jsx(TableCell, {
					className: "numeric",
					children: money(row.stock.amount)
				})
			] }, row.stock.code)) })] }),
			/* @__PURE__ */ jsx("h4", { children: "五、个股强弱与成交额榜" }),
			/* @__PURE__ */ jsxs("div", {
				className: "report-rank-grid",
				children: [/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("h5", { children: "涨幅领先（候选）" }), /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
					/* @__PURE__ */ jsx(TableHead, { children: "股票" }),
					/* @__PURE__ */ jsx(TableHead, { children: "涨跌" }),
					/* @__PURE__ */ jsx(TableHead, { children: "成交额" })
				] }) }), /* @__PURE__ */ jsx(TableBody, { children: (report.gainLeaders || []).map((row) => /* @__PURE__ */ jsxs(TableRow, { children: [
					/* @__PURE__ */ jsxs(TableCell, { children: [row.name, /* @__PURE__ */ jsx("small", {
						className: "table-sub",
						children: row.code
					})] }),
					/* @__PURE__ */ jsx(TableCell, {
						className: "numeric up",
						children: p(row.pct)
					}),
					/* @__PURE__ */ jsx(TableCell, {
						className: "numeric",
						children: money(row.amount)
					})
				] }, `gain-${row.code}`)) })] })] }), /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("h5", { children: "成交额领先" }), /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
					/* @__PURE__ */ jsx(TableHead, { children: "股票" }),
					/* @__PURE__ */ jsx(TableHead, { children: "涨跌" }),
					/* @__PURE__ */ jsx(TableHead, { children: "成交额" })
				] }) }), /* @__PURE__ */ jsx(TableBody, { children: (report.amountLeaders || []).map((row) => /* @__PURE__ */ jsxs(TableRow, { children: [
					/* @__PURE__ */ jsxs(TableCell, { children: [row.name, /* @__PURE__ */ jsx("small", {
						className: "table-sub",
						children: row.code
					})] }),
					/* @__PURE__ */ jsx(TableCell, {
						className: `numeric ${row.pct >= 0 ? "up" : "down"}`,
						children: p(row.pct)
					}),
					/* @__PURE__ */ jsx(TableCell, {
						className: "numeric",
						children: money(row.amount)
					})
				] }, `amount-${row.code}`)) })] })] })]
			}),
			/* @__PURE__ */ jsx("p", {
				className: "muted-copy",
				children: "榜单来自同日收盘日线；这些是“龙头候选”证据，仍需板块归属、龙虎榜和盘中行为确认。"
			}),
			/* @__PURE__ */ jsx("h4", { children: "六、负反馈与前日涨停表现（本地推导）" }),
			/* @__PURE__ */ jsxs("div", {
				className: "report-rank-grid",
				children: [/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("h5", { children: "跌幅领先（负反馈候选）" }), /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
					/* @__PURE__ */ jsx(TableHead, { children: "股票" }),
					/* @__PURE__ */ jsx(TableHead, { children: "涨跌" }),
					/* @__PURE__ */ jsx(TableHead, { children: "成交额" })
				] }) }), /* @__PURE__ */ jsx(TableBody, { children: (report.lossLeaders || []).map((row) => /* @__PURE__ */ jsxs(TableRow, { children: [
					/* @__PURE__ */ jsxs(TableCell, { children: [row.name, /* @__PURE__ */ jsx("small", {
						className: "table-sub",
						children: row.code
					})] }),
					/* @__PURE__ */ jsx(TableCell, {
						className: "numeric down",
						children: p(row.pct)
					}),
					/* @__PURE__ */ jsx(TableCell, {
						className: "numeric",
						children: money(row.amount)
					})
				] }, `loss-${row.code}`)) })] })] }), /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("h5", { children: "跌停阈值候选" }), /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
					/* @__PURE__ */ jsx(TableHead, { children: "股票" }),
					/* @__PURE__ */ jsx(TableHead, { children: "涨跌" }),
					/* @__PURE__ */ jsx(TableHead, { children: "成交额" })
				] }) }), /* @__PURE__ */ jsx(TableBody, { children: (report.limitDownCandidates || []).map((row) => /* @__PURE__ */ jsxs(TableRow, { children: [
					/* @__PURE__ */ jsxs(TableCell, { children: [row.name, /* @__PURE__ */ jsx("small", {
						className: "table-sub",
						children: row.code
					})] }),
					/* @__PURE__ */ jsx(TableCell, {
						className: "numeric down",
						children: p(row.pct)
					}),
					/* @__PURE__ */ jsx(TableCell, {
						className: "numeric",
						children: money(row.amount)
					})
				] }, `limit-down-${row.code}`)) })] })] })]
			}),
			report.priorLimitUpStats && /* @__PURE__ */ jsxs("p", {
				className: "muted-copy",
				children: [
					"前一交易日 ",
					report.priorLimitUpStats.previousDate || "—",
					" 涨停候选",
					" ",
					report.priorLimitUpStats.count || 0,
					" 只，今日平均",
					" ",
					report.priorLimitUpStats.todayAvgPct == null ? "—" : p(report.priorLimitUpStats.todayAvgPct),
					"；上涨",
					" ",
					report.priorLimitUpStats.todayUp || 0,
					" 只、下跌",
					" ",
					report.priorLimitUpStats.todayDown || 0,
					" 只、平盘",
					" ",
					report.priorLimitUpStats.todayFlat || 0,
					" 只。该指标由历史日线推导，仍需官方涨停池快照复核。"
				]
			}),
			report.intradayProxy && /* @__PURE__ */ jsxs(Fragment$1, { children: [
				/* @__PURE__ */ jsx("h4", { children: "七、盘中封板与炸板（OHLC代理）" }),
				/* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
					/* @__PURE__ */ jsx(TableHead, { children: "指标" }),
					/* @__PURE__ */ jsx(TableHead, { children: "数值" }),
					/* @__PURE__ */ jsx(TableHead, { children: "口径" })
				] }) }), /* @__PURE__ */ jsxs(TableBody, { children: [
					/* @__PURE__ */ jsxs(TableRow, { children: [
						/* @__PURE__ */ jsx(TableCell, { children: "涨停触板" }),
						/* @__PURE__ */ jsxs(TableCell, { children: [report.intradayProxy.upperHitCount, " 只"] }),
						/* @__PURE__ */ jsx(TableCell, { children: "日线最高价达到涨停阈值" })
					] }),
					/* @__PURE__ */ jsxs(TableRow, { children: [
						/* @__PURE__ */ jsx(TableCell, { children: "收盘封板" }),
						/* @__PURE__ */ jsxs(TableCell, { children: [report.intradayProxy.upperClosedCount, " 只"] }),
						/* @__PURE__ */ jsx(TableCell, { children: "触板且收盘仍在阈值" })
					] }),
					/* @__PURE__ */ jsxs(TableRow, { children: [
						/* @__PURE__ */ jsx(TableCell, { children: "触板后开板" }),
						/* @__PURE__ */ jsxs(TableCell, { children: [report.intradayProxy.openedAfterHitCount, " 只"] }),
						/* @__PURE__ */ jsx(TableCell, { children: "触板但收盘未封" })
					] }),
					/* @__PURE__ */ jsxs(TableRow, { children: [
						/* @__PURE__ */ jsx(TableCell, { children: "代理封板率" }),
						/* @__PURE__ */ jsx(TableCell, { children: report.intradayProxy.sealRatePct == null ? "—" : `${report.intradayProxy.sealRatePct.toFixed(2)}%` }),
						/* @__PURE__ */ jsx(TableCell, { children: "收盘封板 ÷ 触板" })
					] }),
					/* @__PURE__ */ jsxs(TableRow, { children: [
						/* @__PURE__ */ jsx(TableCell, { children: "代理炸板率" }),
						/* @__PURE__ */ jsx(TableCell, { children: report.intradayProxy.explosionRatePct == null ? "—" : `${report.intradayProxy.explosionRatePct.toFixed(2)}%` }),
						/* @__PURE__ */ jsx(TableCell, { children: "触板后开板 ÷ 触板" })
					] }),
					/* @__PURE__ */ jsxs(TableRow, { children: [
						/* @__PURE__ */ jsx(TableCell, { children: "同日5分钟文件" }),
						/* @__PURE__ */ jsxs(TableCell, { children: [
							report.intradayProxy.lc5CurrentDateCount,
							" / ",
							report.intradayProxy.lc5Files
						] }),
						/* @__PURE__ */ jsx(TableCell, { children: report.intradayProxy.dataFresh ? "可用于同日盘中复核" : "当前文件日期不匹配" })
					] }),
					/* @__PURE__ */ jsxs(TableRow, { children: [
						/* @__PURE__ */ jsx(TableCell, { children: "首封时刻 / 封单额" }),
						/* @__PURE__ */ jsx(TableCell, { children: "未提供" }),
						/* @__PURE__ */ jsx(TableCell, { children: "需要同日1分钟或逐笔/盘口快照" })
					] })
				] })] }),
				/* @__PURE__ */ jsx("p", {
					className: "muted-copy",
					children: "上述涨停数据由日线 high/close 复算，属于可复算代理，不等同于官方盘中封板、回封或封单数据。"
				})
			] }),
			/* @__PURE__ */ jsx("h4", { children: "八、数据充分性与缺口" }),
			/* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
				/* @__PURE__ */ jsx(TableHead, { children: "数据项" }),
				/* @__PURE__ */ jsx(TableHead, { children: "状态" }),
				/* @__PURE__ */ jsx(TableHead, { children: "当前证据" }),
				/* @__PURE__ */ jsx(TableHead, { children: "解决办法" })
			] }) }), /* @__PURE__ */ jsx(TableBody, { children: (report.availability || []).map((row) => /* @__PURE__ */ jsxs(TableRow, { children: [
				/* @__PURE__ */ jsx(TableCell, { children: /* @__PURE__ */ jsx("b", { children: row.item }) }),
				/* @__PURE__ */ jsx(TableCell, { children: /* @__PURE__ */ jsx("span", {
					className: `availability-${row.status === "可用" ? "ok" : row.status === "推导" ? "derived" : row.status === "按需" ? "ondemand" : "missing"}`,
					children: row.status
				}) }),
				/* @__PURE__ */ jsx(TableCell, { children: row.evidence }),
				/* @__PURE__ */ jsx(TableCell, { children: row.solution })
			] }, row.item)) })] }),
			/* @__PURE__ */ jsx("h4", { children: "九、风险与下一步" }),
			/* @__PURE__ */ jsxs("ul", {
				className: "report-list",
				children: [report.cautions.map((x) => /* @__PURE__ */ jsx("li", { children: x }, x)), report.actions.map((x) => /* @__PURE__ */ jsxs("li", { children: [/* @__PURE__ */ jsx("b", { children: "下一步：" }), x] }, x))]
			}),
			report.raw && /* @__PURE__ */ jsxs("details", {
				className: "report-raw",
				children: [/* @__PURE__ */ jsx("summary", { children: "查看 Harness 原始 JSON" }), /* @__PURE__ */ jsx("pre", { children: report.raw })]
			})
		]
	});
}
function WorkspacePages({ page, market, onSelect, onSelectCode, onRefreshMarket, marketRefreshing = false, marketRefreshMessage = "", watch, onWatch, navigate }) {
	const [search, setSearch] = useState(""), [group, setGroup] = useState("all"), [skill, setSkill] = useState(null), [researchCode, setResearchCode] = useState(""), [researchCodeError, setResearchCodeError] = useState(""), [theme, setTheme] = useState(0), [selectedStrategy, setSelectedStrategy] = useState("golden-ignition-v8");
	const [minPct, setMinPct] = useState("3"), [minAmount, setMinAmount] = useState("1"), [filterRan, setFilterRan] = useState(false), [filtered, setFiltered] = useState([]), [filterError, setFilterError] = useState(""), [report, setReport] = useState(() => loadReport(market.date)), [reportBusy, setReportBusy] = useState(false), [aiBusy, setAiBusy] = useState(false), [aiError, setAiError] = useState(""), [skillBusy, setSkillBusy] = useState(false), [skillOutput, setSkillOutput] = useState(""), [skillHarnessBusy, setSkillHarnessBusy] = useState(false), [skillHarnessOutput, setSkillHarnessOutput] = useState(""), [skillHarnessError, setSkillHarnessError] = useState(""), [harnessSkillId, setHarnessSkillId] = useState(""), [harnessStartedAt, setHarnessStartedAt] = useState(null), [harnessElapsed, setHarnessElapsed] = useState(0), [pageNo, setPageNo] = useState(0), [sort, setSort] = useState("gain"), [archiveRows, setArchiveRows] = useState(() => loadReportArchive().filter(shouldShowInMyReports)), [openedArchive, setOpenedArchive] = useState(null), [watchRefreshing, setWatchRefreshing] = useState(false), [watchRefreshMessage, setWatchRefreshMessage] = useState(""), [strategyRuns, setStrategyRuns] = useState({}), [strategyPrefsReady, setStrategyPrefsReady] = useState(false);
	const [singleSignalCode, setSingleSignalCode] = useState("");
	const [singleSignalBusy, setSingleSignalBusy] = useState(false);
	const [singleSignalError, setSingleSignalError] = useState("");
	const [singleSignalResult, setSingleSignalResult] = useState(null);
	const resumedStrategyIds = useRef(/* @__PURE__ */ new Set());
	const [, forceWatchRender] = useState(0);
	useEffect(() => {
		if (!openedArchive) return;
		window.requestAnimationFrame(() => {
			document.querySelector(".archive-sheet")?.scrollTo({
				top: 0,
				left: 0,
				behavior: "auto"
			});
		});
	}, [openedArchive?.id]);
	useEffect(() => {
		if (!skill) return;
		window.requestAnimationFrame(() => {
			document.querySelector(".skill-sheet")?.scrollTo({
				top: 0,
				left: 0,
				behavior: "auto"
			});
		});
	}, [skill?.id]);
	const [capitalSnapshot, setCapitalSnapshot] = useState(null);
	const [capitalHarnessOutput, setCapitalHarnessOutput] = useState("");
	const [capitalLoading, setCapitalLoading] = useState(false);
	const [capitalRefreshNonce, setCapitalRefreshNonce] = useState(0);
	const [mainlineHarnessOutput, setMainlineHarnessOutput] = useState("");
	const [mainlineHarnessLoading, setMainlineHarnessLoading] = useState(false);
	const [environmentSnapshot, setEnvironmentSnapshot] = useState(null);
	const [environmentLoading, setEnvironmentLoading] = useState(false);
	const [environmentMessage, setEnvironmentMessage] = useState("");
	const [dailyRefreshRunning, setDailyRefreshRunning] = useState(false);
	const [indexRebuildRunning, setIndexRebuildRunning] = useState(false);
	const [supplementalRefreshRunning, setSupplementalRefreshRunning] = useState(false);
	const [unifiedArchiveRunning, setUnifiedArchiveRunning] = useState(false);
	const [unifiedVerificationRunning, setUnifiedVerificationRunning] = useState(false);
	const [resourceLibraryContext, setResourceLibraryContext] = useState(null);
	useEffect(() => {
		let active = true;
		fetch(bridgeUrl("/runtime/resource-context"), { cache: "no-store" }).then((response) => response.ok ? response.json() : null).then((value) => {
			if (active && value && typeof value === "object") setResourceLibraryContext(value);
		}).catch(() => void 0);
		return () => {
			active = false;
		};
	}, []);
	useEffect(() => {
		if (page !== "capital") return;
		let active = true;
		setCapitalLoading(true);
		Promise.all([fetch(bridgeUrl("/data/public"), { cache: "no-store" }).then((response) => response.ok ? response.json() : null), fetch(bridgeUrl("/data/harness/daily"), { cache: "no-store" }).then((response) => response.ok ? response.json() : null)]).then(([snapshot, context]) => {
			if (!active) return;
			setCapitalSnapshot(snapshot);
			const output = context?.harness?.output;
			setCapitalHarnessOutput(typeof output === "string" ? output : "");
		}).catch(() => {
			if (active) {
				setCapitalSnapshot(null);
				setCapitalHarnessOutput("");
			}
		}).finally(() => {
			if (active) setCapitalLoading(false);
		});
		return () => {
			active = false;
		};
	}, [page, capitalRefreshNonce]);
	useEffect(() => {
		if (page !== "mainline") return;
		let active = true;
		setMainlineHarnessLoading(true);
		fetch(bridgeUrl("/data/harness/skill/short-term-sentiment-v22"), { cache: "no-store" }).then((response) => response.ok ? response.json() : null).then((job) => {
			if (!active) return;
			const raw = typeof job?.output === "string" ? job.output : "";
			setMainlineHarnessOutput(raw);
			if (raw && (!job?.status || job.status === "completed")) {
				const parsed = parseHarnessOutput(raw);
				const reportDate = String(parsed.dataDate || job?.date || market.date || "");
				(/* @__PURE__ */ new Date()).toISOString();
				createReportId("mainline"), `${reportDate}`, `${d(reportDate)}`, parsed.summary, parsed.dataScope || `${reportDate || "日期未提供"}`;
			}
		}).catch(() => {
			if (active) setMainlineHarnessOutput("");
		}).finally(() => {
			if (active) setMainlineHarnessLoading(false);
		});
		return () => {
			active = false;
		};
	}, [page]);
	const capitalRows = useMemo(() => normalizeCapitalRows(capitalSnapshot), [capitalSnapshot]);
	const themes = useMemo(() => buildThemes(market.stocks, market.conceptBoards || [], market.sectors || []), [
		market.stocks,
		market.conceptBoards,
		market.sectors
	]);
	const ladder = useMemo(() => buildLadder(market.stocks, market.tdxLimitUpCodes || []), [market.stocks, market.tdxLimitUpCodes]);
	const gainLeaders = useMemo(() => rankRows(market.stocks, "pct", 20), [market.stocks]);
	const amountLeaders = useMemo(() => rankRows(market.stocks, "amount", 20), [market.stocks]);
	const lossLeaders = useMemo(() => rankRows(market.stocks, "loss", 20), [market.stocks]);
	const limitDownCandidates = useMemo(() => market.tdxLimitDownCodes?.length ? market.stocks.filter((s) => market.tdxLimitDownCodes?.includes(s.code)).sort((a, b) => a.pct - b.pct).slice(0, 20).map(({ code, name, pct, amount, close, market: venue }) => ({
		code,
		name,
		pct,
		amount,
		close,
		market: venue
	})) : lossLeaders.filter((s) => s.pct < -9.5), [
		market.stocks,
		market.tdxLimitDownCodes,
		lossLeaders
	]);
	const related = skills.filter((x) => x.group === page);
	const visibleSkills = skills.filter((item) => (group === "all" || item.group === group) && `${item.name} ${item.alias} ${item.id}`.includes(search));
	const visibleSkillGroups = Object.entries(groupNames).filter(([groupId]) => visibleSkills.some((item) => item.group === groupId));
	const selectedStrategyRun = strategyRuns[selectedStrategy] || {
		busy: false,
		output: "",
		harnessOutput: "",
		status: "",
		phase: "",
		startedAt: null,
		elapsed: 0
	};
	strategyRunHasReport(selectedStrategyRun);
	const selectedStrategyHasFailure = strategyRunHasFailure(selectedStrategyRun);
	strategyCatalogItem(selectedStrategy);
	strategyDataStatus(selectedStrategy);
	const searchableStocks = useMemo(() => {
		return (market.allStocks?.length ? market.allStocks : market.stocks).filter((row) => Boolean(row.code && row.date));
	}, [market.allStocks, market.stocks]);
	const filteredStocks = useMemo(() => {
		let rows = searchableStocks.filter((x) => `${x.name} ${x.code}`.includes(search.trim()));
		if (sort === "gain") rows = [...rows].sort((a, b) => b.pct - a.pct || b.amount - a.amount);
		if (sort === "amount") rows = [...rows].sort((a, b) => b.amount - a.amount);
		if (sort === "loss") rows = [...rows].sort((a, b) => a.pct - b.pct);
		return rows;
	}, [
		searchableStocks,
		search,
		sort
	]);
	const harnessRunning = aiBusy || skillBusy || skillHarnessBusy;
	async function refreshEnvironment() {
		if (environmentLoading) return;
		setEnvironmentLoading(true);
		setEnvironmentMessage("正在检测通达信、日线文件和 DeepSeek Harness…");
		try {
			const readEnvironment = async () => {
				const response = await fetch(bridgeUrl("/runtime/environment"), { cache: "no-store" });
				const body = await response.json().catch(() => ({}));
				if (!response.ok || body.status !== "ok") throw new Error(body.error || `运行环境检测失败（${response.status}）`);
				return body;
			};
			let body;
			try {
				body = await readEnvironment();
			} catch (firstError) {
				await fetch("/api/runtime/ensure-bridge", { method: "POST" }).catch(() => void 0);
				await new Promise((resolve) => window.setTimeout(resolve, 1400));
				body = await readEnvironment().catch(() => {
					throw firstError;
				});
			}
			setEnvironmentSnapshot(body);
			const dailyState = body.dailyRefresh;
			setDailyRefreshRunning(dailyState?.status === "running");
			const indexState = body.dailyIndexInitialization;
			setIndexRebuildRunning(indexState?.status === "running");
			const archiveState = body.unifiedArchive;
			const verificationState = body.unifiedVerification;
			setUnifiedArchiveRunning(archiveState?.status === "running");
			setUnifiedVerificationRunning(verificationState?.status === "running");
			const checkedAt = typeof body.checkedAt === "string" || typeof body.checkedAt === "number" ? body.checkedAt : Date.now();
			setEnvironmentMessage(`检测完成 · ${new Date(checkedAt).toLocaleTimeString("zh-CN", { hour12: false })}`);
		} catch (error) {
			setEnvironmentMessage(error instanceof Error ? error.message : "运行环境检测失败");
		} finally {
			setEnvironmentLoading(false);
		}
	}
	async function openTongdaxin() {
		setEnvironmentMessage("正在打开通达信客户端…");
		try {
			const response = await fetch(bridgeUrl("/runtime/tdx/open"), { method: "POST" });
			const body = await response.json().catch(() => ({}));
			if (!response.ok || !["accepted", "already_open"].includes(String(body.status))) throw new Error(body.error || "打开通达信失败");
			setEnvironmentMessage(body.status === "already_open" ? "通达信已打开，请完成登录后重新检测。" : "已请求打开通达信，请完成登录后重新检测。");
			window.setTimeout(() => {
				refreshEnvironment();
			}, 2500);
		} catch (error) {
			setEnvironmentMessage(error instanceof Error ? error.message : "打开通达信失败");
		}
	}
	useEffect(() => {
		if (page !== "settings") return;
		refreshEnvironment();
	}, [page]);
	async function replenishDailyData() {
		if (dailyRefreshRunning) return;
		setDailyRefreshRunning(true);
		setEnvironmentMessage("已提交 Harness 日线补全任务：正在调用通达信并等待 DeepSeek 校验…");
		try {
			const started = await startDailyDataRefresh({ force: true });
			let status = started.state?.status || started.job?.status || "running";
			for (let attempt = 0; attempt < 180 && status === "running"; attempt += 1) {
				await new Promise((resolve) => window.setTimeout(resolve, 2e3));
				const current = await getDailyDataRefreshStatus();
				const currentState = current.state;
				const activeStep = (Array.isArray(currentState?.steps) ? currentState.steps : []).find((step) => step.status === "running");
				if (activeStep) {
					const startedAt = Date.parse(String(activeStep.startedAt || ""));
					const elapsed = Number.isFinite(startedAt) ? Math.max(0, Math.floor((Date.now() - startedAt) / 1e3)) : 0;
					const mm = String(Math.floor(elapsed / 60)).padStart(2, "0");
					const ss = String(elapsed % 60).padStart(2, "0");
					setEnvironmentMessage(`${String(activeStep.name || "日线补全")}进行中 · 已运行 ${mm}:${ss} · 通达信正在处理，完成后由 DeepSeek Harness 校验`);
				} else if (currentState?.harness && typeof currentState.harness === "object" && currentState.harness.status === "pending") setEnvironmentMessage("通达信日线步骤已结束 · 正在等待 DeepSeek Harness 校验结果");
				const latestJob = Array.isArray(current.jobs) ? current.jobs.at(-1) : void 0;
				status = String(currentState?.status || latestJob?.status || "") || status;
			}
			setEnvironmentMessage(status === "completed" ? "日线补全与 Harness 校验已完成。" : status === "partial" ? "日线补全已结束，但有步骤未完成，请查看下方状态。" : "日线补全仍在后台运行，可稍后重新检测。");
			await refreshEnvironment();
		} catch (error) {
			setEnvironmentMessage(error instanceof Error ? error.message : "日线补全启动失败");
		} finally {
			setDailyRefreshRunning(false);
		}
	}
	async function rebuildAllIndices() {
		if (indexRebuildRunning || dailyRefreshRunning) return;
		setIndexRebuildRunning(true);
		setEnvironmentMessage("已提交初始化任务：正在扫描所选通达信目录全部 .day，并重建全量个股索引；完成后复核本地 canonical 日线库…");
		try {
			const started = await startDailyIndexInitialization({ force: true });
			let status = String(started.state?.status || started.job?.status || "running");
			for (let attempt = 0; attempt < 900 && status === "running"; attempt += 1) {
				await new Promise((resolve) => window.setTimeout(resolve, 2e3));
				const current = await getDailyIndexInitializationStatus();
				const state = current.state || {};
				const activeStep = (Array.isArray(state.steps) ? state.steps : []).find((step) => step.status === "running");
				if (activeStep) {
					const startedAt = Date.parse(String(activeStep.startedAt || ""));
					const elapsed = Number.isFinite(startedAt) ? Math.max(0, Math.floor((Date.now() - startedAt) / 1e3)) : 0;
					const mm = String(Math.floor(elapsed / 60)).padStart(2, "0");
					const ss = String(elapsed % 60).padStart(2, "0");
					setEnvironmentMessage(`${String(activeStep.name || "全量索引初始化")}进行中 · 已运行 ${mm}:${ss} · 页面可继续使用`);
				}
				const latestJob = Array.isArray(current.jobs) ? current.jobs.at(-1) : void 0;
				status = String(state.status || latestJob?.status || "") || status;
			}
			setEnvironmentMessage(status === "completed" ? "初始化完成：已重建通达信股票索引和本地全历史日线定位索引。" : status === "partial" ? "初始化已完成本地全历史索引，但通达信目录存在缺口；详见下方步骤状态。" : status === "failed" ? "初始化失败：请检查通达信安装目录、磁盘空间和数据包是否完整。" : "初始化仍在后台运行，可稍后重新检测。");
			await refreshEnvironment();
		} catch (error) {
			setEnvironmentMessage(error instanceof Error ? error.message : "全量个股索引初始化启动失败");
		} finally {
			setIndexRebuildRunning(false);
		}
	}
	async function replenishSupplementalData() {
		if (supplementalRefreshRunning) return;
		setSupplementalRefreshRunning(true);
		setEnvironmentMessage("已提交 Harness 其他数据补齐任务：正在刷新公开行情、龙虎榜、涨停池和新闻…");
		try {
			const started = await startSupplementalDataRefresh({ force: true });
			let status = started.state?.status || started.job?.status || "running";
			for (let attempt = 0; attempt < 180 && status === "running"; attempt += 1) {
				await new Promise((resolve) => window.setTimeout(resolve, 2e3));
				const current = await getSupplementalDataRefreshStatus();
				const latestJob = Array.isArray(current.jobs) ? current.jobs.at(-1) : void 0;
				status = current.state?.status || String(latestJob?.status || "") || status;
			}
			setEnvironmentMessage(status === "completed" ? "其他数据补齐与 Harness 校验已完成。" : status === "partial" ? "其他数据补齐结束，但有来源未通过校验，请查看来源状态。" : "其他数据补齐仍在后台运行，可稍后重新检测。");
			await refreshEnvironment();
		} catch (error) {
			setEnvironmentMessage(error instanceof Error ? error.message : "其他数据补齐启动失败");
		} finally {
			setSupplementalRefreshRunning(false);
		}
	}
	async function archiveAllData() {
		if (unifiedArchiveRunning) return;
		setUnifiedArchiveRunning(true);
		setEnvironmentMessage("已提交统一数据落盘任务：正在汇总日线、行情、资讯、公式证据和本地来源清单…");
		try {
			const started = await startUnifiedDataArchive({ force: true });
			let status = started.state?.status || started.job?.status || "running";
			for (let attempt = 0; attempt < 180 && status === "running"; attempt += 1) {
				await new Promise((resolve) => window.setTimeout(resolve, 2e3));
				const current = await getUnifiedDataArchiveStatus();
				const currentState = current.state;
				const activeStep = (Array.isArray(currentState?.steps) ? currentState.steps : []).find((step) => step.status === "running");
				if (activeStep) setEnvironmentMessage(`统一数据落盘：${String(activeStep.name || "正在执行")} · 所有可用数据将写入 resource-library`);
				const latestJob = Array.isArray(current.jobs) ? current.jobs.at(-1) : void 0;
				status = String(currentState?.status || latestJob?.status || "") || status;
			}
			setEnvironmentMessage(status === "completed" ? "统一数据落盘已完成，来源清单已更新。" : status === "partial" ? "统一数据落盘已结束，但有来源未配置或步骤失败，请查看来源清单。" : "统一数据落盘仍在后台运行，可稍后重新检测。");
			await refreshEnvironment();
		} catch (error) {
			setEnvironmentMessage(error instanceof Error ? error.message : "统一数据落盘启动失败");
		} finally {
			setUnifiedArchiveRunning(false);
		}
	}
	async function verifyAllData() {
		if (unifiedVerificationRunning) return;
		setUnifiedVerificationRunning(true);
		setEnvironmentMessage("已提交本地数据校验任务：正在校验文件、来源清单，并调用 DeepSeek Harness…");
		try {
			const started = await startUnifiedDataVerification({ force: true });
			let status = started.state?.status || started.job?.status || "running";
			for (let attempt = 0; attempt < 180 && status === "running"; attempt += 1) {
				await new Promise((resolve) => window.setTimeout(resolve, 2e3));
				const current = await getUnifiedDataVerificationStatus();
				const currentState = current.state;
				const activeStep = (Array.isArray(currentState?.steps) ? currentState.steps : []).find((step) => step.status === "running");
				if (activeStep) setEnvironmentMessage(`本地数据校验：${String(activeStep.name || "正在执行")} · 完成后写入校验回执`);
				const latestJob = Array.isArray(current.jobs) ? current.jobs.at(-1) : void 0;
				status = String(currentState?.status || latestJob?.status || "") || status;
			}
			setEnvironmentMessage(status === "completed" ? "本地数据校验与 Harness 复核已完成。" : status === "partial" ? "本地数据校验完成，但有来源或 Harness 未通过，请查看校验回执。" : "本地数据校验仍在后台运行，可稍后重新检测。");
			await refreshEnvironment();
		} catch (error) {
			setEnvironmentMessage(error instanceof Error ? error.message : "本地数据校验启动失败");
		} finally {
			setUnifiedVerificationRunning(false);
		}
	}
	async function refreshWatchlist() {
		if (watchRefreshing || !watch.length) return;
		setWatchRefreshing(true);
		setWatchRefreshMessage("正在读取自选股实时行情…");
		try {
			const response = await fetch(bridgeUrl(`/market?scope=watchlist&codes=${encodeURIComponent(watch.join(","))}`), { cache: "no-store" });
			const body = await response.json().catch(() => ({}));
			if (!response.ok || body.status !== "ok") throw new Error(body.error || `自选行情服务返回 ${response.status}`);
			const updates = new Map((body.stocks || []).map((row) => [row.code, row]));
			const merge = (rows) => rows.map((row) => updates.has(row.code) ? {
				...row,
				...updates.get(row.code)
			} : row);
			market.stocks = merge(market.stocks);
			if (market.allStocks) market.allStocks = merge(market.allStocks);
			forceWatchRender((v) => v + 1);
			setWatchRefreshMessage(`已刷新 ${updates.size} 只自选股 · ${new Date(body.fetchedAt || Date.now()).toLocaleTimeString("zh-CN", { hour12: false })}`);
		} catch (error) {
			setWatchRefreshMessage(error instanceof Error ? error.message : "自选股刷新失败");
		} finally {
			setWatchRefreshing(false);
		}
	}
	useEffect(() => {
		const refresh = () => setArchiveRows(loadReportArchive().filter(shouldShowInMyReports));
		loadReportArchiveFromLocalRuntime().then((reports) => {
			if (reports.length) setArchiveRows(reports.filter(shouldShowInMyReports));
		});
		const migratedKey = `zhangcai.report.archive.migrated.${market.date}`;
		const legacy = loadReport(market.date);
		if (legacy && !localStorage.getItem(migratedKey)) {
			(/* @__PURE__ */ new Date()).toISOString();
			createReportId("legacy-market"), legacy.date, legacy.title, legacy.generatedBy, legacy.summary, `${legacy.source}${legacy.scope}`, legacy.raw;
			localStorage.setItem(migratedKey, "1");
		}
		refresh();
		window.addEventListener(reportArchiveChangedEvent, refresh);
		return () => window.removeEventListener(reportArchiveChangedEvent, refresh);
	}, [market.date]);
	useEffect(() => {
		if (!harnessStartedAt) return;
		const tick = () => setHarnessElapsed(Math.max(0, Math.floor((Date.now() - harnessStartedAt) / 1e3)));
		tick();
		const timer = window.setInterval(tick, 1e3);
		return () => window.clearInterval(timer);
	}, [harnessStartedAt]);
	useEffect(() => {
		const timer = window.setInterval(() => {
			const now = Date.now();
			setStrategyRuns((previous) => {
				const next = { ...previous };
				for (const [id, run] of Object.entries(next)) if (run.busy && run.startedAt) next[id] = {
					...run,
					elapsed: Math.max(0, Math.floor((now - run.startedAt) / 1e3))
				};
				return next;
			});
		}, 1e3);
		return () => window.clearInterval(timer);
	}, []);
	useEffect(() => {
		try {
			const currentDate = String(market.date || "").replace(/\D/g, "").slice(0, 8);
			const savedRuns = loadStrategyRuns();
			setStrategyRuns(Object.fromEntries(Object.entries(savedRuns).filter(([, run]) => {
				if (run.busy || !currentDate) return true;
				const runDate = strategyRunDataDate(run);
				return !runDate || runDate === currentDate;
			})));
			const saved = localStorage.getItem(selectedStrategyKey) || "";
			if (skills.some((item) => item.id === saved)) setSelectedStrategy(saved);
		} catch {}
		setStrategyPrefsReady(true);
	}, []);
	useEffect(() => {
		if (!strategyPrefsReady) return;
		try {
			localStorage.setItem(strategyRunsKey, JSON.stringify(strategyRuns));
		} catch {}
	}, [strategyRuns, strategyPrefsReady]);
	useEffect(() => {
		if (!strategyPrefsReady) return;
		try {
			localStorage.setItem(selectedStrategyKey, selectedStrategy);
		} catch {}
	}, [selectedStrategy, strategyPrefsReady]);
	function beginHarness(skillId) {
		setHarnessSkillId(skillId);
		setHarnessStartedAt(Date.now());
		setHarnessElapsed(0);
	}
	function endHarness() {
		setHarnessSkillId("");
		setHarnessStartedAt(null);
		setHarnessElapsed(0);
	}
	async function archiveMarketReport(value, reportType, archiveKey = "market-review") {
		const now = (/* @__PURE__ */ new Date()).toISOString();
		await saveReportArchive({
			id: createReportId("market"),
			archiveKey,
			createdAt: now,
			updatedAt: now,
			date: value.date,
			title: value.title,
			reportType,
			generatedBy: value.generatedBy,
			summary: value.summary,
			dataScope: `${value.source} · ${value.scope}`,
			content: {
				kind: "market-report",
				report: value
			},
			raw: value.raw
		});
	}
	function harnessProgress() {
		if (!harnessRunning || !harnessStartedAt) return null;
		const expected = estimateSeconds(harnessSkillId);
		const overdue = harnessElapsed > expected;
		return /* @__PURE__ */ jsxs("div", {
			className: `harness-progress ${overdue ? "overdue" : ""}`,
			role: "status",
			children: [/* @__PURE__ */ jsx(LoaderCircle, {
				className: "spin",
				size: 15
			}), /* @__PURE__ */ jsxs("span", { children: [
				harnessSkillId || "morning-intelligence-plan",
				" 运行中 · 已运行 ",
				formatDuration(harnessElapsed),
				" · 预计 ",
				formatDuration(expected),
				overdue ? " · 已超过预计时间，仍在等待 Harness 返回" : ""
			] })]
		});
	}
	useEffect(() => {
		if (page === "reports") setReport(loadReport(market.date));
	}, [page, market.date]);
	useEffect(() => {
		if (report) localStorage.setItem(reportKey(market.date), JSON.stringify(report));
	}, [report, market.date]);
	useEffect(() => {
		if (!report) return;
		const current = makeBaseReport(market, themes, ladder);
		const dataCorrection = `数据校正：本报告已提供 ${current.gainLeaders.length} 条当日涨幅榜、${current.amountLeaders.length} 条成交额榜、${current.ladder.length} 条 TDX 涨停/连板候选；其余 ${current.availability.filter((x) => x.status === "缺失").length} 项数据缺口已在下表逐项列出，因此当前结论仍标为“龙头候选”。`;
		if ((report.availability || []).length < current.availability.length || (report.gainLeaders || []).length === 0 || (report.amountLeaders || []).length === 0 || (report.lossLeaders || []).length === 0 || (report.limitDownCandidates || []).length === 0 || !Array.isArray(report.sectors) || !Array.isArray(report.conceptBoards) || !report.intradayProxy || (report.amountLeaders || []).some((value) => value.name === "北证50") || !(report.summary || "").includes("结论仍标为“龙头候选”") || (report.cautions || []).some((value) => /不含行业、板块及个股明细|缺少行业\/板块涨跌幅/.test(value))) setReport({
			...report,
			metrics: current.metrics,
			indices: current.indices,
			themes: current.themes,
			gainLeaders: current.gainLeaders,
			amountLeaders: current.amountLeaders,
			lossLeaders: current.lossLeaders,
			limitDownCandidates: current.limitDownCandidates,
			priorLimitUpStats: current.priorLimitUpStats,
			sectors: current.sectors,
			conceptBoards: current.conceptBoards,
			intradayProxy: current.intradayProxy,
			availability: current.availability,
			ladder: current.ladder,
			summary: `${current.summary} ${dataCorrection}`,
			cautions: current.cautions,
			actions: current.actions
		});
	}, [
		report,
		market,
		themes,
		ladder
	]);
	const openById = (id) => setSkill(skills.find((x) => x.id === id) || null);
	const marketPayload = {
		date: market.date,
		currentCount: market.currentCount,
		up: market.up,
		down: market.down,
		flat: market.flat,
		amount: market.amount,
		indices: market.indices.map((x) => ({
			name: x.name,
			close: x.close,
			pct: x.pct
		})),
		gainLeaders,
		amountLeaders,
		lossLeaders,
		limitDownCandidates,
		priorLimitUpStats: market.priorLimitUpStats,
		sectors: market.sectors || [],
		conceptBoards: market.conceptBoards || [],
		intradayProxy: market.intradayProxy,
		dataSources: market.dataSources || {},
		supplemental: market.supplemental,
		limitCandidates: ladder.slice(0, 30).map((x) => ({
			code: x.stock.code,
			name: x.stock.name,
			pct: x.currentPct,
			limitPct: x.limitPct,
			streak: x.streak,
			amount: x.stock.amount
		})),
		themes: themes.map((x) => ({
			name: x.name,
			tag: x.tag,
			count: x.count,
			avgPct: Number(x.avgPct.toFixed(2)),
			amount: x.amount,
			leaders: x.leaders.map((s) => s.name)
		})),
		tdxLimitUpSource: market.tdxLimitUpFiles || []
	};
	async function callHarness(task, skillId = "morning-intelligence-plan", _context, label = skillId) {
		let latestResourceLibrary = resourceLibraryContext || {};
		try {
			const response = await fetch(bridgeUrl("/runtime/resource-context"), { cache: "no-store" });
			if (response.ok) {
				latestResourceLibrary = await response.json();
				setResourceLibraryContext(latestResourceLibrary);
			}
		} catch {}
		return (await runHarnessInBackground({
			task,
			skillId,
			label,
			market: marketPayload,
			context: _context && typeof _context === "object" ? {
				..._context,
				resourceLibrary: latestResourceLibrary
			} : { resourceLibrary: latestResourceLibrary },
			originPage: page,
			expectedSeconds: estimateSeconds(skillId)
		})).output;
	}
	const strategyHarnessPrompt = (name) => `请把“${name}”原始策略结果整理成简短网页报告，直接给出类似 Top10 选股列表的结构化结果。只返回一个严格 JSON 对象：status、summary、data_date、data_scope、cautions、findings、tables。tables 只保留一张“Top 候选”表，最多 10 行，列为排名、代码、名称、评分、波段、游资、机构、风险；如果没有候选，表格 rows 为空并在 cautions 说明原因。summary 不超过 80 字，findings 最多 3 条，每条不超过 50 字。只引用原始交付物和本地行情，不虚构结论。${HARNESS_JSON_SCHEMA}`;
	const selectionHarnessPrompt = (name, preflightStatus, scoreReceipt) => {
		const columns = name.includes("V6.5") ? "排名、代码、名称、评分、波段、主模型、游资、机构、风险" : "排名、代码、名称、评分、波段、游资、机构、风险";
		return `请对“${name}”完成策略选股网页分析。当前网页预检状态为 ${preflightStatus}，并已调用对应原始策略评分引擎完成本地数值回执。候选数组中的 score、wave、primary_model、primary_model_candidate、youzi、institution、risk 来自原始策略评分字段的网页适配展示；不得用涨幅、成交额、候选排名或 TDX 五公式复合分替代 score。必须原样引用 score_source、strategy_score_status、strategy_missing 和 strategy_fields 中能支持的字段。评分回执的 score_status=${scoreReceipt?.score_status || "未知"}；缺失项=${(scoreReceipt?.missing || []).join("、") || "无"}。若 score_status 为 DEGRADED，只能称为本地降级研究评分，必须在 cautions 写出缺失项；若为 BLOCKED，不得把候选表写成已执行策略结果。请严格基于传入的本地行情、原始评分回执、条件候选和预检结果输出分析。只返回一个严格 JSON 对象：status、summary、data_date、data_scope、cautions、findings、tables。tables 只保留一张“Top 候选”表，最多 10 行，列为${columns}；候选不足时 rows 为空并在 cautions 说明原因。summary 不超过 80 字，findings 最多 3 条，每条不超过 50 字。只读研究，不给出买卖建议，不虚构未传入的数据。${HARNESS_JSON_SCHEMA}`;
	};
	async function resumeStrategyAfterRefresh(target, run, rawTask, harnessTask) {
		const startedAt = run.startedAt || rawTask.startedAt || Date.now();
		let strategyOutput = run.output || rawTask.output || "";
		let strategyStructured = run.structured || (rawTask.structured && typeof rawTask.structured === "object" ? rawTask.structured : null);
		let strategyStatus = run.status || rawTask.strategyStatus || "UNKNOWN";
		let receipt = run.receipt || (rawTask.receipt && typeof rawTask.receipt === "object" ? rawTask.receipt : null);
		try {
			setStrategyRuns((previous) => ({
				...previous,
				[target.id]: {
					...previous[target.id],
					busy: true,
					phase: rawTask.status === "completed" ? "harness" : "strategy",
					startedAt,
					elapsed: Math.floor((Date.now() - startedAt) / 1e3)
				}
			}));
			if (rawTask.status !== "completed") {
				const result = await resumeHarnessTask(rawTask);
				strategyOutput = result.output || strategyOutput;
				strategyStructured = result.structured && typeof result.structured === "object" ? result.structured : strategyStructured;
				strategyStatus = result.status || strategyStatus;
				receipt = result.receipt && typeof result.receipt === "object" ? result.receipt : receipt;
			}
			if (!strategyOutput) throw new Error("原始策略已恢复，但没有可供 Harness 解读的交付物");
			setStrategyRuns((previous) => ({
				...previous,
				[target.id]: {
					...previous[target.id],
					busy: true,
					output: strategyOutput,
					status: strategyStatus,
					phase: "harness",
					structured: strategyStructured,
					receipt,
					startedAt,
					elapsed: Math.floor((Date.now() - startedAt) / 1e3)
				}
			}));
			let harnessOutput = run.harnessOutput || "";
			if (harnessTask && harnessTask.status !== "completed") harnessOutput = (await resumeHarnessTask(harnessTask)).output;
			else if (!harnessOutput) harnessOutput = await callHarness(strategyHarnessPrompt(target.name), target.id, {
				strategy_status: strategyStatus,
				strategy_output: strategyOutput,
				strategy_delivery: strategyStructured
			}, `${target.name} · Harness 解读`);
			setStrategyRuns((previous) => ({
				...previous,
				[target.id]: {
					...previous[target.id],
					busy: false,
					output: strategyOutput,
					harnessOutput,
					status: "CLEAN_PASS",
					phase: "completed",
					structured: strategyStructured,
					receipt,
					startedAt: null,
					elapsed: Math.floor((Date.now() - startedAt) / 1e3)
				}
			}));
			const now = (/* @__PURE__ */ new Date()).toISOString();
			await saveReportArchive({
				id: `strategy-${target.id}-${Date.now()}`,
				archiveKey: `strategy:${target.id}:${market.date}`,
				createdAt: now,
				updatedAt: now,
				date: market.date,
				title: `掌财智能体 · ${target.name} · 策略运行报告`,
				reportType: "策略运行",
				generatedBy: "网页脚本 + DeepSeek Harness",
				summary: "刷新后已恢复原始策略与 Harness 解读，结构化报告已生成",
				dataScope: `本地日线归档 · ${d(market.date)} · 已恢复后台交付物`,
				content: {
					kind: "strategy-run",
					strategyId: target.id,
					status: "CLEAN_PASS",
					receipt,
					structured: strategyStructured,
					harnessOutput
				},
				raw: harnessOutput
			});
		} catch (error) {
			const message = error instanceof Error ? error.message : "刷新后恢复策略失败";
			setStrategyRuns((previous) => ({
				...previous,
				[target.id]: {
					...previous[target.id],
					busy: false,
					output: strategyOutput || message,
					harnessOutput: run.harnessOutput || "",
					status: "ERROR",
					phase: "resume_error",
					structured: strategyStructured,
					receipt,
					startedAt: null,
					elapsed: Math.floor((Date.now() - startedAt) / 1e3)
				}
			}));
			setAiError(`${target.name} 刷新后恢复失败：${message}`);
		}
	}
	useEffect(() => {
		if (!strategyPrefsReady || page !== "selection") return;
		const tasks = getHarnessTasks();
		setStrategyRuns((previous) => {
			let changed = false;
			const next = { ...previous };
			for (const [strategyId, run] of Object.entries(previous)) {
				if (!run.busy) continue;
				const target = skills.find((item) => item.id === strategyId);
				if (!target) continue;
				const after = (run.startedAt || 0) - 5e3;
				if ([...tasks.filter((task) => task.skillId === strategyId && task.originPage === "selection" && task.startedAt >= after)].reverse().find((task) => task.backendKind === "strategy" && task.label === `策略 · ${target.name}`)) continue;
				changed = true;
				next[strategyId] = {
					...run,
					busy: false,
					phase: run.harnessOutput || run.structured ? "completed" : "resume_error",
					status: run.harnessOutput || run.structured ? "CLEAN_PASS" : "ERROR",
					startedAt: null
				};
			}
			return changed ? next : previous;
		});
		for (const [strategyId, run] of Object.entries(strategyRuns)) {
			if (!run.busy || resumedStrategyIds.current.has(strategyId)) continue;
			const target = skills.find((item) => item.id === strategyId);
			if (!target) continue;
			const after = (run.startedAt || 0) - 5e3;
			const matches = tasks.filter((task) => task.skillId === strategyId && task.originPage === "selection" && task.startedAt >= after);
			const rawTask = [...matches].reverse().find((task) => task.backendKind === "strategy" && task.label === `策略 · ${target.name}`);
			if (!rawTask) continue;
			const harnessTask = [...matches].reverse().find((task) => task.backendKind === "harness" && task.label === `${target.name} · Harness 解读`);
			resumedStrategyIds.current.add(strategyId);
			resumeStrategyAfterRefresh(target, run, rawTask, harnessTask);
		}
	}, [page, strategyPrefsReady]);
	async function makeHarnessReport(skillId = "morning-intelligence-plan", context) {
		setAiBusy(true);
		beginHarness(skillId);
		setAiError("");
		try {
			const raw = await callHarness(`请按照技能职责完成当日A股研究复盘。${HARNESS_JSON_SCHEMA}不得给出买卖建议，不得虚构新闻、龙虎榜或实时数据。`, skillId, context);
			const base = makeBaseReport(market, themes, ladder);
			const parsed = parseHarnessOutput(raw);
			const modelCautions = parsed.cautions.filter((value) => !/不含.*个股|缺少.*(涨跌幅|成交额|涨跌停|连板)/.test(value));
			const modelSummary = String(parsed.summary || raw).replace(/本输出不含任何个股或板块结论[。；]?/g, "").replace(/缺少涨停\/连板梯队、板块涨幅榜和个股成交额榜[。；]?/g, "").trim();
			const candidateNote = `候选提示：当日涨幅领先为 ${base.gainLeaders.slice(0, 3).map((x) => `${x.name} ${p(x.pct)}`).join("、")}；连续候选最高为 ${base.ladder.slice(0, 3).map((x) => `${x.stock.name} ${x.streak}板`).join("、")}。这些是日线候选，不是已核实龙头。`;
			const dataCorrection = `数据校正：本报告已提供 ${base.gainLeaders.length} 条当日涨幅榜、${base.amountLeaders.length} 条成交额榜、${base.ladder.length} 条 TDX 涨停/连板候选；其余 ${base.availability.filter((x) => x.status === "缺失").length} 项数据缺口已在下表逐项列出，因此当前结论仍标为“龙头候选”。 ${candidateNote}`;
			const rendered = buildAiPresentation(raw, base, "DeepSeek Harness 复盘");
			if (skillId === "short-term-sentiment-v22") setMainlineHarnessOutput(raw);
			const nextReport = {
				...base,
				generatedBy: `DeepSeek Harness · ${skillId}`,
				summary: `${modelSummary || base.summary} ${dataCorrection}`,
				cautions: [...modelCautions, ...base.cautions].filter((value, index, values) => values.indexOf(value) === index),
				raw,
				aiPresentation: rendered.presentation
			};
			setReport(nextReport);
			const reportDate = String(parsed.dataDate || base.date || market.date || "");
			await archiveMarketReport(nextReport, "Harness 复盘", skillId === "short-term-sentiment-v22" ? `mainline:${reportDate}:short-term-sentiment-v22` : `market:${reportDate}:${skillId}`);
		} catch (error) {
			setAiError(error instanceof Error ? error.message : "DeepSeek Harness 调用失败");
		} finally {
			setAiBusy(false);
			endHarness();
		}
	}
	async function fetchSkillPreflight(target) {
		const response = await fetch(bridgeUrl("/skill14/preflight"), {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ skillId: target.id })
		});
		const result = await response.json().catch(() => ({}));
		if (!response.ok) throw new Error(result.error || `本地预检服务返回异常（${response.status}）`);
		return result;
	}
	function formatSkillPreflight(target, result) {
		const missingRequired = Array.isArray(result.required_missing) && result.required_missing.length ? result.required_missing.join("、") : "无";
		const degraded = Array.isArray(result.degraded_missing) ? result.degraded_missing : [];
		const missingOptionalValues = [...Array.isArray(result.optional_missing) ? result.optional_missing : [], ...degraded];
		const missingOptional = missingOptionalValues.length ? missingOptionalValues.join("、") : "无";
		const minute = result.minute_data;
		return [
			`${target.name} · 本地数据预检`,
			`状态：${result.status || "未知"}`,
			`缺少必需数据：${missingRequired}`,
			`缺少可降级数据：${missingOptional}`,
			`5 分钟线：${minute?.requirement === "not_required" || !minute ? "普通任务不依赖，未写入 EXE" : `${minute.status === "available" ? "外部可按需读取" : "未发现，已降级"} · ${minute.purpose || "仅用于分钟级特征"}`}`,
			`规则：${result.degrade_policy || target.note}`,
			`说明：${result.execution_note || "预检回执已写入应用数据目录。"}`
		].join("\n");
	}
	async function runSkill(target) {
		setSkillBusy(true);
		setSkillOutput("");
		try {
			setSkillOutput(formatSkillPreflight(target, await fetchSkillPreflight(target)));
		} catch (error) {
			setSkillOutput(error instanceof Error ? error.message : "本地数据预检失败");
		} finally {
			setSkillBusy(false);
		}
	}
	async function runSkillHarness(target) {
		if (skillHarnessBusy) return;
		setSkillHarnessBusy(true);
		setSkillHarnessOutput("");
		setSkillHarnessError("");
		beginHarness(target.id);
		let preflight = { status: "PREFLIGHT_UNAVAILABLE" };
		try {
			try {
				preflight = await fetchSkillPreflight(target);
				setSkillOutput(formatSkillPreflight(target, preflight));
			} catch (error) {
				preflight = {
					status: "PREFLIGHT_UNAVAILABLE",
					error: error instanceof Error ? error.message : "本地预检失败"
				};
				setSkillOutput(`${target.name} · 本地预检未完成\n${String(preflight.error)}`);
			}
			const catalog = skill14_catalog_default.skills.find((item) => item.id === target.id);
			const raw = await callHarness(`请加载并执行电脑版技能“${target.name}”（技能 ID：${target.id}）的网页适配任务。先核对随附的本地预检结果，再严格按照技能包的职责、依赖和降级规则输出结果。预检为 BLOCKED 时只能输出阻塞诊断和补数清单，不得生成正式结论；预检为 DEGRADED 时必须明确标记降级范围。只读研究，不给出买卖建议，不得虚构未传入的行情、新闻、公告、龙虎榜或公式结果。${HARNESS_JSON_SCHEMA}`, target.id, {
				skill: catalog || {
					id: target.id,
					name: target.name,
					dependencies: target.dependencies,
					note: target.note
				},
				preflight,
				request: {
					page: "skills",
					date: market.date
				}
			}, `${target.name} · Harness`);
			setSkillHarnessOutput(raw);
			const parsed = normalizeHarnessOutput(raw);
			const now = (/* @__PURE__ */ new Date()).toISOString();
			await saveReportArchive({
				id: createReportId("skill14-harness"),
				archiveKey: `skill14:${target.id}:${market.date}`,
				createdAt: now,
				updatedAt: now,
				date: market.date,
				title: `${target.name} · Harness 报告 · ${d(market.date)}`,
				reportType: "14技能 Harness",
				generatedBy: `DeepSeek Harness · ${target.id}`,
				summary: parsed.summary || `${target.name} Harness 结果已生成。`,
				dataScope: parsed.dataScope || `本地行情快照 · ${d(market.date)} · 14 技能适配`,
				content: {
					kind: "harness-skill",
					skillId: target.id,
					skillName: target.name,
					preflight,
					raw
				},
				raw
			});
		} catch (error) {
			setSkillHarnessError(error instanceof Error ? error.message : "Harness 调用失败");
		} finally {
			setSkillHarnessBusy(false);
			endHarness();
		}
	}
	function makeLocalReport() {
		setReportBusy(true);
		window.setTimeout(() => {
			const nextReport = makeBaseReport(market, themes, ladder);
			setReport(nextReport);
			archiveMarketReport(nextReport, "结构化复盘");
			setReportBusy(false);
		}, 180);
	}
	function runFilter() {
		const g = Number(minPct), a = Number(minAmount);
		if (!minPct.trim() || !minAmount.trim() || !Number.isFinite(g) || !Number.isFinite(a) || g < -100 || g > 100 || a < 0) {
			setFilterError("请输入有效条件：涨幅 -100 至 100，成交额不小于 0。");
			return;
		}
		setFilterError("");
		setFiltered(market.stocks.filter((s) => s.pct >= g && s.amount >= a * 1e8));
		setFilterRan(true);
	}
	async function runSingleGoldenIgnition() {
		const digits = singleSignalCode.trim().replace(/\D/g, "").slice(0, 6);
		if (!/^\d{6}$/.test(digits)) {
			setSingleSignalError("请输入 6 位股票代码，例如 300563。");
			setSingleSignalResult(null);
			return;
		}
		if (singleSignalBusy) return;
		setSingleSignalBusy(true);
		setSingleSignalError("");
		setSingleSignalResult(null);
		try {
			const response = await fetch(bridgeUrl("/strategy/golden-ignition/single"), {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					symbol: digits,
					lookback: 5
				})
			});
			const body = await response.json().catch(() => ({}));
			if (!response.ok) throw new Error(body.error || `单股黄金点火服务返回 ${response.status}`);
			setSingleSignalResult(body);
			const resultDate = String(body.latest_trading_date || market.date || "").replace(/\D/g, "").slice(0, 8);
			const now = (/* @__PURE__ */ new Date()).toISOString();
			await saveReportArchive({
				id: `golden-ignition-single-${digits}-${Date.now()}`,
				archiveKey: `golden:${digits}:${resultDate || market.date}`,
				createdAt: now,
				updatedAt: now,
				date: resultDate || market.date,
				title: `黄金点火 · ${digits} · 单股执行信号`,
				reportType: "黄金点火单股信号",
				generatedBy: "黄金点火本地业务入口",
				summary: `${body.signal_status === "HIT" ? "命中点火信号" : "未触发点火信号"} · ${body.analysis_symbol || digits}`,
				dataScope: `通达信本地日线 · ${d(body.latest_trading_date || market.date)} · 黄金点火AI`,
				content: {
					kind: "golden-ignition-single-signal",
					result: body
				},
				raw: JSON.stringify(body, null, 2)
			});
		} catch (error) {
			setSingleSignalError(error instanceof Error ? error.message : "单股黄金点火执行失败");
		} finally {
			setSingleSignalBusy(false);
		}
	}
	async function runSelectedStrategy() {
		const target = skills.find((item) => item.id === selectedStrategy);
		runFilter();
		if (!target || strategyRuns[target.id]?.busy) return;
		const startedAt = Date.now();
		setStrategyRuns((previous) => ({
			...previous,
			[target.id]: {
				busy: true,
				output: "",
				harnessOutput: "",
				status: "RUNNING",
				phase: "preflight",
				startedAt,
				elapsed: 0,
				structured: null
			}
		}));
		try {
			const response = await fetch(bridgeUrl("/skill14/preflight"), {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ skillId: target.id })
			});
			const result = await response.json().catch(() => ({}));
			if (!response.ok) throw new Error(result.error || "本地预检服务返回异常");
			const missingRequired = Array.isArray(result.required_missing) && result.required_missing.length ? result.required_missing.join("、") : "无";
			const missingOptional = Array.isArray(result.optional_missing) && result.optional_missing.length ? result.optional_missing.join("、") : "无";
			const output = [
				`${target.name} · 本地数据预检`,
				`状态：${result.status || "未知"}`,
				`缺少必需数据：${missingRequired}`,
				`缺少可降级数据：${missingOptional}`,
				`规则：${result.degrade_policy || target.note}`,
				"说明：已调用对应原始策略评分引擎完成本地数值回执；Harness 负责基于同一份回执解释结果、列出缺失项与风险边界，不生成买卖建议。"
			].join("\n");
			const filterPct = Number(minPct);
			const filterAmount = Number(minAmount);
			const candidatePool = (market.allStocks?.length ? market.allStocks : market.stocks).filter((stock) => stock.pct >= filterPct && stock.amount >= filterAmount * 1e8).filter((stock) => !market.date || !stock.date || String(stock.date) === String(market.date)).sort((a, b) => b.pct - a.pct || b.amount - a.amount).slice(0, 30);
			const scoreResponse = await fetch(bridgeUrl("/strategy/selection/scored"), {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					strategyId: target.id,
					date: market.date,
					candidates: candidatePool
				}),
				cache: "no-store"
			});
			const scoreReceipt = await scoreResponse.json().catch(() => ({}));
			if (!scoreResponse.ok || scoreReceipt.status !== "ok") throw new Error(scoreReceipt.error || `原始策略评分服务返回 ${scoreResponse.status}`);
			const scoreMap = new Map((Array.isArray(scoreReceipt.results) ? scoreReceipt.results : []).map((item) => [String(item.code || ""), item]));
			const localCandidates = candidatePool.map((stock) => strategyScoreCandidate(stock, scoreMap.get(stock.code), target.id, scoreReceipt)).sort((a, b) => {
				if (target.id === "quant-production-v65") {
					const priority = (candidate) => {
						const fields = candidate.strategy_fields || {};
						const labels = Array.isArray(fields.model_labels) ? fields.model_labels.length : 0;
						const core = (fields.model_states && typeof fields.model_states === "object" ? Object.values(fields.model_states) : []).some((state) => state && typeof state === "object" && state.core === true);
						return labels > 0 ? 2 : core ? 1 : 0;
					};
					return priority(b) - priority(a) || b.score - a.score || b.pct - a.pct || b.amount - a.amount;
				}
				return b.score - a.score || b.pct - a.pct || b.amount - a.amount;
			}).slice(0, 10);
			const scoreStatus = String(scoreReceipt.score_status || "UNKNOWN");
			const scoreMissing = Array.isArray(scoreReceipt.missing) && scoreReceipt.missing.length ? scoreReceipt.missing.join("、") : "无";
			setStrategyRuns((previous) => ({
				...previous,
				[target.id]: {
					...previous[target.id],
					busy: true,
					output: `${output}\n原始评分：${scoreStatus} · 已评分 ${scoreReceipt.candidate_count || localCandidates.length} 只\n评分缺失：${scoreMissing}`,
					harnessOutput: "",
					status: String(result.status || "UNKNOWN"),
					phase: "formula",
					startedAt,
					elapsed: Math.floor((Date.now() - startedAt) / 1e3),
					structured: null,
					receipt: {
						...result,
						scoring: scoreReceipt
					}
				}
			}));
			setStrategyRuns((previous) => ({
				...previous,
				[target.id]: {
					...previous[target.id],
					phase: "harness",
					elapsed: Math.floor((Date.now() - startedAt) / 1e3)
				}
			}));
			const harnessOutput = reconcileSelectionHarnessOutput(await callHarness(selectionHarnessPrompt(target.name, String(result.status || "UNKNOWN"), scoreReceipt), target.id, {
				page: "selection",
				filters: {
					minPct: filterPct,
					minAmountYi: filterAmount
				},
				preflight: result,
				strategy_score: {
					status: scoreStatus,
					missing: scoreReceipt.missing || [],
					source: scoreReceipt.score_source || "embedded_original_engine",
					artifact_path: scoreReceipt.artifact_path || ""
				},
				candidates: localCandidates
			}, `${target.name} · Harness 分析`), localCandidates, market.date, scoreReceipt);
			const parsed = normalizeHarnessOutput(harnessOutput);
			const now = (/* @__PURE__ */ new Date()).toISOString();
			setStrategyRuns((previous) => ({
				...previous,
				[target.id]: {
					...previous[target.id],
					busy: false,
					output,
					harnessOutput,
					status: parsed.status || "COMPLETED",
					phase: "completed",
					startedAt: null,
					elapsed: Math.floor((Date.now() - startedAt) / 1e3),
					structured: null,
					receipt: {
						...result,
						scoring: scoreReceipt
					}
				}
			}));
			await saveReportArchive({
				id: `strategy-harness-${target.id}-${Date.now()}`,
				archiveKey: `strategy:${target.id}:${market.date}`,
				createdAt: now,
				updatedAt: now,
				date: market.date,
				title: `掌财智能体 · ${target.name} · Harness 分析`,
				reportType: "策略选股 Harness",
				generatedBy: `DeepSeek Harness · ${target.id}`,
				summary: parsed.summary || `${target.name} 的本地预检与 Harness 分析已完成。`,
				dataScope: `本地行情快照 · ${d(market.date)} · 条件候选 ${localCandidates.length} 只`,
				content: {
					kind: "strategy-selection-harness",
					strategyId: target.id,
					preflight: result,
					scoring: scoreReceipt,
					filters: {
						minPct: filterPct,
						minAmountYi: filterAmount
					},
					candidates: localCandidates,
					harnessOutput
				},
				raw: harnessOutput
			});
		} catch (error) {
			const message = error instanceof Error ? error.message : "本地数据预检失败";
			setStrategyRuns((previous) => ({
				...previous,
				[target.id]: {
					...previous[target.id],
					busy: false,
					output: previous[target.id]?.output || message,
					harnessOutput: previous[target.id]?.harnessOutput || "",
					status: "ERROR",
					phase: ["formula", "harness"].includes(previous[target.id]?.phase || "") ? `${previous[target.id]?.phase}_error` : "strategy_error",
					startedAt: null,
					elapsed: Math.floor((Date.now() - startedAt) / 1e3),
					structured: null
				}
			}));
		}
	}
	function download() {
		if (!report) return;
		const text = [
			`# ${report.title}`,
			`生成方式：${report.generatedBy}`,
			`数据来源：${report.source}`,
			"",
			report.summary,
			"",
			"## 市场概况",
			...report.metrics.map((x) => `- ${x.label}：${x.value}（${x.detail}）`),
			"",
			"## 主线候选",
			...report.themes.map((x) => `- ${x.name}：${x.count}只，平均${p(x.avgPct)}，代表股${x.leaders.map((s) => s.name).join("、")}`),
			"",
			"## TDX行业板块涨幅榜",
			...(report.sectors || []).slice(0, 12).map((x, i) => `${i + 1}. ${x.name}（${x.code}）${x.count}只，平均${p(x.avgPct)}，成交额${money(x.amount)}，涨停${x.limitCount || 0}只，代表股${(x.leaders || []).map((s) => s.name).join("、")}`),
			"",
			"## 涨停与连板候选",
			...report.ladder.map((x) => `- ${x.stock.name}：${p(x.currentPct)}，连续候选${x.streak}天`),
			"",
			"## 个股涨幅榜",
			...(report.gainLeaders || []).map((x, i) => `${i + 1}. ${x.name}（${x.code}）${p(x.pct)}，成交额 ${money(x.amount)}`),
			"",
			"## 个股成交额榜",
			...(report.amountLeaders || []).map((x, i) => `${i + 1}. ${x.name}（${x.code}）${p(x.pct)}，成交额 ${money(x.amount)}`),
			"",
			"## 负反馈与前日涨停表现（本地推导）",
			...(report.lossLeaders || []).map((x, i) => `${i + 1}. 跌幅 ${x.name}（${x.code}）${p(x.pct)}，成交额 ${money(x.amount)}`),
			...(report.limitDownCandidates || []).map((x) => `- 跌停阈值候选：${x.name}（${x.code}）${p(x.pct)}`),
			report.priorLimitUpStats ? `- 前日涨停候选 ${report.priorLimitUpStats.count || 0} 只，今日平均 ${report.priorLimitUpStats.todayAvgPct == null ? "—" : p(report.priorLimitUpStats.todayAvgPct)}` : "",
			"",
			"## 盘中封板与炸板（OHLC代理）",
			report.intradayProxy ? `- 涨停触板 ${report.intradayProxy.upperHitCount} 只，收盘封板 ${report.intradayProxy.upperClosedCount} 只，触板后开板 ${report.intradayProxy.openedAfterHitCount} 只，代理封板率 ${report.intradayProxy.sealRatePct == null ? "—" : p(report.intradayProxy.sealRatePct)}，代理炸板率 ${report.intradayProxy.explosionRatePct == null ? "—" : p(report.intradayProxy.explosionRatePct)}。` : "- 未生成盘中代理数据",
			report.intradayProxy ? `- 同日5分钟文件 ${report.intradayProxy.lc5CurrentDateCount}/${report.intradayProxy.lc5Files}；首封时刻与封单额未提供。该段仅为日线OHLC代理。` : "",
			"",
			"## 数据充分性与缺口",
			...(report.availability || []).map((x) => `- ${x.item}：${x.status}。${x.evidence}。解决：${x.solution}`),
			"",
			"## 风险与下一步",
			...report.cautions.map((x) => `- ${x}`),
			...report.actions.map((x) => `- 下一步：${x}`)
		].join("\n");
		const url = URL.createObjectURL(new Blob(["﻿" + text], { type: "text/markdown;charset=utf-8" }));
		const a = document.createElement("a");
		a.href = url;
		a.download = `掌财复盘报告-${report.date}.md`;
		a.click();
		setTimeout(() => URL.revokeObjectURL(url), 1e3);
	}
	function stockTable(rows) {
		return /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsx(TableRow, { children: [
			"股票",
			closeDateLabel(market.date),
			"涨跌幅",
			"成交额",
			"自选"
		].map((x) => /* @__PURE__ */ jsx(TableHead, { children: x }, x)) }) }), /* @__PURE__ */ jsx(TableBody, { children: rows.map((s) => /* @__PURE__ */ jsxs(TableRow, { children: [
			/* @__PURE__ */ jsx(TableCell, { children: /* @__PURE__ */ jsxs("button", {
				className: "stock-name",
				onClick: () => onSelect(s),
				children: [s.name, /* @__PURE__ */ jsx("small", { children: s.code })]
			}) }),
			/* @__PURE__ */ jsx(TableCell, {
				className: "numeric",
				title: closeDateLabel(s.date),
				children: s.close.toFixed(2)
			}),
			/* @__PURE__ */ jsx(TableCell, {
				className: `numeric ${s.pct >= 0 ? "up" : "down"}`,
				children: p(s.pct)
			}),
			/* @__PURE__ */ jsx(TableCell, {
				className: "numeric",
				children: money(s.amount)
			}),
			/* @__PURE__ */ jsx(TableCell, { children: /* @__PURE__ */ jsx("button", {
				className: `star-button ${watch.includes(s.code) ? "saved" : ""}`,
				onClick: () => onWatch(s.code),
				"aria-label": `${watch.includes(s.code) ? "移除" : "添加"}自选 ${s.name}`,
				children: /* @__PURE__ */ jsx(Star, {
					size: 16,
					fill: watch.includes(s.code) ? "currentColor" : "none"
				})
			}) })
		] }, s.code)) })] });
	}
	const skillDestination = (item) => {
		return item.group === "research" ? "research" : null;
	};
	function handleSkillClick(item) {
		const destination = skillDestination(item);
		if (destination && destination !== page) {
			setSkill(null);
			navigate(destination);
			return;
		}
		setSkillOutput("");
		setSkillHarnessOutput("");
		setSkillHarnessError("");
		setSkill(item);
	}
	function openResearchCode() {
		const code = researchCode.trim().replace(/\D/g, "").slice(-6);
		if (!/^\d{6}$/.test(code)) {
			setResearchCodeError("请输入 6 位股票代码");
			return;
		}
		const opened = onSelectCode ? onSelectCode(code) : Boolean(searchableStocks.find((row) => row.code === code));
		if (!onSelectCode) {
			const row = searchableStocks.find((item) => item.code === code);
			if (row) onSelect(row);
		}
		if (!opened && onSelectCode) {
			setResearchCodeError(`当日日线中未找到 ${code}，请先刷新行情`);
			return;
		}
		if (!opened && !onSelectCode) {
			setResearchCodeError(`当日日线中未找到 ${code}，请先刷新行情`);
			return;
		}
		setResearchCodeError("");
	}
	function skillCards(list) {
		return /* @__PURE__ */ jsx("div", {
			className: "skill-grid",
			children: list.map((s, i) => {
				const catalogStatus = s.group === "selection" ? strategyDataStatus(s.id) : null;
				const mode = catalogStatus === "missing" ? "data" : catalogStatus === "partial" ? "partial" : skillMode(s.id);
				const detailOnly = mode === "basic";
				const run = s.group === "selection" ? strategyRuns[s.id] : void 0;
				const hasReport = strategyRunHasReport(run);
				const hasFailure = strategyRunHasFailure(run);
				return /* @__PURE__ */ jsxs("button", {
					className: `skill-card skill-card-${mode}`,
					onClick: () => handleSkillClick(s),
					children: [
						/* @__PURE__ */ jsxs("div", {
							className: "skill-card-top",
							children: [/* @__PURE__ */ jsx("span", {
								className: "skill-icon",
								children: i % 3 === 0 ? /* @__PURE__ */ jsx(Target, { size: 19 }) : i % 3 === 1 ? /* @__PURE__ */ jsx(Layers, { size: 19 }) : /* @__PURE__ */ jsx(Workflow, { size: 19 })
							}), /* @__PURE__ */ jsx("small", {
								className: "skill-ready",
								children: detailOnly ? "基础能力 · 仅详情" : "本地数据预检"
							})]
						}),
						/* @__PURE__ */ jsx("h3", { children: s.name }),
						/* @__PURE__ */ jsxs("p", { children: [
							skillIntroduction(s),
							" ",
							detailOnly ? "本页仅展示技能详情，不启动预检或 Harness。" : "先校验已落盘数据与降级规则；进入详情后可生成预检，也可直接调用 Harness。"
						] }),
						/* @__PURE__ */ jsxs("small", {
							className: "skill-original-id",
							children: ["原始技能：", s.id]
						}),
						/* @__PURE__ */ jsx(Tags, { list: s.dependencies.slice(0, 3) }),
						/* @__PURE__ */ jsxs("div", {
							className: "skill-card-bottom",
							children: [/* @__PURE__ */ jsx("span", { children: groupNames[s.group] }), /* @__PURE__ */ jsxs("span", { children: [detailOnly ? "查看技能详情" : run?.busy ? "正在预检…" : hasReport ? "查看最新回执" : hasFailure ? "查看失败详情" : "查看并预检", /* @__PURE__ */ jsx(ArrowUpRight, { size: 14 })] })]
						})
					]
				}, s.id);
			})
		});
	}
	function mainlineTable(rows) {
		return /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
			/* @__PURE__ */ jsx(TableHead, { children: "方向" }),
			/* @__PURE__ */ jsx(TableHead, { children: "样本" }),
			/* @__PURE__ */ jsx(TableHead, { children: "平均涨跌" }),
			/* @__PURE__ */ jsx(TableHead, { children: "成交额" }),
			/* @__PURE__ */ jsx(TableHead, { children: "代表股" })
		] }) }), /* @__PURE__ */ jsx(TableBody, { children: rows.map((x) => /* @__PURE__ */ jsxs(TableRow, { children: [
			/* @__PURE__ */ jsxs(TableCell, { children: [/* @__PURE__ */ jsx("b", { children: x.name }), /* @__PURE__ */ jsx("small", {
				className: "table-sub",
				children: x.tag
			})] }),
			/* @__PURE__ */ jsx(TableCell, { children: x.count }),
			/* @__PURE__ */ jsx(TableCell, {
				className: `numeric ${x.avgPct >= 0 ? "up" : "down"}`,
				children: p(x.avgPct)
			}),
			/* @__PURE__ */ jsx(TableCell, {
				className: "numeric",
				children: money(x.amount)
			}),
			/* @__PURE__ */ jsx(TableCell, { children: x.leaders.map((s) => s.name).join("、") })
		] }, x.name)) })] });
	}
	const environment = environmentSnapshot || {};
	const environmentTdx = environment.tdx && typeof environment.tdx === "object" ? environment.tdx : {};
	const environmentDaily = environment.daily && typeof environment.daily === "object" ? environment.daily : {};
	const environmentHarness = environment.harness && typeof environment.harness === "object" ? environment.harness : {};
	const environmentIndexInitialization = environment.dailyIndexInitialization && typeof environment.dailyIndexInitialization === "object" ? environment.dailyIndexInitialization : {};
	const environmentCanonicalIndex = environment.canonicalDailyIndex && typeof environment.canonicalDailyIndex === "object" ? environment.canonicalDailyIndex : {};
	const runtimeStorageLabel = isDesktopRuntime() ? "EXE 资源库" : "本地运行目录";
	const environmentDailyState = environment.dailyRefresh && typeof environment.dailyRefresh === "object" ? environment.dailyRefresh : {};
	const environmentSupplementalState = environment.supplementalRefresh && typeof environment.supplementalRefresh === "object" ? environment.supplementalRefresh : {};
	const environmentSupplemental = environment.supplemental && typeof environment.supplemental === "object" ? environment.supplemental : {};
	const environmentDailyArchive = environment.dailyArchive && typeof environment.dailyArchive === "object" ? environment.dailyArchive : {};
	const environmentDailyIndex = environment.dailyDataIndex && typeof environment.dailyDataIndex === "object" ? environment.dailyDataIndex : {};
	const environmentDailyIndexSummary = environmentDailyIndex.summary && typeof environmentDailyIndex.summary === "object" ? environmentDailyIndex.summary : {};
	const environmentUnifiedArchive = environment.unifiedArchive && typeof environment.unifiedArchive === "object" ? environment.unifiedArchive : {};
	const environmentUnifiedVerification = environment.unifiedVerification && typeof environment.unifiedVerification === "object" ? environment.unifiedVerification : {};
	const unifiedArchiveStatus = String(environmentUnifiedArchive.status || "未执行");
	const unifiedArchiveSteps = Array.isArray(environmentUnifiedArchive.steps) ? environmentUnifiedArchive.steps : [];
	const unifiedArchiveProgress = unifiedArchiveSteps.filter((step) => [
		"completed",
		"partial",
		"failed"
	].includes(String(step.status || ""))).length;
	const unifiedArchiveTotal = unifiedArchiveSteps.length || 9;
	const unifiedArchiveActiveStep = unifiedArchiveSteps.find((step) => step.status === "running");
	const unifiedArchiveReport = environmentUnifiedArchive.report && typeof environmentUnifiedArchive.report === "object" ? environmentUnifiedArchive.report : {};
	const unifiedArchiveHarness = environmentUnifiedArchive.harness && typeof environmentUnifiedArchive.harness === "object" ? environmentUnifiedArchive.harness : {};
	const unifiedArchiveReportUrl = typeof unifiedArchiveReport.htmlUrl === "string" ? bridgeUrl(unifiedArchiveReport.htmlUrl) : bridgeUrl("/data/archive/report");
	const unifiedArchiveBadge = unifiedArchiveStatus === "completed" ? "已完成" : unifiedArchiveStatus === "running" ? "运行中" : unifiedArchiveStatus === "partial" ? "部分完成" : unifiedArchiveStatus === "failed" ? "失败" : "待执行";
	const environmentSourceManifest = environment.unifiedSourceManifest && typeof environment.unifiedSourceManifest === "object" ? environment.unifiedSourceManifest : {};
	const environmentSourceRows = Array.isArray(environmentSourceManifest.sources) ? environmentSourceManifest.sources : [];
	const environmentIntegrity = environmentDaily.integrity && typeof environmentDaily.integrity === "object" ? environmentDaily.integrity : {};
	const environmentIntegrityAfter = environmentIntegrity.after && typeof environmentIntegrity.after === "object" ? environmentIntegrity.after : {};
	const environmentIntegrityUnresolved = Array.isArray(environmentIntegrity.unresolved) ? environmentIntegrity.unresolved : [];
	const environmentIntegrityUnresolvedCount = Number(environmentIntegrity.unresolvedCount ?? environmentIntegrityUnresolved.length);
	const environmentIntegrityRepairs = Array.isArray(environmentIntegrity.repairs) ? environmentIntegrity.repairs : [];
	const environmentIntegrityNonTrading = Array.isArray(environmentIntegrity.nonTrading) ? environmentIntegrity.nonTrading : [];
	const environmentIntegrityRepairedCount = environmentIntegrityRepairs.filter((item) => item.status === "written").length;
	const environmentIntegrityManualAction = String(environmentIntegrity.manualAction || "");
	const environmentRunningStep = Array.isArray(environmentDailyState.steps) ? environmentDailyState.steps.find((step) => step.status === "running") : void 0;
	const environmentSources = Array.isArray(environment.sources) ? environment.sources : [];
	const environmentValidation = environment.harnessValidation && typeof environment.harnessValidation === "object" ? environment.harnessValidation : {};
	return /* @__PURE__ */ jsxs("div", {
		className: "secondary-page",
		children: [
			harnessProgress(),
			page === "skills" && /* @__PURE__ */ jsxs(Fragment$1, { children: [
				/* @__PURE__ */ jsxs("div", {
					className: "section-intro",
					children: [/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("h2", { children: "电脑版技能目录 · 14 项" }), /* @__PURE__ */ jsx("p", { children: "列表仅包含本次导入的 14 个电脑版技能包，沿用原有工作台分组与卡片版面。每项先生成本地数据预检和落盘回执。" })] }), /* @__PURE__ */ jsxs("span", {
						className: "big-count",
						children: ["14", /* @__PURE__ */ jsx("small", { children: "项技能" })]
					})]
				}),
				/* @__PURE__ */ jsxs("div", {
					className: "filter-toolbar",
					children: [
						/* @__PURE__ */ jsxs("div", {
							className: "search-field",
							children: [/* @__PURE__ */ jsx(Search, { size: 17 }), /* @__PURE__ */ jsx(Input, {
								"aria-label": "搜索技能",
								placeholder: "搜索技能名称、调用别名…",
								value: search,
								onChange: (e) => setSearch(e.target.value)
							})]
						}),
						/* @__PURE__ */ jsxs(Select, {
							value: group,
							onValueChange: (v) => setGroup(v || "all"),
							children: [/* @__PURE__ */ jsx(SelectTrigger, {
								"aria-label": "技能分类",
								className: "filter-select",
								children: /* @__PURE__ */ jsx(SelectValue, { children: group === "all" ? "全部分类" : groupNames[group] })
							}), /* @__PURE__ */ jsxs(SelectContent, { children: [/* @__PURE__ */ jsx(SelectItem, {
								value: "all",
								children: "全部分类"
							}), Object.entries(groupNames).map(([k, v]) => /* @__PURE__ */ jsx(SelectItem, {
								value: k,
								children: v
							}, k))] })]
						}),
						/* @__PURE__ */ jsxs("span", {
							className: "subtle",
							children: [
								visibleSkills.length,
								" ",
								"项匹配"
							]
						})
					]
				}),
				visibleSkillGroups.map(([groupId, groupName]) => {
					const rows = visibleSkills.filter((item) => item.group === groupId);
					return /* @__PURE__ */ jsxs("section", {
						className: "skill-type-section",
						children: [/* @__PURE__ */ jsxs("div", {
							className: "section-label",
							children: [
								groupName,
								" ",
								/* @__PURE__ */ jsxs("span", { children: [rows.length, " 项"] })
							]
						}), skillCards(rows)]
					}, groupId);
				}),
				!visibleSkills.length && /* @__PURE__ */ jsx(Empty, {
					title: "没有匹配技能",
					body: "尝试搜索“龙头”“评分”或切换分类。"
				})
			] }),
			page === "mainline" && /* @__PURE__ */ jsxs(Fragment$1, { children: [
				/* @__PURE__ */ jsxs("div", {
					className: "sample-banner",
					children: [
						/* @__PURE__ */ jsx(RefreshCw, { size: 16 }),
						/* @__PURE__ */ jsxs("span", { children: [
							"已按 ",
							d(market.date),
							" ",
							"通达信日线与 TDX 行业/主题成员刷新；连板网 PDF 仅作历史口径参考。"
						] }),
						/* @__PURE__ */ jsxs(Button, {
							variant: "outline",
							disabled: aiBusy,
							onClick: () => makeHarnessReport("short-term-sentiment-v22", { themes }),
							children: [
								aiBusy ? /* @__PURE__ */ jsx(LoaderCircle, {
									className: "spin",
									size: 15
								}) : /* @__PURE__ */ jsx(Sparkles, { size: 15 }),
								" ",
								"Harness 主线研判"
							]
						})
					]
				}),
				/* @__PURE__ */ jsx(Box, {
					title: "主线研判 · short-term-sentiment-v22",
					extra: /* @__PURE__ */ jsx("span", {
						className: "example-label",
						children: "重点摘要"
					}),
					children: /* @__PURE__ */ jsx("div", {
						className: "content-pad",
						children: mainlineHarnessLoading ? /* @__PURE__ */ jsx("p", {
							className: "muted-copy",
							children: "正在读取最近一次 Harness 报告…"
						}) : mainlineHarnessOutput ? /* @__PURE__ */ jsx(HarnessOutput, {
							raw: mainlineHarnessOutput,
							compact: true
						}) : /* @__PURE__ */ jsx(Empty, {
							title: "暂无已完成的主线研判报告",
							body: "点击上方按钮运行 Harness；完成后报告会自动持久化并在此处显示。"
						})
					})
				}),
				/* @__PURE__ */ jsx("div", {
					className: "theme-grid",
					children: themes.slice(0, 6).map((t, i) => /* @__PURE__ */ jsxs("button", {
						onClick: () => setTheme(i),
						className: `theme-card ${theme === i ? "chosen" : ""}`,
						style: { "--theme-color": t.color },
						children: [
							/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("span", { children: t.tag }), /* @__PURE__ */ jsx(ArrowUpRight, { size: 16 })] }),
							/* @__PURE__ */ jsx("h2", { children: t.name }),
							/* @__PURE__ */ jsxs("p", { children: [
								/* @__PURE__ */ jsx("b", { children: t.count }),
								" 只样本",
								" ",
								/* @__PURE__ */ jsxs("span", {
									className: t.avgPct >= 0 ? "up" : "down",
									children: [p(t.avgPct), " 平均涨跌"]
								})
							] }),
							/* @__PURE__ */ jsx("div", {
								className: "theme-meter",
								children: /* @__PURE__ */ jsx("span", { style: { width: `${Math.min(100, t.count / Math.max(...themes.map((x) => x.count), 1) * 100)}%` } })
							})
						]
					}, t.name))
				}),
				themes.length ? /* @__PURE__ */ jsxs("div", {
					className: "two-column",
					children: [/* @__PURE__ */ jsx(Box, {
						title: `${themes[theme]?.name || themes[0].name} · 当日候选`,
						extra: /* @__PURE__ */ jsx("span", {
							className: "example-label",
							children: d(market.date)
						}),
						children: /* @__PURE__ */ jsxs("div", {
							className: "content-pad",
							children: [
								/* @__PURE__ */ jsx(TableProperties, { size: 17 }),
								mainlineTable([themes[theme] || themes[0]]),
								/* @__PURE__ */ jsx("p", {
									className: "muted-copy",
									children: "代表股来自当日样本涨幅排序；TDX 行业/主题映射已提供结构候选，新闻催化和失效条件仍需由 Harness 结合外部证据核验。"
								})
							]
						})
					}), /* @__PURE__ */ jsx(Box, {
						title: "主线研判逻辑",
						children: /* @__PURE__ */ jsxs("div", {
							className: "content-pad",
							children: [/* @__PURE__ */ jsxs("div", {
								className: "logic-steps",
								children: [
									/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: "1" }), /* @__PURE__ */ jsx("span", { children: "优先读取 TDX 主题成员，缺失时使用 TDX 行业成员" })] }),
									/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: "2" }), /* @__PURE__ */ jsx("span", { children: "按样本数、平均涨跌、成交额和涨停家数排序" })] }),
									/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: "3" }), /* @__PURE__ */ jsx("span", { children: "取涨幅领先个股作为代表股" })] })
								]
							}), /* @__PURE__ */ jsxs(Button, {
								className: "primary-button",
								disabled: aiBusy,
								onClick: () => makeHarnessReport("market-environment-v5", { themes }),
								children: [/* @__PURE__ */ jsx(Sparkles, { size: 15 }), "用 Harness 生成主线报告"]
							})]
						})
					})]
				}) : /* @__PURE__ */ jsx(Empty, {
					title: "当日没有形成聚类",
					body: "请刷新行情文件后重试。"
				}),
				/* @__PURE__ */ jsxs("div", {
					className: "section-label",
					children: ["本页对应技能 ", /* @__PURE__ */ jsxs("span", { children: [related.length, " 项"] })]
				}),
				skillCards(related)
			] }),
			page === "ladder" && /* @__PURE__ */ jsxs(Fragment$1, { children: [
				/* @__PURE__ */ jsxs("div", {
					className: "sample-banner",
					children: [
						/* @__PURE__ */ jsx(RefreshCw, { size: 16 }),
						/* @__PURE__ */ jsxs("span", { children: [
							"已按 ",
							d(market.date),
							" ",
							"日线数据刷新。涨停为按主板、创业板、科创板、北交所和 ST 阈值识别的候选，连板按近 30 个交易日连续阈值计算。"
						] }),
						/* @__PURE__ */ jsxs(Button, {
							variant: "outline",
							disabled: aiBusy,
							onClick: () => makeHarnessReport("limit-up-review", { ladder: ladder.slice(0, 30) }),
							children: [
								aiBusy ? /* @__PURE__ */ jsx(LoaderCircle, {
									className: "spin",
									size: 15
								}) : /* @__PURE__ */ jsx(Sparkles, { size: 15 }),
								" ",
								"Harness 连板复盘"
							]
						})
					]
				}),
				/* @__PURE__ */ jsx("div", {
					className: "metric-grid",
					children: [
						[
							"涨停候选",
							`${ladder.length}`,
							`数据日 ${d(market.date)}`
						],
						[
							"连板候选",
							`${ladder.filter((x) => x.streak > 1).length}`,
							"近 30 日连续阈值"
						],
						[
							"最高连续",
							`${Math.max(0, ...ladder.map((x) => x.streak))} 天`,
							ladder[0]?.stock.name || "—"
						],
						[
							"样本范围",
							`${market.currentCount} 只`,
							"同日股票"
						]
					].map(([l, v, n]) => /* @__PURE__ */ jsxs("div", {
						className: "metric-card",
						children: [
							/* @__PURE__ */ jsx("span", { children: l }),
							/* @__PURE__ */ jsx("b", { children: v }),
							/* @__PURE__ */ jsx("small", { children: n })
						]
					}, l))
				}),
				/* @__PURE__ */ jsxs(Box, {
					title: "当日涨停与连板候选",
					extra: /* @__PURE__ */ jsx("span", {
						className: "example-label",
						children: "自动刷新"
					}),
					children: [ladder.length ? /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
						/* @__PURE__ */ jsx(TableHead, { children: "股票" }),
						/* @__PURE__ */ jsx(TableHead, { children: "涨跌幅" }),
						/* @__PURE__ */ jsx(TableHead, { children: "适用阈值" }),
						/* @__PURE__ */ jsx(TableHead, { children: "连续候选" }),
						/* @__PURE__ */ jsx(TableHead, { children: "成交额" })
					] }) }), /* @__PURE__ */ jsx(TableBody, { children: ladder.slice(0, 40).map((x) => /* @__PURE__ */ jsxs(TableRow, { children: [
						/* @__PURE__ */ jsx(TableCell, { children: /* @__PURE__ */ jsxs("button", {
							className: "stock-name",
							onClick: () => onSelect(x.stock),
							children: [x.stock.name, /* @__PURE__ */ jsx("small", { children: x.stock.code })]
						}) }),
						/* @__PURE__ */ jsx(TableCell, {
							className: "numeric up",
							children: p(x.currentPct)
						}),
						/* @__PURE__ */ jsxs(TableCell, { children: [x.limitPct, "%"] }),
						/* @__PURE__ */ jsx(TableCell, { children: /* @__PURE__ */ jsxs("b", { children: [x.streak, " 天"] }) }),
						/* @__PURE__ */ jsx(TableCell, {
							className: "numeric",
							children: money(x.stock.amount)
						})
					] }, x.stock.code)) })] }) : /* @__PURE__ */ jsx(Empty, {
						title: "今日没有涨停候选",
						body: "请确认通达信日线文件已更新。"
					}), /* @__PURE__ */ jsx("div", {
						className: "panel-footnote",
						children: "日线无法确认盘中封板、炸板和停牌过程；正式报告会保留“候选”标记。"
					})]
				}),
				/* @__PURE__ */ jsxs("div", {
					className: "section-label",
					children: ["涨停研究与监控 ", /* @__PURE__ */ jsxs("span", { children: [related.length, " 项技能"] })]
				}),
				skillCards(related)
			] }),
			page === "selection" && /* @__PURE__ */ jsxs(Fragment$1, { children: [/* @__PURE__ */ jsxs("div", {
				className: "selection-layout",
				children: [/* @__PURE__ */ jsxs(Box, {
					title: "选择策略",
					children: [/* @__PURE__ */ jsx("div", {
						className: "strategy-menu",
						children: skills.filter((s) => s.group === "selection").map((s) => {
							const catalog = strategyCatalogItem(s.id);
							strategyDataStatus(s.id);
							const run = strategyRuns[s.id];
							return /* @__PURE__ */ jsxs("button", {
								className: selectedStrategy === s.id ? "selected" : "",
								disabled: run?.busy,
								title: catalog?.dataNote || "生成本地数据预检与落盘运行单",
								onClick: () => {
									setSelectedStrategy(s.id);
									setFilterRan(false);
								},
								children: [
									/* @__PURE__ */ jsx(Target, { size: 15 }),
									/* @__PURE__ */ jsxs("span", {
										className: "strategy-menu-copy",
										children: [/* @__PURE__ */ jsx("b", { children: s.name }), /* @__PURE__ */ jsx("small", { children: run?.busy ? run.phase === "harness" ? "Harness 分析中" : "本地预检中" : run?.phase === "completed" ? "Harness 已完成" : run?.phase === "preflight" ? `预检 ${run.status}` : strategyRunHasFailure(run) ? "上次运行失败" : "可运行" })]
									}),
									selectedStrategy === s.id && /* @__PURE__ */ jsx(Check, { size: 15 })
								]
							}, s.id);
						})
					}), /* @__PURE__ */ jsx("div", {
						className: "strategy-menu-audit",
						children: "本区保留 3 个选股类电脑版技能；点击运行后先做本地预检，再调用对应技能的 Harness 分析，任务与结果会保存到应用数据目录。"
					})]
				}), /* @__PURE__ */ jsxs("div", { children: [
					/* @__PURE__ */ jsx(Box, {
						title: skills.find((s) => s.id === selectedStrategy)?.name || "策略选股",
						extra: /* @__PURE__ */ jsxs("button", {
							className: "text-link",
							onClick: () => openById(selectedStrategy),
							children: ["技能说明", /* @__PURE__ */ jsx(ArrowUpRight, { size: 14 })]
						}),
						children: /* @__PURE__ */ jsxs("div", {
							className: "content-pad",
							children: [
								/* @__PURE__ */ jsxs("div", {
									className: "sample-banner",
									children: [/* @__PURE__ */ jsx(Info, { size: 16 }), "保持原有筛选布局；运行流程为“本地数据预检 → 对应技能 Harness 分析”，不再直接拼接旧版不存在的策略路径。"]
								}),
								/* @__PURE__ */ jsxs("div", {
									className: "form-grid",
									children: [
										/* @__PURE__ */ jsxs("label", { children: ["最小日涨幅（%）", /* @__PURE__ */ jsx(Input, {
											type: "number",
											min: "-100",
											max: "100",
											value: minPct,
											onChange: (e) => setMinPct(e.target.value)
										})] }),
										/* @__PURE__ */ jsxs("label", { children: ["最小成交额（亿元）", /* @__PURE__ */ jsx(Input, {
											type: "number",
											min: "0",
											value: minAmount,
											onChange: (e) => setMinAmount(e.target.value)
										})] }),
										/* @__PURE__ */ jsxs("label", { children: ["数据范围", /* @__PURE__ */ jsxs("div", {
											className: "readonly-input",
											children: [
												"沪深北 · ",
												market.currentCount,
												" 只同日样本 ·",
												" ",
												d(market.date)
											]
										})] })
									]
								}),
								selectedStrategy === "golden-ignition-v8" && /* @__PURE__ */ jsxs("div", {
									className: "single-signal-section",
									children: [/* @__PURE__ */ jsxs("div", {
										className: "research-code-entry",
										children: [
											/* @__PURE__ */ jsxs("div", {
												className: "research-code-copy",
												children: [/* @__PURE__ */ jsx("b", { children: "单股执行信号" }), /* @__PURE__ */ jsx("span", { children: "输入股票代码，执行黄金点火本地业务入口；结果不参与 Top10 筛选。" })]
											}),
											/* @__PURE__ */ jsxs("div", {
												className: "research-code-controls",
												children: [/* @__PURE__ */ jsx(Input, {
													"aria-label": "单股股票代码",
													placeholder: "股票代码，如 300563",
													value: singleSignalCode,
													maxLength: 6,
													onChange: (e) => {
														setSingleSignalCode(e.target.value.replace(/\D/g, "").slice(0, 6));
														setSingleSignalError("");
													},
													onKeyDown: (e) => {
														if (e.key === "Enter") runSingleGoldenIgnition();
													}
												}), /* @__PURE__ */ jsxs(Button, {
													variant: "outline",
													"aria-label": "执行单股信号",
													disabled: singleSignalBusy,
													onClick: () => void runSingleGoldenIgnition(),
													children: [singleSignalBusy ? /* @__PURE__ */ jsx(LoaderCircle, {
														className: "spin",
														size: 15
													}) : /* @__PURE__ */ jsx(Target, { size: 15 }), singleSignalBusy ? "执行中…" : "执行单股信号"]
												})]
											}),
											singleSignalError && /* @__PURE__ */ jsx("span", {
												className: "form-error",
												role: "alert",
												children: singleSignalError
											})
										]
									}), singleSignalResult && /* @__PURE__ */ jsxs("div", {
										className: `strategy-run-output ${singleSignalResult.status === "ok" ? "ready" : "blocked"}`,
										role: "status",
										children: [
											/* @__PURE__ */ jsxs("b", { children: ["单股信号回执：", singleSignalResult.signal_status === "HIT" ? "HIT · 已触发" : singleSignalResult.signal_status === "NO_SIGNAL" ? "NO_SIGNAL · 未触发" : singleSignalResult.status || "BLOCKED"] }),
											/* @__PURE__ */ jsxs("div", {
												className: "settings-list",
												children: [
													/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "输入 / 分析标的" }), /* @__PURE__ */ jsxs("dd", { children: [
														singleSignalResult.input_symbol || "—",
														" / ",
														singleSignalResult.analysis_symbol || "—"
													] })] }),
													/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "最新交易日" }), /* @__PURE__ */ jsx("dd", { children: d(singleSignalResult.latest_trading_date || "") })] }),
													/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "最新收盘 / EMA3 / EMA21" }), /* @__PURE__ */ jsxs("dd", { children: [
														formulaText(singleSignalResult.local_daily?.latest_close) || "—",
														" / ",
														formulaText(singleSignalResult.local_daily?.latest_ema3) || "—",
														" / ",
														formulaText(singleSignalResult.local_daily?.latest_ema21) || "—"
													] })] }),
													/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "OUTPUT59 / OUTPUT60 / OUTPUT61" }), /* @__PURE__ */ jsxs("dd", { children: [
														formulaText(singleSignalResult.tdx_formula?.fields?.OUTPUT59) || "—",
														" / ",
														formulaText(singleSignalResult.tdx_formula?.fields?.OUTPUT60) || "—",
														" / ",
														formulaText(singleSignalResult.tdx_formula?.fields?.OUTPUT61) || "—"
													] })] }),
													/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "点火布尔 / 公式状态" }), /* @__PURE__ */ jsxs("dd", { children: [
														singleSignalResult.ignition_signal ? "true" : "false",
														" / ",
														singleSignalResult.tdx_formula?.ok ? "已返回" : "未返回或无值"
													] })] }),
													/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "本地回执" }), /* @__PURE__ */ jsx("dd", { children: singleSignalResult.result_path || "已生成，但路径未返回" })] })
												]
											}),
											singleSignalResult.error && /* @__PURE__ */ jsx("p", {
												className: "muted-copy",
												children: singleSignalResult.error
											}),
											Array.isArray(singleSignalResult.risk_boundary) && singleSignalResult.risk_boundary.length > 0 && /* @__PURE__ */ jsxs("p", {
												className: "muted-copy",
												children: ["风险边界：", singleSignalResult.risk_boundary.join("；")]
											})
										]
									})]
								}),
								/* @__PURE__ */ jsxs("div", {
									className: "action-row",
									children: [/* @__PURE__ */ jsxs(Button, {
										className: "primary-button",
										"aria-label": "生成本地预检并调用 Harness 分析",
										disabled: selectedStrategyRun.busy,
										onClick: runSelectedStrategy,
										children: [selectedStrategyRun.busy ? /* @__PURE__ */ jsx(LoaderCircle, {
											className: "spin",
											size: 15
										}) : /* @__PURE__ */ jsx(Workflow, { size: 15 }), selectedStrategyRun.busy ? selectedStrategyRun.phase === "harness" ? "Harness 分析中…" : "生成预检中…" : selectedStrategyRun.phase === "completed" ? "重新预检并调用 Harness 分析" : selectedStrategyRun.phase === "preflight" ? "重新预检并调用 Harness 分析" : selectedStrategyHasFailure ? "重试预检并调用 Harness 分析" : "生成预检并调用 Harness 分析"]
									}), /* @__PURE__ */ jsx("span", {
										className: "harness-eta",
										children: "预检核验落盘数据与降级边界；通过后由 Harness 基于同一份本地数据和候选进行分析，不生成买卖建议。"
									})]
								}),
								selectedStrategyRun.busy && /* @__PURE__ */ jsxs("div", {
									className: "harness-progress",
									role: "status",
									children: [/* @__PURE__ */ jsx(LoaderCircle, {
										className: "spin",
										size: 15
									}), /* @__PURE__ */ jsxs("span", { children: [
										selectedStrategy,
										" ",
										selectedStrategyRun.phase === "harness" ? "Harness 分析中" : "本地预检中",
										" · 已运行 ",
										formatDuration(selectedStrategyRun.elapsed),
										" · ",
										selectedStrategyRun.phase === "harness" ? "正在整理本地候选与预检回执" : "正在核验日线、公式与辅助数据依赖"
									] })]
								}),
								selectedStrategyRun.output && /* @__PURE__ */ jsxs("div", {
									className: `strategy-run-output ${selectedStrategyRun.status === "READY_FOR_VALIDATED_RUN" ? "ready" : "blocked"}`,
									children: [/* @__PURE__ */ jsxs("b", { children: ["本地数据预检：", selectedStrategyRun.status || "UNKNOWN"] }), /* @__PURE__ */ jsx("pre", { children: strategyPreflightDisplayText(selectedStrategyRun.output) })]
								}),
								selectedStrategyRun.harnessOutput && /* @__PURE__ */ jsxs("div", {
									className: "strategy-run-output ready",
									children: [/* @__PURE__ */ jsx("b", { children: "Harness 分析结果" }), /* @__PURE__ */ jsx(HarnessOutput, { raw: selectedStrategyRun.harnessOutput })]
								}),
								filterError && /* @__PURE__ */ jsx("p", {
									className: "form-error",
									role: "alert",
									children: filterError
								})
							]
						})
					}),
					/* @__PURE__ */ jsx("div", { className: "section-spacer" }),
					/* @__PURE__ */ jsx(Box, {
						title: filterRan ? `基础条件匹配 · ${filtered.length} 只` : "本地条件候选",
						extra: filterRan ? /* @__PURE__ */ jsxs("span", {
							className: "subtle",
							children: ["展示前 30 只 · ", d(market.date)]
						}) : void 0,
						children: filterRan ? filtered.length ? stockTable(filtered.slice(0, 30)) : /* @__PURE__ */ jsx(Empty, {
							title: "没有符合条件的股票",
							body: "请调整条件后重试。"
						}) : /* @__PURE__ */ jsx(Empty, {
							title: "生成本地数据预检后查看回执",
							body: "页面会同时展示本地条件候选和 14 技能的预检状态。"
						})
					})
				] })]
			}), /* @__PURE__ */ jsx(StrategyReportGallery, {
				strategies: skills.filter((s) => s.group === "selection"),
				runs: strategyRuns
			})] }),
			page === "research" && /* @__PURE__ */ jsxs(Fragment$1, { children: [
				/* @__PURE__ */ jsxs("div", {
					className: "research-code-entry",
					children: [
						/* @__PURE__ */ jsxs("div", {
							className: "research-code-copy",
							children: [/* @__PURE__ */ jsx("b", { children: "按代码打开个股" }), /* @__PURE__ */ jsxs("span", { children: [market.degraded === true || market.dataQuality === "degraded" || market.quality === "degraded" ? `目标日未落盘，已降级使用 ${d(market.date)} 日线收盘数据` : `使用 ${d(market.date)} 日线收盘数据`, " · 输入后可查看十项个股技能"] })]
						}),
						/* @__PURE__ */ jsxs("div", {
							className: "research-code-controls",
							children: [
								/* @__PURE__ */ jsx(Input, {
									"aria-label": "输入股票代码",
									placeholder: "股票代码，如 300959",
									value: researchCode,
									maxLength: 6,
									onChange: (e) => {
										setResearchCode(e.target.value.replace(/\D/g, "").slice(0, 6));
										setResearchCodeError("");
									},
									onKeyDown: (e) => {
										if (e.key === "Enter") openResearchCode();
									}
								}),
								/* @__PURE__ */ jsx(Button, {
									variant: "outline",
									onClick: openResearchCode,
									children: "查看个股"
								}),
								onRefreshMarket && /* @__PURE__ */ jsxs(Button, {
									variant: "outline",
									onClick: () => void onRefreshMarket(),
									disabled: marketRefreshing,
									children: [marketRefreshing ? /* @__PURE__ */ jsx(LoaderCircle, {
										className: "spin",
										size: 15
									}) : /* @__PURE__ */ jsx(RefreshCw, { size: 15 }), "刷新行情"]
								})
							]
						}),
						researchCodeError && /* @__PURE__ */ jsx("span", {
							className: "form-error",
							children: researchCodeError
						}),
						marketRefreshMessage && /* @__PURE__ */ jsx("span", {
							className: "subtle research-refresh-message",
							children: marketRefreshMessage
						})
					]
				}),
				/* @__PURE__ */ jsxs("div", {
					className: "filter-toolbar",
					children: [
						/* @__PURE__ */ jsxs("div", {
							className: "search-field",
							children: [/* @__PURE__ */ jsx(Search, { size: 17 }), /* @__PURE__ */ jsx(Input, {
								"aria-label": "搜索本地股票",
								placeholder: "搜索全部本地股票：代码或名称",
								value: search,
								onChange: (e) => {
									setSearch(e.target.value);
									setPageNo(0);
								}
							})]
						}),
						/* @__PURE__ */ jsxs(Select, {
							value: sort,
							onValueChange: (v) => {
								setSort(v || "gain");
								setPageNo(0);
							},
							children: [/* @__PURE__ */ jsx(SelectTrigger, {
								"aria-label": "个股排序",
								className: "filter-select",
								children: /* @__PURE__ */ jsx(SelectValue, { children: sort === "gain" ? "涨幅优先" : sort === "loss" ? "跌幅优先" : "成交额优先" })
							}), /* @__PURE__ */ jsxs(SelectContent, { children: [
								/* @__PURE__ */ jsx(SelectItem, {
									value: "gain",
									children: "涨幅优先"
								}),
								/* @__PURE__ */ jsx(SelectItem, {
									value: "loss",
									children: "跌幅优先"
								}),
								/* @__PURE__ */ jsx(SelectItem, {
									value: "amount",
									children: "成交额优先"
								})
							] })]
						}),
						/* @__PURE__ */ jsxs("span", {
							className: "subtle",
							children: [filteredStocks.length, " 只匹配"]
						})
					]
				}),
				/* @__PURE__ */ jsxs(Box, {
					title: "全量个股档案",
					extra: /* @__PURE__ */ jsxs("span", {
						className: "subtle",
						children: [
							searchableStocks.length,
							" 只 ",
							d(market.date),
							" 日线股票",
							market.degraded === true || market.dataQuality === "degraded" || market.quality === "degraded" ? "（最近完整交易日降级）" : "",
							" · 点击查看行情详情"
						]
					}),
					children: [filteredStocks.length ? stockTable(filteredStocks.slice(pageNo * 15, pageNo * 15 + 15)) : /* @__PURE__ */ jsx(Empty, {
						title: "暂无可用日线股票",
						body: "请先刷新行情或完成本地日线归档；随后可按六位代码或中文名称检索。"
					}), filteredStocks.length > 0 && /* @__PURE__ */ jsxs("div", {
						className: "pagination-row",
						children: [
							/* @__PURE__ */ jsxs("span", { children: [
								"第 ",
								pageNo + 1,
								" / ",
								Math.ceil(filteredStocks.length / 15),
								" 页"
							] }),
							/* @__PURE__ */ jsx(Button, {
								variant: "outline",
								disabled: !pageNo,
								onClick: () => setPageNo((v) => v - 1),
								children: "上一页"
							}),
							/* @__PURE__ */ jsx(Button, {
								variant: "outline",
								disabled: (pageNo + 1) * 15 >= filteredStocks.length,
								onClick: () => setPageNo((v) => v + 1),
								children: "下一页"
							})
						]
					})]
				}),
				/* @__PURE__ */ jsxs("div", {
					className: "section-label",
					children: ["研究工具 ", /* @__PURE__ */ jsxs("span", { children: [related.length, " 项技能"] })]
				}),
				skillCards(related)
			] }),
			page === "watchlist" && /* @__PURE__ */ jsxs(Fragment$1, { children: [
				/* @__PURE__ */ jsxs(Tabs, {
					defaultValue: "watch",
					className: "workspace-tabs",
					children: [
						/* @__PURE__ */ jsxs(TabsList, {
							className: "workspace-tabs-list",
							children: [
								/* @__PURE__ */ jsxs(TabsTrigger, {
									value: "watch",
									children: ["我的自选 · ", watch.length]
								}),
								/* @__PURE__ */ jsx(TabsTrigger, {
									value: "holdings",
									children: "持仓监控"
								}),
								/* @__PURE__ */ jsxs(TabsTrigger, {
									value: "journal",
									children: ["研究日志 · ", archiveRows.length]
								})
							]
						}),
						/* @__PURE__ */ jsx(TabsContent, {
							value: "watch",
							children: /* @__PURE__ */ jsxs(Box, {
								title: "自选观察池",
								extra: /* @__PURE__ */ jsxs("div", {
									className: "watchlist-actions",
									children: [/* @__PURE__ */ jsxs(Button, {
										variant: "outline",
										onClick: () => navigate("research"),
										children: [/* @__PURE__ */ jsx(Search, { size: 14 }), "添加股票"]
									}), /* @__PURE__ */ jsxs(Button, {
										variant: "outline",
										onClick: refreshWatchlist,
										disabled: watchRefreshing || !watch.length,
										children: [watchRefreshing ? /* @__PURE__ */ jsx(LoaderCircle, {
											className: "spin",
											size: 14
										}) : /* @__PURE__ */ jsx(RefreshCw, { size: 14 }), "刷新自选行情"]
									})]
								}),
								children: [watch.length ? (() => {
									const source = [...market.allStocks || [], ...market.stocks];
									const rows = watch.map((code) => source.find((s) => s.code === code)).filter((s) => Boolean(s));
									return rows.length ? stockTable(rows) : /* @__PURE__ */ jsx("div", {
										className: "watchlist-missing",
										children: "自选代码已持久保存，但当前行情快照暂未返回对应报价。刷新行情后会自动补齐。"
									});
								})() : /* @__PURE__ */ jsx(Empty, {
									title: "把关注的股票放到这里",
									body: "在行情榜单、策略筛选或个股研究中点击星标加入自选。"
								}), watchRefreshMessage && /* @__PURE__ */ jsx("div", {
									className: "watchlist-refresh-message",
									children: watchRefreshMessage
								})]
							})
						}),
						/* @__PURE__ */ jsx(TabsContent, {
							value: "holdings",
							children: /* @__PURE__ */ jsx(Box, {
								title: "持仓股监控",
								children: /* @__PURE__ */ jsx(Empty, {
									title: "尚未导入持仓",
									body: "正式版需要成本价、数量、行情源及告警服务。"
								})
							})
						}),
						/* @__PURE__ */ jsx(TabsContent, {
							value: "journal",
							children: /* @__PURE__ */ jsx(Box, {
								title: "研究日志",
								extra: /* @__PURE__ */ jsx("span", {
									className: "subtle",
									children: "与“我的报告”实时同步"
								}),
								children: archiveRows.length ? /* @__PURE__ */ jsx("div", {
									className: "research-journal-list",
									children: archiveRows.slice(0, 20).map((item) => /* @__PURE__ */ jsxs("button", {
										className: "research-journal-item",
										onClick: () => setOpenedArchive(item),
										children: [
											/* @__PURE__ */ jsx("span", {
												className: "journal-type",
												children: item.reportType
											}),
											/* @__PURE__ */ jsxs("div", { children: [
												/* @__PURE__ */ jsx("b", { children: item.title }),
												/* @__PURE__ */ jsxs("small", { children: [
													new Date(item.updatedAt || item.createdAt).toLocaleString("zh-CN", { hour12: false }),
													" · ",
													item.generatedBy
												] }),
												/* @__PURE__ */ jsxs("p", { children: [item.summary.slice(0, 120), item.summary.length > 120 ? "…" : ""] })
											] }),
											/* @__PURE__ */ jsx(ArrowUpRight, { size: 15 })
										]
									}, item.id))
								}) : /* @__PURE__ */ jsx(Empty, {
									title: "还没有研究记录",
									body: "从复盘、个股研究或技能中心生成报告后，研究日志会自动出现。"
								})
							})
						})
					]
				}),
				/* @__PURE__ */ jsx("div", {
					className: "section-label",
					children: "工作台技能"
				}),
				skillCards(related)
			] }),
			page === "reports" && /* @__PURE__ */ jsxs(Fragment$1, { children: [
				/* @__PURE__ */ jsxs("div", {
					className: "report-layout",
					children: [/* @__PURE__ */ jsx("div", { children: /* @__PURE__ */ jsxs(Box, {
						title: "智能复盘流程",
						extra: /* @__PURE__ */ jsx("span", {
							className: "example-label",
							children: "当日数据"
						}),
						children: [/* @__PURE__ */ jsx("div", {
							className: "report-flow",
							children: [
								[
									"01",
									"短线市场情绪",
									"判断市场宽度与指数分化"
								],
								[
									"02",
									"核心主线评分",
									"按当日聚类并交给 Harness 复核"
								],
								[
									"03",
									"涨停板深度复盘",
									"识别日线涨停与连续候选"
								],
								[
									"04",
									"投研交付与验收",
									"保留数据日期、范围和风险"
								]
							].map(([n, t, b]) => /* @__PURE__ */ jsxs("div", { children: [
								/* @__PURE__ */ jsx("span", { children: n }),
								/* @__PURE__ */ jsxs("section", { children: [/* @__PURE__ */ jsx("b", { children: t }), /* @__PURE__ */ jsx("small", { children: b })] }),
								/* @__PURE__ */ jsx("label", { children: "已接入" })
							] }, n))
						}), /* @__PURE__ */ jsxs("div", {
							className: "content-pad",
							children: [
								/* @__PURE__ */ jsxs("div", {
									className: "report-actions",
									children: [/* @__PURE__ */ jsxs(Button, {
										className: "primary-button",
										disabled: reportBusy,
										onClick: makeLocalReport,
										children: [reportBusy ? /* @__PURE__ */ jsx(LoaderCircle, {
											className: "spin",
											size: 16
										}) : /* @__PURE__ */ jsx(FileText, { size: 16 }), "生成结构化报告"]
									}), /* @__PURE__ */ jsxs(Button, {
										variant: "outline",
										disabled: aiBusy,
										onClick: () => makeHarnessReport("morning-intelligence-plan", {
											themes,
											ladder: ladder.slice(0, 30)
										}),
										children: [aiBusy ? /* @__PURE__ */ jsx(LoaderCircle, {
											className: "spin",
											size: 16
										}) : /* @__PURE__ */ jsx(Sparkles, { size: 16 }), "DeepSeek Harness 复盘"]
									})]
								}),
								/* @__PURE__ */ jsx("p", {
									className: "muted-copy",
									children: "报告按数据日期保存到当前浏览器，刷新页面后仍会保留；Harness 输出作为摘要和风险字段写入同一份报告。"
								}),
								aiError && /* @__PURE__ */ jsx("p", {
									className: "form-error",
									role: "alert",
									children: aiError
								})
							]
						})]
					}) }), /* @__PURE__ */ jsx(Box, {
						title: "报告预览",
						extra: report && /* @__PURE__ */ jsxs(Button, {
							variant: "outline",
							onClick: download,
							children: [/* @__PURE__ */ jsx(Download, { size: 15 }), "下载报告"]
						}),
						children: report ? /* @__PURE__ */ jsx(ReportView, { report }) : /* @__PURE__ */ jsx(Empty, {
							title: "生成一份可追溯的复盘报告",
							body: "报告包含市场概况、指数表、主线候选表、涨停连板候选表和风险下一步。"
						})
					})]
				}),
				/* @__PURE__ */ jsxs("div", {
					className: "section-label",
					children: ["复盘、写作与交付 ", /* @__PURE__ */ jsxs("span", { children: [related.length, " 项技能"] })]
				}),
				skillCards(related)
			] }),
			page === "my-reports" && /* @__PURE__ */ jsxs(Fragment$1, { children: [
				/* @__PURE__ */ jsxs("div", {
					className: "section-intro",
					children: [/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("h2", { children: "我的报告" }), /* @__PURE__ */ jsx("p", { children: "每次本地复盘、Harness 复盘、技能研究和个股研究都会保存在此浏览器。刷新页面不会丢失。" })] }), /* @__PURE__ */ jsxs("div", {
						className: "big-count",
						children: [archiveRows.length, /* @__PURE__ */ jsx("small", { children: "份" })]
					})]
				}),
				/* @__PURE__ */ jsx(Box, {
					title: "已生成报告",
					extra: /* @__PURE__ */ jsx("span", {
						className: "subtle",
						children: "按生成时间排序 · 最多保留 100 份"
					}),
					children: archiveRows.length ? /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
						/* @__PURE__ */ jsx(TableHead, { children: "报告" }),
						/* @__PURE__ */ jsx(TableHead, { children: "类型" }),
						/* @__PURE__ */ jsx(TableHead, { children: "数据日期" }),
						/* @__PURE__ */ jsx(TableHead, { children: "生成时间" }),
						/* @__PURE__ */ jsx(TableHead, { children: "操作" })
					] }) }), /* @__PURE__ */ jsx(TableBody, { children: archiveRows.map((item) => /* @__PURE__ */ jsxs(TableRow, { children: [
						/* @__PURE__ */ jsxs(TableCell, { children: [/* @__PURE__ */ jsx("b", { children: item.title }), /* @__PURE__ */ jsxs("small", {
							className: "table-sub",
							children: [
								item.generatedBy,
								" · ",
								item.summary.slice(0, 62),
								item.summary.length > 62 ? "…" : ""
							]
						})] }),
						/* @__PURE__ */ jsx(TableCell, { children: /* @__PURE__ */ jsx("span", {
							className: item.content.kind === "harness-task" && String(item.content.status || "") !== "completed" ? "status-warning" : "status-good",
							children: item.content.kind === "harness-task" && String(item.content.status || "") !== "completed" ? `未完成 · ${item.reportType}` : item.reportType
						}) }),
						/* @__PURE__ */ jsx(TableCell, { children: d(item.date) }),
						/* @__PURE__ */ jsx(TableCell, { children: new Date(item.updatedAt || item.createdAt).toLocaleString("zh-CN", { hour12: false }) }),
						/* @__PURE__ */ jsxs(TableCell, {
							className: "archive-actions",
							children: [/* @__PURE__ */ jsxs(Button, {
								variant: "outline",
								size: "sm",
								onClick: () => setOpenedArchive(item),
								children: [/* @__PURE__ */ jsx(FileText, { size: 14 }), "查看"]
							}), /* @__PURE__ */ jsx("button", {
								className: "archive-delete",
								"aria-label": `删除 ${item.title}`,
								onClick: () => /* @__PURE__ */ deleteArchivedReport(item.id),
								children: /* @__PURE__ */ jsx(Trash2, { size: 15 })
							})]
						})
					] }, item.id)) })] }) : /* @__PURE__ */ jsx(Empty, {
						title: "还没有生成报告",
						body: "从“复盘与报告”生成市场报告，或从任一技能运行 Harness 后，这里会自动归档。"
					})
				}),
				/* @__PURE__ */ jsx(Sheet, {
					open: !!openedArchive,
					onOpenChange: (open) => !open && setOpenedArchive(null),
					children: /* @__PURE__ */ jsxs(SheetContent, {
						className: "archive-sheet",
						children: [/* @__PURE__ */ jsxs(SheetHeader, { children: [/* @__PURE__ */ jsx(SheetTitle, { children: openedArchive?.title }), /* @__PURE__ */ jsxs(SheetDescription, { children: [
							openedArchive?.reportType,
							" · ",
							openedArchive ? d(openedArchive.date) : "",
							" · ",
							openedArchive?.generatedBy
						] })] }), openedArchive && /* @__PURE__ */ jsx("div", {
							className: "detail-body",
							children: openedArchive.content.kind === "market-report" && openedArchive.content.report ? /* @__PURE__ */ jsx(ReportView, { report: openedArchive.content.report }) : openedArchive.content.kind === "stock-research" ? /* @__PURE__ */ jsx(ArchivedStockReport, { item: openedArchive }) : /* @__PURE__ */ jsx(HarnessOutput, {
								raw: openedArchive.raw || openedArchive.summary,
								compact: false,
								structured: openedArchive.content.structured
							})
						})]
					})
				})
			] }),
			page === "capital" && /* @__PURE__ */ jsxs(Fragment$1, { children: [
				/* @__PURE__ */ jsxs(Tabs, {
					defaultValue: "lhb",
					className: "workspace-tabs capital-tabs",
					children: [
						/* @__PURE__ */ jsxs(TabsList, {
							className: "workspace-tabs-list",
							children: [
								/* @__PURE__ */ jsx(TabsTrigger, {
									value: "lhb",
									children: "龙虎榜"
								}),
								/* @__PURE__ */ jsx(TabsTrigger, {
									value: "youzi",
									children: "游资追踪"
								}),
								/* @__PURE__ */ jsx(TabsTrigger, {
									value: "institution",
									children: "机构与庄家"
								})
							]
						}),
						/* @__PURE__ */ jsx(TabsContent, {
							value: "lhb",
							children: /* @__PURE__ */ jsxs(Box, {
								title: "龙虎榜资金席位",
								extra: /* @__PURE__ */ jsxs(Button, {
									variant: "outline",
									size: "sm",
									onClick: () => setCapitalRefreshNonce((value) => value + 1),
									disabled: capitalLoading,
									children: [capitalLoading ? /* @__PURE__ */ jsx(LoaderCircle, {
										className: "spin",
										size: 14
									}) : /* @__PURE__ */ jsx(RefreshCw, { size: 14 }), "刷新龙虎榜"]
								}),
								children: [
									/* @__PURE__ */ jsxs("div", {
										className: "capital-source-meta",
										children: [/* @__PURE__ */ jsx("span", { children: capitalLoading ? "正在读取 Harness 落盘数据…" : `数据日 ${d(capitalSnapshot?.date || market.date)} · ${capitalRows.length} 条龙虎榜记录` }), /* @__PURE__ */ jsx("small", { children: capitalSnapshot?.fetchedAt ? `同步于 ${new Date(capitalSnapshot.fetchedAt).toLocaleTimeString("zh-CN", { hour12: false })}` : "等待最新快照" })]
									}),
									capitalRows.length ? /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
										/* @__PURE__ */ jsx(TableHead, { children: "股票" }),
										/* @__PURE__ */ jsx(TableHead, { children: "净买额" }),
										/* @__PURE__ */ jsx(TableHead, { children: "买入额" }),
										/* @__PURE__ */ jsx(TableHead, { children: "卖出额" }),
										/* @__PURE__ */ jsx(TableHead, { children: "上榜原因" })
									] }) }), /* @__PURE__ */ jsx(TableBody, { children: capitalRows.slice(0, 20).map((row, i) => /* @__PURE__ */ jsxs(TableRow, { children: [
										/* @__PURE__ */ jsxs(TableCell, { children: [/* @__PURE__ */ jsx("b", { children: row.name }), /* @__PURE__ */ jsx("small", { children: row.code })] }),
										/* @__PURE__ */ jsx(TableCell, {
											className: row.net >= 0 ? "up" : "down",
											children: money(row.net)
										}),
										/* @__PURE__ */ jsx(TableCell, { children: money(row.buy) }),
										/* @__PURE__ */ jsx(TableCell, { children: money(row.sell) }),
										/* @__PURE__ */ jsx(TableCell, { children: row.reason })
									] }, `${row.code}-${i}`)) })] }) : /* @__PURE__ */ jsx(Empty, {
										title: "等待龙虎榜数据源",
										body: "公开行情快照尚未返回龙虎榜记录，请稍后重试数据更新。"
									}),
									capitalHarnessOutput && /* @__PURE__ */ jsxs("div", {
										className: "capital-harness-report",
										children: [/* @__PURE__ */ jsx("h4", { children: "Harness 资金数据校验" }), /* @__PURE__ */ jsx(HarnessOutput, { raw: capitalHarnessOutput })]
									})
								]
							})
						}),
						/* @__PURE__ */ jsx(TabsContent, {
							value: "youzi",
							children: /* @__PURE__ */ jsxs(Box, {
								title: "游资追踪",
								extra: /* @__PURE__ */ jsx("span", {
									className: "status-warning",
									children: "部分数据待接入"
								}),
								children: [/* @__PURE__ */ jsxs("div", {
									className: "capital-gap-grid",
									children: [
										/* @__PURE__ */ jsxs("div", {
											className: "capital-gap-card ready",
											children: [/* @__PURE__ */ jsx(Check, { size: 16 }), /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: "龙虎榜上榜记录" }), /* @__PURE__ */ jsx("small", { children: "已接入同日 59 条公开记录" })] })]
										}),
										/* @__PURE__ */ jsxs("div", {
											className: "capital-gap-card missing",
											children: [/* @__PURE__ */ jsx(X, { size: 16 }), /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: "营业部 / 游资身份映射" }), /* @__PURE__ */ jsx("small", { children: "缺少席位名称到游资标签的核验表" })] })]
										}),
										/* @__PURE__ */ jsxs("div", {
											className: "capital-gap-card missing",
											children: [/* @__PURE__ */ jsx(X, { size: 16 }), /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: "席位买卖明细" }), /* @__PURE__ */ jsx("small", { children: "公开快照只有个股买卖汇总，没有席位逐笔明细" })] })]
										}),
										/* @__PURE__ */ jsxs("div", {
											className: "capital-gap-card missing",
											children: [/* @__PURE__ */ jsx(X, { size: 16 }), /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: "连续交易日跟踪" }), /* @__PURE__ */ jsx("small", { children: "缺少同一席位的多日净买、锁仓和接力统计" })] })]
										}),
										/* @__PURE__ */ jsxs("div", {
											className: "capital-gap-card missing",
											children: [/* @__PURE__ */ jsx(X, { size: 16 }), /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: "TQ / L2 主力公式" }), /* @__PURE__ */ jsx("small", { children: "本机公式授权与实时资金字段尚未验证" })] })]
										}),
										/* @__PURE__ */ jsxs("div", {
											className: "capital-gap-card missing",
											children: [/* @__PURE__ */ jsx(X, { size: 16 }), /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: "盘中逐笔与封单" }), /* @__PURE__ */ jsx("small", { children: "当前只有收盘日线和 OHLC 触板代理" })] })]
										})
									]
								}), /* @__PURE__ */ jsxs("div", {
									className: "content-pad capital-next-step",
									children: [/* @__PURE__ */ jsx("b", { children: "补全条件" }), /* @__PURE__ */ jsx("p", { children: "需要席位明细源、游资身份映射表、同席位多日历史，以及 TQ/L2 授权后的资金公式快照。接入后，Harness 才会生成游资净买、接力路径和活跃度变化。" })]
								})]
							})
						}),
						/* @__PURE__ */ jsx(TabsContent, {
							value: "institution",
							children: /* @__PURE__ */ jsx(Box, {
								title: "机构与庄家资金",
								children: /* @__PURE__ */ jsx(Empty, {
									title: "等待本机公式与 TQ 验证",
									body: "当前不把成交额冒充资金净流入。"
								})
							})
						})
					]
				}),
				/* @__PURE__ */ jsxs("div", {
					className: "section-label",
					children: ["资金研究技能 ", /* @__PURE__ */ jsxs("span", { children: [related.length, " 项技能"] })]
				}),
				skillCards(related)
			] }),
			page === "settings" && /* @__PURE__ */ jsxs(Fragment$1, { children: [
				/* @__PURE__ */ jsx(Box, {
					title: "运行环境检测",
					extra: /* @__PURE__ */ jsxs(Button, {
						variant: "outline",
						onClick: refreshEnvironment,
						disabled: environmentLoading,
						children: [environmentLoading ? /* @__PURE__ */ jsx(LoaderCircle, {
							className: "spin",
							size: 14
						}) : /* @__PURE__ */ jsx(RefreshCw, { size: 14 }), "重新检测"]
					}),
					children: /* @__PURE__ */ jsxs("div", {
						className: "content-pad environment-panel",
						children: [
							/* @__PURE__ */ jsxs("div", {
								className: "environment-grid",
								children: [
									/* @__PURE__ */ jsxs("div", {
										className: `environment-card ${environmentTdx.status === "open" ? "ready" : "warn"}`,
										children: [
											/* @__PURE__ */ jsx(Database, { size: 20 }),
											/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: "通达信客户端" }), /* @__PURE__ */ jsx("small", { children: environmentTdx.status === "open" ? "进程已打开，可调用 TQ" : "未检测到 TdxW 进程" })] }),
											environmentTdx.status === "open" ? /* @__PURE__ */ jsx("strong", { children: "已打开" }) : /* @__PURE__ */ jsx(Button, {
												variant: "outline",
												size: "sm",
												onClick: openTongdaxin,
												children: "打开通达信"
											})
										]
									}),
									/* @__PURE__ */ jsxs("div", {
										className: `environment-card ${environmentDaily.updateDue === true || environmentDaily.complete !== true ? "warn" : "ready"}`,
										children: [
											/* @__PURE__ */ jsx(Database, { size: 20 }),
											/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: "日线完整性" }), /* @__PURE__ */ jsxs("small", { children: [
												"最新 ",
												d(String(environmentDaily.latestDate || "")),
												" · ",
												String(environmentDaily.latestCount || 0),
												" 只",
												environmentDaily.freshnessMessage ? ` · ${String(environmentDaily.freshnessMessage)}` : ""
											] })] }),
											/* @__PURE__ */ jsx("strong", { children: environmentDaily.updateDue === true ? "需更新" : environmentDaily.complete === true ? "完整" : "需补全" })
										]
									}),
									/* @__PURE__ */ jsxs("div", {
										className: `environment-card ${environmentHarness.status === "ready" ? "ready" : "warn"}`,
										children: [
											/* @__PURE__ */ jsx(Workflow, { size: 20 }),
											/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: "本地 14 技能桥接" }), /* @__PURE__ */ jsxs("small", { children: [
												environmentHarness.base ? String(environmentHarness.base) : "本地数据预检服务",
												" · ",
												bridgeHostLabel()
											] })] }),
											/* @__PURE__ */ jsx("strong", { children: environmentHarness.status === "ready" ? "已就绪" : "需配置" })
										]
									}),
									/* @__PURE__ */ jsxs("div", {
										className: `environment-card ${["completed", "running"].includes(unifiedArchiveStatus) ? "ready" : "warn"}`,
										children: [
											/* @__PURE__ */ jsx(Layers, { size: 20 }),
											/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: "统一落盘与校验" }), /* @__PURE__ */ jsxs("small", { children: [
												"落盘 ",
												unifiedArchiveBadge,
												" · 校验 ",
												String(environmentUnifiedVerification.status || "未执行")
											] })] }),
											/* @__PURE__ */ jsx("strong", { children: unifiedArchiveBadge })
										]
									})
								]
							}),
							environmentSnapshot && /* @__PURE__ */ jsxs("div", {
								className: "environment-details",
								children: [
									/* @__PURE__ */ jsxs("span", { children: [
										"沪 ",
										String(environmentDaily.directories?.SH ? environmentDaily.directories.SH.fileCount || 0 : 0),
										" 文件"
									] }),
									/* @__PURE__ */ jsxs("span", { children: [
										"深 ",
										String(environmentDaily.directories?.SZ?.fileCount || 0),
										" 文件"
									] }),
									/* @__PURE__ */ jsxs("span", { children: [
										"北 ",
										String(environmentDaily.directories?.BJ?.fileCount || 0),
										" 文件"
									] }),
									/* @__PURE__ */ jsxs("span", { children: ["数据目录 ", environmentTdx.root ? String(environmentTdx.root) : "未配置"] }),
									/* @__PURE__ */ jsxs("span", { children: ["日线状态 ", String(environmentDailyState.status || "未执行")] }),
									/* @__PURE__ */ jsxs("span", { children: ["日线时效 ", environmentDaily.updateDue === true ? "收盘后待更新" : "已与最新交易日核对"] }),
									/* @__PURE__ */ jsxs("span", { children: [
										"日线索引 ",
										String(environmentDailyIndex.status || "未生成"),
										" · 降级 ",
										String(environmentDailyIndexSummary.fallback_symbol_count || 0),
										" 股/",
										String(environmentDailyIndexSummary.fallback_record_count || 0),
										" 条"
									] }),
									/* @__PURE__ */ jsxs("span", { children: [
										"全历史索引 ",
										String(environmentCanonicalIndex.status || "未生成"),
										" · ",
										String(environmentCanonicalIndex.symbolCount || 0),
										" 股/",
										String(environmentCanonicalIndex.recordCount || 0),
										" 条"
									] }),
									/* @__PURE__ */ jsxs("span", { children: ["索引初始化 ", String(environmentIndexInitialization.status || "未执行")] }),
									/* @__PURE__ */ jsxs("span", { children: ["其他数据任务 ", String(environmentSupplementalState.status || "未执行")] }),
									/* @__PURE__ */ jsxs("span", { children: [
										"补充覆盖：财务 ",
										environmentSupplemental.coverage && environmentSupplemental.coverage.financial ? "按需可用" : "按需",
										" · 股本 ",
										environmentSupplemental.coverage && environmentSupplemental.coverage.share_capital ? "已取" : "按需",
										" · 指数 ",
										String(environmentSupplemental.indexSymbolCount || 0),
										" 组 · 龙虎榜 ",
										String(environmentSupplemental.lhbMarketRecordCount || environmentSupplemental.lhbRecordCount || 0),
										" 条 · 融资融券 ",
										String(environmentSupplemental.marginRecordCount || 0),
										" 条"
									] })
								]
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "environment-validation",
								children: [
									/* @__PURE__ */ jsx("b", { children: "统一落盘计划" }),
									"：每个交易日收盘后 16:30（Asia/Shanghai）自动执行日线、行情、资讯、公式证据和本地来源清单归档；周末及交易所闭市日跳过，并以本地交易日历和实际数据日期为准。当前清单 ",
									d(String(environmentSourceManifest.tradeDate || "")),
									"，已落盘来源 ",
									String(environmentSourceManifest.availableSourceCount || 0),
									"/",
									String(environmentSourceManifest.sourceCount || 0),
									"。日线归档：",
									String(environmentDailyArchive.archive_mode || "unknown"),
									"，本次新增 ",
									String(environmentDailyArchive.incremental_records || 0),
									" 条；统一落盘：",
									unifiedArchiveBadge,
									"；校验：",
									String(environmentUnifiedVerification.status || "未执行"),
									"。"
								]
							}),
							environmentRunningStep && /* @__PURE__ */ jsxs("div", {
								className: "environment-validation",
								children: [
									"当前数据刷新步骤：",
									String(environmentRunningStep.name || "日线补全"),
									" · 已在后台运行，页面可继续使用"
								]
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "environment-source-list unified-archive-run-card",
								children: [
									/* @__PURE__ */ jsxs("div", {
										className: "environment-source-title",
										children: [/* @__PURE__ */ jsx("b", { children: "统一落盘运行状态" }), /* @__PURE__ */ jsxs("small", { children: [
											"状态 JSON、Harness 上下文和 HTML 报告全部保存在 ",
											runtimeStorageLabel,
											" 内"
										] })]
									}),
									/* @__PURE__ */ jsxs("div", {
										className: "environment-details",
										children: [
											/* @__PURE__ */ jsxs("span", { children: ["状态 ", /* @__PURE__ */ jsx("strong", { children: unifiedArchiveBadge })] }),
											/* @__PURE__ */ jsxs("span", { children: [
												"步骤 ",
												unifiedArchiveProgress,
												"/",
												unifiedArchiveTotal
											] }),
											/* @__PURE__ */ jsxs("span", { children: ["日期 ", d(String(environmentUnifiedArchive.date || ""))] }),
											/* @__PURE__ */ jsxs("span", { children: ["开始 ", environmentUnifiedArchive.startedAt ? new Date(String(environmentUnifiedArchive.startedAt)).toLocaleString("zh-CN", { hour12: false }) : "—"] }),
											/* @__PURE__ */ jsxs("span", { children: ["结束 ", environmentUnifiedArchive.finishedAt ? new Date(String(environmentUnifiedArchive.finishedAt)).toLocaleString("zh-CN", { hour12: false }) : "—"] })
										]
									}),
									unifiedArchiveActiveStep && /* @__PURE__ */ jsxs("div", {
										className: "environment-validation",
										children: [
											"正在执行：",
											String(unifiedArchiveActiveStep.name || "准备下一步"),
											" · 完成后自动更新报告"
										]
									}),
									unifiedArchiveSteps.length > 0 && /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
										/* @__PURE__ */ jsx(TableHead, { children: "步骤" }),
										/* @__PURE__ */ jsx(TableHead, { children: "状态" }),
										/* @__PURE__ */ jsx(TableHead, { children: "返回码" }),
										/* @__PURE__ */ jsx(TableHead, { children: "结果" })
									] }) }), /* @__PURE__ */ jsx(TableBody, { children: unifiedArchiveSteps.map((step, index) => /* @__PURE__ */ jsxs(TableRow, { children: [
										/* @__PURE__ */ jsx(TableCell, { children: String(step.name || "未命名步骤") }),
										/* @__PURE__ */ jsx(TableCell, {
											className: step.status === "completed" ? "up" : step.status === "running" ? "" : "down",
											children: String(step.status || "pending")
										}),
										/* @__PURE__ */ jsx(TableCell, { children: step.code === void 0 || step.code === null ? "—" : String(step.code) }),
										/* @__PURE__ */ jsx(TableCell, { children: step.error ? String(step.error).slice(-160) : step.status === "running" ? "执行中" : step.resultStored || step.resultPath ? "结果已单独落盘" : "已完成" })
									] }, `${String(step.name || "step")}-${index}`)) })] }),
									/* @__PURE__ */ jsxs("div", {
										className: "environment-actions",
										children: [/* @__PURE__ */ jsxs(Button, {
											variant: "outline",
											onClick: () => window.open(unifiedArchiveReportUrl, "_blank", "noopener,noreferrer"),
											disabled: !unifiedArchiveReport.htmlUrl && unifiedArchiveStatus === "未执行",
											children: [/* @__PURE__ */ jsx(ArrowUpRight, { size: 15 }), "查看运行报告"]
										}), /* @__PURE__ */ jsxs("span", { children: [unifiedArchiveReport.relativeHtml ? `HTML：${String(unifiedArchiveReport.relativeHtml)}` : "报告将在任务启动后生成", unifiedArchiveHarness.status ? ` · Harness：${String(unifiedArchiveHarness.status)}` : ""] })]
									})
								]
							}),
							environmentSources.length > 0 && /* @__PURE__ */ jsxs("div", {
								className: "environment-source-list",
								children: [
									/* @__PURE__ */ jsxs("div", {
										className: "environment-source-title",
										children: [/* @__PURE__ */ jsx("b", { children: "其他数据源新鲜度" }), /* @__PURE__ */ jsx("small", { children: "来源快照与 Harness 校验结果" })]
									}),
									/* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
										/* @__PURE__ */ jsx(TableHead, { children: "数据源" }),
										/* @__PURE__ */ jsx(TableHead, { children: "状态" }),
										/* @__PURE__ */ jsx(TableHead, { children: "日期" }),
										/* @__PURE__ */ jsx(TableHead, { children: "记录" }),
										/* @__PURE__ */ jsx(TableHead, { children: "校验" })
									] }) }), /* @__PURE__ */ jsx(TableBody, { children: environmentSources.map((source, index) => {
										const name = String(source.name || `source-${index}`);
										const fresh = source.fresh === true;
										return /* @__PURE__ */ jsxs(TableRow, { children: [
											/* @__PURE__ */ jsx(TableCell, { children: dataSourceLabels[name] || name }),
											/* @__PURE__ */ jsx(TableCell, {
												className: source.status === "available" ? "up" : "down",
												children: source.status === "available" ? "可用" : String(source.status || "缺失")
											}),
											/* @__PURE__ */ jsx(TableCell, { children: d(String(source.date || "")) }),
											/* @__PURE__ */ jsx(TableCell, { children: source.recordCount === null || source.recordCount === void 0 ? "—" : String(source.recordCount) }),
											/* @__PURE__ */ jsx(TableCell, {
												className: fresh ? "up" : "down",
												children: fresh ? "同日最新" : "需复核"
											})
										] }, `${name}-${index}`);
									}) })] }),
									/* @__PURE__ */ jsxs("div", {
										className: "environment-validation",
										children: [
											"Harness 校验：",
											String(environmentValidation.status || "未执行"),
											" · 数据日 ",
											d(String(environmentValidation.dataDate || environmentDaily.date || "")),
											environmentValidation.summary ? ` · ${String(environmentValidation.summary).slice(0, 120)}` : ""
										]
									})
								]
							}),
							environmentSourceRows.length > 0 && /* @__PURE__ */ jsxs("div", {
								className: "environment-source-list",
								children: [/* @__PURE__ */ jsxs("div", {
									className: "environment-source-title",
									children: [/* @__PURE__ */ jsx("b", { children: "统一数据源落盘清单" }), /* @__PURE__ */ jsx("small", { children: "压缩包声明来源、当前实际快照和降级状态均写入本地，Harness 只使用可用文件" })]
								}), /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
									/* @__PURE__ */ jsx(TableHead, { children: "来源" }),
									/* @__PURE__ */ jsx(TableHead, { children: "数据层" }),
									/* @__PURE__ */ jsx(TableHead, { children: "状态" }),
									/* @__PURE__ */ jsx(TableHead, { children: "说明" })
								] }) }), /* @__PURE__ */ jsx(TableBody, { children: environmentSourceRows.map((source, index) => {
									const sourceId = String(source.id || source.name || `source-${index}`);
									const sourceStatus = String(source.status || "missing");
									const statusText = sourceStatus === "available" ? "已落盘" : sourceStatus === "partial" ? "部分落盘" : sourceStatus === "declared_not_snapshotted" ? "仅声明未快照" : sourceStatus === "not_configured" ? "未配置" : sourceStatus === "blocked" ? "需凭据/受阻" : sourceStatus;
									return /* @__PURE__ */ jsxs(TableRow, { children: [
										/* @__PURE__ */ jsx(TableCell, { children: dataSourceLabels[sourceId] || String(source.name || sourceId) }),
										/* @__PURE__ */ jsx(TableCell, { children: String(source.layer || "—") }),
										/* @__PURE__ */ jsx(TableCell, {
											className: sourceStatus === "available" ? "up" : "down",
											children: statusText
										}),
										/* @__PURE__ */ jsx(TableCell, { children: String(source.reason || "—") })
									] }, `${sourceId}-${index}`);
								}) })] })]
							}),
							environmentIntegrityAfter.stockCount !== void 0 && /* @__PURE__ */ jsxs("div", {
								className: "environment-source-list",
								children: [
									/* @__PURE__ */ jsxs("div", {
										className: "environment-source-title",
										children: [/* @__PURE__ */ jsx("b", { children: "个股日线完整性报告" }), /* @__PURE__ */ jsx("small", { children: "按 TQ 股票清单逐代码核验 .day 文件最后一条记录，并用公开历史 K 线作缺口兜底" })]
									}),
									/* @__PURE__ */ jsxs("div", {
										className: "environment-details",
										children: [
											/* @__PURE__ */ jsxs("span", { children: ["目标交易日 ", d(String(environmentIntegrity.targetDate || environmentIntegrityAfter.targetDate || ""))] }),
											/* @__PURE__ */ jsxs("span", { children: [
												"应有 ",
												String(environmentIntegrityAfter.stockCount || 0),
												" 只"
											] }),
											/* @__PURE__ */ jsxs("span", { children: [
												"文件已齐 ",
												String(environmentIntegrityAfter.completeCount || 0),
												" 只"
											] }),
											/* @__PURE__ */ jsxs("span", {
												className: "up",
												children: [
													"未上市/停牌计入 ",
													environmentIntegrityNonTrading.length,
													" 只"
												]
											}),
											/* @__PURE__ */ jsxs("span", {
												className: environmentIntegrityUnresolvedCount ? "down" : "up",
												children: [
													"仍需补齐 ",
													environmentIntegrityUnresolvedCount,
													" 只"
												]
											}),
											/* @__PURE__ */ jsxs("span", {
												className: "up",
												children: [
													"本次补写 ",
													environmentIntegrityRepairedCount,
													" 条"
												]
											})
										]
									}),
									environmentIntegrityUnresolved.length > 0 && /* @__PURE__ */ jsxs(Fragment$1, { children: [/* @__PURE__ */ jsx("div", {
										className: "subtle",
										children: "以下仅展示前 10 条，完整清单保存在本地完整性报告中。"
									}), /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
										/* @__PURE__ */ jsx(TableHead, { children: "代码" }),
										/* @__PURE__ */ jsx(TableHead, { children: "市场" }),
										/* @__PURE__ */ jsx(TableHead, { children: "状态" }),
										/* @__PURE__ */ jsx(TableHead, { children: "说明" })
									] }) }), /* @__PURE__ */ jsx(TableBody, { children: environmentIntegrityUnresolved.map((item, index) => /* @__PURE__ */ jsxs(TableRow, { children: [
										/* @__PURE__ */ jsx(TableCell, { children: String(item.code || "—") }),
										/* @__PURE__ */ jsx(TableCell, { children: String(item.market || "—") }),
										/* @__PURE__ */ jsx(TableCell, {
											className: "down",
											children: "未补齐"
										}),
										/* @__PURE__ */ jsxs(TableCell, { children: [
											"TQ 与公开历史 K 线均未返回 ",
											d(String(environmentIntegrity.targetDate || environmentIntegrityAfter.targetDate || "")),
											" 数据"
										] })
									] }, `${String(item.code || "unknown")}-${index}`)) })] })] }),
									environmentIntegrityNonTrading.length > 0 && /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
										/* @__PURE__ */ jsx(TableHead, { children: "代码" }),
										/* @__PURE__ */ jsx(TableHead, { children: "处理" }),
										/* @__PURE__ */ jsx(TableHead, { children: "依据" })
									] }) }), /* @__PURE__ */ jsx(TableBody, { children: environmentIntegrityNonTrading.map((item, index) => /* @__PURE__ */ jsxs(TableRow, { children: [
										/* @__PURE__ */ jsx(TableCell, { children: String(item.code || "—") }),
										/* @__PURE__ */ jsx(TableCell, {
											className: "up",
											children: String(item.type || "non_trading") === "unlisted" ? "未上市，计入完整" : "停牌/无交易，计入完整"
										}),
										/* @__PURE__ */ jsx(TableCell, { children: String(item.reason || "目标交易日无成交记录") })
									] }, `${String(item.code || "non-trading")}-${index}`)) })] })
								]
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "environment-validation environment-manual-guide",
								children: [
									/* @__PURE__ */ jsx("b", { children: "日线补齐操作顺序" }),
									/* @__PURE__ */ jsx("br", {}),
									/* @__PURE__ */ jsx("span", { children: "① 优先进入通达信客户端并登录，执行“盘后数据下载/日线数据下载”。" }),
									/* @__PURE__ */ jsx("br", {}),
									/* @__PURE__ */ jsx("span", { children: "② 点击“通过 Harness 补全通达信日线”，先核验 TDX 并增量写入；若 TDX 断开，系统自动将公开源精确交易日 OHLCV 写入日线降级层和索引。" }),
									/* @__PURE__ */ jsx("br", {}),
									/* @__PURE__ */ jsx("strong", { children: "公开降级层只补明确缺失日期，保持 degraded 标记；不能替代 TDX 全历史或 TQ 公式现场回执。" })
								]
							}),
							environmentIntegrityManualAction && /* @__PURE__ */ jsx("div", {
								className: "environment-validation",
								children: environmentIntegrityManualAction
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "environment-actions",
								children: [
									/* @__PURE__ */ jsxs(Button, {
										className: "primary-button",
										onClick: archiveAllData,
										disabled: unifiedArchiveRunning,
										children: [unifiedArchiveRunning ? /* @__PURE__ */ jsx(LoaderCircle, {
											className: "spin",
											size: 15
										}) : /* @__PURE__ */ jsx(Download, { size: 15 }), "立即统一落盘（全源）"]
									}),
									/* @__PURE__ */ jsxs(Button, {
										variant: "outline",
										onClick: verifyAllData,
										disabled: unifiedVerificationRunning,
										children: [unifiedVerificationRunning ? /* @__PURE__ */ jsx(LoaderCircle, {
											className: "spin",
											size: 15
										}) : /* @__PURE__ */ jsx(Check, { size: 15 }), "校验落盘并调用 Harness"]
									}),
									/* @__PURE__ */ jsxs(Button, {
										variant: "outline",
										onClick: rebuildAllIndices,
										disabled: indexRebuildRunning || dailyRefreshRunning,
										children: [indexRebuildRunning ? /* @__PURE__ */ jsx(LoaderCircle, {
											className: "spin",
											size: 15
										}) : /* @__PURE__ */ jsx(RefreshCw, { size: 15 }), "初始化并重建全量索引"]
									}),
									/* @__PURE__ */ jsxs(Button, {
										variant: "outline",
										onClick: replenishDailyData,
										disabled: dailyRefreshRunning || indexRebuildRunning,
										children: [dailyRefreshRunning ? /* @__PURE__ */ jsx(LoaderCircle, {
											className: "spin",
											size: 15
										}) : /* @__PURE__ */ jsx(RefreshCw, { size: 15 }), "刷新交易日行情（日线+市场信息）"]
									}),
									/* @__PURE__ */ jsxs(Button, {
										variant: "outline",
										onClick: replenishSupplementalData,
										disabled: supplementalRefreshRunning,
										children: [supplementalRefreshRunning ? /* @__PURE__ */ jsx(LoaderCircle, {
											className: "spin",
											size: 15
										}) : /* @__PURE__ */ jsx(Database, { size: 15 }), "仅补齐其他数据"]
									}),
									/* @__PURE__ */ jsx("span", { children: environmentMessage || "页面打开时检测一次；自动计划在每个交易日收盘后 16:30 落盘。初始化会读取所选通达信目录全部 .day，建立全量个股索引；普通任务不依赖 5 分钟线。" })
								]
							})
						]
					})
				}),
				/* @__PURE__ */ jsx("div", { className: "section-spacer" }),
				/* @__PURE__ */ jsxs("div", {
					className: "two-column",
					children: [/* @__PURE__ */ jsx(Box, {
						title: "本地数据源",
						children: /* @__PURE__ */ jsxs("div", {
							className: "content-pad",
							children: [/* @__PURE__ */ jsxs("div", {
								className: "source-status",
								children: [
									/* @__PURE__ */ jsx(Database, { size: 25 }),
									/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: "通达信日线" }), /* @__PURE__ */ jsx("small", { children: "已读取为当日网页快照" })] }),
									/* @__PURE__ */ jsx("span", {
										className: "status-good",
										children: "已导入"
									})
								]
							}), /* @__PURE__ */ jsxs("dl", {
								className: "settings-list",
								children: [
									/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "行情位置" }), /* @__PURE__ */ jsx("dd", { children: environmentTdx.root ? String(environmentTdx.root) : "未配置" })] }),
									/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "全历史资源库" }), /* @__PURE__ */ jsx("dd", { children: environmentCanonicalIndex.sourceFile ? `${String(environmentCanonicalIndex.sourceFile)} · ${String(environmentCanonicalIndex.symbolCount || 0)} 股` : "未建立，请点击“初始化并重建全量索引”" })] }),
									/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "最新文件日期" }), /* @__PURE__ */ jsx("dd", { children: d(market.date) })] }),
									/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "股票覆盖" }), /* @__PURE__ */ jsxs("dd", { children: [
										market.total,
										" 只 · 同日 ",
										market.currentCount,
										" 只"
									] })] }),
									/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "涨停候选" }), /* @__PURE__ */ jsxs("dd", { children: [
										ladder.length,
										" 只 · 连续候选",
										" ",
										ladder.filter((x) => x.streak > 1).length,
										" 只"
									] })] }),
									/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "TDX行业 / 主题" }), /* @__PURE__ */ jsxs("dd", { children: [
										market.sectors?.length || 0,
										" / ",
										market.conceptBoards?.length || 0,
										" 个聚合榜"
									] })] }),
									/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "盘中数据" }), /* @__PURE__ */ jsxs("dd", { children: [
										market.intradayProxy?.upperHitCount || 0,
										" 只触板 · OHLC代理；5分钟同日 ",
										market.intradayProxy?.lc5CurrentDateCount || 0,
										"/",
										market.intradayProxy?.lc5Files || 0
									] })] }),
									/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "待接入快照" }), /* @__PURE__ */ jsx("dd", { children: "北向资金 · 主力资金 · 当日新闻（融资融券与龙虎榜已接入）" })] })
								]
							})]
						})
					}), /* @__PURE__ */ jsx(Box, {
						title: "DeepSeek Harness",
						children: /* @__PURE__ */ jsxs("div", {
							className: "content-pad",
							children: [/* @__PURE__ */ jsxs("div", {
								className: "source-status",
								children: [
									/* @__PURE__ */ jsx(Workflow, { size: 25 }),
									/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: "DeepSeek Harness" }), /* @__PURE__ */ jsx("small", { children: "本地 headless 桥接" })] }),
									/* @__PURE__ */ jsx("span", {
										className: "status-good",
										children: "已接入"
									})
								]
							}), /* @__PURE__ */ jsxs("dl", {
								className: "settings-list",
								children: [
									/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "受控技能包" }), /* @__PURE__ */ jsx("dd", { children: "14 项" })] }),
									/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "网页桥接" }), /* @__PURE__ */ jsx("dd", { children: bridgeHostLabel() })] }),
									/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "密钥保存" }), /* @__PURE__ */ jsx("dd", { children: "仅环境变量" })] }),
									/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "报告保存" }), /* @__PURE__ */ jsx("dd", { children: "浏览器 localStorage" })] })
								]
							})]
						})
					})]
				}),
				/* @__PURE__ */ jsxs("div", {
					className: "section-label",
					children: ["系统与数据能力 ", /* @__PURE__ */ jsxs("span", { children: [related.length, " 项"] })]
				}),
				skillCards(related)
			] }),
			/* @__PURE__ */ jsx(Sheet, {
				open: !!skill,
				onOpenChange: (open) => !open && setSkill(null),
				children: /* @__PURE__ */ jsxs(SheetContent, {
					className: "skill-sheet",
					children: [/* @__PURE__ */ jsxs(SheetHeader, { children: [/* @__PURE__ */ jsx(SheetTitle, { children: skill?.name }), /* @__PURE__ */ jsxs(SheetDescription, { children: [
						"统一技能入口 · ",
						skill?.id,
						" · 当日数据 ",
						d(market.date)
					] })] }), skill && /* @__PURE__ */ jsxs("div", {
						className: "detail-body",
						children: [
							/* @__PURE__ */ jsx("p", {
								className: "skill-introduction",
								children: skillIntroduction(skill)
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "skill-original-meta",
								children: [
									/* @__PURE__ */ jsx("b", { children: "原始技能 ID：" }),
									skill.id,
									/* @__PURE__ */ jsx("br", {}),
									/* @__PURE__ */ jsx("b", { children: "原始别名：" }),
									skill.alias,
									/* @__PURE__ */ jsx("br", {}),
									/* @__PURE__ */ jsx("b", { children: "迁移说明：" }),
									skill.note
								]
							}),
							skill.group === "selection" && strategyCatalogItem(skill.id) && (() => {
								const catalog = strategyCatalogItem(skill.id);
								return /* @__PURE__ */ jsxs("div", {
									className: "skill-original-meta",
									children: [
										/* @__PURE__ */ jsx("b", { children: "数据状态：" }),
										catalog.dataStatus === "available" ? "可用" : catalog.dataStatus === "partial" ? "部分缺口" : "缺失，已置灰",
										/* @__PURE__ */ jsx("br", {}),
										/* @__PURE__ */ jsx("b", { children: "业务入口：" }),
										catalog.businessEntry,
										/* @__PURE__ */ jsx("br", {}),
										/* @__PURE__ */ jsx("b", { children: "业务代码指纹：" }),
										catalog.businessHash.slice(0, 16),
										"…",
										/* @__PURE__ */ jsx("br", {}),
										/* @__PURE__ */ jsx("b", { children: "执行方式：" }),
										"网页脚本 + DeepSeek Harness",
										catalog.minuteData?.mode === "optional_degraded" && /* @__PURE__ */ jsxs(Fragment$1, { children: [
											/* @__PURE__ */ jsx("br", {}),
											/* @__PURE__ */ jsx("b", { children: "5 分钟线：" }),
											"外部按需读取；缺少时标记 DEGRADED，不进入 EXE"
										] }),
										catalog.missingData.length > 0 && /* @__PURE__ */ jsxs(Fragment$1, { children: [
											/* @__PURE__ */ jsx("br", {}),
											/* @__PURE__ */ jsx("b", { children: "缺少数据：" }),
											catalog.missingData.join("、")
										] })
									]
								});
							})(),
							/* @__PURE__ */ jsxs("div", {
								className: "skill-detail-id",
								children: [/* @__PURE__ */ jsx("b", { children: "依赖：" }), skill.dependencies.join(" · ")]
							}),
							skillMode(skill.id) === "basic" ? /* @__PURE__ */ jsxs(Fragment$1, { children: [
								/* @__PURE__ */ jsxs("div", {
									className: "skill-detail-status skill-detail-status-basic",
									children: [
										/* @__PURE__ */ jsx("b", { children: "基础技能 · 仅展示详情" }),
										/* @__PURE__ */ jsx("br", {}),
										"该能力用于说明系统的数据接入、质量规则和内部支撑边界，不是一次性分析任务。本页不会生成本地预检，不会启动 Harness，也不会写入运行报告。"
									]
								}),
								/* @__PURE__ */ jsx("div", {
									className: "detail-title",
									children: "技能详情"
								}),
								/* @__PURE__ */ jsx("p", {
									className: "muted-copy",
									children: skill.note
								}),
								/* @__PURE__ */ jsx("p", {
									className: "harness-eta",
									children: "如需运行具体分析，请进入对应的行情、策略或个股研究技能；基础能力本身只作为网页端可核验的能力说明。"
								})
							] }) : /* @__PURE__ */ jsxs(Fragment$1, { children: [
								/* @__PURE__ */ jsx("div", {
									className: "detail-title",
									children: "执行说明"
								}),
								/* @__PURE__ */ jsx("p", {
									className: "muted-copy",
									children: "网页适配层先生成本地数据预检与落盘运行单；随后可把同一份预检和当日行情交给对应技能的 Harness。缺数据时仍允许调用，但只返回阻塞诊断或降级报告。"
								}),
								/* @__PURE__ */ jsx("p", {
									className: "harness-eta",
									children: "预检不调用模型、不补造数据，也不把预检结果写成策略结论。预检回执写入应用数据目录；Harness 任务与结果也会由桥接服务落盘。"
								}),
								/* @__PURE__ */ jsxs("div", {
									className: "action-row",
									children: [/* @__PURE__ */ jsxs(Button, {
										className: "primary-button",
										disabled: skillBusy || skillHarnessBusy,
										onClick: () => runSkill(skill),
										children: [skillBusy ? /* @__PURE__ */ jsx(LoaderCircle, {
											className: "spin",
											size: 15
										}) : /* @__PURE__ */ jsx(Database, { size: 15 }), skillBusy ? "生成预检中…" : "生成本地数据预检"]
									}), /* @__PURE__ */ jsxs(Button, {
										variant: "outline",
										disabled: skillBusy || skillHarnessBusy || aiBusy,
										onClick: () => runSkillHarness(skill),
										children: [skillHarnessBusy ? /* @__PURE__ */ jsx(LoaderCircle, {
											className: "spin",
											size: 15
										}) : /* @__PURE__ */ jsx(Sparkles, { size: 15 }), skillHarnessBusy ? "Harness 运行中…" : "调用 Harness"]
									})]
								}),
								skillOutput && /* @__PURE__ */ jsx("div", {
									className: "strategy-run-output ready",
									children: /* @__PURE__ */ jsx("pre", { children: skillOutput })
								}),
								skillHarnessError && /* @__PURE__ */ jsx("p", {
									className: "form-error",
									role: "alert",
									children: skillHarnessError
								}),
								skillHarnessOutput && /* @__PURE__ */ jsx("div", {
									className: "strategy-run-output ready",
									children: /* @__PURE__ */ jsx(HarnessOutput, { raw: skillHarnessOutput })
								})
							] }),
							/* @__PURE__ */ jsxs(Button, {
								variant: "outline",
								onClick: () => setSkill(null),
								children: [/* @__PURE__ */ jsx(X, { size: 15 }), "关闭"]
							})
						]
					})]
				})
			})
		]
	});
}
//#endregion
//#region app/home-client.tsx
function buildMarket(baseMarket, publicSnapshot = {}) {
	const publicLimitUp = publicSnapshot.sources?.eastmoneyLimitUp?.data?.data?.pool || publicSnapshot.sources?.akshareLimitUpPool?.data?.records || [];
	const publicLimitUpCodes = publicLimitUp.map((x) => x.c || x.代码).filter((x) => typeof x === "string");
	const publicStreaks = new Map(publicLimitUp.map((x) => {
		return [x.c || x.代码, typeof x.lbc === "number" ? x.lbc : typeof x.连板数 === "number" ? x.连板数 : Number(String(x.涨停统计 || "").match(/\d+/)?.[0] || 0)];
	}).filter((x) => typeof x[0] === "string" && x[1] > 0));
	const publicLhbRecords = publicSnapshot.sources?.eastmoneyLhb?.data?.result?.data || publicSnapshot.sources?.akshareLhb?.data?.records || [];
	const sameDayPublicSnapshot = publicSnapshot.date === String(baseMarket.date || "").replace(/(\d{4})(\d{2})(\d{2})/, "$1-$2-$3");
	return {
		...baseMarket,
		stocks: sameDayPublicSnapshot ? baseMarket.stocks.map((s) => publicStreaks.has(s.code) ? {
			...s,
			limitStreak: publicStreaks.get(s.code)
		} : s) : baseMarket.stocks,
		tdxLimitUpCodes: sameDayPublicSnapshot && publicLimitUpCodes.length ? publicLimitUpCodes : baseMarket.tdxLimitUpCodes,
		tdxLimitUpFiles: sameDayPublicSnapshot && publicLimitUpCodes.length ? ["公开补全：东方财富/AkShare 涨停池"] : baseMarket.tdxLimitUpFiles,
		publicLhbRecords: sameDayPublicSnapshot ? publicLhbRecords : [],
		dataSources: {
			...baseMarket.dataSources,
			publicMarket: sameDayPublicSnapshot ? "连板网、东方财富/AkShare 涨停池、东方财富龙虎榜" : void 0
		}
	};
}
var dateLabel = dateLabel$1;
var dataTimeLabel = (value) => {
	const raw = String(value || "");
	if (!raw) return "未记录";
	const parsed = new Date(raw);
	return Number.isNaN(parsed.getTime()) ? raw : parsed.toLocaleString("zh-CN", { hour12: false });
};
var number = (n) => n.toLocaleString("en-US", { maximumFractionDigits: 2 });
var pct = (n) => (n > 0 ? "+" : "") + n.toFixed(2) + "%";
var stockResearchEstimate = 100;
var formatTimer = (seconds) => `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
async function fetchIndexedStockHistory(stock, limit = 0) {
	const symbol = `${stock.code}.${stock.market.toUpperCase()}`;
	const response = await fetch(bridgeUrl(`/market/history?symbol=${encodeURIComponent(symbol)}&limit=${limit}`), { cache: "no-store" });
	const body = await response.json().catch(() => ({}));
	if (!response.ok || body.status !== "ok") throw new Error(body.error || `日线索引服务返回 ${response.status}`);
	return body;
}
var stockDetailSkills = [
	{
		id: "baimao-score-system",
		name: "白猫老师评分体系",
		mode: "harness",
		estimate: 100
	},
	{
		id: "big-bull-analysis-scoring-system",
		name: "大牛线分析评分系统",
		mode: "harness",
		estimate: 110
	},
	{
		id: "financial-roe-analysis",
		name: "财务净资产收益率杜邦分析",
		mode: "harness",
		estimate: 100
	},
	{
		id: "stock-analysis",
		name: "个股分析",
		mode: "harness",
		estimate: 100
	},
	{
		id: "stock-research-engine",
		name: "个股研究引擎",
		mode: "harness",
		estimate: 120
	},
	{
		id: "stock-study",
		name: "高级股票研究",
		mode: "harness",
		estimate: 150
	},
	{
		id: "support-pressure-analysis-system",
		name: "支撑压力分析系统",
		mode: "quick",
		estimate: 0
	},
	{
		id: "risk-mine-clearance",
		name: "风险排雷技能",
		mode: "harness",
		estimate: 100
	},
	{
		id: "baimao-teacher-system",
		name: "白猫老师六公式通达信体系",
		mode: "harness",
		estimate: 100
	},
	{
		id: "technical-analysis",
		name: "技术分析",
		mode: "quick",
		estimate: 0
	}
];
function localDailySkillReport(skillId, skillName, stock) {
	const bars = (Array.isArray(stock.history) ? stock.history : []).filter((row) => Number.isFinite(Number(row.close)) && Number(row.close) > 0);
	const closes = bars.map((row) => Number(row.close));
	const lows = bars.map((row) => Number(row.low)).filter((value) => Number.isFinite(value) && value > 0);
	const highs = bars.map((row) => Number(row.high)).filter((value) => Number.isFinite(value) && value > 0);
	const latest = bars.at(-1);
	const previous = bars.at(-2);
	const latestPct = previous && Number(previous.close) > 0 && latest ? (Number(latest.close) / Number(previous.close) - 1) * 100 : Number(stock.pct);
	const avg = (count) => closes.length >= count ? closes.slice(-count).reduce((sum, value) => sum + value, 0) / count : null;
	const dataDate = String(latest?.date || stock.date || "");
	const dataRange = bars.length ? `${bars[0].date} 至 ${dataDate}` : "无可用日线";
	const values = skillId === "technical-analysis" ? [{
		title: "收盘与涨跌",
		text: `${dataDate} 收盘 ${Number(latest?.close || stock.close).toFixed(2)}，日涨跌 ${latestPct.toFixed(2)}%。`
	}, {
		title: "均线位置",
		text: `MA5 ${avg(5)?.toFixed(2) || "样本不足"}；MA20 ${avg(20)?.toFixed(2) || "样本不足"}。`
	}] : [{
		title: "区间位置",
		text: `统计区间 ${dataRange}，共 ${bars.length} 根已载入日线。`
	}, {
		title: "支撑/压力观察",
		text: `样本最低 ${lows.length ? Math.min(...lows).toFixed(2) : "无"}；样本最高 ${highs.length ? Math.max(...highs).toFixed(2) : "无"}；${dataDate} 收盘 ${Number(latest?.close || stock.close).toFixed(2)}。`
	}];
	const summary = bars.length ? `${stock.name}（${stock.code}）${skillName}已按本地日线完成描述性计算；本次样本 ${bars.length} 根，区间 ${dataRange}。` : `${stock.name}（${stock.code}）没有可用日线样本，本次仅归档数据不足状态。`;
	const raw = JSON.stringify({
		schema: "ZHANGCAI_LOCAL_STOCK_RESEARCH_V1",
		status: bars.length ? "COMPLETED_LOCAL" : "DEGRADED",
		summary,
		dataDate,
		dataScope: `本地日线 · ${bars.length} 根 · ${dataRange}`,
		findings: values,
		tables: [{
			title: skillName,
			columns: ["项目", "结果"],
			rows: [
				["数据范围", dataRange],
				["样本数", String(bars.length)],
				["最新收盘", `${Number(latest?.close || stock.close).toFixed(2)} · ${dataDate}`],
				...skillId === "technical-analysis" ? [
					["涨跌幅", `${latestPct.toFixed(2)}%`],
					["MA5", avg(5)?.toFixed(2) || "样本不足"],
					["MA20", avg(20)?.toFixed(2) || "样本不足"]
				] : [["区间最低", lows.length ? Math.min(...lows).toFixed(2) : "无"], ["区间最高", highs.length ? Math.max(...highs).toFixed(2) : "无"]]
			]
		}],
		cautions: ["仅为本地日线描述性指标，不构成买卖建议。", ...bars.length < 20 ? ["当前载入样本不足 20 根，长周期指标不完整。"] : []]
	}, null, 2);
	return {
		dataDate,
		summary,
		dataScope: `本地日线 · ${bars.length} 根 · ${dataRange}`,
		raw
	};
}
var navItems = [
	{
		id: "overview",
		name: "行情总览",
		icon: LayoutDashboard
	},
	{
		id: "mainline",
		name: "主线追踪",
		icon: TrendingUp
	},
	{
		id: "ladder",
		name: "涨停与连板",
		icon: Layers
	},
	{
		id: "selection",
		name: "策略选股",
		icon: SlidersHorizontal
	},
	{
		id: "capital",
		name: "资金透视",
		icon: Activity
	},
	{
		id: "research",
		name: "个股研究",
		icon: ChartCandlestick
	},
	{
		id: "watchlist",
		name: "我的工作台",
		icon: Star
	},
	{
		id: "reports",
		name: "复盘与报告",
		icon: FileText
	},
	{
		id: "my-reports",
		name: "我的报告",
		icon: FileText
	},
	{
		id: "skills",
		name: "技能中心",
		icon: Workflow
	}
];
function StockResearchOutput({ raw, stock }) {
	const parsed = normalizeHarnessOutput(raw);
	const summary = parsed.summary || "Harness 未返回摘要，请展开原始输出查看。";
	const visibleFindings = parsed.findings.slice(0, 5), visibleTables = parsed.tables.slice(0, 3);
	const history = [...stock.history, stock].filter((bar, index, array) => index === array.findIndex((item) => String(item.date).replace(/\D/g, "") === String(bar.date).replace(/\D/g, "")));
	const low = Math.min(...history.map((x) => x.low), stock.close);
	const high = Math.max(...history.map((x) => x.high), stock.close);
	const position = high > low ? Math.max(4, Math.min(96, (stock.close - low) / (high - low) * 100)) : 50;
	return /* @__PURE__ */ jsxs("section", {
		className: "stock-research-report",
		children: [
			/* @__PURE__ */ jsxs("div", {
				className: "ai-report-reading-head",
				children: [
					/* @__PURE__ */ jsx(Sparkles, { size: 16 }),
					/* @__PURE__ */ jsx("b", { children: "个股研究报告" }),
					/* @__PURE__ */ jsxs("span", { children: ["已存入我的报告 · ", parsed.jsonValid ? "JSON 已校验" : "已兼容规范化"] })
				]
			}),
			/* @__PURE__ */ jsx("p", { children: summary }),
			/* @__PURE__ */ jsxs("div", {
				className: "research-signal-visual",
				children: [
					/* @__PURE__ */ jsxs("div", {
						className: "research-signal-head",
						children: [/* @__PURE__ */ jsx("b", { children: "个股收盘价格位置图" }), /* @__PURE__ */ jsxs("small", { children: [
							"近 ",
							history.length,
							" 个本地日线样本 · ",
							closeDateLabel(stock.date)
						] })]
					}),
					/* @__PURE__ */ jsxs("div", {
						className: "research-signal-row",
						children: [
							/* @__PURE__ */ jsx("span", { children: "低位" }),
							/* @__PURE__ */ jsx("i", { children: /* @__PURE__ */ jsx("b", { style: { left: `${position}%` } }) }),
							/* @__PURE__ */ jsx("span", { children: "高位" })
						]
					}),
					/* @__PURE__ */ jsxs("div", {
						className: "research-signal-values",
						children: [
							/* @__PURE__ */ jsx("span", { children: low.toFixed(2) }),
							/* @__PURE__ */ jsxs("strong", { children: [
								stock.close.toFixed(2),
								" · ",
								pct(stock.pct)
							] }),
							/* @__PURE__ */ jsx("span", { children: high.toFixed(2) })
						]
					})
				]
			}),
			/* @__PURE__ */ jsx("div", {
				className: "ai-finding-grid",
				children: visibleFindings.map((item, index) => /* @__PURE__ */ jsxs("article", { children: [/* @__PURE__ */ jsx("h5", { children: item.title }), /* @__PURE__ */ jsx("p", { children: item.text })] }, `${item.title}-${index}`))
			}),
			/* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [/* @__PURE__ */ jsx(TableHead, { children: "观察项" }), /* @__PURE__ */ jsx(TableHead, { children: closeDateLabel(stock.date) })] }) }), /* @__PURE__ */ jsxs(TableBody, { children: [
				/* @__PURE__ */ jsxs(TableRow, { children: [/* @__PURE__ */ jsx(TableCell, { children: "收盘价格 / 涨跌" }), /* @__PURE__ */ jsxs(TableCell, {
					className: stock.pct >= 0 ? "up" : "down",
					children: [
						stock.close.toFixed(2),
						" · ",
						pct(stock.pct)
					]
				})] }),
				/* @__PURE__ */ jsxs(TableRow, { children: [/* @__PURE__ */ jsx(TableCell, { children: "成交额" }), /* @__PURE__ */ jsxs(TableCell, { children: [(stock.amount / 1e8).toFixed(2), " 亿"] })] }),
				/* @__PURE__ */ jsxs(TableRow, { children: [/* @__PURE__ */ jsx(TableCell, { children: "所属行业" }), /* @__PURE__ */ jsx(TableCell, { children: stock.industryName || stock.sectorName || "本地映射未提供" })] }),
				/* @__PURE__ */ jsxs(TableRow, { children: [/* @__PURE__ */ jsx(TableCell, { children: "连续候选" }), /* @__PURE__ */ jsxs(TableCell, { children: [stock.limitStreak || 0, " 天"] })] })
			] })] }),
			visibleTables.map((table, index) => /* @__PURE__ */ jsxs("section", {
				className: "harness-data-table",
				children: [/* @__PURE__ */ jsx("h4", { children: table.title }), /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsx(TableRow, { children: table.columns.map((column) => /* @__PURE__ */ jsx(TableHead, { children: column }, column)) }) }), /* @__PURE__ */ jsx(TableBody, { children: table.rows.slice(0, 10).map((row, rowIndex) => /* @__PURE__ */ jsx(TableRow, { children: row.map((cell, cellIndex) => /* @__PURE__ */ jsx(TableCell, { children: cell || "—" }, `${rowIndex}-${cellIndex}`)) }, rowIndex)) })] })]
			}, `${table.title}-${index}`)),
			(parsed.findings.length > 5 || parsed.tables.length > 3 || parsed.tables.some((table) => table.rows.length > 10)) && /* @__PURE__ */ jsxs("details", {
				className: "harness-more",
				children: [
					/* @__PURE__ */ jsx("summary", { children: "查看完整分析（保留全部结论与表格）" }),
					parsed.findings.slice(5).map((item, index) => /* @__PURE__ */ jsxs("article", { children: [/* @__PURE__ */ jsx("h5", { children: item.title }), /* @__PURE__ */ jsx("p", { children: item.text })] }, `more-${index}`)),
					parsed.tables.slice(3).map((table, index) => /* @__PURE__ */ jsxs("section", {
						className: "harness-data-table",
						children: [/* @__PURE__ */ jsx("h4", { children: table.title }), /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsx(TableRow, { children: table.columns.map((column) => /* @__PURE__ */ jsx(TableHead, { children: column }, column)) }) }), /* @__PURE__ */ jsx(TableBody, { children: table.rows.map((row, rowIndex) => /* @__PURE__ */ jsx(TableRow, { children: row.map((cell, cellIndex) => /* @__PURE__ */ jsx(TableCell, { children: cell || "—" }, `${rowIndex}-${cellIndex}`)) }, rowIndex)) })] })]
					}, `more-table-${index}`))
				]
			}),
			!parsed.jsonValid && /* @__PURE__ */ jsxs("p", {
				className: "form-error",
				children: [
					"输出已兼容规范化：",
					parsed.parseError || "未通过严格 JSON 校验",
					"。"
				]
			}),
			parsed.cautions.length > 0 && /* @__PURE__ */ jsxs(Fragment$1, { children: [/* @__PURE__ */ jsx("h4", { children: "数据边界" }), /* @__PURE__ */ jsx("ul", {
				className: "report-list",
				children: parsed.cautions.slice(0, 6).map((x, index) => /* @__PURE__ */ jsx("li", { children: x }, `${x}-${index}`))
			})] }),
			/* @__PURE__ */ jsxs("details", {
				className: "report-raw",
				children: [/* @__PURE__ */ jsx("summary", { children: "查看原始 JSON" }), /* @__PURE__ */ jsx("pre", { children: raw })]
			})
		]
	});
}
function QuickFormulaOutput({ value }) {
	const labels = [
		{
			name: "大牛线",
			keys: [
				"主趋势线",
				"EMA9",
				"EMA10",
				"EMA11",
				"涨停价",
				"跌停价"
			]
		},
		{
			name: "飞龙在天",
			keys: ["波", "段"]
		},
		{
			name: "游资资金",
			keys: [
				"买方意向",
				"AAA",
				"DDD"
			]
		},
		{
			name: "机构资金",
			keys: [
				"机构大单进",
				"机构大单出",
				"大单动向",
				"大户大单进",
				"散户资金进"
			]
		},
		{
			name: "庄家资金",
			keys: ["控盘程度", "控盘度"]
		}
	];
	const read = (row, keys) => keys.map((k) => {
		const v = row.result?.[k];
		const x = Array.isArray(v) ? v[0] : v;
		return x === null || x === void 0 || String(x).trim() === "" ? null : `${k} ${String(x).trim()}`;
	}).filter(Boolean).join(" · ");
	const hasClientError = (text) => text.includes("通达信客户端未打开") || text.includes("请先") && text.includes("打开通达信");
	const clientHint = value.client_open_required || value.formulas.some((row) => row.client_open_required) || value.formulas.some((row) => hasClientError(String(row.error || "")));
	const failureText = (row) => row.error || row.action || (clientHint ? "请先打开通达信客户端并登录" : "公式执行失败，请查看本地 TQ 回执");
	return /* @__PURE__ */ jsxs("section", {
		className: "stock-research-report quick-formula-card",
		children: [
			/* @__PURE__ */ jsxs("div", {
				className: "ai-report-reading-head",
				children: [
					/* @__PURE__ */ jsx(Activity, { size: 16 }),
					/* @__PURE__ */ jsx("b", { children: "本地快速公式结果" }),
					/* @__PURE__ */ jsxs("span", { children: [
						(value.elapsed_ms / 1e3).toFixed(1),
						" 秒 · ",
						value.symbol
					] })
				]
			}),
			clientHint && /* @__PURE__ */ jsx("p", {
				className: "form-error",
				role: "alert",
				children: "检测到通达信客户端未打开或 TQ 尚未就绪。请先点击“打开通达信”，确认客户端已登录后，再重新执行本地公式。"
			}),
			/* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
				/* @__PURE__ */ jsx(TableHead, { children: "分析类型" }),
				/* @__PURE__ */ jsx(TableHead, { children: "状态" }),
				/* @__PURE__ */ jsx(TableHead, { children: "核心字段 / 失败原因" })
			] }) }), /* @__PURE__ */ jsx(TableBody, { children: value.formulas.map((row, i) => {
				const config = labels[i] || {
					name: row.formula,
					keys: Object.keys(row.result || {}).slice(0, 5)
				};
				return /* @__PURE__ */ jsxs(TableRow, { children: [
					/* @__PURE__ */ jsxs(TableCell, { children: [/* @__PURE__ */ jsx("b", { children: config.name }), /* @__PURE__ */ jsx("small", {
						className: "table-sub",
						children: row.tq_formula || row.formula
					})] }),
					/* @__PURE__ */ jsx(TableCell, {
						className: row.ok ? "up" : "down",
						children: row.ok ? "已返回" : "失败"
					}),
					/* @__PURE__ */ jsx(TableCell, { children: read(row, config.keys) || (!row.ok ? failureText(row) : "公式已执行，暂无可见字段") })
				] }, row.formula);
			}) })] }),
			value.failed_formulas?.length ? /* @__PURE__ */ jsxs("p", {
				className: "form-error",
				children: [
					"失败公式：",
					value.failed_formulas.join("、"),
					value.action ? ` · ${value.action}` : ""
				]
			}) : null
		]
	});
}
function LocalQuickMetrics({ stock }) {
	const bars = stock.history.length ? [...stock.history, stock].filter((bar, i, a) => i === a.findIndex((x) => String(x.date).replace(/\D/g, "") === String(bar.date).replace(/\D/g, ""))) : [stock];
	const closes = bars.map((x) => x.close), lows = bars.map((x) => x.low), highs = bars.map((x) => x.high);
	const avg = (xs) => xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0;
	const ma5 = closes.length >= 5 ? avg(closes.slice(-5)) : null, ma20 = closes.length >= 20 ? avg(closes.slice(-20)) : null;
	return /* @__PURE__ */ jsxs("section", {
		className: "stock-research-report quick-formula-card",
		children: [/* @__PURE__ */ jsxs("div", {
			className: "ai-report-reading-head",
			children: [
				/* @__PURE__ */ jsx(ChartCandlestick, { size: 16 }),
				/* @__PURE__ */ jsx("b", { children: "可秒算技能" }),
				/* @__PURE__ */ jsxs("span", { children: [
					"本地日线 · ",
					bars.length,
					" 个样本",
					stock.historyTotal && stock.historyTotal > bars.length ? `（全量 ${stock.historyTotal}）` : ""
				] })
			]
		}), /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsxs(TableRow, { children: [
			/* @__PURE__ */ jsx(TableHead, { children: "技能" }),
			/* @__PURE__ */ jsx(TableHead, { children: "结果" }),
			/* @__PURE__ */ jsx(TableHead, { children: "数据边界" })
		] }) }), /* @__PURE__ */ jsxs(TableBody, { children: [/* @__PURE__ */ jsxs(TableRow, { children: [
			/* @__PURE__ */ jsx(TableCell, { children: /* @__PURE__ */ jsx("b", { children: "技术分析" }) }),
			/* @__PURE__ */ jsxs(TableCell, { children: [
				closeDateLabel(stock.date),
				" ",
				stock.close.toFixed(2),
				" · 涨跌 ",
				pct(stock.pct),
				" · MA5 ",
				ma5 === null ? "样本不足" : ma5.toFixed(2),
				" · MA20 ",
				ma20 === null ? "样本不足" : ma20.toFixed(2)
			] }),
			/* @__PURE__ */ jsx(TableCell, { children: bars.length < 20 ? "本地快照不足 20 日，仅展示已有样本" : "基于本地日线索引" })
		] }), /* @__PURE__ */ jsxs(TableRow, { children: [
			/* @__PURE__ */ jsx(TableCell, { children: /* @__PURE__ */ jsx("b", { children: "支撑压力分析系统" }) }),
			/* @__PURE__ */ jsxs(TableCell, { children: [
				"支撑 ",
				Math.min(...lows).toFixed(2),
				" · 压力 ",
				Math.max(...highs).toFixed(2),
				" · ",
				closeDateLabel(stock.date),
				" ",
				stock.close.toFixed(2)
			] }),
			/* @__PURE__ */ jsx(TableCell, { children: stock.historySource || "取当前收盘快照与历史样本最低/最高价" })
		] })] })] })]
	});
}
function HarnessTaskTray({ tasks, onOpen, onDismiss, now, currentDate }) {
	const normalizedDate = String(currentDate || "").replace(/\D/g, "").slice(0, 8);
	const visible = tasks.filter((task) => task.status === "starting" || task.status === "running" || task.status === "completed" || task.status === "failed").filter((task) => {
		if (task.status === "starting" || task.status === "running" || !normalizedDate || !task.output) return true;
		const outputDate = String(normalizeHarnessOutput(task.output).dataDate || "").replace(/\D/g, "").slice(0, 8);
		return !outputDate || outputDate === normalizedDate;
	}).slice(0, 5);
	if (!visible.length) return null;
	return /* @__PURE__ */ jsxs("div", {
		className: "harness-task-tray",
		"aria-label": "后台 Harness 任务",
		children: [/* @__PURE__ */ jsxs("div", {
			className: "harness-task-tray-title",
			children: [/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("span", { className: "harness-task-dot" }), "后台计算"] }), /* @__PURE__ */ jsxs("small", { children: [visible.filter((x) => x.status === "starting" || x.status === "running").length, " 个运行中"] })]
		}), visible.map((task) => {
			const elapsed = Math.max(0, Math.floor(((task.completedAt || now) - task.startedAt) / 1e3));
			const running = task.status === "starting" || task.status === "running";
			const expected = task.expectedSeconds;
			return /* @__PURE__ */ jsxs("div", {
				className: `harness-task ${task.status}`,
				children: [/* @__PURE__ */ jsxs("button", {
					className: "harness-task-main",
					onClick: () => onOpen(task),
					title: `${task.label} · 已用 ${formatTimer(elapsed)} · 预计 ${formatTimer(expected)}`,
					children: [/* @__PURE__ */ jsx("span", {
						className: "harness-task-icon",
						children: running ? /* @__PURE__ */ jsx(LoaderCircle, {
							className: "spin",
							size: 15
						}) : task.status === "completed" ? "✓" : "!"
					}), /* @__PURE__ */ jsxs("span", {
						className: "harness-task-copy",
						children: [/* @__PURE__ */ jsx("b", { children: task.label }), /* @__PURE__ */ jsx("small", { children: running ? `已用 ${formatTimer(elapsed)} · 预计 ${formatTimer(expected)}` : task.status === "completed" ? `已完成 · 用时 ${formatTimer(elapsed)}` : `执行失败 · ${task.error || "请点击查看"}` })]
					})]
				}), /* @__PURE__ */ jsx("button", {
					className: "harness-task-dismiss",
					"aria-label": `关闭${task.label}后台任务`,
					onClick: () => onDismiss(task.id),
					children: "×"
				})]
			}, task.id);
		})]
	});
}
function HarnessTaskResult({ task, onClose }) {
	const parsed = normalizeHarnessOutput(task.output || task.error || "");
	return /* @__PURE__ */ jsxs("section", {
		className: "harness-task-result",
		role: "dialog",
		"aria-label": "Harness 任务结果",
		children: [
			/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsxs("b", { children: [task.label, " · 任务结果"] }), /* @__PURE__ */ jsx("button", {
				onClick: onClose,
				"aria-label": "关闭任务结果",
				children: "×"
			})] }),
			/* @__PURE__ */ jsx("p", {
				className: "harness-task-summary",
				children: parsed.summary || task.error || "任务已完成，暂无摘要。"
			}),
			parsed.findings.slice(0, 5).map((item, index) => /* @__PURE__ */ jsxs("article", { children: [/* @__PURE__ */ jsx("b", { children: item.title }), /* @__PURE__ */ jsx("p", { children: item.text })] }, `${item.title}-${index}`)),
			parsed.tables.slice(0, 3).map((table, index) => /* @__PURE__ */ jsxs("section", {
				className: "harness-data-table",
				children: [/* @__PURE__ */ jsx("h5", { children: table.title }), /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsx(TableRow, { children: table.columns.map((column) => /* @__PURE__ */ jsx(TableHead, { children: column }, column)) }) }), /* @__PURE__ */ jsx(TableBody, { children: table.rows.slice(0, 10).map((row, rowIndex) => /* @__PURE__ */ jsx(TableRow, { children: row.map((cell, cellIndex) => /* @__PURE__ */ jsx(TableCell, { children: cell || "—" }, `${rowIndex}-${cellIndex}`)) }, rowIndex)) })] })]
			}, `${table.title}-${index}`)),
			/* @__PURE__ */ jsxs("details", {
				className: "report-raw",
				children: [/* @__PURE__ */ jsx("summary", { children: "查看原始 JSON" }), /* @__PURE__ */ jsx("pre", { children: task.output || task.error || "" })]
			})
		]
	});
}
function Sparkline({ bars, color = "var(--brand)", large = false }) {
	const values = bars.map((s) => s.close), min = Math.min(...values), max = Math.max(...values);
	const pts = values.map((v, i) => `${i / Math.max(values.length - 1, 1) * 600},${150 - (v - min) / (max - min || 1) * 120}`).join(" ");
	return /* @__PURE__ */ jsxs("svg", {
		className: large ? "trend-chart" : "sparkline",
		viewBox: "0 0 600 180",
		preserveAspectRatio: "none",
		"aria-label": "本地日线价格走势",
		role: "img",
		children: [
			large && [
				30,
				70,
				110,
				150
			].map((y) => /* @__PURE__ */ jsx("line", {
				x1: "0",
				x2: "600",
				y1: y,
				y2: y,
				stroke: "var(--line)",
				strokeDasharray: "4 5"
			}, y)),
			/* @__PURE__ */ jsx("polygon", {
				points: `0,180 ${pts} 600,180`,
				fill: color,
				opacity: ".065"
			}),
			/* @__PURE__ */ jsx("polyline", {
				points: pts,
				fill: "none",
				stroke: color,
				strokeWidth: large ? 2.4 : 2,
				vectorEffect: "non-scaling-stroke"
			})
		]
	});
}
function Panel({ title, children, extra, className = "" }) {
	return /* @__PURE__ */ jsxs("section", {
		className: "panel " + className,
		children: [/* @__PURE__ */ jsxs("div", {
			className: "panel-head",
			children: [/* @__PURE__ */ jsx("h2", { children: title }), extra]
		}), children]
	});
}
function StockTable({ stocks, onSelect, watch = [], onWatch, asOfDate }) {
	return /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, { children: /* @__PURE__ */ jsx(TableRow, { children: [
		"股票",
		closeDateLabel(asOfDate || stocks[0]?.date),
		"涨跌幅",
		"成交额",
		...onWatch ? ["自选"] : []
	].map((x) => /* @__PURE__ */ jsx(TableHead, { children: x }, x)) }) }), /* @__PURE__ */ jsx(TableBody, { children: stocks.map((s) => /* @__PURE__ */ jsxs(TableRow, { children: [
		/* @__PURE__ */ jsx(TableCell, { children: /* @__PURE__ */ jsxs("button", {
			className: "stock-name",
			onClick: () => onSelect(s),
			children: [s.name, /* @__PURE__ */ jsx("small", { children: s.code })]
		}) }),
		/* @__PURE__ */ jsx(TableCell, {
			className: "numeric",
			title: closeDateLabel(s.date),
			children: s.close.toFixed(2)
		}),
		/* @__PURE__ */ jsx(TableCell, {
			className: `numeric ${s.pct >= 0 ? "up" : "down"}`,
			children: pct(s.pct)
		}),
		/* @__PURE__ */ jsxs(TableCell, {
			className: "numeric",
			children: [(s.amount / 1e8).toFixed(2), " 亿"]
		}),
		onWatch && /* @__PURE__ */ jsx(TableCell, { children: /* @__PURE__ */ jsx("button", {
			className: "star-button " + (watch.includes(s.code) ? "saved" : ""),
			"aria-label": `${watch.includes(s.code) ? "移除" : "添加"}自选 ${s.name}`,
			onClick: () => onWatch(s.code),
			children: /* @__PURE__ */ jsx(Star, {
				size: 16,
				fill: watch.includes(s.code) ? "currentColor" : "none"
			})
		}) })
	] }, s.code)) })] });
}
function Home({ initialMarket }) {
	const [market] = useState(() => buildMarket(initialMarket, {}));
	const [page, setPage] = useState("overview"), [chart, setChart] = useState("0"), [selected, setSelected] = useState(null), [watch, setWatch] = useState([]), [stockResearchBusy, setStockResearchBusy] = useState(false), [stockResearchSkill, setStockResearchSkill] = useState("stock-analysis"), [stockResearchOutput, setStockResearchOutput] = useState(""), [stockResearchError, setStockResearchError] = useState(""), [stockResearchStarted, setStockResearchStarted] = useState(null), [stockResearchElapsed, setStockResearchElapsed] = useState(0), [quickBusy, setQuickBusy] = useState(false), [quickResult, setQuickResult] = useState(null), [quickError, setQuickError] = useState(""), [indexRefreshing, setIndexRefreshing] = useState(false), [marketRefreshing, setMarketRefreshing] = useState(false), [marketRefreshMessage, setMarketRefreshMessage] = useState("");
	const [pageHydrated, setPageHydrated] = useState(false);
	const [harnessTasks, setHarnessTasks] = useState([]), [openedHarnessTask, setOpenedHarnessTask] = useState(null), [harnessNow, setHarnessNow] = useState(0);
	const [resourceLibraryContext, setResourceLibraryContext] = useState(null);
	const [quoteRefreshing, setQuoteRefreshing] = useState(false), [quoteMode, setQuoteMode] = useState(""), [quoteError, setQuoteError] = useState(""), [quoteRefreshNonce, setQuoteRefreshNonce] = useState(0), [intradayQuote, setIntradayQuote] = useState(null);
	const [, forceMarketRender] = useState(0);
	const indexRefreshingRef = useRef(false), marketRefreshingRef = useRef(false), marketAutoRefreshRef = useRef(false), quickRequestRef = useRef(0);
	const active = navItems.find((x) => x.id === page), idx = market.indices[Number(chart)] || market.indices[0];
	useEffect(() => {
		if (!stockResearchStarted) return;
		const tick = () => setStockResearchElapsed(Math.max(0, Math.floor((Date.now() - stockResearchStarted) / 1e3)));
		tick();
		const timer = window.setInterval(tick, 1e3);
		return () => window.clearInterval(timer);
	}, [stockResearchStarted]);
	useEffect(() => {
		try {
			const saved = JSON.parse(localStorage.getItem("zhangcai.watchlist.v1") || "[]");
			if (Array.isArray(saved)) setWatch(saved.filter((v) => typeof v === "string" && /^\d{6}$/.test(v)));
		} catch {}
	}, []);
	useEffect(() => {
		const unsubscribe = subscribeHarnessTasks(setHarnessTasks);
		resumeHarnessTasks();
		const timer = window.setInterval(() => {
			setHarnessNow(Date.now());
			resumeHarnessTasks();
		}, 1e3);
		return () => {
			unsubscribe();
			window.clearInterval(timer);
		};
	}, []);
	useEffect(() => {
		try {
			const saved = localStorage.getItem("zhangcai.active-page.v1");
			if (saved && navItems.some((item) => item.id === saved)) setPage(saved);
		} catch {} finally {
			setPageHydrated(true);
		}
	}, []);
	useEffect(() => {
		let active = true;
		Promise.allSettled([fetch(bridgeUrl("/data/public"), { cache: "no-store" }).then(async (response) => response.ok ? response.json() : null), fetch(bridgeUrl("/runtime/resource-context"), { cache: "no-store" }).then(async (response) => response.ok ? response.json() : null)]).then(([publicResult, resourceResult]) => {
			if (!active) return;
			const snapshot = publicResult.status === "fulfilled" && publicResult.value && typeof publicResult.value === "object" ? publicResult.value : null;
			if (snapshot) {
				Object.assign(market, buildMarket(market, snapshot));
				forceMarketRender((v) => v + 1);
			}
			if (resourceResult.status === "fulfilled" && resourceResult.value && typeof resourceResult.value === "object") setResourceLibraryContext(resourceResult.value);
		});
		return () => {
			active = false;
		};
	}, [market]);
	useEffect(() => {
		if (!pageHydrated) return;
		try {
			localStorage.setItem("zhangcai.active-page.v1", page);
		} catch {}
	}, [page, pageHydrated]);
	useEffect(() => {
		if (pageHydrated);
	}, [page, pageHydrated]);
	useEffect(() => {
		setQuoteError("");
		setQuoteMode("");
		setIntradayQuote(null);
		if (!selected) {
			quickRequestRef.current += 1;
			setQuoteRefreshing(false);
			return;
		}
		const selectedCode = selected.code;
		let active = true;
		let inFlight = false;
		const refreshSelectedQuote = () => {
			if (inFlight) return;
			inFlight = true;
			setQuoteRefreshing(true);
			fetchLatestQuote(selected).then((body) => {
				if (!active || selectedCode !== selected.code || !body.quote) return;
				const incoming = body.quote;
				setQuoteError("");
				setIntradayQuote(incoming);
				setQuoteMode(body.quoteMode || incoming.quoteMode || "");
			}).catch(() => {
				if (active) setQuoteError("盘中价格暂不可用，请稍后重试");
			}).finally(() => {
				inFlight = false;
				if (active) setQuoteRefreshing(false);
			});
		};
		refreshSelectedQuote();
		const quoteTimer = window.setInterval(refreshSelectedQuote, 6e4);
		return () => {
			active = false;
			window.clearInterval(quoteTimer);
		};
	}, [selected?.code, quoteRefreshNonce]);
	useEffect(() => {
		setQuickResult(null);
		setQuickError("");
		setStockResearchOutput("");
		setStockResearchError("");
		if (!selected) return;
		let active = true;
		const selectedCode = selected.code;
		const restoreLatestHarnessReport = (reports) => {
			if (!active) return;
			const latest = [...reports].filter((item) => item.content?.kind === "stock-research" && item.content.stock?.code === selectedCode && item.generatedBy.startsWith("DeepSeek Harness")).sort((a, b) => Date.parse(b.updatedAt || b.createdAt) - Date.parse(a.updatedAt || a.createdAt))[0];
			if (latest?.raw) setStockResearchOutput(latest.raw);
		};
		restoreLatestHarnessReport(loadReportArchive());
		loadReportArchiveFromLocalRuntime().then(restoreLatestHarnessReport);
		fetchIndexedStockHistory(selected, 120).then((body) => {
			if (!active) return;
			const incoming = Array.isArray(body.history) ? body.history : [];
			if (!incoming.length) return;
			setSelected((prev) => prev && prev.code === selectedCode ? {
				...prev,
				history: incoming.slice(-120),
				historyTotal: Number(body.history_count || incoming.length),
				historyScope: body.history_scope || "",
				historySource: body.source || ""
			} : prev);
		}).catch(() => {});
		runQuickFormula(selected);
		return () => {
			active = false;
			quickRequestRef.current += 1;
		};
	}, [selected?.code]);
	useEffect(() => {
		if (!selected) return;
		window.requestAnimationFrame(() => document.querySelector(".stock-sheet")?.scrollTo({
			top: 0,
			left: 0,
			behavior: "auto"
		}));
	}, [selected?.code]);
	async function restoreLatestMarket() {
		try {
			const response = await fetch(bridgeUrl("/market?scope=latest"), { cache: "no-store" });
			if (!response.ok) return false;
			const body = await response.json().catch(() => ({}));
			if (body.status !== "ok") return false;
			const savedIndices = body.indices || [];
			const savedByCode = new Map(savedIndices.map((row) => [row.code, row]));
			const nextIndices = [...market.indices.map((existing) => {
				const row = savedByCode.get(existing.code);
				return row ? {
					...existing,
					...row,
					history: row.history?.length ? row.history : existing.history
				} : existing;
			}), ...savedIndices.filter((row) => !market.indices.some((existing) => existing.code === row.code))];
			const fullIncoming = body.allStocks || [];
			const leaderboard = body.stocks || [];
			const savedStocks = leaderboard.length ? leaderboard : fullIncoming;
			const summary = body;
			const isFallback = body.fallback === true || body.quality === "degraded";
			Object.assign(market, {
				indices: nextIndices,
				stocks: savedStocks.length ? savedStocks : market.stocks,
				allStocks: isFallback ? [] : fullIncoming.length ? fullIncoming : market.allStocks,
				date: body.date || body.tradeDate || market.date,
				total: summary.total ?? market.total,
				currentCount: summary.currentCount ?? market.currentCount,
				up: summary.up ?? market.up,
				down: summary.down ?? market.down,
				flat: summary.flat ?? market.flat,
				amount: summary.amount ?? market.amount,
				bins: summary.bins ?? market.bins,
				source: body.source || market.source,
				quality: body.quality || market.quality,
				fallback: isFallback,
				indicesSource: body.indicesSource || market.indicesSource,
				indicesQuality: body.indicesQuality || market.indicesQuality,
				indicesFallback: body.indicesFallback === true,
				indicesLatestDataAt: body.indicesLatestDataAt || market.indicesLatestDataAt,
				latestDataAt: body.latestDataAt || body.fetchedAt || body.persistedAt || market.latestDataAt,
				fetchedAt: body.fetchedAt || market.fetchedAt,
				dataSources: {
					...market.dataSources,
					...body.dataSources || {}
				}
			});
			if (isFallback) setMarketRefreshMessage(`已恢复首页最新公开降级参数 · ${body.tradeDate || ""} · 数据时间 ${dataTimeLabel(body.latestDataAt || body.fetchedAt || body.persistedAt)}`);
			forceMarketRender((v) => v + 1);
			return true;
		} catch {
			return false;
		}
	}
	async function refreshIndices(silent = false) {
		if (indexRefreshingRef.current) return;
		indexRefreshingRef.current = true;
		setIndexRefreshing(true);
		if (!silent) setMarketRefreshMessage("第一步：正在读取主要指数…");
		try {
			const response = await fetch(bridgeUrl("/market?scope=indices"), { cache: "no-store" });
			const body = await response.json().catch(() => ({}));
			if (!response.ok || body.status !== "ok") throw new Error(body.error || `指数服务返回 ${response.status}`);
			const currentByCode = new Map(market.indices.map((x) => [x.code, x]));
			const incoming = body.indices || [];
			const incomingByCode = new Map(incoming.map((row) => [row.code, row]));
			const nextIndices = [...market.indices.map((existing) => {
				const row = incomingByCode.get(existing.code);
				if (!row) return existing;
				const close = Number(row.close);
				const previousClose = Number(row.previousClose);
				return {
					...existing,
					...row,
					history: row.history?.length ? row.history : existing.history,
					close: close > 0 ? row.close : existing.close,
					previousClose: previousClose > 0 ? row.previousClose : existing.previousClose,
					open: Number(row.open) > 0 ? row.open : existing.open,
					high: Number(row.high) > 0 ? row.high : existing.high,
					low: Number(row.low) > 0 ? row.low : existing.low
				};
			}), ...incoming.filter((row) => !currentByCode.has(row.code) && Number(row.close) > 0)];
			const isFallback = body.fallback === true || body.quality === "degraded";
			const latestDataAt = body.latestDataAt || body.fetchedAt || body.persistedAt;
			Object.assign(market, {
				indices: nextIndices,
				date: body.tradeDate || market.date,
				source: body.source || market.source,
				quality: body.quality || market.quality,
				fallback: isFallback,
				latestDataAt,
				indicesLatestDataAt: latestDataAt,
				indicesQuoteMode: isFallback ? "public_delayed" : body.quoteMode || "tdx_realtime",
				indicesSource: body.source || market.source,
				indicesQuality: body.quality || body.dataQuality || "primary",
				indicesFallback: isFallback,
				fetchedAt: body.fetchedAt || market.fetchedAt,
				dataSources: {
					...market.dataSources,
					...body.dataSources || {}
				}
			});
			forceMarketRender((v) => v + 1);
			if (!silent || isFallback) setMarketRefreshMessage(isFallback ? `通达信/TQ 不可用，已切换公开行情降级 · ${body.tradeDate || ""} · 刷新于 ${dataTimeLabel(latestDataAt)}` : `第一步完成：主要指数已刷新 · ${body.tradeDate || ""} · 刷新于 ${dataTimeLabel(latestDataAt)}`);
		} catch (error) {
			if (!silent) setMarketRefreshMessage(error instanceof Error ? error.message : "指数刷新失败");
		} finally {
			indexRefreshingRef.current = false;
			setIndexRefreshing(false);
		}
	}
	async function refreshMarket(silent = false) {
		if (marketRefreshingRef.current) return;
		marketRefreshingRef.current = true;
		setMarketRefreshing(true);
		if (!silent) setMarketRefreshMessage("第二步：正在读取首页市场参数…");
		try {
			const response = await fetch(bridgeUrl("/market?scope=market"), { cache: "no-store" });
			const body = await response.json().catch(() => ({}));
			if (!response.ok || body.status !== "ok") throw new Error(body.error || `市场服务返回 ${response.status}`);
			const incoming = body.stocks || [];
			const fullIncoming = body.allStocks || [];
			const isFallback = body.fallback === true || body.quality === "degraded";
			const stockByCode = new Map(market.allStocks?.map((x) => [x.code, x]) || market.stocks.map((x) => [x.code, x]));
			if (!isFallback) for (const row of fullIncoming.length ? fullIncoming : incoming) stockByCode.set(row.code, {
				...stockByCode.get(row.code),
				...row
			});
			const nextStocks = body.replaceLeaderboard ? incoming.sort((a, b) => b.pct - a.pct || b.amount - a.amount) : [...stockByCode.values()].sort((a, b) => b.pct - a.pct || b.amount - a.amount);
			const nextAllStocks = isFallback ? [] : fullIncoming.length ? fullIncoming : [...stockByCode.values()];
			const nextDate = body.tradeDate || market.date;
			const nextLimitUpCodes = nextStocks.filter((row) => row.pct >= (row.limitPct || 10) - .5).map((row) => row.code);
			const nextLimitDownCodes = nextStocks.filter((row) => row.pct <= -((row.limitPct || 10) - .5)).map((row) => row.code);
			const latestDataAt = body.latestDataAt || body.fetchedAt || body.persistedAt;
			Object.assign(market, {
				stocks: nextStocks,
				allStocks: nextAllStocks,
				date: nextDate,
				total: body.marketSummary?.currentCount ?? market.total,
				currentCount: body.marketSummary?.currentCount ?? market.currentCount,
				staleCount: 0,
				amount: body.marketSummary?.amount ?? market.amount,
				up: body.marketSummary?.up ?? market.up,
				down: body.marketSummary?.down ?? market.down,
				flat: body.marketSummary?.flat ?? market.flat,
				bins: body.marketSummary?.bins ?? market.bins,
				source: body.source || market.source,
				quality: body.quality || market.quality,
				fallback: isFallback,
				latestDataAt,
				fetchedAt: body.fetchedAt || market.fetchedAt,
				dataSources: {
					...market.dataSources,
					...body.dataSources || {}
				},
				tdxLimitUpCodes: nextLimitUpCodes,
				tdxLimitDownCodes: nextLimitDownCodes,
				tdxLimitUpFiles: [isFallback ? `公开行情降级首页参数（${nextDate}）` : `通达信最新完整日线（${nextDate}）`]
			});
			setSelected((prev) => prev ? nextAllStocks.find((row) => row.code === prev.code) || nextStocks.find((row) => row.code === prev.code) || prev : prev);
			forceMarketRender((v) => v + 1);
			if (!silent || isFallback) setMarketRefreshMessage(isFallback ? `首页参数已更新（公开行情降级） · ${nextDate} · 数据时间 ${dataTimeLabel(latestDataAt)}` : `第二步完成：已更新首页市场参数 · ${nextDate} · 数据时间 ${dataTimeLabel(latestDataAt)}`);
		} catch (error) {
			if (!silent) setMarketRefreshMessage(error instanceof Error ? error.message : "市场数据刷新失败");
		} finally {
			marketRefreshingRef.current = false;
			setMarketRefreshing(false);
		}
	}
	useEffect(() => {
		if (!pageHydrated || page !== "overview") return;
		let active = true;
		const refreshSilently = async () => {
			if (!active || marketAutoRefreshRef.current) return;
			marketAutoRefreshRef.current = true;
			try {
				await restoreLatestMarket();
				if (!active) return;
				await refreshIndices(true);
				if (!active) return;
				await refreshMarket(true);
			} finally {
				marketAutoRefreshRef.current = false;
			}
		};
		refreshSilently().catch(() => {});
		const timer = window.setInterval(() => {
			refreshSilently().catch(() => {});
		}, 900 * 1e3);
		return () => {
			active = false;
			window.clearInterval(timer);
		};
	}, [page, pageHydrated]);
	useEffect(() => {
		const handler = () => {
			refreshIndices(false).then(() => refreshMarket(false)).catch(() => {});
		};
		window.addEventListener("zhangcai:desktop-market-refresh", handler);
		return () => window.removeEventListener("zhangcai:desktop-market-refresh", handler);
	}, []);
	async function fetchTqFormula(stock) {
		const symbol = `${stock.code}.${stock.market.toUpperCase()}`;
		const response = await fetch(bridgeUrl(`/stock/quick?symbol=${encodeURIComponent(symbol)}`), { cache: "no-store" });
		const body = await response.json().catch(() => ({}));
		if (!response.ok || ![
			"ok",
			"degraded",
			"partial"
		].includes(String(body.status))) {
			const failed = Array.isArray(body.failed_formulas) && body.failed_formulas.length ? `失败公式：${body.failed_formulas.join("、")}` : "";
			const detail = body.error || body.action || failed || `快速公式业务状态 ${body.status || "unknown"}`;
			throw new Error(`${detail}（HTTP ${response.status}）`);
		}
		return body;
	}
	async function fetchLatestQuote(stock) {
		const symbol = `${stock.code}.${stock.market.toUpperCase()}`;
		const response = await fetch(bridgeUrl(`/stock/quote?symbol=${encodeURIComponent(symbol)}`), {
			cache: "no-store",
			signal: AbortSignal.timeout(25e3)
		});
		const body = await response.json().catch(() => ({}));
		if (!response.ok || body.status !== "ok") throw new Error(body.error || `最新价格服务返回 ${response.status}`);
		return body;
	}
	async function runQuickFormula(stock) {
		const requestId = ++quickRequestRef.current;
		setQuickBusy(true);
		setQuickError("");
		let formulaError = "";
		try {
			const formulaTask = fetchTqFormula(stock).then((body) => {
				if (requestId === quickRequestRef.current) setQuickResult(body);
				return body;
			}).catch((error) => {
				formulaError = error instanceof Error ? error.message : "通达信快速公式暂不可用";
				if (requestId === quickRequestRef.current) setQuickError(formulaError);
				return null;
			});
			const localReportsTask = (async () => {
				const skills = stockDetailSkills.filter((item) => item.mode === "quick" && !["support-pressure-analysis-system", "technical-analysis"].includes(item.id));
				if (!skills.length) return;
				let reportStock = stock;
				try {
					const indexed = await fetchIndexedStockHistory(stock, 120);
					if (Array.isArray(indexed.history) && indexed.history.length) {
						const latest = indexed.history.at(-1);
						const previous = indexed.history.at(-2);
						const pct = latest && previous && Number(previous.close) > 0 ? (Number(latest.close) / Number(previous.close) - 1) * 100 : stock.pct;
						reportStock = {
							...stock,
							history: indexed.history,
							date: String(latest?.date || indexed.last_date || stock.date),
							close: Number(latest?.close || stock.close),
							pct,
							historyTotal: Number(indexed.history_count || indexed.history.length)
						};
					}
				} catch {}
				const now = (/* @__PURE__ */ new Date()).toISOString();
				await Promise.all(skills.map(async (skill) => {
					const report = localDailySkillReport(skill.id, skill.name, reportStock);
					const reportDate = report.dataDate || reportStock.date || market.date;
					await saveReportArchive({
						archiveKey: `stock:${reportDate}:${stock.code}:${skill.id}`,
						id: createReportId("stock-local"),
						createdAt: now,
						updatedAt: now,
						date: reportDate,
						title: `个股${skill.name} · ${stock.name} · ${dateLabel(reportDate)}`,
						reportType: `个股${skill.name}`,
						generatedBy: `Local Daily Formula · ${skill.id}`,
						summary: report.summary,
						dataScope: report.dataScope,
						content: {
							kind: "stock-research",
							stock: {
								code: stock.code,
								name: stock.name,
								date: reportDate,
								close: reportStock.close,
								pct: reportStock.pct
							},
							skillId: skill.id,
							localCalculation: true,
							raw: report.raw
						},
						raw: report.raw
					});
				}));
			})();
			await Promise.all([formulaTask, localReportsTask]);
		} catch (error) {
			if (requestId === quickRequestRef.current && !formulaError) setQuickError(error instanceof Error ? error.message : "本地快速公式计算失败");
		} finally {
			if (requestId === quickRequestRef.current) setQuickBusy(false);
		}
	}
	async function runStockResearch(skillId = "stock-analysis", label = "综合研究") {
		if (!selected || stockResearchBusy) return;
		const selectedAtStart = selected;
		setStockResearchBusy(true);
		setStockResearchOutput("");
		setStockResearchError("");
		setStockResearchStarted(Date.now());
		setStockResearchElapsed(0);
		setStockResearchSkill(skillId);
		const dailyDegraded = market.degraded === true || market.dataQuality === "degraded" || market.quality === "degraded";
		const currentDayStocks = (market.allStocks?.length ? market.allStocks : market.stocks).filter((s) => (!market.date || s.date === market.date || dailyDegraded) && ![
			"上证指数",
			"深证成指",
			"创业板指",
			"科创50",
			"上证50",
			"北证50"
		].includes(s.name));
		const gainLeaders = currentDayStocks.sort((a, b) => b.pct - a.pct || b.amount - a.amount).slice(0, 20).map(({ code, name, pct, amount, close, market }) => ({
			code,
			name,
			pct,
			amount,
			close,
			market
		}));
		const amountLeaders = [...currentDayStocks].sort((a, b) => b.amount - a.amount || b.pct - a.pct).slice(0, 20).map(({ code, name, pct, amount, close, market }) => ({
			code,
			name,
			pct,
			amount,
			close,
			market
		}));
		const lossLeaders = [...currentDayStocks].sort((a, b) => a.pct - b.pct || b.amount - a.amount).slice(0, 20).map(({ code, name, pct, amount, close, market }) => ({
			code,
			name,
			pct,
			amount,
			close,
			market
		}));
		const limitCandidates = (market.tdxLimitUpCodes || []).map((code) => currentDayStocks.find((s) => s.code === code)).filter(Boolean).slice(0, 30).map((s) => ({
			code: s.code,
			name: s.name,
			pct: s.pct,
			limitPct: s.limitPct,
			streak: s.limitStreak || 0,
			amount: s.amount
		}));
		const limitDownCandidates = (market.tdxLimitDownCodes || []).map((code) => currentDayStocks.find((s) => s.code === code)).filter(Boolean).slice(0, 20).map((s) => ({
			code: s.code,
			name: s.name,
			pct: s.pct,
			limitPct: s.limitPct,
			amount: s.amount
		}));
		try {
			let indexedHistory = selectedAtStart.history || [];
			let historyMeta = {
				status: "fallback",
				source: "page snapshot",
				returned_count: indexedHistory.length,
				history_scope: "PAGE_SNAPSHOT"
			};
			try {
				const indexed = await fetchIndexedStockHistory(selectedAtStart, 0);
				if (Array.isArray(indexed.history) && indexed.history.length) {
					const indexedBars = indexed.history;
					indexedHistory = indexedBars;
					historyMeta = {
						status: "ok",
						source: indexed.source || "Tongdaxin local .day · indexed lookup",
						source_file: indexed.source_file,
						history_scope: indexed.history_scope,
						history_count: indexed.history_count,
						returned_count: indexed.returned_count,
						first_date: indexed.first_date,
						last_date: indexed.last_date,
						full_history_verified: indexed.full_history_verified === true
					};
					setSelected((prev) => prev && prev.code === selectedAtStart.code ? {
						...prev,
						history: indexedBars.slice(-120),
						historyTotal: Number(indexed.history_count || indexedBars.length),
						historyScope: indexed.history_scope || "",
						historySource: indexed.source || ""
					} : prev);
				}
			} catch (error) {
				historyMeta = {
					...historyMeta,
					error: error instanceof Error ? error.message : String(error)
				};
			}
			let tqFormulaForHarness = quickResult && quickResult.symbol === `${selectedAtStart.code}.${selectedAtStart.market.toUpperCase()}` ? quickResult : null;
			if (!tqFormulaForHarness) try {
				tqFormulaForHarness = await fetchTqFormula(selectedAtStart);
			} catch (error) {
				tqFormulaForHarness = {
					status: "missing",
					symbol: `${selectedAtStart.code}.${selectedAtStart.market.toUpperCase()}`,
					source: "通达信 TQ · tdx-local-hub",
					elapsed_ms: 0,
					formulas: [],
					failed_formulas: [],
					error: error instanceof Error ? error.message : "tdx_tq_formula 获取失败"
				};
			}
			let liveResourceLibrary = resourceLibraryContext || {};
			try {
				const response = await fetch(bridgeUrl("/runtime/resource-context"), { cache: "no-store" });
				if (response.ok) {
					liveResourceLibrary = await response.json();
					setResourceLibraryContext(liveResourceLibrary);
				}
			} catch {}
			const raw = (await runHarnessInBackground({
				skillId,
				label,
				expectedSeconds: stockDetailSkills.find((x) => x.id === skillId)?.estimate || stockResearchEstimate,
				originPage: "research",
				originStockCode: selectedAtStart.code,
				task: `请使用“${label}”技能对目标股票做当日只读研究。${HARNESS_JSON_SCHEMA}目标股票的完整本地 TDX 日线已经通过 market/history 索引接口附在 context.history 中；优先使用全量日线计算指标，并在报告中说明实际使用的起止日期和样本数。context.tdx_tq_formula 是本次股票的通达信 TQ 公式现场回执；如果其 status 不是 ok、公式项失败或客户端未打开，必须明确写入缺失/降级边界，不得把它当成有效公式结论。${historyMeta.status === "fallback" ? "如日线索引不可用，必须明确标注使用的是页面快照。" : ""}说明与${label}相关的证据和限制，只能使用传入的行情，禁止买卖建议，不得虚构行业、新闻、龙虎榜或资金流向。`,
				market: {
					date: market.date,
					currentCount: market.currentCount,
					up: market.up,
					down: market.down,
					flat: market.flat,
					amount: market.amount,
					indices: market.indices.map((x) => ({
						name: x.name,
						close: x.close,
						pct: x.pct
					})),
					gainLeaders,
					amountLeaders,
					lossLeaders,
					limitDownCandidates,
					priorLimitUpStats: market.priorLimitUpStats,
					limitCandidates,
					themes: [],
					sectors: market.sectors || [],
					conceptBoards: market.conceptBoards || [],
					intradayProxy: market.intradayProxy,
					dataSources: market.dataSources || {},
					supplemental: market.supplemental,
					tdxLimitUpSource: market.tdxLimitUpFiles || []
				},
				context: {
					targetStock: {
						code: selectedAtStart.code,
						name: selectedAtStart.name,
						date: selectedAtStart.date,
						close: selectedAtStart.close,
						pct: selectedAtStart.pct,
						amount: selectedAtStart.amount,
						previousClose: selectedAtStart.previousClose,
						limitPct: selectedAtStart.limitPct,
						limitStreak: selectedAtStart.limitStreak,
						industryCode: selectedAtStart.industryCode,
						industryName: selectedAtStart.industryName,
						sectorCode: selectedAtStart.sectorCode,
						sectorName: selectedAtStart.sectorName
					},
					history: indexedHistory,
					historyMeta,
					tdx_tq_formula: tqFormulaForHarness,
					resourceLibrary: liveResourceLibrary
				}
			})).output;
			setStockResearchOutput(raw);
			const parsed = normalizeHarnessOutput(raw);
			const now = (/* @__PURE__ */ new Date()).toISOString();
			const reportDate = String(historyMeta.last_date || selectedAtStart.date || market.date);
			await saveReportArchive({
				archiveKey: `stock:${reportDate}:${selectedAtStart.code}:${skillId}`,
				id: createReportId("stock"),
				createdAt: now,
				updatedAt: now,
				date: reportDate,
				title: `个股${label} · ${selectedAtStart.name} · ${dateLabel(reportDate)}`,
				reportType: `个股${label}`,
				generatedBy: `DeepSeek Harness · ${skillId}`,
				summary: parsed.summary || `${label}结果已生成。`,
				dataScope: parsed.dataScope || `本地通达信日线索引 · ${historyMeta.returned_count || indexedHistory.length} 条`,
				content: {
					kind: "stock-research",
					stock: {
						code: selectedAtStart.code,
						name: selectedAtStart.name,
						date: reportDate,
						close: selectedAtStart.close,
						pct: selectedAtStart.pct,
						amount: selectedAtStart.amount,
						industryName: selectedAtStart.industryName,
						sectorName: selectedAtStart.sectorName,
						limitStreak: selectedAtStart.limitStreak
					},
					tdxTqFormula: tqFormulaForHarness,
					skillId,
					raw
				},
				raw
			});
		} catch (error) {
			setStockResearchError(error instanceof Error ? error.message : "个股 Harness 调用失败");
		} finally {
			setStockResearchBusy(false);
			setStockResearchStarted(null);
			setStockResearchElapsed(0);
		}
	}
	const toggleWatch = (c) => setWatch((prev) => {
		const next = prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c];
		try {
			localStorage.setItem("zhangcai.watchlist.v1", JSON.stringify(next));
		} catch {}
		return next;
	});
	const openHarnessTask = (task) => {
		if (task.originPage === "selection" && task.skillId) try {
			localStorage.setItem("zhangcai.strategy.selected.v1", task.skillId);
		} catch {}
		setPage(task.originPage);
		if (task.originStockCode) {
			const stock = (market.allStocks || market.stocks).find((item) => item.code === task.originStockCode);
			if (stock) {
				setSelected(stock);
				if (task.output) window.setTimeout(() => {
					setStockResearchOutput(task.output || "");
					setStockResearchError("");
				}, 0);
			}
		}
		setOpenedHarnessTask(task);
	};
	const selectStockByCode = (rawCode) => {
		const code = String(rawCode || "").replace(/\D/g, "").slice(-6);
		const stock = (market.allStocks || market.stocks).find((item) => item.code === code);
		if (!stock) return false;
		setSelected(stock);
		return true;
	};
	const navigate = (id) => {
		setPage(id);
	};
	const marketSourceLabel = `${market.fallback === true ? String(market.source || "公开行情延时降级") : String(market.source || "本地行情归档 · 通达信/TQ")} · 已持久化到 ${pageHydrated && isDesktopRuntime() ? "桌面资源库" : "本地运行目录"}`;
	const indexSourceSuffix = market.indicesFallback === true ? ` · 指数源公开降级（${dataTimeLabel(market.indicesLatestDataAt)}）` : "";
	const latestMarketDataAt = market.latestDataAt || market.fetchedAt || market.persistedAt;
	const homepageDataNote = page === "overview" ? `数据源 ${marketSourceLabel}${indexSourceSuffix} · 行情日期 ${dateLabel(market.date)} · 最新数据时间 ${dataTimeLabel(latestMarketDataAt)}` : `读取自 ${marketSourceLabel}${indexSourceSuffix} · 行情日期 ${dateLabel(market.date)} · 最新数据时间 ${dataTimeLabel(latestMarketDataAt)}`;
	const indexQuoteLabel = (stock) => stock.realtime === true || stock.quoteMode === "public_delayed" ? `${stock.quoteMode === "public_delayed" || market.indicesFallback === true ? "公开行情延迟" : "实时刷新"} · 刷新于 ${dataTimeLabel(stock.latestDataAt || market.indicesLatestDataAt)}` : `日线收盘 · ${closeDateLabel(stock.date || market.date)}`;
	return /* @__PURE__ */ jsxs(SidebarProvider, {
		style: { "--sidebar-width": "218px" },
		children: [
			/* @__PURE__ */ jsxs(Sidebar, {
				className: "app-sidebar",
				children: [
					/* @__PURE__ */ jsx(SidebarHeader, { children: /* @__PURE__ */ jsxs("div", {
						className: "brand",
						children: [/* @__PURE__ */ jsx("span", {
							className: "brand-symbol",
							"aria-label": "掌财智能体"
						}), /* @__PURE__ */ jsxs("div", { children: ["掌财智能体", /* @__PURE__ */ jsx("small", { children: "ZHANGCAI AGENT" })] })]
					}) }),
					/* @__PURE__ */ jsxs(SidebarContent, { children: [/* @__PURE__ */ jsx("div", {
						className: "nav-label",
						children: "投研工作空间"
					}), /* @__PURE__ */ jsx(SidebarMenu, { children: navItems.map((item, i) => /* @__PURE__ */ jsxs(SidebarMenuItem, { children: [i === 7 && /* @__PURE__ */ jsx("div", {
						className: "nav-label nav-gap",
						children: "研究与管理"
					}), /* @__PURE__ */ jsxs(SidebarMenuButton, {
						isActive: page === item.id,
						className: "nav-item",
						onClick: () => navigate(item.id),
						children: [
							/* @__PURE__ */ jsx(item.icon, { size: 18 }),
							/* @__PURE__ */ jsx("span", { children: item.name }),
							item.id === "skills" && /* @__PURE__ */ jsx("small", {
								className: "count",
								children: "14"
							})
						]
					})] }, item.id)) })] }),
					/* @__PURE__ */ jsxs(SidebarFooter, { children: [
						/* @__PURE__ */ jsxs("div", {
							className: "engine-box",
							children: [/* @__PURE__ */ jsx("span", { className: "engine-dot" }), /* @__PURE__ */ jsxs("span", { children: ["14技能本地运行时", /* @__PURE__ */ jsx("small", { children: "数据预检与落盘" })] })]
						}),
						/* @__PURE__ */ jsxs("button", {
							className: "settings-link",
							onClick: () => navigate("settings"),
							children: [
								/* @__PURE__ */ jsx(Settings2, { size: 17 }),
								"数据与设置",
								/* @__PURE__ */ jsx(ChevronRight, { size: 14 })
							]
						}),
						/* @__PURE__ */ jsxs("div", {
							className: "profile",
							children: [
								/* @__PURE__ */ jsx("span", {
									className: "avatar",
									children: "掌"
								}),
								/* @__PURE__ */ jsxs("div", { children: ["本地研究空间", /* @__PURE__ */ jsx("small", { children: "本地运行版" })] }),
								/* @__PURE__ */ jsx(CircleQuestionMark, { size: 16 })
							]
						})
					] })
				]
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "app-main",
				children: [/* @__PURE__ */ jsxs("header", {
					className: "topbar",
					children: [/* @__PURE__ */ jsxs("div", {
						className: "breadcrumb",
						children: [
							/* @__PURE__ */ jsx(SidebarTrigger, { className: "mobile-trigger" }),
							/* @__PURE__ */ jsx("span", { children: "工作空间" }),
							/* @__PURE__ */ jsx(ChevronRight, { size: 14 }),
							/* @__PURE__ */ jsx("strong", { children: active?.name || "数据与设置" })
						]
					}), /* @__PURE__ */ jsxs("div", {
						className: "top-actions",
						children: [
							/* @__PURE__ */ jsx("span", {
								className: "preview-tag",
								children: "PREVIEW"
							}),
							/* @__PURE__ */ jsx("span", {
								className: "top-date",
								children: dateLabel(market.date)
							}),
							/* @__PURE__ */ jsx("button", {
								className: "icon-button",
								"aria-label": "查看数据状态",
								onClick: () => navigate("settings"),
								children: /* @__PURE__ */ jsx(Database, { size: 17 })
							})
						]
					})]
				}), /* @__PURE__ */ jsxs("main", {
					className: "workspace",
					children: [
						/* @__PURE__ */ jsxs("div", {
							className: "page-heading",
							children: [/* @__PURE__ */ jsxs("div", { children: [
								/* @__PURE__ */ jsx("div", {
									className: "eyebrow",
									children: "MARKET INTELLIGENCE"
								}),
								/* @__PURE__ */ jsxs("h1", { children: [active?.name || "数据与设置", /* @__PURE__ */ jsxs("span", {
									className: "live-label",
									children: [/* @__PURE__ */ jsx("span", {}), page === "overview" ? market.indicesLatestDataAt ? market.indicesFallback === true ? "公开行情降级 · 已刷新" : "主要指数已刷新" : market.fallback === true ? "公开行情降级" : "通达信日线收盘快照" : "本地行情快照"]
								})] }),
								/* @__PURE__ */ jsx("p", { children: "从市场全貌出发，让每一次研究都有据可循。" })
							] }), /* @__PURE__ */ jsxs("div", {
								className: "heading-actions",
								children: [page === "overview" && /* @__PURE__ */ jsxs("div", {
									className: "overview-refresh-actions",
									children: [/* @__PURE__ */ jsxs(Button, {
										variant: "outline",
										className: "market-refresh-button",
										onClick: () => refreshIndices(),
										disabled: indexRefreshing,
										children: [
											indexRefreshing ? /* @__PURE__ */ jsx(LoaderCircle, {
												className: "spin",
												size: 15
											}) : /* @__PURE__ */ jsx(RefreshCw, { size: 15 }),
											" ",
											indexRefreshing ? "正在刷新主要指数…" : "1. 刷新主要指数"
										]
									}), /* @__PURE__ */ jsxs(Button, {
										variant: "outline",
										className: "market-refresh-button",
										onClick: () => refreshMarket(),
										disabled: marketRefreshing,
										children: [
											marketRefreshing ? /* @__PURE__ */ jsx(LoaderCircle, {
												className: "spin",
												size: 15
											}) : /* @__PURE__ */ jsx(RefreshCw, { size: 15 }),
											" ",
											marketRefreshing ? "正在刷新其他参数…" : "2. 刷新其他参数"
										]
									})]
								}), /* @__PURE__ */ jsxs(Button, {
									className: "primary-button",
									onClick: () => navigate("reports"),
									disabled: !pageHydrated,
									children: [
										/* @__PURE__ */ jsx(Sparkles, { size: 16 }),
										pageHydrated ? "开始智能复盘" : "正在加载",
										/* @__PURE__ */ jsx(ArrowUpRight, { size: 15 })
									]
								})]
							})]
						}),
						/* @__PURE__ */ jsxs("div", {
							className: "data-notice",
							children: [
								/* @__PURE__ */ jsx(Database, { size: 14 }),
								/* @__PURE__ */ jsxs("span", { children: [homepageDataNote, marketRefreshMessage && /* @__PURE__ */ jsxs(Fragment$1, { children: [" · ", marketRefreshMessage] })] }),
								/* @__PURE__ */ jsxs("button", {
									onClick: () => navigate("settings"),
									children: ["数据说明", /* @__PURE__ */ jsx(ArrowRight, { size: 13 })]
								})
							]
						}),
						page === "overview" ? /* @__PURE__ */ jsxs(Fragment$1, { children: [
							/* @__PURE__ */ jsx("div", {
								className: "index-grid",
								children: market.indices.map((s, i) => /* @__PURE__ */ jsxs("button", {
									className: "index-card " + (Number(chart) === i ? "index-active" : ""),
									onClick: () => setChart(String(i)),
									children: [
										/* @__PURE__ */ jsxs("div", {
											className: "index-name",
											children: [s.name, /* @__PURE__ */ jsx("span", { children: s.code.toUpperCase() })]
										}),
										/* @__PURE__ */ jsxs("div", {
											className: "index-value",
											children: [/* @__PURE__ */ jsx("strong", { children: number(s.close) }), /* @__PURE__ */ jsxs("span", {
												className: s.pct >= 0 ? "up" : "down",
												children: [pct(s.pct), /* @__PURE__ */ jsx(ArrowUpRight, { size: 13 })]
											})]
										}),
										/* @__PURE__ */ jsx(Sparkline, {
											bars: (Array.isArray(s.history) && s.history.length ? s.history : [s]).slice(-30),
											color: s.pct >= 0 ? "var(--up)" : "var(--down)"
										}),
										/* @__PURE__ */ jsx("small", { children: indexQuoteLabel(s) })
									]
								}, s.code))
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "overview-grid",
								children: [/* @__PURE__ */ jsxs("div", {
									className: "overview-left",
									children: [/* @__PURE__ */ jsxs(Panel, {
										title: "市场走势",
										extra: /* @__PURE__ */ jsx(Tabs, {
											value: chart,
											onValueChange: (v) => setChart(String(v)),
											children: /* @__PURE__ */ jsx(TabsList, { children: market.indices.slice(0, 3).map((s, i) => /* @__PURE__ */ jsx(TabsTrigger, {
												value: String(i),
												children: s.name.slice(0, 3)
											}, s.code)) })
										}),
										children: [
											/* @__PURE__ */ jsxs("div", {
												className: "chart-summary",
												children: [
													/* @__PURE__ */ jsx("span", { className: "chart-legend" }),
													idx?.name,
													/* @__PURE__ */ jsx("b", { children: number(idx?.close || 0) }),
													/* @__PURE__ */ jsx("span", {
														className: (idx?.pct || 0) >= 0 ? "up" : "down",
														children: pct(idx?.pct || 0)
													}),
													/* @__PURE__ */ jsx("small", { children: idx?.realtime === true || idx?.quoteMode === "public_delayed" ? indexQuoteLabel(idx) : "近 60 个交易日 · 收盘价格" })
												]
											}),
											idx && /* @__PURE__ */ jsx(Sparkline, {
												bars: Array.isArray(idx.history) && idx.history.length ? idx.history : [idx],
												large: true
											}),
											/* @__PURE__ */ jsxs("div", {
												className: "chart-axis",
												children: [
													/* @__PURE__ */ jsx("span", { children: idx && Array.isArray(idx.history) && idx.history.length ? dateLabel(idx.history[0].date) : idx ? dateLabel(idx.date) : "" }),
													/* @__PURE__ */ jsx("span", { children: "日线走势" }),
													/* @__PURE__ */ jsx("span", { children: dateLabel(idx?.date || market.date) })
												]
											})
										]
									}), /* @__PURE__ */ jsxs(Panel, {
										title: "市场宽度",
										extra: /* @__PURE__ */ jsxs("span", {
											className: "subtle",
											children: [
												"同日样本 ",
												number(market.currentCount),
												" 只"
											]
										}),
										children: [
											/* @__PURE__ */ jsxs("div", {
												className: "breadth-stats",
												children: [
													/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("span", { children: "上涨" }), /* @__PURE__ */ jsxs("b", {
														className: "up",
														children: [number(market.up), /* @__PURE__ */ jsx("small", { children: "只" })]
													})] }),
													/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("span", { children: "下跌" }), /* @__PURE__ */ jsxs("b", {
														className: "down",
														children: [number(market.down), /* @__PURE__ */ jsx("small", { children: "只" })]
													})] }),
													/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("span", { children: "平盘" }), /* @__PURE__ */ jsxs("b", { children: [market.flat, /* @__PURE__ */ jsx("small", { children: "只" })] })] }),
													/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("span", { children: "样本成交额" }), /* @__PURE__ */ jsxs("b", { children: [(market.amount / 0xe8d4a51000).toFixed(2), /* @__PURE__ */ jsx("small", { children: "万亿" })] })] })
												]
											}),
											/* @__PURE__ */ jsxs("div", {
												className: "breadth-bar",
												children: [
													/* @__PURE__ */ jsx("span", { style: {
														flex: market.up,
														background: "var(--up)"
													} }),
													/* @__PURE__ */ jsx("span", { style: {
														flex: market.flat,
														background: "#ccd1d9"
													} }),
													/* @__PURE__ */ jsx("span", { style: {
														flex: market.down,
														background: "var(--down)"
													} })
												]
											}),
											/* @__PURE__ */ jsx("div", {
												className: "distribution",
												children: market.bins.map((b, i) => /* @__PURE__ */ jsxs("div", { children: [
													/* @__PURE__ */ jsx("small", { children: b }),
													/* @__PURE__ */ jsx("span", { style: {
														height: Math.max(3, b / Math.max(...market.bins) * 63) + "px",
														background: i < 3 ? "var(--down)" : i === 3 ? "#a8b0bc" : "var(--up)",
														opacity: i === 2 || i === 4 ? .6 : 1
													} }),
													/* @__PURE__ */ jsx("label", { children: [
														"＜−7%",
														"−7~−3%",
														"−3~0%",
														"平盘",
														"0~3%",
														"3~7%",
														"＞7%"
													][i] })
												] }, i))
											})
										]
									})]
								}), /* @__PURE__ */ jsxs("aside", {
									className: "insight-rail",
									children: [
										/* @__PURE__ */ jsxs("section", {
											className: "agent-card",
											children: [
												/* @__PURE__ */ jsxs("div", {
													className: "agent-title",
													children: [
														/* @__PURE__ */ jsx("span", {
															className: "agent-spark",
															children: /* @__PURE__ */ jsx(Sparkles, { size: 19 })
														}),
														/* @__PURE__ */ jsx("strong", { children: "掌财观察" }),
														/* @__PURE__ */ jsx("span", { children: "数据摘要" })
													]
												}),
												/* @__PURE__ */ jsxs("h2", { children: [
													"先看广度，",
													/* @__PURE__ */ jsx("br", {}),
													"再找结构性机会。"
												] }),
												/* @__PURE__ */ jsxs("p", { children: [
													"本地同日样本中，上涨占比 ",
													/* @__PURE__ */ jsxs("b", { children: [(market.up / market.currentCount * 100).toFixed(1), "%"] }),
													"。行情日期和覆盖范围已保留，尚未调用模型生成投研结论。"
												] }),
												/* @__PURE__ */ jsx("div", { className: "agent-divider" }),
												/* @__PURE__ */ jsxs("div", {
													className: "check-row",
													children: [/* @__PURE__ */ jsx(ShieldCheck, { size: 16 }), "保留来源与日期"]
												}),
												/* @__PURE__ */ jsxs("div", {
													className: "check-row",
													children: [/* @__PURE__ */ jsx(Activity, { size: 16 }), "情绪与主线研判待接入"]
												}),
												/* @__PURE__ */ jsxs(Button, {
													onClick: () => navigate("research"),
													className: "agent-button",
													children: ["进入个股研究", /* @__PURE__ */ jsx(ArrowRight, { size: 16 })]
												})
											]
										}),
										/* @__PURE__ */ jsx(Panel, {
											title: "研究路径",
											extra: /* @__PURE__ */ jsx(Workflow, { size: 16 }),
											children: /* @__PURE__ */ jsx("div", {
												className: "workflow-list",
												children: [
													[
														"01",
														"看市场",
														"情绪周期 · 热点舆情",
														"mainline"
													],
													[
														"02",
														"找机会",
														"主线评分 · 策略筛选",
														"selection"
													],
													[
														"03",
														"做验证",
														"个股研究 · 风险排雷",
														"research"
													]
												].map(([n, t, d, p]) => /* @__PURE__ */ jsxs("button", {
													onClick: () => navigate(p),
													children: [
														/* @__PURE__ */ jsx("span", { children: n }),
														/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("strong", { children: t }), /* @__PURE__ */ jsx("small", { children: d })] }),
														/* @__PURE__ */ jsx(ChevronRight, { size: 15 })
													]
												}, n))
											})
										}),
										/* @__PURE__ */ jsxs("div", {
											className: "mini-note",
											children: [
												/* @__PURE__ */ jsx(BookOpen, { size: 17 }),
												/* @__PURE__ */ jsxs("p", { children: ["14 项电脑版技能", /* @__PURE__ */ jsx("small", { children: "按投研流程组织，保留独立入口" })] }),
												/* @__PURE__ */ jsx("button", {
													"aria-label": "打开技能中心",
													onClick: () => navigate("skills"),
													children: /* @__PURE__ */ jsx(ArrowUpRight, { size: 17 })
												})
											]
										})
									]
								})]
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "bottom-grid",
								children: [/* @__PURE__ */ jsx(Panel, {
									title: "当日涨幅榜候选",
									extra: /* @__PURE__ */ jsxs("button", {
										className: "text-link",
										onClick: () => navigate("research"),
										children: ["全部个股", /* @__PURE__ */ jsx(ArrowRight, { size: 14 })]
									}),
									children: /* @__PURE__ */ jsx(StockTable, {
										stocks: market.stocks.slice(0, 5),
										asOfDate: market.date,
										onSelect: setSelected,
										watch,
										onWatch: toggleWatch
									})
								}), /* @__PURE__ */ jsxs(Panel, {
									title: "主线观察",
									extra: /* @__PURE__ */ jsx("span", {
										className: "example-label",
										children: "参考样例 · 09-04"
									}),
									children: [/* @__PURE__ */ jsx("div", {
										className: "theme-list",
										children: [
											[
												"01",
												"养猪",
												"产业催化",
												"7 家涨停"
											],
											[
												"02",
												"大消费",
												"政策驱动",
												"7 家涨停"
											],
											[
												"03",
												"大农业",
												"期货催化",
												"4 家涨停"
											],
											[
												"04",
												"福建自贸",
												"区域主题",
												"5 家涨停"
											]
										].map(([n, t, d, v]) => /* @__PURE__ */ jsxs("button", {
											onClick: () => navigate("mainline"),
											children: [
												/* @__PURE__ */ jsx("span", { children: n }),
												/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: t }), /* @__PURE__ */ jsx("small", { children: d })] }),
												/* @__PURE__ */ jsx("label", { children: v }),
												/* @__PURE__ */ jsx(ChevronRight, { size: 14 })
											]
										}, n))
									}), /* @__PURE__ */ jsx("div", {
										className: "panel-footnote",
										children: "来自连板网参考 PDF 的历史样例，与本地行情分开呈现。"
									})]
								})]
							})
						] }) : /* @__PURE__ */ jsx(WorkspacePages, {
							page,
							market,
							onSelect: setSelected,
							onSelectCode: selectStockByCode,
							onRefreshMarket: () => refreshMarket(),
							marketRefreshing,
							marketRefreshMessage,
							watch,
							onWatch: toggleWatch,
							navigate
						}, page),
						/* @__PURE__ */ jsxs("footer", {
							className: "workspace-footer",
							children: [
								/* @__PURE__ */ jsxs("span", { children: [
									/* @__PURE__ */ jsx("span", { className: "footer-dot" }),
									"本地行情 · ",
									number(market.total),
									" 只股票"
								] }),
								/* @__PURE__ */ jsx("span", { children: "研究辅助工具 · 数据与模型输出需独立核验" }),
								/* @__PURE__ */ jsx("span", { children: "掌财智能体 © 2026" })
							]
						})
					]
				})]
			}),
			/* @__PURE__ */ jsx(HarnessTaskTray, {
				tasks: harnessTasks,
				currentDate: market.date,
				now: harnessNow,
				onOpen: openHarnessTask,
				onDismiss: dismissHarnessTask
			}),
			openedHarnessTask?.output && /* @__PURE__ */ jsx(HarnessTaskResult, {
				task: openedHarnessTask,
				onClose: () => setOpenedHarnessTask(null)
			}),
			/* @__PURE__ */ jsx(Sheet, {
				open: !!selected,
				onOpenChange: (v) => !v && setSelected(null),
				children: /* @__PURE__ */ jsxs(SheetContent, {
					className: "stock-sheet",
					children: [/* @__PURE__ */ jsxs(SheetHeader, { children: [/* @__PURE__ */ jsxs(SheetTitle, {
						className: "stock-detail-title",
						children: [
							selected?.name,
							" ",
							/* @__PURE__ */ jsx("small", { children: selected?.code })
						]
					}), /* @__PURE__ */ jsx(SheetDescription, { children: quoteRefreshing ? "正在刷新盘中价格…" : intradayQuote ? quoteMode === "local_daily_close" ? "仅有最近收盘价" : "盘中价格" : "盘中价格暂不可用" })] }), selected && /* @__PURE__ */ jsxs("div", {
						className: "detail-body",
						children: [
							/* @__PURE__ */ jsxs("div", {
								className: "detail-price",
								children: [
									/* @__PURE__ */ jsx("small", { children: intradayQuote && quoteMode !== "local_daily_close" ? quoteMode === "public_delayed" ? "盘中价格（公开行情延迟）" : "盘中价格" : closeDateLabel(selected.date) }),
									Number(intradayQuote?.close ?? selected.close).toFixed(2),
									/* @__PURE__ */ jsx("span", {
										className: Number(intradayQuote?.pct ?? selected.pct) >= 0 ? "up" : "down",
										children: pct(Number(intradayQuote?.pct ?? selected.pct))
									})
								]
							}),
							quoteError && /* @__PURE__ */ jsx("p", {
								className: "form-error",
								role: "alert",
								children: quoteError
							}),
							selected.history.length > 0 && /* @__PURE__ */ jsx(Sparkline, {
								bars: selected.history,
								large: true
							}),
							/* @__PURE__ */ jsx("div", {
								className: "detail-grid",
								children: [
									["日线开盘", selected.open],
									["日线最高", selected.high],
									["日线最低", selected.low],
									["成交额（亿）", selected.amount / 1e8]
								].map(([k, v]) => /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("small", { children: k }), /* @__PURE__ */ jsx("b", { children: Number(v).toFixed(2) })] }, String(k)))
							}),
							quickBusy && /* @__PURE__ */ jsxs("div", {
								className: "harness-progress",
								role: "status",
								children: [/* @__PURE__ */ jsx(LoaderCircle, {
									className: "spin",
									size: 15
								}), /* @__PURE__ */ jsx("span", { children: "本地五公式计算中 · 通常 10 秒内返回" })]
							}),
							quickError && /* @__PURE__ */ jsx("p", {
								className: "form-error",
								role: "alert",
								children: quickError
							}),
							/* @__PURE__ */ jsx(LocalQuickMetrics, { stock: selected }),
							quickResult && /* @__PURE__ */ jsx(QuickFormulaOutput, { value: quickResult }),
							/* @__PURE__ */ jsxs("div", {
								className: "detail-actions",
								children: [/* @__PURE__ */ jsxs(Button, {
									variant: "outline",
									disabled: quoteRefreshing,
									onClick: () => setQuoteRefreshNonce((value) => value + 1),
									children: [/* @__PURE__ */ jsx(RefreshCw, {
										className: quoteRefreshing ? "spin" : "",
										size: 15
									}), quoteRefreshing ? "刷新盘中价格中" : "刷新盘中价格"]
								}), /* @__PURE__ */ jsxs(Button, {
									onClick: () => toggleWatch(selected.code),
									children: [/* @__PURE__ */ jsx(Star, { size: 15 }), watch.includes(selected.code) ? "移出自选" : "加入自选"]
								})]
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "stock-analysis-actions",
								children: [/* @__PURE__ */ jsx("b", { children: "十项技能" }), /* @__PURE__ */ jsx("div", {
									className: "skill-action-grid",
									children: stockDetailSkills.map((skill) => skill.mode === "quick" ? /* @__PURE__ */ jsxs("div", {
										className: "skill-action-card",
										children: [/* @__PURE__ */ jsxs(Button, {
											variant: "outline",
											disabled: true,
											children: [/* @__PURE__ */ jsx(ChartCandlestick, { size: 15 }), skill.name]
										}), /* @__PURE__ */ jsx("small", { children: "已在上方秒算" })]
									}, skill.id) : /* @__PURE__ */ jsxs("div", {
										className: "skill-action-card",
										children: [/* @__PURE__ */ jsxs(Button, {
											variant: "outline",
											disabled: stockResearchBusy,
											onClick: () => runStockResearch(skill.id, skill.name),
											children: [/* @__PURE__ */ jsx(Sparkles, { size: 15 }), skill.name]
										}), /* @__PURE__ */ jsxs("small", { children: ["Harness · 预计 ", formatTimer(skill.estimate)] })]
									}, skill.id))
								})]
							}),
							/* @__PURE__ */ jsx("p", {
								className: "harness-eta",
								children: "需要深度研究的技能会调用 DeepSeek Harness；运行期间显示计时器并自动保存报告。"
							}),
							stockResearchBusy && /* @__PURE__ */ jsxs("div", {
								className: `harness-progress ${stockResearchElapsed > (stockDetailSkills.find((x) => x.id === stockResearchSkill)?.estimate || stockResearchEstimate) ? "overdue" : ""}`,
								role: "status",
								children: [/* @__PURE__ */ jsx(LoaderCircle, {
									className: "spin",
									size: 15
								}), /* @__PURE__ */ jsxs("span", { children: [
									stockDetailSkills.find((x) => x.id === stockResearchSkill)?.name || stockResearchSkill,
									" 运行中 · 已运行 ",
									formatTimer(stockResearchElapsed),
									" · 预计 ",
									formatTimer(stockDetailSkills.find((x) => x.id === stockResearchSkill)?.estimate || stockResearchEstimate),
									stockResearchElapsed > (stockDetailSkills.find((x) => x.id === stockResearchSkill)?.estimate || stockResearchEstimate) ? " · 已超过预计时间，仍在等待 Harness 返回" : ""
								] })]
							}),
							stockResearchError && /* @__PURE__ */ jsx("p", {
								className: "form-error",
								role: "alert",
								children: stockResearchError
							}),
							stockResearchOutput && /* @__PURE__ */ jsx(StockResearchOutput, {
								raw: stockResearchOutput,
								stock: selected
							}),
							" ",
							/* @__PURE__ */ jsx("div", {
								className: "data-notice",
								children: "本地公式结果来自 tdx-local-hub 技能；分类研究通过 DeepSeek Harness 调用对应技能并自动存入“我的报告”。"
							})
						]
					})]
				})
			})
		]
	});
}
//#endregion
export { Home as default };
