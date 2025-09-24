"""
SynVectorDB Local Deployment - Parts Browser
Browse and search synthetic biology parts database
"""

import streamlit as st
import pandas as pd
from utils import search_parts, get_parts_sample, get_basic_stats

# Page configuration
st.set_page_config(
    page_title="Parts Browser - SynVectorDB",
    page_icon="🧬",
    layout="wide"
)

def main():
    """Main parts browser function"""
    
    st.title("🧬 Parts Browser")
    st.markdown("Browse and search the synthetic biology parts database")
    
    # Search interface
    st.markdown("## 🔍 Search Parts")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_query = st.text_input(
            "Search parts by name or description:",
            placeholder="e.g., promoter, GFP, E.coli"
        )
    
    with col2:
        search_limit = st.selectbox(
            "Results limit:",
            [10, 20, 50, 100],
            index=1
        )
    
    # Advanced filters
    with st.expander("🎛️ Advanced Filters"):
        col1, col2 = st.columns(2)
        
        with col1:
            type_filter = st.selectbox(
                "Part Type:",
                ["", "Coding Sequences", "DNA Elements", "RNA Elements", "Application", "other"]
            )
        
        with col2:
            source_filter = st.selectbox(
                "Source Collection:",
                ["", "addgene", "igem", "lab", "snapgene", "yunzhou"]
            )
    
    # Search button
    if st.button("🔍 Search Parts", type="primary"):
        with st.spinner("Searching parts..."):
            results = search_parts(
                query=search_query,
                type_filter=type_filter,
                source_filter=source_filter,
                limit=search_limit
            )
            
            if results:
                st.success(f"Found {len(results)} parts")
                
                # Display results
                df = pd.DataFrame(results)
                
                # Format the dataframe for display
                display_columns = ['name', 'description', 'type_level_1', 'source_collection']
                available_columns = [col for col in display_columns if col in df.columns]
                
                if available_columns:
                    st.dataframe(
                        df[available_columns],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Download option
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=csv,
                    file_name=f"synvectordb_search_results.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No parts found matching your criteria")
    
    # Sample parts section
    st.markdown("## 📋 Sample Parts")
    
    if st.button("🎲 Show Random Sample"):
        with st.spinner("Loading sample parts..."):
            sample_parts = get_parts_sample(10)
            
            if sample_parts:
                df_sample = pd.DataFrame(sample_parts)
                
                # Display sample
                display_columns = ['name', 'description', 'type_level_1', 'source_collection']
                available_columns = [col for col in display_columns if col in df_sample.columns]
                
                if available_columns:
                    st.dataframe(
                        df_sample[available_columns],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.dataframe(df_sample, use_container_width=True, hide_index=True)
            else:
                st.error("Could not load sample parts")
    
    # Database statistics
    st.markdown("## 📊 Database Overview")
    
    try:
        stats = get_basic_stats()
        if "error" not in stats:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Parts", f"{stats['total_parts']:,}")
            
            with col2:
                st.metric("Part Types", len(stats['type_stats']))
            
            with col3:
                st.metric("Data Sources", len(stats['source_stats']))
            
            # Type distribution
            if stats['type_stats']:
                st.markdown("### Part Type Distribution")
                type_df = pd.DataFrame(
                    list(stats['type_stats'].items()),
                    columns=['Type', 'Count']
                )
                st.bar_chart(type_df.set_index('Type'))
        else:
            st.error(f"Could not load statistics: {stats['error']}")
    except Exception as e:
        st.error(f"Error loading statistics: {e}")

if __name__ == "__main__":
    main()
