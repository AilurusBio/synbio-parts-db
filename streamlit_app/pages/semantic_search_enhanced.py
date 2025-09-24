"""
SynVectorDB githubshare - Enhanced Semantic Search Page
使用本地向量计算的语义搜索功能
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils_enhanced import (
    semantic_search_local, 
    get_part_details, 
    test_vector_functionality,
    get_system_info,
    get_available_filters
)
import time

# 页面配置
st.set_page_config(
    page_title="Semantic Search - SynVectorDB",
    page_icon="🔍",
    layout="wide"
)

def display_search_results(results, query_time):
    """显示搜索结果"""
    if not results:
        st.info("🔍 No results found. Try different keywords or check your query.")
        return
    
    st.success(f"✅ Found {len(results)} results in {query_time:.2f} seconds")
    
    # 创建结果DataFrame
    df = pd.DataFrame(results)
    
    # 显示结果概览
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Results Found", len(results))
    with col2:
        avg_score = df['similarity_score'].mean() if 'similarity_score' in df.columns else 0
        st.metric("Avg Similarity", f"{avg_score:.3f}")
    with col3:
        st.metric("Query Time", f"{query_time:.2f}s")
    
    # 相似度分布图
    if 'similarity_score' in df.columns:
        st.markdown("### 📊 Similarity Score Distribution")
        fig = px.histogram(
            df, 
            x='similarity_score', 
            nbins=20,
            title="Distribution of Similarity Scores",
            labels={'similarity_score': 'Similarity Score', 'count': 'Number of Results'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 详细结果表格
    st.markdown("### 🔍 Search Results")
    
    # 选择显示的列
    display_columns = ['rank', 'name', 'type_level_1', 'source_collection', 'similarity_score']
    available_columns = [col for col in display_columns if col in df.columns]
    
    if available_columns:
        # 格式化相似度分数
        if 'similarity_score' in df.columns:
            df['similarity_score'] = df['similarity_score'].round(4)
        
        # 显示表格
        st.dataframe(
            df[available_columns],
            use_container_width=True,
            hide_index=True
        )
    
    # 详细结果展开
    st.markdown("### 📋 Detailed Results")
    
    for i, result in enumerate(results[:10]):  # 限制显示前10个结果
        with st.expander(f"#{result.get('rank', i+1)} - {result.get('name', 'Unknown')} (Score: {result.get('similarity_score', 0):.4f})"):
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
                st.markdown(f"**Similarity:** {result.get('similarity_score', 0):.4f}")
            
            # 获取更多详情按钮
            if st.button(f"View Full Details", key=f"details_{i}"):
                details = get_part_details(result.get('uid'))
                if details:
                    st.json(details)

def display_example_queries():
    """显示示例查询"""
    st.markdown("### 💡 Example Queries")
    
    examples = [
        {
            "query": "E. coli promoter",
            "description": "Find promoters specific to E. coli",
            "category": "Organism-specific"
        },
        {
            "query": "fluorescent protein reporter",
            "description": "Search for fluorescent proteins used as reporters",
            "category": "Functional"
        },
        {
            "query": "CRISPR Cas9 system",
            "description": "Find CRISPR-Cas9 related components",
            "category": "Technology"
        },
        {
            "query": "mammalian expression vector",
            "description": "Search for vectors designed for mammalian cells",
            "category": "Expression System"
        },
        {
            "query": "antibiotic resistance marker",
            "description": "Find selection markers for antibiotic resistance",
            "category": "Selection"
        },
        {
            "query": "inducible promoter system",
            "description": "Search for inducible regulatory elements",
            "category": "Regulation"
        }
    ]
    
    # 按类别组织示例
    categories = {}
    for example in examples:
        cat = example["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(example)
    
    for category, cat_examples in categories.items():
        with st.expander(f"📂 {category}"):
            for example in cat_examples:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{example['query']}**")
                    st.markdown(f"*{example['description']}*")
                with col2:
                    if st.button("Try This", key=f"example_{example['query']}"):
                        st.session_state.example_query = example['query']
                        st.rerun()

def main():
    """主页面函数"""
    
    # 页面标题
    st.title("🔍 Semantic Search")
    st.markdown("---")
    
    # 系统状态检查
    system_info = get_system_info()
    
    # 显示系统状态
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        status = "✅ Available" if system_info.get('vector_support') else "❌ Unavailable"
        st.metric("Vector Support", status)
    
    with col2:
        db_type = system_info.get('database_type', 'Unknown')
        st.metric("Database", db_type)
    
    with col3:
        model_status = "✅ Loaded" if system_info.get('model_loaded') else "❌ Not Loaded"
        st.metric("AI Model", model_status)
    
    with col4:
        faiss_status = "✅ Available" if system_info.get('faiss_support') else "❌ Unavailable"
        st.metric("FAISS Index", faiss_status)
    
    # 如果向量支持不可用，显示警告
    if not system_info.get('vector_support'):
        st.error("""
        ⚠️ **Vector Support Unavailable**
        
        Semantic search requires additional dependencies. Please install:
        ```bash
        pip install sentence-transformers torch faiss-cpu
        ```
        """)
        st.stop()
    
    # 测试向量功能
    if st.button("🧪 Test Vector Functionality"):
        with st.spinner("Testing vector functionality..."):
            success, message = test_vector_functionality()
            if success:
                st.success(f"✅ {message}")
            else:
                st.error(f"❌ {message}")
    
    st.markdown("---")
    
    # 搜索界面
    st.markdown("## 🔍 Semantic Search")
    st.markdown("Enter natural language queries to find relevant biological parts using AI-powered semantic similarity.")
    
    # 检查是否有示例查询
    if 'example_query' in st.session_state:
        default_query = st.session_state.example_query
        del st.session_state.example_query
    else:
        default_query = ""
    
    # 搜索输入
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(
            "Search Query",
            value=default_query,
            placeholder="e.g., 'E. coli promoter for protein expression'",
            help="Enter a natural language description of what you're looking for"
        )
    
    with col2:
        top_k = st.selectbox("Max Results", [5, 10, 20, 50], index=1)
    
    # 高级选项
    with st.expander("🔧 Advanced Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Search Parameters**")
            min_similarity = st.slider("Minimum Similarity Score", 0.0, 1.0, 0.1, 0.05)
            show_scores = st.checkbox("Show Similarity Scores", value=True)
        
        with col2:
            st.markdown("**Display Options**")
            show_distribution = st.checkbox("Show Score Distribution", value=True)
            show_details = st.checkbox("Show Detailed Results", value=True)
    
    # 搜索按钮
    search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)
    
    # 执行搜索
    if search_clicked and query.strip():
        with st.spinner(f"Searching for '{query}'..."):
            start_time = time.time()
            results = semantic_search_local(query, top_k=top_k)
            query_time = time.time() - start_time
            
            # 过滤结果（如果设置了最小相似度）
            if min_similarity > 0:
                results = [r for r in results if r.get('similarity_score', 0) >= min_similarity]
            
            # 显示结果
            if results:
                display_search_results(results, query_time)
            else:
                st.warning(f"No results found for '{query}' with similarity >= {min_similarity}")
    
    elif search_clicked and not query.strip():
        st.warning("Please enter a search query")
    
    # 显示示例查询
    display_example_queries()
    
    # 技术信息
    st.markdown("---")
    st.markdown("## ℹ️ Technical Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🤖 AI Model")
        st.markdown(f"""
        - **Model**: {system_info.get('embedding_model', 'N/A')}
        - **Type**: Multilingual sentence transformer
        - **Dimensions**: 384 (optimized for speed)
        - **Languages**: 50+ languages supported
        """)
    
    with col2:
        st.markdown("### ⚡ Performance")
        st.markdown(f"""
        - **Vector Index**: {'FAISS' if system_info.get('faiss_support') else 'NumPy'}
        - **Search Method**: Cosine similarity
        - **Indexing**: Real-time computation
        - **Caching**: Streamlit resource caching
        """)
    
    # 使用说明
    with st.expander("📖 How to Use Semantic Search"):
        st.markdown("""
        ### 🎯 Search Tips
        
        1. **Natural Language**: Use descriptive phrases like "E. coli promoter for high expression"
        2. **Specific Terms**: Include organism names, part types, or functions
        3. **Multiple Keywords**: Combine different aspects like "mammalian fluorescent reporter"
        4. **Synonyms**: The AI understands related terms and synonyms
        
        ### 🔍 Query Examples
        
        - **By Function**: "strong promoter", "fluorescent protein", "selection marker"
        - **By Organism**: "E. coli", "mammalian", "yeast expression"
        - **By Technology**: "CRISPR", "optogenetics", "biosensor"
        - **By Application**: "protein production", "gene regulation", "cell imaging"
        
        ### 📊 Understanding Results
        
        - **Similarity Score**: Higher scores (closer to 1.0) indicate better matches
        - **Ranking**: Results are sorted by similarity score
        - **Context**: AI considers both names and descriptions for matching
        """)

if __name__ == "__main__":
    main()
