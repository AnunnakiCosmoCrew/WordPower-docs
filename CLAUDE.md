# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WordPower is a personal word notebook app built with Flutter (Web → iOS → Android). Users collect English words they encounter in daily life, and the app enriches them with definitions, pronunciation, CEFR levels, and semantic domains — then helps users learn through quizzes, flashcards, spelling drills, and spaced repetition.

**This repository (`WordPower-docs`) contains project documentation only.** The app lives in a separate repo.

## Repository Map

| Repo | Purpose | Push to main? |
|------|---------|---------------|
| `AnunnakiCosmoCrew/WordPower-docs` (this repo) | Project docs, specs, competitive analysis | Yes — direct push |
| `AnunnakiCosmoCrew/WordPower-app` | Monorepo: Spring Boot backend + Flutter frontend | No — branch + PR only |

## Git Workflow (Trunk-Based Development)

`main` is the single integration branch. All code changes land via short-lived feature branches and squash-merge PRs.

### Docs repo (this repo)

Documentation changes are committed and pushed directly to `main`. No branch or PR needed.

### App repo (`AnunnakiCosmoCrew/WordPower-app`)

> The `WordPower-app` monorepo was created at the start of Phase 2 (April 2026). The conventions below apply from Phase 2 onwards.

**Never push directly to main** — always create a branch and PR, even for one-line changes.

#### Branch naming

`feature/wp-{N}-{slug}` where `{N}` is the GitHub Issue number (lowercase, e.g., `feature/wp-42-quick-capture-screen`).

#### Commit message format

`WP-{N} <type>[(<scope>)]: description`

Types: `feat`, `fix`, `chore`, `test`, `docs`, `refactor`

Examples:
- `WP-42 feat(notebook): add quick-capture word entry screen`
- `WP-15 fix(srs): correct interval calculation for hard-rated words`
- `WP-8 test: reproduce dictionary lookup timeout bug`

#### Issue Workflow — Follow for Every GitHub Issue

1. **Add issue to the project board** when creating via `gh issue create` (it does NOT auto-add). Use `gh project item-add <PROJECT_NUMBER> --owner AnunnakiCosmoCrew --url <issue-url>`. Then set board fields: estimate, status, priority, label.
2. **Set an estimate** (Fibonacci: 0, 1, 2, 3, 5, 8, 13) on the project board. Bugs are `0`.
3. **Set Model & Effort** on the project board — choose the most appropriate Claude Code model and effort level for the task. Field ID: `PVTF_lADOB9neH84BUuiWzhRw27Q`.
4. **Move ticket to "In Progress"** on the project board before writing any code.
5. **Create a feature branch** from latest `main`: `feature/wp-{N}-{slug}`.
6. **Implement and verify**: For frontend: `flutter analyze --no-fatal-infos`, `dart format --set-exit-if-changed`, `flutter test`. For backend: `./gradlew check`. All must pass.
7. **Commit** to the feature branch with a descriptive message referencing the issue number.
8. **Push and open a PR** with `Closes #NNN` in the body so the issue auto-closes on merge.

> **Do NOT skip steps 1–4.** The project board must reflect the current state of work at all times.

#### Bug Fixes — Test-Driven Bug Fixing (TDBF)

When fixing a bug, the failing test that reproduces it must be written and committed *before* the fix. Two commits on the same branch:

1. **Red commit** — test that reproduces the bug (`flutter test` will fail on this test by design; `flutter analyze` must still pass). Commit: `WP-{N} test: reproduce <bug description>`.
2. **Green commit** — the fix. All tests pass. Commit: `WP-{N} fix(<scope>): <what the fix does>`.

#### Branch Protection (planned)

- Squash merge only
- CI checks must pass before merge
- All review conversations must be resolved (reply **and** explicitly resolve threads)
- Auto-delete head branches after merge
- Force push blocked on `main`

## Project Management

- **Issue tracking**: GitHub Issues on the app repo + GitHub Projects board
- **Estimation**: Fibonacci story points (0, 1, 2, 3, 5, 8, 13) on the board's "Estimate" field
- **Architecture decisions**: Documented in `WordPower-docs` repo
