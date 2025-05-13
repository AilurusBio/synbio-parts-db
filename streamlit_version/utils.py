import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import streamlit as st
import pandas as pd
import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager
from sentence_transformers import SentenceTransformer
import numpy as np
import lancedb
import pickle
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加项目根目录到系统路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# 全局缓存的SemanticSearch实例
_semantic_search_instance = None

# 获取全局缓存的SemanticSearch实例
@st.cache_resource
def get_semantic_search_instance():
    """
    获取全局缓存的SemanticSearch实例，确保整个应用程序中只使用一个实例
    """
    global _semantic_search_instance
    
    if _semantic_search_instance is None:
        logger.info("Creating new SemanticSearch instance (should only happen once)")
        # 延迟导入，避免循环导入
        from data.search_v2 import SemanticSearch
        _semantic_search_instance = SemanticSearch()
    
    return _semantic_search_instance

# 不再需要init_embeddings和get_embeddings_data函数
# 所有嵌入向量相关的操作都通过get_semantic_search_instance函数获取的实例完成

@contextmanager
def get_connection():
    """Create a database connection context manager"""
    conn = None
    try:
        db_path = Path("streamlit_version/data/parts.db")
        conn = sqlite3.connect(db_path)
        yield conn
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        yield None
    finally:
        if conn is not None:
            conn.close() 