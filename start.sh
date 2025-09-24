#!/bin/bash
# SynVectorDB One-Click Startup Script

echo "🚀 SynVectorDB Startup Script"
echo "========================"

# Check Python environment
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not installed, please install Python3 first"
    exit 1
fi

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not installed, please install pip3 first"
    exit 1
fi

# Enter application directory
cd "$(dirname "$0")/streamlit_app"

echo "📦 Checking dependencies..."
# Install dependencies
pip3 install -r requirements.txt

echo "🔍 Checking data files..."
# Check data files
if [ ! -f "../data/parts.duckdb" ]; then
    echo "❌ Database file not found, please ensure data directory contains necessary files"
    exit 1
fi

echo "✅ Ready, starting Streamlit application..."
echo "🌐 Application will open in browser: http://localhost:8501"
echo "⏹️ Press Ctrl+C to stop application"
echo ""

# Start Streamlit
streamlit run Home.py --server.port 8501 --server.address localhost
