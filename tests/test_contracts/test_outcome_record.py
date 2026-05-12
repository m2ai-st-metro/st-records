"""Tests for OutcomeRecord contract."""

import json
from datetime import datetime, timedelta

import pytest

from contracts.outcome_record import OutcomeRecord, PipelineTrace, TerminalOutcome


class TestOutcomeRecord:
    """Schema validation and roundtrip tests."""

    def test_minimal_valid_record(self):
        record = OutcomeRecord(
            idea_id=1,
            idea_title="Test Idea",
            outcome=TerminalOutcome.PUBLISHED,
        )
        assert record.contract_version == "1.2.0"
        assert record.idea_id == 1
        assert record.outcome == TerminalOutcome.PUBLISHED
        assert record.artifact_count == 0
        assert record.tech_stack == []
        assert record.scene_fidelity_score is None
        assert record.scene_fidelity_breakdown is None

    def test_full_record(self):
        now = datetime.now()
        record = OutcomeRecord(
            idea_id=42,
            idea_title="CLI Markdown to EPUB",
            outcome=TerminalOutcome.PUBLISHED,
            overall_score=78.0,
            recommendation="develop",
            capabilities_fit="strong",
            build_outcome="success",
            artifact_count=12,
            tech_stack=["python", "fastapi"],
            pipeline_trace=[
                PipelineTrace(stage="captured", entered_at=now - timedelta(days=7), exited_at=now - timedelta(days=6)),
                PipelineTrace(stage="enriched", entered_at=now - timedelta(days=6), exited_at=now - timedelta(days=5)),
            ],
            total_duration_seconds=604800.0,
            tags=["cli", "tools"],
            github_url="https://github.com/user/repo",
            emitted_at=now,
        )
        assert record.artifact_count == 12
        assert len(record.pipeline_trace) == 2
        assert record.github_url == "https://github.com/user/repo"

    def test_roundtrip_serialization(self):
        record = OutcomeRecord(
            idea_id=1,
            idea_title="Test",
            outcome=TerminalOutcome.REJECTED,
            overall_score=30.0,
        )
        json_str = record.model_dump_json()
        restored = OutcomeRecord.model_validate_json(json_str)
        assert restored.idea_id == record.idea_id
        assert restored.outcome == record.outcome
        assert restored.overall_score == record.overall_score

    def test_all_terminal_outcomes(self):
        for outcome in TerminalOutcome:
            record = OutcomeRecord(
                idea_id=1,
                idea_title="Test",
                outcome=outcome,
            )
            assert record.outcome == outcome

    def test_chronological_trace_order_valid(self):
        now = datetime.now()
        OutcomeRecord(
            idea_id=1,
            idea_title="Test",
            outcome=TerminalOutcome.PUBLISHED,
            pipeline_trace=[
                PipelineTrace(stage="captured", entered_at=now - timedelta(hours=3)),
                PipelineTrace(stage="enriched", entered_at=now - timedelta(hours=2)),
                PipelineTrace(stage="published", entered_at=now - timedelta(hours=1)),
            ],
        )

    def test_chronological_trace_order_invalid(self):
        now = datetime.now()
        with pytest.raises(ValueError, match="not chronological"):
            OutcomeRecord(
                idea_id=1,
                idea_title="Test",
                outcome=TerminalOutcome.PUBLISHED,
                pipeline_trace=[
                    PipelineTrace(stage="enriched", entered_at=now - timedelta(hours=1)),
                    PipelineTrace(stage="captured", entered_at=now - timedelta(hours=3)),
                ],
            )

    def test_json_schema_has_contract_version(self):
        schema = OutcomeRecord.model_json_schema()
        props = schema["properties"]
        assert "contract_version" in props
        assert props["contract_version"]["default"] == "1.2.0"
