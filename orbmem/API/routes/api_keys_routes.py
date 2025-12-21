from fastapi import APIRouter, Header, Depends
from sqlalchemy import text

from orbmem.db.api_keys import create_api_key
from orbmem.db.postgres import SessionLocal
from orbmem.utils.exceptions import DatabaseError, AuthError
from orbmem.core.auth import _verify_firebase_token
from orbmem.API.dependencies import require_auth

router = APIRouter(
    prefix="/v1/api-keys",
    tags=["API Keys"]
)

# =================================================
# CREATE FIRST API KEY (BOOTSTRAP)
# =================================================
@router.post("/create")
def create_first_key(x_firebase_token: str = Header(...)):
    """
    Create FIRST API key for user.
    ❌ Fails if user already has an active key.
    """

    user = _verify_firebase_token(x_firebase_token)
    uid = user["uid"]

    db = SessionLocal()
    try:
        # Check if user already has an ACTIVE key
        existing = db.execute(
            text("""
                SELECT 1
                FROM api_keys
                WHERE user_id = :uid
                  AND is_active = TRUE
                LIMIT 1
            """),
            {"uid": uid}
        ).fetchone()

        if existing:
            raise AuthError(
                "API key already exists. Revoke or regenerate to create a new one."
            )

        raw_key = create_api_key(
            user_id=uid,
            plan="test",
            is_unlimited=True
        )

        return {
            "api_key": raw_key,
            "message": "API key created (shown only once)"
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# =================================================
# REGENERATE API KEY (REVOKE OLD → CREATE NEW)
# =================================================
@router.post("/regenerate")
def regenerate_key(user: dict = Depends(require_auth)):
    """
    Revoke ALL existing keys and generate a NEW one.
    """

    uid = user["uid"]
    db = SessionLocal()

    try:
        # 1️⃣ Revoke all existing keys
        db.execute(
            text("""
                UPDATE api_keys
                SET is_active = FALSE
                WHERE user_id = :uid
            """),
            {"uid": uid}
        )

        # 2️⃣ Create new key
        raw_key = create_api_key(
            user_id=uid,
            plan="test",
            is_unlimited=True
        )

        db.commit()

        return {
            "api_key": raw_key,
            "message": "API key regenerated. Old key revoked."
        }

    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Failed to regenerate API key: {e}")

    finally:
        db.close()


# =================================================
# LIST MY API KEYS (MASKED)
# =================================================
@router.get("/me")
def list_my_keys(x_firebase_token: str = Header(...)):
    """
    Returns masked API keys for the logged-in user.
    NEVER returns raw keys.
    """

    user = _verify_firebase_token(x_firebase_token)
    uid = user["uid"]

    db = SessionLocal()
    try:
        rows = db.execute(
            text("""
                SELECT
                    id,
                    api_key_hash,
                    is_active,
                    is_unlimited,
                    expires_at,
                    plan,
                    created_at
                FROM api_keys
                WHERE user_id = :uid
                  AND is_active = TRUE
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"uid": uid}
        ).mappings().all()

        keys = [
            {
                "id": str(r["id"]),
                "key": f"orbynt-********{r['api_key_hash'][-4:]}",
                "is_active": r["is_active"],
                "is_unlimited": r["is_unlimited"],
                "expires_at": r["expires_at"],
                "plan": r["plan"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]

        return {"keys": keys}

    except Exception as e:
        raise DatabaseError(f"Failed to fetch API keys: {e}")

    finally:
        db.close()