---
date: 2026-01-03T14:32:37-05:00
researcher: Claude
git_commit: f7aacf4da161bab80919966cf9159d24b9fc00ec
branch: main
repository: silmari-Context-Engine
topic: "Running Python library from other directories for Claude local directory context"
tags: [research, codebase, cli, paths, subprocess, claude-runner]
status: complete
last_updated: 2026-01-03
last_updated_by: Claude
---

# Research: Cross-Directory Execution for Claude Local Context

┌─────────────────────────────────────────────────────────────────┐
│  CONTEXT ENGINE - Cross-Directory Execution Research           │
│  Status: Complete | Date: 2026-01-03                            │
└─────────────────────────────────────────────────────────────────┘

**Date**: 2026-01-03T14:32:37-05:00
**Researcher**: Claude
**Git Commit**: f7aacf4da161bab80919966cf9159d24b9fc00ec
**Branch**: main
**Repository**: silmari-Context-Engine

## Research Question

How to run this Python library from other directories to give Claude local directory context?

## Summary

The library provides a `--project` (or `-p`) CLI flag that accepts a target directory path. When specified, Claude and all subprocess commands are executed with `cwd=project_path`, giving Claude access to the local directory context of the target project rather than where the script is run from.

**Quick Answer**: Use `--project /path/to/target` to run from anywhere while giving Claude context of the target directory.

## 📚 Detailed Findings

### 🎯 Primary Mechanism: `--project` Flag

All CLI scripts support specifying the target project directory:

| Script | Flag | Default |
|--------|------|---------|
| `planning_orchestrator.py` | `--project`, `-p` | `Path.cwd()` |
| `orchestrator.py` | `--project`, `-p` | `Path.cwd()` |
| `loop-runner.py` | positional `project` | `Path.cwd()` |
| `mcp-setup.py` | `--project`, `-p` | `Path.cwd()` |

**Usage Examples**:

```bash
# Run planning pipeline on remote project
python planning_orchestrator.py --project ~/other-project --ticket ENG-123

# Run from context-engine directory, target another project
cd ~/Dev/silmari-Context-Engine
python planning_orchestrator.py -p ~/projects/myapp

# Loop runner with positional argument
python loop-runner.py ~/projects/myapp

# Or with absolute path
python loop-runner.py /home/user/projects/myapp
```

### 📊 Path Resolution Behavior

The library resolves paths in this order (`helpers.py:74-141`):

1. **Absolute paths** - Used directly if they exist
2. **Relative to project root** - `project_path / input_path`
3. **Filename search** - Searches in `thoughts/shared/{type}/` directories

```python
# From planning_pipeline/helpers.py:74-141
def resolve_file_path(project_path, input_path, file_type):
    # 1. Try as absolute path
    if Path(input_path).is_absolute() and Path(input_path).exists():
        return Path(input_path)

    # 2. Try relative from project root
    relative_from_project = project_path / input_path
    if relative_from_project.exists():
        return relative_from_project

    # 3. Search in thoughts directories
    ...
```

### 🔧 How Directory Context is Passed to Claude

The library passes directory context via subprocess `cwd` parameter:

```python
# orchestrator.py:1044-1050 (sets cwd ✓)
result = subprocess.run(
    cmd,
    cwd=str(project_path),  # Claude runs in project directory
    stdin=None,
    stdout=None,
    stderr=None,
    timeout=3600
)
```

**Claude CLI has NO `--cwd` flag**. The working directory must be set by the subprocess execution context.

### 📁 Code Locations

| Component | File | Line | Pattern |
|-----------|------|------|---------|
| Argument parsing | `planning_orchestrator.py` | 38-43 | `--project` flag |
| Path resolution | `pipeline.py` | 25-26 | `Path(project_path).resolve()` |
| Path resolver util | `helpers.py` | 74-141 | `resolve_file_path()` |
| Claude invocation (legacy) | `orchestrator.py` | 1046 | `cwd=str(project_path)` |
| Claude invocation (legacy) | `loop-runner.py` | 1080 | `cwd=str(project_path)` |
| Beads subprocess | `beads_controller.py` | 27-29 | `cwd=str(self.project_path)` |

### ⚠️ Important Note: Newer Pipeline Code

The newer planning pipeline modules do **NOT** currently set `cwd` when invoking Claude:

| File | Line | Sets `cwd`? |
|------|------|-------------|
| `claude_runner.py` | 96, 148 | ❌ No |
| `phase_execution/claude_invoker.py` | 32 | ❌ No |

**Implication**: When using `claude_runner.py` directly, Claude inherits the working directory of the Python process. The `--project` flag works correctly because the orchestrators either:
1. Change to the project directory before invoking
2. Use the legacy invocation code that sets `cwd`

### 🛡️ Recommended Usage Patterns

**Pattern 1: From Context Engine Directory**
```bash
cd ~/Dev/silmari-Context-Engine
python planning_orchestrator.py --project ~/projects/target-app
```

**Pattern 2: Using Absolute Paths**
```bash
python ~/Dev/silmari-Context-Engine/planning_orchestrator.py \
    --project ~/projects/target-app
```

**Pattern 3: Programmatic Usage**
```python
from pathlib import Path
from planning_pipeline import PlanningPipeline

# Works from any directory - project_path is explicit
pipeline = PlanningPipeline(Path("~/projects/target-app").expanduser())
result = pipeline.run(research_prompt="Analyze auth flow")
```

**Pattern 4: With Resume Options**
```bash
python planning_orchestrator.py \
    --project ~/projects/myapp \
    --resume \
    --research-path research-doc.md  # Resolves relative to project
```

## Code References

- `planning_orchestrator.py:38-43` - CLI argument parsing for `--project`
- `planning_pipeline/pipeline.py:25-26` - Path resolution in constructor
- `planning_pipeline/helpers.py:74-141` - `resolve_file_path()` function
- `orchestrator.py:1044-1050` - Subprocess with `cwd` parameter
- `planning_pipeline/autonomous_loop.py:82` - Default to `Path.cwd()`
- `planning_pipeline/beads_controller.py:27-29` - Beads subprocess `cwd`

## Architecture Documentation

```
┌─────────────────────────────────────────────────────────────────┐
│                    Execution Flow                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CLI Script (any directory)                                      │
│       │                                                          │
│       ▼                                                          │
│  Parse --project flag → default: Path.cwd()                      │
│       │                                                          │
│       ▼                                                          │
│  Path.expanduser().resolve() → absolute path                     │
│       │                                                          │
│       ▼                                                          │
│  PlanningPipeline(project_path)                                  │
│       │                                                          │
│       ▼                                                          │
│  subprocess.run(cmd, cwd=str(project_path))                      │
│       │                                                          │
│       ▼                                                          │
│  Claude sees target directory as cwd                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Design Decisions**:
- No `os.chdir()` calls - never changes Python process working directory
- All paths resolved to absolute at initialization
- `cwd` parameter used for subprocess calls
- `Path.cwd()` only used as fallback default

## Related Research

- `thoughts/shared/docs/2026-01-01-how-to-use-cli-commands.md` - CLI usage guide

## Open Questions

1. Should `claude_runner.py` and `phase_execution/claude_invoker.py` accept and use a `project_path` parameter for setting `cwd`?
2. Should there be an environment variable option (e.g., `CONTEXT_ENGINE_PROJECT`) for setting default project path?
