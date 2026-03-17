#!/bin/bash
# start-xorg.sh — VastAI onstart script.
# Persists environment variables so they're available in SSH sessions.
# The actual GPU setup (nvidia driver, Xorg, Blender) is handled by
# /opt/cr8/launch-blender.sh, called by cr8_engine via SSH on demand.
set -e

# Export env vars so they're available in SSH sessions
# (VastAI template env vars like WS_URL, CR8_SIGNALLER_URI, TURN_SERVER)
env | grep _ >> /etc/environment
echo "Environment variables persisted to /etc/environment"
