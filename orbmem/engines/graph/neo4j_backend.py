# engines/graph/neo4j_backend.py
# In-memory Graph Engine using NetworkX (Neo4j replacement)

import networkx as nx
from typing import Dict, Any, List
from orbmem.utils.logger import get_logger
from orbmem.utils.exceptions import DatabaseError

logger = get_logger(__name__)


class Neo4jGraphBackend:
    """
    Lightweight in-memory graph engine using NetworkX.
    Fully compatible with OCDB.graph_add() and OCDB.graph_path().
    """

    def __init__(self):
        try:
            self.graph = nx.DiGraph()
            logger.info("In-memory Graph Engine initialized (NetworkX).")
        except Exception as e:
            raise DatabaseError(f"Failed to initialize graph engine: {e}")

    # ---------------------------------------------------------
    # MATCHES ocdb.graph_add(node_id, content, parent)
    # ---------------------------------------------------------
    def add_node(self, node_id: str, content: str, parent: str = None):
        try:
            # Add node with content property
            self.graph.add_node(node_id, content=content)
            logger.info(f"Graph node added: {node_id}")

            # Add edge to parent if provided
            if parent:
                self.graph.add_edge(parent, node_id, relation="next")
                logger.info(f"Graph edge added: {parent} -> {node_id}")

            return {"node_id": node_id, "parent": parent}

        except Exception as e:
            raise DatabaseError(f"Failed adding node: {e}")

    # ---------------------------------------------------------
    # MATCHES ocdb.graph_path(start, end)
    # ---------------------------------------------------------
    def get_path(self, start: str, end: str) -> List[str]:
        try:
            return nx.shortest_path(self.graph, source=start, target=end)
        except Exception:
            return []

    # ---------------------------------------------------------
    # Debug export (optional)
    # ---------------------------------------------------------
    def export(self):
        return {
            "nodes": [
                {"id": n, "properties": self.graph.nodes[n]}
                for n in self.graph.nodes
            ],
            "edges": [
                {
                    "from": u,
                    "to": v,
                    "relation": self.graph.edges[u, v].get("relation", "next")
                }
                for u, v in self.graph.edges
            ]
        }
