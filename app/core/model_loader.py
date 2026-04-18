"""
Singleton DeepPurpose model loader.

The heavy model is downloaded and instantiated exactly once when the FastAPI
application starts up (via the lifespan event in main.py).  All subsequent
calls to `get_model()` return the cached instance without re-loading weights.
"""

import logging
import threading
from typing import Optional

from DeepPurpose import DTI as models

from app.core.config import settings

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_model_instance: Optional[object] = None


def load_model() -> object:
    """
    Load the pretrained DeepPurpose model into memory.

    This function is thread-safe: if two FastAPI worker threads both call it
    simultaneously at startup, only one will actually load; the other will
    wait and then receive the already-loaded instance.

    Returns
    -------
    object
        A pretrained DeepPurpose model ready for inference.

    Raises
    ------
    RuntimeError
        If the model cannot be downloaded or instantiated.
    """
    global _model_instance

    if _model_instance is not None:
        return _model_instance

    with _lock:
        # Double-checked locking — re-check after acquiring the lock.
        if _model_instance is not None:
            return _model_instance

        logger.info("Loading DeepPurpose model '%s' …", settings.MODEL_NAME)
        try:
            _model_instance = models.model_pretrained(model=settings.MODEL_NAME)
            logger.info("Model '%s' loaded successfully.", settings.MODEL_NAME)
        except Exception as exc:
            logger.exception("Failed to load model '%s': %s", settings.MODEL_NAME, exc)
            raise RuntimeError(
                f"Could not load DeepPurpose model '{settings.MODEL_NAME}'"
            ) from exc

    return _model_instance


def get_model() -> object:
    """
    Return the already-loaded model singleton.

    Raises
    ------
    RuntimeError
        If called before `load_model()` has been executed (i.e. before app
        startup has finished).
    """
    if _model_instance is None:
        raise RuntimeError(
            "Model has not been loaded yet. "
            "Ensure `load_model()` is called during application startup."
        )
    return _model_instance
