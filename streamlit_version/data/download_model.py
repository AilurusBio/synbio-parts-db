from pathlib import Path
from sentence_transformers import SentenceTransformer
import argparse

def download_model():
    """下载并缓存模型"""
    # 设置路径
    data_dir = Path(__file__).parent
    cache_dir = data_dir / "models"
    cache_dir.mkdir(exist_ok=True)
    
    print("正在下载模型...")
    try:
        model = SentenceTransformer(
            'all-MiniLM-L6-v2',
            cache_folder=str(cache_dir)
        )
        print("模型下载完成！")
        return True
    except Exception as e:
        print(f"模型下载失败: {e}")
        print("请确保网络连接正常")
        return False

def main():
    parser = argparse.ArgumentParser(description='下载语义搜索模型')
    parser.add_argument('--force', action='store_true', help='强制重新下载')
    
    args = parser.parse_args()
    
    # 检查模型是否已存在
    data_dir = Path(__file__).parent
    cache_dir = data_dir / "models"
    model_dir = cache_dir / "models--sentence-transformers--all-MiniLM-L6-v2"
    
    if model_dir.exists() and not args.force:
        print("模型已存在，跳过下载")
        print(f"模型位置: {model_dir}")
        return
    
    if args.force:
        print("强制重新下载模型...")
        import shutil
        shutil.rmtree(model_dir, ignore_errors=True)
    
    download_model()

if __name__ == "__main__":
    main() 