#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-your-project-id}"
REGION="${REGION:-asia-southeast1}"
SERVICE_NAME="${SERVICE_NAME:-fraud-monitor-api}"
ALLOW_UNAUTHENTICATED="${ALLOW_UNAUTHENTICATED:-true}"
ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-http://localhost,http://127.0.0.1}"
API_KEY_SECRET="${API_KEY_SECRET:-service-api-key}"
LLM_PROVIDER="${LLM_PROVIDER:-openai}"
LLM_MODEL="${LLM_MODEL:-gpt-4o-mini}"
ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-}"
ENV_VARS="^@^ALLOWED_ORIGINS=${ALLOWED_ORIGINS}@LLM_PROVIDER=${LLM_PROVIDER}@LLM_MODEL=${LLM_MODEL}@ANTHROPIC_BASE_URL=${ANTHROPIC_BASE_URL}"

if [[ "${PROJECT_ID}" == "your-project-id" ]]; then
  echo "Set PROJECT_ID env var before running this script."
  exit 1
fi

deploy_args=(
  "${SERVICE_NAME}"
  --source .
  --region "${REGION}"
  --platform managed
  --memory 1Gi
  --cpu 1
  --min-instances 0
  --max-instances 3
  --timeout 300
  --concurrency 80
  --set-env-vars "${ENV_VARS}"
  --update-secrets "API_KEY=${API_KEY_SECRET}:latest"
)

if [[ "${ALLOW_UNAUTHENTICATED,,}" == "true" ]]; then
  deploy_args+=(--allow-unauthenticated)
fi

gcloud run deploy "${deploy_args[@]}"

echo "Deployed URL:"
gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --format 'value(status.url)'
