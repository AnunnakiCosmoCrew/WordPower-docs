# Phase 2 Audit — Cloud & Enrichment: "Smart Notebook"

> [!abstract]
> Phase 2 is **complete**. All 7 planned epics shipped. 53 Phase 2 issues closed in the app repo, plus 14 additional testing/quality issues and 19 documentation audit issues in the docs repo. The app now has a full backend, cloud sync, dictionary enrichment, Firebase Auth, contract-first API, and a comprehensive testing strategy from unit to performance.

| | |
|---|---|
| **Phase** | Phase 2 — Cloud & Enrichment: "Smart Notebook" |
| **Platform** | Web (Flutter) + backend (Spring Boot) |
| **Duration** | April 17 – April 22, 2026 (6 days) |
| **App repo: planned epics** | 7 |
| **App repo: delivered issues** | 67 (53 phase-2 labeled + 14 testing/quality) |
| **Docs repo: audit issues** | 19 (3 epics + 16 sub-issues, all closed) |
| **Merged PRs** | 65+ |
| **Open Phase 2 issues remaining** | 0 |

---

## Planned Deliverables — All Done

Phase 2 was organized into 7 epics, each decomposed into sub-issues:

### Epic 1: PostgreSQL Schema & Flyway Migrations (#71)

| # | Issue | Lead time |
|---|---|---|
| #79 | Flyway V1 migration — users, user_words, dictionary_cache tables | 9.9h |
| #80 | Schema integration tests with Testcontainers | 10.3h |

### Epic 2: Backend Deployment to Cloud Run (#72)

| # | Issue | Lead time |
|---|---|---|
| #81 | Dockerfile — multi-stage build with slim JRE | 11.2h |
| #82 | Cloud Run config + Neon connection via Secret Manager | 16.5h |
| #83 | GitHub Actions deploy workflow for Cloud Run | 16.9h |

### Epic 3: Firebase Auth Integration (#73)

| # | Issue | Lead time |
|---|---|---|
| #84 | FE: Firebase Auth setup + sign-in screen | 46.3h |
| #85 | FE: Auth state management + route guards | 60.1h |
| #86 | BE: Firebase Admin SDK token validation filter | 17.9h |
| #87 | BE: UserService — auto-create user record on first auth | 18.4h |

### Epic 4: REST API for Word CRUD (#74)

| # | Issue | Lead time |
|---|---|---|
| #88 | BE: Word CRUD endpoints — POST/GET/PUT/DELETE /api/words | 60.6h |
| #89 | BE: Word CRUD integration tests | 61.2h |
| #134 | BE: Support explicit-null semantics in UpdateWordRequest | 10.1h |
| #142 | BE: GET /api/words ?updatedSince= incremental sync param | 41.9h |
| #152 | BE: Expose rich enrichment fields in WordResponse | 0.8h |

### Epic 5: Server-Side Auto-Enrichment Pipeline (#75)

| # | Issue | Lead time |
|---|---|---|
| #90 | BE: Server-side DictionaryService with caching | 66.2h |
| #91 | BE: CEFR level + domain assignment on enrichment | 71.4h |
| #150 | BE: Replace starter wordlist with full CEFR-J + wordfreq tier | 37.5h |

### Epic 6: Cloud Sync (#76)

| # | Issue | Lead time |
|---|---|---|
| #92 | FE: ApiClient with Firebase token injection | 66.8h |
| #93 | FE: Refactor WordRepository — API calls + drift cache | 67.5h |
| #94 | FE: Offline outbox — queue writes and drain on reconnect | 70.0h |

### Epic 7: Word Detail View (#77)

| # | Issue | Lead time |
|---|---|---|
| #68 | Rich enrichment data — synonyms, definitions, antonyms | 11.3h |
| #95 | FE: Word Detail View — enriched card with audio | 83.5h |
| #96 | FE: Editable personal notes + native translation | 83.9h |

---

## Additional Deliverables — Beyond Scope

### Design-First API (OpenAPI)

| # | Issue | Lead time |
|---|---|---|
| #107 | WP: Design-first API development with OpenAPI (epic) | 51.8h |
| #108 | BE: Draft OpenAPI spec (api/openapi.yaml) | 0.8h |
| #109 | BE: Add openapi-generator Gradle plugin for server stubs | 1.5h |
| #110 | FE: Add OpenAPI generator for Dart client SDK | 1.2h |
| #111 | BE: Add Swagger UI + OpenAPI spec validation in CI | 1.9h |

### Contract Testing

| # | Issue | Lead time |
|---|---|---|
| #112 | WP: Contract testing with Spring Cloud Contract (epic) | 51.7h |
| #113 | BE: Provider-side contract tests for word CRUD API | 43.4h |
| #114 | FE: Consumer-side contract tests for Dart client SDK | 43.8h |
| #115 | BE: Spec validation + breaking change detection in CI | 44.2h |

### End-to-End & Performance Testing

| # | Issue | Lead time |
|---|---|---|
| #133 | WP: Add Schemathesis nightly API fuzz testing | 35.0h |
| #144 | WP: API journey tests — multi-step HTTP scenarios | 17.2h |
| #145 | WP: Flutter integration tests on Chrome — pre-deploy E2E | 20.0h |
| #146 | WP: k6 performance testing — nightly latency and throughput | 27.7h |
| #147 | FE: Flutter golden tests — visual regression for key widgets | 27.0h |

### Static Analysis Hardening

| # | Issue | Lead time |
|---|---|---|
| #196 | WP: Harden static analysis to industry best practice (epic) | 0.8h |
| #197 | BE: Add PMD security rules | 0.4h |
| #198 | BE: Add PMD design and complexity rules | 0.5h |
| #199 | BE: Add Checkstyle Javadoc enforcement for public APIs | 0.1h |
| #200 | BE: Add PMD performance rules | 0.1h |
| #201 | BE: Integrate Error Prone compiler plugin | 0.1h |
| #202 | BE: Add ArchUnit architectural boundary tests | 0.7h |

### Test Coverage & Quality Gates (#172)

14 additional issues (not labeled phase-2) focused on reaching coverage enforcement:

| # | Issue |
|---|---|
| #172 | WP: Improve test coverage and code quality gates (epic) |
| #173 | BE: Write missing unit tests for dictionary package |
| #174 | BE: Write missing unit tests for auth package |
| #175 | BE: Improve branch coverage for word package |
| #176 | BE: Flip JaCoCo coverage verification to enforcement mode |
| #177 | FE: Exclude generated code from coverage reporting |
| #178 | FE: Flip coverage threshold to enforcement mode in CI |
| #179 | BE: Write missing unit tests for health package |
| #180 | BE: Write missing unit tests for user package |
| #181 | BE: Add JaCoCo coverage verification for component tests (70%) |
| #182 | BE: Migrate word CRUD journey tests to BDD feature files |
| #183 | BE: Migrate WordsApiIntegrationTest to BDD feature files |
| #184 | BE: Migrate FreeDictionaryServiceIntegrationTest to BDD feature file |
| #185 | BE: Add BDD feature file for user management scenarios |

### Spring Boot 4 Migration

| # | Issue | Lead time |
|---|---|---|
| #131 | WP: Spring Boot 4 migration (unblocks springdoc 3 + related deps) | 47.5h |

### Documentation Audit (docs repo)

19 issues across 3 epics — all closed:

| Epic | Issues | What it covered |
|---|---|---|
| #1 | 7 sub-issues | Accuracy fixes: Oxford API reference, repo context, COOP/COEP claim, data size math, FSRS phase, overdue algorithm |
| #2 | 6 sub-issues | Completeness: lessons learned, app repo timeline, NaN fix, currency standardization, mutation testing, overdue test coverage |
| #3 | 3 sub-issues | New docs: Privacy & GDPR (PRIVACY.md), API documentation (API.md), Deployment & operations guide (OPS.md) |

---

## What Shipped (User-Facing)

- **Firebase Auth** — email/password + Google Sign-In + Apple Sign-In
- **Cloud sync** — offline outbox, background push, delta pull, LWW conflict resolution
- **Auto-enrichment** — definitions, pronunciation (audio + IPA), synonyms, antonyms, examples, CEFR level, semantic domain
- **Word Detail View** — full enriched word card with audio playback, editable personal notes and native translation
- **Incremental sync** — `?updatedSince=` parameter for efficient delta pulls
- **PATCH semantics** — explicit-null support for clearing individual fields

## What Shipped (Engineering Foundation)

- **Contract-first API** — OpenAPI spec as source of truth, generated Spring stubs + Dart client SDK
- **Three-layer contract testing** — spec validation (Spectral + oasdiff) → provider tests (@WebMvcTest) → consumer tests (Dart fixtures)
- **API journey tests** — multi-step HTTP scenarios verifying complete user workflows
- **Flutter integration tests** — real app UI on Chrome as pre-deploy gate
- **Fuzz testing** — Schemathesis nightly with auto-ticketing on failure
- **Performance testing** — k6 nightly with latency/throughput thresholds
- **Golden tests** — visual regression for key widgets
- **Static analysis hardening** — PMD security/design/performance rules, Error Prone, ArchUnit boundaries, Checkstyle Javadoc enforcement
- **Coverage enforcement** — JaCoCo flipped to enforced mode (80% unit / 70% component), lcov enforced in frontend
- **BDD migration** — integration tests migrated to Cucumber feature files
- **Spring Boot 4** — unblocked springdoc 3 and modern dependency chain
- **CEFR-J + wordfreq** — full reference dataset replacing starter wordlist

---

## Deviations from Plan

| Change | Rationale |
|---|---|
| OpenAPI / contract testing added (not in original Phase 2 plan) | API-first development prevents FE/BE spec drift; investment pays off immediately |
| E2E, fuzz, performance, golden testing added (not planned) | Testing infrastructure builds confidence for rapid iteration in Phases 3–6 |
| Static analysis hardened beyond Phase 1 levels | PMD security rules, Error Prone, ArchUnit caught real issues during development |
| Coverage enforcement flipped to hard gates | Enough tests accumulated to enforce without blocking legitimate PRs |
| BDD migration (journey → Cucumber feature files) | Readable test scenarios serve as living documentation of API behavior |
| Spring Boot 4 migration | Required for springdoc 3 compatibility; blocking dependency chain |
| iOS deployment deferred to Phase 3 | Cloud + enrichment + testing infrastructure took priority; iOS prep issues (#97, #98, #99) remain open for Phase 3 |

---

## Cycle Time & Lead Time

> [!info] Definitions
> - **Lead time** = time from issue created to issue closed (includes wait time in backlog)
> - Many issues were batch-created at Phase 2 start and worked sequentially, so lead times include significant wait time

### Overall (Phase 2 app repo — 53 issues)

| Metric | Value |
|---|---|
| **Average** | 35.4 hours |
| **Median** | 35.0 hours |
| **Fastest** | 0.1 hours |
| **Slowest** | 84.0 hours |

### By category

| Category | Count | Median lead time | Notes |
|---|---|---|---|
| **Static analysis hardening** | 7 | 0.4h | Small, focused config changes |
| **OpenAPI tooling** | 4 | 1.4h | One-time setup tasks |
| **Testing infrastructure** | 5 | 27.0h | E2E, fuzz, perf, golden — larger scope |
| **Backend core** (CRUD, auth, enrichment) | 15 | 18.4h | Feature implementation |
| **Frontend core** (auth, sync, UI) | 10 | 67.2h | Longer due to batch-creation lead time |
| **Epics** (parent issues) | 12 | 61.0h | Closed when last sub-issue closed |

> [!tip] Observations
>
> - **Lead time ≠ cycle time** — most issues were batch-created on Apr 17. Frontend issues (#84–#96) show 60–84h lead times because they waited in the backlog while backend was built first. True active work time is significantly shorter.
> - **Static analysis and tooling issues are very fast** — median 0.4h. These are config-level changes with clear success criteria.
> - **Testing infrastructure investment was significant** — 5 issues, median 27h each. This was the biggest unplanned addition but is now a permanent quality floor.
> - **Spring Boot 4 migration (47.5h)** was a single large issue that unblocked multiple dependencies. Worth the investment but consumed nearly 2 days.

---

## Lessons Learned

### What went well

| Observation | Evidence |
|---|---|
| **Contract-first API prevented spec drift** | Zero FE/BE disagreement bugs. The OpenAPI spec + 3-layer contract tests caught mismatches at PR time, never in production. |
| **Testcontainers made integration testing effortless** | Same `./gradlew check` runs identically locally and in CI. Zero "works on my machine" issues. |
| **Local-first architecture proved its value** | Offline outbox + delta sync works correctly. Users never wait for the network. Enrichment arrives silently in the background. |
| **Infrastructure-first from Phase 1 paid off** | CI pipeline, static analysis, and branch protection were already in place. Phase 2 features slotted in without CI rework. |
| **Testing pyramid is comprehensive** | 8 layers from static analysis to performance testing. Nightly fuzz and perf tests catch issues no developer would write a test for. |

### What didn't go well

| Observation | Impact | Root cause |
|---|---|---|
| **iOS deferred** | Phase 2 was supposed to ship "Web + iOS" per PROJECT.md. iOS setup (#97, #98, #99) is still open. | Testing infrastructure and API quality work consumed the time budget. Correct prioritization, but plan should have acknowledged the trade-off earlier. |
| **Lead time metrics are noisy** | Batch-created issues inflate lead times. A 70h lead time on #94 (offline outbox) mostly reflects backlog wait, not 70h of work. | Issues were created all at once on Apr 17 but worked sequentially. Need "In Progress" timestamps for true cycle time. |
| **Scope expanded significantly** | 67 issues delivered vs ~25 planned in the original 7 epics. Testing, contract, and static analysis work was valuable but unplanned. | Same pattern as Phase 1 (scope tripled). The Phase 1 lessons learned recommended time-boxing infra work — this wasn't followed. |

### What to change for Phase 3

1. **Ship iOS.** Phase 3 starts with iOS setup (#97, #98, #99) before any quiz engine work. Don't defer platform again.
2. **Track "In Progress" timestamps.** Move issues to "In Progress" on the board when work actually starts. Report cycle time (active work) separately from lead time (wall clock).
3. **Plan testing work explicitly.** Don't treat testing infrastructure as "bonus" — estimate and schedule it alongside features. Phase 2 showed it's ~30% of total effort.
4. **Batch-create less aggressively.** Create sub-issues when the epic starts, not all at phase kickoff. This produces meaningful lead times.

---

## Open Items Carried to Phase 3

| # | Issue | Notes |
|---|---|---|
| #78 | WP: iOS build setup and deployment pipeline | Epic for iOS platform work |
| #97 | FE: Enable iOS platform + Xcode project settings | Sub-issue of #78 |
| #98 | FE: Firebase iOS config + Apple Sign-In capability | Sub-issue of #78 |
| #99 | FE: Fastlane + TestFlight pipeline + CI workflow | Sub-issue of #78 |
| #154 | feat: Add cross-platform audio playback for mobile (iOS/Android) | Audio playback on native platforms |

---

## Phase 3 Readiness

Phase 2 leaves the project well-positioned for Phase 3 ("Quiz Engine & SRS: Learn for Real"):

- Backend API is fully operational with contract-first development ✅
- Cloud sync is working (outbox, delta pull, LWW) ✅
- Dictionary enrichment populates definitions, CEFR levels, and domains ✅
- CEFR-J + wordfreq reference data is seeded and ready for quiz distractors ✅
- SRS algorithm (SM-2) is documented with overdue catch-up algorithm ✅
- FSRS migration is pinned to Phase 5 with telemetry plan in place ✅
- Testing infrastructure covers all 8 layers of the testing pyramid ✅
- Coverage enforcement is active (80% unit / 70% component) ✅
- iOS setup issues are queued as the first Phase 3 deliverables ✅
- Privacy, API, and operations documentation are in place ✅
