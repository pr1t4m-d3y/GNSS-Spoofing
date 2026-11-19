"""Inference wrapper around the fitted pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn

from .errors import FeatureError, ModelIntegrityError
from .features import ALL_MODEL_FEATURES, engineer_features, feature_matrix
from .model import file_sha256, read_manifest

logger = logging.getLogger(__name__)

# Fixed mapping from the forest's decision function to a 0..1 anomaly score.
# Raw decision values are roughly in [-0.2, 0.2]; 0 is the decision boundary.
SCORE_CENTER = 0.2
SCORE_SPAN = 0.4


def normalise_scores(raw: np.ndarray) -> np.ndarray:
    """Map raw decision values to anomaly scores in [0, 1] (higher is more anomalous)."""
    scores: np.ndarray = np.clip(1.0 - (raw + SCORE_CENTER) / SCORE_SPAN, 0.0, 1.0)
    return scores


@dataclass(frozen=True)
class ModelInfo:
    path: str
    sha256: str
    sklearn_runtime: str
    sklearn_trained: str | None
    n_features: int


class Detector:
    """Scores batches of cleaned telemetry rows."""

    def __init__(self, pipeline: Any, info: ModelInfo) -> None:
        self._pipeline = pipeline
        self.info = info

    def decision_function(self, matrix: np.ndarray) -> np.ndarray:
        """Raw decision values for a feature matrix in model-feature order (below 0 = outlier)."""
        return np.asarray(self._pipeline.decision_function(matrix), dtype=float)

    def analyse(self, rows: pd.DataFrame, history: pd.DataFrame | None = None) -> pd.DataFrame:
        """Engineer features for ``rows`` and score them.

        ``rows`` must already be cleaned. ``history`` holds earlier rows of the same
        channels; they feed the rolling windows but are not scored or returned.
        The result is in input order and carries ``_input_index`` (0-based position in
        ``rows``), ``raw_decision_score``, ``anomaly_score`` and ``is_spoofed``.
        """
        current = rows.copy()
        current["_input_index"] = np.arange(len(current))
        if history is not None and len(history):
            past = history.copy()
            past["_input_index"] = -1
            combined = pd.concat([past, current], ignore_index=True, sort=False)
        else:
            combined = current

        features = engineer_features(combined)
        features = features.loc[features["_input_index"] >= 0]
        matrix = feature_matrix(features).to_numpy(dtype=float)
        if not np.isfinite(matrix).all():
            raise FeatureError("Engineered features contain non-finite values")

        raw = self.decision_function(matrix)
        scored = features.copy()
        scored["raw_decision_score"] = raw
        scored["anomaly_score"] = normalise_scores(raw)
        # IsolationForest labels a row an outlier exactly when its decision value is below 0.
        scored["is_spoofed"] = raw < 0
        return scored.sort_values("_input_index", kind="stable").reset_index(drop=True)


def load_detector(model_path: Path, manifest_path: Path | None = None) -> Detector:
    """Load a model artefact after verifying it against its manifest."""
    manifest_path = manifest_path or model_path.with_suffix(".manifest.json")
    manifest = read_manifest(manifest_path)
    digest = file_sha256(model_path)
    if digest != manifest["sha256"]:
        raise ModelIntegrityError(
            f"{model_path} does not match the sha256 recorded in {manifest_path}"
        )

    pipeline = joblib.load(model_path)
    n_features = getattr(pipeline, "n_features_in_", None)
    if n_features != len(ALL_MODEL_FEATURES):
        raise ModelIntegrityError(
            f"Model expects {n_features} features but the feature contract has "
            f"{len(ALL_MODEL_FEATURES)}"
        )

    trained = manifest.get("sklearn_version")
    if trained and trained != sklearn.__version__:
        logger.warning(
            "scikit-learn version differs from the one the model was trained with",
            extra={"fields": {"trained": trained, "runtime": sklearn.__version__}},
        )

    # One thread per request: concurrency comes from the server, not from the forest.
    pipeline.set_params(model__n_jobs=1)
    info = ModelInfo(
        path=str(model_path),
        sha256=digest,
        sklearn_runtime=sklearn.__version__,
        sklearn_trained=trained,
        n_features=int(n_features),
    )
    return Detector(pipeline, info)
