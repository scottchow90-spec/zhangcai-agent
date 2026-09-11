import tailwindcss from '@tailwindcss/postcss';
import vinext from 'vinext';
import { defineConfig } from 'vite';

export default defineConfig(async () => {
  return {
    css: { postcss: { plugins: [tailwindcss()] } },
    server: {
      host: true,
      port: 3001,
      // Harness/TDX 在 data/runtime 下会创建短生命周期临时目录；Vite
      // 监视这些目录会在 Windows 上触发 EBUSY 并导致开发服务退出。
      watch: { ignored: ['**/data/**', '**/.cache/**', '**/runtime-results/**'] },
      proxy: {
        '/bridge': {
          target: 'http://127.0.0.1:4318',
          changeOrigin: false,
          rewrite: (requestPath: string) => requestPath.replace(/^\/bridge/, ''),
        },
      },
    },
    plugins: [vinext()],
  };
});
