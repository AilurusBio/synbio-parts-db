#!/usr/bin/env python3
"""
SynVectorDB - Prebuild Vector Index Script
Pre-compute vector embeddings and FAISS index for faster startup
"""

import sys
import time
from pathlib import Path

# Add streamlit_app to path
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir / "streamlit_app"))

def main():
    """Pre-build vector index for faster application startup"""
    
    print("🤖 SynVectorDB Vector Index Pre-builder")
    print("=" * 60)
    
    try:
        from utils_enhanced import (
            VECTOR_SUPPORT, FAISS_SUPPORT, 
            build_vector_index, get_all_parts_for_vectors
        )
        
        print(f"Vector Support: {VECTOR_SUPPORT}")
        print(f"FAISS Support: {FAISS_SUPPORT}")
        
        if not VECTOR_SUPPORT:
            print("❌ Vector support not available")
            print("   Please install: pip install sentence-transformers")
            return False
        
        if not FAISS_SUPPORT:
            print("❌ FAISS support not available") 
            print("   Please install: pip install faiss-cpu")
            return False
        
        # Check if index already exists
        cache_dir = current_dir / "streamlit_app" / "vector_cache"
        faiss_file = cache_dir / "vector_index.faiss"
        data_file = cache_dir / "vector_data.pkl"
        meta_file = cache_dir / "index_metadata.json"
        
        if all([faiss_file.exists(), data_file.exists(), meta_file.exists()]):
            print("✅ Vector index already exists")
            
            # Load metadata to show info
            import json
            with open(meta_file, "r") as f:
                metadata = json.load(f)
            
            print(f"   Parts count: {metadata['parts_count']:,}")
            print(f"   Created: {metadata['created_at']}")
            print(f"   Model: {metadata['model_name']}")
            
            response = input("\nRebuild index? (y/N): ").strip().lower()
            if response != 'y':
                print("Keeping existing index")
                return True
        
        print("\n🔄 Building vector index...")
        print("This may take 3-5 minutes for 19,850 parts...")
        
        start_time = time.time()
        
        # Build the index (this will also save it)
        index, df = build_vector_index()
        
        build_time = time.time() - start_time
        
        if index is not None and df is not None:
            print(f"\n✅ Vector index built successfully!")
            print(f"   📊 Indexed {len(df):,} parts")
            print(f"   ⏱️  Build time: {build_time:.1f} seconds")
            print(f"   💾 Saved to: {cache_dir}")
            
            # Show file sizes
            if faiss_file.exists():
                faiss_size = faiss_file.stat().st_size / 1024 / 1024
                print(f"   📁 FAISS index: {faiss_size:.1f} MB")
            
            if data_file.exists():
                data_size = data_file.stat().st_size / 1024 / 1024
                print(f"   📁 Data file: {data_size:.1f} MB")
            
            print(f"\n🚀 Next startup will be much faster!")
            return True
        else:
            print("❌ Failed to build vector index")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Please install required dependencies:")
        print("   pip install -r streamlit_app/requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
