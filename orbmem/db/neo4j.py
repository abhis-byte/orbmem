# db/neo4j.py

from neo4j import GraphDatabase
from orbmem.utils.logger import get_logger
from orbmem.utils.exceptions import DatabaseError
from orbmem.core.config import load_config

logger = get_logger(__name__)

_driver = None


def get_neo4j_driver():
    global _driver

    if _driver:
        return _driver

    cfg = load_config()
    url = cfg.db.neo4j_url
    user = cfg.db.neo4j_user
    password = cfg.db.neo4j_password

    try:
        _driver = GraphDatabase.driver(url, auth=(user, password))
        logger.info("Neo4j driver initialized.")
        return _driver

    except Exception as e:
        logger.error(f"Neo4j initialization failed: {e}")
        raise DatabaseError(f"Neo4j init error: {e}")
