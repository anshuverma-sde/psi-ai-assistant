from collections.abc import Iterable

RRF_K = 60


def reciprocal_rank_fusion(rankings: Iterable[list[str]], k: int = RRF_K) -> dict[str, float]:
    """Combines several ranked id lists; robust to the different score scales of each retriever."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, item_id in enumerate(ranking, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
    return scores
