#!/bin/bash
# Run Guard in one-shot mode

# Load .env if it exists
if [ -f .env ]; then
  export $(echo $(grep -v '^#' .env | xargs) | envsubst)
fi

python3 -m core.start_guard --once
