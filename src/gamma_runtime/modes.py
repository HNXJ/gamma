from enum import Enum, auto
from dataclasses import dataclass
from typing import Set

class RuntimeMode(Enum):
    NOHEARTBEAT_SLICE = auto()      # Bounded run, no heartbeat allowed.
    IDLE_SUPERVISED = auto()        # Wait for input, no aggressive heartbeat.
    HEARTBEAT_SUPERVISED = auto()    # Aggressive heartbeat loop enabled.
    TRUTH_CANDIDATE_RUN = auto()    # Full run with intent to commit truth receipts.
    ANALYSIS_ONLY = auto()          # No model calls, data analysis only.
    OBSERVATION_ONLY = auto()       # Read-only UI/Telemetry mode.

@dataclass(frozen=True)
class ModeContract:
    mode: RuntimeMode
    allow_heartbeat: bool
    allow_scientific_turns: bool
    allow_truth_mutation: bool
    require_receipts: bool
    max_rounds: int | None = None

MODE_CONTRACTS = {
    RuntimeMode.NOHEARTBEAT_SLICE: ModeContract(
        mode=RuntimeMode.NOHEARTBEAT_SLICE,
        allow_heartbeat=False,
        allow_scientific_turns=True,
        allow_truth_mutation=False,
        require_receipts=False,
        max_rounds=10
    ),
    RuntimeMode.IDLE_SUPERVISED: ModeContract(
        mode=RuntimeMode.IDLE_SUPERVISED,
        allow_heartbeat=False,
        allow_scientific_turns=True,
        allow_truth_mutation=False,
        require_receipts=False
    ),
    RuntimeMode.HEARTBEAT_SUPERVISED: ModeContract(
        mode=RuntimeMode.HEARTBEAT_SUPERVISED,
        allow_heartbeat=True,
        allow_scientific_turns=True,
        allow_truth_mutation=False,
        require_receipts=False
    ),
    RuntimeMode.TRUTH_CANDIDATE_RUN: ModeContract(
        mode=RuntimeMode.TRUTH_CANDIDATE_RUN,
        allow_heartbeat=True,
        allow_scientific_turns=True,
        allow_truth_mutation=True,
        require_receipts=True
    ),
    RuntimeMode.ANALYSIS_ONLY: ModeContract(
        mode=RuntimeMode.ANALYSIS_ONLY,
        allow_heartbeat=False,
        allow_scientific_turns=False,
        allow_truth_mutation=False,
        require_receipts=False
    ),
    RuntimeMode.OBSERVATION_ONLY: ModeContract(
        mode=RuntimeMode.OBSERVATION_ONLY,
        allow_heartbeat=False,
        allow_scientific_turns=False,
        allow_truth_mutation=False,
        require_receipts=False
    ),
}
