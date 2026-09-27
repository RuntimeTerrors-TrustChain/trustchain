import networkx as nx
from typing import List, Dict

def detect_circular_invoicing(transactions: List[Dict], max_hops: int = 4) -> List[Dict]:
    """
    Builds a directed financial graph and finds high-confidence tight cycles (3-4 hops).
    Filters out long, noisy incidental loops.
    """
    DG = nx.DiGraph()

    for txn in transactions:
        u = txn["from_entity"]
        v = txn["to_entity"]
        # If multiple transactions exist between same pair, sum them
        if DG.has_edge(u, v):
            DG[u][v]["amount"] += txn["amount"]
        else:
            DG.add_edge(u, v, amount=txn["amount"])

    # Look for tight cycles (3 to 4 hops)
    raw_cycles = list(nx.simple_cycles(DG, length_bound=max_hops))
    flagged_cycles = []

    for cycle in raw_cycles:
        if len(cycle) < 3:
            continue  # Ignore 2-way refunds

        total_flow = sum(
            DG[cycle[i]][cycle[(i + 1) % len(cycle)]]["amount"]
            for i in range(len(cycle))
        )

        flagged_cycles.append({
            "path": cycle,
            "hop_count": len(cycle),
            "total_flow": round(total_flow, 2)
        })

    # Sort cycles by shortest hop first, then highest flow
    flagged_cycles.sort(key=lambda c: (c["hop_count"], -c["total_flow"]))
    return flagged_cycles