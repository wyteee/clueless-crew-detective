"""Write one annotation row to manifest/annotations.csv from a JSON spec, after checking it
against the text, and recompute the code-derived fields for every row.

Usage:  python -m src.annotate path/to/spec.json

Spec keys: story_id, annotator, culprit ("principal; accomplice; ..."), reveal_para_idx,
reveal_quote (verbatim; fragments joined by " ... "), aliases ({name: [forms]}, may be {} for a
screened-out row), culprit_before_reveal, exclusion_reason, notes.

Checks (CLAUDE.md rules 3-5, guideline):
- every quote fragment occurs in the reveal paragraph;
- every alias form occurs in the text before the reveal paragraph;
- every culprit has an alias entry; culprit_before_reveal matches the principal's aliases.
Code-derived fields (never typed by hand):
- reveal_pct = reveal_para_idx / n_paragraphs;
- exclusion_reason = other:reveal_before_80pct when reveal_para_idx <= 0.8 * n_paragraphs
  (guideline v0.6), cleared again if the reveal moves later.
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest" / "annotations.csv"
FIELDS = ["annotator", "culprit", "reveal_para_idx", "reveal_quote", "culprit_before_reveal",
          "exclusion_reason", "notes"]
EARLY = "other:reveal_before_80pct"


def n_paragraphs(story_id):
    text = (ROOT / "data" / "processed" / f"{story_id}.txt").read_text(encoding="utf-8")
    return sum(1 for line in text.splitlines() if line.startswith("["))


def check_spec(spec):
    sid = spec["story_id"]
    text = (ROOT / "data" / "processed" / f"{sid}.txt").read_text(encoding="utf-8")
    paras = {line[1:5]: line for line in text.splitlines() if line.startswith("[")}
    if not spec.get("reveal_para_idx"):
        return
    tag = f"{int(spec['reveal_para_idx']):04d}"
    for frag in spec["reveal_quote"].split(" ... "):
        assert frag in paras[tag], f"quote fragment not in [{tag}]: {frag!r}"
    if not spec.get("aliases"):  # screened-out rows (guideline v0.8) carry no aliases
        return
    prefix = text[:text.index(f"[{tag}]")]
    for forms in spec["aliases"].values():
        for a in forms:
            assert a in prefix, f"alias not in pre-reveal text: {a!r}"
    culprits = spec["culprit"].split("; ")
    for c in culprits:
        assert c in spec["aliases"], f"culprit has no alias entry: {c!r}"
    cbr = "yes" if any(a in prefix for a in spec["aliases"][culprits[0]]) else "no"
    assert cbr == spec["culprit_before_reveal"], f"culprit_before_reveal should be {cbr}"


def recompute(m):
    """reveal_pct and the 80% exclusion for every row with a reveal."""
    for j, r in m.iterrows():
        if not r.reveal_para_idx:
            continue
        n = n_paragraphs(r.story_id)
        idx = int(r.reveal_para_idx)
        m.loc[j, "reveal_pct"] = str(round(idx / n, 3))
        late = idx > 0.8 * n
        if not late and not m.loc[j, "exclusion_reason"]:
            m.loc[j, "exclusion_reason"] = EARLY
        elif late and m.loc[j, "exclusion_reason"] == EARLY:
            m.loc[j, "exclusion_reason"] = ""
    return m


def write_row(spec):
    check_spec(spec)
    sid = spec["story_id"]
    m = pd.read_csv(MANIFEST, dtype=str, keep_default_na=False)
    if not (m.story_id == sid).any():  # stories not pre-listed in the manifest (reserves)
        cand = pd.read_csv(ROOT / "data" / "corpus_candidates.csv").set_index("list_id")
        row = {c: "" for c in m.columns} | {"story_id": sid, "title": cand.loc[sid, "title"]}
        m = pd.concat([m, pd.DataFrame([row])], ignore_index=True)
    i = m.index[m.story_id == sid][0]
    for k in FIELDS:
        m.loc[i, k] = str(spec.get(k, "") or "")
    m.loc[i, "aliases"] = json.dumps(spec["aliases"], ensure_ascii=False) if spec.get("aliases") else ""
    m = recompute(m)
    m.to_csv(MANIFEST, index=False)
    return m.loc[i]


if __name__ == "__main__":
    row = write_row(json.load(open(sys.argv[1], encoding="utf-8")))
    print(row.story_id, "ok; reveal_pct =", row.reveal_pct, "| exclusion:", row.exclusion_reason or "-")
