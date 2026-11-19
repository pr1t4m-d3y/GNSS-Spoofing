from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from gnss_shield.data import clean_gnss
from gnss_shield.evaluation import (
    ATTACK_RECIPE,
    binary_metrics,
    evaluate_frame,
    inject_scattered,
    inject_sustained,
    ranking_metrics,
    temporal_split,
)
from gnss_shield.features import engineer_features, feature_matrix
from gnss_shield.model import build_pipeline

from .conftest import make_rows


def test_temporal_split_is_per_channel_and_ordered() -> None:
    rows = clean_gnss(make_rows(100, channels=2))
    train, test = temporal_split(rows, 0.7)
    assert len(train) + len(test) == len(rows)
    for channel in ("ch0", "ch1"):
        in_train = train.loc[train["channel"] == channel, "time"]
        in_test = test.loc[test["channel"] == channel, "time"]
        assert len(in_train) == 35
        assert in_train.max() < in_test.min()


def test_temporal_split_validates_fraction() -> None:
    with pytest.raises(ValueError):
        temporal_split(make_rows(10), 1.0)


def test_scattered_injection_labels_and_changes_only_attacked_rows() -> None:
    _, test = temporal_split(clean_gnss(make_rows(200, channels=2)), 0.5)
    attacked, labels = inject_scattered(test, 0.10, np.random.default_rng(0))
    assert labels.sum() == 10
    assert len(labels) == len(test)
    for column, (low, high) in ATTACK_RECIPE.items():
        shift = attacked[column].to_numpy() - test[column].to_numpy()
        assert np.allclose(shift[labels == 0], 0.0)
        assert ((shift[labels == 1] >= low) & (shift[labels == 1] <= high)).all()


def test_injection_does_not_mutate_the_input() -> None:
    _, test = temporal_split(clean_gnss(make_rows(100, channels=1)), 0.5)
    before = test.copy()
    inject_scattered(test, 0.2, np.random.default_rng(1))
    pd.testing.assert_frame_equal(test, before)


def test_injection_is_deterministic_for_a_seed() -> None:
    _, test = temporal_split(clean_gnss(make_rows(100, channels=1)), 0.5)
    first, labels_first = inject_scattered(test, 0.2, np.random.default_rng(5))
    second, labels_second = inject_scattered(test, 0.2, np.random.default_rng(5))
    pd.testing.assert_frame_equal(first, second)
    np.testing.assert_array_equal(labels_first, labels_second)


def test_sustained_injection_creates_contiguous_blocks_inside_channels() -> None:
    _, test = temporal_split(clean_gnss(make_rows(400, channels=2)), 0.5)
    _, labels = inject_sustained(test, n_blocks=2, block_len=20, rng=np.random.default_rng(0))
    assert labels.sum() == 40
    labelled = test.assign(_label=labels)
    for _, group in labelled.groupby("channel"):
        positions = np.flatnonzero(group["_label"].to_numpy() == 1)
        if len(positions) == 0:
            continue
        runs = np.split(positions, np.flatnonzero(np.diff(positions) != 1) + 1)
        assert all(len(run) % 20 == 0 for run in runs)


def test_sustained_injection_needs_enough_blocks() -> None:
    _, test = temporal_split(clean_gnss(make_rows(40, channels=1)), 0.5)
    with pytest.raises(ValueError, match="blocks"):
        inject_sustained(test, n_blocks=5, block_len=10, rng=np.random.default_rng(0))


def test_binary_metrics_on_a_known_confusion_matrix() -> None:
    truth = np.array([1, 1, 1, 1, 0, 0, 0, 0, 0, 0])
    predicted = np.array([1, 1, 1, 0, 1, 0, 0, 0, 0, 0])
    metrics = binary_metrics(truth, predicted)
    assert (metrics["tp"], metrics["fp"], metrics["fn"], metrics["tn"]) == (3, 1, 1, 5)
    assert metrics["precision"] == pytest.approx(0.75)
    assert metrics["recall"] == pytest.approx(0.75)
    assert metrics["f1"] == pytest.approx(0.75)


def test_binary_metrics_report_undefined_values_as_none() -> None:
    metrics = binary_metrics(np.array([1, 1, 0]), np.array([0, 0, 0]))
    assert metrics["precision"] is None
    assert metrics["f1"] is None
    assert metrics["recall"] == 0.0


def test_ranking_metrics_perfect_and_degenerate() -> None:
    perfect = ranking_metrics(np.array([0, 0, 1, 1]), np.array([0.1, 0.2, 0.8, 0.9]))
    assert perfect["roc_auc"] == pytest.approx(1.0)
    assert perfect["average_precision"] == pytest.approx(1.0)
    single_class = ranking_metrics(np.array([0, 0, 0]), np.array([0.1, 0.2, 0.3]))
    assert single_class == {"roc_auc": None, "average_precision": None}


def test_evaluate_frame_returns_the_full_metric_set() -> None:
    clean = clean_gnss(make_rows(400, channels=2))
    train, test = temporal_split(clean, 0.7)
    matrix = feature_matrix(engineer_features(train)).to_numpy(dtype=float)
    pipeline = build_pipeline(n_estimators=20, n_jobs=1).fit(matrix)
    attacked, labels = inject_scattered(test, 0.1, np.random.default_rng(0))
    result = evaluate_frame(pipeline, attacked, labels)
    for key in ("precision", "recall", "f1", "roc_auc", "average_precision", "tp", "fp", "fn", "tn"):
        assert key in result
    assert result["rows"] == len(test)
    assert result["tp"] + result["fn"] == int(labels.sum())
    assert result["tp"] + result["fp"] + result["fn"] + result["tn"] == len(test)
