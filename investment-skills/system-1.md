# 投资技能文档：工具与系统（一）

技能编号：192-196 / 200+

---

## 192. 数据库设计原则

### 概念定义
数据库设计是量化系统的基础，合理的设计原则确保数据的高效存储、快速查询和可靠维护。

### 核心原则

#### 1. 规范化（Normalization）
- **第一范式（1NF）**：原子性，每列不可再分
- **第二范式（2NF）**：消除部分依赖
- **第三范式（3NF）**：消除传递依赖
- **适度反范式**：查询性能优化时适度冗余

#### 2. 数据完整性
- **实体完整性**：主键唯一且非空
- **参照完整性**：外键约束
- **域完整性**：数据类型、范围约束
- **业务完整性**：检查约束、触发器

#### 3. 可扩展性
- **分区设计**：按时间、范围分区
- **分库分表**：水平/垂直拆分
- **读写分离**：主从架构
- **索引优化**：B+树、哈希索引选择

### 金融数据特点
- **时序性**：时间戳为核心维度
- **高写入**：行情数据高频写入
- **复杂查询**：多维度分析需求
- **历史数据**：长期数据归档

### 表设计规范
```sql
-- 行情数据表示例
CREATE TABLE market_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    trade_time TIME NOT NULL,
    open_price DECIMAL(18,4),
    high_price DECIMAL(18,4),
    low_price DECIMAL(18,4),
    close_price DECIMAL(18,4),
    volume BIGINT,
    amount DECIMAL(20,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol_date (symbol, trade_date),
    INDEX idx_time (trade_date, trade_time)
) ENGINE=InnoDB;
```

### 注意事项
- 选择合适的数据类型（DECIMAL表示价格）
- 预留扩展字段应对业务变化
- 敏感数据加密存储
- 定期备份和归档策略
- 考虑数据合规（个人信息保护）

---

## 193. SQL高级查询

### 概念定义
SQL高级查询技术用于处理复杂的金融数据分析需求，包括窗口函数、CTE、递归查询等。

### 窗口函数（Window Functions）
```sql
-- 计算移动平均
SELECT 
    symbol,
    trade_date,
    close_price,
    AVG(close_price) OVER (
        PARTITION BY symbol 
        ORDER BY trade_date 
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) AS ma20
FROM market_data;

-- 排名
SELECT 
    symbol,
    return_rate,
    RANK() OVER (ORDER BY return_rate DESC) as rank
FROM stock_returns;

-- 领先/滞后
SELECT 
    symbol,
    trade_date,
    close_price,
    LAG(close_price, 1) OVER (PARTITION BY symbol ORDER BY trade_date) AS prev_close,
    LEAD(close_price, 1) OVER (PARTITION BY symbol ORDER BY trade_date) AS next_close
FROM market_data;
```

### CTE（公用表表达式）
```sql
WITH daily_returns AS (
    SELECT 
        symbol,
        trade_date,
        (close_price - LAG(close_price) OVER (PARTITION BY symbol ORDER BY trade_date)) 
            / LAG(close_price) OVER (PARTITION BY symbol ORDER BY trade_date) AS return_rate
    FROM market_data
),
volatility AS (
    SELECT 
        symbol,
        STDDEV(return_rate) AS volatility
    FROM daily_returns
    GROUP BY symbol
)
SELECT * FROM volatility ORDER BY volatility DESC;
```

### 金融常用查询模式
- **收益率计算**：(今收-昨收)/昨收
- **波动率计算**：收益率标准差
- **最大回撤**：历史高点到当前低点的最大跌幅
- **相关系数**：两资产收益的相关性
- **分组聚合**：行业、市值分组统计

### 性能优化
- **索引使用**：WHERE、JOIN、ORDER BY字段加索引
- **避免SELECT ***：只查询需要的列
- **批量操作**：使用批量插入替代单条
- **查询分析**：EXPLAIN分析执行计划
- **分区裁剪**：利用分区减少扫描范围

### 注意事项
- 大数据量查询需分页处理
- 复杂计算考虑预处理或物化视图
- 注意NULL值处理
- 时区统一处理
- 交易时间与非交易时间区分

---

## 194. 时序数据库

### 概念定义
时序数据库（Time Series Database, TSDB）专门优化存储和查询时间序列数据，是金融行情数据存储的首选。

### 特点
- **高写入吞吐**：支持每秒百万级数据点
- **高效压缩**：时序数据高压缩比
- **时间范围查询**：快速查询时间窗口数据
- **降采样**：自动聚合历史数据
- **保留策略**：自动过期旧数据

### 主流时序数据库
| 数据库 | 特点 | 适用场景 |
|--------|------|---------|
| InfluxDB | 开源、易用、生态好 | 中小规模量化系统 |
| TimescaleDB | PostgreSQL扩展 | 需SQL兼容的场景 |
| ClickHouse | OLAP分析强 | 大规模数据分析 |
| DolphinDB | 国产、内置计算 | 一体化量化平台 |
| Kdb+ | 金融行业标准 | 高频交易 |
| QuestDB | 高性能、SQL兼容 | 开源替代方案 |

### InfluxDB示例
```sql
-- 写入数据
INSERT stock_price,symbol=AAPL close=150.5,volume=1000000 1635724800000000000

-- 查询数据
SELECT MEAN(close) FROM stock_price 
WHERE symbol = 'AAPL' 
AND time >= now() - 30d
GROUP BY time(1d)

-- 连续查询（自动降采样）
CREATE CONTINUOUS QUERY cq_1h ON finance
BEGIN
    SELECT mean(close) AS close_avg INTO stock_price_1h FROM stock_price
    GROUP BY time(1h),symbol
END
```

### 数据建模最佳实践
- **Measurement**：类似表的概念（如stock_price）
- **Tag**：索引字段（如symbol, exchange）
- **Field**：数据字段（如price, volume）
- **时间精度**：根据需求选择（纳秒/毫秒/秒）

### 注意事项
- Tag值避免高基数（如订单ID）
- 设计合理的Retention Policy
- 批量写入提高效率
- 高可用架构设计
- 与关系型数据库配合使用

---

## 195. 数据仓库架构

### 概念定义
数据仓库是面向主题的、集成的、相对稳定的、反映历史变化的数据集合，用于量化策略研究和决策支持。

### 架构层次

#### 1. 数据源层
- **行情数据**：交易所、数据供应商
- **基本面数据**：财报、公告
- **另类数据**：舆情、供应链
- **外部数据**：宏观、行业数据

#### 2. 数据采集层（ETL）
- **Extract**：数据抽取
- **Transform**：数据清洗、转换
- **Load**：数据加载

#### 3. 数据存储层
- **ODS（操作数据存储）**：原始数据
- **DWD（明细数据层）**：清洗后明细
- **DWS（汇总数据层）**：轻度聚合
- **ADS（应用数据层）**：面向应用

#### 4. 数据服务层
- **API服务**：统一数据接口
- **文件服务**：批量数据导出
- **实时流**：Kafka等消息队列

### 建模方法
- **维度建模**：星型模型、雪花模型
- **事实表**：交易事实、持仓事实
- **维度表**：时间、股票、行业维度

### 技术栈
- **存储**：HDFS、对象存储、数据湖
- **计算**：Spark、Flink、Presto
- **调度**：Airflow、DolphinScheduler
- **治理**：数据血缘、元数据管理

### 注意事项
- 数据质量是核心（准确性、完整性、及时性）
- 元数据管理便于数据发现
- 数据安全和权限控制
- 冷热数据分层存储
- 成本与性能平衡

---

## 196. 系统架构设计

### 概念定义
量化系统架构设计是构建稳定、高效、可扩展的量化交易平台的技术规划，涵盖数据采集、策略研究、交易执行全流程。

### 系统分层

#### 1. 数据层
- **行情数据**：实时行情、历史行情
- **基础数据**：股票信息、财务数据
- **因子数据**：计算好的各类因子
- **策略数据**：持仓、交易记录

#### 2. 计算层
- **研究环境**：Jupyter、量化回测框架
- **因子计算**：分布式因子引擎
- **策略回测**：事件驱动回测系统
- **模型训练**：机器学习平台

#### 3. 策略层
- **信号生成**：Alpha模型
- **组合构建**：风险模型、优化器
- **执行算法**：TWAP/VWAP/智能路由
- **风控系统**：事前/事中/事后风控

#### 4. 交易层
- **订单管理**：OMS订单管理系统
- **交易网关**：对接券商/交易所
- **清算结算**：对账、资金结算
- **监控报警**：实时监控

### 关键设计原则
- **高可用**：主备、集群、故障转移
- **低延迟**：网络优化、本地计算
- **可扩展**：微服务、容器化
- **安全性**：加密、审计、权限

### 技术选型示例
```
┌─────────────────────────────────────┐
│           前端界面 (Vue/React)        │
├─────────────────────────────────────┤
│           API网关 (Kong/Nginx)       │
├─────────────────────────────────────┤
│  策略服务  │  回测服务  │  数据服务   │
│  (Python) │  (Python)  │  (Go/Java) │
├─────────────────────────────────────┤
│       消息队列 (Kafka/Redis)         │
├─────────────────────────────────────┤
│  时序DB   │  关系DB    │  缓存       │
│InfluxDB   │PostgreSQL  │  Redis     │
└─────────────────────────────────────┘
```

### 注意事项
- 区分研究和生产环境
- 版本控制（代码、数据、模型）
- 完善的日志和监控
- 灾备和恢复计划
- 合规和审计要求

---

*文档生成时间：2026-02-25*
*进度：196/200+ 已完成*
