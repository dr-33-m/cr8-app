# Blender Cr8tive Engine

## Overview

The Blender Cr8tive Engine is a headless Blender addon that executes commands from the Cr8-xyz platform. It enables:

- Remote control of Blender via WebSocket
- Real-time viewport streaming via WebRTC
- AI-assisted 3D content creation

## Requirements

- Blender (Our unOfficial version of blender with Pixel Streaming )
- Python 3.10+
- WebSocket connection to Cr8_engine

## Installation

1. Install required Python dependencies in Blender's Python environment:

   - Open Blender's Python console
   - Run:
     ```python
     import pip
     pip.main(['install', 'websocket-client'])
     ```

2. Install the addon in Blender:
   - Open Blender
   - Go to Edit > Preferences > Add-ons
   - Click "drop down button..." button in top right corner
   - Select `install from disk`
   - Select the `blender_cr8tive_engine` zip file
   - Enable the addon

## Key Features

### WebSocket Integration

- Command routing to specific handlers
- Session management
- Error handling with retries

### Asset Operations

- Append/remove assets
- Transform controls (rotate/scale)
- Asset information retrieval

### Template System

- Template wizard for scene setup
- Control parameter management
- Preset loading

## Troubleshooting

- Connection issues: Verify WS_URL and Blender console logs
- Command failures: Check Blender Python console
- Performance: Monitor WebRTC bandwidth usage
