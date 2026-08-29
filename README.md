# AkShare 技能

基于 AkShare 逐步扩展金融数据能力。

## 安装

```bash
bash scripts/install_akshare.sh
```

脚本优先复用已有 AkShare；缺失时安装到 `.venv`。

## 查询

当前支持基金持仓收益：

```bash
python3 scripts/fund_holding_profit.py \
  --holding "270023,4.5071,11778.31" \
  --holding "000002,1.0000,2000"
```

能力入口见 [SKILL.md](SKILL.md)，基金口径见 [参考文档](references/fund_holding_profit.md)。

## 许可证

[MIT](LICENSE)
