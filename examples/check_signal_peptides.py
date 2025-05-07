"""
检查信号肽相关的部件
"""

from pymongo import MongoClient
import json

def check_signal_peptides():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['synbio_parts_db']
    parts = db['parts']
    
    # 检查所有可能的信号肽相关记录
    queries = [
        {"type_info.main_type": "sig_peptide"},
        {"type_info.sub_types": "Signal peptide"},
        {"type_info.sub_types": "signal peptide"},
        {"label": {"$regex": "signal.*peptide", "$options": "i"}},
        {"notes": {"$regex": "signal.*peptide", "$options": "i"}}
    ]
    
    print("=== 信号肽部件检查 ===\n")
    
    for query in queries:
        results = list(parts.find(query))
        print(f"查询 {query}:")
        if results:
            print(f"找到 {len(results)} 个结果:")
            for part in results:
                print(f"- {part['label']} ({part['type_info']['main_type']}):")
                print(f"  长度: {part['sequence_info']['length']} bp")
                if 'notes' in part:
                    print(f"  注释: {part['notes']}")
                print()
        else:
            print("未找到结果\n")

if __name__ == "__main__":
    check_signal_peptides() 