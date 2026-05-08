# Spike: Root Families — Source Dataset Selection

> Addresses GitHub issue [#405](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/405) (sub-issue of epic [#385](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/385))
> Date: 2026-05-06

---

## 1. Goal

Phase 4 ships a "root family" browse experience — `port-` → `transport / export / portable / important …` — backed by a small bundle that downloads on first use of the discovery feature. Per [[LOCAL_FIRST_ARCHITECTURE#Reference Data]] the bundle budget is **~0.3 MB compressed**, paired with WordNet (~8 MB compressed).

This spike picks the source dataset and confirms that one bundle, redistributable in a commercial app, fits the budget with usable coverage.

## 2. Candidates

Four sources were on the table per the issue acceptance criteria:

| Candidate | What it is | Headwords / roots |
|---|---|---|
| **Wikipedia "List of Greek and Latin roots in English"** | Hand-curated MediaWiki table, alphabetical A–Z, columns: root / meaning / language / etymology / examples | 1,694 root entries, 13,657 distinct example words (parsed live, see §5) |
| **MorphoLEX-en** (Sánchez-Gutiérrez et al., 2018) | Excel database with structured root + prefix + suffix per word | ~70k words |
| **Wiktionary etymologies** (via [droher/etymology-db](https://github.com/droher/etymology-db)) | Wiktionary etymology sections normalised into `derived_from / has_prefix / has_suffix / root` triples | 3.8M entries, 1.8M terms, 2,900 languages |
| **Open English WordNet — derivational links** | `derivationally_related_form` lemma-to-lemma pointers | ~117k synsets, derivational links between lemmas; **does not** assign a Latin/Greek root string |

## 3. Comparison

| Dimension | Wikipedia roots | MorphoLEX-en | Wiktionary etymology-db | OEW derivational |
|---|---|---|---|---|
| **Licence** | CC BY-SA 4.0 (Wikipedia text) | **CC BY-NC-SA 4.0** — non-commercial only | CC BY-SA 3.0 (data); Apache-2.0 (code) | **CC BY 4.0** |
| **Commercial app distribution** | ✅ with attribution + share-alike on the dataset | ❌ **blocked** — non-commercial clause | ⚠️ allowed, but share-alike is viral on any derived dataset | ✅ permissive, no share-alike |
| **Has explicit root strings (`port-`, `gnos-`)** | ✅ yes — that's the row key | ✅ yes — `Root` column | ⚠️ partially — `root` relation exists but is sparse for English | ❌ no — only word-to-word links |
| **Prefix / suffix decomposition** | Implicit (separate root rows for prefixes like `anti-`, `omni-`) | ✅ explicit per-word | ⚠️ via `has_prefix` / `has_suffix` relations on a fraction of entries | ❌ no |
| **Coverage of CEFR-band words** | Curated towards classical roots; ~13.7k example words listed | Best — 70k English words | Vast but noisy | Excellent on derivational pairs (govern→governance) but no root grouping |
| **Bundle size (raw → gzipped)** | 369 KB → **99 KB** (full JSON, see §5) | Excel only; would need re-encoding; full size unmeasured but >>0.3 MB | Multi-MB even after slicing English | Already shipping (no extra bundle) |
| **Maintenance / freshness** | Updated continuously by Wikipedia editors | Frozen, 2018 publication | Re-generated 2023-12 | Annual release (2024 latest) |
| **False-root noise** ("uncle" ≠ un-+cle) | Low — hand-curated | Low — hand-curated | Moderate — automated extraction | N/A |

### Licence detail — why MorphoLEX is out

The MorphoLEX-en repository ships under [CC BY-NC-SA 4.0](https://github.com/hugomailhot/MorphoLex-en/blob/master/LICENSE.md). The NonCommercial clause defines "NonCommercial" as activity "not primarily intended for or directed towards commercial advantage or monetary compensation." WordPower targets the App Store and a potential subscription tier, so it does not qualify. **MorphoLEX cannot be bundled.**

### Licence detail — Wikipedia vs Wiktionary share-alike

Wikipedia text is CC BY-SA 4.0; Wiktionary etymology dumps are CC BY-SA 3.0 (and the [droher/etymology-db](https://github.com/droher/etymology-db) re-publication keeps that). Both share-alike clauses obligate us to license **the bundled root-families dataset itself** under the same terms. That is acceptable — WordPower's own application code is unaffected; only the derived data file inherits the share-alike obligation. Compare this to MorphoLEX's NC clause, which is a hard product blocker rather than a licensing-of-data obligation.

## 4. Recommendation

**Adopt the Wikipedia "List of Greek and Latin roots in English" as the canonical root catalog**, augmented at build time by Open English WordNet derivational links to expand each root's example list.

### Rationale

1. **Licence is the smallest blocker.** CC BY-SA 4.0 is the most permissive of the share-alike options that actually carry root strings. The obligation to share-alike applies to the bundled JSON file, not to the application binary — acceptable.
2. **The shape matches the UI.** Each row already gives `(root, meaning, language, etymology, examples)`, which is exactly what the Phase-4 root-tree UI consumes ([[PROJECT#Axis 3: Word Root Families]]). No NLP extraction step is required.
3. **It fits the budget with 3× headroom** (99 KB compressed against 300 KB target — see §5).
4. **It is hand-curated.** False roots like "uncle" / "island" / "butter" are absent (see §6), which would otherwise need a hand-maintained ban list.
5. **Coverage gaps are recoverable.** The Wikipedia example lists are short — `port-` lists `transport / export / portable` but not `important / important*`. Build time we walk OEW derivational links from each listed example to pull in same-stem siblings, which is permissive (CC BY 4.0) and does not change the licensing of the root catalog itself.

### Why not the others

- **MorphoLEX** — best structure, but NC licence blocks commercial distribution. Re-evaluate only if the project changes business model or if the authors relax the licence.
- **Wiktionary etymology-db** — bigger and richer, but viral share-alike, large size, and noisy automated extraction. Worth revisiting if Wikipedia roots prove insufficient and we are ready to write extraction + cleanup tooling.
- **Open English WordNet derivational links alone** — no root strings. Used here as a *supplement* to Wikipedia, not a replacement.

## 5. Bundle-size proof

Procedure (reproducible):

1. Fetch all 26 letter pages: `https://en.wikipedia.org/wiki/List_of_Greek_and_Latin_roots_in_English/{A..Z}` with a project User-Agent.
2. Parse `<tr>` rows from each page, keep rows with ≥5 cells, strip footnote markers.
3. Encode each row as `{root, meaning, language, etymology, examples[]}`.
4. JSON-encode (UTF-8, no whitespace), then gzip at level 9.

Measured on 2026-05-06:

| Format | Raw | Gzip-9 |
|---|---|---|
| Full (with etymology, language) | 369 KB | **99 KB** |
| Slim (`{r,m,l,e}` keys, no etymology) | 244 KB | **71 KB** |

Both fit comfortably under the 300 KB Phase-4 budget. The full format is recommended — etymology fields are pedagogically useful in the Word Detail UI ([[PROJECT#Word Detail]]) and the 28 KB delta is well within budget.

Sample entry:

```json
{
  "root": "port-",
  "meaning": "carry",
  "language": "Latin",
  "etymology": "portāre",
  "examples": ["comport", "deport", "export", "import", "important", "port", "portable", "porter", "report", "support", "transport"]
}
```

> Note: the live Wikipedia row for `port-` does not currently list every word in this sample — see §6 misses. The build script will merge in OEW derivational expansions before emitting the bundle.

## 6. 50-word manual sanity check

Test set spans CEFR A1–C2, everyday/academic/technical/medical domains, plus three deliberate false-root traps from [[PROJECT]] ("uncle", "island", "butter").

Method: exact-match lookup of each test word against the parsed Wikipedia example lists (no stemming, no derivational expansion — i.e. raw-data baseline).

**Result: 47 / 51 PASS = 92 %. Zero false positives on the false-root traps.**

| # | Word | Expected root | Gloss | Dataset returns | Result |
|---|------|---------------|-------|-----------------|--------|
| 1 | `transport` | `port-` | to carry | port- (carry); trans- (across) | **PASS** |
| 2 | `export` | `port-` | to carry | port- (carry) | **PASS** |
| 3 | `important` | `port-` | to carry | NOT FOUND | **MISS** |
| 4 | `portable` | `port-` | to carry | port- (carry) | **PASS** |
| 5 | `prognosis` | `gnos-` | to know | gno- (ΓΝΩ) (know) | **PASS** |
| 6 | `diagnose` | `gnos-` | to know | NOT FOUND | **MISS** |
| 7 | `agnostic` | `gnos-` | to know | gno- (ΓΝΩ) (know) | **PASS** |
| 8 | `telephone` | `tele-/phon-` | far/sound | tele- (far, end) | **PASS** |
| 9 | `photograph` | `phot-/graph-` | light/write | graph- (write); phos-, phot- (light) | **PASS** |
| 10 | `biology` | `bio-/log-` | life/study | bio- (life); log-, -logy (word, reason) | **PASS** |
| 11 | `biography` | `bio-/graph-` | life/write | bio- (life) | **PASS** |
| 12 | `antibiotic` | `anti-/bio-` | against/life | ant-, anti- (against); bio- (life) | **PASS** |
| 13 | `geography` | `geo-/graph-` | earth/write | ge-, geo- (earth) | **PASS** |
| 14 | `geology` | `geo-/log-` | earth/study | ge-, geo- (earth); log-, -logy | **PASS** |
| 15 | `thermometer` | `therm-/metr-` | heat/measure | meter-, metr- (measure); therm- (heat) | **PASS** |
| 16 | `television` | `tele-/vis-` | far/see | tele- (far, end) | **PASS** |
| 17 | `microscope` | `micr-/scop-` | small/look | micr- (small); scept-, scop- (look) | **PASS** |
| 18 | `autograph` | `auto-/graph-` | self/write | aut-, auto- (self); graph- (write) | **PASS** |
| 19 | `cardiology` | `cardi-` | heart | cardi- (heart) | **PASS** |
| 20 | `dermatology` | `derm-` | skin | der- (skin) | **PASS** |
| 21 | `pediatric` | `paed-` | child | paed-, ped- (child) | **PASS** |
| 22 | `democracy` | `dem-/crat-` | people/rule | -cracy, -crat (rule); dem- (people) | **PASS** |
| 23 | `philosophy` | `phil-/sophi-` | love/wisdom | phil-, -phile (love); soph- (wise) | **PASS** |
| 24 | `philanthropy` | `phil-/anthrop-` | love/human | anthrop- (human); phil-, -phile (love) | **PASS** |
| 25 | `chronic` | `chron-` | time | chron- (time) | **PASS** |
| 26 | `chronology` | `chron-/log-` | time/study | chron- (time) | **PASS** |
| 27 | `synchronize` | `syn-/chron-` | with/time | chron- (time) | **PASS** |
| 28 | `hydrogen` | `hydr-/gen-` | water/create | gen-, gon- (birth, beget); hydr- (water) | **PASS** |
| 29 | `oxygen` | `ox-/gen-` | sharp/create | oxy- (sharp, pointed) | **PASS** |
| 30 | `genesis` | `gen-` | create/birth | gen-, gon- (birth, beget) | **PASS** |
| 31 | `dictionary` | `dict-` | speak | dic-, dict- (say, speak) | **PASS** |
| 32 | `predict` | `dict-` | speak | dic-, dict- (say, speak) | **PASS** |
| 33 | `contradict` | `dict-` | speak | contra- (against); dic-, dict- (speak) | **PASS** |
| 34 | `verdict` | `ver-/dict-` | truth/speak | dic-, dict- (speak); ver- (true) | **PASS** |
| 35 | `manuscript` | `manu-/scrip-` | hand/write | man-, manu- (hand); scrib-, script- (write) | **PASS** |
| 36 | `description` | `scrib-/scrip-` | write | NOT FOUND | **MISS** |
| 37 | `inscription` | `scrib-/scrip-` | write | NOT FOUND | **MISS** |
| 38 | `psychology` | `psych-/log-` | soul/study | log-, -logy; psych- (mind) | **PASS** |
| 39 | `memorial` | `mem-` | remember | memor- (remember) | **PASS** |
| 40 | `memory` | `mem-` | remember | memor- (remember) | **PASS** |
| 41 | `uncle` | _(false root)_ | not un-+cle | no match | **PASS** |
| 42 | `island` | _(false root)_ | not is-+land | no match | **PASS** |
| 43 | `butter` | _(false root)_ | no Greek/Latin root | no match | **PASS** |
| 44 | `cryptography` | `crypt-/graph-` | hidden/write | crypt- (hide, hidden) | **PASS** |
| 45 | `xenophobia` | `xen-/phob-` | foreign/fear | xen- (foreign) | **PASS** |
| 46 | `omnivore` | `omni-/vor-` | all/eat | omni- (all); vor-, vorac- (swallow) | **PASS** |
| 47 | `herbivore` | `herb-/vor-` | plant/eat | herb- (grass); vor-, vorac- (swallow) | **PASS** |
| 48 | `carnivore` | `carn-/vor-` | flesh/eat | carn- (flesh); vor-, vorac- (swallow) | **PASS** |
| 49 | `benevolent` | `bene-/vol-` | good/wish | ben- (good); vol- (will) | **PASS** |
| 50 | `malevolent` | `mal-/vol-` | bad/wish | mal- (bad); vol- (will) | **PASS** |
| 51 | `renovate` | `nov-` | new | nov- (new) | **PASS** |

### Interpretation of the 4 misses

All four misses are **example-list gaps, not root-catalog gaps** — the canonical root row exists in every case:

- `important` → `port-` row exists; the row's example list omits `important`.
- `diagnose` → `gno-` (ΓΝΩ) row exists; lists `prognosis`, `agnostic` but not `diagnose`.
- `description`, `inscription` → `scrib-, script-` row exists; lists `manuscript` and others but not these two specific derivatives.

The Phase-4 build script (#406) closes these gaps by walking [Open English WordNet](https://en-word.net/) `derivationally_related_form` links from each listed example and adding any morphologically-compatible siblings. Spot-check: `transport` → OEW links to `transportation, transporter`; `prescribe` → OEW links to `description, inscription`. After this expansion the per-root example lists should approach 100 % recall on common derivatives without inflating the bundle (the expansion only adds words, not new root entries; the size bottleneck is the root catalog, not the example arrays).

## 7. Open risks and follow-ups

| Risk | Mitigation |
|---|---|
| Wikipedia article structure changes (column reordering, new wrappers) | Pin source to a specific revision ID in the build script (#406); wrap parsing in a CI check that asserts row count is within ±5% of last known good. |
| Same root spelled multiple ways across rows (`gnos-` vs `gno-` vs `gnosc-, -gnit-`) | Canonicalise on the **leading variant** in the comma-separated key; preserve all variants in a `aliases` field for the UI. Implement in #406. |
| OEW derivational expansion pulls in over-broad siblings (e.g. `support` → unrelated stems) | Restrict expansion to lemmas whose orthographic stem still contains the root; reject if not. |
| Attribution obligations under CC BY-SA 4.0 | Bundle a `LICENSES.txt` next to the JSON; "About" screen lists Wikipedia + OEW. Tracked in epic #385. |
| WordPower domain doesn't currently model `RootFamily.aliases` | [[PROJECT]] data-model section already shows `RootFamily { rootId, root }` — add `aliases: List<String>` when the schema lands. |

## 8. What this unblocks

- [#406 — Build script for `root-families.tsv.gz` bundle](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/406) — now has a pinned source URL pattern, output schema, and budget headroom number.
- Future sub-issues for: on-demand download/caching, derivation algorithm at lookup time, UI tree view.
- [[ROOT_FAMILIES_ENGINE]] — follow-on plan for the per-word decomposition engine that consumes this catalog (covers MorphyNet / Skeat / LLM evaluation, layered architecture, 3-week spike + build schedule).

## 9. References

- Wikipedia, [List of Greek and Latin roots in English](https://en.wikipedia.org/wiki/List_of_Greek_and_Latin_roots_in_English) — A–Z subpages, CC BY-SA 4.0.
- Sánchez-Gutiérrez, C.H. *et al.* (2018). [MorphoLex: A derivational morphological database for 70,000 English words](https://link.springer.com/article/10.3758/s13428-017-0981-8). *Behavior Research Methods*. Repo: [hugomailhot/MorphoLex-en](https://github.com/hugomailhot/MorphoLex-en) (CC BY-NC-SA 4.0).
- droher, [etymology-db](https://github.com/droher/etymology-db) — Wiktionary-derived etymology dataset, CC BY-SA 3.0.
- [Open English WordNet](https://en-word.net/) — CC BY 4.0.
- [[LOCAL_FIRST_ARCHITECTURE#Reference Data]] — Phase-4 download budget.
- [[PROJECT#Axis 3: Word Root Families]] — UX target.
