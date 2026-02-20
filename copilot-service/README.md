# CopilotKit Service

Node.js backend service that provides AI-powered prompt optimization using CopilotKit and Ollama.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Make sure Ollama is running:
```bash
ollama serve
```

3. Start the service:
```bash
npm start
```

The service will run on `http://localhost:3001`

## API Endpoints

### POST /api/optimize-prompt
Optimizes a prompt using AI with optional context.

**Request:**
```json
{
  "prompt": "What year was the Eiffel Tower built?",
  "context": {
    "thresholds": {
      "Math": 0.5,
      "Code Operations": 0.5,
      "Reasoning": 0.5,
      "Agentic Tool Use": 0.5,
      "Long Context": 0.5,
      "General QA": 0.5
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "original": "What year was the Eiffel Tower built?",
  "optimized": "Please provide a detailed answer about when the Eiffel Tower was constructed...",
  "metadata": {
    "model": "qwen2.5:1.5b",
    "contextUsed": true
  }
}
```

### GET /health
Health check endpoint.

## Environment Variables

- `PORT` - Server port (default: 3001)
- `OLLAMA_BASE_URL` - Ollama API URL (default: http://localhost:11434/api)
- `MODEL_NAME` - Model to use (default: qwen2.5:1.5b)
