"""Structured JSON logging (one object per line, using Cloud Logging's field names)."""

from __future__ import annotations

import json
import logging
import sys


class JsonFormatter(logging.Formatter):
    """Format records as JSON with ``severity`` and ``message`` keys."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            payload.update(fields)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Route all logging to stdout as JSON. Safe to call more than once."""
    root = logging.getLogger()
    root.setLevel(level)
    for handler in list(root.handlers):
        if getattr(handler, "_gnss_json", False):
            root.removeHandler(handler)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler._gnss_json = True  # type: ignore[attr-defined]
    root.addHandler(handler)
