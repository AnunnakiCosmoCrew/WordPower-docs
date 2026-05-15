#!/usr/bin/env python3
"""WordNet-lexname classifier — uses NLTK's WordNet lexicographer files as
the sole signal. Looks up the headword, takes the lexname (e.g. `noun.body`)
of the most frequent synset, maps to a WordPower domain via
`data/lexname-to-domain.json`.

This is a third comparator in addition to the keyword heuristic and the
embedding classifier. It is a free, deterministic baseline — no API calls,
no manual keyword curation — and exposes how much of the work pre-existing
lexical-resource data already does.

Requires NLTK + WordNet:
    pip install nltk
    python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
"""

import json
import pathlib

try:
    from nltk.corpus import wordnet as wn
except ImportError:
    print("nltk not installed. Run: pip install nltk && "
          "python -c \"import nltk; nltk.download('wordnet')\"")
    raise SystemExit(1)

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RESULTS = ROOT / "results"


def classify_top_k(word: str, lexname_map: dict, k: int = 3) -> "list[str]":
    """Return up to k unique WordPower domains, ranked by synset count for that lexname."""
    synsets = wn.synsets(word)
    if not synsets:
        return []
    # Count distinct WordPower domains weighted by appearance order (most common synset wins).
    weighted: "dict[str, int]" = {}
    for i, syn in enumerate(synsets):
        lex = syn.lexname()
        dom = lexname_map.get(lex)
        if dom is None:
            continue
        # Earlier synsets (more frequent) get higher weight.
        weight = len(synsets) - i
        weighted[dom] = weighted.get(dom, 0) + weight
    ranked = sorted(weighted.items(), key=lambda x: -x[1])
    return [d for d, _ in ranked[:k]]


def main() -> None:
    words = json.load(open(DATA / "test-words.json"))["words"]
    lexname_map = json.load(open(DATA / "lexname-to-domain.json"))["mapping"]

    correct_top1 = 0
    correct_top3 = 0
    no_signal = 0
    per_word = []
    for w in words:
        top3 = classify_top_k(w["word"], lexname_map, 3)
        top1 = top3[0] if top3 else None
        gold = w["gold"]
        if top1 is None:
            no_signal += 1
        if top1 == gold:
            correct_top1 += 1
        if gold in top3:
            correct_top3 += 1
        per_word.append({
            "word": w["word"], "gold": gold,
            "lexname_top1": top1, "lexname_top3": top3,
            "match_top1": top1 == gold,
            "match_top3": gold in top3,
        })

    n = len(words)
    summary = {
        "n": n,
        "top1_accuracy": round(correct_top1 / n, 3),
        "top3_accuracy": round(correct_top3 / n, 3),
        "no_signal_words": no_signal,
        "per_word": per_word,
    }
    out = RESULTS / "lexname-results.json"
    json.dump(summary, open(out, "w"), indent=2)
    print(f"Lexname top-1: {summary['top1_accuracy']:.1%}")
    print(f"Lexname top-3: {summary['top3_accuracy']:.1%}")
    print(f"No-signal words (no WordNet entry / unmapped lexname): {no_signal}/{n}")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
