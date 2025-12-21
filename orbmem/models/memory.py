# NOTE: Experimental – used only in OCDB Cloud mode (v2)


# models/memory.py

from sqlalchemy import Column, Integer, String, JSON, TIMESTAMP
from sqlalchemy.sql import func
# In v1 local mode, memory is pure SQLite, not SQLAlchemy Postgres.
Base = object


class MemoryRecord(Base):
    __tablename__ = "memory_records"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    session_id = Column(String, index=True, nullable=True)
    value = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True)