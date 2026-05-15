#!/usr/bin/env python3
"""Heuristic keyword-based domain classifier — Python port of the JVM
DomainClassifier (WordPower-app backend), extended to the 15 PROJECT.md
top-level domains.

Same scoring rule as the Java version:
  - Lowercase, split on non-word boundaries.
  - For each domain, count how many of its keywords appear as full tokens.
  - Return the domain with the highest count. Ties broken by insertion order
    (narrower / higher-signal domains first).
  - If no keywords match, return None.

Used as the "heuristic fallback" comparator in measure_accuracy.py. Domain ids
match data/domain-centroids.json so accuracy can be compared apples-to-apples
with the embedding classifier.
"""

import json
import re
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# Ordered so narrower / higher-signal domains come first (tie-break).
DOMAIN_KEYWORDS: "dict[str, set[str]]" = {
    "body_and_health": {
        "disease", "patient", "diagnosis", "symptom", "treatment", "surgery",
        "hospital", "doctor", "medical", "medicine", "drug", "therapy",
        "infection", "virus", "vaccine", "anatomy", "clinical", "physician",
        "tissue", "fever", "inflammation", "biopsy", "ailment", "prescription",
        "body", "blood", "swelling", "redness", "illness", "health",
    },
    "law_and_politics": {
        "court", "judge", "lawyer", "legal", "law", "trial", "evidence",
        "verdict", "statute", "contract", "jurisdiction", "plaintiff",
        "defendant", "sentence", "appeal", "judicial", "litigation",
        "parliament", "election", "government", "policy", "minister",
        "subpoena", "writ", "filibuster", "legislation",
    },
    "science_and_technology": {
        "computer", "software", "code", "algorithm", "program", "internet",
        "digital", "data", "machine", "electronic", "network", "device",
        "application", "interface", "processor", "server", "database",
        "encryption", "binary", "experiment", "theory", "molecule", "atom",
        "cell", "organism", "gene", "energy", "hypothesis", "research",
        "laboratory", "physics", "chemistry", "biology", "particle",
        "quantum", "scientific", "photosynthesis", "chemical", "compound",
    },
    "food_and_drink": {
        "cooking", "recipe", "ingredient", "meal", "dish", "restaurant",
        "chef", "cuisine", "flavor", "flavour", "culinary", "baking",
        "roasting", "spice", "herb", "wine", "marinade", "vintage",
        "soaked", "sauce", "vinegar", "oil",
    },
    "work_and_business": {
        "market", "economy", "finance", "investment", "profit", "revenue",
        "company", "corporation", "trade", "commerce", "stock", "shareholder",
        "financial", "accounting", "banking", "economic", "merger",
        "acquisition", "salary", "employee", "employer", "freelance",
        "leverage", "capital", "invoice", "commute", "work", "job",
    },
    "travel_and_places": {
        "journey", "destination", "tourist", "vacation", "travel", "hotel",
        "flight", "passport", "sightseeing", "itinerary", "voyage",
        "expedition", "tourism", "country", "city", "region", "place",
        "area", "location", "vicinity", "expatriate", "native",
    },
    "nature": {
        "animal", "plant", "forest", "ocean", "mountain", "river", "weather",
        "climate", "ecology", "wildlife", "ecosystem", "habitat", "species",
        "biodiversity", "tidal", "rainfall", "estuary", "sea", "prey",
        "drought", "environment", "organisms", "natural",
    },
    "emotions_and_feelings": {
        "feeling", "mood", "happiness", "sadness", "anger", "fear", "love",
        "joy", "emotion", "sentiment", "affection", "anxiety", "grief",
        "compassion", "melancholy", "elation", "exhilaration", "longing",
        "nostalgia", "sorrow", "sad", "happy",
    },
    "communication": {
        "speak", "speech", "writing", "letter", "language", "media", "news",
        "journalism", "broadcast", "transmit", "message", "telephone",
        "conversation", "debate", "rhetoric", "memorandum", "memo",
        "persuasive", "radio", "television",
    },
    "thinking_and_learning": {
        "reasoning", "memory", "knowledge", "intelligence", "study",
        "education", "school", "university", "college", "course",
        "curriculum", "hypothesis", "subject", "cognition", "intuition",
        "investigation", "philosophy", "psychology", "learn", "thinking",
        "explanation",
    },
    "character_and_personality": {
        "trait", "temperament", "virtue", "vice", "honesty", "courage",
        "ambition", "kindness", "honest", "integrity", "stubborn",
        "ambitious", "loyal", "moral", "principles", "character",
        "personality", "determined", "unyielding",
    },
    "culture_and_arts": {
        "painting", "sculpture", "music", "dance", "literature", "poetry",
        "novel", "novella", "theatre", "theater", "cinema", "artist",
        "gallery", "composer", "symphony", "opera", "ballet", "renaissance",
        "baroque", "exhibition", "art", "fresco", "plaster", "watercolor",
    },
    "relationships": {
        "family", "friend", "marriage", "marry", "married", "engaged",
        "betrothed", "romance", "parent", "child", "sibling", "spouse",
        "couple", "estranged", "mentor", "advisor", "social", "relationship",
        "trusted",
    },
    "home_and_living": {
        "house", "home", "apartment", "furniture", "cupboard", "cabinet",
        "wardrobe", "kitchen", "bedroom", "living", "household", "domestic",
        "rent", "mortgage", "thermostat", "appliance", "lease", "tenant",
        "property", "clothes", "hung",
    },
    "daily_life": {
        "shopping", "errand", "laundry", "weekend", "saturday", "sunday",
        "leisure", "hobby", "holiday", "routine", "wash", "linen",
        "deliver", "everyday",
    },
}

WORD_RE = re.compile(r"[a-z][a-z']*")


def classify(text: str) -> "str | None":
    tokens = set(WORD_RE.findall(text.lower()))
    best_domain, best_hits = None, 0
    for domain, kws in DOMAIN_KEYWORDS.items():
        hits = sum(1 for k in kws if k in tokens)
        if hits > best_hits:
            best_domain, best_hits = domain, hits
    return best_domain


def classify_top_k(text: str, k: int = 3) -> "list[str]":
    tokens = set(WORD_RE.findall(text.lower()))
    scored = [
        (domain, sum(1 for kw in kws if kw in tokens))
        for domain, kws in DOMAIN_KEYWORDS.items()
    ]
    scored.sort(key=lambda x: -x[1])
    # Drop zero-hit domains from top-k; if all zero, return [] (no signal).
    return [d for d, h in scored[:k] if h > 0]


def main() -> None:
    words = json.load(open(DATA / "test-words.json"))["words"]
    correct_top1 = 0
    correct_top3 = 0
    no_signal = 0
    per_word = []
    for w in words:
        text = f"{w['word']} {w['short_def']}"
        top3 = classify_top_k(text, 3)
        top1 = top3[0] if top3 else None
        gold = w["gold"]
        match_top1 = top1 == gold
        match_top3 = gold in top3
        if top1 is None:
            no_signal += 1
        if match_top1:
            correct_top1 += 1
        if match_top3:
            correct_top3 += 1
        per_word.append(
            {
                "word": w["word"],
                "gold": gold,
                "heuristic_top1": top1,
                "heuristic_top3": top3,
                "match_top1": match_top1,
                "match_top3": match_top3,
            }
        )
    n = len(words)
    summary = {
        "n": n,
        "top1_accuracy": round(correct_top1 / n, 3),
        "top3_accuracy": round(correct_top3 / n, 3),
        "no_signal_words": no_signal,
        "per_word": per_word,
    }
    out = ROOT / "results" / "heuristic-results.json"
    json.dump(summary, open(out, "w"), indent=2)
    print(f"Heuristic top-1: {summary['top1_accuracy']:.1%}")
    print(f"Heuristic top-3: {summary['top3_accuracy']:.1%}")
    print(f"No-signal words: {no_signal}/{n}")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
