export const content = {
  title: 'A股收盘复盘',
  date: '教学能力演示',
  pulse: '先看结构，再下结论',
  pulseDetail: '量价、市场宽度与主线承接必须同步验证',
  marketMood: '偏强震荡',
  breadth: [
    {label: '上涨家数', value: 3186, tone: 'up' as const},
    {label: '下跌家数', value: 1764, tone: 'down' as const},
    {label: '涨停家数', value: 72, tone: 'up' as const},
  ],
  themes: [
    {name: '主线强度', score: 86, note: '题材辨识度较高，仍需成交证据闭环'},
    {name: '资金承接', score: 71, note: '分歧阶段观察回流持续性'},
    {name: '风险偏好', score: 63, note: '热度抬升，但不支持一致性追涨'},
  ],
  scenario: '次日只做条件响应，不做确定性预测',
  invalidation: '若量价背离、主线扩散失败或承接转弱，立即降低结论置信度。',
  checklist: ['宽度是否继续扩张', '主线是否获得增量承接', '失效条件是否被触发'],
};
