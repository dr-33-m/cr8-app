# Cr8-xyz Engine (WebSocket Server)

## Overview

The Cr8_engine is a FastAPI WebSocket server that acts as the central communication hub between:

- The Cr8-xyz frontend interface
- The Blender Cr8tive Engine addon
- AI agent processes

## Key Features

### WebSocket Architecture

- Dual WebSocket endpoints (`/blender` and `/browser`)
- Message routing based on command patterns
- Session management with exponential backoff retries

### Agent Integration

- MCP server for tool integration
- Context management for AI agents
- Command validation and processing

## Setup & Installation

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (copy from .env.example)
cp .env.example .env
```

## Running the Server

```bash
# Development mode (auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Configuration

### Environment Variables

Create a `.env` file by copying `.env.example` and updating the values:

#### B.L.A.Z.E AI Agent Configuration

```
OPENROUTER_API_KEY=your_openrouter_api_key
AI_PROVIDER=openrouter
OLLAMA_BASE_URL=http://localhost:11434/v1
AI_MODEL_NAME=qwen/qwen3-coder
```

#### Blender Configuration

```
BLENDER_EXECUTABLE_PATH=/path/to/blender/executable
```

For detailed configuration options, see `.env.example`.

### Main Configuration

- Edit `main.py` for:
  - Host/port settings
  - CORS configuration
  - Logging levels

## API Endpoints

### WebSocket

- `/ws/blender` - Blender addon connection
- `/ws/browser` - Frontend connection

### REST API

- `/api/v1/...` - Additional HTTP endpoints

## Troubleshooting

- Connection issues: Check firewall and port settings
- Authentication errors: Verify API keys
- Message processing: Check logs in `logs/cr8_engine.log`
