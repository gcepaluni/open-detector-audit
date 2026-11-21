"""False-positive rates with honest uncertainty."""
from __future__ import annotations

import math
from dataclasses import dataclass


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a proportion k/n (well behaved for small n and k=0)."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


@dataclass
class RouteResult:
    route: str
    n: int
    flagged: int
    mean_score: float

    @property
    def fpr(self) -> float:
        return self.flagged / self.n if self.n else float("nan")

    @property
    def ci(self) -> tuple[float, float]:
        return wilson(self.flagged, self.n)


def summarize(rows: list[dict], threshold: float) -> list[RouteResult]:
    """rows: dicts with 'route' and 'score'. All texts are human-written, so every flag is a false positive."""
    by: dict[str, list[float]] = {}
    for r in rows:
        by.setdefault(r["route"], []).append(r["score"])
    out = []
    for route, scores in by.items():
        out.append(RouteResult(route, len(scores), sum(s >= threshold for s in scores),
                               sum(scores) / len(scores)))
    return out
