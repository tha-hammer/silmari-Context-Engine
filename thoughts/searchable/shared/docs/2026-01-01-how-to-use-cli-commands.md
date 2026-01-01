---
date: 2026-01-01T17:32:38-05:00
researcher: Claude Opus 4.5
git_commit: 13313f8c47ffdb3e249df96edc42458a06b79a18
branch: main
repository: silmari-Context-Engine
topic: "How to Use Command Line Commands"
tags: [documentation, cli, how-to, orchestrator, planning-pipeline, integrated-orchestrator]
status: complete
last_updated: 2026-01-01
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

---

## How to Run the Planning Pipeline

Use `planning_orchestrator.py` to execute a 5-step planning workflow: Research, Planning, Phase Decomposition, Beads Integration, and Memory Capture.

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
   python planning_orchestrator.py --resume --resume-step planning
   ```

6. **Use existing research or plan files:**
   ```bash
   python planning_orchestrator.py --research-path thoughts/research/my-research.md
   python planning_orchestrator.py --plan-path thoughts/plans/my-plan.md
   ```

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
# Resume planning from a specific step
python planning_orchestrator.py --project ~/myproject --resume --resume-step beads

# Or continue the orchestrator
python orchestrator.py --project ~/myproject --continue
```

---

## Conclusion

For detailed API documentation and parameter references, consult the source files directly:

- `orchestrator.py` - Full orchestration with argparse help (`--help`)
- `planning_orchestrator.py` - Planning pipeline with argparse help
- `loop-runner.py` - Feature loop with argparse help
- `mcp-setup.py` - MCP configuration with argparse help
- `planning_pipeline/beads_controller.py` - BeadsController class methods
- `planning_pipeline/integrated_orchestrator.py` - IntegratedOrchestrator class methods
