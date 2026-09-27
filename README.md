
---

```markdown
# 🛡️ TrustChain — Procurement & Vendor Fraud Verification System

> **Document forensics + entity-network intelligence, fused into one explainable risk score.**

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Headless-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.2.1-blue?style=for-the-badge)](https://networkx.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

## 📌 Executive Summary

Procurement and vendor fraud (government tenders, corporate onboarding, grant disbursements) typically operates on two simultaneous layers that existing tools fail to cross-reference:
1. **Document-Level Fraud:** Forged invoices, tampered billing amounts, pasted signatures, and manipulated PDF creation metadata.
2. **Network-Level Fraud (Collusion & Shell Rings):** Multiple "independent" bidding companies that secretly share directors, registered office addresses, phone numbers, or bank accounts to rig competitive tender prices and launder funds through circular invoicing.

**TrustChain** solves this by fusing **physical document forensics** with **graph-theoretic network intelligence** using a transparent, rule-escalation model. Every fraud flag is 100% explainable and defensible in an audit room or court of law.

---

## 🏛️ System Architecture

```
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
                                 │ • 50/50 Baseline Weighting  │
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

## 🚀 Key Features

### 🔍 Layer A — Document Forensics Engine
* **Error Level Analysis (ELA):** Exploits JPEG Discrete Cosine Transform (DCT) quantization differences. When a fraudster splices a modified number into an invoice, the compression error gradient breaks.
* **OpenCV Automated Bounding Boxes:** Converts amplified difference maps to grayscale, calculates the 85th percentile noise cutoff, and uses `cv2.findContours` to draw red bounding boxes around tampered zones.
* **PDF Stream & Metadata Auditing:** Extracts `/Producer`, `/Creator`, `/CreationDate`, and `/ModDate` via `pypdf` to flag Photoshop/Canva usage and post-creation edits.
* **Benford's Law First-Digit Analysis:** Measures Chi-Square ($\chi^2$) deviation against the natural logarithmic curve $P(d) = \log_{10}(1 + 1/d)$ across a vendor's historical invoices to catch fabricated amounts.

### 🕸️ Layer B — Entity Relationship Graph Engine
* **Fuzzy Identity Resolution:** Combines inverted index lookup tables with `RapidFuzz` token sorting ($>90\%$ similarity threshold) to connect entities across misspelled names and addresses.
* **Louvain Community Detection:** Greedily optimizes graph modularity ($Q$) to isolate dense sub-networks ($D \ge 0.5$, size $\le 8$) representing shell company rings.
* **Directed Circular Invoicing Detection:** Runs Johnson’s elementary cycle algorithm on directed financial graphs to expose 3-hop and 4-hop fund round-tripping ($A \to B \to C \to A$).
* **AML Structuring Detection:** Uses rolling 7-day Pandas time-window aggregations to flag vendors issuing $\ge 3$ transactions inside the $[₹49,000, ₹49,999]$ regulatory avoidance band.

### ⚡ Layer C — Multi-Signal Risk Fusion Engine
* **Transparent Rule Escalation:** Avoids unexplainable machine learning black boxes.
* **Compounding Risk Escalations:** Adds $+20$ points when document tampering coincides with shell cluster membership, and $+15$ points when circular fund loops coincide with forensic anomalies.
* **3-Tier Actionable Risk Bands:**
  * **$0.0 - 39.9 \implies$ LOW RISK (Green):** Automated tender clearance.
  * **$40.0 - 69.9 \implies$ MEDIUM RISK (Yellow):** Secondary human auditor review.
  * **$70.0 - 100.0 \implies$ HIGH RISK (Red):** Immediate disbursement hold & mandatory investigation.

---

## 📊 Benchmark & Accuracy Results

Evaluated against a blind ground-truth dataset generated by our localized Indian commerce generator (`data/ground_truth.json`):

```text
=================================================================
📊 TRUSTCHAIN BENCHMARK EVALUATION RESULTS
=================================================================
Total Registry Entities             : 132
Planted Fraud Entities (Shell Rings): 12
Legitimate Clean Entities           : 120
-----------------------------------------------------------------
True Positives  (Fraud Caught)      : 12 / 12
False Positives (False Alarms)      : 0 / 120
True Negatives  (Clean Cleared)     : 120 / 120
False Negatives (Fraud Missed)      : 0 / 12
-----------------------------------------------------------------
🎯 OVERALL ACCURACY                 : 100.00%
🔍 RECALL (Fraud Coverage)          : 100.00%
⚖️  PRECISION (Alert Reliability)    : 100.00%
🏆 F1-SCORE                         : 100.00%
=================================================================
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend API** | FastAPI, Uvicorn, Pydantic | Asynchronous REST endpoints, Swagger documentation, data contracts |
| **Document Forensics** | Pillow, OpenCV (`cv2`), pypdf | JPEG error level re-compression, contour detection, thermal colormaps |
| **Graph Intelligence** | NetworkX, RapidFuzz | Undirected attribute linkage, Louvain clustering, Johnson cycle search |
| **Data Science & AML** | NumPy, Pandas | Log-normal pricing math, 7-day rolling window time-series grouping |
| **Synthetic Generator** | Faker (`en_IN`), ReportLab | Indian registry simulation, injected shell cartels, automated PDF factory |
| **Frontend UI** | HTML5, CSS Grid, Vanilla JS, vis.js | Zero-build dark mode SPA, Barnes-Hut physics graph, ELA modal viewer |

---

## 📂 Project Structure

```text
trustchain/
├── config.py                 # Central control room: weights, paths, and thresholds
├── requirements.txt          # Frozen dependency manifest
├── eval_benchmark.py         # Precision/Recall benchmark evaluation suite
│
├── data/
│   ├── raw/                  # Generated JSON databases (entities.json, transactions.json)
│   ├── documents/            # Generated invoice PDFs and JPEG test files
│   └── ground_truth.json     # Hidden validation ground truth
│
├── modules/
│   ├── forensics/            # Layer A: ELA, metadata, Benford's Law, and orchestrator
│   ├── graph/                # Layer B: Graph builder, Louvain, cycles, structuring
│   └── scoring/              # Layer C: Multi-signal risk fusion and reason compiler
│
├── generator/                # Synthetic data generator (entities, transactions, PDF factory)
│
├── backend/                  # FastAPI web server, Pydantic schemas, and services
│
└── frontend/                 # Zero-build dashboard (index.html, style.css, graph.js, app.js)
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
# 1. Generate companies, transactions, and injected shell rings
python -m generator.run_generator

# 2. Compile clean PDFs and tampered test invoices
python -m generator.pdf_factory
```

### 5. Start the FastAPI Server
```bash
uvicorn backend.main:app --reload --port 8000
```

### 6. Open the Dashboard
Navigate to **`http://127.0.0.1:8000/`** in your browser to interact with the live dashboard.  
Visit **`http://127.0.0.1:8000/docs`** for the interactive Swagger API docs.

---

## 🧪 Running the Benchmark Evaluation

To independently verify the system against the blind ground-truth dataset:

```bash
python eval_benchmark.py
```

---

## 🔌 API Reference

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/entities` | `GET` | Returns list of all registered vendor entities |
| `/entities/{entity_id}` | `GET` | Returns full profile of a single vendor |
| `/analyze-document` | `POST` | Upload an invoice (PDF/JPEG) to run Layer A forensics |
| `/analyze-entity/{id}` | `GET` | Run Layer B graph intelligence on a specific company |
| `/risk-score/{id}` | `GET` | Returns the complete fused risk score and reason dossier |
| `/graph` | `GET` | Returns nodes and edges formatted for `vis-network` |

---

## 🎯 4-Minute Presentation Sequence

1. **Clean Vendor Demo (`0:30`):** Click a green node (`Shanker LLC`). Point out that independent companies with natural Benford curves score **0.0 (LOW RISK)**.
2. **Document Forensics Demo (`1:15`):** Click **"🔬 Inspect Document ELA Heatmap"**. Show the original invoice alongside the OpenCV thermal diff highlighting the spliced ₹98.5L amount in a red box.
3. **Graph & Multi-Signal Climax (`2:15`):** Click `VEND-SHELL-CLUSTER-01-1`. Show the physics graph isolating the 4-company shell ring (density 1.0) and the 3-hop ₹10.39L circular invoice loop. Show the final score hitting **100.0 (HIGH RISK)** with full plain-English audit reasoning.
4. **Hard Numbers (`3:15`):** Present the 100% recall and 0% false-positive confusion matrix from `eval_benchmark.py`.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
```