# Spike — Embedding-based domain suggestion cost/UX validation

**Question:** Are embedding-based domain suggestions worth the infra cost vs the existing keyword→domain heuristic classifier?

**Architecture context:** Phase 4 — Vocabulary System: Organized Learning. The current implementation in `WordPower-app/backend/.../DomainClassifier.java` is an 11-domain keyword classifier. The long-term plan ([`PROJECT.md` §Axis 1](../../docs/product/PROJECT.md)) defines a 15-domain top-level taxonomy organized in three branches (The Physical World / The Mind / Society) and contemplates richer assignment via embeddings.

**Issue:** [#655](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/655)

**Estimate:** 5 points (~1 day)

## Method

### 1. Cost model

Compute back-of-envelope costs for `text-embedding-3-small` (1536-dim) at:

- $/word at enrichment time (sample 50 real "word + short definition" payloads to size the average token count).
- Vector storage per word; total bytes at the 10k-word notebook ceiling.
- Total $/user/year at three usage profiles (light: 100 words, typical: 1k, power: 10k).

Run with `python scripts/cost_model.py`. Output: `results/cost.md` + `results/cost.json`.

### 2. Latency

Measure round-trip: embed query word → cosine-sim vs ~15 centroids → return top-3. 20 iterations, report p50 / p95 / p99. Target: < 100 ms server-side. Run with `python scripts/measure_latency.py` (requires `OPENAI_API_KEY`).

### 3. Accuracy (triangulated ground truth)

50 hand-picked words distributed roughly evenly across the 15 PROJECT.md top-level domains. Each word gets three ground-truth labels and a final consensus label:

- **(a) MW Collegiate `sl` field** — the Collegiate API returns subject labels (unlike MW Learner's, which we use for the app's primary enrichment). Used for the ~15-25 words where `sl` is present.
- **(b) WordNet lexicographer file (lexname)** — `noun.body`, `verb.communication`, etc. ~45 lexnames mapped to the 15 WordPower top-level domains.
- **(c) Hand-label** — the human gold label. Used as the comparison target and as tiebreaker when (a) and (b) disagree.

Comparators:

1. **Embedding** — `text-embedding-3-small`, cosine sim against 15 centroids built from canonical seed text per domain.
2. **Heuristic** — Python port of the existing `DomainClassifier` keyword logic. Extended to 15 domains for an apples-to-apples comparison.
3. **Do-nothing baseline** — predict the modal domain in the labeled set every time.

Run with `python scripts/measure_accuracy.py`. Output: `results/accuracy.json`.

### 4. Operational surface

Documented prose in `FINDINGS.md`:

- Re-embedding cost when the model bumps (e.g. small → medium).
- Re-embedding cost when the taxonomy changes (centroids only vs all words).
- Interaction with the existing dictionary cache and `api-counter` budget.
- In-memory cosine vs `pgvector` at 15 centroids/word (in-memory wins; pgvector is overkill until nearest-word retrieval is needed).

## Acceptance criteria

- [ ] Doc committed under `WordPower-docs/spikes/embedding-domain-suggestions/`.
- [ ] Numeric findings included (cost, latency, accuracy).
- [ ] Clear go/no-go recommendation with reasoning.

## Setup

```bash
# One-time
python3 -m venv .venv && source .venv/bin/activate
pip install openai nltk numpy
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"

# Per-shell — get a key at https://platform.openai.com/api-keys
export OPENAI_API_KEY=sk-...

# Optional — only needed for the MW Collegiate ground-truth fetch
export MW_COLLEGIATE_API_KEY=...
```

## Output layout

```
embedding-domain-suggestions/
  README.md
  data/
    domain-centroids.json     # 15 domains + seed text per centroid
    test-words.json           # 50 words + triangulated ground truth
    lexname-to-domain.json    # WordNet lexname → WordPower domain
    mw-sl-to-domain.json      # MW sl label → WordPower domain
  scripts/
    cost_model.py             # no API needed
    heuristic_baseline.py     # Python port of DomainClassifier
    build_centroids.py        # embed centroid seed text
    embed_words.py            # embed 50 test words
    measure_accuracy.py       # cosine sim + accuracy table
    measure_latency.py        # round-trip timing
  results/
    cost.md / cost.json
    centroids.json
    embeddings.json
    accuracy.json
    latency.json
  FINDINGS.md                 # conclusion + recommendation
```

## Notes on the taxonomy gap

The original issue references "~30 candidate domains". The canonical taxonomy in `PROJECT.md` is **15 top-level domains**, with subdomains hinted but not yet enumerated. This spike uses the 15 top-level set because that is what the product currently defines. Expanding to ~30 leaves is a separate, prior decision — `FINDINGS.md` calls out whether moving to that finer granularity changes the recommendation.
