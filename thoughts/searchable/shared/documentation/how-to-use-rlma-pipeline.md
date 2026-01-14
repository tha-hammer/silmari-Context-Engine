---
date: 2026-01-09T20:31:25-05:00
researcher: Claude Sonnet 4.5
git_commit: 15ed191db4ff2bb1308e2f075e0af3350605f6a4
branch: main
repository: silmari-Context-Engine
topic: "How to Use the Research, Learn, Model, Act (RLMA) Pipeline"
tags: [documentation, how-to, rlma, pipeline, tdd, autonomous]
status: complete
last_updated: 2026-01-09
last_updated_by: Claude Sonnet 4.5
---

# How to Use the Research, Learn, Model, Act Pipeline

## Introduction

This guide provides step-by-step instructions for using the silmari-rlm-act pipeline to autonomously develop features using Test-Driven Development (TDD). The RLMA pipeline takes a research question as input and produces fully implemented, tested code by progressing through six distinct phases: Research, Decomposition, TDD Planning, Multi-Document Splitting, Beads Synchronization, and Implementation.

By the end of this process, you will have:
- Research documentation about the task
- A hierarchical decomposition of testable behaviors
- A comprehensive TDD implementation plan
- Phase-specific task documents
- Tracked work items in beads (optional)
- Fully implemented and tested code

## Prerequisites

Before using the RLMA pipeline, ensure you have:

- **Python environment**: Python 3.10+ installed
- **Package installation**: The `silmari-rlm-act` package installed and available as the `silmari-rlm-act` command
- **Project structure**: A valid project directory with a `.beads/` directory (if using beads integration)
- **Claude Code access**: The pipeline uses Claude Code for research and implementation phases
- **Git repository**: Your project should be a git repository (recommended for beads sync)

## Understanding the Pipeline Phases

The RLMA pipeline executes six phases in sequence:

1. **RESEARCH**: Gathers context about the task using Claude Code, producing a research document
2. **DECOMPOSITION**: Breaks down the task into a hierarchical structure of testable behaviors
3. **TDD_PLANNING**: Creates a comprehensive Red-Green-Refactor TDD plan
4. **MULTI_DOC**: Splits the TDD plan into phase-specific documents
5. **BEADS_SYNC**: Creates beads issues for tracking each phase (requires beads controller)
6. **IMPLEMENTATION**: Executes the TDD plan, implementing and testing code

## Understanding Autonomy Modes

The pipeline supports three autonomy modes that control how and when execution pauses:

- **CHECKPOINT** (default, `-p` not specified): Pauses at each phase for user review and approval
- **BATCH** (`-b` or `--batch`): Groups phases and pauses between groups
- **FULLY_AUTONOMOUS** (`-a` or `--autonomous`): Runs all phases without stopping

Choose your autonomy mode based on your trust level and how much oversight you want during execution.

## Step 1: Starting a New Pipeline Run

To begin a new RLMA pipeline execution, use the `run` command with a research question:

```bash
silmari-rlm-act run -q "How do I implement user authentication with JWT tokens?"
```

### Common Options

**Specify a different project directory:**
```bash
silmari-rlm-act run -q "..." -p /path/to/project
```

**Run in fully autonomous mode (no pauses):**
```bash
silmari-rlm-act run -q "..." -a
```

**Run in batch mode (pause between phase groups):**
```bash
silmari-rlm-act run -q "..." -b
```

**Provide a custom plan name:**
```bash
silmari-rlm-act run -q "..." -n "user-auth"
```

### What Happens During Execution

When you start a pipeline run:

1. The pipeline validates that your question is provided (unless using `--resume`)
2. It creates a CWA (Context Window Array) integration for managing context
3. It initializes a beads controller (if your project has `.beads/` directory)
4. It creates a pipeline instance with your specified autonomy mode
5. It begins executing phases in order

In **checkpoint mode**, after each phase completes, you'll be prompted to review the results and decide whether to continue. This allows you to:
- Review research findings before decomposition
- Examine the behavior hierarchy before planning
- Verify the TDD plan before implementation

In **autonomous or batch mode**, execution continues without user intervention.

## Step 2: Monitoring Pipeline Progress

### Check Current Status

To view the current pipeline state without running anything:

```bash
silmari-rlm-act status
```

Or for a specific project:

```bash
silmari-rlm-act status -p /path/to/project
```

The status command displays:
- Project path
- Current autonomy mode
- Completed phases (marked with `[x]`)
- Pending phases (marked with `[ ]`)
- Next phase to execute
- Whether all phases are complete

### Understanding Status Output

Example output:

```
============================================================
PIPELINE STATUS
============================================================

Project: /home/user/my-project
Mode: checkpoint

Completed phases:
  [x] research
  [x] decomposition
  [x] tdd_planning

Pending phases:
  [ ] multi_doc
  [ ] beads_sync
  [ ] implementation

Next: multi_doc
```

This shows that the pipeline has completed research, decomposition, and TDD planning, and will next execute the multi-document phase.

## Step 3: Resuming from a Checkpoint

The RLMA pipeline automatically creates checkpoints after each phase. If execution is interrupted or you chose to pause in checkpoint mode, you can resume from the last completed phase.

### Using the Resume Command

```bash
silmari-rlm-act resume
```

Or for a specific project:

```bash
silmari-rlm-act resume -p /path/to/project
```

### Changing Autonomy Mode on Resume

You can change the autonomy mode when resuming:

```bash
# Resume in fully autonomous mode
silmari-rlm-act resume -a

# Resume in batch mode
silmari-rlm-act resume -b

# Resume in checkpoint mode (default)
silmari-rlm-act resume
```

### Resume During Initial Run

You can also use the `--resume` flag with the `run` command:

```bash
silmari-rlm-act run --resume -a
```

This is useful when you want to resume and potentially change the plan name or other parameters.

### What Happens During Resume

When resuming:

1. The pipeline detects the most recent checkpoint file in `.workflow-checkpoints/`
2. It loads the saved pipeline state, including:
   - Completed phases and their results
   - Artifacts produced (file paths)
   - CWA entry IDs for context tracking
   - Beads epic ID (if using beads)
3. It displays what phases are complete and what's next
4. It continues execution from the next incomplete phase

If no checkpoint is found, you'll see:
```
No checkpoint found to resume from.
Use 'silmari-rlm-act run -q <question>' to start a new pipeline.
```

## Step 4: Working with Pipeline Artifacts

Each phase produces artifacts (files) that are used by subsequent phases:

### Research Phase Artifacts

- **Location**: `thoughts/searchable/shared/research/YYYY-MM-DD-*.md`
- **Content**: Research findings about the task, codebase patterns, and relevant context
- **Use**: Input for decomposition phase

### Decomposition Phase Artifacts

- **Location**: `thoughts/searchable/shared/plans/YYYY-MM-DD-*-requirements/hierarchy.json`
- **Content**: JSON structure of testable behaviors organized hierarchically
- **Use**: Input for TDD planning phase

### TDD Planning Phase Artifacts

- **Location**: `thoughts/searchable/shared/plans/YYYY-MM-DD-tdd-{plan_name}.md`
- **Content**: Complete TDD implementation plan with Red-Green-Refactor steps
- **Use**: Input for multi-document phase

### Multi-Document Phase Artifacts

- **Location**: Multiple files in `thoughts/searchable/shared/plans/YYYY-MM-DD-tdd-{plan_name}-0X-phase-X.md`
- **Content**: Phase-specific implementation documents
- **Use**: Input for beads sync and implementation phases

### Implementation Phase Artifacts

- **Location**: Your project's source code files
- **Content**: Implemented features with tests
- **Use**: The final deliverable

## Step 5: Handling Errors and Failures

If a phase fails, the pipeline will:

1. Display error messages
2. Create a checkpoint with error details
3. Exit with status code 1

### Viewing Error Details

When a pipeline run fails, you'll see:

```
============================================================
PIPELINE FAILED
============================================================

Errors:
  - Error message describing what went wrong
  - Additional error details if available
```

### Recovering from Failures

After addressing the root cause of the failure:

1. Fix the issue (e.g., install missing dependencies, fix configuration)
2. Resume from the last checkpoint: `silmari-rlm-act resume`

The pipeline will retry the failed phase with your corrections in place.

### Trade-offs in Error Handling

- **Checkpoint mode**: Allows you to catch issues early before they cascade to later phases
- **Autonomous mode**: Faster execution but failures may occur deep in the pipeline, requiring more extensive backtracking

## Step 6: Managing Checkpoints

Over time, checkpoint files accumulate in `.workflow-checkpoints/`. The pipeline provides cleanup tools.

### View Checkpoint Information

```bash
silmari-rlm-act cleanup
```

This displays:
- Most recent checkpoint phase
- Age of the checkpoint in days

### Delete Old Checkpoints

Delete checkpoints older than N days:

```bash
silmari-rlm-act cleanup --days 7
```

### Delete All Checkpoints

Remove all checkpoint files:

```bash
silmari-rlm-act cleanup --all
```

**Warning**: After deleting all checkpoints, you cannot resume the pipeline and must start fresh with `silmari-rlm-act run -q "..."`.

## Step 7: Integration with Beads Task Tracking

If your project has a `.beads/` directory, the pipeline automatically integrates with beads for task tracking.

### What Beads Integration Does

During the **BEADS_SYNC** phase, the pipeline:

1. Creates an epic issue for the overall feature
2. Creates individual task issues for each phase document
3. Adds dependencies between tasks based on phase order
4. Tracks issue IDs for use in the implementation phase

### Accessing Beads Issues

Use standard beads commands to view and manage the created issues:

```bash
# View all issues
bd list

# View the epic
bd show <epic-id>

# View a specific phase task
bd show <task-id>
```

### Closing Issues

The implementation phase can automatically close beads issues as phases complete (depending on the beads controller configuration).

## Step 8: Understanding Pipeline Completion

When all phases complete successfully, you'll see:

```
============================================================
PIPELINE COMPLETE
============================================================

Artifacts produced:
  - thoughts/searchable/shared/research/2026-01-09-user-auth.md
  - thoughts/searchable/shared/plans/2026-01-09-user-auth-requirements/hierarchy.json
  - thoughts/searchable/shared/plans/2026-01-09-tdd-user-auth.md
  - thoughts/searchable/shared/plans/2026-01-09-tdd-user-auth-01-phase-1.md
  - thoughts/searchable/shared/plans/2026-01-09-tdd-user-auth-02-phase-2.md
  - src/auth/jwt.py
  - tests/test_auth_jwt.py
```

The listed artifacts include:
- All intermediate documentation
- Implemented source files
- Test files

## Common Workflows

### Quick Autonomous Run

For straightforward tasks where you trust the pipeline to handle everything:

```bash
silmari-rlm-act run -q "Add logging to the API endpoints" -a
```

### Careful Checkpoint-Based Run

For complex or critical tasks where you want to review each phase:

```bash
# Start in checkpoint mode
silmari-rlm-act run -q "Refactor authentication system"

# Review research findings, approve
# Review decomposition, approve
# Review TDD plan, approve
# Implementation proceeds

# If you need to pause, the checkpoint is saved
# Resume later:
silmari-rlm-act resume
```

### Batch Mode for Grouped Oversight

When you want some oversight but not at every phase:

```bash
silmari-rlm-act run -q "Implement caching layer" -b
```

Batch mode groups related phases and pauses between logical groups, providing a balance between oversight and automation.

## Troubleshooting

### "No checkpoint found to resume from"

**Cause**: No checkpoint files exist in `.workflow-checkpoints/`.

**Solution**: Start a new pipeline run with `silmari-rlm-act run -q "..."`.

### Pipeline hangs during research phase

**Cause**: Claude Code may be waiting for input or processing a complex request.

**Solution**: Check the Claude Code output (streamed to console). If stuck, interrupt with Ctrl+C and resume.

### "No beads controller configured"

**Cause**: The pipeline expected beads integration but couldn't initialize the beads controller.

**Solution**: Ensure your project has a `.beads/` directory and beads is properly initialized. Or run without beads integration.

### Wrong phase documents generated

**Cause**: The multi-document phase uses the TDD plan and hierarchy. If these are incorrect, the output will be wrong.

**Solution**: Review the TDD plan artifact from the previous phase. If needed, manually edit the plan and resume execution.

## Advanced Usage

### Providing Additional Context to Research Phase

While the CLI doesn't currently expose this option directly, the research phase can accept additional context. This requires modifying the pipeline code or using the Python API directly.

### Customizing Research Templates

Place a custom research template at:
```
silmari_rlm_act/commands/research_codebase.md
```

The template should include a `{research_question}` placeholder that will be replaced with your question.

### Using the Python API

For programmatic access:

```python
from pathlib import Path
from silmari_rlm_act.pipeline import RLMActPipeline
from silmari_rlm_act.context.cwa_integration import CWAIntegration
from silmari_rlm_act.models import AutonomyMode
from planning_pipeline.beads_controller import BeadsController

project_path = Path("/path/to/project")
cwa = CWAIntegration()
beads = BeadsController(project_path)

pipeline = RLMActPipeline(
    project_path=project_path,
    cwa=cwa,
    autonomy_mode=AutonomyMode.FULLY_AUTONOMOUS,
    beads_controller=beads,
)

result = pipeline.run(
    research_question="How do I implement feature X?",
    plan_name="feature-x",
)

if result.is_complete:
    print("Success!")
    print(f"Artifacts: {result.artifacts}")
else:
    print("Failed!")
    print(f"Errors: {result.errors}")
```

## Conclusion / Next Steps

After completing a successful pipeline run:

1. **Review the code**: Examine the implemented files and tests
2. **Run tests**: Execute your test suite to verify implementation
3. **Commit changes**: Use git to commit the new code and documentation
4. **Close beads issues**: If using beads and issues weren't auto-closed, manually close them with `bd close <id>`
5. **Clean up checkpoints**: Remove old checkpoints with `silmari-rlm-act cleanup --all`

For more information on specific components, consult the related reference documentation:
- Context Window Array reference
- Beads workflow documentation
- Claude Code integration guide

## Related Documentation

- `silmari_rlm_act/pipeline.py` - Pipeline orchestration implementation
- `silmari_rlm_act/cli.py` - CLI command definitions
- `silmari_rlm_act/models.py` - Core data models and enums
- Context Window Array documentation
- Beads task tracking documentation
