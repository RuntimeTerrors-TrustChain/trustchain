import numpy as np
from collections import Counter
from typing import List, Dict

def benfords_law_score(amounts: List[float]) -> Dict:
    """
    Measures Chi-Square style deviation from Benford's Law: P(d) = log10(1 + 1/d).
    Naturally occurring prices follow this curve; fabricated numbers are unnaturally flat.
    """
    # Extract leading non-zero digit
    leading_digits = [int(str(abs(a)).replace(".", "").lstrip("0")[0]) for a in amounts if a > 0]
    
    if len(leading_digits) < 10:
        # Not enough sample size to score reliably
        return {"deviation": 0.0, "is_anomalous": False}

    observed = Counter(leading_digits)
    n = len(leading_digits)
    
    expected = {d: np.log10(1 + 1 / d) for d in range(1, 10)}
    
    # Compute Chi-Square style deviation
    deviation = 0.0
    for d in range(1, 10):
        obs_freq = observed.get(d, 0) / n
        deviation += ((obs_freq - expected[d]) ** 2) / expected[d]

    # Threshold for anomaly (deviation > 0.15 indicates fabricated amounts)
    is_anomalous = deviation > 0.15

    return {
        "deviation": round(float(deviation), 3),
        "is_anomalous": is_anomalous
    }