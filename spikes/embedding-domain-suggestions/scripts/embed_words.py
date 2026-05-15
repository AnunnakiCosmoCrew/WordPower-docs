#!/usr/bin/env python3
"""Embed every test word's `"word: short_def"` payload and write
`results/embeddings.json`.

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
    words = json.load(open(DATA / "test-words.json"))["words"]
    payloads = [f"{w['word']}: {w['short_def']}" for w in words]

    t0 = time.time()
    resp = client.embeddings.create(model=MODEL, input=payloads)
    elapsed_ms = (time.time() - t0) * 1000

    for w, d in zip(words, resp.data):
        w["vector"] = d.embedding

    out = {
        "model": MODEL,
        "dim": len(resp.data[0].embedding),
        "words": words,
        "embed_elapsed_ms": round(elapsed_ms, 1),
        "total_tokens": resp.usage.total_tokens,
    }
    with open(RESULTS / "embeddings.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"Embedded {len(words)} words in {elapsed_ms:.0f}ms "
          f"({resp.usage.total_tokens} tokens). Wrote results/embeddings.json")


if __name__ == "__main__":
    main()
