"""Template for plugging a detector into Open Detector Audit.

Read one text from standard input and print one number between 0 and 1: the detector's estimate that
the text is AI-written. Replace the body of `score` with a call to the detector you want to audit.
Read any API key from an environment variable; never write keys into this file.

    oda run --texts my_essays --detector command --detector-cmd "python examples/detector_template.py"
"""
import sys


def score(text: str) -> float:
    # Placeholder: replace with a real detector call. Here, a meaningless length-based number.
    return min(1.0, len(text) / 10000)


if __name__ == "__main__":
    print(score(sys.stdin.read()))
