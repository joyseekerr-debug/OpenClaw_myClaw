"""
财务报表阅读 - 单元测试
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, '../code')

import unittest
from financial_statement_analysis import (
    BalanceSheet, IncomeStatement, CashFlowStatement,
    FinancialRatios, FinancialAnalyzer
)


class TestFinancialAnalyzer(unittest.TestCase):
    """测试财务分析器"""
    
    def setUp(self):
        """设置测试数据 - 健康企业"""
        self.balance = BalanceSheet(
            cash=100_000,
            receivables=20_000,
            inventory=30_000,
            current_assets=150_000,
            total_assets=200_000,
            current_liabilities=60_000,
            total_liabilities=80_000,
            equity=120_000,
            goodwill=5_000
        )
        
        self.income = IncomeStatement(
            revenue=100_000,
            cost_of_sales=40_000,
            operating_profit=35_000,
            net_profit=25_000,
            net_profit_deduction=24_000
        )
        
        self.cashflow = CashFlowStatement(
            operating_cashflow=30_000,
            investing_cashflow=-10_000,
            financing_cashflow=-5_000,
            capex=12_000
        )
        
        self.analyzer = FinancialAnalyzer(self.balance, self.income, self.cashflow)
    
    def test_current_ratio(self):
        """测试流动比率计算"""
        ratios = self.analyzer.calculate_ratios()
        expected = 150_000 / 60_000
        self.assertAlmostEqual(ratios.current_ratio, expected, places=2)
    
    def test_quick_ratio(self):
        """测试速动比率计算"""
        ratios = self.analyzer.calculate_ratios()
        expected = (150_000 - 30_000) / 60_000
        self.assertAlmostEqual(ratios.quick_ratio, expected, places=2)
    
    def test_debt_to_asset(self):
        """测试资产负债率"""
        ratios = self.analyzer.calculate_ratios()
        expected = 80_000 / 200_000 * 100  # 返回的是百分比
        self.assertAlmostEqual(ratios.debt_to_asset, expected, places=2)
    
    def test_gross_margin(self):
        """测试毛利率"""
        ratios = self.analyzer.calculate_ratios()
        expected = (100_000 - 40_000) / 100_000 * 100
        self.assertAlmostEqual(ratios.gross_margin, expected, places=2)
    
    def test_net_margin(self):
        """测试净利率"""
        ratios = self.analyzer.calculate_ratios()
        expected = 25_000 / 100_000 * 100
        self.assertAlmostEqual(ratios.net_margin, expected, places=2)
    
    def test_roe(self):
        """测试ROE"""
        ratios = self.analyzer.calculate_ratios()
        expected = 25_000 / 120_000 * 100
        self.assertAlmostEqual(ratios.roe, expected, places=2)
    
    def test_roa(self):
        """测试ROA"""
        ratios = self.analyzer.calculate_ratios()
        expected = 25_000 / 200_000 * 100
        self.assertAlmostEqual(ratios.roa, expected, places=2)
    
    def test_asset_turnover(self):
        """测试资产周转率"""
        ratios = self.analyzer.calculate_ratios()
        expected = 100_000 / 200_000
        self.assertAlmostEqual(ratios.asset_turnover, expected, places=2)
    
    def test_cashflow_to_profit(self):
        """测试现金流/利润比"""
        ratios = self.analyzer.calculate_ratios()
        expected = 30_000 / 25_000 * 100
        self.assertAlmostEqual(ratios.cashflow_to_profit, expected, places=2)
    
    def test_free_cashflow(self):
        """测试自由现金流"""
        ratios = self.analyzer.calculate_ratios()
        expected = 30_000 - 12_000
        self.assertEqual(ratios.free_cashflow, expected)


class TestDupontAnalysis(unittest.TestCase):
    """测试杜邦分析"""
    
    def test_dupont_calculation(self):
        """测试杜邦分析计算"""
        balance = BalanceSheet(
            total_assets=200_000,
            equity=100_000
        )
        income = IncomeStatement(
            revenue=100_000,
            net_profit=15_000
        )
        cashflow = CashFlowStatement()
        
        analyzer = FinancialAnalyzer(balance, income, cashflow)
        dupont = analyzer.dupont_analysis()
        
        # 验证各组成部分
        self.assertAlmostEqual(dupont["net_margin"], 15.0, places=2)
        self.assertAlmostEqual(dupont["asset_turnover"], 0.5, places=2)
        self.assertAlmostEqual(dupont["equity_multiplier"], 2.0, places=2)
        self.assertAlmostEqual(dupont["roe"], 15.0, places=2)  # 15% * 0.5 * 2 = 15%


class TestCashflowPattern(unittest.TestCase):
    """测试现金流模式分析"""
    
    def test_cow_pattern(self):
        """测试奶牛型（经营+，投资-，融资-）"""
        balance = BalanceSheet()
        income = IncomeStatement()
        cashflow = CashFlowStatement(
            operating_cashflow=100,
            investing_cashflow=-50,
            financing_cashflow=-30
        )
        
        analyzer = FinancialAnalyzer(balance, income, cashflow)
        pattern = analyzer.analyze_cashflow_pattern()
        
        self.assertEqual(pattern["type"], "奶牛型")
        self.assertEqual(pattern["health"], "健康")
    
    def test_expansion_pattern(self):
        """测试扩张型（经营+，投资-，融资+）"""
        balance = BalanceSheet()
        income = IncomeStatement()
        cashflow = CashFlowStatement(
            operating_cashflow=100,
            investing_cashflow=-150,
            financing_cashflow=80
        )
        
        analyzer = FinancialAnalyzer(balance, income, cashflow)
        pattern = analyzer.analyze_cashflow_pattern()
        
        self.assertEqual(pattern["type"], "扩张型")
    
    def test_burn_pattern(self):
        """测试烧钱型（经营-，投资-，融资+）"""
        balance = BalanceSheet()
        income = IncomeStatement()
        cashflow = CashFlowStatement(
            operating_cashflow=-50,
            investing_cashflow=-100,
            financing_cashflow=200
        )
        
        analyzer = FinancialAnalyzer(balance, income, cashflow)
        pattern = analyzer.analyze_cashflow_pattern()
        
        self.assertEqual(pattern["type"], "烧钱型")
        self.assertEqual(pattern["health"], "风险")
    
    def test_decline_pattern(self):
        """测试衰退型（经营-，投资+，融资-）"""
        balance = BalanceSheet()
        income = IncomeStatement()
        cashflow = CashFlowStatement(
            operating_cashflow=-50,
            investing_cashflow=100,
            financing_cashflow=-30
        )
        
        analyzer = FinancialAnalyzer(balance, income, cashflow)
        pattern = analyzer.analyze_cashflow_pattern()
        
        self.assertEqual(pattern["type"], "衰退型")
        self.assertEqual(pattern["health"], "高风险")


class TestWarningDetection(unittest.TestCase):
    """测试风险检测"""
    
    def test_negative_operating_cashflow(self):
        """检测经营现金流为负"""
        balance = BalanceSheet()
        income = IncomeStatement(net_profit=10_000)
        cashflow = CashFlowStatement(operating_cashflow=-5_000)
        
        analyzer = FinancialAnalyzer(balance, income, cashflow)
        warnings = analyzer.detect_warnings()
        
        cashflow_warnings = [w for w in warnings if w["type"] == "现金流"]
        self.assertTrue(len(cashflow_warnings) > 0)
        self.assertTrue("经营现金流为负" in cashflow_warnings[0]["message"])
    
    def test_low_cashflow_quality(self):
        """检测现金流质量低"""
        balance = BalanceSheet()
        income = IncomeStatement(net_profit=100_000)
        cashflow = CashFlowStatement(operating_cashflow=30_000)
        
        analyzer = FinancialAnalyzer(balance, income, cashflow)
        warnings = analyzer.detect_warnings()
        
        cashflow_warnings = [w for w in warnings if "含金量低" in w["message"]]
        self.assertTrue(len(cashflow_warnings) > 0)
    
    def test_high_debt_warning(self):
        """检测高负债风险"""
        balance = BalanceSheet(
            total_assets=100_000,
            total_liabilities=80_000
        )
        income = IncomeStatement()
        cashflow = CashFlowStatement()
        
        analyzer = FinancialAnalyzer(balance, income, cashflow)
        warnings = analyzer.detect_warnings()
        
        debt_warnings = [w for w in warnings if w["type"] == "偿债能力"]
        self.assertTrue(len(debt_warnings) > 0)
    
    def test_high_goodwill_warning(self):
        """检测高商誉风险"""
        balance = BalanceSheet(
            equity=100_000,
            goodwill=40_000
        )
        income = IncomeStatement()
        cashflow = CashFlowStatement()
        
        analyzer = FinancialAnalyzer(balance, income, cashflow)
        warnings = analyzer.detect_warnings()
        
        goodwill_warnings = [w for w in warnings if "商誉" in w["message"]]
        self.assertTrue(len(goodwill_warnings) > 0)
    
    def test_negative_profit_warning(self):
        """检测亏损风险"""
        balance = BalanceSheet(total_assets=100_000)
        income = IncomeStatement(revenue=100_000, net_profit=-10_000)
        cashflow = CashFlowStatement()
        
        analyzer = FinancialAnalyzer(balance, income, cashflow)
        warnings = analyzer.detect_warnings()
        
        profit_warnings = [w for w in warnings if "亏损" in w["message"]]
        self.assertTrue(len(profit_warnings) > 0)


class TestHealthScore(unittest.TestCase):
    """测试财务健康评分"""
    
    def test_high_score_company(self):
        """测试高分企业"""
        balance = BalanceSheet(
            cash=100_000,
            current_assets=150_000,
            inventory=20_000,
            total_assets=200_000,
            current_liabilities=60_000,
            total_liabilities=80_000,
            equity=120_000,
            goodwill=5_000
        )
        income = IncomeStatement(
            revenue=100_000,
            cost_of_sales=30_000,
            net_profit=20_000
        )
        cashflow = CashFlowStatement(
            operating_cashflow=25_000,
            capex=5_000
        )
        
        analyzer = FinancialAnalyzer(balance, income, cashflow)
        health = analyzer.calculate_health_score()
        
        self.assertGreater(health["total"], 60)
        self.assertIn(health["rating"], ["A", "B"])
    
    def test_low_score_company(self):
        """测试低分企业"""
        balance = BalanceSheet(
            cash=10_000,
            current_assets=50_000,
            inventory=30_000,
            total_assets=100_000,
            current_liabilities=100_000,
            total_liabilities=90_000,
            equity=10_000,
            goodwill=8_000
        )
        income = IncomeStatement(
            revenue=50_000,
            cost_of_sales=45_000,
            net_profit=1_000
        )
        cashflow = CashFlowStatement(
            operating_cashflow=-5_000,
            capex=10_000
        )
        
        analyzer = FinancialAnalyzer(balance, income, cashflow)
        health = analyzer.calculate_health_score()
        
        self.assertLess(health["total"], 40)
        self.assertEqual(health["rating"], "D")


if __name__ == "__main__":
    unittest.main(verbosity=2)
