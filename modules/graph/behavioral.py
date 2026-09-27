import pandas as pd
from typing import List, Dict
from config import STRUCTURING_THRESHOLD, STRUCTURING_NEAR_BAND, STRUCTURING_MIN_TXNS

def detect_structuring(transactions: List[Dict]) -> List[Dict]:
    """
    Identifies entities issuing repeated transactions just under the reporting threshold.
    """
    if not transactions:
        return []

    df = pd.DataFrame(transactions)
    df["date"] = pd.to_datetime(df["date"])

    lower_bound = STRUCTURING_THRESHOLD * STRUCTURING_NEAR_BAND
    upper_bound = STRUCTURING_THRESHOLD

    near_threshold = df[(df["amount"] >= lower_bound) & (df["amount"] < upper_bound)]
    if near_threshold.empty:
        return []

    # Group by sender over a 7-day rolling window
    structuring_flags = (
        near_threshold.groupby(["from_entity", pd.Grouper(key="date", freq="7D")])
        .agg(txn_count=("amount", "count"), total_amount=("amount", "sum"))
        .reset_index()
    )

    flagged = structuring_flags[structuring_flags["txn_count"] >= STRUCTURING_MIN_TXNS]
    
    results = []
    for _, row in flagged.iterrows():
        results.append({
            "entity_id": row["from_entity"],
            "txn_count": int(row["txn_count"]),
            "total_amount": float(row["total_amount"]),
            "window_start": str(row["date"])
        })
    return results