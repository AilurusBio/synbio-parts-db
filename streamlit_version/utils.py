import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import streamlit as st
import pandas as pd
import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager
from sentence_transformers import SentenceTransformer
import numpy as np
import lancedb
import pickle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize vector model and index
@st.cache_resource
def init_embeddings():
    try:
        # Load model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        with get_connection() as conn:
            if conn is not None:
                # Get sequence descriptions and category data
                query = """
                    SELECT 
                        uid,
                        name,
                        description,
                        type_level_1,
                        type_level_2,
                        type_level_3,
                        metadata_organism,
                        metadata_expression_system,
                        metadata_validation_state
                    FROM parts
                """
                df = pd.read_sql_query(query, conn)
                
                # Combine text features
                texts = []
                for _, row in df.iterrows():
                    text = f"{row['name']} {row['description']} {row['type_level_1']} {row['type_level_2']} {row['type_level_3']} {row['metadata_organism']} {row['metadata_expression_system']}"
                    texts.append(text)
                
                # Generate vectors
                embeddings = model.encode(texts)
                
                # Initialize LanceDB
                db_path = Path("streamlit_version/data/parts.lance")
                db = lancedb.connect(db_path)
                
                # Create table with embeddings
                data = []
                for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                    data.append({
                        "vector": embedding,
                        "text": text,
                        "name": df.iloc[i]["name"],
                        "description": df.iloc[i]["description"],
                        "type": df.iloc[i]["type_level_1"],
                        "source_collection": "lab"  # 默认值，可以根据需要修改
                    })
                
                table = db.create_table("embeddings", data=data)
                
                # Save data
                data = {
                    'db': db,
                    'table': table,
                    'df': df,
                    'model': model
                }
                
                # Save to file
                index_path = Path("streamlit_version/data/search_index.pkl")
                with open(index_path, 'wb') as f:
                    pickle.dump(data, f)
                
                return data
    except Exception as e:
        logger.error(f"Error initializing embeddings: {str(e)}")
        return None

@st.cache_resource
def get_embeddings_data():
    """Get embeddings data from cache or initialize if not exists"""
    try:
        index_path = Path("streamlit_version/data/search_index.pkl")
        if index_path.exists():
            with open(index_path, 'rb') as f:
                return pickle.load(f)
        else:
            return init_embeddings()
    except Exception as e:
        logger.error(f"Error loading embeddings data: {str(e)}")
        return None

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