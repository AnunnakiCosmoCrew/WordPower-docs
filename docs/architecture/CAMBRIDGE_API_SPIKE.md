# Spike: Cambridge Dictionary API — Research Findings

> Addresses GitHub issue #353 (sub-issue of epic #350)
> Date: 2026-05-04

---

## 1. Registration & Commercial Tier

### Sign-up process

1. Register a developer account at `https://dictionary-api.cambridge.org/registration`  
   (name, username, password, email, organisation, address; country/website optional)
2. Submit a licensing application at `https://dictionary-api.cambridge.org/apply`  
   Cambridge asks for: organisation details, use case, target market, dictionary dataset needed, revenue model, Cambridge-brand usage intent.
3. Cambridge responds within **~10 business days** with a licensing offer.

### No free commercial tier

**Critical finding: the "3 k calls/month free" figure is from a 2012 TechCrunch article and is no longer offered.**

The current developer hub explicitly states:

> *"We do not provide free access to our API for research or prototyping purposes."*

Access tiers as of research date:

| Tier | Calls/month | Cost |
|---|---|---|
| Evaluation (30-day trial) | Unspecified | Free |
| Free ongoing commercial | **Does not exist** | — |
| Paid | Custom | Negotiated per licence |

**Action required (human):** register, apply, and negotiate a licence before any production integration begins. Budget should assume a paid arrangement.

### Commercial-use classification

The licensing application asks for revenue model and brand-usage intent. WordPower is a commercial product (App Store distribution, potential subscription revenue), so it must register as **commercial**. The "non-commercial subject to negotiation" clause on the agreement page does **not** apply.

---

## 2. API Basics

| Property | Value |
|---|---|
| Base URL | `https://dictionary.cambridge.org/api/v1/` |
| Authentication | HTTP header `accessKey: <your-key>` |
| Response format | JSON envelope; lexical content as HTML5 or XML blob |
| Supported dictionaries | Multiple (e.g. `cambridge-english`, `english`, etc.) |

### Key endpoints

| Purpose | Endpoint |
|---|---|
| List available dictionaries | `GET /dictionaries` |
| Search (all matches) | `GET /dictionaries/{dictCode}/search?q={term}` |
| Best match | `GET /dictionaries/{dictCode}/search/first?q={term}` |
| Fetch entry by ID | `GET /dictionaries/{dictCode}/entries/{entryId}` |
| Pronunciations | `GET /dictionaries/{dictCode}/entries/{entryId}/pronunciations` |

---

## 3. Response Shape

### Critical design note — no clean JSON tree

The outer wrapper is JSON, but **lexical content lives inside `entryContent`** as an HTML5 or XML blob (DTD: `https://dictionary-api.cambridge.org/resources/xml-lite.dtd`). A dedicated XML parser is required to extract individual fields; you cannot treat the response as a flat JSON document.

```json
{
  "dictionaryCode": "cambridge-english",
  "entryId": "example_1",
  "entryLabel": "example",
  "entryUrl": "https://dictionary.cambridge.org/dictionary/english/example",
  "format": "xml",
  "entryContent": "<...XML blob...>"
}
```

### XML element reference (inside `entryContent`)

| Concept | XML element | Notes |
|---|---|---|
| Sense group | `<sense-block>` | Groups all definitions for one guideword |
| Guideword | `<gw>` | Human-readable sense label, e.g. "OPINION" |
| Definition container | `<def-block>` | One definition within a sense-block |
| Definition text | `<def>` | Plain text definition |
| IPA phonetics | `<ipa>` | Inside a `<pron>` element |
| CEFR level | `<lvl>` | Inside an `<info>` block; values A1–C2 |
| Example container | `<examp>` | |
| Example sentence | `<eg>` | 1–3 per sense typically |
| Incorrect usage example | `<xeg>` | Shown struck-through on site |
| Audio source | `<source>` | `type` = `audio/mpeg` or `audio/ogg`; `src` = URL |
| Audio pronunciation block | `<audio>` | Has `region` attribute for `uk`/`us` |

### Pronunciations endpoint (cleaner JSON)

```json
{
  "dictionaryCode": "cambridge-english",
  "entryId": "example_1",
  "lang": "uk",
  "pronunciationUrl": "https://dictionary.cambridge.org/media/english/uk_pron/u/uke/ukex_/ukexam_029.mp3"
}
```
Supports query params: `format=mp3|ogg`, `lang=uk|us`.

---

## 4. Field-by-Field Mapping to `DictionaryEntry`

| `DictionaryEntry` field | Cambridge source | Notes |
|---|---|---|
| `word` | `entryLabel` (outer JSON) | Direct mapping |
| `partOfSpeech` | `<pos>` in XML blob | Requires XML parsing |
| `phonetic` | `<ipa>` (BrE preferred) | Requires XML parsing; take first `<ipa>` under `uk` audio block |
| `phonetics` (`List<PhoneticVariant>`) | `<ipa>` + `<source src>` per region | Map two variants: BrE + AmE, each with IPA text and audio URL |
| `audioUrl` | `<source src>` (MP3, BrE `uk`) | Set primary to UK MP3; fall back to US if unavailable |
| `definitions` (`List<Definition>`) | `<sense-block>` → `<def-block>` → `<def>` | Each `<def-block>` yields one `Definition`; carry `<gw>` as a sub-sense label |
| `exampleSentences` | `<eg>` text across all senses | Aggregate all `<eg>` elements; exclude `<xeg>` (incorrect-usage examples) |
| `cefrLevel` | `<lvl>` (A1–C2) | Single value per entry (or first sense); compatible with existing CHECK constraint |
| `synonyms` | **Not available in entry responses** | Cambridge thesaurus is a separate endpoint; see note below |
| `antonyms` | **Not available in entry responses** | Same as synonyms |
| `domain` | `<domain>` element (if present) | May be absent for common words |
| `domainPath` | `<domain>` hierarchy | |
| `sourceUrls` | `entryUrl` (outer JSON) | Single source URL |
| `source` | `"cambridge"` (constant) | |
| `enrichable` | `true` if entry found | `false` for 404 responses |
| `frequencyRank` | **Not exposed** | Not present in Cambridge API |
| `rootId` | **Not exposed** | Not present in Cambridge API |

### Synonyms — important gap

Cambridge entry responses **do not include synonyms or antonyms inline**. Synonym data is available through a separate thesaurus-browsing endpoint, but it is not keyed by the entry ID — it requires a different lookup flow. For the multi-source aggregation plan in epic #350, **Free Dictionary remains the fallback source for synonyms and antonyms**, and Cambridge will only contribute `null` / empty list for these fields unless the thesaurus endpoint is wired up in a separate sub-issue.

### Senses / definitions structure

Cambridge uses a two-level hierarchy:

```
sense-block (guideword: "OPINION")
  └── def-block
        ├── def: "your thoughts or your ability to think..."
        ├── lvl: A2
        └── examp → eg: "She has a very logical mind."
  └── def-block
        ├── def: "a very intelligent person"
        └── examp → eg: "She is one of the great minds of our time."
```

Proposed mapping to `Definition` record (`partOfSpeech`, `definition`, `example`, `synonyms`, `antonyms`):
- One `Definition` entry per `<def-block>`
- `partOfSpeech` copied from parent `<pos>` element
- `definition` = `<def>` text
- `example` = first `<eg>` text within the same `<def-block>` (or null)
- CEFR level from `<lvl>` stored on the parent `DictionaryEntry`, not per-definition (Cambridge assigns level at word level, not per sense in most cases)

---

## 5. Audio

- **Formats:** MP3 (`audio/mpeg`) and OGG (`audio/ogg`) — both available
- **Variants:** BrE (region `uk`) and AmE (region `us`)
- **URL structure:** e.g. `https://dictionary.cambridge.org/media/english/uk_pron/u/ukm/ukmin/ukmind_029.mp3`
- **Primary for `audioUrl` field:** UK MP3 (consistent with Cambridge's ESL focus)
- **Both variants** should be stored in `phonetics` (`List<PhoneticVariant>`) for downstream use

---

## 6. Risks & Open Questions

| # | Risk / Question | Owner |
|---|---|---|
| 1 | **No free tier** — must negotiate licence before any integration. Timeline unknown (~10 business days + negotiation). | Human (registration step) |
| 2 | **XML blob parsing** — no clean JSON tree. Needs a proper XML parser (JAXB, Jackson-XML, or DOM). Adds implementation complexity. | Sub-issue #355 |
| 3 | **Synonyms gap** — thesaurus endpoint is separate and not part of entry lookup. Free Dictionary fallback stays for synonyms. | Sub-issue #356 aggregation logic |
| 4 | **CEFR at word level vs. sense level** — Cambridge assigns CEFR to the whole entry in most cases. Some multi-sense words may have per-sense levels. | Spike follow-up if needed |
| 5 | **Evaluation key for dev** — request a 30-day trial key immediately after registration so integration work (sub-issue #355) is not blocked. | Human |

---

## 7. Recommendation

Proceed with the integration plan from epic #350 with two adjustments:

1. **Budget for a paid licence.** The 3 k free tier does not exist. Get a quote immediately after registering.
2. **Use an XML parser for `entryContent`.** The Cambridge API is not a clean JSON API; all lexical data is in an XML blob. Sub-issue #355 must plan for XML parsing, not JSON field mapping.

Everything else (CEFR, audio, IPA BrE + AmE, sense structure, example sentences) is confirmed present and maps cleanly to `DictionaryEntry`.
