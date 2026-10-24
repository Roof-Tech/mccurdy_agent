"""Price a coating job: Good / Better / Best tiers plus a coating-vs-replacement comparison."""
from dataclasses import dataclass, field


@dataclass
class LineItem:
    description: str
    quantity: float
    unit: str
    unit_price: float

    @property
    def total(self) -> float:
        return round(self.quantity * self.unit_price, 2)


@dataclass
class Option:
    key: str
    name: str
    coats: str
    warranty_years: int
    items: list[LineItem] = field(default_factory=list)
    recommended: bool = False

    @property
    def total(self) -> float:
        return round(sum(i.total for i in self.items), 2)


def build_options(job: dict, pricing: dict) -> list[Option]:
    """One Option per tier in config. Job-level `rate_overrides` and `add_ons` apply to every tier."""
    sqft = float(job["roof"]["square_feet"])
    overrides = job.get("rate_overrides", {})
    recommended = job.get("recommended_option", "better")
    add_ons = [LineItem(a["description"], float(a.get("quantity", 1)), a.get("unit", "ea"), float(a["unit_price"]))
               for a in job.get("add_ons", [])]
    minimum = float(pricing.get("minimum_job", 0))

    options = []
    for key, tier in pricing["systems"].items():
        rate = float(overrides.get(key, tier["rate"]))
        coating = LineItem(f"{tier['name']} — full McCurdy Method prep, repairs and grid-applied coating system",
                           sqft, "sq ft", rate)
        items = [coating, *add_ons]
        opt = Option(key, tier["name"], tier.get("coats", "Per manufacturer specification"), tier["warranty_years"], items,
                     key == recommended)
        if opt.total < minimum:
            opt.items.append(LineItem("Minimum project adjustment", 1, "ea", round(minimum - opt.total, 2)))
        options.append(opt)
    return options


def value_summary(pricing: dict, option: Option) -> dict:
    """Warranty years first, price second: extra warranted years vs. a typical replacement-roof warranty,
    and the single 'up to' savings figure. No per-job savings dollars are invented."""
    base = int(pricing.get("typical_replacement_warranty_years", 20))
    extra_pct = round(100 * (option.warranty_years - base) / base) if option.warranty_years > base else 0
    return {
        "warranty_years": option.warranty_years,
        "extra_years_percent": extra_pct,
        "savings_up_to_percent": pricing.get("savings_up_to_percent"),
    }


def payment_schedule(total: float, schedule: list) -> list[tuple[str, float]]:
    """schedule: [[milestone, percent], ...] — percentages should add up to 100."""
    rows = [(m, round(total * float(pct) / 100, 2)) for m, pct in schedule]
    # put any rounding cents on the last milestone so the rows add up exactly
    diff = round(total - sum(a for _, a in rows), 2)
    if rows and diff:
        rows[-1] = (rows[-1][0], round(rows[-1][1] + diff, 2))
    return rows
