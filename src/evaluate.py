"""Ranking models, baselines, cross-validation and metrics (v2, docs/03_revision_plan.md).

One example = one (story, roster node) pair; label 1 for every node of the principal culprit (real name
or a pseudonym persona), 0 otherwise. Rows of one story are dependent; the story is the unit of
cross-validation and of bootstrap resampling. Features are z-scored within each (condition, story).

Models (R5)
- "clogit": penalised conditional logit. P(c | s) = softmax_{k in story s}(beta . x_k), no intercept
  (it cancels within a story). Objective: C * sum_s -log sum_{c in principal nodes} P(c | s)
  + 0.5 * ||beta||^2, minimised with L-BFGS. Every story contributes one term, whatever its roster size.
- "logreg": L2 logistic regression on independent rows, class_weight="balanced" (v1 model, comparison).
Training rows exclude accomplice nodes and stories without a principal node mentioned in the training
text (no positive row); both stay in the test rankings.

Cross-validation (R6): leave-one-story-out, C fixed in config; `c_sensitivity` reruns the full-text
condition for every C in config.C_GRID.

Scoring against the principal culprit (R3, R8)
- The story's culprit score is the best score among principal nodes with a visible mention. Rank =
  1 + number of non-principal nodes scored higher; ties broken at random in expectation.
- If no principal node is mentioned in the visible text, Top-1 = RR = 0 for every method, including
  the random baseline (absent culprit = failure).
- failure_type: "hit" (ranked first alone), "tied_first", "ranking_error" (visible, not first),
  "not_visible" (no visible principal mention). Top-1 = coverage x Top-1 | visible.
"""
from itertools import combinations
from math import comb

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import logsumexp
from sklearn.linear_model import LogisticRegression

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


# ---------------------------------------------------------------------------
# Models

class ConditionalLogit:
    """Penalised conditional logit with possibly several positive rows per group."""

    def __init__(self, C=1.0):
        self.C = C

    def fit(self, X, y, groups):
        X, y, groups = np.asarray(X, float), np.asarray(y, bool), np.asarray(groups)
        blocks = [(X[groups == g], y[groups == g]) for g in pd.unique(groups)]
        blocks = [(Xg, yg) for Xg, yg in blocks if yg.any() and len(yg) > 1]

        def objective(beta):
            f, grad = 0.5 * beta @ beta, beta.copy()
            for Xg, yg in blocks:
                s = Xg @ beta
                p = np.exp(s - logsumexp(s))                 # softmax over the story
                q = np.exp(s[yg] - logsumexp(s[yg]))          # softmax over its principal nodes
                f += self.C * (logsumexp(s) - logsumexp(s[yg]))
                grad += self.C * (p @ Xg - q @ Xg[yg])
            return f, grad

        res = minimize(objective, np.zeros(X.shape[1]), jac=True, method="L-BFGS-B")
        self.coef_, self.converged_ = res.x, res.success
        return self

    def decision_function(self, X):
        return np.asarray(X, float) @ self.coef_


def training_rows(df):
    """Training rows: drop accomplice nodes and stories with no mentioned principal node."""
    named = (df.is_culprit * df.n_mentions).groupby(df.story_id).sum() > 0
    keep = df.story_id.isin(named[named].index) & (df.is_accomplice == 0)
    return df[keep]


def fit(df, cols, C, model):
    tr = training_rows(df)
    X, y = tr[cols].to_numpy(), tr.is_culprit.to_numpy()
    if model == "clogit":
        return ConditionalLogit(C).fit(X, y, tr.story_id.to_numpy())
    if model == "logreg":
        return LogisticRegression(C=C, class_weight="balanced", max_iter=5000).fit(X, y)
    raise ValueError(model)


def predict(m, X):
    return m.decision_function(X)        # monotone in the probability for both models


# ---------------------------------------------------------------------------
# Scoring

def culprit_rank_metrics(scores, is_culprit, visible_culprit):
    """(top1, rr, failure_type) for one story's ranking.

    `visible_culprit`: boolean per row, principal node with a visible mention.
    """
    scores = np.asarray(scores, float)
    is_culprit, visible_culprit = np.asarray(is_culprit, bool), np.asarray(visible_culprit, bool)
    if not visible_culprit.any():
        return 0.0, 0.0, "not_visible"
    s = scores[visible_culprit].max()
    others = scores[~is_culprit]
    higher = int((others > s).sum())
    ties = int((others == s).sum()) + 1
    ranks = np.arange(higher + 1, higher + ties + 1)
    top1 = 1.0 / ties if higher == 0 else 0.0
    kind = "hit" if top1 == 1.0 else ("tied_first" if higher == 0 else "ranking_error")
    return top1, float(np.mean(1.0 / ranks)), kind


def _story_rows(g, scores, method):
    visible = (g.is_culprit == 1) & (g.n_mentions > 0)
    top1, rr, kind = culprit_rank_metrics(scores, g.is_culprit == 1, visible)
    return {"story_id": g.story_id.iloc[0], "method": method, "top1": top1, "rr": rr,
            "failure_type": kind, "culprit_visible": bool(visible.any()), "n_candidates": len(g)}


def score_stories(df, scores, method):
    d = df.assign(_s=np.asarray(scores, float))
    return [_story_rows(g, g._s.to_numpy(), method) for _, g in d.groupby("story_id", sort=False)]


def random_baseline_rows(df):
    """Expected Top-1 / RR of a uniformly random ranking (best of the k principal nodes)."""
    rows = []
    for sid, g in df.groupby("story_id", sort=False):
        # rank among non-principal nodes and the visible principal nodes (as for the models)
        vis_nodes = (g.is_culprit == 1) & (g.n_mentions > 0)
        k = int(vis_nodes.sum())
        n = int((g.is_culprit == 0).sum()) + k
        visible = k > 0
        # P(best principal node at rank r) = C(n - r, k - 1) / C(n, k)
        rr = sum(comb(n - r, k - 1) / comb(n, k) / r for r in range(1, n - k + 2)) if visible else 0.0
        rows.append({"story_id": sid, "method": "random",
                     "top1": k / n if visible else 0.0, "rr": rr,
                     "failure_type": "random" if visible else "not_visible",
                     "culprit_visible": visible, "n_candidates": len(g)})
    return rows


# ---------------------------------------------------------------------------
# Leave-one-story-out cross-validation

def cross_validate(train_feats, test_feats, C=config.C_FIXED, models=config.MODELS, combos=COMBOS,
                   baselines=True):
    """LOSO: for every story, fit on the other stories' unmasked rows and score all its test conditions.

    train_feats: z-scored rows of the unmasked condition; test_feats: z-scored rows of all conditions
    (column `condition`). Returns one row per story x condition x method.
    """
    results = []
    tests = dict(tuple(test_feats.groupby("story_id", sort=False)))
    for sid in sorted(train_feats.story_id.unique()):
        train = train_feats[train_feats.story_id != sid]
        test = tests[sid]
        for model in models:
            for name, cols in combos.items():
                m = fit(train, cols, C, model)
                for cond, g in test.groupby("condition", sort=False):
                    results += [r | {"condition": cond, "model": model}
                                for r in score_stories(g, predict(m, g[cols].to_numpy()), name)]
        if baselines:
            for cond, g in test.groupby("condition", sort=False):
                results += [r | {"condition": cond, "model": "baseline"}
                            for r in score_stories(g, g.n_mentions.to_numpy(), "mention_freq")]
                results += [r | {"condition": cond, "model": "baseline"} for r in random_baseline_rows(g)]
    return pd.DataFrame(results)


def c_sensitivity(train_feats):
    """Full-text LOSO results for every C in the grid (both models, all combinations)."""
    out = []
    for C in config.C_GRID:
        r = cross_validate(train_feats, train_feats, C=C, baselines=False)
        out.append(r.assign(C=C))
    return pd.concat(out, ignore_index=True)


# ---------------------------------------------------------------------------
# Aggregation: story-level bootstrap

def bootstrap_ci(values, seed, n=config.N_BOOTSTRAP, alpha=0.05):
    v = np.asarray(values, float)
    if len(v) == 0:
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(seed)
    means = v[rng.integers(0, len(v), size=(n, len(v)))].mean(axis=1)
    return float(v.mean()), float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def summarise(story_df, by):
    """Mean Top-1 / MRR with 95% story-bootstrap CIs, plus coverage and metrics conditional on a
    visible culprit (Top-1 = coverage x top1_given_visible). One row per story per group expected."""
    rows = []
    for key, g in story_df.groupby(by, sort=False):
        key = key if isinstance(key, tuple) else (key,)
        t, tlo, thi = bootstrap_ci(g.top1, config.SEED)
        m, mlo, mhi = bootstrap_ci(g.rr, config.SEED)
        # culprit_visible may be a seed-averaged fraction; Top-1 and RR are 0 when not visible, so
        # mean(top1) = coverage * E[top1 | visible] holds exactly with these ratios.
        cov = float(g.culprit_visible.astype(float).mean())
        rows.append(dict(zip(by, key)) | {
            "n_stories": len(g), "top1": t, "top1_lo": tlo, "top1_hi": thi,
            "mrr": m, "mrr_lo": mlo, "mrr_hi": mhi,
            "coverage": cov, "n_visible": float(g.culprit_visible.astype(float).sum()),
            "top1_given_visible": t / cov if cov else np.nan,
            "mrr_given_visible": m / cov if cov else np.nan})
    return pd.DataFrame(rows)


def paired_diff(a, b, metric, seed=config.SEED):
    """Mean of (a - b) over stories present in both, with a 95% bootstrap CI and a sign count."""
    m = a.set_index("story_id")[metric].to_frame("a").join(b.set_index("story_id")[metric].to_frame("b"), how="inner")
    d = m.a - m.b
    mean, lo, hi = bootstrap_ci(d, seed)
    return {"n_stories": len(d), "diff": mean, "diff_lo": lo, "diff_hi": hi,
            "a_better": int((d > 0).sum()), "b_better": int((d < 0).sum()), "ties": int((d == 0).sum())}
