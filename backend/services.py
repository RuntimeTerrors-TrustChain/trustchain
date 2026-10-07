import json
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from config import RAW_DATA_DIR, DOCS_DIR, DOCUMENTS_MAP_FILE
from modules.graph.engine import GraphIntelligenceEngine
from modules.forensics.engine import DocumentForensicsEngine
from modules.scoring.fusion import compute_combined_risk_score

import csv
import io
import hashlib
from rapidfuzz import fuzz

graph_engine = GraphIntelligenceEngine()
forensics_engine = DocumentForensicsEngine()
_node_risk_cache: Dict[str, str] = {}


def get_all_entities() -> List[Dict[str, Any]]:
    with open(RAW_DATA_DIR / "entities.json", "r", encoding="utf-8") as f:
        return json.load(f)


def get_entity_by_id(entity_id: str) -> Optional[Dict[str, Any]]:
    entities = get_all_entities()
    for e in entities:
        if e.get("entity_id") == entity_id:
            return e
    return None


def get_entity_documents(entity_id: str) -> List[Dict[str, Any]]:
    if not DOCUMENTS_MAP_FILE.exists():
        return []
    with open(DOCUMENTS_MAP_FILE, "r", encoding="utf-8") as f:
        docs = json.load(f)
    return [d for d in docs if d.get("entity_id") == entity_id]


def analyze_vendor_document(
    file_path: Path, entity_id: Optional[str] = None
) -> Dict[str, Any]:
    amounts = []
    if entity_id:
        with open(RAW_DATA_DIR / "transactions.json", "r", encoding="utf-8") as f:
            txns = json.load(f)
        amounts = [
            t.get("amount", 0.0)
            for t in txns
            if t.get("from_entity") == entity_id or t.get("to_entity") == entity_id
        ]

    return forensics_engine.analyze_document(
        file_path=file_path,
        entity_id=entity_id or "UNASSIGNED",
        vendor_historical_amounts=amounts,
    )


def analyze_vendor_graph(entity_id: str) -> Dict[str, Any]:
    return graph_engine.analyze_entity(entity_id)


def get_full_vendor_risk_assessment(
    entity_id: str, document_name: Optional[str] = None
) -> Dict[str, Any]:
    graph_res = analyze_vendor_graph(entity_id)

    doc_res = {
        "document_id": "NONE",
        "entity_id": entity_id,
        "authenticity_score": 0.0,
        "ela_hotspots": [],
        "metadata_flags": [],
        "benfords_deviation": 0.0,
        "original_image": None,
        "heatmap_image": None,
        "reasons": [],
    }

    mapped_docs = get_entity_documents(entity_id)
    target_doc = None
    if document_name:
        target_doc = DOCS_DIR / document_name
    elif mapped_docs and mapped_docs[0].get("filename"):
        target_doc = DOCS_DIR / mapped_docs[0]["filename"]

    if target_doc and target_doc.is_file():
        doc_res = analyze_vendor_document(target_doc, entity_id)

    fused = compute_combined_risk_score(doc_res, graph_res)
    fused["original_image"] = doc_res.get("original_image")
    fused["heatmap_image"] = doc_res.get("heatmap_image")
    fused["ela_hotspots"] = doc_res.get("ela_hotspots", [])
    fused["benfords_deviation"] = doc_res.get("benfords_deviation", 0.0)

    # Forward all underlying engine keys safely
    fused["authenticity_score"] = doc_res.get("authenticity_score", 0.0)
    fused["metadata_flags"] = doc_res.get("metadata_flags", [])
    fused["cluster_id"] = graph_res.get("cluster_id")
    fused["cluster_density"] = graph_res.get("cluster_density", 0.0)
    fused["cluster_size"] = graph_res.get("cluster_size", 1)
    fused["structuring_flag"] = graph_res.get("structuring_flag", False)
    fused["cycles_involved"] = graph_res.get("cycles_involved", [])

    _node_risk_cache[entity_id] = fused.get("risk_band", "LOW")
    return fused


def get_vis_graph_data() -> Dict[str, Any]:
    G = graph_engine.G
    clusters = getattr(graph_engine, "shell_clusters", [])

    node_cluster_map = {}
    for cl in clusters:
        for m in cl.get("members", []):
            node_cluster_map[m] = cl.get("cluster_id", "CLUSTER")

    nodes = []
    for node_id, data in G.nodes(data=True):
        cluster_id = node_cluster_map.get(node_id)
        if node_id not in _node_risk_cache:
            assessment = get_full_vendor_risk_assessment(node_id)
            _node_risk_cache[node_id] = assessment.get("risk_band", "LOW")

        real_band = _node_risk_cache.get(node_id, "LOW")
        nodes.append(
            {
                "id": node_id,
                "label": data.get("name", node_id),
                "risk_band": real_band,
                "group": cluster_id or "CLEAN",
            }
        )

    # 1. Corporate Attribute Edges (Red Cartel Links)
    edges = []
    seen_pairs = set()

    for u, v, d in G.edges(data=True):
        pair = tuple(sorted([u, v]))
        seen_pairs.add(pair)
        edges.append(
            {
                "from": u,
                "to": v,
                "label": f"{d.get('shared_field')}: {str(d.get('shared_value'))[:15]}...",
                "edge_type": "shared_attribute",
            }
        )

    # 2. Add Clean Commercial Trade Links across Green Nodes (No duplicate clutter)
    with open(RAW_DATA_DIR / "transactions.json", "r", encoding="utf-8") as f:
        txns = json.load(f)

    for t in txns:
        u = t.get("from_entity")
        v = t.get("to_entity")
        if u and v and u != v:
            pair = tuple(sorted([u, v]))
            if (
                pair not in seen_pairs and len(seen_pairs) < 220
            ):  # Curated limit for pristine visual density
                seen_pairs.add(pair)
                edges.append(
                    {
                        "from": u,
                        "to": v,
                        "label": f"Trade: Rs. {t.get('amount', 0):,.0f}",
                        "edge_type": "transaction",
                    }
                )

    return {"nodes": nodes, "edges": edges}


def _draw_real_cluster_thumbnail(entity_id: str, path: Path):
    """Draws a real NetworkX subgraph showing actual cluster geometry and inspected node."""
    G = graph_engine.G
    clusters = getattr(graph_engine, "shell_clusters", [])
    cl = next((c for c in clusters if entity_id in c.get("members", [])), None)

    fig = plt.figure(figsize=(4, 3), facecolor="#090D16")
    if cl and len(cl.get("members", [])) > 0:
        sub = G.subgraph(cl.get("members", []))
        pos = nx.circular_layout(sub)
        nx.draw_networkx_edges(sub, pos, edge_color="#EF4444", width=2)
        node_colors = ["#38BDF8" if n == entity_id else "#EF4444" for n in sub.nodes()]
        nx.draw_networkx_nodes(sub, pos, node_size=600, node_color=node_colors)
        labels = {n: str(n)[-4:] for n in sub.nodes()}
        nx.draw_networkx_labels(
            sub,
            pos,
            labels=labels,
            font_size=8,
            font_color="white",
            font_family="sans-serif",
        )
        density_val = cl.get("density", 0.0)
        plt.title(
            f"Shell Cluster: {len(cl.get('members', []))} Linked Entities (Density: {density_val})",
            color="#F8FAFC",
            fontsize=8.5,
            pad=10,
        )
    else:
        plt.text(
            0.5,
            0.5,
            "Independent Entity\nNo Shell Cluster Linkages",
            color="#94A3B8",
            ha="center",
            va="center",
            fontsize=9.5,
        )

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(str(path), dpi=100, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def generate_audit_dossier_pdf(entity_id: str) -> Path:
    """Generates an auditable 2-page investigation PDF report."""
    assessment = get_full_vendor_risk_assessment(entity_id)
    entity = get_entity_by_id(entity_id) or {
        "name": "Unknown Entity",
        "registered_address": "N/A",
        "director_names": ["N/A"],
        "bank_account": "N/A",
    }

    pdf_filename = f"Audit_Dossier_{entity_id}.pdf"
    pdf_path = DOCS_DIR / pdf_filename

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()
    story = []

    # Title Header
    header_style = ParagraphStyle(
        name="Header",
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=21,
        textColor=colors.HexColor("#0F172A"),
    )
    sub_style = ParagraphStyle(
        name="Sub",
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#64748B"),
    )

    story.append(Paragraph("OFFICIAL AUDIT DOSSIER", header_style))
    story.append(
        Paragraph(
            f"Procurement Screening &amp; Fraud Investigation Report &bull; Case ID: TC-2026-{escape(str(entity_id)[-4:])} &bull; Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            sub_style,
        )
    )
    story.append(Spacer(1, 12))

    # Vendor Profile Table (plain strings, so no XML escaping here)
    vendor_data = [
        ["Target Vendor:", str(entity.get("name", "")), "Vendor ID:", str(entity_id)],
        [
            "Registered Address:",
            str(entity.get("registered_address", ""))[:45] + "...",
            "Bank Account:",
            str(entity.get("bank_account", "")),
        ],
        [
            "Directors:",
            ", ".join(entity.get("director_names", [])),
            "Classification:",
            f"{assessment.get('risk_band', 'LOW')} RISK",
        ],
    ]
    t_vend = Table(vendor_data, colWidths=[110, 210, 80, 140])
    t_vend.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(t_vend)
    story.append(Spacer(1, 10))

    # Risk Score Bar
    risk_band = assessment.get("risk_band", "LOW")
    score_color = (
        colors.HexColor("#EF4444")
        if risk_band == "HIGH"
        else (
            colors.HexColor("#F59E0B")
            if risk_band == "MEDIUM"
            else colors.HexColor("#10B981")
        )
    )
    score_data = [
        [
            f"FINAL RISK SCORE: {assessment.get('final_risk_score', 0.0)} / 100",
            f"BAND: {risk_band} RISK",
            f"Base: {assessment.get('base_score', 0.0)} | Escalation: +{assessment.get('escalation_applied', 0.0)}",
        ]
    ]
    t_score = Table(score_data, colWidths=[200, 160, 180])
    t_score.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), score_color),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t_score)
    story.append(Spacer(1, 12))

    # Real Subgraph & ELA Side-by-Side Images
    story.append(
        Paragraph("<b>FORENSIC &amp; NETWORK TOPOLOGY EVIDENCE:</b>", styles["Normal"])
    )
    story.append(Spacer(1, 6))

    img_elements = []
    if assessment.get("heatmap_image"):
        heatmap_p = DOCS_DIR / Path(assessment["heatmap_image"]).name
        if heatmap_p.exists():
            img_elements.append(RLImage(str(heatmap_p), width=250, height=170))

    graph_thumb_path = DOCS_DIR / f"thumb_graph_{entity_id}.png"
    _draw_real_cluster_thumbnail(entity_id, graph_thumb_path)
    if graph_thumb_path.exists():
        img_elements.append(RLImage(str(graph_thumb_path), width=250, height=170))

    if len(img_elements) == 2:
        img_table = Table(
            [
                [img_elements[0], img_elements[1]],
                [
                    "Figure 1: ELA Compression Heatmap",
                    "Figure 2: Real Subgraph Topology",
                ],
            ],
            colWidths=[270, 270],
        )
        img_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTSIZE", (0, 1), (-1, 1), 7.5),
                    ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#64748B")),
                ]
            )
        )
        story.append(img_table)
    elif len(img_elements) == 1:
        story.append(img_elements[0])

    story.append(Spacer(1, 10))

    # Primary Findings
    story.append(
        Paragraph("<b>AUDIT TRAIL &amp; DETECTION FINDINGS:</b>", styles["Normal"])
    )
    story.append(Spacer(1, 4))
    for r in assessment.get("reasons", []):
        safe_reason = escape(str(r).replace("₹", "Rs. "))
        story.append(Paragraph(f"&bull; {safe_reason}", styles["Normal"]))
        story.append(Spacer(1, 2))

    story.append(PageBreak())

    # PAGE 2: Statutory Compliance Breakdown
    story.append(Paragraph("STATUTORY &amp; LEGAL INDICATORS ANALYSIS", header_style))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "Cross-referenced against current Indian corporate, anti-money laundering, competition, and criminal statutes:",
            sub_style,
        )
    )
    story.append(Spacer(1, 10))

    has_bns_tamper = (
        assessment.get("authenticity_score", 0.0) >= 40.0
        or len(assessment.get("metadata_flags", [])) > 0
    )
    has_pmla_struct = bool(assessment.get("structuring_flag"))
    has_cycle_laundering = len(assessment.get("cycles_involved", [])) > 0
    has_bid_rigging = (
        assessment.get("cluster_density", 0.0) >= 0.5
        or assessment.get("cluster_size", 1) >= 3
    )
    has_general_fraud = risk_band == "HIGH" or has_bns_tamper or has_bid_rigging

    legal_data = [
        ["Statutory Framework", "Applicable Legal Subject", "Analytical Status"],
        [
            "Competition Act, 2002 s.3(3)(d)",
            "Collusive Bid-Rigging & Tender Price Manipulation",
            "Indicator present" if has_bid_rigging else "No indicator found",
        ],
        [
            "Companies Act, 2013 s.447",
            "Corporate Fraud & Material Misrepresentation",
            "Indicator present" if has_general_fraud else "No indicator found",
        ],
        [
            "PMLA, 2002 s.3",
            "Offence of Money Laundering & Structuring Evasion",
            (
                "Indicator present"
                if (has_pmla_struct or has_cycle_laundering)
                else "No indicator found"
            ),
        ],
        [
            "Bharatiya Nyaya Sanhita (BNS) s.336",
            "Forgery of Commercial Invoices & Digital Documents",
            "Indicator present" if has_bns_tamper else "No indicator found",
        ],
        [
            "Bharatiya Nyaya Sanhita (BNS) s.340",
            "Using Forged Electronic Document as Genuine",
            "Indicator present" if has_bns_tamper else "No indicator found",
        ],
    ]
    t_legal = Table(legal_data, colWidths=[185, 255, 100])
    t_legal.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t_legal)
    story.append(Spacer(1, 16))

    # Recommended Action
    action_text = "<b>RECOMMENDED AUDIT ACTION:</b><br/>"
    if risk_band == "HIGH":
        action_text += "<font color='#B91C1C'><b>RECOMMEND HOLD PENDING HUMAN REVIEW:</b> Place temporary administrative hold on bid award. Flag applicant for priority manual review by the Tender Committee before financial disbursement.</font>"
    elif risk_band == "MEDIUM":
        action_text += "<font color='#D97706'><b>SECONDARY VERIFICATION:</b> Request original notarized bank guarantees. Issue clarification notice regarding shared director/address linkages.</font>"
    else:
        action_text += "<font color='#15803D'><b>CLEAR FOR EVALUATION:</b> Vendor exhibits independent ownership and compliant financial distributions. No systemic fraud signals identified.</font>"

    t_action = Table([[Paragraph(action_text, styles["Normal"])]], colWidths=[540])
    t_action.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    (
                        colors.HexColor("#FEF2F2")
                        if risk_band == "HIGH"
                        else colors.HexColor("#F0FDF4")
                    ),
                ),
                ("BOX", (0, 0), (-1, -1), 1, score_color),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(t_action)
    story.append(Spacer(1, 35))

    # Neutral Review Signatures
    sig_data = [
        [
            "____________________________________",
            "____________________________________",
        ],
        ["Forensic Screening System", "Procurement Review Auditor"],
        ["TrustChain Verification Engine", "Internal Audit & Evaluation Division"],
    ]
    t_sig = Table(sig_data, colWidths=[270, 270])
    t_sig.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#475569")),
            ]
        )
    )
    story.append(KeepTogether(t_sig))

    story.append(Spacer(1, 15))
    story.append(
        Paragraph(
            "<i>Notice: This dossier is an automated analytical screening aid. It is intended for audit triaging and does not constitute a definitive judicial finding.</i>",
            ParagraphStyle(
                name="Footnote",
                fontName="Helvetica-Oblique",
                fontSize=7,
                leading=9,
                textColor=colors.HexColor("#94A3B8"),
                alignment=1,
            ),
        )
    )

    doc.build(story)
    return pdf_path


def generate_sample_bidding_csv() -> str:
    """Generates a realistic sample GeM tender bidding sheet with a planted collusion ring."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "tender_id",
            "company_name",
            "cin_llpin",
            "director_names",
            "director_dins",
            "registered_address",
            "gstin",
            "bank_account",
            "quoted_amount_inr",
        ]
    )
    # Planted collusion: Bidder 1 & Bidder 3 secretly share Director Rajesh Sharma (DIN: 08912345) and Okhla address!
    writer.writerow(
        [
            "GEM/2026/B/8941",
            "Apex Tech Infra Solutions Pvt Ltd",
            "U72200DL2023PTC123456",
            "Rajesh Kumar Sharma; Anit Verma",
            "08912345; 09123456",
            "Unit 102, Sector 18, Okhla Ind Area, New Delhi - 110020",
            "07AAAAA0000A1Z5",
            "HDFC000123456789",
            "14500000.00",
        ]
    )
    writer.writerow(
        [
            "GEM/2026/B/8941",
            "BlueSky LogiCorp LLP",
            "AAH1234",
            "Sunil Narang",
            "07654321",
            "Unit 404, Sector 62, Noida, Uttar Pradesh - 201301",
            "09BBBBB1111B1Z2",
            "ICIC000987654321",
            "14800000.00",
        ]
    )
    writer.writerow(
        [
            "GEM/2026/B/8941",
            "Zenith Digital Power Pvt Ltd",
            "U40100DL2024PTC654321",
            "Rajesh Kumar Sharma; Priya Sen",
            "08912345; 06543210",
            "Unit 102, Sector 18, Okhla Ind Area, New Delhi - 110020",
            "07CCCCC2222C1Z9",
            "HDFC000123456789",
            "14200000.00",
        ]
    )
    writer.writerow(
        [
            "GEM/2026/B/8941",
            "Kavita Infrastructure Works Ltd",
            "L45200MH2021PLC789012",
            "Kavita Deshmukh; Rohan Mehta",
            "01234567; 02345678",
            "Plot 88, MIDC Industrial Area, Andheri East, Mumbai - 400093",
            "27DDDDD3333D1Z6",
            "SBIN000555666777",
            "15100000.00",
        ]
    )
    return output.getvalue()


def ingest_and_screen_cohort_csv(csv_content: str) -> Dict[str, Any]:
    """
    Parses uploaded tender bids, runs regulatory syntax checks, hashes bank data,
    adds nodes into graph memory, and performs intra-cohort collusion screening.
    """
    f = io.StringIO(csv_content.strip())
    reader = csv.DictReader(f)

    rows = list(reader)
    if not rows:
        return {
            "tender_id": "UNKNOWN",
            "bidders_count": 0,
            "collusion_detected": False,
            "collusion_flags": [],
            "syntax_validation_errors": ["Empty CSV file"],
            "message": "No data found",
        }

    tender_id = rows[0].get("tender_id", "GEM/2026/TENDER")
    syntax_errors = []
    parsed_bidders = []

    # 1. Pre-Flight Syntax & Format Validation
    for idx, row in enumerate(rows, 1):
        name = row.get("company_name", f"Bidder {idx}").strip()
        gstin = row.get("gstin", "").strip()
        cin = row.get("cin_llpin", "").strip()
        dins = [d.strip() for d in row.get("director_dins", "").split(";") if d.strip()]
        directors = [
            d.strip() for d in row.get("director_names", "").split(";") if d.strip()
        ]
        address = row.get("registered_address", "").strip()
        bank = row.get("bank_account", "").strip()

        # Validate GSTIN structure (15 chars, 'Z' at pos 13)
        if gstin and (len(gstin) != 15 or gstin[13] != "Z"):
            syntax_errors.append(
                f"Row {idx} ({name}): Invalid GSTIN format '{gstin}' (must be 15 chars with 'Z' at 14th pos)"
            )

        # Privacy-Preserving Bank Hashing (Salted SHA-256)
        bank_hash = (
            hashlib.sha256(f"TRUSTCHAIN_SALT_{bank}".encode()).hexdigest()[:12]
            if bank
            else f"HASH_{idx}"
        )

        eid = f"BID-{idx:02d}-{name[:4].upper()}"
        parsed_bidders.append(
            {
                "entity_id": eid,
                "name": name,
                "cin": cin,
                "directors": directors,
                "dins": dins,
                "address": address,
                "bank_hash": bank_hash,
                "quoted_amount": row.get("quoted_amount_inr", "0.0"),
            }
        )

        # Add temporary node to in-memory Graph
        graph_engine.G.add_node(
            eid,
            name=name,
            directors=directors,
            address=address,
            phone="",
            bank_account=bank_hash,
        )

    # 2. Intra-Cohort Collusion Screening (Bid-Rigging Analysis)
    collusion_flags = []
    n = len(parsed_bidders)

    for i in range(n):
        b1 = parsed_bidders[i]
        for j in range(i + 1, n):
            b2 = parsed_bidders[j]

            # Check 1: Shared Director DIN
            shared_dins = set(b1["dins"]).intersection(set(b2["dins"]))
            if shared_dins:
                val = list(shared_dins)[0]
                collusion_flags.append(
                    {
                        "bidder_a": b1["name"],
                        "bidder_b": b2["name"],
                        "shared_attribute": "Director DIN",
                        "attribute_value": f"Shared DIN: {val}",
                        "risk_level": "CRITICAL",
                        "statutory_violation": "Competition Act, 2002 s.3(3)(d) (Collusive Bidding)",
                    }
                )
                graph_engine.G.add_edge(
                    b1["entity_id"],
                    b2["entity_id"],
                    shared_field="director_din",
                    shared_value=val,
                )

            # Check 2: Shared Bank Account Hash
            if b1["bank_hash"] == b2["bank_hash"] and b1["bank_hash"] != "":
                collusion_flags.append(
                    {
                        "bidder_a": b1["name"],
                        "bidder_b": b2["name"],
                        "shared_attribute": "Common Bank Account",
                        "attribute_value": "Identical Bank Account Hash Detected",
                        "risk_level": "HIGH",
                        "statutory_violation": "PMLA, 2002 & Public Procurement Rules",
                    }
                )
                graph_engine.G.add_edge(
                    b1["entity_id"],
                    b2["entity_id"],
                    shared_field="bank_account",
                    shared_value="Common Bank",
                )

            # Check 3: Address Fuzzy Match (>88%)
            if b1["address"] and b2["address"]:
                ratio = fuzz.token_sort_ratio(b1["address"], b2["address"])
                if ratio >= 88.0:
                    collusion_flags.append(
                        {
                            "bidder_a": b1["name"],
                            "bidder_b": b2["name"],
                            "shared_attribute": "Registered Office",
                            "attribute_value": f"Address Similarity: {ratio:.0f}%",
                            "risk_level": "HIGH",
                            "statutory_violation": "Shell Network & Physical Location Sharing",
                        }
                    )
                    graph_engine.G.add_edge(
                        b1["entity_id"],
                        b2["entity_id"],
                        shared_field="registered_address",
                        shared_value=b1["address"][:20],
                    )

    is_collusive = len(collusion_flags) > 0
    return {
        "tender_id": tender_id,
        "bidders_count": len(parsed_bidders),
        "collusion_detected": is_collusive,
        "collusion_flags": collusion_flags,
        "syntax_validation_errors": syntax_errors,
        "message": f"Screened {len(parsed_bidders)} bidders for {tender_id}. {len(collusion_flags)} collusion link(s) intercepted.",
    }
