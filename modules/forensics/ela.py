import io
import cv2
import numpy as np
from PIL import Image, ImageChops
from pathlib import Path
from typing import Tuple, List, Dict, Any
from config import ELA_JPEG_QUALITY, ELA_AMPLIFICATION_SCALE, ELA_HOTSPOT_PERCENTILE, DOCS_DIR

def run_ela(
    image_path: str, 
    quality: int = ELA_JPEG_QUALITY, 
    scale: int = ELA_AMPLIFICATION_SCALE
) -> Tuple[np.ndarray, List[Dict[str, Any]], str]:
    """
    Performs Error Level Analysis (ELA) to detect spliced/edited regions.
    Returns:
      1. diff_array
      2. bounding box hotspots
      3. filename of the saved colored heatmap visual
    """
    original = Image.open(image_path).convert("RGB")
    
    # Re-save to in-memory buffer at known compression
    buffer = io.BytesIO()
    original.save(buffer, "JPEG", quality=quality)
    buffer.seek(0)
    resaved = Image.open(buffer)
    
    diff = ImageChops.difference(original, resaved)
    diff_array = np.array(diff, dtype=np.float64) * scale
    diff_array = np.clip(diff_array, 0, 255).astype(np.uint8)

    gray_diff = cv2.cvtColor(diff_array, cv2.COLOR_RGB2GRAY)
    
    # Threshold at percentile
    threshold_value = float(np.percentile(np.asarray(gray_diff), ELA_HOTSPOT_PERCENTILE))
    _, thresh = cv2.threshold(gray_diff, int(threshold_value), 255, cv2.THRESH_BINARY)
    
    contours_found = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours_found[0] if len(contours_found) == 2 else contours_found[1]
    
    hotspots: List[Dict[str, Any]] = []
    h, w = gray_diff.shape[:2]
    total_area = float(h * w)
    
    # Create colored heatmap visual for presentation
    color_heatmap = cv2.applyColorMap(gray_diff, cv2.COLORMAP_JET)
    
    for cnt in contours:
        area = float(cv2.contourArea(cnt))
        if 150.0 < area < (total_area * 0.25):
            x, y, bw, bh = cv2.boundingRect(cnt)
            roi = np.asarray(gray_diff[y:y+bh, x:x+bw])
            intensity = float(np.mean(roi) / 255.0) if roi.size > 0 else 0.0
            
            # Draw red bounding boxes on the color heatmap
            cv2.rectangle(color_heatmap, (x, y), (x + bw, y + bh), (0, 0, 255), 2)
            
            hotspots.append({
                "bbox": [int(y), int(x), int(y + bh), int(x + bw)],
                "intensity": round(intensity, 2)
            })

    # Save heatmap visual to documents folder for UI serving
    src_p = Path(image_path)
    heatmap_filename = f"{src_p.stem}_ela_heatmap.png"
    heatmap_path = DOCS_DIR / heatmap_filename
    cv2.imwrite(str(heatmap_path), color_heatmap)

    return diff_array, hotspots, heatmap_filename