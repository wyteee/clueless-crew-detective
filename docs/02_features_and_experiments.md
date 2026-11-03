# Step 2–3: Features, prediction and masking experiments (W5–W10)

Run everything: `python -m src.experiments` (about 5 min; `--quick` uses 2 deletion seeds).
Tables go to `outputs/v2/results/`, figures to `outputs/v2/figures/`. All seeds and constants are in `src/config.py`.
Sensitivity run with all alias links merged: `CCD_ALIAS_MODE=full python -m src.experiments --out v2_full_alias`.

This is **v2**, revised after the proposal feedback. Every change from the first run (v1, outputs kept in
`outputs/v1_initial/`) and the formal definitions for the report are in [03_revision_plan.md](03_revision_plan.md).

## Code
| File | Role |
|---|---|
| `src/config.py` | seeds, alias mode, fixed C and grid, models, prefix shares, deletion rates/patterns, crime window |
| `src/masking.py` | sentence units inside the fixed paragraphs; `prefix_mask`, `deletion_mask` |
| `src/features.py` | frozen interface `get_features(story_id, text_mask=None)`; prefix-only alias nodes; three feature groups |
| `src/evaluate.py` | conditional logit + logistic regression, 7 combinations, 2 baselines, LOSO CV, Top-1/MRR, failure types, bootstrap CIs, paired diffs |
| `src/experiments.py` | builds all conditions, runs CV, writes tables and figures |

## Design decisions
1. **Roster** = the characters of the manifest alias table, fixed per story (same for every prefix and deletion). With prefix-only aliases (default) a pseudonym linked only at/after the reveal is its own node, e.g. `Jonas Oldacre [as Mr. Cornelius]`; all nodes of the principal culprit count as the culprit. A masked text can leave a node with 0 mentions; it stays a candidate (CLAUDE.md rule 6). The roster is hand-built (3–15 nodes per story), not extracted by NER.
2. **Mentions** = exact alias forms, longest first, non-overlapping ("Miss Turner" claims its "Turner").
3. **Features**, z-scored within each (condition, story) before the model:
   - visibility: log mentions, mention share, relative first-mention position, paragraph coverage;
   - interaction: degree centrality, strength share, weighted PageRank of the roster co-occurrence network (same paragraph);
   - crime: crime-term tokens within ±15 words of any mention (union per character): log count, share, per-mention rate. The stem list is frozen; v2 removed the story-specific stems `harpoon` and `strychnine`.
4. **Models**: penalised conditional logit (main) and L2 logistic regression with `class_weight="balanced"` (comparison), both with C = 1.0 fixed in advance; `c_sensitivity.csv` reports C ∈ {0.01, 0.1, 1, 10}.
5. **Training rows**: principal nodes = 1, others = 0; accomplice nodes left out of training (kept as test candidates); stories whose principal is never mentioned before the reveal (M26, R07, R12, R23) left out of training.
6. **Train unmasked, test masked**: one model per left-out story, combination and model type, trained on the full pre-reveal text of the other 29 stories, applied to every condition of the left-out story.
7. **Prefixes** are shares of all story paragraphs (not of the pre-reveal text, as on the proposal slide). `prefix_information.csv` reports what each share means in words and in share of the pre-reveal text.
8. **Deletion** works on sentence units of the 80% prefix: scattered = random sentences until the target share of words is hidden; continuous = one random window of target words. Realised shares in `mask_audit.csv`. 10 seeds per story; each story is averaged over seeds before the bootstrap.
9. **Scoring** against the best visible principal node, expected Top-1/RR under random tie-breaking. No visible principal mention = failure for every method, including random. Each story/condition gets a `failure_type` (hit, tied_first, ranking_error, not_visible).

## v2 results (30 eligible stories, leave-one-story-out, C = 1)
Descriptive of this corpus and this procedure; see the reporting rules in 03_revision_plan.md.

**Full pre-reveal text** (`exp0_full_text.csv`). Coverage 26/30 (0.867) for every method, so 0.867 is the ceiling on Top-1 and MRR.

| | V | I | C | V+I | V+C | I+C | V+I+C |
|---|---|---|---|---|---|---|---|
| clogit MRR | 0.35 | 0.44 | 0.41 | 0.40 | 0.42 | 0.48 | 0.43 |
| logreg MRR | 0.39 | 0.47 | 0.42 | 0.43 | 0.36 | 0.48 | 0.46 |

Baselines: mention_freq 0.40, random 0.39. Every 95% CI is about ±0.11–0.12.

- **Primary comparison 1** (clogit V+I+C − mention_freq, MRR): +0.03, 95% CI [−0.09, 0.17]; 12 stories better, 10 worse, 8 tied. No evidence that the features beat counting mentions on this corpus.
- Conditional logit vs. logistic regression: no consistent difference (paired CIs mostly include 0; `exp0_model_comparison.csv`). Results are similar for all C in the grid (`c_sensitivity.csv`, V+I+C MRR 0.40–0.44 for clogit).
- Failure types (clogit V+I+C): 7 hits, 19 ranking errors, 4 not visible. Most failures are ranking errors, not absent culprits.

**Experiment 1, prefixes** (`exp1_prefix.csv`, clogit V+I+C): MRR 0.28 / 0.37 / 0.42 / 0.42 at 20/40/60/80%, 0.43 on the full pre-reveal text. Coverage rises from 0.53 to 0.83 while MRR given a visible culprit stays about 0.51 at every share: the gain with more text comes from the culprit having appeared, not from better ranking among visible candidates. A "20%" prefix covers 15–41% of a story's pre-reveal text (median 26%) and 589–12,739 words (`prefix_information.csv`).

**Experiment 2, deletion** (`exp2_deletion.csv`, `exp2_paired.csv`):
- **Primary comparison 2** (clogit V+I+C, scattered − continuous at 20%, MRR): +0.01, 95% CI [−0.03, 0.05]; 10 stories better under scattered, 15 under continuous.
- Removing 10–30% of the words of the 80% prefix changes MRR by at most 0.05 for any method (largest: C, scattered, 30%); exploratory paired CIs exclude 0 in 2 of 21 feature-combination comparisons (I at 20%, V+I at 30%), compatible with chance.

**Alias sensitivity** (`outputs/v2_full_alias/`): see 03_revision_plan.md, section "v2 results vs v1".

## Open points
- The proposal slide names a TF-IDF candidate-text model as the main model; only the 7 feature combinations are implemented.
- Exp 2 uses one base prefix (80%); the proposal slide speaks of 20% removal of the pre-reveal text.
- Open annotation decisions (roster rule for police, principal of M20/M23, blind re-annotation) are listed in 03_revision_plan.md.
