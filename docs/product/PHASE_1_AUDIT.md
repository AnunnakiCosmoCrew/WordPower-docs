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
| Oxford API deferred from Phase 2 to Phase 6 | £600/yr cost during development; Free Dictionary API is adequate |
| #68 (rich enrichment) moved to Phase 2 | Depends on richer API response parsing; not blocking for MVP |

---

## Open Items Carried to Phase 2

| # | Issue | Notes |
|---|---|---|
| #68 | Rich enrichment data — synonyms, multiple definitions, antonyms | Labeled phase-2, Todo |

---

## Phase 2 Readiness

Phase 1 leaves the project well-positioned for Phase 2 ("Cloud & Enrichment"):

- Backend is already scaffolded with CI, static analysis, and test framework ✅
- `DictionaryService` abstraction is in place for future Oxford swap ✅
- drift schema is designed to mirror PostgreSQL for cloud sync ✅
- CI/quality infrastructure covers both frontend and backend ✅
- Firebase Hosting is live (Firebase Auth is the natural next step) ✅
