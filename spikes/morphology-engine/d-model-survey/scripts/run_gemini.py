#!/usr/bin/env python3
"""Run Gemini 2.5 Flash on the same 81-word set used in Spike C.

Reads:
  - ../../c-llm-haiku/data/test-set.json           (51 words)
  - ../../c-llm-haiku/data/adversarial-set.json    (10 traps + 10 multi-layer + 10 ambiguous)
  - ../../c-llm-haiku/scripts/prompt.md            (system prompt — same as Spike C)

Writes (mirroring Spike C's haiku-* output shape so measure.py can score it):
  - ../results/gemini-test-set.json
  - ../results/gemini-adversarial.json
  - ../results/gemini-usage.json

Requires GEMINI_API_KEY in the environment.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

MODEL = "gemini-2.5-flash"

HERE = Path(__file__).resolve().parent
SPIKE_C = HERE.parent.parent / "c-llm-haiku"
DATA = SPIKE_C / "data"
PROMPT_MD = SPIKE_C / "scripts" / "prompt.md"
RESULTS = HERE.parent / "results"


def load_system_prompt() -> str:
    """Same loader logic as Spike C's _shared.load_system_prompt."""
    text = PROMPT_MD.read_text(encoding="utf-8")
    blocks = re.split(r"^```$", text, flags=re.MULTILINE)
    if len(blocks) < 3:
        raise RuntimeError(
            f"prompt.md structure changed; expected >=3 fenced sections, got {len(blocks)}"
        )
    return blocks[2].strip()


# Tool schema mirroring the Anthropic Spike C schema. Gemini's function-calling
# uses google.genai's `types.FunctionDeclaration` with a JSON-Schema-like
# parameter spec. Same fields as the Anthropic tool, same required set.
DECOMPOSE_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="record_decomposition",
            description=(
                "Record a morphological decomposition of an English word. Call this "
                "exactly once per word. Set confidence to 'low' (and leave decomposition "
                "as an empty array) if the word cannot be reliably decomposed."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "word": types.Schema(type=types.Type.STRING),
                    "decomposition": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "morpheme": types.Schema(type=types.Type.STRING),
                                "type": types.Schema(
                                    type=types.Type.STRING,
                                    enum=["prefix", "root", "suffix"],
                                ),
                                "meaning": types.Schema(type=types.Type.STRING),
                                "language": types.Schema(type=types.Type.STRING),
                                "canonical_root": types.Schema(type=types.Type.STRING),
                                "etymology": types.Schema(type=types.Type.STRING),
                            },
                            required=["morpheme", "type"],
                        ),
                    ),
                    "confidence": types.Schema(
                        type=types.Type.STRING,
                        enum=["high", "medium", "low"],
                    ),
                    "reasoning": types.Schema(type=types.Type.STRING),
                },
                required=["word", "decomposition", "confidence", "reasoning"],
            ),
        )
    ]
)


# Gemini 2.5 Flash pricing (as of 2026-05). Per million tokens.
# Source: https://ai.google.dev/pricing
PRICING = {"input": 0.30, "output": 2.50}


def call_decompose(client: genai.Client, word: str, system_prompt: str) -> tuple[dict, dict]:
    """Call Gemini with forced function-call mode. Returns (record, usage)."""
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[DECOMPOSE_TOOL],
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode=types.FunctionCallingConfigMode.ANY,
                allowed_function_names=["record_decomposition"],
            )
        ),
        # Gemini's default temperature is 1.0; lower for measurement reproducibility.
        temperature=0.2,
    )

    response = client.models.generate_content(
        model=MODEL,
        contents=word,
        config=config,
    )

    # Extract the function-call arguments.
    candidates = response.candidates or []
    if not candidates:
        raise RuntimeError(f"No candidates in response for {word!r}")
    parts = candidates[0].content.parts or []
    function_calls = [p.function_call for p in parts if p.function_call is not None]
    if not function_calls:
        raise RuntimeError(
            f"No function_call in response for {word!r}; "
            f"finish_reason={candidates[0].finish_reason!r}"
        )
    fc = function_calls[0]
    # Gemini's args are a google.protobuf.Struct; convert to dict.
    record = dict(fc.args)

    # Usage stats. Gemini's response.usage_metadata has prompt_token_count,
    # candidates_token_count, total_token_count, cached_content_token_count.
    um = response.usage_metadata
    input_tokens = getattr(um, "prompt_token_count", 0) or 0
    output_tokens = getattr(um, "candidates_token_count", 0) or 0
    cache_read = getattr(um, "cached_content_token_count", 0) or 0
    usage = {
        "input_tokens": input_tokens - cache_read,
        "output_tokens": output_tokens,
        "cache_creation_input_tokens": 0,  # Gemini implicit cache; no separate write count
        "cache_read_input_tokens": cache_read,
    }
    return record, usage


def estimate_cost_per_call(usage: dict) -> float:
    """Per Gemini pricing. Cache reads on 2.5 Flash are billed at 25% of input rate."""
    fresh_input = usage["input_tokens"]
    cache_read = usage["cache_read_input_tokens"]
    output = usage["output_tokens"]
    return (
        fresh_input * PRICING["input"] / 1_000_000
        + cache_read * PRICING["input"] * 0.25 / 1_000_000
        + output * PRICING["output"] / 1_000_000
    )


def run_word(client, word: str, system_prompt: str) -> dict:
    last_error = None
    for attempt in range(2):
        try:
            record, usage = call_decompose(client, word, system_prompt)
            return {
                "word": word,
                "ok": True,
                "decomposition": record,
                "usage": usage,
                "cost_usd": estimate_cost_per_call(usage),
            }
        except Exception as e:
            last_error = repr(e)
            if attempt == 0:
                time.sleep(2)
                continue
            return {"word": word, "ok": False, "error": last_error}
    return {"word": word, "ok": False, "error": last_error}


def main() -> int:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY (or GOOGLE_API_KEY) not set", file=sys.stderr)
        return 2

    client = genai.Client(api_key=api_key)
    system_prompt = load_system_prompt()
    RESULTS.mkdir(exist_ok=True)

    test_set = json.loads((DATA / "test-set.json").read_text(encoding="utf-8"))
    adversarial = json.loads((DATA / "adversarial-set.json").read_text(encoding="utf-8"))

    print(f"=== {MODEL} ===")
    print(f"system prompt length: ~{len(system_prompt)} chars")

    test_results = []
    for entry in test_set:
        rec = run_word(client, entry["word"], system_prompt)
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
            rec = run_word(client, entry["word"], system_prompt)
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

    (RESULTS / "gemini-test-set.json").write_text(
        json.dumps(test_results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (RESULTS / "gemini-adversarial.json").write_text(
        json.dumps(adv_results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    all_records = list(test_results) + [r for cat in adv_results.values() for r in cat]
    total = {
        "model": MODEL,
        "num_calls": len(all_records),
        "successful": sum(1 for r in all_records if r["ok"]),
        "failed": sum(1 for r in all_records if not r["ok"]),
        "total_input_tokens": sum(r.get("usage", {}).get("input_tokens", 0) for r in all_records),
        "total_output_tokens": sum(r.get("usage", {}).get("output_tokens", 0) for r in all_records),
        "total_cache_creation_tokens": sum(
            r.get("usage", {}).get("cache_creation_input_tokens", 0) for r in all_records
        ),
        "total_cache_read_tokens": sum(
            r.get("usage", {}).get("cache_read_input_tokens", 0) for r in all_records
        ),
        "total_cost_usd": round(sum(r.get("cost_usd", 0) for r in all_records), 6),
    }
    (RESULTS / "gemini-usage.json").write_text(json.dumps(total, indent=2), encoding="utf-8")
    print()
    print(json.dumps(total, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
