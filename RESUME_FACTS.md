# Resume facts: GNSS Security Shield

Rule used here: a fact is listed as verified only if code ran and produced it. Statements about code that was written but has not been executed are labelled as such. Numbers marked provisional came from the audit scripts, not from the maintained `make eval` and `make bench` commands, and should be replaced by those generated reports before they go on a resume.

## 1. Verified facts

| Fact | Proof |
|---|---|
| The training sheet has **65,535 raw rows**; after dropping placeholder rows and rows without satellite lock there are **24,725 usable, all genuine** | `docs/audit/output/a1_data_facts.txt` (raw shape, label counts); `docs/audit/output/a2_eval_probe.txt` ("clean genuine rows: 24725"); notebook cell 3 output |
| The receiver has **8 channels** (`ch0`–`ch7`) and the data covers **7 satellites** (PRN 2, 6, 11, 12, 17, 19, 25) | `docs/audit/output/a1_data_facts.txt` |
| Each record has **13 measurement fields** (`PRN`, `Carrier_Doppler_hz`, `Pseudorange_m`, `RX_time`, `TOW`, `Carrier_phase`, `EC`, `LC`, `PC`, `PIP`, `PQP`, `TCD`, `CN0`); the model uses **35 features**: 10 base, 11 engineered, 14 rolling | `docs/audit/output/a1_data_facts.txt` ("base 10 eng 11 roll 14 total 35"); `src/gnss_shield/features.py` |
| The model is `StandardScaler` + `IsolationForest` (200 trees, contamination 0.01, random state 42), trained **unsupervised on genuine rows only** | `models/gnss_iforest.manifest.json`; the model's repr printed during the audit; notebook cell 8 |
| The model file is **2,286,864 bytes** (about 2.2 MB) | `docs/audit/output/a3_sustained_and_edge.txt`; `ls -l models/gnss_iforest.pkl` |
| An Isolation Forest prototype exists as a Colab-exported notebook | `notebooks/GNSS_Hackathon.ipynb` |
| The original repository claimed no labelled evaluation: the notebook reports only flag rates | `docs/AUDIT.md` section 2 (G2) |
| **Provisional.** On synthetic attack injection (the notebook's perturbation of Doppler, pseudorange and CN0) the shipped model scored precision 0.13–0.16 and recall 0.23–0.32 over three seeds; with a time-ordered split, scattered attacks gave precision 0.17–0.23 and recall 0.12–0.16, and sustained attacks gave precision 0.26–0.70 and recall 0.06–0.33; false-alarm rate on genuine held-out rows was 1.19% | `docs/audit/output/a2_eval_probe.txt`, `a3_sustained_and_edge.txt` |
| **Provisional.** Model-only CPU latency, one thread, p50: 3.85 ms for 1 row, 4.01 ms for 100 rows, 6.40 ms for 1,000 rows, 27.1 ms for 10,000 rows (about 369,000 rows/s at 10,000). Measured with scikit-learn 1.9.1 loading a 1.6.1 pickle | `docs/audit/output/a3_sustained_and_edge.txt` |

## 2. Written but not executed (do not claim as working)

| Item | Where | Becomes claimable when |
|---|---|---|
| 90 test functions across 8 files | `tests/` | `make test` passes; quote the pass count and the coverage figure from that run (ROADMAP item 1) |
| Dockerfiles, Compose file, CI workflow | `Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml` | Images build and CI is green (items 1, 3, 4) |
| Reproducible evaluation, benchmark and HTTP latency script | `evals/run.py`, `evals/bench.py`, `evals/bench_http.py` | The generated `RESULTS.md`, `EDGE.md` and `HTTP.md` exist (items 6, 7, 8) |
| Isolation Forest vs XGBoost comparison on real labels | `evals/compare.py`, `src/gnss_shield/comparison.py` | `COMPARE.md` exists, produced from real labelled data (items 11, 12) |
| Cloud Run deployment scripts | `deploy/` | A deploy, `make smoke` and teardown have been run and a URL exists (item 15) |
| API hardening: validation, `/health`, `/ready`, batch endpoint, API-key auth, JSON logging | `src/gnss_shield/api.py` | Tests pass (item 1) |

## 3. Claims to remove or reword

| ID | Original | Problem | Use now | Use after |
|---|---|---|---|---|
| G1 | Python, scikit-learn, FastAPI, React, Docker | Docker image never built; the GUI is Next.js on React | "Python, scikit-learn, FastAPI, Next.js (React)" | Add "Docker" after ROADMAP item 4 |
| G2 | "94% precision … 120K+ telemetry records … 13 features from 8 satellite channels" | No source for 94%; the repo had no labelled evaluation; 24,725 usable rows, not 120K+; the model uses 35 features | "Built an unsupervised Isolation Forest spoofing detector trained on 24,725 genuine receiver-telemetry rows from an 8-channel receiver, engineering 13 raw receiver fields into 35 physics-informed features" | Add the precision, recall and F1 from `evals/results/RESULTS.md` with the words "on a time-ordered split with synthetic attack injection" (item 6) |
| G3 | "physics-informed XGBoost pipeline and an Isolation Forest Colab notebook" | XGBoost exists only as comparison code that has not been run on labelled data | "Isolation Forest prototype in a Colab notebook" | Mention XGBoost only after `evals/results/COMPARE.md` exists (ROADMAP item 12), e.g. "compared an unsupervised Isolation Forest with a supervised XGBoost baseline on real labelled attacks" with the figures from that file |
| G4 | "Dockerized FastAPI service with a React GUI, backed by Pytest suites" | Docker and tests not yet run | "FastAPI service with a Next.js dashboard and a pytest suite" | "…with N tests at X% coverage, built into Docker images" using the figures from the runs (items 1, 4) |
| G5 | "runs on existing GNSS equipment without new hardware, after feedback" | The model needs tracking-loop outputs, which NMEA and standard RINEX files do not contain; no feedback trace in the repo | "Designed as a software-only, CPU-only detector (2.2 MB model) that scores receiver tracking-loop outputs, with no added RF hardware" | Add latency, throughput and peak memory from `evals/results/EDGE.md` (item 7) |
| G6 | "Lead AI Researcher for the NyneOS/IIT Delhi Anti-Spoofing AI Hackathon (Apr 2026)" | Inaccurate: it was your own SRM college hackathon using a public dataset | "Built an unsupervised GNSS spoofing detector for the 1forAll Open Innovation Hackathon at SRMIST, using a public GNSS spoofing dataset" | Name the dataset (Aissou, Mendeley, CC BY 4.0) once ROADMAP item 10 confirms the sheet comes from it |

Do not use: "94% precision", "120K+ records", "XGBoost", "Lead AI Researcher", "NyneOS", "IIT Delhi", "works with NMEA/RINEX", "deployed on Google Cloud" (until item 15 produces a URL).
