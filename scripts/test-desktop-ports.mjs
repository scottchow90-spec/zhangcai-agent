import { findFreePort } from '../electron-app/runtime-ports.mjs';

const legacyWebPorts = [3003, 3004, 4319];
const uiPort = await findFreePort(34303, { avoid: legacyWebPorts });
const bridgePort = await findFreePort(44319, { avoid: [...legacyWebPorts, uiPort] });
const isolated = !legacyWebPorts.includes(uiPort)
  && !legacyWebPorts.includes(bridgePort)
  && uiPort !== bridgePort;
if (!isolated) throw new Error(`桌面端口隔离失败：${uiPort}, ${bridgePort}`);
console.log(JSON.stringify({ status: 'PASS', legacyWebPorts, desktopUiPort: uiPort, desktopBridgePort: bridgePort, isolated }, null, 2));
