"""
行业分析框架 - 单元测试
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, '../code')

import unittest
from industry_analysis_framework import (
    IndustryLifeCycle, IndustryType, PorterFiveForces,
    IndustryMetrics, Industry, IndustryAnalyzer,
    IndustryRotator, IndustryScreener
)


class TestPorterFiveForces(unittest.TestCase):
    """测试波特五力"""
    
    def test_attractiveness_perfect(self):
        """测试理想行业（五力都弱）"""
        forces = PorterFiveForces(
            internal_competition=1,
            new_entrant_threat=1,
            substitute_threat=1,
            supplier_power=1,
            buyer_power=1
        )
        # 最吸引人的行业，分数应接近10
        self.assertAlmostEqual(forces.calculate_attractiveness(), 9.0, places=1)
    
    def test_attractiveness_competitive(self):
        """测试竞争激烈行业（五力都强）"""
        forces = PorterFiveForces(
            internal_competition=10,
            new_entrant_threat=10,
            substitute_threat=10,
            supplier_power=10,
            buyer_power=10
        )
        # 最不吸引人的行业，分数应为0
        self.assertAlmostEqual(forces.calculate_attractiveness(), 0.0, places=1)


class TestIndustryAnalyzer(unittest.TestCase):
    """测试行业分析器"""
    
    def setUp(self):
        self.industry = Industry(
            code="TEST",
            name="测试行业",
            life_cycle=IndustryLifeCycle.GROWTH,
            industry_type=IndustryType.GROWTH,
            five_forces=PorterFiveForces(
                internal_competition=5,
                new_entrant_threat=5,
                substitute_threat=5,
                supplier_power=5,
                buyer_power=5
            ),
            metrics=IndustryMetrics(
                market_size=10000,
                market_growth_rate=25,
                avg_gross_margin=30,
                avg_roe=15,
                cr4=50,
                entry_barrier_score=7
            ),
            policy_support=2
        )
        self.analyzer = IndustryAnalyzer(self.industry)
    
    def test_life_cycle_analysis(self):
        """测试生命周期分析"""
        analysis = self.analyzer.analyze_life_cycle()
        
        self.assertIn("特征", analysis)
        self.assertIn("投资策略", analysis)
        self.assertEqual(analysis["增速"], "20%+")
    
    def test_concentration_oligopoly(self):
        """测试寡头垄断判断"""
        self.industry.metrics.cr4 = 65
        level = self.analyzer.calculate_concentration_level()
        self.assertEqual(level, "寡头垄断")
    
    def test_concentration_monopolistic(self):
        """测试垄断竞争判断"""
        self.industry.metrics.cr4 = 45
        level = self.analyzer.calculate_concentration_level()
        self.assertEqual(level, "垄断竞争")
    
    def test_concentration_perfect(self):
        """测试完全竞争判断"""
        self.industry.metrics.cr4 = 30
        level = self.analyzer.calculate_concentration_level()
        self.assertEqual(level, "完全竞争")
    
    def test_profitability_assessment(self):
        """测试盈利能力评估"""
        assessment = self.analyzer.analyze_profitability()
        
        self.assertIn("毛利率", assessment)
        self.assertIn("ROE", assessment)
    
    def test_industry_score_calculation(self):
        """测试行业评分计算"""
        scores = self.analyzer.calculate_industry_score()
        
        self.assertIn("市场空间", scores)
        self.assertIn("竞争格局", scores)
        self.assertIn("盈利能力", scores)
        self.assertIn("总分", scores)
        self.assertIn("评级", scores)
        
        # 总分应在0-100之间
        self.assertGreaterEqual(scores["总分"], 0)
        self.assertLessEqual(scores["总分"], 100)


class TestIndustryRotator(unittest.TestCase):
    """测试行业轮动"""
    
    def setUp(self):
        self.rotator = IndustryRotator()
    
    def test_recovery_recommendation(self):
        """测试复苏期推荐"""
        rec = self.rotator.get_recommendation("复苏期")
        
        self.assertIn("金融", rec["推荐"])
        self.assertIn("周期", rec["推荐"])
    
    def test_expansion_recommendation(self):
        """测试扩张期推荐"""
        rec = self.rotator.get_recommendation("扩张期")
        
        self.assertIn("科技", rec["推荐"])
    
    def test_stagflation_recommendation(self):
        """测试滞胀期推荐"""
        rec = self.rotator.get_recommendation("滞胀期")
        
        self.assertIn("能源", rec["推荐"])
    
    def test_recession_recommendation(self):
        """测试衰退期推荐"""
        rec = self.rotator.get_recommendation("衰退期")
        
        self.assertIn("医药", rec["推荐"])
    
    def test_industry_position(self):
        """测试行业周期定位"""
        industry = Industry(
            code="BANK",
            name="Bank",
            life_cycle=IndustryLifeCycle.MATURITY,
            industry_type=IndustryType.CYCLICAL
        )
        
        position = self.rotator.analyze_industry_position(industry, "复苏期")
        
        self.assertEqual(position["行业"], "Bank")
        self.assertEqual(position["当前周期"], "复苏期")
        # 验证返回的position包含必要字段
        self.assertIn("建议", position)
        self.assertIn("周期逻辑", position)


class TestIndustryScreener(unittest.TestCase):
    """测试行业筛选器"""
    
    def setUp(self):
        self.industries = [
            Industry("A", "高增长行业", IndustryLifeCycle.GROWTH, IndustryType.GROWTH,
                    metrics=IndustryMetrics(market_growth_rate=30, avg_roe=20)),
            Industry("B", "低增长行业", IndustryLifeCycle.MATURITY, IndustryType.DEFENSIVE,
                    metrics=IndustryMetrics(market_growth_rate=5, avg_roe=8)),
            Industry("C", "高盈利行业", IndustryLifeCycle.MATURITY, IndustryType.DEFENSIVE,
                    metrics=IndustryMetrics(market_growth_rate=10, avg_roe=25)),
        ]
        
        for i in self.industries:
            i.five_forces = PorterFiveForces()
    
    def test_screen_by_growth(self):
        """测试按增速筛选"""
        result = IndustryScreener.screen_by_growth(self.industries, min_growth=20)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "高增长行业")
    
    def test_screen_by_profitability(self):
        """测试按盈利筛选"""
        result = IndustryScreener.screen_by_profitability(self.industries, min_roe=15)
        
        self.assertEqual(len(result), 2)
    
    def test_find_best_industries(self):
        """测试找最优行业"""
        # 给行业添加完整指标以便评分
        for i in self.industries:
            i.metrics.market_size = 10000
            i.metrics.entry_barrier_score = 5
            i.policy_support = 0
        
        best = IndustryScreener.find_best_industries(self.industries, top_n=2)
        
        self.assertEqual(len(best), 2)
        # 验证返回的是元组列表
        self.assertIsInstance(best[0], tuple)
        self.assertIsInstance(best[0][0], Industry)
        self.assertIsInstance(best[0][1], float)


if __name__ == "__main__":
    unittest.main(verbosity=2)
