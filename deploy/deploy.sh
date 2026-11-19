#!/usr/bin/env bash
# Deploy the detector API and the dashboard to Cloud Run (scale to zero).
#
# Requires an authenticated gcloud CLI and these variables:
#   GCP_PROJECT   project ID
#   GCP_REGION    Cloud Run region, e.g. europe-west1
# Optional: SERVICE_API, SERVICE_WEB, SECRET_NAME, RUNTIME_SA_NAME.
#
# The API key is generated once, stored in Secret Manager and never printed.
set -euo pipefail

: "${GCP_PROJECT:?Set GCP_PROJECT}"
: "${GCP_REGION:?Set GCP_REGION}"

SERVICE_API="${SERVICE_API:-gnss-shield-api}"
SERVICE_WEB="${SERVICE_WEB:-gnss-shield-web}"
SECRET_NAME="${SECRET_NAME:-gnss-shield-api-key}"
RUNTIME_SA_NAME="${RUNTIME_SA_NAME:-gnss-shield-run}"
RUNTIME_SA="${RUNTIME_SA_NAME}@${GCP_PROJECT}.iam.gserviceaccount.com"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Enabling required APIs"
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  --project "$GCP_PROJECT"

if ! gcloud iam service-accounts describe "$RUNTIME_SA" --project "$GCP_PROJECT" >/dev/null 2>&1; then
  echo "Creating runtime service account $RUNTIME_SA"
  gcloud iam service-accounts create "$RUNTIME_SA_NAME" \
    --display-name "GNSS Shield runtime" \
    --project "$GCP_PROJECT"
fi

if ! gcloud secrets describe "$SECRET_NAME" --project "$GCP_PROJECT" >/dev/null 2>&1; then
  echo "Creating secret $SECRET_NAME"
  openssl rand -hex 32 | gcloud secrets create "$SECRET_NAME" \
    --data-file=- \
    --replication-policy=automatic \
    --project "$GCP_PROJECT"
fi
gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
  --member "serviceAccount:${RUNTIME_SA}" \
  --role roles/secretmanager.secretAccessor \
  --project "$GCP_PROJECT" >/dev/null

echo "Deploying $SERVICE_API"
gcloud run deploy "$SERVICE_API" \
  --project "$GCP_PROJECT" \
  --region "$GCP_REGION" \
  --source "$ROOT" \
  --service-account "$RUNTIME_SA" \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 2 \
  --cpu 1 \
  --memory 1Gi \
  --concurrency 40 \
  --session-affinity \
  --set-env-vars "GNSS_LOG_LEVEL=INFO" \
  --set-secrets "GNSS_API_KEY=${SECRET_NAME}:latest"

API_URL="$(gcloud run services describe "$SERVICE_API" \
  --project "$GCP_PROJECT" --region "$GCP_REGION" --format 'value(status.url)')"

echo "Deploying $SERVICE_WEB"
gcloud run deploy "$SERVICE_WEB" \
  --project "$GCP_PROJECT" \
  --region "$GCP_REGION" \
  --source "$ROOT/frontend" \
  --service-account "$RUNTIME_SA" \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 2 \
  --cpu 1 \
  --memory 512Mi \
  --set-env-vars "BACKEND_URL=${API_URL}" \
  --set-secrets "GNSS_API_KEY=${SECRET_NAME}:latest"

WEB_URL="$(gcloud run services describe "$SERVICE_WEB" \
  --project "$GCP_PROJECT" --region "$GCP_REGION" --format 'value(status.url)')"

echo
echo "API:       ${API_URL}"
echo "Dashboard: ${WEB_URL}"
