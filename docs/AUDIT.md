# GNSS Security Shield — Audit (Steps 1 & 2)

**Historical document.** File paths in this audit refer to the repository layout at commit `b4e6aa0`, before the restructure; current status is tracked in [`ROADMAP.md`](ROADMAP.md).

Audited on branch `feat/fde-upgrade` (cut from `main` @ `b4e6aa0`). Every number below was produced by code that ran in this audit; the scripts and raw logs live in [`docs/audit/`](audit/) and [`docs/audit/output/`](audit/output/). Nothing in the product code was changed.

**Audit environment:** macOS, Python 3.14.8, fresh venv, `pip install -r backend/requirements.txt` (unpinned) → scikit-learn 1.9.1, pandas 3.1.1, numpy 2.5.5, fastapi 0.165.0. Node, Docker and `gcloud` are **not installed** on this machine, so the React GUI, Docker image and any cloud step could not be run here (see "Can't verify").

---

## 0. Headline

| | |
|---|---|
| **Biggest finding** | The "94% precision" claim **cannot be reproduced and has no source in the repo.** The training data is 100% genuine (`spoofed` is 0 for all 24,725 usable rows), so the repo contains **no labelled spoofed data at all** and no code that ever computes precision. |
| **What I measured instead** | Re-using the notebook's own synthetic attack recipe against the shipped model gives **precision 0.13–0.16, recall 0.23–0.32** (shuffled-sample protocol, 3 seeds) and, with a leak-free time split, **precision 0.17–0.23 / recall 0.12–0.16** (10% scattered attacks) or **precision 0.26–0.70 / recall 0.06–0.33** (sustained attacks). See G2. |
| **Missing entirely** | XGBoost pipeline (G3), Dockerfile (G4), pytest suites (G4), CI, `/health`, any validation or auth. |
| **Solid** | The Isolation Forest pipeline, notebook, FastAPI service and Next.js dashboard exist and the API runs from a clean venv. The physics-informed features are real and sensible. The "no new hardware" story is **plausible and measurable** (2.3 MB model, CPU-only, ~4 ms for a 100-row batch). |

---

## 1. Clean-clone health check

| Question | Result | Evidence |
|---|---|---|
| Backend installs from a clean venv? | **Yes**, but unpinned. `requirements.txt` lists 8 packages with no versions. | `pip install -r backend/requirements.txt` succeeded on Python 3.14.8. `xlrd` is **not** in `requirements.txt` (README says to `pip install xlrd` separately). |
| Backend runs? | **Yes.** `python main.py` serves on :8000, `/scan` returns `model_loaded: true`, `feature_count: 35`. | Ran uvicorn and curl'd `/scan`, `/predict`, `/predict/file`. |
| Model loads cleanly? | **Loads, with a version warning.** Pickle was written by scikit-learn **1.6.1**; unpinned install gives 1.9.1 → `InconsistentVersionWarning` ×4 at startup ("may lead to breaking code or invalid results"). | `docs/audit/output/env.txt`, uvicorn log. Pinning + retraining or pinning 1.6.1 is required. |
| React GUI installs/runs? | **Can't verify** — Node not installed here. It is **Next.js 14.2.35 (React 18)**, not a plain React/Vite app. `package.json`/lockfile are present. API URL is hard-coded to `http://localhost:8000` in 4 places in `frontend/src/app/page.tsx` (lines 69, 123, 172, 198), so it can't point at a deployed backend without a code change. | `frontend/package.json`, `git grep localhost`. |
| Docker? | **Missing.** No Dockerfile, no compose file anywhere. | `git ls-files` shows none. |
| Tests? | **None.** No `tests/`, no `pytest` config, no `test_*.py`. `backend/test_nan.json` and `backend/dirty_test.csv` are leftover manual probes; `test_result.json` is a 0-byte file. | `git ls-files`. |
| README? | **Present but inaccurate/duplicated.** Two READMEs disagree (root: "FastAPI/Flask", `python app.py` which doesn't exist, "35 features", "Label 3 … `triple_residual`"; inner: `python3 main.py`). A "MIT License" badge links to a `LICENSE` file that **does not exist**. | `README.md`, `GNSS_Security_Package/README.md`, `git ls-files`. |
| CI? | **None.** No `.github/`. | `git ls-files`. |
| Hard-coded secrets? | **None found** (no keys, tokens or passwords). | `git grep -iE 'api[_-]?key\|secret\|token\|password\|PRIVATE KEY'` → no hits. |
| Dataset in repo? | **Yes, but only partly.** `train.xls` (12.6 MB, legacy `.xls`, needs `xlrd`) is committed. The hackathon `test.xls` is **not** in the repo, so `submission.csv` (29,926 rows) can't be regenerated. No download script, no source/licence note. | `GNSS_Security_Package/train.xls`; notebook cell 13 reads `test.xls`. |
| Repo hygiene | Model pickle committed **twice** (identical, `cmp` confirmed): root `GNSS_AntiSpoofing_Project_Bundle/` and `GNSS_Security_Package/GNSS_AntiSpoofing_Project_Bundle/`. A stray `Know your project.md` sits at the root. The run guide contains a hard-coded developer-specific absolute path. | `git ls-files`, `cmp`. |

### API behaviour found while exercising it (relevant to the hardening plan)

| Finding | Evidence |
|---|---|
| **No input validation.** `POST /predict {"data":[{"foo":1}]}` returns **200 and `is_spoofed: true`**; missing fields are silently filled with 0.0. | curl, see above |
| **No `/health`** (404). Only `/scan`. | curl |
| **No auth, and CORS reflects any origin with credentials** (`allow_origins=["*"]` + `allow_credentials=True`; `Origin: https://evil.example` was echoed back). | curl `-I` |
| **Shared mutable global state.** Single-row `/predict` uses a process-wide `history_manager` keyed by channel, so concurrent clients contaminate each other's rolling features; `/reset` wipes it for everyone. | `backend/utils.py`, `backend/main.py` |
| **Cleaning bug.** `backend/utils.py::clean_gnss` doesn't drop the 8 `chX` placeholder rows that the notebook's version does → 24,733 vs 24,725 rows, 8 rows with NaN PRN reach the model. | `docs/audit/output/a1_data_facts.txt` |
| **Notebook/backend drift.** Notebook rolling features use `min_periods=1` for training; the notebook's stress test (cell 17) uses `rolling(WINDOW)` with no `min_periods` and `fillna(0)`, i.e. a different feature distribution from training. | `GNSS_Hackathon.ipynb` cells 6, 17 |
| **No latency/size limits:** whole upload is read into memory, `head(200)` truncation is the only cap. | `main.py` |

---

## 2. Claims verification (Step 1)

| ID | Status | Evidence |
|---|---|---|
| **G1** Stack: Python, Scikit-learn, FastAPI, React, Docker | **Partial** | Python ✅ , scikit-learn ✅ (`IsolationForest` + `StandardScaler` pipeline), FastAPI ✅ (`backend/main.py`), React ✅ **via Next.js 14.2.35 / React 18** (`frontend/package.json`). **Docker ❌ — no Dockerfile exists.** |
| **G2** 94% precision, 120K+ records, unsupervised Isolation Forest, 13 features, 8 channels | **Partial → precision claim not verified (see detail)** | Details below. |
| **G3** Physics-informed XGBoost pipeline + Isolation Forest Colab notebook | **Partial** | **Isolation Forest notebook: ✅** `GNSS_Security_Package/GNSS_Hackathon.ipynb` (20 cells, imports `google.colab` in its last cell, saved outputs present). **XGBoost: ❌ Missing** — 0 hits for `xgboost`/`xgb` in any source file or notebook cell. The only "supervised" mention is README prose ("F1 1.0, 99.9% precision … `triple_residual`") and `triple_residual` appears **nowhere** in the code. The *physics-informed features* are real (see G5/G2). |
| **G4** Dockerized FastAPI + React GUI + Pytest suites | **Partial** | FastAPI ✅, React/Next.js GUI ✅ (present, not run here). **Dockerized ❌ (no Dockerfile). Pytest ❌ (zero tests).** |
| **G5** Runs on existing GNSS equipment without new hardware | **Partial — supported by design, not yet by measurement or docs** | See detail below. |
| **G6** "Lead AI Researcher for the NyneOS/IIT Delhi Anti-Spoofing AI Hackathon (Apr 2026)" | **Reword** (per your instruction — not verified) | Web search found **no** public page for a "NyneOS/IIT Delhi" hackathon, consistent with it not being a hackathon you led. The repo itself says "Team 1forAll … 1forAll Open Innovation Hackathon, SRMIST". Suggested wording is in `RESUME_FACTS.md` (to be written in the build step). Dataset credit: see below. |

### G2 in detail

**Record counts (measured, `docs/audit/output/a1_data_facts.txt`):**

| Item | Claimed | Measured |
|---|---|---|
| Telemetry records | "120K+" | `train.xls` has **65,535 raw rows** (the legacy `.xls` row cap — the file is almost certainly truncated at 65,535). After dropping 8 placeholder rows and **40,802 no-lock (PRN=0) rows**, **24,725 usable training rows** over **6,758 epochs**. The hackathon `test.xls` (also 65,535 raw → 29,926 usable per notebook output) is not in the repo. "120K+" is only reachable as train+test **raw sheet rows (≈131K)**, most of which are empty no-lock rows. **Honest figure: 24,725 usable training records (65,535 raw rows).** |
| Satellite channels | 8 | **8** (`ch0`–`ch7`; 7 distinct PRNs: 2, 6, 11, 12, 17, 19, 25) ✅ |
| Features | 13 | **Not 13 in the model.** The raw receiver record has **13 measurement fields** (PRN, Carrier_Doppler_hz, Pseudorange_m, RX_time, TOW, Carrier_phase, EC, LC, PC, PIP, PQP, TCD, CN0) — which matches the source dataset's "13 features extracted from eight parallel channels". The **model consumes 35 features**: 10 base + 11 physics-engineered + 14 rolling (window 10). `len(ALL_MODEL_FEATURES) == 35`, all unique; `model.n_features_in_ == 35`. |
| Model | unsupervised Isolation Forest | ✅ `Pipeline(StandardScaler → IsolationForest(n_estimators=200, contamination=0.01, random_state=42))`, trained on the all-genuine set. |

**How labels were used to evaluate an unsupervised model:** they were **not**. `spoofed` is 0 for every training row, so there is nothing to score against. The notebook reports only (a) "% flagged" on the training data (1.00%, which is just `contamination=0.01` echoed back), (b) 5.03% flagged on the unlabelled hackathon test set, and (c) a hand-made stress test (cell 17) that reports a "flag rate" of 13.55% and prints "SUCCESS" because it exceeds 5.03%. **Flag rate is not precision**; the notebook never computes precision, recall or F1.

**Leakage / split problems found:**
1. The model is fit on **100% of the rows** — there is no train/test split. The stress test samples its 2,000 rows **from the training set** (`df.sample(2000)`), so the "validation" rows were seen during fitting.
2. The row sample is **shuffled** before rolling features are computed, which breaks the temporal windows (an artefact visible below as an 18.5% false-positive rate on genuine rows).
3. The injected "attack" (+350–600 Hz Doppler, +800–1200 m pseudorange, +2–5 dB CN0) is **small relative to natural variation** (std: Doppler 1,746 Hz, pseudorange 776,678 m, CN0 2.42 dB-Hz), so marginals barely move; only the *relationships* between fields betray it.

**Re-run results (script `a2_eval_probe.py`, `a3_sustained_and_edge.py`; labels are the *injected* rows; precision is for the spoofed class):**

| Protocol | Model | Precision | Recall | F1 | Confusion (TP / FP / FN / TN) |
|---|---|---|---|---|---|
| A. Notebook protocol (2,000 shuffled train rows, 200 injected), seed 0 | shipped `.pkl` (trained on these rows) | 0.148 | 0.290 | 0.196 | 58 / 333 / 142 / 1467 |
| A, seed 1 | shipped | 0.157 | 0.320 | 0.211 | 64 / 344 / 136 / 1456 |
| A, seed 2 | shipped | 0.133 | 0.225 | 0.167 | 45 / 294 / 155 / 1506 |
| B. Time split (first 70% of each channel = train, last 30% = held-out, 7,413 rows), 10% scattered attacks, seed 0 | re-fit IF, same hyper-params | 0.166 | 0.124 | 0.142 | 92 / 461 / 649 / 6211 |
| B, seed 1 | re-fit | 0.178 | 0.119 | 0.142 | 88 / 407 / 653 / 6265 |
| B, seed 2 | re-fit | 0.232 | 0.155 | 0.186 | 115 / 381 / 626 / 6291 |
| B4. Time split, **sustained** attacks (5 × 100 contiguous rows), seed 0 | re-fit | 0.701 | 0.328 | 0.447 | 164 / 70 / 336 / 6843 |
| B4, seed 1 | re-fit | 0.261 | 0.062 | 0.100 | 31 / 88 / 469 / 6825 |
| B4, seed 2 | re-fit | 0.611 | 0.276 | 0.380 | 138 / 88 / 362 / 6825 |
| B2. Pure-genuine held-out (no attacks) | re-fit | — | — | — | **false-positive rate 1.19%** (matches `contamination`) |

Caveats on these numbers: they use **synthetic injected** attacks (the only labels available), not the dataset's real spoofing labels; row-level labels penalise neighbours of an attacked row because rolling windows smear the attack over ~10 rows. They are **not** a replacement for evaluating on real labelled spoofing data. They *are* enough to say: **94% precision is not supported by anything in this repo, and the real figure on a comparable protocol is far lower.**

**Where "94%" might have come from:** the repo's README says "operational accuracy is designed to stabilize around 92–95%" (an aspiration, not a result) and "F1 1.0 / 99.9% precision … Label 3 … `triple_residual`" (a supervised result whose code is not in the repo). The *source* Mendeley dataset does carry labelled attack classes (see below); a supervised model on those labels is the only place a high precision number could be honestly produced. **Recommendation:** do not use "94% precision" until it is re-produced by `evals/run.py` on labelled data.

### G5 in detail — what supports "no new hardware"

| Evidence | Finding |
|---|---|
| Inputs are standard receiver fields | The model needs 13 raw per-channel fields (`time, channel, PRN, Carrier_Doppler_hz, Pseudorange_m, RX_time, TOW, Carrier_phase, EC, LC, PC, PIP, PQP, TCD, CN0`). `Carrier_Doppler`, `Pseudorange`, `Carrier_phase`, `CN0`, `PRN`, `TOW` are standard observables (RINEX-style). **`EC/LC/PC/PIP/PQP/TCD`** (early/late/prompt correlators, I/Q prompt powers, tracking carrier Doppler) are **tracking-loop internals** that typical NMEA/RINEX output does **not** expose — they need a receiver that exposes correlator outputs (software-defined or research-grade). So "uses only NMEA/RINEX fields" would be **false**; "uses receiver tracking-loop outputs, no extra antennas/RF front-end" is accurate. |
| CPU-only, no GPU | ✅ scikit-learn only; nothing GPU-related. |
| Model size | **2,286,864 bytes (2.2 MB)** `gnss_anti_spoofing_model.pkl`. |
| Inference latency (model only, 1 thread, CPU, 20 runs) | batch=1: **p50 3.85 ms / p95 3.93 ms**; batch=100: 4.01 / 4.07 ms (~25K rows/s); batch=1,000: 6.40 / 6.48 ms (~156K rows/s); batch=10,000: 27.1 / 27.4 ms (~369K rows/s). Excludes feature engineering and HTTP. |
| Memory | Peak RSS **374 MB** for the *whole audit script* (includes loading the 12 MB `.xls` through pandas/xlrd) — **not** a clean inference-only number; must be re-measured in isolation. |
| Software-only, no new sensors | ✅ by design (README "Software-Only Deployment"), and consistent with the code, which is a pure software consumer of the receiver log. |
| What is **not** supported | No NMEA/RINEX parser exists; no export to a lightweight runtime (ONNX etc.); no on-device packaging; no latency measured end-to-end through the API. The "after feedback" part of the claim has no trace in the repo. |

Verdict: **Partial.** True in spirit (software-only, CPU, 2.2 MB, ms latency), but needs the measurements re-run properly (E2E, isolated memory) and **must not** claim NMEA/RINEX compatibility.

### G6 — dataset licence and credit

- Both READMEs say the data is the "UAV-GS-Dataset". I could not find a dataset by that name. The data matches (8-channel receiver, 13 features, authentic + 3 attack classes) the Mendeley Data set **"A DATASET for GPS Spoofing Detection on Unmanned Aerial System"**, by **Ghilas Aissou** (University of North Dakota), v3, 18 Oct 2022, **DOI [10.17632/z7dj3yyzt8.3](https://doi.org/10.17632/z7dj3yyzt8.3)**, licence **CC BY 4.0** (as stated on its Mendeley page: <https://data.mendeley.com/datasets/z7dj3yyzt8/3>).
- **Status: likely but unconfirmed.** `train.xls` was handed out by the hackathon organisers and may be a derivative/re-labelled subset (its labels are all 0). Please confirm the provenance with your team before the README states it as fact. CC BY 4.0 requires attribution (author, title, DOI, licence, and a note of changes), which the README currently lacks entirely.
- The repo's own code is declared MIT but has no `LICENSE` file.
- If `train.xls` really is CC BY 4.0 material, committing it is allowed with attribution. If it is hackathon-organiser material, the safer route is a documented download step instead of redistributing it. (To decide with you.)

---

## 3. Step 2 — What GNSS should add for the FDE role (confirmed and adjusted)

| Req | Requirement | Already covered by | GNSS opportunity (confirmed / adjusted after audit) |
|---|---|---|---|
| **R2** | Production AI on **Google Cloud** | Drishti, NutriLens | **Confirmed.** Cloud Run deploy of the detector API (scale-to-zero). Today there is no Dockerfile, no health endpoint, a hard-coded `localhost` frontend URL and open CORS, so this is real work, not a formality. |
| **R8** | High-quality code: tests, CI, review standards | Drishti, NutriLens | **Confirmed, higher priority than expected.** Repo has **0 tests, 0 CI, 0 types**, an unpinned `requirements.txt`, duplicate files and a known cleaning bug. A pytest suite, ruff + mypy, pre-commit and GitHub Actions are all net-new. |
| **R10** | Evaluation and debugging for accuracy, safety, latency | Drishti, NutriLens | **Confirmed and reframed.** The existing "accuracy" claim is unsupported, so the reproducible eval is the most valuable item: honest split, real P/R/F1, **plus** latency/throughput. Because the repo has no real spoof labels, the eval has to either (a) obtain the labelled source dataset, or (b) use clearly labelled synthetic injection. Needs your decision (see PLAN). |
| — | Edge/cost-aware deployment ("no new hardware") | — | **Confirmed.** Numbers already partly measured (2.2 MB, ~4 ms/100 rows); formalise in a script and report model size, isolated peak memory, p50/p95 and rows/s. State precisely which receiver fields are needed (tracking-loop outputs, not just NMEA). |
| R4, R3, R6 | Agents, RAG, LLM metrics | Drishti, NutriLens | **Skip.** No natural reason for an LLM here. |
| **New** | Honest claim hygiene | — | **Add:** reword G1/G2/G3/G4/G6 on the resume; fix README (two inconsistent READMEs, phantom `LICENSE`, phantom `triple_residual`), credit the dataset (CC BY 4.0). |

---

## 4. Evidence index

| File | What it is |
|---|---|
| [`docs/audit/a1_data_facts.py`](audit/a1_data_facts.py) → [`output/a1_data_facts.txt`](audit/output/a1_data_facts.txt) | Record, channel, label and feature counts |
| [`docs/audit/a2_eval_probe.py`](audit/a2_eval_probe.py) → [`output/a2_eval_probe.txt`](audit/output/a2_eval_probe.txt) | Notebook-protocol and time-split precision/recall/F1 |
| [`docs/audit/a3_sustained_and_edge.py`](audit/a3_sustained_and_edge.py) → [`output/a3_sustained_and_edge.txt`](audit/output/a3_sustained_and_edge.txt) | Sustained-attack eval; model size, latency, RSS |
| [`docs/audit/output/env.txt`](audit/output/env.txt) | Package versions used |

Reproduce: `cd GNSS_Security_Package && python ../docs/audit/a2_eval_probe.py` (needs `pip install -r backend/requirements.txt xlrd`).

## 5. Can't verify (needs tools not on this machine, or the user)

- React/Next.js GUI install, build and run (**Node not installed**).
- Docker image build/run (**Docker not installed**).
- Anything on Google Cloud (**`gcloud` not installed**; also needs project ID, region, budget).
- The hackathon `test.xls`, `submission.csv` regeneration, and the "supervised F1 1.0 / 99.9% on Label 3" README claim (no code or labelled data in the repo).
- Whether `train.xls` is the Mendeley/Aissou data or a hackathon derivative.
