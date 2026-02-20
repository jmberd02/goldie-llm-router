#!/bin/bash

# Start services for Hybrid LLM Router

echo "🚀 Starting Hybrid LLM Router Services..."
echo ""

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is not running. Please start it with: ollama serve"
    exit 1
fi

echo "✅ Ollama is running"

# Start CopilotKit service in background
echo "🔧 Starting CopilotKit service..."
cd copilot-service && npm start &
COPILOT_PID=$!
cd ..

# Wait for CopilotKit service to be ready
echo "⏳ Waiting for CopilotKit service..."
for i in {1..10}; do
    if curl -s http://localhost:3001/health > /dev/null 2>&1; then
        echo "✅ CopilotKit service is ready"
        break
    fi
    sleep 1
done

# Start Streamlit app
echo "🎨 Starting Streamlit app..."
source venv/bin/activate
streamlit run app.py

# Cleanup on exit
trap "kill $COPILOT_PID" EXIT
