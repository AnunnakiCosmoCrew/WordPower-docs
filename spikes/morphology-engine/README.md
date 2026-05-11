# Morphology Engine Spikes

Four spikes that decided the per-word decomposition engine architecture for the root-families feature.

**Status:** ✅ Complete (2026-05-11).
**Build phase:** ✅ Complete. Bundle at `pipeline/output/morphology-bundle-v1.json`.
**Build pipeline doc:** [`docs/architecture/MORPHOLOGY_BUILD_PIPELINE.md`](../../docs/architecture/MORPHOLOGY_BUILD_PIPELINE.md)
**Mobile benchmark:** [`docs/operations/MORPHOLOGY_BUNDLE_BENCHMARK.md`](../../docs/operations/MORPHOLOGY_BUNDLE_BENCHMARK.md)
**Architecture decision + Week 2–3 build plan:** [`docs/architecture/ROOT_FAMILIES_DECISION.md`](../../docs/architecture/ROOT_FAMILIES_DECISION.md)
**Architecture plan:** [`docs/architecture/ROOT_FAMILIES_ENGINE.md`](../../docs/architecture/ROOT_FAMILIES_ENGINE.md)
**Epic:** [#385 — Root families](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/385)

## Outcome at a glance

| Spike | Issue | Verdict | Used for |
|---|---|---|---|
| [A — MorphyNet](a-morphynet/FINDINGS.md) | [#520](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/520) | DROP (18.75% hit rate, 2 MB bundle) | (none) |
| [B — Webster's 1913 / GCIDE](b-skeat-websters/FINDINGS.md) | [#521](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/521) | SHIP (92.2% coverage, 10/10 modern clean-fail) | L2 etymology overlay |
| [C — Haiku 4.5 LLM cache](c-llm-haiku/FINDINGS.md) | [#522](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/522) | **SHIP** as L1 primary (top-1k production validation reverted from Spike D) | **L1 primary (build-time cache)** |
| [D — Gemini 2.5 Flash comparison](d-model-survey/FINDINGS.md) | [#533](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/533) | Equivalent quality; +11% cost at production scale vs Haiku | L1 secondary (provider-swap fallback) |

Note: Spike C's headline numbers were re-baselined under [#525](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/525) on the locked prompt-v1 (Haiku 95.8% / 10/10 / $87 top-30k). Spike D initially showed Gemini −30% cheaper — the architecture briefly switched to Gemini as primary — but top-1k production validation reversed this: Gemini was +11% more expensive and 6× slower than Haiku with caching at production scale. Haiku was re-confirmed as L1 primary. See [`ROOT_FAMILIES_DECISION.md` §Why Haiku 4.5](../../docs/architecture/ROOT_FAMILIES_DECISION.md#why-haiku-45-the-journey-to-here) for the full evidence.

Combined: **§9 row 3 — LLM cache primary (Haiku 4.5), GCIDE etymology overlay, Wikipedia fallback. MorphyNet dropped. Gemini available as provider-swap secondary.**

## Test set

All three spikes measure against the same 51-word test set defined in [`ROOT_FAMILIES_SPIKE.md` §6](../../docs/architecture/ROOT_FAMILIES_SPIKE.md#6-50-word-manual-sanity-check) so results are directly comparable.

## Original sequencing (for archaeology)

```
Day 1  →  A  (MorphyNet, half day)        — set bar for C
Day 2  →  B  (Skeat / Webster's, full day) — pivoted to GCIDE; OCR data quality
Day 3  →  C  (LLM Haiku, full day)         — load-bearing decision
Day 4  →  Synthesis: ROOT_FAMILIES_DECISION.md
```
