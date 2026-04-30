#!/bin/bash
# Omission Arena: GitHub -> Office Mac Auto-Sync
# Path-based safety classification and deployment ledgering.

REPO_DIR="/Users/HN/MLLM/gamma"
LEDGER="$REPO_DIR/local/game001/deployments.jsonl"
BRANCH="main"

cd "$REPO_DIR" || { echo "Could not cd to $REPO_DIR"; exit 1; }

# 1. Fetch latest from GitHub
git fetch origin "$BRANCH" || { echo "Fetch failed"; exit 1; }

# 2. Check for changes
LOCAL_HASH=$(git rev-parse HEAD)
REMOTE_HASH=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL_HASH" == "$REMOTE_HASH" ]; then
    echo "No changes detected."
    exit 0
fi

# 3. Identify and Classify changed files
CHANGED_FILES=$(git diff --name-only "$LOCAL_HASH" "$REMOTE_HASH")

FROZEN_BLOCK=0
GUARDED_COUNT=0
SAFE_COUNT=0
FILE_DETAILS=""

for file in $CHANGED_FILES; do
    # Frozen Core: src/runtime, src/engine, src/peft
    if [[ $file == src/gamma_runtime/* ]] || [[ $file == src/sde_engine/* ]] || [[ $file == src/gamma_peft/* ]]; then
        FROZEN_BLOCK=1
        FILE_DETAILS="$FILE_DETAILS [FROZEN]$file"
    # Guarded: configs
    elif [[ $file == context/configs/* ]]; then
        GUARDED_COUNT=$((GUARDED_COUNT + 1))
        FILE_DETAILS="$FILE_DETAILS [GUARDED]$file"
    # Safe: UI, Mailbox, Docs, specific tools
    else
        SAFE_COUNT=$((SAFE_COUNT + 1))
        FILE_DETAILS="$FILE_DETAILS [SAFE]$file"
    fi
done

# 4. Decision Logic
STATUS="PENDING"
REASON=""

if [ $FROZEN_BLOCK -eq 1 ]; then
    STATUS="BLOCKED"
    REASON="Touches frozen core paths (src/)"
elif [ $GUARDED_COUNT -gt 0 ]; then
    # Currently blocking guarded changes for manual review, though policy could be relaxed later.
    STATUS="BLOCKED"
    REASON="Touches guarded config paths (context/configs/)"
else
    STATUS="APPLIED"
    REASON="All changes are in safe paths"
    # Apply changes (assuming fast-forward is possible)
    git merge --ff-only "origin/$BRANCH" || { STATUS="FAILED"; REASON="Merge failed (diverged history)"; }
fi

# 5. Record to Deployment Ledger
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
# Create JSON entry (simplified escaping for shell)
LOG_ENTRY="{\"timestamp\": \"$TIMESTAMP\", \"commit\": \"$REMOTE_HASH\", \"status\": \"$STATUS\", \"reason\": \"$REASON\", \"files\": \"$FILE_DETAILS\"}"

mkdir -p "$(dirname "$LEDGER")"
echo "$LOG_ENTRY" >> "$LEDGER"

# 6. Final Report
echo "Deployment $STATUS: $REASON"
if [ "$STATUS" == "BLOCKED" ]; then
    echo "Files causing block: $FILE_DETAILS"
fi
