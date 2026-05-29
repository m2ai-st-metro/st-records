# AGENTS.md - ST Records

## Build & Run

```bash
# Setup
cd ~/projects/st-records
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run loop status
python scripts/loop_status.py

# Run feedback loop (dry-run)
./scripts/run_loop.sh --dry-run

# Run feedback loop (live)
./scripts/run_loop.sh
```

> **Retired 2026-05-28**: The persona-template flow (`scripts/persona_upgrader.py`, `scripts/review_patch.py`, the `api/` FastAPI layer, Academy reader) was removed; cold-archived at `~/projects/skill-forge/archive/st-records-persona-templates-2026-05-28/`. The contract DB and the outcomes/recommendations/research_signals contracts are untouched.

## Key Paths

| Path | Purpose |
|------|---------|
| `contracts/` | Pydantic models for inter-layer contracts |
| `data/*.jsonl` | Append-only data files (source of truth) |
| `data/persona_metrics.db` | SQLite query layer (rebuildable) |
| `scripts/run_loop.sh` | Feedback loop orchestrator |
| `scripts/loop_status.py` | Reports loop health |
| `cron/st-records` | Cron configuration for weekly execution |

## Dependencies

- Python 3.11+
- Sky-Lynx (at `~/projects/sky-lynx/`)
- Metroplex (at `~/projects/metroplex/`)
- Research Agents (at `~/projects/research-agents/`)
