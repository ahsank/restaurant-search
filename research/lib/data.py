"""
Shared data loading utilities for all research scripts.

Parses restaurant markdown files from data/menus/*.md. Each file contains
restaurant metadata followed by one or more menu sections.
"""
import re
from pathlib import Path

_DATA_DIR = Path(__file__).parents[2] / "data"


def _parse_price(raw: str) -> float | None:
    """Extract the first dollar amount from a price string, e.g. 'from $18' -> 18.0."""
    m = re.search(r'\$(\d+(?:\.\d+)?)', raw)
    return float(m.group(1)) if m else None


def _parse_markdown_file(path: Path) -> tuple[dict, list[dict]]:
    """Parse a restaurant .md file into (restaurant_info, [menu_item, ...])."""
    lines = path.read_text().splitlines()
    restaurant: dict = {"id": path.stem}
    items: list[dict] = []
    i = 0

    # Restaurant name from level-1 heading
    while i < len(lines) and not lines[i].startswith("# "):
        i += 1
    if i < len(lines):
        restaurant["name"] = lines[i][2:].strip()
        i += 1

    # Metadata: plain Key: value lines until the first ## heading
    while i < len(lines) and not lines[i].startswith("## "):
        line = lines[i].strip()
        if line and ":" in line and not line.startswith("#") and not line.startswith("-"):
            key, _, value = line.partition(":")
            restaurant[key.strip().lower()] = value.strip()
        i += 1

    # Menu sections
    current_menu_type: str | None = None
    current_category: str | None = None

    while i < len(lines):
        line = lines[i]

        if line.startswith("## Menu Type:"):
            current_menu_type = line[len("## Menu Type:"):].strip().lower()
            i += 1

        elif line.startswith("### "):
            current_category = line[4:].strip()
            i += 1

        elif line.startswith("- ") and " — " in line:
            item_line = line[2:]
            name, _, price_raw = item_line.partition(" — ")

            # Collect indented continuation lines (description and dietary)
            description_parts = []
            dietary = ""
            i += 1
            while i < len(lines) and lines[i].startswith("  ") and not lines[i].startswith("  - "):
                cont = lines[i].strip()
                if cont.lower().startswith("dietary:"):
                    dietary = cont[len("Dietary:"):].strip()
                elif cont:
                    description_parts.append(cont)
                i += 1

            items.append({
                "name": name.strip(),
                "description": " ".join(description_parts),
                "dietary": dietary,
                "price": _parse_price(price_raw.strip()),
                "price_raw": price_raw.strip(),
                "category": current_category,
                "menu_type": current_menu_type,
                "restaurant_id": restaurant["id"],
            })

        else:
            i += 1

    return restaurant, items


def load_data() -> tuple[dict, dict]:
    """Return (restaurants_by_id, items_by_restaurant_id) parsed from data/menus/*.md."""
    restaurants: dict = {}
    menus: dict = {}
    for path in sorted((_DATA_DIR / "menus").glob("*.md")):
        restaurant, items = _parse_markdown_file(path)
        rid = restaurant["id"]
        restaurants[rid] = restaurant
        menus[rid] = items
    return restaurants, menus
