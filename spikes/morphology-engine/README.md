# Morphology Engine Spikes

Three parallel spikes that decide the per-word decomposition engine architecture for the root-families feature.

**Plan:** [`docs/architecture/ROOT_FAMILIES_ENGINE.md`](../../docs/architecture/ROOT_FAMILIES_ENGINE.md)
**Epic:** [#385 — Root families](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/385)

## Test set

All three spikes measure against the same 51-word test set defined in [`ROOT_FAMILIES_SPIKE.md` §6](../../docs/architecture/ROOT_FAMILIES_SPIKE.md#6-50-word-manual-sanity-check) so results are directly comparable.

## Sequencing

Although technically independent, run **A first** (cheapest, scopes C):

```
Day 1  →  A  (MorphyNet, half day)        — sets bar for C
Day 2  →  B  (Skeat / Webster's, full day) — independent of A's outcome
Day 3  →  C  (LLM Haiku, full day)         — scope determined by A's hit rate
Day 4  →  Synthesis: pick architecture per ROOT_FAMILIES_ENGINE.md §9 decision matrix
```

## Spikes

- [`a-morphynet/`](a-morphynet/) — Can MorphyNet serve as the primary decomposition source?
- [`b-skeat-websters/`](b-skeat-websters/) — Can a public-domain dictionary serve as the etymology / classical-coverage layer?
- [`c-llm-haiku/`](c-llm-haiku/) — Can an LLM produce reliable per-word decompositions to ship in a build-time cache?
