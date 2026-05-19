# Phase 4 Audit — Vocabulary System: "Organized Learning"

> [!warning] Strategy pivot recorded 2026-05-19
> This audit's "Phase 5 Readiness" and "What to change for Phase 5" sections were written assuming the original Phase 5 ("Advanced Modes: Deep Practice") would run next. **That plan was descoped on 2026-05-19** — Phase 5 is now a short *Launch Prep* sprint (Playwright + native `integration_test` + sync-divergence test + Notifications + Oxford decision), and the original Advanced Modes deliverables (FSRS, semantic / contextual / gamified quizzes, CSV import, offline upgrade) moved to a post-launch V2 backlog. The recommendations below still apply — they're discipline gates for *whatever comes next*, not specifically the Advanced-Modes scope. Current roadmap lives in [[PROJECT#12. Milestones]].

> [!abstract]
> Phase 4 is **closed (2026-05-18)**. All 10 originally-scoped deliverables shipped — including mixed quiz-type sessions ([#389](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/389), the last one). The Cambridge primary-source plan was shelved after the licensing spike; Merriam-Webster Learner's stepped in as the dev primary with Free Dictionary as fallback. All 9 epics + all carry-over bugs from the 2026-05-14 smoke test closed. Two workflow improvements landed alongside: a **proof-of-fix gate** on bug PRs (#689) and a hardened **bug-close-audit** workflow (#699 + #703) — both prompted by the same failure mode (passing CI on broken behaviour) that caused four wasted #623 fix attempts.

| | |
|---|---|
| **Phase** | Phase 4 — Vocabulary System: "Organized Learning" |
| **Status** | ✅ **Closed** 2026-05-18 |
| **Platform** | Web (Flutter) + iOS + Android + backend (Spring Boot) |
| **Duration** | May 1 – May 18, 2026 (~18 days; bulk of work May 4–18) |
| **App repo: planned epics** | 10 — all delivered (one re-scoped) |
| **App repo: delivered issues** | 113+ (all phase-4 labeled, all closed) |
| **App repo: merged PRs in window** | 165+ (incl. closure-day workflow + fix PRs) |
| **App repo: commits on main in window** | 147+ |
| **Docs repo: commits in window** | 37+ |
| **Spikes completed** | 11 (Cambridge, MW Learner's, Oxford, browser extension, root-families A/B/C/D + re-spike, embedding-domain) |
| **Open Phase 4 issues at close** | 0 |
| **Docs repo audit issues** | None opened — audit findings folded into ad-hoc commits (same pattern as Phase 3) |

## Closure-day delta (2026-05-18)

The 2026-05-14 smoke test produced 27 carry-over bug issues (#603–#625 plus reopens of #550, #551, #596, #598). Most were resolved over May 14–17. Closure day cleaned up the rest:

- **[#696](https://github.com/AnunnakiCosmoCrew/WordPower-app/pull/696)** — actual fix for [#623](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/623) (`[EXCEPTION] main.dart.js:6630` on every page load). Root cause: `LateInitializationError` on `_GoogleSignInPlugin.autoDetectedClientId`. Four prior speculative fix attempts (#645, #678, #685, #691) all missed the call site because the obfuscated stack pointed at a minified frame. Diagnosed in ~15 minutes by deploying a `flutter build web --profile --source-maps` bundle to a Firebase preview channel.
- **[#624](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/624)** root-caused and closed as won't-fix-for-existing-users. The "Drift falls back to sharedIndexedDb" message turned out NOT to be a COOP/COEP failure (that work all landed correctly). It's the **existing-IndexedDB trap** in `drift_flutter`: pre-existing users have an IDB-backed drift database, and `moveExistingIndexedDbToOpfs` defaults to false for data safety. Fresh installs already get `opfsLocks` (OPFS-based). Acceptable cost vs. migration risk.
- **[#690](https://github.com/AnunnakiCosmoCrew/WordPower-app/pull/690)** — proof-of-fix workflow gate. Bug PRs now must include a Chrome MCP screenshot (frontend) or curl output (backend) demonstrating the user-visible flow works.
- **[#700](https://github.com/AnunnakiCosmoCrew/WordPower-app/pull/700)** + **[#704](https://github.com/AnunnakiCosmoCrew/WordPower-app/pull/704)** — `bug-close-audit` now matches both `#{N}` and `WP-{N}` commit refs, and ignores its own reopens (which had been locking bugs OPEN in a close → audit-reopen → close cycle).

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

### Epic 8: Mixed quiz-type sessions (#389) — ✅ Shipped

Shipped via PR [#545](https://github.com/AnunnakiCosmoCrew/WordPower-app/pull/545) (2026-05-12). MCQ + FITB + flashcards interleave in a single configurable session. The earlier "not shipped" note in this audit was written before the catch-up sprint landed it.

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
| **Mixed quiz-type sessions (#389) shipped late but shipped** | Originally at risk of slipping (time consumed by root-families pipeline + Discover v2). Landed via PR #545 on 2026-05-12 in the catch-up sprint. All originally-scoped Phase 4 deliverables shipped. |
| **CI hardening added (#658, #659, #689, #699, #703)** | Bug-close discipline gap visible since Phase 3 retrospective (#544 "WP-471 was reverted, never replaced"). Five CI gates landed across May 14–18: bug-test-line requirement (#658), bug-close-audit (#659), proof-of-fix screenshot gate (#689), audit accepting `WP-{N}` refs (#699), and audit ignoring its own bot-triggered reopens (#703). The last two were prompted by the close → audit-reopen → close lock that surfaced on closure day. |
| **Profile-build diagnosis pattern adopted** | Four speculative fix attempts on #623 all passed CI without resolving the user-visible exception. Root cause found in ~15 min by deploying `flutter build web --profile --source-maps` to a Firebase preview channel and reading the unobfuscated Dart stack. Same approach diagnosed #624 (existing-IDB trap, not COOP/COEP). Now the recommended path for obfuscated-stack bugs. |
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
| **Mixed quiz-type sessions (#389) shipped in catch-up sprint** | Initially deferred mid-phase. Landed via PR #545 on 2026-05-12 once the root-families pipeline freed up bandwidth. | Time consumed by root-families build pipeline (~28% of issues) and Discover v2 redesign. Phase 4 plan didn't originally budget for either, but the catch-up sprint absorbed the variance. |
| **Capture-friction items closed but not in production** | iOS share-sheet (#421), browser extension v1 (#420), and OCR (#422) all closed against spec docs and unit-level implementation, not against an end-to-end "user installs the extension and saves a word" test. | Distribution channels (App Store, Chrome Web Store) are Phase 6 work; capture-friction features were closed when "the code works on the dev box." Risk: they'll need rework when Phase 6 tries to ship them. |
| **Epic parent issues stayed open after sub-issues closed → resolved on closure day** | The 9 phase-4 epic parents lingered open after their sub-issues closed, until the 2026-05-18 closure pass explicitly closed them with re-test evidence. Phase 3 had the same drift but smaller. | Standard Phase 4 close behaviour is "epic closes when last sub-issue closes" — but GitHub doesn't enforce it, and the team didn't have a checklist. Now codified: PHASE_4_CLOSURE.md doc + audit-workflow improvements. Phase 5 should auto-close epics or use sub-issues with `Closes #parent`. |
| **Close → audit-reopen → close lock** | Eight bugs got stuck OPEN on closure day even though they were smoke-verified. The `bug-close-audit` workflow's "latest reopen" pointer included its own reopens, so any subsequent close found no commit in the (now-smaller) `--since` window. | Diagnosed and fixed on the same day (#703). Audit now ignores reopens triggered by `github-actions[bot]`. Worth a Phase 5 retro item: workflow code needs the same test-and-iterate discipline as feature code. |

### What to change for Phase 5

1. **Pin algorithms in spec, not just UX.** Discover v1 and Spelling v1 (Phase 3) both shipped wrong because the spec described behaviour without naming the scoring/difficulty model. Phase 5's FSRS migration, semantic quizzes, and gamified modes all have hidden algorithmic choices — name them upfront.
2. **Ship integration tests per platform.** Web-only UI bugs (scroll, glyph, scrim, ghost questions) dominated the final 4 days. Phase 5 should add Flutter `integration_test` per platform target — iOS, Android, web — gating the deploy pipeline.
3. **Add sync-divergence tests.** #567/#572 (frontend has 23, backend has 2) need a regression test. Phase 5 should add a property-style test: any sequence of online/offline writes leaves frontend and backend with the same word set.
4. **Close epic parents on sub-issue completion.** Either automate it or add it to the close checklist. 8 stale epic parents skew Phase 4's "open issues" count.
5. **Dogfood content models before shipping their UI.** Domain taxonomy needed a rebuild because no one tried Browse-by-Domain on a real notebook before the UI was built. Phase 5's semantic quizzes (synonym/antonym match, odd-one-out) should dogfood the underlying lexical data on a real notebook before the quiz UI lands.
6. **Profile-build is the diagnostic default for obfuscated-stack bugs.** Four #623 fix attempts shipped without anyone reading the actual call site. After `flutter build web --profile --source-maps` + Firebase preview channel, root cause found in 15 minutes. Add this to the bug-triage runbook — when an exception stack points to `main.dart.js:NNNN`, deploy a profile build before writing any fix code.
7. **Track "In Progress" timestamps.** Carried from Phases 2 and 3 lessons. Phase 4 still doesn't separate cycle time from lead time, and the capture-friction 256.8h numbers continue to mislead.

---

## Open Items Carried to Phase 5

### Originally-scoped deliverables not yet started

_None._ All 10 Phase 4 deliverables shipped before close.

### In-flight bugs at phase close — all resolved 2026-05-18

| # | Issue | Resolution |
|---|---|---|
| #603 | Browse by Domain shows "No domains yet" | ✅ Closed — chips render with counts on prod re-test. |
| #606 | Word detail preview shows wrong POS (`ephemeral` tagged as noun) | ✅ Closed — `obsequious` (and `ephemeral`) tagged `adjective` on re-test. |
| #615 | Escape key does not dismiss modal dialogs | ✅ Closed — Escape dismisses with the dialog's input field focused (standard Material behaviour). |
| #618 | Duplicate snackbar lacks "view existing" affordance | ✅ Closed — `View` action present and navigates correctly. |
| #619 | Word field error state doesn't clear when typing | ✅ Closed — helper + outline reset on first valid keystroke. |
| #620 | Quick Capture: notes field label overlaps typed text | ✅ Closed — Personal notes label correctly floated. |
| #622 | Stale Quick Capture form lingers in DOM on Word detail | ✅ Closed — `read_page interactive` returns no orphaned form on Word detail. |
| #623 | Unhandled Dart exception fires on every page load | ✅ Closed — root-caused as `LateInitializationError` in `google_sign_in_web`; fixed by PR [#696](https://github.com/AnunnakiCosmoCrew/WordPower-app/pull/696) (lazy `late final GoogleSignIn`). |
| #624 | Drift WASM SQLite falls back to sharedIndexedDb | ✅ Closed (won't-fix-for-existing-users) — RCA showed this is the "existing IndexedDB trap" in `drift_flutter`, not a COOP/COEP regression. New installs already get `opfsLocks` automatically. |

### Phase 4 epics — all closed 2026-05-18

| # | Epic | Resolution |
|---|---|---|
| #350 | Multi-source dictionary | Closed as "not planned" — Cambridge shelved post-spike, MW Learner's took the primary slot. Oxford re-evaluation in #513. |
| #383 | Word Lists & Folders | Completed |
| #384 | Domain browsing & filtering | Completed |
| #385 | Root families | Completed (including custom morphology bundle pipeline) |
| #386 | Word discovery | Completed (v2 redesign + clustering fixes) |
| #387 | Dashboard | Completed |
| #389 | Mixed quiz-type sessions | Completed |
| #390 | Quiz-content variety | Completed |
| #391 | Reduce capture friction | Completed (Quick Capture surface); browser-extension / iOS share-sheet / OCR distribution deferred to Phase 6 |

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

## Launch Readiness (originally drafted as "Phase 5 Readiness")

Phase 4 leaves the project well-positioned for what comes next — now scoped as a short Phase 5 *Launch Prep* sprint followed by Phase 6 launch, with the original Advanced Modes scope deferred to V2 (see strategy-pivot callout at the top of this audit and [[PROJECT#12. Milestones]]):

- All 6 Phase 3 quiz types still operating; quiz-content variety (sense + stem rotation) layered on ✅
- SM-2 SRS persisting per-word state — ready for FSRS migration evaluation ✅
- Multi-source dictionary backbone in place (MW Learner's dev primary + Free Dictionary fallback + open-list CEFR) ✅
- Root-families morphology bundle shipping in production; layered L0/L1/L3 fallback handles out-of-vocab words ✅
- Word discovery v2 similarity engine (CEFR/semantic/root/POS scoring) operational; ready to extend with semantic quiz types ✅
- Dashboard delivering streak, CEFR distribution, 7-day activity ✅
- Word Lists, Domain filter, Domain landing all in production ✅
- CI bug-discipline gates (test-coverage requirement + auto-reopen) ✅
- Capture-friction prototypes (browser extension, iOS share-sheet, OCR) ready for Phase 6 distribution ✅
- Production bug-fix loop proven across three dogfooding waves (May 12 sync wave + May 13–15 UI polish wave + May 18 closure smoke) ✅
- Proof-of-fix workflow gate active for all future bug PRs ✅
- Profile-build diagnostic pattern documented for obfuscated-stack bugs ✅
