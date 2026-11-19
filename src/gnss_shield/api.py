"""FastAPI service exposing the detector.

Public routes: ``/health``, ``/ready``. Everything else requires ``X-API-Key``
(see :mod:`gnss_shield.auth`).
"""

import io
import json
import logging
import re
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import __version__
from .auth import require_api_key
from .config import Settings
from .data import clean_gnss
from .detector import Detector, load_detector
from .errors import FeatureError, MissingColumnsError
from .features import ALL_MODEL_FEATURES
from .history import SessionStore
from .logging_config import configure_logging
from .schemas import PredictRequest, ResetRequest, rows_to_frame

logger = logging.getLogger("gnss_shield.api")

_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_TIMELINE_LIMIT = 200
_TIMELINE_COLUMNS = ("Carrier_Doppler_hz", "range_residual", "anomaly_score", "is_spoofed")


def _get_detector(request: Request) -> Detector:
    detector: Detector | None = request.app.state.detector
    if detector is None:
        raise HTTPException(status_code=503, detail="Model is not loaded.")
    return detector


def _analyse(
    request: Request, raw: pd.DataFrame, session_id: str | None
) -> tuple[pd.DataFrame, int]:
    """Clean and score ``raw``. Returns the scored rows and the number of rows dropped."""
    detector = _get_detector(request)
    settings: Settings = request.app.state.settings
    sessions: SessionStore = request.app.state.sessions
    try:
        cleaned = clean_gnss(raw)
    except MissingColumnsError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    dropped = len(raw) - len(cleaned)
    if cleaned.empty:
        return cleaned, dropped
    if cleaned["channel"].nunique() > settings.max_channels:
        raise HTTPException(
            status_code=422, detail=f"At most {settings.max_channels} channels per request."
        )
    try:
        if session_id:
            rows, history = sessions.checkout(session_id, cleaned)
            scored = detector.analyse(rows, history=history)
            sessions.commit(session_id, rows)
        else:
            scored = detector.analyse(cleaned)
    except FeatureError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return scored, dropped


def _predictions(scored: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {
            "index": int(index),
            "is_spoofed": bool(spoofed),
            "anomaly_score": float(score),
            "raw_decision_score": float(raw),
        }
        for index, spoofed, score, raw in zip(
            scored["_input_index"],
            scored["is_spoofed"],
            scored["anomaly_score"],
            scored["raw_decision_score"],
            strict=True,
        )
    ]


def _satellite_stats(scored: pd.DataFrame) -> list[dict[str, Any]]:
    if "PRN" not in scored.columns or scored.empty:
        return []
    stats: list[dict[str, Any]] = []
    for prn, group in scored.dropna(subset=["PRN"]).groupby("PRN"):
        stats.append(
            {
                "prn": int(prn),
                "samples": int(len(group)),
                "spoofed_samples": int(group["is_spoofed"].sum()),
                "mean_anomaly_score": float(group["anomaly_score"].mean()),
                "mean_cn0": float(group["CN0"].mean()),
            }
        )
    return stats


def _summary(scored: pd.DataFrame, dropped: int) -> dict[str, Any]:
    count = len(scored)
    return {
        "total_samples": count,
        "spoofed_samples": int(scored["is_spoofed"].sum()) if count else 0,
        "average_anomaly_score": float(scored["anomaly_score"].mean()) if count else 0.0,
        "rows_dropped": dropped,
        "satellites": _satellite_stats(scored),
    }


def create_app(settings: Settings | None = None, detector: Detector | None = None) -> FastAPI:
    """Build the application. Pass ``detector`` to skip loading a model from disk."""
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging(settings.log_level)
        if not settings.auth_disabled and not settings.api_key:
            logger.warning("GNSS_API_KEY is not set: protected routes will answer 503")
        if app.state.detector is None:
            try:
                app.state.detector = load_detector(
                    settings.model_path, settings.resolved_manifest_path
                )
                logger.info(
                    "model loaded",
                    extra={"fields": {"sha256": app.state.detector.info.sha256}},
                )
            except Exception:
                logger.exception("model failed to load")
        yield

    app = FastAPI(title="GNSS Security Shield API", version=__version__, lifespan=lifespan)
    app.state.settings = settings
    app.state.detector = detector
    app.state.sessions = SessionStore(max_sessions=settings.max_sessions)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_methods=["GET", "POST"],
            allow_headers=["X-API-Key", "Content-Type", "X-Request-ID"],
            allow_credentials=False,
        )

    @app.middleware("http")
    async def access_log(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        supplied = request.headers.get("x-request-id", "")
        request_id = supplied if _REQUEST_ID.match(supplied) else uuid.uuid4().hex
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("unhandled error", extra={"fields": {"request_id": request_id}})
            response = JSONResponse({"detail": "Internal server error."}, status_code=500)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request",
            extra={
                "fields": {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                }
            },
        )
        return response

    @app.get("/health")
    def health() -> dict[str, str]:
        """Liveness: the process is up."""
        return {"status": "ok"}

    @app.get("/ready")
    def ready(request: Request) -> JSONResponse:
        """Readiness: the model is loaded."""
        loaded = request.app.state.detector is not None
        return JSONResponse(
            {"status": "ready" if loaded else "unavailable", "model_loaded": loaded},
            status_code=200 if loaded else 503,
        )

    protected = APIRouter(dependencies=[Depends(require_api_key)])

    @protected.get("/scan")
    def scan(request: Request) -> dict[str, Any]:
        """Model and service self-report."""
        current: Detector | None = request.app.state.detector
        return {
            "status": "ok" if current else "degraded",
            "model_loaded": current is not None,
            "feature_count": len(ALL_MODEL_FEATURES),
            "model_sha256": current.info.sha256 if current else None,
            "sklearn_runtime": current.info.sklearn_runtime if current else None,
            "sklearn_trained": current.info.sklearn_trained if current else None,
            "version": __version__,
        }

    @protected.post("/predict")
    def predict(body: PredictRequest, request: Request) -> dict[str, Any]:
        """Score rows and return per-row predictions plus the engineered features."""
        scored, _ = _analyse(request, rows_to_frame(body.data), body.session_id)
        if scored.empty:
            return {"predictions": [], "features": []}
        frame = scored.drop(columns=["_input_index"]).fillna(0)
        features = json.loads(frame.to_json(orient="records"))
        return {"predictions": _predictions(scored), "features": features}

    @protected.post("/predict/batch")
    def predict_batch(body: PredictRequest, request: Request) -> dict[str, Any]:
        """Score rows and return a summary plus compact per-row predictions."""
        scored, dropped = _analyse(request, rows_to_frame(body.data), body.session_id)
        if scored.empty:
            return {"summary": _summary(scored, dropped), "predictions": []}
        return {"summary": _summary(scored, dropped), "predictions": _predictions(scored)}

    @protected.post("/predict/file")
    def predict_file(request: Request, file: UploadFile = File(...)) -> dict[str, Any]:
        """Score an uploaded .csv or .json telemetry log (stateless)."""
        limit = settings.max_file_bytes
        name = (file.filename or "").lower()
        if not name.endswith((".csv", ".json")):
            raise HTTPException(status_code=400, detail="Unsupported file type; use .csv or .json.")
        content = file.file.read(limit + 1)
        if len(content) > limit:
            raise HTTPException(status_code=413, detail=f"File exceeds {limit} bytes.")
        try:
            raw = (
                pd.read_csv(io.BytesIO(content))
                if name.endswith(".csv")
                else pd.read_json(io.BytesIO(content))
            )
        except Exception as exc:
            raise HTTPException(
                status_code=400, detail="Could not parse the uploaded file."
            ) from exc
        if len(raw) > settings.max_file_rows:
            raise HTTPException(
                status_code=413, detail=f"File exceeds {settings.max_file_rows} rows."
            )

        scored, dropped = _analyse(request, raw, session_id=None)
        if scored.empty:
            return {"summary": _summary(scored, dropped), "timeline": []}
        columns = [c for c in (*_TIMELINE_COLUMNS, "time", "PRN") if c in scored.columns]
        timeline = json.loads(scored[columns].head(_TIMELINE_LIMIT).to_json(orient="records"))
        return {
            "summary": _summary(scored, dropped),
            "timeline": timeline,
            "timeline_truncated": len(scored) > _TIMELINE_LIMIT,
        }

    @protected.post("/reset")
    def reset(body: ResetRequest, request: Request) -> dict[str, str]:
        """Forget the rolling-window history of one session."""
        sessions: SessionStore = request.app.state.sessions
        sessions.reset(body.session_id)
        return {"status": "success", "message": "History cleared"}

    app.include_router(protected)
    return app


app = create_app()
