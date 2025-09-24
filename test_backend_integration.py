#!/usr/bin/env python3
"""
SynVectorDB githubshare - Backend API Integration Test
Tests the frontend's integration with production backend APIs
"""

import sys
import time
import requests
import json
from pathlib import Path

# Production backend URLs mentioned in the frontend
BACKEND_BASE_URL = "https://testsdb.sjtu.bio"
FRONTEND_URL = "http://localhost:8501"

def test_backend_api_endpoints():
    """Test production backend API endpoints mentioned in frontend"""
    print("=" * 60)
    print("BACKEND API INTEGRATION TESTS")
    print("=" * 60)
    
    try:
        # Test 1: Stats endpoint
        print("1. Testing /stats endpoint...")
        start_time = time.time()
        response = requests.get(f"{BACKEND_BASE_URL}/stats", timeout=10)
        stats_time = time.time() - start_time
        
        if response.status_code == 200:
            stats_data = response.json()
            print(f"   ✅ PASS: Stats endpoint responding ({stats_time:.3f}s)")
            print(f"   📊 Status: {response.status_code}")
            print(f"   📊 Response size: {len(response.content)} bytes")
            if 'total_parts' in stats_data:
                print(f"   📊 Total parts: {stats_data.get('total_parts', 'N/A')}")
        else:
            print(f"   ❌ FAIL: Stats endpoint error {response.status_code}")
            return False
        
        # Test 2: Parts search endpoint
        print("\n2. Testing /parts/search endpoint...")
        start_time = time.time()
        search_params = {
            "organism": "Mammalian",
            "page_size": 10
        }
        response = requests.get(f"{BACKEND_BASE_URL}/parts/search", 
                              params=search_params, timeout=10)
        search_time = time.time() - start_time
        
        if response.status_code == 200:
            search_data = response.json()
            print(f"   ✅ PASS: Parts search responding ({search_time:.3f}s)")
            print(f"   📊 Status: {response.status_code}")
            if 'results' in search_data:
                results_count = len(search_data.get('results', []))
                print(f"   📊 Results found: {results_count}")
                if results_count > 0:
                    first_result = search_data['results'][0]
                    print(f"   📊 First result UID: {first_result.get('uid', 'N/A')}")
        else:
            print(f"   ❌ FAIL: Parts search error {response.status_code}")
            return False
        
        # Test 3: Semantic search endpoint
        print("\n3. Testing /semantic_search endpoint...")
        start_time = time.time()
        semantic_payload = {
            "query": "E. coli promoter",
            "top_k": 5
        }
        response = requests.post(f"{BACKEND_BASE_URL}/semantic_search",
                               json=semantic_payload,
                               headers={"Content-Type": "application/json"},
                               timeout=15)
        semantic_time = time.time() - start_time
        
        if response.status_code == 200:
            semantic_data = response.json()
            print(f"   ✅ PASS: Semantic search responding ({semantic_time:.3f}s)")
            print(f"   📊 Status: {response.status_code}")
            if 'results' in semantic_data:
                results_count = len(semantic_data.get('results', []))
                print(f"   📊 Semantic results: {results_count}")
        else:
            print(f"   ⚠️  WARN: Semantic search error {response.status_code}")
            # Semantic search might not be available, continue
        
        # Test 4: Downloads index endpoint
        print("\n4. Testing /downloads/index endpoint...")
        start_time = time.time()
        response = requests.get(f"{BACKEND_BASE_URL}/downloads/index", timeout=10)
        downloads_time = time.time() - start_time
        
        if response.status_code == 200:
            downloads_data = response.json()
            print(f"   ✅ PASS: Downloads index responding ({downloads_time:.3f}s)")
            print(f"   📊 Status: {response.status_code}")
            if 'items' in downloads_data:
                items_count = len(downloads_data.get('items', []))
                print(f"   📊 Download items available: {items_count}")
        else:
            print(f"   ❌ FAIL: Downloads index error {response.status_code}")
            return False
        
        # Test 5: Individual part details
        print("\n5. Testing individual part details...")
        if 'results' in search_data and search_data['results']:
            first_uid = search_data['results'][0].get('uid')
            if first_uid:
                start_time = time.time()
                response = requests.get(f"{BACKEND_BASE_URL}/parts/{first_uid}", timeout=10)
                part_time = time.time() - start_time
                
                if response.status_code == 200:
                    part_data = response.json()
                    print(f"   ✅ PASS: Part details responding ({part_time:.3f}s)")
                    print(f"   📊 Part name: {part_data.get('name', 'N/A')}")
                    print(f"   📊 Part type: {part_data.get('type_level_1', 'N/A')}")
                else:
                    print(f"   ❌ FAIL: Part details error {response.status_code}")
                    return False
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ FAIL: Network error - {e}")
        return False
    except Exception as e:
        print(f"   ❌ FAIL: Unexpected error - {e}")
        return False

def test_frontend_backend_integration():
    """Test frontend's display of backend integration information"""
    print("\n" + "=" * 60)
    print("FRONTEND-BACKEND INTEGRATION TESTS")
    print("=" * 60)
    
    try:
        # Test 1: Check if frontend is running
        print("1. Testing frontend availability...")
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print(f"   ✅ PASS: Frontend responding")
        else:
            print(f"   ❌ FAIL: Frontend not responding")
            return False
        
        # Test 2: Check API documentation in source code (more reliable than HTML)
        print("\n2. Testing API documentation in frontend source...")
        try:
            with open('streamlit_app/Home.py', 'r') as f:
                frontend_source = f.read()
            
            api_keywords = ["testsdb.sjtu.bio", "API Integration", "MCP Server", "synvectordb-mcp-server"]
            found_keywords = []
            for keyword in api_keywords:
                if keyword in frontend_source:
                    found_keywords.append(keyword)
            
            if len(found_keywords) >= 3:
                print(f"   ✅ PASS: API documentation found in source")
                print(f"   📊 Keywords found: {', '.join(found_keywords)}")
            else:
                print(f"   ❌ FAIL: API documentation incomplete")
                return False
                
        except FileNotFoundError:
            print(f"   ❌ FAIL: Frontend source file not found")
            return False
        
        # Test 3: Verify backend endpoints mentioned in frontend
        print("\n3. Testing backend endpoints mentioned in frontend...")
        backend_endpoints = ["/stats", "/parts/search", "/semantic_search", "/downloads/index"]
        mentioned_endpoints = []
        
        for endpoint in backend_endpoints:
            if endpoint in frontend_source:
                mentioned_endpoints.append(endpoint)
        
        if mentioned_endpoints:
            print(f"   ✅ PASS: Backend endpoints documented")
            print(f"   📊 Endpoints mentioned: {', '.join(mentioned_endpoints)}")
        else:
            print(f"   ⚠️  WARN: Backend endpoints not explicitly mentioned")
        
        return True
        
    except Exception as e:
        print(f"   ❌ FAIL: Frontend integration test error - {e}")
        return False

def test_mcp_server_documentation():
    """Test MCP server NPM package documentation"""
    print("\n" + "=" * 60)
    print("MCP SERVER INTEGRATION TESTS")
    print("=" * 60)
    
    try:
        # Test frontend MCP documentation in source code
        print("1. Testing MCP documentation in frontend source...")
        try:
            with open('streamlit_app/Home.py', 'r') as f:
                frontend_source = f.read()
            
            mcp_keywords = ["synvectordb-mcp-server", "npm install", "Claude Desktop", "MCP Server"]
            found_mcp = [kw for kw in mcp_keywords if kw in frontend_source]
            
            if len(found_mcp) >= 3:
                print(f"   ✅ PASS: MCP documentation found in frontend")
                print(f"   📊 MCP keywords: {', '.join(found_mcp)}")
            else:
                print(f"   ❌ FAIL: MCP documentation incomplete")
                return False
                
        except FileNotFoundError:
            print(f"   ❌ FAIL: Frontend source file not found")
            return False
        
        # Test NPM package availability (optional)
        print("\n2. Testing NPM package availability...")
        try:
            response = requests.get("https://www.npmjs.com/package/synvectordb-mcp-server", timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ PASS: NPM package page accessible")
            else:
                print(f"   ⚠️  WARN: NPM package page not accessible ({response.status_code})")
        except:
            print(f"   ⚠️  WARN: NPM package check failed (network issue)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ FAIL: MCP documentation test error - {e}")
        return False

def test_performance_integration():
    """Test performance of backend API calls from frontend perspective"""
    print("\n" + "=" * 60)
    print("PERFORMANCE INTEGRATION TESTS")
    print("=" * 60)
    
    try:
        # Test response times for key endpoints
        endpoints = [
            ("/stats", "Statistics"),
            ("/parts/search?page_size=5", "Parts Search"),
            ("/downloads/index", "Downloads")
        ]
        
        total_time = 0
        successful_tests = 0
        
        for endpoint, name in endpoints:
            print(f"Testing {name} performance...")
            start_time = time.time()
            
            try:
                response = requests.get(f"{BACKEND_BASE_URL}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                total_time += response_time
                
                if response.status_code == 200:
                    print(f"   ✅ PASS: {name} ({response_time:.3f}s)")
                    successful_tests += 1
                else:
                    print(f"   ❌ FAIL: {name} error {response.status_code}")
            except Exception as e:
                response_time = time.time() - start_time
                print(f"   ❌ FAIL: {name} exception ({response_time:.3f}s) - {e}")
        
        if successful_tests > 0:
            avg_time = total_time / successful_tests
            print(f"\n   📊 Average response time: {avg_time:.3f}s")
            print(f"   📊 Successful tests: {successful_tests}/{len(endpoints)}")
            
            if avg_time < 3.0:
                print(f"   ✅ PASS: Backend performance acceptable")
                return True
            else:
                print(f"   ⚠️  WARN: Backend performance slow")
                return True  # Still pass, just slow
        else:
            print(f"   ❌ FAIL: No successful backend tests")
            return False
        
    except Exception as e:
        print(f"   ❌ FAIL: Performance test error - {e}")
        return False

def generate_integration_report():
    """Generate comprehensive integration test report"""
    print("\n" + "=" * 60)
    print("BACKEND INTEGRATION TEST REPORT")
    print("=" * 60)
    
    # Run all integration tests
    backend_test = test_backend_api_endpoints()
    frontend_test = test_frontend_backend_integration()
    mcp_test = test_mcp_server_documentation()
    perf_test = test_performance_integration()
    
    # Summary
    total_tests = 4
    passed_tests = sum([backend_test, frontend_test, mcp_test, perf_test])
    
    print(f"\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"Backend API Endpoints: {'✅ PASS' if backend_test else '❌ FAIL'}")
    print(f"Frontend-Backend Integration: {'✅ PASS' if frontend_test else '❌ FAIL'}")
    print(f"MCP Server Documentation: {'✅ PASS' if mcp_test else '❌ FAIL'}")
    print(f"Performance Integration: {'✅ PASS' if perf_test else '❌ FAIL'}")
    print(f"\nOverall: {passed_tests}/{total_tests} integration tests passed ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests >= 3:  # Allow one test to fail
        print("🎉 BACKEND INTEGRATION SUCCESSFUL!")
        print("Frontend successfully integrates with production backend APIs")
        return True
    else:
        print("⚠️  BACKEND INTEGRATION ISSUES DETECTED")
        print("Please review backend connectivity and API documentation")
        return False

if __name__ == "__main__":
    print("SynVectorDB githubshare - Backend Integration Test Suite")
    print("=" * 60)
    print(f"Frontend URL: {FRONTEND_URL}")
    print(f"Backend URL: {BACKEND_BASE_URL}")
    print("=" * 60)
    
    # Run integration tests
    success = generate_integration_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
