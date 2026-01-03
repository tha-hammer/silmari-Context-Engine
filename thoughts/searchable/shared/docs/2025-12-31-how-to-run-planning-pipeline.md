---
date: 2025-12-31T14:55:20-05:00
researcher: maceo
git_commit: 21d7704070c3ea218db0d13655f562e44dab7f08
branch: main
repository: silmari-Context-Engine
topic: "How to Run the Planning Pipeline"
tags: [documentation, how-to, planning-pipeline, python]
status: complete
last_updated: 2025-12-31
last_updated_by: maceo
---

# How to Run the Planning Pipeline

## Introduction

This guide provides step-by-step instructions for running the `planning_pipeline` Python module. The pipeline orchestrates a 5-step planning process that uses Claude Code to research a codebase, create implementation plans, decompose plans into phases, and integrate with the beads issue tracker.

The pipeline produces:
- A research document in `thoughts/shared/research/`
- A plan document in `thoughts/shared/plans/`
- Phase files for each implementation step
- Beads issues with proper dependencies

## Prerequisites

- Python 3.12+ installed
- Claude Code CLI (`claude`) installed and authenticated
- Beads CLI (`bd`) installed and initialized in the project
- Project with `.beads/` directory configured
- Access to the `thoughts/shared/` directory structure

Verify prerequisites:
```bash
python3 --version      # Python 3.12+
claude --version       # Claude Code CLI
bd --version           # Beads CLI
```

## Steps

### 1. Navigate to the Project Directory

Change to the root directory of your project where the `planning_pipeline/` module is located.

```bash
cd /path/to/silmari-Context-Engine
```

### 2. Run the Pipeline with Python

**Option A: Interactive Mode (with checkpoints)**

```python
from pathlib import Path
from planning_pipeline import PlanningPipeline

project_path = Path.cwd()
pipeline = PlanningPipeline(project_path)

result = pipeline.run(
    research_prompt="How does the authentication system work?",
    ticket_id="AUTH-001"
)
```

In interactive mode, the pipeline pauses after the research phase to:
- Display open questions extracted from the research
- Allow you to provide answers before proceeding to planning
- Allow you to reject the plan and provide feedback for re-generation

**Option B: Auto-Approve Mode (no interactive prompts)**

```python
from pathlib import Path
from planning_pipeline import PlanningPipeline

project_path = Path.cwd()
pipeline = PlanningPipeline(project_path)

result = pipeline.run(
    research_prompt="Analyze the API endpoint structure",
    ticket_id="API-002",
    auto_approve=True
)
```

### 3. Run Individual Steps (Alternative)

For more control, run each step independently:

```python
from pathlib import Path
from planning_pipeline import (
    step_research,
    step_planning,
    step_phase_decomposition,
    step_beads_integration
)

project_path = Path.cwd()

# Step 1: Research
research = step_research(project_path, "What testing frameworks exist?")
print(f"Research: {research['research_path']}")

# Step 2: Planning
plan = step_planning(project_path, research['research_path'])
print(f"Plan: {plan['plan_path']}")

# Step 3: Phase Decomposition
phases = step_phase_decomposition(project_path, plan['plan_path'])
print(f"Phases: {phases['phase_files']}")

# Step 4: Beads Integration
beads = step_beads_integration(project_path, phases['phase_files'], "My Epic")
print(f"Epic ID: {beads['epic_id']}")
```

### 4. Use the Claude Runner Directly (Low-Level)

For custom prompts without the full pipeline:

```python
from planning_pipeline import run_claude_sync

result = run_claude_sync(
    prompt="List all Python files in the project",
    timeout=60
)

if result["success"]:
    print(result["output"])
else:
    print(f"Error: {result['error']}")
```

### 5. Use the Beads Controller Independently

Manage beads issues programmatically:

```python
from pathlib import Path
from planning_pipeline import BeadsController

bd = BeadsController(Path.cwd())

# Create an issue
issue = bd.create_issue("Fix login bug", issue_type="bug", priority=1)
print(f"Created: {issue['data']['id']}")

# List open issues
issues = bd.list_issues(status="open")

# Close an issue
bd.close_issue("beads-xxx", reason="Fixed in commit abc123")

# Sync with remote
bd.sync()
```

### 6. Run the Test Suite

Verify the pipeline installation:

```bash
python3 -m pytest planning_pipeline/tests/ -v
```

Expected output: 41 tests passing.

To skip slow tests that call Claude:

```bash
python3 -m pytest planning_pipeline/tests/ -v -m "not slow"
```

### 7. Interpret Pipeline Results

The `pipeline.run()` method returns a dictionary:

```python
{
    "success": True,
    "started": "2025-12-31T10:00:00",
    "completed": "2025-12-31T10:15:00",
    "ticket_id": "AUTH-001",
    "plan_dir": "thoughts/shared/plans/2025-12-31-plan",
    "epic_id": "beads-abc123",
    "steps": {
        "research": {"success": True, "research_path": "...", "open_questions": [...]},
        "planning": {"success": True, "plan_path": "..."},
        "decomposition": {"success": True, "phase_files": [...]},
        "beads": {"success": True, "epic_id": "...", "phase_issues": [...]},
        "memory": {"success": True}
    }
}
```

Key fields:
- `success`: Overall pipeline success
- `plan_dir`: Directory containing all phase files
- `epic_id`: Beads epic tracking this work
- `steps.<name>.success`: Individual step success status

### 8. Handle Failures

If a step fails, the result indicates where:

```python
if not result["success"]:
    if "failed_at" in result:
        print(f"Pipeline failed at: {result['failed_at']}")
        print(f"Error: {result['steps'][result['failed_at']].get('error')}")
    elif "stopped_at" in result:
        print(f"Pipeline stopped by user at: {result['stopped_at']}")
```

### 9. Resume a Failed Pipeline

When a pipeline fails, you can resume from the last successful step using the individual step functions. Here's how to resume from each failure point:

#### Resume from Research Failure

If research failed, simply re-run it:

```python
from pathlib import Path
from planning_pipeline import step_research

project_path = Path.cwd()
research = step_research(project_path, "Your research question here")
```

#### Resume from Planning Failure

If planning failed but research succeeded, use the research path:

**Option 1: Create a script file (recommended for CLI)**

```bash
cat > resume_planning.py << 'EOF'
from pathlib import Path
from planning_pipeline import step_planning, step_phase_decomposition, step_beads_integration

project_path = Path.cwd()

# Use the research path from the failed run
research_path = "/home/maceo/Dev/silmari-Context-Engine/thoughts/shared/research/2026-01-01-baml-integration-research.md"

# Resume from planning
plan = step_planning(project_path, research_path)
if plan["success"]:
    # Continue with remaining steps
    phases = step_phase_decomposition(project_path, plan["plan_path"])
    if phases["success"]:
        beads = step_beads_integration(project_path, phases["phase_files"], "My Epic")
        print(f"✓ Completed: Epic ID {beads.get('epic_id')}")
else:
    print(f"✗ Planning failed: {plan.get('error')}")
EOF

python3 resume_planning.py
```

**Option 2: Run step-by-step in Python shell**

```python
from pathlib import Path
from planning_pipeline import step_planning, step_phase_decomposition, step_beads_integration

project_path = Path.cwd()
research_path = "/home/maceo/Dev/silmari-Context-Engine/thoughts/shared/research/2026-01-01-baml-integration-research.md"

# Step 1: Planning
plan = step_planning(project_path, research_path)
print(f"Planning: {'✓' if plan['success'] else '✗'} {plan.get('plan_path', plan.get('error'))}")

# Step 2: Decomposition (only if planning succeeded)
if plan["success"]:
    phases = step_phase_decomposition(project_path, plan["plan_path"])
    print(f"Decomposition: {'✓' if phases['success'] else '✗'} {len(phases.get('phase_files', []))} files")

# Step 3: Beads (only if decomposition succeeded)
if plan["success"] and phases["success"]:
    beads = step_beads_integration(project_path, phases["phase_files"], "My Epic")
    print(f"Beads: {'✓' if beads['success'] else '✗'} Epic: {beads.get('epic_id')}")
```

#### Resume from Phase Decomposition Failure

If decomposition failed but planning succeeded:

**Create a script file:**

```bash
cat > resume_decomposition.py << 'EOF'
from pathlib import Path
from planning_pipeline import step_phase_decomposition, step_beads_integration

project_path = Path.cwd()

# Use the plan path from the failed run
plan_path = "thoughts/shared/plans/2025-12-31-plan.md"

# Resume from decomposition
phases = step_phase_decomposition(project_path, plan_path)
if phases["success"]:
    # Continue with beads integration
    beads = step_beads_integration(project_path, phases["phase_files"], "My Epic")
    print(f"✓ Completed: Epic ID {beads.get('epic_id')}")
else:
    print(f"✗ Decomposition failed: {phases.get('error')}")
EOF

python3 resume_decomposition.py
```

#### Resume from Beads Integration Failure

If beads integration failed but decomposition succeeded:

**Create a script file:**

```bash
cat > resume_beads.py << 'EOF'
from pathlib import Path
from planning_pipeline import step_beads_integration

project_path = Path.cwd()

# Use the phase files from the failed run
phase_files = [
    "thoughts/shared/plans/2025-12-31/00-overview.md",
    "thoughts/shared/plans/2025-12-31/01-phase-1-setup.md",
    # ... other phase files
]

# Resume from beads integration
beads = step_beads_integration(project_path, phase_files, "My Epic")
print(f"{'✓' if beads['success'] else '✗'} Beads integration: {beads.get('epic_id', beads.get('error'))}")
EOF

python3 resume_beads.py
```

#### Complete Resume Example Script

Here's a complete script you can save and run from the command line to resume a pipeline:

```python
#!/usr/bin/env python3
"""Resume a failed planning pipeline from a specific step."""

from pathlib import Path
import sys
from planning_pipeline import (
    step_research,
    step_planning,
    step_phase_decomposition,
    step_beads_integration
)

def resume_pipeline(step: str, **kwargs):
    """Resume pipeline from a specific step.
    
    Args:
        step: One of 'research', 'planning', 'decomposition', 'beads'
        **kwargs: Required arguments for the step
    """
    project_path = Path.cwd()
    
    if step == "research":
        if "research_prompt" not in kwargs:
            print("Error: research_prompt required for research step")
            sys.exit(1)
        result = step_research(project_path, kwargs["research_prompt"])
        
    elif step == "planning":
        if "research_path" not in kwargs:
            print("Error: research_path required for planning step")
            sys.exit(1)
        result = step_planning(
            project_path,
            kwargs["research_path"],
            kwargs.get("additional_context", "")
        )
        
    elif step == "decomposition":
        if "plan_path" not in kwargs:
            print("Error: plan_path required for decomposition step")
            sys.exit(1)
        result = step_phase_decomposition(project_path, kwargs["plan_path"])
        
    elif step == "beads":
        if "phase_files" not in kwargs or "epic_title" not in kwargs:
            print("Error: phase_files and epic_title required for beads step")
            sys.exit(1)
        result = step_beads_integration(
            project_path,
            kwargs["phase_files"],
            kwargs["epic_title"]
        )
    else:
        print(f"Error: Unknown step '{step}'. Use: research, planning, decomposition, or beads")
        sys.exit(1)
    
    if result["success"]:
        print(f"✓ {step.capitalize()} step completed successfully")
        print(f"Result: {result}")
    else:
        print(f"✗ {step.capitalize()} step failed")
        print(f"Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)
    
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: resume_pipeline.py <step> [args...]")
        print("\nExamples:")
        print("  # Resume from planning")
        print("  resume_pipeline.py planning --research-path thoughts/shared/research/2025-12-31-research.md")
        print("\n  # Resume from decomposition")
        print("  resume_pipeline.py decomposition --plan-path thoughts/shared/plans/2025-12-31-plan.md")
        sys.exit(1)
    
    step = sys.argv[1]
    # Parse additional arguments (simplified - use argparse for production)
    resume_pipeline(step)
```

**Command-line usage examples:**

```bash
# Recommended: Create a resume script (avoids if> prompt issues)
cat > resume_planning.sh << 'EOF'
#!/bin/bash
# Resume pipeline from planning step

cat > /tmp/resume_planning.py << 'PYEOF'
from pathlib import Path
from planning_pipeline import step_planning, step_phase_decomposition, step_beads_integration

project_path = Path.cwd()
research_path = "/thoughts/shared/research/2026-01-01-baml-integration-research.md"  # Update this

# Step 1: Planning
plan = step_planning(project_path, research_path)
print(f"Planning: {'✓' if plan['success'] else '✗'} {plan.get('plan_path', plan.get('error'))}")

# Step 2: Decomposition (only if planning succeeded)
if plan['success']:
    phases = step_phase_decomposition(project_path, plan['plan_path'])
    print(f"Decomposition: {'✓' if phases['success'] else '✗'} {len(phases.get('phase_files', []))} files")
    
    # Step 3: Beads (only if decomposition succeeded)
    if phases['success']:
        beads = step_beads_integration(project_path, phases['phase_files'], 'My Epic')
        print(f"Beads: {'✓' if beads['success'] else '✗'} Epic: {beads.get('epic_id')}")
PYEOF

python3 /tmp/resume_planning.py
EOF

chmod +x resume_planning.sh
./resume_planning.sh

# Or create a simple Python script file
cat > resume.py << 'PYEOF'
from pathlib import Path
from planning_pipeline import step_planning, step_phase_decomposition, step_beads_integration

project_path = Path.cwd()
research_path = "thoughts/shared/research/2025-12-31-your-research.md"  # Update this

# Step 1: Planning
plan = step_planning(project_path, research_path)
print(f"Planning: {'✓' if plan['success'] else '✗'} {plan.get('plan_path', plan.get('error'))}")

# Step 2: Decomposition (only if planning succeeded)
if plan['success']:
    phases = step_phase_decomposition(project_path, plan['plan_path'])
    print(f"Decomposition: {'✓' if phases['success'] else '✗'} {len(phases.get('phase_files', []))} files")
    
    # Step 3: Beads (only if decomposition succeeded)
    if phases['success']:
        beads = step_beads_integration(project_path, phases['phase_files'], 'My Epic')
        print(f"Beads: {'✓' if beads['success'] else '✗'} Epic: {beads.get('epic_id')}")
PYEOF

python3 resume.py
```

## Conclusion

The planning pipeline automates research, planning, and issue tracking for implementation work. After running the pipeline:

- Review generated documents in `thoughts/shared/research/` and `thoughts/shared/plans/`
- Check beads issues with `bd list --status=open`
- Begin implementation using the phase files as guides

For the complete API surface, consult the module's `__init__.py` which exports all public functions and classes.
