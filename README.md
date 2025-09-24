# SynVectorDB Local Deployment

**Local Deployment Version of SynVectorDB: Embedding-Based Retrieval System for Synthetic Biology Parts**

This repository contains a standalone, local deployment of SynVectorDB designed for educational, research, and demonstration purposes. SynVectorDB is a comprehensive embedding-based retrieval system that addresses critical challenges in synthetic biology part discovery through AI-driven semantic search and systematic data curation.

## 📖 About SynVectorDB

SynVectorDB represents a methodological breakthrough in biological part organization and retrieval, developed through collaborative research between Shanghai Jiao Tong University, Beijing Xunzhu Biotechnology, and The University of Queensland. The system addresses fundamental limitations in existing synthetic biology repositories through:

- **Advanced Data Integration**: Systematic curation of 19,850 biological parts from multiple authoritative sources
- **AI-Powered Semantic Search**: BGE-M3 multilingual embeddings enabling context-aware part discovery
- **Hierarchical Classification**: Novel three-level taxonomy organizing parts into functionally coherent categories
- **Standardized Curation**: Literature-based validation protocols achieving 7,656 verified parts
- **SBOL3 Compatibility**: Full compliance with synthetic biology open language standards

### Research Impact

This work has been developed as part of ongoing research in synthetic biology informatics, with findings contributing to improved methodologies for biological part discovery and organization. The system demonstrates significant performance improvements over traditional keyword-based retrieval methods through embedding-based semantic matching.

## 🚀 Quick Start

### Automated Setup (Recommended)
```bash
# Clone the repository
git clone https://github.com/AilurusBio/synbio-parts-db.git
cd synbio-parts-db

# Run automated setup (downloads data, installs dependencies, starts app)
./setup.sh
```

### Manual Setup
```bash
# Install dependencies
pip install -r streamlit_app/requirements.txt

# Download data files
python3 scripts/download_data.py

# Start application
./manage.sh start
```

## 📋 Features

### Core Functionality
- **Comprehensive Database**: Access to 19,850+ curated synthetic biology parts from authoritative sources (Addgene, iGEM Registry, laboratory collections)
- **Advanced Search Capabilities**: Multi-modal search including text-based filtering and AI-powered semantic similarity matching
- **Interactive Data Visualization**: Real-time statistics and distribution analysis across biological part categories
- **Hierarchical Classification System**: Three-level taxonomy (DNA Elements, RNA Elements, Coding Sequences, Application Constructs) with detailed subcategorization
- **Quality Assurance**: Integration of verification status and literature-based validation for 7,656+ parts

### Technical Features
- **Embedding-Based Retrieval**: Local implementation of semantic search using sentence transformers
- **Multi-Database Support**: DuckDB for performance, SQLite for compatibility
- **SBOL3 Export**: Standards-compliant data export in multiple formats
- **Performance Monitoring**: Built-in benchmarking and system health monitoring
- **Scalable Architecture**: Designed for both single-user and multi-user deployment scenarios

### Integration Capabilities
- **API Documentation**: Comprehensive information about SynVectorDB cloud services
- **MCP Server Integration**: Compatible with AI assistant frameworks
- **Data Export Options**: Multiple formats including CSV, JSON, and SBOL3
- **Cloud Service Links**: Direct access to production deployment at https://svdb.sjtu.bio

## 🛠 Technical Stack

- **Frontend**: Streamlit web framework
- **Database**: DuckDB (preferred) with SQLite fallback for maximum compatibility
- **AI Models**: Sentence Transformers for semantic search (optional)
- **Visualization**: Plotly for interactive charts
- **Search**: FAISS for vector similarity search (optional)
- **Data Processing**: Pandas for data manipulation

## 📁 Project Structure

```
synbio-parts-db/
├── streamlit_app/           # Main application code
│   ├── Home.py             # Homepage
│   ├── pages/              # Application pages
│   └── utils.py            # Utility functions
├── scripts/                # Setup and utility scripts
├── data/                   # Database files (auto-downloaded)
├── logs/                   # Application logs
├── streamlit_app/requirements.txt # Python dependencies
├── setup.sh               # Automated setup script
└── manage.sh              # Application management
```

## ⚠️ Important Notes

### System Requirements
- **Python**: 3.8 or higher
- **System Packages**: 
  - `python3-venv` (for virtual environment support)
  - `python3-dev` (for compiling native extensions)
  - `build-essential` (for building dependencies)
- **Memory**: 2GB+ RAM recommended for AI features
- **Storage**: 600MB+ free space (150MB data + 400MB AI models + workspace)
- **Network**: Stable internet connection required for initial setup and data download

### Platform Compatibility
- **Linux**: Fully supported (recommended)
- **macOS**: Supported with minor adjustments
- **Windows**: Supported via WSL2 or native Python installation

### Data Sources
- **Core Database Files**: Automatically downloaded from Cloudflare R2 storage
  - `parts.duckdb` (~50MB): Complete database with embeddings and AI classifications
  - `parts.db` (~45MB): SQLite version for compatibility
- **Optional Data Files**: Additional formats for advanced use cases
  - `parts.fasta` (~25MB): DNA sequences in FASTA format
  - `sbol_ndjson.jsonl` (~30MB): SBOL3-compliant data in JSON format
- **AI Models**: Downloaded on first use (may take 2-3 minutes)
- **Total Download Size**: ~150MB for all data + ~400MB for AI models

### Performance Considerations
- **First Startup**: May take 3-5 minutes due to AI model loading
- **Subsequent Startups**: ~10-20 seconds with cached models
- **Search Performance**: Vector search ~10ms, text search ~100ms
- **Concurrent Users**: Supports 5-10 simultaneous users

### Troubleshooting

#### Common Issues
1. **Port 8501 already in use**
   ```bash
   ./manage.sh stop  # Stop existing instance
   ./setup.sh        # Restart
   ```

2. **Missing dependencies**
   ```bash
   pip install -r streamlit_app/requirements.txt
   ```

3. **Database not found**
   ```bash
   python3 scripts/download_data.py  # Re-download data
   ```

4. **Database type inconsistency**
   ```bash
   python3 test_database_compatibility.py  # Test database setup
   ```
   - Application prefers DuckDB but falls back to SQLite
   - Both database files should be downloaded automatically
   - Check data directory for `parts.duckdb` and `parts.db`

5. **Cross-platform database issues** (Critical)
   ```bash
   # If you see "No files found that match the pattern" errors:
   python3 scripts/download_data.py  # Re-run download script
   # Script will automatically detect and handle incompatible DuckDB files
   ```
   - **Root Cause**: DuckDB file contains hardcoded Windows/WSL absolute paths (e.g., `/mnt/d/...`)
   - **Auto-Detection**: Download script automatically tests DuckDB compatibility
   - **Auto-Resolution**: Incompatible files are renamed to `.incompatible` extension
   - **Fallback**: Application seamlessly uses SQLite database (100% functional)
   - **User Impact**: No functionality loss, just different database backend

6. **System dependencies missing**
   ```bash
   # Ubuntu/Debian:
   sudo apt-get update
   sudo apt-get install python3-venv python3-dev build-essential
   
   # CentOS/RHEL:
   sudo yum install python3-devel gcc gcc-c++
   ```

7. **AI models not loading**
   - Ensure stable internet connection
   - Check available disk space (500MB+ required)
   - Models are cached in `streamlit_app/models/`

#### Memory Issues
- If system has <4GB RAM, disable AI features by using `requirements.txt` instead of `requirements_enhanced.txt`
- Monitor memory usage: `./manage.sh status`

#### Network Issues
- Data download requires stable internet connection
- Corporate firewalls may block model downloads
- Use `./setup.sh download` to test data download separately

### Development

#### Running in Development Mode
```bash
# Enable debug logging
export STREAMLIT_LOGGER_LEVEL=debug

# Start with auto-reload
streamlit run streamlit_app/Home.py --server.runOnSave true
```

#### Adding New Features
1. Create new page in `streamlit_app/pages/`
2. Add utility functions to `streamlit_app/utils.py`
3. Update navigation in `Home.py`
4. Test with `./manage.sh test`

### Deployment

#### Local Production
```bash
# Start as background service
./manage.sh start

# Check status
./manage.sh status

# View logs
./manage.sh logs
```

#### Docker Deployment
```bash
# Build image
docker build -t synvectordb-githubshare .

# Run container
docker run -p 8501:8501 synvectordb-githubshare
```

### Security Notes
- Application runs on localhost by default
- No authentication required for local use
- Database files are read-only
- No user data is collected or stored

### License and Citation
- Open source under MIT License
- If used in research, please cite the SynVectorDB paper
- Data sourced from iGEM Registry and other public repositories

## 🆘 Support

- **Issues**: Report bugs on GitHub Issues
- **Documentation**: See `/docs` folder for detailed guides
- **Community**: Join discussions in GitHub Discussions

## 🌐 SynVectorDB Ecosystem

This local deployment is part of a comprehensive ecosystem of SynVectorDB deployments:

### Production Services
- **Web Interface**: [https://svdb.sjtu.bio](https://svdb.sjtu.bio) - Full-featured production deployment
- **API Services**: [https://testsdb.sjtu.bio](https://testsdb.sjtu.bio) - RESTful API for programmatic access
- **MCP Server**: [NPM Package](https://www.npmjs.com/package/synvectordb) - AI assistant integration

### Local Deployments
- **Local Version** (this repository): Simplified local deployment for education and research
- **Full Local**: Complete feature parity with cloud services for institutional deployment
- **Docker Containers**: Containerized deployment for scalable infrastructure

## 👥 Research Team

**Principal Investigator**: Dr. Wei Zhou  
**Institution**: Department of Endodontics, Shanghai Ninth People's Hospital, Shanghai Jiao Tong University School of Medicine  
**Contact**: zhouweicd@shsmu.edu.cn

**Collaborating Institutions**:
- Shanghai Jiao Tong University School of Medicine
- Beijing Xunzhu Biotechnology Co., Ltd.
- The University of Queensland

## 📚 About This Project

SynVectorDB is developed as part of ongoing research in synthetic biology informatics and AI-driven biological data retrieval. The system demonstrates novel approaches to biological part organization and semantic search technologies.

For academic inquiries or collaboration opportunities, please contact the research team.

## 🔄 Updates

The application auto-checks for updates on startup. To manually update:
```bash
git pull origin main
./setup.sh
```

## 🤝 Contributing

We welcome contributions from the synthetic biology and bioinformatics communities. Please see our contributing guidelines and feel free to:

- Report issues and bugs
- Suggest new features
- Contribute code improvements
- Share feedback on usability and performance

## 🆘 Support

- **Technical Issues**: Report bugs on [GitHub Issues](https://github.com/AilurusBio/synbio-parts-db/issues)
- **Research Inquiries**: Contact corresponding authors directly
- **Collaboration Opportunities**: Reach out through institutional channels
- **Documentation**: Comprehensive guides available in the `/docs` folder
