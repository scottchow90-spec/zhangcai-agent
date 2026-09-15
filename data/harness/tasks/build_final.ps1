$ErrorActionPreference='Stop'
$p='C:\work\260907 掌财智能体\CodeX-st-wsp\zhangcai-demo\data\harness\tasks\task-e4be4ec7-c0ae-4aed-ac64-e8c36cdda3a7.txt'
$c=Get-Content -Raw -Path $p

function Get-JsonAt([string]$text,[string]$marker){
  $i=$text.IndexOf($marker); if($i -lt 0){return $null}
  $st=-1; for($k=$i;$k -lt $text.Length;$k++){ if($text[$k] -eq '[' -or $text[$k] -eq '{'){$st=$k;break} }
  $open=$text[$st]; $close= if($open -eq '{'){'}'}else{']'}
  $d=0;$inS=$false;$e=$false
  for($k=$st;$k -lt $text.Length;$k++){
    $ch=$text[$k]
    if($e){$e=$false;continue}
    if($ch -eq '\'){$e=$true;continue}
    if($ch -eq '"'){$inS=-not $inS;continue}
    if($inS){continue}
    if($ch -eq $open){$d++} elseif($ch -eq $close){$d--; if($d -eq 0){return $text.Substring($st,$k-$st+1)}}
  }
  return $null
}
function Y([object]$v){ [math]::Round([double]$v/1e8,2) }
function S([object]$v){ [string]$v }
function Mk([string[]]$a){ ,@($a) }   # single row

$up=(Get-JsonAt $c '涨幅领先候选：')|ConvertFrom-Json
$amt=(Get-JsonAt $c '成交额领先候选：')|ConvertFrom-Json
$dn=(Get-JsonAt $c '跌幅/负反馈候选：')|ConvertFrom-Json
$dt=(Get-JsonAt $c '跌停阈值候选：')|ConvertFrom-Json
$prev=(Get-JsonAt $c '前日涨停表现（日线推导）：')|ConvertFrom-Json
$ind=(Get-JsonAt $c 'TDX行业板块聚合：')|ConvertFrom-Json
$the=(Get-JsonAt $c 'TDX主题板块聚合：')|ConvertFrom-Json
$proxy=(Get-JsonAt $c '盘中封板/炸板代理（OHLC）：')|ConvertFrom-Json
$src=(Get-JsonAt $c '数据源状态与新鲜度：')|ConvertFrom-Json
$zt=(Get-JsonAt $c '涨停/连板候选：')|ConvertFrom-Json
$ml=(Get-JsonAt $c '主线名称聚类候选：')|ConvertFrom-Json
$sup=(Get-JsonAt $c '补充上下文：')|ConvertFrom-Json
$ctxRaw=(Get-JsonAt $c '本地每日更新上下文：')|ConvertFrom-Json

# ladder lookup
$lad=@{}
foreach($e in $sup.ladder){ $lad[$e.stock.code]=$e }

# ---------- tables ----------
$tables=New-Object System.Collections.Generic.List[object]

$tables.Add([ordered]@{ title='数据日期与市场宽度、指数（传入摘要）'; columns=@('项目','数值'); rows=@(
  (Mk @('数据日期','20260908')),
  (Mk @('同日股票数','2738')),
  (Mk @('上涨家数','1683')),
  (Mk @('下跌家数','996')),
  (Mk @('平盘家数','59')),
  (Mk @('上涨占比','61.47%（1683/2738）')),
  (Mk @('样本成交额','986583295755 元（约 9865.83 亿元）')),
  (Mk @('上证指数','3940.55（+0.2%）')),
  (Mk @('深证成指','13703.21（-0.52%）')),
  (Mk @('创业板指','3359.72（-1.15%）')),
  (Mk @('科创50','1591（-1.52%）')),
  (Mk @('上证50','2908.8（-0.1%）')),
  (Mk @('北证50','1086.25（-0.97%）'))
)})

$rows=@(); foreach($x in $up){ $rows+= ,@((S $x.code),(S $x.name),(S $x.pct),(S $x.close),(S (Y $x.amount)),(S $x.market)) }
$tables.Add([ordered]@{ title='涨幅领先候选（传入 20 条）'; columns=@('代码','名称','涨跌幅%','收盘价','成交额(亿元)','市场'); rows=$rows })

$rows=@(); foreach($x in $amt){ $rows+= ,@((S $x.code),(S $x.name),(S $x.pct),(S $x.close),(S (Y $x.amount)),(S $x.market)) }
$tables.Add([ordered]@{ title='成交额领先候选（传入 20 条）'; columns=@('代码','名称','涨跌幅%','收盘价','成交额(亿元)','市场'); rows=$rows })

$rows=@(); foreach($x in $dn){ $rows+= ,@((S $x.code),(S $x.name),(S $x.pct),(S $x.close),(S (Y $x.amount)),(S $x.market)) }
$tables.Add([ordered]@{ title='跌幅/负反馈候选（传入 20 条）'; columns=@('代码','名称','涨跌幅%','收盘价','成交额(亿元)','市场'); rows=$rows })

$rows=@(); foreach($x in $dt){ $rows+= ,@((S $x.code),(S $x.name),(S $x.pct),(S $x.close),(S (Y $x.amount)),(S $x.market)) }
$tables.Add([ordered]@{ title='跌停阈值候选（日线推导，非交易所披露）'; columns=@('代码','名称','涨跌幅%','收盘价','成交额(亿元)','市场'); rows=$rows })

$tables.Add([ordered]@{ title='前日涨停次日表现（20260907 涨停，日线推导）'; columns=@('项目','数值'); rows=@(
  (Mk @('前一日交易日','20260907')),
  (Mk @('前日涨停家数','54')),
  (Mk @('次日（20260908）平均涨跌幅','3.08%')),
  (Mk @('次日上涨家数','36')),
  (Mk @('次日下跌家数','17')),
  (Mk @('次日平盘家数','1')),
  (Mk @('名单（代码）', ($prev.codes -join ',')))
)})

$rows=@(); foreach($x in ($ind|Sort-Object avgPct -Descending)){
  $ld=($x.leaders|Select-Object -First 3|ForEach-Object{ (S $_.name) }) -join '、'
  $rows+= ,@((S $x.name),(S $x.count),(S $x.avgPct),(S (Y $x.amount)),("{0}/{1}/{2}" -f $x.up,$x.down,$x.flat),(S $x.limitCount),$ld)
}
$tables.Add([ordered]@{ title='TDX行业板块聚合（31 个，按平均涨跌幅降序；成员聚合映射，非官方行业分类）'; columns=@('行业','成分数','平均涨跌幅%','成交额(亿元)','上涨/下跌/平盘','涨停数','领涨前三'); rows=$rows })

$rows=@(); foreach($x in ($the|Sort-Object avgPct -Descending)){
  $ld=($x.leaders|Select-Object -First 3|ForEach-Object{ (S $_.name) }) -join '、'
  $rows+= ,@((S $x.name),(S $x.count),(S $x.avgPct),(S (Y $x.amount)),$ld)
}
$tables.Add([ordered]@{ title='TDX主题板块聚合（40 个，按平均涨跌幅降序；成员聚合映射，非官方概念分类）'; columns=@('主题','成分数','平均涨跌幅%','成交额(亿元)','领涨前三'); rows=$rows })

$rows=@(); foreach($x in $ml){ $rows+= ,@((S $x.name),(S $x.count),(S $x.avgPct),(S (Y $x.amount)),(($x.leaders|ForEach-Object{S $_}) -join '、')) }
$tables.Add([ordered]@{ title='主线名称聚类候选（12 条，TDX主题成员聚合）'; columns=@('主线','成分数','平均涨跌幅%','成交额(亿元)','领涨'); rows=$rows })

$rows=@(); foreach($x in $zt){
  $indName=''; $cum=''; $nh=''
  if($lad.ContainsKey($x.code)){
    $e=$lad[$x.code]; $st=$e.stock; $indName=S $st.industryName
    $cl=$st.history|ForEach-Object{$_.close}
    $first=[double]$cl[0]; $mx=[double](($cl|Measure-Object -Maximum).Maximum)
    $cum=S ([math]::Round(($st.close/$first-1)*100,1))+'%'
    $nh= if($st.close -ge $mx){'是'}else{'否'}
  }
  $rows+= ,@((S $x.code),(S $x.name),(S $x.pct),(S $x.streak),(S (Y $x.amount)),$indName,$cum,$nh)
}
$tables.Add([ordered]@{ title='涨停/连板候选（传入 30 条，含 TDX 行业与 30 日位置推导）'; columns=@('代码','名称','涨跌幅%','连板数','成交额(亿元)','TDX行业','30日累计涨幅','30日收盘新高'); rows=$rows })

$tables.Add([ordered]@{ title='盘中封板/炸板代理（日线 OHLC 推导，非逐笔）'; columns=@('项目','数值'); rows=@(
  (Mk @('日期', (S $proxy.date))),
  (Mk @('来源/方法', (S $proxy.source)+'；'+(S $proxy.method))),
  (Mk @('上摸涨停家数(upperHitCount)', (S $proxy.upperHitCount))),
  (Mk @('收盘封住涨停家数(upperClosedCount)', (S $proxy.upperClosedCount))),
  (Mk @('触板后打开家数(openedAfterHitCount)', (S $proxy.openedAfterHitCount))),
  (Mk @('代理封板率(sealRatePct)', (S $proxy.sealRatePct))),
  (Mk @('代理炸板率(explosionRatePct)', (S $proxy.explosionRatePct))),
  (Mk @('下摸跌停家数(lowerHitCount)', (S $proxy.lowerHitCount))),
  (Mk @('收盘封住跌停家数(lowerClosedCount)', (S $proxy.lowerClosedCount))),
  (Mk @('跌停触板后打开家数', (S $proxy.lowerOpenedAfterHitCount))),
  (Mk @('跌停代理封板率', (S $proxy.lowerSealRatePct))),
  (Mk @('首封时刻可得', (S $proxy.firstSealTimeAvailable))),
  (Mk @('封单/盘口可得', (S $proxy.orderBookAvailable))),
  (Mk @('lc5 文件数', (S $proxy.lc5Files))),
  (Mk @('lc5 日期分布', ($proxy.lc5DateDistribution.PSObject.Properties|ForEach-Object{ "$($_.Name):$($_.Value)" }) -join ',')),
  (Mk @('lc5 当日文件数', (S $proxy.lc5CurrentDateCount))),
  (Mk @('数据新鲜(dataFresh)', (S $proxy.dataFresh)))
)})

$rows=@()
$rows+= ,@('TDX行业映射',(S $src.industry.status),"映射股票 $(S $src.industry.mappedStocks) 只，覆盖 $(S $src.industry.coveragePct)%；映射文件 $(S $src.industry.mappingFile)；行业树 $(S $src.industry.captionFile)")
$rows+= ,@('概念板块',(S $src.conceptBoards.status),"板块数 $(S $src.conceptBoards.boardCount)；文件 $(S $src.conceptBoards.file)")
$rows+= ,@('盘中数据',(S $src.intraday.status),"lc5 文件 $(S $src.intraday.lc5Files)，当日文件 $(S $src.intraday.lc5CurrentDateCount)，首封时间可得 $(S $src.intraday.firstSealTimeAvailable)，盘口可得 $(S $src.intraday.orderBookAvailable)")
$rows+= ,@('融资融券',(S $src.financing.status),"快照文件存在 $(S $src.financing.snapshotExists)；配置 $(S $src.financing.configFile)")
$rows+= ,@('龙虎榜',(S $src.lhb.status),"快照文件存在 $(S $src.lhb.snapshotExists)；配置 $(S $src.lhb.configFile)")
$rows+= ,@('资金流公式',(S $src.capitalFlow.status),'注册公式：'+($src.capitalFlow.formulas -join '、'))
$rows+= ,@('新闻/公告事件',(S $src.news.status),"最新事件日期 $(S $src.news.latestEventDate)，当日匹配 $(S $src.news.currentDateMatched)，文件 $(S $src.news.file)")
$tables.Add([ordered]@{ title='数据源状态与新鲜度（传入）'; columns=@('数据域','状态','关键字段'); rows=$rows })

$rows=@()
foreach($s in $ctxRaw.steps){ $rows+= ,@((S $s.name),(S $s.script),(S $s.status),(S $s.code),(S $s.finishedAt)) }
$tables.Add([ordered]@{ title='本地每日补全步骤（上下文日期 2026-09-10，与本次数据日期不一致）'; columns=@('步骤','脚本','状态','退出码','完成时间(UTC)'); rows=$rows })

$pm=$ctxRaw.snapshots.publicMarket
$rows=@()
$rows+= ,@('lianban（连板网开放数据）',(S $pm.sources.lianban.status),(S $pm.sources.lianban.url),'记录数 '+(S $pm.sources.lianban.recordCount))
$rows+= ,@('eastmoneyLimitUp（东方财富涨停池）',(S $pm.sources.eastmoneyLimitUp.status),(S $pm.sources.eastmoneyLimitUp.url),'记录数 '+(S $pm.sources.eastmoneyLimitUp.recordCount))
$rows+= ,@('eastmoneyLhb（东方财富龙虎榜）',(S $pm.sources.eastmoneyLhb.status),'providerSuccess='+(S $pm.sources.eastmoneyLhb.providerSuccess)+'；'+(S $pm.sources.eastmoneyLhb.providerMessage),'记录数 '+[string]$pm.sources.eastmoneyLhb.recordCount)
$rows+= ,@('news（东方财富快讯）',(S $ctxRaw.snapshots.news.status),(S $ctxRaw.snapshots.news.source.url),'当日记录数 '+(S $ctxRaw.snapshots.news.sameDayRecordCount))
$rows+= ,@('marketBreadth（市场宽度，2026-09-10)',(S $pm.date),'同日 '+(S $pm.marketBreadth.currentCount)+'，涨 '+(S $pm.marketBreadth.up)+'，跌 '+(S $pm.marketBreadth.down)+'，涨停 '+(S $pm.marketBreadth.limitUp)+'，跌停 '+(S $pm.marketBreadth.limitDown)+'，连板 '+(S $pm.marketBreadth.lianban),'-')
$tables.Add([ordered]@{ title='本地每日上下文中的公开数据源与市场宽度（2026-09-10）'; columns=@('来源','状态','地址/说明','记录数'); rows=$rows })

$tables.Add([ordered]@{ title='本地 TDX 涨停文件与榜单覆盖'; columns=@('项目','数值'); rows=@(
  (Mk @('本地 TDX 涨停文件','ZTC.blk、FLZT.blk（传入仅给出文件名，未给出成分明细）')),
  (Mk @('TDX行业涨停数合计','42（31 个行业 limitCount 求和）')),
  (Mk @('盘中封板代理收盘封住涨停家数','42（与行业涨停数合计一致）')),
  (Mk @('涨停/连板候选条数','30（子集，非当日全部封板家数）')),
  (Mk @('前日涨停家数','54（20260907）'))
)})

# ---------- findings ----------
$findings=@(
 [ordered]@{title='指数与市场宽度方向不一致：权重/资源强、成长弱';text='传入指数为上证指数 3940.55（+0.2%）、上证50 2908.8（-0.1%）、深证成指 13703.21（-0.52%）、创业板指 3359.72（-1.15%）、科创50 1591（-1.52%）、北证50 1086.25（-0.97%）；同时同日 2738 只股票中上涨 1683、下跌 996、平盘 59（1683+996+59=2738，上涨占比 61.47%）。即个股层面偏多、权重指数微涨或走平，而创业板/科创/北证等成长指数收跌，呈结构性分化。'},
 [ordered]@{title='资源与周期行业领涨 TDX 行业榜';text='TDX 行业成员聚合中石油 +4.31%（23 只，22 涨 1 跌，涨停 3，成交 128.04 亿元）、煤炭 +2.95%（26 只，25 涨 1 跌，成交 109.18 亿元）、钢铁 +2.54%（26 只全涨）、综合 +2.68%；31 个行业中 27 个平均涨跌幅为正、4 个为负。领涨个股为华锦股份(+10.02%)、和顺石油(+10%)、中曼石油(+9.98%)、云煤能源(+10.1%)、陕西黑猫(+7.73%)。行业归属来自 TDX 成员聚合映射（tdxhy.cfg + hy_tree1_total.xml），不是交易所或申万官方分类。'},
 [ordered]@{title='主题层面磷概念、天然气、土地流转居前';text='TDX 主题成员聚合中磷概念 +3.41%（23 只，成交 218.66 亿元）、天然气 +2.74%（73 只，201.10 亿元）、土地流转 +2.72%（19 只，77.41 亿元）、AI营销 +2.10%（12 只）、黄金概念 +2.04%（47 只，502.99 亿元）、有机硅 +1.89%（21 只）。成交额最大的主题为 5G概念 1718.97 亿元、一带一路 1590.92 亿元、含H股 1562.50 亿元、锂电池 1410.11 亿元、DeepSeek 1361.87 亿元（40 个主题，价格与成交额均为成员聚合口径）。'},
 [ordered]@{title='传媒/出版链是当日最连贯的方向';text='TDX 传媒行业平均 +2.87%（48 只中 45 涨 3 跌，涨停 4，成交 164.99 亿元），领涨出版传媒(+10.01%)、上海电影(+9.99%)、中国出版(+9.98%)、读者传媒(+9.95%)、龙版传媒(+9.12%)。涨停候选表中传媒/出版相关有中国出版(3 连板)、上海电影(2 连板)、读者传媒(2 连板)、出版传媒(首板)，另有博瑞传播(+10.1%，TDX 教育培训)与相关主题 AI营销 +2.10%。'},
 [ordered]@{title='涨停梯队与延续性：最高 4 连板，前日涨停次日平均 +3.08%';text='传入涨停/连板候选 30 条，连板分布为 4 板 2 家（百大集团 600865、亚盛集团 600108）、3 板 2 家（中国出版 601949、敦煌种业 600354）、2 板 6 家（华体科技、科森科技、上海电影、百合花、华脉科技、读者传媒）、首板 20 家。前日（20260907）涨停 54 只，次日平均涨跌幅 +3.08%，涨 36、跌 17、平 1，其中 10 只仍出现在当日涨停候选中（亚盛集团、敦煌种业、百大集团、上海电影、中国出版、华脉科技、科森科技、华体科技、百合花、读者传媒）。上述延续性与连板数均为日线推导口径。'},
 [ordered]@{title='封板强度中等偏弱，炸板比例偏高（日线代理）';text='盘中封板/炸板代理（本地日线 OHLC 估算，非逐笔）显示：上摸涨停 71 家、收盘封住 42 家、触板后打开 29 家，代理封板率 59.15%、代理炸板率 40.85%；跌停方向下摸 6 家、收盘封住 3 家、打开 3 家，跌停代理封板率 50%。31 个 TDX 行业的 limitCount 合计 42，与代理中收盘封住 42 家互相印证。该口径不提供首封时刻与封单额（firstSealTimeAvailable=false、orderBookAvailable=false）。'},
 [ordered]@{title='高位科技股放量分歧，成交额集中但涨跌互现';text='成交额领先候选中兆易创新 146.06 亿元(+0.13%)、长鑫科技 115.66 亿元(-0.14%)、剑桥科技 109.45 亿元(+7.28%)、生益科技 102.48 亿元(-1.26%)、亨通光电 96.97 亿元(-1.39%)、寒武纪 92.89 亿元(-3.06%)；同时 TDX 电子行业平均 -0.98%（275 只中 62 涨 210 跌 3 平）、计算机 -0.52%（132 只中 51 涨 76 跌 5 平）、通信 +0.48%（46 只中 24 涨 22 跌）。即高成交额标的集中在电子/通信，但内部涨跌分化、权重成交股多为下跌或微涨。'},
 [ordered]@{title='强势股位置普遍偏高：30 只涨停候选有 23 只创 30 日收盘新高';text='按传入 30 只个股 30 个交易日历史（20260729-20260908）计算，23 只当日收盘价不低于其 30 日收盘最高值，7 只未创新高（百合花、亚泰集团、深华发Ａ、东亚药业、艾艾精工、圣晖集成、三孚股份）。30 日累计涨幅前列为香江控股 +109.1%、金牛化工 +94.0%、敦煌种业 +80.4%、亚盛集团 +74.8%、科森科技 +65.1%。该位置指标为传入日线数据推导，不构成任何操作建议。'},
 [ordered]@{title='负反馈名单与跌停候选结构';text='跌幅/负反馈候选中新炬网络 -9.32%、思看科技 -9.19%、大禹生物 -8.18%、长盈通 -7.28%、金海高科 -6.98%、星环科技 -6.79%、哈森股份 -6.65%、高凯技术 -6.58%。跌停阈值候选仅 3 只且全部为 ST 类：*ST沐邦 -6.55%、*ST清越 -5.21%、*ST联翔 -4.76%，与代理口径下收盘封住跌停 3 家一致；该候选由日线阈值推导，不是交易所跌停披露。'},
 [ordered]@{title='主线名称聚类给出 12 条候选主线';text='传入主线名称聚类候选 12 条，居前为磷概念（23 只，+3.41%，218.66 亿元）、天然气（73 只，+2.74%，201.10 亿元）、土地流转（19 只，+2.72%，77.41 亿元）、AI营销（12 只，+2.10%）、黄金概念（47 只，+2.04%）、有机硅（21 只，+1.89%）、物业管理（122 只，+1.84%）、乡村振兴（165 只，+1.82%）；并注明本地 TDX 涨停文件为 ZTC.blk 与 FLZT.blk（未传入成分明细，无法与候选表逐条核对）。'},
 [ordered]@{title='当日证据链缺口集中于资金面与消息面';text='数据源状态显示：龙虎榜与融资融券均为 adapter_only 且快照文件不存在（snapshotExists=false）；资金流公式为 formula_unavailable（大牛线4.0、飞龙在天、游资资金监控、机构资金监控、庄家资金监控均未传入结果）；新闻/事件为 historical_catalog_only，latestEventDate=20260513、currentDateMatched=false；盘中 lc5 文件 2738 个但日期分布仅 20260904、当日文件数 0、dataFresh=false。因此本次不给出资金方向、龙虎榜、融资余额与消息面结论。'}
)

$cautions=@(
 '龙虎榜（lhb）状态为 adapter_only 且 snapshotExists=false，传入数据不含当日席位与净买额，禁止据此推断资金方向。',
 '融资融券（financing）同为 adapter_only、快照不存在；资金流公式状态为 formula_unavailable，大牛线4.0、飞龙在天、游资资金监控、机构资金监控、庄家资金监控的结果均未传入。',
 '盘中数据为 derived_ohlc：lc5 文件数 2738，但 lc5DateDistribution 仅 20260904、lc5CurrentDateCount=0、dataFresh=false，且 firstSealTimeAvailable=false、orderBookAvailable=false，无首封时刻与封单额。',
 '跌停阈值候选、前日涨停表现（20260907→20260908）与盘中封板/炸板率均由日线 OHLC 推导（方法字段已明示），属推导候选，不等于交易所披露事实，不得当作封板质量或跌停事实的定论。',
 'TDX 行业/主题板块为成员聚合映射（tdxhy.cfg + hy_tree1_total.xml、infoharbor_block.dat，行业覆盖 2736 只、99.93%），可用于结构化候选，但不能当作交易所或申万官方行业分类事实。',
 '涨停/连板候选仅 30 条，而盘中封板代理显示当日收盘封住涨停 42 家（与 31 个行业 limitCount 合计 42 一致），候选表为子集，涨停家数不得直接等同于候选表条数。',
 '前日涨停名单仅传入 54 个代码，未传入其个股级涨跌幅明细，只能引用 count=54、todayAvgPct=3.08、todayUp=36、todayDown=17、todayFlat=1 等汇总值。',
 '新闻/事件源为 historical_catalog_only（latestEventDate=20260513，currentDateMatched=false），本次无当日新闻或事件证据，不得虚构消息面。',
 '本地每日更新上下文日期为 2026-09-10（generatedAt 2026-09-10T02:33:55.474Z），与本次数据日期 20260908 不一致；该上下文内嵌的旧运行输出声称指数与多个榜单“未提供”，那是针对另一交易日的判断，不适用于本次已传入的榜单。',
 '未提供项：交易所/申万官方行业分类、指数成分与成交额口径说明、涨跌家数口径说明、连板口径定义、个股上市天数与是否含新股/次新、龙虎榜、融资融券、北向资金。',
 '样本成交额 986583295755 元为传入样本口径，未提供其与全市场成交额的换算或口径说明。',
 '涨幅领先候选未提供 limitPct 字段（涨停/连板候选提供 limitPct=10），两者涨跌幅限制口径无法直接对齐；榜单同时包含北交所（920371、920786）与科创板（688 开头）标的。',
 '本回复仅基于传入的本地通达信摘要与公开快照元数据，未读取文件、未访问网络、未重新抓取，所有 sha256 与时间戳均为引用值，未做独立复核。',
 '按要求不给出任何买卖建议，全部内容仅为当日数据的结构化复盘。'
)

$result=[ordered]@{
  status='partial'
  summary=('20260908 传入本地通达信摘要复盘：同日 2738 只中上涨 1683、下跌 996、平盘 59（上涨占比 61.47%），样本成交额 9865.83 亿元；指数分化，上证指数 3940.55（+0.2%）微涨，深证成指 -0.52%、创业板指 -1.15%、科创50 -1.52%、北证50 -0.97% 收跌。TDX 行业成员聚合中石油 +4.31%、煤炭 +2.95%、传媒 +2.87% 领涨，31 个行业中 27 个为正；TDX 主题中磷概念 +3.41%、天然气 +2.74%、土地流转 +2.72% 居前。涨停/连板候选 30 条，最高 4 连板（百大集团、亚盛集团），3 连板 2 家（中国出版、敦煌种业），2 连板 6 家，首板 20 家；前日（20260907）涨停 54 只次日平均 +3.08%（涨 36、跌 17、平 1）。日线 OHLC 代理显示上摸涨停 71 家、收盘封住 42 家、触板后打开 29 家，代理封板率 59.15%、炸板率 40.85%；跌停方向下摸 6 家、收盘封住 3 家。成交额集中但分化，兆易创新 146.06 亿元、长鑫科技 115.66 亿元居前，电子行业平均 -0.98%（275 只中 210 跌）。龙虎榜、融资融券、资金流公式与当日新闻均不可用，相关结论缺失。')
  data_date='20260908'
  data_scope='传入的本地通达信摘要（data\harness\tasks 任务载荷）覆盖：20260908 市场宽度与指数、涨幅/成交额/跌幅负反馈候选各 20 条、跌停阈值候选 3 条、前日涨停表现（日线推导）、TDX 行业板块聚合 31 个、TDX 主题板块聚合 40 个、盘中封板/炸板代理（OHLC）、数据源状态与新鲜度、涨停/连板候选 30 条、主线名称聚类候选 12 条、本地每日更新上下文（日期 2026-09-10）以及补充上下文中的 12 条主题与 30 只个股 30 个交易日（20260729-20260908）日线明细。未读取本地文件、未访问网络、未重新抓取。'
  cautions=$cautions
  findings=$findings
  tables=$tables
}

$json=$result|ConvertTo-Json -Depth 8
$outp='C:\work\260907 掌财智能体\CodeX-st-wsp\zhangcai-demo\data\harness\tasks\_final.json'
[System.IO.File]::WriteAllText($outp,$json,[System.Text.UTF8Encoding]::new($false))
"written bytes: $((Get-Item $outp).Length)"
try{ $null=$json|ConvertFrom-Json; "json valid" }catch{ "json invalid: $_" }
