# Phase 1 Audit — MVP: "Jot & Flip"

> [!abstract]
> Phase 1 is **complete**. All 10 planned issues shipped. 17 additional infrastructure issues were delivered beyond the original scope.

| | |
|---|---|
| **Phase** | Phase 1 — MVP: "Jot & Flip" |
| **Platform** | Web (Flutter) |
| **Duration** | April 15 – April 17, 2026 (3 days) |
| **Planned issues** | 10 |
| **Delivered issues** | 27 (10 planned + 17 additional) |
| **Planned points** | 26 |
| **Delivered points** | 55+ |
| **Merged PRs** | 40 |
| **Commits on main** | 41 |
| **Open issues remaining** | 1 (#68 — moved to Phase 2) |

---

## Planned Deliverables — All Done

| # | Issue | Est | Closed |
|---|---|---|---|
| #1 | Flutter project scaffold, linting, and architecture | 2 | Apr 16 |
| #3 | Frontend GitHub Actions CI pipeline | 3 | Apr 16 |
| #6 | Local database with drift (SQLite) — word storage | 5 | Apr 16 |
| #4 | Quick Capture screen — add a word | 3 | Apr 16 |
| #13 | Word list / My Words browse screen | 3 | Apr 17 |
| #14 | Web deployment pipeline (Firebase Hosting) | 2 | Apr 17 |
| #5 | Free Dictionary API integration | 3 | Apr 17 |
| #8 | Home dashboard screen (minimal) | 2 | Apr 17 |
| #7 | Simple flashcard review screen | 3 | Apr 17 |
| #2 | Spring Boot backend scaffold and CI (Phase 2 head start) | 2 | Apr 16 |

---

## Additional Deliverables — Beyond Scope

### Backend Quality & Static Analysis

| # | Issue | Est |
|---|---|---|
| #21 | Checkstyle (Google style + Spring tweaks) | 2 |
| #22 | SpotBugs + PMD static analysis | 3 |
| #25 | JaCoCo coverage (report-only, target 80%/70%) | 3 |
| #26 | Cucumber BDD component test framework | 5 |

### Frontend Quality

| # | Issue | Est |
|---|---|---|
| #27 | very_good_analysis (free OSS linting) | 2 |
| #28 | Coverage reporting (report-only, target 80%) | 3 |

### Security

| # | Issue | Est |
|---|---|---|
| #23 | Semgrep static analysis workflow | 2 |
| #24 | OWASP dependency-check (monthly) | 2 |
| #44 | Replaced OWASP with Dependabot alerts | 1 |

### CI/CD Infrastructure

| # | Issue | Est |
|---|---|---|
| #29 | Required status checks on main | 1 |
| #41 | CI concurrency cancellation + per-workflow caches | 2 |
| #56 | Fixed push trigger cancellation issue | 1 |
| #62 | Smart CI skipping (dorny/paths-filter) | 2 |

### Other

| # | Issue | Est |
|---|---|---|
| #15 | Root-level .gitignore | 1 |
| #17 | Copilot custom instructions + review rules | 2 |
| #39 | Spring Boot security bump (3.4.1 → 3.4.13) | 1 |
| #53 | App max width centering for wide screens | - |

---

## What Shipped (User-Facing)

- **Quick Capture** — type a word, tap save, done
- **Free Dictionary API enrichment** — auto-fills definition, phonetics, POS, examples
- **Word list / My Words** — browse, search, delete with confirmation
- **Flashcard review** — flip animation, progress indicator, shuffle
- **Home dashboard** — word count, quick actions, recently added words
- **Live deployment** on Firebase Hosting

## What Shipped (Engineering Foundation)

- **Monorepo** — `frontend/` (Flutter) + `backend/` (Spring Boot) with independent CI
- **State management** — Riverpod with code generation
- **Local database** — drift (SQLite) with typed DAOs and migration strategy
- **Abstract dictionary interface** — `DictionaryService` ready for Oxford API swap
- **Full CI pipeline** — analyze, format, test, coverage, static analysis, security scanning
- **Branch protection** — required checks, squash merge only
- **Dependabot** — automated dependency updates

---

## Deviations from Plan

| Change | Rationale |
|---|---|
| Backend scaffold done in Phase 1 (planned for Phase 2) | Agent already working on it; needed for CI pipeline anyway |
| 17 additional CI/quality issues | Engineering foundation investment — pays off across all future phases |
| Oxford API deferred from Phase 2 to Phase 6 | ~$756/yr cost during development; Free Dictionary API is adequate |
| #68 (rich enrichment) moved to Phase 2 | Depends on richer API response parsing; not blocking for MVP |

---

## Open Items Carried to Phase 2

| # | Issue | Notes |
|---|---|---|
| #68 | Rich enrichment data — synonyms, multiple definitions, antonyms | Labeled phase-2, Todo |

---

## Cycle Time & Lead Time

> [!info] Definitions
> - **Lead time** = time from issue created to issue closed (includes wait time in backlog)
> - **Cycle time** = effectively the same here, since most issues were started shortly after creation

### Overall

| Metric | All issues (27) | Phase 1 planned (10) | Infra / bonus (17) |
|---|---|---|---|
| **Average** | 12.2 hours | 24.7 hours | 4.9 hours |
| **Median** | 6.1 hours | 29.6 hours | 3.2 hours |
| **Fastest** | 0.1 hours | 0.2 hours | 0.1 hours |
| **Slowest** | 46.9 hours | 46.9 hours | 17.5 hours |

### Phase 1 planned issues (by lead time)

| # | Issue | Lead time |
|---|---|---|
| #53 | Max width centering | 0.2h |
| #3 | Frontend CI pipeline | 10.8h |
| #1 | Flutter scaffold | 10.9h |
| #6 | Drift local DB | 12.2h |
| #4 | Quick Capture screen | 16.3h |
| #13 | Word list / My Words | 29.6h |
| #14 | Web deployment | 31.3h |
| #5 | Free Dictionary API | 42.5h |
| #8 | Home dashboard | 46.2h |
| #7 | Flashcard review | 46.9h |

### Infrastructure issues (by lead time)

| # | Issue | Lead time |
|---|---|---|
| #17 | Copilot instructions | 0.1h |
| #62 | Smart CI skipping | 0.3h |
| #15 | .gitignore | 0.3h |
| #44 | Dependabot replace | 0.4h |
| #56 | CI trigger fix | 0.6h |
| #23 | Semgrep | 1.5h |
| #28 | Frontend coverage | 1.7h |
| #25 | JaCoCo coverage | 2.1h |
| #21 | Checkstyle | 3.2h |
| #22 | SpotBugs + PMD | 3.6h |
| #26 | Cucumber BDD | 5.3h |
| #27 | very_good_analysis | 5.9h |
| #24 | OWASP dep-check | 6.1h |
| #29 | Required status checks | 6.5h |
| #2 | Spring Boot scaffold | 10.8h |
| #41 | CI optimization | 17.1h |
| #39 | Spring Boot bump | 17.5h |

> [!tip] Observations
>
> - **Infra issues are fast** — median 3.2h. Mostly CI/tooling config with small, focused PRs.
> - **Feature issues take longer** — median 29.6h. Expected: they involve UI, state management, tests, and iteration.
> - **Longer lead times on #5, #7, #8** reflect backlog wait (created Apr 15, closed Apr 17) not active work time. True cycle time is shorter.
> - **Phase 2 baseline:** expect feature issues to average ~1-2 days lead time based on Phase 1 velocity.

---

## Lessons Learned

### What went well

| Observation | Evidence |
|---|---|
| **Infrastructure-first paid off** | 17 unplanned infra issues (CI, static analysis, coverage, security scanning) created a foundation that accelerated every feature issue. Checkstyle, PMD, SpotBugs, Semgrep, and Dependabot now gate every PR with zero per-issue setup cost. |
| **Abstract interfaces from day one** | `DictionaryService` abstraction (WP-5) means Oxford API swap in Phase 6 is a single class change. This pattern costs ~10 minutes upfront and saves weeks later. |
| **Fast infra velocity** | Infrastructure issues had a median lead time of 3.2 hours — focused, well-scoped PRs with clear success criteria. |
| **CI smart-skipping** | `dorny/paths-filter` (WP-62) means frontend-only PRs skip backend CI entirely. Wall-clock CI time stays under 90 seconds regardless of repo growth. |

### What didn't go well

| Observation | Impact | Root cause |
|---|---|---|
| **Scope nearly tripled** | 27 issues delivered vs 10 planned (2.7×). While the extra work was valuable, it was unplanned — no conscious trade-off decision was made upfront. | Opportunistic infrastructure work during feature implementation — "while I'm here, let me also add..." |
| **Feature lead times inflated by backlog wait** | #5 (Dictionary API) shows 42.5h lead time, but much of that was sitting in the backlog, not active work. Lead time ≠ cycle time here. | Issues were created early but worked sequentially. True cycle time metrics would be more useful. |
| **No estimation for bonus issues** | #53 (max width centering) has no estimate. Infra issues were estimated after the fact, not before. | Rapid execution without pausing to estimate — acceptable in a 3-day sprint, but unsustainable. |

### What to change for Phase 2

1. **Time-box infrastructure work.** Dedicate explicit issues for infra before starting features — don't let infra emerge organically during feature work.
2. **Track cycle time separately from lead time.** Add "In Progress" timestamps on the project board to distinguish wait time from active work time.
3. **Estimate before starting.** Every issue gets a Fibonacci estimate before moving to "In Progress" — no exceptions, including bug fixes (which are estimate 0).
4. **Scope control.** If unplanned work exceeds 50% of planned points mid-phase, pause and re-plan rather than absorbing it silently.

---

## Phase 2 Readiness

Phase 1 leaves the project well-positioned for Phase 2 ("Cloud & Enrichment"):

- Backend is already scaffolded with CI, static analysis, and test framework ✅
- `DictionaryService` abstraction is in place for future Oxford swap ✅
- drift schema is designed to mirror PostgreSQL for cloud sync ✅
- CI/quality infrastructure covers both frontend and backend ✅
- Firebase Hosting is live (Firebase Auth is the natural next step) ✅
