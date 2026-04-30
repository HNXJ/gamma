#!/bin/bash
# GAMMA PROTOCOL: Production Main Auto-Sync Script
# Office Mac Deployment Logic (M3 Max)

REPO_DIR="/Users/HN/MLLM/gamma"
LEDGER="$REPO_DIR/local/game001/deployments.jsonl"
PYTHON_BIN="/Users/HN/miniconda3/envs/mllm/bin/python3"
PYTHONPATH="$REPO_DIR/src"
BRANCH="main"
HOTFIX_FLAG="$REPO_DIR/emergency_hotfix.flag"

cd "$REPO_DIR" || { echo "ERROR: Could not cd to $REPO_DIR"; exit 1; }

# 1. Fetch from origin
git fetch origin "$BRANCH" || { echo "ERROR: Git fetch failed"; exit 1; }

LOCAL_HASH=$(git rev-parse HEAD)
REMOTE_HASH=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL_HASH" == "$REMOTE_HASH" ]; then
    # echo "No changes detected."
    exit 0
fi

# 2. Classification
CHANGED_FILES=$(git diff --name-only "$LOCAL_HASH" "$REMOTE_HASH")
CLASS_C_TRIGGERED=0
CLASS_B_TRIGGERED=0
CLASS_A_TRIGGERED=0
FILE_DETAILS=""

for file in $CHANGED_FILES; do
    if [[ $file == src/gamma_runtime/* ]] || [[ $file == src/sde_engine/* ]] || [[ $file == src/gamma_peft/* ]] || [[ $file == src/apps/* ]]; then
        CLASS_C_TRIGGERED=1
        FILE_DETAILS="$FILE_DETAILS [CLASS_C]$file"
    elif [[ $file == context/configs/* ]] || [[ $file == tools/deploy/* ]]; then
        CLASS_B_TRIGGERED=1
        FILE_DETAILS="$FILE_DETAILS [CLASS_B]$file"
    else
        CLASS_A_TRIGGERED=1
        FILE_DETAILS="$FILE_DETAILS [CLASS_A]$file"
    fi
done

# 3. Decision Logic
SHOULD_APPLY=0
STATUS="PENDING"
REASON=""

if [ $CLASS_C_TRIGGERED -eq 1 ]; then
    if [ -f "$HOTFIX_FLAG" ]; then
        SHOULD_APPLY=1
        STATUS="HOTFIX_APPLIED"
        REASON="Class C changes allowed via emergency hotfix flag"
    else
        SHOULD_APPLY=0
        STATUS="BLOCKED"
        REASON="Touches Class C paths (src/); requires manual approval or hotfix flag"
    fi
else
    # Class A and B are auto-applied in this configuration
    SHOULD_APPLY=1
    STATUS="APPLIED"
    REASON="Safe or Guarded changes only"
fi

if [ $SHOULD_APPLY -eq 1 ]; then
    # 4. Sync
    git merge --ff-only "origin/$BRANCH" || { 
        STATUS="FAILED"
        REASON="Merge failed (FF-only check failed)"
        SHOULD_APPLY=0
    }
fi

if [ $SHOULD_APPLY -eq 1 ]; then
    # 5. Smoke Test
    echo "Running Smoke Tests..."
    export PYTHONPATH="$PYTHONPATH"
    $PYTHON_BIN -c "import gamma_runtime.orchestrator; import apps.council_app; print('Imports OK')" > /tmp/gamma_smoke.log 2>&1
    SMOKE_RC=$?
    
    if [ $SMOKE_RC -ne 0 ]; then
        echo "SMOKE TEST FAILED! Rolling back..."
        git reset --hard "$LOCAL_HASH"
        STATUS="FAILED_SMOKE"
        REASON="Post-deploy smoke test failed (imports or startup crash). Rolled back."
    else
        STATUS="SUCCESS"
        # 6. Service Restart (if Class C or significant Class B)
        if [ $CLASS_C_TRIGGERED -eq 1 ]; then
            echo "Restarting services for Class C change..."
            # Terminate old processes (using specific entry point names to be safe)
            pkill -f "src/apps/council_app.py"
            pkill -f "launch_hub.py"
            pkill -f "science_worker.py"
            
            # Launch new entry point in background
            nohup $PYTHON_BIN src/apps/council_app.py > local/logs/council_app.log 2>&1 &
            REASON="$REASON | Services restarted (council_app.py)"
        fi
    fi
fi

# 7. Record to Ledger
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
LOG_ENTRY="{\"timestamp\": \"$TIMESTAMP\", \"commit\": \"$REMOTE_HASH\", \"status\": \"$STATUS\", \"reason\": \"$REASON\", \"files\": \"$FILE_DETAILS\"}"
mkdir -p "$(dirname "$LEDGER")"
echo "$LOG_ENTRY" >> "$LEDGER"

echo "Result: $STATUS - $REASON"
