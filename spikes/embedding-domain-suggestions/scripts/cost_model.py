#!/usr/bin/env python3
"""Back-of-envelope cost model for embedding-based domain suggestions.

Computes:
  - tokens per "word + short_def" payload (approximate, BPE-agnostic)
  - $/word for several embedding models at current OpenAI pricing
  - $/notebook at 100 / 1k / 10k words
  - vector storage per word and per notebook
  - one-time centroid cost

No network calls. Pricing/dimensions are constants and must be checked against
https://platform.openai.com/docs/pricing before quoting numbers downstream.
"""

import json
import pathlib
import math

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

# OpenAI embedding pricing (per 1M input tokens) as of 2026-05.
# https://platform.openai.com/docs/pricing
MODELS = {
    "text-embedding-3-small": {"dim": 1536, "usd_per_1m_tokens": 0.02},
    "text-embedding-3-large": {"dim": 3072, "usd_per_1m_tokens": 0.13},
    "text-embedding-ada-002": {"dim": 1536, "usd_per_1m_tokens": 0.10},
}

# Rough English BPE token estimate: ~1 token per 4 chars. Used because we
# intentionally avoid pulling tiktoken just for an envelope number — tiktoken
# disagrees with OpenAI's by <5% for normal English prose.
def approx_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def main() -> None:
    words = json.load(open(DATA / "test-words.json"))["words"]
    centroids = json.load(open(DATA / "domain-centroids.json"))["centroids"]

    payloads = [f"{w['word']}: {w['short_def']}" for w in words]
    tok_per_payload = [approx_tokens(p) for p in payloads]
    avg_tok = sum(tok_per_payload) / len(tok_per_payload)
    p95_tok = sorted(tok_per_payload)[int(0.95 * len(tok_per_payload))]

    centroid_tok = sum(approx_tokens(c["seed"]) for c in centroids)

    notebook_sizes = {"light": 100, "typical": 1_000, "power": 10_000}

    out = {
        "assumptions": {
            "tokens_per_char": 0.25,
            "avg_tokens_per_word_payload": round(avg_tok, 2),
            "p95_tokens_per_word_payload": p95_tok,
            "centroid_count": len(centroids),
            "centroid_total_tokens": centroid_tok,
            "pricing_source": "https://platform.openai.com/docs/pricing",
            "pricing_date": "2026-05",
        },
        "per_model": {},
    }

    for model_name, m in MODELS.items():
        usd_per_token = m["usd_per_1m_tokens"] / 1_000_000
        per_word = avg_tok * usd_per_token
        centroid_one_time = centroid_tok * usd_per_token
        bytes_per_vec = m["dim"] * 4  # float32

        notebooks = {}
        for label, n in notebook_sizes.items():
            notebooks[label] = {
                "words": n,
                "enrichment_usd_per_user_once": round(per_word * n, 6),
                "vector_storage_bytes_per_user": bytes_per_vec * n,
                "vector_storage_mb_per_user": round(bytes_per_vec * n / 1024 / 1024, 3),
            }

        out["per_model"][model_name] = {
            "dim": m["dim"],
            "usd_per_1m_input_tokens": m["usd_per_1m_tokens"],
            "usd_per_word_enrichment": round(per_word, 8),
            "centroid_one_time_usd": round(centroid_one_time, 8),
            "bytes_per_vector_float32": bytes_per_vec,
            "notebooks": notebooks,
        }

    with open(RESULTS / "cost.json", "w") as f:
        json.dump(out, f, indent=2)

    # Markdown summary
    lines = [
        "# Cost model — embedding-based domain suggestions",
        "",
        "_All numbers computed by `scripts/cost_model.py`. Pricing source: <https://platform.openai.com/docs/pricing> (checked 2026-05). Tokens estimated at 1 per 4 chars; verify against tiktoken before quoting for production._",
        "",
        "## Inputs",
        "",
        f"- Test payloads: {len(payloads)} `word: short_def` strings",
        f"- Avg tokens per payload: **{avg_tok:.1f}**, p95: **{p95_tok}**",
        f"- Centroids: {len(centroids)}, total seed tokens: {centroid_tok}",
        "",
        "## Per-model cost",
        "",
        "| Model | dim | $/1M tok | $/word | Centroid one-time | Bytes/vec |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, m in out["per_model"].items():
        lines.append(
            f"| `{name}` | {m['dim']} | ${m['usd_per_1m_input_tokens']:.4f} | "
            f"${m['usd_per_word_enrichment']:.6f} | "
            f"${m['centroid_one_time_usd']:.6f} | "
            f"{m['bytes_per_vector_float32']:,} |"
        )

    lines += [
        "",
        "## Per-user-notebook (one-time enrichment + storage)",
        "",
        "| Model | Notebook | Words | Enrichment $ | Vector storage |",
        "|---|---|---:|---:|---:|",
    ]
    for name, m in out["per_model"].items():
        for label, nb in m["notebooks"].items():
            lines.append(
                f"| `{name}` | {label} | {nb['words']:,} | "
                f"${nb['enrichment_usd_per_user_once']:.4f} | "
                f"{nb['vector_storage_mb_per_user']} MB |"
            )

    lines += [
        "",
        "## Interpretation",
        "",
        f"- A typical user (1k words) on `text-embedding-3-small`: roughly "
        f"**${out['per_model']['text-embedding-3-small']['notebooks']['typical']['enrichment_usd_per_user_once']:.4f}** "
        f"in one-time embedding cost, **{out['per_model']['text-embedding-3-small']['notebooks']['typical']['vector_storage_mb_per_user']} MB** "
        f"vector storage.",
        f"- The 10k-word ceiling is **${out['per_model']['text-embedding-3-small']['notebooks']['power']['enrichment_usd_per_user_once']:.4f}** "
        f"and **{out['per_model']['text-embedding-3-small']['notebooks']['power']['vector_storage_mb_per_user']} MB** per power user.",
        "- Centroids are embedded once (or on taxonomy bump) — negligible.",
        "- A model bump (e.g. 3-small → 3-large) requires re-embedding every word at the new model's $/token (5–6× higher).",
        "",
    ]
    with open(RESULTS / "cost.md", "w") as f:
        f.write("\n".join(lines))

    print("Wrote results/cost.json and results/cost.md")
    print(f"  avg tokens/payload: {avg_tok:.1f}")
    print(f"  $/word (3-small): ${out['per_model']['text-embedding-3-small']['usd_per_word_enrichment']:.6f}")
    print(f"  10k notebook (3-small): ${out['per_model']['text-embedding-3-small']['notebooks']['power']['enrichment_usd_per_user_once']:.4f}")


if __name__ == "__main__":
    main()
