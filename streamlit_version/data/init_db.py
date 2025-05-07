import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
import lancedb
from tqdm import tqdm
import pyarrow as pa
import os
import shutil

def init_db():
    """初始化 LanceDB 数据库"""
    # 设置路径
    data_dir = Path(__file__).parent
    db_path = Path("/tmp/parts.lance")  # 改用 Linux 临时目录
    cache_dir = data_dir / "models"
    
    # 检查模型是否存在
    model_dir = cache_dir / "models--sentence-transformers--all-MiniLM-L6-v2"
    if not model_dir.exists():
        raise FileNotFoundError("模型不存在，请先运行 download_model.py 下载模型")
    
    # 加载数据
    print("正在加载数据...")
    df = pd.read_parquet(data_dir / "parts.parquet")
    print("数据加载完成，source_collection分布：")
    print(df['source_collection'].value_counts())
    
    # 准备搜索文本
    print("正在准备搜索文本...")
    search_texts = []
    for _, row in df.iterrows():
        text = f"{row['name']} {row['type']} {row['description']}"
        search_texts.append(text)
    
    # 加载模型
    print("正在加载模型...")
    model = SentenceTransformer(
        'all-MiniLM-L6-v2',
        cache_folder=str(cache_dir),
        local_files_only=True  # 禁用网络检查
    )
    
    # 计算向量
    print("正在计算文本嵌入向量...")
    embeddings = model.encode(search_texts, show_progress_bar=True)
    
    # 初始化数据库
    print("正在初始化数据库...")
    if db_path.exists():
        print("删除现有数据库...")
        shutil.rmtree(db_path)
    
    # 定义 schema
    schema = pa.schema([
        ('id', pa.int32()),
        ('vector', pa.list_(pa.float32(), 384)),  # MiniLM-L6-v2 输出维度
        ('text', pa.string()),
        ('name', pa.string()),
        ('type', pa.string()),
        ('type_level_1', pa.string()),
        ('type_level_2', pa.string()),
        ('description', pa.string()),
        ('source_collection', pa.string())
    ])
    
    db = lancedb.connect(db_path)
    table = db.create_table("embeddings", schema=schema)
    
    # 保存数据
    print("正在保存数据到数据库...")
    
    # 批量插入数据
    data = []
    for i, (text, vector) in enumerate(tqdm(zip(search_texts, embeddings), total=len(search_texts))):
        row = df.iloc[i]
        data.append({
            "id": i,
            "vector": vector.tolist(),  # 转换为列表
            "text": text,
            "name": row['name'],
            "type": row['type'],
            "type_level_1": row['type_level_1'],
            "type_level_2": row['type_level_2'],
            "description": row['description'],
            "source_collection": row['source_collection']
        })
    
    table.add(data)
    print("数据库初始化完成！")
    
    # 创建符号链接
    target_path = data_dir / "parts.lance"
    if target_path.exists():
        if target_path.is_symlink():
            os.unlink(target_path)
        else:
            shutil.rmtree(target_path)
    os.symlink(db_path, target_path)
    print(f"创建符号链接: {target_path} -> {db_path}")

if __name__ == "__main__":
    init_db() 