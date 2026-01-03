---
date: 2025-12-31T12:29:06-05:00
researcher: Claude
git_commit: b1e0e420ecc789aee0c14d10a5d0497f6783d9b6
branch: main
repository: silmari-Context-Engine
topic: "Python Deterministic Control for Planning Command Pipeline"
tags: [research, codebase, python, agent-sdk, orchestration, beads, pipeline, deterministic, interactive]
status: complete
last_updated: 2025-12-31
last_updated_by: Claude
last_updated_note: "Updated to use Agent SDK, interactive mode, LLM-based phase parsing"
related_research: 2025-12-31-planning-command-architecture.md
---

```
+------------------------------------------------------------------------------+
|            RESEARCH: PYTHON DETERMINISTIC PIPELINE CONTROL                    |
|                  Using Claude Agent SDK                                       |
|                                                                               |
|  Status: Complete                                    Date: 2025-12-31         |
+------------------------------------------------------------------------------+
```

# Research: Python Deterministic Control for Planning Command Pipeline

**Date**: 2025-12-31T12:29:06-05:00
**Researcher**: Claude
**Git Commit**: b1e0e420ecc789aee0c14d10a5d0497f6783d9b6
**Branch**: main
**Repository**: silmari-Context-Engine

---

## Research Question

How to use Python with the **Claude Agent SDK** to control each step of the planning pipeline, treating Claude Code as a function that can be invoked programmatically with deterministic control?

---

## Summary

| Step | Control Pattern | Interactive Checkpoint |
|------|-----------------|----------------------|
| **Step 1: Research** | Agent SDK `query()` with research prompt | Show path + text input for open questions |
| **Step 2: Planning** | Agent SDK `query()` with plan prompt | Show path + Y/n to continue |
| **Step 3: Phase Decomposition** | Agent SDK `query()` to parse phases | Automatic (LLM-driven) |
| **Step 4: Beads Integration** | `subprocess.run(['bd', ...])` with `--json` | Automatic |
| **Step 5: Memory Capture** | Shell script hooks via subprocess | Automatic |

---

## Key Clarifications

1. **Claude Code as a Function**: The pipeline invokes `claude --dangerously-skip-permissions` via subprocess OR uses the Agent SDK `query()` function
2. **Agent SDK**: Use `claude-agent-sdk` package with async `query()` function
3. **Beads JSON**: The `bd` CLI supports `--json` flag for all output
4. **Phase Parsing**: Done via LLM, not regex - send plan to Claude with parsing prompt
5. **Interactive by Default**: Human checkpoints after research and planning phases

---

## Agent SDK Integration

### Installation

```bash
# Using uv (recommended)
uv init && uv add claude-agent-sdk

# Using pip
pip3 install claude-agent-sdk
```

### Core Pattern: `query()` Function

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage

async def run_claude_task(prompt: str, tools: list = None) -> dict:
    """Run Claude as a function using Agent SDK.

    This treats Claude Code as a callable function that:
    - Executes autonomously
    - Returns structured output
    - Can use specified tools
    """

    tools = tools or ["Read", "Edit", "Glob", "Grep", "Bash", "Task"]
    output_text = []
    tool_calls = []

    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            allowed_tools=tools,
            permission_mode="bypassPermissions"  # Equivalent to --dangerously-skip-permissions
        )
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    output_text.append(block.text)
                elif hasattr(block, "name"):
                    tool_calls.append(block.name)
        elif isinstance(message, ResultMessage):
            return {
                "success": message.subtype == "success",
                "output": "\n".join(output_text),
                "tools_used": tool_calls,
                "result_type": message.subtype
            }

    return {"success": False, "output": "\n".join(output_text), "error": "No result message"}


# Synchronous wrapper for easier use
def run_claude_sync(prompt: str, tools: list = None) -> dict:
    """Synchronous wrapper for run_claude_task."""
    return asyncio.run(run_claude_task(prompt, tools))
```

---

## Step-by-Step Implementation

### Step 1: Research Phase

**Pattern**: Run Claude with research prompt, present results with interactive checkpoint.

```python
from pathlib import Path
from datetime import datetime

async def step_research(project_path: Path, research_prompt: str) -> dict:
    """
    Step 1: Research Phase

    Run Claude to research the codebase, then present:
    - Path to research document
    - Text input for open questions (if any)
    - Y/n to continue to planning
    """

    # Build research prompt
    prompt = f"""# Research Task

{research_prompt}

## Instructions
1. Use codebase-locator to find relevant files
2. Use codebase-analyzer to understand implementation
3. Use thoughts-locator for existing documentation
4. Create a research document at: thoughts/shared/research/{datetime.now().strftime('%Y-%m-%d')}-research.md

## Output Requirements
- Include file:line references for all findings
- Document any open questions at the end
- Be thorough but concise

After creating the document, output the path and any open questions.
"""

    # Run Claude as a function
    result = await run_claude_task(
        prompt=prompt,
        tools=["Read", "Glob", "Grep", "Write", "Task"]
    )

    if not result["success"]:
        return {"success": False, "error": result.get("error", "Research failed")}

    # Find the research document path from output
    research_path = extract_file_path(result["output"], "research")
    open_questions = extract_open_questions(result["output"])

    return {
        "success": True,
        "research_path": research_path,
        "output": result["output"],
        "open_questions": open_questions
    }


def interactive_checkpoint_research(research_result: dict) -> dict:
    """
    Interactive checkpoint after research.

    Flow:
    1. Show path to research document
    2. If open questions exist: text input (end with empty line)
    3. Else: Y/n to continue
    """

    print(f"\n{'='*60}")
    print("RESEARCH COMPLETE")
    print(f"{'='*60}")
    print(f"\nResearch document: {research_result['research_path']}")

    if research_result.get("open_questions"):
        print("\nOpen Questions:")
        for i, q in enumerate(research_result["open_questions"], 1):
            print(f"  {i}. {q}")

        print("\nProvide answers (empty line to finish):")
        answers = []
        while True:
            line = input("> ").strip()
            if not line:
                break
            answers.append(line)

        return {
            "continue": True,
            "answers": answers,
            "research_path": research_result["research_path"]
        }
    else:
        response = input("\nContinue to planning? (Y/n): ").strip().lower()
        return {
            "continue": response != 'n',
            "answers": [],
            "research_path": research_result["research_path"]
        }
```

---

### Step 2: Planning Phase

**Pattern**: Run Claude to create plan, present with Y/n checkpoint.

```python
async def step_planning(
    project_path: Path,
    research_path: str,
    additional_context: str = ""
) -> dict:
    """
    Step 2: Planning Phase

    Run Claude to create an implementation plan, then present:
    - Path to plan document
    - Y/n to continue (if 'n', text input for feedback)
    """

    prompt = f"""# Create Implementation Plan

## Research Document
Read the research at: {research_path}

{f'## Additional Context{chr(10)}{additional_context}' if additional_context else ''}

## Instructions
1. Review the research findings
2. Identify implementation phases
3. Create a plan file at: thoughts/shared/plans/{datetime.now().strftime('%Y-%m-%d')}-plan.md

## Plan Structure Requirements
Each phase must have:
- Clear overview of what it accomplishes
- 1 human-testable function at the end
- File:line references for changes
- Success criteria (automated + manual)

## CRITICAL
- DO NOT leave open questions
- Each phase must be independently testable
- Phases must be ordered by dependencies

Output the plan file path when complete.
"""

    result = await run_claude_task(
        prompt=prompt,
        tools=["Read", "Glob", "Grep", "Write", "Task"]
    )

    if not result["success"]:
        return {"success": False, "error": result.get("error", "Planning failed")}

    plan_path = extract_file_path(result["output"], "plan")

    return {
        "success": True,
        "plan_path": plan_path,
        "output": result["output"]
    }


def interactive_checkpoint_plan(plan_result: dict) -> dict:
    """
    Interactive checkpoint after planning.

    Flow:
    1. Show path to plan document
    2. Y/n to continue
    3. If 'n': text input for feedback
    """

    print(f"\n{'='*60}")
    print("PLANNING COMPLETE")
    print(f"{'='*60}")
    print(f"\nPlan document: {plan_result['plan_path']}")

    response = input("\nContinue to phase decomposition? (Y/n): ").strip().lower()

    if response == 'n':
        print("\nProvide feedback (empty line to finish):")
        feedback = []
        while True:
            line = input("> ").strip()
            if not line:
                break
            feedback.append(line)

        return {
            "continue": False,
            "feedback": "\n".join(feedback),
            "plan_path": plan_result["plan_path"]
        }

    return {
        "continue": True,
        "feedback": "",
        "plan_path": plan_result["plan_path"]
    }
```

---

### Step 3: Phase Decomposition (LLM-Driven)

**Pattern**: Send plan to Claude with parsing prompt to create phase files.

```python
async def step_phase_decomposition(project_path: Path, plan_path: str) -> dict:
    """
    Step 3: Phase Decomposition

    Use LLM to parse the plan and create distinct phase files.
    Each phase ends with 1 human-testable function.
    """

    # LLM-based phase parsing prompt
    prompt = f"""# Phase Decomposition Task

Read the plan file at: {plan_path}

## Instructions
Review this plan file. Deduce how to create distinct phases.
At the end of each phase there should be 1 human testable function.
Create one file per phase.

## Output Structure
Create files at: {Path(plan_path).parent}/
- 00-overview.md (links to all phases)
- 01-phase-1-<name>.md
- 02-phase-2-<name>.md
- etc.

## Phase File Template
Each phase file must contain:
```markdown
# Phase N: <Name>

## Overview
<What this phase accomplishes>

## Human-Testable Function
<The specific function/feature that can be tested at the end of this phase>

## Dependencies
- Requires: <previous phases>
- Blocks: <next phases>

## Changes Required
<file:line references>

## Success Criteria
### Automated
- [ ] Tests pass
### Manual
- [ ] <Human can verify X>

## Beads Issue
- Issue ID: (to be created)
```

After creating all files, output:
1. List of phase file paths
2. The human-testable function for each phase
"""

    result = await run_claude_task(
        prompt=prompt,
        tools=["Read", "Write", "Glob"]
    )

    if not result["success"]:
        return {"success": False, "error": result.get("error", "Phase decomposition failed")}

    # Extract phase files from output
    phase_files = extract_phase_files(result["output"])

    return {
        "success": True,
        "phase_files": phase_files,
        "output": result["output"]
    }


def extract_phase_files(output: str) -> list:
    """Extract phase file paths from Claude output."""
    import re
    # Match paths like thoughts/shared/plans/2025-12-31/01-phase-1-setup.md
    pattern = r'(thoughts/[^\s]+/\d{2}-phase-\d+-[^\s]+\.md)'
    return re.findall(pattern, output)
```

---

### Step 4: Beads Integration

**Pattern**: Use subprocess with `--json` flag for structured output.

```python
import subprocess
import json

class BeadsController:
    """Python wrapper for beads CLI with JSON output support."""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()

    def _run_bd(self, *args) -> dict:
        """Run bd command with --json flag."""
        cmd = ['bd'] + list(args) + ['--json']

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                try:
                    return {"success": True, "data": json.loads(result.stdout)}
                except json.JSONDecodeError:
                    return {"success": True, "data": result.stdout.strip()}
            else:
                return {"success": False, "error": result.stderr.strip()}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_issue(self, title: str, issue_type: str = "task", priority: int = 2) -> dict:
        return self._run_bd('create', f'--title={title}', f'--type={issue_type}', f'--priority={priority}')

    def create_epic(self, title: str, priority: int = 2) -> dict:
        return self.create_issue(title, issue_type="epic", priority=priority)

    def add_dependency(self, issue_id: str, depends_on: str) -> dict:
        return self._run_bd('dep', 'add', issue_id, depends_on)

    def close_issue(self, issue_id: str, reason: str = None) -> dict:
        args = ['close', issue_id]
        if reason:
            args.append(f'--reason={reason}')
        return self._run_bd(*args)

    def list_issues(self, status: str = None) -> dict:
        args = ['list']
        if status:
            args.append(f'--status={status}')
        return self._run_bd(*args)

    def sync(self) -> dict:
        # Note: sync may not support --json, run without it
        result = subprocess.run(
            ['bd', 'sync'],
            cwd=str(self.project_path),
            capture_output=True,
            text=True
        )
        return {"success": result.returncode == 0, "output": result.stdout}


async def step_beads_integration(project_path: Path, phase_files: list, epic_title: str) -> dict:
    """
    Step 4: Beads Integration

    Create beads issues for plan phases with proper dependencies.
    """

    bd = BeadsController(project_path)

    # Create epic
    epic_result = bd.create_epic(epic_title)
    if not epic_result["success"]:
        return {"success": False, "error": f"Failed to create epic: {epic_result['error']}"}

    epic_id = epic_result["data"].get("id") if isinstance(epic_result["data"], dict) else None

    # Create issues for each phase
    phase_issues = []
    for i, phase_file in enumerate(phase_files):
        phase_name = Path(phase_file).stem.split('-', 2)[-1].replace('-', ' ').title()

        result = bd.create_issue(
            title=f"Phase {i+1}: {phase_name}",
            issue_type="task",
            priority=2
        )

        if result["success"]:
            issue_id = result["data"].get("id") if isinstance(result["data"], dict) else None
            phase_issues.append({
                "phase": i + 1,
                "file": phase_file,
                "issue_id": issue_id
            })

    # Link dependencies (each phase depends on previous)
    for i in range(1, len(phase_issues)):
        if phase_issues[i]["issue_id"] and phase_issues[i-1]["issue_id"]:
            bd.add_dependency(phase_issues[i]["issue_id"], phase_issues[i-1]["issue_id"])

    # Sync
    bd.sync()

    return {
        "success": True,
        "epic_id": epic_id,
        "phase_issues": phase_issues
    }
```

---

### Step 5: Memory Capture

**Pattern**: Invoke shell hooks via subprocess.

```python
def step_memory_capture(project_path: Path, plan_dir: str, feature_id: str) -> dict:
    """
    Step 5: Memory Capture

    Store planning artifacts and compile fresh context.
    """

    results = {}

    # Record planning success
    feedback_script = project_path / ".agent" / "hooks" / "capture-feedback.sh"
    if feedback_script.exists():
        result = subprocess.run(
            ['bash', str(feedback_script), 'success', feature_id, f'Created plan at {plan_dir}'],
            cwd=str(project_path),
            capture_output=True,
            text=True
        )
        results["feedback_captured"] = result.returncode == 0

    # Store plan as artifact
    artifact_script = project_path / ".agent" / "hooks" / "artifact-manager.sh"
    if artifact_script.exists():
        result = subprocess.run(
            ['bash', str(artifact_script), 'store', f'{feature_id}-plan.md', plan_dir, 'documents'],
            cwd=str(project_path),
            capture_output=True,
            text=True
        )
        results["artifact_stored"] = result.returncode == 0

    # Compile fresh context
    compile_script = project_path / ".agent" / "hooks" / "compile-context.sh"
    if compile_script.exists():
        result = subprocess.run(
            ['bash', str(compile_script)],
            cwd=str(project_path),
            capture_output=True,
            text=True
        )
        results["context_compiled"] = result.returncode == 0

    return {"success": True, **results}
```

---

## Complete Interactive Pipeline

```python
#!/usr/bin/env python3
"""
Planning Pipeline with Claude Agent SDK

Treats Claude Code as a function with interactive checkpoints.

Usage:
    python planning_pipeline.py "Research prompt here" --ticket ENG-1234
"""

import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional
import argparse

from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage


class PlanningPipeline:
    """
    Interactive planning pipeline using Claude Agent SDK.

    Flow:
    1. Research -> checkpoint (path + questions or Y/n)
    2. Planning -> checkpoint (path + Y/n, 'n' = text input)
    3. Phase Decomposition -> automatic (LLM-driven)
    4. Beads Integration -> automatic
    5. Memory Capture -> automatic
    """

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()
        self.beads = BeadsController(project_path)

    async def run(self, research_prompt: str, ticket_id: Optional[str] = None) -> dict:
        """Run the complete planning pipeline with interactive checkpoints."""

        results = {
            "started": datetime.now().isoformat(),
            "ticket_id": ticket_id,
            "steps": {}
        }

        # Step 1: Research
        print("\n" + "="*60)
        print("STEP 1/5: RESEARCH PHASE")
        print("="*60)

        research = await step_research(self.project_path, research_prompt)
        results["steps"]["research"] = research

        if not research["success"]:
            results["success"] = False
            results["failed_at"] = "research"
            return results

        checkpoint = interactive_checkpoint_research(research)
        if not checkpoint["continue"]:
            results["success"] = False
            results["stopped_at"] = "research"
            return results

        additional_context = "\n".join(checkpoint.get("answers", []))

        # Step 2: Planning (may loop on feedback)
        while True:
            print("\n" + "="*60)
            print("STEP 2/5: PLANNING PHASE")
            print("="*60)

            planning = await step_planning(
                self.project_path,
                checkpoint["research_path"],
                additional_context
            )
            results["steps"]["planning"] = planning

            if not planning["success"]:
                results["success"] = False
                results["failed_at"] = "planning"
                return results

            plan_checkpoint = interactive_checkpoint_plan(planning)

            if plan_checkpoint["continue"]:
                break
            else:
                # User provided feedback, re-run planning with it
                additional_context = plan_checkpoint["feedback"]
                print(f"\nRe-running planning with feedback...")

        # Step 3: Phase Decomposition (automatic)
        print("\n" + "="*60)
        print("STEP 3/5: PHASE DECOMPOSITION")
        print("="*60)

        decomposition = await step_phase_decomposition(
            self.project_path,
            plan_checkpoint["plan_path"]
        )
        results["steps"]["decomposition"] = decomposition

        if not decomposition["success"]:
            results["success"] = False
            results["failed_at"] = "decomposition"
            return results

        print(f"\nCreated {len(decomposition['phase_files'])} phase files")

        # Step 4: Beads Integration (automatic)
        print("\n" + "="*60)
        print("STEP 4/5: BEADS INTEGRATION")
        print("="*60)

        epic_title = f"Plan: {ticket_id}" if ticket_id else f"Plan: {datetime.now().strftime('%Y-%m-%d')}"
        beads = await step_beads_integration(
            self.project_path,
            decomposition["phase_files"],
            epic_title
        )
        results["steps"]["beads"] = beads

        if beads["success"]:
            print(f"\nCreated epic: {beads.get('epic_id')}")
            print(f"Created {len(beads.get('phase_issues', []))} phase issues")

        # Step 5: Memory Capture (automatic)
        print("\n" + "="*60)
        print("STEP 5/5: MEMORY CAPTURE")
        print("="*60)

        memory = step_memory_capture(
            self.project_path,
            str(Path(decomposition["phase_files"][0]).parent) if decomposition["phase_files"] else "",
            ticket_id or "plan"
        )
        results["steps"]["memory"] = memory

        # Complete
        results["success"] = True
        results["completed"] = datetime.now().isoformat()
        results["plan_dir"] = str(Path(decomposition["phase_files"][0]).parent) if decomposition["phase_files"] else None
        results["epic_id"] = beads.get("epic_id")

        print("\n" + "="*60)
        print("PIPELINE COMPLETE")
        print("="*60)
        print(f"\nPlan directory: {results['plan_dir']}")
        print(f"Epic ID: {results['epic_id']}")

        return results


# Helper functions
def extract_file_path(output: str, file_type: str) -> str:
    """Extract file path from Claude output."""
    import re
    pattern = rf'(thoughts/[^\s]+{file_type}[^\s]*\.md)'
    match = re.search(pattern, output, re.IGNORECASE)
    return match.group(1) if match else None


def extract_open_questions(output: str) -> list:
    """Extract open questions from research output."""
    import re
    # Look for "Open Questions" section
    questions = []
    in_questions = False
    for line in output.split('\n'):
        if 'open question' in line.lower():
            in_questions = True
            continue
        if in_questions:
            if line.strip().startswith(('-', '*', '1', '2', '3', '4', '5')):
                questions.append(line.strip().lstrip('-*0123456789. '))
            elif line.strip() and not line.startswith('#'):
                continue
            elif line.startswith('#'):
                break
    return questions


# CLI
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run planning pipeline with Claude Agent SDK")
    parser.add_argument("prompt", help="Research prompt to start planning")
    parser.add_argument("--ticket", help="Ticket ID (e.g., ENG-1234)")
    parser.add_argument("--project", default=".", help="Project path")

    args = parser.parse_args()

    pipeline = PlanningPipeline(Path(args.project))
    result = asyncio.run(pipeline.run(args.prompt, args.ticket))

    import json
    print("\n" + json.dumps(result, indent=2))
```

---

## Alternative: Direct Subprocess Approach

If the Agent SDK is not installed, use direct subprocess calls:

```python
import subprocess

def run_claude_subprocess(prompt: str, project_path: Path) -> dict:
    """
    Run Claude Code directly via subprocess.

    Equivalent to: claude --dangerously-skip-permissions -p "prompt"
    """

    cmd = [
        "claude",
        "--dangerously-skip-permissions",
        "--print",
        "--output-format", "text",
        "-p", prompt
    ]

    result = subprocess.run(
        cmd,
        cwd=str(project_path),
        capture_output=True,
        text=True,
        timeout=900  # 15 minute timeout
    )

    return {
        "success": result.returncode == 0,
        "output": result.stdout,
        "error": result.stderr
    }
```

---

## Code References

| Source | Description |
|--------|-------------|
| [Agent SDK Quickstart](https://platform.claude.com/docs/en/agent-sdk/quickstart) | Official SDK documentation |
| `orchestrator.py:962-1093` | Existing subprocess patterns |
| `loop-runner.py:108-148` | Dependency validation (DFS) |
| `loop-runner.py:154-209` | Topological sorting (Kahn's) |

---

## Interactive Flow Diagram

```
+-------------------+     +------------------+     +---------------------+
| Step 1: Research  |---->| Checkpoint       |---->| Step 2: Planning    |
+-------------------+     +------------------+     +---------------------+
                          |                        |
                          | Path shown             | Path shown
                          | Open questions?        | Y/n to continue
                          |   -> Text input        |   n -> Text input
                          |   -> Empty line ends   |        (feedback)
                          | Else Y/n               |        Re-run plan
                          |                        |
                          +------------------------+
                                     |
                                     v
+-------------------+     +------------------+     +---------------------+
| Step 5: Memory    |<----| Step 4: Beads    |<----| Step 3: Phase       |
| (automatic)       |     | (automatic)      |     | Decomposition       |
+-------------------+     +------------------+     | (LLM-driven)        |
                                                   +---------------------+
```

---

## Success Criteria

### Automated Verification
- [ ] Agent SDK `query()` completes research task
- [ ] Phase decomposition creates 1+ phase files via LLM
- [ ] `bd create --json` returns parseable JSON
- [ ] Dependencies linked: `bd dep add` succeeds

### Manual Verification
- [ ] Interactive checkpoint shows research path correctly
- [ ] Text input for open questions works (empty line ends)
- [ ] Plan checkpoint Y/n flow works correctly
- [ ] 'n' response enables text feedback and re-runs planning
