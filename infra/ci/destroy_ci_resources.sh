#!/usr/bin/env bash
set -euo pipefail

# Lightweight script to destroy a temporary S3 bucket used for CI integration tests.
# Usage: ./destroy_ci_resources.sh BUCKET_NAME [AWS_REGION]
# Expects AWS CLI configured via environment (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) or configured profile.
# Will attempt to remove all objects (including versions) before deleting the bucket.

BUCKET="${1:-}"
AWS_REGION="${2:-${AWS_REGION:-}}"

if [ -z "${BUCKET}" ]; then
  echo "ERROR: BUCKET name must be provided as first argument" >&2
  exit 2
fi

if [ -z "${AWS_REGION}" ]; then
  echo "ERROR: AWS_REGION must be provided (env or second arg)" >&2
  exit 2
fi

echo "Destroying S3 bucket: ${BUCKET} in region ${AWS_REGION}..."

# Remove all object versions (if versioning enabled) and objects
set +e
# Try to delete all objects (non-versioned)
aws s3 rm "s3://${BUCKET}" --recursive --region "${AWS_REGION}"
# Try to delete versions (if any)
VERSIONS=$(aws s3api list-object-versions --bucket "${BUCKET}" --region "${AWS_REGION}" --output json 2>/dev/null || echo "{}")
if echo "${VERSIONS}" | grep -q '"Versions"' || echo "${VERSIONS}" | grep -q '"DeleteMarkers"'; then
  echo "Found versions or delete markers, attempting to remove them..."
  # Use jq if available, otherwise attempt aws s3 rm fallback
  if command -v jq >/dev/null 2>&1; then
    echo "${VERSIONS}" | jq -r '.Versions[]?.Key + "||" + (.Versions[]?.VersionId // "")' | while IFS="||" read -r key vid; do
      if [ -n "$key" ] && [ -n "$vid" ]; then
        aws s3api delete-object --bucket "${BUCKET}" --key "$key" --version-id "$vid" --region "${AWS_REGION}" || true
      fi
    done
    echo "${VERSIONS}" | jq -r '.DeleteMarkers[]?.Key + "||" + (.DeleteMarkers[]?.VersionId // "")' | while IFS="||" read -r key vid; do
      if [ -n "$key" ] && [ -n "$vid" ]; then
        aws s3api delete-object --bucket "${BUCKET}" --key "$key" --version-id "$vid" --region "${AWS_REGION}" || true
      fi
    done
  else
    echo "jq not available; attempted bulk remove above. Continuing."
  fi
fi
set -e

# Finally delete the bucket
aws s3api delete-bucket --bucket "${BUCKET}" --region "${AWS_REGION}" || {
  echo "Failed to delete bucket via s3api; attempting fallback (s3 rb)..." >&2
  aws s3 rb "s3://${BUCKET}" --force --region "${AWS_REGION}" || echo "Fallback delete also failed"
}

echo "Destroy complete (errors may be non-fatal)."
