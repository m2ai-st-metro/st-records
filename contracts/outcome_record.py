"""OutcomeRecord contract: Ultra Magnus -> Sky-Lynx.

Emitted when an idea reaches a terminal state in the UM pipeline.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class TerminalOutcome(str, Enum):
    """Terminal states for an idea in the pipeline."""
    PUBLISHED = "published"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    BUILD_FAILED = "build_failed"
    FEATURE_BACKLOG = "feature_backlog"


class PipelineTrace(BaseModel):
    """Record of an idea passing through a pipeline stage."""
    stage: str
    entered_at: datetime
    exited_at: datetime | None = None
    persona_used: str | None = None


class OutcomeRecord(BaseModel):
    """Record emitted when an idea reaches a terminal state.

    Precondition: idea must be in a terminal state.
    Postcondition: record is append-only, written to JSONL + SQLite.
    Invariant: pipeline_trace is chronologically ordered; contract_version always present.
    """
    contract_version: str = "1.2.0"
    idea_id: int
    idea_title: str
    outcome: TerminalOutcome
    overall_score: float | None = None
    recommendation: str | None = None
    capabilities_fit: str | None = None
    build_outcome: str | None = None
    artifact_count: int = 0
    tech_stack: list[str] = Field(default_factory=list)
    pipeline_trace: list[PipelineTrace] = Field(default_factory=list)
    total_duration_seconds: float = 0.0
    tags: list[str] = Field(default_factory=list)
    github_url: str | None = None
    idea_type: str | None = None
    scene_fidelity_score: float | None = None
    scene_fidelity_breakdown: dict | None = None
    emitted_at: datetime = Field(default_factory=datetime.now)

    @model_validator(mode="after")
    def validate_trace_order(self) -> "OutcomeRecord":
        """Ensure pipeline_trace is chronologically ordered."""
        for i in range(1, len(self.pipeline_trace)):
            prev = self.pipeline_trace[i - 1]
            curr = self.pipeline_trace[i]
            if curr.entered_at < prev.entered_at:
                raise ValueError(
                    f"pipeline_trace not chronological: "
                    f"{prev.stage} ({prev.entered_at}) -> {curr.stage} ({curr.entered_at})"
                )
        return self
