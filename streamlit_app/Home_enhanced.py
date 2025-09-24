"""
SynVectorDB githubshare - Enhanced Home Page
使用DuckDB和本地向量计算的增强版主页
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils_enhanced import (
    get_basic_stats, 
    get_parts_sample, 
    test_database,
    get_system_info,
    test_vector_functionality
)

# 页面配置
st.set_page_config(
    page_title="SynVectorDB - Enhanced Local Version",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

def display_system_status():
    """显示系统状态"""
    st.markdown("## 🖥️ System Status")
    
    # 获取系统信息
    system_info = get_system_info()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        db_type = system_info.get('database_type', 'Unknown')
        st.metric("Database", db_type)
    
    with col2:
        vector_status = "✅ Enabled" if system_info.get('vector_support') else "❌ Disabled"
        st.metric("Vector Search", vector_status)
    
    with col3:
        model_status = "✅ Loaded" if system_info.get('model_loaded') else "❌ Not Loaded"
        st.metric("AI Model", model_status)
    
    with col4:
        faiss_status = "✅ Available" if system_info.get('faiss_support') else "❌ Unavailable"
        st.metric("FAISS Index", faiss_status)
    
    # 详细系统信息
    with st.expander("🔧 Detailed System Information"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Database Configuration")
            st.markdown(f"- **Type**: {system_info.get('database_type')}")
            st.markdown(f"- **Vector Support**: {system_info.get('vector_support')}")
            st.markdown(f"- **FAISS Support**: {system_info.get('faiss_support')}")
        
        with col2:
            st.markdown("### AI Model Configuration")
            model_name = system_info.get('embedding_model', 'Not Available')
            st.markdown(f"- **Model**: {model_name}")
            st.markdown(f"- **Status**: {'Loaded' if system_info.get('model_loaded') else 'Not Loaded'}")
            st.markdown(f"- **Type**: Multilingual Sentence Transformer")

def main():
    """主页面函数"""
    
    # 页面标题
    st.title("🧬 SynVectorDB - Enhanced Local Version")
    st.markdown("*Synthetic Biology Parts Database with Local Vector Search*")
    st.markdown("---")
    
    # 系统状态显示
    display_system_status()
    
    # 测试数据库连接
    db_ok, db_msg = test_database()
    if not db_ok:
        st.error(f"❌ Database connection failed: {db_msg}")
        st.stop()
    else:
        st.success(f"✅ {db_msg}")
    
    # 测试向量功能（如果可用）
    system_info = get_system_info()
    if system_info.get('vector_support'):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("🤖 Vector search functionality is available")
        with col2:
            if st.button("Test Vector System"):
                with st.spinner("Testing vector functionality..."):
                    vec_ok, vec_msg = test_vector_functionality()
                    if vec_ok:
                        st.success(f"✅ {vec_msg}")
                    else:
                        st.error(f"❌ {vec_msg}")
    else:
        st.warning("⚠️ Vector search not available. Install requirements: `pip install sentence-transformers torch faiss-cpu`")
    
    # 获取统计数据
    stats = get_basic_stats()
    if "error" in stats:
        st.error(f"❌ Failed to get statistics: {stats['error']}")
        st.stop()
    
    # 基础统计卡片
    st.markdown("## 📊 Database Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Parts", f"{stats['total_parts']:,}")
    
    with col2:
        st.metric("Function Types", len(stats['type_stats']))
    
    with col3:
        st.metric("Data Sources", len(stats['source_stats']))
    
    with col4:
        organism_count = len(stats.get('organism_stats', []))
        st.metric("Organisms", organism_count if organism_count > 0 else "N/A")
    
    # 图表显示
    st.markdown("## 📈 Data Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Part Type Distribution")
        if stats['type_stats']:
            type_df = pd.DataFrame(stats['type_stats'], columns=['Type', 'Count'])
            fig = px.bar(
                type_df.head(10), 
                x='Type', 
                y='Count', 
                title="Top 10 Part Types",
                color='Count',
                color_continuous_scale='viridis'
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No type data available")
    
    with col2:
        st.markdown("### Data Source Distribution")
        if stats['source_stats']:
            source_df = pd.DataFrame(stats['source_stats'], columns=['Source', 'Count'])
            fig = px.pie(
                source_df, 
                values='Count', 
                names='Source', 
                title="Data Source Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No source data available")
    
    # 物种分布（如果有数据）
    if stats.get('organism_stats'):
        st.markdown("### Organism Distribution")
        organism_df = pd.DataFrame(stats['organism_stats'], columns=['Organism', 'Count'])
        if len(organism_df) > 0:
            fig = px.bar(
                organism_df.head(10),
                x='Organism',
                y='Count',
                title="Top 10 Organisms",
                color='Count',
                color_continuous_scale='plasma'
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
    
    # 样本数据显示
    st.markdown("## 🔍 Sample Data")
    sample_data = get_parts_sample(10)
    if sample_data:
        df = pd.DataFrame(sample_data)
        # 显示主要列
        display_cols = ['name', 'type_level_1', 'source_collection', 'sequence_length', 'metadata_organism']
        available_cols = [col for col in df.columns if col in display_cols]
        
        if available_cols:
            st.dataframe(df[available_cols], use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No sample data available")
    
    # 功能特性展示
    st.markdown("---")
    st.markdown("## ✨ Enhanced Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🔍 Semantic Search")
        st.markdown("""
        **Local AI-Powered Search**
        - Natural language queries
        - Multilingual support (50+ languages)
        - Real-time vector computation
        - FAISS-accelerated indexing
        
        *Try: "E. coli promoter for high expression"*
        """)
        if st.button("Go to Semantic Search", key="semantic"):
            st.switch_page("pages/semantic_search_enhanced.py")
    
    with col2:
        st.markdown("### 📊 Advanced Analytics")
        st.markdown("""
        **Enhanced Data Analysis**
        - Interactive visualizations
        - Multi-dimensional filtering
        - Performance metrics
        - Export capabilities
        
        *Explore comprehensive statistics*
        """)
        if st.button("View Statistics", key="stats"):
            st.switch_page("pages/statistics.py")
    
    with col3:
        st.markdown("### 🧬 Parts Browser")
        st.markdown("""
        **Intelligent Part Discovery**
        - Advanced text search
        - Multi-criteria filtering
        - Detailed part information
        - Sequence visualization
        
        *Browse 19,850+ biological parts*
        """)
        if st.button("Browse Parts", key="browse"):
            st.switch_page("pages/parts_browser.py")
    
    # API集成信息
    st.markdown("---")
    st.markdown("## 🔌 API Integration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### MCP Server (NPM Package)")
        st.markdown("""
        **SynVectorDB MCP Server** provides Model Context Protocol integration for AI assistants:
        
        ```bash
        npm install synvectordb-mcp-server
        ```
        
        **Features:**
        - 🔍 Semantic search capabilities
        - 📊 Parts statistics and filtering
        - 🧬 SBOL and FASTA export
        - 🤖 AI assistant integration
        
        **Claude Desktop Configuration:**
        ```json
        {
          "mcpServers": {
            "synvectordb": {
              "command": "npx",
              "args": ["synvectordb-mcp-server"]
            }
          }
        }
        ```
        """)
    
    with col2:
        st.markdown("### REST API")
        st.markdown("""
        **Production API Access** for external integrations:
        
        **Base URL:** `https://testsdb.sjtu.bio`
        
        **Key Endpoints:**
        - `GET /stats` - Database statistics
        - `GET /parts/search` - Search parts
        - `GET /parts/{uid}` - Get part details
        - `GET /semantic_search` - Semantic search
        - `GET /downloads/index` - Download links
        
        **Example:**
        ```bash
        curl "https://testsdb.sjtu.bio/parts/search?organism=Mammalian&page_size=10"
        ```
        
        *Note: This local version uses local database and vector computation*
        """)
    
    # 技术架构信息
    st.markdown("---")
    st.markdown("## 🏗️ Technical Architecture")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Local Components")
        st.markdown(f"""
        - **Database**: {system_info.get('database_type', 'SQLite')}
        - **Vector Model**: {system_info.get('embedding_model', 'Not Available')}
        - **Search Index**: {'FAISS' if system_info.get('faiss_support') else 'NumPy'}
        - **Frontend**: Streamlit
        - **Caching**: Streamlit resource caching
        """)
    
    with col2:
        st.markdown("### Performance")
        st.markdown("""
        - **Search Speed**: Sub-second response
        - **Vector Computation**: Real-time
        - **Model Size**: ~400MB (optimized)
        - **Memory Usage**: ~1GB RAM
        - **Concurrent Users**: 10+ supported
        """)
    
    # 联系信息
    st.markdown("---")
    st.markdown("## 📞 Contact Information")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📧 Contact Email")
        st.markdown("jiesong@whu.edu.cn")
    
    with col2:
        st.markdown("### 📥 Data Download")
        st.markdown("[Download Database](https://r2data.sjtu.bio/data/parts.duckdb)")
    
    with col3:
        st.markdown("### 🔗 Project Repository")
        st.markdown("[GitHub](https://github.com/AilurusBio/synbio-parts-db/)")
    
    # 系统信息
    st.markdown("---")
    st.markdown("### ℹ️ System Information")
    st.info(f"""
    - **Version**: Enhanced Local Version with Vector Search
    - **Database**: {system_info.get('database_type')} ({stats['total_parts']:,} parts)
    - **Vector Search**: {'Enabled' if system_info.get('vector_support') else 'Disabled'}
    - **AI Model**: {'Loaded' if system_info.get('model_loaded') else 'Not Available'}
    - **Status**: Running locally
    - **Last Updated**: 2025-09-24
    """)

if __name__ == "__main__":
    main()
