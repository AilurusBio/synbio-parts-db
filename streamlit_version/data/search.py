import pandas as pd
from pathlib import Path
import lancedb
from sentence_transformers import SentenceTransformer
import argparse
import requests
import json

class SemanticSearch:
    def __init__(self):
        # 设置路径
        data_dir = Path(__file__).parent
        self.db_path = data_dir / "parts.lance"
        self.cache_dir = data_dir / "models"
        
        # 检查数据库是否存在
        if not self.db_path.exists():
            raise FileNotFoundError("数据库不存在，请先运行 init_db.py 初始化数据库")
        
        # 检查模型是否存在
        model_dir = self.cache_dir / "models--sentence-transformers--all-MiniLM-L6-v2"
        if not model_dir.exists():
            raise FileNotFoundError("模型不存在，请先运行 download_model.py 下载模型")
        
        # 加载数据库
        self.db = lancedb.connect(self.db_path)
        self.table = self.db.open_table("embeddings")
        
        # 加载模型
        self.model = SentenceTransformer(
            'all-MiniLM-L6-v2',
            cache_folder=str(self.cache_dir),
            local_files_only=True  # 禁用网络检查
        )
    
    def optimize_query(self, query: str) -> str:
        """使用 DeepSeek 优化搜索语句"""
        try:
            # DeepSeek API 配置
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Authorization": "Bearer sk-67eade3849cb4a0396471a89cc22fa1c",  # 需要替换为实际的 API key
                "Content-Type": "application/json"
            }
            
            # 构建提示词
            prompt = f"""请优化以下搜索语句，使其更适合搜索生物零件数据库。保持简洁，专注于关键特征。
原始搜索语句: {query}
优化后的搜索语句:"""
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是一个专业的生物信息学搜索优化助手。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 100
            }
            
            # 发送请求
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            optimized_query = result['choices'][0]['message']['content'].strip()
            
            print(f"\n原始搜索语句: {query}")
            print(f"优化后的搜索语句: {optimized_query}")
            
            return optimized_query
            
        except Exception as e:
            print(f"\n优化搜索语句时出错: {e}")
            print("使用原始搜索语句继续...")
            return query
    
    def search(self, query: str, top_k: int = 5, optimize: bool = False):
        """执行语义搜索"""
        # 优化搜索语句
        if optimize:
            query = self.optimize_query(query)
        
        # 计算查询文本的嵌入向量
        query_embedding = self.model.encode([query])[0]
        
        # 使用 LanceDB 的向量搜索
        results = self.table.search(query_embedding).limit(top_k).to_list()
        
        # 格式化结果
        formatted_results = []
        for result in results:
            formatted_results.append({
                'name': result['name'],
                'type': result['type'],
                'description': result['description'],
                'similarity': float(result['_distance'])  # LanceDB 返回的距离
            })
        
        return formatted_results

def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='生物零件语义搜索工具')
    parser.add_argument('query', type=str, help='搜索查询文本')
    parser.add_argument('--top_k', type=int, default=5, help='返回结果数量 (默认: 5)')
    parser.add_argument('--output', type=str, help='输出文件路径 (可选)')
    parser.add_argument('--optimize', action='store_true', help='使用 DeepSeek 优化搜索语句')
    
    args = parser.parse_args()
    
    # 创建搜索实例
    searcher = SemanticSearch()
    
    # 执行搜索
    print(f"\n搜索查询: {args.query}")
    results = searcher.search(args.query, top_k=args.top_k, optimize=args.optimize)
    
    # 打印结果
    print("\n搜索结果:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. 相似度: {result['similarity']:.4f}")
        print(f"名称: {result['name']}")
        print(f"类型: {result['type']}")
        print(f"描述: {result['description'][:200]}...")
    
    # 如果指定了输出文件，保存结果
    if args.output:
        output_df = pd.DataFrame(results)
        output_df.to_csv(args.output, index=False, encoding='utf-8')
        print(f"\n结果已保存到: {args.output}")

if __name__ == "__main__":
    main() 