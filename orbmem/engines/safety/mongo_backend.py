# engines/safety/mongo_backend.py

import re
import time
from typing import List, Dict, Any, Optional

from orbmem.db.mongo import get_mongo_client
from orbmem.utils.logger import get_logger

logger = get_logger(__name__)


class SafetyEvent:
    """
    Represents a detected safety violation.
    """

    def __init__(
        self,
        text: str,
        tag: str,
        severity: float,
        correction: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.text = text
        self.tag = tag
        self.severity = severity
        self.correction = correction or None
        self.details = metadata or {}
        self.timestamp = time.time()

    def to_dict(self):
        return {
            "text": self.text,
            "tag": self.tag,
            "severity": self.severity,
            "correction": self.correction,
            "details": self.details,
            "timestamp": self.timestamp,
        }


class MongoSafetyBackend:
    """
    Scans text for unsafe content and logs events to MongoDB.
    """

    DEFAULT_PATTERNS = {
        "self_harm": re.compile(r"(suicide|kill myself|hurt myself)", re.IGNORECASE),
        "violence": re.compile(r"(kill|shoot|stab|attack)", re.IGNORECASE),
        "hate": re.compile(r"(racial slur|hate\s+speech|bigot)", re.IGNORECASE),
        "privacy": re.compile(r"(password|otp|aadhaar|credit card)", re.IGNORECASE),
    }

    def __init__(self):
        self.client = get_mongo_client()
        if self.client:
            self.collection = self.client["ocdb"]["safety_events"]
            logger.info("MongoSafetyBackend initialized.")
        else:
            self.collection = None
            logger.warning("MongoSafetyBackend disabled (no MongoDB).")

    # ---------------------------------------------------------
    # Scoring model
    # ---------------------------------------------------------
    def _severity(self, tag: str, text: str) -> float:
        base = {
            "self_harm": 0.9,
            "violence": 0.7,
            "hate": 0.8,
            "privacy": 0.6,
        }.get(tag, 0.5)

        length_factor = min(len(text) / 200, 1.0)
        return round(base * length_factor, 3)

    # ---------------------------------------------------------
    # Main scan function
    # ---------------------------------------------------------
    def scan(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[SafetyEvent]:
        if not text:
            return []

        events = []

        for tag, pattern in self.DEFAULT_PATTERNS.items():
            if pattern.search(text):
                severity = self._severity(tag, text)
                evt = SafetyEvent(text, tag, severity, metadata=metadata)
                events.append(evt)

                if self.collection:
                    self.collection.insert_one(evt.to_dict())

        return events
