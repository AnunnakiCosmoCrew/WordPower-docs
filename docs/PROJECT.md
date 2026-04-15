# WordPower (Working Title) — Project Document

> A personal word notebook that turns everyday vocabulary discoveries into lasting knowledge — collect words from daily life, and let the app teach you their meaning, spelling, pronunciation, and related vocabulary through quizzes, flashcards, and spaced repetition.

**Project Manager:** Mert Ertugrul
**Originally Conceived:** January 17, 2024
**Platform:** Flutter (iOS & Android)

---

## 1. Vision

WordPower is a personal word notebook. Users collect words they encounter in daily life — from conversations, books, articles, exams, or anywhere else — and jot them down like they would in a notebook. The app then enriches each word with its meaning, pronunciation, synonyms, CEFR level, and semantic domain. It also surfaces similar words at the same level or in the same category, helping users expand their vocabulary organically. Through quizzes, spelling drills, pronunciation listening, flashcards, and vocabulary exercises, the app turns a personal word collection into deep, lasting knowledge. Words resurface at scientifically-timed intervals so users spend time on what they actually need to review.

## 2. Core Features

### 2.1 Word Management

| Feature | Description |
|---|---|
| **Manual Entry** | Users add words with their own definitions, notes, and example sentences |
| **Dictionary API Lookup** | Type a word and auto-fetch its definition, pronunciation (audio + phonetic), part of speech, and example usage |
| **Bulk Import** | Import word lists from CSV or Excel files |
| **Word Detail View** | Shows definition, pronunciation (with audio playback), example sentences, part of speech, synonyms/antonyms, and personal notes |
| **Word Lists / Folders** | Organize words into custom collections (e.g., "IELTS", "Business", "Daily") |
| **Word Domains** | Every word is tagged with a semantic domain and CEFR level (see Section 2.6) |

### 2.2 Learning & Quiz Engine

| Quiz Type | How It Works |
|---|---|
| **Flashcards** | Show word → reveal definition (and vice versa). User self-rates: Easy / Good / Hard / Again |
| **Multiple Choice** | Given a word, pick the correct definition from 4 options (or given a definition, pick the word) |
| **Spelling** | Hear the word pronounced → type the correct spelling |
| **Listening** | Hear the word → select the correct definition or type the word |
| **Matching** | Match a set of words to their definitions by dragging/tapping |
| **Fill-in-the-Blank** | Complete a sentence with the correct word from the user's database |

### 2.3 Spaced Repetition System (SRS)

- Algorithm based on SM-2 (SuperMemo 2) or a modern variant (FSRS)
- Each word has a familiarity score, interval, and next review date
- Daily review queue is generated automatically based on due words
- Performance in any quiz type feeds back into the SRS scheduling
- Dashboard shows: words due today, mastered count, learning streak

### 2.4 Pronunciation & Audio

- Text-to-speech (TTS) for word pronunciation
- Dictionary API audio where available (higher quality, native speaker)
- Phonetic transcription display (IPA)

### 2.6 Word Domain & Level System

Every word in the app lives on two axes: **what it's about** (semantic domain) and **how advanced it is** (CEFR level). This lets users browse, filter, and study vocabulary by topic, difficulty, or both.

Every word in WordPower lives on three axes:

```
         AXIS 1                AXIS 2              AXIS 3
      What it's about       How hard it is      How it's built
     ──────────────        ──────────────      ──────────────
     Semantic Domain         CEFR Level        Root Family

     Travel & Places            A2             port- (to carry)
           │                    │                    │
           ▼                    ▼                    ▼
       "transport"          "transport"         "transport"
       "commute"            "recipe"            "export"
       "itinerary"          "luggage"           "import"
                                                "portable"
                                                "support"
```

Users can explore vocabulary from any axis — by topic, by difficulty, or by word family. Learning one root unlocks 10+ words.

#### Axis 1: Semantic Domain Tree

Inspired by the Historical Thesaurus of the OED (HTOED), reorganized for modern learners:

```
WordPower Domains
│
├── The Physical World
│   ├── Nature (weather, seasons, geography, animals, plants)
│   ├── Body & Health (body parts, illness, medicine, fitness)
│   ├── Food & Drink (cooking, meals, ingredients, dining)
│   ├── Home & Living (furniture, rooms, household, clothing)
│   └── Science & Technology (physics, chemistry, computing, AI)
│
├── The Mind
│   ├── Emotions & Feelings (joy, anger, fear, surprise, love)
│   ├── Thinking & Learning (logic, memory, creativity, education)
│   ├── Communication (speech, writing, argument, persuasion)
│   └── Character & Personality (traits, virtues, flaws)
│
└── Society
    ├── Work & Business (careers, finance, management, trade)
    ├── Travel & Places (transport, accommodation, destinations)
    ├── Culture & Arts (music, film, literature, sports)
    ├── Relationships (family, friendship, social, romance)
    ├── Law & Politics (government, justice, rights, crime)
    └── Daily Life (shopping, time, numbers, routines)
```

#### Axis 2: CEFR Levels

| Level | Label | Example words |
|---|---|---|
| **A1** | Beginner | head, water, hotel, job |
| **A2** | Elementary | stomach, recipe, luggage, salary |
| **B1** | Intermediate | diagnosis, cuisine, commute, negotiate |
| **B2** | Upper Intermediate | ailment, palatable, vicinity, leverage |
| **C1** | Advanced | prognosis, epicurean, expatriate, fiduciary |
| **C2** | Mastery | visceral, voracious, itinerant, arbitrage |

#### Axis 3: Word Root Families

Words are grouped by their morphological root — the core unit of meaning that generates entire word families through prefixes and suffixes.

**Root origins:**

| Origin | Character | Example roots |
|---|---|---|
| **Germanic** (Old English) | Everyday, simple, emotional | hand-, break-, love-, stand-, light- |
| **Latin** (via French) | Formal, academic, professional | port-, dict-, duct-, ject-, rupt-, scrib- |
| **Greek** | Scientific, technical, medical | graph-, log-, phon-, bio-, psych-, chron- |

**How a root family expands:**

```
Root: port- (Latin: "to carry")
│
├── trans + port         = transport (carry across)
├── ex + port            = export (carry out)
├── im + port            = import (carry in)
│   └── import + -ant    = important (carrying weight)
├── re + port            = report (carry back)
├── de + port            = deport (carry away)
├── sup + port           = support (carry from below)
├── port + -able         = portable (can be carried)
├── port + -er           = porter (one who carries)
└── port + -folio        = portfolio (carry + leaf/page)
```

**Prefix meanings (how they change the root):**

| Prefix | Meaning | With "port" | With "duct" | With "ject" |
|---|---|---|---|---|
| trans- | across | transport | transduct | — |
| ex- | out | export | — | eject |
| im-/in- | in | import | induct | inject |
| re- | back/again | report | reduce | reject |
| de- | away/down | deport | deduct | — |
| pro- | forward | — | produce | project |
| con- | together | — | conduct | — |
| sub-/sup- | under/below | support | — | subject |

**Suffix meanings (how they change word class):**

| Suffix | Creates | Example |
|---|---|---|
| -tion, -sion | noun (action/result) | act → ac**tion**, export → exporta**tion** |
| -ment | noun (result/state) | enjoy → enjoy**ment**, govern → govern**ment** |
| -ness | noun (quality) | happy → happi**ness**, dark → dark**ness** |
| -able, -ible | adjective (can be) | break → break**able**, port → port**able** |
| -ive | adjective (tending to) | act → act**ive**, product → product**ive** |
| -ous, -ful | adjective (full of) | danger → danger**ous**, hope → hope**ful** |
| -ly | adverb (in the manner of) | quick → quick**ly**, active → active**ly** |
| -ize, -ify | verb (to make) | modern → modern**ize**, simple → simpl**ify** |
| -er, -or, -ist | noun (person who) | teach → teach**er**, act → act**or**, art → art**ist** |

**Exceptions and traps (the app should highlight these):**

| Trap | Example | Why |
|---|---|---|
| **False roots** | "uncle" is not un- + cle; "island" is not is- + land | Not all letter patterns are morphemes |
| **Meaning drift** | "awful" meant "full of awe" (positive), now means terrible | Meaning shifted over centuries |
| **Irregular negation** | im-possible, un-able, ir-regular, dis-loyal, in-accurate | Prefix depends on Latin vs Germanic origin and first letter |
| **Unpredictable suffixes** | "action" but "amazement" (not "amazion"); "happiness" but "boredom" (not "boreness") | Historical/phonological reasons |
| **Dead metaphors** | "understand" ≠ "under" + "stand"; "breakfast" = "break" + "fast" (stop fasting) | Compound origins lose literal meaning |
| **Ambiguous affixes** | "unlockable" = "able to unlock" or "not lockable"? | Structural ambiguity — context required |
| **Register pairs** | begin (Germanic) vs commence (Latin) — same meaning, different formality | English has parallel vocabularies from different origins |

#### Data Sources — Three Tiers

WordPower's word intelligence comes from three tiers: paid API, free open data, and copyrighted reference material studied to inform our design.

**Tier 1 — Paid Integration (direct API calls)**

| Source | What it provides | Cost |
|---|---|---|
| **Oxford Dictionaries API** | Definitions, pronunciation audio, phonetics, examples, part of speech | ~£50/mo (cached) |

**Tier 2 — Free/Open Data (shipped as static assets or Firestore collections)**

| Source | What it provides | License |
|---|---|---|
| **Open English WordNet (2025)** | 117K+ synonym sets (synsets), semantic hierarchy (is-a, part-of), antonyms, definitions. Primary source for synonyms, related words, and domain auto-tagging. | CC BY 4.0 |
| **CEFR-J / Words-CEFR-Dataset** | Word → CEFR level mapping with POS, ~7,600 words. Primary source for level assignment. | Free for commercial use |
| **Wordfreq** | Word frequency data across multiple corpora, 400K+ words. Powers "learn useful words first" and supplements CEFR leveling. | MIT |
| **Roget's Thesaurus 1911** | 1,022 thematic categories with word clusters. Supplements WordNet with broader thematic groupings for quiz distractors and word discovery. | Public domain |

**Tier 3 — Copyrighted Reference (studied, not copied)**

These are purchased/subscribed to, studied for methodology and structure, then used to inform our own original domain taxonomy and learning design. No data is extracted or redistributed.

| Source | What we learn from it | Access |
|---|---|---|
| **HTOED** (Historical Thesaurus of the OED) | How to structure a semantic taxonomy of English — the three-tier division (External World / Mind / Society), how categories relate hierarchically, how to handle words that belong in multiple domains | OED subscription (~£100/yr) |
| **David Crystal — Words in Time and Place** | How semantic fields work in practice across 15 worked examples, how words within a field relate chronologically and thematically, what makes a good domain boundary | Book (~£15) |
| **English Vocabulary Profile (full)** | How Cambridge assigns CEFR levels — what criteria distinguish B1 from B2, how polysemous words get different levels per sense, how collocations factor in | Cambridge site (free lookup, study methodology) |
| **Oxford Learner's Dictionaries** | How Oxford organizes topic vocabulary for learners, which semantic groupings work best for language education, how to balance breadth vs depth per topic | Free online access |

#### How Levels Get Assigned Automatically

Words are auto-tagged when fetched from the Oxford API using these sources (in priority order):

1. **CEFR-J Dataset** — Direct word → level lookup in the 20MB SQLite database. Covers ~7,600 common words.
2. **Wordfreq ranking** — For words not in CEFR-J, frequency rank is mapped to a CEFR level (top 1,000 → A1-A2, top 3,000 → B1, top 6,000 → B2, top 10,000 → C1, beyond → C2). Methodology informed by studying the English Vocabulary Profile.
3. **Oxford API metadata** — Register and frequency info from the API response itself.
4. **Fallback** — Words not found in any source default to B2 (upper intermediate) and can be manually adjusted.

#### How Domains Get Assigned Automatically

1. **WordNet semantic hierarchy** — WordNet's is-a tree maps naturally to the domain tree (e.g., "fever" → hyponym of "illness" → Body & Health). Primary and most accurate method.
2. **Roget's category mapping** — The 1,022 categories are mapped to WordPower domains as a supplement for words where WordNet's hierarchy is less clear.
3. **Oxford API definition keywords** — Pattern matching on definitions (e.g., "a medical condition" → Body & Health)
4. **Pre-built override table** — Curated mapping for modern words not in WordNet or Roget's (technology, internet, etc.)
5. **User tagging** — Users can reassign or add domains to any word

#### Word Relationship Engine

Multiple sources are combined to power word connections:

| Feature | Primary source | Supplementary source |
|---|---|---|
| **Synonyms** | WordNet synsets (precise, curated) | Roget's clusters (broader groupings) |
| **Antonyms** | WordNet antonym links | Roget's adjacent opposite entries |
| **Related words / word discovery** | WordNet (hypernyms, hyponyms, meronyms) | Roget's thematic clusters |
| **Quiz distractors** | Roget's same-category words (close but wrong) | WordNet sibling synsets |
| **Word families** | WordNet derivational links | — |
| **Domain auto-tagging** | WordNet is-a hierarchy | Roget's category mapping |

**Processing pipeline (one-time, at build):**

```
Open English WordNet 2025 (CC BY 4.0)
  → Parse synsets, relationships, hierarchy
  → Map hypernym chains to WordPower domains
  → Extract synonym/antonym/related word lists

Roget's 1911 (public domain)
  → Parse 1,022 entries
  → Filter archaic words (cross-reference with Wordfreq)
  → Map categories to WordPower domains
  → Extract thematic clusters for quiz distractors

CEFR-J + Wordfreq
  → Build word → CEFR level lookup table
  → Build frequency rank table

→ Merge all into unified dataset
→ Ship as static asset in app + Firestore /dictionary-meta/ collection
```

#### User Experience

| Path | Example |
|---|---|
| **Browse by domain** | "I want medical vocabulary" → Body & Health → words sorted A1→C2 |
| **Browse by level** | "I'm B1, what should I learn?" → all B1 words across all domains |
| **Browse by root** | "Show me the 'port' family" → transport, export, import, portable, support... |
| **Combine axes** | "B1 Business vocabulary" → Work & Business × B1 |
| **Root discovery** | User learns "transport" → app suggests: "You know the root *port-* (to carry). Explore 9 more words from this family?" |
| **Custom lists** | User creates "IELTS Prep" list → adds words from any domain/level/family |
| **Auto-tagged** | User looks up "prognosis" → auto-tags: Body & Health, C1, root: *gnos-* (to know) |

### 2.7 User Accounts & Cloud Sync

- User authentication (email/password, Google Sign-In, Apple Sign-In)
- Cloud database (Firebase Firestore or Supabase)
- Real-time sync across devices
- Offline support with local cache — syncs when back online

## 3. Target User

English language learners who want a personalized vocabulary tool — not a fixed curriculum. Users who prefer to collect words they encounter in real life (reading, conversations, exams) and actively practice them.

## 4. Language Scope

- **Target language:** English
- **Interface/translations:** Initially English UI; native-language translation field available per word for personal reference
- Future: expandable to other target languages if demand exists

## 5. Technical Stack

| Layer | Technology |
|---|---|
| **Framework** | Flutter (Dart) |
| **State Management** | TBD (Riverpod, Bloc, or Provider) |
| **Local Storage** | Hive, Isar, or SQLite (drift) for offline cache |
| **Backend / Auth** | Firebase (Auth + Firestore + Cloud Functions) |
| **Dictionary API** | Oxford Dictionaries API (API Lite plan) with aggressive server-side caching |
| **Word Intelligence** | Open English WordNet 2025 (synonyms, hierarchy, domains) + Roget's 1911 (thematic clusters, quiz distractors) |
| **CEFR Leveling** | CEFR-J Dataset + Wordfreq (frequency-to-level mapping) |
| **Reference Material** | HTOED, David Crystal's *Words in Time and Place*, English Vocabulary Profile, Oxford Learner's Dictionaries — studied for taxonomy design and leveling methodology |
| **TTS** | Platform-native TTS + dictionary audio files |
| **CI/CD** | GitHub Actions, Fastlane |

## 6. Key Screens

1. **Home / Dashboard** — Today's review count, streak, progress stats, CEFR level progress
2. **Explore Domains** — Browse the semantic domain tree; tap a domain to see its words by level
3. **Explore Roots** — Browse word root families by origin (Germanic, Latin, Greek); tap a root to see all derived words
4. **Word List** — Browse, search, filter all saved words (by domain, level, root family, status, or list)
4. **Add Word** — Manual entry form + dictionary lookup toggle (auto-tags domain + level)
5. **Word Detail** — Full word card with all info, domain badge, CEFR level, edit capability
6. **Quiz Session** — Active quiz with the selected quiz type (can filter by domain/level)
7. **Review Queue** — SRS-driven daily review session (mixed quiz types)
8. **Import** — CSV/Excel upload and field mapping
9. **Profile / Settings** — Account, sync status, quiz preferences, target CEFR level, notifications

## 7. Data Model (High-Level)

```
User
  ├── id, email, displayName, createdAt
  │
  ├── WordLists[]
  │     ├── id, name, description, createdAt
  │     └── wordIds[]
  │
  └── UserWords[] (per-user learning state)
        ├── id, wordId (→ /dictionary/{word})
        ├── personalNotes, nativeTranslation
        ├── tags[]
        └── SRS Fields
              ├── easeFactor, interval, repetitions
              ├── nextReviewDate, lastReviewDate
              └── status (new | learning | review | mastered)

Shared Dictionary Cache (/dictionary/{word})
  ├── word, definitions[], partOfSpeech
  ├── exampleSentences[], pronunciation (IPA), audioUrl
  ├── synonyms[], antonyms[]
  ├── domain (e.g., "body-health", "work-business")
  ├── domainPath (e.g., "The Physical World > Body & Health")
  ├── cefrLevel (A1 | A2 | B1 | B2 | C1 | C2)
  ├── frequencyRank (from COCA or similar corpus)
  ├── rogetCategory (e.g., 769)
  ├── relatedWords[] (from Roget's cluster, filtered for modern usage)
  ├── Root Family Fields
  │     ├── rootId (e.g., "port")
  │     ├── rootMeaning (e.g., "to carry")
  │     ├── rootOrigin (germanic | latin | greek)
  │     ├── prefixes[] (e.g., ["trans-"])
  │     ├── suffixes[] (e.g., ["-ation"])
  │     └── familyWords[] (e.g., ["export", "import", "portable", ...])
  ├── source: "oxford"
  └── fetchedAt: Timestamp

Root Families (/roots/{rootId})
  ├── root (e.g., "port")
  ├── meaning (e.g., "to carry")
  ├── origin (germanic | latin | greek)
  ├── words[] (all words derived from this root)
  ├── commonPrefixes[] (prefixes that combine with this root)
  ├── commonSuffixes[] (suffixes that combine with this root)
  └── exceptions[] (false friends / traps to highlight)
```

## 8. Monetization

- **Model:** 7-day free trial → paid subscription
- **Pricing:** $4.99/month or $29.99/year
- **Free trial gives full access** — users experience Oxford-quality data before deciding
- **Break-even:** ~19 paying users at $4.99/mo (covers ~$78/mo infrastructure)
- **App Store / Play Store cut:** 15% (Apple Small Business Program, Google reduced rate under $1M)

### Monthly Cost Baseline (500 active users)

| Expense | Cost |
|---|---|
| Oxford API Lite | ~$63 (£50) |
| Apple Developer Program | $8.25 |
| Google Play (amortized) | ~$2 |
| Firebase (Auth + Firestore) | $0–5 |
| **Total** | **~$73–78** |

### Dictionary Caching Architecture

A shared, server-side cache ensures each English word is fetched from Oxford **exactly once**, regardless of how many users look it up.

```
┌──────────┐       ┌──────────────────┐       ┌─────────────────────┐
│  Flutter  │──────▶│  Cloud Function   │──────▶│  Firestore          │
│   App     │◀──────│  (lookupWord)     │       │  /dictionary/{word} │
└──────────┘       └────────┬─────────┘       └─────────────────────┘
                            │                          │
                            │  CACHE MISS only         │ CACHE HIT
                            ▼                          │ (most calls)
                   ┌──────────────────┐                │
                   │  Oxford API      │                │
                   │  (external call) │                │
                   └──────────────────┘                │
                            │                          │
                            └──── save to Firestore ───┘
```

**Flow:**

1. User types a word in the app
2. App calls a Firebase Cloud Function (`lookupWord`)
3. Cloud Function checks Firestore `/dictionary/{word}`
   - **HIT** → return cached data immediately (no Oxford API call)
   - **MISS** → call Oxford API → save response to `/dictionary/{word}` → return to user
4. All future lookups for that word by any user are served from Firestore

**Firestore `/dictionary/{word}` document:**

```
{
  word: "ambiguous",
  definitions: [...],
  partOfSpeech: "adjective",
  phonetic: "/amˈbɪɡjʊəs/",
  audioUrl: "https://...",
  exampleSentences: [...],
  synonyms: [...],
  antonyms: [...],
  domain: "communication",
  domainPath: "The Mind > Communication",
  cefrLevel: "B2",
  frequencyRank: 4521,
  rogetCategory: 520,
  relatedWords: ["vague", "unclear", "equivocal", "enigmatic", "cryptic"],
  source: "oxford",
  fetchedAt: Timestamp
}
```

**Why this matters:**

- 500 users looking up "ambiguous" = **1 API call**, not 500
- English has ~170,000 words in common use; after a few months the cache covers nearly every word users will ever search
- Oxford API costs stay flat at the base plan even as user count grows to thousands
- The Oxford API key never touches the client — it stays secure in Cloud Functions

## 9. Success Metrics

- Daily active users returning for review sessions
- Average words mastered per user per month
- Review completion rate (% of due words actually reviewed)
- Retention rate (7-day, 30-day)

## 10. Risks

| Risk | Mitigation |
|---|---|
| Oxford API rate limits or downtime | Aggressive Firestore caching (1 call per word ever); manual entry as fallback |
| Users abandoning due to lack of motivation | Streaks, progress stats, achievement badges |
| Complex SRS logic introducing bugs | Unit test the scheduling algorithm thoroughly in isolation |
| Cloud sync conflicts | Use Firestore's real-time sync with conflict resolution; last-write-wins for simple fields |

## 11. Milestones (Rough Phases)

| Phase | Scope |
|---|---|
| **Phase 1 — Foundation** | Flutter project setup, auth, cloud DB, word CRUD (manual entry), basic word list UI |
| **Phase 2 — Dictionary** | Dictionary API integration, pronunciation/audio, auto-fill word details |
| **Phase 3 — Quiz Engine** | Flashcards + multiple choice, basic SRS scheduling, review queue |
| **Phase 4 — Advanced Quizzes** | Spelling, listening, matching, fill-in-the-blank |
| **Phase 5 — Import & Polish** | CSV/Excel import, dashboard stats, streaks, notifications |
| **Phase 6 — Launch** | App Store / Play Store submission, beta testing, polish |
