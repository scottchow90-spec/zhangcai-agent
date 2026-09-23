import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const version = JSON.parse(fs.readFileSync(path.join(projectRoot, 'package.json'), 'utf8')).version;
const probeRoot = path.join(projectRoot, 'packaging', `.incremental-client-probe-${version}`);
const chunkRoot = path.join(projectRoot, 'dist', 'client', '_next', 'static', 'chunks');

function findSingleChunk(pattern, label) {
  const matches = fs.readdirSync(chunkRoot)
    .filter((name) => pattern.test(name))
    .map((name) => path.join(chunkRoot, name))
    .filter((file) => fs.statSync(file).isFile());
  if (matches.length !== 1) {
    throw new Error(`Expected exactly one ${label} in ${chunkRoot}, found ${matches.length}: ${matches.map(path.basename).join(', ')}`);
  }
  return matches[0];
}

function requireFile(file, label) {
  if (!fs.existsSync(file)) throw new Error(`Missing ${label}: ${file}`);
  return file;
}

const probeChunk = fs.readdirSync(probeRoot)
  .filter((name) => /^incremental-client-entry(?:-.*)?\.js$/.test(name))
  .map((name) => path.join(probeRoot, name))
  .find((file) => fs.statSync(file).isFile());
if (!probeChunk) throw new Error(`Incremental client bundle not found under ${probeRoot}`);

const frameworkFile = findSingleChunk(/^framework-(?!.*-shim\.js$).+\.js$/, 'framework chunk');
const target = findSingleChunk(/^home-client-.*\.js$/, 'Home client chunk');
const frameworkChunk = path.basename(frameworkFile);
requireFile(frameworkFile, 'verified framework chunk');
requireFile(target, 'existing Home client chunk');
let bundle = fs.readFileSync(probeChunk, 'utf8');
bundle = bundle
  .replaceAll('from "react/jsx-runtime"', `from "./framework-jsx-runtime-shim.js"`)
  .replaceAll('from "react"', `from "./framework-react-shim.js"`);
// Some production dependencies are emitted as CommonJS wrappers even when
// the entry imports React as ESM. Their generated __require("react") call is
// not available in a browser module, so point it at the same verified runtime
// object instead of leaving a browser-only bundle that fails during hydration.
bundle = `import ReactRuntime from "./framework-react-shim.js";\n${bundle}`
  .replaceAll('__require("react")', 'ReactRuntime')
  .replaceAll("__require('react')", 'ReactRuntime');
if (bundle.includes('from "react"') || bundle.includes('from "react/jsx-runtime"')) {
  throw new Error('Incremental bundle still contains a bare React import.');
}
if (bundle.includes('__require("react")') || bundle.includes("__require('react')")) {
  throw new Error('Incremental bundle still contains a browser-incompatible React require.');
}
if (!bundle.includes('export { Home as default }')) {
  throw new Error('Incremental bundle does not expose Home as its default export.');
}

// Vinext's framework chunk exports CommonJS module factories.  Importing the
// factory itself looks superficially correct, but it leaves React.createContext
// undefined in the browser.  Invoke the factory once so the shim exposes the
// actual React and jsx-runtime objects used by the generated framework.
const reactShim = `import { i as reactFactory } from "./${frameworkChunk}";
const React = reactFactory();
export default React;
export const Activity = React.Activity;
export const Children = React.Children;
export const Component = React.Component;
export const Fragment = React.Fragment;
export const Profiler = React.Profiler;
export const PureComponent = React.PureComponent;
export const StrictMode = React.StrictMode;
export const Suspense = React.Suspense;
export const __CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE = React.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE;
export const __COMPILER_RUNTIME = React.__COMPILER_RUNTIME;
export const act = React.act;
export const cache = React.cache;
export const cacheSignal = React.cacheSignal;
export const captureOwnerStack = React.captureOwnerStack;
export const cloneElement = React.cloneElement;
export const createContext = React.createContext;
export const createElement = React.createElement;
export const createRef = React.createRef;
export const forwardRef = React.forwardRef;
export const isValidElement = React.isValidElement;
export const lazy = React.lazy;
export const memo = React.memo;
export const startTransition = React.startTransition;
export const unstable_useCacheRefresh = React.unstable_useCacheRefresh;
export const use = React.use;
export const useActionState = React.useActionState;
export const useCallback = React.useCallback;
export const useContext = React.useContext;
export const useDebugValue = React.useDebugValue;
export const useDeferredValue = React.useDeferredValue;
export const useEffect = React.useEffect;
export const useEffectEvent = React.useEffectEvent;
export const useId = React.useId;
export const useImperativeHandle = React.useImperativeHandle;
export const useInsertionEffect = React.useInsertionEffect;
export const useLayoutEffect = React.useLayoutEffect;
export const useMemo = React.useMemo;
export const useOptimistic = React.useOptimistic;
export const useReducer = React.useReducer;
export const useRef = React.useRef;
export const useState = React.useState;
export const useSyncExternalStore = React.useSyncExternalStore;
export const useTransition = React.useTransition;
export const version = React.version;
`;
const jsxShim = `import { r as jsxRuntimeFactory } from "./${frameworkChunk}";
const jsxRuntime = jsxRuntimeFactory();
export const Fragment = jsxRuntime.Fragment;
export const jsx = jsxRuntime.jsx;
export const jsxs = jsxRuntime.jsxs;
export const jsxDEV = jsxRuntime.jsxDEV;
`;

fs.writeFileSync(path.join(chunkRoot, 'framework-react-shim.js'), reactShim, 'utf8');
fs.writeFileSync(path.join(chunkRoot, 'framework-jsx-runtime-shim.js'), jsxShim, 'utf8');
fs.writeFileSync(target, bundle, 'utf8');

// The interactive component build does not rebuild the global stylesheet.
// Carry the small detail-price override into the existing verified CSS asset.
const sourceCss = fs.readFileSync(path.join(projectRoot, 'app', 'globals.css'), 'utf8');
const cssMarker = '.stock-sheet .detail-price{font-size:clamp(42px,6vw,56px)';
const markerAt = sourceCss.indexOf(cssMarker);
if (markerAt < 0) throw new Error('Missing detail-price stylesheet override.');
const cssOverride = sourceCss.slice(markerAt).trim();
const cssRoot = path.join(projectRoot, 'dist', 'client', '_next', 'static', 'css');
const cssFiles = fs.readdirSync(cssRoot).filter((name) => name.endsWith('.css'));
if (cssFiles.length !== 1) throw new Error(`Expected one verified CSS asset, found ${cssFiles.length}`);
const cssTarget = path.join(cssRoot, cssFiles[0]);
const existingCss = fs.readFileSync(cssTarget, 'utf8');
if (!existingCss.includes(cssMarker)) fs.writeFileSync(cssTarget, `${existingCss}\n${cssOverride}\n`, 'utf8');

console.log(JSON.stringify({
  status: 'PASS',
  source: probeChunk,
  target,
  bytes: Buffer.byteLength(bundle),
  frameworkChunk,
  shims: ['framework-react-shim.js', 'framework-jsx-runtime-shim.js'],
  css: cssTarget,
}, null, 2));
