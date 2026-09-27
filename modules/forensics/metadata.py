from pypdf import PdfReader
from typing import Dict, List
from pathlib import Path

def analyze_pdf_metadata(file_path: Path) -> Dict:
    """
    Examines PDF metadata headers for tamper indicators.
    """
    flags = []
    reasons = []

    try:
        reader = PdfReader(str(file_path))
        meta = reader.metadata or {}

        producer = str(meta.get("/Producer", "")).lower()
        creator = str(meta.get("/Creator", "")).lower()
        creation_date = meta.get("/CreationDate", "")
        mod_date = meta.get("/ModDate", "")

        # 1. Suspicious photo-editing software on official invoices
        suspicious_producers = ["photoshop", "gimp", "canva", "illustrator", "inkscape"]
        for sp in suspicious_producers:
            if sp in producer or sp in creator:
                flags.append("producer_mismatch")
                reasons.append(f"Document produced using image-editing software: '{producer or creator}'")
                break

        # 2. Significant modification timestamp mismatch
        if creation_date and mod_date and (creation_date != mod_date):
            flags.append("moddate_after_creationdate")
            reasons.append("Document was modified after initial creation timestamp")

        return {
            "metadata_flags": flags,
            "reasons": reasons,
            "is_tampered": len(flags) > 0
        }

    except Exception:
        # Fallback for image files (.jpg/.png)
        return {"metadata_flags": [], "reasons": [], "is_tampered": False}