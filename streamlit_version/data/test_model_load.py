import logging
import time
from pathlib import Path
from sentence_transformers import SentenceTransformer
# import torch # Not strictly needed for this test if device='cpu' is passed and works.

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("--- Test SentenceTransformer Model Load (App-Style) START ---")
    start_time = time.time()

    current_file_dir = Path(__file__).resolve().parent
    cache_dir = current_file_dir / "models"
    model_name = 'all-MiniLM-L6-v2'

    logger.info(f"Script location: {Path(__file__).resolve()}")
    logger.info(f"Using cache_folder: {cache_dir.resolve()}")
    logger.info(f"Attempting to load model: '{model_name}' with local_files_only=True, device='cpu'")

    # Check for the expected model directory structure
    expected_model_sub_dir = cache_dir / f"models--sentence-transformers--{model_name}"
    if not expected_model_sub_dir.exists() or not expected_model_sub_dir.is_dir():
        # CORRECTED: Combine into a single multi-line f-string
        log_message = (
            f"Expected model directory {expected_model_sub_dir.resolve()} not found or not a directory. "
            f"SentenceTransformer might fail or attempt to download if local_files_only were False.\n"
            f"Contents of cache_dir ({cache_dir.resolve()}):"
        )
        logger.warning(log_message)
        try:
            for item in cache_dir.iterdir():
                logger.warning(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")
        except FileNotFoundError:
            logger.warning(f"  Cache directory {cache_dir.resolve()} itself not found.")

    try:
        model = SentenceTransformer(
            model_name_or_path=model_name,      # Use the short model name
            cache_folder=str(cache_dir),        # Specify the cache directory
            local_files_only=True,              # Crucial for using local files
            device='cpu'                        # Explicitly use CPU
        )
        logger.info("SentenceTransformer model loaded SUCCESSFULLY.")
        logger.info(f"Model type: {type(model)}")
        
        # Optional: Test encoding a sample sentence
        logger.info("Testing model with a sample sentence...")
        sample_embedding = model.encode("This is a test sentence.")
        logger.info(f"Sample embedding type: {type(sample_embedding)}, shape: {sample_embedding.shape if hasattr(sample_embedding, 'shape') else 'N/A'}")
        logger.info("Model test encoding SUCCEEDED.")

    except Exception as e:
        logger.error("Failed to load SentenceTransformer model.", exc_info=True)
        
    end_time = time.time()
    logger.info(f"--- Test SentenceTransformer Model Load (App-Style) FINISHED in {end_time - start_time:.2f} seconds ---")

if __name__ == "__main__":
    main()
