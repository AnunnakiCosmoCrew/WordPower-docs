# Plan: Root-Families Decomposition Engine

> Follow-on to [[ROOT_FAMILIES_SPIKE]] which picked the **root catalog** (Wikipedia's "List of Greek and Latin roots in English"). This doc picks the **decomposition engine** — how the app maps any captured word to its morphological structure (prefix + root + suffix + meanings) for the Word Detail screen and the root-family browse experience.
>
> Date: 2026-05-08
> Addresses follow-on work to GitHub epic [#385](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/385).

---

## 1. Goal

When a user captures (or views) any English word, the app should show:

- **Linear morpheme breakdown** with meanings, e.g. `transportation` → `trans-` (across) + `port` (carry) + `-ation` (act of).
- **Etymology badge**: Latin / Greek / Germanic + original form (`portāre`).
- **Family link**: tap-through to the `port-` family browse screen.
- **Graceful degradation**: when a confident decomposition isn't possible, fall back to "Contains the root *X*" (L0) or no morphology section at all — **never** a wrong-looking parse.

This targets **L2 ambition** on the ladder below. L3 (graph network UI, allomorph variants UI, ambiguity warnings) is deferred to Phase 5+.

### 1.1 Ambition ladder

| Level | What user sees | Engine cost |
|---|---|---|
| L0 | "Contains root *port-* (carry)" | Already covered by [[ROOT_FAMILIES_SPIKE]] |
| L1 | Linear morpheme breakdown with meanings | The whole debate below |
| **L2 (target)** | L1 + etymology + original Latin/Greek form | L1 + Wikipedia etymology field |
| L3 | L2 + graph network + allomorph UI + ambiguity warnings | Deferred to Phase 5+ |

## 2. Full Option Matrix

Every credible option for sourcing per-word morphological decomposition. §3 eliminates, §4 keeps the live candidates.

### 2.1 Per-word decomposition databases

| Source | Coverage | Licence | Status |
|---|---|---|---|
| **CELEX2** | ~52k English lemmas, gold-standard | LDC commercial, restrictive | ❌ cost prohibitive |
| **MorphoLEX-en** | 70k words, structured root + prefix + suffix | CC BY-NC-SA 4.0 | ❌ NC clause (already eliminated [[ROOT_FAMILIES_SPIKE#3]]) |
| **MorphyNet** | ~200k forms, derivational + inflectional | CC BY-SA 4.0 | ⚠️ untested — primary spike candidate |
| **UniMorph** | Mostly inflectional | CC BY-SA | ❌ wrong shape (we need derivational) |
| **CatVar** | Categorical variation database | Free | ❌ dated, narrow coverage |

### 2.2 Public-domain dictionaries (out of copyright)

| Source | Year | Coverage | Notes |
|---|---|---|---|
| **Skeat's *Etymological Dictionary*** | 1882 | ~14k headwords, root-organized | Designed for exactly this teaching purpose |
| **Webster's Unabridged Dictionary** | 1913 | ~400k headwords with etymology | Cleaned XML mirrors on GitHub |
| **OED 1st edition** | 1884–1928 | ~400k headwords | OCR quality varies |
| **Century Dictionary** | 1889–1891 | Massive, strong etymology | Less used in modern projects |

Free to bundle, no attribution required, no NC clause, no share-alike. Known gap: post-1900 coinages (`cyber-`, `nano-`, `e-`, `bit-`/`byte-`, etc.).

### 2.3 Modern copyrighted books (curriculum guidance only)

These are **prose, not data**. Cannot be bundled directly. Useful for *which roots matter* (selection inspiration) and modern teaching consensus, not for content extraction:

- Norman Lewis, *Word Power Made Easy*
- *Vocabulary from Classical Roots* (educational series)
- Donald Ayers, *English Words from Latin and Greek Elements*
- Michael Clay Thompson, *The Word Within the Word*
- Calvert Watkins, AHD *Indo-European Roots Appendix*
- Charles Harrington Elster, *Verbal Advantage*

**Legal path for using these directly:** multi-source consensus + original phrasing + primary-source verification. Labor-intensive (~2–4 weeks for ~200 roots). Realistically substituted by an LLM that has read the same books and outputs synthesised consensus in original phrasing — see §2.5.

### 2.4 Catalog and supplement sources (already in stack)

| Source | Role | Status |
|---|---|---|
| Wikipedia "List of Greek and Latin roots" | Root catalog | ✅ adopted in [[ROOT_FAMILIES_SPIKE]] |
| Open English WordNet | Derivational link expansion | ✅ planned in [[ROOT_FAMILIES_SPIKE]] |
| Wiktionary etymology-db | Modern coinages, gap-fill | ⚠️ noisy; selective use only |

### 2.5 Algorithmic / generative methods

| Method | Description | Notes |
|---|---|---|
| **Runtime algorithm** | Trie-based longest-root match + affix list + recursion + denylist | Cheap; brittle on edges (`unimportant` recursion, `description` allomorphs, `unlockable` ambiguity, `understand` false-decomposition) |
| **LLM at build time** | Run Haiku 4.5 over top N words, ship cache | Higher quality; needs validation; ~$50–200 one-time |
| **LLM at capture time** | API call when user adds word; backend cache | No bundle cost; needs Phase 2+ backend; cold-start latency; only works online for new words |
| **Unsupervised segmentation** (Morfessor, BPE, SentencePiece) | Statistical subword learning | Designed for IR / tokenisation, not linguistic morphology — typically poor on English derivational structure |
| **Stemmer + dictionary lookup** | Snowball / Porter + post-processing | Stemmers strip too aggressively; not suitable as primary engine |

### 2.6 Considered and dismissed (for the record)

Listed for completeness — none reward further investigation:

- **Reverse-engineering competitor apps** — legally questionable, technically annoying
- **Mechanical Turk crowdsourcing** — quality control nightmare for linguistic judgments
- **Hand-writing a morphological grammar (DATR / finite-state)** — months of linguist-time
- **Etymonline scraping** — ToS unclear; better to email Douglas Harper if we want this content
- **University CELEX licensing partnership** — long lead time, uncertain outcome, expensive even if successful
- **User-contributed corrections at v1** — needs moderation infrastructure we don't have

## 3. Eliminations and Rationale

| Eliminated | Why |
|---|---|
| CELEX, MorphoLEX, modern OED, Merriam-Webster, AHD | Licensing — either commercial-blocked or prohibitively expensive |
| UniMorph, CatVar | Wrong data shape (inflectional, not derivational) |
| Morfessor / BPE / stemmers | Not linguistic morphology; quality insufficient for educational UI |
| Pure manual curation of modern books (without LLM) | 2–4 weeks of curator time when an LLM does the same synthesis in hours; revisit only if LLM quality fails |
| Unsupervised methods, crowdsourcing, custom grammar | Effort:value ratio worse than alternatives |
| Capture-time LLM (Option E in earlier discussion) | Doesn't fit local-first constraint; bundle approach wins for offline support. Revisit only if bundle proves infeasible. |

## 4. Live Candidates (after elimination)

Three sources, three methods to combine them:

| Source | Strength | Gap |
|---|---|---|
| **MorphyNet** | Modern + structured + per-word decomposition | Coverage and quality unknown until measured |
| **Skeat 1882 + Webster's 1913** | Authoritative classical etymology, public domain, no licensing exposure | No post-1900 coinages |
| **LLM (Haiku 4.5)** | Fills any gap, modern consensus, original phrasing | Hallucination risk; needs validation |

## 5. Recommended Architecture (provisional — pending spike data)

A **layered fallback** rather than a single source. Each layer has different strengths; together they cover ~99% of what users will capture without any single source being load-bearing:

```
Lookup(word) →
  1. MorphyNet cache              → if found and confidence ≥ threshold, use as decomposition
  2. Skeat / Webster's overlay    → augments any decomposition with historical etymology note
  3. LLM build-time cache         → for words missing from MorphyNet (esp. modern coinages)
  4. Wikipedia root catalog scan  → final fallback: "contains root X" (L0 degradation)
  5. No morphology section        → if even (4) finds nothing
```

**Key design choices:**

- The bundle ships layers 1, 2, 3, 4 (offline-first; consistent with [[LOCAL_FIRST_ARCHITECTURE#Reference Data]]).
- Layer 3 is generated build-time and bundled — *not* runtime API calls — to keep the app offline-capable.
- Layer 5 is the failure mode, never a wrong parse.

This architecture is **provisional**. Final shape depends on spike results:

- If MorphyNet covers ≥ 95% of captured words with high accuracy → layers 2 and 3 become small supplements.
- If MorphyNet whiffs and LLM passes → LLM cache becomes the primary decomposition source.
- If both whiff → ship L0 only and revisit in Phase 5 with stronger models.

## 6. Schema (provisional)

For all engines, produce records of this shape:

```json
{
  "word": "transportation",
  "decomposition": [
    {"morpheme": "trans-", "type": "prefix", "meaning": "across",         "language": "Latin"},
    {"morpheme": "port",   "type": "root",   "meaning": "carry",          "language": "Latin", "canonical_root": "port-", "etymology": "portāre"},
    {"morpheme": "-ation", "type": "suffix", "meaning": "act/result of"}
  ],
  "confidence": "high",
  "source": "morphynet"
}
```

The `source` field (`morphynet`, `llm-haiku-4.5`, `skeat-1882`, `wikipedia-roots`) lets us audit per-record provenance, swap layers without re-validating everything, and present users with attribution if we want to.

The `confidence` field (`high` / `medium` / `low`) gates UI presentation. Only `high` shows the linear breakdown; `medium` shows root-only (L0); `low` shows nothing.

## 7. Spike Programme — "The Machine"

Three **independent, parallel** spikes. Each terminates in a measurement against the existing 51-word test set from [[ROOT_FAMILIES_SPIKE#6]] so results are directly comparable.

### Spike A — MorphyNet quality

**Question:** Can MorphyNet serve as the primary decomposition source?

**Method:**
1. Download MorphyNet ([`kbatsuren/MorphyNet`](https://github.com/kbatsuren/MorphyNet)).
2. Filter to English derivational data; load into a lookup table.
3. Run all 51 words from [[ROOT_FAMILIES_SPIKE#6]] through it.
4. Record: hit rate, decomposition accuracy vs hand-known answer, false-positive rate on the three false-root traps (`uncle`, `island`, `butter`).
5. Measure bundle size of an English-only slice (gzipped).

**Acceptance criteria:**
- Hit rate ≥ 80% on the test set
- Accuracy ≥ 90% on hits
- 0 false positives on the false-root traps
- Bundle slice ≤ 200 KB gzipped

**Estimate:** 3 points (~half day)

### Spike B — Skeat / Webster's 1913 extraction

**Question:** Can a public-domain dictionary serve as the etymology / classical-coverage layer?

**Method:**
1. Source Webster's 1913 cleaned XML (multiple GitHub mirrors exist).
2. Source Skeat 1882 (Project Gutenberg or archive.org).
3. Build a sample extraction script: parse 200 random entries into `{word, etymology, root, source_language}`.
4. Run all 51 test words through the extractor.
5. Record: classical coverage, modern-coinage gap (specifically test 10 modern words: `cyber`, `internet`, `nanotech`, `bitcoin`, `email`, `selfie`, `podcast`, `webinar`, `hashtag`, `meme`).
6. Compare etymology richness vs Wikipedia roots data on the overlap.

**Acceptance criteria:**
- ≥ 90% coverage on classical test words
- ≥ 8/10 modern coinages cleanly flagged as "not found" (clean failure mode, not silent wrong answer)
- Etymology field richer than Wikipedia roots data on ≥ 70% of overlap

**Estimate:** 5 points (~1 day)

### Spike C — LLM (Haiku 4.5) decomposition quality

**Question:** Can an LLM produce reliable per-word decompositions to ship in a build-time cache?

**Method:**
1. Write a structured-output prompt (JSON schema matching §6).
2. Run Haiku 4.5 on all 51 test words.
3. Compare to hand-known answers.
4. Run the same 51 words a second time with Sonnet 4.6; measure agreement rate (cross-LLM consensus as a confidence proxy).
5. Stress-test on adversarial set: 10 false-root traps, 10 multi-layer cases (`unimportant`, `internationalization`, `denationalization`), 10 ambiguous cases (`unlockable`, `unmade`, `unionized`).
6. Estimate cost to run on top-30k frequency list using Anthropic API pricing.

**Acceptance criteria:**
- ≥ 85% accuracy on the 51-word test set
- ≥ 95% agreement between Haiku 4.5 and Sonnet 4.6 on clean cases
- ≥ 8/10 false-root traps correctly refused (`confidence: "low"` or no decomposition)
- Cost projection ≤ $200 for top-30k

**Estimate:** 5 points (~1 day)

## 8. Schedule

Spikes A, B, C are **independent** and can run in parallel — they don't share code or data dependencies. The schedule below assumes a single developer working part-time alongside other Phase 4 work; if full-time, halve it.

```
WEEK 1 — Spikes (decision week)
  Day 1  — File sub-issues for Spikes A, B, C under epic #385
  Day 2  — Spike A (MorphyNet) — half day
  Day 3  — Spike B (Skeat / Webster's) — full day
  Day 4  — Spike C (LLM Haiku 4.5) — full day
  Day 5  — Synthesis: pick architecture per §10; write decision doc

WEEK 2 — Pipeline build
  Day 1     — Schema design (formalize §6 record format, bundle structure, version field)
  Day 2–3   — Build script v0: produce a 100-word sample bundle using chosen architecture
  Day 4     — Hand-validate the 100-word sample; iterate on prompt / extraction rules
  Day 5     — Re-run on 1000-word sample; re-validate

WEEK 3 — Production pipeline
  Day 1–2   — Build script v1: full top-10k bundle
  Day 3     — Bundle size + load time validation on mobile (Flutter, iOS + Web)
  Day 4     — Document the pipeline (this doc becomes the architecture reference)
  Day 5     — Hand off to Phase 4 UI work (existing issue [#406])
```

**3-week elapsed plan, part-time.** Critical path runs through Week 1 Day 5 (architecture decision) — everything in Weeks 2–3 is conditional on what Week 1 reveals.

### 8.1 Decision gates

| Gate | When | What's decided |
|---|---|---|
| **Gate 1** — Architecture | End of Week 1 | Which sources, what layering order, what coverage target, whether to ship LLM cache |
| **Gate 2** — Schema | End of Week 2 Day 1 | Record format frozen, bundle structure, version field |
| **Gate 3** — Sample quality | End of Week 2 | Whether the 100-word sample is shippable quality |
| **Gate 4** — Bundle ship | End of Week 3 | Final bundle measured, loads cleanly on device, ready for Phase 4 UI |

A failure at any gate falls back to a known position rather than blocking:

- Gate 1 fails (no source / method passes acceptance) → ship L0 only (Wikipedia root catalog highlighting), defer L2 to Phase 5
- Gate 2 fails (schema can't represent observed cases) → re-architect schema, slip 2–3 days
- Gate 3 fails (sample quality below threshold) → reduce coverage target, accept smaller initial bundle
- Gate 4 fails (bundle too large or slow to load) → ship without bundle, fall back to runtime root-catalog scan only (essentially L0)

## 9. Decision Criteria — How to Pick After Spikes

After Week 1 the architecture is one of:

| Spike outcomes | Architecture |
|---|---|
| MorphyNet ≥ 90% accuracy + ≤ 200 KB | **MorphyNet primary**, Skeat etymology overlay, Wikipedia fallback. Skip the LLM cache (or only build for top 1k as a safety net). |
| MorphyNet 70–90% + LLM ≥ 85% | **Layered (recommended baseline)**: MorphyNet primary, LLM gap-fill for misses, Skeat etymology overlay. As described in §5. |
| MorphyNet < 70% + LLM ≥ 85% | **LLM cache primary**, Skeat etymology overlay, Wikipedia fallback. Skip MorphyNet entirely. |
| MorphyNet < 70% + LLM < 85% | **Defer L2.** Ship L0 only. Re-evaluate in Phase 5 with stronger models or more curated data. |
| Skeat coverage < 60% on classical | Drop the etymology overlay; use Wikipedia roots' etymology field instead. |

## 10. Risks

| Risk | Mitigation |
|---|---|
| LLM produces plausible-but-wrong output (`understand` = `under-` + `stand`) | Cross-LLM agreement gate; hand-validate adversarial set; fall back to L0 when confidence flag is low |
| MorphyNet license requires share-alike on the bundled data | Acceptable — same posture as Wikipedia roots in [[ROOT_FAMILIES_SPIKE#3]]; obligation is on the data file, not the app code |
| Skeat / Webster's classical accuracy worse than estimated (~95%) | Spike B measures this; if it fails, drop the etymology overlay and fall back to Wikipedia roots' etymology field |
| Bundle exceeds 0.3 MB after combining sources | Tiered bundle: ship top-5k by frequency in app binary, lazy-download top-30k pack on first use of feature |
| Over-claiming structure on `understand`, `uncle`, `island`, `butter` | Hand-curated denylist baked into build script; tested against the false-root trap set in every CI run |
| Schema changes after launch break old caches | Version field in schema; app rejects mismatched-version bundles and re-downloads |
| Modern coinages absent from all classical sources | LLM cache layer specifically targets these; cross-reference Wiktionary etymology-db for verification |
| Cost overrun on LLM build (Spike C cost projection wrong) | Cap top-N at 10k initially; expand only if budget allows; cache results so re-runs are free |

## 11. Out of Scope

Explicit non-goals so we don't scope-creep this into a thesis:

- **L3 graph UI / network visualization** — deferred to Phase 5 conversation. Data layer is graph-shaped (per §5 layering), but UI ships only trees and lists.
- **Other languages** — English-only for the foreseeable future; multilingual morphology is a separate problem.
- **User-contributed corrections** — needs moderation infrastructure; not for v1.
- **Real-time bundle updates** — bundle ships with app version; updates only on app store push.
- **Allomorph table as a separate UI feature** — captured in `canonical_root` field but not surfaced as its own screen for v1.
- **Productive vs unproductive root marker** — interesting linguistically but not load-bearing for learning UX.
- **Personal-notebook graph view** — deferred to Phase 5+; only meaningful once users have 200+ captured words.

## 12. Cross-references

- [[ROOT_FAMILIES_SPIKE]] — source dataset selection (root catalog tier)
- [[LOCAL_FIRST_ARCHITECTURE#Reference Data]] — bundle budgets
- [[PROJECT#Axis 3: Word Root Families]] — UX target
- GitHub epic [#385](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/385)
- Build script issue [#406](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/406)

## 13. Sources Considered (References)

- MorphyNet: Khuyagbaatar Batsuren et al. (2021), [MorphyNet repository](https://github.com/kbatsuren/MorphyNet). CC BY-SA 4.0.
- MorphoLEX-en: Sánchez-Gutiérrez et al. (2018). CC BY-NC-SA 4.0.
- CELEX2: Linguistic Data Consortium. Restrictive commercial licence.
- Skeat, W.W. (1882). *An Etymological Dictionary of the English Language*. Public domain. Available via [Project Gutenberg](https://www.gutenberg.org/) and [archive.org](https://archive.org/).
- *Webster's Unabridged Dictionary* (1913). Public domain. Cleaned XML mirrors on GitHub.
- *Oxford English Dictionary*, 1st edition (1884–1928). Public domain.
- Wikipedia, [List of Greek and Latin roots in English](https://en.wikipedia.org/wiki/List_of_Greek_and_Latin_roots_in_English). CC BY-SA 4.0.
- Open English WordNet: [en-word.net](https://en-word.net/). CC BY 4.0.
- *Feist Publications, Inc. v. Rural Telephone Service Co.*, 499 U.S. 340 (1991) — establishes that facts are not copyrightable in US law.
