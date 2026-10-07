import networkx as nx
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

Leg = Tuple[float, Optional[datetime]]


def _parse(d) -> Optional[datetime]:
    if not d:
        return None
    try:
        return datetime.fromisoformat(str(d))
    except ValueError:
        return None


def _consistent_legs(
    edges, edge_txns, tol: float, window: timedelta
) -> Optional[List[Leg]]:
    """
    Checks if all legs of a directed cycle carry near-identical amounts (+/-10%)
    within a short time window (30 days), filtering out incidental commercial loops.
    """
    for a0, d0 in edge_txns[edges[0]]:
        legs: List[Leg] = [(a0, d0)]
        for e in edges[1:]:
            cands = [
                (a, d)
                for a, d in edge_txns[e]
                if abs(a - a0) <= tol * a0
                and (d0 is None or d is None or abs(d - d0) <= window)
            ]
            if not cands:
                break
            legs.append(min(cands, key=lambda x: abs(x[0] - a0)))
        else:
            return legs
    return None


def detect_circular_invoicing(
    transactions: List[Dict],
    max_hops: int = 4,
    amount_tolerance: float = 0.10,
    window_days: int = 30,
) -> List[Dict]:
    """
    Finds 3-4 hop payment loops with consistent amount volume across legs inside 30 days.
    """
    DG = nx.DiGraph()
    edge_txns: Dict[Tuple[str, str], List[Leg]] = defaultdict(list)

    for txn in transactions:
        u, v = txn["from_entity"], txn["to_entity"]
        if u == v:
            continue
        edge_txns[(u, v)].append((float(txn["amount"]), _parse(txn.get("date"))))
        DG.add_edge(u, v)

    window = timedelta(days=window_days)
    flagged = []

    for cycle in nx.simple_cycles(DG, length_bound=max_hops):
        if len(cycle) < 3:
            continue
        edges = [(cycle[i], cycle[(i + 1) % len(cycle)]) for i in range(len(cycle))]
        legs = _consistent_legs(edges, edge_txns, amount_tolerance, window)
        if legs is None:
            continue
        flagged.append(
            {
                "path": cycle,
                "hop_count": len(cycle),
                "total_flow": round(sum(a for a, _ in legs), 2),
            }
        )

    flagged.sort(key=lambda c: (c["hop_count"], -c["total_flow"], str(c["path"])))
    return flagged
