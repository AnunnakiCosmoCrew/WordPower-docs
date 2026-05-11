# Spike D — Gemini 2.5 Flash vs Haiku 4.5 vs Sonnet 4.6

Same prompt (Spike C `prompt.md`), same 81-word test set (51 test + 30 adversarial), same scoring rubric.

## Headline numbers

| Metric | Haiku 4.5 | Sonnet 4.6 | Gemini 2.5 Flash | Threshold |
|---|---|---|---|---|
| Accuracy (strict) | 93.8% | 97.9% | 97.9% | ≥ 85% |
| Accuracy (weighted) | 95.8% | 99.0% | 97.9% | informational |
| Trap refusal | 10/10 | 10/10 | 10/10 | ≥ 8/10 |
| Multi-layer correct/partial | 90.0% | 80.0% | 90.0% | informational |
| Spike cost (81 calls) | $0.2339 | $0.7005 | $0.1649 | — |
| Projected top-30k cost | $86.61 | $259.46 | $61.09 | ≤ $200 |

## Per-decision-rule verdict

From [`d-model-survey/README.md` § Acceptance criteria](README.md):

**SWITCH to Gemini 2.5 Flash.** Exceeds Haiku 4.5's quality (97.9% vs 93.8%) at ≤ Haiku's cost (Gemini $$61.09 ≤ Haiku $$86.61 for top-30k).

## Per-word disagreements (common test words)

| Word | Haiku | Sonnet | Gemini |
|---|---|---|---|
| `diagnose` | WRONG | CORRECT | CORRECT |
| `description` | PARTIAL | PARTIAL | CORRECT |
| `inscription` | PARTIAL | CORRECT | CORRECT |
| `memory` | CORRECT | CORRECT | NOT_FOUND |
