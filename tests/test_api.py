import io
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
from fastapi.testclient import TestClient
from backend.main import app, MAX_FILE_SIZE_BYTES
from backend.services import (
    generate_sample_bidding_csv,
    ingest_and_screen_cohort_csv,
    graph_engine,
)

client = TestClient(app)

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


def _bid_nodes():
    return [n for n in graph_engine.G.nodes if str(n).startswith("BID-")]


def test_upload_rejects_bad_extension():
    r = client.post("/analyze-document", files={"file": ("evil.exe", b"x")})
    assert r.status_code == 400


def test_upload_rejects_oversize():
    big = b"0" * (MAX_FILE_SIZE_BYTES + 1)
    r = client.post("/analyze-document", files={"file": ("big.pdf", big)})
    assert r.status_code == 413


def test_upload_is_deleted_after_analysis():
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), "white").save(buf, "PNG")
    before = set(DOCS_DIR.glob("upload_*"))
    r = client.post(
        "/analyze-document", files={"file": ("t.png", buf.getvalue(), "image/png")}
    )
    assert r.status_code == 200
    assert set(DOCS_DIR.glob("upload_*")) == before  # upload and heatmap removed


def test_cohort_rejects_non_csv():
    r = client.post("/ingest-cohort", files={"file": ("x.txt", b"a,b")})
    assert r.status_code == 400


def test_cohort_replaces_previous_upload():
    ingest_and_screen_cohort_csv(generate_sample_bidding_csv())
    ingest_and_screen_cohort_csv(generate_sample_bidding_csv())
    assert len(_bid_nodes()) == 4


def test_bad_upload_keeps_previous_cohort():
    ingest_and_screen_cohort_csv(generate_sample_bidding_csv())
    ingest_and_screen_cohort_csv("")  # empty upload must not wipe the last good cohort
    assert len(_bid_nodes()) == 4

def _sample_tender_id():
    import csv

    rows = list(csv.DictReader(io.StringIO(generate_sample_bidding_csv())))
    return rows[0]["tender_id"]


def test_cohort_response_marks_accepted_and_rejected():
    ok = ingest_and_screen_cohort_csv(generate_sample_bidding_csv())
    assert ok["accepted"] is True
    empty = ingest_and_screen_cohort_csv("")
    assert empty["accepted"] is False


def test_cohort_rejects_missing_columns_and_keeps_previous():
    ingest_and_screen_cohort_csv(generate_sample_bidding_csv())
    res = ingest_and_screen_cohort_csv("a,b,c\n1,2,3\n4,5,6\n")
    assert res["accepted"] is False
    assert "Missing required column" in str(res["syntax_validation_errors"])
    assert len(_bid_nodes()) == 4  # last good cohort untouched


def test_cohort_handles_excel_bom():
    res = ingest_and_screen_cohort_csv("\ufeff" + generate_sample_bidding_csv())
    assert res["accepted"] is True
    assert res["tender_id"] == _sample_tender_id()  # not the silent default


def test_cohort_headers_are_case_insensitive():
    csv_text = generate_sample_bidding_csv()
    header, rest = csv_text.split("\n", 1)
    res = ingest_and_screen_cohort_csv(header.upper() + "\n" + rest)
    assert res["accepted"] is True
    assert res["collusion_detected"] is True


def test_cohort_api_empty_upload_is_flagged_not_clean():
    r = client.post("/ingest-cohort", files={"file": ("e.csv", b"")})
    assert r.status_code == 200
    body = r.json()
    assert body["accepted"] is False
    assert body["collusion_detected"] is False


def test_cohort_api_bom_file_keeps_tender_id():
    data = b"\xef\xbb\xbf" + generate_sample_bidding_csv().encode()
    r = client.post("/ingest-cohort", files={"file": ("bom.csv", data)})
    assert r.json()["tender_id"] == _sample_tender_id()