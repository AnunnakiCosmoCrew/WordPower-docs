# Brand & Naming

> [!summary]
> The product ships publicly as **LexiPower**. **WordPower** is the internal codename — repos, branches, commits, and issue/PR identifiers keep using it. Do not rename the codebase.

## Decision

| | |
|---|---|
| **Public brand** | LexiPower |
| **Internal codename** | WordPower |
| **Decided** | 2026-05-21 |
| **Context** | [#842 — Acquire production domain](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/842) |
| **Reason** | `wordpower.app` and `wordpower.com` were unavailable / cost-prohibitive at acquisition time. "LexiPower" preserves the "Power" suffix from the original brand identity while pairing it with *lexis* (Greek: word, vocabulary) — short, distinct, available. |

## Where each name is used

### Use **LexiPower** (public-facing surfaces)

- Domain: `lexipower.app` (apex, registered 2026-05-21 — see #842)
- App display name (Flutter `name:` in `pubspec.yaml`, iOS `CFBundleDisplayName`, Android `android:label`)
- Splash screen, app bar title, About screen
- Marketing site copy, landing page, social media
- App store listings (Apple App Store, Google Play)
- Email sender name (`support@lexipower.app`)
- User-facing legal pages (Terms, Privacy)
- Push notification titles
- Logo and brand assets

### Keep **WordPower** (internal / codebase / process)

- GitHub repositories: `WordPower-app`, `WordPower-docs`
- GitHub Project board ("WordPower" project #11)
- Branch prefix: `feature/wp-<N>-<slug>`
- Commit message prefix: `WP-<N> <type>: …`
- Issue/PR titles still reference `WP-<N>`
- Package names: `com.example.word_power` / Spring Boot package roots
- Database name, Flyway migration history, internal env vars
- CI workflow file names
- Internal documentation, design specs, ADRs (this repo)
- Slack channel names, internal Linear/Notion references

## Rationale for keeping the codename

Renaming repos, branches, packages, and migration history would be expensive churn with **zero user-visible benefit**. The "(Working Title)" tag on early docs always anticipated a public brand divergence — this is the planned split, not a rebrand of the engineering work.

## Migration checklist (LexiPower swap-in surfaces)

When wiring the new domain (#842) and beyond, update these locations to **LexiPower**:

- [ ] `frontend/pubspec.yaml` — `name:` stays `word_power` (package name), but the app display name override
- [ ] `frontend/ios/Runner/Info.plist` — `CFBundleDisplayName` → `LexiPower`
- [ ] `frontend/android/app/src/main/AndroidManifest.xml` — `android:label` → `LexiPower`
- [ ] `frontend/web/index.html` — `<title>`, `<meta name="apple-mobile-web-app-title">`, `<meta name="application-name">`
- [ ] `frontend/web/manifest.json` — `name`, `short_name`
- [ ] Splash screen text + about/settings copy
- [ ] Firebase Hosting custom domain → `lexipower.app` / `app.lexipower.app`
- [ ] Email forwarding: `support@lexipower.app` → user inbox (Cloudflare Email Routing)
- [ ] All marketing-site copy in the marketing repo (when split per #840)

## Future-proofing

If a third name is ever needed (e.g., a regional variant or a major pivot), follow the same pattern: public brand on the user-facing layer, codename frozen in the engineering layer. Do **not** chain renames into the codebase.
