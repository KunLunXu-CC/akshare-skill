#!/usr/bin/env bash

set -euo pipefail

# AkShare 安装脚本
# 在技能目录中创建并复用持久化虚拟环境

AKSHARE_SKILL_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
AKSHARE_VENV_PATH="${AKSHARE_SKILL_ROOT}/.venv"
AKSHARE_VENV_PYTHON="${AKSHARE_VENV_PATH}/bin/python"

echo "正在检查 AkShare 安装状态..."

# 检查 Python 是否可用
if ! command -v python3 >/dev/null 2>&1; then
    echo "错误：未找到 python3，请先安装 Python。"
    exit 1
fi

# 技能自己的虚拟环境优先，确保后续会话可以稳定复用
if [[ -x "${AKSHARE_VENV_PYTHON}" ]] \
    && "${AKSHARE_VENV_PYTHON}" -c "import akshare" >/dev/null 2>&1; then
    echo "检测到技能虚拟环境中的 AkShare，无需重复安装。"
    "${AKSHARE_VENV_PYTHON}" -c "import akshare; print(f'AkShare 版本：{akshare.__version__}')"
    exit 0
fi

# 系统 Python 已经可用时无需再创建虚拟环境
if python3 -c "import akshare" >/dev/null 2>&1; then
    echo "检测到当前 Python 环境中的 AkShare，无需重复安装。"
    python3 -c "import akshare; print(f'AkShare 版本：{akshare.__version__}')"
    exit 0
fi

# 未安装时创建或修复技能自己的虚拟环境，避免修改系统 Python
echo "未检测到 AkShare，正在准备技能虚拟环境：${AKSHARE_VENV_PATH}"
if ! python3 -m venv "${AKSHARE_VENV_PATH}"; then
    echo "错误：无法创建 Python 虚拟环境，请确认已安装 venv 模块。"
    exit 1
fi

if ! "${AKSHARE_VENV_PYTHON}" -m pip --version >/dev/null 2>&1; then
    echo "错误：技能虚拟环境中没有可用的 pip。"
    exit 1
fi

echo "开始在技能虚拟环境中安装 AkShare..."
"${AKSHARE_VENV_PYTHON}" -m pip install akshare

# 验证安装结果
"${AKSHARE_VENV_PYTHON}" -c "import akshare; print(f'AkShare 版本：{akshare.__version__}')"

echo "AkShare 安装成功，后续查询会自动复用该虚拟环境。"
