# AkShare 技能

这是一个逐步扩展的 AkShare 技能。目前支持安装 AkShare，以及根据基金最新净值、持仓成本价和份额查询持仓收益。

## 使用方法

```bash
bash scripts/install_akshare.sh
```

脚本会先检查 Python 和 AkShare。AkShare 已安装时直接输出版本号；未安装时再检查 pip、执行安装并验证导入。

## 当前范围

- AkShare 安装和导入验证。
- 按开放式基金代码或名称查询最新净值。
- 根据每份持仓成本价和持有份额计算持有成本、当前市值、持仓收益、收益率和当日收益。

## 基金查询

```bash
python3 scripts/fund_holding_profit.py 270023 \
  --cost-price 4.5071 \
  --shares 11778.31
```

详细口径见 [基金持仓收益参考](references/fund_holding_profit.md)。

技能入口见 [SKILL.md](SKILL.md)，开发语言规范见 [Agent.md](Agent.md)。

## 许可证

本项目采用 MIT 许可证，详情见 [LICENSE](LICENSE)。
