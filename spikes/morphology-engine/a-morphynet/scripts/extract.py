#!/usr/bin/env python3
"""Build a parent-lookup index from MorphyNet's English derivational TSV.

Input  (gitignored): ../data/eng.derivational.v1.tsv
                     6 columns: source, target, source_pos, target_pos, morpheme, type
                     where `type` is "prefix" or "suffix".

Outputs:
  ../data/morphynet-en-index.json (gitignored, derived)
      JSON object {target: [{"source", "morpheme", "type",
                             "source_pos", "target_pos"}, ...]}
      Multi-parent: list ordered by appearance in the TSV.
  ../data/extract-stats.txt (committed)
      Summary counts.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"
SRC = DATA_DIR / "eng.derivational.v1.tsv"
INDEX_OUT = DATA_DIR / "morphynet-en-index.json"
STATS_OUT = DATA_DIR / "extract-stats.txt"


def main() -> int:
    if not SRC.exists():
        print(f"ERROR: {SRC} missing. Run scripts/download.sh first.", file=sys.stderr)
        return 1

    parents: dict[str, list[dict]] = {}
    type_counts: Counter[str] = Counter()
    rows = 0
    multi_parent = 0

    with SRC.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if len(row) != 6:
                continue
            source, target, src_pos, tgt_pos, morpheme, mtype = row
            entry = {
                "source": source,
                "morpheme": morpheme,
                "type": mtype,
                "source_pos": src_pos,
                "target_pos": tgt_pos,
            }
            if target in parents:
                multi_parent += 1
            parents.setdefault(target, []).append(entry)
            type_counts[mtype] += 1
            rows += 1

    INDEX_OUT.write_text(
        json.dumps(parents, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    distinct_targets = len(parents)
    distinct_sources = len({e["source"] for entries in parents.values() for e in entries})
    type_str = ", ".join(f"{k}={v}" for k, v in sorted(type_counts.items()))

    stats = (
        f"MorphyNet English derivational — extraction stats\n"
        f"source file: {SRC.name}\n"
        f"rows parsed: {rows}\n"
        f"distinct targets: {distinct_targets}\n"
        f"distinct sources: {distinct_sources}\n"
        f"multi-parent edges (target appearing >1 time): {multi_parent}\n"
        f"affix-type distribution: {type_str}\n"
    )
    STATS_OUT.write_text(stats, encoding="utf-8")
    print(stats, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
