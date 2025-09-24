# SynVectorDB githubshare

A local Streamlit application for demonstrating SynVectorDB functionality and data visualization.

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

- **Database Statistics**: Interactive visualizations of 19,850+ synthetic biology parts
- **Parts Browser**: Search and filter biological parts by type, source, and organism
- **Semantic Search**: AI-powered similarity search using sentence transformers
- **API Integration**: Information about SynVectorDB cloud API endpoints
- **Data Export**: Download search results and statistics

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

## 🔄 Updates

The application auto-checks for updates on startup. To manually update:
```bash
git pull origin main
./setup.sh
```
