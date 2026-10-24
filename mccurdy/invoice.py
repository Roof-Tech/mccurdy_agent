"""Invoice YAML -> branded invoice PDF (deposit, progress or final billing)."""
import datetime as dt
from pathlib import Path

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .config import load_config, money
from .pdfstyle import MARGIN, PAGE, branded_table, page_decorator, palette, styles


def invoice_totals(inv: dict, cfg: dict) -> dict:
    items = inv["items"]
    subtotal = round(sum(float(i.get("quantity", 1)) * float(i["unit_price"]) for i in items), 2)
    tax_rate = float(inv.get("tax_percent", cfg["pricing"].get("sales_tax_on_materials_percent", 0)))
    taxable = round(sum(float(i.get("quantity", 1)) * float(i["unit_price"]) for i in items if i.get("taxable")), 2)
    tax = round(taxable * tax_rate / 100, 2)
    paid = round(sum(float(p["amount"]) for p in inv.get("payments", [])), 2)
    total = round(subtotal + tax, 2)
    return {"subtotal": subtotal, "tax": tax, "tax_rate": tax_rate, "total": total, "paid": paid,
            "balance": round(total - paid, 2)}


def build_invoice(inv: dict, out_path: str | Path, cfg: dict | None = None) -> Path:
    cfg = cfg or load_config()
    st = styles(cfg)
    c = palette(cfg)
    co = cfg["company"]
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    issued = dt.date.fromisoformat(str(inv.get("date", dt.date.today())))
    due = issued + dt.timedelta(days=int(inv.get("terms_days", cfg["invoice"]["payment_terms_days"])))
    number = inv["invoice_number"]
    totals = invoice_totals(inv, cfg)
    bill = inv["bill_to"]
    full_w = PAGE[0] - 2 * MARGIN

    doc = SimpleDocTemplate(str(out_path), pagesize=PAGE, leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=1.15 * inch, bottomMargin=0.85 * inch,
                            title=f"{co['name']} Invoice {number}", author=co["name"])
    s = [Spacer(1, 0.1 * inch)]

    head = Table([[
        Paragraph(f"<b>Bill to</b><br/>{bill['name']}<br/>"
                  + (f"{bill['company']}<br/>" if bill.get("company") else "")
                  + "<br/>".join(bill.get("address_lines", []))
                  + (f"<br/>{bill['email']}" if bill.get("email") else ""), st["body"]),
        Paragraph(f"<b>Job site</b><br/>{inv.get('job_site', '')}"
                  + (f"<br/>Proposal {inv['proposal_number']}" if inv.get("proposal_number") else ""), st["body"]),
        Table([["Invoice #", number], ["Issued", f"{issued:%b %d, %Y}"], ["Due", f"{due:%b %d, %Y}"],
               ["Balance due", money(totals["balance"])]],
              style=TableStyle([("FONT", (0, 0), (-1, -1), "Helvetica", 9.5),
                                ("FONT", (0, 3), (-1, 3), "Helvetica-Bold", 11),
                                ("TEXTCOLOR", (0, 3), (-1, 3), c["green"]),
                                ("ALIGN", (1, 0), (1, -1), "RIGHT")])),
    ]], colWidths=[full_w * 0.36, full_w * 0.32, full_w * 0.32])
    head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    s += [Paragraph("Invoice", st["title"]), head, Spacer(1, 0.25 * inch)]

    rows = [["Description", "Qty", "Unit price", "Amount"]]
    for i in inv["items"]:
        q = float(i.get("quantity", 1))
        rows.append([Paragraph(i["description"], st["body"]), f"{q:,.2f}".rstrip("0").rstrip("."),
                     money(float(i["unit_price"])), money(q * float(i["unit_price"]))])
    summary = [["", "", "Subtotal", money(totals["subtotal"])]]
    if totals["tax"]:
        summary.append(["", "", f"Tax ({totals['tax_rate']:g}%)", money(totals["tax"])])
    summary.append(["", "", "Total", money(totals["total"])])
    for p in inv.get("payments", []):
        summary.append(["", "", f"Paid {p.get('date', '')} {p.get('method', '')}".strip(), f"-{money(float(p['amount']))}"])
    summary.append(["", "", "Balance due", money(totals["balance"])])
    t = branded_table(rows + summary, [full_w - 3.4 * inch, 0.7 * inch, 1.2 * inch, 1.5 * inch], cfg,
                      total_rows=1)
    t.setStyle(TableStyle([("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                           ("LINEABOVE", (2, len(rows)), (-1, len(rows)), 0.8, c["blue"])]))
    s.append(t)

    s += [Spacer(1, 0.3 * inch), Paragraph("How to pay", st["h2"]),
          Paragraph(inv.get("payment_instructions", cfg["invoice"]["accepted_payments"]), st["body"]),
          Paragraph(cfg["invoice"]["late_fee_note"], st["small"]),
          Spacer(1, 0.2 * inch),
          Paragraph(f"Thank you for trusting {co['name']} with your roof. Questions about this invoice? "
                    f"Call {co['phone']} or email {co['email']}.", st["body"])]
    if inv.get("notes"):
        s += [Spacer(1, 6), Paragraph(inv["notes"], st["small"])]

    deco = page_decorator(cfg, f"INVOICE {number}")
    doc.build(s, onFirstPage=deco, onLaterPages=deco)
    return out_path
