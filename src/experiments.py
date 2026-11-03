"""Run the feature/prediction study and both masking experiments; write tables and figures (v2).

Usage:  python -m src.experiments                         # writes outputs/v2/
        python -m src.experiments --quick                 # 2 deletion seeds, for a fast check
        CCD_ALIAS_MODE=full python -m src.experiments --out v2_full_alias   # R2 sensitivity run

Outputs (outputs/<out>/results/, outputs/<out>/figures/):
  story_results.csv        one row per condition x model x method x story (top1, rr, failure_type)
  exp0_full_text.csv       7 combinations x 2 models + 2 baselines on the full pre-reveal text
  exp0_failure_types.csv   counts of hit / tied_first / ranking_error / not_visible (R8)
  exp0_model_comparison.csv  clogit - logreg, paired by story, per combination
  c_sensitivity.csv        full-text results for every C in config.C_GRID (R6)
  exp1_prefix.csv          Experiment 1: 20/40/60/80% prefixes (+ full pre-reveal text as reference)
  prefix_information.csv   per story and prefix: visible words, principal mentions, coverage (R9)
  exp2_deletion.csv        Experiment 2: scattered vs continuous at 10/20/30% (+ 0% = 80% prefix)
  exp2_paired.csv          scattered - continuous, paired by story (main model + baselines)
  vs_mention_baseline.csv  each combination of the main model - mention_freq, paired by story
  coefficients.csv         both models fitted on all stories (descriptive only, not interpreted as effects)
  mask_audit.csv
  figures/exp1_prefix.png, figures/exp2_deletion.png
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from joblib import Parallel, delayed

from src import config
from src.evaluate import (ALL_COLS, BASELINES, COMBOS, c_sensitivity, cross_validate, fit, paired_diff,
                          summarise, within_story_z)
from src.features import eligible_story_ids, get_features, load_story_meta
from src.masking import deletion_mask, full_prefix_mask, hidden_word_share, prefix_mask, story_units

ROOT = Path(__file__).resolve().parents[1]
MAIN = config.MAIN_MODEL
METHOD_ORDER = list(COMBOS) + BASELINES


def conditions(mask_seeds):
    """[(condition, info)] for every test condition."""
    out = [("full", {"exp": "full", "share": 1.0})]
    out += [(f"prefix_{int(p * 100)}", {"exp": "prefix", "share": p}) for p in config.PREFIX_SHARES]
    out += [(f"delete_{pat}_{int(r * 100)}_s{s}", {"exp": "delete", "pattern": pat, "rate": r, "seed": s})
            for pat in config.DELETE_PATTERNS for r in config.DELETE_RATES for s in mask_seeds]
    return out


def story_features(sid, conds):
    units = story_units(sid)
    reveal = load_story_meta(sid)["reveal_para_idx"]
    pre = full_prefix_mask(units, reveal)
    pre_words = int(units.n_words[pre].sum())
    rows, audit, info = [], [], []
    for name, cinfo in conds:
        if cinfo["exp"] == "full":
            mask = None
        elif cinfo["exp"] == "prefix":
            mask = prefix_mask(units, cinfo["share"])
        else:
            mask = deletion_mask(units, cinfo["rate"], cinfo["pattern"], cinfo["seed"])
            audit.append({"story_id": sid, **cinfo, "hidden_share": hidden_word_share(units, mask)})
        if mask is not None:  # guard: no reveal or post-reveal paragraph is ever visible
            assert units.para_idx[mask].max() < reveal, (sid, name)
        f = get_features(sid, mask).assign(condition=name)
        rows.append(f)
        if cinfo["exp"] != "delete":
            vis = pre if mask is None else (mask & pre)
            cul = f[f.is_culprit == 1]
            info.append({"story_id": sid, "condition": name, "share": cinfo["share"],
                         "visible_words": int(units.n_words[vis].sum()),
                         "visible_paragraphs": int(units.para_idx[vis].nunique()),
                         "pre_reveal_words": pre_words,
                         "share_of_pre_reveal_text": units.n_words[vis].sum() / pre_words,
                         "principal_mentions": int(cul.n_mentions.sum()),
                         "principal_visible": bool((cul.n_mentions > 0).any()),
                         "roster_size": len(f), "roster_visible": int((f.n_mentions > 0).sum())})
    return pd.concat(rows), audit, info


def build_features(story_ids, conds):
    res = Parallel(n_jobs=-1)(delayed(story_features)(sid, conds) for sid in story_ids)
    feats = pd.concat([r[0] for r in res], ignore_index=True)
    audit = pd.DataFrame([a for r in res for a in r[1]])
    info = pd.DataFrame([a for r in res for a in r[2]])
    return within_story_z(feats), feats, audit, info


def main_and_baselines(df):
    return df[(df.model == MAIN) | (df.model == "baseline")]


def plot_exp1(t, fig_dir):
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for m in METHOD_ORDER:
        g = t[t.method == m].sort_values("share")
        style = {"lw": 2.4} if m == "V+I+C" else ({"ls": "--", "color": "grey" if m == "random" else "black"}
                                                 if m in BASELINES else {"lw": 1, "alpha": .6})
        ax.plot(g.share * 100, g.mrr, marker="o", ms=3, label=m, **style)
    ax.set_xticks([20, 40, 60, 80, 100], ["20%", "40%", "60%", "80%", "pre-reveal\n(full)"])
    ax.set_xlabel("visible text (share of story paragraphs)")
    ax.set_ylabel("MRR (principal culprit)")
    ax.set_title(f"Experiment 1: prefixes ({MAIN}, LOSO)")
    ax.legend(ncol=3, fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(fig_dir / "exp1_prefix.png", dpi=160)
    plt.close(fig)


def plot_exp2(t, fig_dir, methods=("V+I+C", "V", "mention_freq")):
    fig, axes = plt.subplots(1, len(methods), figsize=(4 * len(methods), 3.6), sharey=True)
    for ax, m in zip(axes, methods):
        for pat, color in (("scattered", "#2a7ab9"), ("continuous", "#d0582c")):
            g = t[(t.method == m) & (t.pattern == pat)].sort_values("rate")
            ax.plot(g.rate * 100, g.mrr, marker="o", color=color, label=pat)
            ax.fill_between(g.rate * 100, g.mrr_lo, g.mrr_hi, color=color, alpha=.12)
        ax.set_title(m)
        ax.set_xlabel("words removed from the 80% prefix (%)")
        ax.set_xticks([0, 10, 20, 30])
    axes[0].set_ylabel("MRR (95% story bootstrap CI)")
    axes[0].legend(frameon=False)
    fig.suptitle(f"Experiment 2: same loss, different missingness ({MAIN}, LOSO)")
    fig.tight_layout()
    fig.savefig(fig_dir / "exp2_deletion.png", dpi=160)
    plt.close(fig)


def main(out="v3", quick=False):
    res_dir, fig_dir = ROOT / "outputs" / out / "results", ROOT / "outputs" / out / "figures"
    res_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    seeds = config.MASK_SEEDS[:2] if quick else config.MASK_SEEDS
    conds = conditions(seeds)
    info = pd.DataFrame([{"condition": n, **i} for n, i in conds])
    sids = eligible_story_ids()

    z, raw, audit, pinfo = build_features(sids, conds)
    audit.to_csv(res_dir / "mask_audit.csv", index=False)
    pinfo.to_csv(res_dir / "prefix_information.csv", index=False)
    train = z[z.condition == "full"]
    results = cross_validate(train, z).merge(info, on="condition")
    results.to_csv(res_dir / "story_results.csv", index=False)

    # Exp 0: full pre-reveal text, both models
    full = results[results.condition == "full"]
    exp0 = summarise(full, ["model", "method"])
    exp0.sort_values(["model", "mrr"], ascending=[True, False]).to_csv(res_dir / "exp0_full_text.csv", index=False)
    (full.groupby(["model", "method", "failure_type"]).size().unstack(fill_value=0).reset_index()
         .to_csv(res_dir / "exp0_failure_types.csv", index=False))
    mc = []
    for m in COMBOS:
        a, b = full[(full.model == "clogit") & (full.method == m)], full[(full.model == "logreg") & (full.method == m)]
        for metric in ("rr", "top1"):
            mc.append({"method": m, "metric": metric, "a": "clogit", "b": "logreg", **paired_diff(a, b, metric)})
    pd.DataFrame(mc).to_csv(res_dir / "exp0_model_comparison.csv", index=False)
    summarise(c_sensitivity(train), ["C", "model", "method"]).to_csv(res_dir / "c_sensitivity.csv", index=False)

    # Exp 1: prefixes, with the full pre-reveal text as the right-hand reference
    e1 = summarise(results[results.exp.isin(["prefix", "full"])], ["model", "method", "share"])
    e1.to_csv(res_dir / "exp1_prefix.csv", index=False)
    plot_exp1(main_and_baselines(e1), fig_dir)

    # Exp 2: average each story over deletion seeds first, then bootstrap over stories
    d = results[results.exp == "delete"].assign(culprit_visible=lambda x: x.culprit_visible.astype(float))
    per_story = d.groupby(["model", "method", "pattern", "rate", "story_id"], as_index=False)[
        ["top1", "rr", "culprit_visible"]].mean()
    base = results[results.condition == "prefix_80"]
    zero = pd.concat([base.assign(pattern=p, rate=0.0) for p in config.DELETE_PATTERNS])
    e2 = summarise(pd.concat([zero[per_story.columns], per_story]), ["model", "method", "pattern", "rate"])
    e2.to_csv(res_dir / "exp2_deletion.csv", index=False)
    plot_exp2(main_and_baselines(e2), fig_dir)

    paired = []
    ps = main_and_baselines(per_story)
    for m in METHOD_ORDER:
        for r in config.DELETE_RATES:
            s = ps[(ps.method == m) & (ps.rate == r)]
            for metric in ("rr", "top1"):
                paired.append({"model": MAIN if m in COMBOS else "baseline", "method": m, "rate": r,
                               "metric": metric, "a": "scattered", "b": "continuous",
                               **paired_diff(s[s.pattern == "scattered"], s[s.pattern == "continuous"], metric)})
    pd.DataFrame(paired).to_csv(res_dir / "exp2_paired.csv", index=False)

    # Each combination of the main model vs the mention-frequency baseline
    by_cond = pd.concat([main_and_baselines(results[results.exp != "delete"])[["method", "condition", "story_id", "rr"]],
                         ps.assign(condition=lambda x: "delete_" + x.pattern + "_" +
                                   (x.rate * 100).round().astype(int).astype(str))
                         [["method", "condition", "story_id", "rr"]]])
    vs = []
    for cond, g in by_cond.groupby("condition", sort=False):
        b = g[g.method == "mention_freq"]
        for m in COMBOS:
            vs.append({"condition": cond, "model": MAIN, "method": m, "metric": "rr",
                       **paired_diff(g[g.method == m], b, "rr")})
    pd.DataFrame(vs).to_csv(res_dir / "vs_mention_baseline.csv", index=False)

    # Coefficients fitted on all stories: descriptive only (docs/03 reporting rules)
    coefs = []
    for model in config.MODELS:
        mdl = fit(train, ALL_COLS, config.C_FIXED, model)
        coefs += [{"model": model, "feature": f, "coef": c, "C": config.C_FIXED}
                  for f, c in zip(ALL_COLS, mdl.coef_.ravel())]
    pd.DataFrame(coefs).to_csv(res_dir / "coefficients.csv", index=False)

    cols = ["model", "method", "top1", "mrr", "mrr_lo", "mrr_hi", "coverage", "mrr_given_visible"]
    print(f"alias mode: {config.ALIAS_MODE}, C = {config.C_FIXED}, LOSO over {len(sids)} stories")
    print(exp0[cols].round(3).to_string(index=False))
    print(f"\nwrote {res_dir.relative_to(ROOT)}/ and {fig_dir.relative_to(ROOT)}/")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="v3")
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    main(a.out, a.quick)
