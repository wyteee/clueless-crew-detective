"""Run the feature/prediction study and both masking experiments; write tables and figures.

Usage:  python -m src.experiments            # all 30 eligible main stories
        python -m src.experiments --quick    # 2 deletion seeds, for a fast check

Outputs (outputs/results/, outputs/figures/):
  story_results.csv      one row per condition x method x story (fold, top1, rr, culprit_visible)
  exp0_full_text.csv     7 feature combinations + 2 baselines on the full pre-reveal text
  exp1_prefix.csv        Experiment 1: 20/40/60/80% prefixes (+ full pre-reveal text as reference)
  exp2_deletion.csv      Experiment 2: scattered vs continuous at 10/20/30% (+ 0% = 80% prefix)
  exp2_paired.csv        scattered - continuous, paired by story, per method and rate
  vs_mention_baseline.csv  each combination - mention_freq, paired by story, per condition
  chosen_C.csv, coefficients.csv, mask_audit.csv
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
from src.evaluate import (ALL_COLS, BASELINES, COMBOS, cross_validate, fit, paired_diff,
                          summarise, within_story_z)
from src.features import eligible_story_ids, get_features, load_story_meta
from src.masking import deletion_mask, hidden_word_share, prefix_mask, story_units

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "results"
FIG = ROOT / "outputs" / "figures"
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
    rows, audit = [], []
    for name, info in conds:
        if info["exp"] == "full":
            mask = None
        elif info["exp"] == "prefix":
            mask = prefix_mask(units, info["share"])
        else:
            mask = deletion_mask(units, info["rate"], info["pattern"], info["seed"])
            audit.append({"story_id": sid, **info, "hidden_share": hidden_word_share(units, mask)})
        if mask is not None:  # guard: no reveal or post-reveal paragraph is ever visible
            assert units.para_idx[mask].max() < load_story_meta(sid)["reveal_para_idx"], (sid, name)
        rows.append(get_features(sid, mask).assign(condition=name))
    return pd.concat(rows), audit


def build_features(story_ids, conds):
    res = Parallel(n_jobs=-1)(delayed(story_features)(sid, conds) for sid in story_ids)
    feats = pd.concat([r[0] for r in res], ignore_index=True)
    audit = pd.DataFrame([a for r in res for a in r[1]])
    return within_story_z(feats), feats, audit


def plot_exp1(t):
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for m in METHOD_ORDER:
        g = t[t.method == m].sort_values("share")
        style = {"lw": 2.4} if m == "V+I+C" else ({"ls": "--", "color": "grey" if m == "random" else "black"}
                                                 if m in BASELINES else {"lw": 1, "alpha": .6})
        ax.plot(g.share * 100, g.mrr, marker="o", ms=3, label=m, **style)
    full = t[(t.method == "V+I+C") & (t.share == 1.0)]
    ax.set_xticks([20, 40, 60, 80, 100], ["20%", "40%", "60%", "80%", "pre-reveal\n(full)"])
    ax.set_xlabel("visible text (share of story paragraphs)")
    ax.set_ylabel("MRR (principal culprit)")
    ax.set_title("Experiment 1: information availability")
    ax.legend(ncol=3, fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "exp1_prefix.png", dpi=160)
    plt.close(fig)


def plot_exp2(t, methods=("V+I+C", "V", "mention_freq")):
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
    fig.suptitle("Experiment 2: same loss, different missingness")
    fig.tight_layout()
    fig.savefig(FIG / "exp2_deletion.png", dpi=160)
    plt.close(fig)


def main(quick=False):
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    seeds = config.MASK_SEEDS[:2] if quick else config.MASK_SEEDS
    conds = conditions(seeds)
    info = pd.DataFrame([{"condition": n, **i} for n, i in conds])
    sids = eligible_story_ids()

    z, raw, audit = build_features(sids, conds)
    audit.to_csv(OUT / "mask_audit.csv", index=False)
    results, c_log = cross_validate(z[z.condition == "full"], z)
    results = results.merge(info, on="condition")
    results.to_csv(OUT / "story_results.csv", index=False)
    c_log.to_csv(OUT / "chosen_C.csv", index=False)

    # Exp 0: feature combinations on the full pre-reveal text
    exp0 = summarise(results[results.condition == "full"], ["method"])
    exp0.sort_values("mrr", ascending=False).to_csv(OUT / "exp0_full_text.csv", index=False)

    # Exp 1: prefixes, with the full pre-reveal text as the right-hand reference
    e1 = summarise(results[results.exp.isin(["prefix", "full"])], ["method", "share"])
    e1.to_csv(OUT / "exp1_prefix.csv", index=False)
    plot_exp1(e1)

    # Exp 2: average each story over deletion seeds first, then bootstrap over stories
    d = results[results.exp == "delete"]
    per_story = d.groupby(["method", "pattern", "rate", "story_id"], as_index=False)[
        ["top1", "rr", "culprit_visible"]].mean()
    base = results[results.condition == "prefix_80"]
    zero = pd.concat([base.assign(pattern=p, rate=0.0) for p in config.DELETE_PATTERNS])
    e2 = summarise(pd.concat([zero[per_story.columns], per_story]), ["method", "pattern", "rate"])
    e2.to_csv(OUT / "exp2_deletion.csv", index=False)
    plot_exp2(e2)

    paired = []
    for m in METHOD_ORDER:
        for r in config.DELETE_RATES:
            s = per_story[(per_story.method == m) & (per_story.rate == r)]
            for metric in ("rr", "top1"):
                paired.append({"method": m, "rate": r, "metric": metric, "a": "scattered", "b": "continuous",
                               **paired_diff(s[s.pattern == "scattered"], s[s.pattern == "continuous"], metric)})
    pd.DataFrame(paired).to_csv(OUT / "exp2_paired.csv", index=False)

    # Each combination vs the mention-frequency baseline (deletion conditions averaged over seeds)
    by_cond = pd.concat([results[results.exp != "delete"][["method", "condition", "story_id", "top1", "rr"]],
                         per_story.assign(condition=lambda x: "delete_" + x.pattern + "_" +
                                          (x.rate * 100).round().astype(int).astype(str))
                         [["method", "condition", "story_id", "top1", "rr"]]])
    vs = []
    for cond, g in by_cond.groupby("condition", sort=False):
        b = g[g.method == "mention_freq"]
        for m in COMBOS:
            vs.append({"condition": cond, "method": m, "metric": "rr",
                       **paired_diff(g[g.method == m], b, "rr")})
    pd.DataFrame(vs).to_csv(OUT / "vs_mention_baseline.csv", index=False)

    # Coefficients of the full model fitted on all stories (for interpretation only, not evaluation)
    C = c_log[c_log.combo == "V+I+C"].C.mode().iloc[0]
    model = fit(z[z.condition == "full"], ALL_COLS, C)
    pd.DataFrame({"feature": ALL_COLS, "coef": model.coef_[0], "C": C}).to_csv(OUT / "coefficients.csv", index=False)

    print(exp0[["method", "top1", "mrr", "mrr_lo", "mrr_hi", "culprit_visible"]].round(3).to_string(index=False))
    print(f"\nwrote {OUT.relative_to(ROOT)}/ and {FIG.relative_to(ROOT)}/")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    main(ap.parse_args().quick)
