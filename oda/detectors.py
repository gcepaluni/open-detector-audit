"""Detector adapters. Each returns a score in [0, 1]: the detector's estimate that the text is AI-written.

The repository ships no vendor-specific code. To audit a detector, wrap its API or local model in a
small script and plug it in with the `command` adapter:

    oda run --texts my_essays --detector command --detector-cmd "python my_detector.py"

The script reads one text on standard input and prints one number between 0 and 1. Keep any API key
in an environment variable read by your script, never in files committed to a repository.
"""
from __future__ import annotations

import hashlib
import shlex
import subprocess
from typing import Optional, Protocol


class Detector(Protocol):
    name: str
    price_per_word: float  # USD, used for the dry-run cost estimate

    def score(self, text: str) -> float: ...


class MockDetector:
    """Deterministic, offline stand-in for testing the pipeline. Not a detector."""
    name = "mock"
    price_per_word = 0.0

    def __init__(self, bias: float = 0.0, **_):
        self.bias = bias

    def score(self, text: str) -> float:
        h = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
        return min(1.0, max(0.0, h + self.bias))


class CommandDetector:
    """Runs a user-supplied command: text on stdin, a score in [0, 1] on stdout."""
    name = "command"

    def __init__(self, cmd: Optional[str] = None, price_per_word: float = 0.0, timeout: int = 180, **_):
        if not cmd:
            raise ValueError("The command detector needs --detector-cmd")
        self.argv = shlex.split(cmd, posix=True)
        self.price_per_word = price_per_word
        self.timeout = timeout

    def score(self, text: str) -> float:
        res = subprocess.run(self.argv, input=text, capture_output=True, text=True, encoding="utf-8",
                             timeout=self.timeout, check=False)
        if res.returncode != 0:
            raise RuntimeError(f"Detector command failed ({res.returncode}): {res.stderr.strip()[:300]}")
        value = float(res.stdout.strip().splitlines()[-1])
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"Detector command must print a score in [0, 1], got {value}")
        return value


DETECTORS = {"mock": MockDetector, "command": CommandDetector}


def get_detector(name: str, **kwargs) -> Detector:
    try:
        cls = DETECTORS[name]
    except KeyError:
        raise ValueError(f"Unknown detector '{name}'. Available: {sorted(DETECTORS)}") from None
    return cls(**kwargs)
