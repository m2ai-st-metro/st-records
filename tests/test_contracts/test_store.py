"""Tests for ContractStore."""

import tempfile
from pathlib import Path

import pytest

from contracts.improvement_recommendation import (
    ImprovementRecommendation,
    RecommendationType,
)
from contracts.outcome_record import OutcomeRecord, TerminalOutcome
from contracts.store import ContractStore


@pytest.fixture
def store(tmp_path):
    """Create a ContractStore with temp directory."""
    s = ContractStore(data_dir=tmp_path, db_path=tmp_path / "test.db")
    yield s
    s.close()


class TestContractStoreOutcomes:

    def test_write_and_read_outcome(self, store):
        record = OutcomeRecord(
            idea_id=1,
            idea_title="Test Idea",
            outcome=TerminalOutcome.PUBLISHED,
            overall_score=85.0,
        )
        store.write_outcome(record)

        outcomes = store.read_outcomes()
        assert len(outcomes) == 1
        assert outcomes[0].idea_id == 1
        assert outcomes[0].outcome == TerminalOutcome.PUBLISHED

    def test_query_outcomes_by_type(self, store):
        store.write_outcome(OutcomeRecord(
            idea_id=1, idea_title="A", outcome=TerminalOutcome.PUBLISHED,
        ))
        store.write_outcome(OutcomeRecord(
            idea_id=2, idea_title="B", outcome=TerminalOutcome.REJECTED,
        ))
        store.write_outcome(OutcomeRecord(
            idea_id=3, idea_title="C", outcome=TerminalOutcome.PUBLISHED,
        ))

        published = store.query_outcomes(outcome="published")
        assert len(published) == 2
        rejected = store.query_outcomes(outcome="rejected")
        assert len(rejected) == 1

    def test_jsonl_append_only(self, store):
        store.write_outcome(OutcomeRecord(
            idea_id=1, idea_title="A", outcome=TerminalOutcome.PUBLISHED,
        ))
        store.write_outcome(OutcomeRecord(
            idea_id=2, idea_title="B", outcome=TerminalOutcome.REJECTED,
        ))

        jsonl = (store.data_dir / "outcome_records.jsonl").read_text()
        lines = [l for l in jsonl.strip().splitlines() if l]
        assert len(lines) == 2


class TestContractStoreRecommendations:

    def test_write_and_read_recommendation(self, store):
        rec = ImprovementRecommendation(
            recommendation_id="rec-001",
            recommendation_type=RecommendationType.VOICE_ADJUSTMENT,
            title="Adjust voice",
            description="Test",
            suggested_change="Test change",
        )
        store.write_recommendation(rec)

        recs = store.read_recommendations()
        assert len(recs) == 1
        assert recs[0].recommendation_id == "rec-001"

    def test_query_by_target_system(self, store):
        store.write_recommendation(ImprovementRecommendation(
            recommendation_id="rec-001",
            recommendation_type=RecommendationType.VOICE_ADJUSTMENT,
            title="A", description="A", suggested_change="A",
            target_system="persona",
        ))
        store.write_recommendation(ImprovementRecommendation(
            recommendation_id="rec-002",
            recommendation_type=RecommendationType.CLAUDE_MD_UPDATE,
            title="B", description="B", suggested_change="B",
            target_system="claude_md",
        ))

        persona_recs = store.query_recommendations(target_system="persona")
        assert len(persona_recs) == 1
        assert persona_recs[0].recommendation_id == "rec-001"

    def test_update_recommendation_status(self, store):
        store.write_recommendation(ImprovementRecommendation(
            recommendation_id="rec-001",
            recommendation_type=RecommendationType.VOICE_ADJUSTMENT,
            title="A", description="A", suggested_change="A",
        ))
        store.update_recommendation_status("rec-001", "applied")

        recs = store.query_recommendations(status="applied")
        assert len(recs) == 1


class TestContractStoreRebuild:

    def test_rebuild_from_jsonl(self, store):
        store.write_outcome(OutcomeRecord(
            idea_id=1, idea_title="A", outcome=TerminalOutcome.PUBLISHED,
        ))
        store.write_recommendation(ImprovementRecommendation(
            recommendation_id="rec-001",
            recommendation_type=RecommendationType.VOICE_ADJUSTMENT,
            title="A", description="A", suggested_change="A",
        ))

        # Clear SQLite but keep JSONL
        conn = store._get_conn()
        conn.execute("DELETE FROM outcome_records")
        conn.execute("DELETE FROM improvement_recommendations")
        conn.commit()

        assert len(store.query_outcomes()) == 0

        store.rebuild_sqlite()

        # SQLite should be restored from JSONL
        assert len(store.query_outcomes()) >= 1
