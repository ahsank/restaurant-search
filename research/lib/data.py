"""
Shared data loading utilities for all research scripts.

Data files are read from data/ at the project root, regardless of
which script or subdirectory imports this module.
"""
import json
from pathlib import Path

_DATA_DIR = Path(__file__).parents[2] / "data"


def load_restaurants() -> dict:
    """Return restaurants keyed by id."""
    with open(_DATA_DIR / "restaurants.json") as f:
        return {r["id"]: r for r in json.load(f)}


def load_menus() -> dict:
    """Return menu items keyed by restaurant_id."""
    with open(_DATA_DIR / "menus.json") as f:
        return json.load(f)


def load_data() -> tuple[dict, dict]:
    """Return (restaurants_by_id, menus_by_restaurant_id)."""
    return load_restaurants(), load_menus()
