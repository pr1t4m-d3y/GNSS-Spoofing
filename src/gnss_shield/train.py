"""Train the Isolation Forest on genuine telemetry and write a model artefact + manifest.

Usage: ``python -m gnss_shield.train --data data/train.xls --out models/gnss_iforest.pkl``
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn

from .data import clean_gnss, dataset_summary, genuine_only, load_training_sheet
from .features import ALL_MODEL_FEATURES, engineer_features, feature_matrix
from .model import (
    DEFAULT_CONTAMINATION,
    DEFAULT_N_ESTIMATORS,
    DEFAULT_SEED,
    build_pipeline,
    file_sha256,
    write_manifest,
)


def train(
    data_path: Path,
    out_path: Path,
    *,
    n_estimators: int = DEFAULT_N_ESTIMATORS,
    contamination: float = DEFAULT_CONTAMINATION,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    """Fit on all genuine rows of ``data_path`` and write ``out_path`` plus its manifest."""
    raw = load_training_sheet(data_path)
    clean = genuine_only(clean_gnss(raw))
    features = engineer_features(clean)
    matrix = feature_matrix(features).to_numpy(dtype=float)
    finite = np.isfinite(matrix).all(axis=1)
    matrix = matrix[finite]

    pipeline = build_pipeline(
        n_estimators=n_estimators, contamination=contamination, random_state=seed
    )
    pipeline.fit(matrix)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, out_path)

    manifest: dict[str, Any] = {
        "sha256": file_sha256(out_path),
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sklearn_version": sklearn.__version__,
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "python_version": platform.python_version(),
        "n_features": len(ALL_MODEL_FEATURES),
        "features": list(ALL_MODEL_FEATURES),
        "n_training_rows": int(matrix.shape[0]),
        "n_estimators": n_estimators,
        "contamination": contamination,
        "random_state": seed,
        "training_data": data_path.name,
        "training_data_summary": dataset_summary(raw, clean),
    }
    write_manifest(out_path.with_suffix(".manifest.json"), manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/train.xls"))
    parser.add_argument("--out", type=Path, default=Path("models/gnss_iforest.pkl"))
    parser.add_argument("--n-estimators", type=int, default=DEFAULT_N_ESTIMATORS)
    parser.add_argument("--contamination", type=float, default=DEFAULT_CONTAMINATION)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args(argv)

    manifest = train(
        args.data,
        args.out,
        n_estimators=args.n_estimators,
        contamination=args.contamination,
        seed=args.seed,
    )
    keys = ("sha256", "n_training_rows", "n_features", "sklearn_version")
    print(json.dumps({k: manifest[k] for k in keys}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
