#!/bin/bash
# Run Guard in bounded loop mode

# Load .env if it exists
if [ -f .env ]; then
  export $(echo $(grep -v '^#' .env | xargs) | envsubst)
fi

# Default to 5 iterations for safety
ITERATIONS=${GUARD_MAX_ITERATIONS:-5}

python3 -m core.start_guard --iterations $ITERATIONS
