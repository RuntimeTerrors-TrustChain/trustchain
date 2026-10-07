import pandas as pd
from typing import List, Dict
from config import STRUCTURING_THRESHOLD, STRUCTURING_NEAR_BAND, STRUCTURING_MIN_TXNS


def detect_structuring(transactions: List[Dict], window_days: int = 7) -> List[Dict]:
    """
    Flags senders with >= STRUCTURING_MIN_TXNS payments inside the near-threshold band
    using a true two-pointer sliding window, preventing calendar-bin boundary leaks.
    """
    if not transactions:
        return []

    df = pd.DataFrame(transactions)
    df["date"] = pd.to_datetime(df["date"])

    lower_bound = STRUCTURING_THRESHOLD * STRUCTURING_NEAR_BAND
    upper_bound = STRUCTURING_THRESHOLD

    near = df[(df["amount"] >= lower_bound) & (df["amount"] < upper_bound)]
    if near.empty:
        return []

    window = pd.Timedelta(days=window_days)
    results: List[Dict] = []

    for sender, grp in near.sort_values("date").groupby("from_entity"):
        dates = grp["date"].tolist()
        amounts = grp["amount"].tolist()
        best = None
        i = 0
        for j in range(len(dates)):
            while dates[j] - dates[i] > window:
                i += 1
            count = j - i + 1
            if count >= STRUCTURING_MIN_TXNS and (best is None or count > best[0]):
                best = (count, i, j)
        if best:
            count, s, e = best
            results.append(
                {
                    "entity_id": sender,
                    "txn_count": int(count),
                    "total_amount": float(sum(amounts[s : e + 1])),
                    "window_start": str(dates[s]),
                }
            )
    return results
