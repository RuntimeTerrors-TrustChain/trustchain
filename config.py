"""
TrustChain Global Configuration & Scoring Thresholds
"""

from pathlib import Path

# --- File Paths ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
DOCS_DIR = DATA_DIR / "documents"
GROUND_TRUTH_FILE = DATA_DIR / "ground_truth.json"
DOCUMENTS_MAP_FILE = RAW_DATA_DIR / "documents.json"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# --- Random Seed (Ensures deterministic demo behavior) ---
GLOBAL_SEED = 42

# --- Module A: Document Forensics Constants ---
ELA_JPEG_QUALITY = 90  # Baseline compression quality for ELA diff
ELA_AMPLIFICATION_SCALE = 20  # Multiplier to make subtle pixel diffs visible
ELA_HOTSPOT_PERCENTILE = 85  # Cutoff to ignore baseline scanner noise
ELA_MIN_INTENSITY_THRESHOLD = (
    0.30  # True tampering threshold (separates clean <0.05 from tampered >0.45)
)
BENFORD_MIN_SAMPLE_SIZE = (
    50  # Minimum amounts needed for a statistically valid first-digit test
)
BENFORD_CHI2_CRITICAL = (
    26.12  # Chi-square critical cutoff (df=8, p=0.001 for ~0.1% false positive rate)
)

# --- Module B: Graph Engine Constants ---
FUZZY_MATCH_THRESHOLD = 90.0  # RapidFuzz token similarity for address/director typos
SHELL_CLUSTER_MAX_SIZE = 8  # Maximum members in a tight illicit cartel
SHELL_CLUSTER_MIN_DENSITY = 0.5  # Minimum edge density to qualify as a shell cluster
MAX_CYCLE_HOP_LIMIT = 4  # Maximum search depth for circular money loops
STRUCTURING_THRESHOLD = 50000.0  # Statutory cash reporting limit under PMLA
STRUCTURING_NEAR_BAND = 0.95  # Lower boundary multiplier (covers ₹47,500 - ₹49,999)
STRUCTURING_MIN_TXNS = 3  # Minimum near-threshold transactions to trigger alert

# --- Module C: Risk Fusion & Escalation Weights ---
WEIGHT_DOCUMENT = 0.5  # Weight for physical document forensic signal
WEIGHT_GRAPH = 0.5  # Weight for structural relationship signal

# Explicit explainable escalation rules
ESCALATION_CLUSTER_STANDALONE = (
    25.0  # Boost for being in a dense shell cartel (guarantees MEDIUM)
)
ESCALATION_CLUSTER_AND_TAMPER = (
    20.0  # Compounding bonus: tampered doc inside shell cluster -> HIGH
)
ESCALATION_CYCLE_AND_METADATA = (
    15.0  # Compounding bonus: circular flow + metadata anomaly -> HIGH
)

SCORE_BAND_HIGH = 70.0  # High-risk threshold (Immediate hold)
SCORE_BAND_MEDIUM = 40.0  # Medium-risk threshold (Manual auditor review)
