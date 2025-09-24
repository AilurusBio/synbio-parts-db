# SynVectorDB githubshare

**Local Deployment Version of SynVectorDB: Embedding-Based Retrieval System for Synthetic Biology Parts**

This repository contains the **githubshare** version - a standalone, local deployment of SynVectorDB designed for educational, research, and demonstration purposes. SynVectorDB is a comprehensive embedding-based retrieval system that addresses critical challenges in synthetic biology part discovery through AI-driven semantic search and systematic data curation.

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
cd synbio-parts-db/githubshare

# Run automated setup (downloads data, installs dependencies, starts app)
./setup.sh
```

### Manual Setup
```bash
# Install dependencies
pip install -r requirements_enhanced.txt

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
- **Database**: DuckDB (primary) + SQLite (fallback)
- **AI Models**: Sentence Transformers for semantic search
- **Visualization**: Plotly for interactive charts
- **Search**: FAISS for vector similarity search

## 📁 Project Structure

```
githubshare/
├── streamlit_app/           # Main application code
│   ├── Home.py             # Homepage
│   ├── pages/              # Application pages
│   └── utils.py            # Utility functions
├── scripts/                # Setup and utility scripts
├── data/                   # Database files (auto-downloaded)
├── logs/                   # Application logs
├── requirements.txt        # Python dependencies
├── setup.sh               # Automated setup script
└── manage.sh              # Application management
```

## ⚠️ Important Notes

### System Requirements
- **Python**: 3.8 or higher
- **Memory**: 2GB+ RAM recommended for AI features
- **Storage**: 200MB+ free space for data and models
- **Network**: Internet connection required for initial setup

### Data Sources
- Database files are automatically downloaded from Cloudflare R2 storage
- AI models are downloaded on first use (may take 2-3 minutes)
- Total download size: ~100MB for data + ~400MB for AI models

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
   pip install -r requirements_enhanced.txt
   ```

3. **Database not found**
   ```bash
   python3 scripts/download_data.py  # Re-download data
   ```

4. **AI models not loading**
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

This githubshare version is part of a comprehensive ecosystem of SynVectorDB deployments:

### Production Services
- **Web Interface**: [https://svdb.sjtu.bio](https://svdb.sjtu.bio) - Full-featured production deployment
- **API Services**: [https://testsdb.sjtu.bio](https://testsdb.sjtu.bio) - RESTful API for programmatic access
- **MCP Server**: [NPM Package](https://www.npmjs.com/package/synvectordb) - AI assistant integration

### Local Deployments
- **githubshare** (this repository): Simplified local deployment for education and research
- **Full Local**: Complete feature parity with cloud services for institutional deployment
- **Docker Containers**: Containerized deployment for scalable infrastructure

## 👥 Research Team

### Principal Investigators
- **Dr. Wei Zhou** (Corresponding Author)
  - Department of Endodontics, Shanghai Ninth People's Hospital
  - Shanghai Jiao Tong University School of Medicine
  - Email: zhouweicd@shsmu.edu.cn

- **Dr. Jie Song** (Corresponding Author)
  - Research and Development Department, Beijing Xunzhu Biotechnology Co. Ltd.
  - School of Chemistry and Molecular Biosciences, The University of Queensland
  - Email: jiesong@whu.edu.cn

### Contributing Authors
- **Hao Li** (Co-first Author)
  - Shanghai Jiao Tong University School of Medicine
  - National Center for Stomatology

- **Jiani Hu** (Co-first Author)
  - Beijing Xunzhu Biotechnology Co. Ltd.
  - The University of Queensland

### Institutional Affiliations
- Shanghai Jiao Tong University School of Medicine, College of Stomatology
- National Center for Stomatology, National Clinical Research Center for Oral Diseases
- Shanghai Key Laboratory of Stomatology
- Beijing Xunzhu Biotechnology Co. Ltd.
- School of Chemistry and Molecular Biosciences, The University of Queensland

## 📚 Citation

If you use SynVectorDB in your research, please cite our work:

```bibtex
@article{synvectordb2024,
  title={SynVectorDB: Embedding-Based Retrieval System for Synthetic Biology Parts},
  author={Li, Hao and Hu, Jiani and Song, Jie and Zhou, Wei},
  journal={Bioinformatics},
  year={2024},
  note={Co-first authors: Hao Li, Jiani Hu; Corresponding authors: Jie Song, Wei Zhou},
  url={https://github.com/AilurusBio/synbio-parts-db}
}
```

## 📄 License

This project is licensed under the MIT License, promoting open science and reproducible research in synthetic biology informatics.

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
