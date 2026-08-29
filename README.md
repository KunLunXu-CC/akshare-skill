# OpenClaw AkShare 技能

通过 [AkShare](https://akshare.akfamily.xyz/) 获取中国金融市场数据的 OpenClaw 技能。

## 功能概览

本技能支持以下实时与历史数据：

- A 股：上海、深圳和北京证券交易所行情
- 港股：香港交易所行情
- 美股：美国市场行情
- 期货：商品期货和股指期货
- 基金：开放式基金和 ETF
- 宏观经济指标：国内生产总值、居民消费价格指数、采购经理指数等

## 安装

### 环境要求

- Python 3.7 或更高版本
- OpenClaw 框架

### 安装 AkShare

```bash
pip install akshare
```

也可以运行仓库中的安装脚本：

```bash
bash scripts/install_akshare.sh
```

### 安装技能

将本仓库复制到 OpenClaw 工作区的技能目录：

```bash
cp -r openclaw-akshare-skill /path/to/openclaw/workspace/skills/akshare
```

## 快速开始

### 获取 A 股实时行情

```python
import akshare as ak

# 获取全部 A 股实时行情
df = ak.stock_zh_a_spot_em()
print(df.head())
```

### 获取股票历史行情

```python
# 获取指定股票的日线历史行情
df = ak.stock_zh_a_hist(
    symbol="000001",
    period="daily",
    start_date="20240101",
    end_date="20241231",
    adjust="qfq",  # 前复权
)
print(df.tail())
```

## 主要能力

- 股票：A 股、港股、美股实时行情，以及日线、周线、月线历史行情
- 期货：商品期货实时行情和主要交易所历史行情
- 基金：开放式基金信息和历史净值走势
- 宏观经济：国内生产总值、居民消费价格指数、工业生产者出厂价格指数、采购经理指数等

## 常用参数

周期：`daily` 表示日线，`weekly` 表示周线，`monthly` 表示月线。

复权方式：`qfq` 表示前复权，`hfq` 表示后复权，`""` 表示不复权。

## 示例与文档

- `scripts/example_usage.py`：常用场景示例
- `scripts/test_basic.py`：基础功能测试
- `scripts/test_quick.py`：快速结构测试
- [技能说明](SKILL.md)
- [AkShare API 参考](references/akshare_api.md)
- [常用函数](references/common_functions.md)
- [AkShare 官方文档](https://akshare.akfamily.xyz/)

## 使用建议

1. AkShare 默认不缓存数据；需要时自行实现缓存。
2. 控制请求频率，避免触发数据源限流。
3. 接口通常返回 pandas `DataFrame`，便于进一步处理。
4. 网络或上游数据源可能异常，应增加必要的重试和错误处理。

## 许可证

本项目采用 MIT 许可证，详情见 [LICENSE](LICENSE)。许可证原文依法保留英文。

## 参与贡献

欢迎提交贡献，具体要求见 [CONTRIBUTING.md](CONTRIBUTING.md)。版本历史见 [CHANGELOG.md](CHANGELOG.md)。

## 致谢

- [AkShare](https://akshare.akfamily.xyz/)：底层中国金融数据接口库
- [OpenClaw](https://github.com/openclaw/openclaw)：AI 助手框架
