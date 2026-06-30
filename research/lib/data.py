"""
Shared data loading utilities for all research scripts.

Data files are read from data/ at the project root, regardless of
which script or subdirectory imports this module.
"""
import json
from pathlib import Path

_DATA_DIR = Path(__file__).parents[2] / "data"


def load_restaurants() -> dict:
    """Return restaurants keyed by id, scanning data/restaurants/*.json."""
    restaurants = {}
    for path in sorted((_DATA_DIR / "restaurants").glob("*.json")):
        with open(path) as f:
            r = json.load(f)
            restaurants[r["id"]] = r
    return restaurants


def load_menus() -> dict:
    """Return menu items keyed by restaurant_id, scanning data/menus/*.json.

    Each file has top-level restaurant_id and menu_type fields. Items from
    multiple files for the same restaurant (e.g. dinner + happy_hour) are
    merged. Each returned item has menu_type injected so callers can filter.
    """
    menus: dict[str, list] = {}
    for path in sorted((_DATA_DIR / "menus").glob("*.json")):
        with open(path) as f:
            menu = json.load(f)
        restaurant_id = menu["restaurant_id"]
        menu_type = menu["menu_type"]
        items = [{**item, "menu_type": menu_type} for item in menu["items"]]
        if restaurant_id in menus:
            menus[restaurant_id].extend(items)
        else:
            menus[restaurant_id] = items
    return menus


def load_data() -> tuple[dict, dict]:
    """Return (restaurants_by_id, menus_by_restaurant_id)."""
    return load_restaurants(), load_menus()
