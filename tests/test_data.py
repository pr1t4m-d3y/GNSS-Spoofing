from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from gnss_shield.data import (
    clean_gnss,
    dataset_summary,
    genuine_only,
    load_training_sheet,
)
from gnss_shield.errors import MissingColumnsError

from .conftest import make_rows


def test_clean_keeps_well_formed_rows() -> None:
    rows = make_rows(20)
    assert len(clean_gnss(rows)) == 20


def test_clean_drops_placeholder_rows_from_text_sheets() -> None:
    rows = make_rows(20).astype(str)
    placeholder = rows.iloc[[0]].copy()
    placeholder["Carrier_Doppler_hz"] = "ch0"
    placeholder["Pseudorange_m"] = "ch0"
    cleaned = clean_gnss(pd.concat([placeholder, rows], ignore_index=True))
    assert len(cleaned) == 20
    assert cleaned["Carrier_Doppler_hz"].dtype == float


def test_clean_drops_no_lock_rows() -> None:
    rows = make_rows(20)
    rows.loc[3, "PRN"] = 0
    assert len(clean_gnss(rows)) == 19


def test_clean_drops_non_finite_rows() -> None:
    rows = make_rows(20)
    rows.loc[1, "CN0"] = np.nan
    rows.loc[2, "EC"] = np.inf
    assert len(clean_gnss(rows)) == 18


def test_clean_keeps_rows_without_a_prn_column() -> None:
    rows = make_rows(10).drop(columns=["PRN"])
    assert len(clean_gnss(rows)) == 10


def test_clean_requires_receiver_fields() -> None:
    rows = make_rows(10).drop(columns=["PIP"])
    with pytest.raises(MissingColumnsError):
        clean_gnss(rows)


def test_clean_adds_default_channel() -> None:
    rows = make_rows(10).drop(columns=["channel"])
    assert set(clean_gnss(rows)["channel"]) == {"manual_0"}


def test_clean_rejects_partial_time() -> None:
    rows = make_rows(10)
    rows.loc[4, "time"] = np.nan
    with pytest.raises(ValueError, match="time"):
        clean_gnss(rows)


def test_genuine_only_filters_labels() -> None:
    rows = make_rows(10)
    rows["spoofed"] = [0] * 8 + [1] * 2
    assert len(genuine_only(clean_gnss(rows))) == 8


def test_genuine_only_is_a_no_op_without_labels() -> None:
    assert len(genuine_only(clean_gnss(make_rows(10)))) == 10


def test_load_training_sheet_reads_csv_as_text(tmp_path: Path) -> None:
    path = tmp_path / "sheet.csv"
    make_rows(10).to_csv(path, index=False)
    loaded = load_training_sheet(path)
    assert len(loaded) == 10
    assert loaded["CN0"].dtype == object


def test_load_training_sheet_rejects_unknown_suffix(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        load_training_sheet(tmp_path / "sheet.parquet")


def test_dataset_summary_counts() -> None:
    raw = make_rows(20, channels=2)
    raw["spoofed"] = 0
    summary = dataset_summary(raw, clean_gnss(raw))
    assert summary["raw_rows"] == 20
    assert summary["usable_rows"] == 20
    assert summary["channels"] == ["ch0", "ch1"]
    assert summary["epochs"] == 10
    assert summary["satellites_prn"] == [5, 6]
    assert summary["label_counts"] == {"0": 20}
