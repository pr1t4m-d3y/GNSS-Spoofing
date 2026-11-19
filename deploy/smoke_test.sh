#!/usr/bin/env bash
# Check a deployed API: liveness, readiness, auth enforcement and one scored batch.
#
# Required: GCP_PROJECT, GCP_REGION. Optional: SERVICE_API, SECRET_NAME.
# The API key is read from Secret Manager into memory and is never printed.
set -euo pipefail

: "${GCP_PROJECT:?Set GCP_PROJECT}"
: "${GCP_REGION:?Set GCP_REGION}"
SERVICE_API="${SERVICE_API:-gnss-shield-api}"
SECRET_NAME="${SECRET_NAME:-gnss-shield-api-key}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

API_URL="$(gcloud run services describe "$SERVICE_API" \
  --project "$GCP_PROJECT" --region "$GCP_REGION" --format 'value(status.url)')"
API_KEY="$(gcloud secrets versions access latest --secret "$SECRET_NAME" --project "$GCP_PROJECT")"

PAYLOAD="$(python3 - "$ROOT/examples/safe_signals.csv" <<'PY'
import csv
import json
import sys

with open(sys.argv[1], newline="") as handle:
    rows = [
        {key: (value if key == "channel" else float(value)) for key, value in row.items()}
        for row in csv.DictReader(handle)
    ][:20]
print(json.dumps({"data": rows}))
PY
)"

failures=0
check() {
  local name="$1" expected="$2" actual="$3"
  if [[ "$actual" == "$expected" ]]; then
    echo "ok    $name ($actual)"
  else
    echo "FAIL  $name: expected $expected, got $actual"
    failures=$((failures + 1))
  fi
}

check "GET /health" 200 "$(curl -s -o /dev/null -w '%{http_code}' "$API_URL/health")"
check "GET /ready" 200 "$(curl -s -o /dev/null -w '%{http_code}' "$API_URL/ready")"
check "GET /scan without key" 401 "$(curl -s -o /dev/null -w '%{http_code}' "$API_URL/scan")"
check "GET /scan with key" 200 "$(curl -s -o /dev/null -w '%{http_code}' -H "X-API-Key: $API_KEY" "$API_URL/scan")"
check "POST /predict/batch" 200 "$(curl -s -o /dev/null -w '%{http_code}' -X POST \
  -H "X-API-Key: $API_KEY" -H 'Content-Type: application/json' -d "$PAYLOAD" "$API_URL/predict/batch")"

if [[ "$failures" -gt 0 ]]; then
  echo "$failures check(s) failed"
  exit 1
fi
echo "All checks passed for $API_URL"
