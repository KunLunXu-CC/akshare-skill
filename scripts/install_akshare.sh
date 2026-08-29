#!/bin/bash

# AkShare 安装脚本
# 安装 AkShare 及其依赖

echo "正在安装 AkShare..."

# 检查 pip 是否可用
if ! command -v pip3 &> /dev/null; then
    echo "错误：未找到 pip3，请先安装 Python 和 pip。"
    exit 1
fi

# 安装 AkShare
pip3 install akshare pandas numpy matplotlib

# 验证安装结果
python3 -c "import akshare; print(f'AkShare 版本：{akshare.__version__}')"

echo "AkShare 安装成功！"
echo ""
echo "快速测试："
python3 -c "import akshare as ak; print('正在测试 AkShare...'); df = ak.stock_zh_a_spot_em(); print(f'已加载 {len(df)} 只股票')"

echo ""
echo "更多信息："
echo "  - https://akshare.akfamily.xyz/"
echo "  - https://github.com/akfamily/akshare"
