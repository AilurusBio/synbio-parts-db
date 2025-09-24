@echo off
REM SynVectorDB 一键启动脚本 (Windows)

echo 🚀 SynVectorDB 启动脚本
echo ========================

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装，请先安装Python
    pause
    exit /b 1
)

REM 进入应用目录
cd /d "%~dp0streamlit_app"

echo 📦 检查依赖...
REM 安装依赖
pip install -r requirements.txt

echo 🔍 检查数据文件...
REM 检查数据文件
if not exist "..\data\parts.duckdb" (
    echo ❌ 数据库文件不存在，请确保data目录包含必要文件
    pause
    exit /b 1
)

echo ✅ 准备就绪，启动Streamlit应用...
echo 🌐 应用将在浏览器中打开: http://localhost:8501
echo ⏹️ 按 Ctrl+C 停止应用
echo.

REM 启动Streamlit
streamlit run Home.py --server.port 8501 --server.address localhost
pause
