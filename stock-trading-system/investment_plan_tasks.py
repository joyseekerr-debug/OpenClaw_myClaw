"""
投资计划任务分解 - 使用子代理调度技能
用户: 于志礼
持仓: 小米集团(1810.HK) 1600股, 平均成本35.9 HKD
资金: 20万人民币
当前价格: 35.74 HKD (来自iTick实时数据)
"""

# 任务分解结构
INVESTMENT_PLAN_TASKS = {
    "task_id": "investment_plan_20260224",
    "task_name": "小米集团股票投资计划制定",
    "user": "于志礼",
    "context": {
        "total_capital_rmb": 200000,  # 20万人民币
        "holding_shares": 1600,
        "avg_cost_hkd": 35.9,
        "current_price_hkd": 35.74,
        "stock_symbol": "1810.HK",
        "stock_name": "小米集团-W",
        "unrealized_pnl_pct": (35.74 - 35.9) / 35.9 * 100  # -0.45%
    },
    
    "sub_tasks": [
        {
            "task_id": "T1",
            "name": "持仓状况分析",
            "type": "Simple",  # 简单任务 - 直接计算
            "description": "分析当前持仓的盈亏状况、仓位占比、风险敞口",
            "inputs": {
                "total_capital": 200000,
                "holding_shares": 1600,
                "avg_cost": 35.9,
                "current_price": 35.74
            },
            "expected_outputs": [
                "当前持仓市值(人民币)",
                " unrealized P&L",
                "仓位占比",
                "风险等级评估"
            ]
        },
        
        {
            "task_id": "T2",
            "name": "技术分析 - 多时间尺度",
            "type": "Standard",  # 标准任务 - 使用预测系统
            "description": "使用股票预测系统进行技术分析，获取各时间尺度的预测信号",
            "inputs": {
                "symbol": "1810.HK",
                "timeframes": ["1min", "5min", "15min", "1h", "1d"],
                "indicators": ["MACD", "RSI", "KDJ", "布林带"]
            },
            "expected_outputs": [
                "各时间尺度趋势预测",
                "技术指标信号",
                "综合评分"
            ],
            "tools": ["股票预测系统", "技术分析模块"]
        },
        
        {
            "task_id": "T3",
            "name": "市场情报收集",
            "type": "Standard",  # 标准任务 - 网络搜索
            "description": "收集小米集团的最新新闻、市场情绪、行业动态",
            "inputs": {
                "company": "小米集团",
                "topics": ["汽车业务", "手机销量", "财报", "行业竞争"]
            },
            "expected_outputs": [
                "最新新闻摘要",
                "市场情绪分析",
                "风险因素识别"
            ],
            "tools": ["网络搜索", "NLP情感分析"]
        },
        
        {
            "task_id": "T4",
            "name": "风险评估与资金管理",
            "type": "Orchestrator",  # 编排任务 - 需要综合判断
            "description": "基于T1-T3的结果，制定风险控制和资金管理策略",
            "inputs": {
                "current_position": "T1_output",
                "tech_analysis": "T2_output",
                "market_intel": "T3_output",
                "risk_tolerance": "中等"
            },
            "expected_outputs": [
                "止损位设置",
                "加仓/减仓策略",
                "资金分配方案",
                "风险对冲建议"
            ]
        },
        
        {
            "task_id": "T5",
            "name": "投资策略制定",
            "type": "Orchestrator",  # 编排任务 - 最终决策
            "description": "整合所有分析结果，制定完整的投资行动计划",
            "inputs": {
                "position_analysis": "T1_output",
                "tech_signals": "T2_output",
                "market_sentiment": "T3_output",
                "risk_mgmt": "T4_output"
            },
            "expected_outputs": [
                "短期操作策略(1-7天)",
                "中期策略(1-4周)",
                "长期策略(1-3个月)",
                "具体操作建议",
                "风险警示"
            ]
        },
        
        {
            "task_id": "T6",
            "name": "监控预警设置",
            "type": "Batch",  # 批量任务 - 配置监控
            "description": "设置价格预警、技术指标监控",
            "inputs": {
                "symbol": "1810.HK",
                "current_price": 35.74,
                "avg_cost": 35.9
            },
            "expected_outputs": [
                "价格预警点设置",
                "技术指标预警",
                "通知方式配置"
            ],
            "tools": ["监控系统", "飞书通知"]
        }
    ],
    
    "dependencies": {
        "T1": [],  # 无依赖，可并行
        "T2": [],  # 无依赖，可并行
        "T3": [],  # 无依赖，可并行
        "T4": ["T1", "T2", "T3"],  # 依赖前三个
        "T5": ["T4"],  # 依赖风险评估
        "T6": ["T5"]   # 依赖最终策略
    },
    
    "workflow": {
        "phase1": ["T1", "T2", "T3"],  # 并行执行
        "phase2": ["T4"],               # 编排决策
        "phase3": ["T5"],               # 策略制定
        "phase4": ["T6"]                # 监控配置
    },
    
    "deliverables": {
        "immediate": "持仓分析报告 (T1)",
        "short_term": "7天操作计划 (T5)",
        "long_term": "完整投资策略书 (T5)",
        "system": "监控预警配置 (T6)"
    }
}

# 快速计算当前状况
current_position = {
    "持仓股数": 1600,
    "平均成本(HKD)": 35.9,
    "当前价格(HKD)": 35.74,
    "持仓市值(HKD)": 1600 * 35.74,
    "持仓成本(HKD)": 1600 * 35.9,
    " unrealized P&L(HKD)": 1600 * (35.74 - 35.9),
    " unrealized P&L(%)": round((35.74 - 35.9) / 35.9 * 100, 2),
    "汇率假设": "1 HKD = 0.92 RMB",
    "持仓市值(人民币)": round(1600 * 35.74 * 0.92, 2),
    "仓位占比": "约26%"  # 1600*35.74*0.92 / 200000
}

print("="*60)
print("投资计划任务分解")
print("="*60)
print()
print(f"任务ID: {INVESTMENT_PLAN_TASKS['task_id']}")
print(f"任务名称: {INVESTMENT_PLAN_TASKS['task_name']}")
print()
print("用户持仓状况:")
for key, value in current_position.items():
    print(f"  {key}: {value}")
print()
print("="*60)
print("子任务列表:")
print("="*60)
for task in INVESTMENT_PLAN_TASKS['sub_tasks']:
    print(f"\n[{task['task_id']}] {task['name']}")
    print(f"  类型: {task['type']}")
    print(f"  描述: {task['description']}")
    print(f"  依赖: {INVESTMENT_PLAN_TASKS['dependencies'][task['task_id']]}")
print()
print("="*60)
print("执行流程:")
print("="*60)
for phase, tasks in INVESTMENT_PLAN_TASKS['workflow'].items():
    print(f"  {phase}: {tasks}")
print()
print("="*60)
print("交付物:")
print("="*60)
for key, value in INVESTMENT_PLAN_TASKS['deliverables'].items():
    print(f"  [{key}] {value}")
print("="*60)
