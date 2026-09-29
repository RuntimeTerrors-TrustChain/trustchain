import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import json
from config import RAW_DATA_DIR, GROUND_TRUTH_FILE, DOCUMENTS_MAP_FILE, GLOBAL_SEED
from generator.entities import (
    reset_registry_builder,
    generate_clean_entities,
    inject_shell_cluster,
)
from generator.transactions import (
    generate_clean_transactions,
    inject_circular_chain,
    inject_structuring_pattern,
)
from generator.pdf_factory import (
    generate_clean_invoice_pdf,
    generate_tampered_pdf_metadata,
    generate_tampered_invoice_image,
    generate_clean_invoice_image,
)


def run():
    print("⚙️  Generating synthetic procurement fraud dataset...")

    # Reset builder to guarantee strict determinism
    reset_registry_builder(seed=GLOBAL_SEED)

    # 1. Base clean entities
    entities = generate_clean_entities(count=120)
    ground_truth = {
        "shell_clusters": [],
        "circular_chains": [],
        "structuring_cases": [],
        "tampered_documents": [],
        "held_out_cases": [],
    }

    # 2. Inject 3 Main Shell Clusters (12 entities)
    for i in range(1, 4):
        shell_nodes, cluster_gt = inject_shell_cluster(
            cluster_id=f"CLUSTER-0{i}", size=4
        )
        entities.extend(shell_nodes)
        ground_truth["shell_clusters"].append(cluster_gt)

    # 3. Inject 1 Held-Out Test Cluster (4 entities)
    held_out_nodes, held_out_gt = inject_shell_cluster(
        cluster_id="CLUSTER-HELD-OUT", size=4
    )
    entities.extend(held_out_nodes)
    ground_truth["held_out_cases"].append(held_out_gt)

    all_entity_ids = [e["entity_id"] for e in entities]

    # 4. Generate Transactions (Log-Normal baseline with pinned epoch date)
    transactions = generate_clean_transactions(all_entity_ids, count=700)

    # 5. Inject Circular Invoicing (Cluster 1 & Cluster 2)
    c1_members = ground_truth["shell_clusters"][0]["members"]
    c2_members = ground_truth["shell_clusters"][1]["members"]

    cycle1_txns, c1_gt = inject_circular_chain(c1_members, cycle_amount=350000.0)
    cycle2_txns, c2_gt = inject_circular_chain(c2_members, cycle_amount=180000.0)
    transactions.extend(cycle1_txns)
    transactions.extend(cycle2_txns)
    ground_truth["circular_chains"].extend([c1_gt, c2_gt])

    # 6. Inject Structuring (Cluster 3)
    c3_members = ground_truth["shell_clusters"][2]["members"]
    struct_txns, struct_gt = inject_structuring_pattern(
        c3_members[0], c3_members[1], count=4
    )
    transactions.extend(struct_txns)
    ground_truth["structuring_cases"].append(struct_gt)

    # 7. Generate Document Mapping (data/raw/documents.json) covering all 5 scenarios
    documents_map = []

    # SCENARIO A: Clean vendor + Clean PDF
    clean_vendor_1 = entities[0]["entity_id"]
    doc_a = generate_clean_invoice_pdf(
        "DOC-101", clean_vendor_1, entities[0]["name"], 350000.0
    )
    documents_map.append(
        {
            "document_id": "DOC-101",
            "entity_id": clean_vendor_1,
            "filename": doc_a,
            "is_tampered": False,
        }
    )

    # Clean vendor + Clean JPEG
    clean_vendor_2 = entities[1]["entity_id"]
    doc_a2 = generate_clean_invoice_image("DOC-102", clean_vendor_2)
    documents_map.append(
        {
            "document_id": "DOC-102",
            "entity_id": clean_vendor_2,
            "filename": doc_a2,
            "is_tampered": False,
        }
    )

    # SCENARIO B: Tampered doc alone (Clean standalone vendor, NOT in any cluster)
    standalone_fraud_vendor = entities[5]["entity_id"]
    doc_b = generate_tampered_invoice_image(
        "DOC-201",
        standalone_fraud_vendor,
        patch_text="₹ 7,420,000.00",
        tamper_pos=(540, 205),
    )
    documents_map.append(
        {
            "document_id": "DOC-201",
            "entity_id": standalone_fraud_vendor,
            "filename": doc_b,
            "is_tampered": True,
        }
    )
    ground_truth["tampered_documents"].append(
        {
            "document_id": "DOC-201",
            "entity_id": standalone_fraud_vendor,
            "scenario": "tamper_only",
        }
    )

    # SCENARIO C: Shell cluster member + Clean doc or No doc (Cluster 1, Member 1)
    shell_clean_doc_vendor = c1_members[1]
    doc_c = generate_clean_invoice_pdf(
        "DOC-301", shell_clean_doc_vendor, "Shell Affiliate", 220000.0
    )
    documents_map.append(
        {
            "document_id": "DOC-301",
            "entity_id": shell_clean_doc_vendor,
            "filename": doc_c,
            "is_tampered": False,
        }
    )

    # SCENARIO D: Shell cluster member + Tampered ELA image (Cluster 1, Member 0)
    shell_tampered_vendor = c1_members[0]
    doc_d = generate_tampered_invoice_image(
        "DOC-401",
        shell_tampered_vendor,
        patch_text="₹ 9,850,000.00",
        tamper_pos=(540, 205),
    )
    documents_map.append(
        {
            "document_id": "DOC-401",
            "entity_id": shell_tampered_vendor,
            "filename": doc_d,
            "is_tampered": True,
        }
    )
    ground_truth["tampered_documents"].append(
        {
            "document_id": "DOC-401",
            "entity_id": shell_tampered_vendor,
            "scenario": "shell_and_tamper",
        }
    )

    # SCENARIO E: Circular flow participant + Metadata Tampered PDF (Cluster 2, Member 0)
    cycle_meta_vendor = c2_members[0]
    doc_e = generate_tampered_pdf_metadata(
        "DOC-501", cycle_meta_vendor, "Trading Co", 180000.0
    )
    documents_map.append(
        {
            "document_id": "DOC-501",
            "entity_id": cycle_meta_vendor,
            "filename": doc_e,
            "is_tampered": True,
        }
    )
    ground_truth["tampered_documents"].append(
        {
            "document_id": "DOC-501",
            "entity_id": cycle_meta_vendor,
            "scenario": "cycle_and_metadata",
        }
    )

    # Additional diverse documents across other clean entities
    for idx, e in enumerate(entities[10:25]):
        doc_name = generate_clean_invoice_pdf(
            f"DOC-GEN-{idx+1}", e["entity_id"], e["name"], float(30000 + idx * 5000)
        )
        documents_map.append(
            {
                "document_id": f"DOC-GEN-{idx+1}",
                "entity_id": e["entity_id"],
                "filename": doc_name,
                "is_tampered": False,
            }
        )

    # Write files to disk
    with open(RAW_DATA_DIR / "entities.json", "w", encoding="utf-8") as f:
        json.dump(entities, f, indent=2)

    with open(RAW_DATA_DIR / "transactions.json", "w", encoding="utf-8") as f:
        json.dump(transactions, f, indent=2)

    with open(DOCUMENTS_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(documents_map, f, indent=2)

    with open(GROUND_TRUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    print(
        f"✅ Generated {len(entities)} entities ({len(ground_truth['shell_clusters'])*4 + len(ground_truth['held_out_cases'])*4} total shell entities)."
    )
    print(f"✅ Generated {len(transactions)} transactions.")
    print(f"✅ Generated {len(documents_map)} mapped documents.")
    print(f"📁 Output saved to '{RAW_DATA_DIR}' and '{GROUND_TRUTH_FILE}'.")


if __name__ == "__main__":
    run()
