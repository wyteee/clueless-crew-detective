"""Rule-based alias merging and its evaluation against the hand-built alias tables.

Only text before the reveal paragraph is used (CLAUDE.md rule 5).

Pipeline:
1. extract_mentions: spaCy PERSON entities in the prefix, plus "<title> <Capitalised>" patterns
   spaCy misses; a title directly before an entity is kept as part of the mention. A second pass
   adds bare occurrences of first names / surnames already seen in a fuller name (e.g. "Ryder"
   once "James Ryder" is known), unless they are part of a longer capitalised phrase.
2. merge_aliases: union surface forms into characters with three rules
   (title + surname, surname only, full-name containment), blocked by title-class conflicts
   (Mr./Dr. vs Mrs. vs Miss) and by different first names. When a form fits several
   characters, one sharing its first name (then its title class) wins; otherwise it is left
   unlinked rather than guessed. A bare surname is not attached to a character known only
   as Mrs./Miss (period convention: women are rarely called by surname alone).
3. evaluate_story: pairwise precision/recall over the gold alias forms that occur on their own
   in the prefix (a form seen only inside a longer gold form, e.g. "Windibank" inside
   "Mr. Windibank", cannot be a separate mention and is not scored).
"""
import json
import re
from itertools import combinations
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# Title classes: titles in different classes never refer to the same person.
TITLE_CLASS = {}
for _cls, _titles in {
    "male": ["Mr", "Sir", "Lord", "Dr", "Doctor", "Colonel", "Col", "Captain", "Capt", "Major",
             "General", "Inspector", "Sergeant", "Professor", "Prof", "Father", "Rev", "Reverend",
             "Count", "Baron", "Monsieur", "Signor", "Herr", "Master"],
    "mrs": ["Mrs", "Lady", "Madame", "Mme", "Countess", "Duchess", "Baroness"],
    "miss": ["Miss", "Mademoiselle", "Mlle"],
}.items():
    for _t in _titles:
        TITLE_CLASS[_t.lower()] = _cls

_TITLE_RE = "|".join(sorted({t.capitalize() for t in TITLE_CLASS}, key=len, reverse=True))
TITLE_NAME_RE = re.compile(
    rf"\b(?:{_TITLE_RE})\.?(?:\s+[A-Z][\w’'\-]*)+")


def read_paragraphs(story_id):
    """Return [(para_idx, text)] from data/processed/<story_id>.txt."""
    out = []
    for line in (ROOT / "data" / "processed" / f"{story_id}.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\[(\d{4})\] (.*)$", line)
        if m:
            out.append((int(m.group(1)), m.group(2)))
    return out


def prefix_paragraphs(story_id, reveal_para_idx):
    """Paragraphs strictly before the reveal paragraph."""
    return [(i, t) for i, t in read_paragraphs(story_id) if i < reveal_para_idx]


def _clean(surface):
    s = re.sub(r"\s+", " ", surface).strip(" ,.;:!?“”‘’\"'()—-_")
    s = re.sub(r"(’s|'s)$", "", s)
    return s


def _overlaps(a, b, spans):
    return any(x < b and a < y for x, y in spans)


def extract_mentions(paragraphs, nlp):
    """Return a DataFrame of name mentions: para_idx, surface."""
    rows, all_spans = [], {}
    for idx, text in paragraphs:
        # all-caps lines (letters, signatures) are also run title-cased; offsets are unchanged
        docs = [nlp(text)] + ([nlp(text.title())] if text.isupper() else [])
        spans = []
        for doc in docs:
            for ent in doc.ents:
                if ent.label_ != "PERSON":
                    continue
                start = ent.start
                if start > 0 and doc[start - 1].text.rstrip(".").lower() in TITLE_CLASS:
                    start -= 1
                if not _overlaps(doc[start].idx, ent.end_char, spans):
                    spans.append((doc[start].idx, ent.end_char))
        for m in TITLE_NAME_RE.finditer(text):
            # keep regex hits that do not overlap a spaCy span
            if not _overlaps(m.start(), m.end(), spans):
                spans.append((m.start(), m.end()))
        all_spans[idx] = spans
        for a, b in spans:
            s = _clean(text[a:b])
            if s and any(c.isalpha() for c in s):
                rows.append({"para_idx": idx, "surface": s})

    # Second pass: bare first names / surnames taken from fuller names already found
    known = set()
    for s in {r["surface"] for r in rows}:
        title, given, surname = parse_name(s)
        if surname and (given or title):
            known.update(t for t in s.split() if t.strip(".").lower() not in TITLE_CLASS)
    known = {t for t in known if re.fullmatch(r"[A-Z][\w’'\-]+", t)}
    if known:
        names = "|".join(map(re.escape, sorted(known, key=len, reverse=True)))
        for idx, text in paragraphs:
            caps = text.isupper()
            pat = re.compile(r"(?<![\w’'\-])(?:([A-Z][\w’'\-]+)\s+)?(" + names + r")(?![\w\-])",
                             re.IGNORECASE if caps else 0)
            for m in pat.finditer(text):
                a, b = m.span()
                if _overlaps(a, b, all_spans[idx]) or re.match(r"\s[A-Z]", text[b:b + 2]):
                    continue  # already found, or part of a longer phrase, e.g. "Baker Street"
                if m.group(1):
                    # "<Capitalised> <known name>": a full name unless the first word is a title or
                    # just a capitalised sentence opener ("Then Holmes")
                    first = m.group(1).strip(".").lower()
                    opener = re.search(r"(^|[.!?“\"‘]\s*)$", text[:a]) and not caps
                    if first in TITLE_CLASS or opener:
                        a = m.start(2)
                        if _overlaps(a, b, all_spans[idx]):
                            continue
                elif re.search(r"[A-Z][\w’'\-]*\.?\s$", text[:a]):
                    continue
                rows.append({"para_idx": idx, "surface": _clean(text[a:b])})
    return pd.DataFrame(rows, columns=["para_idx", "surface"])


def parse_name(surface):
    """Split a surface form into (title_class, given_tokens, surname) in lower case."""
    toks = [t.strip(".").lower() for t in surface.split()]
    title = None
    while toks and toks[0] in TITLE_CLASS:
        title = title or TITLE_CLASS[toks[0]]
        toks = toks[1:]
    if not toks:
        return title, [], None
    return title, toks[:-1], toks[-1]


class _Cluster:
    def __init__(self, surface):
        title, given, surname = parse_name(surface)
        self.surfaces = {surface}
        self.titles = {title} if title else set()
        self.given = {given[0]} if given else set()
        self.surnames = {surname} if surname else set()

    def compatible(self, other):
        if len(self.titles | other.titles) > 1:
            return False
        if len(self.given | other.given) > 1:
            return False
        return True

    def absorb(self, other):
        self.surfaces |= other.surfaces
        self.titles |= other.titles
        self.given |= other.given
        self.surnames |= other.surnames


def merge_aliases(surfaces):
    """Group surface forms into characters. Returns {surface: cluster_id}."""
    surfaces = sorted(set(surfaces), key=lambda s: (-len(s.split()), s))
    clusters = []

    def pick(targets, given, title):
        """One target, or the single target sharing the first name, then the title class."""
        if len(targets) == 1:
            return targets[0]
        for key in ([c for c in targets if given and given in c.given],
                    [c for c in targets if title and title in c.titles]):
            if len(key) == 1:
                return key[0]
        return None

    # Pass 1: forms with a surname anchor (two or more name tokens, or title + name)
    single = []
    for s in surfaces:
        title, given, surname = parse_name(s)
        if surname is None:
            continue
        if not given and not title:
            single.append(s)
            continue
        new = _Cluster(s)
        # full-name containment / title + surname: same surname and compatible
        targets = [c for c in clusters if surname in c.surnames and c.compatible(new)]
        target = pick(targets, given[0] if given else None, title)
        if target:
            target.absorb(new)
        else:
            clusters.append(new)

    # Pass 2: bare single names attach to the one cluster they fit (as surname or first name)
    for s in single:
        tok = s.lower()
        female_only = lambda c: c.titles and c.titles <= {"mrs", "miss"}
        targets = [c for c in clusters
                   if (tok in c.surnames and not female_only(c)) or tok in c.given]
        if len(targets) == 1:
            targets[0].surfaces.add(s)
        else:
            clusters.append(_Cluster(s))

    return {s: i for i, c in enumerate(clusters) for s in c.surfaces}


def standalone_forms(gold_aliases, paragraphs):
    """Gold forms that occur at least once in the prefix outside a longer gold form."""
    forms = sorted({f for fs in gold_aliases.values() for f in fs}, key=len, reverse=True)
    found = set()
    for _, text in paragraphs:
        taken = []
        for f in forms:  # longest first, so "Mr. Windibank" claims its "Windibank"
            for m in re.finditer(rf"(?<![\w\-]){re.escape(f)}(?![\w\-])", text):
                if not any(x <= m.start() and m.end() <= y for x, y in taken):
                    found.add(f)
                taken.append(m.span())
    return found


def evaluate_story(gold_aliases, pred_cluster, paragraphs, story_links=None):
    """Pairwise precision/recall over the scorable gold forms (case-insensitive).

    Scorable = occurs on its own in the prefix (see standalone_forms). A scorable form that was
    never extracted counts as its own singleton cluster, so extraction misses lower recall.
    Pairs involving names outside the gold table are not scored.
    Missed pairs are split by cause: a form was never extracted (fn_not_extracted), the pair
    crosses a pseudonym/misnaming link from alias_links.csv (fn_link), or both forms were
    extracted but the rules kept them apart (fn_rules).
    """
    link_group = {}
    if story_links is not None:
        for i, l in enumerate(story_links.sort_values("link_para_idx").itertuples()):
            for f in l.forms:
                link_group.setdefault(f.lower(), i)
    scorable = standalone_forms(gold_aliases, paragraphs)
    gold = {}
    for char, forms in gold_aliases.items():
        for f in forms:
            if f in scorable:
                gold[f.lower()] = char
    pred = {}
    for s, cid in pred_cluster.items():
        pred.setdefault(s.lower(), cid)
    forms = sorted(gold)
    lab = {f: pred.get(f, ("missing", f)) for f in forms}
    tp = fp = fn = 0
    causes = {"fn_not_extracted": 0, "fn_link": 0, "fn_rules": 0}
    for a, b in combinations(forms, 2):
        same_gold, same_pred = gold[a] == gold[b], lab[a] == lab[b]
        tp += same_gold and same_pred
        fp += (not same_gold) and same_pred
        if same_gold and not same_pred:
            fn += 1
            if link_group.get(a) != link_group.get(b):
                causes["fn_link"] += 1
            elif a not in pred or b not in pred:
                causes["fn_not_extracted"] += 1
            else:
                causes["fn_rules"] += 1
    return {
        "gold_forms": sum(len(fs) for fs in gold_aliases.values()),
        "scorable": len(forms),
        "extracted": sum(f in pred for f in forms),
        "precision": tp / (tp + fp) if tp + fp else float("nan"),
        "recall": tp / (tp + fn) if tp + fn else float("nan"),
        "tp": tp, "fp": fp, "fn": fn, **causes,
    }


def culprit_check(gold_aliases, principal, pred_cluster):
    """For the principal culprit: which gold forms land in the same predicted cluster."""
    pred = {s.lower(): cid for s, cid in pred_cluster.items()}
    forms = [f.lower() for f in gold_aliases.get(principal, [])]
    ids = [pred.get(f) for f in forms if f in pred]
    if not ids:
        return {"main_cluster_share": 0.0, "missed": forms}
    main = max(set(ids), key=ids.count)
    missed = [f for f in forms if pred.get(f) != main]
    return {"main_cluster_share": (len(forms) - len(missed)) / len(forms), "missed": missed}


def run_pilot(nlp, story_ids=("P1", "P2", "P3", "P4", "P5")):
    """Return (summary DataFrame, {story_id: details})."""
    manifest = pd.read_csv(ROOT / "manifest" / "pilot.csv")
    links = load_alias_links()
    rows, details = [], {}
    for sid in story_ids:
        r = manifest.set_index("story_id").loc[sid]
        gold = json.loads(r.aliases)
        principal = r.culprit.split("; ")[0]
        paragraphs = prefix_paragraphs(sid, int(r.reveal_para_idx))
        mentions = extract_mentions(paragraphs, nlp)
        pred = merge_aliases(mentions.surface)
        res = evaluate_story(gold, pred, paragraphs, links[links.story_id == sid])
        scorable = standalone_forms(gold, paragraphs)
        cc = culprit_check({c: [f for f in fs if f in scorable] for c, fs in gold.items()}, principal, pred)
        rows.append({"story_id": sid, **res, "culprit_share": cc["main_cluster_share"]})
        details[sid] = {"mentions": mentions, "pred": pred, "gold": gold, "culprit_missed": cc["missed"]}
    return pd.DataFrame(rows), details


# ---------------------------------------------------------------------------
# Merge variants: how much do pseudonym links stated only at/after the reveal matter?

def load_alias_links():
    """manifest/alias_links.csv: forms linked to a character, and the paragraph that states it."""
    links = pd.read_csv(ROOT / "manifest" / "alias_links.csv")
    links["forms"] = links["forms"].map(json.loads)
    return links


def prefix_only_aliases(gold_aliases, story_links, reveal_para_idx):
    """Split off alias groups whose link to the character is stated only at/after the reveal."""
    out = {c: list(fs) for c, fs in gold_aliases.items()}
    for _, l in story_links.iterrows():
        if l.link_para_idx >= reveal_para_idx:
            out[l.character] = [f for f in out[l.character] if f not in l.forms]
            out[f"{l.character} [as {l.forms[0]}]"] = list(l.forms)
    return out


def assign_characters(mentions, rule_pred, gold_aliases=None):
    """Character label per mention: the gold character if the form is in the table, else the rule cluster."""
    gold = {f.lower(): c for c, fs in (gold_aliases or {}).items() for f in fs}
    return mentions.surface.map(lambda s: gold.get(s.lower(), f"rule:{rule_pred[s]}"))


def culprit_visibility(mentions, labels, culprit_label):
    """Prefix mention count, first mention paragraph and mention-frequency rank of one character."""
    counts = labels.value_counts()
    n = int(counts.get(culprit_label, 0))
    first = mentions.para_idx[labels == culprit_label].min() if n else None
    rank = int((counts > n).sum()) + 1 if n else None  # 1 = most mentioned; ties share the best rank
    return {"mentions": n, "first_para": first, "freq_rank": rank, "n_characters": len(counts)}


def compare_merge_variants(nlp, story_ids=("P1", "P2", "P3", "P4", "P5")):
    """Principal culprit's visibility under three rosters: rules only, rules + prefix-only hand
    merges, rules + all hand merges. Also the rule-vs-gold alias scores for both gold variants."""
    manifest = pd.read_csv(ROOT / "manifest" / "pilot.csv").set_index("story_id")
    links = load_alias_links()
    vis_rows, score_rows = [], []
    for sid in story_ids:
        r = manifest.loc[sid]
        reveal = int(r.reveal_para_idx)
        principal = r.culprit.split("; ")[0]
        gold_full = json.loads(r.aliases)
        gold_prefix = prefix_only_aliases(gold_full, links[links.story_id == sid], reveal)
        paragraphs = prefix_paragraphs(sid, reveal)
        mentions = extract_mentions(paragraphs, nlp)
        pred = merge_aliases(mentions.surface)

        # rules only: the culprit is the rule cluster holding most mentions of its prefix-only forms
        rule_labels = assign_characters(mentions, pred)
        own = {f.lower() for f in gold_prefix[principal]}
        hits = rule_labels[mentions.surface.str.lower().isin(own)]
        rule_culprit = hits.value_counts().idxmax() if len(hits) else None
        variants = {
            "rules only": (rule_labels, rule_culprit),
            "rules + prefix-only hand merges": (assign_characters(mentions, pred, gold_prefix), principal),
            "rules + all hand merges": (assign_characters(mentions, pred, gold_full), principal),
        }
        for name, (labels, culprit_label) in variants.items():
            vis_rows.append({"story_id": sid, "roster": name,
                             **culprit_visibility(mentions, labels, culprit_label)})
        for name, gold in (("all hand merges", gold_full), ("prefix-only hand merges", gold_prefix)):
            score_rows.append({"story_id": sid, "gold": name,
                               **evaluate_story(gold, pred, paragraphs, links[links.story_id == sid])})
    return pd.DataFrame(vis_rows), pd.DataFrame(score_rows)
