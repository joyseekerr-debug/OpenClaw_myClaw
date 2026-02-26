"""
财务报表阅读 - 核心分析模块
包含：财务比率计算、杜邦分析、财务健康评分、财报数据提取等功能
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime


@dataclass
class BalanceSheet:
    """资产负债表"""
    # 流动资产
    cash: float = 0.0                    # 货币资金
    receivables: float = 0.0             # 应收账款
    inventory: float = 0.0               # 存货
    prepayments: float = 0.0             # 预付款项
    current_assets: float = 0.0          # 流动资产合计
    
    # 非流动资产
    fixed_assets: float = 0.0            # 固定资产
    intangible_assets: float = 0.0       # 无形资产
    goodwill: float = 0.0                # 商誉
    total_assets: float = 0.0            # 资产总计
    
    # 流动负债
    short_term_loans: float = 0.0        # 短期借款
    payables: float = 0.0                # 应付账款
    current_liabilities: float = 0.0     # 流动负债合计
    
    # 非流动负债
    long_term_loans: float = 0.0         # 长期借款
    total_liabilities: float = 0.0       # 负债合计
    
    # 所有者权益
    share_capital: float = 0.0           # 股本
    retained_earnings: float = 0.0       # 未分配利润
    equity: float = 0.0                  # 所有者权益


@dataclass
class IncomeStatement:
    """利润表"""
    revenue: float = 0.0                 # 营业收入
    cost_of_sales: float = 0.0           # 营业成本
    gross_profit: float = 0.0            # 毛利
    
    sales_expense: float = 0.0           # 销售费用
    admin_expense: float = 0.0           # 管理费用
    rd_expense: float = 0.0              # 研发费用
    finance_expense: float = 0.0         # 财务费用
    
    operating_profit: float = 0.0        # 营业利润
    non_operating_income: float = 0.0    # 营业外收入
    non_operating_expense: float = 0.0   # 营业外支出
    profit_before_tax: float = 0.0       # 利润总额
    tax: float = 0.0                     # 所得税
    net_profit: float = 0.0              # 净利润
    net_profit_deduction: float = 0.0    # 扣非净利润


@dataclass
class CashFlowStatement:
    """现金流量表"""
    operating_cashflow: float = 0.0      # 经营活动现金流
    investing_cashflow: float = 0.0      # 投资活动现金流
    financing_cashflow: float = 0.0      # 筹资活动现金流
    capex: float = 0.0                   # 资本支出


@dataclass
class FinancialRatios:
    """财务比率"""
    # 偿债能力
    current_ratio: float = 0.0           # 流动比率
    quick_ratio: float = 0.0             # 速动比率
    debt_to_asset: float = 0.0           # 资产负债率
    equity_multiplier: float = 0.0       # 权益乘数
    
    # 盈利能力
    gross_margin: float = 0.0            # 毛利率
    operating_margin: float = 0.0        # 营业利润率
    net_margin: float = 0.0              # 净利率
    roe: float = 0.0                     # 净资产收益率
    roa: float = 0.0                     # 总资产收益率
    
    # 运营效率
    asset_turnover: float = 0.0          # 总资产周转率
    
    # 现金流质量
    cashflow_to_profit: float = 0.0      # 经营现金流/净利润
    free_cashflow: float = 0.0           # 自由现金流


class FinancialAnalyzer:
    """
    财务分析器
    """
    
    def __init__(
        self,
        balance_sheet: BalanceSheet,
        income: IncomeStatement,
        cashflow: CashFlowStatement
    ):
        self.bs = balance_sheet
        self.inc = income
        self.cf = cashflow
    
    def calculate_ratios(self) -> FinancialRatios:
        """计算财务比率"""
        ratios = FinancialRatios()
        
        # 偿债能力
        if self.bs.current_liabilities > 0:
            ratios.current_ratio = self.bs.current_assets / self.bs.current_liabilities
            ratios.quick_ratio = (self.bs.current_assets - self.bs.inventory) / self.bs.current_liabilities
        
        if self.bs.total_assets > 0:
            ratios.debt_to_asset = self.bs.total_liabilities / self.bs.total_assets * 100
        
        if self.bs.equity > 0:
            ratios.equity_multiplier = self.bs.total_assets / self.bs.equity
        
        # 盈利能力
        if self.inc.revenue > 0:
            ratios.gross_margin = (self.inc.revenue - self.inc.cost_of_sales) / self.inc.revenue * 100
            ratios.operating_margin = self.inc.operating_profit / self.inc.revenue * 100
            ratios.net_margin = self.inc.net_profit / self.inc.revenue * 100
        
        if self.bs.equity > 0:
            ratios.roe = self.inc.net_profit / self.bs.equity * 100
        
        if self.bs.total_assets > 0:
            ratios.roa = self.inc.net_profit / self.bs.total_assets * 100
            ratios.asset_turnover = self.inc.revenue / self.bs.total_assets
        
        # 现金流质量
        if self.inc.net_profit > 0:
            ratios.cashflow_to_profit = self.cf.operating_cashflow / self.inc.net_profit * 100
        
        ratios.free_cashflow = self.cf.operating_cashflow - self.cf.capex
        
        return ratios
    
    def dupont_analysis(self) -> Dict:
        """
        杜邦分析
        ROE = 净利率 × 资产周转率 × 权益乘数
        """
        if self.inc.revenue <= 0 or self.bs.total_assets <= 0 or self.bs.equity <= 0:
            return {}
        
        net_margin = self.inc.net_profit / self.inc.revenue
        asset_turnover = self.inc.revenue / self.bs.total_assets
        equity_multiplier = self.bs.total_assets / self.bs.equity
        roe = net_margin * asset_turnover * equity_multiplier
        
        return {
            "net_margin": net_margin * 100,
            "asset_turnover": asset_turnover,
            "equity_multiplier": equity_multiplier,
            "roe": roe * 100,
            "profit_contribution": net_margin * asset_turnover * equity_multiplier * 100,
        }
    
    def calculate_health_score(self) -> Dict:
        """
        计算财务健康度评分
        """
        ratios = self.calculate_ratios()
        scores = {}
        
        # 1. 偿债能力 (25分)
        debt_score = 0
        if 1.5 <= ratios.current_ratio <= 2.5:
            debt_score += 10
        elif ratios.current_ratio >= 1.0:
            debt_score += 5
        
        if 0.5 <= ratios.quick_ratio <= 1.5:
            debt_score += 8
        elif ratios.quick_ratio >= 0.8:
            debt_score += 4
        
        if ratios.debt_to_asset <= 0.5:
            debt_score += 7
        elif ratios.debt_to_asset <= 0.6:
            debt_score += 4
        
        scores["debt_ability"] = min(debt_score, 25)
        
        # 2. 盈利能力 (25分)
        profit_score = 0
        if ratios.roe >= 15:
            profit_score += 10
        elif ratios.roe >= 10:
            profit_score += 6
        elif ratios.roe >= 5:
            profit_score += 3
        
        if ratios.gross_margin >= 40:
            profit_score += 8
        elif ratios.gross_margin >= 30:
            profit_score += 5
        elif ratios.gross_margin >= 20:
            profit_score += 3
        
        if ratios.net_margin >= 15:
            profit_score += 7
        elif ratios.net_margin >= 10:
            profit_score += 4
        elif ratios.net_margin >= 5:
            profit_score += 2
        
        scores["profitability"] = min(profit_score, 25)
        
        # 3. 现金流质量 (25分)
        cashflow_score = 0
        if ratios.cashflow_to_profit >= 100:
            cashflow_score += 15
        elif ratios.cashflow_to_profit >= 80:
            cashflow_score += 10
        elif ratios.cashflow_to_profit >= 60:
            cashflow_score += 5
        
        if ratios.free_cashflow > 0:
            cashflow_score += 10
        elif ratios.free_cashflow > -self.inc.net_profit * 0.5:
            cashflow_score += 5
        
        scores["cashflow_quality"] = min(cashflow_score, 25)
        
        # 4. 运营效率 (25分)
        efficiency_score = 0
        if ratios.asset_turnover >= 1.0:
            efficiency_score += 15
        elif ratios.asset_turnover >= 0.5:
            efficiency_score += 8
        elif ratios.asset_turnover >= 0.3:
            efficiency_score += 4
        
        # 营收增长（简化处理，假设）
        efficiency_score += 10
        
        scores["efficiency"] = min(efficiency_score, 25)
        
        # 总分
        scores["total"] = sum(scores.values())
        
        # 评级
        if scores["total"] >= 80:
            scores["rating"] = "A"
            scores["assessment"] = "财务健康"
        elif scores["total"] >= 60:
            scores["rating"] = "B"
            scores["assessment"] = "财务良好"
        elif scores["total"] >= 40:
            scores["rating"] = "C"
            scores["assessment"] = "财务一般"
        else:
            scores["rating"] = "D"
            scores["assessment"] = "财务风险"
        
        return scores
    
    def analyze_cashflow_pattern(self) -> Dict:
        """
        分析现金流模式
        """
        pattern = {}
        
        # 判断各类现金流正负
        op_positive = self.cf.operating_cashflow > 0
        inv_positive = self.cf.investing_cashflow > 0
        fin_positive = self.cf.financing_cashflow > 0
        
        # 模式判断
        if op_positive and not inv_positive and not fin_positive:
            pattern["type"] = "奶牛型"
            pattern["description"] = "经营现金流入，投资支出，还债或分红"
            pattern["health"] = "健康"
        elif op_positive and not inv_positive and fin_positive:
            pattern["type"] = "扩张型"
            pattern["description"] = "经营和融资支持投资扩张"
            pattern["health"] = "关注扩张效率"
        elif not op_positive and not inv_positive and fin_positive:
            pattern["type"] = "烧钱型"
            pattern["description"] = "依赖融资维持经营和投资"
            pattern["health"] = "风险"
        elif not op_positive and inv_positive and not fin_positive:
            pattern["type"] = "衰退型"
            pattern["description"] = "变卖资产偿还债务"
            pattern["health"] = "高风险"
        elif op_positive and inv_positive and not fin_positive:
            pattern["type"] = "成熟型"
            pattern["description"] = "经营良好，投资收益，还债"
            pattern["health"] = "健康"
        else:
            pattern["type"] = "其他"
            pattern["description"] = "需具体分析"
            pattern["health"] = "待评估"
        
        pattern["operating"] = "流入" if op_positive else "流出"
        pattern["investing"] = "流入" if inv_positive else "流出"
        pattern["financing"] = "流入" if fin_positive else "流出"
        
        return pattern
    
    def detect_warnings(self) -> List[Dict]:
        """
        检测财务风险信号
        """
        warnings = []
        
        # 1. 现金流警告
        if self.cf.operating_cashflow < 0:
            warnings.append({
                "type": "现金流",
                "level": "高",
                "message": "经营现金流为负，主营业务无法产生正向现金"
            })
        elif self.cf.operating_cashflow < self.inc.net_profit * 0.5:
            warnings.append({
                "type": "现金流",
                "level": "中",
                "message": "经营现金流显著低于净利润，利润含金量低"
            })
        
        # 2. 偿债能力警告
        if self.bs.current_liabilities > 0:
            current_ratio = self.bs.current_assets / self.bs.current_liabilities
            if current_ratio < 1.0:
                warnings.append({
                    "type": "偿债能力",
                    "level": "高",
                    "message": f"流动比率{current_ratio:.2f}<1，短期偿债压力大"
                })
        
        if self.bs.total_assets > 0:
            debt_ratio = self.bs.total_liabilities / self.bs.total_assets
            if debt_ratio > 0.7:
                warnings.append({
                    "type": "偿债能力",
                    "level": "高",
                    "message": f"资产负债率{debt_ratio*100:.1f}%>70%，财务杠杆过高"
                })
        
        # 3. 商誉警告
        if self.bs.equity > 0:
            goodwill_ratio = self.bs.goodwill / self.bs.equity
            if goodwill_ratio > 0.3:
                warnings.append({
                    "type": "资产质量",
                    "level": "中",
                    "message": f"商誉占净资产{goodwill_ratio*100:.1f}%，减值风险需关注"
                })
        
        # 4. 盈利能力警告
        if self.inc.revenue > 0:
            if self.inc.net_profit < 0:
                warnings.append({
                    "type": "盈利能力",
                    "level": "高",
                    "message": "净利润为负，企业处于亏损状态"
                })
        
        return warnings


# ==================== 演示代码 ====================

def demo_financial_analysis():
    """演示财务分析"""
    print("\n" + "="*60)
    print("   演示：财务分析 - 白酒企业")
    print("="*60)
    
    # 模拟贵州茅台财务数据
    balance_sheet = BalanceSheet(
        cash=150_000_000,           # 1.5亿现金
        receivables=5_000_000,      # 500万应收（极少，先款后货）
        inventory=30_000_000,       # 3000万存货（基酒）
        current_assets=200_000_000,
        total_assets=250_000_000,
        current_liabilities=40_000_000,
        total_liabilities=48_750_000,
        equity=201_250_000,
        goodwill=0
    )
    
    income = IncomeStatement(
        revenue=120_000_000,
        cost_of_sales=10_200_000,
        gross_profit=109_800_000,
        sales_expense=12_000_000,
        admin_expense=8_000_000,
        operating_profit=85_000_000,
        profit_before_tax=87_000_000,
        tax=21_750_000,
        net_profit=65_250_000,
        net_profit_deduction=64_000_000
    )
    
    cashflow = CashFlowStatement(
        operating_cashflow=70_000_000,
        investing_cashflow=-5_000_000,
        financing_cashflow=-30_000_000,
        capex=5_000_000
    )
    
    analyzer = FinancialAnalyzer(balance_sheet, income, cashflow)
    
    # 计算比率
    ratios = analyzer.calculate_ratios()
    print("\n财务比率分析：")
    print(f"  流动比率：      {ratios.current_ratio:.2f}")
    print(f"  速动比率：      {ratios.quick_ratio:.2f}")
    print(f"  资产负债率：    {ratios.debt_to_asset*100:.1f}%")
    print(f"  毛利率：        {ratios.gross_margin:.1f}%")
    print(f"  净利率：        {ratios.net_margin:.1f}%")
    print(f"  ROE：           {ratios.roe:.1f}%")
    print(f"  经营现金流/利润：{ratios.cashflow_to_profit:.1f}%")
    print(f"  自由现金流：    {ratios.free_cashflow:,.0f}")
    
    # 杜邦分析
    dupont = analyzer.dupont_analysis()
    print("\n杜邦分析：")
    print(f"  净利率：        {dupont['net_margin']:.2f}%")
    print(f"  资产周转率：    {dupont['asset_turnover']:.2f}")
    print(f"  权益乘数：      {dupont['equity_multiplier']:.2f}")
    print(f"  ROE：           {dupont['roe']:.2f}%")
    
    # 健康评分
    health = analyzer.calculate_health_score()
    print("\n财务健康评分：")
    print(f"  偿债能力：      {health['debt_ability']}/25")
    print(f"  盈利能力：      {health['profitability']}/25")
    print(f"  现金流质量：    {health['cashflow_quality']}/25")
    print(f"  运营效率：      {health['efficiency']}/25")
    print(f"  总分：          {health['total']}/100")
    print(f"  评级：          {health['rating']} ({health['assessment']})")
    
    # 现金流模式
    pattern = analyzer.analyze_cashflow_pattern()
    print(f"\n现金流模式：{pattern['type']}")
    print(f"  经营：{pattern['operating']}, 投资：{pattern['investing']}, 融资：{pattern['financing']}")
    print(f"  描述：{pattern['description']}")
    
    # 风险警告
    warnings = analyzer.detect_warnings()
    if warnings:
        print("\n风险警告：")
        for w in warnings:
            print(f"  [{w['level']}] {w['type']}: {w['message']}")
    else:
        print("\n无重大财务风险")


def demo_tech_company():
    """演示科技企业分析"""
    print("\n" + "="*60)
    print("   演示：财务分析 - 科技企业")
    print("="*60)
    
    # 模拟科技公司财务数据
    balance_sheet = BalanceSheet(
        cash=80_000_000,
        receivables=30_000_000,
        inventory=5_000_000,
        current_assets=130_000_000,
        total_assets=200_000_000,
        current_liabilities=60_000_000,
        total_liabilities=84_600_000,
        equity=115_400_000,
        goodwill=20_000_000
    )
    
    income = IncomeStatement(
        revenue=150_000_000,
        cost_of_sales=82_200_000,
        gross_profit=67_800_000,
        sales_expense=20_000_000,
        admin_expense=12_000_000,
        rd_expense=18_750_000,  # 研发投入大
        operating_profit=15_000_000,
        profit_before_tax=16_000_000,
        tax=4_000_000,
        net_profit=12_000_000,
        net_profit_deduction=10_500_000
    )
    
    cashflow = CashFlowStatement(
        operating_cashflow=15_000_000,
        investing_cashflow=-40_000_000,  # 大量投资
        financing_cashflow=30_000_000,
        capex=35_000_000
    )
    
    analyzer = FinancialAnalyzer(balance_sheet, income, cashflow)
    
    ratios = analyzer.calculate_ratios()
    print("\n财务比率分析：")
    print(f"  流动比率：      {ratios.current_ratio:.2f}")
    print(f"  毛利率：        {ratios.gross_margin:.1f}%")
    print(f"  研发费用率：    {income.rd_expense/income.revenue*100:.1f}%")
    print(f"  净利率：        {ratios.net_margin:.1f}%")
    print(f"  ROE：           {ratios.roe:.1f}%")
    
    pattern = analyzer.analyze_cashflow_pattern()
    print(f"\n现金流模式：{pattern['type']}")
    print(f"  描述：{pattern['description']}")
    
    warnings = analyzer.detect_warnings()
    if warnings:
        print("\n风险警告：")
        for w in warnings:
            print(f"  [{w['level']}] {w['type']}: {w['message']}")


def demo_warning_detection():
    """演示风险检测"""
    print("\n" + "="*60)
    print("   演示：财务风险检测")
    print("="*60)
    
    # 有风险的企业
    balance_sheet = BalanceSheet(
        cash=10_000_000,
        receivables=80_000_000,  # 应收过高
        current_assets=100_000_000,
        total_assets=150_000_000,
        short_term_loans=90_000_000,  # 短期借款高
        current_liabilities=110_000_000,
        total_liabilities=130_000_000,
        equity=20_000_000,
        goodwill=15_000_000  # 商誉高
    )
    
    income = IncomeStatement(
        revenue=100_000_000,
        cost_of_sales=80_000_000,
        net_profit=2_000_000
    )
    
    cashflow = CashFlowStatement(
        operating_cashflow=-10_000_000,  # 经营现金流为负
        investing_cashflow=-5_000_000,
        financing_cashflow=20_000_000,
        capex=5_000_000
    )
    
    analyzer = FinancialAnalyzer(balance_sheet, income, cashflow)
    
    warnings = analyzer.detect_warnings()
    print("\n检测到的风险信号：")
    for w in warnings:
        print(f"\n  [{w['level']}风险] {w['type']}")
        print(f"    {w['message']}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("   财务报表阅读 - 实战代码演示")
    print("="*60)
    
    demo_financial_analysis()
    demo_tech_company()
    demo_warning_detection()
    
    print("\n" + "="*60)
    print("  所有演示完成!")
    print("="*60)
