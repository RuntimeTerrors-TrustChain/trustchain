import json
from config import RAW_DATA_DIR, GROUND_TRUTH_FILE
from backend.services import get_full_vendor_risk_assessment

def run_benchmark():
    print("=" * 65)
    print("🛡️  TRUSTCHAIN AUDIT & BENCHMARK EVALUATION SUITE")
    print("=" * 65)
    print("Evaluating system performance against blind ground truth...\n")

    # 1. Load Ground Truth
    with open(GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    # Extract all planted fraud entity IDs
    known_fraud_entities = set()
    for cluster in ground_truth.get("shell_clusters", []):
        for member in cluster["members"]:
            known_fraud_entities.add(member)

    # 2. Load all entities in database
    with open(RAW_DATA_DIR / "entities.json", "r", encoding="utf-8") as f:
        all_entities = json.load(f)

    total_entities = len(all_entities)
    actual_fraud_count = len(known_fraud_entities)
    actual_clean_count = total_entities - actual_fraud_count

    # Metrics counters
    tp = 0  # True Positive: Fraud correctly flagged as HIGH/MEDIUM
    fp = 0  # False Positive: Clean company flagged as HIGH/MEDIUM
    tn = 0  # True Negative: Clean company flagged as LOW
    fn = 0  # False Negative: Fraud missed (flagged as LOW)

    print(f"Total Registry Entities: {total_entities}")
    print(f"Planted Shell / Fraud Entities: {actual_fraud_count}")
    print(f"Legitimate Entities: {actual_clean_count}\n")
    print("Running multi-signal inference across all entities...")

    for entity in all_entities:
        eid = entity["entity_id"]
        is_actual_fraud = eid in known_fraud_entities

        assessment = get_full_vendor_risk_assessment(eid)
        predicted_fraud = assessment["risk_band"] in ["HIGH", "MEDIUM"]

        if is_actual_fraud and predicted_fraud:
            tp += 1
        elif not is_actual_fraud and predicted_fraud:
            fp += 1
        elif not is_actual_fraud and not predicted_fraud:
            tn += 1
        elif is_actual_fraud and not predicted_fraud:
            fn += 1

    # 3. Calculate Performance Metrics
    precision = (tp / (tp + fp)) * 100 if (tp + fp) > 0 else 0.0
    recall = (tp / (tp + fn)) * 100 if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = ((tp + tn) / total_entities) * 100

    # 4. Display Results
    print("\n" + "=" * 65)
    print("📊 EVALUATION RESULTS & CONFUSION MATRIX")
    print("=" * 65)
    print(f"True Positives  (Fraud Caught)       : {tp} / {actual_fraud_count}")
    print(f"False Positives (Clean False Alarms) : {fp} / {actual_clean_count}")
    print(f"True Negatives  (Clean Approved)     : {tn} / {actual_clean_count}")
    print(f"False Negatives (Fraud Missed)       : {fn} / {actual_fraud_count}")
    print("-" * 65)
    print(f"🎯 ACCURACY     : {accuracy:.2f}%")
    print(f"🔍 RECALL       : {recall:.2f}%  (Ability to catch all fraud syndicates)")
    print(f"⚖️  PRECISION    : {precision:.2f}%  (Reliability of fraud alerts)")
    print(f"🏆 F1-SCORE     : {f1:.2f}%")
    print("=" * 65)

    print("\n💡 PITCH SLIDE TAKEAWAY:")
    print(f'   "Our multi-signal fusion achieved {recall:.1f}% recall on hidden shell networks')
    print(f'    with a false-positive rate of only {(fp/actual_clean_count)*100:.1f}% across {total_entities} companies."\n')

if __name__ == "__main__":
    run_benchmark()