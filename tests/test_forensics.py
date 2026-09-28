import numpy as np
from pathlib import Path
from modules.forensics.ela import run_ela
from modules.forensics.benford import benfords_law_score
from generator.pdf_factory import generate_tampered_invoice_image

def test_ela_hotspot_detection(tmp_path):
    tampered_file = generate_tampered_invoice_image("TEST_DOC", "VEND-TEST", "₹ 9,999,000.00")
    _, hotspots, _ = run_ela(str(Path("data/documents") / tampered_file))
    assert len(hotspots) > 0, "ELA should catch spliced number"

def test_benford_distribution():
    # Natural numbers generated from log-normal distribution naturally obey Benford's Law
    np.random.seed(42)
    natural_sample = list(np.random.lognormal(mean=10.5, sigma=1.2, size=300))
    res_nat = benfords_law_score(natural_sample)
    assert res_nat["deviation"] < 0.15

    # Uniform fabricated numbers (violates Benford)
    fabricated_sample = [91000, 92000, 93000, 94000, 95000, 96000, 97000, 98000, 99000] * 10
    res_fab = benfords_law_score(fabricated_sample)
    assert res_fab["deviation"] > 0.15
    assert res_fab["is_anomalous"] is True