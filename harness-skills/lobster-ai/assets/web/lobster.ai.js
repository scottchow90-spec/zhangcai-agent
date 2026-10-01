"use strict";

const REFRESH_INTERVAL_MS = 60_000;
const REQUEST_TIMEOUT_MS = 12_000;

const POOL_API = "/api/pool?pool_name=";
const BREADTH_API = "/api/breadth";

let timer = null;
let isRunning = false;
let refreshPromise = null;
let xgbStockData = [];
let limitDownData = [];
let brokenBoardData = [];
let quantRiskList = [];
let quantFakeList = [];
let antiSafeList = [];
let blockList = new Set();
let dataFresh = false;
let effectiveDate = "--";
let marketBreadth = null;

const cycleStages = document.querySelectorAll(".cycle-stage");
const btnStart = document.getElementById("btn-start");
const btnRefresh = document.getElementById("btn-refresh");
const btnStock = document.getElementById("btn-stock");

function byId(id) {
  return document.getElementById(id);
}

function toNumber(value, fallback = 0) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalizeCode(value) {
  return String(value ?? "").replace(/\D/g, "").slice(0, 6);
}

function codeFromSymbol(symbol) {
  return normalizeCode(String(symbol ?? "").split(".")[0]);
}

function formatPercent(value, digits = 2) {
  return `${toNumber(value).toFixed(digits)}%`;
}

function formatTime(timestamp) {
  if (!timestamp) return "--:--";
  const date = new Date(toNumber(timestamp) * 1000);
  if (Number.isNaN(date.getTime())) return "--:--";
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  }).format(date);
}

function formatDate(timestamp) {
  if (!timestamp) return "--";
  const date = new Date(toNumber(timestamp) * 1000);
  if (Number.isNaN(date.getTime())) return "--";
  const parts = new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).formatToParts(date);
  const values = Object.fromEntries(parts.map(part => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

function todayInShanghai() {
  return formatDate(Math.floor(Date.now() / 1000));
}

function normalizePoolStock(raw, poolName) {
  const firstLimitUp = toNumber(raw.first_limit_up);
  const lastLimitUp = toNumber(raw.last_limit_up);
  const firstLimitDown = toNumber(raw.first_limit_down);
  const lastLimitDown = toNumber(raw.last_limit_down);
  return {
    code: codeFromSymbol(raw.symbol),
    name: String(raw.stock_chi_name ?? ""),
    zf: toNumber(raw.change_percent) * 100,
    price: toNumber(raw.price),
    volumeRatio: toNumber(raw.volume_bias_ratio),
    turnoverPct: toNumber(raw.turnover_ratio) * 100,
    buyLockPct: toNumber(raw.buy_lock_volume_ratio) * 100,
    sellLockPct: toNumber(raw.sell_lock_volume_ratio) * 100,
    limitUpDays: Math.max(0, Math.trunc(toNumber(raw.limit_up_days))),
    breakCount: Math.max(0, Math.trunc(toNumber(raw.break_limit_up_times))),
    firstLimitUp,
    lastLimitUp,
    lastTimestamp: Math.max(firstLimitUp, lastLimitUp, firstLimitDown, lastLimitDown),
    isNew: Boolean(raw.is_new_stock),
    plates: Array.isArray(raw.surge_reason?.related_plates)
      ? raw.surge_reason.related_plates.map(item => String(item.plate_name ?? "")).filter(Boolean)
      : [],
    reason: String(raw.surge_reason?.stock_reason ?? ""),
    poolName,
    score: 0
  };
}

function isHardExcluded(stock) {
  const name = stock.name.toUpperCase();
  return !stock.code || !stock.name || stock.isNew || name.includes("ST") || name.includes("退") || name.startsWith("N") || name.startsWith("C");
}

async function fetchJson(url) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(url, {
      cache: "no-store",
      signal: controller.signal,
      headers: { Accept: "application/json" }
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const text = await response.text();
    if (!text.trim()) throw new Error("接口返回空内容");
    return JSON.parse(text);
  } finally {
    clearTimeout(timeout);
  }
}

async function fetchPool(poolName) {
  const payload = await fetchJson(`${POOL_API}${encodeURIComponent(poolName)}&_=${Date.now()}`);
  if (payload.code !== 20000 || !Array.isArray(payload.data)) {
    throw new Error(`${poolName} 数据格式异常`);
  }
  return payload.data
    .map(item => normalizePoolStock(item, poolName))
    .filter(stock => !isHardExcluded(stock));
}

function normalizeBreadthPayload(payload) {
  const raw = payload?.data;
  const riseCount = toNumber(raw?.rise_count, Number.NaN);
  const fallCount = toNumber(raw?.fall_count, Number.NaN);
  const timestamp = toNumber(raw?.timestamp, Number.NaN);
  if (
    payload?.code !== 20000 ||
    !Number.isFinite(riseCount) || riseCount < 0 ||
    !Number.isFinite(fallCount) || fallCount < 0 ||
    riseCount + fallCount <= 0 ||
    !Number.isFinite(timestamp) || timestamp <= 0
  ) {
    throw new Error("全市场广度数据格式异常");
  }
  return {
    riseCount: Math.trunc(riseCount),
    fallCount: Math.trunc(fallCount),
    timestamp: Math.trunc(timestamp),
    effectiveDate: formatDate(timestamp),
    source: String(raw?.source ?? "xuangubao-market-indicator")
  };
}

async function fetchBreadth() {
  const payload = await fetchJson(`${BREADTH_API}?_=${Date.now()}`);
  return normalizeBreadthPayload(payload);
}

function hasMarketBreadth() {
  return Boolean(
    marketBreadth &&
    marketBreadth.effectiveDate === effectiveDate &&
    marketBreadth.effectiveDate === todayInShanghai()
  );
}

function linkToAllSoft(stockCode) {
  const code = normalizeCode(stockCode);
  if (!code) return;
  const market = code.startsWith("6") ? "sh" : /^[489]/.test(code) ? "bj" : "sz";
  const popup = window.open(`https://quote.eastmoney.com/${market}${code}.html`, "_blank", "noopener,noreferrer");
  if (popup) popup.opener = null;
}

function updateClock() {
  byId("top-time").innerText = new Date().toLocaleTimeString("zh-CN", { hour12: false });
}

function checkAuctionTime() {
  const now = new Date();
  const day = now.getDay();
  const minutes = now.getHours() * 60 + now.getMinutes();
  const stage = byId("auction-stage");

  if (day === 0 || day === 6) {
    stage.innerText = "休市日";
    stage.className = "text-slate-400 font-bold";
  } else if (minutes >= 9 * 60 + 15 && minutes < 9 * 60 + 20) {
    stage.innerText = "🔥 09:15-09:20 可撤单";
    stage.className = "text-pink-400 font-bold blink";
  } else if (minutes >= 9 * 60 + 20 && minutes < 9 * 60 + 25) {
    stage.innerText = "🔥 09:20-09:25 不可撤";
    stage.className = "text-red-400 font-bold blink";
  } else if (minutes >= 9 * 60 + 25 && minutes < 9 * 60 + 30) {
    stage.innerText = "✅ 09:25 竞价结果";
    stage.className = "text-green-400 font-bold";
  } else if (minutes >= 14 * 60 + 57 && minutes < 15 * 60) {
    stage.innerText = "🔔 14:57 收盘竞价";
    stage.className = "text-purple-400 font-bold blink";
  } else if (minutes < 9 * 60 + 15) {
    stage.innerText = "⏳ 等待 09:15 竞价";
    stage.className = "text-slate-400 font-bold";
  } else {
    stage.innerText = minutes >= 15 * 60 ? "✅ 今日交易结束" : "盘中交易时段";
    stage.className = "text-slate-400 font-bold";
  }
}

function updateHotConcepts(list) {
  const counts = new Map();
  list.forEach(stock => {
    stock.plates.forEach(plate => counts.set(plate, (counts.get(plate) ?? 0) + 1));
  });
  const concepts = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 10);
  byId("hot-concepts").innerHTML = concepts.length
    ? concepts.map(([name, count], index) =>
      `<span class="hot ${index < 3 ? "up" : ""}">${escapeHtml(name)} <b>${count}</b></span>`
    ).join("")
    : '<span class="text-slate-500 text-xs">暂无可靠题材数据</span>';
}

function detectEmotionCycle() {
  if (!isRunning || !dataFresh) {
    byId("current-cycle").innerText = dataFresh ? "未识别" : "数据非今日";
    disableCycleStages();
    return;
  }

  if (!hasMarketBreadth()) {
    byId("current-cycle").innerText = "无法判定（缺全市场广度）";
    disableCycleStages();
    return;
  }

  enableCycleStages();
  const limitUp = xgbStockData.length;
  const limitDown = limitDownData.length;
  const broken = brokenBoardData.length;
  const continuous = xgbStockData.filter(stock => stock.limitUpDays >= 2).length;
  const blockRate = limitUp + broken > 0 ? limitUp / (limitUp + broken) * 100 : 0;
  const breadthTotal = marketBreadth.riseCount + marketBreadth.fallCount;
  const riseRate = breadthTotal > 0 ? marketBreadth.riseCount / breadthTotal * 100 : 0;
  let currentStage = "萌芽期";

  if (riseRate < 30 && limitUp < 25 && limitDown > 15 && blockRate < 55) currentStage = "冰点期";
  else if (riseRate < 40 || broken > limitUp * 0.8 || blockRate < 55 || limitDown > limitUp) currentStage = "退潮期";
  else if (riseRate >= 70 && limitUp >= 80 && blockRate >= 75 && continuous >= 20) currentStage = "高潮期";
  else if (riseRate >= 60 && limitUp >= 50 && blockRate >= 65 && continuous >= 12) currentStage = "发酵期";
  else if (riseRate >= 55 && limitUp >= 35 && blockRate >= 60) currentStage = "启动期";

  cycleStages.forEach(stage => stage.classList.toggle("active", stage.dataset.stage === currentStage));
  byId("current-cycle").innerText = `${currentStage}（广度${Math.round(riseRate)}%）`;
}

function scoreStock(stock) {
  let score = 0;
  if (stock.buyLockPct >= 5) score += 25;
  else if (stock.buyLockPct >= 2) score += 20;
  else if (stock.buyLockPct >= 0.8) score += 12;

  if (stock.breakCount === 0) score += 25;
  else if (stock.breakCount === 1) score += 10;
  else if (stock.breakCount >= 3) score -= 15;

  if (stock.volumeRatio >= 0.8 && stock.volumeRatio <= 3) score += 15;
  else if (stock.volumeRatio > 3 && stock.volumeRatio <= 5) score += 8;
  if (stock.turnoverPct >= 2 && stock.turnoverPct <= 15) score += 10;
  if (stock.limitUpDays >= 2) score += 10;

  const firstMinutes = timestampMinutes(stock.firstLimitUp);
  if (firstMinutes !== null && firstMinutes <= 9 * 60 + 35) score += 15;
  else if (firstMinutes !== null && firstMinutes <= 10 * 60 + 30) score += 8;
  return Math.max(0, Math.min(100, Math.round(score)));
}

function antiQuantModel(list) {
  quantRiskList = [];
  quantFakeList = [];
  antiSafeList = [];
  blockList.clear();

  if (!dataFresh) {
    ["quant-risk", "quant-fake", "anti-safe", "quant-block"].forEach(id => byId(id).innerText = "--");
    renderAntiQuantList();
    renderQuantRiskList();
    return;
  }

  list.forEach(stock => {
    const highRisk = stock.breakCount >= 3 || (stock.buyLockPct < 0.3 && stock.volumeRatio > 2.5);
    const weakRisk = !highRisk && (stock.breakCount >= 1 || stock.buyLockPct < 0.5);
    const relativelyStable = stock.breakCount === 0 && stock.buyLockPct >= 0.8 &&
      stock.volumeRatio >= 0.3 && stock.volumeRatio <= 5;
    stock.score = scoreStock(stock);

    if (highRisk) {
      quantRiskList.push(stock);
      blockList.add(stock.code);
    } else if (weakRisk) {
      quantFakeList.push(stock);
    }
    if (relativelyStable) antiSafeList.push(stock);
  });

  antiSafeList.sort((a, b) => b.score - a.score);
  quantRiskList.sort((a, b) => b.breakCount - a.breakCount || a.buyLockPct - b.buyLockPct);
  byId("quant-risk").innerText = `${quantRiskList.length} 只`;
  byId("quant-fake").innerText = `${quantFakeList.length} 只`;
  byId("anti-safe").innerText = `${antiSafeList.length} 只`;
  byId("quant-block").innerText = `${blockList.size} 只`;
  renderAntiQuantList();
  renderQuantRiskList();
}

function renderAntiQuantList() {
  const element = byId("antiQuantList");
  if (!dataFresh) {
    element.innerHTML = '<div class="text-center p-2 text-yellow-400">数据非今日，暂停规则筛选</div>';
    return;
  }
  const html = antiSafeList.slice(0, 12).map(stock => `
    <div class="grid-row text-[11px]" data-code="${stock.code}">
      <div>${stock.code}</div><div>${escapeHtml(stock.name)}</div><div class="up">${formatPercent(stock.zf)}</div>
      <div><span class="quant-tag quant-safe-tag">相对稳封</span></div>
      <div>${formatPercent(stock.buyLockPct)}</div><div>${stock.limitUpDays}板</div>
      <div>${stock.volumeRatio.toFixed(2)}</div><div>规则观察</div>
    </div>`).join("");
  element.innerHTML = html || '<div class="text-center p-2 text-slate-500">暂无符合规则的稳封标的</div>';
  bindStockLinks(element);
}

function renderQuantRiskList() {
  const element = byId("quantRiskList");
  if (!dataFresh) {
    element.innerHTML = '<div class="text-center p-1 text-yellow-400">数据非今日，暂停风险标签</div>';
    return;
  }
  const html = quantRiskList.slice(0, 10).map(stock => {
    const label = stock.breakCount >= 3 ? `${stock.breakCount}次开板` : "弱封单";
    return `<div class="p-1.5 border border-red-500 rounded flex justify-between items-center" data-code="${stock.code}">
      <span>${stock.code} ${escapeHtml(stock.name)}</span><span class="quant-tag quant-danger">${label}</span></div>`;
  }).join("");
  element.innerHTML = html || '<div class="text-center p-1 text-slate-500">暂无高风险规则信号</div>';
  bindStockLinks(element);
}

function timestampMinutes(timestamp) {
  if (!timestamp) return null;
  const date = new Date(timestamp * 1000);
  if (Number.isNaN(date.getTime())) return null;
  const time = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Shanghai",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  }).format(date);
  const [hour, minute] = time.split(":").map(Number);
  return hour * 60 + minute;
}

function filterBestAuctionStocks(list) {
  if (!dataFresh) return [];
  return list
    .filter(stock => {
      const minutes = timestampMinutes(stock.firstLimitUp);
      return minutes === 9 * 60 + 25 && stock.breakCount === 0 && stock.buyLockPct >= 0.5;
    })
    .sort((a, b) => b.buyLockPct - a.buyLockPct)
    .slice(0, 12);
}

function filterCloseAuctionStocks(list) {
  if (!dataFresh) return [];
  const now = new Date();
  const currentMinutes = now.getHours() * 60 + now.getMinutes();
  if (currentMinutes < 14 * 60 + 57) return [];
  return list
    .filter(stock => {
      const minutes = timestampMinutes(stock.lastLimitUp || stock.firstLimitUp);
      return minutes !== null && minutes >= 14 * 60 + 57;
    })
    .sort((a, b) => b.lastLimitUp - a.lastLimitUp)
    .slice(0, 12);
}

function filterYZBStocks(list) {
  if (!dataFresh) return [];
  return list
    .filter(stock => timestampMinutes(stock.firstLimitUp) === 9 * 60 + 25 && stock.breakCount === 0)
    .sort((a, b) => b.buyLockPct - a.buyLockPct)
    .slice(0, 10);
}

function renderBestAuctionList(list) {
  byId("good-count").innerText = dataFresh ? String(list.length) : "--";
  const element = byId("auction-best-list");
  if (!dataFresh) {
    element.innerHTML = '<div class="col-span-3 text-center text-yellow-400">数据非今日，暂停规则筛选</div>';
    return;
  }
  const html = list.map(stock => {
    const color = stock.buyLockPct >= 3
      ? "border-green-500 bg-green-900/20"
      : stock.buyLockPct < 1
        ? "border-orange-500 bg-orange-900/20"
        : "border-yellow-500 bg-yellow-900/20";
    return `<div class="p-2 border rounded ${color} text-center" data-code="${stock.code}">
      <div>${stock.code} ${escapeHtml(stock.name)}</div><div class="up">封单比 ${formatPercent(stock.buyLockPct)}</div></div>`;
  }).join("");
  element.innerHTML = html || '<div class="col-span-3 text-center text-slate-500">暂无符合规则的竞价标的</div>';
  bindStockLinks(element);
}

function renderCloseAuctionList(list) {
  const element = byId("close-auction-list");
  if (!dataFresh) {
    element.innerHTML = '<div class="col-span-3 text-center text-yellow-400">数据非今日</div>';
    return;
  }
  const now = new Date();
  if (now.getHours() * 60 + now.getMinutes() < 14 * 60 + 57) {
    element.innerHTML = '<div class="col-span-3 text-center text-slate-500">14:57 后生成</div>';
    return;
  }
  const html = list.map(stock => `<div class="p-2 border rounded border-purple-500 bg-purple-900/20 text-center" data-code="${stock.code}">
    <div>${stock.code} ${escapeHtml(stock.name)}</div><div class="up">${formatTime(stock.lastLimitUp)}</div></div>`).join("");
  element.innerHTML = html || '<div class="col-span-3 text-center text-slate-500">暂无收盘竞价封板标的</div>';
  bindStockLinks(element);
}

function renderYZBBestListHeader(list) {
  const element = byId("yzbBestList-header");
  if (!dataFresh) {
    element.innerHTML = '<div class="text-center p-2 text-yellow-400">数据非今日</div>';
    return;
  }
  const html = list.map(stock => `<div class="p-1.5 border border-purple-500 rounded flex justify-between items-center" data-code="${stock.code}">
    <span class="status-yzb">${stock.code} ${escapeHtml(stock.name)}</span><span class="up">封单比 ${formatPercent(stock.buyLockPct)}</span></div>`).join("");
  element.innerHTML = html || '<div class="text-center p-2 text-slate-500">暂无一字板</div>';
  bindStockLinks(element);
}

function bindStockLinks(root) {
  root.querySelectorAll("[data-code]").forEach(element => {
    element.style.cursor = "pointer";
    element.onclick = () => linkToAllSoft(element.dataset.code);
  });
}

document.querySelectorAll(".tab-btn").forEach(button => {
  button.onclick = () => {
    document.querySelectorAll(".tab-btn").forEach(item => {
      item.classList.remove("active", "bg-pink-900/60");
      item.classList.add("bg-slate-700");
    });
    button.classList.add("active", "bg-pink-900/60");
    button.classList.remove("bg-slate-700");
    const target = button.dataset.target;
    document.querySelectorAll(".tab-content").forEach(content => content.classList.add("hidden"));
    byId(target).classList.remove("hidden");
    renderActiveTab(target);
  };
});

function renderActiveTab(target = document.querySelector(".tab-btn.active")?.dataset.target ?? "time-view") {
  if (target === "time-view") renderTimeView();
  if (target === "plate-view") renderPlateView();
  if (target === "height-view") renderHeightView();
  if (target === "auction-view") renderAuctionView();
}

function renderTimeView() {
  const element = byId("time-view");
  if (!xgbStockData.length) {
    element.innerHTML = '<div class="text-center">暂无数据</div>';
    return;
  }
  const sorted = [...xgbStockData].filter(stock => stock.firstLimitUp).sort((a, b) => a.firstLimitUp - b.firstLimitUp);
  element.innerHTML = sorted.map(stock => `<div class="height-item rise" data-code="${stock.code}">
    <span class="${getCodeClass(stock.code)}">${escapeHtml(stock.name)}</span>
    <span class="text-slate-400">${formatTime(stock.firstLimitUp)}</span>
    <span class="up">${formatPercent(stock.zf)}</span></div>`).join("") || '<div class="text-center">暂无涨停时间</div>';
  bindStockLinks(element);
}

function renderPlateView() {
  const element = byId("plate-view");
  if (!xgbStockData.length) {
    element.innerHTML = '<div class="text-center">暂无数据</div>';
    return;
  }
  const groups = new Map();
  xgbStockData.forEach(stock => {
    stock.plates.forEach(plate => {
      if (!groups.has(plate)) groups.set(plate, []);
      groups.get(plate).push(stock);
    });
  });
  element.innerHTML = [...groups.entries()].sort((a, b) => b[1].length - a[1].length).map(([name, stocks]) => `
    <div class="mb-1"><div class="text-pink-400 font-bold">📌 ${escapeHtml(name)} (${stocks.length})</div>
      ${stocks.map(stock => `<div class="height-item" data-code="${stock.code}">
        <span class="${getCodeClass(stock.code)}">${escapeHtml(stock.name)}</span>
        <span class="text-slate-400">${formatTime(stock.firstLimitUp)}</span>
        <span class="up">${formatPercent(stock.zf)}</span></div>`).join("")}
    </div>`).join("") || '<div class="text-center">暂无板块数据</div>';
  bindStockLinks(element);
}

function renderHeightView() {
  const element = byId("height-view");
  if (!xgbStockData.length) {
    element.innerHTML = '<div class="text-center">暂无数据</div>';
    return;
  }
  const groups = new Map([["5板+", []], ["4板", []], ["3板", []], ["2板", []], ["1板", []]]);
  xgbStockData.forEach(stock => {
    const level = stock.limitUpDays >= 5 ? "5板+" : `${Math.max(1, stock.limitUpDays)}板`;
    groups.get(level)?.push(stock);
  });
  element.innerHTML = [...groups.entries()].filter(([, stocks]) => stocks.length).map(([level, stocks]) => `
    <div class="mb-1"><div class="text-yellow-400 font-bold">🔥 ${level} (${stocks.length})</div>
      ${stocks.map(stock => `<div class="height-item" data-code="${stock.code}">
        <span class="${getCodeClass(stock.code)}">${escapeHtml(stock.name)}</span>
        <span class="text-slate-400">${formatTime(stock.firstLimitUp)}</span>
        <span class="up">${formatPercent(stock.zf)}</span></div>`).join("")}
    </div>`).join("") || '<div class="text-center">暂无高度数据</div>';
  bindStockLinks(element);
}

function renderAuctionView() {
  const element = byId("auction-view");
  if (!xgbStockData.length) {
    element.innerHTML = '<div class="text-center">暂无数据</div>';
    return;
  }
  const sorted = [...xgbStockData].sort((a, b) => b.buyLockPct - a.buyLockPct);
  element.innerHTML = sorted.map(stock => {
    const icon = timestampMinutes(stock.firstLimitUp) === 9 * 60 + 25 && stock.breakCount === 0 ? "🟣" :
      stock.breakCount === 0 ? "🟢" : stock.breakCount <= 2 ? "🟡" : "🟠";
    return `<div class="height-item" data-code="${stock.code}">
      <span>${icon} ${escapeHtml(stock.name)}</span>
      <span class="text-slate-400">封单比 ${formatPercent(stock.buyLockPct)}</span>
      <span class="up">${formatTime(stock.firstLimitUp)}</span></div>`;
  }).join("");
  bindStockLinks(element);
}

function renderBest() {
  const element = byId("bestList");
  if (!dataFresh) {
    element.innerHTML = '<div class="text-center p-2 text-yellow-400">数据非今日，暂停候选评分</div>';
    return;
  }
  const list = xgbStockData
    .filter(stock => !blockList.has(stock.code))
    .map(stock => ({ ...stock, score: scoreStock(stock) }))
    .sort((a, b) => b.score - a.score || b.buyLockPct - a.buyLockPct)
    .slice(0, 12);

  element.innerHTML = list.map(stock => {
    const strength = stock.breakCount === 0 && stock.buyLockPct >= 1 ? "稳封" : stock.breakCount >= 2 ? "反复开板" : "已回封";
    const rowClass = stock.score >= 80 ? "grid-row super" : stock.score >= 65 ? "grid-row hot" : "grid-row";
    return `<div class="${rowClass}" data-code="${stock.code}">
      <div>${stock.code}</div><div>${escapeHtml(stock.name)}</div><div class="up">${formatPercent(stock.zf)}</div>
      <div>${formatPercent(stock.buyLockPct)}</div><div>${formatTime(stock.firstLimitUp)}</div>
      <div>${stock.limitUpDays}板</div><div>${strength}</div><div>${stock.score}分</div></div>`;
  }).join("") || '<div class="text-center p-2 text-slate-500">暂无符合条件的候选</div>';
  bindStockLinks(element);
}

function getCodeClass(code) {
  if (code.startsWith("30")) return "gem";
  if (code.startsWith("68")) return "kechuang";
  if (/^[489]/.test(code)) return "beijiao";
  return "";
}

function enableCycleStages() {
  if (!hasMarketBreadth()) {
    disableCycleStages();
    return;
  }
  cycleStages.forEach(stage => stage.classList.remove("disabled"));
}

function disableCycleStages() {
  cycleStages.forEach(stage => {
    stage.classList.remove("active");
    stage.classList.add("disabled");
  });
}

function bindCycleClick() {
  cycleStages.forEach(item => {
    item.onclick = () => {
      if (!isRunning || !hasMarketBreadth()) return;
      cycleStages.forEach(stage => stage.classList.remove("active"));
      item.classList.add("active");
      byId("current-cycle").innerText = `${item.dataset.stage}（人工）`;
    };
  });
}

function renderPool(id, list, color) {
  const element = byId(id);
  const className = color === "green"
    ? "border-green-500 bg-green-900/30"
    : "border-yellow-500 bg-yellow-900/30";
  element.innerHTML = list.slice(0, 60).map(stock => `<div class="p-2 border rounded ${className} text-center" data-code="${stock.code}">
    <div>${stock.code} ${escapeHtml(stock.name)}</div><div class="up">${formatPercent(stock.zf)} · ${stock.limitUpDays}板</div></div>`).join("") ||
    '<div class="text-center text-slate-500">暂无数据</div>';
  bindStockLinks(element);
}

function updateSummary() {
  const limitUp = xgbStockData.length;
  const limitDown = limitDownData.length;
  const broken = brokenBoardData.length;
  const continuous = xgbStockData.filter(stock => stock.limitUpDays >= 2).length;
  const firstBoards = xgbStockData.filter(stock => stock.limitUpDays <= 1).length;
  const blockRate = limitUp + broken > 0 ? Math.round(limitUp / (limitUp + broken) * 100) : 0;
  const continuousRate = limitUp > 0 ? Math.round(continuous / limitUp * 100) : 0;

  byId("up-count").innerText = hasMarketBreadth() ? String(marketBreadth.riseCount) : "--";
  byId("dn-count").innerText = hasMarketBreadth() ? String(marketBreadth.fallCount) : "--";
  byId("limit-up-total").innerText = String(limitUp);
  byId("limit-dn-total").innerText = String(limitDown);
  byId("block-rate").innerText = `${blockRate}%`;
  byId("yes-up").innerText = `${continuousRate}%`;
  byId("yes-cont").innerText = String(firstBoards);
  byId("big-loss").innerText = String(broken);
  byId("big-profit").innerText = String(continuous);
  byId("limit-up-count").innerText = String(limitUp);
  byId("limit-cont-count").innerText = String(continuous);
  byId("limit-fail-count").innerText = String(broken);
}

function calculateEffectiveDate(lists) {
  const timestamps = lists.flat().map(stock => stock.lastTimestamp).filter(Boolean);
  return formatDate(timestamps.length ? Math.max(...timestamps) : 0);
}

function setDataQuality(message, state = "degraded") {
  const element = byId("data-quality");
  element.innerText = message;
  element.classList.toggle("data-degraded", state === "degraded");
  element.classList.toggle("data-error", state === "error");
  element.classList.toggle("text-green-400", state === "ok");
}

async function refreshAll() {
  if (!isRunning) return;
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    btnRefresh.disabled = true;
    btnRefresh.classList.add("opacity-60");
    byId("sys-status").innerText = "⏳ 数据同步中";
    checkAuctionTime();

    const [upResult, downResult, brokenResult, breadthResult] = await Promise.allSettled([
      fetchPool("limit_up"),
      fetchPool("limit_down"),
      fetchPool("limit_up_broken"),
      fetchBreadth()
    ]);

    if (upResult.status !== "fulfilled") {
      throw new Error(`涨停池不可用：${upResult.reason?.message ?? "未知错误"}`);
    }

    xgbStockData = upResult.value;
    limitDownData = downResult.status === "fulfilled" ? downResult.value : [];
    brokenBoardData = brokenResult.status === "fulfilled" ? brokenResult.value : [];
    marketBreadth = breadthResult.status === "fulfilled" ? breadthResult.value : null;
    if (!isRunning) return;

    effectiveDate = calculateEffectiveDate([xgbStockData, limitDownData, brokenBoardData]);
    dataFresh = effectiveDate !== "--" && effectiveDate === todayInShanghai();
    byId("data-date").innerText = effectiveDate;
    byId("update-time").innerText = new Date().toLocaleTimeString("zh-CN", { hour12: false });

    byId("current-source").innerText = "本机同源代理｜选股宝核心池 + 全市场广度";

    updateSummary();
    updateHotConcepts(xgbStockData);
    antiQuantModel(xgbStockData);
    detectEmotionCycle();
    renderActiveTab();
    renderBest();
    renderBestAuctionList(filterBestAuctionStocks(xgbStockData));
    renderCloseAuctionList(filterCloseAuctionStocks(xgbStockData));
    renderYZBBestListHeader(filterYZBStocks(xgbStockData));
    renderPool("limit-up-pool", xgbStockData, "green");
    renderPool("limit-cont-pool", xgbStockData.filter(stock => stock.limitUpDays >= 2), "yellow");

    if (!dataFresh) {
      byId("sys-status").innerText = `⚠️ 最近交易日 ${effectiveDate}`;
      setDataQuality("非今日数据，筛选已暂停", "degraded");
    } else if (downResult.status !== "fulfilled" || brokenResult.status !== "fulfilled" || !hasMarketBreadth()) {
      byId("sys-status").innerText = "⚠️ 核心数据正常 · 部分降级";
      setDataQuality(
        !hasMarketBreadth()
          ? "净口径核心池正常 · 全市场广度临时不可用"
          : "净口径核心池正常 · 部分来源不可用",
        "degraded"
      );
    } else {
      byId("sys-status").innerText = "✅ 数据同步完成";
      setDataQuality("今日净口径核心池与全市场广度完整", "ok");
    }
  })().catch(error => {
    console.error("LOBSTER AI 刷新失败", error);
    byId("sys-status").innerText = xgbStockData.length ? "⚠️ 更新失败，保留上次数据" : "❌ 核心数据获取失败";
    setDataQuality(error.message || "接口不可用", "error");
  }).finally(() => {
    btnRefresh.disabled = false;
    btnRefresh.classList.remove("opacity-60");
    refreshPromise = null;
  });

  return refreshPromise;
}

function toggleMonitor() {
  isRunning = !isRunning;
  btnStart.classList.toggle("active", isRunning);

  if (isRunning) {
    btnStart.innerHTML = '<i class="fa fa-stop mr-1"></i>✅ 运行中';
    byId("sys-status").innerText = "🚀 已启动";
    byId("anti-quant-status").innerText = "✅ 已启动";
    enableCycleStages();
    clearInterval(timer);
    timer = setInterval(() => refreshAll(), REFRESH_INTERVAL_MS);
    refreshAll();
  } else {
    btnStart.innerHTML = '<i class="fa fa-play mr-1"></i>启动监控';
    clearInterval(timer);
    timer = null;
    byId("sys-status").innerText = "⏸ 已停止";
    byId("anti-quant-status").innerText = "⏸ 已停止";
    disableCycleStages();
  }
}

function manualRefresh() {
  if (!isRunning) {
    toggleMonitor();
    return;
  }
  refreshAll();
}

function showStockSelection() {
  if (!isRunning) {
    byId("sys-status").innerText = "请先启动监控";
    return;
  }
  renderBest();
  byId("bestList").scrollIntoView({ behavior: "smooth", block: "center" });
}

btnStart.onclick = toggleMonitor;
btnRefresh.onclick = manualRefresh;
btnStock.onclick = showStockSelection;

bindCycleClick();
disableCycleStages();
checkAuctionTime();
updateClock();
setInterval(updateClock, 1000);
setInterval(checkAuctionTime, 30_000);
window.addEventListener("beforeunload", () => clearInterval(timer));

window.LobsterApp = {
  refresh: () => refreshAll(),
  getStatus: () => ({
    isRunning,
    dataFresh,
    effectiveDate,
    limitUp: xgbStockData.length,
    limitDown: limitDownData.length,
    broken: brokenBoardData.length,
    breadthAvailable: hasMarketBreadth(),
    marketBreadth
  })
};
