"""Physics-informed feature engineering for GNSS receiver telemetry.

The detector consumes 12 raw per-channel receiver fields and derives 35 model features:
10 base fields, 11 engineered features that encode cross-field physical consistency
(Doppler vs. range rate, pseudorange vs. transit time, carrier phase vs. pseudorange,
I/Q power balance, correlator lock) and 14 rolling mean/variance features over a
10-epoch window per channel.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .errors import MissingColumnsError

SPEED_OF_LIGHT = 299_792_458.0  # m/s
L1_FREQ = 1_575_420_000.0  # Hz, GPS L1 carrier
L1_WAVELENGTH = SPEED_OF_LIGHT / L1_FREQ  # about 0.1903 m
ROLLING_WINDOW = 10
EPS = 1e-6
DEFAULT_CHANNEL = "manual_0"

# Fields the detector needs from the receiver for every epoch and channel.
REQUIRED_COLUMNS: tuple[str, ...] = (
    "Carrier_Doppler_hz",
    "Pseudorange_m",
    "RX_time",
    "TOW",
    "Carrier_phase",
    "EC",
    "LC",
    "PC",
    "PIP",
    "PQP",
    "TCD",
    "CN0",
)

BASE_FEATURES: tuple[str, ...] = (
    "Carrier_Doppler_hz",
    "Pseudorange_m",
    "Carrier_phase",
    "EC",
    "LC",
    "PC",
    "PIP",
    "PQP",
    "TCD",
    "CN0",
)

ENGINEERED_FEATURES: tuple[str, ...] = (
    "range_rate",
    "transit_time_s",
    "computed_range",
    "range_residual",
    "phase_range_bias",
    "cn0_pc_ratio",
    "cn0_ec_ratio",
    "iq_imbalance",
    "lock_ratio",
    "doppler_delta",
    "tcd_cn0",
)

ROLLING_TARGETS: tuple[str, ...] = (
    "Carrier_Doppler_hz",
    "CN0",
    "range_residual",
    "iq_imbalance",
    "doppler_delta",
    "phase_range_bias",
    "lock_ratio",
)

ROLLING_FEATURES: tuple[str, ...] = tuple(
    f"{target}_roll_{stat}" for target in ROLLING_TARGETS for stat in ("mean", "var")
)

# Column order is part of the model contract: the pickled pipeline was fitted on this order.
ALL_MODEL_FEATURES: tuple[str, ...] = BASE_FEATURES + ENGINEERED_FEATURES + ROLLING_FEATURES


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return ``df`` sorted by (channel, time) with all engineered and rolling features added.

    Rolling statistics and ``doppler_delta`` are computed per channel. Rows are sorted
    stably by channel then time, and the index is reset.
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise MissingColumnsError(missing)

    out = df.copy()
    if "channel" not in out.columns:
        out["channel"] = DEFAULT_CHANNEL
    if "time" not in out.columns:
        out["time"] = np.arange(len(out), dtype=float)
    out = out.sort_values(["channel", "time"], kind="stable").reset_index(drop=True)

    out["range_rate"] = -L1_WAVELENGTH * out["Carrier_Doppler_hz"]
    out["transit_time_s"] = out["TOW"] - out["RX_time"]
    out["computed_range"] = out["transit_time_s"] * SPEED_OF_LIGHT
    out["range_residual"] = out["Pseudorange_m"] - out["computed_range"]
    out["phase_range_bias"] = out["Pseudorange_m"] - out["Carrier_phase"] * L1_WAVELENGTH
    out["cn0_pc_ratio"] = out["CN0"] / (out["PC"].abs() + EPS)
    out["cn0_ec_ratio"] = out["CN0"] / (out["EC"].abs() + EPS)
    out["iq_imbalance"] = (out["PIP"].abs() - out["PQP"].abs()) / (
        out["PIP"].abs() + out["PQP"].abs() + EPS
    )
    out["lock_ratio"] = out["LC"] / (out["EC"].abs() + EPS)
    out["doppler_delta"] = (
        out.groupby("channel", sort=False)["Carrier_Doppler_hz"].diff().fillna(0.0)
    )
    out["tcd_cn0"] = out["TCD"] / (out["CN0"] + EPS)

    for target in ROLLING_TARGETS:
        grouped = out.groupby("channel", sort=False)[target]
        out[f"{target}_roll_mean"] = grouped.transform(
            lambda s: s.rolling(ROLLING_WINDOW, min_periods=1).mean()
        )
        out[f"{target}_roll_var"] = grouped.transform(
            lambda s: s.rolling(ROLLING_WINDOW, min_periods=1).var().fillna(0.0)
        )
    return out


def feature_matrix(features: pd.DataFrame) -> pd.DataFrame:
    """Select the model features in the exact order the model expects."""
    return features[list(ALL_MODEL_FEATURES)]
