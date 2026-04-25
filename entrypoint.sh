#!/bin/sh
# entrypoint.sh — Waits for Ollama to be ready, pulls the model, then starts Streamlit.
# Idempotent: if the model is already present, `ollama pull` is a fast no-op.

set -e

OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.1}"
MAX_WAIT=120   # seconds
INTERVAL=5

echo "[entrypoint] Waiting for Ollama at ${OLLAMA_BASE_URL} ..."

elapsed=0
until curl -sf "${OLLAMA_BASE_URL}/api/tags" > /dev/null 2>&1; do
    if [ "$elapsed" -ge "$MAX_WAIT" ]; then
        echo "[entrypoint] ERROR: Ollama did not become available within ${MAX_WAIT}s. Exiting."
        exit 1
    fi
    echo "[entrypoint] Ollama not ready yet. Retrying in ${INTERVAL}s ... (${elapsed}s elapsed)"
    sleep "$INTERVAL"
    elapsed=$((elapsed + INTERVAL))
done

echo "[entrypoint] Ollama is ready. Pulling model '${OLLAMA_MODEL}' ..."
# Use the Ollama REST API to pull the model so we don't need the CLI installed in the app container.
curl -sf "${OLLAMA_BASE_URL}/api/pull" \
    -d "{\"name\": \"${OLLAMA_MODEL}\"}" \
    -H "Content-Type: application/json" \
    --no-buffer \
    | while IFS= read -r line; do
        echo "[entrypoint] $line"
    done

echo "[entrypoint] Model '${OLLAMA_MODEL}' is ready."
echo "[entrypoint] Starting Streamlit ..."

exec streamlit run app/app.py \
    --server.port "${STREAMLIT_SERVER_PORT:-8501}" \
    --server.address "0.0.0.0" \
    --server.headless true
