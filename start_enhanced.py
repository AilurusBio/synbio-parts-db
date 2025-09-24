#!/usr/bin/env python3
"""
SynVectorDB Local Deployment - Enhanced Version Launcher
Start enhanced version with DuckDB and local vector search support
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start enhanced application"""
    
    # Set working directory
    current_dir = Path(__file__).parent
    streamlit_dir = current_dir / "streamlit_app"
    
    print("🧬 SynVectorDB Local Deployment - Enhanced Version")
    print("=" * 60)
    print("Features:")
    print("✅ DuckDB database integration")
    print("✅ Local vector search with sentence-transformers")
    print("✅ FAISS-accelerated similarity search")
    print("✅ Real-time vector computation")
    print("✅ Enhanced statistics and analytics")
    print("=" * 60)
    
    # Check dependencies
    try:
        import streamlit
        import duckdb
        import sentence_transformers
        import faiss
        print("✅ All dependencies available")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install: pip install -r requirements_enhanced.txt")
        sys.exit(1)
    
    # Check database
    db_path = current_dir / "data" / "parts.duckdb"
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        print("Please ensure the DuckDB database file exists")
        sys.exit(1)
    else:
        print(f"✅ Database found: {db_path}")
    
    # Check models
    model_dir = streamlit_dir / "models" / "models--sentence-transformers--all-MiniLM-L6-v2"
    if not model_dir.exists():
        print(f"❌ Vector model not found: {model_dir}")
        print("Please ensure the sentence-transformers model is available")
        sys.exit(1)
    else:
        print(f"✅ Vector model found: {model_dir}")
    
    print("=" * 60)
    print("🚀 Starting enhanced application...")
    print("📊 First startup may take a few minutes to build vector index")
    print("🌐 Access at: http://localhost:8501")
    print("=" * 60)
    
    # Start Streamlit application
    os.chdir(streamlit_dir)
    
    # Use enhanced Home page
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        "Home_enhanced.py",
        "--server.port", "8501",
        "--server.address", "localhost",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ])

if __name__ == "__main__":
    main()
