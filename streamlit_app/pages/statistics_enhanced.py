"""
SynVectorDB githubshare - Enhanced Statistics Page
使用DuckDB的增强统计分析页面
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils_enhanced import (
    get_basic_stats, 
    get_parts_sample,
    get_db_connection,
    get_system_info
)
import numpy as np

# 页面配置
st.set_page_config(
    page_title="Statistics - SynVectorDB",
    page_icon="📊",
    layout="wide"
)

@st.cache_data
def get_detailed_statistics():
    """获取详细统计信息（缓存结果）"""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return {}
            
            stats = {}
            
            # 基础统计
            stats['total_parts'] = conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
            
            # 序列长度统计
            length_stats = conn.execute("""
                SELECT 
                    MIN(LENGTH(sequence)) as min_length,
                    MAX(LENGTH(sequence)) as max_length,
                    AVG(LENGTH(sequence)) as avg_length,
                    COUNT(CASE WHEN sequence IS NOT NULL THEN 1 END) as with_sequence
                FROM parts
            """).fetchone()
            
            stats['sequence_stats'] = {
                'min_length': length_stats[0] if length_stats[0] else 0,
                'max_length': length_stats[1] if length_stats[1] else 0,
                'avg_length': length_stats[2] if length_stats[2] else 0,
                'with_sequence': length_stats[3] if length_stats[3] else 0
            }
            
            # 类型统计
            type_stats = conn.execute("""
                SELECT type_level_1, COUNT(*) as count 
                FROM parts 
                WHERE type_level_1 IS NOT NULL 
                GROUP BY type_level_1 
                ORDER BY count DESC
            """).fetchall()
            stats['type_distribution'] = type_stats
            
            # 来源统计
            source_stats = conn.execute("""
                SELECT source_collection, COUNT(*) as count 
                FROM parts 
                WHERE source_collection IS NOT NULL 
                GROUP BY source_collection 
                ORDER BY count DESC
            """).fetchall()
            stats['source_distribution'] = source_stats
            
            # 物种统计
            try:
                organism_stats = conn.execute("""
                    SELECT metadata_organism, COUNT(*) as count 
                    FROM parts 
                    WHERE metadata_organism IS NOT NULL 
                    GROUP BY metadata_organism 
                    ORDER BY count DESC
                    LIMIT 20
                """).fetchall()
                stats['organism_distribution'] = organism_stats
            except:
                stats['organism_distribution'] = []
            
            # 序列长度分布
            length_distribution = conn.execute("""
                SELECT 
                    CASE 
                        WHEN LENGTH(sequence) < 100 THEN '< 100bp'
                        WHEN LENGTH(sequence) < 500 THEN '100-500bp'
                        WHEN LENGTH(sequence) < 1000 THEN '500-1000bp'
                        WHEN LENGTH(sequence) < 5000 THEN '1-5kb'
                        WHEN LENGTH(sequence) < 10000 THEN '5-10kb'
                        ELSE '> 10kb'
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
            stats['length_distribution'] = length_distribution
            
            # 数据质量统计
            quality_stats = conn.execute("""
                SELECT 
                    COUNT(CASE WHEN name IS NOT NULL AND name != '' THEN 1 END) as with_name,
                    COUNT(CASE WHEN description IS NOT NULL AND description != '' THEN 1 END) as with_description,
                    COUNT(CASE WHEN sequence IS NOT NULL AND sequence != '' THEN 1 END) as with_sequence,
                    COUNT(CASE WHEN type_level_1 IS NOT NULL THEN 1 END) as with_type,
                    COUNT(*) as total
                FROM parts
            """).fetchone()
            
            stats['quality_stats'] = {
                'with_name': quality_stats[0],
                'with_description': quality_stats[1],
                'with_sequence': quality_stats[2],
                'with_type': quality_stats[3],
                'total': quality_stats[4]
            }
            
            return stats
            
    except Exception as e:
        st.error(f"获取详细统计信息失败: {e}")
        return {}

def display_overview_metrics(stats):
    """显示概览指标"""
    st.markdown("## 📊 Database Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Parts", f"{stats.get('total_parts', 0):,}")
    
    with col2:
        type_count = len(stats.get('type_distribution', []))
        st.metric("Part Types", type_count)
    
    with col3:
        source_count = len(stats.get('source_distribution', []))
        st.metric("Data Sources", source_count)
    
    with col4:
        organism_count = len(stats.get('organism_distribution', []))
        st.metric("Organisms", organism_count)
    
    # 序列统计
    seq_stats = stats.get('sequence_stats', {})
    if seq_stats:
        st.markdown("### 🧬 Sequence Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("With Sequences", f"{seq_stats.get('with_sequence', 0):,}")
        
        with col2:
            avg_len = seq_stats.get('avg_length', 0)
            st.metric("Avg Length", f"{avg_len:.0f} bp" if avg_len > 0 else "N/A")
        
        with col3:
            min_len = seq_stats.get('min_length', 0)
            st.metric("Min Length", f"{min_len:,} bp" if min_len > 0 else "N/A")
        
        with col4:
            max_len = seq_stats.get('max_length', 0)
            st.metric("Max Length", f"{max_len:,} bp" if max_len > 0 else "N/A")

def display_distribution_charts(stats):
    """显示分布图表"""
    st.markdown("## 📈 Data Distribution")
    
    col1, col2 = st.columns(2)
    
    # 类型分布
    with col1:
        st.markdown("### Part Type Distribution")
        type_data = stats.get('type_distribution', [])
        if type_data:
            type_df = pd.DataFrame(type_data, columns=['Type', 'Count'])
            fig = px.bar(
                type_df.head(10),
                x='Count',
                y='Type',
                orientation='h',
                title="Top 10 Part Types",
                color='Count',
                color_continuous_scale='viridis'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No type distribution data available")
    
    # 来源分布
    with col2:
        st.markdown("### Data Source Distribution")
        source_data = stats.get('source_distribution', [])
        if source_data:
            source_df = pd.DataFrame(source_data, columns=['Source', 'Count'])
            fig = px.pie(
                source_df,
                values='Count',
                names='Source',
                title="Data Source Distribution"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No source distribution data available")
    
    # 物种分布
    organism_data = stats.get('organism_distribution', [])
    if organism_data:
        st.markdown("### Organism Distribution")
        organism_df = pd.DataFrame(organism_data, columns=['Organism', 'Count'])
        fig = px.bar(
            organism_df.head(15),
            x='Organism',
            y='Count',
            title="Top 15 Organisms",
            color='Count',
            color_continuous_scale='plasma'
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    # 序列长度分布
    length_data = stats.get('length_distribution', [])
    if length_data:
        st.markdown("### Sequence Length Distribution")
        length_df = pd.DataFrame(length_data, columns=['Length Range', 'Count'])
        fig = px.bar(
            length_df,
            x='Length Range',
            y='Count',
            title="Sequence Length Distribution",
            color='Count',
            color_continuous_scale='blues'
        )
        st.plotly_chart(fig, use_container_width=True)

def display_quality_analysis(stats):
    """显示数据质量分析"""
    st.markdown("## 🔍 Data Quality Analysis")
    
    quality = stats.get('quality_stats', {})
    if not quality:
        st.info("No quality statistics available")
        return
    
    total = quality.get('total', 1)
    
    # 质量指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        name_pct = (quality.get('with_name', 0) / total) * 100
        st.metric("With Names", f"{quality.get('with_name', 0):,}", f"{name_pct:.1f}%")
    
    with col2:
        desc_pct = (quality.get('with_description', 0) / total) * 100
        st.metric("With Descriptions", f"{quality.get('with_description', 0):,}", f"{desc_pct:.1f}%")
    
    with col3:
        seq_pct = (quality.get('with_sequence', 0) / total) * 100
        st.metric("With Sequences", f"{quality.get('with_sequence', 0):,}", f"{seq_pct:.1f}%")
    
    with col4:
        type_pct = (quality.get('with_type', 0) / total) * 100
        st.metric("With Types", f"{quality.get('with_type', 0):,}", f"{type_pct:.1f}%")
    
    # 质量分布图
    quality_data = {
        'Field': ['Names', 'Descriptions', 'Sequences', 'Types'],
        'Count': [
            quality.get('with_name', 0),
            quality.get('with_description', 0),
            quality.get('with_sequence', 0),
            quality.get('with_type', 0)
        ],
        'Percentage': [name_pct, desc_pct, seq_pct, type_pct]
    }
    
    quality_df = pd.DataFrame(quality_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            quality_df,
            x='Field',
            y='Count',
            title="Data Completeness by Field",
            color='Percentage',
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(
            quality_df,
            x='Field',
            y='Percentage',
            title="Data Completeness Percentage",
            color='Percentage',
            color_continuous_scale='RdYlGn'
        )
        fig.update_yaxis(range=[0, 100])
        st.plotly_chart(fig, use_container_width=True)

def display_export_options(stats):
    """显示数据导出选项"""
    st.markdown("## 📥 Export Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Statistics (CSV)"):
            # 准备统计数据
            export_data = []
            
            # 基础统计
            export_data.append({
                'Category': 'Overview',
                'Metric': 'Total Parts',
                'Value': stats.get('total_parts', 0)
            })
            
            # 类型统计
            for type_name, count in stats.get('type_distribution', []):
                export_data.append({
                    'Category': 'Part Types',
                    'Metric': type_name,
                    'Value': count
                })
            
            # 来源统计
            for source_name, count in stats.get('source_distribution', []):
                export_data.append({
                    'Category': 'Data Sources',
                    'Metric': source_name,
                    'Value': count
                })
            
            export_df = pd.DataFrame(export_data)
            csv = export_df.to_csv(index=False)
            
            st.download_button(
                label="Download Statistics CSV",
                data=csv,
                file_name="synvectordb_statistics.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📋 Export Sample Data (CSV)"):
            sample_data = get_parts_sample(100)
            if sample_data:
                sample_df = pd.DataFrame(sample_data)
                csv = sample_df.to_csv(index=False)
                
                st.download_button(
                    label="Download Sample CSV",
                    data=csv,
                    file_name="synvectordb_sample.csv",
                    mime="text/csv"
                )
            else:
                st.error("No sample data available")
    
    with col3:
        if st.button("📄 Generate Report"):
            # 生成统计报告
            report = f"""
# SynVectorDB Statistics Report

## Overview
- Total Parts: {stats.get('total_parts', 0):,}
- Part Types: {len(stats.get('type_distribution', []))}
- Data Sources: {len(stats.get('source_distribution', []))}
- Organisms: {len(stats.get('organism_distribution', []))}

## Sequence Statistics
"""
            seq_stats = stats.get('sequence_stats', {})
            if seq_stats:
                report += f"""
- Parts with Sequences: {seq_stats.get('with_sequence', 0):,}
- Average Length: {seq_stats.get('avg_length', 0):.0f} bp
- Min Length: {seq_stats.get('min_length', 0):,} bp
- Max Length: {seq_stats.get('max_length', 0):,} bp
"""
            
            report += "\n## Top Part Types\n"
            for type_name, count in stats.get('type_distribution', [])[:10]:
                report += f"- {type_name}: {count:,}\n"
            
            st.download_button(
                label="Download Report (MD)",
                data=report,
                file_name="synvectordb_report.md",
                mime="text/markdown"
            )

def main():
    """主页面函数"""
    
    # 页面标题
    st.title("📊 Database Statistics")
    st.markdown("Comprehensive analysis of the SynVectorDB database")
    st.markdown("---")
    
    # 系统信息
    system_info = get_system_info()
    st.info(f"📊 Using {system_info.get('database_type', 'Unknown')} database for statistics")
    
    # 获取详细统计信息
    with st.spinner("Loading database statistics..."):
        stats = get_detailed_statistics()
    
    if not stats:
        st.error("Failed to load statistics")
        st.stop()
    
    # 显示各个部分
    display_overview_metrics(stats)
    st.markdown("---")
    
    display_distribution_charts(stats)
    st.markdown("---")
    
    display_quality_analysis(stats)
    st.markdown("---")
    
    display_export_options(stats)
    
    # 技术信息
    st.markdown("---")
    st.markdown("## ℹ️ Technical Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🗄️ Database")
        st.markdown(f"""
        - **Type**: {system_info.get('database_type', 'Unknown')}
        - **Total Records**: {stats.get('total_parts', 0):,}
        - **Data Quality**: High completeness
        - **Update Frequency**: Static snapshot
        """)
    
    with col2:
        st.markdown("### 📊 Statistics")
        st.markdown("""
        - **Real-time**: Live database queries
        - **Caching**: Streamlit resource caching
        - **Export**: CSV and Markdown formats
        - **Visualization**: Interactive Plotly charts
        """)
    
    # 刷新数据按钮
    if st.button("🔄 Refresh Statistics", type="secondary"):
        st.cache_data.clear()
        st.rerun()

if __name__ == "__main__":
    main()
