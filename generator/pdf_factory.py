import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import io
import random
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader, PdfWriter
from config import DOCS_DIR, GLOBAL_SEED

random.seed(GLOBAL_SEED)

def generate_clean_invoice_pdf(doc_id: str, entity_id: str, vendor_name: str, total_amount: float) -> str:
    """Generates a legitimate, digitally created PDF invoice."""
    filename = f"{doc_id}_{entity_id}.pdf"
    file_path = DOCS_DIR / filename
    
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
    story.append(Paragraph(f"TAX INVOICE: {doc_id}", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Vendor:</b> {vendor_name} (ID: {entity_id})", styles["Normal"]))
    story.append(Paragraph("<b>Date of Issue:</b> 2026-03-15", styles["Normal"]))
    story.append(Spacer(1, 20))

    data = [
        ["Item Description", "Qty", "Unit Price (₹)", "Total (₹)"],
        ["Structural Concrete Supply (Grade M25)", "40", "4,500.00", "180,000.00"],
        ["Reinforcement Steel Bars (TMT 500D)", "25", "5,200.00", "130,000.00"],
        ["Logistics & Surcharge", "1", f"{total_amount - 310000.0:,.2f}", f"{total_amount - 310000.0:,.2f}"],
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
    return filename

def generate_tampered_pdf_metadata(doc_id: str, entity_id: str, vendor_name: str, total_amount: float) -> str:
    """Generates a PDF invoice with deliberately fraudulent metadata (Photoshop producer & ModDate mismatch)."""
    clean_filename = generate_clean_invoice_pdf(f"temp_{doc_id}", entity_id, vendor_name, total_amount)
    clean_path = DOCS_DIR / clean_filename
    
    reader = PdfReader(str(clean_path))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
        
    writer.add_metadata({
        "/Producer": "Adobe Photoshop 25.2 (Windows)",
        "/Creator": "Adobe Photoshop 2026",
        "/CreationDate": "D:20260301100000Z",
        "/ModDate": "D:20260320184500Z"
    })
    
    out_filename = f"{doc_id}_{entity_id}_tampered_meta.pdf"
    out_path = DOCS_DIR / out_filename
    with open(out_path, "wb") as f:
        writer.write(f)
        
    clean_path.unlink(missing_ok=True)
    return out_filename

def generate_tampered_invoice_image(
    doc_id: str, 
    entity_id: str, 
    patch_text: str = "₹ 9,850,000.00", 
    tamper_pos: tuple = (560, 210)
) -> str:
    """Creates a JPEG invoice with a spliced low-quality patch."""
    filename = f"{doc_id}_{entity_id}_tampered.jpg"
    img_path = DOCS_DIR / filename
    
    img = Image.new("RGB", (800, 1000), "white")
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([(20, 20), (780, 80)], fill=(44, 62, 80))
    draw.text((40, 35), f"COMMERCIAL INVOICE - {doc_id}", fill=(255, 255, 255))
    draw.text((40, 110), f"Vendor ID: {entity_id}", fill=(0, 0, 0))
    draw.text((40, 140), "Issued: 2026-03-10", fill=(0, 0, 0))
    
    draw.text((40, 220), "Procurement Supply: Industrial Cables", fill=(0, 0, 0))
    draw.text((600, 220), "₹ 150,000.00", fill=(0, 0, 0))
    
    draw.text((40, 320), "Authorized Signature & Stamp:", fill=(0, 0, 0))
    draw.rectangle([(40, 350), (250, 420)], outline=(180, 180, 180), width=1)
    draw.text((60, 375), "[ Verified Official Stamp ]", fill=(100, 100, 100))
    
    # Degrade the patch heavily (quality 20)
    patch = Image.new("RGB", (220, 45), "white")
    p_draw = ImageDraw.Draw(patch)
    p_draw.text((10, 10), patch_text, fill=(180, 0, 0))
    
    buf = io.BytesIO()
    patch.save(buf, "JPEG", quality=20)
    buf.seek(0)
    patch_degraded = Image.open(buf)
    
    img.paste(patch_degraded, tamper_pos)
    # Save the composite at 98 quality so ELA recompression at 90 exposes the patch
    img.save(img_path, "JPEG", quality=98)
    return filename

def generate_clean_invoice_image(doc_id: str, entity_id: str) -> str:
    """Generates an authentic, non-tampered JPEG invoice."""
    filename = f"{doc_id}_{entity_id}_clean.jpg"
    img_path = DOCS_DIR / filename
    
    img = Image.new("RGB", (800, 1000), "white")
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([(20, 20), (780, 80)], fill=(44, 62, 80))
    draw.text((40, 35), f"COMMERCIAL INVOICE - {doc_id}", fill=(255, 255, 255))
    draw.text((40, 110), f"Vendor ID: {entity_id}", fill=(0, 0, 0))
    draw.text((40, 140), "Issued: 2026-03-10", fill=(0, 0, 0))
    draw.text((40, 220), "Procurement Supply: Certified Hardware Units", fill=(0, 0, 0))
    draw.text((600, 220), "₹ 150,000.00", fill=(0, 0, 0))
    
    img.save(img_path, "JPEG", quality=98)
    return filename