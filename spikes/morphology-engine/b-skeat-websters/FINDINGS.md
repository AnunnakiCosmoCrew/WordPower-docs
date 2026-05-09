# Spike B — Skeat / Webster's 1913 Findings

**Date:** 2026-05-09
**Issue:** [AnunnakiCosmoCrew/WordPower-app#521](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/521)
**Architecture context:** [`ROOT_FAMILIES_ENGINE.md` §7 Spike B](../../../docs/architecture/ROOT_FAMILIES_ENGINE.md#spike-b--skeat--websters-1913-extraction)

## TL;DR

**Webster's 1913 (via GCIDE) passes all three acceptance criteria.** Use it as the etymology overlay layer.

| Metric | Threshold | Actual | Verdict |
|---|---|---|---|
| Coverage on test set (strict) | ≥ 90% | **92.2%** (47/51) | **PASS** |
| Coverage on test set (with stem-match) | — | 98.0% (50/51) | informational |
| Modern coinage clean-fail | ≥ 8/10 | **10/10** | **PASS** |
| Etymology richness vs Wikipedia roots | ≥ 70% | **93.6%** (44/47) | **PASS** |

**Decision-matrix landing:** [§9](../../../docs/architecture/ROOT_FAMILIES_ENGINE.md#9-decision-criteria--how-to-pick-after-spikes) row 5's "drop the etymology overlay" condition (Skeat coverage < 60%) is **not triggered** — we are well above 60% and well above the spike's own 90% bar. The etymology-overlay layer in the architecture stays.

**Source pivot:** the spike was originally scoped against **Skeat 1882** + **Webster's 1913**. Skeat 1882's only digital sources are archive.org OCR'd scans, which proved too noisy for reliable extraction (systematic R→B confusion, missing letters, two-column page merge). The spike pivoted to **GCIDE 0.54** (the GNU-maintained Webster's 1913 + supplements) as the cleaner production-shippable source. See [§ Skeat investigation](#skeat-investigation-pivot-rationale) below.

## Method

- **Source:** [GCIDE 0.54](https://ftp.gnu.org/gnu/gcide/gcide-0.54.tar.xz) — GNU Collaborative International Dictionary of English. Maintained derivative of Webster's 1913 with structured XML-like markup (`<ent>`, `<ety>`, `<ets>`, `<grk>`, `<source>` tags). Per-letter files `CIDE.A` through `CIDE.Z`.
- **Index built:** `{lowercase_headword: [{headword, pos, etymology:{...}, source}, ...]}`. **124,155 entries** parsed across 26 letter files; **108,152 distinct lowercase headwords**; **55,266 (44.5%)** have explicit `<ety>` blocks. Source distribution: 1913 Webster's = 108,940; Webster 1913 Suppl. = 3,796; PJC supplement = 2,224; WordNet 1.5 = 7,949.
- **Test set:** 51 words from [`ROOT_FAMILIES_SPIKE.md` §6](../../../docs/architecture/ROOT_FAMILIES_SPIKE.md#6-50-word-manual-sanity-check) (shared with Spike A; copied to [`data/test-set.json`](data/test-set.json)).
- **Modern probe:** 10 post-1913 coinages from issue #521: `cyber`, `internet`, `nanotech`, `bitcoin`, `email`, `selfie`, `podcast`, `webinar`, `hashtag`, `meme`. Encoded at [`data/modern-probe.json`](data/modern-probe.json) with first-known-coined dates.
- **Coverage scoring:**
  - **STRICT** = exact `<ent>WORD</ent>` match (case-insensitive lowercased key).
  - **STEM** = no strict match, but a 5-char-prefix-shared headword exists (e.g. `omnivore` matches `Omnivorous`).
  - **MISS** = neither.
  - The 90% acceptance check uses **strict** coverage (conservative); inclusive coverage is reported alongside.
- **Modern-probe scoring:**
  - **CLEAN_FAIL** = no strict match in any source.
  - **FOUND_IN_SUPPLEMENT** = strict match exists but only in a post-1913 source (`PJC`, `WordNet 1.5`, etc.) — counts as "1913 didn't know it" (still a clean fail for our purpose).
  - **FOUND_IN_1913** = strict match in `1913 Webster` or `Webster 1913 Suppl.` — would be a silent wrong answer.
- **Richness scoring (vs Wikipedia roots baseline):** Wikipedia roots data provides per-root `{meaning, language, examples}`. GCIDE provides per-word prose etymology. GCIDE is **richer** for a word if its etymology block contains ANY of:
  - ≥ 1 `<ets>` source-form token (a chain of ancestor forms).
  - ≥ 1 `<grk>` Greek-source token.
  - A compound morpheme breakdown (`+` in the etymology body, e.g. `Photo- + -graph`).
  - Substantive prose (≥ 30 chars) with ≥ 1 detected language abbreviation.

  Words missing from GCIDE entirely score `not richer`. The percentage is over the overlap (47 strict + stem hits, common-category only).

## Results

### Headline numbers

```
coverage strict           47/51 =  92.16%   PASS  (≥90% required)
coverage inclusive        50/51 =  98.04%   informational
modern probe clean-fail   10/10 = 100.00%   PASS  (≥8/10 required)
etymology richness        44/47 =  93.62%   PASS  (≥70% required)
```

### Coverage breakdown

| Coverage | Count | Words |
|---|---|---|
| STRICT | 47 | (all classical test words except below) |
| STEM | 3 | `cardiology` → `Cardia`; `xenophobia` → `Xenopterygii`; `omnivore` → `Omnivagant`/`Omnivora`/`Omnivorous` |
| MISS | 1 | `television` (coined ~1907; pre-dates GCIDE supplements that include it) |

The stem matches are mixed:
- `cardiology` ↔ `Cardia` — same root, etymology gives Greek `kardia` (heart). **Useful.**
- `xenophobia` ↔ `Xenopterygii` — both share `xeno-` (strange/foreign) root. **Coincidental but the root is reachable.**
- `omnivore` ↔ multiple `Omni-` entries — the noun *omnivore* itself is missing but the family is well-represented (`Omnivora`, `Omnivorous`). **Useful.**

### Modern probe

All 10 modern coinages are absent from 1913 proper:

| Coined | Word | Outcome |
|---|---|---|
| 1948 (Wiener) | `cyber` | CLEAN_FAIL |
| 1974 | `internet` | CLEAN_FAIL |
| 1986 | `nanotech` | FOUND_IN_SUPPLEMENT (PJC; would be clean-fail in 1913 proper) |
| 2008 | `bitcoin` | CLEAN_FAIL |
| 1979 | `email` | CLEAN_FAIL |
| 2002 | `selfie` | CLEAN_FAIL |
| 2004 | `podcast` | CLEAN_FAIL |
| 1998 | `webinar` | CLEAN_FAIL |
| 2007 | `hashtag` | CLEAN_FAIL |
| 1976 (Dawkins) | `meme` | CLEAN_FAIL |

`nanotech` was added to GCIDE later via Patrick Cassidy's PJC supplement — but the entry is correctly tagged as a non-1913 source, so a runtime engine can filter for `source == "1913 Webster"` and treat it as unknown. **Zero silent wrong answers.**

### Etymology richness — examples

GCIDE consistently provides **richer** etymology than Wikipedia roots' flat `{meaning, language, examples}` catalog:

| Word | Wikipedia baseline | GCIDE etymology |
|---|---|---|
| `transport` | `port-` → carry (Latin) | `F. transporter, L. transportare; trans across + portare to carry.` |
| `philosophy` | `phil-/sophi-` → love/wisdom (Greek) | `OE. philosophie, F. philosophie, L. philosophia, fr. Gr. filosofi`a` |
| `pediatric` | `paed-` → child (Greek) | `Gr. pais, paidos, child + iatreia healing.` |
| `manuscript` | `manu-/scrip-` → hand/write (Latin) | `LL. manuscriptum, fr. L. manus hand + scribere, scriptum, to write.` |
| `microscope` | `micr-/scop-` → small/look (Greek) | `Micro- + -scope.` |
| `autograph` | `auto-/graph-` → self/write (Greek) | `F. autographe, fr. Gr. autographos written with one's own hand: cf. autos self + graphein to write.` |

GCIDE adds: per-word entry (Wikipedia indexes by root, not by word); the borrowing chain (English ← French ← Latin ← Greek); morpheme decomposition with literal meanings; cross-references to morpheme entries.

The 3 "not richer" cases are real gaps:
1. `diagnose` — entry exists but `<ety>` block is empty.
2. `antibiotic` — only present in PJC supplement; no etymology block.
3. `synchronize` — etymology is `Gr. <?/.` (just "Greek" + an unprintable Greek token). Too sparse to be meaningfully richer.

Full per-word comparison: [`results/etymology-comparison.md`](results/etymology-comparison.md).

## Verdict against §9 decision matrix

Quoting the relevant row of [`ROOT_FAMILIES_ENGINE.md` §9](../../../docs/architecture/ROOT_FAMILIES_ENGINE.md#9-decision-criteria--how-to-pick-after-spikes):

> | Skeat coverage < 60% on classical | Drop the etymology overlay; use Wikipedia roots' etymology field instead. |

This row's condition is **not triggered**. GCIDE coverage on the classical test set is 92.2% strict / 98.0% inclusive — well above the 60% drop threshold. **The etymology-overlay layer stays in the architecture.**

Combined with Spike A's verdict (MorphyNet < 70% — drop as primary), the architecture is now:

```
L1 primary       : gated on Spike C (LLM)
L2 etym overlay  : GCIDE (Webster's 1913 + supplements)   ← validated by Spike B
L3 fallback      : Wikipedia roots                         (already validated)
```

If Spike C also fails, the architecture defaults to L0 (root-catalog highlighting only). GCIDE remains useful as the etymology source for L0's tooltips.

## Risks surfaced

1. **GCIDE etymology coverage is 44.5% across all entries** — many GCIDE entries (function words, compounds, modern terms in PJC supplement) lack `<ety>` blocks. For our 51-word classical test set this isn't a problem (high-frequency classical words *do* have etymologies); for a top-10k production bundle, expect a meaningful fraction with no etymology.
2. **Greek source tokens use unprintable placeholder `<?/`.** GCIDE marks Greek text using a special encoding that displays as `<?/` after tag-stripping. A production parser needs to handle this — either by reading the raw `<grk>` block contents (which contain a romanization like `kardi`a` or `filosofi`a`) or by surfacing the romanization separately. Not a blocker; just a parser-engineering note.
3. **Stem-matching is a fudge.** 3 of the 47+3 hits are stem-only (`Cardia`/`Xenopterygii`/`Omnivagant`). Stem-matching is fine for the spike's coverage measurement but is **not** a sound engine primitive — `xenophobia` accidentally matching `Xenopterygii` is a coincidence of shared `xeno-` prefix, not a reliable signal. A production engine should use exact-match or hand-curated alias mapping.
4. **Modern coinages' "FOUND_IN_SUPPLEMENT" hits.** `nanotech` is in PJC. A production engine that wants 1913-only behaviour needs to filter `source == "1913 Webster"` (and possibly `Webster 1913 Suppl.`) at query time. Cheap to do; flag for the build pipeline.
5. **Bundle size for production not measured.** This spike's acceptance criteria don't include a bundle-size check (the engine treats GCIDE as an etymology overlay, not the primary lookup layer). For production: the GCIDE source is ~14 MB compressed; a slim etymology-only slice (headword + raw `<ety>` body, no definitions) for the top-10k frequency list would compress much smaller. Worth a follow-up measurement when designing the production bundle.

## Skeat investigation — pivot rationale

The spike was originally scoped against both Skeat 1882 and Webster's 1913. **Skeat was investigated but skipped** because no clean digital source exists.

Investigation:
- Skeat's *Etymological Dictionary of the English Language* (1882) is **not** on Project Gutenberg.
- Available sources are archive.org scans with OCR'd text (`in.ernet.dli.2015.83588`, `anetymologicald01skeagoog`, etc.).
- OCR quality is unreliable on the 1880s typesetting:
  - Systematic letter confusions: `BIOGRAPHY` rendered as `BIOGBAPHY`, `DIALECT` as `DIAliDCT`, `DIAL` as `DIAX`, `DIAPER` as `DIALER`.
  - Two-column page layout occasionally merged into adjacent column text mid-entry (visible in the `ISLAND` entry).
  - Greek and special characters often rendered as ASCII garbage.
- Of 31 sample test-set headwords looked up by exact match `^WORD,`, only 3 matched.

A fuzzy-matching extractor (Levenshtein-tolerant, with OCR confusion-pair handling) could probably extract Skeat usefully — but the work is not worth doing because:
- The extracted data would still be confounded by OCR noise; spike measurements would mix coverage gaps with extraction failures.
- For production deployment, we'd need clean structured data anyway. GCIDE provides that; Skeat doesn't.

GCIDE was selected as the cleaner Webster's 1913 source. It satisfies the spike's underlying question — "can a public-domain dictionary serve as the etymology overlay layer?" — at least as well as Skeat would have, with measurable data.

## Reproducing

```sh
cd spikes/morphology-engine/b-skeat-websters
./scripts/download.sh                # fetches gcide-0.54.tar.xz from FSF FTP
python3 scripts/extract_gcide.py     # builds gcide-index.json + extract-stats.txt
python3 scripts/measure.py           # writes results/{test-set,modern-probe,coverage}.json
                                     # + results/etymology-comparison.md
```

All inputs and outputs are committed except `data/gcide-0.54.tar.xz` (~14 MB, gitignored), `data/gcide-0.54/` (~38 MB extracted, gitignored), and `data/gcide-index.json` (derived, gitignored). `download.sh` re-fetches.

## License note

GCIDE is licensed under [GPL 3.0+](https://www.gnu.org/licenses/gpl-3.0.html) (the GCIDE project is GNU-maintained). The underlying 1913 Webster's text is public domain. **GPL on the data file requires careful handling for app distribution** — strict reading is that the dictionary corpus's GPL would propagate to anything statically linking it. Mitigations:
- Treat the GCIDE bundle as a *data file* loaded at runtime, not as linked code.
- Distribute the bundle separately (e.g., download-on-first-use), with the GCIDE COPYING notice.
- Or extract per-word etymology into a smaller derivative bundle, license-tagged with attribution.

Worth confirming the licensing posture with legal review before shipping a GCIDE-derived bundle to end users. This isn't a blocker for the spike but is a flag for the production pipeline.
