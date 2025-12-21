# engines/vector/qdrant_backend.py
# FAISS-based in-memory vector engine (Qdrant-like behavior)

try:
    import faiss
except ImportError:
    raise ImportError("FAISS is not installed. Install with: pip install faiss-cpu")

import numpy as np
from typing import List, Dict, Any, Optional

from orbmem.utils.logger import get_logger
from orbmem.utils.embeddings import embed_text
from orbmem.utils.exceptions import DatabaseError

logger = get_logger(__name__)


class QdrantVectorBackend:
    """
    Lightweight FAISS-based vector engine.

    Features:
    - Enforced embedding dimension
    - Safe add & search
    - Payload tracking
    - User-level filtering support
    """

    def __init__(self, dim: int = 384, max_k: int = 50):
        self.dim = dim
        self.max_k = max_k

        # FAISS index (L2 similarity)
        self.index = faiss.IndexFlatL2(dim)

        # Internal storage
        self._payloads: List[Dict[str, Any]] = []

        logger.info(f"FAISS vector engine initialized (dim={dim}).")

    # ---------------------------------------------------------
    # INTERNAL: embed + validate
    # ---------------------------------------------------------
    def _embed(self, text: str) -> np.ndarray:
        if not text or not isinstance(text, str):
            raise DatabaseError("Text must be a non-empty string")

        vector = embed_text(text)

        if not isinstance(vector, (list, tuple)):
            raise DatabaseError("Embedding must be a list or tuple")

        if len(vector) != self.dim:
            raise DatabaseError(
                f"Invalid embedding dimension: expected {self.dim}, got {len(vector)}"
            )

        return np.array([vector], dtype="float32")

    # ---------------------------------------------------------
    # ADD VECTOR
    # ---------------------------------------------------------
    def add_text(self, text: str, payload: Dict[str, Any]):
        """
        Add a text embedding with payload.

        Payload MUST include:
            - user_id
        """
        try:
            if "user_id" not in payload:
                raise DatabaseError("Payload must include user_id")

            vector = self._embed(text)

            # Add to FAISS
            self.index.add(vector)

            # Keep payload index-aligned
            self._payloads.append(payload)

            logger.info(
                f"Vector added | total={self.index.ntotal} | user={payload['user_id']}"
            )

        except Exception as e:
            logger.error(f"FAISS add_text error: {e}")
            raise DatabaseError(str(e))

    # ---------------------------------------------------------
    # SEARCH
    # ---------------------------------------------------------
    def search(
        self,
        query: str,
        k: int = 5,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search vectors.

        - k is capped for safety
        - Optional user_id filtering
        """
        try:
            if self.index.ntotal == 0:
                return []

            if k <= 0:
                return []

            k = min(k, self.max_k)

            vector = self._embed(query)

            distances, indices = self.index.search(vector, k)

            results: List[Dict[str, Any]] = []

            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0 or idx >= len(self._payloads):
                    continue

                payload = self._payloads[idx]

                # Optional tenant filter
                if user_id and payload.get("user_id") != user_id:
                    continue

                results.append({
                    "score": float(dist),
                    "payload": payload,
                })

            return results

        except Exception as e:
            logger.error(f"FAISS search error: {e}")
            raise DatabaseError(str(e))