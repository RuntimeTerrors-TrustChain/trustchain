from modules.graph.builder import build_entity_graph
from modules.graph.louvain import detect_shell_clusters
from modules.graph.cycles import detect_circular_invoicing

def test_entity_linkage_shared_director():
    entities = [
        {"entity_id": "V1", "name": "Company A", "director_names": ["Rajesh Kumar"], "registered_address": "Addr 1", "phone": "1", "bank_account": "B1"},
        {"entity_id": "V2", "name": "Company B", "director_names": ["Rajesh Kumar"], "registered_address": "Addr 2", "phone": "2", "bank_account": "B2"},
    ]
    G = build_entity_graph(entities)
    assert G.has_edge("V1", "V2")
    assert G["V1"]["V2"]["shared_field"] == "director"

def test_circular_invoicing_detection():
    txns = [
        {"from_entity": "A", "to_entity": "B", "amount": 100000.0},
        {"from_entity": "B", "to_entity": "C", "amount": 99000.0},
        {"from_entity": "C", "to_entity": "A", "amount": 98000.0},
    ]
    cycles = detect_circular_invoicing(txns)
    assert len(cycles) == 1
    assert cycles[0]["hop_count"] == 3