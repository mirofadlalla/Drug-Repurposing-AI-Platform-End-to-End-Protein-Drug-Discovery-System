# Drug Repurposing AI System — Complete Documentation

## 🎯 System Overview

This is an **AI-powered drug repurposing platform** that discovers novel uses for existing drugs by identifying protein targets associated with diseases and predicting drug-protein binding affinities.

### Architecture: 5-Stage Pipeline

```
┌─────────────┐     ┌────────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────┐
│   Disease   │────▶│  Disease   │────▶│ UniProt  │────▶│ DeepPurpose  │────▶│  Results │
│    Input    │     │  Targets   │     │ Sequences│     │ AI Prediction│     │  Ranked  │
└─────────────┘     └────────────┘     └──────────┘     └──────────────┘     └──────────┘
     Stage 1           Stage 2            Stage 3           Stage 4 & 5
```

---

## 📊 Detailed Pipeline Breakdown

### **Stage 1: Disease-to-Targets Mapping (Open Targets API)**

**Purpose**: Identify protein targets associated with the input disease.

**Data Source**: [Open Targets GraphQL API](https://api.platform.opentargets.org/api/v4/graphql)

**Process**:
1. Search for disease by name → returns EFO ID (standardized disease identifier)
2. Query for all proteins associated with that disease
3. Return top 10 targets ranked by association score (0–1 scale)

**Output Example**:
```json
{
  "disease": "COVID-19",
  "targets": [
    {
      "symbol": "ACE2",
      "name": "angiotensin converting enzyme 2",
      "score": 0.693
    },
    {
      "symbol": "TYK2",
      "name": "tyrosine kinase 2",
      "score": 0.659
    }
  ]
}
```

**Key Concept**: Association Score = strength of scientific evidence linking protein to disease

---

### **Stage 2: Protein Structure Data (UniProt + PDB)**

**Purpose**: Enrich targets with PDB IDs and amino-acid sequences.

**Data Sources**:
- [UniProt API](https://www.uniprot.org/help/api) — protein annotations & cross-references
- [PDB (Protein Data Bank)](https://www.rcsb.org/) — 3D structures

**Process**:
1. For each target protein symbol, query UniProt for human protein
2. Extract PDB cross-references (structural neighbors)
3. Extract amino-acid sequence for Stage 4 AI input
4. Return top 3 PDB IDs per protein

**Output Example**:
```json
{
  "enriched_targets": [
    {
      "symbol": "ACE2",
      "name": "angiotensin converting enzyme 2",
      "score": 0.693,
      "pdb_ids": ["1R42", "1R4L", "2AJF"],
      "sequence": "MDTIDVQWWEDWQVSTAQISFNIQKELSVSPLHSVYVDQWDWERVMGDGERQFSTLKSTVEAIWAGIKATEAAVSEEFGLAPFLPDQIHFVHSQELLSRYPDLDAKGRERAIAKDLGAVFLVGIGGKLSDGHRHDVRAPDYDDWSTPSELGHAQDNGDILVWNPVLEDAFELSSMGIRVDADTLKHQLALTGDEDRLELEWHQALLRGEMPFLFTLKDUDWKAEPQVSTQVSWPAWK..."
    }
  ]
}
```

---

### **Stage 3: Drug Library (TDC - Therapeutics Data Commons)**

**Purpose**: Load approved drugs with their molecular structures.

**Data Source**: [TDC Dataset - ADME](https://tdcommons.ai/)

**Format**: SMILES strings (chemical notation for drug structure)

**Example**:
```
Drug_1: CC(C)Cc1ccc(cc1)C(C)C(O)=O  (Ibuprofen)
Drug_2: CC(=O)Nc1ccc(O)cc1  (Paracetamol)
```

**Count**: ~5,000–10,000 drugs per run (depends on dataset version)

---

### **Stage 4: AI Prediction Engine (DeepPurpose)**

**Purpose**: Predict binding affinity for all drug-target pairs using deep learning.

**Model**: MPNN-CNN (Message Passing Neural Network + Convolutional Neural Network)
- **MPNN**: Processes protein amino-acid sequences
- **CNN**: Processes drug molecular structures (SMILES)
- **Output**: Binding affinity score (higher = stronger binding = better drug candidate)

**Computation**:
- For each disease: `num_drugs × num_targets` predictions
- Example: 5,000 drugs × 10 targets = 50,000 predictions
- Time: ~2–5 minutes per disease (GPU accelerated)

**Output Format**:
```json
{
  "drug_name": "Drug_1234",
  "target_symbol": "ACE2",
  "binding_score": 0.782
}
```

---

### **Stage 5: Result Ranking & Labeling**

**Purpose**: Sort candidates and classify as "Known Treatment" or "Potential Discovery".

**Process**:
1. Sort all predictions by binding score (descending)
2. Check if drug is in "known_drugs" list → label as "✅ Known Treatment"
3. Otherwise → label as "🆕 Potential Discovery" (novel repurposing opportunity)
4. Return top-K results (default: 15)

**Final Output**:
```json
{
  "rank": 1,
  "drug_name": "Drug_1234",
  "target_symbol": "ACE2",
  "binding_score": 0.895,
  "status": "🆕 Potential Discovery"
}
```

---

## 🔌 API Endpoints

### **Endpoint 1: Virtual Screening (Full Pipeline)**

```
POST /api/v1/screen
```

**Purpose**: Run the complete 5-stage pipeline for a disease.

**Request**:
```json
{
  "disease_name": "Type 2 Diabetes",
  "known_drugs": ["Metformin", "Sitagliptin", "Insulin"],
  "extra_smiles": ["CC(C)Cc1ccc(cc1)C(C)C(O)=O"],
  "top_k": 15
}
```

**Response**:
```json
{
  "disease_name": "Type 2 Diabetes",
  "targets_count": 10,
  "drugs_count": 5000,
  "predictions_count": 50000,
  "candidates": [
    {
      "rank": 1,
      "drug": "Drug_456",
      "target": "PPARG",
      "binding_score": 0.892,
      "status": "🆕 Potential Discovery"
    }
  ],
  "warnings": []
}
```

**Time**: ~2–5 minutes

---

### **Endpoint 2: Disease-to-Proteins (Combined Lookup)**

```
GET /api/v1/targets/{disease_name}
```

**Purpose**: Quick lookup of targets and their PDB structures (Stages 1 & 2 only).

**Response**:
```json
{
  "disease": "COVID-19",
  "disease_id": "MONDO_0100096",
  "targets": [
    {
      "symbol": "ACE2",
      "name": "angiotensin converting enzyme 2",
      "association_score": 0.693,
      "pdb_ids": ["1R42", "1R4L", "2AJF"],
      "uniprot_id": "Q9BYF1"
    },
    {
      "symbol": "TYK2",
      "name": "tyrosine kinase 2",
      "association_score": 0.659,
      "pdb_ids": ["3LXN", "3LXP", "3NYX"],
      "uniprot_id": "P29597"
    }
  ]
}
```

**Time**: ~5–10 seconds

---

## 🏗️ Service Layer Architecture

### **target_service.py**
- `fetch_disease_targets()` — Stage 1 (Open Targets)
- `enrich_targets_with_sequences()` — Stage 2 (UniProt)
- `get_pdb_ids()` — PDB lookup for targets

### **drug_service.py**
- `get_drug_library()` — Stage 3 (TDC)

### **ai_service.py**
- `run_virtual_screening()` — Stages 4 & 5 (DeepPurpose)
- `predict_bindings()` — Raw AI predictions
- `rank_candidates()` — Sorting & labeling

---

## 📦 Key Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| **FastAPI** | 0.111.0 | Web framework |
| **DeepPurpose** | 0.1.5 | Drug-target interaction prediction |
| **PyTDC** | 1.0.0 | Drug library (TDC dataset) |
| **RDKit** | 2023.9.6 | Molecular structure processing |
| **httpx** | 0.27.0 | Async HTTP (Open Targets, UniProt) |
| **Pandas** | 2.2.2 | Data manipulation |
| **PyTorch** | 2.2.2 | Deep learning backend |

---

## 🚀 Example Workflow: Type 2 Diabetes

```
User Input: "Type 2 Diabetes"
    ↓
Stage 1: Open Targets finds 10 genes (PPARG, ABCC8, SLC30A8, ...)
    ↓
Stage 2: UniProt enriches with sequences + PDB structures
    ↓
Stage 3: TDC loads 5,000 FDA-approved drugs
    ↓
Stage 4: DeepPurpose predicts 50,000 drug-target pairs
    ↓
Stage 5: Top ranked results:
    1. Drug_123 → PPARG (score: 0.895) 🆕 Potential Discovery
    2. Drug_456 → ABCC8 (score: 0.852) 🆕 Potential Discovery
    3. Metformin → PPARG (score: 0.723) ✅ Known Treatment
    ...
```

---

## ⚙️ Configuration

**File**: `app/core/config.py`

| Setting | Default | Purpose |
|---------|---------|---------|
| `TOP_K_CANDIDATES` | 15 | Results returned per disease |
| `OPEN_TARGETS_API_URL` | https://api.platform.opentargets.org/api/v4/graphql | API endpoint |
| `UNIPROT_API_URL` | https://rest.uniprot.org/uniprotkb/search | Sequence lookup |
| `TDC_DATASET_NAME` | Half_Life_Obach | Drug library source |

---

## 🔍 Error Handling

| Scenario | Response Status | Message |
|----------|-----------------|---------|
| Disease not found | 404 | "No targets found for disease '{name}'" |
| UniProt sequences unavailable | 422 | "Could not retrieve UniProt sequences" |
| TDC dataset unavailable | 503 | "Drug library unavailable" |
| Invalid request | 400 | Validation error details |

---

## 📈 Performance Metrics

| Operation | Time | Notes |
|-----------|------|-------|
| Disease search (Stage 1) | ~1s | API call |
| UniProt enrichment (Stage 2) | ~2–3s | 10 sequential requests |
| Drug library load (Stage 3) | ~5–10s | TDC dataset download |
| AI predictions (Stage 4) | ~1–3 min | Batch processing, GPU if available |
| Total pipeline | **2–5 min** | Per disease |
| Quick lookup (Stages 1–2 only) | **5–10s** | No AI predictions |

---

## 🔐 Security & Best Practices

1. **Input Validation**: All user inputs validated with Pydantic
2. **Async Processing**: Non-blocking API calls using httpx
3. **Error Logging**: Comprehensive logging for debugging
4. **Docker Isolation**: Application runs in isolated container
5. **No Secrets in Code**: Configuration via environment variables

---

## 📚 Data Sources & Attribution

- **Open Targets**: Disease-protein associations (https://www.opentargets.org/)
- **UniProt**: Protein sequences & annotations (https://www.uniprot.org/)
- **PDB**: 3D protein structures (https://www.rcsb.org/)
- **TDC**: Drug library (https://tdcommons.ai/)
- **DeepPurpose**: DTI prediction model (https://github.com/kexinhuang12345/DeepPurpose)

---

## 🛠️ Development & Debugging

### Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run FastAPI server
python main.py

# Visit API docs
http://localhost:8000/docs
```

### Docker Deployment
```bash
docker-compose up --build
```

### Viewing Logs
```bash
docker-compose logs -f drug-repurposing-ai
```

---

**Version**: 1.0  
**Last Updated**: April 2026
