$ErrorActionPreference = 'Stop'
[System.Threading.Thread]::CurrentThread.CurrentCulture = [System.Globalization.CultureInfo]::InvariantCulture
$j = "C:\work\260907 掌财智能体\CodeX-st-wsp\zhangcai-demo\data\harness\tasks\_task5_chunks\json"
function L($n) { Get-Content -Raw -Encoding UTF8 (Join-Path $j "$n.json") | ConvertFrom-Json }
function S($v) { if ($null -eq $v) { '' } elseif ($v -is [bool]) { if ($v) { 'true' } else { 'false' } } else { [string]$v } }

$topgain = L 'topgain'; $topamount = L 'topamount'; $losers = L 'losers'
$limitdown = L 'limitdown'; $prev = L 'prevlimitup'; $ind = L 'industry'
$th = L 'theme'; $intra = L 'intraday'; $ds = L 'datasource'
$luc = L 'limitup_cand'; $ml = L 'mainline'

function StockRows($arr) {
  $l = [System.Collections.Generic.List[object]]::new()
  foreach ($x in @($arr)) {
    $l.Add([object[]]@((S $x.code), (S $x.name), (S $x.pct), (S $x.close), (S $x.amount), (S $x.market)))
  }
  return ,$l
}

$tables = [System.Collections.ArrayList]::new()

[void]$tables.Add([ordered]@{
  title = '指数快照（20260909 收盘）'
  columns = @('指数', '收盘', '涨跌幅')
  rows = @(
    ,@('上证指数', '3932.13', '-0.49%')
    ,@('深证成指', '13617.82', '-0.77%')
    ,@('创业板指', '3338.71', '-0.48%')
    ,@('科创50', '1568.56', '-0.73%')
    ,@('上证50', '2899.01', '-0.39%')
    ,@('北证50', '1056.66', '-2.32%')
  )
})

[void]$tables.Add([ordered]@{
  title = '市场宽度与样本成交（20260909）'
  columns = @('指标', '数值')
  rows = @(
    ,@('数据日期', '20260909')
    ,@('同日股票', '5546')
    ,@('上涨', '1786')
    ,@('下跌', '3646')
    ,@('平盘', '114')
    ,@('样本成交额（元）', '1873328634963')
  )
})

[void]$tables.Add([ordered]@{
  title = '涨幅领先候选（20 条）'
  columns = @('代码', '名称', '涨跌幅%', '收盘', '成交额（元）', '市场')
  rows = StockRows $topgain
})

[void]$tables.Add([ordered]@{
  title = '成交额领先候选（20 条）'
  columns = @('代码', '名称', '涨跌幅%', '收盘', '成交额（元）', '市场')
  rows = StockRows $topamount
})

[void]$tables.Add([ordered]@{
  title = '跌幅/负反馈候选（20 条）'
  columns = @('代码', '名称', '涨跌幅%', '收盘', '成交额（元）', '市场')
  rows = StockRows $losers
})

[void]$tables.Add([ordered]@{
  title = '跌停阈值候选（日线推导，仅 1 条）'
  columns = @('代码', '名称', '涨跌幅%', '收盘', '成交额（元）', '市场')
  rows = StockRows $limitdown
})

[void]$tables.Add([ordered]@{
  title = '前日涨停表现（日线推导）'
  columns = @('指标', '数值')
  rows = @(
    ,@('前一日交易日 previousDate', (S $prev.previousDate))
    ,@('前日涨停家数 count', (S $prev.count))
    ,@('当日平均涨跌幅% todayAvgPct', (S $prev.todayAvgPct))
    ,@('当日上涨 todayUp', (S $prev.todayUp))
    ,@('当日下跌 todayDown', (S $prev.todayDown))
    ,@('当日平盘 todayFlat', (S $prev.todayFlat))
  )
})

$indRows = @($ind | Sort-Object avgPct -Descending | Select-Object -First 12 | ForEach-Object {
  ,@((S $_.name), (S $_.count), (S $_.avgPct), (S $_.up), (S $_.down), (S $_.flat), (S $_.limitCount), (S $_.amount), (($_.leaders | ForEach-Object { $_.name }) -join '、'))
})
[void]$tables.Add([ordered]@{
  title = 'TDX行业板块聚合（共 31 个，按平均涨跌幅取前 12；本地通达信自定义行业映射）'
  columns = @('板块', '成员数', '平均涨跌幅%', '上涨', '下跌', '平盘', '涨停家数', '成交额（元）', '领涨成员前5')
  rows = $indRows
})

$thRows = @($th | Sort-Object avgPct -Descending | Select-Object -First 12 | ForEach-Object {
  ,@((S $_.name), (S $_.count), (S $_.avgPct), (S $_.up), (S $_.down), (S $_.flat), (S $_.limitCount), (S $_.amount), (($_.leaders | ForEach-Object { $_.name }) -join '、'))
})
[void]$tables.Add([ordered]@{
  title = 'TDX主题板块聚合（共 40 个，按平均涨跌幅取前 12；本地通达信自定义主题映射，updatedDate=20260904）'
  columns = @('板块', '成员数', '平均涨跌幅%', '上涨', '下跌', '平盘', '涨停家数', '成交额（元）', '领涨成员前5')
  rows = $thRows
})

$lucRows = @($luc | ForEach-Object { ,@((S $_.code), (S $_.name), (S $_.pct), (S $_.limitPct), (S $_.streak), (S $_.amount)) })
[void]$tables.Add([ordered]@{
  title = '涨停/连板候选（30 条，日线推导候选）'
  columns = @('代码', '名称', '涨跌幅%', '涨停幅度%', '连板数', '成交额（元）')
  rows = $lucRows
})

$mlRows = @($ml | ForEach-Object { ,@((S $_.name), (S $_.tag), (S $_.count), (S $_.avgPct), (S $_.amount), (($_.leaders) -join '、')) })
[void]$tables.Add([ordered]@{
  title = '主线名称聚类候选（12 条，TDX主题成员聚合标签）'
  columns = @('主线', '标签', '成员数', '平均涨跌幅%', '成交额（元）', '领涨成员前5')
  rows = $mlRows
})

[void]$tables.Add([ordered]@{
  title = '盘中封板/炸板代理（本地日线 OHLC 推导，非逐笔；date=20260908）'
  columns = @('指标', '数值')
  rows = @(
    ,@('日期', (S $intra.date))
    ,@('触板家数（上） upperHitCount', (S $intra.upperHitCount))
    ,@('收盘封板（上） upperClosedCount', (S $intra.upperClosedCount))
    ,@('触板后打开（上） openedAfterHitCount', (S $intra.openedAfterHitCount))
    ,@('封板率% sealRatePct', (S $intra.sealRatePct))
    ,@('炸板率% explosionRatePct', (S $intra.explosionRatePct))
    ,@('触板家数（下） lowerHitCount', (S $intra.lowerHitCount))
    ,@('收盘封板（下） lowerClosedCount', (S $intra.lowerClosedCount))
    ,@('触板后打开（下） lowerOpenedAfterHitCount', (S $intra.lowerOpenedAfterHitCount))
    ,@('下封板率% lowerSealRatePct', (S $intra.lowerSealRatePct))
    ,@('首封时刻可得 firstSealTimeAvailable', (S $intra.firstSealTimeAvailable))
    ,@('盘口可得 orderBookAvailable', (S $intra.orderBookAvailable))
    ,@('lc5 文件数', (S $intra.lc5Files))
    ,@('lc5 日期分布', '20260904:2738')
    ,@('lc5 当日文件数 lc5CurrentDateCount', (S $intra.lc5CurrentDateCount))
    ,@('数据新鲜 dataFresh', (S $intra.dataFresh))
  )
})

[void]$tables.Add([ordered]@{
  title = '数据源状态与新鲜度'
  columns = @('来源键', '状态', '关键字段')
  rows = @(
    ,@('industry', (S $ds.industry.status), ('mappedStocks=' + (S $ds.industry.mappedStocks) + '；coveragePct=' + (S $ds.industry.coveragePct) + '；mappingFile=' + (S $ds.industry.mappingFile) + '；captionFile=' + (S $ds.industry.captionFile)))
    ,@('conceptBoards', (S $ds.conceptBoards.status), ('boardCount=' + (S $ds.conceptBoards.boardCount) + '；file=' + (S $ds.conceptBoards.file)))
    ,@('intraday', (S $ds.intraday.status), ('lc5Files=' + (S $ds.intraday.lc5Files) + '；lc5CurrentDateCount=' + (S $ds.intraday.lc5CurrentDateCount) + '；firstSealTimeAvailable=' + (S $ds.intraday.firstSealTimeAvailable) + '；orderBookAvailable=' + (S $ds.intraday.orderBookAvailable)))
    ,@('financing', (S $ds.financing.status), ('snapshotFile=' + (S $ds.financing.snapshotFile) + '；snapshotExists=' + (S $ds.financing.snapshotExists)))
    ,@('lhb', (S $ds.lhb.status), ('snapshotFile=' + (S $ds.lhb.snapshotFile) + '；snapshotExists=' + (S $ds.lhb.snapshotExists)))
    ,@('capitalFlow', (S $ds.capitalFlow.status), ('formulaRegistry=' + (S $ds.capitalFlow.formulaRegistry) + '；formulas=' + (($ds.capitalFlow.formulas) -join '/')))
    ,@('news', (S $ds.news.status), ('file=' + (S $ds.news.file) + '；latestEventDate=' + (S $ds.news.latestEventDate) + '；currentDateMatched=' + (S $ds.news.currentDateMatched)))
  )
})

[void]$tables.Add([ordered]@{
  title = '本地每日更新上下文（date=2026-09-10，与行情数据日 20260909 不是同一天）'
  columns = @('项目', '值')
  rows = @(
    ,@('上下文日期', '2026-09-10')
    ,@('生成时间 generatedAt', '2026-09-10T02:33:55.474Z')
    ,@('步骤1 通达信运行状态', 'completed / code=0 / 2026-09-10T02:33:46.986Z')
    ,@('步骤2 新闻快讯补齐', 'completed / code=0 / 2026-09-10T02:33:47.597Z')
    ,@('步骤3 公开行情补齐', 'completed / code=0 / 2026-09-10T02:33:47.978Z')
    ,@('步骤4 通达信日线补齐', 'completed / code=0 / 2026-09-10T02:33:55.460Z')
    ,@('公开行情快照', 'date=2026-09-10；fetchedAt=2026-09-10T10:33:47+08:00；lianban=available/10 条；eastmoneyLimitUp=available/28 条；eastmoneyLhb=missing')
    ,@('新闻快照', 'available；100 条快讯')
    ,@('TDX 涨停文件', '通达信最新完整日线（20260909）')
    ,@('策略结果目录', 'data\strategy-results\reports\20260909_bottom_fishing_auto')
  )
})

[void]$tables.Add([ordered]@{
  title = '抄底策略原始交付物（a-share-bottom-fishing，trade_date=20260909）'
  columns = @('字段', '值')
  rows = @(
    ,@('schema', 'STOCK_CANONICAL_BUSINESS_RESULT_V1')
    ,@('skill_id', 'a-share-bottom-fishing')
    ,@('status', 'CLEAN_PASS')
    ,@('forecast_status', 'VALIDATED_SELECTION')
    ,@('selection_status', 'VALIDATED_SELECTION')
    ,@('trade_date', '20260909')
    ,@('candidate_count', '0')
    ,@('validator_evidence', 'validated=true；returncode=0；status=CLEAN_PASS；failure_count=0')
    ,@('business_process', 'returncode=0；timed_out=false；failure_tokens=[]；validation_errors=[]')
    ,@('business_binding.sha256', 'd3a18cadcffe6f76c34e7c6ef0d6826cedf095ee0c651d107e633360a4ad854c')
    ,@('artifacts', 'runs\20260910-134032-100222\business_child.stdout.txt / business_child.stderr.txt')
    ,@('STOCK_RUNTIME_RECEIPT', 'runtime=stock-canonical-runtime-v3；status=CLEAN_PASS；receipt_sha256=c15c05fb9160004734d9d77dfeaa27cf7932d30d6cfb29003b3b4d67b7742c7d')
    ,@('strategy_delivery', 'null')
  )
})

$cautions = @(
  '原始策略 a-share-bottom-fishing 在 trade_date=20260909 的 candidate_count=0，即本次没有任何入选标的、没有产生任何买卖信号；本报告不给出买入建议，也不得由 0 候选反推看空或看多个股。',
  '原始交付物 status=CLEAN_PASS 只表示流程与校验通过（validator returncode=0、business_process returncode=0、receipt 存在），不等于策略选中了标的，也不代表策略有效性已被验证。',
  '传入数据未提供策略逐股评分明细、公式输出明细、候选名单文件内容与 strategy_delivery 内容（strategy_delivery=null），因此无法复核策略为何 0 候选。',
  '跌停阈值候选（仅芒果超媒 300413，-9.94%）、前日涨停表现（previousDate=20260907，54 只）与盘中封板/炸板代理（date=20260908）均为本地日线 OHLC 推导候选，不是逐笔成交或交易所口径，不能提供首封时刻、封单额与盘口数据。',
  '盘中封板/炸板代理明确 dataFresh=false、lc5CurrentDateCount=0、lc5DateDistribution=20260904:2738，代理数据落后于行情数据日 20260909，且 firstSealTimeAvailable=false、orderBookAvailable=false。',
  'TDX 行业/主题成员聚合来自本地通达信映射（tdxhy.cfg + hy_tree1_total.xml、infoharbor_block.dat），属于通达信自定义行业/主题口径，不是交易所或申万官方行业分类事实；主题板块 updatedDate=20260904，晚于交易日 20260909，成分与聚合存在滞后。',
  '传入数据的日期锚点不一致：行情与策略数据日为 20260909，本地每日更新上下文 date=2026-09-10，公开行情快照为 2026-09-10 盘中（lianban 10 条、eastmoneyLimitUp 28 条），前日涨停表现 previousDate=20260907；这些不同日期口径不得混用或互相印证。',
  '龙虎榜与融资融券仅 adapter_only 且 snapshotExists=false，资金流公式为 formula_unavailable，新闻为 historical_catalog_only（latestEventDate=20260513、currentDateMatched=false）；当日席位、净买额、资金流方向与当日资讯均不可得，禁止据此推断资金方向。',
  '样本成交额 1873328634963 为样本合计口径，指数为收盘点位与涨跌幅摘要，均非交易所官方全市场统计，口径说明未提供。',
  '行情为跌多涨少结构（上涨 1786、下跌 3646、平盘 114，6 大指数全部收跌），策略在偏空结构中仍为 0 候选；本报告只做数据与状态汇报，不构成任何投资建议，也不预测下一交易日方向。'
)

$findings = @(
  [ordered]@{ title = '行情快照｜20260909 六大指数全部收跌'; text = '20260909 指数为：上证指数 3932.13（-0.49%）、深证成指 13617.82（-0.77%）、创业板指 3338.71（-0.48%）、科创50 1568.56（-0.73%）、上证50 2899.01（-0.39%）、北证50 1056.66（-2.32%），其中北证50 跌幅最大，深证成指次之，权重指数上证50 相对抗跌。' },
  [ordered]@{ title = '行情快照｜市场宽度跌多涨少'; text = '同日股票 5546 只中上涨 1786、下跌 3646、平盘 114，样本成交额 1873328634963 元；下跌家数约为上涨家数的两倍，属偏空宽度结构（平盘 114 家，口径说明未提供）。' },
  [ordered]@{ title = '行情快照｜涨幅领先候选以中小市值与题材股为主'; text = '涨幅领先候选前 20 条中靠前的为兆龙互连 300913（+14.72%，成交额 1733800832 元）、铜冠矿建 920019（+12.79%）、海目星 688559（+12.50%）、*ST天宜 688033（+12.20%）、中科海讯 300810（+11.59%），其中含 *ST天宜、*ST数源两只风险警示股。' },
  [ordered]@{ title = '行情快照｜成交额领先候选集中在光模块与通信'; text = '成交额领先候选前 20 条居前的为中际旭创 300308（18420918272 元，+0.72%）、东山精密 002384（16160062464 元，+5.17%）、亨通光电 600487（14492707840 元，+5.56%）、宁德时代 300750（12957469696 元，+0.40%）、新易盛 300502（12024950784 元，-0.38%），高成交额个股涨跌互现。' },
  [ordered]@{ title = '行情快照｜跌幅/负反馈候选与跌停推导'; text = '跌幅/负反馈候选前 20 条跌幅最大为芒果超媒 300413（-9.94%，成交额 3294277888 元），其后为联讯仪器 688808（-6.86%）、星网锐捷 002396（-4.07%）、摩尔线程 688795（-3.24%）、金健米业 600127（-3.11%）；跌停阈值候选（日线推导）仅 1 条，即芒果超媒 300413，-9.94%，收 18.57 元。' },
  [ordered]@{ title = '行情快照｜前日涨停表现（日线推导）'; text = '前日涨停表现（日线推导）给出 previousDate=20260907，前日涨停 54 只，其当日平均涨跌幅 +3.08%，上涨 36 只、下跌 17 只、平盘 1 只，涨停股当日整体为正收益，但该块为日线推导且与行情数据日 20260909 之间日期口径不一致。' },
  [ordered]@{ title = '公式/指标输出｜TDX 行业成员聚合 31 个板块'; text = 'TDX 行业板块聚合共 31 个。按平均涨跌幅居前的是石油（23 只，+4.31%，涨停 3 只）、煤炭（26 只，+2.95%，涨停 1 只）、传媒（48 只，+2.87%，涨停 4 只）、综合（12 只，+2.68%）、钢铁（26 只，+2.54%）；成员数最大的化工为 219 只、平均 +1.81%、涨停 8 只。该口径来自本地通达信行业映射（覆盖率 99.93%，映射 2736 只），非交易所或申万官方行业。' },
  [ordered]@{ title = '公式/指标输出｜TDX 主题成员聚合 40 个板块'; text = 'TDX 主题板块聚合共 40 个。按平均涨跌幅居前的是磷概念（23 只，+3.41%）、天然气（73 只，+2.74%）、土地流转（19 只，+2.72%）、AI营销（12 只，+2.10%）、黄金概念（47 只，+2.04%）、有机硅（21 只，+1.89%）；按成交额居前的是 5G概念（171897131476 元）、一带一路（159092456740 元）、含H股（156249951251 元）。主题板块 updatedDate=20260904，晚于交易日，属滞后映射。' },
  [ordered]@{ title = '公式/指标输出｜盘中封板/炸板代理（日线推导）'; text = '盘中封板/炸板代理（本地日线 OHLC 推导，非逐笔，date=20260908）：触板 71 只、收盘封板 42 只、触板后打开 29 只，封板率 59.15%、炸板率 40.85%；跌停侧触板 6 只、收盘封板 3 只、触板后打开 3 只，下封板率 50%。firstSealTimeAvailable=false、orderBookAvailable=false，lc5 文件 2738 个但日期分布为 20260904:2738、lc5CurrentDateCount=0、dataFresh=false，代理数据不新鲜。' },
  [ordered]@{ title = '公式/指标输出｜主线名称聚类候选 12 条'; text = '主线名称聚类候选共 12 条，标签均为“TDX主题成员聚合”：磷概念（23 只，+3.41%）、天然气（73 只，+2.74%）、土地流转（19 只，+2.72%）、AI营销（12 只，+2.10%）、黄金概念（47 只，+2.04%）、有机硅（21 只，+1.89%）、物业管理（122 只，+1.84%）、乡村振兴（165 只，+1.82%）、光热发电（18 只，+1.33%）、职业教育（40 只，+1.32%）、碳中和（105 只，+1.28%）、一带一路（365 只，+1.19%）。' },
  [ordered]@{ title = '子系统结论｜涨停/连板候选 30 条，最高 4 连板'; text = '涨停/连板候选（日线推导）30 条，连板数最高为百大集团 600865（+9.97%，涨停幅度 10%，4 连板，成交额 1038728576 元），其次为华脉科技 603042（+10.02%，2 连板）；其余 28 条均为 1 板，其中含 *ST天宜 688033、*ST数源 000909 两只涨停幅度 5% 的风险警示股。该表为日线推导候选，不含首封时刻与封单额。' },
  [ordered]@{ title = '子系统结论｜抄底策略原始交付物：CLEAN_PASS 且 0 候选'; text = 'a-share-bottom-fishing 原始交付物（schema=STOCK_CANONICAL_BUSINESS_RESULT_V1）显示 status=CLEAN_PASS、forecast_status=VALIDATED_SELECTION、selection_status=VALIDATED_SELECTION、trade_date=20260909、candidate_count=0；validator_evidence 为 validated=true/returncode=0/failure_count=0，business_process returncode=0、timed_out=false、failure_tokens 与 validation_errors 均为空，并附带 STOCK_RUNTIME_RECEIPT（status=CLEAN_PASS，receipt_sha256=c15c05fb9160004734d9d77dfeaa27cf7932d30d6cfb29003b3b4d67b7742c7d）；strategy_delivery 为 null。结论：流程校验通过但无任何候选，本次无抄底策略信号。' },
  [ordered]@{ title = '子系统结论｜数据源状态与新鲜度'; text = '行业映射 available（mappedStocks=2736，coveragePct=99.93%）、概念板块 available（boardCount=40）；盘中 intraday 状态 derived_ohlc（lc5Files=2738、lc5CurrentDateCount=0、firstSealTimeAvailable=false、orderBookAvailable=false）；融资融券与龙虎榜均为 adapter_only 且 snapshotExists=false；资金流 capitalFlow 为 formula_unavailable（注册公式：大牛线4.0/飞龙在天/游资资金监控/机构资金监控/庄家资金监控）；新闻 news 为 historical_catalog_only（latestEventDate=20260513、currentDateMatched=false）。' },
  [ordered]@{ title = '子系统结论｜本地每日更新上下文与 TDX 涨停文件'; text = '本地每日更新上下文 date=2026-09-10、generatedAt=2026-09-10T02:33:55.474Z，4 个补全步骤（通达信运行状态、新闻快讯补齐、公开行情补齐、通达信日线补齐）状态均为 completed、code 均为 0；公开行情快照 lianban=available/10 条、eastmoneyLimitUp=available/28 条、eastmoneyLhb=missing；新闻快照 available/100 条；TDX 涨停文件标注为“通达信最新完整日线（20260909）”。该上下文日期 2026-09-10 与本报告行情数据日 20260909 不是同一天，不可混用。' },
  [ordered]@{ title = '风险与后续观察｜无信号是本次最重要的结论'; text = '策略候选数为 0，因此不存在可跟踪的抄底标的，也不存在买点、止损位与仓位建议；任何由板块涨跌或涨停候选反推的个股买卖意见都超出传入数据范围，本报告不予给出。' },
  [ordered]@{ title = '风险与后续观察｜数据缺口与口径风险'; text = '当日龙虎榜与融资融券未落盘（snapshotExists=false）、资金流公式不可用、新闻为历史目录（最新事件 20260513），加上封板代理 dataFresh=false、主题映射 updatedDate=20260904，资金面与情绪面证据不足；同时样本成交额与指数为摘要口径、平盘家数口径未说明，跨日期锚点（20260907/20260908/20260909/2026-09-10）不得互相印证。' },
  [ordered]@{ title = '风险与后续观察｜后续观察要点'; text = '后续只需验证三点：一是下一交易日再跑 a-share-bottom-fishing 是否仍为 candidate_count=0（若仍为 0 则维持无信号结论）；二是 TDX 行业/主题聚合中石油、煤炭、传媒与磷概念、天然气等相对强势板块能否延续，以及涨停/连板候选最高高度（当前百大集团 4 连板）是否维持；三是本地数据新鲜度是否恢复（lc5 更新到当日、龙虎榜/融资融券快照落盘），以便补齐资金面证据后再评估。' }
)

$report = [ordered]@{
  status = 'CLEAN_PASS'
  summary = 'a-share-bottom-fishing「抄底策略」原始交付物显示：status=CLEAN_PASS，forecast_status/selection_status 均为 VALIDATED_SELECTION，validator 与 business_process 的 returncode 均为 0，但 trade_date=20260909 的 candidate_count=0，即本次没有任何入选标的、没有产出买卖信号，且 strategy_delivery 为 null。行情侧（数据日 20260909）为偏空结构：同日股票 5546 只中上涨 1786、下跌 3646、平盘 114，样本成交额 1873328634963 元，六大指数全部收跌（上证指数 3932.13/-0.49%、深证成指 13617.82/-0.77%、创业板指 3338.71/-0.48%、科创50 1568.56/-0.73%、上证50 2899.01/-0.39%、北证50 1056.66/-2.32%）。结构化候选方面：TDX 行业成员聚合 31 个板块中石油(+4.31%)、煤炭(+2.95%)、传媒(+2.87%)、钢铁(+2.54%)相对占优；TDX 主题成员聚合 40 个板块中磷概念(+3.41%)、天然气(+2.74%)、土地流转(+2.72%)、AI营销(+2.10%)、黄金概念(+2.04%)相对占优；涨停/连板候选 30 条，最高为百大集团(600865) 4 连板；跌停阈值候选（日线推导）仅芒果超媒(300413，-9.94%)1 条。以上榜单、板块聚合与涨停候选均为行情与派生候选，不等于抄底策略信号；因策略候选为 0，本报告不提供任何买入建议，相关缺口与推导口径均写入 cautions。'
  data_date = '20260909'
  data_scope = '数据日 20260909（本地通达信最新完整日线，另附 TDX 涨停文件标注“通达信最新完整日线（20260909）”）。范围包括：全市场同日股票 5546 只的涨跌家数、样本成交额与 6 大指数收盘摘要；网页可计算的涨幅领先候选 20 条、成交额领先候选 20 条、跌幅/负反馈候选 20 条、跌停阈值候选 1 条、前日涨停表现（日线推导，previousDate=20260907，54 只）；TDX 行业板块聚合 31 个、TDX 主题板块聚合 40 个、涨停/连板候选 30 条、主线名称聚类候选 12 条；盘中封板/炸板代理（日线 OHLC 推导，date=20260908）；数据源状态与新鲜度；本地每日更新上下文（date=2026-09-10，4 步骤 completed/code=0；lianban 10 条、eastmoneyLimitUp 28 条、eastmoneyLhb missing、新闻 100 条）；以及 a-share-bottom-fishing 原始策略交付物（trade_date=20260909，status=CLEAN_PASS，candidate_count=0）。未包含其余时间段的行情、外部抓取数据与未在传入摘要中出现的字段。'
  cautions = $cautions
  findings = $findings
  tables = @($tables)
}

$json = $report | ConvertTo-Json -Depth 12
$outFile = 'C:\work\260907 掌财智能体\CodeX-st-wsp\zhangcai-demo\data\harness\tasks\_task5_chunks\final_report.json'
[System.IO.File]::WriteAllText($outFile, $json, (New-Object System.Text.UTF8Encoding($false)))
"WROTE $outFile len=$($json.Length)"
$parsed = Get-Content -Raw -Encoding UTF8 $outFile | ConvertFrom-Json
"VALIDATE status=$($parsed.status) date=$($parsed.data_date) findings=$($parsed.findings.Count) tables=$($parsed.tables.Count) cautions=$($parsed.cautions.Count)"
$parsed.tables | ForEach-Object { "  table: $($_.title) cols=$($_.columns.Count) rows=$($_.rows.Count)" }
