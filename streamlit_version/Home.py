import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager
from sentence_transformers import SentenceTransformer
import numpy as np
import lancedb
import pickle
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pages.mcp_server import MCPServer
from utils import init_embeddings, get_embeddings_data, get_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create MCP Server instance
mcp_server = MCPServer()

# Mount MCP Server routes to main application
app.mount("/api/mcp", mcp_server.app)

# Page configuration
st.set_page_config(
    page_title="Synthetic Biology Parts Database",
    page_icon="🧬",
    layout="wide"
)

def main():
    st.title("Synthetic Biology Parts Database")
    
    try:
        # Get statistics
        stats = get_basic_stats()
        
        # Database Overview
        st.header("Database Overview")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Parts", stats["total_parts"])
        with col2:
            st.metric("Functional Categories", len(stats["categories"]))
        with col3:
            st.metric("Subtypes", len(stats["sub_types"]))
        with col4:
            st.metric("Data Sources", len(stats["sources"]))
            
        # Create single tab for all statistics
        st.markdown("## 📊 Database Statistics")
        
        st.markdown("""
        ### About This Database
        
        This database contains {total} experimentally validated synthetic biology standardized parts, covering {categories} major functional categories including promoters, coding sequences, and regulatory elements.
        All parts have been standardized characterized and systematically annotated, containing complete sequence information, functional validation data, and application cases. The data comes from {sources} reliable sources,
        including public databases, published literature, and laboratory validation results. This database aims to provide reliable parts support for synthetic biology design and promote standardized assembly and engineering applications of biological systems.
        """.format(
            total=stats["total_parts"],
            categories=len(stats["categories"]),
            sources=len(stats["sources"])
        ))
        
        # Get all statistics
        type_stats = get_part_type_stats()
        type_general_stats = get_type_stats()
        length_stats = get_sequence_length_stats()
        hierarchy_stats = get_type_hierarchy_stats()
        
        # Display main statistical charts
        st.markdown("### Part Type Distribution")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.plotly_chart(plot_part_type_distribution(type_stats), use_container_width=True)
        with col2:
            st.plotly_chart(plot_type_distribution(type_general_stats), use_container_width=True)
        with col3:
            st.plotly_chart(plot_sequence_length_distribution(length_stats), use_container_width=True)
        
        # Display type hierarchy
        st.markdown("### Part Type Hierarchy")
        display_type_hierarchy(hierarchy_stats)
        
        # Sequence Statistics Analysis
        st.markdown("### Sequence Statistics Analysis")
        
        # Get sequence data
        with get_connection() as conn:
            if conn is not None:
                query = """
                    SELECT 
                        type_level_1 as main_type,
                        LENGTH(sequence) as length
                    FROM parts
                    WHERE sequence IS NOT NULL
                """
                df = pd.read_sql_query(query, conn)
                
                if not df.empty:
                    st.markdown("#### Sequence Length Distribution")
                    fig = px.box(df, x="main_type", y="length", 
                               title="Sequence Length Distribution by Part Type",
                               labels={"main_type": "Part Type", "length": "Sequence Length (bp)"})
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Display statistics
                    stats = df.groupby("main_type")["length"].describe()
                    st.markdown("##### Sequence Length Statistics")
                    st.dataframe(stats)
        
        # Source Statistics Details
        st.markdown("### Source Statistics Details")
        source_stats = get_source_stats()
        source_df = pd.DataFrame(source_stats)
        source_df.columns = ["Source", "Part Count", "Average Length (bp)", "Type Count"]
        source_df["Average Length (bp)"] = source_df["Average Length (bp)"].round(2)
        st.dataframe(source_df)
        
        # Footer
        st.markdown("---")
        st.markdown("📧 Contact Us: example@example.com")
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error("Please ensure the database file exists and is accessible")

# Export FastAPI application
def get_app():
    return app

@st.cache_resource
def get_embeddings_data():
    try:
        index_path = Path("streamlit_version/data/search_index.pkl")
        if index_path.exists():
            with open(index_path, 'rb') as f:
                return pickle.load(f)
        return init_embeddings()
    except Exception as e:
        st.error(f"Failed to load vector data: {str(e)}")
        return None

# Initialize vector data
embeddings_data = get_embeddings_data()

@contextmanager
def get_connection():
    """Create a database connection context manager"""
    conn = None
    try:
        db_path = Path("streamlit_version/data/parts.db")
        conn = sqlite3.connect(db_path)
        yield conn
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        yield None
    finally:
        if conn is not None:
            conn.close()

# Get basic statistics
@st.cache_data
def get_basic_stats():
    with get_connection() as conn:
        if conn is None:
            return {
                "total_parts": 0,
                "categories": [],
                "sub_types": [],
                "sources": []
            }
        try:
            cursor = conn.cursor()
            stats = {}
            
            # Get total
            cursor.execute("SELECT COUNT(*) FROM parts")
            stats["total_parts"] = cursor.fetchone()[0]
            
            # Get main types
            cursor.execute("SELECT DISTINCT type_level_1 FROM parts WHERE type_level_1 IS NOT NULL")
            stats["categories"] = [row[0] for row in cursor.fetchall()]
            
            # Get subtypes
            cursor.execute("SELECT DISTINCT type_level_2 FROM parts WHERE type_level_2 IS NOT NULL")
            stats["sub_types"] = [row[0] for row in cursor.fetchall()]
            
            # Get sources
            cursor.execute("SELECT DISTINCT source_collection FROM parts WHERE source_collection IS NOT NULL")
            stats["sources"] = [row[0] for row in cursor.fetchall()]
            
            return stats
        except Exception as e:
            st.error(f"Failed to get statistics: {str(e)}")
            return {
                "total_parts": 0,
                "categories": [],
                "sub_types": [],
                "sources": []
            }

# Get part type statistics
@st.cache_data
def get_part_type_stats():
    with get_connection() as conn:
        if conn is None:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT type_level_1, COUNT(*) as count 
                FROM parts 
                WHERE type_level_1 IS NOT NULL
                GROUP BY type_level_1
            """)
            return [{"_id": row[0], "count": row[1]} for row in cursor.fetchall()]
        except Exception as e:
            st.error(f"Failed to get part type statistics: {str(e)}")
            return []

# Get host compatibility statistics
@st.cache_data
def get_host_compatibility_stats():
    with get_connection() as conn:
        if conn is None:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    metadata_organism,
                    COUNT(DISTINCT uid) as part_count,
                    COUNT(DISTINCT type_level_1) as type_count
                FROM parts
                WHERE metadata_organism IS NOT NULL
                GROUP BY metadata_organism
            """)
            return [
                {
                    "_id": row[0],
                    "part_count": row[1],
                    "types": row[2]
                } for row in cursor.fetchall()
            ]
        except Exception as e:
            st.error(f"Failed to get host compatibility statistics: {str(e)}")
            return []

# Get expression system statistics
@st.cache_data
def get_expression_system_stats():
    with get_connection() as conn:
        if conn is None:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    metadata_expression_system,
                    COUNT(DISTINCT uid) as part_count,
                    COUNT(DISTINCT type_level_1) as type_count
                FROM parts
                WHERE metadata_expression_system IS NOT NULL
                GROUP BY metadata_expression_system
            """)
            return [
                {
                    "_id": row[0],
                    "part_count": row[1],
                    "types": row[2]
                } for row in cursor.fetchall()
            ]
        except Exception as e:
            st.error(f"Failed to get expression system statistics: {str(e)}")
            return []

# Get sequence length statistics
@st.cache_data
def get_sequence_length_stats():
    with get_connection() as conn:
        if conn is None:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    type_level_1,
                    LENGTH(sequence) as length
                FROM parts
                WHERE sequence IS NOT NULL AND type_level_1 IS NOT NULL
            """)
            results = cursor.fetchall()
            
            # Group by type
            type_lengths = {}
            for row in results:
                main_type = row[0]
                length = row[1]
                if main_type not in type_lengths:
                    type_lengths[main_type] = []
                type_lengths[main_type].append(length)
            
            return [
                {
                    "_id": type_name,
                    "lengths": lengths
                } for type_name, lengths in type_lengths.items()
            ]
        except Exception as e:
            st.error(f"Failed to get sequence length statistics: {str(e)}")
            return []

# Get part type statistics
@st.cache_data
def get_type_stats():
    with get_connection() as conn:
        if conn is None:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT type, COUNT(*) as count 
                FROM parts 
                WHERE type IS NOT NULL AND type != ''
                GROUP BY type
            """)
            return [{"_id": row[0], "count": row[1]} for row in cursor.fetchall()]
        except Exception as e:
            st.error(f"Failed to get type statistics: {str(e)}")
            return []

# Get type hierarchy statistics
@st.cache_data
def get_type_hierarchy_stats():
    with get_connection() as conn:
        if conn is None:
            return {}
        try:
            cursor = conn.cursor()
            # Modify SQL query to ensure all level data is retrieved
            cursor.execute("""
                SELECT 
                    COALESCE(type_level_1, type) as type_level_1,
                    type_level_2,
                    type_level_3,
                    COUNT(*) as count
                FROM parts 
                WHERE COALESCE(type_level_1, type) IS NOT NULL 
                GROUP BY COALESCE(type_level_1, type), type_level_2, type_level_3
                ORDER BY COALESCE(type_level_1, type), type_level_2, type_level_3
            """)
            results = cursor.fetchall()
            
            # Build hierarchy data
            hierarchy = {}
            for row in results:
                level1, level2, level3, count = row
                
                # Process main type
                if level1 not in hierarchy:
                    hierarchy[level1] = {"count": 0, "children": {}}
                hierarchy[level1]["count"] += count
                
                # Process sub type
                if level2:
                    if level2 not in hierarchy[level1]["children"]:
                        hierarchy[level1]["children"][level2] = {"count": 0, "children": {}}
                    hierarchy[level1]["children"][level2]["count"] += count
                    
                    # Process sub type
                    if level3:
                        if level3 not in hierarchy[level1]["children"][level2]["children"]:
                            hierarchy[level1]["children"][level2]["children"][level3] = {"count": count}
                        else:
                            hierarchy[level1]["children"][level2]["children"][level3]["count"] += count
                # Process if no sub type
                elif not level2 and not level3:
                    if "未分类" not in hierarchy[level1]["children"]:
                        hierarchy[level1]["children"]["未分类"] = {"count": count, "children": {}}
                    else:
                        hierarchy[level1]["children"]["未分类"]["count"] += count
            
            return hierarchy
        except Exception as e:
            st.error(f"Failed to get type hierarchy statistics: {str(e)}")
            return {}

# Get part source statistics
@st.cache_data
def get_source_stats():
    with get_connection() as conn:
        if conn is None:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    source_collection,
                    COUNT(*) as count,
                    COUNT(DISTINCT type_level_1) as type_count,
                    AVG(LENGTH(sequence)) as avg_length
                FROM parts 
                WHERE source_collection IS NOT NULL
                GROUP BY source_collection
            """)
            return [
                {
                    "source": row[0],
                    "count": row[1],
                    "type_count": row[2],
                    "avg_length": row[3]
                } for row in cursor.fetchall()
            ]
        except Exception as e:
            st.error(f"Failed to get source statistics: {str(e)}")
            return []

# Get part validation statistics
@st.cache_data
def get_validation_stats():
    with get_connection() as conn:
        if conn is None:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    metadata_validation_state,
                    COUNT(*) as count,
                    COUNT(DISTINCT type_level_1) as type_count
                FROM parts 
                WHERE metadata_validation_state IS NOT NULL
                GROUP BY metadata_validation_state
            """)
            return [
                {
                    "state": row[0],
                    "count": row[1],
                    "type_count": row[2]
                } for row in cursor.fetchall()
            ]
        except Exception as e:
            st.error(f"Failed to get validation statistics: {str(e)}")
            return []

def plot_part_type_distribution(type_stats):
    """Plot part type distribution pie chart"""
    if not type_stats:
        st.warning("No part type data found")
        fig = go.Figure()
        fig.update_layout(title="Part Type Distribution (No Data)")
        return fig
    
    data = []
    for stat in type_stats:
        type_name = stat["_id"] if stat["_id"] else "未分类"
        count = stat["count"]
        data.append({
            "类型": type_name,
            "数量": count
        })
    
    df = pd.DataFrame(data)
    fig = px.pie(
        df,
        values="数量",
        names="类型",
        title="Part Type Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=True)
    return fig

def plot_sequence_length_distribution(length_stats):
    """Plot sequence length distribution"""
    if not length_stats:
        st.warning("No sequence length data found")
        fig = go.Figure()
        fig.update_layout(title="Different Category Part Sequence Length Distribution (No Data)")
        return fig
    
    box_data = []
    for row in length_stats:
        category = row["_id"] if row["_id"] else "未分类"
        lengths = row["lengths"]
        for length in lengths:
            box_data.append({
                "类别": category,
                "序列长度": length
            })
            
    box_df = pd.DataFrame(box_data)
    fig = px.box(
        box_df,
        x="类别",
        y="序列长度",
        title="Different Category Part Sequence Length Distribution",
        color="类别",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_layout(
        xaxis_title="Part Category",
        yaxis_title="Sequence Length (bp)",
        showlegend=True
    )
    return fig

def plot_host_compatibility(host_stats):
    """Plot host compatibility comparison"""
    if not host_stats:
        st.warning("No host compatibility data found")
        fig = go.Figure()
        fig.update_layout(title="Host Compatibility Analysis (No Data)")
        return fig
    
    data = []
    for stat in host_stats:
        host = stat["_id"] if stat["_id"] else "未知"
        count = stat["part_count"]
        type_count = stat["types"]
        data.append({
            "宿主": host,
            "零件数量": count,
            "支持的类型数": type_count
        })
    
    df = pd.DataFrame(data)
    fig = px.bar(
        df,
        x="宿主",
        y="零件数量",
        color="支持的类型数",
        title="Host Compatibility Analysis",
        labels={"零件数量": "零件数量", "支持的类型数": "支持的类型数"},
        color_continuous_scale="Viridis"
    )
    fig.update_layout(
        xaxis_title="Host Type",
        yaxis_title="零件数量",
        showlegend=True
    )
    return fig

def plot_expression_system_stats(expression_stats):
    """Plot expression system statistics"""
    if not expression_stats:
        st.warning("No expression system data found")
        fig = go.Figure()
        fig.update_layout(title="Expression System Analysis (No Data)")
        return fig
    
    data = []
    for stat in expression_stats:
        system = stat["_id"] if stat["_id"] else "未知"
        count = stat["part_count"]
        type_count = stat["types"]
        data.append({
            "表达系统": system,
            "零件数量": count,
            "支持的类型数": type_count
        })
    
    df = pd.DataFrame(data)
    fig = px.bar(
        df,
        x="表达系统",
        y="零件数量",
        color="支持的类型数",
        title="Expression System Analysis",
        labels={"零件数量": "零件数量", "支持的类型数": "支持的类型数"},
        color_continuous_scale="Viridis"
    )
    fig.update_layout(
        xaxis_title="Expression System",
        yaxis_title="零件数量",
        showlegend=True
    )
    return fig

def plot_type_distribution(type_stats):
    """Plot part type distribution pie chart"""
    if not type_stats:
        st.warning("No part type data found")
        fig = go.Figure()
        fig.update_layout(title="Part Type Distribution (No Data)")
        return fig
    
    data = []
    for stat in type_stats:
        if stat["_id"]:  # Only display data with types
            data.append({
                "类型": stat["_id"],
                "数量": stat["count"]
            })
    
    df = pd.DataFrame(data)
    if not df.empty:
        fig = px.pie(
            df,
            values="数量",
            names="类型",
            title="Part Type Distribution",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(showlegend=True)
    else:
        fig = go.Figure()
        fig.update_layout(title="Part Type Distribution (No Data)")
    return fig

def display_type_hierarchy(hierarchy_data):
    """Display type distribution in three columns"""
    st.markdown("### Type Distribution")
    
    if not hierarchy_data:
        st.info("No type distribution data found")
        return
    
    # Convert data to list for group display
    type_list = list(hierarchy_data.items())
    
    # Display 3 types per row
    for i in range(0, len(type_list), 3):
        cols = st.columns(3)
        # Get current row types (max 3)
        current_row = type_list[i:min(i+3, len(type_list))]
        
        # Fill each column
        for col_idx, (level1_type, level1_data) in enumerate(current_row):
            with cols[col_idx]:
                # Create collapsible container with expander, default collapsed
                with st.expander(f"📂 {level1_type} ({level1_data['count']})", expanded=False):
                    if level1_data["children"]:
                        # Sort level 2 types by count in descending order
                        sorted_level2 = sorted(
                            level1_data["children"].items(),
                            key=lambda x: x[1]["count"],
                            reverse=True
                        )
                        for level2_type, level2_data in sorted_level2:
                            st.markdown(f"└── 📁 {level2_type} ({level2_data['count']})")
                            if level2_data["children"]:
                                # Sort level 3 types by count in descending order
                                sorted_level3 = sorted(
                                    level2_data["children"].items(),
                                    key=lambda x: x[1]["count"],
                                    reverse=True
                                )
                                # Display each level 3 type separately
                                for type_name, data in sorted_level3:
                                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;└── {type_name} ({data['count']})")
                    else:
                        st.markdown("└── (No subtypes)")

def plot_source_stats(source_stats):
    """Plot parts source statistics"""
    if not source_stats:
        st.warning("No source data found")
        return None
    
    df = pd.DataFrame(source_stats)
    fig = px.scatter(
        df,
        x="count",
        y="type_count",
        size="avg_length",
        color="source",
        title="Parts Source Analysis",
        labels={
            "count": "Number of Parts",
            "type_count": "Number of Types",
            "avg_length": "Average Sequence Length"
        }
    )
    return fig

def plot_validation_stats(validation_stats):
    """Plot validation status statistics"""
    if not validation_stats:
        st.warning("No validation status data found")
        return None
    
    df = pd.DataFrame(validation_stats)
    fig = px.bar(
        df,
        x="state",
        y="count",
        color="type_count",
        title="Parts Validation Status Analysis",
        labels={
            "state": "Validation Status",
            "count": "Number of Parts",
            "type_count": "Number of Types"
        }
    )
    return fig

# 确保在文件末尾调用 main 函数
if __name__ == "__main__":
    main()