# API Documentation — WordPower

> [!abstract] Summary
> Human-readable companion to the machine-readable OpenAPI spec (`WordPower-app/api/openapi.yaml`). Covers authentication, core endpoints, request/response shapes, error handling, and sync protocol. The OpenAPI spec is the source of truth — this document explains intent and usage patterns.

Related: [[ARCHITECTURE#4. Backend Architecture]] | [[ARCHITECTURE#7. Security Model]] | [[TESTING_STRATEGY#4. Contract Testing]]

---

## Table of Contents

1. [[#1. Base URL & Versioning]]
2. [[#2. Authentication]]
3. [[#3. Common Response Patterns]]
4. [[#4. Core Endpoints]]
5. [[#5. Sync Protocol]]
6. [[#6. Dictionary Enrichment]]
7. [[#7. Error Handling]]
8. [[#8. Rate Limiting]]
9. [[#9. Glossary]]

---

## 1. Base URL & Versioning

| Environment | Base URL |
|---|---|
| **DEV** | `http://localhost:8080` |
| **TEST** | `https://test-api.wordpower.app` (planned) |
| **PROD** | `https://api.wordpower.app` (planned) |

### Versioning

- URL path versioning: `/api/v1/...`
- Breaking changes increment the version prefix
- Non-breaking additions (new optional fields, new endpoints) don't require a version bump
- The OpenAPI spec (`api/openapi.yaml`) is the source of truth for the current contract

### Content type

All requests and responses use `application/json` unless otherwise noted. The `Content-Type` and `Accept` headers should both be set to `application/json`.

---

## 2. Authentication

WordPower uses **Firebase Auth** for identity. Every API request (except health checks) requires a valid Firebase ID token.

### Auth flow

```mermaid
sequenceDiagram
    participant App as Flutter App
    participant FA as Firebase Auth
    participant API as Spring Boot API

    App->>FA: Sign in (email / Google / Apple)
    FA-->>App: Firebase ID Token (JWT)

    App->>API: GET /api/v1/words
    Note over App,API: Authorization: Bearer {token}
    API->>FA: Verify JWT signature
    FA-->>API: Valid — uid: "user-123"
    API->>API: Scope all queries to uid
    API-->>App: 200 OK
```

### Request headers

```http
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
Content-Type: application/json
Accept: application/json
```

### Token lifecycle

| Event | Action |
|---|---|
| Token expired (1 hour) | Flutter SDK auto-refreshes via `getIdToken(true)` |
| User signs out | Token is discarded; API returns 401 on next request |
| Token invalid/malformed | API returns 401 immediately |

---

## 3. Common Response Patterns

### Paginated list response

All list endpoints return a paginated wrapper:

```json
{
  "content": [ ... ],
  "page": 0,
  "size": 20,
  "totalElements": 142,
  "totalPages": 8
}
```

| Parameter | Default | Max | Description |
|---|---|---|---|
| `page` | 0 | — | Zero-indexed page number |
| `size` | 20 | 100 | Items per page |

### Timestamps

All timestamps are ISO 8601 in UTC: `"2026-04-20T14:30:00Z"`

### Null vs absent

- **Null field in response:** the field exists but has no value (e.g., `"synonyms": null` — not yet enriched)
- **Absent field in PATCH request:** the field should not be changed
- **Explicit null in PATCH request:** the field should be cleared (see PATCH semantics below)

---

## 4. Core Endpoints

### Words

#### `POST /api/v1/words` — Create a word

Save a new word to the user's notebook. Triggers async enrichment.

**Request:**

```json
{
  "word": "ubiquitous"
}
```

**Response:** `201 Created`

```json
{
  "id": 42,
  "word": "ubiquitous",
  "personalNotes": null,
  "nativeTranslation": null,
  "definitions": null,
  "partOfSpeech": null,
  "phonetic": null,
  "audioUrl": null,
  "synonyms": null,
  "antonyms": null,
  "exampleSentences": null,
  "cefrLevel": null,
  "domain": null,
  "domainPath": null,
  "status": "NEW",
  "easeFactor": 2.5,
  "interval": 0,
  "repetitions": 0,
  "nextReviewDate": null,
  "deletedAt": null,
  "createdAt": "2026-04-20T14:30:00Z",
  "updatedAt": "2026-04-20T14:30:00Z"
}
```

> [!info] Enrichment is async
> The response returns immediately with `null` enrichment fields. The backend triggers dictionary lookup in the background. The enriched data appears on the next `GET` or delta sync pull.

**Errors:**

| Status | When |
|---|---|
| 400 | `word` is blank or exceeds 100 characters |
| 409 | Word already exists in this user's notebook (case-insensitive dedup) |

---

#### `GET /api/v1/words` — List words

Retrieve the user's word collection, paginated.

**Query parameters:**

| Param | Type | Description |
|---|---|---|
| `page` | int | Page number (default 0) |
| `size` | int | Page size (default 20, max 100) |
| `status` | string | Filter by status: `NEW`, `LEARNING`, `REVIEW`, `MASTERED` |
| `cefrLevel` | string | Filter by CEFR level: `A1`, `A2`, `B1`, `B2`, `C1`, `C2` |
| `search` | string | Case-insensitive prefix search on the word field |
| `updatedSince` | ISO 8601 | Delta sync — return only records changed after this timestamp. **Includes soft-deleted rows** (tombstones) so clients can detect deletions. See [[LOCAL_FIRST_ARCHITECTURE#Step 7 — Delete propagation (tombstones)]] |

**Response:** `200 OK`

```json
{
  "content": [
    {
      "id": 42,
      "word": "ubiquitous",
      "definitions": ["present, appearing, or found everywhere"],
      "partOfSpeech": "adjective",
      "phonetic": "/juːˈbɪkwɪtəs/",
      "audioUrl": "https://api.dictionaryapi.dev/media/pronunciations/en/ubiquitous.mp3",
      "synonyms": ["omnipresent", "pervasive", "universal"],
      "antonyms": ["rare", "scarce"],
      "cefrLevel": "C1",
      "domain": "communication",
      "domainPath": "The Mind > Communication",
      "status": "REVIEW",
      "easeFactor": 2.5,
      "interval": 15,
      "nextReviewDate": "2026-05-10",
      "deletedAt": null,
      "createdAt": "2026-04-20T14:30:00Z",
      "updatedAt": "2026-04-22T09:00:00Z"
    }
  ],
  "page": 0,
  "size": 20,
  "totalElements": 142,
  "totalPages": 8
}
```

---

#### `GET /api/v1/words/{id}` — Get a single word

**Response:** `200 OK` — full `WordResponse` object (same shape as list items).

**Errors:** `404` if the word doesn't exist or belongs to another user.

---

#### `PATCH /api/v1/words/{id}` — Update a word

Partial update using explicit-null semantics. Only send fields you want to change.

**Request — update personal notes:**

```json
{
  "personalNotes": "Heard this in a TED talk about technology"
}
```

**Request — clear native translation (set to null):**

```json
{
  "nativeTranslation": null
}
```

**Response:** `200 OK` — updated `WordResponse`.

**Errors:** `404` if not found.

> [!info] PATCH semantics
> Absent fields are not modified. Explicitly `null` fields are cleared. This allows clearing a personal note without affecting other fields. See WordPower-app#134 for implementation details.

---

#### `DELETE /api/v1/words/{id}` — Delete a word

Soft-deletes the word by setting a `deletedAt` timestamp. The word is excluded from normal list queries but included in delta sync responses (`?updatedSince=`) as a tombstone so other devices can detect the deletion. The shared `dictionary_cache` row (if any) is untouched.

If the user later re-adds the same word via `POST /api/v1/words`, the tombstone is **revived** (`deletedAt` cleared) instead of returning 409 — so the word comes back with its original enrichment data intact.

Tombstones are garbage-collected after a retention period (e.g., 90 days) via a scheduled job.

**Response:** `204 No Content`

**Errors:** `404` if not found.

---

### Health

#### `GET /actuator/health` — Health check

No authentication required.

**Response:** `200 OK`

```json
{
  "status": "UP",
  "components": {
    "db": { "status": "UP" },
    "diskSpace": { "status": "UP" }
  }
}
```

---

## 5. Sync Protocol

The sync protocol enables local-first operation. See [[LOCAL_FIRST_ARCHITECTURE#5. How the Sync Works]] for the full architectural explanation.

### Push: drain the outbox

The Flutter app queues local writes in a `sync_outbox` table. When online, it drains the outbox by calling `POST /api/v1/words` (for creates) or `PATCH /api/v1/words/{id}` (for updates) for each pending entry.

### Pull: delta sync

```
GET /api/v1/words?updatedSince=2026-04-20T14:30:00Z
```

Returns all words changed since the given timestamp — including enrichment updates, SRS state changes, and **soft-deleted rows (tombstones)**. The client inspects each returned row:

- `deletedAt == null` → upsert into local drift (create or update)
- `deletedAt != null` → delete from local drift + clean up any related outbox entries

### Conflict resolution

Last-write-wins (LWW) by `updatedAt` timestamp. See [[LOCAL_FIRST_ARCHITECTURE#6. Conflict Resolution: Last-Write-Wins]].

---

## 6. Dictionary Enrichment

Enrichment is triggered server-side after a word is created. The flow:

1. `POST /api/v1/words` saves the word
2. Backend checks `dictionary_cache` table
3. **Cache hit:** attach cached enrichment to the word
4. **Cache miss:** call Dictionary API → save to cache → attach to word
5. Word's `updatedAt` advances so the next delta sync picks up the enrichment

The client does not call the Dictionary API directly. All lookups go through the server, protecting API keys and enabling the shared cache.

See [[PROJECT#Dictionary Caching Architecture]] for the caching strategy.

---

## 7. Error Handling

### Standard error response

All errors follow a consistent shape:

```json
{
  "status": 400,
  "error": "Bad Request",
  "message": "Word must not be blank",
  "timestamp": "2026-04-20T14:30:00Z",
  "path": "/api/v1/words"
}
```

### Error codes

| Status | Meaning | Common causes |
|---|---|---|
| **400** | Bad Request | Validation failed (blank word, invalid CEFR level, malformed JSON) |
| **401** | Unauthorized | Missing, expired, or invalid Firebase JWT |
| **403** | Forbidden | Valid token but insufficient permissions (reserved for future roles) |
| **404** | Not Found | Word ID doesn't exist or belongs to another user |
| **409** | Conflict | Duplicate word (case-insensitive match in user's notebook) |
| **422** | Unprocessable Entity | Semantically invalid request (e.g., setting interval to negative) |
| **500** | Internal Server Error | Unexpected server failure — never intentional |
| **503** | Service Unavailable | Backend starting up or database connection lost |

### Retry guidance

| Status | Retry? | Strategy |
|---|---|---|
| 4xx | No | Fix the request (client error) |
| 500 | Yes, with backoff | Exponential backoff: 1s, 2s, 4s, max 3 retries |
| 503 | Yes, with backoff | Service recovering; retry after `Retry-After` header if present |

---

## 8. Rate Limiting

No explicit rate limiting is implemented in Phase 2. Cloud Run's auto-scaling handles load naturally. If abuse becomes a concern, rate limiting will be added via:

- **Per-user:** 100 requests/minute (based on Firebase UID from JWT)
- **Global:** Cloud Run max instances cap (cost protection)

Rate-limited responses will use `429 Too Many Requests` with a `Retry-After` header.

---

## 9. Glossary

| Term | Definition |
|---|---|
| **Firebase ID Token** | A JWT issued by Firebase Auth after successful sign-in; contains the user's UID and is verified server-side |
| **Delta sync** | Fetching only records changed since `updatedSince` timestamp, instead of pulling everything |
| **Enrichment** | The process of adding dictionary data (definitions, IPA, CEFR level) to a user's word after creation |
| **Tombstone** | A soft-deleted record (has `deletedAt` set); propagated via sync to other devices, then garbage-collected |
| **Explicit-null PATCH** | PATCH semantics where an absent field means "don't change" and a `null` field means "clear this value" |
| **OpenAPI spec** | Machine-readable API contract (`api/openapi.yaml`); source of truth for request/response shapes |
| **LWW** | Last-write-wins — conflict resolution strategy where the record with the latest `updatedAt` wins |

---

## Further Reading

- **OpenAPI spec:** `WordPower-app/api/openapi.yaml` (source of truth)
- **Swagger UI:** available at `/swagger-ui.html` when running the backend locally
- **Contract testing:** [[TESTING_STRATEGY#4. Contract Testing]] — how spec, backend, and frontend SDK are verified to agree
- **Sync protocol:** [[LOCAL_FIRST_ARCHITECTURE#5. How the Sync Works]] — full sync architecture
