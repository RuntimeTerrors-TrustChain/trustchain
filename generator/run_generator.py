import sys
from pathlib import Path

# Add project root to sys.path so config and modules can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))

import json
from config import RAW_DATA_DIR, GROUND_TRUTH_FILE
from generator.entities import generate_clean_entities, inject_shell_cluster
from generator.transactions import (
    generate_clean_transactions,
    inject_circular_chain,
    inject_structuring_pattern,
)


def run():
    print("⚙️  Generating synthetic procurement data...")

    # 1. Base clean entities
    entities = generate_clean_entities(count=120)
    ground_truth = {
        "shell_clusters": [],
        "circular_chains": [],
        "structuring_cases": [],
    }

    # 2. Inject 3 Shell Clusters
    for i in range(1, 4):
        shell_nodes, cluster_gt = inject_shell_cluster(
            cluster_id=f"CLUSTER-0{i}", size=4
        )
        entities.extend(shell_nodes)
        ground_truth["shell_clusters"].append(cluster_gt)

    all_entity_ids = [e["entity_id"] for e in entities]

    # 3. Base clean transactions
    transactions = generate_clean_transactions(all_entity_ids, count=600)

    # 4. Inject Circular Invoicing in Cluster 1 & Cluster 2
    c1_members = ground_truth["shell_clusters"][0]["members"]
    c2_members = ground_truth["shell_clusters"][1]["members"]

    cycle1_txns, c1_gt = inject_circular_chain(c1_members, cycle_amount=350000.0)
    cycle2_txns, c2_gt = inject_circular_chain(c2_members, cycle_amount=180000.0)

    transactions.extend(cycle1_txns)
    transactions.extend(cycle2_txns)
    ground_truth["circular_chains"].extend([c1_gt, c2_gt])

    # 5. Inject Structuring Sequence in Cluster 3
    c3_members = ground_truth["shell_clusters"][2]["members"]
    struct_txns, struct_gt = inject_structuring_pattern(
        c3_members[0], c3_members[1], count=4
    )
    transactions.extend(struct_txns)
    ground_truth["structuring_cases"].append(struct_gt)

    # Save files
    with open(RAW_DATA_DIR / "entities.json", "w") as f:
        json.dump(entities, f, indent=2)

    with open(RAW_DATA_DIR / "transactions.json", "w") as f:
        json.dump(transactions, f, indent=2)

    with open(GROUND_TRUTH_FILE, "w") as f:
        json.dump(ground_truth, f, indent=2)

    print(
        f"✅ Generated {len(entities)} entities ({len(ground_truth['shell_clusters'])*4} shell companies)."
    )
    print(
        f"✅ Generated {len(transactions)} transactions with injected cycles and structuring."
    )
    print(f"📁 Output saved to '{RAW_DATA_DIR}' and '{GROUND_TRUTH_FILE}'.")


if __name__ == "__main__":
    run()
