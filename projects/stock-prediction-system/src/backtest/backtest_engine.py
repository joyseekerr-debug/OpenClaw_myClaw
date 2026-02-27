"""
股价预测系统 - 回测引擎
历史数据回测，验证预测准确率
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """交易记录"""
    entry_time: datetime
    entry_price: float
    direction: str  # 'long' 或 'short'
    size: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    status: str = 'open'  # 'open', 'closed', 'stopped'


@dataclass
class BacktestResult:
    """回测结果"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    total_return: float
    total_return_pct: float
    equity_curve: List[float] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self,
                 initial_capital: float = 100000,
                 commission: float = 0.001,
                 slippage: float = 0.001,
                 position_size: float = 0.1):
        """
        Args:
            initial_capital: 初始资金
            commission: 手续费 (0.001 = 0.1%)
            slippage: 滑点 (0.001 = 0.1%)
            position_size: 仓位大小 (0.1 = 10%)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.position_size = position_size
        
        self.capital = initial_capital
        self.equity_curve = [initial_capital]
        self.trades = []
        self.current_position = None
    
    def run_backtest(self, 
                     df: pd.DataFrame,
                     predictions: List[Dict],
                     stop_loss: float = 0.02,
                     take_profit: float = 0.05) -> BacktestResult:
        """
        运行回测
        
        Args:
            df: 历史价格数据
            predictions: 预测信号列表 [{time, signal, confidence}, ...]
            stop_loss: 止损比例
            take_profit: 止盈比例
        
        Returns:
            回测结果
        """
        logger.info(f"Starting backtest with {len(predictions)} predictions...")
        
        for i, pred in enumerate(predictions):
            if i >= len(df):
                break
            
            current_price = df['close'].iloc[i]
            current_time = df.index[i]
            
            # 检查当前持仓
            if self.current_position:
                # 检查止损止盈
                exit_price = self._check_exit(
                    self.current_position, current_price, 
                    stop_loss, take_profit
                )
                
                if exit_price:
                    self._close_trade(
                        self.current_position, current_time, exit_price
                    )
                    self.current_position = None
            
            # 开新仓
            if not self.current_position:
                signal = pred.get('signal', 'hold')
                confidence = pred.get('confidence', 0)
                
                if signal != 'hold' and confidence > 0.55:
                    direction = 'long' if signal == 'buy' else 'short'
                    self.current_position = self._open_trade(
                        current_time, current_price, direction
                    )
            
            # 记录权益曲线
            self._update_equity(current_price)
        
        # 关闭未平仓的交易
        if self.current_position:
            final_price = df['close'].iloc[-1]
            final_time = df.index[-1]
            self._close_trade(self.current_position, final_time, final_price)
        
        # 计算绩效指标
        result = self._calculate_metrics()
        
        logger.info("Backtest completed")
        
        return result
    
    def _open_trade(self, time: datetime, price: float, 
                   direction: str) -> Trade:
        """开仓"""
        # 应用滑点
        if direction == 'long':
            entry_price = price * (1 + self.slippage)
        else:
            entry_price = price * (1 - self.slippage)
        
        # 计算仓位
        position_value = self.capital * self.position_size
        size = position_value / entry_price
        
        # 扣除手续费
        commission_cost = position_value * self.commission
        self.capital -= commission_cost
        
        trade = Trade(
            entry_time=time,
            entry_price=entry_price,
            direction=direction,
            size=size
        )
        
        self.trades.append(trade)
        
        return trade
    
    def _close_trade(self, trade: Trade, time: datetime, price: float):
        """平仓"""
        # 应用滑点
        if trade.direction == 'long':
            exit_price = price * (1 - self.slippage)
        else:
            exit_price = price * (1 + self.slippage)
        
        trade.exit_time = time
        trade.exit_price = exit_price
        trade.status = 'closed'
        
        # 计算盈亏
        if trade.direction == 'long':
            trade.pnl = (exit_price - trade.entry_price) * trade.size
            trade.pnl_pct = (exit_price - trade.entry_price) / trade.entry_price
        else:
            trade.pnl = (trade.entry_price - exit_price) * trade.size
            trade.pnl_pct = (trade.entry_price - exit_price) / trade.entry_price
        
        # 扣除手续费
        position_value = trade.size * exit_price
        commission_cost = position_value * self.commission
        trade.pnl -= commission_cost
        
        # 更新资金
        self.capital += trade.pnl
    
    def _check_exit(self, trade: Trade, current_price: float,
                   stop_loss: float, take_profit: float) -> Optional[float]:
        """检查是否需要平仓"""
        if trade.direction == 'long':
            # 止损
            stop_price = trade.entry_price * (1 - stop_loss)
            if current_price <= stop_price:
                trade.status = 'stopped'
                return stop_price
            
            # 止盈
            profit_price = trade.entry_price * (1 + take_profit)
            if current_price >= profit_price:
                return profit_price
        
        else:  # short
            # 止损
            stop_price = trade.entry_price * (1 + stop_loss)
            if current_price >= stop_price:
                trade.status = 'stopped'
                return stop_price
            
            # 止盈
            profit_price = trade.entry_price * (1 - take_profit)
            if current_price <= profit_price:
                return profit_price
        
        return None
    
    def _update_equity(self, current_price: float):
        """更新权益曲线"""
        if self.current_position:
            if self.current_position.direction == 'long':
                unrealized_pnl = (current_price - self.current_position.entry_price) * self.current_position.size
            else:
                unrealized_pnl = (self.current_position.entry_price - current_price) * self.current_position.size
            
            total_equity = self.capital + unrealized_pnl
        else:
            total_equity = self.capital
        
        self.equity_curve.append(total_equity)
    
    def _calculate_metrics(self) -> BacktestResult:
        """计算绩效指标"""
        closed_trades = [t for t in self.trades if t.status == 'closed']
        
        if not closed_trades:
            return BacktestResult(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0,
                avg_win=0,
                avg_loss=0,
                profit_factor=0,
                sharpe_ratio=0,
                max_drawdown=0,
                max_drawdown_pct=0,
                total_return=0,
                total_return_pct=0
            )
        
        # 基础统计
        total_trades = len(closed_trades)
        winning_trades = sum(1 for t in closed_trades if t.pnl > 0)
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 盈亏统计
        wins = [t.pnl for t in closed_trades if t.pnl > 0]
        losses = [t.pnl for t in closed_trades if t.pnl <= 0]
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        
        # 盈亏比
        total_wins = sum(wins)
        total_losses = abs(sum(losses))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # 最大回撤
        equity_array = np.array(self.equity_curve)
        rolling_max = np.maximum.accumulate(equity_array)
        drawdown = equity_array - rolling_max
        max_drawdown = np.min(drawdown)
        max_drawdown_pct = max_drawdown / rolling_max[np.argmin(drawdown)] if np.min(drawdown) != 0 else 0
        
        # 夏普比率 (简化版，假设无风险利率为0)
        returns = np.diff(equity_array) / equity_array[:-1]
        if len(returns) > 1 and np.std(returns) > 0:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)  # 年化
        else:
            sharpe_ratio = 0
        
        # 总收益
        total_return = self.equity_curve[-1] - self.initial_capital
        total_return_pct = total_return / self.initial_capital
        
        return BacktestResult(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            total_return=total_return,
            total_return_pct=total_return_pct,
            equity_curve=self.equity_curve,
            trades=self.trades
        )


class PerformanceMetrics:
    """绩效指标计算"""
    
    @staticmethod
    def calculate_all_metrics(result: BacktestResult) -> Dict:
        """计算所有指标"""
        return {
            '总交易次数': result.total_trades,
            '胜率': f"{result.win_rate:.2%}",
            '盈亏比': f"{result.profit_factor:.2f}",
            '平均盈利': f"${result.avg_win:.2f}",
            '平均亏损': f"${result.avg_loss:.2f}",
            '夏普比率': f"{result.sharpe_ratio:.2f}",
            '最大回撤': f"${result.max_drawdown:.2f}",
            '最大回撤比例': f"{result.max_drawdown_pct:.2%}",
            '总收益': f"${result.total_return:.2f}",
            '总收益率': f"{result.total_return_pct:.2%}"
        }


# 便捷函数
def run_backtest(df: pd.DataFrame, predictions: List[Dict],
                initial_capital: float = 100000) -> BacktestResult:
    """便捷函数：运行回测"""
    engine = BacktestEngine(initial_capital=initial_capital)
    return engine.run_backtest(df, predictions)


if __name__ == '__main__':
    print("Backtest Engine Module")
    
    # 测试代码
    import sys
    sys.path.append('..')
    
    # 模拟数据
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'open': np.random.randn(100).cumsum() + 20,
        'high': np.random.randn(100).cumsum() + 21,
        'low': np.random.randn(100).cumsum() + 19,
        'close': np.random.randn(100).cumsum() + 20,
        'volume': np.random.randint(1000000, 5000000, 100)
    }, index=dates)
    
    # 模拟预测信号
    predictions = [
        {'signal': 'buy' if i % 3 == 0 else 'sell' if i % 3 == 1 else 'hold', 
         'confidence': 0.6 + np.random.random() * 0.3}
        for i in range(100)
    ]
    
    # 回测
    result = run_backtest(df, predictions)
    
    print("\nBacktest Results:")
    metrics = PerformanceMetrics.calculate_all_metrics(result)
    for key, value in metrics.items():
        print(f"  {key}: {value}")
