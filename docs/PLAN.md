# GNSS Security Shield — Plan (Step 3)

**Historical document.** This plan was written before the build and describes the original layout. What is built and what remains is tracked in [`ROADMAP.md`](ROADMAP.md). Based on [`AUDIT.md`](AUDIT.md). Branch: `feat/fde-upgrade`; small commits; PR at the end; no merge until the owner says so.

Effort: S ≈ <½ day, M ≈ ½–1.5 days, L ≈ 2+ days. Impact is for the FDE application.

---

## 0. Decisions I need from you first

| # | Decision | My recommendation |
|---|---|---|
| D1 | **Labelled data for a real eval.** The repo has *no* spoofed labels (`spoofed`=0 for all 24,725 rows), so precision/recall can't be measured on real attacks. Option A: download the labelled source dataset (Aissou, Mendeley, **CC BY 4.0**, DOI 10.17632/z7dj3yyzt8.3; I'd save it under a git-ignored `data/` folder, size not stated on the page — I'll check before downloading and ask you to confirm filename, source and size). Option B: no download; evaluate only on clearly-labelled **synthetic** injection. | **A**, if your team confirms `train.xls` derives from that dataset. It is the only way to produce an honest precision figure *and* a real XGBoost comparison. Without it I'd recommend **dropping XGBoost from the resume** rather than faking it. |
| D2 | **XGBoost.** Resume says it exists; it doesn't. Build one (supervised, physics-informed features, side by side with Isolation Forest) **only if D1 = A**. | Build if D1 = A; otherwise Reword. |
| D3 | **Tooling on this machine:** Node, Docker, `gcloud` aren't installed. I'd like to `brew install node` (GUI build/lint) and run the Docker/Cloud steps via **Cloud Build** (no local Docker needed) or you install Docker Desktop. | Node via brew; deploy with `gcloud run deploy --source`/Cloud Build to avoid Docker Desktop. Tell me if you prefer otherwise. |
| D4 | **Frontend hosting:** Cloud Run (second service, scale-to-zero) vs static host (Firebase Hosting / GCS). The GUI is Next.js 14 and uses `axios` to `localhost:8000` today. | Cloud Run for both (one `make deploy`, same project, both scale to zero); API URL via `NEXT_PUBLIC_API_URL`. |
| D5 | **Dataset in repo:** keep `train.xls` (12.6 MB) or replace with a documented download script + attribution? | Keep nothing large in git: move to `data/` + `scripts/download_data.sh`, credit Aissou in README. Confirm provenance first (unconfirmed). |
| D6 | **GCP project ID, region, budget** (needed before any cloud step; I'll set a budget alert; Cloud Run scale-to-zero keeps cost ≈ 0). | Provide when we reach step 6 — I won't touch GCP before. |
| D7 | **Repo layout:** flatten `GNSS_Security_Package/` into a conventional layout (`backend/` → `src/gnss_shield/`, `tests/`, `evals/`, `deploy/`) and delete the duplicate bundle / stray files? | Yes — do it in its own commit so history stays reviewable. |

---

## 1. Fix — things that are broken or wrong today

| Order | Item | Effort | Impact | Notes |
|---|---|---|---|---|
| F1 | **Leakage & dishonest eval:** no train/held-out split; stress test samples training rows; "flag rate" reported as success; rolling features computed on shuffled rows. Replace with a time-ordered, per-channel split and real P/R/F1. | M | **High** | Core of the "reproducible evaluation" must-have (see B1). |
| F2 | `clean_gnss` doesn't drop `chX` placeholder rows (24,733 vs 24,725) and lets NaN PRN rows reach the model. Single shared implementation used by training, eval and API. | S | High | Training/serving skew is the root cause behind several audit findings. |
| F3 | **Unpinned deps and pickle version drift** (model saved under sklearn 1.6.1, installs 1.9.1 → `InconsistentVersionWarning`). Pin versions, **retrain** under the pinned version via `make train`, record versions/hash next to the artefact. Drop the second duplicate `.pkl`. | S | High | Pin Python 3.12 in Docker (3.14 was only the local interpreter). |
| F4 | **Global mutable `history_manager`** shared across all clients in single-row `/predict`. Make state per request / per session ID, or require batches. | S–M | Med | Directly relevant to concurrency on Cloud Run. |
| F5 | Open CORS (`*` + credentials). Configurable allow-list from env. | S | Med | |
| F6 | Frontend hard-coded `http://localhost:8000` ×4. Use `NEXT_PUBLIC_API_URL`. | S | Med | Needed for deployment. |
| F7 | Repo hygiene: duplicate model pickle, `test_result.json` (0 B), `dirty_test.csv`/`test_nan.json`, `Know your project.md`, two conflicting READMEs, developer-specific absolute path in the run guide, missing `LICENSE`. | S | Med | Part of the layout commit (D7). |

## 2. Build — new things

Order follows your must-haves: **reproducible eval → clean-clone run + tests/CI → Cloud Run deploy → edge measurements → docs.**

| Order | Item | Effort | Impact | Details |
|---|---|---|---|---|
| B1 | **Reproducible evaluation** `evals/run.py` → `evals/results/RESULTS.md` | M | **High** | Time-ordered per-channel split; precision/recall/F1/confusion matrix + split method + seeds; Isolation Forest **and** (if D1=A) XGBoost side by side. Labelled real data if available; otherwise synthetic injection, **labelled as synthetic** in the file. Reports whatever the numbers are. Unsupervised IF is trained on genuine rows only; labels are used **only** to score it (and to train XGBoost). Optionally reports score-based metrics (ROC-AUC/PR-AUC) so the threshold isn't the only story. |
| B2 | **Makefile** + `.env.example` + data script | S | High | `make up` (API + GUI), `make train`, `make eval`, `make test`, `make lint`, `make bench`, `make deploy`, `make teardown`. Clean clone → running in <10 min, verified from a fresh clone before the PR. |
| B3 | **Tests (pytest) + coverage** | M | High | Features (physics formulas with hand-computed cases, rolling windows, NaN/inf handling), cleaning (chX rows, PRN=0), model loading (version/hash check), API (health, validation, batch, auth, error paths, per-request state), eval smoke test on a tiny fixture. Coverage reported from a real run. No fake numbers: I'll report whatever it is. |
| B4 | **Quality gates:** ruff, mypy (typed), pre-commit, **GitHub Actions** CI (lint, type, test+coverage, frontend lint/build, Docker build) | M | High | Python 3.12 matrix; pinned action versions. |
| B5 | **API hardening:** Pydantic models for rows (field ranges), `POST /predict/batch`, `/health` + `/ready`, structured JSON logging with request IDs, API-key auth (`X-API-Key` from Secret Manager) or Cloud Run IAM, request size limit, configurable CORS | M | High | Keep existing `/predict`, `/predict/file`, `/scan` working for the GUI (backwards compatible); GUI sends the key via env. |
| B6 | **Cloud Run deploy:** multi-stage Dockerfile, non-root, `min-instances=0`, `deploy/` scripts (`deploy.sh`, `teardown.sh`), Secret Manager for the API key, budget alert; React GUI as a second service | M–L | **High** | Needs D3/D6. Uses Cloud Build so no local Docker is required. Teardown script verified. |
| B7 | **Deployment-readiness measurements** `make bench` → `evals/results/EDGE.md` | S–M | High | Model size on disk, isolated peak RSS (separate process, inference-only), CPU-only latency p50/p95/p99 for batch sizes 1/100/1,000, throughput rows/s, **end-to-end** API latency (local + Cloud Run), cold-start time, plus the exact receiver-field list. Optional ONNX export **only if** it is quick and measurably helps (I'd skip unless numbers show a gain). |
| B8 | **XGBoost physics-informed pipeline** (only if D1 = A) | M | Med | Same feature set, supervised on real labels, same split. Included in B1's table. |
| B9 | **Docs:** single README (pitch, Mermaid architecture, results table straight from `RESULTS.md`/`EDGE.md`, quickstart <10 min, demo screenshot/GIF, dataset credit), `docs/ARCHITECTURE.md` (why unsupervised; physics-informed features; no-new-hardware design **incl. the honest limit that EC/LC/PC/PIP/PQP/TCD are tracking-loop outputs, not NMEA**), `LICENSE`, `RESUME_FACTS.md` | M | High | Screenshot needs Node + a running GUI. |

## 3. Re-measure

| Item | Effort | Impact | Notes |
|---|---|---|---|
| Precision / recall / F1 / confusion matrix | — | High | Replaced by B1; the 94% figure is retired unless B1 reproduces it. |
| Record, feature, channel counts | S | High | Already measured: 65,535 raw rows → **24,725 usable**, **8 channels**, **13 raw fields → 35 model features**; will be generated by the eval script into `RESULTS.md`, not hand-typed. |
| Latency, throughput, size, peak memory | S | High | Part of B7. Audit numbers (2.2 MB, ~4 ms/100 rows) are provisional because memory was not isolated. |
| Test coverage | S | Med | From B3. |

## 4. Skip

| Item | Why |
|---|---|
| Agents, RAG, LLMs (R3, R4, R6) | Covered by Drishti/NutriLens; no natural fit here. |
| NMEA/RINEX parser | Doesn't match the model's inputs (tracking-loop correlators). Document the limitation instead. |
| ONNX / quantisation by default | 2.2 MB model, ~4 ms/100 rows already; only do it if B7 shows a real gain. |
| Rewriting the frontend, new GUI features, WebSockets, maps | Not needed for FDE; only the URL/env fix and a screenshot. |
| Hyper-parameter tuning / new model families (OC-SVM, deep nets) | Over-building; the point is a verifiable pipeline, not a new SOTA. |

## 5. Reword (resume / README) — final wording goes in `RESUME_FACTS.md`

| ID | Current | Problem | Direction |
|---|---|---|---|
| G2 | "94% precision … 120K+ records … 13 features from 8 channels" | Not reproducible; 24,725 usable rows (65,535 raw); model uses 35 features derived from 13 raw fields; no labelled eval existed | Use only numbers `evals/results/RESULTS.md` produces; say "13 raw receiver fields across 8 channels → 35 engineered features". |
| G3 | "physics-informed XGBoost" | Doesn't exist (yet) | Keep only if B8 ships; otherwise remove. |
| G4 | "Dockerized … Pytest" | Neither exists (yet) | Becomes true after B3/B6; cite real coverage. |
| G5 | "runs on existing GNSS equipment without new hardware" | Needs correlator outputs, not NMEA | "Software-only, CPU-only detector (2.2 MB model, ms-level inference) that consumes receiver tracking-loop outputs; no extra RF hardware." + measured numbers. |
| G6 | "Lead AI Researcher for the NyneOS/IIT Delhi Anti-Spoofing AI Hackathon (Apr 2026)" | Inaccurate | "Built an unsupervised GNSS spoofing detector for our SRM college hackathon, using the public Anti-Spoofing hackathon dataset (Aissou, Mendeley, CC BY 4.0)" — dataset naming to be confirmed. |

---

## 6. Execution order (with commits)

1. **Repo restructure + hygiene** (F7, D7, F2, F3) — one commit each.
2. **Eval** (B1, B8, F1) → `RESULTS.md`.
3. **Makefile / env / data script / clean-clone check** (B2); **tests + CI + lint/types** (B3, B4).
4. **API hardening + frontend env URL** (B5, F4–F6).
5. **Cloud Run** (B6) — after you give project ID / region / budget.
6. **Edge measurements** (B7).
7. **Docs + `RESUME_FACTS.md`** (B9).
8. Show you the summary; **push the branch and open the PR only after your review**; no merge until you say so.

Total effort estimate: ≈ 7–10 working days of effort if D1 = A (XGBoost + real labels); ≈ 6–8 if not.

## 7. Risks

- **The honest number may be lower than the resume** (the audit already suggests so). I'll report it as-is.
- **Real labels may not be obtainable** (D1) → XGBoost and "precision" claims get reworded instead.
- **Sustained spoofing vs per-row labels:** row-level precision is harsh because rolling windows smear attacks; the eval will state its labelling convention and also report event-level detection if useful.
- **Cloud costs:** scale-to-zero + budget alert; teardown script provided.
- **Python 3.14 locally vs 3.12 in Docker/CI:** pinned and tested on 3.12.
