# Step 2–3: Features, prediction and masking experiments (W5–W10)

Run everything: `python -m src.experiments` (about 5 min; `--quick` uses 2 deletion seeds).
Tables go to `outputs/v3/results/`, figures to `outputs/v3/figures/`. All seeds and constants are in `src/config.py`.
Sensitivity run with all alias links merged: `CCD_ALIAS_MODE=full python -m src.experiments --out v3_full_alias`.

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
1. **Roster** = the characters of the manifest alias table, including investigators (guideline v0.13), fixed per story (same for every prefix and deletion). With prefix-only aliases (default) a pseudonym linked only at/after the reveal is its own node, e.g. `Jonas Oldacre [as Mr. Cornelius]`; all nodes of the principal culprit count as the culprit. A masked text can leave a node with 0 mentions; it stays a candidate (CLAUDE.md rule 6). The roster is hand-built (5–17 nodes per story in v3), not extracted by NER.
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

## Current results (v3: v2 code + guideline v0.13 annotations; 30 stories, LOSO, C = 1)
Descriptive of this corpus and this procedure; see the reporting rules in 03_revision_plan.md. v2 results (before the annotation changes) are in `outputs/v2/` and summarised in 03_revision_plan.md.

**Full pre-reveal text** (`outputs/v3/results/exp0_full_text.csv`). Every principal now has a visible node (coverage 30/30).

| | V | I | C | V+I | V+C | I+C | V+I+C |
|---|---|---|---|---|---|---|---|
| clogit MRR | 0.52 | 0.29 | 0.48 | 0.44 | 0.49 | 0.48 | 0.49 |
| logreg MRR | 0.50 | 0.37 | 0.45 | 0.43 | 0.48 | 0.48 | 0.46 |

Baselines: mention_freq 0.30, random 0.37.

- **Primary comparison 1** (clogit V+I+C − mention_freq, MRR): +0.19, 95% CI [0.02, 0.36]; 21 stories better, 6 worse, 3 tied. Against random: +0.12 [0.01, 0.25].
- The detective is the most-mentioned roster member in 27 of 30 stories, so the mention baseline mostly ranks the detective first. Part of the model's gain is learning to rank investigators down; the model still ranks an investigator first in 5 stories.
- Interaction features alone are the weakest (0.29): the detective co-occurs with everyone.
- Failure types (clogit V+I+C): 8 hits, 22 ranking errors, 0 not visible.

**Experiment 1, prefixes** (clogit V+I+C): MRR 0.21 / 0.34 / 0.41 / 0.46 at 20/40/60/80%, 0.49 on the full pre-reveal text. Coverage 0.53 / 0.83 / 0.93 / 0.93; MRR given a visible culprit 0.40 / 0.41 / 0.44 / 0.50. A "20%" prefix covers 15–41% of a story's pre-reveal text and 589–12,739 words (`prefix_information.csv`).

**Experiment 2, deletion**: **primary comparison 2** (clogit V+I+C, scattered − continuous at 20%): −0.01, 95% CI [−0.04, 0.01]; no difference. Exploratory paired CIs exclude 0 in 2 of 21 feature-combination comparisons (V at 30%, V+C at 20%), compatible with chance.

**Alias sensitivity** (`outputs/v3_full_alias/`): with all pseudonym links merged, clogit V+I+C 0.45 and mention_freq 0.32.

## Open points
- The proposal slide names a TF-IDF candidate-text model as the main model; only the 7 feature combinations are implemented.
- Exp 2 uses one base prefix (80%); the proposal slide speaks of 20% removal of the pre-reveal text.
- Planned next: information-matched prefixes (fixed word counts, MRR vs. culprit mentions), by-author and leave-one-author-out results, a filtered metric that does not penalise accomplices, and an error analysis of who is ranked above the culprit.
