from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from gnss_shield.api import create_app
from gnss_shield.config import Settings
from gnss_shield.detector import Detector

from .conftest import make_rows, records

KEY = "test-key"
HEADERS = {"X-API-Key": KEY}


@pytest.fixture()
def client(detector: Detector) -> TestClient:
    return TestClient(create_app(Settings(api_key=KEY), detector=detector))


def post(client: TestClient, path: str, rows: pd.DataFrame, **extra: Any) -> Any:
    return client.post(path, json={"data": records(rows), **extra}, headers=HEADERS)


def test_health_is_public(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_when_model_is_loaded(client: TestClient) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["model_loaded"] is True


def test_not_ready_when_model_is_missing(tmp_path: Path) -> None:
    settings = Settings(api_key=KEY, model_path=tmp_path / "missing.pkl")
    with TestClient(create_app(settings)) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/ready").status_code == 503
        assert client.get("/scan", headers=HEADERS).json()["model_loaded"] is False


def test_protected_routes_require_the_key(client: TestClient) -> None:
    assert client.get("/scan").status_code == 401
    assert client.get("/scan", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/scan", headers=HEADERS).status_code == 200


def test_auth_fails_closed_without_a_configured_key(detector: Detector) -> None:
    client = TestClient(create_app(Settings(api_key=None), detector=detector))
    assert client.get("/scan").status_code == 503


def test_auth_can_be_disabled_explicitly(detector: Detector) -> None:
    client = TestClient(create_app(Settings(auth_disabled=True), detector=detector))
    assert client.get("/scan").status_code == 200


def test_scan_reports_the_feature_contract(client: TestClient) -> None:
    body = client.get("/scan", headers=HEADERS).json()
    assert body["feature_count"] == 35
    assert body["model_loaded"] is True


def test_predict_returns_predictions_and_features(client: TestClient, rows: pd.DataFrame) -> None:
    response = post(client, "/predict", rows.head(3))
    assert response.status_code == 200
    body = response.json()
    assert len(body["predictions"]) == 3
    assert set(body["predictions"][0]) == {
        "index",
        "is_spoofed",
        "anomaly_score",
        "raw_decision_score",
    }
    assert len(body["features"]) == 3
    assert "anomaly_score" in body["features"][0]


def test_predict_rejects_rows_without_receiver_fields(client: TestClient) -> None:
    response = client.post("/predict", json={"data": [{"foo": 1}]}, headers=HEADERS)
    assert response.status_code == 422


def test_predict_rejects_empty_payload(client: TestClient) -> None:
    assert client.post("/predict", json={"data": []}, headers=HEADERS).status_code == 422


def test_predict_rejects_out_of_range_cn0(client: TestClient, rows: pd.DataFrame) -> None:
    bad = rows.head(1).copy()
    bad["CN0"] = 150.0
    assert post(client, "/predict", bad).status_code == 422


def test_predict_rejects_invalid_session_id(client: TestClient, rows: pd.DataFrame) -> None:
    assert post(client, "/predict", rows.head(1), session_id="not a valid id!").status_code == 422


def test_predict_with_only_no_lock_rows_returns_empty(client: TestClient) -> None:
    rows = make_rows(4, channels=1)
    rows["PRN"] = 0
    response = post(client, "/predict", rows)
    assert response.status_code == 200
    assert response.json() == {"predictions": [], "features": []}


def test_batch_endpoint_returns_summary_and_compact_predictions(
    client: TestClient, rows: pd.DataFrame
) -> None:
    response = post(client, "/predict/batch", rows.head(20))
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["total_samples"] == 20
    assert body["summary"]["rows_dropped"] == 0
    assert len(body["predictions"]) == 20
    assert "features" not in body
    assert {s["prn"] for s in body["summary"]["satellites"]} == {5, 6}


def test_batch_endpoint_reports_dropped_rows(client: TestClient) -> None:
    rows = make_rows(6, channels=1)
    rows.loc[0, "PRN"] = 0
    body = post(client, "/predict/batch", rows).json()
    assert body["summary"]["rows_dropped"] == 1
    assert body["summary"]["total_samples"] == 5


def test_too_many_channels_are_rejected(detector: Detector) -> None:
    client = TestClient(create_app(Settings(api_key=KEY, max_channels=1), detector=detector))
    assert post(client, "/predict/batch", make_rows(8, channels=2)).status_code == 422


def test_session_keeps_rolling_state_between_requests(
    client: TestClient, rows: pd.DataFrame
) -> None:
    first = rows.iloc[[0]]
    second = rows.iloc[[1]]
    assert post(client, "/predict", first, session_id="s1").status_code == 200
    with_history = post(client, "/predict", second, session_id="s1").json()
    without_history = post(client, "/predict", second).json()
    assert with_history["features"][0]["Carrier_Doppler_hz_roll_var"] > 0.0
    assert without_history["features"][0]["Carrier_Doppler_hz_roll_var"] == 0.0


def test_sessions_do_not_share_state(client: TestClient, rows: pd.DataFrame) -> None:
    post(client, "/predict", rows.iloc[[0]], session_id="a")
    other = post(client, "/predict", rows.iloc[[1]], session_id="b").json()
    assert other["features"][0]["Carrier_Doppler_hz_roll_var"] == 0.0


def test_reset_clears_the_session(client: TestClient, rows: pd.DataFrame) -> None:
    post(client, "/predict", rows.iloc[[0]], session_id="s2")
    reset = client.post("/reset", json={"session_id": "s2"}, headers=HEADERS)
    assert reset.status_code == 200
    after = post(client, "/predict", rows.iloc[[1]], session_id="s2").json()
    assert after["features"][0]["Carrier_Doppler_hz_roll_var"] == 0.0


def upload(client: TestClient, name: str, content: bytes) -> Any:
    return client.post("/predict/file", files={"file": (name, content)}, headers=HEADERS)


def test_file_upload_returns_summary_and_timeline(client: TestClient, rows: pd.DataFrame) -> None:
    response = upload(client, "telemetry.csv", rows.to_csv(index=False).encode())
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["total_samples"] == len(rows)
    assert len(body["timeline"]) == len(rows)
    assert {"anomaly_score", "is_spoofed", "time", "PRN"} <= set(body["timeline"][0])
    assert body["timeline_truncated"] is False


def test_file_upload_truncates_long_timelines(client: TestClient) -> None:
    long_log = make_rows(300, channels=2)
    body = upload(client, "telemetry.csv", long_log.to_csv(index=False).encode()).json()
    assert body["summary"]["total_samples"] == 300
    assert len(body["timeline"]) == 200
    assert body["timeline_truncated"] is True


def test_file_upload_missing_columns_is_rejected(client: TestClient) -> None:
    response = upload(client, "telemetry.csv", b"Carrier_Doppler_hz,CN0\n1000,46\n")
    assert response.status_code == 422
    assert "Missing required columns" in response.json()["detail"]


def test_file_upload_rejects_unsupported_extension(client: TestClient) -> None:
    assert upload(client, "telemetry.txt", b"x").status_code == 400


def test_file_upload_rejects_unparseable_json(client: TestClient) -> None:
    assert upload(client, "telemetry.json", b"not json").status_code == 400


def test_file_upload_enforces_size_limit(detector: Detector, rows: pd.DataFrame) -> None:
    client = TestClient(create_app(Settings(api_key=KEY, max_file_bytes=100), detector=detector))
    assert upload(client, "telemetry.csv", rows.to_csv(index=False).encode()).status_code == 413


def test_cors_is_closed_by_default(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers


def test_cors_allows_only_configured_origins(detector: Detector) -> None:
    settings = Settings(api_key=KEY, cors_origins=("https://app.example",))
    client = TestClient(create_app(settings, detector=detector))
    allowed = client.get("/health", headers={"Origin": "https://app.example"})
    denied = client.get("/health", headers={"Origin": "https://evil.example"})
    assert allowed.headers["access-control-allow-origin"] == "https://app.example"
    assert "access-control-allow-origin" not in denied.headers


def test_request_id_is_echoed_or_generated(client: TestClient) -> None:
    echoed = client.get("/health", headers={"X-Request-ID": "abc-123"})
    assert echoed.headers["x-request-id"] == "abc-123"
    replaced = client.get("/health", headers={"X-Request-ID": "bad id with spaces"})
    assert replaced.headers["x-request-id"] != "bad id with spaces"
    assert len(replaced.headers["x-request-id"]) == 32
