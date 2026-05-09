# Spike A — MorphyNet Findings

**Date:** 2026-05-09
**Issue:** [AnunnakiCosmoCrew/WordPower-app#520](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/520)
**Architecture context:** [`ROOT_FAMILIES_ENGINE.md` §7 Spike A](../../../docs/architecture/ROOT_FAMILIES_ENGINE.md#spike-a--morphynet-quality)

## TL;DR

**MorphyNet alone fails as primary decomposition source.** Three of four acceptance criteria miss by a wide margin:

| Metric | Threshold | Actual | Verdict |
|---|---|---|---|
| Hit rate on test set | ≥ 80% | **18.75%** (9/48) | **FAIL** |
| Accuracy on hits (CORRECT-only) | ≥ 90% | 100% (9/9) | PASS |
| False positives on traps | 0/3 | **1/3** (`butter`) | **FAIL** |
| Bundle gzipped | ≤ 200 KB | **2052.8 KB** | **FAIL** |

The 9 words that hit are decomposed correctly under the loose-substring rubric, but the dataset simply does not cover the test set: 39 of 48 common words are absent — including everyday vocabulary (`transport`, `export`, `dictionary`, `memory`, `predict`) and almost the entire Greek/Latin classical slice (`philosophy`, `cardiology`, `geography`, …).

**Decision-matrix landing:** §9 row 3 (`MorphyNet < 70%`) — outcome depends on Spike C. If LLM accuracy ≥ 85% → **LLM cache primary, drop MorphyNet entirely**. If LLM < 85% → row 4 (**Defer L2, ship L0 only**).

## Method

- **MorphyNet source:** [`kbatsuren/MorphyNet`](https://github.com/kbatsuren/MorphyNet) commit `378144f64df58c78db5245af19d16a511ccecf3a`, file `eng/eng.derivational.v1.tsv` (225,131 rows; 7977 KB raw).
- **Format:** 6 columns — `source target source_pos target_pos morpheme type`. The `type` column is `prefix` or `suffix` (105,639 prefixes / 119,492 suffixes), so affix orientation is explicit and didn't need to be inferred.
- **Index built:** `{target → [{source, morpheme, type, source_pos, target_pos}, …]}`. 219,410 distinct targets; 70,485 distinct sources; 5,721 multi-parent edges.
- **Decomposition algorithm:** chain-walk parent index until base reached, max depth 10, cycle-guarded. Multi-parent: first-encountered wins.
- **Test set:** 51 words from [`ROOT_FAMILIES_SPIKE.md` §6](../../../docs/architecture/ROOT_FAMILIES_SPIKE.md#6-50-word-manual-sanity-check), encoded at [`data/test-set.json`](data/test-set.json). 48 common + 3 traps (`uncle`, `island`, `butter`).
- **Scoring rubric (loose substring, four levels):**
  - **CORRECT (1.0)** — every expected_root (trailing `-` stripped) is substring in some chain node *or* edge morpheme.
  - **PARTIAL (0.5)** — at least one but not all expected roots match; chain non-empty.
  - **WRONG (0.0)** — chain produced, no expected root matches.
  - **NOT_FOUND** — word absent from MorphyNet → counts against hit rate, excluded from accuracy denominator.
- **Trap scoring:** any non-empty chain on a trap = false positive (1 of 3 failures).
- **Hit rate denominator:** 48 (common words only). Traps are excluded; they're expected to clean-refuse, not hit.
- **Accuracy threshold check:** uses CORRECT-only (PARTIAL excluded from numerator). Weighted accuracy reported alongside as informational.
- **Bundle measurement:** three formats compressed at `gzip -9`. Headline = smallest of slim TSV / JSON map.

## Results

### Headline numbers

```
hit rate                  9/48  =  18.75%   FAIL  (≥80% required)
accuracy (CORRECT-only)   9/9   = 100.00%   PASS  (≥90% required)
accuracy (weighted)       9/9   = 100.00%   (informational)
false positives           1/3   = butter    FAIL  (0/3 required)
bundle (slim TSV, gz -9)  2052.8 KB         FAIL  (≤200 KB required)
```

### Per-word breakdown — the 9 hits

| # | Word | Expected | MorphyNet chain | Score |
|---|------|----------|-----------------|-------|
| 3 | important | port- | `important → import` (`-ant` suffix) | CORRECT |
| 7 | agnostic | gnos- | `agnostic → Gnostic` (`a-` prefix) | CORRECT |
| 8 | telephone | tele-, phon- | `telephone → phone` (`tele-` prefix) | CORRECT |
| 12 | antibiotic | anti-, bio- | `antibiotic → biotic` (`anti-` prefix) | CORRECT |
| 16 | television | tele-, vis- | `television → vision` (`tele-` prefix) | CORRECT |
| 22 | democracy | dem-, crat- | `democracy → democrat` (`-cy` suffix) | CORRECT |
| 27 | synchronize | syn-, chron- | `synchronize → synchrony` (`-ize` suffix) | CORRECT |
| 39 | memorial | mem- | `memorial → memory` (`-al` suffix) | CORRECT |
| 45 | xenophobia | xen-, phob- | `xenophobia → xenophobe` (`-ia` suffix) | CORRECT |

The substring rubric is doing real work here: e.g. `democracy → democrat` contains `dem` and `crat` as substrings of an intermediate node, even though MorphyNet stopped at `democrat` (a free English stem) rather than reaching `dem-/crat-`.

### Per-word breakdown — the 3 traps

| # | Word | Outcome | MorphyNet chain |
|---|------|---------|-----------------|
| 41 | uncle | PASS | _no decomposition_ |
| 42 | island | PASS | _no decomposition_ |
| 43 | **butter** | **FAIL** | `butter → butt` (`-er` suffix) |

`butter` is the failure case. MorphyNet has it as the noun-of-agent derivation of the verb *to butt* (one who butts → butter). That's a real morphological pattern in English — but synchronic, not the etymology of the dairy product. The architecture's false-root traps want clean-refuse on dairy-`butter`'s lack of Greek/Latin roots; MorphyNet doesn't model that distinction.

### Misses (NOT_FOUND, 39 of 48)

```
transport, export, portable, prognosis, diagnose, photograph, biology, biography,
geography, geology, thermometer, microscope, autograph, cardiology, dermatology,
pediatric, philosophy, philanthropy, chronic, chronology, hydrogen, oxygen, genesis,
dictionary, predict, contradict, verdict, manuscript, description, inscription,
psychology, memory, cryptography, omnivore, herbivore, carnivore, benevolent,
malevolent, renovate
```

By category:
- **Greek/Latin classical compounds (the largest group):** `philosophy`, `geography`, `cardiology`, `dermatology`, `cryptography`, `psychology`, `chronology`, `omnivore`/`herbivore`/`carnivore`, etc. MorphyNet does not encode `philo + sophy`, `cardio + logy`, `geo + graphy`, etc. as derivational links — these are classical compounds, not English-internal derivations.
- **Latin verb stems:** `transport`/`export`/`portable`, `dictionary`/`predict`/`contradict`/`verdict`, `description`/`inscription`/`manuscript`, `memory`. MorphyNet treats these as opaque English stems; no `port-`, `dict-`, `scrib-`, `mem-` link.
- **Greek-origin nouns:** `genesis`, `prognosis`, `diagnose`, `chronic`, `hydrogen`, `oxygen`. Opaque to MorphyNet.

This is unsurprising once you see why: MorphyNet is built from Wiktionary's *English-internal* derivational links. It captures `nation → national → nationalize → nationalization`, not `geography ← Greek γεωγραφία`. For a product whose value proposition is teaching learners the Greek/Latin roots that connect words across English, MorphyNet alone is the wrong primitive.

### Bundle size

| Format | Raw KB | Gzipped KB |
|---|---:|---:|
| Raw 6-col TSV (as-shipped) | 7977.6 | 2125.9 |
| **Slim 4-col TSV** (drops POS) | 7098.2 | **2052.8** |
| JSON map (target → {s,m,t}) | 11632.4 | 2281.1 |

Slim TSV is the smallest viable runtime bundle: **2052.8 KB gzipped, 10× over the 200 KB threshold.**

Caveat to be honest about: this is just the derivational lookup layer. Adding the [§6 record schema](../../../docs/architecture/ROOT_FAMILIES_ENGINE.md) (`meaning`, `language`, `canonical_root`, `etymology`) — which MorphyNet does not provide and which a runtime engine *needs* — inflates further. The 200 KB threshold was clearly written with a curated, top-N-words bundle in mind, not the full MorphyNet corpus. A targeted slice (e.g., MorphyNet rows for the top-10k frequency list) would land much smaller, but the hit-rate failure makes that exercise pointless: the words that miss aren't rare.

## Verdict against §9 decision matrix

Quoting the relevant rows of [`ROOT_FAMILIES_ENGINE.md` §9](../../../docs/architecture/ROOT_FAMILIES_ENGINE.md#9-decision-criteria--how-to-pick-after-spikes):

> | Spike outcomes | Architecture |
> |---|---|
> | **MorphyNet < 70% + LLM ≥ 85%** | **LLM cache primary**, Skeat etymology overlay, Wikipedia fallback. Skip MorphyNet entirely. |
> | **MorphyNet < 70% + LLM < 85%** | **Defer L2.** Ship L0 only. Re-evaluate in Phase 5 with stronger models or more curated data. |

Spike A lands MorphyNet at **18.75% hit rate** — well below the 70% boundary. The architecture is therefore decided by Spike C's LLM result:

- **Spike C ≥ 85% accuracy →** drop MorphyNet entirely; LLM cache becomes primary.
- **Spike C < 85% accuracy →** defer L2 to Phase 5; ship L0 only (Wikipedia root-catalog highlighting).

Either way, MorphyNet is out as the L1 primary. It's also not promising as a *fallback* layer — its 19% coverage doesn't materially help the L0 catalog, and the false positive on `butter` is exactly the failure mode the false-root traps were designed to catch.

## Risks surfaced during measurement

1. **MorphyNet's domain is English-internal derivation.** The evaluation matrix treated MorphyNet as comparable to Wikipedia roots; in practice they're orthogonal — Wikipedia roots is a Greek/Latin root catalog with examples; MorphyNet is an English suffix/prefix chain map. The two cover almost-disjoint slices of the morphological problem.
2. **Synchronic ≠ etymological.** The `butter → butt + -er` row is correct synchronically (English does form agent nouns this way) but useless and harmful for an etymology-teaching product. A future engine that consumes MorphyNet rows would need a confidence/etymology filter.
3. **Multi-parent ambiguity is rare** (5,721 / 225,131 = 2.5%) — picking first-encountered is fine in practice; would not have moved the verdict either way.
4. **Bundle size is a non-starter.** Even if MorphyNet had 100% hit rate, 2 MB compressed for the lookup layer alone fails the mobile-bundle requirement.
5. **The 200 KB threshold itself probably wants revisiting** — it's tight even for a curated 10k-word bundle with full §6 schema. Worth flagging in the synthesis after Spikes B and C land.

## Reproducing

```sh
cd spikes/morphology-engine/a-morphynet
./scripts/download.sh        # fetches eng.derivational.v1.tsv at pinned commit
python3 scripts/extract.py   # builds parent index + extract-stats.txt
python3 scripts/measure.py   # writes results/{test-set-results,summary}.json + bundle-size.txt
```

All inputs and outputs are committed except `data/eng.derivational.v1.tsv` (~8 MB, gitignored — `download.sh` re-fetches) and `data/morphynet-en-index.json` (derived).

## License note

MorphyNet is licensed [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) — the architecture doc previously listed it as 4.0; I've left that note for now since the spike conclusion is "drop MorphyNet" anyway. If a future spike revisits MorphyNet, the license should be re-checked.
