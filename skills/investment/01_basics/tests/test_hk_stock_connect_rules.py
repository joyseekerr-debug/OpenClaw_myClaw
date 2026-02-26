"""
港股通规则详解 - 单元测试
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, '../code')

import unittest
from datetime import datetime, time
from hk_stock_connect_rules import (
    StockType, HKStock, HKStockFeeCalculator,
    HKExchangeRateCalculator, HKStockLotManager, HKTradingCalendar
)


class TestHKStockFeeCalculator(unittest.TestCase):
    """测试费用计算器"""
    
    def setUp(self):
        self.calculator = HKStockFeeCalculator(commission_rate=0.0003)
    
    def test_stamp_duty_rounding(self):
        """测试印花税向上取整"""
        # 金额1000港币，印花税应为1港币（向上取整）
        fees = self.calculator.calculate_trading_fees(1000)
        self.assertEqual(fees["stamp_duty"], 1)
        
        # 金额10000港币，印花税10港币
        fees = self.calculator.calculate_trading_fees(10000)
        self.assertEqual(fees["stamp_duty"], 10)
    
    def test_settlement_fee_limits(self):
        """测试交收费上下限"""
        # 小额交易，交收费应为最低2港币
        fees_small = self.calculator.calculate_trading_fees(10000)
        self.assertEqual(fees_small["settlement_fee"], 2.0)
        
        # 大额交易，交收费不超过100港币上限
        fees_large = self.calculator.calculate_trading_fees(100000000)
        self.assertEqual(fees_large["settlement_fee"], 100.0)
    
    def test_ccass_fee_limits(self):
        """测试股份交收费上下限"""
        # 小额交易，股份交收费应为最低3港币
        fees_small = self.calculator.calculate_trading_fees(10000)
        self.assertEqual(fees_small["ccass_fee"], 3.0)
        
        # 大额交易，股份交收费不超过1000港币上限
        fees_large = self.calculator.calculate_trading_fees(100000000)
        self.assertEqual(fees_large["ccass_fee"], 1000.0)
    
    def test_commission_minimum(self):
        """测试佣金最低收费"""
        # 小额交易，佣金应为最低15港币
        fees = self.calculator.calculate_trading_fees(10000)
        self.assertEqual(fees["commission"], 15.0)
        
        # 大额交易，按比例计算
        fees_large = self.calculator.calculate_trading_fees(1000000)
        expected_commission = max(1000000 * 0.0003, 15.0)
        self.assertEqual(fees_large["commission"], expected_commission)
    
    def test_total_fee_calculation(self):
        """测试总费用计算"""
        amount = 40000  # 4万港币
        fees = self.calculator.calculate_trading_fees(amount)
        
        expected_total = (
            fees["stamp_duty"] +
            fees["trading_fee"] +
            fees["levy"] +
            fees["afrc_levy"] +
            fees["settlement_fee"] +
            fees["ccass_fee"] +
            fees["commission"] +
            fees["system_fee"]
        )
        
        self.assertAlmostEqual(fees["total"], expected_total, places=2)
    
    def test_cost_ratio(self):
        """测试成本占比"""
        amount = 100000
        fees = self.calculator.calculate_trading_fees(amount)
        
        expected_ratio = (fees["total"] / amount) * 100
        self.assertAlmostEqual(fees["cost_ratio"], expected_ratio, places=4)
    
    def test_portfolio_fee(self):
        """测试组合费计算"""
        portfolio_value = 1000000  # 100万港币
        daily_fee = self.calculator.calculate_daily_portfolio_fee(portfolio_value)
        
        expected_daily = 1000000 * 0.00008 / 365
        self.assertAlmostEqual(daily_fee, expected_daily, places=2)
    
    def test_dividend_tax_h_share(self):
        """测试H股股息税"""
        dividend = 1000
        result = self.calculator.calculate_dividend_tax(dividend, StockType.H_SHARE)
        
        self.assertEqual(result["tax_rate"], 0.20)
        self.assertEqual(result["tax_amount"], 200)
        self.assertEqual(result["net_dividend"], 800)
    
    def test_dividend_tax_red_chip(self):
        """测试红筹股股息税"""
        dividend = 1000
        result = self.calculator.calculate_dividend_tax(dividend, StockType.RED_CHIP)
        
        self.assertEqual(result["tax_rate"], 0.28)
        self.assertEqual(result["tax_amount"], 280)
        self.assertEqual(result["net_dividend"], 720)
    
    def test_dividend_tax_exempt(self):
        """测试免税股息"""
        dividend = 1000
        result = self.calculator.calculate_dividend_tax(dividend, StockType.BLUE_CHIP)
        
        self.assertEqual(result["tax_rate"], 0.0)
        self.assertEqual(result["tax_amount"], 0)
        self.assertEqual(result["net_dividend"], 1000)


class TestHKExchangeRateCalculator(unittest.TestCase):
    """测试汇率计算器"""
    
    def setUp(self):
        self.calculator = HKExchangeRateCalculator(
            ref_exchange_rate=0.9250,
            settle_exchange_rate=0.9210
        )
    
    def test_buy_frozen_calculation(self):
        """测试买入冻结资金计算"""
        amount = 380000
        fees = 600
        result = self.calculator.calculate_buy_frozen(amount, fees)
        
        expected_total_hkd = amount + fees
        expected_frozen = expected_total_hkd * 0.9250
        expected_actual = expected_total_hkd * 0.9210
        
        self.assertEqual(result["amount_hkd"], amount)
        self.assertEqual(result["fees_hkd"], fees)
        self.assertEqual(result["total_hkd"], expected_total_hkd)
        self.assertAlmostEqual(result["frozen_cny"], expected_frozen, places=2)
        self.assertAlmostEqual(result["actual_cny"], expected_actual, places=2)
        self.assertAlmostEqual(result["refund_cny"], expected_frozen - expected_actual, places=2)
    
    def test_sell_receipt_calculation(self):
        """测试卖出到账计算"""
        amount = 400000
        fees = 600
        original_cost = 350000
        
        result = self.calculator.calculate_sell_receipt(amount, fees, original_cost)
        
        expected_net_hkd = amount - fees
        expected_receipt = expected_net_hkd * 0.9210
        
        self.assertEqual(result["gross_amount_hkd"], amount)
        self.assertEqual(result["fees_hkd"], fees)
        self.assertEqual(result["net_amount_hkd"], expected_net_hkd)
        self.assertAlmostEqual(result["receipt_cny"], expected_receipt, places=2)
        self.assertEqual(result["original_cost_cny"], original_cost)
        self.assertAlmostEqual(result["pnl_cny"], expected_receipt - original_cost, places=2)


class TestHKStockLotManager(unittest.TestCase):
    """测试碎股管理器"""
    
    def setUp(self):
        self.manager = HKStockLotManager()
    
    def test_get_lot_size_known(self):
        """测试获取已知股票每手股数"""
        self.assertEqual(self.manager.get_lot_size("00700"), 100)  # 腾讯
        self.assertEqual(self.manager.get_lot_size("01810"), 200)  # 小米
        self.assertEqual(self.manager.get_lot_size("00005"), 400)  # 汇丰
    
    def test_get_lot_size_default(self):
        """测试获取未知股票默认每手股数"""
        self.assertEqual(self.manager.get_lot_size("99999"), 100)
    
    def test_split_lots_exact(self):
        """测试整手分割"""
        result = self.manager.split_lots("00700", 500)  # 5手
        
        self.assertEqual(result["lot_size"], 100)
        self.assertEqual(result["total_shares"], 500)
        self.assertEqual(result["full_lots"], 5)
        self.assertEqual(result["full_lot_shares"], 500)
        self.assertEqual(result["odd_lot_shares"], 0)
        self.assertTrue(result["can_sell_as_full"])
        self.assertFalse(result["can_sell_as_odd"])
    
    def test_split_lots_with_odd(self):
        """测试含碎股分割"""
        result = self.manager.split_lots("00700", 550)  # 5手+50股
        
        self.assertEqual(result["full_lots"], 5)
        self.assertEqual(result["full_lot_shares"], 500)
        self.assertEqual(result["odd_lot_shares"], 50)
        self.assertTrue(result["can_sell_as_full"])
        self.assertTrue(result["can_sell_as_odd"])
    
    def test_split_lots_only_odd(self):
        """测试仅碎股"""
        result = self.manager.split_lots("00700", 50)  # 仅50股碎股
        
        self.assertEqual(result["full_lots"], 0)
        self.assertEqual(result["full_lot_shares"], 0)
        self.assertEqual(result["odd_lot_shares"], 50)
        self.assertFalse(result["can_sell_as_full"])
        self.assertTrue(result["can_sell_as_odd"])
    
    def test_calculate_buy_quantity_exact(self):
        """测试整手买入计算"""
        result = self.manager.calculate_buy_quantity("00700", 500)
        
        self.assertEqual(result["buyable_shares"], 500)
        self.assertEqual(result["lots"], 5)
        self.assertEqual(result["remainder"], 0)
        self.assertTrue(result["can_buy_exact"])
    
    def test_calculate_buy_quantity_with_remainder(self):
        """测试含余数买入计算"""
        result = self.manager.calculate_buy_quantity("00700", 550)
        
        self.assertEqual(result["buyable_shares"], 500)
        self.assertEqual(result["lots"], 5)
        self.assertEqual(result["remainder"], 50)
        self.assertFalse(result["can_buy_exact"])


class TestHKTradingCalendar(unittest.TestCase):
    """测试交易日历"""
    
    def setUp(self):
        self.calendar = HKTradingCalendar()
    
    def test_is_trading_day_weekday(self):
        """测试工作日判断"""
        # 2026-02-24 是周二，应该是交易日
        date = datetime(2026, 2, 24)
        self.assertTrue(self.calendar.is_trading_day(date))
    
    def test_is_trading_day_saturday(self):
        """测试周六休市"""
        # 2026-02-28 是周六
        date = datetime(2026, 2, 28)
        self.assertFalse(self.calendar.is_trading_day(date))
    
    def test_is_trading_day_sunday(self):
        """测试周日休市"""
        # 2026-03-01 是周日
        date = datetime(2026, 3, 1)
        self.assertFalse(self.calendar.is_trading_day(date))
    
    def test_is_trading_day_holiday(self):
        """测试节假日休市"""
        # 2026-02-16 春节
        date = datetime(2026, 2, 16)
        self.assertFalse(self.calendar.is_trading_day(date))
    
    def test_get_settlement_date(self):
        """测试交收日计算"""
        # 2026-02-24 (周二) 交易，T+2 应该是 2026-02-26 (周四)
        trade_date = datetime(2026, 2, 24)
        settlement = self.calendar.get_settlement_date(trade_date, t_plus=2)
        
        self.assertEqual(settlement, datetime(2026, 2, 26))
    
    def test_get_settlement_date_skip_weekend(self):
        """测试交收日跳过周末"""
        # 2026-02-27 (周五) 交易，T+2 应该是 2026-03-03 (周二)
        trade_date = datetime(2026, 2, 27)
        settlement = self.calendar.get_settlement_date(trade_date, t_plus=2)
        
        self.assertEqual(settlement, datetime(2026, 3, 3))
    
    def test_get_trading_session_morning(self):
        """测试早市时段"""
        t = time(10, 0)  # 10:00 早市
        session = self.calendar.get_trading_session(t)
        self.assertEqual(session, "morning")
    
    def test_get_trading_session_afternoon(self):
        """测试午市时段"""
        t = time(14, 0)  # 14:00 午市
        session = self.calendar.get_trading_session(t)
        self.assertEqual(session, "afternoon")
    
    def test_get_trading_session_non_trading(self):
        """测试非交易时段"""
        t = time(12, 30)  # 12:30 午间休市
        session = self.calendar.get_trading_session(t)
        self.assertIsNone(session)


if __name__ == "__main__":
    unittest.main(verbosity=2)
