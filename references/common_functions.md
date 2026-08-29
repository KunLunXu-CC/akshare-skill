# AkShare 常用函数

## 高频函数速查

### 股票数据

```python
# 全部 A 股实时行情
ak.stock_zh_a_spot_em()

# 单只股票历史行情
ak.stock_zh_a_hist(
    symbol="000001",
    period="daily",
    start_date="20240101",
    end_date="20241231",
    adjust="qfq",
)

# 股票代码和名称列表
ak.stock_info_a_code_name()
```

### 指数数据

```python
# 指数历史行情
ak.index_zh_a_hist(
    symbol="sh000001",
    period="daily",
    start_date="20240101",
    end_date="20241231",
)

# 指数实时行情
ak.index_zh_a_spot()
```

### 基金、期货和宏观数据

```python
# 基金列表和指定基金净值
ak.fund_open_fund_info_em()
ak.fund_open_fund_info_em(fund="000001", indicator="单位净值走势")

# 期货实时和历史行情
ak.futures_zh_spot()
ak.futures_zh_hist_sina(
    symbol="IF0",
    start_date="20240101",
    end_date="20241231",
)

# 宏观指标
ak.macro_china_gdp()
ak.macro_china_cpi()
ak.macro_china_pmi()
```

## 按使用场景查询

### 获取股票价格

```python
# 实时价格
realtime = ak.stock_zh_a_spot_em()
print(realtime[realtime["代码"] == "000001"])

# 历史价格
history = ak.stock_zh_a_hist(
    symbol="000001",
    period="daily",
    start_date="20240101",
    end_date="20241231",
)
```

### 查看市场概况

```python
df = ak.stock_zh_a_spot_em()

# 涨幅榜、跌幅榜和成交量榜
top_gainers = df.sort_values("涨跌幅", ascending=False).head(10)
top_losers = df.sort_values("涨跌幅", ascending=True).head(10)
most_active = df.sort_values("成交量", ascending=False).head(10)
```

### 查询主要指数

```python
# 上证指数
shanghai = ak.index_zh_a_hist(
    symbol="sh000001",
    period="daily",
    start_date="20240101",
    end_date="20241231",
)

# 沪深 300
csi_300 = ak.index_zh_a_hist(
    symbol="sh000300",
    period="daily",
    start_date="20240101",
    end_date="20241231",
)
```

### 查询基金

```python
funds = ak.fund_open_fund_info_em()
technology_funds = funds[funds["基金简称"].str.contains("科技")]
```

## 常见处理模式

### 计算均线并导出

```python
import akshare as ak

df = ak.stock_zh_a_hist(
    symbol="000001",
    period="daily",
    start_date="20240101",
    end_date="20241231",
    adjust="qfq",
)
df["MA5"] = df["收盘"].rolling(5).mean()
df["MA10"] = df["收盘"].rolling(10).mean()
df.to_csv("000001.csv", index=False)
```

### 市场筛选

```python
import akshare as ak

df = ak.stock_zh_a_spot_em()
filtered = df[
    (df["涨跌幅"] > 0)  # 上涨
    & (df["成交量"] > 100000)  # 成交活跃
    & (df["市盈率-动态"] > 0)  # 市盈率为正
    & (df["市盈率-动态"] < 50)  # 市盈率低于 50
]
```

### 批量获取多只股票

```python
import akshare as ak

stock_codes = ["000001", "000002", "600000"]
for code in stock_codes:
    df = ak.stock_zh_a_hist(
        symbol=code,
        period="daily",
        start_date="20240101",
        end_date="20241231",
        adjust="qfq",
    )
    df.to_csv(f"{code}.csv", index=False)
```

## 数据格式说明

股票历史行情常见字段包括：日期、开盘、收盘、最高、最低、成交量、成交额、振幅、涨跌幅、涨跌额和换手率。

实时行情常见字段包括：代码、名称、最新价、涨跌幅、涨跌额、成交量、成交额、振幅、最高、最低、今开、昨收、量比、换手率、市盈率-动态和市净率。

AkShare 日期参数通常使用 `YYYYMMDD` 格式，例如开始日期 `"20240101"`、结束日期 `"20241231"`。

证券代码示例：

- A 股：`"000001"`、`"600000"`、`"300001"`
- 港股：`"00700"`
- 美股：`"AAPL"`、`"MSFT"`

## 性能建议

1. 能一次获取全部数据时，优先使用批量接口。
2. 缓存查询结果，避免重复请求。
3. 尽早筛选大数据集，减少后续计算量。
4. 根据分析需要选择周期，多数场景使用日线即可。

## 故障排查

### 找不到模块

```bash
pip install akshare
```

### 连接错误

- 检查网络连接。
- 增加重试机制。
- 检查上游数据源是否可用。

### 返回空 `DataFrame`

- 检查证券代码是否正确。
- 检查日期范围是否有效。
- 确认该周期内存在可用数据。

### 参数无效

- 检查日期是否为 `YYYYMMDD` 格式。
- 检查证券代码是否存在。
- 检查周期参数是否为接口支持的固定值。
