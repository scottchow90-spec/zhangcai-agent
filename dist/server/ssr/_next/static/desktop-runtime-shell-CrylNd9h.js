import { a as RefreshCw, i as X, n as bridgeUrl, o as Database, s as createLucideIcon } from "./bridge-url-D6eZPRbG.js";
import { t as CircleCheck } from "./circle-check-CxmyBrLe.js";
import { t as Activity } from "./activity-J2y4hB5k.js";
import { useEffect, useRef, useState } from "react";
import { Fragment as Fragment$1, jsx, jsxs } from "react/jsx-runtime";
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var House = createLucideIcon("house", [["path", {
	d: "M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8",
	key: "5wwlr5"
}], ["path", {
	d: "M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",
	key: "r6nss1"
}]]);
/**
* @license lucide-react v1.31.0 - ISC
*
* This source code is licensed under the ISC license.
* See the LICENSE file in the root directory of this source tree.
*/
var MessageSquare = createLucideIcon("message-square", [["path", {
	d: "M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z",
	key: "18887p"
}]]);
//#endregion
//#region app/desktop-runtime-shell.tsx
function uiUrl(pathname) {
	const next = new URL(pathname, window.location.href);
	next.searchParams.set("desktop", "1");
	const bridge = new URLSearchParams(window.location.search).get("bridge");
	if (bridge) next.searchParams.set("bridge", bridge);
	return next.toString();
}
function resultMessage(body, fallback) {
	if (typeof body.message === "string" && body.message) return body.message;
	if (typeof body.error === "string" && body.error) return body.error;
	if (typeof body.status === "string" && body.status) return `${fallback}：${body.status}`;
	return fallback;
}
function minuteDataLabel(value) {
	if (!value || value.status === "missing") return "未发现（普通任务不依赖）";
	if (value.status === "available") return `外置按需（${value.fileCount || 0} 个）`;
	return value.status || "未知";
}
function tdxStatusLabel(status) {
	switch (status) {
		case "open": return "已检测运行";
		case "closed": return "未运行";
		case "path_mismatch": return "运行目录不匹配";
		case "open_unverified": return "检测到进程，路径未确认";
		default: return "未知";
	}
}
function DesktopRuntimeShell() {
	const [enabled, setEnabled] = useState(false);
	const [notice, setNotice] = useState("桌面运行时已隔离");
	const [environment, setEnvironment] = useState(null);
	const [busy, setBusy] = useState("");
	const [credentialInput, setCredentialInput] = useState("");
	const environmentRequestRef = useRef(0);
	useEffect(() => {
		setEnabled(new URLSearchParams(window.location.search).get("desktop") === "1");
	}, []);
	if (!enabled) return null;
	async function inspectEnvironment() {
		const requestId = ++environmentRequestRef.current;
		setEnvironment((current) => current ? {
			...current,
			loading: true,
			refreshing: false,
			error: void 0
		} : {
			loading: true,
			bridge: { status: "读取中" },
			harness: { status: "读取中" },
			tdx: { status: "读取中" }
		});
		setNotice("正在打开运行环境…");
		setBusy("environment");
		try {
			const response = await fetch(bridgeUrl("/runtime/environment?summary=1"), { cache: "no-store" });
			const body = await response.json().catch(() => ({}));
			if (!response.ok) throw new Error(resultMessage(body, `运行环境检测失败（${response.status}）`));
			if (requestId !== environmentRequestRef.current) return;
			setEnvironment({
				...body,
				summary: true,
				loading: false,
				refreshing: false
			});
			setNotice(body.stale ? "已显示最近缓存状态；需要时可手动刷新详细检查" : "已显示运行环境缓存状态");
		} catch (error) {
			if (requestId === environmentRequestRef.current) {
				setEnvironment((current) => current ? {
					...current,
					loading: false,
					refreshing: false,
					error: error instanceof Error ? error.message : "运行环境检测失败"
				} : current);
				setNotice(error instanceof Error ? error.message : "运行环境检测失败");
			}
		} finally {
			if (requestId === environmentRequestRef.current) setBusy("");
		}
	}
	async function refreshEnvironmentDetails() {
		const requestId = ++environmentRequestRef.current;
		setEnvironment((current) => current ? {
			...current,
			refreshing: true,
			error: void 0
		} : current);
		setBusy("environment-details");
		setNotice("正在执行详细环境诊断…");
		try {
			const response = await fetch(bridgeUrl("/runtime/environment"), { cache: "no-store" });
			const body = await response.json().catch(() => ({}));
			if (!response.ok) throw new Error(resultMessage(body, `详细检查失败（${response.status}）`));
			if (requestId !== environmentRequestRef.current) return;
			setEnvironment({
				...body,
				summary: false,
				loading: false,
				refreshing: false
			});
			setNotice("运行环境详细检查已完成");
		} catch (error) {
			if (requestId === environmentRequestRef.current) {
				const message = error instanceof Error ? error.message : "运行环境详细检查失败";
				setEnvironment((current) => current ? {
					...current,
					refreshing: false,
					error: message
				} : current);
				setNotice(`缓存状态仍可查看；详细检查失败：${message}`);
			}
		} finally {
			if (requestId === environmentRequestRef.current) setBusy("");
		}
	}
	async function refreshMarket() {
		if (window.location.pathname === "/") {
			window.dispatchEvent(new CustomEvent("zhangcai:desktop-market-refresh"));
			setNotice("首页正在同步行情");
			return;
		}
		setBusy("market");
		try {
			const response = await fetch(bridgeUrl("/market?scope=indices"), { cache: "no-store" });
			const body = await response.json().catch(() => ({}));
			if (!response.ok) throw new Error(resultMessage(body, `行情同步失败（${response.status}）`));
			setNotice(resultMessage(body, "主要指数已同步"));
		} catch (error) {
			setNotice(error instanceof Error ? error.message : "行情同步失败");
		} finally {
			setBusy("");
		}
	}
	async function openTdx() {
		setBusy("tdx");
		try {
			const response = await fetch(bridgeUrl("/runtime/tdx/open"), { method: "POST" });
			const body = await response.json().catch(() => ({}));
			if (!response.ok) throw new Error(resultMessage(body, `通达信启动失败（${response.status}）`));
			setNotice(resultMessage(body, "通达信启动请求已发送"));
		} catch (error) {
			setNotice(error instanceof Error ? error.message : "通达信启动失败");
		} finally {
			setBusy("");
		}
	}
	async function chooseTdxDirectory() {
		const desktop = window.zhangcaiDesktop;
		if (!desktop) {
			setNotice("当前页面不是桌面端，无法打开目录选择器");
			return;
		}
		setBusy("tdx-directory");
		try {
			const result = await desktop.chooseTdxDirectory();
			if (result.status === "cancelled") return;
			if (result.status !== "saved") {
				setNotice(result.error || "通达信目录未保存");
				return;
			}
			setNotice(`通达信目录已保存：${result.path || ""}，正在重新启动桌面桥接…`);
			await desktop.restart();
		} catch (error) {
			setNotice(error instanceof Error ? error.message : "通达信目录设置失败");
		} finally {
			setBusy("");
		}
	}
	async function openTdxDownload() {
		try {
			await window.zhangcaiDesktop?.openTdxDownload();
			setNotice("已打开通达信 Mock 下载地址");
		} catch (error) {
			setNotice(error instanceof Error ? error.message : "通达信下载地址打开失败");
		}
	}
	async function saveHarnessCredential() {
		const apiKey = credentialInput.trim();
		if (apiKey.length < 12) {
			setNotice("请输入有效的 DeepSeek API 密钥");
			return;
		}
		setBusy("credentials");
		try {
			const response = await fetch(bridgeUrl("/runtime/credentials"), {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ apiKey })
			});
			const body = await response.json().catch(() => ({}));
			if (!response.ok) throw new Error(resultMessage(body, `Harness 凭据保存失败（${response.status}）`));
			setCredentialInput("");
			setNotice("Harness 凭据已保存并生效");
			await inspectEnvironment();
		} catch (error) {
			setNotice(error instanceof Error ? error.message : "Harness 凭据保存失败");
		} finally {
			setBusy("");
		}
	}
	return /* @__PURE__ */ jsxs(Fragment$1, { children: [
		/* @__PURE__ */ jsx("div", {
			className: "desktop-runtime-spacer",
			"aria-hidden": "true"
		}),
		/* @__PURE__ */ jsxs("header", {
			className: "desktop-runtime-shell",
			"data-testid": "desktop-runtime-shell",
			children: [
				/* @__PURE__ */ jsxs("div", {
					className: "desktop-runtime-brand",
					children: [/* @__PURE__ */ jsx("span", {
						className: "desktop-runtime-mark",
						"aria-label": "掌财桌面端"
					}), /* @__PURE__ */ jsx("b", { children: "掌财桌面端" })]
				}),
				/* @__PURE__ */ jsxs("nav", {
					className: "desktop-runtime-nav",
					"aria-label": "桌面页面导航",
					children: [/* @__PURE__ */ jsxs("button", {
						type: "button",
						onClick: () => {
							window.location.href = uiUrl("/");
						},
						className: window.location.pathname === "/" ? "desktop-runtime-action is-active" : "desktop-runtime-action",
						children: [/* @__PURE__ */ jsx(House, { size: 14 }), "首页"]
					}), /* @__PURE__ */ jsxs("button", {
						type: "button",
						onClick: () => {
							window.location.href = uiUrl("/chat");
						},
						className: window.location.pathname.startsWith("/chat") ? "desktop-runtime-action is-chat-active" : "desktop-runtime-action",
						children: [/* @__PURE__ */ jsx(MessageSquare, { size: 14 }), "聊天"]
					})]
				}),
				/* @__PURE__ */ jsxs("div", {
					className: "desktop-runtime-tools",
					children: [
						/* @__PURE__ */ jsxs("button", {
							type: "button",
							onClick: refreshMarket,
							disabled: Boolean(busy),
							className: "desktop-runtime-action",
							children: [/* @__PURE__ */ jsx(RefreshCw, {
								size: 14,
								className: busy === "market" ? "desktop-runtime-spin" : ""
							}), "同步行情"]
						}),
						/* @__PURE__ */ jsxs("button", {
							type: "button",
							onClick: openTdx,
							disabled: Boolean(busy),
							className: "desktop-runtime-action desktop-runtime-tdx",
							children: [/* @__PURE__ */ jsx(Database, { size: 14 }), "通达信"]
						}),
						/* @__PURE__ */ jsxs("button", {
							type: "button",
							onClick: inspectEnvironment,
							disabled: Boolean(busy),
							className: "desktop-runtime-action",
							children: [/* @__PURE__ */ jsx(Activity, { size: 14 }), "运行环境"]
						})
					]
				}),
				/* @__PURE__ */ jsxs("div", {
					className: "desktop-runtime-status",
					title: notice,
					children: [
						/* @__PURE__ */ jsx(CircleCheck, { size: 13 }),
						/* @__PURE__ */ jsx("span", { children: notice }),
						/* @__PURE__ */ jsx("em", { children: "会话已持久化" })
					]
				})
			]
		}),
		environment && /* @__PURE__ */ jsxs("aside", {
			className: "desktop-runtime-panel",
			"aria-label": "桌面运行环境",
			children: [
				/* @__PURE__ */ jsxs("div", {
					className: "desktop-runtime-panel-head",
					children: [
						/* @__PURE__ */ jsx("b", { children: "桌面运行环境" }),
						/* @__PURE__ */ jsx("small", { children: environment.loading ? "正在读取状态…" : environment.refreshing ? "详细诊断进行中…" : environment.stale ? "显示最近缓存状态" : environment.summary ? "缓存状态" : "" }),
						/* @__PURE__ */ jsx("button", {
							type: "button",
							onClick: () => {
								environmentRequestRef.current += 1;
								setBusy("");
								setEnvironment(null);
							},
							"aria-label": "关闭运行环境",
							children: /* @__PURE__ */ jsx(X, { size: 15 })
						})
					]
				}),
				/* @__PURE__ */ jsxs("div", {
					className: "desktop-runtime-panel-grid",
					children: [
						/* @__PURE__ */ jsx("span", { children: "桥接端口" }),
						/* @__PURE__ */ jsx("b", { children: environment.bridge?.port || "动态分配" }),
						/* @__PURE__ */ jsx("span", { children: "桥接状态" }),
						/* @__PURE__ */ jsx("b", { children: environment.bridge?.status || "未知" }),
						/* @__PURE__ */ jsx("span", { children: "Harness" }),
						/* @__PURE__ */ jsx("b", { children: environment.harness?.status || "未知" }),
						/* @__PURE__ */ jsx("span", { children: "通达信" }),
						/* @__PURE__ */ jsx("b", {
							title: `${environment.tdx?.root || ""}${environment.tdx?.checkedAt ? ` · 检查于 ${environment.tdx.checkedAt}` : ""}${environment.tdx?.rootMatches === false ? " · 当前进程目录与设置目录不一致" : ""}`,
							children: environment.stale ? `缓存过期（上次：${tdxStatusLabel(environment.tdx?.lastKnownStatus || environment.tdx?.status)}）` : tdxStatusLabel(environment.tdx?.status)
						}),
						/* @__PURE__ */ jsx("span", { children: "TDX 目录" }),
						/* @__PURE__ */ jsx("b", {
							title: environment.tdx?.root,
							children: environment.tdx?.root || "未设置"
						}),
						/* @__PURE__ */ jsx("span", { children: "5 分钟线" }),
						/* @__PURE__ */ jsx("b", {
							title: environment.minuteData?.reason,
							children: minuteDataLabel(environment.minuteData)
						}),
						/* @__PURE__ */ jsx("span", { children: "行情日期" }),
						/* @__PURE__ */ jsx("b", { children: environment.daily?.date || "等待刷新" }),
						/* @__PURE__ */ jsx("span", { children: "Harness 凭据" }),
						/* @__PURE__ */ jsx("b", { children: environment.harness?.credentialsConfigured ? "已配置" : "未配置" }),
						/* @__PURE__ */ jsx("span", { children: "资源库" }),
						/* @__PURE__ */ jsx("b", {
							title: environment.resourceLibrary?.root,
							children: environment.resourceLibrary?.writable ? "可写" : "未确认"
						})
					]
				}),
				!environment.harness?.credentialsConfigured && /* @__PURE__ */ jsxs("div", {
					className: "desktop-runtime-credentials",
					children: [/* @__PURE__ */ jsx("input", {
						type: "password",
						value: credentialInput,
						onChange: (event) => setCredentialInput(event.target.value),
						placeholder: "输入 DeepSeek API 密钥",
						autoComplete: "off",
						spellCheck: false
					}), /* @__PURE__ */ jsx("button", {
						type: "button",
						onClick: () => void saveHarnessCredential(),
						disabled: busy === "credentials",
						children: busy === "credentials" ? "保存中…" : "保存并启用"
					})]
				}),
				/* @__PURE__ */ jsxs("div", {
					className: "desktop-runtime-settings",
					children: [/* @__PURE__ */ jsx("button", {
						type: "button",
						onClick: () => void chooseTdxDirectory(),
						disabled: Boolean(busy),
						children: "设置通达信目录"
					}), /* @__PURE__ */ jsx("button", {
						type: "button",
						onClick: () => void openTdxDownload(),
						disabled: Boolean(busy),
						children: "下载 Mock"
					})]
				}),
				/* @__PURE__ */ jsxs("button", {
					className: "desktop-runtime-diagnostics",
					type: "button",
					onClick: () => void refreshEnvironmentDetails(),
					disabled: Boolean(busy) || environment.refreshing,
					children: [/* @__PURE__ */ jsx(RefreshCw, {
						size: 12,
						className: environment.refreshing ? "desktop-runtime-spin" : ""
					}), environment.refreshing ? "详细检查中…" : "刷新详细检查"]
				}),
				environment.error && /* @__PURE__ */ jsx("small", {
					className: "desktop-runtime-error",
					children: environment.error
				}),
				/* @__PURE__ */ jsx("small", { children: "桌面版使用独立桥接和可写资源库，网页服务保持独立。" })
			]
		})
	] });
}
//#endregion
export { DesktopRuntimeShell as default };
