#!/usr/bin/env bash
set -euo pipefail

# Lightweight script to create a temporary S3 bucket for CI integration tests.
# Expects AWS CLI configured via environment (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION).
# Usage: ./create_ci_resources.sh [prefix]
# Prints the bucket name to stdout.

PREFIX="${1:-data-mcp-ci}"
RUN_ID="${GITHUB_RUN_ID:-local}"
RANDOM_SUFFIX="$(date +%s)-$RANDOM"
BUCKET_NAME="${PREFIX}-${RUN_ID}-${RANDOM_SUFFIX}"

if [ -z "${AWS_REGION:-}" ]; then
  echo "ERROR: AWS_REGION must be set" >&2
  exit 2
fi

echo "Creating S3 bucket: ${BUCKET_NAME} in region ${AWS_REGION}..."

# For us-east-1, AWS expects no LocationConstraint
if [ "${AWS_REGION}" = "us-east-1" ]; then
  aws s3api create-bucket --bucket "${BUCKET_NAME}"
else
  aws s3api create-bucket \
    --bucket "${BUCKET_NAME}" \
    --create-bucket-configuration "LocationConstraint=${AWS_REGION}" \
    --region "${AWS_REGION}"
fi

# Enable default server-side encryption (AES256)
aws s3api put-bucket-encryption \
  --bucket "${BUCKET_NAME}" \
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' \
  --region "${AWS_REGION}" || true

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket "${BUCKET_NAME}" \
  --versioning-configuration Status=Enabled \
  --region "${AWS_REGION}" || true

# Apply a simple public-block configuration to be safe (block all public access)
aws s3api put-public-access-block \
  --bucket "${BUCKET_NAME}" \
  --public-access-block-configuration '{"BlockPublicAcls":true,"IgnorePublicAcls":true,"BlockPublicPolicy":true,"RestrictPublicBuckets":true}' \
  --region "${AWS_REGION}" || true

echo "${BUCKET_NAME}"
