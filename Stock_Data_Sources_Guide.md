# 股市数据获取方式大全

## 一、我可直接使用的工具/方法

### 1. 网页抓取 (Web Fetch)
**状态**: ✅ 可用，但Yahoo Finance在中国大陆被屏蔽

| 数据源 | URL | 数据类型 | 限制 |
|:---|:---|:---|:---|
| stockanalysis.com | stockanalysis.com/stocks/{代码}/ | 基本面、分析师评级 | 部分页面可用 |
| MarketWatch | marketwatch.com/investing/stock/{代码} | 股价、财报 | 可能有限制 |
| 东方财富 | emsec.eastmoney.com | A股/港股 | 中文数据源 |
| 新浪财经 | finance.sina.com.cn | A股/港股/美股 | 中文数据源 |

**示例**:
```
https://stockanalysis.com/stocks/AAPL/
https://stockanalysis.com/etf/iez/holdings/
```

---

## 二、需要配置后使用的工具

### 2.1 Brave Search API (网络搜索)
**状态**: ⚠️ 需要配置API密钥

```bash
openclaw configure --section web
# 或设置环境变量 BRAVE_API_KEY
```

**用途**: 
- 搜索最新股价、财报、新闻
- 获取分析师评级变化
- 查找ETF成分股列表

---

### 2.2 Python + yfinance (推荐)
**状态**: ⚠️ 需要安装Python库

```bash
pip install yfinance pandas
```

**示例代码**:
```python
import yfinance as yf

# 获取单只股票数据
stock = yf.Ticker("AAPL")
info = stock.info  # 基本面数据
hist = stock.history(period="3mo")  # 3个月历史价格

# 获取ETF持仓
etf = yf.Ticker("IEZ")
holdings = etf.info  # ETF信息

# 批量获取多只股票
tickers = yf.Tickers("AAPL MSFT GOOGL")
```

**数据类型**:
- 实时股价、历史K线
- 财务报表（季报/年报）
- 分析师评级、目标价
- ETF持仓、行业分类
- 期权链数据

---

## 三、免费数据源/API

### 3.1 Alpha Vantage
**网址**: alphavantage.co
**费用**: 免费版500次/天
**数据**: 美股、ETF、外汇、加密货币

**示例**:
```
https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey=YOUR_KEY
```

---

### 3.2 Finnhub
**网址**: finnhub.io
**费用**: 免费版60次/分钟
**数据**: 全球股票（美股、港股、A股）

**示例**:
```
https://finnhub.io/api/v1/quote?symbol=AAPL&token=YOUR_KEY
```

---

### 3.3 IEX Cloud
**网址**: iexcloud.io
**费用**: 免费版50,000次/月
**数据**: 美股实时数据、基本面

---

### 3.4 Polygon.io
**网址**: polygon.io
**费用**: 免费版有限访问
**数据**: 美股历史数据、实时行情

---

### 3.5 Twelve Data
**网址**: twelvedata.com
**费用**: 免费版800次/天
**数据**: 全球股票、ETF、指数

---

## 四、中国股票数据源

### 4.1 AKShare (Python库)
```bash
pip install akshare
```

**示例**:
```python
import akshare as ak

# A股实时行情
stock_zh_a_spot_df = ak.stock_zh_a_spot()

# 港股实时行情
stock_hk_ggt_components_em_df = ak.stock_hk_ggt_components_em()

# 美股实时行情
stock_us_spot_em_df = ak.stock_us_spot_em()
```

---

### 4.2 Tushare
**网址**: tushare.pro
**费用**: 部分免费，高级功能需积分
**数据**: A股、港股、美股、期货、宏观数据

---

### 4.3 Baostock
**网址**: baostock.com
**费用**: 免费
**数据**: A股历史数据、财报数据

---

## 五、专业金融终端 (付费)

| 平台 | 费用 | 数据覆盖 | 适用场景 |
|:---|:---|:---|:---|
| **Bloomberg** | $2万+/年 | 全球 | 机构投资者 |
| **Refinitiv Eikon** | $1万+/年 | 全球 | 专业投资者 |
| **Wind (万得)** | ¥6万+/年 | 中国为主 | 国内机构 |
| **Choice (东方财富)** | ¥2万+/年 | 中国为主 | 国内机构 |
| **iFinD (同花顺)** | ¥1万+/年 | 中国为主 | 个人/机构 |

---

## 六、推荐方案

### 方案A：快速开始 (推荐)
**工具**: Python + yfinance + akshare
**适用**: 美股+A股+港股
**成本**: 免费

```python
# 美股
import yfinance as yf
data = yf.download("AAPL", period="3mo")

# A股
import akshare as ak
data = ak.stock_zh_a_spot()
```

---

### 方案B：网页抓取
**工具**: web_fetch + stockanalysis.com
**适用**: 快速获取ETF持仓、基本面
**成本**: 免费
**限制**: 频率受限，数据可能不完整

---

### 方案C：API集成
**工具**: Finnhub / Alpha Vantage
**适用**: 需要稳定、结构化数据
**成本**: 免费版足够个人使用

---

## 七、我应该优先尝试的方式

1. **网页抓取**: 继续尝试stockanalysis.com等可用站点
2. **Python + yfinance**: 如果你允许我安装Python环境
3. **AKShare**: 获取A股/港股数据
4. **你提供数据**: 你从TradingView/券商导出CSV发给我分析

---

**你希望我尝试哪种方式？或者你有特定的数据源偏好吗？**
