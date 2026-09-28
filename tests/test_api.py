from backend.main import check_engine, list_entities, get_graph

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