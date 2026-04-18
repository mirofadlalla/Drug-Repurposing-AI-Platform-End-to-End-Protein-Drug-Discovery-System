"""
Pydantic schemas for the virtual screening API.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ── Request ───────────────────────────────────────────────────────────────────

class ScreeningRequest(BaseModel):
    """
    Input payload for POST /api/v1/screen.

    Attributes
    ----------
    disease_name : str
        Free-text disease name (e.g. "Type 2 Diabetes").
    known_drugs : list[str], optional
        Names of drugs already known to treat this disease.
        Used to label results as "Known Treatment" vs "Potential Discovery".
        Example: ["Metformin", "Sitagliptin", "Insulin"]
    extra_smiles : list[str], optional
        Additional drug SMILES to include alongside the TDC library.
    top_k : int, optional
        Number of top candidates to return (default: server setting, max: 100).
    """

    disease_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        example="Type 2 Diabetes",
        description="Name of the disease to run virtual screening for.",
    )
    known_drugs: Optional[List[str]] = Field(
        default=None,
        example=["Metformin", "Sitagliptin", "Insulin", "Glipizide"],
        description="Known drug names for this disease — used for result labelling.",
    )
    extra_smiles: Optional[List[str]] = Field(
        default=None,
        example=["CC(=O)Nc1ccc(O)cc1"],
        description="Additional SMILES strings to include in the drug library.",
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=100,
        description="Number of top candidates to return (overrides server default).",
    )


# ── Response ──────────────────────────────────────────────────────────────────

class DrugCandidate(BaseModel):
    """A single ranked drug-target pair from the virtual screen."""

    drug_name: str
    smiles: str
    target_symbol: str
    uniprot_id: str
    binding_score: float = Field(description="Predicted binding score (higher = stronger affinity).")
    rank: int
    status: str = Field(
        description="'Known Treatment' or 'Potential Discovery'."
    )


class ScreeningResponse(BaseModel):
    """Full response body returned by POST /api/v1/screen."""

    disease_name: str
    total_targets_found: int
    total_drugs_screened: int
    total_pairs_evaluated: int
    top_candidates: List[DrugCandidate]
    warnings: List[str] = []


# ── Disease-to-Proteins Response ──────────────────────────────────────────────

class ProteinTarget(BaseModel):
    """A single protein target associated with a disease."""

    symbol: str = Field(
        description="Gene/protein approved symbol (e.g. 'ACE2')."
    )
    name: str = Field(
        description="Full protein name (e.g. 'angiotensin converting enzyme 2')."
    )
    association_score: float = Field(
        description="Association score from Open Targets (0–1, higher = stronger link to disease)."
    )
    uniprot_id: str = Field(
        description="UniProt ID for fetching sequences and structures."
    )
    pdb_ids: List[str] = Field(
        description="List of PDB structure IDs (up to 3) for this protein."
    )


class DiseaseProteinResponse(BaseModel):
    """Response body for GET /api/v1/targets/{disease_name}."""

    disease: str = Field(
        description="Input disease name."
    )
    disease_id: Optional[str] = Field(
        description="Open Targets EFO disease ID (standardized identifier)."
    )
    total_targets: int = Field(
        description="Number of targets returned."
    )
    targets: List[ProteinTarget] = Field(
        description="List of protein targets with PDB structures."
    )
