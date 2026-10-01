from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


DAILY_SOURCE = "通达信日线"
FORMULA_SOURCE = "现行公式离线回放"
MARKET_SOURCE = "通达信本地全市场/指数日线"
CROSS_SECTION_SOURCE = "同日飞龙共振首板横截面"


def build_yaogu_factor_specs() -> dict[str, dict[str, str]]:
    specs: dict[str, dict[str, str]] = {}

    def add(
        key: str,
        name: str,
        family: str,
        definition: str,
        unit: str = "数值",
        source: str = DAILY_SOURCE,
    ) -> None:
        if key in specs:
            raise RuntimeError(f"duplicate_yaogu_factor:{key}")
        specs[key] = {
            "factor": key,
            "name": name,
            "family": family,
            "definition": definition,
            "unit": unit,
            "source": source,
            "available_at": "首板收盘后",
        }

    for key, name, definition, unit in (
        ("board_close_price", "首板收盘价格", "首板收盘价", "元"),
        ("board_vwap_price", "首板日均成交价格", "首板成交额/成交量", "元"),
        ("board_amount_100m", "首板成交额层级", "首板成交额/1亿元", "亿元"),
        ("board_log_amount", "首板成交额对数", "log(1+首板成交额)", "对数"),
        ("board_log_volume", "首板成交量对数", "log(1+首板成交量)", "对数"),
        ("board_amount_per_range_100m", "首板单位振幅成交额", "首板成交额亿元/(首板振幅百分点)", "亿元/百分点"),
        ("board_volume_zscore_20d", "首板成交量20日异常分", "(首板量-前20日均量)/前20日量标准差", "标准差"),
        ("board_amount_zscore_20d", "首板成交额20日异常分", "(首板额-前20日均额)/前20日额标准差", "标准差"),
        ("board_volume_zscore_60d", "首板成交量60日异常分", "(首板量-前60日均量)/前60日量标准差", "标准差"),
        ("board_amount_zscore_60d", "首板成交额60日异常分", "(首板额-前60日均额)/前60日额标准差", "标准差"),
    ):
        add(key, name, "价格与流动性层级", definition, unit)

    distribution_metrics = (
        ("return_mean", "收益均值", "日收益算术平均", "%"),
        ("return_median", "收益中位数", "日收益中位数", "%"),
        ("return_skew", "收益偏度", "日收益三阶标准化矩", "偏度"),
        ("return_excess_kurt", "收益超额峰度", "日收益四阶标准化矩减3", "峰度"),
        ("return_q10", "收益10%分位", "日收益10%分位数", "%"),
        ("return_q90", "收益90%分位", "日收益90%分位数", "%"),
        ("return_iqr", "收益四分位距", "日收益75%分位减25%分位", "%"),
        ("negative_day_ratio", "下跌日占比", "日收益小于0的天数占比", "0-1"),
        ("large_up_day_ratio", "大涨日占比", "日收益不低于3%的天数占比", "0-1"),
        ("large_down_day_ratio", "大跌日占比", "日收益不高于-3%的天数占比", "0-1"),
        ("gain_loss_balance", "平均涨跌幅平衡", "上涨日平均收益/下跌日平均绝对收益", "倍"),
    )
    for window in (10, 20, 60, 120):
        for suffix, name, definition, unit in distribution_metrics:
            add(
                f"prior_{suffix}_{window}d",
                f"前{window}日{name}",
                "收益分布与尾部",
                f"首板前{window}日{definition}",
                unit,
            )

    sequence_metrics = (
        ("sign_change_ratio", "涨跌方向切换率", "相邻日收益符号发生变化的次数占比", "0-1"),
        ("binary_sign_entropy", "涨跌二元熵", "上涨/非上涨状态的归一化香农熵", "0-1"),
        ("three_state_entropy", "涨平跌三状态熵", "收益大于1%、介于正负1%、小于-1%的归一化香农熵", "0-1"),
        ("return_autocorr1", "收益一阶自相关", "日收益与滞后1日收益的相关系数", "相关系数"),
        ("longest_up_streak", "窗口内最长连涨", "窗口内日收益连续大于0的最长天数", "天"),
        ("longest_down_streak", "窗口内最长连跌", "窗口内日收益连续小于0的最长天数", "天"),
    )
    for window in (10, 20, 60, 120):
        for suffix, name, definition, unit in sequence_metrics:
            add(f"prior_{suffix}_{window}d", f"前{window}日{name}", "价格序列记忆", f"首板前{window}日{definition}", unit)
    for window in (20, 60, 120):
        for suffix, name, definition, unit in (
            ("return_autocorr2", "收益二阶自相关", "日收益与滞后2日收益的相关系数", "相关系数"),
            ("variance_ratio2", "二日方差比", "二日对数收益方差/(2倍一日对数收益方差)", "倍"),
            ("log_trend_r2", "对数价格趋势拟合度", "对数收盘价对时间线性回归的R方", "0-1"),
            ("log_trend_residual_vol", "趋势残差波动", "对数价格线性趋势残差标准差", "%"),
            ("log_trend_curvature", "对数价格曲率", "对数收盘价二次回归二次项系数乘10000", "曲率"),
        ):
            add(f"prior_{suffix}_{window}d", f"前{window}日{name}", "价格序列记忆", f"首板前{window}日{definition}", unit)

    coupling_metrics = (
        ("gap_mean", "隔夜缺口均值", "开盘/昨收-1的平均值", "%"),
        ("gap_vol", "隔夜缺口波动", "开盘/昨收-1的标准差", "%"),
        ("intraday_mean", "日内收益均值", "收盘/开盘-1的平均值", "%"),
        ("intraday_vol", "日内收益波动", "收盘/开盘-1的标准差", "%"),
        ("gap_intraday_corr", "隔夜与日内相关", "隔夜缺口与同日日内收益相关系数", "相关系数"),
        ("gap_intraday_opposite_ratio", "隔夜日内反向占比", "隔夜缺口与日内收益符号相反的天数占比", "0-1"),
        ("absolute_gap_share", "绝对波动隔夜占比", "绝对隔夜缺口和/绝对隔夜与日内变动和", "0-1"),
        ("gap_up_ratio", "高开日占比", "隔夜缺口大于0的天数占比", "0-1"),
        ("gap_down_ratio", "低开日占比", "隔夜缺口小于0的天数占比", "0-1"),
    )
    for window in (10, 20, 60):
        for suffix, name, definition, unit in coupling_metrics:
            add(f"prior_{suffix}_{window}d", f"前{window}日{name}", "隔夜日内耦合", f"首板前{window}日{definition}", unit)

    candle_metrics = (
        ("long_upper_shadow_ratio", "长上影占比", "上影线/日振幅不低于40%的天数占比"),
        ("long_lower_shadow_ratio", "长下影占比", "下影线/日振幅不低于40%的天数占比"),
        ("doji_ratio", "十字星占比", "实体/日振幅不高于10%的天数占比"),
        ("close_top10_ratio", "收盘贴近日高占比", "收盘位置不低于0.9的天数占比"),
        ("close_bottom10_ratio", "收盘贴近日低占比", "收盘位置不高于0.1的天数占比"),
        ("strong_bull_body_ratio", "强阳实体占比", "阳线且实体/日振幅不低于60%的天数占比"),
        ("gap_and_go_ratio", "高开走强占比", "高开且收盘高于开盘的天数占比"),
        ("gap_fade_ratio", "高开回落占比", "高开且收盘低于开盘的天数占比"),
        ("low_break_recovery_ratio", "下探收复占比", "最低价跌破昨收且收盘收复昨收的天数占比"),
    )
    for window in (10, 20, 60):
        for suffix, name, definition in candle_metrics:
            add(f"prior_{suffix}_{window}d", f"前{window}日{name}", "K线行为频率", f"首板前{window}日{definition}", "0-1")

    volume_metrics = (
        ("volume_entropy", "成交量熵", "成交量占比的归一化香农熵", "0-1"),
        ("amount_entropy", "成交额熵", "成交额占比的归一化香农熵", "0-1"),
        ("volume_gini", "成交量基尼", "成交量分布基尼系数", "0-1"),
        ("amount_gini", "成交额基尼", "成交额分布基尼系数", "0-1"),
        ("volume_top3_share", "前三大成交量集中度", "窗口内最大3日成交量/总成交量", "0-1"),
        ("amount_top3_share", "前三大成交额集中度", "窗口内最大3日成交额/总成交额", "0-1"),
        ("volume_skew", "成交量偏度", "成交量三阶标准化矩", "偏度"),
        ("amount_skew", "成交额偏度", "成交额三阶标准化矩", "偏度"),
        ("volume_autocorr1", "成交量一阶自相关", "成交量与滞后1日成交量相关系数", "相关系数"),
        ("amount_autocorr1", "成交额一阶自相关", "成交额与滞后1日成交额相关系数", "相关系数"),
    )
    for window in (10, 20, 60):
        for suffix, name, definition, unit in volume_metrics:
            add(f"prior_{suffix}_{window}d", f"前{window}日{name}", "量能分布与集中度", f"首板前{window}日{definition}", unit)

    impact_metrics = (
        ("amihud_illiquidity", "Amihud非流动性", "绝对日收益百分点/(成交额亿元)的均值", "百分点/亿元"),
        ("range_amount_impact", "振幅成交额冲击", "日振幅百分点/(成交额亿元)的均值", "百分点/亿元"),
        ("intraday_amount_impact", "日内成交额冲击", "绝对日内收益百分点/(成交额亿元)的均值", "百分点/亿元"),
        ("amount_per_abs_move", "单位绝对波动成交额", "成交额亿元合计/绝对日收益百分点合计", "亿元/百分点"),
        ("zero_return_ratio", "零涨跌日占比", "绝对日收益小于0.01%的天数占比", "0-1"),
        ("volume_shock_ratio", "放量冲击日占比", "成交量高于窗口均值加1倍标准差的天数占比", "0-1"),
        ("amount_shock_ratio", "放额冲击日占比", "成交额高于窗口均值加1倍标准差的天数占比", "0-1"),
    )
    for window in (10, 20, 60):
        for suffix, name, definition, unit in impact_metrics:
            add(f"prior_{suffix}_{window}d", f"前{window}日{name}", "流动性与价格冲击", f"首板前{window}日{definition}", unit)

    breakout_metrics = (
        ("high_breakout_attempt_ratio", "盘中突破尝试占比", "最高价突破此前同窗口最高价的天数占比"),
        ("failed_high_breakout_ratio", "突破失败占比", "盘中突破此前同窗口最高价但收盘未站上的天数占比"),
        ("close_breakout_ratio", "收盘有效突破占比", "收盘价站上此前同窗口最高价的天数占比"),
        ("resistance_touch_ratio", "压力位触碰占比", "最高价到此前同窗口最高价的99%以上但收盘未站上的天数占比"),
        ("support_break_recovery_ratio", "破位收复占比", "最低价跌破此前同窗口最低价但收盘收复的天数占比"),
        ("new_close_high_ratio", "收盘新高占比", "收盘价突破此前同窗口最高收盘的天数占比"),
    )
    for window in (20, 60, 120):
        for suffix, name, definition in breakout_metrics:
            add(f"prior_{suffix}_{window}d", f"前{window}日{name}", "突破试错与压力消化", f"首板前{window}日{definition}", "0-1")

    recovery_metrics = (
        ("current_drawdown", "当前距峰回撤", "窗口末收盘/窗口最高收盘-1", "%"),
        ("current_recovery", "当前距谷修复", "窗口末收盘/窗口最低收盘-1", "%"),
        ("peak_age", "窗口峰值距今天数", "窗口最高收盘距首板前一日的交易日数", "天"),
        ("trough_age", "窗口谷值距今天数", "窗口最低收盘距首板前一日的交易日数", "天"),
        ("underwater_ratio", "水下运行占比", "收盘低于此前累计峰值的天数占比", "0-1"),
        ("post_trough_recovery_efficiency", "谷底后修复效率", "谷底后净上涨/逐日绝对变化之和；路径无变动时记0", "0-1"),
    )
    for window in (20, 60, 120):
        for suffix, name, definition, unit in recovery_metrics:
            add(f"prior_{suffix}_{window}d", f"前{window}日{name}", "回撤修复与筹码释放", f"首板前{window}日{definition}", unit)

    yaogu_metrics = (
        ("max_limitup_streak", "历史最长连续涨停", "日涨幅不低于9.8%的最长连续天数", "板"),
        ("two_board_episode_count", "历史二板段次数", "连续涨停长度不低于2的独立区段数", "次"),
        ("three_board_episode_count", "历史三板段次数", "连续涨停长度不低于3的独立区段数", "次"),
        ("multi_board_day_count", "连板段内涨停日数", "所有长度不低于2的连续涨停区段所含日数", "天"),
        ("touch_fail_count", "历史炸板近似次数", "最高价触及昨收1.098倍但收盘涨幅低于9.8%的天数", "次"),
        ("touch_fail_ratio", "触板后炸板占比", "历史炸板近似次数/(封住涨停次数+炸板近似次数)；无触板事件时记0", "0-1"),
        ("limit_cluster_count", "涨停聚集簇数", "相邻涨停间隔不超过3个交易日视为同簇的簇数", "簇"),
        ("isolated_limit_share", "孤立涨停占比", "前后最近涨停间隔均大于3个交易日的涨停占比；无涨停事件时记0", "0-1"),
        ("limit_interarrival_cv", "涨停间隔离散度", "相邻涨停间隔总体标准差/均值；不足两个间隔时记0", "倍"),
        ("latest_limit_episode_length", "最近涨停段长度", "窗口内最近一个连续涨停区段的长度", "板"),
        ("days_since_two_board", "距最近二板段天数", "距最近长度不低于2的涨停区段末日交易日数；无则窗口+1", "天"),
        ("days_since_three_board", "距最近三板段天数", "距最近长度不低于3的涨停区段末日交易日数；无则窗口+1", "天"),
    )
    for window in (60, 120, 250):
        for suffix, name, definition, unit in yaogu_metrics:
            add(f"prior_{suffix}_{window}d", f"前{window}日{name}", "妖性连板与炸板记忆", f"首板前{window}日{definition}", unit)
    for key, name, definition, unit in (
        ("prior_limit_event_count_250d", "前250日可评价涨停事件数", "前250日中后续至少有1个已完成交易日的涨停次数", "次"),
        ("prior_limit_nextday_continuation_rate_250d", "历史涨停次日续板率", "历史涨停后下一交易日再次涨停的比例；无可评价涨停事件时记0", "0-1"),
        ("prior_limit_nextday_return_mean_250d", "历史涨停次日平均涨幅", "历史涨停后下一交易日收益均值；无可评价涨停事件时记0", "%"),
        ("prior_limit_nextday_gap_mean_250d", "历史涨停次日平均缺口", "历史涨停后下一交易日开盘缺口均值；无可评价涨停事件时记0", "%"),
        ("prior_limit_post3d_return_mean_250d", "历史涨停后三日平均收益", "历史涨停收盘到其后第3个交易日收盘收益均值；无已完成三日事件时记0", "%"),
        ("prior_limit_post3d_drawdown_mean_250d", "历史涨停后三日平均最大回撤", "历史涨停后3日最低收盘/涨停收盘-1的均值；无已完成三日事件时记0", "%"),
        ("prior_touch_fail_nextday_recovery_rate_250d", "历史炸板次日修复率", "历史炸板近似日后下一交易日收盘高于炸板日收盘的比例；无可评价炸板事件时记0", "0-1"),
    ):
        add(key, name, "妖性后验记忆（仅历史）", definition, unit)

    percentile_metrics = (
        ("return", "首板涨幅历史分位", "首板日收益"),
        ("gap", "首板缺口历史分位", "首板开盘缺口"),
        ("intraday", "首板日内收益历史分位", "首板日内收益"),
        ("range", "首板振幅历史分位", "首板日振幅"),
        ("body", "首板实体历史分位", "首板实体幅度"),
        ("upper_shadow", "首板上影历史分位", "首板上影幅度"),
        ("lower_shadow", "首板下影历史分位", "首板下影幅度"),
        ("volume", "首板成交量历史分位", "首板成交量"),
        ("amount", "首板成交额历史分位", "首板成交额"),
        ("close_location", "首板收盘位置历史分位", "首板收盘位置"),
    )
    for window in (20, 60, 120):
        for suffix, name, definition in percentile_metrics:
            add(
                f"board_{suffix}_percentile_{window}d",
                f"{name}（前{window}日）",
                "首板相对自身历史异常",
                f"{definition}在首板前{window}日经验分布中的百分位",
                "0-1",
            )

    for window in (20, 60, 120, 250):
        add(
            f"prior_corporate_action_count_{window}d",
            f"前{window}日除权事件数",
            "公司行为时距",
            f"本地GBBQ中首板前{window}个交易日内除权除息事件数",
            "次",
            "通达信GBBQ",
        )
    for key, name, definition in (
        ("prior_corporate_action_age", "最近除权事件时距", "最近一次除权除息事件距首板的交易日数；无历史事件为缺失"),
        ("prior_cash_dividend_event_count_250d", "前250日现金分红事件数", "前250个交易日现金分红字段大于0的事件数"),
        ("prior_bonus_share_event_count_250d", "前250日送转事件数", "前250个交易日送股字段大于0的事件数"),
        ("prior_rights_issue_event_count_250d", "前250日配股事件数", "前250个交易日配股字段大于0的事件数"),
    ):
        add(key, name, "公司行为时距", definition, "次" if "数" in name else "天", "通达信GBBQ")

    for key, name, definition in (
        ("formula_active_subsignal_count", "公式活跃子信号数", "现行公式6个已登记子信号中首板日成立数量"),
        ("formula_core_subsignal_count", "公式核心路径数量", "龙头战法、波段密码、暴涨启动、私募秘进4条路径成立数量"),
        ("formula_xs_subsignal_count", "公式XS共振数量", "XS1与XS2首板日成立数量"),
        ("formula_core_density", "公式核心路径密度", "核心路径成立数量/4"),
        ("formula_longtou_waveband_pair", "龙头与波段同现", "龙头战法与波段密码同时成立"),
        ("formula_longtou_rapid_pair", "龙头与暴涨同现", "龙头战法与暴涨启动同时成立"),
        ("formula_longtou_private_pair", "龙头与私募同现", "龙头战法与私募秘进同时成立"),
        ("formula_waveband_rapid_pair", "波段与暴涨同现", "波段密码与暴涨启动同时成立"),
        ("formula_waveband_private_pair", "波段与私募同现", "波段密码与私募秘进同时成立"),
        ("formula_rapid_private_pair", "暴涨与私募同现", "暴涨启动与私募秘进同时成立"),
    ):
        add(key, name, "公式共振内部结构", definition, "计数或0/1", FORMULA_SOURCE)

    rank_bases = (
        "board_close_price",
        "board_amount_100m",
        "board_volume_zscore_20d",
        "board_amount_zscore_20d",
        "prior_return_skew_20d",
        "prior_return_excess_kurt_20d",
        "prior_sign_change_ratio_20d",
        "prior_three_state_entropy_20d",
        "prior_return_autocorr1_20d",
        "prior_variance_ratio2_60d",
        "prior_gap_intraday_corr_20d",
        "prior_gap_intraday_opposite_ratio_20d",
        "prior_long_upper_shadow_ratio_20d",
        "prior_gap_fade_ratio_20d",
        "prior_volume_entropy_20d",
        "prior_amount_gini_20d",
        "prior_volume_top3_share_20d",
        "prior_amihud_illiquidity_20d",
        "prior_failed_high_breakout_ratio_60d",
        "prior_support_break_recovery_ratio_60d",
        "prior_current_drawdown_60d",
        "prior_post_trough_recovery_efficiency_60d",
        "prior_max_limitup_streak_250d",
        "prior_two_board_episode_count_250d",
        "prior_touch_fail_ratio_250d",
        "prior_limit_interarrival_cv_250d",
        "prior_limit_nextday_continuation_rate_250d",
        "board_volume_percentile_60d",
        "board_amount_percentile_60d",
        "prior_corporate_action_age",
    )
    for base in rank_bases:
        add(
            f"cross_section_rank_{base}",
            f"{specs[base]['name']}同日共振池分位",
            "同日横截面稀缺性",
            f"{specs[base]['name']}在同日同交易制度飞龙共振首板池的百分位；池内少于5只为缺失",
            "0-1",
            CROSS_SECTION_SOURCE,
        )

    for source_key, source_name in (
        ("market_advance_ratio", "全市场上涨占比"),
        ("market_ge_9_8_count", "全市场涨停近似家数"),
        ("market_amount_100m", "全市场成交额"),
        ("signal_count", "飞龙共振首板数"),
        ("market_median_return_pct", "全市场中位涨幅"),
        ("market_index_avg_1d_pct", "三大指数平均涨幅"),
    ):
        for window in (5, 10):
            add(
                f"{source_key}_prior_signal_z{window}",
                f"{source_name}相对前{window}个信号日异常分",
                "市场妖股土壤",
                f"({source_name}-此前{window}个有共振交易日均值)/此前{window}个有共振交易日标准差",
                "标准差",
                MARKET_SOURCE,
            )
    for key, name, definition, unit in (
        ("market_limitups_per_signal", "市场涨停数/飞龙共振数", "全市场涨停近似家数/当日飞龙共振首板数", "倍"),
        ("signal_share_of_market_limitups", "飞龙共振占涨停比例", "当日飞龙共振首板数/全市场涨停近似家数", "0-1"),
        ("market_advance_decline_ratio", "市场涨跌家数比", "上涨股数/下跌股数", "倍"),
        ("market_limitup_breadth", "市场涨停宽度", "全市场涨停近似家数/交易股票数", "0-1"),
    ):
        add(key, name, "市场妖股土壤", definition, unit, MARKET_SOURCE)

    return specs


YAOGU_FACTOR_SPECS = build_yaogu_factor_specs()


def _clean(values: pd.Series) -> pd.Series:
    return pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna().astype(float)


def _safe_div(numerator: float, denominator: float) -> float:
    if not math.isfinite(numerator) or not math.isfinite(denominator) or denominator == 0:
        return math.nan
    return numerator / denominator


def _corr(left: pd.Series, right: pd.Series, lag: int = 0) -> float:
    a = pd.to_numeric(left, errors="coerce")
    b = pd.to_numeric(right, errors="coerce")
    if lag:
        a = a.iloc[lag:].reset_index(drop=True)
        b = b.iloc[:-lag].reset_index(drop=True)
    pair = pd.concat([a.reset_index(drop=True), b.reset_index(drop=True)], axis=1).dropna()
    if len(pair) < 4 or pair.iloc[:, 0].nunique() < 2 or pair.iloc[:, 1].nunique() < 2:
        return math.nan
    return float(pair.iloc[:, 0].corr(pair.iloc[:, 1]))


def _skew(values: pd.Series) -> float:
    clean = _clean(values)
    return float(clean.skew()) if len(clean) >= 4 and clean.nunique() > 1 else math.nan


def _kurt(values: pd.Series) -> float:
    clean = _clean(values)
    return float(clean.kurt()) if len(clean) >= 5 and clean.nunique() > 1 else math.nan


def _state_entropy(states: np.ndarray, state_count: int) -> float:
    if not len(states) or state_count <= 1:
        return math.nan
    counts = np.bincount(states.astype(int), minlength=state_count).astype(float)
    probabilities = counts[counts > 0] / counts.sum()
    return float(-(probabilities * np.log(probabilities)).sum() / math.log(state_count))


def _weight_entropy(values: pd.Series) -> float:
    clean = _clean(values)
    if len(clean) < 2 or float(clean.sum()) <= 0:
        return math.nan
    probabilities = clean.to_numpy(dtype=float) / float(clean.sum())
    probabilities = probabilities[probabilities > 0]
    return float(-(probabilities * np.log(probabilities)).sum() / math.log(len(clean)))


def _gini(values: pd.Series) -> float:
    clean = np.sort(_clean(values).to_numpy(dtype=float))
    if not len(clean) or clean.sum() <= 0:
        return math.nan
    index = np.arange(1, len(clean) + 1, dtype=float)
    return float((2.0 * np.dot(index, clean) / (len(clean) * clean.sum())) - (len(clean) + 1.0) / len(clean))


def _longest_streak(flags: np.ndarray) -> int:
    longest = 0
    current = 0
    for value in flags.astype(bool):
        current = current + 1 if value else 0
        longest = max(longest, current)
    return longest


def _episodes(flags: np.ndarray) -> list[tuple[int, int, int]]:
    result: list[tuple[int, int, int]] = []
    start: int | None = None
    for index, value in enumerate(flags.astype(bool)):
        if value and start is None:
            start = index
        if start is not None and (not value or index == len(flags) - 1):
            end = index if value and index == len(flags) - 1 else index - 1
            result.append((start, end, end - start + 1))
            start = None
    return result.copy()


def _percentile(value: float, history: pd.Series) -> float:
    clean = _clean(history)
    if not math.isfinite(value) or not len(clean):
        return math.nan
    values = clean.to_numpy(dtype=float)
    return float((np.sum(values < value) + 0.5 * np.sum(values == value)) / len(values))


def _zscore(value: float, history: pd.Series) -> float:
    clean = _clean(history)
    if not math.isfinite(value) or len(clean) < 3:
        return math.nan
    deviation = float(clean.std(ddof=1))
    return _safe_div(value - float(clean.mean()), deviation)


def _trend_statistics(values: pd.Series) -> tuple[float, float, float]:
    clean = _clean(values)
    if len(clean) < 5 or (clean <= 0).any():
        return math.nan, math.nan, math.nan
    y = np.log(clean.to_numpy(dtype=float))
    x = np.arange(len(y), dtype=float)
    linear = np.polyfit(x, y, 1)
    fitted = np.polyval(linear, x)
    residual = y - fitted
    total = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - float(np.sum(residual**2)) / total if total > 0 else math.nan
    quadratic = np.polyfit(x, y, 2)
    return r2, float(np.std(residual, ddof=1) * 100.0), float(quadratic[0] * 10000.0)


def calculate_yaogu_daily_factors(
    bars: pd.DataFrame,
    date: str,
    actions: pd.DataFrame | None = None,
) -> dict[str, Any]:
    result = {
        key: math.nan
        for key, spec in YAOGU_FACTOR_SPECS.items()
        if spec["source"] in {DAILY_SOURCE, "通达信GBBQ"}
    }
    if date not in bars.index:
        raise RuntimeError(f"event_date_missing:{date}")
    position = int(bars.index.get_loc(date))
    if position < 2:
        return result

    close = bars["close"].astype(float)
    open_ = bars["open"].astype(float)
    high = bars["high"].astype(float)
    low = bars["low"].astype(float)
    volume = bars["volume"].astype(float)
    amount = bars["amount"].astype(float)
    previous_close = close.shift(1)
    returns = close.pct_change()
    gaps = open_ / previous_close - 1.0
    intraday = close / open_ - 1.0
    ranges = (high - low) / previous_close
    bodies = (close - open_) / previous_close
    upper_shadows = (high - pd.concat([open_, close], axis=1).max(axis=1)) / previous_close
    lower_shadows = (pd.concat([open_, close], axis=1).min(axis=1) - low) / previous_close
    absolute_range = (high - low).replace(0, np.nan)
    close_location = (close - low) / absolute_range
    upper_share = (high - pd.concat([open_, close], axis=1).max(axis=1)) / absolute_range
    lower_share = (pd.concat([open_, close], axis=1).min(axis=1) - low) / absolute_range
    body_share = (close - open_).abs() / absolute_range

    current_close = float(close.iloc[position])
    current_volume = float(volume.iloc[position])
    current_amount = float(amount.iloc[position])
    current_range_pct = float(ranges.iloc[position] * 100.0)
    result.update(
        {
            "board_close_price": current_close,
            "board_vwap_price": _safe_div(current_amount, current_volume),
            "board_amount_100m": current_amount / 1e8,
            "board_log_amount": math.log1p(max(current_amount, 0.0)),
            "board_log_volume": math.log1p(max(current_volume, 0.0)),
            "board_amount_per_range_100m": _safe_div(current_amount / 1e8, current_range_pct),
        }
    )
    for window in (20, 60):
        if position >= window:
            volume_history = volume.iloc[position - window : position]
            amount_history = amount.iloc[position - window : position]
            result[f"board_volume_zscore_{window}d"] = _zscore(current_volume, volume_history)
            result[f"board_amount_zscore_{window}d"] = _zscore(current_amount, amount_history)

    for window in (10, 20, 60, 120):
        sample = returns.iloc[position - window : position] if position >= window else pd.Series(dtype=float)
        if len(sample) != window:
            continue
        clean = _clean(sample)
        positive = clean.loc[clean > 0]
        negative = clean.loc[clean < 0]
        result[f"prior_return_mean_{window}d"] = float(clean.mean() * 100.0)
        result[f"prior_return_median_{window}d"] = float(clean.median() * 100.0)
        result[f"prior_return_skew_{window}d"] = _skew(clean)
        result[f"prior_return_excess_kurt_{window}d"] = _kurt(clean)
        result[f"prior_return_q10_{window}d"] = float(clean.quantile(0.10) * 100.0)
        result[f"prior_return_q90_{window}d"] = float(clean.quantile(0.90) * 100.0)
        result[f"prior_return_iqr_{window}d"] = float((clean.quantile(0.75) - clean.quantile(0.25)) * 100.0)
        result[f"prior_negative_day_ratio_{window}d"] = float(clean.lt(0).mean())
        result[f"prior_large_up_day_ratio_{window}d"] = float(clean.ge(0.03).mean())
        result[f"prior_large_down_day_ratio_{window}d"] = float(clean.le(-0.03).mean())
        result[f"prior_gain_loss_balance_{window}d"] = _safe_div(float(positive.mean()), abs(float(negative.mean()))) if len(positive) and len(negative) else math.nan
        signs = np.where(clean.to_numpy(dtype=float) > 0, 1, 0)
        three_states = np.where(clean.to_numpy(dtype=float) > 0.01, 2, np.where(clean.to_numpy(dtype=float) < -0.01, 0, 1))
        result[f"prior_sign_change_ratio_{window}d"] = float(np.mean(signs[1:] != signs[:-1])) if len(signs) > 1 else math.nan
        result[f"prior_binary_sign_entropy_{window}d"] = _state_entropy(signs, 2)
        result[f"prior_three_state_entropy_{window}d"] = _state_entropy(three_states, 3)
        result[f"prior_return_autocorr1_{window}d"] = _corr(clean, clean, 1)
        result[f"prior_longest_up_streak_{window}d"] = _longest_streak(clean.gt(0).to_numpy())
        result[f"prior_longest_down_streak_{window}d"] = _longest_streak(clean.lt(0).to_numpy())
        if window in (20, 60, 120):
            result[f"prior_return_autocorr2_{window}d"] = _corr(clean, clean, 2)
            log_returns = np.log1p(clean.to_numpy(dtype=float))
            one_variance = float(np.var(log_returns, ddof=1))
            two_returns = log_returns[1:] + log_returns[:-1]
            result[f"prior_variance_ratio2_{window}d"] = _safe_div(float(np.var(two_returns, ddof=1)), 2.0 * one_variance)
            price_sample = close.iloc[position - window : position]
            r2, residual_vol, curvature = _trend_statistics(price_sample)
            result[f"prior_log_trend_r2_{window}d"] = r2
            result[f"prior_log_trend_residual_vol_{window}d"] = residual_vol
            result[f"prior_log_trend_curvature_{window}d"] = curvature

    for window in (10, 20, 60):
        if position < window:
            continue
        gap_sample = gaps.iloc[position - window : position]
        intraday_sample = intraday.iloc[position - window : position]
        result[f"prior_gap_mean_{window}d"] = float(gap_sample.mean() * 100.0)
        result[f"prior_gap_vol_{window}d"] = float(gap_sample.std(ddof=1) * 100.0)
        result[f"prior_intraday_mean_{window}d"] = float(intraday_sample.mean() * 100.0)
        result[f"prior_intraday_vol_{window}d"] = float(intraday_sample.std(ddof=1) * 100.0)
        result[f"prior_gap_intraday_corr_{window}d"] = _corr(gap_sample, intraday_sample)
        result[f"prior_gap_intraday_opposite_ratio_{window}d"] = float((gap_sample * intraday_sample < 0).mean())
        result[f"prior_absolute_gap_share_{window}d"] = _safe_div(float(gap_sample.abs().sum()), float(gap_sample.abs().sum() + intraday_sample.abs().sum()))
        result[f"prior_gap_up_ratio_{window}d"] = float(gap_sample.gt(0).mean())
        result[f"prior_gap_down_ratio_{window}d"] = float(gap_sample.lt(0).mean())

        section = slice(position - window, position)
        result[f"prior_long_upper_shadow_ratio_{window}d"] = float(upper_share.iloc[section].ge(0.40).mean())
        result[f"prior_long_lower_shadow_ratio_{window}d"] = float(lower_share.iloc[section].ge(0.40).mean())
        result[f"prior_doji_ratio_{window}d"] = float(body_share.iloc[section].le(0.10).mean())
        result[f"prior_close_top10_ratio_{window}d"] = float(close_location.iloc[section].ge(0.90).mean())
        result[f"prior_close_bottom10_ratio_{window}d"] = float(close_location.iloc[section].le(0.10).mean())
        result[f"prior_strong_bull_body_ratio_{window}d"] = float(((close.iloc[section] > open_.iloc[section]) & body_share.iloc[section].ge(0.60)).mean())
        result[f"prior_gap_and_go_ratio_{window}d"] = float(((gaps.iloc[section] > 0) & (close.iloc[section] > open_.iloc[section])).mean())
        result[f"prior_gap_fade_ratio_{window}d"] = float(((gaps.iloc[section] > 0) & (close.iloc[section] < open_.iloc[section])).mean())
        result[f"prior_low_break_recovery_ratio_{window}d"] = float(((low.iloc[section] < previous_close.iloc[section]) & (close.iloc[section] > previous_close.iloc[section])).mean())

        volume_sample = volume.iloc[section]
        amount_sample = amount.iloc[section]
        result[f"prior_volume_entropy_{window}d"] = _weight_entropy(volume_sample)
        result[f"prior_amount_entropy_{window}d"] = _weight_entropy(amount_sample)
        result[f"prior_volume_gini_{window}d"] = _gini(volume_sample)
        result[f"prior_amount_gini_{window}d"] = _gini(amount_sample)
        result[f"prior_volume_top3_share_{window}d"] = _safe_div(float(volume_sample.nlargest(min(3, window)).sum()), float(volume_sample.sum()))
        result[f"prior_amount_top3_share_{window}d"] = _safe_div(float(amount_sample.nlargest(min(3, window)).sum()), float(amount_sample.sum()))
        result[f"prior_volume_skew_{window}d"] = _skew(volume_sample)
        result[f"prior_amount_skew_{window}d"] = _skew(amount_sample)
        result[f"prior_volume_autocorr1_{window}d"] = _corr(volume_sample, volume_sample, 1)
        result[f"prior_amount_autocorr1_{window}d"] = _corr(amount_sample, amount_sample, 1)

        return_sample = returns.iloc[section]
        range_sample = ranges.iloc[section]
        amount_100m = amount_sample / 1e8
        result[f"prior_amihud_illiquidity_{window}d"] = float((return_sample.abs() * 100.0 / amount_100m.replace(0, np.nan)).mean())
        result[f"prior_range_amount_impact_{window}d"] = float((range_sample * 100.0 / amount_100m.replace(0, np.nan)).mean())
        result[f"prior_intraday_amount_impact_{window}d"] = float((intraday_sample.abs() * 100.0 / amount_100m.replace(0, np.nan)).mean())
        result[f"prior_amount_per_abs_move_{window}d"] = _safe_div(float(amount_100m.sum()), float(return_sample.abs().sum() * 100.0))
        result[f"prior_zero_return_ratio_{window}d"] = float(return_sample.abs().lt(0.0001).mean())
        result[f"prior_volume_shock_ratio_{window}d"] = float(volume_sample.gt(volume_sample.mean() + volume_sample.std(ddof=1)).mean())
        result[f"prior_amount_shock_ratio_{window}d"] = float(amount_sample.gt(amount_sample.mean() + amount_sample.std(ddof=1)).mean())

    for window in (20, 60, 120):
        if position >= 2 * window:
            prior_high = high.shift(1).rolling(window, min_periods=window).max()
            prior_low = low.shift(1).rolling(window, min_periods=window).min()
            prior_close_high = close.shift(1).rolling(window, min_periods=window).max()
            section = slice(position - window, position)
            breakout = high.iloc[section] > prior_high.iloc[section]
            result[f"prior_high_breakout_attempt_ratio_{window}d"] = float(breakout.mean())
            result[f"prior_failed_high_breakout_ratio_{window}d"] = float((breakout & (close.iloc[section] <= prior_high.iloc[section])).mean())
            result[f"prior_close_breakout_ratio_{window}d"] = float((close.iloc[section] > prior_high.iloc[section]).mean())
            result[f"prior_resistance_touch_ratio_{window}d"] = float(((high.iloc[section] >= prior_high.iloc[section] * 0.99) & (close.iloc[section] <= prior_high.iloc[section])).mean())
            result[f"prior_support_break_recovery_ratio_{window}d"] = float(((low.iloc[section] < prior_low.iloc[section]) & (close.iloc[section] > prior_low.iloc[section])).mean())
            result[f"prior_new_close_high_ratio_{window}d"] = float((close.iloc[section] > prior_close_high.iloc[section]).mean())
        if position >= window:
            sample = close.iloc[position - window : position]
            values = sample.to_numpy(dtype=float)
            peak = int(np.argmax(values))
            trough = int(np.argmin(values))
            result[f"prior_current_drawdown_{window}d"] = (_safe_div(values[-1], values[peak]) - 1.0) * 100.0
            result[f"prior_current_recovery_{window}d"] = (_safe_div(values[-1], values[trough]) - 1.0) * 100.0
            result[f"prior_peak_age_{window}d"] = window - 1 - peak
            result[f"prior_trough_age_{window}d"] = window - 1 - trough
            result[f"prior_underwater_ratio_{window}d"] = float(np.mean(values < np.maximum.accumulate(values)))
            recovery_path = values[trough:]
            denominator = float(np.abs(np.diff(recovery_path)).sum())
            result[f"prior_post_trough_recovery_efficiency_{window}d"] = (
                0.0
                if math.isfinite(denominator) and denominator == 0.0
                else _safe_div(float(recovery_path[-1] - recovery_path[0]), denominator)
            )

    limit_flags_all = returns.ge(0.098).fillna(False).to_numpy(dtype=bool)
    touch_fail_all = ((high / previous_close).ge(1.098) & returns.lt(0.098)).fillna(False).to_numpy(dtype=bool)
    for window in (60, 120, 250):
        if position < window:
            continue
        flags = limit_flags_all[position - window : position]
        touch_flags = touch_fail_all[position - window : position]
        episodes = _episodes(flags)
        multi = [episode for episode in episodes if episode[2] >= 2]
        triple = [episode for episode in episodes if episode[2] >= 3]
        positions = np.flatnonzero(flags)
        gaps_between = np.diff(positions)
        clusters = 0 if not len(positions) else int(1 + np.sum(gaps_between > 3))
        isolated = 0
        for index, hit in enumerate(positions):
            previous_gap = hit - positions[index - 1] if index > 0 else window + 1
            next_gap = positions[index + 1] - hit if index + 1 < len(positions) else window + 1
            isolated += int(previous_gap > 3 and next_gap > 3)
        result[f"prior_max_limitup_streak_{window}d"] = max((episode[2] for episode in episodes), default=0)
        result[f"prior_two_board_episode_count_{window}d"] = len(multi)
        result[f"prior_three_board_episode_count_{window}d"] = len(triple)
        result[f"prior_multi_board_day_count_{window}d"] = int(sum(episode[2] for episode in multi))
        result[f"prior_touch_fail_count_{window}d"] = int(touch_flags.sum())
        touch_event_count = int(touch_flags.sum() + flags.sum())
        result[f"prior_touch_fail_ratio_{window}d"] = (
            float(touch_flags.sum()) / touch_event_count if touch_event_count else 0.0
        )
        result[f"prior_limit_cluster_count_{window}d"] = clusters
        result[f"prior_isolated_limit_share_{window}d"] = float(isolated) / len(positions) if len(positions) else 0.0
        result[f"prior_limit_interarrival_cv_{window}d"] = (
            _safe_div(float(np.std(gaps_between, ddof=0)), float(np.mean(gaps_between)))
            if len(gaps_between) >= 2
            else 0.0
        )
        result[f"prior_latest_limit_episode_length_{window}d"] = episodes[-1][2] if episodes else 0
        result[f"prior_days_since_two_board_{window}d"] = window - multi[-1][1] if multi else window + 1
        result[f"prior_days_since_three_board_{window}d"] = window - triple[-1][1] if triple else window + 1

    start = max(0, position - 250)
    historical_limits = [index for index in range(start, position - 1) if limit_flags_all[index]]
    result["prior_limit_event_count_250d"] = len(historical_limits)
    result["prior_limit_nextday_continuation_rate_250d"] = 0.0
    result["prior_limit_nextday_return_mean_250d"] = 0.0
    result["prior_limit_nextday_gap_mean_250d"] = 0.0
    result["prior_limit_post3d_return_mean_250d"] = 0.0
    result["prior_limit_post3d_drawdown_mean_250d"] = 0.0
    if historical_limits:
        next_returns = [float(returns.iloc[index + 1]) for index in historical_limits]
        next_gaps = [float(gaps.iloc[index + 1]) for index in historical_limits]
        result["prior_limit_nextday_continuation_rate_250d"] = float(np.mean([value >= 0.098 for value in next_returns]))
        result["prior_limit_nextday_return_mean_250d"] = float(np.mean(next_returns) * 100.0)
        result["prior_limit_nextday_gap_mean_250d"] = float(np.mean(next_gaps) * 100.0)
        completed_three = [index for index in historical_limits if index + 3 < position]
        if completed_three:
            post_returns = [(float(close.iloc[index + 3]) / float(close.iloc[index]) - 1.0) for index in completed_three]
            post_drawdowns = [(float(close.iloc[index + 1 : index + 4].min()) / float(close.iloc[index]) - 1.0) for index in completed_three]
            result["prior_limit_post3d_return_mean_250d"] = float(np.mean(post_returns) * 100.0)
            result["prior_limit_post3d_drawdown_mean_250d"] = float(np.mean(post_drawdowns) * 100.0)
    historical_fails = [index for index in range(start, position - 1) if touch_fail_all[index]]
    result["prior_touch_fail_nextday_recovery_rate_250d"] = 0.0
    if historical_fails:
        result["prior_touch_fail_nextday_recovery_rate_250d"] = float(np.mean([close.iloc[index + 1] > close.iloc[index] for index in historical_fails]))

    current_series = {
        "return": returns,
        "gap": gaps,
        "intraday": intraday,
        "range": ranges,
        "body": bodies,
        "upper_shadow": upper_shadows,
        "lower_shadow": lower_shadows,
        "volume": volume,
        "amount": amount,
        "close_location": close_location,
    }
    for window in (20, 60, 120):
        if position < window:
            continue
        for suffix, series in current_series.items():
            result[f"board_{suffix}_percentile_{window}d"] = _percentile(float(series.iloc[position]), series.iloc[position - window : position])

    action_frame = actions if actions is not None else pd.DataFrame()
    if not action_frame.empty and "date" in action_frame:
        dates = bars.index.astype(str).to_numpy()
        action_rows = action_frame.loc[action_frame["date"].astype(str).lt(date)].copy()
        action_positions: list[int] = []
        for action_date in action_rows["date"].astype(str):
            action_position = int(np.searchsorted(dates, action_date, side="left"))
            if action_position < position:
                action_positions.append(action_position)
        for window in (20, 60, 120, 250):
            result[f"prior_corporate_action_count_{window}d"] = int(sum(action_position >= position - window for action_position in action_positions))
        if action_positions:
            result["prior_corporate_action_age"] = position - max(action_positions)
        recent_rows = action_rows.loc[action_rows["date"].astype(str).isin(dates[max(0, position - 250) : position])]
        result["prior_cash_dividend_event_count_250d"] = int(pd.to_numeric(recent_rows.get("cash_dividend_per_10"), errors="coerce").fillna(0).gt(0).sum())
        result["prior_bonus_share_event_count_250d"] = int(pd.to_numeric(recent_rows.get("bonus_shares_per_10"), errors="coerce").fillna(0).gt(0).sum())
        result["prior_rights_issue_event_count_250d"] = int(pd.to_numeric(recent_rows.get("rights_shares_per_10"), errors="coerce").fillna(0).gt(0).sum())
    else:
        for window in (20, 60, 120, 250):
            result[f"prior_corporate_action_count_{window}d"] = 0
        result["prior_cash_dividend_event_count_250d"] = 0
        result["prior_bonus_share_event_count_250d"] = 0
        result["prior_rights_issue_event_count_250d"] = 0
    return result


def add_yaogu_context_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    formula_columns = [
        "formula_longtou",
        "formula_waveband_password",
        "formula_rapid_rise",
        "formula_private_entry",
        "formula_xs1",
        "formula_xs2",
    ]
    formula_values = {
        column: pd.to_numeric(result.get(column), errors="coerce").fillna(0.0).gt(0).astype(float)
        for column in formula_columns
    }
    result["formula_active_subsignal_count"] = sum(formula_values.values())
    result["formula_core_subsignal_count"] = sum(formula_values[column] for column in formula_columns[:4])
    result["formula_xs_subsignal_count"] = formula_values["formula_xs1"] + formula_values["formula_xs2"]
    result["formula_core_density"] = result["formula_core_subsignal_count"] / 4.0
    for left, right, key in (
        ("formula_longtou", "formula_waveband_password", "formula_longtou_waveband_pair"),
        ("formula_longtou", "formula_rapid_rise", "formula_longtou_rapid_pair"),
        ("formula_longtou", "formula_private_entry", "formula_longtou_private_pair"),
        ("formula_waveband_password", "formula_rapid_rise", "formula_waveband_rapid_pair"),
        ("formula_waveband_password", "formula_private_entry", "formula_waveband_private_pair"),
        ("formula_rapid_rise", "formula_private_entry", "formula_rapid_private_pair"),
    ):
        result[key] = (formula_values[left].gt(0) & formula_values[right].gt(0)).astype(float)

    group_keys: list[pd.Series] = [result["first_board_date"].astype(str)]
    if "board_regime" in result:
        group_keys.append(result["board_regime"].astype(str))
    rank_specs = [key for key in YAOGU_FACTOR_SPECS if key.startswith("cross_section_rank_")]
    for rank_key in rank_specs:
        base = rank_key.removeprefix("cross_section_rank_")
        values = pd.to_numeric(result.get(base), errors="coerce")
        rank = values.groupby(group_keys, sort=False).rank(method="average", pct=True)
        sizes = values.groupby(group_keys, sort=False).transform("count")
        result[rank_key] = rank.where(sizes.ge(5))

    context_columns = [
        "market_advance_ratio",
        "market_ge_9_8_count",
        "market_amount_100m",
        "signal_count",
        "market_median_return_pct",
        "market_index_avg_1d_pct",
    ]
    daily = result[["first_board_date", *context_columns]].drop_duplicates("first_board_date").sort_values("first_board_date", kind="mergesort").set_index("first_board_date")
    for column in context_columns:
        values = pd.to_numeric(daily[column], errors="coerce")
        for window in (5, 10):
            mean = values.shift(1).rolling(window, min_periods=max(3, window // 2)).mean()
            std = values.shift(1).rolling(window, min_periods=max(3, window // 2)).std(ddof=1).replace(0, np.nan)
            daily[f"{column}_prior_signal_z{window}"] = (values - mean) / std
    traded = pd.to_numeric(daily.get("market_traded_count", result.drop_duplicates("first_board_date").set_index("first_board_date").get("market_traded_count")), errors="coerce")
    advance = pd.to_numeric(daily["market_advance_ratio"], errors="coerce")
    limitups = pd.to_numeric(daily["market_ge_9_8_count"], errors="coerce")
    signals = pd.to_numeric(daily["signal_count"], errors="coerce")
    daily["market_limitups_per_signal"] = limitups / signals.replace(0, np.nan)
    daily["signal_share_of_market_limitups"] = signals / limitups.replace(0, np.nan)
    advancing = traded * advance
    declining = traded * (1.0 - advance)
    daily["market_advance_decline_ratio"] = advancing / declining.replace(0, np.nan)
    daily["market_limitup_breadth"] = limitups / traded.replace(0, np.nan)
    context_specs = [key for key, spec in YAOGU_FACTOR_SPECS.items() if spec["source"] == MARKET_SOURCE]
    for column in context_specs:
        result[column] = result["first_board_date"].map(daily[column])
    return result.copy()
