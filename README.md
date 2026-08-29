# AkShare 技能

这是一个最小化的 AkShare 安装技能。目前只保留 AkShare 的安装与导入验证逻辑，其他能力将在实际需要时逐步增加。

## 使用方法

```bash
bash scripts/install_akshare.sh
```

脚本会先检查 Python 和 AkShare。AkShare 已安装时直接输出版本号；未安装时再检查 pip、执行安装并验证导入。

## 当前范围

- 保留：AkShare 安装和导入验证。
- 暂不包含：数据查询、缓存、命令行查询工具、数据分析、示例和测试。

技能入口见 [SKILL.md](SKILL.md)，开发语言规范见 [Agent.md](Agent.md)。

## 许可证

本项目采用 MIT 许可证，详情见 [LICENSE](LICENSE)。
