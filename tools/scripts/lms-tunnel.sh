#!/bin/bash
# Managed LMS Tunnel Script
# Maintains an SSH tunnel from localhost:1234 to the Office Mac

KEY="/Users/hamednejat/.ssh/bridger_id_ed25519"
REMOTE="HN@100.69.184.42"
PORT="1234"

echo "[TUNNEL] Starting managed tunnel on port $PORT..."

# Run SSH in foreground (no -f) to allow supervisor monitoring
# -N: Do not execute remote command
# -L: Local port forwarding
# -o ExitOnForwardFailure=yes: Ensure it exits if port is busy
# -o ServerAliveInterval=30: Keep connection alive
# -o BatchMode=yes: No password prompting

exec ssh -i "$KEY" -N -L "$PORT:localhost:$PORT" \
    -o ExitOnForwardFailure=yes \
    -o ServerAliveInterval=30 \
    -o BatchMode=yes \
    -o StrictHostKeyChecking=no \
    "$REMOTE"
