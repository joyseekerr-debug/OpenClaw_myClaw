# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## 核心技能 (Core Skills)

### 1. 子代理自适应调度器 ⭐ 主要

**路径:** `skills/subagent-scheduler/`
**版本:** v1.5.0 (全功能版)
**状态:** ✅ **全部功能已启用，自动启动**

**启用功能:**
| 功能 | 状态 | 自动启动 |
|------|------|----------|
| 五大策略分支 | ✅ | - |
| LLM智能分类 | ✅ | - |
| 流式进度通知 | ✅ | - |
| 试探执行 | ✅ | - |
| 分布式追踪 | ✅ | - |
| **每日学习定时任务** | ✅ | 6:00分析+9:00推送 |
| **协作中心** | ✅ | 是 |
| **执行监控** | ✅ | 是 |
| **指令队列** | ✅ | 是 |
| **自动路由** | ✅ | 复杂度检测 |
| **多Agent协作** | ✅ | 复杂度≥70分 |

**使用方式:**
```javascript
const { getMessageHandler } = require('./skills/subagent-scheduler');
const handler = getMessageHandler();

// 处理消息（自动路由+队列+多Agent）
const result = await handler.handleMessage(message, chatId, userInfo);

// 队列状态
const status = handler.getStatus();
console.log(`队列长度: ${status.queueLength}`);

// 监控仪表板
const dashboard = handler.getDashboard();
```

**任务处理流程:**
```
用户消息 → 复杂度分析
              ↓
    简单任务 → 快速处理
    中等任务 → 队列+确认
    复杂任务 → 队列+多Agent+确认
```

**成本上限:**
- 单任务: $1
- 单日: $50

**详细文档:** 见 `SKILL.md`

---

### 2. 视频内容提取器

**路径:** `skills/video-extractor/`

**功能:** 从B站、YouTube等平台提取视频字幕和音频转录

**使用方式:**
```javascript
const { extractVideoContent } = require('./skills/video-extractor');

// 提取视频内容
const result = await extractVideoContent('https://b23.tv/xxx', {
  languages: ['zh-CN'],      // 字幕语言
  autoSubtitles: true,       // 允许自动字幕
  transcribe: true,          // 无字幕时音频转录
  summarize: true            // 生成摘要
});

// 结果
result.info          // 视频信息
result.subtitles     // 字幕内容
result.transcript    // 音频转录
result.summary       // 内容摘要
```

**依赖:**
```bash
pip install yt-dlp openai-whisper
```

---

### 3. 投资交易技能体系 📈 (200+ 技能)

**路径:** `skills/investment/` + `skills/investment-learning/` + `stock-trading-system/`
**状态:** ✅ **已完成全部200+项技能学习**

---

#### 技能总览

| 模块 | 技能数量 | 内容 | 路径 |
|------|----------|------|------|
| **基础认知** | 6项 | 股票机制、港股通、财报分析、估值方法、行业框架、宏观经济 | `investment/01_basics/` |
| **技术分析指标** | 47项 | SMA/EMA/MACD/RSI/KDJ/布林带/ATR等 | `stock-trading-system/features/technical.py` |
| **Alpha因子** | 50+项 | 订单流特征、市场情绪、流动性、趋势强度等 | `stock-trading-system/features/alpha.py` |
| **价格行为学** | 40+项 | 支撑阻力、趋势分析、图表形态、K线、成交量、多时间框架 | `TOOLS.md` 本节 |
| **量化模型** | 3项 | LSTM/XGBoost/Transformer多尺度预测 | `stock-trading-system/models/` |
| **风险管理** | 12项 | 仓位管理、止损止盈、组合风控、压力测试 | `investment/04_risk/` |
| **交易执行** | 8项 | 订单类型、成本控制、滑点管理、执行策略 | `investment/05_execution/` |
| **监控预警** | 10项 | 实时监控、预警算法、通知系统、数据可视化 | `investment/06_monitoring/` |
| **投资心理** | 8项 | 情绪管理、决策框架、复盘机制、行为金融学 | `investment/07_psychology/` |
| **进阶技能** | 16项 | 衍生品、跨市场套利、另类数据、算法交易 | `investment/08_advanced/` |
| **系统组件** | 35+项 | 数据源、缓存、回测、监控、通知等 | `stock-trading-system/` |
| **总计** | **200+项** | 完整投资交易技能体系 | - |

---

#### 3.1 基础认知 (6项)

| 技能 | 文件 | 代码 | 测试 |
|------|------|------|------|
| 股票市场运作机制 | `docs/stock_market_mechanism.md` | `code/stock_market_mechanism.py` | ✅ |
| 港股通规则详解 | `docs/hk_stock_connect_rules.md` | `code/hk_stock_connect_rules.py` | ✅ |
| 财务报表分析 | `docs/financial_statement_analysis.md` | `code/financial_statement_analysis.py` | ✅ |
| 估值方法 | `docs/valuation_methods.md` | `code/valuation_methods.py` | ✅ |
| 行业分析框架 | `docs/industry_analysis_framework.md` | `code/industry_analysis_framework.py` | ✅ |
| 宏观经济基础 | - | - | 📖 |

---

#### 3.2 技术分析指标 (47项)

**趋势指标 (7项):**
1. SMA简单移动平均线
2. EMA指数移动平均线
3. MACD异同移动平均线
4. DMI趋向指标
5. SAR抛物线转向
6. 均线系统
7. 趋势线

**动量指标 (8项):**
8. RSI相对强弱指标
9. KDJ随机指标
10. CCI商品通道指数
11. 威廉指标(WR)
12. ROC变动率指标
13. 动量指标(Momentum)
14. PSY心理线
15. BIAS乖离率

**波动率指标 (4项):**
16. 布林带(Bollinger Bands)
17. ATR平均真实波幅
18. 真实波动率
19. 历史波动率

**成交量指标 (5项):**
20. 成交量分析
21. OBV能量潮
22. VR容量比率
23. 量价趋势
24. 资金流指标

**支撑阻力 (3项):**
25. 支撑阻力位
26. 动态支撑阻力(均线)
27. 黄金分割位

**反转形态 (6项):**
28. 头肩顶/底
29. 双顶/双底
30. 圆弧顶/底
31. V形反转
32. 岛形反转
33. 钻石形态

**持续形态 (5项):**
34. 对称三角形
35. 上升三角形
36. 下降三角形
37. 旗形与楔形
38. 矩形整理

**特殊形态 (4项):**
39. 杯柄形态
40. 扩散三角形
41. 缺口理论
42. 窗口形态

**波浪与斐波那契 (3项):**
43. 波浪理论基础
44. 斐波那契回调
45. 斐波那契扩展

**时间框架 (2项):**
46. 多时间框架分析
47. 时间周期理论

---

#### 3.3 价格行为学 (Price Action) (40+项)

**定义:** 通过分析原始价格走势和图表形态来预测未来价格变动的交易方法，不依赖传统技术指标。

**支撑与阻力 (8项):**
1. 水平支撑阻力位识别
2. 趋势线支撑阻力
3. 动态支撑阻力（均线）
4. 心理关口（整数位）
5. 前期高低点
6. 支撑阻力角色互换
7. 支撑阻力强度判断
8. 假突破识别

**趋势分析 (6项):**
9. 上升趋势线绘制
10. 下降趋势线绘制
11. 趋势通道绘制
12. 趋势角度分析（45°原则）
12. 趋势强度评估
14. 趋势反转信号

**图表形态 - 反转 (8项):**
15. 头肩顶
16. 头肩底
17. 双顶形态
18. 双底形态
19. 圆弧顶
20. 圆弧底
21. V形顶
22. V形底

**图表形态 - 持续 (6项):**
23. 上升三角形
24. 下降三角形
25. 对称三角形
26. 上升旗形
27. 下降旗形
28. 矩形整理

**K线分析 - 单根 (8项):**
29. 锤子线
30. 流星线
31. 十字星
32. 吞没形态（看涨）
33. 吞没形态（看跌）
34. 长腿十字
35. 墓碑十字
36. 蜻蜓十字

**K线分析 - 组合 (6项):**
37. 启明星
38. 黄昏星
39. 三只乌鸦
40. 白兵（三阳线）
41. 孕线形态
42. 刺透形态

**成交量分析 (5项):**
43. 量价配合原则
44. 放量突破确认
45. 缩量回调健康
46. 放量滞涨警示
47. 地量地价识别

**多时间框架 (4项):**
48. 大周期定方向
49. 小周期定时机
50. 周期共振原则
51. 时间框架切换

---

#### 3.4 Alpha因子 (50+项)

**订单流特征 (10项):**
1. 订单失衡(Order Imbalance)
2. 交易强度(Trade Intensity)
3. 大单比率(Large Order Ratio)
4. 主动买入比率
5. 主动卖出比率
6. 买卖压力差
7. 订单簿深度
8. 资金净流入
9. 资金净流出
10. 资金流向趋势

**价格特征 (10项):**
11. 收益率(Returns)
12. 对数收益率
13. 实际波动率
14. 日内波动率
15. 收益率偏度
16. 收益率峰度
17. 价格加速度
18. 价格动量
19. 价格反转信号
20. 价格延续信号

**趋势特征 (8项):**
21. 趋势强度
22. 趋势方向
23. 趋势持续时间
24. 均线偏离度
25. 均线交叉信号
26. 多头排列/空头排列
27. 趋势衰竭信号
28. 趋势加速信号

**均值回归 (6项):**
29. Z分数(20日)
30. Z分数(60日)
31. 距均线距离
32. 布林带位置
33. 超买超卖程度
34. 回归概率

**流动性特征 (8项):**
35. Amihud非流动性指标
36. 换手率
37. 成交量波动
38. 流动性冲击
39. 买卖价差
40. 市场深度
41. 冲击成本
42. 流动性风险

**情绪特征 (8项):**
43. 恐慌贪婪指数
44. 波动率指数(VIX)
45. 市场情绪指标
46. 投机情绪
47. 散户情绪
48. 机构情绪
49. 新闻情绪
50. 社交媒体情绪

---

#### 3.5 量化模型 (3项)

| 模型 | 时间尺度 | 适用场景 | 文件 |
|------|----------|----------|------|
| LSTM | 1-5分钟 | 高频预测 | `models/lstm_model.py` |
| XGBoost | 15-60分钟 | 中频预测 | `models/xgboost_model.py` |
| Transformer | 日线/周线 | 低频预测 | `models/transformer_model.py` |

**模型集成:**
- 多尺度集成框架
- 加权投票机制
- 动态权重调整
- SHAP解释性分析

---

#### 3.6 风险管理 (12项)

**仓位管理 (4项):**
1. 凯利公式
2. 固定比例法
3. 波动率仓位法
4. 最大回撤控制

**止损止盈 (4项):**
5. 固定金额止损
6. 百分比止损
7. ATR动态止损
8. 移动止盈

**组合风控 (4项):**
9. 分散化投资
10. 相关性分析
11. 风险价值(VaR)
12. 压力测试

---

#### 3.7 交易执行 (8项)

**订单类型 (4项):**
1. 市价单
2. 限价单
3. 止损单
4. 条件单

**成本控制 (4项):**
5. 滑点管理
6. 冲击成本
7. 交易费用优化
8. 执行算法

---

#### 3.8 监控预警 (10项)

**实时监控 (4项):**
1. 价格监控
2. 成交量监控
3. 波动率监控
4. 资金流向监控

**预警算法 (4项):**
5. 价格突破预警
6. 异常波动预警
7. 技术指标预警
8. 组合风险预警

**通知系统 (2项):**
9. 飞书通知集成
10. 多渠道通知

---

#### 3.9 投资心理 (8项)

1. 情绪管理
2. 恐惧与贪婪控制
3. 决策框架
4. 认知偏差识别
5. 复盘机制
6. 交易日志
7. 心理韧性训练
8. 行为金融学基础

---

#### 3.10 进阶技能 (16项)

**衍生品 (6项):**
1. 期货基础
2. 期权基础
3. 期权策略
4. 希腊字母
5. 波动率交易
6. 对冲策略

**跨市场套利 (5项):**
7. 期现套利
8. 跨期套利
9. 跨品种套利
10. 跨市场套利
11. 统计套利

**另类数据 (5项):**
12. 卫星图像
13. 社交媒体数据
14. 供应链数据
15. 消费者行为数据
16. 新闻情绪数据

---

#### 3.11 系统组件 (35+项)

**数据源 (4项):**
1. iTick数据源
2. Yahoo Finance
3. AKShare
4. 新浪财经

**数据处理 (6项):**
5. 数据清洗
6. 数据标准化
7. 缺失值处理
8. 异常值检测
9. 数据对齐
10. 数据缓存(Redis)

**特征工程 (5项):**
11. 技术指标计算
12. Alpha因子计算
13. 特征选择
14. 特征缩放
15. 特征缓存

**回测框架 (5项):**
16. 回测引擎
17. 绩效评估(15+指标)
18. 滑点模拟
19. 费用计算
20. 可视化报告

**监控模块 (5项):**
21. 实时数据获取
22. 预警触发器
23. 飞书通知
24. 日志记录
25. 性能监控

**交易执行 (5项):**
26. 订单管理
27. 仓位管理
28. 风控检查
29. 成交确认
30. 记录归档

**工具与测试 (5项):**
31. 数据验证工具
32. API测试脚本
33. 单元测试
34. 集成测试
35. 性能测试

---

#### 使用方式

```javascript
// 读取技能文档
const rsiDoc = await read('skills/investment-learning/phase2-技术分析/01-RSI指标.md');

// 使用技术指标
const { TechnicalIndicatorCalculator } = require('./stock-trading-system/features/technical');
const calc = new TechnicalIndicatorCalculator();
const features = calc.calculate_all(priceData);

// 使用Alpha因子
const { AlphaFactorCalculator } = require('./stock-trading-system/features/alpha');
const alpha = new AlphaFactorCalculator();
const factors = alpha.calculate_all(priceData);

// 启动完整交易系统
const { StockTradingSystem } = require('./stock-trading-system/main');
const system = new StockTradingSystem();
await system.start();
```

---

Add whatever helps you do your job. This is your cheat sheet.
