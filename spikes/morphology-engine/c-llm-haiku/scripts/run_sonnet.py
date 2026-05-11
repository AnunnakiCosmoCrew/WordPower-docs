#!/usr/bin/env python3
"""Run Claude Sonnet 4.6 — same flow as run_haiku.py with a different model.

Cross-validates Haiku 4.5's outputs. Per issue #522 acceptance criterion #2:
≥ 95% agreement between Haiku and Sonnet on clean cases.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import anthropic

from _shared import call_decompose, estimate_cost_per_call, load_system_prompt

MODEL = "claude-sonnet-4-6"
HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
_results_dir = os.environ.get("RESULTS_DIR", "results")
RESULTS = HERE.parent / _results_dir


def run_word(client, model, word, system_prompt) -> dict:
    last_error = None
    for attempt in range(2):
        try:
            decomposition, usage = call_decompose(client, model, word, system_prompt)
            return {
                "word": word,
                "ok": True,
                "decomposition": decomposition,
                "usage": usage,
                "cost_usd": estimate_cost_per_call(usage, model),
            }
        except (anthropic.APIConnectionError, anthropic.APIStatusError) as e:
            last_error = repr(e)
            if attempt == 0:
                time.sleep(2)
                continue
            return {"word": word, "ok": False, "error": last_error}
    return {"word": word, "ok": False, "error": last_error}


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set in environment", file=sys.stderr)
        return 2

    client = anthropic.Anthropic()
    system_prompt = load_system_prompt()
    RESULTS.mkdir(exist_ok=True)

    test_set = json.loads((DATA / "test-set.json").read_text(encoding="utf-8"))
    adversarial = json.loads((DATA / "adversarial-set.json").read_text(encoding="utf-8"))

    print(f"=== {MODEL} ===")
    print(f"system prompt length: ~{len(system_prompt)} chars")

    test_results = []
    for entry in test_set:
        rec = run_word(client, MODEL, entry["word"], system_prompt)
        rec["category"] = entry["category"]
        rec["expected_roots"] = entry["expected_roots"]
        rec["id"] = entry["id"]
        test_results.append(rec)
        cache_read = rec.get("usage", {}).get("cache_read_input_tokens", 0)
        print(
            f"  test  #{entry['id']:2d} {entry['word']:20s} "
            f"{'OK ' if rec['ok'] else 'ERR'} "
            f"cache_read={cache_read:4d}t cost=${rec.get('cost_usd', 0):.5f}"
        )

    adv_results = {}
    for category, items in adversarial.items():
        adv_results[category] = []
        for entry in items:
            rec = run_word(client, MODEL, entry["word"], system_prompt)
            rec["category"] = category
            rec["expected_behavior"] = entry.get("expected_behavior")
            rec["expected_morphemes"] = entry.get("expected_morphemes")
            rec["readings"] = entry.get("readings")
            rec["notes"] = entry.get("notes")
            adv_results[category].append(rec)
            cache_read = rec.get("usage", {}).get("cache_read_input_tokens", 0)
            print(
                f"  adv   {category[:8]:8s} {entry['word']:25s} "
                f"{'OK ' if rec['ok'] else 'ERR'} "
                f"cache_read={cache_read:4d}t cost=${rec.get('cost_usd', 0):.5f}"
            )

    (RESULTS / "sonnet-test-set.json").write_text(
        json.dumps(test_results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (RESULTS / "sonnet-adversarial.json").write_text(
        json.dumps(adv_results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    all_records = list(test_results) + [
        r for cat in adv_results.values() for r in cat
    ]
    total = {
        "model": MODEL,
        "num_calls": len(all_records),
        "successful": sum(1 for r in all_records if r["ok"]),
        "failed": sum(1 for r in all_records if not r["ok"]),
        "total_input_tokens": sum(
            r.get("usage", {}).get("input_tokens", 0) for r in all_records
        ),
        "total_output_tokens": sum(
            r.get("usage", {}).get("output_tokens", 0) for r in all_records
        ),
        "total_cache_creation_tokens": sum(
            r.get("usage", {}).get("cache_creation_input_tokens", 0)
            for r in all_records
        ),
        "total_cache_read_tokens": sum(
            r.get("usage", {}).get("cache_read_input_tokens", 0)
            for r in all_records
        ),
        "total_cost_usd": round(
            sum(r.get("cost_usd", 0) for r in all_records), 6
        ),
    }
    (RESULTS / "sonnet-usage.json").write_text(
        json.dumps(total, indent=2), encoding="utf-8"
    )
    print()
    print(json.dumps(total, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
