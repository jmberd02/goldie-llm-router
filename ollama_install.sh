#!/bin/bash
# setup_ollama.sh — Install Ollama and pull small model for router demo

# ── Config ────────────────────────────────────────────────────────────────────
MODEL="llama3.2:3b"   # AA dataset slug: llama-3-2-instruct-3b
OLLAMA_URL="http://localhost:11434"
# ─────────────────────────────────────────────────────────────────────────────

set -e

# 1. Install Ollama if not already installed
if command -v ollama &> /dev/null; then
    echo "=== Ollama already installed ($(ollama --version)) — skipping install ==="
else
    echo "=== Installing Ollama ==="
    curl -fsSL https://ollama.com/install.sh | sh
fi

echo ""

# 2. Start Ollama server if not already running
if curl -sf "$OLLAMA_URL" &> /dev/null; then
    echo "=== Ollama server already running at $OLLAMA_URL — skipping start ==="
    OLLAMA_PID=""
else
    echo "=== Starting Ollama server ==="
    ollama serve &
    OLLAMA_PID=$!
    echo "Waiting for server to be ready..."
    for i in {1..10}; do
        curl -sf "$OLLAMA_URL" &> /dev/null && break
        sleep 1
    done
    echo "Server ready."
fi

echo ""

# 3. Pull model if not already present
if ollama list | grep -q "^${MODEL}"; then
    echo "=== Model '$MODEL' already pulled — skipping ==="
else
    echo "=== Pulling $MODEL ==="
    ollama pull "$MODEL"
fi

echo ""
echo "=== Quick sanity check ==="
ollama run "$MODEL" "Reply with only valid JSON: {\"status\": \"ok\"}"

echo ""
echo "=== Done! ==="
echo "Ollama is running at $OLLAMA_URL"
echo "Model: $MODEL"
echo ""
echo "Test it manually:"
echo "  curl $OLLAMA_URL/api/generate -d '{\"model\": \"$MODEL\", \"prompt\": \"What is 2+2?\", \"stream\": false}'"
echo ""
if [ -n "$OLLAMA_PID" ]; then
    echo "To stop ollama: kill $OLLAMA_PID"
fi
echo "To start again later: ollama serve"