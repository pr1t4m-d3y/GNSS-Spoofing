from __future__ import annotations

import shutil
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
import sklearn

from gnss_shield.detector import Detector, load_detector, normalise_scores
from gnss_shield.errors import FeatureError, ModelIntegrityError
from gnss_shield.features import ALL_MODEL_FEATURES
from gnss_shield.model import build_pipeline, file_sha256, write_manifest

from .conftest import make_rows

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_normalise_scores_anchor_points() -> None:
    scores = normalise_scores(np.array([0.2, 0.0, -0.2, 5.0, -5.0]))
    assert scores.tolist() == pytest.approx([0.0, 0.5, 1.0, 0.0, 1.0])


def test_analyse_returns_one_scored_row_per_input_row(
    detector: Detector, rows: pd.DataFrame
) -> None:
    scored = detector.analyse(rows)
    assert len(scored) == len(rows)
    assert scored["_input_index"].tolist() == list(range(len(rows)))
    assert scored["anomaly_score"].between(0.0, 1.0).all()
    assert (scored["is_spoofed"] == (scored["raw_decision_score"] < 0)).all()
    for column in ALL_MODEL_FEATURES:
        assert column in scored.columns


def test_analyse_preserves_input_order(detector: Detector, rows: pd.DataFrame) -> None:
    shuffled = rows.sample(frac=1.0, random_state=1).reset_index(drop=True)
    scored = detector.analyse(shuffled)
    assert scored["_input_index"].tolist() == list(range(len(shuffled)))
    np.testing.assert_array_equal(
        scored["Carrier_Doppler_hz"].to_numpy(), shuffled["Carrier_Doppler_hz"].to_numpy()
    )


def test_large_perturbation_raises_anomaly_scores(detector: Detector, rows: pd.DataFrame) -> None:
    attacked = rows.copy()
    attacked["Carrier_Doppler_hz"] += 10_000.0
    attacked["Pseudorange_m"] += 1_000_000.0
    attacked["CN0"] += 40.0
    baseline = detector.analyse(rows)["anomaly_score"].mean()
    assert detector.analyse(attacked)["anomaly_score"].mean() > baseline


def test_non_finite_features_are_rejected(detector: Detector) -> None:
    rows = make_rows(2, channels=1)
    rows["Carrier_Doppler_hz"] = [1e308, -1e308]
    with pytest.raises(FeatureError):
        detector.analyse(rows)


def test_load_detector_reports_model_info(artifact_path: Path, detector: Detector) -> None:
    assert detector.info.sha256 == file_sha256(artifact_path)
    assert detector.info.n_features == len(ALL_MODEL_FEATURES)
    assert detector.info.sklearn_runtime == sklearn.__version__


def test_load_detector_rejects_tampered_artifact(artifact_path: Path, tmp_path: Path) -> None:
    model = tmp_path / "model.pkl"
    shutil.copy(artifact_path, model)
    shutil.copy(artifact_path.with_suffix(".manifest.json"), model.with_suffix(".manifest.json"))
    with model.open("ab") as handle:
        handle.write(b"tampered")
    with pytest.raises(ModelIntegrityError, match="sha256"):
        load_detector(model)


def test_load_detector_requires_a_manifest(artifact_path: Path, tmp_path: Path) -> None:
    model = tmp_path / "model.pkl"
    shutil.copy(artifact_path, model)
    with pytest.raises(FileNotFoundError):
        load_detector(model)


def test_load_detector_rejects_wrong_feature_count(tmp_path: Path) -> None:
    pipeline = build_pipeline(n_estimators=5, n_jobs=1).fit(np.random.default_rng(0).normal(size=(50, 5)))
    model = tmp_path / "model.pkl"
    joblib.dump(pipeline, model)
    write_manifest(model.with_suffix(".manifest.json"), {"sha256": file_sha256(model)})
    with pytest.raises(ModelIntegrityError, match="features"):
        load_detector(model)


def test_shipped_model_matches_its_manifest_and_contract() -> None:
    loaded = load_detector(REPO_ROOT / "models" / "gnss_iforest.pkl")
    assert loaded.info.n_features == len(ALL_MODEL_FEATURES)
