#!/usr/bin/env python3
"""Compare Gemini 2.5 Flash vs Claude Haiku 4.5 on the same top-1k production words.

Inputs:
  /tmp/wp-527-pilot/haiku-top1k.json  (from PR #539 — feature/wp-527-l1-cache-pipeline)
  ./gemini-top1k-cache.json           (produced by run_gemini_top1k.py)

Output:
  ./top1k-comparison.md  (human-readable verdict)
  ./top1k-comparison.json (per-word agreement data)

Decision logic (per ROOT_FAMILIES_DECISION.md and Spike D rules):
  - Both models agree on confidence + decomposition shape → "agreement"
  - Disagreement on confidence (high vs low) → flag for review
  - Disagreement on morpheme count → flag for review

If agreement_rate ≥ 90% across the 1000 words, Gemini is validated for production
and the locked-architecture switch should proceed. If < 90%, the architecture
decision should be revisited.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
HAIKU_FILE = Path("/tmp/wp-527-pilot/haiku-top1k.json")
GEMINI_FILE = HERE / "gemini-top1k-cache.json"
MD_OUT = HERE / "top1k-comparison.md"
JSON_OUT = HERE / "top1k-comparison.json"


def main() -> int:
    haiku = json.loads(HAIKU_FILE.read_text(encoding="utf-8"))
    gemini = json.loads(GEMINI_FILE.read_text(encoding="utf-8"))

    haiku_by_word = {r["word"]: r for r in haiku["records"]}
    gemini_by_word = {r["word"]: r for r in gemini["records"]}

    # Sanity check
    if set(haiku_by_word) != set(gemini_by_word):
        only_h = set(haiku_by_word) - set(gemini_by_word)
        only_g = set(gemini_by_word) - set(haiku_by_word)
        print(f"WARN: word sets differ. Haiku-only={len(only_h)} Gemini-only={len(only_g)}")

    common = sorted(set(haiku_by_word) & set(gemini_by_word))

    agreements = 0
    confidence_diffs = []
    shape_diffs = []
    only_gemini_decomposed = []
    only_haiku_decomposed = []

    for word in common:
        h = haiku_by_word[word]
        g = gemini_by_word[word]
        h_conf = h.get("confidence")
        g_conf = g.get("confidence")
        h_count = len(h.get("decomposition", []))
        g_count = len(g.get("decomposition", []))

        # Bucket: did both refuse, both decompose, or disagree?
        h_refused = h_conf == "low" or h_count == 0
        g_refused = g_conf == "low" or g_count == 0

        if h_refused and g_refused:
            agreements += 1
        elif (not h_refused) and (not g_refused):
            # Both decomposed — check shape similarity
            if abs(h_count - g_count) <= 1 and h_conf == g_conf:
                agreements += 1
            else:
                shape_diffs.append({
                    "word": word,
                    "haiku_conf": h_conf,
                    "gemini_conf": g_conf,
                    "haiku_morphemes": h_count,
                    "gemini_morphemes": g_count,
                    "haiku_decomp": [m.get("morpheme", "") for m in h.get("decomposition", [])],
                    "gemini_decomp": [m.get("morpheme", "") for m in g.get("decomposition", [])],
                })
        elif h_refused and not g_refused:
            only_gemini_decomposed.append({
                "word": word,
                "gemini_conf": g_conf,
                "gemini_morphemes": g_count,
                "gemini_decomp": [m.get("morpheme", "") for m in g.get("decomposition", [])],
            })
            confidence_diffs.append((word, "haiku=refused", f"gemini={g_conf}"))
        else:  # gemini refused, haiku decomposed
            only_haiku_decomposed.append({
                "word": word,
                "haiku_conf": h_conf,
                "haiku_morphemes": h_count,
                "haiku_decomp": [m.get("morpheme", "") for m in h.get("decomposition", [])],
            })
            confidence_diffs.append((word, f"haiku={h_conf}", "gemini=refused"))

    total = len(common)
    agreement_rate = agreements / total if total else 0.0
    decision_pass = agreement_rate >= 0.90

    out = {
        "total_words": total,
        "agreements": agreements,
        "agreement_rate": round(agreement_rate, 4),
        "shape_diffs": len(shape_diffs),
        "only_haiku_decomposed": len(only_haiku_decomposed),
        "only_gemini_decomposed": len(only_gemini_decomposed),
        "haiku_cost_usd": haiku.get("total_cost_usd"),
        "gemini_cost_usd": gemini.get("total_cost_usd"),
        "haiku_confidence_distribution": haiku.get("confidence_distribution"),
        "gemini_confidence_distribution": gemini.get("confidence_distribution"),
        "decision_threshold": 0.90,
        "decision_pass": decision_pass,
        "shape_diff_details": shape_diffs[:50],  # first 50 for the doc
        "only_haiku_decomposed_details": only_haiku_decomposed[:30],
        "only_gemini_decomposed_details": only_gemini_decomposed[:30],
    }
    JSON_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    # Build markdown.
    lines = [
        "# Top-1k Validation — Gemini 2.5 Flash vs Claude Haiku 4.5\n",
        f"Same 1000 SUBTLEX-US words, same prompt-v1, same forced-tool-call schema. "
        f"Haiku results from PR #539; Gemini results from this validation run.\n",
        "## Headline\n",
        "| Metric | Haiku 4.5 | Gemini 2.5 Flash |",
        "|---|---|---|",
        f"| Cost ($1000 words) | ${haiku.get('total_cost_usd'):.4f} | ${gemini.get('total_cost_usd'):.4f} |",
        f"| Confidence: high | {haiku.get('confidence_distribution', {}).get('high', 0)} | {gemini.get('confidence_distribution', {}).get('high', 0)} |",
        f"| Confidence: medium | {haiku.get('confidence_distribution', {}).get('medium', 0)} | {gemini.get('confidence_distribution', {}).get('medium', 0)} |",
        f"| Confidence: low | {haiku.get('confidence_distribution', {}).get('low', 0)} | {gemini.get('confidence_distribution', {}).get('low', 0)} |",
        "",
        "## Cross-model agreement\n",
        f"- **Agreement rate:** {agreements}/{total} = **{agreement_rate*100:.1f}%** "
        f"(threshold ≥ 90% → **{'PASS' if decision_pass else 'FAIL'}**)",
        f"- Shape disagreements (both decomposed, different morpheme count or confidence): {len(shape_diffs)}",
        f"- Only Haiku decomposed (Gemini refused): {len(only_haiku_decomposed)}",
        f"- Only Gemini decomposed (Haiku refused): {len(only_gemini_decomposed)}",
        "",
        "## Verdict\n",
    ]
    if decision_pass:
        lines.append(
            "**Gemini validated. Locked-architecture switch should proceed.** "
            "Gemini agrees with Haiku on at least 90% of the top-1k production words. "
            "Combined with the -30% cost from Spike D, switching to Gemini for the "
            "top-10k production build is the right call.\n"
        )
    else:
        lines.append(
            f"**Gemini does not match Haiku at production scale ({agreement_rate*100:.1f}% < 90%).** "
            "New evidence justifies revisiting the locked architecture decision. "
            "Options: (a) keep Haiku as L1 primary (architectural exception); "
            "(b) tighten the prompt to recover Gemini quality; (c) ship Haiku for v1, "
            "revisit Gemini in v2.\n"
        )

    if shape_diffs:
        lines.append("## Shape disagreements (first 25)\n")
        lines.append("| Word | Haiku conf | Gemini conf | Haiku morphemes | Gemini morphemes |")
        lines.append("|---|---|---|---|---|")
        for d in shape_diffs[:25]:
            h_morphs = " + ".join(d["haiku_decomp"][:6])
            g_morphs = " + ".join(d["gemini_decomp"][:6])
            lines.append(
                f"| `{d['word']}` | {d['haiku_conf']} | {d['gemini_conf']} | "
                f"{h_morphs} | {g_morphs} |"
            )

    if only_haiku_decomposed:
        lines.append("\n## Only Haiku decomposed (Gemini refused) — first 25\n")
        lines.append("These are cases where Haiku tried; Gemini said low-confidence. "
                     "Manual review needed: are these legitimate decompositions Gemini is missing, "
                     "or false-positives Gemini is correctly refusing?\n")
        lines.append("| Word | Haiku conf | Haiku decomp |")
        lines.append("|---|---|---|")
        for d in only_haiku_decomposed[:25]:
            morphs = " + ".join(d["haiku_decomp"][:6])
            lines.append(f"| `{d['word']}` | {d['haiku_conf']} | {morphs} |")

    if only_gemini_decomposed:
        lines.append("\n## Only Gemini decomposed (Haiku refused) — first 25\n")
        lines.append("These are cases where Gemini tried; Haiku said low-confidence. "
                     "Manual review needed: legitimate or false-positive?\n")
        lines.append("| Word | Gemini conf | Gemini decomp |")
        lines.append("|---|---|---|")
        for d in only_gemini_decomposed[:25]:
            morphs = " + ".join(d["gemini_decomp"][:6])
            lines.append(f"| `{d['word']}` | {d['gemini_conf']} | {morphs} |")

    MD_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "agreement_rate": agreement_rate,
        "agreements": agreements,
        "total": total,
        "shape_diffs": len(shape_diffs),
        "only_haiku": len(only_haiku_decomposed),
        "only_gemini": len(only_gemini_decomposed),
        "decision_pass": decision_pass,
        "haiku_cost": haiku.get("total_cost_usd"),
        "gemini_cost": gemini.get("total_cost_usd"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
