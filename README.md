# Open Detector Audit

**Test an AI-text detector on your own human writers, in their languages, before you trust it.**

AI-text detectors now help decide who is accused of cheating, which manuscripts are desk-rejected and which
applicants look "inauthentic". They are mostly validated on native English prose. Schools, small journals and
NGOs that serve people writing in a second language have no simple way to check whether a detector works for
*their* people.

Open Detector Audit is a small, local-first tool that answers one question:

> If we run this detector on writing we know is human, how often does it accuse someone—and does that change
> when the writing has passed through translation, as it does for many non-native writers?

## How it works

1. **Bring verified human writing.** A folder of `.txt` or `.md` files you know were written by people (for
   example, essays written before 2022). Nothing is uploaded anywhere except, if you choose, to the detector
   you are auditing.
2. **Apply real-life routes.** `ORIG` (as written) and `MT:<lang>` (an English → language → English round trip
   with Meta's NLLB-200 running locally, which mimics a writer drafting in another language).
3. **Score and report.** Every flag is a false positive. The report gives false-positive rates per route
   with 95% Wilson intervals, in plain language, plus a suggested fair-use policy.

```bash
pip install -e ".[mt,dev]"          # the MT extra is only needed for translation routes

# Offline dry run with the mock detector (no key, no cost)
oda run --texts examples/sample_texts --routes orig --detector mock

# Real audit: wrap the detector you want to test in a small script (see examples/detector_template.py)
# that reads a text on stdin and prints a score in [0, 1]. Keys stay in your environment.
oda run --texts my_essays --routes orig,mt:pt,mt:hi --detector command --detector-cmd "python my_detector.py" --price-per-word 0.0005          # dry run: shows the cost
oda run --texts my_essays --routes orig,mt:pt,mt:hi --detector command --detector-cmd "python my_detector.py" --price-per-word 0.0005 --confirm-spend
```

Runs are resumable: scores are appended to `audit_out/scores.jsonl`, and re-running skips what is done.
Re-run the same audit after a vendor update to catch silent changes in a model you do not control.

## Status

Version 0.1, a working prototype. It packages methods from the author's ongoing independent audits of
AI-text detectors. The tool is vendor-neutral and ships no vendor-specific code. Planned next: speech-to-text
routes (Whisper), grammar-editing routes, a simple desktop interface, and reports in Portuguese and Spanish.

## Responsible use

- This tool measures **false positives on human writing**. It is not a guide to evading detection, and it does
  not include "humanizer" routes.
- Do not upload writing you do not have the right to process. Get consent from the writers whose texts you audit.
- NLLB-200 is licensed CC-BY-NC 4.0 (non-commercial use). The code in this repository is Apache-2.0.

## Suggested policy for institutions

1. Never sanction anyone on a detector score alone.
2. Audit a detector on your own writers before adopting it, and publish the false-positive rate.
3. Give every flagged writer a route to contest the flag before any consequence.
4. Re-audit at least once per term and after any change in the vendor's model.

## Author

Gabriel Cepaluni, São Paulo State University (UNESP), Brazil · [gcepaluni.github.io](https://gcepaluni.github.io)
