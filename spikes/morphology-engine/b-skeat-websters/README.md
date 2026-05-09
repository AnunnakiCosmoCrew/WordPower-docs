# Spike B — Skeat / Webster's 1913 extraction

**Question:** Can a public-domain dictionary serve as the etymology / classical-coverage layer for the root-families engine?

**Architecture context:** [`ROOT_FAMILIES_ENGINE.md` §7 Spike B](../../../docs/architecture/ROOT_FAMILIES_ENGINE.md#spike-b--skeat--websters-1913-extraction)

**Estimate:** 5 points (~1 day)

## Method

1. Source Webster's 1913 cleaned XML (multiple GitHub mirrors exist; pick one with a permissive licence) into `data/`.
2. Source Skeat 1882 (Project Gutenberg or archive.org) into `data/`.
3. Build a sample extraction script that parses 200 random entries into:
   ```json
   { "word": "...", "etymology": "...", "root": "...", "source_language": "Latin|Greek|Germanic|..." }
   ```
4. Run all 51 test words from [`ROOT_FAMILIES_SPIKE.md` §6](../../../docs/architecture/ROOT_FAMILIES_SPIKE.md#6-50-word-manual-sanity-check) through the extractor.
5. Run the modern-coinage probe set: `cyber`, `internet`, `nanotech`, `bitcoin`, `email`, `selfie`, `podcast`, `webinar`, `hashtag`, `meme`.
6. Compare etymology richness vs Wikipedia roots data on the overlap.

## Acceptance criteria

- [ ] ≥ 90% coverage on classical test words
- [ ] ≥ 8/10 modern coinages cleanly flagged as "not found" (clean failure mode, not silent wrong answer)
- [ ] Etymology field richer than Wikipedia roots data on ≥ 70% of overlap

## Output

- `data/websters-1913.xml` (or compressed equivalent) — source XML
- `data/skeat-1882.txt` — Project Gutenberg plaintext
- `scripts/extract_websters.py` — XML → JSON extraction
- `scripts/extract_skeat.py` — text → JSON extraction
- `scripts/measure.py` — runs test set + modern probe
- `results/test-set-results.json`
- `results/modern-probe-results.json`
- `results/etymology-comparison.md` — Skeat/Webster's vs Wikipedia roots, per-word
- `FINDINGS.md` — written conclusion against acceptance criteria
