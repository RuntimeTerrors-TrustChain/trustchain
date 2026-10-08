import numpy as np
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from config import GLOBAL_SEED, STRUCTURING_THRESHOLD

# Pinned deterministic reference date
FIXED_BASE_DATE = datetime(2026, 1, 15, 9, 0, 0)

np.random.seed(GLOBAL_SEED)
random.seed(GLOBAL_SEED)

def generate_clean_transactions(entity_ids: List[str], count: int = 700) -> List[Dict]:
    """
    Generates authentic business transactions obeying log-normal distribution.
    Generates a concentrated 55-transaction history for clean vendor entity_ids[0]
    to demonstrate Benford's Law compliance (chi2 < 26.12).
    """
    random.seed(GLOBAL_SEED)
    np.random.seed(GLOBAL_SEED)
    
    transactions = []
    amounts = np.random.lognormal(mean=10.5, sigma=1.2, size=count)
    
    # 1. Base mesh transactions
    for i in range(count):
        sender, receiver = random.sample(entity_ids, 2)
        txn_date = FIXED_BASE_DATE + timedelta(days=random.randint(0, 150), minutes=random.randint(0, 1440))
        transactions.append({
            "transaction_id": f"TXN-{10000 + i}",
            "from_entity": sender,
            "to_entity": receiver,
            "amount": round(float(amounts[i]), 2),
            "date": txn_date.strftime("%Y-%m-%d %H:%M:%S"),
            "invoice_ref": f"INV-{random.randint(10000, 99999)}",
            "is_fraud": False
        })

    # 2. Concentrated 55-invoice history for clean control vendor (entity_ids[0])
    clean_target = entity_ids[0]
    clean_amounts = np.random.lognormal(mean=10.2, sigma=1.1, size=55)
    for idx, amt in enumerate(clean_amounts):
        receiver = entity_ids[(idx % 20) + 1]
        txn_date = FIXED_BASE_DATE + timedelta(days=idx * 2, hours=10)
        transactions.append({
            "transaction_id": f"TXN-CLN-HIST-{idx+1:03d}",
            "from_entity": clean_target,
            "to_entity": receiver,
            "amount": round(float(amt), 2),
            "date": txn_date.strftime("%Y-%m-%d %H:%M:%S"),
            "invoice_ref": f"INV-CLN-{idx+1:03d}",
            "is_fraud": False
        })

    return transactions

def inject_benford_fabrication(target_entity_id: str, recipient_ids: List[str], count: int = 55) -> List[Dict]:
    """
    Injects 55 fabricated invoices heavily skewed towards leading digits 8 and 9
    (violates Benford with chi2 > 35.0, p < 0.001).
    """
    random.seed(GLOBAL_SEED)
    transactions = []
    # Concentrated 8s and 9s (unnatural high-digit fabrication)
    fabricated_pool = [91000, 92500, 93000, 94200, 95000, 96400, 97000, 98200, 99000, 85000, 87000, 89000]
    for idx in range(count):
        receiver = recipient_ids[(idx % 15) + 1]
        amt = float(fabricated_pool[idx % len(fabricated_pool)] + random.randint(10, 99))
        txn_date = FIXED_BASE_DATE + timedelta(days=idx * 2, hours=14)
        transactions.append({
            "transaction_id": f"TXN-FAB-HIST-{idx+1:03d}",
            "from_entity": target_entity_id,
            "to_entity": receiver,
            "amount": amt,
            "date": txn_date.strftime("%Y-%m-%d %H:%M:%S"),
            "invoice_ref": f"INV-FAB-{idx+1:03d}",
            "is_fraud": True,
            "fraud_type": "benford_fabrication"
        })
    return transactions

def inject_circular_chain(cluster_members: List[str], cycle_amount: float = 250000.0) -> Tuple[List[Dict], Dict]:
    """Injects a 3 or 4-hop circular invoicing ring (A -> B -> C -> A)."""
    transactions = []
    hop_count = min(len(cluster_members), 3)
    cycle_nodes = cluster_members[:hop_count]
    
    for i in range(hop_count):
        sender = cycle_nodes[i]
        receiver = cycle_nodes[(i + 1) % hop_count]
        txn_amount = cycle_amount * (1.0 - (i * 0.01))
        txn_date = FIXED_BASE_DATE + timedelta(days=160 + (i * 2), hours=10 + i)
        
        transactions.append({
            "transaction_id": f"TXN-CYCLE-{sender[-4:]}-{receiver[-4:]}",
            "from_entity": sender,
            "to_entity": receiver,
            "amount": round(float(txn_amount), 2),
            "date": txn_date.strftime("%Y-%m-%d %H:%M:%S"),
            "invoice_ref": f"INV-CYC-{random.randint(1000, 9999)}",
            "is_fraud": True,
            "fraud_type": "circular_invoicing"
        })
        
    ground_truth = {
        "cycle_path": cycle_nodes + [cycle_nodes[0]],
        "cycle_amount": cycle_amount
    }
    return transactions, ground_truth

def inject_structuring_pattern(sender_id: str, receiver_id: str, count: int = 4) -> Tuple[List[Dict], Dict]:
    """Injects transactions just below the threshold within 48 hours."""
    transactions = []
    
    for i in range(count):
        amount = round(random.uniform(STRUCTURING_THRESHOLD * 0.96, STRUCTURING_THRESHOLD * 0.99), 2)
        txn_date = FIXED_BASE_DATE + timedelta(days=170, hours=i * 8 + 2)
        
        transactions.append({
            "transaction_id": f"TXN-STRUCT-{i+1}",
            "from_entity": sender_id,
            "to_entity": receiver_id,
            "amount": amount,
            "date": txn_date.strftime("%Y-%m-%d %H:%M:%S"),
            "invoice_ref": f"INV-STR-{random.randint(1000, 9999)}",
            "is_fraud": True,
            "fraud_type": "structuring"
        })
        
    ground_truth = {
        "sender": sender_id,
        "receiver": receiver_id,
        "count": count,
        "threshold": STRUCTURING_THRESHOLD
    }
    return transactions, ground_truth