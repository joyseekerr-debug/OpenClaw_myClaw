"""
港股通规则详解 - 核心功能模块
包含：费率计算、汇率计算、碎股处理、交易日历等功能
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum


class StockType(Enum):
    """股票类型"""
    H_SHARE = "H股"              # 内地企业在港上市
    RED_CHIP = "红筹股"          # 中资控股香港上市
    BLUE_CHIP = "蓝筹股"         # 香港本地大盘股
    GROWTH = "成长股"            # 成长型股票


@dataclass
class HKStock:
    """港股信息"""
    code: str                    # 股票代码
    name: str                    # 股票名称
    lot_size: int               # 每手股数
    stock_type: StockType       # 股票类型
    is_eligible: bool = True    # 是否在港股通标的范围内


@dataclass
class TradeRecord:
    """交易记录"""
    stock_code: str
    side: str                   # BUY/SELL
    price: float
    quantity: int
    trade_date: datetime


class HKStockFeeCalculator:
    """
    港股通费用计算器
    """
    
    # 费率表
    FEE_RATES = {
        "stamp_duty": 0.001,           # 印花税 0.1%
        "trading_fee": 0.00005,        # 交易费 0.005%
        "levy": 0.000027,              # 交易征费 0.0027%
        "afrc_levy": 0.0000015,        # 会财局征费 0.00015%
        "settlement_fee_rate": 0.00002, # 交收费率 0.002%
        "settlement_fee_min": 2.0,      # 交收费最低
        "settlement_fee_max": 100.0,    # 交收费最高
        "ccass_fee_rate": 0.00003,      # 股份交收费率 0.003%
        "ccass_fee_min": 3.0,           # 股份交收费最低
        "ccass_fee_max": 1000.0,        # 股份交收费最高
        "system_fee": 0.5,              # 系统使用费
        "portfolio_fee_annual": 0.00008, # 组合费年化 0.008%
        "commission_min": 15.0,         # 最低佣金
    }
    
    def __init__(self, commission_rate: float = 0.0003):
        """
        初始化计算器
        
        Args:
            commission_rate: 佣金费率，默认0.03%
        """
        self.commission_rate = commission_rate
    
    def calculate_trading_fees(self, amount_hkd: float) -> Dict:
        """
        计算交易费用
        
        Args:
            amount_hkd: 交易金额（港币）
        
        Returns:
            费用明细字典
        """
        fees = {}
        
        # 印花税（向上取整到整数）
        fees["stamp_duty"] = int(amount_hkd * self.FEE_RATES["stamp_duty"] + 0.999999)
        
        # 交易费
        fees["trading_fee"] = amount_hkd * self.FEE_RATES["trading_fee"]
        
        # 交易征费
        fees["levy"] = amount_hkd * self.FEE_RATES["levy"]
        
        # 会财局征费
        fees["afrc_levy"] = amount_hkd * self.FEE_RATES["afrc_levy"]
        
        # 交收费（有上下限）
        settlement_fee = amount_hkd * self.FEE_RATES["settlement_fee_rate"]
        fees["settlement_fee"] = max(
            self.FEE_RATES["settlement_fee_min"],
            min(settlement_fee, self.FEE_RATES["settlement_fee_max"])
        )
        
        # 股份交收费（有上下限）
        ccass_fee = amount_hkd * self.FEE_RATES["ccass_fee_rate"]
        fees["ccass_fee"] = max(
            self.FEE_RATES["ccass_fee_min"],
            min(ccass_fee, self.FEE_RATES["ccass_fee_max"])
        )
        
        # 佣金
        fees["commission"] = max(
            amount_hkd * self.commission_rate,
            self.FEE_RATES["commission_min"]
        )
        
        # 系统使用费
        fees["system_fee"] = self.FEE_RATES["system_fee"]
        
        # 总费用
        fees["total"] = sum([
            fees["stamp_duty"],
            fees["trading_fee"],
            fees["levy"],
            fees["afrc_levy"],
            fees["settlement_fee"],
            fees["ccass_fee"],
            fees["commission"],
            fees["system_fee"]
        ])
        
        # 成本占比
        fees["cost_ratio"] = (fees["total"] / amount_hkd) * 100
        
        return fees
    
    def calculate_daily_portfolio_fee(self, portfolio_value: float) -> float:
        """
        计算每日组合费
        
        Args:
            portfolio_value: 持仓市值（港币）
        
        Returns:
            每日组合费（港币）
        """
        return portfolio_value * self.FEE_RATES["portfolio_fee_annual"] / 365
    
    def calculate_dividend_tax(self, dividend_amount: float, stock_type: StockType) -> Dict:
        """
        计算股息红利税
        
        Args:
            dividend_amount: 股息金额（港币）
            stock_type: 股票类型
        
        Returns:
            税务明细
        """
        if stock_type == StockType.H_SHARE:
            tax_rate = 0.20  # H股 20%
        elif stock_type == StockType.RED_CHIP:
            tax_rate = 0.28  # 红筹股 28%
        else:
            tax_rate = 0.0   # 其他免税
        
        tax_amount = dividend_amount * tax_rate
        
        return {
            "gross_dividend": dividend_amount,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "net_dividend": dividend_amount - tax_amount
        }


class HKExchangeRateCalculator:
    """
    港股通汇率计算器
    """
    
    def __init__(
        self,
        ref_exchange_rate: float,
        settle_exchange_rate: float
    ):
        """
        初始化汇率计算器
        
        Args:
            ref_exchange_rate: 参考汇率（盘中冻结用）
            settle_exchange_rate: 结算汇率（实际交收用）
        """
        self.ref_exchange_rate = ref_exchange_rate
        self.settle_exchange_rate = settle_exchange_rate
    
    def calculate_buy_frozen(self, amount_hkd: float, fees_hkd: float) -> Dict:
        """
        计算买入冻结资金
        
        Args:
            amount_hkd: 成交金额（港币）
            fees_hkd: 费用（港币）
        
        Returns:
            资金明细
        """
        total_hkd = amount_hkd + fees_hkd
        frozen_cny = total_hkd * self.ref_exchange_rate
        actual_cny = total_hkd * self.settle_exchange_rate
        
        return {
            "amount_hkd": amount_hkd,
            "fees_hkd": fees_hkd,
            "total_hkd": total_hkd,
            "frozen_cny": frozen_cny,
            "actual_cny": actual_cny,
            "refund_cny": frozen_cny - actual_cny,
            "exchange_gain_pct": ((frozen_cny - actual_cny) / frozen_cny) * 100
        }
    
    def calculate_sell_receipt(
        self,
        amount_hkd: float,
        fees_hkd: float,
        original_cost_cny: float
    ) -> Dict:
        """
        计算卖出资金到账
        
        Args:
            amount_hkd: 成交金额（港币）
            fees_hkd: 费用（港币）
            original_cost_cny: 原始成本（人民币）
        
        Returns:
            资金明细
        """
        net_hkd = amount_hkd - fees_hkd
        receipt_cny = net_hkd * self.settle_exchange_rate
        
        # 盈亏计算（考虑汇率影响）
        pnl_cny = receipt_cny - original_cost_cny
        pnl_pct = (pnl_cny / original_cost_cny) * 100 if original_cost_cny > 0 else 0
        
        return {
            "gross_amount_hkd": amount_hkd,
            "fees_hkd": fees_hkd,
            "net_amount_hkd": net_hkd,
            "receipt_cny": receipt_cny,
            "original_cost_cny": original_cost_cny,
            "pnl_cny": pnl_cny,
            "pnl_pct": pnl_pct
        }


class HKStockLotManager:
    """
    港股碎股管理器
    """
    
    def __init__(self):
        # 常见股票每手股数
        self.lot_sizes = {
            "00700": 100,    # 腾讯
            "09988": 100,    # 阿里
            "03690": 100,    # 美团
            "01810": 200,    # 小米
            "00005": 400,    # 汇丰
            "02331": 500,    # 李宁
            "02015": 100,    # 理想汽车
            "09618": 50,     # 京东
            "09999": 100,    # 网易
            "01024": 100,    # 快手
        }
    
    def get_lot_size(self, stock_code: str) -> int:
        """获取每手股数"""
        return self.lot_sizes.get(stock_code, 100)  # 默认100股
    
    def split_lots(self, stock_code: str, total_shares: int) -> Dict:
        """
        分割整手和碎股
        
        Args:
            stock_code: 股票代码
            total_shares: 总股数
        
        Returns:
            分割结果
        """
        lot_size = self.get_lot_size(stock_code)
        
        full_lots = total_shares // lot_size
        odd_lot = total_shares % lot_size
        
        return {
            "stock_code": stock_code,
            "lot_size": lot_size,
            "total_shares": total_shares,
            "full_lots": full_lots,
            "full_lot_shares": full_lots * lot_size,
            "odd_lot_shares": odd_lot,
            "can_sell_as_full": full_lots > 0,
            "can_sell_as_odd": odd_lot > 0
        }
    
    def calculate_buy_quantity(self, stock_code: str, desired_shares: int) -> Dict:
        """
        计算可买入数量（必须是整手）
        
        Args:
            stock_code: 股票代码
            desired_shares: 期望股数
        
        Returns:
            买入建议
        """
        lot_size = self.get_lot_size(stock_code)
        
        # 向下取整到整手
        buyable_shares = (desired_shares // lot_size) * lot_size
        
        return {
            "stock_code": stock_code,
            "lot_size": lot_size,
            "desired_shares": desired_shares,
            "buyable_shares": buyable_shares,
            "lots": buyable_shares // lot_size,
            "remainder": desired_shares - buyable_shares,
            "can_buy_exact": desired_shares % lot_size == 0
        }


class HKTradingCalendar:
    """
    港股交易日历
    """
    
    # 港股交易时间（北京时间）
    TRADING_HOURS = {
        "pre_open": ("09:00", "09:30"),      # 开市前时段
        "morning": ("09:30", "12:00"),       # 早市
        "afternoon": ("13:00", "16:00"),     # 午市
        "closing": ("16:00", "16:10"),       # 收市竞价
    }
    
    # 2026年港股通关闭日期（示例）
    CLOSED_DATES_2026 = [
        "2026-01-01",  # 元旦
        "2026-02-16", "2026-02-17", "2026-02-18",  # 春节
        "2026-04-03", "2026-04-06",  # 复活节/清明
        "2026-05-01",  # 劳动节
        "2026-06-25",  # 端午节
        "2026-10-01", "2026-10-02",  # 国庆
        "2026-12-25",  # 圣诞节
    ]
    
    def is_trading_day(self, date: datetime) -> bool:
        """判断是否为交易日"""
        date_str = date.strftime("%Y-%m-%d")
        
        # 周末休市
        if date.weekday() >= 5:  # 5=周六, 6=周日
            return False
        
        # 节假日休市
        if date_str in self.CLOSED_DATES_2026:
            return False
        
        return True
    
    def get_settlement_date(self, trade_date: datetime, t_plus: int = 2) -> datetime:
        """
        计算交收日
        
        Args:
            trade_date: 交易日期
            t_plus: T+N交收，默认T+2
        
        Returns:
            交收日期
        """
        settlement_date = trade_date
        days_counted = 0
        
        while days_counted < t_plus:
            settlement_date += timedelta(days=1)
            if self.is_trading_day(settlement_date):
                days_counted += 1
        
        return settlement_date
    
    def get_trading_session(self, time: datetime.time) -> Optional[str]:
        """
        判断当前交易时段
        
        Args:
            time: 当前时间
        
        Returns:
            时段名称或None
        """
        from datetime import time as dt_time
        
        t = time if isinstance(time, dt_time) else dt_time.fromisoformat(time)
        
        for session, (start, end) in self.TRADING_HOURS.items():
            start_t = dt_time.fromisoformat(start)
            end_t = dt_time.fromisoformat(end)
            if start_t <= t < end_t:
                return session
        
        return None


# ==================== 演示代码 ====================

def demo_fee_calculation():
    """演示费用计算"""
    print("\n" + "="*60)
    print("   演示：港股通费用计算")
    print("="*60)
    
    calculator = HKStockFeeCalculator(commission_rate=0.0003)
    
    # 案例：买入10万股腾讯，股价400港币
    amount = 10000 * 400  # 4,000,000 HKD
    fees = calculator.calculate_trading_fees(amount)
    
    print(f"\n交易：买入10,000股腾讯 @ 400 HKD")
    print(f"成交金额：{amount:,.2f} HKD")
    print(f"\n费用明细：")
    print(f"  印花税：      {fees['stamp_duty']:>10,.2f} HKD")
    print(f"  交易费：      {fees['trading_fee']:>10,.2f} HKD")
    print(f"  交易征费：    {fees['levy']:>10,.2f} HKD")
    print(f"  会财局征费：  {fees['afrc_levy']:>10,.2f} HKD")
    print(f"  交收费：      {fees['settlement_fee']:>10,.2f} HKD")
    print(f"  股份交收费：  {fees['ccass_fee']:>10,.2f} HKD")
    print(f"  佣金：        {fees['commission']:>10,.2f} HKD")
    print(f"  系统使用费：  {fees['system_fee']:>10,.2f} HKD")
    print(f"  {'─'*45}")
    print(f"  总费用：      {fees['total']:>10,.2f} HKD ({fees['cost_ratio']:.4f}%)")
    
    # 组合费计算
    portfolio_value = 1000000  # 100万港币持仓
    daily_fee = calculator.calculate_daily_portfolio_fee(portfolio_value)
    annual_fee = daily_fee * 365
    print(f"\n组合费示例（持仓100万港币）：")
    print(f"  每日组合费：{daily_fee:.2f} HKD")
    print(f"  年度组合费：{annual_fee:.2f} HKD")


def demo_exchange_rate():
    """演示汇率计算"""
    print("\n" + "="*60)
    print("   演示：港股通汇率计算")
    print("="*60)
    
    # 买入场景
    calc = HKExchangeRateCalculator(
        ref_exchange_rate=0.9250,
        settle_exchange_rate=0.9210
    )
    
    amount = 1000 * 380  # 买入1000股腾讯，380港币
    fees = 600  # 预估费用
    
    result = calc.calculate_buy_frozen(amount, fees)
    
    print(f"\n买入场景：1000股腾讯 @ 380 HKD")
    print(f"参考汇率：0.9250")
    print(f"结算汇率：0.9210")
    print(f"\n资金计算：")
    print(f"  成交金额：    {result['amount_hkd']:>12,.2f} HKD")
    print(f"  预估费用：    {result['fees_hkd']:>12,.2f} HKD")
    print(f"  港币总计：    {result['total_hkd']:>12,.2f} HKD")
    print(f"\n  冻结资金：    {result['frozen_cny']:>12,.2f} CNY")
    print(f"  实际支付：    {result['actual_cny']:>12,.2f} CNY")
    print(f"  汇率退款：    {result['refund_cny']:>12,.2f} CNY")
    print(f"  汇率收益：    {result['exchange_gain_pct']:+.4f}%")


def demo_lot_management():
    """演示碎股管理"""
    print("\n" + "="*60)
    print("   演示：港股碎股管理")
    print("="*60)
    
    manager = HKStockLotManager()
    
    # 案例1：分割整手和碎股
    print("\n案例1：持有150股腾讯")
    result = manager.split_lots("00700", 150)
    print(f"  股票代码：    {result['stock_code']}")
    print(f"  每手股数：    {result['lot_size']}股")
    print(f"  总股数：      {result['total_shares']}股")
    print(f"  整手数量：    {result['full_lots']}手 ({result['full_lot_shares']}股)")
    print(f"  碎股数量：    {result['odd_lot_shares']}股")
    print(f"  可整手卖出：  {'是' if result['can_sell_as_full'] else '否'}")
    print(f"  可碎股卖出：  {'是' if result['can_sell_as_odd'] else '否'}")
    
    # 案例2：计算可买入数量
    print("\n案例2：想买入550股小米")
    buy_result = manager.calculate_buy_quantity("01810", 550)
    print(f"  股票代码：    {buy_result['stock_code']}")
    print(f"  每手股数：    {buy_result['lot_size']}股")
    print(f"  期望股数：    {buy_result['desired_shares']}股")
    print(f"  可买股数：    {buy_result['buyable_shares']}股 ({buy_result['lots']}手)")
    print(f"  剩余股数：    {buy_result['remainder']}股（无法买入）")


def demo_trading_calendar():
    """演示交易日历"""
    print("\n" + "="*60)
    print("   演示：港股交易日历")
    print("="*60)
    
    calendar = HKTradingCalendar()
    
    # 判断交易日
    test_dates = [
        datetime(2026, 2, 24),   # 周二，交易日
        datetime(2026, 2, 28),   # 周六，休市
        datetime(2026, 2, 16),   # 春节，休市
    ]
    
    print("\n交易日判断：")
    for date in test_dates:
        is_trading = calendar.is_trading_day(date)
        print(f"  {date.strftime('%Y-%m-%d')} ({date.strftime('%A')})：{'交易日' if is_trading else '休市'}")
    
    # T+2交收计算
    trade_date = datetime(2026, 2, 24)
    settlement = calendar.get_settlement_date(trade_date, t_plus=2)
    print(f"\nT+2交收计算：")
    print(f"  交易日期：{trade_date.strftime('%Y-%m-%d')}")
    print(f"  交收日期：{settlement.strftime('%Y-%m-%d')}")
    
    # 交易时段判断
    from datetime import time
    test_times = [time(9, 45), time(12, 30), time(15, 30)]
    print(f"\n交易时段判断：")
    for t in test_times:
        session = calendar.get_trading_session(t)
        session_name = {
            "pre_open": "开市前时段",
            "morning": "早市",
            "afternoon": "午市",
            "closing": "收市竞价"
        }.get(session, "非交易时段")
        print(f"  {t.strftime('%H:%M')}：{session_name}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("   港股通规则详解 - 实战代码演示")
    print("="*60)
    
    demo_fee_calculation()
    demo_exchange_rate()
    demo_lot_management()
    demo_trading_calendar()
    
    print("\n" + "="*60)
    print("  所有演示完成!")
    print("="*60)
