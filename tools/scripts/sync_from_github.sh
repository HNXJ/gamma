#!/bin/bash
REPO_DIR="/Users/HN/MLLM/gamma"
LEDGER="$REPO_DIR/local/game001/deployments.jsonl"
PYTHON_BIN="/Users/HN/miniconda3/envs/mllm/bin/python3"
PYTHONPATH="$REPO_DIR/src"
BRANCH="main"
HOTFIX_FLAG="$REPO_DIR/emergency_hotfix.flag"

cd "$REPO_DIR" || exit 1
git fetch origin "$BRANCH"
LOCAL_HASH=$(git rev-parse HEAD)
REMOTE_HASH=$(git rev-parse "origin/$BRANCH")
if [ "$LOCAL_HASH" == "$REMOTE_HASH" ]; then exit 0; fi

CHANGED_FILES=$(git diff --name-only "$LOCAL_HASH" "$REMOTE_HASH")
CLASS_C=0
for file in $CHANGED_FILES; do
    if [[ $file == src/* ]]; then CLASS_C=1; fi
done

if [ $CLASS_C -eq 1 ] && [ ! -f "$HOTFIX_FLAG" ]; then
    echo "BLOCKED: Requires hotfix flag"
    exit 1
fi

git merge --ff-only "origin/$BRANCH"
export PYTHONPATH="$PYTHONPATH"
$PYTHON_BIN -c "import gamma_runtime.orchestrator; import apps.council_app; print('Imports OK')"
if [ $? -eq 0 ]; then
    if [ $CLASS_C -eq 1 ]; then
        pkill -f "src/apps/council_app.py"
        pkill -f "launch_hub.py"
        pkill -f "science_worker.py"
        nohup $PYTHON_BIN src/apps/council_app.py > local/logs/council_app.log 2>&1 &
    fi
fi
