"""All random seeds and experiment constants (CLAUDE.md rule 7: no seeds anywhere else).

v2 changes (docs/03_revision_plan.md): prefix-only alias merging (R2), leave-one-story-out CV with a
fixed C (R6), conditional logit as the main model (R5).
"""
import os

SEED = 2026                      # master seed: bootstrap, deletion draws

# Alias merging (R2). "prefix_only": pseudonym links stated only at/after the reveal stay separate
# roster nodes. "full": merge every link (v1). Read from the environment so that parallel worker
# processes see the same value: CCD_ALIAS_MODE=full python -m src.experiments --out v2_full_alias
ALIAS_MODE = os.environ.get("CCD_ALIAS_MODE", "prefix_only")

# Cross-validation (R6): leave-one-story-out over the 30 eligible stories; pilot P1-P5 never used.
# C is fixed in advance (inverse L2 strength, same scale for both models); the grid is only used for
# the sensitivity table on the full pre-reveal text.
C_FIXED = 1.0
C_GRID = [0.01, 0.1, 1.0, 10.0]

# Models (R5): "clogit" = penalised conditional logit (main), "logreg" = logistic regression (comparison)
MODELS = ["clogit", "logreg"]
MAIN_MODEL = "clogit"

# Experiment 1: reveal-free prefixes, as a share of ALL paragraphs of the story.
# Every eligible story has reveal_para_idx > 0.8 * n_paragraphs, so the 80% prefix never contains the reveal.
PREFIX_SHARES = [0.2, 0.4, 0.6, 0.8]

# Experiment 2: delete a share of the WORDS of the 80% prefix, in sentence units.
DELETE_BASE_PREFIX = 0.8
DELETE_RATES = [0.1, 0.2, 0.3]
DELETE_PATTERNS = ["scattered", "continuous"]
MASK_SEEDS = list(range(10))     # one deletion draw per seed per story

# Features
CRIME_WINDOW = 15                # words on each side of a mention

# Evaluation
N_BOOTSTRAP = 2000
