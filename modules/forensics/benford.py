import numpy as np
from collections import Counter
from typing import List, Dict, Any
from config import BENFORD_MIN_SAMPLE_SIZE, BENFORD_ANOMALY_THRESHOLD

def benfords_law_score(amounts: List[float]) -> Dict[str, Any]:
    """
    Measures Chi-Square style deviation from Benford's Law: P(d) = log10(1 + 1/d).
    Naturally occurring prices follow this curve; fabricated numbers are unnaturally flat.
    """
    leading_digits = [int(str(abs(a)).replace(".", "").lstrip("0")[0]) for a in amounts if a > 0]
    
    if len(leading_digits) < BENFORD_MIN_SAMPLE_SIZE:
        return {"deviation": 0.0, "is_anomalous": False}

    observed = Counter(leading_digits)
    n = len(leading_digits)
    
    expected = {d: np.log10(1 + 1 / d) for d in range(1, 10)}
    
    deviation = 0.0
    for d in range(1, 10):
        obs_freq = observed.get(d, 0) / n
        deviation += ((obs_freq - expected[d]) ** 2) / expected[d]

    is_anomalous = bool(deviation > BENFORD_ANOMALY_THRESHOLD)

    return {
        "deviation": round(float(deviation), 3),
        "is_anomalous": is_anomalous
    }