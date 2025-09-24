"""
SynVectorDB githubshare - 简化工具函数
重构版本，移除复杂依赖，专注核心功能
"""

import sqlite3
import pandas as pd
import logging
from pathlib import Path
from contextlib import contextmanager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import DuckDB
try:
    import duckdb
    DUCKDB_AVAILABLE = True
    logger.info("DuckDB support enabled")
except ImportError:
    DUCKDB_AVAILABLE = False
    logger.warning("DuckDB not available, using SQLite only")

@contextmanager
def get_db_connection():
    """
    Database connection context manager
    Supports DuckDB (preferred) and SQLite (fallback)
    """
    conn = None
    db_type = None
    
    try:
        # Try DuckDB first if available
        if DUCKDB_AVAILABLE:
            duckdb_paths = [
                Path("../data/parts.duckdb"),
                Path("data/parts.duckdb"),
                Path("./data/parts.duckdb")
            ]
            
            for path in duckdb_paths:
                if path.exists():
                    try:
                        conn = duckdb.connect(str(path), read_only=True)
                        db_type = "DuckDB"
                        logger.info(f"DuckDB连接成功: {path}")
                        yield conn
                        return
                    except Exception as e:
                        logger.warning(f"DuckDB连接失败 {path}: {e}")
                        continue
        
        # Fallback to SQLite
        sqlite_paths = [
            Path("../data/parts.db"),
            Path("data/parts.db"),
            Path("./data/parts.db")
        ]
        
        for path in sqlite_paths:
            if path.exists():
                try:
                    conn = sqlite3.connect(str(path))
                    db_type = "SQLite"
                    logger.info(f"SQLite连接成功: {path}")
                    yield conn
                    return
                except Exception as e:
                    logger.warning(f"SQLite连接失败 {path}: {e}")
                    continue
        
        # No database found
        all_paths = (duckdb_paths if DUCKDB_AVAILABLE else []) + sqlite_paths
        logger.error(f"未找到可用数据库文件: {all_paths}")
        yield None
        
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        yield None
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

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
            
            return {
                "total_parts": total_parts,
                "type_stats": type_stats,
                "source_stats": source_stats,
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
                       source_collection, LENGTH(sequence) as sequence_length
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

def search_parts(query="", type_filter="", source_filter="", limit=20):
    """简化的部件搜索"""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return []
            
            sql = """
                SELECT uid, name, description, type_level_1, type_level_2, 
                       source_collection, LENGTH(sequence) as sequence_length
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
            
            sql += " ORDER BY name LIMIT ?"
            params.append(limit)
            
            df = pd.read_sql_query(sql, conn, params=params)
            return df.to_dict('records')
    except Exception as e:
        logger.error(f"搜索部件失败: {e}")
        return []

def get_database_info():
    """获取数据库类型和状态信息"""
    info = {
        "duckdb_available": DUCKDB_AVAILABLE,
        "database_type": None,
        "database_path": None,
        "connection_status": "disconnected"
    }
    
    try:
        with get_db_connection() as conn:
            if conn is None:
                info["connection_status"] = "failed"
                return info
            
            # Detect database type
            if hasattr(conn, 'execute') and 'duckdb' in str(type(conn)):
                info["database_type"] = "DuckDB"
            else:
                info["database_type"] = "SQLite"
            
            info["connection_status"] = "connected"
            
            # Try to get a simple count to verify functionality
            result = conn.execute("SELECT COUNT(*) FROM parts").fetchone()
            if result:
                info["parts_count"] = result[0]
                info["connection_status"] = "functional"
                
    except Exception as e:
        info["connection_status"] = f"error: {str(e)}"
    
    return info

def test_database():
    """测试数据库连接和基础功能"""
    try:
        db_info = get_database_info()
        
        if db_info["connection_status"] == "functional":
            parts_count = db_info.get("parts_count", 0)
            db_type = db_info.get("database_type", "Unknown")
            return True, f"数据库正常 ({db_type})，共{parts_count}个部件"
        elif db_info["connection_status"] == "connected":
            return False, "数据库连接成功但无法查询数据"
        else:
            return False, f"数据库连接失败: {db_info['connection_status']}"
            
    except Exception as e:
        return False, str(e)
