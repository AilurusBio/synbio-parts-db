"""
Parts Browser - Biological Parts Browser
Simplified version with core search and browsing functionality
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from utils import get_db_connection, search_parts

st.set_page_config(
    page_title="Parts Browser - SynVectorDB",
    page_icon="🔍",
    layout="wide"
)

def get_filter_options():
    """Get filter options"""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return {}, {}
            
            # Get type options
            types = conn.execute("""
                SELECT DISTINCT type_level_1 
                FROM parts 
                WHERE type_level_1 IS NOT NULL 
                ORDER BY type_level_1
            """).fetchall()
            type_options = [t[0] for t in types]
            
            # Get source options
            sources = conn.execute("""
                SELECT DISTINCT source_collection 
                FROM parts 
                WHERE source_collection IS NOT NULL 
                ORDER BY source_collection
            """).fetchall()
            source_options = [s[0] for s in sources]
            
            return type_options, source_options
    except Exception as e:
        st.error(f"Failed to get filter options: {e}")
        return [], []

def get_part_detail(uid):
    """Get part details"""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return None
            
            query = """
                SELECT uid, name, description, type_level_1, type_level_2, type_level_3,
                       source_collection, source_name, metadata_organism,
                       LENGTH(sequence) as sequence_length, sequence_gc_content,
                       sequence
                FROM parts 
                WHERE uid = ?
            """
            
            result = conn.execute(query, [uid]).fetchone()
            if result:
                columns = [desc[0] for desc in conn.description]
                return dict(zip(columns, result))
            return None
    except Exception as e:
        st.error(f"Failed to get part details: {e}")
        return None

def main():
    st.title("🔍 Parts Browser")
    st.markdown("---")
    
    # Sidebar filters
    st.sidebar.header("🎛️ Search and Filter")
    
    # Text search
    search_query = st.sidebar.text_input("🔍 Search Parts", placeholder="Enter name or description keywords...")
    
    # Get filter options
    type_options, source_options = get_filter_options()
    
    # Type filter
    selected_type = st.sidebar.selectbox(
        "📂 Function Type",
        ["All"] + type_options
    )
    type_filter = "" if selected_type == "All" else selected_type
    
    # Source filter
    selected_source = st.sidebar.selectbox(
        "🏢 Data Source",
        ["All"] + source_options
    )
    source_filter = "" if selected_source == "All" else selected_source
    
    # Result count
    limit = st.sidebar.slider("📊 Results to Show", 10, 100, 20)
    
    # Search button
    if st.sidebar.button("🔍 Search", type="primary"):
        st.session_state.search_triggered = True
    
    # Execute search
    if hasattr(st.session_state, 'search_triggered') or search_query or type_filter or source_filter:
        with st.spinner("Searching..."):
            results = search_parts(
                query=search_query,
                type_filter=type_filter,
                source_filter=source_filter,
                limit=limit
            )
        
        if results:
            st.success(f"Found {len(results)} results")
            
            # Display results
            for i, part in enumerate(results):
                with st.expander(f"🧬 {part.get('name', 'Unnamed')} ({part.get('uid', 'N/A')})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**UID:** `{part.get('uid', 'N/A')}`")
                        st.markdown(f"**Name:** {part.get('name', 'Not provided')}")
                        st.markdown(f"**Description:** {part.get('description', 'No description')[:200]}...")
                        
                        if part.get('type_level_1'):
                            st.markdown(f"**Function Type:** {part.get('type_level_1')}")
                        if part.get('type_level_2'):
                            st.markdown(f"**Subtype:** {part.get('type_level_2')}")
                    
                    with col2:
                        st.markdown(f"**Source:** {part.get('source_collection', 'N/A')}")
                        if part.get('sequence_length'):
                            st.markdown(f"**Sequence Length:** {part.get('sequence_length')} bp")
                        
                        # View details button
                        if st.button(f"View Details", key=f"detail_{i}"):
                            st.session_state.selected_part = part.get('uid')
        else:
            st.info("No matching results found. Please try adjusting your search criteria.")
    
    # Display part details
    if hasattr(st.session_state, 'selected_part') and st.session_state.selected_part:
        st.markdown("---")
        st.markdown("## 📋 Part Details")
        
        part_detail = get_part_detail(st.session_state.selected_part)
        if part_detail:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Basic Information")
                st.markdown(f"**UID:** `{part_detail.get('uid')}`")
                st.markdown(f"**Name:** {part_detail.get('name', 'Not provided')}")
                st.markdown(f"**Function Type:** {part_detail.get('type_level_1', 'N/A')}")
                st.markdown(f"**Subtype:** {part_detail.get('type_level_2', 'N/A')}")
                if part_detail.get('type_level_3'):
                    st.markdown(f"**Detailed Type:** {part_detail.get('type_level_3')}")
                
                st.markdown("### Source Information")
                st.markdown(f"**Data Source:** {part_detail.get('source_collection', 'N/A')}")
                st.markdown(f"**Source Name:** {part_detail.get('source_name', 'N/A')}")
                st.markdown(f"**Organism:** {part_detail.get('metadata_organism', 'N/A')}")
            
            with col2:
                st.markdown("### Sequence Information")
                if part_detail.get('sequence_length'):
                    st.markdown(f"**Sequence Length:** {part_detail.get('sequence_length')} bp")
                if part_detail.get('sequence_gc_content'):
                    st.markdown(f"**GC Content:** {part_detail.get('sequence_gc_content'):.2f}%")
                
                # Sequence display
                if part_detail.get('sequence'):
                    st.markdown("### DNA Sequence")
                    sequence = part_detail.get('sequence')
                    if len(sequence) > 100:
                        st.text_area("Sequence (first 100 bases)", sequence[:100] + "...", height=100)
                        st.markdown(f"Full sequence length: {len(sequence)} bp")
                    else:
                        st.text_area("Complete sequence", sequence, height=100)
            
            # Description
            if part_detail.get('description'):
                st.markdown("### Detailed Description")
                st.markdown(part_detail.get('description'))
        
        # Close details button
        if st.button("Close Details"):
            del st.session_state.selected_part
    
    # Usage instructions
    with st.expander("ℹ️ Usage Instructions"):
        st.markdown("""
        ### How to use Parts Browser:
        
        1. **Text Search**: Enter keywords in the search box, supports name and description search
        2. **Type Filter**: Select specific function types for filtering
        3. **Source Filter**: Select specific data sources for filtering
        4. **Result Count**: Adjust the number of results to display (10-100)
        5. **View Details**: Click "View Details" button to see complete part information
        
        ### Features:
        - 🔍 Full-text search support
        - 📂 Multi-dimensional filtering
        - 📋 Detailed information display
        - 🧬 Sequence information viewing
        - 📊 Real-time result statistics
        """)

if __name__ == "__main__":
    main()
