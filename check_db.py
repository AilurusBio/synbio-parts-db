from pymongo import MongoClient
import json
from datetime import datetime
from bson import json_util

def check_data_format():
    # 连接数据库
    client = MongoClient('mongodb://localhost:27017/')
    
    # 显示所有数据库
    print("所有数据库:", client.list_database_names())
    
    # 遍历每个数据库
    for db_name in client.list_database_names():
        if db_name not in ['admin', 'config', 'local']:  # 跳过系统数据库
            db = client[db_name]
            print(f"\n数据库 '{db_name}' 的集合:")
            collections = db.list_collection_names()
            print(collections)
            
            # 检查每个集合的结构
            for coll_name in collections:
                collection = db[coll_name]
                print(f"\n集合 '{coll_name}' 的样本数据:")
                sample = collection.find_one()
                if sample:
                    # 移除_id字段以便更好地显示
                    if '_id' in sample:
                        del sample['_id']
                    print(json.dumps(sample, indent=2, default=json_util.default, ensure_ascii=False))
                    print(f"总记录数: {collection.count_documents({})}")
                    
                    # 显示字段结构
                    print("\n字段结构:")
                    for key, value in sample.items():
                        print(f"{key}: {type(value).__name__}")
                else:
                    print("集合为空")

if __name__ == "__main__":
    check_data_format() 