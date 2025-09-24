"""
Semantic Search - Natural Language Search
Demo version with functionality explanation
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from utils import search_parts

st.set_page_config(
    page_title="Semantic Search - SynVectorDB",
    page_icon="🧠",
    layout="wide"
)

def main():
    st.title("🧠 Semantic Search")
    st.markdown("---")
    
    # Feature explanation
    st.info("""
    **Note**: This is the githubshare demo version with simplified semantic search functionality.
    For full semantic search capabilities, please visit the production version: https://app.sjtu.bio
    """)
    
    # Demo interface
    st.markdown("## 🔍 Natural Language Search")
    
    # Search input
    query = st.text_area(
        "Enter your search query (natural language)",
        placeholder="Example: Find strong promoters for E. coli expression\nExample: Need fluorescent proteins that work in yeast\nExample: Regulatory elements suitable for mammalian cells",
        height=100
    )
    
    # Example queries
    st.markdown("### 💡 Example Queries")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🦠 E. coli Promoters"):
            st.session_state.demo_query = "E. coli promoters"
    
    with col2:
        if st.button("🔬 Fluorescent Proteins"):
            st.session_state.demo_query = "fluorescent proteins"
    
    with col3:
        if st.button("🧬 Regulatory Elements"):
            st.session_state.demo_query = "regulatory elements"
    
    # Handle demo queries
    if hasattr(st.session_state, 'demo_query'):
        query = st.session_state.demo_query
        del st.session_state.demo_query
    
    # Search button
    if st.button("🔍 Semantic Search", type="primary") and query:
        st.markdown("### 🎯 Search Results")
        
        # Demo version: use simple keyword search
        with st.spinner("Performing semantic search..."):
            # Simplified keyword extraction
            keywords = query.lower()
            if "promoter" in keywords:
                search_term = "promoter"
            elif "fluorescent" in keywords or "fluorescence" in keywords:
                search_term = "fluorescent"
            elif "protein" in keywords:
                search_term = "protein"
            elif "regulatory" in keywords:
                search_term = "regulatory"
            elif "reporter" in keywords:
                search_term = "reporter"
            else:
                search_term = query.split()[0] if query.split() else ""
            
            results = search_parts(query=search_term, limit=10)
        
        if results:
            st.success(f"Found {len(results)} relevant results")
            
            for i, part in enumerate(results):
                relevance_score = (10-i)*10
                with st.expander(f"🧬 {part.get('name', 'Unnamed')} (Relevance: {relevance_score}%)"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Name:** {part.get('name', 'Not provided')}")
                        st.markdown(f"**Type:** {part.get('type_level_1', 'N/A')}")
                        st.markdown(f"**Description:** {part.get('description', 'No description')[:150]}...")
                    
                    with col2:
                        st.markdown(f"**Source:** {part.get('source_collection', 'N/A')}")
                        if part.get('sequence_length'):
                            st.markdown(f"**Length:** {part.get('sequence_length')} bp")
        else:
            st.warning("No relevant results found, please try other queries")
    
    # Feature explanation
    st.markdown("---")
    st.markdown("## 📚 About Semantic Search")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎯 Features
        - **Natural Language Understanding**: Supports natural language queries
        - **Semantic Matching**: Based on meaning rather than keyword matching
        - **Intelligent Ranking**: Results sorted by relevance
        - **Multi-language Support**: Supports English and Chinese queries
        - **Context Understanding**: Understands biological context of queries
        """)
    
    with col2:
        st.markdown("""
        ### 🔬 Technical Implementation
        - **Vector Database**: Uses BGE-M3 embedding model
        - **Semantic Indexing**: Semantic index of 19,850 parts
        - **Real-time Search**: Millisecond response time
        - **Cloud Deployment**: Cloudflare Workers + Vectorize
        - **API Integration**: Supports MCP protocol and REST API
        """)
    
    # Production version link
    st.markdown("---")
    st.markdown("## 🌐 Full Feature Experience")
    
    st.info("""
    **Experience the complete semantic search functionality at:**
    
    🔗 **Production Version**: https://app.sjtu.bio/semantic-search
    
    Production version includes:
    - Complete BGE-M3 semantic search
    - Real-time vector retrieval
    - Advanced filtering options
    - Detailed relevance scoring
    - Multi-modal search support
    """)
    
    # API documentation
    with st.expander("🔌 API Integration"):
        st.markdown("""
        ### REST API
        ```bash
        curl "https://testsdb.sjtu.bio/semantic_search" \\
             -H "Content-Type: application/json" \\
             -d '{"query": "E. coli promoter", "top_k": 10}'
        ```
        
        ### MCP Server (NPM)
        ```bash
        npm install synvectordb-mcp-server
        ```
        
        ### Python SDK (Planned)
        ```python
        from synvectordb import SemanticSearch
        
        search = SemanticSearch()
        results = search.query("strong promoter for E. coli")
        ```
        """)

if __name__ == "__main__":
    main()
