"""
MACD指标实战代码
包含计算、信号检测、背离识别
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple, List, Optional


class MACDIndicator:
    """MACD指标计算器"""
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        """
        初始化MACD计算器
        
        Args:
            fast: 快速EMA周期
            slow: 慢速EMA周期
            signal: 信号线周期
        """
        self.fast = fast
        self.slow = slow
        self.signal = signal
    
    def calculate(self, prices: pd.Series) -> pd.DataFrame:
        """
        计算MACD指标
        
        Args:
            prices: 收盘价序列
            
        Returns:
            DataFrame with ['DIF', 'DEA', 'MACD']
        """
        # 计算EMA
        ema_fast = prices.ewm(span=self.fast, adjust=False).mean()
        ema_slow = prices.ewm(span=self.slow, adjust=False).mean()
        
        # DIF线
        dif = ema_fast - ema_slow
        
        # DEA线（DIF的EMA）
        dea = dif.ewm(span=self.signal, adjust=False).mean()
        
        # MACD柱
        macd = (dif - dea) * 2
        
        return pd.DataFrame({
            'DIF': dif,
            'DEA': dea,
            'MACD': macd
        })
    
    def detect_cross(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        检测金叉死叉信号
        
        Args:
            df: DataFrame with DIF and DEA columns
            
        Returns:
            DataFrame with 'Cross_Signal' column
        """
        df = df.copy()
        df['Cross_Signal'] = 0  # 0: 无信号, 1: 金叉, -1: 死叉
        
        # 检测交叉
        for i in range(1, len(df)):
            # 金叉：DIF上穿DEA
            if df['DIF'].iloc[i-1] < df['DEA'].iloc[i-1] and \
               df['DIF'].iloc[i] >= df['DEA'].iloc[i]:
                df.loc[df.index[i], 'Cross_Signal'] = 1
            
            # 死叉：DIF下穿DEA
            elif df['DIF'].iloc[i-1] > df['DEA'].iloc[i-1] and \
                 df['DIF'].iloc[i] <= df['DEA'].iloc[i]:
                df.loc[df.index[i], 'Cross_Signal'] = -1
        
        return df
    
    def detect_divergence(self, prices: pd.Series, dif: pd.Series, 
                          window: int = 20) -> List[dict]:
        """
        检测MACD背离
        
        Args:
            prices: 价格序列
            dif: DIF线
            window: 回溯窗口
            
        Returns:
            List of divergence signals
        """
        divergences = []
        
        for i in range(window, len(prices)):
            # 获取窗口内的数据
            price_window = prices.iloc[i-window:i]
            dif_window = dif.iloc[i-window:i]
            
            # 找局部极值
            price_max_idx = price_window.idxmax()
            price_min_idx = price_window.idxmin()
            dif_max_idx = dif_window.idxmax()
            dif_min_idx = dif_window.idxmin()
            
            # 顶背离：价格新高，DIF未新高
            if prices.iloc[i] >= price_window.max() * 0.99 and \
               dif.iloc[i] < dif_window.max() * 0.95:
                divergences.append({
                    'index': i,
                    'type': 'bearish',
                    'price': prices.iloc[i],
                    'dif': dif.iloc[i],
                    'message': '顶背离预警：价格新高，动能减弱'
                })
            
            # 底背离：价格新低，DIF未新低
            elif prices.iloc[i] <= price_window.min() * 1.01 and \
                 dif.iloc[i] > dif_window.min() * 1.05:
                divergences.append({
                    'index': i,
                    'type': 'bullish',
                    'price': prices.iloc[i],
                    'dif': dif.iloc[i],
                    'message': '底背离预警：价格新低，动能增强'
                })
        
        return divergences
    
    def get_signal_strength(self, df: pd.DataFrame) -> str:
        """
        评估当前信号强度
        
        Args:
            df: DataFrame with MACD data
            
        Returns:
            信号强度描述
        """
        latest = df.iloc[-1]
        dif = latest['DIF']
        dea = latest['DEA']
        macd = latest['MACD']
        
        # 判断零轴位置
        if dif > 0 and dea > 0:
            zone = "零上（强势区）"
        elif dif < 0 and dea < 0:
            zone = "零下（弱势区）"
        else:
            zone = "零轴附近（转换区）"
        
        # 判断趋势
        if dif > dea:
            trend = "多头趋势"
            if macd > 0 and macd > df['MACD'].iloc[-2]:
                strength = "强势上涨"
            else:
                strength = "上涨减弱"
        else:
            trend = "空头趋势"
            if macd < 0 and macd < df['MACD'].iloc[-2]:
                strength = "强势下跌"
            else:
                strength = "下跌减弱"
        
        return f"{zone} | {trend} | {strength}"
    
    def plot(self, prices: pd.Series, macd_df: pd.DataFrame, 
             title: str = "MACD Indicator"):
        """
        绘制MACD图表
        
        Args:
            prices: 价格序列
            macd_df: MACD数据
            title: 图表标题
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), 
                                        gridspec_kw={'height_ratios': [2, 1]})
        
        # 绘制价格
        ax1.plot(prices.index, prices.values, label='Price', color='black')
        ax1.set_title(title)
        ax1.set_ylabel('Price')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 绘制MACD
        ax2.plot(macd_df.index, macd_df['DIF'], label='DIF', color='blue')
        ax2.plot(macd_df.index, macd_df['DEA'], label='DEA', color='orange')
        
        # 绘制MACD柱
        colors = ['green' if v >= 0 else 'red' for v in macd_df['MACD']]
        ax2.bar(macd_df.index, macd_df['MACD'], label='MACD', color=colors, alpha=0.6)
        
        # 零轴线
        ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        
        ax2.set_ylabel('MACD')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()


# 测试代码
if __name__ == "__main__":
    # 生成测试数据
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    
    # 模拟股价走势
    trend = np.linspace(0, 10, 100)
    noise = np.cumsum(np.random.randn(100) * 0.5)
    prices = pd.Series(100 + trend + noise, index=dates)
    
    # 计算MACD
    macd = MACDIndicator(fast=12, slow=26, signal=9)
    macd_df = macd.calculate(prices)
    
    # 检测交叉信号
    signals_df = macd.detect_cross(macd_df)
    
    # 检测背离
    divergences = macd.detect_divergence(prices, macd_df['DIF'])
    
    # 打印结果
    print("="*60)
    print("MACD Analysis Results")
    print("="*60)
    print(f"\nLatest MACD Data:")
    print(f"  DIF: {macd_df['DIF'].iloc[-1]:.4f}")
    print(f"  DEA: {macd_df['DEA'].iloc[-1]:.4f}")
    print(f"  MACD: {macd_df['MACD'].iloc[-1]:.4f}")
    
    print(f"\nSignal Strength:")
    print(f"  {macd.get_signal_strength(macd_df)}")
    
    print(f"\nLatest Cross Signals:")
    cross_signals = signals_df[signals_df['Cross_Signal'] != 0]
    if len(cross_signals) > 0:
        for idx, row in cross_signals.tail(3).iterrows():
            signal_type = "金叉" if row['Cross_Signal'] == 1 else "死叉"
            print(f"  {idx.strftime('%Y-%m-%d')}: {signal_type}")
    else:
        print("  近期无交叉信号")
    
    print(f"\nDivergence Signals:")
    if divergences:
        for div in divergences[-3:]:
            print(f"  {div['message']} @ {div['price']:.2f}")
    else:
        print("  近期无背离信号")
    
    print("="*60)
