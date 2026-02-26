"""
股票市场运作机制 - 核心功能模块
包含：交易撮合、价格计算、费率计算、市场模拟等功能
"""

import sys
import io
# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import heapq
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime, time
import random


class OrderType(Enum):
    """订单类型"""
    LIMIT = "限价单"
    MARKET = "市价单"
    STOP_LOSS = "止损单"
    STOP_LIMIT = "止损限价单"


class OrderSide(Enum):
    """买卖方向"""
    BUY = "买入"
    SELL = "卖出"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "待成交"
    PARTIAL = "部分成交"
    FILLED = "全部成交"
    CANCELLED = "已撤单"


@dataclass
class Order:
    """订单类"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    price: Optional[float]
    quantity: int
    timestamp: datetime = field(default_factory=datetime.now)
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    
    @property
    def remaining_quantity(self) -> int:
        """剩余未成交数量"""
        return self.quantity - self.filled_quantity
    
    @property
    def is_filled(self) -> bool:
        """是否全部成交"""
        return self.filled_quantity >= self.quantity
    
    def __lt__(self, other):
        """用于优先队列排序"""
        if self.side == OrderSide.BUY:
            # 买入：价格高的优先，同价格时间早的优先
            if self.price != other.price:
                return self.price > other.price
            return self.timestamp < other.timestamp
        else:
            # 卖出：价格低的优先，同价格时间早的优先
            if self.price != other.price:
                return self.price < other.price
            return self.timestamp < other.timestamp


@dataclass
class Trade:
    """成交记录"""
    trade_id: str
    symbol: str
    buy_order_id: str
    sell_order_id: str
    price: float
    quantity: int
    timestamp: datetime
    
    def __repr__(self):
        return f"Trade({self.symbol} @ {self.price:.2f} × {self.quantity})"


class OrderBook:
    """
    订单簿 - 实现价格优先、时间优先的撮合机制
    """
    
    def __init__(self, symbol: str, verbose: bool = True):
        self.symbol = symbol
        self.verbose = verbose
        self.bids: List[Order] = []  # 买单队列 (优先队列)
        self.asks: List[Order] = []  # 卖单队列 (优先队列)
        self.trades: List[Trade] = []
        self.trade_counter = 0
    
    def add_order(self, order: Order) -> List[Trade]:
        """
        添加订单并进行撮合
        返回成交记录列表
        """
        new_trades = []
        
        if order.side == OrderSide.BUY:
            # 尝试与卖单撮合
            while order.remaining_quantity > 0 and self.asks:
                best_ask = self.asks[0]
                
                # 价格判断：买价 >= 卖价才能成交
                if order.price and best_ask.price and order.price < best_ask.price:
                    break
                
                # 撮合
                trade_qty = min(order.remaining_quantity, best_ask.remaining_quantity)
                trade_price = best_ask.price if best_ask.price else order.price
                
                trade = Trade(
                    trade_id=f"T{self.trade_counter:06d}",
                    symbol=self.symbol,
                    buy_order_id=order.order_id,
                    sell_order_id=best_ask.order_id,
                    price=trade_price,
                    quantity=trade_qty,
                    timestamp=datetime.now()
                )
                
                self.trades.append(trade)
                new_trades.append(trade)
                self.trade_counter += 1
                
                # 更新订单状态
                order.filled_quantity += trade_qty
                best_ask.filled_quantity += trade_qty
                
                # 移除完全成交的卖单
                if best_ask.is_filled:
                    heapq.heappop(self.asks)
                
                if self.verbose:
                    print(f"  [成交] {trade}")
            
            # 未完全成交的加入买单队列
            if not order.is_filled and order.order_type == OrderType.LIMIT:
                heapq.heappush(self.bids, order)
                if self.verbose:
                    print(f"  [挂单] 买入: {order.price:.2f}元 x {order.remaining_quantity}股")
        
        else:  # SELL
            # 尝试与买单撮合
            while order.remaining_quantity > 0 and self.bids:
                best_bid = self.bids[0]
                
                # 价格判断：卖价 <= 买价才能成交
                if order.price and best_bid.price and order.price > best_bid.price:
                    break
                
                # 撮合
                trade_qty = min(order.remaining_quantity, best_bid.remaining_quantity)
                trade_price = best_bid.price if best_bid.price else order.price
                
                trade = Trade(
                    trade_id=f"T{self.trade_counter:06d}",
                    symbol=self.symbol,
                    buy_order_id=best_bid.order_id,
                    sell_order_id=order.order_id,
                    price=trade_price,
                    quantity=trade_qty,
                    timestamp=datetime.now()
                )
                
                self.trades.append(trade)
                new_trades.append(trade)
                self.trade_counter += 1
                
                # 更新订单状态
                order.filled_quantity += trade_qty
                best_bid.filled_quantity += trade_qty
                
                # 移除完全成交的买单
                if best_bid.is_filled:
                    heapq.heappop(self.bids)
                
                if self.verbose:
                    print(f"  [成交] {trade}")
            
            # 未完全成交的加入卖单队列
            if not order.is_filled and order.order_type == OrderType.LIMIT:
                heapq.heappush(self.asks, order)
                if self.verbose:
                    print(f"  [挂单] 卖出: {order.price:.2f}元 x {order.remaining_quantity}股")
        
        if order.is_filled:
            order.status = OrderStatus.FILLED
        elif order.filled_quantity > 0:
            order.status = OrderStatus.PARTIAL
        
        return new_trades
    
    def get_market_depth(self, levels: int = 5) -> Dict:
        """获取市场深度（买卖五档）"""
        bids_depth = []
        asks_depth = []
        
        # 汇总买单
        bid_prices = {}
        for order in self.bids:
            price = order.price
            if price not in bid_prices:
                bid_prices[price] = 0
            bid_prices[price] += order.remaining_quantity
        
        # 汇总卖单
        ask_prices = {}
        for order in self.asks:
            price = order.price
            if price not in ask_prices:
                ask_prices[price] = 0
            ask_prices[price] += order.remaining_quantity
        
        # 排序并取前N档
        sorted_bids = sorted(bid_prices.items(), key=lambda x: x[0], reverse=True)[:levels]
        sorted_asks = sorted(ask_prices.items(), key=lambda x: x[0])[:levels]
        
        return {
            "bids": [{"price": p, "quantity": q} for p, q in sorted_bids],
            "asks": [{"price": p, "quantity": q} for p, q in sorted_asks],
            "spread": sorted_asks[0][0] - sorted_bids[0][0] if sorted_asks and sorted_bids else None
        }
    
    def display_book(self):
        """显示当前订单簿"""
        if not self.verbose:
            return
            
        depth = self.get_market_depth()
        
        print(f"\n{'='*50}")
        print(f"  {self.symbol} 订单簿")
        print(f"{'='*50}")
        
        print("\n  卖盘 (Ask):")
        for level in reversed(depth["asks"]):
            print(f"    {level['price']:>8.2f}  {level['quantity']:>6}股")
        
        print(f"  {'─'*30}")
        
        print("  买盘 (Bid):")
        for level in depth["bids"]:
            print(f"    {level['price']:>8.2f}  {level['quantity']:>6}股")
        
        if depth["spread"]:
            print(f"\n  买卖价差: {depth['spread']:.2f}元")
        print(f"{'='*50}\n")


class HKStockConnector:
    """
    港股通费率计算器
    """
    
    # 港股通费率结构
    FEES = {
        "stamp_duty": 0.001,        # 印花税 0.1%
        "trading_fee": 0.00005,     # 交易费 0.005%
        "settlement_fee": 0.00002,  # 交收费 0.002%
        "levy": 0.000027,           # 交易征费 0.0027%
        "commission_min": 15,       # 最低佣金 15港币
        "commission_rate": 0.0003,  # 佣金费率 0.03%
    }
    
    def __init__(self, exchange_rate: float = 0.92):
        """
        初始化港股通连接器
        
        Args:
            exchange_rate: 港币兑人民币汇率
        """
        self.exchange_rate = exchange_rate
    
    def calculate_fees(self, amount_hkd: float, is_buy: bool = True) -> Dict:
        """
        计算交易费用
        
        Args:
            amount_hkd: 交易金额（港币）
            is_buy: 是否为买入
        
        Returns:
            费用明细字典
        """
        fees = {}
        
        # 印花税（买卖双向）
        fees["stamp_duty"] = amount_hkd * self.FEES["stamp_duty"]
        
        # 交易费
        fees["trading_fee"] = amount_hkd * self.FEES["trading_fee"]
        
        # 交收费
        fees["settlement_fee"] = amount_hkd * self.FEES["settlement_fee"]
        
        # 交易征费
        fees["levy"] = amount_hkd * self.FEES["levy"]
        
        # 佣金
        commission = max(
            amount_hkd * self.FEES["commission_rate"],
            self.FEES["commission_min"]
        )
        fees["commission"] = commission
        
        # 总费用
        fees["total_hkd"] = sum(fees.values())
        fees["total_cny"] = fees["total_hkd"] * self.exchange_rate
        
        # 成本占比
        fees["cost_ratio"] = (fees["total_hkd"] / amount_hkd) * 100
        
        return fees
    
    def calculate_settlement(
        self, 
        shares: int, 
        price_hkd: float,
        ref_exchange_rate: float,
        settle_exchange_rate: float
    ) -> Dict:
        """
        计算港股通结算金额和汇率差异
        
        Args:
            shares: 股数
            price_hkd: 每股价格（港币）
            ref_exchange_rate: 参考汇率（冻结资金用）
            settle_exchange_rate: 结算汇率（实际交收用）
        
        Returns:
            结算明细
        """
        amount_hkd = shares * price_hkd
        
        # 计算费用
        fees = self.calculate_fees(amount_hkd)
        total_hkd = amount_hkd + fees["total_hkd"]
        
        # 冻结资金（使用参考汇率）
        frozen_cny = total_hkd * ref_exchange_rate
        
        # 实际支付（使用结算汇率）
        actual_cny = total_hkd * settle_exchange_rate
        
        # 汇率差异
        exchange_diff = frozen_cny - actual_cny
        
        return {
            "shares": shares,
            "price_hkd": price_hkd,
            "amount_hkd": amount_hkd,
            "fees_hkd": fees,
            "total_hkd": total_hkd,
            "ref_exchange_rate": ref_exchange_rate,
            "settle_exchange_rate": settle_exchange_rate,
            "frozen_cny": frozen_cny,
            "actual_cny": actual_cny,
            "exchange_diff": exchange_diff,
            "exchange_diff_pct": (exchange_diff / frozen_cny) * 100
        }
    
    def print_settlement_report(self, result: Dict):
        """打印结算报告"""
        print(f"\n{'='*60}")
        print(f" 港股通交易结算报告")
        print(f"{'='*60}")
        print(f"交易数量: {result['shares']}股")
        print(f"成交价格: {result['price_hkd']:.2f} HKD")
        print(f"成交金额: {result['amount_hkd']:,.2f} HKD")
        print(f"\n费用明细:")
        fees = result['fees_hkd']
        print(f"  印花税:     {fees['stamp_duty']:>10,.2f} HKD")
        print(f"  交易费:     {fees['trading_fee']:>10,.2f} HKD")
        print(f"  交收费:     {fees['settlement_fee']:>10,.2f} HKD")
        print(f"  交易征费:   {fees['levy']:>10,.2f} HKD")
        print(f"  佣金:       {fees['commission']:>10,.2f} HKD")
        print(f"  {'─'*40}")
        print(f"  总费用:     {fees['total_hkd']:>10,.2f} HKD ({fees['cost_ratio']:.3f}%)")
        print(f"\n总计 (港币):  {result['total_hkd']:,.2f} HKD")
        print(f"\n汇率信息:")
        print(f"  参考汇率:   {result['ref_exchange_rate']:.4f}")
        print(f"  结算汇率:   {result['settle_exchange_rate']:.4f}")
        print(f"\n人民币资金:")
        print(f"  冻结资金:   {result['frozen_cny']:>10,.2f} CNY")
        print(f"  实际支付:   {result['actual_cny']:>10,.2f} CNY")
        print(f"  汇率差异:   {result['exchange_diff']:>10,.2f} CNY ({result['exchange_diff_pct']:+.3f}%)")
        print(f"{'='*60}\n")


class MarketSimulator:
    """
    市场模拟器 - 模拟股价走势和交易
    """
    
    def __init__(self, initial_price: float = 100.0, volatility: float = 0.02):
        self.price = initial_price
        self.volatility = volatility
        self.price_history = [initial_price]
    
    def next_price(self) -> float:
        """生成下一个价格（随机游走）"""
        change = random.gauss(0, self.volatility)
        self.price *= (1 + change)
        self.price = max(0.01, self.price)  # 价格不能为负
        self.price_history.append(self.price)
        return self.price
    
    def get_stats(self) -> Dict:
        """获取价格统计"""
        prices = self.price_history
        return {
            "current": prices[-1],
            "open": prices[0],
            "high": max(prices),
            "low": min(prices),
            "change_pct": ((prices[-1] - prices[0]) / prices[0]) * 100,
            "volatility": self._calculate_volatility()
        }
    
    def _calculate_volatility(self) -> float:
        """计算历史波动率"""
        if len(self.price_history) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(self.price_history)):
            ret = (self.price_history[i] - self.price_history[i-1]) / self.price_history[i-1]
            returns.append(ret)
        
        import statistics
        return statistics.stdev(returns) if len(returns) > 1 else 0.0


# ==================== 演示代码 ====================

def demo_order_book():
    """演示订单簿撮合机制"""
    print("\n" + "="*60)
    print("   演示：订单簿撮合机制")
    print("="*60)
    
    book = OrderBook("00700.HK")  # 腾讯控股
    
    # 初始化订单簿
    print("\n  初始化订单簿...")
    orders = [
        Order("B001", "00700.HK", OrderSide.BUY, OrderType.LIMIT, 400.0, 100),
        Order("B002", "00700.HK", OrderSide.BUY, OrderType.LIMIT, 399.5, 200),
        Order("B003", "00700.HK", OrderSide.BUY, OrderType.LIMIT, 399.0, 300),
        Order("S001", "00700.HK", OrderSide.SELL, OrderType.LIMIT, 400.5, 150),
        Order("S002", "00700.HK", OrderSide.SELL, OrderType.LIMIT, 401.0, 250),
        Order("S003", "00700.HK", OrderSide.SELL, OrderType.LIMIT, 401.5, 200),
    ]
    
    for order in orders:
        book.add_order(order)
    
    book.display_book()
    
    # 模拟新买单成交
    print("\n  新买单: 400.50元 x 200股 (应与卖一成交)")
    new_buy = Order("B004", "00700.HK", OrderSide.BUY, OrderType.LIMIT, 400.5, 200)
    book.add_order(new_buy)
    
    book.display_book()


def demo_hk_stock_connector():
    """演示港股通结算"""
    print("\n" + "="*60)
    print("   演示：港股通交易结算")
    print("="*60)
    
    connector = HKStockConnector(exchange_rate=0.92)
    
    # 计算结算
    result = connector.calculate_settlement(
        shares=1000,
        price_hkd=35.0,
        ref_exchange_rate=0.9200,
        settle_exchange_rate=0.9180
    )
    
    connector.print_settlement_report(result)


def demo_market_simulation():
    """演示市场模拟"""
    print("\n" + "="*60)
    print("   演示：市场走势模拟")
    print("="*60)
    
    simulator = MarketSimulator(initial_price=100.0, volatility=0.02)
    
    print("\n  模拟20个时间点的价格走势:")
    print(f"{'时间':>6} | {'价格':>10} | {'涨跌':>10}")
    print("-" * 35)
    
    prev_price = simulator.price
    for i in range(20):
        price = simulator.next_price()
        change = ((price - prev_price) / prev_price) * 100
        print(f"{i+1:>6} | {price:>10.2f} | {change:>+9.2f}%")
        prev_price = price
    
    stats = simulator.get_stats()
    print(f"\n  统计信息:")
    print(f"  开盘价: {stats['open']:.2f}")
    print(f"  最高价: {stats['high']:.2f}")
    print(f"  最低价: {stats['low']:.2f}")
    print(f"  收盘价: {stats['current']:.2f}")
    print(f"  涨跌幅: {stats['change_pct']:+.2f}%")
    print(f"  波动率: {stats['volatility']*100:.2f}%")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("   股票市场运作机制 - 实战代码演示")
    print("="*60)
    
    demo_order_book()
    demo_hk_stock_connector()
    demo_market_simulation()
    
    print("\n" + "="*60)
    print("  所有演示完成!")
    print("="*60)
