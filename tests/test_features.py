from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from gnss_shield.errors import MissingColumnsError
from gnss_shield.features import (
    ALL_MODEL_FEATURES,
    BASE_FEATURES,
    L1_WAVELENGTH,
    REQUIRED_COLUMNS,
    SPEED_OF_LIGHT,
    engineer_features,
    feature_matrix,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def one_row(**overrides: float | str) -> pd.DataFrame:
    base: dict[str, float | str] = {
        "time": 0.0,
        "channel": "ch0",
        "Carrier_Doppler_hz": 1000.0,
        "Pseudorange_m": 500_000.0,
        "RX_time": 100.0,
        "TOW": 100.07,
        "Carrier_phase": -100_000.0,
        "EC": 100.0,
        "LC": 90.0,
        "PC": 200.0,
        "PIP": 3.0,
        "PQP": 1.0,
        "TCD": 50.0,
        "CN0": 10.0,
    }
    base.update(overrides)
    return pd.DataFrame([base])


def test_feature_contract_size_and_uniqueness() -> None:
    assert len(ALL_MODEL_FEATURES) == 35
    assert len(set(ALL_MODEL_FEATURES)) == 35
    assert ALL_MODEL_FEATURES[: len(BASE_FEATURES)] == BASE_FEATURES


def test_feature_contract_matches_shipped_manifest() -> None:
    manifest = json.loads((REPO_ROOT / "models" / "gnss_iforest.manifest.json").read_text())
    assert manifest["features"] == list(ALL_MODEL_FEATURES)


def test_engineered_formulas_match_hand_computation() -> None:
    out = engineer_features(one_row()).iloc[0]
    computed_range = (100.07 - 100.0) * SPEED_OF_LIGHT
    assert out["range_rate"] == pytest.approx(-L1_WAVELENGTH * 1000.0)
    assert out["transit_time_s"] == pytest.approx(0.07, rel=1e-6)
    assert out["computed_range"] == pytest.approx(computed_range, rel=1e-6)
    assert out["range_residual"] == pytest.approx(500_000.0 - computed_range, rel=1e-6)
    assert out["phase_range_bias"] == pytest.approx(500_000.0 + 100_000.0 * L1_WAVELENGTH)
    assert out["cn0_pc_ratio"] == pytest.approx(10.0 / (200.0 + 1e-6))
    assert out["cn0_ec_ratio"] == pytest.approx(10.0 / (100.0 + 1e-6))
    assert out["iq_imbalance"] == pytest.approx((3.0 - 1.0) / (3.0 + 1.0 + 1e-6))
    assert out["lock_ratio"] == pytest.approx(90.0 / (100.0 + 1e-6))
    assert out["tcd_cn0"] == pytest.approx(50.0 / (10.0 + 1e-6))


def test_first_row_has_zero_delta_and_zero_variance() -> None:
    out = engineer_features(one_row()).iloc[0]
    assert out["doppler_delta"] == 0.0
    assert out["Carrier_Doppler_hz_roll_var"] == 0.0
    assert out["Carrier_Doppler_hz_roll_mean"] == pytest.approx(1000.0)


def test_delta_and_rolling_statistics_over_two_rows() -> None:
    frame = pd.concat(
        [
            one_row(time=0.0, Carrier_Doppler_hz=10.0),
            one_row(time=1.0, Carrier_Doppler_hz=20.0),
        ],
        ignore_index=True,
    )
    last = engineer_features(frame).iloc[-1]
    assert last["doppler_delta"] == pytest.approx(10.0)
    assert last["Carrier_Doppler_hz_roll_mean"] == pytest.approx(15.0)
    assert last["Carrier_Doppler_hz_roll_var"] == pytest.approx(50.0)  # sample variance of 10, 20


def test_rolling_window_is_capped_at_ten_rows() -> None:
    frame = pd.concat(
        [one_row(time=float(i), Carrier_Doppler_hz=float(i)) for i in range(12)],
        ignore_index=True,
    )
    last = engineer_features(frame).iloc[-1]
    assert last["Carrier_Doppler_hz_roll_mean"] == pytest.approx(6.5)  # mean of 2..11


def test_channels_do_not_mix() -> None:
    frame = pd.concat(
        [
            one_row(channel="ch0", time=0.0, Carrier_Doppler_hz=0.0),
            one_row(channel="ch0", time=1.0, Carrier_Doppler_hz=0.0),
            one_row(channel="ch1", time=0.0, Carrier_Doppler_hz=100.0),
        ],
        ignore_index=True,
    )
    out = engineer_features(frame)
    ch1 = out.loc[out["channel"] == "ch1"].iloc[0]
    assert ch1["doppler_delta"] == 0.0
    assert ch1["Carrier_Doppler_hz_roll_mean"] == pytest.approx(100.0)


def test_rows_are_sorted_by_channel_then_time() -> None:
    frame = pd.concat(
        [one_row(time=2.0), one_row(time=0.0), one_row(time=1.0)], ignore_index=True
    )
    assert engineer_features(frame)["time"].tolist() == [0.0, 1.0, 2.0]


def test_missing_time_and_channel_get_defaults() -> None:
    frame = one_row().drop(columns=["time", "channel"])
    out = engineer_features(frame)
    assert out["time"].tolist() == [0.0]
    assert out["channel"].tolist() == ["manual_0"]


def test_missing_required_columns_raise() -> None:
    frame = one_row().drop(columns=["EC", "TCD"])
    with pytest.raises(MissingColumnsError) as excinfo:
        engineer_features(frame)
    assert set(excinfo.value.columns) == {"EC", "TCD"}


def test_feature_matrix_has_model_order() -> None:
    matrix = feature_matrix(engineer_features(one_row()))
    assert list(matrix.columns) == list(ALL_MODEL_FEATURES)


def test_required_columns_are_all_base_or_time_fields() -> None:
    assert set(BASE_FEATURES) <= set(REQUIRED_COLUMNS)
    assert {"TOW", "RX_time"} <= set(REQUIRED_COLUMNS)
