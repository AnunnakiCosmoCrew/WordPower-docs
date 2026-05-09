# Spike: Browser Extension Stack — Research Findings

> Addresses GitHub issue [#419](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/419) (sub-issue of [#391](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/391) — reduce capture friction).
> Date: 2026-05-09 (migrated from `WordPower-app/docs/spikes/WP-419-extension-stack-spike.md`; original spike completed earlier in Phase 4).

Decides how a "save the selected word to my notebook" browser extension is built and authenticated before we commit to implementation.

---

## Decision summary

| Question | Decision |
| --- | --- |
| Cross-browser approach | **WebExtensions API + Manifest V3**, single codebase for Chrome / Edge / Firefox; Safari deferred to a follow-up |
| Auth | **Firebase Web SDK in the extension**, `signInWithPopup` (Google) on first run; reuse the user's `getIdToken()` per request |
| Backend API | **Reuse `POST /api/words`** — no extension-specific endpoint |
| Build tooling | **Vite + `@crxjs/vite-plugin`**, vanilla TS (no Flutter web component) |
| v1 effort | **~5 story points** (see breakdown below) |

## 1. Cross-browser approach — MV3 WebExtensions

Chrome enforces Manifest V3; Edge tracks Chrome; Firefox 115+ ships MV3 with a few well-known divergences (`browser.*` vs `chrome.*`, event-page vs service-worker background, slightly different `host_permissions` handling). All four targets (Chrome, Edge, Firefox, Safari) accept a single `manifest.json` with minor per-target tweaks generated at build time.

Safari is the outlier: it requires wrapping the WebExtension in an Xcode project and shipping through the App Store. We defer Safari to a follow-up — it adds Apple-developer-account cost and review latency that aren't justified for v1, and our user base is web-first.

**Permissions for v1:** `activeTab` (read selection on user gesture), `storage` (persist auth state), `https://api.wordpower.app/*` host permission for the API call. No `tabs`, no broad host permissions — keeps the store-review surface minimal.

## 2. Auth flow — Firebase ID token, reused

Backend already validates `Authorization: Bearer <Firebase ID token>` via [FirebaseAuthenticationFilter](https://github.com/AnunnakiCosmoCrew/WordPower-app/blob/main/backend/src/main/java/com/wordpower/api/auth/FirebaseAuthenticationFilter.java). The extension can use the same mechanism with **no backend changes**.

- **First run**: popup shows "Sign in with Google". Use Firebase Web SDK `signInWithPopup(GoogleAuthProvider)` — works inside MV3 popups (the auth window is a regular tab, not the extension's own context).
- **Storage**: use Firebase's `indexedDBLocalPersistence`, which writes to IndexedDB scoped to the extension origin (`chrome-extension://<id>` / `moz-extension://<id>`). This is **not** the WebExtensions `chrome.storage.local` API — if we ever need to migrate to that (e.g. for cross-context sharing), we'd write a custom Firebase persistence adapter against `chrome.storage.local` explicitly. Fall back to in-memory persistence if IndexedDB in the MV3 service worker proves flaky (known quirk).
- **Per-request**: call `auth.currentUser.getIdToken()` — the SDK handles the refresh transparently. Tokens are 1h; SDK refreshes ~5 min before expiry.
- **Account linking**: same Google account → same `User` row on the backend (already keyed on Firebase UID). No extra UX needed for v1.
- **Sign out**: explicit "Sign out" in the popup; clears extension storage and Firebase persistence.

**Why not a long-lived API key?** Would require a new endpoint, a key issuance UI in the main app, and our own revocation story. Reusing Firebase auth is strictly less code and inherits revocation / token-rotation for free.

## 3. Backend API — reuse `POST /api/words`

The parent issue text says "reuse existing `/api/notebook` endpoint or extension-specific". The actual capture endpoint is [`POST /api/words`](https://github.com/AnunnakiCosmoCrew/WordPower-app/blob/main/api/openapi.yaml) — `/api/notebook/*` is read-only metadata (domain counts). The reuse target is `POST /api/words`.

Behaviour we already get for free:

- Server-side normalisation (trim + lowercase) → idempotent capture.
- Duplicate handling: `409 Conflict` with a `Problem+json` body. The extension treats 409 as success ("already in your notebook") and shows a non-error confirmation.
- Async enrichment: response returns the row in `status: "new"`. The extension doesn't need to wait — show "Saved" and close.

**CORS**: `cors.allowed-origins` currently only allows the web app. The extension's `Origin` is `chrome-extension://<id>` / `moz-extension://<id>`. Two paths:

1. Add the extension origins to `cors.allowed-origins` once IDs are known.
2. Issue the request from the **background service worker** under `host_permissions` for the API host. The request is still cross-origin, but extension-privileged fetches granted via `host_permissions` bypass normal web-page CORS enforcement — the browser does not require the backend's `Access-Control-Allow-Origin` to list the extension origin.

Pick **(2)**. Avoids coupling the backend CORS allow-list to extension build artefacts (extension IDs differ per-channel and per-browser) and works identically across browsers.

## 4. Build tooling — Vite + `@crxjs/vite-plugin`

Options considered:

| Option | Verdict |
| --- | --- |
| Vanilla JS, no bundler | Rejected — no TS, no HMR, manual manifest mgmt. |
| Webpack + `webextension-toolbox` | Works but slower DX; community is migrating off. |
| **Vite + `@crxjs/vite-plugin`** | **Picked.** Fast HMR for content/popup scripts, MV3-aware, generates per-target manifests. |
| Flutter web component | Rejected. ~2 MB baseline bundle for what is a popup with one button + one text field; no MV3 service-worker story; would block on Flutter web's IndexedDB limitations in extension contexts. |

Stack: **TypeScript + Vite + `@crxjs/vite-plugin` + Firebase Web SDK (modular)**. UI in plain HTML/CSS or a tiny framework (Preact ~3 kB) — not React. No state management library; the popup is two screens.

Repo layout: new `extension/` sibling to `backend/` and `frontend/`, own `package.json`, own CI job (lint + typecheck + build artefact).

## 5. v1 implementation effort estimate

Rough breakdown for the v1 sub-issue (to be filed after this spike merges):

| Slice | Estimate |
| --- | --- |
| Scaffold `extension/` (Vite + crxjs + TS + CI) | 1 |
| Firebase auth in popup + storage persistence | 2 |
| Content script: capture selected word + right-click menu | 1 |
| `POST /api/words` from background worker, success/duplicate/error UX | 1 |
| Per-target manifest (Chrome, Edge, Firefox) + smoke-test in each | 1 |
| Raw sum | 6 |
| **Total (Fibonacci-rounded down to nearest point)** | **5** |

Excluded from v1, tracked separately:

- Safari packaging (Xcode wrapper + App Store).
- Store listing assets (icons, screenshots, descriptions).
- Telemetry (`POST /api/telemetry/events` from the extension).
- Multi-word selection / sentence capture.

## Re-evaluation triggers

- Chrome MV3 policy changes that block Firebase Web SDK usage in service workers (low probability, but the SDK has open issues around persistence in MV3 contexts — re-test before v1 starts).
- Backend pivots away from Firebase auth → revisit auth section.
- Demand for Safari before v1 ships → bump Safari into v1 scope (+2 pts).
