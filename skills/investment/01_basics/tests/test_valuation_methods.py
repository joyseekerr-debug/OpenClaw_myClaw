"""
估值方法（PE/PB/PS/DCF）- 单元测试
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, '../code')

import unittest
from valuation_methods import ValuationInput, ValuationCalculator, ValuationScreening


class TestPECalculation(unittest.TestCase):
    """测试PE计算"""
    
    def test_pe_ttm_calculation(self):
        """测试TTM PE计算"""
        stock = ValuationInput(
            stock_code="TEST",
            stock_name="测试",
            current_price=100,
            total_shares=10,
            eps_ttm=5.0
        )
        calc = ValuationCalculator(stock)
        pe_data = calc.calculate_pe()
        
        self.assertEqual(pe_data["pe_ttm"], 20.0)  # 100/5=20
    
    def test_pe_forward_calculation(self):
        """测试前瞻PE计算"""
        stock = ValuationInput(
            stock_code="TEST",
            stock_name="测试",
            current_price=100,
            total_shares=10,
            eps_ttm=5.0,
            eps_forecast=6.0
        )
        calc = ValuationCalculator(stock)
        pe_data = calc.calculate_pe()
        
        self.assertEqual(pe_data["pe_forward"], 100/6.0)  # 约16.67
    
    def test_pe_negative_eps(self):
        """测试负收益情况"""
        stock = ValuationInput(
            stock_code="TEST",
            stock_name="测试",
            current_price=100,
            total_shares=10,
            eps_ttm=-5.0
        )
        calc = ValuationCalculator(stock)
        pe_data = calc.calculate_pe()
        
        # 负收益时PE为负
        self.assertEqual(pe_data["pe_ttm"], -20.0)


class TestPBCalculation(unittest.TestCase):
    """测试PB计算"""
    
    def test_pb_calculation(self):
        """测试PB计算"""
        stock = ValuationInput(
            stock_code="TEST",
            stock_name="测试",
            current_price=100,
            total_shares=10,
            book_value_per_share=50.0
        )
        calc = ValuationCalculator(stock)
        pb = calc.calculate_pb()
        
        self.assertEqual(pb, 2.0)  # 100/50=2
    
    def test_pb_zero_book_value(self):
        """测试零净资产情况"""
        stock = ValuationInput(
            stock_code="TEST",
            stock_name="测试",
            current_price=100,
            total_shares=10,
            book_value_per_share=0
        )
        calc = ValuationCalculator(stock)
        pb = calc.calculate_pb()
        
        self.assertIsNone(pb)


class TestPSCalculation(unittest.TestCase):
    """测试PS计算"""
    
    def test_ps_calculation(self):
        """测试PS计算"""
        stock = ValuationInput(
            stock_code="TEST",
            stock_name="测试",
            current_price=100,
            total_shares=10,
            revenue_per_share=50.0
        )
        calc = ValuationCalculator(stock)
        ps = calc.calculate_ps()
        
        self.assertEqual(ps, 2.0)  # 100/50=2


class TestPEGCalculation(unittest.TestCase):
    """测试PEG计算"""
    
    def test_peg_calculation(self):
        """测试PEG计算"""
        stock = ValuationInput(
            stock_code="TEST",
            stock_name="测试",
            current_price=100,
            total_shares=10,
            eps_ttm=5.0,
            profit_growth_rate=20  # 20%增长
        )
        calc = ValuationCalculator(stock)
        peg = calc.calculate_peg()
        
        self.assertEqual(peg, 1.0)  # PE=20, 增长=20, PEG=1
    
    def test_peg_undervalued(self):
        """测试低估情况（PEG<1）"""
        stock = ValuationInput(
            stock_code="TEST",
            stock_name="测试",
            current_price=100,
            total_shares=10,
            eps_ttm=5.0,
            profit_growth_rate=30  # 30%增长
        )
        calc = ValuationCalculator(stock)
        peg = calc.calculate_peg()
        
        self.assertLess(peg, 1.0)  # PE=20, 增长=30, PEG=0.67


class TestDCFCalculation(unittest.TestCase):
    """测试DCF计算"""
    
    def test_dcf_basic(self):
        """测试DCF基础计算"""
        stock = ValuationInput(
            stock_code="TEST",
            stock_name="测试",
            current_price=100,
            total_shares=10,
            fcf_current=100,  # 10亿自由现金流
            wacc=0.10,
            terminal_growth=0.03,
            forecast_years=5,
            high_growth_years=3,
            high_growth_rate=0.10,
            net_cash=0
        )
        calc = ValuationCalculator(stock)
        dcf = calc.calculate_dcf()
        
        self.assertIsNotNone(dcf)
        self.assertGreater(dcf["enterprise_value"], 0)
        self.assertGreater(dcf["value_per_share"], 0)
    
    def test_dcf_with_net_cash(self):
        """测试含净现金的DCF"""
        stock = ValuationInput(
            stock_code="TEST",
            stock_name="测试",
            current_price=100,
            total_shares=10,
            fcf_current=100,
            wacc=0.10,
            terminal_growth=0.03,
            net_cash=100  # 100亿净现金
        )
        calc = ValuationCalculator(stock)
        dcf = calc.calculate_dcf()
        
        # 股权价值应大于企业价值
        self.assertGreater(dcf["equity_value"], dcf["enterprise_value"])
    
    def test_dcf_no_fcf(self):
        """测试无自由现金流情况"""
        stock = ValuationInput(
            stock_code="TEST",
            stock_name="测试",
            current_price=100,
            total_shares=10,
            fcf_current=0
        )
        calc = ValuationCalculator(stock)
        dcf = calc.calculate_dcf()
        
        self.assertIsNone(dcf)


class TestSensitivityAnalysis(unittest.TestCase):
    """测试敏感性分析"""
    
    def test_sensitivity_matrix(self):
        """测试敏感性矩阵生成"""
        stock = ValuationInput(
            stock_code="TEST",
            stock_name="测试",
            current_price=100,
            total_shares=10,
            fcf_current=100,
            wacc=0.10,
            terminal_growth=0.03
        )
        calc = ValuationCalculator(stock)
        
        wacc_range = [0.09, 0.10, 0.11]
        growth_range = [0.02, 0.03, 0.04]
        
        sensitivity = calc.sensitivity_analysis(wacc_range, growth_range)
        
        # 验证矩阵维度
        self.assertEqual(len(sensitivity), 3)
        for wacc in wacc_range:
            self.assertEqual(len(sensitivity[wacc]), 3)
        
        # 验证数值合理性：WACC越高估值越低，增长越高估值越高
        # 比较 (WACC=0.09, g=0.04) vs (WACC=0.11, g=0.02)
        high_value = sensitivity[0.09][0.04]
        low_value = sensitivity[0.11][0.02]
        self.assertGreater(high_value, low_value)


class TestValuationScreening(unittest.TestCase):
    """测试估值筛选"""
    
    def setUp(self):
        self.stocks = [
            ValuationInput("A", "低PE", 10, 10, eps_ttm=1.0),  # PE=10
            ValuationInput("B", "中PE", 20, 10, eps_ttm=1.0),  # PE=20
            ValuationInput("C", "高PE", 50, 10, eps_ttm=1.0),  # PE=50
        ]
    
    def test_screen_by_pe(self):
        """测试PE筛选"""
        result = ValuationScreening.screen_by_pe(self.stocks, max_pe=15)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].stock_name, "低PE")
    
    def test_screen_by_pb(self):
        """测试PB筛选"""
        stocks = [
            ValuationInput("A", "低PB", 100, 10, book_value_per_share=100),  # PB=1
            ValuationInput("B", "高PB", 200, 10, book_value_per_share=50),   # PB=4
        ]
        
        result = ValuationScreening.screen_by_pb(stocks, max_pb=2)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].stock_name, "低PB")
    
    def test_screen_by_peg(self):
        """测试PEG筛选"""
        stocks = [
            ValuationInput("A", "低PEG", 20, 10, eps_ttm=1.0, profit_growth_rate=30),  # PEG=0.67
            ValuationInput("B", "高PEG", 50, 10, eps_ttm=1.0, profit_growth_rate=20),  # PEG=2.5
        ]
        
        result = ValuationScreening.screen_by_peg(stocks, max_peg=1.0)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].stock_name, "低PEG")


class TestComprehensiveValuation(unittest.TestCase):
    """测试综合估值"""
    
    def test_comprehensive_result(self):
        """测试综合估值结果"""
        stock = ValuationInput(
            stock_code="TEST",
            stock_name="测试",
            current_price=100,
            total_shares=10,
            eps_ttm=5.0,
            book_value_per_share=50.0,
            revenue_per_share=100.0,
            profit_growth_rate=20,
            fcf_current=80,
            wacc=0.10,
            terminal_growth=0.03,
            net_cash=100
        )
        calc = ValuationCalculator(stock)
        result = calc.comprehensive_valuation()
        
        # 验证结果包含所有指标
        self.assertGreater(result.pe_ttm, 0)
        self.assertGreater(result.pb, 0)
        self.assertGreater(result.ps, 0)
        self.assertGreater(result.peg, 0)
        
        # 验证评估结果不为空
        self.assertNotEqual(result.assessment, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
