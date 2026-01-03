# Planning Pipeline System Architecture

## Overview

The planning pipeline is a multi-stage orchestration system that transforms research prompts into structured, trackable implementation plans. It integrates with Claude Code for LLM operations and Beads for issue tracking.

## System Diagram

```mermaid
flowchart TD
    subgraph Entry["Entry Points"]
        CLI["planning_orchestrator.py<br/>CLI Entry Point"]
        Resume["resume_planning.py<br/>Resume Entry"]
    end

    subgraph Core["Core Pipeline (pipeline.py)"]
        PP["PlanningPipeline"]

        subgraph Steps["6-Step Flow"]
            S1["Step 1: Research<br/>step_research()"]
            S2["Step 2: Memory Sync<br/>step_memory_sync()"]
            S3["Step 3: Requirement Decomposition<br/>step_requirement_decomposition()"]
            S4["Step 4: Planning<br/>step_planning()"]
            S5["Step 5: Phase Decomposition<br/>step_phase_decomposition()"]
            S6["Step 6: Beads Integration<br/>step_beads_integration()"]
        end
    end

    subgraph Checkpoints["Checkpoint System"]
        CP_INT["interactive_checkpoint_research()<br/>interactive_checkpoint_plan()"]
        CP_MGR["checkpoint_manager.py<br/>write/detect/delete checkpoints"]
    end

    subgraph Decomposition["Decomposition Modules"]
        SD["step_decomposition.py<br/>BAML-based decomposition"]
        DEC["decomposition.py<br/>Iterative decomposition loop"]
        VIZ["visualization.py<br/>Mermaid diagram generation"]
        PROP["property_generator.py<br/>Requirements property generator"]
    end

    subgraph Execution["Phase Execution (autonomous_loop.py)"]
        LR["LoopRunner"]
        PB["prompt_builder.py<br/>Build phase prompts"]
        CI["claude_invoker.py<br/>Claude subprocess"]
        RC["result_checker.py<br/>Validate & sync"]
    end

    subgraph External["External Systems"]
        Claude["Claude Code CLI<br/>claude --print"]
        Beads["BeadsController<br/>bd CLI wrapper"]
        Git["Git Repository"]
        Memory["Memory System<br/>(silmari-oracle)"]
    end

    subgraph Orchestrator["Integrated Orchestrator"]
        IO["IntegratedOrchestrator<br/>Plan discovery & feature tracking"]
    end

    %% Entry flow
    CLI --> PP
    Resume --> CP_MGR
    CP_MGR -.->|restore| PP

    %% Main pipeline flow
    PP --> S1
    S1 --> CP_INT
    CP_INT -->|approve| S2
    CP_INT -.->|revise/restart| S1
    S2 --> S3
    S3 --> S4
    S4 --> CP_INT
    S4 --> S5
    S5 --> S6

    %% Step implementations
    S1 --> Claude
    S2 --> Memory
    S3 --> SD
    SD --> DEC
    DEC --> VIZ
    DEC --> PROP
    S4 --> Claude
    S5 --> Claude
    S6 --> Beads

    %% Execution loop
    IO --> LR
    LR --> PB
    PB --> CI
    CI --> Claude
    CI --> RC
    RC --> Git
    RC --> Beads

    %% Checkpoint connections
    S1 -.->|failure| CP_MGR
    S4 -.->|failure| CP_MGR
    S5 -.->|failure| CP_MGR
```

## Component Details

### Entry Points

| Component | File | Purpose |
|-----------|------|---------|
| `planning_orchestrator.py` | Root | CLI entry point, handles `--resume` flag |
| `resume_planning.py` | Root | Dedicated resume functionality |

### Core Pipeline (`planning_pipeline/pipeline.py`)

**PlanningPipeline** class orchestrates the 6-step flow:

```python
class PlanningPipeline:
    def __init__(self, project_path: Path)
    def run(self, research_prompt: str, ticket_id: Optional[str], auto_approve: bool) -> dict
```

### Step Functions (`planning_pipeline/steps.py`)

| Step | Function | Input | Output | Claude Command |
|------|----------|-------|--------|----------------|
| 1 | `step_research()` | project_path, prompt | research doc path | `/research_codebase` |
| 2 | `step_memory_sync()` | project_path, research_path, session_id | sync result | `silmari-oracle` commands |
| 3 | `step_requirement_decomposition()` | project_path, research_path | hierarchy + diagram | BAML functions |
| 4 | `step_planning()` | project_path, research_path, context | plan doc path | `/create_tdd_plan` |
| 5 | `step_phase_decomposition()` | project_path, plan_path | phase files list | Direct Claude |
| 6 | `step_beads_integration()` | project_path, phase_files, epic_title | epic_id, issues | `bd` commands |

### Checkpoint System

**`checkpoints.py`** - Interactive checkpoints:
- `interactive_checkpoint_research()` - Review research, approve/revise/restart/exit
- `interactive_checkpoint_plan()` - Review plan, approve or provide feedback

**`checkpoint_manager.py`** - Persistence:
- `write_checkpoint()` - Save state with completed files and errors
- `detect_resumable_checkpoint()` - Find latest checkpoint
- `delete_checkpoint()` - Clean up on completion

### Decomposition Modules

**`step_decomposition.py`** - BAML-based structured decomposition:
- Uses `DecomposeRequirements` BAML function
- Falls back to Claude Code on BAML failure
- Generates hierarchy YAML and Mermaid diagram

**`decomposition.py`** - Iterative decomposition loop:
- `run_decomposition()` - Main entry point
- `decompose_with_visualization()` - Generate requirements with diagrams
- Multi-iteration refinement support

**`visualization.py`** - Mermaid diagram generation:
- `generate_mermaid_diagram()` - Create requirement hierarchy diagrams
- Supports customizable styling

**`property_generator.py`** - Requirements properties:
- Generate additional metadata for requirements

### Phase Execution (`planning_pipeline/autonomous_loop.py`)

**LoopRunner** class for autonomous plan execution:

```python
class LoopRunner:
    def __init__(self, plan_path, current_phase, orchestrator, project_path)
    async def run()      # Main execution loop
    async def pause()    # Pause execution
    async def resume()   # Resume from pause
```

**`phase_execution/` module:**

| File | Function | Purpose |
|------|----------|---------|
| `prompt_builder.py` | `build_phase_prompt()` | Construct prompts from plan files |
| `claude_invoker.py` | `invoke_claude()` | Subprocess invocation with timeout |
| `result_checker.py` | `check_execution_result()` | Validate results, run bd sync |

### Integrated Orchestrator (`integrated_orchestrator.py`)

**IntegratedOrchestrator** for LLM-driven plan discovery:

```python
class IntegratedOrchestrator:
    def discover_plans() -> list[PlanInfo]
    def get_next_feature() -> Optional[dict]
    def get_current_feature() -> Optional[dict]
```

### External Systems

| System | Interface | Purpose |
|--------|-----------|---------|
| Claude Code | `claude --print -p` | LLM operations |
| Beads | `BeadsController` / `bd` CLI | Issue tracking |
| Git | subprocess | Version control |
| silmari-oracle | subprocess | Memory management |

## Data Flow

### Planning Flow (Pipeline)

```
research_prompt
    │
    ▼
┌─────────────────┐
│  step_research  │ ──► research document (markdown)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ step_memory_sync│ ──► episodic memory recorded
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│step_requirement_decomp. │ ──► hierarchy.yaml + diagram.md
└────────┬────────────────┘
         │
         ▼
┌─────────────────┐
│  step_planning  │ ──► TDD plan document (markdown)
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│step_phase_decomposition │ ──► phase files (01-setup.md, 02-impl.md, ...)
└────────┬────────────────┘
         │
         ▼
┌────────────────────────┐
│step_beads_integration  │ ──► epic + phase issues in Beads
└────────────────────────┘
```

### Execution Flow (LoopRunner)

```
plan_path
    │
    ▼
┌──────────────────┐
│ build_phase_prompt│ ──► formatted prompt string
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  invoke_claude   │ ──► {success, output, error, elapsed}
└────────┬─────────┘
         │
         ▼
┌─────────────────────────┐
│ check_execution_result  │ ──► boolean (pass/fail)
└────────┬────────────────┘
         │
         ├──► git status check
         └──► bd sync
```

## State Management

### Checkpoint States

```
IDLE ──► RUNNING ──► PAUSED
              │          │
              ▼          ▼
         COMPLETED   RUNNING (resume)
              │
              ▼
           FAILED
```

### Beads Issue States

```
open ──► in_progress ──► completed
              │
              ▼
           failed
           blocked
```

## Key Interfaces

### Claude Runner (`claude_runner.py`)

```python
def run_claude_command(
    project_path: Path,
    prompt: str,
    permission_mode: str = "bypassPermissions",
    print_mode: bool = True,
    timeout: int = 300
) -> dict[str, Any]
```

### BeadsController

```python
class BeadsController:
    def create_epic(title: str, description: str) -> str
    def create_issue(title: str, description: str, type: str) -> str
    def add_dependency(issue_id: str, depends_on: str) -> bool
    def update_status(issue_id: str, status: str) -> dict
    def sync() -> dict
```

## File Locations

```
planning_pipeline/
├── __init__.py                    # Module exports
├── pipeline.py                    # PlanningPipeline class
├── steps.py                       # Step functions
├── checkpoints.py                 # Interactive checkpoints
├── checkpoint_manager.py          # Checkpoint persistence
├── step_decomposition.py          # BAML decomposition
├── decomposition.py               # Iterative decomposition
├── visualization.py               # Mermaid generation
├── property_generator.py          # Requirements properties
├── beads_controller.py            # Beads CLI wrapper
├── claude_runner.py               # Claude subprocess runner
├── autonomous_loop.py             # LoopRunner class
├── integrated_orchestrator.py     # Plan discovery
└── phase_execution/
    ├── __init__.py
    ├── prompt_builder.py          # Build prompts
    ├── claude_invoker.py          # Claude subprocess
    └── result_checker.py          # Validate results
```

## References

- Pipeline entry: `planning_orchestrator.py:1-75`
- Main pipeline: `planning_pipeline/pipeline.py:1-282`
- Step functions: `planning_pipeline/steps.py`
- Autonomous loop: `planning_pipeline/autonomous_loop.py:1-265`
- Phase execution: `planning_pipeline/phase_execution/`
- Tests: `tests/test_execute_phase.py`, `tests/test_loop_orchestrator_integration.py`
