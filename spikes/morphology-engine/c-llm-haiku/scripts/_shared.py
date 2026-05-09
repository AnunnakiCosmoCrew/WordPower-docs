"""Shared definitions for run_haiku.py and run_sonnet.py.

Single source of truth for:
- The system prompt (loaded from prompt.md, the human-readable spec)
- The forced-tool schema (matching ROOT_FAMILIES_ENGINE.md §6 + a `reasoning`
  field that is spike-only)
- The cached call wrapper (single API call, returns parsed dict + usage)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import anthropic

HERE = Path(__file__).resolve().parent
PROMPT_MD = HERE / "prompt.md"


def load_system_prompt() -> str:
    """Extract the prose system prompt from prompt.md.

    prompt.md has two fenced code blocks:
      1. ```python ... ``` (the tool schema example — language tag, not bare)
      2. ```      ... ```  (the prose system prompt — bare opening)

    We split on lines that are exactly ``` (no language tag). That gives us 3
    delimiter matches and 4 splits:
      [0] file start through end of tool schema (the ```python opener doesn't
          match our bare-``` pattern, so the tool schema's CLOSING ``` is the
          first match)
      [1] markdown prose between the two fenced blocks
      [2] the system prompt body  <-- what we want
      [3] anything after the closing ``` of the system prompt (empty)
    """
    text = PROMPT_MD.read_text(encoding="utf-8")
    blocks = re.split(r"^```$", text, flags=re.MULTILINE)
    if len(blocks) < 3:
        raise RuntimeError(
            f"prompt.md structure changed; expected ≥3 fenced sections, got {len(blocks)}"
        )
    return blocks[2].strip()


# Forced-tool schema. Matches ROOT_FAMILIES_ENGINE.md §6, plus an extra
# `reasoning` field for measurement (not part of the production schema).
DECOMPOSE_TOOL: dict = {
    "name": "record_decomposition",
    "description": (
        "Record a morphological decomposition of an English word. Call this "
        "exactly once per word. Set confidence to 'low' (and leave decomposition "
        "as an empty array) if the word cannot be reliably decomposed."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "word": {"type": "string"},
            "decomposition": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "morpheme": {"type": "string"},
                        "type": {
                            "type": "string",
                            "enum": ["prefix", "root", "suffix"],
                        },
                        "meaning": {"type": "string"},
                        "language": {"type": "string"},
                        "canonical_root": {"type": "string"},
                        "etymology": {"type": "string"},
                    },
                    "required": ["morpheme", "type"],
                },
            },
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            "reasoning": {"type": "string"},
        },
        "required": ["word", "decomposition", "confidence", "reasoning"],
    },
}


def call_decompose(
    client: anthropic.Anthropic,
    model: str,
    word: str,
    system_prompt: str,
) -> tuple[dict, dict]:
    """Call the model on a single word, return (parsed_decomposition, usage_dict).

    Forces the model to call `record_decomposition` exactly once. Caches the
    system prompt with cache_control=ephemeral. Returns the tool input dict
    (which IS the decomposition record) and the usage stats from the response.
    """
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        tools=[DECOMPOSE_TOOL],
        tool_choice={"type": "tool", "name": "record_decomposition"},
        messages=[{"role": "user", "content": word}],
    )

    # The forced-tool call guarantees exactly one tool_use block.
    tool_blocks = [b for b in response.content if b.type == "tool_use"]
    if not tool_blocks:
        raise RuntimeError(
            f"No tool_use block in response for word={word!r}. "
            f"stop_reason={response.stop_reason!r} content={response.content!r}"
        )
    decomposition = tool_blocks[0].input

    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "cache_creation_input_tokens": getattr(
            response.usage, "cache_creation_input_tokens", 0
        ) or 0,
        "cache_read_input_tokens": getattr(
            response.usage, "cache_read_input_tokens", 0
        ) or 0,
    }
    return decomposition, usage


# Pricing per million tokens (input, output) — used for cost projection.
# Cache reads are ~10% of input price, cache writes are ~125%.
PRICING = {
    "claude-haiku-4-5": {"input": 1.0, "output": 5.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
}


def estimate_cost_per_call(usage: dict, model: str) -> float:
    """Estimate USD cost for a single call given its usage record."""
    p = PRICING[model]
    fresh_input = usage["input_tokens"]
    cache_write = usage["cache_creation_input_tokens"]
    cache_read = usage["cache_read_input_tokens"]
    output = usage["output_tokens"]
    return (
        fresh_input * p["input"] / 1_000_000
        + cache_write * p["input"] * 1.25 / 1_000_000
        + cache_read * p["input"] * 0.10 / 1_000_000
        + output * p["output"] / 1_000_000
    )
