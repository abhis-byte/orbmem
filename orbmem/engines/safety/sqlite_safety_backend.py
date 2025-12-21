# engines/safety/sqlite_safety_backend.py

import sqlite3
import json
from datetime import datetime, timedelta

from orbmem.utils.logger import get_logger
from orbmem.utils.exceptions import DatabaseError

logger = get_logger(__name__)

DB_PATH = "ocdb_safety.sqlite3"


class SQLiteSafetyBackend:
    """
    Safety Backend (SQLite)
    -----------------------
    Fully portable safety engine:
        - Logs violations
        - Stores severity, tags, corrections
        - TTL support
        - Compatible with MongoSafetyBackend interface

    Works everywhere: Kaggle, Colab, VSCode, Jupyter, Local Python.
    """

    def __init__(self):
        try:
            self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self._init_tables()
            logger.info("Safety: SQLite backend initialized.")
        except Exception as e:
            raise DatabaseError(f"SQLite safety init error: {e}")

    # ---------------------------------------------------------
    # CREATE TABLES
    # ---------------------------------------------------------
    def _init_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS safety_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                tag TEXT,
                severity REAL,
                correction TEXT,
                details TEXT,
                timestamp TEXT,
                expires_at TEXT
            )
        """)
        self.conn.commit()

    # ---------------------------------------------------------
    # INTERNAL METHOD: INSERT EVENT
    # ---------------------------------------------------------
    def _insert_event(self, evt, ttl_seconds=None):
        expires_at = None
        if ttl_seconds:
            expires_at = (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat()

        self.cursor.execute("""
            INSERT INTO safety_events 
            (text, tag, severity, correction, details, timestamp, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            evt.text,
            evt.tag,
            evt.severity,
            evt.correction,
            json.dumps(evt.details),
            evt.timestamp,
            expires_at
        ))
        self.conn.commit()

    # ---------------------------------------------------------
    # SCAN TEXT FOR SAFETY EVENTS
    # (delegates pattern detection to SafetyEventEngine)
    # ---------------------------------------------------------
    def scan(self, text: str):
        """
        Simulates scanning using built-in rule engine.
        This will be compatible with MongoSafetyBackend.
        """

        # Import here to avoid circular import
        from orbmem.models.safety import SafetyEvent, SafetyRuleEngine

        rule_engine = SafetyRuleEngine()

        events = rule_engine.apply(text)

        for evt in events:
            self._insert_event(evt)

        return events

    # ---------------------------------------------------------
    # LIST ALL EVENTS
    # ---------------------------------------------------------
    def list_events(self):
        self.cursor.execute("SELECT text, tag, severity, correction, details, timestamp FROM safety_events")
        rows = self.cursor.fetchall()

        results = []
        for r in rows:
            results.append({
                "text": r[0],
                "tag": r[1],
                "severity": r[2],
                "correction": r[3],
                "details": json.loads(r[4]) if r[4] else None,
                "timestamp": r[5],
            })
        return results

    # ---------------------------------------------------------
    # CLEAR EXPIRED EVENTS
    # ---------------------------------------------------------
    def delete_expired(self):
        try:
            now = datetime.utcnow().isoformat()
            self.cursor.execute("DELETE FROM safety_events WHERE expires_at IS NOT NULL AND expires_at < ?", (now,))
            self.conn.commit()
        except Exception as e:
            raise DatabaseError(f"SQLite delete expired error: {e}")

    # ---------------------------------------------------------
    # DELETE ALL EVENTS (RESET)
    # ---------------------------------------------------------
    def clear(self):
        self.cursor.execute("DELETE FROM safety_events")
        self.conn.commit()
