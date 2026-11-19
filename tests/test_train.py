from __future__ import annotations

import json
from pathlib import Path

import pytest

from gnss_shield.detector import load_detector
from gnss_shield.features import ALL_MODEL_FEATURES
from gnss_shield.model import file_sha256
from gnss_shield.train import main, train

from .conftest import make_rows


def write_sheet(path: Path, spoofed_rows: int = 0) -> int:
    rows = make_rows(300, channels=2)
    rows["spoofed"] = 0
    if spoofed_rows:
        rows.loc[: spoofed_rows - 1, "spoofed"] = 1
    rows.to_csv(path, index=False)
    return len(rows)


def test_train_writes_a_loadable_model_and_manifest(tmp_path: Path) -> None:
    data = tmp_path / "sheet.csv"
    count = write_sheet(data)
    out = tmp_path / "model.pkl"

    manifest = train(data, out, n_estimators=10)

    assert manifest["n_training_rows"] == count
    assert manifest["n_features"] == len(ALL_MODEL_FEATURES)
    assert manifest["features"] == list(ALL_MODEL_FEATURES)
    assert manifest["sha256"] == file_sha256(out)
    assert json.loads(out.with_suffix(".manifest.json").read_text())["sha256"] == manifest["sha256"]
    assert load_detector(out).info.n_features == len(ALL_MODEL_FEATURES)


def test_train_uses_genuine_rows_only(tmp_path: Path) -> None:
    data = tmp_path / "sheet.csv"
    count = write_sheet(data, spoofed_rows=20)
    manifest = train(data, tmp_path / "model.pkl", n_estimators=10)
    assert manifest["n_training_rows"] == count - 20


def test_train_cli_prints_a_summary(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    data = tmp_path / "sheet.csv"
    write_sheet(data)
    arguments = ["--data", str(data), "--out", str(tmp_path / "m.pkl"), "--n-estimators", "10"]
    exit_code = main(arguments)
    assert exit_code == 0
    assert "n_training_rows" in capsys.readouterr().out
