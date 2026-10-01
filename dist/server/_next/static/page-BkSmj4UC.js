import { t as require_jsx_runtime_react_server } from "./framework~index~app-page-cache-render~app-page-cache~seed-cache~page~layout~page~app-route-~fe2f04fu-CQIcBs6F.js";
import { V as registerClientReference } from "../../index.js";
//#region app/chat/chat-client.tsx
var chat_client_default = /* @__PURE__ */ registerClientReference(() => {
	throw new Error("Unexpectedly client reference export 'default' is called on server");
}, "878821595ec6", "default");
//#endregion
//#region app/chat/page.tsx
var import_jsx_runtime_react_server = require_jsx_runtime_react_server();
var dynamic = "force-dynamic";
var revalidate = 0;
var metadata = {
	title: "掌财研究工作台",
	description: "股票技能聊天工作台：确认后运行，研究报告本地归档。"
};
function ChatPage() {
	return /* @__PURE__ */ (0, import_jsx_runtime_react_server.jsx)(chat_client_default, {});
}
//#endregion
export { ChatPage as default, dynamic, metadata, revalidate };
