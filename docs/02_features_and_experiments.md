# Step 2–3: Features, prediction and masking experiments (W5–W10)

Run everything: `python -m src.experiments` (about 1 min; `--quick` uses 2 deletion seeds).
Tables go to `outputs/results/`, figures to `outputs/figures/`. All seeds are in `src/config.py`.

## Code
| File | Role |
|---|---|
| `src/config.py` | seeds, C grid, prefix shares, deletion rates/patterns, crime window |
| `src/masking.py` | sentence units inside the fixed paragraphs; `prefix_mask`, `deletion_mask` |
| `src/features.py` | frozen interface `get_features(story_id, text_mask=None)`; three feature groups |
| `src/evaluate.py` | 7 combinations, 2 baselines, GroupKFold CV, Top-1/MRR, bootstrap CIs, paired diffs |
| `src/experiments.py` | builds all conditions, runs CV, writes tables and figures |

## Design decisions (please review)
1. **Roster** = the characters of the manifest alias table (all merges, guideline v0.3), fixed per story. A masked text can leave a character with 0 mentions; it stays a candidate (CLAUDE.md rule 6). A prefix-only-merge roster (`aliases.prefix_only_aliases`) is not yet a run option.
2. **Mentions** = exact alias forms, longest first, non-overlapping ("Miss Turner" claims its "Turner").
3. **Features**, z-scored within each story before the model:
   - visibility: log mentions, mention share, relative first-mention position, paragraph coverage;
   - interaction: degree centrality, strength share, weighted PageRank of the roster co-occurrence network (same paragraph);
   - crime: crime-term tokens within ±15 words of any mention (union per character): log count, share, per-mention rate. The stem list in `features.py` was audited against the corpus to avoid hits like Robert, forget, stable, accustomed.
4. **Model**: L2 logistic regression, `class_weight="balanced"`, C from {0.01, 0.1, 1, 10} by inner 3-fold GroupKFold on the training stories (MRR).
5. **Training rows**: principal culprit = 1, others = 0; accomplices left out of training (kept as test candidates); stories whose principal is never named before the reveal (M26, R07, R12, R23) left out of training.
6. **Train unmasked, test masked**: one model per fold and combination, trained on the full pre-reveal text, applied to every condition.
7. **Prefixes** are shares of all story paragraphs (README), not of the pre-reveal text as on the proposal slide. The full pre-reveal text is reported as a reference point.
8. **Deletion** works on sentence units of the 80% prefix: scattered = random sentences until the target share of words is hidden; continuous = one random window of target words (sentences whose middle word falls inside). Realised shares are in `mask_audit.csv` (within ±1.5 points of the target). 10 seeds per story; each story is averaged over seeds before the bootstrap.
9. **Scoring** against the principal culprit, expected Top-1/RR under random tie-breaking. A culprit with no visible mention is a failure for every method, including random.

## First results (30 eligible stories, 5-fold GroupKFold)
Produced by `python -m src.experiments` on commit of this doc; see `outputs/results/` for CIs.

- Full pre-reveal text, MRR: I+C 0.48, V+I 0.45, I 0.43, mention_freq 0.42, V+I+C 0.41, V 0.38, random 0.37, V+C 0.37, C 0.33. All 95% CIs overlap widely (about ±0.11).
- Only 26/30 culprits are named before the reveal, so 0.867 is the ceiling on Top-1 and MRR.
- Experiment 1: MRR rises with the visible share for nearly all methods (V+I+C 0.25 → 0.40 from 20% to 80%), largely because culprit coverage rises (53% of culprits are named in the 20% prefix, 83% in the 80%).
- Experiment 2: no clear difference between scattered and continuous deletion; paired CIs include 0 for every method and rate except one (I at 20%, +0.025, CI 0.003–0.048), which is likely chance given 27 comparisons.
- Fitted on all stories, crime-language coefficients are negative and interaction coefficients are the largest positive ones.

## Open points
- The proposal slide names a TF-IDF candidate-text model as the main model; the README names the 7 feature combinations. Only the latter is implemented.
- Exp 2 uses one base prefix (80%); the proposal slide speaks of 20% removal of the pre-reveal text.
- C selection is unstable across folds (small training sets); a fixed C would be a simpler, defensible alternative.
