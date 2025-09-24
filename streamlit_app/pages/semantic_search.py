"""
SynVectorDB Local Deployment - Semantic Search
Advanced semantic search using AI embeddings (when available)
"""

import streamlit as st
import pandas as pd
from utils import search_parts, get_parts_sample

# Page configuration
st.set_page_config(
    page_title="Semantic Search - SynVectorDB",
    page_icon="🔍",
    layout="wide"
)

def main():
    """Main semantic search function"""
    
    st.title("🔍 Semantic Search")
    st.markdown("Advanced search using natural language queries and AI-powered semantic matching")
    
    # Check if advanced search is available
    st.info("ℹ️ **Note**: This is a simplified version. Advanced semantic search with AI embeddings requires additional setup.")
    
    # Search interface
    st.markdown("## 🧠 Natural Language Search")
    
    search_query = st.text_area(
        "Describe what you're looking for:",
        placeholder="e.g., 'fluorescent proteins for E.coli expression' or 'strong promoters for mammalian cells'",
        height=100
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        search_limit = st.selectbox(
            "Number of results:",
            [5, 10, 20, 50],
            index=1
        )
    
    with col2:
        search_mode = st.selectbox(
            "Search mode:",
            ["Text-based search", "Semantic search (if available)"],
            index=0
        )
    
    # Search button
    if st.button("🔍 Search", type="primary"):
        if not search_query.strip():
            st.warning("Please enter a search query")
            return
        
        with st.spinner("Searching for relevant parts..."):
            # Use basic text search (semantic search would require additional setup)
            results = search_parts(
                query=search_query,
                limit=search_limit
            )
            
            if results:
                st.success(f"Found {len(results)} potentially relevant parts")
                
                # Display results with enhanced formatting
                for i, part in enumerate(results, 1):
                    with st.expander(f"#{i}: {part.get('name', 'Unnamed Part')}", expanded=(i <= 3)):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown(f"**Description**: {part.get('description', 'No description available')}")
                            
                            if part.get('type_level_1'):
                                st.markdown(f"**Type**: {part.get('type_level_1')}")
                            
                            if part.get('source_collection'):
                                st.markdown(f"**Source**: {part.get('source_collection')}")
                        
                        with col2:
                            if part.get('sequence_length'):
                                st.metric("Sequence Length", f"{part.get('sequence_length')} bp")
                            
                            if part.get('uid'):
                                st.code(f"UID: {part.get('uid')}")
                
                # Download option
                df = pd.DataFrame(results)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Results",
                    data=csv,
                    file_name=f"semantic_search_results.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No parts found matching your query. Try different keywords or a broader description.")
    
    # Example queries
    st.markdown("## 💡 Example Queries")
    
    examples = [
        "Green fluorescent proteins for bacterial expression",
        "Strong constitutive promoters",
        "Inducible expression systems",
        "Protein degradation tags",
        "Ribosome binding sites for E.coli",
        "Mammalian cell expression vectors"
    ]
    
    st.markdown("Try these example queries:")
    
    for example in examples:
        if st.button(f"📝 {example}", key=f"example_{example}"):
            st.rerun()
    
    # Search tips
    with st.expander("🎯 Search Tips"):
        st.markdown("""
        **For better results:**
        - Use descriptive terms about function (e.g., "fluorescent", "inducible")
        - Specify the organism if relevant (e.g., "E.coli", "mammalian")
        - Include the application context (e.g., "expression", "regulation")
        - Try both specific and general terms
        
        **Current limitations:**
        - This version uses text-based matching
        - Full semantic search requires AI model setup
        - Results are ranked by text similarity
        """)
    
    # Random discovery
    st.markdown("## 🎲 Discover Random Parts")
    
    if st.button("🎲 Show Random Parts for Inspiration"):
        with st.spinner("Loading random parts..."):
            random_parts = get_parts_sample(8)
            
            if random_parts:
                st.markdown("### Random Parts from the Database")
                
                # Display in a grid
                cols = st.columns(2)
                
                for i, part in enumerate(random_parts):
                    with cols[i % 2]:
                        with st.container():
                            st.markdown(f"**{part.get('name', 'Unnamed Part')}**")
                            st.caption(f"Type: {part.get('type_level_1', 'Unknown')}")
                            
                            description = part.get('description', 'No description')
                            if len(description) > 100:
                                description = description[:100] + "..."
                            st.markdown(description)
                            
                            if part.get('source_collection'):
                                st.badge(part.get('source_collection'))

if __name__ == "__main__":
    main()
