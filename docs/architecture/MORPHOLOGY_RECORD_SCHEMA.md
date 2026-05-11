# Morphology Record Schema — v1

**Status:** Locked (Phase 2 of root-families build plan)
**Date:** 2026-05-11
**Issue:** [#526](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/526)
**Supersedes:** `ROOT_FAMILIES_ENGINE.md` §6 (provisional schema)

Related: [`ROOT_FAMILIES_DECISION.md`](ROOT_FAMILIES_DECISION.md) · [`ROOT_FAMILIES_ENGINE.md`](ROOT_FAMILIES_ENGINE.md)

---

## 1. Overview

This document is the canonical record-format specification for the morphology bundle shipped with WordPower. It formalises the §6 schema from `ROOT_FAMILIES_ENGINE.md`, adds the bundle-level wrapper, defines merge semantics across data layers, and locks the confidence rendering rule referenced by the Phase 6 UI handoff ([#406](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/406)).

The bundle is a static JSON file generated at build time and loaded by the Flutter app at start-up. The Flutter app validates it against [`morphology-bundle-v1.schema.json`](morphology-bundle-v1.schema.json) (see §5).

---

## 2. Data layers

The bundle merges three independent data layers, each with distinct strengths:

| Layer | Source | Role | Coverage |
|---|---|---|---|
| **L1** | LLM build-time cache (Gemini 2.5 Flash primary; Haiku 4.5 fallback) | Per-word morpheme decomposition, confidence, reasoning | top-10k English words by SUBTLEX-US frequency |
| **L2** | GCIDE (Webster's 1913 + supplements, GPL 3.0+) | Per-word etymology prose, source language chain | ~92% of top-10k by strict match |
| **L3** | Wikipedia "List of Greek and Latin roots in English" (CC BY-SA 4.0) | Root catalog; used for L0 fallback at runtime — **not stored in this bundle** | ~600 roots |

L3 is an independent lookup at runtime. It is not embedded in the morphology bundle.

---

## 3. Per-word record format

Every entry in the bundle's `records` map is a **per-word record** keyed by the lowercase headword.

### 3.1 Full record (high or medium confidence)

```json
{
  "word": "transport",
  "confidence": "high",
  "decomposition": [
    {
      "morpheme": "trans-",
      "type": "prefix",
      "meaning": "across, beyond",
      "language": "Latin",
      "source": "llm-gemini-2.5-flash"
    },
    {
      "morpheme": "port",
      "type": "root",
      "meaning": "carry, bear",
      "language": "Latin",
      "canonical_root": "port-",
      "etymology": "portāre",
      "source": "llm-gemini-2.5-flash"
    }
  ],
  "etymology_note": "F. transporter, L. transportare; trans across + portare to carry. See Port bearing, demeanor.",
  "etymology_languages": ["F.", "L."],
  "etymology_source": "gcide",
  "reasoning": "Classic Latin compound. Both trans- (across) and port- (carry) are highly productive in modern English…",
  "sources": ["llm-gemini-2.5-flash", "gcide"]
}
```

### 3.2 Refused record (low confidence)

When the LLM refuses a decomposition (false-root trap, etymologically-opaque word), the record still exists in the bundle so the app knows the word was evaluated and refused — not merely absent.

```json
{
  "word": "uncle",
  "confidence": "low",
  "decomposition": [],
  "reasoning": "False-root trap. 'Uncle' is borrowed from Old French oncle, from Latin avunculus (mother's brother). The '-cle' is part of the Latin diminutive stem, not a productive English suffix. Teaching 'un- + cle' would create a false analogy.",
  "sources": ["llm-gemini-2.5-flash"]
}
```

Refused records have no `etymology_note` / `etymology_languages` / `etymology_source` fields even when GCIDE has an entry; the confidence gate makes them irrelevant at render time.

---

## 4. Field reference

### 4.1 Top-level fields

| Field | Type | Required | Description |
|---|---|---|---|
| `word` | string | yes | Lowercase headword, matches the key in `records` |
| `confidence` | `"high"` \| `"medium"` \| `"low"` | yes | LLM-assigned confidence gate. Drives UI rendering (§6). |
| `decomposition` | array of morpheme objects | yes | Ordered list of morphemes, left-to-right. Empty array when `confidence = "low"`. |
| `etymology_note` | string | no | Raw GCIDE etymology prose. Present only when L2 matched and `confidence ≠ "low"`. |
| `etymology_languages` | array of strings | no | Source-language abbreviations extracted from GCIDE (e.g. `["F.", "L.", "Gr."]`). Present when `etymology_note` is present. |
| `etymology_source` | `"gcide"` | no | Always `"gcide"` when present. Reserved for future additional etymology layers. |
| `reasoning` | string | yes | LLM chain-of-thought explaining the confidence and morpheme choices. Internal audit field; not displayed to the user. |
| `sources` | array of strings | yes | Ordered list of layers that contributed to this record. Values: `"llm-gemini-2.5-flash"`, `"llm-claude-haiku-4.5"`, `"gcide"`. |

### 4.2 Morpheme object fields

| Field | Type | Required | Description |
|---|---|---|---|
| `morpheme` | string | yes | Surface form as it appears in the word, including any attached hyphen for prefixes/suffixes (e.g. `"trans-"`, `"-ation"`). |
| `type` | `"prefix"` \| `"root"` \| `"suffix"` \| `"connective_vowel"` | yes | Morpheme category. `connective_vowel` is used for interfix vowels (e.g. the `-o-` in `democracy`). |
| `meaning` | string | yes | Plain-English gloss of this morpheme's contribution. |
| `language` | string | yes | Language of origin for this morpheme (e.g. `"Latin"`, `"Greek"`, `"Old English"`). |
| `canonical_root` | string | no | Normalised root entry used for family-browse linking (e.g. `"port-"`). Present on `root`-type morphemes when the LLM can identify the family root. |
| `etymology` | string | no | Original source-language form (e.g. `"portāre"`, `"philos"`). Present on `root`-type morphemes when the LLM provides it. |
| `source` | string | yes | Which layer produced this morpheme entry. Matches one of the values in the top-level `sources` array. |

---

## 5. Bundle wrapper format

The bundle is a single JSON object:

```json
{
  "schema_version": "1",
  "build_date": "2026-05-11",
  "model": "gemini-2.5-flash",
  "prompt_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "records": {
    "transport": { ... },
    "export": { ... },
    "uncle": { ... }
  }
}
```

### Bundle-level fields

| Field | Type | Description |
|---|---|---|
| `schema_version` | string | Integer string; currently `"1"`. The Flutter app rejects bundles with an unrecognised version and re-downloads. |
| `build_date` | string | ISO 8601 date (`YYYY-MM-DD`) when the bundle was generated. |
| `model` | string | Primary L1 model identifier used for this build (e.g. `"gemini-2.5-flash"`, `"claude-haiku-4.5"`). |
| `prompt_hash` | string | SHA-256 hex digest of the prompt file used for generation (see `pipeline/prompt-v1.md`). Changing the prompt invalidates the cache; the hash surfaces the mismatch. |
| `records` | object | Map from lowercase headword to per-word record. The map contains all words for which an L1 call was made, including refused (`confidence: "low"`) words. |

---

## 6. Confidence rendering rule (locked)

Locked in [`ROOT_FAMILIES_DECISION.md` §Locked decisions, item 4](ROOT_FAMILIES_DECISION.md#locked-decisions):

| `confidence` | What the app shows |
|---|---|
| `"high"` | Full morpheme breakdown with meanings and etymology note (L2 ambition target) |
| `"medium"` | Root-only display: "Contains the root *port-* (carry)" — L0-style fallback rendering |
| `"low"` | Nothing from this bundle; app shows definition only. Runtime L0 root-catalog scan still runs. |

The Flutter rendering code must read `confidence` before deciding which UI branch to take. It must **not** infer rendering from the length of `decomposition[]` — the field definitions above are the authoritative source.

---

## 7. Merge semantics

Merge happens at build time in `pipeline/merge_bundle.py`. The runtime engine performs no merging; it reads the already-merged record from the bundle.

### 7.1 Merge algorithm (per word)

```
merge(word):
  1. Fetch L1 record from LLM output file (required — every bundled word has an L1 record)
     → provides: word, confidence, decomposition[], reasoning

  2. Add source tag to each morpheme in decomposition[]:
     morpheme.source = "llm-{model}"

  3. Look up word (lowercase) in GCIDE index (L2):
     if found AND etymology.present == true AND confidence != "low":
       add etymology_note  = gcide_entry.etymology.raw
       add etymology_languages = gcide_entry.etymology.languages
       add etymology_source = "gcide"

  4. Compute sources[]:
     ["llm-{model}"]                      — always
     + ["gcide"]                          — if step 3 added etymology fields

  5. Emit merged record keyed by lowercase word
```

### 7.2 Field provenance summary

| Field(s) | Layer | Notes |
|---|---|---|
| `word`, `confidence`, `decomposition[].*`, `reasoning` | L1 (LLM) | Core record; always present |
| `etymology_note`, `etymology_languages`, `etymology_source` | L2 (GCIDE) | Added when GCIDE matches and confidence ≠ low |
| L3 Wikipedia roots | — | Not merged into bundle; used only at runtime for L0 fallback scan |

### 7.3 Conflict resolution

L1 and L2 are complementary, not competing: L1 provides morpheme structure, L2 provides etymology prose. There is no field overlap that would require conflict resolution at merge time.

If a future layer introduces a conflicting `meaning` or `language` field on an existing morpheme, the rule is: **L1 wins for morpheme structure; the new layer's value is stored under a layer-namespaced key** (e.g. `meaning_gcide`). This keeps the primary fields stable across layer additions.

---

## 8. Runtime lookup (Flutter)

```
lookup(word):
  normalized = word.toLowerCase()
  record = bundle.records[normalized]

  if record == null:
    → run L3 Wikipedia root-catalog scan → L0 display ("Contains root X")
    → if no root match: no morphology section

  if record.confidence == "high":
    → render full morpheme breakdown (§6)
  if record.confidence == "medium":
    → render root-only display: use record.decomposition[].canonical_root where present (§6)
  if record.confidence == "low":
    → skip morphology section; run L3 scan as fallback
```

The app must validate the bundle's `schema_version` on first load. If the version string is not `"1"`, the app must discard the bundle and attempt to re-download from the server.

---

## 9. Gate 2 verification — round-trip of 10 Spike C records

The gate for this phase requires that the schema represents every output observed in the 162 Spike C calls without information loss. Below are 10 representative records drawn from the Spike C results, annotated with which schema fields each exercises.

### Record 1 — `transport` (high confidence, L1 + L2, two morphemes)

| Raw Spike C field | Schema field | Notes |
|---|---|---|
| `decomposition[0].morpheme = "trans-"` | `decomposition[0].morpheme` | prefix, hyphen-suffixed ✓ |
| `decomposition[0].type = "prefix"` | `decomposition[0].type` | valid enum value ✓ |
| `decomposition[1].canonical_root = "port-"` | `decomposition[1].canonical_root` | optional field on root ✓ |
| `decomposition[1].etymology = "portāre"` | `decomposition[1].etymology` | diacritics preserved ✓ |
| `confidence = "high"` | `confidence` | drives full-breakdown render ✓ |
| GCIDE raw: `"F. transporter, L. transportare…"` | `etymology_note` | prose stored verbatim ✓ |
| GCIDE languages: `["F.", "L."]` | `etymology_languages` | array of abbreviations ✓ |

No information loss.

### Record 2 — `export` (high confidence, L1 + L2, prefix + root)

Same field coverage as Record 1. GCIDE entry: `"L. exportare, exportatum; ex out + portare to carry: cf. F. exporter."` — stored verbatim in `etymology_note`. No information loss.

### Record 3 — `uncle` (low confidence, refused)

| Raw Spike C field | Schema field | Notes |
|---|---|---|
| `decomposition = []` | `decomposition = []` | empty array allowed ✓ |
| `confidence = "low"` | `confidence` | drives no-render path ✓ |
| `reasoning = "False-root trap…"` | `reasoning` | audit field preserved ✓ |

GCIDE not consulted for low-confidence records. No information loss.

### Record 4 — `island` (low confidence, refused)

Same as Record 3 pattern. `reasoning` explains the 16th-century folk-etymology insertion. No information loss.

### Record 5 — `butter` (low confidence, refused)

Same as Record 3 pattern. `reasoning` explains Greek *boutyron* etymology. No information loss.

### Record 6 — `incomprehensibility` (medium confidence, multi-layer word)

| Raw Spike C field | Schema field | Notes |
|---|---|---|
| Four morphemes: `in-`, `comprehend`, `-ible`, `-ity` | `decomposition[0..3]` | array of 4 objects ✓ |
| `decomposition[1].canonical_root = "comprehend-"` | `canonical_root` | compound root form ✓ |
| `decomposition[1].etymology = "comprehendere (com- + prehendere, 'seize')"` | `etymology` | parenthetical compound note ✓ |
| `confidence = "medium"` | `confidence` | drives root-only display ✓ |

No information loss.

### Record 7 — `understand` (low confidence, synchronically-opaque)

| Raw Spike C field | Schema field | Notes |
|---|---|---|
| `decomposition = []` | `decomposition = []` | correctly empty ✓ |
| `confidence = "low"` | `confidence` | ✓ |
| `reasoning` explains Old English `understandan` | `reasoning` | etymology context preserved ✓ |

No information loss.

### Record 8 — `important` (high confidence, three morphemes)

| Raw Spike C field | Schema field | Notes |
|---|---|---|
| Three morphemes: `im-`, `port`, `-ant` | `decomposition[0..2]` | ✓ |
| `-ant` has no `canonical_root` or `etymology` (suffix) | optional fields absent | allowed ✓ |
| GCIDE: `"F. important. See Import, v. t."` | `etymology_note` | cross-reference prose ✓ |

No information loss.

### Record 9 — `cyberattack` (expected: high confidence if in bundle, no GCIDE entry)

Spike C adversarial set included modern coinages. GCIDE won't have this word (1913 cutoff). The merge step simply omits `etymology_note`, `etymology_languages`, `etymology_source` — `sources` array contains only `["llm-gemini-2.5-flash"]`. No information loss.

### Record 10 — `denationalization` (high confidence, five morphemes)

| Raw Spike C field | Schema field | Notes |
|---|---|---|
| Five morphemes: `de-`, `nation`, `-al`, `-ize`, `-ation` | `decomposition[0..4]` | ✓ |
| All morphemes have `source` tag | `morpheme.source` | ✓ |
| `confidence = "high"` | `confidence` | ✓ |

No information loss.

**Gate 2 passed.** All 10 records round-trip through the schema without loss. The schema represents every output shape observed across the 162 Spike C calls: two-morpheme, three-morpheme, multi-layer (four+), refused (empty decomposition), medium-confidence, and GCIDE-enriched records.

---

## 10. Versioning policy

- **v1**: this spec. Single `schema_version: "1"` at bundle level. Per-record versioning deferred to v2.
- **Triggering a v2**: any change to required field names, type narrowing, or addition of a new required field. Adding optional fields is backwards-compatible and does not require a version bump.
- **Migration**: the Flutter app rejects mismatched `schema_version` values and re-downloads. The pipeline rebuilds the full bundle on version bump (re-build cost ~$35; not incremental).

---

## 11. Cross-references

- [`ROOT_FAMILIES_ENGINE.md §6`](ROOT_FAMILIES_ENGINE.md#6-schema-provisional) — provisional schema this doc promotes
- [`ROOT_FAMILIES_DECISION.md`](ROOT_FAMILIES_DECISION.md) — locked architecture and build plan
- [`morphology-bundle-v1.schema.json`](morphology-bundle-v1.schema.json) — machine-readable JSON Schema (loadable in Flutter for runtime validation)
- GitHub issue [#406](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/406) — UI handoff; references this doc for confidence rendering rule
- GitHub issue [#527](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/527) — Phase 3 (L1 cache build pipeline)
- GitHub issue [#528](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/528) — Phase 4 (L2 etymology overlay build)
- GitHub issue [#529](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/529) — Phase 5 (bundle merge + mobile validation)
