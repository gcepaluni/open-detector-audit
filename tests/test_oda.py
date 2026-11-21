from pathlib import Path

from oda.cli import main
from oda.corpus import load_folder, split_passages
from oda.routes import RoundTrip, parse_routes
from oda.stats import summarize, wilson

PARA = ("This is a paragraph written by a person about public policy and the way schools adopt new tools. " * 6).strip()


class FakeTranslator:
    """Reverses word order on the way out and back, so a round trip returns the original."""

    def translate(self, sents, src, tgt):
        return [" ".join(reversed(s.split())) for s in sents]


def test_split_keeps_paragraphs_whole():
    text = "\n\n".join([PARA] * 5)
    chunks = split_passages(text, min_words=100, max_words=200)
    assert all(PARA in c for c in chunks)
    assert sum(c.count(PARA) for c in chunks) == 5


def test_load_folder(tmp_path: Path):
    (tmp_path / "a.txt").write_text("\n\n".join([PARA] * 4), encoding="utf-8")
    ps = load_folder(tmp_path, 100, 200)
    assert ps and all(p.source_file == "a.txt" for p in ps)
    assert len({p.passage_id for p in ps}) == len(ps)


def test_roundtrip_preserves_paragraphs():
    rt = RoundTrip("pt", FakeTranslator())
    text = "One sentence here. Another one.\n\nSecond paragraph."
    assert rt.apply(text).count("\n\n") == 1


def test_parse_routes_lazy_translator():
    calls = []
    routes = parse_routes("orig,mt:pt,mt:hi", translator_factory=lambda: calls.append(1) or FakeTranslator())
    assert [r.name for r in routes] == ["ORIG", "MT:pt", "MT:hi"]
    assert len(calls) == 1


def test_wilson_bounds():
    lo, hi = wilson(0, 20)
    assert lo == 0.0 and 0.1 < hi < 0.2
    lo, hi = wilson(10, 20)
    assert lo < 0.5 < hi


def test_summarize_counts_false_positives():
    rows = [{"route": "ORIG", "score": s} for s in (0.1, 0.6, 0.9, 0.2)]
    (r,) = summarize(rows, 0.5)
    assert r.n == 4 and r.flagged == 2 and r.fpr == 0.5


def test_cli_end_to_end_with_mock(tmp_path: Path):
    texts = tmp_path / "texts"
    texts.mkdir()
    (texts / "essay.md").write_text("\n\n".join([PARA] * 6), encoding="utf-8")
    out = tmp_path / "out"
    assert main(["run", "--texts", str(texts), "--routes", "orig", "--detector", "mock", "--out", str(out)]) == 0
    report = (out / "report.md").read_text(encoding="utf-8")
    assert "false positive" in report.lower() and "| ORIG |" in report
    # resumable: a second run adds no duplicate rows
    n1 = len((out / "scores.jsonl").read_text().splitlines())
    main(["run", "--texts", str(texts), "--routes", "orig", "--detector", "mock", "--out", str(out)])
    assert len((out / "scores.jsonl").read_text().splitlines()) == n1


def test_command_detector(tmp_path: Path):
    import sys
    from oda.detectors import CommandDetector
    script = tmp_path / "det.py"
    script.write_text("import sys; t=sys.stdin.read(); print(0.75 if 'flag' in t else 0.1)", encoding="utf-8")
    d = CommandDetector(cmd=f'"{sys.executable}" "{script}"')
    assert d.score("please flag me") == 0.75
    assert d.score("ordinary text") == 0.1
