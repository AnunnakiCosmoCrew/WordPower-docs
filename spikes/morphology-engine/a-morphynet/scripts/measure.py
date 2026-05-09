#!/usr/bin/env python3
"""Run the 51-word test set through MorphyNet's parent index and score it.

Inputs (committed):
  ../data/test-set.json — 51 entries with expected_roots and category
Inputs (gitignored, derived):
  ../data/morphynet-en-index.json — {target: [{source, morpheme, type, ...}, ...]}
  ../data/eng.derivational.v1.tsv — for bundle-size measurement

Outputs (committed):
  ../results/test-set-results.json — per-word: word, expected_roots, found, chain,
                                     base, score, category, scoring_notes
  ../results/summary.json — hit_rate, accuracy_correct_only, accuracy_weighted,
                            false_positives, breakdown
  ../results/bundle-size.txt — three candidate bundle sizes at gzip -9

Scoring rubric (loose substring, four levels):
  CORRECT   (1.0)  — every expected_root (trailing "-" stripped) appears as
                     substring in any chain node OR any affix
  PARTIAL   (0.5)  — at least one but not all expected_roots match; chain non-empty
  WRONG     (0.0)  — chain produced but no expected_root matches anywhere
  NOT_FOUND        — word absent from MorphyNet; counts against hit rate, NOT
                     against accuracy denominator

Acceptance threshold uses CORRECT-only accuracy. Weighted accuracy
(CORRECT * 1.0 + PARTIAL * 0.5) / hits is reported alongside as informational.

Trap scoring is separate: any non-empty chain on uncle/island/butter is a
false positive (1 of 3 traps failed) — the rubric above does NOT apply.
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"
RESULTS_DIR = HERE.parent / "results"

INDEX_IN = DATA_DIR / "morphynet-en-index.json"
TEST_SET_IN = DATA_DIR / "test-set.json"
RAW_TSV = DATA_DIR / "eng.derivational.v1.tsv"

PER_WORD_OUT = RESULTS_DIR / "test-set-results.json"
SUMMARY_OUT = RESULTS_DIR / "summary.json"
BUNDLE_OUT = RESULTS_DIR / "bundle-size.txt"

MAX_DEPTH = 10


def decompose(word: str, parents: dict) -> dict:
    """Walk the parent chain back to a base word."""
    found = word in parents
    chain: list[dict] = []
    nodes: list[str] = [word]   # all word forms encountered (target + intermediates + base)
    visited = {word}
    current = word
    while current in parents and len(chain) < MAX_DEPTH:
        # First-encountered parent wins (multi-parent count is logged at extract time).
        edge = parents[current][0]
        src = edge["source"]
        if src in visited:
            break  # cycle guard
        chain.append({
            "from": current,
            "to": src,
            "morpheme": edge["morpheme"],
            "type": edge["type"],
        })
        visited.add(src)
        nodes.append(src)
        current = src
    return {
        "found": found,
        "chain": chain,
        "base": current,
        "depth": len(chain),
        "nodes": nodes,
    }


def score_hit(expected_roots: list[str], dec: dict) -> tuple[str, str]:
    """Apply the loose-substring rubric. Returns (label, notes)."""
    if not dec["found"]:
        return "NOT_FOUND", "word absent from MorphyNet"

    if not expected_roots:
        # Should never reach here for traps — they're scored separately.
        return "CORRECT", "no expected roots specified"

    # Build the haystack: every chain node + every morpheme on every edge.
    haystack: list[str] = list(dec["nodes"])
    for edge in dec["chain"]:
        haystack.append(edge["morpheme"])
    haystack_lc = [s.lower() for s in haystack]

    matched: list[str] = []
    missed: list[str] = []
    for root in expected_roots:
        bare = root.rstrip("-").lower()
        if any(bare in h for h in haystack_lc):
            matched.append(root)
        else:
            missed.append(root)

    if not missed:
        return "CORRECT", f"all {len(matched)} expected roots matched in chain"
    if matched:
        return "PARTIAL", f"matched {matched}; missed {missed}"
    return "WRONG", f"chain produced but none of {expected_roots} matched"


def trap_outcome(dec: dict) -> tuple[str, str]:
    """Traps fail if MorphyNet produces ANY decomposition."""
    if dec["found"]:
        return "FAIL", f"MorphyNet decomposed trap: chain={dec['chain']}"
    return "PASS", "no decomposition (clean refusal)"


def measure_bundles() -> list[dict]:
    """Measure three candidate runtime bundle formats at gzip -9."""
    if not RAW_TSV.exists():
        return [{"format": "raw 5-col TSV", "error": "raw TSV missing"}]

    raw_bytes = RAW_TSV.read_bytes()
    bundles: list[dict] = []

    bundles.append({
        "format": "raw 6-col TSV (as-shipped)",
        "raw_bytes": len(raw_bytes),
        "gz_bytes": len(gzip.compress(raw_bytes, compresslevel=9)),
        "notes": "as-downloaded from MorphyNet; includes both POS columns",
    })

    # Slim: drop POS columns, keep target/source/morpheme/type.
    slim_lines: list[bytes] = []
    for line in raw_bytes.decode("utf-8").splitlines():
        cols = line.split("\t")
        if len(cols) != 6:
            continue
        source, target, _src_pos, _tgt_pos, morpheme, mtype = cols
        slim_lines.append(f"{target}\t{source}\t{morpheme}\t{mtype}".encode("utf-8"))
    slim_blob = b"\n".join(slim_lines)
    bundles.append({
        "format": "slim 4-col TSV (target source morpheme type)",
        "raw_bytes": len(slim_blob),
        "gz_bytes": len(gzip.compress(slim_blob, compresslevel=9)),
        "notes": "drops POS columns; runtime decomposition needs only target -> (source, morpheme, type)",
    })

    # JSON map: target -> first parent edge (drop multi-parent rows).
    seen: dict[str, dict] = {}
    for line in raw_bytes.decode("utf-8").splitlines():
        cols = line.split("\t")
        if len(cols) != 6:
            continue
        source, target, _src_pos, _tgt_pos, morpheme, mtype = cols
        if target not in seen:
            seen[target] = {"s": source, "m": morpheme, "t": mtype}
    json_blob = json.dumps(seen, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    bundles.append({
        "format": "JSON map (target -> {s,m,t})",
        "raw_bytes": len(json_blob),
        "gz_bytes": len(gzip.compress(json_blob, compresslevel=9)),
        "notes": "first-parent only; runtime-friendly; loses multi-parent edges",
    })

    return bundles


def write_bundle_report(bundles: list[dict]) -> None:
    lines = ["MorphyNet English derivational — candidate bundle sizes (gzip -9)\n"]
    lines.append("\n")
    lines.append(f"{'format':50s} {'raw KB':>10s} {'gz KB':>10s}\n")
    lines.append("-" * 72 + "\n")
    for b in bundles:
        if "error" in b:
            lines.append(f"{b['format']:50s} ERROR: {b['error']}\n")
            continue
        lines.append(
            f"{b['format']:50s} {b['raw_bytes']/1024:>10.1f} {b['gz_bytes']/1024:>10.1f}\n"
        )
    lines.append("\n")
    lines.append("Notes:\n")
    for b in bundles:
        if "notes" in b:
            lines.append(f"  - {b['format']}: {b['notes']}\n")
    lines.append("\n")
    lines.append(
        "Acceptance threshold: ≤ 200 KB gzipped. Compare against the smallest viable "
        "runtime bundle (slim TSV or JSON map). The raw size is the floor from MorphyNet "
        "alone; shipping the §6 record schema (meaning, language, etymology) inflates it.\n"
    )
    BUNDLE_OUT.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    if not INDEX_IN.exists():
        print(f"ERROR: {INDEX_IN} missing. Run scripts/extract.py first.", file=sys.stderr)
        return 1
    if not TEST_SET_IN.exists():
        print(f"ERROR: {TEST_SET_IN} missing.", file=sys.stderr)
        return 1

    parents = json.loads(INDEX_IN.read_text(encoding="utf-8"))
    test_set = json.loads(TEST_SET_IN.read_text(encoding="utf-8"))

    RESULTS_DIR.mkdir(exist_ok=True)

    per_word: list[dict] = []
    hits = 0
    score_counts = {"CORRECT": 0, "PARTIAL": 0, "WRONG": 0, "NOT_FOUND": 0}
    trap_failures = 0
    trap_total = 0

    for entry in test_set:
        word = entry["word"]
        category = entry["category"]
        expected_roots = entry["expected_roots"]
        dec = decompose(word, parents)

        record: dict = {
            "id": entry["id"],
            "word": word,
            "category": category,
            "expected_roots": expected_roots,
            "found": dec["found"],
            "chain": dec["chain"],
            "base": dec["base"],
            "depth": dec["depth"],
        }

        if category == "trap":
            trap_total += 1
            outcome, notes = trap_outcome(dec)
            record["trap_outcome"] = outcome
            record["scoring_notes"] = notes
            if outcome == "FAIL":
                trap_failures += 1
        else:
            label, notes = score_hit(expected_roots, dec)
            record["score"] = label
            record["scoring_notes"] = notes
            score_counts[label] += 1
            if dec["found"]:
                hits += 1

        per_word.append(record)

    common_total = sum(1 for e in test_set if e["category"] == "common")
    not_found = score_counts["NOT_FOUND"]
    correct = score_counts["CORRECT"]
    partial = score_counts["PARTIAL"]
    wrong = score_counts["WRONG"]

    hit_rate = hits / common_total if common_total else 0.0
    accuracy_correct_only = correct / hits if hits else 0.0
    accuracy_weighted = (correct + 0.5 * partial) / hits if hits else 0.0

    bundles = measure_bundles()
    write_bundle_report(bundles)
    smallest_runtime_gz = None
    for b in bundles:
        if b.get("format", "").startswith("raw"):
            continue
        if "gz_bytes" not in b:
            continue
        if smallest_runtime_gz is None or b["gz_bytes"] < smallest_runtime_gz["gz_bytes"]:
            smallest_runtime_gz = b

    summary = {
        "test_set_size": len(test_set),
        "common_words": common_total,
        "trap_words": trap_total,
        "hit_rate": {
            "hits": hits,
            "common_total": common_total,
            "rate": round(hit_rate, 4),
            "threshold": 0.80,
            "pass": hit_rate >= 0.80,
        },
        "accuracy_correct_only": {
            "correct": correct,
            "hits": hits,
            "rate": round(accuracy_correct_only, 4),
            "threshold": 0.90,
            "pass": accuracy_correct_only >= 0.90,
        },
        "accuracy_weighted_informational": {
            "weighted_score": round(correct + 0.5 * partial, 2),
            "hits": hits,
            "rate": round(accuracy_weighted, 4),
        },
        "false_positives_on_traps": {
            "failures": trap_failures,
            "total": trap_total,
            "threshold": 0,
            "pass": trap_failures == 0,
        },
        "score_breakdown_common": score_counts,
        "bundle_size": {
            "smallest_runtime_format": smallest_runtime_gz["format"] if smallest_runtime_gz else None,
            "smallest_runtime_gz_bytes": smallest_runtime_gz["gz_bytes"] if smallest_runtime_gz else None,
            "smallest_runtime_gz_kb": round(smallest_runtime_gz["gz_bytes"] / 1024, 2) if smallest_runtime_gz else None,
            "threshold_kb": 200,
            "pass": (smallest_runtime_gz is not None
                     and smallest_runtime_gz["gz_bytes"] <= 200 * 1024),
            "all_candidates": bundles,
        },
    }

    PER_WORD_OUT.write_text(
        json.dumps(per_word, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    SUMMARY_OUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
