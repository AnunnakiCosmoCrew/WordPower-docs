#!/usr/bin/env python3
"""Measure end-to-end latency for: embed query word → cosine sim vs all
centroids → return top-3. Writes `results/latency.json`.

Runs `iterations` queries (default 20) and reports p50 / p95 / p99 broken
down into:
  - api_ms   — OpenAI embeddings call
  - score_ms — cosine sim over 15 centroids in-memory
  - total_ms — api_ms + score_ms

Requires:
    export OPENAI_API_KEY=sk-...
    pip install openai numpy
"""

import json
import os
import pathlib
import time

import numpy as np
from openai import OpenAI

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RESULTS = ROOT / "results"

MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
ITERATIONS = int(os.environ.get("LATENCY_ITERATIONS", "20"))


def percentile(xs: list[float], p: float) -> float:
    return float(np.percentile(xs, p))


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY not set. See README.md §Setup.")
    if not (RESULTS / "centroids.json").exists():
        raise SystemExit("Run scripts/build_centroids.py first.")

    centroids_doc = json.load(open(RESULTS / "centroids.json"))
    cents = np.array(
        [c["vector"] for c in centroids_doc["centroids"]], dtype=np.float32
    )
    cents_norm = cents / np.linalg.norm(cents, axis=1, keepdims=True)

    words = json.load(open(DATA / "test-words.json"))["words"]
    # Cycle through test words to vary input.
    queries = [f"{w['word']}: {w['short_def']}" for w in words][:ITERATIONS]

    client = OpenAI()
    samples = []
    for q in queries:
        t0 = time.perf_counter()
        resp = client.embeddings.create(model=MODEL, input=q)
        t_api = time.perf_counter()
        wvec = np.array(resp.data[0].embedding, dtype=np.float32)
        wvec_norm = wvec / np.linalg.norm(wvec)
        sims = cents_norm @ wvec_norm
        # Force an actual top-3 to keep numpy honest.
        top3_idx = np.argpartition(-sims, 3)[:3]
        _ = sorted(top3_idx, key=lambda i: -sims[i])
        t_end = time.perf_counter()
        samples.append(
            {
                "api_ms": (t_api - t0) * 1000,
                "score_ms": (t_end - t_api) * 1000,
                "total_ms": (t_end - t0) * 1000,
            }
        )

    def stats(key: str) -> dict:
        xs = [s[key] for s in samples]
        return {
            "p50": round(percentile(xs, 50), 2),
            "p95": round(percentile(xs, 95), 2),
            "p99": round(percentile(xs, 99), 2),
            "mean": round(sum(xs) / len(xs), 2),
            "min": round(min(xs), 2),
            "max": round(max(xs), 2),
        }

    out = {
        "model": MODEL,
        "centroid_count": cents.shape[0],
        "iterations": ITERATIONS,
        "api_ms": stats("api_ms"),
        "score_ms": stats("score_ms"),
        "total_ms": stats("total_ms"),
        "samples": samples,
    }
    with open(RESULTS / "latency.json", "w") as f:
        json.dump(out, f, indent=2)

    print(f"Latency over {ITERATIONS} iterations:")
    print(f"  api_ms   p50={out['api_ms']['p50']}  p95={out['api_ms']['p95']}  p99={out['api_ms']['p99']}")
    print(f"  score_ms p50={out['score_ms']['p50']}  p95={out['score_ms']['p95']}")
    print(f"  total_ms p50={out['total_ms']['p50']}  p95={out['total_ms']['p95']}  p99={out['total_ms']['p99']}")


if __name__ == "__main__":
    main()
