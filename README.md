
---

# 🛡️ TrustChain — Procurement & Vendor Fraud Verification System

> **Document forensics + entity-network intelligence, fused into one explainable risk score.**

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Headless-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.2.1-blue?style=for-the-badge)](https://networkx.org/)
[![Pytest](https://img.shields.io/badge/Pytest-Passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

## 📌 Executive Summary

Procurement and vendor fraud (government tenders, corporate vendor onboarding, subsidy disbursements) operates on two simultaneous layers that existing anti-fraud tools fail to cross-reference:

1. **Document-Level Fraud:** Forged tax certificates, tampered invoice amounts, copy-pasted signatures, and manipulated PDF byte streams.
2. **Network-Level Fraud (Collusion & Shell Rings):** Multiple "independent" bidding companies that secretly share directors, registered addresses, phone numbers, or bank accounts to fake competitive bidding, rig tender prices, or launder funds through circular invoicing.

**TrustChain** solves this by fusing **physical document forensics** with **graph-theoretic network intelligence** using a transparent, rule-escalation model. Every fraud flag is 100% auditable and explainable to procurement officers, forensic investigators, and auditors.

---

## 🏛️ System Architecture

```text
                                  TRUSTCHAIN CORE ARCHITECTURE
                                  
 📄 Submitted Invoice (PDF/Image)                     🏢 Company Registry & Transaction Ledger
                │                                                        │
                ▼                                                        ▼
   ┌───────────────────────────┐                            ┌───────────────────────────┐
   │          LAYER A          │                            │          LAYER B          │
   │ Document Forensics Engine │                            │ Graph Intelligence Engine │
   ├───────────────────────────┤                            ├───────────────────────────┤
   │ • Error Level Analysis    │                            │ • Inverted Index Linkage  │
   │ • OpenCV Contour Bboxes   │                            │ • RapidFuzz String Match  │
   │ • PDF Metadata Inspector  │                            │ • Louvain Modularity (Q)  │
   │ • Benford's Law (Chi-Sq)  │                            │ • Elementary Cycles (DFS) │
   └─────────────┬─────────────┘                            │ • AML 7-Day Structuring   │
                 │                                          └─────────────┬─────────────┘
                 │ Authenticity Score (0-100)                             │ Graph Risk Score (0-100)
                 └──────────────────────────────┬─────────────────────────┘
                                                ▼
                                 ┌─────────────────────────────┐
                                 │           LAYER C           │
                                 │     Risk Fusion Engine      │
                                 ├─────────────────────────────┤
                                 │ • Base Weighted Integration │
                                 │ • +25 Pt Shell Ring Rule    │
                                 │ • +20 Pt Shell+Tamper Bonus │
                                 │ • +15 Pt Cycle+Anomaly Bonus│
                                 │ • Plain-English Reason Tree │
                                 └──────────────┬──────────────┘
                                                ▼
                                 ┌─────────────────────────────┐
                                 │     FASTAPI REST API        │
                                 │    (/risk-score, /graph)    │
                                 └──────────────┬──────────────┘
                                                ▼
                                 ┌─────────────────────────────┐
                                 │     DARK DASHBOARD UI       │
                                 │  vis.js Physics Graph View  │
                                 │  Side-by-Side ELA Heatmap   │
                                 └─────────────────────────────┘
```

---

## 🎬 5 Live Demo Scenarios

Our synthetic pipeline deterministically generates entities and mapped documents covering five concrete audit scenarios:

| Scenario | Scenario Name | Physical & Network Evidence | Expected Risk Score |
| :---: | :--- | :--- | :---: |
| **A** | **Clean Control** | Clean PDF invoice, unique director/address, natural Benford curve | **LOW RISK (0.0)** |
| **B** | **Tampered Doc Alone** | Spliced ₹74.2L amount with ELA hotspot, independent entity | **MEDIUM RISK (45.0 - 55.0)** |
| **C** | **Shell Member Alone** | 4-Node Shell Cartel (Density 1.0, shared director & address), no tampered doc | **MEDIUM RISK (50.0 - 62.5)** |
| **D** | **Multi-Signal Climax** | Dense shell cartel + Spliced JPEG invoice (intensity 0.8) | **HIGH RISK (80.0 - 100.0)** |
| **E** | **Circular AML Flow** | 3-Hop circular invoicing + Photoshop PDF metadata discrepancy | **HIGH RISK (75.0 - 90.0)** |

---

## 🚀 Key Features

### 🔍 Layer A — Document Forensics Engine
* **Error Level Analysis (ELA):** Exploits JPEG Discrete Cosine Transform (DCT) quantization differences. Spliced amounts or altered dates compress with a different error rate than the untouched background.
* **OpenCV Automated Bounding Boxes:** Converts amplified difference maps to grayscale, applies an 85th percentile noise cutoff, and uses `cv2.findContours` to draw red bounding boxes around tampered zones.
* **PDF Stream & Metadata Auditing:** Extracts `/Producer`, `/Creator`, `/CreationDate`, and `/ModDate` via `pypdf` to flag Photoshop/Canva usage and post-creation edits.
* **Benford's Law First-Digit Analysis:** Measures Chi-Square (χ²) deviation against the natural logarithmic curve $P(d) = \log_{10}(1 + 1/d)$ across a vendor's historical invoices to catch fabricated amounts.

### 🕸️ Layer B — Entity Relationship Graph Engine
* **Fuzzy Identity Resolution:** Combines inverted index lookup tables with `RapidFuzz` token sorting (>90% similarity threshold) to connect entities across misspelled names and addresses.
* **Louvain Community Detection:** Greedily optimizes graph modularity ($Q$) to isolate dense sub-networks (Density $\ge 0.5$, Size $\le 8$) representing shell company rings.
* **Directed Circular Invoicing Detection:** Runs Johnson’s elementary cycle algorithm on directed financial graphs to expose 3-hop and 4-hop fund round-tripping ($A \to B \to C \to A$).
* **AML Structuring Detection:** Uses rolling 7-day Pandas time-window aggregations to flag vendors issuing $\ge 3$ transactions inside the ₹49,000–₹49,999 regulatory avoidance band.

### ⚡ Layer C — Multi-Signal Risk Fusion Engine
* **Transparent Rule Escalation:** Avoids unexplainable machine learning black boxes. Every risk score is completely traceable to stated rules.
* **Compounding Risk Escalations:** Adds $+20$ points when document tampering coincides with shell cluster membership, and $+15$ points when circular fund loops coincide with forensic anomalies.
* **3-Tier Actionable Risk Bands:**
  * **0.0 – 39.9 → LOW RISK (Green):** Automated tender clearance.
  * **40.0 – 69.9 → MEDIUM RISK (Yellow):** Secondary human auditor review.
  * **70.0 – 100.0 → HIGH RISK (Red):** Immediate disbursement hold & mandatory investigation.

---

## 📊 Benchmark & Accuracy Results

Evaluated on our synthetic commercial dataset with hidden ground truth (`data/ground_truth.json`):

```text
=================================================================
📊 TRUSTCHAIN MULTI-LAYER BENCHMARK EVALUATION RESULTS
=================================================================
1. GRAPH-ONLY ENGINE BENCHMARK:
   TP: 12 | FP: 1 | TN: 118 | FN: 1
   Recall: 92.3% | Precision: 92.3% | F1: 92.3%

2. DOCUMENT-ONLY FORENSICS BENCHMARK:
   TP: 3 | FP: 0 | TN: 119 | FN: 10
   Recall: 23.1% | Precision: 100.0% | F1: 37.5%

3. COMBINED RISK FUSION (LAYER C):
   TP: 13 | FP: 1 | TN: 118 | FN: 0
   🎯 Accuracy : 99.24%
   🔍 Recall   : 100.00% (Catches both document & syndicate fraud)
   ⚖️  Precision: 92.86%
   🏆 F1-Score : 96.30%

4. HELD-OUT TEST CASES (Unseen Seed Evaluation):
   Generalization Recall: 100.0% (4 / 4 unseen shell entities detected)
=================================================================
```
*(Note: Evaluated on deterministically generated synthetic procurement data with planted ground truth. Combined multi-signal fusion outperforms either single layer in isolation).*

---

## ⚠️ Known Limitations & Domain Assumptions

* **Synthetic Data Environment:** Real procurement ledgers and bank records are legally confidential. Real-world deployment requires integration with corporate registry APIs (such as India's MCA21) and core banking transaction streams.
* **Rescanned / Printed Documents:** Error Level Analysis operates on digital JPEG compression gradients. If a forged document is physically printed and scanned on a flatbed scanner, ELA signals degrade; TrustChain mitigates this by pairing ELA with metadata inspection and Benford's Law.
* **Benford's Law Sample Size:** Reliable first-digit frequency analysis requires $\ge 30–50$ line-item transactions per vendor.
* **Illustrative Thresholds:** Regulatory limits (e.g. ₹50,000 PMLA threshold) are configurable constants in `config.py`.

---

## 🛠️ Tech Stack & Requirements

* **Supported Python Versions:** Python 3.10, 3.11, 3.12 (NumPy 1.26 and OpenCV 4.9.0 require Python $\le 3.12$).
* **Core Libraries:** FastAPI, Uvicorn, Pydantic, NetworkX, Pillow, OpenCV-Headless, RapidFuzz, Pandas, NumPy, ReportLab, Faker, Pytest.

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend API** | FastAPI, Uvicorn, Pydantic | Asynchronous REST endpoints, Swagger documentation, data contracts |
| **Document Forensics** | Pillow, OpenCV (`cv2`), pypdf | JPEG error level re-compression, contour detection, thermal colormaps |
| **Graph Intelligence** | NetworkX, RapidFuzz | Undirected attribute linkage, Louvain clustering, Johnson cycle search |
| **Data Science & AML** | NumPy, Pandas | Log-normal pricing math, 7-day rolling window time-series grouping |
| **Synthetic Generator** | Faker (`en_IN`), ReportLab | Indian registry simulation, injected shell cartels, automated PDF factory |
| **Frontend UI** | HTML5, CSS Grid, Vanilla JS, vis.js | Zero-build dark mode SPA, Barnes-Hut physics graph, ELA modal viewer |
| **Testing Suite** | Pytest, FastAPI TestClient | Unit testing for forensics, graph algorithms, fusion, and API endpoints |

---

## 📂 Project Structure

```text
trustchain/
├── config.py                 # Central control room: weights, paths, and thresholds
├── requirements.txt          # Frozen dependency manifest
├── eval_benchmark.py         # Multi-layer benchmark evaluation suite (Graph, Doc, Fusion, Held-Out)
├── LICENSE                   # MIT License
├── README.md                 # System documentation
│
├── data/
│   ├── raw/
│   │   ├── entities.json     # Neutral corporate registry dataset
│   │   ├── transactions.json # Financial ledger with log-normal pricing & cycles
│   │   └── documents.json    # Explicit vendor-to-document mapping file
│   ├── documents/            # Generated invoice PDFs and JPEG test files
│   └── ground_truth.json     # Hidden validation ground truth (shell rings & tampered docs)
│
├── modules/
│   ├── forensics/
│   │   ├── ela.py            # Error Level Analysis, contour extraction, color heatmap
│   │   ├── metadata.py       # PDF metadata & suspicious producer inspector
│   │   ├── benford.py        # Benford's Law Chi-Square distribution analyzer
│   │   └── engine.py         # Layer A Forensics Orchestrator
│   ├── graph/
│   │   ├── builder.py        # Graph construction & RapidFuzz token matching
│   │   ├── louvain.py        # Louvain Community Detection & density scoring
│   │   ├── cycles.py         # Johnson's elementary cycle detection (DiGraph)
│   │   ├── behavioral.py     # Rolling 7-day AML structuring & threshold evasion
│   │   └── engine.py         # Layer B Graph Orchestrator
│   └── scoring/
│       └── fusion.py         # Layer C: Transparent Rule-Escalation Fusion Engine
│
├── generator/
│   ├── entities.py           # Neutral company generator & planted shell cartels
│   ├── transactions.py       # Log-normal payments, circular chains & structuring
│   ├── pdf_factory.py        # Clean/tampered PDF and spliced JPEG invoice factory
│   └── run_generator.py      # Master data generation CLI
│
├── backend/
│   ├── schemas.py            # Pydantic request/response data contracts
│   ├── services.py           # Engine singletons, lazy risk caching & vis-network transformer
│   └── main.py               # FastAPI gateway, CORS middleware & static media server
│
├── frontend/
│   ├── index.html            # 3-column Single Page Application & forensic modal
│   ├── css/
│   │   └── style.css         # Dark theme design system
│   └── js/
│       ├── graph.js          # vis-network physics graph visualization
│       └── app.js            # Live API state management, search, and upload handler
│
└── tests/
    ├── conftest.py           # Pytest path configurations
    ├── test_forensics.py     # Unit tests for ELA, Benford, and metadata
    ├── test_graph.py         # Unit tests for entity linkage and cycle detection
    ├── test_fusion.py        # Unit tests for rule escalations and risk bands
    └── test_api.py           # API integration tests via FastAPI TestClient
```

---

## ⚡ Quickstart Guide

### 1. Clone the Repository
```bash
git clone https://github.com/kovidsharma27/trustchain.git
cd trustchain
```

### 2. Set Up Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (cmd):
venv\Scripts\activate.bat
# Linux / macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Generate Synthetic Data & Test Invoices
```bash
python -m generator.run_generator
```

### 5. Run the Automated Test Suite
```bash
pytest -q
```

### 6. Start the FastAPI Server
```bash
uvicorn backend.main:app --reload --port 8000
```

### 7. Open the Dashboard
* Navigate to **`http://127.0.0.1:8000/`** in your browser to interact with the live dashboard.  
* Visit **`http://127.0.0.1:8000/docs`** for the interactive Swagger API documentation.

---

## 🧪 Running the Benchmark Evaluation

To independently verify the system across Graph-only, Document-only, Combined Fusion, and Held-out cases:

```bash
python eval_benchmark.py
```

---

## 🔌 API Reference

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/entities` | `GET` | Returns list of all registered vendor entities |
| `/entities/{entity_id}` | `GET` | Returns full profile of a single vendor |
| `/entities/{entity_id}/documents` | `GET` | Returns mapped invoices/documents for a specific entity |
| `/analyze-document` | `POST` | Upload an invoice (PDF/JPEG) to run Layer A forensics (`entity_id` is optional) |
| `/analyze-entity/{id}` | `GET` | Run Layer B graph intelligence on a specific company |
| `/risk-score/{id}` | `GET` | Returns the complete fused risk score and reason dossier |
| `/graph` | `GET` | Returns nodes and edges formatted for `vis-network` |

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---
