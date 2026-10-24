"""Loads config/company.yaml (or a path in MCCURDY_CONFIG)."""
import os
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "company.yaml"


@lru_cache(maxsize=None)
def load_config(path: str | None = None) -> dict:
    cfg_path = Path(path or os.environ.get("MCCURDY_CONFIG") or DEFAULT_CONFIG)
    with open(cfg_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_yaml(path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def unset_fields(cfg: dict) -> list[str]:
    """Company fields still set to REPLACE_ME — shown as a warning, never silently printed."""
    return [k for k, v in cfg["company"].items() if isinstance(v, str) and "REPLACE_ME" in v]


def money(value: float) -> str:
    return f"${value:,.2f}"
