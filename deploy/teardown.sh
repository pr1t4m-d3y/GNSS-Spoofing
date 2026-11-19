#!/usr/bin/env bash
# Remove everything deploy.sh created. Set GCP_PROJECT and GCP_REGION.
# Set DELETE_BUILD_REPO=true to also delete the Artifact Registry repository that
# `gcloud run deploy --source` creates (cloud-run-source-deploy) and its images.
set -euo pipefail

: "${GCP_PROJECT:?Set GCP_PROJECT}"
: "${GCP_REGION:?Set GCP_REGION}"

SERVICE_API="${SERVICE_API:-gnss-shield-api}"
SERVICE_WEB="${SERVICE_WEB:-gnss-shield-web}"
SECRET_NAME="${SECRET_NAME:-gnss-shield-api-key}"
RUNTIME_SA_NAME="${RUNTIME_SA_NAME:-gnss-shield-run}"
RUNTIME_SA="${RUNTIME_SA_NAME}@${GCP_PROJECT}.iam.gserviceaccount.com"

for service in "$SERVICE_WEB" "$SERVICE_API"; do
  if gcloud run services describe "$service" --project "$GCP_PROJECT" --region "$GCP_REGION" >/dev/null 2>&1; then
    gcloud run services delete "$service" --project "$GCP_PROJECT" --region "$GCP_REGION" --quiet
  fi
done

if gcloud secrets describe "$SECRET_NAME" --project "$GCP_PROJECT" >/dev/null 2>&1; then
  gcloud secrets delete "$SECRET_NAME" --project "$GCP_PROJECT" --quiet
fi

if gcloud iam service-accounts describe "$RUNTIME_SA" --project "$GCP_PROJECT" >/dev/null 2>&1; then
  gcloud iam service-accounts delete "$RUNTIME_SA" --project "$GCP_PROJECT" --quiet
fi

if [[ "${DELETE_BUILD_REPO:-false}" == "true" ]]; then
  gcloud artifacts repositories delete cloud-run-source-deploy \
    --project "$GCP_PROJECT" --location "$GCP_REGION" --quiet || true
fi

echo "Teardown complete."
