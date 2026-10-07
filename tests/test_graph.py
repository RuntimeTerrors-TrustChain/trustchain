from datetime import datetime, timedelta
from modules.graph.builder import build_entity_graph
from modules.graph.louvain import detect_shell_clusters
from modules.graph.cycles import detect_circular_invoicing
from modules.graph.behavioral import detect_structuring


def test_entity_linkage_shared_director():
    entities = [
        {
            "entity_id": "V1",
            "name": "Company A",
            "director_names": ["Rajesh Kumar"],
            "registered_address": "Addr 1",
            "phone": "1",
            "bank_account": "B1",
        },
        {
            "entity_id": "V2",
            "name": "Company B",
            "director_names": ["Rajesh Kumar"],
            "registered_address": "Addr 2",
            "phone": "2",
            "bank_account": "B2",
        },
    ]
    G = build_entity_graph(entities)
    assert G.has_edge("V1", "V2")
    assert G["V1"]["V2"]["shared_field"] == "director"


def test_circular_invoicing_consistent_legs():
    base = datetime(2026, 1, 15, 10, 0, 0)
    txns = [
        {"from_entity": "A", "to_entity": "B", "amount": 100000.0, "date": str(base)},
        {
            "from_entity": "B",
            "to_entity": "C",
            "amount": 99000.0,
            "date": str(base + timedelta(days=2)),
        },
        {
            "from_entity": "C",
            "to_entity": "A",
            "amount": 98000.0,
            "date": str(base + timedelta(days=4)),
        },
    ]
    cycles = detect_circular_invoicing(txns)
    assert len(cycles) == 1
    assert cycles[0]["hop_count"] == 3


def test_circular_invoicing_inconsistent_amount_filtered():
    base = datetime(2026, 1, 15, 10, 0, 0)
    # Leg 3 is wildly different amount (ordinary trade, not laundering loop)
    txns = [
        {"from_entity": "A", "to_entity": "B", "amount": 100000.0, "date": str(base)},
        {
            "from_entity": "B",
            "to_entity": "C",
            "amount": 99000.0,
            "date": str(base + timedelta(days=2)),
        },
        {
            "from_entity": "C",
            "to_entity": "A",
            "amount": 1000.0,
            "date": str(base + timedelta(days=4)),
        },
    ]
    cycles = detect_circular_invoicing(txns)
    assert len(cycles) == 0


def test_sliding_window_structuring():
    base = datetime(2026, 1, 15, 10, 0, 0)
    # 3 txns across 3 days in the ₹47,500 - ₹49,999 band
    txns = [
        {"from_entity": "S1", "to_entity": "R1", "amount": 48500.0, "date": str(base)},
        {
            "from_entity": "S1",
            "to_entity": "R1",
            "amount": 49200.0,
            "date": str(base + timedelta(days=2)),
        },
        {
            "from_entity": "S1",
            "to_entity": "R1",
            "amount": 49000.0,
            "date": str(base + timedelta(days=4)),
        },
    ]
    struct = detect_structuring(txns)
    assert len(struct) == 1
    assert struct[0]["txn_count"] == 3
