#!/usr/bin/env python3
"""Parse GCIDE (Webster's 1913 + supplements) into a queryable JSON index.

Input:  ../data/gcide-0.54/CIDE.A through CIDE.Z (gitignored)
Output:
  ../data/gcide-index.json (gitignored, derived)
      {lowercase_headword: [{headword, pos, etymology:{...}, source}, ...]}
  ../data/extract-stats.txt (committed) — summary counts.

GCIDE entry shape (one entry per <p>...</p> block whose first inner tag is <ent>):
  <p><ent>Philosophy</ent><br/
  <hw>Phi*los"o*phy</hw> <pr>(...)</pr>, <pos>n.</pos>; ...
  <ety>[OE. <ets>philosophie</ets>, F. <ets>philosophie</ets>, L.
  <ets>philosophia</ets>, from Gr. <grk>filosofi`a</grk>. See
  <er>Philosopher</er>.]</ety> <sn>1.</sn> <def>...</def><br/
  [<source>1913 Webster</source>]</p>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"
GCIDE_DIR = DATA_DIR / "gcide-0.54"
INDEX_OUT = DATA_DIR / "gcide-index.json"
STATS_OUT = DATA_DIR / "extract-stats.txt"

# Language-abbreviation set from GCIDE's abbrevn.lst (filtered to ones likely
# to appear in etymology blocks). Used to detect source languages by string
# match with a trailing period.
LANG_ABBREVS = {
    "AS.": "Anglo-Saxon",
    "Ar.": "Arabic",
    "Arm.": "Armorican",
    "Bohem.": "Bohemian",
    "Br.": "Breton",
    "Cf.": None,  # "compare", not a language
    "D.": "Dutch",
    "Dan.": "Danish",
    "Du.": "Dutch",
    "E.": "English",
    "F.": "French",
    "Fin.": "Finnish",
    "Fr.": "French",
    "Gael.": "Gaelic",
    "Ger.": "German",
    "Goth.": "Gothic",
    "Gr.": "Greek",
    "Heb.": "Hebrew",
    "Hind.": "Hindi",
    "Icel.": "Icelandic",
    "Ir.": "Irish",
    "It.": "Italian",
    "L.": "Latin",
    "LG.": "Low German",
    "LGr.": "Late Greek",
    "LL.": "Late Latin",
    "MHG.": "Middle High German",
    "ME.": "Middle English",
    "Mex.": "Mexican",
    "NL.": "New Latin",
    "Norm.": "Norman",
    "Norw.": "Norwegian",
    "OE.": "Old English",
    "OF.": "Old French",
    "OHG.": "Old High German",
    "ON.": "Old Norse",
    "Pers.": "Persian",
    "Pg.": "Portuguese",
    "Pol.": "Polish",
    "Pr.": "Provencal",
    "Russ.": "Russian",
    "Sax.": "Saxon",
    "Skr.": "Sanskrit",
    "Slav.": "Slavonic",
    "Sp.": "Spanish",
    "Sw.": "Swedish",
    "Turk.": "Turkish",
    "W.": "Welsh",
}

ENTRY_BLOCK_RE = re.compile(r"<p><ent>([^<]+)</ent>(.*?)</p>", re.DOTALL)
ETY_RE = re.compile(r"<ety>(.*?)</ety>", re.DOTALL)
ETS_RE = re.compile(r"<ets>(.*?)</ets>", re.DOTALL)
GRK_RE = re.compile(r"<grk>(.*?)</grk>", re.DOTALL)
ER_RE = re.compile(r"<er>(.*?)</er>", re.DOTALL)
SOURCE_RE = re.compile(r"<source>(.*?)</source>", re.DOTALL)
POS_RE = re.compile(r"<pos>(.*?)</pos>", re.DOTALL)
TAG_STRIP_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def detect_languages(ety_raw: str) -> list[str]:
    """Find language abbreviations in the etymology block.

    We do simple substring detection — `F.`, `L.`, `Gr.` etc. The match must
    be at a word boundary on the left and followed by whitespace or `,` etc.
    """
    found: list[str] = []
    for abbr in LANG_ABBREVS:
        if LANG_ABBREVS[abbr] is None:
            continue
        # Word boundary on left, must be followed by space or punctuation.
        pat = re.compile(rf"(?:^|[\s\(\[]){re.escape(abbr)}(?=[\s,\]])")
        if pat.search(ety_raw):
            found.append(abbr)
    return found


def clean_text(s: str) -> str:
    """Strip XML-ish tags and collapse whitespace."""
    s = TAG_STRIP_RE.sub(" ", s)
    s = WHITESPACE_RE.sub(" ", s).strip()
    # Drop the surrounding [ ] of an etymology block.
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1].strip()
    return s


def parse_entry(headword: str, body: str) -> dict:
    pos_match = POS_RE.search(body)
    pos = clean_text(pos_match.group(1)) if pos_match else None

    source_match = SOURCE_RE.search(body)
    source = clean_text(source_match.group(1)) if source_match else None

    ety_match = ETY_RE.search(body)
    if ety_match:
        ety_raw = ety_match.group(1)
        ets_tokens = [clean_text(t) for t in ETS_RE.findall(ety_raw)]
        grk_tokens = [clean_text(t) for t in GRK_RE.findall(ety_raw)]
        cross_refs = [clean_text(t) for t in ER_RE.findall(ety_raw)]
        languages = detect_languages(ety_raw)
        ety = {
            "present": True,
            "raw": clean_text(ety_raw),
            "ets_tokens": ets_tokens,
            "grk_tokens": grk_tokens,
            "languages": languages,
            "cross_refs": cross_refs,
        }
    else:
        ety = {"present": False}

    return {
        "headword": headword.strip(),
        "pos": pos,
        "source": source,
        "etymology": ety,
    }


def main() -> int:
    if not GCIDE_DIR.exists():
        print(f"ERROR: {GCIDE_DIR} missing. Run scripts/download.sh first.",
              file=sys.stderr)
        return 1

    index: dict[str, list[dict]] = {}
    per_letter: dict[str, int] = {}
    total_entries = 0
    entries_with_ety = 0
    source_counts: dict[str, int] = {}

    for letter_path in sorted(GCIDE_DIR.glob("CIDE.[A-Z]")):
        letter = letter_path.suffix.lstrip(".")
        text = letter_path.read_text(encoding="latin-1", errors="replace")
        count_in_letter = 0
        for m in ENTRY_BLOCK_RE.finditer(text):
            headword = m.group(1).strip()
            body = m.group(2)
            entry = parse_entry(headword, body)
            key = headword.lower()
            index.setdefault(key, []).append(entry)
            total_entries += 1
            count_in_letter += 1
            if entry["etymology"]["present"]:
                entries_with_ety += 1
            if entry["source"]:
                source_counts[entry["source"]] = source_counts.get(entry["source"], 0) + 1
        per_letter[letter] = count_in_letter

    INDEX_OUT.write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    lines = [
        "GCIDE 0.54 — extraction stats",
        f"source dir: {GCIDE_DIR.name}",
        f"total entries parsed: {total_entries}",
        f"distinct lowercase headwords: {len(index)}",
        f"entries with <ety> block: {entries_with_ety} ({100*entries_with_ety/total_entries:.1f}%)",
        "",
        "entries per letter:",
    ]
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        lines.append(f"  {letter}: {per_letter.get(letter, 0)}")
    lines.append("")
    lines.append("source-tag distribution (top 10):")
    for src, n in sorted(source_counts.items(), key=lambda kv: -kv[1])[:10]:
        lines.append(f"  {src!s:30s} {n}")
    stats_text = "\n".join(lines) + "\n"
    STATS_OUT.write_text(stats_text, encoding="utf-8")
    print(stats_text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
