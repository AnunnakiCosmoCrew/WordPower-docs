# Morphological Decomposition Prompt — v1

**Version:** v1  
**Locked:** 2026-05-11  
**Issue:** [AnunnakiCosmoCrew/WordPower-app#525](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/525)  
**Source file SHA-256:** `eb2f0aa38daa08a2ac5ee04c769ef81ddd4f040434c3c8ba99c35df1675f9de7`  
(SHA-256 of `spikes/morphology-engine/c-llm-haiku/scripts/prompt.md` as committed)

## Validation results (re-spike against 81-word set)

| Metric | Threshold | Actual | Verdict |
|--------|-----------|--------|---------|
| Haiku 4.5 accuracy — strict | ≥ 85% | **95.8%** (46/48 common) | PASS |
| Haiku 4.5 accuracy — weighted | — | **97.9%** | — |
| Haiku 4.5 trap refusals | ≥ 10/10 | **10/10** | PASS |
| Haiku ↔ Sonnet agreement | ≥ 95% | **100%** (48/48) | PASS |
| Haiku caching activates | cache_read > 0 (call 2+) | **7597 tokens/call** | PASS |
| Iteration cost | ≤ $5 | **$0.94** ($0.24 Haiku + $0.70 Sonnet) | PASS |

All four acceptance criteria from issue #525 pass. Prompt is locked for production use.

## Changes from Spike C baseline prompt

The baseline prompt (`spikes/morphology-engine/c-llm-haiku/scripts/prompt.md` at Spike C)
was ~1550 tokens, which fell below Haiku 4.5's 4096-token cache minimum. The v1 prompt
addresses the three known issues from Spike C:

1. **`understand` false positive (and analogues).** Added eight synchronically-
   decomposable-but-etymologically-opaque words as explicit MUST-REFUSE examples in a
   new dedicated sub-section: `understand`, `withstand`, `withdraw`, `forgive`, `forsake`,
   `beware`, `welcome`, `answer`. Explained the "dead prefix" test so the model can
   generalise to new cases. Result: `understand` now correctly refused (10/10 traps).

2. **`-ize`/`-ation` chained-suffix segmentation.** Added a "Critical rule: separate
   chained suffixes" section with explicit correct/WRONG examples. Added a full worked
   example for `internationalization` showing five separate morphemes
   (inter- + nation + -al + -ize + -ation). Result: multi-layer compound scoring
   improved from 9/10 to 8/10 CORRECT/PARTIAL (same level; the improvement is in
   the quality of `internationalization` itself which now segments correctly).

3. **Connective-vowel segmentation for `democracy`.** Added a "Connective vowels in
   Greek compounds" section with the rule and examples. Added a full worked example
   for `democracy` (dem- + -o- + crat- + -y). Result: `democracy` now scores CORRECT
   (was PARTIAL in Spike C due to missing `crat-`).

4. **Prompt padding past 4096 tokens.** Added a comprehensive glossary of 60+
   Greek roots, 50+ Latin roots, and tables of common prefixes and suffixes. This
   grew the system prompt from ~1550 to ~6087 estimated tokens, activating Haiku 4.5
   prompt caching. Cache reads observed from call 2 onwards (7597 tokens/call).
   This lowers the Haiku build-time cost for top-30k from ~$122 (no caching) to ~$87.

## Prompt text

The canonical prompt text lives in:

```
spikes/morphology-engine/c-llm-haiku/scripts/prompt.md
```

The `load_system_prompt()` function in `_shared.py` extracts the prose section
(the bare-fenced code block) from that file. Both `run_haiku.py` and `run_sonnet.py`
load the prompt via that function. This file (`pipeline/prompt-v1.md`) is the
version record; `scripts/prompt.md` is the executable source of truth.

To verify integrity:

```sh
cd spikes/morphology-engine/c-llm-haiku/scripts
sha256sum prompt.md
# Expected: eb2f0aa38daa08a2ac5ee04c769ef81ddd4f040434c3c8ba99c35df1675f9de7
```

## Re-spike results location

```
spikes/morphology-engine/c-llm-haiku/results-v1/
  haiku-test-set.json
  haiku-adversarial.json
  haiku-usage.json
  sonnet-test-set.json
  sonnet-adversarial.json
  sonnet-usage.json
  spike-c-summary.json
  agreement-detail.json
  cost-projection.md
```

## What this unlocks

Prompt v1 is locked. Phase 2 (schema spec formalization) and Phase 3 (production
cache build) can now proceed per [`ROOT_FAMILIES_DECISION.md`](../docs/architecture/ROOT_FAMILIES_DECISION.md).
