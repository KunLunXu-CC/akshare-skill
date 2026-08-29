# AkShare API 参考

## 股票数据接口

### A 股实时行情：`stock_zh_a_spot_em()`

获取东方财富网的沪深京 A 股实时行情。

参数：无。

返回值：包含以下主要字段的 `DataFrame`：

- 代码、名称、最新价、涨跌幅、涨跌额
- 成交量、成交额、振幅
- 最高、最低、今开、昨收
- 量比、换手率、市盈率-动态、市净率

```python
df = ak.stock_zh_a_spot_em()
print(df.head())
```

### A 股历史行情：`stock_zh_a_hist()`

获取东方财富网的沪深京 A 股个股历史行情。

参数：

- `symbol`：股票代码，例如 `"000001"`
- `period`：周期，可选 `"daily"`、`"weekly"`、`"monthly"`
- `start_date`：开始日期，格式为 `YYYYMMDD`
- `end_date`：结束日期，格式为 `YYYYMMDD`
- `adjust`：复权方式；`"qfq"` 为前复权，`"hfq"` 为后复权，`""` 为不复权

返回值：包含开盘价、最高价、最低价、收盘价和成交量等数据的 `DataFrame`。

```python
df = ak.stock_zh_a_hist(
    symbol="000001",
    period="daily",
    start_date="20240101",
    end_date="20241231",
    adjust="qfq",
)
```

### A 股代码与名称：`stock_info_a_code_name()`

获取全部沪深京 A 股代码和名称。无参数，返回股票代码与名称组成的 `DataFrame`。

```python
df = ak.stock_info_a_code_name()
```

## 港股数据接口

### `stock_hk_spot_em()`

获取东方财富网港股实时行情。无参数，返回港股实时行情 `DataFrame`。

### `stock_hk_hist()`

获取东方财富网港股个股历史行情。

- `symbol`：港股代码，例如 `"00700"`
- `period`：周期
- `adjust`：复权方式

```python
df = ak.stock_hk_hist(symbol="00700", period="daily", adjust="qfq")
```

## 美股数据接口

### `stock_us_spot_em()`

获取东方财富网美股实时行情。无参数，返回美股实时行情 `DataFrame`。

## 期货数据接口

### `futures_zh_spot()`

获取东方财富网中国商品期货实时行情。无参数，返回期货实时行情 `DataFrame`。

### `futures_zh_hist_sina()`

获取新浪财经中国商品期货历史行情。

- `symbol`：期货代码，例如 `"IF0"`
- `start_date`：开始日期
- `end_date`：结束日期

```python
df = ak.futures_zh_hist_sina(
    symbol="IF0",
    start_date="20240101",
    end_date="20241231",
)
```

## 基金数据接口

### `fund_open_fund_info_em()`

获取天天基金网开放式基金数据。

- `fund`：基金代码，可选
- `indicator`：指标类型，可选，例如 `"单位净值走势"`

```python
# 获取全部基金
all_funds = ak.fund_open_fund_info_em()

# 获取指定基金
fund = ak.fund_open_fund_info_em(fund="000001", indicator="单位净值走势")
```

## 宏观经济数据接口

以下函数均无参数并返回相应指标的 `DataFrame`：

```python
gdp = ak.macro_china_gdp()  # 国内生产总值
cpi = ak.macro_china_cpi()  # 居民消费价格指数
pmi = ak.macro_china_pmi()  # 采购经理指数
```

## 指数数据接口

### `index_zh_a_hist()`

获取沪深京 A 股指数历史行情。

- `symbol`：指数代码，例如上证指数 `"sh000001"`
- `period`：周期
- `start_date`：开始日期
- `end_date`：结束日期

```python
df = ak.index_zh_a_hist(
    symbol="sh000001",
    period="daily",
    start_date="20240101",
    end_date="20241231",
)
```

### `index_zh_a_spot()`

获取沪深京 A 股指数实时行情。无参数，返回指数实时行情 `DataFrame`。

## 常用证券代码

### 主要 A 股指数

- `sh000001`：上证指数
- `sz399001`：深证成指
- `sz399006`：创业板指
- `sh000300`：沪深 300
- `sz399905`：中证 500

### 主要港股

- `00700`：腾讯控股
- `00941`：中国移动
- `02318`：中国平安
- `03690`：美团
- `00388`：港交所

### 主要美股

- `AAPL`：苹果
- `MSFT`：微软
- `GOOGL`：谷歌
- `TSLA`：特斯拉
- `AMZN`：亚马逊

## 错误处理

常见问题包括网络错误、参数格式错误，以及上游数据源暂时不可用。可以按业务需求增加重试：

```python
import time

import akshare as ak


def fetch_with_retry(func, max_retries=3, delay=1):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception:
            if attempt == max_retries - 1:
                raise
            time.sleep(delay)


df = fetch_with_retry(lambda: ak.stock_zh_a_spot_em())
```

## 常见数据处理

```python
# 筛选涨幅超过 5% 的股票
df = df[df["涨跌幅"] > 5]

# 按成交量降序排列
df = df.sort_values("成交量", ascending=False)

# 计算 5 日均线
df["MA5"] = df["收盘"].rolling(window=5).mean()

# 导出 CSV
df.to_csv("stock_data.csv", index=False)
```

完整接口说明请查看 [AkShare 官方文档](https://akshare.akfamily.xyz/)和 [AkShare GitHub 仓库](https://github.com/akfamily/akshare)。
