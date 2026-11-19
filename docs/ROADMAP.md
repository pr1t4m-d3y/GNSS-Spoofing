# Roadmap

Everything not finished lives in this file, and only here. The code contains no placeholders for these items; each one is simply not built yet or not yet executed. For each: what it needs, and when it counts as done.

The code and tests in this branch were written without being executed in this working session, so nothing in the repository has a recorded test result yet. Items 1 to 4 turn that into evidence.

## First execution

| # | Item | Needs | Done when |
|---|---|---|---|
| 1 | Run the Python quality gates for the first time and fix what they find | Python 3.12 and `make install-dev` | `make lint`, `make typecheck` and `make test` pass locally and in GitHub Actions; the real coverage figure is read from that run |
| 2 | Resolve the pinned requirements on a clean install | Same as 1 | `requirements.txt` and `requirements-dev.txt` install together without conflicts, and the pins are adjusted if they do not |
| 3 | Build and lint the dashboard | Node 20; `npm ci` | `npm run lint`, `npm run typecheck` and `npm run build` pass; the `/api` proxy route is exercised against a running API |
| 4 | Build both Docker images and run the stack | Docker | `make up` starts both services; `/health` and `/ready` answer 200; the dashboard analyses `examples/attack_scenario_sudden.csv` |
| 5 | Format the codebase and turn on the format check in CI | `make format` | `ruff format --check .` passes and is added to the CI workflow |

## Evidence the README points to

| # | Item | Needs | Done when |
|---|---|---|---|
| 6 | Generate `evals/results/RESULTS.md` | `make eval` on `data/train.xls` | The file is committed, reports precision, recall, F1, ROC-AUC, average precision, confusion matrices and false-alarm rate, and the README links to it |
| 7 | Generate `evals/results/EDGE.md` | `make bench` | The file is committed with model size, peak memory and CPU latency and throughput per batch size |
| 8 | Measure end-to-end latency over HTTP, locally and on Cloud Run, including cold start | Items 4 and 11 | A script and its generated report exist; numbers are recorded next to the host they came from |
| 9 | Demo screenshot or recording of the dashboard | Item 4 | An image or GIF is committed and embedded in the README |

## Model and data

| # | Item | Needs | Done when |
|---|---|---|---|
| 10 | Confirm where `data/train.xls` comes from and whether it may be redistributed | An answer from the hackathon team | `data/README.md` and the README state the source as fact, or the sheet is replaced by a download script |
| 11 | Obtain the labelled source dataset (CC BY 4.0, DOI 10.17632/z7dj3yyzt8.3) | Permission to download it; the file name, source and size are confirmed first | The files are in a git-ignored folder and `evals/run.py` can read them |
| 12 | Evaluate against the real labelled attack classes (simplistic, intermediate, sophisticated) | Item 11 | `RESULTS.md` has a section per attack class, produced by the same split protocol |
| 13 | Physics-informed XGBoost model, supervised on real labels, compared with the Isolation Forest on the same split | Item 11 | `evals/run.py` reports both models side by side; until then the repository makes no XGBoost claim |
| 14 | Calibrate the decision threshold against labelled data | Item 11 | The threshold and its trade-off curve are documented, replacing the fixed `contamination` setting |
| 15 | Retrain with `make train` under the pinned scikit-learn and compare with the committed model | Items 1 and 2 | The manifest records the new hash, or the committed model is kept with the reason noted |
| 16 | Replace the stress-test cell in `notebooks/GNSS_Hackathon.ipynb` (it reports a flag rate as success and samples its rows from the training set) | Notebook editing | The cell points to `make eval` or is removed |

## Deployment

| # | Item | Needs | Done when |
|---|---|---|---|
| 17 | Deploy to Cloud Run | GCP project ID, region, billing account and budget; authenticated `gcloud` | `make budget` and `make deploy` print the API and dashboard URLs, `/ready` answers 200, and `make teardown` is run once to confirm it removes everything. Known unknowns to check: Cloud Build service-account permissions for source deploys, the `--filter-projects` value accepted by `gcloud billing budgets create`, and organisation policy on `--allow-unauthenticated` |
| 18 | Tune Cloud Run memory, CPU and concurrency | Items 7 and 8 | `deploy/deploy.sh` uses values justified by the benchmark (the current 1Gi, 40 concurrent requests are not measured) |
| 19 | Put the deployed dashboard behind a login | Identity-Aware Proxy or an auth layer | The dashboard is not open to anyone with the URL |

## Product features not built

These were removed from the dashboard because they did nothing; they return when they work.

| # | Item | Needs | Done when |
|---|---|---|---|
| 20 | Operator-adjustable alert sensitivity | A threshold parameter in the API and a control in the UI | Changing it changes which rows are flagged, with a test |
| 21 | Browser notifications on detection | Notification permission flow in the UI | A flagged row raises a notification when enabled |
| 22 | Per-satellite elevation and health | Ephemeris or position data, which the receiver fields do not contain | A data source is chosen and the satellite view shows real values |
| 23 | NMEA and RINEX ingestion | A target receiver that exposes correlator and I/Q values, and a field mapping | An adapter converts that receiver's output to the required fields, with a test fixture |
| 24 | Shared session store for multi-instance deployments | A decision that exact cross-request windows matter | Sessions survive across instances, or the limit is accepted and documented |

## Other

| # | Item | Needs | Done when |
|---|---|---|---|
| 25 | `LICENSE` file | The copyright holder name from the owners | The file is added and the README states the licence |
| 26 | Frontend automated tests | A test runner choice | Core behaviours (`deriveSatellites`, `errorMessage`, the proxy route) are covered |
