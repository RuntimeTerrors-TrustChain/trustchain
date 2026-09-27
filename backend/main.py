import shutil
import warnings
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

warnings.filterwarnings("ignore")

from config import DOCS_DIR
from backend.schemas import (
    EntityBase,
    DocumentForensicsResponse,
    GraphAnalysisResponse,
    GraphVisualizationResponse,
)
from backend.services import (
    get_all_entities,
    get_entity_by_id,
    analyze_vendor_document,
    analyze_vendor_graph,
    get_full_vendor_risk_assessment,
    get_vis_graph_data
)

app = FastAPI(
    title="TrustChain Core Engine Gate",
    description="Procurement & Vendor Fraud Verification System API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def check_engine():
    return {"status": "TrustChain Core Infrastructure Engine Running"}

# --- 1. Entity Registry Endpoints ---
@app.get("/entities", response_model=List[EntityBase])
def list_entities():
    return get_all_entities()

@app.get("/entities/{entity_id}", response_model=EntityBase)
def get_entity_profile(entity_id: str):
    entity = get_entity_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity

# --- 2. Layer A: Document Forensics ---
@app.post("/analyze-document")
async def upload_and_analyze_document(
    entity_id: str = Query(...),
    file: UploadFile = File(...)
):
    temp_path = DOCS_DIR / f"upload_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    result = analyze_vendor_document(temp_path, entity_id)
    return result

# --- 3. Layer B: Graph Intelligence ---
@app.get("/analyze-entity/{entity_id}", response_model=GraphAnalysisResponse)
def analyze_entity(entity_id: str):
    return analyze_vendor_graph(entity_id)

# --- 4. Layer C: Combined Risk Score Fusion ---
@app.get("/risk-score/{entity_id}")
def get_risk_score(entity_id: str, doc_name: Optional[str] = None):
    return get_full_vendor_risk_assessment(entity_id, doc_name)

# --- 5. Frontend Interactive Network Graph ---
@app.get("/graph", response_model=GraphVisualizationResponse)
def get_graph():
    return get_vis_graph_data()

# --- 6. Mount Document Images Media Route ---
app.mount("/docs-media", StaticFiles(directory=DOCS_DIR), name="docs-media")

# --- 7. Mount Static Frontend (MUST BE LAST) ---
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")