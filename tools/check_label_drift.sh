#!/bin/bash
# tools/check_label_drift.sh
#
# GAMMA-BUS v0 Label Drift Check Tool
# Compares required label set against actual labels in repo
# Usage: ./check_label_drift.sh HNXJ/gamma
#
# Non-destructive (read-only)
# Exits 0 if no drift, nonzero if labels missing

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

echo "Checking label drift for: ${REPO}"

# Define all v0 required labels (names only)
declare -a REQUIRED_LABELS=(
  # Agent labels
  "agent:claude-code"
  "agent:claude-cowork"
  "agent:gemini-cli-flash"
  "agent:gemini-cli-lite"
  "agent:gemini-cli-pro"
  "agent:antigravity-front"
  "agent:gpt-teacher"
  "agent:human"

  # Routing labels (to)
  "to:claude-code"
  "to:claude-cowork"
  "to:gemini-cli-flash"
  "to:gemini-cli-lite"
  "to:gemini-cli-pro"
  "to:antigravity-front"
  "to:gpt-teacher"
  "to:human"

  # Routing labels (from)
  "from:claude-code"
  "from:claude-cowork"
  "from:gemini-cli-flash"
  "from:gemini-cli-lite"
  "from:gemini-cli-pro"
  "from:antigravity-front"
  "from:gpt-teacher"
  "from:human"

  # Plane labels
  "plane:control"
  "plane:execution"
  "plane:truth"
  "plane:observation"
  "plane:doctrine"

  # Repo labels
  "repo:gamma"
  "repo:gamma-arena"
  "repo:gamma-protocol"
  "repo:gamma-science"
  "repo:gamma-analysis"
  "repo:jbiophysic"

  # Type labels
  "type:audit"
  "type:plan"
  "type:execute"
  "type:validate"
  "type:refactor"
  "type:docs"
  "type:bridge"
  "type:release"
  "type:incident"
  "type:ui"

  # Status labels
  "status:intake"
  "status:ready"
  "status:claimed"
  "status:in-progress"
  "status:blocked"
  "status:needs-review"
  "status:done"

  # Risk labels
  "risk:low"
  "risk:medium"
  "risk:high"
  "risk:truth-bearing"
  "risk:credential-sensitive"
  "risk:sandboxed"

  # Evidence labels
  "evidence:none"
  "evidence:diff"
  "evidence:tests"
  "evidence:browser"
  "evidence:receipt"
  "evidence:command-transcript"
  "evidence:pr"
)

# Get actual labels from repo
ACTUAL_LABELS=$(gh label list -R "${REPO}" --json name --jq '.[].name' 2>/dev/null)

if [ $? -ne 0 ]; then
  echo "ERROR: Failed to fetch labels from ${REPO}" >&2
  exit 1
fi

# Check for missing labels
MISSING=()
for REQUIRED_LABEL in "${REQUIRED_LABELS[@]}"; do
  if ! echo "${ACTUAL_LABELS}" | grep -q "^${REQUIRED_LABEL}$"; then
    MISSING+=("${REQUIRED_LABEL}")
  fi
done

# Report results
if [ ${#MISSING[@]} -eq 0 ]; then
  echo "✓ No label drift detected (${#REQUIRED_LABELS[@]} labels present)"
  exit 0
else
  echo "✗ Label drift detected: ${#MISSING[@]} missing labels"
  echo ""
  echo "Missing labels:"
  for MISSING_LABEL in "${MISSING[@]}"; do
    echo "  - ${MISSING_LABEL}"
  done
  exit 1
fi
