"""Plain-language report that a school board or editor can act on."""
from __future__ import annotations

import datetime as dt

from .stats import RouteResult


def render(results: list[RouteResult], detector: str, threshold: float, n_passages: int) -> str:
    today = dt.date.today().isoformat()
    lines = [
        f"# Detector audit report — {detector}",
        "",
        f"Date: {today} · Human-written passages: {n_passages} · Flag threshold: score ≥ {threshold:g}",
        "",
        "Every passage in this audit was written by a person. Any passage the detector flags is a",
        "**false positive**: an accusation against a human writer.",
        "",
        "| Route | Passages | Flagged | False-positive rate | 95% interval | Mean score |",
        "|---|---|---|---|---|---|",
    ]
    for r in sorted(results, key=lambda x: (x.route != "ORIG", x.route)):
        lo, hi = r.ci
        lines.append(f"| {r.route} | {r.n} | {r.flagged} | {r.fpr:.1%} | {lo:.1%}–{hi:.1%} | {r.mean_score:.2f} |")
    worst = max(results, key=lambda x: x.fpr) if results else None
    lines += ["", "## What this means", ""]
    if worst and worst.flagged:
        lo, _ = worst.ci
        lines.append(f"- The highest false-positive rate was on route **{worst.route}**: {worst.fpr:.0%} of human "
                     f"passages flagged (at least {lo:.0%} with 95% confidence).")
    else:
        lines.append("- No human passage was flagged in this sample. With a small sample, that does not prove "
                     "the rate is zero; see the upper end of the interval.")
    lines += [
        "- `ORIG` is the writing as submitted. `MT:<lang>` is the same writing after a round trip through "
        "machine translation, as happens when a writer drafts in another language.",
        "- Re-run this audit after any vendor update: models behind an API can change without notice.",
        "",
        "## Suggested policy",
        "",
        "1. Never sanction anyone on a detector score alone.",
        "2. Before adopting a detector, audit it on your own writers and publish the false-positive rate.",
        "3. Give every flagged writer a route to contest the flag before any consequence.",
        "4. Re-audit at least once per term, and after any change in the vendor's model.",
    ]
    return "\n".join(lines) + "\n"
