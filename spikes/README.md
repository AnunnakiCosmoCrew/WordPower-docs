# Spikes

Exploratory work — measurements, prototypes, dataset evaluations — that informs architecture decisions before we commit production code.

## Convention

- **Spike code, data, and findings live here**, not in `WordPower-app`.
- Each spike has a directory: `spikes/<topic>/<slug>/`.
- The matching architecture decision doc lives at `docs/architecture/<TOPIC>.md` and links into the spike directory for raw data.
- The matching GitHub issue lives on `WordPower-app` (the app repo holds the project board) and links back to both this directory and the architecture doc.

## Why here and not in the app repo

Spikes produce *findings* (which are docs) more than they produce *shipping code*. Keeping them in the docs repo:

- Avoids polluting the app repo with throwaway exploration scripts
- Lets findings be edited directly on `main` (docs-repo workflow), no PR ceremony for measurement data
- Keeps the architecture decision and the data that backed it in one repo for future archaeology

When a spike's outcome promotes to production, the production code lands in `WordPower-app` (typically under `backend/scripts/` or similar); the spike directory remains as the historical record of how that decision was made.

## Active spikes

| Topic | Path | Issue | Architecture doc |
| --- | --- | --- | --- |
| Morphology engine — MorphyNet quality | [`morphology-engine/a-morphynet/`](morphology-engine/a-morphynet/) | TBD (sub-issue of [#385](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/385)) | [`ROOT_FAMILIES_ENGINE.md` §7 Spike A](../docs/architecture/ROOT_FAMILIES_ENGINE.md#spike-a--morphynet-quality) |
| Morphology engine — Skeat / Webster's extraction | [`morphology-engine/b-skeat-websters/`](morphology-engine/b-skeat-websters/) | TBD | [`ROOT_FAMILIES_ENGINE.md` §7 Spike B](../docs/architecture/ROOT_FAMILIES_ENGINE.md#spike-b--skeat--websters-1913-extraction) |
| Morphology engine — LLM Haiku 4.5 decomposition | [`morphology-engine/c-llm-haiku/`](morphology-engine/c-llm-haiku/) | TBD | [`ROOT_FAMILIES_ENGINE.md` §7 Spike C](../docs/architecture/ROOT_FAMILIES_ENGINE.md#spike-c--llm-haiku-45-decomposition-quality) |

(Issue numbers populated when sub-issues are filed.)

## Per-spike directory layout

```
<topic>/<slug>/
  README.md              — restates question, method, acceptance criteria
  data/                  — input datasets (gitignored if large; otherwise checked in)
  scripts/               — extraction / measurement scripts
  results/               — measurement outputs, JSON, CSV
  FINDINGS.md            — written conclusions; promoted to docs/architecture/ when stable
```
