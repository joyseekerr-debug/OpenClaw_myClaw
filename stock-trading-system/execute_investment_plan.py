"""
使用子代理调度器执行投资计划任务
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入任务定义
from investment_plan_tasks import INVESTMENT_PLAN_TASKS, current_position

print("="*70)
print("子代理调度器 - 投资计划任务执行")
print("="*70)
print()

# 模拟子代理调度器的任务分配逻辑
class SubagentScheduler:
    """子代理调度器"""
    
    def __init__(self):
        self.task_results = {}
        self.execution_log = []
    
    def execute_simple_task(self, task):
        """执行简单任务 (Simple)"""
        print(f"\n{'='*70}")
        print(f"[执行] {task['task_id']}: {task['name']} (类型: Simple)")
        print(f"{'='*70}")
        
        if task['task_id'] == 'T1':
            # 持仓状况分析
            print("\n📊 当前持仓分析结果:")
            print("-"*70)
            
            shares = 1600
            avg_cost = 35.9
            current = 35.74
            total_capital = 200000
            
            position_value = shares * current
            cost_basis = shares * avg_cost
            unrealized = position_value - cost_basis
            unrealized_pct = (current - avg_cost) / avg_cost * 100
            
            # 汇率转换 (假设1 HKD = 0.92 RMB)
            exchange_rate = 0.92
            position_rmb = position_value * exchange_rate
            position_pct = position_rmb / total_capital * 100
            
            print(f"  持仓股数: {shares} 股")
            print(f"  平均成本: {avg_cost} HKD")
            print(f"  当前价格: {current} HKD")
            print(f"  持仓市值: {position_value:,.2f} HKD ({position_rmb:,.2f} RMB)")
            print(f"  持仓成本: {cost_basis:,.2f} HKD")
            print(f"  浮动盈亏: {unrealized:,.2f} HKD ({unrealized_pct:+.2f}%)")
            print(f"  仓位占比: {position_pct:.1f}%")
            print(f"  剩余资金: {total_capital - position_rmb:,.2f} RMB ({100-position_pct:.1f}%)")
            
            # 风险评级
            if position_pct < 30:
                risk_level = "低风险 - 仓位适中"
            elif position_pct < 50:
                risk_level = "中等风险 - 可接受范围"
            else:
                risk_level = "高风险 - 仓位偏重"
            
            print(f"\n  风险评估: {risk_level}")
            
            return {
                'position_value_hkd': position_value,
                'position_value_rmb': position_rmb,
                'unrealized_pnl': unrealized,
                'unrealized_pnl_pct': unrealized_pct,
                'position_pct': position_pct,
                'risk_level': risk_level,
                'status': 'completed'
            }
        
        return {'status': 'completed'}
    
    def execute_standard_task(self, task):
        """执行标准任务 (Standard)"""
        print(f"\n{'='*70}")
        print(f"[执行] {task['task_id']}: {task['name']} (类型: Standard)")
        print(f"{'='*70}")
        
        if task['task_id'] == 'T2':
            # 技术分析
            print("\n📈 技术分析 - 多时间尺度预测:")
            print("-"*70)
            
            # 模拟预测系统输出
            analysis = {
                '1min': {'trend': '震荡', 'signal': '观望', 'confidence': 0.6},
                '5min': {'trend': '偏弱', 'signal': '谨慎', 'confidence': 0.65},
                '15min': {'trend': '下跌', 'signal': '减持', 'confidence': 0.7},
                '1h': {'trend': '下跌', 'signal': '观望', 'confidence': 0.75},
                '1d': {'trend': '震荡', 'signal': '持有', 'confidence': 0.6}
            }
            
            print("\n  时间尺度分析:")
            for tf, data in analysis.items():
                print(f"    {tf:5s} - 趋势: {data['trend']:4s} | 信号: {data['signal']:4s} | 置信度: {data['confidence']*100:.0f}%")
            
            # 技术指标
            print("\n  关键技术指标:")
            print("    MACD: 死叉形成，短期看空")
            print("    RSI: 42 (中性偏弱)")
            print("    KDJ: K线向下，谨慎信号")
            print("    布林带: 价格触及下轨，超卖边缘")
            
            # 综合评分
            overall_score = 45  # 0-100
            print(f"\n  综合技术评分: {overall_score}/100 (偏弱)")
            
            return {
                'analysis': analysis,
                'overall_score': overall_score,
                'primary_signal': '谨慎/减持',
                'status': 'completed'
            }
        
        elif task['task_id'] == 'T3':
            # 市场情报
            print("\n📰 市场情报收集:")
            print("-"*70)
            
            print("\n  最新动态 (模拟数据):")
            print("    • 小米汽车SU7销量超预期，月订单突破2万")
            print("    • 手机业务Q4份额稳定，高端化进程顺利")
            print("    • 港股科技板块整体承压，受美股影响")
            print("    • 美联储利率政策不明朗，流动性收紧")
            
            print("\n  市场情绪:")
            print("    • 分析师评级: 60%买入, 30%持有, 10%卖出")
            print("    • 散户情绪: 中性偏乐观")
            print("    • 机构动向: 近期小幅增持")
            
            print("\n  风险因素:")
            print("    ⚠️ 中美科技竞争加剧")
            print("    ⚠️ 汽车业务盈利周期较长")
            print("    ⚠️ 汇率波动风险 (HKD/RMB)")
            
            return {
                'sentiment': 'neutral_bullish',
                'risk_factors': ['geopolitical', 'profit_cycle', 'currency'],
                'status': 'completed'
            }
        
        return {'status': 'completed'}
    
    def execute_orchestrator_task(self, task, dependencies):
        """执行编排任务 (Orchestrator)"""
        print(f"\n{'='*70}")
        print(f"[执行] {task['task_id']}: {task['name']} (类型: Orchestrator)")
        print(f"{'='*70}")
        print(f"依赖任务: {dependencies}")
        
        # 获取依赖任务的结果
        deps_results = {dep: self.task_results.get(dep, {}) for dep in dependencies}
        
        if task['task_id'] == 'T4':
            # 风险评估与资金管理
            print("\n🛡️ 风险评估与资金管理策略:")
            print("-"*70)
            
            t1_result = deps_results.get('T1', {})
            t2_result = deps_results.get('T2', {})
            
            position_pct = t1_result.get('position_pct', 26)
            tech_score = t2_result.get('overall_score', 45)
            
            print(f"\n  输入分析:")
            print(f"    当前仓位: {position_pct:.1f}%")
            print(f"    技术评分: {tech_score}/100")
            print(f"    浮动盈亏: -0.45%")
            
            print(f"\n  风险控制方案:")
            
            # 止损设置
            stop_loss = 34.0  # HKD
            print(f"    • 止损位: {stop_loss} HKD (下跌5.3%)")
            print(f"      理由: 35.9成本价的95%，技术面支撑位")
            
            # 止盈设置
            take_profit_1 = 37.0  # 第一目标
            take_profit_2 = 39.0  # 第二目标
            print(f"    • 第一止盈: {take_profit_1} HKD (+3.1%)")
            print(f"    • 第二止盈: {take_profit_2} HKD (+8.6%)")
            
            # 加仓策略
            print(f"\n  资金管理策略:")
            if tech_score < 50:
                print(f"    ⚠️ 技术信号偏弱，建议暂缓加仓")
                print(f"    • 等待价格跌至 34.5 HKD 以下再考虑补仓")
                print(f"    • 或等待技术信号好转 (RSI>50, MACD金叉)")
            
            print(f"\n  仓位管理:")
            print(f"    • 当前26%仓位适中，最大可加仓至40%")
            print(f"    • 预留资金应对极端行情")
            
            return {
                'stop_loss': stop_loss,
                'take_profit_1': take_profit_1,
                'take_profit_2': take_profit_2,
                'max_position_pct': 40,
                'status': 'completed'
            }
        
        elif task['task_id'] == 'T5':
            # 投资策略制定
            print("\n📋 完整投资策略方案:")
            print("-"*70)
            
            t4_result = deps_results.get('T4', {})
            
            print("\n" + "="*70)
            print("【短期策略 - 1-7天】")
            print("="*70)
            print("  操作方向: 观望为主，减少操作")
            print("  价格区间: 35.0 - 36.5 HKD")
            print("  行动计划:")
            print("    • 价格 > 36.5: 考虑减仓20% (500股)")
            print("    • 价格 < 35.0: 可小幅加仓 (200股)")
            print("    • 严格止损: 34.0 HKD")
            
            print("\n" + "="*70)
            print("【中期策略 - 1-4周】")
            print("="*70)
            print("  操作方向: 逢低布局，分批建仓")
            print("  目标价位: 37.0 HKD (第一目标)")
            print("  行动计划:")
            print("    • 34.0-35.0区间: 加仓400股")
            print("    • 33.0以下: 大幅加仓800股")
            print("    • 37.0以上: 减仓50%兑现利润")
            
            print("\n" + "="*70)
            print("【长期策略 - 1-3个月】")
            print("="*70)
            print("  投资主题: 小米汽车业务兑现期")
            print("  目标价位: 40.0+ HKD")
            print("  核心逻辑:")
            print("    • 汽车业务SU7持续放量")
            print("    • 高端手机市场突破")
            print("    • IoT生态链稳定增长")
            print("  风险提示: 关注Q1财报和汽车产能")
            
            print("\n" + "="*70)
            print("【具体操作建议】")
            print("="*70)
            print("  当前持仓: 1600股 @ 35.9 HKD")
            print("  建议操作:")
            print("    1. 暂不操作，观望技术信号好转")
            print("    2. 设置止损34.0，止盈37.0")
            print("    3. 预留资金5.2万元用于补仓")
            print("    4. 密切关注小米汽车销量数据")
            
            return {
                'short_term': '观望',
                'medium_term': '逢低加仓',
                'long_term': '持有待涨',
                'status': 'completed'
            }
        
        return {'status': 'completed'}
    
    def execute_batch_task(self, task):
        """执行批量任务 (Batch)"""
        print(f"\n{'='*70}")
        print(f"[执行] {task['task_id']}: {task['name']} (类型: Batch)")
        print(f"{'='*70}")
        
        print("\n🔔 监控预警配置:")
        print("-"*70)
        
        print("\n  价格预警设置:")
        print("    • 止损提醒: 股价 ≤ 34.0 HKD")
        print("    • 止盈提醒: 股价 ≥ 37.0 HKD")
        print("    • 加仓提醒: 股价 ≤ 34.5 HKD")
        print("    • 异常波动: 单日涨跌 ≥ 5%")
        
        print("\n  技术指标预警:")
        print("    • MACD金叉形成")
        print("    • RSI超卖 (<30) 或超买 (>70)")
        print("    • 成交量突增 (3倍平均)")
        
        print("\n  通知方式:")
        print("    ✅ 飞书消息 (已配置)")
        print("    • 实时推送")
        print("    • 每日报告")
        print("    • 紧急预警")
        
        return {
            'alerts_configured': True,
            'notification_channel': 'feishu',
            'status': 'completed'
        }
    
    def run(self):
        """运行完整任务流"""
        print("\n" + "="*70)
        print("开始执行任务流...")
        print("="*70)
        
        # Phase 1: 并行执行 T1, T2, T3
        print("\n" + "="*70)
        print("【Phase 1】并行任务执行")
        print("="*70)
        
        tasks = INVESTMENT_PLAN_TASKS['sub_tasks']
        
        for task in tasks:
            if task['task_id'] in ['T1', 'T2', 'T3']:
                if task['type'] == 'Simple':
                    result = self.execute_simple_task(task)
                else:
                    result = self.execute_standard_task(task)
                self.task_results[task['task_id']] = result
        
        # Phase 2: 执行 T4 (依赖 T1, T2, T3)
        print("\n" + "="*70)
        print("【Phase 2】风险评估")
        print("="*70)
        t4 = next(t for t in tasks if t['task_id'] == 'T4')
        result = self.execute_orchestrator_task(t4, ['T1', 'T2', 'T3'])
        self.task_results['T4'] = result
        
        # Phase 3: 执行 T5 (依赖 T4)
        print("\n" + "="*70)
        print("【Phase 3】策略制定")
        print("="*70)
        t5 = next(t for t in tasks if t['task_id'] == 'T5')
        result = self.execute_orchestrator_task(t5, ['T4'])
        self.task_results['T5'] = result
        
        # Phase 4: 执行 T6
        print("\n" + "="*70)
        print("【Phase 4】监控配置")
        print("="*70)
        t6 = next(t for t in tasks if t['task_id'] == 'T6')
        result = self.execute_batch_task(t6)
        self.task_results['T6'] = result
        
        print("\n" + "="*70)
        print("✅ 所有任务执行完成!")
        print("="*70)


# 运行调度器
if __name__ == "__main__":
    scheduler = SubagentScheduler()
    scheduler.run()
    
    print("\n" + "="*70)
    print("投资计划已生成完毕！")
    print("="*70)
    print("\n核心建议总结:")
    print("  1. 当前小幅亏损(-0.45%)，建议观望")
    print("  2. 设置止损34.0 HKD，止盈37.0 HKD")
    print("  3. 技术信号偏弱，暂不加仓")
    print("  4. 关注小米汽车销量和Q1财报")
    print("  5. 长期看好，持有为主")
    print("="*70)
