# Roadmap

Everything not finished lives in this file, and only here. The code contains no placeholders for these items; each one is either not built yet or built but not yet executed. For each: what it needs, and when it counts as done.

The code and tests in this repository were written without being executed, so nothing has a recorded test result yet. Items 1 to 5 turn that into evidence.

## First execution

| # | Item | Needs | Done when |
|---|---|---|---|
| 1 | Run the Python quality gates for the first time and fix what they find | Python 3.12 (see `.python-version`) and `make install-dev` | `make lint`, `make typecheck` and `make test` pass locally and in GitHub Actions; the real test count and coverage figure are read from that run |
| 2 | Resolve the pinned requirements on a clean install | Same as 1 | `requirements.txt` and `requirements-dev.txt` install together without conflicts, and the pins are adjusted if they do not |
| 3 | Build and lint the dashboard | Node 20; `npm ci` | `npm run lint`, `npm run typecheck` and `npm run build` pass; the `/api` proxy route is exercised against a running API |
| 4 | Build both Docker images and run the stack | Docker | `make up` starts both services; `/health` and `/ready` answer 200; the dashboard analyses `examples/attack_scenario_sudden.csv` |
| 5 | Format the codebase and turn on the format check in CI | `make format` | `ruff format --check .` passes and is added to the CI workflow |

## Evidence the README points to

| # | Item | Needs | Done when |
|---|---|---|---|
| 6 | Generate `evals/results/RESULTS.md` | `make eval` on `data/train.xls` | The file is committed and the README links to it |
| 7 | Generate `evals/results/EDGE.md` | `make bench` | The file is committed with model size, peak memory and CPU latency and throughput per batch size |
| 8 | Generate `evals/results/HTTP.md`, locally and against the deployed API | `make bench-http` (items 4 and 15 for the deployed run) | The reports are committed, with the host each came from named in the file |
| 9 | Demo screenshot or recording of the dashboard | Item 4 | An image or GIF is committed and embedded in the README |

## Model and data

| # | Item | Needs | Done when |
|---|---|---|---|
| 10 | Confirm where `data/train.xls` comes from and whether it may be redistributed | An answer from the hackathon team | `data/README.md` and the README state the source as fact, or the sheet is replaced by a download script |
| 11 | Obtain the labelled source dataset (CC BY 4.0, DOI 10.17632/z7dj3yyzt8.3) | Permission to download it; the file name, source and size are confirmed first | The files sit in `data/labelled/` (git-ignored) |
| 12 | Run the Isolation Forest vs XGBoost comparison on real labels | Item 11, `make install-dev`, then `make compare DATA="data/labelled/<file> ..."` | `evals/results/COMPARE.md` is committed with overall and per-attack-class results; only then does the repository claim an XGBoost result |
| 13 | Calibrate the decision threshold against labelled data | Item 12 | The threshold and its precision-recall trade-off are documented, replacing the fixed `contamination` setting |
| 14 | Retrain with `make train` under the pinned scikit-learn and compare with the committed model | Items 1 and 2 | The manifest records the new hash, or the committed model is kept with the reason noted |

## Deployment

| # | Item | Needs | Done when |
|---|---|---|---|
| 15 | Deploy to Cloud Run | GCP project ID, region, billing account and budget; authenticated `gcloud` | `make budget` and `make deploy` print the API and dashboard URLs, `make smoke` passes, and `make teardown` is run once to confirm it removes everything. Known unknowns to check: Cloud Build service-account permissions for source deploys, the `--filter-projects` value accepted by `gcloud billing budgets create`, and organisation policy on `--allow-unauthenticated` |
| 16 | Tune Cloud Run memory, CPU and concurrency | Items 7 and 8 | `deploy/deploy.sh` uses values justified by the benchmarks (the current 1Gi and 40 concurrent requests are not measured) |
| 17 | Put the deployed dashboard behind a login | Identity-Aware Proxy or an auth layer | The dashboard is not open to anyone with the URL |

## Product features not built

These were removed from the dashboard because they did nothing; they return when they work.

| # | Item | Needs | Done when |
|---|---|---|---|
| 18 | Operator-adjustable alert sensitivity | A threshold parameter in the API and a control in the UI | Changing it changes which rows are flagged, with a test |
| 19 | Browser notifications on detection | Notification permission flow in the UI | A flagged row raises a notification when enabled |
| 20 | Per-satellite elevation and health | Ephemeris or position data, which the receiver fields do not contain | A data source is chosen and the satellite view shows real values |
| 21 | NMEA and RINEX ingestion | A target receiver that exposes correlator and I/Q values, and a field mapping | An adapter converts that receiver's output to the required fields, with a test fixture |
| 22 | Shared session store for multi-instance deployments | A decision that exact cross-request windows matter | Sessions survive across instances, or the limit is accepted and documented |

## Other

| # | Item | Needs | Done when |
|---|---|---|---|
| 23 | Frontend automated tests | A test runner choice and a lockfile update | Core behaviours (`deriveSatellites`, `errorMessage`, the proxy route) are covered |
| 24 | Name the copyright holders in `LICENSE` | The owners' names | `LICENSE` lists them instead of "GNSS Security Shield contributors" |
