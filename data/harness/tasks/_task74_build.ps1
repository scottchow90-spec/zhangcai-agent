$ErrorActionPreference = 'Stop'
$src = 'C:\work\260907 掌财智能体\CodeX-st-wsp\zhangcai-demo\data\harness\tasks\_task74_pretty.txt'
$L = Get-Content $src
$up  = $L[1]  | ConvertFrom-Json
$amt = $L[3]  | ConvertFrom-Json
$dn  = $L[5]  | ConvertFrom-Json
$dt  = $L[7]  | ConvertFrom-Json
$prev = ((($L[8] -replace '^前日涨停表现（日线推导）：','') -split ' TDX行业板块聚合')[0]) | ConvertFrom-Json
$ind = $L[9]  | ConvertFrom-Json
$th  = $L[11] | ConvertFrom-Json
$seal = ($L[12] -replace '^盘中封板/炸板代理（OHLC）：','') -replace ' 数据源状态与新鲜度：.*$',''
$seal = $seal | ConvertFrom-Json
$lu  = $L[13] | ConvertFrom-Json
$cl  = $L[15] | ConvertFrom-Json

# derived stats
$stCount = ($lu | Where-Object { $_.name -like '*ST*' }).Count
$luTop = $lu | Sort-Object amount -Descending | Select-Object -First 3
$amtDnOverlap = ($amt | Where-Object { $c = $_.code; ($dn | Where-Object { $_.code -eq $c }).Count -gt 0 })
$indTop = $ind | Sort-Object avgPct -Descending | Select-Object -First 5
$indBot = $ind | Where-Object { $_.code -ne 'UNKNOWN' } | Sort-Object avgPct | Select-Object -First 5
$thTop = $th | Sort-Object avgPct -Descending | Select-Object -First 5
$thBot = $th | Sort-Object avgPct | Select-Object -First 5
$ratio = [Math]::Round(949/4514, 2)

function S($v) { [string]$v }

$t1 = @()
$t1 += ,@('数据日期','20260910','本地通达信摘要口径')
$t1 += ,@('同日股票数','5544','上涨949 / 下跌4514 / 平盘81')
$t1 += ,@('样本成交额(元)','1660527553460','摘要样本口径')
$t1 += ,@('上证指数','3934.4 (-0.43%)','—')
$t1 += ,@('深证成指','13617.67 (-0.77%)','—')
$t1 += ,@('创业板指','3338.42 (-0.49%)','—')
$t1 += ,@('科创50','1569.22 (-0.69%)','—')
$t1 += ,@('上证50','2904.29 (-0.21%)','—')
$t1 += ,@('北证50','1051.41 (-2.81%)','—')

$t2 = @(); foreach ($r in $up)  { $t2 += ,@($r.code,$r.name,[string]$r.pct,[string]$r.close,[string]$r.amount,$r.market) }
$t3 = @(); foreach ($r in $amt) { $t3 += ,@($r.code,$r.name,[string]$r.amount,[string]$r.pct,[string]$r.close) }
$t4 = @(); foreach ($r in $dn)  { $t4 += ,@($r.code,$r.name,[string]$r.pct,[string]$r.close,[string]$r.amount) }
$t5 = @(); foreach ($r in $dt)  { $t5 += ,@($r.code,$r.name,[string]$r.pct,[string]$r.amount,'日线涨跌停阈值推导，非交易所事实') }

$t6 = @()
foreach ($r in ($ind | Sort-Object avgPct -Descending)) {
  $t6 += ,@($r.code,$r.name,[string]$r.count,[string]$r.avgPct,"$($r.up)/$($r.down)/$($r.flat)",[string]$r.limitCount,[string]$r.amount)
}

$t7 = @()
foreach ($r in ($th | Sort-Object avgPct -Descending | Select-Object -First 15)) {
  $t7 += ,@($r.code,$r.name,"$($r.count)/$($r.declaredCount)",[string]$r.avgPct,"$($r.up)/$($r.down)",[string]$r.limitCount,[string]$r.amount)
}
$t8 = @()
foreach ($r in ($th | Sort-Object avgPct | Select-Object -First 8)) {
  $t8 += ,@($r.code,$r.name,"$($r.count)/$($r.declaredCount)",[string]$r.avgPct,"$($r.up)/$($r.down)",[string]$r.limitCount,[string]$r.amount)
}

$t9 = @(); foreach ($r in $lu) { $t9 += ,@($r.code,$r.name,[string]$r.pct,[string]$r.limitPct,[string]$r.streak,[string]$r.amount) }
$t10 = @(); foreach ($r in $cl) { $t10 += ,@($r.name,[string]$r.count,[string]$r.avgPct,[string]$r.amount,($r.leaders -join '、')) }

$t11 = @(
 ,@('推导的前一日交易日',[string]$prev.previousDate,'前日涨停表现口径日期')
 ,@('前日涨停只数',[string]$prev.count,'共54个代码')
 ,@('当日平均涨跌幅%',[string]$prev.todayAvgPct,'对54只前日涨停股的当日均值')
 ,@('上涨/下跌/平盘','36/17/1','36+17+1=54，自洽')
)
$t12 = @(
 ,@('代理日期',[string]$seal.date,'摘要标注的OHLC代理日期，非20260910')
 ,@('触板(high触及上限)只数',[string]$seal.upperHitCount,'日线OHLC推导')
 ,@('收盘封板只数',[string]$seal.upperClosedCount,'以收盘收于阈值估算')
 ,@('触板后打开只数',[string]$seal.openedAfterHitCount,'日线OHLC推导')
 ,@('封板率%',[string]$seal.sealRatePct,'OHLC代理口径，非逐笔')
 ,@('炸板率%',[string]$seal.explosionRatePct,'OHLC代理口径')
 ,@('跌停触板/收盘/打开','6/3/3','日线OHLC推导')
 ,@('首封时刻/封单额可用性','false/false','不提供首封时刻与封单额')
 ,@('lc5分时文件(日期)','2738 (20260904)','lc5CurrentDateCount=0')
 ,@('数据新鲜度','dataFresh=false','不能代表20260910当日')
)
$t13 = @(
 ,@('TDX行业映射','available','mappedStocks=2736，coveragePct=99.93，tdxhy.cfg + hy_tree1_total.xml')
 ,@('TDX主题板块','available','infoharbor_block.dat，boardCount=40')
 ,@('盘中/分时','derived_ohlc','lc5Files=2738，lc5CurrentDateCount=0，firstSealTimeAvailable=false，orderBookAvailable=false')
 ,@('两融','adapter_only','快照文件不存在(snapshotExists=false)')
 ,@('龙虎榜','adapter_only','快照文件不存在(snapshotExists=false)')
 ,@('资金流公式','formula_unavailable','公式注册表可见大牛线4.0/飞龙在天/游资资金监控/机构资金监控/庄家资金监控')
 ,@('新闻','historical_catalog_only','speczsevent.txt，latestEventDate=20260513，currentDateMatched=false')
)

$report = [ordered]@{
  status = 'ok'
  summary = "2026-09-10 A股短线情绪判断：偏弱（结构性分化）。指数普跌（上证3934.4 -0.43%、深证13617.67 -0.77%、创业板3338.42 -0.49%、科创50 1569.22 -0.69%、上证50 2904.29 -0.21%、北证50 1051.41 -2.81%），市场宽度显著偏空（同日股票5544，上涨949、下跌4514、平盘81，涨跌家数比约$ratio），样本成交额1.66万亿元；结构上并未全线熄火：TDX行业成员聚合中石油(+4.31%)、煤炭(+2.95%)、传媒(+2.87%)、钢铁(+2.54%)居前，电子(-0.98%)、计算机(-0.52%)垫底；TDX主题聚合中磷概念(+3.41%)、天然气(+2.74%)、土地流转(+2.72%)领先，5G概念(+0.21%)、算力租赁(+0.22%)、东数西算(+0.26%)、光伏(+0.27%)、AI智能体(+0.28%)等前期热门方向垫底；涨停候选30条连板数全为1（首板候选），其中ST类5条；成交额前20中中际旭创(154.9亿,-2.07%)、天孚通信(138.0亿,+4.25%)、东山精密(109.1亿,-1.18%)居前，多只高成交额通信/电子股同时出现在跌幅候选。反向证据：前一交易日(20260907)的54只涨停股在20260910平均+3.08%、36涨17跌1平，说明局部赚钱效应未完全消失。跌停、前日涨停表现、盘中封板率均为日线推导候选，非交易所或逐笔事实。"
  data_date = '20260910'
  data_scope = '仅使用网页传入的本地通达信摘要（数据日期20260910）：全市场同日宽度统计(5544只：949涨/4514跌/81平)与六大指数收盘、样本成交额；涨幅/成交额/跌幅领先候选各20条；跌停阈值候选；前日涨停表现(日线推导)；TDX行业成员聚合31条；TDX主题板块聚合40条；盘中封板/炸板代理(OHLC代理，日期20260908)；涨停/连板候选30条；主线名称聚类候选12条；数据源状态与新鲜度；TDX涨停文件(通达信最新完整日线20260910)及本地每日更新上下文中的源状态字段。未使用八站舆情原文、龙虎榜席位明细、两融、新闻正文、分时与实时行情，未做任何外部取数或推算。'
  cautions = @(
    '仅使用网页传入的本地通达信摘要，未做任何外部取数或补造；数据源状态显示龙虎榜与两融为adapter_only且快照不存在(snapshotExists=false)、资金流公式formula_unavailable、新闻为historical_catalog_only(latestEventDate=20260513、currentDateMatched=false)，因此本报告不含龙虎榜、两融、资金流公式与当日新闻证据。'
    '短线情绪判断为偏弱（结构性分化），置信度中等：指数与市场宽度一致偏空，但前日涨停股当日平均+3.08%、行业/主题存在明确上涨结构，属冲突证据；按要求未生成加权总分，仅作定性阶段判断。'
    '中级周期（多日连板晋级序列、连续晋级率）无法判定：摘要只提供候选表与前一交易日涨停表现，没有连续多日连板梯队数据。'
    '跌停阈值候选表仅返回1条(600737中粮糖业 -10%)，为日线涨跌停阈值推导，不能据此推断全市场跌停家数或跌停结构。'
    '前日涨停表现(previousDate=20260907、count=54、todayAvgPct=3.08、36涨/17跌/1平)为日线推导，非交易所或官方连板梯队数据。'
    '盘中封板/炸板代理的日期为20260908而不是20260910，且dataFresh=false、lc5CurrentDateCount=0、lc5DateDistribution=20260904(2738)、firstSealTimeAvailable=false、orderBookAvailable=false，因此upperHitCount=71、upperClosedCount=42、sealRatePct=59.15、explosionRatePct=40.85只能作为该代理日的历史参考，绝不能当作20260910当日封板率、炸板率或首封时刻证据。'
    'TDX行业/主题成员聚合是本地通达信映射(industry: tdxhy.cfg + hy_tree1_total.xml，mappedStocks=2736、coveragePct=99.93；conceptBoards: infoharbor_block.dat、boardCount=40)，不是交易所或申万官方行业事实。'
    'TDX行业/主题聚合的leaders字段与该日候选表存在同日冲突：600737中粮糖业在乡村振兴leaders中为+9.99%、收18.16，而在跌幅候选与跌停阈值候选中为-10%、收17.82；600108亚盛集团在土地流转/乡村振兴leaders中为+10%、收5.28，而在跌幅候选中为-8.06%、收5.25。该快照的实际交易日无法由本摘要确认，不得把leaders涨跌幅当作20260910个股事实。'
    '主题聚合覆盖成员数小于声明成员数（如磷概念23/59、天然气73/145、土地流转19/37、AI营销12/44），主题平均涨跌幅与成交额只代表已覆盖成员；行业聚合含UNKNOWN(未分类，2只，avgPct -0.91)。'
    '涨幅/成交额/跌幅领先候选各为20条上限样本，涨停/连板候选为30条候选，均非全市场完整榜单；30条涨停候选的连板数(streak)全为1，未见连板梯队，不能据此得出连板晋级率或最高板结论。'
    '样本成交额1660527553460元为摘要样本口径，与全市场成交额口径可能不一致，引用时须注明口径。'
    '涨停候选表未覆盖全部涨停个股（例如行业/主题leaders中出现的600691潞化科技+10.16%、600596新安股份+10.02%、603077和邦生物+10%等未进入30条候选表），两表口径不同不可合并计数。'
    '涨停候选表的limitPct字段存在口径冲突：ST类5条(300290 ST荣科+18.31%、300010 ST豆神+11.62%、600491 ST龙元+10.19%、002514 *ST宝馨+10.05%、002856 *ST美芝+10.00%)均标注limitPct=5%，其中创业板ST实际涨跌幅限制为20%、主板ST为5%，无法与该字段自洽；因此不得用limitPct判定板性、封板或连板结论，仅可引用其涨跌幅与成交额。'
    '本报告为收盘后数据复盘，不构成任何买卖建议。'
  )
  findings = @(
    [ordered]@{ title='市场宽度与指数：普跌格局'; text="同日股票5544只中上涨949只、下跌4514只、平盘81只，涨跌家数比约$ratio；六大指数全部收跌：上证指数3934.4(-0.43%)、深证成指13617.67(-0.77%)、创业板指3338.42(-0.49%)、科创50 1569.22(-0.69%)、上证50 2904.29(-0.21%)、北证50 1051.41(-2.81%)，其中北证50跌幅最大。样本成交额1660527553460元（约1.66万亿元）。宽度与指数方向一致，构成偏弱判断的主要依据。" }
    [ordered]@{ title='短线情绪判断：偏弱（结构性分化），含反证'; text='根据本地通达信摘要的五维事实（涨停候选、连板结构、热点扩散、成交额、市场宽度）与指数：宽度949涨/4514跌、指数普跌，判定短线情绪为偏弱；但结构未全面熄火——TDX行业聚合中石油+4.31%、煤炭+2.95%、传媒+2.87%、钢铁+2.54%为上涨行业，且前一日(20260907)54只涨停股在20260910平均+3.08%、36涨17跌1平。正向与反向证据并存，按要求登记为冲突，不做平均抵消，也不给加权总分。' }
    [ordered]@{ title='行业结构：能源与周期领先，电子计算机垫底'; text=("TDX行业成员聚合(31条)按平均涨跌幅排序居前为：" + (($indTop | ForEach-Object { "$($_.name)+$($_.avgPct)%(成员$($_.count)、涨$($_.up)/跌$($_.down)、涨停$($_.limitCount))" }) -join '；') + "。垫底为：" + (($indBot | ForEach-Object { "$($_.name)$($_.avgPct)%(成员$($_.count)、涨$($_.up)/跌$($_.down))" }) -join '；') + "。电子行业成交额267064371654元为全部行业最高但平均-0.98%、涨62/跌210，呈量价背离。该映射为本地通达信行业口径。") }
    [ordered]@{ title='主题结构：磷化工、天然气、土地流转领先；算力/5G/光伏/AI垫底'; text=("TDX主题板块聚合(40条)居前为：" + (($thTop | ForEach-Object { "$($_.name)+$($_.avgPct)%(覆盖$($_.count)/$($_.declaredCount)、涨停$($_.limitCount))" }) -join '；') + "。垫底为：" + (($thBot | ForEach-Object { "$($_.name)+$($_.avgPct)%(覆盖$($_.count)/$($_.declaredCount))" }) -join '；') + "。涨停家数最多的主题为乡村振兴(8只)、一带一路(6只)、ST板块(5只)、物业管理(5只)、天然气(4只)、锂电池(4只)、光伏(4只)、DeepSeek(4只)。涨停家数集中在农业/乡村振兴、一带一路、物业管理等低位方向。") }
    [ordered]@{ title='成交额结构：光模块与电子链高换手且分化'; text=("成交额领先候选前五为：" + (($amt | Select-Object -First 5 | ForEach-Object { "$($_.name)$([Math]::Round($_.amount/100000000,1))亿元($($_.pct)%)" }) -join '；') + "。成交额前20中同时进入跌幅候选的有：" + (($amtDnOverlap | ForEach-Object { "$($_.name)($($_.pct)%)" }) -join '、') + "。高成交额集中在通信/电子/光模块链，但同板块内方向分化明显：天孚通信、剑桥科技等上涨，中际旭创、亨通光电、华工科技等下跌。") }
    [ordered]@{ title='涨停候选与首板结构'; text=("涨停/连板候选共$($lu.Count)条，连板数(streak)全部为1，即全部为首板候选；其中ST类$($stCount)条（ST荣科、ST豆神、ST龙元、*ST宝馨、*ST美芝）；候选表标注的涨停幅度限制为5%(ST)与10%两档，创业板ST荣科+18.31%、逸豪新材+15.29%为涨幅候选前两位；但ST类5条的limitPct字段标注为5%，与其实际涨跌幅(ST荣科+18.31%、ST豆神+11.62%、ST龙元+10.19%、*ST宝馨+10.05%、*ST美芝+10.00%)不一致，该字段口径存疑。候选成交额居前为：" + (($luTop | ForEach-Object { "$($_.name)$([Math]::Round($_.amount/100000000,1))亿元" }) -join '、') + "。该表为候选口径，未覆盖全部涨停个股，且无连板梯队，不能用于晋级率结论。") }
    [ordered]@{ title='负反馈与跌停推导'; text=("跌幅/负反馈候选20条居前为：" + (($dn | Select-Object -First 6 | ForEach-Object { "$($_.name)$($_.pct)%(收$($_.close))" }) -join '；') + "。跌停阈值候选仅600737中粮糖业(-10%，成交额3681396224元，收17.82)。该跌停结论为日线阈值推导，且中粮糖业同时出现在乡村振兴主题leaders(+9.99%)中，存在跨表日期冲突，已列入cautions。") }
    [ordered]@{ title='前日涨停表现与赚钱效应（日线推导）'; text="前一交易日20260907共54只涨停股，在20260910平均涨跌幅+3.08%，其中36只上涨、17只下跌、1只平盘(36+17+1=54)；代码清单与前日涨停记录一致。该口径为日线推导，说明前一交易日涨停股次日整体仍取得正收益，是偏弱判断下的正向反证。" }
    [ordered]@{ title='数据新鲜度与可用性边界'; text='行业与主题映射available(覆盖率99.93%/40个主题板块)；盘中/分时仅derived_ohlc且lc5CurrentDateCount=0、dataFresh=false；两融与龙虎榜均adapter_only且快照文件不存在；资金流公式formula_unavailable；新闻historical_catalog_only(最新事件20260513)。因此本报告只能支撑收盘后结构性复盘，不能支撑席位资金、杠杆资金、分时封板与当日新闻驱动的结论。' }
  )
  tables = @(
    [ordered]@{ title='指数与市场宽度（20260910）'; columns=@('项目','数值','备注'); rows=$t1 }
    [ordered]@{ title='涨幅领先候选（20条上限样本）'; columns=@('代码','名称','涨跌幅%','收盘价','成交额(元)','市场'); rows=$t2 }
    [ordered]@{ title='成交额领先候选（20条上限样本）'; columns=@('代码','名称','成交额(元)','涨跌幅%','收盘价'); rows=$t3 }
    [ordered]@{ title='跌幅/负反馈候选（20条上限样本）'; columns=@('代码','名称','涨跌幅%','收盘价','成交额(元)'); rows=$t4 }
    [ordered]@{ title='跌停阈值候选（日线推导）'; columns=@('代码','名称','涨跌幅%','成交额(元)','口径'); rows=$t5 }
    [ordered]@{ title='TDX行业成员聚合（31条，按平均涨跌幅降序）'; columns=@('行业代码','行业','成员数','平均涨跌幅%','涨/跌/平','涨停数','成交额(元)'); rows=$t6 }
    [ordered]@{ title='TDX主题板块聚合（按平均涨跌幅降序前15）'; columns=@('主题代码','主题','覆盖/声明成员','平均涨跌幅%','涨/跌','涨停数','成交额(元)'); rows=$t7 }
    [ordered]@{ title='TDX主题板块聚合（平均涨跌幅垫底8条）'; columns=@('主题代码','主题','覆盖/声明成员','平均涨跌幅%','涨/跌','涨停数','成交额(元)'); rows=$t8 }
    [ordered]@{ title='涨停/连板候选（30条，连板数均为1）'; columns=@('代码','名称','涨跌幅%','涨停幅度限制%','连板数','成交额(元)'); rows=$t9 }
    [ordered]@{ title='主线名称聚类候选（12条）'; columns=@('主线','成员数','平均涨跌幅%','成交额(元)','代表个股'); rows=$t10 }
    [ordered]@{ title='前日涨停表现（日线推导）'; columns=@('项目','数值','说明'); rows=$t11 }
    [ordered]@{ title='盘中封板/炸板代理（OHLC推导，代理日期20260908）'; columns=@('项目','数值','说明'); rows=$t12 }
    [ordered]@{ title='数据源状态与新鲜度'; columns=@('数据域','状态','关键证据'); rows=$t13 }
  )
}

$json = $report | ConvertTo-Json -Depth 8
$dst = 'C:\work\260907 掌财智能体\CodeX-st-wsp\zhangcai-demo\data\harness\tasks\_task74_result.json'
Set-Content -Path $dst -Value $json -Encoding UTF8
# validate
$v = Get-Content -Raw $dst | ConvertFrom-Json
"OK status=$($v.status) findings=$($v.findings.Count) tables=$($v.tables.Count) cautions=$($v.cautions.Count)"
"LEN=$((Get-Content -Raw $dst).Length)"
$v.tables | ForEach-Object { "  table: $($_.title) rows=$($_.rows.Count) cols=$($_.columns.Count)" }

# --- readable-yet-compact serialization: one table row per line ---
function J($x) { ($x | ConvertTo-Json -Depth 12 -Compress) }
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine('{')
[void]$sb.AppendLine('  "status": ' + (J $report.status) + ',')
[void]$sb.AppendLine('  "summary": ' + (J $report.summary) + ',')
[void]$sb.AppendLine('  "data_date": ' + (J $report.data_date) + ',')
[void]$sb.AppendLine('  "data_scope": ' + (J $report.data_scope) + ',')
$cs = ($report.cautions | ForEach-Object { '    ' + (J $_) }) -join ",`n"
[void]$sb.AppendLine('  "cautions": ['); [void]$sb.AppendLine($cs); [void]$sb.AppendLine('  ],')
$fs = ($report.findings | ForEach-Object { '    {"title": ' + (J $_.title) + ', "text": ' + (J $_.text) + '}' }) -join ",`n"
[void]$sb.AppendLine('  "findings": ['); [void]$sb.AppendLine($fs); [void]$sb.AppendLine('  ],')
[void]$sb.AppendLine('  "tables": [')
$tblocks = @()
foreach ($t in $report.tables) {
  $rows = ($t.rows | ForEach-Object { '        ' + (J $_) }) -join ",`n"
  $blk = (@(
    '    {'
    '      "title": ' + (J $t.title) + ','
    '      "columns": ' + (J $t.columns) + ','
    '      "rows": ['
    $rows
    '      ]'
    '    }'
  ) -join "`n")
  $tblocks += $blk
}
[void]$sb.AppendLine(($tblocks -join ",`n"))
[void]$sb.AppendLine('  ]')
[void]$sb.Append('}')
$compact = $sb.ToString()
$dst2 = 'C:\work\260907 掌财智能体\CodeX-st-wsp\zhangcai-demo\data\harness\tasks\_task74_result_compact.json'
Set-Content -Path $dst2 -Value $compact -Encoding UTF8
$v2 = Get-Content -Raw $dst2 | ConvertFrom-Json
$same = ((($v2 | ConvertTo-Json -Depth 12 -Compress)) -eq (($v | ConvertTo-Json -Depth 12 -Compress)))
"COMPACT_OK=$same LINES=$((Get-Content $dst2).Count) LEN=$($compact.Length)"



