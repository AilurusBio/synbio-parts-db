import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import sqlite3
import pickle
import numpy as np
import logging
from contextlib import contextmanager
import plotly.express as px
import plotly.graph_objects as go
import json

# Add main directory to system path
sys.path.append(str(Path(__file__).parent.parent))
from Home import get_embeddings_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Get filter options
@st.cache_data
def get_filter_options():
    """Get filter options"""
    with get_connection() as conn:
        if conn is None:
            return {
                "main_types": [],
                "collections": [],
                "validation_status": [],
                "status": []
            }
        try:
            cursor = conn.cursor()
            
            # Get main types
            cursor.execute("SELECT DISTINCT type_level_1 FROM parts WHERE type_level_1 IS NOT NULL")
            main_types = [row[0] for row in cursor.fetchall()]
            
            # Get source collections
            cursor.execute("SELECT DISTINCT source_collection FROM parts WHERE source_collection IS NOT NULL")
            collections = [row[0] for row in cursor.fetchall()]
            
            # Get validation status
            cursor.execute("SELECT DISTINCT source_validation_status FROM parts WHERE source_validation_status IS NOT NULL")
            validation_status = [row[0] for row in cursor.fetchall()]
            
            # Get part status
            cursor.execute("SELECT DISTINCT status FROM parts WHERE status IS NOT NULL")
            status = [row[0] for row in cursor.fetchall()]
            
            return {
                "main_types": sorted(main_types),
                "collections": sorted(collections),
                "validation_status": sorted(validation_status),
                "status": sorted(status)
            }
        except Exception as e:
            st.error(f"Failed to get filter options: {str(e)}")
            return {
                "main_types": [],
                "collections": [],
                "validation_status": [],
                "status": []
            }

# Build query conditions
def build_query(filters):
    """Build query conditions"""
    conditions = []
    params = []
    
    if filters.get("main_types"):
        placeholders = ",".join("?" * len(filters["main_types"]))
        conditions.append(f"type_level_1 IN ({placeholders})")
        params.extend(filters["main_types"])
        
    if filters.get("collections"):
        placeholders = ",".join("?" * len(filters["collections"]))
        conditions.append(f"source_collection IN ({placeholders})")
        params.extend(filters["collections"])
        
    if filters.get("validation_status"):
        placeholders = ",".join("?" * len(filters["validation_status"]))
        conditions.append(f"source_validation_status IN ({placeholders})")
        params.extend(filters["validation_status"])
        
    if filters.get("status"):
        placeholders = ",".join("?" * len(filters["status"]))
        conditions.append(f"status IN ({placeholders})")
        params.extend(filters["status"])
        
    if filters.get("search_text"):
        search_text = f"%{filters['search_text']}%"
        conditions.append("""(
            uid LIKE ? OR 
            name LIKE ? OR 
            description LIKE ?
        )""")
        params.extend([search_text] * 3)
    
    base_query = """
        SELECT *,
            LENGTH(sequence) as sequence_length,
            CASE 
                WHEN sequence IS NOT NULL 
                THEN CAST(
                    (LENGTH(sequence) - LENGTH(REPLACE(UPPER(sequence), 'G', '')) 
                    - LENGTH(REPLACE(UPPER(sequence), 'C', ''))) 
                    * 100.0 / LENGTH(sequence) AS REAL)
                ELSE NULL 
            END as calculated_gc_content
        FROM parts
    """
    
    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)
        return base_query + where_clause, params
    return base_query, params

# Get parts data
@st.cache_data
def get_parts_data(query, params, page=1, per_page=10):
    with get_connection() as conn:
        if conn is None:
            return [], 0
        try:
            cursor = conn.cursor()
            
            # Get total count
            count_query = f"SELECT COUNT(DISTINCT uid) FROM ({query}) as p"
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            # Get current page data
            paginated_query = query + f" LIMIT {per_page} OFFSET {(page - 1) * per_page}"
            cursor.execute(paginated_query, params)
            columns = [description[0] for description in cursor.description]
            parts = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return parts, total
        except Exception as e:
            st.error(f"Failed to get parts data: {str(e)}")
            return [], 0

def display_part_details(part):
    """Display part details"""
    # Create three-column layout
    col1, col2, col3 = st.columns(3)
    
    # Column 1: Basic Information
    with col1:
        st.markdown("#### Basic Information")
        st.markdown(f"""
        - **ID**: {part['uid']}
        - **Name**: {part.get('name', 'Unnamed')}
        - **Status**: {part.get('status', 'Unknown')}
        - **Version**: {part.get('version', 'Unknown')}
        """)
    
    # Column 2: Type Information
    with col2:
        st.markdown("#### Type Information")
        st.markdown(f"""
        - **Level 1**: {part.get('type_level_1', 'Unknown')}
        - **Level 2**: {part.get('type_level_2', 'Unknown')}
        - **Level 3**: {part.get('type_level_3', 'Unknown')}
        """)
    
    # Column 3: Source Information
    with col3:
        st.markdown("#### Source Information")
        st.markdown(f"""
        - **Collection**: {part.get('source_collection', 'Unknown')}
        - **Validation Status**: {part.get('source_validation_status', 'Unknown')}
        """)
    
    # Sequence Information (New Row)
    if part.get('sequence'):
        st.markdown("#### Sequence Information")
        # Create three columns for sequence statistics
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        with stat_col1:
            st.metric("Sequence Length", f"{part.get('sequence_length', 0)} bp")
        with stat_col2:
            # Fix GC content calculation
            sequence = part.get('sequence', '')
            if sequence:
                g_count = sequence.upper().count('G')
                c_count = sequence.upper().count('C')
                gc_content = (g_count + c_count) * 100.0 / len(sequence)
            else:
                gc_content = 0
            st.metric("GC Content", f"{gc_content:.2f}%")
        
        # Sequence display (scrollable)
        st.markdown("##### Sequence")
        st.code(part.get('sequence', ''), language='text')
    
    # Metadata Information (New Row, Two Columns)
    meta_col1, meta_col2 = st.columns(2)
    with meta_col1:
        st.markdown("#### Host Information")
        st.markdown(f"""
        - **Organism**: {part.get('metadata_organism', 'Unknown')}
        - **Expression System**: {part.get('metadata_expression_system', 'Unknown')}
        """)
    with meta_col2:
        st.markdown("#### Additional Information")
        st.markdown(f"""
        - **Safety Level**: {part.get('metadata_safety_level', 'Unknown')}
        - **Last Modified**: {part.get('last_modified', 'Unknown')}
        """)
    
    # Description (if available)
    if part.get('description'):
        st.markdown("#### Description")
        st.markdown(part['description'])

def export_to_fasta(parts):
    """Export parts to FASTA format"""
    fasta_content = ""
    for part in parts:
        fasta_content += f">{part['uid']} {part.get('name', 'Unnamed')}\n"
        if part.get('sequence'):
            fasta_content += f"{part['sequence']}\n"
    return fasta_content

def export_to_json(parts):
    """Export parts to JSON format"""
    return json.dumps(parts, indent=2)

def main():
    st.title("Sequence Search")
    
    # Create left-right two-column layout
    filter_col, table_col = st.columns([1, 3])
    
    with filter_col:
        st.markdown("### 🔍 Filter Criteria")
        
        # Filter by type
        st.markdown("#### Filter by Type")
        with get_connection() as conn:
            if conn is not None:
                # Get all types
                types_df = pd.read_sql("""
                    SELECT DISTINCT type_level_1, type_level_2, type_level_3
                    FROM parts
                    WHERE type_level_1 IS NOT NULL
                """, conn)
                
                # Create filters
                selected_type1 = st.selectbox(
                    "Main Type",
                    options=["All"] + list(types_df["type_level_1"].unique())
                )
                
                if selected_type1 != "All":
                    type2_options = types_df[
                        types_df["type_level_1"] == selected_type1
                    ]["type_level_2"].unique()
                    selected_type2 = st.selectbox(
                        "Subtype",
                        options=["All"] + list(filter(pd.notna, type2_options))
                    )
                
                    if selected_type2 != "All":
                        type3_options = types_df[
                            (types_df["type_level_1"] == selected_type1) &
                            (types_df["type_level_2"] == selected_type2)
                        ]["type_level_3"].unique()
                        selected_type3 = st.selectbox(
                            "Detailed Type",
                            options=["All"] + list(filter(pd.notna, type3_options))
                        )
        
        # Filter by features
        st.markdown("#### Filter by Features")
        min_length = st.number_input("Minimum Sequence Length", value=0)
        max_length = st.number_input("Maximum Sequence Length", value=10000)
        min_gc = st.slider("Minimum GC Content (%)", 0, 100, 0)
        max_gc = st.slider("Maximum GC Content (%)", 0, 100, 100)
    
    with table_col:
        # Build query
        query = """
            SELECT *,
                LENGTH(sequence) as sequence_length,
                CAST(
                    (LENGTH(REPLACE(UPPER(sequence), 'G', '')) + LENGTH(REPLACE(UPPER(sequence), 'C', ''))) 
                    * 100.0 / LENGTH(sequence) AS REAL
                ) as gc_content
            FROM parts
            WHERE sequence IS NOT NULL
        """
        params = []
        
        # Add filter conditions
        if selected_type1 != "All":
            query += " AND type_level_1 = ?"
            params.append(selected_type1)
            if selected_type2 != "All":
                query += " AND type_level_2 = ?"
                params.append(selected_type2)
                if selected_type3 != "All":
                    query += " AND type_level_3 = ?"
                    params.append(selected_type3)
        
        if min_length > 0 or max_length < 10000:
            query += " AND LENGTH(sequence) BETWEEN ? AND ?"
            params.extend([min_length, max_length])
        
        if min_gc > 0 or max_gc < 100:
            query += """ 
                AND (
                    (LENGTH(REPLACE(UPPER(sequence), 'G', '')) + LENGTH(REPLACE(UPPER(sequence), 'C', ''))) 
                    * 100.0 / LENGTH(sequence) BETWEEN ? AND ?
                )
            """
            params.extend([min_gc, max_gc])
        
        # Execute query and display results
        try:
            # Get data
            with get_connection() as conn:
                if conn is not None:
                    df = pd.read_sql_query(query, conn, params=params)
                    
                    if not df.empty:
                        # Pagination settings
                        items_per_page = 10
                        total_pages = (len(df) + items_per_page - 1) // items_per_page
                        page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
                        start_idx = (page - 1) * items_per_page
                        end_idx = min(start_idx + items_per_page, len(df))
                        
                        st.markdown(f"##### Found {len(df)} matching parts (Page {page}/{total_pages})")
                        
                        # Rename columns for display
                        df_display = df.copy()
                        display_columns = [
                            'uid', 'name', 'type_level_1', 'type_level_2', 'type_level_3', 
                            'sequence_length', 'source_collection', 
                            'source_validation_status'
                        ]
                        df_display = df_display[display_columns]
                        df_display.columns = [
                            'ID', 'Name', 'Level 1', 'Level 2', 'Level 3', 
                            'Sequence Length', 'Source', 'Validation Status'
                        ]
                        
                        # Display current page data
                        df_page = df_display.iloc[start_idx:end_idx].copy()
                        df_page.reset_index(drop=True, inplace=True)
                        
                        # Add selection box for detailed view
                        selected_id = st.selectbox(
                            "Select part to view",
                            options=df_page['ID'].tolist(),
                            format_func=lambda x: f"{x} - {df_page[df_page['ID'] == x]['Name'].iloc[0]}"
                        )
                        
                        # Use st.data_editor to display selectable table
                        selection = st.data_editor(
                            df_page,
                            hide_index=True,
                            column_config={
                                "ID": st.column_config.TextColumn(
                                    "ID",
                                    width="medium",
                                ),
                                "Name": st.column_config.TextColumn(
                                    "Name",
                                    width="medium",
                                ),
                            },
                            use_container_width=True,
                            num_rows="dynamic"
                        )
                        
                        # Display selected part details
                        if selected_id:
                            selected_part = df[df['uid'] == selected_id].iloc[0].to_dict()
                            st.markdown("### Part Details")
                            display_part_details(selected_part)
                        
                        # Export functionality
                        if selection is not None and len(selection) > 0:
                            selected_ids = selection['ID'].tolist()
                            selected_parts = df[df['uid'].isin(selected_ids)].to_dict('records')
                            
                            if selected_parts:
                                st.markdown("### Export Selected Parts")
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("Export as FASTA"):
                                        fasta_content = export_to_fasta(selected_parts)
                                        st.download_button(
                                            label="Download FASTA",
                                            data=fasta_content,
                                            file_name="selected_parts.fasta",
                                            mime="text/plain"
                                        )
                                
                                with col2:
                                    if st.button("Export as JSON"):
                                        json_content = export_to_json(selected_parts)
                                        st.download_button(
                                            label="Download JSON",
                                            data=json_content,
                                            file_name="selected_parts.json",
                                            mime="application/json"
                                        )
                    else:
                        st.info("No matching parts found")
        except Exception as e:
            st.error(f"Query execution failed: {str(e)}")

if __name__ == "__main__":
    main() 