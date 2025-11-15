#!/bin/bash
set -e

# Generate TypeScript types from backend OpenAPI spec
# This script fetches the OpenAPI spec from the backend and generates TypeScript types

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
OPENAPI_URL="${BACKEND_URL}/openapi.json"
OUTPUT_DIR="./lib/api/generated"

echo "Generating TypeScript types from backend OpenAPI spec..."
echo "Backend URL: ${BACKEND_URL}"
echo "OpenAPI URL: ${OPENAPI_URL}"
echo "Output directory: ${OUTPUT_DIR}"

# Check if backend is running
if ! curl -s -f "${BACKEND_URL}/api/health/" > /dev/null 2>&1; then
  echo "Error: Backend is not running at ${BACKEND_URL}"
  echo "Please start the backend server first."
  exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "${OUTPUT_DIR}"

# Fetch OpenAPI spec and generate types
echo "Fetching OpenAPI spec..."
curl -s "${OPENAPI_URL}" -o "${OUTPUT_DIR}/openapi.json"

echo "Generating TypeScript types..."
npx openapi-typescript "${OUTPUT_DIR}/openapi.json" -o "${OUTPUT_DIR}/schema.ts"

echo "Generating API client..."
npx openapi-typescript-codegen --input "${OUTPUT_DIR}/openapi.json" --output "${OUTPUT_DIR}/client" --client fetch

echo "Type generation complete!"
echo "Generated files:"
echo "  - ${OUTPUT_DIR}/schema.ts"
echo "  - ${OUTPUT_DIR}/client/"
