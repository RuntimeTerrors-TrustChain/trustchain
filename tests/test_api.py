import pytest
from pathlib import Path
from PIL import Image
from fastapi import HTTPException
from config import DOCS_DIR
from backend.main import (
    check_engine, 
    list_entities, 
    get_graph, 
    get_risk_score, 
    get_entity_profile
)
from backend.services import generate_sample_bidding_csv, ingest_and_screen_cohort_csv

def test_health_endpoint():
    res = check_engine()
    assert res["status"] == "TrustChain Core Infrastructure Engine Running"

def test_get_entities():
    res = list_entities()
    assert isinstance(res, list)
    assert len(res) > 0

def test_get_graph():
    res = get_graph()
    assert "nodes" in res and "edges" in res

def test_risk_score_404_on_nonexistent_entity():
    with pytest.raises(HTTPException) as exc_info:
        get_risk_score("VEND-NONEXISTENT-9999")
    assert exc_info.value.status_code == 404
    assert "not found in registry" in exc_info.value.detail

def test_entity_profile_404_on_nonexistent_entity():
    with pytest.raises(HTTPException) as exc_info:
        get_entity_profile("VEND-NONEXISTENT-9999")
    assert exc_info.value.status_code == 404

def test_risk_score_path_traversal_blocked():
    # Place a real probe.png in data/ (directly outside data/documents/)
    probe_file = DOCS_DIR.parent / "probe.png"
    Image.new("RGB", (100, 100), "white").save(probe_file)
    
    try:
        all_ents = list_entities()
        valid_id = all_ents[0]["entity_id"] if isinstance(all_ents[0], dict) else all_ents[0].entity_id
        
        # Request with path traversal ../probe.png
        res = get_risk_score(valid_id, doc_name="../probe.png")
        
        # Guard must prevent loading the outside file
        assert res.get("heatmap_image") is None
        assert res.get("authenticity_score", 0.0) == 0.0
    finally:
        probe_file.unlink(missing_ok=True)

def test_sample_cohort_csv():
    csv_data = generate_sample_bidding_csv()
    assert "GEM/2026/B/8941" in csv_data
    assert "Rajesh Kumar Sharma" in csv_data

def test_ingest_cohort_collusion_detection():
    csv_data = generate_sample_bidding_csv()
    res = ingest_and_screen_cohort_csv(csv_data)
    assert res["collusion_detected"] is True
    assert len(res["collusion_flags"]) > 0
    assert any(f["shared_attribute"] == "Director DIN" for f in res["collusion_flags"])

def test_ingest_cohort_row_cap_enforced():
    # Exceeding MAX_COHORT_ROWS (100) returns rejection
    header = "tender_id,company_name,cin_llpin,director_names,director_dins,registered_address,gstin,bank_account,quoted_amount_inr\n"
    rows = "\n".join([f"T1,Co{i},CIN{i},Dir{i},DIN{i},Addr{i},07A{i:04d}0000A1Z5,B{i},1000" for i in range(105)])
    res = ingest_and_screen_cohort_csv(header + rows)
    assert "Row limit exceeded" in str(res.get("syntax_validation_errors", []))