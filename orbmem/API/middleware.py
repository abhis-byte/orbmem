# API/middleware.py

import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from orbmem.utils.logger import get_logger

logger = get_logger(__name__)


def setup_middleware(app: FastAPI):
    """
    Registers all middleware for the ORBMEM API server.
    """

    # ---------------------------------------------------------
    # CORS
    # ---------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],            # Restrict later if needed
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
        allow_credentials=False,
    )

    # ---------------------------------------------------------
    # BLOCK API KEYS IN QUERY PARAMS
    # ---------------------------------------------------------
    @app.middleware("http")
    async def block_query_api_keys(request: Request, call_next):
        forbidden = {"api_key", "apikey", "x-api-key"}

        for key in request.query_params.keys():
            if key.lower() in forbidden:
                logger.warning("API key passed via query params (blocked)")
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "InvalidRequest",
                        "message": "API keys must be sent via headers only",
                    },
                )

        return await call_next(request)

    # ---------------------------------------------------------
    # REQUEST LOGGING
    # ---------------------------------------------------------
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.time()

        response = await call_next(request)

        duration = (time.time() - start) * 1000
        logger.info(
            f"{request.method} {request.url.path} "
            f"| {duration:.2f} ms | {response.status_code}"
        )

        return response

    # ---------------------------------------------------------
    # USAGE TRACKING (NO LIMITING)
    # ---------------------------------------------------------
    @app.middleware("http")
    async def usage_tracker(request: Request, call_next):
        response = await call_next(request)

        try:
            auth = getattr(request.state, "auth", None)
            if auth and "api_key_id" in auth:
                from orbmem.db.usage import increment_usage
                increment_usage(auth["api_key_id"])
        except Exception:
            # Never block requests due to tracking failure
            pass

        return response

    # ---------------------------------------------------------
    # SECURITY HEADERS
    # ---------------------------------------------------------
    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response

    logger.info("Middleware initialized successfully.")