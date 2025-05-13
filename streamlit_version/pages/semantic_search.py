# -*- coding: utf-8 -*-
# Title: Semantic Search

import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import json
import time
import logging
from contextlib import contextmanager
import sqlite3

# Add main directory to system path
sys.path.append(str(Path(__file__).parent.parent))

# 从utils导入共享功能
from utils import get_connection

# 从data目录导入搜索功能
# 使用utils中的全局缓存函数
from utils import get_semantic_search_instance

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 使用全局缓存的SemanticSearch实例
@st.cache_resource
def get_searcher():
    """
    获取全局缓存的SemanticSearch实例
    """
    try:
        logger.info("Getting cached SemanticSearch instance")
        return get_semantic_search_instance()
    except Exception as e:
        st.error(f"Error initializing search: {str(e)}")
        logger.error(f"Error initializing search: {str(e)}", exc_info=True)
        raise

def display_search_results(results):
    """Display search results in a formatted way"""
    if not results["results"]:
        st.warning("No results found.")
        return
    
    # 显示优化信息（如果启用了优化）
    if results.get("optimize") and "optimization" in results:
        opt = results["optimization"]
        if opt["status"] == "success":
            with st.expander("Query Optimization Details", expanded=True):
                st.markdown(f"""
                - **Original Query**: {opt['original_query']}
                - **Optimized Query**: {opt['optimized_query']}
                - **Explanation**: {opt['explanation']}
                """)
                if opt.get("key_terms"):
                    st.markdown("**Key Terms**: " + ", ".join(opt["key_terms"]))
    
    # 显示搜索结果
    for idx, result in enumerate(results["results"], 1):
        with st.expander(f"{idx}. {result['name']} (Similarity: {result['similarity']:.2f})", expanded=True):
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.markdown("**Basic Information**")
                st.markdown(f"""
                - **Type**: {result['type']}
                - **Source**: {result['source_collection']}
                - **Source Name**: {result['source_name']}
                """)
            
            with col2:
                st.markdown("**Description**")
                st.markdown(result['description'])

def main():
    # 设置页面配置，自定义侧边栏显示的名称
    st.set_page_config(
        page_title="Semantic Search",
        page_icon="🔍",
        layout="wide"
    )
    
    # 添加强制使用浅色主题的CSS样式
    st.markdown("""
    <style>
    /* 强制使用浅色主题，覆盖Streamlit的默认主题切换 */
    html, body, [class*="css"] {
        color: #262730 !important;
        background-color: #FFFFFF !important;
    }
    
    /* 固定浅色主题 */
    .stApp {
        background-color: #FFFFFF !important;
    }
    
    /* 确保所有文本使用深色 */
    .stMarkdown, p, h1, h2, h3, h4, h5, h6, span, div {
        color: #262730 !important;
    }
    
    /* 确保所有卡片使用浅色背景 */
    .stTabs [data-baseweb="tab-panel"], div.stBlock {
        background-color: #F0F2F6 !important;
    }
    
    /* 确保侧边栏使用浅色背景 */
    .css-1d391kg, .css-1lcbmhc, .css-12oz5g7 {
        background-color: #F0F2F6 !important;
    }
    
    /* 确保按钮和输入框使用浅色主题 */
    .stButton>button, .stTextInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #FFFFFF !important;
        color: #262730 !important;
        border-color: #CCC !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("Semantic Search")
    st.markdown("""
    This page provides semantic search functionality for biological parts using advanced language models.
    You can search using natural language queries, and the system will find the most relevant parts.
    """)
    
    # 获取搜索器实例
    searcher = get_searcher()
    
    # 创建搜索表单
    with st.form("search_form"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            query = st.text_input("Search Query", placeholder="Enter your search query...")
        
        with col2:
            top_k = st.number_input("Number of Results", min_value=1, max_value=50, value=10)
        
        col3, col4 = st.columns(2)
        with col3:
            optimize = st.checkbox("Optimize Query", value=True, 
                                 help="Use AI to optimize and enhance your search query")
        
        with col4:
            types = st.multiselect(
                "Filter by Type",
                options=["promoter", "terminator", "RBS", "CDS", "plasmid"],
                default=[]
            )
        
        source_collections = st.multiselect(
            "Filter by Source",
            options=["igem", "lab", "addgene", "snapgene", "yunzhou"],
            default=[]
        )
        
        submitted = st.form_submit_button("Search")
    
    if submitted and query:
        with st.spinner("Searching..."):
            # 添加一个随机参数，确保每次查询都是唯一的，防止Streamlit缓存结果
            query_time = time.time()
            search_id = f"{query}_{query_time}"
            st.session_state['last_search_id'] = search_id
            
            start_time = time.time()
            results = searcher.search(
                query=query,
                top_k=top_k,
                optimize=optimize,
                types=types if types else None,
                source_collections=source_collections if source_collections else None
            )
            
            # 将结果存储在session_state中
            st.session_state['last_results'] = results
            st.session_state['search_time'] = time.time() - start_time
            
            st.success(f"Search completed in {st.session_state['search_time']:.2f} seconds")
            display_search_results(results)
    
    # 添加使用说明
    with st.expander("How to Use", expanded=False):
        st.markdown("""
        ### Search Tips
        
        1. **Natural Language Queries**
           - Use natural language to describe what you're looking for
           - Example: "Find strong constitutive promoters for E. coli"
        
        2. **Query Optimization**
           - Enable "Optimize Query" to let AI enhance your search
           - The system will analyze your query and suggest improvements
        
        3. **Filters**
           - Use type filters to narrow down to specific part types
           - Use source filters to focus on specific collections
        
        4. **Results**
           - Results are ranked by semantic similarity
           - Each result shows similarity score and detailed information
        """)

if __name__ == "__main__":
    main() 