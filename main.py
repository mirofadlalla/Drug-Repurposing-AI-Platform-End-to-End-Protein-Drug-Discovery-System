"""
Application entry point.

Initialises the FastAPI application, registers startup/shutdown lifecycle
events, and mounts the v1 API router.

Run locally:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import logging
import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.model_loader import load_model

# ── Logging configuration ─────────────────────────────────────────────────────

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "level": "DEBUG" if settings.DEBUG else "INFO",
        "handlers": ["console"],
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    """
    Load heavy resources at startup; clean up on shutdown.

    The DeepPurpose model is loaded here so that:
    - It is ready before the first request arrives.
    - It is loaded exactly once (Singleton pattern enforced by model_loader).
    """
    logger.info("Starting up %s v%s …", settings.APP_NAME, settings.APP_VERSION)
    load_model()  # Pre-load the Singleton model
    logger.info("Application ready.")
    yield
    logger.info("Shutting down %s …", settings.APP_NAME)


# ── FastAPI application ───────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Drug Repurposing AI — virtual screening pipeline powered by "
        "DeepPurpose, Open Targets, UniProt, and TDC."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — adjust origins for production deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount versioned API router
app.include_router(api_router, prefix="/api/v1")


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Returns 200 OK when the service is alive and the model is loaded."""
    from app.core.model_loader import _model_instance  # noqa: PLC0415

    return {
        "status": "ok",
        "model_loaded": _model_instance is not None,
        "version": settings.APP_VERSION,
    }
