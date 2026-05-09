# Morphology Engine Spikes

Three parallel spikes that decided the per-word decomposition engine architecture for the root-families feature.

**Status:** ✅ Complete (2026-05-09).
**Architecture decision + Week 2–3 build plan:** [`docs/architecture/ROOT_FAMILIES_DECISION.md`](../../docs/architecture/ROOT_FAMILIES_DECISION.md)
**Architecture plan:** [`docs/architecture/ROOT_FAMILIES_ENGINE.md`](../../docs/architecture/ROOT_FAMILIES_ENGINE.md)
**Epic:** [#385 — Root families](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/385)

## Outcome at a glance

| Spike | Issue | Verdict | Used for |
|---|---|---|---|
| [A — MorphyNet](a-morphynet/FINDINGS.md) | [#520](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/520) | DROP (18.75% hit rate, 2 MB bundle) | (none) |
| [B — Webster's 1913 / GCIDE](b-skeat-websters/FINDINGS.md) | [#521](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/521) | SHIP (92.2% coverage, 10/10 modern clean-fail) | L2 etymology overlay |
| [C — Haiku 4.5 LLM cache](c-llm-haiku/FINDINGS.md) | [#522](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/522) | SHIP (89.6% accuracy, 9/10 traps, $122 top-30k) | L1 primary (build-time cache) |

Combined: **§9 row 3 — LLM cache primary, GCIDE etymology overlay, Wikipedia fallback. MorphyNet dropped.**

## Test set

All three spikes measure against the same 51-word test set defined in [`ROOT_FAMILIES_SPIKE.md` §6](../../docs/architecture/ROOT_FAMILIES_SPIKE.md#6-50-word-manual-sanity-check) so results are directly comparable.

## Original sequencing (for archaeology)

```
Day 1  →  A  (MorphyNet, half day)        — set bar for C
Day 2  →  B  (Skeat / Webster's, full day) — pivoted to GCIDE; OCR data quality
Day 3  →  C  (LLM Haiku, full day)         — load-bearing decision
Day 4  →  Synthesis: ROOT_FAMILIES_DECISION.md
```
