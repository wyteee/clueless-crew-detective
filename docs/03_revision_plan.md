# Revision plan after the proposal feedback (v1 → v2)

Branch: `revision-feedback`. v1 = the first full run uploaded in `w5-w10_code_and_results/` (commit `03eabe0`).
v1 outputs are kept unchanged in `outputs/v1_initial/` so every change can be compared with the original.

Instructor feedback points referred to below:
- **F1** grouped evaluation by story; **F2** 5-fold CV is unstable with 25–30 stories;
- **F3** absent culprit vs. culprit ranked incorrectly; **F4** fixed roster defined mathematically;
- **F5** 20/40/60/80% are not equal amounts of information across stories;
- **F6** what one training example is; **F7** characters within a story are not independent;
- **F8** prediction vs. inference (no causal claims).

## Changes

| # | Area | v1 (original) | v2 (new) | Why |
|---|---|---|---|---|
| R1 | Repo layout | Code uploaded into `w5-w10_code_and_results/`; it imports `src.aliases`, which lives in the root `src/`, so it does not run in place. | `src/{config,features,masking,evaluate,experiments}.py` and `docs/02_…` moved to the root; v1 outputs archived in `outputs/v1_initial/`; the subfolder removed. `requirements.txt`: scikit-learn ≥ 1.6 (needed by `GroupKFold(shuffle=True)`), scipy added. | Reproducibility. |
| R2 | Alias merging | Full manifest alias table, including pseudonym links stated only at/after the reveal (principal affected in M05, M11, C04, C05, C09; accomplice in R33). | `aliases.prefix_only_aliases`: a pseudonym linked only at/after the reveal is a separate roster node (e.g. `Killer Evans [as Mr. John Garrideb]`). Config switch `ALIAS_MODE = "prefix_only"`; `"full"` kept as a sensitivity run. | Leakage: proposal says alias decisions use only prefix-available evidence. In v1 the model already "knew" that Mr. Cornelius is Oldacre. |
| R3 | Culprit label with pseudonym nodes | One node per character; `is_culprit` = node is the principal. | Every node that is the principal (real name or a pseudonym persona) has `is_culprit = 1`. A story is scored by the highest-ranked principal node with a visible mention; accomplice personas are accomplices. A real-name node left with no pre-reveal form (M11: Killer Evans appears only as "John Garrideb") is dropped. The random baseline gets the same best-of-k credit. | Before the reveal the reader meets the culprit as e.g. "John Garrideb"; ranking that persona first is a correct identification. |
| R4 | Crime lexicon | 70 stems, "audited against the corpus", including `harpoon` (weapon in M07) and `strychnine` (poison in C12). | Those two story-specific stems removed; the list is frozen and documented as fixed before v2 results were seen. | Leakage: a lexicon tuned on evaluation stories encodes the answer. |
| R5 | Main model | L2 logistic regression on independent rows, `class_weight="balanced"`. | **Penalised conditional logit** (softmax over the candidates of one story; objective $C\cdot$NLL $+\tfrac12\lVert\beta\rVert^2$ as in sklearn, but with one NLL term per story rather than per row). Logistic regression is kept as a comparison model. | F6/F7: the task is "which candidate of this story is the culprit"; conditional logit models exactly that, gives every story equal weight and cancels story-level effects. |
| R6 | Cross-validation | Outer 5-fold GroupKFold (shuffled), inner 3-fold GroupKFold to pick C from {0.01, 0.1, 1, 10}. Chosen C jumped between 0.01 and 10 across folds. | **Leave-one-story-out** (30 folds, deterministic). **C fixed at 1.0**, chosen before seeing v2 results; a sensitivity table reports the full-text results for every C in the grid. | F1/F2: 6 test stories per fold is unstable, and the inner CV could not tell the C values apart. |
| R7 | Training examples | Principal = 1, others = 0; accomplices and stories whose principal is never named before the reveal left out of training. | Unchanged, now stated as the formal definition (below). Stories without any visible principal node are also left out of conditional-logit training (no positive). | F6. |
| R8 | Failure types | One flag `culprit_visible`; an absent culprit scores 0. | Per story and condition: `failure_type` ∈ {`hit`, `ranking_error`, `not_visible`}. Summary tables add coverage and MRR/Top-1 **conditional on the culprit being visible**, so Top-1 = coverage × conditional Top-1. | F3. |
| R9 | Information per prefix | Only the share of paragraphs is reported. | New table `prefix_information.csv`: per story and share, visible words, visible paragraphs, principal mentions, whether the principal is visible, share of the pre-reveal text covered. | F5: 20% of a 3.4k-word story and 20% of *Styles* (59k words) are not comparable amounts of text. |
| R10 | Roster in the prefix experiment | Full pre-reveal roster for every prefix; not documented. | Unchanged behaviour, documented in the definitions below. | F4. |

## Formal definitions (for the report's Methods)

- Story $s$ has paragraphs $1,\dots,n_s$ and an annotated reveal paragraph $r_s$; eligible stories satisfy $r_s > 0.8\,n_s$.
- Prefix: $P_s(q) = \{\,i : i \le q\,n_s,\ i < r_s\,\}$ for $q \in \{0.2,0.4,0.6,0.8\}$; the training text is $P_s^{\text{full}} = \{1,\dots,r_s-1\}$.
- Alias map $A_s$ and roster $R_s$: the hand-built alias table of the manifest (forms seen before the reveal), with pseudonym links stated at or after $r_s$ split into separate nodes (R2). $R_s$ is fixed for the story: it is the same for every prefix and every deletion.
- Deletion: $D \subset P_s(0.8)$ is a set of sentence units with about $\delta \in \{0.1,0.2,0.3\}$ of the words of $P_s(0.8)$; visible text $T = P_s(0.8) \setminus D$. Features $x_c(T)$ are recomputed for all $c \in R_s$ (zero mentions allowed); $R_s$ and $A_s$ are not recomputed.
- Principal nodes $\Pi_s \subseteq R_s$ (R3); accomplice nodes $\mathcal{A}_s$.
- One training example = one pair $(s, c)$, $c \in R_s \setminus \mathcal{A}_s$, label $y_{sc} = \mathbb{1}[c \in \Pi_s]$, computed on $P_s^{\text{full}}$. Rows of one story are dependent; the unit of analysis and of resampling is the story ($N = 30$, at most 26 with a visible principal).
- Conditional logit: $P(c \mid s) = \exp(\beta^\top x_{sc}) / \sum_{k \in R_s \setminus \mathcal{A}_s} \exp(\beta^\top x_{sk})$; the training objective is $C \sum_s -\log \sum_{c \in \Pi_s} P(c \mid s) + \tfrac12\lVert\beta\rVert^2$.
- Score: rank of the best principal node among all of $R_s$ (accomplices included at test time), ties broken at random in expectation; Top-1 and reciprocal rank are 0 when no principal node has a visible mention.

## Reporting rules (F8)
- Results are descriptive of this corpus and this masking procedure: "on this corpus, MRR under continuous deletion was X lower than under scattered deletion (95% CI …)". No "damaging", "causes", or claims about how detective fiction works.
- Primary comparisons fixed in advance: (1) conditional logit V+I+C vs. mention-frequency baseline on the full pre-reveal text; (2) scattered − continuous at 20% deletion for V+I+C. Everything else is exploratory.
- Coefficients are not interpreted as effects.

## Not changed in this revision (open decisions for the team)
- **Roster construction**: still the hand-built alias table (3–15 characters per story), not NLP extraction as in the proposal. To be stated as a design change and limitation; an NER-based roster could be a robustness check if time allows.
- **Police in the roster**: Lestrade (M05), Japp (C04, C08, C09, C12) and Flambeau (M17, R02) are candidates; detectives and narrators are not. A single rule should be chosen and applied.
- **Principal for M20 and M23** still marked "to be confirmed" in the notes.
- **Blind re-annotation check** and guideline v1.0 (docs/01 §5–6).
- **By-author sensitivity** (Holmes 16, Christie 10, Father Brown 4) — can be added once v2 is agreed.

## v2 results vs v1 (full pre-reveal text, MRR)
Produced by code in this repo: v1 = `outputs/v1_initial/` (5-fold, inner-CV C, logistic regression, all alias links merged, v1 lexicon); v2 = `outputs/v2/` (LOSO, C = 1, prefix-only aliases); v2 full alias = `outputs/v2_full_alias/` (same as v2 but all links merged).

| method | v1 logreg | v2 clogit | v2 logreg | v2 clogit, full alias |
|---|---|---|---|---|
| V | 0.38 | 0.35 | 0.39 | 0.39 |
| I | 0.43 | 0.44 | 0.47 | 0.45 |
| C | 0.33 | 0.41 | 0.42 | 0.37 |
| V+I | 0.45 | 0.40 | 0.43 | 0.43 |
| V+C | 0.37 | 0.42 | 0.36 | 0.44 |
| I+C | 0.48 | 0.48 | 0.48 | 0.49 |
| V+I+C | 0.41 | 0.43 | 0.46 | 0.44 |
| mention_freq | 0.42 | 0.40 | 0.40 | 0.42 |
| random | 0.37 | 0.39 | 0.39 | 0.37 |

- The conclusion does not change: no feature combination is clearly better than the baselines; all CIs are about ±0.11.
- Merging post-reveal pseudonym links raises visibility-type methods (mention_freq 0.40 → 0.42, clogit V 0.35 → 0.39), as expected from extra culprit mentions; the size of the leak is small at the corpus level but real for M05 (clogit V+I+C RR 0.33 prefix-only vs 0.50 merged).
- Random differs between v1 and v2 because pseudonym nodes add candidates and give best-of-k credit (R3).
