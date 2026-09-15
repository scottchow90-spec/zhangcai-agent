import tailwindcss from '@tailwindcss/postcss';
import vinext from 'vinext';
import { defineConfig } from 'vite';

export default defineConfig(async () => {
  return {
    css: { postcss: { plugins: [tailwindcss()] } },
    server: {
      host: true,
      port: 3001,
      // The app is exposed through an SSH reverse tunnel and an Nginx
      // sub-path. Vite's dev HMR socket cannot be reliably addressed from
      // that external origin, so disable HMR for the shared preview. Normal
      // page refreshes and application API interactions remain enabled.
      hmr: false,
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
