# Step 1 – Data annotation (Weeks 1–4)

Goal: verified annotations for 5 pilot (`manifest/pilot.csv`) + 30 main stories (`manifest/annotations.csv`; excluded candidates in `manifest/excluded.csv`), plus cleaned, paragraph-numbered texts.

**Team setup:** one annotator (`wyte`) does all preprocessing and annotation and commits directly to `main`. Annotation rows are Claude-assisted drafts: every row is written with `python -m src.annotate spec.json` (quotes and alias forms checked against the text by code) and must be confirmed by the annotator against the quoted paragraphs. There is no second human annotator and no reliability re-annotation (section 5); this is stated as a limitation.

## 0. Decisions (made)
- [x] **Corpus scope.** Holmes + Father Brown + Agatha Christie (*Poirot Investigates*, *The Mysterious Affair at Styles*); candidates and reserves in `data/corpus_candidates.csv`.
- [x] **Who annotates.** One annotator for all stories; no reliability re-annotation (section 5).
- [x] **Earliest explicit reveal.** Defined in `docs/annotation_guideline.md` (v0.2, v0.5).

## 1. Setup
- [x] Run `notebooks/01_prepare_corpus.ipynb` (Adventures, pilot P1–P5) and `notebooks/03_prepare_main_corpus.ipynb` (all other books).
- [x] Commit `data/raw/` and `data/processed/` so paragraph numbers are fixed.

## 2. Pilot annotation
- [x] Annotate P1–P5; fix ambiguities in the guideline and bump its version (v0.2–v0.4).

## 3. Alias reliability check
- [x] Compare hand-built alias tables against a rule-based merge (Mr./Dr. + surname, surname-only, full-name containment), with and without links stated only after the reveal: `notebooks/02_alias_check.ipynb`, results in `outputs/alias_*.csv`.

## 4. Main corpus annotation
- Screen each candidate **reveal-first**: read from the end to find the reveal, let code compute `reveal_pct`; if the reveal is not after 80% (typical of 'capture, then long explanation / confession / flashback' stories), record culprit + reveal only and stop (guideline v0.8).
- Then read → qualifies? → if not, fill `exclusion_reason` and stop.
- `main_screen` rows are expected to be partly excluded; replace from reserves (`R…`, `C…`) to reach 30.
- Stories whose reveal is not after 80% of the paragraphs are excluded automatically (`other:reveal_before_80pct`, guideline v0.6).
- Annotate the novels last; they are 5–8× longer.
- [x] Screening done; 30 eligible stories fully annotated (aliases, `culprit_before_reveal`, `alias_links.csv`).

## 5. Reliability check (dropped)
The blind re-annotation planned in guideline v0.11 was dropped (decision 2026-11-03, guideline v0.13). There is one annotator and no agreement measure; the report states this as a limitation.

## 5a. Revisions after the first results (guideline v0.12–v0.13, 2026-11-03)
- [x] M26, R07, R12, R23: the principal has no name of their own before the reveal; the pre-reveal handle that refers only to the principal is recorded as an alias ('the lady'/'this lady', 'K. K. K.', 'your double'/'other Hall Pycroft', 'G.'/'the man who took the rooms').
- [x] M20 (principal Burnwell) and M23 (principal Gilchrist, accomplice Bannister) confirmed by the annotator.
- [x] Every roster keeps the investigators: detective, sidekick/narrator and police named before the reveal.

## 6. Deliverables / definition of done
- [x] `manifest/annotations.csv` complete; `reveal_pct` filled by code
- [x] `culprit_before_reveal` filled for every included story
- [x] Exclusion reasons recorded for every excluded candidate (`manifest/excluded.csv`)
- [x] Guideline v0.13 (handles for unnamed principals, investigators in every roster)
