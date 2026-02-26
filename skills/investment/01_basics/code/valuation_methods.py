"""
估值方法（PE/PB/PS/DCF）- 核心计算模块
包含：各种估值指标计算、DCF模型、敏感性分析等功能
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class ValuationInput:
    """估值输入数据"""
    # 基本信息
    stock_code: str
    stock_name: str
    
    # 股价信息
    current_price: float
    total_shares: float  # 总股本（亿股）
    
    # 财务数据
    eps_ttm: float = 0.0           # TTM每股收益
    eps_forecast: float = 0.0      # 预测每股收益
    book_value_per_share: float = 0.0  # 每股净资产
    revenue_per_share: float = 0.0     # 每股营收
    net_profit: float = 0.0        # 净利润（亿）
    total_equity: float = 0.0      # 净资产（亿）
    total_revenue: float = 0.0     # 总营收（亿）
    
    # 增长数据
    profit_growth_rate: float = 0.0    # 利润增长率%
    revenue_growth_rate: float = 0.0   # 收入增长率%
    
    # DCF参数
    fcf_current: float = 0.0       # 当前自由现金流（亿）
    wacc: float = 0.10             # 加权平均资本成本
    terminal_growth: float = 0.03  # 永续增长率
    forecast_years: int = 10       # 预测年限
    high_growth_rate: float = 0.15 # 高增长阶段增长率
    high_growth_years: int = 5     # 高增长年限
    net_cash: float = 0.0          # 净现金（亿）


@dataclass
class ValuationResult:
    """估值结果"""
    pe_ttm: float = 0.0
    pe_forward: float = 0.0
    pb: float = 0.0
    ps: float = 0.0
    peg: float = 0.0
    dcf_value_per_share: float = 0.0
    
    # 评估结果
    assessment: str = ""
    upside_downside: float = 0.0  # 上涨/下跌空间%


class ValuationCalculator:
    """
    估值计算器
    """
    
    def __init__(self, data: ValuationInput):
        self.data = data
        self.market_cap = data.current_price * data.total_shares
    
    def calculate_pe(self) -> Dict:
        """计算市盈率"""
        result = {}
        
        # TTM PE - 即使为负也返回，亏损企业的PE为负
        if self.data.eps_ttm != 0:
            result["pe_ttm"] = self.data.current_price / self.data.eps_ttm
        else:
            result["pe_ttm"] = None
        
        # 前瞻PE
        if self.data.eps_forecast != 0:
            result["pe_forward"] = self.data.current_price / self.data.eps_forecast
        else:
            result["pe_forward"] = None
        
        return result
    
    def calculate_pb(self) -> float:
        """计算市净率"""
        if self.data.book_value_per_share > 0:
            return self.data.current_price / self.data.book_value_per_share
        return None
    
    def calculate_ps(self) -> float:
        """计算市销率"""
        if self.data.revenue_per_share > 0:
            return self.data.current_price / self.data.revenue_per_share
        return None
    
    def calculate_peg(self) -> float:
        """计算PEG"""
        pe_data = self.calculate_pe()
        pe = pe_data.get("pe_ttm")
        
        if pe and self.data.profit_growth_rate > 0:
            return pe / self.data.profit_growth_rate
        return None
    
    def calculate_dcf(self) -> Dict:
        """
        DCF估值计算
        """
        if self.data.fcf_current <= 0:
            return None
        
        # 生成未来现金流预测
        fcfs = []
        fcf = self.data.fcf_current
        
        # 高增长阶段
        for year in range(1, self.data.high_growth_years + 1):
            fcf = fcf * (1 + self.data.high_growth_rate)
            fcfs.append(fcf)
        
        # 稳定增长阶段
        stable_growth = self.data.terminal_growth + 0.02  # 稳定增长比永续高2%
        for year in range(self.data.high_growth_years + 1, self.data.forecast_years + 1):
            fcf = fcf * (1 + stable_growth)
            fcfs.append(fcf)
        
        # 计算预测期现值
        pv_fcf = 0
        for i, fcf in enumerate(fcfs):
            pv_fcf += fcf / ((1 + self.data.wacc) ** (i + 1))
        
        # 计算终值（戈登增长模型）
        terminal_fcf = fcfs[-1] * (1 + self.data.terminal_growth)
        terminal_value = terminal_fcf / (self.data.wacc - self.data.terminal_growth)
        pv_terminal = terminal_value / ((1 + self.data.wacc) ** self.data.forecast_years)
        
        # 企业价值和股权价值
        enterprise_value = pv_fcf + pv_terminal
        equity_value = enterprise_value + self.data.net_cash
        
        # 每股价值
        value_per_share = (equity_value / self.data.total_shares) if self.data.total_shares > 0 else 0
        
        return {
            "forecast_fcf": fcfs,
            "pv_fcf": pv_fcf,
            "terminal_value": terminal_value,
            "pv_terminal": pv_terminal,
            "enterprise_value": enterprise_value,
            "equity_value": equity_value,
            "value_per_share": value_per_share
        }
    
    def comprehensive_valuation(self) -> ValuationResult:
        """综合估值"""
        result = ValuationResult()
        
        # 计算各指标
        pe_data = self.calculate_pe()
        result.pe_ttm = pe_data.get("pe_ttm", 0)
        result.pe_forward = pe_data.get("pe_forward", 0)
        result.pb = self.calculate_pb() or 0
        result.ps = self.calculate_ps() or 0
        result.peg = self.calculate_peg() or 0
        
        # DCF估值
        dcf_result = self.calculate_dcf()
        if dcf_result:
            result.dcf_value_per_share = dcf_result["value_per_share"]
        
        # 综合评估
        valuations = []
        
        if result.pe_ttm > 0:
            # 根据PE绝对水平评估
            if result.pe_ttm < 10:
                valuations.append(("低PE", 0.8))
            elif result.pe_ttm < 20:
                valuations.append(("合理PE", 1.0))
            elif result.pe_ttm < 30:
                valuations.append(("偏高PE", 1.2))
            else:
                valuations.append(("高PE", 1.4))
        
        if result.peg > 0:
            # 根据PEG评估
            if result.peg < 0.8:
                valuations.append(("低估", 0.9))
            elif result.peg < 1.2:
                valuations.append(("合理", 1.0))
            else:
                valuations.append(("高估", 1.1))
        
        if result.dcf_value_per_share > 0:
            # 根据DCF评估
            dcf_premium = self.data.current_price / result.dcf_value_per_share
            if dcf_premium < 0.9:
                valuations.append(("低于内在价值", 0.9))
            elif dcf_premium < 1.1:
                valuations.append(("接近内在价值", 1.0))
            else:
                valuations.append(("高于内在价值", 1.1))
        
        # 综合判断
        if valuations:
            avg_multiplier = sum([v[1] for v in valuations]) / len(valuations)
            implied_value = self.data.current_price / avg_multiplier
            result.upside_downside = (implied_value / self.data.current_price - 1) * 100
            
            if result.upside_downside > 20:
                result.assessment = "显著低估"
            elif result.upside_downside > 5:
                result.assessment = "轻度低估"
            elif result.upside_downside > -5:
                result.assessment = "估值合理"
            elif result.upside_downside > -20:
                result.assessment = "轻度高估"
            else:
                result.assessment = "显著高估"
        else:
            result.assessment = "无法评估"
        
        return result
    
    def sensitivity_analysis(self, wacc_range: List[float], growth_range: List[float]) -> Dict:
        """
        DCF敏感性分析
        
        Args:
            wacc_range: WACC取值范围
            growth_range: 永续增长率取值范围
        
        Returns:
            敏感性分析矩阵
        """
        results = {}
        base_wacc = self.data.wacc
        base_growth = self.data.terminal_growth
        
        for wacc in wacc_range:
            results[wacc] = {}
            for growth in growth_range:
                self.data.wacc = wacc
                self.data.terminal_growth = growth
                dcf = self.calculate_dcf()
                if dcf:
                    results[wacc][growth] = dcf["value_per_share"]
                else:
                    results[wacc][growth] = 0
        
        # 恢复原始值
        self.data.wacc = base_wacc
        self.data.terminal_growth = base_growth
        
        return results


class ValuationScreening:
    """
    估值筛选器
    """
    
    @staticmethod
    def screen_by_pe(stocks: List[ValuationInput], max_pe: float = 20) -> List[ValuationInput]:
        """按PE筛选低估值股票"""
        result = []
        for stock in stocks:
            calc = ValuationCalculator(stock)
            pe_data = calc.calculate_pe()
            pe = pe_data.get("pe_ttm")
            if pe and pe <= max_pe and pe > 0:
                result.append(stock)
        return result
    
    @staticmethod
    def screen_by_pb(stocks: List[ValuationInput], max_pb: float = 1.5) -> List[ValuationInput]:
        """按PB筛选破净/低估值股票"""
        result = []
        for stock in stocks:
            calc = ValuationCalculator(stock)
            pb = calc.calculate_pb()
            if pb and pb <= max_pb and pb > 0:
                result.append(stock)
        return result
    
    @staticmethod
    def screen_by_peg(stocks: List[ValuationInput], max_peg: float = 1.0) -> List[ValuationInput]:
        """按PEG筛选成长股"""
        result = []
        for stock in stocks:
            calc = ValuationCalculator(stock)
            peg = calc.calculate_peg()
            if peg and peg <= max_peg and peg > 0:
                result.append(stock)
        return result
    
    @staticmethod
    def find_undervalued(stocks: List[ValuationInput], margin_of_safety: float = 0.3) -> List[Dict]:
        """
        寻找被低估的股票
        
        Args:
            stocks: 股票列表
            margin_of_safety: 安全边际（30%表示低于内在价值30%）
        
        Returns:
            被低估股票列表及详细信息
        """
        undervalued = []
        
        for stock in stocks:
            calc = ValuationCalculator(stock)
            valuation = calc.comprehensive_valuation()
            
            # 使用DCF作为内在价值参考
            dcf_result = calc.calculate_dcf()
            if dcf_result and dcf_result["value_per_share"] > 0:
                intrinsic_value = dcf_result["value_per_share"]
                discount = (intrinsic_value - stock.current_price) / intrinsic_value
                
                if discount >= margin_of_safety:
                    undervalued.append({
                        "stock": stock,
                        "current_price": stock.current_price,
                        "intrinsic_value": intrinsic_value,
                        "discount": discount * 100,
                        "pe": valuation.pe_ttm,
                        "pb": valuation.pb,
                        "peg": valuation.peg
                    })
        
        # 按低估程度排序
        undervalued.sort(key=lambda x: x["discount"], reverse=True)
        return undervalued


# ==================== 演示代码 ====================

def demo_valuation_consumer():
    """演示消费股估值"""
    print("\n" + "="*60)
    print("   演示：消费股估值（茅台风格）")
    print("="*60)
    
    stock = ValuationInput(
        stock_code="MOUTAI",
        stock_name="贵州茅台",
        current_price=1600,
        total_shares=12.56,
        eps_ttm=58.0,
        eps_forecast=65.0,
        book_value_per_share=160.0,
        revenue_per_share=90.0,
        net_profit=730,
        total_equity=2000,
        total_revenue=1350,
        profit_growth_rate=15,
        revenue_growth_rate=12,
        fcf_current=700,
        wacc=0.09,
        terminal_growth=0.03,
        net_cash=1500
    )
    
    calc = ValuationCalculator(stock)
    result = calc.comprehensive_valuation()
    
    print(f"\n{stock.stock_name} ({stock.stock_code})")
    print(f"当前股价: {stock.current_price}元")
    print(f"\n估值指标:")
    print(f"  PE(TTM):      {result.pe_ttm:.1f}倍")
    print(f"  PE(前瞻):     {result.pe_forward:.1f}倍")
    print(f"  PB:           {result.pb:.2f}倍")
    print(f"  PS:           {result.ps:.2f}倍")
    print(f"  PEG:          {result.peg:.2f}")
    print(f"  DCF估值:      {result.dcf_value_per_share:.0f}元")
    print(f"\n综合评估: {result.assessment}")
    print(f"涨跌空间: {result.upside_downside:+.1f}%")


def demo_valuation_bank():
    """演示银行股估值"""
    print("\n" + "="*60)
    print("   演示：银行股估值（招行风格）")
    print("="*60)
    
    stock = ValuationInput(
        stock_code="CMB",
        stock_name="招商银行",
        current_price=35.0,
        total_shares=252,
        eps_ttm=5.5,
        eps_forecast=5.8,
        book_value_per_share=32.0,
        revenue_per_share=15.0,
        net_profit=1400,
        total_equity=8000,
        total_revenue=3400,
        profit_growth_rate=6,
        fcf_current=1300,
        wacc=0.10,
        terminal_growth=0.02,
        net_cash=-5000  # 净负债
    )
    
    calc = ValuationCalculator(stock)
    result = calc.comprehensive_valuation()
    
    print(f"\n{stock.stock_name} ({stock.stock_code})")
    print(f"当前股价: {stock.current_price}元")
    print(f"\n估值指标:")
    print(f"  PE(TTM):      {result.pe_ttm:.1f}倍")
    print(f"  PB:           {result.pb:.2f}倍")
    print(f"  PS:           {result.ps:.2f}倍")
    print(f"\n综合评估: {result.assessment}")
    
    # ROE-PB关系
    roe = stock.net_profit / stock.total_equity * 100
    print(f"\nROE-PB分析:")
    print(f"  ROE:          {roe:.1f}%")
    print(f"  当前PB:       {result.pb:.2f}")
    print(f"  理论合理PB:   {roe/10:.2f}（假设要求回报率10%）")


def demo_valuation_tech():
    """演示科技股估值"""
    print("\n" + "="*60)
    print("   演示：科技股估值（宁德时代风格）")
    print("="*60)
    
    stock = ValuationInput(
        stock_code="CATL",
        stock_name="宁德时代",
        current_price=200.0,
        total_shares=44.0,
        eps_ttm=6.0,
        eps_forecast=8.0,
        book_value_per_share=45.0,
        revenue_per_share=100.0,
        net_profit=260,
        total_equity=2000,
        total_revenue=4400,
        profit_growth_rate=30,
        revenue_growth_rate=25,
        fcf_current=200,
        wacc=0.11,
        terminal_growth=0.03,
        high_growth_rate=0.25,
        net_cash=800
    )
    
    calc = ValuationCalculator(stock)
    result = calc.comprehensive_valuation()
    
    print(f"\n{stock.stock_name} ({stock.stock_code})")
    print(f"当前股价: {stock.current_price}元")
    print(f"\n估值指标:")
    print(f"  PE(TTM):      {result.pe_ttm:.1f}倍")
    print(f"  PE(前瞻):     {result.pe_forward:.1f}倍")
    print(f"  PEG:          {result.peg:.2f}")
    print(f"  PS:           {result.ps:.2f}倍")
    print(f"  DCF估值:      {result.dcf_value_per_share:.0f}元")
    print(f"\n综合评估: {result.assessment}")


def demo_dcf_sensitivity():
    """演示DCF敏感性分析"""
    print("\n" + "="*60)
    print("   演示：DCF敏感性分析")
    print("="*60)
    
    stock = ValuationInput(
        stock_code="DEMO",
        stock_name="示例公司",
        current_price=100.0,
        total_shares=10.0,
        fcf_current=50.0,
        wacc=0.10,
        terminal_growth=0.03,
        high_growth_rate=0.15,
        net_cash=100.0
    )
    
    calc = ValuationCalculator(stock)
    
    # 敏感性分析
    wacc_range = [0.08, 0.09, 0.10, 0.11, 0.12]
    growth_range = [0.02, 0.025, 0.03, 0.035, 0.04]
    
    sensitivity = calc.sensitivity_analysis(wacc_range, growth_range)
    
    print("\nDCF敏感性分析（单位：元/股）")
    print("\n        WACC →")
    header = "g↓      " + "".join([f"{w*100:.0f}%".center(10) for w in wacc_range])
    print(header)
    print("-" * 70)
    
    for growth in growth_range:
        row = f"{growth*100:.1f}%    "
        for wacc in wacc_range:
            value = sensitivity[wacc][growth]
            row += f"{value:8.1f}  "
        print(row)
    
    print("\n说明：表格显示不同WACC和永续增长率组合下的DCF估值")


def demo_screening():
    """演示估值筛选"""
    print("\n" + "="*60)
    print("   演示：估值筛选")
    print("="*60)
    
    # 创建股票列表
    stocks = [
        ValuationInput("A", "股票A", 10, 10, eps_ttm=1.0, profit_growth_rate=10, fcf_current=8),
        ValuationInput("B", "股票B", 20, 10, eps_ttm=1.0, profit_growth_rate=20, fcf_current=15),
        ValuationInput("C", "股票C", 50, 10, eps_ttm=1.0, profit_growth_rate=30, fcf_current=10),
        ValuationInput("D", "股票D", 8, 10, eps_ttm=1.0, profit_growth_rate=5, fcf_current=5),
        ValuationInput("E", "股票E", 25, 10, eps_ttm=1.0, profit_growth_rate=15, fcf_current=20),
    ]
    
    print("\n原始股票列表（股价、EPS、增长率）:")
    for s in stocks:
        print(f"  {s.stock_name}: 股价{s.current_price}元, EPS{s.eps_ttm}, 增长{s.profit_growth_rate}%")
    
    # 低PE筛选
    low_pe = ValuationScreening.screen_by_pe(stocks, max_pe=15)
    print(f"\n低PE筛选（PE≤15）:")
    for s in low_pe:
        calc = ValuationCalculator(s)
        pe = calc.calculate_pe()["pe_ttm"]
        print(f"  {s.stock_name}: PE={pe:.1f}")
    
    # PEG筛选
    low_peg = ValuationScreening.screen_by_peg(stocks, max_peg=1.0)
    print(f"\n低PEG筛选（PEG≤1.0）:")
    for s in low_peg:
        calc = ValuationCalculator(s)
        peg = calc.calculate_peg()
        print(f"  {s.stock_name}: PEG={peg:.2f}")
    
    # 寻找低估股票
    undervalued = ValuationScreening.find_undervalued(stocks, margin_of_safety=0.2)
    print(f"\n低估股票筛选（安全边际≥20%）:")
    for item in undervalued:
        print(f"  {item['stock'].stock_name}: 当前{item['current_price']:.0f}元, "
              f"内在价值{item['intrinsic_value']:.0f}元, 低估{item['discount']:.1f}%")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("   估值方法（PE/PB/PS/DCF）- 实战代码演示")
    print("="*60)
    
    demo_valuation_consumer()
    demo_valuation_bank()
    demo_valuation_tech()
    demo_dcf_sensitivity()
    demo_screening()
    
    print("\n" + "="*60)
    print("  所有演示完成!")
    print("="*60)
