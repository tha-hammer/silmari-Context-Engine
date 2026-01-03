---
date: 2026-01-02T19:18:11-05:00
researcher: Claude
git_commit: ff5064e55e936a91617896a4fa68e67f7222126c
branch: main
repository: silmari-Context-Engine
topic: "Orchestrator Usage on Brownfield Projects with Planning Pipeline"
tags: [research, orchestrator, brownfield, pipeline, planning, beads]
status: complete
last_updated: 2026-01-02
last_updated_by: Claude
---

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│          ORCHESTRATOR BROWNFIELD PIPELINE INTEGRATION                   │
│                                                                         │
│                    Research Document                                    │
│                    Status: Complete                                     │
│                    Date: 2026-01-02                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

# Research: Orchestrator Usage on Brownfield Projects

**Date**: 2026-01-02T19:18:11-05:00
**Researcher**: Claude
**Git Commit**: ff5064e55e936a91617896a4fa68e67f7222126c
**Branch**: main
**Repository**: silmari-Context-Engine

## Research Question

How to use the orchestrator.py file on a brownfield project? The current orchestrator start-up contains `new` and `continue` but needs a way to pipeline into the research → requirement decomp → plan → plan decomp → execute plan pipeline.

## 📊 Summary

The codebase contains **three orchestrator files** serving different purposes:

| File | Purpose | Workflow |
|------|---------|----------|
| `orchestrator.py` | Greenfield project builder | `new` / `continue` with feature_list.json |
| `planning_orchestrator.py` | Planning pipeline CLI | Research → Plan → Decompose → Beads |
| `planning_pipeline/integrated_orchestrator.py` | State management via beads | Wraps BeadsController for issue tracking |

**For brownfield projects**, use `planning_orchestrator.py` which implements the full pipeline:

```
Research → Memory Sync → Requirement Decomposition → Planning → Phase Decomposition → Beads Integration
```

The root `orchestrator.py` is designed for **greenfield projects only** (creating new projects from scratch). It does NOT integrate with the planning pipeline.

---

## 🎯 Detailed Findings

### 1. Root orchestrator.py (Greenfield Only)

**Location**: `/home/maceo/Dev/silmari-Context-Engine/orchestrator.py`
**Lines**: 1-1366

This orchestrator is for building **new projects from scratch**:

```python
# orchestrator.py:1279-1295 - CLI modes
def main():
    # ...
    # Interactive mode - show menu
    print("What would you like to do?")
    print("  1. Start a new project")
    print("  2. Continue an existing project")
```

**Key characteristics**:
- Uses `feature_list.json` for state tracking (lines 421-444)
- Implements `build_init_prompt()` for project scaffolding (lines 508-559)
- Uses `build_implement_prompt()` for feature implementation (lines 786-874)
- Runs Claude Code interactively with `run_claude_code_interactive()` (lines 962-1093)

**NOT suitable for brownfield because**:
- Requires `feature_list.json` to exist (created during `new` project init)
- No integration with planning pipeline steps
- No research or plan decomposition phases
- Expects `.agent/` directory with workflows from harness setup

---

### 2. planning_orchestrator.py (Brownfield Pipeline Entry Point)

**Location**: `/home/maceo/Dev/silmari-Context-Engine/planning_orchestrator.py`
**Lines**: 1-567

This is the **correct entry point for brownfield projects**:

```python
# planning_orchestrator.py:133-160 - Main pipeline run
def run_pipeline(
    project_path: Path,
    prompt: str,
    ticket_id: str = None,
    auto_approve: bool = False
) -> dict:
    """Run the planning pipeline."""
    from planning_pipeline import PlanningPipeline
    pipeline = PlanningPipeline(project_path)
    return pipeline.run(
        research_prompt=prompt,
        ticket_id=ticket_id,
        auto_approve=auto_approve
    )
```

**Usage**:
```bash
# Interactive mode
python planning_orchestrator.py

# With project path
python planning_orchestrator.py --project ~/existing-project

# With ticket tracking
python planning_orchestrator.py --ticket ENG-1234

# Auto-approve (skip interactive checkpoints)
python planning_orchestrator.py --auto-approve

# Resume from checkpoint
python planning_orchestrator.py --resume
```

---

### 3. The 6-Step Planning Pipeline

**Location**: `/home/maceo/Dev/silmari-Context-Engine/planning_pipeline/pipeline.py`
**Lines**: 13-281

The `PlanningPipeline` class orchestrates 6 steps:

```
╔═══════════════════════════════════════════════════════════════════════╗
║                     PLANNING PIPELINE FLOW                            ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  STEP 1: RESEARCH                                                     ║
║  ├─ Input: research_prompt (string)                                   ║
║  ├─ Output: research_path, open_questions                             ║
║  └─ Interactive: revise/restart/continue options                      ║
║                          │                                            ║
║                          ▼                                            ║
║  MEMORY SYNC (between steps)                                          ║
║  ├─ Records episodic memory                                           ║
║  ├─ Compiles working context                                          ║
║  └─ Clears Claude context for next phase                              ║
║                          │                                            ║
║                          ▼                                            ║
║  STEP 2: REQUIREMENT DECOMPOSITION                                    ║
║  ├─ Input: research_path                                              ║
║  ├─ Output: hierarchy_path, diagram_path, tests_path                  ║
║  └─ Interactive: retry/skip options                                   ║
║                          │                                            ║
║                          ▼                                            ║
║  STEP 3: PLANNING                                                     ║
║  ├─ Input: research_path, additional_context                          ║
║  ├─ Output: plan_path                                                 ║
║  └─ Interactive: feedback loop until approved                         ║
║                          │                                            ║
║                          ▼                                            ║
║  STEP 4: PHASE DECOMPOSITION                                          ║
║  ├─ Input: plan_path                                                  ║
║  └─ Output: phase_files[] (list of markdown files)                    ║
║                          │                                            ║
║                          ▼                                            ║
║  STEP 5: BEADS INTEGRATION                                            ║
║  ├─ Input: phase_files[], epic_title                                  ║
║  └─ Output: epic_id, phase_issues[]                                   ║
║                          │                                            ║
║                          ▼                                            ║
║  STEP 6: MEMORY CAPTURE (placeholder)                                 ║
║  └─ Uses existing hooks                                               ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 4. IntegratedOrchestrator (Beads State Management)

**Location**: `/home/maceo/Dev/silmari-Context-Engine/planning_pipeline/integrated_orchestrator.py`
**Lines**: 1-291

This class provides **state management via beads** (not direct orchestration):

```python
class IntegratedOrchestrator:
    """Orchestrator using planning_pipeline and beads for state management."""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()
        self.bd = BeadsController(project_path)

    def get_project_info(self) -> dict[str, Any]:
        """Detect project info from overview.md via LLM."""

    def get_feature_status(self) -> dict[str, Any]:
        """Get feature status from beads issues."""

    def get_next_feature(self) -> dict[str, Any] | None:
        """Get next ready issue from beads (no blockers)."""

    def discover_plans(self) -> list[PlanInfo]:
        """Discover available plans from thoughts directory."""

    def create_phase_issues(self, phase_files, epic_title) -> dict:
        """Create beads issues for phases with priority by order."""
```

**Key methods for brownfield**:
- `discover_plans()` - Finds existing plan files in `thoughts/**/plans/`
- `get_project_info()` - Auto-detects tech stack from overview.md
- `get_next_feature()` - Returns next issue without blockers

---

### 5. Resume Flow for Brownfield

**Location**: `/home/maceo/Dev/silmari-Context-Engine/planning_orchestrator.py:291-388`

The resume flow handles interrupted pipelines:

```python
def handle_resume_flow(args, project_path: Path) -> int:
    """Handle the --resume flow."""
    # Auto-detect from checkpoint
    checkpoint = detect_resumable_checkpoint(project_path)

    if checkpoint:
        # Extract paths from checkpoint artifacts
        for artifact in artifacts:
            if "research" in artifact.lower():
                args.research_path = str(artifact_path)
            elif "plan" in artifact.lower():
                args.plan_path = str(artifact_path)

        # Determine resume step from checkpoint phase
        phase = checkpoint.get("phase", "").lower()
        if "requirement" in phase:
            args.resume_step = "requirement_decomposition"
        elif "planning" in phase:
            args.resume_step = "planning"
        elif "phase" in phase:
            args.resume_step = "phase_decomposition"

    # Execute from specific step
    return execute_from_step(
        project_path=project_path,
        resume_step=resume_step,
        research_path=args.research_path,
        plan_path=args.plan_path,
    )
```

**Resume step options**:
| Step | Requires | Produces |
|------|----------|----------|
| `planning` | `--research-path` | plan_path |
| `requirement_decomposition` | `--research-path` | hierarchy, runs planning too |
| `phase_decomposition` | `--plan-path` | phase_files |

---

### 6. Step Functions (Individual Pipeline Components)

Each step can be called independently:

| Step Function | Location | Input | Output |
|--------------|----------|-------|--------|
| `step_research` | `steps.py:12-90` | `project_path, prompt` | `research_path, open_questions` |
| `step_memory_sync` | `steps.py:546-640` | `project_path, research_path, session_id` | `episode_recorded, context_cleared` |
| `step_requirement_decomposition` | `step_decomposition.py:34-189` | `project_path, research_path` | `hierarchy_path, diagram_path, requirement_count` |
| `step_planning` | `steps.py:93-236` | `project_path, research_path, context` | `plan_path` |
| `step_phase_decomposition` | `steps.py:239-296` | `project_path, plan_path` | `phase_files[]` |
| `step_beads_integration` | `steps.py:299-420` | `project_path, phase_files, epic_title` | `epic_id, phase_issues[]` |

---

## 🚀 How to Use on Brownfield Projects

### Option 1: Full Pipeline (Recommended)

```bash
cd ~/existing-project
python /path/to/planning_orchestrator.py --ticket ENG-1234
```

Enter your research prompt when prompted:
```
Enter your research prompt (blank line to finish):
----------------------------------------
Analyze the authentication system and plan migration to JWT tokens
<blank line>
```

### Option 2: Resume from Existing Research

If you already have a research document:
```bash
python planning_orchestrator.py --resume --resume-step planning \
    --research-path thoughts/shared/research/2026-01-02-auth-analysis.md
```

### Option 3: Resume from Existing Plan

If you already have a plan document:
```bash
python planning_orchestrator.py --resume --resume-step phase_decomposition \
    --plan-path thoughts/shared/plans/2026-01-02-jwt-migration.md
```

### Option 4: Programmatic Usage

```python
from pathlib import Path
from planning_pipeline import PlanningPipeline

project = Path("~/existing-project").expanduser()
pipeline = PlanningPipeline(project)

result = pipeline.run(
    research_prompt="Analyze the auth system",
    ticket_id="ENG-1234",
    auto_approve=False  # Interactive checkpoints
)

if result["success"]:
    print(f"Plan directory: {result['plan_dir']}")
    print(f"Epic ID: {result['epic_id']}")
```

### Option 5: Use IntegratedOrchestrator for State

```python
from pathlib import Path
from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

project = Path("~/existing-project").expanduser()
orch = IntegratedOrchestrator(project)

# Discover existing plans
plans = orch.discover_plans()
for plan in plans:
    print(f"Found: {plan.name} (priority {plan.priority})")

# Get project info (auto-detected)
info = orch.get_project_info()
print(f"Tech stack: {info['stack']}")

# Get next feature to implement
feature = orch.get_next_feature()
if feature:
    print(f"Next: {feature['title']}")
```

---

## 📚 Code References

| Component | File:Line | Description |
|-----------|-----------|-------------|
| Greenfield orchestrator | `orchestrator.py:1-1366` | Full greenfield project builder |
| Planning pipeline CLI | `planning_orchestrator.py:1-567` | CLI entry point for planning |
| Pipeline class | `planning_pipeline/pipeline.py:13-281` | 6-step pipeline orchestration |
| IntegratedOrchestrator | `planning_pipeline/integrated_orchestrator.py:1-291` | Beads state management |
| Research step | `planning_pipeline/steps.py:12-90` | Codebase research |
| Planning step | `planning_pipeline/steps.py:93-236` | Plan generation |
| Phase decomposition | `planning_pipeline/steps.py:239-296` | Split plan into phases |
| Beads integration | `planning_pipeline/steps.py:299-420` | Create issues |
| Requirement decomposition | `planning_pipeline/step_decomposition.py:34-189` | BAML-based decomposition |
| Checkpoint manager | `planning_pipeline/checkpoint_manager.py:1-223` | Checkpoint CRUD |
| Beads controller | `planning_pipeline/beads_controller.py:1-104` | bd CLI wrapper |
| Claude runner | `planning_pipeline/claude_runner.py:23-82` | Claude subprocess |

---

## 🏛️ Architecture Documentation

### Current State: Two Parallel Systems

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CURRENT ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  GREENFIELD SYSTEM                  BROWNFIELD SYSTEM               │
│  ─────────────────                  ────────────────                │
│                                                                     │
│  orchestrator.py                    planning_orchestrator.py        │
│       │                                    │                        │
│       ▼                                    ▼                        │
│  feature_list.json              PlanningPipeline                    │
│       │                                    │                        │
│       ▼                                    ▼                        │
│  Claude Code sessions           step_research()                     │
│  with prompts                   step_requirement_decomposition()    │
│       │                         step_planning()                     │
│       ▼                         step_phase_decomposition()          │
│  .agent/workflows/              step_beads_integration()            │
│                                            │                        │
│                                            ▼                        │
│                                 IntegratedOrchestrator              │
│                                 (beads state management)            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Gap: No Bridge Between Systems

The root `orchestrator.py` does not call the planning pipeline. To use on brownfield:

1. **Use `planning_orchestrator.py` directly** (recommended)
2. Or call pipeline steps programmatically
3. Or create a custom script combining both

---

## 📜 Historical Context (from thoughts/)

| Document | Key Insight |
|----------|-------------|
| `thoughts/shared/research/2026-01-01-planning-orchestrator-integration.md` | Design for IntegratedOrchestrator replacing feature_list.json with beads |
| `thoughts/shared/research/2026-01-01-loop-runner-integrated-orchestrator-analysis.md` | Decision to create AutonomousLoopRunner, not port loop-runner.py |
| `thoughts/shared/plans/2026-01-01-tdd-loop-runner-integrated-orchestrator.md` | TDD plan for integrating LoopRunner with IntegratedOrchestrator |
| `thoughts/shared/research/2026-01-01-resume-pipeline-integration.md` | Resume flow design with checkpoint auto-detection |
| `thoughts/shared/docs/2025-12-31-how-to-run-planning-pipeline.md` | Operational guide for running the 5-step pipeline |

---

## ❓ Open Questions

1. **Should orchestrator.py call planning_orchestrator.py?**
   - Currently they are completely separate systems
   - Could add a third menu option: "3. Plan changes to existing project"

2. **How to transition from planning to execution?**
   - After `step_beads_integration()` creates issues, who runs them?
   - Need `AutonomousLoopRunner` from loop-runner analysis to execute features

3. **Checkpoint cleanup policy?**
   - Currently warns at 30 days
   - Should auto-cleanup after successful pipeline completion (currently does)

---

## ✅ Recommendations for Usage

### For Brownfield Projects

```bash
# 1. Navigate to your project
cd ~/my-existing-project

# 2. Run the planning pipeline
python /path/to/silmari-Context-Engine/planning_orchestrator.py \
    --project . \
    --ticket ENG-1234

# 3. Enter research prompt interactively
# 4. Review and approve at each checkpoint
# 5. Check beads for created issues
bd list --status=open
```

### For Execution After Planning

After the pipeline creates beads issues, execute them using the IntegratedOrchestrator:

```python
from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

orch = IntegratedOrchestrator("/path/to/project")

while True:
    feature = orch.get_next_feature()
    if not feature:
        break
    print(f"Working on: {feature['title']}")
    # ... execute feature ...
    # Update status via bd CLI
```
