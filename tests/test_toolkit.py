import csv
import datetime as dt

import pytest
from openpyxl import load_workbook

from mccurdy.config import load_config, load_yaml, ROOT
from mccurdy.followup import build_drafts, load_sequence, read_prospects
from mccurdy.invoice import build_invoice, invoice_totals
from mccurdy.pricing import build_options, payment_schedule, replacement_comparison
from mccurdy.proposal import build_proposal
from mccurdy import prospects as pr

CFG = load_config()
JOB = load_yaml(ROOT / "examples" / "job_example.yaml")


def test_options_price_every_tier_and_add_ons():
    opts = {o.key: o for o in build_options(JOB, CFG["pricing"])}
    # 42,000 sq ft x $3.40 + drains 6x185 + curbs 14x95
    assert opts["better"].total == pytest.approx(42000 * CFG["pricing"]["systems"]["better"]["rate"] + 1110 + 1330)
    assert opts["better"].recommended and not opts["good"].recommended


def test_minimum_job_applies_to_small_roofs():
    small = {**JOB, "roof": {"square_feet": 500}, "add_ons": []}
    assert all(o.total == CFG["pricing"]["minimum_job"] for o in build_options(small, CFG["pricing"]))


def test_replacement_comparison_uses_configured_percentages():
    opts = {o.key: o for o in build_options(JOB, CFG["pricing"])}
    comp = replacement_comparison(CFG["pricing"], opts["good"])
    assert comp["savings_percent"] == 40
    assert comp["coating_cost"] / comp["replacement_cost"] == pytest.approx(0.60, abs=1e-4)
    # 30-year NDL has no percentage: described in words, never a made-up number
    assert replacement_comparison(CFG["pricing"], opts["best"]) is None


def test_payment_schedule_follows_mccurdy_terms():
    total = 145_240.0
    sched = payment_schedule(total, CFG["pricing"]["payment_schedule"])
    assert sched[0] == ("No deposit required", 0)
    assert sum(a for _, a in sched) == pytest.approx(total)
    odd = payment_schedule(100.01, [["a", 50], ["b", 50]])
    assert sum(a for _, a in odd) == pytest.approx(100.01)


def test_proposal_pdf_has_fillable_signature_fields(tmp_path):
    out = build_proposal(JOB, tmp_path / "p.pdf", CFG)
    data = out.read_bytes()
    assert data.startswith(b"%PDF") and b"/AcroForm" in data and b"sig_0_signature" in data


def test_invoice_totals_and_pdf(tmp_path):
    inv = load_yaml(ROOT / "examples" / "invoice_example.yaml")
    inv["payments"] = [{"amount": 1000}]
    t = invoice_totals(inv, CFG)
    assert t["balance"] == pytest.approx(43572 - 1000)
    assert build_invoice(inv, tmp_path / "i.pdf", CFG).read_bytes().startswith(b"%PDF")


def test_assessor_scoring_filters_and_ranks():
    rows = pr.score_assessor_csv(ROOT / "examples" / "assessor_sample.csv")
    owners = [r["owner"] for r in rows]
    assert "GARCIA MARIA" not in owners  # house, too small
    assert owners[0] == "VALLEY COLD STORAGE LLC"
    assert rows[0]["score"] >= 90 and "absentee" in rows[0]["why"]


def test_polygon_area_of_known_square():
    # ~100 m x 100 m square near Fresno
    lat, lon = 36.75, -119.77
    dlat = 100 / 111_320
    dlon = 100 / (111_320 * 0.8018)
    sq = [(lat, lon), (lat, lon + dlon), (lat + dlat, lon + dlon), (lat + dlat, lon)]
    assert pr.polygon_area_sqm(sq) == pytest.approx(10_000, rel=0.02)


def test_parse_overpass_keeps_large_roofs_only():
    def way(i, size_m, tags):
        lat, lon = 36.7, -119.8
        d = size_m / 111_320
        g = [{"lat": lat, "lon": lon}, {"lat": lat, "lon": lon + d * 1.25}, {"lat": lat + d, "lon": lon + d * 1.25},
             {"lat": lat + d, "lon": lon}]
        return {"id": i, "geometry": g, "tags": tags}
    data = {"elements": [way(1, 200, {"building": "warehouse", "name": "Big DC"}),
                         way(2, 20, {"building": "retail"})]}
    rows = pr.parse_overpass(data, 20_000)
    assert [r["name"] for r in rows] == ["Big DC"] and rows[0]["building_sqft"] > 300_000


def test_prospects_xlsx_then_followup_drafts(tmp_path):
    rows = pr.score_assessor_csv(ROOT / "examples" / "assessor_sample.csv")
    xlsx = pr.write_prospects_xlsx(rows, tmp_path / "p.xlsx", "test", CFG)
    assert load_workbook(xlsx).active["A5"].value == rows[0]["score"]
    back = read_prospects(xlsx)
    assert back[0]["owner"] == "VALLEY COLD STORAGE LLC"
    out = build_drafts(back, "owner_investor", tmp_path, start=dt.date(2026, 11, 2), cfg=CFG)
    drafts = list(csv.DictReader(open(out, encoding="utf-8")))
    steps = load_sequence("owner_investor")
    assert len(drafts) == len(back) * len(steps)
    assert "2650 S Chestnut Ave" in drafts[0]["subject"]
    assert all("{" not in d["body"] for d in drafts)
    assert any("128,400" in d["body"] for d in drafts if "CHESTNUT" in d["property"])


@pytest.mark.parametrize("segment", ["owner_investor", "property_manager", "realtor", "past_client"])
def test_every_template_parses_and_fills(segment):
    steps = load_sequence(segment)
    assert steps and all(s["subject"] for s in steps)
    from mccurdy.followup import personalize
    for s in steps:
        assert "{" not in personalize(s["body"], {"site_address": "1 Main", "building_sqft": 30000}, CFG)
