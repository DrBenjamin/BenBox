#!/bin/bash
set -e

# Setting up environment variables for display
export DISPLAY=:$DISPLAY_NUM

# Cleaning up any existing X server lock files and processes
rm -f /tmp/.X${DISPLAY_NUM}-lock
rm -f /tmp/.X11-unix/X${DISPLAY_NUM}

# Killing any existing Xvfb, x11vnc processes to prevent conflicts
pkill -f "Xvfb :${DISPLAY_NUM}" || true
pkill -f "x11vnc" || true
pkill -f "novnc" || true

# Adding a small delay to ensure processes are fully terminated
sleep 2

# Starting Xvfb
Xvfb :$DISPLAY_NUM -screen 0 ${WIDTH}x${HEIGHT}x24 &
XVFB_PID=$!

# Waiting for Xvfb to start properly
sleep 3

# Starting x11vnc
x11vnc -display :$DISPLAY_NUM -forever -nopw -shared -bg

# Starting noVNC
novnc_proxy --vnc localhost:5900 --listen 6080 &

# Starting Phoenix app (compiled version) in a loop
while true; do
    echo "Starting BenBox Phoenix app..."
    /home/ben/BenBox/dist/BenBox/BenBox
    
    EXIT_CODE=$?
    echo "BenBox Phoenix app exited with code $EXIT_CODE. Restarting in 3 seconds..."
    sleep 3
done
