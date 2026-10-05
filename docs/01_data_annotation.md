# Step 1 – Data annotation (Weeks 1–4)

Goal: a verified `manifest/annotations.csv` for 5 pilot + ~30 main stories, plus cleaned, paragraph-numbered texts.

## 0. Decide first (10-minute team meeting)
- [ ] **Corpus scope.** The Holmes canon likely yields only ~14–19 stories with one clear human (principal) culprit. Options: (a) Holmes + Father Brown to reach ~30 (current list), (b) Holmes only, target ~20–25 (proposal allows 25–35, so would need a note to the instructor), (c) add other authors. Current list = option (a).
- [ ] **Who annotates which stories** (see split below) and who cross-reviews.
- [ ] Confirm the guideline wording of "earliest explicit reveal".

## 1. Setup (Day 1)
- [ ] Create the GitHub repo, add teammates, everyone clones and sets up the venv (see README).
- [ ] Run `notebooks/01_prepare_corpus.ipynb`; check the printed first/last paragraph of each of the 12 Adventures stories; confirm P1–P5 files exist in `data/processed/`.
- [ ] Commit `data/raw/` and `data/processed/` so everyone uses identical paragraph numbers.

## 2. Pilot annotation (Week 1–2)
- [ ] Everyone independently annotates **P1** (Speckled Band) → guideline walk-through, fix ambiguities, bump guideline version.
- [ ] Split P2–P5 between annotators; each story is then independently re-annotated by someone else (all 5 are cross-reviewed).
- [ ] Compute agreement (below) and write a one-page pilot summary.

## 3. Alias reliability check (Week 3)
Compare hand-built alias tables against a rule-based merge (Mr./Dr. + surname, surname-only, full-name containment). Report alias precision/recall per pilot story. If poor → fall back to explicit named mentions + manual audit (proposal's fallback).

## 4. Main corpus annotation (Week 3–4)
- Screen each candidate **reveal-first**: read from the end to find the reveal, let code compute `reveal_pct`; if the reveal is not after 80% (typical of 'capture, then long explanation / confession / flashback' stories), record culprit + reveal only and stop (guideline v0.8).
- Then read → qualifies? → if not, fill `exclusion_reason` and stop.
- `main_screen` rows are expected to be partly excluded; replace from reserves (`R01…`) to reach 30.
- Stories whose reveal is not after 80% of the paragraphs are excluded automatically (`other:reveal_before_80pct`, guideline v0.6); they also count as excluded when topping up from reserves.
- Annotate the two novels last; they are 5–8× longer.
- Cross-review ≥20% (≥6 of 30), chosen at random with a fixed seed, by someone who did not annotate the story.

## 5. Agreement metrics
- Culprit: exact match rate (and Cohen's kappa if enough items).
- Reveal: exact match rate, and within ±2 paragraphs.
- Aliases: precision/recall/F1 of the alias set for the culprit, between annotators.
Disagreements are resolved in a meeting; the resolution goes into the guideline's change log.

## 6. Deliverables / definition of done
- [ ] `manifest/annotations.csv` complete; `reveal_pct` filled by code
- [ ] `culprit_before_reveal` filled for every included story
- [ ] Exclusion table (story, reason) for excluded candidates
- [ ] Agreement numbers + pilot summary (1 page)
- [ ] Guideline v1.0

## Suggested split (3 people, ~35 stories ≈ 12 each)
- A: guideline owner, manifest maintainer, pilot P1–P2, Return stories
- B: P3–P4, Adventures/Memoirs/His Last Bow stories
- C: P5, Case-Book, Father Brown, novels
Everyone cross-reviews someone else's work. Adjust to actual team size.
