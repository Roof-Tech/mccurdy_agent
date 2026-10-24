"""Command line: python -m mccurdy <command> ...  (run with -h for help)."""
import argparse
import sys
from pathlib import Path

from .config import ROOT, load_config, load_yaml, unset_fields

OUT = ROOT / "output"


def _warn_unset(cfg):
    missing = unset_fields(cfg)
    if missing:
        print(f"WARNING: config/company.yaml still has REPLACE_ME for: {', '.join(missing)}. "
              "Fill these in before sending anything to a customer.", file=sys.stderr)


def cmd_proposal(a):
    from .proposal import build_proposal
    cfg = load_config()
    _warn_unset(cfg)
    job = load_yaml(a.job)
    out = Path(a.out or OUT / "proposals" / f"{job.get('proposal_number', Path(a.job).stem)}.pdf")
    print(build_proposal(job, out, cfg))


def cmd_invoice(a):
    from .invoice import build_invoice
    cfg = load_config()
    _warn_unset(cfg)
    inv = load_yaml(a.invoice)
    out = Path(a.out or OUT / "invoices" / f"{inv['invoice_number']}.pdf")
    print(build_invoice(inv, out, cfg))


def cmd_prospects(a):
    from . import prospects as pr
    if a.source == "score":
        rows = pr.score_assessor_csv(a.csv, min_sqft=a.min_sqft, uses=a.uses)
        title = f"Assessor prospects from {Path(a.csv).name}"
        default = OUT / "prospects" / f"prospects_{Path(a.csv).stem}.xlsx"
    else:
        rows = pr.fetch_osm_buildings(a.area, min_sqft=a.min_sqft)
        title = f"Large roofs in {a.area} (OpenStreetMap)"
        default = OUT / "prospects" / f"roofs_{a.area.lower().replace(' ', '_')}.xlsx"
    path = pr.write_prospects_xlsx(rows[: a.limit] if a.limit else rows, a.out or default, title)
    print(f"{len(rows)} prospects -> {path}")


def cmd_followups(a):
    from .followup import build_drafts, read_prospects
    rows = read_prospects(a.prospects)
    if a.min_score:
        rows = [r for r in rows if float(r.get("score") or 0) >= a.min_score]
    out = build_drafts(rows[: a.limit] if a.limit else rows, a.segment, a.out or OUT / "followups")
    print(f"{len(rows)} prospects -> {out}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mccurdy", description="McCurdy Coatings business toolkit")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("proposal", help="Build a signable proposal PDF from a job YAML file")
    p.add_argument("job")
    p.add_argument("--out")
    p.set_defaults(fn=cmd_proposal)

    p = sub.add_parser("invoice", help="Build an invoice PDF from an invoice YAML file")
    p.add_argument("invoice")
    p.add_argument("--out")
    p.set_defaults(fn=cmd_invoice)

    p = sub.add_parser("prospects", help="Find and rank commercial flat-roof prospects")
    psub = p.add_subparsers(dest="source", required=True)
    s = psub.add_parser("score", help="Score a county assessor CSV export")
    s.add_argument("csv")
    s.add_argument("--uses", choices=["commercial", "all"], default="commercial")
    s.add_argument("--min-sqft", type=float, default=10_000)
    s.add_argument("--limit", type=int)
    s.add_argument("--out")
    m = psub.add_parser("map", help="Pull large roofs from OpenStreetMap for a city/county name")
    m.add_argument("--area", required=True, help='e.g. "Fresno", "Visalia", "Fresno County"')
    m.add_argument("--min-sqft", type=float, default=20_000)
    m.add_argument("--limit", type=int)
    m.add_argument("--out")
    p.set_defaults(fn=cmd_prospects)

    p = sub.add_parser("followups", help="Write personalized follow-up email drafts for a prospect list")
    p.add_argument("prospects", help="prospects .xlsx (from the prospects command) or .csv")
    p.add_argument("--segment", default="owner_investor",
                   choices=[f.stem for f in sorted((ROOT / "templates" / "emails").glob("*.md"))])
    p.add_argument("--min-score", type=float, default=0)
    p.add_argument("--limit", type=int)
    p.add_argument("--out")
    p.set_defaults(fn=cmd_followups)

    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
