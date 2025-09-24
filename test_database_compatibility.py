#!/usr/bin/env python3
"""
Database Compatibility Test Script
Tests both DuckDB and SQLite database connections and functionality
"""

import sys
import os
from pathlib import Path

# Add streamlit_app to path
sys.path.append('streamlit_app')

try:
    from utils import get_database_info, test_database, get_basic_stats, get_parts_sample
    print("✅ Successfully imported utility functions")
except ImportError as e:
    print(f"❌ Failed to import utilities: {e}")
    sys.exit(1)

def test_database_compatibility():
    """Test database compatibility and functionality"""
    print("🧬 SynVectorDB Database Compatibility Test")
    print("=" * 50)
    
    # Test 1: Database Info
    print("\n1️⃣ Testing database detection...")
    db_info = get_database_info()
    
    print(f"   🦆 DuckDB Available: {db_info.get('duckdb_available', False)}")
    print(f"   🗃️ Database Type: {db_info.get('database_type', 'Unknown')}")
    print(f"   🔗 Connection Status: {db_info.get('connection_status', 'Unknown')}")
    
    # Check for cross-platform issues
    if db_info.get('cross_platform_issue'):
        print("   🚨 Cross-platform issue detected!")
        print("   ⚠️  DuckDB file contains hardcoded Windows/WSL paths")
        print("   💡 Solution: Run 'python3 scripts/download_data.py' to auto-fix")
        print("   📊 Current status: Using SQLite fallback (fully functional)")
    
    if 'parts_count' in db_info:
        print(f"   📊 Parts Count: {db_info['parts_count']:,}")
    
    # Test 2: Database Connection
    print("\n2️⃣ Testing database connection...")
    db_ok, db_msg = test_database()
    
    if db_ok:
        print(f"   ✅ {db_msg}")
    else:
        print(f"   ❌ {db_msg}")
        return False
    
    # Test 3: Basic Statistics
    print("\n3️⃣ Testing statistics retrieval...")
    try:
        stats = get_basic_stats()
        if "error" in stats:
            print(f"   ❌ Statistics error: {stats['error']}")
            return False
        else:
            print(f"   ✅ Total parts: {stats['total_parts']:,}")
            print(f"   ✅ Function types: {len(stats['type_stats'])}")
            print(f"   ✅ Data sources: {len(stats['source_stats'])}")
    except Exception as e:
        print(f"   ❌ Statistics failed: {e}")
        return False
    
    # Test 4: Sample Data Retrieval
    print("\n4️⃣ Testing sample data retrieval...")
    try:
        sample = get_parts_sample(5)
        if sample:
            print(f"   ✅ Retrieved {len(sample)} sample parts")
            if sample:
                first_part = sample[0]
                print(f"   📄 Sample part: {first_part.get('name', 'N/A')}")
        else:
            print("   ❌ No sample data retrieved")
            return False
    except Exception as e:
        print(f"   ❌ Sample retrieval failed: {e}")
        return False
    
    # Test 5: Database File Detection
    print("\n5️⃣ Testing database file detection...")
    data_dir = Path("data")
    
    if data_dir.exists():
        print(f"   📁 Data directory exists: {data_dir.absolute()}")
        
        duckdb_file = data_dir / "parts.duckdb"
        sqlite_file = data_dir / "parts.db"
        
        if duckdb_file.exists():
            size_mb = duckdb_file.stat().st_size / 1024 / 1024
            print(f"   🦆 DuckDB file: {size_mb:.1f}MB")
        else:
            print("   ⚠️  DuckDB file not found")
        
        if sqlite_file.exists():
            size_mb = sqlite_file.stat().st_size / 1024 / 1024
            print(f"   🗃️ SQLite file: {size_mb:.1f}MB")
        else:
            print("   ⚠️  SQLite file not found")
        
        # Check for incompatible DuckDB files
        incompatible_file = data_dir / "parts.duckdb.incompatible"
        if incompatible_file.exists():
            size_mb = incompatible_file.stat().st_size / 1024 / 1024
            print(f"   🚨 Incompatible DuckDB file: {size_mb:.1f}MB (renamed)")
            print(f"      💡 This file contains Windows/WSL paths")
    else:
        print("   ❌ Data directory not found")
        return False
    
    return True

def main():
    """Main test function"""
    success = test_database_compatibility()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All database compatibility tests passed!")
        print("✅ The application should work correctly with the current database setup.")
    else:
        print("❌ Some tests failed. Please check the database configuration.")
        print("💡 Try running the data download script: python3 scripts/download_data.py")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
