# Step 1 – Data annotation (Weeks 1–4)

Goal: verified annotations for 5 pilot (`manifest/pilot.csv`) + 30 main stories (`manifest/annotations.csv`; excluded candidates in `manifest/excluded.csv`), plus cleaned, paragraph-numbered texts.

**Team setup:** one annotator (`wyte`) does all preprocessing and annotation and commits directly to `main`. Annotation rows are Claude-assisted drafts: every row is written with `python -m src.annotate spec.json` (quotes and alias forms checked against the text by code) and must be confirmed by the annotator against the quoted paragraphs. There is no second human annotator, so the inter-annotator cross-review of the original plan is replaced by a blind re-annotation check (section 5).

## 0. Decisions (made)
- [x] **Corpus scope.** Holmes + Father Brown + Agatha Christie (*Poirot Investigates*, *The Mysterious Affair at Styles*); candidates and reserves in `data/corpus_candidates.csv`.
- [x] **Who annotates.** One annotator for all stories; reliability via the blind re-annotation check below.
- [x] **Earliest explicit reveal.** Defined in `docs/annotation_guideline.md` (v0.2, v0.5).

## 1. Setup
- [x] Run `notebooks/01_prepare_corpus.ipynb` (Adventures, pilot P1–P5) and `notebooks/03_prepare_main_corpus.ipynb` (all other books).
- [x] Commit `data/raw/` and `data/processed/` so paragraph numbers are fixed.

## 2. Pilot annotation
- [x] Annotate P1–P5; fix ambiguities in the guideline and bump its version (v0.2–v0.4).
- [ ] Blind re-annotation of P1–P5 (section 5) and a one-page pilot summary.

## 3. Alias reliability check
- [x] Compare hand-built alias tables against a rule-based merge (Mr./Dr. + surname, surname-only, full-name containment), with and without links stated only after the reveal: `notebooks/02_alias_check.ipynb`, results in `outputs/alias_*.csv`.

## 4. Main corpus annotation
- Screen each candidate **reveal-first**: read from the end to find the reveal, let code compute `reveal_pct`; if the reveal is not after 80% (typical of 'capture, then long explanation / confession / flashback' stories), record culprit + reveal only and stop (guideline v0.8).
- Then read → qualifies? → if not, fill `exclusion_reason` and stop.
- `main_screen` rows are expected to be partly excluded; replace from reserves (`R…`, `C…`) to reach 30.
- Stories whose reveal is not after 80% of the paragraphs are excluded automatically (`other:reveal_before_80pct`, guideline v0.6).
- Annotate the novels last; they are 5–8× longer.
- [x] Screening done; 30 eligible stories fully annotated (aliases, `culprit_before_reveal`, `alias_links.csv`).

## 5. Reliability check (single annotator)
Replaces the multi-person cross-review.
- **Sample:** all 5 pilot stories + a random ≥20% of the eligible main stories (≥6 of 30), drawn with the seed in `src/config.py`.
- **Blind re-annotation:** the annotator re-annotates each sampled story from the text **without looking at its manifest row**, ideally after a gap of at least a few days. Rows go to `manifest/review_wyte.csv` (same columns as the manifest).
- **Compare** the blind pass with `manifest/annotations.csv` / `manifest/pilot.csv` (the Claude-assisted drafts):
  - Culprit: exact match rate of the principal (and of the full culprit list).
  - Reveal: exact match rate, and within ±2 paragraphs.
  - Aliases: precision/recall/F1 of the culprit's alias set.
- **Resolve** each disagreement by rereading the text; fix the manifest row via `src.annotate` and record any rule change in the guideline's change log.
- **Report** the numbers as agreement between the blind human pass and the assisted draft, and state as a limitation that there is no agreement between two independent human annotators.

## 6. Deliverables / definition of done
- [x] `manifest/annotations.csv` complete; `reveal_pct` filled by code
- [x] `culprit_before_reveal` filled for every included story
- [x] Exclusion reasons recorded for every excluded candidate (`manifest/excluded.csv`)
- [ ] Blind re-annotation check (section 5): agreement numbers + pilot summary (1 page)
- [ ] Guideline v1.0
