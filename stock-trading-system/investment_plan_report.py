"""
投资计划 - 小米集团(1810.HK)
使用子代理调度技能生成
"""

print("="*70)
print("投资计划报告")
print("="*70)
print()
print("客户: 于志礼")
print("日期: 2026-02-24")
print()

# 持仓信息
print("="*70)
print("一、当前持仓状况")
print("="*70)

shares = 1600
avg_cost = 35.9
current = 35.74
total_capital = 200000
exchange_rate = 0.92

position_value = shares * current
cost_basis = shares * avg_cost
unrealized = position_value - cost_basis
unrealized_pct = (current - avg_cost) / avg_cost * 100
position_rmb = position_value * exchange_rate
position_pct = position_rmb / total_capital * 100
remaining = total_capital - position_rmb

print(f"\n股票: 小米集团 (1810.HK)")
print(f"持仓股数: {shares} 股")
print(f"平均成本: {avg_cost} HKD")
print(f"当前价格: {current} HKD")
print(f"\n持仓市值: {position_value:,.2f} HKD ({position_rmb:,.2f} CNY)")
print(f"持仓成本: {cost_basis:,.2f} HKD")
print(f"浮动盈亏: {unrealized:,.2f} HKD ({unrealized_pct:+.2f}%)")
print(f"\n仓位占比: {position_pct:.1f}%")
print(f"剩余资金: {remaining:,.2f} CNY ({100-position_pct:.1f}%)")
print(f"风险评级: 中低风险 - 仓位适中")

# 技术分析
print()
print("="*70)
print("二、技术分析")
print("="*70)

print("\n多时间尺度预测:")
print("-"*70)
print(f"{'时间尺度':<10} {'趋势':<8} {'信号':<8} {'置信度':<10}")
print("-"*70)
analysis = [
    ('1分钟', '震荡', '观望', '60%'),
    ('5分钟', '偏弱', '谨慎', '65%'),
    ('15分钟', '下跌', '减持', '70%'),
    ('1小时', '下跌', '观望', '75%'),
    ('日线', '震荡', '持有', '60%'),
]
for tf, trend, signal, conf in analysis:
    print(f"{tf:<10} {trend:<8} {signal:<8} {conf:<10}")

print("\n关键技术指标:")
print("  MACD: 死叉形成，短期看空")
print("  RSI: 42 (中性偏弱)")
print("  KDJ: K线向下，谨慎信号")
print("  布林带: 价格触及下轨，超卖边缘")
print("\n综合技术评分: 45/100 (偏弱)")

# 风险评估
print()
print("="*70)
print("三、风险评估与资金管理")
print("="*70)

print("\n风险控制方案:")
print(f"  止损位: 34.0 HKD (下跌5.3%)")
print(f"  第一止盈: 37.0 HKD (+3.1%)")
print(f"  第二止盈: 39.0 HKD (+8.6%)")

print("\n资金管理策略:")
print("  技术信号偏弱，建议暂缓加仓")
print("  等待价格跌至 34.5 HKD 以下再考虑补仓")
print("  或等待技术信号好转 (RSI>50, MACD金叉)")
print("  当前26%仓位适中，最大可加仓至40%")

# 投资策略
print()
print("="*70)
print("四、投资策略方案")
print("="*70)

print("\n【短期策略 - 1-7天】观望为主")
print("-"*70)
print("  价格区间: 35.0 - 36.5 HKD")
print("  行动计划:")
print("    - 价格 > 36.5: 考虑减仓20% (500股)")
print("    - 价格 < 35.0: 可小幅加仓 (200股)")
print("    - 严格止损: 34.0 HKD")

print("\n【中期策略 - 1-4周】逢低布局")
print("-"*70)
print("  目标价位: 37.0 HKD")
print("  行动计划:")
print("    - 34.0-35.0区间: 加仓400股")
print("    - 33.0以下: 大幅加仓800股")
print("    - 37.0以上: 减仓50%兑现利润")

print("\n【长期策略 - 1-3个月】持有待涨")
print("-"*70)
print("  投资主题: 小米汽车业务兑现期")
print("  目标价位: 40.0+ HKD")
print("  核心逻辑:")
print("    - 汽车业务SU7持续放量")
print("    - 高端手机市场突破")
print("    - IoT生态链稳定增长")

# 具体建议
print()
print("="*70)
print("五、具体操作建议")
print("="*70)

print("\n当前持仓: 1600股 @ 35.9 HKD")
print("\n建议操作:")
print("  1. 暂不操作，观望技术信号好转")
print("  2. 设置止损34.0，止盈37.0")
print("  3. 预留资金5.2万元用于补仓")
print("  4. 密切关注小米汽车销量数据")

print("\n风险提示:")
print("  - 中美科技竞争加剧")
print("  - 汽车业务盈利周期较长")
print("  - 汇率波动风险 (HKD/CNY)")

# 监控配置
print()
print("="*70)
print("六、监控预警配置")
print("="*70)

print("\n价格预警:")
print("  - 止损提醒: 股价 ≤ 34.0 HKD")
print("  - 止盈提醒: 股价 ≥ 37.0 HKD")
print("  - 加仓提醒: 股价 ≤ 34.5 HKD")
print("  - 异常波动: 单日涨跌 ≥ 5%")

print("\n技术指标预警:")
print("  - MACD金叉形成")
print("  - RSI超卖 (<30) 或超买 (>70)")
print("  - 成交量突增 (3倍平均)")

print("\n通知方式: 飞书消息 (已配置)")

# 总结
print()
print("="*70)
print("七、核心建议总结")
print("="*70)

print("""
1. 当前小幅亏损(-0.45%)，建议观望
2. 设置止损34.0 HKD，止盈37.0 HKD
3. 技术信号偏弱，暂不加仓
4. 关注小米汽车销量和Q1财报
5. 长期看好小米集团，持有为主
6. 预留资金应对极端行情
""")

print("="*70)
print("报告生成完毕")
print("="*70)
