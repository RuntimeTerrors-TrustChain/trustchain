import math
from collections import Counter
from typing import List, Dict, Any, Optional
from config import BENFORD_MIN_SAMPLE_SIZE, BENFORD_CHI2_CRITICAL


def _leading_digit(x: float) -> Optional[int]:
    """Leading significant digit via scientific notation (safe for tiny/huge floats)."""
    if x is None or x <= 0 or not math.isfinite(x):
        return None
    return int(f"{float(x):.15e}"[0])


def benfords_law_score(amounts: List[float]) -> Dict[str, Any]:
    """
    First-digit Benford test using a true Pearson chi-square statistic:
        chi2 = n * sum((obs_freq - exp_freq)^2 / exp_freq), df = 8
    Compares against statutory critical value (26.12, p=0.001) to eliminate false alarms.
    """
    digits = [d for d in (_leading_digit(a) for a in amounts) if d]
    n = len(digits)

    if n < BENFORD_MIN_SAMPLE_SIZE:
        return {
            "deviation": 0.0,
            "chi_square": 0.0,
            "sample_size": n,
            "is_anomalous": False,
        }

    observed = Counter(digits)
    expected = {d: math.log10(1 + 1 / d) for d in range(1, 10)}
    distance = sum(
        ((observed.get(d, 0) / n) - expected[d]) ** 2 / expected[d]
        for d in range(1, 10)
    )
    chi2 = n * distance

    return {
        "deviation": round(float(distance), 3),
        "chi_square": round(float(chi2), 2),
        "sample_size": n,
        "is_anomalous": bool(chi2 > BENFORD_CHI2_CRITICAL),
    }
