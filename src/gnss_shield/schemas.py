"""Request schemas for the API."""

from __future__ import annotations

from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

MAX_JSON_ROWS = 10_000
SESSION_ID_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"


class SignalRow(BaseModel):
    """One epoch of receiver telemetry for one channel."""

    model_config = ConfigDict(extra="ignore")

    time: float | None = Field(default=None, allow_inf_nan=False)
    channel: str | None = Field(default=None, min_length=1, max_length=32)
    PRN: int | None = Field(default=None, ge=0)
    Carrier_Doppler_hz: float = Field(allow_inf_nan=False)
    Pseudorange_m: float = Field(allow_inf_nan=False)
    RX_time: float = Field(allow_inf_nan=False)
    TOW: float = Field(allow_inf_nan=False)
    Carrier_phase: float = Field(allow_inf_nan=False)
    EC: float = Field(allow_inf_nan=False)
    LC: float = Field(allow_inf_nan=False)
    PC: float = Field(allow_inf_nan=False)
    PIP: float = Field(allow_inf_nan=False)
    PQP: float = Field(allow_inf_nan=False)
    TCD: float = Field(allow_inf_nan=False)
    CN0: float = Field(ge=0, le=100, allow_inf_nan=False)


class PredictRequest(BaseModel):
    """A batch of rows, optionally tied to a session so rolling windows span requests."""

    data: list[SignalRow] = Field(min_length=1, max_length=MAX_JSON_ROWS)
    session_id: str | None = Field(default=None, pattern=SESSION_ID_PATTERN)


class ResetRequest(BaseModel):
    session_id: str = Field(pattern=SESSION_ID_PATTERN)


def rows_to_frame(rows: list[SignalRow]) -> pd.DataFrame:
    """Build a DataFrame from validated rows, omitting fields the client did not send."""
    records: list[dict[str, Any]] = [row.model_dump(exclude_none=True) for row in rows]
    return pd.DataFrame.from_records(records)
