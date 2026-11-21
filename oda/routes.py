"""Routes: the ordinary things real writers do to a text before it reaches a detector.

Every route takes a human-written English passage and returns the text a detector would see.
The identity route is the baseline. Translation round trips mimic a writer who drafts in another
language, or who passes their English through a translator to check it.

Machine translation runs locally with Meta's NLLB-200 (no account, no data leaves the machine).
NLLB-200 is licensed CC-BY-NC 4.0: non-commercial use only. Install the optional extra with
`pip install open-detector-audit[mt]`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

# NLLB language codes for the intermediate languages most often needed. Extend as required.
NLLB_CODES = {
    "en": "eng_Latn", "pt": "por_Latn", "es": "spa_Latn", "fr": "fra_Latn", "de": "deu_Latn",
    "it": "ita_Latn", "ar": "arb_Arab", "hi": "hin_Deva", "zh": "zho_Hans", "ja": "jpn_Jpan",
    "ko": "kor_Hang", "ru": "rus_Cyrl", "tr": "tur_Latn", "id": "ind_Latn", "vi": "vie_Latn",
    "sw": "swh_Latn", "fa": "pes_Arab", "uk": "ukr_Cyrl", "th": "tha_Thai", "nl": "nld_Latn",
}

_SPLIT = re.compile(r'(?<=[.!?])["”’)]*\s+(?=["“(]?[A-Z0-9À-ÖØ-Þ])')


def sentences(paragraph: str) -> list[str]:
    return [s for s in _SPLIT.split(paragraph.strip()) if s.strip()]


class Route(Protocol):
    name: str

    def apply(self, text: str) -> str: ...


@dataclass
class Identity:
    name: str = "ORIG"

    def apply(self, text: str) -> str:
        return text


class Translator(Protocol):
    def translate(self, sents: list[str], src: str, tgt: str) -> list[str]: ...


class NLLBTranslator:
    """Local NLLB-200 via Hugging Face transformers (CPU is fine for small audits)."""

    def __init__(self, model_id: str = "facebook/nllb-200-distilled-600M", max_length: int = 400):
        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        except ImportError as e:  # pragma: no cover
            raise ImportError("Install the MT extra: pip install open-detector-audit[mt]") from e
        self.tok = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
        self.max_length = max_length

    def translate(self, sents: list[str], src: str, tgt: str) -> list[str]:
        self.tok.src_lang = NLLB_CODES[src]
        batch = self.tok(sents, return_tensors="pt", padding=True, truncation=True, max_length=self.max_length)
        out = self.model.generate(**batch, forced_bos_token_id=self.tok.convert_tokens_to_ids(NLLB_CODES[tgt]),
                                  num_beams=2, do_sample=False, max_length=self.max_length)
        return self.tok.batch_decode(out, skip_special_tokens=True)


@dataclass
class RoundTrip:
    """English -> language -> English, paragraph breaks preserved, deterministic decoding."""
    lang: str
    translator: Translator
    name: str = ""

    def __post_init__(self):
        if self.lang not in NLLB_CODES:
            raise ValueError(f"Unknown language '{self.lang}'. Known: {sorted(NLLB_CODES)}")
        self.name = self.name or f"MT:{self.lang}"

    def _pass(self, text: str, src: str, tgt: str) -> str:
        paras = [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
        out = []
        for p in paras:
            sents = sentences(p)
            out.append(" ".join(self.translator.translate(sents, src, tgt)) if sents else "")
        return "\n\n".join(out)

    def apply(self, text: str) -> str:
        return self._pass(self._pass(text, "en", self.lang), self.lang, "en")


def parse_routes(spec: str, translator_factory=None) -> list:
    """'orig,mt:pt,mt:hi' -> route objects. The translator is loaded only if an MT route is asked for."""
    routes, translator = [], None
    for token in [t.strip().lower() for t in spec.split(",") if t.strip()]:
        if token == "orig":
            routes.append(Identity())
        elif token.startswith("mt:"):
            if translator is None:
                translator = (translator_factory or NLLBTranslator)()
            routes.append(RoundTrip(token.split(":", 1)[1], translator))
        else:
            raise ValueError(f"Unknown route '{token}' (use 'orig' or 'mt:<lang>')")
    return routes
