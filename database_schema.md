# Synbio Parts 数据库结构说明

## 数据库信息
- 数据库名称: `synbio_parts_db`
- 连接地址: `mongodb://localhost:27017`
- 总记录数: 2036条

## 集合结构

### 1. parts 集合
存储生物部件的主要信息集合。

#### 基本信息字段
| 字段路径 | 类型 | 说明 | 示例 |
|---------|------|------|------|
| `id` | string | 唯一标识符 | "b2a9a2cbe74041a7df243abe93bc5bf7" |
| `synbio_parts_id` | string | 生物系统工程ID | "BSE_TEMP00101" |
| `label` | string | 部件标签名 | "4-1BB" |
| `level` | string | 层级类型 | "part" |
| `version` | string | 版本号 | "1.0" |
| `status` | string | 验证状态 | "unverified" |
| `creator` | string | 创建者 | "system" |

#### 序列信息 (`sequence_info`)
| 字段路径 | 类型 | 说明 | 示例 |
|---------|------|------|------|
| `sequence_info.sequence` | string | DNA序列 | "AAACGGGGCA..." |
| `sequence_info.length` | integer | 序列长度 | 126 |
| `sequence_info.gc_content` | float | GC含量 | 0.4206 |

#### 类型信息 (`type_info`)
| 字段路径 | 类型 | 说明 | 示例 |
|---------|------|------|------|
| `type_info.main_type` | string | 主要类型 | "t_cell_signaling_domain" |
| `type_info.sub_types` | array[string] | 子类型列表 | ["Costimulatory domain"] |

#### 注释信息
| 字段路径 | 类型 | 说明 | 示例 |
|---------|------|------|------|
| `notes` | array[string] | 一般注释 | ["4-1BB intracellular costimulatory domain"] |
| `application_notes` | array[string] | 应用说明 | ["Costimulatory domain", "Improves overall survival..."] |

#### 引用信息 (`references`)
| 字段路径 | 类型 | 说明 | 示例 |
|---------|------|------|------|
| `references[].type` | string | 引用类型 | "pubmed", "patent" |
| `references[].id` | string | 引用ID | "" |
| `references[].url` | string | 引用链接 | "https://pubmed.ncbi.nlm.nih.gov/14961035/" |

#### 来源信息 (`source`)
| 字段路径 | 类型 | 说明 | 示例 |
|---------|------|------|------|
| `source.database` | string | 数据库名称 | "SynBio Parts DB" |
| `source.version` | string | 数据库版本 | "V1.2" |
| `source.collection` | string | 集合名称 | "synbio_parts" |
| `source.validation_status` | string | 验证状态 | "unverified" |
| `source.last_updated` | datetime | 最后更新时间 | "2025-03-12T02:46:24.259Z" |

#### 元数据 (`metadata`)
| 字段路径 | 类型 | 说明 | 示例 |
|---------|------|------|------|
| `metadata.organism` | string/null | 生物体 | null |
| `metadata.expression_system` | string/null | 表达系统 | null |
| `metadata.safety_level` | string/null | 安全等级 | null |
| `metadata.storage_conditions` | string/null | 存储条件 | null |

#### 时间戳
| 字段路径 | 类型 | 说明 | 示例 |
|---------|------|------|------|
| `creation_date` | datetime | 创建时间 | "2025-03-12T02:46:24.259Z" |
| `last_modified` | datetime | 最后修改时间 | "2025-03-12T02:46:24.259Z" |

### 2. database_stats 集合
存储数据库统计信息。

| 字段路径 | 类型 | 说明 | 示例 |
|---------|------|------|------|
| `total_parts` | integer | 总部件数 | 2036 |
| `part_types` | array[string] | 所有部件类型列表 | ["3'UTR", "5'UTR", ...] |
| `creation_date` | datetime | 统计创建时间 | "2025-03-12T02:46:24.259Z" |
| `last_update` | datetime | 最后更新时间 | "2025-03-12T02:46:24.259Z" |
| `sequence_length_stats.min` | integer | 最短序列长度 | 10 |
| `sequence_length_stats.max` | integer | 最长序列长度 | 8365 |
| `sequence_length_stats.avg` | float | 平均序列长度 | 765.35 |

## 支持的部件类型
数据库当前支持以下40种部件类型：
1. 3'UTR
2. 5'UTR
3. CDS
4. CDS_marker
5. CDS_reporter
...（其余类型见database_stats集合的part_types字段）

## 查询示例
```python
from pymongo import MongoClient

# 连接数据库
client = MongoClient('mongodb://localhost:27017/')
db = client['synbio_parts_db']
parts = db['parts']

# 按类型查询
results = parts.find({"type_info.main_type": "t_cell_signaling_domain"})

# 按序列长度范围查询
results = parts.find({
    "sequence_info.length": {
        "$gte": 100,
        "$lte": 500
    }
})

# 按GC含量查询
results = parts.find({
    "sequence_info.gc_content": {
        "$gt": 0.4,
        "$lt": 0.6
    }
})
``` 