# Spike: Merriam-Webster Learner's Dictionary API — Research Findings

> Addresses GitHub issue #436 (sub-issue of epic #350, parallel-track companion to #353)
> Date: 2026-05-04

---

## 1. Registration & Commercial Tier

### Sign-up process

1. Register a developer account at `https://dictionaryapi.com/register/index`
   (name, email, password, role, application name + URL + description, launch date).
2. Pick "Learner's Dictionary" for the **Request API Key (1)** dropdown — *not* "Collegiate". Learner's is the ESL product (definitions paraphrased in simpler English, learner-targeted examples, fewer obscure senses); Collegiate is the general-purpose Merriam-Webster dictionary.
3. Verify the email Merriam-Webster sends after submission. The key is then visible under **YOUR KEYS** in the developer dashboard.

**Approval is same-day** (effectively instant after email verification) — the opposite end of the timeline-risk spectrum from Cambridge's ~10-business-day licensing process.

### Free tier — the actual terms

The Merriam-Webster Dictionary API ToS (`https://dictionaryapi.com/info/terms-of-service.htm`) grants a free licence on **three** simultaneous conditions:

> *"Your website or application is non-commercial; reference queries do not exceed 1000/day/reference work; you do not use more than two reference works."*

Quotas:

| Tier | Quota | Cost |
|---|---|---|
| Free non-commercial | 1 000 calls/day per reference, max 2 references | Free |
| Commercial | Custom | Negotiated, contact Merriam-Webster |

WordPower is intended to be commercial (App Store distribution, potential subscription revenue), so the free tier covers **development only**. Production launch needs a separate commercial agreement.

### Compared to Cambridge

| | Merriam-Webster Learner's | Cambridge |
|---|---|---|
| Free non-commercial tier | **Yes** — 1 000/day | **No** (only 30-day eval) |
| Approval time | Same-day | ~10 business days |
| Commercial cost | Quote required | Quote required |
| Integration risk if commercial deal stalls | Free dev work can continue indefinitely | Eval key expires, then blocked |

The free dev tier is the headline win: development against MW can begin immediately and isn't gated on a commercial conversation.

---

## 2. API Basics

| Property | Value |
|---|---|
| Base URL | `https://dictionaryapi.com/api/v3/references/learners/json/` |
| Authentication | `key` query parameter (no header form supported) |
| Response format | **JSON, end-to-end** — no XML/HTML inside (contrast Cambridge) |
| Reference works available | Learner's, Collegiate, Thesaurus, Medical, Spanish, etc. — Learner's only for this spike |

### Endpoints used

There is essentially one endpoint per reference work:

```
GET https://dictionaryapi.com/api/v3/references/learners/json/{word}?key={apiKey}
```

`{word}` may include spaces (URL-encoded) — the API accepts phrasal entries (e.g. `look%20up`), though phrasal verbs are typically returned as defined run-ons (`dros`) under the head verb's entry, not as standalone results.

---

## 3. Response Shape

### Three-state response

The endpoint always returns HTTP 200 with a JSON array. The array's content is one of three states, distinguished by element type:

| State | Array contents | Example |
|---|---|---|
| **Match** | `Object[]` — each element is a full entry | `[{"meta": {...}, "hwi": {...}, ...}]` |
| **Typo / suggestion** | `String[]` — up to 20 suggested headwords | `["hello", "halo", "jello", "held", "hell", ...]` |
| **No match** | `[]` (empty) | `[]` |

Client must dispatch on element type, not HTTP status. The 404 / not-enrichable marker row in our cache fires on either of the latter two states. The suggestion list is also a useful UX hook (Cambridge does not expose this).

### Top-level entry keys

For a successful match, each entry object has roughly:

| Key | Meaning |
|---|---|
| `meta` | Identity + headword stems + `app-shortdef` (compact projection) + `offensive` flag |
| `hwi` | Headword info — syllabified `hw`, plus `prs[]` of pronunciations |
| `hom` | Homograph counter (e.g. `run:1`, `run:2`) |
| `fl` | Functional label = part of speech (`verb`, `adjective`, …) |
| `ins` | Inflections (plural / past tense / etc.) |
| `gram` | Countability for nouns: `count`, `noncount`, or both |
| `def` | Sense sequences — deeply nested (see below) |
| `uros` | Undefined run-ons — derived word forms (e.g. `ubiquity`, `ubiquitously` under `ubiquitous`) |
| `dros` | Defined run-ons — phrasal verbs / idioms (e.g. `abandon yourself to` under `abandon`) |
| `vrs` | Variant spellings |
| `shortdef` | Flat `String[]` of short definitions (the easy projection — *use this*) |

### Sense structure (`def[].sseq[][][]`)

The full sense tree is **four levels deep** and uses a typed-tuple convention:

```
def              (one item per major sense group)
  └── sseq                    List of sense-sequences
        └── (sequence)         List of senses
              └── ("sense", { ... })   2-tuple keyed by string
                    ├── sn       sense number, e.g. "1 a"
                    ├── sls      status labels: ["formal"], ["literary"], ["chiefly British"], ["informal"]
                    └── dt       definition-text fragments — list of 2-tuples
                          ├── ("text", "{bc}to leave and never return to ...")
                          └── ("vis", [ {"t": "...example with {it}word{/it}..."} ])
```

The `dt` fragments use string-tagged tuples: `("text", "...")` is the definition text, `("vis", [...])` is verbal illustrations (example sentences). There are other tags (`("uns", [...])` for usage notes, `("ca", {...})` for called-also, etc.) — the parser should ignore unknown tags.

### Inline markup tokens

Definition / example text contains placeholders that need stripping for plain-text rendering:

| Token | Meaning |
|---|---|
| `{bc}` | Boldface colon — the marker between sense head and definition; render as `: ` or strip |
| `{it}…{/it}` | Italic — used to highlight the headword inside example sentences; strip the wrappers |
| `{phrase}…{/phrase}` | Inline phrase emphasis |
| `{wi}…{/wi}` | "Word in context" — same purpose as `{it}` |
| `{dx}…{/dx}` | Cross-reference block (compare, see also) — strip for clean text |
| `{sx|word||}` | Synonym-style cross-reference; first pipe segment is the target word |

A `Pattern.compile("\\{[^}]*\\}")` regex strips all of them, but for `{sx|...||}` we should extract the target before stripping. Implementation issue (#436's sibling) decides whether to render markup as Markdown or strip entirely; for the cache layer we store stripped plain text.

---

## 4. Field-by-Field Mapping to `DictionaryEntry`

| `DictionaryEntry` field | M-W Learner's source | Notes |
|---|---|---|
| `word` | `meta.id` (strip the `:N` homograph suffix) or the request slug | Direct mapping |
| `partOfSpeech` | `fl` | Direct; same vocabulary as Free Dictionary (verb / noun / adjective / …) |
| `phonetic` | `hwi.prs[0].ipa` | Single AmE form — Learner's does not include BrE (vs. Cambridge which has both). Already Unicode IPA — no transcoding needed |
| `phonetics` (`List<PhoneticVariant>`) | `hwi.prs[]` | Each entry's `.ipa` + constructed audio URL. Most entries have one variant; some have stress / fast-speech alternates |
| `audioUrl` | Constructed from `hwi.prs[0].sound.audio` | See *§5 Audio* — the value is a token, not a URL |
| `definitions` (`List<Definition>`) | `def[].sseq[][][1].dt` | Walk the four-level tree, emit one `Definition` per `("sense", {...})` tuple. Body = first `("text", ...)` fragment with markup stripped; example = first `t` from the first `("vis", [...])` if any |
| `exampleSentences` | All `vis[].t` across all senses | Strip `{it}` markers; keep order |
| `cefrLevel` | **Not available** | Learner's Dictionary does not expose CEFR / GAL / any difficulty tag — see *§6 Risk 1*. Stays sourced from the existing CEFR wordlist |
| `synonyms` | **Not in this reference** — sibling Thesaurus API | Would be a *third* reference, breaching the "max 2 references" free-tier rule unless we drop one |
| `antonyms` | **Not in this reference** — same as synonyms | |
| `domain` | **Not exposed** | M-W does not tag entries with domain hierarchies the way Cambridge sometimes does |
| `domainPath` | **Not exposed** | |
| `sourceUrls` | Constructed: `https://www.merriam-webster.com/dictionary/{word}` | M-W does not include an entry URL in the response, but the public site URL is deterministic |
| `source` | `"merriam-webster-learners"` (constant) | Composite cache key `(word, source)` already supports this |
| `enrichable` | `true` if state = match; `false` if `[]` *or* string-array suggestions | Suggestion-array case is a not-found in cache terms (no entry to enrich), but the suggestion list itself is worth surfacing to UX |
| `frequencyRank` | **Not exposed** | Already sourced from corpus frequency list |
| `rootId` | `meta.stems[]` | Lemma-grouping hint — the array contains the headword + every related form (`ubiquitous` returns `ubiquitous, ubiquitously, ubiquitousness, ubiquity`). Pick `meta.stems[0]` or use the whole array for synonym-of-form lookups elsewhere |

### Senses / definitions structure

Two-level mapping:

- One `Definition` per `("sense", {...})` tuple at the deepest level of `def[].sseq[][]`
- `partOfSpeech` copied from the parent entry's `fl` (M-W does not vary POS within a sense block)
- `definition` = first `("text", "...")` fragment with markup stripped
- `example` = first `t` value in the first `("vis", [...])` fragment (or null)
- `sls` (status labels like *formal*, *literary*, *chiefly British*, *informal*) is useful future signal — currently no field on `Definition` to carry it; likely worth adding when the aggregator (#356) lands

For the v1 mapping the **`shortdef` array** is the pragmatic shortcut: it's a flat `String[]` of pre-flattened short definitions, identical in count and order to the `app-shortdef.def` projection used by the official MW iOS app. Mapping `definitions` from `shortdef` (one `Definition` per element, no example) is a one-line implementation that covers most practical needs and avoids the four-level `sseq` walk entirely. The full walk only needs to happen if/when we want per-sense examples or `sls` status labels.

### Polysemy & homographs

For words with multiple parts of speech (`run` as verb and noun), Merriam-Webster returns **separate entries** in the response array, distinguished by `meta.id` suffix (`run:1`, `run:2`, …). With our composite `(word, source)` PK, the cache stores one row per word per source, so the client must pick a primary entry or merge across them. Recommended: take the first entry whose `fl` matches the most likely POS for the word's context (the Free Dictionary fallback already needed this kind of merge, so it's not new complexity).

### Phrasal verbs

Phrasal verbs live under `dros[]` (defined run-ons) on the head verb's entry, *not* as separate entries. Looking up "look up" returns the entry for `look` with `look up` as one of many `dros`. To support phrasal-verb lookup we'd need to:

1. Detect multi-token requests client-side
2. Fetch the head verb
3. Search `dros[].drp` for the exact phrase

This is a follow-up implementation concern, not a blocker for this spike.

---

## 5. Audio

- **Format:** MP3 only via the standard URL scheme; `.wav` and `.ogg` are also exposed at parallel paths
- **Variant:** AmE only — Learner's Dictionary does not include British recordings (Cambridge does, both regions). The free Cambridge alternative *or* keeping Free Dictionary's audio for BrE-preferring users is the workaround
- **URL construction:** the response contains `hwi.prs[i].sound.audio` as a *token* (e.g. `"abando01"`), not a URL. Build the URL via M-W's documented scheme:

  ```
  https://media.merriam-webster.com/audio/prons/en/us/{format}/{subdir}/{token}.{format}
  ```

  where `subdir` is derived from the token's first character(s):

  | Token starts with | Subdir |
  |---|---|
  | `bix` | `bix` |
  | `gg` | `gg` |
  | A digit or punctuation | `number` |
  | Anything else | First character of the token |

  Example: token `"abando01"` → `https://media.merriam-webster.com/audio/prons/en/us/mp3/a/abando01.mp3` (verified during this spike: HTTP 200, `audio/mpeg`, ~5 KB).

- **Primary for `audioUrl`:** AmE MP3 (only option)
- **Both formats** (MP3 + OGG) should be exposed in `phonetics` (`List<PhoneticVariant>`) so the frontend can pick by browser support

---

## 6. Risks & Open Questions

| # | Risk / Question | Owner |
|---|---|---|
| 1 | **No CEFR / difficulty tag in the response.** Critical gap vs. Cambridge — the existing CEFR-wordlist mechanism stays as the source of truth for `cefrLevel`. The implementation issue must *not* set MW as the priority source for the CEFR field in `DictionaryAggregator` (#356). | Sub-issue (#356) — aggregator wiring |
| 2 | **Synonyms / antonyms gap** — only available via the separate Thesaurus API. Adding it would consume our second free-tier reference slot, blocking any future third reference. Free Dictionary fallback for synonyms stays. | Sub-issue (#356) |
| 3 | **AmE-only audio + IPA.** No British forms. UX impact is small (most users don't have a strong region preference) but if BrE matters we'd need a Cambridge or Free Dictionary fallback for the `phonetics[uk]` slot. | Product call |
| 4 | **Inline markup tokens** (`{bc}`, `{it}`, `{sx|...}`, etc.) — needs a deterministic stripper. Easy to write, but worth a unit-test suite covering the token zoo. | Sub-issue |
| 5 | **Phrasal verbs are nested under head verbs**, not standalone entries. Our cache key `(word, source)` handles multi-word "words" fine, but the lookup path needs to detect the multi-token case and search `dros[].drp` after fetching the head. | Sub-issue (later, if phrasal verbs are in scope) |
| 6 | **Commercial licence cost is unknown.** Same as Cambridge — needs a quote before launch. Difference: free dev work isn't blocked while we wait. | Human — request quote near launch |

---

## 7. Recommendation

**Use Merriam-Webster Learner's Dictionary as the primary upstream for definitions, examples, IPA, and audio.** Contingency rules:

1. **If Cambridge ghosts or rejects (#355):** MW becomes the launch primary with no rework needed — its field coverage is sufficient for every functional UX surface that doesn't depend on CEFR labels (definitions, examples, audio, IPA).
2. **If Cambridge offers reasonable terms:** keep both, and let the aggregator (#356) prefer Cambridge for the fields where it is strictly richer:
   - `cefrLevel` — Cambridge **only**, since MW does not expose it
   - `phonetics[uk]` (BrE IPA + audio) — Cambridge **only**
   - `definitions`, `exampleSentences`, `synonyms` — pick by quality / coverage on a per-call basis (Cambridge tends to have shorter, learner-tuned definitions and 1-3 examples per sense; MW Learner's has more verbose definitions and often more examples — both are fine)
3. **Synonyms remain a Free Dictionary responsibility** until a dedicated thesaurus integration is greenlit.

The MW client implementation (sibling sub-issue) is *small* compared to the Cambridge one:

- No XML parser required (vs. Cambridge's XML-in-JSON `entryContent`)
- `shortdef` array gives a one-line definition mapping
- Deterministic audio URL construction
- Three-state response handling is mechanical

Estimate: ~1–2 days for a clean MW client + cache integration, vs. ~3–5 for Cambridge given the XML parsing cost.

### Decision summary

| Outcome | Concrete next steps |
|---|---|
| MW selected as primary or supplementary | Open implementation sub-issue under #350: client + parser + aggregator priority rules |
| MW skipped | Close #436 with a "decision: skipped" comment; nothing else to revert (no production code, secret can stay or be deleted) |

Default: **proceed with MW** — the schedule risk reduction (no licensing wait) outweighs the field-coverage gaps, all of which already have Free Dictionary or wordlist fallbacks.
