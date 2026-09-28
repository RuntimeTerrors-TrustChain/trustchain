from modules.scoring.fusion import compute_combined_risk_score

def test_fusion_clean_vendor():
    doc = {"document_id": "DOC-CLEAN", "authenticity_score": 0.0, "ela_hotspots": [], "metadata_flags": [], "reasons": []}
    graph = {"graph_risk_score": 0.0, "cluster_size": 1, "cluster_density": 0.0, "cycles_involved": [], "reasons": []}
    res = compute_combined_risk_score(doc, graph)
    assert res["risk_band"] == "LOW"
    assert res["final_risk_score"] < 40.0

def test_fusion_tampered_doc_alone():
    doc = {"document_id": "DOC-TAMPER", "authenticity_score": 50.0, "ela_hotspots": [{"intensity": 0.8}], "metadata_flags": [], "reasons": []}
    graph = {"graph_risk_score": 0.0, "cluster_size": 1, "cluster_density": 0.0, "cycles_involved": [], "reasons": []}
    res = compute_combined_risk_score(doc, graph)
    assert res["risk_band"] == "MEDIUM"
    assert res["final_risk_score"] >= 40.0

def test_fusion_cluster_plus_tamper_escalation():
    doc = {"document_id": "DOC-TAMPER", "authenticity_score": 50.0, "ela_hotspots": [{"intensity": 0.8}], "metadata_flags": [], "reasons": []}
    graph = {"graph_risk_score": 75.0, "cluster_size": 4, "cluster_density": 1.0, "cycles_involved": [], "reasons": []}
    res = compute_combined_risk_score(doc, graph)
    assert res["risk_band"] == "HIGH"
    assert res["final_risk_score"] >= 70.0
    assert any("CRITICAL ESCALATION" in r for r in res["reasons"])