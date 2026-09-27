import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import RAW_DATA_DIR, DOCS_DIR
from modules.graph.engine import GraphIntelligenceEngine
from modules.forensics.engine import DocumentForensicsEngine
from modules.scoring.fusion import compute_combined_risk_score

# Singleton engine instances
graph_engine = GraphIntelligenceEngine()
forensics_engine = DocumentForensicsEngine()

def get_all_entities() -> List[Dict[str, Any]]:
    with open(RAW_DATA_DIR / "entities.json", "r", encoding="utf-8") as f:
        return json.load(f)

def get_entity_by_id(entity_id: str) -> Optional[Dict[str, Any]]:
    entities = get_all_entities()
    for e in entities:
        if e["entity_id"] == entity_id:
            return e
    return None

def analyze_vendor_document(file_path: Path, entity_id: str) -> Dict[str, Any]:
    with open(RAW_DATA_DIR / "transactions.json", "r", encoding="utf-8") as f:
        txns = json.load(f)
    amounts = [t["amount"] for t in txns if t["from_entity"] == entity_id or t["to_entity"] == entity_id]
    
    return forensics_engine.analyze_document(
        file_path=file_path,
        entity_id=entity_id,
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
    
    target_doc = None
    if document_name:
        target_doc = DOCS_DIR / document_name
    else:
        if "CLUSTER-01" in entity_id or "SHELL" in entity_id:
            target_doc = DOCS_DIR / "INV-2026-TAMPERED_tampered.jpg"
            
    if target_doc and target_doc.exists():
        doc_res = analyze_vendor_document(target_doc, entity_id)

    fused = compute_combined_risk_score(doc_res, graph_res)
    fused["original_image"] = doc_res.get("original_image")
    fused["heatmap_image"] = doc_res.get("heatmap_image")
    fused["ela_hotspots"] = doc_res.get("ela_hotspots", [])
    fused["benfords_deviation"] = doc_res.get("benfords_deviation", 0.0)
    
    return fused

def get_vis_graph_data() -> Dict[str, Any]:
    G = graph_engine.G
    clusters = graph_engine.shell_clusters
    
    node_cluster_map = {}
    for cl in clusters:
        for m in cl["members"]:
            node_cluster_map[m] = cl["cluster_id"]

    nodes = []
    for node_id, data in G.nodes(data=True):
        cluster_id = node_cluster_map.get(node_id)
        risk_band = "HIGH" if cluster_id else "LOW"
        nodes.append({
            "id": node_id,
            "label": data.get("name", node_id),
            "risk_band": risk_band,
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