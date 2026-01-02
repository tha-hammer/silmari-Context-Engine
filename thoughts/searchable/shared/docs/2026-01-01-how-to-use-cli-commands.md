---
date: 2026-01-01T17:32:38-05:00
researcher: Claude Opus 4.5
git_commit: 170cbfdb7565a893100ca5817913d9b4937cd23e
branch: main
repository: silmari-Context-Engine
topic: "How to Use Command Line Commands"
tags: [documentation, cli, how-to, orchestrator, planning-pipeline, integrated-orchestrator, loop-runner, autonomous-loop, requirement-decomposition]
status: complete
last_updated: 2026-01-02
last_updated_by: Claude Opus 4.5
---

# How to Use Silmari Context Engine CLI Commands

This guide provides step-by-step instructions for using the command-line tools in the Silmari Context Engine to orchestrate AI-powered project development.

## Prerequisites

- Python 3.11+ installed
- Claude Code CLI (`claude`) installed and configured
- Beads CLI (`bd`) installed and available in PATH
- Git repository initialized in your project

---

## How to Run a Full Project Orchestration

Use `orchestrator.py` to initialize and run an AI-powered development session on a project.

**Steps:**

1. **Start a new project:**
   ```bash
   python orchestrator.py --new ~/path/to/project
   ```

2. **Continue an existing project:**
   ```bash
   python orchestrator.py --project ~/path/to/project --continue
   ```

3. **Check project status:**
   ```bash
   python orchestrator.py --project ~/path/to/project --status
   ```

4. **Run with a specific model:**
   ```bash
   python orchestrator.py --project ~/path/to/project --model opus
   ```

5. **Enable QA testing with Playwright:**
   ```bash
   python orchestrator.py --project ~/path/to/project --with-qa
   ```


## How to Run the Planning Pipeline

Use `planning_orchestrator.py` to execute a 6-step planning workflow: Research, Requirement Decomposition, Planning, Phase Decomposition, Beads Integration, and Memory Capture.

**Steps:**

1. **Run interactively in current directory:**
   ```bash
   python planning_orchestrator.py
   ```
   You will be prompted to enter your research question.

2. **Run with a specific project and ticket:**
   ```bash
   python planning_orchestrator.py --project ~/path/to/project --ticket AUTH-001
   ```

3. **Run non-interactively with a prompt:**
   ```bash
   python planning_orchestrator.py --prompt-text "Implement user authentication with OAuth2"
   ```

4. **Skip interactive confirmations:**
   ```bash
   python planning_orchestrator.py --auto-approve
   ```

5. **Resume from a previous step:**
   ```bash
   # Resume from planning (step 3)
   python planning_orchestrator.py --resume --resume-step planning

   # Resume from requirement decomposition (step 2)
   python planning_orchestrator.py --resume --resume-step requirement_decomposition

   # Resume from phase decomposition (step 4)
   python planning_orchestrator.py --resume --resume-step phase_decomposition
   ```

   Available resume steps: `planning`, `requirement_decomposition`, `phase_decomposition`

6. **Use existing research or plan files:**
   ```bash
   # Provide research file when resuming from requirement_decomposition or planning
   python planning_orchestrator.py --resume --research-path thoughts/research/my-research.md

   # Provide plan file when resuming from phase_decomposition
   python planning_orchestrator.py --resume --plan-path thoughts/plans/my-plan.md
   ```

7. **Combine resume options:**
   ```bash
   python planning_orchestrator.py --resume \
     --resume-step requirement_decomposition \
     --research-path thoughts/shared/research/2026-01-02-feature-research.md \
     --auto-approve
   ```

**Pipeline Steps:**

| Step | Name | Description |
|------|------|-------------|
| 1/6 | Research | Claude researches the topic and generates a research document |
| 2/6 | Requirement Decomposition | BAML-based decomposition into structured requirements with Mermaid visualization |
| 3/6 | Planning | Claude creates a detailed implementation plan |
| 4/6 | Phase Decomposition | Plan is split into phase files |
| 5/6 | Beads Integration | Epic and phase issues are created in beads |
| 6/6 | Memory Capture | Session data is recorded to memory systems |

**Handling Decomposition Failures:**

When requirement decomposition fails (e.g., BAML API issues), the pipeline prompts:
- **(R)etry** - Attempt decomposition again
- **(C)ontinue** - Skip decomposition and proceed to planning

In `--auto-approve` mode, failures are logged and the pipeline continues automatically.

---

## How to Run the Autonomous Feature Loop

Use `loop-runner.py` to autonomously implement features from a `feature_list.json` file.

**Steps:**

1. **Run in current directory:**
   ```bash
   python loop-runner.py
   ```

2. **Run in a specific project:**
   ```bash
   python loop-runner.py ~/path/to/project
   ```

3. **Limit the number of sessions:**
   ```bash
   python loop-runner.py --max-sessions 20
   ```

4. **Run interactively (opens shell for each feature):**
   ```bash
   python loop-runner.py --interactive
   ```

5. **View blocked features:**
   ```bash
   python loop-runner.py --show-blocked
   ```

6. **Unblock a specific feature:**
   ```bash
   python loop-runner.py --unblock FEATURE_ID
   ```

7. **View metrics report:**
   ```bash
   python loop-runner.py --metrics
   ```

8. **Validate feature_list.json:**
   ```bash
   python loop-runner.py --validate
   ```

---

## How to Configure MCP Servers

Use `mcp-setup.py` to configure Model Context Protocol servers for Claude Code.

**Steps:**

1. **Run the interactive wizard:**
   ```bash
   python mcp-setup.py
   ```

2. **Use a preset configuration:**
   ```bash
   python mcp-setup.py --preset web
   ```
   Available presets: `web`, `fullstack`, `data`, `devops`, `minimal`, `rust`, `python`, `node`, `docs`

3. **Add a specific MCP by name:**
   ```bash
   python mcp-setup.py --add postgres
   python mcp-setup.py --add filesystem
   ```

4. **Add an MCP from GitHub:**
   ```bash
   python mcp-setup.py --add "github.com/org/repo"
   ```

5. **List available MCPs:**
   ```bash
   python mcp-setup.py --list
   ```

6. **Use Claude to recommend MCPs based on your project:**
   ```bash
   python mcp-setup.py --smart
   ```

---

## How to Use Beads for Issue Tracking

The `bd` command manages issues, epics, and dependencies. It is called directly or via the `BeadsController` class.

**Steps:**

1. **Create a new task:**
   ```bash
   bd create --title="Implement login" --type=task --priority=2
   ```

2. **Create an epic:**
   ```bash
   bd create --title="Authentication System" --type=epic --priority=1
   ```

3. **List all open issues:**
   ```bash
   bd list --status=open
   ```

4. **View ready issues (no blockers):**
   ```bash
   bd ready
   ```

5. **Add a dependency (issue depends on another):**
   ```bash
   bd dep add ISSUE_ID DEPENDS_ON_ID
   ```

6. **Update issue status:**
   ```bash
   bd update ISSUE_ID --status=in_progress
   ```

7. **Close an issue:**
   ```bash
   bd close ISSUE_ID --reason="Completed implementation"
   ```

8. **Sync with git remote:**
   ```bash
   bd sync
   ```

---

## How to Install the Context Engine

Use `install.sh` to install the orchestrator tools to your system.

**Steps:**

1. **Run the installer:**
   ```bash
   bash install.sh
   ```
   This copies `orchestrator.py`, `loop-runner.py`, and `mcp-setup.py` to `~/tools/context-engine`.

2. **Set up the context-engineered harness:**
   ```bash
   bash setup-context-engineered.sh
   ```
   This configures the 4-layer memory architecture and hooks.

---

## Common Workflows

### Start a New Feature Implementation Project

```bash
# 1. Initialize the project
python orchestrator.py --new ~/myproject

# 2. Configure MCP servers
python mcp-setup.py --project ~/myproject --preset fullstack

# 3. Run the planning pipeline
python planning_orchestrator.py --project ~/myproject --ticket PROJ-001

# 4. Run the autonomous loop
python loop-runner.py ~/myproject --max-sessions 50
```

### Resume Work After Interruption

```bash
# Resume from requirement decomposition (includes planning + subsequent steps)
python planning_orchestrator.py --project ~/myproject --resume --resume-step requirement_decomposition

# Resume from planning step only
python planning_orchestrator.py --project ~/myproject --resume --resume-step planning

# Resume from phase decomposition (when plan already exists)
python planning_orchestrator.py --project ~/myproject --resume --resume-step phase_decomposition

# Auto-detect resume point from checkpoints
python planning_orchestrator.py --project ~/myproject --resume

# Or continue the orchestrator
python orchestrator.py --project ~/myproject --continue
```

---

---

## How to Use the Integrated Orchestrator

Use `IntegratedOrchestrator` from `planning_pipeline/integrated_orchestrator.py` to manage project state through beads and coordinate LLM-powered planning workflows programmatically.

**Steps:**

1. **Initialize the orchestrator:**
   ```python
   from pathlib import Path
   from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

   orchestrator = IntegratedOrchestrator(Path("~/myproject"))
   ```

2. **Detect project information:**
   ```python
   info = orchestrator.get_project_info()
   print(f"Project: {info['name']}")
   print(f"Stack: {info['stack']}")
   print(f"Description: {info['description']}")
   ```
   This uses Claude to analyze overview files or README and extract project metadata.

3. **Get feature status from beads:**
   ```python
   status = orchestrator.get_feature_status()
   print(f"Total: {status['total']}")
   print(f"Completed: {status['completed']}")
   print(f"Remaining: {status['remaining']}")
   print(f"Blocked: {status['blocked']}")
   ```

4. **Get the next ready feature:**
   ```python
   feature = orchestrator.get_next_feature()
   if feature:
       print(f"Next: {feature['title']} ({feature['id']})")
   else:
       print("No features ready")
   ```
   Returns the next issue with no blockers and all dependencies met.

5. **Create phase issues from plan files:**
   ```python
   phase_files = [
       "thoughts/plans/01-setup.md",
       "thoughts/plans/02-implementation.md",
       "thoughts/plans/03-testing.md"
   ]
   result = orchestrator.create_phase_issues(phase_files, "Feature Implementation")
   print(f"Epic ID: {result['epic_id']}")
   for phase in result['phase_issues']:
       print(f"  Phase {phase['phase']}: {phase['issue_id']}")
   ```
   Creates an epic and linked phase tasks with sequential dependencies.

6. **Sync features with git remote:**
   ```python
   exit_code = orchestrator.sync_features_with_git()
   if exit_code == 0:
       print("Synced successfully")
   ```

7. **Log session activity:**
   ```python
   orchestrator.log_session(
       session_id="abc123",
       action="get_next_feature",
       result={"feature_id": "beads-001", "title": "Setup auth"}
   )
   ```
   Logs are written to `.agent/sessions/<session_id>.json`.

8. **Discover available plans:**
   ```python
   plans = orchestrator.discover_plans()
   for plan in plans:
       print(f"{plan.name} (priority {plan.priority}): {plan.path}")
   ```
   Searches `thoughts/**/plans/*-overview.md` and returns plans sorted by priority.

9. **Get currently in-progress feature:**
   ```python
   current = orchestrator.get_current_feature()
   if current:
       print(f"In progress: {current['title']} ({current['id']})")
   ```
   Returns the first issue with status `in_progress`, useful for resuming interrupted work.

---

## How to Use the Async LoopRunner with Orchestrator Integration

Use `LoopRunner` from `planning_pipeline/autonomous_loop.py` to run an async execution loop that integrates with `IntegratedOrchestrator` for automatic plan discovery, phase progression, and status tracking.

**Steps:**

1. **Initialize with orchestrator (automatic mode):**
   ```python
   import asyncio
   from pathlib import Path
   from planning_pipeline.autonomous_loop import LoopRunner, LoopState
   from planning_pipeline.integrated_orchestrator import IntegratedOrchestrator

   orchestrator = IntegratedOrchestrator(Path("~/myproject"))
   runner = LoopRunner(orchestrator=orchestrator)
   ```
   The orchestrator provides plan discovery and feature tracking.

2. **Initialize with explicit plan path (manual mode):**
   ```python
   runner = LoopRunner(plan_path="/path/to/my-plan.md")
   ```
   Use this mode for backward compatibility when no orchestrator is available.

3. **Run the execution loop:**
   ```python
   async def main():
       await runner.run()
       print(f"Final state: {runner.state}")  # COMPLETED or FAILED

   asyncio.run(main())
   ```
   With an orchestrator, the loop:
   - Discovers plans from `thoughts/**/plans/*-overview.md`
   - Queries `get_next_feature()` for each phase
   - Skips BLOCKED features automatically
   - Updates issue status to `in_progress`, `completed`, or `failed`

4. **Check the runner state:**
   ```python
   if runner.state == LoopState.COMPLETED:
       print("All features done!")
   elif runner.state == LoopState.FAILED:
       print(f"Failed at phase: {runner.current_phase}")
   elif runner.state == LoopState.PAUSED:
       print("Execution paused")
   ```
   Available states: `IDLE`, `RUNNING`, `PAUSED`, `COMPLETED`, `FAILED`

5. **Pause and resume execution:**
   ```python
   async def run_with_pause():
       # Start running
       task = asyncio.create_task(runner.run())

       # Pause after some condition
       await runner.pause()
       print(f"Paused at: {runner.current_phase}")

       # Later, resume
       await runner.resume()
       print(f"Final state: {runner.state}")
   ```
   When resuming with an orchestrator, the runner queries `get_current_feature()` to restore state from any `in_progress` issue.

6. **Use both orchestrator and explicit plan path:**
   ```python
   runner = LoopRunner(
       orchestrator=orchestrator,
       plan_path="/explicit/override-plan.md"
   )
   await runner.run()
   ```
   When an explicit `plan_path` is provided, it takes precedence over orchestrator discovery.

7. **Set initial phase:**
   ```python
   runner = LoopRunner(
       plan_path="/path/to/plan.md",
       current_phase="phase-3"
   )
   ```
   Use this to start execution at a specific phase.

---

## How to Use Requirement Decomposition in the Planning Pipeline

Use `step_requirement_decomposition()` from `planning_pipeline/step_decomposition.py` to decompose research documents into structured requirement hierarchies with Mermaid visualization and property-based test skeletons.

**Pipeline Position:** `step_research()` → `step_requirement_decomposition()` → `step_planning()`

**Steps:**

1. **Run requirement decomposition on a research file:**
   ```python
   from pathlib import Path
   from planning_pipeline.step_decomposition import step_requirement_decomposition

   result = step_requirement_decomposition(
       project_path=Path.cwd(),
       research_path="thoughts/shared/research/2026-01-02-my-feature-research.md"
   )
   ```

2. **Check the result and access output files:**
   ```python
   if result["success"]:
       print(f"Hierarchy JSON: {result['hierarchy_path']}")
       print(f"Mermaid diagram: {result['diagram_path']}")
       print(f"Test skeleton: {result.get('tests_path', 'None')}")
       print(f"Total requirements: {result['requirement_count']}")
   else:
       print(f"Error: {result['error']}")
   ```

3. **Specify a custom output directory:**
   ```python
   result = step_requirement_decomposition(
       project_path=Path.cwd(),
       research_path="thoughts/shared/research/my-research.md",
       output_dir="/path/to/custom/output"
   )
   ```
   By default, outputs are written to `{project}/thoughts/shared/plans/{date}-requirements/`.

4. **View the generated Mermaid diagram:**
   - Open the `.mmd` file in [Mermaid Live Editor](https://mermaid.live) to visualize the requirement hierarchy
   - Or use VS Code with the Mermaid extension
   - The diagram shows requirements as rectangles with parent-child relationships

5. **Use the generated test skeleton:**
   - Open `property_tests_skeleton.py` in the output directory
   - The file contains Hypothesis-based test stubs derived from acceptance criteria
   - Fill in the `TODO` sections with actual implementation tests

**Output Files:**

| File | Description |
|------|-------------|
| `requirements_hierarchy.json` | Full requirement hierarchy with metadata, acceptance criteria, and implementation components |
| `requirements_diagram.mmd` | Mermaid flowchart showing requirement relationships |
| `property_tests_skeleton.py` | Hypothesis test stubs (only created if acceptance criteria exist) |

**Integration with Planning Orchestrator:**

```python
from planning_pipeline.steps import step_research
from planning_pipeline.step_decomposition import step_requirement_decomposition

# Step 1: Run research
research_result = step_research(project_path, "Implement user authentication")

# Step 2: Decompose into requirements
if research_result["success"]:
    decomp_result = step_requirement_decomposition(
        project_path=project_path,
        research_path=research_result["research_path"]
    )

    if decomp_result["success"]:
        print(f"Created {decomp_result['requirement_count']} requirements")
        # Continue to step_planning() with the hierarchy
```

---

## Conclusion

For detailed API documentation and parameter references, consult the source files directly:

- `orchestrator.py` - Full orchestration with argparse help (`--help`)
- `planning_orchestrator.py` - Planning pipeline with argparse help
- `loop-runner.py` - Feature loop with argparse help
- `mcp-setup.py` - MCP configuration with argparse help
- `planning_pipeline/beads_controller.py` - BeadsController class methods
- `planning_pipeline/integrated_orchestrator.py` - IntegratedOrchestrator and PlanInfo classes
- `planning_pipeline/autonomous_loop.py` - LoopRunner and LoopState for async orchestrator integration
- `planning_pipeline/step_decomposition.py` - step_requirement_decomposition() for research decomposition
- `planning_pipeline/decomposition.py` - decompose_requirements() BAML-based decomposition
- `planning_pipeline/visualization.py` - generate_requirements_mermaid() diagram generation
- `planning_pipeline/property_generator.py` - derive_properties() and generate_test_skeleton() for Hypothesis tests
