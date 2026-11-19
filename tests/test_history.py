from __future__ import annotations

import numpy as np

from gnss_shield.detector import Detector
from gnss_shield.history import SessionStore

from .conftest import make_rows


def test_checkout_without_history_returns_none_tail() -> None:
    store = SessionStore()
    rows = make_rows(4, channels=1)
    timed, tail = store.checkout("a", rows)
    assert tail is None
    assert len(timed) == 4


def test_missing_time_continues_after_stored_history() -> None:
    store = SessionStore()
    rows = make_rows(6, channels=1).drop(columns=["time"])
    first, _ = store.checkout("a", rows)
    assert first["time"].tolist() == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    store.commit("a", first)
    second, tail = store.checkout("a", rows.head(2))
    assert second["time"].tolist() == [6.0, 7.0]
    assert tail is not None


def test_history_is_trimmed_to_the_rolling_window_per_channel() -> None:
    store = SessionStore()
    rows = make_rows(50, channels=2)
    store.commit("a", rows)
    _, tail = store.checkout("a", rows.head(1))
    assert tail is not None
    assert tail.groupby("channel").size().to_dict() == {"ch0": 10, "ch1": 10}


def test_sessions_are_isolated() -> None:
    store = SessionStore()
    rows = make_rows(10, channels=1)
    store.commit("a", rows)
    _, tail = store.checkout("b", rows)
    assert tail is None


def test_least_recently_used_session_is_evicted() -> None:
    store = SessionStore(max_sessions=2)
    rows = make_rows(4, channels=1)
    for name in ("a", "b", "c"):
        store.commit(name, rows)
    assert len(store) == 2
    assert store.checkout("a", rows)[1] is None
    assert store.checkout("c", rows)[1] is not None


def test_reset_reports_whether_the_session_existed() -> None:
    store = SessionStore()
    store.commit("a", make_rows(4, channels=1))
    assert store.reset("a") is True
    assert store.reset("a") is False


def test_streaming_with_history_matches_scoring_the_whole_batch(detector: Detector) -> None:
    rows = make_rows(50, channels=1)
    whole = detector.analyse(rows)

    store = SessionStore()
    first, tail = store.checkout("s", rows.iloc[:30])
    detector.analyse(first, history=tail)
    store.commit("s", first)

    second, tail = store.checkout("s", rows.iloc[30:])
    streamed = detector.analyse(second, history=tail)

    expected = whole.iloc[30:].reset_index(drop=True)
    for column in (
        "doppler_delta",
        "Carrier_Doppler_hz_roll_mean",
        "CN0_roll_mean",
        "range_residual_roll_mean",
        "Carrier_Doppler_hz_roll_var",
        "CN0_roll_var",
    ):
        np.testing.assert_allclose(
            streamed[column].to_numpy(), expected[column].to_numpy(), rtol=1e-6, atol=1e-6
        )
