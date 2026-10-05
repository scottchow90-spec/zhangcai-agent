(() => {
  "use strict";

  const API = "/api/stock-results";
  const EVENTS_API = "/api/stock-results/events";
  const FALLBACK_REFRESH_MS = 60 * 1000;
  const labels = {
    available: "有入选",
    observation: "仅观察",
    empty: "空候选",
    blocked: "运行阻断",
    missing: "未落盘",
    diagnostic: "仅诊断",
    wrong_target: "目标不符",
    error: "读取错误"
  };
  const tierLabels = { selected: "严格入选", watch: "观察项", theme: "主题结果" };
  const freshnessLabels = { latest: "最新", stale: "历史", undated: "日期未识别", future: "未来日期" };

  const state = {
    payload: null,
    selectedSkill: null,
    search: "",
    sourceState: "all",
    freshness: "all",
    loading: false,
    pendingLoad: false,
    realtimeConnected: false,
    eventSource: null
  };

  const $ = (id) => document.getElementById(id);
  const escapeHtml = (value) => String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

  function formatDate(value) {
    const text = String(value || "").replace(/\D/g, "").slice(0, 8);
    return text.length === 8 ? `${text.slice(0, 4)}-${text.slice(4, 6)}-${text.slice(6, 8)}` : "--";
  }

  function formatTime(value) {
    if (!value) return "--";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString("zh-CN", { hour12: false });
  }

  function statusMatches(source) {
    if (state.sourceState === "all") return true;
    if (state.sourceState === "business") return ["available", "observation", "empty"].includes(source.state);
    if (state.sourceState === "problem") return ["blocked", "missing", "diagnostic", "wrong_target", "error"].includes(source.state);
    return source.state === state.sourceState;
  }

  function sourceMatches(source) {
    if (!statusMatches(source)) return false;
    if (state.freshness !== "all" && source.freshness !== state.freshness) return false;
    const needle = state.search.trim().toLowerCase();
    if (!needle) return true;
    const own = [source.name, source.skill, source.note, source.source_file].join(" ").toLowerCase();
    if (own.includes(needle)) return true;
    return state.payload.candidates.some((row) => row.skill === source.skill && [row.symbol, row.name, row.strategy, row.reason].join(" ").toLowerCase().includes(needle));
  }

  function candidateMatches(row, visibleSkills) {
    if (!visibleSkills.has(row.skill)) return false;
    if (state.selectedSkill && row.skill !== state.selectedSkill) return false;
    const needle = state.search.trim().toLowerCase();
    if (!needle) return true;
    return [row.skill_name, row.skill, row.symbol, row.name, row.strategy, row.reason].join(" ").toLowerCase().includes(needle);
  }

  function renderStats() {
    const summary = state.payload.summary;
    $("stat-skills").textContent = summary.audited_skill_count;
    $("stat-business").textContent = summary.business_result_skill_count;
    $("stat-selected").textContent = summary.selected_candidate_count;
    $("stat-problems").textContent = summary.problem_skill_count;
    $("stat-observation-note").textContent = `观察项 ${summary.watch_candidate_count} · 主题 ${summary.theme_result_count}`;
    $("stat-date-note").textContent = `最新交易日 ${formatDate(state.payload.latest_trade_date)}`;
    $("risk-text").textContent = state.payload.risk_notice;
    $("updated-at").textContent = `动态读取 ${formatTime(state.payload.generated_at)} · 指纹 ${state.payload.data_fingerprint || "--"}`;
    $("source-fingerprint").textContent = `动态指纹 ${state.payload.data_fingerprint || "--"}`;
  }

  function cardMarkup(source) {
    const previews = source.preview.map((item) => `<span class="chip">${escapeHtml(item.name)}${item.symbol ? ` · ${escapeHtml(item.symbol)}` : ""}</span>`).join("");
    const freshness = freshnessLabels[source.freshness] || source.freshness;
    const active = state.selectedSkill === source.skill ? " active" : "";
    const buttonText = source.result_count ? "查看结果明细" : "查看状态说明";
    return `<article class="skill-card${active}" data-skill-card="${escapeHtml(source.skill)}">
      <div class="skill-top">
        <div><h3 class="skill-name">${escapeHtml(source.name)}</h3><div class="skill-id">${escapeHtml(source.skill)}</div></div>
        <span class="badge state-${escapeHtml(source.state)}">${escapeHtml(labels[source.state] || source.state)}</span>
      </div>
      <div class="meta-grid">
        <div class="meta"><span>严格入选</span><strong>${source.selected_count}</strong></div>
        <div class="meta"><span>观察／主题</span><strong>${source.watch_count + source.theme_count}</strong></div>
        <div class="meta"><span>交易日</span><strong>${formatDate(source.trade_date)}</strong></div>
      </div>
      <p class="skill-note">${escapeHtml(source.note)}</p>
      <div class="source-line">${escapeHtml(freshness)} · ${escapeHtml(source.source_file || "无结果文件")}</div>
      <div class="preview">${previews}</div>
      <button class="card-action" type="button" data-skill="${escapeHtml(source.skill)}">${buttonText}</button>
    </article>`;
  }

  function renderSkills() {
    const sources = state.payload.sources.filter(sourceMatches);
    $("skill-grid").innerHTML = sources.map(cardMarkup).join("");
    $("skill-grid").classList.toggle("hidden", sources.length === 0);
    $("skill-empty").classList.toggle("hidden", sources.length !== 0);
    $("skill-count").textContent = `显示 ${sources.length} / ${state.payload.sources.length}`;
    $("skill-grid").querySelectorAll("button[data-skill]").forEach((button) => {
      button.addEventListener("click", () => {
        const skill = button.dataset.skill;
        state.selectedSkill = state.selectedSkill === skill ? null : skill;
        render();
        $("results-section").scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
  }

  function tierBadge(tier) {
    const status = tier === "selected" ? "available" : "observation";
    return `<span class="badge state-${status}">${escapeHtml(tierLabels[tier] || tier)}</span>`;
  }

  function selectedRowMarkup(row, index) {
    const score = row.score === null || row.score === undefined || row.score === "" ? "--" : row.score;
    const isLatest = String(row.signal_date || "").replace(/\D/g, "").slice(0, 8) === String(state.payload.latest_trade_date || "").replace(/\D/g, "").slice(0, 8);
    const freshness = isLatest ? '<span class="latest-flag">最新交易日</span>' : '<span class="history-flag">历史结果</span>';
    return `<tr data-selected-result="${escapeHtml(row.id)}">
      <td class="hero-rank">${index + 1}</td>
      <td><div class="hero-stock"><span class="symbol">${escapeHtml(row.symbol || "--")}</span><strong>${escapeHtml(row.name)}</strong></div></td>
      <td><div class="row-name">${escapeHtml(row.skill_name)}</div><div class="row-sub">${escapeHtml(row.skill)}</div></td>
      <td>${escapeHtml(row.strategy || "--")}</td>
      <td>${escapeHtml(score)}</td>
      <td>${formatDate(row.signal_date)}<div>${freshness}</div></td>
    </tr>`;
  }

  function renderSelected() {
    const visibleSources = state.payload.sources.filter(sourceMatches);
    const visibleSkills = new Set(visibleSources.map((source) => source.skill));
    const rows = state.payload.candidates
      .filter((row) => row.tier === "selected" && candidateMatches(row, visibleSkills))
      .slice()
      .sort((left, right) => {
        const dateOrder = String(right.signal_date || "").localeCompare(String(left.signal_date || ""));
        if (dateOrder !== 0) return dateOrder;
        const scoreOrder = Number(right.score || 0) - Number(left.score || 0);
        if (scoreOrder !== 0) return scoreOrder;
        return Number(left.rank || 0) - Number(right.rank || 0);
      });
    $("selected-body").innerHTML = rows.map(selectedRowMarkup).join("");
    $("selected-body").classList.toggle("hidden", rows.length === 0);
    $("selected-empty").classList.toggle("hidden", rows.length !== 0);
    $("selected-count").firstChild.textContent = `严格入选 ${rows.length} 条`;
  }

  function rowMarkup(row) {
    const score = row.score === null || row.score === undefined || row.score === "" ? "--" : row.score;
    const symbol = row.symbol || (row.entity_type === "theme" ? "主题" : "--");
    return `<tr>
      <td><div class="row-name">${escapeHtml(row.skill_name)}</div><div class="row-sub">${escapeHtml(row.skill)}</div></td>
      <td>${tierBadge(row.tier)}</td>
      <td class="symbol">${escapeHtml(symbol)}</td>
      <td><div class="row-name">${escapeHtml(row.name)}</div><div class="row-sub">${escapeHtml(row.entity_type === "theme" ? "主题／板块" : "A股结果")}</div></td>
      <td>${escapeHtml(row.strategy || "--")}</td>
      <td>${escapeHtml(score)}</td>
      <td>${formatDate(row.signal_date)}</td>
      <td class="reason">${escapeHtml(row.reason)}</td>
    </tr>`;
  }

  function renderResults() {
    const visibleSources = state.payload.sources.filter(sourceMatches);
    const visibleSkills = new Set(visibleSources.map((source) => source.skill));
    const rows = state.payload.candidates.filter((row) => candidateMatches(row, visibleSkills));
    $("result-body").innerHTML = rows.map(rowMarkup).join("");
    $("result-body").classList.toggle("hidden", rows.length === 0);
    $("result-empty").classList.toggle("hidden", rows.length !== 0);
    $("result-count").textContent = `显示 ${rows.length} 条`;
    if (state.selectedSkill) {
      const source = state.payload.sources.find((item) => item.skill === state.selectedSkill);
      $("result-scope").textContent = source ? `当前技能：${source.name}；再次点击卡片可取消单技能筛选。` : "严格入选、观察项与主题结果分栏标识。";
    } else {
      $("result-scope").textContent = "严格入选、观察项与主题结果分栏标识。";
    }
  }

  function render() {
    if (!state.payload) return;
    renderStats();
    renderSelected();
    renderSkills();
    renderResults();
  }

  async function load(trigger = "manual") {
    if (state.loading) {
      state.pendingLoad = true;
      return;
    }
    state.loading = true;
    $("live-dot").className = "dot";
    $("live-text").textContent = "正在动态扫描";
    try {
      const response = await fetch(`${API}?_=${Date.now()}`, { cache: "no-store", headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      if (payload.schema !== "LOBSTER-STOCK-DASHBOARD-V1" || payload.status !== "PASS") throw new Error("结果协议不匹配");
      state.payload = payload;
      if (state.selectedSkill && !payload.sources.some((source) => source.skill === state.selectedSkill)) state.selectedSkill = null;
      render();
      $("live-dot").className = "dot ok";
      $("live-text").textContent = state.realtimeConnected
        ? (trigger === "push" ? "实时推送 · 刚刚更新" : "实时推送已连接 · 文件变化即更新")
        : "实时连接中 · 60秒兜底";
    } catch (error) {
      $("live-dot").className = "dot error";
      $("live-text").textContent = `读取失败：${error.message}`;
      $("skill-grid").innerHTML = "";
      $("selected-body").innerHTML = "";
      $("selected-empty").textContent = `无法读取本机结果接口：${error.message}`;
      $("selected-empty").classList.remove("hidden");
      $("selected-count").textContent = "读取失败";
      $("skill-empty").textContent = `无法读取本机结果接口：${error.message}`;
      $("skill-empty").classList.remove("hidden");
    } finally {
      state.loading = false;
      if (state.pendingLoad) {
        state.pendingLoad = false;
        window.setTimeout(() => load("queued"), 0);
      }
    }
  }

  function connectRealtime() {
    if (!("EventSource" in window)) {
      $("live-text").textContent = "浏览器不支持实时推送 · 60秒兜底";
      return;
    }
    if (state.eventSource) state.eventSource.close();
    const source = new EventSource(EVENTS_API);
    state.eventSource = source;
    source.addEventListener("ready", () => {
      state.realtimeConnected = true;
      $("live-dot").className = "dot ok";
      $("live-text").textContent = "实时推送已连接 · 文件变化即更新";
    });
    source.addEventListener("results-changed", () => {
      state.realtimeConnected = true;
      load("push");
    });
    source.onerror = () => {
      state.realtimeConnected = false;
      $("live-dot").className = "dot";
      $("live-text").textContent = "实时连接重连中 · 60秒兜底";
    };
  }

  $("search").addEventListener("input", (event) => { state.search = event.target.value; render(); });
  $("state-filter").addEventListener("change", (event) => { state.sourceState = event.target.value; state.selectedSkill = null; render(); });
  $("freshness-filter").addEventListener("change", (event) => { state.freshness = event.target.value; state.selectedSkill = null; render(); });
  $("refresh").addEventListener("click", () => load("manual"));
  $("refresh-top").addEventListener("click", () => load("manual"));
  connectRealtime();
  load("initial");
  window.setInterval(() => load("fallback"), FALLBACK_REFRESH_MS);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) load("visibility"); });
  window.addEventListener("beforeunload", () => { if (state.eventSource) state.eventSource.close(); });
})();
