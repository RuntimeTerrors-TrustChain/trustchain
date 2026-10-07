import pytest
from pathlib import Path
from PIL import Image
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


def test_entity_profile_404_on_nonexistent_entity():
    with pytest.raises(HTTPException) as exc_info:
        get_entity_profile("VEND-NONEXISTENT-9999")
    assert exc_info.value.status_code == 404


def test_risk_score_path_traversal_blocked(tmp_path):
    # Create an actual image file outside DOCS_DIR
    outside_dir = tmp_path / "secret_folder"
    outside_dir.mkdir()
    outside_img = outside_dir / "secret.png"
    Image.new("RGB", (100, 100), "white").save(outside_img)

    # Request it with path traversal payload
    all_ents = list_entities()
    valid_id = (
        all_ents[0]["entity_id"]
        if isinstance(all_ents[0], dict)
        else all_ents[0].entity_id
    )
    res = get_risk_score(valid_id, doc_name=f"../../{outside_img.name}")

    # Assert path traversal is blocked (document not loaded)
    assert res.get("heatmap_image") is None
    assert res.get("authenticity_score", 0.0) == 0.0


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
