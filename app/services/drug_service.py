"""
Drug Service — Stage 3
=======================
Loads the FDA-approved drug library using TDC's ADME dataset
(Half_Life_Obach), which provides Drug_ID and SMILES columns.

The dataset is cached in /data folder at project root after the first load.
"""

import logging
import os
import json
from functools import lru_cache
from typing import Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Setup cache directory at project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_DIR = os.path.join(PROJECT_ROOT, "data")
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

DRUG_CACHE_FILE = os.path.join(CACHE_DIR, "tdc_drugs_cache.json")


# ── Cache management ──────────────────────────────────────────────────────────

def _load_drugs_from_cache() -> Optional[List[Dict]]:
    """Load cached TDC drugs from file."""
    if os.path.exists(DRUG_CACHE_FILE):
        try:
            logger.info("Loading drugs from cache: %s", DRUG_CACHE_FILE)
            with open(DRUG_CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception as exc:
            logger.warning("Failed to load cache file: %s", exc)
    return None


def _save_drugs_to_cache(drugs: List[Dict]):
    """Save TDC drugs to cache file."""
    try:
        with open(DRUG_CACHE_FILE, 'w') as f:
            json.dump(drugs, f, indent=4)
        logger.info("Drug library saved to cache: %s", DRUG_CACHE_FILE)
    except Exception as exc:
        logger.error("Failed to save drugs to cache: %s", exc)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _fetch_tdc_drugs() -> List[Dict]:
    """
    Fetch TDC ADME Half_Life_Obach dataset.

    Returns
    -------
    list[dict]
        Each dict: ``{"drug_name": str, "smiles": str}``.
    """
    try:
        from tdc.single_pred import ADME  # type: ignore

        logger.info("Fetching TDC ADME dataset '%s' …", settings.TDC_DATASET_NAME)
        data = ADME(name=settings.TDC_DATASET_NAME).get_data()

        drugs: List[Dict] = [
            {
                "drug_name": f"Drug_{row['Drug_ID']}",
                "smiles": str(row["Drug"]).strip(),
            }
            for _, row in data.iterrows()
            if str(row.get("Drug", "")).strip()
        ]

        logger.info("Fetched %d drugs from TDC dataset.", len(drugs))
        return drugs

    except Exception as exc:
        logger.exception("Failed to fetch TDC dataset: %s", exc)
        return []


@lru_cache(maxsize=1)
def _load_tdc_drugs() -> List[Dict]:
    """
    Load the TDC ADME Half_Life_Obach dataset with caching.
    
    First checks local cache file, then fetches from TDC if needed.
    Results are cached in-memory after the first call via lru_cache.

    Returns
    -------
    list[dict]
        Each dict: ``{"drug_name": str, "smiles": str}``.
    """
    # Try loading from cache file first
    cached_drugs = _load_drugs_from_cache()
    if cached_drugs:
        logger.info("Loaded %d drugs from local cache.", len(cached_drugs))
        return cached_drugs

    # Fetch from TDC if cache miss
    logger.info("Cache miss — fetching drugs from TDC API...")
    drugs = _fetch_tdc_drugs()
    
    # Save to cache for future runs
    if drugs:
        _save_drugs_to_cache(drugs)
    
    return drugs


# ── Public API ────────────────────────────────────────────────────────────────

def get_drug_library(
    extra_smiles: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Stage 3 — Return the TDC drug library, optionally merged with extra SMILES.

    Parameters
    ----------
    extra_smiles : list[str] or None
        Additional SMILES strings to prepend (deduplicated).

    Returns
    -------
    list[dict]
        Each dict: ``{"drug_name": str, "smiles": str}``.
    """
    tdc_drugs = _load_tdc_drugs()
    existing_smiles = {d["smiles"] for d in tdc_drugs}

    extra: List[Dict] = []
    if extra_smiles:
        for smi in extra_smiles:
            smi = smi.strip()
            if smi and smi not in existing_smiles:
                extra.append({"drug_name": smi[:20], "smiles": smi})
                existing_smiles.add(smi)
        logger.info("Added %d extra SMILES to the library.", len(extra))

    combined = extra + tdc_drugs
    logger.info("Drug library total: %d molecules.", len(combined))
    return combined
