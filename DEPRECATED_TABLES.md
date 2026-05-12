# Deprecated Tables

Tables that once participated in the contract layer and are now orphan in
existing databases. The code that wrote/read them has been removed; the
data is preserved for historical record. New databases initialized by
`ContractStore._ensure_tables` will NOT recreate these tables.

## `agent_patches`

- **Deprecated**: 2026-05-12 (CLEANUP-A Scope 2c)
- **Schema**: see git history of `contracts/store.py:133` for the original
  `CREATE TABLE` block.
- **Companion JSONL**: `data/agent_patches.jsonl` (if it existed) is left
  in place. The Metroplex Gate 3 (PatchGate), `scripts/agent_upgrader.py`,
  `scripts/review_agent_patch.py`, and `contracts/agent_upgrade_patch.py`
  modules were the consumers — all removed in the same cleanup.
- **Rows in existing `persona_metrics.db`**: do not drop. The orphan
  table is harmless. A future rebuild via `ContractStore.rebuild_sqlite`
  no longer recreates it; the historical rows persist only until someone
  drops the table explicitly.
- **Successor**: agent-promotion is being re-implemented as the R-B
  `agent-promote` script + ClaudeClaw skill-registry extension (deferred
  to Pass 6 of the pivot sequence).
