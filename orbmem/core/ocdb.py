# core/ocdb.py

from typing import Optional, List
import os

from orbmem.core.config import load_config

# MEMORY ENGINE
from orbmem.engines.memory.postgres_backend import PostgresMemoryBackend

# VECTOR ENGINE (FAISS-based)
from orbmem.engines.vector.FAISS_backend import QdrantVectorBackend

# GRAPH ENGINE
from orbmem.engines.graph.neo4j_backend import Neo4jGraphBackend

# SAFETY ENGINE (auto)
if os.getenv("MONGO_URL"):
    from orbmem.engines.safety.mongo_backend import MongoSafetyBackend as SafetyBackend
else:
    from orbmem.engines.safety.sqlite_safety_backend import SQLiteSafetyBackend as SafetyBackend

from orbmem.engines.safety.timeseries_backend import TimeSeriesSafetyBackend


class OCDB:
    """
    OCDB – Per-user cognitive database.

    Each instance is fully isolated by uid.
    """

    def __init__(self, uid: str):
        self.uid = uid
        self.cfg = load_config()

        # -------------------------------
        # MEMORY
        # -------------------------------
        self.memory = PostgresMemoryBackend()

        # -------------------------------
        # VECTOR
        # -------------------------------
        self.vector_engine = QdrantVectorBackend()

        # -------------------------------
        # GRAPH
        # -------------------------------
        self.graph = Neo4jGraphBackend()

        # -------------------------------
        # SAFETY
        # -------------------------------
        self.safety_event_engine = SafetyBackend()
        self.safety_timeseries = TimeSeriesSafetyBackend()

    # =====================================================
    # INTERNAL NAMESPACE
    # =====================================================

    def _ns(self, key: str) -> str:
        return f"{self.uid}:{key}"

    # =====================================================
    # MEMORY
    # =====================================================

    def memory_set(
      self,
      key: str,
      value: dict,
      session_id: Optional[str] = None,
      ttl_seconds: Optional[int] = None,
    ):
      return self.memory.set(
        key,
        value,
        user_id=self.uid,
        session_id=session_id,
        ttl_seconds=ttl_seconds,
     )

    def memory_get(self, key: str):
     return self.memory.get(
       key,
       user_id=self.uid,
     )

    def memory_keys(self) -> List[str]:
     return self.memory.keys(
       user_id=self.uid,
     )

    # =====================================================
    # VECTOR
    # =====================================================

    def vector_add(self, text: str, payload: dict):
        payload = dict(payload)
        payload["user_id"] = self.uid
        self.vector_engine.add_text(text, payload)

    def vector_search(self, query: str, k: int = 5):
        results = self.vector_engine.search(query, k=k)
        return [
            r for r in results
            if r.get("payload", {}).get("user_id") == self.uid
        ]

    # =====================================================
    # GRAPH
    # =====================================================

    def graph_add(self, node_id: str, content: str, parent: Optional[str] = None):
        return self.graph.add_node(
            self._ns(node_id),
            content,
            self._ns(parent) if parent else None,
        )

    def graph_path(self, start: str, end: str):
        return self.graph.get_path(
            self._ns(start),
            self._ns(end),
        )

    def graph_dump(self):
        return self.graph.export()

    # =====================================================
    # SAFETY
    # =====================================================
    def safety_scan(self, text: str):
        try:
            # SQLite backend (no metadata support)
            events = self.safety_event_engine.scan(text)
        except TypeError:
            # Future backends (Mongo etc.)
            events = self.safety_event_engine.scan(
                text,
                metadata={"user_id": self.uid},
            )

        for evt in events:
            self.safety_timeseries.add_point(evt.tag, evt.severity)

        return [
            {
                "text": evt.text,
                "tag": evt.tag,
                "severity": evt.severity,
                "correction": evt.correction,
                "details": evt.details,
                "timestamp": evt.timestamp,
            }
            for evt in events
        ]