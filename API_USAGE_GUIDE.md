# API Usage Guide — Drug Repurposing AI

## Quick Start

### Base URL
```
http://localhost:8000
```

### Interactive API Docs
```
http://localhost:8000/docs (Swagger UI)
http://localhost:8000/redoc (ReDoc)
```

---

## Endpoint 1: Quick Disease-to-Targets Lookup

**Fastest way to find protein targets for a disease + their 3D structures**

### Request
```
GET /api/v1/screen/targets/{disease_name}
```

**Parameters**:
- `disease_name` (path): Name of the disease (e.g., "COVID-19", "Type 2 Diabetes")

### Example (cURL)
```bash
curl -X GET "http://localhost:8000/api/v1/screen/targets/COVID-19"
```

### Example (Python)
```python
import requests

response = requests.get("http://localhost:8000/api/v1/screen/targets/COVID-19")
result = response.json()

print(f"Disease: {result['disease']}")
print(f"Total Targets: {result['total_targets']}")

for target in result['targets']:
    print(f"\n{target['symbol']} ({target['name']})")
    print(f"  Association Score: {target['association_score']}")
    print(f"  PDB IDs: {', '.join(target['pdb_ids'])}")
    print(f"  UniProt ID: {target['uniprot_id']}")
```

### Response Example
```json
{
  "disease": "COVID-19",
  "disease_id": "MONDO_0100096",
  "total_targets": 10,
  "targets": [
    {
      "symbol": "ACE2",
      "name": "angiotensin converting enzyme 2",
      "association_score": 0.693,
      "uniprot_id": "Q9BYF1",
      "pdb_ids": ["1R42", "1R4L", "2AJF"]
    },
    {
      "symbol": "TYK2",
      "name": "tyrosine kinase 2",
      "association_score": 0.659,
      "uniprot_id": "P29597",
      "pdb_ids": ["3LXN", "3LXP", "3NYX"]
    },
    {
      "symbol": "IFNAR2",
      "name": "interferon alpha and beta receptor subunit 2",
      "association_score": 0.642,
      "uniprot_id": "P48551",
      "pdb_ids": ["1N6U", "1N6V", "2HYM"]
    }
  ]
}
```

**Response Time**: ~5-10 seconds ⚡

---

## Endpoint 2: Full AI Drug Screening Pipeline

**Complete drug repurposing analysis with AI predictions**

### Request
```
POST /api/v1/screen/screen
```

**Request Body** (JSON):
```json
{
  "disease_name": "Type 2 Diabetes",
  "known_drugs": ["Metformin", "Sitagliptin", "Insulin", "Glipizide"],
  "extra_smiles": ["CC(=O)Nc1ccc(O)cc1"],
  "top_k": 15
}
```

**Parameters**:
- `disease_name` (required, string): Disease name
- `known_drugs` (optional, array): List of drugs already known to treat this disease
- `extra_smiles` (optional, array): Additional drug SMILES to screen
- `top_k` (optional, integer): Number of top candidates to return (1-100, default: 15)

### Example (cURL)
```bash
curl -X POST "http://localhost:8000/api/v1/screen/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "disease_name": "COVID-19",
    "known_drugs": ["Remdesivir", "Dexamethasone"],
    "top_k": 10
  }'
```

### Example (Python)
```python
import requests
import json

payload = {
    "disease_name": "COVID-19",
    "known_drugs": ["Remdesivir", "Dexamethasone"],
    "top_k": 10
}

response = requests.post(
    "http://localhost:8000/api/v1/screen/screen",
    json=payload
)

result = response.json()

print(f"Disease: {result['disease_name']}")
print(f"Targets Found: {result['total_targets_found']}")
print(f"Drugs Screened: {result['total_drugs_screened']}")
print(f"Pairs Evaluated: {result['total_pairs_evaluated']}\n")

for candidate in result['top_candidates']:
    print(f"Rank {candidate['rank']}: {candidate['drug_name']}")
    print(f"  Target: {candidate['target_symbol']}")
    print(f"  Binding Score: {candidate['binding_score']}")
    print(f"  Status: {candidate['status']}\n")
```

### Response Example
```json
{
  "disease_name": "COVID-19",
  "total_targets_found": 10,
  "total_drugs_screened": 5000,
  "total_pairs_evaluated": 50000,
  "top_candidates": [
    {
      "rank": 1,
      "drug_name": "Drug_1234",
      "target_symbol": "ACE2",
      "binding_score": 0.895,
      "status": "🆕 Potential Discovery",
      "smiles": "CC(C)Cc1ccc(cc1)C(C)C(O)=O",
      "uniprot_id": "Q9BYF1"
    },
    {
      "rank": 2,
      "drug_name": "Drug_5678",
      "target_symbol": "TYK2",
      "binding_score": 0.872,
      "status": "🆕 Potential Discovery",
      "smiles": "Cc1ccc(cc1)S(=O)(=O)N2CCCC2",
      "uniprot_id": "P29597"
    },
    {
      "rank": 3,
      "drug_name": "Remdesivir",
      "target_symbol": "IFNAR2",
      "binding_score": 0.821,
      "status": "✅ Known Treatment",
      "smiles": "CC(C)Cc1ccc(cc1)C(C)C(O)=O",
      "uniprot_id": "P48551"
    }
  ],
  "warnings": []
}
```

**Response Time**: ~2-5 minutes ⏱️ (depending on hardware)

---

## Common Use Cases

### Use Case 1: Find Drug Targets for a Disease
**Endpoint**: `GET /api/v1/screen/targets/{disease_name}`

```bash
# Find COVID-19 targets and their structures
curl -X GET "http://localhost:8000/api/v1/screen/targets/COVID-19"
```

✅ **Best for**: Quick protein lookup, structural biology research

### Use Case 2: Discover New Drug Candidates
**Endpoint**: `POST /api/v1/screen/screen`

```bash
# Screen drugs for Type 2 Diabetes, marking known treatments
curl -X POST "http://localhost:8000/api/v1/screen/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "disease_name": "Type 2 Diabetes",
    "known_drugs": ["Metformin", "Insulin"],
    "top_k": 20
  }'
```

✅ **Best for**: Drug repurposing, therapeutic discovery

### Use Case 3: Screen Custom Drugs
**Endpoint**: `POST /api/v1/screen/screen` with `extra_smiles`

```python
import requests

custom_drugs = [
    "CC(=O)Nc1ccc(O)cc1",  # Paracetamol
    "CC(C)Cc1ccc(cc1)C(C)C(O)=O"  # Ibuprofen
]

payload = {
    "disease_name": "Alzheimer's Disease",
    "extra_smiles": custom_drugs,
    "top_k": 10
}

response = requests.post(
    "http://localhost:8000/api/v1/screen/screen",
    json=payload
)
```

✅ **Best for**: Testing specific drug candidates, integration with drug development pipelines

---

## Status Codes & Error Handling

### Success Responses

| Status | Meaning |
|--------|---------|
| 200 | Request successful, results returned |

### Error Responses

| Status | Meaning | Example |
|--------|---------|---------|
| 400 | Invalid request (bad JSON, missing fields) | `{"detail": "Validation error..."}` |
| 404 | Disease not found | `{"detail": "No targets found for disease 'XYZ'"}`|
| 422 | Unprocessable entity (no sequences found) | `{"detail": "Could not retrieve UniProt sequences"}` |
| 503 | Service unavailable (TDC dataset error) | `{"detail": "Drug library unavailable"}` |

### Example Error Response
```json
{
  "detail": "No targets found for disease 'InvalidDisease'. Please check the disease name and try again."
}
```

---

## Performance Tips

### 1. Use Quick Lookup First
If you only need protein targets, use `/targets/{disease_name}` (5-10s) instead of full screening (2-5 min).

### 2. Reduce top_k for Faster Results
Smaller `top_k` values don't significantly reduce runtime, but can speed up response serialization.

### 3. Batch Requests Carefully
The server runs heavy AI computations. Avoid simultaneous full screenings on limited hardware.

### 4. Cache Results
If you're working with the same disease repeatedly, store the JSON results locally.

---

## Troubleshooting

### "No targets found for disease"
- Check spelling (case-insensitive, but must match Open Targets database)
- Try more general terms (e.g., "diabetes" instead of "Type 2 Diabetes")
- Some rare diseases may not be in Open Targets

### "Could not retrieve UniProt sequences"
- UniProt API may be temporarily unavailable
- Some proteins may not have sequences in the database
- Try again in a few minutes

### "Drug library unavailable"
- TDC dataset not downloaded during startup
- Check Docker logs: `docker-compose logs drug-repurposing-ai`
- Restart container: `docker-compose up --build`

### Timeout on POST /screen
- Full screening takes 2-5 minutes — be patient!
- For long-running requests, use a timeout > 5 minutes on your client
- Python example: `requests.post(..., timeout=300)`

---

## Data Attribution

- **Disease-Protein Links**: [Open Targets](https://www.opentargets.org/)
- **Protein Sequences**: [UniProt](https://www.uniprot.org/)
- **3D Structures**: [PDB/RCSB](https://www.rcsb.org/)
- **Approved Drugs**: [TDC/ADME Dataset](https://tdcommons.ai/)
- **AI Model**: [DeepPurpose](https://github.com/kexinhuang12345/DeepPurpose)

---

**API Version**: 1.0  
**Last Updated**: April 2026
