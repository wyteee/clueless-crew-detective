"""Text masks for the two experiments.

A story is cut into sentence units (inside fixed paragraphs, CLAUDE.md rule 2). A mask is a boolean
array over these units: True = the unit is visible to the feature pipeline. `features.get_features`
takes such a mask; `None` means the full pre-reveal text (the unmasked training condition).

- Experiment 1, `prefix_mask(units, share)`: paragraphs with idx <= share * n_paragraphs.
- Experiment 2, `deletion_mask(units, rate, pattern, seed)`: start from the 80% prefix and hide about
  `rate` of its words, either as randomly chosen sentences ("scattered") or as one run of
  consecutive sentences ("continuous"). The roster is not touched (CLAUDE.md rule 6).

Paragraphs at or after the reveal are never visible, whatever the mask says (enforced in features.py).
"""
import re
from functools import lru_cache

import numpy as np
import pandas as pd

from src import config
from src.aliases import read_paragraphs

# A sentence ends at . ! ? (optionally followed by closing quotes/brackets) before whitespace and a
# capital letter or opening quote.
_SENT_END = re.compile(r"(?<=[.!?])[”’\"')\]]*\s+(?=[“‘\"'(\[A-Z])")
# Units ending in these tokens are glued to the next unit (titles, initials).
_ABBREV = re.compile(r"(?:\b(?:Mr|Mrs|Dr|St|Messrs|Mme|Mlle|Col|Capt|Prof|Rev|Lt|Gen|Sgt|No|Jr|Sr)|\b[A-Z])\.$")


def split_sentences(text):
    """[(start, end)] character spans of the sentences of one paragraph."""
    spans, start = [], 0
    for m in _SENT_END.finditer(text):
        spans.append((start, m.start()))
        start = m.end()
    spans.append((start, len(text)))
    merged = []
    for a, b in spans:
        if merged and _ABBREV.search(text[merged[-1][0]:merged[-1][1]]):
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return [(a, b) for a, b in merged if text[a:b].strip()]


@lru_cache(maxsize=None)
def story_units(story_id):
    """DataFrame of sentence units of the whole story: para_idx, start, end, n_words, word_offset.

    Cached; treat as read-only.
    """
    rows = []
    for idx, text in read_paragraphs(story_id):
        for a, b in split_sentences(text):
            rows.append({"para_idx": idx, "start": a, "end": b, "n_words": len(text[a:b].split())})
    units = pd.DataFrame(rows)
    units["word_offset"] = units.n_words.cumsum() - units.n_words
    units.attrs["n_paragraphs"] = len(read_paragraphs(story_id))
    return units


def full_prefix_mask(units, reveal_para_idx):
    """All units strictly before the reveal paragraph (the unmasked condition)."""
    return (units.para_idx < reveal_para_idx).to_numpy()


def prefix_mask(units, share):
    """Units in paragraphs idx <= share * n_paragraphs (Experiment 1)."""
    return (units.para_idx <= share * units.attrs["n_paragraphs"]).to_numpy()


def deletion_mask(units, rate, pattern, seed, base_share=config.DELETE_BASE_PREFIX):
    """Hide about `rate` of the words of the `base_share` prefix (Experiment 2).

    scattered:  sentences drawn in random order until the hidden words reach the target;
    continuous: a random window of target words; sentences whose middle word falls inside are hidden.
    """
    base = prefix_mask(units, base_share)
    idx = np.flatnonzero(base)
    words = units.n_words.to_numpy()[idx]
    target = rate * words.sum()
    rng = np.random.default_rng([config.SEED, seed, int(rate * 1000), pattern == "continuous"])
    hide = np.zeros(len(idx), bool)
    if pattern == "scattered":
        removed = 0
        for j in rng.permutation(len(idx)):
            if removed >= target:
                break
            hide[j] = True
            removed += words[j]
    elif pattern == "continuous":
        offs = np.cumsum(words) - words          # word offset of each unit inside the prefix
        start = rng.uniform(0, words.sum() - target)
        mid = offs + words / 2
        hide = (mid >= start) & (mid < start + target)
    else:
        raise ValueError(pattern)
    mask = base.copy()
    mask[idx[hide]] = False
    return mask


def hidden_word_share(units, mask, base_share=config.DELETE_BASE_PREFIX):
    """Realised share of base-prefix words hidden by `mask` (for auditing the deletion)."""
    base = prefix_mask(units, base_share)
    w = units.n_words.to_numpy()
    return 1 - w[base & mask].sum() / w[base].sum()
