"""Model construction and artefact manifests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

DEFAULT_N_ESTIMATORS = 200
DEFAULT_CONTAMINATION = 0.01
DEFAULT_SEED = 42


def build_pipeline(
    *,
    n_estimators: int = DEFAULT_N_ESTIMATORS,
    contamination: float = DEFAULT_CONTAMINATION,
    random_state: int = DEFAULT_SEED,
    n_jobs: int | None = -1,
) -> Pipeline:
    """Standardiser followed by an Isolation Forest.

    The pipeline step names (``scaler``, ``model``) are part of the artefact contract.
    """
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "model",
                IsolationForest(
                    n_estimators=n_estimators,
                    max_samples="auto",
                    contamination=contamination,
                    random_state=random_state,
                    n_jobs=n_jobs,
                ),
            ),
        ]
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or "sha256" not in manifest:
        raise ValueError(f"Manifest {path} must be a JSON object with a 'sha256' field")
    return manifest
