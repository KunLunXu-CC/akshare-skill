---
name: akshare
description: 安装并验证 AkShare Python 库。当用户需要准备 AkShare 运行环境、安装依赖或检查 AkShare 是否可用时使用；当前不提供金融数据查询和分析能力。
---

# AkShare 安装工具

本技能目前只负责安装和验证 AkShare，不包含行情查询、数据处理、缓存、分析或其他金融数据能力。

## 安装

执行仓库提供的安装脚本：

```bash
bash scripts/install_akshare.sh
```

安装脚本会：

1. 检查 `python3` 是否可用。
2. 检查 Python 的 pip 模块是否可用。
3. 安装 AkShare。
4. 导入 AkShare 并输出版本号，确认安装成功。

安装 Python 包会修改当前 Python 环境。执行前应确认用户允许在目标环境中安装依赖。

## 能力边界

当前仅维护安装逻辑。需要新增数据接口、命令行工具、缓存、测试或参考文档时，应按实际需求逐步扩展，不预先加入未使用的能力。
