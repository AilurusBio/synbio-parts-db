"""
Statistics - Data Statistical Analysis
Display detailed statistical information of the database
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from utils import get_db_connection

st.set_page_config(
    page_title="Statistics - SynVectorDB",
    page_icon="📊",
    layout="wide"
)

@st.cache_data
def get_detailed_stats():
    """Get detailed statistical data"""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return {}
            
            stats = {}
            
            # Basic statistics
            stats['total_parts'] = conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
            
            # Type distribution
            type_dist = conn.execute("""
                SELECT type_level_1, COUNT(*) as count
                FROM parts 
                WHERE type_level_1 IS NOT NULL
                GROUP BY type_level_1
                ORDER BY count DESC
            """).fetchall()
            stats['type_distribution'] = pd.DataFrame(type_dist, columns=['Type', 'Count'])
            
            # Source distribution
            source_dist = conn.execute("""
                SELECT source_collection, COUNT(*) as count
                FROM parts 
                WHERE source_collection IS NOT NULL
                GROUP BY source_collection
                ORDER BY count DESC
            """).fetchall()
            stats['source_distribution'] = pd.DataFrame(source_dist, columns=['Source', 'Count'])
            
            # Sequence length distribution
            length_dist = conn.execute("""
                SELECT 
                    CASE 
                        WHEN LENGTH(sequence) < 100 THEN '<100bp'
                        WHEN LENGTH(sequence) < 500 THEN '100-500bp'
                        WHEN LENGTH(sequence) < 1000 THEN '500-1000bp'
                        WHEN LENGTH(sequence) < 5000 THEN '1-5kb'
                        WHEN LENGTH(sequence) < 10000 THEN '5-10kb'
                        ELSE '>10kb'
                    END as length_range,
                    COUNT(*) as count
                FROM parts 
                WHERE sequence IS NOT NULL
                GROUP BY length_range
                ORDER BY 
                    CASE 
                        WHEN LENGTH(sequence) < 100 THEN 1
                        WHEN LENGTH(sequence) < 500 THEN 2
                        WHEN LENGTH(sequence) < 1000 THEN 3
                        WHEN LENGTH(sequence) < 5000 THEN 4
                        WHEN LENGTH(sequence) < 10000 THEN 5
                        ELSE 6
                    END
            """).fetchall()
            stats['length_distribution'] = pd.DataFrame(length_dist, columns=['Length_Range', 'Count'])
            
            # GC content distribution
            gc_stats = conn.execute("""
                SELECT 
                    AVG(sequence_gc_content) as avg_gc,
                    MIN(sequence_gc_content) as min_gc,
                    MAX(sequence_gc_content) as max_gc
                FROM parts 
                WHERE sequence_gc_content IS NOT NULL
            """).fetchone()
            stats['gc_content'] = {
                'avg': gc_stats[0] if gc_stats[0] else 0,
                'min': gc_stats[1] if gc_stats[1] else 0,
                'max': gc_stats[2] if gc_stats[2] else 0
            }
            
            # Organism distribution
            organism_dist = conn.execute("""
                SELECT metadata_organism, COUNT(*) as count
                FROM parts 
                WHERE metadata_organism IS NOT NULL AND metadata_organism != ''
                GROUP BY metadata_organism
                ORDER BY count DESC
                LIMIT 10
            """).fetchall()
            stats['organism_distribution'] = pd.DataFrame(organism_dist, columns=['Organism', 'Count'])
            
            return stats
    except Exception as e:
        st.error(f"Failed to get statistical data: {e}")
        return {}

def main():
    st.title("📊 Statistics - Data Analysis")
    st.markdown("---")
    
    # Get statistical data
    with st.spinner("Loading statistical data..."):
        stats = get_detailed_stats()
    
    if not stats:
        st.error("Unable to load statistical data")
        return
    
    # Overview cards
    st.markdown("## 📈 Database Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Parts", f"{stats['total_parts']:,}")
    
    with col2:
        st.metric("Function Types", len(stats['type_distribution']))
    
    with col3:
        st.metric("Data Sources", len(stats['source_distribution']))
    
    with col4:
        avg_gc = stats['gc_content']['avg']
        st.metric("Average GC Content", f"{avg_gc:.1f}%" if avg_gc else "N/A")
    
    # Chart display
    st.markdown("---")
    st.markdown("## 📊 Detailed Analysis")
    
    # First row charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Function Type Distribution")
        if not stats['type_distribution'].empty:
            fig = px.pie(
                stats['type_distribution'], 
                values='Count', 
                names='Type',
                title="Part Function Type Distribution"
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No type distribution data available")
    
    with col2:
        st.markdown("### Data Source Distribution")
        if not stats['source_distribution'].empty:
            fig = px.bar(
                stats['source_distribution'], 
                x='Source', 
                y='Count',
                title="Data Source Distribution"
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No source distribution data available")
    
    # Second row charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Sequence Length Distribution")
        if not stats['length_distribution'].empty:
            fig = px.bar(
                stats['length_distribution'], 
                x='Length_Range', 
                y='Count',
                title="Sequence Length Distribution",
                color='Count',
                color_continuous_scale='viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No length distribution data available")
    
    with col2:
        st.markdown("### Organism Distribution (Top 10)")
        if not stats['organism_distribution'].empty:
            fig = px.bar(
                stats['organism_distribution'], 
                x='Count', 
                y='Organism',
                orientation='h',
                title="Organism Distribution (Top 10)"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No organism distribution data available")
    
    # Detailed data tables
    st.markdown("---")
    st.markdown("## 📋 Detailed Data")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Function Types", "Data Sources", "Sequence Length", "Organisms"])
    
    with tab1:
        if not stats['type_distribution'].empty:
            st.dataframe(stats['type_distribution'], use_container_width=True)
        else:
            st.info("No function type data available")
    
    with tab2:
        if not stats['source_distribution'].empty:
            st.dataframe(stats['source_distribution'], use_container_width=True)
        else:
            st.info("No data source data available")
    
    with tab3:
        if not stats['length_distribution'].empty:
            st.dataframe(stats['length_distribution'], use_container_width=True)
        else:
            st.info("No sequence length data available")
    
    with tab4:
        if not stats['organism_distribution'].empty:
            st.dataframe(stats['organism_distribution'], use_container_width=True)
        else:
            st.info("No organism data available")
    
    # GC content statistics
    st.markdown("---")
    st.markdown("## 🧬 Sequence Feature Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Average GC Content", 
            f"{stats['gc_content']['avg']:.2f}%" if stats['gc_content']['avg'] else "N/A"
        )
    
    with col2:
        st.metric(
            "Minimum GC Content", 
            f"{stats['gc_content']['min']:.2f}%" if stats['gc_content']['min'] else "N/A"
        )
    
    with col3:
        st.metric(
            "Maximum GC Content", 
            f"{stats['gc_content']['max']:.2f}%" if stats['gc_content']['max'] else "N/A"
        )
    
    # Data export
    st.markdown("---")
    st.markdown("## 💾 Data Export")
    
    if st.button("📥 Export Statistical Data (CSV)"):
        # Create summary data
        summary_data = {
            "Metric": ["Total Parts", "Function Types", "Data Sources", "Average GC Content"],
            "Value": [
                stats['total_parts'],
                len(stats['type_distribution']),
                len(stats['source_distribution']),
                f"{stats['gc_content']['avg']:.2f}%" if stats['gc_content']['avg'] else "N/A"
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        
        csv = summary_df.to_csv(index=False)
        st.download_button(
            label="Download Summary Statistics",
            data=csv,
            file_name="synvectordb_summary_stats.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
