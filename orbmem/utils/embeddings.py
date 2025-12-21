# utils/embeddings.py

from functools import lru_cache
from sentence_transformers import SentenceTransformer
import numpy as np
from orbmem.utils.logger import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Loads the embedding model once.
    MiniLM-L6 model → 384-dimensional vectors.
    """
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    logger.info(f"Loading embedding model: {model_name}")
    return SentenceTransformer(model_name)


def embed_text(text: str):
    """
    Convert text into a 384-d embedding vector.
    Returns a Python list of floats (JSON serializable).
    """
    if not text or not isinstance(text, str):
        return [0.0] * 384

    model = get_embedding_model()
    vector = model.encode(text)

    # Convert NumPy array → list so Qdrant can store it
    return vector.astype(float).tolist()
