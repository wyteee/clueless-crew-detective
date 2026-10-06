# Predicting Culprits in Detective Fiction Under Incomplete Information

**Team: Clueless Crew** · Course project, Data Mining (Text Mining / NLP / Predictive Modeling)

Can we predict the culprit of a detective story *before* the solution is revealed, and which kinds of evidence survive when part of the text is missing?

## Research design (from the proposal)
- **Corpus:** English detective stories from Project Gutenberg (Sherlock Holmes first). 5 pilot stories + ~30 eligible main stories. Main evaluation uses stories with **one identifiable human principal culprit**; named accomplices are annotated too. Stories with no clear principal (`multiple_culprits`), non-criminal, and unresolved cases are documented separately.
- **Annotation (human, one annotator):** culprit, earliest explicit reveal, character aliases; Claude-assisted drafts checked by code and by the annotator. Reliability: blind re-annotation of the pilot + ≥20% of main stories by the same annotator (no second human annotator; stated as a limitation).
- **Features (code):** visibility (mention frequency, first appearance), interaction (paragraph co-occurrence network degree), crime language (crime-term frequency near each character). 7 feature-group combinations.
- **Model:** regularized logistic regression over candidate characters; baselines = random ranking, mention frequency.
- **Experiments:** (1) reveal-free prefix at 20/40/60/80% (stories whose reveal is not after 80% of the paragraphs are excluded, `other:reveal_before_80pct`); (2) at 80%, remove ~10/20/30% of words as scattered sentences vs. one continuous passage, fixed seeds; roster held fixed; train unmasked, test masked.
- **Evaluation:** 5-fold GroupKFold by story (pilot excluded), Top-1 and MRR scored against the principal culprit, paired comparisons and story-level bootstrap CIs, candidate coverage reported (absent culprit = failure).

## Repo layout
```
data/raw/            Gutenberg downloads (never edited)
data/processed/      cleaned, paragraph-numbered texts: [0001] ...
data/corpus_candidates.csv   candidate story list (pilot/main/reserve)
manifest/annotations.csv     annotations of the 30 eligible main stories (source of truth)
manifest/pilot.csv           pilot P1–P5 annotations (development only)
manifest/excluded.csv        screened-out candidates with exclusion_reason
manifest/alias_links.csv     pseudonym / maiden-name links (paragraph + quote)
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
| Step 1 – Data annotation (pilot → corpus) | 1–4 | **main annotation done** (30 eligible stories); blind re-annotation check and guideline v1.0 pending – see [docs/01_data_annotation.md](docs/01_data_annotation.md) |
| Features & prediction | 5–8 | not started |
| Masking experiments | 9–10 | not started |
| Analysis & report | 11–12 | not started |

## Collaboration rules
- Annotation and preprocessing are done by one person, committing directly to `main`.
- Annotation rows are written with `python -m src.annotate spec.json` (checks quotes and aliases against the text, computes `reveal_pct`); blind re-annotation rows go to `manifest/review_<annotator>.csv`.
- Clear notebook outputs before committing (`nbstripout --install`).
- All random seeds live in one `src/config.py`.

## Data policy
Texts come from Project Gutenberg and follow its [robot access policy](https://www.gutenberg.org/policy/robot_access.html): download once, throttle, work from local copies.

## Limitations (stated up front)
Small corpus, a single annotator (reliability measured only by blind self re-annotation), extraction errors, artificial text removal. Findings describe this corpus; prediction accuracy is not a measure of literary quality.
