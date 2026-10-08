import assert from 'node:assert/strict';
import { sameTdxRoot, selectTdxRoot } from '../electron-app/tdx-root.mjs';

const validRoots = new Set([
  'c:\\new_tdx_mock',
  'd:\\program files\\new_tdx_mock',
  'e:\\tdx-copy',
]);
const isValidRoot = (root) => validRoots.has(String(root).replaceAll('/', '\\').replace(/[\\]+$/, '').toLocaleLowerCase('en-US'));

assert.equal(
  selectTdxRoot({
    configuredRoots: ['C:\\new_tdx_mock'],
    runningRoots: ['D:\\Program Files\\new_tdx_mock'],
    isValidRoot,
  }),
  'D:\\Program Files\\new_tdx_mock',
  'a stale but valid C: setting must not override the running D: client',
);

assert.equal(
  selectTdxRoot({
    configuredRoots: ['E:\\tdx-copy'],
    runningRoots: ['C:\\new_tdx_mock', 'D:\\Program Files\\new_tdx_mock'],
    isValidRoot,
  }),
  'C:\\new_tdx_mock',
  'when multiple clients run, choose the configured installation if it is one of them',
);

assert.equal(
  selectTdxRoot({
    configuredRoots: ['E:\\tdx-copy', 'C:\\new_tdx_mock'],
    runningRoots: [],
    isValidRoot,
  }),
  'E:\\tdx-copy',
  'without a running client, retain the saved configuration order',
);

assert.equal(
  selectTdxRoot({ configuredRoots: ['Z:\\missing'], runningRoots: [], isValidRoot }),
  '',
  'ignore invalid paths instead of passing them to formula scripts',
);

assert.equal(
  sameTdxRoot('d:/Program Files/new_tdx_mock/', 'D:\\Program Files\\new_tdx_mock'),
  true,
  'Windows paths with spaces, slash variation, and case differences compare equal',
);

console.log('TDX root resolution tests passed (stale C:, active D:, multiple clients, invalid roots, path normalization).');
