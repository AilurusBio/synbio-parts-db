import subprocess
import json
from datetime import datetime
import time
import os

def search_biomcp(keywords, max_results=20):
    """使用 BioMCP 命令行工具搜索文献"""
    try:
        # 使用 biomcp article search 命令
        cmd = ["biomcp", "article", "search", "--json"]
        
        # 添加关键词
        for keyword in keywords:
            cmd.extend(["--keyword", keyword])
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error executing BioMCP command: {result.stderr}")
            return []
            
        # 解析 JSON 输出
        try:
            articles_data = json.loads(result.stdout)
            articles = []
            
            for article in articles_data[:max_results]:
                articles.append({
                    'pmid': article.get('pmid', ''),
                    'title': article.get('title', ''),
                    'abstract': article.get('abstract', 'No abstract available'),
                    'year': article.get('date', '').split('-')[0] if article.get('date') else 'Unknown',
                    'doi': article.get('doi', ''),
                    'url': article.get('pubmed_url', '')
                })
                
            return articles
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON output: {e}")
            return []
            
    except Exception as e:
        print(f"Error searching BioMCP: {e}")
        return []

def main():
    # 创建输出目录
    output_dir = "papermd/references"
    os.makedirs(output_dir, exist_ok=True)
    
    # 数据库相关的搜索关键词组合
    search_queries = [
        # 数据库架构和设计
        ["biological", "database", "architecture", "design"],
        ["synthetic", "biology", "database", "schema"],
        ["biological", "parts", "database", "structure"],
        
        # 数据库性能
        ["biological", "database", "performance", "optimization"],
        ["synthetic", "biology", "database", "scalability"],
        ["biological", "parts", "database", "efficiency"],
        
        # 数据库标准化
        ["biological", "database", "standardization", "SBOL"],
        ["synthetic", "biology", "database", "format"],
        ["biological", "parts", "database", "protocol"],
        
        # 数据库验证
        ["biological", "database", "validation", "verification"],
        ["synthetic", "biology", "database", "quality"],
        ["biological", "parts", "database", "testing"],
        
        # 数据库集成
        ["biological", "database", "integration", "federation"],
        ["synthetic", "biology", "database", "interoperability"],
        ["biological", "parts", "database", "connectivity"],
        
        # 数据库搜索
        ["biological", "database", "search", "retrieval"],
        ["synthetic", "biology", "database", "query"],
        ["biological", "parts", "database", "indexing"],
        
        # 数据库API
        ["biological", "database", "API", "interface"],
        ["synthetic", "biology", "database", "REST"],
        ["biological", "parts", "database", "endpoint"],
        
        # 数据库安全
        ["biological", "database", "security", "privacy"],
        ["synthetic", "biology", "database", "authentication"],
        ["biological", "parts", "database", "authorization"],
        
        # 数据库可视化
        ["biological", "database", "visualization", "interface"],
        ["synthetic", "biology", "database", "dashboard"],
        ["biological", "parts", "database", "browser"]
    ]
    
    all_results = []
    
    for keywords in search_queries:
        query_str = " ".join(keywords)
        print(f"\nSearching for: {query_str}")
        results = search_biomcp(keywords)
        all_results.extend(results)
        time.sleep(1)  # 避免请求过快
    
    # 去重
    unique_results = {result['pmid']: result for result in all_results if result.get('pmid')}.values()
    
    # 按年份排序
    sorted_results = sorted(unique_results, key=lambda x: x.get('year', 'Unknown'), reverse=True)
    
    # 保存结果
    output = {
        'search_date': datetime.now().strftime('%Y-%m-%d'),
        'total_results': len(sorted_results),
        'results': sorted_results
    }
    
    output_file = os.path.join(output_dir, 'reference_search_results.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\nFound {len(sorted_results)} unique references")
    print(f"Results have been saved to {output_file}")

if __name__ == "__main__":
    main() 