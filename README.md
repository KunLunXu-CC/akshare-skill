# AkShare 技能

这是一个逐步扩展的 AkShare 技能。目前支持安装 AkShare，以及根据基金盘中估值或盘后净值、持仓成本价和份额查询持仓收益。

## 使用方法

```bash
bash scripts/install_akshare.sh
```

脚本会先检查 Python 和 AkShare。它会优先复用技能目录中的持久化 `.venv`；仅在首次缺少依赖时创建环境并安装。基金查询脚本会自动切换到该环境，新会话不需要重新激活或安装。

## 当前范围

- AkShare 安装和导入验证。
- 按开放式基金代码或名称查询盘中估值或最新公布净值。
- 根据每份持仓成本价和持有份额计算持有成本、当前市值、持仓收益、收益率和当日收益。
- 支持多只基金批量查询并输出精简的 Markdown 表格及合计摘要。

## 基金查询

```bash
python3 scripts/fund_holding_profit.py 270023 \
  --cost-price 4.5071 \
  --shares 11778.31

python3 scripts/fund_holding_profit.py \
  --holding "270023,4.5071,11778.31" \
  --holding "000002,1.0000,2000"
```

详细口径见 [基金持仓收益参考](references/fund_holding_profit.md)。

技能入口见 [SKILL.md](SKILL.md)，开发语言规范见 [Agent.md](Agent.md)。

## 许可证

本项目采用 MIT 许可证，详情见 [LICENSE](LICENSE)。
