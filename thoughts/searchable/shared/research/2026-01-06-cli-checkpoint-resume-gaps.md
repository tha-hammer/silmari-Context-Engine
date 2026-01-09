---
date: 2026-01-06T05:23:58-05:00
researcher: Claude
git_commit: 81c1df19182855dc8c0a67088247201a8e9daa75
branch: main
repository: silmari-Context-Engine
topic: "CLI checkpoint resume options missing from --help"
tags: [research, cli, checkpoints, resume, silmari-rlm-act]
status: complete
last_updated: 2026-01-06
last_updated_by: Claude
---

```
┌─────────────────────────────────────────────────────────────────────┐
│          CLI CHECKPOINT RESUME OPTIONS - GAP ANALYSIS               │
│                     silmari-rlm-act Pipeline                        │
└─────────────────────────────────────────────────────────────────────┘
```

**Date**: 2026-01-06T05:23:58-05:00
**Researcher**: Claude
**Git Commit**: 81c1df19182855dc8c0a67088247201a8e9daa75
**Branch**: main
**Repository**: silmari-Context-Engine

---

## Research Question

The `python -m silmari_rlm_act.cli run` command contains arguments to resume checkpoints but they do not show in `--help`. Research the CLI file commands and document all options that should be added to `--help`.

---

## Summary

The CLI has **interactive checkpoint capabilities** in `silmari_rlm_act/checkpoints/interactive.py` that are **not exposed as CLI options**. The `resume` command is also missing the `--batch` flag that exists on the `run` command, creating an inconsistency between the two commands.

---

## 📊 Current CLI Options

### `run` Command (Current)
| Option | Short | Description | Exposed in --help |
|--------|-------|-------------|-------------------|
| `--question` | `-q` | Research question (required) | ✅ |
| `--project` | `-p` | Project directory | ✅ |
| `--plan-name` | `-n` | Name for TDD plan | ✅ |
| `--autonomous` | `-a` | Fully autonomous mode | ✅ |
| `--batch` | `-b` | Batch mode | ✅ |

### `resume` Command (Current)
| Option | Short | Description | Exposed in --help |
|--------|-------|-------------|-------------------|
| `--project` | `-p` | Project directory | ✅ |
| `--autonomous` | `-a` | Continue in autonomous mode | ✅ |
| `--batch` | `-b` | Batch mode | ❌ **MISSING** |

### `cleanup` Command (Current - Complete)
| Option | Short | Description | Exposed in --help |
|--------|-------|-------------|-------------------|
| `--project` | `-p` | Project directory | ✅ |
| `--days` | `-d` | Delete older than N days | ✅ |
| `--all` | - | Delete all checkpoints | ✅ |

### `status` Command (Current - Complete)
| Option | Short | Description | Exposed in --help |
|--------|-------|-------------|-------------------|
| `--project` | `-p` | Project directory | ✅ |

---

## 🚨 Missing CLI Options

### 1. `resume` Missing `--batch` Flag

**Location**: `silmari_rlm_act/cli.py:148`

The `resume` command only supports `--autonomous` but not `--batch`, despite the `run` command supporting both:

```python
# run command (lines 52-64)
@click.option("--autonomous", "-a", is_flag=True, ...)
@click.option("--batch", "-b", is_flag=True, ...)

# resume command (lines 141-148) - MISSING --batch
@click.option("--autonomous", "-a", is_flag=True, ...)
```

**Impact**: Users resuming cannot select batch mode, only checkpoint or autonomous.

---

### 2. Interactive Functions Not Exposed as CLI Options

The `interactive.py` module has prompts that only work interactively, with no CLI flag equivalents:

| Interactive Function | Purpose | Missing CLI Flag |
|---------------------|---------|------------------|
| `prompt_resume_point(phases)` | Select which phase to resume from | `--from-phase` |
| `prompt_use_checkpoint(...)` | Choose whether to use checkpoint | `--no-checkpoint` / `--skip-checkpoint` |
| `prompt_autonomy_mode(...)` | Select execution mode interactively | (partially covered by `--autonomous`) |

**Location**: `silmari_rlm_act/checkpoints/interactive.py:381-410`

```python
def prompt_resume_point(phases: list[str]) -> str:
    """Prompt user to select which phase to resume from."""
    # ... displays numbered list and returns selected phase
```

---

### 3. No Checkpoint Listing Command

There's no way to list available checkpoints before resuming. The `cleanup` command shows the most recent checkpoint info, but there's no dedicated `list` subcommand or `--list` flag.

**CheckpointManager has the capability**: `silmari_rlm_act/checkpoints/manager.py:86-113`

```python
def detect_resumable_checkpoint(self) -> Optional[dict[str, Any]]:
    """Find most recent checkpoint."""
    # Could be extended to return ALL checkpoints for listing
```

---

### 4. No Specific Checkpoint Selection

The `resume` command always uses the most recent checkpoint. There's no way to specify a checkpoint ID or timestamp.

```python
# cli.py:176 - always uses detect_resumable_checkpoint()
if not pipeline.resume_from_checkpoint():
    click.echo("No checkpoint found to resume from.")
```

---

## 📋 Recommended Additions

### Priority Matrix

| Addition | Priority | Rationale |
|----------|----------|-----------|
| `resume --batch` | 🔴 Critical | Parity with `run` command |
| `resume --from-phase PHASE` | 🟡 Important | Exposes existing interactive capability |
| `status --list-checkpoints` | 🟡 Important | Discoverability before resume |
| `resume --checkpoint-id ID` | 🟢 Enhancement | Specific checkpoint selection |
| `resume --no-interactive` | 🟢 Enhancement | CI/CD usage |

---

## 🎯 Code References

| Component | File | Lines |
|-----------|------|-------|
| CLI entry point | `silmari_rlm_act/cli.py` | 1-326 |
| `run` command | `silmari_rlm_act/cli.py` | 31-130 |
| `resume` command | `silmari_rlm_act/cli.py` | 133-206 |
| `status` command | `silmari_rlm_act/cli.py` | 209-270 |
| `cleanup` command | `silmari_rlm_act/cli.py` | 273-321 |
| Interactive prompts | `silmari_rlm_act/checkpoints/interactive.py` | 1-411 |
| CheckpointManager | `silmari_rlm_act/checkpoints/manager.py` | 1-239 |
| Pipeline resume logic | `silmari_rlm_act/pipeline.py` | 436-448 |

---

## Architecture Documentation

### Pipeline Autonomy Modes

The pipeline supports three modes defined in `silmari_rlm_act/models.py:24-27`:

```python
class AutonomyMode(str, Enum):
    CHECKPOINT = "checkpoint"      # Pause at each phase
    FULLY_AUTONOMOUS = "autonomous" # No pauses
    BATCH = "batch"                # Pause between groups
```

The `run` command exposes all three via `--autonomous` and `--batch` flags.
The `resume` command only exposes two (missing `--batch`).

### Checkpoint Storage

Checkpoints are stored in `.rlm-act-checkpoints/` as JSON files with UUID filenames.
Each contains: `id`, `phase`, `timestamp`, `state`, `errors`, `git_commit`.

---

## Open Questions

1. Should `status` command show list of all checkpoints by default, or require a flag?
2. Should `--from-phase` accept phase names or phase numbers?
3. How should `--checkpoint-id` handle non-existent IDs - error or fallback to interactive?
