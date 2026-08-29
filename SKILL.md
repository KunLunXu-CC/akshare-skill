---
name: akshare
description: 使用 AkShare 获取中国金融市场数据，包括 A 股、港股、美股、期货、基金和宏观经济指标的实时与历史数据。当用户查询中国市场行情、股票价格、市场分析或中国交易所金融信息时使用。
---

# AkShare 中国金融数据

## 概述

AkShare 是一个免费、开源的 Python 金融数据接口库。本技能用于查询上海证券交易所、深圳证券交易所、香港交易所等市场的数据。

## 快速开始

安装 AkShare：

```bash
pip install akshare
```

获取 A 股实时行情：

```python
import akshare as ak

df = ak.stock_zh_a_spot_em()  # A 股实时行情
```

## 股票数据

### A 股

实时行情：

```python
# 全部 A 股实时行情
df = ak.stock_zh_a_spot_em()

# 单只股票实时行情
df = ak.stock_zh_a_spot()
```

历史行情：

```python
# 日线历史行情
df = ak.stock_zh_a_hist(
    symbol="000001",
    period="daily",
    start_date="20240101",
    end_date="20241231",
    adjust="qfq",
)
```

股票列表：

```python
# 获取全部 A 股代码和名称
df = ak.stock_info_a_code_name()
```

### 港股

```python
# 实时行情
df = ak.stock_hk_spot_em()

# 历史行情
df = ak.stock_hk_hist(symbol="00700", period="daily", adjust="qfq")
```

### 美股

```python
# 实时行情
df = ak.stock_us_spot_em()
```

## 期货数据

```python
# 商品期货实时行情
df = ak.futures_zh_spot()

# 期货历史行情
df = ak.futures_zh_hist_sina(symbol="IF0")
```

## 基金数据

```python
# 基金列表
df = ak.fund_open_fund_info_em()

# 基金历史净值
df = ak.fund_open_fund_info_em(fund="000001", indicator="单位净值走势")
```

## 宏观经济指标

```python
# 国内生产总值
gdp = ak.macro_china_gdp()

# 居民消费价格指数
cpi = ak.macro_china_cpi()

# 采购经理指数
pmi = ak.macro_china_pmi()
```

## 常用参数

周期：

- `daily`：日线
- `weekly`：周线
- `monthly`：月线

复权方式：

- `qfq`：前复权
- `hfq`：后复权
- `""`：不复权

## 使用建议

1. AkShare 默认不缓存数据；需要时自行实现缓存。
2. 控制请求频率，避免触发数据源限流。
3. 接口通常返回 pandas `DataFrame`，可直接筛选、聚合或导出。
4. 网络和上游数据源可能不稳定，应按场景增加超时、重试和异常处理。

## 参考资料

- [AkShare API 参考](references/akshare_api.md)：详细接口说明
- [常用函数](references/common_functions.md)：高频函数和常见模式
- [AkShare 官方文档](https://akshare.akfamily.xyz/)
