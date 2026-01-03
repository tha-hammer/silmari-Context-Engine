---
date: 2026-01-03T17:28:37-05:00
researcher: Claude
git_commit: c22694872f438407cdf489b94f9f5f7d627b3dda
branch: main
repository: silmari-Context-Engine
topic: "How to Run the Planning Pipeline with BAML Integration"
tags: [how-to, pipeline, baml, context-generation, planning]
status: complete
last_updated: 2026-01-03
last_updated_by: Claude
---

# How to Run the Planning Pipeline with BAML Integration

## Introduction

This guide walks you through running the planning pipeline with BAML-powered context generation. By the end, you will have executed a complete pipeline run that researches your codebase, generates a plan, analyzes your tech stack using BAML, decomposes the plan into phases, and creates trackable beads issues.

## Prerequisites

Before starting, ensure you have:

- Python 3.12 or higher installed
- Claude Code CLI installed and configured (`claude --version`)
- Beads CLI installed (`bd --version`)
- An Anthropic API key set as `ANTHROPIC_API_KEY` environment variable
- The BAML client generated (run `baml-cli generate` if not done)

## Steps

### 1. Set Up Environment Variables

Create or update your `.env` file with the required configuration:

```bash
# Required for BAML
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929

# Optional: BAML logging (set to TRACE for debugging)
BAML_LOG=WARN
```

Load the environment variables in your shell:

```bash
export $(cat .env | xargs)
```

### 2. Generate the BAML Client

If you haven't generated the BAML client or have modified any `.baml` files, regenerate it:

```bash
baml-cli generate
```

This creates the `baml_client/` directory with Python bindings for all BAML functions.

### 3. Run the Full Pipeline (Recommended)

For a complete pipeline execution with all steps including BAML context generation:

```python
#!/usr/bin/env python3
from pathlib import Path
from planning_pipeline import PlanningPipeline

project_path = Path.cwd()
pipeline = PlanningPipeline(project_path)

result = pipeline.run(
    research_prompt="Analyze the authentication system",
    ticket_id="ENG-001",
    auto_approve=True  # Set False for interactive mode
)

if result["success"]:
    print(f"Plan directory: {result['plan_dir']}")
    print(f"Epic ID: {result['epic_id']}")
else:
    print(f"Failed at: {result.get('failed_at', 'unknown')}")
```

Save this as `run_pipeline.py` and execute:

```bash
python3 run_pipeline.py
```

### 4. Run Context Generation Independently

To run only the BAML-powered context generation step:

```python
from pathlib import Path
from planning_pipeline import step_context_generation

result = step_context_generation(
    project_path=Path.cwd(),
    max_files=200  # Limit for performance
)

if result["success"]:
    print(f"Languages: {result['tech_stack'].languages}")
    print(f"Frameworks: {result['tech_stack'].frameworks}")
    print(f"File Groups: {len(result['file_groups'].groups)}")
```

### 5. Run Individual Pipeline Steps

For more control, execute steps individually:

```python
from pathlib import Path
from planning_pipeline import (
    step_research,
    step_planning,
    step_context_generation,
    step_phase_decomposition,
    step_beads_integration
)

project_path = Path.cwd()

# Step 1: Research
research = step_research(project_path, "How does the API handle errors?")

# Step 2: Planning
plan = step_planning(project_path, research['research_path'])

# Step 3: Context Generation (BAML)
context = step_context_generation(project_path)

# Step 4: Phase Decomposition
phases = step_phase_decomposition(project_path, plan['plan_path'])

# Step 5: Beads Integration
beads = step_beads_integration(project_path, phases['phase_files'], "Error Handling Epic")
```

### 6. Resume from a Failed Run

If the pipeline fails partway through, resume from the last successful step:

```python
from pathlib import Path
from planning_pipeline import step_phase_decomposition, step_beads_integration

project_path = Path.cwd()

# Resume from phase decomposition (if planning succeeded)
plan_path = "thoughts/shared/plans/2026-01-03-your-plan.md"

phases = step_phase_decomposition(project_path, plan_path)
if phases["success"]:
    beads = step_beads_integration(
        project_path,
        phases["phase_files"],
        "My Epic"
    )
```

### 7. Verify the Output

After a successful run, check the generated artifacts:

**Research document:**
```bash
ls thoughts/shared/research/
```

**Plan and phase files:**
```bash
ls thoughts/shared/plans/
```

**Context generation output:**
```bash
ls output/*/groups/
cat output/*/groups/tech_stack.json
```

**Beads issues created:**
```bash
bd list --status=open
```

### 8. Run Tests to Verify Setup

Confirm everything is working:

```bash
# Run context generation tests (fast, no LLM calls)
python3 -m pytest planning_pipeline/tests/test_context_generation.py -v

# Run full test suite
python3 -m pytest planning_pipeline/tests/ -v
```

## Conclusion

You have now run the planning pipeline with BAML integration. The pipeline produces:

- Research documents in `thoughts/shared/research/`
- Plan files in `thoughts/shared/plans/`
- Tech stack and file group analysis in `output/{project}/groups/`
- Beads issues for tracking implementation

For details on BAML function definitions, see `baml_src/functions.baml`. For pipeline step implementation details, see `planning_pipeline/steps.py`.
