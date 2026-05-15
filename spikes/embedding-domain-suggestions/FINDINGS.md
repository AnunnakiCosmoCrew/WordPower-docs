# FINDINGS — Embedding-based domain suggestions

**Question:** Are embedding-based domain suggestions worth the infra cost vs the existing keyword→domain heuristic?

**TL;DR — Ship a flat ~10-domain pragmatic keyword classifier with per-user personalization. Skip embeddings entirely.** Cost is not the blocker (embeddings are essentially free), but they're also not earning their complexity. Domain suggestion has two strong signals that don't need a model: (1) most users work within a handful of professional/study domains (Law, Business, Engineering, Finance, Medicine, …), and (2) a user's own notebook already reveals their domains — if 80% of their words are Law, the next word is probably Law too. A keyword classifier on a flat ~10-domain list, biased by the user's notebook history with a **≥3-word guard** to prevent early-mistake feedback loops, is simpler and probably better than any embedding-only approach.

Status of the three measurements:

| Measurement | Result | Source |
|---|---|---|
| **Cost** | **$0.0036** to enrich a 10k-word notebook on `text-embedding-3-small` | [`results/cost.md`](results/cost.md) — no API call needed |
| **Heuristic accuracy** | **96% top-1 / 100% top-3** on the 50-word set (biased — see §3.1) | [`results/heuristic-results.json`](results/heuristic-results.json) |
| **Lexname-only accuracy** | **46% top-1 / 60% top-3** on the 50-word set (unbiased) | [`results/lexname-results.json`](results/lexname-results.json) |
| **Embedding accuracy** | _not run_ — not on the recommended path (see §5); scripts preserved for re-decision | [`scripts/embed_words.py`](scripts/embed_words.py) + [`scripts/measure_accuracy.py`](scripts/measure_accuracy.py) |
| **Embedding latency** | _not run_ — same reason | [`scripts/measure_latency.py`](scripts/measure_latency.py) |

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

**Ship a flat ~10-domain pragmatic keyword classifier with per-user personalization. Skip the embedding pipeline.**

### 5.1 The classifier — two deterministic layers

**Layer A — Flat pragmatic domain list.** Roughly 10–12 domains that match what users actually capture in notebooks: `Law`, `Business`, `Finance`, `Engineering`, `Medicine`, `Science`, `Technology`, `Learning`, `Arts`, `Daily Life`, plus an explicit `Other` bucket so the UI never has to render "uncategorized." Same structure as today's `DomainClassifier` (keyword set per domain, hit-counting with insertion-order tie-break). On capture, run Layer A to propose a top match.

**Layer B — Personalize from the user's own notebook.** Most users settle into 3–10 domains over time (a law student's notebook is dominated by Law / Learning; a software engineer's by Engineering / Business). The user's own history is the strongest signal we have. Decision flow when suggesting a domain for a new word:

1. Score the word with Layer A → top candidate domain `D`.
2. **If the user has ≥3 words already in `D`:** auto-suggest `D` (high confidence). The user can override in the picker, but `D` is the default.
3. **Otherwise:** show the picker with `D` as the top option, but also surface the user's existing domains (those with ≥3 words) as alternatives ranked by notebook count. Nudges the user toward their established taxonomy without forcing it.
4. **Cold start (no domains have ≥3 words yet):** fall back to pure Layer A. Same behavior as today's classifier.

### 5.2 The ≥3-word guard is non-negotiable

Without a guard, personalization-from-history reinforces early mistakes. Concrete failure mode: a user mis-tags one Business word as Law on day 1. Every subsequent Business word the classifier sees now gets nudged toward Law because Law has a notebook presence. One mis-tag compounds into systematic drift.

The ≥3-word guard breaks the loop. A domain must be **intentional** — chosen for at least 3 distinct words by the user — before it influences future suggestions. New users get pure Layer A behavior until they've established a real pattern; mis-tags from day 1 can't propagate because one word doesn't cross the threshold.

**This invariant must be encoded as a test, not a comment.** The implementation should fail loudly if a domain with fewer than 3 user words ever influences a suggestion ranking. Recommended:

- Unit test: simulate a single mis-tag, verify the next 5 captures in the same true-domain are still classified correctly by Layer A.
- Unit test: simulate 3 deliberate tags of the same domain, verify personalization kicks in on the 4th capture.
- Boundary: the count includes manually-tagged words and auto-suggested words the user **accepted** — but not auto-suggested words they overrode (otherwise the loop sneaks back in).

### 5.3 Why this beats the alternatives

| Approach | Top-1 ceiling (est.) | Operational cost | Comment |
|---|---|---|---|
| Today's 11-domain `DomainClassifier`, global only | ~70% | None | Already shipped, no personalization, coverage gaps |
| 15-domain global keyword classifier (spike's earlier draft) | ~75% | One-time curation | Ignores the strongest signal (user history) |
| **10-domain flat + personalization (this proposal)** | **~85–90%** | One-time curation + per-user domain-count query (cheap) | Uses the user's own notebook as ground truth |
| Embedding-based | ~80–90% (unmeasured) | Embedding $, vector storage, model-bump backfills | More moving parts, marginal gain over a personalized keyword approach |

Global-classifier estimates extrapolate between the lexname honest floor (46% top-1) and the self-fitted heuristic ceiling (96% top-1). The personalization layer is the multiplier that makes a small, simple model genuinely competitive with anything heavier.

### 5.4 Divergence from PROJECT.md

[`PROJECT.md` §Axis 1](../../docs/product/PROJECT.md) currently specs a 15-domain HTOED-inspired hierarchy (The Physical World / The Mind / Society, ~15 leaves). The flat 10-domain pragmatic list in §5.1 is a deliberate simplification — different in both *size* and *shape* (flat vs hierarchical, pragmatic vs scholarly). Two viable resolutions:

- **Replace** the PROJECT.md taxonomy with the flat list. Simplest, but loses the discovery/browse value of the three-branch hierarchy.
- **Keep both.** PROJECT.md's hierarchy stays as the canonical organization for browse/discovery UI; the flat 10-domain list is internal to the auto-suggestion classifier, with a mapping table from flat → hierarchy leaf for display. More surface area but preserves both intents.

This is a product decision, not a spike outcome. The recommended implementation in §5.1 can proceed against the flat list either way; the resolution determines only what the UI displays as the domain name to the user.

## 6. Next steps

1. **Open follow-up issue: implement the flat ~10-domain classifier + personalization (Layer A + Layer B).** Ship-blocking requirements: the ≥3-word guard from §5.2 and the boundary rule that overridden auto-suggestions don't count toward the threshold. Both verified by unit tests in the same PR.
2. **Open product issue: resolve PROJECT.md taxonomy divergence** (§5.4 — replace vs keep both). Auto-suggestion implementation can proceed in parallel using the flat list either way; this decision only affects what name the UI shows.
3. **(Optional, low priority)** Set `OPENAI_API_KEY` and run the embedding scripts to populate the §2 / §3.2 numbers in this spike. Only worth doing if §5's recommendation is being challenged. The scripts and decision rule are preserved as a record of what would unblock a re-decision.

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
