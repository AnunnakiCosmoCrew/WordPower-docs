# Phase 4 Audit — Vocabulary System: "Organized Learning"

> [!abstract]
> Phase 4 is **substantially complete**. 9 of 10 planned deliverables shipped: word lists, domain browsing, root families (with a fully custom build pipeline), word discovery, dashboard, quiz-content variety, least-recently-quizzed ordering, capture friction reduction, and a multi-source dictionary backbone. The Cambridge primary-source plan was shelved after the licensing spike returned incompatible terms; Merriam-Webster Learner's stepped in as the dev primary. Mixed quiz-type sessions (#389) is the only originally-scoped deliverable not yet started. 113 phase-4 issues closed; 17 remain open (8 in-flight UI/sync bugs surfaced in the final days + 8 epic parents whose sub-issues are all done + #350 epic still tracking the Oxford follow-up).

| | |
|---|---|
| **Phase** | Phase 4 — Vocabulary System: "Organized Learning" |
| **Platform** | Web (Flutter) + iOS + Android + backend (Spring Boot) |
| **Duration** | May 1 – May 16, 2026 (~16 days; bulk of work May 4–16) |
| **App repo: planned epics** | 10 (per PROJECT.md Phase 4) |
| **App repo: delivered issues** | 113 (all phase-4 labeled, all closed) |
| **App repo: merged PRs in window** | 157 |
| **App repo: commits on main in window** | 140 |
| **Docs repo: commits in window** | 37 |
| **Spikes completed** | 11 (Cambridge, MW Learner's, Oxford, browser extension, root-families A/B/C/D + re-spike, embedding-domain) |
| **Open Phase 4 issues remaining** | 17 (8 in-flight bugs, 8 epic parents to close, #350 awaiting Oxford follow-up) |
| **Docs repo audit issues** | None opened — audit findings folded into ad-hoc commits (same pattern as Phase 3) |

---

## Planned Deliverables — 9 of 10 Shipped

### Epic 1: Multi-source dictionary cache (#350) — Pivoted

Original plan: Cambridge Learner's → Merriam-Webster Learner's → Free Dictionary chain. After spike #353, Cambridge licensing was incompatible (no caching beyond session, no free-product licensing, base fee in the low-five-figures annually) and the epic was re-scoped on the fly.

| # | Issue | Lead time |
|---|---|---|
| #353 | Spike: Cambridge Dictionary API research + commercial-tier registration | 60.8h |
| #354 | Schema migration: composite `(word, source)` key | 62.7h |
| #355 | Cambridge Dictionary API client | 86.9h (closed won't-do post-shelving) |
| #356 | DictionaryAggregator service with per-field source priority chain | 85.8h |
| #357 | Two-pass async enrichment | 87.4h |
| #358 | Cache-miss instrumentation + per-source tier alerting | 86.7h |
| #436 | Spike: Merriam-Webster Learner's Dictionary API as Cambridge alternative | 10.5h |
| #439 | Implement MerriamWebsterService + Learner's Dictionary client | 0.9h |
| #445 | Spike: Oxford Dictionary API as Cambridge replacement | 0.7h |
| #448 | CEFR word-level mapping: open-list lookup table fallback | 4.6h |
| #512 | Remove Cambridge dictionary source (epic #350 shelved) | 2.8h |
| #518 | MW Learner's parser fix — populate examples from `def[].sseq[].vis[]` | 12.0h |

> The epic parent (#350) remains open pending Oxford follow-up; Cambridge sub-issue closed won't-do. CEFR-J + wordfreq open-list (#448) replaced Cambridge's CEFR field.

### Epic 2: Word Lists & Folders (#383)

| # | Issue | Lead time |
|---|---|---|
| #392 | Word lists: schema + repository | 41.1h |
| #393 | Word lists: REST API for list CRUD + membership | 42.1h |
| #394 | Word lists: landing screen with create/rename/delete | 41.6h |
| #395 | Word lists: add/remove from word detail and bulk-select | 45.5h |
| #396 | Word lists: list-filtered notebook view | 45.5h |

### Epic 3: Domain browsing & filtering (#384)

| # | Issue | Lead time |
|---|---|---|
| #397 | Domain filter: filter params on notebook list endpoint | 51.2h |
| #398 | Domain filter: filter chip row UI | 51.2h |
| #399 | Domain filter: persist last-used filter locally | 52.0h |
| #400 | Domain filter: domain landing — domains with counts | 61.5h |

### Epic 4: Root families (#385) — Largest deliverable

Original plan: source a roots dataset, ship a tree view. What actually shipped: 4 spikes (A: MorphyNet, B: Skeat/Webster's 1913, C: LLM Haiku 4.5, D: comparative model survey), a 7-phase custom build pipeline, mobile bundle, and an L0/L1/L3 layered fallback service.

| Track | Issues |
|---|---|
| Original Phase 4 issues (#385) | #405, #406, #407, #408, #409, #410 (6 issues, median 88.4h) |
| Build-pipeline spikes A–D + re-spike | #520, #521, #522, #533, #525 (5 issues) |
| 7-phase build pipeline | #526, #527, #528, #529, #530, #531 (Phase 7 = GPL review) |
| Production bug fixes | #465, #466, #468, #471, #472, #543, #544, #549, #550, #551, #552, #553, #554, #555, #632 (15 issues) |

> [!info] Root-families decisions captured in docs repo
> - [`ROOT_FAMILIES_DECISION.md`](../architecture/ROOT_FAMILIES_DECISION.md) synthesizes the Week 1 spikes
> - [`MORPHOLOGY_BUILD_PIPELINE.md`](../architecture/MORPHOLOGY_BUILD_PIPELINE.md) — operational runbook (locked 2026-05-11)
> - [`MORPHOLOGY_RECORD_SCHEMA.md`](../architecture/MORPHOLOGY_RECORD_SCHEMA.md) — v1 record schema
> - Layered architecture: L0 root-substring scan → L1 LLM cache (top-10k) → L2 GCIDE etymology overlay → L3 Wikipedia roots fallback

### Epic 5: Word discovery (#386) — v1 → v2 redesign mid-phase

v1 shipped May 7 (#414–#417); was judged thin (no real similarity engine, just WordNet sibling fetch). v2 designed and shipped within 24h (#481–#486) with a combined CEFR/semantic/root-family/POS similarity engine, quiz augmentation (guest words), and a Discover section with three-action cards.

| # | Issue | Track | Lead time |
|---|---|---|---|
| #414 | Word discovery: related-words endpoint | v1 | 90.3h |
| #415 | Word discovery: standalone discovery browse page | v1 | 90.0h |
| #416 | Word discovery: post-quiz related-word prompt | v1 | 92.4h |
| #417 | Word discovery: track dismissed/added suggestions | v1 | 93.3h |
| #481 | Word discovery: similarity engine (CEFR/semantic/root/POS scoring) | v2 | 17.4h |
| #482 | Word discovery: quiz augmentation — guest words | v2 | 22.3h |
| #483 | Word discovery: end-of-quiz prompt — batched add-to-list | v2 | 19.6h |
| #484 | Word discovery: Discover section UI — three-action cards | v2 | 19.6h |
| #485 | Word discovery: "Don't suggest" global block list | v2 | 19.6h |
| #486 | Word discovery: quiz-to-Discover bridge — warm-signal boost | v2 | 23.6h |

### Epic 6: Dashboard (#387)

| # | Issue | Lead time |
|---|---|---|
| #401 | Dashboard: aggregation endpoint | 110.2h |
| #402 | Dashboard: streak calculation | 95.1h |
| #403 | Dashboard: route with summary cards | 95.4h |
| #404 | Dashboard: CEFR distribution chart | 95.5h |

### Epic 7: Least-recently-quizzed candidate ordering (#388)

| # | Issue | Lead time |
|---|---|---|
| #388 | Least-recently-quizzed candidate ordering (replaces Phase 3 random-sampling fix) | 207.4h |

### Epic 8: Mixed quiz-type sessions (#389) — **Not shipped**

The only originally-scoped deliverable that did not start. Carried over to Phase 5.

### Epic 9: Quiz-content variety (#390)

| # | Issue | Lead time |
|---|---|---|
| #411 | Quiz variety: definition-sense rotation in MCQ | 233.2h |
| #412 | Quiz variety: FITB stem rotation | 234.0h |
| #413 | Quiz variety: per-(user, word) sense + stem usage tracking | 232.8h |

> Lead times are inflated because these were created at phase kickoff (May 3) but only worked at the tail end (May 13).

### Epic 10: Reduce capture friction (#391)

| # | Issue | Lead time |
|---|---|---|
| #418 | Capture friction: Quick Capture UX polish | 93.0h |
| #419 | Capture friction: spike — browser extension stack | 93.0h |
| #420 | Capture friction: browser extension v1 — select word and save | 256.8h |
| #421 | Capture friction: iOS share-sheet integration | 256.8h |
| #422 | Capture friction: OCR-from-screenshot capture | 256.8h |

---

## Additional Deliverables — Beyond Scope

### Domain taxonomy redesign (mid-to-late phase)

Browse-by-domain dogfooding surfaced that the existing taxonomy didn't match user mental models. A flat 10-domain taxonomy with per-user personalization replaced the existing tree, plus an embedding-based suggestion engine.

| # | Issue | Lead time |
|---|---|---|
| #654 | Word detail: manual domain assignment (override auto-enriched value) | 28.3h |
| #655 | Spike: embedding-based domain suggestion cost/UX validation | 3.3h |
| #656 | Top-3 suggested chips in domain picker (one-tap assign) | 21.7h |
| #664 | Flat 10-domain classifier with per-user personalization | 7.8h |
| #665 | Decide(product): PROJECT.md taxonomy — flat 10-domain vs 15-domain HTOED hierarchy | 0.6h |

### CI hardening (final 48h)

| # | Issue | Lead time |
|---|---|---|
| #658 | CI: require bug-labelled PRs to add lines in a test file | 3.7h |
| #659 | CI: auto-reopen bug issues closed without a referencing commit | 3.0h |

### Production bug response (May 12 dogfooding wave)

A single dogfooding session on May 12 surfaced ~7 high-priority sync/dashboard bugs that were fixed within hours.

| # | Issue | Lead time |
|---|---|---|
| #567 | Sync: local Drift cache shows 23 words but server has 2 | 1.6h |
| #568 | API: `/api/words?size=200` returns 500 instead of validation error | 1.5h |
| #569 | API: `/api/words/count` routes to `/api/words/{id}` — 400 'Invalid UUID' | 0.9h |
| #570 | API: `/api/words` response omits cefrLevel, domain, enrichmentStatus | 1.6h |
| #571 | Dashboard: Stats page shows 'Could not load stats' despite 200 | 1.3h |
| #572 | Sync: words not syncing to backend (local 23 vs server 2) | 5.8h |
| #573 | Home: 'Checking your review queue…' spinner hangs on initial load | 1.8h |

### Discover engine quality fixes (post-dogfooding)

| # | Issue | Lead time |
|---|---|---|
| #584 | `insideBand` rejects every candidate with null CEFR — Discover always empty | 15.3h |
| #585 | MCQ silently shrinks requested size when guest augmentation falls short | 13.0h |
| #586 | CEFR distribution uses cache-only query, ignores `cefr_word_map` fallback | 13.7h |
| #591 | Discover engine silently drops every candidate without a cached dictionary definition | 26.5h |
| #596 | Diversify Discover ordering — eliminate alphabetical clumping in tied-score results | 55.4h |

### UI/quiz production bugs (final 4 days)

19 issues on web UI polish, quiz flow, and modal dialogs — surfaced once dashboard, lists, and discovery were live and being used.

| Pattern | Examples |
|---|---|
| Modal scrim/dismiss bugs | #610, #612, #613 (Create list dialog won't auto-close, scrim too transparent) |
| Quiz session resilience | #598, #605, #609 (silent quiz-start failure, mid-session POST error, ghost question content) |
| Web-platform-only bugs | #608 (word detail can't scroll on web), #625 (→ glyph missing), #617 (chart legend on first paint) |
| Quick Capture polish | #618, #619, #620, #621 (duplicate snackbar, error state, label overlap, error-outline flash) |

---

## What Shipped (User-Facing)

- **Word Lists & Folders** — custom collections with create/rename/delete, bulk add/remove from word detail, list-filtered notebook view
- **Domain browsing & filtering** — filter chip row on notebook, persisted last-used filter, domain-landing screen with per-domain counts
- **Root families** — word-family tree on word detail with prefix/suffix breakdown, on-demand bundle download (~0.3 MB compressed), L0/L1/L3 layered fallback for out-of-vocab words
- **Word discovery v2** — Discover section with three-action cards (add / dismiss / "don't suggest"), in-quiz guest words for recognition-only quizzes, end-of-quiz batched add-to-list prompt, per-user block list, warm-signal boost from quiz performance
- **Dashboard** — collected/mastered counts, streak, CEFR distribution chart, 7-day activity chart, Stats page
- **Quiz-content variety** — definition-sense rotation in MCQ, FITB stem rotation, per-(user, word) sense + stem usage tracking
- **Least-recently-quizzed ordering** — replaces Phase 3 random-sampling with `UserWord.lastQuizzedAt`
- **Capture friction reductions** — Quick Capture UX polish, browser extension v1 (select word → save), iOS share-sheet integration, OCR-from-screenshot capture
- **Manual domain assignment** — override auto-enriched domain via a picker sheet with top-3 personalized suggestions
- **Multi-source dictionary fallback** — MW Learner's primary (dev/staging) + Free Dictionary coverage fallback, content-safety filter applied to all sources
- **Mobile audio + UI polish** — pronunciation buttons properly labeled UK/US with per-button IPA, escape-to-dismiss modals, Word Detail scroll fix on web

## What Shipped (Engineering Foundation)

- **Morphology build pipeline** — 7-phase bundle build (prompt iteration → schema freeze → L1 LLM cache top-10k → L2 GCIDE etymology overlay → bundle merge + mobile validation → docs/handoff → GPL legal review). Reproducible, documented in [`MORPHOLOGY_BUILD_PIPELINE.md`](../architecture/MORPHOLOGY_BUILD_PIPELINE.md).
- **Comparative LLM model survey** — Spike D evaluated Gemini 2.5 Flash, GPT, Llama, Sonnet against Haiku 4.5 at production scale; Haiku 4.5 retained as L1 primary based on top-1k production validation.
- **Discover similarity engine** — combined CEFR/semantic (WordNet + Roget thematic clusters)/root-family/POS scoring, CEFR ±1 hard filter, per-cluster Roget cap, hash-based diversity tiebreaker.
- **Multi-source dictionary cache** — composite `(word, source)` schema, DictionaryAggregator with per-field source priority, two-pass async enrichment (sync primary + async fallback), cache-miss instrumentation per source tier.
- **CEFR word-level open-list** — CEFR-J / wordfreq lookup-table fallback (#448) when dictionary upstream doesn't tag CEFR; powers Dashboard's CEFR distribution chart for words without cached entries.
- **CI bug-discipline workflow** — `bug-close-audit` workflow auto-reopens bug issues that close without a referencing commit (#659); bug-labelled PRs are required to add lines in a test file (#658).
- **Test-architecture convention** — overrides at leaf boundaries (HTTP client / repository), not feature providers, documented in `TESTING_STRATEGY.md` (#472).
- **GCIDE GPL legal posture** — documented in compliance docs; GCIDE used at build time only, never shipped to clients.

---

## Deviations from Plan

| Change | Rationale |
|---|---|
| **Cambridge primary-source shelved** | Cambridge licensing came back incompatible — no caching beyond session, no free-product licensing, low-five-figures base fee. MW Learner's took the dev primary slot the same week; Oxford was filed as the future replacement candidate (#445). |
| **Word discovery redesigned end-to-end** | v1 shipped May 7 with thin WordNet-sibling fetch. v2 was designed and merged within 24h with a real similarity engine. Cost: 6 new issues; saved: rolling out a weak feature to users. |
| **Domain taxonomy rebuilt mid-phase** | After Browse-by-Domain shipped, dogfooding revealed the old domain tree didn't match user mental models. Flat 10-domain taxonomy + per-user personalization replaced it (#664, #665), plus an embedding-suggestion spike (#655). |
| **Root families exploded into a 4-spike + 7-phase build pipeline** | Original epic assumed "pick a dataset, ship a tree view." Reality: no off-the-shelf dataset had the quality + coverage needed. Built a custom morphology bundle from GCIDE + Haiku 4.5 LLM decomposition of top-10k SUBTLEX words. |
| **Mixed quiz-type sessions (#389) deferred** | Time budget consumed by root-families build pipeline and word-discovery redesign. The only originally-scoped Phase 4 deliverable not started. |
| **CI hardening added (#658, #659)** | Bug-close discipline gap was visible in Phase 3 retrospective (#544 "WP-471 was reverted, never replaced"). Two CI gates landed in the final 48h to prevent recurrence. |
| **No iOS share-sheet / browser-extension / OCR rollout to production** | Capture-friction issues (#420, #421, #422) closed against design/spec doc, not against production rollout. App-store and extension-store distribution remain Phase 6. |

---

## Cycle Time & Lead Time

> [!info] Definitions
> - **Lead time** = time from issue created to issue closed (includes wait time in backlog)
> - Phase 4 had two large batch-creation events (Cambridge epic May 1, main Phase 4 batch May 3) — those issues sat in the backlog while spikes ran first

### Overall (113 closed phase-4 issues)

| Metric | Value |
|---|---|
| **Average** | 44.4 hours |
| **Median** | 19.6 hours |
| **Fastest** | 0.3 hours |
| **Slowest** | 256.8 hours (capture-friction sub-issues, batch-created May 3, closed May 14) |

### By category

| Category | Count | Median | Notes |
|---|---|---|---|
| **Production bugs (Sync/Stats)** | 7 | 1.6h | All May 12 dogfooding fixes within the same day |
| **Domain taxonomy redesign + CI** | 7 | 3.7h | Tight scope, high-velocity end-of-phase work |
| **Root families bug fixes** | 14 | 3.2h | Found by dogfooding on web after bundle landed |
| **UI/quiz prod bugs** | 19 | 6.9h | Median half a workday — same fast-fix loop as Phase 3 |
| **Discovery bug fixes** | 5 | 15.0h | Similarity engine had several silent-drop bugs |
| **Word discovery v2 redesign** | 6 | 19.6h | Tight cluster — 6 issues in 24h |
| **Word Lists** | 5 | 42.1h | Standard epic cadence |
| **Domain filter** | 4 | 51.6h | Standard epic cadence |
| **Dictionary multi-source (Cambridge era)** | 6 | 85.9h | Inflated by Cambridge-shelving discovery |
| **Root families (initial epic)** | 6 | 88.4h | Spike A → tree view; before build-pipeline scope-out |
| **Word discovery (v1)** | 4 | 91.4h | Before redesign |
| **Dashboard** | 4 | 95.5h | Last epic to land before May 12 dogfooding |
| **Capture friction** | 5 | 256.8h | Batch-created May 3, worked at end of phase |
| **Quiz variety** | 3 | 233.2h | Same — batch-created May 3, worked May 13 |
| **Root families build pipeline** | 11 | 38.1h | Custom 7-phase pipeline, completed in ~2 days each |
| **Least-recently-quizzed** | 1 | 207.4h | Single issue, sat in backlog while Phase 3 fixes landed |

> [!tip] Observations
>
> - **Median lead time dropped from 75h (Phase 3 fresh issues) to 19.6h** — Phase 4 had many small bugs that closed within a day. The remaining medium-sized epic work stayed in the 40–95h range, consistent with Phase 3.
> - **Production bug response stayed extremely fast** — May 12 dogfooding wave fixed 7 issues in median 1.6h. Same pattern as Phase 3's iOS/Android cutover bugs (median 0.5h).
> - **Word discovery v2 redesign was the fastest epic execution of the phase** — 6 sub-issues, all closed within 24h of design.
> - **Capture friction has the highest median (256.8h)** — but this is pure backlog wait. Sub-issues were batch-created May 3 and only worked May 13–14 once browser-extension spike (#419) resolved the stack. True active time was a single day per issue.
> - **Root-families dominates total effort** — 32 issues across the initial epic, 4 spikes, build pipeline, and bug fixes. ~28% of all Phase 4 issues.

---

## Lessons Learned

### What went well

| Observation | Evidence |
|---|---|
| **Spikes prevented sunk cost** | Cambridge spike #353 returned within 60h with clear "shelve" signal. Had we skipped the spike and started #355 client implementation directly, we'd have wasted days. |
| **24h pivot from Discover v1 → v2** | v1 closed May 7 at 11:13, v2 was designed and filed at 15:25 the same day. All 6 v2 sub-issues closed in 24h. Catching the "shallow similarity is worse than no similarity" failure mode immediately saved a follow-up phase. |
| **Root-families custom pipeline scaled cleanly** | Building a 7-phase build pipeline (spike → prompt → schema → LLM cache → etymology overlay → bundle → docs) was a lot of work, but every phase had a clear deliverable. No phase was stuck. |
| **Multi-model spike (Spike D) was the right judgment call** | Comparing Gemini 2.5 Flash, GPT, Llama against Haiku 4.5 confirmed Haiku as L1 primary at top-1k production scale. Without this, we'd have shipped on a 51-word measurement — exactly the risk the [validate-at-production-scale](../../.claude/projects/-Users-merty-ertugrul-IdeaProjects-WordPower-docs/memory/feedback_validate_at_production_scale.md) memory warns about. |
| **CI bug-discipline added at the right moment** | #658 (require test lines in bug PRs) + #659 (auto-reopen bug issues closed without a commit) shipped after #544 surfaced "WP-471 was reverted, never replaced." Closed the loop on the Phase 3 regression. |
| **Production bug response stayed at Phase 3 cadence** | 7 sync/stats bugs from May 12 dogfooding, median 1.6h to close. Same hot-fix discipline as Phase 3's cutover. |

### What didn't go well

| Observation | Impact | Root cause |
|---|---|---|
| **Discover v1 shipped wrong** | Built a similarity feature with no real similarity engine; had to redesign within 24h. Cost: 4 closed issues + 6 new issues. | Spec described user-facing behaviour but didn't pin the scoring algorithm. Same pattern as Phase 3's spelling-quiz redesign: "the data layer was too thin and we didn't notice until we used it." |
| **Domain taxonomy rebuilt after the UI shipped** | Browse-by-Domain (#400) shipped May 6 against the old taxonomy; flat 10-domain replacement (#664, #665) landed May 15. Cost: ~5 issues rebuilding what the UI displayed. | Auto-enriched domain values weren't dogfooded against real notebooks before the UI was built. The taxonomy was inherited from Phase 2's enrichment work; no one questioned it until it was on screen. |
| **Sync drift on web (#567, #572)** | Local Drift cache showed 23 words; server had 2. Found by dogfooding, not by tests. A user could plausibly lose data here. | Cloud-sync outbox + delta-pull flows have no integration test exercising "frontend believes more than backend." Phase 2's offline outbox tests don't catch divergence in the other direction. |
| **19 UI bugs after Dashboard / Lists / Discovery shipped** | The final 4 days of the phase were dominated by polish bugs — modal scrim transparency, ghost quiz questions, web-only scroll bugs, glyph rendering. | The pluggable-quiz-engine and lists/dashboard UIs aren't covered by integration tests on web. Most bugs were "renders fine on iOS, looks broken on web." Need golden tests + integration coverage per platform. |
| **Mixed quiz-type sessions (#389) deferred** | The only originally-scoped Phase 4 deliverable not started. | Time consumed by root-families build pipeline (~28% of issues) and Discover v2 redesign. Original Phase 4 plan didn't budget for either. |
| **Capture-friction items closed but not in production** | iOS share-sheet (#421), browser extension v1 (#420), and OCR (#422) all closed against spec docs and unit-level implementation, not against an end-to-end "user installs the extension and saves a word" test. | Distribution channels (App Store, Chrome Web Store) are Phase 6 work; capture-friction features were closed when "the code works on the dev box." Risk: they'll need rework when Phase 6 tries to ship them. |
| **Epic parent issues stayed open after sub-issues closed** | 8 phase-4 epic parents (#383, #384, #385, #386, #387, #389 [legitimate], #390, #391) remain open despite all sub-issues being done. | Epic close behaviour differs from Phase 3, where epics got closed when sub-issues completed. Looks like a hygiene gap, not a real "incomplete" signal. |

### What to change for Phase 5

1. **Pin algorithms in spec, not just UX.** Discover v1 and Spelling v1 (Phase 3) both shipped wrong because the spec described behaviour without naming the scoring/difficulty model. Phase 5's FSRS migration, semantic quizzes, and gamified modes all have hidden algorithmic choices — name them upfront.
2. **Ship integration tests per platform.** Web-only UI bugs (scroll, glyph, scrim, ghost questions) dominated the final 4 days. Phase 5 should add Flutter `integration_test` per platform target — iOS, Android, web — gating the deploy pipeline.
3. **Add sync-divergence tests.** #567/#572 (frontend has 23, backend has 2) need a regression test. Phase 5 should add a property-style test: any sequence of online/offline writes leaves frontend and backend with the same word set.
4. **Close epic parents on sub-issue completion.** Either automate it or add it to the close checklist. 8 stale epic parents skew Phase 4's "open issues" count.
5. **Dogfood content models before shipping their UI.** Domain taxonomy needed a rebuild because no one tried Browse-by-Domain on a real notebook before the UI was built. Phase 5's semantic quizzes (synonym/antonym match, odd-one-out) should dogfood the underlying lexical data on a real notebook before the quiz UI lands.
6. **Mixed quiz-type sessions (#389) ships in Phase 5.** Only originally-scoped Phase 4 deliverable not started — pull it into Phase 5 scope explicitly, don't let it drift.
7. **Track "In Progress" timestamps.** Carried from Phases 2 and 3 lessons. Phase 4 still doesn't separate cycle time from lead time, and the capture-friction 256.8h numbers continue to mislead.

---

## Open Items Carried to Phase 5

### Originally-scoped deliverables not yet started

| # | Issue | Notes |
|---|---|---|
| #389 | Mixed quiz-type sessions | Only Phase 4 originally-scoped deliverable not started |

### In-flight bugs (still open at phase close)

| # | Issue | Severity |
|---|---|---|
| #603 | Browse by Domain shows "No domains yet" despite enriched words | Bug — backend |
| #606 | Word detail preview shows wrong POS (`ephemeral` tagged as noun) | Bug — backend |
| #615 | Escape key does not dismiss modal dialogs | Bug — frontend |
| #619 | Quick Capture: Word field error state doesn't clear when typing | Bug — frontend |
| #620 | Quick Capture: notes field label overlaps typed text | Bug — frontend |
| #622 | Stale Quick Capture form lingers in DOM on Word detail | Bug — frontend |
| #623 | Unhandled Dart exception fires on every page load | Bug — frontend |
| #624 | Drift WASM SQLite falls back to sharedIndexedDb (COOP/COEP not effective) | Bug — frontend |

### Epic parents still open (sub-issues done — needs hygiene close)

| # | Epic |
|---|---|
| #383 | Word Lists & Folders (5/5 sub-issues closed) |
| #384 | Domain browsing & filtering (4/4 sub-issues closed) |
| #385 | Root families (all sub-issues + build pipeline closed) |
| #386 | Word discovery (all v2 sub-issues closed) |
| #387 | Dashboard (4/4 sub-issues closed) |
| #390 | Quiz-content variety (3/3 sub-issues closed) |
| #391 | Reduce capture friction (5/5 sub-issues closed) |
| #350 | Multi-source dictionary (Cambridge shelved; awaiting Oxford follow-up) |

### Deferred design decisions handed to Phase 5

| Item | Notes |
|---|---|
| Oxford Dictionary API evaluation | #350 sub-issue, follow-up to Cambridge shelving. Spike #445 closed; commercial-tier evaluation still pending |
| Browser-extension production rollout | #420 closed against dev build; Chrome Web Store distribution = Phase 6 |
| iOS share-sheet production rollout | #421 closed against dev build; App Store rollout = Phase 6 |
| OCR-from-screenshot production rollout | #422 closed against dev build; mobile distribution = Phase 6 |
| Embedding-based domain suggestions | #655 spike complete; production rollout pending Phase 5 budget decision |
| GCIDE GPL legal review for public release | #531 closed against internal review; public release gate revisits before Phase 6 |

---

## Phase 5 Readiness

Phase 4 leaves the project well-positioned for Phase 5 ("Advanced Modes: Deep Practice"):

- All 6 Phase 3 quiz types still operating; quiz-content variety (sense + stem rotation) layered on ✅
- SM-2 SRS persisting per-word state — ready for FSRS migration evaluation ✅
- Multi-source dictionary backbone in place (MW Learner's dev primary + Free Dictionary fallback + open-list CEFR) ✅
- Root-families morphology bundle shipping in production; layered L0/L1/L3 fallback handles out-of-vocab words ✅
- Word discovery v2 similarity engine (CEFR/semantic/root/POS scoring) operational; ready to extend with semantic quiz types ✅
- Dashboard delivering streak, CEFR distribution, 7-day activity ✅
- Word Lists, Domain filter, Domain landing all in production ✅
- CI bug-discipline gates (test-coverage requirement + auto-reopen) ✅
- Capture-friction prototypes (browser extension, iOS share-sheet, OCR) ready for Phase 6 distribution ✅
- Production bug-fix loop proven across two dogfooding waves (May 12 sync wave + May 13–15 UI polish wave) ✅
- Mixed quiz-type sessions (#389) explicitly scoped into Phase 5 as the deferred Phase 4 deliverable ⏳
