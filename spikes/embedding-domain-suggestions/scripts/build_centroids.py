#!/usr/bin/env python3
"""Embed every centroid seed text and write `results/centroids.json`.

Run once per (model, taxonomy) combination. Output is consumed by
`measure_accuracy.py` and `measure_latency.py`.

Requires:
    export OPENAI_API_KEY=sk-...
    pip install openai
"""

import json
import os
import pathlib
import time

from openai import OpenAI

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY not set. See README.md §Setup.")

    client = OpenAI()
    centroids = json.load(open(DATA / "domain-centroids.json"))["centroids"]

    t0 = time.time()
    resp = client.embeddings.create(
        model=MODEL,
        input=[c["seed"] for c in centroids],
    )
    elapsed_ms = (time.time() - t0) * 1000

    for c, d in zip(centroids, resp.data):
        c["vector"] = d.embedding

    out = {
        "model": MODEL,
        "dim": len(resp.data[0].embedding),
        "centroids": centroids,
        "build_elapsed_ms": round(elapsed_ms, 1),
        "total_tokens": resp.usage.total_tokens,
    }
    with open(RESULTS / "centroids.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"Embedded {len(centroids)} centroids in {elapsed_ms:.0f}ms "
          f"({resp.usage.total_tokens} tokens). Wrote results/centroids.json")


if __name__ == "__main__":
    main()
