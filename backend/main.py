import uuid
import shutil
import warnings
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response

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
    get_entity_documents,
    analyze_vendor_document,
    analyze_vendor_graph,
    get_full_vendor_risk_assessment,
    get_vis_graph_data,
    generate_audit_dossier_pdf,
    generate_sample_bidding_csv,
    ingest_and_screen_cohort_csv,
)

app = FastAPI(
    title="TrustChain Core Engine Gate",
    description="Procurement & Vendor Fraud Verification System API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


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
        raise HTTPException(
            status_code=404, detail=f"Entity '{entity_id}' not found in registry"
        )
    return entity


@app.get("/entities/{entity_id}/documents")
def list_entity_documents(entity_id: str):
    entity = get_entity_by_id(entity_id)
    if not entity:
        raise HTTPException(
            status_code=404, detail=f"Entity '{entity_id}' not found in registry"
        )
    return get_entity_documents(entity_id)


# --- 2. Layer A: Document Forensics ---
@app.post("/analyze-document")
async def upload_and_analyze_document(
    entity_id: Optional[str] = Query(None, description="Optional associated vendor ID"),
    file: UploadFile = File(...),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {ALLOWED_UPLOAD_EXTENSIONS}",
        )

    safe_name = f"upload_{uuid.uuid4().hex[:12]}{suffix}"
    temp_path = DOCS_DIR / safe_name
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = analyze_vendor_document(temp_path, entity_id)
    return result


# --- 3. Layer B: Graph Intelligence ---
@app.get("/analyze-entity/{entity_id}", response_model=GraphAnalysisResponse)
def analyze_entity(entity_id: str):
    entity = get_entity_by_id(entity_id)
    if not entity:
        raise HTTPException(
            status_code=404, detail=f"Entity '{entity_id}' not found in registry"
        )
    return analyze_vendor_graph(entity_id)


# --- 4. Layer C: Combined Risk Score Fusion ---
@app.get("/risk-score/{entity_id}")
def get_risk_score(entity_id: str, doc_name: Optional[str] = None):
    entity = get_entity_by_id(entity_id)
    if not entity:
        raise HTTPException(
            status_code=404, detail=f"Entity '{entity_id}' not found in registry"
        )
    return get_full_vendor_risk_assessment(entity_id, doc_name)


# --- 5. Export / View Official PDF Dossier (Inline Mode) ---
@app.get("/export-dossier/{entity_id}")
def export_dossier(entity_id: str):
    entity = get_entity_by_id(entity_id)
    if not entity:
        raise HTTPException(
            status_code=404, detail=f"Entity '{entity_id}' not found in registry"
        )
    pdf_path = generate_audit_dossier_pdf(entity_id)
    return FileResponse(
        pdf_path, media_type="application/pdf", content_disposition_type="inline"
    )


# --- 6. Cohort Ingestion Endpoints ---
@app.get("/sample-cohort-csv")
def get_sample_csv():
    """Provides a downloadable sample tender bidding CSV file with a planted collusion ring."""
    csv_data = generate_sample_bidding_csv()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_tender_bids.csv"},
    )


@app.post("/ingest-cohort")
async def ingest_cohort(file: UploadFile = File(...)):
    """Ingests custom CSV tender bidding sheets and runs in-memory collusion screening."""
    content = await file.read()
    csv_str = content.decode("utf-8", errors="ignore")
    result = ingest_and_screen_cohort_csv(csv_str)
    return result


# --- 7. Frontend Interactive Network Graph ---
@app.get("/graph", response_model=GraphVisualizationResponse)
def get_graph():
    return get_vis_graph_data()


# --- 8. Static Media Mounts ---
app.mount("/docs-media", StaticFiles(directory=DOCS_DIR), name="docs-media")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
