# CopilotKit Integration - Hybrid Approach

This project uses a hybrid architecture with CopilotKit for AI-powered prompt optimization.

## Architecture

```
┌─────────────────┐      HTTP      ┌──────────────────┐      HTTP      ┌─────────┐
│  Streamlit App  │ ────────────> │  Node.js Service │ ────────────> │ Ollama  │
│    (Python)     │   <────────────│  (CopilotKit)    │   <────────────│  LLM    │
└─────────────────┘                └──────────────────┘                └─────────┘
```

## Components

### 1. Streamlit Frontend (`app.py`)
- User interface with prompt input
- Threshold sliders for context
- Calls CopilotKit service for optimization

### 2. CopilotKit Service (`copilot-service/`)
- Node.js Express server
- Receives optimization requests
- Adds context from threshold sliders
- Calls Ollama LLM
- Returns optimized prompts

### 3. Ollama LLM
- Local qwen2.5:1.5b model
- Performs actual prompt optimization
- Fast and free

## Setup & Running

### Prerequisites
1. Node.js (v18+)
2. Python 3.8+
3. Ollama installed and running

### Quick Start

1. **Start Ollama:**
```bash
ollama serve
```

2. **Start CopilotKit Service:**
```bash
cd copilot-service
npm install
npm start
```

3. **Start Streamlit App:**
```bash
source venv/bin/activate
streamlit run app.py
```

### Or use the startup script:
```bash
./start-services.sh
```

## API Endpoints

### CopilotKit Service

**POST /api/optimize-prompt**
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
      "General QA": 0.7
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "original": "What year was the Eiffel Tower built?",
  "optimized": "Please provide a detailed answer about when the Eiffel Tower was constructed, including the historical context and significance of its completion date.",
  "metadata": {
    "model": "qwen2.5:1.5b",
    "contextUsed": true,
    "thresholds": { ... }
  }
}
```

## Features

✅ Context-aware optimization using threshold sliders
✅ Fallback to direct Ollama if service unavailable
✅ Graceful error handling
✅ Real-time optimization feedback
✅ Undo functionality

## How It Works

1. User types a prompt in Streamlit
2. Clicks the 📎 paperclip button
3. Streamlit sends prompt + threshold context to CopilotKit service
4. Service enhances the system prompt with context
5. Calls Ollama to optimize the prompt
6. Returns optimized version to Streamlit
7. User sees improved prompt in text box

## Benefits of Hybrid Approach

- **Keep Streamlit UI**: No need to rewrite frontend
- **Add CopilotKit features**: Context-awareness, better orchestration
- **Modular**: Easy to swap LLM providers
- **Scalable**: Can add more AI features to the service
- **Fallback support**: Works even if service is down

## Future Enhancements

- [ ] Add streaming responses
- [ ] Implement CopilotKit's full runtime features
- [ ] Add more context sources (routing history, user preferences)
- [ ] Support multiple LLM providers
- [ ] Add caching for common optimizations
- [ ] Implement rate limiting

## Troubleshooting

**Service won't start:**
- Check if port 3001 is available
- Ensure Node.js is installed: `node --version`

**Optimization fails:**
- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Check service health: `curl http://localhost:3001/health`

**Slow responses:**
- Ollama model might need to load (first request is slower)
- Check system resources

## Development

**Run in development mode:**
```bash
cd copilot-service
npm run dev
```

**Test the API:**
```bash
curl -X POST http://localhost:3001/api/optimize-prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test prompt"}'
```
