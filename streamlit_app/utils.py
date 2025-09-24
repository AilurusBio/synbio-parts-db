"""
SynVectorDB Local Deployment - Simplified Utility Functions
Refactored version with removed complex dependencies, focused on core functionality
"""

import sqlite3
import pandas as pd
import logging
from pathlib import Path
from contextlib import contextmanager

# Configure logging
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
                        # Test if the database is actually functional
                        test_result = conn.execute("SELECT COUNT(*) FROM parts LIMIT 1").fetchone()
                        if test_result and test_result[0] > 0:
                            db_type = "DuckDB"
                            logger.info(f"DuckDB connection successful: {path} ({test_result[0]} parts)")
                            yield conn
                            return
                        else:
                            logger.warning(f"DuckDB database empty or invalid: {path}")
                            conn.close()
                            continue
                    except Exception as e:
                        logger.warning(f"DuckDB connection failed {path}: {e}")
                        # Check if it's a path-related error (Windows paths on Linux)
                        if "No files found that match the pattern" in str(e) or "/mnt/" in str(e):
                            logger.error(f"Cross-platform path issue detected, DuckDB file contains Windows paths: {e}")
                        try:
                            conn.close()
                        except:
                            pass
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
                    # Test if the database is actually functional
                    cursor = conn.cursor()
                    test_result = cursor.execute("SELECT COUNT(*) FROM parts").fetchone()
                    if test_result and test_result[0] > 0:
                        db_type = "SQLite"
                        logger.info(f"SQLite connection successful: {path} ({test_result[0]} parts)")
                        yield conn
                        return
                    else:
                        logger.warning(f"SQLite database empty or invalid: {path}")
                        conn.close()
                        continue
                except Exception as e:
                    logger.warning(f"SQLite connection failed {path}: {e}")
                    try:
                        conn.close()
                    except:
                        pass
                    continue
        
        # No database found
        all_paths = (duckdb_paths if DUCKDB_AVAILABLE else []) + sqlite_paths
        logger.error(f"No available database files found: {all_paths}")
        yield None
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        yield None
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

def get_basic_stats():
    """Get basic database statistics"""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return {"error": "Database connection failed"}
            
            # Basic statistics
            total_parts = conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
            
            # Type statistics
            type_stats = conn.execute("""
                SELECT type_level_1, COUNT(*) as count 
                FROM parts 
                WHERE type_level_1 IS NOT NULL 
                GROUP BY type_level_1 
                ORDER BY count DESC
            """).fetchall()
            
            # Source statistics
            source_stats = conn.execute("""
                SELECT source_collection, COUNT(*) as count 
                FROM parts 
                WHERE source_collection IS NOT NULL 
                GROUP BY source_collection 
                ORDER BY count DESC
            """).fetchall()
            
            return {
                "total_parts": total_parts,
                "type_stats": dict(type_stats),
                "source_stats": dict(source_stats),
                "status": "success"
            }
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        return {"error": str(e)}

def get_parts_sample(limit=10):
    """Get sample parts data"""
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
        logger.error(f"Failed to get parts sample: {e}")
        return []

def search_parts(query="", type_filter="", source_filter="", limit=20):
    """Simplified parts search"""
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
        logger.error(f"Parts search failed: {e}")
        return []

def get_database_info():
    """Get database type and status information"""
    info = {
        "duckdb_available": DUCKDB_AVAILABLE,
        "database_type": None,
        "database_path": None,
        "connection_status": "disconnected",
        "cross_platform_issue": False
    }
    
    try:
        with get_db_connection() as conn:
            if conn is None:
                info["connection_status"] = "failed"
                # Check for cross-platform issues
                data_dir = Path("data")
                if data_dir.exists():
                    duckdb_file = data_dir / "parts.duckdb"
                    if duckdb_file.exists() and DUCKDB_AVAILABLE:
                        # Try to detect cross-platform path issues
                        try:
                            test_conn = duckdb.connect(str(duckdb_file), read_only=True)
                            test_conn.execute("SELECT COUNT(*) FROM parts LIMIT 1").fetchone()
                            test_conn.close()
                        except Exception as e:
                            if "No files found that match the pattern" in str(e) or "/mnt/" in str(e):
                                info["cross_platform_issue"] = True
                                info["connection_status"] = "cross_platform_error"
                return info
            
            # Detect database type
            if hasattr(conn, 'execute') and 'duckdb' in str(type(conn)):
                info["database_type"] = "DuckDB"
            else:
                info["database_type"] = "SQLite"
            
            info["connection_status"] = "connected"
            
            # Try to get a simple count to verify functionality
            if info["database_type"] == "SQLite":
                cursor = conn.cursor()
                result = cursor.execute("SELECT COUNT(*) FROM parts").fetchone()
            else:
                result = conn.execute("SELECT COUNT(*) FROM parts").fetchone()
                
            if result:
                info["parts_count"] = result[0]
                info["connection_status"] = "functional"
                
    except Exception as e:
        error_msg = str(e)
        if "No files found that match the pattern" in error_msg or "/mnt/" in error_msg:
            info["cross_platform_issue"] = True
            info["connection_status"] = "cross_platform_error"
        else:
            info["connection_status"] = f"error: {error_msg}"
    
    return info

def test_database():
    """Test database connection and basic functionality"""
    try:
        db_info = get_database_info()
        
        if db_info["connection_status"] == "functional":
            parts_count = db_info.get("parts_count", 0)
            db_type = db_info.get("database_type", "Unknown")
            return True, f"Database functional ({db_type}), {parts_count:,} parts available"
        elif db_info["connection_status"] == "connected":
            return False, "Database connected but unable to query data"
        else:
            return False, f"Database connection failed: {db_info['connection_status']}"
            
    except Exception as e:
        return False, str(e)
