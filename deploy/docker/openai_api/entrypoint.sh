#!/bin/bash
set -e

cd /PaddleOCR

# Install the hubserving model package if needed.
if ! command -v hub >/dev/null 2>&1; then
  echo "hub command not found."
  exit 1
fi

echo "Installing PaddleOCR hubserving package..."
hub install deploy/hubserving/ocr_system/ || true

# Start PaddleOCR HubServing in background
echo "Starting PaddleOCR HubServing backend..."
hub serving start -m ocr_system &
HUB_PID=$!

# Wait a short time for the backend to warm up.
for i in $(seq 1 30); do
  if curl -sSf http://127.0.0.1:8868/predict/ocr_system >/dev/null 2>&1; then
    break
  fi
  sleep 1
  echo "Waiting for HubServing to become available... ($i)"
done

exec uvicorn app:app --host 0.0.0.0 --port 8080 --log-level info
