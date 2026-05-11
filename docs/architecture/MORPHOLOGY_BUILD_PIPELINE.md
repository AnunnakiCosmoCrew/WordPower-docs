# Morphology Build Pipeline

**Status:** ✅ v1 shipped (2026-05-11)
**Issue:** [#530](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/530) — Phase 6 of the root-families build plan
**Schema doc:** [`MORPHOLOGY_RECORD_SCHEMA.md`](MORPHOLOGY_RECORD_SCHEMA.md)
**Architecture decision:** [`ROOT_FAMILIES_DECISION.md`](ROOT_FAMILIES_DECISION.md)

This is the canonical operational runbook for rebuilding the morphology bundle (`morphology-bundle-v1.json`). Read it when you need to run a rebuild, diagnose a cost spike, swap providers, or roll back a bad bundle.

---

## 1. Source data inventory

| Source | Repo path | Version / pin | Role |
|---|---|---|---|
| **SUBTLEX-US frequency list** | Not committed in this repository; provide as a local build input in your working directory | Use the exact SUBTLEX-US release used for the target rebuild and record/pin its SHA-256 alongside the build notes | Top-10k word list; determines which words get an L1 LLM call |
| **GCIDE corpus** | Not committed in this repository; restore from the Spike B artifact/history referenced in [#521](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/521) or from the upstream GCIDE 0.54 distribution | GCIDE 0.54; record the source archive/checksum used for the rebuild | L2 etymology overlay source; GPL 3.0+ |
| **Prompt-v1** | Not present in this repository snapshot; use the exact prompt file from the build environment that produced the bundle | SHA-256 hash locked in bundle metadata (`prompt_hash` field); if the prompt changes, the hash changes and a full rebuild is required | L1 LLM instruction set; changing this file triggers a full rebuild |

### 1.1 Re-downloading source data

```bash
# This repository snapshot does not include the raw SUBTLEX-US CSV, a download helper,
# or the GCIDE extraction directory. Obtain them before running a rebuild:
#
# 1) SUBTLEX-US:
#    - Download the approved source file from the upstream distribution used by the team.
#    - Save it into your local build workspace.
#    - Record the file SHA-256 in the rebuild notes so the run is reproducible.
#
# 2) GCIDE:
#    - Restore the GCIDE 0.54 corpus from the Spike B artifact/history in issue #521,
#      or download the matching upstream GCIDE 0.54 release.
#    - Extract it into your local build workspace.
#    - Record the archive source and checksum used for the rebuild.
#
# 3) Prompt-v1:
#    - Use the exact prompt file from the build environment used for the previous bundle,
#      or create the new prompt intentionally and capture its SHA-256 as `prompt_hash`.
#
# Before starting the pipeline, verify that all three inputs exist in your local workspace.
```

---

## 2. Multi-provider model setup

The build pipeline uses three model roles. All API keys should be set as environment variables — never committed.

### 2.1 L1 Primary — Claude Haiku 4.5 (Anthropic)

**Why primary:** At top-1k production scale, Haiku's explicit `cache_control` prompt caching yields ~100% cache-hit rate from call 2 onwards. This makes Haiku 11% cheaper than Gemini 2.5 Flash and 6× faster at production scale (7.5 min vs 42 min for top-10k). See [`ROOT_FAMILIES_DECISION.md` §Why Haiku 4.5](ROOT_FAMILIES_DECISION.md#why-haiku-45-the-journey-to-here) for the full evidence.

**Setup:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Billing / spend cap:** Set a monthly spend limit in the [Anthropic console](https://console.anthropic.com) under Billing → Spending limits. A full top-10k rebuild costs ~$17 on Haiku; budget ≥$50 per rebuild run.

**Caching requirement:** `pipeline/prompt-v1.md` must be ≥ 4096 tokens when encoded as the system prompt. Haiku 4.5's minimum cacheable block is 4096 tokens; anything shorter silently skips caching (no error, just no `cache_read_input_tokens`). Verify caching is active by checking that `usage.cache_read_input_tokens > 0` from the second API call onward.

### 2.2 Cross-validation — Claude Sonnet 4.6 (Anthropic)

**When it runs:** On all `medium`/`low` confidence Haiku outputs (~5–10% of records, est. 500–1000 words) plus a random 10% sample of `high` confidence outputs as an audit. Sonnet's verdict overrides Haiku on disagreements.

**Same `ANTHROPIC_API_KEY`** as Haiku.

**Estimated cost:** ~$13 per full top-10k validation pass, on top of Haiku's $17.

### 2.3 Secondary — Gemini 2.5 Flash (Google)

**When it activates:** Only when Anthropic has a quota event or sustained availability issue (see §7 provider-swap runbook). Gemini is equivalent quality to Haiku at production scale (90.1% agreement) but 11% more expensive and 6× slower due to less-effective implicit caching.

**Setup:**
```bash
export GEMINI_API_KEY="AIza..."
```

**Billing / spend cap:** Set a budget alert in [Google AI Studio](https://aistudio.google.com) → Billing. A Gemini top-10k run costs ~$19.

---

## 3. Prompt versioning policy

- The production prompt is locked in `pipeline/prompt-v1.md`.
- Its SHA-256 hash is embedded in the bundle's `prompt_hash` metadata field (format: `sha256:<hex>`).
- **Any change to `pipeline/prompt-v1.md` requires a full rebuild.** There is no incremental update path — the cache is keyed per prompt version, and partial caches are not safe to use.
- To compute and verify the hash:
  ```bash
  sha256sum pipeline/prompt-v1.md
  # Output format: <hash>  pipeline/prompt-v1.md
  ```
- To lock a new prompt version:
  1. Write the new prompt to `pipeline/prompt-v2.md` (new file, not overwrite).
  2. Compute its hash.
  3. Update `PRIMARY_PROMPT_FILE` and `PROMPT_HASH` in `pipeline/build_llm_cache.py`.
  4. Run Phase 1 gate validation on the new prompt before a full rebuild.
  5. Commit both the new prompt file and the build script update in a single commit.
- **Do not edit `pipeline/prompt-v1.md` in place.** Editing it breaks the hash check for any bundle already in production.

---

## 4. Build script run order

Run all commands from the repo root. Log output is written to `pipeline/logs/build-YYYY-MM-DD.log`.

```
Step 1 — Frequency list
  pipeline/download_frequency_list.sh
  → pipeline/data/subtlex-us.csv    (top-10k slice, pinned version)

Step 2 — L1 LLM cache (Haiku primary)
  python3 pipeline/build_llm_cache.py
  → pipeline/output/top10k-llm-cache-v1.json

Step 3 — Sonnet cross-validation
  python3 pipeline/validate_llm_cache.py
  → pipeline/output/top10k-llm-cache-v1-validated.json

Step 4 — L2 GCIDE etymology overlay
  python3 pipeline/build_etymology_overlay.py
  → pipeline/output/top10k-etymology-overlay-v1.json

Step 5 — Bundle merge (L1 + L2)
  python3 pipeline/merge_bundle.py
  → pipeline/output/morphology-bundle-v1.json

Step 6 — Mobile validation (manual)
  See docs/operations/OPS.md for the Flutter test app and
  benchmark procedure.
```

### 4.1 Quick rebuild checklist

```
[ ] ANTHROPIC_API_KEY is set and has quota
[ ] pipeline/data/subtlex-us.csv exists (run step 1 if not)
[ ] pipeline/prompt-v1.md hash matches bundle's prompt_hash
[ ] pipeline/logs/ directory exists (mkdir -p pipeline/logs)
[ ] Steps 1 → 5 complete in order
[ ] Step 6 passes mobile validation gate
```

---

## 5. Validation gates per phase

Each phase of the build has a hard gate. Do not proceed to the next step if the gate fails.

| Phase | Issue | Gate condition | Threshold | Action on failure |
|---|---|---|---|---|
| Phase 1 — Prompt lock | [#525](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/525) | 81-word re-spike: accuracy / Sonnet agreement / trap refusal | ≥85% / ≥95% / ≥9/10 | Iterate prompt; cost cap $5 across all iterations |
| Phase 2 — Schema freeze | [#526](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/526) | 10-record round-trip through schema, no information loss | Pass/fail | Fix schema; re-verify 10 records |
| Phase 3 — L1 top-1k pilot | [#527](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/527) | Hand-validation: 100 random records, eyeball score | ≥85% acceptable | Iterate prompt; re-run pilot before top-10k |
| Phase 4 — L2 overlay | [#528](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/528) | GCIDE overlay bundle size at gzip -9 | ≤800 KB | Trim cross-references and low-quality etymologies |
| Phase 5 — Mobile bundle | [#529](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/529) | Cold load / p99 lookup / total bundle | ≤500ms / ≤20ms / ≤2.5 MB | Fall back to top-5k; ship smaller v1, expand in v2 |

All five gates passed in the v1 build. See each phase issue for the actual measurement results.

---

## 6. Cost tracking

**Target:** ≤ $50 per full rebuild. **Actual v1:** ~$30.

| Step | Model | Estimated cost | Actual v1 |
|---|---|---|---|
| Step 2 — L1 Haiku top-10k | Claude Haiku 4.5 | ~$15–25 | ~$17 |
| Step 3 — Sonnet cross-validation | Claude Sonnet 4.6 | ~$10–15 | ~$13 |
| Step 4 — GCIDE overlay | (local extraction) | $0 | $0 |
| Step 5 — Merge | (local) | $0 | $0 |
| **Total** | | **~$25–40** | **~$30** |

**How to measure cost per run:**

Each API response includes a `usage` block. The build scripts log token counts to `pipeline/logs/build-YYYY-MM-DD.log`. To compute cost post-run:

```bash
# Haiku 4.5 pricing (as of 2026-05): $0.25/M input, $1.25/M output
# Sonnet 4.6 pricing (as of 2026-05): $3/M input, $15/M output
# Cached input tokens are billed at 10% of the base input rate
grep "usage" pipeline/logs/build-*.log | python3 -c '
import json, re, sys

totals = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0}

def add_usage(d):
    usage = d.get("usage", d) if isinstance(d, dict) else {}
    for key in totals:
        value = usage.get(key, 0)
        if isinstance(value, (int, float)):
            totals[key] += int(value)

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    parsed = False
    for match in re.finditer(r"\{.*?\}", line):
        try:
            add_usage(json.loads(match.group(0)))
            parsed = True
        except Exception:
            pass

    if parsed:
        continue

    for key in totals:
        m = re.search(rf"{key}[\"'=: ]+(\d+)", line)
        if m:
            totals[key] += int(m.group(1))

input_tokens = totals["input_tokens"]
output_tokens = totals["output_tokens"]
cached_tokens = totals["cache_read_input_tokens"]
billable_input_tokens = max(input_tokens - cached_tokens, 0)

def price(base_input_per_million, output_per_million):
    return (
        (billable_input_tokens / 1_000_000.0) * base_input_per_million +
        (cached_tokens / 1_000_000.0) * (base_input_per_million * 0.10) +
        (output_tokens / 1_000_000.0) * output_per_million
    )

print(f"input_tokens={input_tokens}")
print(f"cache_read_input_tokens={cached_tokens}")
print(f"billable_input_tokens={billable_input_tokens}")
print(f"output_tokens={output_tokens}")
print(f"estimated_haiku_cost=${price(0.25, 1.25):.2f}")
print(f"estimated_sonnet_cost=${price(3.00, 15.00):.2f}")
'
```

**Cost alert:** If a single rebuild exceeds $50, stop and investigate before continuing. Common causes: caching not activating on Haiku (verify `cache_read_input_tokens > 0`), accidental re-run of the full pipeline, or running Sonnet on all records instead of only medium/low.

---

## 7. Rollback procedure

### 7.1 Immediate rollback (revert to prior bundle)

```bash
# Find the previous good bundle
ls -lt pipeline/output/morphology-bundle-v*.json
# Or find it in git history
git log --oneline -- pipeline/output/morphology-bundle-v1.json

# Revert the deployed bundle to the prior version
cp pipeline/output/morphology-bundle-v{N-1}.json pipeline/output/morphology-bundle-v1.json
# Then re-deploy to wherever the Flutter app loads the bundle from
```

### 7.2 Root cause diagnosis

1. **`prompt_hash` mismatch:** Check `bundle.prompt_hash` against `sha256sum pipeline/prompt-v1.md`. A mismatch means the bundle was built with a different prompt than what's currently in the repo.
2. **Model behaviour regression:** Compare a sample of records from the bad bundle to the prior bundle. If accuracy dropped, the model may have changed behaviour (check Anthropic release notes for Haiku 4.5).
3. **Merge bug:** If morphology decompositions look correct but etymology data is wrong or missing, the issue is in `pipeline/merge_bundle.py` or the GCIDE extraction.

### 7.3 Re-build with prior prompt

```bash
# Restore the old prompt (if it was overwritten)
git checkout HEAD~1 -- pipeline/prompt-v1.md

# Re-run from step 2
python3 pipeline/build_llm_cache.py
python3 pipeline/validate_llm_cache.py
python3 pipeline/build_etymology_overlay.py
python3 pipeline/merge_bundle.py
```

---

## 8. Provider-swap runbook (Haiku → Gemini)

**When to use:** Anthropic API is returning quota errors (`429`) or sustained errors (>5 min) during a build run.

**Target swap time:** < 1 hour. Validated in Phase 3 smoke test ([#527](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/527)).

```
1. Stop the current build run (Ctrl+C or kill the process).

2. Set the primary provider:
   export PRIMARY_PROVIDER=gemini
   # (Default is "anthropic"; the build script reads this env var)

3. Confirm Gemini credentials and quota:
   echo $GEMINI_API_KEY   # must be non-empty
   # Check quota in Google AI Studio → My quota

4. Resume from where the build stopped (the script checkpoints
   progress to pipeline/output/top10k-llm-cache-v1.json):
   python3 pipeline/build_llm_cache.py --resume

5. Expected behaviour:
   - Quality: 90.1% agreement with Haiku at top-1k scale (equivalent)
   - Cost: ~$19 for top-10k (11% higher than Haiku's ~$17)
   - Wall-clock: ~42 min for top-10k (vs ~7.5 min Haiku with caching)

6. After the Gemini build completes, proceed with steps 3–5 normally
   (validate_llm_cache.py, build_etymology_overlay.py, merge_bundle.py).

7. After Anthropic quota is restored, swap back for the next rebuild:
   unset PRIMARY_PROVIDER   # or set to "anthropic"
```

**Note on the `sources` field in the bundle:** When built with Gemini, each record's `sources` array will contain `"llm-gemini-2.5-flash"` instead of `"llm-claude-haiku-4.5"`, and the bundle-level `model` field will be `"gemini-2.5-flash"`. This is correct and intentional — it records what actually built the bundle.

---

## 9. Appendix — Vendor choice rationale

This appendix records the Haiku-vs-Gemini decision history for future maintainers. It is not load-bearing for day-to-day operations.

**Timeline:**

1. **2026-05-09 (Spike C, [#522](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/522)):** Claude Haiku 4.5 chosen as L1 primary. 89.6% strict accuracy on 51-word test set; all four acceptance criteria passed.

2. **2026-05-11 morning (Spike D, [#533](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/533)):** Gemini 2.5 Flash measured +2.1pp accuracy and −30% projected top-30k cost vs Haiku on the same test set. The locked decision rule fired and architecture switched to Gemini as L1 primary.

3. **2026-05-11 evening (top-1k production validation):** A Gemini run on 1000 SUBTLEX-US words showed the Spike D cost projection didn't hold at scale:

   | Metric | Spike D projection (51 words) | Top-1k actual |
   |---|---|---|
   | Gemini vs Haiku accuracy | +2.1pp better | equivalent (90.1% agreement) |
   | Gemini vs Haiku cost | −30% cheaper | **+11% more expensive** ($1.90 vs $1.71) |
   | Gemini vs Haiku wall-clock | not measured | **6× slower** (42 min vs 7.5 min) |

   Root cause: Haiku's explicit `cache_control` achieves near-100% prompt cache hits at production scale; Gemini's implicit caching is sporadic. At 51 words, per-call output token cost dominates and Gemini looks cheaper. At 1000+ words, prompt-caching savings dominate and Anthropic's explicit caching wins decisively.

4. **Locked decision (current):** Haiku 4.5 as L1 primary. Gemini 2.5 Flash as secondary (provider-swap path only). This is a data-driven revert; see `pipeline/validation/top1k-comparison.md` for full evidence.

**Full evidence:** [`spikes/morphology-engine/d-model-survey/FINDINGS.md`](../../spikes/morphology-engine/d-model-survey/FINDINGS.md) · [`pipeline/validation/top1k-comparison.md`](../../pipeline/validation/top1k-comparison.md)

---

## 10. Cross-references

- [`ROOT_FAMILIES_DECISION.md`](ROOT_FAMILIES_DECISION.md) — locked architecture decision and 12-day build plan
- [`MORPHOLOGY_RECORD_SCHEMA.md`](MORPHOLOGY_RECORD_SCHEMA.md) — canonical per-word record format (Phase 2 deliverable)
- [`morphology-bundle-v1.schema.json`](morphology-bundle-v1.schema.json) — machine-readable JSON Schema for Flutter-side validation
- [`ROOT_FAMILIES_ENGINE.md`](ROOT_FAMILIES_ENGINE.md) — engine design (how Flutter uses the bundle at runtime)
- [`docs/operations/MORPHOLOGY_BUNDLE_BENCHMARK.md`](../operations/MORPHOLOGY_BUNDLE_BENCHMARK.md) — Phase 5 mobile validation results
- GitHub epic [#385](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/385) — root families epic
- GitHub issue [#406](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/406) — Phase 4 UI implementation (handoff target)
