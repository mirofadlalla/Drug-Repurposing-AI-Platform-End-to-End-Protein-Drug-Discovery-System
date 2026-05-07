"""
Application configuration using Pydantic BaseSettings.
Values are loaded from environment variables or the .env file.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration object for the application."""

    # ── Application ──────────────────────────────────────────────────
    APP_NAME: str = "Drug Repurposing AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── DeepPurpose model ─────────────────────────────────────────────
    MODEL_NAME: str = "MPNN_CNN_BindingDB"

    # ── Open Targets GraphQL API ──────────────────────────────────────
    OPEN_TARGETS_API_URL: str = "https://api.platform.opentargets.org/api/v4/graphql"

    # ── UniProt REST API ──────────────────────────────────────────────
    UNIPROT_API_URL: str = "https://rest.uniprot.org/uniprotkb/search"

    # ── TDC drug library settings ─────────────────────────────────────
    TDC_DATASET_NAME: str = "Half_Life_Obach"

    # ── Virtual screening ─────────────────────────────────────────────
    # Maximum drug-target pairs to score in one request (memory guard)
    MAX_SCREENING_PAIRS: int = 500
    # How many top candidates to return (reference pipeline shows 15)
    TOP_K_CANDIDATES: int = 15

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Module-level singleton — import this everywhere
settings = Settings()
