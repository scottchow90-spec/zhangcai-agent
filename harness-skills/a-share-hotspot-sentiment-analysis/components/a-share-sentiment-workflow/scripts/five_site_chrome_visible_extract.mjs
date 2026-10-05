import fs from "node:fs/promises";
import path from "node:path";

const MARKET_WIDE_RE = /(A股|a股|股市|股票|大盘|行情|指数|上证指数|深证成指|创业板指|科创50|成交额|成交量|放量|缩量|主力资金|资金流向|净流入|净流出|融资|上涨家数|下跌家数|涨跌比|涨停|跌停|市场情绪|赚钱效应|风险偏好|热点|龙头|概念|产业链|盘中|收评|复盘|盘前|盘后)/i;
const BUSINESS_SOCIETY_RE = /(商品|现货|价格|报价|涨跌|涨幅|跌幅|供给|供应|需求|库存|产量|开工率|产能|成本|利润|订单|进口|出口|期货|原料|产业链|生意社|100PPI)/i;

function norm(value) {
  return (value || "").replace(/[\u200b\u200c\u200d\ufeff]/g, "").replace(/\s+/g, " ").trim();
}

export function cleanItems(items, site = "") {
  const seen = new Set();
  const out = [];
  for (const item of items || []) {
    const title = norm(item.title);
    const text = norm(item.text);
    const href = item.href || "";
    if (!title || !text || title.length < 3) continue;
    if (/^(AI Works Beta|AI 搜索|首页|消息|登录|注册|热门基金|道琼斯指数|纳斯达克综合指数|标普500指数|热门个股吧|热门主题吧|热门概念吧|A股开户|自选股票)$/.test(title)) continue;
    if (/xueqiu\.com\/S\/\.(DJI|IXIC|INX)|project\/square|type=zhida/.test(href)) continue;
    const wanted = site === "business_society" ? BUSINESS_SOCIETY_RE : MARKET_WIDE_RE;
    if (!wanted.test(`${title} ${text}`)) continue;
    const hrefKey = href && !/^javascript/.test(href) ? href.replace(/[?#].*$/, "") : "";
    const key = `${hrefKey}|${title.replace(/\s/g, "").slice(0, 100)}|${text.replace(/\s/g, "").slice(0, 80)}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ ...item, title, text });
  }
  return out;
}

export async function extractVisible(tab, site, label) {
  return tab.playwright.evaluate(({ site, label }) => {
    const clean = (value) => (value || "").replace(/[\u200b\u200c\u200d\ufeff]/g, "").replace(/\s+/g, " ").trim();
    const wanted = site === "business_society"
      ? /(商品|现货|价格|报价|涨跌|涨幅|跌幅|供给|供应|需求|库存|产量|开工率|产能|成本|利润|订单|进口|出口|期货|原料|产业链|生意社|100PPI)/i
      : /(A股|a股|股市|股票|大盘|行情|指数|上证指数|深证成指|创业板指|科创50|成交额|成交量|放量|缩量|主力资金|资金流向|净流入|净流出|融资|上涨家数|下跌家数|涨跌比|涨停|跌停|市场情绪|赚钱效应|风险偏好|热点|龙头|概念|产业链|盘中|收评|复盘|盘前|盘后)/i;
    const selector = "article,.card-wrap,.card-feed,.timeline__item,.status-item,.ContentItem,.AnswerItem,.items-list-content,.items-list-data,.post_item,.article-list-item,.listitem,.list-item,.feed-item,.news_item,.item,li,tr,h1,h2,h3,h4,a[href]";
    const visible = (el) => {
      try {
        const style = getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
      } catch {
        return false;
      }
    };
    const out = [];
    const seen = new Set();
    for (const el of Array.from(document.querySelectorAll(selector)).filter(visible).slice(0, 3500)) {
      const text = clean(el.innerText || el.textContent || el.getAttribute("aria-label") || "");
      if (!text || text.length < 4 || text.length > 1300 || !wanted.test(text)) continue;
      if (/登录|注册|广告服务|免责声明|隐私|用户协议|app下载/.test(text) && text.length < 70) continue;
      let title = clean(el.querySelector?.("h1,h2,h3,h4,.title,.ContentItem-title,.timeline__item__title,.name,.txt,.card-title")?.innerText || "");
      if (!title) {
        const linkText = clean(el.querySelector?.("a")?.innerText || "");
        if (linkText && linkText.length <= 180) title = linkText;
      }
      if (!title) title = text.slice(0, 140);
      const a = el.matches?.("a[href]") ? el : el.querySelector?.("a[href]");
      const href = a?.href || "";
      const timeMatch = text.match(/(刚刚|\d+\s*秒前|\d+\s*分钟前|\d+\s*小时前|今天\s*\d{1,2}:\d{2}|昨天\s*\d{1,2}:\d{2}|前天\s*\d{1,2}:\d{2}|发表于\s*今天\s*\d{1,2}:\d{2}|\d{4}[年\/-]\d{1,2}[月\/-]\d{1,2}日?\s*\d{0,2}:?\d{0,2}|\d{1,2}[月\/-]\d{1,2}日?\s*\d{0,2}:?\d{0,2}|修改于\d+小时前)/);
      const metrics = Array.from(text.matchAll(/\d+(?:\.\d+)?\s*万?\s*(?:阅读|评论|转发|点赞|赞同|收藏|分享)|转赞人数超过\d+|涨停|跌停/g)).map((m) => m[0]).slice(0, 8);
      const key = `${href}|${title.slice(0, 80)}|${text.slice(0, 80)}`;
      if (seen.has(key)) continue;
      seen.add(key);
      out.push({ site, label, title, text, href, time: timeMatch ? timeMatch[0] : "", metrics, capturedUrl: location.href, pageTitle: document.title });
      if (out.length >= 220) break;
    }
    return out;
  }, { site, label }, { timeoutMs: 18000 }).catch((error) => [{ site, label, error: String(error?.message || error) }]);
}

export async function scrapeBatch({ browser, site, urls, outDir, fileName, collectedAt: collectedAtInput }) {
  const raw = [];
  const errors = [];
  const collectedAt = collectedAtInput ? new Date(collectedAtInput).toISOString() : new Date().toISOString();
  if (Number.isNaN(Date.parse(collectedAt))) {
    throw new Error(`invalid collectedAt: ${collectedAtInput}`);
  }
  await fs.mkdir(outDir, { recursive: true });
  for (const { url, label } of urls) {
    let tab;
    try {
      tab = await browser.tabs.new();
      await tab.goto(url);
      try {
        await tab.playwright.waitForLoadState({ state: "domcontentloaded", timeoutMs: 16000 });
      } catch {}
      await tab.playwright.waitForTimeout(900);
      // Native feeds such as Xueqiu publish the newest cards after the initial
      // viewport.  Scroll only within the rendered Chrome tab, then extract
      // visible DOM text; no HTTP client or hidden API is involved.
      for (let step = 0; step < 3; step += 1) {
        await tab.playwright.evaluate(() => window.scrollTo(0, Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)), { timeoutMs: 8000 }).catch(() => {});
        await tab.playwright.waitForTimeout(500);
      }
      for (const item of await extractVisible(tab, site, label)) {
        if (item.error) errors.push(item);
        else raw.push({ ...item, capturedAt: collectedAt });
      }
    } catch (error) {
      errors.push({ site, label, url, error: String(error?.message || error) });
    } finally {
      if (tab) {
        try { await tab.close(); } catch {}
      }
    }
  }
  const clean = cleanItems(raw, site);
  const targetPath = path.join(outDir, fileName || `${site}.json`);
  const payload = { site, channel: "Chrome logged-in visible pages only", collectedAt, rawCount: raw.length, cleanCount: clean.length, raw, clean, errors };
  await fs.writeFile(targetPath, JSON.stringify(payload, null, 2), "utf8");
  return { site, file: targetPath, raw: payload.rawCount, clean: payload.cleanCount, errors: payload.errors.length, sample: payload.clean.slice(0, 5).map((x) => ({ title: x.title, time: x.time, href: x.href })) };
}
