# ST Records (Snow-Town)

Contract store for the ST Metro pipeline. The shared, dual-write (JSONL + SQLite) store of inter-layer data contracts: pipeline outcomes drive analysis, analysis produces improvement recommendations, and research signals feed the analysis loop.

> **Note**: The persona-template upgrade flow (`PersonaUpgradePatch` / persona_upgrader / Academy / the FastAPI visualization API) was retired 2026-05-28 after a liveness audit found no live consumer. The dead code is cold-archived at `~/projects/skill-forge/archive/st-records-persona-templates-2026-05-28/`. This repo now exists purely as the contract store for outcomes, recommendations, and research signals.

## Architecture

```
Metroplex (idea pipeline)
    |
    +-- OutcomeRecord --> ST Records ContractStore (JSONL + SQLite)
                               |
                               v
                         Sky-Lynx (weekly analysis)
                               |
                               +-- ImprovementRecommendation --> ContractStore

Research Agents
    |
    +-- ResearchSignal --> ContractStore --> Sky-Lynx
```

**Live external readers** (all read the contract store directly, not via any API):
- **Metroplex** — `readers/skylynx_reader.py`
- **Sky-Lynx** — `research_reader.py` (reads JSONL + SQLite for weekly analysis)
- **Research Agents** — `signal_writer.py` (writes `ResearchSignal` records)

## Data Model

### Contracts (Pydantic v2)

| Contract | From | To | File |
|----------|------|----|------|
| `OutcomeRecord` | Metroplex | Sky-Lynx | `contracts/outcome_record.py` |
| `ImprovementRecommendation` | Sky-Lynx | consumers | `contracts/improvement_recommendation.py` |
| `ResearchSignal` | Research Agents | Sky-Lynx | `contracts/research_signal.py` |

### Storage: Dual-Write (JSONL + SQLite)

- **JSONL** (`data/*.jsonl`) — append-only, git-tracked, source of truth
- **SQLite** (`data/persona_metrics.db`) — query layer with status tracking, rebuildable from JSONL via `ContractStore.rebuild_sqlite()`

The `ContractStore` (`contracts/store.py`) handles both writes atomically. Status updates (e.g. recommendation pending -> applied) are written to SQLite only; JSONL preserves the original record.

### SQLite Tables

| Table | Key Columns | Status Values |
|-------|------------|---------------|
| `outcome_records` | idea_id, outcome, overall_score, emitted_at | - |
| `improvement_recommendations` | recommendation_id, recommendation_type, target_system, priority | pending, applied, rejected |
| `research_signals` | signal_id, source, relevance, domain, consumed_by | - |

> The legacy `persona_patches` table remains in `persona_metrics.db` (untouched), but the store no longer reads or writes it — it is dead.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"        # Contracts + scripts + tests
```

## Usage

### Scripts

```bash
source .venv/bin/activate

# Feedback loop (Sky-Lynx analysis -> status report)
./scripts/run_loop.sh                     # Live run
./scripts/run_loop.sh --dry-run           # No API calls

# Status report
python scripts/loop_status.py             # Report loop health and counts
```

## Cron / Automation

Weekly feedback loop (Sundays 2 AM) via `/etc/cron.d/st-records`:

```
0 2 * * 0 apexaipc /home/apexaipc/projects/st-records/scripts/run_loop.sh >> /var/log/st-records/loop.log 2>&1
```

Logrotate configured at `cron/logrotate-st-records`. The loop runs Sky-Lynx analysis and reports loop status.

## Project Structure

```
st-records/
├── contracts/                      # Pydantic v2 data contracts
│   ├── outcome_record.py           # Metroplex -> Sky-Lynx
│   ├── improvement_recommendation.py  # Sky-Lynx -> consumers
│   ├── research_signal.py          # Research Agents -> Sky-Lynx
│   └── store.py                    # Dual-write JSONL + SQLite store
├── schemas/                        # JSON Schema exports (v1)
├── dashboard/                      # Next.js dashboard (legacy; no live backend after API retirement)
├── scripts/
│   ├── run_loop.sh                 # Feedback loop orchestrator
│   └── loop_status.py              # Loop health reporter
├── cron/                           # Cron + logrotate configs
├── data/                           # JSONL (git-tracked) + SQLite (git-ignored)
│   ├── outcome_records.jsonl
│   ├── improvement_recommendations.jsonl
│   ├── research_signals.jsonl
│   └── persona_metrics.db          # SQLite query layer
├── tests/
│   └── test_contracts/             # Contract + store tests
├── pyproject.toml                  # Package config (st-records 0.1.0)
├── BLUEPRINT.md                    # Phase tracker
├── CLAUDE.md                       # Claude Code instructions
└── decisions.log                   # Historical decisions log
```

## Testing

```bash
source .venv/bin/activate
pytest tests/                              # All tests
pytest tests/test_contracts/ -v            # Contract + store tests
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| JSONL as source of truth | Append-only, git-tracked, human-readable, survives SQLite corruption |
| SQLite as query layer | Rebuildable from JSONL; status updates written here only |
| Contracts defined here, imported by layers | Single source of truth for inter-system schemas |
| Weekly cadence | Matches Sky-Lynx's existing cron schedule |

## Related Projects

| Project | Relationship |
|---------|-------------|
| **Metroplex** | Writes `OutcomeRecord` on terminal pipeline states; reads via `readers/skylynx_reader.py` |
| **Sky-Lynx** | Writes `ImprovementRecommendation` records; reads outcomes + signals (`research_reader.py`) |
| **Research Agents** | Write `ResearchSignal` records (`signal_writer.py`) |

## License

Proprietary - ST Metro Ecosystem
