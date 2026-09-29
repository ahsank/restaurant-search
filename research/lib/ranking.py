"""
Shared restaurant-level ranking primitive.

Grouping search results by restaurant and ranking those restaurants needs the
same aggregation in three places: choosing which restaurants to show and in
what order (search_grouped.py), computing the "ideal" restaurant order from
ground-truth relevance judgments (restaurant_eval.py), and computing an
engine's own predicted restaurant order to compare against that ground truth
(also restaurant_eval.py). All three are "group (restaurant_id, value) pairs
by restaurant, score each restaurant by the mean of its own top-k values" —
just fed a different source for `value` (a search engine's score, or a
relevance label). One function covers all three.
"""
from collections import defaultdict


def restaurant_scores(
    item_values: list[tuple[str, float]],
    k: int,
) -> list[tuple[str, float, list[float]]]:
    """
    Group (restaurant_id, value) pairs by restaurant_id, score each restaurant
    as the mean of its own top-k values, and return restaurants sorted by that
    score, highest first.

    item_values: e.g. [(restaurant_id, engine_score), ...] in the order/values
        produced by a search engine, or [(restaurant_id, relevance_label), ...]
        from ground-truth judgments. Order of input doesn't matter — each
        restaurant's own values are re-sorted internally before taking top-k.
    k: how many of each restaurant's best values to average (and, for the
        search_grouped.py use case, how many items to actually display).

    Returns: [(restaurant_id, score, top_k_values), ...] sorted by score desc.
        top_k_values is that restaurant's own top-k values (already sorted
        highest first) — reused directly by callers that also need to know
        *which* values (e.g. which items) made the cut, not just the score.
    """
    by_restaurant: dict[str, list[float]] = defaultdict(list)
    for rid, value in item_values:
        by_restaurant[rid].append(value)

    scored: list[tuple[str, float, list[float]]] = []
    for rid, values in by_restaurant.items():
        top_k = sorted(values, reverse=True)[:k]
        score = sum(top_k) / len(top_k) if top_k else 0.0
        scored.append((rid, score, top_k))

    scored.sort(key=lambda t: t[1], reverse=True)
    return scored
