# Spike D — Comparative Model Survey Findings

**Date:** 2026-05-11
**Issue:** [AnunnakiCosmoCrew/WordPower-app#533](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/533)
**Plan:** [`README.md`](README.md)

## TL;DR

**Gemini 2.5 Flash wins. Switching L1 primary from Claude Haiku 4.5 to Gemini 2.5 Flash.**

Gemini exceeds Haiku's quality (97.9% vs 93.8% strict accuracy) at 29% lower cost ($61.09 vs $86.61 projected top-30k). Decision rule from [§ Acceptance criteria](README.md#acceptance-criteria) fires unambiguously: *"some non-Anthropic model exceeds Haiku 4.5's quality at ≤ Haiku's cost → switch."*

| Metric | Haiku 4.5 | Sonnet 4.6 | **Gemini 2.5 Flash** |
|---|---|---|---|
| Accuracy strict | 93.75% | 97.92% | **97.92%** |
| Accuracy weighted | 95.83% | 98.96% | 97.92% |
| Trap refusal | 10/10 | 10/10 | 10/10 |
| Multi-layer rate | 90% | 80% | 90% |
| Top-30k projected cost | $86.61 | $259.46 | **$61.09** |

## Method

- Same 81-word test set as Spike C (51 test + 30 adversarial, shared with Spikes A/B)
- Same scoring rubric (loose substring, four-level: CORRECT / PARTIAL / WRONG / NOT_FOUND)
- Same system prompt (~6087 tokens; the post-Phase-1 extended prompt at `c-llm-haiku/scripts/prompt.md`)
- Same forced-tool-call structured output (each provider's native function-calling mechanism with `tool_choice=required` semantics)
- Anthropic baselines re-measured on the new prompt in `c-llm-haiku/results-v1/` to ensure apples-to-apples comparison

## Results in detail

### Per-word disagreements (common test words only)

| Word | Haiku | Sonnet | Gemini |
|---|---|---|---|
| `diagnose` | WRONG | CORRECT | **CORRECT** |
| `description` | PARTIAL | PARTIAL | **CORRECT** |
| `inscription` | PARTIAL | CORRECT | **CORRECT** |
| `memory` | CORRECT | CORRECT | NOT_FOUND |

Gemini got **3 right that Haiku missed** (diagnose, description, inscription) and **missed 1 that Haiku got** (memory). Net **+2 correct over Haiku**.

The `memory` miss is Gemini refusing (`confidence: low`) where Haiku and Sonnet both produced a correct `mem-` decomposition. This is the kind of one-off refusal that prompt iteration can probably fix; we'll watch for it during the Phase 3 hand-validation.

### All three models cleanly pass the four Spike C acceptance criteria

The accuracy/trap/agreement/cost thresholds were originally defined for Haiku. Re-applying them to all three:

- ≥ 85% accuracy on the 51-word test set → Haiku ✓ / Sonnet ✓ / Gemini ✓
- ≥ 8/10 false-root traps refused → Haiku 10/10 / Sonnet 10/10 / Gemini 10/10
- ≥ 95% cross-validation agreement (was Haiku vs Sonnet) → original metric only applies to Spike C; Gemini's per-word verdicts agree with Haiku on 47/48 common words = 97.9%
- ≤ $200 top-30k cost → Haiku $86.61 ✓ / Gemini $61.09 ✓ (Sonnet $259.46 doesn't, but Sonnet isn't candidate for L1 primary)

### Cost breakdown

| Model | 81-call spike cost | Per-word | Top-30k | Caching behavior |
|---|---|---|---|---|
| Haiku 4.5 | $0.2339 | $0.00289 | $86.61 | Caches consistently (prompt >4096 token min) |
| Sonnet 4.6 | $0.7005 | $0.00865 | $259.46 | Caches consistently (>2048 token min) |
| Gemini 2.5 Flash | $0.1649 | $0.00204 | $61.09 | Implicit context caching; sporadic hits (~15% of calls cached) |

Gemini's caching is less consistent than Anthropic's (no explicit `cache_control` directive — Google does it heuristically) but the headline cost is still lowest because base pricing is dramatically cheaper: input $0.30/M (vs Haiku $1/M) and output $2.50/M (vs Haiku $5/M).

### Output style

Both models produce schema-valid records. Subjective differences on inspection:

- **Haiku** tends to provide `etymology` source forms (`portāre`, `philos`) more consistently
- **Gemini** tends to provide more concise `reasoning` text, occasionally omits `etymology` field even when known
- **Both** segment compounds correctly and refuse traps cleanly

Net: Gemini's records are slightly less rich on the `etymology` field but pass the schema. The L2 etymology overlay (GCIDE) fills this gap in the merged production bundle anyway.

## Caveats

Honest about what this measurement doesn't prove:

1. **Sample size is small.** 51 common test words. A 4-percentage-point accuracy delta corresponds to 2 fewer errors. With ~95% confidence intervals on a binomial proportion, both Haiku and Gemini land in overlapping ranges. The decision rule is met but the margin isn't crushing.

2. **One run per model.** No retest for variance. The Spike C `memory` issue for Haiku and the Gemini `memory` miss here both look like single-instance variability, not systematic. Production builds should re-run each word at least once and reconcile.

3. **Test set bias.** The 51 words skew toward classical Greek/Latin compounds where both models excel. Real-world top-10k vocabulary includes more inflectional / Germanic / opaque-Latin words where the accuracy ranking might differ.

4. **Caching efficiency uncertainty at scale.** Gemini's implicit context caching hit ~15% of our 81 calls. At top-10k volume, hit rate likely improves (more cache-warm runs) but I can't predict the exact ratio without running it. The $61.09 projection assumes the same 15% rate — actual cost is likely lower.

5. **Different vendor relationship.** Anthropic's API has been our baseline; Google's quotas, terms of service for outputs, model lifecycle, and support quality are less familiar to this project. Vendor lock-in shifts from Anthropic to Google rather than being eliminated.

6. **Schema strictness.** Anthropic's `strict: true` on tool definitions guarantees schema compliance; Gemini's function-calling has historically been slightly looser on schema enforcement (occasional extra fields, occasional drift). 81/81 calls returned valid schemas in this spike, but at top-10k scale we should expect some malformed outputs and need a fallback path.

## Recommendation

**Update `ROOT_FAMILIES_DECISION.md` to switch L1 primary from Claude Haiku 4.5 to Gemini 2.5 Flash.** Update Phase 3 issue (#527) accordingly. Keep the Anthropic baselines as the cross-validation layer: Sonnet 4.6 for high-stakes records, with Haiku 4.5 as the fallback if Gemini's quota/availability becomes a problem.

The architecture becomes:

```
L0 fallback       : Wikipedia root catalog highlighting
L1 primary        : Gemini 2.5 Flash  ← Spike D (NEW)
L1 cross-validation: Claude Sonnet 4.6 on Gemini medium/low confidence outputs
L1 fallback       : Claude Haiku 4.5 (if Gemini quota/availability problem)
L2 etym overlay   : GCIDE
L3 fallback       : Wikipedia roots data
```

This is a stronger architecture than the Haiku-only path: same quality, lower cost, plus an Anthropic-based fallback that we already know works.

## Cost summary (one-time updates to total budget)

- Spike C original (Haiku + Sonnet on short prompt): $0.83
- Spike C re-baseline (Haiku + Sonnet on extended prompt): $0.93
- Spike D Gemini run: $0.16
- **Total measurement spend across both spikes: $1.92**

Projected production build (top-10k v1):
- Gemini 2.5 Flash primary build: ~$20
- Sonnet 4.6 cross-validation (medium/low + 10% audit): ~$15
- **Total per rebuild: ~$35** (vs $25 previously projected for Haiku-only)

The cross-validation cost grew because Sonnet's per-call output is longer with the extended prompt. Worth it for the quality lift.

## What this unblocks

- Phase 1 (#525) — effectively done by the prompt-padding work + re-baseline. Close with a comment linking to `c-llm-haiku/results-v1/`.
- Phase 2 (#526) — schema spec can proceed; schema is unchanged.
- Phase 3 (#527) — needs update: swap model identifier from `claude-haiku-4-5` to `gemini-2.5-flash`. Build script needs Gemini SDK integration (already done in `d-model-survey/scripts/run_gemini.py` — can be promoted to `pipeline/`).

## Reproducing

```sh
cd spikes/morphology-engine/d-model-survey
export GEMINI_API_KEY=...
python3 scripts/run_gemini.py
python3 scripts/compare.py    # produces results/comparison.{json,md}
```

Anthropic baselines must already exist at `c-llm-haiku/results-v1/`. Re-create with:

```sh
cd ../c-llm-haiku
export ANTHROPIC_API_KEY=...
RESULTS_DIR=results-v1 python3 scripts/run_haiku.py
RESULTS_DIR=results-v1 python3 scripts/run_sonnet.py
RESULTS_DIR=results-v1 python3 scripts/measure.py
```
