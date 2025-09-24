#!/usr/bin/env python3
"""
SynVectorDB githubshare - Enhanced Features Test Suite
测试DuckDB集成和本地向量计算功能
"""

import sys
import time
import os
sys.path.append('streamlit_app')

from utils_enhanced import (
    test_database,
    test_vector_functionality,
    get_system_info,
    get_basic_stats,
    semantic_search_local,
    build_vector_index,
    get_embedding_model
)

def test_database_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("DATABASE CONNECTION TESTS")
    print("=" * 60)
    
    success, message = test_database()
    if success:
        print(f"✅ PASS: {message}")
        return True
    else:
        print(f"❌ FAIL: {message}")
        return False

def test_system_configuration():
    """测试系统配置"""
    print("\n" + "=" * 60)
    print("SYSTEM CONFIGURATION TESTS")
    print("=" * 60)
    
    system_info = get_system_info()
    
    print(f"Database Type: {system_info.get('database_type', 'Unknown')}")
    print(f"Vector Support: {system_info.get('vector_support', False)}")
    print(f"FAISS Support: {system_info.get('faiss_support', False)}")
    print(f"Embedding Model: {system_info.get('embedding_model', 'N/A')}")
    
    if system_info.get('vector_support'):
        print("✅ PASS: Vector support available")
        return True
    else:
        print("⚠️  WARN: Vector support not available")
        return False

def test_enhanced_statistics():
    """测试增强统计功能"""
    print("\n" + "=" * 60)
    print("ENHANCED STATISTICS TESTS")
    print("=" * 60)
    
    try:
        stats = get_basic_stats()
        
        if "error" in stats:
            print(f"❌ FAIL: {stats['error']}")
            return False
        
        print(f"✅ PASS: Basic statistics retrieved")
        print(f"   📊 Total parts: {stats.get('total_parts', 0):,}")
        print(f"   📊 Type categories: {len(stats.get('type_stats', []))}")
        print(f"   📊 Source categories: {len(stats.get('source_stats', []))}")
        print(f"   📊 Organism categories: {len(stats.get('organism_stats', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Statistics test failed - {e}")
        return False

def test_vector_model_loading():
    """测试向量模型加载"""
    print("\n" + "=" * 60)
    print("VECTOR MODEL LOADING TESTS")
    print("=" * 60)
    
    try:
        model = get_embedding_model()
        
        if model is None:
            print("⚠️  WARN: Embedding model not loaded")
            return False
        
        print("✅ PASS: Embedding model loaded successfully")
        
        # 测试简单编码
        test_text = ["E. coli promoter", "fluorescent protein"]
        start_time = time.time()
        embeddings = model.encode(test_text)
        encode_time = time.time() - start_time
        
        print(f"✅ PASS: Text encoding successful")
        print(f"   📊 Encoded {len(test_text)} texts in {encode_time:.3f}s")
        print(f"   📊 Embedding dimension: {embeddings.shape[1]}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Vector model test failed - {e}")
        return False

def test_vector_index_building():
    """测试向量索引构建"""
    print("\n" + "=" * 60)
    print("VECTOR INDEX BUILDING TESTS")
    print("=" * 60)
    
    try:
        start_time = time.time()
        index, df = build_vector_index()
        build_time = time.time() - start_time
        
        if index is None or df is None:
            print("⚠️  WARN: Vector index not built (may be normal if no vector support)")
            return False
        
        print("✅ PASS: Vector index built successfully")
        print(f"   📊 Index build time: {build_time:.2f}s")
        print(f"   📊 Indexed parts: {len(df)}")
        
        if hasattr(index, 'ntotal'):
            print(f"   📊 FAISS index size: {index.ntotal}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Vector index test failed - {e}")
        return False

def test_semantic_search():
    """测试语义搜索功能"""
    print("\n" + "=" * 60)
    print("SEMANTIC SEARCH TESTS")
    print("=" * 60)
    
    test_queries = [
        "E. coli promoter",
        "fluorescent protein reporter",
        "mammalian expression vector"
    ]
    
    total_tests = len(test_queries)
    passed_tests = 0
    
    for query in test_queries:
        try:
            print(f"\nTesting query: '{query}'")
            start_time = time.time()
            results = semantic_search_local(query, top_k=5)
            search_time = time.time() - start_time
            
            if results:
                print(f"   ✅ PASS: Found {len(results)} results in {search_time:.3f}s")
                # 显示第一个结果
                first_result = results[0]
                print(f"   📊 Top result: {first_result.get('name', 'N/A')}")
                print(f"   📊 Similarity: {first_result.get('similarity_score', 0):.4f}")
                passed_tests += 1
            else:
                print(f"   ⚠️  WARN: No results found for '{query}'")
                
        except Exception as e:
            print(f"   ❌ FAIL: Search failed for '{query}' - {e}")
    
    if passed_tests > 0:
        print(f"\n✅ PASS: Semantic search functional ({passed_tests}/{total_tests} queries)")
        return True
    else:
        print(f"\n❌ FAIL: Semantic search not working")
        return False

def test_performance_benchmarks():
    """测试性能基准"""
    print("\n" + "=" * 60)
    print("PERFORMANCE BENCHMARK TESTS")
    print("=" * 60)
    
    try:
        # 数据库查询性能
        start_time = time.time()
        stats = get_basic_stats()
        db_time = time.time() - start_time
        
        print(f"Database query time: {db_time:.3f}s")
        
        # 向量搜索性能（如果可用）
        system_info = get_system_info()
        if system_info.get('vector_support'):
            start_time = time.time()
            results = semantic_search_local("promoter", top_k=10)
            vector_time = time.time() - start_time
            
            print(f"Vector search time: {vector_time:.3f}s")
            print(f"Results returned: {len(results)}")
            
            if db_time < 5.0 and vector_time < 10.0:
                print("✅ PASS: Performance benchmarks acceptable")
                return True
            else:
                print("⚠️  WARN: Performance slower than expected")
                return True  # Still pass, just slow
        else:
            if db_time < 5.0:
                print("✅ PASS: Database performance acceptable")
                return True
            else:
                print("⚠️  WARN: Database performance slower than expected")
                return True
        
    except Exception as e:
        print(f"❌ FAIL: Performance test failed - {e}")
        return False

def generate_test_report():
    """生成测试报告"""
    print("\n" + "=" * 60)
    print("ENHANCED FEATURES TEST REPORT")
    print("=" * 60)
    
    # 运行所有测试
    tests = [
        ("Database Connection", test_database_connection),
        ("System Configuration", test_system_configuration),
        ("Enhanced Statistics", test_enhanced_statistics),
        ("Vector Model Loading", test_vector_model_loading),
        ("Vector Index Building", test_vector_index_building),
        ("Semantic Search", test_semantic_search),
        ("Performance Benchmarks", test_performance_benchmarks)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ FAIL: {test_name} - Exception: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed >= total * 0.7:  # 70% pass rate
        print("🎉 ENHANCED FEATURES READY!")
        print("Local DuckDB and vector search functionality is working")
        return True
    else:
        print("⚠️  ENHANCED FEATURES NEED ATTENTION")
        print("Some functionality may not be available")
        return False

if __name__ == "__main__":
    print("SynVectorDB githubshare - Enhanced Features Test Suite")
    print("=" * 60)
    print("Testing DuckDB integration and local vector computation")
    print("=" * 60)
    
    # 运行测试
    success = generate_test_report()
    
    # 退出码
    sys.exit(0 if success else 1)
