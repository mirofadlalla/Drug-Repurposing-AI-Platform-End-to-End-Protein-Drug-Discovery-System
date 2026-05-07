"""
Target Service — Stage 1 & 2
=============================
Stage 1: Query Open Targets GraphQL API to discover disease-associated proteins.
Stage 2: Enrich each target with its UniProt amino-acid sequence.

Local caching in /data folder at project root.
"""

import logging
import json
import os
from typing import Dict, List, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Ensure data directory exists at project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_DIR = os.path.join(PROJECT_ROOT, "data")
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

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

def get_cache_filename(disease_name: str) -> str:
    safe_name = "".join([c if c.isalnum() else "_" for c in disease_name.lower()])
    return os.path.join(CACHE_DIR, f"cache_{safe_name}.json")

def save_to_cache(disease_name: str, disease_id: Optional[str], targets: List[Dict]):
    cache_data = {"disease_id": disease_id, "targets": targets}
    filename = get_cache_filename(disease_name)
    with open(filename, 'w') as f:
        json.dump(cache_data, f, indent=4)
    logger.info("Data cached to %s", filename)

def load_from_cache(disease_name: str) -> Optional[tuple[Optional[str], List[Dict]]]:
    filename = get_cache_filename(disease_name)
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            data = json.load(f)
        return data.get("disease_id"), data.get("targets", [])
    return None

async def fetch_disease_targets(disease_name: str) -> List[Dict]:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(settings.OPEN_TARGETS_API_URL, json={"query": _DISEASE_SEARCH_QUERY, "variables": {"queryString": disease_name}})
            hits = response.json().get("data", {}).get("search", {}).get("hits", [])
        if not hits: return []
        disease_id = hits[0]["id"]
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(settings.OPEN_TARGETS_API_URL, json={"query": _DISEASE_TARGETS_QUERY, "variables": {"diseaseId": disease_id}})
            rows = response.json().get("data", {}).get("disease", {}).get("associatedTargets", {}).get("rows", [])
        return [{"symbol": r["target"]["approvedSymbol"], "name": r["target"]["approvedName"], "score": r["score"]} for r in rows]
    except Exception: return []

async def enrich_targets_with_sequences(targets: List[Dict]) -> List[Dict]:
    async with httpx.AsyncClient(timeout=30) as client:
        for t in targets:
            try:
                res = await client.get(f"https://rest.uniprot.org/uniprotkb/search?query={t['symbol']}&format=json")
                t["sequence"] = res.json()["results"][0]["sequence"]["value"]
            except: t["sequence"] = None
    return targets

async def fetch_pdb_ids(targets: List[Dict]) -> List[Dict]:
    async with httpx.AsyncClient(timeout=30) as client:
        for t in targets:
            try:
                res = await client.get(f"https://rest.uniprot.org/uniprotkb/search?query={t['symbol']}+AND+taxonomy_id:9606&format=json")
                data = res.json()
                t["pdb_ids"] = [ref["id"] for ref in data["results"][0].get("uniProtKBCrossReferences", []) if ref["database"] == "PDB"][:3]
                t["uniprot_id"] = data["results"][0].get("primaryAccession", "")
            except: t["pdb_ids"], t["uniprot_id"] = [], ""
    return targets

async def fetch_disease_targets_with_structures(disease_name: str) -> tuple[Optional[str], List[Dict]]:
    cached = load_from_cache(disease_name)
    if cached: return cached
    targets = await fetch_disease_targets(disease_name)
    if not targets: return None, []
    targets = await enrich_targets_with_sequences(targets)
    targets = await fetch_pdb_ids(targets)
    disease_id = None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(settings.OPEN_TARGETS_API_URL, json={"query": _DISEASE_SEARCH_QUERY,
                                                                          "variables": {"queryString": disease_name}}
            )
            disease_id = res.json()["data"]["search"]["hits"][0]["id"]
    except: pass
    save_to_cache(disease_name, disease_id, targets)
    return disease_id, targets



# diseases_to_download = [
#     "Type 2 Diabetes", "Alzheimer's disease", "Asthma", "Hypertension",
#     "Breast Cancer", "Parkinson's disease", "Rheumatoid Arthritis", "Crohn's disease",
#     "Multiple Sclerosis", "Schizophrenia", "Psoriasis", "Obesity",
#     "Colorectal Cancer", "Lupus", "Osteoarthritis", "Glaucoma",
#     "Myocardial Infarction", "Stroke", "Epilepsy", "Cystic Fibrosis",
#     "Chronic Obstructive Pulmonary Disease", "Atopic Dermatitis"
# ]
# import asyncio


# async def mass_download(disease_list):
#     for d in disease_list:
#         print(f"Processing: {d}...")
#         # Now we 'await' the coroutine so it actually runs
#         await fetch_disease_targets_with_structures(d)
#     print("\n--- All diseases processed and stored in /data folder ---")

# if __name__ == "__main__":
#     # This creates the event loop and runs the async function
#     asyncio.run(mass_download(diseases_to_download))