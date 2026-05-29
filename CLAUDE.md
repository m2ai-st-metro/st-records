# CLAUDE.md - ST Records

## Quick Commands

```bash
source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/
```

## Project Purpose

ST Records is the contract store that holds the inter-layer data contracts for the feedback loop:
1. **Metroplex** - Idea pipeline (produces OutcomeRecords)
2. **Sky-Lynx** - Observer (analyzes outcomes, produces ImprovementRecommendations)
3. **Research Agents** - Signal fleet (produces ResearchSignals)

> **Retired 2026-05-28**: The persona-template upgrade flow (`PersonaUpgradePatch`, `scripts/persona_upgrader.py`, `scripts/review_patch.py`, the `api/` FastAPI visualization layer, and the Academy reader) was removed after a liveness audit found no live consumer. The dead code is cold-archived at `~/projects/skill-forge/archive/st-records-persona-templates-2026-05-28/`. The `persona_metrics.db` itself is untouched and remains load-bearing for outcomes / recommendations / research_signals. Live readers: `metroplex/readers/skylynx_reader.py`, `sky-lynx/research_reader.py`, `research-agents/signal_writer.py`.

## Architecture

```
contracts/              # Pydantic models defining inter-layer data contracts
  outcome_record.py     # Metroplex -> Sky-Lynx
  improvement_recommendation.py  # Sky-Lynx -> consumers
  research_signal.py    # Research Agents -> Sky-Lynx
  store.py              # Dual-write JSONL + SQLite store
schemas/                # JSON Schema exports for TypeScript consumers
data/                   # JSONL data files (append-only, git-tracked)
scripts/                # Orchestration and automation
tests/                  # Contract tests
```

## Key Decisions

- **JSONL as source of truth** - append-only, git-tracked, human-readable
- **SQLite as query layer** - rebuildable from JSONL at any time
- **Contracts defined here, imported by layers** - single source of truth for schemas
- **Weekly cadence** - matches Sky-Lynx's existing cron schedule

## Data Flow

```
Metroplex terminal state -> OutcomeRecord -> JSONL
Sky-Lynx reads JSONL -> analyzes -> ImprovementRecommendation -> JSONL
Research Agents -> ResearchSignal -> JSONL -> Sky-Lynx
```
