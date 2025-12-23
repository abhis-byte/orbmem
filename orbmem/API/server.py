# API/server.py

from dotenv import load_dotenv
load_dotenv()   # 🔥 THIS IS THE FIX

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from orbmem.core.config import load_config
from orbmem.API.middleware import setup_middleware
from orbmem.API.routes.ocdb_routes import router as ocdb_router
from orbmem.API.routes.api_keys_routes import router as api_keys_router
from orbmem.API.routes.payment_routes import router as payment_router
from orbmem.API.routes.webhook_routes import router as webhook_router
from orbmem.utils.logger import get_logger
from orbmem.utils.exceptions import (
    OCDBError,
    ValidationError,
    DatabaseError,
    AuthError,
)

logger = get_logger(__name__)

# ---------------------------------------------------------
# LOAD CONFIG ONCE
# ---------------------------------------------------------
CONFIG = load_config()


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI app for ORBMEM Cloud API.
    """

    app = FastAPI(
        title="ORBMEM Cloud API",
        description="Cognitive Database API",
        version="1.0.0",
        docs_url="/docs" if CONFIG.api.debug else None,
        redoc_url="/redoc" if CONFIG.api.debug else None,
    )

    # ---------------------------------------------------------
    # MIDDLEWARE
    # ---------------------------------------------------------
    setup_middleware(app)

    # ---------------------------------------------------------
    # ROUTERS
    # ---------------------------------------------------------
    app.include_router(ocdb_router)
    app.include_router(api_keys_router)
    app.include_router(payment_router)
    app.include_router(webhook_router)
    logger.info("API routes registered successfully.")


    # ---------------------------------------------------------
    # GLOBAL EXCEPTION HANDLERS
    # ---------------------------------------------------------

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError):
        logger.warning(f"Validation error: {exc}")
        return JSONResponse(
            status_code=400,
            content={
                "error": "ValidationError",
                "message": str(exc),
            },
        )

    @app.exception_handler(AuthError)
    async def auth_handler(request: Request, exc: AuthError):
        logger.warning(f"Authentication error: {exc}")
        return JSONResponse(
            status_code=401,
            content={
                "error": "Unauthorized",
                "message": str(exc),
            },
        )

    @app.exception_handler(DatabaseError)
    async def database_handler(request: Request, exc: DatabaseError):
        logger.error(f"Database error: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "DatabaseError",
                "message": "A database error occurred",
            },
        )

    @app.exception_handler(OCDBError)
    async def ocdb_handler(request: Request, exc: OCDBError):
        logger.error(f"OCDB internal error: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "OCDBError",
                "message": "Internal server error",
            },
        )

    # ---------------------------------------------------------
    # HEALTH CHECK
    # ---------------------------------------------------------
    @app.get("/health", tags=["System"])
    async def health_check():
        return {
            "status": "ok",
            "service": "orbmem-api",
            "mode": CONFIG.api.mode,
        }

    logger.info("ORBMEM API server initialized.")
    return app


# ---------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------
app = create_app()