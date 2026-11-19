"""Runtime configuration, read from environment variables (see .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


def _csv(name: str) -> tuple[str, ...]:
    raw = os.environ.get(name, "")
    return tuple(item.strip() for item in raw.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    """Service settings. Defaults are safe: authentication is on and CORS is closed."""

    model_path: Path = Path("models/gnss_iforest.pkl")
    manifest_path: Path | None = None
    api_key: str | None = None
    auth_disabled: bool = False
    cors_origins: tuple[str, ...] = ()
    max_file_bytes: int = 10 * 1024 * 1024
    max_file_rows: int = 50_000
    max_channels: int = 64
    max_sessions: int = 256
    log_level: str = "INFO"

    @property
    def resolved_manifest_path(self) -> Path:
        return self.manifest_path or self.model_path.with_suffix(".manifest.json")

    @classmethod
    def from_env(cls) -> Settings:
        manifest = os.environ.get("GNSS_MANIFEST_PATH")
        return cls(
            model_path=Path(os.environ.get("GNSS_MODEL_PATH", "models/gnss_iforest.pkl")),
            manifest_path=Path(manifest) if manifest else None,
            api_key=os.environ.get("GNSS_API_KEY") or None,
            auth_disabled=_flag("GNSS_AUTH_DISABLED"),
            cors_origins=_csv("GNSS_CORS_ORIGINS"),
            max_file_bytes=_int("GNSS_MAX_FILE_BYTES", 10 * 1024 * 1024),
            max_file_rows=_int("GNSS_MAX_FILE_ROWS", 50_000),
            max_channels=_int("GNSS_MAX_CHANNELS", 64),
            max_sessions=_int("GNSS_MAX_SESSIONS", 256),
            log_level=os.environ.get("GNSS_LOG_LEVEL", "INFO").upper(),
        )
