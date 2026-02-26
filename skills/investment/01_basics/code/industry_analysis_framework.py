"""
行业分析框架 - 核心分析模块
包含：波特五力分析、行业评分、行业轮动模型等功能
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class IndustryLifeCycle(Enum):
    """行业生命周期"""
    INTRODUCTION = "导入期"
    GROWTH = "成长期"
    MATURITY = "成熟期"
    DECLINE = "衰退期"


class IndustryType(Enum):
    """行业类型"""
    CYCLICAL = "周期型"
    DEFENSIVE = "防御型"
    GROWTH = "成长型"


@dataclass
class PorterFiveForces:
    """波特五力分析"""
    internal_competition: int = 5      # 行业内竞争 (1-10, 1=弱, 10=强)
    new_entrant_threat: int = 5        # 新进入者威胁
    substitute_threat: int = 5         # 替代品威胁
    supplier_power: int = 5            # 供应商议价能力
    buyer_power: int = 5               # 买方议价能力
    
    def calculate_attractiveness(self) -> float:
        """
        计算行业吸引力
        分数越低越吸引人（竞争压力小）
        """
        total = (self.internal_competition + 
                self.new_entrant_threat + 
                self.substitute_threat + 
                self.supplier_power + 
                self.buyer_power)
        return 10 - (total / 5)  # 转换为1-10分，越高越好


@dataclass
class IndustryMetrics:
    """行业关键指标"""
    # 市场规模
    market_size: float = 0.0           # 市场规模（亿元）
    market_growth_rate: float = 0.0    # 市场增长率%
    
    # 盈利能力
    avg_gross_margin: float = 0.0      # 平均毛利率%
    avg_roe: float = 0.0               # 平均ROE%
    
    # 集中度
    cr4: float = 0.0                   # 前4大集中度%
    cr8: float = 0.0                   # 前8大集中度%
    
    # 进入壁垒
    entry_barrier_score: float = 5.0   # 进入壁垒评分 (1-10)


@dataclass
class Industry:
    """行业数据类"""
    code: str
    name: str
    life_cycle: IndustryLifeCycle
    industry_type: IndustryType
    five_forces: PorterFiveForces = field(default_factory=PorterFiveForces)
    metrics: IndustryMetrics = field(default_factory=IndustryMetrics)
    policy_support: int = 0            # 政策支持度 (-5到+5)


class IndustryAnalyzer:
    """
    行业分析器
    """
    
    def __init__(self, industry: Industry):
        self.industry = industry
    
    def analyze_life_cycle(self) -> Dict:
        """分析生命周期阶段特征"""
        stage = self.industry.life_cycle
        
        characteristics = {
            IndustryLifeCycle.INTRODUCTION: {
                "特征": "技术不成熟，市场教育成本高，渗透率极低",
                "增速": "波动大",
                "竞争": "格局未定",
                "盈利": "普遍亏损",
                "投资策略": "高风险高回报，适合风投",
                "风险等级": "极高"
            },
            IndustryLifeCycle.GROWTH: {
                "特征": "需求快速增长，渗透率快速提升",
                "增速": "20%+",
                "竞争": "参与者增加，格局形成中",
                "盈利": "规模效应显现，盈利改善",
                "投资策略": "投资黄金期，优选龙头",
                "风险等级": "中等"
            },
            IndustryLifeCycle.MATURITY: {
                "特征": "增长放缓，格局稳定",
                "增速": "5-10%",
                "竞争": "集中度提升，龙头优势明显",
                "盈利": "盈利稳定，现金流好",
                "投资策略": "关注龙头，重视分红",
                "风险等级": "较低"
            },
            IndustryLifeCycle.DECLINE: {
                "特征": "需求萎缩，产能过剩",
                "增速": "负增长",
                "竞争": "价格战，洗牌",
                "盈利": "盈利下滑甚至亏损",
                "投资策略": "回避或博弈反弹",
                "风险等级": "高"
            }
        }
        
        return characteristics.get(stage, {})
    
    def calculate_concentration_level(self) -> str:
        """判断集中度水平"""
        cr4 = self.industry.metrics.cr4
        
        if cr4 >= 60:
            return "寡头垄断"
        elif cr4 >= 40:
            return "垄断竞争"
        else:
            return "完全竞争"
    
    def analyze_profitability(self) -> Dict:
        """分析盈利能力"""
        metrics = self.industry.metrics
        
        assessment = {}
        
        # 毛利率评估
        if metrics.avg_gross_margin >= 40:
            assessment["毛利率"] = "优秀"
        elif metrics.avg_gross_margin >= 25:
            assessment["毛利率"] = "良好"
        elif metrics.avg_gross_margin >= 15:
            assessment["毛利率"] = "一般"
        else:
            assessment["毛利率"] = "较差"
        
        # ROE评估
        if metrics.avg_roe >= 15:
            assessment["ROE"] = "优秀"
        elif metrics.avg_roe >= 10:
            assessment["ROE"] = "良好"
        elif metrics.avg_roe >= 5:
            assessment["ROE"] = "一般"
        else:
            assessment["ROE"] = "较差"
        
        return assessment
    
    def calculate_industry_score(self) -> Dict:
        """
        行业综合评分
        """
        scores = {}
        
        # 1. 市场空间 (20分)
        market_score = 0
        if self.industry.metrics.market_size >= 10000:  # 万亿市场
            market_score = 20
        elif self.industry.metrics.market_size >= 5000:
            market_score = 15
        elif self.industry.metrics.market_size >= 1000:
            market_score = 10
        else:
            market_score = 5
        
        # 增速加分
        if self.industry.metrics.market_growth_rate >= 30:
            market_score += 5
        elif self.industry.metrics.market_growth_rate >= 20:
            market_score += 3
        elif self.industry.metrics.market_growth_rate >= 10:
            market_score += 1
        
        scores["市场空间"] = min(market_score, 20)
        
        # 2. 竞争格局 (25分)
        # 五力模型评估
        attractiveness = self.industry.five_forces.calculate_attractiveness()
        competition_score = attractiveness * 2.5  # 转换为25分制
        scores["竞争格局"] = competition_score
        
        # 3. 盈利能力 (20分)
        profit_score = 0
        if self.industry.metrics.avg_gross_margin >= 40:
            profit_score += 10
        elif self.industry.metrics.avg_gross_margin >= 30:
            profit_score += 7
        elif self.industry.metrics.avg_gross_margin >= 20:
            profit_score += 4
        
        if self.industry.metrics.avg_roe >= 15:
            profit_score += 10
        elif self.industry.metrics.avg_roe >= 10:
            profit_score += 7
        elif self.industry.metrics.avg_roe >= 5:
            profit_score += 4
        
        scores["盈利能力"] = profit_score
        
        # 4. 成长确定性 (15分)
        growth_score = 0
        if self.industry.life_cycle == IndustryLifeCycle.GROWTH:
            growth_score = 12
        elif self.industry.life_cycle == IndustryLifeCycle.MATURITY:
            growth_score = 8
        elif self.industry.life_cycle == IndustryLifeCycle.INTRODUCTION:
            growth_score = 5
        else:
            growth_score = 2
        
        # 增速稳定性
        if self.industry.metrics.market_growth_rate >= 15:
            growth_score += 3
        
        scores["成长确定性"] = min(growth_score, 15)
        
        # 5. 政策环境 (10分)
        policy_score = 5 + self.industry.policy_support  # 基准5分
        scores["政策环境"] = max(0, min(policy_score, 10))
        
        # 6. 进入壁垒 (10分)
        barrier_score = self.industry.metrics.entry_barrier_score
        scores["进入壁垒"] = barrier_score
        
        # 总分
        scores["总分"] = sum([v for k, v in scores.items() if k != "总分"])
        
        # 评级
        total = scores["总分"]
        if total >= 80:
            scores["评级"] = "A"
            scores["评估"] = "优质赛道"
        elif total >= 65:
            scores["评级"] = "B"
            scores["评估"] = "良好赛道"
        elif total >= 50:
            scores["评级"] = "C"
            scores["评估"] = "一般赛道"
        else:
            scores["评级"] = "D"
            scores["评估"] = "需谨慎"
        
        return scores
    
    def generate_report(self) -> str:
        """生成行业分析报告"""
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"行业分析报告：{self.industry.name}")
        lines.append(f"{'='*60}")
        
        # 基本信息
        lines.append(f"\n【基本信息】")
        lines.append(f"  行业代码：{self.industry.code}")
        lines.append(f"  生命周期：{self.industry.life_cycle.value}")
        lines.append(f"  行业类型：{self.industry.industry_type.value}")
        
        # 生命周期分析
        life_cycle_info = self.analyze_life_cycle()
        lines.append(f"\n【生命周期特征】")
        for key, value in life_cycle_info.items():
            lines.append(f"  {key}：{value}")
        
        # 五力分析
        lines.append(f"\n【波特五力分析】")
        ff = self.industry.five_forces
        lines.append(f"  行业内竞争：     {ff.internal_competition}/10")
        lines.append(f"  新进入者威胁：   {ff.new_entrant_threat}/10")
        lines.append(f"  替代品威胁：     {ff.substitute_threat}/10")
        lines.append(f"  供应商议价力：   {ff.supplier_power}/10")
        lines.append(f"  买方议价力：     {ff.buyer_power}/10")
        lines.append(f"  行业吸引力：     {ff.calculate_attractiveness():.1f}/10")
        
        # 关键指标
        m = self.industry.metrics
        lines.append(f"\n【关键指标】")
        lines.append(f"  市场规模：       {m.market_size:,.0f}亿元")
        lines.append(f"  市场增速：       {m.market_growth_rate:.1f}%")
        lines.append(f"  平均毛利率：     {m.avg_gross_margin:.1f}%")
        lines.append(f"  平均ROE：        {m.avg_roe:.1f}%")
        lines.append(f"  CR4集中度：      {m.cr4:.1f}%")
        lines.append(f"  集中度水平：     {self.calculate_concentration_level()}")
        
        # 综合评分
        scores = self.calculate_industry_score()
        lines.append(f"\n【综合评分】")
        for key, value in scores.items():
            if isinstance(value, float):
                lines.append(f"  {key}：{value:.1f}分")
            else:
                lines.append(f"  {key}：{value}")
        
        lines.append(f"{'='*60}\n")
        
        return "\n".join(lines)


class IndustryRotator:
    """
    行业轮动模型
    """
    
    # 经济周期阶段
    ECONOMIC_CYCLES = ["复苏期", "扩张期", "滞胀期", "衰退期"]
    
    # 行业轮动矩阵
    ROTATION_MATRIX = {
        "复苏期": {
            "推荐": ["金融", "周期", "地产"],
            "回避": ["公用事业", "必需消费"],
            "逻辑": "经济开始复苏，利率低位，金融和周期股受益"
        },
        "扩张期": {
            "推荐": ["科技", "可选消费", "工业"],
            "回避": ["公用事业", "医药"],
            "逻辑": "经济过热，成长股表现最佳"
        },
        "滞胀期": {
            "推荐": ["能源", "公用事业", "必需消费"],
            "回避": ["科技", "金融"],
            "逻辑": "通胀高企，防守型行业占优"
        },
        "衰退期": {
            "推荐": ["医药", "必需消费", "公用事业"],
            "回避": ["周期", "科技", "金融"],
            "逻辑": "经济下行，防御性行业避险"
        }
    }
    
    def get_recommendation(self, cycle_phase: str) -> Dict:
        """获取当前周期推荐"""
        return self.ROTATION_MATRIX.get(cycle_phase, {})
    
    def analyze_industry_position(self, industry: Industry, cycle_phase: str) -> Dict:
        """
        分析行业在当前周期的位置
        """
        recommendation = self.get_recommendation(cycle_phase)
        
        position = {
            "行业": industry.name,
            "当前周期": cycle_phase,
            "行业类型": industry.industry_type.value
        }
        
        # 判断是否推荐
        if industry.name in recommendation.get("推荐", []):
            position["定位"] = "推荐配置"
            position["建议"] = "超配"
        elif industry.name in recommendation.get("回避", []):
            position["定位"] = "建议回避"
            position["建议"] = "低配"
        else:
            position["定位"] = "中性"
            position["建议"] = "标配"
        
        position["周期逻辑"] = recommendation.get("逻辑", "")
        
        return position


class IndustryScreener:
    """
    行业筛选器
    """
    
    @staticmethod
    def screen_by_score(industries: List[Industry], min_score: float = 65) -> List[Industry]:
        """按综合评分筛选优质行业"""
        result = []
        for industry in industries:
            analyzer = IndustryAnalyzer(industry)
            scores = analyzer.calculate_industry_score()
            if scores["总分"] >= min_score:
                result.append(industry)
        return result
    
    @staticmethod
    def screen_by_growth(industries: List[Industry], min_growth: float = 20) -> List[Industry]:
        """筛选高成长行业"""
        return [i for i in industries if i.metrics.market_growth_rate >= min_growth]
    
    @staticmethod
    def screen_by_profitability(industries: List[Industry], min_roe: float = 15) -> List[Industry]:
        """筛选高盈利行业"""
        return [i for i in industries if i.metrics.avg_roe >= min_roe]
    
    @staticmethod
    def find_best_industries(industries: List[Industry], top_n: int = 5) -> List[Tuple[Industry, float]]:
        """找出最优秀的行业"""
        scored = []
        for industry in industries:
            analyzer = IndustryAnalyzer(industry)
            scores = analyzer.calculate_industry_score()
            scored.append((industry, scores["总分"]))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]


# ==================== 演示代码 ====================

def demo_industry_analysis():
    """演示行业分析"""
    print("\n" + "="*60)
    print("   演示：白酒行业分析")
    print("="*60)
    
    baijiu = Industry(
        code="BK0477",
        name="白酒",
        life_cycle=IndustryLifeCycle.MATURITY,
        industry_type=IndustryType.DEFENSIVE,
        five_forces=PorterFiveForces(
            internal_competition=3,      # 竞争温和
            new_entrant_threat=2,        # 进入壁垒极高
            substitute_threat=2,         # 替代品威胁低
            supplier_power=2,            # 供应商弱势
            buyer_power=3                # 买方议价力弱
        ),
        metrics=IndustryMetrics(
            market_size=6000,
            market_growth_rate=7,
            avg_gross_margin=70,
            avg_roe=22,
            cr4=35,
            entry_barrier_score=9
        ),
        policy_support=0
    )
    
    analyzer = IndustryAnalyzer(baijiu)
    report = analyzer.generate_report()
    print(report)


def demo_new_energy_vehicle():
    """演示新能源汽车行业分析"""
    print("\n" + "="*60)
    print("   演示：新能源汽车行业分析")
    print("="*60)
    
    nev = Industry(
        code="BK0978",
        name="新能源汽车",
        life_cycle=IndustryLifeCycle.GROWTH,
        industry_type=IndustryType.GROWTH,
        five_forces=PorterFiveForces(
            internal_competition=9,      # 竞争极其激烈
            new_entrant_threat=6,        # 进入壁垒中等
            substitute_threat=2,         # 趋势不可逆
            supplier_power=7,            # 电池供应商强势
            buyer_power=7                # 买方选择多
        ),
        metrics=IndustryMetrics(
            market_size=15000,
            market_growth_rate=35,
            avg_gross_margin=18,
            avg_roe=12,
            cr4=55,
            entry_barrier_score=6
        ),
        policy_support=4
    )
    
    analyzer = IndustryAnalyzer(nev)
    scores = analyzer.calculate_industry_score()
    
    print(f"\n{nev.name} 综合评分：")
    for key, value in scores.items():
        if isinstance(value, float):
            print(f"  {key}：{value:.1f}")
        else:
            print(f"  {key}：{value}")


def demo_industry_rotation():
    """演示行业轮动"""
    print("\n" + "="*60)
    print("   演示：行业轮动模型")
    print("="*60)
    
    rotator = IndustryRotator()
    
    for phase in rotator.ECONOMIC_CYCLES:
        print(f"\n【{phase}】")
        rec = rotator.get_recommendation(phase)
        print(f"  推荐配置：{', '.join(rec['推荐'])}")
        print(f"  建议回避：{', '.join(rec['回避'])}")
        print(f"  投资逻辑：{rec['逻辑']}")


def demo_industry_screening():
    """演示行业筛选"""
    print("\n" + "="*60)
    print("   演示：行业筛选")
    print("="*60)
    
    industries = [
        Industry("A", "白酒", IndustryLifeCycle.MATURITY, IndustryType.DEFENSIVE,
                metrics=IndustryMetrics(market_size=6000, market_growth_rate=7, avg_roe=22, entry_barrier_score=9)),
        Industry("B", "新能源", IndustryLifeCycle.GROWTH, IndustryType.GROWTH,
                metrics=IndustryMetrics(market_size=15000, market_growth_rate=35, avg_roe=12, entry_barrier_score=6),
                policy_support=4),
        Industry("C", "银行", IndustryLifeCycle.MATURITY, IndustryType.CYCLICAL,
                metrics=IndustryMetrics(market_size=50000, market_growth_rate=5, avg_roe=10, entry_barrier_score=8)),
        Industry("D", "医药", IndustryLifeCycle.GROWTH, IndustryType.DEFENSIVE,
                metrics=IndustryMetrics(market_size=20000, market_growth_rate=12, avg_roe=15, entry_barrier_score=7)),
        Industry("E", "钢铁", IndustryLifeCycle.DECLINE, IndustryType.CYCLICAL,
                metrics=IndustryMetrics(market_size=8000, market_growth_rate=-2, avg_roe=5, entry_barrier_score=4)),
    ]
    
    # 设置五力模型
    for i in industries:
        i.five_forces = PorterFiveForces(
            internal_competition=5,
            new_entrant_threat=5,
            substitute_threat=5,
            supplier_power=5,
            buyer_power=5
        )
    
    print("\n行业列表：")
    for i in industries:
        print(f"  {i.name}：规模{i.metrics.market_size}亿，增速{i.metrics.market_growth_rate}%")
    
    # 高成长筛选
    high_growth = IndustryScreener.screen_by_growth(industries, min_growth=15)
    print(f"\n高成长行业（增速≥15%）：")
    for i in high_growth:
        print(f"  {i.name}")
    
    # 高盈利筛选
    high_profit = IndustryScreener.screen_by_profitability(industries, min_roe=15)
    print(f"\n高盈利行业（ROE≥15%）：")
    for i in high_profit:
        print(f"  {i.name}")
    
    # 最优行业
    print(f"\n行业综合排名：")
    best = IndustryScreener.find_best_industries(industries, top_n=3)
    for idx, (industry, score) in enumerate(best, 1):
        print(f"  {idx}. {industry.name} - {score:.1f}分")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("   行业分析框架 - 实战代码演示")
    print("="*60)
    
    demo_industry_analysis()
    demo_new_energy_vehicle()
    demo_industry_rotation()
    demo_industry_screening()
    
    print("\n" + "="*60)
    print("  所有演示完成!")
    print("="*60)
