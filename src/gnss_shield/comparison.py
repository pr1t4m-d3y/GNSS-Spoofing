"""Unsupervised Isolation Forest against supervised XGBoost on labelled telemetry.

Both models use the same 35 features and the same time-ordered split. The Isolation Forest
is fitted on the genuine training rows only; XGBoost also sees the spoofed training rows
and their labels. The gap between them is the price of not needing labelled attacks.
Requires real labels (a non-zero ``spoofed`` value marks a spoofed row).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .data import LABEL_COLUMN
from .evaluation import metric_set, temporal_split
from .features import ALL_MODEL_FEATURES, engineer_features, feature_matrix
from .model import build_pipeline
from .supervised import build_xgb, positive_weight, top_features


def _matrix(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Feature matrix and original label per row, with non-finite rows removed."""
    features = engineer_features(frame)
    matrix = feature_matrix(features).to_numpy(dtype=float)
    finite = np.isfinite(matrix).all(axis=1)
    classes = features[LABEL_COLUMN].to_numpy(dtype=int)
    return matrix[finite], classes[finite]


def class_counts(classes: np.ndarray) -> dict[str, int]:
    values, counts = np.unique(classes, return_counts=True)
    return {str(int(v)): int(c) for v, c in zip(values, counts, strict=True)}


def compare_models(
    clean: pd.DataFrame, *, train_fraction: float = 0.7, seed: int = 42
) -> dict[str, Any]:
    """Fit both models on the training split and score them on the held-out split.

    ``clean`` is the output of ``clean_gnss`` for a labelled recording (all classes kept).
    Raises ``ValueError`` if either split lacks genuine or spoofed rows.
    """
    labelled = clean.dropna(subset=[LABEL_COLUMN]).copy()
    labelled[LABEL_COLUMN] = labelled[LABEL_COLUMN].astype(int)
    train, test = temporal_split(labelled, train_fraction)
    x_train, classes_train = _matrix(train)
    x_test, classes_test = _matrix(test)
    y_train = (classes_train != 0).astype(int)
    y_test = (classes_test != 0).astype(int)

    for name, labels in (("train", y_train), ("test", y_test)):
        if len(labels) == 0 or labels.min() == labels.max():
            raise ValueError(f"The {name} split needs both genuine and spoofed rows")

    forest = build_pipeline(random_state=seed)
    forest.fit(x_train[y_train == 0])
    booster = build_xgb(positive_weight(y_train), random_state=seed)
    booster.fit(x_train, y_train)

    forest_raw = np.asarray(forest.decision_function(x_test), dtype=float)
    booster_proba = np.asarray(booster.predict_proba(x_test))[:, 1]

    def both(mask: np.ndarray) -> dict[str, Any]:
        return {
            "isolation_forest": metric_set(
                y_test[mask], (forest_raw[mask] < 0).astype(int), -forest_raw[mask]
            ),
            "xgboost": metric_set(
                y_test[mask], (booster_proba[mask] >= 0.5).astype(int), booster_proba[mask]
            ),
        }

    per_class: dict[str, Any] = {}
    for value in sorted(set(classes_test.tolist()) - {0}):
        per_class[str(value)] = both((classes_test == 0) | (classes_test == value))

    return {
        "splits": {
            "train_fraction": train_fraction,
            "train_rows": int(len(y_train)),
            "test_rows": int(len(y_test)),
            "train_classes": class_counts(classes_train),
            "test_classes": class_counts(classes_test),
        },
        "overall": both(np.ones(len(y_test), dtype=bool)),
        "per_class": per_class,
        "xgboost_top_features": top_features(booster, ALL_MODEL_FEATURES),
        "seed": seed,
    }
