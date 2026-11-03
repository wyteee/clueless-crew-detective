"""All random seeds and experiment constants (CLAUDE.md rule 7: no seeds anywhere else)."""

SEED = 2026                      # master seed: CV fold assignment, bootstrap, random baseline

# Cross-validation (pilot stories P1-P5 are never part of it)
N_FOLDS = 5
C_GRID = [0.01, 0.1, 1.0, 10.0]  # inverse L2 strength, tuned by inner GroupKFold on training stories
INNER_FOLDS = 3

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
