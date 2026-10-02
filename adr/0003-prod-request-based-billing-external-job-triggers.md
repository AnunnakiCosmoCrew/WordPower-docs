# ADR 0003 — Prod Cloud Run on request-based billing, periodic jobs triggered by Cloud Scheduler

**Status:** Accepted
**Date:** 2026-10-02
**Deciders:** @mertyertugrul
**Tracking:** WordPower-app#1071 · PRs WordPower-app#1072, #1074
**Supersedes:** the lines of [ADR 0002](0002-dev-environment-scales-to-zero.md) saying prod
keeps always-on CPU (`cpu-throttling: "false"`) and runs the background jobs in-process

## Context

`wordpower-api-prod` ran with `minScale: "1"` and `cpu-throttling: "false"` (always-on CPU,
WP-895). The September 2026 invoice showed what that costs: about ₺2,360 a month before VAT
for 77 requests in 30 days, because always-on CPU bills every second the instance is up,
whether or not it serves anything.

The obvious fix, `cpu-throttling: "true"` (CPU billed only while a request is in flight), was
not safe on its own. Prod runs two `@Scheduled` jobs on its warm instance: hourly push
notifications and a 5-minute enrichment backfill. With throttled CPU, an idle instance gets
almost none between requests, so both would run late or not at all, and the notification job
does not catch up a missed hour.

Scaling prod to zero instead is not an option yet: the cold start is about 120 s
([WordPower-app#1066](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/1066)).

## Decision

1. **Trigger the jobs over HTTP.** A property `wordpower.jobs.trigger` selects `in-process`
   (default: the old `@Scheduled` triggers, kept for local runs and tests) or `external`. In
   `external` mode `POST /internal/jobs/notifications` and `/internal/jobs/enrichment-backfill`
   run the same job methods synchronously and answer 204. The job logic did not change.
2. **Authenticate with a Google ID token.** The endpoints sit behind their own Spring Security
   chain and accept only a Google-signed token (issuer `https://accounts.google.com`) whose
   audience is the service URL and whose verified email is the `jobs-invoker` service account.
   Empty configuration refuses every request. The Cloud Run service itself stays public and the
   application verifies the token, so `jobs-invoker` holds no IAM roles.
3. **Cloud Scheduler drives them.** `wp-prod-notifications` (`0 * * * *`, `Etc/UTC`) and
   `wp-prod-enrichment-backfill` (`*/5 * * * *`), each with a 60 s attempt deadline and up to
   two retries. The HTTP backfill is bounded to a 30 s time budget so it ends inside prod's 60 s
   request timeout.
4. **Prod switches to `cpu-throttling: "true"`** with `WORDPOWER_JOBS_TRIGGER=external`.
   `minScale: "1"` is kept so first traffic is not gated on a cold start.

## Consequences

- **Cost:** CPU is billed only while a request is in flight. Expected prod cost drops to about
  ₺600–800 a month (a saving of roughly ₺1,600–1,750). This is an estimate; the measured
  result is recorded on WordPower-app#1071 after the 48-hour billing check.
- **Jobs now depend on Cloud Scheduler** and on the Cloud Run service being reachable. A paused
  or broken Scheduler job means no notifications, with no in-JVM fallback in `external` mode.
- **Work after a response is sent is best-effort.** Async enrichment (Pass 1.5 / Pass 2) and
  other post-response work run only while some request holds the CPU, so they may lag until the
  next request. HikariCP housekeeping likewise runs only during requests (the observation behind
  WP-895); the latency before and after the change is recorded on #1071.
- **Overlapping notification runs can double-send.** The per-day `notification_log` check
  protects a retry after a run has finished, not two runs at the same time. The same exposure
  already existed across instances; tracked in
  [WordPower-app#1073](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/1073).
- **Dev** exposes the same endpoints (`external`) so they can be tested there, but has no
  Scheduler job: it scales to zero, so its jobs still do not run (ADR 0002).
- **Rollback:** pause both Scheduler jobs, revert the prod manifest change and let the deploy
  run. Prod returns to in-process scheduling and always-on CPU.

## Alternatives considered

1. **Flip `cpu-throttling` only.** Rejected: both jobs would starve (see Context).
2. **Keep always-on CPU.** Rejected: about ₺2,360 a month for 77 requests.
3. **Scale prod to zero.** Blocked by the ~120 s cold start (#1066); revisit when it is fixed.
4. **Run the jobs as Cloud Run Jobs or a separate worker.** More moving parts and a second
   deployable for two small jobs; the HTTP trigger reuses the existing service and image.
