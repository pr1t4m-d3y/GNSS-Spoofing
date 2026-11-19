"""Supervised baseline: gradient-boosted trees on the same 35 physics-informed features.

Used only by the comparison in ``gnss_shield.comparison``; the deployed detector is the
unsupervised Isolation Forest. Importing this module requires ``xgboost`` (a development
dependency, not part of the API image).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from xgboost import XGBClassifier


def positive_weight(labels: np.ndarray) -> float:
    """Ratio of genuine to spoofed rows, used to re-weight the rare spoofed class."""
    truth = np.asarray(labels).astype(int)
    positives = int((truth == 1).sum())
    negatives = int((truth == 0).sum())
    return negatives / positives if positives and negatives else 1.0


def build_xgb(scale_pos_weight: float = 1.0, *, random_state: int = 42) -> XGBClassifier:
    """XGBoost classifier with fixed, conventional settings and one thread for repeatability."""
    return XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        eval_metric="aucpr",
        tree_method="hist",
        n_jobs=1,
        random_state=random_state,
    )


def top_features(model: Any, names: Sequence[str], k: int = 10) -> list[dict[str, Any]]:
    """The ``k`` most important features of a fitted model, most important first."""
    importances = np.asarray(model.feature_importances_, dtype=float)
    if len(importances) != len(names):
        raise ValueError("Feature names do not match the model's feature count")
    order = np.argsort(importances)[::-1][:k]
    return [{"feature": names[i], "importance": float(importances[i])} for i in order]
