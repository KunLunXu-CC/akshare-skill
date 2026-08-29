# AkShare 技能

基于 AkShare 逐步扩展金融数据能力。

## 安装

```bash
bash scripts/install_akshare.sh
```

脚本优先复用已有 AkShare；缺失时安装到 `.venv`。

## 能力

- 从截图中的持有金额和持有收益计算成本价、份额，并在平台支持时更新记忆。
- 从输入或记忆读取持仓，查询基金收益。

```bash
python3 scripts/fund_holding_profit.py \
  --holding "270023,4.5071,11778.31"
```

批量查询：

```bash
python3 scripts/fund_holding_profit.py \
  --holding "270023,4.5071,11778.31" \
  --holding "000002,1.0000,2000"
```

能力入口见 [SKILL.md](SKILL.md)，基金口径见 [参考文档](references/fund_holding_profit.md)。

## 许可证

[MIT](LICENSE)
