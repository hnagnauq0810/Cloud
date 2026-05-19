#!/usr/bin/env bash
set -euo pipefail

# Run this script on EC2 from inside the repository folder after editing .env.
CONTAINER_NAME="fastapi-app"
IMAGE_NAME="fastapi-app:latest"

git pull

docker stop "$CONTAINER_NAME" || true
docker rm "$CONTAINER_NAME" || true
docker build -t "$IMAGE_NAME" .
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  --env-file .env \
  -p 8000:8000 \
  "$IMAGE_NAME"

docker ps --filter "name=$CONTAINER_NAME"
curl -f http://localhost:8000/health
