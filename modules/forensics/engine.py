from pathlib import Path
from typing import Dict, List, Optional, Any
from modules.forensics.ela import run_ela
from modules.forensics.metadata import analyze_pdf_metadata
from modules.forensics.benford import benfords_law_score
from config import ELA_MIN_INTENSITY_THRESHOLD


class DocumentForensicsEngine:
    def analyze_document(
        self,
        file_path: Path,
        entity_id: str,
        vendor_historical_amounts: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        reasons: List[str] = []
        authenticity_score: float = 0.0
        hotspots: List[Dict[str, Any]] = []
        metadata_flags: List[str] = []
        heatmap_image: Optional[str] = None

        # 1. ELA Image Forensics
        if file_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            _, raw_hotspots, heatmap_file = run_ela(str(file_path))
            heatmap_image = f"/docs-media/{heatmap_file}"

            significant_hotspots = [
                h
                for h in raw_hotspots
                if h.get("intensity", 0) >= ELA_MIN_INTENSITY_THRESHOLD
            ]
            hotspots = significant_hotspots

            if significant_hotspots:
                highest_intensity = max(h["intensity"] for h in significant_hotspots)
                authenticity_score += 45.0 + (highest_intensity * 20.0)
                reasons.append(
                    f"Error Level Analysis (ELA) detected {len(significant_hotspots)} tampered hotspot(s) (intensity: {highest_intensity})"
                )

        # 2. PDF Metadata Inspection
        if file_path.suffix.lower() == ".pdf":
            meta_res = analyze_pdf_metadata(file_path)
            metadata_flags = meta_res["metadata_flags"]
            if meta_res["is_tampered"]:
                authenticity_score += 45.0
                reasons.extend(meta_res["reasons"])

        # 3. Benford's Law on vendor history (Per-vendor check)
        benford_res = {
            "deviation": 0.0,
            "chi_square": 0.0,
            "sample_size": 0,
            "is_anomalous": False,
        }
        if vendor_historical_amounts:
            benford_res = benfords_law_score(vendor_historical_amounts)
            if benford_res["is_anomalous"]:
                authenticity_score += 20.0
                reasons.append(
                    f"Vendor's historical amounts deviate from Benford's Law "
                    f"(chi-square {benford_res['chi_square']} over {benford_res['sample_size']} amounts)"
                )

        return {
            "document_id": file_path.stem,
            "entity_id": entity_id,
            "authenticity_score": round(min(100.0, authenticity_score), 1),
            "ela_hotspots": hotspots,
            "metadata_flags": metadata_flags,
            "benfords_deviation": benford_res["deviation"],
            "benfords_chi2": benford_res["chi_square"],
            "original_image": (
                f"/docs-media/{file_path.name}"
                if file_path.suffix.lower() in [".jpg", ".jpeg", ".png"]
                else None
            ),
            "heatmap_image": heatmap_image,
            "reasons": reasons,
        }
