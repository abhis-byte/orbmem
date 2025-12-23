# orbmem/engines/vector/FAISS_backend.py

import numpy as np

try:
    import faiss
except ImportError as e:
    raise ImportError(
        "FAISS is required for vector search.\n"
        "Install it using: pip install faiss-cpu"
    ) from e


class QdrantVectorBackend:
    """
    FAISS-based in-memory vector store.
    Per-process, shared across users (payload filters isolate users).
    """

    def __init__(self, dim: int = 384):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)

        # Store metadata separately
        self._payloads = []

    # --------------------------------------------------
    # INTERNAL
    # --------------------------------------------------

    def _embed(self, text: str) -> np.ndarray:
        """
        VERY simple deterministic embedding.
        (You can replace later with real models.)
        """
        rng = np.random.default_rng(abs(hash(text)) % (2**32))
        vec = rng.random(self.dim, dtype=np.float32)
        return vec

    # --------------------------------------------------
    # PUBLIC API (required by BaseEngine)
    # --------------------------------------------------

    def add_text(self, text: str, payload: dict):
        vector = self._embed(text)
        vector = np.expand_dims(vector, axis=0)

        self.index.add(vector)
        self._payloads.append(payload)

    def search(self, query: str, k: int = 5):
        if self.index.ntotal == 0:
            return []

        query_vec = self._embed(query)
        query_vec = np.expand_dims(query_vec, axis=0)

        distances, indices = self.index.search(query_vec, k)

        results = []
        for idx in indices[0]:
            if idx == -1:
                continue
            results.append({
                "payload": self._payloads[idx],
            })

        return results