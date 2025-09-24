# SynVectorDB githubshare 重构计划

## 当前问题
- 严重的模块导入错误 (`streamlit_version` 模块不存在)
- Streamlit缓存问题导致旧代码残留
- 复杂的依赖关系 (FastAPI, LanceDB, sentence-transformers)
- 多个页面都有错误

## 功能需求分析

### 核心功能 (必须保留)
1. **主页面 (Home.py)**
   - 数据库统计概览
   - 部件类型分布图表
   - npm包说明和API集成信息
   - 联系方式和下载链接

2. **部件浏览器 (parts_browser.py)**
   - 部件列表和筛选
   - 基本搜索功能
   - 部件详情显示

### 可选功能 (简化或移除)
3. **语义搜索 (semantic_search.py)** - 简化为演示说明
4. **问答系统 (qa.py)** - 移除或简化
5. **MCP服务器 (mcp_server.py)** - 移除，用npm包说明替代

## 技术栈简化

### 保留依赖
- streamlit
- pandas
- plotly
- sqlite3 (内置)
- duckdb

### 移除依赖
- FastAPI
- sentence-transformers
- lancedb
- biopython (如果不必要)
- 复杂的缓存机制

## 重构步骤

### Phase 1: 基础设施
1. 创建新的简化 utils.py
2. 创建新的 Home.py (仅基础功能)
3. 测试基础页面运行

### Phase 2: 数据展示
1. 重写数据库连接函数
2. 重写统计图表生成
3. 添加npm包说明

### Phase 3: 部件浏览
1. 重写 parts_browser.py
2. 简化搜索和筛选功能
3. 测试部件列表显示

### Phase 4: 清理和优化
1. 移除不需要的页面
2. 更新requirements.txt
3. 测试完整功能

## 数据库结构 (已知)
- 位置: `../data/parts.db` (SQLite)
- 主表: `parts` (19,850条记录)
- 包含AI分类数据: `organism_classification`

## 目标
- 零错误的本地演示应用
- 快速启动和响应
- 清晰的npm包说明
- 基础的数据浏览功能
