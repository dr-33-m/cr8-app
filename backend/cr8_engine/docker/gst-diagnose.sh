#!/bin/bash
# GStreamer diagnostic script for VastAI instances.
# Run via SSH: ssh root@vastai-host /opt/cr8/gst-diagnose.sh

echo "=== GStreamer Version ==="
gst-inspect-1.0 --version 2>&1

echo ""
echo "=== Plugin Scanner ==="
find /usr/lib -name gst-plugin-scanner -type f 2>/dev/null || echo "NOT FOUND"

echo ""
echo "=== webrtcsink Element ==="
GST_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/gstreamer-1.0 \
GST_DEBUG=4 gst-inspect-1.0 webrtcsink 2>&1

echo ""
echo "=== libgstrswebrtc.so Dependencies ==="
ldd /usr/lib/x86_64-linux-gnu/gstreamer-1.0/libgstrswebrtc.so 2>&1

echo ""
echo "=== Missing Libraries ==="
MISSING=$(ldd /usr/lib/x86_64-linux-gnu/gstreamer-1.0/libgstrswebrtc.so 2>&1 | grep "not found")
if [ -n "$MISSING" ]; then
    echo "$MISSING"
else
    echo "None — all dependencies satisfied"
fi

echo ""
echo "=== GLX Info ==="
DISPLAY=:2 glxinfo -B 2>&1 || echo "glxinfo not available or display :2 not running"

echo ""
echo "=== X Display ==="
DISPLAY=:2 xdpyinfo 2>&1 | head -20

echo ""
echo "=== NVIDIA ==="
nvidia-smi 2>&1 | head -10

echo ""
echo "=== GStreamer GL Elements ==="
GST_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/gstreamer-1.0 \
gst-inspect-1.0 2>&1 | grep -iE "gl|opengl"

echo ""
echo "=== GStreamer Debug Log (last run) ==="
tail -100 /tmp/gst_debug_*.log 2>/dev/null || echo "No GST debug log found"
