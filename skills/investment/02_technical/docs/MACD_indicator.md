# 技能文档：MACD指标（指数平滑异同平均线）

## 学习日期
2026-02-24

## 技能概述
MACD是最经典的技术指标之一，用于判断趋势方向、强度和反转信号。

---

## 一、概念定义

### 1.1 什么是MACD
MACD（Moving Average Convergence Divergence）通过计算两条不同周期的指数移动平均线（EMA）的差值，来判断价格趋势的强度和方向。

### 1.2 组成部分

| 组成部分 | 英文 | 说明 |
|----------|------|------|
| **DIF线** | Difference | 快速EMA - 慢速EMA |
| **DEA线** | Signal | DIF的9日EMA（信号线） |
| **MACD柱** | Histogram | (DIF - DEA) × 2 |

---

## 二、计算公式

### 2.1 EMA计算
```
EMA(n) = Price × k + EMA(previous) × (1-k)

其中：
- k = 2 / (n + 1)
- n = 周期（通常12和26）
```

### 2.2 MACD计算
```python
# 标准参数：12, 26, 9
EMA12 = 收盘价的12日指数移动平均
EMA26 = 收盘价的26日指数移动平均

DIF = EMA12 - EMA26
DEA = DIF的9日指数移动平均
MACD柱 = (DIF - DEA) × 2
```

---

## 三、信号解读

### 3.1 金叉死叉

| 信号 | 条件 | 含义 |
|------|------|------|
| **金叉** | DIF上穿DEA | 买入信号，趋势转多 |
| **死叉** | DIF下穿DEA | 卖出信号，趋势转空 |

**关键区分：**
- **零上金叉**：强势上涨，可靠买入
- **零下金叉**：弱势反弹，谨慎参与
- **零上死叉**：回调开始，减仓观望
- **零下死叉**：加速下跌，坚决卖出

### 3.2 背离信号

| 背离类型 | 价格 | MACD | 含义 |
|----------|------|------|------|
| **顶背离** | 创新高 | 未创新高 | 顶部预警，即将下跌 |
| **底背离** | 创新低 | 未创新低 | 底部预警，即将上涨 |

**背离确认：**
- 至少两个明显的价格高点/低点
- MACD相应位置对比
- 配合成交量验证

### 3.3 MACD柱分析

| 柱子状态 | 含义 |
|----------|------|
| **红柱放大** | 多头动能增强 |
| **红柱缩小** | 多头动能减弱 |
| **绿柱放大** | 空头动能增强 |
| **绿柱缩小** | 空头动能减弱 |
| **柱由绿转红** | 转多信号 |
| **柱由红转绿** | 转空信号 |

---

## 四、Python实现

```python
import pandas as pd
import numpy as np

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """
    计算MACD指标
    
    Parameters:
        prices: 收盘价序列
        fast: 快速EMA周期 (默认12)
        slow: 慢速EMA周期 (默认26)
        signal: 信号线周期 (默认9)
    
    Returns:
        DataFrame with DIF, DEA, MACD
    """
    # 计算EMA
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    
    # 计算DIF
    dif = ema_fast - ema_slow
    
    # 计算DEA（DIF的EMA）
    dea = dif.ewm(span=signal, adjust=False).mean()
    
    # 计算MACD柱
    macd = (dif - dea) * 2
    
    return pd.DataFrame({
        'DIF': dif,
        'DEA': dea,
        'MACD': macd
    })


def detect_macd_signals(df):
    """
    检测MACD交易信号
    
    Parameters:
        df: DataFrame with DIF, DEA columns
    
    Returns:
        DataFrame with signal column
    """
    signals = []
    
    for i in range(1, len(df)):
        # 金叉：DIF上穿DEA
        if df['DIF'].iloc[i-1] < df['DEA'].iloc[i-1] and \
           df['DIF'].iloc[i] >= df['DEA'].iloc[i]:
            signals.append('Golden Cross (BUY)')
        
        # 死叉：DIF下穿DEA
        elif df['DIF'].iloc[i-1] > df['DEA'].iloc[i-1] and \
             df['DIF'].iloc[i] <= df['DEA'].iloc[i]:
            signals.append('Death Cross (SELL)')
        
        else:
            signals.append('')
    
    signals.insert(0, '')  # 第一天无信号
    df['Signal'] = signals
    
    return df


def detect_divergence(prices, macd_values, window=20):
    """
    检测MACD背离
    
    Parameters:
        prices: 价格序列
        macd_values: MACD值（通常用DIF）
        window: 回溯窗口
    
    Returns:
        str: 'bullish_divergence', 'bearish_divergence', 'none'
    """
    # 获取近期高点/低点
    price_high = prices[-window:].max()
    price_low = prices[-window:].min()
    macd_high = macd_values[-window:].max()
    macd_low = macd_values[-window:].min()
    
    # 顶背离：价格新高，MACD未新高
    if prices.iloc[-1] >= price_high * 0.98 and \
       macd_values.iloc[-1] < macd_high * 0.95:
        return 'bearish_divergence'  # 看跌背离
    
    # 底背离：价格新低，MACD未新低
    if prices.iloc[-1] <= price_low * 1.02 and \
       macd_values.iloc[-1] > macd_low * 1.05:
        return 'bullish_divergence'  # 看涨背离
    
    return 'none'


# 实战示例
if __name__ == "__main__":
    # 模拟价格数据
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 0.5))
    
    # 计算MACD
    macd_df = calculate_macd(prices)
    
    # 检测信号
    signals_df = detect_macd_signals(macd_df.copy())
    
    # 打印最新信号
    latest_signal = signals_df['Signal'].iloc[-1]
    print(f"Latest MACD Signal: {latest_signal}")
    print(f"DIF: {signals_df['DIF'].iloc[-1]:.4f}")
    print(f"DEA: {signals_df['DEA'].iloc[-1]:.4f}")
    print(f"MACD: {signals_df['MACD'].iloc[-1]:.4f}")
```

---

## 五、实战案例

### 案例1：小米集团金叉信号

**场景：**
- 日期：2026-02-20
- DIF：-0.15
- DEA：-0.25
- 前一日：DIF(-0.20) < DEA(-0.18)

**分析：**
1. DIF从-0.20上升到-0.15
2. DEA从-0.18变化到-0.25
3. DIF上穿DEA → **金叉形成**
4. 在零轴下方（-0.15），属于**弱势金叉**

**操作建议：**
- 可小仓位试探性买入
- 需等待站上零轴确认强势
- 设置止损在前期低点下方

### 案例2：顶背离预警

**场景：**
- 股价：35.5 → 36.8 → 37.2（创新高）
- MACD(DIF)：0.45 → 0.42 → 0.38（未创新高）

**分析：**
1. 价格连续创新高
2. MACD未能同步创新高
3. **顶背离形成**，上涨动能减弱

**操作建议：**
- 考虑减仓或止盈
- 等待价格确认回调
- 若死叉出现，坚决卖出

---

## 六、注意事项

### 6.1 滞后性
MACD基于移动平均线，具有滞后性：
- 金叉出现时，价格可能已上涨一段
- 适合趋势确认，不适合捕捉拐点

### 6.2 震荡市失效
在横盘震荡行情中：
- 金叉死叉频繁出现
- 容易产生假信号
- 建议配合布林带或ADX使用

### 6.3 参数优化
默认参数(12,26,9)适合日线：
- 超短线：可调整为(6,13,5)
- 长线：可调整为(24,52,18)
- 需根据回测确定最优参数

---

## 七、进阶组合

### 7.1 MACD + RSI
- MACD判断趋势方向
- RSI判断超买超卖
- RSI超卖+MACD金叉 = 强买入信号

### 7.2 MACD + 布林带
- 布林带判断波动区间
- MACD判断趋势强度
- 价格触下轨+MACD金叉 = 反弹信号

---

## 学习总结

**核心要点：**
1. 理解DIF、DEA、MACD柱的含义
2. 掌握金叉死叉的四种形态
3. 学会识别顶背离和底背离
4. 知道MACD的滞后性和局限性

**掌握程度：** ⭐⭐⭐⭐⭐

**下一步学习：** RSI指标
