#!/bin/bash
# Startup script for Smart Apply Agent — runs both FastAPI backend and Streamlit frontend.

set -e

FASTAPI_PORT="${FASTAPI_PORT:-8000}"
STREAMLIT_PORT="${STREAMLIT_PORT:-8501}"

echo "=== Smart Apply Agent ==="
echo "FastAPI backend : http://0.0.0.0:${FASTAPI_PORT}  (Swagger: http://0.0.0.0:${FASTAPI_PORT}/docs)"
echo "Streamlit frontend: http://0.0.0.0:${STREAMLIT_PORT}"
echo "=========================="

# Start FastAPI in the background
uvicorn career_agent.api.app:app \
    --host 0.0.0.0 \
    --port "${FASTAPI_PORT}" \
    --log-level info &

# Start Streamlit in the foreground (so container stays alive)
streamlit run demo/streamlit/app.py \
    --server.address=0.0.0.0 \
    --server.port="${STREAMLIT_PORT}" \
    --server.headless=true &

# Wait for any process to exit
wait -n

# If one exits, kill the other and exit
echo "A process exited. Shutting down..."
exit 1
