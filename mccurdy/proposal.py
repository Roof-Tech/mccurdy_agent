"""Job YAML -> branded, signable proposal PDF."""
import datetime as dt
from pathlib import Path

from reportlab.lib.units import inch
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .config import load_config, money
from .pdfstyle import MARGIN, PAGE, branded_table, page_decorator, palette, styles
from .pricing import build_options, payment_schedule, replacement_comparison
from .signature import SignatureBlock

DEFAULT_SCOPE = [
    "Safety setup: fall-protection plan, rooftop access control and daily site cleanup.",
    "Inspect and core-sample the roof; mark and replace wet or damaged insulation found.",
    "Power-wash the full roof surface and let it dry completely.",
    "Repair seams, blisters, splits and flashings; reinforce penetrations, drains and transitions with fabric.",
    "Apply primer where the substrate needs it (adhesion-tested first).",
    "Apply the silicone coating system in multiple passes to the specified dry-mil thickness.",
    "Mil-gauge check across the roof, final walk-through with owner and photo documentation.",
    "Register the manufacturer warranty and hand over the warranty and maintenance packet.",
]

# Business & Professions Code §7030 notice for California contracts.
CSLB_NOTICE = ("Contractors are required by law to be licensed and regulated by the Contractors' State License Board "
               "which has jurisdiction to investigate complaints against contractors if a complaint regarding a patent "
               "act or omission is filed within four years of the date of the alleged violation. A complaint regarding "
               "a latent act or omission pertaining to structural defects must be filed within 10 years of the date of "
               "the alleged violation. Any questions concerning a contractor may be referred to the Registrar, "
               "Contractors' State License Board, P.O. Box 26000, Sacramento, California 95826.")

DEFAULT_TERMS = [
    "Pricing is valid for {valid} days from the proposal date.",
    "Work is scheduled when the weather allows; coatings are not applied in rain, dew or below the manufacturer's minimum temperature.",
    "Any hidden conditions found during work (wet insulation, deck damage) will be shown to the owner and priced in writing before that work is done.",
    "{name} carries general liability and workers' compensation insurance; certificates are available on request.",
    "Warranty is subject to final payment and the manufacturer's terms.",
]


def _p(text, st):
    return Paragraph(str(text), st)


def _bullets(items, st):
    return [Paragraph(str(i), st["bullet"], bulletText="•") for i in items]


def _choice_table(rows, full_w, cfg):
    """Option list with an empty tick box per row (prints and fills cleanly; no special glyphs needed)."""
    t = branded_table(rows, [0.3 * inch, full_w - 1.9 * inch, 1.6 * inch], cfg, header=False, zebra=False)
    box = palette(cfg)["blue"]
    t.setStyle(TableStyle([("ALIGN", (2, 0), (2, -1), "RIGHT")]
                          + [("BOX", (0, r), (0, r), 0.9, box) for r in range(len(rows))]))
    return t


def build_proposal(job: dict, out_path: str | Path, cfg: dict | None = None) -> Path:
    cfg = cfg or load_config()
    st = styles(cfg)
    c = palette(cfg)
    co = cfg["company"]
    pricing = cfg["pricing"]
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    customer = job["customer"]
    prop = job["property"]
    date = dt.date.fromisoformat(str(job.get("date", dt.date.today())))
    valid_until = date + dt.timedelta(days=int(pricing["proposal_valid_days"]))
    number = job.get("proposal_number", f"MCC-{date:%Y%m%d}")
    options = build_options(job, pricing)
    recommended = next((o for o in options if o.recommended), options[-1])
    comparison = replacement_comparison(job, pricing, recommended)

    doc = SimpleDocTemplate(str(out_path), pagesize=PAGE, leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=1.15 * inch, bottomMargin=0.85 * inch,
                            title=f"{co['name']} Proposal {number}", author=co["name"],
                            subject=f"Roof renewal proposal for {prop['address']}")
    full_w = PAGE[0] - 2 * MARGIN
    s = []

    # ── Cover ──
    s += [Spacer(1, 0.2 * inch), _p("Commercial Roof Renewal Proposal", st["title"]),
          _p(f"Prepared for <b>{customer['name']}</b>"
             + (f", {customer['company']}" if customer.get("company") else ""), st["body"]),
          Spacer(1, 0.15 * inch)]
    facts = [
        ["Property", prop["address"]],
        ["Roof area", f"{float(job['roof']['square_feet']):,.0f} sq ft"
                      + (f" · existing {job['roof']['existing_type']}" if job["roof"].get("existing_type") else "")],
        ["Proposal #", number],
        ["Date", f"{date:%B %d, %Y}"],
        ["Valid until", f"{valid_until:%B %d, %Y}"],
        ["Prepared by", f"{job.get('estimator', co['signer_name'])} · {co['phone']}"],
    ]
    s.append(branded_table(facts, [1.4 * inch, full_w - 1.4 * inch], cfg, header=False))
    s.append(Spacer(1, 0.2 * inch))

    # Big recommendation call-out
    callout = Table([[
        _p(f"<font color='{cfg['brand']['white']}' size=9>OUR RECOMMENDATION</font><br/>"
           f"<font color='{cfg['brand']['white']}' size=14><b>{recommended.name}</b></font><br/>"
           f"<font color='{cfg['brand']['white']}' size=10>{recommended.warranty_years}-year warranty · "
           f"{recommended.dry_mils} dry mils · {money(recommended.total)}</font>", st["body"]),
        _p(f"<font color='{cfg['brand']['white']}' size=9>VS. TEAR-OFF &amp; REPLACE</font><br/>"
           f"<font color='{cfg['brand']['white']}' size=14><b>Save {money(comparison['savings'])}</b></font><br/>"
           f"<font color='{cfg['brand']['white']}' size=10>about {comparison['savings_percent']:g}% less, "
           f"no tear-off, no business shutdown</font>", st["body"]),
    ]], colWidths=[full_w * 0.55, full_w * 0.45])
    callout.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), c["blue"]), ("BACKGROUND", (1, 0), (1, 0), c["green"]),
        ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    s += [callout, Spacer(1, 0.2 * inch)]

    if job.get("summary"):
        s += [_p("Summary", st["h1"]), _p(job["summary"], st["body"])]

    # ── Condition ──
    if job.get("condition") or job.get("key_issues"):
        s.append(_p("What We Found", st["h1"]))
        if job.get("condition"):
            s.append(_p(job["condition"], st["body"]))
        if job.get("key_issues"):
            s.append(_p("Key issues", st["h2"]))
            s += _bullets(job["key_issues"], st)

    # ── Photos ──
    photos = [ph for ph in job.get("photos", []) if Path(ph["path"]).exists()]
    if photos:
        s.append(_p("Inspection Photos", st["h1"]))
        cells, row = [], []
        cell_w = (full_w - 0.2 * inch) / 2
        for ph in photos:
            img = Image(ph["path"])
            ratio = img.imageHeight / float(img.imageWidth)
            img.drawWidth, img.drawHeight = cell_w, min(cell_w * ratio, 2.6 * inch)
            row.append([img, _p(ph.get("caption", ""), st["small"])])
            if len(row) == 2:
                cells.append(row)
                row = []
        if row:
            cells.append(row + [""])
        grid = Table(cells, colWidths=[cell_w + 0.1 * inch] * 2)
        grid.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        s.append(grid)

    # ── Scope ──
    s += [_p("Scope of Work", st["h1"])]
    s += _bullets(job.get("scope", DEFAULT_SCOPE), st)

    # ── Options ──
    s += [_p("Investment Options", st["h1"]),
          _p("Every option is a full silicone restoration over your existing roof. Thicker systems carry longer "
             "manufacturer warranties.", st["body"]), Spacer(1, 0.1 * inch)]
    rows = [["Option", "Dry mils", "Warranty", "Investment", "$ / sq ft"]]
    sqft = float(job["roof"]["square_feet"])
    for o in options:
        label = (f"<b>{o.name}</b><br/><font color='{cfg['brand']['green']}' size=8><b>RECOMMENDED</b></font>"
                 if o.recommended else o.name)
        rows.append([_p(label, st["body"]), str(o.dry_mils),
                     f"{o.warranty_years} yrs", money(o.total), f"${o.total / sqft:,.2f}"])
    tbl = branded_table(rows, [3.0 * inch, 0.8 * inch, 0.9 * inch, 1.2 * inch, full_w - 5.9 * inch], cfg)
    rec_row = 1 + options.index(recommended)
    tbl.setStyle(TableStyle([("BACKGROUND", (0, rec_row), (-1, rec_row), c["green_light"]),
                             ("ALIGN", (1, 0), (-1, -1), "RIGHT")]))
    s.append(tbl)

    if job.get("add_ons"):
        s.append(_p("Included in every option", st["h2"]))
        s += _bullets([f"{a['description']} — {money(float(a.get('quantity', 1)) * float(a['unit_price']))}"
                       for a in job["add_ons"]], st)

    # ── Comparison ──
    s.append(_p("Renewal vs. Replacement", st["h1"]))
    comp = [["", "Tear-off & replace", f"McCurdy renewal ({recommended.key.title()})"],
            ["Estimated cost", money(comparison["replacement_cost"]), money(comparison["coating_cost"])],
            ["Business disruption", "Weeks of noise, debris, open roof", "Building stays open"],
            ["Landfill waste", "Old roof hauled to landfill", "Existing roof stays in place"],
            ["Energy", "Depends on new membrane", "Reflective white surface lowers roof temperature"],
            ["Future", "Start over at end of life", "Re-coat to extend life again"],
            ["You save", "", f"{money(comparison['savings'])} ({comparison['savings_percent']:g}%)"]]
    comp = [[_p(cell, st["body"]) if r and cell else cell for cell in row] for r, row in enumerate(comp)]
    s.append(branded_table(comp, [1.6 * inch, (full_w - 1.6 * inch) / 2, (full_w - 1.6 * inch) / 2], cfg,
                           total_rows=1))
    s.append(_p("Replacement estimate uses a typical regional tear-off rate for comparison only.", st["small"]))

    # ── Payment ──
    s.append(_p("Payment Schedule (recommended option)", st["h1"]))
    sched = [["Milestone", "Amount"]] + [[m, money(a)] for m, a in
                                         payment_schedule(recommended.total, pricing["deposit_percent"])]
    sched.append(["Total", money(recommended.total)])
    t = branded_table(sched, [full_w - 1.6 * inch, 1.6 * inch], cfg, total_rows=1)
    t.setStyle(TableStyle([("ALIGN", (1, 0), (1, -1), "RIGHT")]))
    s.append(t)
    s.append(_p("If a different option is chosen, the same percentages apply to that option's total.", st["small"]))

    # ── Warranty & maintenance ──
    s += [_p("Warranty &amp; Care", st["h1"])]
    s += _bullets(job.get("warranty_notes", [
        "Manufacturer material warranty matched to the option chosen.",
        f"{co['name']} workmanship warranty: {job.get('workmanship_years', 2)} years.",
        "Optional yearly roof check-up and drain cleaning plan keeps the warranty in good standing.",
    ]), st)

    # ── Terms ──
    s.append(_p("Exclusions &amp; Terms", st["h1"]))
    if job.get("exclusions"):
        s.append(_p("<b>Not included:</b> " + "; ".join(job["exclusions"]), st["body"]))
        s.append(Spacer(1, 4))
    s += _bullets([t.format(valid=pricing["proposal_valid_days"], name=co["name"])
                   for t in job.get("terms", DEFAULT_TERMS)], st)

    # ── Acceptance ──
    choice_rows = [["", o.name, money(o.total)] for o in options]
    accept = [
        _p("Acceptance", st["h1"]),
        _p("Check the option you choose, sign and date below. Signing authorizes "
           f"{co['name']} to schedule the work under the terms above.", st["body"]),
        Spacer(1, 6),
        _choice_table(choice_rows, full_w, cfg),
        Spacer(1, 0.25 * inch),
        SignatureBlock(cfg, [
            ("Property Owner / Authorized Agent", ["Signature", "Printed name", "Title", "Date"]),
            (co["name"], ["Signature", f"{co['signer_name']}, {co['signer_title']}", "Date"]),
        ], width=full_w),
        Spacer(1, 0.15 * inch),
        _p(f"{co['legal_name']} · CSLB License #{co['license']}. " + CSLB_NOTICE, st["small"]),
    ]
    s.append(KeepTogether(accept))

    deco = page_decorator(cfg, f"PROPOSAL {number}")
    doc.build(s, onFirstPage=deco, onLaterPages=deco)
    return out_path
