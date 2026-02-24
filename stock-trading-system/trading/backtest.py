"""
回测框架
完整的策略回测系统，支持多种评估指标
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TradeRecord:
    """交易记录"""
    timestamp: datetime
    action: str  # 'buy', 'sell', 'hold'
    price: float
    quantity: float
    value: float
    commission: float = 0.0
    signal: str = ''  # 交易信号来源
    

@dataclass
class BacktestResult:
    """回测结果"""
    # 收益指标
    total_return: float  # 总收益率
    annual_return: float  # 年化收益率
    daily_returns: pd.Series  # 每日收益率
    
    # 风险指标
    volatility: float  # 波动率
    max_drawdown: float  # 最大回撤
    max_drawdown_duration: int  # 最大回撤持续天数
    
    # 风险调整收益
    sharpe_ratio: float  # 夏普比率
    sortino_ratio: float  # 索提诺比率
    calmar_ratio: float  # 卡玛比率
    
    # 交易统计
    total_trades: int  # 总交易次数
    winning_trades: int  # 盈利次数
    losing_trades: int  # 亏损次数
    win_rate: float  # 胜率
    avg_win: float  # 平均盈利
    avg_loss: float  # 平均亏损
    profit_factor: float  # 盈亏比
    
    # 持仓信息
    equity_curve: pd.Series  # 权益曲线
    position_history: pd.DataFrame  # 持仓历史
    trade_history: List[TradeRecord]  # 交易历史
    
    # 基准对比
    benchmark_return: float  # 基准收益率
    alpha: float  # Alpha
    beta: float  # Beta
    information_ratio: float  # 信息比率


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, 
                 initial_capital: float = 100000.0,
                 commission_rate: float = 0.001,
                 slippage: float = 0.001):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金
            commission_rate: 手续费率
            slippage: 滑点
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        # 回测状态
        self.cash = initial_capital
        self.position = 0.0
        self.equity = initial_capital
        self.trades = []
        self.daily_stats = []
        
    def reset(self):
        """重置回测状态"""
        self.cash = self.initial_capital
        self.position = 0.0
        self.equity = self.initial_capital
        self.trades = []
        self.daily_stats = []
        logger.info("🔄 回测引擎已重置")
    
    def execute_trade(self, timestamp: datetime, action: str, 
                     price: float, quantity: Optional[float] = None,
                     signal: str = '') -> bool:
        """
        执行交易
        
        Args:
            timestamp: 交易时间
            action: 'buy', 'sell', 'close'
            price: 交易价格
            quantity: 交易数量（None表示全部）
            signal: 交易信号
        
        Returns:
            交易是否成功
        """
        # 应用滑点
        if action == 'buy':
            executed_price = price * (1 + self.slippage)
        else:  # sell or close
            executed_price = price * (1 - self.slippage)
        
        if action == 'buy':
            # 计算可买入数量
            max_quantity = self.cash / (executed_price * (1 + self.commission_rate))
            
            if quantity is None:
                quantity = max_quantity
            
            quantity = min(quantity, max_quantity)
            
            if quantity <= 0:
                return False
            
            cost = quantity * executed_price
            commission = cost * self.commission_rate
            total_cost = cost + commission
            
            self.cash -= total_cost
            self.position += quantity
            
            trade = TradeRecord(
                timestamp=timestamp,
                action='buy',
                price=executed_price,
                quantity=quantity,
                value=cost,
                commission=commission,
                signal=signal
            )
            self.trades.append(trade)
            
        elif action in ['sell', 'close']:
            if quantity is None or action == 'close':
                quantity = self.position
            
            quantity = min(quantity, self.position)
            
            if quantity <= 0:
                return False
            
            revenue = quantity * executed_price
            commission = revenue * self.commission_rate
            net_revenue = revenue - commission
            
            self.cash += net_revenue
            self.position -= quantity
            
            trade = TradeRecord(
                timestamp=timestamp,
                action='sell',
                price=executed_price,
                quantity=quantity,
                value=revenue,
                commission=commission,
                signal=signal
            )
            self.trades.append(trade)
        
        # 更新权益
        self.equity = self.cash + self.position * executed_price
        
        return True
    
    def record_daily_stats(self, timestamp: datetime, price: float):
        """记录每日统计"""
        self.equity = self.cash + self.position * price
        
        self.daily_stats.append({
            'timestamp': timestamp,
            'price': price,
            'cash': self.cash,
            'position': self.position,
            'equity': self.equity,
            'returns': (self.equity - self.initial_capital) / self.initial_capital
        })
    
    def run(self, df: pd.DataFrame, 
           signal_generator: Callable,
           start_date: Optional[str] = None,
           end_date: Optional[str] = None) -> BacktestResult:
        """
        运行回测
        
        Args:
            df: 包含价格数据的DataFrame
            signal_generator: 信号生成函数
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            回测结果
        """
        self.reset()
        
        # 数据筛选
        if start_date:
            df = df[df['timestamp'] >= start_date]
        if end_date:
            df = df[df['timestamp'] <= end_date]
        
        logger.info(f"🚀 开始回测: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
        logger.info(f"   数据条数: {len(df)}")
        
        # 获取基准价格
        benchmark_price = df['close'].iloc[0]
        
        # 逐日回测
        for idx, row in df.iterrows():
            timestamp = pd.to_datetime(row['timestamp'])
            price = row['close']
            
            # 生成交易信号
            signal = signal_generator(row, self.position, self.equity)
            
            # 执行交易
            if signal == 'buy' and self.position == 0:
                self.execute_trade(timestamp, 'buy', price, signal='model')
            elif signal == 'sell' and self.position > 0:
                self.execute_trade(timestamp, 'sell', price, quantity=self.position, signal='model')
            
            # 记录每日状态
            self.record_daily_stats(timestamp, price)
        
        # 平仓
        if self.position > 0:
            final_price = df['close'].iloc[-1]
            final_time = pd.to_datetime(df['timestamp'].iloc[-1])
            self.execute_trade(final_time, 'close', final_price, signal='end_of_backtest')
        
        logger.info(f"✅ 回测完成")
        
        # 计算回测结果
        return self._calculate_results(df)
    
    def _calculate_results(self, df: pd.DataFrame) -> BacktestResult:
        """计算回测结果指标"""
        stats_df = pd.DataFrame(self.daily_stats)
        
        if len(stats_df) == 0:
            raise ValueError("没有回测数据")
        
        stats_df.set_index('timestamp', inplace=True)
        
        # 权益曲线
        equity_curve = stats_df['equity']
        
        # 每日收益率
        daily_returns = equity_curve.pct_change().dropna()
        
        # 总收益率
        total_return = (equity_curve.iloc[-1] - self.initial_capital) / self.initial_capital
        
        # 年化收益率
        n_days = len(stats_df)
        annual_return = (1 + total_return) ** (252 / n_days) - 1
        
        # 波动率
        volatility = daily_returns.std() * np.sqrt(252)
        
        # 最大回撤
        rolling_max = equity_curve.cummax()
        drawdown = (equity_curve - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # 最大回撤持续时间
        is_drawdown = drawdown < 0
        drawdown_starts = is_drawdown.astype(int).diff().fillna(0).eq(1)
        drawdown_groups = drawdown_starts.cumsum()
        drawdown_durations = is_drawdown.groupby(drawdown_groups).sum()
        max_drawdown_duration = drawdown_durations.max() if len(drawdown_durations) > 0 else 0
        
        # 夏普比率（假设无风险利率为3%）
        risk_free_rate = 0.03
        if volatility > 0:
            sharpe_ratio = (annual_return - risk_free_rate) / volatility
        else:
            sharpe_ratio = 0
        
        # 索提诺比率
        downside_returns = daily_returns[daily_returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        if downside_std > 0:
            sortino_ratio = (annual_return - risk_free_rate) / downside_std
        else:
            sortino_ratio = 0
        
        # 卡玛比率
        if max_drawdown < 0:
            calmar_ratio = annual_return / abs(max_drawdown)
        else:
            calmar_ratio = 0
        
        # 交易统计
        trade_df = pd.DataFrame([
            {
                'timestamp': t.timestamp,
                'action': t.action,
                'price': t.price,
                'quantity': t.quantity,
                'value': t.value,
                'commission': t.commission
            }
            for t in self.trades
        ])
        
        if len(trade_df) > 0:
            # 配对买卖计算盈亏
            trades_list = []
            current_position = 0
            entry_price = 0
            entry_value = 0
            
            for _, trade in trade_df.iterrows():
                if trade['action'] == 'buy':
                    if current_position == 0:
                        entry_price = trade['price']
                        entry_value = trade['value']
                    else:
                        # 加仓，计算加权平均成本
                        total_value = entry_value + trade['value']
                        total_quantity = current_position + trade['quantity']
                        entry_price = total_value / total_quantity
                        entry_value = total_value
                    current_position += trade['quantity']
                    
                elif trade['action'] in ['sell', 'close'] and current_position > 0:
                    pnl = (trade['price'] - entry_price) * trade['quantity'] - trade['commission']
                    trades_list.append({
                        'pnl': pnl,
                        'return_pct': pnl / entry_value * 100 if entry_value > 0 else 0
                    })
                    current_position -= trade['quantity']
            
            if len(trades_list) > 0:
                trades_summary = pd.DataFrame(trades_list)
                total_trades = len(trades_summary)
                winning_trades = (trades_summary['pnl'] > 0).sum()
                losing_trades = (trades_summary['pnl'] < 0).sum()
                win_rate = winning_trades / total_trades if total_trades > 0 else 0
                avg_win = trades_summary[trades_summary['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
                avg_loss = abs(trades_summary[trades_summary['pnl'] < 0]['pnl'].mean()) if losing_trades > 0 else 1
                profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
            else:
                total_trades = winning_trades = losing_trades = 0
                win_rate = avg_win = avg_loss = profit_factor = 0
        else:
            total_trades = winning_trades = losing_trades = 0
            win_rate = avg_win = avg_loss = profit_factor = 0
        
        # 基准对比
        benchmark_return = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]
        
        # Beta (简化计算)
        stock_returns = df['close'].pct_change().dropna()
        benchmark_returns = stock_returns  # 假设基准就是股票本身
        if len(stock_returns) > 1:
            covariance = np.cov(stock_returns, benchmark_returns)[0][1]
            benchmark_variance = np.var(benchmark_returns)
            beta = covariance / benchmark_variance if benchmark_variance > 0 else 1
        else:
            beta = 1
        
        # Alpha
        alpha = annual_return - (0.03 + beta * (benchmark_return * 252 / n_days - 0.03))
        
        # 信息比率
        tracking_error = (daily_returns - stock_returns).std() * np.sqrt(252)
        information_ratio = (annual_return - benchmark_return * 252 / n_days) / tracking_error if tracking_error > 0 else 0
        
        return BacktestResult(
            total_return=total_return,
            annual_return=annual_return,
            daily_returns=daily_returns,
            volatility=volatility,
            max_drawdown=max_drawdown,
            max_drawdown_duration=int(max_drawdown_duration),
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            equity_curve=equity_curve,
            position_history=stats_df,
            trade_history=self.trades,
            benchmark_return=benchmark_return,
            alpha=alpha,
            beta=beta,
            information_ratio=information_ratio
        )
    
    def plot_results(self, result: BacktestResult, save_path: Optional[str] = None):
        """可视化回测结果"""
        try:
            import matplotlib.pyplot as plt
            
            fig, axes = plt.subplots(3, 1, figsize=(12, 10))
            
            # 1. 权益曲线
            ax1 = axes[0]
            result.equity_curve.plot(ax=ax1, label='Strategy', linewidth=2)
            
            # 基准
            initial = result.equity_curve.iloc[0]
            benchmark = initial * (1 + result.benchmark_return * 
                                 np.arange(len(result.equity_curve)) / len(result.equity_curve))
            ax1.plot(result.equity_curve.index, benchmark, '--', label='Benchmark', alpha=0.7)
            
            ax1.set_title('Equity Curve')
            ax1.set_ylabel('Portfolio Value')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 2. 回撤
            ax2 = axes[1]
            rolling_max = result.equity_curve.cummax()
            drawdown = (result.equity_curve - rolling_max) / rolling_max
            drawdown.plot(ax=ax2, color='red', alpha=0.7)
            ax2.fill_between(drawdown.index, drawdown, 0, color='red', alpha=0.3)
            ax2.set_title('Drawdown')
            ax2.set_ylabel('Drawdown')
            ax2.grid(True, alpha=0.3)
            
            # 3. 每日收益分布
            ax3 = axes[2]
            result.daily_returns.hist(ax=ax3, bins=50, alpha=0.7, edgecolor='black')
            ax3.axvline(result.daily_returns.mean(), color='red', linestyle='--', 
                       label=f'Mean: {result.daily_returns.mean():.4f}')
            ax3.set_title('Daily Returns Distribution')
            ax3.set_xlabel('Daily Return')
            ax3.set_ylabel('Frequency')
            ax3.legend()
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"📊 回测图已保存: {save_path}")
            
            plt.show()
            
        except ImportError:
            logger.warning("⚠️ matplotlib未安装，无法绘图")
    
    def generate_report(self, result: BacktestResult) -> str:
        """生成回测报告"""
        report = []
        report.append("="*70)
        report.append("回测报告")
        report.append("="*70)
        
        report.append(f"\n【收益指标】")
        report.append(f"  总收益率: {result.total_return*100:.2f}%")
        report.append(f"  年化收益率: {result.annual_return*100:.2f}%")
        report.append(f"  基准收益率: {result.benchmark_return*100:.2f}%")
        report.append(f"  Alpha: {result.alpha:.4f}")
        report.append(f"  Beta: {result.beta:.4f}")
        
        report.append(f"\n【风险指标】")
        report.append(f"  波动率: {result.volatility*100:.2f}%")
        report.append(f"  最大回撤: {result.max_drawdown*100:.2f}%")
        report.append(f"  最大回撤持续: {result.max_drawdown_duration} 天")
        
        report.append(f"\n【风险调整收益】")
        report.append(f"  夏普比率: {result.sharpe_ratio:.4f}")
        report.append(f"  索提诺比率: {result.sortino_ratio:.4f}")
        report.append(f"  卡玛比率: {result.calmar_ratio:.4f}")
        report.append(f"  信息比率: {result.information_ratio:.4f}")
        
        report.append(f"\n【交易统计】")
        report.append(f"  总交易次数: {result.total_trades}")
        report.append(f"  盈利次数: {result.winning_trades}")
        report.append(f"  亏损次数: {result.losing_trades}")
        report.append(f"  胜率: {result.win_rate*100:.2f}%")
        report.append(f"  盈亏比: {result.profit_factor:.2f}")
        
        report.append("\n" + "="*70)
        
        return "\n".join(report)


# 使用示例
if __name__ == "__main__":
    print("="*70)
    print("回测框架")
    print("="*70)
    
    # 示例：简单的信号生成函数
    def simple_signal(row, position, equity):
        """简单动量策略"""
        if 'sma_20' not in row or 'close' not in row:
            return 'hold'
        
        if row['close'] > row['sma_20'] and position == 0:
            return 'buy'
        elif row['close'] < row['sma_20'] and position > 0:
            return 'sell'
        
        return 'hold'
    
    print("\n✅ 回测框架就绪")
    print("   • 支持多种订单类型")
    print("   • 完整的绩效评估指标")
    print("   • 可视化和报告生成")
    print("="*70)
