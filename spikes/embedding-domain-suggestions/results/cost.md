# Cost model — embedding-based domain suggestions

_All numbers computed by `scripts/cost_model.py`. Pricing source: <https://platform.openai.com/docs/pricing> (checked 2026-05). Tokens estimated at 1 per 4 chars; verify against tiktoken before quoting for production._

## Inputs

- Test payloads: 50 `word: short_def` strings
- Avg tokens per payload: **18.2**, p95: **24**
- Centroids: 15, total seed tokens: 466

## Per-model cost

| Model | dim | $/1M tok | $/word | Centroid one-time | Bytes/vec |
|---|---:|---:|---:|---:|---:|
| `text-embedding-3-small` | 1536 | $0.0200 | $0.000000 | $0.000009 | 6,144 |
| `text-embedding-3-large` | 3072 | $0.1300 | $0.000002 | $0.000061 | 12,288 |
| `text-embedding-ada-002` | 1536 | $0.1000 | $0.000002 | $0.000047 | 6,144 |

## Per-user-notebook (one-time enrichment + storage)

| Model | Notebook | Words | Enrichment $ | Vector storage |
|---|---|---:|---:|---:|
| `text-embedding-3-small` | light | 100 | $0.0000 | 0.586 MB |
| `text-embedding-3-small` | typical | 1,000 | $0.0004 | 5.859 MB |
| `text-embedding-3-small` | power | 10,000 | $0.0036 | 58.594 MB |
| `text-embedding-3-large` | light | 100 | $0.0002 | 1.172 MB |
| `text-embedding-3-large` | typical | 1,000 | $0.0024 | 11.719 MB |
| `text-embedding-3-large` | power | 10,000 | $0.0237 | 117.188 MB |
| `text-embedding-ada-002` | light | 100 | $0.0002 | 0.586 MB |
| `text-embedding-ada-002` | typical | 1,000 | $0.0018 | 5.859 MB |
| `text-embedding-ada-002` | power | 10,000 | $0.0182 | 58.594 MB |

## Interpretation

- A typical user (1k words) on `text-embedding-3-small`: roughly **$0.0004** in one-time embedding cost, **5.859 MB** vector storage.
- The 10k-word ceiling is **$0.0036** and **58.594 MB** per power user.
- Centroids are embedded once (or on taxonomy bump) — negligible.
- A model bump (e.g. 3-small → 3-large) requires re-embedding every word at the new model's $/token (5–6× higher).
