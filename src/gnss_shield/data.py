"""Loading and cleaning GNSS receiver telemetry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .errors import MissingColumnsError
from .features import DEFAULT_CHANNEL, REQUIRED_COLUMNS

NUMERIC_COLUMNS: tuple[str, ...] = (
    "time",
    "PRN",
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
LABEL_COLUMN = "spoofed"


def clean_gnss(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and clean raw telemetry.

    * raises :class:`MissingColumnsError` if a required receiver field is absent;
    * drops the ``chX`` placeholder rows that some sheet exports embed in data columns;
    * coerces measurement columns to numbers;
    * drops no-lock rows (``PRN == 0``) and rows with non-finite required fields;
    * fills a missing ``channel`` column with a single default channel.

    ``time`` must be present on every row or on none.
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise MissingColumnsError(missing)

    out = df.copy()
    numeric = [c for c in NUMERIC_COLUMNS if c in out.columns]

    placeholder = pd.Series(False, index=out.index)
    for col in numeric:
        if not pd.api.types.is_numeric_dtype(out[col]):
            placeholder |= out[col].astype(str).str.startswith("ch")
    out = out.loc[~placeholder].copy()

    for col in numeric:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    if LABEL_COLUMN in out.columns:
        out[LABEL_COLUMN] = pd.to_numeric(out[LABEL_COLUMN], errors="coerce")

    if "PRN" in out.columns:
        out = out.loc[out["PRN"] != 0]

    finite = np.isfinite(out[list(REQUIRED_COLUMNS)].to_numpy(dtype=float)).all(axis=1)
    out = out.loc[finite].copy()

    if "time" in out.columns and out["time"].isna().any():
        raise ValueError("time must be present on every row or on none")

    if "channel" in out.columns:
        out["channel"] = out["channel"].astype(str)
    else:
        out["channel"] = DEFAULT_CHANNEL
    return out.reset_index(drop=True)


def load_training_sheet(path: str | Path) -> pd.DataFrame:
    """Read a raw telemetry sheet (.xls or .csv) with every cell kept as text."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".xls":
        return pd.read_excel(path, engine="xlrd", header=0, dtype=str)
    if suffix == ".csv":
        return pd.read_csv(path, dtype=str)
    raise ValueError(f"Unsupported data file type: {suffix!r} (use .xls or .csv)")


def genuine_only(clean: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows labelled genuine when a label column exists."""
    if LABEL_COLUMN in clean.columns:
        return clean.loc[clean[LABEL_COLUMN] == 0].reset_index(drop=True)
    return clean


def dataset_summary(raw: pd.DataFrame, clean: pd.DataFrame) -> dict[str, Any]:
    """Counts that describe a loaded dataset, for reports."""
    summary: dict[str, Any] = {
        "raw_rows": int(len(raw)),
        "usable_rows": int(len(clean)),
        "discarded_rows": int(len(raw) - len(clean)),
        "channels": sorted(clean["channel"].unique().tolist()),
        "epochs": int(clean["time"].nunique()) if "time" in clean.columns else None,
        "satellites_prn": (
            sorted(int(p) for p in clean["PRN"].dropna().unique()) if "PRN" in clean.columns else []
        ),
    }
    if LABEL_COLUMN in clean.columns:
        counts = clean[LABEL_COLUMN].value_counts().to_dict()
        summary["label_counts"] = {str(int(k)): int(v) for k, v in counts.items()}
    return summary
