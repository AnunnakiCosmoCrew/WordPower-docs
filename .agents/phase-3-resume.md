# Phase 3 (#527) — Resume after credit outage

You were working on [Phase 3 of the root-families engine build (#527)](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/527). You stopped mid-task because the Anthropic API returned an out-of-credit error. **Credits are topped up now.** Resume from where you stopped, but do not redo work you've already done — every redundant call costs real money.

## Step 1 — Take stock before spending anything

Before any API call, run these read-only checks to figure out where you stopped:

```sh
cd /Users/merty.ertugrul/IdeaProjects/WordPower-docs

# Recent commits — what did you commit before stopping?
git log --oneline --since="3 days ago" | head -20

# Pipeline directory state
ls -la pipeline/ pipeline/output/ 2>/dev/null

# Progress comments / acceptance ticks on the issue
gh issue view 527 --repo AnunnakiCosmoCrew/WordPower-app \
  --json body,comments | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('=== BODY ===')
print(d['body'])
print()
print('=== COMMENTS ===')
for c in d.get('comments', []):
    print(f\"--- {c['author']['login']} {c['createdAt']} ---\")
    print(c['body'][:500])
    print()
"
```

Compare what exists on disk against the acceptance checklist in #527's body. Anything already present and committed = done. **Do not rerun any item that's already produced output.**

## Step 2 — Verify API access is restored

The Anthropic outage was the trigger for the stop. Confirm it's back before resuming any Anthropic-dependent step:

```sh
# Pull keys from interactive zsh (the Bash tool's subshell doesn't inherit them)
export ANTHROPIC_API_KEY="$(zsh -ic 'echo -n $ANTHROPIC_API_KEY' 2>/dev/null)"
export GEMINI_API_KEY="$(zsh -ic 'echo -n $GEMINI_API_KEY' 2>/dev/null)"

# 1-call probe for each — cheap, ~$0.001 total
python3 -c "
import os, anthropic
c = anthropic.Anthropic()
r = c.messages.create(model='claude-haiku-4-5', max_tokens=10,
                      messages=[{'role':'user','content':'say ok'}])
print('Anthropic OK:', r.content[0].text)
"

python3 -c "
import os
from google import genai
c = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
r = c.models.generate_content(model='gemini-2.5-flash', contents='say ok')
print('Gemini OK:', r.text[:30])
"
```

If either fails with 429 / billing error, **stop and report to the user before doing anything else**. Don't try to work around a billing issue.

## Step 3 — Resume from the next unchecked acceptance item

Phase 3's acceptance checklist (from #527's body):

- [ ] `pipeline/download_frequency_list.sh` — SUBTLEX-US, top-10k, pin version
- [ ] `pipeline/build_l1_cache.py` — based on `spikes/morphology-engine/d-model-survey/scripts/run_gemini.py`
- [ ] **Top-1k pilot run** (~$2, ~30 min): Gemini 2.5 Flash, prompt-v1, words 1-1000 → `pipeline/output/top1k-llm-cache.json`
- [ ] Hand-validate top-1k: 100 random records, eyeball score. **Gate: ≥ 85% acceptable.**
- [ ] **Top-10k production run** (~$20, ~5-10 min): words 1-10000 → `pipeline/output/top10k-llm-cache-v1.json`
- [ ] **Sonnet validation pass** (~$10-15): Sonnet 4.6 on Gemini medium/low + 10% high-confidence audit → `pipeline/output/top10k-llm-cache-v1-validated.json`
- [ ] **Provider-fallback smoke test** (~$2): 100-word Haiku run to verify fallback path works
- [ ] Total spend ≤ $50 (target ~$35)

Resume from the first unchecked item.

## Step 4 — Hard constraints (do not violate)

1. **Locked prompt:** Use `pipeline/prompt-v1.md` verbatim. Do NOT modify it. It was iterated and locked under #525, with SHA-256 documented in the file. Modifying it invalidates the existing measurement baselines.

2. **Schema:** Output records match `docs/architecture/ROOT_FAMILIES_ENGINE.md` §6. The Gemini and Anthropic runners already enforce this via forced tool-call. Don't write your own JSON parsing.

3. **Pilot gate is real:** If top-1k hand-validation falls below 85%, **do not proceed to top-10k**. Run the fallback ladder from `ROOT_FAMILIES_DECISION.md` §Locked decisions item 7: tighten prompt → re-run pilot → drop to top-5k if still failing → defer L2 if still failing.

4. **Don't overwrite committed results.** Before any write to `pipeline/output/` or `spikes/morphology-engine/c-llm-haiku/results-v1/`, run `git log --oneline -- <target-path>`. If the user committed something there, do NOT overwrite it — read it instead. (This is a lesson learned the hard way last session: redundant runs cost the user ~$10.)

5. **Cost cap:** Total Phase 3 spend ≤ $50. If you approach $30 and haven't finished, **stop and report**.

## Step 5 — Canonical references

- **Architecture and decision rationale:** `docs/architecture/ROOT_FAMILIES_DECISION.md` — the canonical doc; read first
- **Schema:** `docs/architecture/ROOT_FAMILIES_ENGINE.md` §6
- **Working Gemini runner (reference for `build_l1_cache.py`):** `spikes/morphology-engine/d-model-survey/scripts/run_gemini.py`
- **Working Anthropic runners:** `spikes/morphology-engine/c-llm-haiku/scripts/run_haiku.py` and `run_sonnet.py`
- **Locked prompt:** `pipeline/prompt-v1.md`
- **Spike D findings (why Gemini, not Haiku):** `spikes/morphology-engine/d-model-survey/FINDINGS.md`

## Step 6 — When done

1. **Commit:** Docs repo allows direct push to `main` (per `CLAUDE.md`). Commit messages: `WP-527 feat(morphology): …`
2. **Update #527:** post a comment with the final results table (per-stage cost, top-1k pilot score, top-10k coverage, Sonnet validation results, total spend). Close the issue.
3. **Move board:** `gh project item-edit` to set status=Done for #527 on project board 11.

## Step 7 — When in doubt

The user prefers a brief pause to check than a confident-but-wrong action. If you're about to:
- Run anything that costs > $5
- Overwrite a file with uncommitted user changes
- Modify `pipeline/prompt-v1.md`
- Skip a gate
- Make an architecture decision

**stop and ask first.** A 30-second confirmation is cheaper than a $10 redundant run or a regressed bundle.
