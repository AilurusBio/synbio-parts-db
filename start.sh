#!/bin/bash
# SynVectorDB 一键启动脚本

echo "🚀 SynVectorDB 启动脚本"
echo "========================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 未安装，请先安装pip3"
    exit 1
fi

# 进入应用目录
cd "$(dirname "$0")/streamlit_app"

echo "📦 检查依赖..."
# 安装依赖
pip3 install -r requirements.txt

echo "🔍 检查数据文件..."
# 检查数据文件
if [ ! -f "../data/parts.duckdb" ]; then
    echo "❌ 数据库文件不存在，请确保data目录包含必要文件"
    exit 1
fi

echo "✅ 准备就绪，启动Streamlit应用..."
echo "🌐 应用将在浏览器中打开: http://localhost:8501"
echo "⏹️ 按 Ctrl+C 停止应用"
echo ""

# 启动Streamlit
streamlit run Home.py --server.port 8501 --server.address localhost
