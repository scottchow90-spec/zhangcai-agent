import React, {useCallback, useEffect, useState} from 'react';
import {Audio} from '@remotion/media';
import {TransitionSeries, linearTiming} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {slide} from '@remotion/transitions/slide';
import {
  AbsoluteFill,
  Easing,
  Sequence,
  cancelRender,
  continueRender,
  delayRender,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {content} from './content';

const P = {
  black: '#050607',
  ink: '#0A1016',
  ivory: '#F1EEE6',
  paper: '#D8D2C5',
  cyan: '#40E8FF',
  blue: '#176BFF',
  green: '#6CF59C',
  red: '#FF4255',
  amber: '#FFB52E',
  violet: '#7D5CFF',
  white: '#FFFFFF',
};
const FONT = 'Microsoft YaHei, Noto Sans SC, sans-serif';
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const cubic = Easing.bezier(0.16, 1, 0.3, 1);
const show = (frame: number, start = 0, duration = 24) => interpolate(frame, [start, start + duration], [0, 1], {...clamp, easing: cubic});
const loop = (frame: number, period: number) => (frame % period) / period;

const Grain: React.FC<{dark?: boolean}> = ({dark = true}) => {
  const frame = useCurrentFrame();
  return <AbsoluteFill style={{pointerEvents: 'none', opacity: dark ? 0.12 : 0.08, mixBlendMode: dark ? 'screen' : 'multiply', translate: `${(frame * 1.7) % 18}px ${(frame * 1.1) % 18}px`, backgroundImage: 'radial-gradient(circle at 1px 1px, currentColor 1px, transparent 1.4px)', backgroundSize: '18px 18px', color: dark ? P.white : P.black}} />;
};

const EdgeIndex: React.FC<{value: string; dark?: boolean}> = ({value, dark = true}) => (
  <div style={{position: 'absolute', right: 24, top: 68, writingMode: 'vertical-rl', fontFamily: FONT, fontSize: 19, fontWeight: 900, letterSpacing: 5, color: dark ? 'rgba(255,255,255,.5)' : 'rgba(5,6,7,.5)'}}>{value}</div>
);

const MovingBand: React.FC<{text: string; color: string; background: string; top: number}> = ({text, color, background, top}) => {
  const frame = useCurrentFrame();
  const x = -((frame * 4.6) % 760);
  return <div style={{position: 'absolute', left: 0, right: 0, top, height: 82, overflow: 'hidden', background, color, display: 'flex', alignItems: 'center', borderTop: `2px solid ${color}`, borderBottom: `2px solid ${color}`}}><div style={{whiteSpace: 'nowrap', translate: `${x}px 0`, fontFamily: FONT, fontSize: 26, fontWeight: 900, letterSpacing: 5}}>{`${text}  ◆  `.repeat(12)}</div></div>;
};

const Risk: React.FC = () => {
  const frame = useCurrentFrame();
  const title = show(frame, 2, 20);
  return <AbsoluteFill style={{fontFamily: FONT, background: '#E9E2D3', color: '#11151A', padding: '0 64px', boxSizing: 'border-box'}}>
    <div style={{position: 'absolute', left: 0, right: 0, top: 0, height: 390, background: '#0B2442'}} />
    <div style={{position: 'relative', marginTop: 74, fontSize: 27, fontWeight: 900, color: '#FFD65A', letterSpacing: 2}}>教学案例｜交流学习｜方法演示</div>
    <div style={{position: 'relative', marginTop: 70, fontSize: 108, lineHeight: 1.02, fontWeight: 950, color: P.white, opacity: title, translate: `${(1 - title) * -36}px 0`}}>投资<br />风险提示</div>
    <div style={{position: 'relative', display: 'grid', gap: 18, marginTop: 76}}>
      {['不作为股票推荐', '不构成投资建议', '不作为买卖依据'].map((text, i) => <div key={text} style={{height: 116, display: 'flex', alignItems: 'center', padding: '0 36px', background: '#FFF1C7', borderLeft: '12px solid #D40000', color: '#D40000', fontSize: 42, fontWeight: 950, opacity: show(frame, 12 + i * 6, 20), translate: `${(1 - show(frame, 12 + i * 6, 20)) * 40}px 0`}}>{text}</div>)}
    </div>
    <div style={{display: 'grid', gap: 14, marginTop: 32}}>
      <div style={{background: '#9D0000', color: P.white, padding: '26px 34px', fontSize: 28, lineHeight: 1.55, fontWeight: 800}}>授课方/作者不具备荐股资质</div>
      <div style={{background: '#9D0000', color: P.white, padding: '26px 34px', fontSize: 27, lineHeight: 1.55, fontWeight: 800}}>学生不得据此直接买卖；需独立判断并严格根据规则训练</div>
    </div>
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 260, background: '#0B2442', padding: '48px 64px', boxSizing: 'border-box'}}>
      <div style={{fontSize: 38, color: '#FFD65A', fontWeight: 950}}>股市有风险，入市需谨慎</div>
      <div style={{fontSize: 25, color: P.white, lineHeight: 1.55, marginTop: 25}}>本页为教学案例风险提示，后续内容依据当前交易日数据计算。</div>
    </div>
  </AbsoluteFill>;
};

const CandleField: React.FC = () => {
  const frame = useCurrentFrame();
  const values = [42, 58, 51, 75, 68, 91, 80, 112, 102, 134, 118, 150, 138, 172, 160, 198, 184];
  return <div style={{position: 'absolute', left: 52, right: 52, top: 820, height: 530, display: 'flex', alignItems: 'flex-end', gap: 16, overflow: 'hidden'}}>{values.map((value, i) => {
    const p = show(frame, 22 + i * 3, 22);
    const up = i % 4 !== 1;
    const drift = Math.sin((frame + i * 9) / 14) * 8;
    return <div key={i} style={{height: value * 2.15 * p, flex: 1, minWidth: 22, position: 'relative', translate: `0 ${drift}px`}}><div style={{position: 'absolute', width: 3, left: '50%', top: -30, bottom: -24, background: up ? P.green : P.red}} /><div style={{position: 'absolute', inset: 0, border: `4px solid ${up ? P.green : P.red}`, background: up ? `${P.green}25` : `${P.red}25`}} /></div>;
  })}</div>;
};

const HookScene: React.FC = () => {
  const frame = useCurrentFrame();
  const p = show(frame, 3, 28);
  return <AbsoluteFill style={{fontFamily: FONT, background: P.ivory, color: P.black, overflow: 'hidden'}}>
    <div style={{position: 'absolute', left: -120, top: 120, fontSize: 390, fontWeight: 950, lineHeight: 0.8, color: 'rgba(5,6,7,.055)', rotate: '-8deg'}}>A股</div>
    <div style={{position: 'absolute', left: 0, top: 0, width: 28, height: 1920, background: P.red}} />
    <div style={{position: 'absolute', left: 62, top: 70, fontSize: 26, fontWeight: 950, letterSpacing: 3}}>收盘复盘 / 教学能力演示</div>
    <div style={{position: 'absolute', left: 58, top: 240, width: 780, fontSize: 146, lineHeight: 0.94, fontWeight: 950, letterSpacing: -7, opacity: p, translate: `${(1 - p) * -70}px 0`}}>先看结构<br /><span style={{color: P.red}}>再下结论</span></div>
    <div style={{position: 'absolute', left: 64, top: 590, width: 850, fontSize: 35, lineHeight: 1.55, fontWeight: 750}}>量价 · 市场宽度 · 主线承接<br /><span style={{fontSize: 26, opacity: 0.6}}>三项必须同步验证</span></div>
    <CandleField />
    <MovingBand text="STRUCTURE BEFORE OPINION / 结构先于结论" color={P.ivory} background={P.black} top={1440} />
    <div style={{position: 'absolute', right: 50, top: 520, width: 180, height: 180, borderRadius: '50%', background: P.cyan, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 30, fontWeight: 950, rotate: `${frame * 0.22}deg`}}>01 / 05</div>
    <EdgeIndex value="MARKET STRUCTURE" dark={false} />
    <Grain dark={false} />
  </AbsoluteFill>;
};

const HeatTile: React.FC<{i: number}> = ({i}) => {
  const frame = useCurrentFrame();
  const up = i < 20 || i % 7 === 0;
  const p = show(frame, 3 + i * 1.25, 18);
  const pulse = 0.86 + Math.sin((frame + i * 13) / 16) * 0.14;
  const height = [142, 188, 116, 164, 208][i % 5];
  return <div style={{height, position: 'relative', overflow: 'hidden', background: up ? P.green : P.red, opacity: p * pulse, border: `3px solid ${P.black}`}}><div style={{position: 'absolute', left: 14, top: 12, fontFamily: FONT, fontSize: 19, fontWeight: 950, color: P.black}}>{String(i + 1).padStart(2, '0')}</div><div style={{position: 'absolute', right: 12, bottom: 8, fontSize: 22, fontWeight: 950, color: P.black}}>{up ? '▲' : '▼'}</div></div>;
};

const BreadthScene: React.FC = () => {
  const frame = useCurrentFrame();
  const p = show(frame, 5, 32);
  return <AbsoluteFill style={{fontFamily: FONT, background: P.black, color: P.white, overflow: 'hidden'}}>
    <div style={{position: 'absolute', left: 54, top: 64, fontSize: 24, color: P.green, fontWeight: 950, letterSpacing: 3}}>02 / 市场宽度</div>
    <div style={{position: 'absolute', left: 48, right: 48, top: 150, display: 'grid', gridTemplateColumns: '1.15fr .85fr', gap: 18}}>
      <div style={{background: P.ivory, color: P.black, padding: '28px 30px 34px'}}><div style={{fontSize: 26, fontWeight: 900}}>上涨家数</div><div style={{fontSize: 118, lineHeight: 1, fontWeight: 950, letterSpacing: -6, marginTop: 12}}>{Math.round(content.breadth[0].value * p).toLocaleString()}</div><div style={{fontSize: 25, color: '#087A49', fontWeight: 950, marginTop: 16}}>▲ 广度扩张</div></div>
      <div style={{background: P.red, color: P.white, padding: '28px 26px'}}><div style={{fontSize: 25, fontWeight: 900}}>下跌家数</div><div style={{fontSize: 88, lineHeight: 1, fontWeight: 950, letterSpacing: -4, marginTop: 20}}>{Math.round(content.breadth[1].value * p).toLocaleString()}</div><div style={{fontSize: 22, fontWeight: 950, marginTop: 20}}>▼ 风险侧</div></div>
    </div>
    <div style={{position: 'absolute', left: 48, right: 48, top: 510, height: 940, display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gridAutoRows: 'min-content', gap: 5, overflow: 'hidden'}}>{Array.from({length: 32}, (_, i) => <HeatTile key={i} i={i} />)}</div>
    <div style={{position: 'absolute', left: 52, bottom: 318, background: P.black, border: `4px solid ${P.white}`, padding: '20px 28px', fontSize: 34, fontWeight: 950}}>不是一根指数线，是全市场横截面</div>
    <MovingBand text="3186 UP / 1764 DOWN / BREADTH IS EVIDENCE" color={P.black} background={P.green} top={1455} />
    <EdgeIndex value="MARKET BREADTH" />
    <Grain />
  </AbsoluteFill>;
};

const FlowColumn: React.FC<{name: string; score: number; note: string; color: string; index: number}> = ({name, score, note, color, index}) => {
  const frame = useCurrentFrame();
  const p = show(frame, 8 + index * 14, 34);
  const level = score * p;
  return <div style={{position: 'relative', height: 1040, background: 'rgba(0,0,0,.2)', border: '2px solid rgba(255,255,255,.2)', overflow: 'hidden'}}>
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: `${level}%`, background: `linear-gradient(180deg, ${color}, ${color}33)`}} />
    <div style={{position: 'absolute', left: 22, right: 20, top: 24}}><div style={{fontSize: 24, fontWeight: 950}}>{name}</div><div style={{fontSize: 100, lineHeight: 1, fontWeight: 950, marginTop: 24}}>{Math.round(level)}</div></div>
    <div style={{position: 'absolute', left: 20, right: 18, bottom: 30, fontSize: 22, lineHeight: 1.5, fontWeight: 750}}>{note}</div>
    {Array.from({length: 5}, (_, i) => <div key={i} style={{position: 'absolute', left: 18 + ((frame * (1.1 + index * .2) + i * 53) % 210), bottom: ((frame * (2 + index * .4) + i * 140) % 760), width: 8 + i * 2, height: 8 + i * 2, borderRadius: '50%', background: P.white, opacity: .3}} />)}
  </div>;
};

const FlowScene: React.FC = () => {
  const frame = useCurrentFrame();
  return <AbsoluteFill style={{fontFamily: FONT, background: 'linear-gradient(155deg,#071329,#082C4D 50%,#04111E)', color: P.white, overflow: 'hidden'}}>
    <div style={{position: 'absolute', left: 52, top: 60, fontSize: 24, fontWeight: 950, color: P.cyan, letterSpacing: 3}}>03 / 主线与承接</div>
    <div style={{position: 'absolute', left: 48, right: 48, top: 155, fontSize: 92, lineHeight: 1.03, fontWeight: 950, letterSpacing: -4}}>热度要穿过<br /><span style={{color: P.green}}>资金验证</span></div>
    <div style={{position: 'absolute', left: 48, right: 48, top: 480, display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14}}>
      {content.themes.map((item, i) => <FlowColumn key={item.name} {...item} index={i} color={[P.cyan, P.green, P.amber][i]} />)}
    </div>
    <div style={{position: 'absolute', left: -80, bottom: 165, fontSize: 178, fontWeight: 950, letterSpacing: -10, color: 'rgba(255,255,255,.055)', translate: `${-30 + loop(frame, 240) * 90}px 0`}}>CAPITAL FLOW</div>
    <EdgeIndex value="CAPITAL FLOW" />
    <Grain />
  </AbsoluteFill>;
};

const ScenarioScene: React.FC = () => {
  const frame = useCurrentFrame();
  const path = show(frame, 18, 68);
  return <AbsoluteFill style={{fontFamily: FONT, background: P.ivory, color: P.black, overflow: 'hidden'}}>
    <div style={{position: 'absolute', left: 46, top: 58, fontSize: 24, fontWeight: 950, letterSpacing: 3}}>04 / 条件响应</div>
    <div style={{position: 'absolute', left: -16, top: 135, fontSize: 290, lineHeight: .8, fontWeight: 950, letterSpacing: -18}}>IF</div>
    <div style={{position: 'absolute', right: -12, top: 390, fontSize: 220, lineHeight: .8, fontWeight: 950, letterSpacing: -14, color: P.red}}>THEN</div>
    <svg viewBox="0 0 1080 1180" width="1080" height="1180" style={{position: 'absolute', top: 300, left: 0}}>
      <path d="M90 550 C260 360 390 360 520 550 S790 760 990 470" fill="none" stroke="#111" strokeWidth="18" pathLength="1" strokeDasharray="1" strokeDashoffset={1 - path} />
      <path d="M90 550 C260 360 390 360 520 550 S790 760 990 470" fill="none" stroke={P.cyan} strokeWidth="6" pathLength="100" strokeDasharray="9 13" strokeDashoffset={-frame * 1.5} />
    </svg>
    {[
      {n: '01', text: '宽度延续', x: 62, y: 820, color: P.green},
      {n: '02', text: '主线承接', x: 380, y: 650, color: P.cyan},
      {n: '03', text: '条件执行', x: 740, y: 850, color: P.amber},
    ].map((item, i) => <div key={item.n} style={{position: 'absolute', left: item.x, top: item.y, width: 275, height: 240, background: P.black, color: P.white, padding: 28, boxSizing: 'border-box', borderTop: `12px solid ${item.color}`, opacity: show(frame, 24 + i * 16, 22), translate: `0 ${(1 - show(frame, 24 + i * 16, 22)) * 55}px`}}><div style={{fontSize: 27, color: item.color, fontWeight: 950}}>{item.n}</div><div style={{fontSize: 39, fontWeight: 950, marginTop: 36}}>{item.text}</div></div>)}
    <div style={{position: 'absolute', left: 48, right: 48, top: 1210, padding: '34px 38px', background: P.red, color: P.white, fontSize: 35, lineHeight: 1.5, fontWeight: 850}}><span style={{color: P.black, fontWeight: 950}}>失效：</span>{content.invalidation}</div>
    <MovingBand text="NO CERTAINTY / ONLY CONDITIONS / 不做确定性预测" color={P.ivory} background={P.black} top={1470} />
    <EdgeIndex value="IF / THEN" dark={false} />
    <Grain dark={false} />
  </AbsoluteFill>;
};

const CheckRow: React.FC<{index: number; text: string; color: string}> = ({index, text, color}) => {
  const frame = useCurrentFrame();
  const p = show(frame, 8 + index * 18, 28);
  return <div style={{height: 250, display: 'grid', gridTemplateColumns: '230px 1fr 110px', alignItems: 'center', background: index % 2 === 0 ? P.ivory : '#101418', color: index % 2 === 0 ? P.black : P.white, borderBottom: `4px solid ${color}`, opacity: p, translate: `${(1 - p) * (index % 2 === 0 ? -80 : 80)}px 0`}}><div style={{fontSize: 98, fontWeight: 950, paddingLeft: 42, color}}>{String(index + 1).padStart(2, '0')}</div><div style={{fontSize: 42, lineHeight: 1.35, fontWeight: 950}}>{text}</div><div style={{width: 64, height: 64, borderRadius: '50%', background: color, color: P.black, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 38, fontWeight: 950}}>✓</div></div>;
};

const CloseScene: React.FC = () => {
  const frame = useCurrentFrame();
  return <AbsoluteFill style={{fontFamily: FONT, background: P.black, color: P.white, overflow: 'hidden'}}>
    <div style={{position: 'absolute', left: 48, top: 60, fontSize: 24, fontWeight: 950, color: P.green, letterSpacing: 3}}>05 / 复盘落点</div>
    <div style={{position: 'absolute', left: 44, top: 150, fontSize: 96, lineHeight: 1.02, fontWeight: 950, letterSpacing: -5}}>复盘不是<br /><span style={{color: P.red}}>预测</span></div>
    <div style={{position: 'absolute', right: 46, top: 185, width: 280, height: 280, borderRadius: '50%', border: `20px solid ${P.green}`, display: 'flex', alignItems: 'center', justifyContent: 'center', rotate: `${frame * .35}deg`}}><div style={{fontSize: 34, fontWeight: 950, rotate: `${-frame * .35}deg`}}>EVIDENCE<br />LOOP</div></div>
    <div style={{position: 'absolute', left: 0, right: 0, top: 560}}>{content.checklist.map((item, i) => <CheckRow key={item} index={i} text={item} color={[P.green, P.cyan, P.amber][i]} />)}</div>
    <div style={{position: 'absolute', left: 48, right: 48, top: 1370, height: 170, display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: `2px solid ${P.green}`, borderBottom: `2px solid ${P.green}`}}><div style={{fontSize: 31, color: P.green, fontWeight: 950}}>观点 → 条件 → 验证</div><div style={{fontSize: 22, color: 'rgba(255,255,255,.6)', lineHeight: 1.55, textAlign: 'right'}}>AI生成配音 · 教学能力演示<br />以证据和来源截止时间为准</div></div>
    <div style={{position: 'absolute', left: -40, bottom: 180, fontSize: 120, fontWeight: 950, letterSpacing: -5, color: 'rgba(255,255,255,.06)', translate: `${-20 + loop(frame, 180) * 80}px 0`}}>VERIFY BEFORE ACT</div>
    <Grain />
  </AbsoluteFill>;
};

type Caption = {text: string; startMs: number; endMs: number};
const Captions: React.FC = () => {
  const [items, setItems] = useState<Caption[] | null>(null);
  const [handle] = useState(() => delayRender('captions'));
  const load = useCallback(async () => {
    try {
      const response = await fetch(staticFile('captions.json'));
      if (!response.ok) throw new Error(`captions:${response.status}`);
      setItems(await response.json() as Caption[]);
      continueRender(handle);
    } catch (error) { cancelRender(error); }
  }, [handle]);
  useEffect(() => { void load(); }, [load]);
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ms = (frame / fps) * 1000;
  const active = items?.find((item) => item.startMs <= ms && item.endMs > ms);
  if (!active) return null;
  const p = interpolate(ms, [active.startMs, active.startMs + 180], [0, 1], {...clamp, easing: cubic});
  const accent = ms < 11000 ? P.red : ms < 24500 ? P.green : ms < 41000 ? P.cyan : ms < 54500 ? P.red : P.green;
  return <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', padding: '0 48px 88px', boxSizing: 'border-box', pointerEvents: 'none'}}><div style={{position: 'relative', minWidth: 680, maxWidth: 950, background: 'rgba(4,5,6,.94)', color: P.white, padding: '24px 34px 26px 44px', fontFamily: FONT, fontSize: 47, lineHeight: 1.32, fontWeight: 950, textAlign: 'center', borderTop: `6px solid ${accent}`, boxShadow: '0 18px 60px rgba(0,0,0,.48)', opacity: p, translate: `0 ${(1 - p) * 18}px`}}><div style={{position: 'absolute', left: 0, top: 0, bottom: 0, width: 12, background: accent}} />{active.text}</div></AbsoluteFill>;
};

const Business: React.FC = () => <TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={330}><HookScene /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={slide({direction: 'from-bottom'})} timing={linearTiming({durationInFrames: 15})} />
  <TransitionSeries.Sequence durationInFrames={420}><BreadthScene /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={fade()} timing={linearTiming({durationInFrames: 15})} />
  <TransitionSeries.Sequence durationInFrames={510}><FlowScene /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={slide({direction: 'from-left'})} timing={linearTiming({durationInFrames: 15})} />
  <TransitionSeries.Sequence durationInFrames={420}><ScenarioScene /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={fade()} timing={linearTiming({durationInFrames: 15})} />
  <TransitionSeries.Sequence durationInFrames={330}><CloseScene /></TransitionSeries.Sequence>
</TransitionSeries>;

export const StockRecap: React.FC = () => <AbsoluteFill style={{background: P.black}}>
  <Sequence name="Risk notice" durationInFrames={150}><Risk /></Sequence>
  <Sequence name="Five editorial systems" from={150} durationInFrames={1950}><Business /></Sequence>
  <Sequence name="Narration" from={150}><Audio src={staticFile('voiceover.mp3')} volume={1} /></Sequence>
  <Sequence name="Captions" from={150}><Captions /></Sequence>
</AbsoluteFill>;
