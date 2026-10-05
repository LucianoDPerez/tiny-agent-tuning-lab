"""Heuristic scoring of eval responses against a senior-dev rubric.

Not a substitute for human review, but catches systematic regressions
(rambling, no structure, no security mention, no error handling).
"""
import json
import re
import sys

RAMBLE_PATTERNS = [
    r"\bwe need to\b", r"\bvamos a analizar\b", r"\bvaya,\b", r"\bdejame analizar\b",
    r"\bthe user (is|seems|wants)\b", r"\bthis (question|problem|prompt)\b",
]
CRITERIA = [
    ("Estructura clara (listas o pasos)", lambda t: len(re.findall(r"\n\s*[-*\d]", t)) >= 2),
    ("Conciso (< 1200 chars)", lambda t: len(t) < 1200),
    ("Sin monólogo interno", lambda t: not any(re.search(p, t, re.I) for p in RAMBLE_PATTERNS)),
    ("Menciona verificación", lambda t: bool(re.search(r"verific|test|build|comando|run ", t, re.I))),
    ("Menciona un principio aplicable", lambda t: bool(re.search(r"SOLID|DRY|KISS|idempoten|dedup|backpressure|OWASP|clean arch|hexagonal|puerto|adaptador", t, re.I))),
]

def score(path):
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    totals = {name: 0 for name, _ in CRITERIA}
    n = 0
    for r in rows:
        t = r["response"]
        n += 1
        for name, ok in CRITERIA:
            totals[name] += ok(t)
    print(f"\n== {path} ({n} respuestas) ==")
    total = 0
    for name, ok in CRITERIA:
        total += totals[name]
        print(f"  {name}: {totals[name]}/{n}")
    print(f"  SCORE: {total}/{n * len(CRITERIA)}")
    return total

if __name__ == "__main__":
    for path in sys.argv[1:]:
        score(path)
