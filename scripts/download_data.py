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
        "url": "https://r2data.sjtu.bio/parts.duckdb",
        "size": "~50MB",
        "description": "Main DuckDB database with 19,850 synthetic biology parts"
    },
    "parts.db": {
        "url": "https://r2data.sjtu.bio/parts.db", 
        "size": "~45MB",
        "description": "SQLite fallback database"
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

def main():
    """Main download function"""
    print("SynVectorDB githubshare - Data Download Script")
    print("=" * 50)
    
    # Create data directory
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    print(f"📁 Data directory: {data_dir}")
    
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
    
    print("\n" + "=" * 50)
    print(f"📊 Download Summary: {success_count}/{total_count} files successful")
    
    if success_count == total_count:
        print("🎉 All data files downloaded successfully!")
        return True
    else:
        print("⚠️  Some downloads failed. The application may not work properly.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
