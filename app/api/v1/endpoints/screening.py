"""
FastAPI endpoint: POST /api/v1/screen
======================================
Orchestrates the full pipeline (Stages 1–5):
  Stage 1 — Open Targets: disease → top 10 associated targets
  Stage 2 — UniProt: fetch amino-acid sequences
  Stage 3 — TDC ADME: load drug library (Half_Life_Obach)
  Stage 4 — DeepPurpose: score all drug-target pairs (MPNN/CNN)
  Stage 5 — Sort descending, label Known Treatment vs Potential Discovery
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.schemas.screening import (
    ScreeningRequest,
    ScreeningResponse,
    DiseaseProteinResponse,
    ProteinTarget,
)
from app.services import ai_service, drug_service, target_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/screen",
    response_model=ScreeningResponse,
    summary="Run virtual drug screening for a disease",
    response_description="Ranked list of top drug-target binding candidates.",
    status_code=status.HTTP_200_OK,
)
async def screen_disease(payload: ScreeningRequest) -> ScreeningResponse:
    """
    Run the full 5-stage drug repurposing pipeline for a given disease.

    - **disease_name**: e.g. `"Type 2 Diabetes"`
    - **known_drugs**: drug names used to label results as *Known Treatment*
      instead of *Potential Discovery* (e.g. `["Metformin", "Insulin"]`)
    - **extra_smiles**: additional SMILES to merge into the drug library
    - **top_k**: how many top results to return (default: 15)
    """
    disease = payload.disease_name
    top_k = payload.top_k or settings.TOP_K_CANDIDATES

    logger.info("=== Virtual screening started for: '%s' ===", disease)

    # ── Stage 1: Disease → targets (Open Targets) ─────────────────────
    logger.info("[Stage 1] Querying Open Targets...")
    raw_targets = await target_service.fetch_disease_targets(disease)

    if not raw_targets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No targets found for disease '{disease}'. "
                "Please check the disease name and try again."
            ),
        )

    # ── Stage 2: Enrich with UniProt sequences ────────────────────────
    logger.info("[Stage 2] Fetching UniProt sequences for %d targets...", len(raw_targets))
    enriched_targets = await target_service.enrich_targets_with_sequences(raw_targets)

    if not enriched_targets:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not retrieve UniProt sequences for any identified target.",
        )

    # ── Stage 3: Load drug library (TDC ADME) ─────────────────────────
    logger.info("[Stage 3] Loading drug library...")
    drugs = drug_service.get_drug_library(extra_smiles=payload.extra_smiles)

    if not drugs:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Drug library unavailable — TDC dataset could not be loaded.",
        )

    # ── Stage 4 + 5: AI prediction and result ranking ─────────────────
    logger.info(
        "[Stage 4] DeepPurpose: %d drugs × %d targets...",
        len(drugs),
        len(enriched_targets),
    )
    candidates, warnings = ai_service.run_virtual_screening(
        drugs=drugs,
        targets=enriched_targets,
        top_k=top_k,
        known_drug_names=payload.known_drugs,
    )

    logger.info(
        "=== Screening complete: %d candidates for '%s' ===",
        len(candidates),
        disease,
    )

    return ScreeningResponse(
        disease_name=disease,
        total_targets_found=len(raw_targets),
        total_drugs_screened=len(drugs),
        total_pairs_evaluated=min(
            len(drugs) * len(enriched_targets),
            settings.MAX_SCREENING_PAIRS,
        ),
        top_candidates=candidates,
        warnings=warnings,
    )


@router.get(
    "/targets/{disease_name}",
    response_model=DiseaseProteinResponse,
    summary="Lookup disease targets and their PDB structures",
    response_description="List of protein targets with PDB structure IDs for a disease.",
    status_code=status.HTTP_200_OK,
)
async def get_disease_targets(disease_name: str) -> DiseaseProteinResponse:
    """
    Quick endpoint to fetch all protein targets associated with a disease.

    This runs Stages 1 & 2 only:
    - Stage 1: Disease → Associated protein targets (Open Targets)
    - Stage 2: Enrichment with UniProt sequences and PDB structure IDs

    This is much faster than the full virtual screening (no AI predictions).

    Parameters
    ----------
    disease_name : str
        Name of the disease (e.g. "COVID-19", "Type 2 Diabetes")

    Returns
    -------
    DiseaseProteinResponse
        JSON with disease info and list of protein targets with PDB IDs.

    Raises
    ------
    HTTPException
        404 if no targets found for the disease.
    """
    logger.info("=== Targets lookup for disease: '%s' ===", disease_name)

    # Combined lookup: Stage 1 + 2 + PDB
    disease_id, enriched_targets = (
        await target_service.fetch_disease_targets_with_structures(disease_name)
    )

    if not enriched_targets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No targets found for disease '{disease_name}'. "
                "Please check the disease name and try again."
            ),
        )

    logger.info(
        "=== Targets lookup complete: %d targets for '%s' ===",
        len(enriched_targets),
        disease_name,
    )

    # Build response with proper schema
    targets_response = [
        ProteinTarget(
            symbol=t["symbol"],
            name=t.get("name", ""),  # Note: original targets don't have name, will update fetch
            association_score=t.get("score", 0.0),
            uniprot_id=t.get("uniprot_id", ""),
            pdb_ids=t.get("pdb_ids", []),
        )
        for t in enriched_targets
    ]

    return DiseaseProteinResponse(
        disease=disease_name,
        disease_id=disease_id,
        total_targets=len(targets_response),
        targets=targets_response,
    )
