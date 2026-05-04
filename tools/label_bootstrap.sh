#!/bin/bash
# tools/label_bootstrap.sh
#
# GAMMA-BUS v0 Label Bootstrap Tool
# Idempotent label creation across target repos
# Usage: ./label_bootstrap.sh HNXJ/gamma
#
# Uses existing gh CLI authentication (no secrets required)
# Exits 0 on success, nonzero on errors

set -o pipefail

REPO="${1}"

if [[ -z "${REPO}" ]]; then
  echo "Usage: $0 HNXJ/gamma" >&2
  exit 1
fi

# Verify gh CLI is available and authenticated
if ! command -v gh &> /dev/null; then
  echo "ERROR: gh CLI not found in PATH" >&2
  exit 1
fi

# Check authentication (non-invasive)
if ! gh auth status &> /dev/null; then
  echo "ERROR: gh CLI not authenticated" >&2
  exit 1
fi

echo "Bootstrap labels for: ${REPO}"

# Define all v0 labels with colors
# Format: "label_name" "description" "color"
LABELS=(
  # Agent labels
  "agent:claude-code" "Claude Code agent identity" "0366d6"
  "agent:claude-cowork" "Claude Cowork agent identity" "0366d6"
  "agent:gemini-cli-flash" "Gemini CLI Flash agent identity" "f9d71c"
  "agent:gemini-cli-lite" "Gemini CLI Lite agent identity" "f9d71c"
  "agent:gemini-cli-pro" "Gemini CLI Pro agent identity" "f9d71c"
  "agent:antigravity-front" "Antigravity frontend agent identity" "9e42f5"
  "agent:gpt-teacher" "GPT Teacher agent identity" "0366d6"
  "agent:human" "Human agent identity" "ffffff"

  # Routing labels (to)
  "to:claude-code" "Route to Claude Code agent" "0366d6"
  "to:claude-cowork" "Route to Claude Cowork agent" "0366d6"
  "to:gemini-cli-flash" "Route to Gemini CLI Flash agent" "f9d71c"
  "to:gemini-cli-lite" "Route to Gemini CLI Lite agent" "f9d71c"
  "to:gemini-cli-pro" "Route to Gemini CLI Pro agent" "f9d71c"
  "to:antigravity-front" "Route to Antigravity frontend" "9e42f5"
  "to:gpt-teacher" "Route to GPT Teacher agent" "0366d6"
  "to:human" "Route to human operator" "ffffff"

  # Routing labels (from)
  "from:claude-code" "Source: Claude Code agent" "0366d6"
  "from:claude-cowork" "Source: Claude Cowork agent" "0366d6"
  "from:gemini-cli-flash" "Source: Gemini CLI Flash agent" "f9d71c"
  "from:gemini-cli-lite" "Source: Gemini CLI Lite agent" "f9d71c"
  "from:gemini-cli-pro" "Source: Gemini CLI Pro agent" "f9d71c"
  "from:antigravity-front" "Source: Antigravity frontend" "9e42f5"
  "from:gpt-teacher" "Source: GPT Teacher agent" "0366d6"
  "from:human" "Source: human operator" "ffffff"

  # Plane labels
  "plane:control" "GAMMA Control plane (GitHub coordination)" "34a853"
  "plane:execution" "GAMMA Execution plane (CLI/backend)" "fbbc04"
  "plane:truth" "GAMMA Truth plane (durable state)" "d32f2f"
  "plane:observation" "GAMMA Observation plane (user/public)" "1976d2"
  "plane:doctrine" "GAMMA Doctrine plane (policy/spec)" "7b1fa2"

  # Repo labels
  "repo:gamma" "GAMMA core coordination repo" "34a853"
  "repo:gamma-arena" "GAMMA Arena frontend repo" "34a853"
  "repo:gamma-protocol" "GAMMA Protocol specification repo" "34a853"
  "repo:gamma-science" "GAMMA Science research repo" "34a853"
  "repo:gamma-analysis" "GAMMA Analysis tooling repo" "34a853"
  "repo:jbiophysic" "Biophysics integration repo" "34a853"

  # Type labels
  "type:audit" "Audit or review task" "ffb300"
  "type:plan" "Planning or design task" "1976d2"
  "type:execute" "Execution/implementation task" "34a853"
  "type:validate" "Validation or testing task" "4caf50"
  "type:refactor" "Refactoring or optimization task" "2196f3"
  "type:docs" "Documentation or specification" "9c27b0"
  "type:bridge" "Bridge/coordination infrastructure" "673ab7"
  "type:release" "Release or deployment task" "f57c00"
  "type:incident" "Incident response or fix" "d32f2f"
  "type:ui" "User interface or UX task" "e91e63"

  # Status labels
  "status:intake" "Task in intake/triage phase" "cccccc"
  "status:ready" "Task ready to claim" "fbbc04"
  "status:claimed" "Task claimed by agent" "2196f3"
  "status:in-progress" "Task actively in progress" "ff9800"
  "status:blocked" "Task blocked by dependency" "d32f2f"
  "status:needs-review" "Task pending review" "ffb300"
  "status:done" "Task completed" "4caf50"

  # Risk labels
  "risk:low" "Low risk task" "4caf50"
  "risk:medium" "Medium risk task" "ffb300"
  "risk:high" "High risk task" "d32f2f"
  "risk:truth-bearing" "Task affects truth plane" "d32f2f"
  "risk:credential-sensitive" "Task handles credentials" "d32f2f"
  "risk:sandboxed" "Task in sandboxed environment" "9e42f5"

  # Evidence labels
  "evidence:none" "No evidence artifact" "cccccc"
  "evidence:diff" "Diff/code change artifact" "2196f3"
  "evidence:tests" "Test results artifact" "4caf50"
  "evidence:browser" "Browser screenshot artifact" "9c27b0"
  "evidence:receipt" "Execution receipt artifact" "1976d2"
  "evidence:command-transcript" "Command transcript artifact" "03a9f4"
  "evidence:pr" "Pull request artifact" "34a853"
)

FAILED=0
CREATED=0

# Create or update labels in groups of 3 (name, description, color)
for ((i = 0; i < ${#LABELS[@]}; i += 3)); do
  LABEL_NAME="${LABELS[i]}"
  LABEL_DESC="${LABELS[i+1]}"
  LABEL_COLOR="${LABELS[i+2]}"

  if gh label create "${LABEL_NAME}" \
    --description "${LABEL_DESC}" \
    --color "${LABEL_COLOR}" \
    --force \
    -R "${REPO}" 2> /dev/null; then
    CREATED=$((CREATED + 1))
  else
    echo "WARN: Failed to create/update label ${LABEL_NAME} in ${REPO}" >&2
    FAILED=$((FAILED + 1))
  fi
done

echo "Bootstrap complete: ${CREATED} labels created/updated, ${FAILED} failed"

if [ ${FAILED} -gt 0 ]; then
  exit 1
fi

exit 0
