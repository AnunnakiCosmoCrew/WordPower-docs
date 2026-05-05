# Spike: Oxford Dictionary API — Research Findings

> Addresses GitHub issue #445 (sub-issue of epic #350). Replacement candidate for Cambridge (#353, shelved 2026-05-04).
> Date: 2026-05-05

---

## 1. Registration & Commercial Tier

### Sign-up process

1. Register a developer account at `https://account.oxforddictionaries.com/sign-up`
   (name, email, organisation).
2. Select a plan and pay — Oxford uses self-serve billing (credit card), unlike Cambridge's negotiated-licensing model.
3. Credentials (`app_id` + `app_key`) are available immediately after plan activation.

**Approval is same-day** (self-serve), similar to Merriam-Webster and in stark contrast to Cambridge's ~10-business-day licensing process.

### Free tier — sandbox

Oxford offers a **Sandbox** (free) tier:

| Property | Value |
|---|---|
| Total call budget | 500 calls (one-time pool, not monthly reset) |
| Vocabulary restriction | **Words beginning with 'A' only** (in any language) |
| Rate limit | 100 requests per 300 seconds |
| Purpose | Evaluation only |

The 'A' restriction makes the sandbox effectively useless for testing real word coverage. It serves as a "hello world" credential check but cannot simulate production workloads.

### Paid tiers (as of January 2025 relaunch)

Oxford relaunched its API offering on 9 January 2025. Previous tier naming (e.g. "Prototype", "Advanced") was replaced:

| Tier | Monthly cost (billed annually) | Calls / month | Overage rate |
|---|---|---|---|
| **API Lite** | £50 (£600/year) | 5,000 | £0.05 / call |
| **Growing Business** | £200 (£2,400/year) | 50,000 | £0.01 / call |
| **Enterprise** | £415+ (£5,000+/year) | 500,000 | £0.005 / call |

Overage is charged automatically — the API does not cut off at the limit.

**Minimum viable cost for commercial use: £600/year (API Lite).**

### Compared to Cambridge and Merriam-Webster

| | Merriam-Webster Learner's | Cambridge | Oxford |
|---|---|---|---|
| Free non-commercial tier | Yes — 1,000/day | No | 500 calls (sandbox only) |
| Approval time | Same-day | ~10 business days | Same-day |
| Minimum commercial cost | Quote required | "Low five figures annually" | £600/year (confirmed) |
| Persistent caching | Allowed | Banned | Banned by default (Enterprise deal possible) |

---

## 2. API Basics

| Property | Value |
|---|---|
| Base URL | `https://od-api.oxforddictionaries.com/api/v2/` |
| Authentication | HTTP headers — `app_id: <id>` and `app_key: <key>` (both required) |
| Response format | **JSON, end-to-end** — no XML/HTML blob (contrast Cambridge) |
| Languages | English (en-gb, en-us), and 10+ others |

### Key endpoints

| Purpose | Endpoint |
|---|---|
| Word entry (definitions, phonetics, audio) | `GET /entries/{language}/{word}` |
| Thesaurus (synonyms / antonyms) | `GET /thesaurus/{language}/{word}` |
| Example sentences | `GET /sentences/{language}/{word}` |
| Lemma lookup | `GET /lemmas/{language}/{word}` |
| Lexical categories | `GET /lexicalcategories/{language}` |

---

## 3. Response Shape

### Overview

The `entries` response is a clean JSON document — no embedded XML/HTML to parse (a significant improvement over Cambridge's `entryContent` XML blob).

```json
{
  "metadata": {
    "provider": "Oxford University Press"
  },
  "results": [
    {
      "id": "publish",
      "language": "en-gb",
      "lexicalEntries": [
        {
          "lexicalCategory": { "id": "verb", "text": "Verb" },
          "pronunciations": [
            {
              "audioFile": "https://audio.oxforddictionaries.com/en/mp3/publish_gb_1.mp3",
              "dialects": ["British English"],
              "phoneticNotation": "IPA",
              "phoneticSpelling": "ˈpʌblɪʃ"
            },
            {
              "audioFile": "https://audio.oxforddictionaries.com/en/mp3/publish_us_1.mp3",
              "dialects": ["American English"],
              "phoneticNotation": "IPA",
              "phoneticSpelling": "ˈpʌblɪʃ"
            }
          ],
          "entries": [
            {
              "senses": [
                {
                  "definitions": [
                    "prepare and issue (a book, journal, or piece of music) for public sale"
                  ],
                  "examples": [ { "text": "the company publishes a newsletter" } ],
                  "domainClasses": [ { "id": "media", "text": "Media" } ],
                  "registers": []
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

**Key omission:** no CEFR level field in the response — see §4 CEFR below.

### Thesaurus endpoint

Synonyms and antonyms live in a separate call:

```
GET /thesaurus/en/{word}
```

Returns `synonyms[]` and `antonyms[]` arrays per sense. Requires a second API call (adds latency and consumes quota).

---

## 4. Field-by-Field Mapping to `DictionaryEntry`

| `DictionaryEntry` field | Oxford source | Notes |
|---|---|---|
| `word` | `results[].id` | Direct mapping |
| `partOfSpeech` | `lexicalEntries[].lexicalCategory.id` | Clean JSON — no XML parsing |
| `phonetic` | First `pronunciations[].phoneticSpelling` where `dialects` contains `"British English"` | IPA; prefer BrE for primary |
| `phonetics` (`List<PhoneticVariant>`) | All entries in `pronunciations[]` | BrE + AmE both present as separate objects |
| `audioUrl` | `pronunciations[].audioFile` for `"British English"` dialect | MP3 format, BrE primary |
| `definitions` (`List<Definition>`) | `entries[].senses[].definitions[]` | One `Definition` per definition string |
| `exampleSentences` | `entries[].senses[].examples[].text` | Per-sense array; quality drawn from OUP corpus |
| `cefrLevel` | **NOT AVAILABLE** | Critical gap — see §4.1 |
| `synonyms` | Separate `/thesaurus/{language}/{word}` call | Not bundled in entry response |
| `antonyms` | Same thesaurus endpoint | |
| `domain` | `entries[].senses[].domainClasses[].text` | e.g. "Medicine", "Business" |
| `domainPath` | `domainClasses[].id` | Normalised slug |
| `sourceUrls` | Constructed: `https://www.oxfordlearnersdictionaries.com/definition/english/{word}` | No canonical URL in response |
| `source` | `"oxford"` (constant) | |
| `enrichable` | `true` if results array non-empty | HTTP 404 = not found |
| `frequencyRank` | **Not exposed** | Already sourced from corpus frequency list |
| `rootId` | **Not exposed** | Would need lemma endpoint for this |

### 4.1 CEFR — critical gap

**CEFR level is NOT returned in the Oxford Dictionaries API entry response.**

Oxford Learner's Dictionaries (the website at `oxfordlearnersdictionaries.com`) organises its content by CEFR level, and the Oxford 3000/5000 word lists are CEFR-tagged (A1–C2 and B2–C1 respectively), but this data is not surfaced in any documented field of the `/entries` API response.

A separate product, the Oxford Learner's Dictionaries API (`languages.oup.com/oxford-learners-dictionaries-api/`), exists and may return CEFR labels, but its documentation at time of research is sparse and its pricing/licensing appear distinct from the standard Oxford Dictionaries API.

**This is the single most critical unresolved question for the WordPower integration decision.** See §7 (Action Items) for the exact question to send to OUP.

---

## 5. Audio

- **Format:** MP3 (`audio/mpeg`) — direct URL in response (no token-to-URL construction needed, contrast M-W)
- **Variants:** British English (`"British English"` in `dialects[]`) and American English (`"American English"`) — both present as separate `pronunciations[]` entries
- **URL structure:** `https://audio.oxforddictionaries.com/en/mp3/{word}_{dialect}_1.mp3`
- **Primary for `audioUrl`:** BrE MP3 (consistent with OUP's ESL focus)
- **Both variants** stored in `phonetics` (`List<PhoneticVariant>`) for downstream use

**Advantage over Merriam-Webster:** Oxford provides BrE audio; M-W only provides AmE.

---

## 6. Licensing — deal-breaker analysis

Cambridge established the checklist for licensing blockers. Findings for Oxford against each criterion:

### 6.1 Free app distribution (App Store / Play Store, freemium)

**Status: AMBIGUOUS — requires written confirmation before integration.**

The Oxford API Terms and Conditions permit both "commercial and non-commercial use" in principle, but no clause explicitly addresses free-distributed apps with optional paid features (freemium). The distinction between a commercial _product_ (generates revenue) and a free _distribution_ (monetised via in-app purchase or subscriptions) is not addressed in the public documentation.

Cambridge's explicit ban on "free products / personal projects" makes Oxford's silence look permissive by comparison, but relying on implied permission for a production system is unacceptable.

**Action required:** Confirm in writing before launch — see §7 (Action Items).

### 6.2 Persistent caching in PostgreSQL

**Status: FORBIDDEN by the standard terms — custom Enterprise deal required.**

The Terms and Conditions contain:

> "You will not cache, store, or save Content."

Session-level caching is permitted as a narrow exception:

> "You may employ user-level session caching of the formatted display of Content solely for the purpose of displaying Content in your application."

This explicitly permits in-memory / browser-session caching but prohibits:
- Storing entries in a persistent database (`dictionary_cache`)
- Offline mode
- Any form of bulk download

**To enable persistent caching:**
- Negotiate a custom Enterprise licence agreement with OUP Licensing
- Enterprise tier starts at £5,000/year for one language; caching rights require an additional licence fee (amount not public)
- Contact: `ELT.LicensingandPartnerships@oup.com`

**Verdict:** More negotiable than Cambridge (Cambridge had an unconditional ban; Oxford permits it via Enterprise deal), but still a blocker for the current API Lite / Growing Business tiers. The entire persistent-cache architecture (#354) depends on this right being granted.

### 6.3 Branding / attribution

**Required:** "Powered by Oxford Dictionaries" must appear in the product or UI.

This is compatible with a visible credits section in the app. No logo or splash-screen requirement is specified.

### 6.4 Search engine exposure

No explicit search-engine clause found in the public Terms and Conditions. Oxford prohibits bulk scraping and derivative APIs but does not mirror Cambridge's blanket prohibition on any exposure to search engine indexing. A mobile app serving definitions to logged-in users falls well outside these restrictions.

---

## 7. Risks & Open Questions

| # | Risk / Question | Owner |
|---|---|---|
| 1 | **CEFR not returned by API.** Most critical technical gap — if Oxford cannot provide CEFR the main differentiator over M-W is lost. May be available via Oxford Learner's Dictionaries API (separate product). | Human — contact OUP (see below) |
| 2 | **Free app distribution not confirmed.** Ambiguous in public T&C. Must be resolved before using in any released build. | Human — written confirmation from OUP |
| 3 | **Persistent caching banned on standard tiers.** Requires Enterprise deal at unknown additional cost. | Human — contact `ELT.LicensingandPartnerships@oup.com` |
| 4 | **500-call sandbox can only fetch 'A' words.** Integration testing against the sandbox is too limited to be useful. Need at least API Lite to properly test coverage. | If licensed: test with real API Lite key |
| 5 | **Thesaurus is a separate endpoint.** Synonyms / antonyms require a second call, doubling quota consumption for words where those fields are needed. | Sub-issue (#356 aggregation wiring) |
| 6 | **Pricing confirmed as of Jan 2025 relaunch; may change.** Monitor at `developer.oxforddictionaries.com/updates`. | Ongoing |

### 7.1 Required written confirmations before proceeding

**1. CEFR level support**
- Contact: `developer-support@oxforddictionaries.com`
- Question: "Does the `/entries/{language}/{word}` endpoint return a CEFR level (A1–C2) in the response? If so, in which field? On which pricing tier? Does it label every entry or only words in the Oxford 3000/5000 list?"
- Fallback to explore: Is the Oxford Learner's Dictionaries API (separate product) an alternative, and does it include CEFR?

**2. Free app distribution**
- Contact: `ELT.LicensingandPartnerships@oup.com`
- Question: "Our app is distributed free of charge on the App Store and Google Play. Users can unlock premium features via in-app purchase. May we use the Oxford Dictionaries API under the API Lite or Growing Business plan?"

**3. Persistent caching cost**
- Contact: `ELT.LicensingandPartnerships@oup.com`
- Question: "We intend to cache dictionary entries in a PostgreSQL database for offline access. What would a custom licence cost to permit this, and on what terms?"

---

## 8. Recommendation

**Path B — Defer Oxford until monetisation; launch with Merriam-Webster only.**

Rationale:

1. **CEFR is non-negotiable.** WordPower's CEFR-level display and quiz difficulty filtering both depend on per-word CEFR labels. M-W does not expose CEFR; if Oxford cannot either, the main reason to pay £600+/year evaporates. This question must be answered before any integration investment is made.

2. **Persistent caching is banned on affordable tiers.** The entire `dictionary_cache` architecture (#354) assumes the right to store entries persistently. The standard API Lite / Growing Business tiers prohibit this. A custom Enterprise deal costs an unknown amount on top of £5,000+/year base — likely incompatible with a pre-revenue product.

3. **Free app licensing is unconfirmed.** Integrating Oxford before written confirmation is the same risk Cambridge represented.

4. **M-W unblocks launch.** Merriam-Webster Learner's is free for development and covers definitions, IPA, AmE audio, and examples. These are sufficient for the launch feature set. CEFR labels are already sourced from the Oxford 3000/5000 static word lists, not the API.

5. **Provider abstraction.** The `DictionaryAggregator` design from #356 already expects multiple pluggable sources. Adding Oxford later is a new source implementation under the existing interface — no structural rework required.

**Trigger to revisit Oxford:**
- OUP confirms in writing that CEFR is returned by the API, and
- OUP confirms in writing that free App Store distribution is permitted, and
- Either the caching ban is lifted (Enterprise deal priced acceptably) or an architecture decision confirms that session-level lookup without persistent storage is viable for the Oxford fields specifically

**If all three are confirmed:** recommend Path A — Oxford as commercial primary for prod (M-W retained for free dev/staging tier), with the Oxford Learner's Dictionaries API as the preferred product if it exposes CEFR.

**If CEFR is definitively unavailable:** recommend Path C — skip Oxford; open a separate sub-issue for a CEFR-mapping table derived from the static Oxford 3000/5000 + CEFR-J word lists.

---

## 9. Comparison summary

| Criterion | Merriam-Webster Learner's | Cambridge (shelved) | Oxford |
|---|---|---|---|
| Free dev tier | Yes — 1,000 calls/day | No | 500-call sandbox (unusable) |
| Commercial minimum cost | Quote required | "Low five figures/year" | £600/year |
| Free app distribution | Permitted (non-commercial only) | Banned | Ambiguous |
| Persistent caching | Allowed | Banned | Banned (Enterprise deal possible) |
| CEFR level in API | No | Yes | Not confirmed |
| IPA — BrE | No (AmE only) | Yes | Yes |
| Audio — BrE + AmE | No (AmE only) | Yes | Yes |
| Synonyms in entry call | No (separate Thesaurus ref) | No (separate endpoint) | No (separate endpoint) |
| Response format | JSON | JSON-wrapped XML blob | JSON |
| Attribution required | No | Yes | Yes — "Powered by Oxford Dictionaries" |
