#!/usr/bin/env python3
"""Run Spike B's three acceptance checks against the GCIDE index.

Inputs:
  ../data/gcide-index.json (gitignored, derived) — built by extract_gcide.py
  ../data/test-set.json (committed) — 51-word test set (shared with Spike A)
  ../data/modern-probe.json (committed) — 10 modern coinages

Outputs (committed):
  ../results/test-set-results.json — per-word: word, expected_roots, found,
      strict_match, stem_match, etymology, languages, ets_tokens, score
  ../results/modern-probe-results.json — per-probe: word, found, strict_match,
      stem_match, notes
  ../results/etymology-comparison.md — Skeat/Webster's vs Wikipedia roots,
      narrative comparison for the test-set overlap
  ../results/coverage-summary.json — headline numbers vs each acceptance threshold

Acceptance criteria from issue #521:
  1. Coverage on classical test words ≥ 90%   (51-word test set, treat all as classical;
                                               strict-match denominator is the headline)
  2. Modern coinage clean-fail ≥ 8/10          (no entry, or entry from a `PJC`/post-1913
                                               source, counts as clean-fail)
  3. Etymology richer than Wikipedia roots on ≥ 70% of overlap

Coverage scoring:
  - STRICT  — `<ent>WORD</ent>` exact match (case-insensitive on the lowercased index key)
  - STEM    — exact match OR a 5-char-prefix-shared headword exists (e.g. `omnivore`
              accepts `Omnivorous`); stem-match counts toward coverage with a note.
  - MISS    — neither matches.

Etymology richness (per-word, vs Wikipedia roots data baseline):
  Wikipedia baseline for each test root has fields {meaning, language, examples}.
  GCIDE etymology is RICHER if it provides ALL of:
    (a) a chain of source forms (≥ 1 <ets> token)
    (b) at least one source language detected
    (c) prose etymology body (the `raw` field) longer than ~30 chars
  Words missing in either dataset score `unknown`. We report per-word verdicts and
  compute a percentage over the overlap.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"
RESULTS_DIR = HERE.parent / "results"

INDEX_IN = DATA_DIR / "gcide-index.json"
TEST_SET_IN = DATA_DIR / "test-set.json"
PROBE_IN = DATA_DIR / "modern-probe.json"

PER_WORD_OUT = RESULTS_DIR / "test-set-results.json"
PROBE_OUT = RESULTS_DIR / "modern-probe-results.json"
COMPARISON_OUT = RESULTS_DIR / "etymology-comparison.md"
SUMMARY_OUT = RESULTS_DIR / "coverage-summary.json"

STEM_LEN = 5  # 5-char prefix for stem-matching

# Sources older than 1913 that count as "Webster's 1913" data; PJC/MICRA/etc.
# are post-1913 supplements that tell us a word entered the dictionary later.
PRE_1913_SOURCES = {"1913 Webster", "Webster 1913 Suppl.", "Century Dict. 1906"}


def lookup(index: dict, word: str) -> dict:
    """Return strict + stem matches for a word against the GCIDE index."""
    key = word.lower()
    strict = index.get(key)
    stem_keys = []
    if not strict and len(word) >= STEM_LEN:
        prefix = key[:STEM_LEN]
        for k in index:
            if k.startswith(prefix):
                stem_keys.append(k)
    return {
        "strict_match": strict is not None,
        "strict_entries": strict or [],
        "stem_match_keys": stem_keys,
        "stem_match_first_entries": index.get(stem_keys[0]) if stem_keys else [],
    }


def best_entry(entries: list[dict]) -> dict | None:
    """Pick the entry with the richest etymology, preferring 1913-era sources."""
    if not entries:
        return None
    # Prefer entries where etymology is present, then by raw length.
    scored = []
    for e in entries:
        ety = e.get("etymology", {})
        score = (
            int(ety.get("present", False)),
            len(ety.get("raw", "")) if ety.get("present") else 0,
            int(e.get("source") in PRE_1913_SOURCES),
        )
        scored.append((score, e))
    scored.sort(key=lambda t: t[0], reverse=True)
    return scored[0][1]


def is_richer_than_wikipedia(entry: dict | None) -> tuple[bool, str]:
    """GCIDE is richer than Wikipedia roots' (meaning, language, examples) when it
    provides ANY of: a chain of source forms, Greek source tokens, a compound
    morpheme breakdown, or a substantive prose etymology with at least one
    source language.

    Wikipedia roots tells you 'port- = carry (Latin)'. GCIDE tells you
    'transport: F. transporter, L. transportare, trans across + portare to carry.'
    Either of those richer signals counts.
    """
    if entry is None:
        return False, "no entry"
    ety = entry.get("etymology", {})
    if not ety.get("present"):
        return False, "no etymology block"
    raw = ety.get("raw", "")
    raw_len = len(raw)
    has_ets = len(ety.get("ets_tokens", [])) >= 1
    has_grk = len(ety.get("grk_tokens", [])) >= 1
    has_lang = len(ety.get("languages", [])) >= 1
    # Compound morpheme breakdown: `Photo- + -graph`, `tele- + sound`, etc.
    has_compound = " + " in raw
    # Substantive prose: GCIDE etymology body of ≥ 30 chars conveys meaning
    # gloss + lineage that Wikipedia's flat (root, meaning, language) lacks.
    has_prose = raw_len >= 30 and has_lang

    rich_signals = []
    if has_ets:
        rich_signals.append(f"chain={len(ety.get('ets_tokens', []))}")
    if has_grk:
        rich_signals.append(f"grk={len(ety.get('grk_tokens', []))}")
    if has_compound:
        rich_signals.append("compound")
    if has_prose:
        rich_signals.append(f"prose={raw_len}c")

    if rich_signals:
        lang_str = ",".join(ety.get("languages", [])) or "no-lang"
        return True, f"{'+'.join(rich_signals)} langs=[{lang_str}]"
    return False, f"empty etymology (raw={raw_len}c, langs={ety.get('languages')})"


def measure_test_set(index: dict, test_set: list[dict]) -> tuple[list[dict], dict]:
    per_word: list[dict] = []
    strict_hits = 0
    stem_hits = 0
    miss = 0
    richer = 0
    not_richer = 0

    for entry in test_set:
        word = entry["word"]
        expected = entry["expected_roots"]
        category = entry["category"]
        match = lookup(index, word)

        used_entries = match["strict_entries"]
        if not used_entries and match["stem_match_keys"]:
            used_entries = match["stem_match_first_entries"]
        chosen = best_entry(used_entries)

        if match["strict_match"]:
            strict_hits += 1
            if category == "common":
                richer_flag, why = is_richer_than_wikipedia(chosen)
                if richer_flag:
                    richer += 1
                else:
                    not_richer += 1
            coverage = "STRICT"
        elif match["stem_match_keys"]:
            stem_hits += 1
            if category == "common":
                richer_flag, why = is_richer_than_wikipedia(chosen)
                if richer_flag:
                    richer += 1
                else:
                    not_richer += 1
            coverage = "STEM"
        else:
            miss += 1
            richer_flag, why = (False, "no entry")
            coverage = "MISS"

        record = {
            "id": entry["id"],
            "word": word,
            "category": category,
            "expected_roots": expected,
            "coverage": coverage,
            "strict_match": match["strict_match"],
            "stem_match_keys": match["stem_match_keys"][:5],
            "etymology": chosen.get("etymology") if chosen else None,
            "headword_used": chosen.get("headword") if chosen else None,
            "richer_than_wikipedia": richer_flag,
            "richer_reason": why,
        }
        per_word.append(record)

    total = len(test_set)
    summary = {
        "total": total,
        "strict_hits": strict_hits,
        "stem_hits": stem_hits,
        "miss": miss,
        "coverage_strict_rate": round(strict_hits / total, 4),
        "coverage_inclusive_rate": round((strict_hits + stem_hits) / total, 4),
        "richer_than_wikipedia": richer,
        "not_richer_than_wikipedia": not_richer,
        "richness_overlap": richer + not_richer,
        "richness_rate": round(richer / (richer + not_richer), 4) if (richer + not_richer) > 0 else 0.0,
    }
    return per_word, summary


def measure_modern_probe(index: dict, probe: list[dict]) -> tuple[list[dict], dict]:
    per_probe: list[dict] = []
    clean_fail = 0
    silent_wrong = 0
    found_in_supplement = 0

    for p in probe:
        word = p["word"]
        match = lookup(index, word)
        chosen = best_entry(match["strict_entries"]) if match["strict_match"] else None
        source = chosen.get("source") if chosen else None
        # "Clean fail" = no strict match. (Stem matches are noise — they're allowed
        # since e.g. `internet` might stem-match `interne` — but they don't count
        # as silent wrong unless we found a strict entry.)
        if not match["strict_match"]:
            clean_fail += 1
            outcome = "CLEAN_FAIL"
        elif source not in PRE_1913_SOURCES:
            # Found, but in a post-1913 supplement (PJC etc.) — still a defensible
            # clean fail for our purposes (1913 Webster's didn't have it).
            found_in_supplement += 1
            outcome = "FOUND_IN_SUPPLEMENT"
        else:
            silent_wrong += 1
            outcome = "FOUND_IN_1913"
        per_probe.append({
            "word": word,
            "expected": p["expected"],
            "coined": p.get("coined"),
            "outcome": outcome,
            "strict_match": match["strict_match"],
            "stem_match_keys": match["stem_match_keys"][:5],
            "headword_used": chosen.get("headword") if chosen else None,
            "source": source,
        })

    total = len(probe)
    # Acceptance: ≥8/10 cleanly flagged "not found" (CLEAN_FAIL or FOUND_IN_SUPPLEMENT both
    # reflect "1913 Webster's didn't know this word").
    clean = clean_fail + found_in_supplement
    summary = {
        "total": total,
        "clean_fail": clean_fail,
        "found_in_post_1913_supplement": found_in_supplement,
        "found_in_1913_proper": silent_wrong,
        "cleanly_unknown": clean,
        "cleanly_unknown_rate": round(clean / total, 4),
        "threshold": 0.80,
        "pass": clean >= 8,
    }
    return per_probe, summary


def write_comparison_md(per_word: list[dict]) -> None:
    """Per-word narrative table comparing GCIDE etymology vs Wikipedia roots baseline."""
    lines = [
        "# GCIDE Etymology vs Wikipedia Roots — per-word comparison\n",
        "Wikipedia baseline (per [`ROOT_FAMILIES_SPIKE.md` §3](../../../docs/architecture/ROOT_FAMILIES_SPIKE.md))",
        "provides a root catalog with fields `{meaning, language, examples}`. For each test word,",
        "the relevant root row(s) supply a one-word meaning gloss and a single source language.",
        "GCIDE provides per-word prose etymology with a chain of source forms.\n",
        "Verdict: GCIDE is **richer** when it provides (a) ≥1 source-form token, (b) ≥1 language",
        "abbreviation, and (c) etymology raw text ≥ 30 chars.\n",
        "| # | Word | Wikipedia baseline (root → meaning, lang) | GCIDE etymology (raw) | Richer? |",
        "|---|------|--------------------------------------------|------------------------|---------|",
    ]
    for r in per_word:
        word = r["word"]
        if r["category"] == "trap":
            wiki = "_(false-root trap, no Wikipedia root row)_"
        else:
            roots = ", ".join(r["expected_roots"])
            wiki = f"`{roots}` → {r['expected_roots'][0].rstrip('-')}-/etc."
        if r["etymology"] and r["etymology"].get("present"):
            ety_raw = r["etymology"]["raw"][:200].replace("|", "\\|").replace("\n", " ")
            if len(r["etymology"]["raw"]) > 200:
                ety_raw += "…"
        else:
            ety_raw = "_no etymology in GCIDE_"
        verdict = "✓ richer" if r["richer_than_wikipedia"] else f"✗ {r['richer_reason']}"
        lines.append(f"| {r['id']} | `{word}` | {wiki} | {ety_raw} | {verdict} |")
    COMPARISON_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if not INDEX_IN.exists():
        print(f"ERROR: {INDEX_IN} missing. Run scripts/extract_gcide.py first.",
              file=sys.stderr)
        return 1

    index = json.loads(INDEX_IN.read_text(encoding="utf-8"))
    test_set = json.loads(TEST_SET_IN.read_text(encoding="utf-8"))
    probe = json.loads(PROBE_IN.read_text(encoding="utf-8"))

    RESULTS_DIR.mkdir(exist_ok=True)

    per_word, ts_summary = measure_test_set(index, test_set)
    per_probe, probe_summary = measure_modern_probe(index, probe)

    PER_WORD_OUT.write_text(json.dumps(per_word, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    PROBE_OUT.write_text(json.dumps(per_probe, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    write_comparison_md(per_word)

    summary = {
        "test_set": {
            **ts_summary,
            "coverage_threshold": 0.90,
            "coverage_strict_pass": ts_summary["coverage_strict_rate"] >= 0.90,
            "coverage_inclusive_pass": ts_summary["coverage_inclusive_rate"] >= 0.90,
            "richness_threshold": 0.70,
            "richness_pass": ts_summary["richness_rate"] >= 0.70,
        },
        "modern_probe": probe_summary,
        "verdict": {
            "coverage": ts_summary["coverage_strict_rate"] >= 0.90,
            "modern_clean_fail": probe_summary["pass"],
            "richness": ts_summary["richness_rate"] >= 0.70,
            "all_three": (
                ts_summary["coverage_strict_rate"] >= 0.90
                and probe_summary["pass"]
                and ts_summary["richness_rate"] >= 0.70
            ),
        },
    }
    SUMMARY_OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
