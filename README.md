# Predicting Culprits in Detective Fiction Under Incomplete Information

**Team: Clueless Crew** · Course project, Data Mining (Text Mining / NLP / Predictive Modeling)

Can we predict the culprit of a detective story *before* the solution is revealed, and which kinds of evidence survive when part of the text is missing?

## Research design (from the proposal)
- **Corpus:** English detective stories from Project Gutenberg (Sherlock Holmes first). 5 pilot stories + ~30 eligible main stories. Main evaluation uses stories with **exactly one identifiable human culprit**; multiple-culprit, non-criminal, and unresolved cases are documented separately.
- **Annotation (human):** culprit, earliest explicit reveal, character aliases. ≥20% of stories cross-reviewed.
- **Features (code):** visibility (mention frequency, first appearance), interaction (paragraph co-occurrence network degree), crime language (crime-term frequency near each character). 7 feature-group combinations.
- **Model:** regularized logistic regression over candidate characters; baselines = random ranking, mention frequency.
- **Experiments:** (1) reveal-free prefix at 20/40/60/80%; (2) at 80%, remove ~10/20/30% of words as scattered sentences vs. one continuous passage, fixed seeds; roster held fixed; train unmasked, test masked.
- **Evaluation:** 5-fold GroupKFold by story (pilot excluded), Top-1 and MRR, paired comparisons and story-level bootstrap CIs, candidate coverage reported (absent culprit = failure).

## Repo layout
```
data/raw/            Gutenberg downloads (never edited)
data/processed/      cleaned, paragraph-numbered texts: [0001] ...
data/corpus_candidates.csv   candidate story list (pilot/main/reserve)
manifest/annotations.csv     annotation table (source of truth)
docs/                guideline, step docs, story list
notebooks/           numbered notebooks (01_prepare_corpus, ...)
src/                 reusable code (features, experiments)
```

## Setup
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```
Open the folder **at the repo root** in VS Code and select the `.venv` kernel for notebooks.

## Status
| Phase | Weeks | Status |
|---|---|---|
| Step 1 – Data annotation (pilot → corpus) | 1–4 | **in progress** – see [docs/01_data_annotation.md](docs/01_data_annotation.md) |
| Features & prediction | 5–8 | not started |
| Masking experiments | 9–10 | not started |
| Analysis & report | 11–12 | not started |

## Collaboration rules
- One branch per person (`annot-<name>`), merge via Pull Request.
- During annotation each person writes to `manifest/annotations_<name>.csv`; merge into `annotations.csv` after review.
- Clear notebook outputs before committing (`nbstripout --install`).
- All random seeds live in one `src/config.py`.

## Data policy
Texts come from Project Gutenberg and follow its [robot access policy](https://www.gutenberg.org/policy/robot_access.html): download once, throttle, work from local copies.

## Limitations (stated up front)
Small corpus, extraction errors, artificial text removal. Findings describe this corpus; prediction accuracy is not a measure of literary quality.
