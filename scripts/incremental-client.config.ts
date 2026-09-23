import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readFileSync } from 'node:fs';
import { defineConfig } from 'vite';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const version = JSON.parse(readFileSync(path.join(root, 'package.json'), 'utf8')).version;

// Rebuild only the interactive home component when the full Vinext graph
// would exceed a small packaging machine's available memory.
export default defineConfig({
  root,
  resolve: { alias: { '@': root } },
  build: {
    outDir: path.join(root, 'packaging', `.incremental-client-probe-${version}`),
    emptyOutDir: true,
    minify: false,
    sourcemap: false,
    lib: {
      entry: path.join(root, 'scripts', 'incremental-client-entry.tsx'),
      formats: ['es'],
      fileName: () => 'incremental-client-entry.js',
    },
    rollupOptions: {
      external: ['react', 'react/jsx-runtime'],
      output: { inlineDynamicImports: true },
    },
  },
});
