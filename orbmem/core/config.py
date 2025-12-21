import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
from orbmem.utils.exceptions import ConfigError


# ===========================
# DATA CLASSES
# ===========================

@dataclass
class DatabaseConfig:
    postgres_url: Optional[str] = None
    redis_url: Optional[str] = None
    mongo_url: Optional[str] = None
    neo4j_url: Optional[str] = None


@dataclass
class APIConfig:
    mode: str
    debug: bool
    owner_uid: Optional[str]


@dataclass
class RazorpayConfig:
    key_id: str
    key_secret: str
    webhook_secret: Optional[str] = None


@dataclass
class OCDBConfig:
    db: DatabaseConfig
    api: APIConfig
    razorpay: Optional[RazorpayConfig] = None


# ===========================
# ENV HELPER
# ===========================

def _get_env(name: str, default=None, required=False):
    value = os.getenv(name, default)
    if value is not None:
        value = value.strip() or None
    if required and not value:
        raise ConfigError(f"Missing required env var: {name}")
    return value


# ===========================
# MAIN CONFIG
# ===========================

def load_config() -> OCDBConfig:
    load_dotenv(override=True)

    # MODE
    mode = _get_env("OCDB_MODE", "local").lower()
    if mode not in ("local", "cloud"):
        raise ConfigError("OCDB_MODE must be local or cloud")

    # DATABASE
    db_cfg = DatabaseConfig(
        postgres_url=_get_env("POSTGRES_URL"),
        redis_url=_get_env("REDIS_URL"),
        mongo_url=_get_env("MONGO_URL"),
        neo4j_url=_get_env("NEO4J_URL"),
    )

    # API
    api_cfg = APIConfig(
        mode=mode,
        debug=_get_env("OCDB_DEBUG", "0") in ("1", "true", "yes"),
        owner_uid=_get_env("OCDB_OWNER_UID"),
    )

    # RAZORPAY
    key_id = _get_env("RAZORPAY_KEY_ID")
    key_secret = _get_env("RAZORPAY_KEY_SECRET")
    webhook_secret = _get_env("RAZORPAY_WEBHOOK_SECRET")

    razorpay_cfg = None
    if key_id and key_secret:
        razorpay_cfg = RazorpayConfig(
            key_id=key_id,
            key_secret=key_secret,
            webhook_secret=webhook_secret,
        )
    elif key_id or key_secret:
        raise ConfigError("Razorpay partially configured")

    print(f"🔧 OCDB_MODE: {mode}")
    print(f"🗄  Postgres configured: {bool(db_cfg.postgres_url)}")
    print(f"💳 Razorpay enabled: {bool(razorpay_cfg)}")

    return OCDBConfig(
        db=db_cfg,
        api=api_cfg,
        razorpay=razorpay_cfg,
    )