# API/dependencies.py

from fastapi import Request, HTTPException, status
from orbmem.core.auth import validate_request
from orbmem.core.config import load_config
from orbmem.utils.exceptions import AuthError
from orbmem.utils.logger import get_logger

logger = get_logger(__name__)


def require_auth(request: Request):
    """
    FastAPI authentication dependency.

    LOCAL MODE:
        - Auth is bypassed
        - Used for PyPI / offline users

    CLOUD MODE:
        - Firebase identity required
        - API key required (X-API-KEY)
        - Validation delegated to core.auth
    """

    cfg = load_config()

    # -------------------------------
    # LOCAL MODE → BYPASS AUTH
    # -------------------------------
    if cfg.api.mode == "local":
        auth_ctx = {
            "mode": "local",
            "uid": None,
            "email": None,
            "is_unlimited": True,
        }
        request.state.auth = auth_ctx
        return auth_ctx

    # -------------------------------
    # CLOUD MODE → STRICT AUTH
    # -------------------------------
    try:
        auth_ctx = validate_request(request)

        # 🔑 IMPORTANT: attach auth context to request state
        request.state.auth = auth_ctx

        return auth_ctx

    except AuthError as e:
        logger.warning(f"Unauthorized request: {e}")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Unauthorized",
                "message": str(e),
            },
        )