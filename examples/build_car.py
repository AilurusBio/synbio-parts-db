"""
CAR-T质粒构建工具

用法:
python build_car.py --target CD19 --promoter EF1a --costim 4-1BB --signal-peptide Ig-kappa

参数说明：
- target: 靶点 (如 CD19, CD20, BCMA 等)
- promoter: 启动子
- costim: 共刺激结构域 (如 4-1BB, CD28 等)
- signal_peptide: 信号肽
"""

from pymongo import MongoClient
from typing import List, Dict, Optional, Tuple
import json
import re
import argparse
from pathlib import Path

class CARPlasmidBuilder:
    def __init__(self, db_url: str = 'mongodb://localhost:27017/'):
        self.client = MongoClient(db_url)
        self.db = self.client['synbio_parts_db']
        self.parts = self.db['parts']
        
    def find_parts_by_type(self, main_type: str, sub_type: str = None, 
                          label_pattern: str = None) -> List[Dict]:
        """按类型查找部件"""
        queries = []
        if main_type:
            queries.append({"type_info.main_type": main_type})
        if sub_type:
            queries.append({"type_info.sub_types": {"$regex": sub_type, "$options": "i"}})
        if label_pattern:
            queries.append({"label": {"$regex": label_pattern, "$options": "i"}})
            
        final_query = {"$and": queries} if len(queries) > 1 else queries[0] if queries else {}
        return list(self.parts.find(final_query))
        
    def find_part_by_label(self, label: str, fuzzy: bool = True) -> Optional[Dict]:
        """按标签查找部件"""
        if fuzzy:
            return self.parts.find_one({"label": {"$regex": label, "$options": "i"}})
        return self.parts.find_one({"label": label})
    
    def list_available_parts(self, part_type: str) -> List[str]:
        """列出指定类型的所有可用部件"""
        parts = self.find_parts_by_type(part_type)
        return [part['label'] for part in parts]
    
    def find_scfv(self, target: str) -> Optional[Dict]:
        """查找特定靶点的scFv"""
        queries = [
            {"label": {"$regex": f"{target}.*scFv", "$options": "i"}},
            {"label": {"$regex": f"scFv.*{target}", "$options": "i"}},
            {"type_info.main_type": "scfv", "label": {"$regex": target, "$options": "i"}}
        ]
        
        for query in queries:
            result = self.parts.find_one(query)
            if result:
                return result
        return None
    
    def find_signal_peptide(self, name: str = None) -> Optional[Dict]:
        """查找信号肽"""
        if name:
            return self.find_part_by_label(name)
            
        # 默认优先级
        default_signals = ["Ig-kappa leader", "IL2-sig", "CD8-leader"]
        for signal in default_signals:
            part = self.find_part_by_label(signal)
            if part:
                return part
                
        # 如果找不到指定的，返回任意一个信号肽
        sig_peptides = self.find_parts_by_type("sig_peptide")
        return sig_peptides[0] if sig_peptides else None
    
    def find_costim_domain(self, name: str = None) -> Optional[Dict]:
        """查找共刺激结构域"""
        if name:
            return self.find_part_by_label(name)
            
        # 默认使用4-1BB
        return self.find_part_by_label("4-1BB")
    
    def find_cd3z_domain(self) -> Optional[Dict]:
        """查找CD3z结构域"""
        queries = [
            {"label": {"$regex": "CD3.*zeta", "$options": "i"}},
            {"label": {"$regex": "CD3z", "$options": "i"}},
            {"type_info.main_type": "t_cell_signaling_domain", 
             "label": {"$regex": "CD3|zeta|TCR", "$options": "i"}}
        ]
        
        for query in queries:
            result = self.parts.find_one(query)
            if result:
                return result
        return None
    
    def build_car_plasmid(self, target: str, promoter: str = None, 
                         costim: str = None, signal_peptide: str = None,
                         output_dir: str = "output") -> Tuple[Dict, str]:
        """构建CAR-T质粒"""
        # 创建输出目录
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 1. 收集所有部件
        parts_to_find = [
            ("找到启动子", lambda: (
                self.find_part_by_label(promoter) if promoter 
                else self.find_parts_by_type("promoter")[0]
            )),
            ("找到信号肽", lambda: self.find_signal_peptide(signal_peptide)),
            (f"找到{target} scFv", lambda: self.find_scfv(target)),
            ("找到连接序列", lambda: self.find_parts_by_type("protein_linker")[0]),
            ("找到共刺激结构域", lambda: self.find_costim_domain(costim)),
            ("找到CD3z结构域", lambda: self.find_cd3z_domain()),
            ("找到终止子", lambda: self.find_parts_by_type("terminator")[0])
        ]
        
        sequences = []
        print("\n=== 部件查找过程 ===")
        
        for desc, finder in parts_to_find:
            part = finder()
            if part:
                print(f"✓ {desc}: {part['label']} ({part['sequence_info']['length']} bp)")
                if 'notes' in part and part['notes']:
                    print(f"  注释: {part['notes'][0]}")
                sequences.append(part)
            else:
                raise Exception(f"未找到所需部件: {desc}")
        
        # 2. 生成报告
        report = {
            "target": target,
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
        
        # 3. 保存文件
        base_name = f"CAR_{target}"
        if costim:
            base_name += f"_{costim}"
            
        report_file = f"{output_dir}/{base_name}_report.json"
        fasta_file = f"{output_dir}/{base_name}.fasta"
        
        # 保存报告
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        # 保存序列
        with open(fasta_file, "w") as f:
            f.write(f">{base_name}\n")
            seq = report["full_sequence"]
            for i in range(0, len(seq), 60):
                f.write(seq[i:i+60] + "\n")
                
        return report, base_name

def list_available_options(builder: CARPlasmidBuilder):
    """列出所有可用选项"""
    print("\n=== 可用部件列表 ===")
    
    # 列出启动子
    promoters = builder.list_available_parts("promoter")
    print("\n启动子:")
    for p in promoters[:5]:
        print(f"- {p}")
    if len(promoters) > 5:
        print(f"... 等{len(promoters)}个")
        
    # 列出信号肽
    signal_peptides = builder.list_available_parts("sig_peptide")
    print("\n信号肽:")
    for sp in signal_peptides[:5]:
        print(f"- {sp}")
    if len(signal_peptides) > 5:
        print(f"... 等{len(signal_peptides)}个")
        
    # 列出共刺激结构域
    costims = builder.find_parts_by_type("t_cell_signaling_domain")
    print("\n共刺激结构域:")
    for c in costims[:5]:
        print(f"- {c['label']}")
    if len(costims) > 5:
        print(f"... 等{len(costims)}个")

def main():
    parser = argparse.ArgumentParser(description="CAR-T质粒构建工具")
    parser.add_argument("--target", help="靶点 (如 CD19, CD20, BCMA)")
    parser.add_argument("--promoter", help="启动子名称")
    parser.add_argument("--costim", help="共刺激结构域 (如 4-1BB, CD28)")
    parser.add_argument("--signal-peptide", help="信号肽名称")
    parser.add_argument("--output-dir", default="output", help="输出目录")
    parser.add_argument("--list", action="store_true", help="列出所有可用部件")
    
    args = parser.parse_args()
    
    # 创建构建器
    builder = CARPlasmidBuilder()
    
    # 如果是列出可用部件
    if args.list:
        list_available_options(builder)
        return
        
    # 检查是否提供了target参数
    if not args.target:
        parser.error("构建质粒时必须提供 --target 参数")
        
    try:
        # 构建质粒
        report, base_name = builder.build_car_plasmid(
            target=args.target,
            promoter=args.promoter,
            costim=args.costim,
            signal_peptide=args.signal_peptide,
            output_dir=args.output_dir
        )
        
        # 输出报告
        print(f"\n=== {base_name} 质粒组装报告 ===")
        print(f"总长度: {report['total_length']} bp")
        print(f"总GC含量: {report['gc_content']:.2%}")
        print("\n组成部分:")
        for part in report["plasmid_components"]:
            print(f"- {part['name']} ({part['type']}):")
            print(f"  长度: {part['length']} bp")
            print(f"  GC含量: {part['gc_content']:.2%}")
            if part.get("notes"):
                print(f"  注释: {part['notes'][0]}")
                
        print(f"\n序列和报告已保存到 {args.output_dir} 目录")
        
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    main() 