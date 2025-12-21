# orbmem/db/usage.py

from datetime import datetime, timezone
from orbmem.db.postgres import SessionLocal
from orbmem.utils.exceptions import DatabaseError


def increment_usage(api_key_id: str):
    """
    Track API usage per API key.
    Unlimited plans are NOT blocked.
    This is tracking only.
    """
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        db.execute(
            """
            INSERT INTO api_usage (api_key_id, count, window_start)
            VALUES (:api_key_id, 1, :now)
            ON CONFLICT (api_key_id)
            DO UPDATE SET count = api_usage.count + 1
            """,
            {
                "api_key_id": api_key_id,
                "now": now,
            },
        )

        db.commit()

    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Usage tracking failed: {e}")

    finally:
        db.close()