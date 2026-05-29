# ST Records Data Contract

Stable interface for all systems that read from or write to ST Records' data stores. ST Records uses a dual-write architecture: **JSONL files are source of truth** (append-only, git-tracked), **SQLite is the query layer** (status updates, indexed queries, rebuildable).

## Database: `data/persona_metrics.db`

SQLite 3 database. External consumers **must** open in read-only mode:

```python
import sqlite3
conn = sqlite3.connect("file:/path/to/persona_metrics.db?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
```

## Tables

### `outcome_records`

Terminal pipeline outcomes from Ultra-Magnus builds.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal row ID |
| `idea_id` | INTEGER | NOT NULL | IdeaForge idea ID |
| `idea_title` | TEXT | NOT NULL | Idea title |
| `outcome` | TEXT | NOT NULL | `published`, `rejected`, `deferred`, `build_failed`, `feature_backlog` |
| `overall_score` | REAL | nullable | IdeaForge weighted score |
| `recommendation` | TEXT | nullable | Build recommendation text |
| `capabilities_fit` | TEXT | nullable | Capabilities assessment |
| `build_outcome` | TEXT | nullable | Build result description |
| `artifact_count` | INTEGER | DEFAULT 0 | Number of artifacts produced |
| `tech_stack` | TEXT | JSON array | Technologies used in build |
| `total_duration_seconds` | REAL | DEFAULT 0 | Pipeline wall-clock time |
| `tags` | TEXT | JSON array | Categorization tags |
| `github_url` | TEXT | nullable | Published repo URL |
| `emitted_at` | TEXT | NOT NULL | ISO-8601 emission timestamp |
| `raw_json` | TEXT | NOT NULL | Full contract serialized as JSON |

### `improvement_recommendations`

Sky-Lynx generated recommendations for system improvement.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal row ID |
| `recommendation_id` | TEXT | NOT NULL UNIQUE | Unique identifier |
| `session_id` | TEXT | nullable | Analysis session ID (dedup key) |
| `recommendation_type` | TEXT | NOT NULL | See types below |
| `target_system` | TEXT | DEFAULT 'persona' | `persona`, `claude_md`, `pipeline` |
| `title` | TEXT | NOT NULL | Recommendation title |
| `priority` | TEXT | DEFAULT 'medium' | `high`, `medium`, `low` |
| `scope` | TEXT | | `specific_persona`, `all_personas`, `all_in_department` |
| `target_department` | TEXT | nullable | Required when scope = `all_in_department` |
| `status` | TEXT | DEFAULT 'pending' | `pending`, `dispatched`, `applied`, `rejected` |
| `emitted_at` | TEXT | NOT NULL | ISO-8601 timestamp |
| `raw_json` | TEXT | NOT NULL | Full contract as JSON |
| `effectiveness` | TEXT | nullable | `effective`, `neutral`, `harmful` (post-hoc) |
| `effectiveness_score` | REAL | nullable | -1.0 to 1.0 (post-hoc) |
| `effectiveness_evaluated_at` | TEXT | nullable | ISO-8601 timestamp |

**Recommendation types:** `voice_adjustment`, `framework_addition`, `framework_refinement`, `validation_marker_change`, `case_study_addition`, `constraint_addition`, `constraint_removal`, `claude_md_update`, `pipeline_change`, `tier_promotion`, `tier_demotion`, `other`

### `persona_patches` (DEAD — retired 2026-05-28)

> The persona-template upgrade flow was retired. The table physically remains in `persona_metrics.db` (untouched) but the `ContractStore` no longer reads or writes it, and no live consumer depends on it. Dead code cold-archived at `~/projects/skill-forge/archive/st-records-persona-templates-2026-05-28/`. Do not build new consumers against this table.

### `research_signals`

Market research signals from the research agent fleet.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal row ID |
| `signal_id` | TEXT | NOT NULL UNIQUE | Unique identifier |
| `source` | TEXT | NOT NULL | See sources below |
| `title` | TEXT | NOT NULL | Signal title |
| `summary` | TEXT | NOT NULL | Signal summary |
| `url` | TEXT | nullable | Source URL |
| `relevance` | TEXT | NOT NULL | `high`, `medium`, `low` |
| `relevance_rationale` | TEXT | DEFAULT '' | Why this relevance level |
| `tags` | TEXT | JSON array | Categorization tags |
| `domain` | TEXT | nullable | Technology domain |
| `consumed_by` | TEXT | nullable | Downstream consumer name |
| `emitted_at` | TEXT | NOT NULL | ISO-8601 timestamp |
| `raw_json` | TEXT | NOT NULL | Full contract as JSON |

**Signal sources:** `arxiv_hf`, `tool_monitor`, `domain_watch`, `idea_machine`, `youtube_scanner`, `rss_scanner`, `manual`, `trend_analyzer`, `perplexity`, `chatgpt`, `gemini_research`

## JSONL Files (Source of Truth)

All in `data/`. Append-only, git-tracked, one JSON record per line.

| File | Contract | Access Methods |
|------|----------|---------------|
| `outcome_records.jsonl` | OutcomeRecord | `store.write_outcome()`, `store.read_outcomes()` |
| `improvement_recommendations.jsonl` | ImprovementRecommendation | `store.write_recommendation()`, `store.read_recommendations()` |
| `research_signals.jsonl` | ResearchSignal | `store.write_signal()`, `store.read_signals()` |

> `persona_patches.jsonl` is retained on disk (historical) but the store no longer reads/writes it — the persona-template flow was retired 2026-05-28.

## Dual-Write Architecture

- **`write_*()`** — appends to JSONL + inserts to SQLite
- **`read_*()`** — reads from JSONL (immutable historical view)
- **`query_*()`** — reads from SQLite (current state with status overlays)
- **`update_*_status()`** — SQLite only (mutable state)
- **`rebuild_sqlite()`** — drops + recreates all SQLite tables from JSONL

**Rule:** Status-aware queries use `query_*()` (SQLite). Historical/immutable queries use `read_*()` (JSONL).

## Status Lifecycles

### ImprovementRecommendation
```
pending → dispatched → applied
                    → rejected
```

### OutcomeRecord
No mutable status — `outcome` is terminal: `published`, `rejected`, `deferred`, `build_failed`, `feature_backlog`.

### ResearchSignal
No mutable status — `consumed_by` tracks downstream consumption.

## Reader Contracts

### Metroplex (`readers/skylynx_reader.py`)

**Reads:** `improvement_recommendations` / `outcome_records` from `persona_metrics.db` (opens with `?mode=ro`).

### Sky-Lynx (`src/sky_lynx/`)

**Reads:** `outcome_records.jsonl` via `outcome_reader.py`, `research_signals.jsonl` via `research_reader.py`.

**Purpose:** Weekly analysis loop (Sunday 2 AM) identifies patterns, generates ImprovementRecommendations.

### ClaudeClaw

**Reads:** `persona_metrics.db` for reporting (research signal age, metrics).

## Writer Contracts

### Metroplex (`outcome_emitter.py`)

**Writes:** `OutcomeRecord` contracts when an idea reaches terminal pipeline state. Uses `store.write_outcome()` (dual-write to JSONL + SQLite). Includes full IdeaForge scores in `raw_json`.

### Sky-Lynx (`src/sky_lynx/report_writer.py`)

**Writes:** `ImprovementRecommendation` contracts after weekly analysis. Uses `store.write_recommendation()`. Deduplication via `session_id`.

### Research Agents (`src/research_agents/signal_writer.py`)

**Writes:** `ResearchSignal` contracts from daily cron agents (one per LLM). Uses `store.write_signal()`.

> **Retired 2026-05-28:** the `persona_upgrader` writer and FastAPI dashboard reader were removed (no live consumer). Cold-archived at `~/projects/skill-forge/archive/st-records-persona-templates-2026-05-28/`.

## Importing Contracts

ST Records contracts are imported via `sys.path` injection, not pip:

```python
import sys
sys.path.insert(0, os.path.expanduser("~/projects/st-records"))
from contracts.outcome_record import OutcomeRecord
from contracts.store import ContractStore
```

## Environment Variables

- `ST_RECORDS_DATA_DIR` (default: `~/projects/st-records/data`) — JSONL + SQLite directory
- `ST_RECORDS_DB_PATH` (default: `~/projects/st-records/data/persona_metrics.db`)

## Stability Guarantees

- Column names and types are stable. New columns may be added; existing columns will not be renamed or removed.
- JSONL files are append-only. Records are never modified or deleted.
- SQLite is rebuildable from JSONL at any time via `store.rebuild_sqlite()`.
- Contract versions follow semver. Breaking changes increment the major version.
- Always use `?mode=ro` for read-only consumers.
- Status values are stable. New values may be added to enums.
