import pytest
from fastapi import HTTPException
from backend.main import (
    check_engine,
    list_entities,
    get_graph,
    get_risk_score,
    get_entity_profile,
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


def test_risk_score_path_traversal_guard():
    # Pass path traversal payload in doc_name
    res = get_risk_score("VEND-2824", doc_name="../../etc/passwd")
    assert res["final_risk_score"] < 40.0


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
