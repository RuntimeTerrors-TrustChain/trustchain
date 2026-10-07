import numpy as np
from pathlib import Path
from modules.forensics.ela import run_ela
from modules.forensics.benford import benfords_law_score
from generator.pdf_factory import (
    generate_tampered_invoice_image,
    generate_clean_invoice_image,
)
from config import ELA_MIN_INTENSITY_THRESHOLD


def test_ela_hotspot_detection(tmp_path):
    tampered_file = generate_tampered_invoice_image(
        "TEST_DOC", "VEND-TEST", "₹ 9,999,000.00"
    )
    _, hotspots, _ = run_ela(str(Path("data/documents") / tampered_file))
    assert len(hotspots) > 0, "ELA should catch spliced number"
    assert any(
        h["intensity"] >= ELA_MIN_INTENSITY_THRESHOLD for h in hotspots
    ), "Tampered hotspot should have intensity >= 0.30"


def test_ela_clean_image_no_hotspots(tmp_path):
    clean_file = generate_clean_invoice_image("TEST_CLEAN", "VEND-CLEAN")
    _, hotspots, _ = run_ela(str(Path("data/documents") / clean_file))
    significant = [h for h in hotspots if h["intensity"] >= ELA_MIN_INTENSITY_THRESHOLD]
    assert len(significant) == 0, "Clean image should have zero significant hotspots"


def test_benford_distribution():
    np.random.seed(42)
    # 300 samples from log-normal distribution naturally conform to Benford (chi2 < 26.12)
    natural_sample = list(np.random.lognormal(mean=10.5, sigma=1.2, size=300))
    res_nat = benfords_law_score(natural_sample)
    assert res_nat["is_anomalous"] is False
    assert res_nat["chi_square"] < 26.12

    # Fabricated flat distribution (60 samples) severely deviates from Benford
    fabricated_sample = [
        91000,
        92000,
        93000,
        94000,
        95000,
        96000,
        97000,
        98000,
        99000,
    ] * 10
    res_fab = benfords_law_score(fabricated_sample)
    assert res_fab["is_anomalous"] is True
    assert res_fab["chi_square"] > 26.12
