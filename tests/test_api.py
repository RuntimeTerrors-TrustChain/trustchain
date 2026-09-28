import pytest
from fastapi import HTTPException
from backend.main import check_engine, list_entities, get_graph, get_risk_score, get_entity_profile

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