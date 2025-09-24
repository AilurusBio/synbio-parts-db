"""
SynVectorDB githubshare - Enhanced Parts Browser Page
使用DuckDB和增强搜索功能的部件浏览器
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils_enhanced import (
    search_parts, 
    get_part_details, 
    get_available_filters,
    get_basic_stats
)
import time

# 页面配置
st.set_page_config(
    page_title="Parts Browser - SynVectorDB",
    page_icon="🧬",
    layout="wide"
)

def display_search_results(results, query_time, query_info):
    """显示搜索结果"""
    if not results:
        st.info("🔍 No parts found matching your criteria. Try adjusting your search parameters.")
        return
    
    # 结果概览
    st.success(f"✅ Found {len(results)} parts in {query_time:.2f} seconds")
    
    # 查询信息
    if query_info:
        with st.expander("🔍 Search Details"):
            col1, col2 = st.columns(2)
            with col1:
                if query_info.get('query'):
                    st.markdown(f"**Text Query**: {query_info['query']}")
                if query_info.get('type_filter'):
                    st.markdown(f"**Type Filter**: {query_info['type_filter']}")
            with col2:
                if query_info.get('source_filter'):
                    st.markdown(f"**Source Filter**: {query_info['source_filter']}")
                if query_info.get('organism_filter'):
                    st.markdown(f"**Organism Filter**: {query_info['organism_filter']}")
    
    # 创建结果DataFrame
    df = pd.DataFrame(results)
    
    # 结果统计
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Results", len(results))
    with col2:
        unique_types = df['type_level_1'].nunique() if 'type_level_1' in df.columns else 0
        st.metric("Unique Types", unique_types)
    with col3:
        unique_sources = df['source_collection'].nunique() if 'source_collection' in df.columns else 0
        st.metric("Unique Sources", unique_sources)
    with col4:
        avg_length = df['sequence_length'].mean() if 'sequence_length' in df.columns else 0
        st.metric("Avg Seq Length", f"{avg_length:.0f}" if avg_length > 0 else "N/A")
    
    # 结果分析图表
    if len(results) > 1:
        st.markdown("### 📊 Results Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 类型分布
            if 'type_level_1' in df.columns:
                type_counts = df['type_level_1'].value_counts()
                if len(type_counts) > 0:
                    fig = px.pie(
                        values=type_counts.values,
                        names=type_counts.index,
                        title="Part Type Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 序列长度分布
            if 'sequence_length' in df.columns and df['sequence_length'].notna().sum() > 0:
                fig = px.histogram(
                    df,
                    x='sequence_length',
                    nbins=20,
                    title="Sequence Length Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # 结果表格
    st.markdown("### 📋 Search Results")
    
    # 选择显示的列
    display_columns = [
        'name', 'type_level_1', 'type_level_2', 'source_collection', 
        'sequence_length', 'metadata_organism'
    ]
    available_columns = [col for col in display_columns if col in df.columns and col is not None]
    
    if available_columns:
        # 格式化数据
        display_df = df[available_columns].copy()
        
        # 重命名列以便显示
        column_names = {
            'name': 'Name',
            'type_level_1': 'Type',
            'type_level_2': 'Subtype',
            'source_collection': 'Source',
            'sequence_length': 'Length',
            'metadata_organism': 'Organism'
        }
        
        display_df = display_df.rename(columns=column_names)
        
        # 显示表格
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.dataframe(df, use_container_width=True)
    
    # 详细结果展开
    st.markdown("### 🔍 Detailed Results")
    
    for i, result in enumerate(results[:20]):  # 限制显示前20个结果
        with st.expander(f"#{i+1} - {result.get('name', 'Unknown')}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Name:** {result.get('name', 'N/A')}")
                st.markdown(f"**Description:** {result.get('description', 'N/A')}")
                st.markdown(f"**UID:** `{result.get('uid', 'N/A')}`")
            
            with col2:
                st.markdown(f"**Type:** {result.get('type_level_1', 'N/A')}")
                st.markdown(f"**Subtype:** {result.get('type_level_2', 'N/A')}")
                st.markdown(f"**Source:** {result.get('source_collection', 'N/A')}")
                st.markdown(f"**Organism:** {result.get('metadata_organism', 'N/A')}")
                st.markdown(f"**Sequence Length:** {result.get('sequence_length', 'N/A')}")
            
            # 获取更多详情按钮
            if st.button(f"View Full Details", key=f"details_{i}"):
                details = get_part_details(result.get('uid'))
                if details:
                    st.json(details)

def main():
    """主页面函数"""
    
    # 页面标题
    st.title("🧬 Parts Browser")
    st.markdown("Search and explore biological parts with advanced filtering")
    st.markdown("---")
    
    # 获取可用的筛选选项
    filters = get_available_filters()
    
    # 搜索界面
    st.markdown("## 🔍 Search Parameters")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 文本搜索
        query = st.text_input(
            "Text Search",
            placeholder="Search in names and descriptions...",
            help="Enter keywords to search in part names and descriptions"
        )
    
    with col2:
        # 结果限制
        limit = st.selectbox("Max Results", [10, 20, 50, 100], index=1)
    
    # 筛选选项
    st.markdown("### 🎯 Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 类型筛选
        type_options = ["All Types"] + filters.get('types', [])
        type_filter = st.selectbox("Part Type", type_options)
        if type_filter == "All Types":
            type_filter = ""
    
    with col2:
        # 来源筛选
        source_options = ["All Sources"] + filters.get('sources', [])
        source_filter = st.selectbox("Data Source", source_options)
        if source_filter == "All Sources":
            source_filter = ""
    
    with col3:
        # 物种筛选
        organism_options = ["All Organisms"] + filters.get('organisms', [])
        organism_filter = st.selectbox("Organism", organism_options)
        if organism_filter == "All Organisms":
            organism_filter = ""
    
    # 高级选项
    with st.expander("🔧 Advanced Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Search Options**")
            case_sensitive = st.checkbox("Case Sensitive Search", value=False)
            exact_match = st.checkbox("Exact Match Only", value=False)
        
        with col2:
            st.markdown("**Display Options**")
            show_charts = st.checkbox("Show Result Charts", value=True)
            show_details = st.checkbox("Show Detailed View", value=True)
    
    # 搜索按钮
    search_clicked = st.button("🔍 Search Parts", type="primary", use_container_width=True)
    
    # 执行搜索
    if search_clicked:
        # 准备查询信息
        query_info = {
            'query': query,
            'type_filter': type_filter,
            'source_filter': source_filter,
            'organism_filter': organism_filter
        }
        
        with st.spinner("Searching parts..."):
            start_time = time.time()
            results = search_parts(
                query=query,
                type_filter=type_filter,
                source_filter=source_filter,
                organism_filter=organism_filter,
                limit=limit
            )
            query_time = time.time() - start_time
            
            # 显示结果
            display_search_results(results, query_time, query_info)
    
    # 快速搜索示例
    st.markdown("---")
    st.markdown("## 💡 Quick Search Examples")
    
    examples = [
        {"name": "Promoters", "query": "promoter", "type": "", "desc": "Find all promoter sequences"},
        {"name": "E. coli Parts", "query": "", "organism": "E. coli", "desc": "Parts specific to E. coli"},
        {"name": "Fluorescent Proteins", "query": "fluorescent protein", "type": "", "desc": "Reporter proteins"},
        {"name": "iGEM Parts", "query": "", "source": "iGEM", "desc": "Parts from iGEM registry"},
        {"name": "Coding Sequences", "query": "", "type": "CDS", "desc": "Protein coding sequences"},
        {"name": "Mammalian Systems", "query": "", "organism": "Mammalian", "desc": "Parts for mammalian cells"}
    ]
    
    cols = st.columns(3)
    for i, example in enumerate(examples):
        with cols[i % 3]:
            if st.button(f"🔍 {example['name']}", key=f"example_{i}"):
                # 设置搜索参数
                st.session_state.example_search = {
                    'query': example.get('query', ''),
                    'type_filter': example.get('type', ''),
                    'source_filter': example.get('source', ''),
                    'organism_filter': example.get('organism', '')
                }
                st.rerun()
    
    # 如果有示例搜索，执行它
    if 'example_search' in st.session_state:
        example = st.session_state.example_search
        del st.session_state.example_search
        
        with st.spinner("Running example search..."):
            start_time = time.time()
            results = search_parts(
                query=example['query'],
                type_filter=example['type_filter'],
                source_filter=example['source_filter'],
                organism_filter=example['organism_filter'],
                limit=20
            )
            query_time = time.time() - start_time
            
            display_search_results(results, query_time, example)
    
    # 数据库统计
    st.markdown("---")
    st.markdown("## 📊 Database Statistics")
    
    stats = get_basic_stats()
    if "error" not in stats:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### Part Types")
            if stats.get('type_stats'):
                type_df = pd.DataFrame(stats['type_stats'], columns=['Type', 'Count'])
                for _, row in type_df.head(5).iterrows():
                    st.markdown(f"- **{row['Type']}**: {row['Count']:,}")
        
        with col2:
            st.markdown("### Data Sources")
            if stats.get('source_stats'):
                source_df = pd.DataFrame(stats['source_stats'], columns=['Source', 'Count'])
                for _, row in source_df.head(5).iterrows():
                    st.markdown(f"- **{row['Source']}**: {row['Count']:,}")
        
        with col3:
            st.markdown("### Organisms")
            if stats.get('organism_stats'):
                organism_df = pd.DataFrame(stats['organism_stats'], columns=['Organism', 'Count'])
                for _, row in organism_df.head(5).iterrows():
                    st.markdown(f"- **{row['Organism']}**: {row['Count']:,}")
    
    # 使用说明
    with st.expander("📖 How to Use Parts Browser"):
        st.markdown("""
        ### 🔍 Search Tips
        
        1. **Text Search**: Enter keywords that appear in part names or descriptions
        2. **Filters**: Use dropdown filters to narrow down results by type, source, or organism
        3. **Combine Filters**: Use multiple filters together for precise searches
        4. **Result Limit**: Adjust the maximum number of results to display
        
        ### 📊 Understanding Results
        
        - **Name**: Official name of the biological part
        - **Type**: Primary classification (e.g., Promoter, CDS, Terminator)
        - **Subtype**: Secondary classification for more specific categorization
        - **Source**: Database or collection where the part originates
        - **Length**: Sequence length in base pairs
        - **Organism**: Target organism or source organism
        
        ### 🎯 Search Strategies
        
        - **Broad Search**: Use general terms like "promoter" or "protein"
        - **Specific Search**: Combine text with filters for precise results
        - **Organism-Specific**: Filter by organism for system-specific parts
        - **Source-Specific**: Filter by source for parts from specific databases
        """)

if __name__ == "__main__":
    main()
