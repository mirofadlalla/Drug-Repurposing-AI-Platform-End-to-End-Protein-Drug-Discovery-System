# 🔬 Drug Repurposing AI Platform — End-to-End Protein-Drug Discovery System

## 🧠 Problem Statement

Drug discovery is one of the most expensive and time-consuming processes in the pharmaceutical industry.
Developing a new drug from scratch can take **10–15 years** and cost **billions of dollars**.

Meanwhile:

* Thousands of approved drugs already exist
* Many diseases still lack effective treatments
* Huge biological datasets are underutilized

👉 The challenge:
**How can we reuse existing drugs to treat new diseases efficiently using AI?**

---

## 🚀 Solution Overview

This project is a **Production-Ready AI System for Drug Repurposing** that:

* Takes a **disease name**
* Finds its **most relevant protein targets**
* Retrieves **protein structures (PDB)**
* Uses **AI models** to predict drug–protein interactions
* Ranks **top candidate drugs**

---

## ⚡ Core Features

### ✨ 1. Fast Disease → Protein Lookup (NEW)

* Returns **top 10 protein targets**
* Includes:

  * Protein names
  * Association scores
  * UniProt IDs
  * PDB structure IDs
* ⚡ Response time: **5–10 seconds**

---

### 🤖 2. Full AI Drug Screening Pipeline

* Screens **5000+ approved drugs**
* Generates **50,000+ drug-target predictions**
* Uses **Deep Learning (DeepPurpose)**
* Returns **Top ranked candidates**
* ⏱️ Response time: **2–5 minutes**

---

### 🧪 3. Scientific Data Integration

* Open Targets → Disease–Target associations
* UniProt → Protein sequences + metadata
* PDB → 3D structures
* TDC → Drug datasets
* DeepPurpose → AI predictions

---

## 🔌 API Endpoints

### ⚡ Endpoint 1: Quick Lookup (NEW)

```
GET /api/v1/screen/targets/{disease_name}
```

**Example:**

```bash
curl "http://localhost:8000/api/v1/screen/targets/COVID-19"
```

**Response:**

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
    }
  ]
}
```

---

### 🤖 Endpoint 2: Full AI Screening

```
POST /api/v1/screen/screen
```

**Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/screen/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "disease_name": "Type 2 Diabetes",
    "known_drugs": ["Metformin", "Insulin"],
    "top_k": 15
  }'
```

---

## 🏗️ System Architecture

```
User Input (Disease)
        │
        ▼
Stage 1: Open Targets API
        │
        ▼
Stage 2: UniProt Enrichment
        │
        ├──► (Quick Endpoint returns here ⚡)
        │
        ▼
Stage 3: Drug Library (TDC)
        │
        ▼
Stage 4: AI Model (DeepPurpose)
        │
        ▼
Stage 5: Ranking Engine
        │
        ▼
Final Drug Candidates
```

---

## 🔬 Pipeline Explained

### Stage 1 — Disease → Targets

* Fetch top 10 proteins
* With association scores

### Stage 2 — Protein Enrichment

* Get sequences
* Get UniProt IDs
* Extract PDB structures

👉 Used by quick endpoint

---

### Stage 3 — Drug Library

* Load 5000+ approved drugs

### Stage 4 — AI Predictions

* Evaluate drug–target binding
* ~50,000 combinations

### Stage 5 — Ranking

* Sort by binding score
* Label:

  * Known drugs
  * New discoveries

---

## 🐳 Docker Deployment

### Run the system

```bash
docker-compose up --build
```

### Open API docs

```
http://localhost:8000/docs
```

---

## 🧪 Python Usage

### Quick Lookup

```python
import requests

res = requests.get("http://localhost:8000/api/v1/screen/targets/COVID-19")
data = res.json()

for t in data["targets"]:
    print(t["symbol"], t["pdb_ids"])
```

---

### Full Screening

```python
import requests

payload = {
    "disease_name": "Alzheimer's Disease",
    "top_k": 10
}

res = requests.post(
    "http://localhost:8000/api/v1/screen/screen",
    json=payload,
    timeout=300
)

print(res.json())
```

---

## 📊 Performance

| Operation          | Time        |
| ------------------ | ----------- |
| Disease Lookup     | ~1s         |
| UniProt Enrichment | ~3s         |
| Quick Endpoint     | **5–10s**   |
| Full AI Screening  | **2–5 min** |

---

## 📁 Project Structure

```
app/
 ├── api/
 │   └── endpoints/
 ├── services/
 ├── schemas/
 ├── core/

Docker/
 ├── Dockerfile
 └── docker-compose.yml
```

---

## 📚 Documentation Included

* SYSTEM_DOCUMENTATION.md → Deep architecture
* API_USAGE_GUIDE.md → Examples
* IMPLEMENTATION_SUMMARY.md → Code changes
* CHECKLIST.md → Deployment readiness

---

## 🎯 Use Cases

### 👨‍🔬 Researchers

* Fast protein discovery
* Structural biology workflows

### 🤖 AI Engineers

* Drug-target modeling
* ML pipeline integration

### 💊 Pharma Teams

* Drug repurposing
* Candidate prioritization

---

## 🔥 Key Advantages

* ⚡ Fast + Full modes
* 🧠 AI-powered predictions
* 🧬 Real biological data
* 🧱 Scalable architecture
* 🐳 Dockerized
* ✅ Production-ready

---

## 🚀 Future Improvements

* Caching system
* Batch disease processing
* Visualization (3D proteins)
* Drug interaction data
* Clinical trial integration

---

## ✅ Status

```
✔ Production Ready
✔ No Breaking Changes
✔ Fully Documented
✔ AI Integrated
```

---

## 🎉 Final Note

This is not just an API.
This is a **complete AI-powered drug discovery system** combining:

* Biology
* Data Engineering
* Machine Learning
* Backend Systems

---

## 👨‍💻 Author

**AI Engineer | Backend Developer | Data Scientist**

---

## ⭐ If you like this project

Give it a star ⭐ and feel free to contribute!

---
