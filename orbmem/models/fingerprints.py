# models/fingerprints.py

from sqlalchemy import Column, Integer, String, Float, TIMESTAMP
from sqlalchemy.sql import func
# orbmem/models/fingerprints.py

# NOTE:
# In OCDB v1 (local mode), safety fingerprints are stored in SQLite 
# through TimeSeriesSafetyBackend. SQLAlchemy-based Postgres models 
# are only used in OCDB Cloud v2. 
#
# Therefore, Postgres Base import is disabled.

Base = object  # placeholder for future cloud version

# (If you had any dataclasses or models here, keep them. They won’t break.)


class SafetyFingerprint(Base):
    __tablename__ = "safety_fingerprints"

    id = Column(Integer, primary_key=True)
    tag = Column(String, index=True, nullable=False)
    score = Column(Float, nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now())
