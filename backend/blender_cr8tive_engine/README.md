# Blender Cr8tive Engine

## Overview

The Blender Cr8tive Engine is a headless Blender addon that executes commands from the Cr8-xyz platform. It enables:

- Remote control of Blender via WebSocket
- Real-time viewport streaming via WebRTC
- AI-assisted 3D content creation
- AI orchestration for multiple asset management addons

## Requirements

- Blender (Our unOfficial version of blender with Pixel Streaming)
- Python 3.10+
- WebSocket connection to Cr8_engine

## Prerequisites

This addon requires the **Multi-Registry Asset Manager** (set-builder) addon as a prerequisite. The set-builder addon provides essential asset management capabilities that are discovered and utilized by the AI router.

### Multi-Registry Asset Manager (Required)

- **Repository**: [https://code.cr8-xyz.art/Cr8-xyz/set-builder](https://code.cr8-xyz.art/Cr8-xyz/set-builder)
- **Version**: 2.0.0
- **Purpose**: AI-capable multi-registry asset addon with direct API access for fast asset search across Polyhaven, BlenderKit, and more
- **Features**:
  - Polyhaven integration (HDRIs, textures, models)
  - AI-powered asset selection and scoring
  - Natural language search interface
  - B.L.A.Z.E compatible for conversational asset management
  - Automatic scene integration and material setup

## Installation

### 1. Install Set-Builder Addon (Prerequisite)

1. Clone the set-builder repository:

   ```bash
   git clone https://code.cr8-xyz.art/Cr8-xyz/set-builder.git
   cd set-builder
   ```

2. Package the set-builder addon:

   ```bash
   python package_addon.py
   # This creates: dist/multi_registry_asset_manager_v1.0.0.zip
   ```

3. Install in Blender:
   - Open Blender
   - Go to Edit > Preferences > Add-ons
   - Click "Install..." and select the generated zip file
   - Enable "Multi-Registry Asset Manager"

### 2. Install Blender Cr8tive Engine

1. Package the blender_cr8tive_engine addon:

   ```bash
   # Navigate to the blender_cr8tive_engine directory
   python package_addon.py
   # This creates: dist/blender_cr8tive_engine_v1.0.0.zip
   ```

2. Install the addon in Blender:

   - Open Blender
   - Go to Edit > Preferences > Add-ons
   - Click "Install..." and select the `blender_cr8tive_engine` zip file
   - Enable the addon

3. Verify installation:
   - Both addons should appear in the addon list
   - The AI Router should automatically discover the Multi-Registry Asset Manager

## Packaging

Both addons include packaging scripts for easy distribution:

### Package Set-Builder (Prerequisite)

```bash
# From set-builder directory
python package_addon.py
# Creates: dist/multi_registry_asset_manager_v1.0.0.zip
```

### Package Blender Cr8tive Engine

```bash
# From blender_cr8tive_engine directory
python package_addon.py
# Creates: dist/blender_cr8tive_engine_v1.0.0.zip
```

### Development Packages

For development builds that include source files:

```bash
python package_addon.py --dev
```

## Architecture

The Cr8tive Engine system consists of two complementary addons:

### Blender Cr8tive Engine (AI Router)

- **Role**: Main orchestration and command routing
- **Discovery**: Automatically finds AI-capable addons
- **Integration**: WebSocket communication with CR8 Engine backend

### Multi-Registry Asset Manager (Asset Provider)

- **Role**: Provides asset management capabilities
- **Registries**: Polyhaven integration (HDRIs, textures, models)
- **AI Integration**: Natural language asset search and download

The AI Router discovers and utilizes the asset management tools from the Multi-Registry Asset Manager, creating a comprehensive AI-assisted 3D workflow.

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
