## Snow-Town Project Review

> **Retired 2026-05-28 — persona-template subsystem removed.** This review describes the
> original three-layer design including the **Agent Persona Academy**, `PersonaUpgradePatch`
> flow, `persona_upgrader`, and the FastAPI **read-only API layer** + 3D dashboard. Those were
> retired after a liveness audit found no live consumer. What remains live is the **contract
> store** for `OutcomeRecord`, `ImprovementRecommendation`, and `ResearchSignal` (Metroplex →
> Sky-Lynx, Research Agents → Sky-Lynx). Treat any Academy / persona-patch / FastAPI / dashboard
> mention below as historical. Dead code cold-archived at
> `~/projects/skill-forge/archive/st-records-persona-templates-2026-05-28/`.

### What It Is

Snow-Town is a **closed-loop learning ecosystem** — an orchestration layer that wires three independent projects into a self-improving feedback triangle:

```
Ultra Magnus ──OutcomeRecord──> Sky-Lynx
     ^                              │
     │                    ImprovementRecommendation
PersonaUpgradePatch                 │
     │                              v
     └──────────── Agent Persona Academy
```

The core insight: **AI agent personas can improve themselves** through structured feedback derived from their own performance data.

---

### The Three Layers

**1. Ultra Magnus (UM) — "The Factory"**
- An idea pipeline that takes raw ideas through stages: capture → enrichment → evaluation → review → scaffold → build → publish
- When ideas reach terminal states (published/rejected/deferred/build_failed), UM emits `OutcomeRecord` objects into Snow-Town's JSONL store
- Idea #5 (WHEELJACK) was published with score 78; Idea #6 (Dyson Sphere) was deferred with score 35 — real data already flowing

**2. Sky-Lynx (SL) — "The Analyst"**
- An observer that reads outcome records + weekly usage data
- Runs Claude analysis to find patterns and produce typed `ImprovementRecommendation` objects
- Each recommendation is classified by `target_system` (persona / claude_md / pipeline), `target_persona` (specific persona ID), and `recommendation_type` (voice_adjustment, framework_addition, etc.)
- Currently 5 real recommendations exist — covering session tracking, offline workflows, success pattern reinforcement, and quality score analysis

**3. Agent Persona Academy (AP) — "The Academy"**
- A factory that maintains AI persona definitions as structured YAML files (8 personas currently)
- Consumes persona-targeted recommendations, uses Claude API to generate `PersonaUpgradePatch` objects (JSON Pointer-based YAML diffs)
- Patches default to "proposed" status requiring human review; `--auto-apply` available for validated patches
- 1 real patch exists: adding a "user adoption journey" framework to the Sky-Lynx persona itself

---

### Architecture Highlights

**Data contracts** — Three Pydantic models define strict inter-layer boundaries:

| Contract | Direction | Fields of Note |
|----------|-----------|----------------|
| `OutcomeRecord` | UM → SL | idea_id, outcome (terminal state), pipeline_trace (chronologically validated), tech_stack, overall_score |
| `ImprovementRecommendation` | SL → AP | recommendation_type (10 enum values), target_system, evidence (with signal_strength 0-1), scope (specific vs all personas) |
| `PersonaUpgradePatch` | AP → UM | patches (JSON Pointer operations: add/replace/remove), schema_valid flag, proposed/applied/rejected status |

**Dual-write storage** — JSONL files are the source of truth (append-only, git-tracked, human-readable). SQLite serves as a rebuildable query layer. The `ContractStore` class writes to both atomically.

**Weekly cadence** — `run_loop.sh` orchestrates: Sky-Lynx analyzer → persona upgrader → loop status reporter. Cron configured for Sundays at 2 AM.

**Read-only API layer** — FastAPI serves the dashboard, aggregating data from ContractStore, Academy YAML files, and UM's SQLite. Never writes to any data source.

**3D Dashboard** — Next.js 14 + React Three Fiber dashboard with:
- 3D ecosystem view: three Platonic solids (icosahedron/octahedron/dodecahedron) representing UM/SL/Academy, arranged in a triangle with bezier flow edges
- Growth tier system: nodes scale from wireframe "Seed" (0 records) to glowing "Complex" (200+ records)
- Edge state visualization: dormant → active → busy → saturated based on recent record counts
- Agent gallery: browsable persona cards with identity, voice, frameworks, case studies
- Pipeline funnel: stage-by-stage visualization of ideas flowing through UM
- WebXR/VR mode: placeholder scaffolded for Quest 3 (Phase 7h, not yet implemented)

---

### Current State (Production Data)

- **3 outcome records** (2 published WHEELJACK, 1 deferred Dyson Sphere)
- **5 improvement recommendations** (4 real + 1 dry-run test)
- **1 persona patch** (adding user_adoption_journey framework to sky-lynx persona, schema validated, status: proposed)
- **52+ tests passing** across contract tests (33) and API tests (19)

---

### Key Design Decisions

1. **JSONL over database** — Human-readable, git-diffable, append-only. SQLite is secondary, rebuildable
2. **Contracts centralized in snow-town** — Single source of truth imported via `sys.path` (all on same EC2)
3. **Human-in-the-loop by default** — Patches are "proposed" until reviewed. Auto-apply is opt-in
4. **R3F over Unity for viz** — Web-native, single codebase for browser + VR, same React skills
5. **SWR over TanStack Query** — Simpler API, 30s auto-refresh, sufficient for the dashboard's needs

---

### Article Planning Notes

For your 4-article series:

**Article 1: "Snow-Town: Building a Self-Improving AI Agent Ecosystem"**
- The big idea: closing the loop so AI agents can learn from their own outputs
- The triangle architecture and why each layer exists
- The real data: first WHEELJACK outcome → Sky-Lynx recommendation → Sky-Lynx self-upgrading its own persona
- Brief layer overviews

**Article 2: "Ultra Magnus — The Idea Pipeline" (UM Deep-Dive)**
- The full pipeline: capture → enrichment → evaluation → review → scaffold → build → publish
- OutcomeRecord emission hooks (auto-emit on terminal states)
- 14 MCP tools, Claude-as-orchestrator architecture
- The interesting tension: scored ideas (78 vs 35) creating signal for the feedback loop

**Article 3: "Sky-Lynx — The AI Observer" (SL Deep-Dive)**
- Observer pattern: reading outcome data + usage patterns
- Claude analysis producing typed, classified recommendations
- The recommendation taxonomy (10 types, 3 target systems)
- Evidence-based signal strength scoring
- The meta-learning angle: Sky-Lynx analyzing its own recommendations' effectiveness

**Article 4: "Agent Persona Academy — The Persona Factory" (AP Deep-Dive)**
- Personas as structured YAML (identity, voice, frameworks, case studies)
- Claude API generating JSON Pointer patches from recommendations
- Schema validation via Academy CLI
- The human-in-the-loop design and why auto-apply is opt-in
- The 3D dashboard: visualizing the ecosystem as a living organism
- The vision: WebXR inspection on Quest 3

The most compelling narrative thread: **the system already upgraded itself** — Sky-Lynx recommended adding an adoption analysis framework to its own persona, the upgrader generated a validated patch, and it's sitting in "proposed" status awaiting human review. That's the feedback loop working end-to-end.
