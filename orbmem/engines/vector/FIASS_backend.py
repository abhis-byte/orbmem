# orbmem/engines/vector/FIASS_backend.py

import os

FAISS_ENABLED = os.getenv("ENABLE_FAISS", "0") == "1"

if FAISS_ENABLED:
    try:
        import faiss
    except ImportError:
        raise ImportError(
            "FAISS is enabled but not installed. "
            "Install with: pip install faiss-cpu"
        )
else:
    faiss = None


class QdrantVectorBackend:
    def __init__(self, *args, **kwargs):
        if not FAISS_ENABLED:
            raise RuntimeError(
                "FAISS backend is disabled in this environment"
            )