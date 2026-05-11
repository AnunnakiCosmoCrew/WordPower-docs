#!/usr/bin/env python3
"""Validation run — Gemini 2.5 Flash on the same top-1k words used by PR #539's Haiku pilot.

Question this answers: does Gemini 2.5 Flash maintain comparable quality to Claude
Haiku 4.5 on the actual top-1k production frequency words (not the 51-word spike
test set)? If yes, the architecture decision to use Gemini stands. If Gemini
materially regresses, that's new evidence justifying a deviation from the locked
architecture.

Reads:
  /tmp/wp-527-pilot/top1k.txt  (top-1k SUBTLEX-US words from PR #539's branch)
  ../../spikes/morphology-engine/c-llm-haiku/scripts/prompt.md  (locked prompt-v1, SHA-verified)

Writes:
  ../validation/gemini-top1k-cache.json  (same envelope shape as PR #539's haiku-top1k JSON)

Requires GEMINI_API_KEY in the environment.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

MODEL = "gemini-2.5-flash"
LOCKED_PROMPT_SHA = "eb2f0aa38daa08a2ac5ee04c769ef81ddd4f040434c3c8ba99c35df1675f9de7"

HERE = Path(__file__).resolve().parent
DOCS_REPO = HERE.parent.parent
PROMPT_MD = DOCS_REPO / "spikes" / "morphology-engine" / "c-llm-haiku" / "scripts" / "prompt.md"
WORDLIST = Path("/tmp/wp-527-pilot/top1k.txt")
OUTPUT = HERE / "gemini-top1k-cache.json"


def load_system_prompt() -> str:
    """Load + verify the locked prompt-v1. Same logic as PR #539's _shared.py."""
    raw = PROMPT_MD.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != LOCKED_PROMPT_SHA:
        raise RuntimeError(
            f"prompt.md SHA mismatch — expected {LOCKED_PROMPT_SHA}, got {actual_sha}"
        )
    text = PROMPT_MD.read_text(encoding="utf-8")
    blocks = re.split(r"^```$", text, flags=re.MULTILINE)
    return blocks[2].strip()


# Gemini function-calling tool — mirrors PR #539's Anthropic tool schema (which mirrors §6).
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

PRICING = {"input": 0.30, "output": 2.50}  # USD per million tokens


def call_decompose(client: genai.Client, word: str, system_prompt: str) -> tuple[dict, dict]:
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[DECOMPOSE_TOOL],
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode=types.FunctionCallingConfigMode.ANY,
                allowed_function_names=["record_decomposition"],
            )
        ),
        temperature=0.2,
    )
    response = client.models.generate_content(model=MODEL, contents=word, config=config)
    cand = (response.candidates or [None])[0]
    if not cand:
        raise RuntimeError(f"no candidates for {word!r}")
    fcs = [p.function_call for p in (cand.content.parts or []) if p.function_call]
    if not fcs:
        raise RuntimeError(f"no function_call for {word!r} (finish={cand.finish_reason!r})")
    record = dict(fcs[0].args)
    um = response.usage_metadata
    cache_read = getattr(um, "cached_content_token_count", 0) or 0
    input_tokens = (getattr(um, "prompt_token_count", 0) or 0) - cache_read
    output_tokens = getattr(um, "candidates_token_count", 0) or 0
    usage = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_input_tokens": cache_read,
    }
    cost = (input_tokens * PRICING["input"]
            + cache_read * PRICING["input"] * 0.25
            + output_tokens * PRICING["output"]) / 1_000_000
    return record, usage, round(cost, 6)


def run_word(client, word: str, system_prompt: str) -> dict:
    last_err = None
    for attempt in range(3):
        try:
            record, usage, cost = call_decompose(client, word, system_prompt)
            return {
                "word": word,
                "ok": True,
                "confidence": record.get("confidence"),
                "decomposition": record.get("decomposition", []),
                "reasoning": record.get("reasoning", ""),
                "usage": usage,
                "cost_usd": cost,
            }
        except Exception as e:
            last_err = repr(e)[:200]
            wait = 2 ** attempt
            if attempt < 2:
                time.sleep(wait)
                continue
            return {"word": word, "ok": False, "error": last_err}
    return {"word": word, "ok": False, "error": last_err}


def main() -> int:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set", file=sys.stderr)
        return 2
    if not WORDLIST.exists():
        print(f"ERROR: {WORDLIST} missing. Fetch top-1k from PR #539 first.", file=sys.stderr)
        return 2

    client = genai.Client(api_key=api_key)
    system_prompt = load_system_prompt()
    words = [w.strip() for w in WORDLIST.read_text().splitlines() if w.strip()]
    print(f"=== {MODEL} on top-{len(words)} (prompt-v1 SHA-verified) ===")

    start = time.monotonic()
    records = []
    total_cost = 0.0
    for i, word in enumerate(words, 1):
        rec = run_word(client, word, system_prompt)
        records.append(rec)
        total_cost += rec.get("cost_usd", 0)
        if i % 50 == 0 or i == len(words):
            print(f"  {i:4d}/{len(words)}  spent=${total_cost:.4f}  last={word!r}")

    elapsed = time.monotonic() - start
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    ok = sum(1 for r in records if r["ok"])
    confidence_counts = {}
    for r in records:
        if r["ok"]:
            c = r.get("confidence", "unknown")
            confidence_counts[c] = confidence_counts.get(c, 0) + 1

    envelope = {
        "model": MODEL,
        "prompt_sha": LOCKED_PROMPT_SHA,
        "word_count": len(words),
        "ok_count": ok,
        "fail_count": len(records) - ok,
        "confidence_distribution": confidence_counts,
        "total_cost_usd": round(total_cost, 6),
        "elapsed_seconds": round(elapsed, 1),
        "records": records,
    }
    OUTPUT.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")
    print()
    print(json.dumps({k: v for k, v in envelope.items() if k != "records"}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
