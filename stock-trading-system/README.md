# 小米集团股票交易预测系统

## 项目概述

基于多数据源、多时间尺度、多模型集成的股票交易预测系统，专注于小米集团(1810.HK)的深度分析与预测。

## 核心特性

- 🔴 **秒级实时监控** - WebSocket实时数据推送
- 📊 **多时间尺度预测** - 1分钟/5分钟/15分钟/日线/周线
- 🤖 **多模型集成** - LSTM + XGBoost + Transformer
- 🔗 **多数据源融合** - iTick + Yahoo + AKShare
- 🧠 **SHAP解释性** - 模型决策可解释
- 🚨 **智能预警系统** - 飞书实时通知
- 💾 **Redis高速缓存** - 特征与预测结果缓存

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    小米集团股票预测系统                        │
├─────────────────────────────────────────────────────────────┤
│  数据层  →  特征层  →  模型层  →  预测层  →  监控层  →  通知层  │
├─────────────────────────────────────────────────────────────┤
│ • iTick         • 技术指标      • LSTM      • 信号融合    • 实时大屏    │
│ • Yahoo        • Alpha因子    • XGBoost   • 置信度      • 预警系统    │
│ • AKShare      • NLP情感      • Transformer • 回测验证   • 飞书通知    │
│ • 爬虫        • 产业链特征    • 集成模型   • SHAP解释              │
└─────────────────────────────────────────────────────────────┘
```

## 开发阶段

### Phase 0: 基础架构 ✅ 进行中
- [x] 项目结构搭建
- [x] 多数据源管理
- [x] Redis缓存系统
- [ ] 实时数据流

### Phase 1: 特征工程 (Week 2-3)
- [ ] 技术指标计算
- [ ] Alpha因子开发
- [ ] NLP情感分析
- [ ] 产业链特征

### Phase 2: 多尺度预测 (Week 4-6)
- [ ] 高频预测模型
- [ ] 中频预测模型
- [ ] 低频预测模型
- [ ] 信号融合系统

### Phase 3: 模型集成 (Week 7-8)
- [ ] 多模型训练
- [ ] Stacking集成
- [ ] SHAP解释性

### Phase 4: 回测风控 (Week 9)
- [ ] 回测框架
- [ ] 风险管理系统

### Phase 5: 监控部署 (Week 10)
- [ ] 秒级监控系统
- [ ] 飞书通知对接

## 快速开始

```bash
# 1. 克隆项目
git clone <repo-url>
cd stock-trading-system

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的API key

# 4. 启动系统
python main.py
```

## 配置说明

复制 `.env.example` 到 `.env` 并填写:

```env
# iTick API
ITICK_API_KEY=your_itick_api_key

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# 飞书
FEISHU_WEBHOOK_URL=your_webhook_url
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
```

## 项目结构

```
stock-trading-system/
├── data/              # 数据层
│   ├── data_source.py # 多数据源管理
│   └── preprocessor.py # 数据预处理
├── features/          # 特征工程
│   ├── technical.py   # 技术指标
│   ├── fundamental.py # 基本面特征
│   └── nlp.py         # NLP情感分析
├── models/            # 模型层
│   ├── lstm.py        # LSTM模型
│   ├── xgboost.py     # XGBoost模型
│   ├── transformer.py # Transformer模型
│   └── ensemble.py    # 集成模型
├── monitoring/        # 监控层
│   ├── realtime.py    # 实时监控
│   ├── alerts.py      # 预警系统
│   └── notifier.py    # 通知系统
├── trading/           # 交易层
│   ├── backtest.py    # 回测系统
│   ├── risk.py        # 风控管理
│   └── executor.py    # 交易执行(预留)
├── utils/             # 工具
│   ├── cache.py       # Redis缓存
│   ├── logger.py      # 日志配置
│   └── database.py    # 数据库
├── config.py          # 全局配置
├── main.py            # 主入口
├── requirements.txt   # 依赖
└── README.md          # 说明
```

## 技术栈

- **Python 3.11+**
- **数据**: pandas, numpy, yfinance, akshare, itick
- **ML/DL**: scikit-learn, XGBoost, PyTorch, Transformers
- **数据库**: Redis, SQLite
- **可视化**: matplotlib, plotly, dash
- **通知**: requests (飞书Webhook)

## 许可证

MIT License
