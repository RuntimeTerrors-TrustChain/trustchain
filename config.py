"""
TrustChain Global Configuration & Scoring Thresholds
"""
from pathlib import Path

# File Paths
BASE_DIR = Path(__file__).resolve().parent # parent location of config.py
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
DOCS_DIR = DATA_DIR / "documents"
GROUND_TRUTH_FILE = DATA_DIR / "ground_truth.json"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# --- Random Seed (Ensures deterministic demo behavior) ---
GLOBAL_SEED = 42

# --- Module A: Document Forensics Constants ---
ELA_JPEG_QUALITY = 90
ELA_AMPLIFICATION_SCALE = 20
ELA_HOTSPOT_PERCENTILE = 85
BENFORD_MIN_SAMPLE_SIZE = 30  # Minimum line items needed for reliable vendor score

# --- Module B: Graph Engine Constants ---
FUZZY_MATCH_THRESHOLD = 90.0   # Percentage similarity for names/addresses (RapidFuzz)
SHELL_CLUSTER_MAX_SIZE = 8     # Shell clusters are small and tight
SHELL_CLUSTER_MIN_DENSITY = 0.5
MAX_CYCLE_HOP_LIMIT = 6        # Restrict depth-first simple cycle bounds
STRUCTURING_THRESHOLD = 50000.0  # Regulatory cash flag threshold
STRUCTURING_NEAR_BAND = 0.98    # Flag amounts between [49,000, 49,999]
STRUCTURING_MIN_TXNS = 3       # Min txns within window to flag

# --- Module C: Risk Fusion & Escalation ---
WEIGHT_DOCUMENT = 0.5
WEIGHT_GRAPH = 0.5
ESCALATION_CLUSTER_AND_TAMPER = 20.0
ESCALATION_CYCLE_AND_METADATA = 15.0

SCORE_BAND_HIGH = 70.0
SCORE_BAND_MEDIUM = 40.0