'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import catalog from '@/config/skill14-catalog.json';
import { bridgeHostLabel, bridgeUrl } from '@/lib/bridge-url';
import styles from './skill14.module.css';

type Asset = { status?: string; reason?: string; file?: string; file_count?: number; current_trade_date_symbols?: number };
type StatusResponse = { data_root?: string; assets?: Record<string, Asset>; error?: string };
type Preflight = { status: string; report_id?: string; skill?: { name?: string }; required_missing?: string[]; optional_missing?: string[]; degrade_policy?: string; execution_note?: string; error?: string };
type Report = { report_id?: string; skill_name?: string; status?: string; created_at?: string };

const assetNames = Object.fromEntries(catalog.dataAssets.map((asset) => [asset.id, asset.name]));
const statusText: Record<string, string> = { available: '可用', missing: '待归档', degraded: '降级', BLOCKED: '已阻断', DEGRADED: '降级预检', READY_FOR_VALIDATED_RUN: '可验证运行' };

function stateClass(value?: string) {
  const normalized = String(value || 'missing').toLowerCase();
  if (normalized.includes('available') || normalized.includes('ready')) return styles.available;
  if (normalized.includes('degrad')) return styles.degraded;
  return styles.missing;
}

export default function Skill14Home() {
  const [status, setStatus] = useState<StatusResponse>({});
  const [reports, setReports] = useState<Report[]>([]);
  const [busy, setBusy] = useState('');
  const [message, setMessage] = useState('正在连接本地桥接服务…');
  const [selected, setSelected] = useState<Preflight | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [statusResponse, reportResponse] = await Promise.all([
        fetch(bridgeUrl('/skill14/status'), { cache: 'no-store' }),
        fetch(bridgeUrl('/skill14/reports'), { cache: 'no-store' }),
      ]);
      const statusBody = await statusResponse.json();
      const reportBody = await reportResponse.json();
      if (!statusResponse.ok) throw new Error(statusBody.error || '无法读取本地数据状态');
      setStatus(statusBody);
      setReports(Array.isArray(reportBody.reports) ? reportBody.reports : []);
      setMessage('本地数据目录已连接。所有快照、预检回执和日报均只写入该目录。');
    } catch (error) {
      setMessage(error instanceof Error ? `${error.message}。请运行 pnpm start:local。` : '本地桥接尚未启动。');
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  const availableCount = useMemo(() => Object.values(status.assets || {}).filter((asset) => asset.status === 'available').length, [status]);

  async function action(kind: 'archive' | 'prepare' | 'preflight', skillId?: string) {
    setBusy(skillId || kind);
    setSelected(null);
    try {
      const url = kind === 'archive' ? '/skill14/archive-daily' : kind === 'prepare' ? '/skill14/prepare-packages' : '/skill14/preflight';
      const response = await fetch(bridgeUrl(url), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: kind === 'preflight' ? JSON.stringify({ skillId }) : undefined,
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error || '本地任务失败');
      if (kind === 'preflight') setSelected(body as Preflight);
      await refresh();
    } catch (error) {
      setSelected({ status: 'error', error: error instanceof Error ? error.message : String(error) });
    } finally {
      setBusy('');
    }
  }

  return <div className={styles.shell}>
    <header className={styles.header}>
      <div><div className={styles.eyebrow}>ZHANGCAI · 14 SKILL RUNTIME</div><h1>14 个电脑版技能的网页运行台</h1><p>网页只负责任务、数据门禁和报告展示；原始规则仍由 Python、数据服务或 Windows 通达信/TQ Worker 执行。缺数据会落盘并明确标识，不用模型补写结论。</p></div>
      <div className={styles.ports}><span>本地运行</span><span>本地桥接 {bridgeHostLabel()}</span><span>数据目录 {status.data_root || 'resource-library'}</span></div>
    </header>
    <div className={styles.grid}>
      <main className={styles.main}>
        <section className={styles.card}>
          <div className={styles.cardHead}><h2>数据落盘与降级控制</h2><div className={styles.actions}><button className={`${styles.button} ${styles.secondary}`} disabled={Boolean(busy)} onClick={() => void action('prepare')}>{busy === 'prepare' ? '部署中…' : '部署 14 个技能包'}</button><button className={styles.button} disabled={Boolean(busy)} onClick={() => void action('archive')}>{busy === 'archive' ? '归档中…' : '归档本地日线（420 日）'}</button></div></div>
          <div className={styles.statusGrid}><div className={styles.metric}><b>14</b><span>受控技能包</span></div><div className={styles.metric}><b>{availableCount}</b><span>可用数据资产</span></div><div className={styles.metric}><b>{reports.length}</b><span>已落盘预检报告</span></div><div className={styles.metric}><b>{status.assets?.tdx_daily_history?.current_trade_date_symbols || '—'}</b><span>同日股票覆盖</span></div></div>
          <p className={`${styles.notice} ${message.includes('无法') || message.includes('尚未') ? styles.error : ''}`}>{message}</p>
        </section>
        <section className={styles.card}>
          <div className={styles.cardHead}><h2>14 项技能适配</h2><span className={styles.tag}>先预检，再运行</span></div>
          <div className={styles.skills}>{catalog.skills.map((skill) => <article className={styles.skill} key={skill.id}><div className={styles.skillTop}><div><h3>{skill.name}</h3><div className={styles.meta}><span>{skill.category}</span><span>·</span><span>{skill.mode}</span></div></div><span className={`${styles.state} ${stateClass(selected?.skill?.name === skill.name ? selected.status : '')}`}>{selected?.skill?.name === skill.name ? statusText[selected.status] || selected.status : '待预检'}</span></div><p>{skill.summary}</p><div className={styles.policy}>{skill.degrade}</div><button className={styles.button} disabled={Boolean(busy)} onClick={() => void action('preflight', skill.id)}>{busy === skill.id ? '生成运行单…' : '生成数据预检与运行单'}</button></article>)}</div>
        </section>
        {selected && <section className={styles.result}><h3>{selected.skill?.name || '预检结果'} · {statusText[selected.status] || selected.status}</h3>{selected.error ? <p>{selected.error}</p> : <><p>{selected.execution_note}</p><ul><li>缺少必需数据：{selected.required_missing?.length ? selected.required_missing.map((item) => assetNames[item] || item).join('、') : '无'}</li><li>缺少可降级数据：{selected.optional_missing?.length ? selected.optional_missing.map((item) => assetNames[item] || item).join('、') : '无'}</li><li>规则：{selected.degrade_policy}</li></ul></>}</section>}
      </main>
      <aside className={styles.side}>
        <section className={styles.card}><div className={styles.cardHead}><h2>数据资产状态</h2><button className={`${styles.button} ${styles.secondary}`} disabled={Boolean(busy)} onClick={() => void refresh()}>刷新</button></div>{catalog.dataAssets.map((asset) => { const item = status.assets?.[asset.id]; return <div className={styles.asset} key={asset.id}><b>{asset.name}</b><span className={`${styles.state} ${stateClass(item?.status)}`}>{statusText[item?.status || 'missing'] || item?.status || '待归档'}</span><small>{item?.reason || asset.path}</small></div>; })}</section>
        <section className={styles.card}><div className={styles.cardHead}><h2>已落盘日报 / 回执</h2><span className={styles.tag}>{reports.length}</span></div>{reports.length ? reports.slice(0, 10).map((report) => <div className={styles.report} key={report.report_id}><span className={`${styles.state} ${stateClass(report.status)}`}>{statusText[report.status || ''] || report.status}</span><div><b>{report.skill_name}</b><small>{report.created_at}</small></div></div>) : <p className={styles.empty}>尚未生成预检报告。每次预检都会同时写入 JSON 回执与 Markdown 日报。</p>}</section>
      </aside>
    </div>
    <footer className={styles.footer}>数据目录结构：market/daily · public · evidence · skills · reports/daily · jobs。面向后续 EXE 时，只需将 ZHANGCAI_DATA_DIR 指向用户可写目录。</footer>
  </div>;
}
