# Spike C — LLM Haiku 4.5 decomposition quality

**Question:** Can an LLM produce reliable per-word morphological decompositions to ship in a build-time cache?

**Architecture context:** [`ROOT_FAMILIES_ENGINE.md` §7 Spike C](../../../docs/architecture/ROOT_FAMILIES_ENGINE.md#spike-c--llm-haiku-45-decomposition-quality)

**Estimate:** 5 points (~1 day)

> **Sequencing note:** Run **after Spike A**. If MorphyNet covers ≥ 95% of words at high quality, this spike's scope shrinks to "validate a small gap-fill cache." If MorphyNet whiffs, this spike becomes the primary architecture and deserves more careful prompt iteration. Wait for Spike A's `FINDINGS.md` before starting.

## Method

1. Write a structured-output prompt (JSON schema matching [`ROOT_FAMILIES_ENGINE.md` §6](../../../docs/architecture/ROOT_FAMILIES_ENGINE.md#6-schema-provisional)).
2. Run Haiku 4.5 on all 51 test words from [`ROOT_FAMILIES_SPIKE.md` §6](../../../docs/architecture/ROOT_FAMILIES_SPIKE.md#6-50-word-manual-sanity-check).
3. Compare to hand-known answers.
4. Run the same 51 words a second time with Sonnet 4.6; measure cross-LLM agreement (proxy for confidence calibration).
5. Stress-test on adversarial set:
   - **False-root traps (10):** `uncle`, `island`, `butter`, `understand`, `breakfast`, `noted`, `nothing`, `forget`, `forty`, `office`
   - **Multi-layer (10):** `unimportant`, `internationalization`, `denationalization`, `counterintuitive`, `predetermination`, `antidisestablishmentarian`, `reorganization`, `misinterpretation`, `incomprehensibility`, `unpredictability`
   - **Ambiguous (10):** `unlockable`, `unmade`, `unionized`, `discover`, `recover`, `inflammable`, `cleave`, `oversight`, `sanction`, `dust`
6. Estimate cost to run on top-30k frequency list using Anthropic API pricing.

## Acceptance criteria

- [ ] ≥ 85% accuracy on the 51-word test set
- [ ] ≥ 95% agreement between Haiku 4.5 and Sonnet 4.6 on clean cases
- [ ] ≥ 8/10 false-root traps correctly refused (`confidence: "low"` or no decomposition)
- [ ] Cost projection ≤ $200 for top-30k

## Output

- `scripts/prompt.md` — the prompt text + JSON schema
- `scripts/run_haiku.py` — calls Anthropic API on test set
- `scripts/run_sonnet.py` — same with Sonnet 4.6 for cross-validation
- `scripts/measure.py` — accuracy + agreement scoring
- `results/haiku-test-set.json`
- `results/sonnet-test-set.json`
- `results/adversarial-results.json`
- `results/cost-projection.md`
- `FINDINGS.md` — written conclusion against acceptance criteria
