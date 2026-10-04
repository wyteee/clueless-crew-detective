# CLAUDE.md – project context for Claude Code

## What this repo is
Course project (Data Mining) "Predicting Culprits in Detective Fiction Under Incomplete Information". See README.md for the design. Team members mostly write in Chinese; reply in the language the user uses. Code, comments and docs stay in English.

## Current phase
**Step 1: data annotation.** Read `docs/01_data_annotation.md` and `docs/annotation_guideline.md` before touching data.

## Hard rules
1. `data/raw/` is immutable. Never edit or regenerate by hand.
2. `data/processed/<story_id>.txt` has fixed paragraph numbers `[0001]`. Never renumber, merge or split paragraphs after annotation starts; annotations depend on them.
3. **Ground truth comes only from reading the text.** `data/corpus_candidates.csv` and `docs/story_list.md` contain culprit names recalled from memory; they are unverified and must not be copied into `manifest/annotations.csv`. When asked to annotate, locate evidence in the text and quote it.
4. `reveal_pct` is computed by code (`reveal_para_idx / n_paragraphs`), never typed by hand.
5. Alias surface forms and the character roster come only from text **before** the reveal paragraph. Exception (guideline v0.3): a pseudonym is merged into the real name whenever the text states they are the same person, even if only at/after the reveal; `notes` records the source paragraph so the feature pipeline can also run a prefix-only variant.
6. In the masking experiments the character roster is fixed from the unmasked prefix; only features are recomputed.
7. No random seeds outside `src/config.py`. Pilot stories (P1–P5) are development-only and excluded from the GroupKFold evaluation.
8. Gutenberg: download once with a descriptive User-Agent and a delay, per its robot access policy; then read local files.
9. Do not claim or report numbers that were not produced by code in this repo.

## Conventions
- Manifest columns: `story_id,title,annotator,culprit,reveal_para_idx,reveal_pct,reveal_quote,aliases,culprit_before_reveal,exclusion_reason,notes`.
- `exclusion_reason` ∈ `multiple_culprits | non_criminal | unresolved | non_human | culprit_unnamed | other:<text>`.
- Cross-review rows: same `story_id`, different `annotator`, stored in that person's own CSV.
- Notebooks are numbered `NN_name.ipynb`, run top to bottom, outputs cleared before commit.

## Commands
```bash
pip install -r requirements.txt && python -m spacy download en_core_web_sm
jupyter lab            # or open notebooks in VS Code
```

## Next after annotation
Feature pipeline in `src/features.py` with a frozen interface `get_features(story_id, text_mask=None) -> DataFrame`, then evaluation (`src/evaluate.py`) and masking (`src/masking.py`).
