#!/usr/bin/env python3
"""
SynVectorDB githubshare - Comprehensive Test Suite
Tests all functionality including database connectivity, search, and performance
"""

import sys
import time
import requests
import subprocess
import json
from pathlib import Path

# Add streamlit_app to path
sys.path.append('streamlit_app')

def test_database_functionality():
    """Test database connectivity and basic operations"""
    print("=" * 60)
    print("DATABASE FUNCTIONALITY TESTS")
    print("=" * 60)
    
    try:
        from utils import test_database, get_basic_stats, search_parts, get_parts_sample
        
        # Test 1: Database Connection
        print("1. Testing database connection...")
        start_time = time.time()
        ok, msg = test_database()
        db_time = time.time() - start_time
        
        if ok:
            print(f"   ✅ PASS: Database connected ({db_time:.3f}s)")
            print(f"   📊 {msg}")
        else:
            print(f"   ❌ FAIL: Database connection failed - {msg}")
            return False
        
        # Test 2: Basic Statistics
        print("\n2. Testing basic statistics...")
        start_time = time.time()
        stats = get_basic_stats()
        stats_time = time.time() - start_time
        
        if stats and 'total_parts' in stats:
            print(f"   ✅ PASS: Statistics retrieved ({stats_time:.3f}s)")
            print(f"   📊 Total parts: {stats['total_parts']:,}")
            print(f"   📊 Type categories: {len(stats.get('type_stats', []))}")
            print(f"   📊 Source categories: {len(stats.get('source_stats', []))}")
        else:
            print(f"   ❌ FAIL: Statistics retrieval failed")
            return False
        
        # Test 3: Search Functionality
        print("\n3. Testing search functionality...")
        
        # Text search
        start_time = time.time()
        results = search_parts(query='promoter', limit=5)
        search_time = time.time() - start_time
        
        if results:
            print(f"   ✅ PASS: Text search ({search_time:.3f}s)")
            print(f"   📊 Found {len(results)} results for 'promoter'")
            print(f"   📊 First result: {results[0].get('name', 'N/A')}")
        else:
            print(f"   ⚠️  WARN: No results for text search")
        
        # Type filter search
        start_time = time.time()
        results = search_parts(type_filter='Coding Sequences', limit=5)
        filter_time = time.time() - start_time
        
        if results:
            print(f"   ✅ PASS: Type filter search ({filter_time:.3f}s)")
            print(f"   📊 Found {len(results)} coding sequences")
        else:
            print(f"   ⚠️  WARN: No results for type filter")
        
        # Source filter search
        start_time = time.time()
        results = search_parts(source_filter='igem', limit=5)
        source_time = time.time() - start_time
        
        if results:
            print(f"   ✅ PASS: Source filter search ({source_time:.3f}s)")
            print(f"   📊 Found {len(results)} iGEM parts")
        else:
            print(f"   ⚠️  WARN: No results for source filter")
        
        # Test 4: Sample Data
        print("\n4. Testing sample data retrieval...")
        start_time = time.time()
        sample = get_parts_sample(10)
        sample_time = time.time() - start_time
        
        if sample:
            print(f"   ✅ PASS: Sample data retrieved ({sample_time:.3f}s)")
            print(f"   📊 Sample size: {len(sample)} parts")
        else:
            print(f"   ❌ FAIL: Sample data retrieval failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ FAIL: Database test exception - {e}")
        return False

def test_streamlit_app():
    """Test Streamlit application"""
    print("\n" + "=" * 60)
    print("STREAMLIT APPLICATION TESTS")
    print("=" * 60)
    
    try:
        # Test 1: Check if service is running
        print("1. Testing Streamlit service...")
        try:
            response = requests.get("http://localhost:8501", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ PASS: Streamlit service responding")
                print(f"   📊 Status code: {response.status_code}")
            else:
                print(f"   ❌ FAIL: Unexpected status code {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"   ❌ FAIL: Streamlit service not accessible - {e}")
            return False
        
        # Test 2: Check health endpoint
        print("\n2. Testing health endpoint...")
        try:
            response = requests.get("http://localhost:8501/healthz", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ PASS: Health endpoint responding")
            else:
                print(f"   ⚠️  WARN: Health endpoint status {response.status_code}")
        except:
            print(f"   ⚠️  WARN: Health endpoint not available")
        
        # Test 3: Page imports
        print("\n3. Testing page imports...")
        try:
            import streamlit_app.Home as Home
            print(f"   ✅ PASS: Home page import")
            
            import streamlit_app.pages.parts_browser as parts_browser
            print(f"   ✅ PASS: Parts browser import")
            
            import streamlit_app.pages.semantic_search as semantic_search
            print(f"   ✅ PASS: Semantic search import")
            
            import streamlit_app.pages.statistics as statistics
            print(f"   ✅ PASS: Statistics page import")
            
        except Exception as e:
            print(f"   ❌ FAIL: Page import failed - {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ FAIL: Streamlit test exception - {e}")
        return False

def test_performance_benchmarks():
    """Performance benchmarking"""
    print("\n" + "=" * 60)
    print("PERFORMANCE BENCHMARKS")
    print("=" * 60)
    
    try:
        from utils import get_basic_stats, search_parts, get_parts_sample
        
        # Benchmark 1: Database queries
        print("1. Database query performance...")
        
        times = []
        for i in range(5):
            start_time = time.time()
            stats = get_basic_stats()
            query_time = time.time() - start_time
            times.append(query_time)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"   📊 Average query time: {avg_time:.3f}s")
        print(f"   📊 Min query time: {min_time:.3f}s")
        print(f"   📊 Max query time: {max_time:.3f}s")
        
        if avg_time < 5.0:
            print(f"   ✅ PASS: Query performance acceptable")
        else:
            print(f"   ⚠️  WARN: Query performance slow")
        
        # Benchmark 2: Search performance
        print("\n2. Search performance...")
        
        search_times = []
        search_queries = ['promoter', 'protein', 'regulatory', 'reporter', 'terminator']
        
        for query in search_queries:
            start_time = time.time()
            results = search_parts(query=query, limit=10)
            search_time = time.time() - start_time
            search_times.append(search_time)
            print(f"   📊 '{query}': {search_time:.3f}s ({len(results)} results)")
        
        avg_search_time = sum(search_times) / len(search_times)
        print(f"   📊 Average search time: {avg_search_time:.3f}s")
        
        if avg_search_time < 3.0:
            print(f"   ✅ PASS: Search performance acceptable")
        else:
            print(f"   ⚠️  WARN: Search performance slow")
        
        return True
        
    except Exception as e:
        print(f"   ❌ FAIL: Performance test exception - {e}")
        return False

def test_data_integrity():
    """Test data integrity and consistency"""
    print("\n" + "=" * 60)
    print("DATA INTEGRITY TESTS")
    print("=" * 60)
    
    try:
        from utils import get_db_connection
        
        print("1. Testing data consistency...")
        
        with get_db_connection() as conn:
            if conn is None:
                print(f"   ❌ FAIL: Database connection failed")
                return False
            
            # Test table existence
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            table_names = [t[0] for t in tables]
            
            if 'parts' in table_names:
                print(f"   ✅ PASS: Parts table exists")
            else:
                print(f"   ❌ FAIL: Parts table missing")
                return False
            
            # Test data counts
            total_parts = conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
            parts_with_names = conn.execute("SELECT COUNT(*) FROM parts WHERE name IS NOT NULL").fetchone()[0]
            parts_with_sequences = conn.execute("SELECT COUNT(*) FROM parts WHERE sequence IS NOT NULL").fetchone()[0]
            
            print(f"   📊 Total parts: {total_parts:,}")
            print(f"   📊 Parts with names: {parts_with_names:,} ({parts_with_names/total_parts*100:.1f}%)")
            print(f"   📊 Parts with sequences: {parts_with_sequences:,} ({parts_with_sequences/total_parts*100:.1f}%)")
            
            if total_parts > 0:
                print(f"   ✅ PASS: Database contains data")
            else:
                print(f"   ❌ FAIL: Database is empty")
                return False
            
            # Test data quality
            null_names = conn.execute("SELECT COUNT(*) FROM parts WHERE name IS NULL OR name = ''").fetchone()[0]
            null_descriptions = conn.execute("SELECT COUNT(*) FROM parts WHERE description IS NULL OR description = ''").fetchone()[0]
            
            print(f"   📊 Parts without names: {null_names:,} ({null_names/total_parts*100:.1f}%)")
            print(f"   📊 Parts without descriptions: {null_descriptions:,} ({null_descriptions/total_parts*100:.1f}%)")
            
            if null_names / total_parts < 0.1:  # Less than 10% missing names
                print(f"   ✅ PASS: Data quality acceptable")
            else:
                print(f"   ⚠️  WARN: High percentage of missing names")
        
        return True
        
    except Exception as e:
        print(f"   ❌ FAIL: Data integrity test exception - {e}")
        return False

def generate_test_report():
    """Generate comprehensive test report"""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST REPORT")
    print("=" * 60)
    
    # Run all tests
    db_test = test_database_functionality()
    app_test = test_streamlit_app()
    perf_test = test_performance_benchmarks()
    data_test = test_data_integrity()
    
    # Summary
    total_tests = 4
    passed_tests = sum([db_test, app_test, perf_test, data_test])
    
    print(f"\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Database Functionality: {'✅ PASS' if db_test else '❌ FAIL'}")
    print(f"Streamlit Application: {'✅ PASS' if app_test else '❌ FAIL'}")
    print(f"Performance Benchmarks: {'✅ PASS' if perf_test else '❌ FAIL'}")
    print(f"Data Integrity: {'✅ PASS' if data_test else '❌ FAIL'}")
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - System ready for production!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - Please review and fix issues")
        return False

if __name__ == "__main__":
    print("SynVectorDB githubshare - Comprehensive Test Suite")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("data/parts.db").exists():
        print("❌ FAIL: Please run this script from the githubshare root directory")
        sys.exit(1)
    
    # Run comprehensive tests
    success = generate_test_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
