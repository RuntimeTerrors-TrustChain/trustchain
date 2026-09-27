import sys
from pathlib import Path

# Add project root to sys.path for direct execution
sys.path.append(str(Path(__file__).resolve().parent.parent))

import io
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from config import DOCS_DIR

def generate_clean_invoice(invoice_id: str, vendor_id: str, vendor_name: str, total_amount: float) -> Path:
    """Generates a legitimate, digitally generated PDF invoice."""
    file_path = DOCS_DIR / f"{invoice_id}_clean.pdf"
    
    doc = SimpleDocTemplate(
        str(file_path), 
        pagesize=letter, 
        rightMargin=30, 
        leftMargin=30, 
        topMargin=30, 
        bottomMargin=30
    )
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(name="Title", fontName="Helvetica-Bold", fontSize=18, leading=22)
    story.append(Paragraph(f"INVOICE: {invoice_id}", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Vendor:</b> {vendor_name} (ID: {vendor_id})", styles["Normal"]))
    story.append(Paragraph("<b>Date:</b> 2026-03-15", styles["Normal"]))
    story.append(Spacer(1, 20))

    data = [
        ["Item Description", "Qty", "Unit Price (₹)", "Total (₹)"],
        ["Structural Concrete Supply (Grade M25)", "40", "4,500.00", "180,000.00"],
        ["Reinforcement Steel Bars (TMT 500D)", "25", "5,200.00", "130,000.00"],
        ["Logistics & Transport Surcharge", "1", "40,000.00", "40,000.00"],
        ["", "", "<b>Grand Total:</b>", f"<b>₹{total_amount:,.2f}</b>"]
    ]
    
    t = Table(data, colWidths=[240, 50, 100, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#BDC3C7")),
    ]))
    story.append(t)
    doc.build(story)
    return file_path

def generate_tampered_invoice_image(invoice_id: str, vendor_id: str) -> Path:
    """
    Creates an image-based invoice with a deliberately pasted/altered amount region.
    """
    img_path = DOCS_DIR / f"{invoice_id}_tampered.jpg"
    
    # Base clean canvas
    img = Image.new("RGB", (800, 1000), "white")
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([(20, 20), (780, 80)], fill=(44, 62, 80))
    draw.text((40, 35), f"COMMERCIAL INVOICE - {invoice_id}", fill=(255, 255, 255))
    draw.text((40, 110), f"Vendor ID: {vendor_id}", fill=(0, 0, 0))
    draw.text((40, 140), "Issued: 2026-03-10", fill=(0, 0, 0))
    
    draw.text((40, 220), "Procurement Supply: Industrial Cables", fill=(0, 0, 0))
    draw.text((600, 220), "₹ 150,000.00", fill=(0, 0, 0))
    
    img.save(img_path, "JPEG", quality=95)
    
    # Tampering: Paste degraded compression patch
    tampered = Image.open(img_path).convert("RGB")
    patch = Image.new("RGB", (220, 45), "white")
    p_draw = ImageDraw.Draw(patch)
    p_draw.text((10, 10), "₹ 9,850,000.00", fill=(200, 0, 0))
    
    buf = io.BytesIO()
    patch.save(buf, "JPEG", quality=60)
    buf.seek(0)
    patch_degraded = Image.open(buf)
    
    tampered.paste(patch_degraded, (560, 210))
    tampered.save(img_path, "JPEG", quality=90)
    
    return img_path

if __name__ == "__main__":
    generate_clean_invoice("INV-2026-001", "VEND-1001", "Clean Corp", 350000.0)
    generate_tampered_invoice_image("INV-2026-TAMPERED", "VEND-SHELL-CLUSTER-01-1")
    print(f"✅ Generated sample invoices in '{DOCS_DIR}'")