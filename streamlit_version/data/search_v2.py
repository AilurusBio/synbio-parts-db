import pandas as pd
from pathlib import Path
import lancedb
from sentence_transformers import SentenceTransformer
import argparse
import requests
import json
import os
from openai import OpenAI
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SemanticSearch:
    def __init__(self):
        start_time = time.time()
        # 获取项目根目录（当前文件所在目录的父目录的父目录）
        self.root_dir = Path(__file__).parent.parent.parent
        self.data_dir = self.root_dir / "streamlit_version" / "data"
        self.db_path = self.data_dir / "parts.lance"
        self.cache_dir = self.data_dir / "models"
        
        # 定义source_collection映射
        self.source_mapping = {
            "iGEM registry": "igem",
            "iGEM": "igem",
            "igem": "igem",
            "laboratory": "lab",
            "lab": "lab",
            "addgene": "addgene",
            "snapgene": "snapgene",
            "yunzhou": "yunzhou"
        }
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}. Please run init_db.py first.")
        
        model_dir = self.cache_dir / "models--sentence-transformers--all-MiniLM-L6-v2"
        if not model_dir.exists():
            raise FileNotFoundError(f"Model not found at {model_dir}. Please run download_model.py first.")
        
        self.db = lancedb.connect(self.db_path)
        self.table = self.db.open_table("embeddings")
        
        self.model = SentenceTransformer(
            'all-MiniLM-L6-v2',
            cache_folder=str(self.cache_dir),
            local_files_only=True
        )
        print(f"Model loaded in {time.time() - start_time:.2f} seconds")
        
        # 初始化 DeepSeek API 客户端
        self.client = OpenAI(
            base_url="https://api.deepseek.com"
        )
    
    def optimize_query(self, query: str) -> dict:
        """使用DeepSeek API优化查询"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的查询优化助手。请帮助优化用户的查询，使其更准确、更具体。"},
                    {"role": "user", "content": query}
                ],
                api_key=os.getenv("DEEPSEEK_API_KEY"),
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"查询优化失败: {str(e)}")
            return query
    
    def search(self, query: str, top_k: int = 5, optimize: bool = False, 
              types: list = None, source_collections: list = None) -> dict:
        """Execute semantic search with filters"""
        start_time = time.time()
        response = {
            "query": query,
            "optimize": optimize,
            "top_k": top_k,
            "filters": {
                "types": types,
                "source_collections": source_collections
            },
            "results": []
        }
        
        if optimize:
            optimization_result = self.optimize_query(query)
            response["optimization"] = optimization_result
            
            if optimization_result != query:
                query = optimization_result
                # 使用语义解析的筛选条件
                filters = {}
                if types:
                    filters["include_types"] = types
                if source_collections:
                    filters["include_sources"] = source_collections
        
        # 计算查询向量
        query_embedding = self.model.encode([query])[0]
        
        # 构建查询条件
        where = []
        if types:
            type_conditions = []
            for t in types:
                # 根据source_collection使用不同的匹配规则
                if source_collections and 'igem' in source_collections:
                    # igem数据使用type_level_1和type_level_2
                    if t.lower() == 'promoter':
                        type_conditions.extend([
                            "type_level_1 = 'DNA Elements'",
                            "type_level_2 = 'Regulatory'",
                            "name LIKE '%promoter%'"
                        ])
                    else:
                        type_conditions.extend([
                            f"type_level_1 = '{t}'",
                            f"type_level_2 = '{t}'"
                        ])
                else:
                    # 其他数据使用type字段
                    type_conditions.append(f"type = '{t}'")
            where.append(f"({' OR '.join(type_conditions)})")
            
        if source_collections:
            source_list = ", ".join([f"'{s}'" for s in source_collections])
            where.append(f"source_collection IN ({source_list})")
        
        # 执行搜索
        if where:
            where_clause = " AND ".join(where)
            print(f"\nDebug - SQL where clause: {where_clause}")
            results = self.table.search(query_embedding).where(where_clause).limit(top_k).to_list()
        else:
            results = self.table.search(query_embedding).limit(top_k).to_list()
        
        for result in results:
            response["results"].append({
                'name': result['name'],
                'type': result['type'],
                'description': result['description'],
                'source_collection': result.get('source_collection', ''),
                'source_name': result.get('source_name', ''),
                'similarity': float(result['_distance'])
            })
        
        print(f"Search completed in {time.time() - start_time:.2f} seconds")
        return response

def main():
    start_time = time.time()
    parser = argparse.ArgumentParser(description='Biological Parts Semantic Search Tool')
    parser.add_argument('query', type=str, help='Search query text')
    parser.add_argument('--top_k', type=int, default=5, help='Number of results to return (default: 5)')
    parser.add_argument('--output', type=str, help='Output file path (optional)')
    parser.add_argument('--optimize', action='store_true', help='Use DeepSeek to optimize query')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--type', nargs='+', help='Filter by part type (e.g., --type promoter terminator)')
    parser.add_argument('--source', nargs='+', help='Filter by source collection (e.g., --source igem addgene)')
    
    args = parser.parse_args()
    
    # 切换到项目根目录
    root_dir = Path(__file__).parent.parent.parent
    os.chdir(root_dir)
    
    searcher = SemanticSearch()
    results = searcher.search(
        args.query, 
        top_k=args.top_k, 
        optimize=args.optimize,
        types=args.type,
        source_collections=args.source
    )
    
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        if args.optimize and "optimization" in results:
            opt = results["optimization"]
            if opt != results["query"]:
                print(f"\nOriginal query: {results['query']}")
                print(f"Optimized query: {opt}")
            else:
                print(f"\nQuery optimization failed: {opt}")
        
        print("\nSearch Results:")
        for i, result in enumerate(results["results"], 1):
            print(f"\n{i}. Similarity: {result['similarity']:.4f}")
            print(f"Name: {result['name']}")
            print(f"Type: {result['type']}")
            if result.get('source_collection'):
                print(f"Source: {result['source_collection']}")
            print(f"Description: {result['description'][:200]}...")
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {args.output}")
    
    print(f"Total execution time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()