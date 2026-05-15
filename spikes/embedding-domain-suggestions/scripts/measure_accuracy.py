#!/usr/bin/env python3
"""Score embedding domain classification against the gold labels in
`data/test-words.json` and write `results/accuracy.json`.

Reads pre-computed embeddings from `results/embeddings.json` and
`results/centroids.json` — run `embed_words.py` and `build_centroids.py`
first.

Cosine similarity. Top-1 and top-3 accuracy reported alongside the heuristic
and lexname baselines (loaded from their respective results JSON for direct
comparison in one file).
"""

import json
import pathlib

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def main() -> None:
    if not (RESULTS / "embeddings.json").exists():
        raise SystemExit(
            "results/embeddings.json missing. Run scripts/embed_words.py first."
        )
    if not (RESULTS / "centroids.json").exists():
        raise SystemExit(
            "results/centroids.json missing. Run scripts/build_centroids.py first."
        )

    embeddings = json.load(open(RESULTS / "embeddings.json"))
    centroids_doc = json.load(open(RESULTS / "centroids.json"))

    cents = [
        {"id": c["id"], "vec": np.array(c["vector"], dtype=np.float32)}
        for c in centroids_doc["centroids"]
    ]

    correct_top1 = 0
    correct_top3 = 0
    per_word = []
    for w in embeddings["words"]:
        wvec = np.array(w["vector"], dtype=np.float32)
        sims = [(c["id"], cosine(wvec, c["vec"])) for c in cents]
        sims.sort(key=lambda x: -x[1])
        top3 = [s[0] for s in sims[:3]]
        top1 = top3[0]
        gold = w["gold"]
        if top1 == gold:
            correct_top1 += 1
        if gold in top3:
            correct_top3 += 1
        per_word.append(
            {
                "word": w["word"],
                "gold": gold,
                "embedding_top1": top1,
                "embedding_top3": top3,
                "embedding_top1_sim": round(sims[0][1], 4),
                "match_top1": top1 == gold,
                "match_top3": gold in top3,
            }
        )

    n = len(embeddings["words"])
    embedding_summary = {
        "model": embeddings["model"],
        "n": n,
        "top1_accuracy": round(correct_top1 / n, 3),
        "top3_accuracy": round(correct_top3 / n, 3),
    }

    # Load baselines for one-shot side-by-side reporting.
    baselines = {}
    for name, path in [
        ("heuristic", RESULTS / "heuristic-results.json"),
        ("lexname", RESULTS / "lexname-results.json"),
    ]:
        if path.exists():
            r = json.load(open(path))
            baselines[name] = {
                "top1_accuracy": r["top1_accuracy"],
                "top3_accuracy": r["top3_accuracy"],
                "no_signal_words": r.get("no_signal_words"),
            }

    out = {
        "embedding": embedding_summary,
        "baselines": baselines,
        "per_word": per_word,
    }
    with open(RESULTS / "accuracy.json", "w") as f:
        json.dump(out, f, indent=2)

    print(f"Embedding ({embeddings['model']}):")
    print(f"  top-1: {embedding_summary['top1_accuracy']:.1%}")
    print(f"  top-3: {embedding_summary['top3_accuracy']:.1%}")
    for name, b in baselines.items():
        print(f"{name}:")
        print(f"  top-1: {b['top1_accuracy']:.1%}")
        print(f"  top-3: {b['top3_accuracy']:.1%}")
    print(f"Wrote {RESULTS / 'accuracy.json'}")


if __name__ == "__main__":
    main()
