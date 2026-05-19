#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"

echo "1. Root endpoint"
curl -s "$BASE_URL/" | python -m json.tool

echo "2. Health endpoint"
curl -s "$BASE_URL/health" | python -m json.tool

echo "3. DB health endpoint"
curl -s "$BASE_URL/health/db" | python -m json.tool

echo "4. Create item in database"
curl -s -X POST "$BASE_URL/items" \
  -H "Content-Type: application/json" \
  -d '{"title":"Evidence item","description":"Created for grading evidence"}' | python -m json.tool

echo "5. List items"
curl -s "$BASE_URL/items" | python -m json.tool

echo "6. S3 health endpoint"
curl -s "$BASE_URL/health/s3" | python -m json.tool

echo "7. Upload file to S3. Create sample file and upload."
echo "Hello AWS S3 evidence" > /tmp/fastapi-evidence.txt
curl -s -X POST "$BASE_URL/files/upload" \
  -F "file=@/tmp/fastapi-evidence.txt" | python -m json.tool
