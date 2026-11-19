"""Exception types shared across the package."""

from __future__ import annotations


class MissingColumnsError(ValueError):
    """Raised when telemetry lacks fields the detector needs."""

    def __init__(self, columns: list[str]) -> None:
        self.columns = columns
        super().__init__(f"Missing required columns: {', '.join(columns)}")


class FeatureError(ValueError):
    """Raised when engineered features are not finite numbers."""


class ModelIntegrityError(RuntimeError):
    """Raised when a model artefact does not match its manifest or the feature contract."""
