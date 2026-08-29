#!/usr/bin/env bash

set -euo pipefail

# AkShare 安装脚本
# 仅安装并验证 AkShare

echo "正在安装 AkShare..."

# 检查 Python 是否可用
if ! command -v python3 >/dev/null 2>&1; then
    echo "错误：未找到 python3，请先安装 Python。"
    exit 1
fi

# 检查 pip 是否可用
if ! python3 -m pip --version >/dev/null 2>&1; then
    echo "错误：当前 Python 环境未安装 pip。"
    exit 1
fi

# 安装 AkShare
python3 -m pip install akshare

# 验证安装结果
python3 -c "import akshare; print(f'AkShare 版本：{akshare.__version__}')"

echo "AkShare 安装成功！"
