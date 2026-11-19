#!/usr/bin/env bash
# Create a Cloud Billing budget with alerts at 50%, 90% and 100% of the amount.
#
# Required: GCP_PROJECT, BILLING_ACCOUNT_ID, BUDGET_AMOUNT (a number, e.g. 5)
# Optional: BUDGET_CURRENCY (default USD)
set -euo pipefail

: "${GCP_PROJECT:?Set GCP_PROJECT}"
: "${BILLING_ACCOUNT_ID:?Set BILLING_ACCOUNT_ID}"
: "${BUDGET_AMOUNT:?Set BUDGET_AMOUNT}"
BUDGET_CURRENCY="${BUDGET_CURRENCY:-USD}"

gcloud services enable billingbudgets.googleapis.com --project "$GCP_PROJECT"

PROJECT_NUMBER="$(gcloud projects describe "$GCP_PROJECT" --format 'value(projectNumber)')"

gcloud billing budgets create \
  --billing-account "$BILLING_ACCOUNT_ID" \
  --display-name "gnss-shield-${GCP_PROJECT}" \
  --budget-amount "${BUDGET_AMOUNT}${BUDGET_CURRENCY}" \
  --filter-projects "projects/${PROJECT_NUMBER}" \
  --threshold-rule percent=0.5 \
  --threshold-rule percent=0.9 \
  --threshold-rule percent=1.0
