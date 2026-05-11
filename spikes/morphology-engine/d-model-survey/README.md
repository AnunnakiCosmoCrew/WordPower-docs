# Spike D — Comparative Model Survey

**Status:** ✅ Complete (2026-05-11). **Outcome: switch L1 primary to Gemini 2.5 Flash.** See [FINDINGS.md](FINDINGS.md).
**Filed:** 2026-05-09, in response to the question "are we sure Haiku 4.5 is the right choice?"
**Scope as executed:** narrowed to Gemini 2.5 Flash only (vs the planned Gemini + GPT + Llama survey) per user request to test the specific data point.

**Question:** Is Claude Haiku 4.5 the best available model for the L1 build-time decomposition cache, or could another commercial / open-weights model deliver equivalent quality at materially lower cost — or higher quality at acceptable cost?

**Architecture context:** [`ROOT_FAMILIES_DECISION.md`](../../../docs/architecture/ROOT_FAMILIES_DECISION.md) currently commits to Haiku 4.5 based on Spike C's measurement. Spike C answered "does Haiku work?" (yes) but never asked "what else works at the same or lower cost?". This spike closes that gap before we commit to a vendor for the full lifetime of the bundle.

**Estimate:** 3 points (~half day to a full day).

## Why this matters

1. **Vendor lock-in.** Every future rebuild for the app's lifetime depends on Anthropic API availability + pricing. A 5-year horizon = many rebuilds. Validating the choice once is much cheaper than discovering a better option after Phase 3 ships.
2. **The space shifted between when the architecture doc was written and now.** Gemini 2.5 Flash, Llama 3.3 via Groq, and OpenAI's small-model tier are all credibly competitive on structured-output tasks at lower price points.
3. **Open-weights posture.** Even if we don't end up using a non-commercial model, knowing the quality gap is useful for future risk planning (e.g., if Anthropic deprecates Haiku 4.5 unexpectedly, what's our fallback?).
4. **The comparison is cheap.** ~$10-15 total in API spend across all candidates. Same 81-word test set as Spike C, same scoring rubric, results directly comparable.

## Candidates

Five models. Two are already measured (Haiku 4.5, Sonnet 4.6); three are new.

| Model | Provider | Why include | Est. cost for 81 calls |
|---|---|---|---|
| Claude Haiku 4.5 | Anthropic | Current baseline (Spike C: 89.6% accuracy, 9/10 traps, ~$0.33) | — (already done) |
| Claude Sonnet 4.6 | Anthropic | Ceiling within Anthropic (Spike C: 95.8% accuracy, 10/10 traps, ~$0.50) | — (already done) |
| **Gemini 2.5 Flash** | Google | Most aggressive on cost in the closed-model space. Function calling for structured output. | ~$0.20 |
| **GPT-5 mini** (or current cheap tier) | OpenAI | Vendor diversification check. Strong structured output via JSON schema. | ~$0.50-1.00 |
| **Llama 3.3 70B via Groq** | Meta / Groq | Best open-weights option. Groq's inference is extremely fast and cheap. License is open. | ~$0.30 |

**Total spike cost: ~$1-2 in API spend across the three new models.** Cost cap: $20 across all iterations.

### Why not these

- **GPT-5 flagship / Gemini 2.5 Pro:** the apples-to-apples comparison for Haiku 4.5 is the *cheap* tier, not flagship. We already know flagship works (Sonnet 4.6 confirms it).
- **Llama 3.3 8B or smaller:** too small for reliable structured morphology output. Below our quality bar.
- **DeepSeek / Qwen:** strong models but data-residency concerns (China-hosted by default) and our structured-output integration would need more work. If the top-3 above all fail, consider as a follow-on.
- **Self-hosted inference:** out of scope. We use managed providers for fair comparison. If we ever want self-hosted, that's a separate evaluation.
- **Tiny on-device models:** out of scope. This spike is about build-time inference, not runtime. The bundle is the runtime output regardless of which model produced it.

## Methodology

Mirror Spike C exactly so results are directly comparable.

1. **Reuse the prompt-v1** from Phase 1 (#525). Each provider gets the same system prompt and the same structured-output schema, translated to its API's native mechanism:
   - Anthropic: tool use with `tool_choice: {type: "tool", name: ...}` (already done)
   - OpenAI: function calling with `tool_choice: "required"` + JSON schema
   - Google Gemini: function calling with `tool_config: {function_calling_config: {mode: "ANY"}}`
   - Groq (for Llama): OpenAI-compatible function calling
2. **Reuse the 81-word test set + adversarial set** from Spike C (no new test set).
3. **Reuse the scoring rubric** from `c-llm-haiku/scripts/measure.py` (loose substring, four-level: CORRECT / PARTIAL / WRONG / NOT_FOUND, plus trap and adversarial scoring).
4. **Measure per model:**
   - Accuracy strict (CORRECT / common)
   - Accuracy weighted (CORRECT + 0.5·PARTIAL / common)
   - Trap refusal rate (≥ 8/10)
   - Multi-layer breakdown rate
   - Ambiguous handling
   - Cost per 81 calls
   - Cost per 30,000 words (projected)
   - p50 / p99 latency per call (informational; not a gate)
5. **Cross-tabulate** in a single results table.

## Acceptance criteria

This spike has one binary output: **does the architecture decision change?**

Decision logic:
- **Some non-Anthropic model matches Haiku 4.5's quality at ≥ 2× cost reduction** → switch to that model in `ROOT_FAMILIES_DECISION.md`, update Phase 3 issue (#527).
- **Some non-Anthropic model exceeds Haiku 4.5's quality at ≤ Haiku's cost** → switch to that model.
- **An open-weights model matches Haiku 4.5's quality at any cost** → flag as the vendor-independence backup option, document, keep Haiku 4.5 as primary.
- **Otherwise** → confirm Haiku 4.5 with a comparison table; document the choice with evidence.

In all four cases, the deliverable is a clear, evidenced decision. The point of the spike is to make the choice defensible, not necessarily to change it.

## Out of scope

- Self-hosted inference (Together, Replicate, on-device)
- Models below 7B params (insufficient for structured morphology)
- Closed Chinese models (data-residency concerns; defer unless top-3 above all fail)
- Re-running Anthropic models (already done in Spike C)
- Prompt tuning per provider (use the same prompt-v1 for fairness; provider-specific tuning is a follow-on if a candidate is close-but-not-quite)

## Sequencing

This spike can run:
- **In parallel with Phase 1 (#525)** — the prompt iteration work doesn't depend on which model we eventually use.
- **Before Phase 3 (#527)** — must complete before we lock the model for the production build.

Recommended slot: **after Phase 1 prompt-v1 is locked** (so we test all candidates on the same final prompt), **before Phase 3 production build kickoff**.

If Phase 1 takes 1-2 days and this spike takes 0.5-1 day, total elapsed before Phase 3 is +1 day vs the original plan.

## Risks

1. **API key plumbing per provider.** Each adds 30-60 min of setup time. Mitigation: write a thin wrapper that abstracts over `anthropic`, `openai`, `google-generativeai`, `groq` SDKs so each runner is ~30 lines of provider-specific code plus shared scoring.
2. **Structured-output mechanism differences.** Function calling in OpenAI/Gemini/Groq is similar to Anthropic tool use but not identical. Mitigation: same JSON schema across all; verify each provider returns a parsed structured output, not free-form JSON-in-text.
3. **Cost surprises.** Cap at $20 total. Each provider's cost is easy to predict from token counts.
4. **Different "refuse" behavior across vendors.** Some models may refuse for content-policy reasons rather than confidence reasons (e.g., the system prompt's refusal logic). Mitigation: log refusal reasons; manually inspect.
5. **Result tie or marginal differences.** If Gemini is 88% vs Haiku 89.6% at half the cost, is that a swap? Define the decision rule clearly *before* running so we don't post-hoc rationalize.

## Where the work lives

- Plan: this README
- Provider runners: `scripts/run_{gemini,openai,llama}.py`
- Shared wrapper: `scripts/_shared.py` (extends Spike C's wrapper with multi-provider support)
- Results: `results/{gemini,openai,llama}-{test-set,adversarial,usage}.json`
- Comparison: `results/comparison.json` + `results/comparison.md`
- Final decision: append to or update `ROOT_FAMILIES_DECISION.md` with the evidenced verdict

## Acceptance checklist

- [ ] Each candidate model called on full 81-word set (51 test + 30 adversarial)
- [ ] Same prompt-v1 used across all candidates
- [ ] Results scored against the same rubric
- [ ] Comparison table written, ranked by cost-adjusted accuracy
- [ ] Decision documented in `ROOT_FAMILIES_DECISION.md`:
  - Either confirm Haiku 4.5 with evidence
  - Or switch primary model; update Phase 3 issue (#527) accordingly
- [ ] Spike D issue closed with results comment + comparison link
- [ ] Total spend ≤ $20
