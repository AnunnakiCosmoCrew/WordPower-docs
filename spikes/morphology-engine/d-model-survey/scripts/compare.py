#!/usr/bin/env python3
"""Score Gemini results and build a 3-way comparison table (Haiku / Sonnet / Gemini).

Reuses Spike C's scoring functions via a sys.path import — no duplicate code.

Reads:
  ../results/gemini-test-set.json, gemini-adversarial.json, gemini-usage.json
  ../../c-llm-haiku/results/{haiku,sonnet}-test-set.json + adversarial + usage

Writes:
  ../results/comparison.json   (full per-model breakdown)
  ../results/comparison.md     (human-readable comparison table)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPIKE_C_SCRIPTS = HERE.parent.parent / "c-llm-haiku" / "scripts"
# Use results-v1 (re-baselined on the extended prompt) so the 3-way comparison
# is apples-to-apples on the prompt we'd actually ship. Override with
# BASELINE_DIR=results to compare against the original Spike C numbers.
import os as _os  # noqa: E402
_baseline = _os.environ.get("BASELINE_DIR", "results-v1")
SPIKE_C_RESULTS = HERE.parent.parent / "c-llm-haiku" / _baseline
RESULTS = HERE.parent / "results"

# Pull Spike C's scoring functions verbatim.
sys.path.insert(0, str(SPIKE_C_SCRIPTS))
from measure import summarize_test, summarize_adversarial  # noqa: E402


def load_model(prefix: str, results_dir: Path) -> dict:
    test = json.loads((results_dir / f"{prefix}-test-set.json").read_text(encoding="utf-8"))
    adv = json.loads((results_dir / f"{prefix}-adversarial.json").read_text(encoding="utf-8"))
    usage = json.loads((results_dir / f"{prefix}-usage.json").read_text(encoding="utf-8"))
    return {
        "test_set": summarize_test(test),
        "adversarial": summarize_adversarial(adv),
        "usage": usage,
    }


def project_cost(usage: dict, target_count: int = 30_000) -> float:
    n = usage["num_calls"]
    if n == 0:
        return 0.0
    avg = usage["total_cost_usd"] / n
    return round(avg * target_count, 2)


def main() -> int:
    haiku = load_model("haiku", SPIKE_C_RESULTS)
    sonnet = load_model("sonnet", SPIKE_C_RESULTS)
    gemini = load_model("gemini", RESULTS)

    comparison = {
        "haiku-4-5": haiku,
        "sonnet-4-6": sonnet,
        "gemini-2-5-flash": gemini,
    }

    # Headline table.
    def headline(m: dict) -> dict:
        ts = m["test_set"]
        adv = m["adversarial"]
        u = m["usage"]
        return {
            "accuracy_strict": ts["accuracy_strict"],
            "accuracy_weighted": ts["accuracy_weighted"],
            "trap_refusal": f"{adv['traps']['refused_count']}/{adv['traps']['total']}",
            "trap_refusal_pass": adv["traps"]["pass"],
            "multi_layer_rate": adv["multi_layer"]["rate"],
            "spike_cost_usd": u["total_cost_usd"],
            "projected_top_30k_usd": project_cost(u),
        }

    headline_data = {model: headline(m) for model, m in comparison.items()}

    (RESULTS / "comparison.json").write_text(
        json.dumps({"models": headline_data, "detail": comparison}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Markdown table.
    lines = [
        "# Spike D — Gemini 2.5 Flash vs Haiku 4.5 vs Sonnet 4.6\n",
        f"Same prompt (Spike C `prompt.md`), same 81-word test set "
        f"(51 test + 30 adversarial), same scoring rubric.\n",
        "## Headline numbers\n",
        "| Metric | Haiku 4.5 | Sonnet 4.6 | Gemini 2.5 Flash | Threshold |",
        "|---|---|---|---|---|",
    ]

    def fmt_pct(v: float) -> str:
        return f"{v*100:.1f}%"

    def row(label, h_v, s_v, g_v, threshold, fmt=fmt_pct):
        return f"| {label} | {fmt(h_v)} | {fmt(s_v)} | {fmt(g_v)} | {threshold} |"

    h = headline_data["haiku-4-5"]
    s = headline_data["sonnet-4-6"]
    g = headline_data["gemini-2-5-flash"]

    lines.append(row("Accuracy (strict)", h["accuracy_strict"], s["accuracy_strict"], g["accuracy_strict"], "≥ 85%"))
    lines.append(row("Accuracy (weighted)", h["accuracy_weighted"], s["accuracy_weighted"], g["accuracy_weighted"], "informational"))
    lines.append(f"| Trap refusal | {h['trap_refusal']} | {s['trap_refusal']} | {g['trap_refusal']} | ≥ 8/10 |")
    lines.append(row("Multi-layer correct/partial", h["multi_layer_rate"], s["multi_layer_rate"], g["multi_layer_rate"], "informational"))
    lines.append(f"| Spike cost (81 calls) | ${h['spike_cost_usd']:.4f} | ${s['spike_cost_usd']:.4f} | ${g['spike_cost_usd']:.4f} | — |")
    lines.append(f"| Projected top-30k cost | ${h['projected_top_30k_usd']:.2f} | ${s['projected_top_30k_usd']:.2f} | ${g['projected_top_30k_usd']:.2f} | ≤ $200 |")

    # Decision section.
    haiku_strict = h["accuracy_strict"]
    gemini_strict = g["accuracy_strict"]
    haiku_traps = h["trap_refusal_pass"]
    gemini_traps = g["trap_refusal_pass"]
    haiku_cost = h["projected_top_30k_usd"]
    gemini_cost = g["projected_top_30k_usd"]

    cost_ratio = haiku_cost / gemini_cost if gemini_cost > 0 else float("inf")

    lines.append("\n## Per-decision-rule verdict\n")
    lines.append("From [`d-model-survey/README.md` § Acceptance criteria](README.md):\n")

    matches_quality_at_lower_cost = (
        abs(gemini_strict - haiku_strict) <= 0.02  # within 2% accuracy
        and gemini_traps
        and cost_ratio >= 2.0
    )
    exceeds_quality_at_same_cost = (
        gemini_strict > haiku_strict
        and gemini_traps
        and gemini_cost <= haiku_cost
    )

    if matches_quality_at_lower_cost:
        verdict = (
            "**SWITCH to Gemini 2.5 Flash.** Matches Haiku 4.5's quality "
            f"(strict accuracy {fmt_pct(gemini_strict)} vs Haiku's {fmt_pct(haiku_strict)}; "
            f"trap refusal pass={gemini_traps}) at ≥ 2× cost reduction "
            f"(Haiku $${haiku_cost:.2f} / Gemini $${gemini_cost:.2f} for top-30k = "
            f"{cost_ratio:.1f}× cheaper). Update `ROOT_FAMILIES_DECISION.md` and "
            f"Phase 3 issue (#527) to use Gemini 2.5 Flash as L1 primary."
        )
    elif exceeds_quality_at_same_cost:
        verdict = (
            "**SWITCH to Gemini 2.5 Flash.** Exceeds Haiku 4.5's quality "
            f"({fmt_pct(gemini_strict)} vs {fmt_pct(haiku_strict)}) at ≤ Haiku's cost "
            f"(Gemini $${gemini_cost:.2f} ≤ Haiku $${haiku_cost:.2f} for top-30k)."
        )
    else:
        # Confirm Haiku.
        reasons = []
        if gemini_strict < haiku_strict - 0.02:
            reasons.append(
                f"accuracy lower ({fmt_pct(gemini_strict)} vs {fmt_pct(haiku_strict)})"
            )
        if not gemini_traps:
            reasons.append(f"trap refusal below threshold ({g['trap_refusal']})")
        if cost_ratio < 2.0 and gemini_cost > haiku_cost * 0.5:
            reasons.append(
                f"cost ratio only {cost_ratio:.1f}× (need ≥ 2× to switch at equivalent quality)"
            )
        if not reasons:
            reasons.append("matches Haiku but doesn't clear the switching threshold")
        verdict = (
            f"**CONFIRM Haiku 4.5** as L1 primary. Gemini 2.5 Flash "
            f"{'; '.join(reasons)}. Keep Haiku for production build per `ROOT_FAMILIES_DECISION.md` §9 row 3."
        )

    lines.append(verdict + "\n")

    # Per-word disagreement.
    lines.append("## Per-word disagreements (common test words)\n")
    h_per = {w["word"]: w for w in haiku["test_set"]["per_word"] if w["category"] == "common"}
    g_per = {w["word"]: w for w in gemini["test_set"]["per_word"] if w["category"] == "common"}
    s_per = {w["word"]: w for w in sonnet["test_set"]["per_word"] if w["category"] == "common"}
    disagreements = []
    for word, hw in h_per.items():
        gw = g_per.get(word)
        if not gw:
            continue
        if hw["verdict"] != gw["verdict"]:
            disagreements.append({
                "word": word,
                "haiku": hw["verdict"],
                "sonnet": s_per.get(word, {}).get("verdict", "?"),
                "gemini": gw["verdict"],
            })
    if disagreements:
        lines.append("| Word | Haiku | Sonnet | Gemini |")
        lines.append("|---|---|---|---|")
        for d in disagreements:
            lines.append(f"| `{d['word']}` | {d['haiku']} | {d['sonnet']} | {d['gemini']} |")
    else:
        lines.append("_All three models reach the same verdict on every common test word._")

    (RESULTS / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
