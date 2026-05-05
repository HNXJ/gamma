#!/bin/bash
# Gamma Hub Launcher
# Madelane Golden Dark Edition

echo "🚀 Launching GAMMA HUB..."
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
./.venv/bin/python3 src/gamma_runtime/app.py
