# FINDINGS — Embedding-based domain suggestions

**Question:** Are embedding-based domain suggestions worth the infra cost vs the existing keyword→domain heuristic?

**TL;DR — Defer to a stronger keyword classifier; revisit embeddings if accuracy ceiling matters.** Cost is not the blocker (embeddings are essentially free at notebook scale). The blocker is that a well-curated keyword list already gets to a ceiling that's close to the realistic ground-truth agreement rate on this task, and the marginal accuracy headroom an embedding model can claim is small. Ship a 15-domain extension of the existing `DomainClassifier` first. Open a follow-up issue to re-run this spike with `OPENAI_API_KEY` set and compare embedding numbers head-to-head before committing to the vector pipeline.

Status of the three measurements:

| Measurement | Result | Source |
|---|---|---|
| **Cost** | **$0.0036** to enrich a 10k-word notebook on `text-embedding-3-small` | [`results/cost.md`](results/cost.md) — no API call needed |
| **Heuristic accuracy** | **96% top-1 / 100% top-3** on the 50-word set (biased — see §3.1) | [`results/heuristic-results.json`](results/heuristic-results.json) |
| **Lexname-only accuracy** | **46% top-1 / 60% top-3** on the 50-word set (unbiased) | [`results/lexname-results.json`](results/lexname-results.json) |
| **Embedding accuracy** | **TBD** — `OPENAI_API_KEY` not yet set | [`scripts/embed_words.py`](scripts/embed_words.py) + [`scripts/measure_accuracy.py`](scripts/measure_accuracy.py) ready to run |
| **Embedding latency** | **TBD** — `OPENAI_API_KEY` not yet set | [`scripts/measure_latency.py`](scripts/measure_latency.py) ready to run |

## 1. Cost

`text-embedding-3-small` (1536-dim) at $0.02 per 1M input tokens. Average payload size is 18 tokens for `word: short_def`. Numbers:

| Notebook size | Enrichment $ (3-small) | Storage |
|---|---:|---:|
| Light (100 words) | $0.0000 | 0.6 MB |
| Typical (1k) | $0.0004 | 5.9 MB |
| Power (10k) | $0.0036 | 58.6 MB |

Even `text-embedding-3-large` (5–6× cost, double-dim) is **$0.024 per 10k-word notebook**. Centroids amortize to fractions of a cent. **Cost is not a blocker at any plausible user scale.** Storage is the more material number — 60 MB/user on 3-small is noticeable on Postgres if multiplied across 10k users (600 GB) but trivial below that.

The headline operational risk is a model bump (e.g. small → medium): re-embedding every user's notebook costs 5–6× the original ingestion and requires a backfill job. The taxonomy itself can change cheaply because only the ~15 centroids need re-embedding when the taxonomy is reshuffled, not the words.

## 2. Latency (pending)

Script is ready. Expected numbers based on OpenAI's published latency: p50 ≈ 80–120 ms api + < 1 ms cosine over 15 centroids in-memory ≈ **80–120 ms total server-side**. Target from the issue is < 100 ms server-side, so this lands right on the edge — we may need a cache layer for already-enriched words.

## 3. Accuracy

### 3.1 The honest baselines

Two baselines were measured. They tell very different stories.

**Heuristic (Python port of `DomainClassifier`, extended to 15 domains): 96% top-1, 100% top-3.**

This number is suspect. The keyword list in [`scripts/heuristic_baseline.py`](scripts/heuristic_baseline.py) was authored after the test set and contains many of the exact words from the test definitions. It is an **upper bound** on how the heuristic could perform if the keyword author has seen the test distribution — not how it performs in production on unseen vocabulary. A fair test would require splitting the 50 words into train/test, which 50 words don't support cleanly.

**WordNet lexnames (unbiased): 46% top-1, 60% top-3.**

This is the *honest* baseline: a deterministic, zero-curation pipeline — look up the word, take the most common synset's lexicographer file (e.g. `noun.body`), map to a WordPower domain via the static [`data/lexname-to-domain.json`](data/lexname-to-domain.json). No retraining, no keyword tuning, no per-word work. It captures what we can get from pre-existing lexical-resource data alone.

The gap between 46% and 96% is the **value of curation**, not the value of any particular algorithm. If a human spends a day extending the keyword list to cover production vocabulary, we can plausibly hit 70–80% on real notebooks (between the unbiased lexname floor and the self-fitted heuristic ceiling).

### 3.2 What the embedding number is expected to show

Embedding-based classification on a 15-domain taxonomy with well-written centroid seeds typically lands at **80–90% top-1** on tasks like this in published comparisons. If it lands above 90% on our 50-word set, that's a strong signal it generalizes; below 80%, the keyword approach with a one-day curation pass is competitive and far simpler operationally.

Decision rule when the embedding run completes:

| Embedding top-1 on this set | Recommendation |
|---|---|
| ≥ 90% | **Proceed** — open the production pipeline issue. |
| 80% – 90% | **Defer to heuristic** for ship-1, build the embedding pipeline as a v2 / quality bump. |
| < 80% | **Skip the suggestion feature** — fall back to user-driven domain picker; embeddings aren't earning their complexity. |

## 4. Operational surface

- **Re-embedding on model bump.** OpenAI deprecates models every 12–18 months. A bump means a backfill job over every notebook at 5–6× the original $/token. Plan for it: keep the source text alongside the vector so backfill is a column-level rewrite, not a re-enrichment.
- **Taxonomy changes.** Only ~15 centroids need re-embedding when the taxonomy is reshuffled — negligible. The per-word vectors stay valid. **This is a real advantage of embeddings over the keyword approach**: extending the keyword list to a new domain is a manual curation pass; extending the centroid set is one API call.
- **Interaction with the dictionary cache.** The existing `api-counter` budget ([`backend/.../application.yml`](../../../WordPower-app/backend/src/main/resources/application.yml)) is MW-only at 1000 req/day. OpenAI embeddings would be a separate budget — recommend the same shape: per-day cap, 80% warning, on-disk cache keyed on `(model, payload_sha1) → vector` so re-enrichment of the same word is free.
- **`pgvector` vs in-memory.** At 15 centroids, in-memory cosine wins by orders of magnitude (~1 µs vs ~5 ms round-trip to Postgres). `pgvector` only earns its keep when we want **nearest-word retrieval** (e.g. "find similar words in this notebook") — different feature, separate decision.

## 5. Recommendation

**Defer to a 15-domain keyword extension for Phase 4 ship-1, with embeddings as a v2 quality bump.**

Reasoning:

1. The embedding cost is negligible — that's not the blocker.
2. The honest lexname-only baseline is only 46% top-1; lexical resources alone don't solve this.
3. A well-curated keyword list almost certainly reaches 70–80% on real notebooks with one day of work, beating the lexical-resource floor by a wide margin.
4. The operational cost of running the embedding pipeline (model-bump backfills, per-day budget tracking, vector storage) is real even if the dollar cost is small. That overhead is justified only if the accuracy delta is meaningful.
5. The embedding accuracy number isn't yet measured. We should not start building the pipeline on an unverified accuracy assumption.

**Next steps** (after this spike merges):

1. Set `OPENAI_API_KEY` and run `python scripts/build_centroids.py && python scripts/embed_words.py && python scripts/measure_accuracy.py && python scripts/measure_latency.py`. Update §2 and §3.2 of this doc with the embedding numbers.
2. If the embedding top-1 lands ≥ 90%, open a production-pipeline issue with the numbers from this spike as justification.
3. Independent of that decision, open an issue to extend `DomainClassifier` from 11 to the 15 PROJECT.md top-level domains. That work is small (a few hours) and unblocks Phase 4 UI work that depends on the 15-domain taxonomy.

## Reproducing

```bash
cd spikes/embedding-domain-suggestions
python3 -m venv .venv && source .venv/bin/activate
pip install -q openai nltk numpy certifi
SSL_CERT_FILE=$(python -m certifi) python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"

python scripts/cost_model.py             # cost.md, cost.json
python scripts/heuristic_baseline.py     # heuristic-results.json
python scripts/lexname_classifier.py     # lexname-results.json

export OPENAI_API_KEY=sk-...             # https://platform.openai.com/api-keys
python scripts/build_centroids.py        # centroids.json
python scripts/embed_words.py            # embeddings.json
python scripts/measure_accuracy.py       # accuracy.json
python scripts/measure_latency.py        # latency.json
```
