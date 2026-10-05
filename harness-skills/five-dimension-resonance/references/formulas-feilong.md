# 飞龙在天公式源码与波段解读

> 包含：完整TDX指标公式与选股公式源码、波/段数值体系、超买超卖区间、爆发信号、波段操作规则。

---

## 一、完整TDX指标公式源码（飞龙在天副图ZB）

```text
X_15X:=EMA(CLOSE,89);
X_16X:=EMA(EMA(EMA(HIGH,13),13),13);
波:X_15X;  {注：此为TQ早期返回的额外字段，实际TQ输出以X_15/X_16为主}
段:X_16X;
X_17X:=EMA(EMA(EMA(HIGH,5),5),5);
X_18X:=(CLOSE-REF(CLOSE,1))/REF(CLOSE,1)*100;
X_19X:=FINANCE(42)>120;
X_20X:=IF(NAMELIKE(1),0,1);
X_21X:=IF(NAMELIKE(2),0,1);
X_22:=REF(CLOSE<89,1) AND REF(CLOSE>2,1);
X_23:=IF(CODELIKE(3),0,1);
X_24:=CLOSE>X_17X AND CLOSE>X_16X AND CLOSE>X_15X;
X_25:=HIGH/X_17X;
X_26:=X_18X>=9.84 AND REF(X_18X<9.84,1) AND REF(X_18X<9.84,2);
X_27:=X_19X AND X_20X AND X_21X AND X_22 AND X_23 AND X_24 AND X_25<1.16 AND X_26;
X_28:=IF(CLOSE>OPEN,CLOSE,OPEN);
X_29:=IF(CLOSE>OPEN,OPEN,CLOSE);
X_30:=LLV(X_28,4);
X_31:=HHV(X_29,4);
X_32:=X_28>=X_30 AND X_29<=X_30 AND X_28>=X_31 AND X_29<=X_31;
X_33:=REF(X_28,1)>=X_30 AND REF(X_29,1)<=X_30 AND REF(X_28,1)>=X_31 AND REF(X_29,1)<=X_31;
X_34:=REF(X_28,2)>=X_30 AND REF(X_29,2)<=X_30 AND REF(X_28,2)>=X_31 AND REF(X_29,2)<=X_31;
X_35:=REF(X_28,3)>=X_30 AND REF(X_29,3)<=X_30 AND REF(X_28,3)>=X_31 AND REF(X_29,3)<=X_31;
X_36:=X_32 AND X_33 AND X_34 AND X_35;
X_37:=EXIST(X_36>0,36);
X_38:=(REF(OPEN,5)+REF(CLOSE,5))/2;
X_39:=(HIGH+LOW+CLOSE+OPEN)/4;
X_40:=MAX(X_38,MAX(X_39,HHV(HIGH,5)));
X_41:=MIN(X_38,MIN(X_39,LLV(LOW,5)));
X_42:=X_40=X_38;
X_43:=X_42;
X_44:=REF(X_40,BARSLAST(X_43));
X_45:=X_18X>9.85 AND NOT(OPEN=CLOSE);
X_46:=COUNT(X_45,21);
X_47:=X_46=1 AND X_45;
X_48:=REF(X_31,BARSLAST(X_36));
X_49:=REF(X_40,BARSLAST(X_43));
X_50:=X_41/X_49;
X_51:=X_41/X_48;
X_52:=X_50<1.3 AND X_51<1.3 AND X_45;
X_53:=CLOSE>X_44;
X_54:=(CONST(LLV(X_52,X_52))/100+1)*X_52;
X_55:=X_27 AND X_52 AND X_37;
波段密码打板:=IF(FILTER(X_55,13) AND X_47,100,DRAWNULL),COLORYELLOW;
X_7:=(CLOSE-REF(CLOSE,1))/REF(CLOSE,1)*100;
X_8:=MA(VOL,2)/MA(VOL,10);
X_9:=VOL/CAPITAL;
X_10:=0.0068*X_7-0.0072*X_8-0.5676*X_9-0.0105;
X_11:=0.0015*X_7-0.0124*X_8+1.7461*X_9-0.0074;
暴涨启动:=(0-12.2401*X_10-1*X_11+0.321<0)*100,COLORRED,LINETHICK8;
X_13:=(CLOSE-LLV(LOW,36))/(HHV(HIGH,36)-LLV(LOW,36))*100;
X_14:=SMA(X_13,3,1);
X_15:=SMA(X_14,3,1);
X_16:=SMA(X_15,3,1);
波:X_15;   {实际TQ返回的波段振荡值}
段:X_16;
X_20:=CLOSE/REF(CLOSE,1)>1.048 AND CLOSE=HIGH AND BETWEEN(FORCAST(VOL,4),0.2*FORCAST(VOL,12),2.1*FORCAST(VOL,12));
私募秘进:=FILTER(X_20,28)*100,COLORYELLOW,LINETHICK3;
XS1:=私募秘进 OR (0-12.2401*X_10-1*X_11+0.321<0);
X_1X:=13;
X_4X:=1;
X_5X:=REF(CLOSE,1);
X_6X:=EMA(HHV(HIGH,1),8);
X_7X:=EMA(CLOSE,8);
X_8X:=X_7X<REF(X_7X,1) AND CLOSE<X_7X;
X_9X:=IF(X_6X<REF(X_6X,1) OR X_8X,1,0);
X_10X:=SMA(MAX(CLOSE-X_5X,0),2,1)/SMA(ABS(CLOSE-X_5X),2,1)*100;
X_11X:=45;X_12X:=20;
X_13X:=X_10X<X_11X AND REF(X_10X,1)>X_11X AND MACD.DIF!=0;
X_14X:=X_10X<X_12X AND REF(X_10X,1)>X_12X*X_4X;
龙头战法:=IF((COUNT(X_9X=1,4)=3 AND X_9X=0 AND OPEN<CLOSE AND (CLOSE-REF(CLOSE,1))/REF(CLOSE,1)>0.089)*10>=10 OR ((CLOSE-REF(CLOSE,1))/REF(CLOSE,1)>0.089 AND (REF(X_14X,1) OR REF(X_13X,1))) AND X_4X=1,100,DRAWNULL),COLORRED,LINETHICK9;
XS2:=(FILTER(X_55,13) AND X_47) OR ((COUNT(X_9X=1,4)=3 AND X_9X=0 AND OPEN<CLOSE AND (CLOSE-REF(CLOSE,1))/REF(CLOSE,1)>0.089)*10>=10 OR ((CLOSE-REF(CLOSE,1))/REF(CLOSE,1)>0.089 AND (REF(X_14X,1) OR REF(X_13X,1))) AND X_4X=1);
STICKLINE(XS1 AND XS2,0,100,2,0),COLORMAGENTA;
STICKLINE(XS1 AND XS2,0,70,4,0),COLORRED;
STICKLINE(XS1 AND XS2,0,50,6,0),COLORYELLOW;
DRAWTEXT(XS1 AND XS2,90,'   主升启动'),COLORYELLOW;
```

本地调用（ZB）：`tq.formula_process_mul_zb('飞龙在天', stock_list=[code], count=0)` ⚠️count必须=0

---

## 二、完整TDX选股公式源码（飞龙在天选股XG）

```text
XS1:=私募秘进 OR 暴涨启动条件;
XS2:=波段密码打板 OR 龙头战法条件;
X1:=XS1 AND XS2;
X2:=FINANCE(40)/100000000>20 AND FINANCE(40)/100000000<500;
去除ST:=NOT(NAMELIKE('ST') OR NAMELIKE('*ST') OR NAMELIKE('S'));
主板:=FINANCE(3)=1;
X3:=去除ST AND 主板;
X4:=AMO>100000000;
XG:X1 AND X2 AND X3 AND X4;
```

本地调用（XG）：`tq.formula_process_mul_xg('飞龙在天选股', stock_list=[code], count=0)` ⚠️公式名必须是`飞龙在天选股`

---

## 三、波/段数值体系（核心）

飞龙的波/段来自36日区间随机振荡体系：

```text
X_13=(CLOSE-LLV(LOW,36))/(HHV(HIGH,36)-LLV(LOW,36))*100
X_14=SMA(X_13,3,1)
波=X_15=SMA(X_14,3,1)
段=X_16=SMA(X_15,3,1)
```

**波/段是约0-100的波段振荡值，天然适合判断超买超卖和波段节奏。**

---

## 四、波段区间与含义

| 波/段区间 | 状态 | 含义 | 操作观察 |
|---|---|---|---|
| <20 | 超卖区 | 杀跌后低位 | 不直接买，等形成金叉+资金确认 |
| 20-50 | 修复区 | 反弹/启动初 | 观察是否转强 |
| 50-80 | 主升健康区 | 最优波段跟踪 | 重点跟踪资金同步 |
| >80 | 高位强势/超买 | 强者恒强或风险累积 | 不追高，看钝化背离 |
| >90 | 极强/过热 | 高位过热 | 持股/风控为主 |

---

## 五、波段操作状态

| 状态 | 条件 | 处理 |
|---|---|---|
| 低位转强 | 波<30且形成金叉 | 加入观察 |
| 修复确认 | 波在20-50,金叉 | 等大牛线/资金确认 |
| 主升健康 | 金叉,波段同步上行,波50-80 | 强关注 |
| 高位钝化 | 波>80且段跟随上行 | 不追高,持股观察 |
| 高位背离 | 股价新高但波不新高,或形成死叉 | 降权风控 |
| 退潮确认 | 形成死叉且跌破80/50 | 降级或剔除 |
| 超卖陷阱 | 波<20但未形成金叉 | 不因低位直接看多 |

---

## 六、爆发信号

| 信号 | TQ字段 | 含义 | 角色 |
|---|---|---|---|
| 私募秘进 | OUTPUT4 | 涨幅>4.8%+最高价收盘+温和放量 | 先行信号 |
| 暴涨启动 | OUTPUT5 | 大单净流入临界值 | 先行信号 |
| 波段密码打板 | OUTPUT3 | 涨停+平台突破+缩量整理 | 确认信号 |
| 龙头战法 | OUTPUT6 | 连阳后缩量涨停形态 | 辅助信号 |
| 主升启动 | OUTPUT7/XS1&XS2 | 双维度共振 | 核心爆发 |
| XG选股通过 | XG=1 | 选股条件满足 | 入池确认 |

---

## 七、标准化输出

飞龙波段输出：`低位转强/主升健康/高位钝化/高位背离/退潮确认/超卖未转强`

飞龙爆发输出：`私募秘进/暴涨启动/波段密码打板/龙头战法/主升启动/无`

双字段示例：`主升健康 + 主升启动`

---

## 八、云端使用说明

- 波/段数值可通过TQ接口获取（需通达信本地），或从K线数据手动计算X_13/X_15/X_16。
- 如无TQ，可从K线高低点和收盘价估算波段位置：`(Close-36日最低)/(36日最高-36日最低)*100`。
- XS1/XS2爆发信号在无TQ时需从涨幅、成交量、全档资金流手动判断。
