# Spike C — Cost projection for top-30k bundle

Acceptance criterion: ≤ $200 for top-30k frequency list.

Methodology: per-word cost measured on the 81-word spike (51 test + 30 adversarial)
with system-prompt caching (`cache_control: ephemeral`), then linearly extrapolated
to 30,000 words. Linear extrapolation slightly OVERestimates because cache hits
amortize better at scale than at 81 calls.

## Haiku 4.5
- Measured: 81 calls = $0.3287
- Avg per word: $0.00406
- Projected for top-30k: **$121.72** (PASS ≤ $200)

## Sonnet 4.6 (cross-validation, optional in production)
- Measured: 81 calls = $0.5029
- Avg per word: $0.00621
- Projected for top-30k: **$186.26** (PASS ≤ $200)

## Notes
- Production builds on Haiku alone meet the budget at 30k.
- Running Sonnet on every word (full cross-validation) adds Sonnet's projected cost.
- A pragmatic production cross-validation strategy: run Sonnet only on Haiku's `medium`
  / `low` confidence outputs and on a 10% random sample of `high` confidence outputs.
  Estimated overhead: 20-30% of Sonnet's full-run cost.
