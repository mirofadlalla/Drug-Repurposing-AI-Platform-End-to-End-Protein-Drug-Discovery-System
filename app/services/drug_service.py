"""
Drug Service — Stage 3
=======================
Loads the FDA-approved drug library using TDC's ADME dataset
(Half_Life_Obach), which provides Drug_ID and SMILES columns.

The dataset is cached in-memory after the first load via lru_cache.
"""

import logging
from functools import lru_cache
from typing import Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


# ── Internal helpers ──────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_tdc_drugs() -> List[Dict]:
    """
    Load the TDC ADME Half_Life_Obach dataset (cached after first call).

    Returns
    -------
    list[dict]
        Each dict: ``{"drug_name": str, "smiles": str}``.
    """
    try:
        from tdc.single_pred import ADME  # type: ignore

        logger.info("Loading TDC ADME dataset '%s' …", settings.TDC_DATASET_NAME)
        data = ADME(name=settings.TDC_DATASET_NAME).get_data()

        drugs: List[Dict] = [
            {
                "drug_name": f"Drug_{row['Drug_ID']}",
                "smiles": str(row["Drug"]).strip(),
            }
            for _, row in data.iterrows()
            if str(row.get("Drug", "")).strip()
        ]

        logger.info("Loaded %d drugs ready for screening.", len(drugs))
        return drugs

    except Exception as exc:
        logger.exception("Failed to load TDC dataset: %s", exc)
        return []


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
