# MongoDB数据模型设计

## 零件集合 (parts)

```javascript
{
  // 基本信息
  "part_id": "BSP001",           // 零件唯一标识符
  "name": "GFP",                 // 零件名称
  "description": "...",          // 功能描述
  "category": {                  // 功能分类
    "main_type": "reporter",     // 主要类型
    "sub_type": "fluorescent"    // 子类型
  },
  
  // 来源信息
  "source": {
    "organism": "A. victoria",   // 原始生物体
    "designer": "Zhang Lab",     // 设计者
    "references": [              // 文献引用
      {
        "doi": "10.1093/...",
        "pmid": "12345678",
        "title": "..."
      }
    ]
  },
  
  // 序列信息
  "sequence": {
    "full": "ATGGTG...",        // 完整序列
    "core": "ATGGTG...",        // 核心功能序列
    "prefix": "GAATTC...",      // 5'标准接口
    "suffix": "CTGCAG..."       // 3'标准接口
  },
  
  // 工程特性
  "engineering": {
    // 表达系统
    "expression": {
      "promoter_strength": "strong",
      "induction": {
        "inducer": "IPTG",
        "concentration": "1mM"
      },
      "dynamics": {
        "response_time": "30min",
        "peak_time": "4h"
      }
    },
    
    // 组装特性
    "assembly": {
      "standard": "BioBrick",
      "restriction_sites": ["EcoRI", "XbaI", "SpeI", "PstI"],
      "instructions": "..."
    },
    
    // 兼容性
    "compatibility": {
      "vectors": ["pSB1C3", "pSB3K3"],
      "hosts": ["E. coli DH5α", "E. coli BL21"],
      "verified_combinations": [
        {
          "vector": "pSB1C3",
          "host": "E. coli DH5α",
          "success_rate": 0.95
        }
      ]
    }
  },
  
  // 实验数据
  "experimental_data": {
    // 表达验证
    "expression_validation": {
      "western_blot": {
        "image_url": "...",
        "description": "..."
      },
      "fluorescence": {
        "excitation": 488,
        "emission": 509,
        "intensity": 1000
      }
    },
    
    // 功能测试
    "functional_tests": {
      "activity": {
        "value": 1000,
        "unit": "RFU"
      },
      "kinetics": {
        "km": 0.5,
        "vmax": 100
      }
    },
    
    // 稳定性
    "stability": {
      "genetic": {
        "generations": 50,
        "mutation_rate": 0.001
      },
      "expression": {
        "cv": 0.1,
        "half_life": "24h"
      }
    },
    
    // 安全性
    "safety": {
      "toxicity": "low",
      "metabolic_burden": 0.1,
      "growth_impact": -0.05
    }
  },
  
  // 使用统计
  "usage_stats": {
    "downloads": 100,
    "success_cases": 45,
    "failure_cases": 5,
    "average_rating": 4.5
  },
  
  // 元数据
  "metadata": {
    "created_at": ISODate("2024-03-12"),
    "updated_at": ISODate("2024-03-12"),
    "version": "1.0"
  }
}
```

## 索引设计

```javascript
// 创建索引
db.parts.createIndex({"part_id": 1}, {unique: true})
db.parts.createIndex({"name": 1})
db.parts.createIndex({"category.main_type": 1})
db.parts.createIndex({"category.sub_type": 1})
db.parts.createIndex({"engineering.compatibility.vectors": 1})
db.parts.createIndex({"engineering.compatibility.hosts": 1})
db.parts.createIndex({"sequence.full": "text"})
```

## 数据验证规则

```javascript
{
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["part_id", "name", "category", "sequence"],
      properties: {
        part_id: {
          bsonType: "string",
          pattern: "^BSP\\d{3}$"
        },
        name: {
          bsonType: "string",
          minLength: 1
        },
        category: {
          bsonType: "object",
          required: ["main_type"],
          properties: {
            main_type: {
              enum: ["reporter", "regulatory", "coding", "structural"]
            }
          }
        }
      }
    }
  }
} 