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
    # Leg 3 is wildly different amount (ordinary commerce, not a laundering loop)
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


def test_sliding_window_structuring_straddles_calendar_boundary():
    # Day 0 advances bin; Days 6, 7, 8 straddle across a 7-day calendar bin edge
    base = datetime(2026, 1, 1, 10, 0, 0)
    txns = [
        {
            "from_entity": "OTHER",
            "to_entity": "R1",
            "amount": 48000.0,
            "date": str(base),
        },  # day 0
        {
            "from_entity": "SENDER1",
            "to_entity": "R1",
            "amount": 48500.0,
            "date": str(base + timedelta(days=6)),
        },  # day 6
        {
            "from_entity": "SENDER1",
            "to_entity": "R1",
            "amount": 49000.0,
            "date": str(base + timedelta(days=7)),
        },  # day 7
        {
            "from_entity": "SENDER1",
            "to_entity": "R1",
            "amount": 49500.0,
            "date": str(base + timedelta(days=8)),
        },  # day 8
    ]
    # Fixed 7D grouper sees SENDER1 with count=1 in Bin 1 and count=2 in Bin 2 -> 0 alerts (MISSED FRAUD).
    # True two-pointer sliding window sees Day 6 to Day 8 (span = 2 days <= 7 days) with count=3 -> 1 ALERT (CAUGHT FRAUD).
    struct = detect_structuring(txns, window_days=7)
    sender1_alerts = [s for s in struct if s["entity_id"] == "SENDER1"]
    assert len(sender1_alerts) == 1
    assert sender1_alerts[0]["txn_count"] == 3
