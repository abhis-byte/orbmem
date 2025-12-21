from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
import secrets
import hashlib

from orbmem.db.postgres import SessionLocal
from orbmem.utils.exceptions import DatabaseError, AuthError
from sqlalchemy import text

API_KEY_PREFIX = "orbynt-"


# -------------------------------------------------
# INTERNAL HELPERS
# -------------------------------------------------

def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_api_key() -> tuple[str, str]:
    """
    Generates a raw API key and its hash.
    """
    token = secrets.token_urlsafe(32)
    raw_key = f"{API_KEY_PREFIX}{token}"
    return raw_key, _hash_key(raw_key)


# -------------------------------------------------
# CREATE API KEY
# -------------------------------------------------

from sqlalchemy import text   # you already imported this ✅

def create_api_key(
    *,
    user_id: str,
    plan: str,
    is_unlimited: bool = False,
    duration_days: Optional[int] = None,
) -> str:
    """
    Creates a new API key for a user.
    Returns RAW key (shown only once).
    """

    raw_key, key_hash = generate_api_key()

    expires_at = None
    if not is_unlimited and duration_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)

    db = SessionLocal()
    try:
        db.execute(
            text("""
                INSERT INTO api_keys (
                    user_id,
                    api_key_hash,
                    is_active,
                    is_unlimited,
                    expires_at,
                    plan
                )
                VALUES (
                    :user_id,
                    :hash,
                    TRUE,
                    :is_unlimited,
                    :expires_at,
                    :plan
                )
            """),
            {
                "user_id": user_id,
                "hash": key_hash,
                "is_unlimited": is_unlimited,
                "expires_at": expires_at,
                "plan": plan,
            }
        )
        db.commit()
        return raw_key

    except Exception as e:
        db.rollback()
        raise DatabaseError(f"API key creation failed: {e}")

    finally:
        db.close()

# -------------------------------------------------
# LOOKUP API KEY (YOUR ORIGINAL LOGIC)
# -------------------------------------------------

def get_api_key_record(api_key_hash: str) -> Optional[Dict]:
    """
    Fetch API key record by hash.
    Returns dict or None.
    """
    db = SessionLocal()
    try:
        result = db.execute(
          text("""
            SELECT id, user_id, is_active, is_unlimited, expires_at
            FROM api_keys
            WHERE api_key_hash = :hash
            LIMIT 1
          """),
           {"hash": api_key_hash}
        ).fetchone()

        if not result:
            return None

        return {
            "id": result[0],
            "user_id": result[1],
            "is_active": result[2],
            "is_unlimited": result[3],
            "expires_at": result[4],
        }

    except Exception as e:
        raise DatabaseError(f"API key lookup failed: {e}")

    finally:
        db.close()


# -------------------------------------------------
# VERIFY API KEY
# -------------------------------------------------

def verify_api_key(raw_key: str) -> Dict:
    """
    Validates API key:
    - exists
    - active
    - not expired (unless unlimited)
    """

    if not raw_key.startswith(API_KEY_PREFIX):
        raise AuthError("Invalid API key prefix")

    key_hash = _hash_key(raw_key)
    record = get_api_key_record(key_hash)

    if not record:
        raise AuthError("Invalid API key")

    if not record["is_active"]:
        raise AuthError("API key is disabled")

    if not record["is_unlimited"] and record["expires_at"]:
        if datetime.now(timezone.utc) > record["expires_at"]:
            raise AuthError("API key expired")

    return {
        "api_key_id": record["id"],
        "user_id": record["user_id"],
        "is_unlimited": record["is_unlimited"],
    }