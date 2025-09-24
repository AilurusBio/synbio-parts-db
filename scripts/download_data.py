#!/usr/bin/env python3
"""
Data Download Script for SynVectorDB githubshare
Download required data files from Cloudflare R2 storage
"""

import os
import sys
import requests
import hashlib
from pathlib import Path
from urllib.parse import urljoin

# Data sources configuration
DATA_SOURCES = {
    "parts.duckdb": {
        "url": "https://r2data.sjtu.bio/data/parts.duckdb",
        "size": "~50MB",
        "description": "Complete database with parts data, embeddings, and AI classifications integrated"
    },
    "parts.db": {
        "url": "https://r2data.sjtu.bio/data/parts.db", 
        "size": "~45MB",
        "description": "SQLite version with parts data and AI classifications"
    }
}

# Optional data sources for advanced features
OPTIONAL_DATA_SOURCES = {
    "parts.fasta": {
        "url": "https://r2data.sjtu.bio/exports/parts.fasta",
        "size": "~25MB",
        "description": "DNA sequences in FASTA format for all parts"
    },
    "sbol_ndjson.jsonl": {
        "url": "https://r2data.sjtu.bio/exports/sbol_ndjson.jsonl",
        "size": "~30MB", 
        "description": "SBOL3-compliant data in newline-delimited JSON format"
    }
}

def download_file(url: str, filepath: Path, description: str = "") -> bool:
    """Download a file with progress indication"""
    try:
        print(f"📥 Downloading {filepath.name}...")
        if description:
            print(f"   📄 {description}")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\r   📊 Progress: {progress:.1f}%", end='', flush=True)
        
        print(f"\n✅ Downloaded {filepath.name} ({downloaded / 1024 / 1024:.1f}MB)")
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to download {filepath.name}: {e}")
        return False

def verify_file(filepath: Path) -> bool:
    """Basic file verification"""
    if not filepath.exists():
        return False
    
    size = filepath.stat().st_size
    if size < 1024:  # Less than 1KB is suspicious
        print(f"⚠️  Warning: {filepath.name} is very small ({size} bytes)")
        return False
    
    print(f"✅ Verified {filepath.name} ({size / 1024 / 1024:.1f}MB)")
    return True

def download_optional_data(data_dir: Path) -> int:
    """Download optional data files for advanced features"""
    print("\n📦 Downloading optional data files...")
    success_count = 0
    
    # Create exports directory for optional files
    exports_dir = data_dir / "exports"
    exports_dir.mkdir(exist_ok=True)
    
    for filename, config in OPTIONAL_DATA_SOURCES.items():
        if filename.endswith('.fasta'):
            filepath = exports_dir / filename
        elif filename.endswith('.jsonl'):
            filepath = exports_dir / filename
        else:
            filepath = data_dir / filename
        
        # Skip if file already exists and is valid
        if filepath.exists() and verify_file(filepath):
            print(f"⏭️  Skipping {filename} (already exists)")
            success_count += 1
            continue
        
        # Download the file
        if download_file(config["url"], filepath, config["description"]):
            if verify_file(filepath):
                success_count += 1
            else:
                print(f"❌ Verification failed for {filename}")
        else:
            print(f"❌ Download failed for {filename}")
    
    return success_count

def main():
    """Main download function"""
    print("SynVectorDB Local Deployment - Data Download Script")
    print("=" * 60)
    
    # Create data directory
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    print(f"📁 Data directory: {data_dir}")
    
    # Download core database files
    print("\n🗄️  Downloading core database files...")
    success_count = 0
    total_count = len(DATA_SOURCES)
    
    for filename, config in DATA_SOURCES.items():
        filepath = data_dir / filename
        
        # Skip if file already exists and is valid
        if filepath.exists() and verify_file(filepath):
            print(f"⏭️  Skipping {filename} (already exists)")
            success_count += 1
            continue
        
        # Download the file
        if download_file(config["url"], filepath, config["description"]):
            if verify_file(filepath):
                success_count += 1
            else:
                print(f"❌ Verification failed for {filename}")
        else:
            print(f"❌ Download failed for {filename}")
    
    # Download optional files
    optional_success = download_optional_data(data_dir)
    
    print("\n" + "=" * 60)
    print(f"📊 Core Database Files: {success_count}/{total_count} successful")
    print(f"📦 Optional Data Files: {optional_success}/{len(OPTIONAL_DATA_SOURCES)} successful")
    
    if success_count == total_count:
        print("🎉 All core data files downloaded successfully!")
        if optional_success > 0:
            print(f"✨ {optional_success} optional files also downloaded for enhanced features!")
        return True
    elif success_count > 0:
        print("⚠️  Some core downloads failed, but application can run with available data.")
        return True
    else:
        print("❌ No core data files available. Application may not work properly.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
