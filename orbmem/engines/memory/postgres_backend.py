# engines/memory/postgres_backend.py
# SQLite-based memory backend (cloud-safe v1)

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List

from orbmem.utils.logger import get_logger
from orbmem.utils.exceptions import DatabaseError

logger = get_logger(__name__)

DB_PATH = "ocdb.sqlite3"


class PostgresMemoryBackend:
    """
    Tenant-safe SQLite memory backend.
    """

    def _init_(self):
        self._connect()

    # ---------------------------------------------------------
    # CONNECT / RECONNECT (CRITICAL FIX)
    # ---------------------------------------------------------
    def _connect(self):
        try:
            self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self._init_tables()
            logger.info("Memory backend initialized (SQLite, tenant-safe).")
        except Exception as e:
            raise DatabaseError(f"SQLite init error: {e}")

    def _ensure_connection(self):
        if not hasattr(self, "cursor") or self.cursor is None:
            logger.warning("Memory backend cursor missing, reconnecting...")
            self._connect()

    # ---------------------------------------------------------
    # INIT TABLES
    # ---------------------------------------------------------
    def _init_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                session_id TEXT,
                expires_at TEXT,
                PRIMARY KEY (user_id, key)
            )
        """)
        self.conn.commit()

    # ---------------------------------------------------------
    # CLEAN EXPIRED
    # ---------------------------------------------------------
    def _cleanup_expired(self):
        self._ensure_connection()
        now = datetime.utcnow().isoformat()
        self.cursor.execute(
            "DELETE FROM memory WHERE expires_at IS NOT NULL AND expires_at < ?",
            (now,)
        )
        self.conn.commit()

    # ---------------------------------------------------------
    # SET
    # ---------------------------------------------------------
    def set(
        self,
        key: str,
        value,
        *,
        user_id: str,
        session_id: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
    ):
        try:
            self._ensure_connection()
            self._cleanup_expired()

            expires_at = None
            if ttl_seconds:
                expires_at = (
                    datetime.utcnow() + timedelta(seconds=ttl_seconds)
                ).isoformat()

            value_json = json.dumps(value)

            self.cursor.execute("""
                INSERT INTO memory (user_id, key, value, session_id, expires_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, key) DO UPDATE SET
                    value=excluded.value,
                    session_id=excluded.session_id,
                    expires_at=excluded.expires_at
            """, (
                user_id,
                key,
                value_json,
                session_id,
                expires_at
            ))

            self.conn.commit()

        except Exception as e:
            raise DatabaseError(f"Memory set error: {e}")

    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------
    def get(self, key: str, *, user_id: str):
        try:
            self._ensure_connection()
            self._cleanup_expired()

            self.cursor.execute(
                "SELECT value FROM memory WHERE user_id = ? AND key = ?",
                (user_id, key)
            )

            row = self.cursor.fetchone()
            return json.loads(row[0]) if row else None

        except Exception as e:
            raise DatabaseError(f"Memory get error: {e}")

    # ---------------------------------------------------------
    # KEYS
    # ---------------------------------------------------------
    def keys(self, *, user_id: str) -> List[str]:
        try:
            self._ensure_connection()
            self._cleanup_expired()

            self.cursor.execute(
                "SELECT key FROM memory WHERE user_id = ?",
                (user_id,)
            )
            return [r[0] for r in self.cursor.fetchall()]

        except Exception as e:
            raise DatabaseError(f"Memory keys error: {e}")

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------
    def delete(self, key: str, *, user_id: str):
        try:
            self._ensure_connection()
            self.cursor.execute(
                "DELETE FROM memory WHERE user_id = ? AND key = ?",
                (user_id, key)
            )
            self.conn.commit()
        except Exception as e:
            raise DatabaseError(f"Memory delete error: {e}")