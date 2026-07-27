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

# An addon id is written down in four places (manifest, addon_ai.json, directory
# name, frontend constants) and a mismatch only shows up at runtime as
# NO_HANDLERS on a command that silently does nothing. Catch it before it ships.
ID_CHECK="$CR8_ADDONS_DIR/validate_addon_ids.py"
if [ -f "$ID_CHECK" ]; then
    echo "Checking addon id consistency..."
    if ! python3 "$ID_CHECK"; then
        echo "ERROR: addon ids are inconsistent — refusing to build."
        exit 1
    fi
    echo ""
fi

# Each addon is versioned independently, so resolve its zip by glob rather than
# pinning a version here — otherwise a version bump silently ships the old zip
# (or fails the build) until someone remembers to edit this file.
CR8_ADDONS=(cr8_router cr8_sets cr8_controls cr8_script cr8_render)
ADDON_ZIPS=()

# Fail loudly on a missing or ambiguous zip. An image built without one of these
# still starts and streams fine, and only reveals the gap much later as
# COMMAND_NOT_FOUND on a user's first render.
for addon in "${CR8_ADDONS[@]}"; do
    # shellcheck disable=SC2206
    matches=($CR8_ADDONS_DIR/$addon/dist/${addon}_v*.zip)
    if [ ! -f "${matches[0]}" ]; then
        echo "ERROR: No zip found at $CR8_ADDONS_DIR/$addon/dist/${addon}_v*.zip"
        echo "Run: (cd $CR8_ADDONS_DIR/$addon && python3 package_addon.py)"
        exit 1
    fi
    if [ "${#matches[@]}" -gt 1 ]; then
        echo "ERROR: Multiple zips for $addon — cannot tell which to ship:"
        printf '  %s\n' "${matches[@]}"
        echo "Delete the stale ones and repackage."
        exit 1
    fi
    ADDON_ZIPS+=("${matches[0]}")
    echo "  $addon -> $(basename "${matches[0]}")"
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
rm -rf "$SCRIPT_DIR/addons"
mkdir -p "$SCRIPT_DIR/addons"
for addon_zip in "${ADDON_ZIPS[@]}"; do
    cp -f "$addon_zip" "$SCRIPT_DIR/addons/"
done
echo "  Copied ${#ADDON_ZIPS[@]} cr8 addon zips (router, sets, controls, script, render)"

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
