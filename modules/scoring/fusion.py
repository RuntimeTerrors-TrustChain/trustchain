from typing import Dict, Any, List
from config import (
    WEIGHT_DOCUMENT,
    WEIGHT_GRAPH,
    ESCALATION_CLUSTER_AND_TAMPER,
    ESCALATION_CYCLE_AND_METADATA,
    SCORE_BAND_HIGH,
    SCORE_BAND_MEDIUM,
)

def compute_combined_risk_score(doc_result: Dict[str, Any], graph_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fuses Document Forensics (Layer A) and Graph Intelligence (Layer B)
    using transparent rule-escalation logic.
    """
    doc_score = float(doc_result.get("authenticity_score", 0.0))
    graph_score = float(graph_result.get("graph_risk_score", 0.0))

    # 1. Base Weighted Score
    base_score = (WEIGHT_DOCUMENT * doc_score) + (WEIGHT_GRAPH * graph_score)
    escalation = 0.0
    escalation_reasons: List[str] = []

    # Escalation Rule 1: Tampered Document + Belongs to Shell Cluster
    has_tamper = doc_score >= 40.0 or len(doc_result.get("ela_hotspots", [])) > 0
    in_shell_cluster = (graph_result.get("cluster_size", 1) > 1) or (graph_result.get("cluster_density", 0.0) >= 0.5)

    if has_tamper and in_shell_cluster:
        escalation += ESCALATION_CLUSTER_AND_TAMPER
        escalation_reasons.append(
            "🚨 CRITICAL ESCALATION: Tampered document detected AND entity belongs to a linked shell cluster "
            "— combined fraud signal indicates organized bidding fraud."
        )

    # Escalation Rule 2: Inconsistency + Circular Fund Routing
    has_meta_or_ela = len(doc_result.get("metadata_flags", [])) > 0 or len(doc_result.get("ela_hotspots", [])) > 0
    has_cycles = len(graph_result.get("cycles_involved", [])) > 0

    if has_meta_or_ela and has_cycles:
        escalation += ESCALATION_CYCLE_AND_METADATA
        escalation_reasons.append(
            "⚠️ CROSS-LAYER FLAG: Document forensic anomalies coincide with active circular fund routing involving this entity."
        )

    # Final Fused Score
    final_score = min(100.0, base_score + escalation)

    # Risk Band Determination
    if final_score >= SCORE_BAND_HIGH:
        risk_band = "HIGH"
    elif final_score >= SCORE_BAND_MEDIUM:
        risk_band = "MEDIUM"
    else:
        risk_band = "LOW"

    # Combine all explainable reasons cleanly
    all_reasons = (
        doc_result.get("reasons", [])
        + graph_result.get("reasons", [])
        + escalation_reasons
    )

    return {
        "entity_id": doc_result.get("entity_id") or graph_result.get("entity_id", "UNKNOWN"),
        "final_risk_score": round(final_score, 1),
        "risk_band": risk_band,
        "base_score": round(base_score, 1),
        "escalation_applied": round(escalation, 1),
        "reasons": all_reasons
    }