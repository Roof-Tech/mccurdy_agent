"""Shared branded look for every McCurdy PDF (header band, footer, styles, tables)."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle

PAGE = letter
LOGO_WHITE = Path(__file__).resolve().parent.parent / "brand" / "logo-horizontal-white.png"
MARGIN = 0.75 * inch


def palette(cfg: dict) -> dict:
    return {k: colors.HexColor(v) for k, v in cfg["brand"].items()}


def styles(cfg: dict) -> dict:
    c = palette(cfg)
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=24,
                                leading=28, textColor=c["blue"], alignment=0, spaceAfter=6),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=15,
                             textColor=c["blue"], spaceBefore=14, spaceAfter=6),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11.5,
                             textColor=c["green"], spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName="Helvetica", fontSize=10,
                               leading=14, textColor=c["black"]),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontName="Helvetica", fontSize=8,
                                leading=10.5, textColor=c["gray"]),
        "right": ParagraphStyle("right", parent=base["BodyText"], fontName="Helvetica", fontSize=10,
                                alignment=TA_RIGHT),
        "bullet": ParagraphStyle("bullet", parent=base["BodyText"], fontName="Helvetica", fontSize=10,
                                 leading=14, leftIndent=12, bulletIndent=2, textColor=c["black"]),
    }


def draw_logo(canvas, x, y, size, cfg):
    """Roof-and-drop mark: a roof line over a coating drop. Drawn as vectors so it prints sharp."""
    c = palette(cfg)
    canvas.saveState()
    canvas.setLineJoin(1)
    canvas.setLineCap(1)
    canvas.setStrokeColor(c["white"])
    canvas.setLineWidth(size * 0.09)
    s = size
    p = canvas.beginPath()
    p.moveTo(x, y + s * 0.45)
    p.lineTo(x + s * 0.5, y + s * 0.9)
    p.lineTo(x + s, y + s * 0.45)
    canvas.drawPath(p, stroke=1, fill=0)
    canvas.setFillColor(c["green"])
    d = canvas.beginPath()
    d.moveTo(x + s * 0.5, y + s * 0.62)
    d.curveTo(x + s * 0.72, y + s * 0.35, x + s * 0.72, y + s * 0.08, x + s * 0.5, y + s * 0.08)
    d.curveTo(x + s * 0.28, y + s * 0.08, x + s * 0.28, y + s * 0.35, x + s * 0.5, y + s * 0.62)
    canvas.drawPath(d, stroke=0, fill=1)
    canvas.restoreState()


def page_decorator(cfg: dict, doc_label: str):
    """onPage callback: blue header band with logo + green rule, footer with license and page number."""
    c = palette(cfg)
    co = cfg["company"]
    w, h = PAGE

    def _draw(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(c["blue"])
        canvas.rect(0, h - 0.8 * inch, w, 0.8 * inch, stroke=0, fill=1)
        canvas.setFillColor(c["green"])
        canvas.rect(0, h - 0.86 * inch, w, 0.06 * inch, stroke=0, fill=1)
        if LOGO_WHITE.exists():
            logo_h = 0.62 * inch
            canvas.drawImage(str(LOGO_WHITE), MARGIN - 0.08 * inch, h - 0.72 * inch, width=logo_h * 1600 / 498,
                             height=logo_h, mask="auto")
        else:
            draw_logo(canvas, MARGIN, h - 0.68 * inch, 0.48 * inch, cfg)
            canvas.setFillColor(c["white"])
            canvas.setFont("Helvetica-Bold", 15)
            canvas.drawString(MARGIN + 0.62 * inch, h - 0.42 * inch, co["name"].upper())
            canvas.setFont("Helvetica", 8.5)
            canvas.drawString(MARGIN + 0.62 * inch, h - 0.58 * inch, co["tagline"])
        canvas.setFillColor(c["white"])
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawRightString(w - MARGIN, h - 0.47 * inch, doc_label)

        canvas.setStrokeColor(c["gray_light"])
        canvas.line(MARGIN, 0.62 * inch, w - MARGIN, 0.62 * inch)
        canvas.setFillColor(c["gray"])
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(MARGIN, 0.45 * inch,
                          f"{co['legal_name']} · CSLB Lic. #{co['license']} · {co['phone']} · {co['email']}")
        canvas.drawRightString(w - MARGIN, 0.45 * inch, f"Page {doc.page}")
        canvas.restoreState()

    return _draw


def branded_table(data, col_widths, cfg, header=True, zebra=True, total_rows=0):
    c = palette(cfg)
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, c["gray_light"]),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), c["blue"]),
                  ("TEXTCOLOR", (0, 0), (-1, 0), c["white"]),
                  ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9.5)]
    if zebra:
        start = 1 if header else 0
        for r in range(start, len(data) - total_rows):
            if (r - start) % 2 == 1:
                style.append(("BACKGROUND", (0, r), (-1, r), c["gray_light"]))
    for r in range(len(data) - total_rows, len(data)):
        style.append(("FONT", (0, r), (-1, r), "Helvetica-Bold", 10))
    if total_rows:
        style.append(("BACKGROUND", (0, -1), (-1, -1), c["green_light"]))
        style.append(("TEXTCOLOR", (0, -1), (-1, -1), c["blue"]))
    t.setStyle(TableStyle(style))
    return t
