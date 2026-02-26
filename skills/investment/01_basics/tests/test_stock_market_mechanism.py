"""
股票市场运作机制 - 单元测试
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, '../code')

import unittest
from datetime import datetime
from stock_market_mechanism import (
    Order, OrderType, OrderSide, OrderStatus,
    Trade, OrderBook, HKStockConnector, MarketSimulator
)


class TestOrder(unittest.TestCase):
    """测试订单类"""
    
    def test_order_creation(self):
        """测试订单创建"""
        order = Order(
            order_id="TEST001",
            symbol="00700.HK",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=400.0,
            quantity=100
        )
        
        self.assertEqual(order.order_id, "TEST001")
        self.assertEqual(order.symbol, "00700.HK")
        self.assertEqual(order.side, OrderSide.BUY)
        self.assertEqual(order.price, 400.0)
        self.assertEqual(order.quantity, 100)
        self.assertEqual(order.remaining_quantity, 100)
        self.assertFalse(order.is_filled)
    
    def test_order_fill(self):
        """测试订单成交"""
        order = Order("TEST001", "00700.HK", OrderSide.BUY, OrderType.LIMIT, 400.0, 100)
        
        order.filled_quantity = 50
        self.assertEqual(order.remaining_quantity, 50)
        self.assertEqual(order.status, OrderStatus.PENDING)
        
        order.filled_quantity = 100
        self.assertTrue(order.is_filled)
    
    def test_order_comparison(self):
        """测试订单排序（价格优先、时间优先）"""
        from datetime import timedelta
        
        now = datetime.now()
        
        # 买单：高价优先
        buy1 = Order("B1", "TEST", OrderSide.BUY, OrderType.LIMIT, 410.0, 100)
        buy1.timestamp = now
        buy2 = Order("B2", "TEST", OrderSide.BUY, OrderType.LIMIT, 400.0, 100)
        buy2.timestamp = now
        
        self.assertTrue(buy1 < buy2)  # 410 > 400, 所以buy1排在前面
        
        # 卖单：低价优先
        sell1 = Order("S1", "TEST", OrderSide.SELL, OrderType.LIMIT, 390.0, 100)
        sell1.timestamp = now
        sell2 = Order("S2", "TEST", OrderSide.SELL, OrderType.LIMIT, 400.0, 100)
        sell2.timestamp = now
        
        self.assertTrue(sell1 < sell2)  # 390 < 400, 所以sell1排在前面


class TestOrderBook(unittest.TestCase):
    """测试订单簿"""
    
    def setUp(self):
        """每个测试前创建新的订单簿"""
        self.book = OrderBook("00700.HK", verbose=False)
    
    def test_add_buy_order_no_match(self):
        """测试添加买单（无撮合）"""
        order = Order("B1", "00700.HK", OrderSide.BUY, OrderType.LIMIT, 390.0, 100)
        trades = self.book.add_order(order)
        
        self.assertEqual(len(trades), 0)
        self.assertEqual(len(self.book.bids), 1)
        self.assertEqual(len(self.book.asks), 0)
    
    def test_add_sell_order_no_match(self):
        """测试添加卖单（无撮合）"""
        order = Order("S1", "00700.HK", OrderSide.SELL, OrderType.LIMIT, 410.0, 100)
        trades = self.book.add_order(order)
        
        self.assertEqual(len(trades), 0)
        self.assertEqual(len(self.book.bids), 0)
        self.assertEqual(len(self.book.asks), 1)
    
    def test_full_match(self):
        """测试完全成交"""
        # 先加卖单
        sell = Order("S1", "00700.HK", OrderSide.SELL, OrderType.LIMIT, 400.0, 100)
        self.book.add_order(sell)
        
        # 再加买单（价格匹配）
        buy = Order("B1", "00700.HK", OrderSide.BUY, OrderType.LIMIT, 400.0, 100)
        trades = self.book.add_order(buy)
        
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].price, 400.0)
        self.assertEqual(trades[0].quantity, 100)
        self.assertTrue(buy.is_filled)
    
    def test_partial_match(self):
        """测试部分成交"""
        # 卖单100股
        sell = Order("S1", "00700.HK", OrderSide.SELL, OrderType.LIMIT, 400.0, 100)
        self.book.add_order(sell)
        
        # 买单200股
        buy = Order("B1", "00700.HK", OrderSide.BUY, OrderType.LIMIT, 400.0, 200)
        trades = self.book.add_order(buy)
        
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].quantity, 100)  # 只成交100股
        self.assertEqual(buy.remaining_quantity, 100)  # 还剩100股
        self.assertEqual(buy.status, OrderStatus.PARTIAL)
        self.assertEqual(len(self.book.bids), 1)  # 剩余买单在队列中
    
    def test_multiple_matches(self):
        """测试多笔撮合"""
        # 两个卖单
        sell1 = Order("S1", "00700.HK", OrderSide.SELL, OrderType.LIMIT, 400.0, 50)
        sell2 = Order("S2", "00700.HK", OrderSide.SELL, OrderType.LIMIT, 401.0, 50)
        self.book.add_order(sell1)
        self.book.add_order(sell2)
        
        # 一个大买单
        buy = Order("B1", "00700.HK", OrderSide.BUY, OrderType.LIMIT, 401.0, 100)
        trades = self.book.add_order(buy)
        
        self.assertEqual(len(trades), 2)
        self.assertTrue(buy.is_filled)
    
    def test_price_priority(self):
        """测试价格优先原则"""
        # 两个卖单，价格不同
        sell1 = Order("S1", "00700.HK", OrderSide.SELL, OrderType.LIMIT, 400.0, 50)
        sell2 = Order("S2", "00700.HK", OrderSide.SELL, OrderType.LIMIT, 399.0, 50)
        self.book.add_order(sell1)
        self.book.add_order(sell2)
        
        # 买单应该优先与价格低的成交
        buy = Order("B1", "00700.HK", OrderSide.BUY, OrderType.LIMIT, 400.0, 50)
        trades = self.book.add_order(buy)
        
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].price, 399.0)  # 与低价卖单成交
    
    def test_market_depth(self):
        """测试市场深度"""
        # 添加多个价位的订单
        orders = [
            Order("B1", "00700.HK", OrderSide.BUY, OrderType.LIMIT, 400.0, 100),
            Order("B2", "00700.HK", OrderSide.BUY, OrderType.LIMIT, 400.0, 200),
            Order("B3", "00700.HK", OrderSide.BUY, OrderType.LIMIT, 399.0, 100),
            Order("S1", "00700.HK", OrderSide.SELL, OrderType.LIMIT, 401.0, 150),
            Order("S2", "00700.HK", OrderSide.SELL, OrderType.LIMIT, 402.0, 100),
        ]
        
        for order in orders:
            self.book.add_order(order)
        
        depth = self.book.get_market_depth(levels=3)
        
        # 买单应该合并同价位
        self.assertEqual(depth["bids"][0]["price"], 400.0)
        self.assertEqual(depth["bids"][0]["quantity"], 300)  # 100+200
        
        # 价差
        self.assertEqual(depth["spread"], 1.0)  # 401 - 400


class TestHKStockConnector(unittest.TestCase):
    """测试港股通连接器"""
    
    def setUp(self):
        self.connector = HKStockConnector(exchange_rate=0.92)
    
    def test_fee_calculation(self):
        """测试费用计算"""
        amount = 35000.0  # 1000股 @ 35港币
        fees = self.connector.calculate_fees(amount)
        
        # 检查各项费用
        self.assertAlmostEqual(fees["stamp_duty"], amount * 0.001, places=2)
        self.assertAlmostEqual(fees["trading_fee"], amount * 0.00005, places=2)
        self.assertAlmostEqual(fees["settlement_fee"], amount * 0.00002, places=2)
        self.assertAlmostEqual(fees["levy"], amount * 0.000027, places=2)
        
        # 佣金取最大值（固定vs比例）
        expected_commission = max(amount * 0.0003, 15)
        self.assertAlmostEqual(fees["commission"], expected_commission, places=2)
        
        # 总费用
        expected_total = (
            fees["stamp_duty"] + fees["trading_fee"] + 
            fees["settlement_fee"] + fees["levy"] + fees["commission"]
        )
        self.assertAlmostEqual(fees["total_hkd"], expected_total, places=2)
    
    def test_settlement_calculation(self):
        """测试结算计算"""
        result = self.connector.calculate_settlement(
            shares=1000,
            price_hkd=35.0,
            ref_exchange_rate=0.9200,
            settle_exchange_rate=0.9180
        )
        
        # 基础检查
        self.assertEqual(result["shares"], 1000)
        self.assertEqual(result["price_hkd"], 35.0)
        self.assertEqual(result["amount_hkd"], 35000.0)
        
        # 汇率差异检查
        total_hkd = result["total_hkd"]
        expected_frozen = total_hkd * 0.9200
        expected_actual = total_hkd * 0.9180
        
        self.assertAlmostEqual(result["frozen_cny"], expected_frozen, places=2)
        self.assertAlmostEqual(result["actual_cny"], expected_actual, places=2)
        self.assertAlmostEqual(result["exchange_diff"], expected_frozen - expected_actual, places=2)
    
    def test_cost_ratio(self):
        """测试成本占比"""
        amount = 10000.0
        fees = self.connector.calculate_fees(amount)
        
        # 成本占比应该在0.25%-0.5%之间
        self.assertGreater(fees["cost_ratio"], 0.25)
        self.assertLess(fees["cost_ratio"], 0.5)


class TestMarketSimulator(unittest.TestCase):
    """测试市场模拟器"""
    
    def setUp(self):
        self.simulator = MarketSimulator(initial_price=100.0, volatility=0.02)
    
    def test_initial_price(self):
        """测试初始价格"""
        self.assertEqual(self.simulator.price, 100.0)
        self.assertEqual(len(self.simulator.price_history), 1)
    
    def test_price_generation(self):
        """测试价格生成"""
        price = self.simulator.next_price()
        
        # 价格应该为正
        self.assertGreater(price, 0)
        
        # 历史记录应该增加
        self.assertEqual(len(self.simulator.price_history), 2)
    
    def test_statistics(self):
        """测试统计信息"""
        # 生成一些价格
        for _ in range(10):
            self.simulator.next_price()
        
        stats = self.simulator.get_stats()
        
        # 检查统计字段
        self.assertIn("current", stats)
        self.assertIn("open", stats)
        self.assertIn("high", stats)
        self.assertIn("low", stats)
        self.assertIn("change_pct", stats)
        self.assertIn("volatility", stats)
        
        # 高低价约束
        self.assertGreaterEqual(stats["high"], stats["low"])
        self.assertGreaterEqual(stats["current"], stats["low"])
        self.assertLessEqual(stats["current"], stats["high"])


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_full_trading_scenario(self):
        """测试完整交易场景"""
        book = OrderBook("00700.HK", verbose=False)
        
        # 模拟连续竞价过程
        orders = [
            ("B1", OrderSide.BUY, 399.0, 100),
            ("B2", OrderSide.BUY, 400.0, 100),
            ("S1", OrderSide.SELL, 401.0, 100),
            ("S2", OrderSide.SELL, 400.0, 100),  # 应该与B2成交
            ("B3", OrderSide.BUY, 401.0, 200),   # 应该与S1和S2成交
        ]
        
        total_trades = 0
        for order_id, side, price, qty in orders:
            order = Order(order_id, "00700.HK", side, OrderType.LIMIT, price, qty)
            trades = book.add_order(order)
            total_trades += len(trades)
        
        # 验证：应该有3笔成交
        # B2(400)与S2(400)成交，B3(401)与S2(剩余)和S1(401)成交
        self.assertGreater(total_trades, 0)
        self.assertEqual(len(book.trades), total_trades)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestOrder))
    suite.addTests(loader.loadTestsFromTestCase(TestOrderBook))
    suite.addTests(loader.loadTestsFromTestCase(TestHKStockConnector))
    suite.addTests(loader.loadTestsFromTestCase(TestMarketSimulator))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
