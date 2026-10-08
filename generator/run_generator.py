import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import json
from collections import defaultdict
from config import RAW_DATA_DIR, GROUND_TRUTH_FILE, DOCUMENTS_MAP_FILE, GLOBAL_SEED
from generator.entities import reset_registry_builder, generate_clean_entities, inject_shell_cluster
from generator.transactions import (
    generate_clean_transactions,
    inject_circular_chain,
    inject_structuring_pattern,
    inject_benford_fabrication
)
from generator.pdf_factory import (
    generate_clean_invoice_pdf,
    generate_tampered_pdf_metadata,
    generate_tampered_invoice_image,
    generate_clean_invoice_image
)

def verify_and_repair_entities(entities, ground_truth, builder):
    """
    Mandatory safety net: scans all clean entities for unintended attribute collisions
    and deterministically repairs them.
    """
    planted_eids = set()
    planted_directors = set()
    planted_addresses = set()

    for cluster in ground_truth["shell_clusters"]:
        for m in cluster["members"]:
            planted_eids.add(m)
        planted_directors.add(cluster["shared_director"])
        planted_addresses.add(cluster["shared_address"])

    seen_directors = defaultdict(list)
    seen_addresses = defaultdict(list)
    seen_phones = defaultdict(list)
    seen_banks = defaultdict(list)

    for e in entities:
        eid = e["entity_id"]
        is_plant = eid in planted_eids
        
        for d in e["director_names"]:
            if is_plant:
                seen_directors[d].append(eid)
            else:
                if d in planted_directors:
                    raise RuntimeError(f"FATAL: Clean entity {eid} collides with planted director '{d}'")
                seen_directors[d].append(eid)

        addr = e["registered_address"]
        if is_plant:
            seen_addresses[addr].append(eid)
        else:
            if addr in planted_addresses:
                raise RuntimeError(f"FATAL: Clean entity {eid} collides with planted address '{addr}'")
            seen_addresses[addr].append(eid)

        seen_phones[e["phone"]].append(eid)
        seen_banks[e["bank_account"]].append(eid)

    repairs_count = 0
    for e in entities:
        eid = e["entity_id"]
        if eid in planted_eids:
            continue

        new_directors = []
        for d in e["director_names"]:
            if len(seen_directors[d]) > 1:
                new_d = builder.get_unique_director_name()
                print(f"⚠️  REPAIR: Clean entity {eid} duplicate director '{d}' -> '{new_d}'")
                seen_directors[d].remove(eid)
                seen_directors[new_d].append(eid)
                new_directors.append(new_d)
                repairs_count += 1
            else:
                new_directors.append(d)
        e["director_names"] = new_directors

        addr = e["registered_address"]
        if len(seen_addresses[addr]) > 1:
            new_addr = builder.get_unique_address()
            print(f"⚠️  REPAIR: Clean entity {eid} duplicate address -> '{new_addr}'")
            seen_addresses[addr].remove(eid)
            seen_addresses[new_addr].append(eid)
            e["registered_address"] = new_addr
            repairs_count += 1

        phone = e["phone"]
        if len(seen_phones[phone]) > 1:
            new_phone = builder.get_unique_phone()
            print(f"⚠️  REPAIR: Clean entity {eid} duplicate phone -> '{new_phone}'")
            seen_phones[phone].remove(eid)
            seen_phones[new_phone].append(eid)
            e["phone"] = new_phone
            repairs_count += 1

        bank = e["bank_account"]
        if len(seen_banks[bank]) > 1:
            new_bank = builder.get_unique_bank_account()
            print(f"⚠️  REPAIR: Clean entity {eid} duplicate bank -> '{new_bank}'")
            seen_banks[bank].remove(eid)
            seen_banks[new_bank].append(eid)
            e["bank_account"] = new_bank
            repairs_count += 1

    clean_entities = [e for e in entities if e["entity_id"] not in planted_eids]
    clean_directors = [d for e in clean_entities for d in e["director_names"]]
    if len(clean_directors) != len(set(clean_directors)):
        raise RuntimeError("FATAL: Unresolved clean director collision after repair pass!")

    print(f"🛡️  Verify-and-Repair Pass Complete: {repairs_count} collision(s) repaired. 0 unintended duplicates remain.")

def run():
    print("⚙️  Generating synthetic procurement fraud dataset...")
    builder = reset_registry_builder(seed=GLOBAL_SEED)
    
    entities = generate_clean_entities(count=120)
    ground_truth = {
        "shell_clusters": [], 
        "circular_chains": [], 
        "structuring_cases": [],
        "tampered_documents": [],
        "held_out_cases": []
    }
    
    for i in range(1, 4):
        shell_nodes, cluster_gt = inject_shell_cluster(cluster_id=f"CLUSTER-0{i}", size=4)
        entities.extend(shell_nodes)
        ground_truth["shell_clusters"].append(cluster_gt)
        
    held_out_nodes, held_out_gt = inject_shell_cluster(cluster_id="CLUSTER-HELD-OUT", size=4)
    entities.extend(held_out_nodes)
    ground_truth["shell_clusters"].append(held_out_gt)
    ground_truth["held_out_cases"].append(held_out_gt)
        
    verify_and_repair_entities(entities, ground_truth, builder)

    all_entity_ids = [e["entity_id"] for e in entities]
    transactions = generate_clean_transactions(all_entity_ids, count=700)
    
    c1_members = ground_truth["shell_clusters"][0]["members"]
    c2_members = ground_truth["shell_clusters"][1]["members"]
    
    # Inject Benford flat-digit fabrication specifically on Scenario D (Climax Vendor)
    benford_txns = inject_benford_fabrication(c1_members[0], all_entity_ids, count=55)
    transactions.extend(benford_txns)

    cycle1_txns, c1_gt = inject_circular_chain(c1_members, cycle_amount=350000.0)
    cycle2_txns, c2_gt = inject_circular_chain(c2_members, cycle_amount=180000.0)
    transactions.extend(cycle1_txns)
    transactions.extend(cycle2_txns)
    ground_truth["circular_chains"].extend([c1_gt, c2_gt])
    
    c3_members = ground_truth["shell_clusters"][2]["members"]
    struct_txns, struct_gt = inject_structuring_pattern(c3_members[0], c3_members[1], count=4)
    transactions.extend(struct_txns)
    ground_truth["structuring_cases"].append(struct_gt)
    
    documents_map = []
    
    # SCENARIO A: Clean vendor + Clean PDF
    clean_vendor_1 = entities[0]["entity_id"]
    doc_a = generate_clean_invoice_pdf("DOC-101", clean_vendor_1, entities[0]["name"], 350000.0)
    documents_map.append({"document_id": "DOC-101", "entity_id": clean_vendor_1, "filename": doc_a, "is_tampered": False})

    # Clean vendor + Clean JPEG
    clean_vendor_2 = entities[1]["entity_id"]
    doc_a2 = generate_clean_invoice_image("DOC-102", clean_vendor_2)
    documents_map.append({"document_id": "DOC-102", "entity_id": clean_vendor_2, "filename": doc_a2, "is_tampered": False})

    # SCENARIO B: Tampered doc alone (Clean standalone vendor, NOT in any cluster, clean Benford history)
    standalone_fraud_vendor = entities[5]["entity_id"]
    doc_b = generate_tampered_invoice_image("DOC-201", standalone_fraud_vendor, patch_text="₹ 7,420,000.00", tamper_pos=(540, 205))
    documents_map.append({"document_id": "DOC-201", "entity_id": standalone_fraud_vendor, "filename": doc_b, "is_tampered": True})
    ground_truth["tampered_documents"].append({"document_id": "DOC-201", "entity_id": standalone_fraud_vendor, "scenario": "tamper_only"})

    # SCENARIO C: Shell cluster member + Clean doc
    shell_clean_doc_vendor = c1_members[1]
    doc_c = generate_clean_invoice_pdf("DOC-301", shell_clean_doc_vendor, "Shell Affiliate", 220000.0)
    documents_map.append({"document_id": "DOC-301", "entity_id": shell_clean_doc_vendor, "filename": doc_c, "is_tampered": False})

    # SCENARIO D: Shell cluster member + Tampered ELA image + Fabricated Benford history
    shell_tampered_vendor = c1_members[0]
    doc_d = generate_tampered_invoice_image("DOC-401", shell_tampered_vendor, patch_text="₹ 9,850,000.00", tamper_pos=(540, 205))
    documents_map.append({"document_id": "DOC-401", "entity_id": shell_tampered_vendor, "filename": doc_d, "is_tampered": True})
    ground_truth["tampered_documents"].append({"document_id": "DOC-401", "entity_id": shell_tampered_vendor, "scenario": "shell_and_tamper"})

    # SCENARIO E: Circular flow participant + Metadata Tampered PDF
    cycle_meta_vendor = c2_members[0]
    doc_e = generate_tampered_pdf_metadata("DOC-501", cycle_meta_vendor, "Trading Co", 180000.0)
    documents_map.append({"document_id": "DOC-501", "entity_id": cycle_meta_vendor, "filename": doc_e, "is_tampered": True})
    ground_truth["tampered_documents"].append({"document_id": "DOC-501", "entity_id": cycle_meta_vendor, "scenario": "cycle_and_metadata"})

    for idx, e in enumerate(entities[10:25]):
        doc_name = generate_clean_invoice_pdf(f"DOC-GEN-{idx+1}", e["entity_id"], e["name"], float(30000 + idx*5000))
        documents_map.append({"document_id": f"DOC-GEN-{idx+1}", "entity_id": e["entity_id"], "filename": doc_name, "is_tampered": False})

    with open(RAW_DATA_DIR / "entities.json", "w", encoding="utf-8") as f:
        json.dump(entities, f, indent=2)
        
    with open(RAW_DATA_DIR / "transactions.json", "w", encoding="utf-8") as f:
        json.dump(transactions, f, indent=2)

    with open(DOCUMENTS_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(documents_map, f, indent=2)
        
    with open(GROUND_TRUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    print(f"✅ Generated {len(entities)} entities ({len(ground_truth['shell_clusters'])*4} total shell entities).")
    print(f"✅ Generated {len(transactions)} transactions.")
    print(f"✅ Generated {len(documents_map)} mapped documents.")
    print(f"📁 Output saved to '{RAW_DATA_DIR}' and '{GROUND_TRUTH_FILE}'.")

if __name__ == "__main__":
    run()