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
    dry_mils: int
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
        coating = LineItem(f"{tier['name']} — prep, repairs, primer and {tier['dry_mils']} dry-mil silicone system",
                           sqft, "sq ft", rate)
        items = [coating, *add_ons]
        opt = Option(key, tier["name"], tier["dry_mils"], tier["warranty_years"], items, key == recommended)
        if opt.total < minimum:
            opt.items.append(LineItem("Minimum project adjustment", 1, "ea", round(minimum - opt.total, 2)))
        options.append(opt)
    return options


def replacement_comparison(job: dict, pricing: dict, option: Option) -> dict:
    """What the owner saves by renewing instead of tearing off and replacing."""
    sqft = float(job["roof"]["square_feet"])
    replacement = round(sqft * float(pricing["tear_off_replacement_rate"]), 2)
    savings = round(replacement - option.total, 2)
    return {
        "replacement_cost": replacement,
        "coating_cost": option.total,
        "savings": savings,
        "savings_percent": round(100 * savings / replacement, 1) if replacement else 0.0,
    }


def payment_schedule(total: float, deposit_percent: float) -> list[tuple[str, float]]:
    deposit = round(total * deposit_percent / 100, 2)
    return [
        (f"Deposit at signing ({deposit_percent:g}%)", deposit),
        ("Balance at substantial completion", round(total - deposit, 2)),
    ]
