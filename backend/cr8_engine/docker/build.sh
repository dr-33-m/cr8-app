#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Build the cr8/blender Docker image for VastAI deployment
#
# This script stages all required artifacts into the Docker
# build context, then builds the image.
#
# Usage:
#   ./build.sh                          # build only
#   ./build.sh --push                   # build and push
#   ./build.sh --tag myrepo/blender:v2  # custom tag
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_TAG="${IMAGE_TAG:-cr8/blender:latest}"
PUSH=false

# --- Default artifact paths (override via env vars) ---
BLENDER_BUILD="${BLENDER_BUILD:-$HOME/Garage/blender-git/build_linux_release/bin}"
GST_PLUGIN_DIR="${GST_PLUGIN_DIR:-/usr/lib/x86_64-linux-gnu/gstreamer-1.0}"
CR8_ADDONS_DIR="${CR8_ADDONS_DIR:-$SCRIPT_DIR/../..}"

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --push) PUSH=true; shift ;;
        --tag) IMAGE_TAG="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo "=== cr8/blender Docker Build ==="
echo "Image tag:     $IMAGE_TAG"
echo "Blender build: $BLENDER_BUILD"
echo "GStreamer dir:  $GST_PLUGIN_DIR"
echo "cr8 addons:    $CR8_ADDONS_DIR"
echo ""

# --- Validate sources exist ---
if [ ! -f "$BLENDER_BUILD/blender" ]; then
    echo "ERROR: Blender binary not found at $BLENDER_BUILD/blender"
    echo "Set BLENDER_BUILD to your build_linux_release/bin/ directory"
    exit 1
fi

if [ ! -f "$GST_PLUGIN_DIR/libgstrswebrtc.so" ]; then
    echo "ERROR: libgstrswebrtc.so not found in $GST_PLUGIN_DIR"
    echo "Set GST_PLUGIN_DIR to the directory containing gst-plugins-rs binaries"
    exit 1
fi

CR8_ROUTER_ZIP="$CR8_ADDONS_DIR/cr8_router/dist/blender_ai_router_v1.0.0.zip"
CR8_SETS_ZIP="$CR8_ADDONS_DIR/cr8_sets/dist/cr8_sets_v1.0.0.zip"
CR8_CONTROLS_ZIP="$CR8_ADDONS_DIR/cr8_controls/dist/blender_controls_v1.0.0.zip"

for addon_zip in "$CR8_ROUTER_ZIP" "$CR8_SETS_ZIP" "$CR8_CONTROLS_ZIP"; do
    if [ ! -f "$addon_zip" ]; then
        echo "ERROR: Addon zip not found at $addon_zip"
        echo "Build the addon first, or set CR8_ADDONS_DIR to the backend/ directory"
        exit 1
    fi
done

# --- Stage artifacts into build context ---
echo "Staging artifacts..."

# Blender build (cp -rL dereferences symlinks — Docker can't follow symlinks outside build context)
# Remove stale symlink from previous builds if present
rm -f "$SCRIPT_DIR/blender" 2>/dev/null || true
if [ ! -d "$SCRIPT_DIR/blender" ]; then
    echo "  Copying Blender build (~1.2GB)... this may take a moment"
    cp -rL "$BLENDER_BUILD" "$SCRIPT_DIR/blender"
    echo "  Copied blender/ from $BLENDER_BUILD"
fi

# GStreamer plugins
mkdir -p "$SCRIPT_DIR/gst-plugins"
cp -f "$GST_PLUGIN_DIR/libgstrswebrtc.so" "$SCRIPT_DIR/gst-plugins/"
cp -f "$GST_PLUGIN_DIR/libgstrsrtp.so" "$SCRIPT_DIR/gst-plugins/"
echo "  Copied gst-plugins-rs binaries"

# cr8 addons
mkdir -p "$SCRIPT_DIR/addons"
cp -f "$CR8_ROUTER_ZIP" "$SCRIPT_DIR/addons/"
cp -f "$CR8_SETS_ZIP" "$SCRIPT_DIR/addons/"
cp -f "$CR8_CONTROLS_ZIP" "$SCRIPT_DIR/addons/"
echo "  Copied cr8 addon zips (router, sets, controls)"

echo ""

# --- Build ---
echo "Building Docker image: $IMAGE_TAG"
docker build -t "$IMAGE_TAG" -f "$SCRIPT_DIR/Dockerfile" "$SCRIPT_DIR"

# --- Cleanup staged artifacts ---
echo "Cleaning up staged artifacts..."
rm -rf "$SCRIPT_DIR/blender"
rm -rf "$SCRIPT_DIR/gst-plugins"
rm -rf "$SCRIPT_DIR/addons"

echo ""
echo "Build complete: $IMAGE_TAG"

if [ "$PUSH" = true ]; then
    echo "Pushing $IMAGE_TAG..."
    docker push "$IMAGE_TAG"
    echo "Push complete."
fi
