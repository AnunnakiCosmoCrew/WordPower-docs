# Spike A — MorphyNet quality

**Question:** Can MorphyNet serve as the primary per-word decomposition source for the root-families engine?

**Architecture context:** [`ROOT_FAMILIES_ENGINE.md` §7 Spike A](../../../docs/architecture/ROOT_FAMILIES_ENGINE.md#spike-a--morphynet-quality)

**Estimate:** 3 points (~half day)

## Method

1. Download MorphyNet ([`kbatsuren/MorphyNet`](https://github.com/kbatsuren/MorphyNet)) into `data/`.
2. Filter to English derivational data; load into a lookup table.
3. Run all 51 words from [`ROOT_FAMILIES_SPIKE.md` §6](../../../docs/architecture/ROOT_FAMILIES_SPIKE.md#6-50-word-manual-sanity-check) through it.
4. Record into `results/`:
   - hit rate (% of test words found)
   - decomposition accuracy on hits (vs hand-known answer)
   - false-positive rate on the three false-root traps (`uncle`, `island`, `butter`)
5. Measure bundle size of an English-only slice (gzipped).

## Acceptance criteria

- [ ] Hit rate ≥ 80% on the test set
- [ ] Accuracy ≥ 90% on hits
- [ ] 0 false positives on the false-root traps
- [ ] Bundle slice ≤ 200 KB gzipped

## Output

- `data/morphynet-en.tsv` (or similar) — extracted English slice
- `scripts/extract_morphynet.py` — extraction + filter
- `scripts/measure.py` — runs the 51-word test
- `results/test-set-results.json` — per-word measurement
- `results/bundle-size.txt` — gzipped size of English slice
- `FINDINGS.md` — written conclusion against acceptance criteria; promotes to architecture doc decision matrix
