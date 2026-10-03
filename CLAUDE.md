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

#### Issue workflow, bug fixes, branch protection

`WordPower-app/CLAUDE.md` and its skills (`wp-issue-start`, `wp-bug-fix`, `wp-pr-open`) are the
source of truth: worktrees, draft-first PRs, the four board fields, and the enforced checks.
Board: `gh project item-add 11 --owner AnunnakiCosmoCrew --url <issue-url>`.

## Project Management

- **Issue tracking**: GitHub Issues on the app repo + GitHub Projects board
- **Estimation**: Fibonacci story points (0, 1, 2, 3, 5, 8, 13) on the board's "Estimate" field
- **Architecture decisions**: Documented in `WordPower-docs` repo
