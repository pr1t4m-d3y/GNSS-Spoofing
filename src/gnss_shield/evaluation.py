"""Evaluation protocol: time-ordered split, synthetic attack injection and metrics.

The training sheet contains only genuine signals, so spoofed rows are *synthesised* by
perturbing held-out genuine rows. Labels are used only to score the detector, never to
train it. Metrics from this protocol describe how well the detector separates the
injected perturbation from genuine data; they are not a measure of performance against
real spoofing hardware.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from .features import engineer_features, feature_matrix

# Per-row perturbation added to a genuine row to simulate a spoofed one.
ATTACK_RECIPE: dict[str, tuple[float, float]] = {
    "Carrier_Doppler_hz": (350.0, 600.0),  # Hz
    "Pseudorange_m": (800.0, 1200.0),  # metres
    "CN0": (2.0, 5.0),  # dB-Hz
}


def temporal_split(
    df: pd.DataFrame, train_fraction: float = 0.7
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split each channel's timeline: the first ``train_fraction`` rows train, the rest test.

    Both outputs are sorted by (channel, time) with a fresh index.
    """
    if not 0.0 < train_fraction < 1.0:
        raise ValueError("train_fraction must be between 0 and 1 (exclusive)")
    ordered = df.sort_values(["channel", "time"], kind="stable").reset_index(drop=True)
    position = ordered.groupby("channel").cumcount()
    size = ordered.groupby("channel")["time"].transform("size")
    is_train = (position / size) < train_fraction
    return ordered.loc[is_train].reset_index(drop=True), ordered.loc[~is_train].reset_index(
        drop=True
    )


def _perturb(frame: pd.DataFrame, positions: np.ndarray, rng: np.random.Generator) -> None:
    for column, (low, high) in ATTACK_RECIPE.items():
        shift = rng.uniform(low, high, size=len(positions))
        frame.loc[positions, column] = frame.loc[positions, column].to_numpy(dtype=float) + shift


def inject_scattered(
    df: pd.DataFrame, rate: float, rng: np.random.Generator
) -> tuple[pd.DataFrame, np.ndarray]:
    """Perturb a random ``rate`` fraction of rows. Returns the new frame and 0/1 labels."""
    if not 0.0 < rate < 1.0:
        raise ValueError("rate must be between 0 and 1 (exclusive)")
    frame = df.reset_index(drop=True).copy()
    count = max(1, int(round(rate * len(frame))))
    positions = rng.choice(len(frame), size=count, replace=False)
    _perturb(frame, positions, rng)
    labels = np.zeros(len(frame), dtype=int)
    labels[positions] = 1
    return frame, labels


def inject_sustained(
    df: pd.DataFrame, n_blocks: int, block_len: int, rng: np.random.Generator
) -> tuple[pd.DataFrame, np.ndarray]:
    """Perturb ``n_blocks`` contiguous runs of ``block_len`` rows, each within one channel.

    ``df`` must be sorted by (channel, time), as returned by :func:`temporal_split`.
    """
    frame = df.reset_index(drop=True).copy()
    blocks: list[np.ndarray] = []
    for positions in frame.groupby("channel").indices.values():
        ordered = np.sort(positions)
        for start in range(0, len(ordered) - block_len + 1, block_len):
            blocks.append(ordered[start : start + block_len])
    if len(blocks) < n_blocks:
        raise ValueError(f"Only {len(blocks)} blocks of {block_len} rows available; need {n_blocks}")
    chosen = rng.choice(len(blocks), size=n_blocks, replace=False)
    target = np.concatenate([blocks[i] for i in chosen])
    _perturb(frame, target, rng)
    labels = np.zeros(len(frame), dtype=int)
    labels[target] = 1
    return frame, labels


def binary_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    """Precision, recall, F1 and the confusion matrix for the spoofed (1) class.

    A metric whose denominator is zero is reported as ``None``.
    """
    truth = np.asarray(y_true).astype(int)
    pred = np.asarray(y_pred).astype(int)
    tp = int(((truth == 1) & (pred == 1)).sum())
    fp = int(((truth == 0) & (pred == 1)).sum())
    fn = int(((truth == 1) & (pred == 0)).sum())
    tn = int(((truth == 0) & (pred == 0)).sum())
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and (precision + recall) > 0
        else None
    )
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }


def ranking_metrics(y_true: np.ndarray, anomaly_scores: np.ndarray) -> dict[str, float | None]:
    """ROC-AUC and average precision from continuous scores; ``None`` if one class is absent."""
    truth = np.asarray(y_true).astype(int)
    if truth.min() == truth.max():
        return {"roc_auc": None, "average_precision": None}
    return {
        "roc_auc": float(roc_auc_score(truth, anomaly_scores)),
        "average_precision": float(average_precision_score(truth, anomaly_scores)),
    }


def evaluate_frame(pipeline: Any, frame: pd.DataFrame, labels: np.ndarray) -> dict[str, Any]:
    """Score a labelled frame (stateless batch features) with a fitted pipeline."""
    labelled = frame.reset_index(drop=True).copy()
    labelled["_label"] = labels
    features = engineer_features(labelled)
    matrix = feature_matrix(features).to_numpy(dtype=float)
    finite = np.isfinite(matrix).all(axis=1)
    matrix = matrix[finite]
    truth = features["_label"].to_numpy(dtype=int)[finite]

    raw = np.asarray(pipeline.decision_function(matrix), dtype=float)
    predicted = (raw < 0).astype(int)
    result: dict[str, Any] = binary_metrics(truth, predicted)
    result.update(ranking_metrics(truth, -raw))
    result["rows"] = int(len(truth))
    result["rows_dropped_nonfinite"] = int((~finite).sum())
    result["flag_rate"] = float(predicted.mean()) if len(predicted) else None
    return result
