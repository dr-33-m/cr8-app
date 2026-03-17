#!/bin/bash
# launch-blender.sh — Self-contained Blender launcher for VastAI GPU instances.
# Called by cr8_engine via SSH. Handles the entire prerequisite chain:
#   1. Environment setup
#   2. NVIDIA X driver installation (matching host driver)
#   3. Xorg startup and verification
#   4. Blender launch with addon connection
#
# Usage: /opt/cr8/launch-blender.sh <username>
# Output: Prints structured status lines prefixed with CR8: for parsing.
#         Final line is either "CR8:PID:<number>" or "CR8:ERROR:<reason>"

set -euo pipefail

USERNAME="${1:?Usage: launch-blender.sh <username>}"
LOGFILE="/tmp/blender_${USERNAME}.log"

# Structured output for the engine to parse
cr8_status() { echo "CR8:STATUS:$1"; }
cr8_error()  { echo "CR8:ERROR:$1" >&2; echo "CR8:ERROR:$1"; exit 1; }
cr8_pid()    { echo "CR8:PID:$1"; }

# ============================================================
# Step 1: Environment — make env vars available
# ============================================================
cr8_status "env_setup"
set -a
. /etc/environment 2>/dev/null || true
set +a

# ============================================================
# Step 2: NVIDIA X driver — use toolkit or download as fallback
# ============================================================
cr8_status "nvidia_driver"

if ! command -v nvidia-smi &>/dev/null; then
    cr8_error "nvidia_not_found"
fi

DRIVER_VERSION=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)
if [ -z "$DRIVER_VERSION" ]; then
    cr8_error "nvidia_no_version"
fi

# The NVIDIA Container Toolkit (NVIDIA_DRIVER_CAPABILITIES=all) may already
# mount nvidia_drv.so at its own path. Check both locations before downloading.
TOOLKIT_DRV="/usr/lib/x86_64-linux-gnu/nvidia/xorg/nvidia_drv.so"
STANDARD_DRV="/usr/lib/xorg/modules/drivers/nvidia_drv.so"

if [ -f "$TOOLKIT_DRV" ]; then
    cr8_status "nvidia_toolkit:${DRIVER_VERSION}"
    NVIDIA_MODULE_PATH="/usr/lib/x86_64-linux-gnu/nvidia/xorg"
elif [ -f "$STANDARD_DRV" ]; then
    cr8_status "nvidia_cached:${DRIVER_VERSION}"
    NVIDIA_MODULE_PATH=""
else
    cr8_status "nvidia_downloading:${DRIVER_VERSION}"
    cd /tmp

    if ! wget -q "https://us.download.nvidia.com/XFree86/Linux-x86_64/${DRIVER_VERSION}/NVIDIA-Linux-x86_64-${DRIVER_VERSION}.run" -O nvidia.run 2>/dev/null; then
        cr8_error "nvidia_download_failed:${DRIVER_VERSION}"
    fi

    chmod +x nvidia.run
    if ! ./nvidia.run --extract-only --target nvidia-driver >/dev/null 2>&1; then
        rm -f nvidia.run
        cr8_error "nvidia_extract_failed:${DRIVER_VERSION}"
    fi

    mkdir -p /usr/lib/xorg/modules/drivers /usr/lib/xorg/modules/extensions
    cp nvidia-driver/nvidia_drv.so /usr/lib/xorg/modules/drivers/
    cp nvidia-driver/libglxserver_nvidia.so.${DRIVER_VERSION} \
       /usr/lib/xorg/modules/extensions/libglxserver_nvidia.so 2>/dev/null || true
    cp -n nvidia-driver/libEGL_nvidia.so.${DRIVER_VERSION} \
       /usr/lib/x86_64-linux-gnu/ 2>/dev/null || true
    cp -n nvidia-driver/libGLX_nvidia.so.${DRIVER_VERSION} \
       /usr/lib/x86_64-linux-gnu/ 2>/dev/null || true

    rm -rf nvidia.run nvidia-driver
    cr8_status "nvidia_installed:${DRIVER_VERSION}"
    NVIDIA_MODULE_PATH=""
fi

# ============================================================
# Step 3: Xorg — start if not running, verify it works
# Cascading fallback: try nvidia DDX first, then modesetting DDX.
# nvidia DDX works on most instances (even some with modeset=Y).
# modesetting DDX works when nvidia DDX can't acquire modesetting permission.
# ============================================================
cr8_status "xorg_setup"

if DISPLAY=:2 xdpyinfo >/dev/null 2>&1; then
    cr8_status "xorg_already_running"
else
    # Detect GPU PCI BusID and convert from nvidia-smi hex to Xorg decimal.
    RAW_BUS_ID=$(nvidia-smi --query-gpu=pci.bus_id --format=csv,noheader | head -1)
    BUS_HEX=$(echo "$RAW_BUS_ID" | sed 's/^[^:]*:\([^:]*\):.*/\1/')
    DEV_HEX=$(echo "$RAW_BUS_ID" | sed 's/^[^:]*:[^:]*:\([^.]*\).*/\1/')
    FUNC=$(echo "$RAW_BUS_ID" | sed 's/.*\.\(.*\)/\1/')
    GPU_BUS_ID="PCI:$((16#$BUS_HEX)):$((16#$DEV_HEX)):${FUNC}"

    if [ -z "$GPU_BUS_ID" ]; then
        cr8_error "xorg_no_gpu_busid"
    fi

    mkdir -p /etc/X11

    # Build optional ModulePath section for container toolkit driver
    MODULE_PATH_SECTION=""
    if [ -n "${NVIDIA_MODULE_PATH:-}" ]; then
        MODULE_PATH_SECTION="
Section \"Files\"
    ModulePath \"${NVIDIA_MODULE_PATH}\"
    ModulePath \"/usr/lib/xorg/modules\"
EndSection
"
    fi

    # Helper: write Xorg config for a given driver and attempt to start on display :2
    try_xorg_driver() {
        local DRIVER="$1"
        local EXTRA_OPTS="$2"

        cat > /etc/X11/xorg-headless.conf << XEOF
Section "ServerLayout"
    Identifier "Layout0"
    Screen 0 "Screen0"
EndSection
${MODULE_PATH_SECTION}
Section "Monitor"
    Identifier "Monitor0"
    VendorName "Unknown"
    ModelName "Unknown"
    Modeline "1920x1080_60.00" 173.00 1920 2048 2248 2576 1080 1083 1088 1120 -hsync +vsync
EndSection

Section "Device"
    Identifier "Device0"
    Driver "${DRIVER}"
    VendorName "NVIDIA Corporation"
    BusID "${GPU_BUS_ID}"
${EXTRA_OPTS}
EndSection

Section "Screen"
    Identifier "Screen0"
    Device "Device0"
    Monitor "Monitor0"
    DefaultDepth 24
    SubSection "Display"
        Depth 24
        Modes "1920x1080_60.00"
        Virtual 1920 1080
    EndSubSection
EndSection

Section "ServerFlags"
    Option "AutoAddDevices" "False"
EndSection
XEOF

        cr8_status "xorg_trying:${DRIVER}:${GPU_BUS_ID}"
        Xorg :2 -noreset -sharevts -ac \
             -config /etc/X11/xorg-headless.conf \
             -logfile /var/log/Xorg.2.log >/dev/null 2>&1 &
        local XORG_PID=$!

        for i in $(seq 1 10); do
            sleep 1
            if DISPLAY=:2 xdpyinfo >/dev/null 2>&1; then
                cr8_status "xorg_ready:${DRIVER}"
                return 0
            fi
            # If the process already exited, no point waiting
            if ! kill -0 $XORG_PID 2>/dev/null; then
                break
            fi
        done

        # Failed — kill if still running
        kill $XORG_PID 2>/dev/null; wait $XORG_PID 2>/dev/null
        return 1
    }

    XORG_OK=false

    # Attempt 1: nvidia DDX — works on most instances including many with modeset=Y
    NVIDIA_OPTS='    Option "AllowEmptyInitialConfiguration" "True"
    Option "ConnectedMonitor" "DFP-0"'
    if try_xorg_driver "nvidia" "$NVIDIA_OPTS"; then
        XORG_OK=true
    fi

    # Attempt 2: modesetting DDX — fallback when nvidia DDX can't acquire modesetting
    if [ "$XORG_OK" = false ]; then
        cr8_status "xorg_nvidia_failed_trying_modesetting"
        if try_xorg_driver "modesetting" ""; then
            XORG_OK=true
        fi
    fi

    if [ "$XORG_OK" = false ]; then
        echo "--- Xorg.2.log (last attempt) ---" >&2
        cat /var/log/Xorg.2.log >&2 2>/dev/null || true
        cr8_error "xorg_all_drivers_failed"
    fi
fi

# ============================================================
# Step 3.5: GStreamer pre-flight — verify pipeline can work
# ============================================================
cr8_status "gst_preflight"

# Auto-detect gst-plugin-scanner
GST_SCANNER=$(find /usr/lib -name gst-plugin-scanner -type f 2>/dev/null | head -1)
if [ -n "$GST_SCANNER" ]; then
    export GST_PLUGIN_SCANNER="$GST_SCANNER"
    cr8_status "gst_scanner:found"
else
    cr8_status "gst_scanner:not_found"
fi

# Verify webrtcsink element loads
if command -v gst-inspect-1.0 &>/dev/null; then
    if GST_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/gstreamer-1.0 \
       gst-inspect-1.0 webrtcsink >/dev/null 2>&1; then
        cr8_status "gst_webrtcsink:ok"
    else
        cr8_status "gst_webrtcsink:FAILED"
        # Check for missing shared libraries
        PLUGIN_SO="/usr/lib/x86_64-linux-gnu/gstreamer-1.0/libgstrswebrtc.so"
        if [ -f "$PLUGIN_SO" ]; then
            MISSING=$(ldd "$PLUGIN_SO" 2>/dev/null | grep "not found" || true)
            [ -n "$MISSING" ] && cr8_status "gst_missing_libs:${MISSING}"
        else
            cr8_status "gst_plugin_file:MISSING"
        fi
    fi
fi

# Verify GLX on display :2
if command -v glxinfo &>/dev/null; then
    if DISPLAY=:2 glxinfo -B >/dev/null 2>&1; then
        cr8_status "glx:ok"
    else
        cr8_status "glx:FAILED"
    fi
fi

# ============================================================
# Step 4: Launch Blender — deferred addon operator via timer
# ============================================================
cr8_status "blender_launching"

DISPLAY=:2 \
CR8_USERNAME="${USERNAME}" \
GST_GL_WINDOW=x11 \
GST_GL_PLATFORM=glx \
GST_DEBUG="3,webrtcsink:5,rswebrtc:5,webrtc-signaller:5,gstglcontext:5,gstgldisplay:5,gstglwindow:5,gstpipeline:4" \
GST_DEBUG_FILE="/tmp/gst_debug_${USERNAME}.log" \
GST_PLUGIN_SCANNER="${GST_PLUGIN_SCANNER:-}" \
GST_PLUGIN_PATH="/usr/lib/x86_64-linux-gnu/gstreamer-1.0" \
nohup blender --app-template cr8 \
    > "$LOGFILE" 2>&1 &

BLENDER_PID=$!

# Quick check: did it crash immediately?
sleep 1
if ! kill -0 $BLENDER_PID 2>/dev/null; then
    echo "--- blender log ---" >&2
    tail -20 "$LOGFILE" >&2 2>/dev/null || true
    cr8_error "blender_crashed"
fi

cr8_pid "$BLENDER_PID"
