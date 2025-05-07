"""
检查CAR-T质粒所需部件的可用性
"""

from pymongo import MongoClient
from typing import List, Dict
import json

def check_available_parts():
    # 连接数据库
    client = MongoClient('mongodb://localhost:27017/')
    db = client['synbio_parts_db']
    parts = db['parts']
    
    # 要检查的部件类型
    required_parts = [
        ("promoter", None),
        ("sig_peptide", None),
        ("scfv", None),
        ("protein_linker", None),
        ("t_cell_signaling_domain", None),
        ("terminator", None)
    ]
    
    print("=== 可用部件检查 ===")
    for main_type, sub_type in required_parts:
        query = {"type_info.main_type": main_type}
        if sub_type:
            query["type_info.sub_types"] = sub_type
            
        results = list(parts.find(query))
        print(f"\n{main_type}:")
        if results:
            print(f"找到 {len(results)} 个部件:")
            for part in results[:3]:  # 只显示前3个
                print(f"- {part['label']} (长度: {part['sequence_info']['length']} bp)")
            if len(results) > 3:
                print(f"... 等 {len(results)} 个部件")
        else:
            print("未找到部件")
    
    # 特别检查4-1BB
    bb_result = parts.find_one({"label": "4-1BB"})
    print("\n4-1BB:")
    if bb_result:
        print(f"找到 4-1BB (长度: {bb_result['sequence_info']['length']} bp)")
    else:
        print("未找到 4-1BB")

if __name__ == "__main__":
    check_available_parts() 