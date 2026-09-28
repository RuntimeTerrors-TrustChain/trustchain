import json
from typing import Dict
from config import RAW_DATA_DIR
from modules.graph.builder import build_entity_graph
from modules.graph.louvain import detect_shell_clusters
from modules.graph.cycles import detect_circular_invoicing
from modules.graph.behavioral import detect_structuring

class GraphIntelligenceEngine:
    def __init__(self):
        with open(RAW_DATA_DIR / "entities.json", "r", encoding="utf-8") as f:
            self.entities = json.load(f)
        with open(RAW_DATA_DIR / "transactions.json", "r", encoding="utf-8") as f:
            self.transactions = json.load(f)

        self.G = build_entity_graph(self.entities)
        self.shell_clusters = detect_shell_clusters(self.G)
        self.circular_cycles = detect_circular_invoicing(self.transactions, max_hops=4)
        self.structuring_events = detect_structuring(self.transactions)

    def analyze_entity(self, entity_id: str) -> Dict:
        score = 0.0
        reasons = []
        
        # 1. Shell Cluster Check (40.0 pts)
        entity_cluster = None
        for cluster in self.shell_clusters:
            if entity_id in cluster["members"]:
                entity_cluster = cluster
                score += 40.0
                reasons.append(
                    f"Part of a {cluster['size']}-entity cluster '{cluster['cluster_id']}' "
                    f"with high edge density ({cluster['density']}) sharing directors/registered address"
                )
                break

        # 2. Circular Invoicing (30.0 pts)
        entity_cycles = [c for c in self.circular_cycles if entity_id in c["path"]]
        if entity_cycles:
            score += 30.0
            primary_cycle = entity_cycles[0]
            reasons.append(
                f"Involved in primary {primary_cycle['hop_count']}-hop circular transaction ring totaling ₹{primary_cycle['total_flow']:,.2f}"
            )
            if len(entity_cycles) > 1:
                total_cycle_volume = sum(c["total_flow"] for c in entity_cycles)
                reasons.append(
                    f"Detected {len(entity_cycles)} linked circular flow paths with cumulative volume of ₹{total_cycle_volume:,.2f}"
                )

        # 3. Structuring Check (25.0 pts)
        is_structuring = any(s["entity_id"] == entity_id for s in self.structuring_events)
        if is_structuring:
            score += 25.0
            reasons.append("Structuring detected: Multiple transactions placed just under ₹50,000 threshold within a 7-day window")

        graph_risk_score = min(100.0, score)

        return {
            "entity_id": entity_id,
            "cluster_id": entity_cluster["cluster_id"] if entity_cluster else None,
            "cluster_density": entity_cluster["density"] if entity_cluster else 0.0,
            "cluster_size": entity_cluster["size"] if entity_cluster else 1,
            "shared_links": entity_cluster["shared_links"] if entity_cluster else [],
            "cycles_involved": entity_cycles[:3],
            "structuring_flag": is_structuring,
            "fan_pattern_flag": len(entity_cycles) > 0,
            "graph_risk_score": round(graph_risk_score, 1),
            "reasons": reasons
        }