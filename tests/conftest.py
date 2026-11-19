"""Shared fixtures: synthetic telemetry and a tiny trained model artefact."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import pytest
import sklearn

from gnss_shield.detector import Detector, load_detector
from gnss_shield.features import engineer_features, feature_matrix
from gnss_shield.model import build_pipeline, file_sha256, write_manifest


def make_rows(n: int, channels: int = 2, seed: int = 0) -> pd.DataFrame:
    """Synthetic but well-formed telemetry: ``n`` rows split evenly over ``channels``."""
    rng = np.random.default_rng(seed)
    per_channel = n // channels
    frames = []
    for index in range(channels):
        t = np.arange(per_channel, dtype=float)
        tow = 491_655.0 + t * 0.02
        frames.append(
            pd.DataFrame(
                {
                    "time": t,
                    "channel": f"ch{index}",
                    "PRN": 5 + index,
                    "Carrier_Doppler_hz": 1000.0 + rng.normal(0, 5, per_channel),
                    "Pseudorange_m": 505_000.0 + rng.normal(0, 20, per_channel),
                    "RX_time": tow - 0.07,
                    "TOW": tow,
                    "Carrier_phase": -109_000.0 + rng.normal(0, 3, per_channel),
                    "EC": 120_000.0 + rng.normal(0, 500, per_channel),
                    "LC": 119_800.0 + rng.normal(0, 500, per_channel),
                    "PC": 133_000.0 + rng.normal(0, 500, per_channel),
                    "PIP": -3_700.0 + rng.normal(0, 30, per_channel),
                    "PQP": 200.0 + rng.normal(0, 5, per_channel),
                    "TCD": 2_760.0 + rng.normal(0, 2, per_channel),
                    "CN0": 46.0 + rng.normal(0, 1, per_channel),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """JSON-safe list of row dicts."""
    return list(json.loads(frame.to_json(orient="records")))


def write_artifact(directory: Path, rows: pd.DataFrame) -> Path:
    """Fit a small pipeline on ``rows`` and write it with a matching manifest."""
    matrix = feature_matrix(engineer_features(rows)).to_numpy(dtype=float)
    pipeline = build_pipeline(n_estimators=20, n_jobs=1).fit(matrix)
    model_path = directory / "model.pkl"
    joblib.dump(pipeline, model_path)
    write_manifest(
        model_path.with_suffix(".manifest.json"),
        {"sha256": file_sha256(model_path), "sklearn_version": sklearn.__version__},
    )
    return model_path


@pytest.fixture(scope="session")
def rows() -> pd.DataFrame:
    return make_rows(200, channels=2)


@pytest.fixture(scope="session")
def artifact_path(tmp_path_factory: pytest.TempPathFactory, rows: pd.DataFrame) -> Path:
    return write_artifact(tmp_path_factory.mktemp("artifact"), rows)


@pytest.fixture(scope="session")
def detector(artifact_path: Path) -> Detector:
    return load_detector(artifact_path)
