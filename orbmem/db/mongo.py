# db/mongo.py

from pymongo import MongoClient
from orbmem.core.config import load_config
from orbmem.utils.logger import get_logger
from orbmem.utils.exceptions import DatabaseError

logger = get_logger(__name__)

CONFIG = load_config()
MONGO_URL = CONFIG.db.mongo_url


def get_mongo_client():
    """Get MongoDB client for safety engine."""
    if not MONGO_URL:
        return None

    try:
        client = MongoClient(MONGO_URL)
        logger.info("MongoDB connection established.")
        return client
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise DatabaseError(f"MongoDB init error: {e}")
