# Cr8-xyz Platform

## Overview

Cr8-xyz is a CGI content creation platform powered by Blender as the creative engine. Our mission is to democratize 3D content creation by putting the power of Blender in everyone's hands through natural language interfaces and AI automation.

### Core Components

1. **Frontend**: Tanstack-based interface with WebRTC streaming
2. **Cr8_engine**: FastAPI WebSocket server for real-time communication
3. **Custom Blender Build**: Modified Blender with integrated WebRTC viewport streaming
4. **WebRTC Infrastructure**: GStreamer-based pixel streaming pipeline
5. **Blender Addons**: AI-capable addons for dynamic capability discovery

## System Requirements

### Prerequisites

- **Operating System**: Linux (Debian 12+, Ubuntu 22.04+ tested)
- **Node.js**: 18.x (for frontend)
- **Python**: 3.10+ (for backend)
- **Rust**: Latest stable (for GStreamer plugin building)
- **Hardware**: 8GB+ RAM, multi-core CPU, dedicated GPU recommended

### Network Requirements

- **Bandwidth**: 2-12 Mbps per streaming session (varies by resolution)
- **Ports**: 8000 (Cr8 Engine), 8443 (WebRTC signaling), WebRTC peer-to-peer

## Complete Setup Guide

### Step 1: WebRTC Infrastructure Setup

Install GStreamer WebRTC plugin and signaling server:

- **Documentation**: [GStreamer WebRTC Setup](docs/GST_WEBRTC_SETUP.md)
- **Build webrtcsink plugin** from gst-plugins-rs source
- **Start signaling server** on port 8443

### Step 2: Custom Blender Build

Build Blender with integrated WebRTC viewport streaming:

- **Documentation**: [Custom Blender Build](docs/CUSTOM_BLENDER_BUILD.md)
- **Clone custom repository** with WebRTC modifications
- **Install prerequisite addons**:
  - Multi-Registry Asset Manager (set-builder)
  - Blender Cr8tive Engine
- **Configure path** in Cr8 Engine environment

### Step 3: Platform Setup

1. Clone the repository:

   ```bash
   git clone https://code.cr8-xyz.art/Cr8-xyz/cr8-app.git
   cd cr8-app
   ```

2. Set up components:
   - [Frontend Setup](frontend/README.md) - WebRTC streaming interface
   - [Cr8_engine Setup](backend/cr8_engine/README.md) - WebSocket server and AI agent
   - [Blender Addons Setup](backend/blender_cr8tive_engine/README.md) - AI router system

### Step 4: Configuration

Configure environment variables:

**Frontend** (`frontend/.env`):

```bash
VITE_WEBSOCKET_URL=ws://localhost:8000/ws
VITE_API_URL=http://localhost:8000
VITE_WEBRTC_SIGNALING_SERVER_URL=ws://127.0.0.1:8443
```

**Backend** (`backend/cr8_engine/.env`):

```bash
BLENDER_EXECUTABLE_PATH=/path/to/your/custom/blender/build_linux/bin/blender
OPENROUTER_API_KEY=your_openrouter_api_key
AI_PROVIDER=openrouter
```

## Setup Checklist

Complete this checklist to ensure full functionality:

### WebRTC Infrastructure

- [ ] GStreamer 1.22+ installed with all required plugins
- [ ] webrtcsink plugin built from gst-plugins-rs source
- [ ] GST_PLUGIN_PATH configured in shell (`~/.zshrc` or `~/.bashrc`)
- [ ] Signaling server running (`cargo run --bin gst-webrtc-signalling-server`)
- [ ] `gst-inspect-1.0 webrtcsink` works without errors

### Custom Blender Build

- [ ] Custom Blender repository cloned (`webrtc-viewport-streaming` branch)
- [ ] Build dependencies installed (see [Blender Build Docs](https://developer.blender.org/docs/handbook/building_blender/linux/))
- [ ] `make update` completed successfully
- [ ] `make` build completed successfully
- [ ] Blender executable runs without errors (`./build_linux/bin/blender`)

### Prerequisite Addons

- [ ] Multi-Registry Asset Manager (set-builder) installed
- [ ] Blender Cr8tive Engine installed
- [ ] Both addons appear in Blender addon list
- [ ] AI Router discovers set-builder addon automatically

### Platform Integration

- [ ] Frontend dependencies installed (`pnpm install`)
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] BLENDER_EXECUTABLE_PATH configured in backend environment
- [ ] WebRTC signaling URL configured in frontend environment
- [ ] Cr8 Engine runs on port 8000 (`uvicorn main:app --reload`)
- [ ] Frontend development server runs (`pnpm dev`)

### End-to-End Testing

- [ ] Signaling server displays "listening on ws://127.0.0.1:8443"
- [ ] Cr8 Engine shows WebSocket endpoints active
- [ ] Frontend connects to WebSocket successfully
- [ ] Blender instance launches through Cr8 Engine
- [ ] WebRTC connection established between Blender and frontend
- [ ] Viewport streaming displays in browser
- [ ] B.L.A.Z.E AI agent responds to natural language commands

## Development

### Start All Services

```bash
# Terminal 1: WebRTC Signaling Server
cd gst-plugins-rs/signalling
cargo run --bin gst-webrtc-signalling-server

# Terminal 2: Cr8 Engine Backend
cd backend/cr8_engine
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Frontend
cd frontend
pnpm dev

# Terminal 4: Launch Blender (optional, Cr8 Engine can launch automatically)
# /path/to/your/custom/blender/build_linux/bin/blender
```

### Access Points

- **Frontend**: http://localhost:3000 (or Vite dev server port)
- **Cr8 Engine API**: http://localhost:8000
- **WebSocket**: ws://localhost:8000/ws
- **WebRTC Signaling**: ws://127.0.0.1:8443

## Architecture

The Cr8-xyz system combines multiple technologies:

```
Browser ↔ WebRTC Stream ↔ Custom Blender ↔ WebSocket ↔ Cr8 Engine ↔ B.L.A.Z.E AI
                ↑                       ↓
         GStreamer Pipeline        Blender Addons
                ↑                       ↓
         webrtcsink Plugin        AI Router System
```

### Key Technologies

- **WebRTC**: Real-time peer-to-peer streaming
- **GStreamer**: Video processing and WebRTC encoding
- **Blender**: 3D engine with WebRTC integration
- **FastAPI**: WebSocket communication and AI orchestration
- **B.L.A.Z.E**: Dynamic AI agent with extensible capabilities

## Troubleshooting

### Common Issues

- **WebRTC Connection Failed**: Check signaling server status and firewall settings
- **"No such element or plugin"**: Verify GST_PLUGIN_PATH and plugin installation
- **Blender Launch Failed**: Check BLENDER_EXECUTABLE_PATH and addon installation
- **AI Commands Not Working**: Verify set-builder addon is enabled and discovered

### Debug Commands

```bash
# Test GStreamer plugin
gst-inspect-1.0 webrtcsink

# Test signaling server
curl -i http://localhost:8443

# Check Blender path
/path/to/blender --version

# Test WebSocket connection
wscat -c ws://localhost:8000/ws
```

## Contributing

We welcome contributions! Please see our architecture documentation:

- [B.L.A.Z.E Architecture](docs/BLAZE_ARCHITECTURE.md)
- [Blender Multi Addon Architecture](docs/BLENDER_MULTI_ADDON_ARCHITECTURE.md)

## License

This project is licensed under the GNU Affero General Public License v3.0 or later - see the [LICENSE](docs/LICENSE) file for details.
