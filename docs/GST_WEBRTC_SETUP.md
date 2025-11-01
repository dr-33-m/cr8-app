# GStreamer WebRTC Plugin Setup Guide

## Overview

Cr8-xyz requires the `webrtcsink` GStreamer plugin for WebRTC-based pixel streaming. This plugin is not included in standard GStreamer packages and must be built from source.

## System Requirements

### GStreamer Core Dependencies

Install GStreamer 1.22.0+ with required packages:

```bash
# Debian/Ubuntu
sudo apt update
sudo apt install \
  gstreamer1.0-tools \
  gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly \
  gstreamer1.0-gl \
  libgstreamer1.0-dev \
  libgstreamer-plugins-base1.0-dev \
  libgstreamer-plugins-bad1.0-dev
```

### Build Tools

```bash
# Install Rust and cargo-c for building Rust-based GStreamer plugins
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
cargo install cargo-c
```

## webrtcsink Plugin Installation

### Step 1: Build from Source

```bash
# Clone the gst-plugins-rs repository
git clone https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs.git
cd gst-plugins-rs

# Build and install the WebRTC plugin (user directory)
cargo cinstall -p gst-plugin-webrtc --prefix=$HOME/.local --release
```

### Step 2: Configure Plugin Path

Add to your shell configuration (`~/.bashrc` or `~/.zshrc`):

```bash
export GST_PLUGIN_PATH="$HOME/.local/lib/x86_64-linux-gnu/gstreamer-1.0:$GST_PLUGIN_PATH"
```

Reload your shell:

```bash
source ~/.zshrc  # or ~/.bashrc
```

### Step 3: Verify Installation

```bash
# Check if webrtcsink is available
gst-inspect-1.0 webrtcsink
```

This should display plugin information. If you get "No such element or plugin", the path is incorrect.

## Troubleshooting

### Plugin Not Found

If `gst-inspect-1.0 webrtcsink` returns "No such element or plugin":

1. **Verify plugin file exists:**

   ```bash
   ls -la ~/.local/lib/x86_64-linux-gnu/gstreamer-1.0/libgstrswebrtc.so
   ```

2. **Check GST_PLUGIN_PATH:**

   ```bash
   echo $GST_PLUGIN_PATH
   ```

3. **Set correct path:**
   ```bash
   export GST_PLUGIN_PATH="$HOME/.local/lib/x86_64-linux-gnu/gstreamer-1.0:$GST_PLUGIN_PATH"
   ```

### Permission Issues

If installation fails with permission errors:

```bash
# Use full path to cargo with sudo
sudo /home/$USER/.cargo/bin/cargo cinstall -p gst-plugin-webrtc --prefix=/usr --release
```

### Build Errors

If build fails, ensure you have the latest Rust toolchain:

```bash
rustup update
cargo update
```

## WebRTC Signaling Server Setup

### Overview

The WebRTC signaling server is a crucial component that manages peer-to-peer connections between the GStreamer producer (Blender) and consumers (web browsers). The gst-plugins-rs includes a built-in signaling server.

### Step 1: Navigate to Signaling Directory

```bash
cd gst-plugins-rs/signalling
```

### Step 2: Run the Signaling Server

```bash
# Run the signaling server on port 8443 (default)
cargo run --bin gst-webrtc-signalling-server
```

### Step 3: Verify Server is Running

The server should display output indicating it's listening on `ws://127.0.0.1:8443`.

### Step 4: Keep Server Running

The signaling server must remain running for WebRTC connections to work. Run it in a separate terminal or as a background process.

## Integration with Cr8-xyz

Once installed and verified, the plugin will be automatically used by:

1. **Custom Blender Build** - The modified Blender with streaming capabilities
2. **WebRTC Streaming Pipeline** - Processing viewport frames for web streaming
3. **Frontend Connection** - Received by `@dr33m/gstwebrtc-api` in the browser

## Notes

- The `webrtcsink` plugin handles WebRTC encoding and signaling internally
- Compatible with GStreamer 1.22+ (Debian 12+, Ubuntu 22.04+)
- Installation is permanent unless manually removed
- Environment variable must be set in each new shell session
