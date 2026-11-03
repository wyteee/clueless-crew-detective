"""Ranking model, baselines, cross-validation and metrics.

Model: L2-regularised logistic regression over candidate rows (principal culprit = 1, other roster
characters = 0). Features are z-scored within each story first, so the model compares characters of
the same story rather than long vs. short stories. Candidates are ranked by predicted probability.

Training (README design): train on the unmasked full pre-reveal text, test on masked text.
Training rows exclude accomplices (neither clearly positive nor negative) and stories whose principal
culprit is never named before the reveal (no positive row). Both stay in the test rankings.

Scoring is against the principal culprit:
- Top-1 and reciprocal rank, with ties broken at random in expectation (a culprit tied with k-1
  others at rank r gets Top-1 = 1/k if r = 1, and RR = mean of 1/r..1/(r+k-1)).
- If the culprit has no mention in the visible text it counts as a failure (Top-1 = RR = 0) for
  every method, including the random baseline (README: absent culprit = failure).
"""
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from src import config
from src.features import GROUPS

GROUP_LETTER = {"visibility": "V", "interaction": "I", "crime": "C"}
COMBOS = {"+".join(GROUP_LETTER[g] for g in combo): [c for g in combo for c in GROUPS[g]]
          for k in (1, 2, 3) for combo in combinations(GROUPS, k)}          # 7 combinations
BASELINES = ["random", "mention_freq"]
ALL_COLS = [c for cols in GROUPS.values() for c in cols]


def within_story_z(df, cols=ALL_COLS):
    """Standardise feature columns within each (condition, story); constant columns become 0."""
    keys = [k for k in ("condition", "story_id") if k in df.columns]
    g = df.groupby(keys)[cols]
    sd = g.transform("std", ddof=0)
    out = df.copy()
    out[cols] = ((df[cols] - g.transform("mean")) / sd.where(sd > 0)).fillna(0.0)
    return out


def culprit_rank_metrics(scores, is_culprit, culprit_visible=True):
    """(top1, rr) for one story's ranking with expected random tie-breaking."""
    if not culprit_visible:
        return 0.0, 0.0
    scores, is_culprit = np.asarray(scores, float), np.asarray(is_culprit, bool)
    s = scores[is_culprit][0]
    higher = int((scores > s).sum())
    ties = int((scores == s).sum())                    # includes the culprit
    ranks = np.arange(higher + 1, higher + ties + 1)
    return (1.0 / ties if higher == 0 else 0.0), float(np.mean(1.0 / ranks))


def training_rows(df):
    named = (df.is_culprit * df.n_mentions).groupby(df.story_id).sum() > 0
    keep = df.story_id.isin(named[named].index) & (df.is_accomplice == 0)
    return df[keep]


def fit(df, cols, C):
    tr = training_rows(df)
    model = LogisticRegression(C=C, class_weight="balanced", max_iter=5000)
    return model.fit(tr[cols].to_numpy(), tr.is_culprit.to_numpy())


def score_stories(df, scores, method):
    """Per-story Top-1 / RR rows for one condition's test rows and their scores."""
    rows = []
    d = df.assign(_s=scores)
    for sid, g in d.groupby("story_id", sort=False):
        visible = bool((g.is_culprit * g.n_mentions).sum() > 0)
        top1, rr = culprit_rank_metrics(g._s, g.is_culprit, visible)
        rows.append({"story_id": sid, "method": method, "top1": top1, "rr": rr,
                     "n_candidates": len(g), "culprit_visible": visible})
    return rows


def random_baseline_rows(df):
    rows = []
    for sid, g in df.groupby("story_id", sort=False):
        n = len(g)
        visible = bool((g.is_culprit * g.n_mentions).sum() > 0)
        rows.append({"story_id": sid, "method": "random",
                     "top1": 1 / n if visible else 0.0,
                     "rr": float(np.mean(1 / np.arange(1, n + 1))) if visible else 0.0,
                     "n_candidates": n, "culprit_visible": visible})
    return rows


def mean_rr(df, cols, C, folds):
    """Inner-CV MRR for choosing C."""
    rr = []
    for tr, te in folds:
        m = fit(df[df.story_id.isin(tr)], cols, C)
        test = df[df.story_id.isin(te)]
        rr += [r["rr"] for r in score_stories(test, m.predict_proba(test[cols].to_numpy())[:, 1], "")]
    return float(np.mean(rr))


def story_folds(story_ids, n_splits, seed):
    """[(train_ids, test_ids)] from GroupKFold with each story as its own group."""
    ids = np.array(sorted(story_ids))
    gkf = GroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return [(ids[tr], ids[te]) for tr, te in gkf.split(ids, groups=ids)]


def choose_C(train_df, cols, seed):
    sids = train_df.story_id.unique()
    inner = story_folds(sids, min(config.INNER_FOLDS, len(sids)), seed)
    scores = {C: mean_rr(train_df, cols, C, inner) for C in config.C_GRID}
    return max(scores, key=lambda C: (scores[C], -C))  # ties -> stronger regularisation


def cross_validate(train_feats, test_feats):
    """Outer 5-fold GroupKFold by story.

    train_feats: rows for the unmasked condition (one per story x character), z-scored.
    test_feats:  rows for all test conditions (column `condition`), z-scored.
    Returns (per-story results DataFrame, chosen-C log DataFrame).
    """
    folds = story_folds(train_feats.story_id.unique(), config.N_FOLDS, config.SEED)
    results, c_log = [], []
    for k, (tr_ids, te_ids) in enumerate(folds):
        train = train_feats[train_feats.story_id.isin(tr_ids)]
        test = test_feats[test_feats.story_id.isin(te_ids)]
        for name, cols in COMBOS.items():
            C = choose_C(train, cols, config.SEED + k + 1)
            c_log.append({"fold": k, "combo": name, "C": C})
            model = fit(train, cols, C)
            for cond, g in test.groupby("condition", sort=False):
                p = model.predict_proba(g[cols].to_numpy())[:, 1]
                results += [r | {"condition": cond, "fold": k} for r in score_stories(g, p, name)]
        for cond, g in test.groupby("condition", sort=False):
            results += [r | {"condition": cond, "fold": k}
                        for r in score_stories(g, g.n_mentions.to_numpy(), "mention_freq")]
            results += [r | {"condition": cond, "fold": k} for r in random_baseline_rows(g)]
    return pd.DataFrame(results), pd.DataFrame(c_log)


# ---------------------------------------------------------------------------
# Aggregation: story-level bootstrap

def bootstrap_ci(values, seed, n=config.N_BOOTSTRAP, alpha=0.05):
    v = np.asarray(values, float)
    rng = np.random.default_rng(seed)
    means = v[rng.integers(0, len(v), size=(n, len(v)))].mean(axis=1)
    return float(v.mean()), float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def summarise(story_df, by):
    """Mean Top-1 / MRR with 95% story-bootstrap CIs. `story_df` has one row per story per group."""
    rows = []
    for key, g in story_df.groupby(by, sort=False):
        key = key if isinstance(key, tuple) else (key,)
        t, tlo, thi = bootstrap_ci(g.top1, config.SEED)
        m, mlo, mhi = bootstrap_ci(g.rr, config.SEED)
        rows.append(dict(zip(by, key)) | {"n_stories": len(g), "top1": t, "top1_lo": tlo, "top1_hi": thi,
                                          "mrr": m, "mrr_lo": mlo, "mrr_hi": mhi,
                                          "culprit_visible": g.culprit_visible.mean()})
    return pd.DataFrame(rows)


def paired_diff(a, b, metric, seed=config.SEED):
    """Mean of (a - b) over stories present in both, with a 95% bootstrap CI and a sign count."""
    m = a.set_index("story_id")[metric].to_frame("a").join(b.set_index("story_id")[metric].to_frame("b"), how="inner")
    d = m.a - m.b
    mean, lo, hi = bootstrap_ci(d, seed)
    return {"n_stories": len(d), "diff": mean, "diff_lo": lo, "diff_hi": hi,
            "a_better": int((d > 0).sum()), "b_better": int((d < 0).sum()), "ties": int((d == 0).sum())}
