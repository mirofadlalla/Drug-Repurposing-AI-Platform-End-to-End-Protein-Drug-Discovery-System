"""
Target Service — Stage 1 & 2
=============================
Stage 1: Query Open Targets GraphQL API to discover disease-associated proteins.
Stage 2: Enrich each target with its UniProt amino-acid sequence.
"""

import logging
from typing import Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── GraphQL queries ───────────────────────────────────────────────────────────

_DISEASE_SEARCH_QUERY = """
query searchDisease($queryString: String!) {
  search(queryString: $queryString, entityNames: ["disease"]) {
    hits { id name }
  }
}
"""

_DISEASE_TARGETS_QUERY = """
query diseaseTargets($diseaseId: String!) {
  disease(efoId: $diseaseId) {
    associatedTargets(page: {index: 0, size: 10}) {
      rows {
        target { approvedSymbol approvedName }
        score
      }
    }
  }
}
"""


# ── Public helpers ────────────────────────────────────────────────────────────

async def fetch_disease_targets(disease_name: str) -> List[Dict]:
    """
    Stage 1 — Search for disease via Open Targets and return associated targets.

    Parameters
    ----------
    disease_name : str
        Free-text disease name (e.g. "Type 2 Diabetes").

    Returns
    -------
    list[dict]
        Each dict has keys: ``symbol``, ``score``.
    """
    logger.info("Searching Open Targets for disease: '%s'", disease_name)

    # Step 1.1 — Resolve EFO ID
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                settings.OPEN_TARGETS_API_URL,
                json={
                    "query": _DISEASE_SEARCH_QUERY,
                    "variables": {"queryString": disease_name},
                },
            )
            response.raise_for_status()
            hits = (
                response.json()
                .get("data", {})
                .get("search", {})
                .get("hits", [])
            )
    except httpx.HTTPStatusError as exc:
        logger.error("Open Targets search HTTP error: %s", exc)
        return []
    except httpx.RequestError as exc:
        logger.error("Open Targets search request error: %s", exc)
        return []

    if not hits:
        logger.warning("No disease found for query '%s'", disease_name)
        return []

    disease_id = hits[0]["id"]
    logger.info(
        "Target Disease Identified: %s (%s)", hits[0]["name"], disease_id
    )

    # Step 1.2 — Fetch top 10 associated proteins
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                settings.OPEN_TARGETS_API_URL,
                json={
                    "query": _DISEASE_TARGETS_QUERY,
                    "variables": {"diseaseId": disease_id},
                },
            )
            response.raise_for_status()
            rows = (
                response.json()
                .get("data", {})
                .get("disease", {})
                .get("associatedTargets", {})
                .get("rows", [])
            )
    except httpx.HTTPStatusError as exc:
        logger.error("Open Targets targets HTTP error: %s", exc)
        return []
    except httpx.RequestError as exc:
        logger.error("Open Targets targets request error: %s", exc)
        return []

    targets = [
        {
            "symbol": r["target"]["approvedSymbol"],
            "name": r["target"]["approvedName"],
            "score": r["score"],
        }
        for r in rows
    ]
    logger.info("Retrieved %d targets for disease '%s'", len(targets), disease_name)
    return targets


async def enrich_targets_with_sequences(targets: List[Dict]) -> List[Dict]:
    """
    Stage 2 — Fetch UniProt amino-acid sequences for each target.

    Targets for which retrieval fails are silently skipped.

    Parameters
    ----------
    targets : list[dict]
        Output of :func:`fetch_disease_targets`.

    Returns
    -------
    list[dict]
        Enriched dicts with added key: ``sequence``.
    """
    logger.info("Fetching Amino Acid Sequences from UniProt...")
    final_targets: List[Dict] = []

    for t in targets:
        symbol = t["symbol"]
        url = f"https://rest.uniprot.org/uniprotkb/search?query={symbol}&format=json"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

            sequence: Optional[str] = (
                data["results"][0]["sequence"]["value"]
            )
            t["sequence"] = sequence
            final_targets.append(t)
            logger.info("Successfully fetched sequence for: %s", symbol)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to fetch sequence for '%s': %s", symbol, exc)

    return final_targets


async def fetch_pdb_ids(targets: List[Dict]) -> List[Dict]:
    """
    Enrich targets with PDB structure IDs from UniProt cross-references.

    Parameters
    ----------
    targets : list[dict]
        Targets with keys: ``symbol``, ``score``, etc.

    Returns
    -------
    list[dict]
        Enriched targets with added key: ``pdb_ids`` (list of up to 3 IDs).
    """
    logger.info("Fetching PDB structure IDs from UniProt...")

    for t in targets:
        symbol = t["symbol"]
        url = f"https://rest.uniprot.org/uniprotkb/search?query={symbol}+AND+taxonomy_id:9606&format=json"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

            # Extract PDB IDs from cross-references
            references = data["results"][0].get("uniProtKBCrossReferences", [])
            pdb_entries = [
                ref["id"]
                for ref in references
                if ref["database"] == "PDB"
            ]

            # Keep first 3 PDB IDs
            t["pdb_ids"] = pdb_entries[:3]
            
            # Also capture UniProt ID
            t["uniprot_id"] = data["results"][0].get("primaryAccession", "")

            logger.info(
                "Found %d PDB IDs for: %s", len(t["pdb_ids"]), symbol
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to fetch PDB IDs for '%s': %s", symbol, exc
            )
            t["pdb_ids"] = []
            t["uniprot_id"] = ""

    return targets


async def fetch_disease_targets_with_structures(
    disease_name: str,
) -> tuple[Optional[str], List[Dict]]:
    """
    Combined endpoint: Fetch disease, targets, sequences, AND PDB structures.

    Parameters
    ----------
    disease_name : str
        Free-text disease name.

    Returns
    -------
    tuple[str, list[dict]]
        (disease_id, enriched_targets_with_pdb)
    """
    logger.info("=== Combined lookup for disease: '%s' ===", disease_name)

    # Step 1: Get targets
    targets = await fetch_disease_targets(disease_name)
    if not targets:
        return None, []

    # Step 2: Get sequences
    targets_with_seqs = await enrich_targets_with_sequences(targets)
    if not targets_with_seqs:
        return None, []

    # Step 3: Get PDB IDs
    targets_with_pdb = await fetch_pdb_ids(targets_with_seqs)

    # Extract disease ID from first lookup
    disease_id = None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                settings.OPEN_TARGETS_API_URL,
                json={
                    "query": _DISEASE_SEARCH_QUERY,
                    "variables": {"queryString": disease_name},
                },
            )
            hits = (
                response.json()
                .get("data", {})
                .get("search", {})
                .get("hits", [])
            )
            if hits:
                disease_id = hits[0]["id"]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not fetch disease ID: %s", exc)

    return disease_id, targets_with_pdb
