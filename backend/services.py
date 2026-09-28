import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import RAW_DATA_DIR, DOCS_DIR, DOCUMENTS_MAP_FILE
from modules.graph.engine import GraphIntelligenceEngine
from modules.forensics.engine import DocumentForensicsEngine
from modules.scoring.fusion import compute_combined_risk_score

# Singleton engine instances
graph_engine = GraphIntelligenceEngine()
forensics_engine = DocumentForensicsEngine()

# In-memory cache for node risk bands
_node_risk_cache: Dict[str, str] = {}

def get_all_entities() -> List[Dict[str, Any]]:
    with open(RAW_DATA_DIR / "entities.json", "r", encoding="utf-8") as f:
        return json.load(f)

def get_entity_by_id(entity_id: str) -> Optional[Dict[str, Any]]:
    entities = get_all_entities()
    for e in entities:
        if e["entity_id"] == entity_id:
            return e
    return None

def get_entity_documents(entity_id: str) -> List[Dict[str, Any]]:
    """Reads document mappings from data/raw/documents.json."""
    if not DOCUMENTS_MAP_FILE.exists():
        return []
    with open(DOCUMENTS_MAP_FILE, "r", encoding="utf-8") as f:
        docs = json.load(f)
    return [d for d in docs if d["entity_id"] == entity_id]

def analyze_vendor_document(file_path: Path, entity_id: Optional[str] = None) -> Dict[str, Any]:
    amounts = []
    if entity_id:
        with open(RAW_DATA_DIR / "transactions.json", "r", encoding="utf-8") as f:
            txns = json.load(f)
        amounts = [t["amount"] for t in txns if t["from_entity"] == entity_id or t["to_entity"] == entity_id]
    
    return forensics_engine.analyze_document(
        file_path=file_path,
        entity_id=entity_id or "UNASSIGNED",
        vendor_historical_amounts=amounts
    )

def analyze_vendor_graph(entity_id: str) -> Dict[str, Any]:
    return graph_engine.analyze_entity(entity_id)

def get_full_vendor_risk_assessment(entity_id: str, document_name: Optional[str] = None) -> Dict[str, Any]:
    graph_res = analyze_vendor_graph(entity_id)
    
    doc_res = {
        "document_id": "NONE",
        "entity_id": entity_id,
        "authenticity_score": 0.0,
        "ela_hotspots": [],
        "metadata_flags": [],
        "benfords_deviation": 0.0,
        "original_image": None,
        "heatmap_image": None,
        "reasons": []
    }
    
    # Look up mapped documents for this entity without ID string matching
    mapped_docs = get_entity_documents(entity_id)
    target_doc = None
    if document_name:
        target_doc = DOCS_DIR / document_name
    elif mapped_docs:
        target_doc = DOCS_DIR / mapped_docs[0]["filename"]
            
    if target_doc and target_doc.exists():
        doc_res = analyze_vendor_document(target_doc, entity_id)

    fused = compute_combined_risk_score(doc_res, graph_res)
    fused["original_image"] = doc_res.get("original_image")
    fused["heatmap_image"] = doc_res.get("heatmap_image")
    fused["ela_hotspots"] = doc_res.get("ela_hotspots", [])
    fused["benfords_deviation"] = doc_res.get("benfords_deviation", 0.0)
    
    # Update cache
    _node_risk_cache[entity_id] = fused["risk_band"]
    return fused

def get_vis_graph_data() -> Dict[str, Any]:
    """Prepares node/edge list using real fused risk bands."""
    G = graph_engine.G
    clusters = graph_engine.shell_clusters
    
    node_cluster_map = {}
    for cl in clusters:
        for m in cl["members"]:
            node_cluster_map[m] = cl["cluster_id"]

    nodes = []
    for node_id, data in G.nodes(data=True):
        cluster_id = node_cluster_map.get(node_id)
        # Check cache or evaluate
        if node_id not in _node_risk_cache:
            assessment = get_full_vendor_risk_assessment(node_id)
            _node_risk_cache[node_id] = assessment["risk_band"]
            
        real_band = _node_risk_cache.get(node_id, "LOW")
        nodes.append({
            "id": node_id,
            "label": data.get("name", node_id),
            "risk_band": real_band,
            "group": cluster_id or "CLEAN"
        })

    edges = []
    for u, v, d in G.edges(data=True):
        edges.append({
            "from": u,
            "to": v,
            "label": f"{d.get('shared_field')}: {str(d.get('shared_value'))[:15]}...",
            "edge_type": "shared_attribute"
        })

    return {"nodes": nodes, "edges": edges}