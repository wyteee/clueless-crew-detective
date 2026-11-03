"""Candidate features: one row per roster character per story (frozen interface `get_features`).

Roster = the characters of the hand-built alias table in the manifest (pre-reveal forms, guideline
v0.3 merges). It is fixed for a story; masks change only the visible text (CLAUDE.md rule 6), so a
character can have zero mentions in a masked text and still be a candidate.

Mentions: exact, case-sensitive alias forms, longest form first and non-overlapping, so
"Miss Turner" claims its "Turner" before the bare "Turner" (John Turner) is matched.

Feature groups (raw values; the model standardises them within each story):
  visibility  v_log_mentions   log(1 + mentions)
              v_mention_share  mentions / all roster mentions in the visible text
              v_first_pos      relative word position of the first mention (1.0 = never mentioned)
              v_para_coverage  share of visible paragraphs mentioning the character
  interaction i_degree         degree centrality in the paragraph co-occurrence network of the roster
              i_strength_share weighted degree / total weighted degree
              i_pagerank       weighted PageRank
  crime       c_log_hits       log(1 + crime-term tokens within CRIME_WINDOW words of any mention)
              c_hit_share      those tokens / all crime tokens near any roster mention
              c_hit_rate       crime tokens near the character per mention
"""
import json
import re
from functools import lru_cache
from itertools import combinations
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

from src import config
from src.aliases import read_paragraphs
from src.masking import full_prefix_mask, story_units

ROOT = Path(__file__).resolve().parents[1]

GROUPS = {
    "visibility": ["v_log_mentions", "v_mention_share", "v_first_pos", "v_para_coverage"],
    "interaction": ["i_degree", "i_strength_share", "i_pagerank"],
    "crime": ["c_log_hits", "c_hit_share", "c_hit_rate"],
}

# Word-initial stems; a token counts if it starts with one of them (lower case). Stems are chosen
# not to hit common non-crime words or names (e.g. "rob" would match Robert,
# "forg" forget, "stab" stable, "accus" accustomed; "struck" is mostly "it struck me").
CRIME_STEMS = [
    # violence and death
    "murder", "kill", "slay", "slain", "dead", "death", "died", "dying", "corpse", "body", "blood",
    "wound", "stabbed", "stabbing", "strangl", "shot", "shoot", "violen", "attack", "assault",
    # weapons and means
    "weapon", "pistol", "revolver", "gun", "knife", "dagger", "poison", "strychnine", "arsenic",
    "rope", "harpoon",
    # property crime and deceit
    "crime", "criminal", "guilt", "thief", "theft", "steal", "stole", "stolen", "robbe", "robbed", "burglar",
    "fraud", "forger", "forged", "blackmail", "disguis", "lied", "liar", "false", "conceal", "hidden", "hiding",
    # investigation
    "police", "arrest", "suspect", "suspicio", "alibi", "motive", "clue", "evidence", "victim",
    "inquest", "accuse", "accusa", "confess", "escape", "fled", "flight", "footprint", "trace",
]
_CRIME_RE = re.compile(r"^(?:" + "|".join(sorted(CRIME_STEMS, key=len, reverse=True)) + r")")
_TOKEN_RE = re.compile(r"[\w’'\-]+")


@lru_cache(maxsize=None)
def load_story_meta(story_id):
    """reveal_para_idx, principal culprit, accomplices and alias table from the manifest."""
    for f in ("annotations.csv", "pilot.csv"):
        m = pd.read_csv(ROOT / "manifest" / f, dtype=str, keep_default_na=False)
        if (m.story_id == story_id).any():
            r = m.set_index("story_id").loc[story_id]
            culprits = r.culprit.split("; ")
            return {"reveal_para_idx": int(r.reveal_para_idx), "principal": culprits[0],
                    "accomplices": culprits[1:], "aliases": json.loads(r.aliases)}
    raise KeyError(story_id)


def eligible_story_ids():
    """The 30 eligible main stories (pilot excluded)."""
    return pd.read_csv(ROOT / "manifest" / "annotations.csv").story_id.tolist()


def visible_paragraphs(story_id, text_mask=None):
    """[(para_idx, text)] built from the visible sentence units; never at/after the reveal."""
    meta = load_story_meta(story_id)
    units = story_units(story_id)
    mask = full_prefix_mask(units, meta["reveal_para_idx"]) if text_mask is None else np.asarray(text_mask)
    mask = mask & (units.para_idx < meta["reveal_para_idx"]).to_numpy()
    texts = dict(read_paragraphs(story_id))
    out = []
    for idx, g in units[mask].groupby("para_idx", sort=True):
        t = texts[idx]
        out.append((idx, " ".join(t[a:b] for a, b in zip(g.start, g.end))))
    return out


def _alias_regex(aliases):
    form_to_char = {}
    for char, forms in aliases.items():
        for f in forms:
            form_to_char.setdefault(f, char)
    forms = sorted(form_to_char, key=len, reverse=True)
    if not forms:
        return None, form_to_char
    pat = re.compile(r"(?<![\w\-])(?:" + "|".join(map(re.escape, forms)) + r")(?![\w\-])")
    return pat, form_to_char


def find_mentions(paragraphs, aliases):
    """DataFrame: para_idx, character, word_pos (global word index in the visible text).

    Also returns the list of all visible tokens (lower case) for the crime-term windows.
    """
    pat, form_to_char = _alias_regex(aliases)
    rows, tokens, offset = [], [], 0
    for idx, text in paragraphs:
        toks = list(_TOKEN_RE.finditer(text))
        starts = np.array([t.start() for t in toks])
        if pat is not None:
            for m in pat.finditer(text):
                w = int(np.searchsorted(starts, m.start(), side="right") - 1) if len(starts) else 0
                rows.append({"para_idx": idx, "character": form_to_char[m.group(0)],
                             "word_pos": offset + max(w, 0)})
        tokens.extend(t.group(0).lower() for t in toks)
        offset += len(toks)
    return pd.DataFrame(rows, columns=["para_idx", "character", "word_pos"]), tokens


def get_features(story_id, text_mask=None):
    """Feature rows for every roster character of `story_id` under `text_mask`
    (boolean array over `masking.story_units(story_id)`; None = full pre-reveal text)."""
    meta = load_story_meta(story_id)
    roster = list(meta["aliases"])
    paras = visible_paragraphs(story_id, text_mask)
    mentions, tokens = find_mentions(paras, meta["aliases"])
    n_words, n_paras = max(len(tokens), 1), max(len(paras), 1)

    counts = mentions.character.value_counts()
    first = mentions.groupby("character").word_pos.min()
    coverage = mentions.groupby("character").para_idx.nunique()

    # paragraph co-occurrence network over the roster
    g = nx.Graph()
    g.add_nodes_from(roster)
    for _, chars in mentions.groupby("para_idx").character:
        for a, b in combinations(sorted(set(chars)), 2):
            w = g[a][b]["weight"] + 1 if g.has_edge(a, b) else 1
            g.add_edge(a, b, weight=w)
    degree = nx.degree_centrality(g) if len(roster) > 1 else {c: 0.0 for c in roster}
    strength = dict(g.degree(weight="weight"))
    total_strength = sum(strength.values())
    pagerank = nx.pagerank(g, weight="weight") if g.number_of_edges() else {c: 1 / len(roster) for c in roster}

    # crime tokens within the window of each character's mentions (union, so no double counting)
    is_crime = np.array([bool(_CRIME_RE.match(t)) for t in tokens], bool)
    near = {}
    for char, pos in mentions.groupby("character").word_pos:
        cover = np.zeros(len(tokens), bool)
        for p in pos:
            cover[max(0, p - config.CRIME_WINDOW):p + config.CRIME_WINDOW + 1] = True
        near[char] = cover
    any_near = np.logical_or.reduce(list(near.values())) if near else np.zeros(len(tokens), bool)
    total_hits = int((is_crime & any_near).sum())

    rows = []
    for c in roster:
        n = int(counts.get(c, 0))
        hits = int((is_crime & near[c]).sum()) if c in near else 0
        rows.append({
            "story_id": story_id, "character": c,
            "is_culprit": int(c == meta["principal"]), "is_accomplice": int(c in meta["accomplices"]),
            "n_mentions": n,
            "v_log_mentions": np.log1p(n),
            "v_mention_share": n / len(mentions) if len(mentions) else 0.0,
            "v_first_pos": first[c] / n_words if n else 1.0,
            "v_para_coverage": coverage.get(c, 0) / n_paras,
            "i_degree": degree[c],
            "i_strength_share": strength[c] / total_strength if total_strength else 0.0,
            "i_pagerank": pagerank[c],
            "c_log_hits": np.log1p(hits),
            "c_hit_share": hits / total_hits if total_hits else 0.0,
            "c_hit_rate": hits / n if n else 0.0,
        })
    return pd.DataFrame(rows)
