# Root-Families Engine — Decision & Build Plan

**Date:** 2026-05-09 (revised 2026-05-11 after Spike D; revised again 2026-05-11 after top-1k production validation)
**Status:** Architecture locked, build pipeline in progress (#527 / PR #539), ready to execute remaining phases.
**Supersedes:** `ROOT_FAMILIES_ENGINE.md` §8 schedule (which was the *plan to discover*); this is the *plan to build*.

## TL;DR

The Week 1 spike programme + a follow-on top-1k production validation are complete.

| Spike | Verdict | Used for |
|---|---|---|
| **A — MorphyNet** | DROP entirely | (none) |
| **B — Webster's 1913 / GCIDE** | SHIP | L2 etymology overlay |
| **C — Haiku 4.5 LLM cache** | **SHIP** as L1 primary | L1 primary (build-time cache) |
| **D — Gemini 2.5 Flash comparison** | Validated as candidate; cost advantage didn't hold at production scale | (cross-validation only) |

Combined with previously validated Wikipedia roots data (L3) and root-catalog highlighting (L0):

```
L0 fallback         : Wikipedia root catalog highlighting (always available, no bundle dependency)
L1 primary          : LLM cache — Claude Haiku 4.5, build-time, top-10k words  ← per top-1k production validation
L1 cross-validation : Claude Sonnet 4.6 on Haiku medium/low confidence outputs
L1 secondary        : Gemini 2.5 Flash — equivalent quality, available as alternate provider if Anthropic quota/availability problem
L2 etym overlay     : GCIDE — slim per-word etymology slice, top-10k words
L3 fallback         : Wikipedia roots data — already shipped
```

**Estimated build cost:** ~$30 per rebuild (Haiku top-10k ~$17 + Sonnet validation ~$13). **Estimated effort:** 8-12 days part-time, including mobile-bundle validation.

The action plan in [§ Next-step actions](#next-step-actions) is sequenced and ready to execute.

## Why Haiku 4.5 (the journey to here)

This decision changed twice. Honest history:

**1. Initial choice (2026-05-09, Spike C):** Claude Haiku 4.5 as L1 primary. Spike C measured Haiku at 89.6% strict accuracy on a 51-word test set; all four acceptance criteria passed.

**2. Pivot to Gemini (2026-05-11 morning, Spike D):** Comparative survey on the same 51-word test set with the locked prompt-v1 measured Gemini 2.5 Flash at +2.1pp accuracy and -30% projected top-30k cost. The locked decision rule fired ("exceeds quality at ≤ same cost → switch"). Architecture was updated to Gemini as L1 primary.

**3. Revert to Haiku (2026-05-11 evening, top-1k production validation):** A Gemini run on the same 1000 SUBTLEX-US production words used by PR #539's Haiku pilot showed the Spike D cost projection didn't hold at production scale. Headline:

| Metric | Spike D (51 words) projection | Top-1k actual measurement |
|---|---|---|
| Gemini accuracy vs Haiku | +2.1pp better | equivalent (90.1% agreement) |
| Gemini cost vs Haiku | -30% cheaper | **+11% MORE expensive** ($1.90 vs $1.71) |
| Gemini wall-clock vs Haiku | not measured | **6× slower** (42 min vs 7.5 min) |

The most plausible cause: Haiku's explicit `cache_control` (Anthropic) hits cache on ~100% of calls after the first; Gemini's implicit caching is sporadic. At 51 words the dynamics are dominated by per-call output costs (where Gemini is cheaper). At 1000 words and beyond, prompt caching dominates total cost, and Anthropic's explicit caching wins decisively.

At top-1k production scale: neither switch condition fires (Gemini doesn't exceed Haiku quality, and Gemini is more expensive, not cheaper). Per the same locked decision rule that originally triggered the switch: **confirm Haiku**.

This is the right behavior of a decision rule. Locking it in advance prevents post-hoc rationalization. The Spike D evidence said switch; new top-1k evidence says don't. We follow the data.

**The load-bearing claim now:** Haiku 4.5 validates at production scale (100/100 hand-validation on top-1k, $1.71 cost, fast wall-clock with caching). Gemini 2.5 Flash is equivalent quality at slightly higher cost and slower wall-clock at production scale; it earns a place in the architecture as a secondary provider (drop-in replacement if Anthropic has a quota/availability problem) but not as primary.

See [Spike D FINDINGS](../../spikes/morphology-engine/d-model-survey/FINDINGS.md) and [`pipeline/validation/top1k-comparison.md`](../../pipeline/validation/top1k-comparison.md) for full evidence.

Haiku 4.5 remains in the architecture as the fallback when Gemini has quota/availability issues — we already know it works, the integration is already built (`c-llm-haiku/scripts/run_haiku.py`), and the cost difference at fallback frequency is negligible.

---

## What the spikes told us (combined view)

Three measurements, one architectural decision, several cross-cutting observations.

### 1. The architecture decision is unambiguous

[`ROOT_FAMILIES_ENGINE.md` §9](ROOT_FAMILIES_ENGINE.md#9-decision-criteria--how-to-pick-after-spikes) row 3 (`MorphyNet < 70% + LLM ≥ 85%`) is the row we land in:

- Spike A: MorphyNet hit rate 18.75% — far below the 70% boundary
- Spike C: Haiku accuracy 89.6% strict / 93.8% weighted — above the 85% boundary
- Spike B: GCIDE coverage 92.2% — far above the 60% drop-the-overlay threshold

There is no ambiguity to resolve. The chosen architecture is row 3's: *"LLM cache primary, GCIDE etymology overlay, Wikipedia fallback. Skip MorphyNet entirely."*

### 2. Domain mismatch was the largest single risk — and we caught it cheaply

MorphyNet looked like a free, well-known win going in. It is a real and well-built dataset — it just models the wrong thing for our use case. It captures English-internal derivational chains (`nation → national → nationalize → nationalization`) but doesn't decompose classical compounds (`philosophy ← φιλοσοφία`, `geography ← γεωγραφία`). For a product whose value proposition is "did you know `cardiology` and `cardiovascular` share the Greek root `cardi-`," this is a fatal mismatch.

We discovered this in **half a day, for $0 in API cost**. The cost of not running Spike A would have been weeks of building on a foundation that fails at exactly the words our learners care about most. Cheap-spike-first is the load-bearing principle that made the rest of the programme work.

### 3. Public-domain etymology data is scarcer than expected

Spike B's original plan called for both Skeat 1882 and Webster's 1913. **Skeat doesn't exist in clean digital form** — only archive.org OCR scans with systematic letter confusions (`BIOGRAPHY` rendered as `BIOGBAPHY`, multi-column page merge artifacts). The pivot to GCIDE (the GNU-maintained Webster's 1913 corpus) was forced by data quality, not preference.

This narrows our future options: if GCIDE is ever insufficient (license issue, coverage gap, etc.), the next-best alternative isn't Skeat — it's OED (commercial license) or building our own from Wikipedia/Wiktionary. Worth knowing now.

### 4. LLM forced-tool-use is the right primitive for this task

Spike C used `tool_choice: {type: "tool", name: "record_decomposition"}` to force the model into a strict JSON schema. **Zero parse failures across 162 calls.** No regex, no validation logic, no JSON repair. The schema lives in the tool definition; the API enforces it.

This is the right pattern for any structured-output build pipeline going forward: define the schema as a tool, force the call, parse `block.input` directly. It also gives us a `reasoning` field "for free" — an audit trail of why the model produced what it did, useful for debugging and for the eventual hand-validation passes.

### 5. Caching minimums are model-specific and silent

The system prompt was ~1500 tokens. Sonnet 4.6 (cache minimum 2048) cached after the first call (~92% read rate); Haiku 4.5 (cache minimum 4096) silently did *not* cache — no error, no warning, just `cache_creation_input_tokens: 0`. The fix is to grow the production system prompt past 4096 tokens (more few-shot examples, a glossary of common Greek/Latin roots, more refusal cases). This roughly halves the per-word cost on Haiku — material at scale.

### 6. Synchronic ≠ etymological — and LLMs default to synchronic

Multiple words across the three spikes showed the same pattern: a synchronic decomposition exists, but it's not the etymological story we want to teach. Examples:

| Word | What MorphyNet/Haiku gave us | What we wanted |
|---|---|---|
| `butter` | `butt + -er` (agent suffix; one who butts) | refusal — Greek/Latin compound, not English-derived |
| `understand` | `under- + stand` (Haiku, high confidence) | refusal — Old English `understandan`, opaque |
| `forget` | refusal (Haiku, correct) | refusal ✓ |
| `breakfast` | `break + fast` (Haiku, compound) | acceptable shallow decomposition ✓ |

The system prompt's "wrong is much worse than refused" instruction kept this contained — Haiku refused 9 of 10 trap words. But `understand` slipped through. **Production prompt iteration must explicitly enumerate more synchronically-decomposable-but-etymologically-opaque words** as refusal examples.

### 7. The test-set rubric is generous and that's OK — but it's not the production scorer

The "loose substring" rubric used for both Spike A and Spike C scoring counts an expected root as found if its bare form appears as substring in any morpheme field. This was deliberately generous — MorphyNet's chains terminate at English free stems (`transport` not `port-`), and the rubric accommodates that.

Production scoring is different: the engine surfaces the model's morphemes directly to the user, not against a canonical-root oracle. The user-facing accuracy is closer to the weighted score (93.8% on Haiku) than the strict score (89.6%). The hand-validation passes in Phase 4 below should use eyeball-and-judge scoring, not substring matching, against a 100-word sample.

### 8. Cost is not the binding constraint

We worried about budget going in. We're nowhere near it.

| Layer | One-time build cost | Notes |
|---|---|---|
| L1 LLM cache (Haiku, top-10k) | ~$15-25 | Including Sonnet validation pass on medium/low confidence |
| L2 GCIDE etymology overlay | $0 | Local extraction from already-downloaded GCIDE corpus |
| L3 Wikipedia roots | $0 | Already in production |
| **Total build** | **~$25** | One-time, per-version |

The $200 ceiling in the spike acceptance criteria was based on top-30k. The actual build is top-10k initially (~one-third the cost). Re-spending to rebuild on a new prompt is cheap enough that we can iterate freely.

---

## The architecture, concretely

```
                      ┌─────────────────────────────────────────┐
                      │  user looks up "transportation"         │
                      └──────────────────┬──────────────────────┘
                                         │
                              ┌──────────▼──────────┐
                              │  bundle lookup       │
                              │  by lowercase word   │
                              └──┬────────────┬──────┘
                                 │ hit        │ miss
                                 │            │
              ┌──────────────────▼─┐        ┌─▼────────────────────────┐
              │  L1 LLM cache       │        │  L0 root-catalog scan     │
              │  (Haiku-decomposed) │        │  (Wikipedia roots data)   │
              │                     │        │  (substring match against │
              │  morphemes:         │        │   known roots; show       │
              │  trans- / port /    │        │   "contains root port-")  │
              │  -ation             │        │                           │
              └──────────┬──────────┘        └───────────────────────────┘
                         │
              ┌──────────▼──────────┐
              │  L2 etymology       │
              │  overlay (GCIDE)    │
              │                     │
              │  per-morpheme:      │
              │  meaning, language, │
              │  etymological form  │
              │  (portāre, etc.)    │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  L3 Wikipedia       │
              │  roots data         │
              │  (root → "carry"    │
              │   mappings; used    │
              │   to verify L2,     │
              │   gap-fill missing  │
              │   meaning fields)   │
              └─────────────────────┘
```

**Bundle structure (target):**
- One JSON file per layer, keyed by lowercase headword
- Top-level metadata: schema version, source, build date, model+prompt hash
- Per-record schema = `ROOT_FAMILIES_ENGINE.md` §6 + a `confidence` field
- Engine merges layers at runtime; each record's `source` field tracks provenance

**Bundle size budget (target, gzipped):**

| Layer | Target | Stretch |
|---|---|---|
| L1 LLM cache (top-10k) | ~1 MB | ≤ 1.5 MB |
| L2 etymology overlay (top-10k) | ~500 KB | ≤ 800 KB |
| L3 Wikipedia roots | already shipped | — |
| **Total morphology bundle** | **~1.5 MB** | **≤ 2.5 MB** |

To be measured during Phase 4 below. The 200 KB threshold from the original spike was for the *MorphyNet lookup layer alone* and was too tight for a production multi-layer bundle. A revised budget is part of Phase 4's deliverable.

---

## Next-step actions

Twelve days of work, organized as 7 phases. Each phase has explicit deliverables and a gate.

### Phase 1 — Prompt iteration (Days 1-2, ~$1)

**Goal:** address the three known issues from Spike C, re-validate, lock the production prompt.

Tasks:
1. Tighten the system prompt to:
   - Add `understand` and 5-10 similar synchronically-decomposable-but-etymologically-opaque words to the explicit refusal examples (e.g. `withstand`, `forgive`, `withdraw`)
   - Add a worked example showing `-ize` / `-ation` segmentation in chained suffixes (`internationalization`)
   - Add a worked example showing connective-vowel segmentation (`democracy = dem- + -o- + -crat- + -y`)
   - Pad past 4096 tokens (more refusal examples, a glossary of common Greek/Latin roots) to activate Haiku caching
2. Re-run the Spike C 81-word measurement on the tightened prompt
3. Compare new accuracy/agreement/trap-refusal numbers to the previous baseline
4. Confirm caching activates on Haiku (`cache_read_input_tokens > 0` from call 2 onwards)
5. Lock the prompt: write `pipeline/prompt-v1.md` with version + SHA, commit

**Gate 1:** Tightened prompt must maintain ≥ 85% accuracy, ≥ 95% Sonnet agreement, ≥ 9/10 trap refusal (one better than baseline). If any criterion regresses, iterate. **Cost cap: $5 across all iterations.**

**Deliverable:** `pipeline/prompt-v1.md` + tightened-prompt re-spike results in `spikes/morphology-engine/c-llm-haiku/results-v1/`.

### Phase 2 — Schema freeze (Day 3, half day)

**Goal:** formalize the §6 schema as the canonical record format for the production bundle.

Tasks:
1. Promote `ROOT_FAMILIES_ENGINE.md` §6 to a standalone schema spec at `docs/architecture/MORPHOLOGY_RECORD_SCHEMA.md`
2. Define bundle-level wrapper: `{schema_version, source, build_date, model, prompt_hash, records: {...}}`
3. Write JSON Schema definition for the bundle (so the Flutter app can validate at load time)
4. Define merge semantics: how L1 (LLM) and L2 (GCIDE) and L3 (Wikipedia roots) combine into a single per-word record at runtime

**Gate 2:** Schema must represent every output we observed in the 162 Spike C calls without information loss. Round-trip a sample of 10 records through the schema → bundle → load path to verify.

**Deliverable:** `docs/architecture/MORPHOLOGY_RECORD_SCHEMA.md` with JSON Schema spec.

### Phase 3 — L1 cache build pipeline (Days 4-7, ~$20-35)

**Goal:** build the per-word LLM decomposition cache for the top-10k frequency list, using Gemini 2.5 Flash as primary with Sonnet validation and Haiku fallback.

Tasks:
1. **Pick a frequency list.** Candidates: SUBTLEX-US (subtitle frequency, learner-friendly), COCA top-N (broader corpus), Google Web Trillion Word Corpus (web-skewed). Default: SUBTLEX-US — best match for vocabulary-app domain. Source from [`crr.ugent.be/papers/SUBTLEX-US.zip`](https://www.ugent.be/pp/experimentele-psychologie/en/research/documents/subtlexus) and pin the version.
2. **Top-1k pilot run** (~$2, ~30 min). Run Gemini 2.5 Flash with prompt-v1 on words 1-1000 of the frequency list. Output: `pipeline/output/top1k-llm-cache.json`.
3. **Hand-validate the top-1k.** Sample 100 random records, eyeball score. Gate on ≥ 85% acceptable. Surface any systematic prompt-iteration issues.
4. **Top-10k production run** (~$20, ~5-10 min). If the top-1k passes the gate, run on words 1-10000. Output: `pipeline/output/top10k-llm-cache-v1.json`.
5. **Sonnet validation pass** (~$10-15). For records with `confidence ∈ {medium, low}` (~5-10% of records, est. 500-1000 words), run Sonnet 4.6 on the same words. Compare outputs. For disagreements, prefer Sonnet's verdict. Output: `pipeline/output/top10k-llm-cache-v1-validated.json`.
6. **Provider-fallback smoke test** (~$2). Run Haiku 4.5 on a 100-word sample to verify the fallback path works end-to-end. We don't ship the Haiku build, just confirm the runner exists and produces a schema-valid output if/when we ever need to swap providers.

**Gate 3:** Top-1k hand-validation ≥ 85%. If below, iterate the prompt and re-run the pilot. Don't proceed to top-10k until the pilot passes.

**Deliverable:** `pipeline/output/top10k-llm-cache-v1-validated.json` (~10,000 records).

### Phase 4 — L2 etymology overlay build (Days 8-9)

**Goal:** build the GCIDE-derived per-word etymology slice for the top-10k.

Tasks:
1. Write `pipeline/build_etymology_overlay.py`: read `gcide-index.json` (built in Spike B), filter to the top-10k frequency list, emit slim per-word records with just the `<ety>` body, source-form chain, language abbreviations, and cross-references.
2. Measure overlay bundle size at gzip -9 (target ~500 KB).
3. Verify coverage: how many of the top-10k words have a non-empty etymology entry in GCIDE? Goal ≥ 60% (anything under is a finding to surface).
4. Filter and clean: remove residual XML-ish markup tokens (`<grk>`, `<?/`), normalize whitespace, ensure UTF-8.

**Gate 4:** Overlay bundle ≤ 800 KB gzipped. If over, trim further (drop cross-references, drop obscure-language abbreviations, drop entries with low-quality etymology).

**Deliverable:** `pipeline/output/top10k-etymology-overlay-v1.json`.

### Phase 5 — Bundle merge + mobile validation (Days 10-11)

**Goal:** merge the layers into a single shippable bundle and verify it loads cleanly on device.

Tasks:
1. Write `pipeline/merge_bundle.py`: for each top-10k word, produce a single record by merging L1's morphemes with L2's etymology fields. The merge logic is per the §6 schema's `source` provenance — the engine knows which fields came from where.
2. Hand-validate 100 random end-to-end records. For each, write a one-sentence verdict.
3. Measure final bundle size at gzip -9. Target ≤ 1.5 MB; stretch ≤ 2.5 MB.
4. Mobile load test: integrate the bundle into a throwaway Flutter test app. Measure cold-load time on iOS Simulator and Web (Chrome). Target ≤ 200ms cold load, ≤ 50 MB memory footprint.
5. Stress test: query 1000 random words back-to-back; measure 99th-percentile lookup latency. Target ≤ 5ms.

**Gate 5:** Mobile load ≤ 500ms (twice the target as a buffer); 99th-percentile lookup ≤ 20ms; bundle ≤ 2.5 MB. If any fails, fall back to top-5k for v1 and ship the smaller bundle.

**Deliverable:** `pipeline/output/morphology-bundle-v1.json` + mobile load benchmark report at `docs/operations/MORPHOLOGY_BUNDLE_BENCHMARK.md`.

### Phase 6 — Documentation + handoff (Day 12)

**Goal:** write the canonical build-pipeline doc; hand off to Phase 4 UI work.

Tasks:
1. Write `docs/architecture/MORPHOLOGY_BUILD_PIPELINE.md` covering: source data inventory, prompt versioning, build script run, validation gates, cost tracking, rollback procedure.
2. Update [#406](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/406) (existing Phase 4 UI issue) with: bundle path, schema doc link, sample queries showing high/medium/low confidence rendering.
3. File a follow-on issue under #385 for Phase 5 expansion: top-30k bundle, additional languages, alternative frequency lists.
4. Update `spikes/morphology-engine/README.md` to mark all three spikes as complete and link to this decision doc.

**Deliverable:** `docs/architecture/MORPHOLOGY_BUILD_PIPELINE.md`, hand-off comment on #406.

### Phase 7 — Legal review (parallel; blocking before public release)

**Goal:** clear GCIDE GPL 3.0+ posture before any user-visible release.

Tasks:
1. Confirm the bundle distribution model with legal counsel: data file loaded at runtime, distributed separately from app binary, with attribution.
2. Decide: ship the GCIDE COPYING notice in the app's Settings → Open-Source Licenses screen, or as a license file alongside the bundle, or both.
3. Backup option if legal pushes back: extract a smaller derivative bundle with only the morpheme + meaning + language fields (the §6 schema fields), license-tagged with attribution. The full prose etymology stays out of the bundle.

**Gate 7:** Legal sign-off on at least one distribution model.

**Deliverable:** legal sign-off note (file or email) attached to issue #385.

---

## Locked decisions

The decisions surfaced during synthesis review (2026-05-09) are locked in below. The remaining items are operational and resolved at their phase boundary.

1. **Frequency list source: SUBTLEX-US.** Subtitle-derived US English frequency list — best match for the vocabulary-app domain (reflects words people actually encounter in everyday spoken/screen English). Free, ~74k words, easy to slice top-10k. Source: [`crr.ugent.be/papers/SUBTLEX-US.zip`](https://www.ugent.be/pp/experimentele-psychologie/en/research/documents/subtlexus). Pin the version in `pipeline/download_frequency_list.sh`.

2. **Sonnet validation strategy: medium/low confidence + 10% high-confidence audit.** Sonnet runs on Haiku's medium/low outputs (~5-10% of records) plus a random 10% sample of high-confidence outputs as an audit. Estimated cost: ~$10-30 on top of Haiku's ~$15. Disagreements: prefer Sonnet's verdict.

3. **Top-N target for v1: top-10k.** Covers ~95% of typical learner-vocabulary lookups by frequency. Bundle size target ~1.5 MB. Build cost ~$25. Top-30k expansion is filed as a follow-on under #385 once v1 ships and we have user-facing analytics.

4. **Confidence rendering at runtime: lock the §5 mapping.** `high` → full morpheme breakdown shown; `medium` → root-only display (L0-style fallback rendering); `low` → engine declines, app shows definition only. Surfaced in the Phase 2 schema spec and referenced from the Phase 6 UI handoff to #406.

5. **Bundle versioning: top-level only for v1.** `{schema_version, source, build_date, model, prompt_hash, records: {...}}` at the top; per-record version added in v2 only if the §6 schema evolves materially.

6. **Re-build cadence: full rebuild every time.** When prompt-v2 ships, full top-10k rebuild. It's $25 and 10 minutes; the complexity of incremental rebuild isn't worth saving.

7. **Phase 3 hand-validation fallback ladder.** If the top-1k pilot fails the ≥ 85% gate: (1) tighten prompt and re-run pilot; (2) if still failing, drop coverage to top-5k for v1; (3) if still failing, defer L2 to Phase 5 and ship L0-only (Wikipedia root-catalog highlighting). Document the rung we land on.

---

## Risks (consolidated, ranked by likelihood × impact)

1. **Prompt-iteration creep.** Tightening the prompt to fix one issue (`understand`) can introduce regressions on others. *Mitigation: Phase 1 gate is strict and re-runs the full 81-word measurement; cost cap is $5.*

2. **Bundle size at top-10k exceeds 2.5 MB.** *Mitigation: Phase 4 has explicit gates and a top-5k fallback. Worst case we ship a smaller v1 and expand in v2.*

3. **GCIDE GPL legal pushback.** *Mitigation: Phase 7 has a slim-derivative-bundle backup. Worst case we drop the etymology overlay, fall back to Wikipedia roots' etymology field per §9 row 5.*

4. **Mobile load time exceeds budget.** *Mitigation: Phase 5 measures it before ship. If slow, lazy-load by alphabet shard or first-letter; the engine doesn't need the whole bundle for a single lookup.*

5. **`understand`-class false positives in production.** Even after prompt iteration, some synchronically-defensible decompositions will slip through. *Mitigation: ship with a feedback loop — let users flag wrong decompositions; re-validate quarterly with the latest model. Production scoring is per-record `confidence`, not per-bundle accuracy.*

6. **Frequency list mismatch with actual user lookups.** Top-10k by SUBTLEX may miss the words our actual users encounter. *Mitigation: ship analytics on which words get looked up and don't have a cache hit; backfill in v2.*

7. **L1 model deprecation mid-lifecycle.** Both Gemini 2.5 Flash and Haiku 4.5 will eventually be replaced by successors. *Mitigation: pin model identifier in build script + bundle metadata. Migration when needed is a re-run, not a re-architecture. The multi-provider integration (Gemini primary + Haiku fallback + Sonnet validation) means we're not dependent on any single vendor's release schedule.*

---

## What was different from the original §8 plan

The §8 schedule (in `ROOT_FAMILIES_ENGINE.md`) was written *before* the spikes. Comparing what it expected to what we now know:

| §8 expected | Spike outcome | Plan change |
|---|---|---|
| MorphyNet maybe primary | 18.75% hit rate, dropped | Skip layered architecture entirely; LLM cache is L1 |
| Skeat 1882 as etymology source | Skeat unavailable in clean form | Pivoted to GCIDE; added GPL legal-review task |
| LLM as gap-fill (worst case primary) | LLM is now primary | Build pipeline focus shifts to LLM cache + GCIDE merge |
| Schema design Day 1 of Week 2 | Schema validated by 162 calls | Schema freeze is now half a day, not a full day |
| 100-word sample → 1000-word sample → 10k bundle | Top-1k pilot → top-10k production | Same shape, faster — Spike C already proved the path |
| Bundle size target 200 KB | Threshold was for MorphyNet alone | New target ~1.5 MB total morphology bundle |

Net effect: the build phase is **faster and cheaper than originally planned** because the spikes resolved most of the unknowns. The 12-day estimate above is conservative.

---

## How this doc relates to the others

```
ROOT_FAMILIES_SPIKE.md       — original L0 spike (Wikipedia roots data baseline)
ROOT_FAMILIES_ENGINE.md      — the architecture plan (§9 has spike outcomes annotated)
ROOT_FAMILIES_DECISION.md    — THIS DOC: decision + build plan (closes Week 1)
MORPHOLOGY_RECORD_SCHEMA.md  — Phase 2 deliverable: canonical record schema
MORPHOLOGY_BUILD_PIPELINE.md — Phase 6 deliverable: production build doc

spikes/morphology-engine/
  a-morphynet/FINDINGS.md       — Spike A measurements
  b-skeat-websters/FINDINGS.md  — Spike B measurements
  c-llm-haiku/FINDINGS.md       — Spike C measurements
```

This doc is the **decision** — the architecture is locked, the action plan is set. The spike FINDINGS docs are the **evidence** — the per-spike data backing the decision. The architecture doc is the **plan** — the design that was validated. Future readers should:

- **Want to know what we're shipping?** Read this doc.
- **Want to know why we're shipping it?** Read this doc + the spike FINDINGS for evidence.
- **Want to know how the engine works?** Read `ROOT_FAMILIES_ENGINE.md`.
- **Want to know how to build the bundle?** Read `MORPHOLOGY_BUILD_PIPELINE.md` (after Phase 6 lands).

---

## Ready to execute

Phase 1 is the immediate next action. Estimated start: as soon as this doc is reviewed and approved. Estimated completion of all 7 phases: 2-3 weeks elapsed, part-time.

The Week 1 spike programme cost ~$0.83 in API spend and produced three rigorous findings docs plus this synthesis. The Week 2-3 build programme is projected at ~$25 in API spend plus mobile-bundle validation. The whole engine ships at roughly the cost of dinner for two.

---

## Addendum: WP-551 — canonical-root post-process patch

**Date:** 2026-05-12

**Symptom:** The shipped `root-families.json.gz` rendered short Latin stems
(`stru-`, `dic-`, `spec-`, `duc-`, `tex-`, `fric-`, `rep-`, `sec-`) as the
canonical root chip. Etymology dictionaries (Wiktionary, Online Etymology
Dictionary) conventionally cite the longer form with the productive consonant
cluster preserved (`struct-`, `dict-`, `spect-`, `duct-`, `text-`, `frict-`,
`rept-`, `sect-`).

**Root cause:** Not the L1 LLM cache (Phase 3) as the issue first assumed —
the L1 cache's canonical roots are correct (`struct-`, `port-`, `phon-`).
The shipped bundle is built by `backend/scripts/root-families/build_root_families.py`
(WP-406) from Wikipedia's "List of Greek and Latin roots in English". Wikipedia
rows list short and long variants together (e.g. `stru-, struct-`); the build
script picks the first comma-separated form as canonical.

**Decision:** Post-process patch script over the existing bundle — no LLM
rebuild, no re-spike. Path (b) from the issue.

**Why not full rebuild (path a):** The L1 LLM cache is already correct, so a
prompt+rebuild fixes nothing for this issue. The shipped bundle is the
Wikipedia-derived artifact, which is deterministic and cheap to re-patch.

**Why not blanket rule:** 60 families have a short-then-long alias pattern,
but most are legitimate (`ab-/abs-`, `aut-/auto-`, `phil-/-phile`, `re-/red-`).
A blanket rule would create new bugs.

**Implementation:** `backend/scripts/root-families/patch_canonical_roots.py`
holds a curated `CANONICAL_RENAMES` map (8 entries) and rewrites root +
aliases + per-word decomp triples idempotently. Re-gzips with `mtime=0` to
keep the WP-406 reproducibility invariant.

**Operational note:** Whenever `build_root_families.py` is re-run (e.g. on a
Wikipedia revision bump), `patch_canonical_roots.py` must be re-run before
committing the regenerated bundle.
