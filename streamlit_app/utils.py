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

@contextmanager
def get_db_connection():
    """
    Database connection context manager
    Simplified version, SQLite only
    """
    conn = None
    try:
        # Try different possible paths
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
            logger.error(f"Database file not found in any of: {possible_paths}")
            yield None
            return
        
        conn = sqlite3.connect(str(db_path))
        logger.info("数据库连接成功")
        yield conn
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        yield None
    finally:
        if conn:
            conn.close()

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
