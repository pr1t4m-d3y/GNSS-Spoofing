# syntax=docker/dockerfile:1

# ---- build stage: resolve and install pinned dependencies into a virtualenv ----
FROM python:3.12-slim AS builder
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /build
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---- runtime stage: no build tools, non-root user ----
FROM python:3.12-slim AS runtime
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080
RUN useradd --system --uid 10001 --no-create-home gnss
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY src ./src
COPY models ./models
USER gnss
EXPOSE 8080
# One worker: the per-session rolling-window store lives in process memory.
# Request logging is done by the app itself, so uvicorn's access log is off.
CMD ["sh", "-c", "exec uvicorn gnss_shield.api:app --host 0.0.0.0 --port ${PORT} --no-access-log"]
