# SynBio Parts Database

A comprehensive synthetic biology parts database with semantic search capabilities and RESTful API.

## Features

- 🔍 Semantic Search: Natural language-based intelligent search
- 📊 Data Visualization: Interactive database statistics
- 🔌 RESTful API: Standardized data access interface
- 🧬 Part Classification: Multi-level classification system
- 🔄 Real-time Updates: Dynamic data management

## Quick Start

### Prerequisites

- Python 3.8+
- MongoDB
- Streamlit

### Installation

```bash
# Clone repository
git clone https://github.com/AilurusBio/synbio-parts-db.git
cd synbio-parts-db

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration
```

### Running the Application

```bash
# Start Web Interface
streamlit run streamlit_version/Home.py

# Start API Server
python streamlit_version/pages/mcp_server.py
```

## API Documentation

Access API documentation at: `http://localhost:8000/docs`

Key Endpoints:
- `GET /tools` - List available tools
- `POST /tools/semantic_search` - Perform semantic search
- `GET /parts/{part_id}` - Get part details
- `POST /parts/search` - Search parts with multiple parameters
- `GET /stats` - Get database statistics

## Project Structure

```
synbio-parts-db/
├── streamlit_version/     # Web application
├── papermd/              # Documentation and papers
├── examples/             # Example code
└── requirements.txt      # Project dependencies
```

## Database Schema

Main collections:
- `parts`: Stores all biological parts
- `database_stats`: Stores database statistics

### Part Fields
```json
{
    "part_id": "PART_TEMP00101",
    "label": "4-1BB",
    "type_info": {
        "main_type": "t_cell_signaling_domain",
        "sub_types": ["Costimulatory domain"]
    },
    "sequence_info": {
        "sequence": "AAACGGGGCAGAAAGAAACTCCTGTATATATTCAAACAACCATTTATGAGACCAGTACAAACTACTCAAGAGGAAGATGGCTGTAGCTGCCGATTTCCAGAAGAAGAAGAAGGAGGATGTGAACTG",
        "length": 123,
        "gc_content": 0.4634146341463415
    },
    "notes": ["4-1BB intracellular costimulatory domain"],
    "application_notes": [
        "Costimulatory domain",
        "Improves overall survival, proliferation and persistence of activated CAR-T cells"
    ],
    "references": [
        {
            "type": "pubmed",
            "id": "14961035",
            "url": "https://pubmed.ncbi.nlm.nih.gov/14961035/"
        }
    ],
    "source": {
        "database": "SynBio Parts DB",
        "version": "V1.2",
        "collection": "synbio_parts",
        "last_updated": "2025-02-18T00:10:00+08:00"
    },
    "creation_date": "2025-02-18T00:10:00+08:00",
    "last_modified": "2025-02-18T00:10:00+08:00"
}
```

## Contributing

We welcome contributions! Please feel free to submit issues and pull requests.

## License

MIT License

## Contact

- Organization: AilurusBio
- Email: contact@ailurus.bio
