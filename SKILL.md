---
name: akshare-skill
description: 使用 AkShare 获取和处理金融数据。用户说“提取持仓信息”或发送支付宝等基金截图时记录持仓，也支持从记忆读取持仓并查询收益，以及安装或验证运行环境。
---

# AkShare

## 能力

| 能力 | 用途 | 入口 |
| --- | --- | --- |
| 基金持仓记录 | 从截图或文字提取持仓，输出表格并在可用时更新记忆 | [使用说明](references/fund_holding_record.md) |
| 基金持仓收益 | 查询单只或多只基金的收益、收益率和当日收益 | [使用说明](references/fund_holding_profit.md) |
| 环境准备 | 安装或验证 AkShare | `bash scripts/install_akshare.sh` |

只读取当前任务对应的参考文档。未列出的能力表示尚未实现。

## 公共规则

- 优先调用能力自带脚本，不用网页数据替代执行结果。
- 查询脚本会自动复用 `.venv`。确认缺少 AkShare 后，先取得安装许可，再运行安装脚本并重试原任务。
- 脚本失败时说明原因，不得虚构结果。
