"""
Shared data loading utilities for all research scripts.

Parses restaurant markdown files from data/menus/*.md. Each file contains
restaurant metadata followed by one or more menu sections.
"""
import argparse
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

        elif line.startswith("- ") and current_menu_type is not None:
            item_line = line[2:]
            if " — " in item_line:
                name, _, price_raw = item_line.partition(" — ")
                price_raw = price_raw.strip()
            else:
                name = item_line.strip()
                price_raw = ""

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
                "price": _parse_price(price_raw),
                "price_raw": price_raw,
                "category": current_category,
                "menu_type": current_menu_type,
                "restaurant_id": restaurant["id"],
            })

        else:
            i += 1

    return restaurant, items


def load_data(restaurant_ids: set[str] | None = None) -> tuple[dict, dict]:
    """
    Return (restaurants_by_id, items_by_restaurant_id) parsed from data/menus/*.md.

    restaurant_ids: if given, only parse restaurants whose filename stem is in
    this set — e.g. pass judged_restaurant_ids() to restrict to the curated
    benchmark subset. Default (None) loads every restaurant in data/menus/.
    """
    restaurants: dict = {}
    menus: dict = {}
    for path in sorted((_DATA_DIR / "menus").glob("*.md")):
        if restaurant_ids is not None and path.stem not in restaurant_ids:
            continue
        restaurant, items = _parse_markdown_file(path)
        rid = restaurant["id"]
        restaurants[rid] = restaurant
        menus[rid] = items
    return restaurants, menus


def judged_restaurant_ids() -> set[str]:
    """
    Restaurant IDs that have relevance judgments — i.e. a
    data/queries/relevance_<id>.csv file exists, regardless of whether it
    currently has any rows. This is what lets evaluate.py (and --benchmark-only
    in the individual search scripts) stay scoped to a curated subset as more
    restaurants are added to data/menus/ without judgments yet: a restaurant
    only enters this set once its relevance file is created, not just because
    its menu exists.
    """
    return {
        p.stem.removeprefix("relevance_")
        for p in (_DATA_DIR / "queries").glob("relevance_*.csv")
    }


def restaurant_scope_cli_args() -> argparse.ArgumentParser:
    """
    Reusable --benchmark-only flag fragment — pass via parents=[...] (see
    colbert_search.cli_args() for the pattern) so every search script gets
    this flag without redefining it.

    Individual search scripts default to searching every restaurant in
    data/menus/ (the realistic, production-like behavior once there are many
    restaurants). --benchmark-only restricts to judged_restaurant_ids() — the
    smaller set with relevance judgments — for focused debugging against
    data/queries/relevance_*.csv without the noise of restaurants that have no
    ground truth to check results against.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--benchmark-only", action="store_true",
        help="Search only restaurants with relevance judgments in data/queries/ "
             "(the benchmark subset) instead of every restaurant in data/menus/.",
    )
    return parser
