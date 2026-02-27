# 股价预测系统 - 架构设计文档

**版本**: 1.0.0  
**日期**: 2026-02-26  
**作者**: Multi-Agent Development Team

---

## 1. 系统概述

### 1.1 设计目标

构建一套专业的股价预测系统，基于价格行为学和多时间框架分析，实现：
- **多时间框架预测**: 1分钟到周线级别的涨跌预测
- **概率输出**: 明确的上涨/下跌概率（如：上涨概率 65%）
- **多模型集成**: LSTM/XGBoost/Transformer/价格行为模型
- **历史回测**: 验证预测准确率并持续优化

### 1.2 核心特性

| 特性 | 描述 |
|------|------|
| 多时间框架 | 支持 1m/5m/15m/1h/4h/1d/1w 六个时间级别 |
| 多模型融合 | 4种预测模型加权集成 |
| 概率校准 | 输出经过校准的涨跌概率 |
| 实时预测 | 支持实时数据流预测 |
| 回测验证 | 完整的回测框架与绩效评估 |
| 参数优化 | 自动超参数调优 |

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      股价预测系统 v1.0.0                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   数据采集层  │───▶│   特征工程层  │───▶│   模型预测层  │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  多时间框架  │    │  价格行为   │    │  多模型集成  │       │
│  │  数据获取   │    │  特征提取   │    │  概率融合   │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                   │              │
│  ┌──────────────┐    ┌──────────────┐            │              │
│  │   回测验证层  │◀───│   预测输出   │◀───────────┘              │
│  └──────────────┘    └──────────────┘                           │
│         │                                                   │    │
│         ▼                                                   │    │
│  ┌──────────────┐    ┌──────────────┐                       │    │
│  │  参数优化   │───▶│  模型更新   │─────────────────────────┘    │
│  └──────────────┘    └──────────────┘                            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 模块划分

```
src/
├── data/                    # 数据采集层
│   ├── data_loader.py      # 多源数据加载
│   ├── data_processor.py   # 数据清洗与预处理
│   └── data_store.py       # 数据存储管理
│
├── features/                # 特征工程层
│   ├── technical_features.py    # 技术指标特征
│   ├── price_action_features.py # 价格行为特征
│   ├── alpha_features.py        # Alpha因子
│   └── feature_engineering.py   # 特征工程主类
│
├── models/                  # 模型预测层
│   ├── lstm_model.py       # LSTM高频预测
│   ├── xgboost_model.py    # XGBoost中频预测
│   ├── transformer_model.py # Transformer低频预测
│   └── price_action_model.py # 价格行为预测
│
├── ensemble/                # 模型集成层
│   ├── model_ensemble.py   # 多模型集成
│   ├── probability_calibration.py # 概率校准
│   └── confidence_scoring.py # 置信度评分
│
├── backtest/                # 回测验证层
│   ├── backtest_engine.py  # 回测引擎
│   ├── performance_metrics.py # 绩效指标
│   └── visualization.py    # 可视化
│
├── optimization/            # 参数优化层
│   ├── hyperparameter_tuning.py # 超参数调优
│   ├── feature_selection.py     # 特征选择
│   └── threshold_optimization.py # 阈值优化
│
├── deployment/              # 部署服务层
│   ├── prediction_service.py # 预测服务
│   └── api_server.py       # API接口
│
└── monitoring/              # 监控层
    ├── model_monitoring.py # 模型监控
    └── alerting.py         # 告警系统
```

---

## 3. 数据流设计

### 3.1 数据流向图

```
外部数据源
    │
    ├──▶ iTick API ──────┐
    ├──▶ Yahoo Finance ──┼──▶ Data Loader ──▶ Data Processor ──▶ Feature Engineering
    └──▶ AKShare ────────┘
                                                    │
                    ┌───────────────────────────────┼───────────────────────────────┐
                    │                               │                               │
                    ▼                               ▼                               ▼
            ┌──────────────┐              ┌──────────────┐              ┌──────────────┐
            │ 技术指标特征  │              │ 价格行为特征  │              │ Alpha因子    │
            └──────────────┘              └──────────────┘              └──────────────┘
                    │                               │                               │
                    └───────────────────────────────┼───────────────────────────────┘
                                                    │
                                                    ▼
                                          ┌─────────────────┐
                                          │   特征融合矩阵   │
                                          └─────────────────┘
                                                    │
                    ┌───────────────────────────────┼───────────────────────────────┐
                    │                               │                               │
                    ▼                               ▼                               ▼
            ┌──────────────┐              ┌──────────────┐              ┌──────────────┐
            │ LSTM模型     │              │ XGBoost模型  │              │ Transformer  │
            │ (1m/5m)      │              │ (15m/1h)     │              │ (1d/1w)      │
            └──────────────┘              └──────────────┘              └──────────────┘
                    │                               │                               │
                    │         ┌──────────────┐      │                               │
                    │         │ 价格行为模型  │◀─────┘                               │
                    │         │ (全时间框架)  │                                      │
                    │         └──────────────┘                                      │
                    │                   │                                           │
                    └───────────────────┼───────────────────────────────────────────┘
                                        │
                                        ▼
                              ┌─────────────────────┐
                              │   多模型概率融合     │
                              │   (加权投票)        │
                              └─────────────────────┘
                                        │
                                        ▼
                              ┌─────────────────────┐
                              │   概率校准输出       │
                              │   (上涨/下跌概率)   │
                              └─────────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    │                                       │
                    ▼                                       ▼
          ┌─────────────────┐                     ┌─────────────────┐
          │   回测验证      │                     │   实时预测      │
          │   (历史数据)    │                     │   (实时数据)    │
          └─────────────────┘                     └─────────────────┘
                    │                                       │
                    ▼                                       ▼
          ┌─────────────────┐                     ┌─────────────────┐
          │   绩效评估      │                     │   预测结果      │
          │   (准确率等)    │                     │   (概率+置信度) │
          └─────────────────┘                     └─────────────────┘
                    │
                    ▼
          ┌─────────────────┐
          │   参数优化      │
          │   (自动调参)    │
          └─────────────────┘
                    │
                    └────────────────▶ 模型更新 ◀────────────────┘
```

### 3.2 数据存储结构

```
data/
├── raw/                    # 原始数据
│   ├── 1m/                 # 1分钟K线
│   ├── 5m/                 # 5分钟K线
│   ├── 15m/                # 15分钟K线
│   ├── 1h/                 # 1小时K线
│   ├── 1d/                 # 日线
│   └── 1w/                 # 周线
│
├── processed/              # 处理后数据
│   ├── features/           # 特征数据
│   └── labels/             # 标签数据
│
└── cache/                  # 缓存数据
    ├── technical/          # 技术指标缓存
    ├── price_action/       # 价格行为缓存
    └── predictions/        # 预测结果缓存
```

---

## 4. 模型架构

### 4.1 多时间框架模型选择

| 时间框架 | 主要模型 | 辅助模型 | 特点 |
|----------|----------|----------|------|
| 1分钟 | LSTM | PriceAction | 高频，捕捉短期模式 |
| 5分钟 | LSTM | PriceAction | 短期趋势 |
| 15分钟 | XGBoost | PriceAction | 中频，特征丰富 |
| 1小时 | XGBoost | PriceAction | 日内交易 |
| 4小时 | Transformer | PriceAction | 波段交易 |
| 日线 | Transformer | PriceAction | 趋势跟踪 |
| 周线 | Transformer | PriceAction | 长期投资 |

### 4.2 LSTM模型架构

```python
# 1分钟/5分钟高频预测
LSTM_Model = {
    "input": {
        "sequence_length": 120,  # 2小时历史数据
        "features": [
            "open", "high", "low", "close", "volume",
            "sma_5", "sma_10", "ema_12", "rsi_14",
            "macd", "macd_signal", "bb_upper", "bb_lower"
        ]
    },
    "architecture": [
        {"layer": "LSTM", "units": 128, "return_sequences": True, "dropout": 0.2},
        {"layer": "LSTM", "units": 64, "return_sequences": True, "dropout": 0.2},
        {"layer": "LSTM", "units": 32, "return_sequences": False, "dropout": 0.2},
        {"layer": "Dense", "units": 16, "activation": "relu"},
        {"layer": "Dense", "units": 2, "activation": "softmax"}  # 上涨/下跌概率
    ],
    "output": {
        "up_probability": "float [0,1]",
        "down_probability": "float [0,1]"
    }
}
```

### 4.3 XGBoost模型架构

```python
# 15分钟/1小时中频预测
XGBoost_Model = {
    "input": {
        "features": [
            # 价格特征
            "returns", "log_returns", "volatility", "price_position",
            # 技术指标
            "rsi_6", "rsi_12", "rsi_24", "kdj_k", "kdj_d", "kdj_j",
            "macd", "macd_hist", "bb_width", "bb_position",
            # 价格行为特征
            "support_distance", "resistance_distance", "trend_slope",
            "pattern_strength", "candlestick_score",
            # Alpha因子
            "momentum_10", "momentum_20", "volatility_regime"
        ]
    },
    "parameters": {
        "max_depth": 6,
        "learning_rate": 0.1,
        "n_estimators": 200,
        "objective": "binary:logistic",
        "eval_metric": ["auc", "logloss"]
    },
    "output": {
        "up_probability": "float [0,1]",
        "feature_importance": "dict"
    }
}
```

### 4.4 Transformer模型架构

```python
# 日线/周线低频预测
Transformer_Model = {
    "input": {
        "sequence_length": 60,  # 60个交易日
        "features": [
            "open", "high", "low", "close", "volume",
            "weekly_returns", "monthly_returns"
        ]
    },
    "architecture": {
        "d_model": 128,
        "n_heads": 8,
        "n_layers": 4,
        "d_ff": 512,
        "dropout": 0.1,
        "positional_encoding": "sinusoidal"
    },
    "output": {
        "up_probability": "float [0,1]",
        "trend_strength": "float [0,1]",
        "attention_weights": "matrix"
    }
}
```

### 4.5 价格行为模型

```python
PriceAction_Model = {
    "components": {
        "support_resistance": {
            "method": "pivot_points",
            "lookback": 100,
            "tolerance": 0.02,
            "output": ["support_levels", "resistance_levels", "strength_scores"]
        },
        "trend_lines": {
            "method": "linear_regression",
            "min_points": 3,
            "max_deviation": 0.01,
            "output": ["trend_direction", "trend_slope", "trend_strength"]
        },
        "chart_patterns": {
            "patterns": [
                "head_and_shoulders", "inverse_head_and_shoulders",
                "double_top", "double_bottom",
                "ascending_triangle", "descending_triangle", "symmetrical_triangle",
                "bull_flag", "bear_flag",
                "cup_and_handle"
            ],
            "output": ["pattern_name", "pattern_confidence", "target_price"]
        },
        "candlestick_patterns": {
            "patterns": [
                "hammer", "shooting_star", "engulfing_bullish", "engulfing_bearish",
                "morning_star", "evening_star", "three_white_soldiers", "three_black_crows"
            ],
            "output": ["pattern_name", "reliability_score"]
        }
    },
    "fusion": {
        "method": "weighted_sum",
        "weights": {
            "support_resistance": 0.3,
            "trend_lines": 0.25,
            "chart_patterns": 0.25,
            "candlestick_patterns": 0.2
        }
    },
    "output": {
        "up_probability": "float [0,1]",
        "signal_strength": "float [0,1]",
        "key_levels": "list"
    }
}
```

---

## 5. 模型集成策略

### 5.1 集成架构

```
┌─────────────────────────────────────────────────────────────────┐
│                       模型集成层                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐                                              │
│   │ 时间框架选择  │                                              │
│   │ (1m/5m/15m/  │                                              │
│   │  1h/4h/1d/1w)│                                              │
│   └──────┬───────┘                                              │
│          │                                                       │
│          ▼                                                       │
│   ┌────────────────────────────────────────────────────────┐    │
│   │                   模型输出收集                          │    │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │    │
│   │  │ LSTM     │  │ XGBoost  │  │Transformr│  │PA Model│ │    │
│   │  │ 0.65 up  │  │ 0.58 up  │  │ 0.72 up  │  │0.60 up │ │    │
│   │  └──────────┘  └──────────┘  └──────────┘  └────────┘ │    │
│   └────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│   ┌────────────────────────────────────────────────────────┐    │
│   │                   加权投票融合                          │    │
│   │                                                        │    │
│   │   权重: LSTM(0.25) + XGBoost(0.25) +                  │    │
│   │         Transformer(0.25) + PA(0.25)                  │    │
│   │                                                        │    │
│   │   融合结果: 0.25×0.65 + 0.25×0.58 +                   │    │
│   │             0.25×0.72 + 0.25×0.60 = 0.6375            │    │
│   │                                                        │    │
│   │   原始概率: up=0.6375, down=0.3625                    │    │
│   └────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│   ┌────────────────────────────────────────────────────────┐    │
│   │                   概率校准                              │    │
│   │                                                        │    │
│   │   方法: Platt Scaling / Isotonic Regression           │    │
│   │                                                        │    │
│   │   校准后: up=0.62, down=0.38                          │    │
│   │                                                        │    │
│   │   置信区间: [0.55, 0.69] (95% CI)                     │    │
│   └────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│   ┌────────────────────────────────────────────────────────┐    │
│   │                   最终输出                              │    │
│   │                                                        │    │
│   │   预测: 上涨                                           │    │
│   │   概率: 62%                                            │    │
│   │   置信度: 中 (置信区间宽度 0.14)                       │    │
│   │   建议: 轻仓试多                                       │    │
│   │                                                        │    │
│   └────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 动态权重调整

```python
class DynamicWeightAdjustment:
    """
    根据历史准确率动态调整模型权重
    """
    
    def __init__(self, window=30):
        self.window = window  # 30天滑动窗口
        self.weights = {
            'LSTM': 0.25,
            'XGBoost': 0.25,
            'Transformer': 0.25,
            'PriceAction': 0.25
        }
    
    def update_weights(self, model_performances):
        """
        根据最近30天表现更新权重
        
        performances: {
            'LSTM': {'accuracy': 0.65, 'sharpe': 1.2},
            'XGBoost': {'accuracy': 0.62, 'sharpe': 1.1},
            ...
        }
        """
        # 基于准确率计算新权重
        total_accuracy = sum(p['accuracy'] for p in model_performances.values())
        
        for model, perf in model_performances.items():
            self.weights[model] = perf['accuracy'] / total_accuracy
        
        return self.weights
```

---

## 6. 回测框架设计

### 6.1 回测流程

```
┌─────────────────────────────────────────────────────────────────┐
│                       回测引擎                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   输入: 历史数据 (过去N年)                                       │
│                                                                  │
│   ┌────────────────────────────────────────────────────────┐    │
│   │  步骤1: 数据回放                                        │    │
│   │  - 按时间顺序遍历历史数据                               │    │
│   │  - 模拟实时预测场景                                     │    │
│   └────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│   ┌────────────────────────────────────────────────────────┐    │
│   │  步骤2: 生成预测信号                                    │    │
│   │  - 在每个时间点运行预测模型                             │    │
│   │  - 记录预测概率和方向                                   │    │
│   └────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│   ┌────────────────────────────────────────────────────────┐    │
│   │  步骤3: 交易决策                                        │    │
│   │  - 根据预测概率决定仓位                                 │    │
│   │  - 概率>0.6: 满仓, 0.55-0.6: 半仓, <0.55: 空仓        │    │
│   └────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│   ┌────────────────────────────────────────────────────────┐    │
│   │  步骤4: 模拟交易执行                                    │    │
│   │  - 考虑滑点和手续费                                     │    │
│   │  - 执行止损止盈逻辑                                     │    │
│   └────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│   ┌────────────────────────────────────────────────────────┐    │
│   │  步骤5: 绩效评估                                        │    │
│   │  - 计算各项指标                                         │    │
│   │  - 生成回测报告                                         │    │
│   └────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 绩效指标

| 指标 | 说明 | 目标值 |
|------|------|--------|
| **Accuracy** | 预测准确率 | >55% (随机50%) |
| **Precision** | 精确率 | >60% |
| **Recall** | 召回率 | >50% |
| **F1-Score** | F1分数 | >55% |
| **Win Rate** | 胜率 | >50% |
| **Profit Factor** | 盈亏比 | >1.2 |
| **Sharpe Ratio** | 夏普比率 | >1.0 |
| **Max Drawdown** | 最大回撤 | <20% |
| **Calmar Ratio** | Calmar比率 | >2.0 |

---

## 7. 参数优化设计

### 7.1 优化目标

```python
optimization_objectives = {
    # 目标1: 最大化预测准确率
    "maximize_accuracy": {
        "target": "accuracy",
        "weight": 0.3
    },
    # 目标2: 最大化夏普比率
    "maximize_sharpe": {
        "target": "sharpe_ratio",
        "weight": 0.4
    },
    # 目标3: 最小化最大回撤
    "minimize_drawdown": {
        "target": "max_drawdown",
        "weight": 0.3
    }
}
```

### 7.2 优化方法

| 方法 | 适用场景 | 复杂度 |
|------|----------|--------|
| **Grid Search** | 参数空间小 | 低 |
| **Random Search** | 参数空间大 | 中 |
| **Bayesian Optimization** | 计算资源有限 | 高 |
| **Genetic Algorithm** | 多目标优化 | 高 |

---

## 8. 部署架构

### 8.1 实时预测服务

```
┌─────────────────────────────────────────────────────────────────┐
│                    实时预测服务架构                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│   │  数据接入    │───▶│  预测引擎    │───▶│  结果输出    │     │
│   │  (WebSocket) │    │  (多模型)    │    │  (API/通知)  │     │
│   └──────────────┘    └──────────────┘    └──────────────┘     │
│                              │                                   │
│                              ▼                                   │
│                    ┌─────────────────┐                          │
│                    │   模型缓存      │                          │
│                    │   (Redis)       │                          │
│                    └─────────────────┘                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 API设计

```python
# 预测API
POST /api/v1/predict
{
    "symbol": "1810.HK",
    "timeframe": "1d",
    "features": [...]  # 可选自定义特征
}

Response:
{
    "symbol": "1810.HK",
    "timeframe": "1d",
    "prediction": {
        "direction": "up",
        "up_probability": 0.62,
        "down_probability": 0.38,
        "confidence": "medium",
        "confidence_interval": [0.55, 0.69]
    },
    "model_contributions": {
        "LSTM": 0.25,
        "XGBoost": 0.25,
        "Transformer": 0.30,
        "PriceAction": 0.20
    },
    "timestamp": "2026-02-26T16:00:00Z"
}
```

---

## 9. 监控与告警

### 9.1 监控指标

| 指标类型 | 具体指标 | 告警阈值 |
|----------|----------|----------|
| **模型性能** | 预测准确率下降 | <50% (连续7天) |
| **模型性能** | 夏普比率下降 | <0.5 (连续7天) |
| **系统健康** | API响应时间 | >2s (平均) |
| **系统健康** | 预测失败率 | >5% |
| **数据质量** | 数据延迟 | >5分钟 |

### 9.2 自动重训练触发

```python
retraining_triggers = {
    "accuracy_drop": {
        "condition": "accuracy < 0.50 for 7 consecutive days",
        "action": "trigger_retraining"
    },
    "sharpe_drop": {
        "condition": "sharpe_ratio < 0.5 for 7 consecutive days",
        "action": "trigger_retraining"
    },
    "data_drift": {
        "condition": "feature_distribution_change > 0.2",
        "action": "trigger_retraining"
    }
}
```

---

## 10. 项目计划

### 10.1 开发阶段

| 阶段 | 内容 | 工期 | 依赖 |
|------|------|------|------|
| **阶段一** | 架构设计+数据准备 | Day 1 | - |
| **阶段二** | 价格行为学模块 | Day 1-2 | 阶段一 |
| **阶段三** | 预测模型开发 | Day 2-3 | 阶段一 |
| **阶段四** | 模型集成 | Day 3 | 阶段二、三 |
| **阶段五** | 回测框架 | Day 3-4 | 阶段四 |
| **阶段六** | 参数优化 | Day 4-5 | 阶段五 |
| **阶段七** | 部署监控 | Day 5 | 阶段六 |

### 10.2 关键里程碑

- **Day 1 End**: 数据模块 + 基础特征工程完成
- **Day 2 End**: 价格行为模块 + LSTM模型完成
- **Day 3 End**: 所有模型 + 集成框架完成
- **Day 4 End**: 回测框架 + 初步优化完成
- **Day 5 End**: 完整系统 + 部署上线

---

## 附录

### A. 技术栈

- **语言**: Python 3.11+
- **ML框架**: TensorFlow/PyTorch, XGBoost, scikit-learn
- **数据处理**: Pandas, NumPy
- **可视化**: Matplotlib, Plotly
- **数据库**: SQLite (开发), PostgreSQL (生产)
- **缓存**: Redis
- **API**: FastAPI

### B. 参考文献

1. "Advances in Financial Machine Learning" - Marcos López de Prado
2. "Deep Learning for Time Series Forecasting" - Jason Brownlee
3. "Technical Analysis of the Financial Markets" - John Murphy
4. "Price Action Trading" - Bob Volman

---

*文档版本: 1.0.0*  
*创建时间: 2026-02-26 16:00*  
*最后更新: 2026-02-26 16:30*
