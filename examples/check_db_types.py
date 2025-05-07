"""
检查数据库中所有可用的部件类型
"""

from pymongo import MongoClient
from collections import defaultdict

def check_db_types():
    # 连接数据库
    client = MongoClient('mongodb://localhost:27017/')
    db = client['synbio_parts_db']
    parts = db['parts']
    
    # 统计每种类型的部件数量
    type_counts = defaultdict(int)
    subtype_counts = defaultdict(int)
    
    # 获取所有部件
    all_parts = parts.find()
    
    print("=== 数据库部件类型统计 ===\n")
    
    for part in all_parts:
        if 'type_info' in part:
            main_type = part['type_info'].get('main_type')
            if main_type:
                type_counts[main_type] += 1
            
            subtypes = part['type_info'].get('sub_types', [])
            for subtype in subtypes:
                subtype_counts[subtype] += 1
    
    print("主要类型统计:")
    for type_name, count in sorted(type_counts.items()):
        print(f"- {type_name}: {count}个")
    
    print("\n子类型统计:")
    for subtype, count in sorted(subtype_counts.items()):
        print(f"- {subtype}: {count}个")
    
    # 检查特定部件
    print("\n特定部件检查:")
    specific_parts = [
        {"label": "4-1BB"},
        {"type_info.main_type": "promoter"},
        {"type_info.main_type": "sig_peptide"},
        {"type_info.main_type": "scfv"},
        {"type_info.main_type": "protein_linker"},
        {"type_info.sub_types": "CD3z"}
    ]
    
    for query in specific_parts:
        count = parts.count_documents(query)
        print(f"- {query}: 找到{count}个")

if __name__ == "__main__":
    check_db_types() 