"""Load a folder of verified human writing and cut it into passages."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Passage:
    passage_id: str
    source_file: str
    text: str

    @property
    def n_words(self) -> int:
        return len(self.text.split())


def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def split_passages(text: str, min_words: int = 150, max_words: int = 400) -> list[str]:
    """Group whole paragraphs into passages of roughly min_words..max_words words.

    Paragraphs are never cut, so a single very long paragraph becomes its own passage.
    A trailing chunk shorter than min_words is merged into the previous passage.
    """
    out: list[list[str]] = []
    cur: list[str] = []
    n = 0
    for p in _paragraphs(text):
        w = len(p.split())
        if cur and n + w > max_words:
            out.append(cur)
            cur, n = [], 0
        cur.append(p)
        n += w
    if cur:
        if out and n < min_words:
            out[-1].extend(cur)
        else:
            out.append(cur)
    return ["\n\n".join(c) for c in out if sum(len(x.split()) for x in c) >= min(min_words, 50)]


def load_folder(folder: str | Path, min_words: int = 150, max_words: int = 400) -> list[Passage]:
    """Read every .txt and .md file in a folder (non-recursive) into passages."""
    folder = Path(folder)
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in {".txt", ".md"})
    if not files:
        raise FileNotFoundError(f"No .txt or .md files in {folder}")
    passages = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        for k, chunk in enumerate(split_passages(text, min_words, max_words)):
            pid = hashlib.sha256(f"{f.name}|{k}|{chunk}".encode()).hexdigest()[:12]
            passages.append(Passage(pid, f.name, chunk))
    return passages
