"""
SynVectorDB Local Deployment - Statistics Dashboard
View database statistics and analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import get_basic_stats

# Page configuration
st.set_page_config(
    page_title="Statistics - SynVectorDB",
    page_icon="📊",
    layout="wide"
)

def main():
    """Main statistics function"""
    
    st.title("📊 Database Statistics")
    st.markdown("Comprehensive analytics of the synthetic biology parts database")
    
    # Load statistics
    with st.spinner("Loading database statistics..."):
        stats = get_basic_stats()
    
    if "error" in stats:
        st.error(f"Could not load statistics: {stats['error']}")
        return
    
    # Overview metrics
    st.markdown("## 📈 Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Parts",
            f"{stats['total_parts']:,}",
            help="Total number of synthetic biology parts in the database"
        )
    
    with col2:
        st.metric(
            "Part Types",
            len(stats['type_stats']),
            help="Number of different part type categories"
        )
    
    with col3:
        st.metric(
            "Data Sources",
            len(stats['source_stats']),
            help="Number of different source collections"
        )
    
    with col4:
        # Calculate average parts per type
        avg_per_type = stats['total_parts'] / len(stats['type_stats']) if stats['type_stats'] else 0
        st.metric(
            "Avg Parts/Type",
            f"{avg_per_type:.0f}",
            help="Average number of parts per type category"
        )
    
    # Part Type Distribution
    st.markdown("## 🧬 Part Type Distribution")
    
    if stats['type_stats']:
        # Create DataFrame for type statistics
        type_df = pd.DataFrame(
            list(stats['type_stats'].items()),
            columns=['Part Type', 'Count']
        ).sort_values('Count', ascending=False)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Bar chart
            fig_bar = px.bar(
                type_df,
                x='Part Type',
                y='Count',
                title="Parts by Type",
                color='Count',
                color_continuous_scale='viridis'
            )
            fig_bar.update_layout(
                xaxis_title="Part Type",
                yaxis_title="Number of Parts",
                showlegend=False
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            # Pie chart
            fig_pie = px.pie(
                type_df,
                values='Count',
                names='Part Type',
                title="Type Distribution"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Data table
        st.markdown("### Detailed Breakdown")
        
        # Add percentage column
        type_df['Percentage'] = (type_df['Count'] / stats['total_parts'] * 100).round(2)
        type_df['Percentage'] = type_df['Percentage'].astype(str) + '%'
        
        st.dataframe(
            type_df,
            use_container_width=True,
            hide_index=True
        )
    
    # Source Collection Distribution
    st.markdown("## 📚 Source Collection Distribution")
    
    if stats['source_stats']:
        # Create DataFrame for source statistics
        source_df = pd.DataFrame(
            list(stats['source_stats'].items()),
            columns=['Source Collection', 'Count']
        ).sort_values('Count', ascending=False)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Horizontal bar chart
            fig_source = px.bar(
                source_df,
                x='Count',
                y='Source Collection',
                orientation='h',
                title="Parts by Source Collection",
                color='Count',
                color_continuous_scale='plasma'
            )
            fig_source.update_layout(
                xaxis_title="Number of Parts",
                yaxis_title="Source Collection",
                showlegend=False
            )
            st.plotly_chart(fig_source, use_container_width=True)
        
        with col2:
            # Donut chart
            fig_donut = px.pie(
                source_df,
                values='Count',
                names='Source Collection',
                title="Source Distribution",
                hole=0.4
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        
        # Data table
        st.markdown("### Source Collection Details")
        
        # Add percentage column
        source_df['Percentage'] = (source_df['Count'] / stats['total_parts'] * 100).round(2)
        source_df['Percentage'] = source_df['Percentage'].astype(str) + '%'
        
        st.dataframe(
            source_df,
            use_container_width=True,
            hide_index=True
        )
    
    # Summary insights
    st.markdown("## 💡 Key Insights")
    
    insights = []
    
    if stats['type_stats']:
        # Most common type
        most_common_type = max(stats['type_stats'], key=stats['type_stats'].get)
        most_common_count = stats['type_stats'][most_common_type]
        insights.append(f"**Most common part type**: {most_common_type} ({most_common_count:,} parts)")
    
    if stats['source_stats']:
        # Largest source
        largest_source = max(stats['source_stats'], key=stats['source_stats'].get)
        largest_count = stats['source_stats'][largest_source]
        insights.append(f"**Largest source collection**: {largest_source} ({largest_count:,} parts)")
    
    # Database size insight
    if stats['total_parts'] > 10000:
        insights.append(f"**Large-scale database**: Contains {stats['total_parts']:,} parts, suitable for comprehensive research")
    
    for insight in insights:
        st.markdown(f"• {insight}")
    
    # Export options
    st.markdown("## 📥 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if stats['type_stats']:
            type_csv = type_df.to_csv(index=False)
            st.download_button(
                label="📊 Download Type Statistics",
                data=type_csv,
                file_name="synvectordb_type_statistics.csv",
                mime="text/csv"
            )
    
    with col2:
        if stats['source_stats']:
            source_csv = source_df.to_csv(index=False)
            st.download_button(
                label="📚 Download Source Statistics",
                data=source_csv,
                file_name="synvectordb_source_statistics.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
