# Custom Blender Build with WebRTC Viewport Streaming

## Overview

The Cr8-xyz platform uses a custom build of Blender that includes integrated WebRTC viewport streaming capabilities for real-time browser streaming.

## Repository Information

- **Repository**: https://code.cr8-xyz.art/Cr8-xyz/blender.git
- **Branch**: `webrtc-viewport-streaming`

## Build Process

### 1. Clone the Custom Blender Repository

```bash
git clone https://code.cr8-xyz.art/Cr8-xyz/blender.git
cd blender
git checkout webrtc-viewport-streaming
```

### 2. Install Build Dependencies

Follow the official [Blender Linux Build Documentation](https://developer.blender.org/docs/handbook/building_blender/linux/) for detailed requirements.

### 3. Update Submodules

```bash
make update
```

### 4. Build Blender

```bash
make
```

## Integration with Cr8-xyz

After building, configure the path in your `backend/cr8_engine/.env`:

```bash
BLENDER_EXECUTABLE_PATH=/path/to/your/custom/blender/build_linux/bin/blender
```

## Install Prerequisite Addons

After successfully building the custom Blender, install these two required addons:

### 1. Multi-Registry Asset Manager (set-builder)

**Repository**: https://code.cr8-xyz.art/Cr8-xyz/set-builder

```bash
# Clone and package the set-builder addon
git clone https://code.cr8-xyz.art/Cr8-xyz/set-builder.git
cd set-builder
python package_addon.py
```

**Install in Blender**:

- Open Blender
- Go to Edit > Preferences > Add-ons
- Click "Install..." and select `dist/multi_registry_asset_manager_v1.0.0.zip`
- Enable the addon

### 2. Blender Cr8tive Engine

```bash
# From the cr8-app repository
cd backend/blender_cr8tive_engine
python package_addon.py
```

**Install in Blender**:

- Open Blender
- Go to Edit > Preferences > Add-ons
- Click "Install..." and select `dist/blender_cr8tive_engine_v1.0.0.zip`
- Enable the addon

Both addons should appear in the addon list, and the AI Router should automatically discover the Multi-Registry Asset Manager.

---

**Branch**: webrtc-viewport-streaming  
**Built with**: GStreamer 1.22+ WebRTC integration
