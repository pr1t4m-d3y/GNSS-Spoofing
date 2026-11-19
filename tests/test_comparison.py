from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("xgboost")

from gnss_shield.comparison import class_counts, compare_models  # noqa: E402
from gnss_shield.data import clean_gnss  # noqa: E402
from gnss_shield.evaluation import metric_set  # noqa: E402
from gnss_shield.features import ALL_MODEL_FEATURES  # noqa: E402
from gnss_shield.supervised import build_xgb, positive_weight, top_features  # noqa: E402

from .conftest import make_rows  # noqa: E402


def labelled_recording() -> pd.DataFrame:
    """Two channels; attack classes 1 and 2 appear in both the early and the late part."""
    rows = make_rows(800, channels=2).reset_index(drop=True)
    rows["spoofed"] = 0
    for channel in ("ch0", "ch1"):
        index = rows.index[rows["channel"] == channel].to_numpy()
        n = len(index)
        for cls, (low, high) in {1: (0.40, 0.50), 2: (0.80, 0.90)}.items():
            target = index[int(low * n) : int(high * n)]
            rows.loc[target, "spoofed"] = cls
            rows.loc[target, "Carrier_Doppler_hz"] += 5_000.0 * cls
            rows.loc[target, "Pseudorange_m"] += 1_000_000.0 * cls
    return rows


def test_positive_weight() -> None:
    assert positive_weight(np.array([0, 0, 0, 0, 1])) == pytest.approx(4.0)
    assert positive_weight(np.array([0, 0, 0])) == 1.0


def test_class_counts() -> None:
    assert class_counts(np.array([0, 0, 1, 2, 2, 2])) == {"0": 2, "1": 1, "2": 3}


def test_metric_set_contains_all_metrics() -> None:
    result = metric_set(np.array([0, 1, 1, 0]), np.array([0, 1, 0, 0]), np.array([0.1, 0.9, 0.4, 0.2]))
    for key in ("precision", "recall", "f1", "roc_auc", "average_precision", "tp", "fp", "fn", "tn"):
        assert key in result


def test_top_features_are_sorted_and_validated() -> None:
    rng = np.random.default_rng(0)
    x = rng.normal(size=(200, len(ALL_MODEL_FEATURES)))
    y = (x[:, 3] > 0).astype(int)
    model = build_xgb(1.0).fit(x, y)
    top = top_features(model, ALL_MODEL_FEATURES, k=5)
    assert len(top) == 5
    assert top[0]["importance"] >= top[-1]["importance"]
    assert top[0]["feature"] == ALL_MODEL_FEATURES[3]
    with pytest.raises(ValueError):
        top_features(model, ALL_MODEL_FEATURES[:-1])


def test_compare_models_reports_both_models_overall_and_per_class() -> None:
    clean = clean_gnss(labelled_recording())
    result = compare_models(clean, train_fraction=0.7, seed=1)
    assert set(result["overall"]) == {"isolation_forest", "xgboost"}
    # Class 1 occurs only in the training period, class 2 only in the held-out period.
    assert set(result["splits"]["train_classes"]) == {"0", "1"}
    assert set(result["per_class"]) == {"2"}
    assert result["splits"]["train_rows"] + result["splits"]["test_rows"] == len(clean)
    assert len(result["xgboost_top_features"]) == 10


def test_compare_models_needs_both_classes_in_each_split() -> None:
    rows = make_rows(200, channels=2)
    rows["spoofed"] = 0
    with pytest.raises(ValueError, match="both genuine and spoofed"):
        compare_models(clean_gnss(rows))
