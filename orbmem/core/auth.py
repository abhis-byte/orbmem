from fastapi import Request
from datetime import datetime, timezone
import hashlib
import os

from orbmem.utils.exceptions import AuthError
from orbmem.core.config import load_config
from orbmem.db.api_keys import get_api_key_record


# =================================================
# FIREBASE (ENV BASED, SAFE)
# =================================================

_firebase_initialized = False


def _init_firebase():
    global _firebase_initialized
    if _firebase_initialized:
        return

    try:
        import firebase_admin
        from firebase_admin import credentials

        project_id = os.getenv("FIREBASE_PROJECT_ID")
        private_key = os.getenv("FIREBASE_PRIVATE_KEY")
        client_email = os.getenv("FIREBASE_CLIENT_EMAIL")

        if not project_id or not private_key or not client_email:
            raise AuthError("Firebase ENV variables not configured")

        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": project_id,
            "private_key": private_key.replace("\\n", "\n"),
            "client_email": client_email,
            "token_uri": "https://oauth2.googleapis.com/token",
        })

        firebase_admin.initialize_app(cred)
        _firebase_initialized = True

    except Exception as e:
        raise AuthError(f"Firebase init failed: {e}")


def _verify_firebase_token(id_token: str) -> dict:
    """
    Verifies Firebase ID token and returns user dict
    """
    try:
        _init_firebase()
        from firebase_admin import auth
        return auth.verify_id_token(id_token)
    except Exception:
        raise AuthError("Invalid Firebase token")


# =================================================
# API KEY HELPERS
# =================================================

API_KEY_PREFIX = "orbynt-"


def _hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _validate_api_key_format(key: str):
    if not key.startswith(API_KEY_PREFIX):
        raise AuthError("Invalid API key prefix")


# =================================================
# MAIN AUTH ENTRY
# =================================================

def validate_request(request: Request) -> dict:
    """
    LOCAL MODE:
        - No auth required

    CLOUD MODE:
        - Firebase token required (X-Firebase-Token)
        - API key required (Authorization: Bearer <API_KEY>)
    """

    cfg = load_config()

    # ---------------------------
    # LOCAL MODE
    # ---------------------------
    if cfg.api.mode == "local":
        auth_ctx = {
            "mode": "local",
            "is_unlimited": True,
        }
        request.state.auth = auth_ctx
        return auth_ctx

    # ---------------------------
    # HEADERS
    # ---------------------------
    api_auth = request.headers.get("Authorization")
    firebase_token = request.headers.get("X-Firebase-Token")

    if not api_auth or not firebase_token:
        raise AuthError("Missing Authorization or X-Firebase-Token")

    if not api_auth.startswith("Bearer "):
        raise AuthError("Invalid Authorization header format")

    raw_api_key = api_auth.replace("Bearer ", "").strip()

    # ---------------------------
    # VERIFY FIREBASE
    # ---------------------------
    user = _verify_firebase_token(firebase_token)
    uid = user["uid"]

    # ---------------------------
    # VERIFY API KEY
    # ---------------------------
    _validate_api_key_format(raw_api_key)
    api_key_hash = _hash_api_key(raw_api_key)

    record = get_api_key_record(api_key_hash)

    if not record:
        raise AuthError("Invalid API key")

    if record["user_id"] != uid:
        raise AuthError("API key does not belong to this user")

    if not record["is_active"]:
        raise AuthError("API key is disabled")

    if not record["is_unlimited"] and record["expires_at"]:
        now = datetime.now(timezone.utc)
        if record["expires_at"] < now:
            raise AuthError("API key expired")

    # ---------------------------
    # AUTH CONTEXT
    # ---------------------------
    auth_ctx = {
        "mode": "cloud",
        "uid": uid,
        "email": user.get("email"),
        "api_key_id": record["id"],
        "is_unlimited": record["is_unlimited"],
    }

    request.state.auth = auth_ctx
    return auth_ctx