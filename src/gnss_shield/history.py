"""Bounded per-session history so single-row requests get correct rolling features.

Rolling statistics need the previous epochs of the same channel. A client that streams
rows one request at a time passes a ``session_id``; the store keeps the last
``ROLLING_WINDOW`` rows per channel for that session and the detector prepends them
before computing features. Nothing is shared between sessions.
"""

from __future__ import annotations

import threading
from collections import OrderedDict

import pandas as pd

from .features import REQUIRED_COLUMNS, ROLLING_WINDOW

STORED_COLUMNS: tuple[str, ...] = ("channel", "time", "PRN", *REQUIRED_COLUMNS)


def _next_times(channels: pd.Series, tail: pd.DataFrame | None) -> pd.Series:
    """Assign increasing times per channel, continuing after the stored history."""
    last: dict[str, float] = {}
    if tail is not None and len(tail):
        last = {str(k): float(v) for k, v in tail.groupby("channel")["time"].max().items()}
    offset = channels.map(lambda c: last.get(str(c), -1.0) + 1.0).astype(float)
    position = channels.groupby(channels).cumcount().astype(float)
    return offset + position


class SessionStore:
    """Thread-safe LRU store of the most recent rows per channel for each session."""

    def __init__(self, max_sessions: int = 256, rows_per_channel: int = ROLLING_WINDOW) -> None:
        if max_sessions < 1 or rows_per_channel < 1:
            raise ValueError("max_sessions and rows_per_channel must be at least 1")
        self._max_sessions = max_sessions
        self._rows_per_channel = rows_per_channel
        self._sessions: OrderedDict[str, pd.DataFrame] = OrderedDict()
        self._lock = threading.Lock()

    def __len__(self) -> int:
        with self._lock:
            return len(self._sessions)

    def checkout(
        self, session_id: str, rows: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame | None]:
        """Return ``(rows_with_time, history)`` for a session.

        If ``rows`` has no ``time`` column, times continue from the stored history.
        """
        with self._lock:
            tail = self._sessions.get(session_id)
            if tail is not None:
                self._sessions.move_to_end(session_id)
                tail = tail.copy()
        timed = rows.copy()
        if "time" not in timed.columns:
            timed["time"] = _next_times(timed["channel"], tail)
        return timed, tail

    def commit(self, session_id: str, rows: pd.DataFrame) -> None:
        """Append ``rows`` (which must carry ``time``) and trim to the window per channel."""
        keep = [c for c in STORED_COLUMNS if c in rows.columns]
        incoming = rows[keep]
        with self._lock:
            tail = self._sessions.get(session_id)
            merged = incoming if tail is None else pd.concat([tail, incoming], ignore_index=True)
            merged = (
                merged.sort_values(["channel", "time"], kind="stable")
                .groupby("channel", sort=False)
                .tail(self._rows_per_channel)
                .reset_index(drop=True)
            )
            self._sessions[session_id] = merged
            self._sessions.move_to_end(session_id)
            while len(self._sessions) > self._max_sessions:
                self._sessions.popitem(last=False)

    def reset(self, session_id: str) -> bool:
        """Forget a session. Returns True if it existed."""
        with self._lock:
            return self._sessions.pop(session_id, None) is not None
