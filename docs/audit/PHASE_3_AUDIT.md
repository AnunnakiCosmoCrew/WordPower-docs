# Phase 3 Audit — Quiz Engine & SRS: "Learn for Real"

> [!abstract]
> Phase 3 is **complete**. All 4 planned epics shipped: pluggable quiz engine, six core quiz types (flashcard, MCQ, spelling, listening, matching, fill-in-the-blank), SM-2 spaced repetition, and the daily review queue. iOS shipped (carried over from Phase 2) and Android was added opportunistically. 70 phase-3 issues closed in the app repo, 88 PRs merged. Zero open phase-3 issues remain.

| | |
|---|---|
| **Phase** | Phase 3 — Quiz Engine & SRS: "Learn for Real" |
| **Platform** | Web (Flutter) + iOS + Android (added beyond plan) + backend (Spring Boot) |
| **Duration** | April 23 – May 4, 2026 (~12 days) |
| **App repo: planned epics** | 4 (quiz engine, core quiz types, SM-2, review queue) + 1 carryover (iOS) |
| **App repo: delivered issues** | 70 (all phase-3 labeled, all closed) |
| **Merged PRs** | 88 |
| **Open Phase 3 issues remaining** | 0 |
| **Docs repo audit issues** | None opened — audit findings folded into ad-hoc commits |

---

## Planned Deliverables — All Done

### Epic 0 (carried from Phase 2): iOS build setup and deployment pipeline (#78)

| # | Issue | Lead time |
|---|---|---|
| #97 | FE: Enable iOS platform + Xcode project settings | 234.6h |
| #98 | FE: Firebase iOS config + Apple Sign-In capability | 379.0h |
| #99 | FE: Fastlane + TestFlight pipeline + CI workflow | 382.7h |
| #154 | feat: Add cross-platform audio playback for mobile (iOS/Android) | 168.0h |

> Lead times include the Phase 2 backlog wait — these were created Apr 17 but iOS work didn't start until Phase 3 kickoff.

### Epic 1: Quiz engine architecture and framework (#220, #221)

| # | Issue | Lead time |
|---|---|---|
| #225 | BE: Quiz domain model and database schema | 4.1h |
| #226 | BE: Quiz API design (OpenAPI spec + endpoints) | 45.2h |
| #227 | BE: Distractor service quality rules (Phase A — in-collection) | 74.8h |
| #228 | FE: Quiz engine state management (Riverpod) | 93.2h |
| #229 | FE: Quiz session UI framework (pluggable widget system) | 96.3h |
| #230 | FE: Quiz result and summary screen | 97.2h |
| #282 | BE: Lexical-knowledge distractor strategies (WordNet + Roget's) | 143.1h |

### Epic 2: Core quiz types (#222)

#### Flashcard (#231)
| # | Issue | Lead time |
|---|---|---|
| #232 | BE: Flashcard question generation | 21.2h |
| #233 | FE: Flashcard flip UI with self-rating | 127.3h |

#### Multiple choice (#234)
| # | Issue | Lead time |
|---|---|---|
| #235 | BE: MCQ generation with smart distractors | 22.3h |
| #236 | FE: Multiple choice quiz UI | 127.7h |

#### Spelling (#237)
| # | Issue | Lead time |
|---|---|---|
| #238 | BE: Spelling question generation | 91.9h |
| #239 | FE: Spelling quiz UI with audio and text input | 141.2h |

#### Listening (#240)
| # | Issue | Lead time |
|---|---|---|
| #241 | BE: Listening question generation | 171.3h |
| #242 | FE: Listening quiz UI with audio playback | 171.6h |

#### Matching (#243)
| # | Issue | Lead time |
|---|---|---|
| #244 | BE: Matching set generation (word-definition pairs) | 143.0h |
| #245 | FE: Matching quiz UI (tap-to-match) | 143.0h |

#### Fill-in-the-blank (#246)
| # | Issue | Lead time |
|---|---|---|
| #247 | BE: FITB question generation from example sentences | 75.3h |
| #248 | FE: Fill-in-the-blank quiz UI | 128.3h |

### Epic 3: SM-2 spaced repetition system (#223)

| # | Issue | Lead time |
|---|---|---|
| #249 | BE: SM-2 algorithm implementation | 20.6h |
| #250 | BE: SRS database migration (add SRS fields to user_words) | 24.4h |
| #251 | BE: Review result recording API | 25.8h |
| #252 | FE: SRS state display on word detail view | 122.8h |
| #253 | FE: Review rating collection (auto-infer + flashcard self-rate) | 124.3h |

### Epic 4: Daily review queue (#224)

| # | Issue | Lead time |
|---|---|---|
| #254 | BE: Review queue generation and API endpoint | 195.3h |
| #255 | FE: Review queue screen and dashboard widget | 195.9h |
| #256 | FE: Review session flow (mixed quiz types from due words) | 199.7h |
| #257 | FE: Review completion summary screen | 201.0h |

---

## Additional Deliverables — Beyond Scope

### Android platform (opportunistic add)

| # | Issue | Lead time |
|---|---|---|
| #285 | FE: Enable Android platform + Gradle/manifest setup | 0.3h |

> Phase 2 plan called for iOS only in Phase 3. Android was enabled in a single low-effort change once cross-platform audio (#154) was working.

### Production bug fixes (post-deploy)

iOS + Android cutover surfaced configuration and content-correctness bugs that were patched in flight:

| # | Issue | Lead time |
|---|---|---|
| #304 | FE deploy: missing `--dart-define` routes prod traffic to localhost | 0.2h |
| #306 | BE deploy: Cloud Run manifests missing `CORS_ALLOWED_ORIGINS` — prod browser blocked | 11.2h |
| #308 | BE: word capture leaves `user_words.definition` NULL — quiz can't generate questions | 0.5h |
| #310 | BE: scheduled backfill of historical `user_words.definition` NULL rows | 0.5h |
| #312 | FE: Return to dashboard from quiz result screen leaves a blank page | 1.7h |
| #315 | BE: expose `wordId` on QuizQuestionResponse | 0.2h |
| #320 | FE: Surface server `Problem.detail` on quiz-start errors | 12.7h |
| #322 | FE: Quiz start fails on backend cold start (warm up + bump POST timeout) | 0.3h |
| #348 | [P0] Ingest-time content-safety filter for `dictionary_cache` example sentences | 1.4h |

### Quiz quality and content fixes

Issues found during dogfooding the quiz engine on real notebooks:

| # | Issue | Lead time |
|---|---|---|
| #335 | BE: Random candidate-pool sampling to fix older-word lockout | 29.7h |
| #338 | BE: Small-collection distractor fallback to dictionary cache | 44.9h |
| #349 | FITB quality fixes: random stem selection + a/an article placeholder | 14.6h |
| #351 | Drop listening TYPE mode — spelling already covers hear-and-type | 0.5h |
| #362 | BE: FITB morphological-form matching for example-sentence eligibility | 12.2h |
| #367 | BE: Mixed-type review-queue quiz sessions (review_queue source + mixed quiz type) | 1.0h |
| #369 | BE: Read CEFR from DictionaryEntry instead of re-classifying in distractor service | 21.7h |

### Spelling quiz redesign (assisted-production model)

The original spelling quiz exposed only an audio prompt; users found it too hard with no scaffolding. Redesigned mid-phase to show definition + blanked example, with an opt-in hint button gated by SRS rating downgrade:

| # | Issue | Lead time |
|---|---|---|
| #327 | BE: Spelling generator emits definition + blanked example | 2.3h |
| #328 | BE: Add `hintsUsed` to QuizAnswer + accept on submit | 2.8h |
| #329 | BE: Spelling SRS rating inference (assisted production + hint downgrade) | 3.5h |
| #330 | FE: Spelling session UI renders definition + blanked example | 8.3h |
| #331 | FE: Spelling hint button with cap enforcement | 9.1h |
| #332 | BE+FE: HINT_USED telemetry event | 10.0h |

### Report-this-sentence flow (#359)

User-facing escape hatch for bad example sentences in FITB / Spelling / Flashcard:

| # | Issue | Lead time |
|---|---|---|
| #373 | BE: Report-this-sentence flow — table, endpoint, suppression | 13.9h |
| #374 | FE: Report-this-sentence affordance on FITB / Spelling / Flashcard | 17.4h |

---

## What Shipped (User-Facing)

- **iOS app** — Apple Sign-In, Fastlane + TestFlight, full feature parity with web
- **Android app** — opportunistic add, full feature parity
- **Native audio playback** — iOS/Android cross-platform audio for word pronunciation
- **6 quiz types** — flashcard (with SRS self-rate), multiple choice, spelling (assisted production), listening, matching, fill-in-the-blank
- **SM-2 spaced repetition** — per-word familiarity, intervals, next-review dates surfaced on word detail
- **Daily review queue** — auto-generated from due words, mixed quiz types per session, completion summary
- **Smart distractors** — multi-strategy (in-collection → WordNet/Roget's → dictionary cache) with quality rules and small-collection fallback
- **Spelling assistance** — definition + blanked example shown, opt-in hint button with SRS rating downgrade
- **Report-this-sentence** — user-facing affordance to flag bad example sentences across FITB/Spelling/Flashcard
- **Quiz error UX** — server `Problem.detail` surfaced on quiz-start errors, cold-start warmup

## What Shipped (Engineering Foundation)

- **Pluggable quiz engine** — Riverpod state management, pluggable widget system, generators per quiz type behind a uniform contract
- **Quiz domain model** — `quiz_session`, `quiz_question`, `quiz_answer` schema with `wordId` exposure for SRS linkage
- **OpenAPI-first quiz API** — full spec coverage extending the Phase 2 contract-first pattern
- **Layered distractor chain** — in-collection → WordNet siblings → Roget's categories → dictionary cache; CEFR/POS/length signals; random pool sampling to prevent older-word lockout
- **SRS persistence** — Flyway migration adding `easeFactor`, `interval`, `repetitions`, `nextReviewAt` to `user_words`
- **Review queue generator** — server-side due-word aggregation feeding mixed-type review sessions
- **Content-safety ingest filter** — applied at `dictionary_cache` write time to prevent unsafe example sentences from ever reaching quiz generators
- **HINT_USED telemetry** — for measuring hint usage during the spelling assisted-production rollout

---

## Deviations from Plan

| Change | Rationale |
|---|---|
| Android added (not planned for Phase 3) | Cross-platform audio (#154) made Android essentially free — single Gradle/manifest setup (#285, 0.3h) |
| Spelling quiz redesigned mid-phase | First version shipped audio-only and was unusably hard; pivoted to assisted-production with hints. Six new issues (#327–#332) added |
| Listening TYPE mode dropped (#351) | Overlapped with spelling's audio-first variant; collapsed to one quiz type |
| Lexical-knowledge distractors built (#282) | Original plan was in-collection only; small notebooks (~20 words) couldn't generate quality MCQs without WordNet/Roget's lexical fallback |
| Report-this-sentence flow added (#359, #373, #374) | Dictionary cache contains noisy example sentences; user-facing flag + suppression was needed before scaling to more users |
| Many in-flight production bugs | iOS/Android cutover and quiz dogfooding surfaced ~9 production issues — all fixed within hours, but not pre-planned |
| Random candidate-pool sampling (#335) | Older words were locked out of quiz selection; fixed with random sampling. Real fix (least-recently-quizzed ordering) deferred to Phase 4 |

---

## Cycle Time & Lead Time

> [!info] Definitions
> - **Lead time** = time from issue created to issue closed (includes wait time in backlog)
> - 5 issues were carried over from Phase 2's batch-creation (#78, #97, #98, #99, #154) and inflate the overall lead time

### Overall (all 70 phase-3 issues)

| Metric | Value |
|---|---|
| **Average** | 90.9 hours |
| **Median** | 75.3 hours |
| **Fastest** | 0.2 hours |
| **Slowest** | 396.2 hours (#78 iOS epic, created Apr 17) |

### Excluding Phase 2 carryover (65 issues created during Phase 3)

| Metric | Value |
|---|---|
| **Average** | 73.9 hours |
| **Median** | 44.9 hours |
| **Fastest** | 0.2 hours |
| **Slowest** | 201.4 hours (#224 review queue epic) |

### By category

| Category | Count | Median lead time | Notes |
|---|---|---|---|
| **Production bug fixes** | 9 | 0.5h | Found and fixed within hours of deploy |
| **Quiz quality fixes** | 7 | 14.6h | Distractor and FITB content correctness |
| **Spelling redesign** | 6 | 5.7h | Tightly scoped UX pivot |
| **iOS/Android setup** | 6 | 201.0h | Lead time inflated by Phase 2 batch creation |
| **Quiz engine architecture** | 7 | 93.2h | Foundation work, ran in parallel with FE |
| **Per-quiz-type BE generators** | 6 | 83.6h | Flashcard / MCQ / Spelling / Listening / Matching / FITB |
| **Per-quiz-type FE UIs** | 6 | 134.8h | Slightly behind BE generators throughout |
| **SM-2 SRS implementation** | 5 | 25.8h | Compact and well-defined |
| **Review queue** | 4 | 197.8h | Last to land — depended on all quiz types being ready |
| **Lexical distractors** | 1 | 143.1h | Single large issue spanning WordNet + Roget's |
| **Report-this-sentence** | 2 | 15.7h | Quick BE + FE pair after dogfooding feedback |

> [!tip] Observations
>
> - **Median dropped from 35h (Phase 2) to 45h (Phase 3 fresh issues)** — comparable cadence despite shipping iOS, Android, and 6 quiz types in 12 days
> - **Production bug fixes were extremely fast** — median 0.5h. Issues were filed, fixed, deployed within the same day. Cloud sync from Phase 2 made hot-fixes safe
> - **FE quiz UIs trailed BE generators by ~50h consistently** — BE generators were small and clear, FE pluggable widgets had more design ambiguity
> - **Review queue (epic 4) closed last** — all sub-issues ~195–201h because the queue wraps the other quiz types and could only be exercised once they all worked

---

## Lessons Learned

### What went well

| Observation | Evidence |
|---|---|
| **Pluggable quiz engine paid off immediately** | All 6 quiz types reused the same Riverpod state machine and session UI framework. Adding a new quiz type was ~2 issues (BE generator + FE widget), not a system rewrite |
| **OpenAPI-first extended naturally to quizzes** | The Phase 2 contract-first pattern carried over with zero rework. Quiz API spec + generated stubs landed in #226 in 45h |
| **In-flight bug response was fast** | 9 production bugs from cutover found and fixed in median 0.5h. Cloud Run + branch-protection PR flow allowed safe hot-fixing without process drag |
| **Spelling redesign pivot was cheap** | Catching the "audio-only is too hard" UX problem mid-phase and pivoting to assisted-production cost only 6 issues (~36h total) and didn't slip the phase |
| **Lexical distractors unlocked small notebooks** | WordNet + Roget's fallback (#282, #338) made MCQs viable for users with <50 words — before this, distractor pools were too thin |

### What didn't go well

| Observation | Impact | Root cause |
|---|---|---|
| **Spelling shipped wrong the first time** | One full quiz type had to be redesigned mid-phase (#327–#332). Cost ~36h of unplanned work | Spec didn't pin down the difficulty model. "Hear audio, type word" sounded fine on paper but was unusable in practice. No prototype tested before BE+FE work started |
| **Older-word lockout in candidate pool (#335)** | Distractor selection biased toward newer words; older words were never picked. Found by user complaint, not test | Selection logic used insertion-order traversal with a cap. Should have been caught by a property test on selection fairness |
| **Example-sentence quality varied wildly** | Forced #348 (content-safety filter), #349 (FITB stem selection), #359 (report-this-sentence flow), #362 (morphological matching) | Free Dictionary example sentences are unfiltered. Phase 4's Cambridge migration targets the root cause |
| **CEFR re-classification in distractor service (#369)** | Distractor service re-derived CEFR per request from word forms instead of reading the cached `DictionaryEntry.cefrLevel` from Phase 2's enrichment | Knowledge gap between team members on what was already in the cache. Cost a 21.7h refactor |
| **Phase 2 carryover inflated lead-time metrics again** | 5 iOS issues created Apr 17 closed at 168–396h — but this is mostly backlog wait, not active work | Same root cause as Phase 2 lessons learned (item 4): "batch-create less aggressively." Still not fully fixed — though Phase 3 fresh issues were created closer to start time |

### What to change for Phase 4

1. **Prototype before specifying.** For any quiz type or interaction model, build a 30-min throwaway before opening BE+FE issues. The spelling redesign would have been avoided.
2. **Property tests for selection logic.** Distractor and candidate-pool selection must have property tests (fairness, coverage, age distribution). The older-word lockout was a one-line bug that survived because no test exercised the distribution.
3. **Single source of truth for enrichment fields.** When a value lives in `DictionaryEntry`, downstream services must read it — not re-derive. Add an ArchUnit rule forbidding CEFR/POS classification outside the enrichment package.
4. **Track "In Progress" timestamps (carried from Phase 2).** Phase 3 still doesn't separate cycle time from lead time. This was a Phase 2 action item that didn't land.
5. **Cambridge migration is high-leverage.** Many Phase 3 quality fixes (#348, #349, #359, #362) trace back to Free Dictionary example-sentence quality. The Phase 4 Cambridge primary-source migration targets the root cause.

---

## Open Items Carried to Phase 4

No phase-3 issues are open. Phase 4 work is already scoped (#350 Cambridge migration, #394–#422 vocabulary system) and tracked separately.

The following Phase 3 deferrals are explicitly handed to Phase 4:

| Item | Phase 4 ticket | Notes |
|---|---|---|
| Least-recently-quizzed candidate ordering | (Phase 4 plan) | Replaces the random-sampling fix in #335 with a real `lastQuizzedAt` column |
| Mixed quiz-type sessions outside the review queue | (Phase 4 plan) | #367 added it for review queue only; ad-hoc quiz sessions still single-type |
| Quiz-content variety (sense rotation, FITB stem rotation) | #411, #412, #413 | Counter encoding-specificity memorisation |
| Cambridge as primary dictionary source | #350 | Targets root cause of example-sentence quality issues |

---

## Phase 4 Readiness

Phase 3 leaves the project well-positioned for Phase 4 ("Vocabulary System: Organized Learning"):

- iOS and Android shipped with full feature parity ✅
- All 6 core quiz types working in production ✅
- SM-2 SRS persisting per-word state and driving the daily review queue ✅
- Layered distractor chain (in-collection → WordNet → Roget's → cache) operational ✅
- Quiz API is OpenAPI-first with generated client SDK ✅
- Production bug response loop is proven (cloud sync + branch-protected hot-fixes) ✅
- Cambridge Dictionary spike (#353) is complete; migration epic #350 is scoped ✅
- Word lists, dashboard, root families, word discovery, and capture-friction tickets are all open and grouped under Phase 4 epics ✅
