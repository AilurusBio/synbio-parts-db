"""
CAR-T质粒构建示例

目的：从数据库中检索必要的部件并构建CAR-T质粒
组成部分：
1. 启动子 (promoter)
2. 信号肽 (Ig-kappa leader)
3. scFv
4. 铰链区 (linker)
5. 共刺激结构域 (4-1BB)
6. CD3z结构域
7. 终止子 (terminator)
"""

from pymongo import MongoClient
from typing import List, Dict, Optional
import json
import re

class PlasmidAssembler:
    def __init__(self):
        # 连接数据库
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['synbio_parts_db']
        self.parts = self.db['parts']
        
    def find_part_by_type(self, main_type: str, sub_type: str = None, label_pattern: str = None) -> List[Dict]:
        """按类型查找部件，支持标签模式匹配"""
        queries = []
        
        # 主类型查询
        if main_type:
            type_query = {"type_info.main_type": main_type}
            queries.append(type_query)
        
        # 子类型查询
        if sub_type:
            subtype_query = {"type_info.sub_types": {"$regex": sub_type, "$options": "i"}}
            queries.append(subtype_query)
            
        # 标签模式查询
        if label_pattern:
            label_query = {"label": {"$regex": label_pattern, "$options": "i"}}
            queries.append(label_query)
            
        # 组合查询
        if len(queries) > 1:
            final_query = {"$and": queries}
        elif len(queries) == 1:
            final_query = queries[0]
        else:
            final_query = {}
            
        return list(self.parts.find(final_query))
    
    def find_part_by_label(self, label: str, fuzzy: bool = True) -> Optional[Dict]:
        """按标签查找部件，支持模糊匹配"""
        if fuzzy:
            return self.parts.find_one({"label": {"$regex": label, "$options": "i"}})
        return self.parts.find_one({"label": label})
    
    def find_signal_peptide(self) -> Optional[Dict]:
        """查找合适的信号肽"""
        # 优先尝试Ig-kappa leader
        ig_kappa = self.find_part_by_label("Ig-kappa leader")
        if ig_kappa:
            return ig_kappa
            
        # 其次尝试IL2信号肽
        il2_sig = self.find_part_by_label("IL2-sig")
        if il2_sig:
            return il2_sig
            
        # 最后尝试其他信号肽
        sig_peptides = self.find_part_by_type("sig_peptide")
        if sig_peptides:
            return sig_peptides[0]
            
        return None
    
    def find_cd3z_domain(self) -> Optional[Dict]:
        """特殊处理：查找CD3z结构域"""
        # 尝试多种可能的查询方式
        queries = [
            {"label": {"$regex": "CD3.*zeta", "$options": "i"}},
            {"label": {"$regex": "CD3z", "$options": "i"}},
            {"type_info.sub_types": {"$regex": "CD3.*zeta", "$options": "i"}},
            {"type_info.main_type": "t_cell_signaling_domain", 
             "label": {"$regex": "CD3|zeta|TCR", "$options": "i"}}
        ]
        
        for query in queries:
            result = self.parts.find_one(query)
            if result:
                return result
        return None
    
    def assemble_car_t_plasmid(self):
        """组装CAR-T质粒"""
        # 1. 获取所需部件
        parts_to_find = [
            (("promoter", None, None), "找到启动子"),
            ((None, None, None), "找到信号肽"),  # 特殊处理信号肽
            (("scfv", None, None), "找到scFv"),
            (("protein_linker", None, None), "找到连接序列"),
            ((None, None, "4-1BB"), "找到4-1BB共刺激结构域"),
            ((None, None, None), "找到CD3z结构域"),  # 特殊处理CD3z
            (("terminator", None, None), "找到终止子")
        ]
        
        sequences = []
        print("\n=== 部件查找过程 ===")
        
        for (main_type, sub_type, label), desc in parts_to_find:
            if desc == "找到信号肽":
                part = self.find_signal_peptide()
            elif desc == "找到CD3z结构域":
                part = self.find_cd3z_domain()
            elif label == "4-1BB":
                part = self.find_part_by_label("4-1BB")
            else:
                results = self.find_part_by_type(main_type, sub_type)
                part = results[0] if results else None
                
            if part:
                print(f"✓ {desc}: {part['label']} ({part['sequence_info']['length']} bp)")
                if 'notes' in part and part['notes']:
                    print(f"  注释: {part['notes'][0]}")
                sequences.append(part)
            else:
                raise Exception(f"未找到所需部件: {desc}")
        
        # 2. 生成报告
        report = {
            "plasmid_components": [],
            "total_length": 0,
            "gc_content": 0,
            "full_sequence": ""
        }
        
        full_seq = ""
        for part in sequences:
            seq = part["sequence_info"]["sequence"]
            full_seq += seq
            report["plasmid_components"].append({
                "name": part["label"],
                "type": part["type_info"]["main_type"],
                "length": len(seq),
                "gc_content": part["sequence_info"]["gc_content"],
                "notes": part.get("notes", [])
            })
        
        report["full_sequence"] = full_seq
        report["total_length"] = len(full_seq)
        report["gc_content"] = (full_seq.count('G') + full_seq.count('C')) / len(full_seq)
        
        return report

def main():
    # 创建组装器实例
    assembler = PlasmidAssembler()
    
    # 组装质粒
    try:
        result = assembler.assemble_car_t_plasmid()
        
        # 输出报告
        print("\n=== CAR-T质粒组装报告 ===")
        print(f"总长度: {result['total_length']} bp")
        print(f"总GC含量: {result['gc_content']:.2%}")
        print("\n组成部分:")
        for part in result["plasmid_components"]:
            print(f"- {part['name']} ({part['type']}):")
            print(f"  长度: {part['length']} bp")
            print(f"  GC含量: {part['gc_content']:.2%}")
            if part.get("notes"):
                print(f"  注释: {part['notes'][0]}")
        
        # 将完整报告保存到文件
        with open("examples/car_t_plasmid_report.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        # 将序列保存到FASTA文件
        with open("examples/car_t_plasmid.fasta", "w") as f:
            f.write(">CAR-T_Plasmid\n")
            seq = result["full_sequence"]
            # 每行输出60个碱基
            for i in range(0, len(seq), 60):
                f.write(seq[i:i+60] + "\n")
                
        print("\n序列已保存到 car_t_plasmid.fasta")
        print("完整报告已保存到 car_t_plasmid_report.json")
        
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    main() 