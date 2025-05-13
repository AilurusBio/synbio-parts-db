# -*- coding: utf-8 -*-
# Title: MCP Server

import os
from dotenv import load_dotenv
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import streamlit as st
import json
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading
import time
from pydantic import BaseModel
import sqlite3
from pathlib import Path
from contextlib import contextmanager
import pandas as pd
import sys
import logging

# Add main directory to system path
sys.path.append(str(Path(__file__).parent.parent))

# 从utils导入共享功能
from utils import get_connection

# 从data目录导入搜索功能
# 使用utils中的全局缓存函数
from utils import get_semantic_search_instance

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 使用全局缓存的SemanticSearch实例
@st.cache_resource
def get_searcher():
    """
    获取全局缓存的SemanticSearch实例
    """
    logger.info("Getting cached SemanticSearch instance")
    return get_semantic_search_instance()

# Define data models
class Tool(BaseModel):
    name: str
    description: str
    input_schema: dict

class Resource(BaseModel):
    name: str
    pattern: str
    description: str
    parameters: dict

class Prompt(BaseModel):
    name: str
    template: str
    parameters: dict

class MCPServer:
    def __init__(self):
        self.app = FastAPI(title="MCP Server API")
        self._setup_cors()
        self._setup_routes()
        logger.info("MCPServer initialized")
        
    def _setup_cors(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("CORS middleware setup completed")
        
    def _setup_routes(self):
        logger.info("Setting up API routes")
        
        @self.app.get("/")
        async def root():
            logger.info("Root endpoint accessed")
            return {"message": "Welcome to MCP Server API"}
            
        @self.app.get("/tools")
        async def list_tools():
            logger.info("Tools endpoint accessed")
            tools = {
                "semantic_search": {
                    "name": "semantic_search",
                    "description": "Perform semantic search on parts database",
                    "endpoint": "POST /tools/semantic_search",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query string"},
                            "top_k": {"type": "integer", "description": "Number of results to return", "default": 10},
                            "types": {"type": "array", "items": {"type": "string"}, "description": "Filter by part types"},
                            "source_collections": {"type": "array", "items": {"type": "string"}, "description": "Filter by source collections"}
                        }
                    },
                    "example_request": {
                        "query": "Find strong constitutive promoters for E. coli",
                        "top_k": 5,
                        "types": ["promoter"],
                        "source_collections": ["igem"]
                    },
                    "example_response": {
                        "results": [
                            {
                                "part_id": "BBa_J23100",
                                "name": "Constitutive Promoter",
                                "description": "Strong constitutive promoter",
                                "score": 0.95
                            }
                        ]
                    }
                },
                "part_details": {
                    "name": "part_details",
                    "description": "Get detailed information about a specific part",
                    "endpoint": "GET /parts/{part_id}",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "part_id": {"type": "string", "description": "Unique identifier of the part"}
                        }
                    },
                    "example_request": {
                        "part_id": "BBa_J23100"
                    },
                    "example_response": {
                        "uid": "BBa_J23100",
                        "name": "Constitutive Promoter",
                        "type_level_1": "DNA Elements",
                        "type_level_2": "Regulatory",
                        "description": "Strong constitutive promoter",
                        "sequence": "TTGACGGCTAGCTCAGTCCTAGGTACAGTGCTAGC",
                        "sequence_length": 35,
                        "calculated_gc_content": 52.9,
                        "source_collection": "igem"
                    }
                },
                "part_search": {
                    "name": "part_search",
                    "description": "Search parts with multiple parameters",
                    "endpoint": "POST /parts/search",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "type_level_1": {"type": "string", "description": "Main type of the part"},
                            "type_level_2": {"type": "string", "description": "Subtype of the part"},
                            "source_collection": {"type": "string", "description": "Source of the part"},
                            "limit": {"type": "integer", "description": "Number of results to return", "default": 10},
                            "offset": {"type": "integer", "description": "Offset for pagination", "default": 0}
                        }
                    },
                    "example_request": {
                        "type_level_1": "DNA Elements",
                        "source_collection": "lab",
                        "limit": 5,
                        "offset": 0
                    },
                    "example_response": {
                        "total_count": 100,
                        "parts": [
                            {
                                "uid": "BBa_J23100",
                                "name": "Constitutive Promoter",
                                "type_level_1": "DNA Elements",
                                "type_level_2": "Regulatory",
                                "description": "Strong constitutive promoter",
                                "source_collection": "lab"
                            }
                        ],
                        "available_filters": {
                            "types": ["DNA Elements", "RNA Elements", "Coding Sequences"],
                            "subtypes": ["Regulatory", "Structural", "Enzyme"],
                            "sources": ["lab", "igem", "addgene"]
                        }
                    }
                },
                "statistics": {
                    "name": "statistics",
                    "description": "Get database statistics and available filters",
                    "endpoint": "GET /stats",
                    "input_schema": {
                        "type": "object",
                        "properties": {}
                    },
                    "example_request": {},
                    "example_response": {
                        "total_parts": 19850,
                        "categories": [
                            {"name": "Coding Sequences", "count": 12509},
                            {"name": "DNA Elements", "count": 6666}
                        ],
                        "sub_types": [
                            {"name": "Reporter", "count": 5584},
                            {"name": "Regulatory", "count": 4562}
                        ],
                        "sources": [
                            {"name": "addgene", "count": 12383},
                            {"name": "igem", "count": 4322}
                        ],
                        "type_combinations": [
                            {"type_level_1": "Coding Sequences", "type_level_2": "Reporter", "count": 5584},
                            {"type_level_1": "DNA Elements", "type_level_2": "Regulatory", "count": 4562}
                        ]
                    }
                }
            }
            return {"tools": list(tools.values())}
            
        @self.app.post("/tools/semantic_search")
        async def execute_semantic_search(request: Request):
            try:
                data = await request.json()
                logger.info(f"Semantic search request data: {data}")
                query = data.get("query")
                top_k = data.get("top_k", 10)
                types = data.get("types")
                source_collections = data.get("source_collections")
                optimize = data.get("optimize", True)
                
                if not query:
                    logger.warning("No query provided for semantic search")
                    return {"error": "Query is required"}
                    
                # 使用缓存的搜索器实例
                searcher = get_searcher()
                results = searcher.search(
                    query=query,
                    top_k=top_k,
                    optimize=optimize,
                    types=types if types else None,
                    source_collections=source_collections if source_collections else None
                )
                logger.info(f"Semantic search results: {results}")
                return results
            except Exception as e:
                logger.error(f"Error in semantic search: {str(e)}")
                logger.exception("Full traceback:")
                return {"error": str(e)}
                
        @self.app.get("/parts/{part_id}")
        async def get_part_details(part_id: str):
            try:
                logger.info(f"Getting details for part: {part_id}")
                with get_connection() as conn:
                    if conn is None:
                        logger.error("Database connection failed")
                        return {"error": "Database connection failed"}
                        
                    cursor = conn.cursor()
                    cursor.execute("""
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
                        WHERE uid = ?
                    """, (part_id,))
                    
                    columns = [description[0] for description in cursor.description]
                    part = cursor.fetchone()
                    
                    if part is None:
                        logger.warning(f"Part not found: {part_id}")
                        return {"error": f"Part {part_id} not found"}
                        
                    logger.info(f"Found part: {part}")
                    return dict(zip(columns, part))
            except Exception as e:
                logger.error(f"Error getting part details: {str(e)}")
                logger.exception("Full traceback:")
                return {"error": str(e)}
                
        @self.app.post("/parts/search")
        async def search_parts(
            request: Request,
            part_id: str = None,
            name: str = None,
            type_level_1: str = None,
            type_level_2: str = None,
            source_collection: str = None,
            limit: int = 10,
            offset: int = 0
        ):
            try:
                # 从请求体获取参数
                data = await request.json()
                part_id = data.get("part_id")
                name = data.get("name")
                type_level_1 = data.get("type_level_1")
                type_level_2 = data.get("type_level_2")
                source_collection = data.get("source_collection")
                limit = data.get("limit", 10)
                offset = data.get("offset", 0)
                
                logger.info(f"Request URL: {request.url}")
                logger.info(f"Request body: {data}")
                logger.info(f"Searching parts with params: part_id={part_id}, name={name}, type_level_1={type_level_1}, type_level_2={type_level_2}, source_collection={source_collection}")
                
                with get_connection() as conn:
                    if conn is None:
                        logger.error("Database connection failed")
                        return {"error": "Database connection failed"}
                        
                    cursor = conn.cursor()
                    
                    # 构建基础查询
                    query = """
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
                    
                    # 添加条件
                    conditions = []
                    params = []
                    if type_level_1:
                        conditions.append("type_level_1 = ?")
                        params.append(type_level_1)
                    if source_collection:
                        conditions.append("source_collection = ?")
                        params.append(source_collection)
                        
                    if conditions:
                        query += " WHERE " + " AND ".join(conditions)
                        
                    # 添加分页
                    query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])
                    
                    logger.info(f"Executing query: {query}")
                    logger.info(f"With params: {params}")
                    
                    # 执行查询
                    cursor.execute(query, params)
                    columns = [description[0] for description in cursor.description]
                    parts = cursor.fetchall()
                    
                    logger.info(f"Found {len(parts)} parts")
                    
                    # 获取总记录数
                    count_query = "SELECT COUNT(*) FROM parts"
                    if conditions:
                        count_query += " WHERE " + " AND ".join(conditions)
                    logger.info(f"Executing count query: {count_query}")
                    logger.info(f"With count params: {params[:-2]}")
                    cursor.execute(count_query, params[:-2])
                    total_count = cursor.fetchone()[0]
                    
                    logger.info(f"Total count: {total_count}")
                    
                    # 获取可用的筛选选项
                    cursor.execute("""
                        SELECT type_level_1, COUNT(*) as count 
                        FROM parts 
                        WHERE type_level_1 IS NOT NULL 
                        GROUP BY type_level_1 
                        ORDER BY count DESC
                    """)
                    available_types = [{"name": row[0], "count": row[1]} for row in cursor.fetchall()]
                    
                    cursor.execute("""
                        SELECT type_level_2, COUNT(*) as count 
                        FROM parts 
                        WHERE type_level_2 IS NOT NULL 
                        GROUP BY type_level_2 
                        ORDER BY count DESC
                    """)
                    available_subtypes = [{"name": row[0], "count": row[1]} for row in cursor.fetchall()]
                    
                    cursor.execute("""
                        SELECT source_collection, COUNT(*) as count 
                        FROM parts 
                        WHERE source_collection IS NOT NULL 
                        GROUP BY source_collection 
                        ORDER BY count DESC
                    """)
                    available_sources = [{"name": row[0], "count": row[1]} for row in cursor.fetchall()]
                    
                    logger.info(f"Available filters: types={available_types}, subtypes={available_subtypes}, sources={available_sources}")
                    
                    result = {
                        "total_count": total_count,
                        "parts": [dict(zip(columns, part)) for part in parts],
                        "available_filters": {
                            "types": available_types,
                            "subtypes": available_subtypes,
                            "sources": available_sources
                        }
                    }
                    logger.info(f"Returning result: {result}")
                    return result
            except Exception as e:
                logger.error(f"Error in search_parts: {str(e)}")
                logger.exception("Full traceback:")
                return {
                    "total_count": 0,
                    "parts": [],
                    "available_filters": {
                        "types": [],
                        "subtypes": [],
                        "sources": []
                    }
                }
                
        @self.app.get("/stats")
        async def get_statistics():
            try:
                with get_connection() as conn:
                    if conn is None:
                        return {"error": "Database connection failed"}
                        
                    cursor = conn.cursor()
                    
                    # Get total parts
                    cursor.execute("SELECT COUNT(*) FROM parts")
                    total_parts = cursor.fetchone()[0]
                    
                    # Get main types with counts
                    cursor.execute("""
                        SELECT type_level_1, COUNT(*) as count 
                        FROM parts 
                        WHERE type_level_1 IS NOT NULL 
                        GROUP BY type_level_1 
                        ORDER BY count DESC
                    """)
                    categories = [{"name": row[0], "count": row[1]} for row in cursor.fetchall()]
                    
                    # Get subtypes with counts
                    cursor.execute("""
                        SELECT type_level_2, COUNT(*) as count 
                        FROM parts 
                        WHERE type_level_2 IS NOT NULL 
                        GROUP BY type_level_2 
                        ORDER BY count DESC
                    """)
                    sub_types = [{"name": row[0], "count": row[1]} for row in cursor.fetchall()]
                    
                    # Get sources with counts
                    cursor.execute("""
                        SELECT source_collection, COUNT(*) as count 
                        FROM parts 
                        WHERE source_collection IS NOT NULL 
                        GROUP BY source_collection 
                        ORDER BY count DESC
                    """)
                    sources = [{"name": row[0], "count": row[1]} for row in cursor.fetchall()]
                    
                    # Get type_level_1 and type_level_2 combinations
                    cursor.execute("""
                        SELECT type_level_1, type_level_2, COUNT(*) as count 
                        FROM parts 
                        WHERE type_level_1 IS NOT NULL AND type_level_2 IS NOT NULL 
                        GROUP BY type_level_1, type_level_2 
                        ORDER BY count DESC
                    """)
                    type_combinations = [{"type_level_1": row[0], "type_level_2": row[1], "count": row[2]} for row in cursor.fetchall()]
                    
                    return {
                        "total_parts": total_parts,
                        "categories": categories,
                        "sub_types": sub_types,
                        "sources": sources,
                        "type_combinations": type_combinations
                    }
            except Exception as e:
                logger.error(f"Error in get_statistics: {str(e)}")
                logger.exception("Full traceback:")
                return {"error": str(e)}

# 创建MCPServer实例
mcp_server = MCPServer()
app = mcp_server.app

def main():
    # 设置页面配置，自定义侧边栏显示的名称
    st.set_page_config(
        page_title="MCP Server",
        page_icon="💻",
        layout="wide"
    )
    
    # 添加强制使用浅色主题的CSS样式
    st.markdown("""
    <style>
    /* 强制使用浅色主题，覆盖Streamlit的默认主题切换 */
    html, body, [class*="css"] {
        color: #262730 !important;
        background-color: #FFFFFF !important;
    }
    
    /* 固定浅色主题 */
    .stApp {
        background-color: #FFFFFF !important;
    }
    
    /* 确保所有文本使用深色 */
    .stMarkdown, p, h1, h2, h3, h4, h5, h6, span, div {
        color: #262730 !important;
    }
    
    /* 确保所有卡片使用浅色背景 */
    .stTabs [data-baseweb="tab-panel"], div.stBlock {
        background-color: #F0F2F6 !important;
    }
    
    /* 确保侧边栏使用浅色背景 */
    .css-1d391kg, .css-1lcbmhc, .css-12oz5g7 {
        background-color: #F0F2F6 !important;
    }
    
    /* 确保按钮和输入框使用浅色主题 */
    .stButton>button, .stTextInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #FFFFFF !important;
        color: #262730 !important;
        border-color: #CCC !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("MCP Server API Documentation")
    
    # Start FastAPI server in a separate thread
    if not hasattr(st.session_state, 'server_started'):
        st.session_state.server_started = True
        server_thread = threading.Thread(target=start_server)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(1)  # 等待服务器启动
    
    # API Overview
    st.markdown("""
    ## API Overview
    
    MCP Server provides the following API endpoints:
    
    ### Base Endpoints
    - `GET /` - Welcome page
    - `GET /tools` - List all available tools
    - `GET /stats` - Get database statistics
    
    ### Tool Endpoints
    - `POST /tools/semantic_search` - Perform semantic search
    - `GET /parts/{part_id}` - Get part details by ID
    - `POST /parts/search` - Search parts with multiple parameters
    
    ### Authentication
    All API requests require a valid authentication token in the header:
    ```
    Authorization: Bearer <token>
    ```
    """)
    
    # API Documentation
    st.markdown("""
    ## API Documentation
    
    ### List Available Tools API
    
    ```http
    GET /tools
    ```
    
    Returns a list of all available tools with their descriptions, input schemas, and examples.
    
    Example Response:
    ```json
    {
        "tools": [
            {
                "name": "semantic_search",
                "description": "Perform semantic search on parts database",
                "endpoint": "POST /tools/semantic_search",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query string"},
                        "top_k": {"type": "integer", "description": "Number of results to return", "default": 10},
                        "types": {"type": "array", "items": {"type": "string"}, "description": "Filter by part types"},
                        "source_collections": {"type": "array", "items": {"type": "string"}, "description": "Filter by source collections"}
                    }
                },
                "example_request": {
                    "query": "Find strong constitutive promoters for E. coli",
                    "top_k": 5,
                    "types": ["promoter"],
                    "source_collections": ["igem"]
                },
                "example_response": {
                    "results": [
                        {
                            "part_id": "BBa_J23100",
                            "name": "Constitutive Promoter",
                            "description": "Strong constitutive promoter",
                            "score": 0.95
                        }
                    ]
                }
            },
            {
                "name": "part_details",
                "description": "Get detailed information about a specific part",
                "endpoint": "GET /parts/{part_id}",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "part_id": {"type": "string", "description": "Unique identifier of the part"}
                    }
                },
                "example_request": {
                    "part_id": "BBa_J23100"
                },
                "example_response": {
                    "uid": "BBa_J23100",
                    "name": "Constitutive Promoter",
                    "type_level_1": "DNA Elements",
                    "type_level_2": "Regulatory",
                    "description": "Strong constitutive promoter",
                    "sequence": "TTGACGGCTAGCTCAGTCCTAGGTACAGTGCTAGC",
                    "sequence_length": 35,
                    "calculated_gc_content": 52.9,
                    "source_collection": "igem"
                }
            },
            {
                "name": "part_search",
                "description": "Search parts with multiple parameters",
                "endpoint": "POST /parts/search",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "type_level_1": {"type": "string", "description": "Main type of the part"},
                        "type_level_2": {"type": "string", "description": "Subtype of the part"},
                        "source_collection": {"type": "string", "description": "Source of the part"},
                        "limit": {"type": "integer", "description": "Number of results to return", "default": 10},
                        "offset": {"type": "integer", "description": "Offset for pagination", "default": 0}
                    }
                },
                "example_request": {
                    "type_level_1": "DNA Elements",
                    "source_collection": "lab",
                    "limit": 5,
                    "offset": 0
                },
                "example_response": {
                    "total_count": 100,
                    "parts": [
                        {
                            "uid": "BBa_J23100",
                            "name": "Constitutive Promoter",
                            "type_level_1": "DNA Elements",
                            "type_level_2": "Regulatory",
                            "description": "Strong constitutive promoter",
                            "source_collection": "lab"
                        }
                    ],
                    "available_filters": {
                        "types": ["DNA Elements", "RNA Elements", "Coding Sequences"],
                        "subtypes": ["Regulatory", "Structural", "Enzyme"],
                        "sources": ["lab", "igem", "addgene"]
                    }
                }
            },
            {
                "name": "statistics",
                "description": "Get database statistics and available filters",
                "endpoint": "GET /stats",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                },
                "example_request": {},
                "example_response": {
                    "total_parts": 19850,
                    "categories": [
                        {"name": "Coding Sequences", "count": 12509},
                        {"name": "DNA Elements", "count": 6666}
                    ],
                    "sub_types": [
                        {"name": "Reporter", "count": 5584},
                        {"name": "Regulatory", "count": 4562}
                    ],
                    "sources": [
                        {"name": "addgene", "count": 12383},
                        {"name": "igem", "count": 4322}
                    ],
                    "type_combinations": [
                        {"type_level_1": "Coding Sequences", "type_level_2": "Reporter", "count": 5584},
                        {"type_level_1": "DNA Elements", "type_level_2": "Regulatory", "count": 4562}
                    ]
                }
            }
        ]
    }
    ```
    """)
    
    if st.button("Test List Tools"):
        result = test_endpoint("/tools")
        st.json(result)
    
    if st.button("Test Semantic Search"):
        data = {
            "query": "Find strong constitutive promoters for E. coli",
            "top_k": 5
        }
        result = test_endpoint("/tools/semantic_search", "POST", data)
        st.json(result)
    
    st.markdown("""
    ### Part Search API
    
    ```http
    POST /parts/search
    ```
    
    Request Example:
    ```json
    {
        "type_level_1": "DNA Elements",
        "source_collection": "lab",
        "limit": 5,
        "offset": 0
    }
    ```
    
    Returns:
    ```json
    {
        "total_count": 100,
        "parts": [...],
        "available_filters": {
            "types": ["promoter", "terminator", "RBS"],
            "subtypes": ["constitutive", "inducible"],
            "sources": ["igem", "addgene"]
        }
    }
    ```
    """)
    
    if st.button("Test Part Search"):
        data = {
            "type_level_1": "DNA Elements",
            "source_collection": "lab",
            "limit": 5
        }
        result = test_endpoint("/parts/search", "POST", data)
        st.json(result)
    
    st.markdown("""
    ### Statistics API
    
    ```http
    GET /stats
    ```
    
    Returns:
    ```json
    {
        "total_parts": 1000,
        "categories": ["promoter", "terminator", "RBS"],
        "sub_types": ["constitutive", "inducible"],
        "sources": ["igem", "addgene"]
    }
    ```
    """)
    
    if st.button("Test Statistics"):
        result = test_endpoint("/stats")
        st.json(result)

def start_server():
    """Start the FastAPI server"""
    uvicorn.run(app, host="0.0.0.0", port=8000)

def test_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    try:
        headers = {"Authorization": f"Bearer {os.getenv('MCP_SERVER_TOKEN')}"}
        url = f"http://localhost:8000{endpoint}"
        
        logger.info(f"Testing endpoint: {url}")
        logger.info(f"Method: {method}")
        logger.info(f"Headers: {headers}")
        if data:
            logger.info(f"Data: {data}")
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        else:
            response = requests.post(url, headers=headers, json=data)
            
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response content: {response.text}")
        
        return response.json()
    except Exception as e:
        logger.error(f"Error in test_endpoint: {str(e)}")
        logger.exception("Full traceback:")
        return {"error": str(e)}

# 测试API
def test_api():
    headers = {"Authorization": f"Bearer {os.getenv('MCP_SERVER_TOKEN')}"}
    response = requests.get("http://localhost:8000/api/v1/parts", headers=headers)
    print(response.json())

if __name__ == "__main__":
    main() 