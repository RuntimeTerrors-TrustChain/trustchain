import json
from config import RAW_DATA_DIR, GROUND_TRUTH_FILE
from backend.services import (
    analyze_vendor_graph,
    get_full_vendor_risk_assessment,
    get_entity_documents,
    analyze_vendor_document,
    DOCS_DIR
)

def compute_metrics(tp: int, fp: int, tn: int, fn: int):
    precision = (tp / (tp + fp)) * 100 if (tp + fp) > 0 else 0.0
    recall = (tp / (tp + fn)) * 100 if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    total = tp + fp + tn + fn
    accuracy = ((tp + tn) / total) * 100 if total > 0 else 0.0
    return {"accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1}

def run_benchmark():
    print("=" * 65)
    print("🛡️  TRUSTCHAIN AUDIT & BENCHMARK EVALUATION SUITE")
    print("=" * 65)
    print("Evaluating Graph-Only, Document-Only, and Combined Fusion performance...\n")

    with open(GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    # 1. Main Training/Evaluation set
    known_shell_entities = set()
    for cluster in ground_truth.get("shell_clusters", []):
        for member in cluster["members"]:
            known_shell_entities.add(member)

    known_tamper_entities = {d["entity_id"] for d in ground_truth.get("tampered_documents", [])}
    all_known_fraud = known_shell_entities.union(known_tamper_entities)

    # 2. Held-Out cases set
    held_out_entities = set()
    for cluster in ground_truth.get("held_out_cases", []):
        for member in cluster["members"]:
            held_out_entities.add(member)

    with open(RAW_DATA_DIR / "entities.json", "r", encoding="utf-8") as f:
        all_entities = json.load(f)

    # Filter out held-out entities for the main benchmark
    eval_entities = [e for e in all_entities if e["entity_id"] not in held_out_entities]
    held_out_list = [e for e in all_entities if e["entity_id"] in held_out_entities]

    # Metrics storage
    graph_counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    doc_counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    fused_counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}

    for entity in eval_entities:
        eid = entity["entity_id"]
        is_fraud = eid in all_known_fraud

        # --- A. Graph-Only Evaluation ---
        g_res = analyze_vendor_graph(eid)
        g_flag = g_res["graph_risk_score"] >= 40.0
        if is_fraud and g_flag: graph_counts["tp"] += 1
        elif not is_fraud and g_flag: graph_counts["fp"] += 1
        elif not is_fraud and not g_flag: graph_counts["tn"] += 1
        elif is_fraud and not g_flag: graph_counts["fn"] += 1

        # --- B. Document-Only Evaluation ---
        mapped_docs = get_entity_documents(eid)
        d_flag = False
        if mapped_docs:
            d_res = analyze_vendor_document(DOCS_DIR / mapped_docs[0]["filename"], eid)
            d_flag = d_res["authenticity_score"] >= 40.0

        if is_fraud and d_flag: doc_counts["tp"] += 1
        elif not is_fraud and d_flag: doc_counts["fp"] += 1
        elif not is_fraud and not d_flag: doc_counts["tn"] += 1
        elif is_fraud and not d_flag: doc_counts["fn"] += 1

        # --- C. Fused Multi-Signal Evaluation ---
        f_res = get_full_vendor_risk_assessment(eid)
        f_flag = f_res["risk_band"] in ["HIGH", "MEDIUM"]
        if is_fraud and f_flag: fused_counts["tp"] += 1
        elif not is_fraud and f_flag: fused_counts["fp"] += 1
        elif not is_fraud and not f_flag: fused_counts["tn"] += 1
        elif is_fraud and not f_flag: fused_counts["fn"] += 1

    # --- D. Held-Out Evaluation ---
    held_out_tp = 0
    for entity in held_out_list:
        res = get_full_vendor_risk_assessment(entity["entity_id"])
        if res["risk_band"] in ["HIGH", "MEDIUM"]:
            held_out_tp += 1

    # Format output tables
    g_m = compute_metrics(**graph_counts)
    d_m = compute_metrics(**doc_counts)
    f_m = compute_metrics(**fused_counts)

    print("-" * 65)
    print("📊 1. GRAPH-ONLY ENGINE BENCHMARK")
    print("-" * 65)
    print(f"TP: {graph_counts['tp']} | FP: {graph_counts['fp']} | TN: {graph_counts['tn']} | FN: {graph_counts['fn']}")
    print(f"Recall: {g_m['recall']:.1f}% | Precision: {g_m['precision']:.1f}% | F1: {g_m['f1']:.1f}%")

    print("\n" + "-" * 65)
    print("📊 2. DOCUMENT-ONLY FORENSICS BENCHMARK")
    print("-" * 65)
    print(f"TP: {doc_counts['tp']} | FP: {doc_counts['fp']} | TN: {doc_counts['tn']} | FN: {doc_counts['fn']}")
    print(f"Recall: {d_m['recall']:.1f}% | Precision: {d_m['precision']:.1f}% | F1: {d_m['f1']:.1f}%")

    print("\n" + "=" * 65)
    print("🏆 3. COMBINED RISK FUSION BENCHMARK (LAYER C)")
    print("=" * 65)
    print(f"TP: {fused_counts['tp']} | FP: {fused_counts['fp']} | TN: {fused_counts['tn']} | FN: {fused_counts['fn']}")
    print(f"🎯 Accuracy : {f_m['accuracy']:.2f}%")
    print(f"🔍 Recall   : {f_m['recall']:.2f}% (Catches both document & syndicate fraud)")
    print(f"⚖️  Precision: {f_m['precision']:.2f}%")
    print(f"🏆 F1-Score : {f_m['f1']:.2f}%")

    print("\n" + "=" * 65)
    print("🛡️  4. HELD-OUT TEST CASES (Unseen Seed Evaluation)")
    print("=" * 65)
    print(f"Held-Out Fraud Entities Detected: {held_out_tp} / {len(held_out_list)} ({(held_out_tp/len(held_out_list))*100:.1f}% Generalization Recall)")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    run_benchmark()