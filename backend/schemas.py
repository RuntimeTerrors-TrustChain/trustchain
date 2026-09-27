from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# --- Entity Models ---
class EntityBase(BaseModel):
    entity_id: str
    name: str
    director_names: List[str]
    registered_address: str
    phone: str
    bank_account: str
    registration_date: Optional[str] = None

# --- Layer A: Document Forensics Contract (Section 3.4) ---
class ELAHotspot(BaseModel):
    bbox: List[int] = Field(..., description="[ymin, xmin, ymax, xmax]")
    intensity: float

class DocumentForensicsResponse(BaseModel):
    document_id: str
    entity_id: str
    authenticity_score: float = Field(..., description="0-100, higher = more suspicious")
    ela_hotspots: List[ELAHotspot] = []
    metadata_flags: List[str] = []
    benfords_deviation: float = Field(..., description="Vendor-level leading digit deviation")
    reasons: List[str] = []

# --- Layer B: Graph Intelligence Contract (Section 4.7) ---
class CycleInfo(BaseModel):
    path: List[str]
    total_flow: float
    hop_count: int

class GraphAnalysisResponse(BaseModel):
    entity_id: str
    cluster_id: Optional[str] = None
    cluster_density: float = 0.0
    cluster_size: int = 1
    shared_links: List[List[str]] = []
    cycles_involved: List[CycleInfo] = []
    structuring_flag: bool = False
    fan_pattern_flag: bool = False
    graph_risk_score: float = Field(..., description="0-100, higher = more suspicious")
    reasons: List[str] = []

# --- Layer C: Combined Risk Score Contract (Section 5.1) ---
class RiskScoreResponse(BaseModel):
    entity_id: str
    final_risk_score: float = Field(..., description="0-100 fused risk score")
    risk_band: str = Field(..., description="HIGH, MEDIUM, or LOW")
    base_score: float
    escalation_applied: float
    reasons: List[str]

# --- Frontend Graph Contract ---
class GraphNode(BaseModel):
    id: str
    label: str
    risk_band: str = "LOW"
    group: Optional[str] = None

class GraphEdge(BaseModel):
    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    label: str
    edge_type: str = "shared_attribute"  # or 'transaction'

class GraphVisualizationResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]