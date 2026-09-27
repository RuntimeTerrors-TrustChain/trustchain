from pathlib import Path
from typing import Dict, List, Optional, Any
from modules.forensics.ela import run_ela
from modules.forensics.metadata import analyze_pdf_metadata
from modules.forensics.benford import benfords_law_score

class DocumentForensicsEngine:
    def analyze_document(
        self, 
        file_path: Path, 
        entity_id: str, 
        vendor_historical_amounts: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        reasons: List[str] = []
        authenticity_score: float = 0.0
        hotspots: List[Dict[str, Any]] = []
        metadata_flags: List[str] = []
        heatmap_image: Optional[str] = None

        # 1. ELA analysis (for image formats)
        if file_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            _, hotspots, heatmap_file = run_ela(str(file_path))
            heatmap_image = f"/docs-media/{heatmap_file}"
            if hotspots:
                highest_intensity = max(h["intensity"] for h in hotspots)
                authenticity_score += 45.0 + (highest_intensity * 20.0)
                reasons.append(
                    f"Error Level Analysis (ELA) detected {len(hotspots)} tampered hotspot(s) (intensity: {highest_intensity})"
                )

        # 2. PDF Metadata check
        if file_path.suffix.lower() == ".pdf":
            meta_res = analyze_pdf_metadata(file_path)
            metadata_flags = meta_res["metadata_flags"]
            if meta_res["is_tampered"]:
                authenticity_score += 35.0
                reasons.extend(meta_res["reasons"])

        # 3. Benford's Law on vendor history
        benford_res = {"deviation": 0.0, "is_anomalous": False}
        if vendor_historical_amounts:
            benford_res = benfords_law_score(vendor_historical_amounts)
            if benford_res["is_anomalous"]:
                authenticity_score += 25.0
                reasons.append(
                    f"Vendor's historical invoices deviate from Benford's Law (deviation: {benford_res['deviation']})"
                )

        return {
            "document_id": file_path.stem,
            "entity_id": entity_id,
            "authenticity_score": round(min(100.0, authenticity_score), 1),
            "ela_hotspots": hotspots,
            "metadata_flags": metadata_flags,
            "benfords_deviation": benford_res["deviation"],
            "original_image": f"/docs-media/{file_path.name}" if file_path.suffix.lower() in [".jpg", ".jpeg", ".png"] else None,
            "heatmap_image": heatmap_image,
            "reasons": reasons
        }