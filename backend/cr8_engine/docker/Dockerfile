FROM nvidia/cuda:12.2.2-runtime-ubuntu22.04

LABEL maintainer="cr8-app"
LABEL description="Blender 5.1 with GStreamer WebRTC streaming for VastAI GPU instances"

ENV DEBIAN_FRONTEND=noninteractive

# --- System packages ---
# GStreamer (core + plugins + WebRTC deps), X11/Xorg (headless rendering),
# OpenGL, and misc libs required by Blender
#
# Ubuntu 22.04 ships GStreamer 1.20, but the gst-plugins-rs binaries (libgstrswebrtc.so)
# are built against GStreamer 1.22 on the host. Use Savoury PPA for GStreamer 1.24 (ABI-compatible).
RUN apt-get update && apt-get install -y --no-install-recommends software-properties-common && \
    add-apt-repository -y ppa:savoury1/multimedia && \
    apt-get update && apt-get install -y --no-install-recommends \
    # GStreamer core and plugins
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-gl \
    gstreamer1.0-x \
    gstreamer1.0-nice \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    libgstreamer-gl1.0-0 \
    # X11 and Xorg for headless GPU rendering
    xserver-xorg-core \
    x11-utils \
    # OpenGL / EGL
    libegl1 \
    libgl1 \
    libgles2 \
    libgbm1 \
    libdrm2 \
    # Wayland (Blender links against these)
    libwayland-client0 \
    libwayland-cursor0 \
    libwayland-egl1 \
    libwayland-server0 \
    # X11 libs
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxkbcommon0 \
    libxau6 \
    # Misc runtime deps
    libsm6 \
    libice6 \
    libbsd0 \
    libbz2-1.0 \
    libelf1 \
    libexpat1 \
    libffi8 \
    libgudev-1.0-0 \
    liblzma5 \
    liborc-0.4-0 \
    libunwind8 \
    zlib1g \
    # Utilities
    unzip \
    wget \
    mesa-utils \
    && rm -rf /var/lib/apt/lists/*

# --- GStreamer Rust plugins (pre-built) ---
# webrtcsink (rswebrtc) and rsrtp from gst-plugins-rs
COPY gst-plugins/libgstrswebrtc.so /usr/lib/x86_64-linux-gnu/gstreamer-1.0/
COPY gst-plugins/libgstrsrtp.so /usr/lib/x86_64-linux-gnu/gstreamer-1.0/

# --- Blender 5.1 build ---
COPY blender/ /opt/blender/
RUN ln -sf /opt/blender/blender /usr/local/bin/blender && \
    chmod +x /opt/blender/blender

# --- Python dependencies for addons (MUST come before extension install) ---
# blender_ai_router imports socketio during register(), so deps must exist first.
RUN /opt/blender/5.1/python/bin/python3.11 -m pip install "python-socketio[client]" websocket-client

# --- cr8 extensions (install + enable via Blender CLI) ---
# All three are required for the full cr8 pipeline:
#   - blender_ai_router: WebSocket/WebRTC connection (ws_handler.connect_websocket)
#   - cr8_sets: AI-capable asset management for production design
#   - blender_controls: Scene manipulation and viewport controls for AI agents
COPY addons/*.zip /tmp/addons/
RUN blender --background --command extension install-file \
        -r user_default -e /tmp/addons/blender_ai_router_v1.0.0.zip && \
    blender --background --command extension install-file \
        -r user_default -e /tmp/addons/cr8_sets_v1.0.0.zip && \
    blender --background --command extension install-file \
        -r user_default -e /tmp/addons/blender_controls_v1.0.0.zip && \
    rm -rf /tmp/addons

# --- cr8 Application Template ---
# Template provides: startup.blend (no splash), userpref.blend (extensions enabled),
# __init__.py (auto-connects WebSocket after startup)
COPY cr8_template/__init__.py /opt/blender/5.1/scripts/startup/bl_app_templates_system/cr8/__init__.py
COPY generate_template_blends.py /tmp/generate_template_blends.py
RUN blender --background --python /tmp/generate_template_blends.py && \
    rm /tmp/generate_template_blends.py

# --- Startup scripts ---
# start-xorg.sh: VastAI onstart — persists env vars (lightweight, runs once at boot)
# launch-blender.sh: Called by cr8_engine via SSH — handles nvidia driver, Xorg, and Blender
COPY start-xorg.sh /opt/cr8/start-xorg.sh
COPY launch-blender.sh /opt/cr8/launch-blender.sh
COPY gst-diagnose.sh /opt/cr8/gst-diagnose.sh
RUN chmod +x /opt/cr8/start-xorg.sh /opt/cr8/launch-blender.sh /opt/cr8/gst-diagnose.sh

# --- Environment ---
ENV DISPLAY=:2
ENV GST_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/gstreamer-1.0
# Tell NVIDIA Container Toolkit to mount ALL driver components from the host,
# including the Xorg driver (nvidia_drv.so), OpenGL libs, and nvidia-smi.
# This avoids version mismatches — the host's driver always matches its kernel module.
ENV NVIDIA_DRIVER_CAPABILITIES=all
ENV NVIDIA_VISIBLE_DEVICES=all
# Blender needs this to find its bundled data
ENV BLENDER_SYSTEM_RESOURCES=/opt/blender/5.1

# GPU setup (nvidia driver, Xorg, Blender) is handled on-demand by
# /opt/cr8/launch-blender.sh, called via SSH from cr8_engine.

CMD ["blender", "--version"]
