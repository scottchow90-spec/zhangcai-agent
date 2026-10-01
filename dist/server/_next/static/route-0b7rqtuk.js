import path from "node:path";
import { existsSync } from "node:fs";
import { spawn } from "node:child_process";
//#region app/api/runtime/ensure-bridge/route.ts
var runtime = "nodejs";
var launchInProgress = false;
async function POST() {
	const port = Number(process.env.ZHANGCAI_BRIDGE_PORT || 4319);
	if (process.env.ZHANGCAI_PACKAGED === "1") return Response.json({
		status: "ready",
		packaged: true,
		port
	});
	const appRoot = path.resolve(process.env.ZHANGCAI_APP_ROOT || process.cwd());
	const launcher = path.join(appRoot, "scripts", "start-local.ps1");
	if (!existsSync(launcher)) return Response.json({
		status: "error",
		error: `本地启动脚本不存在：${launcher}`
	}, { status: 500 });
	if (!launchInProgress) {
		launchInProgress = true;
		spawn("powershell.exe", [
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			launcher
		], {
			cwd: appRoot,
			detached: true,
			windowsHide: true,
			stdio: "ignore"
		}).unref();
		setTimeout(() => {
			launchInProgress = false;
		}, 5e3);
	}
	return Response.json({
		status: "starting",
		port,
		launcher: "scripts/start-local.ps1"
	}, { status: 202 });
}
//#endregion
export { POST, runtime };
