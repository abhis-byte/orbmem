# NOTE: Experimental – used only in OCDB Cloud mode (v2)

# db/postgres.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from orbmem.core.config import load_config
from orbmem.utils.logger import get_logger
from orbmem.utils.exceptions import DatabaseError

logger = get_logger(__name__)

# Load configuration
CONFIG = load_config()
POSTGRES_URL = CONFIG.db.postgres_url

# Create SQLAlchemy engine
try:
    engine = create_engine(
        POSTGRES_URL,
        echo=False,
        pool_pre_ping=True,   # auto-detect dead connections
        pool_recycle=1800      # refresh stale connections
    )
    logger.info("PostgreSQL engine initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize PostgreSQL engine: {e}")
    raise DatabaseError(f"PostgreSQL init error: {e}")

# Create database session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all SQLAlchemy ORM models
Base = declarative_base()
