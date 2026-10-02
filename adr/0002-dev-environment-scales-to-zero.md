# ADR 0002 — The dev Cloud Run service scales to zero

**Status:** Accepted
**Date:** 2026-09-30
**Deciders:** @mertyertugrul
**Tracking:** WordPower-app#1063 · PR WordPower-app#1064
**Supersedes:** the always-on dev setting from WP-895 (2026-05-22), for dev only

## Context

`wordpower-api-dev` ran with `autoscaling.knative.dev/minScale: "1"` and
`run.googleapis.com/cpu-throttling: "false"` (WP-895). The reason was real: a
2026-05-22 on-device iOS test session hit 125 s+ tail latencies on the first request
after scale-to-zero, and HikariCP / the Firebase token verifier were believed to need
background CPU.

The 2026-09-30 cost audit showed what that costs. With zero requests in six hours the
service still billed a full always-on vCPU, and its live DB connection kept the dev
Neon endpoint from autosuspending:

| Item | Cost / month (pre-VAT) |
| --- | --- |
| Cloud Run `wordpower-api-dev` (always-on vCPU + memory) | ~$52 |
| Neon dev endpoint that never suspends | ~$32 |

Dev is used only by `pr-preview.yml` reviewers and occasional manual on-device testing.

## Decision

`service-dev.yaml` sets `minScale: "0"` and `cpu-throttling: "true"`. Prod
(`service-prod.yaml`) is unchanged: `minScale: "1"`, `cpu-throttling: "false"`.
*(Superseded by [ADR 0003](0003-prod-request-based-billing-external-job-triggers.md) on
2026-10-02 for prod's CPU setting: prod now runs `cpu-throttling: "true"`. `minScale: "1"`
stands.)*

## Consequences

- **Cold start:** measured 2026-09-30 after merge: the first request after idle took
  **about 120 s**, not the 22–28 s assumed when this ADR was drafted. Tomcat is up after
  ~19 s, but the startup probe only passes ~120 s after instance start because the
  dictionary seed loaders (`CefrWordMapLoader` ~49 s, `WordNetDictionarySeedLoader`
  ~49 s) run on the main thread first. This matches the 125 s+ latencies that led to
  WP-895. `pr-preview.yml` points its web build at dev with a 60 s API timeout, so the
  first preview request after idle times out; a retry succeeds once the instance is up.
  Startup-CPU boost stays on. Follow-up: [WordPower-app#1066](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/1066) (make the seed loaders non-blocking, or
  raise the preview timeout). Decision 2026-09-30: accept the failed first preview request meanwhile.
- **Background jobs do not run on dev** while it is scaled to zero
  (`NightlyNotificationScheduler`, `EnrichmentBackfillService`). Acceptable for dev; prod
  keeps its warm instance and still runs them. *(Superseded by
  [ADR 0003](0003-prod-request-based-billing-external-job-triggers.md): prod no longer runs
  them in-process; Cloud Scheduler triggers them over HTTP. Dev has the HTTP endpoints too
  but no Scheduler job.)*
- **Savings:** ~$84/month (~$52 Cloud Run + ~$32 Neon), plus the Neon dev endpoint now
  autosuspends.
- **Deploy path:** merging to `main` runs `backend-deploy.yml`, dev then prod with the
  same SHA. Prod's manifest is unchanged, so prod gets an identical revision.
- **Reversal:** if dev testing needs a warm instance again, set `minScale: "1"` in
  `service-dev.yaml` or, for one session, `gcloud run services update wordpower-api-dev
  --min-instances=1` and revert afterwards so the manifest stays the source of truth.

## Alternatives considered

1. **Keep always-on, cheaper sizing.** Does not stop the Neon endpoint from staying awake.
2. **Scale to zero with a scheduler keep-alive.** Same cost as always-on, plus an
   undocumented moving part (SliceFocus had exactly this; removed in MER-399).
