# Cr8-xyz Platform

## Overview

Cr8-xyz is a CGI content creation platform powered by Blender as the creative engine. Our mission is to democratize 3D content creation by putting the power of Blender in everyone's hands through natural language interfaces and AI automation.

### Core Components

1. **Frontend**: Tanstack-based interface with WebRTC streaming
2. **Cr8_engine**: FastAPI WebSocket server for real-time communication
3. **Blender Cr8tive Engine**: Headless Blender addon for command execution

## Getting Started

### Prerequisites

- Node.js 18.x (for frontend)
- Python 3.10+ (for backend)
- Blender 4.2+ (for creative engine)(Our Unofficial version with Pixel Streaming)

### Installation

1. Clone the repository:

   ```bash
   git clone https://code.streetcrisis.online/Cr8-xyz/cr8-app.git
   cd cr8-app
   ```

2. Set up components:
   - [Frontend Setup](frontend/README.md)
   - [Cr8_engine Setup](backend/cr8_engine/README.md)
   - [Blender Addon Setup](backend/blender_cr8tive_engine/README.md)

## Development

```bash
# Start all services
cd frontend && pnpm dev
cd backend/cr8_engine && uvicorn main:app --reload
```

## Contributing

We welcome contributions!

## License

This project is licensed under the GNU General Public License v3.0 or later - see the [LICENSE](docs/LICENSE) file for details.
