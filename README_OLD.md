# SynVectorDB - Synthetic Biology Parts Database

[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](./test_suite.py)
[![Python](https://img.shields.io/badge/python-3.8+-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Overview

SynVectorDB is a comprehensive synthetic biology parts database featuring semantic search capabilities and multi-format data export. This repository contains the **githubshare** version - a standalone, simplified deployment for local use and demonstration purposes.

## Key Features

- 🔍 **Advanced Search**: Text-based and filtered search across 19,850+ biological parts
- 📊 **Interactive Visualizations**: Real-time statistics and data distribution charts
- 🧬 **Comprehensive Data**: Complete part information including sequences, types, and metadata
- 📈 **Performance Analytics**: Built-in performance monitoring and benchmarking
- 🌐 **Web Interface**: Modern Streamlit-based user interface
- 🔌 **API Integration**: Documentation for MCP Server and REST API integration

## System Requirements

- **Python**: 3.8 or higher
- **Memory**: 4GB+ RAM recommended
- **Storage**: 2GB+ available disk space
- **OS**: Linux, macOS, or Windows

## Quick Start

### Automated Setup

#### Linux/macOS
```bash
# Clone or download the project
cd synvectordb

# Run the startup script
./start.sh
```

#### Windows
```cmd
# Navigate to project directory
cd synvectordb

# Run the startup script
start.bat
```

### Manual Installation

If automated scripts fail, install manually:

```bash
# Install dependencies
cd streamlit_app
pip install -r requirements.txt

# Start the application
streamlit run Home.py --server.port 8501
```

### Using Management Script

The project includes a comprehensive management script:

```bash
# Start the service
./manage.sh start

# Check status
./manage.sh status

# Run tests
./manage.sh test

# View logs
./manage.sh logs

# Stop the service
./manage.sh stop
```

## Project Structure

```
synvectordb/
├── data/                   # Database files
│   ├── parts.duckdb       # Main database (DuckDB format)
│   ├── parts.db           # SQLite database
│   └── parts.lance/       # Vector database (LanceDB)
├── streamlit_app/         # Streamlit application
│   ├── Home.py           # Main page
│   ├── pages/            # Sub-pages
│   │   ├── parts_browser.py    # Parts browser
│   │   ├── semantic_search.py  # Semantic search
│   │   └── statistics.py       # Data analytics
│   └── utils.py          # Utility functions
├── logs/                  # Application logs
├── test_suite.py         # Comprehensive test suite
├── manage.sh             # Management script
└── README.md             # This file
```

## Usage Guide

### 1. Database Overview
- View comprehensive statistics of 19,850+ biological parts
- Explore data distribution across function types and sources
- Monitor system performance and data quality

### 2. Parts Browser
- **Text Search**: Search by part names and descriptions
- **Advanced Filtering**: Filter by function type, data source
- **Detailed View**: Access complete part information including sequences
- **Export Options**: Download search results and part details

### 3. Semantic Search (Demo)
- **Natural Language Queries**: Search using biological terminology
- **Example Queries**: Pre-configured search examples
- **Production Links**: Access to full semantic search capabilities

### 4. Statistics & Analytics
- **Interactive Charts**: Visualize data distributions and trends
- **Performance Metrics**: Monitor query and search performance
- **Data Export**: Download statistical summaries in CSV format

## Performance Benchmarks

Based on comprehensive testing with 19,850 parts:

| Operation | Average Time | Performance |
|-----------|--------------|-------------|
| Database Connection | 3.4s | ✅ Acceptable |
| Basic Statistics | 2.4s | ✅ Acceptable |
| Text Search | 1.1s | ✅ Fast |
| Filtered Search | 1.1s | ✅ Fast |
| Data Integrity | 100% | ✅ Excellent |

## Data Sources

- **Addgene**: Plasmid repository with verified constructs
- **iGEM**: International Genetically Engineered Machine registry
- **Laboratory Collections**: Curated experimental data

## Technical Stack

- **Frontend**: Streamlit 1.28+
- **Database**: SQLite, DuckDB
- **Visualization**: Plotly, Pandas
- **Performance**: Built-in benchmarking and monitoring
- **Testing**: Comprehensive test suite with 100% coverage

## API Integration

### MCP Server (NPM Package)
```bash
npm install synvectordb-mcp-server
```

### REST API
```bash
# Base URL: https://testsdb.sjtu.bio
curl "https://testsdb.sjtu.bio/parts/search?organism=Mammalian&page_size=10"
```

## Testing

Run the comprehensive test suite:

```bash
# Execute all tests
python3 test_suite.py

# Expected output: 4/4 tests passed (100.0%)
```

The test suite covers:
- ✅ Database functionality and connectivity
- ✅ Streamlit application responsiveness
- ✅ Performance benchmarks
- ✅ Data integrity validation

## Development

### Code Quality
- **Type Hints**: Comprehensive type annotations
- **Documentation**: Detailed docstrings and comments
- **Error Handling**: Robust exception management
- **Performance**: Optimized database queries and caching

### Contributing
1. Fork the repository
2. Create a feature branch
3. Run the test suite
4. Submit a pull request

## Deployment

### Local Development
```bash
./manage.sh start
# Access: http://localhost:8501
```

### Production Deployment
- **Frontend**: https://app.sjtu.bio
- **Backend API**: https://testsdb.sjtu.bio
- **Data Downloads**: https://r2data.sjtu.bio

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

**Principal Investigator**: Dr. Jie Song  
**Email**: jiesong@whu.edu.cn  
**Institution**: Wuhan University

## Citation

If you use SynVectorDB in your research, please cite:

```bibtex
@software{synvectordb2024,
  title={SynVectorDB: A Comprehensive Synthetic Biology Parts Database},
  author={Song, Jie and contributors},
  year={2024},
  url={https://github.com/AilurusBio/synbio-parts-db}
}
```

---

**Note**: This is the githubshare demonstration version. For production features including full semantic search capabilities, please visit [app.sjtu.bio](https://app.sjtu.bio).
