"""
SynVectorDB githubshare - Home Page
Refactored version, simplified functionality, focused on core display
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import get_basic_stats, get_parts_sample, test_database, get_database_info

# Page configuration
st.set_page_config(
    page_title="SynVectorDB - Synthetic Biology Parts Database",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main page function"""
    
    # Page title
    st.title("🧬 SynVectorDB - Synthetic Biology Parts Database")
    st.markdown("---")
    
    # Test database connection and show database info
    db_info = get_database_info()
    db_ok, db_msg = test_database()
    
    # Database status section
    st.markdown("## 🗄️ Database Status")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if db_ok:
            st.success(f"✅ {db_msg}")
        else:
            st.error(f"❌ {db_msg}")
    
    with col2:
        db_type = db_info.get("database_type", "Unknown")
        if db_type == "DuckDB":
            st.info(f"🦆 Database: {db_type}")
        elif db_type == "SQLite":
            st.info(f"🗃️ Database: {db_type}")
        else:
            st.warning(f"❓ Database: {db_type}")
    
    with col3:
        duckdb_status = "✅ Available" if db_info.get("duckdb_available") else "❌ Not Available"
        st.info(f"🦆 DuckDB Support: {duckdb_status}")
    
    # Check for cross-platform issues
    if db_info.get("cross_platform_issue"):
        st.error("🚨 **跨平台兼容性问题检测**")
        st.error("DuckDB数据库文件包含Windows路径，无法在Linux上使用。系统已自动切换到SQLite数据库。")
        st.info("💡 **解决方案**: 请使用在Linux系统上生成的DuckDB文件，或继续使用SQLite数据库。")
    
    if not db_ok:
        st.stop()
    
    # Get statistics data
    stats = get_basic_stats()
    if "error" in stats:
        st.error(f"❌ Failed to get statistics: {stats['error']}")
        st.stop()
    
    # Basic statistics cards
    st.markdown("## 📊 Database Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Parts", f"{stats['total_parts']:,}")
    
    with col2:
        st.metric("Function Types", len(stats['type_stats']))
    
    with col3:
        st.metric("Data Sources", len(stats['source_stats']))
    
    with col4:
        st.metric("Status", "Running")
    
    # Chart display
    st.markdown("## 📈 Data Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Part Type Distribution")
        if stats['type_stats']:
            type_df = pd.DataFrame(stats['type_stats'], columns=['Type', 'Count'])
            fig = px.bar(type_df.head(10), x='Type', y='Count', 
                        title="Top 10 Part Types")
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No type data available")
    
    with col2:
        st.markdown("### Data Source Distribution")
        if stats['source_stats']:
            source_df = pd.DataFrame(stats['source_stats'], columns=['Source', 'Count'])
            fig = px.pie(source_df, values='Count', names='Source', 
                        title="Data Source Distribution")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No source data available")
    
    # Sample data display
    st.markdown("## 🔍 Sample Data")
    sample_data = get_parts_sample(10)
    if sample_data:
        df = pd.DataFrame(sample_data)
        # Only display main columns
        display_cols = ['name', 'type_level_1', 'source_collection', 'sequence_length']
        available_cols = [col for col in display_cols if col in df.columns]
        st.dataframe(df[available_cols], use_container_width=True)
    else:
        st.info("No sample data available")
    
    # API Integration
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
        **Direct API Access** for custom integrations:
        
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
        """)
    
    # Footer information
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
    
    # System information
    st.markdown("---")
    st.markdown("### ℹ️ System Information")
    st.info(f"""
    - **Version**: githubshare demo version
    - **Database**: SQLite ({stats['total_parts']:,} parts)
    - **Status**: Running normally
    - **Last Updated**: 2025-09-24
    """)

if __name__ == "__main__":
    main()
