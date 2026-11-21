"""Command line: oda run --texts DIR --routes orig,mt:pt --detector command --detector-cmd "python my_detector.py" """
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .corpus import load_folder
from .detectors import get_detector
from .report import render
from .routes import parse_routes
from .stats import summarize


def run(args: argparse.Namespace) -> int:
    passages = load_folder(args.texts, args.min_words, args.max_words)
    routes = parse_routes(args.routes)
    detector = get_detector(args.detector, cmd=args.detector_cmd, price_per_word=args.price_per_word)
    words = sum(p.n_words for p in passages) * len(routes)
    cost = words * detector.price_per_word
    print(f"{len(passages)} passages x {len(routes)} routes = about {words:,} words; estimated cost US${cost:,.2f}")
    if cost > 0 and not args.confirm_spend:
        print("Dry run only. Add --confirm-spend to call the paid detector.")
        return 0

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows_path = out_dir / "scores.jsonl"
    done = set()
    if rows_path.exists():
        done = {(r["passage_id"], r["route"]) for r in map(json.loads, rows_path.read_text(encoding="utf-8").splitlines())}
    with rows_path.open("a", encoding="utf-8") as f:
        for p in passages:
            for route in routes:
                if (p.passage_id, route.name) in done:
                    continue
                text = route.apply(p.text)
                row = {"passage_id": p.passage_id, "source_file": p.source_file, "route": route.name,
                       "detector": detector.name, "score": detector.score(text), "n_words": len(text.split())}
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()

    rows = [json.loads(line) for line in rows_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    report = render(summarize(rows, args.threshold), detector.name, args.threshold, len(passages))
    (out_dir / "report.md").write_text(report, encoding="utf-8")
    print(f"Report written to {out_dir / 'report.md'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="oda", description="Audit an AI-text detector on your own human writers.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="score human passages under each route and write a report")
    r.add_argument("--texts", required=True, help="folder of .txt/.md files written by people")
    r.add_argument("--routes", default="orig", help="comma list: orig, mt:<lang> (e.g. orig,mt:pt,mt:hi)")
    r.add_argument("--detector", default="mock", help="mock | command")
    r.add_argument("--detector-cmd", default=None, help="for --detector command: program that reads text on stdin and prints a score in [0,1]")
    r.add_argument("--price-per-word", type=float, default=0.0, help="USD per word, for the cost estimate of a paid detector")
    r.add_argument("--threshold", type=float, default=0.5, help="score at or above which a text counts as flagged")
    r.add_argument("--out", default="audit_out")
    r.add_argument("--min-words", type=int, default=150)
    r.add_argument("--max-words", type=int, default=400)
    r.add_argument("--confirm-spend", action="store_true", help="required before calling a paid detector")
    args = ap.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
