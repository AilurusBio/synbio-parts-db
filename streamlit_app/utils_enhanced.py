"""
SynVectorDB githubshare - Enhanced Utilities with Local Vector Support
支持DuckDB数据库和本地向量计算的增强工具函数
"""

import sqlite3
import duckdb
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Tuple
import streamlit as st

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 尝试导入向量计算相关库
try:
    from sentence_transformers import SentenceTransformer
    VECTOR_SUPPORT = True
    logger.info("Vector support enabled with sentence-transformers")
except ImportError:
    VECTOR_SUPPORT = False
    logger.warning("Vector support disabled - sentence-transformers not available")

try:
    import faiss
    FAISS_SUPPORT = True
    logger.info("FAISS support enabled")
except ImportError:
    FAISS_SUPPORT = False
    logger.warning("FAISS support disabled - faiss not available")

# 全局变量
_embedding_model = None
_vector_index = None
_vector_data = None

@st.cache_resource
def get_embedding_model():
    """获取或初始化嵌入模型"""
    global _embedding_model
    if _embedding_model is None and VECTOR_SUPPORT:
        try:
            # 使用本地缓存的模型 - 使用相对路径避免跨平台问题
            cache_dir = Path("streamlit_app/models").resolve()
            model_name = "all-MiniLM-L6-v2"
            
            logger.info(f"Loading embedding model from local cache: {model_name}")
            logger.info(f"Cache directory: models/")
            
            # 检查本地模型是否存在
            model_dir = cache_dir / f"models--sentence-transformers--{model_name}"
            if model_dir.exists():
                logger.info(f"Found local model in cache")
                _embedding_model = SentenceTransformer(
                    model_name,
                    cache_folder=str(cache_dir),
                    local_files_only=True,
                    device='cpu'
                )
                logger.info(f"Embedding model loaded successfully from local cache: {model_name}")
            else:
                logger.warning(f"Local model not found at {model_dir}, trying online download")
                # 备用：尝试在线下载
                _embedding_model = SentenceTransformer(model_name, device='cpu')
                logger.info(f"Embedding model loaded from online: {model_name}")
                
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            _embedding_model = None
    return _embedding_model

@contextmanager
def get_duckdb_connection():
    """
    DuckDB数据库连接上下文管理器
    """
    conn = None
    try:
        # 尝试不同的可能路径
        possible_paths = [
            Path("../data/parts.duckdb"),
            Path("data/parts.duckdb"),
            Path("./data/parts.duckdb")
        ]
        
        db_path = None
        for path in possible_paths:
            if path.exists():
                db_path = path
                break
        
        if db_path is None:
            logger.error(f"DuckDB file not found in any of: {possible_paths}")
            yield None
            return
        
        conn = duckdb.connect(str(db_path))
        logger.info(f"DuckDB连接成功: {db_path}")
        yield conn
    except Exception as e:
        logger.error(f"DuckDB连接失败: {e}")
        yield None
    finally:
        if conn:
            conn.close()

@contextmanager
def get_sqlite_connection():
    """
    SQLite数据库连接上下文管理器（备用）
    """
    conn = None
    try:
        possible_paths = [
            Path("../data/parts.db"),
            Path("data/parts.db"),
            Path("./data/parts.db")
        ]
        
        db_path = None
        for path in possible_paths:
            if path.exists():
                db_path = path
                break
        
        if db_path is None:
            logger.error(f"SQLite file not found in any of: {possible_paths}")
            yield None
            return
        
        conn = sqlite3.connect(str(db_path))
        logger.info(f"SQLite连接成功: {db_path}")
        yield conn
    except Exception as e:
        logger.error(f"SQLite连接失败: {e}")
        yield None
    finally:
        if conn:
            conn.close()

@contextmanager
def get_db_connection():
    """
    智能数据库连接，优先使用DuckDB，备用SQLite
    """
    # 首先尝试DuckDB
    try:
        with get_duckdb_connection() as conn:
            if conn is not None:
                yield conn
                return
    except Exception as e:
        logger.warning(f"DuckDB connection failed, trying SQLite: {e}")
    
    # 备用SQLite
    with get_sqlite_connection() as conn:
        yield conn

def get_basic_stats():
    """获取基础统计信息"""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return {"error": "数据库连接失败"}
            
            # 基础统计
            total_parts = conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
            
            # 类型统计
            type_stats = conn.execute("""
                SELECT type_level_1, COUNT(*) as count 
                FROM parts 
                WHERE type_level_1 IS NOT NULL 
                GROUP BY type_level_1 
                ORDER BY count DESC
            """).fetchall()
            
            # 来源统计
            source_stats = conn.execute("""
                SELECT source_collection, COUNT(*) as count 
                FROM parts 
                WHERE source_collection IS NOT NULL 
                GROUP BY source_collection 
                ORDER BY count DESC
            """).fetchall()
            
            # 物种统计（如果有的话）
            try:
                organism_stats = conn.execute("""
                    SELECT metadata_organism, COUNT(*) as count 
                    FROM parts 
                    WHERE metadata_organism IS NOT NULL 
                    GROUP BY metadata_organism 
                    ORDER BY count DESC
                    LIMIT 10
                """).fetchall()
            except:
                organism_stats = []
            
            return {
                "total_parts": total_parts,
                "type_stats": type_stats,
                "source_stats": source_stats,
                "organism_stats": organism_stats,
                "status": "success"
            }
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return {"error": str(e)}

def get_parts_sample(limit=10):
    """获取部件样本数据"""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return []
            
            query = """
                SELECT uid, name, description, type_level_1, type_level_2, 
                       source_collection, LENGTH(sequence) as sequence_length,
                       metadata_organism
                FROM parts 
                WHERE name IS NOT NULL 
                ORDER BY RANDOM() 
                LIMIT ?
            """
            
            df = pd.read_sql_query(query, conn, params=[limit])
            return df.to_dict('records')
    except Exception as e:
        logger.error(f"获取部件样本失败: {e}")
        return []

def search_parts(query="", type_filter="", source_filter="", organism_filter="", limit=20):
    """增强的部件搜索功能"""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return []
            
            sql = """
                SELECT uid, name, description, type_level_1, type_level_2, 
                       source_collection, LENGTH(sequence) as sequence_length,
                       metadata_organism
                FROM parts 
                WHERE 1=1
            """
            params = []
            
            if query:
                sql += " AND (name LIKE ? OR description LIKE ?)"
                params.extend([f"%{query}%", f"%{query}%"])
            
            if type_filter:
                sql += " AND type_level_1 = ?"
                params.append(type_filter)
            
            if source_filter:
                sql += " AND source_collection = ?"
                params.append(source_filter)
            
            if organism_filter:
                sql += " AND metadata_organism = ?"
                params.append(organism_filter)
            
            sql += " ORDER BY name LIMIT ?"
            params.append(limit)
            
            df = pd.read_sql_query(sql, conn, params=params)
            return df.to_dict('records')
    except Exception as e:
        logger.error(f"搜索部件失败: {e}")
        return []

def get_part_details(uid: str) -> Optional[Dict[str, Any]]:
    """获取单个部件的详细信息"""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return None
            
            query = """
                SELECT * FROM parts WHERE uid = ?
            """
            
            df = pd.read_sql_query(query, conn, params=[uid])
            if len(df) == 0:
                return None
            
            return df.iloc[0].to_dict()
    except Exception as e:
        logger.error(f"获取部件详情失败: {e}")
        return None

@st.cache_data
def get_all_parts_for_vectors():
    """获取所有部件用于向量计算（缓存结果）"""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return pd.DataFrame()
            
            # 首先检查是否有预构建的embeddings表
            try:
                # 检查embeddings表是否存在
                tables = conn.execute("SHOW TABLES").fetchall()
                table_names = [table[0] for table in tables]
                
                if 'embeddings' in table_names:
                    logger.info("Found pre-built embeddings table, loading vectors from DuckDB")
                    query = """
                        SELECT id, name, description, type_level_1, type_level_2, 
                               source_collection, vector
                        FROM embeddings 
                        WHERE vector IS NOT NULL
                        ORDER BY id
                    """
                    df = pd.read_sql_query(query, conn)
                    logger.info(f"Loaded {len(df)} parts with pre-built vectors from DuckDB")
                    return df
                    
            except Exception as e:
                logger.warning(f"Could not load from embeddings table: {e}")
            
            # 回退到原始方法
            query = """
                SELECT uid, name, description, type_level_1, type_level_2, 
                       source_collection, metadata_organism
                FROM parts 
                WHERE name IS NOT NULL AND description IS NOT NULL
                ORDER BY uid
            """
            
            df = pd.read_sql_query(query, conn)
            
            logger.info(f"Loaded {len(df)} parts for vector computation")
            return df
    except Exception as e:
        logger.error(f"获取部件向量数据失败: {e}")
        return pd.DataFrame()

def compute_embeddings(texts: List[str]) -> Optional[np.ndarray]:
    """计算文本嵌入向量"""
    if not VECTOR_SUPPORT:
        logger.warning("Vector support not available")
        return None
    
    model = get_embedding_model()
    if model is None:
        logger.warning("Embedding model not available")
        return None
    
    try:
        embeddings = model.encode(texts, show_progress_bar=True)
        logger.info(f"Computed embeddings for {len(texts)} texts")
        return embeddings
    except Exception as e:
        logger.error(f"计算嵌入向量失败: {e}")
        return None

def save_vector_index(index, df, cache_dir):
    """保存向量索引到文件"""
    try:
        import pickle
        import json
        
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(exist_ok=True)
        
        # 保存FAISS索引
        if FAISS_SUPPORT and index is not None:
            import faiss
            faiss.write_index(index, str(cache_dir / "vector_index.faiss"))
        
        # 保存DataFrame
        df.to_pickle(cache_dir / "vector_data.pkl")
        
        # 保存元数据
        metadata = {
            "parts_count": len(df),
            "created_at": str(pd.Timestamp.now()),
            "model_name": "all-MiniLM-L6-v2"
        }
        with open(cache_dir / "index_metadata.json", "w") as f:
            json.dump(metadata, f)
        
        logger.info(f"Vector index saved to {cache_dir}")
        return True
    except Exception as e:
        logger.error(f"Failed to save vector index: {e}")
        return False

def load_vector_index(cache_dir):
    """从文件加载向量索引"""
    try:
        import json
        
        cache_dir = Path(cache_dir)
        
        # 检查文件是否存在
        faiss_file = cache_dir / "vector_index.faiss"
        data_file = cache_dir / "vector_data.pkl"
        meta_file = cache_dir / "index_metadata.json"
        
        if not all([faiss_file.exists(), data_file.exists(), meta_file.exists()]):
            return None, None
        
        # 加载元数据
        with open(meta_file, "r") as f:
            metadata = json.load(f)
        
        logger.info(f"Loading cached vector index: {metadata['parts_count']} parts")
        
        # 加载DataFrame
        df = pd.read_pickle(data_file)
        
        # 加载FAISS索引
        index = None
        if FAISS_SUPPORT and faiss_file.exists():
            import faiss
            index = faiss.read_index(str(faiss_file))
        
        logger.info("✅ Vector index loaded from cache")
        return index, df
        
    except Exception as e:
        logger.error(f"Failed to load vector index: {e}")
        return None, None

@st.cache_resource
def build_vector_index():
    """构建向量索引（缓存结果）"""
    global _vector_index, _vector_data
    
    # 尝试从文件加载缓存的索引
    cache_dir = Path("streamlit_app/vector_cache").resolve()
    
    cached_index, cached_df = load_vector_index(cache_dir)
    if cached_index is not None and cached_df is not None:
        _vector_index = cached_index
        _vector_data = cached_df
        return cached_index, cached_df
    
    if not VECTOR_SUPPORT:
        logger.warning("Vector support not available for index building")
        return None, None
    
    # 获取所有部件数据
    df = get_all_parts_for_vectors()
    if df.empty:
        logger.warning("No data available for vector index")
        return None, None
    
    # 检查是否有预构建向量
    if 'vector' in df.columns:
        logger.info("Using pre-built vectors from DuckDB")
        # 将向量列转换为numpy数组，确保数据类型正确
        embeddings = np.array([list(vector) for vector in df['vector']], dtype=np.float32)
        logger.info(f"Loaded pre-built embeddings: {embeddings.shape}")
    else:
        # 构建新索引
        logger.info("Building fresh vector index...")
        texts = []
        for _, row in df.iterrows():
            text = f"{row['name']} {row['description']}"
            texts.append(text)
        
        embeddings = compute_embeddings(texts)
        
        if embeddings is None:
            logger.warning("Failed to compute embeddings")
            return None, None
    
    # 构建FAISS索引（如果可用）
    index = None
    if FAISS_SUPPORT:
        try:
            import faiss
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatIP(dimension)  # 内积相似度
            
            # 确保向量是连续的float32数组
            embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)
            # 标准化向量
            faiss.normalize_L2(embeddings)
            index.add(embeddings)
            
            logger.info(f"Built FAISS index with {index.ntotal} vectors")
            
            # 保存索引到文件以便下次快速加载
            cache_dir = Path("streamlit_app/vector_cache").resolve()
            if save_vector_index(index, df, cache_dir):
                logger.info("Vector index saved for future use")
            
            logger.info("✅ Vector index built successfully (using Streamlit cache)")
                
        except Exception as e:
            logger.error(f"Failed to build FAISS index: {e}")
            index = None
    
    _vector_index = index
    _vector_data = df
    
    return index, df

def semantic_search_local(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """本地语义搜索功能"""
    if not VECTOR_SUPPORT:
        return []
    
    try:
        # 获取或构建向量索引
        index, df = build_vector_index()
        
        if index is None or df is None or df.empty:
            logger.warning("Vector index not available")
            return []
        
        # 计算查询向量
        model = get_embedding_model()
        if model is None:
            return []
        
        query_embedding = model.encode([query])
        
        if FAISS_SUPPORT and index is not None:
            # 使用FAISS搜索
            import faiss
            faiss.normalize_L2(query_embedding)
            
            scores, indices = index.search(query_embedding.astype('float32'), top_k)
            
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(df):
                    row = df.iloc[idx]
                    result = {
                        'uid': row.get('uid', row.get('id')),  # 兼容不同的ID字段
                        'name': row['name'],
                        'description': row['description'],
                        'type_level_1': row['type_level_1'],
                        'type_level_2': row['type_level_2'],
                        'source_collection': row['source_collection'],
                        'metadata_organism': row.get('metadata_organism', ''),
                        'similarity_score': float(score),
                        'rank': i + 1
                    }
                    results.append(result)
            
            logger.info(f"Semantic search returned {len(results)} results")
            return results
        
        else:
            # 使用numpy计算相似度（备用方案）
            logger.info("Using numpy similarity computation")
            
            # 重新计算所有向量（如果没有FAISS）
            texts = df['text_content'].tolist()
            all_embeddings = compute_embeddings(texts)
            
            if all_embeddings is None:
                return []
            
            # 使用与之前一致的余弦相似度计算方法
            # Cosine similarity: dot(q, v) / (||q|| * ||v||)
            query_norm = np.linalg.norm(query_embedding) + 1e-8
            doc_norms = np.linalg.norm(all_embeddings, axis=1) + 1e-8
            similarities = (all_embeddings @ query_embedding.T) / (doc_norms * query_norm)
            
            # 获取top_k结果
            top_indices = np.argsort(-similarities)[:top_k]
            
            results = []
            for i, idx in enumerate(top_indices):
                row = df.iloc[idx]
                result = {
                    'uid': row['uid'],
                    'name': row['name'],
                    'description': row['description'],
                    'type_level_1': row['type_level_1'],
                    'type_level_2': row['type_level_2'],
                    'source_collection': row['source_collection'],
                    'metadata_organism': row['metadata_organism'],
                    'similarity_score': float(similarities[idx]),
                    'rank': i + 1
                }
                results.append(result)
            
            return results
    
    except Exception as e:
        logger.error(f"语义搜索失败: {e}")
        return []

def get_available_filters():
    """获取可用的筛选选项"""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return {}
            
            # 获取类型选项
            types = conn.execute("""
                SELECT DISTINCT type_level_1 
                FROM parts 
                WHERE type_level_1 IS NOT NULL 
                ORDER BY type_level_1
            """).fetchall()
            
            # 获取来源选项
            sources = conn.execute("""
                SELECT DISTINCT source_collection 
                FROM parts 
                WHERE source_collection IS NOT NULL 
                ORDER BY source_collection
            """).fetchall()
            
            # 获取物种选项
            try:
                organisms = conn.execute("""
                    SELECT DISTINCT metadata_organism 
                    FROM parts 
                    WHERE metadata_organism IS NOT NULL 
                    ORDER BY metadata_organism
                """).fetchall()
            except:
                organisms = []
            
            return {
                "types": [t[0] for t in types],
                "sources": [s[0] for s in sources],
                "organisms": [o[0] for o in organisms]
            }
    except Exception as e:
        logger.error(f"获取筛选选项失败: {e}")
        return {}

def test_database():
    """测试数据库连接和基础功能"""
    try:
        stats = get_basic_stats()
        if "error" in stats:
            return False, stats["error"]
        
        sample = get_parts_sample(5)
        if not sample:
            return False, "无法获取样本数据"
        
        return True, f"数据库正常，共{stats['total_parts']}个部件"
    except Exception as e:
        return False, str(e)

def test_vector_functionality():
    """测试向量功能"""
    if not VECTOR_SUPPORT:
        return False, "向量支持不可用"
    
    try:
        model = get_embedding_model()
        if model is None:
            return False, "无法加载嵌入模型"
        
        # 测试简单的向量计算
        test_texts = ["promoter", "protein coding sequence"]
        embeddings = compute_embeddings(test_texts)
        
        if embeddings is None:
            return False, "无法计算嵌入向量"
        
        # 测试语义搜索
        results = semantic_search_local("E. coli promoter", top_k=3)
        
        return True, f"向量功能正常，测试搜索返回{len(results)}个结果"
    except Exception as e:
        return False, f"向量功能测试失败: {e}"

def get_system_info():
    """获取系统信息"""
    info = {
        "database_type": "DuckDB" if Path("data/parts.duckdb").exists() else "SQLite",
        "vector_support": VECTOR_SUPPORT,
        "faiss_support": FAISS_SUPPORT,
        "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2" if VECTOR_SUPPORT else None
    }
    
    if VECTOR_SUPPORT:
        model = get_embedding_model()
        info["model_loaded"] = model is not None
    
    return info
