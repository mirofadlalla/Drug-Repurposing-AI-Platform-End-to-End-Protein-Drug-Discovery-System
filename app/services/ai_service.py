"""
AI Service — Stage 4 & 5
=========================
Stage 4: Runs DeepPurpose virtual screening — pairs every drug with every
         target, encodes using MPNN/CNN, and scores binding affinity.
Stage 5: Sorts results (descending score), labels each candidate as
         "Known Treatment" or "Potential Discovery".
"""

import logging
from typing import Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.model_loader import get_model
from app.schemas.screening import DrugCandidate

logger = logging.getLogger(__name__)


# ── Public API ────────────────────────────────────────────────────────────────

def run_virtual_screening(
    drugs: List[Dict],
    targets: List[Dict],
    top_k: int,
    known_drug_names: Optional[List[str]] = None,
) -> Tuple[List[DrugCandidate], List[str]]:
    """
    Stage 4 + 5 — Score all drug-target pairs and return ranked candidates.

    Uses hard-coded MPNN / CNN encodings to match the reference pipeline.
    Results are sorted descending (higher score = stronger predicted binding
    as per BindingDB pIC50 convention).

    Parameters
    ----------
    drugs : list[dict]
        Each element: ``{"drug_name": str, "smiles": str}``.
    targets : list[dict]
        Each element: ``{"symbol": str, "sequence": str, …}``.
    top_k : int
        How many top results to return.
    known_drug_names : list[str] or None
        Drug name substrings used to label "Known Treatment" vs
        "Potential Discovery" (Stage 5, mirrors the reference pipeline).

    Returns
    -------
    candidates : list[DrugCandidate]
        Ranked results (index 0 = best score).
    warnings : list[str]
        Non-fatal messages (e.g. pair-count cap notice).
    """
    warnings: List[str] = []
    model = get_model()
    known_names = [n.lower() for n in (known_drug_names or [])]

    # ── Build cross-product pairs capped at MAX_SCREENING_PAIRS ──────
    X_drugs: List[str] = []
    X_targets: List[str] = []
    pair_info: List[Dict] = []

    logger.info("Preparing data for AI Prediction (Virtual Screening)...")
    for drug in drugs:
        for target in targets:
            smi = drug.get("smiles", "").strip()
            seq = target.get("sequence", "").strip()
            if not smi or not seq:
                continue
            X_drugs.append(smi)
            X_targets.append(seq)
            pair_info.append(
                {
                    "drug_name": drug.get("drug_name", smi[:20]),
                    "target_symbol": target["symbol"],
                }
            )
            if len(X_drugs) >= settings.MAX_SCREENING_PAIRS:
                msg = (
                    f"Drug-target pair count capped at {settings.MAX_SCREENING_PAIRS}. "
                    "Adjust MAX_SCREENING_PAIRS in .env to change this limit."
                )
                logger.warning(msg)
                warnings.append(msg)
                break
        if len(X_drugs) >= settings.MAX_SCREENING_PAIRS:
            break

    total_pairs = len(X_drugs)
    if total_pairs == 0:
        logger.warning("No valid drug-target pairs could be built.")
        warnings.append("No valid drug-target pairs could be built.")
        return [], warnings

    # ── Encode and predict (MPNN drug encoding, CNN target encoding) ──
    logger.info("Running DeepPurpose on %d pairs...", total_pairs)
    try:
        from DeepPurpose.utils import data_process  # type: ignore

        X_pred = data_process(
            X_drug=X_drugs,
            X_target=X_targets,
            y=[0] * total_pairs,       # Dummy labels — not used for inference
            drug_encoding="MPNN",
            target_encoding="CNN",
            split_method="no_split",
        )
        logger.info("AI is predicting Binding Affinities...")
        scores = model.predict(X_pred)
    except Exception as exc:
        logger.exception("DeepPurpose prediction failed: %s", exc)
        warnings.append(f"Prediction error: {exc}")
        return [], warnings

    # ── Stage 5: Sort descending, label Known / Discovery ────────────
    results = [
        {
            "drug_name": pair_info[i]["drug_name"],
            "target_symbol": pair_info[i]["target_symbol"],
            "score": round(float(scores[i]), 4),
        }
        for i in range(total_pairs)
    ]
    results.sort(key=lambda x: x["score"], reverse=True)

    candidates: List[DrugCandidate] = []
    for rank, res in enumerate(results[:top_k], start=1):
        is_known = any(
            known in res["drug_name"].lower() for known in known_names
        )
        status = "Known Treatment" if is_known else "Potential Discovery"

        candidates.append(
            DrugCandidate(
                drug_name=res["drug_name"],
                smiles=X_drugs[rank - 1],   # Preserve original SMILES
                target_symbol=res["target_symbol"],
                uniprot_id="N/A",
                binding_score=res["score"],
                rank=rank,
                status=status,
            )
        )

    logger.info("Returning %d top candidates.", len(candidates))
    return candidates, warnings
