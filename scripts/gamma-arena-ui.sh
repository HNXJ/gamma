#!/bin/bash
# Wrapper for Gamma Arena UI
# Usage: ./gamma-arena-ui.sh
# Policy: Mandatory 30s timeout for foreground startup; backgrounding thereafter.

cd computational/gamma-arena
echo "Starting Gamma Arena UI on port 3012..."
perl -e 'alarm shift; exec @ARGV' 30 npm run dev -- --port 3012 --host 0.0.0.0 &
PID=$!
echo "Process started with PID: $PID"
echo "Verification: curl -I http://localhost:3012"
