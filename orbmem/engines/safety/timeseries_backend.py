# engines/safety/timeseries_backend.py

import time
from typing import Dict, List

from orbmem.utils.logger import get_logger

logger = get_logger(__name__)


class TimeSeriesSafetyBackend:
    """
    Stores a simple in-memory safety fingerprint time series.
    In production, this could be replaced with TimescaleDB, InfluxDB, etc.
    """

    def __init__(self):
        self.store: Dict[str, List[Dict]] = {}
        logger.info("TimeSeriesSafetyBackend initialized.")

    def add_point(self, tag: str, severity: float):
        """
        Adds a timestamped event to the timeseries.
        """
        if tag not in self.store:
            self.store[tag] = []

        self.store[tag].append({
            "timestamp": time.time(),
            "score": severity
        })

        logger.info(f"Added safety point: tag={tag}, severity={severity}")

    def get_series(self, tag: str):
        return self.store.get(tag, [])
