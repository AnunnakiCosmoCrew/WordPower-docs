# Deployment & Operations Guide — WordPower

> [!abstract] Summary
> How to run WordPower locally, deploy to staging/production, manage the database, monitor the system, and respond to incidents. This is a living document — update it as infrastructure evolves.

Related: [[ARCHITECTURE#6. Deployment Topology]] | [[ARCHITECTURE#8. Cross-Cutting Concerns]] | [[TESTING_STRATEGY#10. What Runs When]]

---

## Table of Contents

1. [[#1. Local Development Setup]]
2. [[#2. CI/CD Pipeline]]
3. [[#3. Environments & Deployment]]
4. [[#4. Database Management]]
5. [[#5. Firebase Configuration]]
6. [[#6. Monitoring & Observability]]
7. [[#7. Incident Response]]
8. [[#8. Cost Monitoring]]
9. [[#9. Runbook: Common Operations]]
10. [[#10. Glossary]]

---

## 1. Local Development Setup

### Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| **Flutter SDK** | 3.x (stable) | Frontend development |
| **Java** | 21 (LTS) | Backend development |
| **Docker Desktop** | Latest | Testcontainers (integration tests) |
| **Node.js** | 18+ | OpenAPI tooling (Spectral, oasdiff) |
| **Firebase CLI** | Latest | Local emulator, hosting deploys |
| **gh CLI** | Latest | GitHub issue/PR management |

### Clone and setup

```bash
# Clone the monorepo
git clone git@github.com:AnunnakiCosmoCrew/WordPower-app.git
cd WordPower-app

# Backend
cd backend
./gradlew build          # compile + test + static analysis
./gradlew bootRun        # start API on http://localhost:8080

# Frontend (separate terminal)
cd frontend
flutter pub get
flutter run -d chrome    # start web app on localhost
```

### Environment variables (local)

Create `backend/.env.local` (gitignored):

```properties
SPRING_PROFILES_ACTIVE=dev
SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/wordpower_dev
SPRING_DATASOURCE_USERNAME=postgres
SPRING_DATASOURCE_PASSWORD=postgres
FIREBASE_PROJECT_ID=wordpower-dev
```

> [!warning] Never commit `.env` files
> Environment files contain secrets. They are gitignored by default. If you see `.env` in `git status`, something is wrong.

### Running tests locally

```bash
# Backend — requires Docker Desktop running
cd backend
./gradlew check          # all tests + static analysis
./gradlew test           # unit + integration tests only
./gradlew componentTest  # Cucumber BDD tests only
./gradlew coverage       # JaCoCo unit + component reports
./gradlew pitest         # mutation testing (domain + application packages)

# Frontend
cd frontend
flutter analyze --no-fatal-infos
dart format --set-exit-if-changed .
flutter test             # unit + widget + golden + consumer contract
flutter test --coverage  # same + lcov report
```

### Local database

- **Backend:** Testcontainers auto-starts PostgreSQL for tests. For `bootRun`, use a local PostgreSQL instance or Neon dev branch.
- **Frontend:** drift uses in-browser SQLite (OPFS). No setup needed — data lives in browser storage.

---

## 2. CI/CD Pipeline

### What runs when

```mermaid
flowchart TB
    subgraph PR["Every Pull Request"]
        FCI["frontend-ci<br/>(~50s)"]
        BCI["backend-ci<br/>(~90s)"]
        SV["spec-validation<br/>(~5s)"]
        SG["semgrep<br/>(~15s)"]
    end

    subgraph Nightly["Nightly (3 AM UTC)"]
        Fuzz["schemathesis<br/>(~3 min)"]
        Perf["k6 perf<br/>(~2 min)"]
        Mut["pitest<br/>(~5 min)"]
    end

    subgraph Deploy["Pre-deploy"]
        E2E["flutter integration tests<br/>(Chrome, ~3 min)"]
    end

    PR --> Nightly --> Deploy
```

### CI workflows (in `WordPower-app/.github/workflows/`)

| Workflow | Trigger | What it does |
|---|---|---|
| `frontend-ci.yml` | PR (frontend changes) | analyze, format, test, coverage, golden tests, consumer contract |
| `backend-ci.yml` | PR (backend changes) | checkstyle, PMD, SpotBugs, ArchUnit, unit tests, integration tests, journey tests, provider contracts, JaCoCo |
| `openapi-ci.yml` | PR (api/ changes) | Spectral lint, oasdiff breaking change check |
| `semgrep.yml` | PR + push to main + weekly | OWASP top 10, Java security rules |
| `nightly.yml` | Cron (3 AM UTC) | Schemathesis fuzz, k6 perf, PIT mutation |
| `deploy.yml` | Push to main (manual gate) | Flutter integration tests → Firebase Hosting deploy |

### Smart skipping

`dorny/paths-filter` skips irrelevant jobs. A frontend-only PR won't trigger `backend-ci.yml`. Spec validation only runs when `api/` or `.spectral.yaml` changes.

### Required status checks

These must pass before merge to `main`:

- `frontend-ci` (if frontend files changed)
- `backend-ci` (if backend files changed)
- `spec-validation` (if API spec changed)
- `semgrep`

---

## 3. Environments & Deployment

### Environment matrix

| Environment | Cloud Run | Neon Database | Firebase Project | URL |
|---|---|---|---|---|
| **DEV** | Local (`bootRun`) | Neon dev branch or local PG | `wordpower-dev` | `http://localhost:8080` |
| **TEST** | GCP test instance | Neon test branch | `wordpower-test` | TBD |
| **PROD** | GCP prod instance | Neon prod database | `wordpower-prod` | TBD |

### Backend deployment (Cloud Run)

```mermaid
flowchart LR
    Push["Push to main"] --> Build["Cloud Build<br/>(Dockerfile)"]
    Build --> Image["Container image<br/>(Artifact Registry)"]
    Image --> Deploy["Cloud Run<br/>(deploy new revision)"]
    Deploy --> Health["Health check<br/>(/actuator/health)"]
    Health -->|"Pass"| Live["✅ Traffic shifted"]
    Health -->|"Fail"| Rollback["❌ Previous revision kept"]
```

**Key settings:**

| Setting | Value | Why |
|---|---|---|
| Min instances | 0 | Scale to zero when idle ($0 at rest) |
| Max instances | 5 | Cost protection during development |
| Memory | 512 MB | Sufficient for Spring Boot + Testcontainers-free runtime |
| CPU | 1 vCPU | Sufficient for expected load |
| Concurrency | 80 | Requests per instance before scaling |
| Startup probe | `/actuator/health`, 30s timeout | Spring Boot needs time to start |

### Frontend deployment (Firebase Hosting)

```bash
cd frontend
flutter build web --release
firebase deploy --only hosting
```

Firebase Hosting serves the compiled Flutter web app as static files via its global CDN. Custom headers (COOP/COEP) are configured in `firebase.json`:

```json
{
  "hosting": {
    "headers": [
      {
        "source": "**",
        "headers": [
          { "key": "Cross-Origin-Opener-Policy", "value": "same-origin" },
          { "key": "Cross-Origin-Embedder-Policy", "value": "require-corp" }
        ]
      }
    ]
  }
}
```

### Rollback

| Component | How to rollback |
|---|---|
| **Cloud Run** | `gcloud run services update-traffic wordpower-api --to-revisions=PREVIOUS_REVISION=100` |
| **Firebase Hosting** | `firebase hosting:channel:deploy rollback` or redeploy previous commit |
| **Database** | Neon point-in-time recovery (see section 4) |

---

## 4. Database Management

### Neon PostgreSQL

| Concern | How |
|---|---|
| **Connection string** | `postgresql://user:pass@ep-xxx.us-east-1.aws.neon.tech/wordpower` (in GCP Secret Manager) |
| **Connection pooling** | Built-in pgbouncer — handles Cloud Run's bursty connection pattern |
| **Branching** | `neon branches create --name test-branch` for isolated test databases |
| **Auto-suspend** | Computes suspend after 5 min of inactivity (dev/test). Disabled for prod. |

### Flyway migrations

Migrations live in `backend/src/main/resources/db/migration/`:

```
V1__initial_schema.sql
V2__add_cefr_level.sql
V3__add_sync_fields.sql
...
```

| Operation | Command |
|---|---|
| Run migrations | Automatic on Spring Boot startup (`spring.flyway.enabled=true`) |
| Check migration status | `./gradlew flywayInfo` |
| Repair checksums | `./gradlew flywayRepair` (use with caution) |

> [!warning] Migration safety rules
> - Never modify a migration that has already been applied to production
> - Never delete a migration file
> - Test migrations against a Neon branch before applying to prod
> - Always include a rollback strategy in the PR description for schema changes

### Backup & recovery

| Feature | Neon capability |
|---|---|
| **Point-in-time recovery** | Restore to any point in the last 7 days (free tier) or 30 days (pro) |
| **Branch restore** | Create a branch from any point in time — instant, copy-on-write |
| **Logical backup** | `pg_dump` via Neon connection string |

---

## 5. Firebase Configuration

### Projects

| Project | Firebase ID | Purpose |
|---|---|---|
| DEV | `wordpower-dev` | Local development, emulators |
| TEST | `wordpower-test` | CI, staging |
| PROD | `wordpower-prod` | Live users |

### Auth providers

| Provider | Phase | Setup |
|---|---|---|
| Email/password | Phase 2 | Firebase Console → Authentication → Sign-in methods |
| Google Sign-In | Phase 2 | OAuth client ID configured in Firebase Console |
| Apple Sign-In | Phase 2 (iOS) | Apple Developer account + Service ID configured |

### Firebase Hosting headers

COOP/COEP headers (required for OPFS fast path) are configured in `firebase.json`. See [[BROWSER_DATABASE_INTERNALS#6. Where the Bytes Actually Live]] for why these matter.

### Firebase emulator (local development)

```bash
firebase emulators:start --only auth
# Auth emulator runs on http://localhost:9099
```

Set `FIREBASE_AUTH_EMULATOR_HOST=localhost:9099` in the backend environment to use the emulator instead of production Firebase.

---

## 6. Monitoring & Observability

### Health checks

| Endpoint | What it checks | Alerting |
|---|---|---|
| `GET /actuator/health` | App running, DB connected | Cloud Run auto-restarts unhealthy instances |
| Cloud Run health dashboard | Request latency, error rate, instance count | GCP Monitoring alerts (planned) |

### Logging

| Component | Tool | Where to find logs |
|---|---|---|
| **Backend** | SLF4J + Logback (structured JSON) | GCP Cloud Logging (Cloud Run logs) |
| **Frontend** | `dart:developer` | Browser DevTools console |
| **CI** | GitHub Actions logs | Actions tab in the repo |

### Key metrics to watch

| Metric | Source | Warning threshold | Critical threshold |
|---|---|---|---|
| API error rate (5xx) | Cloud Run metrics | > 1% over 5 min | > 5% over 5 min |
| API p95 latency | Cloud Run metrics | > 500ms | > 2000ms |
| Database connections | Neon dashboard | > 80% pool capacity | Connection errors in logs |
| Dictionary API errors | Application logs | > 5 failures/hour | API unreachable for > 10 min |
| Cold start duration | Cloud Run metrics | > 10s | > 30s |
| CI pipeline duration | GitHub Actions | > 5 min (PR pipeline) | > 10 min |

### Planned monitoring (Phase 6)

- Firebase Crashlytics (frontend crash reporting)
- GCP Cloud Monitoring alerts (Slack/email integration)
- Uptime checks (external ping every 5 minutes)

---

## 7. Incident Response

### Severity levels

| Level | Definition | Response time | Examples |
|---|---|---|---|
| **SEV-1** | Service down, all users affected | Immediate | Cloud Run unresponsive, database unreachable |
| **SEV-2** | Major feature broken, workaround exists | < 4 hours | Sync broken but local-first still works, enrichment pipeline down |
| **SEV-3** | Minor feature issue, low user impact | Next business day | Golden test regression, flaky nightly test |

### Runbook: service down (SEV-1)

1. **Verify:** check `/actuator/health` directly. Is it the API or a downstream dependency?
2. **Check Cloud Run:** GCP Console → Cloud Run → wordpower-api → Revisions. Is the latest revision healthy?
3. **Check Neon:** Neon Console → is the database suspended? Connection limit hit?
4. **Rollback if needed:** revert to previous Cloud Run revision (see section 3)
5. **Communicate:** update status page (planned) or notify affected users
6. **Post-mortem:** document root cause, timeline, and prevention measures

### Runbook: enrichment pipeline down (SEV-2)

1. **Check Dictionary API:** is `dictionaryapi.dev` responding? (for Phase 1-5)
2. **Impact:** new words won't be enriched, but local-first capture still works. Existing enriched words unaffected.
3. **Resolution:** dictionary cache means most lookups succeed from cache. Only truly new words are affected.
4. **If prolonged (> 1 hour):** add a user-facing banner: "Word definitions are temporarily unavailable. Your words are saved and will be enriched automatically when the service recovers."

### Rollback decision tree

```mermaid
flowchart TB
    Issue["Issue detected"] --> Severity{"Severity?"}
    Severity -->|"SEV-1"| Rollback["Rollback immediately"]
    Severity -->|"SEV-2"| Workaround{"Workaround<br/>available?"}
    Workaround -->|"Yes"| Fix["Fix forward<br/>(hotfix branch → PR)"]
    Workaround -->|"No"| Rollback
    Severity -->|"SEV-3"| Fix
    Rollback --> Postmortem["Post-mortem"]
    Fix --> Postmortem
```

---

## 8. Cost Monitoring

### Monthly cost breakdown (development phase)

| Service | Estimated cost | Scaling trigger |
|---|---|---|
| **Cloud Run** | $0 (scale to zero) | First sustained traffic |
| **Neon PostgreSQL** | $0 (free tier: 0.5 GB storage, auto-suspend) | > 0.5 GB data or need for always-on |
| **Firebase Auth** | $0 (free up to 10K MAU) | > 10K monthly active users |
| **Firebase Hosting** | $0 (free tier: 10 GB bandwidth/month) | > 10 GB bandwidth |
| **Apple Developer Program** | $99/yr (~$8.25/mo) | Fixed cost for iOS distribution |
| **GitHub Actions** | $0 (free tier: 2,000 min/month) | > 2,000 CI minutes |
| **Total (dev)** | **~$8.25/mo** | |

### Monthly cost at 500 active users (Phase 6)

| Service | Estimated cost | Notes |
|---|---|---|
| **Cloud Run** | $0–10 | Scale-to-zero + bursty usage |
| **Neon PostgreSQL** | $0–19 | Depends on storage and compute usage |
| **Oxford API** | ~$63 | Flat rate (API Lite plan) |
| **Firebase Auth** | $0 | Still under 10K MAU |
| **Firebase Hosting** | $0–5 | CDN bandwidth |
| **Apple Developer** | $8.25 | Fixed |
| **Total (500 users)** | **~$73–102/mo** | |

### Cost alerts

Set up GCP billing alerts:

| Threshold | Action |
|---|---|
| $50/mo | Email notification (review usage) |
| $100/mo | Email + investigate (is something scaling unexpectedly?) |
| $200/mo | Budget cap — review immediately |

---

## 9. Runbook: Common Operations

### Add a new Flyway migration

```bash
# Create migration file with next version number
touch backend/src/main/resources/db/migration/V4__description.sql

# Write SQL
# Test locally: ./gradlew test (Testcontainers runs migrations)
# Test against Neon branch: create a branch, connect, verify
# Commit and PR
```

### Create a Neon database branch

```bash
neon branches create --name feature-branch-name
# Returns connection string for the branch
# Branch is a copy-on-write snapshot — instant, zero cost until writes
```

### Deploy to Cloud Run manually

```bash
cd backend
./gradlew bootBuildImage  # builds container image
docker tag wordpower-api gcr.io/wordpower-prod/wordpower-api:latest
docker push gcr.io/wordpower-prod/wordpower-api:latest
gcloud run deploy wordpower-api \
  --image gcr.io/wordpower-prod/wordpower-api:latest \
  --region us-central1 \
  --allow-unauthenticated
```

### Rotate a secret

```bash
# Update in GCP Secret Manager
gcloud secrets versions add DICTIONARY_API_KEY --data-file=new-key.txt

# Restart Cloud Run to pick up new secret
gcloud run services update wordpower-api --region us-central1 --update-env-vars FORCE_RESTART=$(date +%s)
```

### Check sync health

```sql
-- Count unsynced outbox entries per user (run against Neon)
SELECT user_id, COUNT(*) as pending
FROM sync_outbox
WHERE synced_at IS NULL
GROUP BY user_id
ORDER BY pending DESC;

-- Check for stale outbox entries (> 24 hours old)
SELECT * FROM sync_outbox
WHERE synced_at IS NULL
AND created_at < NOW() - INTERVAL '24 hours';
```

---

## 10. Glossary

| Term | Definition |
|---|---|
| **Cloud Run** | Google Cloud's serverless container platform — auto-scales from 0 to N instances based on traffic |
| **Neon** | Serverless PostgreSQL with branching, auto-suspend, and point-in-time recovery |
| **Flyway** | Database migration tool — versioned SQL scripts applied in order on startup |
| **Testcontainers** | Java library that spins up Docker containers (PostgreSQL) for integration tests |
| **Firebase Hosting** | Static file hosting with global CDN, custom domain support, and header configuration |
| **Firebase Auth** | Managed authentication service supporting email, Google, Apple sign-in |
| **COOP/COEP** | HTTP headers required for cross-origin isolation, enabling SharedArrayBuffer and fast OPFS |
| **Scale to zero** | Cloud Run feature where instances shut down during inactivity, reducing cost to $0 at rest |
| **Neon branch** | A copy-on-write database snapshot — instant to create, isolated for testing |
| **Point-in-time recovery** | Neon feature to restore the database to any moment in the retention window |
| **Secret Manager** | GCP service for storing API keys, passwords, and certificates securely |
| **Revision** | A specific deployment of a Cloud Run service — rollback means routing traffic to a previous revision |
