# Architecture — WordPower

> [!abstract] Summary
> WordPower is a local-first personal vocabulary app built with Flutter (frontend) and Spring Boot (backend). Users collect words on-device with zero latency, the backend enriches them via dictionary APIs and serves as the sync bridge between devices. This document is the single map of how the system fits together — component boundaries, data flow, deployment, security, and the key trade-offs behind each decision.

Related: [[LOCAL_FIRST_ARCHITECTURE]] | [[BROWSER_DATABASE_INTERNALS]] | [[TESTING_STRATEGY]] | [[PROJECT]]

---

## Table of Contents

1. [[#1. System Context]]
2. [[#2. High-Level Component Diagram]]
3. [[#3. Data Flow]]
4. [[#4. Backend Architecture]]
5. [[#5. Frontend Architecture]]
6. [[#6. Deployment Topology]]
7. [[#7. Security Model]]
8. [[#8. Cross-Cutting Concerns]]
9. [[#9. Key Technology Decisions]]
10. [[#10. Evolution Path]]

---

## 1. System Context

WordPower is a **local-first lite** vocabulary notebook. The user interacts with the Flutter app, which reads and writes locally first. The Spring Boot API acts as a sync bridge and enrichment engine — it is never on the critical path of a user action.

```mermaid
C4Context
    title System Context — WordPower

    Person(user, "Learner", "Collects English words<br/>and reviews them")

    System(wp, "WordPower", "Flutter app + Spring Boot API<br/>+ PostgreSQL")

    System_Ext(firebase, "Firebase Auth", "Authentication<br/>(email, Google, Apple)")
    System_Ext(dictionary, "Dictionary API", "Free Dictionary (Phase 1-5)<br/>Oxford API (Phase 6)")
    System_Ext(gcp, "Google Cloud Platform", "Cloud Run hosting")
    System_Ext(neon, "Neon", "Serverless PostgreSQL")

    Rel(user, wp, "Collects words, reviews, quizzes")
    Rel(wp, firebase, "Authenticates users")
    Rel(wp, dictionary, "Fetches definitions,<br/>pronunciation, examples")
    Rel(wp, neon, "Persists user data<br/>+ dictionary cache")
    Rel(wp, gcp, "Hosts backend API")
```

### System boundaries

| Inside WordPower | Outside WordPower (external dependencies) |
|---|---|
| Flutter web/iOS app | Firebase Auth (identity provider) |
| Spring Boot REST API | Neon (managed PostgreSQL) |
| drift/SQLite local database | Dictionary API (Free Dictionary / Oxford) |
| Sync engine (outbox + delta pull) | Google Cloud Platform (Cloud Run) |
| Enrichment pipeline | Apple App Store / Firebase Hosting (distribution) |
| SRS scheduling algorithm | |

**Design principle:** external dependencies are abstracted behind interfaces. The `DictionaryService` interface means swapping Free Dictionary for Oxford is a single implementation class change. Firebase Auth is consumed via a Spring Security filter — replacing it means swapping one filter, not rewriting auth logic.

---

## 2. High-Level Component Diagram

```mermaid
flowchart TB
    subgraph Client["Flutter App (Web / iOS)"]
        UI["UI Layer<br/>(Screens + Widgets)"]
        RP["State Management<br/>(Riverpod)"]
        DS["Data Layer<br/>(Repositories)"]
        DR["drift<br/>(SQLite)"]
        OB["Sync Outbox"]
    end

    subgraph Server["Spring Boot API (Cloud Run)"]
        WEB["Web Layer<br/>(Controllers)"]
        APP["Application Layer<br/>(Services)"]
        DOM["Domain Layer<br/>(Entities, SRS Logic)"]
        PER["Persistence Layer<br/>(Repositories)"]
    end

    subgraph External["External Services"]
        FA["Firebase Auth"]
        PG[("PostgreSQL<br/>(Neon)")]
        DICT["Dictionary API"]
    end

    UI --> RP --> DS
    DS --> DR
    DS --> OB

    OB -.->|"Background sync<br/>(push local changes)"| WEB
    DS -.->|"Delta pull<br/>(fetch remote changes)"| WEB

    WEB --> APP --> DOM
    APP --> PER
    PER --> PG

    APP -->|"Enrichment"| DICT
    WEB -->|"JWT validation"| FA

    style Client fill:#e8f4fd,stroke:#1a73e8
    style Server fill:#fef3e8,stroke:#e8a01a
    style External fill:#f0f0f0,stroke:#999
```

### Component responsibilities

| Component | Responsibility | Does NOT do |
|---|---|---|
| **UI Layer** | Renders screens, handles user input, animations | Business logic, direct DB access |
| **Riverpod** | State management, dependency injection, caching | Network calls directly (delegates to repositories) |
| **Data Layer** | Coordinates local reads/writes and sync | UI rendering, SRS calculation |
| **drift (SQLite)** | Local persistence, typed queries, migrations | Network, sync decisions |
| **Sync Outbox** | Queues unsynced writes, drains when online | Conflict resolution (server handles this) |
| **Web Layer** | HTTP routing, request/response mapping, validation | Business logic, direct DB queries |
| **Application Layer** | Orchestrates use cases, triggers enrichment | HTTP concerns, SQL |
| **Domain Layer** | SRS algorithm, CEFR assignment, domain tagging | Framework dependencies |
| **Persistence Layer** | PostgreSQL access via Spring Data JPA | Business rules |

---

## 3. Data Flow

### The core loop: Collect → Enrich → Learn → Review

```mermaid
flowchart LR
    A["User types<br/>'ubiquitous'"] --> B["Save to<br/>local SQLite<br/>(instant)"]
    B --> C["Queue in<br/>sync outbox"]
    C -.->|"Background"| D["POST /api/words<br/>(Spring Boot)"]
    D --> E["Save to<br/>PostgreSQL"]
    E --> F["Trigger<br/>enrichment"]
    F --> G["Dictionary API<br/>→ definition, IPA,<br/>audio, CEFR, domain"]
    G --> H["UPDATE word<br/>with enrichment"]
    H -.->|"Next sync pull"| I["Local DB updated<br/>with enriched data"]
    I --> J["Word appears in<br/>quiz / flashcard"]
    J --> K["User rates:<br/>Easy / Good / Hard"]
    K --> L["SRS updates<br/>next review date"]
    L -.-> J
```

### Request flow: saving a word (Phase 2+)

| Step | Where | What happens | Latency |
|---|---|---|---|
| 1 | Flutter app | User taps Save | 0ms |
| 2 | drift (SQLite) | `INSERT INTO user_words` | ~5ms |
| 3 | UI | "Saved!" shown to user | ~5ms total |
| 4 | Sync outbox | Write queued for background push | ~1ms |
| 5 | Spring Boot | `POST /api/words` (when online) | ~100ms |
| 6 | PostgreSQL | Word persisted server-side | ~10ms |
| 7 | Enrichment | Dictionary API lookup (or cache hit) | ~200ms (miss) / ~5ms (hit) |
| 8 | PostgreSQL | Enrichment data stored | ~10ms |
| 9 | Flutter app | Next delta pull picks up enrichment | Background |

**Key insight:** the user sees "Saved!" at step 3 (~5ms). Steps 5-9 happen invisibly in the background. The network is never on the critical path.

> [!info] Deep dive
> For the full sync protocol (outbox, delta sync, LWW conflict resolution), see [[LOCAL_FIRST_ARCHITECTURE#5. How the Sync Works]].

### Dictionary caching flow

The dictionary cache is **shared across all users**. Each English word is fetched from the external API exactly once.

```mermaid
flowchart LR
    REQ["Enrichment<br/>request"] --> CHECK{"dictionary_cache<br/>has word?"}
    CHECK -->|"HIT"| RET["Return cached<br/>data (~5ms)"]
    CHECK -->|"MISS"| FETCH["Call Dictionary<br/>API (~200ms)"]
    FETCH --> STORE["Save to<br/>dictionary_cache"]
    STORE --> RET
```

After a few months, the cache covers nearly every word users will ever search. Dictionary API costs stay flat regardless of user count (particularly important once Oxford API replaces Free Dictionary in Phase 6).

---

## 4. Backend Architecture

The Spring Boot backend follows a **layered architecture** with strict dependency rules enforced by ArchUnit at build time.

### Package structure

```
com.wordpower.api
├── web/                  ← Controllers, DTOs, request/response mapping
│   ├── WordsController
│   ├── QuizController
│   └── dto/
├── application/          ← Services, use-case orchestration
│   ├── WordService
│   ├── EnrichmentService
│   ├── QuizService
│   └── SrsService
├── domain/               ← Entities, value objects, domain logic
│   ├── UserWord
│   ├── DictionaryEntry
│   ├── SrsCalculator
│   └── CefrAssigner
├── persistence/          ← Spring Data JPA repositories
│   ├── WordRepository
│   ├── DictionaryCacheRepository
│   └── UserRepository
├── infrastructure/       ← External integrations
│   ├── dictionary/       ← DictionaryService interface + implementations
│   ├── firebase/         ← Firebase Auth filter
│   └── config/           ← Spring configuration
└── gen/                  ← Generated OpenAPI stubs (excluded from analysis)
```

### Layer dependency rules

```mermaid
flowchart TB
    WEB["web/"] -->|"can access"| APP["application/"]
    APP -->|"can access"| DOM["domain/"]
    APP -->|"can access"| PER["persistence/"]
    APP -->|"can access"| INFRA["infrastructure/"]
    DOM -.->|"NO dependency on"| WEB
    DOM -.->|"NO dependency on"| PER
    DOM -.->|"NO dependency on"| INFRA

    style DOM fill:#d4edda,stroke:#28a745
```

| Rule | Enforced by | Why |
|---|---|---|
| Controllers access services only (not repositories) | ArchUnit | Prevents bypassing business logic |
| Domain has no Spring/framework imports | ArchUnit | Domain stays portable and testable |
| No circular package dependencies | ArchUnit | Packages form a DAG |
| Services may access repositories and other services | Convention | Orchestration layer needs both |

> [!info] ArchUnit details
> See [[TESTING_STRATEGY#ArchUnit — Architectural boundary enforcement (Level 3: bytecode + structural analysis)]] for the test implementation and enforcement policy.

### Feature modules

The backend organizes around business capabilities:

| Module | Responsibility |
|---|---|
| **word** | CRUD for user words, personal notes, word lists |
| **dictionary** | Dictionary API integration, caching, enrichment pipeline |
| **auth** | Firebase JWT validation, user identity, security filter |
| **user** | User profile, preferences, subscription status |
| **quiz** | Quiz session management, question generation, answer scoring |
| **srs** | SM-2 scheduling, interval calculation, review queue generation |

### API design

- **Contract-first:** OpenAPI spec (`api/openapi.yaml`) is the source of truth
- **Code generation:** Spring controller interfaces and Dart client SDK generated from the spec
- **Validation:** Spectral lints the spec, oasdiff detects breaking changes, provider contract tests verify implementation matches spec
- **Versioning:** URL path versioning (`/api/v1/...`) when breaking changes are unavoidable

> [!info] Contract testing
> See [[TESTING_STRATEGY#4. Contract Testing]] for the three-layer contract testing approach (spec validation → provider tests → consumer tests).

---

## 5. Frontend Architecture

### Technology choices

| Concern | Technology | Why |
|---|---|---|
| **Framework** | Flutter (Dart) | Single codebase for web + iOS + Android |
| **State management** | Riverpod (with code generation) | Compile-safe, testable, supports async |
| **Local database** | drift (SQLite via WASM in browser) | Typed queries, migrations, mirrors PostgreSQL schema |
| **API client** | Generated Dart SDK from OpenAPI spec | Always in sync with backend contract |
| **Navigation** | go_router | Declarative, deep-linkable |

### Feature-based structure

```
lib/
├── features/
│   ├── capture/          ← Quick Capture screen + logic
│   │   ├── presentation/ ← Widgets, screens
│   │   ├── application/  ← Riverpod providers
│   │   └── data/         ← Repository (local + remote)
│   ├── notebook/         ← Word list, search, filter
│   ├── word_detail/      ← Full word card view
│   ├── flashcard/        ← Flashcard review
│   ├── quiz/             ← Quiz engine + types
│   ├── dashboard/        ← Home screen, stats
│   └── settings/         ← Profile, preferences
├── data/
│   ├── database/         ← drift database, DAOs, tables
│   └── sync/             ← Outbox, delta pull, sync engine
├── api/
│   └── generated/        ← OpenAPI-generated client (excluded from lint/coverage)
└── core/
    ├── router.dart       ← go_router configuration
    ├── theme.dart         ← Material 3 theme
    └── constants.dart
```

### State management pattern

```mermaid
flowchart LR
    W["Widget"] -->|"reads"| P["Provider<br/>(Riverpod)"]
    P -->|"calls"| R["Repository"]
    R -->|"reads/writes"| DB["drift (SQLite)"]
    R -.->|"sync"| API["Spring Boot API"]
```

Each feature follows the same pattern:

1. **Widget** reads state from a Riverpod provider (reactive rebuild on change)
2. **Provider** holds business logic, calls repository methods
3. **Repository** coordinates local persistence (drift) and remote sync (API client)
4. **drift** is the immediate source of truth — all reads come from local SQLite

### How the browser database works

On web, drift compiles SQLite to WebAssembly and runs it inside a Web Worker. The main thread (Flutter) communicates with the worker via `postMessage`. Data is persisted to the Origin Private File System (OPFS) for durability.

```
Main Thread (Flutter) → postMessage → Web Worker → WASM (SQLite) → OPFS
```

> [!info] Deep dive
> See [[BROWSER_DATABASE_INTERNALS]] for a full explanation of Web Workers, WASM compilation, OPFS vs IndexedDB, and performance characteristics.

---

## 6. Deployment Topology

### Phase 1 (current) — Web only, no backend

```mermaid
flowchart LR
    U["User"] --> FH["Firebase Hosting<br/>(static files)"]
    FH --> APP["Flutter Web App<br/>(compiled JS + WASM)"]
    APP --> LOCAL[("drift / SQLite<br/>(browser OPFS)")]
    APP --> DICT["Free Dictionary API<br/>(direct, no auth)"]
```

No backend, no auth, no database server. The Flutter app is a static site hosted on Firebase Hosting. All data lives in the browser's local storage via drift/SQLite/OPFS.

### Phase 2+ — Full stack

```mermaid
flowchart TB
    subgraph User Devices
        WEB["Browser<br/>(Flutter Web)"]
        IOS["iPhone<br/>(Flutter iOS)"]
    end

    subgraph Firebase
        FH["Firebase Hosting<br/>(static web files)"]
        FA["Firebase Auth<br/>(identity)"]
    end

    subgraph GCP["Google Cloud Platform"]
        CR["Cloud Run<br/>(Spring Boot API)"]
    end

    subgraph Neon
        PG[("PostgreSQL<br/>(serverless)")]
    end

    DICT["Dictionary API"]

    WEB --> FH
    WEB & IOS -->|"JWT"| FA
    WEB & IOS -->|"REST API"| CR
    CR --> PG
    CR -->|"Enrichment"| DICT
    CR -->|"Validates JWT"| FA
```

### Environments

| Environment | Cloud Run | PostgreSQL (Neon) | Firebase | Purpose |
|---|---|---|---|---|
| **DEV** | dev instance | dev branch/database | dev project | Local development, feature branches |
| **TEST** | test instance | test branch/database | test project | PR validation, staging |
| **PROD** | prod instance | prod database | prod project | Live users |

### Scaling characteristics

| Component | Scaling model | Limit before action needed |
|---|---|---|
| **Flutter web** | Static files on CDN (Firebase Hosting) | Effectively unlimited |
| **Flutter iOS** | Runs on user's device | N/A |
| **Cloud Run** | Auto-scales 0 → N containers | ~1000 concurrent users per instance |
| **Neon PostgreSQL** | Serverless auto-suspend, scales compute | Branch-level isolation; upgrade to Pro if >1GB |
| **Dictionary cache** | Grows once per unique English word | ~170K entries max (covers all common English) |

**Cost at rest:** Cloud Run scales to zero when idle. Neon auto-suspends after inactivity. During development, the only fixed cost is the Apple Developer Program ($99/yr).

---

## 7. Security Model

### Authentication flow

```mermaid
sequenceDiagram
    actor User
    participant App as Flutter App
    participant FA as Firebase Auth
    participant API as Spring Boot API

    User->>App: Sign in (email / Google / Apple)
    App->>FA: Authenticate
    FA-->>App: Firebase ID Token (JWT)
    App->>App: Store token locally

    Note over App,API: Every API request includes the token
    App->>API: GET /api/words<br/>Authorization: Bearer {token}
    API->>FA: Verify JWT signature<br/>(Firebase Admin SDK)
    FA-->>API: Token valid, uid = "user-123"
    API->>API: Scope all queries to uid
    API-->>App: 200 OK (user's words only)
```

### Security layers

| Layer | Mechanism | What it protects |
|---|---|---|
| **Identity** | Firebase Auth (email, Google, Apple Sign-In) | Who the user is |
| **Transport** | HTTPS everywhere (Cloud Run enforces TLS) | Data in transit |
| **API authentication** | Firebase JWT validation via Spring Security filter | Unauthorized API access |
| **Data isolation** | Every query scoped by `user_id` from JWT | Users seeing each other's data |
| **API key protection** | Oxford API key stored in Cloud Run env vars, never sent to client | Key leakage |
| **CORS** | Allowlisted origins only | Cross-origin attacks |
| **Input validation** | Bean Validation (backend) + Dart types (frontend) | Injection, malformed data |
| **Static analysis** | Semgrep (OWASP top 10) + SpotBugs/FindSecBugs (CWE-mapped) | Code-level vulnerabilities |
| **Dependency scanning** | Dependabot (Gradle, pub, GitHub Actions) | Known CVEs in dependencies |

### Per-user data isolation

This is the most critical security property. Every database query includes the authenticated user's ID:

```java
// Repository — every query is scoped
@Query("SELECT w FROM UserWord w WHERE w.userId = :userId")
List<UserWord> findAllByUserId(@Param("userId") String userId);

// Service — userId comes from the authenticated principal, never from request body
public List<WordDto> getWords(String userId) {
    return wordRepository.findAllByUserId(userId);
}

// Controller — extracts userId from the validated Firebase JWT
@GetMapping("/api/words")
public List<WordDto> getWords(@AuthenticationPrincipal FirebaseToken token) {
    return wordService.getWords(token.getUid());
}
```

A user can never request another user's data because the `userId` is extracted from the JWT, not from query parameters or request bodies.

---

## 8. Cross-Cutting Concerns

### Error handling strategy

| Layer | Strategy |
|---|---|
| **Flutter UI** | Riverpod `AsyncValue` for loading/error/data states; user-friendly error messages |
| **Flutter data** | Repository catches exceptions, maps to domain error types |
| **Spring Boot controllers** | `@ControllerAdvice` with global exception handler; consistent `ErrorResponse` JSON shape |
| **Spring Boot services** | Custom exception hierarchy (`WordNotFoundException`, `EnrichmentFailedException`) |
| **External API calls** | Circuit breaker pattern for dictionary API; fallback to cached data or graceful degradation |
| **Sync failures** | Outbox retains failed writes; exponential backoff on retry; never blocks UI |

### Logging and observability

| Concern | Tool | Where |
|---|---|---|
| **Structured logging** | SLF4J + Logback (backend), `dart:developer` (frontend) | Both |
| **Request tracing** | Spring Boot request IDs in MDC | Backend |
| **Health check** | `/actuator/health` (Spring Boot Actuator) | Backend |
| **Uptime monitoring** | Cloud Run built-in metrics | GCP |
| **Error tracking** | Firebase Crashlytics (planned, Phase 6) | Frontend |
| **Performance metrics** | k6 nightly tests catch regressions | CI |

### Configuration management

| Environment variable | Where | Purpose |
|---|---|---|
| `SPRING_DATASOURCE_URL` | Cloud Run | Neon PostgreSQL connection |
| `FIREBASE_PROJECT_ID` | Cloud Run | JWT verification audience |
| `DICTIONARY_API_KEY` | Cloud Run (Phase 6) | Oxford API authentication |
| `SPRING_PROFILES_ACTIVE` | Cloud Run | `dev` / `test` / `prod` profile selection |

**Secrets** are stored in GCP Secret Manager and injected as environment variables into Cloud Run. They never appear in code, config files, or version control.

**Spring profiles** control environment-specific behavior:
- `dev` — verbose logging, relaxed CORS, local Firebase emulator
- `test` — Testcontainers PostgreSQL, mock dictionary service
- `prod` — strict CORS, production Firebase project, real dictionary API

---

## 9. Key Technology Decisions

Each decision below was made for a specific reason. Links point to the deep-dive documents where the full rationale is documented.

### Why Flutter (not React Native, not native)

| Factor | Decision |
|---|---|
| **Single codebase** | Web + iOS + Android from one Dart codebase |
| **Web-first** | Flutter web is a first-class target — critical for Phase 1 (zero friction, no app store) |
| **Performance** | Compiled to native ARM (iOS) and optimized JS + WASM (web) |
| **Ecosystem** | drift, Riverpod, go_router — mature packages for the architecture we need |

### Why Spring Boot (not serverless functions, not Node.js)

| Factor | Decision |
|---|---|
| **Java ecosystem** | Mature libraries for auth, ORM, testing, static analysis |
| **Testcontainers** | Integration tests against real PostgreSQL with zero CI config |
| **Type safety** | Java 21 + strong typing catches bugs at compile time |
| **Cloud Run** | Containerized Spring Boot on Cloud Run = auto-scaling with zero infrastructure management |
| **Team skill** | Backend expertise is in Java/Spring |

### Why drift + SQLite (not IndexedDB, not Hive)

| Factor | Decision |
|---|---|
| **SQL** | Full relational queries — joins, indexes, aggregations for SRS scheduling |
| **Schema mirrors PostgreSQL** | Same relational model locally and in the cloud — sync is field-level, not translation |
| **WASM in browser** | SQLite compiled to WebAssembly runs in a Web Worker — non-blocking, performant |
| **Typed queries** | drift generates Dart code from schema — compile-time query safety |
| **Migration support** | Versioned schema migrations, same model as Flyway on the backend |

> [!info] Deep dive
> See [[BROWSER_DATABASE_INTERNALS]] for how drift, Web Workers, WASM, and OPFS fit together.

### Why Neon PostgreSQL (not RDS, not Supabase)

| Factor | Decision |
|---|---|
| **Serverless** | Auto-suspends on inactivity — $0 cost during development |
| **Branch databases** | Neon branches = isolated database copies for test environments |
| **PostgreSQL native** | Full PostgreSQL feature set (JSONB, GIN indexes, `ON CONFLICT` upsert) |
| **Connection pooling** | Built-in pgbouncer — handles Cloud Run's bursty connection pattern |

### Why local-first lite (not cloud-first, not full CRDT)

| Factor | Decision |
|---|---|
| **Quick Capture < 200ms** | Local write is instant; cloud-first adds a network round trip |
| **Offline support** | Works on the train, in coffee shops, anywhere without internet |
| **No shared documents** | Every word belongs to one user — LWW conflict resolution is sufficient |
| **Engineering simplicity** | CRDTs add significant complexity for zero benefit in a single-user notebook |

> [!info] Deep dive
> See [[LOCAL_FIRST_ARCHITECTURE]] for the full local-first spectrum analysis and sync protocol.

---

## 10. Evolution Path

The architecture is designed to handle WordPower's growth without requiring a rewrite. Below are the known constraints and what triggers a change.

### Current constraints (acceptable today)

| Constraint | Why it's fine now | When it breaks |
|---|---|---|
| **LWW conflict resolution** | Single-user notebook — conflicts near zero | If collaborative word lists are added (multi-user editing) |
| **Full sync on cold start** | Users have < 500 words in early phases | When vocabularies exceed ~5,000 words on a new device |
| **Single Cloud Run instance** | < 100 concurrent users during development | Sustained > 1,000 concurrent users |
| **Free Dictionary API** | Sufficient quality for MVP | Phase 6 (Oxford API provides better data quality, pronunciation, CEFR hints) |
| **No CDN for audio** | Low user count, audio files served via dictionary API URLs | If audio playback latency becomes noticeable at scale |

### Graduation triggers

| Trigger | Current state | Graduates to | Documented in |
|---|---|---|---|
| **> 5,000 words per user** | Full sync on cold start | Progressive sync (paginated initial load) | [[LOCAL_FIRST_ARCHITECTURE#9. The Cold Start Problem: New Device, Lots of Data]] |
| **Collaborative features** | LWW (last-write-wins) | PowerSync or ElectricSQL (CRDT-based sync) | [[LOCAL_FIRST_ARCHITECTURE#10. Future Graduation Path]] |
| **> 1,000 concurrent users** | Single Cloud Run instance | Cloud Run auto-scaling (already supported, just costs more) | — |
| **Phase 6 launch** | Free Dictionary API | Oxford API behind server-side cache | [[PROJECT#Dictionary Caching Architecture]] |
| **Enrichment bottleneck** | Synchronous enrichment in API call | Async enrichment via message queue (Cloud Tasks / Pub/Sub) | — |
| **Complex quiz scheduling** | In-memory SRS calculation | Precomputed review queues, materialized views | — |

### What doesn't change

These architectural invariants hold regardless of scale:

- **Local-first reads** — the Flutter app always reads from drift, never waits for the network
- **Per-user data isolation** — `userId` from JWT scopes every query
- **Contract-first API** — OpenAPI spec remains the source of truth
- **Layered backend** — web → application → domain → persistence, enforced by ArchUnit
- **Static analysis pipeline** — Checkstyle, PMD, SpotBugs, ArchUnit, Semgrep gate every PR
