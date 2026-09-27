import numpy as np
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from config import GLOBAL_SEED, STRUCTURING_THRESHOLD

np.random.seed(GLOBAL_SEED)
random.seed(GLOBAL_SEED)

def generate_clean_transactions(entity_ids: List[str], count: int = 800) -> List[Dict]:
    """Generates authentic business transactions obeying log-normal distribution."""
    transactions = []
    # Log-normal distribution naturally satisfies Benford's Law
    amounts = np.random.lognormal(mean=10.5, sigma=1.2, size=count)
    base_date = datetime.now() - timedelta(days=180)
    
    for i in range(count):
        sender, receiver = random.sample(entity_ids, 2)
        txn_date = base_date + timedelta(days=random.randint(0, 180), minutes=random.randint(0, 1440))
        transactions.append({
            "transaction_id": f"TXN-{10000 + i}",
            "from_entity": sender,
            "to_entity": receiver,
            "amount": round(float(amounts[i]), 2),
            "date": txn_date.strftime("%Y-%m-%d %H:%M:%S"),
            "invoice_ref": f"INV-{random.randint(10000, 99999)}",
            "is_fraud": False
        })
    return transactions

def inject_circular_chain(cluster_members: List[str], cycle_amount: float = 250000.0) -> Tuple[List[Dict], Dict]:
    """Injects a 3 or 4-hop circular invoicing ring (A -> B -> C -> A)."""
    transactions = []
    hop_count = min(len(cluster_members), 3)
    cycle_nodes = cluster_members[:hop_count]
    
    base_date = datetime.now() - timedelta(days=15)
    
    for i in range(hop_count):
        sender = cycle_nodes[i]
        receiver = cycle_nodes[(i + 1) % hop_count]
        # Slight variation in amount to mimic fake margin deduction
        txn_amount = cycle_amount * (1.0 - (i * 0.01))
        txn_date = base_date + timedelta(days=i * 2, hours=random.randint(1, 5))
        
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
    base_date = datetime.now() - timedelta(days=5)
    
    for i in range(count):
        # Amounts deliberately placed in the near-band (e.g. 48,500 to 49,800)
        amount = round(random.uniform(STRUCTURING_THRESHOLD * 0.96, STRUCTURING_THRESHOLD * 0.99), 2)
        txn_date = base_date + timedelta(hours=i * 8 + random.randint(1, 3))
        
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