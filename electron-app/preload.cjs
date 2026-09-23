const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('zhangcaiDesktop', {
  chooseTdxDirectory: () => ipcRenderer.invoke('tdx:choose-directory'),
  restart: () => ipcRenderer.invoke('desktop:restart'),
  openTdxDownload: () => ipcRenderer.invoke('desktop:open-external', 'https://data.tdx.com.cn/mock/new_tdx_mock.exe'),
});
