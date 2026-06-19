"""Runtime configuration, all overridable via environment variables."""
from __future__ import annotations

import os


class Settings:
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./companybrain.db")
    GRAPH_BACKEND: str = os.environ.get("GRAPH_BACKEND", "memory")
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    ENV: str = os.environ.get("ENV", "local")


settings = Settings()
